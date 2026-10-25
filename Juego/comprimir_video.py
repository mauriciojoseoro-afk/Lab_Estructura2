"""
Comprime un video de Juego/Assets/Videos para que pese menos de 100 MB
(el limite de GitHub).

- Lo baja a 1280 px de ancho (la ventana del juego es de 900, no se nota).
- Le quita el audio, porque el juego ya usa el .mp3 aparte.
- Guarda una copia del original como <nombre>_original.mp4 por si acaso.
  Esa copia NO se debe subir a GitHub.

Uso (desde la carpeta Lab_Estructura2):
    python Juego/comprimir_video.py escena1_llegada.mp4
"""

import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg

CARPETA_VIDEOS = Path(__file__).parent / "Assets" / "Videos"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


def tamano_mb(ruta: Path) -> float:
    return ruta.stat().st_size / (1024 * 1024)


def main() -> None:
    if len(sys.argv) < 2:
        print("Escribe el nombre del video, por ejemplo:")
        print("    python Juego/comprimir_video.py escena1_llegada.mp4")
        return

    video = CARPETA_VIDEOS / sys.argv[1]
    if not video.exists():
        print(f"No encontre {video}")
        return

    original = video.with_name(video.stem + "_original.mp4")
    temporal = video.with_name(video.stem + "_temp.mp4")

    print(f"Comprimiendo {video.name} ({tamano_mb(video):.1f} MB)... puede tardar un par de minutos.")

    resultado = subprocess.run(
        [
            FFMPEG, "-y", "-i", str(video),
            "-vf", "scale=1280:-2",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "24",
            "-pix_fmt", "yuv420p",
            "-an",
            str(temporal),
        ],
        capture_output=True,
        text=True,
    )

    if resultado.returncode != 0:
        print("ERROR al comprimir:")
        print(resultado.stderr[-1500:])
        if temporal.exists():
            temporal.unlink()
        return

    if original.exists():
        original.unlink()
    video.rename(original)
    temporal.rename(video)

    print(f"Listo: {video.name} ahora pesa {tamano_mb(video):.1f} MB")
    print(f"El original quedo guardado como {original.name} (no lo subas a GitHub).")


if __name__ == "__main__":
    main()
