# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
UN COSTE QUE NO SE SABE NO PUEDE TENER LA PINTA DE UNO QUE SÍ.

El master, 30/08, importando una proforma de Alvic: «ahora toco el candado y no
veo mi desglose como antes».

LO QUE SE ENCONTRÓ AL MIRARLO, que es peor que un desglose que no sale:

`RULES[familia] || RULE_GENERICA` no devuelve «no se sabe» cuando la familia no
existe. Devuelve el coste de un «Bajo Con Balda» de 800 mm con una puerta y una
pata. O sea que un PANEL de 150×400 se costeaba como un bajo estándar, y el
número salía en pantalla con exactamente la misma pinta que uno real.

Rentabilidad MV lo marcaba con un «aprox» diminuto. El Presupuestador —que es
donde se fija el precio— NO lo marcaba en absoluto: se veía un coste, un margen
y un porcentaje, todos inventados y ninguno señalado.

Y LA IMPORTACIÓN LO AGRAVABA: fabricaba un código para cualquier línea que no lo
trajera, y el último `else` la bautizaba `B<ancho>D/I`. Con paneles salía
`B150D/I` —un bajo de 150 cm, que no existe: el ancho estándar más grande es
120— y con un alto de 400 cm. Un código inventado se arrastra al pedido y llega
al taller.

Es la ADN del proyecto: NUNCA inventar. Lo que no se sabe se dice.

── 31/08: EL MASTER SUBIÓ LA APUESTA, Y ESTE CANDADO CAMBIA CON ÉL ───────────

Marcarlo con un «aprox» no bastaba, y se vio con su cocina delante: de 12
líneas, 7 eran PANEL u OTRO y cada una entraba costando 67,01 € —lo que cuesta
un bajo de 80—. Un TIRADOR costando 67,01 €. Con eso, el margen del presupuesto
entero salía en −126,8 % en una cocina que gana dinero: el número seguía
sumando aunque llevara su etiqueta al lado.

Preguntado, eligió: «Nada: “?” y fuera del margen». Así que ya no se marca un
coste inventado — NO SE CALCULA. La línea se queda sin coste, se dice en el
panel, y el aviso del pie cuenta cuántas hay y advierte de que el margen que se
ve es MÁS ALTO que el real.

