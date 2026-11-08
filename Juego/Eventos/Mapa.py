import math
import sys
from pathlib import Path

import pygame

ANCHO, ALTO = 1280, 720
CARPETA = Path(__file__).resolve().parent.parent / "Assets" / "Interfaz"   # aquí está mapa.png

ROJO = (200, 30, 25)
TINTA = (48, 30, 18)


# GRAFO DE LA CIUDAD
class Grafo:
    def __init__(self):
        self.adyacencia = {}          # cada lugar guarda sus vecinos: {lugar: {vecino: peso}}

    def agregar_nodo(self, nodo):
        if nodo not in self.adyacencia:
            self.adyacencia[nodo] = {}          # el lugar nuevo empieza sin caminos

    def eliminar_nodo(self, nodo):
        if nodo not in self.adyacencia:
            return                               # si no existe, no hay nada que borrar
        # primero se borran los caminos que llegan a este lugar
        for vecino in list(self.adyacencia[nodo]):
            del self.adyacencia[vecino][nodo]
        # después se borra el lugar
        del self.adyacencia[nodo]

    def agregar_arista(self, a, b, peso=1):
        self.agregar_nodo(a)
        self.agregar_nodo(b)
        self.adyacencia[a][b] = peso             # camino de a hacia b
        self.adyacencia[b][a] = peso             # y de b hacia a (no dirigido)

    def eliminar_arista(self, a, b):
        if a in self.adyacencia and b in self.adyacencia[a]:
            del self.adyacencia[a][b]
        if b in self.adyacencia and a in self.adyacencia[b]:
            del self.adyacencia[b][a]

    def vecinos(self, nodo):
        if nodo not in self.adyacencia:
            return []
        return list(self.adyacencia[nodo])

    def aristas(self):
        lista = []
        for a in self.adyacencia:
            for b in self.adyacencia[a]:
                peso = self.adyacencia[a][b]
                if (b, a, peso) not in lista:      # cada camino está guardado dos veces: se cuenta una
                    lista.append((a, b, peso))
        return lista


LUGARES = {
    "El Cruce del Pozo":     {"punto": (0.280, 0.731), "zona": (0.285, 0.760, 0.135, 0.170)},
    "Barrio Las Acacias":    {"punto": (0.128, 0.498), "zona": (0.128, 0.551, 0.116, 0.148)},
    "El Mercado Cubierto":   {"punto": (0.268, 0.233), "zona": (0.214, 0.280, 0.170, 0.130)},
    "La Torre de la Antena": {"punto": (0.512, 0.244), "zona": (0.512, 0.307, 0.137, 0.159)},
    "El Campo Sembrado":     {"punto": (0.458, 0.551), "zona": (0.500, 0.580, 0.200, 0.190)},
    "El Almacén del Este":   {"punto": (0.798, 0.244), "zona": (0.800, 0.310, 0.185, 0.215)},
    "Central de Datos":      {"punto": (0.780, 0.646), "zona": (0.780, 0.700, 0.150, 0.200)},    }

# Camino de cada personaje: lugar del Evento 1, Evento 2, Evento 3...
RUTAS = {
        "LÍDER":         ["El Cruce del Pozo", "El Campo Sembrado", "El Almacén del Este", "Central de Datos"],
    "SOBREVIVIENTE": ["Barrio Las Acacias", "El Campo Sembrado", "El Almacén del Este", "Central de Datos"],
    "CRONISTA":      ["El Mercado Cubierto", "El Campo Sembrado", "El Almacén del Este", "Central de Datos"],
    "VOZ":           ["La Torre de la Antena", "El Campo Sembrado", "El Almacén del Este", "Central de Datos"],
}


PESOS = {("El Campo Sembrado", "El Almacén del Este"): 6, ("El Almacén del Este", "Central de Datos"): 4}

# NIEBLA (nubes que se mueven)
import numpy as np

REDUCCION = 4          # la niebla se calcula 4 veces más pequeña y se agranda: más rápida y más suave


