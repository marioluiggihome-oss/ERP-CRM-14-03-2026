# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
UN PEDIDO LO COBRAN DOS PERSONAS, Y CADA UNA SE LIQUIDA POR SU CUENTA.

Este candado nace de un fallo encontrado auditando, el 29/08. No daba ningún
error, no salía en ninguna prueba y costaba dinero de verdad.

La marca de «ya pagado» era UNA sola para el pedido entero (`liquidadoEn`), pero
del mismo pedido cobran el comercial (por tramos) y el montador (mano de obra
por mueble). Al cerrarle el mes a uno de los dos, el pedido quedaba marcado:

  · `POST /liquidar` del otro se lo saltaba para siempre, y
  · en el panel del otro la línea salía «liquidada» — o sea, se le decía que ya
    se le había pagado.

Un pedido de 7.000 € con 10 muebles son 400 € del comercial que no vuelve a ver
nadie. Y la comisión congelada YA iba por rol (regla 17 de CLAUDE.md): lo que
faltaba era que la marca de pagado hiciera lo mismo.

LO QUE SE VIGILA AQUÍ:
  1. Que pagarle a uno no deje sin cobrar al otro.
  2. Que a cada uno se le lea SU importe congelado, nunca el del compañero.
  3. Que los pedidos liquidados ANTES de este arreglo se sigan entendiendo, y
     que en la duda no se vuelva a pagar.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("JWT_SECRET", "secreto-de-pruebas-largo-y-aleatorio-0123456789")

import pytest  # noqa: E402

from services import liquidaciones as L  # noqa: E402


def pedido(**cambios):
    """Un pedido servido y cobrado del todo: 10 muebles, 7.000 € de base.

    Con esos números el comercial se lleva 40 €/mueble (tramo de 6.000 a 9.000)
    = 400 €, y el montador 17 €/mueble = 170 €.
    """
    base = {
        "id": "P1",
        "aceptadoAt": "2026-08-01",
        "servidoAt": "2026-08-10",
        "cobradoAt": "2026-08-05",
        "pendienteCobro": 0,
        "muebles": 10,
        "baseImponible": 7000.0,
        "manoPorMueble": 17.0,
    }
    base.update(cambios)
    return base


def _liquidado(p, rol, periodo="2026-08"):
    """El pedido tal como queda escrito después de `POST /liquidar` para ese rol."""
    congelada = L.congelar(p, rol, periodo)
    return dict(p,
                **{L.LIQUIDADO_POR_ROL[rol]: periodo,
                   L.CONGELADA_POR_ROL[rol]: congelada})


def test_PAGARLE_AL_MONTADOR_NO_DEJA_SIN_COBRAR_AL_COMERCIAL():
    """El fallo, tal cual. Son 400 € y no saltaba ningún error."""
    p = _liquidado(pedido(), L.MONTADOR)

    assert L.estado_de(p, L.MONTADOR) == L.LIQUIDADA
    assert L.estado_de(p, L.COMERCIAL) == L.CONSOLIDADA, (
        "al liquidarle el mes al montador, la comisión del comercial se ha dado "
        "por pagada. En pantalla le dice «liquidada» y `POST /liquidar` se la "
        "salta: no la cobra nunca")

    del_mes = L.liquidacion_del_mes([p], L.COMERCIAL, "2026-08")
    assert del_mes["euros"] == 400.0, (
        "el comercial se ha quedado fuera de la liquidación de su propio pedido")
    assert L.liquidado_en(p, L.COMERCIAL) is None
    assert L.liquidado_en(p, L.MONTADOR) == "2026-08"


def test_y_al_reves_pagarle_al_comercial_no_deja_sin_cobrar_al_montador():
    p = _liquidado(pedido(), L.COMERCIAL)
    assert L.estado_de(p, L.COMERCIAL) == L.LIQUIDADA
    assert L.estado_de(p, L.MONTADOR) == L.CONSOLIDADA
    assert L.liquidacion_del_mes([p], L.MONTADOR, "2026-08")["euros"] == 170.0


def test_cada_uno_lee_SU_congelada_y_nunca_la_del_companero():
    """Leer la del otro es pagarle lo que no es suyo (CLAUDE.md, regla 17)."""
    p = _liquidado(pedido(), L.MONTADOR)          # 170 € congelados, rol montador
    l_com = L.linea(p, L.COMERCIAL)
    assert l_com["euros"] == 400.0, (
        "el comercial está cobrando los euros congelados del montador")
    assert l_com["congelada"] is False
    l_mon = L.linea(p, L.MONTADOR)
    assert (l_mon["euros"], l_mon["congelada"]) == (170.0, True)


