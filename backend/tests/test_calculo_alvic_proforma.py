"""Proforma Alvic: el total de cada linea.

Protege el fallo del 03/08: el importe de la linea se guardaba como
`total = pvp`, ignorando las unidades. Una fila de 2 muebles contaba como una y
el presupuesto Alvic salia corto; de ahi el "no calcula bien".

Regla: manda el importe que trae la proforma; si no viene, precio x unidades.

Mongo, fitz y la IA se simulan: no hace falta ni base de datos ni red.
"""
import importlib.util
import os
import sys
import types

import pytest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture()
def cascos(monkeypatch):
    """Carga routes/cascos.py con lo pesado (Mongo, PyMuPDF, IA) simulado."""
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
    jwt.get_current_user = _req
    jwt.verify_access_token = lambda *a, **k: {"sub": "u1"}
    jwt.ADMIN_ROLE_FLAGS = ["isAdmin"]
    monkeypatch.setitem(sys.modules, "services.jwt_service", jwt)

    # PyMuPDF y la vision no se tocan en estas pruebas.
    monkeypatch.setitem(sys.modules, "fitz", types.ModuleType("fitz"))
    vision = types.ModuleType("services.llm_vision")

    async def _sin_ia(*a, **k):
        return ""
    vision.analyze_image_with_gemini = _sin_ia
    monkeypatch.setitem(sys.modules, "services.llm_vision", vision)

    rutas = types.ModuleType("routes")
    rutas.__path__ = [os.path.join(BACKEND, "routes")]
    monkeypatch.setitem(sys.modules, "routes", rutas)

    spec = importlib.util.spec_from_file_location(
        "routes.cascos", os.path.join(BACKEND, "routes", "cascos.py"))
    mod = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, "routes.cascos", mod)
    spec.loader.exec_module(mod)
    return mod


def _fila(**kw):
    base = {"n": 1, "cod": "80GF/1P1GIN", "descripcion": "BAJO 2 CAJONES",
            "material": "MELAMINA BLANCO", "largo": 800, "ancho": 720,
            "grueso": 580, "cantidad": 1, "pvp": 100.0}
    base.update(kw)
    return base


def test_dos_unidades_valen_el_doble(cascos):
    it = cascos._filas_a_items([_fila(cantidad=2, pvp=100.0)])[0]
    assert it["total"] == 200.0, "una linea de 2 unidades se contaba como una"
    assert it["pvp"] == 100.0, "el precio unitario tiene que seguir siendo el unitario"
    assert it["cantidad"] == 2


def test_manda_el_importe_de_la_proforma_si_viene(cascos):
    """Si la proforma trae su total (con su redondeo), ese es el bueno."""
    it = cascos._filas_a_items([_fila(cantidad=3, pvp=33.33, importe=99.98)])[0]
    assert it["total"] == 99.98


def test_una_unidad_se_queda_igual(cascos):
    it = cascos._filas_a_items([_fila(cantidad=1, pvp=402.73)])[0]
    assert it["total"] == 402.73


def test_sin_cantidad_se_cuenta_una(cascos):
    it = cascos._filas_a_items([_fila(cantidad=None, pvp=50.0)])[0]
    assert it["cantidad"] == 1.0 and it["total"] == 50.0


def test_una_cantidad_ilegible_no_rompe_la_importacion(cascos):
    it = cascos._filas_a_items([_fila(cantidad="dos", pvp=50.0)])[0]
    assert it["cantidad"] == 1.0 and it["total"] == 50.0


def test_sin_precio_no_se_inventa_un_total(cascos):
    """Regla del proyecto: lo que no se sabe NO se rellena con un numero."""
    it = cascos._filas_a_items([_fila(pvp=None, cantidad=2)])[0]
    assert it["pvp"] is None and it["total"] is None


def test_un_precio_ilegible_no_rompe_ni_inventa(cascos):
    it = cascos._filas_a_items([_fila(pvp="—", cantidad=2)])[0]
    assert it["pvp"] is None and it["total"] is None


def test_se_conservan_codigo_y_descripcion(cascos):
    """De ellos dependen la equivalencia ACB y a que proveedor se pide."""
    it = cascos._filas_a_items([_fila(cod="60BC", descripcion="BAJO CON BALDA 600")])[0]
    assert it["cod"] == "60BC"
    assert it["descripcion"] == "BAJO CON BALDA 600"
    assert it["tipo"] == "bajo", "sin tipo, la linea se queda sin casco equivalente"
