# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
LA LETRA DE LA REFERENCIA DICE LO QUE LLEVA DENTRO EL MUEBLE.

El master, 11/09/2026: «la referencia CHMG no detecta el precio de las gavetas
para el coste de artículos».

En la tarifa MV, COLUMNA_HORNO y COLUMNA_HORNO_MICRO son UNA familia cada una
con cuatro referencias dentro, y lo que las diferencia es el interior:

    CH60 · CHPC60 · CHGC60 · CHC60
    CHM60 · CHMG60 · CHMC60 · CHMCG60

La regla de despiece era la misma para las cuatro, así que un CHMG60D/I salía
del escandallo con la casilla de GAVETAS vacía: 54,37 € de herraje que no se
contaban. No da ningún error — da un COSTE más bajo y un MARGEN más alto que
el real, que es la clase de número que nadie mira dos veces porque gusta. En
una cocina con dos columnas así son 109 € que se creen ganados.

CÓMO SE COMPRUEBA: EJECUTANDO las funciones de verdad en node, no leyendo si
la palabra «gavFn» aparece en el fichero. Las lecciones de las reglas 31 y 34
son justo esa: un candado que lee literales pasa en verde con el código roto
—en la tarifa ACB costó una caída en producción—, y uno que reescribe la
lógica en Python protege la copia, no el original.

