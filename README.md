# The Leader

En una ciudad destruida por la desinformación, 4 sobrevivientes deciden qué compartir, verificar o ignorar mientras Civitas, una IA que esparce rumores, los manipula. Cada decisión cambia la confianza del grupo… hasta descubrir que todos tuvieron que ver con Civitas.

Videojuego educativo sobre la desinformación y el uso responsable de las redes sociales, desarrollado como laboratorio de la asignatura **Estructura de Datos II** — Universidad del Norte.

## Historia

**Ciudad Nova** colapsó después de que una noticia falsa se regara por **CIVINET**, la red controlada por **Civitas**, una inteligencia artificial que decide qué ve la ciudad. Los sobrevivientes buscan a alguien que los guíe, pero nadie confía en nadie. Cada jugador asume uno de cuatro personajes, y todos esconden algo:

- **Héctor — Presidente:** detectó el rumor antes del colapso y nadie le hizo caso.
- **Osamu Kuga — Periodista:** tenía la prueba que lo desmentía y esperó demasiado.
- **Jenny — Influencer:** lo publicó sin verificarlo.
- **Estella — Ciudadana:** lo compartió sin leerlo.

## Recorrido

1. **Intro:** una cinemática muestra cómo una sola notificación compartida por todos destruye la ciudad.
2. **Evento 1:** cada personaje por su lado decide qué hacer con un mensaje dudoso.
3. **Evento 2 — Campo minado:** el grupo cruza el Campo Sembrado.
4. **Entrevista en vivo:** Osamu entrevista a Héctor mientras Civitas publica rumores; cada rol decide si verificar, compartir o corregir.
5. **Evento 3 — La oficina:** en la Central de Datos el jugador descubre su propio expediente.
6. **Final:** depende de la **Confianza**, el **Caos** y la **Cohesión** (en multijugador, del promedio del grupo).

## Modos de juego

- **Un jugador:** los demás personajes los maneja el juego.
- **Multijugador local:** 2 a 4 jugadores en el mismo PC, cada uno con sus teclas.
- **Multijugador en red:** uno crea la partida y los demás se unen por IP (los personajes elegidos se bloquean).

## Estructuras de datos utilizadas

- **Árboles AVL:** organizan las preguntas y respuestas de la entrevista en vivo (el árbol de preguntas del periodista y el de respuestas del presidente, sincronizados por ID).
- **Grafos:** representan el mapa de la ciudad y la red social del grupo; en la oficina se usa **BFS** para mostrar cómo se propagó el rumor ronda por ronda y para encontrar caminos en el tablero de pistas.

## Tecnologías

- **Lenguaje:** Python 3.12
- **Interfaz gráfica:** Pygame
- **Video:** OpenCV (`opencv-python`)
- **Arquitectura:** cliente-servidor mediante sockets (multijugador)

## Requisitos

- Python 3.12 o superior
- Pygame, OpenCV y NumPy

```bash
pip install pygame opencv-python numpy
```

## Ejecución

El juego siempre se ejecuta desde el punto de entrada principal:

```bash
cd Juego
python Pantalla.py
```

## Integrantes

- Isaac González
- Karla Paredes
- Laura Lanchero
- Mauricio Orozco