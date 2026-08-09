# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO del enganche entre los tres presupuestadores.

EL FALLO QUE PROTEGE, Y NO DABA NINGUN ERROR
--------------------------------------------
Una linea de material puede venir de tres sitios y cada uno la escribe con
otros nombres:

    Cocina Montada 1 y 2 →  code / productCode  ·  quantity / qty
    Cocina Desmontada    →  cod                 ·  cantidad
    Despiece y armarios  →  referencia          ·  cantidad

El almacen y la validacion tecnica solo miraban `code` y `productCode`. O sea
que **una proforma entera de Cocina Desmontada era invisible**: el plan de
compra contestaba «ninguna linea trae referencia» y la validacion daba por
bueno un proyecto sin haber mirado un solo codigo.

Y no fallaba nada. Simplemente no encontraba nada, que es peor.

Lo que se protege:

1. LOS TRES ORIGENES SE LEEN IGUAL. Es el candado principal: si alguien vuelve
   a mirar solo `code`, un modulo entero se queda fuera del almacen sin que
   nadie se entere.

2. NO SE INVENTA UN CODIGO. Una linea sin codigo devuelve vacio; no se rellena
   con la descripcion ni con «MANUAL», que la haria pasar por buena.

3. SIN CANTIDAD ES UNA, NO CERO. Cero la borra del plan de compra en silencio.

4. LAS LINEAS DESCARTADAS EN PANTALLA NO ENTRAN. Y se filtran por posicion, que
   es como las guarda la proforma.
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
def lp():
    return _cargar("_linea_pedido", "linea_pedido.py")


@pytest.fixture()
def ad():
    return _cargar("_almacen_datos_lp", "almacen_datos.py")


@pytest.fixture()
def vf():
    return _cargar("_validacion_lp", "validacion_fabricacion.py")


# Una linea de cada presupuestador, tal como la escribe cada uno.
MONTADA_1 = {"code": "B60D", "quantity": 2, "name": "Bajo 60 dcha"}
MONTADA_2 = {"productCode": "B60D", "qty": 2, "productName": "Bajo 60 dcha"}
DESMONTADA = {"cod": "B60D", "cantidad": 2, "descripcion": "BAJO 60 2 PUERTAS"}
DESPIECE = {"referencia": "B60D", "cantidad": 2}


# ─── 1. Los tres origenes se leen igual ─────────────────────────────────────

@pytest.mark.parametrize("linea,de_donde", [
    (MONTADA_1, "Cocina Montada 1"),
    (MONTADA_2, "Cocina Montada 2"),
    (DESMONTADA, "Cocina Desmontada"),
    (DESPIECE, "despiece"),
])
def test_el_codigo_y_las_unidades_se_leen_venga_de_donde_venga(lp, linea, de_donde):
    """CANDADO PRINCIPAL."""
    assert lp.codigo(linea) == "B60D", f"no se lee el codigo de {de_donde}"
    assert lp.cantidad(linea) == 2, f"no se leen las unidades de {de_donde}"


def test_el_almacen_ve_una_proforma_de_cocina_desmontada(ad):
    """Era el fallo: el plan de compra decia «ninguna linea trae referencia»
    delante de una proforma entera."""
    nec = ad.necesidades_del_despiece([DESMONTADA, {"cod": "A90", "cantidad": 1}])
    assert nec == {"B60D": 2, "A90": 1}


def test_el_almacen_suma_la_misma_referencia_venga_de_donde_venga(ad):
    """Un proyecto puede llevar lineas de dos presupuestadores a la vez."""
    assert ad.necesidades_del_despiece([MONTADA_1, DESMONTADA]) == {"B60D": 4}


def test_la_validacion_ve_los_codigos_de_cocina_desmontada(vf):
    """Antes daba por bueno un proyecto de Desmontada sin mirarle un codigo, o
    lo marcaba entero como «sin codigo». Las dos cosas mienten."""
    proyecto = {"itemsMontada": [], "itemsDespiece": [DESMONTADA]}
    check = next(c for c in vf.validar(proyecto)["checks"] if c["clave"] == "codigos")
    assert check["estado"] == vf.OK


def test_la_validacion_nombra_la_linea_de_desmontada_por_su_codigo(vf):
    """Un aviso que dice «linea 7» obliga a repasar el pedido entero."""
    proyecto = {"itemsDespiece": [{"cod": "", "descripcion": "COSTADO VISTO"}]}
    check = next(c for c in vf.validar(proyecto)["checks"] if c["clave"] == "codigos")
    assert "COSTADO VISTO" in check["detalle"]


def test_la_mano_sin_decidir_se_ve_tambien_en_desmontada(vf):
    proyecto = {"itemsDespiece": [{"cod": "B60D/I", "cantidad": 1}]}
    check = next(c for c in vf.validar(proyecto)["checks"] if c["clave"] == "apertura")
    assert check["estado"] == vf.FALTA and check["bloquea"] is True


# ─── 2. No se inventa un codigo ─────────────────────────────────────────────

def test_una_linea_sin_codigo_devuelve_vacio(lp):
    """Rellenarlo con la descripcion la haria pasar por buena en el plan de
    compra, y ahi es justo la que hay que mirar a mano."""
    assert lp.codigo({"descripcion": "PORTE"}) == ""
    assert lp.codigo({}) == ""


def test_las_lineas_sin_codigo_se_listan_aparte(lp):
    lineas = [MONTADA_1, {"descripcion": "PORTE"}, {"name": "Trabajo a medida"}]
    assert lp.sin_codigo(lineas) == ["PORTE", "Trabajo a medida"]


def test_para_nombrar_una_linea_manda_el_codigo(lp):
    assert lp.identificar(DESMONTADA, 6) == "B60D"
    assert lp.identificar({"descripcion": "PORTE"}, 6) == "PORTE"
    assert lp.identificar({}, 6) == "línea 7"


# ─── 3. Sin cantidad es UNA, no cero ────────────────────────────────────────

def test_sin_cantidad_cuenta_una(lp):
    assert lp.cantidad({"cod": "B60D"}) == 1


def test_una_cantidad_vacia_tampoco_es_cero(lp):
    assert lp.cantidad({"cod": "B60D", "cantidad": ""}) == 1


def test_un_cero_escrito_a_mano_SI_se_respeta(lp):
    """Distinto de «no consta»: alguien ha escrito un cero a proposito, y el
    almacen ya sabe que hacer con el."""
    assert lp.cantidad({"cod": "B60D", "cantidad": 0}) == 0


# ─── 4. Las lineas descartadas en pantalla no entran ────────────────────────

def test_normalizar_deja_fuera_las_lineas_borradas(lp):
    lineas = [DESMONTADA, {"cod": "A90", "cantidad": 1}, {"cod": "Z10", "cantidad": 3}]
    salida = lp.normalizar(lineas, quitar=[1])
    assert [l["referencia"] for l in salida] == ["B60D", "Z10"]


def test_normalizar_guarda_de_que_fila_venia_cada_una(lp):
    """Para poder volver a la linea de la pantalla de donde salio."""
    salida = lp.normalizar([DESMONTADA, {"cod": "A90"}], quitar=[0])
    assert salida[0]["indice"] == 1


def test_normalizar_no_revienta_con_indices_raros(lp):
    salida = lp.normalizar([DESMONTADA], quitar=["a", None, "0"])
    assert salida == [], "el «0» en texto es una fila descartada de verdad"


def test_sin_lineas_no_revienta(lp):
    assert lp.normalizar(None) == [] and lp.sin_codigo(None) == []
