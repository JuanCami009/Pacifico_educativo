"""
intro.py - Pantalla de inicio del juego Pacífico Educativo
Muestra el campo de nombre del niño y gestiona la creación/carga de perfil
"""

import math
import pygame
from utils.database import obtener_o_crear_estudiante, buscar_estudiante

# ---------------------------------------------------------------------------
# Paleta de colores del litoral Pacífico colombiano
# ---------------------------------------------------------------------------
COLOR_SELVA      = (45, 90, 39)      # Verde selva #2D5A27
COLOR_RIO        = (27, 79, 114)     # Azul río #1B4F72
COLOR_MADERA     = (139, 105, 20)    # Ocre madera #8B6914
COLOR_ARENA      = (210, 180, 120)   # Arena de playa
COLOR_TEXTO      = (240, 235, 210)   # Crema para texto sobre fondo oscuro
COLOR_BOTON      = (180, 130, 20)    # Dorado madera para botones
COLOR_BOTON_HOV  = (210, 160, 40)    # Hover del botón
COLOR_INPUT_BG   = (255, 252, 235)   # Fondo claro del campo de texto
COLOR_INPUT_ORD  = (139, 105, 20)    # Borde normal del campo
COLOR_INPUT_ACT  = (27, 79, 114)     # Borde activo del campo
COLOR_OK         = (100, 180, 80)    # Verde para mensajes de éxito
COLOR_ERROR      = (180, 50, 50)     # Rojo para mensajes de error


