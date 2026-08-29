# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
UNA COMISIÓN PAGADA ES UN HECHO DEL PASADO, NO UNA FÓRMULA.

El 28/08 el master pidió poder ponerle a cada montador su mano de obra por
mueble. Eso abrió un agujero que antes no existía: las comisiones se calculaban
enteras cada vez que alguien abría la pantalla, así que el día que le cambiara
los 17 € a alguien cambiarían TAMBIÉN sus pedidos ya pagados de meses
anteriores. La liquidación de agosto dejaría de cuadrar con lo que se pagó en
agosto, sin que saltara ningún error: los dos números son plausibles.

Y al mirarlo apareció algo peor. `liquidadoEn` se leía en cinco sitios y NO LO
ESCRIBÍA NADIE, así que el estado LIQUIDADA no se alcanzaba nunca: la misma
comisión podía entrar en la liquidación de septiembre, la de octubre y la de
noviembre. «Liquidada = ya pagada, no vuelve a entrar nunca» (regla 17) era una
intención escrita, no una barrera.

Las dos mitades se arreglan en el mismo sitio: al cerrar el mes se guarda en el
pedido lo que se ha pagado por él, y a partir de ahí eso se LEE, no se calcula.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("JWT_SECRET", "secreto-de-pruebas-largo-y-aleatorio-0123456789")

from services import liquidaciones as L  # noqa: E402


def pedido(**kw):
    """Servido y cobrado en agosto: una comisión lista para liquidar."""
    base = {
        "id": "PED-1",
        "aceptadoAt": "2026-07-20",
        "servidoAt": "2026-08-12",
        "cobradoAt": "2026-08-14",
        "pendienteCobro": 0,
        "muebles": 10,
        "baseImponible": 7000.0,
        "manoPorMueble": 17.0,
    }
    base.update(kw)
    return base


def test_sin_congelar_la_comision_SE_MUEVE_al_cambiar_la_mano_de_obra():
    """El problema, enseñado antes de arreglarlo.

    Es el comportamiento de siempre y sigue siendo el correcto MIENTRAS no se
    haya pagado: lo que aún no es tuyo puede cambiar.
    """
    a = L.linea(pedido(manoPorMueble=17.0), L.MONTADOR)
    b = L.linea(pedido(manoPorMueble=25.0), L.MONTADOR)
    assert a["euros"] == 170.0 and b["euros"] == 250.0
    assert a["congelada"] is False


def test_UNA_VEZ_CONGELADA_ya_no_se_mueve_aunque_cambie_todo():
    """Lo que se pagó, se pagó.

    Se cambia la mano de obra a 25 €, se cambian los muebles y se cambia la
    base imponible — y siguen saliendo los 170 € que se pagaron.
    """
    congelada = L.congelar(pedido(), L.MONTADOR, "2026-08")
    p = pedido(manoPorMueble=25.0, muebles=40, baseImponible=99000.0,
               liquidadoEn="2026-08", comisionCongelada=congelada)
    l = L.linea(p, L.MONTADOR)
    assert l["euros"] == 170.0, (
        f"la comisión ya pagada se ha movido a {l['euros']} €: la nómina de "
        "agosto ya no cuadra con lo que se pagó en agosto")
    assert l["muebles"] == 10 and l["porMueble"] == 17.0
    assert l["congelada"] is True
    assert l["estado"] == L.LIQUIDADA


def test_lo_congelado_del_COMERCIAL_tampoco_se_mueve_si_cambia_la_escala():
    """El otro rol: si un día se toca la tabla de tramos, lo ya pagado se queda
    donde estaba. Un tramo nuevo no puede reescribir nóminas viejas."""
    congelada = L.congelar(pedido(), L.COMERCIAL, "2026-08")
    assert congelada["euros"] == 400.0, congelada   # 7.000 € -> 40 €/mueble x 10
    p = pedido(baseImponible=14000.0, liquidadoEn="2026-08",
               comisionCongelada=congelada)
    l = L.linea(p, L.COMERCIAL)
    assert l["euros"] == 400.0
    assert l["tramo"] == congelada["tramo"], (
        "el rótulo del tramo también se congela: si se recalculara, el recibo "
        "diría un tramo y el importe sería de otro")


def test_lo_congelado_de_UN_ROL_no_se_le_aplica_al_otro():
    """Un pedido lo cobran dos personas distintas, cada una lo suyo. Si el
    montador leyera la congelación del comercial, cobraría sus 400 €."""
    congelada = L.congelar(pedido(), L.COMERCIAL, "2026-08")
    p = pedido(liquidadoEn="2026-08", comisionCongelada=congelada)
    l = L.linea(p, L.MONTADOR)
    assert l["euros"] == 170.0, (
        f"el montador está cobrando {l['euros']} €, que es la comisión del "
        "comercial")
    assert l["congelada"] is False


