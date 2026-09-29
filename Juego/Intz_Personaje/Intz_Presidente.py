import pygame
import sys
from pathlib import Path
from Eventos import Periodista_Presidente
import Metodos


def Presidente():
    pygame.init()

    fondo_original = pygame.image.load(Path(__file__).parent.parent / "Assets" / "Interfaz" / "Escritorio_Presidente.png")
    ancho_original, alto_original = fondo_original.get_size()
    ANCHO = 900
    ALTO = int(ANCHO * alto_original / ancho_original)

    display, canvas = Metodos.crear_ventana(ANCHO, ALTO, "My Game")
    ruta_video = Path(__file__).parent.parent / "Assets" / "Videos" / "escena1_llegada.mp4"
    Metodos.reproducir_video(display, canvas, ruta_video)
    fondo = pygame.transform.smoothscale(fondo_original.convert(), (ANCHO, ALTO))

    boton_primer_evento = pygame.Rect(int(ANCHO * 0.38), int(ALTO * 0.85), int(ANCHO * 0.24), int(ALTO * 0.08))

    running = True
    while running:
        click = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.VIDEORESIZE:
                display = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                click = True

        ancho_ventana, alto_ventana = display.get_size()
        escala = min(ancho_ventana / ANCHO, alto_ventana / ALTO)
        offset_x = (ancho_ventana - int(ANCHO * escala)) // 2
        offset_y = (alto_ventana - int(ALTO * escala)) // 2
        mouse_pos = Metodos.mouse_en_canvas(escala, offset_x, offset_y)

        canvas.blit(fondo, (0, 0))

        if Metodos.boton(canvas, boton_primer_evento, "Primer Evento", mouse_pos, click):
            Periodista_Presidente.Entrevista()

        Metodos.mostrar_canvas(display, canvas)
        pygame.display.update()