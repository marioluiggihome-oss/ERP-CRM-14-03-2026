# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO del comparador presupuestado vs fabricado.

Este calculo existe para pillar el fallo caro: que se presupuesten unas cosas y
se fabriquen otras. Si el comparador se equivoca, se equivoca en la direccion
peor --- decir "todo cuadra" cuando no cuadra --- y entonces es peor que no
tenerlo, porque da tranquilidad falsa.

Dos trampas que se protegen:

1. EMPAREJAR A LA FUERZA. Dos lineas que se parecen no son la misma linea. Si
   el comparador junta un bajo de 600 con uno de 800 "porque son los que
   quedaban", esconde exactamente el error que se busca.

2. AFIRMAR SIN LAS DOS PUNTAS. Si un dato falta en un lado, eso no es un
   cambio: es que no consta. Decir "el acabado cambio de roble a nada" seria
   inventarse una diferencia.
"""
import importlib.util
import os

import pytest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture()
def cf():
    ruta = os.path.join(BACKEND, "services", "comparador_fabricacion.py")
    spec = importlib.util.spec_from_file_location("_comparador_fab", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def L(code="", qty=1, w=None, h=None, d=None, mat="", puerta="", tipo="cocina", nombre=""):
    return {"productCode": code, "quantity": qty, "width": w, "height": h, "depth": d,
            "material": mat, "doorFinish": puerta, "itemType": tipo, "productName": nombre}


# ─── Lo que tiene que cuadrar ───────────────────────────────────────────────

def test_dos_listas_identicas_cuadran(cf):
    items = [L("B60", 2, 60, 80), L("A60", 1, 60, 70)]
    r = cf.comparar(items, items)
    assert r["hayDiferencias"] is False
    assert r["iguales"] == 2
    assert "Todo cuadra" in r["resumen"]


def test_dos_listas_vacias_no_revientan(cf):
    r = cf.comparar([], [])
    assert r["hayDiferencias"] is False and r["iguales"] == 0
    assert cf.comparar(None, None)["hayDiferencias"] is False


# ─── El caso que motiva todo esto ───────────────────────────────────────────

def test_cinco_de_600_presupuestados_y_cuatro_mas_uno_de_800_fabricados(cf):
    """El ejemplo exacto del que salio esta funcion."""
    presupuestado = [L("B60", 5, 60, 80)]
    fabricado = [L("B60", 4, 60, 80), L("B80", 1, 80, 80)]

    r = cf.comparar(presupuestado, fabricado)
    assert r["hayDiferencias"] is True

    # El B60 se empareja y se ve que faltan unidades.
    assert len(r["cambiados"]) == 1
    dif = r["cambiados"][0]["diferencias"][0]
    assert dif["campo"] == "unidades" and dif["antes"] == 5 and dif["despues"] == 4

    # Y el de 800 aparece como fabricado sin estar presupuestado.
    assert len(r["soloFabricacion"]) == 1
    assert r["soloFabricacion"][0]["codigo"] == "B80"
    assert not r["soloPresupuesto"]


# ─── No emparejar a la fuerza ───────────────────────────────────────────────

def test_no_junta_dos_lineas_distintas_solo_porque_sobren(cf):
    """CANDADO: un bajo de 600 y uno de 800 NO son la misma linea, aunque sean
    los unicos que quedan sin pareja."""
    r = cf.comparar([L("B60", 1, 60, 80)], [L("B80", 1, 80, 80)])
    assert len(r["soloPresupuesto"]) == 1
    assert len(r["soloFabricacion"]) == 1
    assert not r["cambiados"], "no puede presentarlo como 'una linea que cambio de ancho'"


def test_sin_codigo_empareja_por_forma(cf):
    """Sin codigo a ninguno de los dos lados, se reconoce por tipo+ancho+alto,
    que es como lo reconoce una persona mirando el plano."""
    r = cf.comparar([L("", 2, 60, 80, mat="blanco")], [L("", 2, 60, 80, mat="roble")])
    assert len(r["cambiados"]) == 1
    assert r["cambiados"][0]["diferencias"][0]["campo"] == "material"


def test_sin_codigo_y_sin_medidas_no_se_empareja_a_ciegas(cf):
    r = cf.comparar([L("", 1)], [L("", 1)])
    assert len(r["soloPresupuesto"]) == 1 and len(r["soloFabricacion"]) == 1


# ─── No afirmar sin las dos puntas ──────────────────────────────────────────

def test_un_dato_que_falta_no_es_un_cambio(cf):
    """CANDADO: si el acabado no consta en fabricacion, NO se dice que 'cambio
    a nada'. Eso seria inventarse una diferencia."""
    r = cf.comparar([L("B60", 1, 60, 80, puerta="roble")],
                    [L("B60", 1, 60, 80, puerta="")])
    assert r["hayDiferencias"] is False, "un hueco no es una diferencia"


def test_una_medida_ausente_tampoco_afirma_nada(cf):
    r = cf.comparar([L("B60", 1, 60, 80)], [L("B60", 1, 60, None)])
    assert not r["cambiados"]


# ─── Diferencias reales ─────────────────────────────────────────────────────

def test_detecta_cambio_de_acabado(cf):
    r = cf.comparar([L("B60", 1, 60, 80, puerta="roble")],
                    [L("B60", 1, 60, 80, puerta="blanco")])
    d = r["cambiados"][0]["diferencias"][0]
    assert d["campo"] == "acabado de puerta" and d["antes"] == "roble" and d["despues"] == "blanco"


def test_el_acabado_no_distingue_mayusculas(cf):
    r = cf.comparar([L("B60", 1, 60, 80, puerta="Roble")],
                    [L("B60", 1, 60, 80, puerta="roble")])
    assert r["hayDiferencias"] is False


def test_linea_presupuestada_que_no_se_fabrica(cf):
    r = cf.comparar([L("B60", 1, 60, 80), L("A90", 1, 90, 70)], [L("B60", 1, 60, 80)])
    assert len(r["soloPresupuesto"]) == 1
    assert r["soloPresupuesto"][0]["codigo"] == "A90"
    assert "NO se fabrican" in r["resumen"]


# ─── El aviso de unidades ───────────────────────────────────────────────────

def test_avisa_si_huele_a_centimetros_contra_milimetros(cf):
    """600 frente a 60 no es "el mueble encogio": es que alguien mezclo mm y cm.
    Presentarlo como un cambio real mandaria a buscar un fallo que no existe."""
    r = cf.comparar([L("B60", 1, 60, 80)], [L("B60", 1, 600, 80)])
    assert r["posibleLioDeUnidades"] is True
    assert r["cambiados"][0]["diferencias"][0]["unidades"] is True


def test_un_cambio_normal_no_se_marca_como_lio_de_unidades(cf):
    r = cf.comparar([L("B60", 1, 60, 80)], [L("B60", 1, 80, 80)])
    assert r["posibleLioDeUnidades"] is False
