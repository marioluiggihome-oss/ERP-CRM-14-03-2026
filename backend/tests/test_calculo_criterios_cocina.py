# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""Criterio profesional: lo que un buen equipo miraria antes de pedir.

No inventa nada ni corrige por su cuenta: AVISA. Y avisa de lo que de verdad
para una obra o cuesta dinero: una altura que esta fabrica no fabrica, un ancho
que no existe en tarifa, o piezas que se olvidan siempre (el bajo del
fregadero, la campana, los remates de los extremos).

Las medidas de fabricacion salen de la memoria del proyecto.
"""
import importlib.util
import os
import sys
import types

import pytest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture()
def criterios(monkeypatch):
    servicios = types.ModuleType("services")
    servicios.__path__ = [os.path.join(BACKEND, "services")]
    monkeypatch.setitem(sys.modules, "services", servicios)
    spec = importlib.util.spec_from_file_location(
        "services.criterios_cocina", os.path.join(BACKEND, "services", "criterios_cocina.py"))
    mod = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, "services.criterios_cocina", mod)
    spec.loader.exec_module(mod)
    return mod


def _textos(avisos):
    return " · ".join(a["texto"] for a in avisos)


def _bajo(**kw):
    base = {"tipo": "BAJO", "subtipo": "1_PUERTA", "nombre": "BAJO 60",
            "ancho_estimado": 600, "alto_estimado": 80, "cantidad": 1}
    base.update(kw)
    return base


def test_un_bajo_que_no_mide_80_es_un_error_de_fabricacion(criterios):
    """En esta fabrica los bajos se hacen SOLO a 80 cm de casco."""
    avisos = criterios.revisar_composicion([_bajo(alto_estimado=72)])
    assert any(a["nivel"] == "error" for a in avisos)
    assert "80" in _textos(avisos)


def test_un_bajo_de_80_no_da_guerra(criterios):
    avisos = criterios.revisar_composicion([_bajo()])
    assert not any(a["nivel"] == "error" for a in avisos)


def test_un_alto_solo_puede_ser_de_70_o_90(criterios):
    avisos = criterios.revisar_composicion([
        {"tipo": "ALTO", "nombre": "ALTO 60", "ancho_estimado": 600, "alto_estimado": 80}])
    assert "70 o 90" in _textos(avisos)


def test_un_ancho_que_no_existe_en_tarifa_se_avisa(criterios):
    avisos = criterios.revisar_composicion([_bajo(ancho_estimado=630)])
    assert "fuera de los estándar" in _textos(avisos)
    assert "60" in _textos(avisos), "hay que decir cual seria el ancho bueno"


def test_un_ancho_estandar_no_molesta(criterios):
    for ancho in (300, 450, 600, 900, 1200):
        avisos = criterios.revisar_composicion([_bajo(ancho_estimado=ancho)])
        assert "fuera de los estándar" not in _textos(avisos), f"{ancho} es estandar"


def test_si_hay_fregadero_tiene_que_haber_mueble_debajo(criterios):
    avisos = criterios.revisar_composicion([
        {"tipo": "ELECTRODOMESTICO", "subtipo": "FREGADERO", "nombre": "FREGADERO"}])
    assert "bajo fregadero" in _textos(avisos)


def test_con_el_bajo_fregadero_puesto_no_se_avisa(criterios):
    avisos = criterios.revisar_composicion([
        _bajo(subtipo="BAJO_FREGADERO", nombre="BAJO FREGADERO 60")])
    assert "bajo fregadero" not in _textos(avisos)


def test_una_placa_sin_campana_se_avisa(criterios):
    avisos = criterios.revisar_composicion([
        {"tipo": "ELECTRODOMESTICO", "subtipo": "PLACA", "nombre": "PLACA INDUCCION"}])
    assert "campana" in _textos(avisos)


def test_una_cocina_solo_de_bajos_hace_sospechar(criterios):
    avisos = criterios.revisar_composicion([_bajo(), _bajo(), _bajo()])
    assert "Solo se han detectado muebles bajos" in _textos(avisos)


def test_los_remates_de_los_extremos_se_recuerdan(criterios):
    """Costados vistos y regletas: son pedido y se olvidan casi siempre."""
    avisos = criterios.revisar_composicion([_bajo() for _ in range(4)])
    assert "costados vistos ni regletas" in _textos(avisos)


def test_con_costado_visto_ya_no_lo_recuerda(criterios):
    muebles = [_bajo() for _ in range(4)] + [
        {"tipo": "COSTADO", "nombre": "COSTADO VISTO", "ancho_estimado": 600}]
    avisos = criterios.revisar_composicion(muebles)
    assert "costados vistos ni regletas" not in _textos(avisos)


def test_una_composicion_vacia_no_inventa_avisos(criterios):
    assert criterios.revisar_composicion([]) == []


def test_no_se_repite_el_mismo_aviso_una_vez_por_mueble(criterios):
    """Diez bajos mal medidos son UN aviso, no diez lineas iguales."""
    avisos = criterios.revisar_composicion([_bajo(alto_estimado=72) for _ in range(10)])
    assert len([a for a in avisos if "80 cm" in a["texto"]]) == 1


def test_las_medidas_de_fabrica_son_las_de_la_casa(criterios):
    """Si alguien cambia estos numeros, cambia lo que se fabrica."""
    e = criterios.ESTANDARES
    assert e["casco_bajo_alto"] == 800
    assert e["casco_alto_alturas"] == (700, 900)
    assert e["columna_alturas"] == (2000, 2200)
    assert e["fondo_alto"] == 330 and e["fondo_bajo"] == 580
    assert e["encimera_a_alto"] == (550, 600)
