# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
QUÉ PEDIDO SE HA SERVIDO Y CUÁL SE HA COBRADO, SEGÚN SUS DOCUMENTOS.

La liquidación esperaba `servidoAt` y `cobradoAt` en el pedido, y no los escribía
nadie: NINGÚN pedido consolidaba jamás. El ERP sí lo sabe, pero en Gestión
Comercial — el ALBARÁN dice que la mercancía salió y la FACTURA pagada dice que
el dinero entró.

LO QUE NO PUEDE PASAR AQUÍ, Y ES TODO LO MISMO: QUE UN PEDIDO COBRE POR LOS
DOCUMENTOS DE OTRO. Dos pedidos del mismo cliente por el mismo importe son cosa
de todos los días. Por eso se ata por `projectId` y `budgetNumber` —las
referencias que el propio gestor guarda— y por nada más. Un pedido sin
referencia se queda sin servir: mejor que no cobre todavía a que cobre por el
albarán del vecino. Pagar de menos se reclama; pagar de más no se devuelve.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("JWT_SECRET", "secreto-de-pruebas-largo-y-aleatorio-0123456789")

from services import enlace_documentos as ED  # noqa: E402
from services import liquidaciones as L        # noqa: E402

PEDIDO = {"id": "PED-1", "budgetNumber": "PRE-2026-0001",
          "aceptadoAt": "2026-07-20", "muebles": 10, "manoPorMueble": 17.0}

ALBARAN = {"docType": "albaran", "budgetNumber": "PRE-2026-0001",
           "issueDate": "2026-08-12"}
FACTURA_PAGADA = {"docType": "factura", "budgetNumber": "PRE-2026-0001",
                  "issueDate": "2026-08-13", "status": "paid",
                  "paidAt": "2026-08-14", "total": 7000.0}


def test_el_ALBARAN_es_lo_que_dice_que_la_mercancia_salio():
    p = ED.enriquecer(PEDIDO, ED.indexar([ALBARAN]))
    assert p["servidoAt"] == "2026-08-12"


def test_la_FACTURA_PAGADA_es_lo_que_dice_que_el_dinero_entro():
    p = ED.enriquecer(PEDIDO, ED.indexar([ALBARAN, FACTURA_PAGADA]))
    assert p["cobradoAt"] == "2026-08-14"
    assert p["pendienteCobro"] == 0
    assert L.estado_de(p) == L.CONSOLIDADA, (
        "con su albarán y su factura pagada, el pedido tiene que consolidar")
    assert L.periodo_de_consolidacion(p) == "2026-08", (
        "el mes es el de la ENTREGA, no el del cobro (master)")


def test_una_factura_SIN_PAGAR_no_libera_nada():
    sin_pagar = dict(FACTURA_PAGADA, status="issued", paidAt=None)
    p = ED.enriquecer(PEDIDO, ED.indexar([ALBARAN, sin_pagar]))
    assert p.get("cobradoAt") is None
    assert p["pendienteCobro"] == 7000.0
    assert L.estado_de(p) == L.EN_PROGRESO
    assert L.es_anomalia(p) is True, (
        "mercancía servida y sin cobrar tiene que salir marcada: la norma de la "
        "casa dice que no puede pasar, pero la teclean personas")


def test_UNA_FACTURA_PAGADA_Y_OTRA_NO_es_un_pedido_a_medio_cobrar():
    """Lo que de verdad se escapa: dos facturas del mismo pedido.

    Si bastara con que hubiera UNA pagada, se liberaría la comisión con la
    mitad del dinero fuera.
    """
    otra = dict(FACTURA_PAGADA, status="issued", paidAt=None, total=3000.0)
    p = ED.enriquecer(PEDIDO, ED.indexar([ALBARAN, FACTURA_PAGADA, otra]))
    assert p.get("cobradoAt") is None, (
        "se ha dado por cobrado un pedido con una factura sin pagar")
    assert p["pendienteCobro"] == 3000.0
    assert L.estado_de(p) == L.EN_PROGRESO


def test_un_pedido_SIN_REFERENCIA_no_hereda_los_documentos_de_nadie():
    """Es el fallo caro: atribuirle a un pedido el albarán de otro."""
    huerfano = {"id": "PED-X", "aceptadoAt": "2026-07-20", "muebles": 10,
                "manoPorMueble": 17.0}
    p = ED.enriquecer(huerfano, ED.indexar([ALBARAN, FACTURA_PAGADA]))
    assert p.get("servidoAt") is None, (
        "un pedido sin referencia se ha quedado con el albarán de otro pedido")
    assert p.get("cobradoAt") is None
    assert L.estado_de(p) == L.EN_PROGRESO


def test_los_documentos_de_OTRO_pedido_no_se_mezclan():
    otro_albaran = dict(ALBARAN, budgetNumber="PRE-2026-0999")
    p = ED.enriquecer(PEDIDO, ED.indexar([otro_albaran]))
    assert p.get("servidoAt") is None, (
        "el albarán de PRE-2026-0999 se le ha atribuido a PRE-2026-0001")


def test_se_ata_TAMBIEN_por_projectId():
    """Las dos referencias que guarda el gestor, no solo una."""
    pedido = {"id": "PED-2", "projectId": "proj-7", "aceptadoAt": "2026-07-01",
              "muebles": 5, "manoPorMueble": 17.0}
    alb = {"docType": "albaran", "projectId": "proj-7", "issueDate": "2026-08-03"}
    p = ED.enriquecer(pedido, ED.indexar([alb]))
    assert p["servidoAt"] == "2026-08-03"


def test_LO_QUE_YA_TRAE_EL_PEDIDO_manda_sobre_el_documento():
    """Si alguien estampó la fecha a mano, esa es la buena. El documento es la
    fuente cuando no hay otra, no una corrección de lo ya decidido."""
    p = ED.enriquecer(dict(PEDIDO, servidoAt="2026-07-01"), ED.indexar([ALBARAN]))
    assert p["servidoAt"] == "2026-07-01"


def test_con_VARIAS_ENTREGAS_manda_la_ultima():
    """La mercancía no está fuera del todo hasta el último albarán. Con el
    primero, la comisión se pagaría un mes antes de tiempo."""
    primero = dict(ALBARAN, issueDate="2026-07-30")
    ultimo = dict(ALBARAN, issueDate="2026-08-12")
    p = ED.enriquecer(PEDIDO, ED.indexar([primero, ultimo]))
    assert p["servidoAt"] == "2026-08-12"
    assert L.periodo_de(p["servidoAt"]) == "2026-08", (
        "con el albarán equivocado la comisión se liquidaría en julio")


def test_no_revienta_con_documentos_absurdos():
    for basura in (None, [], [{}], [{"docType": "albaran"}], [{"budgetNumber": ""}]):
        p = ED.enriquecer(PEDIDO, ED.indexar(basura))
        assert p["id"] == "PED-1"
