"""
database.py - Módulo de gestión de base de datos para el juego educativo Pacífico
Maneja el registro de estudiantes y el seguimiento de progreso usando SQLite3
"""

import sqlite3
import os
from datetime import datetime


def _obtener_ruta_db() -> str:
    """Devuelve una ruta de base de datos válida para local y Vercel."""
    ruta_personalizada = os.getenv("DATABASE_PATH")
    if ruta_personalizada:
        return ruta_personalizada

    if os.getenv("VERCEL"):
        return "/tmp/progress.db"

    return os.path.join(os.path.dirname(__file__), '..', 'data', 'progress.db')


def obtener_conexion():
    """
    Crea y devuelve una conexión a la base de datos SQLite.
    Crea el directorio /data si no existe.
    """
    ruta_db = _obtener_ruta_db()
    directorio = os.path.dirname(ruta_db)
    os.makedirs(directorio, exist_ok=True)

    conexion = sqlite3.connect(ruta_db)
    conexion.row_factory = sqlite3.Row
    return conexion


def _asegurar_columnas():
    """
    Migración no destructiva: añade columnas nuevas a 'progreso' si no existen.
    Seguro para bases de datos existentes (no borra datos previos).
    """
    nuevas_columnas = [
        ('aciertos',     'INTEGER DEFAULT 0'),
        ('errores',      'INTEGER DEFAULT 0'),
        ('intentos',     'INTEGER DEFAULT 0'),
        ('duracion_seg', 'INTEGER DEFAULT 0'),
        ('tema',         'TEXT    DEFAULT ""'),
    ]
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute('PRAGMA table_info(progreso)')
    columnas_existentes = {fila['name'] for fila in cursor.fetchall()}
    for nombre, definicion in nuevas_columnas:
        if nombre not in columnas_existentes:
            cursor.execute(f'ALTER TABLE progreso ADD COLUMN {nombre} {definicion}')
            print(f'[BD] Columna añadida: progreso.{nombre}')
    conexion.commit()
    conexion.close()


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
            aciertos        INTEGER DEFAULT 0,
            errores         INTEGER DEFAULT 0,
            intentos        INTEGER DEFAULT 0,
            duracion_seg    INTEGER DEFAULT 0,
            tema            TEXT    DEFAULT "",
            FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id)
        )
    ''')

    # Tabla de reportes: cache de reportes generados por IA o fallback
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reportes (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            ambito        TEXT    NOT NULL,
            estudiante_id INTEGER,
            contenido     TEXT    NOT NULL,
            fuente        TEXT    NOT NULL,
            fecha         TEXT    NOT NULL
        )
    ''')

    conexion.commit()
    conexion.close()

    # Migración no destructiva para bases de datos existentes
    _asegurar_columnas()
    print("[BD] Base de datos inicializada correctamente.")


# ---------------------------------------------------------------------------
# Funciones de estudiantes
# ---------------------------------------------------------------------------

def crear_estudiante(nombre: str) -> dict | None:
    """Crea un nuevo perfil de estudiante. Devuelve None si ya existe."""
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
        print(f"[BD] El estudiante '{nombre}' ya existe. Cargando perfil...")
        return None
    finally:
        conexion.close()


def buscar_estudiante(nombre: str) -> dict | None:
    """Busca un estudiante por nombre (sin distinción de mayúsculas)."""
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
    """Devuelve el perfil del estudiante. Si no existe, lo crea."""
    estudiante = buscar_estudiante(nombre)
    if estudiante:
        return estudiante

    resultado = crear_estudiante(nombre)
    if resultado:
        return resultado

    return buscar_estudiante(nombre)


