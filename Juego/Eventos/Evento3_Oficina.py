import math
import random
import sys
from pathlib import Path

import pygame

import Metodos
from Eventos.Mapa import Grafo

# RUTAS Y TAMAÑO
ANCHO, ALTO = 1600, 900
RUTA_INTERFAZ = Path(__file__).resolve().parent.parent / "Assets" / "Interfaz"
RUTA_FUENTES = Path(__file__).resolve().parent.parent / "Assets" / "Fuentes"
RUTA_VIDEOS = Path(__file__).resolve().parent.parent / "Assets" / "Videos"
FONDO_OFICINA = "Oficina.jpg"
IMAGEN_RADIO = "radio.png"
FONDO_ALMACEN = "Almacen.jpg"     # opcional: si no está, se usa la oficina oscurecida

# COLORES (los mismos tonos del Evento 2: papel, tinta, óxido y ámbar)
PAPEL = (214, 199, 166)
PAPEL_CLARO = (232, 222, 196)
TINTA = (44, 34, 24)
OXIDO = (170, 82, 46)
AMBAR = (232, 170, 74)
ROJO = (234, 50, 43)
AZUL = (110, 170, 230)
GRIS = (130, 128, 122)
BLANCO = (245, 242, 235)
NEGRO = (10, 9, 8)
CRT = (255, 182, 72)          # letras del computador viejo
CRT_OSCURO = (120, 70, 20)

# OBJETOS DE LA OFICINA (fracción de la imagen: x1, y1, x2, y2)
OBJETOS = {
    "calendario": {"zona": (0.023, 0.211, 0.098, 0.591), "nombre": "Calendario"},
    "titular1":   {"zona": (0.284, 0.179, 0.389, 0.403), "nombre": "Recorte de periódico"},
    "tablero":    {"zona": (0.268, 0.140, 0.778, 0.605), "nombre": "Tablero de pistas"},
    "titular2":   {"zona": (0.628, 0.419, 0.731, 0.575), "nombre": "Recorte con una nota"},
    "computador": {"zona": (0.213, 0.509, 0.365, 0.762), "nombre": "Computador"},
    "radio":      {"zona": (0.443, 0.608, 0.557, 0.737), "nombre": "Radio"},
    "telefono":   {"zona": (0.409, 0.742, 0.513, 0.806), "nombre": "Teléfono"},
    "foto":       {"zona": (0.665, 0.634, 0.760, 0.772), "nombre": "Foto familiar"},
    "archivador": {"zona": (0.807, 0.587, 0.918, 0.746), "nombre": "Archivador"},
    "dibujo":     {"zona": (0.150, 0.752, 0.300, 0.835), "nombre": "Papeles"},
}

# GRAFO SOCIAL: el grupo del pozo (posición dentro de la pantalla del computador, de 0 a 1)
PERSONAS = {
    "LÍDER":     (0.50, 0.52),
    "ROSA":      (0.30, 0.34),
    "DON ELÍAS": (0.70, 0.32),
    "MATEO":     (0.24, 0.58),
    "LUCÍA":     (0.77, 0.58),
    "TOMÁS":     (0.39, 0.80),
    "INÉS":      (0.62, 0.80),
    "BRUNO":     (0.08, 0.40),
    "JULIÁN":    (0.50, 0.17),
    "MARIE":     (0.92, 0.40),
    "SAMUEL":    (0.12, 0.84),
    "ANA":       (0.88, 0.84),
}
CONFIANZA = [
    ("LÍDER", "ROSA"), ("LÍDER", "DON ELÍAS"), ("LÍDER", "MATEO"), ("LÍDER", "LUCÍA"),
    ("LÍDER", "TOMÁS"), ("LÍDER", "INÉS"),
    ("ROSA", "BRUNO"), ("ROSA", "JULIÁN"), ("ROSA", "MATEO"),
    ("DON ELÍAS", "JULIÁN"), ("DON ELÍAS", "MARIE"),
    ("MATEO", "SAMUEL"), ("MATEO", "BRUNO"),
    ("LUCÍA", "MARIE"), ("LUCÍA", "ANA"),
    ("TOMÁS", "SAMUEL"), ("TOMÁS", "INÉS"), ("INÉS", "ANA"),
]
ORIGEN_CIVITAS = "CIVITAS"
TOTAL_PISTAS = 4          # calendario, foto, dibujo y radio


# FUENTES
_fuentes = {}


def fuente(nombre, tamano):
    """'mono', 'mono_negrita' o 'narracion'."""
    clave = (nombre, int(tamano))
    if clave not in _fuentes:
        archivos = {"mono": "SpaceMono-Regular.ttf", "mono_negrita": "SpaceMono-Bold.ttf",
                    "narracion": "CormorantGaramond-BoldItalic.ttf"}
        ruta = RUTA_FUENTES / archivos[nombre]
        if ruta.exists():
            _fuentes[clave] = pygame.font.Font(str(ruta), int(tamano))
        else:
            _fuentes[clave] = pygame.font.SysFont("georgia" if nombre == "narracion" else "consolas",
                                                  int(tamano), bold=True, italic=nombre == "narracion")
    return _fuentes[clave]


# SONIDOS (hechos con código)
def crear_sonidos():
    sonidos = {}
    try:
        import numpy as np
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        frec, _, canales = pygame.mixer.get_init()

        def a_sonido(onda, volumen):
            datos = (np.clip(onda, -1, 1) * 32767 * volumen).astype(np.int16)
            if canales == 2:
                datos = np.ascontiguousarray(np.column_stack([datos, datos]))
            return pygame.sndarray.make_sound(datos)

        t = np.linspace(0, 0.5, int(frec * 0.5), dtype=np.float32)
        campana = (np.sin(2 * np.pi * 880 * t) + 0.5 * np.sin(2 * np.pi * 1320 * t)) * np.exp(-t * 7)
        sonidos["pista"] = a_sonido(campana / 1.5, 0.35)

        t = np.linspace(0, 0.12, int(frec * 0.12), dtype=np.float32)
        sonidos["tecla"] = a_sonido(np.sin(2 * np.pi * 220 * t) * np.exp(-t * 60), 0.3)
        sonidos["error"] = a_sonido(np.sign(np.sin(2 * np.pi * 140 * np.linspace(0, 0.3, int(frec * 0.3)))) * 0.5, 0.25)

        ruido = np.random.default_rng(3).standard_normal(int(frec * 2)).astype(np.float32)
        suave = np.convolve(ruido, np.ones(4) / 4, mode="same")
        sonidos["estatica"] = a_sonido(suave / 3, 0.6)
    except Exception:
        pass
    return sonidos


def sonar(sonidos, nombre):
    if nombre in sonidos:
        sonidos[nombre].play()


# CASO DE ESTA PARTIDA (cambia cada vez: componente aleatorio)
def crear_caso():
    """La clave del computador sale de 4 lugares: calendario (I), foto (II), dibujo (III) y radio (IV).
    En cada pista hay UN número marcado en rojo."""
    dia = random.randint(1, 9)                         # I: el día marcado en el calendario
    anio = random.randint(2031, 2039)                  # II: un número subrayado del año de la foto
    pos_anio = random.choice([2, 3])
    edad = random.randint(31, 58)                      # III: un número subrayado en el dibujo del cumpleaños
    pos_edad = random.randint(0, 1)
    refugio = random.randint(1, 9)                     # IV: el refugio que nombran en la radio
    frecuencia = round(random.randint(95, 106) + random.randint(1, 9) / 10, 1)
    digitos = [dia, int(str(anio)[pos_anio]), int(str(edad)[pos_edad]), refugio]
    return {
        "dia": dia, "anio": anio, "pos_anio": pos_anio,
        "edad": edad, "pos_edad": pos_edad,
        "refugio": refugio, "frecuencia": frecuencia,
        "digitos": digitos, "clave": "".join(str(d) for d in digitos),
    }


# GRAFO SOCIAL Y PROPAGACIÓN (BFS)
def crear_grafo_social():
    grafo = Grafo()
    for persona in PERSONAS:
        grafo.agregar_nodo(persona)
    for a, b in CONFIANZA:
        grafo.agregar_arista(a, b)
    return grafo


def bfs_propagacion(grafo, origen, bloqueados, max_rondas):
    """Recorrido por niveles: cada nivel es una ronda del rumor.
    Devuelve el nivel (ronda) en que le llegó a cada persona y quién se lo contó (padre)."""
    nivel = {origen: 0}
    padre = {origen: ORIGEN_CIVITAS}
    cola = [origen]
    i = 0
    while i < len(cola):
        persona = cola[i]
        i += 1
        if nivel[persona] >= max_rondas:
            continue
        for vecino in grafo.vecinos(persona):
            if vecino not in nivel and vecino not in bloqueados:
                nivel[vecino] = nivel[persona] + 1
                padre[vecino] = persona
                cola.append(vecino)
    return nivel, padre


def propagar_segun_decision(resultado_evento1):
    """La hoja del árbol del Evento 1 decide cómo se propagó el rumor en el grafo social."""
    grafo = crear_grafo_social()
    cortadas = []
    if resultado_evento1 == "COMPARTIR":
        origen, bloqueados, rondas = "LÍDER", set(), 10          # tú lo gritaste: le llegó a todos
        texto = "Tú compartiste el mensaje. El rumor salió de ti hacia todos los que confían en ti."
    elif resultado_evento1 == "IGNORAR":
        origen, bloqueados, rondas = "ROSA", {"LÍDER"}, 10       # tú callaste, el rumor siguió por otros
        texto = "Tú guardaste silencio. El rumor no pasó por ti... pero encontró otros caminos."
    elif resultado_evento1 == "REPORTAR":
        origen, bloqueados, rondas = "ROSA", set(), 1            # se frenó después de la primera ronda
        texto = "Tú reportaste el mensaje. Después de la primera ronda, los caminos del rumor se cortaron."
    else:
        # VERIFICAR: quienes confían en ti escucharon tu verificación y no lo creyeron
        origen = "ROSA"
        bloqueados = {"LÍDER"} | (set(grafo.vecinos("LÍDER")) - {origen})
        rondas = 10
        texto = "Tú verificaste antes de hablar. Quienes confían en ti no le creyeron al rumor."
    nivel, padre = bfs_propagacion(grafo, origen, bloqueados, rondas)
    if resultado_evento1 == "REPORTAR":
        # ELIMINAR ARISTAS: se cortan los caminos que salían de quienes ya lo habían recibido
        for persona in list(nivel):
            for vecino in grafo.vecinos(persona):
                if vecino not in nivel:
                    grafo.eliminar_arista(persona, vecino)
                    cortadas.append((persona, vecino))
    protegidos = bloqueados - {"LÍDER"} if resultado_evento1.startswith("VERIFICAR") else set()
    return {"grafo": grafo, "origen": origen, "nivel": nivel, "padre": padre,
            "protegidos": protegidos, "cortadas": cortadas, "texto": texto,
            "rondas": max(nivel.values()), "alcanzados": len(nivel)}


