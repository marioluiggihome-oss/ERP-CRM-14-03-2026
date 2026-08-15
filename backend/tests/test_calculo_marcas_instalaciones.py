# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO: las tomas del render no pueden pisarse unas a otras.

14/08/2026, el master: «coloca mucho mejor todas las tomas y enchufes». En su
captura salían siete marcas amontonadas en el lado izquierdo, dos de ellas
literalmente encima, todas con la misma cota de 110 cm, y media cocina sin un
solo punto.

POR QUÉ NO SE ARREGLA PIDIÉNDOSELO MEJOR AL MODELO
--------------------------------------------------
Al modelo de visión se le puede pedir DÓNDE está cada cosa. Lo que no se le
puede exigir es que dos etiquetas no se solapen: eso no es ver, es geometría, y
la geometría se calcula. Tarde o temprano devolverá dos puntos en el mismo
píxel —el horno y el microondas están uno encima del otro— y ese plano ya no se
puede leer. Es el papel que se lleva el electricista a picar pared.

Se prueba con las marcas de SU captura, no con un caso inventado.
"""
import importlib.util
import os
import sys
import types

import pytest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_AI = os.path.join(BACKEND, "routes", "ai_engine.py")


@pytest.fixture()
def marcas(monkeypatch):
    """El servicio de verdad, sin arrastrar el resto del backend."""
    paquete = types.ModuleType("services")
    paquete.__path__ = [os.path.join(BACKEND, "services")]
    monkeypatch.setitem(sys.modules, "services", paquete)
    spec = importlib.util.spec_from_file_location(
        "services.marcas_instalaciones",
        os.path.join(BACKEND, "services", "marcas_instalaciones.py"))
    mod = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, "services.marcas_instalaciones", mod)
    spec.loader.exec_module(mod)
    return mod


# Las marcas tal como salían en la captura del master.
CAPTURA = [
    {"type": "enchufe", "x": 12.0, "y": 47.0},
    {"type": "enchufe", "x": 22.0, "y": 43.0},
    {"type": "enchufe", "x": 14.5, "y": 55.0},
    {"type": "enchufe", "x": 22.5, "y": 56.0},
    {"type": "enchufe", "x": 23.0, "y": 56.5},   # el mismo punto, otra vez
    {"type": "enchufe", "x": 32.0, "y": 55.0},
    {"type": "enchufe", "x": 22.0, "y": 60.0},
    {"type": "enchufe", "x": 85.0, "y": 52.0},
    {"type": "desague", "x": 57.0, "y": 66.0},
]


def _minima(ms):
    return min((((a["x"] - b["x"]) ** 2 + (a["y"] - b["y"]) ** 2) ** 0.5)
               for i, a in enumerate(ms) for b in ms[i + 1:])


# Separación mínima EXIGIDA, escrita aquí como número y no leída del código.
# Comprobar contra `marcas.SEPARACION_MIN` no protege de nada: bajar esa
# constante a cero haría pasar la prueba. El candado tiene que decir cuánto es
# «suficiente» por su cuenta.
SEPARACION_EXIGIDA = 6.0


def test_ninguna_marca_se_pisa_con_otra(marcas):
    """CANDADO PRINCIPAL. Dos etiquetas encima no son dos puntos: son cero."""
    r = marcas.ordenar_marcas(CAPTURA)
    assert _minima(r) >= SEPARACION_EXIGIDA, (
        f"vuelven a solaparse marcas (la más cercana a {_minima(r):.2f}%, hace "
        f"falta {SEPARACION_EXIGIDA}%): el plano del electricista deja de poder "
        f"leerse")


def test_el_listón_de_separacion_no_se_puede_bajar_sin_enterarse(marcas):
    """El circulo son 40 px y debajo va la etiqueta con la cota. Por debajo de
    esto se tocan, por mucho que el codigo diga que estan «separadas»."""
    assert marcas.SEPARACION_MIN >= SEPARACION_EXIGIDA, (
        f"se ha bajado SEPARACION_MIN a {marcas.SEPARACION_MIN}: las marcas "
        f"volveran a pisarse aunque el codigo crea que las separa")


def test_el_mismo_punto_detectado_dos_veces_no_sale_dos_veces(marcas):
    """Dos del MISMO tipo casi en el mismo píxel son el mismo punto."""
    r = marcas.ordenar_marcas(CAPTURA)
    assert len(r) == len(CAPTURA) - 1, (
        f"esperaba que se fuera 1 duplicado; entraron {len(CAPTURA)} y salen {len(r)}")


def test_dos_puntos_de_TIPO_DISTINTO_no_se_funden(marcas):
    """Un agua y un desagüe van casi en el mismo sitio y son DOS instalaciones.
    Fundirlos dejaría al fontanero sin una de las dos."""
    r = marcas.ordenar_marcas([
        {"type": "agua", "x": 50.0, "y": 60.0},
        {"type": "desague", "x": 50.5, "y": 60.5},
    ])
    assert len(r) == 2, "se ha perdido una instalación al juntarlas"
    assert _minima(r) >= SEPARACION_EXIGIDA


def test_ninguna_marca_se_sale_de_la_imagen(marcas):
    """Si se va del borde, la etiqueta se corta y la cota no se lee."""
    r = marcas.ordenar_marcas([
        {"type": "enchufe", "x": -20.0, "y": 50.0},
        {"type": "enchufe", "x": 140.0, "y": 50.0},
        {"type": "agua", "x": 0.0, "y": 0.0},
    ])
    for m in r:
        assert marcas.MARGEN_BORDE - 0.01 <= m["x"] <= 100 - marcas.MARGEN_BORDE + 0.01
        assert marcas.MARGEN_BORDE - 0.01 <= m["y"] <= 100 - marcas.MARGEN_BORDE + 0.01


def test_cada_toma_lleva_SU_altura_y_no_todas_110(marcas):
    """En la captura del master TODO salía a 110 cm. Un desagüe no va a 110."""
    r = marcas.ordenar_marcas(CAPTURA)
    alturas = {m["type"]: m.get("h") for m in r}
    assert alturas.get("enchufe") == 110
    assert alturas.get("desague") == 40, \
        "el desagüe vuelve a salir a la altura del enchufe"


def test_la_altura_que_dice_la_IA_manda_si_es_creible(marcas):
    """La IA sabe que el enchufe de la campana va alto y el del horno bajo."""
    r = marcas.ordenar_marcas([{"type": "enchufe", "x": 50.0, "y": 20.0, "alto_cm": 220}])
    assert r[0]["h"] == 220, "se ignora la altura que ha deducido la IA"


def test_una_altura_imposible_se_descarta(marcas):
    """3.000 cm no es una variante, es un error. Se usa la de la casa."""
    for absurdo in (3000, -5, "arriba", None):
        r = marcas.ordenar_marcas([{"type": "enchufe", "x": 50.0, "y": 20.0, "alto_cm": absurdo}])
        assert r[0]["h"] == 110, f"«{absurdo}» ha pasado como altura buena"


def test_el_resultado_es_siempre_el_mismo(marcas):
    """Dos marcas exactamente encima hay que separarlas por ALGÚN criterio. Si
    ese criterio no es estable, el mismo render da un plano distinto cada vez."""
    a = marcas.ordenar_marcas(CAPTURA)
    b = marcas.ordenar_marcas(CAPTURA)
    assert [(m["type"], m["x"], m["y"]) for m in a] == [(m["type"], m["x"], m["y"]) for m in b]


def test_salen_ordenadas_de_izquierda_a_derecha(marcas):
    """Es como se lee el plano y como se pica la pared."""
    r = marcas.ordenar_marcas(CAPTURA)
    assert [m["x"] for m in r] == sorted(m["x"] for m in r)


def test_el_endpoint_ordena_las_marcas_antes_de_devolverlas():
    """El servicio puede estar perfecto y no servir de nada si nadie lo llama."""
    with open(RUTA_AI, encoding="utf-8") as f:
        src = f.read()
    i = src.index('@ai_engine_router.post("/detect-installations")')
    cuerpo = src[i:src.index("\n@ai_engine_router.", i + 10)]
    assert "ordenar_marcas" in cuerpo, (
        "detect-installations vuelve a devolver las marcas en crudo: se pisarán "
        "otra vez")


def test_a_la_IA_se_le_pide_repartirlas_y_dar_la_altura():
    with open(RUTA_AI, encoding="utf-8") as f:
        src = f.read()
    i = src.index('@ai_engine_router.post("/detect-installations")')
    cuerpo = src[i:src.index("\n@ai_engine_router.", i + 10)]
    assert "REPARTE LOS PUNTOS POR TODA LA COCINA" in cuerpo, (
        "ya no se le pide recorrer la cocina entera: volverá a amontonarlas en "
        "un lado y dejar media cocina sin instalación")
    assert "alto_cm" in cuerpo, "ya no se le pide la altura de cada toma"
