import pygame
import sys
from pathlib import Path
from Eventos import Evento1_Pozo
from Eventos import Evento_2
from Eventos import Evento3_Oficina
from Eventos import Mapa
import Metodos


def Ciudadano():
    """Recorrido del Sobreviviente: el mismo orden que el Presidente, con su propia ruta del mapa
    (Barrio Las Acacias -> Campo Sembrado -> Almacén del Este -> Central de Datos)."""
    pygame.init()

    fondo_original = pygame.image.load(Path(__file__).parent.parent / "Assets" / "Interfaz" / "Escritorio_Ciudadano.png")
    ancho_original, alto_original = fondo_original.get_size()
    ANCHO = 900
    ALTO = int(ANCHO * alto_original / ancho_original)

    display, canvas = Metodos.crear_ventana(ANCHO, ALTO, "My Game")

    # ---------- MAPA: ruta del Sobreviviente ----------
    mapa = Mapa.Mapa("SOBREVIVIENTE")
    Metodos.MAPA = mapa                         # el icono del mapa sale arriba a la derecha
    Mapa.mostrar_mapa(display, mapa, terminar=False)   # "Estás aquí: Barrio Las Acacias"

    # ---------- EVENTO 1: el mercado y el mensaje viral ----------
    resultado_evento1 = Evento1_Pozo.jugar(display, canvas, personaje="SOBREVIVIENTE")

    # ---------- MAPA: X en Barrio Las Acacias y se abre el camino al Campo Sembrado ----------
    Mapa.mostrar_mapa(display, mapa)

    # ---------- EVENTO 2: campo minado (el camino hacia el agua) ----------
    resultado_evento2 = Evento_2.Evento_2()

    # Evento 2 pone pantalla completa: volvemos a la ventana normal
    display, canvas = Metodos.crear_ventana(ANCHO, ALTO, "My Game")

    # ---------- MAPA: X en el Campo Sembrado y se abre el camino al Almacén del Este ----------
    Mapa.mostrar_mapa(display, mapa)

    # ---------- EVENTO 3: la oficina (pistas, grafo social y el final) ----------
    resultado_evento3 = Evento3_Oficina.jugar(display, canvas,
                                              resultado_evento1["indicadores"],
                                              resultado_evento1["resultado"],
                                              "CIUDADANO")
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
