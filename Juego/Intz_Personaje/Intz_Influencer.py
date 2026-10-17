import pygame
from pathlib import Path
import sys
import Metodos
from Eventos import Periodista_Presidente


def Influencer(genero):
    pygame.init()
    
    ANCHO, ALTO = 900, 600 
    display, canvas = Metodos.crear_ventana(ANCHO, ALTO, f"Influencer - {genero}")
    reloj = pygame.time.Clock()
    
    ruta_assets = Path(__file__).parent.parent / "Assets" / "Interfaz"

    if genero == "Masculino":
        ruta_imagen = ruta_assets / "Influencer_M.png"
        ruta_detalles = ruta_assets / "Detalles_M.png"
    elif genero == "Femenino":
        ruta_imagen = ruta_assets / "Influencer_F.png"
        ruta_detalles = ruta_assets / "Detalles_F.png"
    else:
        raise ValueError(f"Género de influencer no válido: {genero}")
        
    imagen_fondo = pygame.image.load(str(ruta_imagen)).convert()
    imagen_fondo = pygame.transform.scale(imagen_fondo, (ANCHO, ALTO))
    
    imagen_detalles = None
    if ruta_detalles.exists():
        imagen_detalles = pygame.image.load(str(ruta_detalles)).convert()
        imagen_detalles = pygame.transform.scale(imagen_detalles, (ANCHO, ALTO))

    boton_detalles = pygame.Rect(90, 190, 200, 60)
    boton_evento = pygame.Rect(600, 180, 200, 60)
    boton_regresar_principal = pygame.Rect(90, 320, 200, 60)
    
    # Boton exclusivo de detalles
    boton_regresar_detalles = pygame.Rect(350, 500, 200, 60)

    en_detalles = False

    running = True
    while running:
        click = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()
            if event.type == pygame.VIDEORESIZE:
                display = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                click = True

        ancho_ventana, alto_ventana = display.get_size()
        escala = min(ancho_ventana / ANCHO, alto_ventana / ALTO)
        offset_x = (ancho_ventana - int(ANCHO * escala)) // 2
        offset_y = (alto_ventana - int(ALTO * escala)) // 2
        mouse_pos = Metodos.mouse_en_canvas(escala, offset_x, offset_y)

        # Si el usuario abrio los detalles
        if en_detalles:
            if imagen_detalles:
                canvas.blit(imagen_detalles, (0, 0))
            else:
                canvas.fill((30, 30, 30))
            
            if Metodos.boton_inv(canvas, boton_regresar_detalles, mouse_pos, click):
                en_detalles = False

        else:
            canvas.blit(imagen_fondo, (0, 0))

            # 1. Botón Detalles
            if Metodos.boton_inv(canvas, boton_detalles, mouse_pos, click):
                en_detalles = True

            if Metodos.boton_inv(canvas, boton_evento, mouse_pos, click):
                Periodista_Presidente.Entrevista()

            if Metodos.boton_inv(canvas, boton_regresar_principal, mouse_pos, click):
                running = False

        Metodos.mostrar_canvas(display, canvas)
        pygame.display.update()
        reloj.tick(30)