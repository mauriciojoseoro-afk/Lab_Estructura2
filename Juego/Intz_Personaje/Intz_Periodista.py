import pygame
from pathlib import Path


def Periodista():
    pygame.init()

    display = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("My Game")

    fondo = pygame.image.load(Path(__file__).parent.parent / "Assets" /"Interfaz" / "Periodista.png").convert()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False


        display.blit(fondo, (0, 0))
        pygame.display.update()




    pygame.quit()