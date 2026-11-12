"""Opciones compartidas de The Leader. No modifica sprites ni reglas."""
import json
from pathlib import Path
import pygame
import numpy as np
CONFIG=Path(__file__).resolve().parent/'theleader_settings.json'
DEFAULT={'window':[1280,720], 'filter':'Normal', 'music':0.7}
MODES=('Normal','Protanopia','Deuteranopia','Tritanopia','Alto contraste')
def read():
    try:
        d=DEFAULT.copy();d.update(json.loads(CONFIG.read_text(encoding='utf8')));return d
    except (OSError,ValueError,TypeError):return DEFAULT.copy()
def save(**kwargs):
    d=read();d.update(kwargs);CONFIG.write_text(json.dumps(d,indent=2),encoding='utf8')
def window(size=None, title=None):
    # Tamaño físico persistente; los canvases de cada evento mantienen su resolución lógica.
    size=tuple(size or read()['window'])
    if not pygame.display.get_init():pygame.display.init()
    display=pygame.display.set_mode(size,pygame.RESIZABLE)
    if title:pygame.display.set_caption(title)
    return display
def remember_size(size):
    if size[0]>=640 and size[1]>=400:save(window=list(size))
# Matrices aproximadas para SIMULACIÓN de percepción; el modo compensatorio usa daltonización.
SIM={
 'Protanopia':np.array([[.152,.849,0],[.115,.885,0],[0,.063,.937]],dtype=np.float32),
 'Deuteranopia':np.array([[.367,.633,0],[.280,.720,0],[-.012,.102,.910]],dtype=np.float32),
 'Tritanopia':np.array([[1,0,0],[0,.433,.567],[0,.475,.525]],dtype=np.float32),
}
def filter_surface(surface,mode=None):
    mode=mode or read().get('filter','Normal')
    if mode=='Normal':return surface
    # Aplicación sobre una copia; nunca muta assets originales.
    if not pygame.display.get_init():return surface
    result=surface.copy()
    rgb=pygame.surfarray.pixels3d(result)
    a=rgb.astype(np.float32)
    if mode=='Alto contraste':
        a=np.clip((a-128)*1.35+128,0,255)
    elif mode in SIM:
        sim=np.clip(a@SIM[mode].T,0,255)
        error=a-sim
        # Corrección daltónica suave, redistribuye información perdida a canales visibles.
        a=np.clip(a+np.stack((.0*error[...,0]+.65*error[...,1],
                               .7*error[...,0]+.15*error[...,2],
                               .65*error[...,1]+.25*error[...,0]),axis=-1),0,255)
    rgb[:]=a.astype(np.uint8)
    del rgb
    return result
HELP={
 'minas':('EXPEDIENTE / CAMPO MINADO',[
 'OBJETIVO: alcanzar el final del campo sin pisar minas.',
 'Dos exploradores deben avanzar coordinados.',
 'El terreno oculta minas; observa el camino.',
 'Pulsa B para activar el escáner cuando esté listo.',
 'El escáner revela temporalmente las minas cercanas.',
 'El sensor compartido avisa del peligro próximo,',
 'pero no identifica cuál explorador está amenazado.',
 'Administra tus vidas y espera la recarga del poder.']),
 'entrevista':('EXPEDIENTE / ENTREVISTA',[
 'OBJETIVO: conducir una entrevista y evaluar respuestas.',
 'Lee las preguntas y los diálogos antes de decidir.',
 'Las decisiones modifican la percepción del público.',
 'Observa el chat y los indicadores de la interfaz.',
 'CIVITAS puede intervenir durante la transmisión.',
 'Analiza las consecuencias antes de continuar.']),
 'oficina':('EXPEDIENTE / OFICINA',[
 'OBJETIVO: investigar la información de la ciudad.',
 'Explora los objetos interactivos de la oficina.',
 'Revisa pistas, titulares y comunicaciones.',
 'Relaciona la información y toma decisiones.',
 'Tus acciones influyen en la propagación de rumores.',
 'Utiliza los botones de cada escena para avanzar.'])}
def help_overlay(display,event):
    """Modal F1; usa display físico para funcionar incluso con canvases de 1600x900."""
    if not pygame.display.get_init() or pygame.display.get_surface() is None:return
    title,lines=HELP[event]
    clock=pygame.time.Clock();running=True
    while running:
        for e in pygame.event.get():
            if e.type==pygame.QUIT:
                pygame.event.post(e);return
            if e.type==pygame.KEYDOWN and e.key in (pygame.K_F1,pygame.K_ESCAPE,pygame.K_RETURN):running=False
            if e.type==pygame.MOUSEBUTTONDOWN:running=False
        display=pygame.display.get_surface()
        w,h=display.get_size()
        # Render a logical modal, scale to physical resolution.
        layer=pygame.Surface((1000,680),pygame.SRCALPHA)
        layer.fill((6,8,11,244))
        pygame.draw.rect(layer,(26,24,25),(43,44,914,587),border_radius=8)
        pygame.draw.rect(layer,(171,116,74),(43,44,914,587),3,border_radius=8)
        for x in (62,937):
            for y in (63,613):pygame.draw.circle(layer,(188,144,98),(x,y),5)
        def line(s,y,size=25,color=(232,216,190),bold=False):
            font=pygame.font.SysFont('timesnewroman',size,bold=bold)
            layer.blit(font.render(s,True,color),(85,y))
        line(title,88,35,(226,193,147),True)
        pygame.draw.line(layer,(155,72,52),(82,145),(917,145),3)
        for i,s in enumerate(lines):line(s,182+i*43,25)
        line('F1 / ESC / CLIC  —  CERRAR EXPEDIENTE',573,19,(176,143,116),True)
        dw,dh=min(w,int(h*1000/680)),min(h,int(w*680/1000))
        view=pygame.transform.smoothscale(layer,(dw,dh))
        display.blit(view,((w-dw)//2,(h-dh)//2))
        pygame.display.flip()
        clock.tick(30)
