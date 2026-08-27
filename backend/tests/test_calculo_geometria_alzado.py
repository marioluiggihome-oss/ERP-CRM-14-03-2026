# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
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


# ── Las medidas ESCRITAS mandan sobre lo que estima la IA ────────────────────
# Croquis acotado a mano del master: 30+60+60+60+2+60+1+60+2+70+2 = 407 cm.
# La IA estimaba la pared en 280 y el codigo aplastaba contra ese 280 las cotas
# escritas: los muebles salian encogidos y la cocina no era la del croquis.

_CROQUIS = [("cajonera", "Bajo 3 cajones", 30), ("placa", "Placa", 60),
            ("mueble", "Mueble bajo", 60), ("mueble_fregadero", "Bajo fregadero", 60),
            ("relleno", "Relleno", 2), ("columna_hornos", "Columna horno", 60),
            ("relleno", "Relleno", 1), ("frigorifico", "Frigorífico", 60),
            ("relleno", "Relleno", 2), ("despensa", "Columna despensa", 70),
            ("relleno", "Relleno", 2)]
SUMA_CROQUIS = sum(w for _i, _l, w in _CROQUIS)   # 407


def _dist_croquis(ancho_ia, escrito=True, ancho_escrito=False):
    x, els = 0, []
    for eid, lab, w in _CROQUIS:
        els.append({"id": eid, "label": lab, "pared_idx": 0, "posicion_cm": x,
                    "ancho": w, "medida_escrita": escrito})
        x += w
    return {"tipo": "lineal",
            "paredes": [{"nombre": "P", "ancho": ancho_ia, "alto": 240,
                         "ancho_escrito": ancho_escrito}],
            "elementos": els}


def test_el_ancho_de_pared_sale_de_las_cotas_escritas(geom):
    r = geom.validar_distribucion(_dist_croquis(ancho_ia=280))
    assert r["paredes"][0]["ancho"] == SUMA_CROQUIS, (
        f"la pared sigue valiendo {r['paredes'][0]['ancho']} cm (lo que estimó la "
        f"IA) en vez de los {SUMA_CROQUIS} cm que suman las cotas escritas.")


def test_ninguna_medida_escrita_se_toca_para_cuadrar(geom):
    """Una cota escrita es un DATO. Si no cuadra se dice, no se falsea."""
    r = geom.validar_distribucion(_dist_croquis(ancho_ia=280))
    anchos = [e["ancho"] for e in r["elementos"] if e.get("fila") == "bajo"]
    assert anchos == [w for _i, _l, w in _CROQUIS], \
        f"se han modificado medidas escritas del croquis: {anchos}"


def test_lo_que_teclea_el_usuario_manda_incluso_sobre_el_croquis(geom):
    """Orden de verdad: usuario > cota escrita > suma de módulos > estimación."""
    r = geom.validar_distribucion(_dist_croquis(ancho_ia=280), ancho_real=420)
    assert r["paredes"][0]["ancho"] == 420


def test_una_cota_de_pared_escrita_manda_sobre_la_suma(geom):
    """Si el plano dice cuánto mide la pared, esa cota gana: lo que falte es un
    hueco real, no un error de la cota."""
    r = geom.validar_distribucion(
        _dist_croquis(ancho_ia=430, ancho_escrito=True))
    assert r["paredes"][0]["ancho"] == 430


def test_sin_medidas_escritas_se_sigue_cuadrando_como_antes(geom):
    """Si nada está acotado, todo son estimaciones y el reparto es el de siempre:
    los módulos se reparten el ancho de pared que dice la IA."""
    r = geom.validar_distribucion(_dist_croquis(ancho_ia=380, escrito=False))
    assert r["ok"] is True, r.get("motivo")
    assert r["paredes"][0]["ancho"] == 380
    suelo = [e for e in r["elementos"] if e.get("fila") == "bajo"]
    assert sum(e["ancho"] for e in suelo) == 380


def test_sin_cotas_escritas_y_sin_sitio_no_se_dibuja(geom):
    """407 cm de módulos estimados no caben en una pared de 300: antes se
    dibujaban igual, saliéndose. Ahora se rechaza y se explica."""
    r = geom.validar_distribucion(_dist_croquis(ancho_ia=300, escrito=False))
    assert r["ok"] is False, "una composición que no cabe no puede darse por buena"
    assert "suman" in (r.get("motivo") or "") or "caben" in (r.get("motivo") or "")


