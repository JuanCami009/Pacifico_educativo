"""
puzzle.py - Minijuego de Rompecabezas (Puzzle)
Dos modos: Ordenar Secuencias o Completar Imágenes.
"""

import pygame
import random
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
C_HUECO      = (30, 60, 30, 150) # Semitransparente
C_BLANCO     = (255, 255, 255)

class PiezaPuzzle:
    """Pieza arrastrable del rompecabezas."""
    def __init__(self, datos, pos_inicial, target_idx=None, target_pos=None):
        self.texto = datos.get("texto", "")
        self.target_idx = target_idx # Para modo secuencia
        self.target_pos = target_pos # Para modo completar (x,y en la pantalla)
        
        ruta_img = datos.get("imagen", "")
        if os.path.exists(ruta_img):
            self.imagen = pygame.image.load(ruta_img).convert_alpha()
        else:
            # Placeholder si no hay imagen
            self.imagen = pygame.Surface((100, 100), pygame.SRCALPHA)
            pygame.draw.rect(self.imagen, C_MADERA, self.imagen.get_rect(), border_radius=10)
            pygame.draw.rect(self.imagen, C_ORO, self.imagen.get_rect(), 2, border_radius=10)
            if self.texto:
                f = pygame.font.SysFont('Arial', 20, bold=True)
                t = f.render(self.texto, True, C_TEXTO)
                self.imagen.blit(t, t.get_rect(center=(50,50)))

        self.rect = self.imagen.get_rect(center=pos_inicial)
        self.pos_original = pygame.Vector2(pos_inicial)
        self.pos_actual = pygame.Vector2(pos_inicial)
        
        self.arrastrando = False
        self.colocada = False
        self.offset = pygame.Vector2(0, 0)
        self.retornando = False

    def actualizar(self, dt):
        if self.arrastrando:
            raton_pos = pygame.Vector2(pygame.mouse.get_pos())
            self.pos_actual = raton_pos + self.offset
            self.rect.center = self.pos_actual
        elif self.retornando:
            dir_vec = self.pos_original - self.pos_actual
            dist = dir_vec.length()
            if dist < 5.0:
                self.pos_actual = pygame.Vector2(self.pos_original)
                self.retornando = False
            else:
                self.pos_actual += dir_vec.normalize() * dist * 15.0 * dt
            self.rect.center = self.pos_actual

    def dibujar(self, pantalla):
        if self.arrastrando:
            sombra = self.rect.copy()
            sombra.move_ip(5, 5)
            pygame.draw.rect(pantalla, (0,0,0,80), sombra, border_radius=10)
            
            escala = pygame.transform.smoothscale(self.imagen, (int(self.rect.w*1.1), int(self.rect.h*1.1)))
            pantalla.blit(escala, escala.get_rect(center=self.rect.center))
        else:
            if self.colocada:
                # Borde verde suave si ya está colocada
                pygame.draw.rect(pantalla, C_OK, self.rect.inflate(6,6), 3, border_radius=10)
            pantalla.blit(self.imagen, self.rect)


