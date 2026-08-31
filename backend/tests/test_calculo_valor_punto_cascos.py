# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
EL VALOR DEL PUNTO DE CASCOS: UNO SOLO, Y ES DOS.

El master, 31/08: «el precio parte del PVP, por eso se multiplica por el valor,
que ahora es 2», y «el valor del punto hoy es 2, según la casilla de márgenes»
(Panel Maestro → Márgenes → «Cocina Des-Montada (€/punto)»).

CÓMO SE FORMA EL PRECIO DE UN CASCO, que son DOS cuentas distintas y no se
mezclan:

    PVP   = tarifa ACB × valor del punto        ← lo que paga el cliente
    coste = tarifa ACB × (1 − descuento ACB)    ← lo que paga la casa

El catálogo `cascos.js` trae LA TARIFA, que es el coste antes del descuento
(master: «los precios del catálogo cascos son mi costo, pero de ahí nos hacen un
descuento»). El descuento —hoy un −28 %— lo teclea él «porque puede variar», así
que NO se cablea: vive en el modal de descuentos y por defecto es 0.

EL FALLO, Y LO QUE COSTABA
--------------------------
El valor del punto se leía en CUATRO sitios con CUATRO defectos distintos:

    PricingTab (la casilla de Ajustes) .............. 1,0
    App.js al cargar los ajustes .................... 1,0
    Cascos.jsx (Cocina Desmontada) .................. 1
    getFactorDesmontada (el Presupuestador) ......... 1,30
    y CLAUDE.md decía ............................... 2

Con la casilla vacía —o simplemente mientras los ajustes todavía no han
cargado—, el MISMO casco de 58,52 € de tarifa se vendía a 58,52 € en Cocina
Desmontada y a 76,08 € en el Presupuestador, cuando su PVP son 117,04 €.
Desmontada lo vendía a MITAD DE PRECIO. Sin ningún error, sin ningún aviso, y
con toda la pinta de un presupuesto normal.

Un dato de dinero con cuatro defectos no tiene defecto: tiene cuatro precios.
"""
import json
import os
import shutil
import subprocess

import pytest

from jsx_limpio import sin_comentarios

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(RAIZ, "frontend", "src")
MODULO = os.path.join(SRC, "utils", "valorPuntoCascos.js")
CASCOS = os.path.join(SRC, "components", "Cascos.jsx")
RENT = os.path.join(SRC, "components", "RentabilidadMV.jsx")
APP = os.path.join(SRC, "App.js")
AJUSTES = os.path.join(SRC, "components", "settings", "PricingTab.jsx")


def _lee(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        return f.read()


def _resuelve(estados, guardado=None):
    """Ejecuta la función REAL contra varios estados y devuelve el valor.

    `guardado` es lo que hay en localStorage, que es la OTRA puerta por la que
    entra este dato (la que usa el Presupuestador). Comprobar que la cadena
    `pointValueDesmontada` aparece en el fichero no prueba nada: se comprobó
    rompiéndolo —quitando la lectura de localStorage la prueba seguía en verde,
    porque el nombre sale también en la rama del `state`—. Hay que EJECUTARLO.
    """
    if not shutil.which("node"):
        pytest.skip("hace falta node para ejecutar el cálculo de verdad")
    src = _lee(MODULO).replace("export const", "const")
    js = """
