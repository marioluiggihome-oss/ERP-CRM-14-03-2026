# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
"""Ejecuta detección normalizada -> catálogo -> precio con medidas reales."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from services.kitchen_geometry import validar_distribucion
from services.distribucion_a_mv import distribucion_a_relacion, reaplica_alturas, notacion_de
from services.mv_relacion import parse_relacion_text


def cocina(eid, **datos):
    return {"tipo": "lineal", "paredes": [{"ancho": 60, "alto": 260, "ancho_escrito": True}],
            "elementos": [{"id": eid, "ancho": 60, "posicion_cm": 0, "pared_idx": 0,
                           "medida_escrita": True, **datos}]}


def test_altos_del_dibujo_y_presupuesto_coinciden_a_90():
    d = validar_distribucion(cocina("alto"))
    assert d["elementos"][0]["alto"] == 90
    r = distribucion_a_relacion(d)
    assert r["lineas"][0]["alto"] == 90
    assert parse_relacion_text(notacion_de(r["lineas"]), "T1")[0]["alto"] == 90


def test_bajo_70_expreso_se_conserva_al_retarifar():
    d = validar_distribucion(cocina("bajo", alto=70))
    r = distribucion_a_relacion(d)
    assert r["lineas"][0]["alto"] == 70
    assert parse_relacion_text(r["notacion"], "T1")[0]["alto"] == 70
    assert reaplica_alturas(r["lineas"], 90, 220)[0]["alto"] == 70
    assert validar_distribucion(cocina("bajo"))["elementos"][0]["alto"] == 80


def test_altura_incoherente_no_se_presupuesta():
    d = validar_distribucion(cocina("bajo", alto=72))
    r = distribucion_a_relacion(d)
    assert not r["lineas"] and r["sin_codigo"]


def test_ancho_provisional_no_se_convierte_en_pedido():
    r = distribucion_a_relacion(cocina("bajo", ancho_desconocido=True))
    assert not r["lineas"] and r["sin_codigo"]
    d = validar_distribucion(cocina("bajo", ancho_desconocido=True))
    assert d["elementos"][0]["ancho_desconocido"]
    assert not distribucion_a_relacion(d)["lineas"]
    r = distribucion_a_relacion(cocina("bajo", ancho=60.5))
    assert not r["lineas"] and r["sin_codigo"]


def test_sobremodulo_no_hereda_90_ni_precio_sin_ficha():
    r = distribucion_a_relacion(cocina("sobremodulo", alto=35))
    assert not r["lineas"] and "Sobremódulo" in r["sin_codigo"][0]["motivo"]


def test_columna_mantiene_ancho_y_altura_en_el_presupuesto():
    d = validar_distribucion(cocina("columna_frigo", alto=200))
    r = distribucion_a_relacion(d)
    t = parse_relacion_text(r["notacion"], "T1")[0]
    assert d["elementos"][0]["alto"] == t["alto"] == 200
    assert d["elementos"][0]["ancho"] == t["ancho"] == 60


def test_repartos_expresos_no_se_confunden():
    for eid, prefijo in [("bajo_2_gavetas_1_cajon", "BGC"),
                         ("bajo_3_cajones_1_gaveta", "BCG"), ("bajo_5_cajones", "BC")]:
        r = distribucion_a_relacion(validar_distribucion(cocina(eid)))
        assert r["lineas"][0]["codigo"].startswith(prefijo + "60")
        assert not r["lineas"][0]["confirmar_familia"]
        assert parse_relacion_text(r["notacion"], "T1")[0]["pvp"] > 0
