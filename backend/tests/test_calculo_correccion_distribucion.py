# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""Corregir a mano lo que ha leído la IA. Y sobre todo: qué NO puede moverse.

El panel de «Detectar distribución» enseña lo que la IA ha leído del croquis o
del render. Desde el 24/08/2026 se puede corregir ahí mismo: cambiar el ancho
de un módulo, quitarlo, añadir uno o corregir el ancho de la pared. Es el paso
que convierte «la IA lo ha leído así» en «esto es lo que se fabrica».

ESTAS PRUEBAS EJECUTAN EL VALIDADOR DE VERDAD. No miran texto: le pasan una
distribución, la corrigen y comprueban qué sale. Están escritas porque la
primera versión de esto tenía un fallo serio y solo se vio probándolo:

    corriges un bajo fregadero de 60 a 90  →  LA PARED crecía de 300 a 330
    quitas el lavavajillas                 →  LA PARED encogía a 270

Una pared no crece porque cambies un mueble ni encoge porque quites un
electrodoméstico: lo que te queda es un hueco de 60 cm. Venía de que el
validador, cuando la pared no está marcada como medida firme, deduce su ancho
de la SUMA de los módulos acotados — correcto leyendo un croquis, desastroso
revalidando una corrección. Es el agujero contra el que avisa CLAUDE.md: si la
pared se estira hasta los muebles, cualquier composición «cabe» y el validador
deja de validar nada.
"""
import asyncio
import importlib.util
import os

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEOMETRIA = os.path.join(RAIZ, "backend", "services", "kitchen_geometry.py")


def _geometria():
    spec = importlib.util.spec_from_file_location("kg_correccion", GEOMETRIA)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


kg = _geometria()


def _cocina():
    """Una pared de 300 con cinco módulos que ya cuadran."""
    return {
        "tipo": "lineal",
        "paredes": [{"nombre": "Pared 1", "ancho": 300, "alto": 240}],
        "elementos": [
            {"id": "bajo_fregadero", "label": "Bajo fregadero", "pared_idx": 0, "posicion_cm": 0, "ancho": 60},
            {"id": "lavavajillas", "label": "Lavavajillas", "pared_idx": 0, "posicion_cm": 60, "ancho": 60},
            {"id": "bajo", "label": "Bajo", "pared_idx": 0, "posicion_cm": 120, "ancho": 90},
            {"id": "placa", "label": "Placa", "pared_idx": 0, "posicion_cm": 210, "ancho": 60},
            {"id": "cajonera", "label": "Cajonera", "pared_idx": 0, "posicion_cm": 270, "ancho": 30},
        ],
    }


def _revalidar(dist):
    """Lo que hace el endpoint al recibir una corrección: clava el ancho de
    pared y valida. Si esto deja de coincidir con `validar_distribucion_corregida`,
    lo canta `test_el_endpoint_clava_de_verdad_el_ancho_de_pared`."""
    for pared in dist["paredes"]:
        pared["ancho_escrito"] = True
    return kg.validar_distribucion(dist)


def _copia(v):
    return {**v,
            "paredes": [dict(p) for p in v["paredes"]],
            "elementos": [dict(e) for e in v["elementos"]]}


def _suelo(v):
    return [e for e in v["elementos"] if e.get("fila") == "bajo"]


def _suma(v):
    return sum(e["ancho"] for e in _suelo(v))


# ── Lo que NO puede moverse ─────────────────────────────────────────────────

def test_corregir_un_modulo_NO_estira_la_pared():
    """CANDADO del fallo que motivó este fichero."""
    v = _revalidar(_copia(kg.validar_distribucion(_cocina())))
    corr = _copia(v)
    for e in corr["elementos"]:
        if e["id"] == "bajo_fregadero":
            e["ancho"] = 90
            e["corregida"] = True
    salida = _revalidar(corr)
    assert salida["paredes"][0]["ancho"] == 300, (
        f"la pared se ha ido sola a {salida['paredes'][0]['ancho']} cm al corregir "
        "un mueble. Una pared no crece porque cambies un bajo fregadero.")


def test_quitar_un_electrodomestico_NO_encoge_la_pared_deja_un_hueco():
    """Quitar el lavavajistas deja 60 cm de hueco, no una cocina más pequeña."""
    v = _revalidar(_copia(kg.validar_distribucion(_cocina())))
    corr = _copia(v)
    corr["elementos"] = [e for e in corr["elementos"] if e["id"] != "lavavajillas"]
    salida = _revalidar(corr)
    assert salida["paredes"][0]["ancho"] == 300, (
        f"la pared ha encogido a {salida['paredes'][0]['ancho']} cm al quitar un "
        "electrodoméstico: el hueco ha desaparecido del plano.")
    # El hueco se puede cuadrar de dos maneras válidas, y las dos son cosa del
    # validador: ensanchando los módulos flexibles (si el ajuste es razonable) o
    # metiendo un relleno. Lo que NO vale es que desaparezca encogiendo la pared,
    # que es lo que hacía antes. Aquí se comprueba el invariante, no cuál de las
    # dos salidas eligió.
    assert _suma(salida) == 300, (
        f"los módulos suman {_suma(salida)} cm en una pared de 300: el hueco que "
        "deja el lavavajillas no se ha cuadrado con nada.")


def test_la_suma_cuadra_despues_de_cada_correccion():
    """CLAUDE.md: la suma de anchos de una pared DEBE coincidir con la pared."""
    v = _revalidar(_copia(kg.validar_distribucion(_cocina())))
    assert _suma(v) == v["paredes"][0]["ancho"]

    corr = _copia(v)
    for e in corr["elementos"]:
        if e["id"] == "bajo_fregadero":
            e["ancho"] = 90
            e["corregida"] = True
    v2 = _revalidar(corr)
    assert _suma(v2) == v2["paredes"][0]["ancho"], "tras corregir un ancho, la pared no cuadra"

    corr2 = _copia(v2)
    corr2["elementos"] = [e for e in corr2["elementos"] if e["id"] != "lavavajillas"]
    v3 = _revalidar(corr2)
    assert _suma(v3) == v3["paredes"][0]["ancho"], "tras quitar un módulo, la pared no cuadra"


# ── Lo que SÍ tiene que respetarse ──────────────────────────────────────────

def test_una_medida_corregida_a_mano_se_respeta_tal_cual():
    """Si el master dice 90, es 90. Los demás se ajustan alrededor, no él."""
    v = _revalidar(_copia(kg.validar_distribucion(_cocina())))
    corr = _copia(v)
    for e in corr["elementos"]:
        if e["id"] == "bajo_fregadero":
            e["ancho"] = 90
            e["corregida"] = True
    salida = _revalidar(corr)
    fregadero = [e for e in salida["elementos"] if e["id"] == "bajo_fregadero"][0]
    assert fregadero["ancho"] == 90, (
        f"la corrección del master se ha reescalado a {fregadero['ancho']} cm para "
        "cuadrar la pared. Una medida que ha dicho él es un dato, no una estimación.")


def test_la_marca_de_corregida_sobrevive_a_la_validacion():
    """Si se pierde, la pantalla vuelve a presentar lo que ha tecleado el master
    como una estimación de la IA — y con eso se fabrica."""
    v = _revalidar(_copia(kg.validar_distribucion(_cocina())))
    corr = _copia(v)
    for e in corr["elementos"]:
        if e["id"] == "placa":
            e["ancho"] = 90
            e["corregida"] = True
    salida = _revalidar(corr)
    placa = [e for e in salida["elementos"] if e["id"] == "placa"][0]
    assert placa.get("corregida") is True, "se ha perdido la marca de corregida a mano"
    assert placa.get("medida_escrita") is True, \
        "una medida corregida a mano tiene que contar como medida real"


def test_una_placa_corregida_gana_a_la_tabla_de_anchos_fijos():
    """`ANCHO_FIJO` dice que una placa mide 60. Es lo que mide CUANDO NADIE HA
    DICHO NADA: en cuanto el master dice 90, manda el master."""
    v = _revalidar(_copia(kg.validar_distribucion(_cocina())))
    corr = _copia(v)
    for e in corr["elementos"]:
        if e["id"] == "placa":
            e["ancho"] = 90
            e["corregida"] = True
    salida = _revalidar(corr)
    placa = [e for e in salida["elementos"] if e["id"] == "placa"][0]
    assert placa["ancho"] == 90, \
        f"la placa ha vuelto a 60 por la tabla de anchos fijos, pisando al master"


def test_una_pared_corregida_a_mano_gana_al_ancho_de_la_estancia():
    """Los dos los ha tecleado él. Gana el último que ha dicho, que es el del
    panel — más reciente y más concreto."""
    v = _revalidar(_copia(kg.validar_distribucion(_cocina())))
    corr = _copia(v)
    corr["paredes"][0]["ancho"] = 340
    corr["paredes"][0]["ancho_corregido"] = True
    salida = kg.validar_distribucion(corr, ancho_real=300)
    assert salida["paredes"][0]["ancho"] == 340, (
        "el ancho de «Medidas de la estancia» ha pisado la corrección del panel: "
        f"quedó en {salida['paredes'][0]['ancho']} cm.")
    assert _suma(salida) == 340, "la pared corregida no cuadra con sus módulos"


# ── Que el endpoint haga lo que dicen estas pruebas ─────────────────────────

def test_el_endpoint_clava_de_verdad_el_ancho_de_pared():
    """Las pruebas de arriba imitan al endpoint. Esta comprueba que el endpoint
    hace lo mismo — si no, protegerían a un doble y no al código de verdad."""
    os.environ.setdefault("JWT_SECRET", "x" * 64)
    import sys
    backend = os.path.join(RAIZ, "backend")
    if backend not in sys.path:
        sys.path.insert(0, backend)
    try:
        from routes.estudio_cocinas import validar_distribucion_corregida
    except Exception as e:                      # pragma: no cover
        pytest.fail(f"no se pudo importar el endpoint: {e}")

    dist = kg.validar_distribucion(_cocina())
    corr = _copia(dist)
    corr["elementos"] = [e for e in corr["elementos"] if e["id"] != "lavavajillas"]
    for e in corr["elementos"]:
        if e["id"] == "bajo_fregadero":
            e["ancho"] = 90
            e["corregida"] = True

    r = asyncio.run(validar_distribucion_corregida({"distribucion": corr}))
    assert r["success"]
    salida = r["distribucion"]
    assert salida["paredes"][0]["ancho"] == 300, (
        f"el endpoint deja que la pared se mueva a {salida['paredes'][0]['ancho']} cm")
    fregadero = [e for e in salida["elementos"] if e["id"] == "bajo_fregadero"][0]
    assert fregadero["ancho"] == 90 and fregadero.get("corregida") is True
    assert sum(e["ancho"] for e in salida["elementos"] if e.get("fila") == "bajo") == 300


def test_el_endpoint_no_valida_una_distribucion_sin_paredes():
    """Sin paredes no hay nada que validar, y desde luego nada que dibujar."""
    os.environ.setdefault("JWT_SECRET", "x" * 64)
    import sys
    backend = os.path.join(RAIZ, "backend")
    if backend not in sys.path:
        sys.path.insert(0, backend)
    from fastapi import HTTPException
    from routes.estudio_cocinas import validar_distribucion_corregida
    with pytest.raises(HTTPException) as ex:
        asyncio.run(validar_distribucion_corregida({"distribucion": {"paredes": []}}))
    assert ex.value.status_code == 422
