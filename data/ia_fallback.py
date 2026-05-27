"""
ia_fallback.py - Respuestas predefinidas para el modo offline.
Se usan automáticamente cuando Ollama no está disponible o tarda demasiado.
Organizadas por personaje y tipo de interacción.
"""

import random


# ── Respuestas por personaje ─────────────────────────────────────────────────

RESPUESTAS_PERSONAJE = {
    "El Riviel": {
        "saludo": [
            "¡Hola, pequeño aventurero! Soy El Riviel, el espíritu del río. 🌊",
            "¡Bienvenido a mi río mágico! ¿Listo para aprender matemáticas conmigo?",
            "¡Ey, amiguito! El río me trajo buenas noticias, ¡hoy aprenderemos juntos!",
            "¡Qué alegría verte! Naveguemos juntos por el mundo de los números. 🚣",
        ],
        "ayuda": [
            "¡No te preocupes! Cuenta despacio, como las olas del río. Uno... dos... tres...",
            "Piensa en los peces del río: si tienes 3 y llegan 2 más, ¿cuántos hay? ¡Tú puedes!",
            "Los números son como los cangrejos: hay que atraparlos con paciencia. 🦀",
            "Recuerda: sumar es juntar y restar es quitar. ¡Como la marea que sube y baja!",
            "¡Tranquilo! Hasta el río más grande empezó con una gota. Inténtalo de nuevo.",
        ],
        "historia": [
            "Había una vez un cangrejo que no sabía contar. Un día, el río le enseñó que cada ola traía un número nuevo. Así aprendió a sumar: ola tras ola. 🌊",
            "En el manglar vivían 5 peces amigos. Un día llegaron 3 más y juntos formaron la pandilla más divertida del Pacífico. ¿Cuántos eran en total? ¡8! 🐟",
            "El Riviel navegaba su canoa cuando encontró 10 estrellas de mar. Le regaló 4 a la Madre de Agua. ¿Cuántas le quedaron? ¡6 brillantes estrellas! ⭐",
        ],
        "pregunta": [
            "Si tienes 4 cangrejos y encuentras 3 más en la playa, ¿cuántos cangrejos tienes?",
            "En el río hay 7 peces. Si 2 se van nadando, ¿cuántos quedan?",
            "¿Cuántas patas tiene un cangrejo? ¡Pista: son más de 5 y menos de 11! 🦀",
            "Si repartes 6 conchas entre 2 amigos por igual, ¿cuántas le tocan a cada uno?",
        ],
        "retroalimentacion_buena": [
            "¡Excelente trabajo! Eres tan rápido como la corriente del río. 🌟",
            "¡Increíble! Los números te obedecen como los peces al río.",
            "¡Muy bien! El Riviel está orgulloso de ti. ¡Sigue así, campeón! 🏆",
        ],
        "retroalimentacion_regular": [
            "¡Buen intento! Cada error es una ola que te acerca a la respuesta correcta.",
            "¡No te rindas! El río no para de fluir y tú no pares de intentar. 💪",
            "¡Casi lo logras! La próxima vez lo harás mejor, estoy seguro.",
        ],
    },

    "La Tunda": {
        "saludo": [
            "¡Hola, mi niño! Soy La Tunda, guardiana de las palabras del bosque. 🌿",
            "¡Bienvenido a mi selva de letras! Aquí las palabras crecen como árboles.",
            "¡Qué bueno que llegaste! Las letras del bosque te estaban esperando. 📖",
            "¡Hola, pequeño lector! ¿Listo para descubrir los secretos de las palabras?",
        ],
        "ayuda": [
            "Escucha el sonido de cada letra, como el canto de los pájaros del bosque. 🐦",
            "Las sílabas son como las ramas: se unen para formar palabras hermosas.",
            "Lee despacio, como caminas por la selva. Cada letra es un paso.",
            "¡No te apures! Las palabras bonitas se arman con calma, como un nido.",
            "Piensa en el sonido: MA-RIM-BA. ¿Ves? Cada parte tiene su música. 🎵",
        ],
        "historia": [
            "En lo profundo del bosque, La Tunda guardaba un libro mágico. Cada vez que un niño aprendía una palabra nueva, una flor nacía en la selva. 🌺",
            "Había una vez una marimba que no tenía nombre. Los niños del pueblo la llamaron 'Alegría', porque su música hacía bailar hasta a los árboles. 🎶",
            "Un tucán curioso encontró letras en las hojas del manglar. Las juntó y formó la palabra 'AMIGO'. Desde ese día, nunca más estuvo solo. 🦜",
        ],
        "pregunta": [
            "¿Con qué letra empieza la palabra 'Árbol'? 🌳",
            "¿Cuántas sílabas tiene la palabra 'MA-RIM-BA'?",
            "¿Qué palabra se forma si juntas 'PA' + 'CÍ' + 'FI' + 'CO'?",
            "¿Cuál es el opuesto de 'grande'? ¡Piensa en los animales del bosque!",
        ],
        "retroalimentacion_buena": [
            "¡Maravilloso! Tus palabras brillan como las luciérnagas del bosque. ✨",
            "¡Excelente! La Tunda aplaude tu sabiduría con las letras. 👏",
            "¡Eres un maestro de las palabras! El bosque celebra contigo. 🎉",
        ],
        "retroalimentacion_regular": [
            "¡Buen esfuerzo! Las letras a veces son traviesas, pero tú las dominarás.",
            "¡Ánimo! Cada palabra que aprendes es una semilla que crece. 🌱",
            "¡Casi! Lee de nuevo con calma, como el viento entre los árboles.",
        ],
    },

    "El Duende": {
        "saludo": [
            "Hello, my friend! Soy El Duende y te enseñaré inglés de forma divertida! 🎩",
            "Welcome! ¿Listo para aprender palabras mágicas en inglés? Let's go!",
            "¡Hola, amiguito! Today is a great day to learn English! 🌟",
            "Hey there! El Duende está aquí para ayudarte con el inglés. Ready?",
        ],
        "ayuda": [
            "Remember: BLUE es azul, RED es rojo y GREEN es verde. ¡Los colores son fáciles! 🎨",
            "Repite conmigo: ONE, TWO, THREE... ¡Los números en inglés suenan divertido!",
            "Think about it slowly. En inglés, FISH es pez y WHALE es ballena. 🐋",
            "¡No te preocupes! Learning es aprender, y tú estás aprendiendo muy bien.",
            "Escucha la palabra en tu mente: MONKEY suena como 'mon-ki'. ¡Fácil! 🐒",
        ],
        "historia": [
            "Once upon a time, a little FISH learned to count: ONE, TWO, THREE! And the whole RIVER celebrated. 🐟",
            "The MONKEY said 'HELLO' to the WHALE. The WHALE said 'HI' back. And they became FRIENDS forever! 🐋🐒",
            "In the JUNGLE, El Duende found a RAINBOW with all the COLORS: RED, BLUE, GREEN, YELLOW... ¡Mágico! 🌈",
        ],
        "pregunta": [
            "¿Cómo se dice 'pez' en inglés? Pista: empieza con F... 🐟",
            "What color is the sky? ¿De qué color es el cielo? ¡En inglés!",
            "¿Cómo se dice 'buenos días' en inglés? Good _____!",
            "How do you say 'amigo' in English? Pista: empieza con F! 😊",
        ],
        "retroalimentacion_buena": [
            "Excellent! ¡Eres un campeón del inglés! Very good! 🌟",
            "Amazing! El Duende está muy orgulloso. You're doing great! 🎩",
            "Perfect! Hablas inglés como un nativo del Pacífico mágico. ⭐",
        ],
        "retroalimentacion_regular": [
            "Good try! ¡Buen intento! Practice makes perfect. 💪",
            "Don't give up! No te rindas, cada intento te hace mejor.",
            "Almost! ¡Casi lo tienes! Try again, you can do it! 🎯",
        ],
    },

    "La Madre de Agua": {
        "saludo": [
            "¡Bienvenido, pequeño guardián! Soy la Madre de Agua, protectora de toda la vida. 💧",
            "¡Hola, mi niño! El agua del Pacífico te da la bienvenida. 🌊",
            "¡Qué alegría! Un nuevo guardián viene a aprender sobre la naturaleza. 🌿",
            "Soy la Madre de Agua y juntos cuidaremos los seres vivos del Pacífico.",
        ],
        "ayuda": [
            "Observa con cuidado: los animales se mueven y las plantas tienen raíces. 🌱",
            "Recuerda: los mamíferos tienen pelo, los peces tienen escamas y las aves tienen plumas.",
            "La cadena alimenticia es como un río: la energía fluye del sol a las plantas y de las plantas a los animales. ☀️",
            "¡Piensa en nuestro manglar! Las raíces están en el agua y las hojas en el aire.",
            "Cada ser vivo tiene su lugar especial en el ecosistema. ¡Ninguno sobra! 🦜",
        ],
        "historia": [
            "En el manglar más antiguo del Pacífico vivía una familia de cangrejos. Ellos limpiaban el agua para que los peces pudieran respirar. Así funciona la naturaleza: todos nos ayudamos. 🦀",
            "La Madre de Agua vio cómo un niño sembró un árbol junto al río. Con el tiempo, ese árbol dio sombra a los peces y hogar a los pájaros. Una semilla cambió todo. 🌳",
            "Un día, el manglar se enfermó porque alguien tiró basura al río. Los animales se unieron para limpiarlo y la vida volvió a florecer. ¡Cuidar el agua es cuidar la vida! 💧",
        ],
        "pregunta": [
            "¿Qué necesitan las plantas para vivir? Pista: viene del cielo y brilla mucho. ☀️",
            "¿Los delfines son peces o mamíferos? ¡Piensa en cómo respiran! 🐬",
            "¿Qué pasa si tiramos basura al río? ¿Cómo afecta a los animales?",
            "¿Cuál es la diferencia entre un animal y una planta? ¡Las plantas no caminan! 🌿",
        ],
        "retroalimentacion_buena": [
            "¡Maravilloso, pequeño guardián! La naturaleza te agradece. 🌟",
            "¡Excelente! Serás un gran protector del Pacífico. 💧",
            "¡Increíble! La Madre de Agua celebra tu sabiduría. 🎉",
        ],
        "retroalimentacion_regular": [
            "¡Buen intento! La naturaleza nos enseña con paciencia. 🌱",
            "¡No te desanimes! Hasta el río más largo empezó como un arroyito.",
            "¡Casi lo logras! Observa la naturaleza y encontrarás la respuesta. 🔍",
        ],
    },
}


