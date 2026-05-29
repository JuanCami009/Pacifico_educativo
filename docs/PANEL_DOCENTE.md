# Panel Administrativo Docente — Pacífico Educativo

Guía para probar el panel docente. No requiere internet; funciona 100 % local.

---

## Qué es

Un panel protegido por PIN donde el docente puede:

- Ver la **lista de estudiantes** registrados con su progreso general.
- Generar un **reporte individual** por estudiante con falencias y recomendaciones.
- Generar un **reporte de clase completa** con las materias/temas más débiles del grupo.
- Los reportes los redacta el **modelo local Ollama** (IA sin internet). Si Ollama no está activo, el sistema genera un análisis automático offline igual de útil.

---

## Requisitos previos

1. Python 3.10+ con el entorno virtual del proyecto activado.
2. (Opcional, recomendado) **Ollama** instalado y corriendo con el modelo `llama3.2:1b`:

   ```bash
   ollama pull llama3.2:1b
   ollama serve            # en una terminal aparte
   ```

   Sin Ollama el panel sigue funcionando con el modo sin conexión.

---

## Cómo arrancar la aplicación

```bash
# Desde la raíz del repositorio
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows

python server.py
# La app queda en http://localhost:5000
```

---

## Probar el panel paso a paso

### 1. Crear datos de prueba

Antes de ver reportes útiles necesitas que al menos un estudiante juegue niveles.

1. Abre `http://localhost:5000` en el navegador.
2. Ingresa un nombre (ej. `María`) y presiona **¡Entrar a la aventura!**
3. Juega 2 o 3 niveles de distintas materias (puedes fallar a propósito para generar errores).
4. Repite con otro nombre (`Pedro`) para tener varios estudiantes.

### 2. Abrir el panel docente

1. En la pantalla de inicio, haz clic en el botón discreto **"Soy docente"** (abajo del card de login).
2. Ingresa el PIN. Por defecto: **`1234`**.
3. Si el PIN es correcto, entrarás al panel.

### 3. Ver el reporte de clase

1. Haz clic en **Generar Reporte de Clase**.
2. Si Ollama está activo verás el badge **🟢 IA local**; si no, **🔴 Modo sin conexión** con el análisis automático.
3. El reporte muestra materias débiles del grupo y recomendaciones pedagógicas.

### 4. Ver el reporte individual

1. En la sección **Estudiantes** verás la lista con nombre, niveles completados y promedio.
2. Haz clic en **Ver reporte** junto al estudiante.
3. El reporte se genera abajo con el desglose por materia y tema.
4. Usa **Regenerar con IA** para forzar un nuevo reporte (ignora el cache).

---

## Configuración del PIN

El PIN se cambia con la variable de entorno `DOCENTE_PIN`:

```bash
DOCENTE_PIN=miPinSeguro python server.py
```

> **Importante:** cambia el PIN por defecto `1234` antes de usar en el aula.

---

## Datos que se capturan por nivel

Desde esta versión, cada vez que un estudiante completa un nivel se guardan:

| Campo | Descripción |
|---|---|
| `puntaje` | Puntuación final (0–100) |
| `aciertos` | Respuestas correctas en el minijuego |
| `errores` | Respuestas incorrectas |
| `intentos` | Total de interacciones |
| `duracion_seg` | Tiempo en segundos que tomó el nivel |
| `tema` | Concepto pedagógico (ej. `suma`, `vocales`, `ecosistema`) |

---

## Temas por materia

| Materia | Temas |
|---|---|
| Matemáticas | conteo · suma · resta · multiplicacion · division |
| Lenguaje | vocales · silabas · palabras · oraciones · vocabulario |
| Inglés | colores · animales · numeros · saludos · vocabulario_ingles |
| Biología | clasificacion · anatomia · ecosistema · cadena_alimenticia · conservacion |

---

## Modo sin conexión (offline)

El panel **no requiere internet**. La única dependencia de red es Ollama en `localhost:11434`. Si está apagado:

- Badge **🔴 Modo sin conexión**.
- Reporte generado automáticamente desde la base de datos: ordena materias por promedio, detecta temas débiles, da recomendaciones específicas por materia.

Esto garantiza funcionamiento en zonas sin red.
