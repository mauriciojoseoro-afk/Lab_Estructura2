"""SERVIDOR de The Leader (multijugador local).

Se ejecuta UNA vez, en el PC que hace de servidor, desde la carpeta Juego:
    python -m Red.servidor

Mantiene y sincroniza el estado compartido:
  - jugadores conectados y que rol usa cada uno (un rol solo puede tenerlo una persona)
  - progreso e indicadores de cada jugador (para el panel del grupo)
  - el campo minado compartido: la misma semilla para todos y las minas que ya se pisaron
  - la ENTREVISTA POR TURNOS: sala de espera, la decision del dueño de cada fase
    o la votacion del grupo, repartida a todos en orden
  - el FINAL DEL GRUPO: espera a que todos terminen, promedia sus indicadores y puntajes
    y envia a todos la misma tabla y el mismo puntaje del grupo
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
        # SALA DE ESPERA: si la partida se creo desde el menu (CON COMPAÑIA), solo el anfitrion
        # puede iniciarla. Si el servidor se abrio con el comando, no hay anfitrion y se juega como antes.
        self.anfitrion = None            # id del jugador que creo la partida
        self.iniciada = True
        # CAMPO MINADO COMPARTIDO: con la misma semilla todos generan las mismas minas
        self.semilla = random.randint(1, 10 ** 9)
        self.minas_pisadas = {}          # indice de la mina -> nombre de quien la piso
        # ENTREVISTA POR TURNOS
        self.entrevista_listos = set()   # ids de quienes ya llegaron a la entrevista
        self.decisiones = []             # decision numero n -> opcion elegida (la misma para todos)
        self.votos = {}                  # numero de decision -> [(id, opcion), ...] en orden de llegada

    # ---------- estado ----------
    def ocupados(self):
        """{rol: nombre} de los roles en uso (llamar con el candado tomado)."""
        return {r: self.jugadores[j]["nombre"] for r, j in self.roles.items() if j is not None}

    def lista_jugadores(self):
        return [{"nombre": d["nombre"], "rol": d["rol"], "progreso": d["progreso"],
                 "indicadores": d["indicadores"], "decision": d["decision"],
                 "anfitrion": j == self.anfitrion}
                for j, d in sorted(self.jugadores.items())]

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

    # ---------- final del grupo ----------
    def participantes(self):
        """Jugadores que estan jugando (tienen rol)."""
        return [d for d in self.jugadores.values() if d["rol"] is not None]

    def revisar_final(self):
        """Avisa quien falta; si ya terminaron todos, calcula el promedio y lo envia."""
        jugando = self.participantes()
        listos = [d["nombre"] for d in jugando if d["termino"]]
        faltan = [d["nombre"] for d in jugando if not d["termino"]]
        if not listos:
            return
        self.difundir({"tipo": "ESPERA", "listos": listos, "faltan": faltan})
        if faltan:
            return
        terminados = [d for d in jugando if d["termino"]]
        claves = ("Confianza", "Caos", "Cohesión")
        promedio = {k: round(sum(d["indicadores"].get(k, 0) for d in terminados) / len(terminados), 1)
                    for k in claves}
        puntaje = round(sum(d["puntaje"] for d in terminados) / len(terminados))
        tabla = sorted(({"nombre": d["nombre"], "rol": d["rol"], "indicadores": d["indicadores"],
                         "puntaje": d["puntaje"]} for d in terminados),
                       key=lambda fila: fila["puntaje"], reverse=True)
        self.difundir({"tipo": "FINAL", "promedio": promedio, "puntaje": puntaje, "tabla": tabla})
        print(f"    FINAL DEL GRUPO: puntaje {puntaje}  promedio {promedio}")
        for d in terminados:                 # listo para otra partida
            d["termino"] = False

    # ---------- entrevista por turnos ----------
    def revisar_entrevista(self):
        """Sala de espera: cuando llegan todos los que juegan, empieza la entrevista."""
        jugando = [j for j, d in self.jugadores.items() if d["rol"] is not None]
        if not self.entrevista_listos:
            return
        listos = [self.jugadores[j]["nombre"] for j in jugando if j in self.entrevista_listos]
        faltan = [self.jugadores[j]["nombre"] for j in jugando if j not in self.entrevista_listos]
        self.difundir({"tipo": "ENTREVISTA_ESPERA", "listos": listos, "faltan": faltan})
        if not faltan:
            self.decisiones = []
            self.votos = {}
            self.entrevista_listos = set()
            self.difundir({"tipo": "ENTREVISTA_INICIO"})
            print("    ENTREVISTA: empieza con", ", ".join(listos))

    def publicar_decision(self, numero, opcion):
        self.decisiones.append(opcion)
        self.difundir({"tipo": "DECISION", "numero": numero, "opcion": opcion})

    def revisar_votos(self, numero):
        """Si ya votaron todos los que juegan, gana la opcion con mas votos
        (empate: la que se voto primero)."""
        if numero != len(self.decisiones) or numero not in self.votos:
            return
        jugando = [j for j, d in self.jugadores.items() if d["rol"] is not None]
        votos = [(j, o) for j, o in self.votos[numero] if j in jugando]
        self.difundir({"tipo": "VOTOS", "numero": numero, "votaron": len(votos), "total": len(jugando)})
        if len(votos) < len(jugando):
            return
        conteo = {}
        for _, o in votos:
            conteo[o] = conteo.get(o, 0) + 1
        mayor = max(conteo.values())
        ganadora = next(o for _, o in votos if conteo[o] == mayor)
        print(f"    ENTREVISTA: votacion {numero} -> opcion {ganadora + 1} {conteo}")
        self.publicar_decision(numero, ganadora)

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
                                   "progreso": "Eligiendo personaje", "indicadores": None, "decision": None,
                                   "termino": False, "puntaje": None}
        print(f"[+] Conectado jugador {jid} desde {direccion[0]}")
        try:
            for msg in lineas(sock):
                tipo = msg.get("tipo")
                with self.candado:
                    if tipo == "HOLA":
                        nombre = str(msg.get("nombre") or "").strip()[:20]
                        if nombre:
                            self.jugadores[jid]["nombre"] = nombre
                        if msg.get("anfitrion") and self.anfitrion is None:
                            self.anfitrion = jid             # el que creo la partida
                            self.iniciada = False            # se espera a que el pulse INICIAR
                        elif self.iniciada and self.anfitrion is not None:
                            enviar(sock, {"tipo": "RECHAZADO", "motivo": "La partida ya empezó"})
                            break                            # llega tarde: no entra
                        enviar(sock, {"tipo": "BIENVENIDO", "id": jid, "ocupados": self.ocupados(),
                                      "anfitrion": self.anfitrion, "iniciada": self.iniciada})
                        self.avisar_jugadores()

                    elif tipo == "INICIAR":
                        if jid == self.anfitrion and not self.iniciada:
                            self.iniciada = True
                            self.difundir({"tipo": "INICIO"})
                            print("[*] El anfitrion inicio la partida")

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

                    elif tipo == "ENTREVISTA_LISTO":
                        self.entrevista_listos.add(jid)
                        self.revisar_entrevista()

                    elif tipo == "ELECCION":
                        # Una decision de la entrevista: del dueño de la fase o un voto
                        numero, opcion = msg.get("numero"), msg.get("opcion")
                        if not isinstance(numero, int) or not isinstance(opcion, int):
                            continue
                        if numero != len(self.decisiones):
                            continue                 # ya se decidio (o llega fuera de orden)
                        if msg.get("modo") == "voto":
                            lista = self.votos.setdefault(numero, [])
                            if all(j != jid for j, _ in lista):
                                lista.append((jid, opcion))
                            self.revisar_votos(numero)
                        else:
                            self.publicar_decision(numero, opcion)

                    elif tipo == "TERMINE":
                        # Termino la partida: guarda sus indicadores y puntaje y espera a los demas
                        datos = self.jugadores[jid]
                        if isinstance(msg.get("indicadores"), dict) and isinstance(msg.get("puntaje"), (int, float)):
                            datos["indicadores"] = msg["indicadores"]
                            datos["puntaje"] = msg["puntaje"]
                            datos["termino"] = True
                            datos["progreso"] = "Esperando al grupo"
                            print(f"    {datos['nombre']} termino con puntaje {datos['puntaje']}")
                            self.avisar_jugadores()
                            self.revisar_final()

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
                self.revisar_final()             # si los demas lo estaban esperando, ya no
                self.entrevista_listos.discard(jid)
                self.revisar_entrevista()
                for numero in list(self.votos):
                    self.revisar_votos(numero)
            sock.close()
            print(f"[-] {nombre} se desconecto" + (f" (libera {rol})" if rol else ""))

    def abrir(self):
        servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        servidor.bind(("0.0.0.0", self.puerto))
        servidor.listen()
        return servidor

    def aceptar(self, servidor):
        while True:
            sock, direccion = servidor.accept()
            threading.Thread(target=self.atender, args=(sock, direccion), daemon=True).start()

    def iniciar(self):
        servidor = self.abrir()
        print(f"Servidor de The Leader escuchando en el puerto {self.puerto}")
        print("IP de este PC (ponla en Red/config.json de los otros PCs):", ip_local())
        print("Ctrl + C para cerrar.\n")
        try:
            self.aceptar(servidor)
        except KeyboardInterrupt:
            print("\nServidor cerrado.")
        finally:
            servidor.close()


_en_marcha = None          # servidor abierto desde el menu (CREAR PARTIDA -> CON COMPAÑIA)


def en_segundo_plano(puerto=None):
    """Abre el servidor DENTRO del juego, en un hilo, sin escribir comandos.
    Devuelve (ok, ip_de_este_pc). Si ya hay un servidor abierto en este PC
    (por ejemplo con el comando), se usa ese. Se cierra al cerrar el juego."""
    global _en_marcha
    if puerto is None:
        _, puerto = leer_config()
    if _en_marcha is None:
        try:                                         # ¿ya hay uno escuchando aqui?
            socket.create_connection(("127.0.0.1", puerto), timeout=0.5).close()
            return True, ip_local()
        except OSError:
            pass
        srv = Servidor(puerto)
        try:
            sock = srv.abrir()
        except OSError:
            return False, ip_local()
        threading.Thread(target=srv.aceptar, args=(sock,), daemon=True).start()
        _en_marcha = srv
    return True, ip_local()


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
