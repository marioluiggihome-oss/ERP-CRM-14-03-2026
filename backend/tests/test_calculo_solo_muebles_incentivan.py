# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
SOLO LOS MUEBLES INCENTIVAN. NI PUERTAS, NI COSTADOS, NI SERVICIOS.

El master, 25/08/2026: «las líneas de muebles siempre incentivarán a los
comerciales, pero las puertas y los costados y las líneas manuales con los
distintos servicios que añadamos manualmente no van a llevar compensación de
ningún tipo. Solo los muebles».

NO ES UN MATIZ, CAMBIA EL DINERO POR LOS DOS LADOS:

  · Las unidades. Contar 14 puertas y 4 costados como si fueran muebles paga
    18 comisiones que no existen.
  · Y el TRAMO. Su importe entra en la valoración, así que un pedido de
    11.000 € de muebles con 1.500 € de puertas salta a un tramo que no le toca
    y cobra más POR CADA MUEBLE, además de por las puertas.

En un pedido corriente son 990 € contra 420 €: se pagaba un 136% de más.

CÓMO SE DECIDE QUÉ ES MUEBLE, sin listas escritas a ojo que se quedan viejas:

  · Categoría «lineal» de `nomenclaturas_pdf.FAMILIAS` — costados, laterales,
    regletas, techos y elementos lineales.
  · Tipo «matrix» de la tarifa MV — PUERTAS, VITRINA y REJILLA, que son FRENTES
    (se tarifan por alto x ancho, no por código de mueble).
  · Sin familia = línea manual de servicio.

Y ojo con no pasarse: un ALTO_VITRINA SÍ es un mueble —un casco con puerta de
cristal—. Por eso el corte va por el tipo `matrix` y no por la palabra
«vitrina».
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("JWT_SECRET", "secreto-de-pruebas-largo-y-aleatorio-0123456789")

from services import area_cooperativista as AC  # noqa: E402
from services import comisiones as C  # noqa: E402


@pytest.mark.parametrize("familia,cuenta", [
    ("BAJO", True), ("ALTO", True), ("COLUMNA_DESPENSERO", True),
    ("BAJO_FREGADERO", True), ("COLUMNA_HORNO", True), ("MEDIACOLUMNA", True),
    ("ALTO_VITRINA", True),          # casco con puerta de cristal: ES un mueble
    ("MEDIACOLUMNA_VITRINA", True),
    ("PUERTAS", False), ("VITRINA", False), ("REJILLA_CONFESIONARIO", False),
    ("COSTADOS_COLOR", False), ("COSTADOS_MELAMINA", False),
    ("LATERALES_COLOR", False), ("REGLETA_COLOR", False),
    ("TECHO_COLOR", False), ("ELEMENTOS_LINEALES", False),
    ("", False),                     # línea manual / servicio
])
def test_que_cuenta_y_que_no(familia, cuenta):
    assert C.es_mueble({"familia": familia}) is cuenta, (
        f"«{familia or 'línea manual'}» debería {'contar' if cuenta else 'NO contar'}")


def test_un_ALTO_VITRINA_no_se_confunde_con_la_familia_VITRINA():
    """El caso fino. Si el corte fuera por la palabra «vitrina», se dejarían de
    pagar muebles de verdad — un casco con puerta de cristal es un mueble."""
    assert C.es_mueble({"familia": "ALTO_VITRINA"})
    assert not C.es_mueble({"familia": "VITRINA"})


def test_una_linea_SIN_FAMILIA_no_paga():
    """Una línea manual es un servicio (montaje, portes, medición). Y ante la
    duda NO se paga: pagar de menos se reclama, pagar de más no se devuelve."""
    for l in ({"familia": ""}, {"familia": None}, {}, {"desc": "Montaje"}):
        assert not C.es_mueble(l)


# ── La cuenta completa ───────────────────────────────────────────────────────
PEDIDO = [
    {"familia": "BAJO", "qty": 6, "pvp": 210.0},
    {"familia": "ALTO", "qty": 5, "pvp": 170.0},
    {"familia": "COLUMNA_DESPENSERO", "qty": 3, "pvp": 480.0},
    {"familia": "PUERTAS", "qty": 14, "pvp": 62.0},
    {"familia": "COSTADOS_COLOR", "qty": 4, "pvp": 110.0},
    {"familia": "", "qty": 1, "pvp": 650.0},          # montaje
]