def ruido_nubes(alto, ancho, detalle, semilla):
    """Ruido tipo nube que se repite sin cortes (para poder moverlo en bucle)."""
    rng = np.random.default_rng(semilla)
    blanco = rng.standard_normal((alto, ancho))
    fy = np.fft.fftfreq(alto)[:, None]
    fx = np.fft.fftfreq(ancho)[None, :]
    f = np.sqrt(fx ** 2 + fy ** 2)
    f[0, 0] = 1
    filtro = 1 / f ** detalle                   # más detalle = nubes más grandes y suaves
    filtro[0, 0] = 0
    n = np.real(np.fft.ifft2(np.fft.fft2(blanco) * filtro))
    n = (n - n.min()) / (n.max() - n.min())
    return n.astype(np.float32)


def desplazar(capa, dy, dx):
    """Mueve la capa una cantidad con decimales (movimiento suave, sin saltos)."""
    iy, ix = int(np.floor(dy)), int(np.floor(dx))
    fy, fx = dy - iy, dx - ix
    a = np.roll(capa, (iy, ix), axis=(0, 1))
    b = np.roll(a, 1, axis=1)
    c = np.roll(a, 1, axis=0)
    d = np.roll(b, 1, axis=0)
    return a * (1 - fx) * (1 - fy) + b * fx * (1 - fy) + c * (1 - fx) * fy + d * fx * fy


class Niebla:
    def __init__(self, tam_mapa, mascara_papel):
        self.w, self.h = tam_mapa[0] // REDUCCION, tam_mapa[1] // REDUCCION
        self.tam_mapa = tam_mapa
        # tres capas de nubes que se mueven a distinta velocidad
        self.capa1 = ruido_nubes(self.h, self.w, 2.4, 1)     # nubes grandes
        self.capa2 = ruido_nubes(self.h, self.w, 2.1, 2)     # nubes medianas
        self.capa3 = ruido_nubes(self.h, self.w, 1.6, 3)     # detalle fino
        self.borde = ruido_nubes(self.h, self.w, 1.4, 4)          # para que los bordes del hueco sean irregulares
        self.papel = mascara_papel                                # 1 donde hay papel, 0 afuera
        yy, xx = np.mgrid[0:self.h, 0:self.w]
        self.xx, self.yy = xx.astype(np.float32), yy.astype(np.float32)
        self.t = 0.0

    def mover(self, dt):
        self.t += dt

    def dibujar(self, zonas, caminos=(), ancho_camino=40):
        """zonas: lista de ((cx, cy, rx, ry), progreso) · caminos: lista de ((a, b), progreso). En píxeles del mapa."""
        t = self.t
        # 1. las capas se desplazan en direcciones distintas (efecto de niebla que se mueve)
        c1 = desplazar(self.capa1, t * 0.8, t * 2.4)
        c2 = desplazar(self.capa2, -t * 0.5, t * 1.5)
        c3 = desplazar(self.capa3, t * 0.3, -t * 1.1)
        densidad = 0.50 * c1 + 0.35 * c2 + 0.15 * c3

        # 2. casi opaca: no se ve lo que sigue
        contraste = np.clip((densidad - 0.30) / 0.45, 0, 1)
        contraste = contraste * contraste * (3 - 2 * contraste)
        alfa = np.clip(0.97 + contraste * 0.03, 0, 1)

        # 3. la niebla se deshace en jirones desde el centro de cada zona hacia afuera
        quitar = np.ones_like(alfa)
        jirones = (0.6 * self.borde + 0.4 * c3) - 0.5          # ruido que se mueve: bordes vivos
        for (cx, cy, rx, ry), p in zonas:
            if p <= 0:
                continue
            d = np.sqrt(((self.xx - cx / REDUCCION) / (rx / REDUCCION)) ** 2 +
                        ((self.yy - cy / REDUCCION) / (ry / REDUCCION)) ** 2)
            puntaje = (1 - d) + jirones * 0.7                   # alto en el centro, irregular en el borde
            limite = 1.45 - suavizar(p) * 1.45                  # baja con el tiempo: se va abriendo
            quitar *= np.clip((limite - puntaje) / 0.22, 0, 1)
        # el camino también se despeja, avanzando de un lugar al otro, con bordes de niebla irregulares
        for (a, b), p in caminos:
            if p <= 0:
                continue
            ax, ay, bx, by = a[0] / REDUCCION, a[1] / REDUCCION, b[0] / REDUCCION, b[1] / REDUCCION
            vx, vy = bx - ax, by - ay
            largo2 = vx * vx + vy * vy
            u = ((self.xx - ax) * vx + (self.yy - ay) * vy) / largo2           # 0 en el inicio, 1 en el final
            uc = np.clip(u, 0, 1)
            d = np.sqrt((self.xx - (ax + uc * vx)) ** 2 + (self.yy - (ay + uc * vy)) ** 2) / (ancho_camino / REDUCCION)
            dentro = np.clip((1 - d + jirones * 0.9) / 0.35, 0, 1)              # franja con bordes de jirones
            frente = np.clip((p * 1.08 - u + jirones * 0.06) / 0.08, 0, 1)      # avanza con el progreso
            quitar *= 1 - dentro * frente
        alfa = alfa * quitar * self.papel
        orilla = np.clip((1 - quitar) * quitar * 4, 0, 1)      # borde de la nube: más espeso y gris

        # 4. color: blanco cálido con sombras suaves
        sombra = np.roll(contraste, (3, 3), axis=(0, 1))
        luz = 205 + contraste * 50 - np.clip(sombra - contraste, 0, 1) * 25 - orilla * 40
        luz = luz[..., None]
        color = np.concatenate([luz, luz - 3, luz - 8], axis=2)
        rgba = np.dstack([color, alfa[..., None] * 255]).clip(0, 255).astype(np.uint8)
        sup = pygame.image.frombuffer(rgba.tobytes(), (self.w, self.h), "RGBA")
        return pygame.transform.smoothscale(sup, self.tam_mapa)


