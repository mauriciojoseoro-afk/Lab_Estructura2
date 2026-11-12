"""The Leader: menú transparente; usa el fondo con textos ya incorporados."""
import sys
from pathlib import Path
import cv2
import pygame
import Historia
import Accesibilidad
from Red import cliente
from Red import servidor as red_servidor

BASE=Path(__file__).resolve().parent
VIDEO=BASE/'Assets'/'Interfaz'/'Juego.mp4'
W,H=900,600
# Regiones de los textos ya dibujados en el vídeo (coords del canvas 900x600).
BUTTONS={
 'JUGAR':pygame.Rect(91,275,300,50),
 'UNIRSE':pygame.Rect(65,327,325,47),
 'INSTRUCCIONES':pygame.Rect(80,372,280,39),
 'CONFIGURACIÓN':pygame.Rect(90,416,275,39),
 'SALIR':pygame.Rect(140,457,175,39),
 'CRÉDITOS':pygame.Rect(400,552,110,35),
}
# Ventanas de CREAR PARTIDA / UNIRSE A PARTIDA (coords del canvas 900x600).
SOLO=pygame.Rect(160,195,580,100)
GRUPO=pygame.Rect(160,315,580,100)
COMENZAR=pygame.Rect(300,420,300,54)
CAMPO_IP=pygame.Rect(160,252,580,58)
ENTRAR=pygame.Rect(300,420,300,54)
def a_canvas(display,pos):
 ww,hh=display.get_size();scale=min(ww/W,hh/H)
 return ((pos[0]-(ww-W*scale)/2)/scale,(pos[1]-(hh-H*scale)/2)/scale)
def jugar():
 Historia.Historia()
 if not pygame.get_init():pygame.init()
 return Accesibilidad.window(title='The Leader')
def label(s,msg,x,y,size=22,color=(238,222,197),bold=False,italic=False):
 f=pygame.font.SysFont('timesnewroman',size,bold=bold,italic=italic)
 s.blit(f.render(msg,True,color),(x,y))
def modal(s,page):
 cover=pygame.Surface((W,H),pygame.SRCALPHA);cover.fill((5,7,10,208));s.blit(cover,(0,0))
 r=pygame.Rect(105,65,690,475)
 pygame.draw.rect(s,(23,22,25),r,border_radius=6)
 pygame.draw.rect(s,(175,130,91),r,3,border_radius=6)
 label(s,page,140,104,34,bold=True)
 pygame.draw.line(s,(163,80,59),(138,155),(760,155),2)
 if page=='INSTRUCCIONES':
  for i,line in enumerate(('Cuatro perspectivas. Una ciudad.','Completa las misiones y toma decisiones.',
      'CAMPO MINADO: B activa el escáner cuando esté listo.',
      'ENTREVISTA: analiza preguntas y respuestas.',
      'OFICINA: explora pistas y reconstruye los hechos.',
      'F1 abre el expediente de ayuda dentro de cada evento.')):
   label(s,line,143,189+i*42,21)
 elif page=='CONFIGURACIÓN':
  label(s,'FILTRO DE COLOR',144,185,25,bold=True)
  for i,name in enumerate(Accesibilidad.MODES):
   r=pygame.Rect(142,227+i*43,380,37)
   selected=Accesibilidad.read()['filter']==name
   pygame.draw.rect(s,(91,47,39) if selected else (43,40,41),r,border_radius=3)
   pygame.draw.rect(s,(195,142,93) if selected else (91,81,73),r,1)
   label(s,name,156,231+i*43,22)
  label(s,'El filtro se aplica a las escenas compatibles.',143,454,18)
 elif page=='CRÉDITOS':
  for i,line in enumerate(('THE LEADER','Videojuego narrativo sobre liderazgo y confianza',
      'EDITAR: nombres de los integrantes del equipo')):
   label(s,line,147,200+i*62,25)
 label(s,'ESC — VOLVER',142,501,20,(203,158,110),italic=True)
def boton(s,r,titulo,sub=None,hover=False):
 pygame.draw.rect(s,(91,47,39) if hover else (43,40,41),r,border_radius=4)
 pygame.draw.rect(s,(195,142,93) if hover else (91,81,73),r,2,border_radius=4)
 t=pygame.font.SysFont('timesnewroman',28,bold=True).render(titulo,True,(238,222,197))
 if sub:
  s.blit(t,(r.x+26,r.y+16));label(s,sub,r.x+26,r.y+58,19,(203,178,140))
 else:s.blit(t,t.get_rect(center=r.center))

