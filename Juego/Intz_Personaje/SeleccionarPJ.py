# -*- coding: utf-8 -*-
"""Selector de The Leader, estética de la entrevista. Requiere pygame y los PNG incluidos."""
import math
import sys
from pathlib import Path
import pygame
import Metodos
from Intz_Personaje import Intz_Ciudadano, Intz_Influencer, Intz_Periodista, Intz_Presidente
from Red import cliente

ANCHO, ALTO = 800, 600
BASE = Path(__file__).resolve().parent.parent / 'Assets' / 'Interfaz' / 'SelectorEntrevista'
PAPEL=(235,220,198)
ORO=(173,139,106)
ROJO=(143,77,65)
ROLES=[
 {'nombre':'PERIODISTA','clave':'01','lema':'LA VERDAD TIENE UN PRECIO','detalle':'Investiga y revela lo que otros intentan ocultar.'},
 {'nombre':'INFLUENCER','clave':'02','lema':'LA VOZ DE LA MULTITUD','detalle':'Influye en la opinión pública durante la crisis.'},
 {'nombre':'CIUDADANO','clave':'03','lema':'SOBREVIVIR ES RESISTIR','detalle':'Enfrenta el caos desde las calles de la ciudad.'},
 {'nombre':'PRESIDENTE','clave':'04','lema':'EL PESO DEL MANDO','detalle':'Decide el futuro de una sociedad al límite.'},
]
TARJETAS=[pygame.Rect(35+i*187,157,169,288) for i in range(4)]
VOLVER=pygame.Rect(26,525,124,53)
OTRO=pygame.Rect(434,522,154,56)
CONFIRMAR=pygame.Rect(591,522,184,56)

def fuente(tam, negrita=False, cursiva=False):
    # Toda la interfaz utiliza Times New Roman, incluso los botones.
    return pygame.font.SysFont('timesnewroman', tam, bold=negrita, italic=cursiva)

def texto(surf, mensaje, tam, color, centro=None, pos=None, negrita=False, cursiva=False):
    img=fuente(tam,negrita,cursiva).render(str(mensaje),True,color)
    if centro is not None: surf.blit(img,img.get_rect(center=centro))
    elif pos is not None: surf.blit(img,pos)

def coord_canvas(display,pos):
    w,h=display.get_size(); esc=min(w/ANCHO,h/ALTO)
    return ((pos[0]-(w-ANCHO*esc)/2)/esc,(pos[1]-(h-ALTO*esc)/2)/esc)

