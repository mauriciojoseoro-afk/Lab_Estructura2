"""CLIENTE del multijugador. Lo usa el juego (no se ejecuta solo).

    from Red import cliente
    red = cliente.conectar()        # None si no hay servidor -> se juega en modo un jugador
    ok, por = red.elegir("CIUDADANO")

Un hilo en segundo plano recibe los mensajes del servidor y mantiene
actualizado red.ocupados = {rol: nombre}.
"""
import getpass
import queue
import socket
import threading

from Red.protocolo import enviar, lineas, leer_config

_conexion = None            # una sola conexion para todo el juego


class Conexion:
    def __init__(self, sock, nombre):
        self.sock = sock
        self.nombre = nombre
        self.id = None
        self.rol = None                      # rol que el servidor nos confirmo
        self.ocupados = {}                   # {rol: nombre} (lo actualiza el hilo)
        self.conectado = True
        self._respuestas = queue.Queue()     # respuestas a ELEGIR
        self._candado = threading.Lock()
        threading.Thread(target=self._escuchar, daemon=True).start()
        self._enviar({"tipo": "HOLA", "nombre": nombre})

    def _enviar(self, mensaje):
        try:
            with self._candado:
                enviar(self.sock, mensaje)
        except OSError:
            self.conectado = False

    def _escuchar(self):
        for msg in lineas(self.sock):
            tipo = msg.get("tipo")
            if tipo == "BIENVENIDO":
                self.id = msg.get("id")
                self.ocupados = msg.get("ocupados", {})
            elif tipo == "ROLES":
                self.ocupados = msg.get("ocupados", {})
            elif tipo in ("ELEGIDO", "OCUPADO"):
                self._respuestas.put(msg)
        self.conectado = False
        self._respuestas.put({"tipo": "OCUPADO", "por": "se perdio la conexion"})

    # ---------- lo que usa el juego ----------
    def ocupado_por_otro(self, rol):
        """Nombre de quien usa el rol, o None si esta libre o es nuestro."""
        if rol == self.rol:
            return None
        return self.ocupados.get(rol)

    def elegir(self, rol, espera=3.0):
        """Pide el rol al servidor. Devuelve (True, None) o (False, 'quien lo tiene')."""
        while not self._respuestas.empty():
            self._respuestas.get_nowait()
        self._enviar({"tipo": "ELEGIR", "rol": rol})
        try:
            r = self._respuestas.get(timeout=espera)
        except queue.Empty:
            return False, "el servidor no respondio"
        if r.get("tipo") == "ELEGIDO":
            self.rol = rol
            return True, None
        return False, r.get("por")

    def soltar(self):
        """Libera nuestro rol (por ejemplo, al volver a la seleccion)."""
        if self.rol is not None:
            self.rol = None
            self._enviar({"tipo": "SOLTAR"})


def conectar(nombre=None, espera=1.0):
    """Intenta conectarse al servidor de Red/config.json (solo la primera vez).
    Si no hay servidor devuelve None y el juego sigue en modo un jugador."""
    global _conexion
    if _conexion is not None and _conexion.conectado:
        return _conexion
    host, puerto = leer_config()
    try:
        sock = socket.create_connection((host, puerto), timeout=espera)
        sock.settimeout(None)
    except OSError:
        _conexion = None
        return None
    try:
        nombre = nombre or getpass.getuser()
    except Exception:
        nombre = "Jugador"
    _conexion = Conexion(sock, nombre)
    return _conexion


def actual():
    """La conexion activa (o None en modo un jugador)."""
    return _conexion if _conexion is not None and _conexion.conectado else None
