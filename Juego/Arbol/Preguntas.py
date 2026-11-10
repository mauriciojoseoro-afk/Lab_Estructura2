from Arbol.Arbol_AVL import ArbolAVL


def preguntas_P():
    preguntas_periodista = {
        1: "Durante la crisis, muchos ciudadanos no tenían acceso a agua potable. ¿Cómo logró su gobierno responder a esta situación?",
        2: "Algunos habitantes dicen que la solución fue temporal y que pronto volverá a faltar agua. ¿Qué les responde?",
        3: "En CIVINET circulan publicaciones que aseguran que el agua entregada estaba contaminada. ¿Qué puede decirnos al respecto?",
        4: "¿Cómo puede la ciudadanía comprobar que las cifras sobre la recuperación del suministro son reales?",
        5: "¿Qué papel tuvieron los ciudadanos que colaboraron durante la emergencia?",
        6: "Algunas publicaciones afirman que usted ocultó información durante los días más críticos. ¿Cómo responde a esas acusaciones?",
        7: "¿Qué medidas tomará para evitar que Ciudad Nova vuelva a sufrir una crisis de agua?",
        8: "¿Cómo piensa combatir los rumores y las noticias falsas que aparecen cada vez que ocurre una emergencia?",
        9: "Si CIVINET publica información manipulada sobre su gestión, ¿cómo podrán los ciudadanos distinguir la verdad?",
        10: "Después de lo ocurrido, ¿qué mensaje les daría a los habitantes de Ciudad Nova sobre la importancia de informarse antes de compartir una publicación?"
    }
    return preguntas_periodista


def respuestas_P():
    respuestas_presidente = {
        1: {
            "muy_buena": "Organizamos equipos de distribución, priorizamos los sectores más afectados y trabajamos con voluntarios para garantizar que el agua llegara a quienes más la necesitaban.",
            "regular": "Fue una situación difícil, pero hicimos todo lo posible para solucionar el problema y ayudar a la población.",
            "mala": "La crisis fue culpa de quienes estaban antes en el poder. Nosotros simplemente hicimos lo que pudimos."
        },
        2: {
            "muy_buena": "Entiendo la preocupación. Por eso estamos trabajando en un plan de mantenimiento y vigilancia del suministro. Publicaremos informes periódicos para que todos puedan comprobar los avances.",
            "regular": "Esperamos que no vuelva a ocurrir. Estamos intentando mantener el servicio funcionando.",
            "mala": "No tienen motivos para preocuparse. Si vuelve a faltar agua, seguramente será culpa de quienes no apoyaron nuestra gestión."
        },
        3: {
            "muy_buena": "No debemos creer ni compartir esa publicación sin pruebas. Los resultados de los análisis deben consultarse en fuentes oficiales y verificables. Invitamos a todos a revisarlos.",
            "regular": "No creo que el agua esté contaminada, pero sería bueno investigar un poco más.",
            "mala": "Eso es completamente falso. Compartan esta entrevista para demostrar que quienes publican esas cosas solo quieren perjudicarnos."
        },
        4: {
            "muy_buena": "Publicaremos los registros de distribución, los resultados de calidad del agua y las fechas de recuperación. La ciudadanía debe poder contrastar nuestras cifras con evidencias.",
            "regular": "Vamos a publicar algunos datos para que las personas sepan cómo estamos avanzando.",
            "mala": "Deben confiar en nosotros. No necesitamos demostrar cada cifra porque estamos trabajando por la ciudad."
        },
        5: {
            "muy_buena": "Fueron fundamentales. Muchos vecinos organizaron puntos de ayuda, compartieron información verificada y colaboraron con la distribución. La recuperación fue un esfuerzo colectivo.",
            "regular": "Algunas personas ayudaron bastante y estamos agradecidos por su colaboración.",
            "mala": "La solución fue principalmente gracias a mi gobierno. Sin nosotros, los ciudadanos no habrían podido hacer nada."
        },
        6: {
            "muy_buena": "Entiendo que existan dudas. Por eso vamos a publicar los reportes y registros de lo ocurrido durante la emergencia. Si cometimos errores, debemos reconocerlos y explicarlos con transparencia.",
            "regular": "No ocultamos información intencionalmente. Fueron días complicados y no siempre pudimos comunicar todo a tiempo.",
            "mala": "Eso es una mentira inventada por quienes quieren destruir mi reputación. No pierdan el tiempo investigando esas publicaciones."
        },
        7: {
            "muy_buena": "Crearemos un sistema de monitoreo, planes de mantenimiento y reservas de emergencia. También informaremos a los ciudadanos sobre cualquier interrupción del servicio.",
            "regular": "Intentaremos mejorar la infraestructura y estar más preparados si ocurre otra emergencia.",
            "mala": "Mientras yo esté al mando, no volverá a faltar agua. No hay necesidad de preocuparse por eso."
        },
        8: {
            "muy_buena": "Debemos verificar las fuentes, consultar los canales oficiales y evitar compartir información sin pruebas. También impulsaremos talleres de alfabetización digital para toda la comunidad.",
            "regular": "Las personas deben tener más cuidado con lo que comparten y consultar las noticias antes de creerlas.",
            "mala": "La mejor forma de combatir esos rumores es compartir nuestras publicaciones para que tengan más alcance que las demás."
        },
        9: {
            "muy_buena": "Comparando cada publicación con la entrevista original y los comunicados oficiales. También habilitaremos un canal donde los ciudadanos puedan reportar contenido manipulado y consultar las aclaraciones.",
            "regular": "Podrán consultar nuestras redes oficiales para saber qué información es verdadera.",
            "mala": "Si ven publicaciones que nos critican, no les presten atención. Lo importante es que sigan apoyando nuestro trabajo."
        },
        10: {
            "muy_buena": "La crisis nos enseñó que debemos estar preparados y comunicarnos con responsabilidad. Les pido verificar la información en fuentes confiables antes de compartirla.",
            "regular": "Es importante que todos estén informados y que consulten las fuentes oficiales.",
            "mala": "La gente debe compartir lo que encuentre para que todos sepan lo que está pasando."
        },
    }
    return respuestas_presidente