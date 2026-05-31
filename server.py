"""
server.py - Servidor Flask para Pacífico Educativo.
Define todas las rutas API y sirve el frontend SPA.
"""
import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify, request, render_template
from utils.ollama_service import servicio_ia
from data.ia_fallback import MATERIA_A_PERSONAJE
from utils.database import (
    inicializar_base_de_datos,
    obtener_o_crear_estudiante,
    guardar_puntaje,
    obtener_nivel_maximo,
    contar_niveles_completados,
    obtener_puntajes_por_materia,
    obtener_mejor_puntaje,
    listar_estudiantes,
    obtener_desempeno_estudiante,
    obtener_desempeno_clase,
    obtener_reporte_cacheado,
    guardar_reporte,
)
from data.niveles_contenido import obtener_datos_nivel_completo

app = Flask(__name__, static_folder="static", template_folder="templates")

# Inicializar la base de datos al arrancar el servidor
inicializar_base_de_datos()

MATERIAS = ["matematicas", "lenguaje", "ingles", "biologia"]

# PIN del panel docente: configurable vía variable de entorno DOCENTE_PIN.
# Por defecto "1234" — cambiar en producción.
DOCENTE_PIN = os.getenv("DOCENTE_PIN", "1234")
IA_NIVELES_HABILITADOS = {
    materia: {1, 2, 3, 4, 5} for materia in MATERIAS
}