# SONIDOS (se generan con código, no necesitan archivos)
def crear_sonido(duracion, tipo):
    try:
        if not pygame.mixer.get_init():
            return None
        frec = pygame.mixer.get_init()[0]
        n = int(frec * duracion)
        t = np.linspace(0, 1, n, dtype=np.float32)
        ruido = np.random.default_rng(5 if tipo == "whoosh" else 9).standard_normal(n).astype(np.float32)
        if tipo == "whoosh":                                  # trazo rápido: sube y cae
            envolvente = np.clip(np.sin(np.pi * t ** 0.6), 0, 1) ** 2
            corte = 0.04 + 0.30 * np.sin(np.pi * t)           # el "filtro" se abre en el medio
            volumen = 0.28
        else:                                                 # viento suave al abrirse la niebla
            envolvente = np.clip(np.sin(np.pi * t), 0, 1) ** 1.5
            corte = 0.015 + 0.03 * np.sin(np.pi * t * 2) ** 2
            volumen = 0.35
        salida = np.zeros(n, dtype=np.float32)
        y = 0.0
        for i in range(n):                                    # filtro pasa-bajos simple
            y += corte[i] * (ruido[i] - y)
            salida[i] = y
        salida = salida / (np.abs(salida).max() + 1e-6) * envolvente * volumen
        datos = (salida * 32767).astype(np.int16)
        canales = pygame.mixer.get_init()[2]
        if canales == 2:
            datos = np.ascontiguousarray(np.column_stack([datos, datos]))
        return pygame.sndarray.make_sound(datos)
    except Exception:
        return None


def sonar(sonido):
    if sonido is not None:
        sonido.play()


