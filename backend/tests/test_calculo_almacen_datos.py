# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO de las existencias y las reservas del almacen.

El motor de calculo (`almacen.py`) ya sabia decir que hay que comprar; esto es
lo que le da los datos. Si esta capa se equivoca, el motor calcula
perfectamente sobre numeros que no son.

Y los dos errores posibles cuestan dinero en direcciones opuestas: comprar de
mas es inmovilizado, y comprar de menos es una obra parada con el montador ya
alli.

Lo que se protege:

1. LO MIO NO CUENTA COMO RESERVADO POR OTROS. Al mirar si a P-482 le falta
   material, lo que tienen apartado los DEMAS resta; lo que ella misma tiene
   reservado NO, o se restaria dos veces y saldria una compra que no hace
   falta. Parece obvio escrito: es exactamente el error de juntar las dos
   listas sin mirar de quien es cada reserva.

2. UNA REFERENCIA REPETIDA SE SUMA. La misma referencia viene en varias lineas
   del despiece. Mirandolas de una en una, todas parecen cubiertas con el mismo
   tablero y al final falta material: es el mismo tablero contado tres veces.

3. SIN FICHA NO SE INVENTA UN CERO. Una referencia que nadie ha dado de alta
   tiene stock desconocido, no stock cero. Cero dispara una compra que quiza
   sobra; «no se sabe» manda a alguien a la estanteria.

4. LA REFERENCIA SE CRUZA NORMALIZADA. Las fichas se teclean a mano: « b60d »
   y «B60D» son la misma pieza. Sin normalizar, la reserva de una y el stock de
   la otra no se encuentran y el resultado sale mal sin que nada falle.
