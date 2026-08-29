# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
EL PRESUPUESTADOR, CERRADO TAMBIÉN EN EL SERVIDOR. LA OTRA MITAD.

La regla 22 de CLAUDE.md decía, en su último punto, que el corte por permiso
estaba SOLO en pantalla «a propósito y de momento»: la regla 8 pide cerrarlo
también detrás, pero ese mismo día (28/08) apretar un candado a ciegas dejó al
master sin sus propios precios y toda la relación salió a 0,00 €. Se dejó dicho
que se haría en el orden correcto: mirar primero a quién afecta, cerrar después.

Esto es el «después». Y el orden se nota en lo que NO se ha cerrado.

QUÉ SE CIERRA: las ESCRITURAS. Crear, modificar medidas y borrar un pedido piden
el permiso de SU sección. Antes no pedían ninguno: esconder una pestaña no
cierra nada, y cualquiera con sesión podía trabajar en Cocina Desmontada
llamando a la API a mano.

QUÉ NO SE CIERRA, Y POR QUÉ. Las LECTURAS de `/cascos/orders`. De esa lista
comen también Rentabilidad, el Expediente y Almacén, cada una con su puerta y su
permiso. Cerrarla aquí les quitaría datos a pantallas que no son el
Presupuestador — que es literalmente repetir el error del 28/08. Y esa lista ya
va recortada por dueño: quien no tiene un rol elevado solo ve sus pedidos.

EL PERMISO SALE DEL ORIGEN DEL PEDIDO, NO DEL ENDPOINT. Es lo más fácil de
hacer mal aquí. Los dos presupuestadores guardan en `cascos_orders` —Cocina
Montada 3 crea pedidos ahí desde el 28/08—, así que si `POST /cascos/orders`
preguntara «¿puedes usar Cocina Desmontada?», un usuario que solo tiene Montada
dejaría de poder pasar a pedido. Sin error entendible y sin que nadie
relacionara las dos cosas.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("JWT_SECRET", "secreto-de-pruebas-largo-y-aleatorio-0123456789")

from services import origen_pedidos as OP      # noqa: E402
from services import presupuestador as P       # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JS = os.path.join(RAIZ, "frontend", "src", "presupuestador.js")
RUTA_CASCOS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "routes", "cascos.py")

# Los mismos de la prueba de pantalla, más los bordes que separan a las dos
# mitades cuando alguien reescribe una condición.
USUARIOS = [
    {"isMaster": True},
    {"isPrimaryAdmin": True},
    {"isAdmin": True},
    {"canUsePresupuestador3": True, "canUseCascos": True},
    {"canUseCascos": False},
    {"canUsePresupuestador3": False, "canUseCascos": True},
    {"isTienda": True, "canUseCascos": True},
    {"canUsePresupuestador3": False},
    {},
    # `canUseCascos` tiene que ser EXACTAMENTE `true`, y `canUsePresupuestador3`
    # EXACTAMENTE `false` para cerrar. Un `1` o un `"si"` no valen.
    {"canUseCascos": 1},
    {"canUseCascos": "true"},
    {"canUsePresupuestador3": 0},
    {"canUsePresupuestador3": None},
    {"isTienda": True, "isAdmin": True},
]


