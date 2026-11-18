"""Ayuda contextual global para The Leader. Instalar con instalar_ayuda.py."""
import inspect
import pygame

CONTENIDOS = {
 'menu': ('GUÍA DEL JUGADOR','THE LEADER','Conoce Ciudad Nova y el uso responsable de las redes sociales.','Selecciona la modalidad de juego y el personaje. En configuración puedes revisar las opciones de accesibilidad, incluido el filtro de daltonismo.'),
 'seleccion': ('SELECCIÓN DE ROL','PERSONAJES','Elige entre Presidente, Periodista, Influencer y Ciudadano.','Cada rol ofrece una perspectiva distinta sobre la información y las decisiones en Ciudad Nova.'),
 'mapa': ('MAPA DE CIUDAD NOVA','RECORRIDO','Consulta la ubicación de la siguiente misión.','Sigue la secuencia de eventos para avanzar en la historia.'),
 'minas': ('CAMPO MINADO','TRANSPORTE DE RECURSOS','Cruza el terreno peligroso para entregar recursos a otras personas.','Coordina los movimientos y evita las minas. Utiliza el escáner con B cuando esté disponible. Las gotas de agua representan tus oportunidades; los controles de movimiento dependen de la modalidad elegida.'),
 'entrevista': ('ENTREVISTA','INFORMACIÓN Y RUMORES','Los rumores difundidos en Civitas requieren una evaluación responsable.','Lee con atención las preguntas y respuestas, contrasta lo que se afirma y toma decisiones informadas. La puntuación de este evento influye en el desenlace.'),
 'oficina': ('ENCUENTRA EL CÓDIGO','INVESTIGACIÓN','Explora la oficina para encontrar una clave de cuatro cifras.','Observa los objetos y las pistas disponibles, relaciónalos y escribe la combinación en el dispositivo correspondiente. La ayuda no revela pistas adicionales ni la solución.'),
 'pozo': ('EVENTO INTRODUCTORIO','CIUDAD NOVA','Sigue la escena y las decisiones de tu personaje.','Lee cada opción antes de decidir. Las decisiones pueden afectar los indicadores de la historia.'),
 'general': ('AYUDA','THE LEADER','Este panel explica las instrucciones de la sección actual.','Pulsa el botón ? o F1 para abrirlo y cerrarlo. El panel no aparece durante las cinemáticas.'),
}
_original_get=None
_original_flip=None
_original_update=None
_instalado=False
_abierto=False
_scroll=0
_boton=pygame.Rect(0,0,42,42)
_panel=pygame.Rect(0,0,300,500)


def _contexto():
    pila=inspect.stack(context=0)
    archivos=[(f.filename.replace('\\','/').lower(),f.function.lower()) for f in pila]
    # el reproductor de vídeo y las escenas de transición nunca muestran el panel.
    for ruta,fn in archivos:
        if fn in ('cinematica_minas','reproducir_escena','remaster_cinematica','reproducirvideo','video'):
            return None
        if 'evento3_oficina.py' in ruta and fn in ('final',):
            return None
    for ruta,fn in archivos:
        if 'evento3_oficina.py' in ruta and fn in ('jugar','eventos','pantalla_computador','dibujar','actualizar'):
            return 'oficina'
        if 'periodista_presidente.py' in ruta and fn == 'entrevista':return 'entrevista'
        if 'evento_2.py' in ruta and fn == 'evento_2':return 'minas'
        if 'evento1_pozo.py' in ruta and fn == 'jugar':return 'pozo'
        if 'mapa.py' in ruta and fn in ('mostrar_mapa','jugar'):return 'mapa'
        if 'seleccionarpj.py' in ruta:return 'seleccion'
        if 'pantalla.py' in ruta and fn == 'main':return 'menu'
    return None


def _fuente(n,negrita=False):
    if not pygame.font.get_init():pygame.font.init()
    return pygame.font.SysFont('timesnewroman',n,bold=negrita,italic=True)


def _lineas(texto,fuente,ancho):
    res=[];actual=''
    for palabra in texto.split():
        intento=(actual+' '+palabra).strip()
        if fuente.size(intento)[0]>ancho and actual:res.append(actual);actual=palabra
        else:actual=intento
    if actual:res.append(actual)
    return res


def _texto(surface,texto,x,y,ancho,color=(227,220,203),tam=15,inter=5):
    fuente=_fuente(tam)
    for linea in _lineas(texto,fuente,ancho):
        surface.blit(fuente.render(linea,True,color),(x,y));y+=tam+inter
    return y


