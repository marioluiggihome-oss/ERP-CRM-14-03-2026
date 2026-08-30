# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
UN MUEBLE ANCHO LLEVA DOS PUERTAS. Y DE AHÍ SALE EL HERRAJE QUE SE PIDE.

El master, 30/08, con un alzado del Estudio 3D delante: «al pulsar poner
medidas, no calcula bien los muebles».

Y no los calculaba. El alzado contaba UNA PUERTA POR MUEBLE, fuera del ancho que
fuera: un «Mueble fregadero 100×80» contaba una, y un «Mueble alto 100×70»,
otra. De ese recuento salen las cifras del pie del plano:

    bisagras  = puertas × 2
    tiradores = puertas + cajones

O sea que un frente de 100 pedía LA MITAD del herraje. Y un herraje corto no da
ningún error: se ve el día que el montador está en la obra con la cocina
delante y le faltan bisagras.

EL CORTE NO SE INVENTA: SALE DE LA TARIFA. En `mv_tarifas_oficiales.json`, los
códigos con sufijo `D/I` —los de UNA puerta, derecha o izquierda— llegan hasta
60 en BAJO, ALTO, BAJO_FREGADERO, BAJO_PUERTA_CAJON, ALTO_VITRINA y
COLUMNA_DESPENSERO; de 60 en adelante los códigos van SIN `D/I`, que es como MV
escribe los de DOS puertas (CLAUDE.md, «Nomenclatura MV»). En el 60 clavado
existen los dos y se toma el de una hoja, que es el corriente.

