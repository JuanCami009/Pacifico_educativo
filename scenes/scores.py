"""
scores.py - Pantalla de puntajes del estudiante
Estilo visual de "Diario de Viaje" o "Mapa del Tesoro" para ver el progreso sin competencia.
"""

import pygame
from utils.database import obtener_mejor_puntaje

# Colores estilo "Diario de viaje / Mapa"
C_FONDO_PAGINA = (245, 235, 215) # Papel viejo / Pergamino
C_TINTA        = (60, 45, 30)    # Tinta sepia oscura
C_LINEA        = (180, 160, 130) # Líneas guía del papel
C_MATERIA      = (120, 40, 30)   # Tinta roja oscura para títulos
C_BOTON        = (140, 100, 60)
C_BOTON_HOVER  = (160, 120, 80)

MATERIAS = [
    ('matematicas', 'Matemáticas'),
    ('lenguaje', 'Lenguaje'),
    ('ingles', 'Inglés'),
    ('biologia', 'Biología')
]

class PantallaScores:
    def __init__(self, pantalla, ancho, alto, estudiante):
        self.pantalla = pantalla
        self.ancho = ancho
        self.alto = alto
        self.estudiante = estudiante
        
        self.activo = True
        self.escena_siguiente = 'menu'
        
        # Cargar fuentes
        self.f_titulo = pygame.font.SysFont('Georgia', 36, bold=True, italic=True)
        self.f_sub    = pygame.font.SysFont('Georgia', 22, bold=True)
        self.f_texto  = pygame.font.SysFont('Georgia', 20)
        self.f_boton  = pygame.font.SysFont('Arial', 20, bold=True)
        
        # Botón Volver
        self.rect_volver = pygame.Rect(self.ancho // 2 - 100, self.alto - 70, 200, 45)
        
        # Obtener puntajes: 4 materias x 5 niveles
        self.puntajes = {}
        for mat_id, _ in MATERIAS:
            self.puntajes[mat_id] = []
            for nivel in range(1, 6):
                pts = obtener_mejor_puntaje(self.estudiante['id'], mat_id, nivel)
                self.puntajes[mat_id].append(pts)

    def manejar_eventos(self, eventos):
        for ev in eventos:
            if ev.type == pygame.QUIT:
                self.activo = False
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                raton = pygame.mouse.get_pos()
                if self.rect_volver.collidepoint(raton):
                    self.activo = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    self.activo = False

    def actualizar(self, dt):
        pass

    def dibujar(self):
        # Fondo de pergamino
        self.pantalla.fill(C_FONDO_PAGINA)
        
        # Dibujar líneas horizontales tenues simulando un cuaderno viejo
        for y in range(100, self.alto - 80, 40):
            pygame.draw.line(self.pantalla, C_LINEA, (40, y), (self.ancho - 40, y), 1)
            
        # Título
        tit = self.f_titulo.render(f"Diario de Viaje de {self.estudiante['nombre']}", True, C_TINTA)
        self.pantalla.blit(tit, tit.get_rect(center=(self.ancho // 2, 50)))
        
        # Encabezados de tabla
        x_inicio = 80
        y_inicio = 120
        ancho_col = 130
        
        # Niveles (columnas)
        for i in range(1, 6):
            txt_n = self.f_sub.render(f"Nivel {i}", True, C_TINTA)
            self.pantalla.blit(txt_n, txt_n.get_rect(center=(x_inicio + 150 + (i-1)*ancho_col, y_inicio)))
            
        pygame.draw.line(self.pantalla, C_TINTA, (x_inicio, y_inicio + 30), (self.ancho - x_inicio, y_inicio + 30), 2)
        
        # Filas por materia
        y_actual = y_inicio + 60
        for mat_id, mat_nombre in MATERIAS:
            # Nombre de materia
            txt_m = self.f_sub.render(mat_nombre, True, C_MATERIA)
            self.pantalla.blit(txt_m, (x_inicio, y_actual - 12))
            
            # Puntajes
            for i, pts in enumerate(self.puntajes[mat_id]):
                str_pts = str(pts) if pts > 0 else "—"
                txt_p = self.f_texto.render(str_pts, True, C_TINTA)
                x_pts = x_inicio + 150 + i * ancho_col
                self.pantalla.blit(txt_p, txt_p.get_rect(center=(x_pts, y_actual)))
                
            y_actual += 60
            
        # Botón Volver
        raton = pygame.mouse.get_pos()
        hover = self.rect_volver.collidepoint(raton)
        c_btn = C_BOTON_HOVER if hover else C_BOTON
        
        # Efecto de sombra rústica
        sombra = self.rect_volver.copy()
        sombra.move_ip(3, 3)
        pygame.draw.rect(self.pantalla, (100, 80, 50), sombra, border_radius=8)
        pygame.draw.rect(self.pantalla, c_btn, self.rect_volver, border_radius=8)
        pygame.draw.rect(self.pantalla, C_TINTA, self.rect_volver, 2, border_radius=8)
        
        txt_btn = self.f_boton.render("Volver al Menú", True, C_FONDO_PAGINA)
        self.pantalla.blit(txt_btn, txt_btn.get_rect(center=self.rect_volver.center))
