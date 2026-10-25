"""
EVENTO 1 del Lider: "El pozo".

Flujo:
    1. Video de la intro (escena1_llegada). Termina mostrando la pantalla
       de DECISION con los 4 botones (ya vienen dibujados en el video).
    2. El ultimo cuadro de la intro se queda quieto y los 4 botones del video
       se vuelven clicables (zonas invisibles encima de cada caja).
    3. Video de la opcion elegida (ya trae dialogos y texto).
       - VERIFICAR: el juego decide al azar si el rumor era falso (70%) o verdadero (30%).
       - REPORTAR: todavia no tiene video, muestra el texto en pantalla.
    4. El ultimo cuadro se queda quieto hasta que el jugador haga clic.

Para saltar videos mientras prueban: doble clic en la esquina de arriba a la derecha.

Indicadores (Confianza, Caos, Cohesion): se ven arriba a la izquierda en la
pantalla de decision y, al final del video, se animan con el cambio.

Uso desde Intz_Presidente.py:
    from Eventos import Evento1_Pozo
    resultado = Evento1_Pozo.jugar(display, canvas)

Devuelve un diccionario con la opcion elegida, sus efectos y el objeto
Indicadores ya actualizado (resultado["indicadores"]), para pasarselo
al siguiente evento: Evento2.jugar(display, canvas, resultado["indicadores"]).
"""

import random
import sys
from pathlib import Path

import cv2
import pygame

import Metodos

# ------------------------------------------------------------------ rutas
RUTA_VIDEOS = Path(__file__).parent.parent / "Assets" / "Videos"
RUTA_FUENTES = Path(__file__).parent.parent / "Assets" / "Interfaz"

# ------------------------------------------------------------------ colores
ROJO = (229, 57, 53)
BLANCO = (240, 240, 240)
GRIS = (170, 170, 170)

# ------------------------------------------------------------------ zonas clicables
# Posicion de cada boton DENTRO DEL VIDEO, como fraccion del ancho y alto
# del video: (x_inicio, y_inicio, x_fin, y_fin). 0 = borde izquierdo/arriba, 1 = derecho/abajo.
ZONAS_BOTONES = {
    "COMPARTIR": (0.133, 0.525, 0.432, 0.655),
    "IGNORAR":   (0.548, 0.525, 0.848, 0.655),
    "VERIFICAR": (0.133, 0.750, 0.432, 0.882),
    "REPORTAR":  (0.548, 0.745, 0.848, 0.872),
}
# Ponlo en True para ver las zonas en rojo y comprobar que coinciden con tus cajas.
MOSTRAR_ZONAS = False

# ------------------------------------------------------------------ contenido del evento
PROBABILIDAD_FALSO = 0.7

CONSECUENCIAS = {
    "COMPARTIR": {
        "video": "escena1_compartir.mp4",
        "texto": "Compartiste sin saber si era cierto. El miedo se esparció más rápido que el agua.",
        "efectos": {"Confianza": -15, "Caos": +20, "Cohesión": -10},
    },
    "VERIFICAR_FALSO": {
        "video": "escena1_verificar_falso.mp4",
        "texto": "Verificaste antes de hablar. Esta vez, la verdad llegó primero.",
        "efectos": {"Confianza": +15, "Caos": -10, "Cohesión": +10},
    },
    "VERIFICAR_VERDADERO": {
        "video": "escena1_verificar_verdadero.mp4",
        "texto": "Verificaste, y esta vez el rumor era cierto. Gracias a ti, nadie bebió.",
        "efectos": {"Confianza": +15, "Caos": -10, "Cohesión": +10},
    },
    "IGNORAR": {
        "video": "escena1_ignorar.mp4",
        "texto": "Tu silencio también comunicó algo. El rumor siguió corriendo.",
        "efectos": {"Confianza": -10, "Caos": +10, "Cohesión": -5},
    },
    "REPORTAR": {
        "video": "escena1_reportar.mp4",
        "texto": "Marcaste el mensaje como no confiable. El rumor dejó de circular... aunque nadie comprobó el agua.",
        "efectos": {"Confianza": 0, "Caos": -10, "Cohesión": +5},
    },
}


