"""Panel del grupo: quien esta jugando, en que va y sus indicadores.
Se dibuja en el mapa (entre evento y evento) cuando hay servidor."""
import pygame

NOMBRE_ROL = {"PRESIDENTE": "Presidente", "CIUDADANO": "Ciudadano",
              "PERIODISTA": "Periodista", "INFLUENCER": "Influencer", None: "sin rol"}
_fuentes = {}


def _fuente(tam, negrita=False):
    clave = (tam, negrita)
    if clave not in _fuentes:
        _fuentes[clave] = pygame.font.SysFont("consolas", tam, bold=negrita)
    return _fuentes[clave]


def dibujar_panel_grupo(canvas, red, x=18, y=18):
    """Dibuja la tabla del grupo. red: la conexion (Red.cliente)."""
    if red is None:
        return
    jugadores = red.jugadores
    ancho, alto_fila = 470, 44
    alto = 40 + alto_fila * max(1, len(jugadores))
    caja = pygame.Surface((ancho, alto), pygame.SRCALPHA)
    caja.fill((14, 16, 20, 215))
    pygame.draw.rect(caja, (200, 160, 90), caja.get_rect(), 2, border_radius=8)
    canvas.blit(caja, (x, y))

    titulo = _fuente(18, True).render(f"GRUPO · {len(jugadores)} conectado(s)", True, (235, 215, 175))
    canvas.blit(titulo, (x + 14, y + 10))
    for i, j in enumerate(jugadores):
        fy = y + 40 + i * alto_fila
        yo = j.get("nombre") == red.nombre and j.get("rol") == red.rol
        color = (255, 225, 140) if yo else (230, 230, 230)
        nombre = f"{j.get('nombre', '?')} ({NOMBRE_ROL.get(j.get('rol'), j.get('rol'))})" + ("  ← tú" if yo else "")
        canvas.blit(_fuente(16, True).render(nombre, True, color), (x + 14, fy))
        canvas.blit(_fuente(14).render(str(j.get("progreso") or ""), True, (160, 170, 180)), (x + 14, fy + 20))
        ind = j.get("indicadores")
        if ind:
            for k, (clave, col) in enumerate((("Confianza", (235, 235, 235)), ("Caos", (234, 80, 70)),
                                              ("Cohesión", (120, 200, 130)))):
                valor = ind.get(clave, 0)
                bx = x + 300 + k * 56
                canvas.blit(_fuente(12, True).render(clave[:4].upper(), True, (160, 160, 160)), (bx, fy))
                pygame.draw.rect(canvas, (60, 60, 60), (bx, fy + 18, 48, 6), border_radius=2)
                pygame.draw.rect(canvas, col, (bx, fy + 18, int(48 * max(0, min(100, valor)) / 100), 6), border_radius=2)
                canvas.blit(_fuente(12, True).render(str(int(valor)), True, col), (bx, fy + 26))
