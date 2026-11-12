import math
import random
import sys
from pathlib import Path

import cv2
import pygame

import Metodos

# RUTAS
RUTA_VIDEOS = Path(__file__).parent.parent / "Assets" / "Videos"
RUTA_FUENTES = Path(__file__).parent.parent / "Assets" / "Fuentes"

# COLORES (sacados de los videos originales)
ROJO = (234, 50, 43)
BLANCO = (252, 252, 252)
GRIS = (170, 170, 170)
VERDE = (76, 175, 80)
NEGRO_ALERTA = (17, 9, 9)
TINTA_ALERTA = (28, 12, 12)

# Todo lo que se dibuja encima del video se mide sobre un video de 1920 x 1080.
# El código lo agranda o lo achica según el tamaño de la ventana.
REF_ANCHO, REF_ALTO = 1920, 1080

# Oscuridad del filtro de la pregunta y de la consecuencia (0 = nada, 255 = negro)
OSCURIDAD = 125

PROBABILIDAD_FALSO = 0.7

# TIEMPO PARA DECIDIR
# La barra roja debajo de la pregunta se encoge hasta desaparecer.
# El conteo empieza cuando la pregunta termina de escribirse.
TIEMPO_DECISION = 10          # segundos
EMPIEZA_CONTEO = 2.5          # la pregunta tarda 2.5 s en escribirse
SI_SE_ACABA = "IGNORAR"       # no decidir también es decidir: cuenta como ignorar


# GUION DE CADA VIDEO
# subtitulos: (empieza, termina de escribirse, desaparece, texto)   en segundos del video
# alerta:     (aparece, desaparece)  la notificación de Civitas
# pantalla:   segundo en que se oscurece el video y sale la pregunta o la consecuencia
INTRO = {
    "video": "escena1_llegada.mp4",
    "subtitulos": [
        (0.07, 2.27, 4.10, "Llegaron a las ruinas hace apenas unas horas."),
        (4.60, 7.23, 9.07, "No hay refugio seguro. El agua se está acabando."),
        (11.43, 12.57, 13.93, 'MUJER: "¿Lo leyeron? Dicen que el agua del pozo está envenenada..."'),
        (16.67, 17.83, 19.17, 'HOMBRE: "Dos personas se enfermaron por tomarla."'),
        (21.90, 23.20, 24.73, 'ANCIANO: "¿Y ahora qué vamos a tomar?"'),
        (33.67, 34.70, 35.97, "Todos te miran."),
        (36.03, 37.87, 39.60, "Nadie te nombró líder... pero nadie más está hablando."),
    ],
    "alerta": (12.60, 16.75),
    "pantalla": 39.63,
}

CONSECUENCIAS = {
    "COMPARTIR": {
        "video": "escena1_compartir.mp4",
        "subtitulos": [(1.47, 2.33, 3.33, 'LÍDER: "¡Aléjense del pozo! ¡El agua está envenenada!"')],
        "pantalla": 7.27,
        "opcion": "COMPARTIR",
        "texto": "Compartiste sin saber si era\ncierto. El miedo se esparció más\nrápido que el agua...",
        "efectos": {"Confianza": -15, "Caos": +20, "Cohesión": -10},
    },
    "VERIFICAR_FALSO": {
        "video": "escena1_verificar_falso.mp4",
        "subtitulos": [(13.83, 14.67, 15.63, 'LÍDER: "El agua está bien. Se los aseguro."')],
        "pantalla": 17.27,
        "opcion": "VERIFICAR",
        "texto": "Verificaste antes de hablar. Esta\nvez, la verdad llegó primero.",
        "efectos": {"Confianza": +15, "Caos": -10, "Cohesión": +10},
    },
    "VERIFICAR_VERDADERO": {
        "video": "escena1_verificar_verdadero.mp4",
        "subtitulos": [],
        "pantalla": 17.23,
        "opcion": "VERIFICAR",
        "texto": "Verificaste, y esta vez el rumor\nera cierto. Gracias a ti, nadie\nbebió.",
        "efectos": {"Confianza": +15, "Caos": -10, "Cohesión": +10},
    },
    "IGNORAR": {
        "video": "escena1_ignorar.mp4",
        "subtitulos": [(3.17, 4.03, 5.03, 'MUJER: "¿No va a decir nada?"')],
        "pantalla": 5.33,
        "opcion": "IGNORAR",
        "texto": "Tu silencio también comunicó algo.\nEl rumor siguió corriendo.",
        "efectos": {"Confianza": -10, "Caos": +10, "Cohesión": -5},
    },
    "REPORTAR": {
        "video": "escena1_reportar.mp4",
        "subtitulos": [],
        "pantalla": 5.30,
        "opcion": "REPORTAR",
        "texto": "Marcaste el mensaje como no confiable.\nEl rumor dejó de circular... aunque\nnadie comprobó el agua.",
        "efectos": {"Confianza": 0, "Caos": -10, "Cohesión": +5},
    },
}