def dibujar_logo(surf, zona, indice, t, resaltado=False):
    """Los cuatro emblemas originales: prensa, señal, ojo y escudo."""
    cx, cy = zona.center
    pulso = (math.sin(t * 3.3 + indice) + 1) / 2
    pygame.draw.rect(surf, (25, 27, 27), zona)
    # Grabado radial, doble anillo y puntas de la insignia.
    for radio in (61, 55, 47):
        pygame.draw.circle(surf, (75, 69, 56), (cx, cy), radio, 1)
    puntas = []
    for j in range(16):
        ang = -math.pi / 2 + j * math.pi / 8
        r = 67 if j % 2 == 0 else 53
        puntas.append((int(cx + math.cos(ang) * r), int(cy + math.sin(ang) * r)))
    color = (218, 172 + int(28*pulso), 112) if resaltado else (163, 140, 105)
    pygame.draw.polygon(surf, color, puntas, 2)
    pygame.draw.circle(surf, color, (cx, cy), 47, 2)
    pygame.draw.circle(surf, (89, 80, 65), (cx, cy), 42, 1)
    if indice == 0:  # Periodista: periódico
        r = pygame.Rect(cx - 27, cy - 25, 54, 49)
        pygame.draw.rect(surf, color, r, 3)
        pygame.draw.rect(surf, color, (cx-20, cy-17, 17, 17), 2)
        for yy in (-16, -9, -2, 6, 14):
            x1 = cx+3 if yy < 0 else cx-20
            pygame.draw.line(surf, color, (x1,cy+yy), (cx+19,cy+yy), 2)
    elif indice == 1:  # Influencer: antena y ondas
        pygame.draw.circle(surf, color, (cx,cy-6), 6, 2)
        pygame.draw.line(surf, color, (cx,cy+2), (cx,cy+29), 3)
        pygame.draw.line(surf, color, (cx-13,cy+29), (cx+13,cy+29), 3)
        for rad in (18, 30):
            pygame.draw.arc(surf,color,(cx-rad,cy-6-rad,rad*2,rad*2),.55,2.6,2)
            pygame.draw.arc(surf,color,(cx-rad,cy-6-rad,rad*2,rad*2),3.68,5.73,2)
    elif indice == 2:  # Ciudadano: ojo vigilante
        pygame.draw.ellipse(surf,color,(cx-33,cy-16,66,32),3)
        pygame.draw.circle(surf,color,(cx,cy),13,3)
        pygame.draw.circle(surf,color,(cx,cy),5)
        for sign in (-1,1):
            pygame.draw.line(surf,color,(cx-8,cy+sign*25),(cx,cy+sign*33),2)
            pygame.draw.line(surf,color,(cx+8,cy+sign*25),(cx,cy+sign*33),2)
    else:  # Presidente: escudo con corona
        escudo=[(cx,cy-32),(cx+30,cy-21),(cx+26,cy+16),(cx,cy+35),(cx-26,cy+16),(cx-30,cy-21)]
        pygame.draw.polygon(surf,color,escudo,3)
        pygame.draw.polygon(surf,color,[(cx-18,cy-8),(cx-20,cy-22),(cx-7,cy-14),(cx,cy-26),
                                        (cx+7,cy-14),(cx+20,cy-22),(cx+18,cy-8)],2)
        pygame.draw.line(surf,color,(cx-17,cy-3),(cx+17,cy-3),2)
    # Esquinas de la placa
    for x,dx in ((zona.left+8,1),(zona.right-8,-1)):
        for y,dy in ((zona.top+8,1),(zona.bottom-8,-1)):
            pygame.draw.line(surf,color,(x,y),(x+dx*13,y),2)
            pygame.draw.line(surf,color,(x,y),(x,y+dy*13),2)


def abrir_rol(nombre):
    if nombre=='PRESIDENTE': return Intz_Presidente.Presidente()
    if nombre=='CIUDADANO': return Intz_Ciudadano.Ciudadano()
    if nombre=='PERIODISTA': return Intz_Periodista.Periodista()
    return Intz_Influencer.Influencer('Femenino')

def cargar_assets():
    archivos=('fondo_entrevista','panel_inferior','boton_rojo','boton_claro','boton_volver')
    recursos={}
    for nombre in archivos:
        ruta=BASE/(nombre+'.png')
        if not ruta.is_file():
            raise FileNotFoundError(f'Falta asset del selector: {ruta}. Copia la carpeta SelectorEntrevista del ZIP.')
        recursos[nombre]=pygame.image.load(str(ruta)).convert_alpha()
    recursos['fondo_entrevista']=pygame.transform.smoothscale(recursos['fondo_entrevista'],(ANCHO,ALTO))
    return recursos

def imagen_ajustada(surf, img, rect, alpha=255):
    # Los PNG originales tienen bordes propios; se escalan al rectángulo indicado.
    nueva=pygame.transform.smoothscale(img,rect.size)
    if alpha!=255: nueva.set_alpha(alpha)
    surf.blit(nueva,rect.topleft)

def placa(surf,rect,color=(20,17,17,225),borde=ORO):
    capa=pygame.Surface(rect.size,pygame.SRCALPHA)
    pygame.draw.rect(capa,color,capa.get_rect(),border_radius=4)
    surf.blit(capa,rect.topleft)
    pygame.draw.rect(surf,borde,rect,1,border_radius=4)
    for x in (rect.left+7,rect.right-7):
        for y in (rect.top+7,rect.bottom-7):
            pygame.draw.circle(surf,(137,103,64),(x,y),2)