def camino_al_origen(padre, persona):
    """Sigue hacia atrás quién le contó a quién hasta llegar a Civitas (recorrido en profundidad)."""
    camino = [persona]
    while camino[-1] != ORIGEN_CIVITAS:
        camino.append(padre[camino[-1]])
    return camino


def camino_bfs(grafo, inicio, fin):
    """Camino más corto entre dos nodos (BFS). Devuelve la lista de nodos o None."""
    if inicio not in grafo.adyacencia or fin not in grafo.adyacencia:
        return None
    anterior = {inicio: None}
    cola = [inicio]
    i = 0
    while i < len(cola):
        actual = cola[i]
        i += 1
        if actual == fin:
            camino = [fin]
            while anterior[camino[-1]] is not None:
                camino.append(anterior[camino[-1]])
            return camino[::-1]
        for vecino in grafo.vecinos(actual):
            if vecino not in anterior:
                anterior[vecino] = actual
                cola.append(vecino)
    return None


# AYUDAS DE DIBUJO
def partir(texto, f, ancho):
    lineas = []
    for parrafo in texto.split("\n"):
        actual = ""
        for palabra in parrafo.split():
            prueba = f"{actual} {palabra}".strip()
            if f.size(prueba)[0] <= ancho:
                actual = prueba
            else:
                lineas.append(actual)
                actual = palabra
        lineas.append(actual)
    return lineas


def escribir(superficie, texto, f, color, pos, ancla="topleft", sombra=True):
    img = f.render(texto, True, color)
    rect = img.get_rect(**{ancla: pos})
    if sombra:
        s = f.render(texto, True, (0, 0, 0))
        s.set_alpha(140)
        superficie.blit(s, rect.move(2, 2))
    superficie.blit(img, rect)
    return rect


