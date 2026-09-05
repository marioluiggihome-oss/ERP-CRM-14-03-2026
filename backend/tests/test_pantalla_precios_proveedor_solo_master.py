# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
LOS PRECIOS DE PROVEEDOR SON DEL MASTER, Y DE QUIEN ÉL MARQUE.

El master, 04/09/2026: «lo de los proveedores sólo para mí, efectivamente hazlo
ya, pero también pon un permiso para activárselo a los usuarios que yo
considere».

QUÉ HAY DETRÁS DE ESA PUERTA. El panel «Proveedores» del Presupuestador es
donde se teclea el descuento de ACB, el €/m² de las puertas MV, el precio de
cada herraje y la mano de obra. O sea LO QUE LE CUESTA A LA CASA cada pieza —
lo mismo que la regla 8b protege en la tarifa MV.

CÓMO SE REPARTE. `canVerPreciosProveedor`, una casilla del panel Master, apagada
por defecto. Se da de uno en uno. El master entra siempre, sin necesidad de
marcarse nada.

LO QUE SE PROTEGE
-----------------
1. LA PUERTA SE COMPRUEBA DONDE SE PINTA, no solo donde se ofrece. Esconder el
   botón no cierra nada: el panel cuelga de un estado y bastaría con que ese
   estado se pusiera por cualquier otro camino.

2. LA REGLA DEL MASTER NO SE COPIA. Se le pregunta a `modulePermissions.js`,
   que es donde vive para todo el ERP. Dos listas del mismo dinero acaban
   apretándose una y quedándose la otra abierta (CLAUDE.md, regla 8c).

3. APAGADO POR DEFECTO. Un permiso de dinero que naciera encendido se lo
   encontraría puesto todo el mundo el día del despliegue.

4. SE PUEDE ENCONTRAR PARA QUITARLO. La casilla se llama como la sección que
   abre (regla 26), y sale marcada en la ficha del usuario.

LO QUE ESTO **NO** ES
---------------------
Un cierre de servidor. La tarifa de ACB viaja dentro de la aplicación, igual
que `cascos.js` desde siempre: esto esconde el panel donde se editan los
descuentos, no los números. Si el master quiere que las tarifas de proveedor
dejen de viajar al navegador, hay que servirlas desde el backend con la puerta
del MV — es otro trabajo y él decide si merece la pena.
"""
import os
import re

import pytest

from jsx_limpio import sin_comentarios

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(RAIZ, "frontend", "src")
CM3 = os.path.join(SRC, "components", "CocinaMontada3.jsx")
AJUSTES = os.path.join(SRC, "components", "SettingsModal.jsx")

PERMISO = "canVerPreciosProveedor"


def _lee(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        return sin_comentarios(f.read())


def _bloque(cuerpo, arranque, cierre):
    i = cuerpo.index(arranque)
    return cuerpo[i:cuerpo.index(cierre, i) + len(cierre)]


def test_LA_PUERTA_ES_EL_MASTER_MAS_QUIEN_EL_MARQUE():
    cuerpo = _lee(CM3)
    regla = _bloque(cuerpo, "const vePreciosProveedor =", ";")
    assert "esMasterSistema(currentUser)" in regla, (
        f"el master no entra a sus propios precios de proveedor: {regla.strip()}")
    assert f"currentUser?.{PERMISO} === true" in regla, (
        f"no hay forma de dárselo a nadie más: {regla.strip()}")
    # `=== true` y no a secas: un `canVerPreciosProveedor: 'no'` guardado en una
    # ficha vieja es una cadena, y en JavaScript una cadena no vacía es cierta.
    assert f"{PERMISO} === true" in regla, (
        "el permiso se lee sin comparar con `true`: cualquier valor guardado en "
        "la ficha abriría la puerta")


def test_LA_REGLA_DEL_MASTER_NO_SE_COPIA():
    """Dos listas del mismo dinero acaban apretándose una y quedándose la otra
    abierta (regla 8c)."""
    cuerpo = _lee(CM3)
    assert "from '../modulePermissions'" in cuerpo, (
        "el Presupuestador no le pregunta a la matriz de permisos quién es el master")
    regla = _bloque(cuerpo, "const vePreciosProveedor =", ";")
    for a_mano in ("isMaster", "isPrimaryAdmin", "isAdmin"):
        assert a_mano not in regla, (
            f"la regla mira `{a_mano}` a mano en vez de preguntar a "
            f"`modulePermissions.js`: el día que se cambie quién es el master, "
            f"cambiará en un sitio y no en el otro")


def test_LA_PUERTA_SE_COMPRUEBA_DONDE_SE_PINTA():
    """Esconder el botón no cierra nada: el panel cuelga de un estado."""
    cuerpo = _lee(CM3)
    assert "{vePreciosProveedor && showProveedores && (" in cuerpo, (
        "el panel de proveedores se pinta sin comprobar el permiso: bastaría con "
        "que `showProveedores` se pusiera por cualquier otro camino")
    # Y el botón tampoco se ofrece.
    i = cuerpo.index('data-testid="cm3-boton-proveedores"')
    antes = cuerpo[max(0, i - 400):i]
    assert "{vePreciosProveedor && (" in antes, (
        "el botón de Proveedores se le ofrece a todo el mundo")


def test_SE_REPARTE_DESDE_EL_PANEL_MASTER_Y_NACE_APAGADO():
    """Un permiso de dinero que naciera encendido se lo encontraría puesto todo
    el mundo el día del despliegue (regla 8c)."""
    cuerpo = _lee(AJUSTES)
    assert 'data-testid="permiso-precios-proveedor"' in cuerpo, (
        "no hay casilla en el panel Master para dar el permiso")
    apagados = re.findall(rf"{PERMISO}: (\w+),", cuerpo)
    assert apagados, "el permiso no aparece en la ficha de usuario nueva"
    assert set(apagados) == {"false"}, (
        f"el permiso nace encendido en alguna plantilla de usuario: {apagados}")
    # Y entra en «marcar todo / desmarcar todo», o el master no podría quitarlo
    # de golpe al repasar una ficha.
    capacidades = _bloque(cuerpo, "const CAPABILITY_KEYS = [", "\n];")
    assert f"'{PERMISO}'" in capacidades, (
        "el permiso no está en CAPABILITY_KEYS: «desmarcar todo» lo dejaría puesto")


def test_LA_CASILLA_SE_PUEDE_ENCONTRAR_PARA_QUITARLA():
    """Se llama como la sección que abre (regla 26) y se ve en la ficha."""
    cuerpo = _lee(AJUSTES)
    casilla = _bloque(cuerpo, 'data-testid="permiso-precios-proveedor"', "</label>")
    assert "Precios de proveedor" in casilla, (
        "la casilla no se llama como lo que abre: un permiso que no se puede "
        "encontrar es un permiso que no se puede quitar")
    assert "cuesta a la casa" in casilla, (
        "el texto de ayuda no dice qué se está dando: son los costes de compra")
    assert "PRECIOS PROVEEDOR" in cuerpo, (
        "el permiso no sale en la ficha del usuario: no se ve de un vistazo a "
        "quién se le ha dado")
