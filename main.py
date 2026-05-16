"""
main.py - Lanzador del servidor Flask para Pacífico Educativo.
Inicia Flask en un hilo y abre el navegador automáticamente.
"""
import sys
import os
import threading
import webbrowser
import time

# Agregar la carpeta raíz al path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PUERTO = 5000
URL = f"http://localhost:{PUERTO}"


def abrir_navegador():
    """Espera 1.5 segundos y abre el navegador predeterminado."""
    time.sleep(1.5)
    try:
        webbrowser.open(URL)
    except Exception:
        print(f"[Inicio] Abre manualmente en tu navegador: {URL}")


def main():
    from server import app

    print("=" * 50)
    print("  Pacífico Educativo - Iniciando servidor...")
    print(f"  URL: {URL}")
    print("  Cierra esta ventana para apagar el juego.")
    print("=" * 50)

    # Abrir navegador en hilo paralelo
    hilo_navegador = threading.Thread(target=abrir_navegador, daemon=True)
    hilo_navegador.start()

    # Iniciar Flask (bloquea hasta que se cierre)
    try:
        app.run(host="localhost", port=PUERTO, debug=False, use_reloader=False)
    except OSError as e:
        print(f"[Error] No se pudo iniciar en el puerto {PUERTO}: {e}")
        print(f"  Intenta abrir manualmente: {URL}")
        input("Presiona Enter para salir...")


if __name__ == "__main__":
    main()