# ================================================================== ayudas
def cargar_fuente(tamano, negrita=False):
    """Usa Space Mono si esta en Assets/Interfaz; si no, Consolas."""
    nombre = "SpaceMono-Bold.ttf" if negrita else "SpaceMono-Regular.ttf"
    ruta = RUTA_FUENTES / nombre
    if ruta.exists():
        return pygame.font.Font(str(ruta), tamano)
    return pygame.font.SysFont("Consolas", tamano, bold=negrita)


def cuadro_a_imagen(cuadro):
    """Convierte un cuadro de OpenCV en una imagen de pygame (tamano original)."""
    cuadro = cv2.cvtColor(cuadro, cv2.COLOR_BGR2RGB)
    alto, ancho = cuadro.shape[:2]
    return pygame.image.frombuffer(cuadro.tobytes(), (ancho, alto), "RGB").copy()


def ultimo_cuadro(ruta_video):
    """Devuelve el ultimo cuadro de un video como imagen de pygame (o None)."""
    video = cv2.VideoCapture(str(ruta_video))
    total = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    video.set(cv2.CAP_PROP_POS_FRAMES, max(total - 2, 0))

    cuadro = None
    while True:
        ok, siguiente = video.read()
        if not ok:
            break
        cuadro = siguiente
    video.release()

    return None if cuadro is None else cuadro_a_imagen(cuadro)


def dibujar_ajustado(canvas, imagen):
    """Dibuja la imagen lo mas grande posible sin recortarla (igual que el video).
    Devuelve el rectangulo donde quedo dibujada."""
    canvas.fill((0, 0, 0))
    if imagen is None:
        return canvas.get_rect()
    ancho_c, alto_c = canvas.get_size()
    ancho_i, alto_i = imagen.get_size()
    escala = min(ancho_c / ancho_i, alto_c / alto_i)
    nuevo = (int(ancho_i * escala), int(alto_i * escala))
    rect = pygame.Rect(0, 0, *nuevo)
    rect.center = (ancho_c // 2, alto_c // 2)
    canvas.blit(pygame.transform.smoothscale(imagen, nuevo), rect)
    return rect


def partir_texto(texto, fuente, ancho_max):
    """Divide un texto en lineas que quepan en ancho_max."""
    lineas, actual = [], ""
    for palabra in texto.split():
        prueba = f"{actual} {palabra}".strip()
        if fuente.size(prueba)[0] <= ancho_max:
            actual = prueba
        else:
            lineas.append(actual)
            actual = palabra
    if actual:
        lineas.append(actual)
    return lineas


def leer_eventos():
    """Devuelve (click, tecla_continuar). Cierra el juego si se cierra la ventana."""
    click = continuar = False
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.VIDEORESIZE:
            pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            click = True
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN):
            continuar = True
    return click, continuar


def mostrar(canvas):
    """Pasa el canvas a la ventana y devuelve la posicion del mouse dentro del canvas."""
    escala, off_x, off_y = Metodos.mostrar_canvas(pygame.display.get_surface(), canvas)
    pygame.display.update()
    return Metodos.mouse_en_canvas(escala, off_x, off_y)


