# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
QUÉ PEDIDOS ENTRAN EN LA COOPERATIVA. SOLO DOS SECCIONES.

El master, 28/08: «solo lista los pedidos que se hayan realizado desde Cocina
Montada 3 o Cocina Desmontada». Lo dijo viendo en pantalla pedidos de la primera
sección de fábrica, que no tienen nada que ver con este negocio.

El ERP los guarda en sitios distintos: Cocina Desmontada en `cascos_orders` y
las secciones VIEJAS —BudgetTable, Presupuestador 2— en `orders`. La pantalla de
COOP leía `orders` entera.

LA LISTA ES BLANCA, y eso es lo que vigila este candado. Se dice qué entra, no
qué se excluye. Con una lista negra, una sección nueva del ERP —o un pedido de
fábrica— entraría sola en la nómina el día que alguien la añada, y no se sabría
hasta fin de mes.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("JWT_SECRET", "secreto-de-pruebas-largo-y-aleatorio-0123456789")

from services import origen_pedidos as OP  # noqa: E402

# CON SUS LÍNEAS DE VERDAD: con `lines` vacío la traducción no se ejerce y el
# candado pasa por casualidad (se vio rompiéndolo).
DESMONTADA = {"id": "casco-1", "kind": "pedido", "cliente": "Pérez",
              "ref": "EXP-7", "total": 4000.0, "createdAt": "2026-08-01",
              "lines": [{"code": "B60D/I", "familia": "BAJO",
                         "quantity": 4, "price": 1200.0}]}
MONTADA_3 = {"id": "cm3-1", "tipo": "cocina_montada_3", "customerName": "Ruiz"}
DE_FABRICA = {"id": "order-1", "customerName": "MARIO - ARMARIO",
              "budgetNumber": "MV-2026-64608", "orderKind": "cocina"}


def test_SOLO_entran_montada_3_y_desmontada():
    assert set(OP.ORIGENES_QUE_CUENTAN) == {OP.MONTADA_3, OP.DESMONTADA}
    assert OP.cuenta_para_la_cooperativa(DESMONTADA)
    assert OP.cuenta_para_la_cooperativa(MONTADA_3)


def test_un_pedido_de_LAS_SECCIONES_VIEJAS_no_entra():
    """Es lo que el master vio en pantalla y lo que hay que dejar fuera."""
    assert not OP.cuenta_para_la_cooperativa(DE_FABRICA), (
        "un pedido de la sección vieja sigue entrando en la cooperativa")
    assert OP.solo_los_que_cuentan([DE_FABRICA]) == []


def test_la_lista_es_BLANCA_y_no_negra():
    """Un origen que no se reconoce NO entra.

    Es la diferencia entre las dos listas: con una negra, cualquier sección
    nueva del ERP se colaría sola el día que alguien la añada.
    """
    for desconocido in ({"id": "x"}, {"id": "x", "origen": "seccion_nueva"},
                        {"id": "x", "tipo": "otra_cosa"}, {"id": "x", "kind": "presupuesto"},
                        {"id": "x", "kind": "compra"}, {}, None):
        assert not OP.cuenta_para_la_cooperativa(desconocido), desconocido


def test_en_cascos_solo_cuenta_lo_que_ES_UN_PEDIDO():
    """`cascos_orders` guarda tres cosas. Un presupuesto todavía no se ha
    vendido y una compra es al proveedor: ni uno ni otro pagan comisión."""
    assert not OP.cuenta_para_la_cooperativa(dict(DESMONTADA, kind="presupuesto"))
    assert not OP.cuenta_para_la_cooperativa(dict(DESMONTADA, kind="compra"))
    assert OP.cuenta_para_la_cooperativa(dict(DESMONTADA, kind="pedido"))


def test_el_ORIGEN_viaja_con_el_pedido_para_poder_verlo():
    """Si un día vuelve a aparecer un pedido que no toca, hay que poder ver de
    dónde ha entrado."""
    fuera = OP.solo_los_que_cuentan([DESMONTADA, MONTADA_3, DE_FABRICA])
    assert [p["origen"] for p in fuera] == [OP.DESMONTADA, OP.MONTADA_3]
    assert fuera[0]["origenNombre"] == "Cocina Desmontada"
    assert fuera[1]["origenNombre"] == "Cocina Montada 3"


def test_lo_MARCADO_manda_sobre_lo_deducido():
    """Las pantallas nuevas estampan `origen`. Deducirlo es solo para lo que ya
    está guardado."""
    assert OP.origen_de({"origen": "cocina_montada_3", "kind": "pedido"}) == OP.MONTADA_3
    # Y una marca que no se reconoce no cuela.
    assert OP.origen_de({"origen": "fabrica"}) == ""


def test_un_pedido_de_DESMONTADA_se_traduce_a_los_nombres_de_siempre():
    """`cascos_orders` dice `cliente`, `ref` y `lines`; el resto del ERP dice
    `customerName`, `budgetNumber` e `items`. Si no se tradujera, el pedido
    saldría sin cliente y sin líneas: cero muebles y cero comisión."""
    p = OP.normaliza_pedido_de_cascos(DESMONTADA)
    assert p["customerName"] == "Pérez"
    assert p["budgetNumber"] == "EXP-7"
    assert p["items"] == DESMONTADA["lines"], (
        "las líneas no se han traducido: el pedido saldría sin muebles y sin "
        "comisión")
    assert p["confirmedAt"] == "2026-08-01"
    assert p["origen"] == OP.DESMONTADA