Este candado comprueba las dos mitades: que la regla es la que dice la tarifa, y
que la tarifa sigue diciendo eso.
"""
import ast
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("JWT_SECRET", "secreto-de-pruebas-largo-y-aleatorio-0123456789")

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA = os.path.join(BACKEND, "routes", "estudio_cocinas.py")
TARIFA = os.path.join(BACKEND, "data", "mv_tarifas_oficiales.json")

# Las familias donde MV distingue una hoja de dos con el sufijo `D/I`.
FAMILIAS_CON_D_I = ("BAJO", "ALTO", "BAJO_FREGADERO", "BAJO_PUERTA_CAJON",
                    "ALTO_VITRINA", "COLUMNA_DESPENSERO")


def _hojas_de():
    """`hojas_de` sacada del fichero, sin arrastrar matplotlib ni el router."""
    with open(RUTA, "r", encoding="utf-8") as f:
        arbol = ast.parse(f.read())
    fn = next((n for n in ast.walk(arbol)
               if isinstance(n, ast.FunctionDef) and n.name == "hojas_de"), None)
    assert fn is not None, "ya no existe `hojas_de` en el alzado"
    ambito = {}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), RUTA, "exec"), ambito)
    return ambito["hojas_de"]


def _anchos(codigos, con_di):
    import re
    fuera = set()
    for c in codigos:
        if c.endswith("D/I") != con_di:
            continue
        m = re.search(r"(\d{2,3})", c)
        if m:
            fuera.add(int(m.group(1)))
    return fuera


def test_LA_TARIFA_SIGUE_DICIENDO_DONDE_ESTA_EL_CORTE():
    """Si MV cambiara la nomenclatura, la regla de abajo dejaría de valer y hay
    que enterarse aquí, no en una obra."""
    with open(TARIFA, "r", encoding="utf-8") as f:
        t = json.load(f)["tariffs"]["T1"]
    for fam in FAMILIAS_CON_D_I:
        items = (t.get(fam) or {}).get("items") or {}
        assert items, f"la familia {fam} ha desaparecido de la tarifa"
        una = _anchos(items, True)
        dos = _anchos(items, False)
        assert una, f"{fam}: ya no hay códigos D/I (una hoja)"
        assert max(una) <= 60, (
            f"{fam}: hay un código de UNA puerta de más de 60 ({sorted(una)}). "
            "El corte del alzado se apoya en que no los haya")
        assert dos and min(dos) >= 60, (
            f"{fam}: hay códigos SIN D/I por debajo de 60 ({sorted(dos)})")


def test_HASTA_60_UNA_PUERTA_POR_ENCIMA_DOS():
    hojas = _hojas_de()
    for w in (15, 20, 30, 40, 45, 50, 60):
        assert hojas(w) == 1, f"un mueble de {w} no lleva dos puertas"
    for w in (70, 80, 90, 100, 120):
        assert hojas(w) == 2, (
            f"un mueble de {w} sigue contando UNA puerta: se pediría la mitad "
            "del herraje y no daría ningún error hasta la obra")


def test_EL_BORDE_DE_60_ES_UNA_HOJA():
    """En el 60 clavado la tarifa tiene las dos versiones (B60D/I y B60). Se
    toma la de una hoja, que es la corriente."""
    assert _hojas_de()(60) == 1
    assert _hojas_de()(60.5) == 2


def test_UN_ANCHO_QUE_NO_SE_SABE_NO_INVENTA_HERRAJE():
    """Sin ancho no se pueden pedir dos puertas «por si acaso»: pedir de más se
    paga (CLAUDE.md, regla 7 — lo que no se sabe no se rellena)."""
    hojas = _hojas_de()
    for malo in (None, "", "ancho", {}, []):
        assert hojas(malo) == 1, f"con ancho {malo!r} se están pidiendo dos puertas"


def test_EL_HERRAJE_Y_EL_DIBUJO_USAN_LA_MISMA_REGLA():
    """Que no se arregle el dibujo y se quede el recuento corto, o al revés: el
    plano diría dos hojas y el pie del plano pediría una bisagra para ellas."""
    with open(RUTA, "r", encoding="utf-8") as f:
        cuerpo = f.read()
    assert cuerpo.count("hojas_de(w)") >= 3, (
        "el dibujo de la puerta, el alto y el bajo tienen que salir todos de "
        "`hojas_de`: si alguno se queda con el 1 fijo, el plano y el herraje "
        "dicen cosas distintas")
    assert 'herr["puertas"] += 1' not in cuerpo, (
        "queda un sitio que suma UNA puerta fija, sin mirar el ancho")


def test_LA_COLUMNA_SIGUE_CONTANDO_SUS_DOS_PUERTAS():
    """Una columna de horno lleva dos puertas por su ALTURA (arriba y abajo), no
    por su ancho: 60 de ancho y dos hojas. No se toca."""
    with open(RUTA, "r", encoding="utf-8") as f:
        cuerpo = f.read()
    assert 'herr["puertas"] += 2' in cuerpo, (
        "la columna ha dejado de contar sus dos puertas")


# ─── EL DIBUJO TIENE QUE SER LA COCINA ──────────────────────────────────────
#
# El master, 30/08: «lo de poner medidas me refiero al dibujo que hace, que no
# cuadra con el diseño». Y no cuadraba, por tres sitios: la placa y los
# electrodomésticos salían dibujados como armarios con su aspa de puerta, y el
# fregadero salía sin fregadero.

def _fuente():
    with open(RUTA, "r", encoding="utf-8") as f:
        return f.read()


def _cuerpo_de(nombre_conjunto):
    """El conjunto de tipos, leído del fichero."""
    import re
    m = re.search(rf"^\s+{nombre_conjunto} = \{{(.+?)\}}", _fuente(), re.S | re.M)
    assert m, f"ya no existe el conjunto {nombre_conjunto}"
    return {t.strip().strip('"\'') for t in m.group(1).split(",")
            if t.strip() and not t.strip().startswith("#")}


def test_LOS_ELECTRODOMESTICOS_NO_SON_MUEBLES():
    """Regla 6: van en HUECO, SIN CASCO. Se dibujaban como un bajo cualquiera,
    con aspa de puerta, y encima pedían bisagras para una lavadora."""
    electro = _cuerpo_de("ELECTRO")
    for aparato in ("lavadora", "secadora", "horno"):
        assert aparato in electro, f"«{aparato}» sigue tratándose como un mueble"
    fuente = _fuente()
    assert "tipo not in HOB and tipo not in ELECTRO" in fuente, (
        "los electrodomésticos vuelven a contar puerta y tirador de mueble")


def test_EL_LAVAVAJILLAS_ES_LA_EXCEPCION_DE_LA_REGLA_6():
    """«Lavavajillas = electrodoméstico. Su puerta de integración = material
    nuestro» (CLAUDE.md, regla 6). Se dibuja como aparato, pero su frente SÍ
    cuenta: es la excepción que más fácil se olvida."""
    lv = _cuerpo_de("LAVAVAJILLAS")
    assert "lavavajillas" in lv
    assert "lavavajillas" not in _cuerpo_de("ELECTRO"), (
        "el lavavajillas ha caído en la lista de los que NO llevan puerta "
        "nuestra: su puerta de integración es material de la casa y se dejaría "
        "de pedir")


def test_EL_ASPA_DE_PUERTA_NO_SE_PINTA_SOBRE_LO_QUE_NO_LA_TIENE():
    """Una placa va apoyada en la encimera y un aparato va en hueco: ninguno
    tiene puerta. El aspa encima es lo que hacía que el alzado no se pareciera
    a la cocina."""
    fuente = _fuente()
    assert "if tipo not in HOB and not _es_electro:" in fuente, (
        "el aspa de puerta se vuelve a pintar sobre la placa o sobre un "
        "electrodoméstico")


def test_EL_FREGADERO_SE_DIBUJA():
    """`SINK` estaba definido desde el principio y NO LO USABA NADIE: el mueble
    del fregadero salía como un armario, sin seno ni grifo. En un alzado de
    cocina es lo primero que se echa en falta."""
    fuente = _fuente()
    assert "SINK = {" in fuente, "ha desaparecido la lista de tipos de fregadero"
    assert "tipo in SINK" in fuente, (
        "`SINK` vuelve a estar definido y sin usar: el fregadero se dibuja como "
        "un armario cualquiera")


def test_EL_PIE_DEL_PLANO_DICE_LO_QUE_NO_HA_CONTADO():
    """Lo mismo que ya se hacía con los altos propuestos: si algo queda fuera
    del herraje, se dice — o alguien pregunta en la obra por la puerta de la
    lavadora."""
    fuente = _fuente()
    assert 'herr["electro"] += 1' in fuente
    assert "sin herraje de mueble" in fuente, (
        "el pie del plano ya no avisa de los electrodomésticos que van en hueco")
