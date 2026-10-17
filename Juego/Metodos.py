

import pygame
from pathlib import Path
import sys
import cv2
import Metodos
from Intz_Personaje import Intz_Presidente, Intz_Ciudadano, Intz_Periodista, Intz_Influencer

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

def boton_inv(display, rect, mouse_pos, click):
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


def ElegirGenero(rol):
    ruta_video = Path(__file__).parent / "Assets" / "Interfaz" / f"Genero_{rol}.mp4"
    video = cv2.VideoCapture(str(ruta_video))

    if not video.isOpened():
        print(f"No se pudo encontrar o abrir el video: {ruta_video}")
        return None

    ancho_original = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    alto_original = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps_video = video.get(cv2.CAP_PROP_FPS) or 30

    ANCHO = 900
    ALTO = int(ANCHO * alto_original / ancho_original)

    display, canvas = crear_ventana(ANCHO, ALTO, f"Elegir Género - {rol}")
    reloj = pygame.time.Clock()

    def siguiente_frame(vid, ancho, alto):
        ret, frame = vid.read()
        if not ret or frame is None:
            vid.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = vid.read()
            if not ret or frame is None:
                return pygame.Surface((ancho, alto))
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, (ancho, alto))
        frame = frame.swapaxes(0, 1)
        return pygame.surfarray.make_surface(frame)

    boton_masculino = pygame.Rect(450, 300, 300, 220)
    boton_femenino = pygame.Rect(80, 300, 300, 220)

    genero_elegido = None
    running = True

    while running:
        click = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                video.release()
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
        mouse_pos = mouse_en_canvas(escala, offset_x, offset_y)

        fondo = siguiente_frame(video, ANCHO, ALTO)
        canvas.blit(fondo, (0, 0))

        if boton_inv(canvas, boton_masculino, mouse_pos, click):
            genero_elegido = "Masculino"
            running = False

        if boton_inv(canvas, boton_femenino, mouse_pos, click):
            genero_elegido = "Femenino"
            running = False

        mostrar_canvas(display, canvas)
        pygame.display.update()
        reloj.tick(fps_video)

    video.release()
    return genero_elegido


    def LanzarEscenaRol(rol, genero):
        if rol == "Presidente":
            Intz_Presidente.Presidente(genero)
        elif rol == "Ciudadano":
            Intz_Ciudadano.Ciudadano(genero)
        elif rol == "Periodista":
            Intz_Periodista.Periodista(genero)
        elif rol == "Influencer":
            Intz_Influencer.Influencer(genero)


def ReproducirVideo(nombre_archivo):
    ruta_video = Path(__file__).parent / "Assets" / "Interfaz" / nombre_archivo
    video = cv2.VideoCapture(str(ruta_video))

    if not video.isOpened():
        print(f" No se pudo encontrar o abrir el video: {ruta_video}")
        return

    ancho_original = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    alto_original = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps_video = video.get(cv2.CAP_PROP_FPS) or 30

    ANCHO = 900
    ALTO = int(ANCHO * alto_original / ancho_original)

    display, canvas = crear_ventana(ANCHO, ALTO, "Cinemática")
    reloj = pygame.time.Clock()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                video.release()
                pygame.quit()
                sys.exit()
            if event.type == pygame.VIDEORESIZE:
                display = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

        ret, frame = video.read()

        if not ret or frame is None:
            break

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, (ANCHO, ALTO))
        frame = frame.swapaxes(0, 1)
        fondo = pygame.surfarray.make_surface(frame)

        canvas.blit(fondo, (0, 0))

        mostrar_canvas(display, canvas)
        pygame.display.update()
        reloj.tick(fps_video)

    video.release()


def reproducir_video(display, canvas, ruta):
    video = cv2.VideoCapture(str(ruta))
    fps = video.get(cv2.CAP_PROP_FPS) or 30
    reloj = pygame.time.Clock()
    ancho_canvas, alto_canvas = canvas.get_size()

    ruta_audio = Path(ruta).with_suffix(".mp3")
    if ruta_audio.exists():
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        pygame.mixer.music.load(str(ruta_audio))
        pygame.mixer.music.play()

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
                pygame.mixer.music.stop()
                return

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
    pygame.mixer.music.stop()
