====================================================
GUIA RAPIDA PARA EL DOCENTE - PACIFICO EDUCATIVO
====================================================

Este juego fue disenado para que los estudiantes aprendan de manera interactiva
sobre la region Pacifica.

COMO INICIAR EL JUEGO
1. Instale Python si va a ejecutar desde el codigo fuente.
2. Instale dependencias con:
   pip install -r requirements.txt
3. Ejecute:
   python server.py
4. Abra en el navegador:
   http://localhost:5000

IA LOCAL SIN API KEYS
1. El juego usa Ollama para ejecutar un modelo local en el computador.
2. No usa OpenAI, Gemini, Anthropic ni API keys externas.
3. Modelo principal recomendado:
   ollama pull llama3.2:1b
4. Alternativa mas liviana:
   ollama pull tinyllama
5. La primera descarga del modelo requiere internet. Despues, el modelo corre
   localmente.
6. Si Ollama no esta disponible, el juego usa respuestas educativas de respaldo
   para que el chat, las pistas y la retroalimentacion sigan funcionando.

CAMBIAR MODELO
Antes de iniciar el servidor puede configurar:
   set OLLAMA_MODEL=llama3.2:1b

Para equipos muy limitados:
   set OLLAMA_MODEL=tinyllama

Tambien puede cambiar la URL de Ollama:
   set OLLAMA_URL=http://localhost:11434

PROBLEMAS COMUNES
- Ollama no esta corriendo:
  Abra la aplicacion de Ollama o ejecute "ollama serve".

- Modelo no encontrado:
  Ejecute "ollama pull llama3.2:1b".

- Puerto 11434 ocupado:
  Inicie Ollama en otro puerto y configure OLLAMA_URL.

- El computador es lento:
  Use TinyLlama con "ollama pull tinyllama" y "set OLLAMA_MODEL=tinyllama".

COMO VER LOS PUNTAJES
1. El estudiante escribe su nombre al iniciar.
2. En el menu principal, haga clic en "Mis Puntajes".
3. Se abre el diario de viaje con los niveles y puntajes del estudiante.

NOTA
Si desea reiniciar todo desde cero para una nueva clase, borre el archivo
data/progress.db.
