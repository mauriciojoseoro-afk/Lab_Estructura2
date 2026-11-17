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
SOLO=pygame.Rect(160,176,580,86)
LOCAL=pygame.Rect(160,272,580,86)
RED=pygame.Rect(160,368,580,86)
CANTIDADES={n:pygame.Rect(190+(n-2)*185,232,150,110) for n in (2,3,4)}
INICIAR=pygame.Rect(300,412,300,62)
CAMPO_IP=pygame.Rect(160,252,580,58)
ENTRAR=pygame.Rect(300,412,300,62)
# ESTÉTICA DEL PROYECTO: marcos industriales de las escenas (HistoriaIndustrial / CronicaUI)
INTERFAZ=BASE/'Assets'/'Interfaz'
PAPEL=(236,229,211);AMBAR=(214,180,112);OXIDO=(166,133,86);VIVO=(184,73,66)
AGUA=(169,188,171);APAGADO=(182,175,160);TENUE=(120,114,104)
_IMG={}
def _img(nombre):
 if nombre not in _IMG:
  try:_IMG[nombre]=pygame.image.load(str(INTERFAZ/nombre)).convert_alpha()
  except Exception:_IMG[nombre]=None
 return _IMG[nombre]
def marco(s,nombre,r,b):
 """Estira un marco PNG a cualquier tamaño sin deformar sus esquinas (9-slice). b=(izq,arr,der,aba)."""
 img=_img(nombre)
 if img is None:return False
 w,h=img.get_size();l,t,d,a=b
 xs,ys=(0,l,w-d,w),(0,t,h-a,h)
 xd,yd=(r.x,r.x+l,r.right-d,r.right),(r.y,r.y+t,r.bottom-a,r.bottom)
 for i in range(3):
  for j in range(3):
   sw,sh=xs[i+1]-xs[i],ys[j+1]-ys[j];dw,dh=xd[i+1]-xd[i],yd[j+1]-yd[j]
   if sw<=0 or sh<=0 or dw<=0 or dh<=0:continue
   pieza=img.subsurface((xs[i],ys[j],sw,sh))
   s.blit(pieza if (sw,sh)==(dw,dh) else pygame.transform.smoothscale(pieza,(dw,dh)),(xd[i],yd[j]))
 return True
def rotulo(s,msg,x,y,color=OXIDO,size=14):
 """Texto pequeño en mayúsculas espaciadas, como las etiquetas de los expedientes."""
 label(s,' '.join(msg.upper()).replace('   ','     '),x,y,size,color,bold=True)
def a_canvas(display,pos):
 ww,hh=display.get_size();scale=min(ww/W,hh/H)
 return ((pos[0]-(ww-W*scale)/2)/scale,(pos[1]-(hh-H*scale)/2)/scale)
# MOUSE SOBRE EL VIDEO A PANTALLA COMPLETA -> coordenadas viejas del canvas 900x600
VIDEO_INFO={'w':1662,'h':1246,'barra':96}
CREDITOS_PANTALLA=pygame.Rect(0,0,0,0)   # se ubica al dibujar, abajo al centro
def a_video(display,pos,last):
 if last is None:return a_canvas(display,pos)
 dw,dh=display.get_size();esc=max(dw/last.get_width(),dh/last.get_height())
 ox=(dw-last.get_width()*esc)/2;oy=(dh-last.get_height()*esc)/2
 k=(VIDEO_INFO['h']-2*VIDEO_INFO['barra'])/last.get_height()
 fx=(pos[0]-ox)/esc*k;fy=(pos[1]-oy)/esc*k+VIDEO_INFO['barra']
 return (fx*W/VIDEO_INFO['w'],fy*H/VIDEO_INFO['h'])
def jugar():
 Historia.Historia()
 if not pygame.get_init():pygame.init()
 return Accesibilidad.window(title='The Leader')
def label(s,msg,x,y,size=22,color=(238,222,197),bold=False,italic=False):
 f=pygame.font.SysFont('timesnewroman',size,bold=bold,italic=italic)
 s.blit(f.render(msg,True,color),(x,y))
def modal(s,page):
 r=pygame.Rect(105,65,690,475)
 if not marco(s,'HistoriaIndustrial/panel_narracion.png',r,(46,46,118,46)):
  pygame.draw.rect(s,(23,22,25),r,border_radius=6)
  pygame.draw.rect(s,(175,130,91),r,3,border_radius=6)
 rotulo(s,'The Leader · expediente',142,90,OXIDO,12)
 label(s,page,140,108,34,PAPEL,bold=True)
 pygame.draw.line(s,OXIDO,(138,156),(760,156),1)
 pygame.draw.rect(s,VIVO,(138,155,64,3))
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
      'Isaac Gonzalez · Laura Lanchero','Mauricio Orozco · Karla Paredes')):
   label(s,line,147,200+i*62,25)
 rotulo(s,'Esc · volver',142,503,AMBAR,13)