# ================================================================== video
def reproducir(canvas, ruta):
    """Reproduce un video con su .mp3.
    Para saltarlo: doble clic en la esquina de arriba a la derecha."""
    video = cv2.VideoCapture(str(ruta))
    fps = video.get(cv2.CAP_PROP_FPS) or 30
    reloj = pygame.time.Clock()

    ancho_c, alto_c = canvas.get_size()
    zona_saltar = pygame.Rect(int(ancho_c * 0.80), 0, int(ancho_c * 0.20), int(alto_c * 0.20))

    ruta_audio = Path(ruta).with_suffix(".mp3")
    if ruta_audio.exists():
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        pygame.mixer.music.load(str(ruta_audio))
        pygame.mixer.music.play()

    inicio = pygame.time.get_ticks()
    cuadro_actual = 0
    ultimo_click = -1000
    mouse = (-1, -1)

    while True:
        saltar = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                video.release()
                pygame.quit()
                sys.exit()
            if event.type == pygame.VIDEORESIZE:
                pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and zona_saltar.collidepoint(mouse):
                ahora = pygame.time.get_ticks()
                if ahora - ultimo_click < 400:
                    saltar = True
                ultimo_click = ahora

        if saltar:
            break

        cuadro_objetivo = int((pygame.time.get_ticks() - inicio) / 1000 * fps)
        ok, cuadro = video.read()
        cuadro_actual += 1
        while ok and cuadro_actual < cuadro_objetivo:
            ok, cuadro = video.read()
            cuadro_actual += 1
        if not ok:
            break

        dibujar_ajustado(canvas, cuadro_a_imagen(cuadro))
        mouse = mostrar(canvas)
        reloj.tick(fps)

    video.release()
    if pygame.mixer.get_init():
        pygame.mixer.music.stop()


# ================================================================== indicadores
class Indicadores:
    """Confianza, Caos y Cohesion del grupo, de 0 a 100."""

    # True = subir es bueno (verde); False = subir es malo (rojo)
    SUBIR_ES_BUENO = {"Confianza": True, "Caos": False, "Cohesión": True}

    def __init__(self, confianza=50, caos=50, cohesion=50):
        self.valores = {"Confianza": confianza, "Caos": caos, "Cohesión": cohesion}

    def aplicar(self, efectos):
        for nombre, cambio in efectos.items():
            self.valores[nombre] = max(0, min(100, self.valores[nombre] + cambio))

    def copia(self):
        return dict(self.valores)


VERDE = (76, 175, 80)


def dibujar_indicadores(canvas, valores, cambios=None, alfa_cambios=255):
    """Panel pequeno arriba a la izquierda con una barra por indicador.
    valores: lo que se dibuja ahora (puede ir cambiando durante la animacion).
    cambios: {"Caos": +20, ...} para mostrar el +/- en verde o rojo."""
    ancho_c, alto_c = canvas.get_size()
    fuente = cargar_fuente(max(11, int(alto_c * 0.030)), negrita=True)

    margen = 14
    ancho_panel = int(ancho_c * 0.27)
    alto_fila = int(alto_c * 0.085)
    alto_panel = alto_fila * len(valores) + 16

    panel = pygame.Surface((ancho_panel, alto_panel), pygame.SRCALPHA)
    pygame.draw.rect(panel, (0, 0, 0, 165), panel.get_rect(), border_radius=10)
    pygame.draw.rect(panel, (255, 255, 255, 60), panel.get_rect(), width=1, border_radius=10)
    canvas.blit(panel, (margen, margen))

    x = margen + 12
    ancho_barra = ancho_panel - 24
    y = margen + 8
    for nombre, valor in valores.items():
        etiqueta = fuente.render(nombre.upper(), True, BLANCO)
        canvas.blit(etiqueta, (x, y))

        numero = fuente.render(str(int(round(valor))), True, BLANCO)
        canvas.blit(numero, numero.get_rect(topright=(x + ancho_barra, y)))

        if cambios and cambios.get(nombre):
            cambio = cambios[nombre]
            bueno = (cambio > 0) == Indicadores.SUBIR_ES_BUENO[nombre]
            texto = fuente.render(f"{cambio:+d}", True, VERDE if bueno else ROJO)
            texto.set_alpha(alfa_cambios)
            canvas.blit(texto, texto.get_rect(topright=(x + ancho_barra - numero.get_width() - 10, y)))

        y_barra = y + etiqueta.get_height() + 3
        alto_barra = max(5, int(alto_fila * 0.16))
        pygame.draw.rect(canvas, (70, 70, 70), (x, y_barra, ancho_barra, alto_barra), border_radius=3)
        lleno = int(ancho_barra * max(0, min(100, valor)) / 100)
        if lleno > 0:
            color = ROJO if nombre == "Caos" else BLANCO
            pygame.draw.rect(canvas, color, (x, y_barra, lleno, alto_barra), border_radius=3)

        y += alto_fila


