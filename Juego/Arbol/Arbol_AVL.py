class NodoAVL:
    def __init__(self, id):
        self.id = id
        self.izquierda = None
        self.derecha = None
        self.altura = 1


class ArbolAVL:
    def __init__(self):
        self.raiz = None

   
    def _altura(self, nodo):
        if nodo is None:
            return 0
        return nodo.altura

    def _balance(self, nodo):
        if nodo is None:
            return 0
        return self._altura(nodo.derecha) - self._altura(nodo.izquierda)

    def _actualizar_altura(self, nodo):
        nodo.altura = 1 + max(self._altura(nodo.izquierda), self._altura(nodo.derecha))

    def _rotacion_derecha(self, y):
        x = y.izquierda
        t2 = x.derecha

        x.derecha = y
        y.izquierda = t2

        self._actualizar_altura(y)
        self._actualizar_altura(x)

        return x 

    def _rotacion_izquierda(self, x):
        y = x.derecha
        t2 = y.izquierda

        y.izquierda = x
        x.derecha = t2

        self._actualizar_altura(x)
        self._actualizar_altura(y)

        return y 



    def set(self, id):
        self.raiz = self._insertar(self.raiz, id)

    def _insertar(self, nodo, id):
     
        if nodo is None:
            return NodoAVL(id)

        if id < nodo.id:
            nodo.izquierda = self._insertar(nodo.izquierda, id)
        elif id > nodo.id:
            nodo.derecha = self._insertar(nodo.derecha, id)
        else:
           
            return nodo

       
        self._actualizar_altura(nodo)

    
        balance = self._balance(nodo)

             
        # caso izquierda-izquierda
        if balance < -1 and id < nodo.izquierda.id:
            return self._rotacion_derecha(nodo)

        # caso derecha-derecha
        if balance > 1 and id > nodo.derecha.id:
            return self._rotacion_izquierda(nodo)

        # caso izquierda-derecha
        if balance < -1 and id > nodo.izquierda.id:
            nodo.izquierda = self._rotacion_izquierda(nodo.izquierda)
            return self._rotacion_derecha(nodo)

        # caso derecha-izquierda
        if balance > 1 and id < nodo.derecha.id:
            nodo.derecha = self._rotacion_derecha(nodo.derecha)
            return self._rotacion_izquierda(nodo)

        return nodo



    def get(self, id):
        return self._buscar(self.raiz, id)

    def _buscar(self, nodo, id):
        if nodo is None:
            return None
        if id == nodo.id:
            return nodo
        if id < nodo.id:
            return self._buscar(nodo.izquierda, id)
        return self._buscar(nodo.derecha, id)