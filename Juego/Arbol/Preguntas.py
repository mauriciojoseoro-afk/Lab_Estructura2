
from Arbol_AVL import ArbolAVL

preguntas_periodista = {
    1: "¿Cómo piensa combatir la corrupción en su gobierno?",
    2: "¿Qué opina sobre el aumento de la propaganda política en redes sociales?",
    3: "¿Cuál es su plan para mejorar la seguridad ciudadana?",
    4: "¿Está dispuesto a rendir cuentas públicas sobre el uso de fondos municipales?"
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
    1: "Implementaré auditorías trimestrales y un canal ciudadano de denuncias.",
    2: "La regularé sin censurar, exigiendo transparencia en cuentas verificadas.",
    3: "Aumentaré la iluminación pública y el patrullaje en zonas críticas.",
    4: "Sí, publicaré informes financieros abiertos cada trimestre."
}

arbol_respuestas = ArbolAVL()
for id in respuestas_presidente.keys():
    arbol_respuestas.set(id)


id_pregunta = 3

nodo_pregunta = arbol_periodista.get(id_pregunta)
nodo_respuesta = arbol_respuestas.get(id_pregunta)

if nodo_pregunta and nodo_respuesta:
    print("Periodista pregunta:", preguntas_periodista[nodo_pregunta.id])
    print("Presidente responde:", respuestas_presidente[nodo_respuesta.id])