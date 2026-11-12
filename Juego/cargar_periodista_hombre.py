"""Cargador de las poses del periodista hombre para Pygame."""
from pathlib import Path
import pygame


def cargar_periodista_hombre(raiz_assets, tamano=None):
    """Devuelve dict[str, list[pygame.Surface]].

    raiz_assets: ruta a la carpeta Assets del juego.
    tamano: (ancho, alto) opcional para redimensionar cada fotograma.
    Llamar después de inicializar pygame y crear la ventana.
    """
    carpeta = Path(raiz_assets) / "Personajes" / "Periodista" / "Hombre"
    animaciones = {}
    for direccion in ("abajo", "arriba", "derecha", "izquierda",
                      "quieto_abajo", "quieto_arriba", "quieto_derecha", "quieto_izquierda"):
        archivos = sorted((carpeta / direccion).glob("frame_*.png"))
        if not archivos:
            raise FileNotFoundError(f"No se encontraron fotogramas en {carpeta / direccion}")
        fotogramas = []
        for archivo in archivos:
            superficie = pygame.image.load(str(archivo)).convert_alpha()
            if tamano is not None:
                superficie = pygame.transform.smoothscale(superficie, tamano)
            fotogramas.append(superficie)
        animaciones[direccion] = fotogramas
    return animaciones


def frame_actual(animaciones, direccion, tiempo_segundos, fps=8):
    """Obtiene el frame correspondiente sin modificar el estado del juego."""
    frames = animaciones[direccion]
    return frames[int(tiempo_segundos * fps) % len(frames)]
