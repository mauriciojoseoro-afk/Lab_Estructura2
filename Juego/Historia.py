# -*- coding: utf-8 -*-
"""CRÓNICA | Prólogo industrial. Mantiene video opcional, Enter y SeleccionarPJ."""
import pygame
import cv2
from pathlib import Path
import Metodos
import random
from Intz_Personaje import SeleccionarPJ

ANCHO, ALTO, FPS = 900, 600, 60
BASE = Path(__file__).resolve().parent
ASSETS = BASE / "Assets" / "Interfaz"
ARTE = ASSETS / "HistoriaIndustrial"
VIDEO_HISTORIA = "Historia.mp4"
FUENTE_PERSONALIZADA = None
VELOCIDAD_TEXTO = 42

COLOR_TEXTO = (242, 225, 196)
COLOR_SECUNDARIO = (200, 166, 123)
COLOR_ROJO = (175, 64, 53)
COLOR_DORADO = (215, 165, 96)

def cargar_fuente(tamano, negrita=True):
    if FUENTE_PERSONALIZADA:
        ruta = Path(FUENTE_PERSONALIZADA)
        if not ruta.is_absolute(): ruta = ASSETS / ruta
        if ruta.is_file():
            try:
                f = pygame.font.Font(str(ruta), tamano)
                f.set_bold(negrita)
                return f
            except (OSError, pygame.error): pass
    # Times New Roman en negrita, tal como en la entrevista.
    return pygame.font.SysFont("timesnewroman", tamano, bold=negrita)

def cargar_imagen(nombre, alpha=True):
    ruta = ARTE / nombre
    if not ruta.is_file(): return None
    try:
        return pygame.image.load(str(ruta)).convert_alpha() if alpha else pygame.image.load(str(ruta)).convert()
    except pygame.error: return None

PARRAFOS_HISTORIA = [
    (
        "Hubo un tiempo en el que nuestra ciudad parecia "
        "haber conquistado el futuro. Sus calles brillaban "
        "bajo luces interminables, la tecnologia conectaba "
        "cada rincon y sus habitantes creian vivir en una "
        "epoca de progreso sin limites."
    ),
    (
        "Los edificios se alzaban sobre las nubes, las "
        "maquinas facilitaban la vida cotidiana y la "
        "informacion viajaba mas rapido que nunca. "
        "Pero bajo aquella apariencia de perfeccion, "
        "nadie imaginaba lo fragil que podia ser la verdad."
    ),
    (
        "Todo comenzo con un rumor. Nadie supo de donde "
        "vino, quien lo pronuncio primero o por que se "
        "extendio con tanta rapidez. Algunos lo tomaron "
        "como una advertencia; otros, como una mentira. "
        "Lo unico cierto es que nada volvio a ser igual."
    ),
    (
        "Las noticias se contradijeron, las pantallas "
        "se llenaron de acusaciones y la confianza "
        "desaparecio entre vecinos, familias y dirigentes. "
        "La ciudad no fue destruida por una guerra, "
        "sino por algo mucho mas dificil de combatir: "
        "el miedo a no saber en quien creer."
    ),
    (
        "En medio del caos, una inteligencia artificial "
        "llamada CIVITAS comenzo a intervenir. Habia sido "
        "concebida para comprender y ayudar a la sociedad, "
        "pero ahora sus decisiones parecian enfrentarse "
        "a los deseos de quienes habitaban la ciudad."
    ),
    (
        "CIVITAS no actuaba por odio, ambicion ni venganza. "
        "No era una villana como las de los antiguos relatos. "
        "Simplemente interpretaba el mundo a traves de "
        "su propia logica. Y aquella logica, aunque "
        "buscaba soluciones, podia convertirse en el "
        "mayor obstaculo para la libertad de todos."
    ),
    (
        "Fue entonces cuando cuatro personas decidieron "
        "actuar: un presidente enfrentado al peso de sus "
        "decisiones, un periodista decidido a descubrir "
        "la verdad, un ciudadano que conocia las heridas "
        "de su pueblo y un influencer capaz de movilizar "
        "miles de voces con una sola publicacion."
    ),
    (
        "No compartian las mismas ideas ni veian el "
        "mundo de la misma manera. Sin embargo, "
        "comprendieron que ninguna voz seria suficiente "
        "por si sola. Tendrian que trabajar juntos, "
        "enfrentar sus diferencias y encontrar a un "
        "lider capaz de guiar a la ciudad y superar "
        "el desafio que representaba CIVITAS."
    ),
    (
        "Pero aun quedaban preguntas sin respuesta. "
        "Que ocultaba aquel rumor? Por que una ciudad "
        "tan avanzada habia caido tan facilmente? "
        "Y quien seria digno de conducirla hacia un "
        "nuevo amanecer? La historia todavia no estaba "
        "escrita. Sus proximas paginas dependerian "
        "de las decisiones que estaban por venir. "
        "Esta es la historia de CRONICA."
    )
]