# Botones de la pregunta, en el video de 1920 x 1080: (x, y, ancho, alto)
BOTONES = {
    "COMPARTIR": (257, 568, 570, 132),
    "IGNORAR":   (1053, 568, 570, 132),
    "VERIFICAR": (257, 816, 570, 131),
    "REPORTAR":  (1053, 806, 570, 131),
}

# Texto de la notificación de Civitas (cada línea como sale en el video)
ALERTA_TITULO = "MENSAJE VIRAL"
ALERTA_LINEAS = [
    "EL AGUA DEL POZO DE LA PLAZA ESTÁ",
    "ENVENENADA. COMPARTAN ANTES DE QUE ALGUIEN",
    "MÁS LA TOME.",
]


# ---------------------------------------------------------------------------
# GUION DEL SOBREVIVIENTE (personaje CIUDADANO): el mercado de Barrio Las Acacias
# Mismo sistema que el del Líder; cambian los videos, los textos y la alerta.
# VERIFICAR no tiene final falso/verdadero: ella se va con el hombre hacia el
# campo minado (Evento 2), así que el resultado se guarda como "VERIFICAR".
# ---------------------------------------------------------------------------
INTRO_SOBREVIVIENTE = {
    "video": "ciudadano_llegada.mp4",
    "subtitulos": [
        (1.00, 3.20, 6.50, "El mercado de Barrio Las Acacias. Aquí todo se cambia por agua."),
        (11.00, 13.00, 16.50, "Y cada día queda menos para cambiar."),
        (28.20, 29.40, 31.40, "Todos te miran. Nadie sabe qué hacer."),
    ],
    "alerta": (20.60, 25.80),
    "alerta_lineas": [
        "ALGUIEN VA CAMINO AL DEPÓSITO A LLEVARSE",
        "TODA EL AGUA PARA ÉL Y LOS SUYOS.",
        "COMPÁRTANLO ANTES DE QUE SEA TARDE.",
    ],
    "pantalla": 31.50,
}

CONSECUENCIAS_SOBREVIVIENTE = {
    "COMPARTIR": {
        "video": "ciudadano_compartir.mp4",
        "subtitulos": [],
        "pantalla": 3.70,
        "opcion": "COMPARTIR",
        "texto": "Reenviaste el mensaje sin saber si\nera cierto. El mercado entró en\npánico.",
        "efectos": {"Confianza": -15, "Caos": +20, "Cohesión": -10},
    },
    "IGNORAR": {
        "video": "ciudadano_ignorar.mp4",
        "subtitulos": [],
        "pantalla": 3.70,
        "opcion": "IGNORAR",
        "texto": "Guardaste silencio. El rumor\nsiguió corriendo sin ti.",
        "efectos": {"Confianza": -10, "Caos": +10, "Cohesión": -5},
    },
    "REPORTAR": {
        "video": "ciudadano_reportar.mp4",
        "subtitulos": [],
        "pantalla": 3.70,
        "opcion": "REPORTAR",
        "texto": "Marcaste el mensaje como no confiable.\nEl rumor se detuvo... pero nadie\nsabe la verdad.",
        "efectos": {"Confianza": 0, "Caos": -10, "Cohesión": +5},
    },
    "VERIFICAR": {
        "video": "ciudadano_verificar.mp4",
        "subtitulos": [],
        "pantalla": 7.60,
        "opcion": "VERIFICAR",
        "texto": "Decidiste verlo con tus propios ojos.\nPara llegar al agua, primero hay\nque cruzar el campo.",
        "efectos": {"Confianza": +15, "Caos": -10, "Cohesión": +10},
    },
}