def _transformar_rutas(obj):
    """
    Reemplaza recursivamente 'assets/' por '/static/' en strings del dict,
    para que las rutas de imágenes funcionen en el navegador.
    """
    if isinstance(obj, dict):
        return {k: _transformar_rutas(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_transformar_rutas(i) for i in obj]
    if isinstance(obj, str):
        return obj.replace("assets/", "/static/")
    return obj


def _leer_entero(valor, por_defecto=0):
    try:
        return int(valor)
    except (TypeError, ValueError):
        return por_defecto


def _verificar_pin(req) -> bool:
    """Comprueba el PIN docente enviado en el header X-Docente-Pin."""
    pin = (req.headers.get("X-Docente-Pin") or "").strip()
    return pin == DOCENTE_PIN


def _ia_habilitada_para_nivel(materia, nivel):
    return nivel in IA_NIVELES_HABILITADOS.get(materia, set())


def _obtener_contexto_ia_nivel(materia, nivel):
    datos = obtener_datos_nivel_completo(materia, nivel)
    if not datos:
        return None

    contexto = {
        "materia": materia,
        "nivel": nivel,
        "nombre": datos.get("nombre", ""),
        "personaje": datos.get("personaje", ""),
        "minijuego": datos.get("minijuego", ""),
        "modo": datos.get("modo", ""),
        "instruccion": datos.get("instruccion", ""),
        "frase_intro": datos.get("frase_intro", ""),
    }

    contenido = datos.get("datos")
    if isinstance(contenido, dict):
        contexto["conteos"] = {
            "items": len(contenido.get("items", [])) if isinstance(contenido.get("items"), list) else 0,
            "piezas": len(contenido.get("piezas", [])) if isinstance(contenido.get("piezas"), list) else 0,
            "zonas": len(contenido.get("zonas", [])) if isinstance(contenido.get("zonas"), list) else 0,
        }
    elif isinstance(contenido, list):
        contexto["conteos"] = {"items": len(contenido)}

    return contexto


# ── Ruta principal ───────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# ── API: Estudiantes ─────────────────────────────────────────────────────────

@app.route("/api/estudiante/login", methods=["POST"])
def login():
    """Busca o crea un estudiante por nombre. Devuelve {id, nombre}."""
    datos = request.get_json(silent=True) or {}
    nombre = (datos.get("nombre") or "").strip()
    if not nombre:
        return jsonify({"error": "El nombre es requerido"}), 400

    estudiante = obtener_o_crear_estudiante(nombre)
    return jsonify(dict(estudiante))


@app.route("/api/estudiantes")
def get_estudiantes():
    """Lista todos los estudiantes con resumen de progreso (para la pantalla de login)."""
    estudiantes = listar_estudiantes()
    return jsonify(estudiantes)


@app.route("/api/progreso/reset", methods=["POST"])
def reset_progreso():
    """Borra todo el progreso de un estudiante para que comience desde cero."""
    datos = request.get_json(silent=True) or {}
    estudiante_id = datos.get("estudiante_id")
    if not estudiante_id:
        return jsonify({"error": "estudiante_id requerido"}), 400
    from utils.database import obtener_conexion
    con = obtener_conexion()
    con.execute("DELETE FROM progreso WHERE estudiante_id = ?", (int(estudiante_id),))
    con.commit()
    con.close()
    return jsonify({"ok": True})


# ── API: Progreso ────────────────────────────────────────────────────────────

@app.route("/api/progreso/<int:estudiante_id>")
def get_progreso(estudiante_id):
    """
    Devuelve el progreso completo del estudiante:
    {materia: {nivel_maximo, completados, puntajes[5]}}
    """
    resultado = {}
    for mat in MATERIAS:
        puntajes = [
            obtener_mejor_puntaje(estudiante_id, mat, nivel)
            for nivel in range(1, 6)
        ]
        resultado[mat] = {
            "nivel_maximo": obtener_nivel_maximo(estudiante_id, mat),
            "completados": contar_niveles_completados(estudiante_id, mat),
            "puntajes": puntajes,
        }
    return jsonify(resultado)


@app.route("/api/progreso/guardar", methods=["POST"])
def guardar_progreso():
    """
    Guarda el desempeño de un nivel.
    Body: {estudiante_id, materia, nivel, puntaje, metricas?}
    metricas: {aciertos, errores, intentos, duracion_seg}
    """
    datos = request.get_json(silent=True) or {}
    try:
        materia  = datos["materia"]
        nivel    = int(datos["nivel"])
        metricas = datos.get("metricas") or {}

        # Resolver el tema del nivel desde el contenido pedagógico
        nivel_info = obtener_datos_nivel_completo(materia, nivel)
        tema = nivel_info.get("tema", "") if nivel_info else ""

        guardar_puntaje(
            int(datos["estudiante_id"]),
            materia,
            nivel,
            int(datos["puntaje"]),
            aciertos=int(metricas.get("aciertos", 0)),
            errores=int(metricas.get("errores", 0)),
            intentos=int(metricas.get("intentos", 0)),
            duracion_seg=int(metricas.get("duracion_seg", 0)),
            tema=tema,
        )
        return jsonify({"ok": True})
    except (KeyError, ValueError) as e:
        return jsonify({"error": str(e)}), 400


# ── API: Niveles ─────────────────────────────────────────────────────────────

@app.route("/api/niveles/<materia>/<int:nivel>")
def get_nivel(materia, nivel):
    """
    Devuelve los datos pedagógicos de un nivel específico.
    Las rutas de imágenes se transforman de assets/ a /static/.
    """
    datos = obtener_datos_nivel_completo(materia, nivel)
    if not datos:
        return jsonify({"error": "Nivel no encontrado"}), 404
    return jsonify(_transformar_rutas(datos))


@app.route("/api/niveles/<materia>")
def get_niveles_materia(materia):
    """Devuelve la lista de todos los niveles de una materia (sin datos pesados)."""
    from data.niveles_contenido import TODOS_LOS_NIVELES
    niveles = [
        {"nivel": n["nivel"], "nombre": n["nombre"], "personaje": n["personaje"]}
        for n in TODOS_LOS_NIVELES
        if n["materia"] == materia
    ]
    return jsonify(niveles)


# ── API: IA Local (Ollama) ────────────────────────────────────────────────────

@app.route("/api/ia/estado")
def ia_estado():
    """Verifica si el servicio de IA local (Ollama) está disponible."""
    return jsonify(servicio_ia.estado())


@app.route("/api/ia/chat", methods=["POST"])
def ia_chat():
    """Envía un mensaje al personaje IA y recibe una respuesta."""
    datos = request.get_json(silent=True) or {}
    mensaje = (datos.get("mensaje") or "").strip()
    personaje = (datos.get("personaje") or "").strip()
    materia = (datos.get("materia") or "").strip()
    nivel = _leer_entero(datos.get("nivel", 0))

    if not mensaje:
        return jsonify({"error": "El mensaje es requerido"}), 400

    # Si no se especificó personaje, inferirlo de la materia
    if not personaje and materia:
        personaje = MATERIA_A_PERSONAJE.get(materia, "")

    contexto_nivel = _obtener_contexto_ia_nivel(materia, nivel) if _ia_habilitada_para_nivel(materia, nivel) else None

    resultado = servicio_ia.generar_respuesta(
        personaje=personaje,
        mensaje=mensaje,
        contexto_materia=materia,
        contexto_nivel=nivel,
        contexto_nivel_info=contexto_nivel,
    )
    return jsonify(resultado)


@app.route("/api/ia/pista", methods=["POST"])
def ia_pista():
    """Genera una pista corta y contextual para el nivel actual."""
    datos = request.get_json(silent=True) or {}
    personaje = (datos.get("personaje") or "").strip()
    materia = (datos.get("materia") or "").strip()
    nivel = _leer_entero(datos.get("nivel", 0))
    instruccion = (datos.get("instruccion") or "").strip()
    minijuego = (datos.get("minijuego") or "").strip()

    if not materia or not nivel:
        return jsonify({
            "respuesta": "Lee la instruccion con calma y prueba paso a paso.",
            "fuente": "fallback",
            "modelo": servicio_ia.modelo,
            "disponible": False,
            "error": "Materia y nivel son requeridos para una pista contextual.",
        }), 400

    if not personaje and materia:
        personaje = MATERIA_A_PERSONAJE.get(materia, "")

    contexto_nivel = _obtener_contexto_ia_nivel(materia, nivel) if _ia_habilitada_para_nivel(materia, nivel) else None
    resultado = servicio_ia.generar_pista(
        personaje=personaje,
        materia=materia,
        nivel=nivel,
        instruccion=instruccion,
        minijuego=minijuego,
        contexto_nivel_info=contexto_nivel,
    )
    return jsonify(resultado)


@app.route("/api/ia/retroalimentacion", methods=["POST"])
def ia_retroalimentacion():
    """Genera retroalimentación IA después de completar un nivel."""
    datos = request.get_json(silent=True) or {}
    personaje = (datos.get("personaje") or "").strip()
    materia = (datos.get("materia") or "").strip()
    nivel = _leer_entero(datos.get("nivel", 0))
    puntaje = _leer_entero(datos.get("puntaje", 0))

    if not personaje and materia:
        personaje = MATERIA_A_PERSONAJE.get(materia, "")

    contexto_nivel = _obtener_contexto_ia_nivel(materia, nivel) if _ia_habilitada_para_nivel(materia, nivel) else None

    resultado = servicio_ia.generar_retroalimentacion(
        personaje=personaje,
        materia=materia,
        nivel=nivel,
        puntaje=puntaje,
        contexto_nivel_info=contexto_nivel,
    )
    return jsonify(resultado)


# ── API: Panel Docente ────────────────────────────────────────────────────────

@app.route("/api/docente/login", methods=["POST"])
def docente_login():
    """
    Valida el PIN docente. El PIN se envía también en X-Docente-Pin header.
    Responde {ok: true} si correcto, 401 si incorrecto.
    """
    if _verificar_pin(request):
        return jsonify({"ok": True})
    return jsonify({"error": "PIN incorrecto"}), 401


@app.route("/api/docente/estudiantes")
def docente_estudiantes():
    """Lista todos los estudiantes con resumen de progreso."""
    if not _verificar_pin(request):
        return jsonify({"error": "PIN incorrecto"}), 401
    return jsonify({"estudiantes": listar_estudiantes()})


@app.route("/api/docente/reporte/estudiante/<int:estudiante_id>", methods=["POST"])
def docente_reporte_estudiante(estudiante_id):
    """
    Devuelve el reporte IA del estudiante. Si ya hay uno cacheado lo usa,
    a menos que se pase ?regenerar=1.
    """
    if not _verificar_pin(request):
        return jsonify({"error": "PIN incorrecto"}), 401

    regenerar = request.args.get("regenerar") == "1"

    if not regenerar:
        cache = obtener_reporte_cacheado("estudiante", estudiante_id)
        if cache:
            return jsonify({
                "reporte": cache["contenido"],
                "fuente":  cache["fuente"],
                "fecha":   cache["fecha"],
            })

    desempeno = obtener_desempeno_estudiante(estudiante_id)
    resultado = servicio_ia.generar_reporte_docente(
        desempeno, "estudiante", nombre=desempeno.get("nombre", "")
    )
    guardar_reporte("estudiante", resultado["respuesta"], resultado["fuente"], estudiante_id)

    return jsonify({
        "reporte": resultado["respuesta"],
        "fuente":  resultado["fuente"],
    })


@app.route("/api/docente/reporte/clase", methods=["POST"])
def docente_reporte_clase():
    """
    Devuelve el reporte IA de la clase completa. Cache a menos de ?regenerar=1.
    """
    if not _verificar_pin(request):
        return jsonify({"error": "PIN incorrecto"}), 401

    regenerar = request.args.get("regenerar") == "1"

    if not regenerar:
        cache = obtener_reporte_cacheado("clase")
        if cache:
            return jsonify({
                "reporte": cache["contenido"],
                "fuente":  cache["fuente"],
                "fecha":   cache["fecha"],
            })

    desempeno = obtener_desempeno_clase()
    resultado = servicio_ia.generar_reporte_docente(desempeno, "clase")
    guardar_reporte("clase", resultado["respuesta"], resultado["fuente"])

    return jsonify({
        "reporte": resultado["respuesta"],
        "fuente":  resultado["fuente"],
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
