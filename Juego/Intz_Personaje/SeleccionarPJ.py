import sys
from pathlib import Path

import cv2
import pygame

from Intz_Personaje import Intz_Ciudadano, Intz_Influencer, Intz_Periodista, Intz_Presidente
import Metodos

RUTA_INTERFAZ = Path(__file__).parent.parent / "Assets" / "Interfaz"
ANCHO, ALTO = 900, 675            # mismo formato que los videos (800 x 600)

# PERSONAJES: cada uno sale de su video de "Selecciona el género", recortando su retrato.
# recorte = (x1, y1, x2, y2) dentro del video de 800 x 600. Cada recorte está medido para que
# las 4 caras queden del mismo tamaño y a la misma altura (mismo acercamiento).
PERSONAJES = [
    {"rol": "PRESIDENTE", "video": "Genero_Presidente.mp4", "recorte": (470, 207, 673, 421), "genero": "Masculino"},
    {"rol": "CIUDADANO",  "video": "Genero_Ciudadano.mp4",  "recorte": (118, 206, 358, 458), "genero": "Femenino"},
    {"rol": "PERIODISTA", "video": "Genero_Periodista.mp4", "recorte": (452, 198, 696, 452), "genero": "Masculino"},
    {"rol": "INFLUENCER", "video": "Genero_Influencer.mp4", "recorte": (96, 243, 332, 491), "genero": "Femenino"},
]
FONDO = "Fondo_Seleccion.mp4"     # la ciudad destruida, sin los botones viejos

BLANCO = (245, 245, 245)


# VIDEOS
class VideoEnBucle:
    """Lee un video y vuelve a empezar cuando se acaba."""

    def __init__(self, ruta):
        self.video = cv2.VideoCapture(str(ruta))

    def cuadro(self):
        ok, cuadro = self.video.read()
        if not ok:
            self.video.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok, cuadro = self.video.read()
        return cuadro if ok else None

    def cerrar(self):
        self.video.release()


def a_superficie(cuadro, tam):
    cuadro = cv2.cvtColor(cv2.resize(cuadro, tam, interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB)
    return pygame.image.frombuffer(cuadro.tobytes(), tam, "RGB").copy()


def tarjeta(canvas, retrato, rect, encima):
    """Retrato con borde de papel blanco y una hoja detrás, igual para los 4."""
    atras = rect.move(7, -7)
    pygame.draw.rect(canvas, (205, 208, 210), atras)
    pygame.draw.rect(canvas, (245, 245, 243), rect)
    adentro = rect.inflate(-14, -14)
    canvas.blit(pygame.transform.smoothscale(retrato, adentro.size), adentro)
    if encima:
        pygame.draw.rect(canvas, (255, 225, 170), rect.inflate(8, 8), 3)


# DIBUJO
def fuente(tam):
    ruta = RUTA_INTERFAZ / "upheavtt.ttf"
    if ruta.exists():
        return pygame.font.Font(str(ruta), tam)
    return pygame.font.SysFont("consolas", tam, bold=True)


def texto_brillante(canvas, texto, f, centro):
    """Texto blanco con un brillo suave alrededor (como los títulos de los videos)."""
    img = f.render(texto, True, BLANCO)
    brillo = f.render(texto, True, (200, 210, 225))
    for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3), (-2, -2), (2, 2), (-2, 2), (2, -2)):
        brillo.set_alpha(45)
        canvas.blit(brillo, brillo.get_rect(center=(centro[0] + dx, centro[1] + dy)))
    canvas.blit(img, img.get_rect(center=centro))


def marco_doble(canvas, rect, color):
    """El marco de dos líneas cruzadas de los botones del juego."""
    pygame.draw.rect(canvas, color, rect, 3)
    pygame.draw.rect(canvas, color, rect.inflate(-12, -12), 2)
    pygame.draw.line(canvas, color, (rect.x - 10, rect.bottom - 6), (rect.x + 40, rect.bottom - 6), 2)
    pygame.draw.line(canvas, color, (rect.right - 6, rect.y - 8), (rect.right - 6, rect.y + 30), 2)


