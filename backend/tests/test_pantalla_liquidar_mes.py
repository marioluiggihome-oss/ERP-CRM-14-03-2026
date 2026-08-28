# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
LA PANTALLA DE CERRAR EL MES: LA ÚNICA QUE COMPROMETE DINERO DE VERDAD.

Lo que hace no se deshace: al cerrar, cada pedido queda marcado como liquidado y
con su importe congelado dentro. Por eso esta pantalla tiene obligaciones que
ninguna otra tiene.

Y una que se rompe sola: LA CLAVE DEL IMPORTE. El backend devuelve `euros` y la
primera versión de la pantalla leía `total`, así que enseñaba 0 € y el botón se
quedaba deshabilitado para siempre — sin ningún error en consola, sin build
roto, sin nada. Se cazó leyendo la respuesta del backend en vez de suponerla.
"""
import os
import re

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSX = os.path.join(RAIZ, "frontend", "src", "components", "LiquidarMes.jsx")
APP = os.path.join(RAIZ, "frontend", "src", "App.js")


def _lee(ruta=JSX):
    with open(ruta, "r", encoding="utf-8") as f:
        return f.read()


def test_la_pantalla_lee_LA_CLAVE_QUE_DEVUELVE_EL_BACKEND():
    """`liquidacion_del_mes` devuelve `euros`. Si la pantalla lee `total`,
    enseña 0 € y el botón no se puede pulsar: la liquidación entera queda
    muerta sin que salte un solo error."""
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.environ.setdefault("JWT_SECRET", "secreto-de-pruebas-largo-y-aleatorio-0123456789")
    from services import liquidaciones as L

    resumen = L.liquidacion_del_mes([], L.MONTADOR, "2026-08")
    assert "euros" in resumen and "total" not in resumen, (
        "ha cambiado la forma de la respuesta; esta prueba hay que rehacerla")

    cuerpo = _lee()
    assert "detalle.euros" in cuerpo or "detalle?.euros" in cuerpo, (
        "la pantalla no lee `euros`, que es lo que devuelve el backend")
    assert not re.search(r"detalle\??\.total\b", cuerpo), (
        "la pantalla lee `detalle.total`, que el backend NO devuelve: enseñaría "
        "0 € y el botón se quedaría deshabilitado para siempre")


def test_se_AVISA_de_que_no_se_deshace_antes_de_pulsar():
    """Congelar es definitivo. Una pantalla que compromete nómina sin decirlo
    convierte un clic de más en un pago que no se puede retirar."""
    cuerpo = _lee()
    assert "window.confirm" in cuerpo, (
        "se cierra el mes sin pedir confirmación")
    assert "congelad" in cuerpo, (
        "no se dice en ninguna parte que los importes quedan congelados")
    assert "No se deshace" in cuerpo


def test_el_boton_se_BLOQUEA_mientras_trabaja():
    """El servidor ya es idempotente, pero que la barrera esté en el servidor no
    es excusa para dejar una trampa en la pantalla."""
    cuerpo = _lee()
    assert "disabled={liquidando" in cuerpo, (
        "el botón de cerrar el mes se puede pulsar dos veces seguidas")


def test_estan_LOS_TRES_FILTROS_que_pidio_el_master():
    """«Que se pueda filtrar por documento, por usuario, etcétera» (28/08)."""
    cuerpo = _lee()
    for testid in ("liquidar-filtro-rol", "liquidar-filtro-usuario",
                   "liquidar-filtro-periodo"):
        assert testid in cuerpo, f"falta el filtro «{testid}»"


def test_el_NOMBRE_DEL_MES_se_deriva_y_no_se_escribe_a_mano():
    """Un rótulo escrito a mano al lado de un importe acaba mintiendo, y aquí el
    importe es una nómina. Es el mismo fallo que ya tuvo el rótulo del tramo."""
    cuerpo = _lee()
    assert "nombreDelPeriodo" in cuerpo
    assert cuerpo.count("'agosto'") <= 1, (
        "hay meses escritos a mano fuera de la tabla que los deriva")


def test_las_ANOMALIAS_se_enseñan_antes_de_pagar():
    """`liquidaciones.es_anomalia` marca la mercancía que salió sin cobrar. Que
    el motor lo marque no sirve de nada si quien paga no lo ve."""
    cuerpo = _lee()
    assert "anomalia" in cuerpo and "sin estar cobrado" in cuerpo


def test_la_pantalla_SE_ABRE_y_solo_para_el_master():
    cuerpo = _lee(APP)
    assert "LiquidarMes" in cuerpo, "la pantalla no se importa: no hay forma de abrirla"
    assert "liquidar-nav-btn" in cuerpo, "no hay botón en la barra"
    # Se busca el sitio que PINTA la pantalla, no el que colorea el botón: la
    # primera aparición de `currentTab === 'liquidar'` es la del `className`,
    # y comprobar esa dejaría pasar una pestaña abierta de par en par.
    m = re.search(r"\{state\.currentTab === 'liquidar' &&([^\n]*)", cuerpo)
    assert m, "no se pinta la pestaña de liquidar en ninguna parte"
    assert "isMaster" in m.group(1), (
        f"la pestaña de liquidar no está cerrada al master: {m.group(1)[:120]}")
