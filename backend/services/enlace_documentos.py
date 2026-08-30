# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
QUÉ PEDIDO SE HA SERVIDO Y CUÁL SE HA COBRADO, SEGÚN SUS DOCUMENTOS.

`liquidaciones.py` necesita dos fechas: cuándo salió la mercancía y cuándo entró
el dinero. Las esperaba en el propio pedido (`servidoAt`, `cobradoAt`) y no las
escribía nadie, así que NINGÚN pedido consolidaba jamás: todo se quedaba en «en
progreso» para siempre y el área del cooperativista enseñaba una promesa que no
se cumplía nunca.

Pero el ERP sí sabe las dos cosas — en Gestión Comercial, con otros nombres:

    ALBARÁN  (`docType: "albaran"`)  la mercancía ha salido.
    FACTURA  (`docType: "factura"`)  con `status: "paid"`, el dinero ha entrado.

Aquí se hace ese enlace, y solo eso. No decide quién cobra ni cuánto: rellena
las dos fechas y el pendiente, y `liquidaciones` sigue mandando sobre el resto.

CÓMO SE ENLAZA, Y POR QUÉ ASÍ. Por `projectId` primero y por `budgetNumber`
después, que son las dos referencias que el propio gestor ya guarda en cada
documento. No se enlaza por cliente ni por importe: dos pedidos del mismo
cliente por el mismo dinero son cosa de todos los días, y confundirlos aquí es
pagarle una comisión a quien no le toca.

LO QUE NO SE HACE: INVENTARSE UN ENLACE. Si un pedido no tiene ninguna
referencia, no se le atribuye ningún documento — se queda sin servir, que es lo
correcto: mejor que no cobre todavía a que cobre por el albarán de otro. Pagar
de menos se reclama; pagar de más no se devuelve.
"""
from __future__ import annotations

from typing import Iterable, Optional

ALBARAN = "albaran"
FACTURA = "factura"

# La factura solo libera el dinero cuando está pagada del todo. Un cobro a
# cuenta NO libera nada (CLAUDE.md, regla 17).
PAGADA = "paid"

# CÓMO LLAMA CADA PANTALLA A «COBRADO A MEDIAS», Y CUÁNTO LLEVA DENTRO.
#
# Esto salió el 30/08 y explica por qué en COOP salía «Falta la señal» en TODOS
# los pedidos aunque la señal estuviera cobrada y con su comprobante adjunto.
#
# Gestión Comercial ya implementaba la regla 50/50 del master —botón de señal
# con importe, fecha, método y comprobante— pero con su propio vocabulario:
# escribe `status: "partially_paid"` y el importe en `senialImporte`. Aquí se
# leía `cobrado` o `paidAmount`, que NO los escribe nadie. Dos módulos hablando
# del mismo dinero con palabras distintas: la señal se registraba y la
# cooperativa no se enteraba nunca.
#
# Se aceptan todas las formas, y en un solo sitio. Reconocer de más aquí no
# cuesta nada; reconocer de menos deja un cobro sin ver.
A_MEDIAS = ("partially_paid", "partial")

# De dónde sale lo que YA se ha cobrado de una factura que no está pagada del
# todo. `senialImporte` es el de Gestión Comercial; los otros dos, los del
# endpoint de estado.
IMPORTE_COBRADO = ("cobrado", "paidAmount", "senialImporte")


def cobrado_de_la_factura(f: dict) -> float:
    """Cuánto lleva cobrado esa factura, se llame como se llame el campo."""
    d = f or {}
    if (d.get("status") or "") == PAGADA:
        return _num(d.get("total"))
    for clave in IMPORTE_COBRADO:
        if d.get(clave) not in (None, ""):
            return _num(d[clave])
    # Marcada a medias y sin importe: se sabe que algo entró, pero no cuánto.
    # NO se inventa la mitad (regla 7): se devuelve 0 y el pedido sigue
    # apareciendo como pendiente, que es la lectura conservadora.
    return 0.0


def _ref(doc: dict) -> tuple:
    """Las referencias por las que un documento se puede atar a un pedido."""
    d = doc or {}
    return (str(d.get("projectId") or "").strip(),
            str(d.get("budgetNumber") or "").strip())


def _num(v) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def indexar(documentos: Iterable[dict]) -> dict:
    """Los documentos, agrupados por cada referencia que traen.

    Un documento con las dos referencias entra en las dos entradas: así un
    pedido lo encuentra por cualquiera de ellas.
    """
    indice: dict = {}
    for doc in (documentos or []):
        for r in _ref(doc):
            if r:
                indice.setdefault(r, []).append(doc)
    return indice


def documentos_de(pedido: dict, indice: dict) -> list:
    """Los documentos de ESE pedido. Lista vacía si no hay forma de atarlo."""
    vistos, fuera = set(), []
    for r in _ref(pedido):
        if not r:
            continue
        for doc in indice.get(r, []):
            clave = id(doc)
            if clave not in vistos:
                vistos.add(clave)
                fuera.append(doc)
    return fuera


def _fecha_de(doc: dict) -> Optional[str]:
    d = doc or {}
    return d.get("issueDate") or d.get("createdAt") or None


def enriquecer(pedido: dict, indice: dict) -> dict:
    """El pedido con `servidoAt`, `cobradoAt` y `pendienteCobro` puestos.

    NO PISA lo que el pedido ya trae. Si alguien estampó la fecha a mano en el
    pedido, esa manda: el documento es la fuente cuando no hay otra, no una
    corrección de lo que ya se decidió.

    El pendiente sale de las facturas que NO están pagadas. Con eso, un pedido
    facturado a medias no libera comisión aunque tenga su albarán — que es la
    regla de siempre: cobrado es cobrado del todo.
    """
    p = dict(pedido or {})
    docs = documentos_de(p, indice)
    if not docs:
        return p

    albaranes = [d for d in docs if (d.get("docType") or "") == ALBARAN]
    facturas = [d for d in docs if (d.get("docType") or "factura") == FACTURA]

    # SERVIDO: el albarán más reciente. Si hay varias entregas, la mercancía no
    # está fuera del todo hasta la última.
    if not p.get("servidoAt") and not p.get("deliveredAt") and albaranes:
        fechas = sorted([f for f in (_fecha_de(a) for a in albaranes) if f])
        if fechas:
            p["servidoAt"] = fechas[-1]

    if facturas:
        pagadas = [f for f in facturas if (f.get("status") or "") == PAGADA]
        # COBRADO: solo cuando NO queda ninguna factura sin pagar. Una pagada y
        # otra a medias es un pedido a medio cobrar.
        if not p.get("cobradoAt") and not p.get("paidAt") and pagadas and len(pagadas) == len(facturas):
            fechas = sorted([f for f in (x.get("paidAt") or _fecha_de(x) for x in pagadas) if f])
            if fechas:
                p["cobradoAt"] = fechas[-1]
        # Lo que falta por cobrar, para que un cobro a cuenta no libere nada.
        if "pendienteCobro" not in p:
            p["pendienteCobro"] = round(
                sum(max(0.0, _num(f.get("total")) - cobrado_de_la_factura(f))
                    for f in facturas if (f.get("status") or "") != PAGADA), 2)
    return p


def enriquecer_todos(pedidos: Iterable[dict], documentos: Iterable[dict]) -> list:
    indice = indexar(documentos)
    return [enriquecer(p, indice) for p in (pedidos or [])]
