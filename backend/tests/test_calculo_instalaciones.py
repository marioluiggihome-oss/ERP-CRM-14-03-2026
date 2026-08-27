# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""Plan de instalaciones: sale de la cocina real y no dice barbaridades.

Este papel lo usa el instalador para hacer rozas ANTES de alicatar. Un punto mal
puesto se paga picando pared, así que aquí no vale una plantilla.

Lo que había hasta el 05/08/2026 y estas pruebas impiden que vuelva:

· Listaba «circuito lavavajillas» y «circuito frigorífico» hubiera o no, y
  colocaba los enchufes «cada 120 cm en la pared norte» sin saber qué había.
· «Potencia total estimada: <suma de amperios> A». Sumar los calibres de los
  magnetotérmicos no es la potencia, y la potencia no se mide en amperios.
· «Placa de inducción — línea trifásica». En vivienda va monofásica a 230 V.
· «RITE para fontanería». El RITE es de instalaciones térmicas.
"""
import importlib.util
import os
import sys
import types

import pytest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture()
def inst(monkeypatch):
    paquete = types.ModuleType("services")
    paquete.__path__ = [os.path.join(BACKEND, "services")]
    monkeypatch.setitem(sys.modules, "services", paquete)
    spec = importlib.util.spec_from_file_location(
        "services.instalaciones_cocina",
        os.path.join(BACKEND, "services", "instalaciones_cocina.py"))
    mod = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, "services.instalaciones_cocina", mod)
    spec.loader.exec_module(mod)
    return mod


def _mods(*defs):
    x, out = 0, []
    for eid, label, w in defs:
        out.append({"id": eid, "label": label, "posicion_cm": x, "ancho": w})
        x += w
    return out


COCINA = _mods(("cajonera", "Bajo 3 cajones", 30), ("placa", "Placa inducción", 60),
               ("mueble", "Mueble bajo", 60), ("mueble_fregadero", "Bajo fregadero", 60),
               ("columna_hornos", "Columna horno y microondas", 60),
               ("frigorifico", "Frigorífico integrado", 60))
ANCHO = sum(m["ancho"] for m in COCINA)


def _tipos(puntos):
    return [p["tipo"] for p in puntos]


# ── 1. Los puntos salen de muebles que EXISTEN ───────────────────────────────

def test_no_se_inventa_un_circuito_de_lavavajillas_si_no_lo_hay(inst):
    r = inst.plan_electrico(COCINA, ANCHO, con_isla=False)
    assert not [t for t in _tipos(r["puntos"]) if "lavavajillas" in t.lower()], \
        "se lista un circuito de lavavajillas en una cocina que no lo tiene"


def test_cada_electrodomestico_presente_tiene_su_toma(inst):
    r = inst.plan_electrico(COCINA, ANCHO, con_isla=False)
    t = " ".join(_tipos(r["puntos"])).lower()
    for esperado in ("placa", "horno", "frigorífico"):
        assert esperado in t, f"falta la toma de {esperado}"


def test_una_columna_de_horno_y_microondas_lleva_dos_tomas(inst):
    """Son dos aparatos. Con una sola toma, el micro se queda sin enchufe."""
    r = inst.plan_electrico(COCINA, ANCHO, con_isla=False)
    t = " ".join(_tipos(r["puntos"])).lower()
    assert "microondas" in t, "la columna horno+micro solo ha recibido una toma"


def test_cada_punto_dice_DONDE_va(inst):
    """Sin cota, el instalador no puede replantear. Lo que no se sabe va a None,
    nunca con un número inventado."""
    r = inst.plan_electrico(COCINA, ANCHO, con_isla=False)
    de_aparato = [p for p in r["puntos"] if p["modulo"]]
    assert de_aparato, "ningún punto está ligado a un módulo"
    for p in de_aparato:
        assert p["x_cm"] is not None, f"«{p['tipo']}» no dice a qué distancia va"
        assert 0 <= p["x_cm"] <= ANCHO, f"«{p['tipo']}» cae fuera de la pared"


def test_los_enchufes_de_encimera_no_caen_sobre_la_placa_ni_el_fregadero(inst):
    r = inst.plan_electrico(COCINA, ANCHO, con_isla=False)
    prohibido = [(m["posicion_cm"], m["ancho"]) for m in COCINA
                 if m["id"] in ("placa", "mueble_fregadero")]
    for p in r["puntos"]:
        if not p["tipo"].startswith("Enchufe encimera"):
            continue
        for px, pw in prohibido:
            assert not (px <= p["x_cm"] <= px + pw), \
                f"«{p['tipo']}» cae sobre un módulo donde no puede ir (x={p['x_cm']})"


# ── 2. Lo que decía mal, técnicamente ────────────────────────────────────────

def test_la_potencia_va_en_vatios_y_con_simultaneidad(inst):
    """Sumar calibres de magnetotérmicos no es la potencia."""
    r = inst.plan_electrico(COCINA, ANCHO, con_isla=False)
    assert r["potencia_calculo_w"] < r["potencia_instalada_w"], \
        "no se ha aplicado coeficiente de simultaneidad"
    assert 0 < r["simultaneidad"] < 1
    # La suma de calibres de los circuitos NO puede ser la cifra que se publica.
    suma_calibres = sum(p["amperios"] for p in r["puntos"])
    assert abs(r["intensidad_a"] - suma_calibres) > 1, \
        "la intensidad publicada vuelve a ser la suma de los magnetotérmicos"
    assert "kW" in r["circuitos"], "la potencia debe expresarse en kW, no en A"


def test_la_placa_no_es_trifasica(inst):
    """En vivienda española la placa va monofásica a 230 V."""
    r = inst.plan_electrico(COCINA, ANCHO, con_isla=False)
    placa = [p for p in r["puntos"] if "placa" in p["tipo"].lower()][0]
    detalle = placa["detalle"].lower()
    assert "monofásica" in detalle, "la placa debe pedirse monofásica a 230 V"
    # Puede nombrar "trifásica" solo para negarla explícitamente.
    if "trifásic" in detalle:
        assert "no trifásica" in detalle, \
            "se sigue pidiendo línea trifásica para la placa"
    assert placa["circuito"] == "C3", "la placa va en el circuito C3 del ITC-BT-25"
    assert placa["seccion_mm2"] >= 6, "C3 se ejecuta con 6 mm²"


def test_la_normativa_de_fontaneria_no_es_el_rite(inst):
    """El RITE es de instalaciones TÉRMICAS. Agua va por CTE DB-HS4/HS5."""
    assert "RITE" not in inst.NORMATIVA
    assert "HS4" in inst.NORMATIVA and "HS5" in inst.NORMATIVA
    assert "ITC-BT-25" in inst.NORMATIVA


# ── 3. Fontanería y gas ──────────────────────────────────────────────────────

def test_el_agua_va_donde_esta_el_fregadero(inst):
    r = inst.plan_fontaneria(COCINA, con_isla=False)
    fregadero = [m for m in COCINA if m["id"] == "mueble_fregadero"][0]
    centro = fregadero["posicion_cm"] + fregadero["ancho"] // 2
    assert r["puntos"], "no hay ni un punto de fontanería"
    for p in r["puntos"]:
        if p["x_cm"] is not None:
            assert p["x_cm"] == centro, "el agua no cae en el bajo fregadero"


def test_sin_fregadero_no_hay_fontaneria_inventada(inst):
    sin_agua = _mods(("mueble", "Mueble bajo", 60), ("frigorifico", "Frigo", 60))
    r = inst.plan_fontaneria(sin_agua, con_isla=False)
    assert r["puntos"] == [], "se inventan tomas de agua sin fregadero"


def test_no_se_supone_gas_si_no_lo_hay(inst):
    assert inst.plan_gas(COCINA, "cocina moderna con placa de inducción") is None


def test_con_placa_de_gas_aparece_la_llave_y_la_ventilacion(inst):
    con_gas = _mods(("placa", "Placa de gas", 60), ("mueble_fregadero", "Fregadero", 60))
    r = inst.plan_gas(con_gas, "placa de gas natural")
    assert r is not None
    t = " ".join(p["tipo"].lower() for p in r["puntos"])
    assert "llave de paso" in t and "ventilación" in t