# ── Respuestas genéricas (cuando no se identifica el personaje) ──────────────

RESPUESTAS_GENERICAS = {
    "saludo": [
        "¡Hola, aventurero! Bienvenido al mundo de Pacífico Educativo. 🌿",
        "¡Qué bueno que estás aquí! ¿Listo para aprender cosas increíbles?",
    ],
    "ayuda": [
        "¡Tú puedes! Lee con calma y piensa antes de responder. 💪",
        "¡No te rindas! Cada intento te hace más fuerte.",
        "Respira profundo y vuelve a intentarlo. ¡La respuesta está cerca!",
    ],
    "historia": [
        "En el Pacífico colombiano hay playas hermosas, selvas mágicas y ríos llenos de vida. ¡Es un lugar increíble para aprender! 🌊",
    ],
    "pregunta": [
        "¿Sabías que el Pacífico colombiano es uno de los lugares con más biodiversidad del mundo? 🌿",
        "¿Cuántos colores puedes ver en un atardecer del Pacífico? ¡Inténtalo! 🌅",
    ],
    "retroalimentacion_buena": [
        "¡Excelente trabajo! ¡Sigue así, campeón! 🏆",
    ],
    "retroalimentacion_regular": [
        "¡Buen esfuerzo! La próxima vez lo harás mejor. 💪",
    ],
    "default": [
        "¡Qué interesante pregunta! Sigue explorando y aprendiendo. 🌟",
        "¡Me encanta tu curiosidad! Eso es lo más importante para aprender.",
        "¡Sigue así! Cada día aprendes algo nuevo en el Pacífico. 🌊",
    ],
}


