import pygame
import sys
from pathlib import Path
from Eventos import Periodista_Presidente
from Eventos import Evento1_Pozo
from Eventos import Evento_2
from Eventos import Evento3_Oficina
from Eventos import Mapa
import Metodos


def Presidente():
    pygame.init()

    fondo_original = pygame.image.load(Path(__file__).parent.parent / "Assets" / "Interfaz" / "Escritorio_Presidente.png")
    ancho_original, alto_original = fondo_original.get_size()
    ANCHO = 900
    ALTO = int(ANCHO * alto_original / ancho_original)

    display, canvas = Metodos.crear_ventana(ANCHO, ALTO, "My Game")

    # ---------- MAPA: se crea una sola vez, aquí vive el grafo de la ciudad ----------
    mapa = Mapa.Mapa("LÍDER")
    Metodos.MAPA = mapa                         # desde ahora el icono del mapa sale arriba a la derecha
    Mapa.mostrar_mapa(display, mapa, terminar=False)   # "Estás aquí: El Cruce del Pozo"

    # ---------- EVENTO 1: el pozo ----------
    resultado_evento1 = Evento1_Pozo.jugar(display, canvas)

    # ---------- MAPA: X en el Cruce del Pozo y se abre el camino al Campo Sembrado ----------
    Mapa.mostrar_mapa(display, mapa)

    # ---------- EVENTO 2: campo minado ----------
    resultado_evento2 = Evento_2.Evento_2()

    # Evento 2 pone pantalla completa: volvemos a la ventana normal
    display, canvas = Metodos.crear_ventana(ANCHO, ALTO, "My Game")
    
    # ---------- MAPA: X en el Campo Sembrado y se abre el camino al Almacén del Este ----------
    Mapa.mostrar_mapa(display, mapa)

    # EVENTO 3: la oficina (pistas, grafo social y el final) 
    resultado_evento3 = Evento3_Oficina.jugar(display, canvas,
                                              resultado_evento1["indicadores"],
                                              resultado_evento1["resultado"],
                                              "LÍDER")
    display, canvas = Metodos.crear_ventana(ANCHO, ALTO, "My Game")
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