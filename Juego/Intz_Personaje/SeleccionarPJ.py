import pygame
from pathlib import Path


from Intz_Personaje import Intz_Ciudadano
from Intz_Personaje import Intz_Influencer, Intz_Periodista, Intz_Presidente
import Metodos

def SeleccionarPJ():
    pygame.init()

    display = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("My Game")

    fondo = pygame.image.load(Path(__file__).parent.parent / "Assets" / "Interfaz" / "Elegir_PJ.png").convert()

    # posiciones distintas para cada botón
    boton_presidente = pygame.Rect(40, 500, 150, 60)
    boton_ciudadano = pygame.Rect(640, 500, 150, 60)
    boton_periodista = pygame.Rect(240, 500, 150, 60)
    boton_influencer = pygame.Rect(440, 500, 150, 60)
   

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        click = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                click = True

        display.blit(fondo, (0, 0))

        if Metodos.boton(display, boton_ciudadano, "Ciudadano", mouse_pos, click):
            
            Intz_Ciudadano.Ciudadano()   
            running = False

        if Metodos.boton(display, boton_presidente, "Presidente", mouse_pos, click):
            Intz_Presidente.Presidente()
            running = False

        if Metodos.boton(display, boton_periodista, "Periodista", mouse_pos, click):
            Intz_Periodista.Periodista()
            running = False

        if Metodos.boton(display, boton_influencer, "Influencer", mouse_pos, click):
            Intz_Influencer.Influencer()
            running = False

        pygame.display.update()

    pygame.quit()