"""
ollama_service.py - Servicio de IA local usando Ollama.
Gestiona la comunicación con el modelo TinyLlama para generar respuestas
educativas en el juego Pacífico Educativo.
Incluye fallback automático si Ollama no está disponible.
"""

import json
import time
import threading
from urllib import request as urllib_request
from urllib.error import URLError
from collections import OrderedDict

from data.ia_fallback import (
    obtener_respuesta_fallback,
    clasificar_mensaje,
    MATERIA_A_PERSONAJE,
)


# ── Configuración ────────────────────────────────────────────────────────────

OLLAMA_URL = "http://localhost:11434"
MODELO_DEFECTO = "tinyllama"
TIMEOUT_SEGUNDOS = 8
MAX_TOKENS = 120
TEMPERATURA = 0.7
CACHE_MAX = 30


# ── System prompts por personaje ─────────────────────────────────────────────

SYSTEM_PROMPTS = {
    "El Riviel": (
        "Eres El Riviel, un espíritu sabio del río Pacífico colombiano. "
        "Hablas con niños de 8 a 12 años. Enseñas matemáticas usando ejemplos "
        "del río, cangrejos, peces y canoas. Responde SIEMPRE en español. "
        "Máximo 2 oraciones cortas. Usa emojis. Sé amigable y motivador."
    ),
    "La Tunda": (
        "Eres La Tunda, guardiana mística del bosque del Pacífico colombiano. "
        "Hablas con niños de 8 a 12 años. Enseñas lenguaje usando ejemplos "
        "del bosque, árboles, pájaros y la selva. Responde SIEMPRE en español. "
        "Máximo 2 oraciones cortas. Usa emojis. Sé amigable y motivadora."
    ),
    "El Duende": (
        "Eres El Duende, un personaje mágico que enseña inglés a niños "
        "colombianos de 8 a 12 años. Mezclas español e inglés de forma divertida. "
        "Usas vocabulario básico en inglés con traducción. "
        "Máximo 2 oraciones cortas. Usa emojis. Sé divertido y motivador."
    ),
    "La Madre de Agua": (
        "Eres La Madre de Agua, protectora de la vida acuática del Pacífico "
        "colombiano. Hablas con niños de 8 a 12 años. Enseñas biología usando "
        "ejemplos del manglar, ballenas, peces y el ecosistema. "
        "Responde SIEMPRE en español. Máximo 2 oraciones cortas. Usa emojis. "
        "Sé amigable y sabia."
    ),
}

SYSTEM_PROMPT_GENERICO = (
    "Eres un personaje amigable del juego educativo Pacífico Educativo. "
    "Hablas con niños de 8 a 12 años del Pacífico colombiano. "
    "Responde SIEMPRE en español. Máximo 2 oraciones cortas. "
    "Usa emojis. Sé amigable y motivador."
)


# ── Caché simple en memoria ─────────────────────────────────────────────────

class CacheIA:
    """Caché LRU simple en memoria para evitar llamadas repetidas a Ollama."""

    def __init__(self, capacidad: int = CACHE_MAX):
        self._cache = OrderedDict()
        self._capacidad = capacidad
        self._lock = threading.Lock()

    def obtener(self, clave: str) -> str | None:
        """Busca una respuesta en caché. None si no existe."""
        with self._lock:
            if clave in self._cache:
                self._cache.move_to_end(clave)
                return self._cache[clave]
        return None

    def guardar(self, clave: str, valor: str):
        """Guarda una respuesta en caché, eliminando la más vieja si está lleno."""
        with self._lock:
            if clave in self._cache:
                self._cache.move_to_end(clave)
            self._cache[clave] = valor
            if len(self._cache) > self._capacidad:
                self._cache.popitem(last=False)


# ── Servicio principal ───────────────────────────────────────────────────────

