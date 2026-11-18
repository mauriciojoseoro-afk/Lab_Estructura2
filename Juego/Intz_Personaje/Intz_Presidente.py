import pygame
import sys
from pathlib import Path
from Eventos import Periodista_Presidente
from Eventos import Evento1_Pozo
from Eventos import Evento_2
from Eventos import Evento3_Oficina
from Eventos import Mapa
import Metodos
from Red import cliente      # multijugador, avisa al grupo al terminar cada evento


def Presidente():
    pygame.init()

    fondo_original = pygame.image.load(Path(__file__).parent.parent / "Assets" / "Interfaz" / "Escritorio_Presidente.png")
    ancho_original, alto_original = fondo_original.get_size()
    ANCHO = 900
    ALTO = int(ANCHO * alto_original / ancho_original)

    display, canvas = Metodos.crear_ventana(ANCHO, ALTO, "The Leader")

    # mapa, se crea una sola vez, aquí vive el grafo de la ciudad
    mapa = Mapa.Mapa("LÍDER")
    Metodos.MAPA = mapa                         # desde ahora el icono del mapa sale arriba a la derecha
    Mapa.mostrar_mapa(display, mapa, terminar=False)   # "estás aquí, el cruce del pozo"

    # evento 1, el pozo
    cliente.reportar("Empezando", Evento1_Pozo.Indicadores())
    resultado_evento1 = Evento1_Pozo.jugar(display, canvas)
    cliente.reportar("Terminó el Evento 1", resultado_evento1["indicadores"], resultado_evento1["resultado"])

    # mapa, x en el cruce del pozo y se abre el camino al campo sembrado
    Mapa.mostrar_mapa(display, mapa)

    # evento 2, campo minado
    resultado_evento2 = Evento_2.Evento_2("PRESIDENTE")
    cliente.reportar("Cruzó el campo minado")

    # evento 2 pone pantalla completa, volvemos a la ventana normal
    display, canvas = Metodos.crear_ventana(ANCHO, ALTO, "The Leader")
    # mapa, x en el campo sembrado, siguiente destino el almacén del este (igual que los demás)
    Mapa.mostrar_mapa(display, mapa)
        # escena del periodista y entrevista
    Evento3_Oficina.reproducir_escena(Evento3_Oficina.ESCENA_ENTREVISTA)
    Periodista_Presidente.Entrevista("PRESIDENTE")
    cliente.reportar("Terminó la entrevista")
    display, canvas = Metodos.crear_ventana(ANCHO, ALTO, "The Leader")

    
    # mapa, x en el almacén del este y se abre el camino a la central de datos
    Mapa.mostrar_mapa(display, mapa)

    # evento 3, la oficina (pistas, grafo social y el final)
    # lo que hizo en las minas y en la entrevista también cuenta
    Evento1_Pozo.sumar_eventos(resultado_evento1["indicadores"], resultado_evento2,
                               Periodista_Presidente.ULTIMO_RESULTADO)
    resultado_evento3 = Evento3_Oficina.jugar(display, canvas,
                                              resultado_evento1["indicadores"],
                                              resultado_evento1["resultado"],
                                              "LÍDER")
    cliente.reportar("Terminó la partida", resultado_evento1["indicadores"])

    # fin, igual que los demás personajes, se vuelve al menú (antes quedaba en una pantalla de prueba
    # con un botón que repetía la entrevista)
    Metodos.MAPA = None
    return {'evento1': resultado_evento1, 'minas': resultado_evento2,
            'entrevista': Periodista_Presidente.ULTIMO_RESULTADO, 'oficina': resultado_evento3,
            'personaje': 'PRESIDENTE'}
