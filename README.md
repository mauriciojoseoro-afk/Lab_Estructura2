# The Leader

Videojuego educativo sobre la desinformación y el uso responsable de las redes sociales, desarrollado como laboratorio de la asignatura **Estructura de Datos II** — Universidad del Norte.

## Historia

**Ciudad Nova** colapsó después de que un rumor falso sobre el agua se regara por **CIVINET**, la red controlada por **Civitas**, una inteligencia artificial que decide qué ve la ciudad. Los sobrevivientes buscan a alguien que los guíe, pero nadie confía en nadie. Cada jugador asume uno de cuatro personajes, y todos esconden algo:

- **Héctor — Presidente:** detectó el rumor antes del colapso y nadie le hizo caso.
- **Osamu Kuga — Periodista:** tenía la prueba que lo desmentía y esperó demasiado.
- **Jenny — Influencer:** lo publicó sin verificarlo.
- **Estella — Sobreviviente:** lo compartió sin leerlo.

## Recorrido

1. **Evento 1:** cada personaje por su lado (el pozo, el depósito, el video del periodista…); decide qué hacer con un mensaje dudoso.
2. **Evento 2 — Campo minado:** el grupo cruza el Campo Sembrado.
3. **Entrevista en vivo:** Osamu entrevista a Héctor mientras Civitas publica rumores; cada rol decide si verificar, compartir o corregir.
4. **Evento 3 — La oficina:** en la Central de Datos el jugador descubre su propio expediente.
5. **Final:** según la **Confianza**, el **Caos** y la **Cohesión** (en multijugador, el promedio del grupo).

Los videos se saltan con **doble espacio**.

## Tecnologías

- **Lenguaje:** Python 3.12
- **Interfaz gráfica:** Pygame
- **Video:** OpenCV (`opencv-python`)
- **Arquitectura:** Cliente-servidor mediante sockets (multijugador)

## Modos de juego

- **Un jugador:** los demás personajes los maneja el juego.
- **Multijugador local:** 2 a 4 jugadores en el mismo PC, cada uno con sus teclas.
- **Multijugador en red:** uno crea la partida y los demás se unen por IP (los personajes elegidos se bloquean).

## Estructuras de datos utilizadas

- **Árboles AVL:** organizan las preguntas y respuestas de cada rol (por ejemplo, el árbol de preguntas del periodista y el árbol de respuestas del presidente, sincronizados por ID), usados en la entrevista en vivo.
- **Grafos:** representan el mapa de la ciudad y la red social del grupo; en la oficina se usa **BFS** para mostrar cómo se propagó el rumor ronda por ronda y para encontrar caminos en el tablero de pistas.


## Requisitos

- Python 3.12 o superior
- Pygame, OpenCV y NumPy

Instalación de dependencias:

\`\`\`bash
pip install pygame opencv-python numpy
\`\`\`

## Ejecución

El juego siempre se debe ejecutar desde el punto de entrada principal, nunca desde los archivos internos por separado:

\`\`\`bash
cd Juego
python Pantalla.py
\`\`\`


## Integrantes

- Mauricio Orozco
- Karla Paredes
- Laura Lanchero
- Isaac González

