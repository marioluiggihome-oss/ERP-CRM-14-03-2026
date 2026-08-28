# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
QUIÉN COBRA CADA PEDIDO: LA PANTALLA DE ASIGNACIÓN DEL MASTER.

Sin esto el área del cooperativista no sirve de nada: un pedido servido y
cobrado al que nadie le ha puesto comercial ni montador NO da ningún error —
simplemente no sale en la nómina de nadie, y de eso no se entera nunca quien
tenía que cobrar. Por eso `sinAsignar` se cuenta y sale primero.

LAS DOS COSAS QUE VIGILA ESTE CANDADO:

1. QUE LA LISTA DE SOCIOS NO VUELQUE EL USUARIO ENTERO. El documento de un
   usuario lleva dentro la contraseña, sus descuentos comerciales y todos sus
   permisos. Una pantalla de «elige quién montó esto» no tiene por qué enseñar
   nada de eso, así que sale por lista BLANCA. Con una lista negra, cualquier
   campo nuevo saldría solo el día que alguien lo añada.

2. QUE NO SE PUEDA ELEGIR A QUIEN NO ES SOCIO. Si en el desplegable saliera el
   comercial en nómina o un suscriptor de carpinter.io, asignarle un pedido
   sería meterlo en la liquidación por la puerta de atrás.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("JWT_SECRET", "secreto-de-pruebas-largo-y-aleatorio-0123456789")

from services import area_cooperativista as AC  # noqa: E402

SOCIO_COM = {"id": "u-com", "clientName": "Ana", "esCooperativistaComercial": True,
             "password": "hash-secreto", "commercialDiscount": 12.5,
             "canSeeCost": True, "isAdmin": False}
SOCIO_MON = {"id": "u-mon", "clientName": "Bea", "esCooperativistaMontador": True,
             "manoObraPorMueble": 19.0, "password": "hash-secreto"}
COMERCIAL_EN_NOMINA = {"id": "u-nom", "clientName": "Carlos", "isRepresentative": True}
SUSCRIPTOR = {"id": "u-car", "clientName": "Dani", "esCooperativistaComercial": True,
              "plataforma": "carpinter"}

PEDIDO = {
    "id": "order-1", "customerName": "Pérez", "budgetNumber": "P-100",
    "confirmedAt": "2026-08-01",
    "items": [{"familia": "BAJO", "qty": 8, "pvp": 500.0},
              {"familia": "PUERTAS", "qty": 20, "pvp": 30.0}],
}


def test_la_lista_de_socios_NO_VUELCA_el_usuario_entero():
    """Lista BLANCA: solo id, nombre, rol y —el montador— su mano de obra."""
    ficha = AC.socio_publico(SOCIO_COM)
    assert set(ficha) <= set(AC.CAMPOS_DEL_SOCIO), (
        f"salen campos que no están en la lista blanca: "
        f"{set(ficha) - set(AC.CAMPOS_DEL_SOCIO)}")
    volcado = repr(ficha)
    for prohibido in ("hash-secreto", "password", "12.5", "commercialDiscount",
                      "canSeeCost"):
        assert prohibido not in volcado, (
            f"la lista de socios enseña «{prohibido}»: {volcado}")


def test_solo_SOCIOS_pueden_elegirse():
    """Ni el comercial en nómina ni un suscriptor entran en el desplegable."""
    assert AC.socio_publico(COMERCIAL_EN_NOMINA) is None, (
        "el comercial de toda la vida de la casa sale en la lista de socios: "
        "asignarle un pedido lo metería en la nómina por la puerta de atrás")
    assert AC.socio_publico(SUSCRIPTOR) is None, (
        "un suscriptor de carpinter.io sale como socio de la cooperativa")
    assert AC.socio_publico({}) is None
    assert AC.socio_publico(None) is None


def test_los_socios_salen_SEPARADOS_POR_ROL_y_ordenados():
    """Son dos desplegables distintos: el comercial no puede aparecer en el de
    montadores, porque cobran de forma distinta."""
    s = AC.socios_de([SOCIO_MON, SOCIO_COM, COMERCIAL_EN_NOMINA, SUSCRIPTOR, {}])
    assert [f["id"] for f in s["comerciales"]] == ["u-com"]
    assert [f["id"] for f in s["montadores"]] == ["u-mon"]
    # El nombre, no el identificador: es lo que el master reconoce.
    assert s["comerciales"][0]["nombre"] == "Ana"


