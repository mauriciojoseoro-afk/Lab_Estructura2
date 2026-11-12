# -*- coding: utf-8 -*-
"""Secuencia de misiones común a los cuatro protagonistas."""
from pathlib import Path
import pygame
import Metodos
from Eventos import Mapa, Evento_2, Periodista_Presidente, Evento3_Oficina, Evento1_Pozo
from Eventos.Evento1_Pozo import Indicadores
from Red import cliente      # multijugador: avisa al grupo al terminar cada evento

BASE = Path(__file__).resolve().parent.parent
INTRO_MINAS = BASE / "Assets" / "Videos" / "minas_intro.mp4"
PERSONAJES = {
    "PRESIDENTE": ("LÍDER", "LÍDER"),
    "CIUDADANO": ("SOBREVIVIENTE", "CIUDADANO"),
    "PERIODISTA": ("CRONISTA", "PERIODISTA"),
    "INFLUENCER": ("VOZ", "INFLUENCER"),
}

def cinematica_minas():
    # No sustituir por escena1_llegada.mp4: ese video es del POZO.
    # Si existe la cinemática específica, reproducirla una vez.
    if INTRO_MINAS.is_file():
        import cv2
        cap = cv2.VideoCapture(str(INTRO_MINAS))
        if not cap.isOpened():
            print('[Misiones] No se pudo abrir la cinematica de minas.')
            cap.release()
            return
        reloj = pygame.time.Clock()
        pantalla = pygame.display.get_surface()
        fps = cap.get(cv2.CAP_PROP_FPS)
        fps = fps if 1 <= fps <= 120 else 30
        try:
            while True:
                for e in pygame.event.get():
                    if e.type == pygame.QUIT:
                        raise SystemExit
                    if e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                        return
                    if e.type == pygame.VIDEORESIZE:
                        pantalla = pygame.display.set_mode((max(320,e.w),max(240,e.h)),pygame.RESIZABLE)
                ok, frame = cap.read()
                if not ok:
                    break
                frame=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
                h,w=frame.shape[:2]
                imagen=pygame.image.frombuffer(frame.tobytes(),(w,h),'RGB').copy()
                imagen=pygame.transform.smoothscale(imagen,pantalla.get_size())
                pantalla.blit(imagen,(0,0))
                pygame.display.flip()
                reloj.tick(fps)
        finally:
            cap.release()
    else:
        print('[Misiones] Cinemática de minas no encontrada:',INTRO_MINAS.name)

def jugar_secuencia(rol):
    if rol not in PERSONAJES:
        raise ValueError('Rol desconocido: '+str(rol))
    mapa_rol, oficina_rol = PERSONAJES[rol]
    pygame.init()
    display, canvas = Metodos.crear_ventana(900, 675, 'The Leader')
    mapa = Mapa.Mapa(mapa_rol)
    Metodos.MAPA = mapa
    try:
        # 1: primer lugar visible, sin marcar misión terminada.
        cliente.reportar("Empezando", Indicadores())
        Mapa.mostrar_mapa(display,mapa,terminar=False)
        # 1b: si el personaje tiene escena propia en el Evento 1 (hoy: SOBREVIVIENTE = el mercado),
        # se juega aquí y sus indicadores/decisión pasan a la oficina.
        resultado_evento1 = None
        if mapa_rol in Evento1_Pozo.GUIONES and mapa_rol != "LÍDER":
            resultado_evento1 = Evento1_Pozo.jugar(display, canvas, personaje=mapa_rol)
            cliente.reportar("Terminó el Evento 1", resultado_evento1["indicadores"], resultado_evento1["resultado"])
            display,canvas=Metodos.crear_ventana(900,675,'The Leader')
            Mapa.mostrar_mapa(display,mapa,terminar=True)
        cinematica_minas()
        resultado_minas = Evento_2.Evento_2(rol)
        cliente.reportar("Cruzó el campo minado")
        # Evento_2 modifica el display, por eso recreamos la ventana.
        display,canvas=Metodos.crear_ventana(900,675,'The Leader')
        Mapa.mostrar_mapa(display,mapa,terminar=True)
        # 2: entrevista. El retorno son dos puntuaciones, no indicadores del pozo.
        resultado_entrevista = Periodista_Presidente.Entrevista()
        cliente.reportar("Terminó la entrevista")
        display,canvas=Metodos.crear_ventana(900,675,'The Leader')
        Mapa.mostrar_mapa(display,mapa,terminar=True)
        # 3: oficina. El evento 1 del pozo ya no se juega, por tanto
        # no inventamos una decisión anterior: usamos indicadores neutros.
        # 'VERIFICAR_FALSO' es el valor predeterminado que requiere la oficina;
        # su dependencia narrativa del pozo sigue pendiente de rediseño.
        indicadores = Indicadores()
        decision = 'VERIFICAR_FALSO'
        if resultado_evento1 is not None:       # este personaje sí jugó su Evento 1
            indicadores = resultado_evento1["indicadores"]
            decision = resultado_evento1["resultado"]
        resultado_oficina = Evento3_Oficina.jugar(display,canvas,indicadores,
                                                  decision,oficina_rol)
        cliente.reportar("Terminó la partida", indicadores)
        return {'evento1':resultado_evento1,'minas':resultado_minas,'entrevista':resultado_entrevista,
                'oficina':resultado_oficina,'personaje':rol}
    finally:
        Metodos.MAPA = None
