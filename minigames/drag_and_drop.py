"""
drag_and_drop.py - Minijuego de arrastrar y soltar (Drag and Drop)
Maneja niveles donde el niño arrastra elementos visuales hacia zonas destino correctas.
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
C_ZONA       = (30, 60, 30)
C_BLANCO     = (255, 255, 255)
C_ZONA_HOVER = (60, 120, 60) # Color cuando una pieza está cerca

class ZonaDestino:
    """Representa una zona donde se pueden soltar piezas."""
    def __init__(self, datos, pos_defecto=(0,0)):
        self.id = datos.get("id", "zona")
        self.etiqueta = datos.get("etiqueta", "")
        
        # Intentar cargar imagen, si no, usar placeholder
        ruta_img = datos.get("imagen", "")
        if os.path.exists(ruta_img):
            self.imagen = pygame.image.load(ruta_img).convert_alpha()
        else:
            self.imagen = pygame.Surface((140, 100), pygame.SRCALPHA)
            pygame.draw.rect(self.imagen, C_ZONA, self.imagen.get_rect(), border_radius=15)
            pygame.draw.rect(self.imagen, C_MADERA, self.imagen.get_rect(), 3, border_radius=15)

        # Usar posición provista o la de defecto
        pos = datos.get("posicion", pos_defecto)
        self.rect = self.imagen.get_rect(center=pos)
        self.hover = False # Indica si una pieza está siendo arrastrada sobre esta zona
        self.ocupada = False # Opcional: si solo acepta una pieza
        
        self.f_etiqueta = pygame.font.SysFont('Arial', 18, bold=True)

    def dibujar(self, pantalla):
        # Dibujar base
        img_dibujar = self.imagen.copy()
        
        # Efecto visual si una pieza está cerca (hover)
        if self.hover:
            pygame.draw.rect(img_dibujar, C_ZONA_HOVER, img_dibujar.get_rect(), 4, border_radius=15)
            
        pantalla.blit(img_dibujar, self.rect)
        
        # Dibujar etiqueta debajo de la zona
        if self.etiqueta:
            txt = self.f_etiqueta.render(self.etiqueta, True, C_TEXTO)
            pantalla.blit(txt, txt.get_rect(center=(self.rect.centerx, self.rect.bottom + 15)))

class ItemPieza:
    """Representa un elemento que el niño puede arrastrar."""
    def __init__(self, datos, pos_inicial):
        self.nombre = datos.get("nombre", "pieza")
        self.zona_destino = datos.get("zona_destino", "")
        
        # Intentar cargar imagen
        ruta_img = datos.get("imagen", "")
        if os.path.exists(ruta_img):
            self.imagen = pygame.image.load(ruta_img).convert_alpha()
        else:
            self.imagen = pygame.Surface((80, 80), pygame.SRCALPHA)
            pygame.draw.circle(self.imagen, C_ORO, (40, 40), 38)
            pygame.draw.circle(self.imagen, C_MADERA, (40, 40), 38, 2)
            f_nombre = pygame.font.SysFont('Arial', 16, bold=True)
            # Mostrar primeras letras si no hay imagen
            txt = f_nombre.render(self.nombre[:4], True, C_SELVA)
            self.imagen.blit(txt, txt.get_rect(center=(40,40)))

        self.rect = self.imagen.get_rect(center=pos_inicial)
        self.pos_original = pygame.Vector2(pos_inicial)
        self.pos_actual = pygame.Vector2(pos_inicial)
        
        self.arrastrando = False
        self.colocada = False
        self.offset_arrastre = pygame.Vector2(0, 0)
        
        # Animación de retorno
        self.retornando = False
        self.velocidad_retorno = 15.0

    def actualizar(self, dt):
        if self.arrastrando:
            raton_pos = pygame.Vector2(pygame.mouse.get_pos())
            self.pos_actual = raton_pos + self.offset_arrastre
            self.rect.center = self.pos_actual
        elif self.retornando:
            # Movimiento suave hacia la posición original
            direccion = self.pos_original - self.pos_actual
            distancia = direccion.length()
            
            if distancia < 5.0:
                self.pos_actual = pygame.Vector2(self.pos_original)
                self.retornando = False
            else:
                direccion = direccion.normalize()
                # Velocidad proporcional a la distancia
                self.pos_actual += direccion * distancia * self.velocidad_retorno * dt
            
            self.rect.center = self.pos_actual

    def dibujar(self, pantalla):
        # Si se está arrastrando, dibujar un poco más grande y con sombra
        if self.arrastrando:
            sombra = self.rect.copy()
            sombra.move_ip(5, 5)
            pygame.draw.rect(pantalla, (0,0,0,80), sombra, border_radius=40)
            
            img_escala = pygame.transform.smoothscale(self.imagen, (int(self.rect.width*1.1), int(self.rect.height*1.1)))
            rect_escala = img_escala.get_rect(center=self.rect.center)
            pantalla.blit(img_escala, rect_escala)
        else:
            # Si está colocada, dibujar un efecto de encaje (brillo sutil)
            if self.colocada:
                pygame.draw.circle(pantalla, C_OK, self.rect.center, self.rect.width//2 + 4, 3)
            pantalla.blit(self.imagen, self.rect)


class MinijuegoDragDrop:
    """
    Minijuego principal de arrastrar y soltar.
    """
    def __init__(self, pantalla, ancho, alto, nivel, materia, piezas_datos=None, zonas_datos=None, instruccion="", pares_datos=None):
        self.pantalla = pantalla
        self.ancho = ancho
        self.alto = alto
        self.nivel = nivel
        self.materia = materia
        self.instruccion = instruccion
        
        self.activo = True
        self.escena_siguiente = 'level_select'
        self.puntaje_final = 0
        self.puntaje = 100
        
        self.tiempo_transcurrido = 0.0
        self.victoria = False
        self.timer_victoria = 0.0
        
        self.piezas = []
        self.zonas = []
        self.pieza_arrastrada = None # Referencia a la pieza actual (para z-order)

        self._cargar_fuentes()
        
        # Adaptabilidad: Si se llama desde main.py antiguo que pasaba pares_datos
        if pares_datos and not piezas_datos:
            self._convertir_pares_a_piezas_zonas(pares_datos)
        elif piezas_datos and zonas_datos:
            self._inicializar_desde_datos(piezas_datos, zonas_datos)
        else:
            # Fallback demo
            self._generar_demo()

    def _cargar_fuentes(self):
        self.f_inst   = pygame.font.SysFont('Arial', 26, bold=True)
        self.f_info   = pygame.font.SysFont('Arial', 18)
        self.f_vict   = pygame.font.SysFont('Arial', 48, bold=True)

    def _convertir_pares_a_piezas_zonas(self, pares):
        """Convierte el formato antiguo de tuplas al nuevo formato de diccionarios."""
        if not self.instruccion:
            self.instruccion = "Empareja cada concepto con su definicion"
        
        z_datos = []
        p_datos = []
        for i, (concepto, definicion) in enumerate(pares):
            id_zona = f"zona_{i}"
            z_datos.append({"id": id_zona, "etiqueta": definicion})
            p_datos.append({"nombre": concepto, "zona_destino": id_zona})
            
        self._inicializar_desde_datos(p_datos, z_datos)

    def _generar_demo(self):
        self.instruccion = "Arrastra los animales a su habitat"
        z_datos = [
            {"id": "rio", "etiqueta": "El Rio"},
            {"id": "selva", "etiqueta": "La Selva"}
        ]
        p_datos = [
            {"nombre": "Pez", "zona_destino": "rio"},
            {"nombre": "Rana", "zona_destino": "rio"},
            {"nombre": "Jaguar", "zona_destino": "selva"},
            {"nombre": "Mono", "zona_destino": "selva"}
        ]
        self._inicializar_desde_datos(p_datos, z_datos)

    def _inicializar_desde_datos(self, piezas_datos, zonas_datos):
        # Distribuir Zonas (mitad derecha o inferior)
        num_zonas = len(zonas_datos)
        espacio_y = self.alto // (num_zonas + 1)
        
        for i, z_dato in enumerate(zonas_datos):
            pos = (self.ancho - 200, espacio_y * (i + 1))
            self.zonas.append(ZonaDestino(z_dato, pos))
            
        # Distribuir Piezas (mitad izquierda)
        # Mezclar el orden visual de las piezas
        random.shuffle(piezas_datos)
        num_piezas = len(piezas_datos)
        espacio_y_p = self.alto // (num_piezas + 1)
        
        for i, p_dato in enumerate(piezas_datos):
            pos = (150, espacio_y_p * (i + 1))
            self.piezas.append(ItemPieza(p_dato, pos))

    def manejar_eventos(self, eventos):
        if self.victoria: return

        for ev in eventos:
            if (ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1) or ev.type == pygame.FINGERDOWN:
                if ev.type == pygame.FINGERDOWN:
                    pos = (ev.x * self.ancho, ev.y * self.alto)
                else:
                    pos = ev.pos
                
                # Buscar pieza bajo el ratón (empezando por la última dibujada -> z-order top)
                for pieza in reversed(self.piezas):
                    if not pieza.colocada and pieza.rect.collidepoint(pos):
                        pieza.arrastrando = True
                        pieza.retornando = False
                        pieza.offset_arrastre = pygame.Vector2(pieza.rect.center) - pygame.Vector2(pos)
                        self.pieza_arrastrada = pieza
                        gestor_audio.reproducir_sonido('clic.wav')
                        
                        # Mover la pieza al final de la lista para dibujarla encima del resto
                        self.piezas.remove(pieza)
                        self.piezas.append(pieza)
                        break

            elif (ev.type == pygame.MOUSEBUTTONUP and ev.button == 1) or ev.type == pygame.FINGERUP:
                if self.pieza_arrastrada:
                    self._verificar_soltar(self.pieza_arrastrada)
                    self.pieza_arrastrada.arrastrando = False
                    self.pieza_arrastrada = None
                    
                    # Resetear hover de zonas
                    for z in self.zonas:
                        z.hover = False

    def _verificar_soltar(self, pieza):
        zona_soltada = None
        
        # Buscar en qué zona se soltó (intersección)
        for z in self.zonas:
            if pieza.rect.colliderect(z.rect):
                zona_soltada = z
                break
                
        if zona_soltada:
            if pieza.zona_destino == zona_soltada.id:
                # Éxito: Encajar
                pieza.colocada = True
                pieza.pos_actual = pygame.Vector2(zona_soltada.rect.center)
                pieza.rect.center = pieza.pos_actual
                gestor_audio.reproducir_sonido('correcto.wav')
                
                # Comprobar victoria (todas las piezas colocadas)
                if all(p.colocada for p in self.piezas):
                    self.victoria = True
                    self.puntaje_final = max(0, self.puntaje)
            else:
                # Error: Zona incorrecta
                pieza.retornando = True
                self.puntaje -= 10
                gestor_audio.reproducir_sonido('incorrecto.wav')
        else:
            # Soltado en el aire: volver sin penalizar (o opcional penalizar, aquí no)
            pieza.retornando = True

    def actualizar(self, dt):
        self.tiempo_transcurrido += dt
        
        for p in self.piezas:
            p.actualizar(dt)
            
        # Comprobar hover de zona
        if self.pieza_arrastrada:
            for z in self.zonas:
                z.hover = self.pieza_arrastrada.rect.colliderect(z.rect)

        if self.victoria:
            self.timer_victoria += dt
            if self.timer_victoria >= 3.0:
                self.activo = False

    def dibujar(self):
        self.pantalla.fill(C_SELVA)
        
        # Decoración simple
        pygame.draw.rect(self.pantalla, C_RIO, (0, 0, self.ancho, 60))
        
        # Instrucción
        ins_surf = self.f_inst.render(self.instruccion, True, C_TEXTO)
        self.pantalla.blit(ins_surf, ins_surf.get_rect(center=(self.ancho//2, 30)))

        # Dibujar Zonas (Capa inferior)
        for z in self.zonas:
            z.dibujar(self.pantalla)

        # Dibujar Piezas (El z-order está gestionado porque al arrastrar se mueve al final de la lista)
        for p in self.piezas:
            p.dibujar(self.pantalla)

        # UI inferior
        txt_pts = self.f_info.render(f"Puntaje: {max(0, self.puntaje)}", True, C_ARENA)
        self.pantalla.blit(txt_pts, (20, self.alto - 40))

        # Victoria
        if self.victoria:
            overlay = pygame.Surface((self.ancho, self.alto), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.pantalla.blit(overlay, (0, 0))
            
            v_surf = self.f_vict.render("¡EXCELENTE!", True, C_ORO)
            self.pantalla.blit(v_surf, v_surf.get_rect(center=(self.ancho//2, self.alto//2 - 40)))
            
            p_surf = self.f_inst.render(f"Puntaje Final: {self.puntaje_final}", True, C_BLANCO)
            self.pantalla.blit(p_surf, p_surf.get_rect(center=(self.ancho//2, self.alto//2 + 30)))

def ejecutar_minijuego(piezas_datos, zonas_datos, instruccion, audio_manager=None):
    """
    Función de utilidad para ejecutar el minijuego de forma independiente.
    """
    pygame.init()
    pantalla = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Pacífico Educativo - Drag and Drop")
    reloj = pygame.time.Clock()
    
    juego = MinijuegoDragDrop(pantalla, 800, 600, 1, 'general', piezas_datos=piezas_datos, zonas_datos=zonas_datos, instruccion=instruccion)
    
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
