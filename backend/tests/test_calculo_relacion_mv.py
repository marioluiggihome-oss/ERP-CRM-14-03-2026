# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""Relación de muebles MV escrita en la plantilla de nomenclaturas.

Protege los fallos del 03/08, cuando "se importaba bien pero no calculaba bien":

  1. "1ASFA 60X30" se perdia. El codigo de tarifa es ASF60A (la variante va
     DESPUES del ancho) y el lector solo probaba ASFA60.
  2. "2 - 90 x 60" en el recuadro de puertas se perdia: una puerta suelta no
     lleva codigo, se tarifa en la matriz alto x ancho.
  3. Un codigo que no esta en la tarifa valia 0 EUR y NADIE avisaba: el total
     salia corto y parecia bueno.
  4. Habia varias familias en matriz y la ultima pisaba a la anterior en el
     indice, asi que una puerta normal se tarifaba contra la de rincon.

Solo hace falta el fichero de tarifas: ni base de datos, ni red, ni IA.
"""
import importlib.util
import os
import sys
import types

import pytest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture()
def mv(monkeypatch):
    servicios = types.ModuleType("services")
    servicios.__path__ = [os.path.join(BACKEND, "services")]
    monkeypatch.setitem(sys.modules, "services", servicios)
    spec = importlib.util.spec_from_file_location(
        "services.mv_relacion", os.path.join(BACKEND, "services", "mv_relacion.py"))
    mod = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, "services.mv_relacion", mod)
    spec.loader.exec_module(mod)
    return mod


def _codigos(r):
    return [m["cod"] for m in r["muebles"]]


def test_la_variante_puede_ir_detras_del_ancho(mv):
    """'1ASFA 60X30' es ASF60A en la tarifa. Antes se perdia la linea entera."""
    r = mv.parse_relacion("1ASFA 60X30")
    assert _codigos(r) == ["ASF60A"]
    assert r["muebles"][0]["pts"], "sin puntos, la linea vale 0 EUR"


def test_una_puerta_suelta_se_tarifa_por_la_matriz(mv):
    """'2 - 90 x 60' en el recuadro de puertas: 2 puertas de 90 alto x 60 ancho."""
    r = mv.parse_relacion("2 - 90 x 60", contexto="Puertas")
    assert len(r["muebles"]) == 1
    p = r["muebles"][0]
    assert p["qty"] == 2 and p["alto"] == 90 and p["ancho"] == 60
    assert p["familia"] == "PUERTAS", "se ha tarifado contra otra matriz (rincon)"
    assert p["pts"] == 19 and p["pvp"] == 63.27


def test_sin_saber_el_recuadro_no_se_adivina_que_es_una_puerta(mv):
    """Un '2 - 90 x 60' suelto, sin contexto, seria adivinar: se reporta."""
    r = mv.parse_relacion("2 - 90 x 60")
    assert r["muebles"] == []
    assert len(r["noLeidas"]) == 1


def test_un_codigo_que_no_existe_se_avisa_y_no_se_corrige_solo(mv):
    r = mv.parse_relacion("1BFC60I", contexto="Bajo fregadero")
    assert len(r["noLeidas"]) == 1
    nl = r["noLeidas"][0]
    assert "no está en la tarifa" in nl["motivo"]
    assert nl.get("sugerencia") == "BF60", "hay que proponer el codigo parecido"
    # Pero NO se aplica: el mueble entra sin precio, para que se vea y se corrija.
    assert r["muebles"][0]["cod"] is None and r["muebles"][0]["pvp"] is None


def test_varios_muebles_en_una_misma_anotacion(mv):
    r = mv.parse_relacion("1B60D + 1B30I")
    assert _codigos(r) == ["B60D/I", "B30D/I"]
    assert all(m["encontrado"] for m in r["muebles"])


def test_las_unidades_se_respetan(mv):
    r = mv.parse_relacion("3 B60D")
    assert r["muebles"][0]["qty"] == 3


def test_un_bajo_sin_altura_se_fabrica_a_80(mv):
    """Regla de fabrica: en esta casa los bajos solo se hacen a 80 cm."""
    r = mv.parse_relacion("1B60D")
    assert r["muebles"][0]["alto"] == 80


def test_la_altura_de_la_anotacion_manda(mv):
    r = mv.parse_relacion("1ASC60x90")
    m = r["muebles"][0]
    assert m["alto"] == 90
    assert m["pts"], "un alto de 90 tiene que tener puntos propios"


def test_nada_se_pierde_en_silencio(mv):
    """Todo lo escrito sale por algun lado: como mueble, como aviso o como ambos.

    El codigo desconocido aparece en las DOS listas a proposito: en la de
    muebles para verlo y poder corregirlo, y en la de avisos porque va sin
    precio.
    """
    texto = "1B60D + 1BFC60I\n2 - 90 x 60\nesto no es nada"
    r = mv.parse_relacion(texto, contexto="Puertas")
    visto = {m["raw"] for m in r["muebles"]} | {n["texto"] for n in r["noLeidas"]}
    for escrito in ("1b60d", "1bfc60i", "2 - 90 x 60", "esto no es nada"):
        assert escrito in visto, f"se ha perdido «{escrito}» por el camino"


def test_la_notacion_antigua_sigue_funcionando(mv):
    """parse_relacion_text se usa desde la ruta de texto libre."""
    muebles = mv.parse_relacion_text("1 b60i (altura 80)")
    assert len(muebles) == 1 and muebles[0]["cod"] == "B60D/I"
