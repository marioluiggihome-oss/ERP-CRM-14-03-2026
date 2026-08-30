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
"""
import os
import re

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


def test_EL_PRESUPUESTADOR_MARCA_EL_COSTE_GENERICO():
    """Rentabilidad ya lo marcaba; aquí es donde se fija el precio."""
    s = _lee(CM3)
    # EN LA CELDA DEL COSTE, no «en algún sitio del fichero». La primera versión
    # buscaba `m.despiece?.generica` en todo el JSX y esa cadena también está en
    # el aviso de arriba, así que aprobaba con la marca de la fila quitada.
    # LA CELDA DEL COSTE, anclada en su `<td>` — `{eur(m.coste)}` también sale
    # antes, en el resumen de arriba, y anclar ahí dejaba pasar el fallo.
    i = s.index('text-right font-mono text-dato-900 font-black">')
    celda = s[i:i + 900]
    assert "m.despiece?.generica" in celda, (
        "la celda del coste ya no distingue el genérico de uno real: mismo "
        "aspecto, y uno de los dos es inventado")
    assert "aprox" in celda, "no se rotula la línea aproximada"


def test_SE_DICE_CUANTO_DEL_MARGEN_ES_INVENTADO():
    """Marcar la fila no basta: con veinte líneas nadie va contando cuáles
    llevan «aprox», y el margen de abajo incluye ese coste."""
    s = _lee(CM3)
    assert "coste\n              aproximado" in s or "coste aproximado" in s.replace("\n", " "), (
        "no hay aviso de cuántas líneas llevan coste inventado")
    assert "margen de abajo incluye" in s.replace("\n", " ").replace("  ", " "), (
        "no se dice que el margen total incluye el coste inventado, que es lo "
        "que de verdad hay que saber antes de fijar un precio")


def test_EL_GENERICO_SIGUE_MARCADO_EN_RENTABILIDAD():
    """No se ha quitado de donde ya estaba al añadirlo aquí."""
    rent = _lee(RENT)
    assert "r.generica &&" in rent, (
        "Rentabilidad ha dejado de marcar el coste aproximado")


def test_LA_FAMILIA_GENERICA_SIGUE_SIENDO_UN_BAJO_Y_SE_DICE_CUAL():
    """Si algún día cambia el mueble del respaldo, el aviso tiene que cambiar
    con él: decir «bajo de 80 con una puerta» y usar otra cosa es peor que no
    decir nada."""
    rent = _lee(RENT)
    i = rent.index("export const RULE_GENERICA")
    linea = rent[i:i + 200]
    assert "'Bajo Con Balda'" in linea and "alto: 800" in linea and "puertas: 1" in linea, (
        "ha cambiado el mueble genérico: hay que actualizar el aviso del "
        "Presupuestador, que dice «bajo de 80 con una puerta»")
    assert "bajo de 80 con una puerta" in _lee(CM3), (
        "el aviso ya no dice de qué mueble sale el coste inventado")