def flecha(canvas, rect, encima):
    color = BLANCO if not encima else (255, 220, 160)
    cx, cy = rect.center
    pygame.draw.polygon(canvas, color, [(cx - 26, cy), (cx - 6, cy - 20), (cx - 6, cy - 8),
                                        (cx + 26, cy - 8), (cx + 26, cy + 8), (cx - 6, cy + 8), (cx - 6, cy + 20)])


# PANTALLA
def SeleccionarPJ():
    pygame.init()
    display, canvas = Metodos.crear_ventana(ANCHO, ALTO, "The Leader")
    reloj = pygame.time.Clock()

    fondo = VideoEnBucle(RUTA_INTERFAZ / FONDO)
    videos = [VideoEnBucle(RUTA_INTERFAZ / p["video"]) for p in PERSONAJES]

    ancho_t, alto_t = 190, 198
    espacio = 22
    x0 = (ANCHO - (4 * ancho_t + 3 * espacio)) // 2
    tarjetas = [pygame.Rect(x0 + i * (ancho_t + espacio), 190, ancho_t, alto_t) for i in range(4)]
    etiquetas = [pygame.Rect(r.x - 4, r.bottom + 26, r.w + 8, 58) for r in tarjetas]
    boton_salir = pygame.Rect(30, 90, 70, 50)
    f_titulo, f_rol = fuente(44), fuente(24)

    def cerrar_todo():
        fondo.cerrar()
        for v in videos:
            v.cerrar()

    while True:
        click = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                cerrar_todo()
                pygame.quit()
                sys.exit()
            if event.type == pygame.VIDEORESIZE:
                display = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                click = True

        ancho_v, alto_v = display.get_size()
        escala = min(ancho_v / ANCHO, alto_v / ALTO)
        mouse = Metodos.mouse_en_canvas(escala, (ancho_v - int(ANCHO * escala)) // 2,
                                        (alto_v - int(ALTO * escala)) // 2)

        # 1. la ciudad destruida de fondo (ya viene un poco desenfocada) y franjas negras
        cuadro = fondo.cuadro()
        if cuadro is not None:
            canvas.blit(a_superficie(cuadro, (ANCHO, ALTO)), (0, 0))
        else:
            canvas.fill((60, 66, 72))
        velo = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        velo.fill((0, 0, 0, 35))
        canvas.blit(velo, (0, 0))
        pygame.draw.rect(canvas, (0, 0, 0), (0, 0, ANCHO, 62))
        pygame.draw.rect(canvas, (0, 0, 0), (0, ALTO - 62, ANCHO, 62))

        texto_brillante(canvas, "SELECCIONA TU PERSONAJE", f_titulo, (ANCHO // 2 + 30, 116))
        flecha(canvas, boton_salir, boton_salir.collidepoint(mouse))

        # 2. las 4 tarjetas animadas (cada una es un pedazo de su video)
        elegido = None
        for i, (p, video, r, e) in enumerate(zip(PERSONAJES, videos, tarjetas, etiquetas)):
            encima = r.collidepoint(mouse) or e.collidepoint(mouse)
            cuadro = video.cuadro()
            destino = r.inflate(14, 14) if encima else r
            if cuadro is not None:
                x1, y1, x2, y2 = p["recorte"]
                tarjeta(canvas, a_superficie(cuadro[y1:y2, x1:x2], (x2 - x1, y2 - y1)), destino, encima)
            color = (255, 225, 170) if encima else BLANCO
            marco_doble(canvas, e, color)
            texto_brillante(canvas, p["rol"], f_rol, e.center)
            if encima and click:
                elegido = p

        Metodos.mostrar_canvas(display, canvas)
        pygame.display.update()
        reloj.tick(30)

        # 3. qué pasa al elegir
        if click and boton_salir.collidepoint(mouse):
            cerrar_todo()
            pygame.quit()
            sys.exit()

        if elegido:
            cerrar_todo()
            if elegido["rol"] == "PRESIDENTE":
                Intz_Presidente.Presidente()
                return
            if elegido["rol"] == "CIUDADANO":
                Intz_Ciudadano.Ciudadano()
                return
            if elegido["rol"] == "PERIODISTA":
                Intz_Periodista.Periodista()
                return
            # La influencer tiene su video antes de entrar; al salir vuelve a esta pantalla
            Metodos.ReproducirVideo("Video_Influencer_F.mp4")
            Intz_Influencer.Influencer(elegido["genero"])
            return SeleccionarPJ()