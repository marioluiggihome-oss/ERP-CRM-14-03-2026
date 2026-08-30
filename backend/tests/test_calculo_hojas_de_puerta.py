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