def test_una_congelacion_CORRUPTA_no_borra_la_comision():
    """Si lo guardado no es un diccionario, se vuelve a calcular en vez de
    devolver cero. Un dato roto no puede dejar a nadie sin cobrar en silencio."""
    for basura in ("", [], "170", 0, None):
        l = L.linea(pedido(comisionCongelada=basura), L.MONTADOR)
        assert l["euros"] == 170.0, f"con {basura!r} la comisión se ha perdido"


def test_no_se_puede_congelar_un_pedido_que_NO_GENERA_comision():
    """Un pedido anulado o sin aceptar no tiene nada que congelar, y guardar un
    cero ahí lo convertiría en «pagado, 0 €» para siempre."""
    with pytest.raises(ValueError):
        L.congelar(pedido(anulado=True), L.MONTADOR, "2026-08")
    with pytest.raises(ValueError):
        L.congelar(pedido(aceptadoAt=None), L.MONTADOR, "2026-08")


def test_el_periodo_que_se_congela_es_el_de_LA_ENTREGA():
    """«Si se sirven en agosto se liquidan en agosto» (master). Se sirve el 12
    de agosto y se cobra el 14: agosto."""
    assert L.periodo_de_consolidacion(pedido()) == "2026-08"
    congelada = L.congelar(pedido(), L.MONTADOR, L.periodo_de_consolidacion(pedido()))
    assert congelada["periodo"] == "2026-08"


def test_se_leen_los_nombres_QUE_EL_ERP_YA_USA_para_entrega_y_cobro():
    """`projects.py` estampa `deliveredAt` al pasar a «entregado» e
    `invoices.py` estampa `paidAt` al pasar a «paid».

    Nadie escribía `servidoAt` ni `cobradoAt`, así que un pedido entregado y
    cobrado de verdad se quedaba en «en progreso» para siempre esperando a un
    campo que no le pone nadie.
    """
    p = {"id": "P", "aceptadoAt": "2026-07-01", "deliveredAt": "2026-08-12",
         "paidAt": "2026-08-14", "pendienteCobro": 0, "muebles": 10,
         "manoPorMueble": 17.0}
    assert L.estado_de(p) == L.CONSOLIDADA, (
        "un pedido entregado y cobrado con los nombres de campo que el ERP ya "
        "usa se queda sin consolidar")
    assert L.periodo_de_consolidacion(p) == "2026-08"


def test_un_cobro_A_CUENTA_sigue_sin_liberar_aunque_traiga_paidAt():
    """El nombre nuevo no puede saltarse la regla de siempre: cobrado es
    cobrado del TODO."""
    p = {"id": "P", "aceptadoAt": "2026-07-01", "deliveredAt": "2026-08-12",
         "paidAt": "2026-08-14", "pendienteCobro": 500.0, "muebles": 10,
         "manoPorMueble": 17.0}
    assert L.estado_de(p) == L.EN_PROGRESO
    assert L.es_anomalia(p) is True, (
        "mercancía fuera y dinero sin entrar tiene que salir marcado")


def test_la_ruta_de_liquidar_NO_PAGA_DOS_VECES_y_es_del_master():
    """Se comprueba en el fichero de rutas, no solo en la pantalla.

    Lo que hace falta: que sea del master, que solo pague lo CONSOLIDADO, que se
    salte lo que ese ROL ya tenga liquidado, que el `update` lleve la condición
    de no estar liquidado —para que dos pulsaciones a la vez no paguen dos
    veces— y que si el `update` no toca nada, ese pedido NO se cuente como
    pagado.
    """
    ruta = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "routes", "cooperativistas.py")
    with open(ruta, "r", encoding="utf-8") as f:
        cuerpo = f.read()
    i = cuerpo.index('@router.post("/liquidar")')
    j = cuerpo.index("@router", i + 10)
    trozo = cuerpo[i:j]

    assert "_es_master" in trozo, "liquidar no está cerrado al master"
    assert "L.CONSOLIDADA" in trozo, (
        "liquidar no comprueba que el pedido esté consolidado: pagaría comisiones "
        "de mercancía sin servir o sin cobrar")
    assert "L.liquidado_en(crudo, rol)" in trozo, (
        "liquidar no se salta lo que ESE ROL ya tiene liquidado: pagaría dos veces")
    assert 'clave_liquidado: {"$in": [None, ""]}' in trozo, (
        "el update no lleva la condición de no estar ya liquidado. Sin ella, dos "
        "pulsaciones seguidas pagan dos veces el mismo pedido")
    assert "L.LIQUIDADO_POR_ROL[rol]" in trozo and "L.CONGELADA_POR_ROL[rol]" in trozo, (
        "liquidar marca el pedido entero en vez de marcarlo POR ROL. De un pedido "
        "cobran el comercial y el montador: con una marca sola, al pagarle a uno "
        "el otro se queda sin cobrar para siempre")
    assert "if not tocados:" in trozo, (
        "liquidar cuenta como pagado un pedido cuyo update no ha tocado nada: el "
        "total del mes saldría duplicado")
    assert "L.congelar" in trozo, (
        "liquidar no congela: al mes siguiente el importe volvería a calcularse")
