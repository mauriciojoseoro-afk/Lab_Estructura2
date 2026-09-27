import pygame
from pathlib import Path
import sys


from Intz_Personaje import Intz_Ciudadano
from Intz_Personaje import Intz_Influencer, Intz_Periodista, Intz_Presidente
import Metodos

def SeleccionarPJ():
    pygame.init()

    fondo_original = pygame.image.load(Path(__file__).parent.parent / "Assets" / "Interfaz" / "Elegir_PJ.png")
    ancho_original, alto_original = fondo_original.get_size()
    ANCHO = 900
    ALTO = int(ANCHO * alto_original / ancho_original)

    display, canvas = Metodos.crear_ventana(ANCHO, ALTO, "My Game")

    fondo = pygame.transform.smoothscale(fondo_original.convert(), (ANCHO, ALTO))

    # posiciones distintas para cada botón
    tarjeta_ancho = int(ANCHO * 0.19)
    tarjeta_alto = int(ALTO * 0.42)
    y_tarjetas = int(ALTO * 0.32)

    boton_ciudadano = pygame.Rect(int(ANCHO * 0.11), y_tarjetas, tarjeta_ancho, tarjeta_alto)
    boton_periodista = pygame.Rect(int(ANCHO * 0.32), y_tarjetas, tarjeta_ancho, tarjeta_alto)
    boton_influencer = pygame.Rect(int(ANCHO * 0.53), y_tarjetas, tarjeta_ancho, tarjeta_alto)
    boton_presidente = pygame.Rect(int(ANCHO * 0.74), y_tarjetas, tarjeta_ancho, tarjeta_alto)
    tamano_salir = int(ANCHO * 0.08)
    boton_salir = pygame.Rect(int(ANCHO * 0.04), int(ANCHO * 0.05), tamano_salir, tamano_salir)

    running = True
    while running:
        click = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.VIDEORESIZE:
                display = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                click = True

        ancho_ventana, alto_ventana = display.get_size()
        escala = min(ancho_ventana / ANCHO, alto_ventana / ALTO)
        offset_x = (ancho_ventana - int(ANCHO * escala)) // 2
        offset_y = (alto_ventana - int(ALTO * escala)) // 2
        mouse_pos = Metodos.mouse_en_canvas(escala, offset_x, offset_y)

        if click and boton_salir.collidepoint(mouse_pos):
            pygame.quit()
            sys.exit()

        canvas.blit(fondo, (0, 0))

        if click and boton_ciudadano.collidepoint(mouse_pos):
            Intz_Ciudadano.Ciudadano()
            running = False

        if click and boton_presidente.collidepoint(mouse_pos):
            Intz_Presidente.Presidente()
            running = False

        if click and boton_periodista.collidepoint(mouse_pos):
            Intz_Periodista.Periodista()
            running = False

        if click and boton_influencer.collidepoint(mouse_pos):
            Intz_Influencer.Influencer()
            running = False

        Metodos.mostrar_canvas(display, canvas)
        pygame.display.update()

    pygame.quit()