# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""CANDADO del control de cambios de proyecto.

Lo que se protege aqui es un calculo que acaba en una conversacion incomoda con
un cliente: "esto se cambio el dia tal, lo pidio fulano y costo tanto".

La trampa principal: confundir "no cambio" con "no se sabe". Si el total de
antes no existe, el impacto NO es 0 euros --- es desconocido. Escribir 0 ahi es
inventar una cifra, y encima la mas peligrosa, porque un 0 se lee como "esto no
costo nada" y nadie lo vuelve a mirar.

La segunda: quien PIDIO el cambio no se deduce de quien lo tecleo. El comercial
teclea lo que pide el cliente; dar por hecho que el autor es el solicitante
convertiria el historial en una coartada falsa.
"""
import importlib.util
import os

import pytest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture()
def cp():
    ruta = os.path.join(BACKEND, "services", "cambios_proyecto.py")
    spec = importlib.util.spec_from_file_location("_cambios_proyecto", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _p(pvp=None, coste=None, status="borrador", montada=0, despiece=0):
    return {
        "totalPvp": pvp, "totalCoste": coste, "status": status,
        "itemsMontada": [{"n": i} for i in range(montada)],
        "itemsDespiece": [{"n": i} for i in range(despiece)],
    }


# ─── El impacto se deriva, nunca se estima ──────────────────────────────────

def test_impacto_economico_es_la_resta_real(cp):
    r = cp.resumen_cambio(_p(pvp=18500), _p(pvp=19200))
    assert r["impactoPvp"] == 700.0
    assert r["pvpAntes"] == 18500 and r["pvpDespues"] == 19200


def test_sin_dato_anterior_el_impacto_es_DESCONOCIDO_no_cero(cp):
    """CANDADO: la trampa principal.

    Un 0 se lee como "no costo nada". Si no habia total antes, la respuesta
    honesta es None: no se sabe.
    """
    r = cp.resumen_cambio(_p(pvp=None, montada=1), _p(pvp=19200, montada=2))
    assert r["impactoPvp"] is None, "sin cifra de partida no se puede calcular impacto"
    assert r["impactoPvp"] != 0, "un impacto desconocido NO es un impacto de cero"


def test_texto_vacio_no_se_toma_como_cero(cp):
    r = cp.resumen_cambio(_p(pvp="", montada=1), _p(pvp=100, montada=2))
    assert r["impactoPvp"] is None


def test_una_bajada_de_precio_sale_en_negativo(cp):
    r = cp.resumen_cambio(_p(pvp=19200), _p(pvp=18500))
    assert r["impactoPvp"] == -700.0


# ─── Qué cuenta como cambio ─────────────────────────────────────────────────

def test_sin_cambios_no_ensucia_el_historial(cp):
    assert cp.resumen_cambio(_p(pvp=100, montada=2), _p(pvp=100, montada=2)) is None


def test_cambiar_lineas_sin_tocar_el_precio_SI_se_anota(cp):
    """Cambiar un acabado por otro del mismo precio es un cambio real: si no se
    anota, en obra aparece algo que nadie recuerda haber pedido."""
    r = cp.resumen_cambio(_p(pvp=100, montada=2), _p(pvp=100, montada=3))
    assert r is not None
    assert r["lineasNetas"] == 1
    assert r["impactoPvp"] == 0.0


def test_cuenta_lineas_de_montada_y_despiece(cp):
    r = cp.resumen_cambio(_p(pvp=1, montada=2, despiece=3), _p(pvp=1, montada=2, despiece=5))
    assert r["lineasAntes"] == 5 and r["lineasDespues"] == 7


# ─── Quién lo pidió no se adivina ───────────────────────────────────────────

def test_quien_lo_pidio_nace_vacio_aunque_haya_autor(cp):
    """CANDADO: el autor teclea; el solicitante puede ser otro. No se deduce."""
    r = cp.resumen_cambio(_p(pvp=100), _p(pvp=200), autor="maria")
    assert r["autor"] == "maria"
    assert r["pedidoPor"] is None, "el solicitante lo rellena una persona, no se infiere del autor"


# ─── Cuándo hace falta aprobación ───────────────────────────────────────────

@pytest.mark.parametrize("estado", ["aceptado", "entregado"])
def test_tocar_un_presupuesto_ya_aceptado_es_critico(cp, estado):
    r = cp.resumen_cambio(_p(pvp=100, status=estado), _p(pvp=200, status=estado))
    assert r["critico"] is True


@pytest.mark.parametrize("estado", ["borrador", "enviado", "rechazado"])
def test_retocar_un_borrador_no_bloquea_nada(cp, estado):
    """Si todo pidiera aprobación se aprobaría todo sin mirar, y el control
    dejaría de servir para lo que sirve."""
    r = cp.resumen_cambio(_p(pvp=100, status=estado), _p(pvp=200, status=estado))
    assert r["critico"] is False


def test_un_cambio_critico_nace_sin_aprobar(cp):
    r = cp.resumen_cambio(_p(pvp=100, status="aceptado"), _p(pvp=200, status="aceptado"))
    assert r["aprobadoPor"] is None and r["aprobadoAt"] is None


# ─── El bloqueo de fabricación (funcion #6) ─────────────────────────────────

def test_sin_cambios_pendientes_se_fabrica(cp):
    ok, motivo = cp.puede_fabricar({"cambios": []})
    assert ok is True and motivo == ""


def test_un_critico_sin_aprobar_bloquea(cp):
    proyecto = {"cambios": [
        {"critico": True, "aprobadoAt": None, "fecha": "2026-08-07T10:00:00", "impactoPvp": 700.0},
    ]}
    ok, motivo = cp.puede_fabricar(proyecto)
    assert ok is False
    assert "sin aprobar" in motivo
    assert "+700.00" in motivo, "el motivo tiene que decir CUANTO, no solo que hay un problema"


def test_una_vez_aprobado_deja_de_bloquear(cp):
    proyecto = {"cambios": [
        {"critico": True, "aprobadoAt": "2026-08-07T11:00:00", "aprobadoPor": "master",
         "fecha": "2026-08-07T10:00:00", "impactoPvp": 700.0},
    ]}
    ok, _ = cp.puede_fabricar(proyecto)
    assert ok is True


def test_los_no_criticos_nunca_bloquean(cp):
    proyecto = {"cambios": [{"critico": False, "aprobadoAt": None, "fecha": "2026-08-07"}]}
    assert cp.puede_fabricar(proyecto)[0] is True


def test_el_motivo_no_miente_cuando_falta_el_impacto(cp):
    """Si el impacto es desconocido, el motivo lo dice; no escribe '+0.00 €'."""
    proyecto = {"cambios": [
        {"critico": True, "aprobadoAt": None, "fecha": "2026-08-07T10:00:00", "impactoPvp": None},
    ]}
    ok, motivo = cp.puede_fabricar(proyecto)
    assert ok is False
    assert "sin calcular" in motivo and "0.00" not in motivo


def test_proyecto_sin_campo_cambios_no_revienta(cp):
    assert cp.puede_fabricar({})[0] is True
    assert cp.puede_fabricar(None)[0] is True


# ─── El bloqueo tiene que estar ENCHUFADO, no solo disponible ───────────────

def test_la_confirmacion_de_pedido_consulta_el_bloqueo():
    """CANDADO: `puede_fabricar` calculando bien no sirve de nada si nadie lo
    llama. Aqui se comprueba que la confirmacion de pedido --- que es donde
    nace la orden de fabricacion --- lo consulta de verdad.

    Si alguien quita el guardian, esta prueba se pone roja y hay que quitarla
    a proposito, dejando constancia.
    """
    ruta = os.path.join(BACKEND, "routes", "orders.py")
    with open(ruta, encoding="utf-8") as f:
        codigo = f.read()

    assert "from services.cambios_proyecto import puede_fabricar" in codigo, (
        "orders.py ya no importa el bloqueo de fabricacion"
    )
    assert "puede_fabricar(" in codigo, (
        "orders.py importa el bloqueo pero no lo llama: el guardian es de adorno"
    )
    # Y que corta de verdad, en vez de limitarse a avisar.
    assert "status_code=409" in codigo, (
        "el bloqueo tiene que RECHAZAR la confirmacion, no solo registrarla"
    )