class PantallaIntro:
    """
    Pantalla de bienvenida donde el niño ingresa su nombre.
    Gestiona el flujo de login/creación de perfil con SQLite.
    """

    def __init__(self, pantalla: pygame.Surface, ancho: int, alto: int):
        self.pantalla = pantalla
        self.ancho = ancho
        self.alto = alto

        # Estado de la escena
        self.activo = True
        self.escena_siguiente = None
        self.estudiante = None

        # Estado del campo de texto
        self.nombre_ingresado = ""
        self.campo_activo = False
        self.cursor_visible = True
        self.timer_cursor = 0.0

        # Mensaje de estado
        self.mensaje = ""
        self.color_mensaje = COLOR_ERROR

        # Animación de fondo
        self.olas_offset = 0.0

        self._cargar_fuentes()
        self._calcular_layout()

    def _cargar_fuentes(self):
        """Carga fuentes del sistema como respaldo robusto."""
        self.fuente_titulo    = pygame.font.SysFont('Arial', 52, bold=True)
        self.fuente_texto     = pygame.font.SysFont('Arial', 32)
        self.fuente_pequena   = pygame.font.SysFont('Arial', 24)

    def _calcular_layout(self):
        """Calcula las posiciones de los elementos de la UI."""
        cx = self.ancho // 2
        # Panel central
        pw, ph = 520, 300
        self.rect_panel = pygame.Rect(cx - pw // 2, self.alto // 2 - ph // 2 + 40, pw, ph)
        # Campo de texto
        cw, ch = 380, 54
        self.rect_campo = pygame.Rect(cx - cw // 2, self.rect_panel.top + 115, cw, ch)
        # Botón Entrar
        bw, bh = 220, 58
        self.rect_boton = pygame.Rect(cx - bw // 2, self.rect_campo.bottom + 28, bw, bh)
        # Posición del mensaje de estado
        self.pos_mensaje = (cx, self.rect_boton.bottom + 24)

    # -----------------------------------------------------------------------
    # Lógica
    # -----------------------------------------------------------------------

    def manejar_eventos(self, eventos):
        """Procesa eventos de pygame para esta pantalla."""
        for evento in eventos:
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                raton = pygame.mouse.get_pos()
                self.campo_activo = self.rect_campo.collidepoint(raton)
                if self.rect_boton.collidepoint(raton):
                    self._intentar_entrar()

            elif evento.type == pygame.KEYDOWN and self.campo_activo:
                if evento.key == pygame.K_RETURN:
                    self._intentar_entrar()
                elif evento.key == pygame.K_BACKSPACE:
                    self.nombre_ingresado = self.nombre_ingresado[:-1]
                    self.mensaje = ""
                else:
                    if len(self.nombre_ingresado) < 20 and evento.unicode.isprintable():
                        self.nombre_ingresado += evento.unicode
                        self.mensaje = ""

            elif evento.type == pygame.USEREVENT + 1:
                # Temporizador para cambio de escena
                self.escena_siguiente = 'menu'
                self.activo = False

    def _intentar_entrar(self):
        """Valida el nombre e intenta autenticar o crear el perfil del estudiante."""
        nombre = self.nombre_ingresado.strip()
        if len(nombre) < 2:
            self.mensaje = "¡Escribe tu nombre (mínimo 2 letras)!"
            self.color_mensaje = COLOR_ERROR
            return
        if len(nombre) > 20:
            self.mensaje = "El nombre es muy largo (máximo 20 letras)."
            self.color_mensaje = COLOR_ERROR
            return

        existente = buscar_estudiante(nombre)
        self.estudiante = obtener_o_crear_estudiante(nombre)

        if existente:
            self.mensaje = f"¡Bienvenido de nuevo, {self.estudiante['nombre']}!"
        else:
            self.mensaje = f"¡Hola {self.estudiante['nombre']}! Tu perfil fue creado."
        self.color_mensaje = COLOR_OK

        # Cambiar de escena después de 1.5 segundos
        pygame.time.set_timer(pygame.USEREVENT + 1, 1500)

    def actualizar(self, dt: float):
        """Actualiza la lógica de animación."""
        self.olas_offset = (self.olas_offset + 40 * dt) % self.ancho
        self.timer_cursor += dt
        if self.timer_cursor >= 0.5:
            self.timer_cursor = 0.0
            self.cursor_visible = not self.cursor_visible

    # -----------------------------------------------------------------------
    # Dibujo
    # -----------------------------------------------------------------------

    def dibujar(self):
        """Renderiza todos los elementos visuales."""
        self._dibujar_fondo()
        self._dibujar_olas()
        self._dibujar_titulo()
        self._dibujar_panel()
        self._dibujar_campo()
        self._dibujar_boton()
        if self.mensaje:
            self._dibujar_mensaje()

    def _dibujar_fondo(self):
        """Fondo con degradado vertical selva → río."""
        for y in range(self.alto):
            t = y / self.alto
            r = int(COLOR_SELVA[0] * (1 - t) + COLOR_RIO[0] * t)
            g = int(COLOR_SELVA[1] * (1 - t) + COLOR_RIO[1] * t)
            b = int(COLOR_SELVA[2] * (1 - t) + COLOR_RIO[2] * t)
            pygame.draw.line(self.pantalla, (r, g, b), (0, y), (self.ancho, y))

    def _dibujar_olas(self):
        """Olas decorativas animadas en la parte inferior."""
        for i in range(3):
            amp = 12 - i * 3
            fase = self.olas_offset + i * 60
            y_base = self.alto - 65 + i * 20
            puntos = []
            for x in range(0, self.ancho + 10, 10):
                y = y_base + int(amp * math.sin((x + fase) * 0.025))
                puntos.append((x, y))
            puntos += [(self.ancho, self.alto), (0, self.alto)]
            tono = min(255, COLOR_RIO[2] + 20 + i * 15)
            pygame.draw.polygon(self.pantalla, (COLOR_RIO[0], COLOR_RIO[1], tono), puntos)

    def _dibujar_titulo(self):
        """Dibuja el título y subtítulo del juego."""
        cx = self.ancho // 2
        # Sombra
        som = self.fuente_titulo.render("Pacifico Educativo", True, (0, 0, 0))
        self.pantalla.blit(som, som.get_rect(center=(cx + 2, 82)))
        # Título
        tit = self.fuente_titulo.render("Pacifico Educativo", True, COLOR_TEXTO)
        self.pantalla.blit(tit, tit.get_rect(center=(cx, 80)))
        # Subtítulo
        sub = self.fuente_pequena.render("Aprende y explora el litoral colombiano", True, COLOR_ARENA)
        self.pantalla.blit(sub, sub.get_rect(center=(cx, 126)))

    def _dibujar_panel(self):
        """Panel semitransparente con la pregunta del nombre."""
        sup = pygame.Surface((self.rect_panel.width, self.rect_panel.height), pygame.SRCALPHA)
        sup.fill((0, 0, 0, 120))
        pygame.draw.rect(sup, (*COLOR_MADERA, 200), sup.get_rect(), 3, border_radius=18)
        self.pantalla.blit(sup, self.rect_panel.topleft)
        # Pregunta
        preg = self.fuente_texto.render("¿Como te llamas?", True, COLOR_TEXTO)
        self.pantalla.blit(preg, preg.get_rect(center=(self.ancho // 2, self.rect_panel.top + 52)))

    def _dibujar_campo(self):
        """Campo de texto para el nombre del estudiante."""
        color_borde = COLOR_INPUT_ACT if self.campo_activo else COLOR_INPUT_ORD
        pygame.draw.rect(self.pantalla, COLOR_INPUT_BG, self.rect_campo, border_radius=10)
        pygame.draw.rect(self.pantalla, color_borde, self.rect_campo, 3, border_radius=10)

        texto = self.nombre_ingresado
        if self.campo_activo and self.cursor_visible:
            texto += "|"
        sup_txt = self.fuente_texto.render(texto, True, (20, 20, 20))
        self.pantalla.blit(
            sup_txt,
            (self.rect_campo.left + 12, self.rect_campo.centery - sup_txt.get_height() // 2)
        )
        # Texto de ayuda
        if not self.nombre_ingresado and not self.campo_activo:
            ayuda = self.fuente_pequena.render("Escribe tu nombre aqui...", True, (160, 140, 100))
            self.pantalla.blit(
                ayuda,
                (self.rect_campo.left + 12, self.rect_campo.centery - ayuda.get_height() // 2)
            )

    def _dibujar_boton(self):
        """Botón de 'Entrar' con efecto hover."""
        hover = self.rect_boton.collidepoint(pygame.mouse.get_pos())
        color = COLOR_BOTON_HOV if hover else COLOR_BOTON
        # Sombra
        sombra = self.rect_boton.move(3, 4)
        pygame.draw.rect(self.pantalla, (20, 15, 5), sombra, border_radius=14)
        # Botón
        pygame.draw.rect(self.pantalla, color, self.rect_boton, border_radius=14)
        pygame.draw.rect(self.pantalla, COLOR_MADERA, self.rect_boton, 2, border_radius=14)
        # Texto
        txt = self.fuente_texto.render("¡Entrar!", True, (255, 255, 240))
        self.pantalla.blit(txt, txt.get_rect(center=self.rect_boton.center))

    def _dibujar_mensaje(self):
        """Mensaje de éxito o error debajo del botón."""
        sup = self.fuente_pequena.render(self.mensaje, True, self.color_mensaje)
        self.pantalla.blit(sup, sup.get_rect(center=self.pos_mensaje))
