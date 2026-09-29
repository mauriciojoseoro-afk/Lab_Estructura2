import pygame
from pathlib import Path
import sys
import cv2

from Intz_Personaje import Intz_Ciudadano, Intz_Influencer, Intz_Periodista, Intz_Presidente
import Metodos

def SeleccionarPJ():
    pygame.init()

    ruta_video = Path(__file__).parent.parent / "Assets" / "Interfaz" / "Elegir_PJ.mp4"
    video = cv2.VideoCapture(str(ruta_video))

    ancho_original = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    alto_original = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps_video = video.get(cv2.CAP_PROP_FPS) or 30

    ANCHO = 900
    ALTO = int(ANCHO * alto_original / ancho_original)

    display, canvas = Metodos.crear_ventana(ANCHO, ALTO, "My Game")
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

    # Botones de roles (x, y, ancho, alto)
    boton_presidente = pygame.Rect(100, 250, 300, 90)
    boton_ciudadano = pygame.Rect(520, 250, 300, 90)
    boton_periodista = pygame.Rect(100, 450, 300, 90)
    boton_influencer = pygame.Rect(520, 450, 300, 90)
    boton_salir = pygame.Rect(20, 100, 100, 60)

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

        fondo = siguiente_frame(video, ANCHO, ALTO)
        canvas.blit(fondo, (0, 0))

        # Se llama a la funcion
        if Metodos.boton_inv(canvas, boton_presidente, mouse_pos, click):
            video.release()
            genero = Metodos.ElegirGenero("Presidente")
            if genero in ["Masculino", "Femenino"]:
                Intz_Presidente.Presidente()
                running = False
            else:
                return SeleccionarPJ()

        if Metodos.boton_inv(canvas, boton_ciudadano, mouse_pos, click):
            video.release()
            genero = Metodos.ElegirGenero("Ciudadano")
            if genero in ["Masculino", "Femenino"]:
                Intz_Ciudadano.Ciudadano()
                running = False
            else:
                return SeleccionarPJ()

        if Metodos.boton_inv(canvas, boton_periodista, mouse_pos, click):
            video.release()
            genero = Metodos.ElegirGenero("Periodista")
            if genero in ["Masculino", "Femenino"]:
                Intz_Periodista.Periodista()
                running = False
            else:
                return SeleccionarPJ()

        if Metodos.boton_inv(canvas, boton_influencer, mouse_pos, click):
            video.release()
            genero = Metodos.ElegirGenero("Influencer")
            if genero in ["Masculino", "Femenino"]:
                # Reproduce el video cinematográfico antes de entrar al influencer según su género
                if genero == "Masculino":
                    Metodos.ReproducirVideo("Video_Influencer_M.mp4")
                else:
                    Metodos.ReproducirVideo("Video_Influencer_F.mp4")
                
                Intz_Influencer.Influencer(genero)
                running = False
            else:
                return SeleccionarPJ()

        if Metodos.boton_inv(canvas, boton_salir, mouse_pos, click):
            video.release()
            pygame.quit()
            sys.exit()

        Metodos.mostrar_canvas(display, canvas)
        pygame.display.update()
        reloj.tick(fps_video)  

    video.release()
    pygame.quit()