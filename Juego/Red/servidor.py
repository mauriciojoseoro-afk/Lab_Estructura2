"""SERVIDOR de The Leader (multijugador local).

Se ejecuta UNA vez, en el PC que hace de servidor, desde la carpeta Juego:
    python -m Red.servidor

Mantiene y sincroniza el estado compartido:
  - jugadores conectados y que rol usa cada uno (un rol solo puede tenerlo una persona)
  - progreso e indicadores de cada jugador (para el panel del grupo)
  - el campo minado compartido: la misma semilla para todos y las minas que ya se pisaron
Cuando un jugador se desconecta, su rol queda libre.
"""
import random
import socket
import threading

try:
    from Red.protocolo import ROLES, enviar, lineas, leer_config
except ImportError:                      # si se ejecuta como "python servidor.py" dentro de Red/
    from protocolo import ROLES, enviar, lineas, leer_config


class Servidor:
    def __init__(self, puerto):
        self.puerto = puerto
        self.candado = threading.Lock()  # protege el estado: dos hilos no lo cambian a la vez
        self.jugadores = {}              # id -> {"nombre", "rol", "sock", "progreso", "indicadores", "decision"}
        self.roles = {r: None for r in ROLES}   # rol -> id del jugador que lo usa (o None)
        self.siguiente_id = 1
        # CAMPO MINADO COMPARTIDO: con la misma semilla todos generan las mismas minas
        self.semilla = random.randint(1, 10 ** 9)
        self.minas_pisadas = {}          # indice de la mina -> nombre de quien la piso

    # ---------- estado ----------
    def ocupados(self):
        """{rol: nombre} de los roles en uso (llamar con el candado tomado)."""
        return {r: self.jugadores[j]["nombre"] for r, j in self.roles.items() if j is not None}

    def lista_jugadores(self):
        return [{"nombre": d["nombre"], "rol": d["rol"], "progreso": d["progreso"],
                 "indicadores": d["indicadores"], "decision": d["decision"]}
                for _, d in sorted(self.jugadores.items())]

    def difundir(self, mensaje):
        """Envia un mensaje a todos los jugadores conectados."""
        for datos in list(self.jugadores.values()):
            try:
                enviar(datos["sock"], mensaje)
            except OSError:
                pass

    def avisar_roles(self):
        self.difundir({"tipo": "ROLES", "ocupados": self.ocupados()})
        self.avisar_jugadores()

    def avisar_jugadores(self):
        self.difundir({"tipo": "JUGADORES", "lista": self.lista_jugadores()})

    def soltar_rol(self, jid):
        rol = self.jugadores[jid]["rol"]
        if rol is not None:
            self.roles[rol] = None
            self.jugadores[jid]["rol"] = None
        return rol

    # ---------- un hilo por jugador ----------
    def atender(self, sock, direccion):
        with self.candado:
            jid = self.siguiente_id
            self.siguiente_id += 1
            self.jugadores[jid] = {"nombre": f"Jugador {jid}", "rol": None, "sock": sock,
                                   "progreso": "Eligiendo personaje", "indicadores": None, "decision": None}
        print(f"[+] Conectado jugador {jid} desde {direccion[0]}")
        try:
            for msg in lineas(sock):
                tipo = msg.get("tipo")
                with self.candado:
                    if tipo == "HOLA":
                        nombre = str(msg.get("nombre") or "").strip()[:20]
                        if nombre:
                            self.jugadores[jid]["nombre"] = nombre
                        enviar(sock, {"tipo": "BIENVENIDO", "id": jid, "ocupados": self.ocupados()})
                        self.avisar_jugadores()

                    elif tipo == "ELEGIR":
                        rol = msg.get("rol")
                        if rol not in self.roles:
                            enviar(sock, {"tipo": "OCUPADO", "rol": rol, "por": "rol desconocido"})
                            continue
                        dueno = self.roles[rol]
                        if dueno is not None and dueno != jid:
                            # Alguien lo tomo primero: se rechaza
                            enviar(sock, {"tipo": "OCUPADO", "rol": rol, "por": self.jugadores[dueno]["nombre"]})
                            continue
                        self.soltar_rol(jid)               # si tenia otro, lo libera
                        self.roles[rol] = jid
                        self.jugadores[jid]["rol"] = rol
                        self.jugadores[jid]["progreso"] = "Empezando"
                        enviar(sock, {"tipo": "ELEGIDO", "rol": rol})
                        print(f"    {self.jugadores[jid]['nombre']} eligio {rol}")
                        self.avisar_roles()

                    elif tipo == "SOLTAR":
                        if self.soltar_rol(jid):
                            self.jugadores[jid]["progreso"] = "Eligiendo personaje"
                            self.avisar_roles()

                    elif tipo == "ROLES?":
                        enviar(sock, {"tipo": "ROLES", "ocupados": self.ocupados()})

                    elif tipo == "RESULTADO":
                        # Un jugador termino un evento: se guarda y se reparte a todos
                        datos = self.jugadores[jid]
                        datos["progreso"] = str(msg.get("evento") or datos["progreso"])
                        if isinstance(msg.get("indicadores"), dict):
                            datos["indicadores"] = msg["indicadores"]
                        if msg.get("decision"):
                            datos["decision"] = msg["decision"]
                        print(f"    {datos['nombre']}: {datos['progreso']} {datos['indicadores'] or ''}")
                        self.avisar_jugadores()

                    elif tipo == "CAMPO?":
                        enviar(sock, {"tipo": "CAMPO", "semilla": self.semilla,
                                      "pisadas": {str(i): n for i, n in self.minas_pisadas.items()}})

                    elif tipo == "PISE":
                        indice = msg.get("indice")
                        if isinstance(indice, int) and indice not in self.minas_pisadas:
                            nombre = self.jugadores[jid]["nombre"]
                            self.minas_pisadas[indice] = nombre
                            self.difundir({"tipo": "MINA", "indice": indice, "por": nombre})
        finally:
            with self.candado:
                nombre = self.jugadores[jid]["nombre"]
                rol = self.soltar_rol(jid)
                del self.jugadores[jid]
                self.avisar_roles()
            sock.close()
            print(f"[-] {nombre} se desconecto" + (f" (libera {rol})" if rol else ""))

    def iniciar(self):
        servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        servidor.bind(("0.0.0.0", self.puerto))
        servidor.listen()
        print(f"Servidor de The Leader escuchando en el puerto {self.puerto}")
        print("IP de este PC (ponla en Red/config.json de los otros PCs):", ip_local())
        print("Ctrl + C para cerrar.\n")
        try:
            while True:
                sock, direccion = servidor.accept()
                threading.Thread(target=self.atender, args=(sock, direccion), daemon=True).start()
        except KeyboardInterrupt:
            print("\nServidor cerrado.")
        finally:
            servidor.close()


def ip_local():
    """IP de este PC en la red local (no envia datos, solo consulta la ruta)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


if __name__ == "__main__":
    _, puerto = leer_config()
    Servidor(puerto).iniciar()
