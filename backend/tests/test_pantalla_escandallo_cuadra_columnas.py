# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
UNA TABLA A LA QUE LE FALTA UNA CELDA NO DA ERROR: CORRE LOS RÓTULOS.

El master, 11/09/2026, mirando el escandallo del Presupuestador:

    «pones q el HKT de blum VALE 17 EUROS? yo creo q son las columnas
     que no están bien posicionadas»

Tenía razón, y el fallo era exactamente ese. La cabecera pintaba catorce
columnas (Casco … Margen) y cada fila pintaba trece: le faltaba la del HKT
Blum. El navegador no se queja de eso — simplemente corre una casilla a la
izquierda todo lo que viene detrás. Resultado:

    · la MANO DE OBRA (17,00 € por mueble, la comisión del montador) se leía
      bajo el rótulo «HKT Blum»,
    · el COSTE UD. bajo «M. obra»,
    · y el PVP bajo «Coste × uds».

Lo peligroso es que NINGÚN número era falso: la suma cuadraba consigo misma y
con los totales. Lo único que mentía era el rótulo de encima, que es justo por
donde se lee la tabla cuando se busca dónde se va el margen. Un herraje de
17 € por mueble en una cocina de veinte son 340 € que se creen gastados en
Blum y están en la nómina del montador.

CÓMO SE COMPRUEBA: contando celdas, no buscando la palabra «hkt». Un candado
que buscara «hkt» en el fichero pasaría en verde con la celda borrada, porque
«hkt» sigue escrito en la cabecera, en los totales y en este mismo comentario.
Aquí se cuentan los `<th>` de la cabecera y los `<td>` de la fila y del pie, y
se exige que salga la MISMA anchura contando los `colSpan`.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jsx_limpio import sin_comentarios  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CM3 = os.path.join(RAIZ, "frontend", "src", "components", "CocinaMontada3.jsx")

ANCHO_ESPERADO = 18  # #, Código, Descripción, Uds + 14 de dinero


def _cuerpo():
    with open(CM3, "r", encoding="utf-8") as f:
        crudo = f.read()
    limpio = sin_comentarios(crudo)
    # El recorte no puede haberse comido el código (lección de las reglas 24,
    # 34 y 35: tres candados se engañaron con su propio comentario, y uno se
    # comió medio componente al quitarlos a lo bruto).
    assert "Escandallo" in limpio
    assert "cm3-escandallo-total" in limpio
    return limpio


def _tabla_del_escandallo(cuerpo):
    """El `<table>` del escandallo, desde su cabecera hasta el `</table>`."""
    i = cuerpo.index("cm3-escandallo-total")
    ini = cuerpo.rindex("<table", 0, i)
    fin = cuerpo.index("</table>", i)
    return cuerpo[ini:fin]


def _ancho(trozo, etiqueta):
    """Cuántas columnas ocupa una tira de celdas, contando los `colSpan`."""
    total = 0
    for celda in re.findall(r"<%s\b[^>]*>" % etiqueta, trozo):
        m = re.search(r"colSpan=\{(\d+)\}", celda)
        total += int(m.group(1)) if m else 1
    return total


def test_LA_CABECERA_DEL_ESCANDALLO_TIENE_LAS_COLUMNAS_QUE_SE_ESPERAN():
    """Si se añade o se quita una columna hay que revisar la fila y el pie, y
    esta prueba es la que obliga a mirarlos."""
    tabla = _tabla_del_escandallo(_cuerpo())
    thead = tabla[tabla.index("<thead"):tabla.index("</thead>")]
    assert _ancho(thead, "th") == ANCHO_ESPERADO, (
        "la cabecera del escandallo ya no tiene %d columnas. Si el cambio es a "
        "propósito, hay que ajustar la fila, el pie y el `colSpan` de «Sin "
        "coste» A LA VEZ — si no, la tabla sigue pintando y miente en los "
        "rótulos." % ANCHO_ESPERADO)


def test_CADA_FILA_PINTA_TANTAS_CELDAS_COMO_COLUMNAS_TIENE_LA_CABECERA():
    """ESTE es el fallo del 11/09: trece celdas para catorce rótulos."""
    tabla = _tabla_del_escandallo(_cuerpo())
    tbody = tabla[tabla.index("<tbody"):tabla.index("</tbody>")]
    # La fila tiene dos ramas: la normal y la de «Sin coste». Las celdas
    # comunes (las cuatro de identificación y las tres finales) están fuera del
    # ternario; las de en medio son la rama con coste.
    con_coste = tbody[tbody.index("<>"):tbody.index("</>")]
    # El `<tbody>` lleva las celdas de LAS DOS ramas del ternario. La fila que
    # se pinta de verdad es: identificación + una rama + finales. Se descuenta
    # la rama de «Sin coste» (la única celda con `colSpan`) para quedarse con
    # la ancha, que es la que se rompió.
    sin_coste = sum(int(x) for x in re.findall(r"<td\b[^>]*colSpan=\{(\d+)\}", tbody))
    fila = _ancho(tbody, "td") - sin_coste
    assert fila == ANCHO_ESPERADO, (
        "la fila del escandallo pinta %d celdas y la cabecera tiene %d. "
        "Al navegador le da igual: corre las columnas a la izquierda y cada "
        "número sale bajo el rótulo de otro." % (fila, ANCHO_ESPERADO))
    assert _ancho(con_coste, "td") == sin_coste, (
        "la rama con coste pinta %d celdas y el aviso «Sin coste» tapa %d"
        % (_ancho(con_coste, "td"), sin_coste))


