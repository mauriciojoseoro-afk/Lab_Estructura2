"""
Saca el audio (.mp3) de cada video .mp4 de Juego/Assets/Videos.

El juego reproduce el video con OpenCV y el sonido con pygame.mixer,
asi que cada video necesita un .mp3 con el mismo nombre al lado.

Uso (desde la carpeta Lab_Estructura2):
    python Juego/extraer_audio.py

Si el .mp3 ya existe y es mas nuevo que el video, no lo vuelve a crear.
"""

import subprocess
from pathlib import Path

import imageio_ffmpeg

CARPETA_VIDEOS = Path(__file__).parent / "Assets" / "Videos"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


def extraer(video: Path) -> None:
    audio = video.with_suffix(".mp3")

    if audio.exists() and audio.stat().st_mtime >= video.stat().st_mtime:
        print(f"  Ya existe:   {audio.name}")
        return

    resultado = subprocess.run(
        [FFMPEG, "-y", "-i", str(video), "-vn", "-acodec", "libmp3lame", "-q:a", "2", str(audio)],
        capture_output=True,
        text=True,
    )

    if resultado.returncode == 0:
        print(f"  Creado:      {audio.name}")
    else:
        print(f"  ERROR en {video.name}: el video no tiene audio o no se pudo leer.")


def main() -> None:
    videos = sorted(CARPETA_VIDEOS.glob("*.mp4"))
    if not videos:
        print(f"No encontre videos en {CARPETA_VIDEOS}")
        return

    print(f"Revisando {len(videos)} videos en {CARPETA_VIDEOS}\n")
    for video in videos:
        tamano_mb = video.stat().st_size / (1024 * 1024)
        aviso = "  <-- PASA DE 100 MB, GitHub no lo acepta" if tamano_mb > 100 else ""
        print(f"{video.name} ({tamano_mb:.1f} MB){aviso}")
        extraer(video)

    print("\nListo.")


if __name__ == "__main__":
    main()