LO QUE NO SE INVENTA (regla 7): cuántos cajones llevan CHC60 y CHMC60, la «C»
sola. En los bajos, la «C» sola de un BCG son TRES cajones y la de un BGC es
UNO, así que la letra no basta. Están pendientes de confirmar con el master y
cuentan 0, que es lo que contaban antes: no se mejora, pero tampoco se inventa
una cifra que acabaría en un pedido a proveedor.
"""
import json
import os
import re
import shutil
import subprocess
import sys

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RENT = os.path.join(RAIZ, "frontend", "src", "components", "RentabilidadMV.jsx")
TARIFA = os.path.join(RAIZ, "backend", "data", "mv_tarifas_oficiales.json")

FAMILIAS = ("COLUMNA_HORNO", "COLUMNA_HORNO_MICRO")


def _regla(familia):
    """La entrada de RULES tal cual está escrita, hasta su llave de cierre."""
    with open(RENT, "r", encoding="utf-8") as f:
        cuerpo = f.read()
    m = re.search(r"^  %s: \{" % familia, cuerpo, re.M)
    assert m, "%s ya no está en RULES" % familia
    i = m.end() - 1
    nivel, j = 0, i
    while j < len(cuerpo):
        if cuerpo[j] == "{":
            nivel += 1
        elif cuerpo[j] == "}":
            nivel -= 1
            if nivel == 0:
                return cuerpo[i:j + 1]
        j += 1
    raise AssertionError("no se cierra la regla de %s" % familia)


def _cuenta_en_node(familia, codigos):
    """Corre `gavFn` y `cajFn` DE VERDAD sobre cada código."""
    node = shutil.which("node")
    if not node:
        pytest.skip("no hay node en esta máquina")
    regla = _regla(familia)
    guion = (
        "const R = %s;\n"
        "const codigos = %s;\n"
        "const out = {};\n"
        "for (const c of codigos) out[c] = {\n"
        "  gav: R.gavFn ? R.gavFn(c) : (R.gavetas || 0),\n"
        "  caj: R.cajFn ? R.cajFn(c) : (R.cajones || 0) };\n"
        "console.log(JSON.stringify(out));\n" % (regla, json.dumps(codigos))
    )
    r = subprocess.run([node, "-e", guion], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def test_CHMG_CUENTA_SU_GAVETA():
    """El fallo que vio el master, en sus dos manos (D/I y de dos puertas)."""
    r = _cuenta_en_node("COLUMNA_HORNO_MICRO", ["CHMG60D/I", "CHMG60"])
    for cod, v in r.items():
        assert v["gav"] == 1, (
            "%s no cuenta su gaveta: el escandallo deja la casilla vacía y el "
            "margen sale más alto que el real" % cod)


def test_LA_COLUMNA_SIN_GAVETA_NO_SE_INVENTA_UNA():
    """Al revés también cuenta: cobrar un herraje que el mueble no lleva sube
    el coste y hunde el margen de un mueble que estaba bien."""
    r = _cuenta_en_node("COLUMNA_HORNO_MICRO", ["CHM60D/I", "CHM60", "CHMC60"])
    for cod, v in r.items():
        assert v["gav"] == 0, "%s se está inventando una gaveta" % cod
    r = _cuenta_en_node("COLUMNA_HORNO", ["CH60D/I", "CH60", "CHPC60", "CHC60"])
    for cod, v in r.items():
        assert v["gav"] == 0, "%s se está inventando una gaveta" % cod


def test_LA_G_DE_LA_COLUMNA_DE_HORNO_TAMBIEN_ES_UNA_GAVETA():
    """CHGC y CHMCG llevan la misma letra por el mismo motivo. Un arreglo
    puesto en una referencia y no en sus hermanas no es un arreglo (regla 1)."""
    assert _cuenta_en_node("COLUMNA_HORNO", ["CHGC60", "CHGC60D/I"])["CHGC60"]["gav"] == 1
    assert _cuenta_en_node("COLUMNA_HORNO_MICRO", ["CHMCG60"])["CHMCG60"]["gav"] == 1


def test_LA_C_DE_LAS_MIXTAS_ES_UN_CAJON():
    """CHPC, CHGC y CHMCG llevan además un cajón."""
    r = _cuenta_en_node("COLUMNA_HORNO", ["CHPC60", "CHGC60", "CH60"])
    assert r["CHPC60"]["caj"] == 1
    assert r["CHGC60"]["caj"] == 1
    assert r["CH60"]["caj"] == 0
    assert _cuenta_en_node("COLUMNA_HORNO_MICRO", ["CHMCG60", "CHM60"])["CHMCG60"]["caj"] == 1


def test_CHM_NO_SE_LLEVA_LA_GAVETA_DE_CHMG_POR_EMPEZAR_IGUAL():
    """La trampa de leer códigos por prefijo: `CHM` está DENTRO de `CHMG`, y
    `CH` dentro de todos. Si el patrón no estuviera anclado al principio, o
    fuera un `includes`, un CHM60 pagaría la gaveta del CHMG."""
    r = _cuenta_en_node("COLUMNA_HORNO_MICRO", ["CHM60", "CHMG60"])
    assert (r["CHM60"]["gav"], r["CHMG60"]["gav"]) == (0, 1)
    r = _cuenta_en_node("COLUMNA_HORNO", ["CH60", "CHGC60"])
    assert (r["CH60"]["gav"], r["CHGC60"]["gav"]) == (0, 1)


def test_LAS_REFERENCIAS_QUE_SE_COMPRUEBAN_SON_LAS_DE_LA_TARIFA():
    """Que la lista de arriba no se quede vieja: si MV añade una referencia a
    estas familias, esta prueba obliga a decidir qué lleva dentro en vez de
    dejarla contando cero en silencio."""
    with open(TARIFA, "r", encoding="utf-8") as f:
        tarifa = json.load(f)
    conocidas = {
        "COLUMNA_HORNO": {"CH60", "CH60D/I", "CHPC60", "CHPC60D/I",
                          "CHGC60", "CHGC60D/I", "CHC60", "CHC60D/I"},
        "COLUMNA_HORNO_MICRO": {"CHM60", "CHM60D/I", "CHMG60", "CHMG60D/I",
                                "CHMC60", "CHMC60D/I", "CHMCG60", "CHMCG60D/I"},
    }
    for t, fams in tarifa["tariffs"].items():
        for fam in FAMILIAS:
            items = set((fams.get(fam) or {}).get("items", {}))
            nuevas = items - conocidas[fam]
            assert not nuevas, (
                "referencias nuevas en %s (%s): %s. Hay que decidir cuántos "
                "cajones y gavetas llevan antes de tarifarlas — mientras tanto "
                "cuentan 0 y el margen sale más alto que el real"
                % (fam, t, sorted(nuevas)))


def test_LA_GAVETA_LLEGA_AL_COSTE_Y_NO_SE_QUEDA_EN_UN_CONTADOR():
    """El contador sin precio no arregla nada: se comprueba que el despiece
    multiplica las gavetas por su tarifa, que es lo que el master echaba en
    falta («no detecta el PRECIO de las gavetas»)."""
    with open(RENT, "r", encoding="utf-8") as f:
        cuerpo = f.read()
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from jsx_limpio import sin_comentarios
    limpio = sin_comentarios(cuerpo)
    assert "const gavetas = (R.gavFn ? R.gavFn(cod) : (R.gavetas || 0));" in limpio
    assert re.search(r"gav:\s*gavetas\s*\*\s*\(Number\(p\.gaveta\)\s*\|\|\s*0\)", limpio), (
        "el despiece ya no multiplica las gavetas por su precio: contarlas sin "
        "cobrarlas deja el coste igual de corto que antes")
