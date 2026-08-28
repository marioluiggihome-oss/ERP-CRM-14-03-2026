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
    Cocina Montada 3    → `projects`, con `tipo: "cocina_montada_3"`.
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

NOMBRES = {
    MONTADA_3: "Cocina Montada 3",
    DESMONTADA: "Cocina Desmontada",
}

# Lo que `cascos_orders` considera un pedido de verdad. Un «presupuesto» todavía
# no se ha vendido y una «compra» es al proveedor: ni uno ni otro pagan comisión.
KIND_PEDIDO = "pedido"


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
    """Un pedido de Cocina Desmontada, con los nombres que usa la liquidación.

    `cascos_orders` guarda `cliente`, `ref` y `lines`; el resto del ERP dice
    `customerName`, `budgetNumber` e `items`. Se traduce aquí y en un solo sitio:
    si cada pantalla lo tradujera por su cuenta, acabarían contando cosas
    distintas.
    """
    d = doc or {}
    return {
        **d,
        "id": d.get("id") or "",
        "customerName": d.get("cliente") or d.get("customerName") or "",
        "budgetNumber": d.get("ref") or d.get("expediente") or "",
        "projectReference": d.get("expediente") or "",
        "items": d.get("lines") or d.get("items") or [],
        "confirmedAt": d.get("createdAt") or d.get("confirmedAt"),
        "descuentoPct": d.get("descuento") or 0,
        "origen": DESMONTADA,
        "origenNombre": NOMBRES[DESMONTADA],
    }
