"""
database.py - Módulo de gestión de base de datos para el juego educativo Pacífico
Maneja el registro de estudiantes y el seguimiento de progreso usando SQLite3
"""

import sqlite3
import os
from datetime import datetime


# Ruta de la base de datos relativa al directorio del proyecto
RUTA_DB = os.path.join(os.path.dirname(__file__), '..', 'data', 'progress.db')


def obtener_conexion():
    """
    Crea y devuelve una conexión a la base de datos SQLite.
    Crea el directorio /data si no existe.
    """
    # Asegurar que el directorio de datos existe
    directorio = os.path.dirname(RUTA_DB)
    os.makedirs(directorio, exist_ok=True)

    conexion = sqlite3.connect(RUTA_DB)
    # Devolver filas como diccionarios para mayor comodidad
    conexion.row_factory = sqlite3.Row
    return conexion


def inicializar_base_de_datos():
    """
    Crea las tablas necesarias si no existen.
    Debe llamarse al inicio de la aplicación.
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    # Tabla de estudiantes: almacena el perfil básico de cada jugador
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS estudiantes (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre          TEXT    NOT NULL UNIQUE COLLATE NOCASE,
            fecha_creacion  TEXT    NOT NULL
        )
    ''')

    # Tabla de progreso: registra el desempeño por materia y nivel
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS progreso (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            estudiante_id   INTEGER NOT NULL,
            materia         TEXT    NOT NULL,
            nivel           INTEGER NOT NULL DEFAULT 1,
            puntaje         INTEGER NOT NULL DEFAULT 0,
            fecha           TEXT    NOT NULL,
            FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id)
        )
    ''')

    conexion.commit()
    conexion.close()
    print("[BD] Base de datos inicializada correctamente.")


# ---------------------------------------------------------------------------
# Funciones de estudiantes
# ---------------------------------------------------------------------------

def crear_estudiante(nombre: str) -> dict | None:
    """
    Crea un nuevo perfil de estudiante en la base de datos.

    Args:
        nombre: Nombre del estudiante (se almacena sin distinción de mayúsculas).

    Returns:
        Diccionario con los datos del estudiante creado, o None si ya existe.
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    try:
        fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(
            'INSERT INTO estudiantes (nombre, fecha_creacion) VALUES (?, ?)',
            (nombre.strip(), fecha_actual)
        )
        conexion.commit()
        estudiante_id = cursor.lastrowid
        print(f"[BD] Nuevo estudiante creado: '{nombre}' (ID: {estudiante_id})")
        return {'id': estudiante_id, 'nombre': nombre.strip(), 'fecha_creacion': fecha_actual}
    except sqlite3.IntegrityError:
        # El nombre ya existe
        print(f"[BD] El estudiante '{nombre}' ya existe. Cargando perfil...")
        return None
    finally:
        conexion.close()


def buscar_estudiante(nombre: str) -> dict | None:
    """
    Busca un estudiante por nombre (sin distinción de mayúsculas).

    Args:
        nombre: Nombre a buscar.

    Returns:
        Diccionario con los datos del estudiante o None si no existe.
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute(
        'SELECT id, nombre, fecha_creacion FROM estudiantes WHERE nombre = ?',
        (nombre.strip(),)
    )
    fila = cursor.fetchone()
    conexion.close()

    if fila:
        return dict(fila)
    return None


def obtener_o_crear_estudiante(nombre: str) -> dict:
    """
    Devuelve el perfil del estudiante. Si no existe, lo crea.

    Args:
        nombre: Nombre del estudiante.

    Returns:
        Diccionario con los datos del estudiante (existente o recién creado).
    """
    estudiante = buscar_estudiante(nombre)
    if estudiante:
        return estudiante

    resultado = crear_estudiante(nombre)
    if resultado:
        return resultado

    # Si falló la creación (raza condición), intentar buscar de nuevo
    return buscar_estudiante(nombre)


# ---------------------------------------------------------------------------
# Funciones de progreso
# ---------------------------------------------------------------------------

def guardar_puntaje(estudiante_id: int, materia: str, nivel: int, puntaje: int):
    """
    Guarda un registro de puntaje para un estudiante en una materia y nivel.

    Args:
        estudiante_id: ID del estudiante.
        materia:       Nombre de la materia (ej. 'matematicas', 'ciencias').
        nivel:         Número de nivel completado.
        puntaje:       Puntaje obtenido en ese nivel.
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute(
        '''INSERT INTO progreso (estudiante_id, materia, nivel, puntaje, fecha)
           VALUES (?, ?, ?, ?, ?)''',
        (estudiante_id, materia.lower(), nivel, puntaje, fecha_actual)
    )
    conexion.commit()
    conexion.close()
    print(f"[BD] Puntaje guardado: Estudiante {estudiante_id} | {materia} Nivel {nivel} | {puntaje} pts")


