# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
UN ALTO ABATIBLE LLEVA EL HERRAJE DE ELEVACIÓN DE BLUM.

El master, 31/08: «cuando meta un mueble abatible alto que meta el herraje hkt
de Blum».

QUÉ FALTABA. El frente de un AA80 no gira de lado: sube, y lo sube un Aventos
HK top. Es la pieza cara del mueble y no estaba en el escandallo, así que el
coste de TODOS los altos abatibles salía corto y su margen más alto que el real.
En la pantalla que lo destapó, el AA80 decía 19,28 € de herrajes —cuatro
bisagras y dos colgadores— para un mueble cuyo herraje de verdad es el
mecanismo.

EL PRECIO NO SE INVENTA (CLAUDE.md, regla 7). El campo arranca VACÍO y se teclea
en «Proveedores», como el resto de la tarifa de herraje. Pero vacío tiene un
problema propio: el abatible sale costando exactamente lo mismo que antes de que
el herraje existiera —mismo número, misma pinta de bueno— y el margen sigue
mintiendo sin que nada avise. Por eso se CUENTA y se AVISA al lado del coste,
igual que las líneas sin casco.

LO QUE SE PROTEGE
-----------------
1. La regla del abatible lleva el herraje, y el cálculo lo suma al coste.
2. El precio arranca vacío: nadie ha puesto un número plausible.
3. Un abatible sin ese precio se marca, se cuenta y se dice en pantalla.
4. Se puede teclear desde el Presupuestador, sin ir a otra pantalla.
5. El desglose lo enseña: un coste que sube sin decir por qué es peor que uno
   corto.
"""
import os
import re

import pytest

from jsx_limpio import sin_comentarios

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(RAIZ, "frontend", "src")
RENT = os.path.join(SRC, "components", "RentabilidadMV.jsx")
CM3 = os.path.join(SRC, "components", "CocinaMontada3.jsx")


def _lee(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        return sin_comentarios(f.read())


def _bloque(cuerpo, arranque, cierre):
    i = cuerpo.index(arranque)
    return cuerpo[i:cuerpo.index(cierre, i) + len(cierre)]


def test_EL_ABATIBLE_LLEVA_EL_HERRAJE():
    """La regla del mueble, no una lista de códigos escrita aparte."""
    cuerpo = _lee(RENT)
    regla = _bloque(cuerpo, "  ALTO_ABATIBLE: {", "},")
    assert re.search(r"\bhkt:\s*1\b", regla), (
        f"un alto abatible no lleva el herraje de elevación: {regla.strip()}")
    # Y SOLO el abatible: un alto normal gira sobre bisagras y no lleva Aventos.
    reglas = _bloque(cuerpo, "export const RULES = {", "\n};")
    con_hkt = [ln.split(":")[0].strip() for ln in reglas.split("\n") if re.search(r"\bhkt:", ln)]
    assert con_hkt == ["ALTO_ABATIBLE"], (
        f"el herraje de elevación se le está cobrando a muebles que no se abaten: {con_hkt}")


def test_EL_CALCULO_LO_SUMA_AL_COSTE():
    """Devolverlo sin sumarlo lo dejaría de adorno en el desglose."""
    cuerpo = _lee(RENT)
    linea = _bloque(cuerpo, "const hkt = ", ";")
    assert "(R.hkt || 0) * (Number(p.hkt) || 0)" in linea, (
        f"el herraje no sale de la regla del mueble y de la tarifa: {linea.strip()}")
    formula = _bloque(cuerpo, "const costeHerrajes", "* 100) / 100;")
    assert "+ hkt" in formula, (
        "el herraje de elevación no entra en el coste de los herrajes")


def test_EL_PRECIO_ARRANCA_VACIO_Y_NO_INVENTADO():
    """Un número plausible puesto por rellenar se queda para siempre: nadie lo
    vuelve a mirar y el margen del abatible miente sin dar un error (regla 7)."""
    cuerpo = _lee(RENT)
    defecto = _bloque(cuerpo, "export const MV_COSTES_DEFAULT = {", "\n};")
    m = re.search(r"^\s*hkt:\s*(.+?),\s*$", defecto, re.M)
    assert m, "el herraje de Blum no está en la tarifa de proveedor"
    assert m.group(1).strip() in ("''", '""'), (
        f"el precio del herraje de Blum viene con un número puesto: {m.group(1)}. "
        "No se inventa una tarifa de proveedor.")


def test_UN_ABATIBLE_SIN_PRECIO_DEL_HERRAJE_SE_MARCA():
    """Vacío, el mueble cuesta lo mismo que antes de que el herraje existiera:
    mismo número, misma pinta de bueno, y el margen mintiendo."""
    cuerpo = _lee(RENT)
    linea = _bloque(cuerpo, "const faltaHkt =", ";")
    assert "!!R.hkt && !(Number(p.hkt) > 0)" in linea, (
        f"no se detecta el abatible al que le falta la tarifa del herraje: {linea.strip()}")
    # EL `return` DE `despiece`, no el primero del fichero: `_bloque` busca desde
    # el principio y el primer «  return {» es el de `precioColor`, cien líneas
    # más arriba. Se ancla en una clave que solo devuelve `despiece`.
    devuelto = _bloque(cuerpo, "    fam: familia,", "\n  };")
    assert re.search(r"^\s*faltaHkt,", devuelto, re.M), (
        "`despiece` no devuelve el aviso: la pantalla no podría enseñarlo")


def test_LA_PANTALLA_LO_CUENTA_Y_LO_DICE():
    """Como el aviso de las líneas sin casco, y por el mismo motivo: el número
    que se ve es más bajo que el real."""
    cuerpo = _lee(CM3)
    conteo = _bloque(cuerpo, "const sinHkt =", ";")
    assert "m.despiece?.faltaHkt" in conteo, (
        f"no se cuentan los abatibles sin tarifa del herraje: {conteo.strip()}")
    assert 'data-testid="cm3-aviso-hkt"' in cuerpo, "el aviso no se pinta"
    aviso = _bloque(cuerpo, "{sinHkt.length > 0 && (", ")}")
    assert "sin precio del HKT" in aviso, "el aviso no dice qué falta"
    assert "MÁS ALTO que el real" in aviso, (
        "el aviso no dice qué le pasa al margen, que es lo único que importa de él")


def test_SE_TECLEA_DESDE_EL_PRESUPUESTADOR():
    """Una tarifa que solo se puede cambiar en otra pantalla es una tarifa que
    nadie cambia (master, 31/08: «lo quiero tener a mano todo»)."""
    cuerpo = _lee(CM3)
    tabla = _bloque(cuerpo, "export const TARIFAS_DE_PROVEEDOR = [", "\n];")
    assert "k: 'hkt'" in tabla, (
        "el precio del herraje de Blum no se puede teclear en «Proveedores»")
    assert "Blum" in tabla, "la casilla no dice de quién es el herraje"


def test_EL_DESGLOSE_LO_ENSENA():
    """Un coste que sube sin decir por qué es peor que uno corto."""
    cuerpo = _lee(CM3)
    for lista in ("const herr = [", "{['bisagras', 'patas', 'colg', 'caj', 'gav', 'soportes',"):
        i = cuerpo.index(lista)
        assert "'hkt'" in cuerpo[i:cuerpo.index("]", i)], (
            f"el herraje de elevación no sale en el desglose ({lista.strip()})")
    assert "Elevación abatible (Blum HKT)" in cuerpo, (
        "«En qué se va el coste» no nombra el herraje del abatible")
    assert "HKT Blum</th>" in cuerpo, "al escandallo le falta la columna del herraje"