def test_la_MANO_DE_OBRA_solo_sale_para_el_montador():
    """Al comercial no se le enseña un € por mueble que no cobra: cobra por
    tramos. Enseñárselo sería inventarle una nómina que no existe."""
    assert "manoObraPorMueble" not in AC.socio_publico(SOCIO_COM)
    assert AC.socio_publico(SOCIO_MON)["manoObraPorMueble"] == 19.0
    # Y el que no tiene cifra propia sale con la de la casa, no vacío.
    sin_cifra = dict(SOCIO_MON)
    sin_cifra.pop("manoObraPorMueble")
    assert AC.socio_publico(sin_cifra)["manoObraPorMueble"] == 17.0


def test_un_pedido_SIN_ASIGNAR_se_marca():
    """Es lo único que de verdad hay que ver en esta pantalla."""
    p = AC.pedido_para_asignar(PEDIDO)
    assert p["sinAsignar"] is True
    assert p["comercialUserId"] == "" and p["montadorUserId"] == ""

    medio = dict(PEDIDO, comercialUserId="u-com")
    assert AC.pedido_para_asignar(medio)["sinAsignar"] is True, (
        "un pedido con comercial pero sin montador está sin asignar: el "
        "montador no cobraría y nadie se enteraría")

    entero = dict(PEDIDO, comercialUserId="u-com", montadorUserId="u-mon")
    assert AC.pedido_para_asignar(entero)["sinAsignar"] is False


def test_los_MUEBLES_de_la_pantalla_son_los_que_incentivan():
    """Ocho muebles y veinte puertas son OCHO. Si la pantalla contara las líneas
    del pedido, el master asignaría creyendo que paga por 28."""
    p = AC.pedido_para_asignar(PEDIDO)
    assert p["muebles"] == 8, (
        f"la pantalla cuenta {p['muebles']} muebles: las puertas no incentivan")
    assert p["sinDesglose"] is False


def test_un_pedido_SIN_LINEAS_se_marca_y_no_se_inventa_un_numero():
    p = AC.pedido_para_asignar({"id": "x", "itemsCount": 30})
    assert p["sinDesglose"] is True
    assert p["muebles"] == 0, (
        "sin las líneas no se puede saber qué era mueble: contar el pedido "
        "entero sería pagar de más, y pagar de más no se devuelve")


def test_la_pantalla_NO_ENSEÑA_EL_IMPORTE_del_pedido():
    """El master podría verlo, pero para decidir quién montó una cocina no hace
    falta. Cuanto menos dinero viaje por rutas nuevas, menos sitios hay por los
    que se pueda escapar (CLAUDE.md, 8b y 9)."""
    p = AC.pedido_para_asignar(dict(PEDIDO, totalAmount=4600.0, coste=2000.0,
                                    margen=1200.0))
    volcado = repr(p)
    for prohibido in ("4600", "totalAmount", "coste", "margen", "2000", "1200",
                      "baseImponible"):
        assert prohibido not in volcado, (
            f"la pantalla de asignación enseña «{prohibido}»: {volcado}")


def test_el_NOMBRE_del_asignado_se_resuelve_para_poder_leerlo():
    nombres = {"u-com": "Ana", "u-mon": "Bea"}
    p = AC.pedido_para_asignar(
        dict(PEDIDO, comercialUserId="u-com", montadorUserId="u-mon"), nombres)
    assert p["comercial"] == "Ana" and p["montador"] == "Bea"
    # Y si el usuario ya no existe, no revienta ni inventa un nombre.
    huerfano = AC.pedido_para_asignar(dict(PEDIDO, comercialUserId="u-fue"), nombres)
    assert huerfano["comercial"] == ""
    assert huerfano["comercialUserId"] == "u-fue", (
        "se ha perdido el identificador del asignado: sin él no hay forma de "
        "ver que el pedido apunta a alguien que ya no está")


def test_las_rutas_de_socios_y_pedidos_son_SOLO_DEL_MASTER():
    """La lista de socios es «quién cobra en esta casa» y la de pedidos es
    quién cobra cada uno. Se comprueba en el FICHERO de rutas, no solo en la
    pantalla: si únicamente se cierra la pantalla, el cierre es de adorno."""
    ruta = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "routes", "cooperativistas.py")
    with open(ruta, "r", encoding="utf-8") as f:
        cuerpo = f.read()
    for endpoint in ('@router.get("/socios")', '@router.get("/pedidos")',
                     '@router.post("/asignar")'):
        i = cuerpo.index(endpoint)
        j = cuerpo.index("@router", i + 10) if "@router" in cuerpo[i + 10:] else len(cuerpo)
        trozo = cuerpo[i:j]
        assert "_es_master" in trozo, (
            f"«{endpoint}» no comprueba el master en el servidor")
