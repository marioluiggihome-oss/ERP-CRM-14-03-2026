# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
LAS LÍNEAS DE UN PEDIDO DE VERDAD, NO LAS QUE ME INVENTÉ EN LAS PRUEBAS.

Visto en producción el 28/08: la pantalla de COOP enseñaba «0 muebles» en TODOS
los pedidos. O sea comisión cero para todo el mundo, sin un solo error.

La causa era mía. `orders.py` guarda las líneas tal como las manda
`BudgetTable.jsx`: `{code, name, quantity, price}`. Y el cálculo leía `familia`,
`qty` y `pvp` — los nombres que usaban mis fixtures. Un candado escrito contra
datos inventados no protege nada: pasaba en verde mientras la nómina real salía
a cero.

DOS ARREGLOS, Y EL SEGUNDO ES EL QUE IMPORTA:

1. Se leen los nombres de verdad (`quantity`, `price`), y la familia se resuelve
   por el CÓDIGO contra el catálogo (`B25D/I` → «BAJO», que es su `category`).

2. NO SABER NO ES CERO. Si ninguna línea se puede clasificar, el pedido no tiene
   «0 muebles»: es que no se sabe lo que lleva. Se marca `sinDesglose` y se
   rotula «?», que es la regla 7 de CLAUDE.md. Un 0 parece un dato y deja a
   alguien sin cobrar sin decirle por qué.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("JWT_SECRET", "secreto-de-pruebas-largo-y-aleatorio-0123456789")

from services import area_cooperativista as AC  # noqa: E402
from services import comisiones as C            # noqa: E402

# Un pedido tal y como lo guarda `orders.py`: sin `familia`, con `quantity` y
# `price`, y con `price` YA multiplicado por las unidades.
PEDIDO_REAL = {
    "id": "MV-2026-64608", "confirmedAt": "2026-06-20",
    "customerName": "MARIO - ARMARIO",
    "items": [
        {"code": "B60D/I", "name": "BAJO 60", "quantity": 4, "price": 1200.0},
        {"code": "P45", "name": "PUERTA 45", "quantity": 8, "price": 400.0},
    ],
}
CATALOGO = {"B60D/I": "BAJO", "P45": "PUERTAS"}


def test_las_UNIDADES_se_leen_de_quantity():
    """`quantity` es el nombre del ERP. Antes se caía al `or 1` y una línea de
    cuatro muebles contaba como uno."""
    assert C.unidades_de({"quantity": 4}) == 4
    assert C.unidades_de({"qty": 4}) == 4          # el de las pruebas, que sigue valiendo
    assert C.unidades_de({}) == 1                  # sin nada, una unidad
    assert C.unidades_de({"quantity": 0}) == 0     # un cero es un cero
    assert C.unidades_de({"quantity": "tres"}) == 0


def test_el_IMPORTE_se_lee_de_price_y_no_se_multiplica_dos_veces():
    """`price` de BudgetTable es `details.total`: YA lleva las unidades dentro.
    Multiplicarlo otra vez inflaría la base imponible y subiría de tramo al
    comercial sin que el pedido valiera un euro más."""
    assert C.importe_de({"quantity": 4, "price": 1200.0}) == 1200.0
    # `pvp` sí es por unidad: ese sí se multiplica.
    assert C.importe_de({"qty": 4, "pvp": 300.0}) == 1200.0


def test_la_FAMILIA_se_resuelve_por_el_CODIGO_contra_el_catalogo():
    """Las líneas guardan el código, no la familia. La familia es la `category`
    del producto."""
    p = AC.normaliza_pedido(PEDIDO_REAL, 17.0, CATALOGO)
    assert p["muebles"] == 4, (
        f"cuenta {p['muebles']} muebles: los 4 bajos cuentan y las 8 puertas no")
    assert p["baseImponible"] == 1200.0, (
        "la base imponible tiene que ser solo la de los muebles: las puertas no "
        "incentivan")
    assert p["sinDesglose"] is False