def test_un_relleno_no_se_ajusta_a_un_ancho_de_catalogo(geom):
    """El relleno es una pieza a medida. Al revalidar, uno de 10 cm pasaba a 15 y
    descuadraba la pared que ya cuadraba."""
    r = geom.validar_distribucion(_dist_croquis(ancho_ia=280))
    rellenos = [e["ancho"] for e in r["elementos"] if e["id"] == "relleno"]
    assert rellenos == [2, 1, 2, 2], f"los rellenos se han redondeado: {rellenos}"


def test_la_distribucion_ya_validada_sobrevive_a_una_segunda_validacion(geom):
    """detect-distribucion valida, y /alzado vuelve a validar lo que aquella
    devolvió. La segunda pasada no puede romper lo que la primera cuadró."""
    primera = geom.validar_distribucion(_dist_croquis(ancho_ia=280))
    segunda = geom.validar_distribucion(
        {"tipo": "lineal", "paredes": primera["paredes"], "elementos": primera["elementos"]})
    assert segunda["ok"] is True, segunda.get("motivo")
    suelo_1 = [(e["label"], e["ancho"]) for e in primera["elementos"] if e.get("fila") == "bajo"]
    suelo_2 = [(e["label"], e["ancho"]) for e in segunda["elementos"] if e.get("fila") == "bajo"]
    assert suelo_1 == suelo_2, \
        f"la segunda validación ha cambiado la composición:\n{suelo_1}\n{suelo_2}"


# ─── UNA MEDIDA ESCRITA GANA TAMBIEN A LA TABLA DE ANCHOS FIJOS ────────────
#
# Encontrado el 18/08 mirando el PNG de un alzado, no buscandolo: se le paso
# una PLACA DE 90 marcada como medida escrita y el alzado dibujo 60.
#
# `ANCHO_FIJO` dice lo que mide un electrodomestico CUANDO NADIE HA DICHO
# NADA: placa 60, campana 60, frigorifico 60, lavavajillas 60... Pero se
# miraba ANTES que `medida_escrita`, asi que pisaba lo que el cliente habia
# escrito en su propio plano.
#
# No es un caso raro. El glosario de la casa tiene «Bajo Placa 2 Gavetas:
# 90 cm», y un side by side de 120 se quedaba igual en 60. Son 30 o 60 cm de
# encimera y de frentes que desaparecen del presupuesto.
#
# Y no avisaba de nada: como `medida_escrita` seguia siendo True, la cota se
# pintaba «60» LIMPIA, sin marca de estimada. O sea que el plano que va a
# fabrica afirmaba un 60 como dato confirmado. Peor que una estimacion: una
# certeza falsa.
#
# Orden de verdad, ahora sin agujeros:
#     usuario > cota escrita > tabla de anchos fijos > estimacion.


def _pared_con_placa(ancho_placa, escrita):
    """Una pared de 300 con fregadero 60 + cajonera 90 + placa + bajo 60."""
    return {"tipo": "lineal",
            "paredes": [{"nombre": "P", "ancho": 300, "alto": 240}],
            "elementos": [
                {"id": "bajo_fregadero", "label": "Bajo fregadero", "pared_idx": 0,
                 "posicion_cm": 0, "ancho": 60, "medida_escrita": True},
                {"id": "cajonera", "label": "Cajonera", "pared_idx": 0,
                 "posicion_cm": 60, "ancho": 90, "medida_escrita": False},
                {"id": "placa", "label": "Placa", "pared_idx": 0,
                 "posicion_cm": 150, "ancho": ancho_placa, "medida_escrita": escrita},
                {"id": "bajo", "label": "Mueble bajo", "pared_idx": 0,
                 "posicion_cm": 240, "ancho": 60, "medida_escrita": False},
            ]}


def _placa(resultado):
    return next(e for e in resultado["elementos"] if e["id"] == "placa")


def test_una_placa_de_90_escrita_no_se_encoge_a_60(geom):
    """EL FALLO, tal cual. 90 escrito en el plano, 60 dibujado en el alzado."""
    r = geom.validar_distribucion(_pared_con_placa(90, escrita=True))
    assert _placa(r)["ancho"] == 90, (
        f"la placa de 90 escrita en el plano se ha quedado en "
        f"{_placa(r)['ancho']} cm: la tabla de anchos fijos vuelve a pisar lo "
        f"que escribio el cliente, y son 30 cm de encimera y de frentes que "
        f"desaparecen del presupuesto sin un solo aviso")