"""
import importlib.util
import os

import pytest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _cargar(nombre, fichero):
    ruta = os.path.join(BACKEND, "services", fichero)
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def ad():
    return _cargar("_almacen_datos", "almacen_datos.py")


@pytest.fixture()
def al():
    return _cargar("_almacen", "almacen.py")


# ─── 1. Lo mio no cuenta como reservado por otros ───────────────────────────

def test_lo_reservado_por_mi_proyecto_no_resta(ad):
    """CANDADO PRINCIPAL. Si lo mio restara, saldria una compra de material que
    ya tengo apartado."""
    reservas = [
        {"referencia": "B60D", "proyecto": "P-482", "cantidad": 4},
        {"referencia": "B60D", "proyecto": "P-491", "cantidad": 3},
    ]
    assert ad.reservado_para_otros(reservas, "P-482") == {"B60D": 3}


def test_lo_reservado_por_los_demas_si_resta(ad):
    reservas = [{"referencia": "B60D", "proyecto": "P-491", "cantidad": 3},
                {"referencia": "B60D", "proyecto": "P-503", "cantidad": 2}]
    assert ad.reservado_para_otros(reservas, "P-482") == {"B60D": 5}


def test_una_reserva_sin_cantidad_no_resta_nada(ad):
    reservas = [{"referencia": "B60D", "proyecto": "P-491", "cantidad": None}]
    assert ad.reservado_para_otros(reservas, "P-482") == {}


def test_el_proyecto_se_compara_normalizado(ad):
    """« p-482 » y «P-482» son el mismo proyecto. Si no se normaliza, lo suyo
    se le cuenta como ajeno y compra de mas."""
    reservas = [{"referencia": "B60D", "proyecto": " p-482 ", "cantidad": 4}]
    assert ad.reservado_para_otros(reservas, "P-482") == {}


# ─── 2. Una referencia repetida se suma ─────────────────────────────────────

def test_la_misma_referencia_en_varias_lineas_se_suma(ad):
    """Mirandolas de una en una, todas parecen cubiertas con el mismo tablero."""
    lineas = [{"code": "B60D", "quantity": 2},
              {"code": "B60D", "quantity": 3},
              {"code": "A60D", "quantity": 1}]
    assert ad.necesidades_del_despiece(lineas) == {"B60D": 5, "A60D": 1}


def test_una_linea_sin_cantidad_cuenta_como_una(ad):
    """Es lo que significa una linea suelta en un pedido. Cero la haria
    desaparecer del plan de compra."""
    assert ad.necesidades_del_despiece([{"code": "B60D"}]) == {"B60D": 1}


def test_una_linea_sin_referencia_se_ignora(ad):
    assert ad.necesidades_del_despiece([{"quantity": 5}]) == {}


def test_las_referencias_se_cruzan_normalizadas(ad):
    lineas = [{"code": " b60d "}, {"code": "B60D"}]
    assert ad.necesidades_del_despiece(lineas) == {"B60D": 2}


# ─── 3. Sin ficha no se inventa un cero ─────────────────────────────────────

def test_una_referencia_sin_ficha_queda_con_stock_desconocido(ad):
    lineas = ad.montar_lineas({"B60D": 5}, fichas=[], reservas=[], proyecto="P-482")
    assert lineas[0]["stock"] is None, (
        "se ha inventado un stock: cero dispara una compra que quiza sobra")


def test_una_ficha_sin_stock_tampoco_vale_cero(ad):
    fichas = [{"referencia": "B60D", "stock": "", "minimo": 2}]
    idx = ad.stock_por_referencia(fichas)
    assert idx["B60D"]["stock"] is None


def test_el_motor_dice_ve_a_mirarlo_y_no_da_por_cubierto(ad, al):
    """La capa de datos y el motor tienen que entenderse: un `None` de aqui
    tiene que salir en `sinDato` alli, NO entre las cubiertas."""
    lineas = ad.montar_lineas({"B60D": 5}, fichas=[], reservas=[], proyecto="P-482")
    plan = al.plan_de_compra(lineas)
    assert len(plan["sinDato"]) == 1
    assert plan["cubiertas"] == 0
    assert "SIN dato de stock" in plan["resumen"]


def test_se_listan_aparte_las_referencias_que_nadie_ha_dado_de_alta(ad):
    """No es lo mismo una referencia que existe y esta a cero que una que nadie
    ha creado todavia."""
    fichas = [{"referencia": "B60D", "stock": 0}]
    assert ad.sin_ficha({"B60D": 1, "A90": 2}, fichas) == ["A90"]


# ─── 4. El enganche completo, de punta a punta ──────────────────────────────

def test_el_caso_del_traspaso_de_punta_a_punta(ad, al):
    """Diez tableros en la estanteria, ocho de otra cocina: quedan dos.

    Es el ejemplo que abre `almacen.py`, y aqui se comprueba que la capa de
    datos lo alimenta bien.
    """
    necesidades = ad.necesidades_del_despiece([{"code": "TAB19", "quantity": 5}])
    fichas = [{"referencia": "TAB19", "stock": 10, "minimo": 3}]
    reservas = [{"referencia": "TAB19", "proyecto": "P-491", "cantidad": 8}]
    lineas = ad.montar_lineas(necesidades, fichas, reservas, proyecto="P-482")

    assert lineas[0]["stock"] == 10
    assert lineas[0]["reservadoOtros"] == 8
    plan = al.plan_de_compra(lineas)
    # Disponible 2, necesita 5 -> faltan 3.
    assert plan["pendientes"][0]["pendiente"] == 3
    assert plan["hayQueComprar"] is True


def test_lo_que_viene_de_camino_cuenta(ad, al):
    necesidades = {"TAB19": 5}
    fichas = [{"referencia": "TAB19", "stock": 2}]
    lineas = ad.montar_lineas(necesidades, fichas, reservas=[], proyecto="P-482",
                              pedidos={"TAB19": 3})
    plan = al.plan_de_compra(lineas)
    assert plan["hayQueComprar"] is False, "ya viene de camino y sigue mandando comprar"


def test_mi_propia_reserva_no_me_hace_comprar_de_mas(ad, al):
    """El caso completo del candado 1: la cocina tiene 5 tableros apartados
    para ella misma y hay 5 en la estanteria. No hay que comprar nada."""
    necesidades = {"TAB19": 5}
    fichas = [{"referencia": "TAB19", "stock": 5}]
    reservas = [{"referencia": "TAB19", "proyecto": "P-482", "cantidad": 5}]
    lineas = ad.montar_lineas(necesidades, fichas, reservas, proyecto="P-482")
    plan = al.plan_de_compra(lineas)
    assert plan["hayQueComprar"] is False, (
        "se ha restado dos veces la reserva del propio proyecto: manda comprar "
        "material que ya tiene apartado")


def test_la_ubicacion_viaja_para_poder_ir_a_por_ello(ad):
    fichas = [{"referencia": "TAB19", "stock": 4, "ubicacion": "Estantería A3"}]
    lineas = ad.montar_lineas({"TAB19": 1}, fichas, [], "P-482")
    assert lineas[0]["ubicacion"] == "Estantería A3"


def test_sin_nada_que_necesitar_no_revienta(ad, al):
    assert ad.montar_lineas({}, [], [], "P-482") == []
    assert al.plan_de_compra([])["hayQueComprar"] is False