def test_la_ruta_NO_LEE_la_coleccion_de_pedidos_a_pelo():
    """Se comprueba en el fichero: si alguien vuelve a poner un `orders.find`
    suelto, se salta la lista blanca y vuelven los pedidos de fábrica."""
    ruta = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "routes", "cooperativistas.py")
    with open(ruta, "r", encoding="utf-8") as f:
        cuerpo = f.read()
    # La única lectura directa permitida es la de dentro del ayudante.
    assert cuerpo.count("_db().orders.find") == 1, (
        "hay lecturas de `orders` fuera de `_pedidos_de_la_cooperativa`: por ahí "
        "vuelven a entrar los pedidos que el master no quiere ver")
    assert "_pedidos_de_la_cooperativa" in cuerpo


def test_al_escribir_se_tocan_LAS_DOS_COLECCIONES():
    """Un pedido de Cocina Desmontada vive en `cascos_orders`. Escribir siempre
    en `orders` dejaba SIN EFECTO asignarle un comercial o liquidarlo: la
    llamada respondía que sí y no cambiaba nada."""
    ruta = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "routes", "cooperativistas.py")
    with open(ruta, "r", encoding="utf-8") as f:
        cuerpo = f.read()
    assert "_db().orders, _db().cascos_orders" in cuerpo, (
        "el escritor ya no toca las dos colecciones")
    assert cuerpo.count("_db().orders.update_one") == 0, (
        "hay escrituras que van solo a `orders`: en un pedido de Cocina "
        "Desmontada no harían nada y nadie se enteraría")


# ── PEDIDOS DESDE COCINA MONTADA 3 ──────────────────────────────────────────
#
# El master, 28/08: «necesito crear pedidos desde Cocina Montada 3». Hasta
# entonces esa pantalla solo guardaba presupuestos, así que sus cocinas no
# llegaban nunca a la cooperativa. Ahora crea pedidos en la misma colección que
# Cocina Desmontada, y se distinguen por la marca `origen`.

def test_un_pedido_de_CM3_se_reconoce_por_su_marca_y_no_como_desmontada():
    """Los dos viven en `cascos_orders` con `kind: "pedido"`. Sin la marca, un
    pedido de Cocina Montada 3 se contaría como de Desmontada — las dos entran
    en la cooperativa, pero mezclarlas haría imposible saber de dónde sale el
    trabajo."""
    cm3 = {"id": "cm3-ped-1", "kind": "pedido", "origen": "cocina_montada_3",
           "cliente": "Ruiz", "lines": []}
    assert OP.origen_de(cm3) == OP.MONTADA_3
    assert OP.cuenta_para_la_cooperativa(cm3)
    assert OP.solo_los_que_cuentan([cm3])[0]["origenNombre"] == "Cocina Montada 3"


def test_el_ORIGEN_que_llega_por_la_PETICION_pasa_por_lista_blanca():
    """Es el mismo fallo que tuvo el motor de render: la pantalla mandaba lo
    correcto y la API se fiaba de lo que le llegara.

    El origen viaja en el cuerpo de la petición. Si se guardara tal cual,
    cualquiera con sesión podría meter en la nómina de la cooperativa un pedido
    de la sección que fuera, mandando el origen que le conviniera.
    """
    ruta = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "routes", "cascos.py")
    with open(ruta, "r", encoding="utf-8") as f:
        cuerpo = f.read()
    i = cuerpo.index('"origen":')
    trozo = cuerpo[i:i + 400]
    assert "_OP.ORIGENES_QUE_CUENTAN" in trozo, (
        "el origen que llega en la petición se guarda sin comprobar: por ahí se "
        "mete cualquier pedido en la nómina de la cooperativa")


def test_la_pantalla_de_CM3_manda_LA_FAMILIA_y_el_importe_ya_multiplicado():
    """Sin `familia` el pedido entra con «0 muebles» y no paga a nadie; y si
    `price` fuera por unidad, el cálculo lo multiplicaría otra vez e inflaría la
    base imponible, subiendo de tramo al comercial sin que el pedido valiera un
    euro más."""
    raiz = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ruta = os.path.join(raiz, "frontend", "src", "components", "CocinaMontada3.jsx")
    with open(ruta, "r", encoding="utf-8") as f:
        cuerpo = f.read()
    i = cuerpo.index("const pasarAPedido")
    trozo = cuerpo[i:cuerpo.index("};", cuerpo.index("finally", i))]
    assert "origen: 'cocina_montada_3'" in trozo, (
        "el pedido de CM3 no lleva su marca de origen: entraría como si fuera de "
        "Cocina Desmontada")
    assert "kind: 'pedido'" in trozo, "se está creando un presupuesto, no un pedido"
    assert "familia:" in trozo, (
        "las líneas van sin familia: el pedido entraría en COOP con «0 muebles»")
    assert "(Number(m.pvp) || 0) * (Number(m.qty) || 1)" in trozo, (
        "el importe de la línea no lleva las unidades dentro; el cálculo espera "
        "`price` ya multiplicado")
