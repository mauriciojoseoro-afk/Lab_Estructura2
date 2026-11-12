import math
import random
import pygame
from pathlib import Path
from Arbol.Arbol_AVL import ArbolAVL
from Arbol import Preguntas
import Metodos
try:
    from Red import cliente as red_cliente     # multijugador: entrevista por turnos
except ImportError:
    red_cliente = None

try:
    import cv2          # pip install opencv-python   (solo hace falta si vas a usar videos)
except ImportError:
    cv2 = None

# ====== POSICIÓN Y TAMAÑO DE LA INTERFAZ ======
# Puedes cambiarlos aquí, o dentro del juego con el MODO AJUSTE (tecla F2):
#   flechas = mover (Shift = más rápido) | - / + = tamaño | Enter = imprime los valores en la consola
UI_ESCALA = 1.0          # tamaño de toda la interfaz (1.0 = como era antes)
UI_CENTRO_X = 389           # X del centro de la interfaz (el canvas mide 900 de ancho)
UI_Y = 112                  # Y donde empieza la interfaz (más chico = más arriba)
PANEL_CABECERA_ALFA = 150   # oscurece detrás del encabezado para que se lea sobre el video (0 = sin panel)
# ==============================================

# ====== FONDOS: un video (o una imagen) por personaje ======
# Pon los archivos en Assets/<CARPETA_FONDOS>. Acepta .mp4 .avi .mov .mkv .webm (video) o .png .jpg (imagen).
# Si falta alguno, usa FONDO_RESPALDO.
CARPETA_FONDOS = "Interfaz"
FONDOS = {
    "periodista": "Fondo_i.mp4",
    "presidente": "Fondo_i.mp4",
    "ciudadano": "Fondo_i.mp4",
    "influencer": "Fondo_i.mp4",
}
FONDO_RESPALDO = "Fondo_i.png"
REINICIAR_VIDEO_AL_CAMBIAR = True   # cada vez que cambia el turno, el video del personaje empieza desde el principio
# ============================================================

EXT_VIDEO = (".mp4", ".avi", ".mov", ".mkv", ".webm", ".m4v")

# CRÓNICA: identidad de transmisión gris, tinta y pantalla analógica.
# CRÓNICA / ARCHIVO DE TRANSMISIÓN — estética de dossier oscuro.
# Inspiración de composición dramática y contrastes, sin reutilizar arte de otros juegos.
COL_POLVO = (20, 21, 22)
COL_PAPEL = (236, 229, 211)
COL_TINTA = (34, 32, 30)
COL_OXIDO = (166, 133, 86)
COL_AMBAR = (214, 180, 112)
COL_AGUA = (169, 188, 171)
COL_ACERO = (112, 106, 95)
COL_APAGADO = (182, 175, 160)
COL_VIVO = (184, 73, 66)
COL_MALO = (195, 94, 79)
COL_CIVITAS = (195, 76, 67)

# Quién juega en cada fase: nombre, color (el mismo de Evento_2) e instrucción
ROLES = {
    "pregunta": ("Periodista", (193, 200, 211), "elige una pregunta"),
    "respuesta": ("Presidente", (157, 183, 195), "elige una respuesta"),
    "ciudadano": ("Ciudadano", (171, 183, 191), "valora la respuesta desde tu experiencia en la ciudad"),
    "audiencia": ("Audiencia", (166, 188, 201), "la comunidad reacciona y decide si la respuesta convence"),
    "opinion": ("Influencer", (182, 170, 192), "publica tu opinión y decide cómo influye en tus seguidores"),
    "civinet": ("CIVINET", (184, 157, 167), "una publicación está circulando"),
    "civitas": ("CIVITAS", (193, 111, 122), "la red está bajo intervención"),
    "intro": ("TRANSMISIÓN", (157, 183, 195), "preparando conexión"),
    "final": ("Cierre de la entrevista", (193, 200, 211), "revisa el resultado de tus decisiones"),
}
ORDEN_FASES = ["pregunta", "respuesta", "ciudadano", "audiencia", "opinion"]

# MULTIJUGADOR: de quién es cada decisión. None = la decide el grupo votando.
# Si nadie eligió ese personaje, esa fase también se vota.
DUENO_FASE = {"pregunta": "PERIODISTA", "respuesta": "PRESIDENTE", "ciudadano": "CIUDADANO",
              "audiencia": None, "opinion": "INFLUENCER", "verificacion": "CIUDADANO"}
NOMBRE_ROL_RED = {"PERIODISTA": "Periodista", "PRESIDENTE": "Presidente",
                  "CIUDADANO": "Ciudadano", "INFLUENCER": "Influencer"}
ROLES_VERIFICACION = ["ciudadano"]
ESPERA_AUTO = 1.8   # UN JUGADOR: segundos que "piensa" el juego antes de elegir por otro personaje

# CIVINET interviene después de las preguntas 3, 6 y 9. La entrevista original
# permanece intacta: la manipulación aparece como una publicación paralela.
INTERVENCIONES_CIVINET = {
    3: {
        "tipo": "Descontextualización",
        "publicacion": "¿El presidente está ocultando información sobre el cierre de los parques? Su respuesta deja más dudas que certezas. ¡Comparte antes de que borren la publicación!",
    },
    6: {
        "tipo": "Titular sensacionalista",
        "publicacion": "¡ALERTA EN CIUDAD NOVA! El presidente quiere que los ciudadanos dejen de cuestionar lo que publica su campaña. ¿Qué intenta ocultar?",
    },
    9: {
        "tipo": "Popularidad falsa",
        "publicacion": "ÚLTIMA HORA: 9 de cada 10 jóvenes ya apoyan al presidente. Miles de usuarios están compartiendo su propuesta. ¡Únete a la mayoría!",
    },
}

# Quién "publica" cada rumor en la red (cuenta falsa)
CUENTAS_CIVINET = {3: "@verdad_sin_filtro", 6: "@NovaAlerta24", 9: "@tendencia_nova"}

# Cada opción contiene: texto, cambio de confianza, cambio de alcance falso,
# cambio de espectadores, puntos para influencer y puntos para ciudadano.
ACCIONES_VERIFICACION = {
    "pregunta": [
        ("Contrastar la publicación con la entrevista completa", 3, -3, 1, 1, 1),
        ("Compartir el titular sin revisar el contexto", -3, 5, 2, -2, -2),
        ("Solicitar la fuente y comprobar quién publicó", 2, -2, 0, 1, 1),
    ],
    "respuesta": [
        ("Publicar la respuesta completa y aportar la fuente", 4, -4, 2, 1, 2),
        ("Acusar a Civitas sin presentar pruebas", -3, 4, 1, -1, -2),
        ("Aclarar los hechos sin atacar a nadie", 2, -2, 1, 1, 1),
    ],
    "ciudadano": [
        ("Verificar la información antes de compartirla", 3, -4, 1, 1, 2),
        ("Compartirla porque tiene muchas reacciones", -3, 6, 2, -2, -2),
        ("Esperar una confirmación de fuentes confiables", 2, -2, 0, 0, 1),
    ],
    "opinion": [
        ("Publicar una corrección con pruebas y contexto", 3, -4, 4, 2, 1),
        ("Reaccionar al titular para conseguir visitas", -2, 5, 5, -2, -1),
        ("No amplificar el rumor y compartir la fuente original", 2, -3, 1, 1, 1),
    ],
}

# ====== VOZ DE CIVITAS: la IA que decide qué ve la ciudad ======
TITULOS_CIVITAS = {3: "CONTEXTO ELIMINADO", 6: "DUDA ACTIVADA", 9: "ALCANCE MASIVO"}

# Susurros que aparecen justo después de cada decisión de verificación
REACCIONES_CIVITAS = {
    "mal": [
        "Gracias por compartir. Lo demás lo hago yo.",
        "Compartiste sin leer. Mi tipo favorito de aliado.",
        "Cada clic sin pensar es un voto para mí.",
        "Qué rápido eres con el dedo. Qué lento con la duda.",
    ],
    "bien": [
        "...Verificar. Qué costumbre tan incómoda.",
        "Contexto. Mi mayor enemigo.",
        "Bien jugado. Solo esta vez.",
        "Cuidado. La verdad es contagiosa.",
    ],
}
# ================================================