def cargar_progreso(estudiante_id: int) -> list[dict]:
    """
    Carga todos los registros de progreso de un estudiante.

    Args:
        estudiante_id: ID del estudiante.

    Returns:
        Lista de diccionarios con los registros de progreso ordenados por fecha.
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute(
        '''SELECT materia, nivel, puntaje, fecha
           FROM progreso
           WHERE estudiante_id = ?
           ORDER BY fecha DESC''',
        (estudiante_id,)
    )
    filas = [dict(fila) for fila in cursor.fetchall()]
    conexion.close()

    return filas


def obtener_nivel_maximo(estudiante_id: int, materia: str) -> int:
    """
    Obtiene el nivel más alto desbloqueado por un estudiante en una materia.

    Args:
        estudiante_id: ID del estudiante.
        materia:       Nombre de la materia.

    Returns:
        El número del nivel más alto con puntaje registrado. Retorna 1 si no hay progreso.
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute(
        '''SELECT MAX(nivel) AS nivel_max
           FROM progreso
           WHERE estudiante_id = ? AND materia = ?''',
        (estudiante_id, materia.lower())
    )
    fila = cursor.fetchone()
    conexion.close()

    nivel_max = fila['nivel_max'] if fila and fila['nivel_max'] is not None else 0
    # El siguiente nivel desbloqueado es el máximo completado + 1
    return nivel_max + 1


def obtener_mejor_puntaje(estudiante_id: int, materia: str, nivel: int) -> int:
    """
    Obtiene el mejor puntaje registrado de un estudiante en un nivel específico.

    Args:
        estudiante_id: ID del estudiante.
        materia:       Nombre de la materia.
        nivel:         Número del nivel.

    Returns:
        El puntaje más alto registrado, o 0 si no hay registros.
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute(
        '''SELECT MAX(puntaje) AS mejor
           FROM progreso
           WHERE estudiante_id = ? AND materia = ? AND nivel = ?''',
        (estudiante_id, materia.lower(), nivel)
    )
    fila = cursor.fetchone()
    conexion.close()

    return fila['mejor'] if fila and fila['mejor'] is not None else 0


def contar_niveles_completados(estudiante_id: int, materia: str) -> int:
    """
    Cuenta cuántos niveles distintos tiene al menos un puntaje registrado.
    Se usa para calcular el porcentaje de la barra de progreso en el menú.

    Args:
        estudiante_id: ID del estudiante.
        materia:       Nombre de la materia.

    Returns:
        Número de niveles con al menos un intento (0 a TOTAL_NIVELES).
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute(
        '''SELECT COUNT(DISTINCT nivel) AS completados
           FROM progreso
           WHERE estudiante_id = ? AND materia = ? AND puntaje > 0''',
        (estudiante_id, materia.lower())
    )
    fila = cursor.fetchone()
    conexion.close()

    return fila['completados'] if fila and fila['completados'] is not None else 0


def obtener_puntajes_por_materia(estudiante_id: int) -> dict:
    """
    Devuelve un diccionario con el puntaje total acumulado por materia.
    Útil para la pantalla de "Ver mis puntajes".

    Args:
        estudiante_id: ID del estudiante.

    Returns:
        Diccionario {materia: puntaje_total}.
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute(
        '''SELECT materia, SUM(puntaje) AS total, COUNT(DISTINCT nivel) AS niveles
           FROM progreso
           WHERE estudiante_id = ?
           GROUP BY materia
           ORDER BY total DESC''',
        (estudiante_id,)
    )
    filas = cursor.fetchall()
    conexion.close()

    return {fila['materia']: {'total': fila['total'], 'niveles': fila['niveles']}
            for fila in filas}
