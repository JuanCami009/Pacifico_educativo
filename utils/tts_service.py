"""
tts_service.py - TTS para Pacifico Educativo, con tres backends.

Orden de preferencia:
  1. Edge TTS (Microsoft Neural Voices) — voces latinoamericanas animadas,
     gratis, ~2MB de pip install, requiere internet la primera vez por texto.
  2. Windows SAPI via PowerShell — totalmente offline, voz del sistema.
  3. espeak-ng — fallback robotico Linux/Mac.

Los WAV/MP3 se cachean en static/audio/tts_cache/ y luego se sirven offline.
"""
import asyncio
import hashlib
import os
import subprocess
import sys

BASE_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(BASE_DIR, 'static', 'audio', 'tts_cache')
CACHE_URL = '/static/audio/tts_cache'   # URL publica

# Voz Edge TTS — latina, animada, gratuita. Cambiable via env var.
EDGE_VOICE = os.getenv('TTS_VOICE', 'es-MX-DaliaNeural')
# Otras opciones recomendadas:
#   es-CO-SalomeNeural   (Colombia, mujer joven)
#   es-CO-GonzaloNeural  (Colombia, hombre)
#   es-MX-JorgeNeural    (Mexico, hombre)
#   es-AR-ElenaNeural    (Argentina)
#   es-US-PalomaNeural   (Latino US)

# Detectar si edge-tts esta disponible
try:
    import edge_tts  # type: ignore
    EDGE_TTS_OK = True
except ImportError:
    EDGE_TTS_OK = False


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _asegurar_dir() -> None:
    os.makedirs(CACHE_DIR, exist_ok=True)


def _clave(texto: str) -> str:
    """Hash MD5 truncado a 16 chars como nombre de archivo."""
    return hashlib.md5(texto.encode('utf-8')).hexdigest()[:16]


def _escapar_ps(texto: str) -> str:
    """Limpia el texto para incrustarlo en una cadena PowerShell."""
    return (
        texto
        .replace('"',  "'")
        .replace('`',  "'")
        .replace('\n', ' ')
        .replace('\r', '')
    )


# ---------------------------------------------------------------------------
# Backends de generacion
# ---------------------------------------------------------------------------

def _generar_sapi_windows(texto: str, ruta_wav: str) -> bool:
    """
    Genera WAV via Windows SAPI (System.Speech) usando PowerShell.
    Selecciona automaticamente la primera voz en espanol instalada;
    si no hay ninguna, usa la voz por defecto del sistema.
    Rate=2 suena mas animado que el valor 0 (normal).
    """
    texto_ps = _escapar_ps(texto)
    ruta_ps  = ruta_wav.replace('\\', '/')

    script = f'''\
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$s.Rate = 2
# Intentar primero voces de espanol latinoamericano
$latinCultures = @("es-CO","es-MX","es-AR","es-CL","es-PE","es-VE","es-US","es-419")
$found = $false
foreach ($culture in $latinCultures) {{
    foreach ($v in $s.GetInstalledVoices()) {{
        if ($v.VoiceInfo.Culture.Name -eq $culture) {{
            $s.SelectVoice($v.VoiceInfo.Name); $found = $true; break
        }}
    }}
    if ($found) {{ break }}
}}
# Fallback: cualquier voz en espanol
if (-not $found) {{
    foreach ($v in $s.GetInstalledVoices()) {{
        if ($v.VoiceInfo.Culture.Name -like "es*") {{
            $s.SelectVoice($v.VoiceInfo.Name); break
        }}
    }}
}}
$s.SetOutputToWaveFile("{ruta_ps}")
$s.Speak("{texto_ps}")
$s.Dispose()
'''
    try:
        result = subprocess.run(
            ['powershell', '-NonInteractive', '-NoProfile', '-Command', script],
            capture_output=True,
            timeout=45,
        )
        return os.path.exists(ruta_wav) and os.path.getsize(ruta_wav) > 100
    except Exception as exc:
        print(f'[TTS-SAPI] {exc}')
        return False


def _generar_espeak(texto: str, ruta_wav: str) -> bool:
    """Fallback para Linux/Mac con espeak-ng instalado."""
    try:
        subprocess.run(
            ['espeak-ng', '-v', 'es+f3', '-s', '155', '-w', ruta_wav, texto],
            capture_output=True,
            timeout=20,
        )
        return os.path.exists(ruta_wav) and os.path.getsize(ruta_wav) > 100
    except Exception as exc:
        print(f'[TTS-ESPEAK] {exc}')
        return False