def _pintar():
    pantalla=pygame.display.get_surface()
    if pantalla is None or _contexto() is None:return
    w,h=pantalla.get_size()
    if w<340 or h<300:return
    global _boton,_panel
    _boton=pygame.Rect(w-58,h-58,42,42)
    pygame.draw.circle(pantalla,(20,19,17),_boton.center,23)
    pygame.draw.circle(pantalla,(194,135,43),_boton.center,20)
    pygame.draw.circle(pantalla,(244,198,108),(_boton.centerx-5,_boton.centery-6),8)
    pygame.draw.circle(pantalla,(210,149,56),_boton.center,16)
    q=_fuente(26,True).render('?',True,(28,23,16))
    pantalla.blit(q,q.get_rect(center=_boton.center))
    if not _abierto:return
    ph=min(500,h-20);_panel=pygame.Rect(max(8,w-316),max(10,h-ph-68),300,ph)
    if _panel.bottom>h-8:_panel.bottom=h-8
    pygame.draw.rect(pantalla,(25,24,22),_panel)
    pygame.draw.rect(pantalla,(180,126,49),_panel,2)
    x,y=_panel.topleft
    pygame.draw.rect(pantalla,(41,38,32),(x+2,y+2,296,38))
    _texto(pantalla,'THE LEADER / AYUDA',x+12,y+12,245,(235,184,89),13)
    pygame.draw.line(pantalla,(137,99,44),(x+10,y+42),(x+290,y+42))
    pygame.draw.rect(pantalla,(79,58,30),(x+266,y+7,24,24))
    _texto(pantalla,'X',x+274,y+10,16,(239,226,198),14)
    contexto=_contexto() or 'general';titulo,sub,desc,instr=CONTENIDOS.get(contexto,CONTENIDOS['general'])
    contenido=pygame.Surface((276,750),pygame.SRCALPHA)
    cy=10;cy=_texto(contenido,titulo,5,cy,265,(242,232,209),20,8)+9
    cy=_texto(contenido,sub,5,cy,265,(222,167,74),13)+24
    cy=_texto(contenido,'DESCRIPCIÓN',5,cy,265,(222,167,74),13)+9
    cy=_texto(contenido,desc,5,cy,265,(229,219,199),15)+23
    cy=_texto(contenido,'INSTRUCCIONES',5,cy,265,(222,167,74),13)+9
    cy=_texto(contenido,instr,5,cy,265,(229,219,199),15)+20
    area=pygame.Rect(x+12,y+51,276,max(10,ph-115))
    max_scroll=max(0,cy-area.height+10)
    global _scroll
    _scroll=min(_scroll,max_scroll)
    pantalla.blit(contenido,area.topleft,pygame.Rect(0,_scroll,276,area.height))
    pygame.draw.rect(pantalla,(194,135,43),(x+12,y+ph-51,276,35))
    pygame.draw.line(pantalla,(246,203,118),(x+13,y+ph-50),(x+286,y+ph-50),2)
    pygame.draw.line(pantalla,(105,70,29),(x+13,y+ph-17),(x+286,y+ph-17),2)
    txt=_fuente(15,True).render('ENTENDIDO',True,(28,23,16))
    pantalla.blit(txt,txt.get_rect(center=(x+150,y+ph-34)))


def _eventos():
    global _abierto,_scroll
    eventos=_original_get()
    if _contexto() is None:return eventos
    visibles=[]
    for e in eventos:
        if e.type==pygame.KEYDOWN and e.key==pygame.K_F1:
            _abierto=not _abierto;_scroll=0;continue
        if e.type==pygame.MOUSEBUTTONDOWN and e.button==1:
            if _boton.collidepoint(e.pos):_abierto=not _abierto;_scroll=0;continue
            if _abierto and _panel.collidepoint(e.pos):
                if e.pos[1]<_panel.y+42 and e.pos[0]>_panel.right-40 or e.pos[1]>_panel.bottom-57:
                    _abierto=False
                continue
        if _abierto and e.type==pygame.MOUSEWHEEL:
            _scroll=max(0,_scroll-e.y*30);continue
        if _abierto and e.type in (pygame.KEYDOWN,pygame.TEXTINPUT):continue
        visibles.append(e)
    return visibles


def _flip(*args,**kwargs):
    _pintar()
    return _original_flip(*args,**kwargs)


def _update(*args,**kwargs):
    _pintar()
    # redibujar todo cuando el overlay está visible, incluso si el evento actualiza rectángulos.
    if _contexto() is not None and pygame.display.get_surface() is not None:
        return _original_update()
    return _original_update(*args,**kwargs)


def instalar():
    global _instalado,_original_get,_original_flip,_original_update
    if _instalado:return
    _original_get=pygame.event.get
    _original_flip=pygame.display.flip
    _original_update=pygame.display.update
    pygame.event.get=_eventos
    pygame.display.flip=_flip
    pygame.display.update=_update
    _instalado=True
