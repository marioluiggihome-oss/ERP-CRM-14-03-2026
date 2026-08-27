# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO del calculo de almacen.

De aqui salen ordenes de compra y promesas de fecha. Los dos errores posibles
cuestan dinero en direcciones opuestas: comprar de mas es inmovilizado, y
comprar de menos es una obra parada con el montador ya alli.

Lo que se protege:

1. STOCK FISICO NO ES STOCK DISPONIBLE. Si hay 10 tableros y 8 estan
   comprometidos con otra cocina, quedan 2. Contar los 10 es exactamente como
   se llega al dia del montaje sin material: el sistema decia que habia, y
   habia, pero eran de otro.

2. NO SABER NO ES CERO. Sin dato de stock la respuesta es "ve a mirarlo", no
   "no hay". Un cero dispara una compra que quiza sobra.
"""
import importlib.util
import os

import pytest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture()
def al():
    ruta = os.path.join(BACKEND, "services", "almacen.py")
    spec = importlib.util.spec_from_file_location("_almacen", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ─── Stock físico vs disponible ─────────────────────────────────────────────

def test_lo_reservado_para_otros_no_esta_disponible(al):
    """CANDADO: la trampa principal."""
    assert al.disponible(stock=10, reservado_otros=8) == 2


def test_sin_reservas_todo_el_stock_esta_disponible(al):
    assert al.disponible(stock=10) == 10


def test_se_puede_estar_en_negativo(al):
    """Si se ha reservado mas de lo que hay, hay que verlo, no taparlo con un 0:
    significa que alguien prometio material que no existe."""
    assert al.disponible(stock=2, reservado_otros=5) == -3


def test_sin_dato_de_stock_no_se_sabe(al):
    assert al.disponible(stock=None, reservado_otros=3) is None
    assert al.disponible(stock="") is None


# ─── Cuánto hay que comprar ─────────────────────────────────────────────────

def test_lo_que_falta_descuenta_disponible_y_pedido(al):
    r = al.necesidad(necesario=10, stock=4, reservado_otros=1, pedido=2)
    assert r["disponible"] == 3          # 4 - 1
    assert r["pendiente"] == 5           # 10 - 3 - 2
    assert r["cubierto"] is False


def test_si_sobra_material_no_hay_que_comprar(al):
    r = al.necesidad(necesario=2, stock=10)
    assert r["pendiente"] == 0 and r["cubierto"] is True


def test_lo_pendiente_nunca_es_negativo(al):
    """Que sobren 8 no significa "comprar -8": significa comprar cero."""
    assert al.necesidad(necesario=2, stock=10)["pendiente"] == 0


def test_sin_dato_de_stock_no_se_inventa_una_compra(al):
    """CANDADO: la segunda trampa. Sin stock conocido, ni 'faltan 10' ni
    'no falta nada' --- hay que ir a mirarlo."""
    r = al.necesidad(necesario=10, stock=None)
    assert r["pendiente"] is None
    assert r["cubierto"] is None
    assert "mirarlo" in r["motivo"]


def test_el_desglose_viene_entero(al):
    """El numero solo ("faltan 3") no deja comprobar de donde sale."""
    r = al.necesidad(necesario=10, stock=4, reservado_otros=1, pedido=2)
    for k in ("necesario", "disponible", "pedido", "pendiente"):
        assert k in r


# ─── Reposición ─────────────────────────────────────────────────────────────

def test_avisa_cuando_lo_disponible_baja_del_minimo(al):
    assert al.necesita_reposicion(stock=10, reservado_otros=9, minimo=5) is True


def test_no_avisa_si_hay_de_sobra(al):
    assert al.necesita_reposicion(stock=10, reservado_otros=0, minimo=5) is False


def test_el_minimo_se_mide_contra_lo_disponible_no_contra_la_estanteria(al):
    """CANDADO: con 10 en la estanteria y minimo 5 parece que sobra, pero si 9
    estan reservados queda 1 y hay que reponer."""
    assert al.necesita_reposicion(stock=10, reservado_otros=9, minimo=5) is True


def test_sin_minimo_definido_no_se_avisa(al):
    """Un aviso inventado se aprende a ignorar, y entonces tampoco se ven los
    de verdad."""
    assert al.necesita_reposicion(stock=0, minimo=None) is False


def test_sin_dato_de_stock_no_se_avisa_de_reposicion(al):
    assert al.necesita_reposicion(stock=None, minimo=5) is False


# ─── Plan de compra ─────────────────────────────────────────────────────────

def test_separa_lo_que_falta_de_lo_que_no_se_sabe(al):
    r = al.plan_de_compra([
        {"referencia": "TAB19", "necesario": 10, "stock": 2},
        {"referencia": "BIS35", "necesario": 4, "stock": 100},
        {"referencia": "PAT10", "necesario": 8, "stock": None},
    ])
    assert len(r["pendientes"]) == 1 and r["pendientes"][0]["referencia"] == "TAB19"
    assert len(r["sinDato"]) == 1 and r["sinDato"][0]["referencia"] == "PAT10"
    assert r["cubiertas"] == 1
    assert r["hayQueComprar"] is True


def test_las_referencias_sin_dato_NO_cuentan_como_cubiertas(al):
    """CANDADO: mezclarlas daria por resuelto lo que ni se ha mirado."""
    r = al.plan_de_compra([{"referencia": "X", "necesario": 5, "stock": None}])
    assert r["cubiertas"] == 0
    assert "SIN dato" in r["resumen"]


def test_todo_cubierto_lo_dice_claro(al):
    r = al.plan_de_compra([{"referencia": "X", "necesario": 1, "stock": 10}])
    assert r["hayQueComprar"] is False
    assert "Todo cubierto" in r["resumen"]


def test_lista_vacia_no_revienta(al):
    r = al.plan_de_compra([])
    assert r["hayQueComprar"] is False and r["cubiertas"] == 0
    assert al.plan_de_compra(None)["hayQueComprar"] is False