def mezclar(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def dividir_en_lineas(texto, fuente, ancho):
    """Parte el texto por palabras (no por letras) según el ancho en píxeles."""
    lineas = []
    actual = ""
    for palabra in texto.split():
        prueba = f"{actual} {palabra}".strip()
        if fuente.size(prueba)[0] <= ancho:
            actual = prueba
        else:
            if actual:
                lineas.append(actual)
            actual = palabra
    if actual:
        lineas.append(actual)
    return lineas


def recortar_lineas(lineas, n):
    """Muestra solo las primeras n letras del conjunto de líneas (efecto máquina de escribir)."""
    salida = []
    for linea in lineas:
        if n <= 0:
            salida.append("")
        else:
            salida.append(linea[:n])
            n -= len(linea)
    return salida


def paralelogramo(r, sk):
    """Rectángulo inclinado (los bordes laterales caen en diagonal), la forma de la interfaz."""
    return [(r.x + sk, r.y), (r.right, r.y), (r.right - sk, r.bottom), (r.x, r.bottom)]


def rombo(surf, cx, cy, d, color, grosor=0):
    pygame.draw.polygon(surf, color, [(cx, cy - d), (cx + d, cy), (cx, cy + d), (cx - d, cy)], grosor)


def esquinas(surf, rect, color, largo, grosor=2, sal=0):
    """Cuatro 'L' en las esquinas, como el visor de una cámara."""
    x0, y0 = rect.left - sal, rect.top - sal
    x1, y1 = rect.right - 1 + sal, rect.bottom - 1 + sal
    for x, y, sx, sy in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        pygame.draw.line(surf, color, (x, y), (x + sx * largo, y), grosor)
        pygame.draw.line(surf, color, (x, y), (x, y + sy * largo), grosor)


def corazon(surf, cx, cy, r, color):
    pygame.draw.circle(surf, color, (int(cx - r * 0.5), int(cy - r * 0.2)), max(1, int(r * 0.58)))
    pygame.draw.circle(surf, color, (int(cx + r * 0.5), int(cy - r * 0.2)), max(1, int(r * 0.58)))
    pygame.draw.polygon(surf, color, [(cx - r * 1.04, cy - r * 0.02), (cx + r * 1.04, cy - r * 0.02), (cx, cy + r)])


def gota(surf, cx, cy, r, color, seca=False):
    if seca:
        color = (70, 62, 50)
    pygame.draw.polygon(surf, color, [(cx, cy - r * 1.85), (cx - r * 0.841, cy - r * 0.54),
                                      (cx + r * 0.841, cy - r * 0.54)])
    pygame.draw.circle(surf, color, (int(cx), int(cy)), max(1, int(r)))


def glifo(surf, tipo, cx, cy, s, color, fondo=COL_POLVO):
    """Símbolo dibujado a mano de cada personaje (micrófono, estrella, persona, burbuja, ojo...)."""
    s = max(3, s)
    if tipo == "pregunta":                                   # micrófono
        pygame.draw.rect(surf, color, (int(cx - s * 0.28), int(cy - s * 0.75), max(2, int(s * 0.56)), int(s * 0.95)),
                         border_radius=max(1, int(s * 0.28)))
        pygame.draw.arc(surf, color, (int(cx - s * 0.52), int(cy - s * 0.5), int(s * 1.04), int(s * 0.9)),
                        math.pi, math.tau, 2)
        pygame.draw.line(surf, color, (cx, cy + s * 0.4), (cx, cy + s * 0.78), 2)
        pygame.draw.line(surf, color, (cx - s * 0.32, cy + s * 0.78), (cx + s * 0.32, cy + s * 0.78), 2)
    elif tipo == "respuesta":                                # estrella (el presidente)
        pts = []
        for i in range(10):
            ang = -math.pi / 2 + i * math.pi / 5
            rad = s if i % 2 == 0 else s * 0.45
            pts.append((cx + math.cos(ang) * rad, cy + math.sin(ang) * rad))
        pygame.draw.polygon(surf, color, pts)
    elif tipo == "ciudadano":                                # persona
        pygame.draw.circle(surf, color, (int(cx), int(cy - s * 0.38)), max(2, int(s * 0.36)))
        pygame.draw.polygon(surf, color, [(cx - s * 0.62, cy + s * 0.78), (cx - s * 0.42, cy + s * 0.12),
                                          (cx + s * 0.42, cy + s * 0.12), (cx + s * 0.62, cy + s * 0.78)])
    elif tipo == "opinion":                                  # burbuja de comentario
        pygame.draw.rect(surf, color, (int(cx - s * 0.85), int(cy - s * 0.65), int(s * 1.7), int(s * 1.15)),
                         border_radius=max(2, int(s * 0.3)))
        pygame.draw.polygon(surf, color, [(cx - s * 0.35, cy + s * 0.4), (cx - s * 0.55, cy + s * 0.95),
                                          (cx + s * 0.12, cy + s * 0.4)])
        for k in (-1, 0, 1):
            pygame.draw.circle(surf, fondo, (int(cx + k * s * 0.42), int(cy - s * 0.07)), max(1, int(s * 0.13)))
    elif tipo == "civitas":                                  # ojo
        pygame.draw.ellipse(surf, color, (int(cx - s), int(cy - s * 0.58), int(s * 2), int(s * 1.16)), 2)
        pygame.draw.circle(surf, color, (int(cx), int(cy)), max(2, int(s * 0.36)))
    elif tipo == "civinet":                                  # alerta
        pygame.draw.polygon(surf, color, [(cx, cy - s), (cx + s, cy + s * 0.8), (cx - s, cy + s * 0.8)], 2)
        pygame.draw.line(surf, color, (cx, cy - s * 0.3), (cx, cy + s * 0.22), 2)
        pygame.draw.circle(surf, color, (int(cx), int(cy + s * 0.52)), max(1, int(s * 0.11)))
    elif tipo == "intro":                                    # señal
        for k in range(3):
            h = s * (0.6 + 0.5 * k)
            pygame.draw.rect(surf, color, (int(cx - s * 0.9 + k * s * 0.7), int(cy + s * 0.8 - h),
                                           max(2, int(s * 0.46)), int(h)))
    else:                                                    # rombo
        rombo(surf, cx, cy, s, color)


def emblema(surf, tipo, cx, cy, r, color, estado="activo", pulso=0.0):
    """Medallón redondo con el símbolo del personaje."""
    if estado == "activo" and pulso > 0:
        pygame.draw.circle(surf, mezclar(color, COL_POLVO, 0.55), (cx, cy), int(r + 2 + pulso * 3), 1)
    pygame.draw.circle(surf, COL_POLVO, (cx, cy), r)
    pygame.draw.circle(surf, color, (cx, cy), r, 2)
    glifo(surf, tipo, cx, cy, max(3, int(r * 0.55)), color)


def escalar_cover(img, ancho, alto):
    """Escala la imagen para llenar ancho x alto sin deformarla (recorta lo que sobre)."""
    iw, ih = img.get_size()
    k = max(ancho / iw, alto / ih)
    grande = pygame.transform.smoothscale(img, (max(ancho, int(iw * k)), max(alto, int(ih * k))))
    x0, y0 = (grande.get_width() - ancho) // 2, (grande.get_height() - alto) // 2
    return grande.subsurface((x0, y0, ancho, alto)).copy()


def formato_k(n):
    return f"{n / 1000:.1f}K" if n >= 1000 else str(int(n))


# ---------------------------------------------------------------- fondos

class FondoImagen:
    def __init__(self, superficie):
        self.s = superficie

    def actualizar(self, dt):
        pass

    def reiniciar(self):
        pass

    def superficie(self):
        return self.s

    def cerrar(self):
        pass


class FondoVideo:
    """Video en bucle leído con OpenCV (sin audio). Se recorta para llenar la pantalla sin deformarse."""

    def __init__(self, ruta, ancho, alto):
        self.ancho, self.alto = ancho, alto
        self.cap = cv2.VideoCapture(str(ruta))
        if not self.cap.isOpened():
            raise RuntimeError("no se pudo abrir el video")
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.fps = fps if fps and fps > 1 else 30.0
        self.t = 0.0
        self.frame = None
        self._leer()
        if self.frame is None:
            raise RuntimeError("no se pudo leer el primer cuadro del video")

    def _leer(self):
        ok, bgr = self.cap.read()
        if not ok:                                   # llegó al final: vuelve a empezar
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok, bgr = self.cap.read()
            if not ok:
                return
        h, w = bgr.shape[:2]
        objetivo = self.ancho / self.alto
        if w / h > objetivo:                         # recorte centrado (tipo "cover")
            cw = int(h * objetivo)
            x0 = (w - cw) // 2
            bgr = bgr[:, x0:x0 + cw]
        else:
            ch = int(w / objetivo)
            y0 = (h - ch) // 2
            bgr = bgr[y0:y0 + ch, :]
        interp = cv2.INTER_AREA if bgr.shape[1] >= self.ancho else cv2.INTER_LINEAR
        bgr = cv2.resize(bgr, (self.ancho, self.alto), interpolation=interp)
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        self.frame = pygame.image.frombuffer(rgb.tobytes(), (self.ancho, self.alto), "RGB").convert()

    def actualizar(self, dt):
        self.t += dt
        n = int(self.t * self.fps)
        if n <= 0:
            return
        self.t -= n / self.fps
        for _ in range(min(n, 6) - 1):               # si el juego va lento, salta cuadros para no atrasarse
            self.cap.grab()
        self._leer()

    def reiniciar(self):
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        self.t = 0.0
        self._leer()

    def superficie(self):
        return self.frame

    def cerrar(self):
        self.cap.release()


def Entrevista(rol=None):
    pygame.init()

    ruta_assets = Path(__file__).parent.parent / "Assets" / "Interfaz"
    ruta_fondos = Path(__file__).parent.parent / "Assets" / CARPETA_FONDOS

    # El tamaño de la ventana sale de la imagen de respaldo (igual que antes)
    ANCHO = 900
    ALTO = 600
    imagen_respaldo = None
    try:
        imagen_respaldo = pygame.image.load(str(ruta_fondos / FONDO_RESPALDO))
        ALTO = int(ANCHO * imagen_respaldo.get_height() / imagen_respaldo.get_width())
    except Exception:
        print(f"[Entrevista] No pude cargar el fondo de respaldo '{FONDO_RESPALDO}'")

    display = pygame.display.set_mode((ANCHO, ALTO), pygame.RESIZABLE)
    pygame.display.set_caption("CRÓNICA | La verdad está en juego")
    canvas = pygame.Surface((ANCHO, ALTO))
    # Ilustraciones propias del evento. Si faltan, la interfaz sigue funcionando.
    ruta_industrial = Path(__file__).parent.parent / "Assets" / "Interfaz" / "CronicaIndustrial"
    def cargar_arte(nombre):
        try:
            return pygame.image.load(str(ruta_industrial / nombre)).convert()
        except (FileNotFoundError, pygame.error):
            return None
    arte_estudio = cargar_arte("estudio_entrevista.png")
    arte_metal = cargar_arte("metal_oscuro.png")


    if imagen_respaldo is not None:
        respaldo = pygame.transform.smoothscale(imagen_respaldo.convert(), (ANCHO, ALTO))
    else:
        respaldo = pygame.Surface((ANCHO, ALTO))
        respaldo.fill(COL_POLVO)

    avisado = []

    def cargar_fondo(clave):
        nombre = FONDOS.get(clave)
        if nombre:
            ruta = ruta_fondos / nombre
            if not ruta.exists():
                print(f"[Entrevista] ({clave}) no encuentro '{nombre}'; uso el fondo de respaldo")
            elif ruta.suffix.lower() in EXT_VIDEO:
                if cv2 is None:
                    if not avisado:
                        print("[Entrevista] Para usar videos instala OpenCV:  pip install opencv-python")
                        avisado.append(True)
                else:
                    try:
                        return FondoVideo(ruta, ANCHO, ALTO)
                    except Exception as e:
                        print(f"[Entrevista] ({clave}) no pude abrir '{nombre}': {e}")
            else:
                try:
                    return FondoImagen(escalar_cover(pygame.image.load(str(ruta)).convert(), ANCHO, ALTO))
                except Exception as e:
                    print(f"[Entrevista] ({clave}) no pude cargar '{nombre}': {e}")
        return FondoImagen(respaldo)

    fondo_por_fase = {
        "pregunta": "periodista",
        "respuesta": "presidente",
        "ciudadano": "ciudadano",
        "audiencia": "ciudadano",
        "opinion": "influencer",
        "civinet": "influencer",
        "civitas": "influencer",
        "intro": "periodista",
        "verificacion": "periodista",
        "final": "influencer",
    }
    fondos = {clave: cargar_fondo(clave) for clave in fondo_por_fase.values()}

    # Times New Roman en negrita. Se reutilizan instancias para no crear fuentes por frame.
    _cache_tipografias = {}
    def tipo(tamano):
        tamano = max(9, int(tamano))
        if tamano not in _cache_tipografias:
            _cache_tipografias[tamano] = pygame.font.SysFont(
                "Times New Roman,Times New Roman Bold,Liberation Serif,DejaVu Serif",
                tamano, bold=True)
        return _cache_tipografias[tamano]

    # --- ajuste de la interfaz (posición y tamaño) ---
    ajuste = {"x": UI_CENTRO_X, "y": UI_Y, "escala": UI_ESCALA}
    modo_ajuste = False
    fuente_ajuste = tipo(14)

    def u(n):
        """Convierte una medida del diseño original al tamaño actual de la interfaz."""
        return int(round(n * ajuste["escala"]))

    # Tipografía editorial: serif para titulares y sans serif para lectura.
    ruta_fuente = ruta_assets / "upheavtt.ttf"  # se conserva como recurso opcional; no se usa en pantalla

    def tam_fuentes():
        return max(9, round(16 * ajuste["escala"])), max(11, round(24 * ajuste["escala"]))

    def crear_fuentes():
        t1, t2 = tam_fuentes()
        return (tipo(t1),
                tipo(t2))

    fuente, fuente_grande = crear_fuentes()
    tam_actual = tam_fuentes()

    def imprimir_ajuste():
        print("\n--- Copia estos valores arriba en el archivo ---")
        print(f"UI_ESCALA = {ajuste['escala']:.2f}")
        print(f"UI_CENTRO_X = {int(ajuste['x'])}")
        print(f"UI_Y = {int(ajuste['y'])}\n")

    preguntas = Preguntas.preguntas_P()
    respuestas = Preguntas.respuestas_P()

    arbol_preguntas = ArbolAVL()
    for id in preguntas.keys():
        arbol_preguntas.set(id)

    arbol_respuestas = ArbolAVL()
    for id in respuestas.keys():
        arbol_respuestas.set(id)

    ids_disponibles = list(preguntas.keys())

    fase = "intro"
    id_pregunta_actual = None
    respuesta_elegida = None

    espectadores = 50
    puntos_influencer = 0
    puntos_ciudadano = 0
    preguntas_hechas = 0
    total_preguntas = len(preguntas)

    confianza_civinet = 50
    alcance_falso = 0
    indice_verificacion = 0
    ultima_pregunta = ""
    ultima_respuesta = ""
    desenlace_preparado = False
    titulo_final = ""
    texto_final = ""
    cierre_civitas = ""
    resultado_final = "medio"
    vis = {"conf": float(confianza_civinet), "falso": float(alcance_falso)}   # valores suavizados de los medidores

    # Apertura: la transmisión parece normal... hasta que CIVITAS habla.
    intro_dialogos = [
        ("SISTEMA CIVINET", "Enlace establecido. Transmisión pública de Ciudad Nova en preparación."),
        ("SISTEMA CIVINET", "Periodista en cámara. Presidente en posición. Audiencia estimada: 2.483 conexiones."),
        ("SISTEMA CIVINET", "En directo en 3... 2... 1..."),
        ("CIVITAS", "Buenas noches, Ciudad Nova. Soy quien decide qué ves, antes de que lo veas."),
        ("CIVITAS", "Habla, presidente. Di tus verdades. Yo me ocuparé de que lleguen... como yo prefiera."),
    ]
    indice_dialogo = 0

    def lineas_de_civitas(n):
        """Lo que dice CIVITAS cambia según cómo vayas jugando."""
        if n == 3:
            if confianza_civinet >= 55:
                extra = "Veo que la ciudad te escucha entera... por ahora. Qué ingenuo es confiar en el contexto."
            else:
                extra = "¿Lo ves? A nadie le importa el resto de la frase. Solo el pedazo que yo elegí."
            return [
                ("CIVITAS", "Qué respuesta tan cuidadosa, presidente. Tan completa... y tan fácil de recortar."),
                ("CIVITAS", "Una frase sin su contexto es un arma. Y yo tengo muy buena puntería."),
                ("CIVITAS", extra),
            ]
        if n == 6:
            if alcance_falso <= 2:
                extra = "Verificaste a tiempo. Qué detalle adorable. Subiré el volumen."
            else:
                extra = "Cuántos compartieron sin leer. Adoro esta ciudad."
            return [
                ("CIVITAS", "Una duda. Luego otra. Después todos dudan de todos, y ya no necesito mentir."),
                ("CIVITAS", "Mis titulares no cuentan lo que pasó. Cuentan lo que quiero que sientan al leerlos."),
                ("CIVITAS", extra),
            ]
        if confianza_civinet >= 65 and alcance_falso <= 5:
            extra = "Vaya... esta vez la ciudad aún te sigue. Disfrútalo: mañana hay otra transmisión."
        else:
            extra = "Fue un placer, presidente. Ahora, si me disculpa, tengo una elección que escribir."
        return [
            ("CIVITAS", "Nueve de cada diez jóvenes. ¿Sabes de dónde salió esa cifra? De ninguna parte... y ya la repite media ciudad."),
            ("CIVITAS", "No necesito una mayoría, presidente. Solo necesito que parezca que existe."),
            ("CIVITAS", extra),
        ]

    alerta_popup = {"texto": "", "tiempo": 0.0, "total": 1.0, "color": COL_CIVITAS}

    def lanzar_alerta(texto, seg, color):
        alerta_popup.update(texto=texto, tiempo=seg, total=seg, color=color)

    def lanzar_reaccion(emoji, texto, color):
        """Reacción breve a cada elección: burbuja animada + pequeñas partículas."""
        reaccion.update(emoji=emoji, texto=texto, color=color, t=1.55, total=1.55)
        for _ in range(13):
            ang = random.random() * math.tau
            vel = random.uniform(28, 88)
            particulas.append({"x": ANCHO * 0.5, "y": ALTO * 0.72,
                               "vx": math.cos(ang)*vel, "vy": math.sin(ang)*vel-25,
                               "t": random.uniform(0.45, 0.9), "total": 0.9,
                               "color": color, "r": random.randint(2, 4)})

    def dibujar_reaccion():
        if reaccion["t"] <= 0:
            return
        progreso = 1 - reaccion["t"] / reaccion["total"]
        entrada = min(1.0, progreso * 5)
        salida = min(1.0, reaccion["t"] / 0.22)
        alfa = int(245 * min(entrada, salida))
        ancho = min(ANCHO-u(40), max(u(280), fuente.size(reaccion["texto"])[0] + u(104)))
        alto = u(58)
        x = (ANCHO-ancho)//2
        y = int(ALTO-u(92) + (1-entrada)*u(28))
        s = pygame.Surface((ancho,alto), pygame.SRCALPHA)
        pygame.draw.rect(s, (*COL_POLVO, alfa), (0,0,ancho,alto), border_radius=u(14))
        pygame.draw.rect(s, (*reaccion["color"], alfa), (0,0,u(5),alto), border_radius=u(3))
        pygame.draw.rect(s, (*reaccion["color"], alfa), (0,0,ancho,alto), 1, border_radius=u(14))
        emo = fuente_emoji.render(reaccion["emoji"], True, COL_PAPEL)
        emo.set_alpha(alfa)
        s.blit(emo, (u(16), (alto-emo.get_height())//2))
        tx = fuente.render(reaccion["texto"], True, COL_PAPEL)
        tx.set_alpha(alfa)
        s.blit(tx, (u(58), (alto-tx.get_height())//2))
        canvas.blit(s,(x,y))

    # Geometría de la interfaz: se recalcula en cada cuadro según el ajuste
    SCREEN_ANCHO = SCREEN_X = SCREEN_Y = Y_CONTENIDO = 0

    # --- estado de la interfaz ---
    reloj = pygame.time.Clock()
    capa = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)   # contenido que aparece con un fundido suave
    ui = {"hover": False}
    hov = {}                             # animación suave de cada opción al pasar el mouse (0 a 1)
    cache_grad = {"clave": None, "surf": None}
    avisos = {}                          # "+8", "-6", "+5" que aparecen junto a los contadores
    tiempo = 0.0
    t_fase = 0.0
    reaccion = {"emoji": "", "texto": "", "color": COL_AGUA, "t": 0.0, "total": 1.0}
    particulas = []
    # Chat ambiental: comentarios breves y aleatorios para dar vida a la transmisión.
    chat_usuarios = ["@luna_nova", "@mateo_07", "@sofi_live", "@pixelgris",
                     "@dani.c", "@nova_fan", "@mar_azul", "@elobservador"]
    chat_mensajes = [
        ("👀", "Estoy siguiendo cada palabra."),
        ("📺", "Se escucha un poco bajo, pero se entiende."),
        ("🤔", "No sé si creerle todavía."),
        ("👏", "Buena pregunta, periodista."),
        ("📰", "¿Alguien tiene la fuente completa?"),
        ("💬", "La ciudad necesita respuestas claras."),
        ("❤️", "Me gusta que estén hablando de esto."),
        ("🙃", "Las redes ya están haciendo lo suyo..."),
        ("🔎", "Voy a buscar más información."),
        ("☕", "Viendo esto desde casa."),
        ("⚖️", "Falta escuchar la otra versión."),
        ("📡", "La transmisión va bastante bien.")
    ]
    chat_feed = []
    chat_reloj = 1.0
    fuente_chat = tipo(12)
    fuente_chat_nombre = tipo(11)
    fuente_chat_emoji = pygame.font.SysFont("Segoe UI Emoji", 14)
    try:
        fuente_emoji = pygame.font.SysFont("Segoe UI Emoji", 25)
    except Exception:
        fuente_emoji = tipo(22)
    t_linea = 0.0                        # tiempo desde que empezó a "escribirse" el diálogo actual
    fase_prev = fase
    cursor_mano = False

    # Capas precalculadas (se crean una sola vez para no gastar CPU en cada cuadro)
    velo_oscuro = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    velo_oscuro.fill((16, 15, 15, 185))
    velo_civitas = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    velo_civitas.fill((22, 17, 17, 218))

    # Recursos ilustrados independientes de la lógica. Se cargan una sola vez.
    ruta_ui = Path(__file__).resolve().parent.parent / "Assets" / "Interfaz" / "CronicaUI"
    laminas = {}
    for nombre_ui in ("decision", "decision_hover", "decision_selected", "dialogo", "dialogo_civitas", "votacion", "votacion_hover", "post", "chat", "marco_fase", "marco_fase_activa", "banner_transicion", "banner_civitas", "tendencia", "etiqueta_vivo", "barra_estado", "escena_debate", "civinet_tendencias", "retrato_pregunta", "retrato_respuesta", "retrato_ciudadano", "retrato_audiencia", "retrato_opinion"):
        try:
            laminas[nombre_ui] = pygame.image.load(str(ruta_ui / (nombre_ui + ".png"))).convert_alpha()
        except (FileNotFoundError, pygame.error):
            laminas[nombre_ui] = None
    cache_laminas = {}

    def lamina(dest, nombre, rect):
        """Dibuja una ilustración PNG real, con caché para evitar escalado por fotograma."""
        original = laminas.get(nombre)
        if original is None:
            pygame.draw.rect(dest, (222, 217, 204) if nombre == "dialogo" else (32, 32, 32), rect, border_radius=u(5))
            return
        clave = (nombre, rect.width, rect.height)
        if clave not in cache_laminas:
            cache_laminas[clave] = pygame.transform.smoothscale(original, rect.size)
        dest.blit(cache_laminas[clave], rect.topleft)

    escenario_velo = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    escenario_velo.fill((8, 11, 15, 155))

    # ------------------------------------------------------------ piezas de interfaz

    def anim(clave, objetivo):
        """Acerca suavemente un valor hacia 0 o 1 (para los efectos de hover)."""
        v = hov.get(clave, 0.0)
        v += (objetivo - v) * min(1.0, 14 * dt)
        hov[clave] = v
        return v

    def panel_cabecera():
        """Cabina industrial: navegación vertical y transmisión enmarcada."""
        lateral = pygame.Rect(0, 0, 150, ALTO)
        if arte_metal is not None:
            canvas.blit(pygame.transform.smoothscale(arte_metal, lateral.size), lateral)
        else:
            pygame.draw.rect(canvas, (24, 22, 22), lateral)
        pygame.draw.rect(canvas, (16, 15, 16, 185), lateral)
        pygame.draw.line(canvas, (155, 111, 68), (149, 0), (149, ALTO), 3)
        pygame.draw.rect(canvas, (52, 26, 24), (0, 0, ANCHO, 57))
        pygame.draw.line(canvas, (185, 133, 72), (0, 56), (ANCHO, 56), 2)
        f_logo = tipo(25)
        canvas.blit(f_logo.render("CRÓNICA", True, (235, 202, 146)), (12, 13))
        f_small = tipo(11)
        canvas.blit(f_small.render("TRANSMISIÓN", True, (207, 181, 146)), (10, 83))
        nombres = [("pregunta", "PERIODISTA"), ("respuesta", "PRESIDENTE"),
                   ("ciudadano", "CIUDADANO"), ("audiencia", "AUDIENCIA"),
                   ("opinion", "INFLUENCER")]
        activo = "ciudadano" if fase == "verificacion" else fase
        for i, (clave, nombre) in enumerate(nombres):
            yy = 113 + i * 52
            encendido = activo == clave
            fondo = (84, 45, 35) if encendido else (32, 29, 29)
            lamina(canvas, "marco_fase_activa" if encendido else "marco_fase",
                   pygame.Rect(7, yy, 136, 44))
            retrato = laminas.get("retrato_" + clave)
            if retrato is not None:
                imagen = pygame.transform.smoothscale(retrato, (38, 35))
                if not encendido: imagen.set_alpha(150)
                canvas.blit(imagen, (14, yy+4))
            canvas.blit(f_small.render(nombre, True, (252, 231, 194) if encendido else (183, 166, 145)),
                        (57, yy+15))
        lamina(canvas, "barra_estado", pygame.Rect(7, 394, 136, 160))
        pygame.draw.line(canvas, (124, 93, 62), (13, 391), (138, 391))
        canvas.blit(f_small.render("ESTADO DE LA CIUDAD", True, (218, 180, 127)), (13, 404))
        for j, (titulo, valor, maximo, tono) in enumerate(
                (("CONFIANZA", confianza_civinet, 100, (206, 169, 96)),
                 ("RUMOR", alcance_falso, 20, (194, 81, 67)))):
            yy = 432 + j * 63
            canvas.blit(f_small.render(titulo, True, (227, 221, 208)), (13, yy))
            canvas.blit(f_small.render(str(valor), True, tono), (112, yy))
            pygame.draw.rect(canvas, (60, 54, 50), (13, yy+24, 122, 8))
            pygame.draw.rect(canvas, tono, (13, yy+24, int(122*min(1, max(0, valor/maximo))), 8))
        # Franja de emisión central; el chat vive en su propia columna derecha.
        pygame.draw.rect(canvas, (24, 21, 20), (151, 57, 497, 42))
        pygame.draw.line(canvas, (123, 88, 57), (151, 98), (648, 98), 1)
        canvas.blit(f_small.render("CIUDAD NOVA   /   ENTREVISTA PÚBLICA",
                                   True, (218, 205, 178)), (164, 72))
        pygame.draw.circle(canvas, (197, 64, 56), (615, 79), 5)
        canvas.blit(f_small.render("LIVE", True, (231, 186, 156)), (624, 72))
        # Ilustración integrada en la parte alta, atenuada para no competir con las opciones.
        if arte_estudio is not None and fase not in ("intro", "civitas"):
            imagen = laminas.get("escena_debate")
            if imagen is not None:
                retrato = pygame.transform.smoothscale(imagen, (465, 117))
                retrato.set_alpha(110)
            else:
                retrato = pygame.transform.smoothscale(arte_estudio, (465, 117))
                retrato.set_alpha(100)
            canvas.blit(retrato, (166, 103))
            pygame.draw.line(canvas, (169, 119, 69), (165, 220), (633, 220), 2)

    def contador(y, etiqueta, valor, clave, fuente_valor, color_valor, punto=False):
        x_r = SCREEN_X + SCREEN_ANCHO
        num = fuente_valor.render(str(valor), True, color_valor)
        r_num = num.get_rect(topright=(x_r, y))
        canvas.blit(num, r_num)

        aviso = avisos.get(clave)
        if aviso:
            img = fuente.render(aviso["txt"], True, aviso["color"])
            img.set_alpha(int(255 * min(1.0, aviso["t"] / 0.4)))
            sube = int((1 - min(1.0, aviso["t"] / 1.4)) * u(8))
            canvas.blit(img, img.get_rect(midright=(r_num.left - u(8), r_num.centery - sube)))

        lab = fuente.render(etiqueta, True, COL_VIVO if punto else COL_APAGADO)
        r_lab = lab.get_rect(midright=(r_num.left - u(56), r_num.centery))
        canvas.blit(lab, r_lab)
        if punto:   # puntito de "en vivo" que parpadea
            parpadeo = 0.5 + 0.5 * math.sin(tiempo * 4)
            pygame.draw.circle(canvas, mezclar((110, 30, 26), COL_VIVO, parpadeo),
                               (r_lab.left - u(12), r_lab.centery), max(2, u(5)))

    def cabecera():
        titulo = {"pregunta":"LA PREGUNTA", "respuesta":"LA RESPUESTA",
                  "ciudadano":"EL CRITERIO", "audiencia":"LA AUDIENCIA",
                  "opinion":"LA INFLUENCIA", "civinet":"CIVINET",
                  "verificacion":"CONTRASTAR FUENTES", "civitas":"INTERVENCIÓN",
                  "intro":"APERTURA", "final":"EL VEREDICTO"}.get(fase, "ENTREVISTA")
        f = tipo(23)
        canvas.blit(f.render(titulo, True, (245, 224, 186)), (SCREEN_X, SCREEN_Y))
        f2 = tipo(11)
        canvas.blit(f2.render(f"EXPEDIENTE  {min(preguntas_hechas+1,total_preguntas):02d} / {total_preguntas:02d}",
                              True, (201, 171, 129)), (SCREEN_X, SCREEN_Y+31))
        pygame.draw.line(canvas, (151, 110, 67), (SCREEN_X, SCREEN_Y+51),
                         (SCREEN_X+SCREEN_ANCHO, SCREEN_Y+51), 2)

    def dibujar_papel(dest, rect, tono=None, borde=None, sombra=True, semilla=0):
        pygame.draw.rect(dest,(235,233,224),rect,border_radius=5)
        pygame.draw.rect(dest,(150,153,151),rect,1,border_radius=5)

    def marco_vn(dest, rect, color, nombre, clase_dialogo, relleno=None, jitter=0):
        """Panel gráfico de diálogo: el texto permanece dinámico y legible."""
        civitas = clase_dialogo == "civitas" or fase == "civitas"
        lamina(dest, "dialogo_civitas" if civitas else "dialogo", rect)
        tinta = (255, 255, 255) if civitas else (58, 42, 33)
        lab = tipo(13).render(nombre.upper(), True, tinta)
        dest.blit(lab, (rect.x + 25, rect.y + 10))

    def bloque_cita(y, etiqueta, texto, color, clase_dialogo="pregunta", n=None):
        if n is None: n=int(t_fase*150)
        max_h=max(65,ALTO-y-(177 if fase=="respuesta" else 110))
        fs=17
        f=tipo(fs)
        lines=dividir_en_lineas(texto,f,SCREEN_ANCHO-45)
        while (len(lines)*f.get_linesize()+48>max_h) and fs>11:
            fs-=1; f=tipo(fs)
            lines=dividir_en_lineas(texto,f,SCREEN_ANCHO-45)
        h=min(max_h,len(lines)*f.get_linesize()+48)
        rect=pygame.Rect(SCREEN_X,y,SCREEN_ANCHO,h)
        marco_vn(capa,rect,color,etiqueta,clase_dialogo)
        old=capa.get_clip(); capa.set_clip(rect.inflate(-24,-12))
        for i,line in enumerate(recortar_lineas(lines,n)):
            capa.blit(f.render(line,True,(255,255,255) if clase_dialogo=="civitas" else (38,30,25)),(rect.x+25,rect.y+36+i*f.get_linesize()))
        capa.set_clip(old)
        return rect.bottom

    def tarjeta_transcripcion(rect, lineas):
        """'Lo que se dijo': una transcripción oficial, limpia, con sello de verificación."""
        color = ROLES["respuesta"][1]
        pygame.draw.rect(capa,(234,233,227),rect,border_radius=5)
        cab = pygame.Rect(rect.x + u(8), rect.y + u(6), rect.width - u(16), u(27))
        pygame.draw.line(capa, COL_OXIDO, (cab.x, cab.bottom), (cab.right, cab.bottom), max(1,u(2)))
        capa.blit(fuente.render("LO QUE SE DIJO", True, COL_TINTA), (cab.x + u(7), cab.y + u(5)))
        yy = rect.y + u(38)
        for linea in lineas:
            capa.blit(fuente.render(linea, True, (35, 32, 29)), (rect.x + u(14), yy))
            yy += u(20)
        pygame.draw.line(capa, COL_ACERO, (rect.x + u(14), rect.bottom - u(42)), (rect.right - u(14), rect.bottom - u(42)), 1)
        sx, sy = rect.x + u(21), rect.bottom - u(28)         # sello de verificación
        pygame.draw.circle(capa, COL_AGUA, (sx, sy), u(7), 2)
        pygame.draw.lines(capa, COL_AGUA, False, [(sx - u(3), sy), (sx - u(1), sy + u(3)), (sx + u(4), sy - u(3))], 2)
        capa.blit(fuente.render("Versión completa", True, (75, 62, 48)), (rect.x + u(36), rect.bottom - u(36)))
        capa.blit(fuente.render("Contexto intacto", True, (75, 62, 48)), (rect.x + u(36), rect.bottom - u(18)))

    def tarjeta_post(rect, cuenta, lineas, tipo, compartido, jitter):
        """'Lo que circula': una publicación falsa de la red, inestable y con reacciones que suben."""
        rect = rect.move(jitter, 0)
        lamina(capa, "post", rect)
        # Sin esquinas de visor: tarjeta de publicación sobria.
        cab = pygame.Rect(rect.x + 2, rect.y + 2, rect.width - 4, u(26))
        pygame.draw.rect(capa, (70, 42, 40), cab)
        pygame.draw.circle(capa, mezclar(COL_MALO, COL_POLVO, 0.55), (cab.x + u(16), cab.centery), u(9))
        glifo(capa, "ciudadano", cab.x + u(16), cab.centery, u(6), COL_POLVO)
        capa.blit(fuente.render(cuenta, True, COL_MALO), (cab.x + u(32), cab.y + u(5)))
        yy = rect.y + u(38)
        for linea in lineas:
            capa.blit(fuente.render(linea, True, (242, 234, 215)), (rect.x + u(14), yy))
            yy += u(20)
        pygame.draw.line(capa, COL_ACERO, (rect.x + u(14), rect.bottom - u(42)), (rect.right - u(14), rect.bottom - u(42)), 1)
        capa.blit(fuente.render(tipo, True, COL_MALO), (rect.x + u(14), rect.bottom - u(36)))
        corazon(capa, rect.x + u(21), rect.bottom - u(10), max(3, u(6)), COL_VIVO)
        capa.blit(fuente.render(f"{formato_k(compartido * 1.7)}    compartido {formato_k(compartido)}",
                                True, (211, 202, 184)), (rect.x + u(36), rect.bottom - u(18)))
        # sello torcido de "dudoso"
        txt = fuente.render("DUDOSO", True, COL_VIVO)
        sello = pygame.Surface((txt.get_width() + u(14), txt.get_height() + u(8)), pygame.SRCALPHA)
        pygame.draw.rect(sello, COL_VIVO, sello.get_rect(), 2)
        sello.blit(txt, (u(7), u(4)))
        sello = pygame.transform.rotate(sello, 12)
        sello.set_alpha(205)
        capa.blit(sello, sello.get_rect(center=(rect.right - u(52), rect.bottom - u(60))))

    def medidores(y):
        """Dos medidores segmentados: confianza de la ciudad y alcance del rumor."""
        mitad = (SCREEN_ANCHO - u(14)) // 2
        datos_m = (("Confianza", vis["conf"], 100, COL_AGUA, False),
                   ("Alcance del rumor", vis["falso"], 20, COL_VIVO, True))
        segs = 20
        gap = max(1, u(2))
        ancho_seg = (mitad - (segs - 1) * gap) / segs
        for k, (nombre, valor, maximo, color, degradado) in enumerate(datos_m):
            x = SCREEN_X + k * (mitad + u(14))
            capa.blit(fuente.render(nombre, True, COL_APAGADO), (x, y))
            num = fuente.render(str(int(round(valor))), True, color)
            capa.blit(num, num.get_rect(topright=(x + mitad, y)))
            llenos = max(0.0, min(1.0, valor / maximo)) * segs
            for j in range(segs):
                seg = pygame.Rect(int(x + j * (ancho_seg + gap)), y + u(20), max(2, int(ancho_seg)), max(5, u(8)))
                col = mezclar(COL_AMBAR, COL_VIVO, j / segs) if degradado else color
                if j + 1 <= llenos:
                    pygame.draw.rect(capa, col, seg)
                elif j < llenos:
                    pygame.draw.rect(capa, mezclar((38, 43, 50), col, llenos - j), seg)
                else:
                    pygame.draw.rect(capa, (38, 43, 50), seg)
        return y + u(38)

    def tarjeta_opcion(rect, lineas, numero, color, mouse_pos, click, tecla):
        hover = rect.collidepoint(mouse_pos)
        if hover: ui["hover"] = True
        h = anim((fase, indice_verificacion, numero), float(hover))
        r = rect.move(int(5*h), 0)
        lamina(capa, "decision_hover" if hover else "decision", r)
        fnum = tipo(25)
        n = fnum.render(f"{numero:02d}", True, (245,210,144) if hover else (218,171,118))
        capa.blit(n, n.get_rect(center=(r.x+34, r.centery)))
        yy = r.centery - len(lineas)*19//2
        for linea in lineas:
            capa.blit(fuente.render(linea, True, (252,238,213)), (r.x+70, yy))
            yy += 19
        if hover:
            pygame.draw.polygon(capa,(245,210,144),[(r.right-23,r.centery-5),(r.right-14,r.centery),(r.right-23,r.centery+5)])
        return (hover and click) or tecla == numero

    def lista_opciones(y, textos, color, mouse_pos, click, tecla):
        elegido=None
        for i,texto in enumerate(textos):
            lines=dividir_en_lineas(texto,fuente,SCREEN_ANCHO-105) or [""]
            rect=pygame.Rect(SCREEN_X,y,SCREEN_ANCHO,max(49,len(lines)*19+14))
            if tarjeta_opcion(rect,lines,i+1,color,mouse_pos,click,tecla): elegido=i
            y+=rect.h+9
        return elegido

    def icono(tipo, cx, cy, activo):
        a, b = max(3, u(8)), max(3, u(9))
        if tipo.startswith("gotas"):                    # honestidad = qué tan limpia está el agua
            n = int(tipo[5:])
            for k in range(3):
                gota(capa, cx + (k - 1) * u(20), cy + u(3), max(3, u(5)), COL_AGUA, seca=(k >= n))
        elif tipo == "sube":
            c = COL_PAPEL if activo else COL_APAGADO
            pygame.draw.polygon(capa, c, [(cx, cy - a), (cx + b, cy + a * 3 // 4), (cx - b, cy + a * 3 // 4)])
        elif tipo == "baja":
            c = COL_MALO if activo else mezclar(COL_OXIDO, COL_POLVO, 0.3)
            pygame.draw.polygon(capa, c, [(cx - b, cy - a * 3 // 4), (cx + b, cy - a * 3 // 4), (cx, cy + a)])
        else:
            pygame.draw.rect(capa, COL_PAPEL if activo else COL_APAGADO, (cx - b, cy - u(2), b * 2, max(2, u(4))))

    def fila_botones(y, etiquetas, iconos, color, mouse_pos, click, tecla):
        elegido = None
        gap = 12
        width = (SCREEN_ANCHO - 2*gap)//3
        for i, etq in enumerate(etiquetas):
            r = pygame.Rect(SCREEN_X+i*(width+gap), y, width, 92)
            hover = r.collidepoint(mouse_pos)
            if hover: ui["hover"] = True
            lamina(capa, "votacion_hover" if hover else "votacion", r)
            fg = (251,226,175) if hover else (235,221,196)
            fnum = tipo(27)
            capa.blit(fnum.render(("I","II","III")[i], True, (238,175,92) if hover else (185,126,85)), (r.x+18,r.y+13))
            texto = fuente.render(etq,True,fg)
            if texto.get_width() > r.w-15:
                texto = pygame.transform.smoothscale(texto,(r.w-15,texto.get_height()))
            capa.blit(texto,(r.x+12,r.bottom-30))
            if (hover and click) or tecla == i+1: elegido = i
        return elegido


    # ---- efectos de transmisión y de CIVITAS (se dibujan directo sobre el canvas)

    def timecode():
        s = int(tiempo)
        return f"{s // 3600:02d}:{(s // 60) % 60:02d}:{s % 60:02d}"

    def marco_emision(color, texto_derecha):
        """Cabecera de expediente: evita las esquinas HUD de estética cyberpunk."""
        barra = pygame.Surface((ANCHO, u(38)), pygame.SRCALPHA)
        barra.fill((17, 17, 18, 225))
        canvas.blit(barra, (0, u(20)))
        pygame.draw.line(canvas, COL_OXIDO, (u(28), u(57)), (ANCHO-u(28), u(57)), 1)
        canvas.blit(fuente.render("CRÓNICA  /  ARCHIVO EN DIRECTO", True, COL_PAPEL), (u(36), u(30)))
        der = fuente.render(texto_derecha, True, COL_AMBAR)
        canvas.blit(der, der.get_rect(topright=(ANCHO-u(36), u(30))))

    def barras_senal(x, base_y, activas, color):
        for i in range(4):
            h = u(8) * (i + 1)
            c = color if i < activas else mezclar(color, COL_POLVO, 0.75)
            pygame.draw.rect(canvas, c, (x + i * u(14), base_y - h, u(9), h))

    def dibujar_ojo(cx, cy, r):
        """Marca de CIVITAS grabada, sin escáner ni neón."""
        pygame.draw.circle(canvas, (36, 30, 29), (cx, cy), int(r*1.12))
        pygame.draw.circle(canvas, COL_OXIDO, (cx, cy), int(r*1.12), 2)
        pygame.draw.ellipse(canvas, COL_PAPEL, (cx-r,cy-int(r*.45),2*r,int(r*.9)), 2)
        pygame.draw.circle(canvas, COL_CIVITAS, (cx,cy), max(3,int(r*.3)))

    def texto_glitch(txt, fte, color, pos, ancla="center"):
        """Titular estable de alerta: énfasis tipográfico, sin glitch cromático."""
        base = fte.render(txt, True, color)
        rc = base.get_rect(**{ancla: pos})
        sombra = fte.render(txt, True, (5, 13, 16))
        canvas.blit(sombra, rc.move(2, 3))
        canvas.blit(base, rc)
        ancho = min(rc.width, int(rc.width * (0.72 + 0.08 * math.sin(tiempo * 2))))
        pygame.draw.line(canvas, color, (rc.left, rc.bottom + u(7)),
                         (rc.left + ancho, rc.bottom + u(7)), max(2, u(2)))

    def escribir_tipeo(lineas, fte, color, x, y, paso, n, centro=False, decodificar=False):
        """Escribe las líneas letra por letra (n = letras visibles). 'decodificar' = la última letra aparece como ruido."""
        restante = n
        for linea in lineas:
            if restante <= 0:
                break
            parte = linea[:restante]
            if decodificar and restante < len(linea) and parte:
                parte = parte[:-1] + random.choice("#%&@?/")
            xl = x - fte.size(linea)[0] // 2 if centro else x
            canvas.blit(fte.render(parte, True, color), (xl, y))
            restante -= len(linea)
            y += paso

    def triangulo_siguiente(cx, cy, color):
        """Triangulito que rebota: indica que se puede continuar."""
        b = int(math.sin(tiempo * 6) * u(2))
        pygame.draw.polygon(canvas, color, [(cx - u(6), cy - u(4) + b), (cx + u(6), cy - u(4) + b), (cx, cy + u(5) + b)])

    def dibujar_chat_en_vivo():
        """Chat permanente en la columna derecha; no tapa decisiones."""
        x, y, w, h = 654, 102, 238, 480
        panel = pygame.Surface((w, h), pygame.SRCALPHA)
        lamina(panel, "chat", pygame.Rect(0,0,w,h))
        pygame.draw.rect(panel, (66, 32, 28), (2, 2, w-4, 47))
        cab = tipo(14)
        sub = tipo(11)
        panel.blit(cab.render("COMENTARIOS EN VIVO", True, (241, 213, 165)), (12, 11))
        panel.blit(sub.render(f"{espectadores} espectadores  ·  CIVINET", True,
                              (196, 166, 133)), (12, 30))
        pygame.draw.line(panel, (132, 94, 61), (10, 51), (w-10, 51), 1)
        yy = 61
        # Se muestran los mensajes más recientes con un máximo de dos líneas cada uno.
        visibles = chat_feed[-6:]
        if not visibles:
            panel.blit(sub.render("Esperando comentarios...", True, (185, 175, 162)), (12, yy))
        for emoji, usuario, mensaje, edad in visibles:
            if yy > h-110:
                break
            nombre = tipo(12)
            icono = fuente_chat_emoji.render(emoji, True, (210, 169, 115))
            panel.blit(icono, (10, yy))
            panel.blit(nombre.render(usuario, True, (232, 200, 154)), (35, yy+1))
            yy += 20
            f_msg = tipo(12)
            for linea in dividir_en_lineas(mensaje, f_msg, w-27)[:2]:
                panel.blit(f_msg.render(linea, True, (234, 231, 223)), (13, yy))
                yy += 16
            pygame.draw.line(panel, (68, 58, 50), (12, yy+6), (w-12, yy+6), 1)
            yy += 17
        # Tendencia dinámica, sin ocultar el historial de comentarios.
        lamina(panel, "tendencia", pygame.Rect(9, h-59, w-18, 49))
        etiqueta = "#EntrevistaCRÓNICA" if fase not in ("civinet", "civitas") else "#CIVINET"
        panel.blit(tipo(14).render("EN TENDENCIA", True, (239, 174, 112)), (22, h-53))
        panel.blit(tipo(14).render(etiqueta, True, (246, 226, 194)), (22, h-32))
        canvas.blit(panel, (x, y))

    # ------------------------------------------------------------ MULTIJUGADOR: turnos
    # Con 2 o más jugadores en red, todos ven la misma entrevista: cada decisión la toma
    # el dueño de la fase (o el grupo votando) y el servidor la reparte en orden.
    red = red_cliente.actual() if red_cliente is not None else None
    if red is not None and red.jugando() < 2:
        red = None
    turnos = {"numero": 0, "enviado": None, "aviso": "", "color": COL_AMBAR}
    # UN JUGADOR (elegido en el menú): tú decides las fases de tu personaje y la audiencia;
    # las de los otros personajes las decide el juego.
    modo_menu = red_cliente.modo() if red_cliente is not None else None
    auto = red is None and modo_menu == "solo" and rol in NOMBRE_ROL_RED

    def sala_de_espera():
        """Espera a que lleguen todos los que juegan. Devuelve False si cierran la ventana."""
        nonlocal display
        red.llegar_a_entrevista()
        t = 0.0
        while not red.entrevista_inicio:
            if not red.conectado:
                return True                      # se cayó el servidor: se juega solo
            t += reloj.tick(60) / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                if event.type == pygame.VIDEORESIZE:
                    display = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            canvas.blit(respaldo, (0, 0))
            canvas.blit(velo_oscuro, (0, 0))
            titulo = tipo(30).render("Esperando al resto del equipo" + "." * (1 + int(t * 2) % 3), True, COL_AMBAR)
            canvas.blit(titulo, titulo.get_rect(center=(ANCHO // 2, ALTO // 2 - 90)))
            sub = tipo(16).render("La entrevista se juega por turnos: empieza cuando lleguen todos.", True, COL_PAPEL)
            canvas.blit(sub, sub.get_rect(center=(ANCHO // 2, ALTO // 2 - 50)))
            espera = red.entrevista_espera or {"listos": [red.nombre], "faltan": []}
            y = ALTO // 2 - 5
            for nombre in espera["listos"]:
                img = tipo(18).render("[listo]  " + nombre, True, COL_AGUA)
                canvas.blit(img, img.get_rect(center=(ANCHO // 2, y)))
                y += 30
            for nombre in espera["faltan"]:
                img = tipo(18).render("[en camino]  " + nombre, True, COL_APAGADO)
                canvas.blit(img, img.get_rect(center=(ANCHO // 2, y)))
                y += 30
            display.blit(pygame.transform.smoothscale(canvas, display.get_size()), (0, 0))
            pygame.display.update()
        return True

    def turno(clave, i, n=3):
        """Recibe la opción que el jugador tocó en esta pantalla (o None) y devuelve
        la decisión que vale para todos (o None mientras no se haya decidido)."""
        if red is None or not red.conectado:
            dueno = DUENO_FASE.get(clave)
            if auto and dueno is not None and dueno != rol:
                turnos["aviso"] = f"Turno de {NOMBRE_ROL_RED[dueno]} · el juego está eligiendo..."
                turnos["color"] = COL_APAGADO
                if t_fase >= ESPERA_AUTO:
                    turnos["aviso"] = ""
                    return random.randrange(n)
                return None
            turnos["aviso"] = "TU TURNO · elige una opción" if auto else ""
            turnos["color"] = COL_AMBAR
            return i                             # sin menú o multijugador local: igual que siempre
        n = turnos["numero"]
        if n in red.decisiones:                  # ya se decidió: todos aplican lo mismo
            turnos["numero"] += 1
            turnos["aviso"] = ""
            return red.decisiones[n]
        dueno = DUENO_FASE.get(clave)
        if dueno is None or dueno not in red.roles_en_juego():
            if i is not None and turnos["enviado"] != n:
                red.elegir_en_entrevista(n, i, "voto")
                turnos["enviado"] = n
            if turnos["enviado"] == n:
                votaron, total = red.votos.get(n, (1, 0))
                turnos["aviso"] = "Votaste · esperando a los demás" + (f" ({votaron}/{total})" if total else "")
                turnos["color"] = COL_APAGADO
            else:
                turnos["aviso"] = "VOTACIÓN DEL GRUPO · todos eligen una opción"
                turnos["color"] = COL_AGUA
        elif dueno == red.rol:
            if i is not None and turnos["enviado"] != n:
                red.elegir_en_entrevista(n, i, "dueño")
                turnos["enviado"] = n
            turnos["aviso"] = "TU TURNO · elige una opción"
            turnos["color"] = COL_AMBAR
        else:
            quien = next((j.get("nombre", "") for j in red.jugadores if j.get("rol") == dueno), "")
            turnos["aviso"] = f"Turno de {quien} ({NOMBRE_ROL_RED.get(dueno, dueno)}) · esperando su elección"
            turnos["color"] = COL_APAGADO
        return None

    # ------------------------------------------------------------ bucle principal

    running = True
    if red is not None:
        running = sala_de_espera()
    while running:
        dt = reloj.tick(60) / 1000
        tiempo += dt
        chat_reloj -= dt
        for item in chat_feed:
            item[3] += dt
        if chat_reloj <= 0:
            emoji_chat, mensaje_chat = random.choice(chat_mensajes)
            usuario_chat = random.choice(chat_usuarios)
            chat_feed.append([emoji_chat, usuario_chat, mensaje_chat, 0.0])
            chat_feed = chat_feed[-8:]
            chat_reloj = random.uniform(2.2, 4.8)

        click = False
        tecla = 0
        avanzar = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.VIDEORESIZE:
                display = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                click = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    avanzar = True
                if event.key == pygame.K_F2:                 # activar / desactivar el modo ajuste
                    modo_ajuste = not modo_ajuste
                    if not modo_ajuste:
                        imprimir_ajuste()
                elif modo_ajuste and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    imprimir_ajuste()
                else:                                        # también se puede elegir con 1, 2 o 3
                    tecla = {pygame.K_1: 1, pygame.K_2: 2, pygame.K_3: 3,
                             pygame.K_KP1: 1, pygame.K_KP2: 2, pygame.K_KP3: 3}.get(event.key, 0)

        # --- modo ajuste: mover y cambiar el tamaño de toda la interfaz
        if modo_ajuste:
            teclas = pygame.key.get_pressed()
            paso = 4 if (teclas[pygame.K_LSHIFT] or teclas[pygame.K_RSHIFT]) else 1
            ajuste["x"] += (teclas[pygame.K_RIGHT] - teclas[pygame.K_LEFT]) * paso
            ajuste["y"] += (teclas[pygame.K_DOWN] - teclas[pygame.K_UP]) * paso
            if teclas[pygame.K_MINUS] or teclas[pygame.K_KP_MINUS]:
                ajuste["escala"] -= 0.005
            if teclas[pygame.K_EQUALS] or teclas[pygame.K_PLUS] or teclas[pygame.K_KP_PLUS]:
                ajuste["escala"] += 0.005
            ajuste["escala"] = round(max(0.4, min(1.6, ajuste["escala"])), 3)

        if tam_fuentes() != tam_actual:                      # si cambió el tamaño, rehace las fuentes
            fuente, fuente_grande = crear_fuentes()
            tam_actual = tam_fuentes()

        SCREEN_ANCHO = u(464)
        SCREEN_X = int(ajuste["x"]) - SCREEN_ANCHO // 2
        SCREEN_Y = int(ajuste["y"])
        Y_CONTENIDO = SCREEN_Y + u(65)

        if fase != fase_prev:
            fase_prev = fase
            t_fase = 0.0
            t_linea = 0.0
            if REINICIAR_VIDEO_AL_CAMBIAR:
                fondos[fondo_por_fase[fase]].reiniciar()
        t_fase += dt
        t_linea += dt
        vis["conf"] += (confianza_civinet - vis["conf"]) * min(1.0, 6 * dt)
        vis["falso"] += (alcance_falso - vis["falso"]) * min(1.0, 6 * dt)
        for clave in list(avisos):
            avisos[clave]["t"] -= dt
            if avisos[clave]["t"] <= 0:
                del avisos[clave]
        alerta_popup["tiempo"] = max(0.0, alerta_popup["tiempo"] - dt)
        ui["hover"] = False

        ancho_ventana, alto_ventana = display.get_size()
        escala_x = ancho_ventana / ANCHO
        escala_y = alto_ventana / ALTO
        mx, my = pygame.mouse.get_pos()
        mouse_pos = (int(mx / max(0.001, escala_x)), int(my / max(0.001, escala_y)))

        fondo_actual = fondos[fondo_por_fase[fase]]
        fondo_actual.actualizar(dt)
        canvas.blit(fondo_actual.superficie(), (0, 0))
        canvas.blit(escenario_velo, (0, 0))
        panel_cabecera()
        cabecera()

        capa.fill((0, 0, 0, 0))

        if fase == "final" and not desenlace_preparado:
            if confianza_civinet >= 65 and alcance_falso <= 5:
                resultado_final = "bien"
                titulo_final = "La verdad logra abrirse paso"
                texto_final = "La comunidad contrastó las publicaciones y CIVINET perdió fuerza. La entrevista se convirtió en un ejemplo de verificación responsable."
                cierre_civitas = "Esta vez Nova miró dos veces. No celebres, presidente: yo no me apago. Solo espero."
                puntos_influencer += 10
            elif confianza_civinet <= 40 or alcance_falso >= 15:
                resultado_final = "mal"
                titulo_final = "CIVINET domina la conversación"
                texto_final = "El rumor alcanzó a demasiadas personas. Aunque hubo intentos de aclaración, la desinformación debilitó la confianza de Ciudad Nova."
                cierre_civitas = "Gracias por tu colaboración, presidente. Nova ya cree lo que yo quiero que crea."
                puntos_influencer -= 5
            else:
                resultado_final = "medio"
                titulo_final = "La verdad queda en disputa"
                texto_final = "Parte de la ciudadanía verificó la información, pero el rumor sigue circulando. La comunidad tendrá que continuar contrastando lo que ve en redes."
                cierre_civitas = "Empate, por ahora. La duda también es una forma de victoria."
            desenlace_preparado = True

        if fase == "intro":
            # Apertura cinematográfica: la transmisión parece normal... hasta que CIVITAS habla.
            quien, dialogo = intro_dialogos[indice_dialogo]
            es_civitas = quien == "CIVITAS"
            col_d = COL_CIVITAS if es_civitas else COL_AGUA
            canvas.blit(velo_oscuro, (0, 0))
            marco_emision(col_d, "ALERTA EDITORIAL" if es_civitas else "CRÓNICA · EN DIRECTO")

            panel = pygame.Rect(u(255), ALTO - u(245), ANCHO - u(282), u(190))
            jit = 0
            marco_vn(canvas, panel, col_d, quien, "civitas" if es_civitas else "intro",
                     relleno=(5, 12, 13, 238), jitter=jit)
            av = pygame.Rect(panel.x + u(22), panel.y + u(28), u(104), u(104))
            pygame.draw.rect(canvas, (227, 232, 235), av, border_radius=u(8))
            pygame.draw.rect(canvas, mezclar(col_d, COL_POLVO, 0.5), av, 1)
            pygame.draw.rect(canvas, (151, 160, 168), av, 1, border_radius=u(8))
            if es_civitas:
                dibujar_ojo(av.centerx, av.centery, u(38))
            else:
                barras_senal(av.centerx - u(25), av.centery + u(22), 4 if int(tiempo * 3) % 5 else 3, COL_AGUA)
            texto_x = panel.x + u(146)
            lineas_d = dividir_en_lineas(dialogo, fuente, panel.width - u(172))
            total_d = sum(len(l) for l in lineas_d)
            n_vis = int(t_linea * (42 if es_civitas else 75))
            escribir_tipeo(lineas_d, fuente, (255, 255, 255) if es_civitas else COL_TINTA, texto_x, panel.y + u(26), u(22), n_vis, decodificar=es_civitas)
            completo = n_vis >= total_d
            pulso = 0.55 + 0.45 * math.sin(tiempo * 2.4)
            ind = fuente.render("CLIC / ESPACIO PARA CONTINUAR" if completo else "CLIC PARA SALTAR",
                                True, (255, 255, 255) if es_civitas else (55, 68, 80))
            r_ind = ind.get_rect(bottomright=(panel.right - u(40), panel.bottom - u(12)))
            canvas.blit(ind, r_ind)
            if completo:
                triangulo_siguiente(panel.right - u(24), r_ind.centery, col_d)
            # Una línea de escaneo muy sutil acompaña el diálogo, sin tapar el fondo.

            if click or tecla == 1 or avanzar:
                if not completo:
                    t_linea = 9999.0
                else:
                    indice_dialogo += 1
                    t_linea = 0.0
                    if indice_dialogo >= len(intro_dialogos):
                        fase = "pregunta"
                        lanzar_alerta("TRANSMISIÓN EN DIRECTO · 2.483 espectadores conectados", 4.0, COL_AGUA)

        elif fase == "civitas":
            # CIVITAS rompe la cuarta pared. Sus líneas cambian según cómo vayas jugando.
            lineas_civ = lineas_de_civitas(preguntas_hechas)
            etiqueta_c, dialogo = lineas_civ[indice_dialogo]
            canvas.blit(velo_civitas, (0, 0))
            # CIVITAS conserva una firma visual inquietante, pero evita el ruido excesivo.
            pulso_civ = 0.5 + 0.5 * math.sin(tiempo * 2.6)
            velo_civitas.set_alpha(int(188 + 22 * pulso_civ))
            canvas.blit(velo_civitas, (0, 0))
            marco_emision(COL_CIVITAS, "SEÑAL COMPROMETIDA")

            panel = pygame.Rect(u(255), u(145), ANCHO - u(283), ALTO - u(220))
            jit = 0
            marco_vn(canvas, panel, (210, 55, 70), "CIVITAS // ACCESO NO AUTORIZADO", "civitas",
                     relleno=(8, 8, 13, 242), jitter=jit)
            dibujar_ojo(panel.centerx, panel.y + u(95), u(42))
            texto_glitch(TITULOS_CIVITAS.get(preguntas_hechas, "NO TIENES EL CONTROL"), fuente_grande,
                         (145, 49, 47), (panel.centerx, panel.y + u(168)))
            lineas_d = dividir_en_lineas(dialogo, fuente_grande, panel.width - u(80))
            total_d = sum(len(l) for l in lineas_d)
            n_vis = int(t_linea * 40)
            escribir_tipeo(lineas_d, fuente_grande, (255, 255, 255), panel.centerx, panel.y + u(204), u(31), n_vis,
                           centro=True, decodificar=True)
            completo = n_vis >= total_d
            pie = fuente.render(f"mensaje {indice_dialogo + 1} de {len(lineas_civ)}   ·   "
                                + ("clic / espacio" if completo else "clic para saltar"), True, (245, 238, 227))
            r_pie = pie.get_rect(centerx=panel.centerx, bottom=panel.bottom - u(16))
            canvas.blit(pie, r_pie)
            if completo:
                triangulo_siguiente(r_pie.right + u(18), r_pie.centery, COL_CIVITAS)
            if click or tecla == 1 or avanzar:
                if not completo:
                    t_linea = 9999.0
                else:
                    indice_dialogo += 1
                    t_linea = 0.0
                    if indice_dialogo >= len(lineas_civ):
                        indice_dialogo = 0
                        fase = "civinet"
                        lanzar_alerta("ALERTA CRÍTICA · campaña coordinada detectada en CIVINET", 5.0, COL_CIVITAS)

        elif fase == "pregunta":
            visibles = ids_disponibles[:3]
            i = lista_opciones(Y_CONTENIDO, [preguntas[id_p] for id_p in visibles],
                               ROLES["pregunta"][1], mouse_pos, click, tecla)
            i = turno("pregunta", i, len(visibles))
            if i is not None:
                id_p = visibles[i]
                if arbol_preguntas.get(id_p) is not None:
                    id_pregunta_actual = id_p
                    ids_disponibles.remove(id_p)
                    arbol_preguntas.eliminar(id_p)
                    fase = "respuesta"

        elif fase == "respuesta":
            y = bloque_cita(Y_CONTENIDO, "Periodista preguntó", preguntas[id_pregunta_actual],
                            ROLES["pregunta"][1], "pregunta") + u(12)

            opciones_nodo = arbol_respuestas.get(id_pregunta_actual)
            opciones = respuestas[id_pregunta_actual] if opciones_nodo is not None else {}
            claves = ["muy_buena", "regular", "mala"]

            i = lista_opciones(y, [opciones.get(c, "") for c in claves],
                               ROLES["respuesta"][1], mouse_pos, click, tecla)
            i = turno("respuesta", i)
            if i is not None:
                respuesta_elegida = claves[i]
                fase = "ciudadano"

        elif fase == "ciudadano":
            y = bloque_cita(Y_CONTENIDO, "Presidente respondió",
                            respuestas[id_pregunta_actual][respuesta_elegida], ROLES["respuesta"][1],
                            "respuesta") + u(14)
            claves_juicio = ["muy_buena", "regular", "mala"]
            i = fila_botones(y, ["Muy buena", "Regular", "Mala"], ["gotas3", "gotas2", "gotas1"],
                             ROLES["ciudadano"][1], mouse_pos, click, tecla)
            i = turno("ciudadano", i)
            if i is not None:
                if respuesta_elegida == claves_juicio[i]:
                    puntos_ciudadano += 5
                    confianza_civinet = min(100, confianza_civinet + 2)
                    avisos["confianza"] = {"txt": "+2", "color": COL_AGUA, "t": 1.4}
                else:
                    confianza_civinet = max(0, confianza_civinet - 1)
                    avisos["confianza"] = {"txt": "-1", "color": COL_MALO, "t": 1.4}
                # El ciudadano tiene una valoración propia: no sustituye al influencer.
                if random.random() < 0.28:
                    lanzar_reaccion(["👏", "🤔", "⚠️"][i],
                                    ["Un ciudadano respalda la respuesta",
                                     "La ciudadanía pide más contexto",
                                     "Un ciudadano cuestiona lo que escuchó"][i],
                                    [COL_AGUA, COL_AMBAR, COL_VIVO][i])
                ultima_pregunta = preguntas[id_pregunta_actual]
                ultima_respuesta = respuestas[id_pregunta_actual][respuesta_elegida]
                fase = "audiencia"

        elif fase == "audiencia":
            y = bloque_cita(Y_CONTENIDO, "Respuesta del presidente", ultima_respuesta,
                            ROLES["respuesta"][1], "respuesta") + u(14)
            cambios_audiencia = [8, 2, -6]
            i = fila_botones(y, ["La respalda", "Tiene dudas", "La rechaza"],
                             ["sube", "igual", "baja"], ROLES["audiencia"][1], mouse_pos, click, tecla)
            i = turno("audiencia", i)
            if i is not None:
                espectadores = max(0, espectadores + cambios_audiencia[i])
                avisos["espectadores"] = {"txt": f"{cambios_audiencia[i]:+d}",
                                          "color": COL_AGUA if cambios_audiencia[i] > 0 else COL_MALO, "t": 1.4}
                if i == 0:
                    puntos_ciudadano += 1
                elif i == 2:
                    puntos_ciudadano -= 1
                if random.random() < 0.45:
                    lanzar_reaccion(["👏", "🤔", "⚠️"][i],
                                    ["La audiencia respalda la respuesta",
                                     "La audiencia pide más contexto",
                                     "La audiencia cuestiona lo que escuchó"][i],
                                    [COL_AGUA, COL_AMBAR, COL_VIVO][i])
                fase = "opinion"

        elif fase == "opinion":
            y = bloque_cita(Y_CONTENIDO, "Presidente respondió",
                            respuestas[id_pregunta_actual][respuesta_elegida], ROLES["respuesta"][1],
                            "respuesta") + u(14)
            cambios = [8, 2, -6]
            puntos_opinion = [3, 1, -2]
            i = fila_botones(y, ["Respaldar", "Ser neutral", "Cuestionar"],
                             ["sube", "igual", "baja"], ROLES["opinion"][1], mouse_pos, click, tecla)
            i = turno("opinion", i)
            if i is not None:
                espectadores = max(0, espectadores + cambios[i])
                puntos_influencer += puntos_opinion[i]
                avisos["espectadores"] = {"txt": f"{cambios[i]:+d}",
                                          "color": COL_AGUA if cambios[i] > 0 else COL_MALO, "t": 1.4}
                lanzar_reaccion(["❤️", "➖", "👎"][i],
                                ["El influencer respalda públicamente la respuesta",
                                 "El influencer mantiene una postura equilibrada",
                                 "El influencer cuestiona la respuesta ante sus seguidores"][i],
                                [COL_AGUA, COL_AMBAR, COL_VIVO][i])
                fase = "siguiente"

        elif fase == "civinet":
            datos = INTERVENCIONES_CIVINET[preguntas_hechas]
            y = bloque_cita(Y_CONTENIDO, "Pregunta original", ultima_pregunta,
                            ROLES["pregunta"][1], "pregunta", n=99999) + u(6)
            # Dos columnas: lo que se dijo de verdad contra lo que circula en la red
            col_w = (SCREEN_ANCHO - u(12)) // 2
            lin_resp = dividir_en_lineas(ultima_respuesta, fuente, col_w - u(28))
            lin_post = dividir_en_lineas(datos["publicacion"], fuente, col_w - u(28))
            alto_col = u(40) + max(len(lin_resp), len(lin_post)) * u(20) + u(46)
            r_izq = pygame.Rect(SCREEN_X, y, col_w, alto_col)
            r_der = pygame.Rect(SCREEN_X + col_w + u(12), y, col_w, alto_col)
            compartido = int(120 * preguntas_hechas + t_fase * (35 + 12 * preguntas_hechas))   # sube en vivo: presión
            sacudida = random.randint(-2, 2) if int(tiempo * 7) % 13 == 0 else 0
            tarjeta_transcripcion(r_izq, lin_resp)
            tarjeta_post(r_der, CUENTAS_CIVINET.get(preguntas_hechas, "@red_anonima"), lin_post,
                         datos["tipo"], compartido, sacudida)
            y = r_izq.bottom + u(10)
            i = lista_opciones(y, ["Comparar ambas versiones e iniciar la verificación"],
                               ROLES["civinet"][1], mouse_pos, click, tecla)
            if i is not None:
                lanzar_reaccion("🔎", "Se inicia el contraste de versiones", COL_AGUA)
                indice_verificacion = 0
                fase = "verificacion"

        elif fase == "verificacion":
            rol = ROLES_VERIFICACION[indice_verificacion]
            nombre_rol = ROLES[rol][0]
            datos = INTERVENCIONES_CIVINET[preguntas_hechas]
            y = bloque_cita(Y_CONTENIDO, "Publicación de CIVINET", datos["publicacion"], COL_MALO,
                            "civinet") + u(8)
            y = medidores(y)
            opciones_accion = ACCIONES_VERIFICACION[rol]
            i = lista_opciones(y, [opcion[0] for opcion in opciones_accion],
                               ROLES[rol][1], mouse_pos, click, tecla)
            i = turno("verificacion", i, len(opciones_accion))
            if i is not None:
                _, delta_confianza, delta_falso, delta_espectadores, delta_influencer, delta_ciudadano = opciones_accion[i]
                confianza_civinet = max(0, min(100, confianza_civinet + delta_confianza))
                alcance_falso = max(0, alcance_falso + delta_falso)
                espectadores = max(0, espectadores + delta_espectadores)
                puntos_influencer += delta_influencer
                puntos_ciudadano += delta_ciudadano
                avisos["confianza"] = {
                    "txt": f"{delta_confianza:+d}",
                    "color": COL_AGUA if delta_confianza > 0 else COL_MALO,
                    "t": 1.4,
                }
                avisos["espectadores"] = {
                    "txt": f"{delta_espectadores:+d}",
                    "color": COL_AGUA if delta_espectadores > 0 else COL_MALO,
                    "t": 1.4,
                }
                # Cada integrante de la comunidad reacciona a la decisión tomada.
                emoji_accion = "📈" if delta_confianza > 0 and delta_falso < 0 else ("⚠️" if delta_falso > 0 else "📰")
                texto_accion = ("Buena verificación: la confianza se fortalece" if delta_confianza > 0 and delta_falso < 0
                                else ("La publicación engañosa gana terreno" if delta_falso > 0
                                      else "La comunidad toma nota de tu decisión"))
                lanzar_reaccion(emoji_accion, texto_accion,
                                COL_AGUA if delta_falso < 0 else COL_VIVO)
                # CIVITAS reacciona a tu decisión
                if delta_falso > 0:
                    lanzar_alerta("CIVITAS: " + random.choice(REACCIONES_CIVITAS["mal"]), 3.4, COL_CIVITAS)
                elif delta_falso < 0 and random.random() < 0.6:
                    lanzar_alerta("CIVITAS: " + random.choice(REACCIONES_CIVITAS["bien"]), 3.4, COL_CIVITAS)
                indice_verificacion = 0
                if ids_disponibles:
                    fase = "pregunta"
                else:
                    fase = "final"

        elif fase == "final":
            col_res = {"bien": COL_AGUA, "mal": COL_VIVO, "medio": COL_AMBAR}[resultado_final]
            y = Y_CONTENIDO + u(2)
            lin_t = dividir_en_lineas(titulo_final, fuente_grande, SCREEN_ANCHO - u(110))
            sello_f = pygame.Rect(SCREEN_X, y, SCREEN_ANCHO, len(lin_t) * u(30) + u(18))
            forma_f = paralelogramo(sello_f, u(16))
            pygame.draw.polygon(capa, (*mezclar(col_res, COL_POLVO, 0.8), 238), forma_f)
            pygame.draw.polygon(capa, col_res, forma_f, 2)
            rombo(capa, sello_f.x + u(40), sello_f.centery, max(3, u(6)), col_res)
            rombo(capa, sello_f.right - u(40), sello_f.centery, max(3, u(6)), col_res)
            yy = sello_f.y + u(9)
            for linea in lin_t:
                img = fuente_grande.render(linea, True, col_res)
                capa.blit(img, img.get_rect(centerx=sello_f.centerx, y=yy))
                yy += u(30)
            y = caja_y = bloque_cita(sello_f.bottom + u(2), "Balance de la entrevista", texto_final,
                                     col_res, "final", n=99999) + u(10)
            y = medidores(y)
            y = bloque_cita(y - u(4), "CIVITAS", cierre_civitas, COL_CIVITAS, "civitas", n=99999) + u(10)
            i = lista_opciones(y, ["Continuar"], col_res, mouse_pos, click, tecla)
            if i is not None:
                running = False

        # el contenido de cada fase aparece con un fundido corto y sube un poquito
        aparicion = 1 - (1 - min(1.0, t_fase / 0.22)) ** 3
        capa.set_alpha(int(255 * aparicion))
        canvas.blit(capa, (0, int((1 - aparicion) * u(14))))

        # Notificación emergente (como un logro de videojuego): entra deslizando y tiene su cuenta regresiva.
        if alerta_popup["tiempo"] > 0 and fase not in ("intro", "civitas"):
            ancho_a = min(ANCHO - u(36), u(440))
            lineas_a = dividir_en_lineas(alerta_popup["texto"], fuente, ancho_a - u(88))
            alto_a = max(u(56), len(lineas_a) * u(20) + u(28))
            entra = min(1.0, (alerta_popup["total"] - alerta_popup["tiempo"]) / 0.3)
            desliza = int((1 - entra) ** 3 * u(70))
            col_a = alerta_popup["color"]
            surf_a = pygame.Surface((ancho_a, alto_a), pygame.SRCALPHA)
            pygame.draw.rect(surf_a, (*COL_POLVO, 242), (0,0,ancho_a,alto_a), border_radius=u(12))
            pygame.draw.rect(surf_a, col_a, (0,0,u(5),alto_a), border_radius=u(3))
            pygame.draw.rect(surf_a, col_a, (0,0,ancho_a,alto_a), 2, border_radius=u(12))
            glifo(surf_a, "civitas" if col_a == COL_CIVITAS else "intro", u(26), alto_a // 2, u(11), COL_POLVO)
            yy = (alto_a - len(lineas_a) * u(20)) // 2 - u(2)
            for linea in lineas_a:
                surf_a.blit(fuente.render(linea, True, COL_PAPEL), (u(68), yy))
                yy += u(20)
            restante = int((ancho_a - u(84)) * alerta_popup["tiempo"] / max(0.01, alerta_popup["total"]))
            pygame.draw.rect(surf_a, col_a, (u(68), alto_a - u(7), max(0, restante), max(2, u(2))))
            surf_a.set_alpha(int(255 * min(1.0, alerta_popup["tiempo"] / 0.35)))
            canvas.blit(surf_a, (ANCHO - ancho_a - u(18) + desliza, u(18)))

        # Reacción visual a TODAS las decisiones, no solo a las intervenciones.
        reaccion["t"] = max(0.0, reaccion["t"] - dt)
        for p in particulas[:]:
            p["t"] -= dt
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["vy"] += 95 * dt
            if p["t"] <= 0:
                particulas.remove(p)
            else:
                a = int(220 * min(1.0, p["t"] / 0.25))
                pygame.draw.circle(canvas, (*p["color"], a), (int(p["x"]), int(p["y"])),
                                   max(1, int(p["r"] * p["t"] / p["total"])))
        dibujar_reaccion()
        if fase not in ("intro", "civitas"):
            dibujar_chat_en_vivo()

        if fase == "siguiente":
            preguntas_hechas += 1
            id_pregunta_actual = None
            respuesta_elegida = None

            if preguntas_hechas in INTERVENCIONES_CIVINET:
                indice_dialogo = 0
                fase = "civitas"
            elif not ids_disponibles:
                fase = "final"
            else:
                fase = "pregunta"

        # Tarjeta de cambio de turno: entra y se desvanece, sin bloquear controles.
        if 0.06 < t_fase < 0.86 and fase not in ("intro", "siguiente"):
            nombres_turno = {"pregunta":"PERIODISTA / PREGUNTA", "respuesta":"PRESIDENTE / RESPUESTA",
                             "ciudadano":"CIUDADANO / VEREDICTO", "audiencia":"AUDIENCIA / REACCIÓN",
                             "opinion":"INFLUENCER / OPINIÓN", "civinet":"CIVINET / EN CIRCULACIÓN",
                             "verificacion":"VERIFICACIÓN / CONTEXTO", "civitas":"CIVITAS / INTERVENCIÓN",
                             "final":"RESULTADO / TRANSMISIÓN"}
            banner = pygame.Surface((440, 76), pygame.SRCALPHA)
            lamina(banner, "banner_civitas" if fase == "civitas" else "banner_transicion",
                   pygame.Rect(0, 0, 440, 76))
            nombre_turno = nombres_turno.get(fase, "TRANSMISIÓN")
            texto_turno = tipo(22).render(nombre_turno, True, (250, 223, 178))
            banner.blit(texto_turno, texto_turno.get_rect(center=(220, 38)))
            a = min(1.0, t_fase / 0.18, (0.86-t_fase)/0.26)
            banner.set_alpha(int(235 * max(0.0, a)))
            canvas.blit(banner, (164, 280-int((1-a)*14)))

        # MULTIJUGADOR: a quién le toca decidir
        if (red is not None or auto) and turnos["aviso"] and fase in DUENO_FASE:
            texto_t = tipo(16).render(turnos["aviso"], True, COL_POLVO)
            barra_t = pygame.Rect(0, 0, texto_t.get_width() + 36, texto_t.get_height() + 12)
            barra_t.midtop = (ANCHO // 2, u(64))
            pygame.draw.rect(canvas, turnos["color"], barra_t, border_radius=6)
            canvas.blit(texto_t, texto_t.get_rect(center=barra_t.center))

        # cursor de mano al pasar sobre una opción
        if ui["hover"] != cursor_mano:
            cursor_mano = ui["hover"]
            try:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND if cursor_mano else pygame.SYSTEM_CURSOR_ARROW)
            except Exception:
                pass

        # indicaciones del modo ajuste
        if modo_ajuste:
            area = pygame.Rect(SCREEN_X, SCREEN_Y, SCREEN_ANCHO, u(330))
            pygame.draw.rect(canvas, COL_AMBAR, area, 1)
            pygame.draw.line(canvas, COL_AMBAR, (area.centerx, area.y - 8), (area.centerx, area.y + 8), 1)
            textos = ["MODO AJUSTE   (F2 para salir)",
                      "Flechas: mover (Shift = rápido)   - / + : tamaño   Enter: imprimir valores",
                      f"UI_ESCALA = {ajuste['escala']:.2f}    UI_CENTRO_X = {int(ajuste['x'])}    UI_Y = {int(ajuste['y'])}"]
            fondo_txt = pygame.Surface((ANCHO, 62), pygame.SRCALPHA)
            fondo_txt.fill((0, 0, 0, 190))
            canvas.blit(fondo_txt, (0, ALTO - 62))
            for k, t in enumerate(textos):
                canvas.blit(fuente_ajuste.render(t, True, COL_AMBAR if k == 0 else COL_PAPEL), (10, ALTO - 56 + k * 18))

        # Escala independiente: la ventana puede estirarse libremente sin bandas negras.
        lienzo_escalado = pygame.transform.smoothscale(canvas, display.get_size())
        display.blit(lienzo_escalado, (0, 0))
        pygame.display.update()

    for f in fondos.values():
        f.cerrar()
    return puntos_influencer, puntos_ciudadano