
import pygame
import cv2
from pathlib import Path
import Metodos
from Intz_Personaje import SeleccionarPJ

escenas = {
    "escena0": {
        "imagen": "Escena0.mp4",
        "opciones": {"Continuar": "escena1"}
    },
    "escena1": {
        "imagen": "Escena1.jpg",
        "opciones": {"Continuar": "escena2"}
    },
    "escena2": {
        "imagen": "Escena2.jpg",
        "opciones": {
            "Atravesar las ruinas": "escena3",
            "Rodear la ciudad": "escena4"
        }
    },
    "escena3": {
        "imagen": "Escena3.jpg",
        "opciones": {"Continuar": "escena5"}
    },
    "escena4": {
        "imagen": "Escena4.jpg",
        "opciones": {"Continuar": "escena5"}
    },
    "escena5": {
        "imagen": "Escena5.jpg",
        "opciones": {}
    }
}

def Historia():
    pygame.init()

    ruta_assets = Path(__file__).parent / "Assets" / "Interfaz"

    ANCHO = 900
    ALTO = 600

    pantalla, canvas = Metodos.crear_ventana(ANCHO, ALTO, "My Game")

    imagenes = {}

    for nombre_escena, datos in escenas.items():
        archivo = datos["imagen"]

        if archivo.endswith(".mp4"):
            continue

        imagen = pygame.image.load(ruta_assets / archivo).convert()
        imagen = pygame.transform.smoothscale(imagen, (ANCHO, ALTO))
        imagenes[nombre_escena] = imagen

    video = None

    boton_siguiente = pygame.Rect(660, 540, 220, 45)
    boton_opcion1 = pygame.Rect(180, 400, 250, 95)
    boton_opcion2 = pygame.Rect(480, 400, 250, 95)

    escena_actual = "escena0"
    enfriamiento = 0
    ejecutando = True

    while ejecutando:
        clic = False

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                ejecutando = False

            if evento.type == pygame.VIDEORESIZE:
                pantalla = pygame.display.set_mode((evento.w, evento.h), pygame.RESIZABLE)

            if evento.type == pygame.MOUSEBUTTONDOWN:
                if evento.button == 1:
                    clic = True

        ancho_ventana, alto_ventana = pantalla.get_size()
        escala = min(ancho_ventana / ANCHO, alto_ventana / ALTO)
        desplazamiento_x = (ancho_ventana - int(ANCHO * escala)) // 2
        desplazamiento_y = (alto_ventana - int(ALTO * escala)) // 2
        posicion_mouse = Metodos.mouse_en_canvas(escala, desplazamiento_x, desplazamiento_y)

        if enfriamiento > 0:
            enfriamiento -= 1
            clic = False

        # Escena 0: video
        if escena_actual == "escena0":
            if video is None:
                video = cv2.VideoCapture(str(ruta_assets / "Escena0.mp4"))

            ret, cuadro = video.read()

            if ret:
                cuadro = cv2.cvtColor(cuadro, cv2.COLOR_BGR2RGB)
                cuadro = cv2.resize(cuadro, (ANCHO, ALTO))
                cuadro = cuadro.swapaxes(0, 1)
                superficie_video = pygame.surfarray.make_surface(cuadro)
                canvas.blit(superficie_video, (0, 0))

            else:
                video.release()
                video = None
                escena_actual = "escena1"
                enfriamiento = 15

        # Resto de escenas
        else:
            canvas.blit(imagenes[escena_actual], (0, 0))
            opciones = list(escenas[escena_actual]["opciones"].items())

            # Última escena
            if len(opciones) == 0:
                if Metodos.boton_inv(canvas, boton_siguiente, posicion_mouse, clic):
                    SeleccionarPJ.SeleccionarPJ()
                    ejecutando = False

            # Escena lineal
            elif len(opciones) == 1:
                texto, destino = opciones[0]

                if Metodos.boton_inv(canvas, boton_siguiente, posicion_mouse, clic):
                    escena_actual = destino
                    enfriamiento = 15

            # Escena de decisión
            else:
                texto1, destino1 = opciones[0]
                texto2, destino2 = opciones[1]

                if Metodos.boton_inv(canvas, boton_opcion1, posicion_mouse, clic):
                    escena_actual = destino1
                    enfriamiento = 15

                elif Metodos.boton_inv(canvas, boton_opcion2, posicion_mouse, clic):
                    escena_actual = destino2
                    enfriamiento = 15

        Metodos.mostrar_canvas(pantalla, canvas)
        pygame.display.update()

    if video is not None:
        video.release()

    pygame.quit()

