# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO de la PLANTA de cocina.

El master lo dijo asi: «donde pone planta, no esta bien, lo que dibuja es un
alzado; el alzado es visto de frente y la planta vista desde arriba, con cotas
y medidas».

QUE ESTABA MAL
--------------
1. La planta NO USABA LOS ANCHOS REALES. Pintaba modulos genericos de 55 cm en
   un bucle y DESPUES colocaba los elementos aparte, con un espaciado propio
   (`elem_x += ew + 10`) que no tenia nada que ver con donde estan. Los
   rectangulos eran decoracion y las etiquetas se amontonaban unas sobre otras.

2. SE INVENTABA EL FONDO DE LA ESTANCIA: `max(250, ancho*0,6)` en lineal, y un
   suelo de 250 que pisaba el ancho real de la segunda pared en L. Un numero
   inventado, en un plano rotulado «ESCALA 1:20».

Lo que se protege:

1. CADA MODULO CON SU ANCHO. Si vuelven los modulos genericos, la suma deja de
   cuadrar con la pared y el plano miente sobre lo que cabe.

2. LOS MODULOS NO SE PISAN NI DEJAN HUECOS. Van corridos a lo largo del muro.

3. LA PLANTA Y EL BOCETO COLOCAN LAS PAREDES IGUAL. Usan la MISMA funcion. Si
   cada uno pusiera las paredes a su manera, ensenarian dos cocinas distintas
   del mismo proyecto y nadie sabria cual mirar.

4. NO SE CIERRA LA HABITACION POR DETRAS. De una cocina lineal solo se conoce
   el ancho de SU pared; lo que hay enfrente no lo ha medido nadie.

5. LO QUE NO SE PUEDE DIBUJAR SE DICE. Un modulo sin ancho se omite y se
   informa; no se le pone uno «razonable».

6. SI LA SUMA NO CUADRA CON LA PARED, SE AVISA. No se corrige por nuestra
   cuenta: estirar un modulo o meter un relleno que nadie ha pedido es
   exactamente como se cuela una medida inventada en un plano que parece bueno.
