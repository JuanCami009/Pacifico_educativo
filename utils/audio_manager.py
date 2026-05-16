"""
audio_manager.py - Gestor centralizado de audio para el juego Pacífico Educativo
Maneja música de fondo y efectos de sonido usando pygame.mixer
"""

import pygame
import os


# Directorio base de assets de audio
DIRECTORIO_AUDIO = os.path.join(os.path.dirname(__file__), '..', 'assets', 'audio')

# Volumen por defecto (0.0 a 1.0)
VOLUMEN_MUSICA_DEFAULT = 0.5
VOLUMEN_EFECTOS_DEFAULT = 0.8


class GestorAudio:
    """
    Clase que administra la reproducción de música de fondo y efectos de sonido.
    Diseñada como singleton para uso global en el juego.
    """

    def __init__(self):
        """Inicializa el gestor de audio y el mixer de pygame."""
        self._inicializado = False
        self._sonidos_cache = {}       # Caché de efectos de sonido cargados
        self._musica_actual = None     # Nombre del archivo de música actual
        self._volumen_musica = VOLUMEN_MUSICA_DEFAULT
        self._volumen_efectos = VOLUMEN_EFECTOS_DEFAULT
        self._silenciado = False

        try:
            # Inicializar el mixer con parámetros de calidad estándar
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self._inicializado = True
            print("[Audio] Mixer inicializado correctamente.")
        except pygame.error as e:
            print(f"[Audio] ADVERTENCIA: No se pudo inicializar el mixer: {e}")

    # -----------------------------------------------------------------------
    # Música de fondo
    # -----------------------------------------------------------------------

    def reproducir_musica(self, nombre_archivo: str, repeticiones: int = -1):
        """
        Carga y reproduce un archivo de música en bucle.

        Args:
            nombre_archivo: Nombre del archivo dentro de /assets/audio/ (ej. 'menu.ogg').
            repeticiones:   -1 para bucle infinito, 0 para reproducir una vez.
        """
        if not self._inicializado:
            return

        ruta = os.path.join(DIRECTORIO_AUDIO, nombre_archivo)

        # Evitar recargar si ya se está reproduciendo la misma pista
        if self._musica_actual == nombre_archivo and pygame.mixer.music.get_busy():
            return

        if not os.path.exists(ruta):
            print(f"[Audio] ADVERTENCIA: No se encontró el archivo '{nombre_archivo}'.")
            return

        try:
            pygame.mixer.music.load(ruta)
            pygame.mixer.music.set_volume(self._volumen_musica if not self._silenciado else 0.0)
            pygame.mixer.music.play(repeticiones)
            self._musica_actual = nombre_archivo
            print(f"[Audio] Reproduciendo música: {nombre_archivo}")
        except pygame.error as e:
            print(f"[Audio] Error al reproducir música: {e}")

    def detener_musica(self):
        """Detiene la música de fondo que se está reproduciendo."""
        if self._inicializado:
            pygame.mixer.music.stop()
            self._musica_actual = None

    def pausar_musica(self):
        """Pausa la música de fondo sin perder la posición."""
        if self._inicializado:
            pygame.mixer.music.pause()

    def reanudar_musica(self):
        """Reanuda la música de fondo desde donde se pausó."""
        if self._inicializado:
            pygame.mixer.music.unpause()

    def ajustar_volumen_musica(self, volumen: float):
        """
        Ajusta el volumen de la música.

        Args:
            volumen: Valor entre 0.0 (silencio) y 1.0 (máximo).
        """
        self._volumen_musica = max(0.0, min(1.0, volumen))
        if self._inicializado and not self._silenciado:
            pygame.mixer.music.set_volume(self._volumen_musica)

    # -----------------------------------------------------------------------
    # Efectos de sonido
    # -----------------------------------------------------------------------

    def cargar_sonido(self, nombre_archivo: str) -> pygame.mixer.Sound | None:
        """
        Carga un efecto de sonido en caché para reproducción rápida.

        Args:
            nombre_archivo: Nombre del archivo dentro de /assets/audio/.

        Returns:
            Objeto Sound de pygame o None si no se pudo cargar.
        """
        if not self._inicializado:
            return None

        # Retornar desde caché si ya fue cargado
        if nombre_archivo in self._sonidos_cache:
            return self._sonidos_cache[nombre_archivo]

        ruta = os.path.join(DIRECTORIO_AUDIO, nombre_archivo)
        if not os.path.exists(ruta):
            print(f"[Audio] ADVERTENCIA: Sonido no encontrado: '{nombre_archivo}'.")
            return None

        try:
            sonido = pygame.mixer.Sound(ruta)
            sonido.set_volume(self._volumen_efectos)
            self._sonidos_cache[nombre_archivo] = sonido
            return sonido
        except pygame.error as e:
            print(f"[Audio] Error al cargar sonido '{nombre_archivo}': {e}")
            return None

    def reproducir_sonido(self, nombre_archivo: str):
        """
        Reproduce un efecto de sonido. Lo carga si no está en caché.

        Args:
            nombre_archivo: Nombre del archivo de sonido.
        """
        if self._silenciado:
            return

        sonido = self.cargar_sonido(nombre_archivo)
        if sonido:
            sonido.play()

    def ajustar_volumen_efectos(self, volumen: float):
        """
        Ajusta el volumen de todos los efectos de sonido cargados.

        Args:
            volumen: Valor entre 0.0 y 1.0.
        """
        self._volumen_efectos = max(0.0, min(1.0, volumen))
        for sonido in self._sonidos_cache.values():
            sonido.set_volume(self._volumen_efectos)

    # -----------------------------------------------------------------------
    # Control global
    # -----------------------------------------------------------------------

    def alternar_silencio(self):
        """Activa o desactiva el silencio global del juego."""
        self._silenciado = not self._silenciado
        if self._inicializado:
            if self._silenciado:
                pygame.mixer.music.set_volume(0.0)
                for sonido in self._sonidos_cache.values():
                    sonido.set_volume(0.0)
            else:
                pygame.mixer.music.set_volume(self._volumen_musica)
                for sonido in self._sonidos_cache.values():
                    sonido.set_volume(self._volumen_efectos)

        estado = "silenciado" if self._silenciado else "activado"
        print(f"[Audio] Audio {estado}.")

    @property
    def esta_silenciado(self) -> bool:
        """Retorna True si el audio está silenciado."""
        return self._silenciado

    def limpiar(self):
        """Libera todos los recursos de audio al cerrar el juego."""
        if self._inicializado:
            pygame.mixer.music.stop()
            self._sonidos_cache.clear()
            pygame.mixer.quit()
            print("[Audio] Recursos de audio liberados.")


# Instancia global del gestor de audio (patrón singleton ligero)
gestor_audio = GestorAudio()
