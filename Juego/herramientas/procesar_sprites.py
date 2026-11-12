"""
procesar_sprites.py  -  Python 3.12
Convierte las 4 hojas generadas (fondo verde, cuadricula 8x2) en sprites
listos para el juego.

Pasos: quitar verde + halo -> cortar 16 frames -> recortar al contenido
-> igualar escala -> (opcional) pixelar -> pegar con los pies en la misma
linea base -> exportar hojas finales + frames sueltos + JSON.

Instalar:   pip install pillow numpy
Usar:       python procesar_sprites.py
            (pon las 4 hojas en herramientas/originales/ con los nombres de ENTRADAS)
"""
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image

# ------------------------- CONFIGURACION -------------------------
BASE = Path(__file__).resolve().parent
ENTRADAS = {            # direccion -> hoja generada (en herramientas/originales/)
    "down":  BASE / "originales" / "abajo.jpg",
    "up":    BASE / "originales" / "arriba.jpg",
    "left":  BASE / "originales" / "izquierda.jpg",
    "right": BASE / "originales" / "derecha.jpg",
}
COLUMNAS, FILAS = 8, 2
FILA_ANIM = {0: "walk", 1: "idle"}   # fila 1 = caminar, fila 2 = quieto
# nombres de carpeta que usan los eventos del juego (Evento_2, etc.)
CARPETA_JUEGO = {"down": "abajo", "up": "arriba", "left": "izquierda", "right": "derecha"}

ALTO_PERSONAJE = 240   # alto final del personaje en px (pixel art real)
PIXELAR = True          # True = reduce con NEAREST (pixel art limpio)
                        # False = reduce suave (LANCZOS)
MARGEN = 4              # px libres alrededor del personaje en cada celda
QUITAR_SOMBRAS = True   # borra manchas oscuras verdosas (sombras en el suelo)
SALIDA = BASE.parent / "Assets" / "Personajes" / "Sobreviviente"
# -----------------------------------------------------------------


def quitar_verde(img: Image.Image) -> Image.Image:
    """Chroma key al verde + despill del halo verde en los bordes."""
    a = np.asarray(img.convert("RGBA")).astype(np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]

    # "cuanto mas verde que el resto" es cada pixel
    exceso = g - np.maximum(r, b)

    # fondo: verde dominante y brillante
    fondo = (exceso > 60) & (g > 120)
    # sombras del suelo: verde dominante pero oscuro
    if QUITAR_SOMBRAS:
        fondo |= (exceso > 25) & (g > 40) & (g < 140) & (r < 90) & (b < 90)

    alpha = np.where(fondo, 0, 255).astype(np.float32)

    # despill: a los pixeles que quedan, no dejar que G supere a max(R,B)
    limite = np.maximum(r, b)
    g = np.where(g > limite, limite, g)

    out = np.stack([r, g, b, alpha], axis=-1).clip(0, 255).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


def limpiar_ruido(frame: Image.Image, minimo: int = 30) -> Image.Image:
    """Elimina islas sueltas de pocos pixeles que deja el chroma key."""
    a = np.asarray(frame).copy()
    opaco = a[..., 3] > 0
    h, w = opaco.shape
    visto = np.zeros_like(opaco)
    for y0 in range(h):
        for x0 in range(w):
            if opaco[y0, x0] and not visto[y0, x0]:
                pila, region = [(y0, x0)], []
                visto[y0, x0] = True
                while pila:
                    y, x = pila.pop()
                    region.append((y, x))
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = y + dy, x + dx
                        if 0 <= ny < h and 0 <= nx < w and opaco[ny, nx] and not visto[ny, nx]:
                            visto[ny, nx] = True
                            pila.append((ny, nx))
                if len(region) < minimo:
                    for y, x in region:
                        a[y, x, 3] = 0
    return Image.fromarray(a, "RGBA")


def cortar(hoja: Image.Image) -> list[list[Image.Image]]:
    """Devuelve frames[fila][i] recortados a su contenido.

    No usa una cuadricula fija: dentro de cada fila busca las columnas
    vacias (sin pixeles opacos) y separa cada figura por su silueta.
    Asi funciona aunque el generador haya puesto 7, 8 o 10 figuras."""
    W, H = hoja.size
    ch = H / FILAS
    frames = []
    for f in range(FILAS):
        franja = hoja.crop((0, round(f * ch), W, round((f + 1) * ch)))
        alfa = np.asarray(franja)[..., 3] > 0
        ocupada = alfa.sum(axis=0) > 2          # columnas con personaje

        # tramos continuos de columnas ocupadas
        tramos, ini = [], None
        for x, o in enumerate(ocupada):
            if o and ini is None:
                ini = x
            elif not o and ini is not None:
                tramos.append([ini, x]); ini = None
        if ini is not None:
            tramos.append([ini, W])

        # unir tramos separados por huecos minusculos (p.ej. mochila/brazo)
        unidos = []
        for t in tramos:
            if unidos and t[0] - unidos[-1][1] < 8:
                unidos[-1][1] = t[1]
            else:
                unidos.append(t)
        # descartar ruido (tramos muy finos)
        unidos = [t for t in unidos if t[1] - t[0] > 25]

        fila = []
        for x0, x1 in unidos:
            celda = franja.crop((x0, 0, x1, franja.height))
            bbox = celda.getbbox()
            fila.append(celda.crop(bbox) if bbox else celda)
        frames.append(fila)
    return frames


