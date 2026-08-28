# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
LO QUE TIENES A TIRO: EL MOTOR DEL PLAN DE ESTIMULACIÓN.

El master, 25/08/2026: «queremos un plan de estimulación continua, que cuando
accedan a su área puedan estar viendo lo que tienen que producir y los
beneficios que van a tener cuando lo produzcan».

No basta con enseñar lo ganado. Hay que enseñar lo que está a un paso: «a este
pedido le faltan 600 € para pasar de 50 a 60 € por mueble, y con sus 14 muebles
son 140 € más para ti».

EL FALLO QUE TUVO ESTO AL NACER, y que enseña cómo está hecha la tabla. Los
tramos son pares `(hasta, euros)`: «hasta ese importe se cobra eso». La primera
versión buscaba el `tope` del tramo SIGUIENTE, y por eso decía que a un pedido de
11.400 € le faltaban 3.600 € cuando le faltaban 600: se saltaba un escalón
entero. Un plan de estimulación que enseña la meta seis veces más lejos de lo
que está desanima, que es lo contrario de para lo que se hizo.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("JWT_SECRET", "secreto-de-pruebas-largo-y-aleatorio-0123456789")

from services import comisiones as C  # noqa: E402

falta = C.cuanto_falta_para_el_siguiente_tramo


@pytest.mark.parametrize("valoracion,faltan,hasta,nuevo", [
    (0,        2500.0,  2500.0,  30.0),
    (2400,      100.0,  2500.0,  30.0),
    (5900,      100.0,  6000.0,  40.0),
    (8000,     1000.0,  9000.0,  50.0),
    (11400,     600.0, 12000.0,  60.0),
    (11999.99,    0.01, 12000.0, 60.0),
    (14999,       1.0, 15000.0,  70.0),
])
def test_el_salto_es_AL_ESCALON_DE_AL_LADO_y_no_a_dos(valoracion, faltan, hasta, nuevo):
    g = falta(valoracion, 10)
    assert g, f"con {valoracion} € debería haber un tramo por delante"
    assert g["faltan"] == pytest.approx(faltan), (
        f"con {valoracion} € dice que faltan {g['faltan']} y faltan {faltan}. "
        "Se está saltando un escalón: la tabla es (hasta, euros), así que el "
        "umbral es el `hasta` del tramo ACTUAL, no el del siguiente.")
    assert g["hasta"] == hasta
    assert g["porMuebleSiSalta"] == nuevo


def test_EN_EL_TRAMO_MAS_ALTO_no_se_persigue_nada():
    """Enseñar un objetivo inalcanzable desmotiva en vez de estimular."""
    assert falta(15000, 10) is None
    assert falta(50000, 10) is None


def test_lo_que_se_gana_MULTIPLICA_POR_LOS_MUEBLES():
    """Regla 4 de CLAUDE.md: las unidades multiplican. Y es lo que convierte el
    dato en un motivo: «10 € más por mueble» no mueve a nadie; «140 € más», sí."""
    g = falta(11400, 14)
    assert g["extraPorMueble"] == 10.0
    assert g["extraTotal"] == 140.0
    assert falta(11400, 0)["extraTotal"] == 0.0


def test_el_gancho_CUADRA_con_lo_que_se_paga_de_verdad():
    """No puede ser una cuenta aparte: si el gancho promete 60 € y el cálculo
    paga otra cosa, el comercial persigue una cifra que no existe."""
    for v in (0, 2400, 5900, 8000, 11400, 14999):
        g = falta(v, 10)
        assert g["porMuebleAhora"] == C.euros_por_mueble_comercial(v)
        # Justo al llegar al umbral se cobra ya lo prometido.
        assert C.euros_por_mueble_comercial(g["hasta"]) == g["porMuebleSiSalta"]


@pytest.mark.parametrize("basura", [None, "", "x", -100])
def test_una_valoracion_absurda_no_revienta(basura):
    g = falta(basura, 3)
    assert g is None or g["faltan"] >= 0


# ── UN PEDIDO ES UN PEDIDO. NO SE JUNTAN. ────────────────────────────────────
#
# El master, 25/08/2026: «hay que tener en cuenta que eso que falte en cada
# pedido tiene que ser en ESE pedido; no se pueden juntar dos pedidos».
#
# Ya se comportaba así, pero se amarra porque «enseñar cuánto falta EN TOTAL
# para el siguiente tramo» es exactamente la clase de mejora que alguien añade
# con buena intención — y sumando dos pedidos de 7.000 € el comercial vería un
# tramo de 60 €/mueble que no va a cobrar nunca. Prometer una comisión que no
# llega es peor que no prometer nada.

