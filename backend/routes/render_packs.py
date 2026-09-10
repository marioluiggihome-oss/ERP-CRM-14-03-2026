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
async def comprar(request: Request, payload: dict, user: dict = Depends(require_auth)):
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
    from services.plataformas import plataforma_entrada, plataforma_de, organizacion_de
    entry = plataforma_entrada(request.headers.get("x-platform-entry"))
    plataforma = entry if entry in {"carpinter", "studio3k"} else plataforma_de(user)
    organization_id = organizacion_de(user)
    base = _url_base_front()
    if plataforma == "carpinter":
        base = base.rstrip("/") + "/carp/app"
    elif plataforma == "studio3k":
        base = base.rstrip("/") + "/s3k/app"
    try:
        sesion = stripe_pagos.crear_checkout(
            pack_id=pack_id,
            user_id=user.get("id") or "",
            email=user.get("email") or "",
            url_ok=f"{base}/?recarga=ok",
            url_ko=f"{base}/?recarga=cancelada",
            plataforma=plataforma,
            organization_id=organization_id,
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

    # ─── QUE UNA COMPRA ABONE UNA VEZ, Y SOLO UNA ────────────────────────────
    #
    # Stripe REINTENTA los webhooks, y puede entregar el mismo evento DOS VECES
    # A LA VEZ. Aqui habia un «mirar si ya esta y si no abonar», que parece
    # bastar y no basta: entre MIRAR y ABONAR caben las dos entregas, las dos
    # ven que no esta, y las dos abonan. Un pack de 20 se convierte en 40.
    # Encontrado en la auditoria externa del 10/09/2026, reproducido con dos
    # entregas simultaneas.
    #
    # SE ARREGLA CAMBIANDO EL ORDEN, no anadiendo comprobaciones. Primero se
    # RESERVA la compra con un `update_one(upsert=True)` sobre el id de sesion:
    # es UNA sola operacion atomica en Mongo, asi que de dos entregas a la vez
    # solo una la crea. Y solo la que la crea abona.
    #
    # EL ABONO SE MARCA APARTE (`abonadoAt`), y eso cierra la otra forma de
    # repetir: si el servidor se cae entre reservar y abonar, el reintento de
    # Stripe encuentra la reserva SIN abonar y termina el trabajo. Con el orden
    # de antes, una caida en ese hueco dejaba el saldo dado y la compra sin
    # registrar, asi que el siguiente reintento volvia a abonar.
    #
    # Un indice unico en `sessionId` NO habria bastado: llega despues del abono,
    # o sea que impide el segundo REGISTRO pero no deshace los renders ya dados.
    reserva = await db.render_pack_purchases.update_one(
        {"sessionId": datos["sessionId"]},
        {"$setOnInsert": {
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
            "plataforma": datos.get("plataforma") or "cooperativa",
            "organizationId": datos.get("organization_id") or "",
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "abonadoAt": None,
        }},
        upsert=True,
    )

    if reserva.upserted_id is None:
        # Ya existia: o se abono del todo, o se quedo a medias por una caida.
        previa = await db.render_pack_purchases.find_one(
            {"sessionId": datos["sessionId"]}, {"_id": 0, "abonadoAt": 1}) or {}
        if previa.get("abonadoAt"):
            return {"received": True, "duplicado": True}
        logger.warning(
            "render-packs webhook: la compra %s estaba reservada SIN abonar "
            "(caida entre reservar y abonar). Se termina ahora.",
            datos["sessionId"])

    from services.ai_usage import añadir_saldo
    saldo = await añadir_saldo(datos["user_id"], datos["renders"])
    await db.render_pack_purchases.update_one(
        {"sessionId": datos["sessionId"]},
        {"$set": {"abonadoAt": datetime.now(timezone.utc).isoformat()}},
    )
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
