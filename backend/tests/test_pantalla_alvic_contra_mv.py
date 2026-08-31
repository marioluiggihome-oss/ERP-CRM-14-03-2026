# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
ALVIC CONTRA MV: LOS DOS PRECIOS, UNO AL LADO DEL OTRO.

El master, 31/08: «cuando importo de Alvic q informe del precio de este
fabricante y ponga también el precio de MV al lado y así vemos la diferencia».

QUÉ PASABA. La importación metía el precio de Alvic en `pvp` y ahí se acababa:
quedaba indistinguible de un precio de la tarifa MV. O sea que lo único para lo
que se importa una proforma de la competencia —comparar— había que hacerlo a
mano con los dos PDF delante.

Y EL PRECIO SE PERDÍA SIN AVISAR. `pvp` es la casilla de la tarifa MV: en cuanto
se tocaba el alto, el ancho o el código de la línea, `setAlto`,
`setMedidaMueble` o `setCod` lo recalculaban del catálogo y el precio del
fabricante desaparecía. Sin un error, sin rastro, y en una pantalla en la que
ajustar medidas después de importar es lo normal.

LO QUE SE PROTEGE
-----------------
1. EL PRECIO DE ALVIC VIVE EN SU PROPIO CAMPO (`pvpAlvic`) y llega marcado
   (`origenPrecio`), para poder decir de dónde sale cada número.

2. NO SE PISA. La línea entra con `pvpManual`, que es el freno que ya existía
   para un precio que no sale de la tarifa MV.

3. NO SE INVENTA EL PRECIO DE MV. Un código que la tarifa MV no tiene se cuenta
   aparte y NO entra en el total. Si contara como 0 €, la diferencia saldría a
   favor de MV por muebles que MV no sabe hacer (CLAUDE.md, regla 7).

4. EL PRECIO DE MV SE CALCULA AL PINTAR, no al importar: la tarifa llega del
   servidor DESPUÉS de la importación, así que hecho allí saldría vacío siempre.

5. LA MARCA DICE LO QUE EL NÚMERO ES. «A mano» en una línea traída de Alvic
   sería mentira; y si se borra el precio y MV no tiene ese código, la línea se
   queda con el de Alvic pero pierde `pvpManual` — sin esto se leería como un
   precio de tarifa MV que no lo es.
