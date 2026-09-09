# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
"""Regresión de lectura textual: composición lineal con bajos, altos y sobremódulos."""
import importlib.util
import os
import sys
import types
import pytest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture()
def geom(monkeypatch):
    paquete = types.ModuleType("services")
    paquete.__path__ = [os.path.join(BACKEND, "services")]
    monkeypatch.setitem(sys.modules, "services", paquete)
    spec = importlib.util.spec_from_file_location(
        "services.kitchen_geometry", os.path.join(BACKEND, "services", "kitchen_geometry.py")
    )
    mod = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, "services.kitchen_geometry", mod)
    spec.loader.exec_module(mod)
    return mod


COMPOSICION = {
    "tipo": "lineal",
    "paredes": [{"nombre": "Pared única", "ancho": 469, "alto": 240, "ancho_escrito": True}],
    "elementos": [
        {"id": "frigorifico", "label": "Frigorífico francés negro", "pared_idx": 0, "ancho": 84, "fila": "bajo", "medida_escrita": True},
        {"id": "mueble", "label": "Bajo 30 cm, una puerta", "pared_idx": 0, "ancho": 30, "fila": "bajo", "medida_escrita": True},
        {"id": "cajonera", "label": "Bajo fregadero 90 cm, dos gavetas", "pared_idx": 0, "ancho": 90, "fila": "bajo", "medida_escrita": True},
        {"id": "lavavajillas", "label": "Lavavajillas 60 cm totalmente integrable", "pared_idx": 0, "ancho": 60, "fila": "bajo", "medida_escrita": True},
        {"id": "cajonera", "label": "Bajo placa 90 cm, dos gavetas", "pared_idx": 0, "ancho": 90, "fila": "bajo", "medida_escrita": True},
        {"id": "mueble", "label": "Bajo 15 cm", "pared_idx": 0, "ancho": 15, "fila": "bajo", "medida_escrita": True},
        {"id": "columna_hornos", "label": "Columna horno y microondas 60 cm", "pared_idx": 0, "ancho": 60, "fila": "bajo", "medida_escrita": True},
        {"id": "columna_escobero", "label": "Columna escobero 40 cm", "pared_idx": 0, "ancho": 40, "fila": "bajo", "medida_escrita": True},
        {"id": "sobremodulo", "label": "Sobremódulo sobre frigorífico", "pared_idx": 0, "ancho": 84, "fila": "alto", "fondo": 60, "medida_escrita": True},
        {"id": "alto", "label": "Alto 120 cm, dos puertas abatibles", "pared_idx": 0, "ancho": 120, "fila": "alto", "fondo": 35, "medida_escrita": True},
        {"id": "alto", "label": "Alto 60 cm, una puerta", "pared_idx": 0, "ancho": 60, "fila": "alto", "fondo": 35, "medida_escrita": True},
        {"id": "alto", "label": "Alto 115 cm, dos puertas abatibles", "pared_idx": 0, "ancho": 115, "fila": "alto", "fondo": 35, "medida_escrita": True},
        {"id": "sobremodulo", "label": "Sobremódulo 100 cm", "pared_idx": 0, "ancho": 100, "fila": "alto", "fondo": 60, "medida_escrita": True},
    ],
}


def test_composicion_lineal_conserva_tres_niveles_y_cotas(geom):
    resultado = geom.validar_distribucion(COMPOSICION)
    # La descripción contiene una inconsistencia real: los sobremódulos y altos
    # suman 479 cm, mientras que la pared/bajos suman 469 cm. No se corrige a
    # 469 ni se estrecha un módulo; se devuelve incidencia para revisión.
    assert resultado["ok"] is False
    assert "479" in resultado.get("motivo", "") or "no caben" in resultado.get("motivo", "").lower()
    assert COMPOSICION["tipo"] == "lineal"
    assert len(resultado["paredes"]) == 1
    bajos = [e for e in resultado["elementos"] if e["fila"] == "bajo"]
    altos = [e for e in resultado["elementos"] if e["fila"] == "alto"]
    assert sum(e["ancho"] for e in bajos) == 469
    assert [e["ancho"] for e in bajos] == [84, 30, 90, 60, 90, 15, 60, 40]
    assert [e["ancho"] for e in altos] == [84, 120, 60, 115, 100]
    assert altos[0]["fondo"] == 60
    assert all(e["fondo"] == 35 for e in altos[1:4])
    assert next(e for e in bajos if e["id"] == "lavavajillas")["ancho"] == 60


def test_sobremodulo_no_se_confunde_con_bajo(geom):
    assert geom.es_alto("sobremodulo", "Sobremódulo superior") is True
    assert geom.es_alto("columna_escobero", "Columna escobero") is False
    assert geom.fondo_modulo("sobremodulo") == 33
    assert geom.fondo_modulo("columna_escobero") == 58
