# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
almacen.py — QUÉ HAY, QUÉ ESTÁ COMPROMETIDO Y QUÉ HAY QUE COMPRAR.

Cálculo puro, sin base de datos, para poder probarlo.

LA IDEA QUE HACE QUE ESTO SIRVA
-------------------------------
Lo que hay en la estantería NO es lo que se puede usar. Una parte ya está
prometida a otros proyectos. Contarla dos veces es exactamente como se llega al
día del montaje sin material: el sistema decía que había diez tableros, y había
diez, pero ocho eran de otra cocina.

    disponible = stock físico − reservado para otros proyectos

Y a partir de ahí:

    pendiente de comprar = necesario − disponible − ya pedido al proveedor

NUNCA SE INVENTA UN NÚMERO
--------------------------
Si no se sabe el stock de una referencia, el resultado es "no se sabe", no
cero. Un cero dice "no hay" y dispara una compra que quizá sobra; un `None`
dice "ve a mirarlo", que es la verdad. Son cosas distintas y aquí no se
confunden.
"""


def _num(v):
    """Número, o None si no consta. Cadena vacía NO es cero."""
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def disponible(stock, reservado_otros=0):
    """Lo que de verdad se puede coger de la estantería.

    Devuelve None si no se conoce el stock: sin ese dato no se puede afirmar
    nada, y afirmar 0 mandaría a comprar algo que a lo mejor está ahí.
    """
    s = _num(stock)
    if s is None:
        return None
    r = _num(reservado_otros) or 0
    return round(s - r, 3)


def necesidad(necesario, stock=None, reservado_otros=0, pedido=0):
    """Cuánto falta por comprar de una referencia, para UN proyecto.

    Devuelve un diccionario con el desglose completo, porque el número solo
    ("faltan 3") no deja comprobar de dónde sale y nadie se fía de él.
    """
    nec = _num(necesario) or 0
    disp = disponible(stock, reservado_otros)
    ped = _num(pedido) or 0

    if disp is None:
        return {
            "necesario": nec,
            "disponible": None,
            "pedido": ped,
            "pendiente": None,
            "cubierto": None,
            "motivo": "Sin dato de stock: hay que mirarlo en el almacén.",
        }

    cubierto = disp + ped
    pendiente = round(max(0.0, nec - cubierto), 3)
    return {
        "necesario": nec,
        "disponible": disp,
        "pedido": ped,
        "pendiente": pendiente,
        "cubierto": pendiente == 0,
        "motivo": "",
    }


def necesita_reposicion(stock, reservado_otros=0, minimo=None):
    """¿Hay que reponer esta referencia?

    Se compara contra lo DISPONIBLE, no contra el stock físico: si hay 10 y 9
    están reservados, queda 1 aunque la estantería parezca llena.
    Sin mínimo definido no se avisa — un aviso inventado se aprende a ignorar,
    y entonces tampoco se ven los de verdad.
    """
    m = _num(minimo)
    if m is None:
        return False
    disp = disponible(stock, reservado_otros)
    if disp is None:
        return False
    return disp < m


def plan_de_compra(lineas):
    """Junta las necesidades de varias referencias en una sola lista.

    `lineas`: [{referencia, necesario, stock, reservadoOtros, pedido, minimo}]
    """
    pendientes, sin_dato, cubiertas = [], [], 0
    for l in lineas or []:
        n = necesidad(l.get("necesario"), l.get("stock"),
                      l.get("reservadoOtros"), l.get("pedido"))
        fila = {"referencia": l.get("referencia") or "", **n}
        if n["pendiente"] is None:
            sin_dato.append(fila)
        elif n["pendiente"] > 0:
            pendientes.append(fila)
        else:
            cubiertas += 1

    return {
        "pendientes": pendientes,
        "sinDato": sin_dato,
        "cubiertas": cubiertas,
        "hayQueComprar": bool(pendientes),
        "resumen": _resumen(pendientes, sin_dato, cubiertas),
    }


def _resumen(pendientes, sin_dato, cubiertas):
    partes = []
    if pendientes:
        partes.append(f"{len(pendientes)} referencia(s) por comprar")
    if sin_dato:
        # Se nombran aparte a propósito: no son "cero pendientes", son un
        # agujero de información. Mezclarlas con las cubiertas daría por
        # resuelto lo que ni siquiera se ha mirado.
        partes.append(f"{len(sin_dato)} SIN dato de stock")
    if not partes:
        return f"Todo cubierto: {cubiertas} referencia(s)."
    return "; ".join(partes) + f" ({cubiertas} cubiertas)."
