# Pacifico Educativo

Juego educativo web para ninos del litoral Pacifico colombiano. Cubre matematicas y lenguaje en 5 niveles con minijuegos interactivos, personajes mitologicos del Pacifico, historias generadas por IA local y audio TTS completamente offline.

---

## Tabla de contenidos

1. [Requisitos](#requisitos)
2. [Instalacion](#instalacion)
3. [Como correr el proyecto](#como-correr-el-proyecto)
4. [Variables de entorno (opcional)](#variables-de-entorno-opcional)
5. [Estructura del proyecto](#estructura-del-proyecto)
6. [Funcionalidades principales](#funcionalidades-principales)
7. [TTS offline (voces)](#tts-offline-voces)
8. [Panel docente](#panel-docente)
9. [Fallback sin IA](#fallback-sin-ia)
10. [Troubleshooting](#troubleshooting)

---

## Requisitos

| Herramienta | Version minima | Notas |
|---|---|---|
| Python | 3.10+ | Solo necesita Flask |
| Ollama | cualquiera | Para IA local. Descarga: https://ollama.com |
| Windows | 10/11 | Para TTS con voz SAPI. En Linux/Mac usa espeak-ng |

**No se necesita** `.env`, API keys, ni instalar nada extra de pip.

---

## Instalacion

```bat
pip install -r requirements.txt
```

Esto solo instala Flask. Todo lo demas (SQLite, TTS, IA) ya viene incluido en Python o en Ollama.

Descargar el modelo de IA (solo la primera vez, requiere internet):

```bat
ollama pull llama3.2:1b
```

Alternativa mas liviana para PCs con pocos recursos:

```bat
ollama pull tinyllama
```

---

## Como correr el proyecto

### Opcion A — Dos terminales (recomendado)

**Terminal 1 — Ollama:**
```bat
ollama serve
```

**Terminal 2 — Servidor Flask:**
```bat
python server.py
```

Luego abre el navegador en: `http://localhost:5000`

---

### Opcion B — Una sola terminal

Si ya tienes la **app de escritorio de Ollama** instalada (el icono en la bandeja del sistema), Ollama ya corre en segundo plano automaticamente. Solo necesitas:

```bat
python server.py
```

---

### Opcion C — Sin Ollama (solo fallback)

Si no tienes Ollama o no quieres usarlo, el juego sigue funcionando con historias predefinidas y sin necesidad de correr nada extra. Las voces TTS si funcionan sin Ollama.

```bat
python server.py
```

---

## Variables de entorno (opcional)

No se necesita un archivo `.env`. Si quieres cambiar algo, usa `set` antes de correr el servidor:

```bat
rem Cambiar el modelo de IA (por defecto: llama3.2:1b)
set OLLAMA_MODEL=tinyllama
python server.py

rem Cambiar la URL de Ollama (por defecto: http://localhost:11434)
set OLLAMA_URL=http://localhost:11434
python server.py

rem Cambiar el PIN del panel docente (por defecto: 1234)
set DOCENTE_PIN=mi_pin_secreto
python server.py
```

En PowerShell usa `$env:` en lugar de `set`:

```powershell
$env:OLLAMA_MODEL = "tinyllama"
python server.py
```

---

## Estructura del proyecto

```
pacifico_educativo/
├── server.py                  # Servidor Flask + todas las rutas API
├── requirements.txt           # Solo Flask
│
├── templates/
│   └── index.html             # SPA (una sola pagina HTML)
│
├── static/
│   ├── css/styles.css         # Estilos del juego
│   ├── js/
│   │   ├── app.js             # Logica principal del frontend
│   │   ├── mate_niveles.js    # Minijuegos de matematicas (niv 2-5)
│   │   ├── point_and_click.js # Minijuego point & click
│   │   ├── drag_and_drop.js   # Minijuego drag & drop
│   │   ├── puzzle.js          # Minijuego puzzle
│   │   ├── atrapa_ranas.js    # Minijuego atrapar elementos
│   │   ├── ia_chat.js         # Chat con el personaje IA
│   │   └── pacific_icons.js   # SVGs de fauna del Pacifico
│   ├── images/                # Imagenes del juego
│   └── audio/
│       └── tts_cache/         # Cache de WAV generados por TTS (auto-creado)
│
├── utils/
│   ├── ollama_service.py      # Servicio IA (Ollama + fallback)
│   ├── tts_service.py         # TTS offline via Windows SAPI / espeak-ng
│   ├── database.py            # SQLite3: progreso y puntajes
│   └── audio_manager.py       # Utilidades de audio
│
├── data/
│   ├── niveles_contenido.py   # Contenido pedagogico de los 5 niveles
│   └── ia_fallback.py         # Respuestas predefinidas si no hay IA
│
└── docs/
    └── PANEL_DOCENTE.md       # Documentacion del panel docente
```

---

## Funcionalidades principales

- **5 niveles por materia** (matematicas y lenguaje) con minijuegos distintos
- **Personajes del Pacifico**: El Riviel (matematicas), Tunda (lenguaje), etc.
- **Historias de IA**: cada vez que entras a un nivel, Ollama genera una mini-historia narrativa (2-3 oraciones) + explicacion del nivel (1-2 oraciones)
- **Precarga de historias**: cuando abres el selector de niveles, las 5 historias se generan en segundo plano para que al entrar al nivel ya esten listas
- **TTS offline**: la historia se lee en voz alta usando las voces del sistema operativo (sin internet)
- **Progreso persistente**: SQLite guarda puntajes por estudiante
- **Multiples estudiantes**: cada quien ingresa con su nombre
- **Panel docente**: reportes individuales y de clase generados por IA

---

## TTS offline (voces)

El juego genera audio para las historias usando las voces instaladas en tu sistema operativo. No requiere internet ni pip extra.

**Windows** (automatico):
- Usa Windows SAPI via PowerShell
- Selecciona automaticamente la primera voz en espanol instalada
- Si no hay voz en espanol, usa la voz por defecto del sistema
- Los archivos WAV se guardan en `static/audio/tts_cache/` y se reusan

**Linux/Mac** (fallback):
- Requiere `espeak-ng` instalado: `sudo apt install espeak-ng`

**Para agregar mas voces en espanol en Windows:**
- Configuracion > Hora e idioma > Idioma > Espanol > Opciones > Descargar voz

Los WAV en cache se acumulan con el tiempo. El sistema limita automaticamente a 300 archivos.

---

## Panel docente

Accede desde la pantalla de inicio con el boton "Soy docente".

- **PIN por defecto**: `1234`
- **Cambiar PIN**: `set DOCENTE_PIN=tu_pin` antes de correr el servidor
- **Funciones**: ver todos los estudiantes, puntajes por nivel, reporte individual con IA, reporte de clase con IA

---

## Fallback sin IA

Si Ollama no esta corriendo o el modelo no responde, el juego usa:

1. **Historias predefinidas** en `utils/ollama_service.py` (funcion `_historia_fallback`) — hay una historia por nivel para matematicas y lenguaje
2. **Respuestas de chat predefinidas** en `data/ia_fallback.py`
3. **El TTS si funciona** con los textos de fallback (no necesita Ollama)

El juego nunca se rompe si Ollama falla.

---

## Troubleshooting

**Ollama no responde:**
```bat
rem Verifica que este corriendo
ollama list
rem Si no responde, inicialo manualmente
ollama serve
```

**El modelo no esta descargado:**
```bat
ollama pull llama3.2:1b
```

**Puerto 11434 ocupado:**
```bat
set OLLAMA_URL=http://localhost:OTRO_PUERTO
python server.py
```

**PC lenta / historias tardan mucho:**
```bat
ollama pull tinyllama
set OLLAMA_MODEL=tinyllama
python server.py
```

**No hay voz en espanol en Windows:**
- Ve a Configuracion > Hora e idioma > Idioma > Espanol (Colombia o cualquier variante) > Opciones > Voz > Descargar
- Reinicia el servidor para que detecte la nueva voz

**El audio TTS no suena:**
- Verifica que `static/audio/tts_cache/` existe y tiene archivos `.wav`
- Abre las DevTools del navegador > Console y busca errores de red en las peticiones al endpoint `/api/ia/historia_nivel`
- Verifica que la respuesta JSON tenga el campo `audioUrl` con una ruta valida

**Puerto 5000 ocupado:**
```bat
rem Cambia el puerto en la ultima linea de server.py
rem app.run(debug=True, port=5001)
```

**Base de datos corrupta:**
```bat
rem Borra el archivo SQLite y se recrea automaticamente
del pacifico.db
python server.py
```
