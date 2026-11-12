# -*- coding: utf-8 -*-
"""Selector de roles de The Leader con ilustraciones originales.

Clic en expediente: muestra su ficha y pregunta si desea elegirlo.
Confirmar entra al rol; Elegir otro regresa al tablero.
"""
import sys
from pathlib import Path
import pygame
import Metodos
from Intz_Personaje import Intz_Ciudadano, Intz_Influencer, Intz_Periodista, Intz_Presidente
from Red import cliente      # multijugador: bloqueo de roles (si no hay servidor, se juega solo)

ANCHO, ALTO = 800, 600
IMAGENES = Path(__file__).resolve().parent.parent / 'Assets' / 'Interfaz' / 'SeleccionNovia'
# Orden exacto de los expedientes en 3.png (de izquierda a derecha).
ROLES = [
    ('PERIODISTA', '11.png', pygame.Rect(78, 163, 159, 241)),
    ('INFLUENCER', '8.png', pygame.Rect(246, 163, 159, 241)),
    ('CIUDADANO', '12.png', pygame.Rect(414, 163, 159, 241)),
    ('PRESIDENTE', '15.png', pygame.Rect(582, 163, 159, 241)),
]
# Pequeña barra en la esquina inferior derecha de la ficha.
# La información del personaje termina por encima de esta zona.
PANEL = pygame.Rect(512, 533, 276, 59)
CONFIRMAR = pygame.Rect(522, 555, 126, 31)
OTRO = pygame.Rect(655, 555, 126, 31)
REGRESAR_TABLERO = pygame.Rect(5, 533, 108, 47)


def dibujar_brillo(canvas, area, tiempo):
    """Halo cálido ajustado al expediente bajo el cursor, sin moverlo."""
    import math
    intensidad = 0.72 + 0.28 * math.sin(tiempo * 4)
    halo = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    for grosor, alpha, margen in ((14, 13, 11), (9, 27, 7), (5, 55, 4)):
        pygame.draw.rect(halo, (255, 190, 91, int(alpha * (1 + intensidad))),
                         area.inflate(margen * 2, margen * 2), grosor,
                         border_radius=6)
    canvas.blit(halo, (0, 0))
    pygame.draw.rect(canvas, (255, 218, 135), area, 3, border_radius=4)
    # Esquinas metálicas del expediente, alineadas con su contorno.
    for x, sx in ((area.left, 1), (area.right, -1)):
        for y, sy in ((area.top, 1), (area.bottom, -1)):
            pygame.draw.line(canvas, (255, 237, 175), (x, y), (x + sx * 17, y), 3)
            pygame.draw.line(canvas, (255, 237, 175), (x, y), (x, y + sy * 17), 3)


def posicion_en_canvas(display, pos):
    """Convierte coordenadas de ventana a 800x600, respetando bandas negras."""
    w, h = display.get_size()
    escala = min(w / ANCHO, h / ALTO)
    ox, oy = (w - ANCHO * escala) / 2, (h - ALTO * escala) / 2
    return ((pos[0] - ox) / escala, (pos[1] - oy) / escala)


def dibujar_ocupado(canvas, area, quien, fuente_sello, fuente_nombre):
    """Expediente ya elegido por otro jugador: oscuro, con sello EN USO y su nombre."""
    velo = pygame.Surface(area.size, pygame.SRCALPHA)
    velo.fill((12, 10, 9, 170))
    canvas.blit(velo, area.topleft)
    sello = fuente_sello.render('EN USO', True, (205, 52, 44))
    caja = pygame.Surface((sello.get_width() + 16, sello.get_height() + 6), pygame.SRCALPHA)
    pygame.draw.rect(caja, (205, 52, 44), caja.get_rect(), 3, border_radius=4)
    caja.blit(sello, (8, 3))
    caja = pygame.transform.rotate(caja, 14)
    canvas.blit(caja, caja.get_rect(center=(area.centerx, area.centery - 20)))
    texto = fuente_nombre.render(quien, True, (240, 225, 200))
    canvas.blit(texto, texto.get_rect(center=(area.centerx, area.centery + 32)))