# Qué guion usa cada personaje del mapa (los demás usan el del Líder)
GUIONES = {
    "LÍDER": (INTRO, CONSECUENCIAS),
    "SOBREVIVIENTE": (INTRO_SOBREVIVIENTE, CONSECUENCIAS_SOBREVIVIENTE),
}


# FUENTES
_fuentes = {}


def fuente(nombre, tamano):
    """nombre: 'mono', 'mono_negrita' o 'subtitulo'. Se guardan para no cargarlas cada vez."""
    tamano = max(8, int(tamano))
    clave = (nombre, tamano)
    if clave not in _fuentes:
        archivos = {
            "mono": "SpaceMono-Regular.ttf",
            "mono_negrita": "SpaceMono-Bold.ttf",
            "subtitulo": "CormorantGaramond-BoldItalic.ttf",
        }
        ruta = RUTA_FUENTES / archivos[nombre]
        if ruta.exists():
            _fuentes[clave] = pygame.font.Font(str(ruta), tamano)
        else:
            _fuentes[clave] = pygame.font.SysFont("georgia" if nombre == "subtitulo" else "consolas",
                                                  tamano, bold=True, italic=nombre == "subtitulo")
    return _fuentes[clave]


def cargar_fuente(tamano, negrita=False):
    """La usan los indicadores."""
    return fuente("mono_negrita" if negrita else "mono", tamano)


# AYUDAS PARA DIBUJAR
def letras_visibles(texto, t, empieza, termina):
    """Efecto máquina de escribir: cuántas letras se ven en el segundo t."""
    if t < empieza:
        return 0
    if t >= termina:
        return len(texto)
    return int(len(texto) * (t - empieza) / (termina - empieza))


def escribir(pantalla, texto, letras, f, color, centro, sombra=False):
    """Escribe solo las primeras 'letras', pero dejando el texto donde quedaría completo
    (así crece hacia la derecha, como en el video)."""
    if letras <= 0:
        return
    ancho_total = f.size(texto)[0]
    x = centro[0] - ancho_total // 2
    y = centro[1] - f.get_height() // 2
    parte = texto[:letras]
    if sombra:
        s = f.render(parte, True, (0, 0, 0))
        s.set_alpha(110)
        pantalla.blit(s, (x + 2, y + 2))
    pantalla.blit(f.render(parte, True, color), (x, y))


def oscurecer(pantalla, rect, alfa):
    velo = pygame.Surface(rect.size, pygame.SRCALPHA)
    velo.fill((0, 0, 0, alfa))
    pantalla.blit(velo, rect.topleft)