def _lee(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        return f.read()


def test_LA_PANTALLA_Y_EL_SERVIDOR_dicen_lo_mismo_usuario_a_usuario():
    """Dos copias de una regla de permisos que no se comparan, se separan.

    Y separarse aquí duele por los dos lados: o la pantalla enseña una pestaña
    que da 403 al guardar —con una relación entera ya tecleada—, o el servidor
    deja hacer lo que la pantalla ya no ofrece.

    Se EJECUTA el JS en node: comparar el texto de los dos ficheros no probaría
    nada, porque lo que importa es lo que devuelven.
    """
    node = shutil.which("node")
    if not node:
        pytest.skip("no hay node en esta máquina")

    guion = _lee(JS).replace("export const", "const")
    guion += ("\nconst us = " + json.dumps(USUARIOS) + ";\n"
              "console.log(JSON.stringify(us.map((u) => "
              "[puedeMontada(u), puedeDesmontada(u), puedeEntrar(u)])));\n")
    with tempfile.NamedTemporaryFile("w", suffix=".mjs", delete=False, encoding="utf-8") as f:
        f.write(guion)
        ruta = f.name
    try:
        salida = subprocess.run([node, ruta], capture_output=True, text=True, timeout=60)
    finally:
        os.unlink(ruta)
    assert salida.returncode == 0, f"el módulo de pantalla no corre: {salida.stderr.strip()}"

    for usuario, (m, d, e) in zip(USUARIOS, json.loads(salida.stdout)):
        assert m == P.puede_montada(usuario), (
            f"Cocina Montada: la pantalla dice {m} y el servidor "
            f"{P.puede_montada(usuario)} para {usuario!r}")
        assert d == P.puede_desmontada(usuario), (
            f"Cocina Desmontada: la pantalla dice {d} y el servidor "
            f"{P.puede_desmontada(usuario)} para {usuario!r}")
        assert e == P.puede_entrar(usuario), (
            f"entrar en la sección: la pantalla dice {e} y el servidor "
            f"{P.puede_entrar(usuario)} para {usuario!r}")


def test_los_PERMISOS_siguen_siendo_los_de_siempre():
    """Cerrar el servidor no puede cambiar de paso quién entra."""
    assert P.puede_montada({"canUsePresupuestador3": True})
    assert P.puede_montada({}), (
        "Cocina Montada 3 era «no estar desactivado»: sin el campo, se entra")
    assert not P.puede_montada({"canUsePresupuestador3": False})

    assert P.puede_desmontada({"canUseCascos": True})
    assert not P.puede_desmontada({}), (
        "Cocina Desmontada pide permiso EXPLÍCITO: sin el campo, no se entra")
    assert not P.puede_desmontada({"canUseCascos": True, "isTienda": True}), (
        "una tienda no ve Cocina Desmontada ni con el permiso puesto")
    assert not P.puede_montada(None) and not P.puede_desmontada(None)

    for flag in ("isMaster", "isPrimaryAdmin"):
        assert P.puede_montada({flag: True}) and P.puede_desmontada({flag: True}), (
            f"el master ({flag}) se ha quedado fuera de su propio presupuestador")
    # `isAdmin` YA NO ES MASTER (29/08). Sigue entrando en Cocina Montada —el
    # permiso de ahí es «no estar desactivado»— pero Cocina Desmontada le pide
    # su permiso explícito como a cualquiera.
    assert P.puede_montada({"isAdmin": True})
    assert not P.puede_desmontada({"isAdmin": True}), (
        "un administrador sin `canUseCascos` sigue entrando en Cocina "
        "Desmontada: `isAdmin` ha vuelto a colarse como master")


def test_QUIEN_SOLO_TIENE_MONTADA_PUEDE_PASAR_A_PEDIDO():
    """El trampa-mortal de este cambio, y el motivo de que el permiso salga del
    ORIGEN y no del endpoint.

    Cocina Montada 3 crea sus pedidos en `cascos_orders`, o sea por la misma
    puerta que Cocina Desmontada. Si esa puerta pidiera «¿puedes usar Cocina
    Desmontada?», el comercial que solo tiene Montada dejaría de poder pasar a
    pedido — y con él se caerían su comisión y la del montador, porque un
    presupuesto no cuenta para la cooperativa.
    """
    solo_montada = {"canUseCascos": False}
    assert P.puede_con_el_pedido(solo_montada, OP.MONTADA_3), (
        "quien solo tiene Cocina Montada no puede crear su propio pedido")
    assert not P.puede_con_el_pedido(solo_montada, OP.DESMONTADA), (
        "quien solo tiene Cocina Montada está creando pedidos de Desmontada")

    solo_desmontada = {"canUsePresupuestador3": False, "canUseCascos": True}
    assert P.puede_con_el_pedido(solo_desmontada, OP.DESMONTADA)
    assert not P.puede_con_el_pedido(solo_desmontada, OP.MONTADA_3)


def test_UN_ORIGEN_RARO_PIDE_EL_PERMISO_MAS_ESTRICTO():
    """En la duda se pide el más estricto, no el más flojo.

    Un pedido sin origen, o con uno inventado en el cuerpo de la petición, cae en
    Cocina Desmontada — que es de quien es esa colección de siempre y además es
    el permiso EXPLÍCITO de los dos. Al revés, escribir `origen: "loquesea"`
    sería la puerta de atrás para saltarse el candado que se acaba de poner.
    """
    for raro in ("", None, "fabrica", "cocina_montada_4", 123, {"a": 1}):
        assert P.seccion_de_origen(raro) == P.DESMONTADA, f"con origen {raro!r}"
        assert not P.puede_con_el_pedido({"canUsePresupuestador3": True}, raro), (
            f"con `origen={raro!r}` se está entrando sin el permiso de Desmontada")
    assert P.seccion_de_origen(OP.MONTADA_3) == P.MONTADA
    assert P.seccion_de_origen("  COCINA_MONTADA_3  ") == P.MONTADA


def test_LAS_TRES_ESCRITURAS_estan_cerradas_en_la_ruta():
    """Crear, cambiar medidas y borrar. Se mira el fichero de rutas porque un
    candado que solo existe en el servicio no cierra ningún endpoint."""
    cuerpo = _lee(RUTA_CASCOS)
    assert "_exigir_permiso_de_la_seccion(current_user, doc[\"origen\"])" in cuerpo, (
        "`POST /cascos/orders` no pide el permiso de la sección: cualquiera con "
        "sesión puede crear pedidos de Cocina Desmontada")
    assert cuerpo.count("para_escribir=True") >= 2, (
        "guardar medidas o tomarlas/confirmarlas no pide el permiso de la "
        "sección: ser el dueño de un pedido no basta si te han quitado ese "
        "presupuestador")
    assert "_exigir_permiso_de_la_seccion(current_user, o.get(\"origen\"))" in cuerpo, (
        "`DELETE /cascos/orders/{id}` no pide el permiso de la sección, y borrar "
        "es la escritura más definitiva que hay")
    assert '"origen": 1' in cuerpo, (
        "el `find_one` del borrado no se trae el `origen`, así que el permiso se "
        "resolvería siempre como Desmontada aunque el pedido fuera de Montada")


def test_LEER_no_se_ha_cerrado_de_paso():
    """La mitad que NO se toca, y que hay que dejar amarrada para que nadie la
    «termine» con buena intención.

    De `/cascos/orders` leen Rentabilidad, el Expediente y Almacén. Si esta
    lectura pidiera el permiso del Presupuestador, un controller o un gerente sin
    `canUseCascos` se quedaría sin datos en pantallas que no tienen nada que ver
    — el error del 28/08, calcado.
    """
    cuerpo = _lee(RUTA_CASCOS)
    i = cuerpo.index('@router.get("/cascos/orders")')
    # Hasta el final de ESA función, no hasta el siguiente `@router`: entre una
    # ruta y la siguiente hay funciones auxiliares, y meterlas en el trozo hace
    # que la prueba acuse a un código que no es (ya pasó con el candado del
    # origen, que leía 400 caracteres a bulto).
    m = re.search(r"\n(?:@router|def |async def )", cuerpo[i + 10:])
    listado = cuerpo[i:i + 10 + (m.start() if m else len(cuerpo))]
    assert "_exigir_permiso_de_la_seccion" not in listado, (
        "se ha cerrado la LECTURA de los pedidos. De esta lista comen "
        "Rentabilidad, el Expediente y Almacén, que tienen su propia puerta: "
        "cerrarla aquí les quita datos a pantallas que no son el Presupuestador")

    # Y `_pedido_o_404` sigue pudiendo leer sin exigir sección.
    k = cuerpo.index("async def _pedido_o_404")
    firma = cuerpo[k:k + 400]
    assert "para_escribir: bool = False" in firma, (
        "leer un pedido ha pasado a pedir el permiso de la sección por defecto")
