import math
import random
import string

M = 64
SEMILLAS = [31, 37, 41]
K = len(SEMILLAS)


def posiciones(nombre):
    resultado = []
    for semilla in SEMILLAS:
        h = 0
        for letra in nombre:
            h = h * semilla + ord(letra)
        resultado.append(h % M)
    return resultado


def agregar(bits, nombre):
    for p in posiciones(nombre):
        bits[p] = 1


def buscar(bits, nombre):
    return all(bits[p] == 1 for p in posiciones(nombre))


def nombres_aleatorios(cantidad, usados):
    
    nombres = set()
    while len(nombres) < cantidad:
        n = "".join(random.choices(string.ascii_lowercase, k=8))
        if n not in usados:
            nombres.add(n)
    return list(nombres)


def evaluar(n, pruebas= 10000):
    bits = [0] * M

    insertados = nombres_aleatorios(n, set())
    for nombre in insertados:
        agregar(bits, nombre)

    falsos_negativos = sum(1 for nombre in insertados if not buscar(bits, nombre))

    no_insertados = nombres_aleatorios(pruebas, set(insertados))
    falsos_positivos = sum(1 for nombre in no_insertados if buscar(bits, nombre))
    tasa_real = falsos_positivos / pruebas

    tasa_teorica = (1 - math.exp(-K * n / M)) ** K

    bits_en_1 = sum(bits)
    return falsos_negativos, tasa_real, tasa_teorica, bits_en_1


random.seed(1)  

print(f"Filtro con m = {M} bits y k = {K} funciones hash\n")
print(f"{'n':>4} | {'bits en 1':>9} | {'falsos neg.':>11} | {'FP real':>8} | {'FP teórico':>10}")
print("-" * 54)

for n in [1, 2, 5, 10, 15, 20, 30]:
    fn, real, teorica, llenos = evaluar(n)
    print(f"{n:>4} | {llenos:>5}/{M:<3} | {fn:>11} | {real:>7.1%} | {teorica:>9.1%}")

print("\nLectura de resultados:")
print("- Falsos negativos debe ser SIEMPRE 0 (si no, el filtro está mal).")
print("- FP real = % de nombres nunca registrados que el filtro dijo que SÍ están.")
print("- FP teórico = fórmula p = (1 - e^(-kn/m))^k de la exposición.")