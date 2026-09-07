# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
EL PRESUPUESTADOR TIENE DOS CARAS, Y LAS DOS TIENEN QUE HACER LO MISMO.

La misma pantalla se pinta de dos formas: una TABLA a partir de `lg`, y una
FICHA por mueble (`lg:hidden`) para abajo. El master trabaja en una tablet de
8,6 pulgadas — lo dijo el 06/09 al pedir que «Mis renders» subiera a la
cabecera— y ahí lo que se ve es la FICHA, no la tabla.

CÓMO SE HA LLEGADO A ESTO. Todo lo que se le fue añadiendo al presupuestador el
07/09 —el descuento por línea, la cota definitiva del alto, el escalón que sube
solo, el coste de un electrodoméstico— se hizo sobre la TABLA. La ficha se
quedó atrás, o sea que en el dispositivo donde de verdad se trabaja no existía
nada de eso.

Y una de esas diferencias no era una función que faltaba: era un NÚMERO
DISTINTO. La ficha seguía pintando el total en BRUTO mientras el pie del
presupuesto ya descontaba, así que en cuanto hubiera un descuento la línea
decía una cifra y el total otra — y ninguna de las dos parecía un error.

Esta prueba no compara pixel a pixel: comprueba que lo que MUEVE DINERO o
DECIDE UNA MEDIDA está en las dos.
"""
import os
import re

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CM3 = os.path.join(RAIZ, "frontend", "src", "components", "CocinaMontada3.jsx")


def _partes():
    """La FICHA (`lg:hidden`) y la TABLA, por separado."""
    with open(CM3, "r", encoding="utf-8") as f:
        src = f.read()
    i = src.index('<div className="lg:hidden space-y-2.5">')
    j = src.index("<table", i)
    ficha = src[i:j]
    k = src.index("</table>", j)
    return ficha, src[j:k]


# Lo que tiene que estar en las DOS. Cada una con lo que se rompe si falta.
EN_LAS_DOS = [
    ("setDto(m._k",
     "el descuento por línea: en la tablet no se podría poner"),
    ("m.importeLinea",
     "el total CON el descuento: en bruto, la línea dice una cifra y el pie "
     "otra, y ninguna parece un error"),
    ("m.dtoAplicado",
     "el porcentaje que se está aplicando de verdad"),
    ("m.escalonSubido",
     "el aviso de que el escalón ha subido solo: si no, el precio se mueve y "
     "nadie sabe por qué"),
    ("setMedidaMueble(m._k, 'alto'",
     "el alto tecleable de los muebles que no tienen escalones"),
    ("setMedidaMueble(m._k, 'ancho'",
     "el ancho tecleable"),
    ("m.esElectro",
     "que un electrodoméstico no se despiece como un mueble: si no, se le "
     "pintan cuatro ceros y un margen del 100 %"),
    ("manoDe(m)",
     "la mano leída de la LÍNEA y no del código suelto: «A60D/I» acaba en «I» "
     "y saldría como izquierda"),
    ("setPvp(m._k",
     "el precio a mano"),
    ("verCoste",
     "el candado del coste"),
]


def test_LA_FICHA_HACE_LO_MISMO_QUE_LA_TABLA():
    ficha, tabla = _partes()
    faltan = []
    for trozo, porque in EN_LAS_DOS:
        if trozo not in ficha:
            faltan.append(f"FICHA (tablet) — {porque}")
        if trozo not in tabla:
            faltan.append(f"TABLA (escritorio) — {porque}")
    assert not faltan, (
        "las dos caras del presupuestador se han separado:\n  - "
        + "\n  - ".join(faltan))


def test_LA_COTA_DEFINITIVA_DEL_ALTO_ESTA_EN_LOS_MUEBLES_DE_LAS_DOS_CARAS():
    """Se mira por su ETIQUETA, no por el nombre de la función.

    Las dos caras tienen DOS sitios donde se escribe una cota: la rama de
    costados/laterales (que la tenía desde agosto) y la de los muebles con
    escalón (que se añadió el 07/09). Buscando «setMedidaReal(…altoReal…)» a
    secas, la de los costados hace que la prueba pase aunque se caiga la de los
    muebles — se probó, y la mutación se escapaba.
    """
    ficha, tabla = _partes()
    assert 'data-testid="cm3-alto-real-ficha"' in ficha, (
        "la FICHA (tablet) no deja escribir el alto definitivo de un mueble")
    assert 'data-testid="cm3-alto-real-mueble"' in tabla, (
        "la TABLA no deja escribir el alto definitivo de un mueble")
    # Y que la casilla siga ESCRIBIENDO, no solo existiendo.
    for nombre, cuerpo, etq in (("la ficha", ficha, "cm3-alto-real-ficha"),
                                ("la tabla", tabla, "cm3-alto-real-mueble")):
        i = cuerpo.index(f'data-testid="{etq}"')
        assert "setMedidaReal(m._k, 'altoReal'" in cuerpo[max(0, i - 500):i], (
            f"la casilla del alto de {nombre} ya no guarda la medida")


def test_LA_FICHA_SEPARA_EL_ELECTRO_DEL_MUEBLE_EN_LAS_DOS_RAMAS():
    """No basta con que la palabra `esElectro` aparezca: tienen que estar LAS
    DOS ramas. Se probó quitando la del electro y la prueba seguía en verde,
    porque la otra (`!m.esElectro`) también la nombra — y entonces un
    electrodoméstico se quedaba sin desglose ninguno."""
    ficha, _ = _partes()
    assert "verCoste && m.esElectro &&" in ficha, (
        "la ficha ya no enseña el coste de un electrodoméstico")
    assert "verCoste && !m.esElectro &&" in ficha, (
        "la ficha ya no enseña el desglose de un mueble")


def test_NINGUNA_DE_LAS_DOS_pinta_el_total_en_bruto():
    """El fallo concreto que había: `pvp × qty` como total de la línea. Con un
    descuento puesto, eso es una cifra que no se cobra."""
    ficha, tabla = _partes()
    patron = re.compile(r"font-black[^>]*>\s*\{eur\(\(Number\(m\.pvp\)")
    for nombre, cuerpo in (("la ficha", ficha), ("la tabla", tabla)):
        assert not patron.search(cuerpo), (
            f"{nombre} pinta como TOTAL el PVP por unidades, sin el descuento")


def test_LAS_DOS_CARAS_SALEN_DE_LA_MISMA_LISTA():
    """`filas` es donde se calculan el neto, el coste y el margen. Si una de las
    dos se pintara desde `muebles` en crudo, tendría los números sin calcular."""
    ficha, tabla = _partes()
    for nombre, cuerpo in (("la ficha", ficha), ("la tabla", tabla)):
        assert "filasFiltradas.map" in cuerpo, (
            f"{nombre} ya no se pinta desde `filas`: sus importes serían otros")
