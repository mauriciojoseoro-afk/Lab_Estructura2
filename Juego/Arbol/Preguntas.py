
from Arbol_AVL import ArbolAVL

preguntas_periodista = {
    1: "En las redes circula que usted quiere cerrar el colegio de Ciudad Nova. ¿Es cierto?",
    2: "Se dice que el alcalde actual está robando dinero. ¿Usted qué opina?",
    3: "Una publicación viral dice que mañana cerrarán todos los parques. La gente está alarmada. ¿Qué les dice?",
    4: "Sus seguidores atacan a otros candidatos en los comentarios. ¿Qué piensa hacer?",
    5: "Un influencer compartió una noticia falsa que lo favorece a usted. ¿Va a pronunciarse?",
    6: "¿Cómo pueden los ciudadanos saber si una publicación sobre su campaña es real?",
    7: "Se sospecha que hay cuentas falsas apoyando su campaña. ¿Qué responde?",
    8: "Hubo una discusión fuerte entre vecinos por publicaciones políticas. ¿Qué propone?",
    9: "Muchos jóvenes pasan demasiadas horas en Redes. ¿Tiene alguna propuesta?",
    10: "Si pierde las elecciones, ¿qué les dirá a sus seguidores en redes?",
}

arbol_periodista = ArbolAVL()

for id in preguntas_periodista.keys():
    arbol_periodista.set(id)


nodo = arbol_periodista.get(2)

if nodo is not None:
    texto_pregunta = preguntas_periodista[nodo.id]
    print(texto_pregunta)
else:
    print("Esa pregunta no existe en el árbol")



respuestas_presidente = {
    1: {
        "muy_buena": "No es cierto. Publiqué mi propuesta completa de educación en mi perfil oficial y los invito a leerla y compararla antes de compartir cualquier publicación.",
        "regular": "Eso no es verdad, la gente inventa muchas cosas en campaña.",
        "mala": "Seguro ese rumor lo inventó el equipo del candidato Juan. Ellos son los que quieren cerrarlo.",
    },
    2: {
        "muy_buena": "No tengo pruebas de eso y no voy a repetir una acusación sin verificar. Si alguien tiene evidencia, debe llevarla a los organismos de control.",
        "regular": "No sé si es verdad, pero habría que investigar.",
        "mala": "Todo el mundo lo sabe. Compartan esa información para que la ciudad despierte.",
    },
    3: {
        "muy_buena": "Consulté con la Alcaldía y esa información es falsa. Les pido que no la compartan y que revisen siempre la fuente oficial antes de reaccionar.",
        "regular": "No creo que sea cierto, pero no tengo más información.",
        "mala": "Si es verdad, es culpa del gobierno actual. Por eso deben votar por mí.",
    },
    4: {
        "muy_buena": "No apoyo los ataques. Pido a mis seguidores debatir con respeto sobre las propuestas y voy a reportar los mensajes ofensivos, vengan de donde vengan.",
        "regular": "Yo no puedo controlar lo que escribe cada persona.",
        "mala": "Los otros candidatos se lo buscaron. La gente solo dice lo que piensa.",
    },
    5: {
        "muy_buena": "Sí. Aunque me favorezca, es falsa. Ya le pedí que la corrija y aclaré en mis redes cuál es la información real.",
        "regular": "No la compartí yo, así que no es mi responsabilidad.",
        "mala": "Si la gente la cree y me ayuda, no veo el problema.",
    },
    6: {
        "muy_buena": "Toda mi información sale de mi cuenta verificada, con fecha y fuente. Si ven algo raro, pueden consultarlo con medios confiables o preguntarnos directamente.",
        "regular": "Deben confiar en lo que yo digo.",
        "mala": "Si lo ven en muchas cuentas, seguramente es verdad.",
    },
    7: {
        "muy_buena": "No uso cuentas falsas. Pediré a mi equipo revisar esas cuentas y, si se comprueba algo, lo reportaré públicamente.",
        "regular": "No sé nada de eso, no manejo esas cosas.",
        "mala": "Todos los candidatos lo hacen. Es parte de la campaña.",
    },
    8: {
        "muy_buena": "Propongo una campaña de convivencia digital: debatir ideas sin insultar, bloquear o reportar el acoso y recordar que el vecino no es un enemigo.",
        "regular": "Es normal que haya discusiones en elecciones.",
        "mala": "Quien no apoye mis propuestas no quiere el bien de la ciudad.",
    },
    9: {
        "muy_buena": "Sí: talleres en el colegio sobre bienestar digital, espacios en los parques para desconectarse y guías para familias sobre uso responsable.",
        "regular": "Cada familia debe encargarse de eso.",
        "mala": "Mientras más tiempo estén conectados, más gente ve mis publicaciones.",
    },
    10: {
        "muy_buena": "Que respeten el resultado, eviten difundir teorías sin pruebas y sigan participando con responsabilidad por el bien de Ciudad Nova.",
        "regular": "Veremos qué pasa cuando lleguen los resultados.",
        "mala": "Si pierdo, es porque hubo fraude. Estén atentos y compartan todo lo que encuentren.",
    },
}

arbol_respuestas = ArbolAVL()
for id in respuestas_presidente.keys():
    arbol_respuestas.set(id)


id_pregunta = 3

nodo_pregunta = arbol_periodista.get(id_pregunta)
nodo_respuesta = arbol_respuestas.get(id_pregunta)

if nodo_pregunta and nodo_respuesta:
    opciones = respuestas_presidente[nodo_respuesta.id]
    print("Periodista pregunta:", preguntas_periodista[nodo_pregunta.id])
    print("Muy buena:", opciones["muy_buena"])
    print("Regular:", opciones["regular"])
    print("Mala:", opciones["mala"])
