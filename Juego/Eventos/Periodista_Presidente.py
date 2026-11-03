import math
import pygame
from pathlib import Path
from Arbol.Arbol_AVL import ArbolAVL
from Arbol import Preguntas
import Metodos

try:
    import cv2          # pip install opencv-python   (solo hace falta si vas a usar videos)
except ImportError:
    cv2 = None

# ====== POSICIÓN Y TAMAÑO DE LA INTERFAZ ======
# Puedes cambiarlos aquí, o dentro del juego con el MODO AJUSTE (tecla F2):
#   flechas = mover (Shift = más rápido) | - / + = tamaño | Enter = imprime los valores en la consola
UI_ESCALA = 0.98          # tamaño de toda la interfaz (1.0 = como era antes)
UI_CENTRO_X = 435           # X del centro de la interfaz (el canvas mide 900 de ancho)
UI_Y = 120                  # Y donde empieza la interfaz (más chico = más arriba)
PANEL_CABECERA_ALFA = 140   # oscurece detrás del encabezado para que se lea sobre el video (0 = sin panel)
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

# ====== PALETA (la misma del campo minado) ======
COL_POLVO = (22, 18, 14)
COL_PAPEL = (214, 199, 166)
COL_OXIDO = (170, 82, 46)
COL_AMBAR = (232, 170, 74)
COL_AGUA = (96, 190, 205)
COL_ACERO = (96, 88, 76)
COL_APAGADO = (122, 112, 96)
COL_VIVO = (226, 70, 58)
COL_MALO = (235, 120, 86)

# Quién juega en cada fase: nombre, color (el mismo de Evento_2) e instrucción
ROLES = {
    "pregunta": ("Periodista", (255, 220, 70), "elige una pregunta"),
    "respuesta": ("Presidente", (70, 130, 255), "elige una respuesta"),
    "ciudadano": ("Ciudadano", (80, 220, 120), "¿qué tan honesta fue esta respuesta?"),
    "opinion": ("Influencer", (200, 110, 255), "da tu opinión sobre esta respuesta"),
}
ORDEN_FASES = ["pregunta", "respuesta", "ciudadano", "opinion"]
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


def forma_cortada(r, a=10, b=6):
    """Rectángulo con las esquinas cortadas en diagonal (en vez de redondeadas)."""
    return [(r.x + a, r.y), (r.right - 1, r.y), (r.right - 1, r.bottom - b),
            (r.right - b, r.bottom - 1), (r.x, r.bottom - 1), (r.x, r.y + a)]


def gota(surf, cx, cy, r, color, seca=False):
    if seca:
        color = (70, 62, 50)
    pygame.draw.polygon(surf, color, [(cx, cy - r * 1.85), (cx - r * 0.841, cy - r * 0.54),
                                      (cx + r * 0.841, cy - r * 0.54)])
    pygame.draw.circle(surf, color, (int(cx), int(cy)), max(1, int(r)))


def escalar_cover(img, ancho, alto):
    """Escala la imagen para llenar ancho x alto sin deformarla (recorta lo que sobre)."""
    iw, ih = img.get_size()
    k = max(ancho / iw, alto / ih)
    grande = pygame.transform.smoothscale(img, (max(ancho, int(iw * k)), max(alto, int(ih * k))))
    x0, y0 = (grande.get_width() - ancho) // 2, (grande.get_height() - alto) // 2
    return grande.subsurface((x0, y0, ancho, alto)).copy()


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


