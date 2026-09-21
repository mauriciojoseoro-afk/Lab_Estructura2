import pygame
import sys
from pathlib import Path


def Periodista():
    pygame.init()

    fondo_original = pygame.image.load(Path(__file__).parent.parent / "Assets" / "Interfaz" / "Escritorio_Periodista.png")
    ancho_original, alto_original = fondo_original.get_size()
    ANCHO = 900
    ALTO = int(ANCHO * alto_original / ancho_original)

    display = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption("My Game")

    fondo = pygame.transform.smoothscale(fondo_original.convert(), (ANCHO, ALTO))

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        display.blit(fondo, (0, 0))

        pygame.display.update()