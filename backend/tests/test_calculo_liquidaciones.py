# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
CUÁNDO COBRA UN COOPERATIVISTA. ESTO ES NÓMINA.

Las reglas las dictó el master el 25/08/2026:

    «las liquidaciones de comisiones se liquidan una vez al mes»

    «tanto el cooperativista comercial como el cooperativista montador ven los
    euros que van en progreso al irse aceptando los pedidos pero no se liberan
    hasta que no están totalmente servidos los pedidos y cobrados»

Tres cosas no pueden pasar NUNCA, y cada una tiene su prueba:

  · Pagar dos veces el mismo pedido.
  · Pagar por dinero que no ha entrado (servido pero sin cobrar, o cobrado a
    medias).
  · Que un pedido caído siga contando.

Y una cuarta que es la que se rompe sola: que «en progreso» y «consolidada» se
sumen en un único número. Son promesas de distinto valor.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("JWT_SECRET", "secreto-de-pruebas-largo-y-aleatorio-0123456789")

from services import liquidaciones as L  # noqa: E402


def pedido(**kw):
    """Un pedido aceptado, de 10 muebles, 13.000 € de base -> tramo de 60 €."""
    base = {
        "id": "PED-1",
        "aceptadoAt": "2026-08-01",
        "servidoAt": None,
        "cobradoAt": None,
        "pendienteCobro": 0.0,
        "muebles": 10,
        "baseImponible": 13000.0,
        "manoPorMueble": 20.0,
    }
    base.update(kw)
    return base


# ── Los tres estados ─────────────────────────────────────────────────────────
def test_un_pedido_aceptado_esta_EN_PROGRESO():
    """Se ve, pero no es suyo. Para eso está el plan de estimulación."""
    assert L.estado_de(pedido()) == L.EN_PROGRESO


def test_servido_Y_cobrado_lo_CONSOLIDA():
    p = pedido(servidoAt="2026-08-10", cobradoAt="2026-08-20", pendienteCobro=0)
    assert L.estado_de(p) == L.CONSOLIDADA


def test_lo_ya_liquidado_se_queda_LIQUIDADO():
    p = pedido(servidoAt="2026-08-10", cobradoAt="2026-08-20", liquidadoEn="2026-08")
    assert L.estado_de(p) == L.LIQUIDADA


# ── Las dos condiciones son una «Y» ──────────────────────────────────────────
def test_SERVIDO_PERO_SIN_COBRAR_no_libera_nada():
    """El material puesto y el dinero fuera. El master: «servidos Y cobrados»."""
    p = pedido(servidoAt="2026-08-10", cobradoAt=None)
    assert L.estado_de(p) == L.EN_PROGRESO, (
        "se ha liberado una comisión de un pedido servido pero sin cobrar: se "
        "estaría pagando con dinero que no ha entrado")


def test_COBRADO_PERO_SIN_SERVIR_tampoco():
    """Un anticipo no es un pedido terminado."""
    p = pedido(servidoAt=None, cobradoAt="2026-08-20")
    assert L.estado_de(p) == L.EN_PROGRESO


def test_COBRADO_A_MEDIAS_no_es_cobrado():
    """Este ERP lleva cobros a cuenta: un pedido puede estar al 90%.

    Mientras quede un euro pendiente la comisión no se libera. Si esta prueba se
    pone roja, se estaría liquidando sobre cobros parciales.
    """
    p = pedido(servidoAt="2026-08-10", cobradoAt="2026-08-20", pendienteCobro=1.0)
    assert L.estado_de(p) == L.EN_PROGRESO


def test_medio_centimo_pendiente_SI_es_cobrado():
    """Eso es redondeo, no deuda. Si no, un céntimo de descuadre dejaría a un
    cooperativista sin cobrar su comisión para siempre."""
    p = pedido(servidoAt="2026-08-10", cobradoAt="2026-08-20", pendienteCobro=0.004)
    assert L.estado_de(p) == L.CONSOLIDADA


# ── Lo que no cuenta ─────────────────────────────────────────────────────────
def test_un_pedido_SIN_ACEPTAR_no_cuenta_ni_en_progreso():
    assert L.estado_de(pedido(aceptadoAt=None)) is None


def test_un_pedido_ANULADO_desaparece():
    """Y devuelve None, no «cero euros»: una línea a cero en el panel del
    comercial es recordarle lo que no va a cobrar."""
    p = pedido(servidoAt="2026-08-10", cobradoAt="2026-08-20", anulado=True)
    assert L.estado_de(p) is None


def test_una_fecha_ILEGIBLE_no_libera():
    """Nunca inventar un dato (CLAUDE.md). Una fecha que no se entiende es «no
    se sabe», y sin saberlo no se paga."""
    p = pedido(servidoAt="mañana", cobradoAt="2026-08-20")
    assert L.estado_de(p) == L.EN_PROGRESO


# ── En qué mes cae ───────────────────────────────────────────────────────────
def test_cae_en_el_mes_de_la_ULTIMA_condicion():
    """Servido en julio, cobrado en agosto -> es de agosto. Antes de esa fecha
    no había nada que liquidar."""
    p = pedido(servidoAt="2026-07-30", cobradoAt="2026-08-02")
    assert L.periodo_de_consolidacion(p) == "2026-08"

    p2 = pedido(servidoAt="2026-09-03", cobradoAt="2026-08-28")
    assert L.periodo_de_consolidacion(p2) == "2026-09"