def Entrevista():
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
    pygame.display.set_caption("My Game")
    canvas = pygame.Surface((ANCHO, ALTO))

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
        "opinion": "influencer",
    }
    fondos = {clave: cargar_fondo(clave) for clave in fondo_por_fase.values()}

    # --- ajuste de la interfaz (posición y tamaño) ---
    ajuste = {"x": UI_CENTRO_X, "y": UI_Y, "escala": UI_ESCALA}
    modo_ajuste = False
    fuente_ajuste = pygame.font.SysFont("Consolas", 14)

    def u(n):
        """Convierte una medida del diseño original al tamaño actual de la interfaz."""
        return int(round(n * ajuste["escala"]))

    # Carga de la tipografía Upheaval desde los assets
    ruta_fuente = ruta_assets / "upheavtt.ttf"

    def tam_fuentes():
        return max(8, round(16 * ajuste["escala"])), max(10, round(22 * ajuste["escala"]))

    def crear_fuentes():
        t1, t2 = tam_fuentes()
        try:
            return pygame.font.Font(str(ruta_fuente), t1), pygame.font.Font(str(ruta_fuente), t2)
        except Exception:
            return pygame.font.SysFont("Consolas", t1), pygame.font.SysFont("Consolas", t2, bold=True)

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

    fase = "pregunta"
    id_pregunta_actual = None
    respuesta_elegida = None

    espectadores = 50
    puntos_influencer = 0
    puntos_ciudadano = 0
    preguntas_hechas = 0
    total_preguntas = len(preguntas)

    # Geometría de la interfaz: se recalcula en cada cuadro según el ajuste
    SCREEN_ANCHO = SCREEN_X = SCREEN_Y = Y_CONTENIDO = 0

    # --- estado de la interfaz ---
    reloj = pygame.time.Clock()
    capa = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)   # contenido que aparece con un fundido suave
    ui = {"hover": False}
    avisos = {}                          # "+8", "-6", "+5" que aparecen junto a los contadores
    tiempo = 0.0
    t_fase = 0.0
    fase_prev = fase
    cursor_mano = False

    # ------------------------------------------------------------ piezas de interfaz

    def panel_cabecera():
        if PANEL_CABECERA_ALFA <= 0:
            return
        r = pygame.Rect(SCREEN_X - u(12), SCREEN_Y - u(10), SCREEN_ANCHO + u(24), u(108))
        s = pygame.Surface(r.size, pygame.SRCALPHA)
        pygame.draw.polygon(s, (*COL_POLVO, PANEL_CABECERA_ALFA),
                            forma_cortada(pygame.Rect(0, 0, r.width, r.height), u(14), u(8)))
        canvas.blit(s, r.topleft)

    def contador(y, etiqueta, valor, clave, fuente_valor, color_valor, punto=False):
        x_r = SCREEN_X + SCREEN_ANCHO
        num = fuente_valor.render(str(valor), True, color_valor)
        r_num = num.get_rect(topright=(x_r, y))
        canvas.blit(num, r_num)

        aviso = avisos.get(clave)
        if aviso:
            img = fuente.render(aviso["txt"], True, aviso["color"])
            img.set_alpha(int(255 * min(1.0, aviso["t"] / 0.4)))
            canvas.blit(img, img.get_rect(midright=(r_num.left - u(8), r_num.centery)))

        lab = fuente.render(etiqueta, True, COL_VIVO if punto else COL_APAGADO)
        r_lab = lab.get_rect(midright=(r_num.left - u(56), r_num.centery))
        canvas.blit(lab, r_lab)
        if punto:   # puntito de "en vivo" que parpadea
            parpadeo = 0.5 + 0.5 * math.sin(tiempo * 4)
            pygame.draw.circle(canvas, mezclar((110, 30, 26), COL_VIVO, parpadeo),
                               (r_lab.left - u(12), r_lab.centery), max(2, u(5)))

    def cabecera():
        x_r = SCREEN_X + SCREEN_ANCHO

        # título y una marca por cada pregunta
        n_actual = min(preguntas_hechas + 1, total_preguntas)
        titulo = fuente_grande.render(f"Pregunta {n_actual} de {total_preguntas}", True, COL_PAPEL)
        canvas.blit(titulo, (SCREEN_X, SCREEN_Y))
        for k in range(total_preguntas):
            if k < preguntas_hechas:
                color = COL_AMBAR
            elif k == preguntas_hechas:
                color = COL_PAPEL
            else:
                color = COL_ACERO
            pygame.draw.rect(canvas, color, (SCREEN_X + k * u(16), SCREEN_Y + u(32), max(2, u(12)), max(2, u(6))))

        contador(SCREEN_Y, "en vivo", espectadores, "espectadores", fuente_grande, COL_PAPEL, punto=True)
        contador(SCREEN_Y + u(26), "confianza", puntos_ciudadano, "confianza", fuente, COL_AGUA)

        # línea divisoria con un tramo de óxido
        y_div = SCREEN_Y + u(50)
        pygame.draw.line(canvas, COL_ACERO, (SCREEN_X, y_div), (x_r, y_div), 1)
        pygame.draw.line(canvas, COL_OXIDO, (SCREEN_X, y_div), (SCREEN_X + u(48), y_div), max(2, u(3)))

        # de quién es el turno (con su color) y qué tiene que hacer
        nombre, color, instruccion = ROLES.get(fase, ROLES["pregunta"])
        etiqueta = fuente.render(nombre, True, COL_POLVO)
        sello = pygame.Rect(SCREEN_X, y_div + u(12), etiqueta.get_width() + u(24), u(26))
        pygame.draw.polygon(canvas, color, forma_cortada(sello, u(8), u(5)))
        canvas.blit(etiqueta, etiqueta.get_rect(center=sello.center))
        inst = fuente.render(instruccion, True, COL_PAPEL)
        canvas.blit(inst, inst.get_rect(midleft=(sello.right + u(14), sello.centery)))

        # los 4 turnos del ciclo: el actual se ve lleno, los pasados apagados, los que faltan en contorno
        i_act = ORDEN_FASES.index(fase) if fase in ORDEN_FASES else 0
        lado = max(6, u(12))
        for k, f in enumerate(ORDEN_FASES):
            col = ROLES[f][1]
            cuad = pygame.Rect(x_r - (4 - k) * u(18) + u(4), sello.centery - lado // 2, lado, lado)
            if k == i_act:
                pygame.draw.rect(canvas, col, cuad)
            elif k < i_act:
                pygame.draw.rect(canvas, mezclar(col, COL_POLVO, 0.6), cuad)
            else:
                pygame.draw.rect(canvas, mezclar(col, COL_POLVO, 0.4), cuad, 2)

    def bloque_cita(y, etiqueta, texto, color):
        """Lo que se dijo (pregunta o respuesta), con una barra del color de quien lo dijo."""
        lineas = dividir_en_lineas(texto, fuente, SCREEN_ANCHO - u(28))
        rect = pygame.Rect(SCREEN_X, y, SCREEN_ANCHO, u(38) + len(lineas) * u(20))
        pygame.draw.rect(capa, (22, 18, 14, 205), rect)
        pygame.draw.rect(capa, color, (rect.x, rect.y, max(3, u(5)), rect.height))
        capa.blit(fuente.render(etiqueta, True, color), (rect.x + u(18), rect.y + u(8)))
        yy = rect.y + u(30)
        for linea in lineas:
            capa.blit(fuente.render(linea, True, COL_PAPEL), (rect.x + u(18), yy))
            yy += u(20)
        return rect.bottom

    def tarjeta_opcion(rect, lineas, numero, color, mouse_pos, click, tecla):
        hover = rect.collidepoint(mouse_pos)
        if hover:
            ui["hover"] = True
        r = rect.move(u(4), 0) if hover else rect       # al pasar el mouse, la tarjeta se corre un poco
        forma = forma_cortada(r, u(10), u(6))
        pygame.draw.polygon(capa, (44, 36, 27, 245) if hover else (26, 21, 16, 235), forma)
        pygame.draw.polygon(capa, color if hover else COL_ACERO, forma, 2)
        pygame.draw.rect(capa, color if hover else mezclar(color, COL_POLVO, 0.55),
                         (r.x + u(2), r.y + u(14), max(3, u(5)), max(2, r.height - u(28))))

        lado = max(14, u(24))
        insignia = pygame.Rect(r.x + u(18), r.centery - lado // 2, lado, lado)   # número = tecla para elegir
        pygame.draw.rect(capa, color if hover else COL_PAPEL, insignia, border_radius=3)
        num = fuente.render(str(numero), True, COL_POLVO)
        capa.blit(num, num.get_rect(center=insignia.center))

        y = r.centery - (len(lineas) * u(19)) // 2
        for linea in lineas:
            capa.blit(fuente.render(linea, True, COL_PAPEL), (r.x + u(56), y))
            y += u(19)
        return (hover and click) or tecla == numero

    def lista_opciones(y, textos, color, mouse_pos, click, tecla):
        """Tarjetas apiladas; cada una crece según las líneas de su texto. Devuelve el índice elegido."""
        elegido = None
        for i, texto in enumerate(textos):
            lineas = dividir_en_lineas(texto, fuente, SCREEN_ANCHO - u(76)) or [""]
            rect = pygame.Rect(SCREEN_X, y, SCREEN_ANCHO, max(u(50), len(lineas) * u(19) + u(24)))
            if tarjeta_opcion(rect, lineas, i + 1, color, mouse_pos, click, tecla):
                elegido = i
            y += rect.height + u(8)
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
        sep = u(10)
        ancho_btn = (SCREEN_ANCHO - 2 * sep) // 3
        elegido = None
        for i, (etq, ico) in enumerate(zip(etiquetas, iconos)):
            rect = pygame.Rect(SCREEN_X + i * (ancho_btn + sep), y, ancho_btn, u(70))
            hover = rect.collidepoint(mouse_pos)
            if hover:
                ui["hover"] = True
            r = rect.move(0, -u(3)) if hover else rect  # al pasar el mouse, el botón sube un poco
            forma = forma_cortada(r, u(10), u(6))
            pygame.draw.polygon(capa, (44, 36, 27, 245) if hover else (26, 21, 16, 235), forma)
            pygame.draw.polygon(capa, color if hover else COL_ACERO, forma, 2)
            pygame.draw.rect(capa, color if hover else mezclar(color, COL_POLVO, 0.55),
                             (r.x + u(14), r.y + u(2), max(2, r.width - u(28)), max(2, u(4))))
            icono(ico, r.centerx, r.y + u(26), hover)
            t = fuente.render(etq, True, COL_PAPEL)
            capa.blit(t, t.get_rect(midbottom=(r.centerx, r.bottom - u(10))))
            capa.blit(fuente.render(str(i + 1), True, COL_APAGADO), (r.x + u(14), r.y + u(12)))
            if (hover and click) or tecla == i + 1:
                elegido = i
        return elegido

    # ------------------------------------------------------------ bucle principal

    running = True
    while running:
        dt = reloj.tick(60) / 1000
        tiempo += dt

        click = False
        tecla = 0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.VIDEORESIZE:
                display = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                click = True
            if event.type == pygame.KEYDOWN:
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

        SCREEN_ANCHO = u(580)
        SCREEN_X = int(ajuste["x"]) - SCREEN_ANCHO // 2
        SCREEN_Y = int(ajuste["y"])
        Y_CONTENIDO = SCREEN_Y + u(104)

        if fase != fase_prev:
            fase_prev = fase
            t_fase = 0.0
            if REINICIAR_VIDEO_AL_CAMBIAR:
                fondos[fondo_por_fase[fase]].reiniciar()
        t_fase += dt
        for clave in list(avisos):
            avisos[clave]["t"] -= dt
            if avisos[clave]["t"] <= 0:
                del avisos[clave]
        ui["hover"] = False

        ancho_ventana, alto_ventana = display.get_size()
        escala = min(ancho_ventana / ANCHO, alto_ventana / ALTO)
        offset_x = (ancho_ventana - int(ANCHO * escala)) // 2
        offset_y = (alto_ventana - int(ALTO * escala)) // 2
        mouse_pos = Metodos.mouse_en_canvas(escala, offset_x, offset_y)

        fondo_actual = fondos[fondo_por_fase[fase]]
        fondo_actual.actualizar(dt)
        canvas.blit(fondo_actual.superficie(), (0, 0))
        panel_cabecera()
        cabecera()

        capa.fill((0, 0, 0, 0))

        if fase == "pregunta":
            visibles = ids_disponibles[:3]
            i = lista_opciones(Y_CONTENIDO, [preguntas[id_p] for id_p in visibles],
                               ROLES["pregunta"][1], mouse_pos, click, tecla)
            if i is not None:
                id_p = visibles[i]
                if arbol_preguntas.get(id_p) is not None:
                    id_pregunta_actual = id_p
                    ids_disponibles.remove(id_p)
                    arbol_preguntas.eliminar(id_p)
                    fase = "respuesta"

        elif fase == "respuesta":
            y = bloque_cita(Y_CONTENIDO, "Periodista preguntó", preguntas[id_pregunta_actual],
                            ROLES["pregunta"][1]) + u(12)

            opciones_nodo = arbol_respuestas.get(id_pregunta_actual)
            opciones = respuestas[id_pregunta_actual] if opciones_nodo is not None else {}
            claves = ["muy_buena", "regular", "mala"]

            i = lista_opciones(y, [opciones.get(c, "") for c in claves],
                               ROLES["respuesta"][1], mouse_pos, click, tecla)
            if i is not None:
                respuesta_elegida = claves[i]
                fase = "ciudadano"

        elif fase == "ciudadano":
            y = bloque_cita(Y_CONTENIDO, "Presidente respondió",
                            respuestas[id_pregunta_actual][respuesta_elegida], ROLES["respuesta"][1]) + u(14)
            claves_juicio = ["muy_buena", "regular", "mala"]
            i = fila_botones(y, ["Muy buena", "Regular", "Mala"], ["gotas3", "gotas2", "gotas1"],
                             ROLES["ciudadano"][1], mouse_pos, click, tecla)
            if i is not None:
                if respuesta_elegida == claves_juicio[i]:
                    puntos_ciudadano += 5
                    avisos["confianza"] = {"txt": "+5", "color": COL_AGUA, "t": 1.4}
                fase = "opinion"

        elif fase == "opinion":
            y = bloque_cita(Y_CONTENIDO, "Presidente respondió",
                            respuestas[id_pregunta_actual][respuesta_elegida], ROLES["respuesta"][1]) + u(14)
            cambios = [8, 2, -6]
            i = fila_botones(y, ["Positiva", "Imparcial", "Mala"], ["sube", "igual", "baja"],
                             ROLES["opinion"][1], mouse_pos, click, tecla)
            if i is not None:
                espectadores += cambios[i]
                avisos["espectadores"] = {"txt": f"{cambios[i]:+d}",
                                          "color": COL_AGUA if cambios[i] > 0 else COL_MALO, "t": 1.4}
                fase = "siguiente"

        # el contenido de cada fase aparece con un fundido corto y sube un poquito
        aparicion = 1 - (1 - min(1.0, t_fase / 0.22)) ** 3
        capa.set_alpha(int(255 * aparicion))
        canvas.blit(capa, (0, int((1 - aparicion) * u(14))))

        if fase == "siguiente":
            preguntas_hechas += 1
            id_pregunta_actual = None
            respuesta_elegida = None

            if not ids_disponibles:
                if espectadores >= 70:
                    puntos_influencer += 10
                else:
                    puntos_influencer -= 5
                running = False
            else:
                fase = "pregunta"

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

        Metodos.mostrar_canvas(display, canvas)
        pygame.display.update()

    for f in fondos.values():
        f.cerrar()
    return puntos_influencer, puntos_ciudadano