"""
levels.py - Definición de contenidos para cada nivel y materia.
Aquí se configuran los items, instrucciones y parámetros de cada minijuego.
"""

# Configuración de niveles para el minijuego Point and Click (Nivel 1 y 4)
POINT_AND_CLICK_LEVELS = {
    'matematicas': {
        1: {
            'instruccion': "Toca exactamente 5 cangrejos rojos",
            'items': [
                {'nombre': 'cangrejo', 'es_correcto': True, 'imagen': 'assets/images/characters/cangrejo.png'},
                {'nombre': 'cangrejo', 'es_correcto': True, 'imagen': 'assets/images/characters/cangrejo.png'},
                {'nombre': 'cangrejo', 'es_correcto': True, 'imagen': 'assets/images/characters/cangrejo.png'},
                {'nombre': 'cangrejo', 'es_correcto': True, 'imagen': 'assets/images/characters/cangrejo.png'},
                {'nombre': 'cangrejo', 'es_correcto': True, 'imagen': 'assets/images/characters/cangrejo.png'},
                {'nombre': 'piedra', 'es_correcto': False, 'imagen': 'assets/images/characters/piedra.png'},
                {'nombre': 'piedra', 'es_correcto': False, 'imagen': 'assets/images/characters/piedra.png'},
            ]
        },
        4: {
            'instruccion': "Encuentra todos los peces azules (hay 4)",
            'items': [
                {'nombre': 'pez', 'es_correcto': True, 'imagen': 'assets/images/characters/pez_azul.png'},
                {'nombre': 'pez', 'es_correcto': True, 'imagen': 'assets/images/characters/pez_azul.png'},
                {'nombre': 'pez', 'es_correcto': True, 'imagen': 'assets/images/characters/pez_azul.png'},
                {'nombre': 'pez', 'es_correcto': True, 'imagen': 'assets/images/characters/pez_azul.png'},
                {'nombre': 'pez_rojo', 'es_correcto': False, 'imagen': 'assets/images/characters/pez_rojo.png'},
            ]
        }
    },
    'ingles': {
        1: {
            'instruccion': "Toca los objetos de color RED (Rojo)",
            'items': [
                {'nombre': 'flor', 'es_correcto': True, 'imagen': 'assets/images/characters/flor_roja.png'},
                {'nombre': 'fruta', 'es_correcto': True, 'imagen': 'assets/images/characters/fruta_roja.png'},
                {'nombre': 'hoja', 'es_correcto': False, 'imagen': 'assets/images/characters/hoja_verde.png'},
            ]
        }
    },
    'biologia': {
        1: {
            'instruccion': "Toca solo los animales (no las plantas)",
            'items': [
                {'nombre': 'mono', 'es_correcto': True, 'imagen': 'assets/images/characters/mono.png'},
                {'nombre': 'ballena', 'es_correcto': True, 'imagen': 'assets/images/characters/ballena.png'},
                {'nombre': 'palma', 'es_correcto': False, 'imagen': 'assets/images/characters/palma.png'},
                {'nombre': 'flor', 'es_correcto': False, 'imagen': 'assets/images/characters/flor.png'},
            ]
        }
    }
}

# Configuración para Drag and Drop (Nivel 2 y 5)
DRAG_AND_DROP_LEVELS = {
    'matematicas': {
        2: [
            ("Triangulo", "Tiene 3 lados"),
            ("Cuadrado", "Tiene 4 lados iguales"),
            ("Circulo", "Es redondo"),
        ]
    },
    'biologia': {
        2: [
            ("Manglar", "Arboles en el agua"),
            ("Ballena", "Mamifero marino"),
            ("Tucan", "Ave de pico largo"),
        ]
    },
    'lenguaje': {
        2: [
            ("Sustantivo", "Nombra personas o cosas"),
            ("Verbo", "Expresa una accion"),
            ("Adjetivo", "Dice como es algo"),
        ]
    }
}

# Configuración para Puzzle (Nivel 3)
PUZZLE_LEVELS = {
    'biologia': {
        3: [
            ("BALLENA", "El animal mas grande del mar"),
            ("DELFIN", "Animal marino muy inteligente"),
            ("TIBURON", "Pez con muchos dientes"),
        ]
    },
    'lenguaje': {
        3: [
            ("PACIFICO", "Nombre de nuestro oceano"),
            ("MARIMBA", "Piano de la selva"),
            ("LITORAL", "La costa de nuestra region"),
        ]
    }
}

def obtener_datos_nivel(materia, nivel, tipo_juego):
    """Retorna los datos específicos del nivel o datos genéricos si no existen."""
    if tipo_juego == 'point_and_click':
        return POINT_AND_CLICK_LEVELS.get(materia, {}).get(nivel, None)
    elif tipo_juego == 'drag_and_drop':
        return DRAG_AND_DROP_LEVELS.get(materia, {}).get(nivel, None)
    elif tipo_juego == 'puzzle':
        return PUZZLE_LEVELS.get(materia, {}).get(nivel, None)
    return None