def boton(surf,recursos,rect,nombre,mouse,tipo='claro'):
    hover=rect.collidepoint(mouse)
    archivo={'claro':'boton_claro','rojo':'boton_rojo','volver':'boton_volver'}[tipo]
    if hover:
        sombra=pygame.Surface((rect.w+8,rect.h+8),pygame.SRCALPHA)
        pygame.draw.rect(sombra,(234,169,110,32),sombra.get_rect(),border_radius=7)
        surf.blit(sombra,(rect.x-4,rect.y-4))
    imagen_ajustada(surf,recursos[archivo],rect)
    color=(255,236,191) if tipo!='claro' else (46,31,24)
    
    # El botón de regreso usa exclusivamente el icono de flecha del PNG.
    if tipo != 'volver':
        texto(surf,nombre,16,color,rect.center,negrita=True,cursiva=True)
    if hover: pygame.draw.rect(surf,(215,177,133),rect,2,border_radius=5)

def tarjeta(surf,recursos,indice,rect,mouse,t,seleccionado,ocupado_por):
    hover=rect.collidepoint(mouse)
    activo=(hover or seleccionado==indice) and not ocupado_por
    marco=pygame.Rect(rect.x,rect.y,rect.w,rect.h)
    placa(surf,marco,(25,23,23,219),(211,165,118) if activo else (122,101,83))
    pygame.draw.rect(surf,(74,45,43),(rect.x+5,rect.y+6,rect.w-10,29))
    texto(surf,'EXPEDIENTE '+ROLES[indice]['clave'],13,PAPEL,(rect.centerx,rect.y+20),negrita=True)
    zona=pygame.Rect(rect.x+12,rect.y+47,rect.w-24,159)
    dibujar_logo(surf,zona,indice,t,activo)
    pygame.draw.rect(surf,(135,96,62),zona,1)
    pygame.draw.line(surf,(139,91,52),(rect.x+12,rect.y+217),(rect.right-12,rect.y+217),1)
    texto(surf,ROLES[indice]['nombre'],16,PAPEL,(rect.centerx,rect.y+239),negrita=True)
    texto(surf,'REGISTRO '+ROLES[indice]['clave']+' · CIVITAS',11,(170,130,91),(rect.centerx,rect.y+264),cursiva=True)
    if activo:
        brillo=pygame.Surface(rect.size,pygame.SRCALPHA)
        pygame.draw.rect(brillo,(232,179,116,18),brillo.get_rect(),border_radius=4)
        surf.blit(brillo,rect.topleft)
        pygame.draw.rect(surf,(215,178,133),rect,2,border_radius=4)
    if ocupado_por:
        capa=pygame.Surface(rect.size,pygame.SRCALPHA);capa.fill((5,5,5,191));surf.blit(capa,rect.topleft)
        texto(surf,'EN USO',22,(222,83,63),(rect.centerx,rect.centery),negrita=True)
        texto(surf,str(ocupado_por)[:18],12,PAPEL,(rect.centerx,rect.centery+27))