def main() -> None:
    SALIDA.mkdir(parents=True, exist_ok=True)
    datos = {}

    # 1) cargar, quitar fondo y cortar todas las direcciones
    for d, archivo in ENTRADAS.items():
        if not Path(archivo).exists():
            print(f"[!] Falta {archivo}, se omite '{d}'")
            continue
        print(f"Procesando {d} ({archivo})...")
        datos[d] = cortar(quitar_verde(Image.open(archivo)))

    if not datos:
        print("No se encontro ninguna hoja.")
        return

    # 2) escala comun: el idle de cada direccion define su altura real,
    #    y todas se llevan a ALTO_PERSONAJE
    escalas = {}
    for d, frames in datos.items():
        alto_idle = np.median([fr.height for fr in frames[1]])
        escalas[d] = ALTO_PERSONAJE / alto_idle

    # 3) escalar frames (LANCZOS conserva los contornos al reducir;
    #    si PIXELAR, luego el alfa se vuelve binario = bordes de pixel art)
    finales = {}
    for d, frames in datos.items():
        s = escalas[d]
        finales[d] = [[fr.resize((max(1, round(fr.width * s)),
                                  max(1, round(fr.height * s))),
                                 Image.LANCZOS)
                       for fr in fila] for fila in frames]
        if PIXELAR:  # alfa binario = bordes de pixel art limpios
            for fila in finales[d]:
                for i, fr in enumerate(fila):
                    a = np.asarray(fr).copy()
                    a[..., 3] = np.where(a[..., 3] > 128, 255, 0)
                    fila[i] = limpiar_ruido(Image.fromarray(a, "RGBA"))

    # 4) tamano de celda unico para TODO (el frame mas grande + margen)
    todos = [fr for d in finales for fila in finales[d] for fr in fila]
    cel_w = max(fr.width for fr in todos) + 2 * MARGEN
    cel_h = max(fr.height for fr in todos) + 2 * MARGEN
    cel_w += cel_w % 2  # par, para centrar exacto

    # 5) pegar con pivote abajo-centro y exportar
    meta = {"cell_w": cel_w, "cell_h": cel_h,
            "pivot": "bottom-center", "animations": {}}
    for d, filas in finales.items():
        n_max = max(len(fila) for fila in filas)
        hoja = Image.new("RGBA", (cel_w * n_max, cel_h * FILAS), (0, 0, 0, 0))
        for f, fila in enumerate(filas):
            nombre = f"{FILA_ANIM[f]}_{d}"
            carpeta = SALIDA / "frames" / nombre
            carpeta.mkdir(parents=True, exist_ok=True)
            for c, fr in enumerate(fila):
                celda = Image.new("RGBA", (cel_w, cel_h), (0, 0, 0, 0))
                x = (cel_w - fr.width) // 2
                y = cel_h - MARGEN - fr.height   # pies en la misma linea
                celda.paste(fr, (x, y), fr)
                celda.save(carpeta / f"{nombre}_{c}.png")
                hoja.paste(celda, (c * cel_w, f * cel_h))
            meta["animations"][nombre] = {"sheet": f"{d}.png", "row": f,
                                          "frames": len(fila)}
        hoja.save(SALIDA / f"{d}.png")
        print(f"  -> {SALIDA / (d + '.png')}")

        # Copia en el formato que usan los eventos del juego (p.ej. Evento_2):
        #   Sobreviviente/abajo/frame_1.png ... Sobreviviente/quieto_abajo/frame_1.png ...
        for f, fila in enumerate(filas):
            carpeta_juego = SALIDA / (CARPETA_JUEGO[d] if f == 0 else f"quieto_{CARPETA_JUEGO[d]}")
            carpeta_juego.mkdir(parents=True, exist_ok=True)
            for viejo in carpeta_juego.glob("frame_*.png"):
                viejo.unlink()          # por si antes habia mas frames
            nombre = f"{FILA_ANIM[f]}_{d}"
            for c in range(len(fila)):
                shutil.copyfile(SALIDA / "frames" / nombre / f"{nombre}_{c}.png",
                                carpeta_juego / f"frame_{c + 1}.png")

    (SALIDA / "sprites.json").write_text(json.dumps(meta, indent=2))
    print(f"\nListo. Celda: {cel_w}x{cel_h}px. Revisa la carpeta '{SALIDA}'.")


if __name__ == "__main__":
    main()
