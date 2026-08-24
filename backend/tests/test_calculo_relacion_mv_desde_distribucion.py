# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""El puente: la distribución del Estudio 3D → muebles MV de catálogo.

Cierra el circuito. Lo que la IA lee del croquis (y el master corrige a mano)
se convierte en códigos MV con su precio, listos para revisar y pedir.

El puente NO pone precios: escribe la notación y de tarifar se encarga
`mv_relacion`, que lee el catálogo oficial y ya estaba probado. Estas pruebas
ejecutan LOS DOS de verdad, porque el fallo que tuvo esto al escribirse solo se
veía haciéndolo:

    la cocina entera en UNA línea con «+»  →  «(altura 80)» se lo comía todo

`parse_relacion` busca «altura N» una vez por RENGLÓN y borra los paréntesis
antes de trocear. Con todo junto, los siete muebles salían a 80 cm — incluidos
los ALTOS, que a 80 no existen (van a 70 o a 90) y que valen distinto en cada
altura: un A60 son 156,51 € a 70 y 169,83 € a 90. El precio salía del mueble
equivocado sin un solo error por pantalla.
"""
import importlib.util
import os
import sys

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BACKEND = os.path.join(RAIZ, "backend")


def _cargar(nombre, relativo):
    spec = importlib.util.spec_from_file_location(nombre, os.path.join(BACKEND, relativo))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = mod
    spec.loader.exec_module(mod)
    return mod


puente = _cargar("puente_mv_test", os.path.join("services", "distribucion_a_mv.py"))
mv = _cargar("mv_relacion_test", os.path.join("services", "mv_relacion.py"))


def _cocina():
    return {
        "tipo": "lineal",
        "paredes": [{"nombre": "Pared 1", "ancho": 360, "alto": 240}],
        "elementos": [
            {"id": "bajo_fregadero", "label": "Bajo fregadero", "pared_idx": 0, "posicion_cm": 0, "ancho": 90, "fila": "bajo"},
            {"id": "lavavajillas", "label": "Lavavajillas", "pared_idx": 0, "posicion_cm": 90, "ancho": 60, "fila": "bajo"},
            {"id": "bajo", "label": "Bajo", "pared_idx": 0, "posicion_cm": 150, "ancho": 60, "fila": "bajo"},
            {"id": "frigorifico", "label": "Columna frigo", "pared_idx": 0, "posicion_cm": 210, "ancho": 60, "fila": "bajo"},
            {"id": "alto", "label": "Alto", "pared_idx": 0, "posicion_cm": 0, "ancho": 80, "fila": "alto"},
            {"id": "relleno", "label": "Relleno", "pared_idx": 0, "posicion_cm": 270, "ancho": 45, "fila": "bajo"},
        ],
    }


def _tarifar(dist=None, **kw):
    r = puente.distribucion_a_relacion(dist or _cocina(), **kw)
    return r, mv.parse_relacion_text(r["notacion"], kw.get("tarifa", "T1"))


# ── El fallo que motivó este fichero ────────────────────────────────────────

def test_cada_mueble_se_tarifa_por_SU_altura():
    """CANDADO. Un mueble por renglón: si se juntan, la primera altura se las
    come todas y el precio sale de otro mueble."""
    r, tarifadas = _tarifar(alto_altos=90)
    porc = {t["cod"]: t for t in tarifadas}
    alto = [t for t in tarifadas if t["familia"] == "ALTO"][0]
    assert alto["alto"] == 90, (
        f"el alto se ha tarifado a {alto['alto']} cm en vez de a 90: la altura de "
        "un mueble se la ha comido la de otro.")
    columna = [t for t in tarifadas if t["familia"] == "COLUMNA_FRIGO"][0]
    assert columna["alto"] == 200, \
        f"la columna se ha tarifado a {columna['alto']} cm en vez de a 200"
    bajos = [t for t in tarifadas if t["familia"] in ("BAJO", "BAJO_FREGADERO")]
    assert all(b["alto"] == 80 for b in bajos), \
        "algún bajo no se ha tarifado a 80, que es la única altura que fabrica esta casa"
    assert porc  # silencia el linter sin quitar el dato de contexto


def test_la_altura_de_un_alto_CAMBIA_el_precio():
    """La prueba de arriba no valdría de nada si dar la altura fuese indiferente."""
    _, a70 = _tarifar(alto_altos=70)
    _, a90 = _tarifar(alto_altos=90)
    p70 = [t for t in a70 if t["familia"] == "ALTO"][0]["pvp"]
    p90 = [t for t in a90 if t["familia"] == "ALTO"][0]["pvp"]
    assert p90 > p70, (
        f"un alto de 90 ({p90} €) no sale más caro que uno de 70 ({p70} €): "
        "si la altura no cambia el precio, esta prueba no protege nada.")


def test_la_notacion_va_UN_MUEBLE_POR_LINEA():
    r = puente.distribucion_a_relacion(_cocina())
    renglones = [x for x in r["notacion"].split("\n") if x.strip()]
    assert len(renglones) == len(r["lineas"]), \
        "la notación ha vuelto a juntar muebles en el mismo renglón"


# ── Reglas de la casa que el puente no puede saltarse ───────────────────────

def test_el_lavavajillas_NO_lleva_casco():
    """CLAUDE.md, regla 6: va en hueco. Ponerle un mueble infla el pedido al
    proveedor con un casco que no existe."""
    r = puente.distribucion_a_relacion(_cocina())
    codigos = [x["codigo"] for x in r["lineas"]]
    assert not any(c.startswith("LV") for c in codigos)
    fuera = {x["id"] for x in r["sin_codigo"]}
    assert "lavavajillas" in fuera, "al lavavajillas se le ha puesto un casco MV"


def test_el_bajo_fregadero_SI_es_un_mueble():
    """La otra mitad de la regla 6, que es la que se olvida."""
    r = puente.distribucion_a_relacion(_cocina())
    assert any(x["codigo"].startswith("BF") for x in r["lineas"]), \
        "el bajo fregadero ha desaparecido de la relación: es un MUEBLE"


def test_el_relleno_no_se_pide_a_MV():
    r = puente.distribucion_a_relacion(_cocina())
    assert "relleno" in {x["id"] for x in r["sin_codigo"]}, \
        "el relleno se ha colado como mueble de catálogo: es una pieza a medida"


def test_no_se_inventa_un_codigo_que_no_existe_en_la_tarifa():
    """CANDADO (regla de oro). MV no hace bajos de 15: eso no es un mueble."""
    dist = {"paredes": [{"nombre": "P1", "ancho": 300, "alto": 240}],
            "elementos": [{"id": "bajo", "label": "Bajo", "pared_idx": 0,
                           "posicion_cm": 0, "ancho": 15, "fila": "bajo"}]}
    r = puente.distribucion_a_relacion(dist)
    assert not r["lineas"], "se ha inventado un B15, que no existe en la tarifa MV"
    assert r["sin_codigo"], "no se dice por qué no hay mueble"
    assert "15" in r["sin_codigo"][0]["motivo"]


def test_todo_lo_que_sale_con_codigo_se_tarifa_de_verdad():
    """Si el puente propone un código, tiene que tener precio. Un mueble en la
    relación sin precio es un mueble que nadie va a saber cuánto cuesta."""
    r, tarifadas = _tarifar()
    assert len(tarifadas) == len(r["lineas"]), \
        f"el tarificador reconoció {len(tarifadas)} de {len(r['lineas'])} líneas"
    for t in tarifadas:
        assert t.get("cod"), f"línea sin código: {t}"
        assert (t.get("pvp") or 0) > 0, f"línea sin precio: {t.get('cod')}"


# ── La mano (D/I) se PROPONE, no se deduce ──────────────────────────────────

def test_la_mano_va_marcada_como_propuesta():
    """No sale del diseño: el croquis no dice hacia dónde abre una puerta. Si
    no se marca, una suposición del programa pasa por dato."""
    r = puente.distribucion_a_relacion(_cocina())
    con_mano = [x for x in r["lineas"] if x["mano"]]
    assert con_mano, "ningún mueble lleva mano: hasta 60 cm todos son de una puerta"
    assert all(x["mano_propuesta"] for x in con_mano), \
        "la mano ya no se marca como propuesta y parece leída del diseño"


def test_de_70_para_arriba_no_hay_mano_que_elegir():
    """En el catálogo MV, de 70 en adelante son de dos puertas y no llevan D/I.
    Pedir la mano ahí sería preguntar por algo que no existe."""
    r = puente.distribucion_a_relacion(_cocina())
    anchos_grandes = [x for x in r["lineas"] if x["ancho"] >= 70]
    assert anchos_grandes, "el ejemplo ya no tiene ningún mueble de 70 o más"
    assert all(x["mano"] is None for x in anchos_grandes), \
        "se está pidiendo la mano de un mueble de dos puertas"


def test_cambiar_la_mano_no_cambia_el_precio():
    """Un B60D y un B60I son el mismo mueble con la puerta al otro lado. Si el
    precio bailara, es que se está tarifando contra otra familia."""
    d = mv.parse_relacion_text("1 b60d (altura 80)", "T1")[0]
    i = mv.parse_relacion_text("1 b60i (altura 80)", "T1")[0]
    assert d["pvp"] == i["pvp"], f"B60D vale {d['pvp']} y B60I {i['pvp']}"


def test_una_puerta_y_dos_puertas_son_muebles_DISTINTOS():
    """Por eso el cambio «→2» vuelve a pedir el precio al catálogo en vez de
    quedarse con el que ya tenía."""
    una = mv.parse_relacion_text("1 b60d (altura 80)", "T1")[0]
    dos = mv.parse_relacion_text("1 b60 (altura 80)", "T1")[0]
    assert una["cod"] != dos["cod"], \
        "B60D y B60 resuelven al mismo código: no se distinguen una y dos puertas"


# ── Y que el endpoint haga lo mismo que estas pruebas ───────────────────────

def test_el_endpoint_devuelve_la_relacion_tarifada():
    os.environ.setdefault("JWT_SECRET", "x" * 64)
    if BACKEND not in sys.path:
        sys.path.insert(0, BACKEND)
    import asyncio
    try:
        from routes.estudio_cocinas import relacion_mv
    except Exception as e:                      # pragma: no cover
        pytest.fail(f"no se pudo importar el endpoint: {e}")
    r = asyncio.run(relacion_mv({"distribucion": _cocina()}))
    assert r["success"] and r["lineas"]
    assert all(x.get("pvp") for x in r["lineas"]), "alguna línea vuelve sin precio"
    assert r["totalPvp"] == round(sum(x["pvp"] for x in r["lineas"]), 2)
    assert not r["sinPrecio"]


def test_el_endpoint_no_reparte_precios_a_ojo():
    """Si el tarificador devolviera menos líneas de las que se le mandaron, un
    precio acabaría en el mueble equivocado. Antes que eso, se falla."""
    codigo = open(os.path.join(BACKEND, "routes", "estudio_cocinas.py"), encoding="utf-8").read()
    i = codigo.index("async def relacion_mv")
    cuerpo = codigo[i:codigo.index("\n@router", i)]
    assert "len(tarifadas) != len(lineas)" in cuerpo, \
        "ya no se comprueba que se hayan tarifado TODAS las líneas"