def SeleccionarPJ():
    pygame.init()
    display,canvas=Metodos.crear_ventana(ANCHO,ALTO,'The Leader')
    recursos=cargar_assets()
    reloj=pygame.time.Clock()
    red=cliente.conectar()
    if red is not None: red.soltar()
    seleccionado=None
    aviso=''; aviso_hasta=0.; tiempo=0.

    def ocupado(nombre):
        return red.ocupado_por_otro(nombre) if red is not None else None

    while True:
        tiempo+=min(reloj.tick(60)/1000.,0.1)
        mouse=coord_canvas(display,pygame.mouse.get_pos())
        accion=None
        for ev in pygame.event.get():
            if ev.type==pygame.QUIT:
                pygame.quit();sys.exit()
            if ev.type==pygame.VIDEORESIZE:
                display=pygame.display.set_mode((max(320,ev.w),max(240,ev.h)),pygame.RESIZABLE)
            elif ev.type==pygame.KEYDOWN:
                if ev.key==pygame.K_ESCAPE:
                    if seleccionado is not None: seleccionado=None
                    else: pygame.quit();sys.exit()
                elif ev.key==pygame.K_BACKSPACE: seleccionado=None
                elif ev.key in (pygame.K_RETURN,pygame.K_KP_ENTER) and seleccionado is not None:
                    accion=seleccionado
            elif ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:
                punto=coord_canvas(display,ev.pos)
                if VOLVER.collidepoint(punto):
                    if seleccionado is not None: seleccionado=None
                    else: pygame.quit();sys.exit()
                elif seleccionado is not None and OTRO.collidepoint(punto): seleccionado=None
                elif seleccionado is not None and CONFIRMAR.collidepoint(punto): accion=seleccionado
                else:
                    for i,r in enumerate(TARJETAS):
                        if r.collidepoint(punto):
                            quien=ocupado(ROLES[i]['nombre'])
                            if quien:
                                aviso=f'{ROLES[i]["nombre"]} EN USO POR {quien}';aviso_hasta=tiempo+2.5
                            else: seleccionado=i
                            break
        if accion is not None:
            nombre=ROLES[accion]['nombre']
            if red is not None and red.conectado:
                ok,quien=red.elegir(nombre)
                if not ok:
                    aviso=f'{nombre} EN USO POR {quien}';aviso_hasta=tiempo+2.5
                    seleccionado=None;accion=None
            if accion is not None: return abrir_rol(nombre)

        canvas.blit(recursos['fondo_entrevista'],(0,0))
        # Oscurece la escena para que los expedientes sean legibles.
        velo=pygame.Surface((ANCHO,ALTO),pygame.SRCALPHA)
        velo.fill((16,12,12,82));canvas.blit(velo,(0,0))
        placa(canvas,pygame.Rect(20,17,760,120),(22,19,19,198),(154,120,93))
        texto(canvas,'THE LEADER',36,(242,211,166),(400,52),negrita=True)
        texto(canvas,'Archivo de identidades · Selección de personaje',15,(207,172,139),(400,88),cursiva=True)
        texto(canvas,'Civitas · Archivo reservado',11,(185,148,125),pos=(37,111))
        if red is not None:
            estado='EN LINEA' if red.conectado else 'SIN CONEXION'
            texto(canvas,'Conexión: '+estado,11,(140,194,138) if red.conectado else (208,112,91),pos=(672,111))
        for i,r in enumerate(TARJETAS):
            tarjeta(canvas,recursos,i,r,mouse,tiempo,seleccionado,ocupado(ROLES[i]['nombre']))
        imagen_ajustada(canvas,recursos['panel_inferior'],pygame.Rect(18,464,764,127))
        boton(canvas,recursos,VOLVER,'',mouse,'volver')
        if seleccionado is None:
            texto(canvas,'Selecciona un expediente para conocer su historia',15,PAPEL,(470,542),cursiva=True)
        else:
            rol=ROLES[seleccionado]
            texto(canvas,rol['nombre']+' · Expediente '+rol['clave'],15,PAPEL,pos=(168,509),negrita=True)
            texto(canvas,rol['detalle'][:38],12,(212,182,153),pos=(168,535),cursiva=True)
            boton(canvas,recursos,OTRO,'ELEGIR OTRO',mouse,'claro')
            boton(canvas,recursos,CONFIRMAR,'CONFIRMAR',mouse,'rojo')
        if aviso and tiempo<aviso_hasta:
            placa(canvas,pygame.Rect(188,447,426,31),(72,39,38,230),(212,77,62))
            texto(canvas,aviso,13,PAPEL,(401,463),negrita=True)
        Metodos.mostrar_canvas(display,canvas)
        pygame.display.flip()
