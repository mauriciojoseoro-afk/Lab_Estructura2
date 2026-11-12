"""Protocolo comun del cliente y el servidor.

Cada mensaje es un diccionario JSON en UNA linea terminada en '\n'.
Todos llevan la clave "tipo". Ejemplos:
    cliente  -> servidor : {"tipo": "HOLA", "nombre": "Isaac"}
    cliente  -> servidor : {"tipo": "ELEGIR", "rol": "CIUDADANO"}
    servidor -> cliente  : {"tipo": "ELEGIDO", "rol": "CIUDADANO"}
    servidor -> cliente  : {"tipo": "OCUPADO", "rol": "CIUDADANO", "por": "Ana"}
    servidor -> todos    : {"tipo": "ROLES", "ocupados": {"CIUDADANO": "Isaac"}}
    cliente  -> servidor : {"tipo": "RESULTADO", "evento": "Evento 1", "indicadores": {...}, "decision": "VERIFICAR"}
    servidor -> todos    : {"tipo": "JUGADORES", "lista": [{"nombre", "rol", "progreso", "indicadores"}, ...]}
    cliente  -> servidor : {"tipo": "ENTREVISTA_LISTO"}     (sala de espera de la entrevista)
    servidor -> todos    : {"tipo": "ENTREVISTA_ESPERA", "listos": [...], "faltan": [...]}
    servidor -> todos    : {"tipo": "ENTREVISTA_INICIO"}
    cliente  -> servidor : {"tipo": "ELECCION", "numero": 3, "opcion": 1, "modo": "dueño" | "voto"}
    servidor -> todos    : {"tipo": "VOTOS", "numero": 3, "votaron": 1, "total": 2}
    servidor -> todos    : {"tipo": "DECISION", "numero": 3, "opcion": 1}
    cliente  -> servidor : {"tipo": "TERMINE", "indicadores": {...}, "puntaje": 85}
    servidor -> todos    : {"tipo": "ESPERA", "listos": ["Ana"], "faltan": ["Beto"]}
    servidor -> todos    : {"tipo": "FINAL", "promedio": {...}, "puntaje": 72, "tabla": [{nombre, rol, indicadores, puntaje}]}
"""
import json
from pathlib import Path

ROLES = ["PRESIDENTE", "CIUDADANO", "PERIODISTA", "INFLUENCER"]

_CONFIG = Path(__file__).resolve().parent / "config.json"


def leer_config():
    """IP y puerto del servidor (se cambian en Red/config.json)."""
    datos = {"servidor": "127.0.0.1", "puerto": 5050}
    try:
        datos.update(json.loads(_CONFIG.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        pass
    return datos["servidor"], int(datos["puerto"])


def enviar(sock, mensaje):
    """Envia un diccionario como una linea JSON."""
    sock.sendall((json.dumps(mensaje, ensure_ascii=False) + "\n").encode("utf-8"))


def lineas(sock):
    """Generador: devuelve los mensajes que llegan por el socket, uno por uno.
    Termina cuando la conexion se cierra."""
    pendiente = b""
    while True:
        try:
            datos = sock.recv(4096)
        except OSError:
            return
        if not datos:
            return
        pendiente += datos
        while b"\n" in pendiente:
            linea, pendiente = pendiente.split(b"\n", 1)
            if linea.strip():
                try:
                    yield json.loads(linea.decode("utf-8"))
                except ValueError:
                    continue