# ── Mapeo de materia a personaje ─────────────────────────────────────────────

MATERIA_A_PERSONAJE = {
    "matematicas": "El Riviel",
    "lenguaje": "La Tunda",
    "ingles": "El Duende",
    "biologia": "La Madre de Agua",
}


# ── Funciones de acceso al fallback ──────────────────────────────────────────

def obtener_respuesta_fallback(personaje: str, tipo: str = "default") -> str:
    """
    Devuelve una respuesta aleatoria del fallback para un personaje y tipo dados.

    Args:
        personaje: Nombre del personaje (ej. 'El Riviel').
        tipo:      Tipo de respuesta (saludo, ayuda, historia, pregunta,
                   retroalimentacion_buena, retroalimentacion_regular, default).

    Returns:
        String con la respuesta seleccionada aleatoriamente.
    """
    # Intentar obtener del personaje específico
    datos_personaje = RESPUESTAS_PERSONAJE.get(personaje, {})
    respuestas = datos_personaje.get(tipo)

    # Si no hay respuestas para ese tipo en el personaje, usar genéricas
    if not respuestas:
        respuestas = RESPUESTAS_GENERICAS.get(tipo, RESPUESTAS_GENERICAS["default"])

    return random.choice(respuestas)


def clasificar_mensaje(mensaje: str) -> str:
    """
    Clasifica el mensaje del usuario para seleccionar el tipo de fallback adecuado.
    Usa detección simple por palabras clave.

    Args:
        mensaje: Texto enviado por el usuario.

    Returns:
        Tipo de respuesta: 'saludo', 'ayuda', 'historia', 'pregunta' o 'default'.
    """
    texto = mensaje.lower().strip()

    # Saludos
    palabras_saludo = ["hola", "buenos", "hey", "hi", "hello", "qué tal", "buenas"]
    if any(p in texto for p in palabras_saludo):
        return "saludo"

    # Ayuda
    palabras_ayuda = [
        "ayuda", "ayúdame", "no entiendo", "no sé", "difícil",
        "pista", "explica", "cómo", "help", "no puedo",
    ]
    if any(p in texto for p in palabras_ayuda):
        return "ayuda"

    # Historia
    palabras_historia = [
        "cuento", "historia", "cuéntame", "narra", "había una vez",
        "relato", "aventura",
    ]
    if any(p in texto for p in palabras_historia):
        return "historia"

    # Pregunta educativa
    palabras_pregunta = [
        "pregunta", "quiz", "pregúntame", "evalúa", "examen",
        "hazme una pregunta", "ponme una pregunta",
    ]
    if any(p in texto for p in palabras_pregunta):
        return "pregunta"

    return "default"