def test_un_frigorifico_de_120_escrito_se_respeta(geom):
    """El side by side del glosario: 120 cm de dos columnas de 60."""
    d = _pared_con_placa(60, escrita=True)
    d["elementos"][3] = {"id": "frigorifico", "label": "Side by side", "pared_idx": 0,
                         "posicion_cm": 240, "ancho": 120, "medida_escrita": True}
    d["paredes"][0]["ancho"] = 360
    r = geom.validar_distribucion(d)
    frigo = next(e for e in r["elementos"] if e["id"] == "frigorifico")
    assert frigo["ancho"] == 120, (
        f"el side by side de 120 escrito se ha quedado en {frigo['ancho']} cm")


def test_sin_medida_escrita_la_tabla_sigue_mandando(geom):
    """La tabla NO sobra: es lo que vale cuando nadie ha dicho nada. Si esto
    se rompe, una placa sin cota se estiraria a lo que hiciera falta para
    cuadrar la pared, que es justo lo que la tabla evita."""
    r = geom.validar_distribucion(_pared_con_placa(75, escrita=False))
    assert _placa(r)["ancho"] == 60, (
        f"una placa SIN cota escrita ya no cae al ancho de catalogo (60) sino "
        f"a {_placa(r)['ancho']} cm: se reparte como si fuera un mueble mas")


# ─── Una cota dice DE DÓNDE SALE, o no se escribe ────────────────────────────
#
# 23/08/2026, auditoría. El alzado rotulaba «~60» tres veces por motivos
# distintos, y una de ellas era mentira: cuando un módulo llegaba sin ancho, el
# código ponía 60 de respaldo para poder dibujar algo y luego lo rotulaba como
# si fuera una estimación LEÍDA DEL DIBUJO. Nadie había medido ni deducido ese
# 60. Y el «~» hacía daño en vez de ayudar: le daba credibilidad de estimación
# a un número de relleno.
#
# La regla 7 de CLAUDE.md no admite matices: lo que no se sabe va vacío o con
# «?». Este papel va a fábrica.

def test_una_medida_escrita_se_rotula_a_secas(geom):
    """Un número que puso el cliente es un DATO: ni «~» ni nada."""
    ancho, cota, origen = geom.cota_de_ancho({"ancho": 90, "medida_escrita": True})
    assert (ancho, cota, origen) == (90, "90", "escrita")


def test_un_ancho_derivado_se_rotula_con_virgulilla(geom):
    """Lo cuadró el validador contra la pared real: estimación con fundamento."""
    ancho, cota, origen = geom.cota_de_ancho({"ancho": 60})
    assert (ancho, cota, origen) == (60, "~60", "estimada")


def test_un_modulo_sin_ancho_NO_se_rotula_con_un_numero(geom):
    """CANDADO de la regla 7: lo que no se sabe se dice, no se rellena."""
    ancho, cota, origen = geom.cota_de_ancho({})
    assert cota == "?", (
        f"un módulo sin ancho se está rotulando «{cota}». Ese número no lo ha "
        f"medido ni deducido nadie: es el valor de respaldo del código, y va "
        f"impreso en un plano que se manda a cortar.")
    assert origen == "sin_dato"
    assert ancho == geom.ANCHO_DIBUJO_SIN_DATO, (
        "el módulo tiene que seguir DIBUJÁNDOSE —un alzado con un hueco tampoco "
        "sirve—: lo que no puede es escribirse la cota")


def test_un_ancho_a_cero_tampoco_cuela(geom):
    """0 no es una medida; es la forma habitual de que llegue un hueco vacío."""
    _, cota, origen = geom.cota_de_ancho({"ancho": 0})
    assert (cota, origen) == ("?", "sin_dato")


def test_dibujar_y_rotular_son_DOS_cosas(geom):
    """El fondo del asunto: se dibuja con 60 y se rotula «?». A la vez."""
    ancho, cota, _ = geom.cota_de_ancho({"ancho": None})
    assert ancho > 0 and cota == "?", (
        "o se dibuja y no se rotula, o se ha vuelto a confundir el ancho de "
        "dibujo con la medida del mueble")


def test_el_alzado_pinta_la_cota_que_diga_el_helper(geom):
    """Que la ruta USE esto, no que lo copie.

    Un helper probado y una ruta que decide por su cuenta es tener la regla
    escrita en dos sitios, o sea tenerla en ninguno."""
    ruta = os.path.join(BACKEND, "routes", "estudio_cocinas.py")
    with open(ruta, encoding="utf-8") as f:
        fuente = f.read()
    assert "cota_de_ancho(e)" in fuente, \
        "el alzado ha vuelto a decidir la cota por su cuenta"
    i = fuente.index("cota_de_ancho(e)")
    alrededor = fuente[i - 400:i + 400]
    assert 'or 60' not in alrededor, \
        "ha vuelto el ancho de respaldo a mano al lado del helper"
