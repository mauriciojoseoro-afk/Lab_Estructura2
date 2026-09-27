import pygame
from pathlib import Path
from Arbol.Arbol_AVL import ArbolAVL
from Arbol import Preguntas
import Metodos


def Entrevista():
    pygame.init()

    ruta_assets = Path(__file__).parent.parent / "Assets" / "Interfaz"

    # un fondo distinto según de quién es el turno
    fondos_originales = {
        "periodista": pygame.image.load(ruta_assets / "Escritorio_Periodista.png"),
        "presidente": pygame.image.load(ruta_assets / "Escritorio_Presidente.png"),
        "influencer": pygame.image.load(ruta_assets / "Escritorio_Influencer.png"),
    }

    ancho_original, alto_original = fondos_originales["periodista"].get_size()
    ANCHO = 900
    ALTO = int(ANCHO * alto_original / ancho_original)

    display = pygame.display.set_mode((ANCHO, ALTO), pygame.RESIZABLE)
    pygame.display.set_caption("My Game")
    canvas = pygame.Surface((ANCHO, ALTO))

    fondos = {
        clave: pygame.transform.smoothscale(imagen.convert(), (ANCHO, ALTO))
        for clave, imagen in fondos_originales.items()
    }

    fuente = pygame.font.SysFont(None, 24)
    fuente_grande = pygame.font.SysFont(None, 28)

    # --- preparación, una sola vez ---
    preguntas = Preguntas.preguntas_P()
    respuestas = Preguntas.respuestas_P()

    arbol_preguntas = ArbolAVL()
    for id in preguntas.keys():
        arbol_preguntas.set(id)

    arbol_respuestas = ArbolAVL()
    for id in respuestas.keys():
        arbol_respuestas.set(id)

    ids_disponibles = list(preguntas.keys())

    fase = "pregunta"        # "pregunta" -> "respuesta" -> "opinion"
    id_pregunta_actual = None
    respuesta_elegida = None

    espectadores = 50
    puntos_influencer = 0
    preguntas_hechas = 0
    total_preguntas = len(preguntas)  # ahora se usan todas, no un límite fijo

    # qué fondo corresponde a cada fase (turno de quién es)
    fondo_por_fase = {
        "pregunta": "periodista",
        "respuesta": "presidente",
        "opinion": "influencer",
    }

    def texto_recortado(texto, ancho_max, fuente):
        if fuente.size(texto)[0] <= ancho_max:
            return texto
        while texto and fuente.size(texto + "...")[0] > ancho_max:
            texto = texto[:-1]
        return texto + "..."

    def dibujar_tarjeta(canvas, rect, texto, fuente, mouse_pos, click):
        # dibuja una casilla con borde (sin relleno) y el texto ajustado en varias líneas
        color_borde = (255, 230, 150) if rect.collidepoint(mouse_pos) else (255, 255, 255)
        pygame.draw.rect(canvas, color_borde, rect, width=2, border_radius=10)

        palabras = texto.split(" ")
        lineas = []
        linea = ""
        ancho_max = rect.width - 20
        for palabra in palabras:
            prueba = linea + palabra + " "
            if fuente.size(prueba)[0] > ancho_max:
                lineas.append(linea.strip())
                linea = palabra + " "
            else:
                linea = prueba
        lineas.append(linea.strip())

        y_texto = rect.y + 10
        for linea in lineas:
            if y_texto > rect.y + rect.height - 20:
                break  # no seguir escribiendo si ya no cabe dentro de la casilla
            render_linea = fuente.render(linea, True, (255, 255, 255))
            canvas.blit(render_linea, (rect.x + 10, y_texto))
            y_texto += 22

        return rect.collidepoint(mouse_pos) and click

    running = True
    while running:
        click = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.VIDEORESIZE:
                display = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                click = True

        # se calcula la escala/offset actuales para traducir el mouse a coordenadas del canvas
        ancho_ventana, alto_ventana = display.get_size()
        escala = min(ancho_ventana / ANCHO, alto_ventana / ALTO)
        offset_x = (ancho_ventana - int(ANCHO * escala)) // 2
        offset_y = (alto_ventana - int(ALTO * escala)) // 2
        mouse_pos = Metodos.mouse_en_canvas(escala, offset_x, offset_y)

        # se dibuja el fondo del rol que tiene el turno en esta fase
        canvas.blit(fondos[fondo_por_fase[fase]], (0, 0))

        titulo = fuente_grande.render(f"Entrevista  -  Pregunta {preguntas_hechas + 1} de {total_preguntas}", True, (255, 255, 255))
        canvas.blit(titulo, (30, 20))

        marcador = fuente.render(f"Espectadores: {espectadores}", True, (255, 255, 255))
        canvas.blit(marcador, (700, 20))

        # ---------- FASE 1: turno del Periodista ----------
        if fase == "pregunta":
            instruccion = fuente.render("Periodista: elige una pregunta", True, (255, 255, 255))
            canvas.blit(instruccion, (30, 60))

            y = 100
            preguntas_visibles = ids_disponibles[:3]  # solo se muestran 3 a la vez
            for id in preguntas_visibles:
                rect = pygame.Rect(30, y, 800, 90)
                texto_completo = f"{id}. {preguntas[id]}"

                if dibujar_tarjeta(canvas, rect, texto_completo, fuente, mouse_pos, click):
                    if arbol_preguntas.get(id) is not None:
                        id_pregunta_actual = id
                        ids_disponibles.remove(id)
                        fase = "respuesta"

                y += 105

        # ---------- FASE 2: turno del Presidente ----------
        elif fase == "respuesta":
            texto_pregunta = preguntas[id_pregunta_actual]
            lineas = [texto_pregunta[i:i + 90] for i in range(0, len(texto_pregunta), 90)]
            y_pregunta = 60
            for linea in lineas:
                render_linea = fuente.render(linea, True, (255, 255, 0))
                canvas.blit(render_linea, (30, y_pregunta))
                y_pregunta += 26

            instruccion = fuente.render("Presidente: elige una respuesta", True, (255, 255, 255))
            canvas.blit(instruccion, (30, y_pregunta + 10))

            opciones_nodo = arbol_respuestas.get(id_pregunta_actual)
            opciones = respuestas[id_pregunta_actual] if opciones_nodo is not None else {}
            claves = ["muy_buena", "regular", "mala"]

            y = y_pregunta + 45
            for clave in claves:
                rect = pygame.Rect(30, y, 800, 90)
                texto_opcion = opciones.get(clave, "")

                if dibujar_tarjeta(canvas, rect, texto_opcion, fuente, mouse_pos, click):
                    respuesta_elegida = clave
                    fase = "opinion"

                y += 105

        # ---------- FASE 3: turno del Influencer ----------
        elif fase == "opinion":
            texto_respuesta = respuestas[id_pregunta_actual][respuesta_elegida]
            lineas = [texto_respuesta[i:i + 90] for i in range(0, len(texto_respuesta), 90)]
            y_resp = 60
            for linea in lineas:
                render_linea = fuente.render(linea, True, (255, 255, 0))
                canvas.blit(render_linea, (30, y_resp))
                y_resp += 26

            instruccion = fuente.render("Influencer: da tu opinión sobre esta respuesta", True, (255, 255, 255))
            canvas.blit(instruccion, (30, y_resp + 10))

            boton_positiva = pygame.Rect(30, y_resp + 45, 270, 60)
            boton_imparcial = pygame.Rect(315, y_resp + 45, 270, 60)
            boton_mala = pygame.Rect(600, y_resp + 45, 270, 60)

            if Metodos.boton(canvas, boton_positiva, "Opinion positiva", mouse_pos, click):
                espectadores += 8
                fase = "siguiente"
            if Metodos.boton(canvas, boton_imparcial, "Opinion imparcial", mouse_pos, click):
                espectadores += 2
                fase = "siguiente"
            if Metodos.boton(canvas, boton_mala, "Opinion mala", mouse_pos, click):
                espectadores -= 6
                fase = "siguiente"

        # ---------- transición ----------
        if fase == "siguiente":
            preguntas_hechas += 1
            id_pregunta_actual = None
            respuesta_elegida = None

            if not ids_disponibles:
                if espectadores >= 70:
                    puntos_influencer += 10
                else:
                    puntos_influencer -= 5
                running = False
            else:
                fase = "pregunta"

        Metodos.mostrar_canvas(display, canvas)
        pygame.display.update()

    pygame.quit()
    return puntos_influencer