def test_la_base_de_comision_DEJA_FUERA_lo_que_no_es_mueble():
    b = C.base_de_comision(PEDIDO)
    assert b["muebles"] == 14, "las unidades incluyen puertas, costados o servicios"
    assert b["baseImponible"] == 3550.0, (
        "la valoración incluye importe que no es de muebles; eso mueve el TRAMO")
    assert b["sinComision"]["unidades"] == 19
    assert b["sinComision"]["pvp"] == 1958.0


def test_CUANTO_SE_PAGABA_DE_MAS():
    """El número, escrito, para que se vea lo que costaba la confusión."""
    todo_pvp = sum(l["pvp"] * l["qty"] for l in PEDIDO)
    todo_uds = sum(l["qty"] for l in PEDIDO)
    antes = C.comision_comercial(C.base_imponible(todo_pvp), todo_uds)["total"]
    b = C.base_de_comision(PEDIDO)
    ahora = C.comision_comercial(b["baseImponible"], b["muebles"])["total"]
    assert antes == 990.0 and ahora == 420.0


def test_las_PUERTAS_no_pueden_empujar_el_TRAMO():
    """El daño menos visible: no es solo pagar por las puertas, es que su
    importe sube el €/mueble de TODOS los muebles del pedido."""
    muebles = [{"familia": "BAJO", "qty": 10, "pvp": 1150.0}]      # 11.500 €
    puertas = [{"familia": "PUERTAS", "qty": 10, "pvp": 100.0}]    # +1.000 €
    solo = C.base_de_comision(muebles)
    con = C.base_de_comision(muebles + puertas)
    assert solo["baseImponible"] == con["baseImponible"] == 11500.0, (
        "las puertas están entrando en la valoración")
    assert C.euros_por_mueble_comercial(11500.0) == 50.0
    assert C.euros_por_mueble_comercial(12500.0) == 60.0, (
        "con las puertas dentro se saltaría de 50 a 60 € por mueble")


def test_el_descuento_se_aplica_SOLO_sobre_los_muebles():
    b = C.base_de_comision(PEDIDO, descuento_pct=10)
    assert b["baseImponible"] == 3195.0        # 3.550 - 10%


# ── El área usa esta cuenta y no la del pedido entero ────────────────────────
def test_el_area_cuenta_SOLO_MUEBLES():
    p = AC.normaliza_pedido({"id": "A", "confirmedAt": "2026-08-01",
                             "items": PEDIDO, "itemsCount": 33,
                             "baseImponible": 5508})
    assert p["muebles"] == 14 and p["baseImponible"] == 3550.0, (
        "el área sigue usando `itemsCount` y `baseImponible` del pedido entero")


def test_UN_PEDIDO_SIN_SUS_LINEAS_NO_PAGA_Y_SE_MARCA():
    """Sin líneas no se puede saber qué era mueble.

    No se cuenta nada y se marca. Contar el pedido entero sería pagar de más —y
    pagar de más no se devuelve—; contar a ciegas y callarse sería peor todavía,
    porque nadie lo arreglaría nunca.
    """
    p = AC.normaliza_pedido({"id": "B", "confirmedAt": "2026-08-01",
                             "itemsCount": 33, "baseImponible": 5508})
    assert p["muebles"] == 0 and p["baseImponible"] == 0.0
    assert p["sinDesglose"] is True


def test_las_familias_sin_comision_SALEN_DE_LOS_DATOS_del_ERP():
    """No de una lista escrita a mano que se queda vieja el día que MV añada una
    familia de frentes."""
    f = C.FAMILIAS_SIN_COMISION
    for esperada in ("PUERTAS", "VITRINA", "COSTADOS_COLOR", "REGLETA_COLOR",
                     "LATERALES_COLOR", "TECHO_COLOR", "ELEMENTOS_LINEALES"):
        assert esperada in f, f"falta «{esperada}» entre las que no comisionan"
    for mueble in ("BAJO", "ALTO", "COLUMNA_DESPENSERO", "ALTO_VITRINA"):
        assert mueble not in f, f"«{mueble}» ha dejado de comisionar y es un mueble"