def boton(s,r,titulo,sub=None,hover=False,etiqueta=None,activo=True):
 """Tarjeta de decisión, igual que las opciones de la entrevista."""
 b=min(34,r.h//2-1)
 nombre='CronicaUI/decision_hover.png' if hover and activo else 'CronicaUI/decision.png'
 if not marco(s,nombre,r,(b,b,b,b)):
  pygame.draw.rect(s,(91,47,39) if hover else (43,40,41),r,border_radius=4)
  pygame.draw.rect(s,(195,142,93) if hover else (91,81,73),r,2,border_radius=4)
 color=PAPEL if activo else TENUE
 t=pygame.font.SysFont('timesnewroman',26 if sub else 24,bold=True).render(titulo,True,color)
 if sub:
  s.blit(t,(r.x+34,r.y+13));label(s,sub,r.x+34,r.bottom-35,18,APAGADO if activo else TENUE)
 elif titulo:s.blit(t,t.get_rect(center=r.center))
 if etiqueta:
  e=pygame.font.SysFont('timesnewroman',30,bold=True).render(etiqueta,True,AMBAR if hover else OXIDO)
  s.blit(e,e.get_rect(midright=(r.right-34,r.centery)))
def lista_sala(s,red,y):
 """Jugadores conectados a la sala, con el anfitrión marcado."""
 jugadores=red.jugadores if red is not None else []
 rotulo(s,f'Jugadores en la sala · {len(jugadores)}',150,y,OXIDO,13)
 for k,j in enumerate(jugadores[:8]):
  col,fila=divmod(k,4)
  fila_r=pygame.Rect(150+col*300,y+26+fila*31,285,27)
  pygame.draw.rect(s,(31,29,29),fila_r)
  pygame.draw.rect(s,VIVO if j.get('anfitrion') else OXIDO,(fila_r.x,fila_r.y,4,fila_r.h))
  label(s,j.get('nombre','?'),fila_r.x+14,fila_r.y+3,19,PAPEL)
  if j.get('anfitrion'):
   tag=pygame.font.SysFont('timesnewroman',12,bold=True).render('ANFITRIÓN',True,PAPEL)
   caja=tag.get_rect(midright=(fila_r.right-8,fila_r.centery)).inflate(10,4)
   pygame.draw.rect(s,VIVO,caja);s.blit(tag,tag.get_rect(center=caja.center))

def main():
 pygame.init();display=Accesibilidad.window(title='The Leader')
 canvas=pygame.Surface((W,H),pygame.SRCALPHA);clock=pygame.time.Clock()
 video=cv2.VideoCapture(str(VIDEO))
 if not video.isOpened():raise FileNotFoundError('No se pudo abrir '+str(VIDEO))
 fps=video.get(cv2.CAP_PROP_FPS) or 30
 frame_time=0;last=None;page=None;running=True
 ip='';ip_host='';aviso='';unirse=False;sala=None
 while running:
  dt=min(clock.tick(60)/1000,.08);frame_time+=dt
  for e in pygame.event.get():
   if e.type==pygame.QUIT:running=False
   if e.type==pygame.VIDEORESIZE:
    Accesibilidad.remember_size((e.w,e.h));display=Accesibilidad.window((e.w,e.h))
   if e.type==pygame.KEYDOWN and e.key==pygame.K_ESCAPE:
    if page in ('SALA','SALA_HOST'):cliente.salir();sala=None
    page='CREAR' if page=='LOCAL' else None
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
     elif LOCAL.collidepoint(pt):page='LOCAL'
     elif RED.collidepoint(pt):
      ok,ip_host=red_servidor.en_segundo_plano()
      if ok:
       cliente.usar_servidor('127.0.0.1')
       sala=cliente.conectar(espera=2.0,anfitrion=True)
      if ok and sala is not None:page='SALA_HOST'
      else:aviso='No se pudo abrir la partida: el puerto está ocupado.'
    elif page=='LOCAL':
     for n,r in CANTIDADES.items():
      if r.collidepoint(pt):
       cliente.modo_local(n);page=None;display=jugar();break
    elif page=='SALA_HOST':
     if INICIAR.collidepoint(pt) and sala is not None and sala.es_anfitrion():
      sala.iniciar_partida();page=None;display=jugar()
    elif page=='UNIRSE':
     if ENTRAR.collidepoint(pt):unirse=True
    elif not page:
     pt_video=a_video(display,e.pos,last)
     if CREDITOS_PANTALLA.collidepoint(e.pos):page='CRÉDITOS'
     for name,rect in BUTTONS.items():
      if rect.collidepoint(pt_video):
       if name=='SALIR':running=False
       elif name=='JUGAR':page='CREAR';aviso=''   # el botón dice CREAR PARTIDA
       elif name=='UNIRSE':page='UNIRSE';aviso=''
       else:page=name
       break
  if not running:break
  if unirse:
   unirse=False;destino=ip.strip() or '127.0.0.1'
   cliente.usar_servidor(destino)
   sala=cliente.conectar(espera=2.0)
   if sala is not None:page='SALA';ip_host=destino
   else:aviso=f'No se encontró ninguna partida en {destino}.'
  # SALA DE ESPERA: los que se unen empiezan cuando el anfitrión pulsa INICIAR.
  if page in ('SALA','SALA_HOST') and sala is not None:
   if sala.rechazo:
    aviso=sala.rechazo+'.';cliente.salir();sala=None;page='UNIRSE'
   elif not sala.conectado:
    aviso='El anfitrión cerró la partida.';cliente.salir();sala=None;page='UNIRSE'
   elif page=='SALA' and sala.bienvenido and sala.iniciada:
    page=None;display=jugar()
  if last is None or frame_time>=1/max(1,fps):
   frame_time=0
   ok,frame=video.read()
   if not ok:
    video.set(cv2.CAP_PROP_POS_FRAMES,0);ok,frame=video.read()
   if ok:
    # QUITAR LAS BARRAS NEGRAS QUE TRAE EL VIDEO (arriba y abajo)
    VIDEO_INFO.update(w=frame.shape[1],h=frame.shape[0],barra=round(frame.shape[0]*96/1246))
    barra=VIDEO_INFO['barra'];frame=frame[barra:frame.shape[0]-barra]
    fh,fw=frame.shape[:2];frame=cv2.resize(frame,(round(fw*720/fh),720),interpolation=cv2.INTER_AREA)
    frame=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
    last=pygame.image.frombuffer(frame.tobytes(),(frame.shape[1],frame.shape[0]),'RGB').convert()
  canvas.fill((0,0,0,0))
  if page:
   m=a_canvas(display,pygame.mouse.get_pos())
   if page=='CREAR':
    modal(canvas,'CREAR PARTIDA')
    boton(canvas,SOLO,'UN JUGADOR','Tú solo. Los demás personajes los maneja el juego.',SOLO.collidepoint(m),'I')
    boton(canvas,LOCAL,'MULTIJUGADOR LOCAL','Varios en este mismo PC, cada uno con sus teclas.',LOCAL.collidepoint(m),'II')
    boton(canvas,RED,'MULTIJUGADOR EN RED','Cada uno en su PC. Tus compañeros se unen a ti.',RED.collidepoint(m),'III')
    if aviso:label(canvas,aviso,160,462,19,VIVO)
   elif page=='LOCAL':
    modal(canvas,'MULTIJUGADOR LOCAL')
    label(canvas,'¿Cuántos van a jugar en este PC?',150,180,23,PAPEL)
    for n,r in CANTIDADES.items():
     sobre=r.collidepoint(m)
     boton(canvas,r,'',hover=sobre)
     t=pygame.font.SysFont('timesnewroman',64,bold=True).render(str(n),True,AMBAR if sobre else PAPEL)
     canvas.blit(t,t.get_rect(center=(r.centerx,r.centery-10)))
     t=pygame.font.SysFont('timesnewroman',13,bold=True).render('J U G A D O R E S',True,OXIDO)
     canvas.blit(t,t.get_rect(center=(r.centerx,r.bottom-20)))
    rotulo(canvas,'Controles',150,360,OXIDO,13)
    label(canvas,'Jugador 1: W A S D   ·   Jugador 2: flechas   ·   Jugador 3: I J K L',150,382,19,PAPEL)
    label(canvas,'Con 4 juegan por parejas y por turnos, como en el modo clásico.',150,408,19,PAPEL)
    label(canvas,'En el campo minado juegan a la vez; en lo demás se pasan el control.',150,440,17,APAGADO,italic=True)
   elif page=='SALA_HOST':
    modal(canvas,'SALA DE ESPERA')
    rotulo(canvas,'Dirección de la partida',150,172,OXIDO,13)
    caja=pygame.Rect(150,192,332,58)
    pygame.draw.rect(canvas,(13,12,13),caja);pygame.draw.rect(canvas,OXIDO,caja,1);pygame.draw.rect(canvas,VIVO,(caja.x,caja.y,4,caja.h))
    t=pygame.font.SysFont('timesnewroman',40,bold=True).render(ip_host,True,AMBAR)
    canvas.blit(t,t.get_rect(midleft=(caja.x+18,caja.centery)))
    label(canvas,'Tus compañeros pulsan',500,194,16,APAGADO)
    label(canvas,'UNIRSE A PARTIDA y la escriben.',500,213,16,APAGADO)
    label(canvas,'En este mismo PC: 127.0.0.1',500,233,15,TENUE,italic=True)
    lista_sala(canvas,sala,272)
    puede=sala is not None and sala.es_anfitrion()
    boton(canvas,INICIAR,'INICIAR PARTIDA',hover=INICIAR.collidepoint(m),activo=puede)
    label(canvas,'Solo el anfitrión puede iniciar.' if puede else 'Ya hay otra partida creada en este PC.',
          470,503,15,APAGADO,italic=True)
   elif page=='SALA':
    modal(canvas,'SALA DE ESPERA')
    rotulo(canvas,f'Conectado a {ip_host}',150,172,OXIDO,13)
    puntos='.'*(1+int(pygame.time.get_ticks()/400)%3)
    label(canvas,'Esperando a que el anfitrión',150,196,27,AMBAR,bold=True)
    label(canvas,'inicie la partida'+puntos,150,228,27,AMBAR,bold=True)
    pulso=int(pygame.time.get_ticks()/500)%2
    pygame.draw.circle(canvas,VIVO if pulso else (110,48,44),(752,214),6)
    lista_sala(canvas,sala,272)
   elif page=='UNIRSE':
    modal(canvas,'UNIRSE A PARTIDA')
    label(canvas,'Escribe la dirección que le aparece al anfitrión:',150,190,22,PAPEL)
    rotulo(canvas,'Dirección (IP)',160,230,OXIDO,13)
    pygame.draw.rect(canvas,(13,12,13),CAMPO_IP)
    pygame.draw.rect(canvas,AMBAR,CAMPO_IP,1);pygame.draw.rect(canvas,VIVO,(CAMPO_IP.x,CAMPO_IP.y,4,CAMPO_IP.h))
    cursor='|' if int(pygame.time.get_ticks()/500)%2 else ''
    if ip:label(canvas,ip+cursor,CAMPO_IP.x+20,CAMPO_IP.y+11,30,PAPEL)
    else:label(canvas,'127.0.0.1'+cursor,CAMPO_IP.x+20,CAMPO_IP.y+11,30,TENUE)
    if aviso:label(canvas,aviso,160,330,19,VIVO)
    else:label(canvas,'Pulsa Enter o ENTRAR para unirte.',160,330,18,APAGADO,italic=True)
    boton(canvas,ENTRAR,'ENTRAR',hover=ENTRAR.collidepoint(m))
   else:modal(canvas,page)
  # PANTALLA COMPLETA: el video llena toda la ventana y el menú va centrado encima
  dw,dh=display.get_size();scale=min(dw/W,dh/H)
  nw,nh=max(1,round(W*scale)),max(1,round(H*scale))
  vista=pygame.Surface((dw,dh))
  if last:
   esc=max(dw/last.get_width(),dh/last.get_height())
   fw,fh=round(last.get_width()*esc),round(last.get_height()*esc)
   vista.blit(pygame.transform.smoothscale(last,(fw,fh)),((dw-fw)//2,(dh-fh)//2))
  else:vista.fill((27,25,25))
  if page:
   oscuro=pygame.Surface((dw,dh),pygame.SRCALPHA);oscuro.fill((5,7,10,208));vista.blit(oscuro,(0,0))
  vista.blit(pygame.transform.smoothscale(canvas,(nw,nh)),((dw-nw)//2,(dh-nh)//2))
  if not page:   # "Créditos" venía en la barra negra del video: ahora se dibuja aquí
   fc=pygame.font.SysFont('timesnewroman',max(16,round(20*scale)));fc.set_underline(True)
   tc=fc.render('Créditos',True,(238,222,197) if CREDITOS_PANTALLA.collidepoint(pygame.mouse.get_pos()) else (205,195,180))
   CREDITOS_PANTALLA.update(tc.get_rect(midbottom=(dw//2,dh-12)).inflate(16,8))
   sombra=pygame.Surface(CREDITOS_PANTALLA.size,pygame.SRCALPHA);sombra.fill((0,0,0,120))
   vista.blit(sombra,CREDITOS_PANTALLA);vista.blit(tc,tc.get_rect(center=CREDITOS_PANTALLA.center))
  display.blit(Accesibilidad.filter_surface(vista),(0,0))
  pygame.display.flip()
 video.release();pygame.quit()
if __name__=='__main__':main()