def _generar_edge_tts(texto: str, ruta_mp3: str) -> bool:
    """
    Genera MP3 con voz neural latina usando Edge TTS (Azure Cognitive Services).
    Gratis, requiere internet la primera vez por texto. Voz animada de alta calidad.
    """
    if not EDGE_TTS_OK:
        return False
    try:
        async def _run():
            comm = edge_tts.Communicate(texto, EDGE_VOICE)
            await comm.save(ruta_mp3)

        # Necesitamos un event loop nuevo si el thread no tiene uno
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Si ya hay un loop corriendo (raro en Flask threaded), crear nuevo en thread
                import threading
                ok_holder = {'ok': False}
                def _worker():
                    try:
                        asyncio.run(_run())
                        ok_holder['ok'] = True
                    except Exception as e:
                        print(f'[TTS-EDGE] {e}')
                t = threading.Thread(target=_worker)
                t.start()
                t.join(timeout=15)
                if not ok_holder['ok']:
                    return False
            else:
                asyncio.run(_run())
        except RuntimeError:
            asyncio.run(_run())

        return os.path.exists(ruta_mp3) and os.path.getsize(ruta_mp3) > 100
    except Exception as exc:
        print(f'[TTS-EDGE] {exc}')
        return False


# ---------------------------------------------------------------------------
# API publica
# ---------------------------------------------------------------------------

def url_si_cacheada(texto: str) -> str | None:
    """
    Devuelve la URL del audio SOLO si ya esta en cache (sin generar nada).
    Chequeo instantaneo de archivo. Util para responder rapido y diferir
    la generacion del audio a una peticion aparte.
    """
    clave    = _clave(texto)
    ruta_mp3 = os.path.join(CACHE_DIR, f'{clave}.mp3')
    ruta_wav = os.path.join(CACHE_DIR, f'{clave}.wav')
    if os.path.exists(ruta_mp3) and os.path.getsize(ruta_mp3) > 100:
        return f'{CACHE_URL}/{clave}.mp3'
    if os.path.exists(ruta_wav) and os.path.getsize(ruta_wav) > 100:
        return f'{CACHE_URL}/{clave}.wav'
    return None


def generar_audio(texto: str) -> str | None:
    """
    Genera (o devuelve del cache) la URL publica del audio para el texto dado.
    Prioridad: Edge TTS (mp3) > SAPI Windows (wav) > espeak (wav).
    Retorna None si todos los backends fallan.
    """
    _asegurar_dir()
    clave    = _clave(texto)
    ruta_mp3 = os.path.join(CACHE_DIR, f'{clave}.mp3')
    ruta_wav = os.path.join(CACHE_DIR, f'{clave}.wav')

    # Cache hit MP3 (Edge TTS)
    if os.path.exists(ruta_mp3) and os.path.getsize(ruta_mp3) > 100:
        return f'{CACHE_URL}/{clave}.mp3'
    # Cache hit WAV (SAPI / espeak)
    if os.path.exists(ruta_wav) and os.path.getsize(ruta_wav) > 100:
        return f'{CACHE_URL}/{clave}.wav'

    # 1. Intentar Edge TTS (voz latina, animada, internet la 1a vez)
    if EDGE_TTS_OK:
        if _generar_edge_tts(texto, ruta_mp3):
            print(f'[TTS-EDGE] Generado: {clave}.mp3 ({os.path.getsize(ruta_mp3)//1024} KB, voz={EDGE_VOICE})')
            return f'{CACHE_URL}/{clave}.mp3'

    # 2. Fallback offline
    if sys.platform == 'win32':
        ok = _generar_sapi_windows(texto, ruta_wav)
    else:
        ok = _generar_espeak(texto, ruta_wav)

    if ok:
        print(f'[TTS] Generado: {clave}.wav ({os.path.getsize(ruta_wav)//1024} KB)')
        return f'{CACHE_URL}/{clave}.wav'

    print(f'[TTS] Fallo la generacion para clave={clave}')
    return None


def limpiar_cache(max_archivos: int = 300) -> None:
    """Elimina los WAV mas viejos si el cache supera max_archivos."""
    _asegurar_dir()
    archivos = sorted(
        [os.path.join(CACHE_DIR, f) for f in os.listdir(CACHE_DIR) if f.endswith('.wav')],
        key=os.path.getmtime,
    )
    for f in archivos[:-max_archivos]:
        try:
            os.remove(f)
        except OSError:
            pass