class MinijuegoPuzzle:
    """
    Minijuego de rompecabezas. Soporta dos modos: 'secuencia' y 'completar'.
    """
    def __init__(self, pantalla, ancho, alto, nivel, materia, modo="secuencia", datos=None, instruccion="", palabras_datos=None):
        self.pantalla = pantalla
        self.ancho = ancho
        self.alto = alto
        self.nivel = nivel
        self.materia = materia
        self.modo = modo
        self.instruccion = instruccion
        
        self.activo = True
        self.escena_siguiente = 'level_select'
        self.puntaje_final = 0
        self.puntaje = 100
        
        self.tiempo_transcurrido = 0.0
        self.victoria = False
        self.timer_victoria = 0.0

        self.piezas = []
        self.huecos = [] # Para secuencias: [rects], para completar: [rects] target
        self.imagen_base = None
        self.pieza_arrastrada = None

        self._cargar_fuentes()

        # Adaptador para el sistema antiguo que pasaba palabras_datos (main.py antiguo)
        if palabras_datos and not datos:
            # Convertimos la primera palabra en una secuencia de letras (modo secuencia)
            palabra = palabras_datos[0][0] # Ej: "BALLENA"
            self.modo = "secuencia"
            self.instruccion = f"Ordena las letras para formar la palabra de la pista: {palabras_datos[0][1]}"
            datos = [{"texto": letra} for letra in palabra]

        if datos:
            if self.modo == "secuencia":
                self._iniciar_modo_secuencia(datos)
            elif self.modo == "completar":
                self._iniciar_modo_completar(datos)
        else:
            # Fallback Demo si no hay datos
            self._iniciar_demo()

    def _cargar_fuentes(self):
        self.f_inst   = pygame.font.SysFont('Arial', 26, bold=True)
        self.f_info   = pygame.font.SysFont('Arial', 18)
        self.f_vict   = pygame.font.SysFont('Arial', 48, bold=True)

    def _iniciar_modo_secuencia(self, datos_secuencia):
        if not self.instruccion:
            self.instruccion = "Arrastra las tarjetas en el orden correcto"
            
        n = len(datos_secuencia)
        tam_w, tam_h = 100, 100
        sep = 20
        total_w = n * tam_w + (n-1) * sep
        inicio_x = self.ancho // 2 - total_w // 2
        y_huecos = self.alto // 2 - 80
        
        # Crear los huecos (slots) en orden correcto
        for i in range(n):
            rect = pygame.Rect(inicio_x + i * (tam_w + sep), y_huecos, tam_w, tam_h)
            self.huecos.append({'rect': rect, 'idx': i})

        # Crear piezas desordenadas abajo
        y_piezas = self.alto // 2 + 100
        indices_mezclados = list(range(n))
        random.shuffle(indices_mezclados)
        
        for i, real_idx in enumerate(indices_mezclados):
            pos = (inicio_x + i * (tam_w + sep) + tam_w//2, y_piezas + tam_h//2)
            p = PiezaPuzzle(datos_secuencia[real_idx], pos, target_idx=real_idx)
            self.piezas.append(p)

    def _iniciar_modo_completar(self, datos_completar):
        if not self.instruccion:
            self.instruccion = "Completa la imagen arrastrando las piezas a su lugar"
            
        # datos_completar debe ser dict: {"imagen_base": "...", "piezas": [...]}
        ruta_base = datos_completar.get("imagen_base", "")
        if os.path.exists(ruta_base):
            self.imagen_base = pygame.image.load(ruta_base).convert_alpha()
            self.rect_base = self.imagen_base.get_rect(center=(self.ancho//2, self.alto//2 - 20))
        else:
            # Placeholder imagen base
            self.imagen_base = pygame.Surface((400, 300))
            self.imagen_base.fill(C_RIO)
            pygame.draw.rect(self.imagen_base, C_SELVA, (0, 200, 400, 100)) # Suelo
            self.rect_base = self.imagen_base.get_rect(center=(self.ancho//2, self.alto//2 - 20))

        piezas_datos = datos_completar.get("piezas", [])
        
        # Distribuir piezas sueltas a los lados
        for i, pdato in enumerate(piezas_datos):
            # pdato["posicion"] indica dónde debe ir respecto a la pantalla
            target_pos = pdato.get("posicion", (self.ancho//2, self.alto//2))
            
            # Ponerla en un lugar random a los bordes
            if i % 2 == 0:
                pos_ini = (random.randint(60, 150), random.randint(150, self.alto-150))
            else:
                pos_ini = (random.randint(self.ancho-150, self.ancho-60), random.randint(150, self.alto-150))
                
            p = PiezaPuzzle(pdato, pos_ini, target_pos=target_pos)
            self.piezas.append(p)
            
            # Crear hueco visual (opcional, para ayudar al niño)
            tam = p.rect.size
            self.huecos.append({'rect': pygame.Rect(0, 0, tam[0], tam[1]), 'pos': target_pos})
            self.huecos[-1]['rect'].center = target_pos

    def _iniciar_demo(self):
        # Demo de modo secuencia (Ej: ciclo del agua)
        self.modo = "secuencia"
        datos = [
            {"texto": "Sol calienta"},
            {"texto": "Evaporacion"},
            {"texto": "Nubes"},
            {"texto": "Lluvia"}
        ]
        self._iniciar_modo_secuencia(datos)

    def manejar_eventos(self, eventos):
        if self.victoria: return

        for ev in eventos:
            if (ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1) or ev.type == pygame.FINGERDOWN:
                if ev.type == pygame.FINGERDOWN: pos = (ev.x * self.ancho, ev.y * self.alto)
                else: pos = ev.pos
                
                # Buscar de arriba hacia abajo (z-order invertido)
                for p in reversed(self.piezas):
                    if not p.colocada and p.rect.collidepoint(pos):
                        p.arrastrando = True
                        p.retornando = False
                        p.offset = pygame.Vector2(p.rect.center) - pygame.Vector2(pos)
                        self.pieza_arrastrada = p
                        gestor_audio.reproducir_sonido('clic.wav')
                        
                        # Z-order top
                        self.piezas.remove(p)
                        self.piezas.append(p)
                        break
                        
            elif (ev.type == pygame.MOUSEBUTTONUP and ev.button == 1) or ev.type == pygame.FINGERUP:
                if self.pieza_arrastrada:
                    self._verificar_soltar(self.pieza_arrastrada)
                    self.pieza_arrastrada.arrastrando = False
                    self.pieza_arrastrada = None

    def _verificar_soltar(self, p):
        encajo = False
        
        if self.modo == "secuencia":
            # Verificar con qué hueco colisiona
            for h in self.huecos:
                if p.rect.colliderect(h['rect']):
                    if p.target_idx == h['idx']:
                        # Correcto
                        p.colocada = True
                        p.pos_actual = pygame.Vector2(h['rect'].center)
                        p.rect.center = p.pos_actual
                        encajo = True
                    break
        elif self.modo == "completar":
            # Verificar si está cerca de su target_pos
            dist = pygame.Vector2(p.rect.center).distance_to(p.target_pos)
            if dist < 60: # Margen de error generoso (60px)
                p.colocada = True
                p.pos_actual = pygame.Vector2(p.target_pos)
                p.rect.center = p.pos_actual
                encajo = True
                
        if encajo:
            gestor_audio.reproducir_sonido('correcto.wav')
            if all(pz.colocada for pz in self.piezas):
                self.victoria = True
                self.puntaje_final = max(0, self.puntaje)
        else:
            p.retornando = True
            self.puntaje -= 10
            gestor_audio.reproducir_sonido('incorrecto.wav')

    def actualizar(self, dt):
        self.tiempo_transcurrido += dt
        for p in self.piezas:
            p.actualizar(dt)

        if self.victoria:
            self.timer_victoria += dt
            if self.timer_victoria >= 3.0:
                self.activo = False

    def dibujar(self):
        # Fondo
        self.pantalla.fill(C_RIO if self.modo == "secuencia" else C_SELVA)
        
        # Instrucción
        ins = self.f_inst.render(self.instruccion, True, C_TEXTO)
        self.pantalla.blit(ins, ins.get_rect(center=(self.ancho//2, 30)))

        if self.modo == "secuencia":
            # Dibujar huecos
            for h in self.huecos:
                pygame.draw.rect(self.pantalla, (0,0,0,50), h['rect'], border_radius=10)
                pygame.draw.rect(self.pantalla, C_ARENA, h['rect'], 2, border_radius=10)
        
        elif self.modo == "completar":
            if self.imagen_base:
                # Sombra de imagen base
                sombra_base = self.rect_base.copy().move(5,5)
                pygame.draw.rect(self.pantalla, (0,0,0,100), sombra_base)
                self.pantalla.blit(self.imagen_base, self.rect_base)
            
            # Dibujar siluetas/huecos donde van las piezas
            for h in self.huecos:
                pygame.draw.rect(self.pantalla, (0,0,0,60), h['rect'], border_radius=10)
                pygame.draw.rect(self.pantalla, C_ARENA, h['rect'], 2, border_radius=10, style=pygame.BLEND_RGBA_ADD)

        # Dibujar piezas (z-order controlado automáticamente por la lista)
        for p in self.piezas:
            p.dibujar(self.pantalla)

        # UI inferior
        pts = self.f_info.render(f"Puntaje: {max(0, self.puntaje)}", True, C_ARENA)
        self.pantalla.blit(pts, (20, self.alto - 30))

        # Victoria
        if self.victoria:
            overlay = pygame.Surface((self.ancho, self.alto), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.pantalla.blit(overlay, (0, 0))
            
            v = self.f_vict.render("¡ROMPECABEZAS RESUELTO!", True, C_ORO)
            self.pantalla.blit(v, v.get_rect(center=(self.ancho//2, self.alto//2 - 40)))
            
            p = self.f_inst.render(f"Puntaje Final: {self.puntaje_final}", True, C_BLANCO)
            self.pantalla.blit(p, p.get_rect(center=(self.ancho//2, self.alto//2 + 30)))

def ejecutar_minijuego(modo, datos, instruccion, audio_manager=None):
    """Función de utilidad para testear el minijuego de manera aislada."""
    pygame.init()
    pantalla = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Pacífico Educativo - Puzzle")
    reloj = pygame.time.Clock()
    
    juego = MinijuegoPuzzle(pantalla, 800, 600, 1, 'general', modo=modo, datos=datos, instruccion=instruccion)
    
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
