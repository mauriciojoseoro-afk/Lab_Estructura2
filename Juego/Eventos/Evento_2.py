import sys
import math
import random
from pathlib import Path
import pygame
import Metodos

# ====== AJUSTES DEL EVENTO ======
NUM_MINAS = 450
DISTANCIA_MINIMA = 52
MINAS_VISIBLES = False      # solo para pruebas: si es True las minas se ven siempre
VIDAS = 2

# --- PODER (tecla B): muestra las minas un momento ---
TECLA_PODER = pygame.K_b
DURACION_PODER = 8.0        # segundos que se ven las minas
ESPERA_PODER = 5.0         # segundos para volver a usarlo (cuentan desde que lo activas)
# -----------------------------------------------------

# --- SEPARACIÓN DE TAMAÑOS ---
RADIO_SPRITE_VISUAL = 75    # Tamaño gigante para que se vea genial y detallado en pantalla
RADIO_HITBOX = 12           # Hitbox pequeña y justa: está en los PIES del personaje
# -----------------------------

RADIO_MINA = 7
VELOCIDAD = 170

ANCHO = 1600
ALTO = 900
ALTO_MUNDO = 3600
ALTO_META = 160             # zona sin minas al final (el personaje llega con la cabeza al borde, necesita espacio)
ALTO_INICIO = 80
PAUSA_ENTRE_PAREJAS = 2.5   # subí esto de 1 a 2.5 para que alcance a leerse el resultado de la pareja
INVULNERABLE = 2.0

# --- FONDO ---
# Copia la imagen mejorada a Assets/Interfaz y ponle este nombre.
FONDO = "Mapa_evnt2.jpg"
ALTURA_CORTE_TERRENO = 815  # separa el terreno de la plataforma inferior de la imagen
# -------------

# --- EFECTOS VISUALES (no necesitan imagenes adicionales) ---
ACTIVAR_SOMBRAS = True
ACTIVAR_POLVO = True
ACTIVAR_ILUMINACION = True
ACTIVAR_PROGRESO = True
CANTIDAD_PARTICULAS = 190
DURACION_DESTELLO = 0.36
DURACION_SACUDIDA = 0.24
DURACION_GOTA = 0.7         # tiempo que tarda en "evaporarse" la gota cuando pierdes una vida
# -----------------------------------------------------------

# --- MINI INTERFAZ DE ARRIBA: una imagen por pareja, guardadas en Assets/Interfaz ---
IMAGENES_DUO = ["Duo_1.png", "Duo_2.png"]   # 1a pareja (Presidente + Influencer) y 2a pareja (Periodista + Ciudadano)
# ------------------------------------------------------------------------------------

# --- TIPOGRAFIAS (opcionales): ponlas en Assets/Fuentes. Si no estan, usa fuentes del sistema ---
# Recomendadas (gratis en Google Fonts): "Stardos Stencil" (titulos) y "Special Elite" (maquina de escribir)
FUENTE_TITULO_TTF = "StardosStencil-Bold.ttf"
FUENTE_TEXTO_TTF = "SpecialElite-Regular.ttf"
VELOCIDAD_TEXTO = 70        # letras por segundo en la maquina de escribir del tutorial
# -------------------------------------------------------------------------------------------
# ================================

# ====== PALETA DE LA INTERFAZ ======
# Todo el mundo es polvo, oxido y metal viejo; el UNICO color frio es el agua.
# Asi el agua (vidas y deposito) es lo que mas llama la atencion, igual que en la historia.
COL_POLVO = (22, 18, 14)
COL_PAPEL = (214, 199, 166)
COL_TINTA = (44, 34, 24)
COL_OXIDO = (170, 82, 46)
COL_AMBAR = (232, 170, 74)
COL_AGUA = (96, 190, 205)
COL_ACERO = (96, 88, 76)
COL_APAGADO = (122, 112, 96)
COL_MINA = (220, 40, 40)
# ===================================

FPS_ANIMACION = 12
ESCALA_SPRITE = 1.0

# --- PRUEBA DE SPRITES: usa el cuerpo de otro personaje sin cambiar nombres ni HUD ---
# {"Ciudadano": "Sobreviviente"} = el Ciudadano (punto verde) se dibuja con los sprites de Sobreviviente.
# Deja el diccionario vacio ({}) para volver a la normalidad.
SPRITES_PRUEBA = {"Ciudadano": "Sobreviviente"}
# ---------------------------------------------------------------------------------------

ALTURA_SPRITE = int(RADIO_SPRITE_VISUAL * 2 * ESCALA_SPRITE)
LIMITE_ARRIBA = ALTURA_SPRITE - RADIO_HITBOX   # y mínima de los pies para que la cabeza no se salga por arriba

WASD = (pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d)
FLECHAS = (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT)

PAREJAS = [
    [("Presidente", (70, 130, 255), WASD), ("Influencer", (200, 110, 255), FLECHAS)],
    [("Periodista", (255, 220, 70), WASD), ("Ciudadano", (80, 220, 120), FLECHAS)],
]

ESTADOS_MOVIMIENTO = ["arriba", "abajo", "izquierda", "derecha", "corriendo"]
ESTADOS_QUIETO = ["quieto", "quieto_arriba", "quieto_abajo", "quieto_izquierda", "quieto_derecha"]

ANIMACIONES = {}
FUENTES = {}


def carpeta_assets(*partes):
    base = Path(__file__).resolve().parent.parent
    ruta = base.joinpath("Assets", *partes)
    if not ruta.exists():
        ruta = base.parent.joinpath("Assets", *partes)
    return ruta


# ---------------------------------------------------------------- animaciones

def cargar_frames(carpeta):
    originales = []
    idx = 1
    while True:
        archivo = carpeta / f"frame_{idx:02d}.png"
        if not archivo.exists():
            archivo = carpeta / f"frame_{idx:02d}.PNG"
        if not archivo.exists():
            archivo = carpeta / f"frame_{idx}.png"
        if not archivo.exists():
            archivo = carpeta / f"frame_{idx}.PNG"
        if not archivo.exists():
            break
        try:
            originales.append(pygame.image.load(str(archivo)).convert_alpha())
        except Exception as e:
            print(f"[Evento_2] No se pudo cargar {archivo}: {e}")
            break
        idx += 1

    if not originales:
        return []

    # Caja que contiene al personaje en TODOS los cuadros de esta animación.
    # Se usa la misma caja y la misma escala para todos, así no "palpita" al caminar.
    caja = None
    for img in originales:
        r = img.get_bounding_rect(50)          # solo píxeles visibles (alfa >= 128)
        if r.width > 0 and r.height > 0:
            caja = r if caja is None else caja.union(r)
    if caja is None:
        caja = originales[0].get_rect()

    escala = ALTURA_SPRITE / caja.height
    nuevo_ancho = max(1, int(caja.width * escala))

    imgs = []
    for img in originales:
        recorte = img.subsurface(caja).copy()
        imgs.append(pygame.transform.smoothscale(recorte, (nuevo_ancho, ALTURA_SPRITE)))
    return imgs


def cargar_animaciones():
    ANIMACIONES.clear()
    ruta_base = carpeta_assets("Personajes")

    for pareja in PAREJAS:
        for nombre, color, teclas in pareja:
            ANIMACIONES[nombre] = {}
            carpeta = SPRITES_PRUEBA.get(nombre, nombre)      # p.ej. el Ciudadano usa los sprites de Sobreviviente
            ruta_personaje = ruta_base / carpeta / "Hombre" if carpeta == "Periodista" else ruta_base / carpeta
            if not ruta_personaje.exists():
                if nombre == "Periodista":
                    print(f"[Evento_2] No se encuentra el periodista hombre en: {ruta_personaje}")
                continue

            for estado in ESTADOS_MOVIMIENTO + ESTADOS_QUIETO:
                ruta_estado = ruta_personaje / estado
                ANIMACIONES[nombre][estado] = cargar_frames(ruta_estado) if ruta_estado.exists() else []
            if nombre == "Periodista":
                cantidad = sum(len(v) for v in ANIMACIONES[nombre].values())
                print(f"[Evento_2] Periodista hombre: {cantidad} fotogramas cargados")

            # si falta una animación de movimiento, usa otra de movimiento que sí exista
            respaldo = next((ANIMACIONES[nombre][e] for e in ESTADOS_MOVIMIENTO if ANIMACIONES[nombre][e]), [])
            for estado in ESTADOS_MOVIMIENTO:
                if not ANIMACIONES[nombre][estado]:
                    ANIMACIONES[nombre][estado] = respaldo
            # las de "quieto" NO se rellenan: si no existen, parado se ve un solo cuadro (sin caminar en el lugar)


