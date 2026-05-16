"""
point_and_click.py - Minijuego de señalar y hacer clic (Point and Click)
Maneja niveles donde el niño identifica elementos en pantalla según una instrucción.
"""

import pygame
import random
import math
import os
from utils.audio_manager import gestor_audio

# ---------------------------------------------------------------------------
# Colores del litoral Pacífico
# ---------------------------------------------------------------------------
C_SELVA      = (45, 90, 39)
C_RIO        = (27, 79, 114)
C_MADERA     = (139, 105, 20)
C_ORO        = (244, 208, 63)
C_ARENA      = (210, 180, 120)
C_TEXTO      = (240, 235, 210)
C_OK         = (80, 200, 80)
C_ERROR      = (200, 70, 70)
C_BLANCO     = (255, 255, 255)

class ItemPointClick:
    """
    Representa un objeto interactivo en el minijuego.
    Maneja su propia animación de escala y temblor.
    """
    def __init__(self, datos, pos):
        self.nombre = datos.get("nombre", "item")
        self.es_correcto = datos.get("es_correcto", False)
        self.seleccionado = False
        self.error_activo = False
        
        # Cargar imagen
        ruta_img = datos.get("imagen", "")
        if os.path.exists(ruta_img):
            self.imagen_original = pygame.image.load(ruta_img).convert_alpha()
        else:
            # Placeholder si no existe la imagen
            self.imagen_original = pygame.Surface((80, 80), pygame.SRCALPHA)
            pygame.draw.circle(self.imagen_original, C_MADERA, (40, 40), 35)
            # Dibujar inicial o algo identificativo
            fuente = pygame.font.SysFont('Arial', 20, bold=True)
            txt = fuente.render(self.nombre[:2].upper(), True, C_TEXTO)
            self.imagen_original.blit(txt, txt.get_rect(center=(40, 40)))

        self.rect = self.imagen_original.get_rect(center=pos)
        self.pos_original = pygame.Vector2(pos)
        
        # Animación
        self.escala_actual = 1.0
        self.objetivo_escala = 1.0
        self.timer_error = 0.0
        self.offset_error = pygame.Vector2(0, 0)

    def actualizar(self, dt, raton_pos):
        # Escala suave al pasar el mouse
        if self.rect.collidepoint(raton_pos) and not self.seleccionado:
            self.objetivo_escala = 1.15
        else:
            self.objetivo_escala = 1.0
        
        # Interpolar escala
        self.escala_actual += (self.objetivo_escala - self.escala_actual) * 10 * dt
        
        # Animación de temblor si hubo error
        if self.error_activo:
            self.timer_error -= dt
            if self.timer_error <= 0:
                self.error_activo = False
                self.offset_error = pygame.Vector2(0, 0)
            else:
                # Oscilación rápida
                self.offset_error.x = math.sin(pygame.time.get_ticks() * 0.05) * 5
        
        # Actualizar rect para colisiones precisas (opcional, aquí usamos el centro)
        nuevo_ancho = int(self.imagen_original.get_width() * self.escala_actual)
        nuevo_alto = int(self.imagen_original.get_height() * self.escala_actual)
        self.rect.width = nuevo_ancho
        self.rect.height = nuevo_alto
        self.rect.center = self.pos_original + self.offset_error

    def dibujar(self, pantalla):
        # Dibujar sombra
        sombra_rect = self.rect.copy()
        sombra_rect.move_ip(3, 3)
        sombra_surf = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        sombra_surf.fill((0, 0, 0, 80))
        # pantalla.blit(sombra_surf, sombra_rect) # Simplificado

        # Escalar imagen
        img_dibujar = pygame.transform.smoothscale(self.imagen_original, self.rect.size)
        
        # Resaltar si ya fue seleccionado correctamente
        if self.seleccionado:
            # Dibujar un brillo o borde verde
            pygame.draw.rect(pantalla, C_OK, self.rect.inflate(10, 10), 3, border_radius=10)
        elif self.error_activo:
            pygame.draw.rect(pantalla, C_ERROR, self.rect.inflate(10, 10), 3, border_radius=10)

        pantalla.blit(img_dibujar, self.rect)

    def activar_error(self):
        self.error_activo = True
        self.timer_error = 0.5 # Medio segundo de temblor