def parrafo(superficie, texto, f, color, x, y, ancho, letras=None, interlineado=1.15, centrado=False):
    """Escribe un texto en varias líneas. 'letras' = cuántas letras se ven (máquina de escribir)."""
    quedan = 10 ** 6 if letras is None else letras
    for linea in partir(texto, f, ancho):
        parte = linea[:max(0, quedan)]
        quedan -= len(linea)
        if parte:
            if centrado:
                escribir(superficie, parte, f, color, (x + (ancho - f.size(linea)[0]) // 2, y))
            else:
                escribir(superficie, parte, f, color, (x, y))
        y += int(f.get_linesize() * interlineado)
    return y


def placa(superficie, rect, alfa=225):
    """Placa de metal oscuro con franja de óxido arriba (como el HUD del Evento 2)."""
    capa = pygame.Surface(rect.size, pygame.SRCALPHA)
    c = 14
    puntos = [(c, 0), (rect.w - c, 0), (rect.w, c), (rect.w, rect.h - c),
              (rect.w - c, rect.h), (c, rect.h), (0, rect.h - c), (0, c)]
    pygame.draw.polygon(capa, (18, 15, 12, alfa), puntos)
    pygame.draw.polygon(capa, (*OXIDO, 255), puntos, 2)
    pygame.draw.line(capa, (*OXIDO, 255), (c, 5), (rect.w - c, 5), 3)
    superficie.blit(capa, rect.topleft)


def hoja(superficie, rect, color=PAPEL_CLARO, giro=0):
    """Hoja de papel con sombra (se puede girar un poquito)."""
    papel = pygame.Surface(rect.size, pygame.SRCALPHA)
    papel.fill((*color, 255))
    for i in range(0, rect.h, 4):
        tono = 8 * math.sin(i * 0.13)
        pygame.draw.line(papel, (max(0, color[0] - 12 + int(tono)), max(0, color[1] - 12 + int(tono)),
                                 max(0, color[2] - 14 + int(tono)), 40), (0, i), (rect.w, i))
    pygame.draw.rect(papel, (120, 100, 70, 255), papel.get_rect(), 2)
    if giro:
        papel = pygame.transform.rotate(papel, giro)
    sombra = pygame.Surface(papel.get_size(), pygame.SRCALPHA)
    sombra.fill((0, 0, 0, 120))
    destino = papel.get_rect(center=rect.center)
    superficie.blit(sombra, destino.move(8, 10))
    superficie.blit(papel, destino)
    return papel


def boton(superficie, rect, texto, mouse, activo=True):
    encima = activo and rect.collidepoint(mouse)
    color = AMBAR if encima else (PAPEL if activo else GRIS)
    pygame.draw.rect(superficie, (18, 15, 12), rect, border_radius=8)
    pygame.draw.rect(superficie, color, rect, 2, border_radius=8)
    escribir(superficie, texto, fuente("mono_negrita", 22), color, rect.center, "center", sombra=False)
    return encima


# VENTANA
class Ventana:
    """Guarda el canvas y la escala para saber dónde está el mouse dentro del canvas."""

    def __init__(self):
        self.canvas = pygame.Surface((ANCHO, ALTO))
        self.escala, self.ox, self.oy = 1, 0, 0
        self.reloj = pygame.time.Clock()

    def eventos(self):
        lista = []
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type == pygame.VIDEORESIZE:
                pygame.display.set_mode((e.w, e.h), pygame.RESIZABLE)
            lista.append(e)
        return lista

    def mouse(self):
        return Metodos.mouse_en_canvas(self.escala, self.ox, self.oy)

    def mostrar(self):
        self.escala, self.ox, self.oy = Metodos.mostrar_canvas(pygame.display.get_surface(), self.canvas)
        pygame.display.update()
        return self.reloj.tick(60) / 1000


def clic(eventos):
    return any(e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 for e in eventos)


def tecla(eventos, *teclas):
    return any(e.type == pygame.KEYDOWN and e.key in teclas for e in eventos)


# VIDEOS DEL FINAL (cámbialos por los tuyos con el mismo nombre en Assets/Videos)
# subtitulos: (empieza, termina de escribirse, desaparece, texto) en segundos del video
CONFRONTACION = {
    "video": "evento3_confrontacion.mp4",
    "subtitulos": [
        (0.3, 1.6, 3.4, "Se escuchan pasos. El grupo entra y ve la pantalla."),
        (6.1, 6.6, 7.4, 'ROSA: "¿Tú eras parte de Civitas?"'),
        (8.0, 8.4, 9.5, 'SAMUEL: "¡Nos mentiste!"'),
        (9.6, 10.1, 11.7, 'MARIE: "¿Cómo pudiste no decirnos?"'),
    ],
}
# LA PÁGINA QUE EXPLICA LO QUE PASÓ
VERDAD = ("Llegar a este lugar fue una trampa. Civitas te dejó encontrar esta oficina para que el grupo "
          "supiera quién eres... y se separara.")
VERDAD_TORRE = "Pero sabes algo que Civitas no quería que supieras: cómo detenerla. Les cuentas lo de la Torre."
VERDAD_SIN_TORRE = "Ahora todos saben la verdad."
VERDAD_FINAL = "¿El grupo te seguirá?"
NOTA_TORRE = ("No guardé esto en el computador: ella lo lee todo.\n\n"
              "Todo lo que Civitas dice sale de un solo servidor, en la Torre Civitas. No tiene copia. "
              "Si se desconecta, Civitas se queda muda: no más alertas, no más rumores.\n\n"
              "Ella lo sabe. Por eso nunca lo dice.\n\n— E. Varela")
BONO_TORRE = 15           # puntos extra para el final si encontraste la nota de la Torre

FINALES = {
    "disuelto": {
        "video": "evento3_final_disuelto.mp4",
        "subtitulos": [
            (0.5, 2.0, 3.8, "Uno a uno, te dan la espalda y se van."),
            (4.0, 5.8, 7.9, "Civitas no tuvo que mentir. Le bastó con la verdad."),
        ],
        "titulo": "EL GRUPO SE DISUELVE",
        "color": ROJO,
        "cierre": "Mañana irás solo a la Torre Civitas.",
    },
    "desconfianza": {
        "video": "evento3_final_desconfianza.mp4",
        "subtitulos": [
            (0.3, 1.8, 2.8, 'FABIO: "Puedes quedarte..."'),
            (2.9, 5.7, 7.9, 'FABIO: "...pero vas a tener que recuperar nuestra confianza."'),        ],
        "titulo": "QUÉDATE Y GÁNATELOS DE NUEVO",
        "color": AMBAR,
        "cierre": "Mañana les contarás todo sobre Civitas. Ahora tienes que lograr que te crean.",
    },
    "confian": {
        "video": "evento3_final_confian.mp4",
        "subtitulos": [
            (1.3, 2.8, 3.6, 'ROSA: "Lo que hiciste antes no te define..."'),
            (3.8, 5.3, 7.9, 'ROSA: "...lo que hiciste aquí, lo que hiciste por nosotros, sí."'),
        ],
        "titulo": "EL GRUPO CONFÍA EN TI",
        "color": AZUL,
        "cierre": "Civitas no logró separarlos. Mañana irán juntos a la Torre Civitas.",
    },
}

# LLEGADA: EL FALSO PEDIDO DE AYUDA Y LA BÚSQUEDA PISO POR PISO
LLEGADA = [
    ("texto", ["Llegaron al Almacén del Este. Había agua... pero no para todos.",
               "Esa noche, todos los dispositivos sonaron a la vez."]),
    ("alerta", None),
    ("texto", ["Todo el grupo fue. El viejo edificio de Civitas, al lado del depósito, estaba a oscuras.",
               "Se separaron para buscar más rápido, piso por piso."]),
    ("pisos", ["PISO 1 ... Nadie.", "PISO 2 ... Nadie.", "PISO 3 ... Nadie."]),
    ("texto", ["Tú subiste solo al último piso.",
               "Al fondo del pasillo, una sola puerta tenía luz por debajo."]),
]
MENSAJE_FALSO = ("por favor alguien que lea esto. soy Lucas, estoy con mi hermana y mi papá. "
                 "él está herido, no puede caminar. estamos en el último piso de la vieja oficina "
                 "de Civitas, al lado del depósito. no tenemos agua desde ayer. "
                 "POR FAVOR VENGAN RÁPIDO")

# TUTORIAL (nota con instrucciones, como en el Evento 2)
TUTORIAL = [
    ("No hay nadie", "La oficina está vacía. Nadie pidió ayuda desde aquí... pero hay un computador que todavía funciona."),
    ("Está bloqueado", "El computador pide una clave de 4 números. Quien trabajaba aquí la dejó escondida en este mismo cuarto."),
    ("Busca las pistas", "Pasa el mouse por la oficina: lo que se puede revisar se ilumina. Haz clic para verlo de cerca. "
                         "Arriba a la derecha verás cuántas pistas llevas."),
    ("Un número en rojo", "En cada pista hay un número marcado en rojo. El número romano (I, II, III, IV) dice en qué lugar va."),
    ("Ordénalas y entra", "Con las 4 pistas, ve al tablero y únelas con hilo en orden. Con la clave, enciende el computador... "
                          "y descubre quién los trajo aquí."),
]

# FICHAS DEL PERSONAL DE CIVITAS (el giro: los 4 personajes estuvieron metidos)
FICHAS = [
    ("LÍDER", "Ingeniero/a principal", "Diseñó el algoritmo que decide a quién le llega cada mensaje."),
    ("PERIODISTA", "Periodista asociado/a", "Publicó la primera alerta de Civitas sin verificarla."),
    ("INFLUENCER", "Creador/a de contenido", "Recibía pagos por repetir los mensajes de Civitas."),
    ("CIUDADANO", "Usuario de prueba #001", "Compartió cada mensaje que recibió, sin leerlo."),
]

# EL EVENTO
class Oficina:
    def __init__(self, indicadores, resultado_evento1, personaje="LÍDER"):
        self.v = Ventana()
        self.indicadores = indicadores
        self.resultado_evento1 = resultado_evento1
        self.personaje = personaje
        self.caso = crear_caso()
        self.sonidos = crear_sonidos()
        self.red = propagar_segun_decision(resultado_evento1)

        self.fondo = self.cargar_fondo()
        self.oscuro = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        self.oscuro.fill((0, 0, 0, 170))

        self.vistos = set()                 # objetos ya revisados
        self.pistas = {}                    # pistas encontradas: clave -> texto
        self.sabe_frecuencia = False        # leyó la nota del recorte
        self.orden_resuelto = False         # ordenó los números en el tablero
        self.computador_abierto = False
        self.archivos_vistos = set()
        self.dato_torre = False             # encontró la nota de la Torre (opcional, suma en el final)
        self.descubierto = False            # abrió su propia ficha: llega el grupo
        self.consecuencia_red = None

        # TABLERO DE PISTAS (otro grafo): cada pista es un nodo; los hilos en orden son las aristas
        self.tablero = Grafo()
        self.mensaje = ""
        self.mensaje_t = 0

    # CARGA
    def cargar_fondo(self):
        try:
            img = pygame.image.load(str(RUTA_INTERFAZ / FONDO_OFICINA)).convert()
            escala = max(ANCHO / img.get_width(), ALTO / img.get_height())
            img = pygame.transform.smoothscale(img, (int(img.get_width() * escala), int(img.get_height() * escala)))
            self.desfase = ((img.get_width() - ANCHO) // 2, (img.get_height() - ALTO) // 2)
            recorte = pygame.Surface((ANCHO, ALTO))
            recorte.blit(img, (-self.desfase[0], -self.desfase[1]))
            self.tam_img = img.get_size()
            return recorte
        except (FileNotFoundError, pygame.error):
            self.desfase, self.tam_img = (0, 0), (ANCHO, ALTO)
            s = pygame.Surface((ANCHO, ALTO))
            s.fill((30, 30, 34))
            return s

    def zona(self, clave):
        x1, y1, x2, y2 = OBJETOS[clave]["zona"]
        w, h = self.tam_img
        return pygame.Rect(int(x1 * w) - self.desfase[0], int(y1 * h) - self.desfase[1],
                           int((x2 - x1) * w), int((y2 - y1) * h))

    def avisar(self, texto):
        self.mensaje, self.mensaje_t = texto, 3.5

    def ganar_pista(self, clave, texto):
        if clave not in self.pistas:
            self.pistas[clave] = texto
            self.tablero.agregar_nodo(clave)          # AGREGAR NODO al tablero
            sonar(self.sonidos, "pista")
            if len(self.pistas) == TOTAL_PISTAS:
                self.avisar("¡Tienes todas las pistas! Ve al tablero y ordénalas.")
            else:
                self.avisar(f"Nueva pista ({len(self.pistas)}/{TOTAL_PISTAS})")

    # OBJETIVO ACTUAL (orienta al jugador)
    def objetivo(self):
        if len(self.pistas) < TOTAL_PISTAS:
            return "Busca en la oficina los 4 números de la clave del computador."
        if not self.orden_resuelto:
            return "Ve al tablero y ordena las 4 pistas para armar la clave."
        if not self.computador_abierto:
            return f"La clave es {self.caso['clave']}. Escríbela en el computador."
        return "Revisa los archivos del computador."

    # DIBUJO DE LA SALA
    def objeto_bajo(self, mouse):
        """Si hay varios objetos debajo del mouse (por ejemplo un recorte dentro del tablero), gana el más pequeño."""
        opciones = [c for c in OBJETOS if self.zona(c).collidepoint(mouse)]
        if not opciones:
            return None
        return min(opciones, key=lambda c: self.zona(c).w * self.zona(c).h)

    def iluminar(self, c, r, t):
        """Aclara suavemente el objeto, con el borde difuminado (como una silueta más clara)."""
        grande = r.inflate(20, 20)
        luz = pygame.Surface(grande.size)
        luz.fill((0, 0, 0))
        fuerza = 26 + 10 * math.sin(t * 5)
        pasos = 10
        for i in range(pasos):
            v = int(fuerza * (i + 1) / pasos)
            pygame.draw.rect(luz, (v, int(v * 0.9), int(v * 0.75)),
                             pygame.Rect(0, 0, grande.w, grande.h).inflate(-i * 2, -i * 2), border_radius=16)
        c.blit(luz, grande.topleft, special_flags=pygame.BLEND_RGB_ADD)
        borde = pygame.Surface(grande.size, pygame.SRCALPHA)
        pygame.draw.rect(borde, (255, 225, 170, 70), borde.get_rect().inflate(-6, -6), 2, border_radius=16)
        c.blit(borde, grande.topleft)

    def dibujar_sala(self, mouse, t, resaltar=True):
        c = self.v.canvas
        c.blit(self.fondo, (0, 0))
        encima = None
        if resaltar:
            encima = self.objeto_bajo(mouse)
            for clave in OBJETOS:
                r = self.zona(clave)
                if clave == encima:
                    self.iluminar(c, r, t)
                elif clave not in self.vistos:
                    a = int(90 + 90 * math.sin(t * 2 + len(clave)))
                    punto = pygame.Surface((14, 14), pygame.SRCALPHA)
                    pygame.draw.circle(punto, (*AMBAR, a), (7, 7), 5)
                    c.blit(punto, (r.right - 12, r.y - 2))

        f = fuente("mono", 19)
        lineas = partir(self.objetivo(), f, 680)
        alto = 44 + len(lineas) * int(f.get_linesize() * 1.15) + 10
        placa(c, pygame.Rect(20, 18, 720, alto))
        escribir(c, "OBJETIVO", fuente("mono_negrita", 18), OXIDO, (40, 28))
        parrafo(c, self.objetivo(), f, PAPEL, 40, 52, 680)

        f = fuente("mono_negrita", 22)
        texto = f"PISTAS: {len(self.pistas)}/{TOTAL_PISTAS}"
        r = f.render(texto, True, AMBAR).get_rect(topright=(ANCHO - 40, 32))
        placa(c, r.inflate(36, 22))
        escribir(c, texto, f, AMBAR, r.topleft, sombra=False)

        if self.mensaje_t > 0 and resaltar:
            self.dibujar_aviso(c, ALTO - 70)
        return encima

    def dibujar_aviso(self, c, y):
        f = fuente("mono_negrita", 22)
        r = f.render(self.mensaje, True, BLANCO).get_rect(center=(ANCHO // 2, y))
        placa(c, r.inflate(36, 20))
        if self.mensaje.startswith("★"):
            texto = self.mensaje[1:].strip()
            r = f.render(texto, True, BLANCO).get_rect(center=(ANCHO // 2 + 20, y))
            placa(c, r.inflate(90, 20))
            pygame.draw.rect(c, (255, 205, 90), r.inflate(84, 14), 3, border_radius=6)
            estrella(c, (r.x - 22, r.centery), 13, (255, 205, 90))
            escribir(c, texto, f, (255, 214, 110), r.topleft, sombra=False)
        else:
            escribir(c, self.mensaje, f, AMBAR, r.topleft, sombra=False)

    # BUCLE PRINCIPAL
    def jugar(self):
        Metodos.MAPA_BLOQUEADO = True
        self.llegada()
        self.tutorial()
        t = 0
        while True:
            dt = min(0.05, self.v.reloj.get_time() / 1000 or 0.016)
            t += dt
            self.mensaje_t -= dt
            eventos = self.v.eventos()
            mouse = self.v.mouse()
            encima = self.dibujar_sala(mouse, t)
            if clic(eventos) and encima:
                self.vistos.add(encima)
                if self.abrir(encima):
                    break
            self.v.mostrar()
        final = self.final()
        Metodos.MAPA_BLOQUEADO = False
        return final

    def abrir(self, clave):
        """Abre la vista de cerca. Devuelve True cuando el jugador termina de revisar el computador."""
        if clave == "calendario":
            self.ver_calendario()
        elif clave == "foto":
            self.ver_foto()
        elif clave == "archivador":
            self.ver_nota_torre()
        elif clave == "dibujo":
            self.ver_dibujo()
        elif clave in ("titular1", "titular2"):
            self.ver_titular(clave)
        elif clave == "telefono":
            self.ver_telefono()
        elif clave == "radio":
            if not self.sabe_frecuencia:
                sonar(self.sonidos, "error")
                self.avisar("Solo se escucha estática. No sabes en qué emisora buscar.")
            else:
                self.pantalla_radio()
        elif clave == "tablero":
            if len(self.pistas) < TOTAL_PISTAS:
                self.avisar(f"Aún no tienes todas las pistas ({len(self.pistas)}/{TOTAL_PISTAS}).")
            else:
                self.pantalla_tablero()
        elif clave == "computador":
            self.pantalla_computador()
            return self.descubierto
        return False

    # LLEGADA: CIVITAS LOS LLEVA A LA OFICINA
    def esperar_pantalla(self, dibujar, duracion):
        """Dibuja una pantalla hasta que pase 'duracion' y el jugador haga clic (un clic antes la completa)."""
        inicio = pygame.time.get_ticks()
        while True:
            eventos = self.v.eventos()
            seg = (pygame.time.get_ticks() - inicio) / 1000
            dibujar(self.v.canvas, seg)
            listo = seg >= duracion
            if listo and (pygame.time.get_ticks() // 600) % 2 == 0:
                escribir(self.v.canvas, "Haz clic para continuar", fuente("mono", 20), GRIS,
                         (ANCHO // 2, ALTO - 70), "midtop")
            if clic(eventos) or tecla(eventos, pygame.K_SPACE, pygame.K_RETURN):
                if listo:
                    return
                inicio -= 100000
            self.v.mostrar()

    def llegada(self):
        try:
            img = pygame.image.load(str(RUTA_INTERFAZ / FONDO_ALMACEN)).convert()
            fondo = pygame.transform.smoothscale(img, (ANCHO, ALTO))
            oscuridad = 120
        except (FileNotFoundError, pygame.error):
            fondo = self.fondo
            oscuridad = 205
        oscuro = fondo.copy()
        velo = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        velo.fill((0, 0, 0, oscuridad))
        oscuro.blit(velo, (0, 0))
        f = fuente("narracion", 44)
        for tipo, datos in LLEGADA:
            if tipo == "texto":
                def dibujar(c, seg, lineas=datos):
                    c.blit(oscuro, (0, 0))
                    y = ALTO // 2 - 40 * len(lineas)
                    for i, linea in enumerate(lineas):
                        letras = int(max(0, seg - 0.3 - i * 2.2) * 32)
                        if letras:
                            escribir(c, linea[:letras], f, BLANCO, (ANCHO // 2 - f.size(linea)[0] // 2, y))
                        y += 80
                self.esperar_pantalla(dibujar, 0.3 + len(datos) * 2.2)
            elif tipo == "pisos":
                def dibujar(c, seg, lineas=datos):
                    c.fill(NEGRO)
                    for i, linea in enumerate(lineas):
                        if seg > i * 1.1:
                            img = fuente("mono_negrita", 40).render(linea, True, GRIS)
                            img.set_alpha(min(255, int((seg - i * 1.1) * 400)))
                            c.blit(img, img.get_rect(center=(ANCHO // 2, ALTO // 2 - 90 + i * 90)))
                self.esperar_pantalla(dibujar, len(datos) * 1.1)
            else:
                sonar(self.sonidos, "error")
                def dibujar(c, seg):
                    c.blit(oscuro, (0, 0))
                    self.dibujar_notificacion(c, seg)
                self.esperar_pantalla(dibujar, 0.6 + len(MENSAJE_FALSO) / 45)

    def dibujar_notificacion(self, c, seg):
        """La notificación de Civitas con el falso pedido de ayuda."""
        k = min(1.0, seg / 0.35)
        k = 1 - (1 - k) ** 3
        r = pygame.Rect(0, 0, int(1100 * (0.3 + 0.7 * k)), int(470 * (0.1 + 0.9 * k)))
        r.center = (ANCHO // 2, ALTO // 2 - 20)
        for i, a in ((18, 25), (8, 45)):
            halo = pygame.Surface(r.inflate(2 * i, 2 * i).size, pygame.SRCALPHA)
            pygame.draw.rect(halo, (*ROJO, a), halo.get_rect(), border_radius=24)
            c.blit(halo, r.inflate(2 * i, 2 * i).topleft)
        pygame.draw.rect(c, (17, 9, 9), r, border_radius=16)
        pygame.draw.rect(c, ROJO, r, 4, border_radius=16)
        if k < 1:
            return
        barra = pygame.Rect(r.x, r.y, r.w, 76)
        pygame.draw.rect(c, ROJO, barra, border_top_left_radius=16, border_top_right_radius=16)
        escribir(c, "CIVITAS // MENSAJE REENVIADO", fuente("mono_negrita", 30), (28, 12, 12),
                 (r.x + 36, barra.centery), "midleft", sombra=False)
        parrafo(c, MENSAJE_FALSO, fuente("mono", 26), (240, 236, 236), r.x + 50, r.y + 110, r.w - 100,
                letras=int(max(0, seg - 0.4) * 45))
        if seg > 0.4 + len(MENSAJE_FALSO) / 45:
            escribir(c, "— Enviado por: Sobreviviente_27", fuente("mono_negrita", 24), ROJO,
                     (r.right - 50, r.bottom - 50), "bottomright", sombra=False)

    def tutorial(self):
        """Nota con las instrucciones, página por página (como en el Evento 2)."""
        pagina = 0
        inicio = pygame.time.get_ticks()
        while pagina < len(TUTORIAL):
            eventos = self.v.eventos()
            mouse = self.v.mouse()
            seg = (pygame.time.get_ticks() - inicio) / 1000
            c = self.v.canvas
            c.blit(self.fondo, (0, 0))
            c.blit(self.oscuro, (0, 0))
            titulo, texto = TUTORIAL[pagina]
            nota = pygame.Rect(0, 0, 820, 500)
            nota.center = (ANCHO // 2, ALTO // 2 - 30)
            hoja(c, nota, color=(226, 214, 184), giro=-1)
            escribir(c, f"{pagina + 1}/{len(TUTORIAL)}", fuente("mono", 20), OXIDO, (nota.right - 40, nota.y + 30),
                     "topright", sombra=False)
            escribir(c, titulo, fuente("mono_negrita", 44), TINTA, (nota.x + 60, nota.y + 60), sombra=False)
            pygame.draw.line(c, OXIDO, (nota.x + 60, nota.y + 128), (nota.right - 60, nota.y + 128), 3)
            letras = int(seg * 60)
            parrafo(c, texto, fuente("narracion", 38), TINTA, nota.x + 60, nota.y + 160, nota.w - 120, letras=letras)
            completo = letras >= len(texto)
            ultimo = pagina == len(TUTORIAL) - 1
            b = pygame.Rect(0, 0, 240, 52)
            b.midtop = (ANCHO // 2, nota.bottom + 30)
            presiono = boton(c, b, "Empezar" if ultimo else "Siguiente", mouse) and clic(eventos)
            saltar = pygame.Rect(ANCHO - 230, ALTO - 90, 190, 46)
            if not ultimo and boton(c, saltar, "Saltar", mouse) and clic(eventos):
                return
            if presiono or tecla(eventos, pygame.K_SPACE, pygame.K_RETURN):
                if completo:
                    pagina += 1
                    inicio = pygame.time.get_ticks()
                else:
                    inicio -= 100000
            self.v.mostrar()

    # VISTA DE CERCA GENÉRICA
    def vista(self, dibujar, texto_boton="Volver"):
        """Oscurece la sala y llama a dibujar(c, mouse, t, eventos) hasta que el jugador cierre.
        Si dibujar devuelve algo distinto de None, la vista se cierra y devuelve ese valor."""
        t = 0
        while True:
            dt = self.v.reloj.get_time() / 1000
            t += dt
            self.mensaje_t -= dt
            eventos = self.v.eventos()
            mouse = self.v.mouse()
            self.dibujar_sala(mouse, 0, resaltar=False)
            self.v.canvas.blit(self.oscuro, (0, 0))
            resultado = dibujar(self.v.canvas, mouse, t, eventos)
            if resultado is not None:
                return resultado
            if texto_boton:
                r = pygame.Rect(ANCHO - 200, ALTO - 130, 170, 50)
                if boton(self.v.canvas, r, texto_boton, mouse) and clic(eventos):
                    return None
            if tecla(eventos, pygame.K_ESCAPE):
                return None
            if self.mensaje_t > 0:
                self.dibujar_aviso(self.v.canvas, ALTO - 105)
            self.v.mostrar()

    def marca(self, c, numero, pos, color=ROJO):
        """El número romano escrito a mano que dice el orden de la pista."""
        escribir(c, numero, fuente("narracion", 54), color, pos, "center", sombra=False)

    # I. CALENDARIO
    def ver_calendario(self):
        dia = self.caso["dia"]

        def dibujar(c, mouse, t, eventos):
            r = pygame.Rect(0, 0, 560, 640)
            r.center = (ANCHO // 2, ALTO // 2 - 10)
            hoja(c, r, giro=-2)
            escribir(c, "MARZO", fuente("mono_negrita", 40), TINTA, (r.centerx, r.y + 30), "midtop", sombra=False)
            escribir(c, str(self.caso["anio"]), fuente("mono", 22), TINTA, (r.centerx, r.y + 82), "midtop", sombra=False)
            f = fuente("mono", 24)
            for i, d in enumerate("LMMJVSD"):
                escribir(c, d, f, OXIDO, (r.x + 60 + i * 70, r.y + 130), "midtop", sombra=False)
            for n in range(1, 32):
                fila, col = divmod(n + 2, 7)
                cx, cy = r.x + 60 + col * 70, r.y + 180 + fila * 72
                escribir(c, str(n), f, TINTA, (cx, cy), "midtop", sombra=False)
                if n == dia:
                    pygame.draw.ellipse(c, ROJO, (cx - 30, cy - 10, 60, 50), 4)
                    escribir(c, "Lanzamiento", fuente("narracion", 30), ROJO, (cx, cy + 38), "midtop", sombra=False)
            self.marca(c, "I", (r.right - 50, r.y + 50))
            return None

        self.vista(dibujar)
        self.ganar_pista("calendario", f"Calendario: el día {dia} marcado")

    # II. FOTO (un número del año está subrayado)
    def ver_foto(self):
        estado = {"volteada": False}
        x1, y1, x2, y2 = OBJETOS["foto"]["zona"]
        try:
            img = pygame.image.load(str(RUTA_INTERFAZ / FONDO_OFICINA)).convert()
            iw, ih = img.get_size()
            recorte = img.subsurface(pygame.Rect(int(x1 * iw), int(y1 * ih), int((x2 - x1) * iw),
                                                 int((y2 - y1) * ih))).copy()
            frente = pygame.transform.smoothscale(recorte, (840, int(840 * recorte.get_height() / recorte.get_width())))
        except (FileNotFoundError, pygame.error, ValueError):
            frente = pygame.Surface((840, 600))
            frente.fill((60, 55, 50))

        def dibujar(c, mouse, t, eventos):
            r = frente.get_rect(center=(ANCHO // 2, ALTO // 2 - 40))
            if not estado["volteada"]:
                sombra = pygame.Surface(r.size, pygame.SRCALPHA)
                sombra.fill((0, 0, 0, 120))
                c.blit(sombra, r.move(8, 10))
                c.blit(frente, r)
                pygame.draw.rect(c, (60, 45, 30), r, 8)
            else:
                hoja(c, r, color=(222, 210, 180))
                y = r.y + 140
                for linea in ["Todos juntos, el día", "que lanzamos Civitas."]:
                    escribir(c, linea, fuente("narracion", 54), TINTA, (r.centerx, y), "midtop", sombra=False)
                    y += 68
                f = fuente("narracion", 96)
                anio = str(self.caso["anio"])
                x = r.centerx - f.size(anio)[0] // 2
                y += 30
                for i, d in enumerate(anio):
                    marcado = i == self.caso["pos_anio"]
                    rr = escribir(c, d, f, ROJO if marcado else TINTA, (x, y), sombra=False)
                    if marcado:
                        pygame.draw.line(c, ROJO, (rr.x - 4, rr.bottom - 12), (rr.right + 4, rr.bottom - 16), 6)
                    x += f.size(d)[0]
                self.marca(c, "II", (r.right - 60, r.y + 60))
            b = pygame.Rect(0, 0, 260, 50)
            b.midtop = (ANCHO // 2, r.bottom + 22)
            if boton(c, b, "Voltear la foto", mouse) and clic(eventos):
                estado["volteada"] = not estado["volteada"]
                if estado["volteada"]:
                    self.ganar_pista("foto", "Foto")
            return None

        self.vista(dibujar)

    # III. DIBUJO DE LA HIJA (un número subrayado)
    def ver_dibujo(self):
        edad = str(self.caso["edad"])
        pos = self.caso["pos_edad"]
        azar = random.Random(7)

        def crayon(c, color, puntos, ancho=7):
            """Trazo de crayón: varias líneas temblorosas encima."""
            for k in range(3):
                pts = [(x + azar.uniform(-2, 2), y + azar.uniform(-2, 2)) for x, y in puntos]
                pygame.draw.lines(c, color, False, pts, max(2, ancho - k * 2))

        def dibujar(c, mouse, t, eventos):
            azar.seed(7)
            r = pygame.Rect(0, 0, 760, 600)
            r.center = (ANCHO // 2, ALTO // 2 - 20)
            hoja(c, r, color=(236, 228, 206), giro=2)
            # manchas de tiempo
            for _ in range(6):
                m = pygame.Surface((90, 70), pygame.SRCALPHA)
                pygame.draw.ellipse(m, (150, 120, 70, 35), m.get_rect())
                c.blit(m, (r.x + azar.randint(20, r.w - 110), r.y + azar.randint(20, r.h - 90)))
            # pastel
            base = pygame.Rect(r.centerx - 170, r.y + 360, 340, 130)
            crayon(c, (200, 110, 150), [base.topleft, base.topright, base.bottomright, base.bottomleft, base.topleft], 8)
            crayon(c, (120, 80, 50), [(base.x, base.y + 50), (base.right, base.y + 50)], 6)
            capa = pygame.Rect(base.x + 40, base.y - 80, base.w - 80, 80)
            crayon(c, (110, 160, 210), [capa.bottomleft, capa.topleft, capa.topright, capa.bottomright], 7)
            for k in range(5):
                x = capa.x + 30 + k * (capa.w - 60) // 4
                crayon(c, (230, 190, 60), [(x, capa.y), (x, capa.y - 50)], 6)
                pygame.draw.circle(c, (240, 120, 40), (x, capa.y - 62), 9)
            crayon(c, (90, 140, 70), [(r.x + 60, base.bottom + 20), (r.right - 60, base.bottom + 20)], 5)
            # texto con letra de niña
            f = fuente("narracion", 50)
            escribir(c, "Para papá:", f, (60, 90, 170), (r.centerx, r.y + 40), "midtop", sombra=False)
            g = fuente("narracion", 54)
            frase = "feliz cumpleaños "
            x = r.centerx - (g.size(frase)[0] + g.size(edad)[0]) // 2
            rr = escribir(c, frase, g, (60, 90, 170), (x, r.y + 110), sombra=False)
            x = rr.right
            for i, d in enumerate(edad):
                marcado = i == pos
                rd = escribir(c, d, g, ROJO if marcado else (60, 90, 170), (x, r.y + 110), sombra=False)
                if marcado:
                    pygame.draw.line(c, ROJO, (rd.x - 2, rd.bottom - 6), (rd.right + 2, rd.bottom - 10), 6)
                x = rd.right
            self.marca(c, "III", (r.right - 60, r.y + 60))
            return None

        self.vista(dibujar)
        self.ganar_pista("dibujo", "Dibujo")

    # EL ARCHIVADOR: LA NOTA DE LA TORRE (opcional, Civitas no la puede leer)
    def ver_nota_torre(self):
        def dibujar(c, mouse, t, eventos):
            carpeta = pygame.Rect(0, 0, 900, 640)
            carpeta.center = (ANCHO // 2, ALTO // 2 - 20)
            pygame.draw.rect(c, (176, 142, 86), carpeta, border_radius=10)
            pygame.draw.rect(c, (110, 84, 46), carpeta, 3, border_radius=10)
            nota = carpeta.inflate(-90, -80)
            hoja(c, nota, color=(232, 224, 200), giro=-1)
            parrafo(c, NOTA_TORRE, fuente("narracion", 34), TINTA, nota.x + 50, nota.y + 50, nota.w - 100,
                    letras=int(t * 55), interlineado=1.05)
            return None

        self.vista(dibujar)
        if not self.dato_torre:
            self.dato_torre = True
            sonar(self.sonidos, "pista")
            self.avisar("★ Esto puede servirte. Recuérdalo para decírselo al grupo.")

    # RECORTES (uno trae la nota con la emisora)
    def ver_titular(self, clave):
        if clave == "titular1":
            titulo = "CIVITAS: LA NUEVA IA DEL FUTURO"
            cuerpo = ("La inteligencia artificial que decide qué noticias ve cada persona promete acabar con el ruido "
                      "en las redes. 'Civitas aprende lo que te importa y te lo muestra primero', explicó su equipo "
                      "de ingenieros durante el lanzamiento.")
        else:
            titulo = "PROBLEMAS CON LA MEJOR IA"
            cuerpo = ("Expertos advierten que Civitas favorece los mensajes que más miedo generan, porque son los que "
                      "más se comparten. En una semana, tres rumores falsos llegaron a millones de personas.")

        def dibujar(c, mouse, t, eventos):
            r = pygame.Rect(0, 0, 760, 560)
            r.center = (ANCHO // 2 - (60 if clave == "titular2" else 0), ALTO // 2 - 20)
            hoja(c, r, color=(220, 214, 196), giro=-1)
            y = parrafo(c, titulo, fuente("mono_negrita", 46), TINTA, r.x + 50, r.y + 50, r.w - 100)
            pygame.draw.line(c, TINTA, (r.x + 50, y + 6), (r.right - 50, y + 6), 3)
            parrafo(c, cuerpo, fuente("narracion", 32), TINTA, r.x + 50, y + 30, r.w - 100)
            if clave == "titular2":
                nota = pygame.Rect(r.right - 150, r.bottom - 230, 280, 230)
                hoja(c, nota, color=(240, 214, 120), giro=6)
                escribir(c, "Si todo cae,", fuente("narracion", 32), TINTA, (nota.centerx, nota.y + 30), "midtop", sombra=False)
                escribir(c, "escucha", fuente("narracion", 32), TINTA, (nota.centerx, nota.y + 70), "midtop", sombra=False)
                escribir(c, f"{self.caso['frecuencia']:.1f} FM", fuente("narracion", 44), ROJO,
                         (nota.centerx, nota.y + 112), "midtop", sombra=False)
                self.marca(c, "IV", (nota.right - 40, nota.y + 36))
            return None

        self.vista(dibujar)
        if clave == "titular2" and not self.sabe_frecuencia:
            self.sabe_frecuencia = True
            self.avisar(f"Anotaste una emisora: {self.caso['frecuencia']:.1f} FM")

    # TELÉFONO (ambientación)
    def ver_telefono(self):
        texto = ("1 mensaje sin escuchar.\n\n"
                 "\"Papá, ¿por qué no contestas? En la escuela todos dicen que mañana cierran la ciudad. "
                 "Lo vi en Civitas... ¿es verdad? Llámame, por favor.\"")
        sonar(self.sonidos, "tecla")

        def dibujar(c, mouse, t, eventos):
            r = pygame.Rect(0, 0, 760, 380)
            r.center = (ANCHO // 2, ALTO // 2 - 30)
            placa(c, r)
            escribir(c, "CONTESTADORA", fuente("mono_negrita", 26), OXIDO, (r.x + 40, r.y + 30))
            parrafo(c, texto, fuente("narracion", 34), BLANCO, r.x + 40, r.y + 80, r.w - 80, letras=int(t * 40))
            return None

        self.vista(dibujar)

    # IV. RADIO (girar el dial hasta la emisora de la nota)
    def pantalla_radio(self):
        ESC = ANCHO / 1280
        centro = (int(960 * ESC), int(469 * ESC))
        radio_dial = int(109 * ESC)
        aguja_x = (int(234 * ESC), int(1046 * ESC))
        aguja_y = (int(217 * ESC), int(269 * ESC))
        giro_max = 300
        mhz_vuelta = 20 / giro_max * 360
        objetivo = self.caso["frecuencia"]
        try:
            fondo = pygame.transform.smoothscale(pygame.image.load(str(RUTA_INTERFAZ / IMAGEN_RADIO)).convert(), (ANCHO, ALTO))
        except (FileNotFoundError, pygame.error):
            fondo = pygame.Surface((ANCHO, ALTO))
            fondo.fill((40, 34, 28))
            pygame.draw.circle(fondo, (80, 70, 60), centro, radio_dial)
            pygame.draw.rect(fondo, (25, 22, 18), (aguja_x[0] - 10, aguja_y[0] - 10,
                                                   aguja_x[1] - aguja_x[0] + 20, aguja_y[1] - aguja_y[0] + 20))
        r = radio_dial
        perilla = pygame.Surface((2 * r, 2 * r), pygame.SRCALPHA)
        perilla.blit(fondo, (0, 0), pygame.Rect(centro[0] - r, centro[1] - r, 2 * r, 2 * r))
        mascara = pygame.Surface((2 * r, 2 * r), pygame.SRCALPHA)
        pygame.draw.circle(mascara, (255, 255, 255, 255), (r, r), r)
        perilla.blit(mascara, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        pygame.draw.line(perilla, (225, 220, 210), (r, 14), (r, 50), 6)

        transmision = ("...aquí Radio Refugio, para quien todavía pueda escucharnos... hay agua y comida en el "
                       f"refugio número {self.caso['refugio']}... repetimos: refugio número {self.caso['refugio']}... "
                       "no crean lo que dice Civitas...")
        estado = {"f": 88.0, "arrastre": False, "ang": 0.0, "sintonizada": None}
        canal = self.sonidos["estatica"].play(loops=-1) if "estatica" in self.sonidos else None
        while True:
            eventos = self.v.eventos()
            mouse = self.v.mouse()
            c = self.v.canvas
            seg = pygame.time.get_ticks() / 1000
            for e in eventos:
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and math.dist(mouse, centro) <= radio_dial:
                    estado["arrastre"] = True
                    estado["ang"] = math.atan2(mouse[1] - centro[1], mouse[0] - centro[0])
                if e.type == pygame.MOUSEMOTION and estado["arrastre"]:
                    ang = math.atan2(mouse[1] - centro[1], mouse[0] - centro[0])
                    cambio = (ang - estado["ang"] + math.pi) % (2 * math.pi) - math.pi
                    estado["ang"] = ang
                    estado["f"] = max(88.0, min(108.0, estado["f"] + math.degrees(cambio) / 360 * mhz_vuelta))
                if e.type == pygame.MOUSEWHEEL:
                    estado["f"] = max(88.0, min(108.0, round(estado["f"] + e.y * 0.1, 1)))
                if e.type == pygame.MOUSEBUTTONUP and e.button == 1:
                    estado["arrastre"] = False
            distancia = abs(estado["f"] - objetivo)
            en_senal = distancia < 0.06
            if en_senal and estado["sintonizada"] is None:
                estado["sintonizada"] = seg
            elif not en_senal:
                estado["sintonizada"] = None

            if canal:
                canal.set_volume(0.12 + 0.88 * min(1, distancia / 1.5))
            c.blit(fondo, (0, 0))
            p = (estado["f"] - 88) / 20
            xa = aguja_x[0] + p * (aguja_x[1] - aguja_x[0])
            pygame.draw.line(c, ROJO, (xa, aguja_y[0]), (xa, aguja_y[1]), 4)
            girada = pygame.transform.rotozoom(perilla, -(-giro_max / 2 + p * giro_max), 1)
            c.blit(girada, girada.get_rect(center=centro))
            escribir(c, f"{estado['f']:.1f} FM", fuente("mono_negrita", 44), PAPEL_CLARO, (40, 30))
            escribir(c, "Gira la perilla con el mouse (o la rueda) · ESC para volver", fuente("mono", 18), GRIS, (40, 96))

            caja = pygame.Rect(0, 0, 1100, 130)
            caja.midbottom = (ANCHO // 2, ALTO - 24)
            placa(c, caja)
            if en_senal:
                letras = int((seg - estado["sintonizada"]) * 26)
                parrafo(c, transmision, fuente("narracion", 32), BLANCO, caja.x + 30, caja.y + 20, caja.w - 60,
                        letras=letras, centrado=True)
                if letras > len(transmision) // 2:
                    self.ganar_pista("radio", f"Radio: \"refugio número {self.caso['refugio']}\"")
            elif distancia < 1:
                escribir(c, "...se escucha una voz entre la estática...", fuente("mono", 24), PAPEL, caja.center, "center", sombra=False)
            else:
                escribir(c, "solo estática", fuente("mono", 24), GRIS, caja.center, "center", sombra=False)

            r_volver = pygame.Rect(ANCHO - 200, 30, 170, 50)
            if (boton(c, r_volver, "Volver", mouse) and clic(eventos)) or tecla(eventos, pygame.K_ESCAPE):
                break
            self.v.mostrar()
        if canal:
            canal.stop()

    # TABLERO: ordenar las 4 pistas con hilo (camino en un grafo)
    def pantalla_tablero(self):
        orden = ["calendario", "foto", "dibujo", "radio"]
        romanos = {"calendario": "I", "foto": "II", "dibujo": "III", "radio": "IV"}
        posiciones = {"foto": (360, 300), "radio": (820, 270), "calendario": (560, 600), "dibujo": (1180, 560)}
        d = self.caso["digitos"]
        detalle = {
            "calendario": f"Día {self.caso['dia']} marcado → {d[0]}",
            "foto": f"Año {self.caso['anio']}, subrayado → {d[1]}",
            "dibujo": f"\"Feliz cumpleaños {self.caso['edad']}\", subrayado → {d[2]}",
            "radio": f"\"Refugio número {self.caso['refugio']}\" → {d[3]}",
        }
        estado = {"arrastre": None, "fallo": 0.0}
        corcho = self.fondo.subsurface(self.zona("tablero").clip(self.fondo.get_rect())).copy()
        corcho = pygame.transform.smoothscale(corcho, (ANCHO - 120, ALTO - 220))
        velo = pygame.Surface(corcho.get_size(), pygame.SRCALPHA)
        velo.fill((20, 14, 8, 160))
        corcho.blit(velo, (0, 0))

        def siguiente_libre():
            """El primer nodo del orden que todavía no tiene hilo hacia el siguiente."""
            for i in range(len(orden) - 1):
                if orden[i + 1] not in self.tablero.vecinos(orden[i]):
                    return i
            return None

        def dibujar(c, mouse, t, eventos):
            c.blit(corcho, (60, 60))
            escribir(c, "TABLERO DE PISTAS", fuente("mono_negrita", 30), AMBAR, (90, 80))
            escribir(c, "Une las pistas con hilo en el orden correcto. Fíjate en los números romanos.",
                     fuente("mono", 18), PAPEL, (90, 122))

            for a, b, _ in self.tablero.aristas():
                hilo(c, posiciones[a], posiciones[b], AMBAR if self.orden_resuelto else ROJO)

            rects = {}
            for clave in orden:
                x, y = posiciones[clave]
                r = pygame.Rect(0, 0, 300, 150)
                r.center = (x, y)
                hoja(c, r, color=PAPEL_CLARO)
                pygame.draw.circle(c, ROJO, (r.centerx, r.y + 6), 8)
                escribir(c, romanos[clave], fuente("narracion", 46), ROJO, (r.x + 20, r.y + 12), sombra=False)
                escribir(c, clave.upper(), fuente("mono_negrita", 18), OXIDO,
                         (r.x + 90, r.y + 26), sombra=False)
                parrafo(c, detalle[clave], fuente("narracion", 28), TINTA, r.x + 20, r.y + 66, r.w - 40)
                rects[clave] = r

            for e in eventos:
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and not self.orden_resuelto:
                    for clave, r in rects.items():
                        if r.collidepoint(mouse):
                            estado["arrastre"] = clave
                if e.type == pygame.MOUSEBUTTONUP and e.button == 1 and estado["arrastre"]:
                    desde = estado["arrastre"]
                    estado["arrastre"] = None
                    for clave, r in rects.items():
                        if r.collidepoint(mouse) and clave != desde:
                            i = siguiente_libre()
                            correcto = i is not None and {desde, clave} == {orden[i], orden[i + 1]}
                            if correcto:
                                self.tablero.agregar_arista(orden[i], orden[i + 1])     # AGREGAR ARISTA (hilo)
                                sonar(self.sonidos, "tecla")
                                if camino_bfs(self.tablero, orden[0], orden[-1]):        # BFS: ¿ya hay camino de I a IV?
                                    self.orden_resuelto = True
                                    sonar(self.sonidos, "pista")
                            else:
                                estado["fallo"] = 1.6
                                sonar(self.sonidos, "error")
            if estado["arrastre"]:
                hilo(c, posiciones[estado["arrastre"]], mouse, ROJO)
            if estado["fallo"] > 0:
                estado["fallo"] -= 1 / 60
                escribir(c, "Ese no es el orden.", fuente("mono_negrita", 22), ROJO, (ANCHO // 2, ALTO - 150), "center")
            if self.orden_resuelto:
                escribir(c, f"¡Lo lograste! La clave es {self.caso['clave']}",
                         fuente("mono_negrita", 34), AMBAR, (ANCHO // 2, ALTO - 150), "center")
            return None

        self.vista(dibujar)

    # COMPUTADOR: CLAVE Y ARCHIVOS SECRETOS
    def pantalla_computador(self):
        estado = {"clave": "", "error": 0.0, "fallos": 0, "abierto": None, "inicio_archivo": 0.0}
        archivos = [
            ("registro", "REGISTRO_PROPAGACION", "Rumor #0417 · el pozo"),
            ("enviados", "MENSAJES_ENVIADOS", "Desde esta terminal"),
            ("personal", "PERSONAL_CIVITAS", "Fichas del equipo"),
        ]

        def marco_crt(c):
            marco = pygame.Rect(140, 90, ANCHO - 280, ALTO - 220)
            pygame.draw.rect(c, (40, 36, 32), marco.inflate(40, 40), border_radius=30)
            pygame.draw.rect(c, (12, 10, 8), marco, border_radius=22)
            return marco

        def lineas_crt(c, marco, t):
            capa = pygame.Surface(marco.size, pygame.SRCALPHA)
            for y in range(0, marco.h, 4):
                pygame.draw.line(capa, (0, 0, 0, 70), (0, y), (marco.w, y))
            c.blit(capa, marco.topleft)

        def dibujar(c, mouse, t, eventos):
            marco = marco_crt(c)
            f = fuente("mono", 24)
            fg = fuente("mono_negrita", 30)

            # 1. CLAVE
            if not self.computador_abierto:
                escribir(c, "CIVITAS · TERMINAL DE INGENIERÍA", fg, CRT, (marco.x + 60, marco.y + 50), sombra=False)
                escribir(c, "Ingrese la clave de acceso (4 dígitos):", f, CRT, (marco.x + 60, marco.y + 140), sombra=False)
                cursor = "_" if (pygame.time.get_ticks() // 400) % 2 == 0 else " "
                texto = (estado["clave"] + cursor)[:4]
                escribir(c, " ".join(texto.ljust(4, "·")), fuente("mono_negrita", 64), CRT,
                         (marco.x + 60, marco.y + 200), sombra=False)
                if estado["fallos"] >= 3:
                    escribir(c, "Ayuda: la clave está en el tablero de pistas.", fuente("mono", 20), CRT_OSCURO,
                             (marco.x + 60, marco.bottom - 60), sombra=False)
                if estado["error"] > 0:
                    estado["error"] -= 1 / 60
                    escribir(c, "ACCESO DENEGADO", fg, ROJO, (marco.x + 60, marco.y + 320), sombra=False)
                for e in eventos:
                    if e.type == pygame.KEYDOWN:
                        if e.unicode.isdigit() and len(estado["clave"]) < 4:
                            estado["clave"] += e.unicode
                            sonar(self.sonidos, "tecla")
                        elif e.key == pygame.K_BACKSPACE:
                            estado["clave"] = estado["clave"][:-1]
                if len(estado["clave"]) == 4:
                    if estado["clave"] == self.caso["clave"]:
                        self.computador_abierto = True
                        sonar(self.sonidos, "pista")
                    else:
                        estado["clave"] = ""
                        estado["error"] = 1.5
                        estado["fallos"] += 1
                        sonar(self.sonidos, "error")
                lineas_crt(c, marco, t)
                return None

            # 2. ESCRITORIO CON ARCHIVOS
            if estado["abierto"] is None:
                escribir(c, "CIVITAS · ARCHIVOS CLASIFICADOS", fg, CRT, (marco.x + 60, marco.y + 40), sombra=False)
                for i, (clave, nombre, desc) in enumerate(archivos):
                    ancho_a = (marco.w - 160 - 2 * 40) // 3
                    r = pygame.Rect(marco.x + 80 + i * (ancho_a + 40), marco.y + 170, ancho_a, 200)
                    encima = r.collidepoint(mouse)
                    pygame.draw.rect(c, (40, 26, 10) if encima else (22, 16, 8), r, border_radius=10)
                    pygame.draw.rect(c, CRT if encima else CRT_OSCURO, r, 2, border_radius=10)
                    carpeta = pygame.Rect(r.x + 28, r.y + 40, 80, 60)
                    pygame.draw.rect(c, CRT, (carpeta.x, carpeta.y - 12, 34, 14), border_radius=3)
                    pygame.draw.rect(c, CRT, carpeta, border_radius=4)
                    if clave in self.archivos_vistos:
                        cx, cy = carpeta.center
                        pygame.draw.lines(c, NEGRO, False, [(cx - 14, cy), (cx - 4, cy + 10), (cx + 16, cy - 12)], 5)
                    escribir(c, nombre, fuente("mono_negrita", 20), CRT, (r.x + 28, r.y + 120), sombra=False)
                    escribir(c, desc, fuente("mono", 17), CRT_OSCURO, (r.x + 28, r.y + 154), sombra=False)
                    if encima and clic(eventos):
                        estado["abierto"] = clave
                        estado["inicio_archivo"] = t
                        self.archivos_vistos.add(clave)
                        sonar(self.sonidos, "tecla")
                escribir(c, "Abre los archivos para saber qué pasó.", fuente("mono", 20), CRT_OSCURO,
                         (marco.centerx, marco.bottom - 50), "center", sombra=False)
                lineas_crt(c, marco, t)
                return None

            # 3. UN ARCHIVO ABIERTO
            ta = t - estado["inicio_archivo"]
            if estado["abierto"] == "registro":
                self.dibujar_registro(c, marco, ta)
            elif estado["abierto"] == "personal":
                if self.dibujar_personal(c, marco, ta, mouse, eventos):
                    self.descubierto = True
                    return "grupo"
            elif estado["abierto"] == "enviados":
                escribir(c, "MENSAJES_ENVIADOS · ÚLTIMAS 24 HORAS", fg, CRT, (marco.x + 60, marco.y + 40), sombra=False)
                filas = [
                    ("19:42", "Firma", "Sobreviviente_27"),
                    ("19:42", "Mensaje", "\"Ayuda, por favor. Somos tres...\""),
                    ("19:42", "Origen real", "ESTA TERMINAL"),
                    ("19:43", "Destino", "Dispositivos cerca del Almacén del Este"),
                    ("19:43", "Estado", "ENTREGADO"),
                ]
                y = marco.y + 120
                for k, (hora, campo, valor) in enumerate(filas):
                    if ta < 0.4 + k * 0.6:
                        break
                    escribir(c, hora, fuente("mono", 24), CRT_OSCURO, (marco.x + 60, y), sombra=False)
                    escribir(c, campo, fuente("mono_negrita", 24), CRT, (marco.x + 180, y), sombra=False)
                    escribir(c, valor, fuente("mono", 24), ROJO if campo == "Origen real" else CRT,
                             (marco.x + 420, y), sombra=False)
                    y += 54
                if ta > 3.6:
                    escribir(c, "Nadie pidió ayuda. El mensaje lo escribió Civitas.", fuente("mono_negrita", 26), ROJO,
                             (marco.x + 60, y + 24), sombra=False)
            b = pygame.Rect(marco.x + 40, marco.bottom - 76, 220, 50)
            if boton(c, b, "< Archivos", mouse) and clic(eventos):
                estado["abierto"] = None
            lineas_crt(c, marco, t)
            return None

        self.vista(dibujar)

    def dibujar_registro(self, c, marco, ta):
        """Evidencia: cómo se regó el rumor del pozo por el grupo, ronda por ronda (BFS),
        y el camino de vuelta hasta Civitas."""
        red = self.red
        fg = fuente("mono_negrita", 30)
        f = fuente("mono", 22)
        escribir(c, "REGISTRO DE PROPAGACIÓN · RUMOR #0417", fg, CRT, (marco.x + 40, marco.y + 24), sombra=False)
        escribir(c, "\"El agua del pozo de la plaza está envenenada.\"", fuente("mono", 20), CRT,
                 (marco.x + 40, marco.y + 66), sombra=False)
        area = pygame.Rect(marco.x + 40, marco.y + 120, marco.w - 440, marco.h - 220)
        ronda_actual = int(ta / 1.1)
        termino = ronda_actual > red["rondas"]
        pos = {p: (area.x + int(x * area.w), area.y + int(y * area.h)) for p, (x, y) in PERSONAS.items()}
        pos[ORIGEN_CIVITAS] = (area.x + 90, area.y + 10)
        camino = camino_al_origen(red["padre"], self.ultimo_alcanzado()) if termino else []

        for a, b in CONFIANZA:
            cortada = (a, b) in red["cortadas"] or (b, a) in red["cortadas"]
            color, ancho = ((60, 60, 60) if cortada else (70, 50, 25)), 2
            na, nb = red["nivel"].get(a), red["nivel"].get(b)
            if na is not None and nb is not None and max(na, nb) <= ronda_actual:
                if red["padre"].get(a) == b or red["padre"].get(b) == a:
                    color, ancho = ROJO, 3
            if a in camino and b in camino and abs(camino.index(a) - camino.index(b)) == 1:
                color, ancho = CRT, 5
            if cortada:
                linea_cortada(c, pos[a], pos[b], color)
            else:
                pygame.draw.line(c, color, pos[a], pos[b], ancho)
        if termino:
            pygame.draw.line(c, CRT, pos[ORIGEN_CIVITAS], pos[red["origen"]], 5)
            caja = pygame.Rect(0, 0, 150, 40)
            caja.center = pos[ORIGEN_CIVITAS]
            pygame.draw.rect(c, ROJO, caja, border_radius=6)
            escribir(c, "CIVITAS", fuente("mono_negrita", 22), NEGRO, caja.center, "center", sombra=False)

        fn = fuente("mono_negrita", 16)
        for p, (x, y) in pos.items():
            if p == ORIGEN_CIVITAS:
                continue
            n = red["nivel"].get(p)
            if n is not None and n <= ronda_actual:
                color = ROJO
            elif p in red["protegidos"] and ronda_actual >= 1:
                color = AZUL
            else:
                color = (90, 80, 70)
            if p == "LÍDER":
                pygame.draw.circle(c, CRT, (x, y), 26, 3)
            pygame.draw.circle(c, color, (x, y), 18)
            pygame.draw.circle(c, NEGRO, (x, y), 18, 2)
            if n is not None and n <= ronda_actual:
                escribir(c, str(n), fn, NEGRO, (x, y), "center", sombra=False)
            escribir(c, "TÚ" if p == "LÍDER" else p, fn, CRT, (x, y + 24), "midtop", sombra=False)

        px = marco.right - 380
        ronda_vista = min(ronda_actual, red["rondas"])
        alcanzados = sum(1 for n in red["nivel"].values() if n <= ronda_vista)
        escribir(c, f"RONDA {ronda_vista}", fg, CRT, (px, marco.y + 120), sombra=False)
        escribir(c, f"Alcanzados: {alcanzados} de {len(PERSONAS)}", f, CRT, (px, marco.y + 170), sombra=False)
        escribir(c, "Rojo: lo creyó", fuente("mono", 18), ROJO, (px, marco.y + 216), sombra=False)
        escribir(c, "Azul: protegido", fuente("mono", 18), AZUL, (px, marco.y + 242), sombra=False)
        escribir(c, "Gris: no le llegó", fuente("mono", 18), (150, 140, 120), (px, marco.y + 268), sombra=False)
        if termino:
            if self.consecuencia_red is None:
                self.aplicar_consecuencia_red()
            parrafo(c, red["texto"], fuente("mono", 18), CRT, px, marco.y + 310, 340)
            escribir(c, "ORIGEN:", fuente("mono_negrita", 22), ROJO, (px, marco.bottom - 190), sombra=False)
            escribir(c, "TERMINAL CIVITAS", fuente("mono_negrita", 22), ROJO, (px, marco.bottom - 160), sombra=False)

    def foto_ficha(self, rol, tam):
        """La foto de la ficha: Assets/Interfaz/ficha_<rol>.png (si no está, una silueta)."""
        if not hasattr(self, "_fotos"):
            self._fotos = {}
        if rol not in self._fotos:
            nombre = {"LÍDER": "lider", "PERIODISTA": "periodista", "INFLUENCER": "influencer",
                      "CIUDADANO": "ciudadano"}[rol]
            try:
                img = pygame.image.load(str(RUTA_INTERFAZ / f"ficha_{nombre}.png")).convert()
                escala = max(tam[0] / img.get_width(), tam[1] / img.get_height())
                img = pygame.transform.smoothscale(img, (int(img.get_width() * escala), int(img.get_height() * escala)))
                recorte = pygame.Surface(tam)
                recorte.blit(img, ((tam[0] - img.get_width()) // 2, (tam[1] - img.get_height()) // 2))
                self._fotos[rol] = recorte
            except (FileNotFoundError, pygame.error):
                self._fotos[rol] = None
        return self._fotos[rol]

    def dibujar_personal(self, c, marco, ta, mouse, eventos):
        """Las 4 fichas. Devuelve True cuando el jugador hace clic en la suya."""
        escribir(c, "PERSONAL_CIVITAS · ACCESO RESTRINGIDO", fuente("mono_negrita", 30), CRT,
                 (marco.x + 40, marco.y + 24), sombra=False)
        escribir(c, "Haz clic en una ficha para abrirla.", fuente("mono", 18), CRT_OSCURO,
                 (marco.x + 40, marco.y + 64), sombra=False)
        if not hasattr(self, "fichas_abiertas"):
            self.fichas_abiertas = set()
        ancho = (marco.w - 80) // 4
        for i, (rol, puesto, desc) in enumerate(FICHAS):
            if ta < 0.3 + i * 0.4:
                continue
            r = pygame.Rect(marco.x + 40 + i * ancho, marco.y + 100, ancho - 20, marco.h - 210)
            abierta = rol in self.fichas_abiertas
            encima = r.collidepoint(mouse)
            pygame.draw.rect(c, (40, 26, 10) if encima else (30, 20, 10), r, border_radius=8)
            pygame.draw.rect(c, CRT if encima else CRT_OSCURO, r, 2, border_radius=8)
            foto = pygame.Rect(r.x + 24, r.y + 22, r.w - 48, 190)
            img = self.foto_ficha(rol, foto.size)
            if img is not None:
                c.blit(img, foto)
            else:
                pygame.draw.rect(c, (60, 45, 28), foto, border_radius=6)
                pygame.draw.circle(c, (25, 18, 10), (foto.centerx, foto.y + 70), 34)
                pygame.draw.ellipse(c, (25, 18, 10), (foto.centerx - 60, foto.y + 110, 120, 90))
                pygame.draw.rect(c, (30, 20, 10), (foto.x, foto.bottom, foto.w, 24))
            pygame.draw.rect(c, CRT_OSCURO, foto, 2)
            escribir(c, f"EMPLEADO #{i + 1:03d}", fuente("mono_negrita", 18), CRT, (r.x + 20, r.y + 226), sombra=False)
            if abierta or encima:
                parrafo(c, puesto.upper(), fuente("mono_negrita", 18), CRT, r.x + 20, r.y + 258, r.w - 40)
                parrafo(c, desc, fuente("mono", 17), PAPEL, r.x + 20, r.y + 314, r.w - 40)
            else:
                escribir(c, "[ clic para abrir ]", fuente("mono", 17), CRT_OSCURO, (r.x + 20, r.y + 262), sombra=False)
            if encima and clic(eventos):
                self.fichas_abiertas.add(rol)
                sonar(self.sonidos, "tecla")
                if rol == self.personaje:
                    return True
        return False

    def ultimo_alcanzado(self):
        nivel = self.red["nivel"]
        return max(sorted(nivel), key=lambda p: nivel[p])

    def aplicar_consecuencia_red(self):
        """El BFS decide las consecuencias: cuantas más personas lo creyeron, peor para el grupo."""
        proporcion = self.red["alcanzados"] / len(PERSONAS)
        if proporcion <= 0.35:
            efectos = {"Confianza": +5, "Caos": -5}
        else:
            efectos = {"Cohesión": -round(10 * proporcion), "Caos": +round(10 * proporcion)}
        self.consecuencia_red = efectos
        if self.indicadores is not None:
            self.indicadores.aplicar(efectos)

    # VIDEO CON SUBTÍTULOS EN CÓDIGO (igual que en el Evento 1)
    def video(self, guion, al_final=None):
        """Reproduce el video del guion con sus subtítulos. Al terminar deja quieto el último cuadro y,
        si se da al_final(pantalla, rect, s, seg), lo dibuja encima hasta que el jugador haga clic."""
        import cv2
        from Eventos import Evento1_Pozo as E1
        ruta = RUTA_VIDEOS / guion["video"]
        video = cv2.VideoCapture(str(ruta))
        fps = video.get(cv2.CAP_PROP_FPS) or 30
        ruta_audio = ruta.with_suffix(".mp3")
        if ruta_audio.exists():
            try:
                pygame.mixer.music.load(str(ruta_audio))
                pygame.mixer.music.play()
            except pygame.error:
                pass
        inicio = pygame.time.get_ticks()
        leidos, imagen, tam, cuadro = 0, None, None, None
        termino = not video.isOpened()
        fin_video = None
        while True:
            pantalla = pygame.display.get_surface()
            rect = E1.rect_video(pantalla)
            s = rect.h / E1.REF_ALTO
            t = (pygame.time.get_ticks() - inicio) / 1000
            eventos = self.v.eventos()
            nuevo = False
            while not termino and leidos <= int(t * fps):
                ok, sig = video.read()
                if not ok:
                    termino = True
                    break
                cuadro, leidos, nuevo = sig, leidos + 1, True
            if termino and fin_video is None:
                fin_video = t
            if cuadro is not None and (nuevo or tam != rect.size):
                peq = cv2.cvtColor(cv2.resize(cuadro, rect.size, interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB)
                imagen = pygame.image.frombuffer(peq.tobytes(), rect.size, "RGB")
                tam = rect.size
            pantalla.fill((0, 0, 0))
            if imagen is not None:
                pantalla.blit(imagen, rect)
            else:
                fondo = pygame.transform.smoothscale(self.fondo, rect.size)
                pantalla.blit(fondo, rect)
            E1.dibujar_subtitulos(pantalla, rect, s, t, guion["subtitulos"])
            listo = fin_video is not None and t - fin_video > 0.3
            if listo and al_final:
                al_final(pantalla, rect, s, t - fin_video)
            elif listo and (pygame.time.get_ticks() // 600) % 2 == 0:
                ayuda = E1.fuente("mono", 30 * s).render("Haz clic para continuar", True, GRIS)
                pantalla.blit(ayuda, ayuda.get_rect(center=(rect.centerx, rect.y + int(0.95 * rect.h))))
            pygame.display.update()
            self.v.reloj.tick(60)
            if clic(eventos) or tecla(eventos, pygame.K_SPACE, pygame.K_RETURN):
                if listo:
                    break
                if not termino:                       # saltar el video
                    termino, fin_video = True, t
                    video.set(cv2.CAP_PROP_POS_FRAMES, max(0, int(video.get(cv2.CAP_PROP_FRAME_COUNT)) - 2))
                    ok, sig = video.read()
                    if ok:
                        cuadro, tam = sig, None
        video.release()
        pygame.mixer.music.stop()

    # FINAL: CONFRONTACIÓN, REACCIÓN DEL GRUPO Y CLIFFHANGER
    def final(self):
        valores = self.indicadores.copia() if self.indicadores is not None else {"Confianza": 50, "Caos": 50, "Cohesión": 50}
        puntaje = valores["Confianza"] + valores["Cohesión"] - valores["Caos"]
        if self.dato_torre:
            puntaje += BONO_TORRE                    # les contaste cómo detener a Civitas
        if puntaje < 40:
            clave = "disuelto"
        elif puntaje < 75:
            clave = "desconfianza"
        else:
            clave = "confian"
        datos = FINALES[clave]

        logros = []
        if self.resultado_evento1 and self.resultado_evento1.startswith("VERIFICAR"):
            logros.append("Verificaste antes de hablar")
        if self.red["alcanzados"] <= 4:
            logros.append("El rumor no llegó lejos")
        if self.resultado_evento1 == "COMPARTIR":
            logros.append("El rumor salió de ti")
        logros.append("Descubriste la verdad sobre Civitas")
        if self.dato_torre:
            logros.append("Encontraste cómo detener a Civitas")

        # 1. llega el grupo y ve la pantalla
        self.video(CONFRONTACION)

        # 2. la página que explica lo que pasó
        texto = VERDAD + "\n\n" + (VERDAD_TORRE if self.dato_torre else VERDAD_SIN_TORRE)

        def dibujar(c, seg):
            c.blit(self.fondo, (0, 0))
            c.blit(self.oscuro, (0, 0))
            nota = pygame.Rect(0, 0, 940, 620)
            nota.center = (ANCHO // 2, ALTO // 2 - 30)
            hoja(c, nota, color=(226, 214, 184), giro=-1)
            escribir(c, "Entiendes lo que pasó", fuente("mono_negrita", 40), TINTA, (nota.x + 60, nota.y + 55), sombra=False)
            pygame.draw.line(c, OXIDO, (nota.x + 60, nota.y + 118), (nota.right - 60, nota.y + 118), 3)
            y = parrafo(c, texto, fuente("narracion", 38), TINTA, nota.x + 60, nota.y + 150, nota.w - 120,
                        letras=int(seg * 45))
            if seg * 45 > len(texto) + 10:
                escribir(c, VERDAD_FINAL, fuente("narracion", 46), ROJO, (nota.centerx, y + 20), "midtop", sombra=False)

        self.esperar_pantalla(dibujar, len(texto) / 45 + 0.6)

        # 2. la reacción (uno de los 3 videos) y el resultado encima del último cuadro
        from Eventos import Evento1_Pozo as E1

        def resultado(pantalla, rect, s, seg):
            velo = pygame.Surface(rect.size, pygame.SRCALPHA)
            velo.fill((0, 0, 0, min(190, int(seg * 95))))
            pantalla.blit(velo, rect)
            escribir(pantalla, datos["titulo"], E1.fuente("mono_negrita", 70 * s), datos["color"],
                     (rect.centerx, rect.y + int(330 * s)), "midtop")
            if seg > 0.8:
                y = rect.y + int(470 * s)
                escribir(pantalla, "LOGROS", E1.fuente("mono_negrita", 26 * s), OXIDO, (rect.centerx, y), "midtop")
                for k, logro in enumerate(logros):
                    escribir(pantalla, "» " + logro, E1.fuente("mono", 30 * s), AMBAR,
                             (rect.centerx, y + int((50 + k * 44) * s)), "midtop")
                escribir(pantalla, f"Puntaje del grupo: {puntaje}", E1.fuente("mono_negrita", 28 * s), PAPEL,
                         (rect.right - int(40 * s), rect.y + int(36 * s)), "topright")
                E1.dibujar_indicadores(pantalla.subsurface(rect), valores)
            if seg > 1.5 and (pygame.time.get_ticks() // 600) % 2 == 0:
                ayuda = E1.fuente("mono", 28 * s).render("Haz clic para continuar", True, GRIS)
                pantalla.blit(ayuda, ayuda.get_rect(center=(rect.centerx, rect.y + int(0.95 * rect.h))))

        self.video(datos, al_final=resultado)

        # 3. continuará
        inicio = pygame.time.get_ticks()
        while True:
            eventos = self.v.eventos()
            seg = (pygame.time.get_ticks() - inicio) / 1000
            c = self.v.canvas
            c.fill(NEGRO)
            escribir(c, datos["cierre"], fuente("narracion", 46), BLANCO, (ANCHO // 2, ALTO // 2 - 80), "midtop")
            if seg > 1.5:
                img = fuente("mono_negrita", 80).render("CONTINUARÁ...", True, ROJO)
                img.set_alpha(min(255, int((seg - 1.5) * 200)))
                c.blit(img, img.get_rect(center=(ANCHO // 2, ALTO // 2 + 60)))
            if seg > 2.5 and (clic(eventos) or tecla(eventos, pygame.K_SPACE, pygame.K_RETURN)):
                break
            self.v.mostrar()
        return {"final": clave, "puntaje": puntaje, "alcanzados": self.red["alcanzados"],
                "rondas": self.red["rondas"], "logros": logros, "indicadores": self.indicadores}


def estrella(superficie, centro, radio, color):
    """Estrella de 5 puntas (la letra de la fuente no trae el símbolo)."""
    puntos = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rr = radio if i % 2 == 0 else radio * 0.45
        puntos.append((centro[0] + rr * math.cos(ang), centro[1] + rr * math.sin(ang)))
    pygame.draw.polygon(superficie, color, puntos)


def hilo(superficie, a, b, color):
    """Hilo rojo un poco caído entre dos puntos."""
    puntos = []
    for i in range(21):
        t = i / 20
        x = a[0] + (b[0] - a[0]) * t
        y = a[1] + (b[1] - a[1]) * t + math.sin(math.pi * t) * 18
        puntos.append((x, y))
    pygame.draw.lines(superficie, color, False, puntos, 3)


def linea_cortada(superficie, a, b, color):
    largo = math.dist(a, b)
    for d in range(0, int(largo), 14):
        t1, t2 = d / largo, min(d + 6, largo) / largo
        pygame.draw.line(superficie, color, (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1),
                         (a[0] + (b[0] - a[0]) * t2, a[1] + (b[1] - a[1]) * t2), 2)


# PARA USAR DESDE EL JUEGO
def jugar(display, canvas, indicadores=None, resultado_evento1="VERIFICAR_FALSO", personaje="LÍDER"):
    """indicadores: los del Evento 1. resultado_evento1: la hoja del árbol que eligió el jugador.
    personaje: LÍDER, PERIODISTA, INFLUENCER o CIUDADANO (decide cuál ficha es la suya)."""
    pygame.display.set_mode(pygame.display.get_surface().get_size(), pygame.RESIZABLE)
    return Oficina(indicadores, resultado_evento1, personaje).jugar()


if __name__ == "__main__":
    # PRUEBA RÁPIDA DEL FINAL
    # 1 = el grupo se disuelve, 2 = te dejan pero desconfían, 3 = confían en ti
    # Enter sin número = jugar el Evento 3 completo
    opcion = input("Final (1, 2, 3) o Enter para jugar todo: ").strip()

    pygame.init()
    pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
    pygame.display.set_caption("The Leader - La oficina")
    from Eventos import Evento1_Pozo

    if opcion in ("1", "2", "3"):
        valores = {"1": (20, 80, 20), "2": (50, 50, 50), "3": (80, 20, 80)}[opcion]
        indicadores = Evento1_Pozo.Indicadores(*valores)   # confianza, caos, cohesión
        Oficina(indicadores, "VERIFICAR_FALSO").final()
    else:
        print(jugar(None, None, Evento1_Pozo.Indicadores(), random.choice(
            ["COMPARTIR", "IGNORAR", "REPORTAR", "VERIFICAR_FALSO", "VERIFICAR_VERDADERO"])))