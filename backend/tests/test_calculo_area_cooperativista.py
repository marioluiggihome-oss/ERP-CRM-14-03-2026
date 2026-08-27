# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
QUIÉN VE QUÉ EN EL ÁREA DEL COOPERATIVISTA. ESTO ES NÓMINA Y ES PRIVACIDAD.

El master, 25/08/2026: que un montador y un comercial puedan entrar con su clave
y ver lo suyo, dentro del plan de estimulación continua.

LAS DOS COSAS QUE NO PUEDEN PASAR NUNCA:

  1. QUE UNO VEA LO DEL OTRO. Ver lo que cobra un compañero no es un fallo de
     permisos: es un problema entre personas, y no se arregla con un parche.

  2. QUE LA COMISIÓN ABRA LA PUERTA AL DINERO DE LA CASA. Es el riesgo de
     verdad. Para calcular la comisión hace falta la base imponible del pedido,
     y de ahí a enseñar el coste, el margen o la tarifa MV hay un paso. El ERP
     tiene eso cerrado al master EN EL SERVIDOR (CLAUDE.md, 8b y 9), y una
     pantalla nueva no puede ser la puerta de atrás. La regla del proyecto vale
     igual aquí: un candado que se rodea por otra ruta no es un candado.

Y una tercera, de diseño: EL FILTRO SALE DEL TOKEN, NUNCA DE LA PETICIÓN. Si el
«de quién son los pedidos» viajara en la URL, cualquiera cambiaría el número. Es
el mismo fallo que tenía el motor de render antes del 25/08 —la pantalla ofrecía
lo correcto y la API se fiaba de lo que le mandaran—, y se cierra igual.
"""
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("JWT_SECRET", "secreto-de-pruebas-largo-y-aleatorio-0123456789")

from services import area_cooperativista as AC  # noqa: E402

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA = os.path.join(RAIZ, "routes", "cooperativistas.py")

MONTADOR = {"id": "u-mon", "isMontador": True}
COMERCIAL = {"id": "u-com", "isRepresentative": True}
GERENTE = {"id": "u-ger", "isGerente": True}


def pedido(muebles=10, valor=13000.0, **kw):
    """Un pedido CON SUS LÍNEAS.

    Desde el 25/08 la comisión se calcula de las líneas y no de `itemsCount` /
    `baseImponible` del pedido entero, porque puertas, costados y servicios no
    incentivan. Estas fixtures traían el pedido sin líneas y por eso daban cero:
    no era un fallo del código, era la prueba fabricando un pedido que ya no
    existe.
    """
    base = {"id": "PED-1", "confirmedAt": "2026-08-01",
            "items": [{"familia": "BAJO", "qty": muebles,
                       "pvp": round(valor / muebles, 6)}],
            "servidoAt": None, "cobradoAt": None, "pendienteCobro": 0}
    base.update(kw)
    return base


# ── Quién es cooperativista ──────────────────────────────────────────────────
def test_solo_montadores_y_comerciales_tienen_area():
    assert AC.rol_de(MONTADOR) == AC.MONTADOR
    assert AC.rol_de(COMERCIAL) == AC.COMERCIAL
    assert AC.rol_de(GERENTE) is None
    assert AC.rol_de({"id": "x"}) is None
    assert AC.rol_de(None) is None


def test_el_que_NO_es_cooperativista_no_tiene_area_NI_filtro():
    """`None` y no un panel vacío: un panel a cero invita a preguntarse por qué
    está vacío, y además dejaría la estructura a la vista."""
    assert AC.filtro_de(GERENTE) is None
    assert AC.panel_de(GERENTE, [pedido()]) is None


def test_UN_FILTRO_NULO_NO_PUEDE_CONFUNDIRSE_CON_UNO_VACIO():
    """El fallo que dejaría la casa abierta.

    `filtro_de` devuelve `None` cuando el usuario no es cooperativista. Si quien
    llama lo tomara por «sin filtro» y lo pasara a Mongo como `{}`, la consulta
    devolvería TODOS los pedidos de la casa. Por eso es `None` y no `{}`, y por
    eso la ruta lo comprueba antes de tocar la base de datos.
    """
    assert AC.filtro_de(GERENTE) is None
    assert AC.filtro_de(GERENTE) != {}


# ── Cada uno lo suyo ─────────────────────────────────────────────────────────
def test_el_filtro_ATA_los_pedidos_al_usuario_del_token():
    assert AC.filtro_de(COMERCIAL) == {"comercialUserId": "u-com"}
    assert AC.filtro_de(MONTADOR) == {"montadorUserId": "u-mon"}


def test_el_filtro_NO_SALE_DE_LA_PETICION():
    """Se lee la ruta: el filtro tiene que construirse desde `current_user`."""
    with open(RUTA, "r", encoding="utf-8") as f:
        cuerpo = f.read()
    i = cuerpo.index("async def mi_area")
    trozo = cuerpo[i:i + 700]
    assert "AC.filtro_de(current_user)" in trozo, (
        "el área ya no filtra por el usuario del token")
    assert not re.search(r"async def mi_area\([^)]*\busuario\b", cuerpo), (
        "`mi-area` acepta un usuario por parámetro: cualquiera cambiaría el "
        "número y vería la nómina del compañero")


def test_asignar_quien_cobra_es_SOLO_del_master():
    with open(RUTA, "r", encoding="utf-8") as f:
        cuerpo = f.read()
    for fn in ("async def asignar", "async def liquidacion"):
        i = cuerpo.index(fn)
        trozo = cuerpo[i:i + 500]
        assert "_es_master(current_user)" in trozo, (
            f"«{fn}» no está cerrada al master. Cambiar el comercial de un "
            "pedido es mover una comisión de un bolsillo a otro.")


# ── El dinero de la casa no sale ─────────────────────────────────────────────
PROHIBIDOS = ("coste", "margen", "pvp", "baseImponible", "tarifa", "puntos",
              "descuento", "escandallo", "totalAmount", "valorPunto")


def test_EL_PANEL_NO_LLEVA_NI_UN_DATO_DEL_DINERO_DE_LA_CASA(monkeypatch):
    """El candado importante, y estuvo A PUNTO DE NO SERLO.

    La primera versión pasaba por el motivo equivocado: `liquidaciones.linea()`
    hoy no produce ningún campo prohibido, así que el recorte del panel NUNCA se
    ejercía. Se comprobó rompiéndolo —quitando el recorte entero— y la prueba
    seguía en verde. Una prueba que pasa porque el peligro no ha llegado todavía
    no protege de nada: protege el día que llegue, y ese día ya no está.

    Así que aquí se OBLIGA a que llegue: se hace que la capa de abajo devuelva
    los campos del dinero, y se comprueba que el panel los corta igual.
    """
    import json
    from services import liquidaciones as _L

    original = _L.linea

    def linea_con_dinero(p, rol):
        l = original(p, rol)
        if l:
            l.update({"baseImponible": 13000.0, "coste": 4200.0,
                      "margen": 61.2, "valorPunto": 3.33})
        return l

    monkeypatch.setattr(AC.L, "linea", linea_con_dinero)

    pan = AC.panel_de(COMERCIAL, [
        pedido(id="A"),
        pedido(id="B", servidoAt="2026-08-10", cobradoAt="2026-08-09"),
    ])
    texto = json.dumps(pan).lower()
    for p in PROHIBIDOS:
        assert p.lower() not in texto, (
            f"el área del cooperativista está sacando «{p}». Por ahí se ve el "
            "dinero que el ERP le cierra al master en el servidor.")


def test_la_lista_de_lo_que_sale_es_BLANCA_y_no_negra(monkeypatch):
    """Con una lista negra, cualquier campo NUEVO —un coste, un margen— saldría
    solo el día que alguien lo añada arriba. Se comprueba igual: forzando que
    arriba aparezcan campos nuevos."""
    from services import liquidaciones as _L
    original = _L.linea

    def linea_con_basura(p, rol):
        l = original(p, rol)
        if l:
            l.update({"costeReal": 999, "margenPct": 42, "campoNuevoDeMañana": 7})
        return l

    monkeypatch.setattr(AC.L, "linea", linea_con_basura)
    pan = AC.panel_de(COMERCIAL, [pedido()])
    linea = pan["enProgreso"]["lineas"][0]
    assert set(linea) <= set(AC.CAMPOS_VISIBLES), (
        f"se ha colado un campo que nadie autorizó: {set(linea) - set(AC.CAMPOS_VISIBLES)}")


def test_LA_LISTA_BLANCA_NO_PUEDE_CRECER_CON_DINERO_DENTRO():
    """La otra mitad: que nadie meta un campo de dinero en la lista visible.

    Es un cambio de una palabra y no lo notaría nadie, porque el panel seguiría
    funcionando igual de bien — solo que enseñando lo que no debe.
    """
    for campo in AC.CAMPOS_VISIBLES:
        for p in PROHIBIDOS:
            assert p.lower() not in campo.lower(), (
                f"«{campo}» ha entrado en la lista de campos visibles y huele a "
                f"dinero de la casa («{p}»)")


def test_el_cooperativista_SI_ve_lo_suyo():
    """Cerrar de más también es un fallo: si no ve sus euros, el área no sirve
    para lo que se hizo, que es el plan de estimulación."""
    pan = AC.panel_de(COMERCIAL, [pedido()])
    assert pan["rol"] == AC.COMERCIAL
    # 13.000 € está en el tramo de 60 €, x10 muebles.
    assert pan["enProgreso"]["euros"] == 600.0
    assert pan["enProgreso"]["lineas"][0]["tramo"] == "de 12.000 € a 15.000 €"


def test_el_montador_cobra_LA_MANO_DE_OBRA_y_no_ve_tramo():
    """Su comisión es la mano de obra por mueble (CLAUDE.md, regla 16), que no
    depende de la valoración: por eso su panel no deja deducir el PVP."""
    pan = AC.panel_de(MONTADOR, [pedido()], mano_por_mueble=20.0)
    assert pan["enProgreso"]["euros"] == 200.0
    assert pan["enProgreso"]["lineas"][0]["tramo"] is None


# ── Los estados, ya cerrados en liquidaciones.py, siguen mandando ────────────
def test_lo_que_no_esta_servido_Y_cobrado_sigue_EN_PROGRESO():
    pan = AC.panel_de(COMERCIAL, [pedido(servidoAt="2026-08-10")])
    assert pan["consolidada"]["euros"] == 0
    assert pan["enProgreso"]["euros"] == 600.0


def test_un_pedido_ANULADO_no_aparece_en_el_area():
    for anulado in ({"anulado": True}, {"status": "cancelled"}):
        pan = AC.panel_de(COMERCIAL, [pedido(**anulado)])
        assert pan["enProgreso"]["pedidos"] == 0


@pytest.mark.parametrize("basura", [None, [], [{}], [None]])
def test_pedidos_absurdos_no_revientan_el_area(basura):
    pan = AC.panel_de(COMERCIAL, basura)
    assert pan["enProgreso"]["euros"] == 0