def main():
 pygame.init();display=Accesibilidad.window(title='The Leader')
 canvas=pygame.Surface((W,H));clock=pygame.time.Clock()
 video=cv2.VideoCapture(str(VIDEO))
 if not video.isOpened():raise FileNotFoundError('No se pudo abrir '+str(VIDEO))
 fps=video.get(cv2.CAP_PROP_FPS) or 30
 frame_time=0;last=None;page=None;running=True
 ip='';ip_host='';aviso='';unirse=False
 while running:
  dt=min(clock.tick(60)/1000,.08);frame_time+=dt
  for e in pygame.event.get():
   if e.type==pygame.QUIT:running=False
   if e.type==pygame.VIDEORESIZE:
    Accesibilidad.remember_size((e.w,e.h));display=Accesibilidad.window((e.w,e.h))
   if e.type==pygame.KEYDOWN and e.key==pygame.K_ESCAPE:page=None
   elif e.type==pygame.KEYDOWN and page=='UNIRSE':
    if e.key in (pygame.K_RETURN,pygame.K_KP_ENTER):unirse=True
    elif e.key==pygame.K_BACKSPACE:ip=ip[:-1]
    elif e.unicode and (e.unicode.isalnum() or e.unicode in '.-') and len(ip)<40:ip+=e.unicode
   if e.type==pygame.MOUSEBUTTONDOWN and e.button==1:
    ww,hh=display.get_size();scale=min(ww/W,hh/H)
    ox=(ww-W*scale)/2;oy=(hh-H*scale)/2
    pt=((e.pos[0]-ox)/scale,(e.pos[1]-oy)/scale)
    if page=='CONFIGURACIÓN':
     for i,name in enumerate(Accesibilidad.MODES):
      if pygame.Rect(142,227+i*43,380,37).collidepoint(pt):Accesibilidad.save(filter=name)
    elif page=='CREAR':
     if SOLO.collidepoint(pt):
      cliente.modo_solo();page=None;display=jugar()
     elif GRUPO.collidepoint(pt):
      ok,ip_host=red_servidor.en_segundo_plano()
      if ok:cliente.usar_servidor('127.0.0.1');page='ANFITRION'
      else:aviso='No se pudo abrir la partida: el puerto está ocupado.'
    elif page=='ANFITRION':
     if COMENZAR.collidepoint(pt):page=None;display=jugar()
    elif page=='UNIRSE':
     if ENTRAR.collidepoint(pt):unirse=True
    elif not page:
     for name,rect in BUTTONS.items():
      if rect.collidepoint(pt):
       if name=='SALIR':running=False
       elif name=='JUGAR':page='CREAR';aviso=''   # el botón dice CREAR PARTIDA
       elif name=='UNIRSE':page='UNIRSE';aviso=''
       else:page=name
       break
  if not running:break
  if unirse:
   unirse=False;destino=ip.strip() or '127.0.0.1'
   cliente.usar_servidor(destino)
   if cliente.conectar(espera=2.0) is not None:page=None;display=jugar()
   else:aviso=f'No se encontró ninguna partida en {destino}.'
  if last is None or frame_time>=1/max(1,fps):
   frame_time=0
   ok,frame=video.read()
   if not ok:
    video.set(cv2.CAP_PROP_POS_FRAMES,0);ok,frame=video.read()
   if ok:
    # INTER_AREA al reducir, INTER_CUBIC al ampliar; conserva detalles originales.
    interpolation=cv2.INTER_AREA if frame.shape[1]>W else cv2.INTER_CUBIC
    frame=cv2.resize(frame,(W,H),interpolation=interpolation)
    frame=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
    last=pygame.image.frombuffer(frame.tobytes(),(W,H),'RGB').convert()
  if last:canvas.blit(last,(0,0))
  else:canvas.fill((27,25,25))
  if page:
   m=a_canvas(display,pygame.mouse.get_pos())
   if page=='CREAR':
    modal(canvas,'CREAR PARTIDA')
    boton(canvas,SOLO,'JUGAR SOLO','Tú solo, sin servidor ni esperas.',SOLO.collidepoint(m))
    boton(canvas,GRUPO,'CON COMPAÑÍA','Abres la partida y tus compañeros se unen a ti.',GRUPO.collidepoint(m))
    if aviso:label(canvas,aviso,160,440,19,(226,120,95))
   elif page=='ANFITRION':
    modal(canvas,'PARTIDA CREADA')
    label(canvas,'Tus compañeros deben pulsar UNIRSE A PARTIDA',150,185,23)
    label(canvas,'y escribir esta dirección:',150,218,23)
    t=pygame.font.SysFont('timesnewroman',54,bold=True).render(ip_host,True,(226,178,104))
    canvas.blit(t,t.get_rect(center=(W//2,300)))
    label(canvas,'(si juegan en este mismo PC: 127.0.0.1)',150,350,19,(170,160,145),italic=True)
    boton(canvas,COMENZAR,'COMENZAR',hover=COMENZAR.collidepoint(m))
   elif page=='UNIRSE':
    modal(canvas,'UNIRSE A PARTIDA')
    label(canvas,'Escribe la dirección que le aparece al anfitrión:',150,195,23)
    pygame.draw.rect(canvas,(14,13,15),CAMPO_IP,border_radius=4)
    pygame.draw.rect(canvas,(195,142,93),CAMPO_IP,2,border_radius=4)
    cursor='|' if int(pygame.time.get_ticks()/500)%2 else ''
    if ip:label(canvas,ip+cursor,CAMPO_IP.x+18,CAMPO_IP.y+12,30)
    else:label(canvas,'127.0.0.1'+cursor,CAMPO_IP.x+18,CAMPO_IP.y+12,30,(110,104,98))
    if aviso:label(canvas,aviso,160,335,19,(226,120,95))
    else:label(canvas,'Enter o ENTRAR para unirte.',160,335,19,(170,160,145),italic=True)
    boton(canvas,ENTRAR,'ENTRAR',hover=ENTRAR.collidepoint(m))
   else:modal(canvas,page)
  view=Accesibilidad.filter_surface(canvas)
  dw,dh=display.get_size();scale=min(dw/W,dh/H)
  nw,nh=max(1,round(W*scale)),max(1,round(H*scale))
  display.fill((0,0,0))
  display.blit(pygame.transform.smoothscale(view,(nw,nh)),((dw-nw)//2,(dh-nh)//2))
  pygame.display.flip()
 video.release();pygame.quit()
if __name__=='__main__':main()