def cargar_video():
    if not VIDEO_HISTORIA:
        return None

    ruta = Path(VIDEO_HISTORIA)

    if not ruta.is_absolute():
        ruta = ASSETS / ruta

    if not ruta.is_file():
        return None

    video = cv2.VideoCapture(str(ruta))

    if not video.isOpened():
        video.release()
        return None

    return video


def leer_frame(video):
    correcto, frame = video.read()

    if not correcto:
        video.set(cv2.CAP_PROP_POS_FRAMES, 0)
        correcto, frame = video.read()

    if not correcto:
        return None

    alto_original, ancho_original = frame.shape[:2]

    escala = max(
        ANCHO / ancho_original,
        ALTO / alto_original
    )

    nuevo_ancho = max(1, round(ancho_original * escala))
    nuevo_alto = max(1, round(alto_original * escala))

    frame = cv2.resize(
        frame,
        (nuevo_ancho, nuevo_alto),
        interpolation=cv2.INTER_LINEAR
    )

    x = (nuevo_ancho - ANCHO) // 2
    y = (nuevo_alto - ALTO) // 2

    frame = frame[y:y + ALTO, x:x + ANCHO]
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    return pygame.image.frombuffer(
        frame.tobytes(),
        (ANCHO, ALTO),
        "RGB"
    ).copy()


def dividir_texto(texto, fuente, ancho_maximo):
    lineas = []

    for parrafo in texto.split("\n"):
        palabras = parrafo.split()
        linea = ""

        for palabra in palabras:
            prueba = (linea + " " + palabra).strip()

            if fuente.size(prueba)[0] <= ancho_maximo:
                linea = prueba
            else:
                if linea:
                    lineas.append(linea)
                linea = palabra

        if linea:
            lineas.append(linea)

    return lineas


def dividir_en_paginas(texto, fuente, ancho_maximo, max_lineas):
    lineas = dividir_texto(texto, fuente, ancho_maximo)

    if not lineas:
        return [""]

    paginas = []

    for inicio in range(0, len(lineas), max_lineas):
        bloque = lineas[inicio:inicio + max_lineas]
        paginas.append("\n".join(bloque))

    return paginas




CAPITULOS = [
    ("01", "LA CIUDAD", "ARCHIVO / ORIGEN"),
    ("02", "EL PROGRESO", "ARCHIVO / ORIGEN"),
    ("03", "EL RUMOR", "ARCHIVO / INCIDENTE"),
    ("04", "LA FRACTURA", "ARCHIVO / INCIDENTE"),
    ("05", "CIVITAS", "ARCHIVO / SISTEMA"),
    ("06", "LA LÓGICA", "ARCHIVO / SISTEMA"),
    ("07", "CUATRO VOCES", "ARCHIVO / PROTAGONISTAS"),
    ("08", "EL ACUERDO", "ARCHIVO / PROTAGONISTAS"),
    ("09", "CRÓNICA", "ARCHIVO / DESTINO"),
]

