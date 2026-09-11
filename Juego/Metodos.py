

import pygame

from Intz_Personaje.Intz_Ciudadano import Ciudadano


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