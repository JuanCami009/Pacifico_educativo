"""
level_select.py - Selección de nivel del juego Pacífico Educativo
Muestra 5 niveles con nombres temáticos del Pacífico, respeta el progreso del
estudiante y presenta al personaje guía antes de iniciar el minijuego.
"""

import math
import pygame
from utils.database import obtener_nivel_maximo, obtener_mejor_puntaje

# ---------------------------------------------------------------------------
# Colores
# ---------------------------------------------------------------------------
C_SELVA     = (45,  90,  39)
C_RIO       = (27,  79,  114)
C_MADERA    = (139, 105, 20)
C_ORO       = (244, 208, 63)
C_ARENA     = (210, 180, 120)
C_TEXTO     = (240, 235, 210)
C_NEGRO     = (10,  15,  10)

C_NIVEL_OK   = (60,  170, 80)   # Verde: nivel desbloqueado sin completar
C_NIVEL_DONE = (200, 165, 30)   # Dorado: nivel ya completado
C_NIVEL_BLOQ = (55,  55,  55)   # Gris: bloqueado
C_NIVEL_NEXT = (80,  200, 220)  # Cian: próximo disponible (resaltado)

C_OVERLAY = (0, 0, 0, 175)

# ---------------------------------------------------------------------------
# Número de niveles por materia
# ---------------------------------------------------------------------------
TOTAL_NIVELES = 5

# ---------------------------------------------------------------------------
# Nombres temáticos de cada nivel (aplica a todas las materias)
# ---------------------------------------------------------------------------
NOMBRES_NIVEL = [
    "La Orilla del Rio",
    "El Manglar Sagrado",
    "La Selva Oscura",
    "El Corazon del Pacifico",
    "El Guardabosques",
]

# ---------------------------------------------------------------------------
# Datos de personajes guía por materia
# ---------------------------------------------------------------------------
PERSONAJES = {
    'matematicas': {
        'nombre':  'El Riviel',
        'emoji':   '🕯',
        'frase':   ('El Riviel te guia entre los numeros\n'
                    'como su luz guia a los navegantes\n'
                    'por el oscuro rio Pacifico.'),
        'color':   (80,  140, 200),   # Azul espectral
    },
    'lenguaje': {
        'nombre':  'La Tunda',
        'emoji':   '🌿',
        'frase':   ('La Tunda conoce todos los secretos\n'
                    'del bosque... y las palabras que\n'
                    'lo habitan. ¡Aprende con ella!'),
        'color':   (80,  140, 60),    # Verde selva
    },
    'ingles': {
        'nombre':  'El Duende',
        'emoji':   '🎩',
        'frase':   ('El Duende viaja entre mundos\n'
                    'y habla muchas lenguas.\n'
                    '¡Hoy te ensenara el ingles!'),
        'color':   (180, 90,  200),   # Morado misterioso
    },
    'biologia': {
        'nombre':  'La Madre de Agua',
        'emoji':   '💧',
        'frase':   ('La Madre de Agua cuida cada ser\n'
                    'vivo del Pacifico. Acompanala\n'
                    'y conoce la vida del litoral.'),
        'color':   (40,  160, 200),   # Azul agua serena
    },
}

# Personaje por defecto si la clave no existe
PERSONAJE_DEFAULT = {
    'nombre': 'El Guia',
    'emoji':  '🌟',
    'frase':  'Tu guia te espera. ¡Adelante!',
    'color':  C_ORO,
}


# ---------------------------------------------------------------------------
# Sub-pantalla: presentación del personaje antes de jugar
# ---------------------------------------------------------------------------

