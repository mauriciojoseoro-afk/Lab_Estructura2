import pygame
import sys

from Intz_Personaje import SeleccionarPJ

pygame.init()

fondo_original = pygame.image.load("Assets/Interfaz/Juego.png")
ancho_original, alto_original = fondo_original.get_size()

ANCHO = 900
ALTO = int(ANCHO * alto_original / ancho_original)

display = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("My Game")

fondo = pygame.transform.smoothscale(fondo_original.convert(), (ANCHO, ALTO))

frac_centro_x = 0.5
frac_centro_y = 0.80
frac_ancho = 0.27
frac_alto = 0.12

boton_ancho = int(ANCHO * frac_ancho)
boton_alto = int(ALTO * frac_alto)
centro_x = int(ANCHO * frac_centro_x)
centro_y = int(ALTO * frac_centro_y)
boton_rect = pygame.Rect(centro_x - boton_ancho // 2, centro_y - boton_alto // 2, boton_ancho, boton_alto)
tamano_salir = int(ANCHO * 0.08)
boton_salir = pygame.Rect(int(ANCHO * 0.04), int(ANCHO * 0.05), tamano_salir, tamano_salir)

running = True
while running:
    mouse_pos = pygame.mouse.get_pos()

    for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                if boton_rect.collidepoint(event.pos):
                    SeleccionarPJ.SeleccionarPJ()
                if boton_salir.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()

    display.blit(fondo, (0, 0))

    pygame.display.update()

pygame.quit()