Lo que este fichero vigilaba sigue vigilado; lo que ha cambiado es el remedio:
antes «que se note que es inventado», ahora «que no se invente».
"""
import os
import re

from jsx_limpio import sin_comentarios

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CM3 = os.path.join(RAIZ, "frontend", "src", "components", "CocinaMontada3.jsx")
RENT = os.path.join(RAIZ, "frontend", "src", "components", "RentabilidadMV.jsx")

# Los anchos estándar de fabricación (CLAUDE.md). No hay bajos de 150.
ANCHO_MAXIMO_CM = 120


def _lee(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        return f.read()


def _importar_alvic():
    """El cuerpo de la importación, y solo ese."""
    s = _lee(CM3)
    i = s.index("const importarAlvic = async")
    return s[i:s.index("\n  };", i)]


def test_LAS_FAMILIAS_QUE_SE_SABEN_DESGLOSAR_SE_PUEDEN_PREGUNTAR():
    """Sin esto, cada pantalla lo adivina por su cuenta y se separan."""
    rent = _lee(RENT)
    assert "export const FAMILIAS_CON_DESPIECE" in rent
    assert "export const tieneDespieceReal" in rent, (
        "no hay forma de preguntar si una familia se puede costear de verdad")


def test_UN_PANEL_NO_SE_BAUTIZA_COMO_BAJO():
    """`B150D/I` no existe: el ancho estándar más grande es 120 cm."""
    trozo = _importar_alvic()
    assert "tieneDespieceReal(tipo)" in trozo, (
        "la importación no comprueba si el tipo es una familia que se sabe "
        "costear: le pondrá nombre de bajo a lo que no lo es")
    # LA CONDICIÓN DEL `if`, no «la palabra aparece por ahí cerca». La primera
    # versión de esta prueba miraba 700 caracteres hacia atrás y ahí estaba el
    # `const conocida = …`, así que aprobaba aunque se quitara la comprobación
    # del `if`. Se probó rompiéndolo y no mordió.
    # LA LÍNEA DEL `if`, entera. Nada de ventanas de N caracteres ni de regex
    # con llaves —el propio patrón del código lleva `{1,5}` dentro—: se busca la
    # línea que decide, y se mira si en ELLA está la comprobación.
    linea = next((l for l in trozo.split("\n") if "test(codMv)" in l), None)
    assert linea, "no se ha podido leer la condición que deduce el código"
    assert "conocida" in linea, (
        f"el código de bajo se sigue fabricando sin mirar la familia: {linea.strip()}")


def test_SIN_FAMILIA_RECONOCIDA_NO_SE_INVENTA_UN_CODIGO():
    """Un `B60D/I` puesto por defecto es un mueble que nadie ha pedido."""
    trozo = _importar_alvic()
    assert "`B${widthCm || 60}D/I`" not in trozo, (
        "se sigue poniendo `B60D/I` por defecto a una línea sin código")
    assert "conocida && widthCm" in trozo, (
        "el código por defecto no mira si la familia se conoce")


def test_EL_PRESUPUESTADOR_NO_CALCULA_UN_COSTE_QUE_NO_SABE():
    """El remedio de hoy: no es marcarlo, es no inventarlo.

    Se comprueba en el CÁLCULO, no en el rótulo: mientras `despiece` siga
    devolviendo un número para una familia que no conoce, ese número acabará
    sumando en algún sitio — que es exactamente lo que pasó con el «aprox».
    """
    rent = _lee(RENT)
    i = rent.index("const costeTotal")
    sentencia = rent[i:rent.index(";", i)]
    assert "sinDespiece" in sentencia, (
        "el coste total se sigue calculando para una familia que el despiece no "
        "conoce: sale el precio de un bajo de 80 con la misma pinta que un "
        "coste de verdad, y arrastra el margen del presupuesto entero")
    j = rent.index("const sinDespiece")
    assert "R.generica" in rent[j:rent.index("\n", j)], (
        "`sinDespiece` no se deduce de la regla genérica")


def test_LA_LINEA_SIN_COSTE_SE_DICE_EN_EL_PANEL():
    """Sin coste no es lo mismo que coste cero: hay que verlo y saber por qué."""
    s = sin_comentarios(_lee(CM3))
    assert "Sin coste — el despiece no conoce" in s, (
        "una línea sin coste no se explica en el panel: se vería un hueco y "
        "parecería que la pantalla está rota")


def test_SE_DICE_CUANTAS_LINEAS_SE_QUEDAN_FUERA_DEL_MARGEN():
    """Marcar la fila no basta: con veinte líneas nadie va contando cuáles
    llevan la marca, y quien fija el precio mira el margen de abajo.

    Y AHORA EL AVISO DICE LO CONTRARIO QUE ANTES, que es el cambio: el margen ya
    no «incluye un coste inventado» sino que es MÁS ALTO que el real, porque
    esas líneas no suman coste. Decirlo al revés sería peor que no decirlo.
    """
    s = sin_comentarios(_lee(CM3)).replace("\n", " ")
    while "  " in s:
        s = s.replace("  ", " ")
    assert "línea{sinCoste.length === 1 ? '' : 's'} sin coste." in s, (
        "no se cuenta cuántas líneas se han quedado sin coste")
    assert "el margen que ves es más alto que el real" in s, (
        "no se advierte de que el margen de abajo sale más alto de lo que es: "
        "es justo lo que hay que saber antes de fijar un precio")
    assert "margen de abajo incluye" not in s, (
        "sigue el aviso viejo, que decía que el margen INCLUYE un coste "
        "inventado. Ya no se inventa ninguno: ahora el margen sale ALTO porque "
        "faltan costes. Un aviso que dice lo contrario de lo que pasa engaña "
        "más que no tener aviso")


def test_EL_GENERICO_SIGUE_MARCADO_EN_RENTABILIDAD():
    """No se ha quitado de donde ya estaba al añadirlo aquí."""
    rent = _lee(RENT)
    assert "r.generica &&" in rent, (
        "Rentabilidad ha dejado de marcar el coste aproximado")


def test_LA_REGLA_GENERICA_SIGUE_MARCANDOSE_COMO_TAL():
    """`RULE_GENERICA` no desaparece —se sigue usando para las medidas y para
    saber que la familia no se conoce—, pero tiene que seguir llevando su
    bandera: es de ahí de donde sale `sinDespiece`. Sin la bandera, una familia
    desconocida volvería a costearse como un bajo de 80 y en silencio."""
    rent = _lee(RENT)
    i = rent.index("export const RULE_GENERICA")
    linea = rent[i:i + 200]
    assert "generica: true" in linea, (
        "la regla genérica ha perdido su bandera: `sinDespiece` dejaría de "
        "detectarla y volvería el coste inventado de un bajo de 80")


def test_LOS_COSTES_VIVEN_FUERA_DE_LA_TABLA():
    """El master, 31/08: «no me gusta este sistema de ver costos, me gustaba más
    la pantalla anterior», y al elegir: los costes en un panel aparte.

    Tenía razón por lo que se veía en su pantallazo: el candado metía SEIS
    columnas más en la tabla, así que la cabecera se salía de pantalla y el
    PVP —que es lo que se mira para vender— quedaba arrinconado contra el borde.
    La tabla es la que se enseña con un cliente delante; el coste es otra
    conversación y va en otro sitio.

    LO QUE SE VIGILA: que la tabla NO tenga columnas que aparezcan y desaparezcan
    con el candado. Que exista el panel no basta — el fallo era la tabla que se
    ensancha, y podrían convivir los dos.
    """
    cuerpo = sin_comentarios(_lee(CM3))
    assert 'data-testid="cm3-panel-costes"' in cuerpo, (
        "no hay panel de costes: el desglose por línea no se ve en ninguna parte")

    # Ni una cabecera ni una celda condicionadas al candado dentro de la tabla.
    cabecera = cuerpo[cuerpo.index("<thead"):cuerpo.index("</thead>")]
    assert "verCoste" not in cabecera, (
        "han vuelto las columnas de coste a la cabecera de la tabla: con el "
        "candado abierto la tabla se ensancha, la cabecera se sale y el PVP "
        "queda contra el borde")
    cuerpo_tabla = cuerpo[cuerpo.index("</thead>"):cuerpo.index('data-testid="cm3-panel-costes"')]
    assert "{verCoste && (\n                        <td" not in cuerpo_tabla, (
        "han vuelto las celdas de coste a las filas de la tabla")
