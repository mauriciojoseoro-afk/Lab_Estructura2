# Alcalde Digital

Videojuego educativo sobre el uso responsable de las redes sociales, desarrollado como laboratorio de la asignatura **Estructura de Datos II** — Universidad del Norte.

## Descripción

Ambientado en la ciudad ficticia de **Ciudad Nova**, durante una contienda electoral. El juego es multijugador (2 a 4 jugadores) y cada participante asume uno de los siguientes roles:

- **Ciudadano**
- **Periodista**
- **Influencer**
- **Candidato a alcalde**

A través de eventos, decisiones y propuestas, los jugadores exploran cómo la información (verdadera o falsa) se propaga en redes sociales y cómo eso afecta una elección.

## Cambios recientes del equipo

El proyecto ha recibido varias actualizaciones por parte del equipo para mejorar la experiencia del juego y completar la narrativa:

- Ajustes en la historia y en los recursos visuales del juego.
- Nueva pantalla de selección con fondo urbano y personajes con proporciones uniformes.
- Evento 1 reforzado con tiempos, alertas, filtros y textos actualizados.
- Mapa mejorado con la Central de Datos, zonas de niebla y una representación más clara de la ciudad.
- Evento 2 con nuevas interacciones y movimientos del presidente.
- Evento 3 ampliado con oficina, grafo social, pistas, finales y subtítulos nuevos.
- Incorporación de recursos adicionales y animaciones del periodista para una experiencia visual más rica.

## Tecnologías

- **Lenguaje:** Python 3.12
- **Interfaz gráfica:** Pygame
- **Arquitectura:** Cliente-servidor mediante sockets (multijugador)

## Estructuras de datos utilizadas

- **Árboles AVL:** organizan las preguntas y respuestas de cada rol (por ejemplo, el árbol de preguntas del periodista y el árbol de respuestas del presidente, sincronizados por ID), así como las propuestas de gobierno (inserción por el candidato, eliminación por votación de los demás roles).
- **Grafos:** representan la ciudad y la red social de propagación de información entre jugadores.


## Requisitos

- Python 3.12 o superior
- Pygame

Instalación de dependencias:

\`\`\`bash
pip install pygame
\`\`\`

## Ejecución

El juego siempre se debe ejecutar desde el punto de entrada principal, nunca desde los archivos internos por separado:

\`\`\`bash
python Juego/Pantalla.py
\`\`\`


## Integrantes

- Mauricio Orozco
- Karla Paredes
- Laura Lanchero
- Isak González

