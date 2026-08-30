# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
QUÉ PEDIDOS ENTRAN EN LA COOPERATIVA, Y DE DÓNDE SALEN.

El master, 28/08: «solo lista los pedidos que se hayan realizado desde Cocina
Montada 3 o Cocina Desmontada». Antes salían todos, incluidos los de la primera
sección de fábrica, que no tienen nada que ver con este negocio.

EL ERP GUARDA LOS PEDIDOS EN SITIOS DISTINTOS SEGÚN QUIÉN LOS HAGA:

    Cocina Desmontada   → colección `cascos_orders`, con `kind: "pedido"`
                          (`presupuesto` y `compra` NO son pedidos).
    Cocina Montada 3    → `cascos_orders` TAMBIÉN, desde el 28/08, con
                          `kind: "pedido"` y su `origen` puesto. La colección ya
                          no basta para saber de dónde viene un pedido: manda el
                          `origen` que trae escrito.
    Las secciones VIEJAS (BudgetTable, Presupuestador 2) → colección `orders`.

LA LISTA ES BLANCA, y eso es lo importante. Se dice qué orígenes SÍ entran, no
cuáles se excluyen. Con una lista negra, cualquier sección nueva del ERP
—o cualquier pedido de fábrica— entraría sola en la nómina el día que alguien la
añada, y nadie se enteraría hasta fin de mes.

