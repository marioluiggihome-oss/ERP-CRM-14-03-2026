# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
almacen_datos.py — LAS EXISTENCIAS Y LAS RESERVAS, sin base de datos.

El motor de cálculo (`almacen.py`) ya sabía decir qué hay que comprar, pero
nadie le daba los datos: faltaban las existencias de cada referencia y las
reservas por proyecto. Esto es esa parte, en cálculo puro para poder probarla;
las rutas (`routes/almacen.py`) solo leen y escriben.

LA REGLA QUE SOSTIENE TODO ESTO
-------------------------------
**Reservado para OTROS no incluye lo mío.** Cuando se calcula si a la cocina
P-482 le falta material, lo que tienen comprometido los DEMÁS proyectos resta,
pero lo que ella misma tiene reservado NO — o se restaría dos veces y saldría
una compra que no hace falta.

Parece obvio escrito, y es exactamente el error que se comete al juntar las
dos listas sin mirar de quién es cada reserva.

LO QUE NO SE INVENTA
--------------------
Una referencia sin ficha de almacén tiene `stock = None`, que quiere decir «ve
a mirarlo», no «no hay». Un cero dispara una compra que quizá sobra; un `None`
manda a alguien a la estantería. Son cosas distintas y el motor ya las trata
distinto — aquí lo único que hay que hacer es NO rellenar el hueco.
"""


# El lector de líneas se carga a mano y no con un `from services import`: este
# módulo es cálculo puro y se prueba cargándolo por ruta, sin levantar el
# paquete `services` —que arrastra la autenticación y exige un JWT_SECRET—.
# `linea_pedido` tampoco importa nada, así que se carga igual de suelto.
try:
    from services import linea_pedido                 # dentro del ERP
except Exception:                                     # cargado suelto, por ruta
    import importlib.util as _ilu
    import os as _os
    _r = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "linea_pedido.py")
    _sp = _ilu.spec_from_file_location("_linea_pedido_almacen", _r)
    linea_pedido = _ilu.module_from_spec(_sp)
    _sp.loader.exec_module(linea_pedido)


def _num(v):
    """Número, o None si no consta. Cadena vacía NO es cero."""
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _ref(v):
    """La referencia, normalizada. Es la clave con la que se cruza todo.

    Se compara SIN espacios sobrantes y en mayúsculas: en las fichas se teclean
    a mano y « b60d » y «B60D» son la misma pieza. Sin esto, la reserva de una
    y el stock de la otra no se encuentran, y el resultado sale mal sin que
    nada falle.
    """
    return str(v or "").strip().upper()


def reservado_para_otros(reservas, proyecto):
    """Cuánto tienen comprometido los DEMÁS proyectos, por referencia.

    `reservas`: [{referencia, proyecto, cantidad}]

    Lo reservado por `proyecto` NO cuenta: es suyo, ya está contado en lo que
    necesita. Restarlo otra vez le haría comprar material que ya tiene apartado.
    """
    mio = _ref(proyecto)
    fuera = {}
    for r in reservas or []:
        if _ref(r.get("proyecto")) == mio:
            continue
        cant = _num(r.get("cantidad")) or 0
        if cant <= 0:
            continue
        ref = _ref(r.get("referencia"))
        if not ref:
            continue
        fuera[ref] = round(fuera.get(ref, 0.0) + cant, 3)
    return fuera


def stock_por_referencia(fichas):
    """Las existencias, indexadas por referencia.

    `fichas`: [{referencia, stock, minimo, ubicacion}]

    Una ficha SIN stock se guarda igual, con `stock` a None: existe la
    referencia pero no se sabe cuánta hay. Convertirlo en 0 aquí sería meter
    una mentira justo en el sitio donde el motor sabe distinguirlas.
    """
    idx = {}
    for f in fichas or []:
        ref = _ref(f.get("referencia"))
        if not ref:
            continue
        idx[ref] = {
            "referencia": ref,
            "stock": _num(f.get("stock")),
            "minimo": _num(f.get("minimo")),
            "ubicacion": (f.get("ubicacion") or "").strip(),
        }
    return idx


def necesidades_del_despiece(lineas):
    """Lo que el proyecto necesita de cada referencia, sumando las repetidas.

    `lineas`: las del despiece / pedido — [{code|referencia, quantity|cantidad}]

    UNA REFERENCIA PUEDE VENIR EN VARIAS LÍNEAS. Sumarlas es el enganche entre
    el despiece y el almacén: si se mira línea a línea, cada una parece cubierta
    con el mismo tablero y al final falta material. Es el mismo tablero contado
    tres veces.
    """
    total = {}
    for l in lineas or []:
        # El código y las unidades los lee `linea_pedido`, que conoce los
        # nombres de LOS TRES presupuestadores. Antes aquí solo se miraba
        # `code`/`productCode`, así que una proforma de Cocina Desmontada
        # —que escribe `cod` y `cantidad`— era invisible entera: el plan de
        # compra decía «ninguna línea trae referencia». Y no daba error.
        ref = _ref(linea_pedido.codigo(l))
        if not ref:
            continue
        cant = linea_pedido.cantidad(l)
        if cant <= 0:
            continue
        total[ref] = round(total.get(ref, 0.0) + cant, 3)
    return total


def montar_lineas(necesidades, fichas, reservas, proyecto, pedidos=None):
    """Arma la entrada de `almacen.plan_de_compra` para un proyecto.

    Junta las cuatro cosas que hacen falta —lo que necesita, lo que hay, lo que
    tienen apartado los demás y lo que ya viene de camino— y deja el cálculo al
    motor, que es quien sabe qué es «no se sabe» y qué es cero.
    """
    idx_stock = stock_por_referencia(fichas)
    de_otros = reservado_para_otros(reservas, proyecto)
    en_camino = {_ref(k): (_num(v) or 0) for k, v in (pedidos or {}).items()}

    lineas = []
    for ref, necesario in sorted(necesidades.items()):
        ficha = idx_stock.get(ref) or {}
        lineas.append({
            "referencia": ref,
            "necesario": necesario,
            # Sin ficha, `stock` queda a None y el motor dirá «ve a mirarlo».
            "stock": ficha.get("stock"),
            "reservadoOtros": de_otros.get(ref, 0),
            "pedido": en_camino.get(ref, 0),
            "minimo": ficha.get("minimo"),
            "ubicacion": ficha.get("ubicacion", ""),
        })
    return lineas


def sin_ficha(necesidades, fichas):
    """Referencias que el proyecto necesita y que NO están dadas de alta.

    Se listan aparte para poder crearlas, en vez de dejarlas mezcladas entre
    las que «no tienen stock»: no es lo mismo una referencia que existe y está
    a cero que una que nadie ha dado de alta todavía.
    """
    idx = stock_por_referencia(fichas)
    return sorted(ref for ref in necesidades if ref not in idx)