def triangulo_pixelado(tam_celda):
    """El triángulo de advertencia hecho con cuadritos, como un letrero de luces."""
    forma = [
        "..........##..........",
        ".........####.........",
        ".........####.........",
        "........##..##........",
        "........##..##........",
        ".......##....##.......",
        ".......##.##.##.......",
        "......##..##..##......",
        "......##..##..##......",
        ".....##...##...##.....",
        ".....##...##...##.....",
        "....##....##....##....",
        "....##..........##....",
        "...##.....##.....##...",
        "...##.....##.....##...",
        "..##..............##..",
        ".######################",
        "######################",
    ]
    columnas = max(len(f) for f in forma)
    sup = pygame.Surface((columnas * tam_celda, len(forma) * tam_celda), pygame.SRCALPHA)
    lado = max(1, tam_celda - max(1, tam_celda // 5))     # espacio entre cuadritos
    for fila, linea in enumerate(forma):
        for col, c in enumerate(linea):
            if c == "#":
                pygame.draw.rect(sup, ROJO, (col * tam_celda, fila * tam_celda, lado, lado))
    return sup


# SUBTÍTULOS
def dibujar_subtitulos(pantalla, rect, s, t, subtitulos):
    f = fuente("subtitulo", 56 * s)
    for empieza, termina, desaparece, texto in subtitulos:
        if empieza <= t < desaparece:
            n = letras_visibles(texto, t, empieza, termina)
            escribir(pantalla, texto, n, f, BLANCO,
                     (rect.x + rect.w // 2, rect.y + int(0.91 * rect.h)), sombra=True)


# NOTIFICACIÓN DE CIVITAS
def caja_alerta(s, tl, dur, lineas=None):
    """Dibuja la ventana de alerta completa (sin efectos) en su tamaño final."""
    ancho, alto = int(1360 * s), int(551 * s)
    alto_barra = int(93 * s)
    corte = int(22 * s)
    borde = max(2, int(4 * s))
    caja = pygame.Surface((ancho, alto), pygame.SRCALPHA)

    # cuerpo negro con borde rojo
    cuerpo = pygame.Rect(0, alto_barra - corte, ancho, alto - alto_barra + corte)
    pygame.draw.rect(caja, (*NEGRO_ALERTA, 238), cuerpo, border_radius=int(20 * s))
    pygame.draw.rect(caja, ROJO, cuerpo, width=borde, border_radius=int(20 * s))
    # líneas de televisor vieja
    paso = max(3, int(5 * s))
    for y in range(alto_barra, alto - borde, paso):
        pygame.draw.line(caja, (255, 255, 255, 9), (borde, y), (ancho - borde, y))

    # barra roja de arriba con las esquinas cortadas
    pygame.draw.polygon(caja, ROJO, [(corte, 0), (ancho - corte, 0), (ancho, corte),
                                     (ancho, alto_barra), (0, alto_barra), (0, corte)])
    f_barra = fuente("mono_negrita", 36 * s)
    texto = f_barra.render("CIVITAS // ALERTA", True, TINTA_ALERTA)
    caja.blit(texto, (int(42 * s), alto_barra // 2 - texto.get_height() // 2 + int(2 * s)))
    lado = int(47 * s)
    for i in range(3):
        x = ancho - int(223 * s) + i * int(68 * s)
        pygame.draw.rect(caja, TINTA_ALERTA, (x, int(25 * s), lado, lado), width=max(2, int(4 * s)))

    # triángulo
    tri = triangulo_pixelado(max(2, int(12 * s)))
    caja.blit(tri, (int(199 * s) - tri.get_width() // 2, int(183 * s)))

    # textos que se escriben solos (se borran justo antes de que se vaya)
    if tl < dur - 0.35:
        f_titulo = fuente("mono_negrita", 57 * s)
        n = letras_visibles(ALERTA_TITULO, tl, 0.23, 2.0)
        if n:
            caja.blit(f_titulo.render(ALERTA_TITULO[:n], True, ROJO),
                      (int(357 * s), int(181 * s) - f_titulo.get_height() // 2))
        f_cuerpo = fuente("mono", 36 * s)
        lineas = lineas or ALERTA_LINEAS
        todo = sum(len(l) for l in lineas)
        quedan = letras_visibles("x" * todo, tl, 0.15, 1.8)
        for i, linea in enumerate(lineas):
            parte = linea[:max(0, quedan)]
            quedan -= len(linea)
            if parte:
                caja.blit(f_cuerpo.render(parte, True, (240, 236, 236)),
                          (int(359 * s), int((280 + 50 * i) * s) - f_cuerpo.get_height() // 2))
    return caja


def dibujar_alerta(pantalla, rect, s, t, inicio, fin, lineas=None):
    if not (inicio <= t < fin):
        return
    tl, dur = t - inicio, fin - inicio
    entrada = min(1.0, tl / 0.30)
    salida = min(1.0, (dur - tl) / 0.30)
    k = min(entrada, salida)
    k = 1 - (1 - k) ** 3                           # se abre rápido y frena
    # interferencia fuerte al aparecer y al desaparecer
    glitch = max(0.0, 1 - tl / 0.6) if tl < 0.6 else max(0.0, 1 - (dur - tl) / 0.4)

    caja = caja_alerta(s, tl, dur, lineas)
    ancho = max(4, int(caja.get_width() * (0.22 + 0.78 * k)))
    alto = max(3, int(caja.get_height() * (0.08 + 0.92 * k)))
    if (ancho, alto) != caja.get_size():
        caja = pygame.transform.smoothscale(caja, (ancho, alto))

    centro = (rect.x + int(968 * s), rect.y + int(512 * s))
    destino = caja.get_rect(center=centro)

    # brillo rojo alrededor
    for i, a in ((18, 22), (10, 35), (4, 50)):
        halo = pygame.Surface((ancho + 2 * int(i * s), alto + 2 * int(i * s)), pygame.SRCALPHA)
        pygame.draw.rect(halo, (*ROJO, int(a * k)), halo.get_rect(), border_radius=int(30 * s))
        pantalla.blit(halo, halo.get_rect(center=centro))

    if glitch <= 0.02:
        pantalla.blit(caja, destino)
        return

    azar = random.Random(int(t * 30))
    # copias de color corridas (como una pantalla mal sintonizada)
    corrimiento = int(10 * s * glitch)
    for color, dx in (((255, 40, 40), corrimiento), ((40, 220, 255), -corrimiento)):
        copia = caja.copy()
        copia.fill((*color, 255), special_flags=pygame.BLEND_RGBA_MULT)
        copia.set_alpha(int(45 * glitch))
        pantalla.blit(copia, destino.move(dx, 0))
    # franjas horizontales que se desplazan
    franja = max(2, int(alto / 14))
    for y in range(0, alto, franja):
        dx = int(azar.uniform(-1, 1) * 28 * s * glitch) if azar.random() < 0.45 else 0
        pantalla.blit(caja, (destino.x + dx, destino.y + y), pygame.Rect(0, y, ancho, franja))
    # bandas oscuras que bajan
    for _ in range(3):
        y = azar.randint(0, alto)
        banda = pygame.Surface((ancho, max(2, int(10 * s))), pygame.SRCALPHA)
        banda.fill((0, 0, 0, int(120 * glitch)))
        pantalla.blit(banda, (destino.x, destino.y + y))


# BARRA DE TIEMPO
def tiempo_restante(tl):
    """Segundos que le quedan al jugador (de TIEMPO_DECISION a 0)."""
    pasado = max(0, tl - EMPIEZA_CONTEO)
    return max(0, TIEMPO_DECISION - pasado)


def barra_tiempo(pantalla, s, punto, tl, x1, x2, y):
    """Línea roja que se encoge desde los lados hacia el centro.
    En los últimos 3 segundos parpadea para avisar."""
    fraccion = tiempo_restante(tl) / TIEMPO_DECISION
    if fraccion <= 0:
        return
    if tiempo_restante(tl) < 3 and (pygame.time.get_ticks() // 250) % 2 == 0:
        return                                   # parpadeo
    centro = (x1 + x2) / 2
    mitad = (x2 - x1) / 2 * fraccion
    pygame.draw.line(pantalla, ROJO, punto(centro - mitad, y), punto(centro + mitad, y), max(2, int(4 * s)))


# PANTALLA DE LA PREGUNTA
def dibujar_decision(pantalla, rect, s, tl, mouse):
    """tl: segundos desde que salió la pregunta. Devuelve los botones en coordenadas de pantalla."""
    oscurecer(pantalla, rect, OSCURIDAD)

    def punto(x, y):
        return rect.x + int(x * s), rect.y + int(y * s)

    titulo = "DECISIÓN"
    escribir(pantalla, titulo, letras_visibles(titulo, tl, 0.05, 1.25),
             fuente("mono_negrita", 57 * s), ROJO, punto(942, 255))
    pregunta = "¿Qué vas a hacer con el mensaje?"
    escribir(pantalla, pregunta, letras_visibles(pregunta, tl, 0.0, 2.5),
             fuente("mono", 57 * s), BLANCO, punto(960, 395))
    barra_tiempo(pantalla, s, punto, tl, 620, 1300, 451)

    f_boton = fuente("mono", 54 * s)
    zonas = {}
    for opcion, (x, y, w, h) in BOTONES.items():
        zona = pygame.Rect(*punto(x, y), int(w * s), int(h * s))
        encima = zona.collidepoint(mouse)
        radio = int(52 * s)
        if encima:
            brillo = pygame.Surface(zona.size, pygame.SRCALPHA)
            pygame.draw.rect(brillo, (255, 255, 255, 38), brillo.get_rect(), border_radius=radio)
            pantalla.blit(brillo, zona.topleft)
        pygame.draw.rect(pantalla, BLANCO, zona, width=max(2, int(3 * s)), border_radius=radio)
        texto = f_boton.render(opcion, True, BLANCO)
        pantalla.blit(texto, texto.get_rect(center=zona.center))
        zonas[opcion] = zona
    return zonas


# PANTALLA DE LA CONSECUENCIA
def tiempo_consecuencia(datos):
    """Cuánto tarda en escribirse todo el texto de la consecuencia."""
    return max(1.25, len(datos["texto"]) / 48 + 0.1)


def dibujar_consecuencia(pantalla, rect, s, tl, datos):
    oscurecer(pantalla, rect, OSCURIDAD)

    def punto(x, y):
        return rect.x + int(x * s), rect.y + int(y * s)

    titulo = "CONSECUENCIA"
    escribir(pantalla, titulo, letras_visibles(titulo, tl, 0.0, 1.25),
             fuente("mono_negrita", 57 * s), ROJO, punto(960, 255))
    opcion = datos["opcion"]
    escribir(pantalla, opcion, letras_visibles(opcion, tl, 0.0, len(opcion) / 9),
             fuente("mono", 56 * s), BLANCO, punto(960, 355))
    pygame.draw.line(pantalla, ROJO, punto(620, 417), punto(1300, 417), max(2, int(4 * s)))

    f = fuente("mono", 58 * s)
    lineas = datos["texto"].split("\n")
    quedan = letras_visibles(datos["texto"].replace("\n", ""), tl, 0.0, tiempo_consecuencia(datos) - 0.1)
    for i, linea in enumerate(lineas):
        escribir(pantalla, linea, quedan, f, BLANCO, punto(960, 578 + 80 * i))
        quedan -= len(linea)


# INDICADORES
class Indicadores:
    """Confianza, Caos y Cohesión del grupo, de 0 a 100."""

    # True = subir es bueno (verde); False = subir es malo (rojo)
    SUBIR_ES_BUENO = {"Confianza": True, "Caos": False, "Cohesión": True}

    def __init__(self, confianza=50, caos=50, cohesion=50):
        self.valores = {"Confianza": confianza, "Caos": caos, "Cohesión": cohesion}

    def aplicar(self, efectos):
        for nombre, cambio in efectos.items():
            self.valores[nombre] = max(0, min(100, self.valores[nombre] + cambio))

    def copia(self):
        return dict(self.valores)


def dibujar_indicadores(canvas, valores, cambios=None, alfa_cambios=255):
    """Panel pequeño arriba a la izquierda con una barra por indicador.
    valores: lo que se dibuja ahora (puede ir cambiando durante la animación).
    cambios: {"Caos": +20, ...} para mostrar el +/- en verde o rojo."""
    ancho_c, alto_c = canvas.get_size()
    f = cargar_fuente(max(11, int(alto_c * 0.030)), negrita=True)

    margen = int(alto_c * 0.025)
    ancho_panel = int(ancho_c * 0.27)
    alto_fila = int(alto_c * 0.085)
    alto_panel = alto_fila * len(valores) + int(alto_c * 0.03)

    panel = pygame.Surface((ancho_panel, alto_panel), pygame.SRCALPHA)
    pygame.draw.rect(panel, (0, 0, 0, 165), panel.get_rect(), border_radius=10)
    pygame.draw.rect(panel, (255, 255, 255, 60), panel.get_rect(), width=1, border_radius=10)
    canvas.blit(panel, (margen, margen))

    x = margen + int(ancho_panel * 0.05)
    ancho_barra = ancho_panel - 2 * int(ancho_panel * 0.05)
    y = margen + int(alto_c * 0.015)
    for nombre, valor in valores.items():
        etiqueta = f.render(nombre.upper(), True, BLANCO)
        canvas.blit(etiqueta, (x, y))

        numero = f.render(str(int(round(valor))), True, BLANCO)
        canvas.blit(numero, numero.get_rect(topright=(x + ancho_barra, y)))

        if cambios and cambios.get(nombre):
            cambio = cambios[nombre]
            bueno = (cambio > 0) == Indicadores.SUBIR_ES_BUENO[nombre]
            texto = f.render(f"{cambio:+d}", True, VERDE if bueno else ROJO)
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
    """Mueve los valores de 'antes' a 'despues' poco a poco (después de una pequeña espera)."""
    t = (pygame.time.get_ticks() - inicio - espera) / duracion
    t = max(0.0, min(1.0, t))
    t = 1 - (1 - t) ** 3  # empieza rápido y frena al final
    return {k: antes[k] + (despues[k] - antes[k]) * t for k in antes}


# REPRODUCIR UNA ESCENA (video + todo lo que va encima)
def rect_video(pantalla):
    """El video lo más grande posible dentro de la ventana, sin deformarlo (16:9)."""
    ancho, alto = pantalla.get_size()
    escala = min(ancho / REF_ANCHO, alto / REF_ALTO)
    rect = pygame.Rect(0, 0, int(REF_ANCHO * escala), int(REF_ALTO * escala))
    rect.center = (ancho // 2, alto // 2)
    return rect


def escena(guion, modo, valores=None, antes=None, despues=None):
    """Reproduce el video del guion con sus subtítulos, la alerta y la pantalla final.
    modo = "decision": devuelve la opción que el jugador eligió.
    modo = "consecuencia": termina cuando el jugador hace clic al final.
    Para saltar el video: doble clic arriba a la derecha (va directo a la pregunta / consecuencia).
    Todo se dibuja directo en la ventana, a su tamaño real, para que el texto se vea nítido."""
    ruta = RUTA_VIDEOS / guion["video"]
    video = cv2.VideoCapture(str(ruta))
    fps = video.get(cv2.CAP_PROP_FPS) or 30
    reloj = pygame.time.Clock()
    Metodos.MAPA_BLOQUEADO = True              # durante la escena no se abre el mapa

    ruta_audio = ruta.with_suffix(".mp3")
    hay_audio = ruta_audio.exists()
    if hay_audio:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        pygame.mixer.music.load(str(ruta_audio))
        pygame.mixer.music.play()

    inicio = pygame.time.get_ticks()
    adelanto = 0.0                 # segundos que se saltaron
    leidos = 0                     # cuadros leídos del video
    cuadro = None                  # último cuadro (imagen de OpenCV)
    imagen = None                  # ese cuadro ya escalado para la ventana
    tam_imagen = None
    video_terminado = False
    ultimo_clic = -1000
    ultimo_espacio = -1000
    fin_escritura = None           # cuándo terminó de escribirse la consecuencia
    completar_texto = False
    pantalla = pygame.display.get_surface()

    while True:
        pantalla = pygame.display.get_surface()
        rect = rect_video(pantalla)
        s = rect.h / REF_ALTO
        mouse = pygame.mouse.get_pos()
        t = (pygame.time.get_ticks() - inicio) / 1000 + adelanto
        tl = t - guion["pantalla"]                 # tiempo desde que sale la pantalla final

        # 1. EVENTOS
        clic = False
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                video.release()
                pygame.quit()
                sys.exit()
            if evento.type == pygame.VIDEORESIZE:
                pygame.display.set_mode((evento.w, evento.h), pygame.RESIZABLE)
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_RETURN:
                clic = True
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_SPACE:
                clic = True
                ahora = pygame.time.get_ticks()
                if tl < 0 and ahora - ultimo_espacio < 400:    # doble espacio: saltar
                    adelanto += guion["pantalla"] - t
                    video.set(cv2.CAP_PROP_POS_FRAMES, int(guion["pantalla"] * fps))
                    leidos = int(guion["pantalla"] * fps)
                    if hay_audio:
                        pygame.mixer.music.play(start=guion["pantalla"])
                    clic = False
                ultimo_espacio = ahora
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                clic = True
                zona_saltar = pygame.Rect(int(pantalla.get_width() * 0.80), 0,
                                          int(pantalla.get_width() * 0.20), int(pantalla.get_height() * 0.20))
                ahora = pygame.time.get_ticks()
                if tl < 0 and zona_saltar.collidepoint(evento.pos):
                    if ahora - ultimo_clic < 400:          # doble clic: saltar
                        adelanto += guion["pantalla"] - t
                        video.set(cv2.CAP_PROP_POS_FRAMES, int(guion["pantalla"] * fps))
                        leidos = int(guion["pantalla"] * fps)
                        if hay_audio:
                            pygame.mixer.music.play(start=guion["pantalla"])
                        clic = False
                    ultimo_clic = ahora

        # 2. EL CUADRO DEL VIDEO QUE TOCA EN ESTE SEGUNDO
        objetivo = int(t * fps)
        nuevo = False
        while not video_terminado and leidos <= objetivo:
            ok, siguiente = video.read()
            if not ok:
                video_terminado = True
                break
            cuadro, leidos, nuevo = siguiente, leidos + 1, True
        if cuadro is not None and (nuevo or tam_imagen != rect.size):
            pequeño = cv2.resize(cuadro, rect.size, interpolation=cv2.INTER_AREA)
            pequeño = cv2.cvtColor(pequeño, cv2.COLOR_BGR2RGB)
            imagen = pygame.image.frombuffer(pequeño.tobytes(), rect.size, "RGB")
            tam_imagen = rect.size

        # 3. DIBUJAR
        pantalla.fill((0, 0, 0))
        if imagen is not None:
            pantalla.blit(imagen, rect)
        dibujar_subtitulos(pantalla, rect, s, t, guion["subtitulos"])
        if "alerta" in guion:
            dibujar_alerta(pantalla, rect, s, t, *guion["alerta"], guion.get("alerta_lineas"))

        if tl >= 0 and modo == "decision":
            zonas = dibujar_decision(pantalla, rect, s, tl, mouse)
            dibujar_indicadores(pantalla.subsurface(rect), valores)
            if tiempo_restante(tl) <= 0:               # se acabó el tiempo
                video.release()
                if hay_audio:
                    pygame.mixer.music.stop()
                Metodos.MAPA_BLOQUEADO = False
                return SI_SE_ACABA
            if clic and tl > 0.3:
                for opcion, zona in zonas.items():
                    if zona.collidepoint(mouse):
                        video.release()
                        if hay_audio:
                            pygame.mixer.music.stop()
                        Metodos.MAPA_BLOQUEADO = False
                        return opcion

        if tl >= 0 and modo == "consecuencia":
            duracion_texto = tiempo_consecuencia(guion)
            if clic and fin_escritura is None:
                completar_texto = True                 # un clic completa el texto de una vez
                clic = False
            tl_texto = duracion_texto if completar_texto else tl
            dibujar_consecuencia(pantalla, rect, s, tl_texto, guion)
            if tl_texto >= duracion_texto:
                if fin_escritura is None:
                    fin_escritura = pygame.time.get_ticks()
                dibujar_indicadores(pantalla.subsurface(rect),
                                    valores_animados(antes, despues, fin_escritura), guion["efectos"])
                if (pygame.time.get_ticks() // 600) % 2 == 0:
                    ayuda = fuente("mono", 30 * s).render("Haz clic para continuar", True, GRIS)
                    pantalla.blit(ayuda, ayuda.get_rect(center=(rect.centerx, rect.y + int(0.93 * rect.h))))
                if clic and pygame.time.get_ticks() - fin_escritura > 300:
                    video.release()
                    if hay_audio:
                        pygame.mixer.music.stop()
                    Metodos.MAPA_BLOQUEADO = False
                    return None

        pygame.display.update()
        reloj.tick(60)


# EVENTO COMPLETO
def jugar(display, canvas, indicadores=None, personaje="LÍDER"):
    """indicadores: los que vienen del evento anterior. Si no hay, empiezan en 50.
    personaje: la ruta del mapa ("LÍDER", "SOBREVIVIENTE"...). Elige el guion de la escena."""
    if indicadores is None:
        indicadores = Indicadores()
    intro, consecuencias = GUIONES.get(personaje, GUIONES["LÍDER"])

    # 1. Intro: llegada, alerta de Civitas y la pregunta
    eleccion = escena(intro, "decision", valores=indicadores.copia())

    # 2. Qué pasó (si verifica y el guion tiene dos finales, el juego decide al azar si el rumor era falso)
    if eleccion == "VERIFICAR" and "VERIFICAR" not in consecuencias:
        clave = "VERIFICAR_FALSO" if random.random() < PROBABILIDAD_FALSO else "VERIFICAR_VERDADERO"
    else:
        clave = eleccion
    datos = consecuencias[clave]

    antes = indicadores.copia()
    indicadores.aplicar(datos["efectos"])
    despues = indicadores.copia()

    # 3. Video de la consecuencia con su texto y los indicadores
    escena(datos, "consecuencia", antes=antes, despues=despues)

    return {
        "opcion": eleccion,
        "resultado": clave,
        "efectos": datos["efectos"],
        "indicadores": indicadores,
    }