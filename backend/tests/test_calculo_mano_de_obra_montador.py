# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
LO QUE COBRA UN MONTADOR POR MUEBLE MONTADO. ESTO ES NÓMINA.

El master, 28/08/2026: «la rentabilidad por mueble montado va a ser de 17 euros,
no de 20. Y además lo podré cambiar para cada montador, incluso».

Así que hay tres escalones, y el orden importa:

    1. la cifra que el master le haya puesto A ÉL, en su ficha;
    2. si no tiene, la de la casa, en los ajustes;
    3. si tampoco hay ajuste, 17 €.

LO QUE MÁS CARO SALE AQUÍ ES EL CERO. Las rutas lo leían con
`float(aj.get("manoObraPorMueble") or 0)`, y con un `or` un 0 tecleado a
propósito por el master se cae al escalón siguiente: el montador cobraría 17 €
por mueble cuando su jefe había decidido que no cobra. Pagar de menos se
reclama; pagar de más no se devuelve.

Y la otra mitad: la PANTALLA de Rentabilidad calcula el margen de la casa con
esta misma cifra. Si las dos se separan, la pantalla enseña un margen y la
nómina paga otra cosa, sin que salte ningún error.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("JWT_SECRET", "secreto-de-pruebas-largo-y-aleatorio-0123456789")

from services import comisiones as C  # noqa: E402

CASA = {"manoObraPorMueble": 20.0}


def test_son_17_EUROS_y_no_20():
    """El número que dijo el master. Si alguien lo cambia, que sea a sabiendas."""
    assert C.MANO_DE_OBRA_POR_DEFECTO == 17.0, (
        "la mano de obra por mueble montado son 17 € (master, 28/08). Cambiarla "
        "cambia la nómina de todos los montadores a la vez.")


def test_sin_cifra_propia_y_sin_ajuste_cobra_LA_DE_LA_CASA_por_defecto():
    assert C.mano_de_obra_de({}, {}) == 17.0
    assert C.mano_de_obra_de(None, None) == 17.0
    assert C.mano_de_obra_de({"id": "u"}) == 17.0


def test_el_ajuste_de_la_casa_manda_sobre_el_defecto():
    assert C.mano_de_obra_de({"id": "u"}, CASA) == 20.0


def test_LA_CIFRA_DEL_MONTADOR_manda_sobre_la_de_la_casa():
    """Es lo que pidió el master: poder cambiarla montador a montador."""
    u = {"id": "u", "manoObraPorMueble": 25.5}
    assert C.mano_de_obra_de(u, CASA) == 25.5
    assert C.mano_de_obra_de(u, {}) == 25.5


def test_UN_CERO_PUESTO_A_PROPOSITO_se_respeta_y_no_se_cae_al_siguiente():
    """El fallo que traían las rutas escrito con `or`.

    Si el master le pone 0 a alguien, es una decisión suya. Con `or`, ese 0 es
    falso y se cae al escalón siguiente: el montador cobraría 17 € por mueble
    sin que nadie lo hubiera decidido, y en un pedido de 40 muebles son 680 €
    que no se recuperan.
    """
    assert C.mano_de_obra_de({"manoObraPorMueble": 0}, CASA) == 0.0
    assert C.mano_de_obra_de({"manoObraPorMueble": 0.0}, CASA) == 0.0
    assert C.mano_de_obra_de({}, {"manoObraPorMueble": 0}) == 0.0


def test_NO_TENER_CIFRA_no_es_lo_mismo_que_tener_un_cero():
    """`None` y la clave ausente son «cobra la de la casa». Distinguirlos del 0
    es justo lo que hace que el caso de arriba se pueda expresar."""
    assert C.mano_de_obra_de({"manoObraPorMueble": None}, CASA) == 20.0
    assert C.mano_de_obra_de({}, CASA) == 20.0


def test_una_cifra_CORRUPTA_no_inventa_una_nomina():
    """Texto en la casilla, o un valor que no es número: se pasa al escalón
    siguiente. Nunca se convierte en un importe a ojo."""
    for basura in ("", "  ", "veinte", [], {}, "17 €"):
        assert C.mano_de_obra_de({"manoObraPorMueble": basura}, CASA) == 20.0, basura
        assert C.mano_de_obra_de({"manoObraPorMueble": basura}, {}) == 17.0, basura


def test_una_cifra_NEGATIVA_no_resta():
    """Un descuido con el signo no puede volverse una comisión en negativo."""
    assert C.mano_de_obra_de({"manoObraPorMueble": -5}, CASA) == 0.0


def test_la_cifra_LLEGA_HASTA_EL_IMPORTE_y_no_se_queda_por_el_camino():
    """Que el resolver acierte no sirve de nada si el cálculo no lo usa."""
    mano = C.mano_de_obra_de({"manoObraPorMueble": 17.0}, {})
    assert C.comision_montadores(mano, 40)["total"] == 680.0
    assert C.comision_montadores(C.mano_de_obra_de({}, {}), 10)["total"] == 170.0


def test_la_PANTALLA_de_rentabilidad_usa_la_misma_cifra_que_la_nomina():
    """La pantalla calcula el margen de la casa con la mano de obra por mueble.

    Si se separan, la pantalla enseña un margen con 20 € y la nómina paga 17 —o
    al revés—, y no salta ningún error: los dos números son plausibles. Por eso
    se lee el de la pantalla del fichero, y no se copia aquí.
    """
    import re

    raiz = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ruta = os.path.join(raiz, "frontend", "src", "components", "RentabilidadMV.jsx")
    with open(ruta, "r", encoding="utf-8") as f:
        cuerpo = f.read()

    m = re.search(r"export const MANO_DE_OBRA_POR_DEFECTO\s*=\s*([\d.]+)\s*;", cuerpo)
    assert m, ("la pantalla de Rentabilidad ya no exporta "
               "`MANO_DE_OBRA_POR_DEFECTO`: sin eso no hay forma de comprobar "
               "que calcula el margen con lo que de verdad se paga")
    assert float(m.group(1)) == C.MANO_DE_OBRA_POR_DEFECTO, (
        f"la pantalla usa {m.group(1)} € de mano de obra por mueble y la nómina "
        f"paga {C.MANO_DE_OBRA_POR_DEFECTO} €. Uno de los dos miente y ninguno "
        "da error.")

    # Y que la casilla de costes de la pantalla parta de ahí, no de un número suelto.
    assert re.search(r"mano:\s*MANO_DE_OBRA_POR_DEFECTO", cuerpo), (
        "la casilla «mano» de Rentabilidad ha vuelto a llevar un número escrito "
        "a mano: es el camino por el que se separan otra vez")