Un pedido cuyo origen no se reconoce NO entra. Es la decisión conservadora de
siempre: pagar de menos se reclama; pagar de más no se devuelve.
"""
from __future__ import annotations

from typing import Iterable, Optional

MONTADA_3 = "cocina_montada_3"
DESMONTADA = "cocina_desmontada"

# LOS ÚNICOS que cuentan para la cooperativa (master, 28/08).
ORIGENES_QUE_CUENTAN = (MONTADA_3, DESMONTADA)

# CÓMO SE LEE cada origen. El VALOR (`cocina_montada_3`) NO se toca nunca: está
# escrito dentro de cada pedido guardado y con él cuadra la nómina. Renombrar la
# pantalla no puede mover un dato.
#
# El master, 29/08: Cocina Montada 3 pasa a llamarse «Presupuestador». Se deja
# «· Montada» al lado porque aquí los dos rótulos salen juntos, uno debajo de
# otro, y a secas no se distinguirían: las dos secciones viven dentro del
# Presupuestador.
NOMBRES = {
    MONTADA_3: "Presupuestador · Montada",
    DESMONTADA: "Presupuestador · Desmontada",
}

# Lo que `cascos_orders` considera un pedido de verdad. Un «presupuesto» todavía
# no se ha vendido y una «compra» es al proveedor: ni uno ni otro pagan comisión.
KIND_PEDIDO = "pedido"


# QUÉ ORÍGENES PAGAN COMISIÓN, Y CUÁL NO.
#
# El master, 30/08: «los cascos no pagan comisión; los pedidos de cascos solo
# son para separar cascos, cuando un cliente se lleva la cocina desmontada».
#
# O sea que Cocina Desmontada CUENTA para la cooperativa —es un pedido de la
# casa, entra en COOP, se le asigna montador y se sigue en producción— pero NO
# reparte comisión. Son dos preguntas distintas y hasta ahora solo estaba
# escrita la primera.
#
# POR QUÉ HAY QUE ESCRIBIRLO, si hoy ya pagan cero: pagan cero POR ACCIDENTE.
# Las líneas de un casco no traen familia del catálogo, y sin familia el cálculo
# no las cuenta como mueble. El día que alguien le ponga familia a esas líneas
# —o las empareje con el catálogo, que es una mejora razonable— Cocina
# Desmontada empezaría a repartir comisiones sin que nadie lo hubiera decidido,
# y sin que saltara ningún error. Un cero que sale solo no es una regla.
ORIGENES_SIN_COMISION = (DESMONTADA,)


def es_solo_cascos(pedido: Optional[dict]) -> bool:
    """¿Es un pedido de cascos, de los que NO reparten comisión?

    SE PREGUNTA EN POSITIVO, y eso importa. La primera versión hacía lo
    contrario —«comisiona solo si el origen está en la lista blanca»— y con eso
    un pedido al que nadie le hubiera marcado el origen dejaba de pagar EN
    SILENCIO. Rompió 19 candados de golpe, y en producción habría sido peor: no
    un error, sino comisiones que no llegan.

    Así que se excluye únicamente cuando CONSTA que es Cocina Desmontada. En la
    duda se sigue contando por familias, como siempre — que un mueble no cuente
    se ve en la nómina y se reclama; que deje de contar todo un origen no lo ve
    nadie.
    """
    return origen_de(pedido) == DESMONTADA


def origen_de(pedido: Optional[dict]) -> str:
    """De qué sección salió, o cadena vacía si no se reconoce.

    Manda lo que el propio documento diga (`origen`), que es lo que estampan las
    pantallas nuevas. Si no lo trae, se deduce de la forma del documento — pero
    solo cuando es inequívoca.
    """
    p = pedido or {}
    marcado = str(p.get("origen") or "").strip().lower()
    if marcado in ORIGENES_QUE_CUENTAN:
        return marcado
    tipo = str(p.get("tipo") or "").strip().lower()
    if tipo == MONTADA_3:
        return MONTADA_3
    # `cascos_orders` es, por definición, Cocina Desmontada: la colección ES el
    # origen. Se reconoce por `kind`, que solo existe ahí.
    if str(p.get("kind") or "").strip().lower() == KIND_PEDIDO:
        return DESMONTADA
    return ""


def cuenta_para_la_cooperativa(pedido: Optional[dict]) -> bool:
    return origen_de(pedido) in ORIGENES_QUE_CUENTAN


def solo_los_que_cuentan(pedidos: Iterable[dict]) -> list:
    """Los pedidos de la cooperativa, con su origen puesto para poder enseñarlo.

    Que se vea de qué sección viene cada uno no es un adorno: si un día vuelve a
    aparecer un pedido que no toca, se sabrá de dónde ha entrado.
    """
    fuera = []
    for p in (pedidos or []):
        o = origen_de(p)
        if o in ORIGENES_QUE_CUENTAN:
            fuera.append(dict(p, origen=o, origenNombre=NOMBRES.get(o, o)))
    return fuera


def normaliza_pedido_de_cascos(doc: dict) -> dict:
    """Un pedido guardado en `cascos_orders`, con los nombres que usa la liquidación.

    `cascos_orders` guarda `cliente`, `ref` y `lines`; el resto del ERP dice
    `customerName`, `budgetNumber` e `items`. Se traduce aquí y en un solo sitio:
    si cada pantalla lo tradujera por su cuenta, acabarían contando cosas
    distintas.

    EL ORIGEN NO SE PISA. En esta colección no solo hay Cocina Desmontada: desde
    el 28/08 los PEDIDOS de Cocina Montada 3 se guardan aquí también, con su
    `origen` puesto. Esta función los marcaba a todos como Desmontada, así que en
    COOP cada pedido de Montada 3 salía con la sección equivocada. Contar,
    contaban —las dos están en la lista blanca—, pero el rótulo es justo lo que
    hay que mirar el día que se cuele un pedido que no toca: si miente, el
    «solo Montada 3 o Desmontada» que pidió el master no se puede comprobar.
    """
    d = doc or {}
    marcado = str(d.get("origen") or "").strip().lower()
    origen = marcado if marcado in ORIGENES_QUE_CUENTAN else DESMONTADA
    return {
        **d,
        "id": d.get("id") or "",
        "customerName": d.get("cliente") or d.get("customerName") or "",
        "budgetNumber": d.get("ref") or d.get("expediente") or "",
        "projectReference": d.get("expediente") or "",
        "items": d.get("lines") or d.get("items") or [],
        "confirmedAt": d.get("createdAt") or d.get("confirmedAt"),
        "descuentoPct": d.get("descuento") or 0,
        "origen": origen,
        "origenNombre": NOMBRES[origen],
    }
