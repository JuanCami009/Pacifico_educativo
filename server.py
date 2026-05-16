"""
server.py - Servidor Flask para Pacífico Educativo.
Define todas las rutas API y sirve el frontend SPA.
"""
import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify, request, render_template
from utils.database import (
    inicializar_base_de_datos,
    obtener_o_crear_estudiante,
    guardar_puntaje,
    obtener_nivel_maximo,
    contar_niveles_completados,
    obtener_puntajes_por_materia,
    obtener_mejor_puntaje,
)
from data.niveles_contenido import obtener_datos_nivel_completo

app = Flask(__name__, static_folder="static", template_folder="templates")

# Inicializar la base de datos al arrancar el servidor
inicializar_base_de_datos()

MATERIAS = ["matematicas", "lenguaje", "ingles", "biologia"]


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
    """Guarda el puntaje de un nivel. Body: {estudiante_id, materia, nivel, puntaje}"""
    datos = request.get_json(silent=True) or {}
    try:
        guardar_puntaje(
            int(datos["estudiante_id"]),
            datos["materia"],
            int(datos["nivel"]),
            int(datos["puntaje"]),
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


if __name__ == "__main__":
    app.run(debug=True, port=5000)