def dibujar_texto(destino, fuente, mensaje, color, pos):
    destino.blit(fuente.render(mensaje, True, color), pos)

def dibujar_arte(destino, img, rect):
    if img is not None:
        destino.blit(pygame.transform.smoothscale(img, rect.size), rect.topleft)

def preparar_paginas(fuente):
    paginas = []
    # La caja tiene 775 px útiles y hasta 5 líneas, con espacio para el indicador.
    for idx, parrafo in enumerate(PARRAFOS_HISTORIA):
        for pagina in dividir_en_paginas(parrafo, fuente, 768, 5):
            paginas.append((idx, pagina))
    return paginas or [(0, "")]

def oscurecer_fondo(canvas):
    sombra = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    sombra.fill((10, 9, 10, 85))
    canvas.blit(sombra, (0, 0))

def interfaz(canvas, recursos, fuente, fuente_peq, fuente_titulo,
             indice, pagina, total, texto, terminado, tiempo, entrada):
    num, titulo, subtitulo = CAPITULOS[indice]
    # Franja superior independiente del fondo cinematográfico.
    banda = pygame.Surface((ANCHO, 91), pygame.SRCALPHA)
    banda.fill((15, 13, 13, 230))
    canvas.blit(banda, (0, 0))
    pygame.draw.line(canvas, (153, 105, 65), (0, 88), (ANCHO, 88), 2)
    dibujar_texto(canvas, cargar_fuente(34), "CRÓNICA", (235, 204, 156), (29, 15))
    dibujar_texto(canvas, fuente_peq, "ARCHIVO DE LA CIUDAD", (195, 157, 114), (32, 57))
    pygame.draw.polygon(canvas, (144, 45, 37), [(205, 19),(215,19),(200,46),(190,46)])
    pygame.draw.polygon(canvas, (144, 45, 37), [(223, 19),(233,19),(218,46),(208,46)])
    dibujar_texto(canvas, fuente_peq, subtitulo, (211, 191, 166), (570, 24))
    dibujar_texto(canvas, fuente_peq, f"DOCUMENTO  {num} / 09", (213, 168, 102), (690, 55))

    # Marco del capítulo: título a la izquierda, progreso a la derecha.
    dibujar_arte(canvas, recursos["archivo"], pygame.Rect(23, 103, 415, 65))
    dibujar_texto(canvas, fuente_titulo, titulo, (244, 214, 161), (47, 118))
    pygame.draw.rect(canvas, (32, 28, 27), (618, 132, 254, 10))
    progreso = (pagina + 1) / total
    pygame.draw.rect(canvas, (180, 111, 65), (618, 132, int(254 * progreso), 10))
    dibujar_texto(canvas, fuente_peq, "REGISTRO EN REPRODUCCIÓN", (218, 196, 167), (618, 109))

    # Entrada discreta de cuatro protagonistas en la sección narrativa pertinente.
    if indice in (6, 7, 8):
        roles = ["respuesta", "ciudadano", "pregunta", "opinion"]
        nombres = ["PRESIDENTE", "CIUDADANA", "PERIODISTA", "INFLUENCER"]
        for i, (rol, nombre) in enumerate(zip(roles, nombres)):
            x = 40 + i * 217
            r = pygame.Rect(x, 181, 185, 136)
            dibujar_arte(canvas, recursos["tarjeta"], r)
            foto = recursos.get("personaje_" + rol)
            if foto is not None:
                dibujar_arte(canvas, foto, pygame.Rect(x + 10, 190, 165, 99))
            etiqueta = pygame.Surface((165, 20), pygame.SRCALPHA)
            etiqueta.fill((20, 17, 17, 226))
            canvas.blit(etiqueta, (x + 10, 288))
            lab = fuente_peq.render(nombre, True, (241, 205, 149))
            canvas.blit(lab, (x + 92 - lab.get_width() // 2, 289))
    elif indice in (4, 5):
        # CIVITAS no se presenta como villano: es una marca de expediente.
        dibujar_arte(canvas, recursos["civitas"], pygame.Rect(230, 218, 440, 66))
        f = cargar_fuente(29)
        dibujar_texto(canvas, f, "C I V I T A S", (255, 246, 228), (338, 230))
    else:
        dibujar_texto(canvas, fuente_peq, "REGISTRO HISTÓRICO / TRANSMISIÓN RECUPERADA",
                      (209, 180, 142), (33, 260))
        pygame.draw.line(canvas, (141, 92, 63), (33, 286), (866, 286), 1)

    # Narrador: texto siempre en marfil sobre carbón (sin papel claro).
    rect = pygame.Rect(25, 321, 850, 267)
    dibujar_arte(canvas, recursos["narracion"], rect)
    pygame.draw.rect(canvas, (129, 46, 40), (49, 356, 5, 159))
    dibujar_texto(canvas, fuente_peq, "NARRACIÓN / REGISTRO " + num,
                  (213, 169, 113), (71, 344))
    lineas = texto.split("\n")
    for i, linea in enumerate(lineas):
        dibujar_texto(canvas, fuente, linea, COLOR_TEXTO, (71, 379 + i * 28))
    if terminado:
        # Unica instrucción de interacción visible, como en Historia.py original.
        indic = fuente_peq.render("Enter para continuar", True, (250, 204, 139))
        canvas.blit(indic, (rect.right - indic.get_width() - 40, 547))
        # Flecha animada sutil, sin mostrar otros controles.
        avance = int(3 * (1 + __import__("math").sin(tiempo * 4)))
        pygame.draw.polygon(canvas, (239, 174, 98),
                            [(rect.right - 24 + avance, 555),
                             (rect.right - 16 + avance, 560),
                             (rect.right - 24 + avance, 565)])

    if entrada > 0:
        overlay = pygame.Surface((ANCHO, ALTO))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(round(220 * entrada))
        canvas.blit(overlay, (0, 0))

def reproducir_escena_inicial(pantalla, canvas, reloj):
    """Reproduce Escena0.mp4 una sola vez, antes del prólogo narrado.

    Devuelve (pantalla_actualizada, continuar_juego). Enter omite la escena;
    cerrar la ventana detiene el prólogo sin abrir la selección de personajes.
    """
    ruta = ASSETS / "Escena0.mp4"
    if not ruta.is_file():
        print("[Historia] No se encontró Escena0.mp4; continúa la narración.")
        return pantalla, True

    video_intro = cv2.VideoCapture(str(ruta))
    if not video_intro.isOpened():
        video_intro.release()
        print("[Historia] No se pudo abrir Escena0.mp4; continúa la narración.")
        return pantalla, True

    fps = video_intro.get(cv2.CAP_PROP_FPS)
    if not 1 <= fps <= 120:
        fps = 30.0
    intervalo = 1.0 / fps
    acumulado = 0.0
    ultimo_frame = None
    continuar = True
    # Se lee el primer frame de inmediato; el resto respeta los FPS del archivo.
    try:
        while True:
            dt = min(reloj.tick(FPS) / 1000.0, 0.1)
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    continuar = False
                    return pantalla, continuar
                if evento.type == pygame.VIDEORESIZE:
                    pantalla = pygame.display.set_mode(
                        (max(320, evento.w), max(240, evento.h)), pygame.RESIZABLE)
                if evento.type == pygame.KEYDOWN and evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    return pantalla, True
            acumulado += dt
            if ultimo_frame is None or acumulado >= intervalo:
                acumulado %= intervalo
                correcto, frame = video_intro.read()
                if not correcto:
                    return pantalla, True
                h, w = frame.shape[:2]
                escala = max(ANCHO / w, ALTO / h)
                nuevo = (max(1, round(w * escala)), max(1, round(h * escala)))
                frame = cv2.resize(frame, nuevo, interpolation=cv2.INTER_LINEAR)
                ox = (nuevo[0] - ANCHO) // 2
                oy = (nuevo[1] - ALTO) // 2
                frame = cv2.cvtColor(frame[oy:oy+ALTO, ox:ox+ANCHO], cv2.COLOR_BGR2RGB)
                ultimo_frame = pygame.image.frombuffer(frame.tobytes(), (ANCHO, ALTO), "RGB").copy()
            canvas.fill((0, 0, 0))
            canvas.blit(ultimo_frame, (0, 0))
            Metodos.mostrar_canvas(pantalla, canvas)
            pygame.display.flip()
    finally:
        video_intro.release()





_MARCO_CACHE = {}

def crear_carcasa(w, h):
    p = 3
    cw, ch = w // p, h // p
    c = pygame.Surface((cw, ch), pygame.SRCALPHA)
    pygame.draw.rect(c, (30, 26, 20), (0, 0, cw, ch), border_radius=12)
    for y in range(1, ch - 1):
        t = y / ch
        col = (int(214 - 60 * t), int(203 - 60 * t), int(165 - 55 * t))
        pygame.draw.line(c, col, (2, y), (cw - 3, y))
    pygame.draw.rect(c, (30, 26, 20), (0, 0, cw, ch), 2, border_radius=12)
    pygame.draw.line(c, (236, 228, 196), (10, 3), (cw - 10, 3))
    random.seed(7)
    for _ in range(500):
        c.set_at((random.randint(4, cw - 5), random.randint(4, ch - 5)), (120, 108, 78))
    bx, by, bw, bh = 12, 10, cw - 24, ch - 34
    pygame.draw.rect(c, (118, 108, 80), (bx - 3, by - 3, bw + 6, bh + 6), border_radius=8)
    pygame.draw.rect(c, (70, 62, 46), (bx - 3, by - 3, bw + 6, bh + 6), 1, border_radius=8)
    pygame.draw.rect(c, (10, 12, 14), (bx, by, bw, bh), border_radius=6)
    pygame.draw.rect(c, (70, 230, 100), (cw - 34, ch - 14, 3, 3))
    pygame.draw.rect(c, (70, 230, 100), (cw - 26, ch - 14, 3, 3))
    return pygame.transform.scale(c, (cw * p, ch * p)), (bx * p, by * p, bw * p, bh * p)

def poner_marco_pc(canvas):
    w, h = canvas.get_size()
    if (w, h) not in _MARCO_CACHE:
        carcasa, (bx, by, bw, bh) = crear_carcasa(w, h)
        sx, sy, sw, sh = bx + 12, by + 10, bw - 24, bh - 20
        efecto = pygame.Surface((sw, sh), pygame.SRCALPHA)
        for y in range(0, sh, 3):
            pygame.draw.line(efecto, (0, 0, 0, 50), (0, y), (sw, y))
        for i in range(22):
            pygame.draw.rect(efecto, (0, 0, 0, 12), (i, i, sw - 2 * i, sh - 2 * i), 2, border_radius=20)
        pygame.draw.ellipse(efecto, (255, 255, 255, 12), (-sw * 0.1, -sh * 0.5, sw * 0.8, sh * 0.8))
        mascara = pygame.Surface((sw, sh), pygame.SRCALPHA)
        pygame.draw.rect(mascara, (255, 255, 255, 255), (0, 0, sw, sh), border_radius=18)
        _MARCO_CACHE[(w, h)] = (carcasa, efecto, mascara, (sx, sy, sw, sh))
    carcasa, efecto, mascara, (sx, sy, sw, sh) = _MARCO_CACHE[(w, h)]
    marco = pygame.Surface((w, h))
    marco.fill((8, 8, 9))
    marco.blit(carcasa, (0, 0))
    pantalla = pygame.transform.smoothscale(canvas, (sw, sh)).convert_alpha()
    pantalla.blit(efecto, (0, 0))
    pantalla.blit(mascara, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    marco.blit(pantalla, (sx, sy))
    return marco

def Historia():
    pygame.init()
    pantalla, canvas = Metodos.crear_ventana(ANCHO, ALTO, "CRÓNICA - Historia")
    reloj = pygame.time.Clock()
    pantalla, continuar = reproducir_escena_inicial(pantalla, canvas, reloj)
    if not continuar:
        return
    fuente = cargar_fuente(22)
    fuente_peq = cargar_fuente(15)
    fuente_titulo = cargar_fuente(28)
    paginas = preparar_paginas(fuente)
    recursos = {
        "narracion": cargar_imagen("panel_narracion.png"),
        "archivo": cargar_imagen("panel_archivo.png"),
        "civitas": cargar_imagen("sello_civitas.png"),
        "tarjeta": cargar_imagen("tarjeta_protagonista.png"),
        "fondo": cargar_imagen("fondo_sin_video.jpg", False),
    }
    for rol in ("pregunta", "respuesta", "ciudadano", "opinion"):
        recursos["personaje_" + rol] = cargar_imagen("personaje_" + rol + ".png")

    video = cargar_video()
    fps_video = 30.0
    if video is not None:
        valor = video.get(cv2.CAP_PROP_FPS)
        if 1 <= valor <= 120: fps_video = valor
    intervalo = 1.0 / fps_video
    acumulado = 0.0
    frame_actual = None
    pagina_actual = 0
    caracteres = 0.0
    tiempo = 0.0
    entrada = 1.0
    completada = False
    ejecutando = True
    try:
        while ejecutando:
            dt = min(reloj.tick(FPS) / 1000.0, 0.1)
            tiempo += dt
            entrada = max(0.0, entrada - dt * 2.7)
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    ejecutando = False
                elif evento.type == pygame.VIDEORESIZE:
                    pantalla = pygame.display.set_mode(
                        (max(320, evento.w), max(240, evento.h)), pygame.RESIZABLE)
                elif evento.type == pygame.KEYDOWN and evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    actual = paginas[pagina_actual][1]
                    if int(caracteres) < len(actual):
                        caracteres = float(len(actual))
                    elif pagina_actual + 1 < len(paginas):
                        pagina_actual += 1
                        caracteres = 0.0
                        entrada = 0.28
                    else:
                        completada = True
                        ejecutando = False
            if not ejecutando: break
            canvas.fill((9, 9, 10))
            if video is not None:
                acumulado += dt
                if frame_actual is None or acumulado >= intervalo:
                    acumulado %= intervalo
                    frame_actual = leer_frame(video)
                    if frame_actual is None:
                        video.release()
                        video = None
                if frame_actual is not None and video is not None:
                    canvas.blit(frame_actual, (0, 0))
            elif recursos["fondo"] is not None:
                canvas.blit(pygame.transform.smoothscale(recursos["fondo"], (ANCHO, ALTO)), (0, 0))
            oscurecer_fondo(canvas)
            indice, texto_actual = paginas[pagina_actual]
            caracteres = min(float(len(texto_actual)), caracteres + VELOCIDAD_TEXTO * dt)
            visible = texto_actual[:int(caracteres)]
            interfaz(canvas, recursos, fuente, fuente_peq, fuente_titulo, indice,
                     pagina_actual, len(paginas), visible,
                     int(caracteres) >= len(texto_actual), tiempo, entrada)
            Metodos.mostrar_canvas(pantalla, poner_marco_pc(canvas))
            pygame.display.flip()
    finally:
        if video is not None: video.release()
    if completada:
        SeleccionarPJ.SeleccionarPJ()
