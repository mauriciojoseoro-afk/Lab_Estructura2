import pygame
import sys
import cv2


from pathlib import Path
import Metodos
import Historia
pygame.init()

ANCHO = 900
ALTO = 600  

display = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("My Game")

ruta_video = Path(__file__).parent / "Assets" / "Interfaz" / "Juego.mp4"
video = cv2.VideoCapture(str(ruta_video))

fps_video = video.get(cv2.CAP_PROP_FPS) or 30  
reloj = pygame.time.Clock()


def siguiente_frame(video, ancho, alto):
    ret, frame = video.read()

    if not ret:
        video.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ret, frame = video.read()

    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = cv2.resize(frame, (ancho, alto))
    frame = frame.swapaxes(0, 1)  

    return pygame.surfarray.make_surface(frame)


boton_jugar = pygame.Rect(180, 270, 220, 60)
boton_salir = pygame.Rect(180, 450, 230, 50)

running = True
while running:
    mouse_pos = pygame.mouse.get_pos()
    click = False

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            click = True

    fondo = siguiente_frame(video, ANCHO, ALTO)
    display.blit(fondo, (0, 0))

    if Metodos.boton_inv(display, boton_jugar, mouse_pos, click):
        Historia.Historia()

    if Metodos.boton_inv(display, boton_salir, mouse_pos, click):
        pygame.quit()
        sys.exit()

    pygame.display.update()
    reloj.tick(fps_video)  

video.release()
pygame.quit()