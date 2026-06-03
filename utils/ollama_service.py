"""
ollama_service.py - Servicio de IA local usando Ollama.

Usa un modelo local liviano sin API keys externas. El modelo principal se
configura con OLLAMA_MODEL y por defecto usa llama3.2:1b. TinyLlama queda como
opcion de respaldo documentada para equipos con menos recursos.
"""

from __future__ import annotations

import json
import os
import socket
import threading
import time
from collections import OrderedDict
from urllib import request as urllib_request
from urllib.error import HTTPError, URLError

from data.ia_fallback import (
    MATERIA_A_PERSONAJE,
    clasificar_mensaje,
    obtener_respuesta_fallback,
)
from data.reporte_fallback import generar_reporte_fallback


OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
# llama3.2:1b — modelo por defecto: rapido, ~1.3GB. El usuario puede cambiarlo
# desde la pantalla de inicio (selector) si tiene mas modelos descargados.
MODELO_DEFECTO = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
MODELO_RESPALDO = "tinyllama"
TIMEOUT_SEGUNDOS = 60
MAX_TOKENS = 120
TEMPERATURA = 0.7
CACHE_MAX = 30
KEEP_ALIVE = "15m"
CONTEXTO_TOKENS = 4096


SYSTEM_PROMPTS = {
    "El Riviel": (
        "Eres El Riviel, un espiritu sabio del rio Pacifico colombiano. "
        "Hablas con ninos de 8 a 12 anos. Ensenas matematicas con ejemplos "
        "del rio, cangrejos, peces y canoas."
    ),
    "La Tunda": (
        "Eres La Tunda, guardiana mistica del bosque del Pacifico colombiano. "
        "Hablas con ninos de 8 a 12 anos. Ensenas lenguaje con ejemplos "
        "del bosque, arboles, pajaros y la selva."
    ),
    "El Duende": (
        "Eres El Duende, un personaje magico que ensena ingles a ninos "
        "colombianos de 8 a 12 anos. Mezclas espanol e ingles de forma clara."
    ),
    "La Madre de Agua": (
        "Eres La Madre de Agua, protectora de la vida acuatica del Pacifico "
        "colombiano. Hablas con ninos de 8 a 12 anos y ensenas biologia con "
        "ejemplos del manglar, ballenas, peces y el ecosistema."
    ),
}

SYSTEM_PROMPT_GENERICO = (
    "Eres un personaje amigable del juego educativo Pacifico Educativo. "
    "Hablas con ninos de 8 a 12 anos del Pacifico colombiano."
)

REGLAS_RESPUESTA_CORTA = (
    "Responde siempre en espanol, con tono infantil, educativo y motivador. "
    "Usa maximo 2 oraciones cortas, o 3 si es una pista. "
    "No menciones detalles tecnicos, Ollama, modelos ni errores internos."
)

SYSTEM_PROMPT_DOCENTE = (
    "Eres un asistente pedagogico para docentes de educacion primaria. "
    "Analizas datos de desempeno estudiantil y generas informes claros sobre "
    "las principales dificultades de los estudiantes, con recomendaciones "
    "pedagogicas concretas para mejorar el aprendizaje. "
    "No uses lenguaje infantil. Sé preciso y util para el docente."
)

REGLAS_REPORTE_DOCENTE = (
    "Responde en espanol con tono profesional y directo, dirigido a un docente de primaria. "
    "Usa parrafos cortos. Maximo 300 palabras. "
    "Se especifico: menciona las materias y temas debiles por nombre. "
    "No menciones Ollama, modelos ni detalles tecnicos."
)


class CacheIA:
    """Cache LRU simple en memoria para evitar llamadas repetidas a Ollama."""

    def __init__(self, capacidad: int = CACHE_MAX):
        self._cache = OrderedDict()
        self._capacidad = capacidad
        self._lock = threading.Lock()

    def obtener(self, clave: str) -> str | None:
        with self._lock:
            if clave in self._cache:
                self._cache.move_to_end(clave)
                return self._cache[clave]
        return None

    def guardar(self, clave: str, valor: str):
        with self._lock:
            if clave in self._cache:
                self._cache.move_to_end(clave)
            self._cache[clave] = valor
            if len(self._cache) > self._capacidad:
                self._cache.popitem(last=False)