const _guardado = %s;
globalThis.localStorage = _guardado === null ? undefined : {
  getItem: (k) => (k in _guardado ? String(_guardado[k]) : null),
};
%s
const out = [];
for (const st of %s) { out.push(valorPuntoCascos(st)); }
console.log(JSON.stringify(out));
""" % (json.dumps(guardado), src, json.dumps(estados))
    r = subprocess.run(["node", "-e", js], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, f"el módulo no se ejecuta: {r.stderr[-400:]}"
    return json.loads(r.stdout)


def test_EL_VALOR_DE_LA_CASA_ES_DOS():
    """Y se comprueba en el número, no en el nombre de la constante."""
    src = sin_comentarios(_lee(MODULO))
    assert "export const VALOR_PUNTO_CASCOS = 2;" in src, (
        "el valor del punto de cascos ya no es 2. Si el master lo ha cambiado, "
        "esta cifra se actualiza A MANO aquí y en la casilla de Márgenes — no "
        "se ajusta la prueba a lo que salga")


def test_SIN_CASILLA_NO_SE_VENDE_A_MITAD_DE_PRECIO():
    """EL FALLO, TAL CUAL. Con la casilla vacía o los ajustes sin cargar, el
    valor tiene que ser el de la casa, nunca 1 ni 1,30."""
    valores = _resuelve([{}, None, {"settings": {}}])
    assert valores == [2, 2, 2], (
        f"con la casilla vacía el punto sale {valores} en vez de 2: un casco de "
        "58,52 € de tarifa se vendería por 58,52 € o por 76,08 € en vez de por "
        "117,04 €, y nadie vería un error")


def test_LA_CASILLA_DEL_MASTER_MANDA():
    """Es un dato suyo: si lo cambia a 2,5, se usa 2,5."""
    v = _resuelve([{"pointValueDesmontada": 2.5},
                   {"settings": {"cascosPointValue": 3}}])
    assert v == [2.5, 3], f"no se está respetando lo que hay en la casilla: {v}"


def test_UN_VALOR_IMPOSIBLE_NO_VENDE_A_CERO():
    """Sale de una casilla y de localStorage: se puede corromper. Un 0 o un
    texto no pueden dejar el PVP en cero — eso es regalar la cocina."""
    v = _resuelve([{"pointValueDesmontada": 0},
                   {"pointValueDesmontada": "abc"},
                   {"pointValueDesmontada": -3}])
    assert v == [2, 2, 2], (
        f"un valor imposible se está tomando por bueno: {v}. Con un 0 el "
        "presupuesto entero saldría a 0,00 €, imprimible y enviable")


def test_LAS_DOS_PANTALLAS_LEEN_EL_MISMO_SITIO():
    """Cocina Desmontada y el Presupuestador venden el mismo casco. Si cada una
    resuelve el valor por su cuenta, se separan — y ya se separaron."""
    cascos = sin_comentarios(_lee(CASCOS))
    assert "valorPuntoCascos(state)" in cascos, (
        "Cocina Desmontada vuelve a resolver el valor del punto por su cuenta")
    assert "?? state?.settings?.cascosPointValue) || 1" not in cascos, (
        "ha vuelto el `|| 1` de Cocina Desmontada: con la casilla vacía vendería "
        "los cascos a mitad de precio")

    rent = sin_comentarios(_lee(RENT))
    assert "valorPuntoCascos()" in rent, (
        "el Presupuestador no usa la fuente común del valor del punto")
    assert "1.30" not in rent, (
        "ha vuelto el 1,30 del Presupuestador: es un tercer precio para el "
        "mismo casco")


def test_NADIE_MAS_SE_INVENTA_UN_DEFECTO():
    """Los otros dos sitios donde vivía el dato: la casilla y la carga inicial."""
    for ruta, nombre in ((APP, "App.js"), (AJUSTES, "PricingTab.jsx")):
        cuerpo = sin_comentarios(_lee(ruta))
        i = cuerpo.find("pointValueDesmontada")
        assert i != -1, f"{nombre} ya no toca el valor del punto de cascos"
        trozo = cuerpo[i:i + 400]
        assert "VALOR_PUNTO_CASCOS" in trozo, (
            f"{nombre} usa su propio valor por defecto para el punto de cascos "
            "en vez del de la casa: con la casilla vacía daría otro precio")
        assert "|| 1.0" not in trozo and "?? 1.0" not in trozo, (
            f"{nombre} ha vuelto a caer en 1,0")


def test_EL_DESCUENTO_DE_ACB_NO_SE_CABLEA_AQUI():
    """El master: «eso lo meto yo a mano, porque puede variar». El −28 % de hoy
    NO es una constante: si se cableara, el día que renegocie la tarifa el coste
    seguiría saliendo con el descuento viejo y nadie lo relacionaría."""
    src = sin_comentarios(_lee(MODULO))
    for prohibido in ("0.72", "28", "0.50"):
        assert prohibido not in src.replace("VALOR_PUNTO_CASCOS = 2", ""), (
            f"el módulo del valor del punto lleva dentro un «{prohibido}»: el "
            "descuento del proveedor lo teclea el master, no se cablea")


def test_EL_PVP_Y_EL_COSTE_SON_DOS_CUENTAS_DISTINTAS():
    """El valor del punto hace el PVP; el descuento hace el coste. Si el
    descuento tocara el PVP, se le estaría regalando al cliente el margen de la
    negociación con ACB (CLAUDE.md, regla 5)."""
    rent = sin_comentarios(_lee(RENT))
    i = rent.index("const dtoCascos = Math.min")
    tramo = rent[i:i + 400]
    assert "pvpDesmontada" not in tramo, (
        "el descuento de compra está tocando el PVP de venta")


def test_TAMBIEN_SE_LEE_LO_QUE_HAY_GUARDADO_EN_EL_NAVEGADOR():
    """La otra puerta. El Presupuestador no recibe el `state` de la aplicación:
    lee de localStorage, que es donde queda el ajuste después de cargarlo. Si esa
    rama se pierde, el Presupuestador cae en el valor de la casa mientras Cocina
    Desmontada usa el de la casilla — y vuelven los dos precios."""
    v = _resuelve([None], guardado={"pointValueDesmontada": "2.5"})
    assert v == [2.5], (
        f"no se está leyendo el valor guardado en el navegador: sale {v}. El "
        "Presupuestador se quedaría con el valor de la casa e ignoraría la "
        "casilla del master")

    v = _resuelve([{"pointValueDesmontada": 3}], guardado={"pointValueDesmontada": "2"})
    assert v == [3], (
        f"lo guardado en el navegador está ganando al ajuste recién cargado: {v}")

    v = _resuelve([None], guardado={"pointValueDesmontada": "0"})
    assert v == [2], f"un 0 guardado deja el PVP en cero: {v}"


def test_SIN_NAVEGADOR_NO_REVIENTA():
    """El cálculo también se ejecuta fuera del navegador (los propios candados
    lo hacen). Sin `localStorage` tiene que devolver el valor de la casa, no
    lanzar una excepción que tumbe la pantalla."""
    assert _resuelve([None], guardado=None) == [2]
