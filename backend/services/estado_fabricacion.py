# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
POR DÓNDE VA CADA PEDIDO EN FÁBRICA.

El master, 30/08: una pestaña en COOP con «los pedidos y el estado de los
mismos en fábrica, vamos los procesos de producción y su estado».

DE DÓNDE SALE EL ESTADO, que es lo que no se puede inventar. La fábrica lleva su
propia colección, `fabrica_orders`, atada al pedido por `budgetNumber`, con un
`status` y un `progress`. Eso ya existía y ya lo traducía `routes/orders.py`
para «Mis Pedidos» — con la tabla escrita ahí dentro, a mano.

AQUÍ ESTÁ ESA TABLA, Y SOLO AQUÍ. Copiarla habría sido la cuarta vez en este
proyecto que una regla vive en dos sitios y se separan: la de `es_master` vivía
en cuatro ficheros, la del origen de los pedidos en dos, la de los tramos de
comisión en la pantalla y en el cálculo. Cuando se separan, una pantalla dice
«En producción» y la otra «Confirmado» del mismo pedido, y nadie sabe cuál
mentir.

LO QUE NO SE INVENTA: un pedido del que la fábrica no sabe nada NO está
«pendiente» ni «en producción» — está `confirmed`, que es lo que significa: se
vendió y todavía no ha entrado en el taller. Poner otra cosa sería adivinar.
"""
from __future__ import annotations

from typing import Optional

from services import comisiones as C
from services import liquidaciones as L

# El `status` de `fabrica_orders` → el estado que se enseña. La tabla es la que
# ya usaba `routes/orders.py`; se ha traído aquí para que no haya dos.
DE_FABRICA = {
    "draft": "pending",
    "confirmed": "confirmed",
    "in_progress": "in_production",
    "completed": "ready",
    "shipped": "shipped",
    "delivered": "delivered",
}

# Cuando la fábrica no tiene ficha de ese pedido. No es un error ni un hueco:
# es un pedido vendido que aún no ha entrado en el taller.
SIN_FICHA_EN_FABRICA = "confirmed"

# Los estados, EN ORDEN de proceso, con lo que se lee en pantalla. El orden es
# el del taller y se usa para ordenar la lista: lo que está más atrás primero,
# que es lo que hay que empujar.
ESTADOS = (
    ("pending", "Pendiente"),
    ("confirmed", "Confirmado"),
    ("in_production", "En producción"),
    ("ready", "Listo para envío"),
    ("shipped", "Enviado"),
    ("delivered", "Entregado"),
)

ORDEN = {clave: i for i, (clave, _) in enumerate(ESTADOS)}
NOMBRES = dict(ESTADOS)


def estado_de(ficha_de_fabrica: Optional[dict]) -> str:
    """El estado de fabricación a partir de la ficha de `fabrica_orders`."""
    if not ficha_de_fabrica:
        return SIN_FICHA_EN_FABRICA
    return DE_FABRICA.get(ficha_de_fabrica.get("status"), SIN_FICHA_EN_FABRICA)


def progreso_de(ficha_de_fabrica: Optional[dict]) -> int:
    """El porcentaje, acotado. Un progreso corrupto es 0, no una barra rara."""
    try:
        v = int(float((ficha_de_fabrica or {}).get("progress") or 0))
    except (TypeError, ValueError):
        return 0
    return max(0, min(100, v))


# Lo único que sale de un pedido hacia la pestaña de producción. Lista BLANCA,
# como en todo este módulo: aquí se mira POR DÓNDE VA una cocina, no lo que
# vale. El dinero de estos pedidos ya tiene su sitio —Rentabilidad— y no viaja
# por rutas nuevas.
CAMPOS_DE_LA_LINEA = (
    "pedidoId", "referencia", "cliente", "origen", "fecha",
    "estado", "estadoNombre", "progreso", "servido", "cobrado",
)


def linea(pedido: dict, ficha_de_fabrica: Optional[dict] = None) -> dict:
    """Una fila de la pestaña de producción."""
    p = pedido or {}
    clave = estado_de(ficha_de_fabrica)
    return {
        "pedidoId": p.get("id") or "",
        "referencia": (p.get("budgetNumber") or p.get("projectReference")
                       or p.get("ref") or ""),
        "cliente": (p.get("customerName") or p.get("cliente") or "").strip(),
        "origen": p.get("origenNombre") or p.get("origen") or "",
        "fecha": p.get("confirmedAt") or p.get("createdAt") or "",
        "estado": clave,
        "estadoNombre": NOMBRES.get(clave, clave),
        "progreso": progreso_de(ficha_de_fabrica),
        # El final del proceso, que ya sabe el ERP por el albarán y la factura
        # (`services/enlace_documentos.py`). Sin esto la pestaña se queda a
        # medias: «Entregado» en fábrica no quiere decir cobrado.
        "servido": bool(L.servido_de(p)),
        "cobrado": bool(L.cobrado_de(p)),
    }


def lineas(pedidos, fichas_por_referencia: Optional[dict] = None) -> list:
    """Todas las filas, lo más atrasado primero: es lo que hay que empujar."""
    fichas = fichas_por_referencia or {}
    fuera = []
    for p in (pedidos or []):
        ref = ((p or {}).get("budgetNumber") or (p or {}).get("ref") or "")
        fuera.append(linea(p, fichas.get(str(ref).strip())))
    fuera.sort(key=lambda l: (ORDEN.get(l["estado"], 99), str(l["fecha"] or "")))
    return fuera


def resumen(filas) -> dict:
    """Cuántos hay en cada estado, en orden de proceso."""
    cuenta = {clave: 0 for clave, _ in ESTADOS}
    for f in (filas or []):
        if f.get("estado") in cuenta:
            cuenta[f["estado"]] += 1
    return {"total": len(filas or []),
            "porEstado": [{"estado": c, "nombre": n, "pedidos": cuenta[c]}
                          for c, n in ESTADOS]}


# ─── QUÉ LLEVA UN PEDIDO ────────────────────────────────────────────────────
#
# El master, 30/08: «que podamos entrar en los pedidos, si no no sabemos lo que
# hay en cada uno de ellos». La lista dice POR DÓNDE VA; esto dice QUÉ ES.
#
# SIN IMPORTES, igual que la lista. Para saber qué cocina hay que fabricar hacen
# falta los códigos y las unidades, no los euros: para eso está Rentabilidad,
# con su puerta. Lista BLANCA otra vez, porque dentro de una línea de pedido
# viajan `price`, `pvp` y los descuentos.
CAMPOS_DE_LA_LINEA_DEL_PEDIDO = ("codigo", "descripcion", "unidades", "familia",
                                 "esMueble")


def linea_de_pedido(l: dict, familias: Optional[dict] = None) -> dict:
    """Una línea del pedido, con lo justo para saber qué es.

    LAS UNIDADES Y LA FAMILIA NO SE LEEN AQUÍ A MANO. Se las pide a
    `services/comisiones.py`, que es donde ya está escrito qué nombre usa cada
    pantalla del ERP (`qty`, `cant`, `quantity`, `unidades`) y qué es la familia
    de una línea. Escribirlo otra vez es exactamente el fallo del 28/08: las
    pruebas leían `qty`/`familia` y los pedidos de verdad guardan
    `quantity`/`code`, así que COOP enseñaba «0 muebles» en todos los pedidos.
    Si un día cambia el nombre, cambia en un sitio.
    """
    d = dict(l or {})
    if familias:
        d.setdefault("_familiaResuelta",
                     C.familia_de(d)
                     or familias.get(str(d.get("code") or "").strip().upper(), ""))
    return {
        "codigo": str(d.get("code") or d.get("cod") or "").strip(),
        "descripcion": str(d.get("name") or d.get("desc")
                           or d.get("etiqueta") or "").strip(),
        "unidades": C.unidades_de(d),
        "familia": C.familia_de(d),
        # POR QUÉ SE MARCA. El panel del cooperativista enseña «14 muebles» en un
        # pedido de 20 líneas, y quien lo mira tiene que poder ver cuáles son las
        # otras seis o pensará que le están quitando. Es la MISMA función que
        # decide la comisión, no una copia: si se separaran, esta pantalla
        # explicaría una cosa y la nómina pagaría otra.
        "esMueble": C.es_mueble(d),
    }


def contenido_de(pedido: dict, familias: Optional[dict] = None) -> dict:
    """Lo que lleva un pedido: sus líneas y cuántos muebles suman.

    `muebles` cuenta con el mismo criterio que la comisión (solo muebles: ni
    puertas, ni costados, ni líneas manuales de servicios), y `unidades` cuenta
    todo lo que hay que fabricar y montar. Son dos números distintos a
    propósito, y por eso salen los dos: el de fábrica y el de la nómina.

    UN PEDIDO SIN LÍNEAS NO LLEVA «0 MUEBLES»: es que no se sabe lo que lleva
    (`sinDesglose`), y eso se rotula «?». Un 0 parece un dato (regla 7).
    """
    p = pedido or {}
    crudas = p.get("items") or p.get("lines") or p.get("lineas") or []
    lineas = [linea_de_pedido(l, familias) for l in crudas]
    return {
        "pedidoId": p.get("id") or "",
        "referencia": (p.get("budgetNumber") or p.get("ref") or ""),
        "cliente": (p.get("customerName") or p.get("cliente") or "").strip(),
        "origen": p.get("origenNombre") or p.get("origen") or "",
        "lineas": lineas,
        "unidades": sum(l["unidades"] for l in lineas),
        "muebles": sum(l["unidades"] for l in lineas if l["esMueble"]),
        "sinDesglose": not lineas,
    }