"""
import os
import re

import pytest

from jsx_limpio import sin_comentarios

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CM3 = os.path.join(RAIZ, "frontend", "src", "components", "CocinaMontada3.jsx")


def _cm3():
    with open(CM3, "r", encoding="utf-8") as f:
        return sin_comentarios(f.read())


def _bloque(cuerpo, arranque, cierre):
    i = cuerpo.index(arranque)
    return cuerpo[i:cuerpo.index(cierre, i) + len(cierre)]


def _panel():
    """El bloque ENTERO de la comparativa: las cuentas Y el JSX.

    Empieza en `const lineasAlvic` y no en el `data-testid`, porque los totales
    se calculan ANTES de pintar nada: cortando por la etiqueta, las
    comprobaciones de las sumas miraban un trozo que no las contiene y pasaban
    por no encontrar lo que buscaban.
    """
    return _bloque(_cm3(), "const lineasAlvic = filas.filter", "\n      })()}")


def test_LA_IMPORTACION_GUARDA_EL_PRECIO_DE_ALVIC_APARTE():
    """En `pvp` a secas es indistinguible de un precio de la tarifa MV."""
    cuerpo = _cm3()
    importar = _bloque(cuerpo, "const importarAlvic = async (file)", "\n  };")
    assert "pvpAlvic: pvpUnit > 0 ? pvpUnit : null" in importar, (
        "el precio del fabricante no se guarda aparte: no hay con qué comparar")
    assert "origenPrecio: pvpUnit > 0 ? 'ALVIC' : null" in importar, (
        "la línea no dice de dónde viene su precio")


def test_EL_PRECIO_DE_ALVIC_NO_SE_PISA_AL_TOCAR_LA_LINEA():
    """`setAlto`, `setMedidaMueble` y `setCod` recalculan `pvp` del catálogo.
    Sin `pvpManual`, ajustar una medida después de importar borraba el precio
    del fabricante en silencio."""
    cuerpo = _cm3()
    importar = _bloque(cuerpo, "const importarAlvic = async (file)", "\n  };")
    assert "pvpManual: pvpUnit > 0" in importar, (
        "la línea importada no lleva el freno: tocar el alto, el ancho o el "
        "código le borraría el precio de Alvic sin dar un error")
    # Y el freno tiene que seguir frenando en los tres sitios.
    # Los TRES sitios que recalculan `pvp` del catálogo. `setMedidaMueble` no
    # está: solo escribe el ancho y el alto, no toca el precio.
    for fn in ("const setCod", "const setAlto", "const setAnchoTarifa"):
        bloque = _bloque(cuerpo, fn, "\n  }));")
        assert "if (m.pvpManual)" in bloque, (
            f"{fn[6:]} ya no respeta un precio que no sale de la tarifa MV: "
            "tocar la línea borraría el de Alvic en silencio")
        assert "puntosLocal(" in bloque, (
            f"{fn[6:]} ya no recalcula de la tarifa: la comprobación de arriba "
            "habría dejado de significar nada")


def test_EL_PRECIO_DE_MV_SE_CALCULA_AL_PINTAR():
    """La tarifa llega del servidor DESPUÉS de importar: hecho al importar,
    saldría vacío siempre."""
    cuerpo = _cm3()
    filas = _bloque(cuerpo, "const filas = muebles.map(m =>", "\n  });")
    assert "const pvpMv = m.pvpAlvic != null ? puntosLocal(" in filas, (
        "el precio de MV no se calcula en la fila")
    linea = _bloque(filas, "const pvpMv =", ";")
    assert "pvp: null" in linea, (
        f"`puntosLocal` devuelve el pvp de la línea cuando el código no está en "
        f"el catálogo: sin `pvp: null` se compararía Alvic consigo mismo: {linea.strip()}")
    importar = _bloque(cuerpo, "const importarAlvic = async (file)", "\n  };")
    assert "pvpMv" not in importar, (
        "el precio de MV se calcula al importar, cuando la tarifa todavía no ha llegado")


def test_UN_CODIGO_QUE_MV_NO_TIENE_NO_VALE_CERO():
    """Contarlo como 0 € haría que la diferencia saliera a favor de MV por
    muebles que MV no sabe hacer (regla 7)."""
    panel = _panel()
    comparables = _bloque(panel, "const comparables =", ";")
    assert "m.pvpMv != null" in comparables, (
        f"las líneas sin tarifa MV entran en la comparación: {comparables.strip()}")
    for total in ("const totAlvic =", "const totMv ="):
        suma = _bloque(panel, total, ", 0);")
        assert "comparables.reduce" in suma, (
            f"el total suma todas las líneas, no solo las comparables: {suma.strip()}")
        assert "(Number(m.qty) || 1)" in suma or "uds(m)" in suma, (
            f"el total no multiplica por las unidades: {suma.strip()}")
    assert 'data-testid="cm3-alvic-sin-tarifa-mv"' in panel, (
        "no se dice cuántas líneas se han quedado fuera de la comparación")


def test_LA_COMPARATIVA_SOLO_SALE_SI_HAY_LINEAS_DE_ALVIC():
    """Una tabla vacía permanente es ruido en una pantalla que ya está llena."""
    cuerpo = _cm3()
    i = cuerpo.index('data-testid="cm3-comparativa-alvic"')
    antes = cuerpo[max(0, i - 700):i]
    assert "const lineasAlvic = filas.filter(m => m.pvpAlvic != null);" in antes, (
        "la comparativa no se saca de las líneas importadas de Alvic")
    assert "if (!lineasAlvic.length) return null;" in antes, (
        "la comparativa se pinta aunque no se haya importado nada de Alvic")


def test_LA_DIFERENCIA_SE_DICE_EN_EUROS_Y_EN_PORCENTAJE():
    """Es el número por el que se decide a qué fabricante se le pide."""
    panel = _panel()
    dif = _bloque(panel, "const dif =", ";")
    assert "totMv - totAlvic" in dif, (
        f"la diferencia no compara los dos fabricantes: {dif.strip()}")
    assert 'data-testid="cm3-alvic-diferencia"' in panel, "la diferencia no se pinta"
    assert "MÁS CARAS" in panel and "MÁS BARATAS" in panel, (
        "no se dice en qué sentido va la diferencia: un signo se lee mal con prisa")
    pct = _bloque(panel, "const pct =", ";")
    assert "totAlvic > 0" in pct, (
        f"el porcentaje divide sin comprobar el divisor: {pct.strip()}")


def test_LA_MARCA_DICE_LO_QUE_EL_NUMERO_ES():
    """«A mano» en una línea de Alvic sería mentira, y al revés también."""
    cuerpo = _cm3()
    marca = _bloque(cuerpo, "{(m.origenPrecio === 'ALVIC' && Number(m.pvp) === Number(m.pvpAlvic))", ": null}")
    assert 'data-testid="cm3-marca-precio-alvic"' in marca, (
        "una línea con el precio de Alvic no se distingue de una tecleada a mano")
    assert "'a mano'" in marca or "a mano<" in marca, (
        "se ha perdido la marca de precio escrito a mano")
    # La condición mira el NÚMERO, no solo la etiqueta: si se borra el precio y
    # MV no tiene el código, la línea sigue llevando el de Alvic sin `pvpManual`.
    assert "Number(m.pvp) === Number(m.pvpAlvic)" in marca, (
        "la marca se fía de la etiqueta y no de lo que vale la línea")


def test_LA_TABLA_ENSENA_LOS_DOS_PRECIOS_EN_LA_LINEA():
    """La decisión de dejar Alvic o pasar a MV se toma en la tabla de arriba,
    no bajando al panel."""
    cuerpo = _cm3()
    assert 'data-testid="cm3-pvp-mv-linea"' in cuerpo, (
        "la tabla no enseña el precio de MV al lado del de Alvic")
    celda = _bloque(cuerpo, '{m.pvpAlvic != null && (', ")}")
    assert "m.pvpMv == null" in celda, (
        "una línea sin tarifa MV no se distingue: hay que rotularla «?», no 0 €")
    assert "MV: ?" in celda, "falta el «?» de la línea sin equivalencia en MV"


def test_EL_PANEL_DICE_QUE_PRECIO_SE_ESTA_USANDO():
    """Ver dos precios sin saber cuál está en el presupuesto es peor que no
    verlos: se firma un total creyendo que es el otro."""
    panel = _panel()
    assert "El PVP que se está usando en el presupuesto es el de Alvic" in panel, (
        "el panel no dice cuál de los dos precios está en el total del presupuesto")