def test_LA_FILA_SIN_COSTE_TAPA_EXACTAMENTE_LAS_COLUMNAS_QUE_SUSTITUYE():
    """El aviso «Sin coste» ocupa el hueco de la rama con coste. Si el
    `colSpan` se queda corto, esa fila también corre los rótulos."""
    tabla = _tabla_del_escandallo(_cuerpo())
    tbody = tabla[tabla.index("<tbody"):tabla.index("</tbody>")]
    con_coste = _ancho(tbody[tbody.index("<>"):tbody.index("</>")], "td")
    m = re.search(r"colSpan=\{(\d+)\}[^>]*>\s*\n?\s*Sin coste", tbody)
    assert m is None or int(m.group(1)) == con_coste, (
        "el aviso «Sin coste» abarca %s columnas y la rama con coste pinta %d"
        % (m.group(1), con_coste))
    # Y por si el rótulo cambia de texto: se localiza por la única celda con
    # `colSpan` del cuerpo.
    spans = [int(x) for x in re.findall(r"<td\b[^>]*colSpan=\{(\d+)\}", tbody)]
    assert spans == [con_coste], (
        "el `colSpan` del cuerpo es %s y la rama con coste pinta %d celdas"
        % (spans, con_coste))


def test_EL_PIE_DE_TOTALES_TAMBIEN_CUADRA():
    tabla = _tabla_del_escandallo(_cuerpo())
    tfoot = tabla[tabla.index("<tfoot"):]
    # Los ocho herrajes del pie se pintan con un `.map`, no uno a uno.
    mapeados = re.search(r"\[([^\]]*)\]\.map\(k =>", tfoot)
    assert mapeados, "el pie ya no pinta los herrajes con un `.map`"
    n_map = len([x for x in mapeados.group(1).split(",") if x.strip()])
    total = _ancho(tfoot, "td") + n_map - 1  # la celda del `.map` cuenta n veces
    assert total == ANCHO_ESPERADO, (
        "el pie de totales pinta %d columnas y la cabecera tiene %d"
        % (total, ANCHO_ESPERADO))


def test_LA_MANO_DE_OBRA_Y_EL_HKT_SON_DOS_COLUMNAS_DISTINTAS():
    """Se comprueba el ORDEN, que es lo que se rompió: el HKT va ANTES de la
    mano de obra, en la cabecera y en la fila. Con las dos celdas presentes
    pero cambiadas de sitio, la tabla seguiría descuadrada."""
    tabla = _tabla_del_escandallo(_cuerpo())
    thead = tabla[tabla.index("<thead"):tabla.index("</thead>")]
    assert thead.index("HKT Blum") < thead.index("M. obra")
    tbody = tabla[tabla.index("<tbody"):tabla.index("</tbody>")]
    con_coste = tbody[tbody.index("<>"):tbody.index("</>")]
    assert "d.hkt" in con_coste, (
        "la fila del escandallo ya no pinta el HKT: es el fallo del 11/09 otra "
        "vez — la columna de la cabecera se queda sin su celda y todo lo que "
        "viene detrás se corre una casilla")
    assert con_coste.index("d.hkt") < con_coste.index("d.mo"), (
        "el HKT se pinta DESPUÉS de la mano de obra y la cabecera los anuncia "
        "al revés")


def test_EL_PVP_DEL_ESCANDALLO_ES_EL_MISMO_DEL_QUE_SALE_EL_MARGEN():
    """Master, 11/09: «porque arriba a la izquierda da un margen y abajo a la
    derecha otro». La columna de PVP imprimía el precio de tarifa y la de al
    lado restaba sobre el neto: con descuento, PVP − Coste no daba el margen de
    su propia fila."""
    tabla = _tabla_del_escandallo(_cuerpo())
    tbody = tabla[tabla.index("<tbody"):tabla.index("</tbody>")]
    assert re.search(r"\{eur\(m\.pvpNeto\)\}", tbody), (
        "el escandallo ya no imprime `pvpNeto`; si vuelve a imprimir `m.pvp` "
        "la fila dejará de cuadrar en cuanto haya un descuento")
    assert not re.search(r"(?<!\$)\{eur\(m\.pvp\)\}", tbody), (
        "vuelve a imprimirse el PVP de tarifa junto a un margen calculado "
        "sobre el neto")
    tfoot = tabla[tabla.index("<tfoot"):]
    assert "eur(baseImponible)" in tfoot, (
        "el pie del escandallo suma el PVP bruto mientras el margen se calcula "
        "sobre la base imponible: los dos totales no cuadran entre sí")
