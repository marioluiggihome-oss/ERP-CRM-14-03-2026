# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""Geometría del alzado: la suma CUADRA y los altos no roban sitio a los bajos.

Caso real del master (05/08/2026): pared de 324 cm y un alzado con 415 cm de
módulos dibujados, saliéndose de la pared, con la cota total diciendo 324. Dos
fallos encadenados:

1. Los muebles ALTOS entraban en la misma fila que los bajos. Un alzado tiene
   DOS filas independientes —la de suelo y la colgada— y cada una ocupa el
   ancho de la pared por su cuenta. Al mezclarlas, los 105 cm de altos se
   sumaban al suelo y la pared "se alargaba".
2. Cuando la suma no cuadraba, el validador avisaba… y devolvía `ok: True`. Se
   dibujaba igual. Un alzado con muebles fuera de la pared es peor que no tener
   alzado, porque parece bueno y se manda al taller.

Regla protegida (CLAUDE.md): «la suma de anchos de los módulos de una pared debe
coincidir EXACTAMENTE con el ancho real de esa pared».
"""
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
        "services.kitchen_geometry", os.path.join(BACKEND, "services", "kitchen_geometry.py"))
    mod = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, "services.kitchen_geometry", mod)
    spec.loader.exec_module(mod)
    return mod


# La cocina del master, tal cual la devolvió el análisis del render.
PARED = 324
CASO_REAL = {
    "tipo": "lineal",
    "paredes": [{"nombre": "Pared principal", "ancho": PARED, "alto": 240}],
    "elementos": [
        {"id": "lavavajillas", "label": "Lavavajillas", "pared_idx": 0, "posicion_cm": 0, "ancho": 60},
        {"id": "mueble_alto", "label": "Mueble alto", "pared_idx": 0, "posicion_cm": 60, "ancho": 30},
        {"id": "mueble_horno", "label": "Mueble horno", "pared_idx": 0, "posicion_cm": 90, "ancho": 60},
        {"id": "placa", "label": "Placa vitrocerámica", "pared_idx": 0, "posicion_cm": 150, "ancho": 60},
        {"id": "mueble_fregadero", "label": "Mueble fregadero", "pared_idx": 0, "posicion_cm": 210, "ancho": 40},
        {"id": "mueble_alto", "label": "Mueble alto", "pared_idx": 0, "posicion_cm": 250, "ancho": 45},
        {"id": "mueble_bajo", "label": "Mueble bajo", "pared_idx": 0, "posicion_cm": 295, "ancho": 30},
        {"id": "mueble_alto", "label": "Mueble alto", "pared_idx": 0, "posicion_cm": 325, "ancho": 30},
        {"id": "frigorifico", "label": "Columna frigorífico", "pared_idx": 0, "posicion_cm": 355, "ancho": 60},
    ],
}


def _fila(resultado, cual):
    return [e for e in resultado["elementos"] if e.get("fila") == cual]


def test_la_fila_de_suelo_suma_exactamente_el_ancho_de_la_pared(geom):
    r = geom.validar_distribucion(CASO_REAL)
    assert r["ok"] is True, f"no debería rechazarse: {r.get('motivo')}"
    suma = sum(e["ancho"] for e in _fila(r, "bajo"))
    assert suma == PARED, (
        f"los módulos de suelo suman {suma} cm en una pared de {PARED} cm. "
        f"Se dibujarían muebles fuera de la pared.")


def test_los_altos_no_ocupan_ancho_en_la_fila_de_suelo(geom):
    """El fallo de origen: 105 cm de altos sumándose al suelo."""
    r = geom.validar_distribucion(CASO_REAL)
    etiquetas_suelo = [e["label"].lower() for e in _fila(r, "bajo")]
    assert not [t for t in etiquetas_suelo if t.startswith("mueble alto")], \
        f"un mueble alto ha vuelto a la fila de suelo: {etiquetas_suelo}"
    assert len(_fila(r, "alto")) == 3, "se han perdido los muebles altos"


def test_los_altos_no_se_pasan_del_ancho_de_la_pared(geom):
    r = geom.validar_distribucion(CASO_REAL)
    for e in _fila(r, "alto"):
        assert e["posicion_cm"] + e["ancho"] <= PARED, \
            f"«{e['label']}» se sale de la pared (x={e['posicion_cm']}, ancho={e['ancho']})"


def test_los_altos_se_quedan_donde_estan_y_no_se_amontonan(geom):
    """Empaquetarlos a la izquierda los movía de encima de su bajo."""
    r = geom.validar_distribucion(CASO_REAL)
    posiciones = [e["posicion_cm"] for e in _fila(r, "alto")]
    assert posiciones[0] > 0, \
        f"los altos se han empaquetado desde el origen ({posiciones}): ya no están sobre su bajo"


def test_todo_mueble_tiene_un_ancho_de_catalogo(geom):
    """Un mueble de 69 cm no existe. El sobrante va a un relleno, como en obra."""
    r = geom.validar_distribucion(CASO_REAL)
    raros = [(e["label"], e["ancho"]) for e in r["elementos"]
             if e["id"] != "relleno" and e["ancho"] not in geom.ANCHOS_STD]
    assert not raros, f"anchos que no son de catálogo: {raros}"


def test_si_no_cuadra_no_se_dibuja(geom):
    """Antes se avisaba y se dibujaba igual. Un alzado que miente es peor que
    ninguno: parece bueno y se manda al taller."""
    imposible = {
        "tipo": "lineal",
        "paredes": [{"nombre": "P", "ancho": 120, "alto": 240}],
        # Solo electrodomésticos de ancho fijo: 240 cm en una pared de 120.
        "elementos": [
            {"id": "lavavajillas", "label": "Lavavajillas", "pared_idx": 0, "posicion_cm": 0, "ancho": 60},
            {"id": "horno", "label": "Horno", "pared_idx": 0, "posicion_cm": 60, "ancho": 60},
            {"id": "placa", "label": "Placa", "pared_idx": 0, "posicion_cm": 120, "ancho": 60},
            {"id": "frigorifico", "label": "Frigorífico", "pared_idx": 0, "posicion_cm": 180, "ancho": 60},
        ],
    }
    r = geom.validar_distribucion(imposible)
    assert r["ok"] is False, "una composición que no cabe NO puede darse por buena"
    assert r.get("motivo"), "se rechaza sin decir por qué"


@pytest.mark.parametrize("eid,label,esperado", [
    ("mueble_alto", "Mueble alto", True),
    ("alacena", "Alacena", True),
    ("microondas", "Microondas", True),
    ("campana", "Campana extractora", True),
    ("frigorifico", "Columna frigorífico", False),
    ("mueble_bajo", "Mueble bajo", False),
    ("mueble_fregadero", "Bajo fregadero", False),
    ("lavavajillas", "Lavavajillas", False),
    ("cajonera", "Cajonera 4 gavetas", False),
    ("placa", "Placa vitrocerámica", False),
])
def test_se_distingue_un_alto_de_un_bajo(geom, eid, label, esperado):
    """De esto depende en qué fila cae cada módulo, o sea, si la suma cuadra."""
    assert geom.es_alto(eid, label) is esperado, f"«{label}» mal clasificado"