def test_los_dos_liquidados_es_lo_normal_al_cerrar_el_mes():
    p = _liquidado(_liquidado(pedido(), L.MONTADOR), L.COMERCIAL)
    assert L.estado_de(p, L.COMERCIAL) == L.LIQUIDADA
    assert L.estado_de(p, L.MONTADOR) == L.LIQUIDADA
    assert L.linea(p, L.COMERCIAL)["euros"] == 400.0
    assert L.linea(p, L.MONTADOR)["euros"] == 170.0
    for rol in (L.COMERCIAL, L.MONTADOR):
        assert L.liquidacion_del_mes([p], rol, "2026-08")["euros"] == 0.0, (
            "un pedido ya liquidado vuelve a entrar en la liquidación del mes")


def test_UNA_COMISION_CONGELADA_NO_SE_MUEVE_aunque_cambie_la_mano_de_obra():
    """La razón de ser del congelado: la nómina de agosto tiene que seguir
    cuadrando con lo que se pagó en agosto."""
    p = _liquidado(pedido(), L.MONTADOR)
    p["manoPorMueble"] = 30.0                     # el master le sube la mano hoy
    assert L.linea(p, L.MONTADOR)["euros"] == 170.0, (
        "cambiar la mano de obra de un montador ha movido hacia atrás una "
        "liquidación ya pagada")


# ─── Lo de antes del arreglo ────────────────────────────────────────────────

def test_UN_PEDIDO_LIQUIDADO_ANTES_se_sigue_entendiendo():
    """Los pedidos ya cerrados traen `liquidadoEn` + `comisionCongelada`, y el
    `rol` que lleva el congelado dentro dice de quién era."""
    congelada = L.congelar(pedido(), L.MONTADOR, "2026-08")
    p = dict(pedido(), liquidadoEn="2026-08", comisionCongelada=congelada)

    assert L.estado_de(p, L.MONTADOR) == L.LIQUIDADA
    assert L.linea(p, L.MONTADOR)["congelada"] is True
    assert L.estado_de(p, L.COMERCIAL) == L.CONSOLIDADA, (
        "un pedido viejo liquidado al montador sigue dejando sin cobrar al "
        "comercial: el legado no se está leyendo por rol")
    l_com = L.linea(p, L.COMERCIAL)
    assert (l_com["euros"], l_com["congelada"]) == (400.0, False), (
        "al comercial se le están dando por congelados los 170 € del montador: "
        "el importe ya pagado del compañero no es el suyo")


def test_UN_LEGADO_SIN_ROL_no_se_vuelve_a_pagar_a_nadie():
    """En la duda no se paga otra vez: pagar de menos se reclama, pagar de más
    no se devuelve. Aquí no se puede saber de quién era, así que vale para los
    dos."""
    p = dict(pedido(), liquidadoEn="2026-08")     # sin `comisionCongelada`
    assert L.estado_de(p, L.COMERCIAL) == L.LIQUIDADA
    assert L.estado_de(p, L.MONTADOR) == L.LIQUIDADA


def test_sin_rol_se_contesta_lo_conservador():
    p = _liquidado(pedido(), L.MONTADOR)
    assert L.estado_de(p) == L.LIQUIDADA, (
        "quien no dice de quién pregunta no puede recibir un «te queda por "
        "cobrar» que a lo mejor no es suyo")


def test_normaliza_sigue_siendo_IDEMPOTENTE():
    """Se llama siempre y se le pasa a veces su propia salida: si el legado se
    tradujera solo en la primera pasada, la segunda lo perdería."""
    congelada = L.congelar(pedido(), L.COMERCIAL, "2026-08")
    p = dict(pedido(), liquidadoEn="2026-08", comisionCongelada=congelada)
    una = L.normaliza(p)
    assert L.normaliza(una) == una


def test_un_rol_inventado_no_pasa_de_aqui():
    """Un rol mal escrito no puede acabar leyendo un `None` y pagando cero."""
    p = pedido()
    for llamada in (lambda: L.linea(p, "montadores"),
                    lambda: L.liquidado_en(p, ""),
                    lambda: L.congelada_de(p, "jefe")):
        with pytest.raises(ValueError):
            llamada()