"""
import importlib.util
import os
import sys
import types

import pytest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _cargar(nombre, ruta):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def pl():
    """Carga `planta_cocina` sin arrastrar `services/__init__`, que trae la
    base de datos entera. Igual que hacen las demas pruebas de calculo."""
    if "services" not in sys.modules or not hasattr(sys.modules.get("services"), "__path__"):
        pkg = types.ModuleType("services")
        pkg.__path__ = [os.path.join(BACKEND, "services")]
        sys.modules["services"] = pkg
    _cargar("services.perspectiva", os.path.join(BACKEND, "services", "perspectiva.py"))
    return _cargar("services.planta_cocina",
                   os.path.join(BACKEND, "services", "planta_cocina.py"))


def D(tipo="lineal", paredes=None, elementos=None):
    return {"tipo": tipo,
            "paredes": paredes if paredes is not None else [{"nombre": "A", "ancho": 360, "alto": 250}],
            "elementos": elementos or []}


# ─── 1. Cada modulo con SU ancho ────────────────────────────────────────────

def test_cada_modulo_ocupa_su_ancho_real(pl):
    r = pl.montar(D(elementos=[
        {"id": "B60", "label": "Bajo 60", "pared_idx": 0, "ancho": 60},
        {"id": "B90", "label": "Bajo 90", "pared_idx": 0, "ancho": 90},
    ]))
    assert [m["ancho"] for m in r["modulos"]] == [60, 90], (
        "han vuelto los modulos genericos: el plano dejaria de decir lo que cabe")


def test_los_modulos_van_corridos_sin_pisarse(pl):
    r = pl.montar(D(elementos=[
        {"id": "A", "pared_idx": 0, "ancho": 60},
        {"id": "B", "pared_idx": 0, "ancho": 90},
        {"id": "C", "pared_idx": 0, "ancho": 45},
    ]))
    for a, b in zip(r["modulos"], r["modulos"][1:]):
        assert a["hasta"] == pytest.approx(b["desde"]), "dos modulos se pisan o dejan hueco"
    assert r["modulos"][-1]["hasta"] == pytest.approx(195)


def test_el_rectangulo_en_planta_mide_ancho_por_fondo(pl):
    r = pl.montar(D(elementos=[{"id": "B60", "pared_idx": 0, "ancho": 60}]),
                  fondo_modulo=lambda _id: 58)
    e = r["modulos"][0]["esquinas"]
    assert abs(e[1][0] - e[0][0]) == pytest.approx(60), "el rectangulo no mide el ancho"
    assert abs(e[3][1] - e[0][1]) == pytest.approx(58), "el rectangulo no mide el fondo"


# ─── 2. Altos y bajos son DOS filas ─────────────────────────────────────────

def test_los_altos_corren_por_su_cuenta(pl):
    """En planta el alto va dibujado a trazos POR ENCIMA del bajo, no a
    continuacion: son dos filas, como en el alzado y en la perspectiva."""
    r = pl.montar(D(elementos=[
        {"id": "B60", "pared_idx": 0, "ancho": 60},
        {"id": "B90", "pared_idx": 0, "ancho": 90},
        {"id": "A60", "pared_idx": 0, "ancho": 60},
    ]), es_alto=lambda eid, label="": eid.startswith("A"))
    alto = next(m for m in r["modulos"] if m["id"] == "A60")
    assert alto["desde"] == 0, "el alto arranca donde acaban los bajos"


def test_la_cadena_de_cotas_es_solo_de_los_bajos(pl):
    """Encadenar las dos filas daria una cadena que no suma el largo de la
    pared, y quien la lea pensara que falta un mueble."""
    r = pl.montar(D(elementos=[
        {"id": "B60", "pared_idx": 0, "ancho": 60},
        {"id": "A60", "pared_idx": 0, "ancho": 60},
    ]), es_alto=lambda eid, label="": eid.startswith("A"))
    assert len(r["cotas"]) == 1
    assert [t["medida"] for t in r["cotas"][0]["tramos"]] == [60]


# ─── 3. La planta y el boceto colocan las paredes IGUAL ─────────────────────

def test_usa_la_misma_colocacion_de_paredes_que_la_perspectiva(pl):
    """Misma funcion, a proposito: dos criterios acabarian ensenando dos
    cocinas distintas del mismo proyecto."""
    import services.perspectiva as pe
    paredes = [{"ancho": 360, "alto": 250}, {"ancho": 240, "alto": 250}]
    for i in (0, 1):
        assert pl.origen_de_pared(i, "l", paredes) == pe.origen_de_pared(i, "l", paredes)


def test_en_L_la_segunda_pared_gira(pl):
    r = pl.montar(D(tipo="l",
                    paredes=[{"ancho": 360, "alto": 250}, {"ancho": 240, "alto": 250}],
                    elementos=[{"id": "B60", "pared_idx": 0, "ancho": 60},
                               {"id": "B90", "pared_idx": 1, "ancho": 90}]))
    a = next(m for m in r["modulos"] if m["id"] == "B60")
    b = next(m for m in r["modulos"] if m["id"] == "B90")
    assert a["direccion"] != b["direccion"], "las dos paredes corren igual: no es una L"
    assert b["esquinas"][0][0] == pytest.approx(360), "la segunda pared no arranca al final de la primera"


# ─── 4. No se cierra la habitacion por detras ───────────────────────────────

def test_en_lineal_no_hay_rincon_que_acotar(pl):
    """Solo se conoce el ancho de SU pared. El fondo de la estancia no lo ha
    medido nadie: antes se rellenaba con max(250, ancho*0,6)."""
    assert pl.montar(D())["rincon"] is None


def test_en_L_el_rincon_sale_de_las_DOS_paredes_reales(pl):
    r = pl.montar(D(tipo="l", paredes=[{"ancho": 360, "alto": 250},
                                       {"ancho": 240, "alto": 250}]))
    assert r["rincon"] == {"ancho": 360, "fondo": 240}


def test_una_L_sin_la_segunda_pared_no_inventa_el_rincon(pl):
    r = pl.montar(D(tipo="l", paredes=[{"ancho": 360, "alto": 250},
                                       {"ancho": 0, "alto": 250}]))
    assert r["rincon"] is None


def test_el_muro_mide_su_largo_real(pl):
    r = pl.montar(D(paredes=[{"ancho": 445, "alto": 250}]))
    assert r["muros"][0]["largo"] == 445


# ─── 5. Lo que no se puede dibujar se dice ──────────────────────────────────

def test_un_modulo_sin_ancho_se_omite_y_se_informa(pl):
    r = pl.montar(D(elementos=[
        {"id": "B60", "pared_idx": 0, "ancho": 60},
        {"id": "B??", "label": "B??", "pared_idx": 0, "ancho": None},
    ]))
    assert len(r["modulos"]) == 1
    assert r["omitidos"][0]["id"] == "B??" and r["omitidos"][0]["motivo"] == "sin ancho"


def test_un_modulo_en_una_pared_que_no_existe_se_omite(pl):
    r = pl.montar(D(elementos=[{"id": "X", "pared_idx": 7, "ancho": 60}]))
    assert not r["modulos"] and "inexistente" in r["omitidos"][0]["motivo"]


def test_una_pared_sin_ancho_no_se_dibuja(pl):
    r = pl.montar(D(paredes=[{"ancho": None, "alto": 250}]))
    assert r["muros"] == []


def test_una_distribucion_vacia_no_revienta(pl):
    r = pl.montar(None)
    assert r["modulos"] == [] and r["muros"] == [] and r["omitidos"] == []


# ─── 6. Si la suma no cuadra con la pared, se avisa ─────────────────────────

def test_se_avisa_cuando_los_muebles_no_dan_el_largo_de_la_pared(pl):
    """Regla de oro: la suma de anchos de una pared coincide con su ancho real.
    Aqui no se corrige, se DICE."""
    r = pl.montar(D(paredes=[{"ancho": 360, "alto": 250}], elementos=[
        {"id": "B60", "pared_idx": 0, "ancho": 60},
        {"id": "B90", "pared_idx": 0, "ancho": 90},
    ]))
    fuera = pl.descuadres(r["cotas"])
    assert len(fuera) == 1
    assert "faltan" in fuera[0]["motivo"] and "210" in fuera[0]["motivo"]


def test_cuando_cuadra_no_se_avisa_de_nada(pl):
    r = pl.montar(D(paredes=[{"ancho": 150, "alto": 250}], elementos=[
        {"id": "B60", "pared_idx": 0, "ancho": 60},
        {"id": "B90", "pared_idx": 0, "ancho": 90},
    ]))
    assert pl.descuadres(r["cotas"]) == []


def test_tambien_se_avisa_si_SOBRAN_muebles(pl):
    r = pl.montar(D(paredes=[{"ancho": 100, "alto": 250}], elementos=[
        {"id": "B60", "pared_idx": 0, "ancho": 60},
        {"id": "B90", "pared_idx": 0, "ancho": 90},
    ]))
    fuera = pl.descuadres(r["cotas"])
    assert len(fuera) == 1 and "sobran" in fuera[0]["motivo"]