# MAPA
class Mapa:
    def __init__(self, personaje):
        img = pygame.image.load(str(CARPETA / "mapa.png")).convert_alpha()
        escala = min((ANCHO - 80) / img.get_width(), (ALTO - 80) / img.get_height())
        self.img = pygame.transform.smoothscale(img, (int(img.get_width() * escala), int(img.get_height() * escala)))
        self.pos = ((ANCHO - self.img.get_width()) // 2, (ALTO - self.img.get_height()) // 2)
        # máscara del papel (para que la niebla no salga por fuera del borde roto)
        pequeña = pygame.transform.smoothscale(self.img, (self.img.get_width() // REDUCCION, self.img.get_height() // REDUCCION))
        papel = pygame.surfarray.array_alpha(pequeña).T.astype(np.float32) / 255
        self.niebla = Niebla(self.img.get_size(), papel)
        self.radio = int(self.img.get_width() * 0.105)
        self.sonido_trazo = crear_sonido(0.32, "whoosh")
        self.sonido_niebla = crear_sonido(1.8, "viento")
        self.reiniciar(personaje)

    def reiniciar(self, personaje):
        self.personaje = personaje
        self.ruta = RUTAS[personaje]
        self.grafo = Grafo()
        self.grafo.agregar_nodo(self.ruta[0])        # solo se ve el lugar del Evento 1
        self.paso = 0                                  # en qué evento va
        self.visitados = set()
        self.revelado = {self.ruta[0]: 1.0}            # cuánto se quitó la niebla (0 a 1)
        self.x_progreso = {}                           # cuánto se dibujó cada X (0 a 1)
        self.camino_progreso = {}                      # cuánto se dibujó cada camino (0 a 1)
        self.animacion = []                            # cola de animaciones pendientes
        self.trazos_x = {}                             # forma de cada X (hecha a mano)
        self.x_listas = {}                             # X ya terminadas (se guardan dibujadas)
        self.tiempo_paso = 0.0
        self.avance_niebla = 0.0

    def xy(self, lugar):
        fx, fy = LUGARES[lugar]["punto"]
        return int(fx * self.img.get_width()), int(fy * self.img.get_height())

    def zona(self, lugar):
        cx, cy, rx, ry = LUGARES[lugar]["zona"]
        w, h = self.img.get_size()
        return cx * w, cy * h, rx * w, ry * h

    # ---------- Al terminar un evento ----------
    def terminar_evento(self):
        if self.paso >= len(self.ruta) - 1 or self.animacion:
            return
        actual, siguiente = self.ruta[self.paso], self.ruta[self.paso + 1]
        self.visitados.add(actual)
        self.grafo.agregar_nodo(siguiente)                                  # AGREGAR NODO
        peso = PESOS.get((actual, siguiente), 8)
        self.grafo.agregar_arista(actual, siguiente, peso)                  # AGREGAR ARISTA
        self.paso += 1
        self.x_listas.pop(actual, None)
        # orden de la animación: pausa -> X roja -> pausa -> se abre la niebla (y aparece el camino)
        self.trazos_x[actual] = crear_trazos_x(self.xy(actual), int(self.radio * 0.48), semilla=len(self.trazos_x) + 3)
        self.animacion = [("pausa", 0.35), ("x", actual), ("pausa", 0.4), ("niebla", (actual, siguiente))]
        self.tiempo_paso = 0.0

    def actualizar(self, dt):
        self.niebla.mover(dt)
        if not self.animacion:
            return
        tipo, que = self.animacion[0]
        if tipo == "pausa":
            self.tiempo_paso += dt
            if self.tiempo_paso >= que:
                self.tiempo_paso = 0.0
                self.animacion.pop(0)
            return
        if tipo == "x":
            antes = self.x_progreso.get(que, 0)
            ahora = min(1.0, antes + dt * 1.6)
            if antes == 0 or (antes < 0.55 <= ahora):         # suena al empezar cada trazo
                sonar(self.sonido_trazo)
            self.x_progreso[que] = ahora
            if ahora >= 1.0:
                self.animacion.pop(0)
            return
        if tipo == "niebla":
            actual, siguiente = que
            antes = self.avance_niebla
            if antes == 0:
                sonar(self.sonido_niebla)
            ahora = min(1.0, antes + dt * 0.4)
            self.avance_niebla = ahora
            # primero se despeja el camino (0 a 0.55) y luego el lugar nuevo (0.4 a 1)
            self.camino_progreso[(actual, siguiente)] = min(1.0, ahora / 0.55)
            self.revelado[siguiente] = max(0.0, (ahora - 0.4) / 0.6)
            if ahora >= 1.0:
                self.avance_niebla = 0.0
                self.animacion.pop(0)
                self.grafo.eliminar_nodo(actual)                            # ELIMINAR NODO (ya no se vuelve ahí)

    # ---------- Dibujar ----------
    def dibujar(self, pantalla):
        pantalla.fill((17, 20, 24))
        lienzo = self.img.copy()

        # caminos recorridos, dibujados poco a poco con línea punteada
        # (se dibujan aunque el lugar anterior ya no esté en el grafo)
        for (a, b), p in self.camino_progreso.items():
            linea_punteada(lienzo, self.xy(a), self.xy(b), p, TINTA)

        # niebla que se mueve y se abre en las zonas descubiertas
        zonas = [(self.zona(lugar), p) for lugar, p in self.revelado.items()]
        caminos = [((self.xy(a), self.xy(b)), p) for (a, b), p in self.camino_progreso.items()]
        lienzo.blit(self.niebla.dibujar(zonas, caminos, self.img.get_width() * 0.035), (0, 0))

        # X roja hecha a mano en los lugares ya visitados
        for lugar, p in self.x_progreso.items():
            dibujar_x(lienzo, self.trazos_x[lugar], p, self.x_listas, lugar)

        # lugar actual: círculo de tinta que late
        if not self.animacion:
            x, y = self.xy(self.ruta[self.paso])
            pulso = 4 * math.sin(pygame.time.get_ticks() / 250)
            pygame.draw.circle(lienzo, TINTA, (x, y), int(self.radio * 0.6 + pulso), 4)

        pantalla.blit(lienzo, self.pos)


def suavizar(t):
    return 1 - (1 - t) ** 3


def linea_punteada(superficie, a, b, progreso, color):
    largo = math.dist(a, b)
    total = int(largo * progreso)
    for d in range(0, total, 18):
        t1, t2 = d / largo, min(d + 10, total) / largo
        p1 = (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)
        p2 = (a[0] + (b[0] - a[0]) * t2, a[1] + (b[1] - a[1]) * t2)
        pygame.draw.line(superficie, color, p1, p2, 4)


ROJO_PINTURA = (222, 12, 10)


def crear_trazos_x(centro, tam, semilla):
    """Dos brochazos de pintura roja: borde irregular, cerdas secas y gotas salpicadas."""
    rng = np.random.default_rng(semilla)
    x, y = centro
    trazos = []
    for (sx, sy), (ex, ey) in [((-1, -1.05), (1.05, 1.1)), ((1.05, -1.0), (-1.1, 1.15))]:
        a = np.array([x + sx * tam + rng.uniform(-5, 5), y + sy * tam + rng.uniform(-5, 5)])
        b = np.array([x + ex * tam + rng.uniform(-5, 5), y + ey * tam + rng.uniform(-5, 5)])
        dirr = (b - a) / np.linalg.norm(b - a)
        normal = np.array([-dirr[1], dirr[0]])
        control = (a + b) / 2 + normal * rng.uniform(-0.08, 0.08) * tam * 2
        ancho = tam * 0.15
        n = 90
        # cada "cerda" de la brocha es una línea paralela que se seca en un punto distinto
        cerdas = []
        for k in range(12):
            o = rng.uniform(-1, 1)
            fin = 1.0 if abs(o) < 0.35 else rng.uniform(0.45, 0.95)      # las de los lados se secan antes
            huecos = [(h, h + rng.uniform(0.03, 0.09)) for h in rng.uniform(0.1, 0.95, rng.integers(0, 3))]
            cerdas.append((o, fin, huecos, rng.uniform(0.6, 1.2)))
        puntos = []
        for i in range(n):
            t = i / (n - 1)
            centro_t = (1 - t) ** 2 * a + 2 * (1 - t) * t * control + t ** 2 * b
            # forma del brochazo: mancha gruesa al inicio, cuerpo y punta afilada al final
            perfil = 1.15 if t < 0.05 else (1.0 if t < 0.7 else max(0.12, 1 - (t - 0.7) / 0.3))
            perfil *= 1 + 0.12 * np.sin(t * 23 + semilla)                   # pequeñas ondulaciones
            puntos.append((centro_t, perfil))
        gotas = []
        for _ in range(rng.integers(4, 9)):                                  # salpicaduras
            t = rng.choice([rng.uniform(0, 0.12), rng.uniform(0.85, 1.0), rng.uniform(0.3, 0.7)])
            c = (1 - t) ** 2 * a + 2 * (1 - t) * t * control + t ** 2 * b
            lado = rng.choice([-1, 1]) * rng.uniform(1.1, 2.2) * ancho
            gotas.append((t, c + normal * lado + dirr * rng.uniform(-6, 6), rng.uniform(1.0, 2.6)))
        trazos.append({"puntos": puntos, "cerdas": cerdas, "gotas": gotas, "ancho": ancho, "normal": normal})
    return trazos


def pintar_x(tam_superficie, trazos, progreso):
    capa = pygame.Surface(tam_superficie, pygame.SRCALPHA)
    for i, tr in enumerate(trazos):
        p = max(0.0, min(1.0, (progreso - i * 0.55) / 0.45))
        if p <= 0:
            continue
        puntos, normal, ancho = tr["puntos"], tr["normal"], tr["ancho"]
        hasta = int(len(puntos) * p)
        for j in range(hasta):
            t = j / (len(puntos) - 1)
            c, perfil = puntos[j]
            w = ancho * perfil
            # cuerpo sólido del brochazo
            pygame.draw.circle(capa, ROJO_PINTURA, (int(c[0]), int(c[1])), max(2, int(w * 0.42)))
            # cerdas: dan el borde rasgado y las vetas secas
            for o, fin, huecos, g in tr["cerdas"]:
                if t > fin or any(h0 <= t <= h1 for h0, h1 in huecos):
                    continue
                q = c + normal * o * w
                pygame.draw.circle(capa, ROJO_PINTURA, (int(q[0]), int(q[1])), max(1, int(w * 0.22 * g)))
        for t, pos, r in tr["gotas"]:
            if t <= p:
                pygame.draw.circle(capa, ROJO_PINTURA, (int(pos[0]), int(pos[1])), int(r))
    return capa


def dibujar_x(superficie, trazos, progreso, cache, clave):
    """Dibuja la X avanzando. Cuando termina, se guarda ya pintada para no recalcularla."""
    if clave in cache:
        superficie.blit(cache[clave], (0, 0))
        return
    capa = pintar_x(superficie.get_size(), trazos, progreso)
    if progreso >= 1.0:
        cache[clave] = capa
    superficie.blit(capa, (0, 0))


# ICONO DEL MAPA (arriba a la derecha)
def dibujar_icono(pantalla, rect, encima):
    color = (235, 215, 175) if encima else (210, 190, 150)
    pygame.draw.rect(pantalla, (17, 20, 24), rect.inflate(10, 10), border_radius=10)
    x, y, w, h = rect
    puntos = [(x, y + 6), (x + w // 3, y), (x + 2 * w // 3, y + 6), (x + w, y),
              (x + w, y + h - 6), (x + 2 * w // 3, y + h), (x + w // 3, y + h - 6), (x, y + h)]
    pygame.draw.polygon(pantalla, color, puntos)
    pygame.draw.line(pantalla, TINTA, (x + w // 3, y), (x + w // 3, y + h - 6), 2)
    pygame.draw.line(pantalla, TINTA, (x + 2 * w // 3, y + 6), (x + 2 * w // 3, y + h), 2)
    pygame.draw.line(pantalla, ROJO, (x + 8, y + 14), (x + 18, y + 24), 3)
    pygame.draw.line(pantalla, ROJO, (x + 18, y + 14), (x + 8, y + 24), 3)


# PARA USAR DENTRO DEL JUEGO
def animacion_terminada(mapa):
    return not mapa.animacion


def mostrar_mapa(display, mapa, terminar=True):
    """Abre el mapa en pantalla.
    terminar=True: marca el evento actual como terminado (X roja) y se abre el camino al siguiente.
    terminar=False: solo muestra dónde está el jugador ahora.
    Cuando termina la animación, espera un clic (o ENTER / ESPACIO / ESC) para seguir."""
    import Metodos
    bloqueado_antes = Metodos.MAPA_BLOQUEADO
    Metodos.MAPA_BLOQUEADO = True          # mientras el mapa está abierto no se dibuja el icono
    canvas = pygame.Surface((ANCHO, ALTO))
    reloj = pygame.time.Clock()
    fuente = pygame.font.SysFont("consolas", 22, bold=True)
    if terminar:
        mapa.terminar_evento()

    while True:
        dt = min(reloj.tick(60) / 1000, 0.05)
        listo = animacion_terminada(mapa)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type == pygame.VIDEORESIZE:
                display = pygame.display.set_mode((e.w, e.h), pygame.RESIZABLE)
            if listo and ((e.type == pygame.MOUSEBUTTONDOWN and e.button == 1) or
                          (e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE, pygame.K_m))):
                Metodos.MAPA_BLOQUEADO = bloqueado_antes
                return

        mapa.actualizar(dt)
        mapa.dibujar(canvas)

        if listo:
            lugar = mapa.ruta[mapa.paso]
            alfa = int(170 + 85 * math.sin(pygame.time.get_ticks() / 300))
            if terminar:
                mensaje = f"Siguiente destino: {lugar}   ·   clic para continuar"
            else:
                mensaje = f"Estás aquí: {lugar}   ·   clic para cerrar"
            texto = fuente.render(mensaje, True, (235, 215, 175))
            texto.set_alpha(alfa)
            caja = texto.get_rect(center=(ANCHO // 2, ALTO - 26))
            pygame.draw.rect(canvas, (17, 20, 24), caja.inflate(24, 12), border_radius=8)
            canvas.blit(texto, caja)

        Metodos.mostrar_canvas(display, canvas)
        pygame.display.update()


# PRUEBA (solo si corres este archivo directamente)
def main():
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.init()
    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption("The Leader - Mapa")
    reloj = pygame.time.Clock()
    fuente = pygame.font.SysFont("consolas", 20, bold=True)

    personajes = list(RUTAS)
    mapa = Mapa(personajes[0])
    mapa_abierto = False
    icono = pygame.Rect(ANCHO - 70, 20, 50, 40)

    while True:
        dt = reloj.tick(60) / 1000
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and icono.collidepoint(e.pos):
                mapa_abierto = not mapa_abierto
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    mapa_abierto = False
                if e.key == pygame.K_SPACE:
                    mapa_abierto = True            # al terminar un evento, el mapa se abre solo
                    mapa.terminar_evento()
                if e.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                    mapa.reiniciar(personajes[e.key - pygame.K_1])

        mapa.actualizar(dt)

        if mapa_abierto:
            mapa.dibujar(pantalla)
        else:
            pantalla.fill((40, 44, 50))
            t = fuente.render(f"(aquí va el evento)  Personaje: {mapa.personaje}  ·  Lugar: {mapa.ruta[mapa.paso]}",
                              True, (230, 230, 230))
            pantalla.blit(t, t.get_rect(center=(ANCHO // 2, ALTO // 2)))

        ayuda = fuente.render("ESPACIO: terminar evento   ·   1-4: cambiar personaje   ·   clic en el icono: mapa",
                              True, (255, 225, 220))
        pantalla.blit(ayuda, (20, ALTO - 34))
        dibujar_icono(pantalla, icono, icono.collidepoint(pygame.mouse.get_pos()))
        pygame.display.flip()


if __name__ == "__main__":
    main()
