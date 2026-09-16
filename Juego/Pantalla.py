import pygame


from Intz_Personaje import SeleccionarPJ




pygame.init()

display = pygame.display.set_mode((800, 600))
pygame.display.set_caption("My Game")

fondo = pygame.image.load("Juego/Assets/Interfaz/Juego.png").convert()

#Boton
boton_rect = pygame.Rect(50, 300, 200, 60)
color_normal = (70, 130, 180)
color_hover = (100, 160, 210)
fuente = pygame.font.SysFont(None, 32)

running = True
while running:
    mouse_pos = pygame.mouse.get_pos()  

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # detectar clic sobre el botón
        if event.type == pygame.MOUSEBUTTONDOWN:
            if boton_rect.collidepoint(event.pos):
                SeleccionarPJ.SeleccionarPJ() 

    display.blit(fondo, (0, 0))

    
    color_actual = color_hover if boton_rect.collidepoint(mouse_pos) else color_normal
    pygame.draw.rect(display, color_actual, boton_rect, border_radius=8)
    texto = fuente.render("Seleccionar Personaje", True, (255, 255, 255))
    texto_rect = texto.get_rect(center=boton_rect.center)
    display.blit(texto, texto_rect)

    pygame.display.update()

pygame.quit()