def listar_estudiantes() -> list[dict]:
    """
    Devuelve todos los estudiantes con resumen de progreso.
    Útil para el panel docente.
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute('''
        SELECT e.id,
               e.nombre,
               e.fecha_creacion,
               (SELECT COUNT(DISTINCT materia || '|' || nivel)
                FROM progreso WHERE estudiante_id = e.id) AS niveles_completados,
               (SELECT ROUND(AVG(puntaje), 0)
                FROM progreso WHERE estudiante_id = e.id) AS promedio_global
        FROM estudiantes e
        ORDER BY e.nombre
    ''')
    filas = [dict(fila) for fila in cursor.fetchall()]
    conexion.close()
    return filas


# ---------------------------------------------------------------------------
# Funciones de progreso
# ---------------------------------------------------------------------------

def guardar_puntaje(
    estudiante_id: int,
    materia: str,
    nivel: int,
    puntaje: int,
    aciertos: int = 0,
    errores: int = 0,
    intentos: int = 0,
    duracion_seg: int = 0,
    tema: str = '',
):
    """
    Guarda un registro de desempeño para un estudiante en una materia y nivel.
    Acepta métricas enriquecidas opcionales (para compatibilidad con datos previos).
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    fecha_actual = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute(
        '''INSERT INTO progreso
               (estudiante_id, materia, nivel, puntaje, fecha,
                aciertos, errores, intentos, duracion_seg, tema)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (estudiante_id, materia.lower(), nivel, puntaje, fecha_actual,
         aciertos, errores, intentos, duracion_seg, tema)
    )
    conexion.commit()
    conexion.close()
    print(
        f"[BD] Puntaje guardado: Estudiante {estudiante_id} | "
        f"{materia} Nivel {nivel} | {puntaje} pts | "
        f"a:{aciertos} e:{errores} tema:{tema}"
    )


def cargar_progreso(estudiante_id: int) -> list[dict]:
    """Carga todos los registros de progreso de un estudiante."""
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
    """Obtiene el nivel más alto desbloqueado por un estudiante en una materia."""
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
    return nivel_max + 1


def obtener_mejor_puntaje(estudiante_id: int, materia: str, nivel: int) -> int:
    """Obtiene el mejor puntaje registrado de un estudiante en un nivel específico."""
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
    """Cuenta cuántos niveles distintos tienen al menos un puntaje registrado."""
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


# ---------------------------------------------------------------------------
# Funciones de análisis de desempeño (para el panel docente)
# ---------------------------------------------------------------------------

def obtener_desempeno_estudiante(estudiante_id: int) -> dict:
    """
    Devuelve desempeño agregado de un estudiante por materia y por tema.
    Usado para generar el reporte individual del panel docente.
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute('SELECT nombre FROM estudiantes WHERE id = ?', (estudiante_id,))
    fila_e = cursor.fetchone()
    nombre = fila_e['nombre'] if fila_e else 'Desconocido'

    # Por materia
    cursor.execute('''
        SELECT materia,
               ROUND(AVG(puntaje), 1)          AS promedio_puntaje,
               COUNT(DISTINCT nivel)            AS niveles_completados,
               SUM(COALESCE(aciertos,  0))      AS total_aciertos,
               SUM(COALESCE(errores,   0))      AS total_errores,
               SUM(COALESCE(intentos,  0))      AS total_intentos
        FROM progreso
        WHERE estudiante_id = ?
        GROUP BY materia
    ''', (estudiante_id,))
    por_materia = {}
    for fila in cursor.fetchall():
        t_int = fila['total_intentos'] or 0
        t_err = fila['total_errores'] or 0
        por_materia[fila['materia']] = {
            'promedio_puntaje':    float(fila['promedio_puntaje'] or 0),
            'niveles_completados': fila['niveles_completados'] or 0,
            'total_aciertos':      fila['total_aciertos'] or 0,
            'total_errores':       t_err,
            'total_intentos':      t_int,
            'tasa_error':          round(t_err / max(t_int, 1), 2),
        }

    # Por tema (solo registros con tema registrado)
    cursor.execute('''
        SELECT tema,
               ROUND(AVG(puntaje), 1)     AS promedio_puntaje,
               COUNT(*)                   AS total_sesiones,
               SUM(COALESCE(aciertos, 0)) AS total_aciertos,
               SUM(COALESCE(errores,  0)) AS total_errores
        FROM progreso
        WHERE estudiante_id = ? AND tema IS NOT NULL AND tema != ''
        GROUP BY tema
        ORDER BY promedio_puntaje ASC
    ''', (estudiante_id,))
    por_tema = {}
    for fila in cursor.fetchall():
        por_tema[fila['tema']] = {
            'promedio_puntaje': float(fila['promedio_puntaje'] or 0),
            'total_sesiones':   fila['total_sesiones'] or 0,
            'total_aciertos':   fila['total_aciertos'] or 0,
            'total_errores':    fila['total_errores'] or 0,
        }

    conexion.close()
    return {'nombre': nombre, 'por_materia': por_materia, 'por_tema': por_tema}


def obtener_desempeno_clase() -> dict:
    """
    Devuelve desempeño agregado de toda la clase por materia y por tema.
    Identifica las áreas con mayor dificultad del grupo.
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute('SELECT COUNT(*) AS total FROM estudiantes')
    total_estudiantes = cursor.fetchone()['total']

    cursor.execute('''
        SELECT materia,
               ROUND(AVG(puntaje), 1)          AS promedio_puntaje,
               COUNT(DISTINCT estudiante_id)    AS estudiantes,
               SUM(COALESCE(errores,   0))      AS total_errores,
               SUM(COALESCE(intentos,  0))      AS total_intentos
        FROM progreso
        GROUP BY materia
    ''')
    por_materia = {}
    for fila in cursor.fetchall():
        t_int = fila['total_intentos'] or 0
        t_err = fila['total_errores'] or 0
        por_materia[fila['materia']] = {
            'promedio_puntaje': float(fila['promedio_puntaje'] or 0),
            'estudiantes':      fila['estudiantes'] or 0,
            'total_errores':    t_err,
            'total_intentos':   t_int,
            'tasa_error':       round(t_err / max(t_int, 1), 2),
        }

    cursor.execute('''
        SELECT tema,
               ROUND(AVG(puntaje), 1)          AS promedio_puntaje,
               COUNT(DISTINCT estudiante_id)    AS estudiantes
        FROM progreso
        WHERE tema IS NOT NULL AND tema != ''
        GROUP BY tema
        ORDER BY promedio_puntaje ASC
    ''')
    por_tema = {}
    for fila in cursor.fetchall():
        por_tema[fila['tema']] = {
            'promedio_puntaje': float(fila['promedio_puntaje'] or 0),
            'estudiantes':      fila['estudiantes'] or 0,
        }

    conexion.close()
    return {
        'total_estudiantes': total_estudiantes,
        'por_materia':       por_materia,
        'por_tema':          por_tema,
    }


# ---------------------------------------------------------------------------
# Cache de reportes docente
# ---------------------------------------------------------------------------

def obtener_reporte_cacheado(ambito: str, estudiante_id: int | None = None) -> dict | None:
    """Devuelve el reporte más reciente cacheado para el ámbito dado."""
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    if estudiante_id is not None:
        cursor.execute(
            '''SELECT contenido, fuente, fecha FROM reportes
               WHERE ambito = ? AND estudiante_id = ?
               ORDER BY fecha DESC LIMIT 1''',
            (ambito, estudiante_id)
        )
    else:
        cursor.execute(
            '''SELECT contenido, fuente, fecha FROM reportes
               WHERE ambito = ? AND estudiante_id IS NULL
               ORDER BY fecha DESC LIMIT 1''',
            (ambito,)
        )

    fila = cursor.fetchone()
    conexion.close()
    return dict(fila) if fila else None


def guardar_reporte(
    ambito: str,
    contenido: str,
    fuente: str,
    estudiante_id: int | None = None,
):
    """Persiste un reporte generado (IA o fallback) en la tabla de reportes."""
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute(
        '''INSERT INTO reportes (ambito, estudiante_id, contenido, fuente, fecha)
           VALUES (?, ?, ?, ?, ?)''',
        (ambito, estudiante_id, contenido, fuente, fecha)
    )
    conexion.commit()
    conexion.close()