def valores_animados(antes, despues, inicio, espera=400, duracion=900):
    """Mueve los valores de 'antes' a 'despues' poco a poco (despues de una pequena espera)."""
    t = (pygame.time.get_ticks() - inicio - espera) / duracion
    t = max(0.0, min(1.0, t))
    t = 1 - (1 - t) ** 3  # empieza rapido y frena al final
    return {k: antes[k] + (despues[k] - antes[k]) * t for k in antes}


# ================================================================== pantallas
def pantalla_decision(canvas, imagen, valores):
    """Deja quieto el ultimo cuadro de la intro (que ya trae los 4 botones dibujados)
    y convierte esas cajas en zonas clicables. Espera sin limite de tiempo."""
    reloj = pygame.time.Clock()
    mouse = (-1, -1)

    while True:
        click, _ = leer_eventos()
        rect_imagen = dibujar_ajustado(canvas, imagen)

        for opcion, (x1, y1, x2, y2) in ZONAS_BOTONES.items():
            zona = pygame.Rect(
                rect_imagen.x + int(x1 * rect_imagen.w),
                rect_imagen.y + int(y1 * rect_imagen.h),
                int((x2 - x1) * rect_imagen.w),
                int((y2 - y1) * rect_imagen.h),
            )
            encima = zona.collidepoint(mouse)

            if encima:
                # brillo suave dentro de la caja del video, para que se note el hover
                brillo = pygame.Surface(zona.size, pygame.SRCALPHA)
                pygame.draw.rect(brillo, (255, 255, 255, 40), brillo.get_rect(), border_radius=18)
                canvas.blit(brillo, zona.topleft)
            if MOSTRAR_ZONAS:
                pygame.draw.rect(canvas, ROJO, zona, width=2)

            if encima and click:
                return opcion

        dibujar_indicadores(canvas, valores)
        mouse = mostrar(canvas)
        reloj.tick(60)