class ServicioIA:
    """
    Servicio de IA local que usa Ollama con TinyLlama.
    Si Ollama no está disponible, usa fallback automático con respuestas
    predefinidas para garantizar funcionamiento offline.
    """

    def __init__(self, modelo: str = MODELO_DEFECTO):
        self.modelo = modelo
        self.cache = CacheIA()
        self._disponible = None  # None = no verificado aún
        self._ultima_verificacion = 0

    def verificar_disponibilidad(self) -> bool:
        """
        Verifica si Ollama está corriendo y el modelo está descargado.
        Cachea el resultado por 30 segundos para evitar verificaciones excesivas.

        Returns:
            True si Ollama está disponible y responde, False en caso contrario.
        """
        ahora = time.time()
        if self._disponible is not None and (ahora - self._ultima_verificacion) < 30:
            return self._disponible

        try:
            req = urllib_request.Request(
                f"{OLLAMA_URL}/api/tags",
                method="GET",
            )
            with urllib_request.urlopen(req, timeout=3) as resp:
                datos = json.loads(resp.read().decode("utf-8"))
                modelos = [m.get("name", "") for m in datos.get("models", [])]
                # Verificar si el modelo está disponible (con o sin tag)
                self._disponible = any(
                    self.modelo in nombre for nombre in modelos
                )
                self._ultima_verificacion = ahora
                if self._disponible:
                    print(f"[IA] Ollama disponible con modelo '{self.modelo}'.")
                else:
                    print(f"[IA] Ollama corriendo pero modelo '{self.modelo}' no encontrado.")
                    print(f"[IA] Modelos disponibles: {modelos}")
                return self._disponible
        except (URLError, OSError, Exception) as e:
            self._disponible = False
            self._ultima_verificacion = ahora
            print(f"[IA] Ollama no disponible: {e}")
            return False

    def generar_respuesta(
        self,
        personaje: str,
        mensaje: str,
        contexto_materia: str = "",
        contexto_nivel: int = 0,
    ) -> dict:
        """
        Genera una respuesta del personaje al mensaje del usuario.
        Intenta usar Ollama; si falla, usa fallback automático.

        Args:
            personaje:        Nombre del personaje (ej. 'El Riviel').
            mensaje:          Texto del usuario.
            contexto_materia: Materia actual (ej. 'matematicas').
            contexto_nivel:   Nivel actual (1-5).

        Returns:
            Dict con {respuesta: str, fuente: 'ollama'|'fallback'}.
        """
        # Intentar caché primero
        clave_cache = f"{personaje}:{mensaje[:80]}"
        respuesta_cache = self.cache.obtener(clave_cache)
        if respuesta_cache:
            return {"respuesta": respuesta_cache, "fuente": "cache"}

        # Intentar Ollama
        if self.verificar_disponibilidad():
            respuesta_ia = self._llamar_ollama(personaje, mensaje, contexto_materia, contexto_nivel)
            if respuesta_ia:
                self.cache.guardar(clave_cache, respuesta_ia)
                return {"respuesta": respuesta_ia, "fuente": "ollama"}

        # Fallback automático
        tipo = clasificar_mensaje(mensaje)
        respuesta_fb = obtener_respuesta_fallback(personaje, tipo)
        return {"respuesta": respuesta_fb, "fuente": "fallback"}

    def generar_retroalimentacion(
        self,
        personaje: str,
        materia: str,
        nivel: int,
        puntaje: int,
    ) -> dict:
        """
        Genera retroalimentación después de completar un nivel.

        Args:
            personaje: Nombre del personaje guía.
            materia:   Materia del nivel.
            nivel:     Número de nivel completado.
            puntaje:   Puntaje obtenido (0-100).

        Returns:
            Dict con {respuesta: str, fuente: 'ollama'|'fallback'}.
        """
        tipo_retro = "retroalimentacion_buena" if puntaje >= 60 else "retroalimentacion_regular"

        if self.verificar_disponibilidad():
            prompt_usuario = (
                f"El niño acaba de completar el nivel {nivel} de {materia} "
                f"con {puntaje} puntos de 100. "
                f"Dale una retroalimentación {'positiva' if puntaje >= 60 else 'motivadora'}."
            )
            respuesta_ia = self._llamar_ollama(personaje, prompt_usuario, materia, nivel)
            if respuesta_ia:
                return {"respuesta": respuesta_ia, "fuente": "ollama"}

        respuesta_fb = obtener_respuesta_fallback(personaje, tipo_retro)
        return {"respuesta": respuesta_fb, "fuente": "fallback"}

    def _llamar_ollama(
        self,
        personaje: str,
        mensaje: str,
        contexto_materia: str = "",
        contexto_nivel: int = 0,
    ) -> str | None:
        """
        Realiza la llamada HTTP a la API local de Ollama.
        No bloquea más de TIMEOUT_SEGUNDOS.

        Args:
            personaje:        Nombre del personaje.
            mensaje:          Mensaje del usuario.
            contexto_materia: Materia para contexto adicional.
            contexto_nivel:   Nivel para contexto adicional.

        Returns:
            String con la respuesta generada, o None si falló.
        """
        system_prompt = SYSTEM_PROMPTS.get(personaje, SYSTEM_PROMPT_GENERICO)

        # Agregar contexto de materia/nivel si está disponible
        if contexto_materia:
            system_prompt += f" Estás en la materia de {contexto_materia}."
        if contexto_nivel:
            system_prompt += f" Nivel {contexto_nivel} de 5."

        payload = {
            "model": self.modelo,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": mensaje},
            ],
            "stream": False,
            "options": {
                "temperature": TEMPERATURA,
                "num_predict": MAX_TOKENS,
                "top_p": 0.9,
                "repeat_penalty": 1.1,
            },
        }

        try:
            datos_json = json.dumps(payload).encode("utf-8")
            req = urllib_request.Request(
                f"{OLLAMA_URL}/api/chat",
                data=datos_json,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib_request.urlopen(req, timeout=TIMEOUT_SEGUNDOS) as resp:
                resultado = json.loads(resp.read().decode("utf-8"))
                contenido = resultado.get("message", {}).get("content", "").strip()
                if contenido:
                    print(f"[IA] Respuesta Ollama ({personaje}): {contenido[:80]}...")
                    return contenido
                return None
        except Exception as e:
            print(f"[IA] Error al llamar Ollama: {e}")
            self._disponible = False
            return None


# ── Instancia global del servicio ────────────────────────────────────────────

servicio_ia = ServicioIA()