def test_SIN_CATALOGO_sale_INTERROGANTE_y_no_un_cero_enganoso():
    """El fallo que se vio en pantalla.

    Sin poder clasificar ninguna línea, el pedido NO tiene cero muebles: no se
    sabe lo que lleva. Un 0 parece un dato y deja a alguien sin cobrar sin
    decirle por qué; un «?» se ve y se arregla.
    """
    p = AC.normaliza_pedido(PEDIDO_REAL, 17.0)
    assert p["sinDesglose"] is True, (
        "un pedido cuyas líneas no se pueden clasificar sale como «0 muebles» en "
        "vez de «?»: eso es lo que enseñaba la pantalla el 28/08")
    assert p["muebles"] == 0 and p["baseImponible"] == 0.0, (
        "y mientras no se sepa, no paga: contar el pedido entero sería pagar de "
        "más, y pagar de más no se devuelve")

    fila = AC.pedido_para_asignar(PEDIDO_REAL)
    assert fila["sinDesglose"] is True


def test_si_SOLO_ALGUNAS_lineas_se_clasifican_el_pedido_SI_cuenta():
    """«No se sabe» es cuando no se sabe NADA. Si una línea se reconoce, el
    pedido tiene desglose y se paga por lo que se reconoce — lo desconocido no
    incentiva, que es la decisión conservadora de siempre."""
    medio = dict(PEDIDO_REAL, items=[
        {"code": "B60D/I", "name": "BAJO 60", "quantity": 4, "price": 1200.0},
        {"code": "XX999", "name": "Algo raro", "quantity": 2, "price": 50.0},
    ])
    p = AC.normaliza_pedido(medio, 17.0, {"B60D/I": "BAJO"})
    assert p["sinDesglose"] is False
    assert p["muebles"] == 4


def test_una_linea_que_YA_TRAE_su_familia_no_necesita_catalogo():
    """Los pedidos nuevos la guardan (`BudgetTable` y `Presupuestador2` la
    mandan desde el 28/08), así que un pedido viejo sigue contando aunque el
    producto cambie de categoría o desaparezca del catálogo."""
    con_familia = dict(PEDIDO_REAL, items=[
        {"code": "B60D/I", "familia": "BAJO", "quantity": 4, "price": 1200.0},
        {"code": "P45", "familia": "PUERTAS", "quantity": 8, "price": 400.0},
    ])
    p = AC.normaliza_pedido(con_familia, 17.0)
    assert p["muebles"] == 4 and p["baseImponible"] == 1200.0
    assert p["sinDesglose"] is False


def test_la_familia_del_catalogo_NO_PISA_la_que_trae_la_linea():
    """Lo que se guardó con el pedido manda: es la foto del día en que se hizo."""
    linea = {"code": "B60D/I", "familia": "PUERTAS", "quantity": 1, "price": 10.0}
    p = AC.normaliza_pedido(dict(PEDIDO_REAL, items=[linea]), 0.0, {"B60D/I": "BAJO"})
    assert p["muebles"] == 0, (
        "el catálogo ha pisado la familia guardada en la línea")


def test_la_fuente_de_familias_SIN_COMISION_se_lee_de_verdad():
    """`_familias_que_no_son_mueble` importaba `FAMILIAS`, que no existe en
    `nomenclaturas_pdf` —se llama `FAM_META`—, y el `except` se lo tragaba: esa
    fuente NUNCA se leyó. Todo dependía de la red de seguridad escrita a mano.
    """
    from services.nomenclaturas_pdf import FAM_META
    lineales = {k for k, v in FAM_META.items()
                if isinstance(v, (list, tuple)) and len(v) > 1 and v[1] == "lineal"}
    assert lineales, "FAM_META ha dejado de marcar familias «lineal»"
    assert lineales <= set(C.FAMILIAS_SIN_COMISION), (
        f"estas familias lineales no están excluidas: "
        f"{lineales - set(C.FAMILIAS_SIN_COMISION)}. Costados y regletas no "
        "incentivan (master, 25/08)")
