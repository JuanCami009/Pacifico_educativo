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
MODELO_DEFECTO = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
MODELO_RESPALDO = "tinyllama"
TIMEOUT_SEGUNDOS = 40        # llama3.2:1b necesita ~15-25s. qwen2.5:0.5b ~3-6s
MAX_TOKENS = 80              # mas corto = MUCHO mas rapido. Antes 120
TEMPERATURA = 0.7
CACHE_MAX = 30
KEEP_ALIVE = "10m"           # mantener el modelo en RAM 10 min entre llamadas


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
            "keep_alive": KEEP_ALIVE,   # mantener modelo en RAM 10 min
            "options": {
                "temperature": TEMPERATURA,
                "num_predict": max_tokens if max_tokens is not None else MAX_TOKENS,
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
                max_tokens=120,
                normalizar=False,
            )
            if respuesta:
                respuesta = _limpiar_markdown(respuesta)
                partes = _separar_oraciones(respuesta)
                historia = " ".join(partes[:3])
                # Si el texto sigue siendo confuso (muy largo o con palabras prohibidas),
                # caer al fallback curado
                if (len(historia) > 60 and len(historia) < 380
                        and "lament" not in historia.lower()
                        and "niño" not in historia.lower()):
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
            # ── MATEMÁTICAS ────────────────────────────────────────────
            "matematicas": {
                1: [
                    "¡Hola! Soy El Riviel, espíritu del río. Mira: los cangrejos salieron a pasear por el muelle y necesito tu ayuda. Atrapa SOLO los cangrejos que tengan el número que yo te diga. ¡Tócalos rápido antes de que se metan al agua!",
                    "El sol salió sobre el manglar y los cangrejitos corren por la arena. Tu misión: tocar únicamente los cangrejos que tengan el número correcto. ¡Sé rápido, valiente!",
                    "¡Qué bueno verte! Los cangrejos están jugando carreras en la orilla. Yo te diré un número y tú debes tocar SOLO los cangrejos que lo lleven encima. ¡Ánimo, tú puedes!",
                ],
                2: [
                    "Los pescadores volvieron con canoas llenas de peces brillantes. Cada canoa necesita una cantidad exacta de peces para no hundirse. Tu misión: arrastrar los grupos de peces a la canoa cuyo número coincida con la SUMA del grupo. ¡A pescar matemáticas!",
                    "El muelle está lleno de peces saltarines y tres canoas esperan su carga. Suma los peces de cada grupo y arrástralos a la canoa que tenga el número correcto. ¡Tú eres el capitán hoy!",
                    "¡Mira cuántos peces! Cada canoa tiene un número escrito. Suma los peces del grupo y llévalo a la canoa que tenga esa misma cantidad. ¡Tu cerebro pesca mejor que cualquier red!",
                ],
                3: [
                    "La marea subió y se llevó algunos caracoles de la playa. Mira cuántos había al inicio, mira cuántos se llevó el agua, y dime cuántos quedaron. ¡Es una resta marina!",
                    "Anoche las olas jugaron con los caracoles y se llevaron unos cuantos. Resta los que se fueron y descubre cuántos siguen brillando en la arena. ¡Cuenta con calma!",
                    "El mar se llevó parte del tesoro de la playa. Observa cuántos caracoles había y cuántos faltan ahora — ¡la resta te dirá el resto! Tú decides el número final.",
                ],
                4: [
                    "El fondo del río esconde cofres cubiertos de conchas brillantes. Cada cofre tiene un número. Yo te diré la multiplicación y tú debes tocar SOLO el cofre cuyo número sea la respuesta correcta. ¡Multiplica como un maestro!",
                    "¡Tesoros! Los cofres del manglar tienen números pintados. Calcula la multiplicación que te pido y toca el cofre con el resultado exacto. ¡El oro del Pacífico será tuyo!",
                    "Bajo el agua descansan cofres llenos de conchas. Cada uno tiene un número. Resuelve la multiplicación en tu mente y toca el cofre correcto. ¡Demuestra que sabes multiplicar!",
                ],
                5: [
                    "El día de pesca fue increíble y todo el pueblo espera su parte. Tu trabajo: arrastrar los peces a las canastas para que CADA familia reciba la misma cantidad. ¡La división es repartir parejo!",
                    "¡Hay tantos peces! Reparte los peces en partes iguales entre las canastas. Cuando todas tengan lo mismo, el pueblo te aplaudirá. ¡Divide con justicia!",
                    "Las canastas vacías esperan los peces. Cuenta cuántos peces hay y repártelos parejo entre todas las canastas. ¡En el Pacífico, lo justo es compartir!",
                ],
            },
            # ── LENGUAJE ───────────────────────────────────────────────
            "lenguaje": {
                1: [
                    "¡Hola! Soy La Tunda, guardiana de las palabras. Te muestro una letra y tú debes tocar TODAS las imágenes cuyo nombre empiece con esa letra. ¡Escucha con los ojos!",
                    "Los animales del manglar quieren jugar contigo. Mira la letra que te enseño y toca solo los dibujos cuyo nombre comience con esa letra. ¡Es como un tesoro de sonidos!",
                    "La selva está llena de palabras escondidas. Yo te doy una letra y tú encuentras los dibujos que empiecen así. ¡Tus oídos y tus ojos son tu mejor herramienta!",
                ],
                2: [
                    "Las palabras viajan en pedacitos por el río y se llaman sílabas. Tu tarea: arrastrar cada sílaba a su lugar correcto para formar la palabra completa. ¡Tú eres el constructor de palabras!",
                    "Una palabra mágica se rompió en sílabas. Arrástralas en el orden correcto y la palabra cobrará vida. ¡Vamos, sílaba por sílaba!",
                    "Las sílabas están desordenadas como peces nadando sueltos. Ponlas en su sitio una por una y formarás la palabra correcta. ¡La selva esperará tu canción!",
                ],
                3: [
                    "Un animal del bosque perdió una sílaba de su nombre. Mira las opciones, elige la sílaba correcta y arrástrala al hueco para completar su nombre. ¡Él te lo agradecerá!",
                    "La palabra le falta un pedacito. Tu trabajo: encontrar la sílaba que falta y arrastrarla al espacio vacío. ¡Cuando esté completa, la selva sonreirá!",
                    "¡Mira la palabra incompleta! Una sílaba se perdió. Búscala entre las opciones y ponla en su lugar para que la palabra sea perfecta.",
                ],
                4: [
                    "Las palabras de una oración están todas revueltas. Tu misión: ordenarlas correctamente arrastrándolas para formar una oración que tenga sentido. ¡Ponlas en su sitio!",
                    "Una historia bonita se mezcló por el viento. Arrastra las palabras en el orden correcto y formarás una oración hermosa. ¡Tú eres el escritor del Pacífico!",
                    "Las palabras flotan sin orden como hojas en el río. Acomódalas correctamente para construir la oración. ¡Solo tú puedes hacer que tenga sentido!",
                ],
                5: [
                    "Yo te digo una palabra y tú tocas la imagen que corresponde. ¡Vamos a descubrir cuántas palabras conoces!",
                    "Te muestro varias imágenes y te digo una palabra. Toca la imagen correcta y demostrarás tu vocabulario del Pacífico. ¡A ver qué tan listo eres!",
                    "Mira bien las imágenes. Yo digo una palabra y tú encuentras a qué dibujo corresponde. ¡Cada acierto suma al gran libro de tus palabras!",
                ],
            },
            # ── INGLÉS ─────────────────────────────────────────────────
            "ingles": {
                1: [
                    "Hi! Soy El Duende y te voy a enseñar palabras en inglés. Te muestro una palabra como 'fish' o 'crab' y tú tocas la imagen correcta. ¡Aprender es divertido!",
                    "¡Hello! Los animales del manglar tienen nombres en inglés. Toca la imagen que corresponde a la palabra que te digo. ¡Tú puedes hablar como un explorador!",
                ],
                2: [
                    "Los colores del Pacífico son hermosos. Yo te digo un color en inglés ('red', 'blue', 'green'...) y tú tocas el objeto que tenga ese color. ¡Pinta tu mundo en inglés!",
                    "Mira los objetos de mil colores. Te digo el color en inglés y tú lo encuentras. ¡Cada acierto es una victoria, my friend!",
                ],
                3: [
                    "Los números también tienen nombre en inglés: 'one, two, three...'. Yo te digo un número en inglés y tú tocas el grupo de animales con esa cantidad. ¡Cuenta con valentía!",
                    "¡A contar en inglés! Te digo 'four' y tú buscas el grupo de cuatro objetos. ¡La selva tiene mucho que enseñarte en inglés!",
                ],
                4: [
                    "Cada cosa tiene su lugar. Yo te muestro una palabra en inglés y tú arrastras el objeto a la categoría correcta (frutas, animales, colores...). ¡Organiza el mundo en inglés!",
                    "Las palabras viven en grupos. Arrastra cada palabra al grupo al que pertenece (animals, colors, fruits). ¡Tú entiendes el idioma de la aventura!",
                ],
                5: [
                    "Frases cortas en inglés perdieron una palabra. Tú eliges la palabra correcta para completarla. ¡Forma frases como un verdadero pirata del Pacífico!",
                    "Lee la frase incompleta en inglés y arrastra la palabra que falta. ¡Cuando la termines, podrás hablar con cualquier marinero del mundo!",
                ],
            },
            # ── BIOLOGÍA ───────────────────────────────────────────────
            "biologia": {
                1: [
                    "¡Hola! Soy La Madre de Agua. El manglar está lleno de seres vivos: peces, cangrejos, aves, plantas. Tu misión: tocar SOLO los seres vivos (no las piedras ni los objetos). ¡A descubrir la vida!",
                    "El manglar respira. Mira a tu alrededor y toca los seres vivos que veas — pero ten cuidado, no todo lo que se mueve está vivo. ¡Aprende a observar!",
                ],
                2: [
                    "Cada animal tiene su comida favorita. Arrastra cada animal a la comida que come (el pez al plancton, el cangrejo a la arena, el pájaro a los frutos...). ¡La cadena de la vida es maravillosa!",
                    "En el manglar todos comen algo distinto. Arrastra cada animal a su comida correcta y entenderás cómo se mantienen vivos. ¡Eres un biólogo del Pacífico!",
                ],
                3: [
                    "Los animales viven en lugares diferentes: el agua, los árboles, la tierra. Arrastra cada animal a su hábitat correcto. ¡Cada quien tiene su casa en la naturaleza!",
                    "Tu misión: poner cada criatura en el lugar donde vive. Pez al agua, mono al árbol, cangrejo a la arena. ¡Conoce los hogares del Pacífico!",
                ],
                4: [
                    "Las plantas del Pacífico tienen partes: raíz, tallo, hojas, flor, fruto. Yo te muestro un nombre y tú tocas la parte correcta de la planta. ¡La botánica es vida!",
                    "Mira esta planta del manglar. Yo digo el nombre de una parte y tú la encuentras. ¡Las plantas son fascinantes!",
                ],
                5: [
                    "Algunos animales del Pacífico están en peligro. Aprende sobre ellos: yo te digo un nombre y tú tocas la imagen del animal correcto. ¡Cuidar la naturaleza empieza por conocerla!",
                    "Cada animal del Pacífico tiene su historia. Identifica cuál es cuál y aprende a proteger nuestro hogar. ¡Tú eres el guardián del futuro!",
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
            f"Analiza el siguiente desempeno estudiantil y genera un reporte "
            f"pedagogico para el docente:\n\n{resumen}\n\n"
            f"Incluye: diagnostico de dificultades, fortalezas observadas "
            f"y 3 recomendaciones pedagogicas especificas."
        )
        system = f"{SYSTEM_PROMPT_DOCENTE} {REGLAS_REPORTE_DOCENTE}"

        respuesta = self._llamar_ollama(
            personaje="",
            mensaje=prompt,
            system_prompt_override=system,
            max_tokens=400,
            normalizar=False,
        )

        if respuesta:
            return {
                "respuesta":  respuesta,
                "fuente":     "ollama",
                "modelo":     self.modelo,
                "disponible": True,
                "error":      "",
            }

        reporte = generar_reporte_fallback(desempeno, ambito)
        return {
            "respuesta":  reporte,
            "fuente":     "fallback",
            "modelo":     self.modelo,
            "disponible": False,
            "error":      self._ultimo_error,
        }

    def _normalizar_respuesta(self, texto: str) -> str:
        limpio = " ".join(str(texto).split())
        partes = _separar_oraciones(limpio)
        if len(partes) > 3:
            return " ".join(partes[:3])
        return limpio


def _construir_resumen_desempeno(desempeno: dict, ambito: str, nombre: str = '') -> str:
    """Genera texto resumido del desempeño para incluir en el prompt de Ollama."""
    lineas = []

    if ambito == 'clase':
        total = desempeno.get('total_estudiantes', 0)
        lineas.append(f"Clase completa ({total} estudiantes):")
    else:
        nom = nombre or desempeno.get('nombre', 'Estudiante')
        lineas.append(f"Estudiante: {nom}")

    por_materia = desempeno.get('por_materia', {})
    if por_materia:
        lineas.append("Desempeno por materia (promedio/100):")
        for mat, d in sorted(por_materia.items(), key=lambda x: x[1].get('promedio_puntaje', 0)):
            prom = d.get('promedio_puntaje', 0)
            niv  = d.get('niveles_completados') or d.get('estudiantes') or 0
            terr = d.get('tasa_error', 0)
            lineas.append(f"  - {mat}: {prom:.0f}/100, {niv} niveles, tasa error {terr:.0%}")

    por_tema = desempeno.get('por_tema', {})
    if por_tema:
        temas_bajos = {t: d for t, d in por_tema.items() if d.get('promedio_puntaje', 100) < 60}
        if temas_bajos:
            lineas.append("Temas con mayor dificultad (promedio < 60):")
            for tema, d in sorted(temas_bajos.items(), key=lambda x: x[1].get('promedio_puntaje', 100)):
                lineas.append(f"  - {tema}: {d.get('promedio_puntaje', 0):.0f}/100")

    if not por_materia:
        lineas.append("Sin datos de desempeno registrados aun.")

    return '\n'.join(lineas)


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
