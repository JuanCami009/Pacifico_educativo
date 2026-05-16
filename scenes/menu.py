"""
menu.py - Menú principal del juego Pacífico Educativo
Muestra el saludo al estudiante, 4 botones de materias con barra de progreso
y acceso a la pantalla de puntajes.
"""

import math
import pygame
from utils.database import contar_niveles_completados, obtener_puntajes_por_materia
from utils.audio_manager import gestor_audio

# ---------------------------------------------------------------------------
# Paleta de colores del litoral Pacífico colombiano
# ---------------------------------------------------------------------------
C_SELVA      = (45,  90,  39)    # #2D5A27  Verde selva
C_RIO        = (27,  79,  114)   # #1B4F72  Azul río
C_MADERA     = (139, 105, 20)    # #8B6914  Ocre madera
C_ORO        = (244, 208, 63)    # #F4D03F  Amarillo dorado
C_ARENA      = (210, 180, 120)
C_TEXTO      = (240, 235, 210)   # Crema sobre fondo oscuro
C_NEGRO_SUP  = (15,  20,  15)    # Negro verdoso para sombras
C_BARRA_BG   = (20,  40,  20)    # Fondo de barra de progreso
C_BARRA_OK   = (100, 200, 80)    # Progreso completado
C_OVERLAY    = (0,   0,   0,  170)  # Overlay modal

# Total de niveles por materia (para la barra de progreso)
TOTAL_NIVELES = 5

# ---------------------------------------------------------------------------
# Definición de materias
# ---------------------------------------------------------------------------
# Cada materia lleva: (etiqueta visible, clave BD, emoji, color_acento, color_hover)
MATERIAS = [
    {
        'nombre':    'Matematicas',
        'clave':     'matematicas',
        'emoji':     '🛶',          # Canoa
        'subtitulo': 'Numeros y operaciones',
        'color':     (50,  120, 80),
        'hover':     (70,  160, 110),
        'personaje': 'El Riviel',
    },
    {
        'nombre':    'Lenguaje',
        'clave':     'lenguaje',
        'emoji':     '🍃',          # Hoja
        'subtitulo': 'Lectura y escritura',
        'color':     (160, 85,  20),
        'hover':     (200, 115, 40),
        'personaje': 'La Tunda',
    },
    {
        'nombre':    'Ingles',
        'clave':     'ingles',
        'emoji':     '⭐',          # Estrella
        'subtitulo': 'Palabras y frases',
        'color':     (40,  90,  160),
        'hover':     (60,  120, 200),
        'personaje': 'El Duende',
    },
    {
        'nombre':    'Biologia',
        'clave':     'biologia',
        'emoji':     '🌿',          # Hoja tropical
        'subtitulo': 'Fauna y flora del Pacifico',
        'color':     (60,  130, 70),
        'hover':     (85,  170, 95),
        'personaje': 'La Madre de Agua',
    },
]


# ---------------------------------------------------------------------------
# Sub-pantalla: Ver mis puntajes
# ---------------------------------------------------------------------------

