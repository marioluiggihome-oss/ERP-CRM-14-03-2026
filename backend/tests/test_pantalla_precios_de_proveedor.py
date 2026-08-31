# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
LOS PRECIOS DE PROVEEDOR SE TECLEAN EN EL PRESUPUESTADOR.

El master, 31/08: «pon botones para poder editar y cambiar datos para pedir a
los distintos proveedores de cascos, herraje, puertas, etc.», después de «no
está en esta sección y lo quiero tener a mano todo».

QUÉ PASABA. Las cifras existían y movían TODOS los costes de la pantalla —el
€/m² de puerta, la bisagra, las patas, el colgador, el cajón, la gaveta, el
soporte de balda y la mano de obra—, pero en Cocina Montada 3 se leían con un
`useMemo` de dependencias vacías: una foto de `localStorage` tomada al entrar y
sin forma de cambiarla. Para subir el precio de una bisagra había que irse a
Rentabilidad MV, cambiarlo allí y volver. O sea que el número que decide si un
presupuesto gana dinero se editaba en otra pantalla — y por eso no se editaba:
se presupuestaba con la tarifa del año pasado, sin que nada diera un error.

LO QUE ESTE CANDADO PROTEGE
---------------------------
1. TODA TARIFA QUE ENTRE EN EL COSTE SE PUEDE TECLEAR. Las claves de
   `MV_COSTES_DEFAULT` (menos los descuentos, que van aparte) tienen que estar
   en `TARIFAS_DE_PROVEEDOR`. El día que se añada un herraje nuevo al cálculo y
   no se pueda cambiar aquí, esto se pone rojo.

2. UNA SOLA CLAVE DE GUARDADO. El Presupuestador escribe en `mv_costes`, la
   MISMA que Rentabilidad MV. Con dos claves, la bisagra valdría 3,07 € en una
   pantalla y 4,10 € en la otra, en el mismo pedido, y ninguna de las dos
   parecería un error.

3. ENTRAR A MIRAR NO PISA UNA TARIFA. El guardado va en el setter, NUNCA en un
   `useEffect` de montaje: si se escribiera al montar, abrir el Presupuestador
   machacaría con su copia lo que el master acabara de teclear en Rentabilidad.

4. UN CAMPO VACÍO NO ES UN CERO. `Number('')` es 0, y un 0 en la tarifa es «esta
   bisagra no cuesta nada» — una afirmación distinta de «todavía no lo he
   tecleado» (CLAUDE.md, regla 7).

5. LOS DESCUENTOS DEL PANEL SON LOS MISMOS, NO UNA COPIA. Los de cascos y
   puertas que se ven aquí van a los setters de siempre. Una segunda pareja de
   campos que escribiera en otro estado dejaría al master tecleando un descuento
   que no mueve ningún coste.
