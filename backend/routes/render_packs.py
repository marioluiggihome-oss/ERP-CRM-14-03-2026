# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""Recarga de renders por el propio cliente (packs de IA).

Hasta ahora solo el master podia conceder packs, asi que un cliente que se
quedaba sin renders un sabado tenia que esperar. Aqui se compra con tarjeta y el
saldo se abona solo.

El saldo comprado NO caduca: se guarda en `ai_credit_balance` (ver
services/ai_usage.py). Se gasta primero el cupo del plan, que si caduca.
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from datetime import datetime, timezone
import logging
import os
import uuid

from services.db_client import get_db
from services.jwt_service import require_auth
from services import stripe_pagos

logger = logging.getLogger(__name__)
router = APIRouter(tags=["render-packs"])


def _url_base_front() -> str:
    """A donde devolver al cliente tras pagar."""
    origenes = (os.environ.get("CORS_ORIGINS") or "").split(",")
    primero = next((o.strip() for o in origenes if o.strip()), "")
    return primero or "https://erp.luiggihome.es"


@router.get("/render-packs/catalogo")
async def catalogo(user: dict = Depends(require_auth)):
    """Packs a la venta y si se puede pagar con tarjeta ahora mismo.

    Si Stripe no esta configurado se devuelve igualmente el catalogo con
    `pagoTarjeta: false`, para que el ERP pueda enseñar los precios y decir que
    la recarga se pide al administrador.
    """
    packs = []
    for p in stripe_pagos.RENDER_PACKS.values():
        packs.append({
            **p,
            "precioSinIva": p["price"],
            "precioConIva": stripe_pagos.precio_con_iva(p),
            "porRender": round(p["price"] / p["renders"], 3),
        })
    packs.sort(key=lambda x: x["renders"])
    return {
        "success": True,
        "packs": packs,
        "iva": stripe_pagos.IVA_PCT,
        "pagoTarjeta": stripe_pagos.disponible(),
        "caducan": False,
    }


@router.post("/render-packs/comprar")
async def comprar(payload: dict, user: dict = Depends(require_auth)):
    """Abre la pasarela de pago para el pack pedido y devuelve la URL.

    No se abona nada aqui: los renders se suman cuando Stripe confirma el cobro
    en el webhook. Si se abonaran ahora, bastaria con abrir la pasarela y no
    pagar para llevarselos gratis.
    """
    pack_id = str((payload or {}).get("packId") or "").strip()
    if pack_id not in stripe_pagos.RENDER_PACKS:
        raise HTTPException(status_code=400, detail="Pack no valido")
    if not stripe_pagos.disponible():
        raise HTTPException(
            status_code=503,
            detail="El pago con tarjeta todavia no esta activado. Pide la recarga al administrador.",
        )
    base = _url_base_front()
    try:
        sesion = stripe_pagos.crear_checkout(
            pack_id=pack_id,
            user_id=user.get("id") or "",
            email=user.get("email") or "",
            url_ok=f"{base}/?recarga=ok",
            url_ko=f"{base}/?recarga=cancelada",
        )
    except Exception as e:
        logger.error("render-packs comprar: %s", e)
        raise HTTPException(status_code=502, detail="No se pudo abrir la pasarela de pago. Reintentalo.")
    return {"success": True, **sesion}


@router.post("/render-packs/webhook")
async def webhook(request: Request):
    """Aviso de Stripe cuando un pago se completa. Ruta PUBLICA a proposito:
    Stripe no lleva sesion del ERP. Lo que la protege es la FIRMA del evento.
    """
    firma = request.headers.get("stripe-signature", "")
    cuerpo = await request.body()
    try:
        evento = stripe_pagos.leer_evento(cuerpo, firma)
    except Exception as e:
        # Firma invalida = no viene de Stripe. 400 para que no lo reintente.
        logger.warning("render-packs webhook: firma rechazada: %s", e)
        raise HTTPException(status_code=400, detail="Firma no valida")

    datos = stripe_pagos.datos_de_pago(evento)
    if not datos or not datos.get("user_id") or datos.get("renders", 0) <= 0:
        return {"received": True, "ignorado": True}

    db = get_db()
    # Stripe REINTENTA los webhooks. Sin esto, un reintento abonaria el pack dos
    # veces. El id de sesion es unico por compra.
    ya = await db.render_pack_purchases.find_one({"sessionId": datos["sessionId"]}, {"_id": 0, "id": 1})
    if ya:
        return {"received": True, "duplicado": True}

    from services.ai_usage import añadir_saldo
    saldo = await añadir_saldo(datos["user_id"], datos["renders"])
    await db.render_pack_purchases.insert_one({
        "id": f"pack-{uuid.uuid4().hex[:8]}",
        "sessionId": datos["sessionId"],
        "user_id": datos["user_id"],
        "renders": datos["renders"],
        "pack": datos["pack_id"],
        "price": datos["importe"],
        "name": (stripe_pagos.RENDER_PACKS.get(datos["pack_id"]) or {}).get("name", ""),
        "email": datos.get("email", ""),
        "origen": "stripe",
        "grantedBy": "",
        "createdAt": datetime.now(timezone.utc).isoformat(),
    })
    logger.info("render-packs: abonados %d renders a %s (saldo %d)",
                datos["renders"], datos["user_id"], saldo)
    return {"received": True, "renders": datos["renders"], "saldo": saldo}


@router.get("/render-packs/mis-compras")
async def mis_compras(user: dict = Depends(require_auth)):
    """Historico de packs comprados por el usuario."""
    db = get_db()
    compras = await db.render_pack_purchases.find(
        {"user_id": str(user.get("id") or "")}, {"_id": 0}
    ).sort("createdAt", -1).to_list(100)
    return {"success": True, "compras": compras, "total": len(compras)}
