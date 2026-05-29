"""
reporte_fallback.py - Generador determinista de reportes docentes sin IA.

Funciona completamente offline a partir del diccionario de desempeño calculado
por database.py. No requiere Ollama ni ninguna conexión de red.
"""

NOMBRES_MATERIA = {
    'matematicas': 'Matemáticas',
    'lenguaje':    'Lenguaje',
    'ingles':      'Inglés',
    'biologia':    'Biología',
}

NOMBRES_TEMA = {
    'conteo':            'Conteo numérico',
    'suma':              'Suma',
    'resta':             'Resta',
    'multiplicacion':    'Multiplicación',
    'division':          'División',
    'vocales':           'Vocales',
    'silabas':           'Sílabas',
    'palabras':          'Formación de palabras',
    'oraciones':         'Construcción de oraciones',
    'vocabulario':       'Vocabulario',
    'colores':           'Colores en inglés',
    'animales':          'Animales en inglés',
    'numeros':           'Números en inglés',
    'saludos':           'Saludos en inglés',
    'vocabulario_ingles':'Vocabulario en inglés',
    'clasificacion':     'Clasificación de seres vivos',
    'anatomia':          'Anatomía animal',
    'ecosistema':        'Ecosistema',
    'cadena_alimenticia':'Cadena alimenticia',
    'conservacion':      'Conservación del medio ambiente',
}

RECOMENDACIONES_MATERIA = {
    'matematicas': [
        'Repasar con materiales concretos (piedras, semillas) para afianzar la numeración.',
        'Practicar operaciones básicas con ejercicios cortos y repetitivos de 5 minutos diarios.',
        'Usar canciones o rimas matemáticas para reforzar tablas y sumas.',
    ],
    'lenguaje': [
        'Leer en voz alta cuentos cortos del Pacífico para fortalecer la comprensión lectora.',
        'Trabajar silabeo con aplausos y juegos de palabras en el aula.',
        'Dictar palabras simples y pedir que las estudiantes las dibujen.',
    ],
    'ingles': [
        'Usar tarjetas de imágenes (flashcards) con vocabulario básico del entorno natural.',
        'Practicar saludos y colores con canciones sencillas en inglés.',
        'Repetir palabras en inglés vinculándolas con objetos del salón.',
    ],
    'biologia': [
        'Salidas cortas al entorno natural para identificar flora y fauna locales.',
        'Construir una cadena alimenticia con recortes o dibujos hechos por los estudiantes.',
        'Debatir en clase sobre acciones de conservación del río Pacífico.',
    ],
}

RECOMENDACIONES_GENERICAS = [
    'Destinar 10 minutos al inicio de la clase para repasar los temas con mayor dificultad.',
    'Formar parejas de trabajo donde el estudiante con mejor desempeño apoya al que tiene dificultades.',
    'Usar el minijuego nuevamente como práctica guiada en grupo antes de la evaluación individual.',
]


def _nivel_desempeno(promedio: float) -> str:
    if promedio >= 80:
        return 'ALTO'
    if promedio >= 60:
        return 'MEDIO'
    return 'BAJO ⚠'


def _nombre_materia(clave: str) -> str:
    return NOMBRES_MATERIA.get(clave, clave.capitalize())


def _nombre_tema(clave: str) -> str:
    return NOMBRES_TEMA.get(clave, clave.replace('_', ' ').capitalize())


def generar_reporte_fallback(desempeno: dict, ambito: str) -> str:
    """
    Genera un reporte pedagógico en texto plano a partir del dict de desempeño.

    Args:
        desempeno: Resultado de obtener_desempeno_estudiante() o obtener_desempeno_clase().
        ambito:    'estudiante' | 'clase'

    Returns:
        Texto del reporte listo para mostrar al docente.
    """
    lineas = []
    separador = '─' * 48

    # ── Encabezado ────────────────────────────────────────
    if ambito == 'clase':
        total = desempeno.get('total_estudiantes', 0)
        lineas.append('REPORTE DE DESEMPEÑO — CLASE COMPLETA')
        lineas.append(f'Estudiantes registrados: {total}')
    else:
        nombre = desempeno.get('nombre', 'Estudiante')
        lineas.append(f'REPORTE DE DESEMPEÑO — {nombre.upper()}')
    lineas.append(separador)

    por_materia = desempeno.get('por_materia', {})

    if not por_materia:
        lineas.append('')
        lineas.append('Aún no hay datos de desempeño registrados.')
        lineas.append('El estudiante debe completar al menos un nivel para generar el reporte.')
        lineas.append('')
        lineas.append('[Reporte generado en modo sin conexión]')
        return '\n'.join(lineas)

    # ── Desempeño por materia ──────────────────────────────
    lineas.append('')
    lineas.append('DESEMPEÑO POR MATERIA:')
    materias_ordenadas = sorted(
        por_materia.items(),
        key=lambda x: x[1].get('promedio_puntaje', 0)
    )
    for mat, datos in materias_ordenadas:
        prom   = datos.get('promedio_puntaje', 0)
        niv    = datos.get('niveles_completados', datos.get('estudiantes', 0))
        nivel_str = _nivel_desempeno(prom)
        lineas.append(f'  • {_nombre_materia(mat)}: {prom:.0f}/100 — {nivel_str} ({niv} nivel(es))')

    # ── Falencias por tema ─────────────────────────────────
    por_tema = desempeno.get('por_tema', {})
    temas_debiles = [
        (t, d) for t, d in por_tema.items()
        if d.get('promedio_puntaje', 100) < 60
    ]
    temas_debiles.sort(key=lambda x: x[1].get('promedio_puntaje', 100))

    if temas_debiles:
        lineas.append('')
        lineas.append('TEMAS CON MAYOR DIFICULTAD:')
        for tema, datos in temas_debiles[:6]:
            prom = datos.get('promedio_puntaje', 0)
            lineas.append(f'  ⚠ {_nombre_tema(tema)}: promedio {prom:.0f}/100')
    else:
        lineas.append('')
        lineas.append('No se detectaron temas con dificultad crítica (< 60/100).')

    # ── Fortalezas ────────────────────────────────────────
    materias_buenas = [
        (m, d) for m, d in por_materia.items()
        if d.get('promedio_puntaje', 0) >= 70
    ]
    if materias_buenas:
        lineas.append('')
        lineas.append('FORTALEZAS:')
        for mat, datos in sorted(materias_buenas, key=lambda x: -x[1].get('promedio_puntaje', 0)):
            prom = datos.get('promedio_puntaje', 0)
            lineas.append(f'  ✓ {_nombre_materia(mat)}: {prom:.0f}/100')

    # ── Recomendaciones ───────────────────────────────────
    lineas.append('')
    lineas.append('RECOMENDACIONES PEDAGÓGICAS:')

    # Recomendaciones específicas por materia débil
    recomendaciones_usadas = set()
    for mat, _ in materias_ordenadas[:2]:  # Las 2 materias más débiles
        for rec in RECOMENDACIONES_MATERIA.get(mat, [])[:2]:
            if rec not in recomendaciones_usadas:
                lineas.append(f'  • {rec}')
                recomendaciones_usadas.add(rec)

    # Recomendaciones genéricas de relleno
    for rec in RECOMENDACIONES_GENERICAS:
        if len(recomendaciones_usadas) >= 4:
            break
        if rec not in recomendaciones_usadas:
            lineas.append(f'  • {rec}')
            recomendaciones_usadas.add(rec)

    lineas.append('')
    lineas.append(separador)
    lineas.append('[Reporte generado en modo sin conexión — análisis automático]')

    return '\n'.join(lineas)
