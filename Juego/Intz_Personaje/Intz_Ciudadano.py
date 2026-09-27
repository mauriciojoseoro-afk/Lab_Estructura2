import pygame
import sys
from pathlib import Path
import Metodos


def Ciudadano():
    pygame.init()

    fondo_original = pygame.image.load(Path(__file__).parent.parent / "Assets" / "Interfaz" / "Escritorio_Ciudadano.png")
    ancho_original, alto_original = fondo_original.get_size()
    ANCHO = 900
    ALTO = int(ANCHO * alto_original / ancho_original)

    display, canvas = Metodos.crear_ventana(ANCHO, ALTO, "My Game")

    fondo = pygame.transform.smoothscale(fondo_original.convert(), (ANCHO, ALTO))

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.VIDEORESIZE:
                display = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

        canvas.blit(fondo, (0, 0))

        Metodos.mostrar_canvas(display, canvas)
        pygame.display.update()