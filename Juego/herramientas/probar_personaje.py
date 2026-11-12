"""
probar_personaje.py  -  Python 3.12 + Pygame
Carga los sprites de 'sprites_final/' y mueve al personaje con WASD/flechas.

Instalar:   pip install pygame-ce     (o: pip install pygame)
Usar:       python probar_personaje.py
"""
import json
from pathlib import Path

import pygame

CARPETA = Path(__file__).resolve().parent.parent / "Assets" / "Personajes" / "Sobreviviente"
ESCALA = 2            # zoom en pantalla (entero = pixeles nitidos)
VELOCIDAD = 120       # px por segundo (en coordenadas del sprite)
FPS_ANIM = {"walk": 10, "idle": 5}


class Personaje:
    def __init__(self, x: float, y: float):
        meta = json.loads((CARPETA / "sprites.json").read_text())
        cw, ch = meta["cell_w"], meta["cell_h"]
        self.anims: dict[str, list[pygame.Surface]] = {}
        hojas: dict[str, pygame.Surface] = {}
        for nombre, info in meta["animations"].items():
            hoja = hojas.setdefault(info["sheet"],
                                    pygame.image.load(CARPETA / info["sheet"]).convert_alpha())
            frames = []
            for c in range(info["frames"]):
                f = hoja.subsurface((c * cw, info["row"] * ch, cw, ch))
                frames.append(pygame.transform.scale_by(f, ESCALA))  # nearest
            self.anims[nombre] = frames

        self.pos = pygame.Vector2(x, y)   # posicion de los PIES
        self.direccion = "down"
        self.estado = "idle"
        self.t = 0.0

    def actualizar(self, dt: float, teclas) -> None:
        mov = pygame.Vector2(
            (teclas[pygame.K_d] or teclas[pygame.K_RIGHT]) - (teclas[pygame.K_a] or teclas[pygame.K_LEFT]),
            (teclas[pygame.K_s] or teclas[pygame.K_DOWN]) - (teclas[pygame.K_w] or teclas[pygame.K_UP]),
        )
        nuevo = "walk" if mov.length_squared() else "idle"
        if mov.length_squared():
            # el eje dominante decide la direccion
            if abs(mov.x) > abs(mov.y):
                self.direccion = "right" if mov.x > 0 else "left"
            else:
                self.direccion = "down" if mov.y > 0 else "up"
            self.pos += mov.normalize() * VELOCIDAD * ESCALA * dt
        if nuevo != self.estado:
            self.estado, self.t = nuevo, 0.0   # reinicia el ciclo al cambiar
        self.t += dt

    def dibujar(self, pantalla: pygame.Surface) -> None:
        frames = self.anims[f"{self.estado}_{self.direccion}"]
        i = int(self.t * FPS_ANIM[self.estado]) % len(frames)
        img = frames[i]
        # pivote abajo-centro: los pies quedan en self.pos
        pantalla.blit(img, img.get_rect(midbottom=self.pos))


def main() -> None:
    pygame.init()
    pantalla = pygame.display.set_mode((1000, 700))
    pygame.display.set_caption("Prueba de sprites - WASD / flechas")
    reloj = pygame.time.Clock()
    pj = Personaje(500, 450)

    while True:
        dt = reloj.tick(60) / 1000
        for e in pygame.event.get():
            if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                pygame.quit()
                return
        pj.actualizar(dt, pygame.key.get_pressed())
        pantalla.fill((60, 70, 55))
        pj.dibujar(pantalla)
        pygame.display.flip()


if __name__ == "__main__":
    main()
