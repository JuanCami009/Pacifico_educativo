"""
niveles_contenido.py - Definición de contenidos pedagógicos.
Contiene los 20 niveles del juego Pacífico Educativo organizados por materia.
No contiene lógica, solo la estructura de datos que consumirán los minijuegos.
"""

# Lista de todos los niveles del juego
TODOS_LOS_NIVELES = [
    # ---------------------------------------------------------
    # MATEMÁTICAS - Personaje: El Riviel
    # ---------------------------------------------------------
    {
        "materia": "matematicas",
        "nivel": 1,
        "nombre": "Los cangrejos del manglar",
        "personaje": "El Riviel",
        "frase_intro": (
            "Naveguemos juntos por el río... "
            "¿Puedes atrapar los números que te pido?"
        ),
        "minijuego": "atrapa_ranas",
        "instruccion": "La gaviota atrapa los cangrejos con el número que indica el Riviel.",
        "audio_intro": "assets/audio/riviel_intro.ogg",
        "configuracion": {
            "rondas": 5,
            "insectos_para_ganar_ronda": 3,
            "vidas": 3,
            "rango_numeros": [1, 9],
            "velocidad_base": 1.5,
            "imagenes": {
                "cangrejo": "/static/images/level_matematicas/cangrejo.png",
                "gaviota": "/static/images/level_matematicas/gaviota.png",
                "riviel": "/static/images/level_matematicas/riviel.png",
            },
        },
    },
    {
        "materia": "matematicas",
        "nivel": 2,
        "nombre": "Pesca Abundante",
        "personaje": "El Riviel",
        "frase_intro": "¿Sabes sumar? Ayúdame a organizar la pesca en las canoas correctas.",
        "minijuego": "drag_and_drop",
        "instruccion": "Arrastra cada grupo de peces a la canoa con el número correcto",
        "audio_intro": "assets/audio/riviel_m2.ogg",
        "datos": {
            "piezas": [
                {"imagen": "assets/images/ui/grupo_3peces.png", "nombre": "3 peces", "zona_destino": "canoa_3"},
                {"imagen": "assets/images/ui/grupo_5peces.png", "nombre": "5 peces", "zona_destino": "canoa_5"},
                {"imagen": "assets/images/ui/grupo_2peces.png", "nombre": "2 peces", "zona_destino": "canoa_2"}
            ],
            "zonas": [
                {"id": "canoa_3", "etiqueta": "2 + 1", "posicion": (500, 150), "imagen": "assets/images/ui/canoa.png"},
                {"id": "canoa_5", "etiqueta": "3 + 2", "posicion": (500, 300), "imagen": "assets/images/ui/canoa.png"},
                {"id": "canoa_2", "etiqueta": "1 + 1", "posicion": (500, 450), "imagen": "assets/images/ui/canoa.png"}
            ]
        }
    },
    {
        "materia": "matematicas",
        "nivel": 3,
        "nombre": "El Misterio de la Marea",
        "personaje": "El Riviel",
        "frase_intro": "La marea se llevó algunos caracoles. Completa la resta para saber cuántos quedan.",
        "minijuego": "puzzle",
        "modo": "completar",
        "instruccion": "Arrastra el número correcto para completar la resta",
        "audio_intro": "assets/audio/riviel_m3.ogg",
        "datos": {
            "imagen_base": "assets/images/ui/resta_5_menos_2.png",
            "piezas": [
                {"imagen": "assets/images/ui/num_3.png", "texto": "3", "posicion": (400, 350)},
                {"imagen": "assets/images/ui/num_4.png", "texto": "4", "posicion": (100, 100)}, # Incorrecta (usada como trampa visual si soporta)
                {"imagen": "assets/images/ui/num_2.png", "texto": "2", "posicion": (100, 500)}  # Incorrecta
            ]
        }
    },
    {
        "materia": "matematicas",
        "nivel": 4,
        "nombre": "El Tesoro Multiplicado",
        "personaje": "El Riviel",
        "frase_intro": "Mira todas estas conchas brillantes. Encuentra los grupos que forman un 2x3.",
        "minijuego": "point_and_click",
        "instruccion": "Toca los grupos que contienen exactamente 6 conchas",
        "audio_intro": "assets/audio/riviel_m4.ogg",
        "datos": {
            "items": [
                {"imagen": "assets/images/ui/grupo_6conchas.png", "es_correcto": True, "nombre": "6 conchas"},
                {"imagen": "assets/images/ui/grupo_6conchas_b.png", "es_correcto": True, "nombre": "6 conchas"},
                {"imagen": "assets/images/ui/grupo_4conchas.png", "es_correcto": False, "nombre": "4 conchas"},
                {"imagen": "assets/images/ui/grupo_5conchas.png", "es_correcto": False, "nombre": "5 conchas"},
                {"imagen": "assets/images/ui/grupo_8conchas.png", "es_correcto": False, "nombre": "8 conchas"}
            ]
        }
    },
    {
        "materia": "matematicas",
        "nivel": 5,
        "nombre": "El Reparto en el Pueblo",
        "personaje": "El Riviel",
        "frase_intro": "Hoy fue un gran día de pesca. Ayuda a repartir los peces en las canastas por igual.",
        "minijuego": "drag_and_drop",
        "instruccion": "Reparte 12 peces en 3 canastas (4 peces en cada una)",
        "audio_intro": "assets/audio/riviel_m5.ogg",
        "datos": {
            "piezas": [
                {"imagen": "assets/images/ui/grupo_4peces.png", "nombre": "4 peces", "zona_destino": "canasta_1"},
                {"imagen": "assets/images/ui/grupo_4peces.png", "nombre": "4 peces", "zona_destino": "canasta_2"},
                {"imagen": "assets/images/ui/grupo_4peces.png", "nombre": "4 peces", "zona_destino": "canasta_3"}
            ],
            "zonas": [
                {"id": "canasta_1", "etiqueta": "Canasta A", "posicion": (500, 150), "imagen": "assets/images/ui/canasta.png"},
                {"id": "canasta_2", "etiqueta": "Canasta B", "posicion": (500, 300), "imagen": "assets/images/ui/canasta.png"},
                {"id": "canasta_3", "etiqueta": "Canasta C", "posicion": (500, 450), "imagen": "assets/images/ui/canasta.png"}
            ]
        }
    },

    # ---------------------------------------------------------
    # LENGUAJE - Personaje: La Tunda
    # ---------------------------------------------------------
    {
        "materia": "lenguaje",
        "nivel": 1,
        "nombre": "Voces del Bosque",
        "personaje": "La Tunda",
        "frase_intro": "Escucha las vocales que el viento trae... toca las imágenes que empiecen con 'A'.",
        "minijuego": "point_and_click",
        "instruccion": "Toca todos los elementos que empiecen con la letra A",
        "audio_intro": "assets/audio/tunda_l1.ogg",
        "datos": {
            "items": [
                {"imagen": "assets/images/characters/arbol.png", "es_correcto": True, "nombre": "árbol"},
                {"imagen": "assets/images/characters/agua.png", "es_correcto": True, "nombre": "agua"},
                {"imagen": "assets/images/characters/ave.png", "es_correcto": True, "nombre": "ave"},
                {"imagen": "assets/images/characters/mono.png", "es_correcto": False, "nombre": "mono"},
                {"imagen": "assets/images/characters/pez.png", "es_correcto": False, "nombre": "pez"}
            ]
        }
    },
    {
        "materia": "lenguaje",
        "nivel": 2,
        "nombre": "Armando el Currulao",
        "personaje": "La Tunda",
        "frase_intro": "Las palabras bailan como el agua. Únelas para formar palabras de nuestra tierra.",
        "minijuego": "drag_and_drop",
        "instruccion": "Arrastra la sílaba correcta para completar cada palabra",
        "audio_intro": "assets/audio/tunda_l2.ogg",
        "datos": {
            "piezas": [
                {"imagen": "assets/images/ui/silaba_rim.png", "nombre": "RIM", "zona_destino": "ma_ba"},
                {"imagen": "assets/images/ui/silaba_ta.png", "nombre": "TA", "zona_destino": "chon_duro"},
                {"imagen": "assets/images/ui/silaba_glar.png", "nombre": "GLAR", "zona_destino": "man"}
            ],
            "zonas": [
                {"id": "ma_ba", "etiqueta": "MA ___ BA", "posicion": (500, 150), "imagen": "assets/images/ui/letrero_vacio.png"},
                {"id": "chon_duro", "etiqueta": "CHON ___ DURO", "posicion": (500, 300), "imagen": "assets/images/ui/letrero_vacio.png"},
                {"id": "man", "etiqueta": "MAN ___", "posicion": (500, 450), "imagen": "assets/images/ui/letrero_vacio.png"}
            ]
        }
    },
    {
        "materia": "lenguaje",
        "nivel": 3,
        "nombre": "El Nombre Perdido",
        "personaje": "La Tunda",
        "frase_intro": "A este animal se le borró una sílaba de su nombre. ¡Ayúdalo a recordarla!",
        "minijuego": "puzzle",
        "modo": "completar",
        "instruccion": "Arrastra la sílaba 'LLE' al centro de la palabra BA_NA",
        "audio_intro": "assets/audio/tunda_l3.ogg",
        "datos": {
            "imagen_base": "assets/images/characters/ballena_letrero.png",
            "piezas": [
                {"imagen": "assets/images/ui/silaba_lle.png", "texto": "LLE", "posicion": (400, 300)}
            ]
        }
    },
    {
        "materia": "lenguaje",
        "nivel": 4,
        "nombre": "Historias del Río",
        "personaje": "La Tunda",
        "frase_intro": "Ordena estas palabras para contar una hermosa historia sobre nuestro río.",
        "minijuego": "puzzle",
        "modo": "secuencia",
        "instruccion": "Ordena la oración: EL RÍO ES VIDA",
        "audio_intro": "assets/audio/tunda_l4.ogg",
        "datos": [
            {"texto": "EL"},
            {"texto": "RÍO"},
            {"texto": "ES"},
            {"texto": "VIDA"}
        ]
    },
    {
        "materia": "lenguaje",
        "nivel": 5,
        "nombre": "Secretos de la Selva",
        "personaje": "La Tunda",
        "frase_intro": "Observa con atención la imagen y responde a mis preguntas tocando la respuesta.",
        "minijuego": "point_and_click",
        "instruccion": "Toca la imagen que describe la palabra 'Canoa'",
        "audio_intro": "assets/audio/tunda_l5.ogg",
        "datos": {
            "items": [
                {"imagen": "assets/images/ui/bote_madera.png", "es_correcto": True, "nombre": "canoa"},
                {"imagen": "assets/images/ui/barco_metal.png", "es_correcto": False, "nombre": "barco"},
                {"imagen": "assets/images/ui/submarino.png", "es_correcto": False, "nombre": "submarino"}
            ]
        }
    },

    # ---------------------------------------------------------
    # INGLÉS - Personaje: El Duende
    # ---------------------------------------------------------
    {
        "materia": "ingles",
        "nivel": 1,
        "nombre": "Colors of the Jungle",
        "personaje": "El Duende",
        "frase_intro": "Hello my friend! Hoy vamos a aprender colores. Toca todos los objetos BLUE (Azules).",
        "minijuego": "point_and_click",
        "instruccion": "Toca los animales y objetos de color BLUE",
        "audio_intro": "assets/audio/duende_i1.ogg",
        "datos": {
            "items": [
                {"imagen": "assets/images/characters/pez_azul.png", "es_correcto": True, "nombre": "blue fish"},
                {"imagen": "assets/images/characters/mariposa_azul.png", "es_correcto": True, "nombre": "blue butterfly"},
                {"imagen": "assets/images/characters/rana_verde.png", "es_correcto": False, "nombre": "green frog"},
                {"imagen": "assets/images/characters/flor_roja.png", "es_correcto": False, "nombre": "red flower"}
            ]
        }
    },
    {
        "materia": "ingles",
        "nivel": 2,
        "nombre": "Animals Vocabulary",
        "personaje": "El Duende",
        "frase_intro": "¿Cómo se llaman nuestros animales en inglés? Únelos con su nombre correcto.",
        "minijuego": "drag_and_drop",
        "instruccion": "Arrastra la imagen del animal a su nombre en inglés",
        "audio_intro": "assets/audio/duende_i2.ogg",
        "datos": {
            "piezas": [
                {"imagen": "assets/images/characters/mono.png", "nombre": "mono", "zona_destino": "monkey"},
                {"imagen": "assets/images/characters/ballena.png", "nombre": "ballena", "zona_destino": "whale"},
                {"imagen": "assets/images/characters/pez.png", "nombre": "pez", "zona_destino": "fish"}
            ],
            "zonas": [
                {"id": "monkey", "etiqueta": "MONKEY", "posicion": (500, 150), "imagen": "assets/images/ui/cuadro_ingles.png"},
                {"id": "whale", "etiqueta": "WHALE", "posicion": (500, 300), "imagen": "assets/images/ui/cuadro_ingles.png"},
                {"id": "fish", "etiqueta": "FISH", "posicion": (500, 450), "imagen": "assets/images/ui/cuadro_ingles.png"}
            ]
        }
    },
    {
        "materia": "ingles",
        "nivel": 3,
        "nombre": "Counting in English",
        "personaje": "El Duende",
        "frase_intro": "One, two, three... ¡A contar! Toca los grupos que tienen THREE (3) animales.",
        "minijuego": "point_and_click",
        "instruccion": "Toca solo las hojas que tengan THREE (3) ranas",
        "audio_intro": "assets/audio/duende_i3.ogg",
        "datos": {
            "items": [
                {"imagen": "assets/images/ui/3ranas.png", "es_correcto": True, "nombre": "three frogs"},
                {"imagen": "assets/images/ui/3ranas_b.png", "es_correcto": True, "nombre": "three frogs"},
                {"imagen": "assets/images/ui/2ranas.png", "es_correcto": False, "nombre": "two frogs"},
                {"imagen": "assets/images/ui/4ranas.png", "es_correcto": False, "nombre": "four frogs"}
            ]
        }
    },
    {
        "materia": "ingles",
        "nivel": 4,
        "nombre": "A Friendly Greeting",
        "personaje": "El Duende",
        "frase_intro": "¿Cómo decimos 'Buenos días'? Ordena las palabras para formar el saludo.",
        "minijuego": "puzzle",
        "modo": "secuencia",
        "instruccion": "Ordena las palabras para decir BUENOS DÍAS en inglés",
        "audio_intro": "assets/audio/duende_i4.ogg",
        "datos": [
            {"texto": "GOOD"},
            {"texto": "MORNING"},
            {"texto": "FRIEND"}
        ]
    },
    {
        "materia": "ingles",
        "nivel": 5,
        "nombre": "The River Environment",
        "personaje": "El Duende",
        "frase_intro": "Let's find the RIVER! Observa el paisaje y toca lo que te pido en inglés.",
        "minijuego": "point_and_click",
        "instruccion": "Toca todos los elementos que sean un RIVER (Río)",
        "audio_intro": "assets/audio/duende_i5.ogg",
        "datos": {
            "items": [
                {"imagen": "assets/images/backgrounds/rio_1.png", "es_correcto": True, "nombre": "river"},
                {"imagen": "assets/images/backgrounds/rio_2.png", "es_correcto": True, "nombre": "river"},
                {"imagen": "assets/images/backgrounds/montana.png", "es_correcto": False, "nombre": "mountain"},
                {"imagen": "assets/images/backgrounds/cielo.png", "es_correcto": False, "nombre": "sky"}
            ]
        }
    },

    # ---------------------------------------------------------
    # BIOLOGÍA - Personaje: La Madre de Agua
    # ---------------------------------------------------------
    {
        "materia": "biologia",
        "nivel": 1,
        "nombre": "Flora y Fauna",
        "personaje": "La Madre de Agua",
        "frase_intro": "Soy la guardiana de la vida. Ayúdame a separar los animales de las plantas mágicas.",
        "minijuego": "drag_and_drop",
        "instruccion": "Arrastra los seres vivos a la zona de Animales o Plantas",
        "audio_intro": "assets/audio/madreagua_b1.ogg",
        "datos": {
            "piezas": [
                {"imagen": "assets/images/characters/pez.png", "nombre": "Pez", "zona_destino": "animales"},
                {"imagen": "assets/images/characters/rana.png", "nombre": "Rana", "zona_destino": "animales"},
                {"imagen": "assets/images/characters/hoja.png", "nombre": "Hoja", "zona_destino": "plantas"},
                {"imagen": "assets/images/characters/palma.png", "nombre": "Palma", "zona_destino": "plantas"}
            ],
            "zonas": [
                {"id": "animales", "etiqueta": "ANIMALES", "posicion": (500, 200), "imagen": "assets/images/ui/zona_animal.png"},
                {"id": "plantas", "etiqueta": "PLANTAS", "posicion": (500, 400), "imagen": "assets/images/ui/zona_planta.png"}
            ]
        }
    },
    {
        "materia": "biologia",
        "nivel": 2,
        "nombre": "Anatomía del Río",
        "personaje": "La Madre de Agua",
        "frase_intro": "A este hermoso tucán le faltan sus alas para volar. ¡Devuélvele su forma!",
        "minijuego": "puzzle",
        "modo": "completar",
        "instruccion": "Arrastra el ala del tucán a su lugar en el cuerpo",
        "audio_intro": "assets/audio/madreagua_b2.ogg",
        "datos": {
            "imagen_base": "assets/images/characters/tucan_sin_ala.png",
            "piezas": [
                {"imagen": "assets/images/characters/tucan_ala.png", "texto": "Ala", "posicion": (420, 280)}
            ]
        }
    },
    {
        "materia": "biologia",
        "nivel": 3,
        "nombre": "El Ecosistema Oculto",
        "personaje": "La Madre de Agua",
        "frase_intro": "El manglar está incompleto sin sus raíces en el agua. Arma la escena de la vida.",
        "minijuego": "puzzle",
        "modo": "completar",
        "instruccion": "Coloca las raíces del mangle en el agua salada",
        "audio_intro": "assets/audio/madreagua_b3.ogg",
        "datos": {
            "imagen_base": "assets/images/backgrounds/manglar_incompleto.png",
            "piezas": [
                {"imagen": "assets/images/backgrounds/raices_mangle.png", "texto": "Raíces", "posicion": (400, 450)}
            ]
        }
    },
    {
        "materia": "biologia",
        "nivel": 4,
        "nombre": "La Cadena de la Vida",
        "personaje": "La Madre de Agua",
        "frase_intro": "La energía fluye en el río. Ordena quién se alimenta de quién para mantener el equilibrio.",
        "minijuego": "puzzle",
        "modo": "secuencia",
        "instruccion": "Ordena la cadena: Sol -> Planta -> Insecto -> Rana",
        "audio_intro": "assets/audio/madreagua_b4.ogg",
        "datos": [
            {"imagen": "assets/images/characters/sol.png", "texto": "1. Sol"},
            {"imagen": "assets/images/characters/hoja.png", "texto": "2. Planta"},
            {"imagen": "assets/images/characters/insecto.png", "texto": "3. Insecto"},
            {"imagen": "assets/images/characters/rana.png", "texto": "4. Rana"}
        ]
    },
    {
        "materia": "biologia",
        "nivel": 5,
        "nombre": "Guardianes del Agua",
        "personaje": "La Madre de Agua",
        "frase_intro": "Nuestro deber es cuidar el Pacífico. Señala las acciones que protegen el agua limpia.",
        "minijuego": "point_and_click",
        "instruccion": "Toca las imágenes que representen CUIDAR el río",
        "audio_intro": "assets/audio/madreagua_b5.ogg",
        "datos": {
            "items": [
                {"imagen": "assets/images/ui/reciclar.png", "es_correcto": True, "nombre": "reciclar basura"},
                {"imagen": "assets/images/ui/sembrar_arbol.png", "es_correcto": True, "nombre": "sembrar árbol"},
                {"imagen": "assets/images/ui/basura_rio.png", "es_correcto": False, "nombre": "tirar basura"},
                {"imagen": "assets/images/ui/talar_arbol.png", "es_correcto": False, "nombre": "talar árboles"}
            ]
        }
    }
]

def obtener_datos_nivel_completo(materia, nivel):
    """
    Busca y retorna el diccionario completo del nivel solicitado.
    """
    for n in TODOS_LOS_NIVELES:
        if n["materia"] == materia and n["nivel"] == nivel:
            return n
    return None
