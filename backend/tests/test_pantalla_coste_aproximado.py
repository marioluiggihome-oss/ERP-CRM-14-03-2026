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


def test_LAS_COLUMNAS_DE_COSTE_ESTAN_SIEMPRE_Y_NO_ENSANCHAN_LA_TABLA():
    """EL DESGLOSE ORIGINAL, RECUPERADO (master, 31/08: «hay que buscar bien
    dónde está el desglose de Cocina Montada 3 inicial»).

    Estaba, y no donde se buscaba: CM3 nació el 14/08 siendo una CARCASA que
    reutilizaba `RelacionReview` —lo dice su propia cabecera—, así que el
    desglose vivía allí. Y funcionaba de una forma que se había perdido:

        · DOS columnas, no seis: «Coste» y «Margen» (solo el %).
        · ESTAN SIEMPRE. Con el candado echado enseñan «•••»; al abrirlo, la
          cifra. Al tocar el candado NO se añade ni se quita una columna.
        · El candado ES la cabecera de la columna.
        · Margen con semáforo: ≥40 % verde · ≥25 % ámbar · por debajo, rojo.
        · Sin coste conocido: «—», nunca un número.

    LO QUE ARREGLA, Y ES TODO EL ASUNTO: cuando las columnas aparecían y
    desaparecían con el candado, la tabla se ensanchaba de golpe, la cabecera se
    salía de pantalla y el PVP —lo que se mira para vender— quedaba contra el
    borde. Eso es lo que el master vio y no le gustó, y por eso decía que la de
    antes era mejor: no lo era por tener menos datos, era por no moverse.

    (El 31/08 por la mañana lo saqué a un panel debajo. Estaba MÁS lejos de lo
    que él recordaba, no más cerca. Este candado guarda lo que había de verdad,
    comprobado contra la rama del 14/08.)
    """
    cuerpo = sin_comentarios(_lee(CM3))

    # LA CABECERA DE LA TABLA PRINCIPAL, no «el primer <thead> del fichero».
    # Desde que existe el panel de Frentes hay DOS tablas, y la de aquel sí
    # esconde sus columnas de dinero con el candado (es correcto: ahí el coste
    # de compra no se enseña con un cliente delante). Se ancla en «PVP Ud.»,
    # que solo está en la tabla del presupuesto.
    fin_tabla = cuerpo.index("PVP Ud.</th>")
    cabecera = cuerpo[cuerpo.rindex("<thead", 0, fin_tabla):cuerpo.index("</thead>", fin_tabla)]
    assert "{verCoste &&" not in cabecera, (
        "hay columnas que aparecen y desaparecen con el candado: la tabla se "
        "ensancha al abrirlo, la cabecera se sale y el PVP queda contra el "
        "borde. Es justo lo que el master pidió deshacer")
    assert ">Margen<" in cabecera and "Coste" in cabecera, (
        "faltan las columnas de coste y margen en la cabecera")

    # Y en las celdas: se TAPAN, no se quitan.
    assert "OCULTO" in cuerpo, (
        "las celdas de coste no se tapan con un marcador: si se dejan vacías, "
        "la columna se estrecha y la tabla vuelve a moverse")
    i = cuerpo.index("const OCULTO")
    assert "'•••'" in cuerpo[i:i + 60], "el marcador de tapado ha cambiado"


def test_EL_MARGEN_LLEVA_SEMAFORO():
    """Del desglose original. Un margen es lo único de esta pantalla que sí es
    bueno o malo —por eso lleva color, y el importe no (docs/DISENO.md)."""
    cuerpo = sin_comentarios(_lee(CM3))
    i = cuerpo.index("m.margenPct >= 40")
    tramo = cuerpo[i:i + 200]
    for umbral, color in (("40", "text-ok-600"), ("25", "text-aviso-600")):
        assert umbral in tramo, f"falta el umbral del {umbral}%"
        assert color in tramo, f"falta el color de ese tramo ({color})"
    assert "text-error-600" in tramo, "un margen por debajo del 25% no se pinta en rojo"


def test_UN_MUEBLE_SIN_COSTE_ENSEÑA_UNA_RAYA_Y_NO_UN_NUMERO():
    """Es la regla que el desglose original ya traía
    (`m.encontrado ? eur(m.coste) : '—'`) y la que el master reeligió el 31/08."""
    cuerpo = sin_comentarios(_lee(CM3))
    assert "m.coste == null ? <span className=\"text-aviso-600\">—</span>" in cuerpo, (
        "una línea sin coste no enseña «—»: enseñaría un hueco o, peor, un cero")
    assert "m.margenPct == null ? '—'" in cuerpo, (
        "se está calculando un porcentaje de margen sobre un coste que no existe")


def test_EL_CANDADO_SE_DECIDE_EN_UN_SOLO_SITIO():
    """Ahora hay TRES botones que lo abren: las dos cabeceras y el del pie.
    Escrito tres veces, el día que se cambie el gesto cambiaría en uno y no en
    los otros, y el master pulsaría un candado que no abre — que es exactamente
    el fallo que este botón ya tuvo el 30/08."""
    cuerpo = sin_comentarios(_lee(CM3))
    assert "const clicCandado" in cuerpo, (
        "el gesto del candado no está en una sola función")
    assert cuerpo.count("onClick={clicCandado}") >= 3, (
        f"hay botones de candado que no usan el manejador común "
        f"({cuerpo.count('onClick={clicCandado}')} de 3)")
    assert "handlersCandado.consumir()" in cuerpo[cuerpo.index("const clicCandado"):
                                                  cuerpo.index("const clicCandado") + 700], (
        "el manejador común no consume la pulsación larga: el clic que manda el "
        "navegador al soltar volvería a cerrar el candado en el mismo gesto")


def test_SE_DICE_CUANTAS_LINEAS_SE_QUEDAN_FUERA_DEL_MARGEN():
    """Marcar la fila con «—» no basta: con veinte líneas nadie va contando
    cuáles la llevan, y quien fija el precio mira el total de abajo. El aviso se
    mudó al pie, junto al margen, que es donde se lee."""
    cuerpo = sin_comentarios(_lee(CM3))
    assert 'data-testid="cm3-aviso-casco"' in cuerpo, (
        "no se avisa de cuántas líneas se han quedado sin coste")
    i = cuerpo.index('data-testid="cm3-aviso-casco"')
    aviso = " ".join(cuerpo[i:i + 700].split())
    assert "sin coste" in aviso, "el aviso no dice qué pasa con esas líneas"
    assert "MÁS ALTO que el real" in aviso, (
        "el aviso no advierte de en qué DIRECCIÓN miente el margen: si faltan "
        "costes, sale más alto de lo que es")
    # Y que salga JUNTO al total, no en otra parte de la pantalla.
    total = cuerpo.index('data-testid="cm3-total-coste"')
    assert 0 < i - total < 900, (
        "el aviso no está junto al margen total: ahí es donde se mira antes de "
        "fijar un precio")