class PantallaPersonaje:
    """
    Modal con el personaje guía de la materia, su frase y el botón ¡Jugar!
    Se muestra al hacer clic en un nivel disponible.
    """

    def __init__(self, pantalla: pygame.Surface, ancho: int, alto: int,
                 materia: str, nivel: int, nombre_nivel: str):
        self.pantalla    = pantalla
        self.ancho       = ancho
        self.alto        = alto
        self.nivel       = nivel
        self.nombre_nivel = nombre_nivel
        self.confirmar   = False   # True → el usuario pulsó ¡Jugar!
        self.cancelar    = False   # True → cerró el modal sin jugar
        self.tiempo      = 0.0

        self.personaje = PERSONAJES.get(materia, PERSONAJE_DEFAULT)

        self.f_titulo  = pygame.font.SysFont('Arial', 28, bold=True)
        self.f_texto   = pygame.font.SysFont('Arial', 21)
        self.f_sub     = pygame.font.SysFont('Arial', 18)
        self.f_emoji   = pygame.font.SysFont('Segoe UI Emoji', 72)

        # Panel central
        pw, ph = 460, 360
        self.rect_panel = pygame.Rect(ancho // 2 - pw // 2, alto // 2 - ph // 2, pw, ph)

        # Botón Jugar
        bw, bh = 180, 50
        self.rect_jugar = pygame.Rect(
            self.rect_panel.centerx - bw // 2,
            self.rect_panel.bottom - bh - 18,
            bw, bh
        )

        # Botón Volver (X esquina superior derecha del panel)
        self.rect_volver = pygame.Rect(
            self.rect_panel.right - 38, self.rect_panel.top + 8, 30, 30
        )

    def manejar_eventos(self, eventos):
        for ev in eventos:
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                raton = pygame.mouse.get_pos()
                if self.rect_jugar.collidepoint(raton):
                    self.confirmar = True
                elif self.rect_volver.collidepoint(raton):
                    self.cancelar = True
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_RETURN:
                    self.confirmar = True
                elif ev.key == pygame.K_ESCAPE:
                    self.cancelar = True

    def actualizar(self, dt: float):
        self.tiempo += dt

    def dibujar(self):
        # Overlay oscuro sobre el fondo
        overlay = pygame.Surface((self.ancho, self.alto), pygame.SRCALPHA)
        overlay.fill(C_OVERLAY)
        self.pantalla.blit(overlay, (0, 0))

        per = self.personaje
        cx  = self.rect_panel.centerx

        # Panel con color del personaje
        c_panel = tuple(max(0, c - 60) for c in per['color'])
        pygame.draw.rect(self.pantalla, c_panel, self.rect_panel, border_radius=22)
        pygame.draw.rect(self.pantalla, per['color'], self.rect_panel, 3, border_radius=22)

        # Botón cerrar "✕"
        hover_v = self.rect_volver.collidepoint(pygame.mouse.get_pos())
        pygame.draw.circle(
            self.pantalla,
            (180, 50, 50) if hover_v else (100, 30, 30),
            self.rect_volver.center, 15
        )
        x_txt = self.f_sub.render("X", True, C_TEXTO)
        self.pantalla.blit(x_txt, x_txt.get_rect(center=self.rect_volver.center))

        # Emoji del personaje con pulso de escala (simulado con alpha)
        pulso_alpha = int(200 + 55 * math.sin(self.tiempo * 3.0))
        emoji_surf = self.f_emoji.render(per['emoji'], True, per['color'])
        emoji_surf.set_alpha(pulso_alpha)
        self.pantalla.blit(emoji_surf, emoji_surf.get_rect(
            center=(cx, self.rect_panel.top + 72)
        ))

        # Nombre del personaje
        nom = self.f_titulo.render(per['nombre'], True, per['color'])
        self.pantalla.blit(nom, nom.get_rect(center=(cx, self.rect_panel.top + 130)))

        # Nombre del nivel
        niv_txt = self.f_sub.render(
            f"Nivel {self.nivel}: {self.nombre_nivel}", True, C_ARENA
        )
        self.pantalla.blit(niv_txt, niv_txt.get_rect(center=(cx, self.rect_panel.top + 158)))

        # Frase (puede tener saltos de línea)
        lineas = per['frase'].split('\n')
        y_frase = self.rect_panel.top + 186
        for linea in lineas:
            surf = self.f_texto.render(linea.strip(), True, C_TEXTO)
            self.pantalla.blit(surf, surf.get_rect(center=(cx, y_frase)))
            y_frase += 26

        # Botón ¡Jugar!
        hover_j = self.rect_jugar.collidepoint(pygame.mouse.get_pos())
        c_boton = per['color'] if hover_j else tuple(max(0, c - 40) for c in per['color'])
        pygame.draw.rect(self.pantalla, C_NEGRO, self.rect_jugar.move(3, 4), border_radius=14)
        pygame.draw.rect(self.pantalla, c_boton, self.rect_jugar, border_radius=14)
        pygame.draw.rect(self.pantalla, C_ORO, self.rect_jugar, 2, border_radius=14)
        jugar_txt = self.f_titulo.render("¡Jugar!", True, C_TEXTO)
        self.pantalla.blit(jugar_txt, jugar_txt.get_rect(center=self.rect_jugar.center))


# ---------------------------------------------------------------------------
# Pantalla principal de selección de nivel
# ---------------------------------------------------------------------------

class PantallaLevelSelect:
    """
    Muestra 5 círculos representando los niveles.
    - Bloqueados: gris oscuro con candado
    - Completados: dorado con estrella
    - Próximo disponible: cian resaltado con pulso
    - Desbloqueados sin completar: verde

    Al hacer clic en un nivel disponible abre PantallaPersonaje.
    Retorna nivel_seleccionado para que main.py lo pase al minijuego.
    """

    def __init__(self, pantalla: pygame.Surface, ancho: int, alto: int,
                 estudiante: dict, materia: str):
        self.pantalla   = pantalla
        self.ancho      = ancho
        self.alto       = alto
        self.estudiante = estudiante
        self.materia    = materia

        # Estado de la escena
        self.activo            = True
        self.escena_siguiente  = None
        self.nivel_seleccionado = None

        # Nivel más alto desbloqueado (consulta BD)
        self.nivel_maximo = obtener_nivel_maximo(estudiante['id'], materia)

        # Animación
        self.olas_offset = 0.0
        self.tiempo      = 0.0

        # Modal de personaje (None = cerrado)
        self.modal_personaje: PantallaPersonaje | None = None

        # Personaje de la materia para el encabezado
        self.personaje = PERSONAJES.get(materia, PERSONAJE_DEFAULT)

        self._cargar_fuentes()
        self._calcular_circulos()

    def _cargar_fuentes(self):
        self.f_titulo   = pygame.font.SysFont('Arial', 36, bold=True)
        self.f_nivel    = pygame.font.SysFont('Arial', 22, bold=True)
        self.f_nombre   = pygame.font.SysFont('Arial', 15)
        self.f_pequena  = pygame.font.SysFont('Arial', 18)
        self.f_emoji    = pygame.font.SysFont('Segoe UI Emoji', 26)

    def _calcular_circulos(self):
        """
        Coloca 5 círculos en línea horizontal centrada.
        Cada círculo lleva: rect_centro, nivel, estado y puntaje.
        """
        radio      = 52
        separacion = 38        # Espacio entre bordes de círculos
        paso       = radio * 2 + separacion
        total_w    = TOTAL_NIVELES * paso - separacion
        cx_inicio  = self.ancho // 2 - total_w // 2 + radio
        cy         = self.alto // 2 + 30

        self.circulos = []
        for i in range(TOTAL_NIVELES):
            nivel         = i + 1
            cx            = cx_inicio + i * paso
            desbloqueado  = nivel <= self.nivel_maximo
            puntaje       = (obtener_mejor_puntaje(self.estudiante['id'], self.materia, nivel)
                             if desbloqueado else 0)
            es_siguiente  = (nivel == self.nivel_maximo) and (puntaje == 0)

            self.circulos.append({
                'centro':       (cx, cy),
                'radio':        radio,
                'nivel':        nivel,
                'desbloqueado': desbloqueado,
                'puntaje':      puntaje,
                'siguiente':    es_siguiente,
                'nombre':       NOMBRES_NIVEL[i],
            })

    # -----------------------------------------------------------------------
    # Ciclo de vida
    # -----------------------------------------------------------------------

    def manejar_eventos(self, eventos):
        """Distribuye eventos al modal si está activo, o al propio selector."""
        if self.modal_personaje:
            self.modal_personaje.manejar_eventos(eventos)

            if self.modal_personaje.confirmar:
                # El usuario pulsó ¡Jugar! → pasar al minijuego
                self.nivel_seleccionado = self.modal_personaje.nivel
                self.escena_siguiente   = 'minijuego'
                self.activo             = False
                self.modal_personaje    = None

            elif self.modal_personaje.cancelar:
                self.modal_personaje = None
            return

        for ev in eventos:
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                raton = pygame.mouse.get_pos()
                for circulo in self.circulos:
                    if (circulo['desbloqueado'] and
                            self._en_circulo(raton, circulo)):
                        # Abrir modal del personaje
                        self.modal_personaje = PantallaPersonaje(
                            self.pantalla, self.ancho, self.alto,
                            self.materia, circulo['nivel'], circulo['nombre']
                        )
                        return

            elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                self.escena_siguiente = 'menu'
                self.activo = False

    def _en_circulo(self, punto: tuple, circulo: dict) -> bool:
        """Comprueba si un punto está dentro del círculo de nivel."""
        cx, cy = circulo['centro']
        px, py = punto
        return math.hypot(px - cx, py - cy) <= circulo['radio']

    def actualizar(self, dt: float):
        self.olas_offset = (self.olas_offset + 35 * dt) % self.ancho
        self.tiempo += dt
        if self.modal_personaje:
            self.modal_personaje.actualizar(dt)

    def dibujar(self):
        self._dibujar_fondo()
        self._dibujar_olas()
        self._dibujar_cabecera()
        self._dibujar_circulos()
        self._dibujar_leyenda()
        self._dibujar_pie()

        if self.modal_personaje:
            self.modal_personaje.dibujar()

    # -----------------------------------------------------------------------
    # Dibujo interno
    # -----------------------------------------------------------------------

    def _dibujar_fondo(self):
        """Fondo degradado selva → río, con tinte del color del personaje."""
        per_color = self.personaje['color']
        for y in range(self.alto):
            t = y / self.alto
            r = int(C_SELVA[0] * (1 - t) + per_color[0] * t * 0.35 + C_RIO[0] * t * 0.65)
            g = int(C_SELVA[1] * (1 - t) + per_color[1] * t * 0.35 + C_RIO[1] * t * 0.65)
            b = int(C_SELVA[2] * (1 - t) + per_color[2] * t * 0.35 + C_RIO[2] * t * 0.65)
            pygame.draw.line(self.pantalla, (
                max(0, min(255, r)),
                max(0, min(255, g)),
                max(0, min(255, b))
            ), (0, y), (self.ancho, y))

    def _dibujar_olas(self):
        for i in range(2):
            amp   = 9 - i * 3
            fase  = self.olas_offset + i * 65
            y_base = self.alto - 58 + i * 22
            puntos = []
            for x in range(0, self.ancho + 10, 8):
                y = y_base + int(amp * math.sin((x + fase) * 0.022))
                puntos.append((x, y))
            puntos += [(self.ancho, self.alto), (0, self.alto)]
            tono = min(255, C_RIO[2] + 15 + i * 12)
            pygame.draw.polygon(self.pantalla, (C_RIO[0], C_RIO[1], tono), puntos)

    def _dibujar_cabecera(self):
        """Encabezado con nombre de la materia y emoji del personaje."""
        cx  = self.ancho // 2
        per = self.personaje
        mat = self.materia.capitalize()

        # Emoji pulsante
        pulso = int(210 + 45 * math.sin(self.tiempo * 2.5))
        emoji_s = self.f_emoji.render(per['emoji'], True, per['color'])
        emoji_s.set_alpha(pulso)
        self.pantalla.blit(emoji_s, emoji_s.get_rect(
            center=(cx - self._ancho_texto(mat) // 2 - 28, 50)
        ))

        # Título de la materia con sombra
        sombra = self.f_titulo.render(f"Niveles de {mat}", True, C_NEGRO)
        self.pantalla.blit(sombra, sombra.get_rect(center=(cx + 2, 52)))
        tit = self.f_titulo.render(f"Niveles de {mat}", True, C_TEXTO)
        self.pantalla.blit(tit, tit.get_rect(center=(cx, 50)))

        # Guía: "Tu guía: [nombre personaje]"
        guia = self.f_pequena.render(f"Tu guia: {per['nombre']}", True, per['color'])
        self.pantalla.blit(guia, guia.get_rect(center=(cx, 82)))

    def _ancho_texto(self, texto: str) -> int:
        """Devuelve el ancho en píxeles del texto con la fuente de título."""
        return self.f_titulo.size(texto)[0]

    def _dibujar_circulos(self):
        """Dibuja los 5 círculos de niveles con su estado visual."""
        raton = pygame.mouse.get_pos()

        for circ in self.circulos:
            cx, cy = circ['centro']
            r      = circ['radio']
            desbl  = circ['desbloqueado']
            puntaje = circ['puntaje']
            sig     = circ['siguiente']
            hover   = desbl and self._en_circulo(raton, circ)

            # --- Elegir color según estado ---
            if not desbl:
                color_circulo = C_NIVEL_BLOQ
            elif puntaje > 0:
                color_circulo = C_NIVEL_DONE
            elif sig:
                # Pulso animado para el próximo nivel
                pulso = int(30 * math.sin(self.tiempo * 4.0))
                color_circulo = (
                    min(255, C_NIVEL_NEXT[0] + pulso),
                    min(255, C_NIVEL_NEXT[1] + pulso),
                    min(255, C_NIVEL_NEXT[2] - pulso),
                )
            else:
                color_circulo = C_NIVEL_OK

            if hover:
                color_circulo = tuple(min(255, c + 35) for c in color_circulo)

            # --- Sombra del círculo ---
            pygame.draw.circle(self.pantalla, C_NEGRO, (cx + 4, cy + 5), r)

            # --- Círculo principal ---
            pygame.draw.circle(self.pantalla, color_circulo, (cx, cy), r)

            # --- Anillo exterior ---
            grosor_anillo = 3 if not sig else 5
            color_anillo  = C_ORO if puntaje > 0 else C_MADERA
            if sig:
                color_anillo = C_NIVEL_NEXT
            pygame.draw.circle(self.pantalla, color_anillo, (cx, cy), r, grosor_anillo)

            # --- Contenido interior ---
            if not desbl:
                # Candado (texto "🔒" o símbolo)
                txt = self.f_nivel.render("🔒", True, (140, 140, 140))
                self.pantalla.blit(txt, txt.get_rect(center=(cx, cy - 5)))
            elif puntaje > 0:
                # Número + estrella
                num = self.f_nivel.render(str(circ['nivel']), True, C_TEXTO)
                self.pantalla.blit(num, num.get_rect(center=(cx, cy - 10)))
                star = self.f_nombre.render("★ Completado", True, C_ORO)
                self.pantalla.blit(star, star.get_rect(center=(cx, cy + 14)))
            else:
                # Solo número
                num = self.f_nivel.render(str(circ['nivel']), True, C_TEXTO)
                self.pantalla.blit(num, num.get_rect(center=(cx, cy)))

            # --- Nombre temático debajo del círculo ---
            nom_sup = self.f_nombre.render(circ['nombre'], True, C_ARENA if desbl else (90, 90, 90))
            self.pantalla.blit(nom_sup, nom_sup.get_rect(center=(cx, cy + r + 16)))

            # --- Puntaje debajo del nombre si completado ---
            if puntaje > 0:
                pts = self.f_nombre.render(f"{puntaje} pts", True, C_ORO)
                self.pantalla.blit(pts, pts.get_rect(center=(cx, cy + r + 32)))

        # Conectar círculos con una línea de "camino"
        self._dibujar_camino()

    def _dibujar_camino(self):
        """Dibuja una línea que conecta los centros de los círculos."""
        if len(self.circulos) < 2:
            return
        puntos = [c['centro'] for c in self.circulos]
        for i in range(len(puntos) - 1):
            desbloqueado_par = (self.circulos[i]['desbloqueado'] and
                                self.circulos[i + 1]['desbloqueado'])
            color_camino = C_MADERA if desbloqueado_par else (50, 50, 50)
            pygame.draw.line(self.pantalla, color_camino,
                             puntos[i], puntos[i + 1], 4)

    def _dibujar_leyenda(self):
        """Leyenda de colores en la parte inferior del área de juego."""
        items = [
            (C_NIVEL_NEXT, "Disponible"),
            (C_NIVEL_DONE, "Completado"),
            (C_NIVEL_BLOQ, "Bloqueado"),
        ]
        x = 30
        y = self.alto - 95
        for color, texto in items:
            pygame.draw.circle(self.pantalla, color, (x + 8, y + 8), 8)
            txt = self.f_nombre.render(texto, True, C_ARENA)
            self.pantalla.blit(txt, (x + 22, y))
            x += txt.get_width() + 50

    def _dibujar_pie(self):
        """Instrucciones de navegación en la base de la pantalla."""
        pie = self.f_pequena.render(
            "Clic en un nivel disponible para jugar  |  ESC para volver al menu",
            True, C_ARENA
        )
        self.pantalla.blit(pie, pie.get_rect(center=(self.ancho // 2, self.alto - 28)))
