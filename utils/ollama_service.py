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
TIMEOUT_SEGUNDOS = 8
MAX_TOKENS = 120
TEMPERATURA = 0.7
CACHE_MAX = 30


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