def dibujar_aviso(canvas, mensaje, fuente):
    """Mensaje corto en la parte de abajo (rol ocupado, etc.)."""
    texto = fuente.render(mensaje, True, (250, 226, 190))
    fondo = pygame.Rect(0, 0, texto.get_width() + 30, texto.get_height() + 14)
    fondo.center = (ANCHO // 2, 470)
    capa = pygame.Surface(fondo.size, pygame.SRCALPHA)
    capa.fill((25, 12, 10, 230))
    canvas.blit(capa, fondo.topleft)
    pygame.draw.rect(canvas, (205, 52, 44), fondo, 2, border_radius=4)
    canvas.blit(texto, texto.get_rect(center=fondo.center))


def abrir_rol(nombre):
    if nombre == 'PRESIDENTE':
        return Intz_Presidente.Presidente()
    if nombre == 'CIUDADANO':
        return Intz_Ciudadano.Ciudadano()
    if nombre == 'PERIODISTA':
        return Intz_Periodista.Periodista()
    # Mantener la cinemática original de la influencer y su género.
    Metodos.ReproducirVideo('Video_Influencer_F.mp4')
    Intz_Influencer.Influencer('Femenino')
    return SeleccionarPJ()


def SeleccionarPJ():
    pygame.init()
    display, canvas = Metodos.crear_ventana(ANCHO, ALTO, 'The Leader')
    reloj = pygame.time.Clock()
    imagenes = {}
    for nombre in ['3.png'] + [r[1] for r in ROLES]:
        ruta = IMAGENES / nombre
        if not ruta.is_file():
            raise FileNotFoundError(f'Falta la imagen de selección: {ruta}')
        imagenes[nombre] = pygame.image.load(str(ruta)).convert()
        if imagenes[nombre].get_size() != (ANCHO, ALTO):
            imagenes[nombre] = pygame.transform.smoothscale(imagenes[nombre], (ANCHO, ALTO))

    # ---- MULTIJUGADOR: conexión con el servidor (None = modo un jugador) ----
    red = cliente.conectar()
    if red is not None:
        red.soltar()                  # al volver a esta pantalla, el rol anterior queda libre
    fuente_sello = pygame.font.SysFont('timesnewroman', 26, bold=True)
    fuente_estado = pygame.font.SysFont('timesnewroman', 13, bold=True)
    aviso, aviso_hasta = None, 0.0

    def ocupado(rol):
        return red.ocupado_por_otro(rol) if red is not None else None

    seleccionado = None
    fuente_pregunta = pygame.font.SysFont('timesnewroman', 14, bold=True)
    fuente_boton = pygame.font.SysFont('timesnewroman', 15, bold=True)
    tiempo = 0.0

    def dibujar_pregunta(indice):
        # Barra mínima, sobre la madera inferior derecha y NO sobre la biografía.
        capa = pygame.Surface(PANEL.size, pygame.SRCALPHA)
        capa.fill((23, 19, 18, 239))
        pygame.draw.rect(capa, (173, 125, 77), capa.get_rect(), 2,
                         border_radius=5)
        canvas.blit(capa, PANEL.topleft)
        mensaje = '¿Elegir a ' + ROLES[indice][0].title() + '?'
        titulo = fuente_pregunta.render(mensaje, True, (245, 220, 179))
        canvas.blit(titulo, titulo.get_rect(center=(PANEL.centerx, PANEL.y + 12)))
        mouse = posicion_en_canvas(display, pygame.mouse.get_pos())
        for rect, titulo in ((CONFIRMAR, 'CONFIRMAR'), (OTRO, 'ELEGIR OTRO')):
            hover = rect.collidepoint(mouse)
            pygame.draw.rect(canvas, (112, 62, 43) if hover else (56, 44, 37),
                             rect, border_radius=4)
            pygame.draw.rect(canvas, (246, 199, 122) if hover else (150, 109, 72),
                             rect, 2, border_radius=4)
            label = fuente_boton.render(titulo, True, (249, 225, 189))
            canvas.blit(label, label.get_rect(center=rect.center))

    while True:
        tiempo += min(reloj.tick(60) / 1000.0, 0.1)
        accion = None
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if evento.type == pygame.VIDEORESIZE:
                display = pygame.display.set_mode(
                    (max(320, evento.w), max(240, evento.h)), pygame.RESIZABLE)
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    if seleccionado is not None:
                        seleccionado = None
                    else:
                        pygame.quit()
                        sys.exit()
                elif evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if seleccionado is not None:
                        accion = seleccionado
                elif evento.key == pygame.K_BACKSPACE:
                    seleccionado = None
            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                punto = posicion_en_canvas(display, evento.pos)
                if seleccionado is None:
                    # Solo el clic (no hover) abre la ficha de detalles.
                    for i, (rol, _, area) in enumerate(ROLES):
                        if area.collidepoint(punto):
                            quien = ocupado(rol)
                            if quien:
                                aviso, aviso_hasta = f'{rol.title()} ya lo eligió {quien}', tiempo + 2.5
                            else:
                                seleccionado = i
                            break
                    # La flecha inferior izquierda del tablero original:
                    # se conserva su comportamiento de salida.
                    if seleccionado is None and REGRESAR_TABLERO.collidepoint(punto):
                        pygame.quit()
                        sys.exit()
                else:
                    if CONFIRMAR.collidepoint(punto):
                        accion = seleccionado
                    elif OTRO.collidepoint(punto):
                        seleccionado = None
                    # Los demás clics sobre la ficha no hacen nada.
        if accion is not None:
            rol = ROLES[accion][0]
            if red is not None and red.conectado:
                ok, quien = red.elegir(rol)       # el servidor decide: el primero que lo pide se lo queda
                if not ok:
                    aviso, aviso_hasta = f'{rol.title()} ya lo eligió {quien}', tiempo + 2.5
                    seleccionado = None
                    accion = None
            if accion is not None:
                return abrir_rol(rol)
        archivo = '3.png' if seleccionado is None else ROLES[seleccionado][1]
        canvas.blit(imagenes[archivo], (0, 0))
        if seleccionado is None:
            mouse = posicion_en_canvas(display, pygame.mouse.get_pos())
            for rol, _, area in ROLES:
                quien = ocupado(rol)
                if quien:
                    dibujar_ocupado(canvas, area, quien, fuente_sello, fuente_pregunta)
                elif area.collidepoint(mouse):
                    dibujar_brillo(canvas, area, tiempo)
        else:
            dibujar_pregunta(seleccionado)
        if aviso and tiempo < aviso_hasta:
            dibujar_aviso(canvas, aviso, fuente_boton)
        if red is not None:
            estado = 'EN LÍNEA' if red.conectado else 'SIN CONEXIÓN'
            color = (120, 220, 130) if red.conectado else (220, 90, 80)
            canvas.blit(fuente_estado.render('● MULTIJUGADOR · ' + estado, True, color), (ANCHO - 215, 8))
        Metodos.mostrar_canvas(display, canvas)
        pygame.display.flip()
