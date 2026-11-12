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
_solo = False               # True = el jugador eligio JUGAR SOLO en el menu: nunca se conecta
_destino = None             # (ip, puerto) elegido en el menu; None = usar Red/config.json


class Conexion:
    def __init__(self, sock, nombre):
        self.sock = sock
        self.nombre = nombre
        self.id = None
        self.rol = None                      # rol que el servidor nos confirmo
        self.ocupados = {}                   # {rol: nombre} (lo actualiza el hilo)
        self.jugadores = []                  # [{nombre, rol, progreso, indicadores, decision}]
        self.minas_pisadas = {}              # {indice de mina: nombre} del campo compartido
        self._campo = queue.Queue()
        self.espera = None                   # {"listos": [...], "faltan": [...]} mientras se espera al grupo
        self.final = None                    # {"promedio", "puntaje", "tabla"} cuando todos terminaron
        # entrevista por turnos
        self.entrevista_espera = None        # {"listos": [...], "faltan": [...]}
        self.entrevista_inicio = False
        self.decisiones = {}                 # numero de decision -> opcion
        self.votos = {}                      # numero -> (votaron, total)
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
            elif tipo == "JUGADORES":
                self.jugadores = msg.get("lista", [])
            elif tipo == "CAMPO":
                self.minas_pisadas = {int(i): n for i, n in msg.get("pisadas", {}).items()}
                self._campo.put(msg.get("semilla"))
            elif tipo == "MINA":
                self.minas_pisadas[int(msg["indice"])] = msg.get("por", "")
            elif tipo == "ESPERA":
                self.espera = {"listos": msg.get("listos", []), "faltan": msg.get("faltan", [])}
            elif tipo == "FINAL":
                self.final = msg
            elif tipo == "ENTREVISTA_ESPERA":
                self.entrevista_espera = {"listos": msg.get("listos", []), "faltan": msg.get("faltan", [])}
            elif tipo == "ENTREVISTA_INICIO":
                self.decisiones = {}
                self.votos = {}
                self.entrevista_inicio = True
            elif tipo == "DECISION":
                self.decisiones[int(msg["numero"])] = int(msg["opcion"])
            elif tipo == "VOTOS":
                self.votos[int(msg["numero"])] = (msg.get("votaron", 0), msg.get("total", 0))
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

    def jugando(self):
        """Cuantos jugadores tienen personaje elegido."""
        return sum(1 for j in self.jugadores if j.get("rol"))

    def terminar(self, indicadores, puntaje):
        """Avisa que termine la partida. El servidor responde con FINAL cuando terminen todos."""
        self.final = None
        self.espera = None
        self._enviar({"tipo": "TERMINE", "indicadores": indicadores, "puntaje": puntaje})

    def llegar_a_entrevista(self):
        """Entra a la sala de espera de la entrevista."""
        self.entrevista_inicio = False
        self.entrevista_espera = None
        self.decisiones = {}
        self.votos = {}
        self._enviar({"tipo": "ENTREVISTA_LISTO"})

    def elegir_en_entrevista(self, numero, opcion, modo):
        """modo: "dueño" (la fase es mia) o "voto" (la fase la decide el grupo)."""
        self._enviar({"tipo": "ELECCION", "numero": numero, "opcion": opcion, "modo": modo})

    def roles_en_juego(self):
        return {j.get("rol") for j in self.jugadores if j.get("rol")}

    def conectados(self):
        """Cuantos jugadores hay en la partida (contandome)."""
        return max(1, len(self.jugadores))

    def enviar_resultado(self, evento, indicadores=None, decision=None):
        """Avisa al grupo que termine un evento (y con que indicadores)."""
        self._enviar({"tipo": "RESULTADO", "evento": evento,
                      "indicadores": indicadores, "decision": decision})

    def pedir_campo(self, espera=2.0):
        """Semilla del campo minado compartido (None si el servidor no responde)."""
        while not self._campo.empty():
            self._campo.get_nowait()
        self._enviar({"tipo": "CAMPO?"})
        try:
            return self._campo.get(timeout=espera)
        except queue.Empty:
            return None

    def pisar(self, indice):
        """Avisa que pise una mina: se revela en el campo de todos."""
        if indice not in self.minas_pisadas:
            self.minas_pisadas[indice] = self.nombre
            self._enviar({"tipo": "PISE", "indice": indice})

    def soltar(self):
        """Libera nuestro rol (por ejemplo, al volver a la seleccion)."""
        if self.rol is not None:
            self.rol = None
            self._enviar({"tipo": "SOLTAR"})


def conectar(nombre=None, espera=1.0):
    """Intenta conectarse al servidor de Red/config.json (solo la primera vez).
    Si no hay servidor devuelve None y el juego sigue en modo un jugador."""
    global _conexion
    if _solo:
        return None
    if _conexion is not None and _conexion.conectado:
        return _conexion
    host, puerto = leer_config()
    if _destino is not None:
        host, puerto = _destino[0], _destino[1] or puerto
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


def _cerrar():
    global _conexion
    if _conexion is not None:
        try:
            _conexion.sock.close()
        except OSError:
            pass
    _conexion = None


def modo_solo():
    """Menu -> CREAR PARTIDA -> JUGAR SOLO: el juego no busca ningun servidor."""
    global _solo, _destino
    _cerrar()
    _solo, _destino = True, None


def usar_servidor(host, puerto=None):
    """Menu -> CON COMPAÑIA (host = 127.0.0.1) o UNIRSE (host = IP del anfitrion)."""
    global _solo, _destino
    _cerrar()
    _solo, _destino = False, (host, puerto)


def actual():
    """La conexion activa (o None en modo un jugador)."""
    return _conexion if _conexion is not None and _conexion.conectado else None


def reportar(evento, indicadores=None, decision=None):
    """Atajo para el juego: envia el resultado si hay servidor; si no, no hace nada."""
    red = actual()
    if red is not None:
        if indicadores is not None and hasattr(indicadores, "copia"):
            indicadores = indicadores.copia()
        red.enviar_resultado(evento, indicadores, decision)
