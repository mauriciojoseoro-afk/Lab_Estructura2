

import pygame


def boton(display, rect, texto, mouse_pos, click):
    color_normal = (70, 130, 180)
    color_hover = (100, 160, 210)

    color_actual = color_hover if rect.collidepoint(mouse_pos) else color_normal
    pygame.draw.rect(display, color_actual, rect, border_radius=8)

    fuente = pygame.font.SysFont(None, 32)
    texto_render = fuente.render(texto, True, (255, 255, 255))
    texto_rect = texto_render.get_rect(center=rect.center)
    display.blit(texto_render, texto_rect)

    return rect.collidepoint(mouse_pos) and click 

def crear_ventana(ancho_logico, alto_logico, titulo="My Game"):
    display = pygame.display.set_mode((ancho_logico, alto_logico), pygame.RESIZABLE)
    pygame.display.set_caption(titulo)
    canvas = pygame.Surface((ancho_logico, alto_logico))
    return display, canvas


def mostrar_canvas(display, canvas):
    ancho_ventana, alto_ventana = display.get_size()
    ancho_canvas, alto_canvas = canvas.get_size()

    escala = min(ancho_ventana / ancho_canvas, alto_ventana / alto_canvas)
    nuevo_ancho = int(ancho_canvas * escala)
    nuevo_alto = int(alto_canvas * escala)

    canvas_escalado = pygame.transform.smoothscale(canvas, (nuevo_ancho, nuevo_alto))

    offset_x = (ancho_ventana - nuevo_ancho) // 2
    offset_y = (alto_ventana - nuevo_alto) // 2

    display.fill((0, 0, 0))
    display.blit(canvas_escalado, (offset_x, offset_y))

    return escala, offset_x, offset_y


def mouse_en_canvas(escala, offset_x, offset_y):
    x, y = pygame.mouse.get_pos()
    if escala == 0:
        return (-1, -1)
    return ((x - offset_x) / escala, (y - offset_y) / escala)