@echo off
chcp 65001 > nul
title Configuración de IA Local - Pacífico Educativo

echo =======================================================================
echo          PACÍFICO EDUCATIVO - CONFIGURACIÓN DE IA OFFLINE
echo =======================================================================
echo.
echo Este script configurará el modelo de Inteligencia Artificial local
echo para que puedas jugar e interactuar con los personajes sin internet.
echo.

:: 1. Verificar si Ollama está instalado/en PATH
where ollama >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Ollama no está instalado o no se encuentra en el PATH.
    echo.
    echo Por favor:
    echo 1. Descarga e instala Ollama desde: https://ollama.com
    echo 2. Abre la aplicación de Ollama una vez para inicializarla.
    echo 3. Vuelve a ejecutar este script.
    echo.
    pause
    exit /b 1
)

echo [OK] Ollama está instalado en tu sistema.
echo.

:: 2. Verificar si el servicio de Ollama se está ejecutando
echo [INFO] Verificando que el servicio de Ollama esté activo...
curl -s -I http://localhost:11434 >nul 2>nul
if %errorlevel% neq 0 (
    echo [INFO] El servicio de Ollama no parece estar corriendo.
    echo [INFO] Intentando iniciar el servicio de Ollama...
    start "" /b ollama serve
    :: Esperar unos segundos a que inicie
    timeout /t 5 /nobreak >nul
)

:: Re-verificar si ya responde
curl -s -I http://localhost:11434 >nul 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] No se pudo verificar si el servicio de Ollama inició.
    echo           Asegúrate de que la aplicación Ollama esté abierta en la barra de tareas.
    echo.
) else (
    echo [OK] Servicio de Ollama detectado y activo.
    echo.
)

:: 3. Descargar/Actualizar el modelo TinyLlama
echo [INFO] Descargando y configurando el modelo 'tinyllama' (aprox. 637MB)...
echo Este paso puede tardar unos minutos dependiendo de tu velocidad de conexión
echo (sólo es necesario realizarlo la primera vez).
echo.
ollama pull tinyllama
if %errorlevel% neq 0 (
    echo.
    echo [WARNING] Hubo un error al intentar descargar el modelo automáticamente.
    echo           Asegúrate de tener conexión a internet en este momento para la descarga inicial.
    echo.
    pause
) else (
    echo.
    echo [OK] Modelo 'tinyllama' configurado exitosamente.
    echo.
)

:: 4. Instalar dependencias de Python
echo [INFO] Verificando dependencias de Python...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [WARNING] No se pudieron instalar las dependencias con pip.
    echo           Asegúrate de tener Python instalado y accesible en tu PATH.
    echo.
) else (
    echo [OK] Dependencias verificadas correctamente.
    echo.
)

:: 5. Ejecutar el servidor del juego
echo =======================================================================
echo ¡Todo listo! Iniciando el servidor del juego...
echo =======================================================================
echo.
echo Presiona CTRL+C para detener el servidor cuando termines.
echo.
python server.py
pause
