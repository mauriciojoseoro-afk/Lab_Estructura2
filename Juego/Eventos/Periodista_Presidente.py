import pygame
from pathlib import Path
from Arbol.Arbol_AVL import ArbolAVL
from Arbol import Preguntas
import Metodos


def Entrevista():
    pygame.init()

    ruta_assets = Path(__file__).parent.parent / "Assets" / "Interfaz"

    fondos_originales = {
        "periodista": pygame.image.load(ruta_assets / "Fondo_i.png"),
        "presidente": pygame.image.load(ruta_assets / "Fondo_i.png"),
        "influencer": pygame.image.load(ruta_assets / "Fondo_i.png"),
        "ciudadano": pygame.image.load(ruta_assets / "Fondo_i.png"),
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
    
    # Carga de la tipografía Upheaval desde los assets[cite: 8]
    ruta_fuente = ruta_assets / "upheavtt.ttf"
    try:
        fuente = pygame.font.Font(str(ruta_fuente), 16)          
        fuente_grande = pygame.font.Font(str(ruta_fuente), 22)    
    except Exception:
        # Fallback por si la ruta no coincide exactamente
        fuente = pygame.font.SysFont("Consolas", 16)
        fuente_grande = pygame.font.SysFont("Consolas", 20, bold=True)

    preguntas = Preguntas.preguntas_P()
    respuestas = Preguntas.respuestas_P()

    arbol_preguntas = ArbolAVL()
    for id in preguntas.keys():
        arbol_preguntas.set(id)

    arbol_respuestas = ArbolAVL()
    for id in respuestas.keys():
        arbol_respuestas.set(id)

    ids_disponibles = list(preguntas.keys())

    fase = "pregunta"        
    id_pregunta_actual = None
    respuesta_elegida = None

    espectadores = 50
    puntos_influencer = 0
    puntos_ciudadano = 0
    preguntas_hechas = 0
    total_preguntas = len(preguntas)  

    fondo_por_fase = {
        "pregunta": "periodista",
        "respuesta": "presidente",
        "ciudadano": "ciudadano",
        "opinion": "influencer",
    }

    # Dimensiones y centrado de la pantalla interior de la tablet
    SCREEN_ANCHO = 580                      
    SCREEN_X = ((ANCHO - SCREEN_ANCHO) // 2) - 15  
    SCREEN_Y = 160                          
    SCREEN_ALTO = ALTO - 190   

    def dibujar_tarjeta_centrada(canvas, rect, texto, fuente, mouse_pos, click):
        colision = rect.collidepoint(mouse_pos)
        color_borde = (100, 180, 100) if colision else (60, 120, 60)  
        
        pygame.draw.rect(canvas, (20, 25, 20), rect, border_radius=6)
        pygame.draw.rect(canvas, color_borde, rect, width=2, border_radius=6)

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

        altura_total_texto = len(lineas) * 18
        y_texto = rect.y + (rect.height - altura_total_texto) // 2

        for linea in lineas:
            render_linea = fuente.render(linea, True, (180, 240, 180)) 
            x_texto = rect.x + (rect.width - render_linea.get_width()) // 2
            canvas.blit(render_linea, (x_texto, y_texto))
            y_texto += 18

        return colision and click

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

        ancho_ventana, alto_ventana = display.get_size()
        escala = min(ancho_ventana / ANCHO, alto_ventana / ALTO)
        offset_x = (ancho_ventana - int(ANCHO * escala)) // 2
        offset_y = (alto_ventana - int(ALTO * escala)) // 2
        mouse_pos = Metodos.mouse_en_canvas(escala, offset_x, offset_y)

        canvas.blit(fondos[fondo_por_fase[fase]], (0, 0))

        # Cabecera superior de la tablet
        titulo = fuente_grande.render(f"Entrevista - Pregunta {preguntas_hechas + 1} de {total_preguntas}", True, (160, 200, 160))
        canvas.blit(titulo, (SCREEN_X, SCREEN_Y))

        marcador = fuente.render(f"En vivo  {espectadores}", True, (255, 80, 80))
        canvas.blit(marcador, (SCREEN_X + SCREEN_ANCHO - marcador.get_width(), SCREEN_Y))

        marcador_ciudadano = fuente.render(f"Confianza: {puntos_ciudadano}", True, (180, 180, 180))
        canvas.blit(marcador_ciudadano, (SCREEN_X + SCREEN_ANCHO - marcador_ciudadano.get_width(), SCREEN_Y + 22))

        if fase == "pregunta":
            # Instrucción colocada más arriba y separada de las preguntas
            instruccion = fuente.render("Periodista: elige una pregunta", True, (130, 180, 130))
            canvas.blit(instruccion, (SCREEN_X, SCREEN_Y + 45))

            y = SCREEN_Y + 75
            preguntas_visibles = ids_disponibles[:3]  
            for id in preguntas_visibles:
                rect = pygame.Rect(SCREEN_X, y, SCREEN_ANCHO, 65)
                texto_completo = f"{id}. {preguntas[id]}"

                if dibujar_tarjeta_centrada(canvas, rect, texto_completo, fuente, mouse_pos, click):
                    if arbol_preguntas.get(id) is not None:
                        id_pregunta_actual = id
                        ids_disponibles.remove(id)
                        arbol_preguntas.eliminar(id)  
                        fase = "respuesta"

                y += 76

        elif fase == "respuesta":
            texto_pregunta = preguntas[id_pregunta_actual]
            lineas = [texto_pregunta[i:i + 60] for i in range(0, len(texto_pregunta), 60)]
            y_pregunta = SCREEN_Y + 35
            for linea in lineas:
                render_linea = fuente.render(linea, True, (240, 240, 100))
                canvas.blit(render_linea, (SCREEN_X, y_pregunta))
                y_pregunta += 20

            # Instrucción del presidente separada arriba de las opciones
            instruccion = fuente.render("Presidente: elige una respuesta", True, (130, 180, 130))
            canvas.blit(instruccion, (SCREEN_X, y_pregunta + 10))

            opciones_nodo = arbol_respuestas.get(id_pregunta_actual)
            opciones = respuestas[id_pregunta_actual] if opciones_nodo is not None else {}
            claves = ["muy_buena", "regular", "mala"]

            y = y_pregunta + 35
            for clave in claves:
                rect = pygame.Rect(SCREEN_X, y, SCREEN_ANCHO, 65)
                texto_opcion = opciones.get(clave, "")

                if dibujar_tarjeta_centrada(canvas, rect, texto_opcion, fuente, mouse_pos, click):
                    respuesta_elegida = clave
                    fase = "ciudadano"

                y += 76

        elif fase == "ciudadano":
            texto_respuesta = respuestas[id_pregunta_actual][respuesta_elegida]
            lineas = [texto_respuesta[i:i + 60] for i in range(0, len(texto_respuesta), 60)]
            y_resp = SCREEN_Y + 35
            for linea in lineas:
                render_linea = fuente.render(linea, True, (240, 240, 100))
                canvas.blit(render_linea, (SCREEN_X, y_resp))
                y_resp += 20

            # Instrucción del ciudadano separada arriba
            instruccion = fuente.render("Ciudadano: ¿qué tan honesta fue esta respuesta?", True, (130, 180, 130))
            canvas.blit(instruccion, (SCREEN_X, y_resp + 10))

            ancho_btn = (SCREEN_ANCHO - 20) // 3
            y_btns = y_resp + 38

            rect_muy_buena = pygame.Rect(SCREEN_X, y_btns, ancho_btn, 55)
            rect_regular = pygame.Rect(SCREEN_X + ancho_btn + 10, y_btns, ancho_btn, 55)
            rect_mala = pygame.Rect(SCREEN_X + (ancho_btn * 2) + 20, y_btns, ancho_btn, 55)

            if dibujar_tarjeta_centrada(canvas, rect_muy_buena, "Muy buena", fuente, mouse_pos, click):
                if respuesta_elegida == "muy_buena":
                    puntos_ciudadano += 5
                fase = "opinion"
            if dibujar_tarjeta_centrada(canvas, rect_regular, "Regular", fuente, mouse_pos, click):
                if respuesta_elegida == "regular":
                    puntos_ciudadano += 5
                fase = "opinion"
            if dibujar_tarjeta_centrada(canvas, rect_mala, "Mala", fuente, mouse_pos, click):
                if respuesta_elegida == "mala":
                    puntos_ciudadano += 5
                fase = "opinion"

        elif fase == "opinion":
            texto_respuesta = respuestas[id_pregunta_actual][respuesta_elegida]
            lineas = [texto_respuesta[i:i + 60] for i in range(0, len(texto_respuesta), 60)]
            y_resp = SCREEN_Y + 35
            for linea in lineas:
                render_linea = fuente.render(linea, True, (240, 240, 100))
                canvas.blit(render_linea, (SCREEN_X, y_resp))
                y_resp += 20

            # Instrucción del influencer separada arriba
            instruccion = fuente.render("Influencer: da tu opinión sobre esta respuesta", True, (130, 180, 130))
            canvas.blit(instruccion, (SCREEN_X, y_resp + 10))

            ancho_btn = (SCREEN_ANCHO - 20) // 3
            y_btns = y_resp + 38

            rect_positiva = pygame.Rect(SCREEN_X, y_btns, ancho_btn, 55)
            rect_imparcial = pygame.Rect(SCREEN_X + ancho_btn + 10, y_btns, ancho_btn, 55)
            rect_mala_inf = pygame.Rect(SCREEN_X + (ancho_btn * 2) + 20, y_btns, ancho_btn, 55)

            if dibujar_tarjeta_centrada(canvas, rect_positiva, "Positiva", fuente, mouse_pos, click):
                espectadores += 8
                fase = "siguiente"
            if dibujar_tarjeta_centrada(canvas, rect_imparcial, "Imparcial", fuente, mouse_pos, click):
                espectadores += 2
                fase = "siguiente"
            if dibujar_tarjeta_centrada(canvas, rect_mala_inf, "Mala", fuente, mouse_pos, click):
                espectadores -= 6
                fase = "siguiente"

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
    return puntos_influencer, puntos_ciudadano