def elegir_fotogramas(nombre, estado, ultima_direccion):
    """Devuelve (lista de cuadros, animar). Si animar es False se muestra solo el primer cuadro."""
    anim = ANIMACIONES.get(nombre)
    if not anim:
        return [], False

    if estado == "quieto":
        for clave in (f"quieto_{ultima_direccion}", "quieto"):
            if anim.get(clave):
                return anim[clave], True
        fotogramas = anim.get(ultima_direccion) or anim.get("corriendo") or []
        if not fotogramas:
            fotogramas = next((lista for lista in anim.values() if lista), [])
        return fotogramas, False

    fotogramas = anim.get(estado) or anim.get("corriendo") or []
    if not fotogramas:
        fotogramas = next((lista for lista in anim.values() if lista), [])
    return fotogramas, True


def actualizar_animacion(jugador, dt):
    fotogramas, animar = elegir_fotogramas(jugador["nombre"], jugador["estado"], jugador["ultima_direccion"])

    clave = (jugador["estado"], jugador["ultima_direccion"] if jugador["estado"] == "quieto" else None)
    if jugador.get("clave_anim") != clave:
        jugador["clave_anim"] = clave
        jugador["animacion_tiempo"] = 0.0      # al cambiar de estado, arranca desde el primer cuadro

    if not fotogramas:
        jugador["frame_activo"] = None
        return

    if animar:
        jugador["animacion_tiempo"] += dt
        indice = int(jugador["animacion_tiempo"] * FPS_ANIMACION) % len(fotogramas)
    else:
        indice = 0
    jugador["frame_activo"] = fotogramas[indice]


# ---------------------------------------------------------------- mundo

def crear_minas():
    minas = []
    celdas = {}
    intentos = 0
    while len(minas) < NUM_MINAS and intentos < 60000:
        intentos += 1
        x = random.randint(35, ANCHO - 35)
        y = random.randint(ALTO_META + 35, ALTO_MUNDO - ALTO_INICIO - 35)
        cx, cy = x // DISTANCIA_MINIMA, y // DISTANCIA_MINIMA

        libre = True
        for i in (cx - 1, cx, cx + 1):
            for k in (cy - 1, cy, cy + 1):
                for mx, my in celdas.get((i, k), ()):
                    if math.hypot(x - mx, y - my) < DISTANCIA_MINIMA:
                        libre = False

        if libre:
            minas.append((x, y))
            celdas.setdefault((cx, cy), []).append((x, y))
    return minas


def crear_jugadores(pareja):
    jugadores = []
    for i, (nombre, color, teclas) in enumerate(pareja):
        x = ANCHO // 3 * (i + 1)
        y = ALTO_MUNDO - ALTO_INICIO + 20       # (x, y) es la posición de los PIES
        jugador = {
            "nombre": nombre,
            "color": color,
            "teclas": teclas,
            "x": x,
            "y": y,
            "inicio": (x, y),
            "vidas": VIDAS,
            "gota_t": 0.0,                      # animación de la gota que se pierde en el HUD
            "invulnerable": 0.0,
            "llego": False,
            "eliminado": False,
            "estado": "quieto",
            "ultima_direccion": "derecha",
            "animacion_tiempo": 0.0,
            "clave_anim": None,
            "frame_activo": None,
        }
        actualizar_animacion(jugador, 0)        # así desde el primer cuadro se ve el sprite y no la bolita
        jugadores.append(jugador)
    return jugadores


def mover(jugador, presionadas, dt):
    arriba, abajo, izquierda, derecha = jugador["teclas"]
    dx = presionadas[derecha] - presionadas[izquierda]
    dy = presionadas[abajo] - presionadas[arriba]

    if dx > 0:
        jugador["estado"] = "derecha"
        jugador["ultima_direccion"] = "derecha"
    elif dx < 0:
        jugador["estado"] = "izquierda"
        jugador["ultima_direccion"] = "izquierda"
    elif dy > 0:
        jugador["estado"] = "abajo"
        jugador["ultima_direccion"] = "abajo"
    elif dy < 0:
        jugador["estado"] = "arriba"
        jugador["ultima_direccion"] = "arriba"
    else:
        jugador["estado"] = "quieto"

    if dx and dy:
        dx *= 0.7071
        dy *= 0.7071

    jugador["x"] = max(RADIO_HITBOX, min(ANCHO - RADIO_HITBOX, jugador["x"] + dx * VELOCIDAD * dt))
    jugador["y"] = max(LIMITE_ARRIBA, min(ALTO_MUNDO - RADIO_HITBOX, jugador["y"] + dy * VELOCIDAD * dt))


# ---------------------------------------------------------------- fondo