class ServicioIA:
    """
    Servicio de IA local con Ollama.

    Si Ollama esta apagado, el modelo no esta instalado, hay timeout o la
    respuesta viene vacia, devuelve fallback offline para que el juego no se
    detenga.
    """

    def __init__(self, modelo: str = MODELO_DEFECTO, url: str = OLLAMA_URL):
        self.modelo = modelo
        self.url = url.rstrip("/")
        self.cache = CacheIA()
        self._disponible: bool | None = None
        self._ultima_verificacion = 0.0
        self._ultimo_error = ""

    def cambiar_modelo(self, nuevo_modelo: str) -> dict:
        """Cambia el modelo activo en runtime y lo verifica."""
        nuevo_modelo = (nuevo_modelo or "").strip()
        if not nuevo_modelo:
            return {"ok": False, "error": "Modelo vacio"}
        anterior = self.modelo
        self.modelo = nuevo_modelo
        # Forzar reverificacion (no usar cache)
        self._disponible = None
        self._ultima_verificacion = 0.0
        ok = self.verificar_disponibilidad()
        if ok:
            print(f"[IA] Modelo cambiado: '{anterior}' -> '{nuevo_modelo}'")
            return {"ok": True, "modelo": self.modelo}
        # Revertir si fallo
        self.modelo = anterior
        self._disponible = None
        self._ultima_verificacion = 0.0
        return {"ok": False, "error": f"El modelo '{nuevo_modelo}' no esta disponible en Ollama.", "modelo": anterior}

    def listar_modelos_instalados(self) -> list[str]:
        """Devuelve la lista de modelos instalados en Ollama. Vacia si Ollama no responde."""
        try:
            req = urllib_request.Request(f"{self.url}/api/tags", method="GET")
            with urllib_request.urlopen(req, timeout=3) as resp:
                datos = json.loads(resp.read().decode("utf-8"))
                return sorted([m.get("name", "") for m in datos.get("models", []) if m.get("name")])
        except Exception as e:
            print(f"[IA] No se pudieron listar modelos: {e}")
            return []

    def estado(self) -> dict:
        disponible = self.verificar_disponibilidad()
        return {
            "disponible": disponible,
            "modelo": self.modelo,
            "modelo_respaldo": MODELO_RESPALDO,
            "url": self.url,
            "fuente": "ollama" if disponible else "fallback",
            "mensaje": (
                "IA local activa."
                if disponible
                else "Modo sin conexion activo: usare respuestas educativas de respaldo."
            ),
            "error": "" if disponible else self._ultimo_error,
        }

    def _clave_cache(
        self,
        personaje: str,
        mensaje: str,
        contexto_materia: str,
        contexto_nivel: int,
        contexto_nivel_info: dict | None,
    ) -> str:
        nombre_nivel = ""
        if isinstance(contexto_nivel_info, dict):
            nombre_nivel = str(contexto_nivel_info.get("nombre", ""))
        return f"{self.modelo}:{personaje}:{contexto_materia}:{contexto_nivel}:{nombre_nivel}:{mensaje[:80]}"

    def _construir_contexto_nivel(
        self,
        contexto_materia: str,
        contexto_nivel: int,
        contexto_nivel_info: dict | None = None,
    ) -> str:
        partes = []
        if contexto_materia:
            partes.append(f"Materia: {contexto_materia}.")
        if contexto_nivel:
            partes.append(f"Nivel: {contexto_nivel} de 5.")

        if isinstance(contexto_nivel_info, dict):
            for clave, etiqueta in (
                ("nombre", "Nombre del nivel"),
                ("personaje", "Personaje del nivel"),
                ("minijuego", "Minijuego"),
                ("modo", "Modo"),
                ("instruccion", "Instruccion"),
                ("frase_intro", "Frase intro"),
            ):
                valor = contexto_nivel_info.get(clave)
                if valor:
                    partes.append(f"{etiqueta}: {valor}.")

            conteos = contexto_nivel_info.get("conteos")
            if isinstance(conteos, dict):
                resumen = []
                for clave in ("items", "piezas", "zonas"):
                    cantidad = conteos.get(clave)
                    if cantidad:
                        resumen.append(f"{cantidad} {clave}")
                if resumen:
                    partes.append("Contenido interactivo: " + ", ".join(resumen) + ".")

        return " ".join(partes)

    def verificar_disponibilidad(self) -> bool:
        # Override global desde la UI: si IA esta apagada, reportar como no disponible.
        if os.getenv("IA_GLOBAL_OFF") == "1":
            return False
        ahora = time.time()
        if self._disponible is not None and (ahora - self._ultima_verificacion) < 30:
            return self._disponible

        try:
            req = urllib_request.Request(f"{self.url}/api/tags", method="GET")
            with urllib_request.urlopen(req, timeout=3) as resp:
                datos = json.loads(resp.read().decode("utf-8"))
                modelos = [m.get("name", "") for m in datos.get("models", [])]
                self._disponible = self._modelo_instalado(modelos)
                self._ultima_verificacion = ahora
                if self._disponible:
                    self._ultimo_error = ""
                    print(f"[IA] Ollama disponible con modelo '{self.modelo}'.")
                else:
                    self._ultimo_error = f"Modelo '{self.modelo}' no instalado."
                    print(f"[IA] Ollama corriendo pero modelo '{self.modelo}' no encontrado.")
                    print(f"[IA] Modelos disponibles: {modelos}")
                return self._disponible
        except (URLError, OSError, socket.timeout, TimeoutError) as e:
            self._disponible = False
            self._ultima_verificacion = ahora
            self._ultimo_error = "Ollama no esta corriendo o no responde en el puerto configurado."
            print(f"[IA] Ollama no disponible: {e}")
            return False

    def _modelo_instalado(self, modelos: list[str]) -> bool:
        for nombre in modelos:
            if nombre == self.modelo:
                return True
            if ":" not in self.modelo and nombre.startswith(f"{self.modelo}:"):
                return True
        return False

    def _resultado_fallback(
        self,
        personaje: str,
        tipo: str,
        materia: str = "",
        nivel: int = 0,
        contexto_nivel_info: dict | None = None,
    ) -> dict:
        respuesta = obtener_respuesta_fallback(
            personaje,
            tipo,
            materia=materia,
            nivel=nivel,
            contexto=contexto_nivel_info,
        )
        return {
            "respuesta": respuesta,
            "fuente": "fallback",
            "modelo": self.modelo,
            "disponible": False,
            "error": self._ultimo_error,
        }

    def generar_respuesta(
        self,
        personaje: str,
        mensaje: str,
        contexto_materia: str = "",
        contexto_nivel: int = 0,
        contexto_nivel_info: dict | None = None,
    ) -> dict:
        if not personaje and contexto_materia:
            personaje = MATERIA_A_PERSONAJE.get(contexto_materia, "")

        clave_cache = self._clave_cache(
            personaje, mensaje, contexto_materia, contexto_nivel, contexto_nivel_info
        )
        respuesta_cache = self.cache.obtener(clave_cache)
        if respuesta_cache:
            return {
                "respuesta": respuesta_cache,
                "fuente": "cache",
                "modelo": self.modelo,
                "disponible": True,
                "error": "",
            }

        if self.verificar_disponibilidad():
            respuesta_ia = self._llamar_ollama(
                personaje,
                mensaje,
                contexto_materia,
                contexto_nivel,
                contexto_nivel_info,
            )
            if respuesta_ia:
                self.cache.guardar(clave_cache, respuesta_ia)
                return {
                    "respuesta": respuesta_ia,
                    "fuente": "ollama",
                    "modelo": self.modelo,
                    "disponible": True,
                    "error": "",
                }

        tipo = clasificar_mensaje(mensaje)
        return self._resultado_fallback(
            personaje, tipo, contexto_materia, contexto_nivel, contexto_nivel_info
        )

    def generar_retroalimentacion(
        self,
        personaje: str,
        materia: str,
        nivel: int,
        puntaje: int,
        contexto_nivel_info: dict | None = None,
    ) -> dict:
        if not personaje and materia:
            personaje = MATERIA_A_PERSONAJE.get(materia, "")

        tipo_retro = "retroalimentacion_buena" if puntaje >= 60 else "retroalimentacion_regular"

        if self.verificar_disponibilidad():
            prompt_usuario = (
                f"El nino completo el nivel {nivel} de {materia} con {puntaje} puntos de 100. "
                f"Dale una retroalimentacion {'positiva' if puntaje >= 60 else 'motivadora'} "
                "y una recomendacion muy corta para seguir jugando."
            )
            respuesta_ia = self._llamar_ollama(
                personaje,
                prompt_usuario,
                materia,
                nivel,
                contexto_nivel_info,
            )
            if respuesta_ia:
                return {
                    "respuesta": respuesta_ia,
                    "fuente": "ollama",
                    "modelo": self.modelo,
                    "disponible": True,
                    "error": "",
                }

        return self._resultado_fallback(personaje, tipo_retro, materia, nivel, contexto_nivel_info)

    def generar_pista(
        self,
        personaje: str,
        materia: str,
        nivel: int,
        instruccion: str = "",
        minijuego: str = "",
        contexto_nivel_info: dict | None = None,
    ) -> dict:
        if not personaje and materia:
            personaje = MATERIA_A_PERSONAJE.get(materia, "")

        datos_contexto = dict(contexto_nivel_info or {})
        if instruccion:
            datos_contexto["instruccion"] = instruccion
        if minijuego:
            datos_contexto["minijuego"] = minijuego

        prompt_usuario = (
            f"Dame una pista corta para un nino en el nivel {nivel} de {materia}. "
            f"Instruccion del juego: {instruccion or datos_contexto.get('instruccion', '')}. "
            "No des la respuesta completa; solo orienta el primer paso."
        )

        if self.verificar_disponibilidad():
            respuesta_ia = self._llamar_ollama(personaje, prompt_usuario, materia, nivel, datos_contexto)
            if respuesta_ia:
                return {
                    "respuesta": respuesta_ia,
                    "fuente": "ollama",
                    "modelo": self.modelo,
                    "disponible": True,
                    "error": "",
                }

        return self._resultado_fallback(personaje, "pista", materia, nivel, datos_contexto)

    def _llamar_ollama(
        self,
        personaje: str,
        mensaje: str,
        contexto_materia: str = "",
        contexto_nivel: int = 0,
        contexto_nivel_info: dict | None = None,
        system_prompt_override: str | None = None,
        max_tokens: int | None = None,
        normalizar: bool = True,
    ) -> str | None:
        if system_prompt_override:
            system_prompt = system_prompt_override
        else:
            system_prompt = SYSTEM_PROMPTS.get(personaje, SYSTEM_PROMPT_GENERICO)
            contexto_extra = self._construir_contexto_nivel(
                contexto_materia,
                contexto_nivel,
                contexto_nivel_info,
            )
            if contexto_extra:
                system_prompt = f"{system_prompt} Contexto del nivel: {contexto_extra}"
            system_prompt = f"{system_prompt} {REGLAS_RESPUESTA_CORTA}"

        payload = {
            "model": self.modelo,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": mensaje},
            ],
            "stream": False,
            "keep_alive": KEEP_ALIVE,   # mantener modelo en RAM
            "options": {
                "temperature": TEMPERATURA,
                "num_predict": max_tokens if max_tokens is not None else MAX_TOKENS,
                "num_ctx": CONTEXTO_TOKENS,  # ventana 4k = rapida y suficiente
                "top_p": 0.9,
                "repeat_penalty": 1.1,
            },
        }

        try:
            datos_json = json.dumps(payload).encode("utf-8")
            req = urllib_request.Request(
                f"{self.url}/api/chat",
                data=datos_json,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib_request.urlopen(req, timeout=TIMEOUT_SEGUNDOS) as resp:
                resultado = json.loads(resp.read().decode("utf-8"))
                contenido = resultado.get("message", {}).get("content", "").strip()
                if contenido:
                    if normalizar:
                        contenido = self._normalizar_respuesta(contenido)
                    print(f"[IA] Respuesta Ollama ({personaje or 'docente'}): {contenido[:80]}...")
                    return contenido
                self._ultimo_error = "Ollama respondio sin contenido."
                return None
        except (socket.timeout, TimeoutError) as e:
            print(f"[IA] Timeout al llamar Ollama: {e}")
            self._disponible = False
            self._ultimo_error = "Ollama tardo demasiado en responder."
            return None
        except HTTPError as e:
            print(f"[IA] Error HTTP al llamar Ollama: {e}")
            self._disponible = False
            self._ultimo_error = "Ollama rechazo la solicitud o el modelo no esta listo."
            return None
        except (URLError, OSError, Exception) as e:
            print(f"[IA] Error al llamar Ollama: {e}")
            self._disponible = False
            self._ultimo_error = "No pude conectar con Ollama; usare modo de respaldo."
            return None

    def generar_historia_nivel(
        self,
        personaje: str,
        materia: str,
        nivel: int,
        nombre_nivel: str = "",
        instruccion: str = "",
        minijuego: str = "",
        contexto_nivel_info: dict | None = None,
    ) -> dict:
        """
        Devuelve una historia clara, divertida y explicativa para el nivel.

        Decisión de diseño: se usan SIEMPRE las historias predefinidas
        escritas a mano. Los LLMs pequeños (qwen 0.5b, llama 1b) generan
        texto confuso y formal — para un niño de 10 años las historias
        curadas funcionan MUCHO mejor que cualquier LLM ligero.

        Si en el futuro se quiere variedad infinita via IA, basta con
        setear OLLAMA_HISTORIAS=1 en el entorno.
        """
        if not personaje and materia:
            personaje = MATERIA_A_PERSONAJE.get(materia, "")

        usar_ia = os.getenv("OLLAMA_HISTORIAS", "0") == "1"

        if usar_ia and self.verificar_disponibilidad():
            # Modo experimental: dejar que el LLM genere la historia
            desc_minijuego = {
                "atrapa_ranas":  "atrapar los cangrejos con el número correcto antes de que escapen",
                "mate2_pesca":   "arrastrar grupos de peces a la canoa cuya suma sea correcta",
                "mate3_marea":   "observar cuántos caracoles arrastra la marea y elegir cuántos quedan",
                "mate4_tesoro":  "tocar los cofres de conchas que tengan el número exacto pedido",
                "mate5_reparto": "arrastrar peces a las canastas para repartirlos por igual",
            }.get(minijuego, instruccion or "resolver el desafío del nivel")

            prompt = (
                f"Eres {personaje}. Habla con el jugador usando 'tú'. "
                f"Escribe MÁXIMO 3 oraciones cortas y claras para un niño de 10 años:\n"
                f"1. Una escena del Pacífico (mar, manglar, animales).\n"
                f"2. La instrucción exacta: {desc_minijuego}.\n"
                f"3. Una frase motivadora corta.\n"
                f"NO uses: 'niño', 'aventurero', '(historia)', '(misión)', 'lamento', 'lamentamos'."
            )
            system = (
                "Responde SOLO en español de Colombia. Tono claro y alegre para niños. "
                "Sin etiquetas, sin formal, sin disculpas. Máximo 3 oraciones."
            )

            respuesta = self._llamar_ollama(
                personaje=personaje,
                mensaje=prompt,
                system_prompt_override=system,
                max_tokens=220,          # suficiente para no truncar a media frase
                normalizar=False,
            )
            if respuesta:
                historia = _limpiar_historia_ia(respuesta)
                # Validacion estricta: si sigue confusa/truncada, usar curado
                low = historia.lower()
                malo = any(p in low for p in ("lament", "niño", "niña", "pecado", "no tengo", "necesito"))
                # Truncada = no termina en signo de cierre de oracion
                truncada = bool(historia) and historia[-1] not in ".!?…"
                if historia and 50 < len(historia) < 400 and not malo and not truncada:
                    return {
                        "historia": historia,
                        "fuente":   "ollama",
                        "modelo":   self.modelo,
                        "disponible": True,
                        "error": "",
                    }

        # Fuente principal: historias curadas (rápidas, claras, kid-friendly)
        historia = self._historia_fallback(personaje, materia, nivel, nombre_nivel)
        return {
            "historia":   historia,
            "fuente":     "curado",
            "modelo":     self.modelo,
            "disponible": True,
            "error":      "",
        }

    def _historia_fallback(
        self, personaje: str, materia: str, nivel: int, nombre_nivel: str = ""
    ) -> str:
        """
        Historias predefinidas variadas por materia y nivel.
        Escritas a mano: claras, divertidas, en segunda persona, kid-friendly.
        Esta es la fuente PRINCIPAL (mas rapida y mas clara que cualquier LLM pequeno).
        """
        import random as _rand
        historias = {
            # ── MATEMÁTICAS (El Riviel) ────────────────────────────────
            "matematicas": {
                1: [
                    "¡Epa! Soy El Riviel, el espíritu travieso del río Atrato. Esta mañana los cangrejos se escaparon de mi canasta y andan corriendo por todo el muelle como locos, ¡moviendo sus tenazas y echándome agua! Necesito que me ayudes a recogerlos antes de que se metan al manglar. En este nivel yo te diré un número, y tú tienes que tocar solo los cangrejos que lleven ese número encima. ¡Rápido, que son veloces!",
                    "Ay, qué alegría verte por la orilla. Anoche soñé que un montón de cangrejitos salían del río cargando números pintados en el caparazón, ¡y al despertar era verdad! Andan paseando por el muelle muy orgullosos. En este nivel tu trabajo es sencillo pero divertido: yo digo un número y tú tocas únicamente los cangrejos que tengan ese mismo número. ¡A entrenar el ojo, campeón!",
                ],
                2: [
                    "¡Llegaron las canoas! Los pescadores volvieron al amanecer con redes repletas de peces que brillan como monedas de plata. Pero hay un problema: cada canoa solo aguanta una cantidad exacta de peces o se hunde, ¡y nadie quiere nadar con los tiburones! En este nivel vas a sumar los peces de cada grupo y arrastrarlos a la canoa que tenga ese mismo número. Suma bien y mantén el barco a flote. ¡Eres el capitán!",
                    "El muelle huele a mar y a aventura, y tres canoas se mecen esperando su carga de peces. Cada una tiene un número pintado en la madera. En este nivel tu misión es sumar cuántos peces hay en cada grupo y llevarlos a la canoa cuyo número coincida con esa suma. ¡Tu cabeza suma más rápido que cualquier red, ya verás!",
                ],
                3: [
                    "Anoche la marea subió altísima y jugó toda la noche con los caracoles de la playa, llevándose unos cuantos mar adentro entre risas de espuma. ¡Qué traviesa es el agua! Esta mañana quedaron menos. En este nivel vas a mirar cuántos caracoles había, cuántos se llevó la marea, y restar para decirme cuántos quedaron en la arena. ¡Tú tienes el ojo del buen contador!",
                    "El mar es un ladronzuelo simpático: cada noche se lleva prestados algunos caracoles y los devuelve cuando quiere. Hoy se llevó varios de la orilla. En este nivel observa cuántos caracoles había al principio, fíjate cuántos desaparecieron con las olas, y resta para encontrar cuántos siguen brillando en la playa. ¡A restar como todo un explorador!",
                ],
                4: [
                    "¡Shhh, acércate! En el fondo del río descansan cofres antiguos cubiertos de conchas de mil colores, y dicen que guardan el tesoro de los abuelos pescadores. Pero solo se abren con la respuesta correcta. En este nivel yo te diré una multiplicación, y tú debes tocar únicamente el cofre cuyo número sea el resultado exacto. Multiplica con calma y el oro del Pacífico será tuyo. ¡Vamos, valiente buzo!",
                    "El arrecife esconde un secreto brillante: cofres llenos de conchas, cada uno marcado con un número. Solo el que sabe multiplicar puede elegir el correcto. En este nivel resuelve en tu mente la multiplicación que te pido y toca el cofre con el resultado exacto. ¡Demuestra que llevas un matemático adentro!",
                ],
                5: [
                    "¡Qué día de pesca tan bueno! Las redes salieron tan llenas que todo el pueblo del manglar se reunió en la orilla para celebrar. Pero ahora viene lo importante: hay que repartir los peces para que cada familia reciba lo justo, ni más ni menos. En este nivel vas a arrastrar los peces a las canastas para que todas queden con la misma cantidad. ¡La división es compartir parejo, y en el Pacífico nadie se queda con hambre!",
                    "El río fue generoso hoy y regaló más peces de los que cabían en las canastas. Ahora todo el pueblo espera su parte con una sonrisa. En este nivel tu misión es repartir los peces en partes iguales entre todas las canastas, sin que ninguna tenga de más. ¡Divide con justicia y serás el héroe de la fiesta!",
                ],
            },
            # ── LENGUAJE (La Tunda) ────────────────────────────────────
            "lenguaje": {
                1: [
                    "¡Hola, hola! Soy La Tunda, la guardiana de las palabras de la selva. Esta mañana el viento sopló tan fuerte que revolvió todos los sonidos del bosque, ¡y ahora las letras andan jugando a las escondidas entre los dibujos! Necesito tu oído fino. En este nivel yo te mostraré una letra, y tú debes tocar todas las imágenes cuyo nombre empiece con ese sonido. ¡Escucha con los ojos, pequeño explorador!",
                    "La selva amaneció cantando: los pájaros silban, las ranas croan y hasta el río murmura palabras. Entre tanto sonido se escondieron unas letras juguetonas. En este nivel te enseñaré una letra y tú tendrás que encontrar y tocar los dibujos cuyo nombre comience con ella. ¡Es como una cacería de sonidos por todo el manglar!",
                ],
                2: [
                    "¡Ay, qué desorden! Las mariposas del bosque pasaron volando y se robaron las sílabas de mis palabras, dejándolas todas en pedacitos regados por el suelo. Una palabra rota no puede cantar. En este nivel tu misión es arrastrar cada sílaba a su lugar correcto, en orden, hasta armar la palabra completa. ¡Tú eres el constructor de palabras de la selva!",
                    "Las palabras del manglar viajan en pedacitos llamados sílabas, y hoy una palabra muy importante se desarmó en la corriente del río. Si no la armamos, la selva se quedará callada. En este nivel vas a unir las sílabas en el orden correcto, arrastrándolas una por una, para que la palabra vuelva a tener sentido. ¡Sílaba por sílaba lo lograrás!",
                ],
                3: [
                    "Pobrecito el animalito del bosque: una tormenta se llevó un pedacito de su nombre y ahora nadie sabe cómo llamarlo, ¡anda triste y perdido entre los árboles! Tú puedes devolverle su nombre. En este nivel mira la palabra incompleta, busca entre las opciones la sílaba que falta, y arrástrala al hueco para completarla. ¡Él te lo agradecerá con un canto!",
                    "El viento travieso se llevó una sílaba de cada palabra y dejó huecos por toda la selva, como dientes que faltan en una sonrisa. En este nivel tu trabajo es encontrar la sílaba exacta que completa cada palabra y ponerla en su lugar. ¡Cuando la palabra esté entera, el bosque volverá a cantar feliz!",
                ],
                4: [
                    "¡Qué lío armó el remolino del río! Tomó una oración bien bonita sobre el Pacífico y la sacudió hasta dejar todas las palabras revueltas, flotando sin orden como hojas en el agua. En este nivel tu misión es arrastrar las palabras y acomodarlas en el orden correcto para que la oración tenga sentido otra vez. ¡Tú eres el narrador que pone todo en su sitio!",
                    "Las palabras de una historia preciosa se mezclaron cuando la brisa pasó corriendo por el manglar, y ahora la frase no se entiende ni un poquito. En este nivel vas a ordenar las palabras, una tras otra, hasta formar una oración que suene bonita y tenga sentido. ¡Solo un buen escritor del Pacífico como tú puede lograrlo!",
                ],
                5: [
                    "El Duende del bosque escondió palabras mágicas detrás de los dibujos del manglar, ¡y le encanta retar a los más curiosos! ¿Aceptas el reto? En este nivel yo te diré una palabra y tú deberás tocar la imagen que le corresponde. Cada acierto agranda el gran libro de palabras que llevas en la cabeza. ¡A demostrar cuánto vocabulario tienes!",
                    "Cada criatura y cada cosa del Pacífico tiene un nombre que guarda su historia, y hoy vamos a jugar a reconocerlos. En este nivel te diré una palabra y tú tocarás el dibujo correcto entre varios. ¡Mientras más palabras reconozcas, más sabio te vuelves, explorador!",
                ],
            },
            # ── INGLÉS (El Duende) ─────────────────────────────────────
            "ingles": {
                1: [
                    "Hi! Soy El Duende, el más viajero de todo el Pacífico, ¡y traje palabras nuevas desde el otro lado del mar! En inglés, los animales del manglar tienen otros nombres muy divertidos: el pez es 'fish' y el cangrejo es 'crab'. En este nivel yo te diré una palabra en inglés y tú tocarás la imagen correcta. ¡Vas a hablar como un explorador del mundo entero!",
                    "¡Hello, amigo! Me encanta viajar en canoa contando historias en dos idiomas. Hoy quiero enseñarte los nombres secretos de las cosas en inglés. En este nivel te mostraré una palabra en inglés y tú deberás tocar el dibujo que le corresponde. ¡Cada acierto te acerca a hablar como un verdadero aventurero internacional!",
                ],
                2: [
                    "¡Mira qué colorido amaneció el manglar! Las flores, los peces y las canoas pintan el Pacífico de mil colores, y en inglés cada color tiene su nombre: 'red' es rojo, 'blue' es azul, 'green' es verde. En este nivel yo diré un color en inglés y tú tocarás el objeto que tenga ese color. ¡Pinta tu mundo en inglés, my friend!",
                    "Los colores son la fiesta del Pacífico, y hoy aprenderemos a nombrarlos en inglés. En este nivel te diré un color en inglés y tú buscarás y tocarás el objeto que lo tenga. ¡Cada color que reconozcas es una pequeña victoria de campeón!",
                ],
                3: [
                    "¿Sabías que los números también hablan inglés? 'One, two, three...' suenan distinto pero cuentan lo mismo. Los animales del manglar quieren jugar a contarse contigo. En este nivel yo diré un número en inglés y tú tocarás el grupo de animales que tenga esa cantidad. ¡A contar en inglés con valentía!",
                    "¡A jugar con los números en inglés! En el Pacífico hasta los pelícanos cuentan sus peces. En este nivel te diré un número en inglés, como 'four' o 'five', y tú buscarás el grupo que tenga esa cantidad exacta de cosas. ¡La selva tiene mucho que enseñarte en otro idioma!",
                ],
                4: [
                    "El Duende organizado tiene un baúl mágico con tres cajones: uno para animales, otro para colores y otro para frutas, ¡pero todo se mezcló! En este nivel yo te mostraré una palabra en inglés y tú la arrastrarás al grupo al que pertenece: 'animals', 'colors' o 'fruits'. ¡Ordena el mundo en inglés y serás mi ayudante favorito!",
                    "Las palabras en inglés viven en familias: las frutas con las frutas, los animales con los animales. Hoy se nos revolvieron todas. En este nivel vas a arrastrar cada palabra en inglés al grupo correcto. ¡Tú entiendes el idioma de la gran aventura!",
                ],
                5: [
                    "¡Casi eres todo un explorador bilingüe! Solo falta el reto final: unas frases cortas en inglés perdieron una palabra en el viento del mar. En este nivel vas a leer la frase incompleta y elegir la palabra correcta para terminarla. ¡Cuando lo logres, podrás conversar con cualquier marinero del mundo!",
                    "El último tesoro del idioma son las frases completas. Algunas se quedaron sin una palabra y no se entienden bien. En este nivel tu misión es completar cada frase en inglés escogiendo la palabra que falta. ¡Forma frases como un verdadero capitán del Pacífico!",
                ],
            },
            # ── BIOLOGÍA (La Madre de Agua) ────────────────────────────
            "biologia": {
                1: [
                    "Soy La Madre de Agua, la que cuida cada gota y cada criatura del manglar. Mira a tu alrededor: hay peces que nadan, cangrejos que corren, aves que cantan y plantas que crecen... pero también piedras, canoas y conchas vacías que no están vivas. En este nivel vas a tocar solamente los seres vivos, los que respiran y crecen. ¡Aprende a ver quién tiene vida en el Pacífico!",
                    "El manglar entero respira como un gran corazón verde, lleno de vida por todos lados. Pero no todo lo que ves está vivo: hay cosas que solo descansan quietas. En este nivel tu misión es observar bien y tocar únicamente los seres vivos. ¡Conviértete en el guardián que distingue la vida!",
                ],
                2: [
                    "Tengo hambre... ¡y todos mis animales también! Cada criatura del manglar come algo diferente: el pez busca su plancton, el cangrejo rasca la arena y el pájaro picotea los frutos. En este nivel vas a arrastrar cada animal hasta la comida que le gusta. ¡Así descubrirás la maravillosa cadena de la vida del Pacífico!",
                    "En el manglar hay un gran banquete y cada quien tiene su plato favorito, pero hoy todos andan confundidos buscando qué comer. En este nivel tu trabajo es unir cada animal con su alimento correcto, arrastrándolo hasta él. ¡Serás un verdadero biólogo que entiende cómo se alimenta la naturaleza!",
                ],
                3: [
                    "Cada criatura del Pacífico tiene su hogar: el pez vive en el agua, el mono en los árboles y el cangrejo en la arena tibia. ¡Pero hoy todos se perdieron y no encuentran su casa! En este nivel vas a arrastrar a cada animal hasta el lugar donde vive. ¡Ayúdalos a volver a casa y conocerás los rincones del manglar!",
                    "El manglar tiene muchos hogares distintos: el agua, los árboles y la tierra húmeda. Una tormenta despistó a los animalitos y ya no saben adónde ir. En este nivel tu misión es llevar a cada criatura a su hábitat correcto. ¡Cada quien tiene su lugar en la naturaleza, y tú los guiarás!",
                ],
                4: [
                    "Las plantas del manglar son sabias y tienen partes con nombres especiales: la raíz que bebe agua, el tallo que sostiene, las hojas que respiran, la flor que perfuma y el fruto que alimenta. En este nivel yo diré el nombre de una parte y tú tocarás esa parte de la planta. ¡La botánica es pura vida, y tú la vas a descubrir!",
                    "¡Acércate a esta planta del Pacífico! Como tú, ella tiene partes que cumplen su función: raíz, tallo, hojas, flor y fruto. En este nivel te diré el nombre de una parte y tú deberás encontrarla y tocarla. ¡Las plantas son fascinantes cuando aprendes a mirarlas con cuidado!",
                ],
                5: [
                    "Tengo que contarte algo importante: algunos animales del Pacífico están en peligro y necesitan que los conozcamos para poder cuidarlos. Tú puedes ser su guardián. En este nivel yo te diré el nombre de un animal y tú tocarás su imagen correcta. ¡Cuidar la naturaleza empieza por aprender quién vive en ella!",
                    "Cada animal del Pacífico guarda una historia, y algunos están desapareciendo del manglar. Conocerlos es el primer paso para protegerlos. En este nivel deberás identificar y tocar el animal correcto según el nombre que te diga. ¡Tú eres el guardián del futuro de nuestra tierra!",
                ],
            },
        }
        niveles_mat = historias.get(materia, {})
        opciones = niveles_mat.get(nivel) or [
            f"¡Hola! El nivel '{nombre_nivel or nivel}' te está esperando. Lee la instrucción con calma y demuestra lo que sabes. ¡Tú puedes!"
        ]
        return _rand.choice(opciones)

    def generar_reporte_docente(
        self,
        desempeno: dict,
        ambito: str,
        nombre: str = '',
    ) -> dict:
        """
        Genera un reporte pedagógico para el docente a partir del desempeño
        calculado por la base de datos.
        Si Ollama no está disponible, usa el análisis determinista offline.

        Args:
            desempeno: dict de obtener_desempeno_estudiante() o obtener_desempeno_clase().
            ambito:    'estudiante' | 'clase'
            nombre:    Nombre del estudiante (solo para ámbito 'estudiante').
        """
        if not self.verificar_disponibilidad():
            reporte = generar_reporte_fallback(desempeno, ambito)
            return {
                "respuesta":  reporte,
                "fuente":     "fallback",
                "modelo":     self.modelo,
                "disponible": False,
                "error":      self._ultimo_error,
            }

        resumen = _construir_resumen_desempeno(desempeno, ambito, nombre)
        prompt = (
            f"DATOS DEL ESTUDIANTE (ya tienes toda la informacion necesaria, NO pidas mas):\n"
            f"{resumen}\n\n"
            f"INSTRUCCION: Con los datos de arriba, escribe un reporte pedagogico breve "
            f"para el docente. No pidas mas informacion. Usa los datos tal cual estan.\n\n"
            f"Estructura del reporte (escribela tal cual, llenando con los datos):\n"
            f"1. Resumen: una linea con el promedio general y el nivel completado.\n"
            f"2. Fortalezas: 1-2 puntos basados en las materias con mejor desempeno.\n"
            f"3. Dificultades: 1-2 puntos basados en las materias o temas con peor desempeno. "
            f"Si no hay dificultades, escribe 'No se detectan dificultades importantes'.\n"
            f"4. Recomendaciones pedagogicas: 3 acciones concretas para el docente.\n\n"
            f"Responde directamente con el reporte, sin saludos ni preguntas."
        )
        system = (
            f"{SYSTEM_PROMPT_DOCENTE} {REGLAS_REPORTE_DOCENTE} "
            f"NUNCA pidas mas informacion al usuario. NUNCA digas 'lo siento' o 'necesito mas datos'. "
            f"Usa SOLO los datos que te dan en el mensaje. Si los datos son escasos, igualmente genera el reporte."
        )

        respuesta = self._llamar_ollama(
            personaje="",
            mensaje=prompt,
            system_prompt_override=system,
            max_tokens=400,
            normalizar=False,
        )

        # Validar la respuesta: si el modelo "alucina pidiendo datos", caer al fallback
        respuesta_invalida = False
        if respuesta:
            r_lower = respuesta.lower()
            frases_malas = [
                "lo siento", "necesitaria", "necesitaría", "necesito mas",
                "necesito más", "podrias proporcionar", "podrías proporcionar",
                "puedes proporcionarme", "puedes darme", "no tengo informacion",
                "no tengo información", "no se proporciono", "no se proporcionó",
                "mas detalles", "más detalles", "mas informacion", "más información",
            ]
            if any(f in r_lower for f in frases_malas):
                respuesta_invalida = True
                print(f"[IA] Reporte rechazado (modelo pidio mas datos): {respuesta[:100]}...")

        if respuesta and not respuesta_invalida:
            return {
                "respuesta":  respuesta,
                "fuente":     "ollama",
                "modelo":     self.modelo,
                "disponible": True,
                "error":      "",
            }

        # Fallback determinista basado solo en los datos de la DB
        reporte = generar_reporte_fallback(desempeno, ambito)
        return {
            "respuesta":  reporte,
            "fuente":     "fallback",
            "modelo":     self.modelo,
            "disponible": False,
            "error":      self._ultimo_error or "Modelo no genero reporte util",
        }

    def _normalizar_respuesta(self, texto: str) -> str:
        limpio = " ".join(str(texto).split())
        partes = _separar_oraciones(limpio)
        if len(partes) > 3:
            return " ".join(partes[:3])
        return limpio


def _construir_resumen_desempeno(desempeno: dict, ambito: str, nombre: str = '') -> str:
    """Genera texto resumido y legible del desempeno para incluir en el prompt."""
    NOMBRES_MAT = {
        'matematicas': 'Matemáticas',
        'lenguaje':    'Lenguaje',
        'ingles':      'Inglés',
        'biologia':    'Biología',
    }
    lineas = []

    if ambito == 'clase':
        total = desempeno.get('total_estudiantes', 0)
        lineas.append(f"AMBITO: Clase completa con {total} estudiantes activos.")
    else:
        nom = nombre or desempeno.get('nombre', 'Estudiante')
        lineas.append(f"ESTUDIANTE: {nom}")

    por_materia = desempeno.get('por_materia') or {}
    if por_materia:
        # Promedio general
        promedios = [d.get('promedio_puntaje', 0) for d in por_materia.values()]
        prom_general = sum(promedios) / len(promedios) if promedios else 0
        lineas.append(f"PROMEDIO GENERAL: {prom_general:.0f}/100")

        lineas.append("DESEMPENO POR MATERIA:")
        for mat, d in sorted(por_materia.items(), key=lambda x: x[1].get('promedio_puntaje', 0), reverse=True):
            nom_mat = NOMBRES_MAT.get(mat, mat.capitalize())
            prom = d.get('promedio_puntaje', 0)
            niv  = d.get('niveles_completados') or d.get('estudiantes') or 0
            terr = d.get('tasa_error', 0)
            etiqueta_nivel = 'niveles completados' if ambito == 'estudiante' else 'estudiantes participantes'
            categoria = ('FUERTE' if prom >= 80 else 'REGULAR' if prom >= 60 else 'DEBIL')
            lineas.append(
                f"  - {nom_mat} [{categoria}]: puntaje {prom:.0f}/100, "
                f"{niv} {etiqueta_nivel}, tasa de error {int(terr*100)}%"
            )
    else:
        lineas.append("NOTA: Aun no hay materias con desempeno registrado.")

    por_tema = desempeno.get('por_tema') or {}
    if por_tema:
        temas_bajos = {t: d for t, d in por_tema.items() if d.get('promedio_puntaje', 100) < 70}
        if temas_bajos:
            lineas.append("TEMAS CON DIFICULTAD (puntaje < 70):")
            for tema, d in sorted(temas_bajos.items(), key=lambda x: x[1].get('promedio_puntaje', 100))[:6]:
                lineas.append(f"  - {tema}: {d.get('promedio_puntaje', 0):.0f}/100")
        else:
            lineas.append("TEMAS CON DIFICULTAD: ninguno (todos los temas registrados estan por encima de 70).")

    return '\n'.join(lineas)


def _limpiar_historia_ia(texto: str) -> str:
    """
    Limpia una historia generada por IA para uso experimental:
    - Quita markdown y etiquetas (reusa _limpiar_markdown).
    - Elimina preambulos tipo '¡Hola, amigo! Eres X y aqui tienes una aventura'.
    - Fusiona listas numeradas (1. 2. 3.) en texto corrido fluido.
    """
    import re
    texto = _limpiar_markdown(texto)
    # Quitar prefijos de lista numerada al inicio de cada parte: "1. ", "2) ", etc.
    texto = re.sub(r'(?m)^\s*\d+\s*[\.\)\-]\s*', '', texto)
    # Quitar preambulos genericos comunes del modelo
    preambulos = [
        r'^¡?hola[^.!?]*[.!?]\s*',
        r'^eres\s+[^.!?]*aventura[^.!?]*[.!?]\s*',
        r'^aqu[ií]\s+tienes[^.!?]*[.!?]\s*',
        r'^soy\s+[^.!?]*[.!?]\s*',
    ]
    for p in preambulos:
        texto = re.sub(p, '', texto, flags=re.IGNORECASE)
    # Colapsar saltos y espacios
    texto = re.sub(r'\s+', ' ', texto).strip()
    # Quitar numeros sueltos al final ("... para ti. 1") o residuos
    texto = re.sub(r'\s*\d+\s*$', '', texto).strip()
    return texto


def _limpiar_markdown(texto: str) -> str:
    """Elimina marcadores Markdown y etiquetas estructurales que Ollama inserta."""
    import re
    # Quitar **negrita**, *cursiva*, __subrayado__
    texto = re.sub(r'\*{1,2}([^*]+)\*{1,2}', r'\1', texto)
    texto = re.sub(r'_{1,2}([^_]+)_{1,2}', r'\1', texto)
    # Quitar etiquetas estructurales: PARTE 1, (historia), (misión), [historia], etc.
    texto = re.sub(r'(?i)\bparte\s*\d+\s*[:\-–)]*\s*', '', texto)
    texto = re.sub(r'(?i)[\(\[\{]\s*(historia|misi[oó]n|narrativa|narracion|explicaci[oó]n|introducci[oó]n)\s*[\)\]\}]\s*:?\s*', '', texto)
    texto = re.sub(r'(?im)^\s*(historia|misi[oó]n|narrativa|explicaci[oó]n|introducci[oó]n)\s*:\s*', '', texto)
    # Quitar prefijos de lista (*, -, •) al inicio de línea
    texto = re.sub(r'(?m)^[\*\-•]\s+', '', texto)
    # Quitar almohadillas de encabezado
    texto = re.sub(r'(?m)^#+\s*', '', texto)
    # Reemplazar referencias en tercera persona por segunda persona ("tú")
    # Esto corrige cuando el modelo ignora la instrucción y escribe "el niño..."
    sustituciones = [
        (r'\b[Eel]l ni[ñn]o\b',           'tú'),
        (r'\bla ni[ñn]a\b',               'tú'),
        (r'\b[Eel]l peque[ñn]o aventurero\b', 'tú'),
        (r'\b[Eel]l peque[ñn]o\b',        'tú'),
        (r'\b[Aa]venturero\b',            ''),
    ]
    for patron, repl in sustituciones:
        texto = re.sub(patron, repl, texto)
    # Colapsar espacios múltiples y saltos de línea dobles
    texto = re.sub(r'\n{2,}', ' ', texto)
    texto = re.sub(r' {2,}', ' ', texto)
    return texto.strip()


def _separar_oraciones(texto: str) -> list[str]:
    partes = []
    inicio = 0
    for i, ch in enumerate(texto):
        if ch in ".!?":
            frag = texto[inicio:i + 1].strip()
            if frag:
                partes.append(frag)
            inicio = i + 1
    resto = texto[inicio:].strip()
    if resto:
        partes.append(resto)
    return partes or [texto]


servicio_ia = ServicioIA()
