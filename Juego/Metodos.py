

import pygame
import sys
import cv2
from pathlib import Path


def boton(display, rect, texto, mouse_pos, click):
    color_normal = (70, 130, 180)
    color_hover = (100, 160, 210)

    color_actual = color_hover if rect.collidepoint(mouse_pos) else color_normal
    pygame.draw.rect(display, color_actual, rect, border_radius=8)

    fuente = pygame.font.SysFont(None, 32)
    texto_render = fuente.render(texto, True, (255, 255, 255))
    texto_rect = texto_render.get_rect(center=rect.center)
    display.blit(texto_render, texto_rect)

    return rect.collidepoint(mouse_pos) and click 

def crear_ventana(ancho_logico, alto_logico, titulo="My Game"):
    display = pygame.display.set_mode((ancho_logico, alto_logico), pygame.RESIZABLE)
    pygame.display.set_caption(titulo)
    canvas = pygame.Surface((ancho_logico, alto_logico))
    return display, canvas


def mostrar_canvas(display, canvas):
    ancho_ventana, alto_ventana = display.get_size()
    ancho_canvas, alto_canvas = canvas.get_size()

    escala = min(ancho_ventana / ancho_canvas, alto_ventana / alto_canvas)
    nuevo_ancho = int(ancho_canvas * escala)
    nuevo_alto = int(alto_canvas * escala)

    canvas_escalado = pygame.transform.smoothscale(canvas, (nuevo_ancho, nuevo_alto))

    offset_x = (ancho_ventana - nuevo_ancho) // 2
    offset_y = (alto_ventana - nuevo_alto) // 2

    display.fill((0, 0, 0))
    display.blit(canvas_escalado, (offset_x, offset_y))

    return escala, offset_x, offset_y


def mouse_en_canvas(escala, offset_x, offset_y):
    x, y = pygame.mouse.get_pos()
    if escala == 0:
        return (-1, -1)
    return ((x - offset_x) / escala, (y - offset_y) / escala)


def reproducir_video(display, canvas, ruta):
    video = cv2.VideoCapture(str(ruta))
    fps = video.get(cv2.CAP_PROP_FPS) or 30
    reloj = pygame.time.Clock()
    ancho_canvas, alto_canvas = canvas.get_size()

    # NUEVO: si hay un .mp3 con el mismo nombre, lo reproduce
    ruta_audio = Path(ruta).with_suffix(".mp3")
    if ruta_audio.exists():
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        pygame.mixer.music.load(str(ruta_audio))
        pygame.mixer.music.play()

    # NUEVO: para mantener video y audio sincronizados
    inicio = pygame.time.get_ticks()
    cuadro_actual = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                video.release()
                pygame.quit()
                sys.exit()
            if event.type == pygame.VIDEORESIZE:
                display = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_ESCAPE):
                video.release()
                pygame.mixer.music.stop()  # NUEVO
                return

        # NUEVO: calcula en qué cuadro debería ir según el tiempo
        cuadro_objetivo = int((pygame.time.get_ticks() - inicio) / 1000 * fps)
        ok, cuadro = video.read()
        cuadro_actual += 1
        while ok and cuadro_actual < cuadro_objetivo:
            ok, cuadro = video.read()
            cuadro_actual += 1

        if not ok:
            break

        cuadro = cv2.cvtColor(cuadro, cv2.COLOR_BGR2RGB)
        alto_v, ancho_v = cuadro.shape[:2]
        escala = min(ancho_canvas / ancho_v, alto_canvas / alto_v)
        nuevo_ancho, nuevo_alto = int(ancho_v * escala), int(alto_v * escala)
        cuadro = cv2.resize(cuadro, (nuevo_ancho, nuevo_alto))
        imagen = pygame.image.frombuffer(cuadro.tobytes(), (nuevo_ancho, nuevo_alto), "RGB")

        canvas.fill((0, 0, 0))
        canvas.blit(imagen, ((ancho_canvas - nuevo_ancho) // 2, (alto_canvas - nuevo_alto) // 2))
        mostrar_canvas(display, canvas)
        pygame.display.update()
        reloj.tick(fps)

    video.release()
    pygame.mixer.music.stop()  # NUEVO