def test_lo_que_no_esta_consolidado_no_tiene_mes():
    assert L.periodo_de_consolidacion(pedido()) is None


# ── Los euros: los pone `comisiones.py`, aquí no se recalcula nada ───────────
def test_los_euros_salen_de_comisiones_y_no_de_una_copia():
    from services import comisiones as C
    p = pedido()
    assert L.euros_de(p, L.COMERCIAL) == C.comision_comercial(13000.0, 10)["total"]
    assert L.euros_de(p, L.MONTADOR) == C.comision_montadores(20.0, 10)["total"]
    # 13.000 € está en el tramo de 60 € (12.000–15.000), x10 muebles.
    assert L.euros_de(p, L.COMERCIAL) == 600.0
    assert L.euros_de(p, L.MONTADOR) == 200.0


def test_un_rol_desconocido_revienta_en_vez_de_pagar_cero():
    """Devolver 0 € sería peor: parecería que ese pedido no vale nada."""
    with pytest.raises(ValueError):
        L.euros_de(pedido(), "gerente")


# ── El panel ─────────────────────────────────────────────────────────────────
def test_el_panel_NO_suma_el_progreso_con_lo_consolidado():
    """La que se rompe sola. «En progreso» y «a cobrar» son promesas de distinto
    valor: en un solo número, el cooperativista leería como suyo un dinero que
    todavía se puede caer."""
    pedidos = [
        pedido(id="A"),
        pedido(id="B", servidoAt="2026-08-10", cobradoAt="2026-08-20"),
        pedido(id="C", servidoAt="2026-07-10", cobradoAt="2026-07-20",
               liquidadoEn="2026-07"),
    ]
    pan = L.panel(pedidos, L.COMERCIAL)
    assert pan["enProgreso"]["euros"] == 600.0
    assert pan["consolidada"]["euros"] == 600.0
    assert pan["liquidada"]["euros"] == 600.0
    assert "total" not in pan, (
        "el panel ofrece un total que mezcla los tres montones")


def test_el_panel_ignora_lo_que_no_cuenta():
    pedidos = [pedido(id="A"), pedido(id="X", anulado=True),
               pedido(id="Y", aceptadoAt=None)]
    pan = L.panel(pedidos, L.COMERCIAL)
    assert pan["enProgreso"]["pedidos"] == 1
    assert pan["consolidada"]["pedidos"] == 0


def test_el_panel_del_montador_usa_la_mano_de_obra():
    """Su comisión ES la mano de obra que ya se teclea (CLAUDE.md, regla 16).
    No tiene fórmula propia a propósito."""
    pan = L.panel([pedido(manoPorMueble=25.0)], L.MONTADOR)
    assert pan["enProgreso"]["euros"] == 250.0


# ── La liquidación del mes ───────────────────────────────────────────────────
def test_la_liquidacion_del_mes_solo_lleva_lo_CONSOLIDADO_de_ese_mes():
    pedidos = [
        pedido(id="A"),                                                    # en progreso
        pedido(id="B", servidoAt="2026-08-10", cobradoAt="2026-08-20"),    # agosto
        pedido(id="C", servidoAt="2026-07-10", cobradoAt="2026-07-20"),    # julio
    ]
    liq = L.liquidacion_del_mes(pedidos, L.COMERCIAL, "2026-08")
    assert [l["pedidoId"] for l in liq["lineas"]] == ["B"]
    assert liq["euros"] == 600.0
    assert liq["muebles"] == 10


def test_UN_PEDIDO_YA_LIQUIDADO_NO_VUELVE_A_ENTRAR():
    """La prueba que evita pagar dos veces, que es el fallo caro de verdad."""
    p = pedido(servidoAt="2026-08-10", cobradoAt="2026-08-20", liquidadoEn="2026-08")
    liq = L.liquidacion_del_mes([p], L.COMERCIAL, "2026-08")
    assert liq["pedidos"] == 0 and liq["euros"] == 0, (
        "un pedido ya liquidado vuelve a entrar en la liquidación del mes: se "
        "pagaría dos veces")


def test_lo_EN_PROGRESO_no_entra_por_mucho_que_se_vea_en_el_panel():
    liq = L.liquidacion_del_mes([pedido()], L.COMERCIAL, "2026-08")
    assert liq["euros"] == 0


def test_un_mes_sin_nada_da_cero_y_no_revienta():
    liq = L.liquidacion_del_mes([], L.MONTADOR, "2026-08")
    assert liq["euros"] == 0 and liq["pedidos"] == 0


# ── Basura ───────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("basura", [None, {}, {"id": "X"}, {"muebles": "dos"}])
def test_un_pedido_absurdo_no_revienta_ni_paga(basura):
    assert L.linea(basura, L.COMERCIAL) is None


def test_el_panel_aguanta_una_lista_vacia_o_nula():
    for entrada in ([], None):
        pan = L.panel(entrada, L.COMERCIAL)
        assert pan["enProgreso"]["euros"] == 0