def preparar_fondo(imagen):
    """Construye el recorrido sin deformar el terreno ni reflejarlo."""
    ancho_original, alto_original = imagen.get_size()
    corte = max(1, min(ALTURA_CORTE_TERRENO, alto_original - 1))

    # Separamos el terreno de la plataforma inferior.
    terreno_original = imagen.subsurface((0, 0, ancho_original, corte)).copy()
    alto_terreno = max(1, int(terreno_original.get_height() * ANCHO / ancho_original))
    terreno = pygame.transform.smoothscale(terreno_original, (ANCHO, alto_terreno)).convert()

    # Repetimos siempre la imagen en su orientacion original. Para disimular
    # las uniones, mezclamos suavemente una franja entre una copia y la siguiente.
    fondo = pygame.Surface((ANCHO, ALTO_MUNDO)).convert()
    solape = min(70, max(24, alto_terreno // 12))
    paso = max(1, alto_terreno - solape)

    fondo.blit(terreno, (0, 0))
    y = paso
    while y < ALTO_MUNDO:
        fondo.blit(terreno, (0, y))

        # Mezcla progresiva entre el borde inferior de la copia anterior
        # y el borde superior de la nueva copia. Evita el reflejo invertido.
        for fila in range(solape):
            progreso = fila / max(1, solape - 1)
            anterior = terreno.subsurface((0, alto_terreno - solape + fila, ANCHO, 1)).copy()
            nueva = terreno.subsurface((0, fila, ANCHO, 1)).copy()
            anterior.set_alpha(int(255 * (1 - progreso)))
            nueva.set_alpha(int(255 * progreso))
            fondo.blit(anterior, (0, y + fila))
            fondo.blit(nueva, (0, y + fila))

        y += paso

    # La plataforma se coloca una sola vez, al final del recorrido.
    plataforma_original = imagen.subsurface((0, corte, ancho_original, alto_original - corte)).copy()
    alto_plataforma = max(1, int(plataforma_original.get_height() * ANCHO / ancho_original))
    plataforma = pygame.transform.smoothscale(plataforma_original, (ANCHO, alto_plataforma)).convert()
    y_plataforma = max(0, ALTO_MUNDO - alto_plataforma)
    fondo.blit(plataforma, (0, y_plataforma))

    print(f"[Evento_2] Fondo preparado: {ANCHO}x{ALTO_MUNDO}; terreno sin reflejos; plataforma inferior unica.")
    return fondo


def dibujar_fondo(canvas, fondo, camara):
    if fondo is None:
        canvas.fill((52, 56, 60))
        for y_linea in range(0, ALTO_MUNDO + 1, 100):
            sy = y_linea - camara
            if 0 <= sy <= ALTO:
                pygame.draw.line(canvas, (62, 66, 70), (0, sy), (ANCHO, sy), 1)
        return

    canvas.blit(fondo, (0, 0), (0, camara, ANCHO, ALTO))


# ---------------------------------------------------------------- efectos visuales

def crear_particulas_polvo(cantidad):
    """Crea particulas de polvo mas visibles, repartidas por el recorrido."""
    particulas = []
    for _ in range(cantidad):
        particulas.append({
            "x": random.uniform(0, ANCHO),
            "y": random.uniform(0, ALTO_MUNDO),
            "tam": random.choice((2, 2, 3, 3, 4)),
            "velocidad": random.uniform(9, 24),
            "fase": random.uniform(0, math.tau),
            "alfa": random.randint(115, 195)
        })
    return particulas


def actualizar_particulas_polvo(particulas, dt, tiempo):
    for p in particulas:
        p["y"] -= p["velocidad"] * dt
        p["x"] += math.sin(tiempo * 1.15 + p["fase"]) * 12 * dt
        if p["y"] < 0:
            p["y"] = ALTO_MUNDO
            p["x"] = random.uniform(0, ANCHO)
        if p["x"] < 0:
            p["x"] = ANCHO
        elif p["x"] > ANCHO:
            p["x"] = 0


def dibujar_particulas_polvo(canvas, particulas, camara, capa):
    """Dibuja particulas claras con un halo suave para que se distingan del suelo."""
    capa.fill((0, 0, 0, 0))
    for p in particulas:
        sy = int(p["y"] - camara)
        if -10 <= sy <= ALTO + 10:
            x = int(p["x"])
            tam = p["tam"]
            color = (255, 232, 190)
            pygame.draw.circle(capa, (*color, max(25, p["alfa"] // 4)), (x, sy), tam * 3)
            pygame.draw.circle(capa, (*color, p["alfa"]), (x, sy), tam)
    canvas.blit(capa, (0, 0))


def crear_sombra():
    """Sombra baja y discreta, colocada un poco detras de los pies."""
    sombra = pygame.Surface((52, 16), pygame.SRCALPHA)
    pygame.draw.ellipse(sombra, (18, 14, 10, 62), (2, 2, 48, 12))
    return sombra


def dibujar_sombra_personaje(canvas, sombra, jugador, sy):
    x = int(jugador["x"] - sombra.get_width() / 2)
    # En pantalla, unos pixeles por debajo de los pies equivale a dejarla atras.
    y = int(sy + RADIO_HITBOX - 3)
    canvas.blit(sombra, (x, y))


def crear_capa_ambiente():
    """Tinte calido y viñeta ligera precalculados para no gastar CPU cada frame."""
    capa = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    if not ACTIVAR_ILUMINACION:
        return capa

    capa.fill((75, 48, 22, 18))
    grosor = 42
    for i in range(grosor):
        alfa = int(42 * ((grosor - i) / grosor) ** 2)
        pygame.draw.rect(capa, (18, 13, 9, alfa), (i, i, ANCHO - 2 * i, 2))
        pygame.draw.rect(capa, (18, 13, 9, alfa), (i, ALTO - i - 2, ANCHO - 2 * i, 2))
        pygame.draw.rect(capa, (18, 13, 9, alfa), (i, i, 2, ALTO - 2 * i))
        pygame.draw.rect(capa, (18, 13, 9, alfa), (ANCHO - i - 2, i, 2, ALTO - 2 * i))
    return capa


def crear_explosion(particulas, ondas, x, y):
    """Estallido mas contundente: chispas, polvo, fragmentos y ondas expansivas."""
    # Fragmentos principales: salen disparados en todas las direcciones.
    for _ in range(48):
        angulo = random.uniform(0, math.tau)
        velocidad = random.uniform(85, 290)
        particulas.append({
            "x": float(x), "y": float(y),
            "vx": math.cos(angulo) * velocidad,
            "vy": math.sin(angulo) * velocidad - random.uniform(10, 65),
            "vida": random.uniform(0.38, 0.9),
            "vida_max": 0.9,
            "tam": random.randint(2, 7),
            "color": random.choice(((255, 190, 85), (230, 125, 48), (190, 75, 42),
                                    (105, 91, 76), (225, 205, 165), (255, 225, 165)))
        })

    # Polvo mas grande que se abre cerca del suelo.
    for _ in range(16):
        angulo = random.uniform(0, math.tau)
        velocidad = random.uniform(25, 115)
        particulas.append({
            "x": float(x), "y": float(y),
            "vx": math.cos(angulo) * velocidad,
            "vy": math.sin(angulo) * velocidad - 18,
            "vida": random.uniform(0.55, 1.05),
            "vida_max": 1.05,
            "tam": random.randint(5, 10),
            "color": random.choice(((145, 119, 88), (174, 143, 105), (202, 174, 133)))
        })

    ondas.append({"x": float(x), "y": float(y), "radio": 8.0, "vida": 0.42, "vida_max": 0.42})
    ondas.append({"x": float(x), "y": float(y), "radio": 4.0, "vida": 0.28, "vida_max": 0.28})


def actualizar_explosiones(particulas, ondas, dt):
    for p in particulas[:]:
        p["x"] += p["vx"] * dt
        p["y"] += p["vy"] * dt
        p["vy"] += 185 * dt
        p["vida"] -= dt
        if p["vida"] <= 0:
            particulas.remove(p)

    for onda in ondas[:]:
        onda["radio"] += 245 * dt
        onda["vida"] -= dt
        if onda["vida"] <= 0:
            ondas.remove(onda)


def dibujar_explosiones(canvas, particulas, ondas, camara):
    # Ondas expansivas visibles sobre el terreno.
    for onda in ondas:
        sy = int(onda["y"] - camara)
        if -100 <= sy <= ALTO + 100:
            progreso = 1 - onda["vida"] / onda["vida_max"]
            grosor = max(1, int(6 * (1 - progreso)))
            color = (235, 166, 83) if onda["vida_max"] > 0.3 else (255, 220, 155)
            pygame.draw.circle(canvas, color, (int(onda["x"]), sy), int(onda["radio"]), grosor)

    # Chispas y fragmentos con una pequeña estela.
    for p in particulas:
        sy = int(p["y"] - camara)
        if -20 <= sy <= ALTO + 20:
            progreso = max(0.0, min(1.0, p["vida"] / p["vida_max"]))
            radio = max(1, int(p["tam"] * (0.55 + progreso * 0.45)))
            pygame.draw.circle(canvas, p["color"], (int(p["x"]), sy), radio)
            if p["tam"] >= 5:
                pygame.draw.circle(canvas, (255, 220, 160), (int(p["x"]), sy), max(1, radio // 2))


def dibujar_destello_dano(canvas, tiempo_restante):
    if tiempo_restante > 0:
        alfa = int(105 * min(1, tiempo_restante / DURACION_DESTELLO))
        capa = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        capa.fill((190, 25, 25, alfa))
        canvas.blit(capa, (0, 0))


# ---------------------------------------------------------------- textos flotantes (feedback en el mundo)

def crear_texto_flotante(lista, x, y, texto, color):
    lista.append({"x": x, "y": y, "texto": texto, "color": color, "vida": 1.1})


def actualizar_textos(lista, dt):
    for t in lista[:]:
        t["y"] -= 38 * dt
        t["vida"] -= dt
        if t["vida"] <= 0:
            lista.remove(t)


def dibujar_textos(canvas, lista, camara):
    for t in lista:
        sy = int(t["y"] - camara)
        if not (-40 <= sy <= ALTO + 40):
            continue
        alfa = int(255 * min(1.0, t["vida"] / 0.4))
        sombra = render_texto(t["texto"], FUENTES["nombre"], COL_POLVO).copy()
        img = render_texto(t["texto"], FUENTES["nombre"], t["color"]).copy()
        sombra.set_alpha(alfa)
        img.set_alpha(alfa)
        rect = img.get_rect(center=(int(t["x"]), sy))
        canvas.blit(sombra, rect.move(1, 2))
        canvas.blit(img, rect)


# ================================================================
#  INTERFAZ
#  Idea: el juego va de AGUA escasa en unas ruinas. Todo lo que se ve en pantalla
#  sale de ese mundo: las vidas son gotas, el progreso es una ruta hacia un deposito
#  que se llena, el escaner es un radar, el tutorial es una nota recuperada.
# ================================================================

def mezclar(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


# ---------------------------------------------------------------- tipografia

_CACHE_TEXTO = {}


def _cargar_fuente(archivo, nombres_sistema, tam, negrita=False):
    if archivo:
        ruta = carpeta_assets("Fuentes", archivo)
        if ruta.exists():
            try:
                return pygame.font.Font(str(ruta), tam)
            except Exception as e:
                print(f"[Evento_2] No se pudo cargar la fuente {ruta}: {e}")
    return pygame.font.SysFont(nombres_sistema, tam, bold=negrita)


def cargar_fuentes():
    FUENTES.clear()
    _CACHE_TEXTO.clear()
    titulares = "impact,haettenschweiler,arialnarrow,arial"
    maquina = "couriernew,consolas,dejavusansmono,courier"
    FUENTES["nombre"] = _cargar_fuente(FUENTE_TITULO_TTF, titulares, 27)
    FUENTES["titulo"] = _cargar_fuente(FUENTE_TITULO_TTF, titulares, 54)
    FUENTES["tecla"] = _cargar_fuente(FUENTE_TITULO_TTF, titulares, 20)
    FUENTES["cuerpo"] = _cargar_fuente(FUENTE_TEXTO_TTF, maquina, 28, True)
    FUENTES["nota"] = _cargar_fuente(FUENTE_TEXTO_TTF, maquina, 19, True)
    FUENTES["pequena"] = _cargar_fuente(FUENTE_TEXTO_TTF, maquina, 16, True)


def render_texto(texto, fuente, color):
    clave = (texto, id(fuente), color)
    img = _CACHE_TEXTO.get(clave)
    if img is None:
        if len(_CACHE_TEXTO) > 400:
            _CACHE_TEXTO.clear()
        img = fuente.render(texto, True, color)
        _CACHE_TEXTO[clave] = img
    return img


def escribir(canvas, texto, fuente, color, pos, ancla="topleft", sombra=True):
    """Dibuja texto con una sombrita dura para que se lea sobre cualquier parte del mapa."""
    img = render_texto(texto, fuente, color)
    rect = img.get_rect(**{ancla: pos})
    if sombra:
        canvas.blit(render_texto(texto, fuente, COL_POLVO), rect.move(1, 2))
    canvas.blit(img, rect)
    return rect


def dividir_en_lineas(texto, fuente, ancho):
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


# ---------------------------------------------------------------- piezas base

_CACHE_PLACAS = {}


def placa(canvas, rect, corte=18, alfa=214):
    """Placa de metal con esquinas cortadas (no redondeadas) y una franja de oxido arriba."""
    clave = (rect.w, rect.h, corte, alfa)
    img = _CACHE_PLACAS.get(clave)
    if img is None:
        w, h = rect.size
        img = pygame.Surface((w, h), pygame.SRCALPHA)
        puntos = [(corte, 0), (w - 1, 0), (w - 1, h - corte // 2), (w - corte // 2, h - 1), (0, h - 1), (0, corte)]
        pygame.draw.polygon(img, (*COL_POLVO, alfa), puntos)
        pygame.draw.polygon(img, COL_ACERO, puntos, 2)
        pygame.draw.line(img, COL_OXIDO, (corte + 6, 4), (w - 8, 4), 3)
        _CACHE_PLACAS[clave] = img
    canvas.blit(img, rect.topleft)


def dibujar_tecla(canvas, texto, x, y, brillo=0.0):
    """Tecla de teclado dibujada: asi el jugador reconoce el boton que tiene que pulsar."""
    img = render_texto(texto, FUENTES["tecla"], COL_TINTA)
    w = max(30, img.get_width() + 18)
    h = 26
    pygame.draw.rect(canvas, (60, 52, 42), (x, y + 4, w, h), border_radius=4)
    tapa = pygame.Rect(x, y, w, h)
    pygame.draw.rect(canvas, mezclar(COL_PAPEL, COL_AMBAR, brillo), tapa, border_radius=4)
    canvas.blit(img, img.get_rect(center=tapa.center))
    return pygame.Rect(x, y, w, h + 4)


def dibujar_gota(canvas, cx, cy, r, color, seca=False):
    """Gota de agua. (cx, cy) es el centro de la parte redonda; la punta sube desde ahi."""
    r = max(2.0, r)
    t1 = (cx - r * 0.841, cy - r * 0.54)
    t2 = (cx + r * 0.841, cy - r * 0.54)
    punta = (cx, cy - r * 1.85)
    if seca:
        color = (58, 50, 41)
    pygame.draw.polygon(canvas, color, [punta, t1, t2])
    pygame.draw.circle(canvas, color, (int(cx), int(cy)), int(r))
    if seca:
        grieta = [(cx - r * 0.1, cy - r * 1.1), (cx + r * 0.25, cy - r * 0.4),
                  (cx - r * 0.15, cy + r * 0.05), (cx + r * 0.2, cy + r * 0.6)]
        pygame.draw.lines(canvas, COL_APAGADO, False, grieta, 1)
    else:
        brillo = mezclar(color, (255, 255, 255), 0.55)
        pygame.draw.circle(canvas, brillo, (int(cx - r * 0.38), int(cy - r * 0.12)), max(1, int(r * 0.22)))


def dibujar_arco(canvas, color, cx, cy, r, fraccion, ancho=4):
    fraccion = max(0.0, min(1.0, fraccion))
    if fraccion <= 0:
        return
    pasos = max(2, int(48 * fraccion))
    puntos = []
    for i in range(pasos + 1):
        a = -math.pi / 2 + math.tau * fraccion * i / pasos
        puntos.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    pygame.draw.lines(canvas, color, False, puntos, ancho)


def dibujar_radar(canvas, cx, cy, r, angulo, color, barrido=True, minas=None):
    """Radar del escaner. 'minas' es una lista de (angulo, distancia 0-1) que se iluminan al pasar el barrido."""
    fondo = (16, 22, 21)
    tenue = mezclar(color, fondo, 0.78)
    pygame.draw.circle(canvas, fondo, (cx, cy), r)
    pygame.draw.circle(canvas, mezclar(color, fondo, 0.5), (cx, cy), r, 2)
    pygame.draw.circle(canvas, tenue, (cx, cy), max(2, r // 2), 1)
    pygame.draw.line(canvas, tenue, (cx - r, cy), (cx + r, cy), 1)
    pygame.draw.line(canvas, tenue, (cx, cy - r), (cx, cy + r), 1)

    if barrido:
        n, abanico = 14, 1.0
        for k in range(n):
            a1 = angulo - k * abanico / n
            a2 = angulo - (k + 1) * abanico / n
            p1 = (cx + math.cos(a1) * (r - 2), cy + math.sin(a1) * (r - 2))
            p2 = (cx + math.cos(a2) * (r - 2), cy + math.sin(a2) * (r - 2))
            pygame.draw.polygon(canvas, mezclar(color, fondo, 0.25 + 0.75 * k / n), [(cx, cy), p1, p2])
        pygame.draw.line(canvas, color, (cx, cy),
                         (cx + math.cos(angulo) * (r - 2), cy + math.sin(angulo) * (r - 2)), 2)

    if minas:
        for ang, dist in minas:
            diff = (angulo - ang) % math.tau
            if diff < 3.6:
                f = 1 - diff / 3.6
                px = cx + math.cos(ang) * dist * r
                py = cy + math.sin(ang) * dist * r
                pygame.draw.circle(canvas, mezclar(fondo, COL_MINA, f), (int(px), int(py)), max(3, r // 28))


def dibujar_tanque(canvas, cx, y, ancho, alto, nivel):
    """Deposito de agua con ventanilla. Devuelve la posicion del grifo (para animar gotas)."""
    x = cx - ancho // 2
    cuerpo = pygame.Rect(x, y + int(alto * 0.14), ancho, int(alto * 0.64))
    grosor_pata = max(3, ancho // 14)

    for lado in (-1, 1):
        px = cx + lado * int(ancho * 0.34)
        pygame.draw.line(canvas, COL_ACERO, (px, cuerpo.bottom), (px + lado * int(ancho * 0.06), y + alto), grosor_pata)

    pygame.draw.ellipse(canvas, (58, 51, 43), (x, cuerpo.bottom - int(alto * 0.14), ancho, int(alto * 0.28)))
    pygame.draw.rect(canvas, (70, 62, 52), cuerpo)
    for f in (0.33, 0.66):
        yy = cuerpo.y + int(cuerpo.h * f)
        pygame.draw.line(canvas, (46, 40, 33), (cuerpo.x, yy), (cuerpo.right - 1, yy), 2)
    pygame.draw.ellipse(canvas, (104, 95, 82), (x, y, ancho, int(alto * 0.28)))
    pygame.draw.ellipse(canvas, (40, 34, 28), (x, y, ancho, int(alto * 0.28)), 2)
    pygame.draw.line(canvas, (40, 34, 28), (cuerpo.x, cuerpo.y + 2), (cuerpo.x, cuerpo.bottom), 2)
    pygame.draw.line(canvas, (40, 34, 28), (cuerpo.right - 1, cuerpo.y + 2), (cuerpo.right - 1, cuerpo.bottom), 2)

    # veta de oxido
    pygame.draw.rect(canvas, mezclar(COL_OXIDO, (70, 62, 52), 0.45),
                     (cuerpo.right - max(5, ancho // 6), cuerpo.y + 3, max(3, ancho // 14), int(cuerpo.h * 0.55)))

    # ventanilla con el nivel de agua
    ventana = pygame.Rect(0, 0, int(ancho * 0.4), int(cuerpo.h * 0.78))
    ventana.center = (cx - int(ancho * 0.06), cuerpo.centery)
    pygame.draw.rect(canvas, (12, 18, 20), ventana)
    alto_agua = int((ventana.h - 4) * max(0.0, min(1.0, nivel)))
    if alto_agua > 0:
        agua = pygame.Rect(ventana.x + 2, ventana.bottom - 2 - alto_agua, ventana.w - 4, alto_agua)
        pygame.draw.rect(canvas, COL_AGUA, agua)
        pygame.draw.line(canvas, mezclar(COL_AGUA, (255, 255, 255), 0.5), agua.topleft, (agua.right - 1, agua.y), 2)
    pygame.draw.rect(canvas, COL_ACERO, ventana, 2)

    # grifo
    gw, gh = max(5, ancho // 6), max(3, ancho // 12)
    gx, gy = cuerpo.right, cuerpo.bottom - int(alto * 0.12)
    pygame.draw.rect(canvas, COL_ACERO, (gx, gy, gw, gh))
    return (gx + gw - 2, gy + gh)


# ---------------------------------------------------------------- HUD de arriba a la izquierda

def crear_retrato(i, imagen):
    """Foto instantanea pegada con cinta. Se genera una sola vez al cargar."""
    w, h, pad = 128, 148, 12
    foto = pygame.Surface((w, h + pad), pygame.SRCALPHA)
    pygame.draw.rect(foto, (226, 213, 183), (0, pad, w, h))
    caja = pygame.Rect(9, pad + 9, w - 18, 100)
    pygame.draw.rect(foto, (20, 20, 18), caja)
    if imagen:
        foto.blit(imagen, imagen.get_rect(center=caja.center))
    else:
        for k, (nombre, color, _) in enumerate(PAREJAS[i]):
            img = render_texto(nombre, FUENTES["nota"], color)
            foto.blit(img, img.get_rect(center=(caja.centerx, caja.y + 36 + k * 28)))
    pie = render_texto(f"Pareja {i + 1}", FUENTES["nota"], COL_TINTA)
    foto.blit(pie, pie.get_rect(center=(w // 2, pad + h - 20)))
    pygame.draw.rect(foto, (150, 135, 104), (0, pad, w, h), 1)

    cinta = pygame.Surface((54, 20), pygame.SRCALPHA)
    cinta.fill((205, 184, 112, 175))
    cinta = pygame.transform.rotate(cinta, 6)
    foto.blit(cinta, cinta.get_rect(center=(w // 2, pad)))
    return pygame.transform.rotozoom(foto, 3, 1.0)


def ajustar_en_caja(imagen, ancho_max, alto_max):
    escala = min(ancho_max / imagen.get_width(), alto_max / imagen.get_height())
    return pygame.transform.smoothscale(imagen, (max(1, int(imagen.get_width() * escala)), max(1, int(imagen.get_height() * escala))))


def cargar_duos():
    """Una foto pegada por pareja (con la imagen si existe, y con los nombres si no)."""
    duos = []
    for i in range(len(PAREJAS)):
        imagen = None
        if i < len(IMAGENES_DUO):
            ruta = carpeta_assets("Interfaz", IMAGENES_DUO[i])
            if ruta.exists():
                try:
                    imagen = ajustar_en_caja(pygame.image.load(str(ruta)).convert_alpha(), 106, 92)
                except Exception as e:
                    print(f"[Evento_2] No se pudo cargar {ruta}: {e}")
        duos.append(crear_retrato(i, imagen))
    return duos


def dibujar_hud(canvas, jugadores, retrato, poder_espera, poder_activo, tiempo):
    panel = pygame.Rect(22, 18, 580, 150)
    placa(canvas, panel, corte=24)

    if retrato:
        canvas.blit(retrato, retrato.get_rect(center=(panel.x + 84, panel.centery)))

    # --- jugadores: nombre y gotas de agua (vidas)
    x0 = panel.x + 172
    for i, j in enumerate(jugadores):
        y = panel.y + 26 + i * 52
        fuera = j["eliminado"]
        pygame.draw.rect(canvas, COL_APAGADO if fuera else j["color"], (x0, y + 2, 6, 34))
        r = escribir(canvas, j["nombre"], FUENTES["nombre"], COL_APAGADO if fuera else COL_PAPEL,
                     (x0 + 18, y + 19), "midleft")
        if fuera:
            pygame.draw.line(canvas, COL_OXIDO, (r.left - 4, r.centery), (r.right + 4, r.centery), 3)

        gota_t = j.get("gota_t", 0.0)
        for k in range(VIDAS):
            cx, cy = x0 + 236 + k * 30, y + 25
            if k < j["vidas"]:
                dibujar_gota(canvas, cx, cy, 8, COL_AGUA)
            elif k == j["vidas"] and gota_t > 0:
                f = gota_t / DURACION_GOTA                    # la gota perdida se encoge y se pone roja
                dibujar_gota(canvas, cx, cy, 8 * f, mezclar(COL_OXIDO, COL_AGUA, f))
            else:
                dibujar_gota(canvas, cx, cy, 8, COL_APAGADO, seca=True)

    # --- escaner: radar + anillo de tiempo + tecla
    cx, cy = panel.right - 64, panel.y + 58
    if poder_activo > 0:
        fraccion, color, estado = poder_activo / DURACION_PODER, COL_AMBAR, "Activo"
    elif poder_espera > 0:
        fraccion, color, estado = 1 - poder_espera / ESPERA_PODER, COL_APAGADO, f"{math.ceil(poder_espera)} s"
    else:
        fraccion, color, estado = 1.0, COL_PAPEL, "Listo"

    pygame.draw.circle(canvas, (52, 46, 38), (cx, cy), 34, 4)
    dibujar_arco(canvas, color, cx, cy, 34, fraccion, 4)
    dibujar_radar(canvas, cx, cy, 26, tiempo * (5.0 if poder_activo > 0 else 0.8), color,
                  barrido=(poder_activo > 0 or poder_espera <= 0))

    brillo = 0.5 + 0.5 * math.sin(tiempo * 5) if (poder_espera <= 0 and poder_activo <= 0) else 0.0
    tecla = dibujar_tecla(canvas, "B", cx - 46, panel.y + 108, brillo)
    escribir(canvas, estado, FUENTES["nota"], color, (tecla.right + 8, tecla.centery - 1), "midleft")


# ---------------------------------------------------------------- ruta de progreso (derecha)

def dibujar_ruta(canvas, x, y_tanque, y_base, marcadores, esc=1.0, restante=None, nivel=None):
    """Ruta vertical hacia el deposito. Cada jugador es un marcador que sube; el deposito se llena con el que va primero."""
    if nivel is None:
        nivel = max([m["progreso"] for m in marcadores] or [0.0])
    ancho_t, alto_t = int(54 * esc), int(66 * esc)
    dibujar_tanque(canvas, x, y_tanque, ancho_t, alto_t, nivel)
    if restante is not None:
        escribir(canvas, restante, FUENTES["pequena"], COL_PAPEL, (x, y_tanque + alto_t + int(4 * esc)), "midtop")

    y_top = y_tanque + alto_t + int(28 * esc)
    pygame.draw.line(canvas, COL_POLVO, (x, y_top), (x, y_base), int(8 * esc))
    y = y_base
    while y > y_top:
        pygame.draw.line(canvas, COL_PAPEL, (x, y), (x, max(y_top, y - int(8 * esc))), max(2, int(2 * esc)))
        y -= int(14 * esc)

    # equis de salida
    d = int(7 * esc)
    yx = y_base + int(14 * esc)
    pygame.draw.line(canvas, COL_OXIDO, (x - d, yx - d), (x + d, yx + d), 3)
    pygame.draw.line(canvas, COL_OXIDO, (x - d, yx + d), (x + d, yx - d), 3)

    for k, m in enumerate(marcadores):
        py = int(y_base - m["progreso"] * (y_base - y_top))
        lado = -1 if k % 2 == 0 else 1
        mx = x + lado * int(17 * esc)
        rad = int(10 * esc)
        pygame.draw.line(canvas, COL_PAPEL, (x, py), (mx, py), 2)
        pygame.draw.circle(canvas, COL_POLVO, (mx, py), rad + 2)
        pygame.draw.circle(canvas, m["color"], (mx, py), rad)
        escribir(canvas, "x" if m["eliminado"] else m["inicial"], FUENTES["pequena"], COL_POLVO,
                 (mx, py), "center", sombra=False)


def dibujar_ruta_juego(canvas, jugadores):
    if not ACTIVAR_PROGRESO:
        return
    inicio_y = ALTO_MUNDO - ALTO_INICIO + 20
    total = max(1, inicio_y - LIMITE_ARRIBA)
    marcadores = []
    for j in jugadores:
        p = 1.0 if j["llego"] else max(0.0, min(1.0, (inicio_y - j["y"]) / total))
        marcadores.append({
            "progreso": p,
            "color": COL_APAGADO if j["eliminado"] else j["color"],
            "inicial": j["nombre"][0],
            "eliminado": j["eliminado"],
        })
    vivos = [m for m in marcadores if not m["eliminado"]] or marcadores
    mejor = max(m["progreso"] for m in vivos)
    dibujar_ruta(canvas, ANCHO - 48, 20, ALTO - 60, marcadores, 1.0,
                 f"{int((1 - mejor) * total / 10)} m", nivel=mejor)


# ---------------------------------------------------------------- resultado entre parejas

def dibujar_resultado(canvas, jugadores, siguiente):
    llegaron = [j for j in jugadores if j["llego"]]
    if len(llegaron) == len(jugadores):
        titulo = "Los dos llegaron al depósito"
    elif llegaron:
        titulo = f"{llegaron[0]['nombre']} llegó al depósito"
    else:
        titulo = "Nadie llegó al depósito"

    banda = pygame.Rect(0, ALTO // 2 - 95, ANCHO, 190)
    capa = pygame.Surface(banda.size, pygame.SRCALPHA)
    capa.fill((16, 13, 10, 228))
    canvas.blit(capa, banda.topleft)
    pygame.draw.line(canvas, COL_OXIDO, (0, banda.y), (ANCHO, banda.y), 3)
    pygame.draw.line(canvas, COL_OXIDO, (0, banda.bottom), (ANCHO, banda.bottom), 3)

    x = 160
    escribir(canvas, titulo, FUENTES["titulo"], COL_PAPEL, (x, banda.y + 20), "topleft")
    for i, j in enumerate(jugadores):
        if j["llego"]:
            texto = f"{j['nombre']}: llegó con {j['vidas']} {'gota' if j['vidas'] == 1 else 'gotas'}"
            color = COL_PAPEL
        else:
            texto = f"{j['nombre']}: se quedó sin gotas"
            color = COL_APAGADO
        escribir(canvas, texto, FUENTES["cuerpo"], color, (x, banda.y + 98 + i * 38), "topleft")
    if siguiente is not None:
        escribir(canvas, f"Sigue la pareja {siguiente + 1}", FUENTES["nota"], COL_AMBAR,
                 (ANCHO - 160, banda.bottom - 24), "bottomright")


# ---------------------------------------------------------------- tutorial: una nota recuperada

def crear_fondo_tutorial(fondo):
    base = pygame.Surface((ANCHO, ALTO))
    base.fill(COL_POLVO)
    if fondo is not None:
        zona_y = max(0, min(ALTO_MUNDO - ALTO, ALTO_MUNDO // 2 - ALTO // 2))
        base.blit(fondo, (0, 0), (0, zona_y, ANCHO, ALTO))
    capa = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    capa.fill((10, 8, 6, 190))
    grosor = 140
    for i in range(grosor):
        alfa = int(110 * ((grosor - i) / grosor) ** 2)
        pygame.draw.rect(capa, (6, 5, 4, alfa), (i, i, ANCHO - 2 * i, 2))
        pygame.draw.rect(capa, (6, 5, 4, alfa), (i, ALTO - i - 2, ANCHO - 2 * i, 2))
        pygame.draw.rect(capa, (6, 5, 4, alfa), (i, i, 2, ALTO - 2 * i))
        pygame.draw.rect(capa, (6, 5, 4, alfa), (ANCHO - i - 2, i, 2, ALTO - 2 * i))
    base.blit(capa, (0, 0))
    return base.convert()


def crear_nota(rect):
    """Hoja con el borde de abajo rasgado, sombra, cinta y una mancha de cafe. Se genera una vez."""
    w, h = rect.size
    pad = 18
    surf = pygame.Surface((w + pad * 2, h + pad * 2), pygame.SRCALPHA)
    rng = random.Random(11)

    puntos = [(0, 0), (w, 0), (w, h - 8)]
    x = w
    while x > 0:
        x -= rng.randint(14, 30)
        puntos.append((max(0, x), h - rng.randint(0, 16)))
    puntos.append((0, h - 8))

    sombra = [(px + pad + 10, py + pad + 12) for px, py in puntos]
    capa = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    pygame.draw.polygon(capa, (0, 0, 0, 120), sombra)
    surf.blit(capa, (0, 0))
    pygame.draw.polygon(surf, COL_PAPEL, [(px + pad, py + pad) for px, py in puntos])

    # mancha de cafe
    mancha = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    pygame.draw.circle(mancha, (150, 120, 80, 70), (pad + w - 150, pad + h - 190), 52, 5)
    pygame.draw.circle(mancha, (150, 120, 80, 28), (pad + w - 150, pad + h - 190), 47)
    surf.blit(mancha, (0, 0))

    # dos pedazos de cinta
    for cx, ang in ((pad + 70, 8), (pad + w - 70, -8)):
        cinta = pygame.Surface((96, 28), pygame.SRCALPHA)
        cinta.fill((205, 184, 112, 185))
        cinta = pygame.transform.rotate(cinta, ang)
        surf.blit(cinta, cinta.get_rect(center=(cx, pad + 2)))
    return surf, pad


def crear_visor(tam):
    """Marco con esquinas, como el visor del dispositivo de escaneo, donde se ve la demostracion."""
    s = pygame.Surface(tam, pygame.SRCALPHA)
    s.fill((10, 12, 11, 170))
    w, h = tam
    largo = 34
    for x, y, sx, sy in ((2, 2, 1, 1), (w - 3, 2, -1, 1), (2, h - 3, 1, -1), (w - 3, h - 3, -1, -1)):
        pygame.draw.line(s, COL_PAPEL, (x, y), (x + sx * largo, y), 3)
        pygame.draw.line(s, COL_PAPEL, (x, y), (x, y + sy * largo), 3)
    return s


MINAS_DEMO = [(0.6, 0.55), (1.9, 0.8), (2.8, 0.4), (3.9, 0.7), (4.8, 0.5), (5.6, 0.85), (1.2, 0.3)]


def demo_intro(canvas, r, t):
    cx = r.centerx
    alto, ancho = 330, 190
    y = r.y + 70
    grifo = dibujar_tanque(canvas, cx, y, ancho, alto, 0.10 + 0.02 * math.sin(t * 1.5))
    suelo = y + alto + 6
    pygame.draw.line(canvas, COL_ACERO, (cx - 150, suelo), (cx + 150, suelo), 3)
    f = (t % 1.8) / 1.8
    if f < 0.95:
        gy = grifo[1] + f * f * (suelo - grifo[1] - 12)
        dibujar_gota(canvas, grifo[0], gy, 6 * (1 - 0.2 * f), COL_AGUA)


def demo_vidas(canvas, r, t):
    ciclo = t % 5.0
    cy = r.centery - 30
    sep = 120
    x_ini = r.centerx - (VIDAS - 1) * sep / 2
    for k in range(VIDAS):
        cx = x_ini + k * sep
        if k < VIDAS - 1 or ciclo < 1.5 or ciclo >= 4.4:
            dibujar_gota(canvas, cx, cy, 34, COL_AGUA)
        elif ciclo < 2.2:
            f = 1 - (ciclo - 1.5) / 0.7
            dibujar_gota(canvas, cx, cy, 34 * f, mezclar(COL_OXIDO, COL_AGUA, f))
        else:
            dibujar_gota(canvas, cx, cy, 34, COL_APAGADO, seca=True)
    mina = (r.centerx, r.centery + 150)
    pygame.draw.circle(canvas, COL_MINA, mina, RADIO_MINA)
    if 1.3 <= ciclo < 2.0:
        radio = int(RADIO_MINA + (ciclo - 1.3) / 0.7 * 60)
        pygame.draw.circle(canvas, COL_AMBAR, mina, radio, 3)


def demo_poder(canvas, r, t):
    dibujar_tecla(canvas, "B", r.centerx - 15, r.y + 16, 0.5 + 0.5 * math.sin(t * 5))
    cx, cy = r.centerx, r.centery + 22
    dibujar_radar(canvas, cx, cy, 165, t * 2.2, COL_AMBAR, True, MINAS_DEMO)
    pygame.draw.circle(canvas, PAREJAS[0][0][1], (cx, cy), 7)
    pygame.draw.circle(canvas, (255, 255, 255), (cx, cy), 7, 2)


def demo_progreso(canvas, r, t):
    marcadores = []
    for k, (offset, vel) in enumerate(((0.0, 0.11), (0.25, 0.08))):
        nombre, color, _ = PAREJAS[0][k]
        marcadores.append({"progreso": (t * vel + offset) % 1.0, "color": color,
                           "inicial": nombre[0], "eliminado": False})
    mejor = max(m["progreso"] for m in marcadores)
    dibujar_ruta(canvas, r.centerx, r.y + 20, r.bottom - 40, marcadores, 1.5,
                 f"{int((1 - mejor) * 340)} m", nivel=mejor)


def demo_objetivo(canvas, r, t):
    nivel = min(1.0, (t % 5.0) / 4.0)
    dibujar_tanque(canvas, r.centerx, r.y + 70, 190, 330, nivel)
    pygame.draw.line(canvas, COL_ACERO, (r.centerx - 150, r.y + 406), (r.centerx + 150, r.y + 406), 3)


def mostrar_tutorial(display, canvas, fondo, reloj):
    """Tutorial omisible: una nota recuperada que se escribe sola, con una demostracion de cada mecanica."""
    paginas = [
        {
            "titulo": "El último suministro",
            "texto": "El agua se está acabando. Al otro lado de estas ruinas todavía queda un depósito, "
                     "pero el camino está plagado de explosivos. Hay ciudadanos esperando ese suministro... "
                     "y alguien debe llegar hasta él.",
            "demo": demo_intro,
        },
        {
            "titulo": "Cuida tus vidas",
            "texto": f"Cada explorador comienza con {VIDAS} vidas, una por cada gota de agua que lleva. "
                     "Si pisas una mina, pierdes una. Si te quedas sin gotas, quedas fuera del recorrido. "
                     "Avanza con cuidado.",
            "demo": demo_vidas,
        },
        {
            "titulo": "Escanea el terreno",
            "texto": f"Tu dispositivo puede revelar temporalmente las minas ocultas. Pulsa B para activarlo. "
                     f"El escaneo dura {int(DURACION_PODER)} segundos y luego necesita {int(ESPERA_PODER)} "
                     "segundos para recargarse.",
            "demo": demo_poder,
        },
        {
            "titulo": "Observa tu progreso",
            "texto": "La línea de la derecha muestra cuánto ha avanzado cada integrante de la pareja. "
                     "Arriba está el depósito: se va llenando de agua a medida que alguien se acerca, "
                     "y debajo te dice cuántos metros faltan.",
            "demo": demo_progreso,
        },
        {
            "titulo": "Lleva el agua a Nova",
            "texto": "Cruza el campo minado y alcanza el otro extremo. Tu objetivo es llegar al depósito "
                     "para recuperar el agua que necesitan los ciudadanos. El primer jugador se mueve con "
                     "W, A, S, D; el segundo, con las flechas.",
            "demo": demo_objetivo,
        },
    ]

    fondo_tutorial = crear_fondo_tutorial(fondo)
    nota_rect = pygame.Rect(120, 130, 800, 640)
    nota, pad_nota = crear_nota(nota_rect)
    visor_rect = pygame.Rect(1010, 165, 470, 540)
    visor = crear_visor(visor_rect.size)
    margen = 56
    ancho_texto = nota_rect.width - margen * 2

    def preparar(pagina):
        titulo = dividir_en_lineas(pagina["titulo"], FUENTES["titulo"], ancho_texto)
        cuerpo = dividir_en_lineas(pagina["texto"], FUENTES["cuerpo"], ancho_texto)
        return titulo, cuerpo, sum(len(l) for l in cuerpo)

    indice = 0
    lineas_titulo, lineas_cuerpo, total = preparar(paginas[0])
    t_pagina = 0.0
    t_total = 0.0
    terminado = False

    while not terminado:
        dt = min(reloj.tick(60) / 1000, 0.05)
        t_pagina += dt
        t_total += dt
        revelado = int(t_pagina * VELOCIDAD_TEXTO) >= total

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_RIGHT):
                    if not revelado:
                        t_pagina = 9999.0          # primer toque: termina de escribir la nota
                    else:
                        indice += 1
                        if indice >= len(paginas):
                            terminado = True
                        else:
                            lineas_titulo, lineas_cuerpo, total = preparar(paginas[indice])
                            t_pagina = 0.0
                elif event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
                    terminado = True
                elif event.key == pygame.K_LEFT and indice > 0:
                    indice -= 1
                    lineas_titulo, lineas_cuerpo, total = preparar(paginas[indice])
                    t_pagina = 0.0

        if terminado:
            break

        pagina = paginas[indice]
        canvas.blit(fondo_tutorial, (0, 0))

        # --- nota
        canvas.blit(nota, (nota_rect.x - pad_nota, nota_rect.y - pad_nota))
        x = nota_rect.x + margen
        y = nota_rect.y + 62
        for linea in lineas_titulo:
            escribir(canvas, linea, FUENTES["titulo"], COL_OXIDO, (x, y), "topleft", sombra=False)
            y += FUENTES["titulo"].get_linesize()
        y += 26

        # texto que se escribe solo
        fuente = FUENTES["cuerpo"]
        escribiendo = not revelado
        restantes = int(t_pagina * VELOCIDAD_TEXTO)
        cursor = None
        for linea in lineas_cuerpo:
            if restantes > 0:
                parte = linea[:restantes]
                escribir(canvas, parte, fuente, COL_TINTA, (x, y), "topleft", sombra=False)
                if escribiendo and cursor is None and restantes <= len(linea):
                    cursor = (x + fuente.size(parte)[0] + 2, y)
            restantes -= len(linea)
            y += fuente.get_linesize() + 8
        if cursor and int(t_total * 6) % 2 == 0:
            pygame.draw.rect(canvas, COL_TINTA, (cursor[0], cursor[1] + 4, 12, fuente.get_linesize() - 8))

        # pie de la nota: teclas reales
        y_pie = nota_rect.bottom - 82
        r1 = dibujar_tecla(canvas, "Enter", x, y_pie)
        ultima = indice == len(paginas) - 1
        r1b = escribir(canvas, "empezar" if ultima else "seguir", FUENTES["nota"], COL_TINTA,
                       (r1.right + 10, r1.centery - 1), "midleft", sombra=False)
        r2 = dibujar_tecla(canvas, "Esc", r1b.right + 36, y_pie)
        escribir(canvas, "saltar", FUENTES["nota"], COL_TINTA, (r2.right + 10, r2.centery - 1), "midleft", sombra=False)
        escribir(canvas, f"{indice + 1}/{len(paginas)}", FUENTES["nota"], COL_TINTA,
                 (nota_rect.right - margen, y_pie + 16), "midright", sombra=False)

        # --- visor con la demostracion
        canvas.blit(visor, visor_rect.topleft)
        canvas.set_clip(visor_rect)
        pagina["demo"](canvas, visor_rect, t_pagina)
        canvas.set_clip(None)

        Metodos.mostrar_canvas(display, canvas)
        pygame.display.update()


# ---------------------------------------------------------------- evento

def Evento_2():
    pygame.init()

    pantalla_completa = False
    display = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
    pygame.display.set_caption("The Leader Game - Campo Minado")
    canvas = pygame.Surface((ANCHO, ALTO))

    cargar_fuentes()                # después de pygame.init()
    cargar_animaciones()            # después de crear la ventana: convert_alpha() la necesita

    fondo = None
    if FONDO:
        try:
            fondo = preparar_fondo(pygame.image.load(str(carpeta_assets("Interfaz", FONDO))).convert())
        except Exception as e:
            print(f"[Evento_2] No se pudo cargar el fondo '{FONDO}': {e}")

    duos = cargar_duos()

    reloj = pygame.time.Clock()

    # El tutorial se muestra una sola vez al entrar al minijuego.
    mostrar_tutorial(display, canvas, fondo, reloj)

    # Recursos visuales creados una sola vez para cuidar el rendimiento.
    particulas_polvo = crear_particulas_polvo(CANTIDAD_PARTICULAS) if ACTIVAR_POLVO else []
    particulas_explosion = []
    ondas_explosion = []
    textos_flotantes = []
    sacudida = 0.0
    capa_particulas = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
    canvas_mundo = pygame.Surface((ANCHO, ALTO))
    sombra_personaje = crear_sombra()
    capa_ambiente = crear_capa_ambiente()
    tiempo_mundo = 0.0
    destello_dano = 0.0

    resultados = {}
    indice_pareja = 0
    duo_actual = 0                  # pareja que está jugando ahora (para la imagen de arriba)
    jugadores = crear_jugadores(PAREJAS[0])
    minas = crear_minas()
    poder_activo = 0.0
    poder_espera = 0.0
    camara = ALTO_MUNDO - ALTO
    fase = "jugando"
    pausa = 0

    running = True
    while running:
        dt = min(reloj.tick(60) / 1000, 0.05)
        tiempo_mundo += dt
        poder_activo = max(0.0, poder_activo - dt)
        poder_espera = max(0.0, poder_espera - dt)
        destello_dano = max(0.0, destello_dano - dt)
        sacudida = max(0.0, sacudida - dt)
        for j in jugadores:
            j["gota_t"] = max(0.0, j.get("gota_t", 0.0) - dt)
        if ACTIVAR_POLVO:
            actualizar_particulas_polvo(particulas_polvo, dt, tiempo_mundo)
        actualizar_explosiones(particulas_explosion, ondas_explosion, dt)
        actualizar_textos(textos_flotantes, dt)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.VIDEORESIZE and not pantalla_completa:
                display = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            if event.type == pygame.KEYDOWN:
                if event.key == TECLA_PODER and fase == "jugando" and poder_espera <= 0:
                    poder_activo = DURACION_PODER
                    poder_espera = ESPERA_PODER
                if event.key == pygame.K_F11:
                    pantalla_completa = not pantalla_completa
                    if pantalla_completa:
                        display = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                    else:
                        display = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)

        if fase == "jugando":
            presionadas = pygame.key.get_pressed()
            activos = [j for j in jugadores if not j["llego"] and not j["eliminado"]]

            for j in activos:
                mover(j, presionadas, dt)
                actualizar_animacion(j, dt)

            if activos:
                objetivo = min(j["y"] for j in activos) - ALTO * 0.6
                objetivo = max(0, min(ALTO_MUNDO - ALTO, objetivo))
                camara += (objetivo - camara) * min(1, 8 * dt)

            for j in activos:
                # el que se queda atrás no se sale de la pantalla: el borde de abajo lo va empujando
                j["y"] = max(camara + LIMITE_ARRIBA, min(camara + ALTO - RADIO_HITBOX, j["y"]))
                j["invulnerable"] = max(0, j["invulnerable"] - dt)

                # --- COLISIONES USANDO RADIO_HITBOX (en los pies) ---
                if j["invulnerable"] <= 0:
                    for mx, my in minas:
                        if abs(my - j["y"]) < RADIO_HITBOX + RADIO_MINA and \
                                math.hypot(j["x"] - mx, j["y"] - my) < RADIO_HITBOX + RADIO_MINA:
                            crear_explosion(particulas_explosion, ondas_explosion, mx, my)
                            destello_dano = DURACION_DESTELLO
                            sacudida = DURACION_SACUDIDA
                            j["vidas"] -= 1
                            j["gota_t"] = DURACION_GOTA
                            crear_texto_flotante(textos_flotantes, j["x"], j["y"] - ALTURA_SPRITE,
                                                 "Sin gotas" if j["vidas"] <= 0 else "-1 gota", (235, 120, 86))
                            if j["vidas"] > 0:
                                j["x"] = j["inicio"][0]
                                j["y"] = camara + ALTO - 40
                                j["invulnerable"] = INVULNERABLE
                            else:
                                j["eliminado"] = True
                            break
                # ----------------------------------------------------

                if not j["eliminado"] and j["y"] <= LIMITE_ARRIBA + 4:
                    j["llego"] = True       # llegó con la cabeza al borde superior: el final del recorrido

            if all(j["llego"] or j["eliminado"] for j in jugadores):
                for j in jugadores:
                    resultados[j["nombre"]] = {"llego": j["llego"], "vidas": j["vidas"]}

                indice_pareja += 1
                if indice_pareja < len(PAREJAS):
                    minas = crear_minas()
                fase = "pausa"
                pausa = PAUSA_ENTRE_PAREJAS

        elif fase == "pausa":
            pausa -= dt
            if pausa <= 0:
                if indice_pareja < len(PAREJAS):
                    duo_actual = indice_pareja
                    jugadores = crear_jugadores(PAREJAS[indice_pareja])
                    camara = ALTO_MUNDO - ALTO
                    poder_activo = 0.0
                    poder_espera = 0.0
                    fase = "jugando"
                else:
                    running = False

        cam = int(camara)
        dibujar_fondo(canvas_mundo, fondo, cam)

        if ACTIVAR_POLVO:
            dibujar_particulas_polvo(canvas_mundo, particulas_polvo, cam, capa_particulas)
        dibujar_explosiones(canvas_mundo, particulas_explosion, ondas_explosion, cam)

        if MINAS_VISIBLES or poder_activo > 0:
            for mx, my in minas:
                sy = my - cam
                if -RADIO_MINA <= sy <= ALTO + RADIO_MINA:
                    pygame.draw.circle(canvas_mundo, COL_MINA, (mx, sy), RADIO_MINA)

        for j in jugadores:
            sy = int(j["y"]) - cam
            # el sprite va ANCLADO A LOS PIES: se dibuja hacia arriba desde la hitbox
            if sy + RADIO_HITBOX < 0 or sy + RADIO_HITBOX - ALTURA_SPRITE > ALTO:
                continue

            if ACTIVAR_SOMBRAS:
                dibujar_sombra_personaje(canvas_mundo, sombra_personaje, j, sy)

            frame_a_dibujar = j.get("frame_activo")

            if frame_a_dibujar:
                superficie_a_blit = frame_a_dibujar
                # Micro movimiento corporal: pasos mas vivos al caminar y respiracion al estar quieto.
                if j["estado"] == "quieto":
                    balanceo = math.sin(tiempo_mundo * 2.8 + j["x"] * 0.01) * 1.1
                else:
                    balanceo = abs(math.sin(j["animacion_tiempo"] * math.tau * 0.85)) * -2.2
                sprite_rect = superficie_a_blit.get_rect(midbottom=(int(j["x"]), int(sy + RADIO_HITBOX + balanceo)))

                if j["eliminado"]:
                    superficie_a_blit = frame_a_dibujar.copy()
                    superficie_a_blit.fill((255, 255, 255, 128), special_flags=pygame.BLEND_RGBA_MULT)
                elif j["invulnerable"] > 0 and int(j["invulnerable"] * 10) % 2 == 0:
                    superficie_a_blit = frame_a_dibujar.copy()
                    superficie_a_blit.set_alpha(100)

                canvas_mundo.blit(superficie_a_blit, sprite_rect)
            else:
                # Fallback de bolita: es justo la hitbox
                color = (110, 110, 110) if j["eliminado"] else j["color"]
                pygame.draw.circle(canvas_mundo, color, (int(j["x"]), sy), RADIO_HITBOX)
                pygame.draw.circle(canvas_mundo, (255, 255, 255), (int(j["x"]), sy), RADIO_HITBOX, 2)
                if j["eliminado"]:
                    pygame.draw.line(canvas_mundo, (255, 255, 255), (int(j["x"]) - 7, sy - 7), (int(j["x"]) + 7, sy + 7), 3)
                    pygame.draw.line(canvas_mundo, (255, 255, 255), (int(j["x"]) - 7, sy + 7), (int(j["x"]) + 7, sy - 7), 3)

        dibujar_textos(canvas_mundo, textos_flotantes, cam)

        # El ambiente se aplica encima del mundo, pero debajo de la interfaz.
        if ACTIVAR_ILUMINACION:
            canvas_mundo.blit(capa_ambiente, (0, 0))
        dibujar_destello_dano(canvas_mundo, destello_dano)

        # Sacudida breve de camara al pisar una mina; el HUD permanece estable.
        canvas.fill((15, 13, 11))
        if sacudida > 0:
            intensidad = sacudida / DURACION_SACUDIDA
            desplazamiento_x = random.randint(-7, 7) * intensidad
            desplazamiento_y = random.randint(-5, 5) * intensidad
        else:
            desplazamiento_x = desplazamiento_y = 0
        canvas.blit(canvas_mundo, (int(desplazamiento_x), int(desplazamiento_y)))

        retrato = duos[duo_actual] if duo_actual < len(duos) else None
        dibujar_hud(canvas, jugadores, retrato, poder_espera, poder_activo, tiempo_mundo)
        dibujar_ruta_juego(canvas, jugadores)
        if fase == "pausa":
            dibujar_resultado(canvas, jugadores, indice_pareja if indice_pareja < len(PAREJAS) else None)

        Metodos.mostrar_canvas(display, canvas)
        pygame.display.update()

    return resultados


if __name__ == "__main__":
    Evento_2()