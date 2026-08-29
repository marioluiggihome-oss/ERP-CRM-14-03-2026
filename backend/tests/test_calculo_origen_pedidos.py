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

    SE EJECUTA LA FUNCIÓN, no se lee el fichero. La primera versión de esta
    prueba buscaba `"origen":` en el texto de `routes/cascos.py` y leía los 400
    caracteres siguientes; el día que apareció otro `"origen":` más arriba —en la
    proyección de un `find_one`— la prueba se puso roja acusando a un trozo de
    código que no era. Un candado que señala el sitio equivocado hace perder el
    tiempo igual que uno que no salta.
    """
    from routes.cascos import _origen_valido

    for bueno in OP.ORIGENES_QUE_CUENTAN:
        assert _origen_valido(bueno) == bueno
    assert _origen_valido("  COCINA_MONTADA_3 ") == OP.MONTADA_3, (
        "un origen bueno con espacios o mayúsculas se está tirando")
    for malo in ("fabrica", "orders", "cooperativa", "", None, 123, {"a": 1}):
        assert _origen_valido(malo) == "", (
            f"«{malo!r}» se está guardando como origen: por ahí se mete "
            "cualquier pedido en la nómina de la cooperativa")


def test_un_guardado_que_no_trae_el_ORIGEN_no_puede_borrarlo():
    """Se escribe con un `$set` del documento entero (misma trampa que la regla
    12 de CLAUDE.md con las medidas). Sin respaldar lo que ya había, re-guardar
    un pedido de Cocina Montada 3 desde otra pantalla lo dejaría sin origen — y
    pasaría a contarse como Cocina Desmontada sin que nadie tocara nada."""
    ruta = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "routes", "cascos.py")
    with open(ruta, "r", encoding="utf-8") as f:
        cuerpo = f.read()
    i = cuerpo.index('"origen": _origen_valido(')
    linea = cuerpo[i:cuerpo.index("\n", i)]
    assert '(existing or {}).get("origen")' in linea, (
        "el origen no se respalda con el que ya tenía el pedido: un guardado que "
        "no lo traiga lo borra")
    assert '"origen": 1' in cuerpo[:i], (
        "el `find_one` no se trae el `origen`, así que el respaldo de arriba "
        "siempre valdrá vacío y no protege nada")


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


# ── QUIEN GRABA EL PEDIDO SE LO LLEVA ───────────────────────────────────────
#
# El master, 28/08: «dependiendo del usuario que grabe el pedido, así
# comisionará, si son usuarios cooperativistas».
#
# Le ahorra asignar a mano el caso normal —el comercial que teclea su propio
# pedido— pero es dinero, así que tiene tres candados: solo socios, en SU rol, y
# sin pisar nunca lo que el master ya decidió.

def _trozo_de_guardar_pedido():
    ruta = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "routes", "cascos.py")
    with open(ruta, "r", encoding="utf-8") as f:
        cuerpo = f.read()
    i = cuerpo.index("QUIEN GRABA EL PEDIDO SE LO LLEVA")
    return cuerpo[i:cuerpo.index("update_one", i) + 200]


def test_solo_un_SOCIO_se_lleva_el_pedido_que_graba():
    """Se pregunta a `rol_de`, que ya exige la marca de socio Y la plataforma.

    Un comercial en nómina o un suscriptor de carpinter.io graban pedidos igual
    y no cobran. Si aquí se mirara `isRepresentative` —el rol genérico— entraría
    en la nómina medio ERP por la puerta de grabar un pedido.
    """
    trozo = _trozo_de_guardar_pedido()
    assert "_AC.rol_de(current_user)" in trozo, (
        "no se comprueba que quien graba sea SOCIO: cualquiera que teclee un "
        "pedido se lo llevaría")
    for generico in ("isRepresentative", "isComercial", "isMontador"):
        assert generico not in trozo, (
            f"se está mirando «{generico}», que es el rol genérico del ERP y no "
            "la marca de socio")


def test_se_asigna_EN_SU_ROL_y_no_en_el_otro():
    """El comercial cobra por tramos y el montador la mano de obra. Un montador
    que grabe un pedido no puede entrar como comercial."""
    trozo = _trozo_de_guardar_pedido()
    assert "_AC.COMERCIAL" in trozo and "comercialUserId" in trozo
    assert "_AC.MONTADOR" in trozo and "montadorUserId" in trozo


def test_NO_SE_PISA_lo_que_el_master_ya_asigno():
    """Asignar es del master (regla 20). Si él lo puso en otro bolsillo, manda
    él; y al re-guardar el mismo pedido tampoco se reescribe."""
    trozo = _trozo_de_guardar_pedido()
    assert 'not (existing or {}).get(_clave)' in trozo, (
        "se asigna sin mirar si ya estaba asignado: re-guardar un pedido le "
        "quitaría la comisión a quien el master hubiera puesto")
    # Y el documento anterior tiene que traerse esos campos, o la comprobación
    # de arriba miraría siempre vacío y pisaría siempre.
    ruta = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "routes", "cascos.py")
    with open(ruta, "r", encoding="utf-8") as f:
        cuerpo = f.read()
    i = cuerpo.index("cascos_orders.find_one(")
    proyeccion = cuerpo[i:i + 260]
    assert '"comercialUserId": 1' in proyeccion and '"montadorUserId": 1' in proyeccion, (
        "el pedido anterior se lee sin sus asignaciones, así que la "
        "comprobación de «ya estaba asignado» siempre daría vacío y pisaría")


def test_UN_PEDIDO_DE_MONTADA_3_NO_SE_ROTULA_COMO_DESMONTADA():
    """`cascos_orders` ya no es solo Cocina Desmontada.

    Desde el 28/08 los PEDIDOS de Cocina Montada 3 se guardan en esa misma
    colección, con su `origen` puesto. `normaliza_pedido_de_cascos` los marcaba
    a TODOS como Desmontada, así que en COOP cada pedido de Montada 3 salía con
    la sección equivocada.

    Contar, contaban —las dos están en la lista blanca—, pero el rótulo es justo
    lo que hay que mirar el día que se cuele un pedido que no toca: si miente, el
    «solo Montada 3 o Desmontada» que pidió el master no se puede comprobar.
    """
    d = OP.normaliza_pedido_de_cascos(
        {"id": "cm3-ped-1", "kind": "pedido", "origen": OP.MONTADA_3,
         "cliente": "Ana", "lines": []})
    assert d["origen"] == OP.MONTADA_3, (
        "un pedido de Cocina Montada 3 se está rotulando como Cocina Desmontada")
    assert d["origenNombre"] == "Cocina Montada 3"


def test_un_pedido_de_cascos_SIN_origen_sigue_siendo_desmontada():
    """La otra mitad: los pedidos de siempre no traen `origen`, y esa colección
    ES Cocina Desmontada. Sin esto se quedarían sin sección."""
    d = OP.normaliza_pedido_de_cascos({"id": "c1", "kind": "pedido", "cliente": "Ana"})
    assert d["origen"] == OP.DESMONTADA
    assert d["origenNombre"] == "Cocina Desmontada"


def test_un_origen_QUE_NO_CUENTA_no_se_cuela_por_esta_puerta():
    """Escribir `origen: "fabrica"` en un documento de `cascos_orders` no puede
    servir para meter en la nómina una sección que no está en la lista blanca —
    ni para inventarse un rótulo que no existe."""
    d = OP.normaliza_pedido_de_cascos({"id": "x", "kind": "pedido", "origen": "fabrica"})
    assert d["origen"] in OP.ORIGENES_QUE_CUENTAN
    assert d["origenNombre"] == "Cocina Desmontada"
