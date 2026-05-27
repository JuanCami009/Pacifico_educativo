@echo off
chcp 65001 > nul
title Configuracion de IA Local - Pacifico Educativo

echo =======================================================================
echo          PACIFICO EDUCATIVO - CONFIGURACION DE IA OFFLINE
echo =======================================================================
echo.
echo Este script configura un modelo de IA local con Ollama.
echo No usa API keys externas. La primera descarga requiere internet.
echo Luego el modelo corre localmente en este computador.
echo.

:: 1. Verificar si Ollama esta instalado/en PATH
where ollama >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Ollama no esta instalado o no se encuentra en el PATH.
    echo.
    echo Por favor:
    echo 1. Descarga e instala Ollama desde: https://ollama.com
    echo 2. Abre la aplicacion de Ollama una vez para inicializarla.
    echo 3. Vuelve a ejecutar este script.
    echo.
    pause
    exit /b 1
)

echo [OK] Ollama esta instalado en tu sistema.
echo.

:: 2. Verificar si el servicio de Ollama se esta ejecutando
echo [INFO] Verificando que el servicio de Ollama este activo...
curl -s -I http://localhost:11434 >nul 2>nul
if %errorlevel% neq 0 (
    echo [INFO] El servicio de Ollama no parece estar corriendo.
    echo [INFO] Intentando iniciar el servicio de Ollama...
    start "" /b ollama serve
    timeout /t 5 /nobreak >nul
)

curl -s -I http://localhost:11434 >nul 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] No se pudo verificar si el servicio de Ollama inicio.
    echo           Asegurate de que la aplicacion Ollama este abierta.
    echo.
) else (
    echo [OK] Servicio de Ollama detectado y activo.
    echo.
)

:: 3. Descargar/Actualizar el modelo principal
set OLLAMA_MODEL=llama3.2:1b
echo [INFO] Descargando y configurando el modelo principal '%OLLAMA_MODEL%' (aprox. 1.3GB)...
echo Este paso puede tardar unos minutos dependiendo de tu velocidad de conexion.
echo Solo es necesario realizarlo la primera vez.
echo.
ollama pull %OLLAMA_MODEL%
if %errorlevel% neq 0 (
    echo.
    echo [WARNING] Hubo un error al intentar descargar el modelo automaticamente.
    echo           Asegurate de tener conexion a internet para la descarga inicial.
    echo           Alternativa mas liviana: ollama pull tinyllama
    echo.
    pause
) else (
    echo.
    echo [OK] Modelo '%OLLAMA_MODEL%' configurado exitosamente.
    echo [INFO] Alternativa para equipos muy limitados: ollama pull tinyllama
    echo [INFO] Para usarla en esta consola: set OLLAMA_MODEL=tinyllama
    echo.
)

:: 4. Instalar dependencias de Python
echo [INFO] Verificando dependencias de Python...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [WARNING] No se pudieron instalar las dependencias con pip.
    echo           Asegurate de tener Python instalado y accesible en tu PATH.
    echo.
) else (
    echo [OK] Dependencias verificadas correctamente.
    echo.
)

:: 5. Ejecutar el servidor del juego
echo =======================================================================
echo Todo listo. Iniciando el servidor del juego...
echo =======================================================================
echo.
echo URL: http://localhost:5000
echo Presiona CTRL+C para detener el servidor cuando termines.
echo.
python server.py
pause