def esperar_clic(canvas, imagen, antes, despues, efectos):
    """Deja quieto el ultimo cuadro del video, anima los indicadores
    y espera a que el jugador haga clic."""
    ancho, alto = canvas.get_size()
    fuente_ayuda = cargar_fuente(int(alto * 0.032))
    reloj = pygame.time.Clock()
    inicio = pygame.time.get_ticks()

    while True:
        click, tecla = leer_eventos()
        if click or tecla:
            return

        dibujar_ajustado(canvas, imagen)
        dibujar_indicadores(canvas, valores_animados(antes, despues, inicio), efectos)
        if (pygame.time.get_ticks() // 600) % 2 == 0:
            ayuda = fuente_ayuda.render("Haz clic para continuar", True, GRIS)
            fondo_ayuda = pygame.Surface((ayuda.get_width() + 24, ayuda.get_height() + 10), pygame.SRCALPHA)
            fondo_ayuda.fill((0, 0, 0, 150))
            centro = (ancho // 2, int(alto * 0.94))
            canvas.blit(fondo_ayuda, fondo_ayuda.get_rect(center=centro))
            canvas.blit(ayuda, ayuda.get_rect(center=centro))

        mostrar(canvas)
        reloj.tick(60)


def pantalla_consecuencia(canvas, imagen_fondo, opcion, texto, antes, despues, efectos):
    """Solo para opciones SIN video: CONSECUENCIA + opcion + texto letra por letra.
    Un clic completa el texto; el siguiente clic continua."""
    ancho, alto = canvas.get_size()
    fuente_titulo = cargar_fuente(int(alto * 0.055), negrita=True)
    fuente_opcion = cargar_fuente(int(alto * 0.05))
    fuente_texto = cargar_fuente(int(alto * 0.058))
    fuente_ayuda = cargar_fuente(int(alto * 0.032))

    lineas = partir_texto(texto, fuente_texto, int(ancho * 0.70))
    total_letras = sum(len(l) for l in lineas)
    letras_por_segundo = 35

    velo = pygame.Surface((ancho, alto), pygame.SRCALPHA)
    velo.fill((0, 0, 0, 240))

    inicio = pygame.time.get_ticks()
    completo = False
    reloj = pygame.time.Clock()

    while True:
        click, tecla = leer_eventos()
        if click or tecla:
            if completo:
                return
            completo = True

        transcurrido = (pygame.time.get_ticks() - inicio) / 1000
        visibles = total_letras if completo else int(transcurrido * letras_por_segundo)
        if visibles >= total_letras:
            completo = True

        dibujar_ajustado(canvas, imagen_fondo)
        canvas.blit(velo, (0, 0))

        y = int(alto * 0.20)
        t = fuente_titulo.render("CONSECUENCIA", True, ROJO)
        canvas.blit(t, t.get_rect(center=(ancho // 2, y)))
        o = fuente_opcion.render(opcion, True, BLANCO)
        rect_o = o.get_rect(center=(ancho // 2, y + fuente_titulo.get_height() + 4))
        canvas.blit(o, rect_o)
        y_linea = rect_o.bottom + 8
        largo = int(ancho * 0.35)
        pygame.draw.line(canvas, ROJO, (ancho // 2 - largo // 2, y_linea), (ancho // 2 + largo // 2, y_linea), 2)

        y = y_linea + int(alto * 0.10)
        restantes = visibles
        for linea in lineas:
            parte = linea[:max(restantes, 0)]
            restantes -= len(linea)
            if parte:
                r = fuente_texto.render(parte, True, BLANCO)
                canvas.blit(r, r.get_rect(midtop=(ancho // 2, y)))
            y += fuente_texto.get_linesize() + 4

        dibujar_indicadores(canvas, valores_animados(antes, despues, inicio), efectos)

        if completo and (pygame.time.get_ticks() // 600) % 2 == 0:
            ayuda = fuente_ayuda.render("Haz clic para continuar", True, GRIS)
            canvas.blit(ayuda, ayuda.get_rect(center=(ancho // 2, int(alto * 0.92))))

        mostrar(canvas)
        reloj.tick(60)


# ================================================================== evento completo
def jugar(display, canvas, indicadores=None):
    """indicadores: los que vienen del evento anterior. Si no hay, empiezan en 50."""
    if indicadores is None:
        indicadores = Indicadores()

    # 1. Intro (termina mostrando la pantalla de decision)
    ruta_intro = RUTA_VIDEOS / "escena1_llegada.mp4"
    reproducir(canvas, ruta_intro)

    # 2. Decision: ultimo cuadro de la intro + zonas clicables sobre sus botones
    cuadro_decision = ultimo_cuadro(ruta_intro)
    eleccion = pantalla_decision(canvas, cuadro_decision, indicadores.copia())

    # 3. Que paso
    if eleccion == "VERIFICAR":
        clave = "VERIFICAR_FALSO" if random.random() < PROBABILIDAD_FALSO else "VERIFICAR_VERDADERO"
    else:
        clave = eleccion
    datos = CONSECUENCIAS[clave]

    antes = indicadores.copia()
    indicadores.aplicar(datos["efectos"])
    despues = indicadores.copia()

    if datos["video"]:
        # El video ya trae los dialogos y el texto del narrador.
        ruta = RUTA_VIDEOS / datos["video"]
        reproducir(canvas, ruta)
        esperar_clic(canvas, ultimo_cuadro(ruta), antes, despues, datos["efectos"])
    else:
        # Sin video (por ahora REPORTAR): se muestra el texto en pantalla.
        pantalla_consecuencia(canvas, cuadro_decision, eleccion, datos["texto"],
                              antes, despues, datos["efectos"])

    return {
        "opcion": eleccion,
        "resultado": clave,
        "efectos": datos["efectos"],
        "indicadores": indicadores,
    }