def _panel(pedidos):
    from services.area_cooperativista import panel_de
    # Socio comercial: el rol genérico `isRepresentative` ya no basta (master,
    # 27/08 — el comercial en nómina no cobra comisión).
    return panel_de({"id": "u1", "esCooperativistaComercial": True}, pedidos)


def _ped(pid, base, muebles):
    """Con sus LÍNEAS: la comisión se calcula de ellas, no del pedido entero.
    Solo muebles, para que el importe del pedido sea el que comisiona."""
    return {"id": pid, "confirmedAt": "2026-08-01",
            "items": [{"familia": "BAJO", "qty": muebles,
                       "pvp": round(base / muebles, 6)}]}


def test_DOS_PEDIDOS_NO_SE_SUMAN_PARA_SUBIR_DE_TRAMO():
    """Dos de 7.000 € pagan 40 €/mueble cada uno, no los 60 de un 14.000."""
    pan = _panel([_ped("A", 7000, 10), _ped("B", 7000, 10)])
    lineas = pan["enProgreso"]["lineas"]
    assert [l["porMueble"] for l in lineas] == [40.0, 40.0], (
        f"los pedidos se están valorando juntos: {[l['porMueble'] for l in lineas]}. "
        "Cada pedido se tarifa por SU base imponible.")
    assert pan["enProgreso"]["euros"] == 800.0, (
        "el total no es la suma de cada pedido valorado por separado")


def test_EL_GANCHO_ES_DE_CADA_PEDIDO_por_separado():
    """A cada uno le faltan 2.000 € LOS SUYOS. No 'os faltan 2.000 entre los
    dos', que es lo que saldría si se agregaran."""
    pan = _panel([_ped("A", 7000, 10), _ped("B", 7000, 10)])
    a_tiro = pan["aTiro"]
    assert len(a_tiro) == 2, "el gancho ha dejado de ser por pedido"
    for t in a_tiro:
        assert t["faltan"] == 2000.0
        assert t["porMuebleSiSalta"] == 50.0
    assert all("pedidoId" in t for t in a_tiro), (
        "una línea del gancho sin pedido detrás es un objetivo abstracto: hay "
        "que poder decirle A QUÉ pedido empujar")


def test_el_gancho_NO_TRAE_NINGUNA_LINEA_AGREGADA():
    """Un `aTiro` con alguna línea sin pedido detrás sería una fila «total»
    colada por la puerta de atrás.

    OJO CON LOS DATOS DE ESTA PRUEBA. La primera versión usaba pedidos que
    sumaban 26.000 €, o sea ya en el tramo más alto: una fila agregada ni
    siquiera se habría creado, así que la prueba no ejercía el caso que dice
    vigilar. Se comprobó rompiéndolo —añadiendo la fila «total»— y esta prueba
    siguió en verde. Ahora los importes suman 10.000 €, que está a mitad de
    escala y por tanto SÍ tiene un tramo por delante que agregar.
    """
    pedidos = [_ped("A", 7000, 10), _ped("B", 3000, 4)]
    # La suma se calcula COMO LA CALCULA EL CÓDIGO —de las líneas—, no leyendo
    # un campo del pedido: desde el 25/08 ese campo ya no existe, y leerlo
    # rompía la prueba sin que hubiera nada roto.
    from services import area_cooperativista as _AC
    suma = sum(_AC.normaliza_pedido(p)["baseImponible"] for p in pedidos)
    assert suma == 10000, (
        f"los importes de esta prueba suman {suma}; si caen en el tramo más "
        "alto, la fila agregada no se crearía y esto dejaría de probar nada")
    pan = _panel(pedidos)
    ids = [t["pedidoId"] for t in pan["aTiro"]]
    assert all(i in ("A", "B") for i in ids), (
        f"hay líneas que no son de un pedido: {ids}. Una fila «total» junta "
        "pedidos y promete un tramo que no se va a cobrar.")
    assert len(pan["aTiro"]) <= len(pedidos)


def test_un_pedido_YA_EN_EL_TRAMO_MAS_ALTO_no_se_persigue():
    pan = _panel([_ped("A", 7000, 10), _ped("C", 16000, 8)])
    assert "C" not in [t["pedidoId"] for t in pan["aTiro"]]


def test_juntar_los_pedidos_DARIA_OTRA_COSA_y_por_eso_no_se_hace():
    """Se deja escrito el número exacto de lo que NO se hace, para que quien
    lea esto sepa cuánto se estaría inflando si alguien agregara."""
    from services import comisiones as C
    juntos = C.comision_comercial(14000, 20)["total"]      # 60 x 20
    separados = (C.comision_comercial(7000, 10)["total"]
                 + C.comision_comercial(7000, 10)["total"])  # 40 x 10 dos veces
    assert juntos == 1200.0 and separados == 800.0
    assert _panel([_ped("A", 7000, 10), _ped("B", 7000, 10)])["enProgreso"]["euros"] == separados