class PantallaScores:
    """
    Modal de puntajes superpuesto sobre el menú.
    Muestra tabla con materia, niveles completados y puntaje total.
    """

    def __init__(self, pantalla: pygame.Surface, ancho: int, alto: int,
                 estudiante: dict):
        self.pantalla   = pantalla
        self.ancho      = ancho
        self.alto       = alto
        self.estudiante = estudiante
        self.activo     = True          # False → cerrar modal

        self.fuente_tit  = pygame.font.SysFont('Arial', 30, bold=True)
        self.fuente_txt  = pygame.font.SysFont('Arial', 22)
        self.fuente_sub  = pygame.font.SysFont('Arial', 19)

        # Cargar datos de la base de datos
        self.datos = obtener_puntajes_por_materia(estudiante['id'])

        # Panel central
        pw, ph = 520, 380
        self.rect_panel = pygame.Rect(ancho // 2 - pw // 2, alto // 2 - ph // 2, pw, ph)

        # Botón cerrar
        bw, bh = 160, 44
        self.rect_cerrar = pygame.Rect(
            self.rect_panel.centerx - bw // 2,
            self.rect_panel.bottom - bh - 16,
            bw, bh
        )

    def manejar_eventos(self, eventos):
        for ev in eventos:
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if self.rect_cerrar.collidepoint(pygame.mouse.get_pos()):
                    self.activo = False
            elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                self.activo = False

    def dibujar(self):
        # Overlay oscuro
        overlay = pygame.Surface((self.ancho, self.alto), pygame.SRCALPHA)
        overlay.fill(C_OVERLAY)
        self.pantalla.blit(overlay, (0, 0))

        # Panel
        pygame.draw.rect(self.pantalla, (30, 55, 30), self.rect_panel, border_radius=20)
        pygame.draw.rect(self.pantalla, C_ORO, self.rect_panel, 3, border_radius=20)

        # Título
        cx = self.rect_panel.centerx
        tit = self.fuente_tit.render(
            f"Puntajes de {self.estudiante['nombre']}", True, C_ORO
        )
        self.pantalla.blit(tit, tit.get_rect(center=(cx, self.rect_panel.top + 32)))

        # Encabezados de tabla
        y_tabla = self.rect_panel.top + 72
        enc_cols = [("Materia", 0.25), ("Niveles", 0.58), ("Puntaje total", 0.82)]
        for texto, frac in enc_cols:
            x = self.rect_panel.left + int(self.rect_panel.width * frac)
            enc = self.fuente_sub.render(texto, True, C_ARENA)
            self.pantalla.blit(enc, (x, y_tabla))

        # Línea divisoria
        pygame.draw.line(
            self.pantalla, C_MADERA,
            (self.rect_panel.left + 16, y_tabla + 24),
            (self.rect_panel.right - 16, y_tabla + 24), 1
        )

        # Filas de datos
        nombres_display = {m['clave']: m['nombre'] for m in MATERIAS}
        y_fila = y_tabla + 38
        for materia in MATERIAS:
            clave = materia['clave']
            info = self.datos.get(clave, {'total': 0, 'niveles': 0})
            emoji = materia['emoji']

            x_mat  = self.rect_panel.left + int(self.rect_panel.width * 0.05)
            x_niv  = self.rect_panel.left + int(self.rect_panel.width * 0.55)
            x_pts  = self.rect_panel.left + int(self.rect_panel.width * 0.77)

            # Emoji + nombre
            nom_txt = self.fuente_txt.render(f"{emoji} {nombres_display[clave]}", True, C_TEXTO)
            self.pantalla.blit(nom_txt, (x_mat, y_fila))

            # Niveles completados como "N / TOTAL_NIVELES"
            niv_txt = self.fuente_txt.render(
                f"{info['niveles']} / {TOTAL_NIVELES}", True, C_TEXTO
            )
            self.pantalla.blit(niv_txt, (x_niv, y_fila))

            # Puntaje total
            pts_txt = self.fuente_txt.render(str(info['total']), True, C_ORO)
            self.pantalla.blit(pts_txt, (x_pts, y_fila))

            y_fila += 46

        # Botón cerrar
        hover = self.rect_cerrar.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(
            self.pantalla,
            C_MADERA if hover else (100, 75, 10),
            self.rect_cerrar, border_radius=12
        )
        pygame.draw.rect(self.pantalla, C_ORO, self.rect_cerrar, 2, border_radius=12)
        cerrar_txt = self.fuente_txt.render("Cerrar", True, C_TEXTO)
        self.pantalla.blit(cerrar_txt, cerrar_txt.get_rect(center=self.rect_cerrar.center))


# ---------------------------------------------------------------------------
# Pantalla principal del menú
# ---------------------------------------------------------------------------

class PantallaMenu:
    """
    Menú principal con 4 botones de materias, barra de progreso por materia,
    saludo al estudiante y botón de puntajes.
    """

    def __init__(self, pantalla: pygame.Surface, ancho: int, alto: int,
                 estudiante: dict):
        self.pantalla   = pantalla
        self.ancho      = ancho
        self.alto       = alto
        self.estudiante = estudiante

        # Estado de escena
        self.activo           = True
        self.escena_siguiente = None
        self.materia_seleccionada = None

        # Animación de fondo
        self.olas_offset = 0.0
        self.tiempo      = 0.0     # Tiempo acumulado para animaciones

        # Sub-pantalla de puntajes (None = cerrada)
        self.modal_scores: PantallaScores | None = None

        # Cargar fuentes
        self._cargar_fuentes()

        # Cargar progreso del estudiante por materia
        self._cargar_progreso()

        # Calcular posiciones
        self._calcular_layout()

        # Reproducir música de fondo si existe
        gestor_audio.reproducir_musica('menu.ogg')

    def _cargar_fuentes(self):
        """Carga todas las fuentes usadas en el menú."""
        self.f_saludo   = pygame.font.SysFont('Arial', 34, bold=True)
        self.f_subtit   = pygame.font.SysFont('Arial', 20)
        self.f_boton    = pygame.font.SysFont('Arial', 26, bold=True)
        self.f_sub_bot  = pygame.font.SysFont('Arial', 17)
        self.f_pequena  = pygame.font.SysFont('Arial', 18)
        self.f_emoji    = pygame.font.SysFont('Segoe UI Emoji', 32)

    def _cargar_progreso(self):
        """
        Consulta la base de datos para obtener los niveles completados
        de cada materia, usados para dibujar la barra de progreso.
        """
        eid = self.estudiante['id']
        self.progreso = {
            m['clave']: contar_niveles_completados(eid, m['clave'])
            for m in MATERIAS
        }

    def _calcular_layout(self):
        """
        Calcula los rectángulos de los 4 botones de materias (cuadrícula 2×2)
        y el botón de puntajes.
        """
        ancho_btn = 360
        alto_btn  = 108
        sep_x     = 22
        sep_y     = 18
        total_w   = 2 * ancho_btn + sep_x
        total_h   = 2 * alto_btn + sep_y
        inicio_x  = self.ancho // 2 - total_w // 2
        inicio_y  = self.alto // 2 - total_h // 2 + 28

        self.botones = []
        for i, materia in enumerate(MATERIAS):
            col = i % 2
            fila = i // 2
            x = inicio_x + col * (ancho_btn + sep_x)
            y = inicio_y + fila * (alto_btn + sep_y)
            rect = pygame.Rect(x, y, ancho_btn, alto_btn)
            self.botones.append({'rect': rect, 'materia': materia})

        # Botón pequeño "Ver mis puntajes" — esquina inferior derecha
        self.rect_scores = pygame.Rect(self.ancho - 196, self.alto - 50, 184, 36)

    # -----------------------------------------------------------------------
    # Ciclo de vida
    # -----------------------------------------------------------------------

    def manejar_eventos(self, eventos):
        """Distribuye eventos: primero al modal si está abierto, luego al menú."""
        if self.modal_scores and self.modal_scores.activo:
            self.modal_scores.manejar_eventos(eventos)
            if not self.modal_scores.activo:
                self.modal_scores = None
            return

        for ev in eventos:
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                raton = pygame.mouse.get_pos()

                # Botón de puntajes
                if self.rect_scores.collidepoint(raton):
                    self.modal_scores = PantallaScores(
                        self.pantalla, self.ancho, self.alto, self.estudiante
                    )
                    return

                # Botones de materias
                for btn in self.botones:
                    if btn['rect'].collidepoint(raton):
                        self.materia_seleccionada = btn['materia']['clave']
                        self.escena_siguiente = 'level_select'
                        self.activo = False
                        return

    def actualizar(self, dt: float):
        """Actualiza animaciones del fondo."""
        self.olas_offset = (self.olas_offset + 35 * dt) % self.ancho
        self.tiempo += dt

    def dibujar(self):
        """Renderiza el menú completo y, si está activo, el modal de puntajes."""
        self._dibujar_fondo()
        self._dibujar_olas()
        self._dibujar_cabecera()
        self._dibujar_botones()
        self._dibujar_boton_puntajes()

        if self.modal_scores and self.modal_scores.activo:
            self.modal_scores.dibujar()

    # -----------------------------------------------------------------------
    # Dibujo interno
    # -----------------------------------------------------------------------

    def _dibujar_fondo(self):
        """Fondo degradado vertical de selva → río."""
        for y in range(self.alto):
            t = y / self.alto
            r = int(C_SELVA[0] * (1 - t) + C_RIO[0] * t)
            g = int(C_SELVA[1] * (1 - t) + C_RIO[1] * t)
            b = int(C_SELVA[2] * (1 - t) + C_RIO[2] * t)
            pygame.draw.line(self.pantalla, (r, g, b), (0, y), (self.ancho, y))

    def _dibujar_olas(self):
        """Olas animadas en la franja inferior."""
        for i in range(3):
            amp   = 10 - i * 2
            fase  = self.olas_offset + i * 60
            y_base = self.alto - 62 + i * 20
            puntos = []
            for x in range(0, self.ancho + 10, 8):
                y = y_base + int(amp * math.sin((x + fase) * 0.022))
                puntos.append((x, y))
            puntos += [(self.ancho, self.alto), (0, self.alto)]
            tono = min(255, C_RIO[2] + 15 + i * 12)
            pygame.draw.polygon(self.pantalla, (C_RIO[0], C_RIO[1], tono), puntos)

    def _dibujar_cabecera(self):
        """Saludo personalizado y subtítulo animado con pulso."""
        cx = self.ancho // 2
        nombre = self.estudiante.get('nombre', 'Estudiante')

        # Saludo principal con sombra
        texto_saludo = f"Hola, {nombre}!"
        sombra = self.f_saludo.render(texto_saludo, True, C_NEGRO_SUP)
        self.pantalla.blit(sombra, sombra.get_rect(center=(cx + 2, 42)))
        saludo = self.f_saludo.render(texto_saludo, True, C_ORO)
        self.pantalla.blit(saludo, saludo.get_rect(center=(cx, 40)))

        # Subtítulo con pulso suave en opacidad
        alpha = int(180 + 60 * math.sin(self.tiempo * 2.0))
        sub = self.f_subtit.render("¿Que quieres aprender hoy?", True, C_ARENA)
        sub.set_alpha(alpha)
        self.pantalla.blit(sub, sub.get_rect(center=(cx, 72)))

    def _dibujar_botones(self):
        """Dibuja los 4 botones de materias con emoji, texto y barra de progreso."""
        raton = pygame.mouse.get_pos()

        for btn in self.botones:
            rect    = btn['rect']
            mat     = btn['materia']
            hover   = rect.collidepoint(raton)
            c_fondo = mat['hover'] if hover else mat['color']
            niveles_ok = self.progreso.get(mat['clave'], 0)

            # --- Sombra ---
            sombra = rect.move(5, 6)
            pygame.draw.rect(self.pantalla, C_NEGRO_SUP, sombra, border_radius=18)

            # --- Fondo del botón con ligero brillo en hover ---
            pygame.draw.rect(self.pantalla, c_fondo, rect, border_radius=18)

            # Franja superior más clara (efecto biselado)
            franja = pygame.Rect(rect.x + 4, rect.y + 4, rect.width - 8, 26)
            sup = pygame.Surface((franja.width, franja.height), pygame.SRCALPHA)
            sup.fill((255, 255, 255, 28))
            self.pantalla.blit(sup, franja.topleft)

            # Borde dorado
            pygame.draw.rect(self.pantalla, C_MADERA, rect, 2, border_radius=18)

            # --- Emoji (columna izquierda) ---
            emoji_surf = self.f_emoji.render(mat['emoji'], True, C_TEXTO)
            self.pantalla.blit(
                emoji_surf,
                (rect.left + 18, rect.centery - emoji_surf.get_height() // 2 - 8)
            )

            # --- Nombre de la materia ---
            nom = self.f_boton.render(mat['nombre'], True, C_TEXTO)
            self.pantalla.blit(nom, (rect.left + 68, rect.top + 18))

            # --- Subtítulo pequeño ---
            sub = self.f_sub_bot.render(mat['subtitulo'], True, C_ARENA)
            self.pantalla.blit(sub, (rect.left + 68, rect.top + 48))

            # --- Barra de progreso (0 a TOTAL_NIVELES) ---
            self._dibujar_barra_progreso(rect, niveles_ok)

            # --- Personaje guía en esquina inferior derecha ---
            per = self.f_sub_bot.render(mat['personaje'], True, C_ORO)
            self.pantalla.blit(per, per.get_rect(
                bottomright=(rect.right - 12, rect.bottom - 8)
            ))

    def _dibujar_barra_progreso(self, rect_boton: pygame.Rect, completados: int):
        """
        Dibuja una barra de progreso dentro del botón de materia.

        Args:
            rect_boton:  Rectángulo del botón contenedor.
            completados: Número de niveles completados (0 a TOTAL_NIVELES).
        """
        barra_w = rect_boton.width - 78   # Dejar espacio para emoji
        barra_h = 10
        barra_x = rect_boton.left + 68
        barra_y = rect_boton.bottom - 22

        # Fondo de la barra
        rect_bg = pygame.Rect(barra_x, barra_y, barra_w, barra_h)
        pygame.draw.rect(self.pantalla, C_BARRA_BG, rect_bg, border_radius=5)

        # Progreso relleno
        fraccion = min(1.0, completados / TOTAL_NIVELES)
        if fraccion > 0:
            ancho_ok = max(8, int(barra_w * fraccion))
            rect_ok = pygame.Rect(barra_x, barra_y, ancho_ok, barra_h)
            pygame.draw.rect(self.pantalla, C_BARRA_OK, rect_ok, border_radius=5)

        # Texto de niveles (ej. "3 / 5")
        txt_prog = self.f_sub_bot.render(
            f"{completados} / {TOTAL_NIVELES}", True, C_ARENA
        )
        self.pantalla.blit(txt_prog, (barra_x, barra_y - 16))

    def _dibujar_boton_puntajes(self):
        """Botón pequeño en la esquina inferior derecha para ver puntajes."""
        hover = self.rect_scores.collidepoint(pygame.mouse.get_pos())
        color = C_MADERA if hover else (90, 65, 8)
        pygame.draw.rect(self.pantalla, color, self.rect_scores, border_radius=10)
        pygame.draw.rect(self.pantalla, C_ORO, self.rect_scores, 2, border_radius=10)
        txt = self.f_pequena.render("Ver mis puntajes", True, C_TEXTO)
        self.pantalla.blit(txt, txt.get_rect(center=self.rect_scores.center))
