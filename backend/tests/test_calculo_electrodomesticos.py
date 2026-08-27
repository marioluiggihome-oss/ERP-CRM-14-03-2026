# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""¿Mueble o aparato? De esto depende que una línea entre o no en el presupuesto.

Reglas de la casa:
  · Un BAJO FREGADERO o un BAJO HORNO son MUEBLES que fabricamos: el aparato va
    dentro. Contarlos como electrodoméstico los sacaba del presupuesto.
  · El LAVAVAJILLAS va en un HUECO, sin casco: es electrodoméstico aunque la IA
    lo etiquete como bajo.
  · Una PUERTA de integración ("puerta lavavajillas") SÍ es material nuestro:
    es un frente, y cuenta como una puerta.
"""
import importlib.util
import os
import sys
import types

import pytest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture()
def ia_lab(monkeypatch):
    if "python_multipart" not in sys.modules:
        pm = types.ModuleType("python_multipart")
        pm.__version__ = "0.0.20"
        monkeypatch.setitem(sys.modules, "python_multipart", pm)
    servicios = types.ModuleType("services")
    servicios.__path__ = [os.path.join(BACKEND, "services")]
    monkeypatch.setitem(sys.modules, "services", servicios)
    dbc = types.ModuleType("services.db_client")
    dbc.get_db = lambda: None
    monkeypatch.setitem(sys.modules, "services.db_client", dbc)
    jwt = types.ModuleType("services.jwt_service")

    async def _req():
        return {"id": "u1", "isAdmin": True}
    jwt.require_auth = _req
    monkeypatch.setitem(sys.modules, "services.jwt_service", jwt)
    rutas = types.ModuleType("routes")
    rutas.__path__ = [os.path.join(BACKEND, "routes")]
    monkeypatch.setitem(sys.modules, "routes", rutas)
    spec = importlib.util.spec_from_file_location(
        "routes.ia_lab", os.path.join(BACKEND, "routes", "ia_lab.py"))
    mod = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, "routes.ia_lab", mod)
    spec.loader.exec_module(mod)
    return mod


def test_el_bajo_fregadero_es_un_mueble(ia_lab):
    assert ia_lab.es_electrodomestico(
        {"tipo": "BAJO", "subtipo": "BAJO_FREGADERO", "nombre": "BAJO FREGADERO 60"}) is False


def test_el_bajo_horno_es_un_mueble(ia_lab):
    assert ia_lab.es_electrodomestico(
        {"tipo": "BAJO", "subtipo": "BAJO_HORNO", "nombre": "BAJO HORNO 60"}) is False


def test_el_lavavajillas_es_electrodomestico_aunque_lo_llamen_bajo(ia_lab):
    """Va en un hueco: no lleva casco, no se fabrica."""
    assert ia_lab.es_electrodomestico(
        {"tipo": "BAJO", "subtipo": "LAVAVAJILLAS", "nombre": "LAVAV 60"}) is True


def test_la_puerta_del_lavavajillas_si_es_material_nuestro(ia_lab):
    assert ia_lab.es_electrodomestico(
        {"tipo": "PUERTA", "subtipo": "PUERTA_LAVAVAJILLAS",
         "nombre": "PUERTA LAVAVAJILLAS 60"}) is False


def test_un_frente_de_integracion_tampoco_es_aparato(ia_lab):
    assert ia_lab.es_electrodomestico(
        {"tipo": "PANEL", "subtipo": "", "nombre": "PUERTA DE INTEGRACION 60"}) is False


def test_el_horno_suelto_si_es_electrodomestico(ia_lab):
    assert ia_lab.es_electrodomestico(
        {"tipo": "ELECTRODOMESTICO", "subtipo": "HORNO", "nombre": "HORNO"}) is True


def test_la_campana_es_electrodomestico(ia_lab):
    assert ia_lab.es_electrodomestico({"tipo": "", "subtipo": "CAMPANA", "nombre": "CAMPANA 60"}) is True


def test_un_alto_normal_no_es_electrodomestico(ia_lab):
    assert ia_lab.es_electrodomestico(
        {"tipo": "ALTO", "subtipo": "1_PUERTA", "nombre": "ALTO 60"}) is False