class MinijuegoPointClick:
    """
    Minijuego donde el niño debe tocar los elementos correctos.
    Compatible con el sistema de escenas de main.py.
    """
    def __init__(self, pantalla, ancho, alto, nivel, materia, items_datos=None, instruccion=""):
        self.pantalla = pantalla
        self.ancho = ancho
        self.alto = alto
        self.nivel = nivel
        self.materia = materia
        self.instruccion = instruccion
        
        # Si no pasan items_datos (llamada desde main.py), usar unos por defecto para demo
        if items_datos is None:
            items_datos = self._generar_items_demo()
            self.instruccion = self._generar_instruccion_demo()

        self.activo = True
        self.escena_siguiente = 'level_select'
        self.puntaje_final = 0
        self.puntaje = 100
        self.errores = 0
        
        self.tiempo_transcurrido = 0.0
        self.victoria = False
        self.timer_victoria = 0.0

        # Fuentes
        self.f_instruccion = pygame.font.SysFont('Arial', 28, bold=True)
        self.f_info = pygame.font.SysFont('Arial', 20)
        self.f_victoria = pygame.font.SysFont('Arial', 48, bold=True)

        # Crear objetos y distribuirlos
        self.items = []
        self._distribuir_items(items_datos)
        
        # Cantidad de items correctos a encontrar
        self.total_correctos = sum(1 for d in items_datos if d.get("es_correcto", False))
        self.encontrados = 0

    def _generar_items_demo(self):
        # Generar datos de ejemplo según materia y nivel
        # Esto es lo que main.py llamaría si no se le inyectan datos
        if self.materia == 'matematicas':
            cantidad = random.randint(3, 6)
            items = []
            # 'Correctos' (ej. cangrejos)
            for _ in range(cantidad):
                items.append({"nombre": "cangrejo", "es_correcto": True, "imagen": "assets/images/characters/cangrejo.png"})
            # 'Incorrectos' (ej. piedras)
            for _ in range(4):
                items.append({"nombre": "piedra", "es_correcto": False, "imagen": "assets/images/characters/piedra.png"})
            return items
        elif self.materia == 'biologia':
            return [
                {"nombre": "ballena", "es_correcto": True},
                {"nombre": "mono", "es_correcto": True},
                {"nombre": "planta", "es_correcto": False},
                {"nombre": "flor", "es_correcto": False},
                {"nombre": "tucan", "es_correcto": True},
            ]
        # Default
        return [{"nombre": f"Item {i}", "es_correcto": i%2==0} for i in range(6)]

    def _generar_instruccion_demo(self):
        if self.materia == 'matematicas':
            return "Toca todos los cangrejos que encuentres"
        elif self.materia == 'biologia':
            return "Toca solo los animales de la selva"
        return "Toca los elementos correctos"

    def _distribuir_items(self, datos):
        # Intentar colocar items sin que se solapen demasiado
        margen = 100
        intentos_max = 50
        for d in datos:
            colocado = False
            for _ in range(intentos_max):
                x = random.randint(margen, self.ancho - margen)
                y = random.randint(margen + 80, self.alto - margen)
                nueva_pos = (x, y)
                
                # Verificar colisión con existentes
                solapado = False
                for item in self.items:
                    if pygame.Vector2(nueva_pos).distance_to(item.pos_original) < 100:
                        solapado = True
                        break
                
                if not solapado:
                    self.items.append(ItemPointClick(d, nueva_pos))
                    colocado = True
                    break
            
            if not colocado: # Si fallan los intentos, colocar igual
                self.items.append(ItemPointClick(d, (random.randint(margen, self.ancho-margen), random.randint(margen+80, self.alto-margen))))

    def manejar_eventos(self, eventos):
        if self.victoria:
            return

        for ev in eventos:
            # Soporte para clic y touch
            if (ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1) or ev.type == pygame.FINGERDOWN:
                if ev.type == pygame.FINGERDOWN:
                    pos = (ev.x * self.ancho, ev.y * self.alto)
                else:
                    pos = ev.pos
                
                self._procesar_clic(pos)

    def _procesar_clic(self, pos):
        for item in self.items:
            if not item.seleccionado and item.rect.collidepoint(pos):
                if item.es_correcto:
                    item.seleccionado = True
                    self.encontrados += 1
                    gestor_audio.reproducir_sonido('correcto.wav')
                    if self.encontrados == self.total_correctos:
                        self.victoria = True
                        self.puntaje_final = max(0, self.puntaje)
                else:
                    item.activar_error()
                    self.errores += 1
                    self.puntaje -= 10
                    gestor_audio.reproducir_sonido('incorrecto.wav')
                break

    def actualizar(self, dt):
        self.tiempo_transcurrido += dt
        raton_pos = pygame.mouse.get_pos()
        
        for item in self.items:
            item.actualizar(dt, raton_pos)
            
        if self.victoria:
            self.timer_victoria += dt
            if self.timer_victoria >= 3.0:
                self.activo = False

    def dibujar(self):
        # Fondo temático (Arena/Playa)
        self.pantalla.fill(C_ARENA)
        
        # Dibujar decoraciones simples (olas arriba)
        pygame.draw.rect(self.pantalla, C_RIO, (0, 0, self.ancho, 60))
        
        # Instrucción
        ins_surf = self.f_instruccion.render(self.instruccion, True, C_TEXTO)
        self.pantalla.blit(ins_surf, ins_surf.get_rect(center=(self.ancho//2, 30)))
        
        # Items
        for item in self.items:
            item.dibujar(self.pantalla)
            
        # UI: Puntaje y Progreso
        txt_pts = self.f_info.render(f"Puntaje: {max(0, self.puntaje)}", True, C_MADERA)
        self.pantalla.blit(txt_pts, (20, self.alto - 40))
        
        txt_prog = self.f_info.render(f"Encontrados: {self.encontrados}/{self.total_correctos}", True, C_MADERA)
        self.pantalla.blit(txt_prog, (self.ancho - 200, self.alto - 40))
        
        # Tiempo (Min:Seg)
        mins = int(self.tiempo_transcurrido // 60)
        segs = int(self.tiempo_transcurrido % 60)
        txt_tiempo = self.f_info.render(f"Tiempo: {mins:02d}:{segs:02d}", True, C_MADERA)
        self.pantalla.blit(txt_tiempo, (self.ancho//2 - 50, self.alto - 40))

        # Pantalla de Victoria
        if self.victoria:
            overlay = pygame.Surface((self.ancho, self.alto), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            self.pantalla.blit(overlay, (0, 0))
            
            vic_surf = self.f_victoria.render("¡EXCELENTE TRABAJO!", True, C_ORO)
            self.pantalla.blit(vic_surf, vic_surf.get_rect(center=(self.ancho//2, self.alto//2 - 50)))
            
            pts_surf = self.f_instruccion.render(f"Puntaje Final: {self.puntaje_final}", True, C_BLANCO)
            self.pantalla.blit(pts_surf, pts_surf.get_rect(center=(self.ancho//2, self.alto//2 + 20)))
            
            msg_surf = self.f_info.render("Regresando al mapa...", True, C_ARENA)
            self.pantalla.blit(msg_surf, msg_surf.get_rect(center=(self.ancho//2, self.alto//2 + 80)))

def ejecutar_minijuego(items_datos, instruccion, audio_manager=None):
    """
    Función de utilidad para ejecutar este minijuego de forma independiente si es necesario.
    Crea una ventana temporal de pygame y corre el bucle.
    """
    pygame.init()
    pantalla = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Pacífico Educativo - Point and Click")
    reloj = pygame.time.Clock()
    
    # Inyectar audio_manager si se provee (aunque usamos el singleton por defecto)
    
    juego = MinijuegoPointClick(pantalla, 800, 600, 1, 'general', items_datos, instruccion)
    
    while juego.activo:
        dt = reloj.tick(60) / 1000.0
        eventos = pygame.event.get()
        for ev in eventos:
            if ev.type == pygame.QUIT:
                return 0
        
        juego.manejar_eventos(eventos)
        juego.actualizar(dt)
        juego.dibujar()
        pygame.display.flip()
        
    return juego.puntaje_final