"""
import os
import re

import pytest

from jsx_limpio import sin_comentarios

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(RAIZ, "frontend", "src")
CM3 = os.path.join(SRC, "components", "CocinaMontada3.jsx")
RENT = os.path.join(SRC, "components", "RentabilidadMV.jsx")


def _lee(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        return f.read()


def _cm3():
    return sin_comentarios(_lee(CM3))


def _bloque(cuerpo, arranque, cierre):
    """Devuelve el bloque que empieza en `arranque` y acaba en `cierre`."""
    i = cuerpo.index(arranque)
    return cuerpo[i:cuerpo.index(cierre, i) + len(cierre)]


def _claves_de_tarifa():
    """Las claves de `MV_COSTES_DEFAULT` que son PRECIO, no descuento."""
    cuerpo = sin_comentarios(_lee(RENT))
    bloque = _bloque(cuerpo, "export const MV_COSTES_DEFAULT = {", "};")
    claves = re.findall(r"^\s*([A-Za-z0-9_]+)\s*:", bloque, re.M)
    assert claves, "no se leen las claves de MV_COSTES_DEFAULT"
    return [k for k in claves if not k.startswith("dto")]


def test_TODA_TARIFA_DEL_COSTE_SE_PUEDE_TECLEAR():
    """Si entra en el coste, se cambia aquí. Si no, se presupuesta con la del año pasado."""
    cuerpo = _cm3()
    tabla = _bloque(cuerpo, "export const TARIFAS_DE_PROVEEDOR = [", "\n];")
    for k in _claves_de_tarifa():
        assert f"k: '{k}'" in tabla, (
            f"«{k}» entra en el coste del mueble y no se puede cambiar desde el "
            f"Presupuestador: falta en TARIFAS_DE_PROVEEDOR")


def test_CADA_TARIFA_TIENE_SU_CASILLA_EN_PANTALLA():
    """La tabla no vale de nada si no se pinta un input por campo."""
    cuerpo = _cm3()
    panel = _bloque(cuerpo, 'data-testid="cm3-panel-proveedores"', "\n      )}")
    assert "TARIFAS_DE_PROVEEDOR.map" in panel, (
        "el panel no recorre la tabla de tarifas: los campos estarían escritos a mano")
    assert "onChange={e => setTarifaProveedor(c.k, e.target.value)}" in panel, (
        "las casillas del panel no escriben en la tarifa")
    assert 'data-testid={`prov-tarifa-${c.k}`}' in panel, (
        "las casillas no se pueden localizar una a una")


def test_SE_GUARDA_EN_LA_MISMA_CLAVE_QUE_RENTABILIDAD():
    """Dos claves = la misma bisagra a dos precios, y ninguna parece un error."""
    cm3 = _cm3()
    rent = sin_comentarios(_lee(RENT))
    assert "localStorage.setItem('mv_costes'" in rent, (
        "Rentabilidad MV ha dejado de guardar en 'mv_costes': revisa las dos pantallas")
    setter = _bloque(cm3, "const setTarifaProveedor", "\n  });")
    assert "localStorage.setItem('mv_costes'" in setter, (
        "el Presupuestador no guarda la tarifa en la clave de Rentabilidad ('mv_costes')")
    otras = set(re.findall(r"localStorage\.setItem\('([^']+)'\s*,\s*JSON\.stringify\(\s*(?:siguiente|MV_COSTES_DEFAULT)",
                           cm3))
    assert otras == {"mv_costes"}, (
        f"el Presupuestador guarda la tarifa en otra clave además de 'mv_costes': {otras}")


def _llamada(cuerpo, i):
    """El texto de la llamada que abre su paréntesis en `i`, por BALANCE.

    Nada de ventanas de N caracteres: una ventana fija se pasa de largo y
    acaba leyendo el código de al lado — que es justo cómo esta prueba pasó a
    verde por el motivo equivocado la primera vez.
    """
    j = cuerpo.index("(", i)
    hondo = 0
    for k in range(j, len(cuerpo)):
        if cuerpo[k] == "(":
            hondo += 1
        elif cuerpo[k] == ")":
            hondo -= 1
            if hondo == 0:
                return cuerpo[i:k + 1]
    raise AssertionError("paréntesis sin cerrar en el JSX")


def test_ENTRAR_A_MIRAR_NO_PISA_LA_TARIFA():
    """Si se guardara al montar, abrir el Presupuestador machacaría lo tecleado en Rentabilidad."""
    cuerpo = _cm3()
    for m in re.finditer(r"\buseEffect\b", cuerpo):
        efecto = _llamada(cuerpo, m.start())
        assert "setItem('mv_costes'" not in efecto, (
            "un useEffect escribe 'mv_costes': entrar en la pantalla pisaría la "
            "tarifa que el master acabe de teclear en Rentabilidad MV")


def test_UN_CAMPO_VACIO_NO_VALE_CERO():
    """Vacío es «no lo he tecleado», no «no cuesta nada» (regla 7)."""
    cuerpo = _cm3()
    setter = _bloque(cuerpo, "const setTarifaProveedor", "\n  });")
    assert "valor === '' ? '' : Number(valor)" in setter, (
        f"un campo vacío se convierte en 0 y la tarifa se queda a cero: {setter.strip()[:200]}")
    assert "|| 0" not in setter, (
        "el setter cae a 0: un precio sin teclear pasaría a decir que no cuesta nada")


def test_LOS_DESCUENTOS_DEL_PANEL_SON_LOS_MISMOS():
    """Una segunda pareja de campos que escriba en otro estado no mueve ningún coste."""
    cuerpo = _cm3()
    panel = _bloque(cuerpo, 'data-testid="cm3-panel-proveedores"', "\n      )}")
    for setter in ("setDtoCascos1(", "setDtoCascos2(", "setDtoPuertas1(", "setDtoPuertas2("):
        assert setter in panel, (
            f"el panel de proveedores no usa {setter[:-1]}: estaría tecleando un "
            "descuento que no mueve ningún coste")


def test_EL_PANEL_SE_PUEDE_ABRIR():
    """Una pantalla sin puerta no existe."""
    cuerpo = _cm3()
    assert 'data-testid="cm3-boton-proveedores"' in cuerpo, "no hay botón para abrir el panel"
    boton = _bloque(cuerpo, 'data-testid="cm3-boton-proveedores"', "</button>")
    i = cuerpo.index('data-testid="cm3-boton-proveedores"')
    abre = cuerpo[max(0, i - 400):i]
    assert "setShowProveedores(v => !v)" in abre, (
        f"el botón no abre el panel: {abre[-160:]}")
    assert "Proveedores" in boton, "el botón no dice a dónde lleva"
    assert "{showProveedores && (" in cuerpo, "el panel no cuelga de su interruptor"


def test_LOS_DESCUENTOS_NO_ESTAN_EN_LA_TABLA_DE_TARIFAS():
    """Un descuento no es un precio: si se colara, se teclearía dos veces y en dos sitios."""
    cuerpo = _cm3()
    tabla = _bloque(cuerpo, "export const TARIFAS_DE_PROVEEDOR = [", "\n];")
    assert "dto" not in tabla, (
        "un descuento se ha colado en la tabla de precios de proveedor: van en la "
        "cabecera del escandallo, donde se ve su efecto")


def test_LA_TARIFA_SIGUE_ARRANCANDO_DE_LO_GUARDADO():
    """Si arrancara de los valores de la casa, entrar borraría lo negociado."""
    cuerpo = _cm3()
    estado = _bloque(cuerpo, "const [p, setP] = useState(", "\n  });")
    assert "localStorage.getItem('mv_costes')" in estado, (
        "el Presupuestador ya no lee la tarifa guardada: entraría siempre con los "
        "valores de la casa y el descuento negociado se perdería al abrir")
    assert "...MV_COSTES_DEFAULT" in estado, (
        "sin los valores de la casa por debajo, una tarifa guardada a medias "
        "dejaría campos sin precio")


def test_VOLVER_A_LOS_VALORES_DE_LA_CASA_NO_BORRA_EL_DESCUENTO():
    """El botón promete precios. Si además devolviera el −28 % de ACB a cero,
    borraría el descuento NEGOCIADO — y no aquí, sino en Rentabilidad MV, que
    lee los descuentos de esta misma clave. El master no lo vería hasta mirar un
    margen que ya no cuadra."""
    cuerpo = _cm3()
    reset = _bloque(cuerpo, "const restablecerTarifas", "\n  });")
    assert "startsWith('dto')" in reset, (
        f"«Valores de la casa» restablece también los descuentos: {reset.strip()[:220]}")
    assert "prev[k]" in reset, (
        "el restablecer no conserva el descuento que ya había")
