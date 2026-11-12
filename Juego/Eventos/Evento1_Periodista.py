# -*- coding: utf-8 -*-
"""The Leader - Evento 1 Periodista.

Reproduce el video original y lo pausa en sus cuatro preguntas.
Solo permite seleccionar A/B/C/D haciendo clic sobre las respuestas del video.
No introduce puntuaciones, consecuencias ni interfaces nuevas.
"""
from pathlib import Path
import sys
import cv2
import pygame

# Momentos donde todas las opciones ya están escritas en el video.
# Se usan fotogramas del propio archivo, no un reloj que siga corriendo en pausa.
PAUSAS_SEGUNDOS = (17.0, 35.0, 53.0, 72.0)

# Coordenadas sobre una referencia de 831 x 623 (misma proporción que el video).
REF_W, REF_H = 831, 623
ZONAS = (
    ((75, 265, 685, 60), (75, 325, 685, 78), (75, 403, 685, 55), (75, 458, 685, 60)),
    ((162, 277, 560, 46), (162, 329, 560, 46), (162, 380, 560, 46), (162, 430, 560, 48)),
    ((105, 307, 635, 45), (105, 359, 635, 45), (105, 408, 635, 48), (105, 459, 635, 46)),
    ((105, 260, 635, 67), (105, 338, 635, 68), (105, 415, 635, 67), (105, 486, 635, 47)),
)


def ruta_video():
    carpeta_eventos = Path(__file__).resolve().parent
    juego = carpeta_eventos.parent if carpeta_eventos.name.lower() == 'eventos' else carpeta_eventos
    candidatos = (
        juego / 'Assets' / 'Videos' / 'Evento1 periodista.mp4',
        juego / 'Assets' / 'Interfaz' / 'Evento1 periodista.mp4',
        carpeta_eventos / 'Evento1 periodista.mp4',
    )
    for ruta in candidatos:
        if ruta.is_file():
            return ruta
    raise FileNotFoundError('No encuentro Evento1 periodista.mp4. Colócalo en Juego/Assets/Videos/')


def rect_video(pantalla, ancho, alto):
    w, h = pantalla.get_size()
    escala = min(w / ancho, h / alto)
    rw, rh = max(1, round(ancho * escala)), max(1, round(alto * escala))
    return pygame.Rect((w - rw) // 2, (h - rh) // 2, rw, rh)


def opcion_en_posicion(pos, rect, pregunta):
    """Convierte clic físico a coordenadas del video, incluidas bandas negras."""
    if not rect.collidepoint(pos):
        return None
    x = (pos[0] - rect.x) * REF_W / rect.w
    y = (pos[1] - rect.y) * REF_H / rect.h
    for indice, (zx, zy, zw, zh) in enumerate(ZONAS[pregunta]):
        if zx <= x <= zx + zw and zy <= y <= zy + zh:
            return 'ABCD'[indice]
    return None


def Evento1Periodista():
    pygame.init()
    ruta = ruta_video()
    cap = cv2.VideoCapture(str(ruta))
    if not cap.isOpened():
        raise RuntimeError(f'No se pudo abrir el video: {ruta}')

    vw = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    vh = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = float(cap.get(cv2.CAP_PROP_FPS))
    if vw <= 0 or vh <= 0 or fps <= 0:
        cap.release()
        raise RuntimeError('El video no tiene dimensiones o FPS válidos')

    pantalla = pygame.display.get_surface()
    if pantalla is None:
        pantalla = pygame.display.set_mode((900, 675), pygame.RESIZABLE)
    pygame.display.set_caption('The Leader | Evento 1 - Periodista')

    # Leer hasta el fotograma exacto de cada pregunta, evitando saltársela.
    frames_pausa = [round(seg * fps) for seg in PAUSAS_SEGUNDOS]
    numero_frame = 0
    indice_pregunta = 0
    pausado = False
    selecciones = []
    ultimo_bgr = None
    ultimo_rgb = None
    superficie_escalada = None
    tam_escalado = None
    reloj = pygame.time.Clock()
    acumulado = 0.0

    # Audio opcional separado. No se exige para que el evento funcione.
    audio = ruta.with_name('Evento1 periodista_audio.mp3')
    reproduciendo_audio = False
    if audio.is_file():
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pygame.mixer.music.load(str(audio))
            pygame.mixer.music.play()
            reproduciendo_audio = True
        except pygame.error as exc:
            print('[Periodista] Audio no disponible:', exc)

    print('[Periodista] Iniciado. Pausas:', PAUSAS_SEGUNDOS)
    try:
        activo = True
        while activo:
            dt = min(reloj.tick(60) / 1000.0, 0.1)
            pantalla = pygame.display.get_surface()
            if pantalla is None:
                break
            rect = rect_video(pantalla, vw, vh)

            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    activo = False
                    break
                if evento.type == pygame.VIDEORESIZE:
                    pantalla = pygame.display.set_mode((max(320, evento.w), max(240, evento.h)), pygame.RESIZABLE)
                    rect = rect_video(pantalla, vw, vh)
                    tam_escalado = None
                if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1 and pausado:
                    opcion = opcion_en_posicion(evento.pos, rect, indice_pregunta)
                    print('[Periodista] Clic:', evento.pos, 'respuesta:', opcion)
                    if opcion is not None:
                        selecciones.append(opcion)
                        print(f'[Periodista] Pregunta {indice_pregunta + 1}: {opcion}')
                        indice_pregunta += 1
                        pausado = False
                        acumulado = 0.0
                        if reproduciendo_audio:
                            pygame.mixer.music.unpause()
            if not activo:
                break

            if not pausado:
                acumulado += dt
                cantidad = min(int(acumulado * fps), 6)
                if cantidad:
                    acumulado -= cantidad / fps
                for _ in range(cantidad):
                    ok, bgr = cap.read()
                    if not ok:
                        activo = False
                        break
                    numero_frame += 1
                    ultimo_bgr = bgr
                    ultimo_rgb = None
                    if indice_pregunta < len(frames_pausa) and numero_frame >= frames_pausa[indice_pregunta]:
                        pausado = True
                        acumulado = 0.0
                        if reproduciendo_audio:
                            pygame.mixer.music.pause()
                        print(f'[Periodista] PAUSA {indice_pregunta + 1} ({numero_frame / fps:.2f}s)')
                        break

            if ultimo_bgr is not None:
                if ultimo_rgb is None:
                    rgb = cv2.cvtColor(ultimo_bgr, cv2.COLOR_BGR2RGB)
                    ultimo_rgb = pygame.image.frombuffer(rgb.tobytes(), (vw, vh), 'RGB').copy()
                    tam_escalado = None
                if tam_escalado != rect.size:
                    superficie_escalada = (ultimo_rgb if rect.size == (vw, vh)
                                          else pygame.transform.smoothscale(ultimo_rgb, rect.size))
                    tam_escalado = rect.size
                pantalla.fill((0, 0, 0))
                pantalla.blit(superficie_escalada, rect.topleft)
                pygame.display.flip()

            if pausado:
                sobre = opcion_en_posicion(pygame.mouse.get_pos(), rect, indice_pregunta)
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND if sobre else pygame.SYSTEM_CURSOR_ARROW)
            else:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
    finally:
        cap.release()
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
        if reproduciendo_audio:
            pygame.mixer.music.stop()

    return selecciones


def Periodista():
    return Evento1Periodista()


if __name__ == '__main__':
    print('Selecciones:', Evento1Periodista())
