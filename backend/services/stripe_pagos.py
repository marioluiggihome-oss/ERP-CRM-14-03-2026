# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""Cobro con tarjeta de los packs de renders (Stripe Checkout).

Queda INERTE mientras no existan las variables de entorno: sin claves, el
catalogo se sirve igual y el ERP sigue funcionando, pero `disponible()` devuelve
False y el frontend no ofrece el pago con tarjeta. Asi se puede desplegar el
codigo antes de tener la cuenta de Stripe lista.

Variables necesarias (en Railway, servicio del backend):
    STRIPE_SECRET_KEY      sk_live_... (o sk_test_... para pruebas)
    STRIPE_WEBHOOK_SECRET  whsec_...   (del webhook registrado en Stripe)

El PRECIO NUNCA llega del navegador: se toma del catalogo del servidor a partir
del identificador del pack. De lo contrario cualquiera podria comprar 100
renders por un céntimo manipulando la peticion.
"""
import logging
import os

logger = logging.getLogger(__name__)

# Catalogo de packs. Es la UNICA fuente de precios: el cliente manda el id y el
# servidor pone el importe. Los renders comprados no caducan (ai_usage.py).
#
# CUADRADO CON LO QUE DICE LA WEB (master, 15/09/2026: «cuadra los packs de la
# web con los del ERP», y eligiendo que mande la web). Habia TRES listas y no
# coincidian: esta, la del panel del master (`routes/admin.py`) y la publicada
# en `CarpinterosLanding.jsx`. El cliente leia «100 renders, 99 €» y Stripe le
# cobraba 60 €; en el escalon pequeno leia 10 y recibia 20. Siempre a favor del
# cliente y nunca a favor de la casa, sin dar ningun error.
#
# Y LOS IDS DECIAN LA CANTIDAD VIEJA. `pack20` pasando a valer 10 renders es
# una trampa para el siguiente que lo lea, asi que los ids nuevos dicen la
# verdad.
RENDER_PACKS = {
    "pack10":  {"id": "pack10",  "name": "Pack 10 renders",  "renders": 10,  "price": 15, "color": "#C4622D"},
    "pack30":  {"id": "pack30",  "name": "Pack 30 renders",  "renders": 30,  "price": 39, "color": "#0891b2"},
    "pack100": {"id": "pack100", "name": "Pack 100 renders", "renders": 100, "price": 99, "color": "#059669"},
}

# PACKS RETIRADOS: NO SE VENDEN, PERO SE SIGUEN RESOLVIENDO.
#
# Un cliente que pago `pack20` cinco minutos antes de este despliegue recibe el
# webhook DESPUES. Si el id ya no existiera, `RENDER_PACKS.get("pack20")` daria
# None, `renders` saldria 0 y el cliente habria PAGADO SIN RECIBIR NADA — sin
# error, sin aviso y sin que nadie lo relacione con este cambio. Aqui se les
# abona lo que SE LES VENDIO, no lo que cuesta hoy.
#
# `pack100` no hace falta ponerlo: el id y el numero de renders no cambian, y
# el precio solo se usa al ABRIR la sesion de pago, nunca al abonarla.
PACKS_RETIRADOS = {
    "pack20": {"id": "pack20", "name": "Pack 20 renders", "renders": 20, "price": 15, "color": "#C4622D"},
    "pack50": {"id": "pack50", "name": "Pack 50 renders", "renders": 50, "price": 35, "color": "#0891b2"},
}


def pack_por_id(pack_id: str) -> dict:
    """El pack con ese id, mirando tambien los retirados. {} si no existe.

    Se usa para ABONAR (webhook, concesion del master). Para VENDER se usa
    `RENDER_PACKS` a secas: un pack retirado no vuelve al escaparate.
    """
    clave = (pack_id or "").strip()
    return RENDER_PACKS.get(clave) or PACKS_RETIRADOS.get(clave) or {}

MONEDA = "eur"
IVA_PCT = 21  # Los precios del catalogo son SIN IVA, igual que los planes.


def _clave_secreta() -> str:
    return (os.environ.get("STRIPE_SECRET_KEY") or "").strip()


def _clave_webhook() -> str:
    return (os.environ.get("STRIPE_WEBHOOK_SECRET") or "").strip()


def disponible() -> bool:
    """¿Se puede cobrar con tarjeta ahora mismo?"""
    if not _clave_secreta():
        return False
    try:
        import stripe  # noqa: F401
        return True
    except Exception:
        logger.warning("stripe: la libreria no esta instalada")
        return False


def _stripe():
    import stripe
    stripe.api_key = _clave_secreta()
    return stripe


def precio_con_iva(pack: dict) -> float:
    return round(float(pack["price"]) * (1 + IVA_PCT / 100), 2)


def crear_checkout(pack_id: str, user_id: str, email: str, url_ok: str, url_ko: str,
                    plataforma: str = "cooperativa", organization_id: str = "") -> dict:
    """Abre una sesion de pago y devuelve la URL a la que mandar al cliente.

    En los metadatos van el usuario y el pack para que el webhook sepa a quien
    abonar los renders. No se abona nada aqui: solo cuando Stripe confirma el
    cobro (ver `leer_evento`).
    """
    pack = RENDER_PACKS.get(pack_id)
    if not pack:
        raise ValueError(f"El pack '{pack_id}' no existe")
    if not disponible():
        raise RuntimeError("El pago con tarjeta no esta configurado en el servidor")

    stripe = _stripe()
    sesion = stripe.checkout.Session.create(
        mode="payment",
        line_items=[{
            "quantity": 1,
            "price_data": {
                "currency": MONEDA,
                # Stripe trabaja en centimos y con enteros.
                "unit_amount": int(round(precio_con_iva(pack) * 100)),
                "product_data": {
                    "name": pack["name"],
                    "description": f"{pack['renders']} renders de IA · no caducan",
                },
            },
        }],
        success_url=url_ok,
        cancel_url=url_ko,
        customer_email=email or None,
        metadata={
            "user_id": str(user_id),
            "pack_id": pack["id"],
            "renders": str(pack["renders"]),
            "plataforma": str(plataforma or "cooperativa"),
            "organization_id": str(organization_id or ""),
        },
        # Un mismo usuario comprando el mismo pack dos veces SI son dos compras
        # distintas, asi que no se fija clave de idempotencia aqui: la
        # proteccion contra duplicados va en el webhook, por id de sesion.
    )
    return {"url": sesion.url, "sessionId": sesion.id}


def leer_evento(cuerpo: bytes, firma: str) -> dict:
    """Valida la firma del webhook y devuelve el evento.

    La firma es lo unico que demuestra que la llamada viene de Stripe: sin esta
    comprobacion, cualquiera podria regalarse renders llamando al webhook.
    """
    secreto = _clave_webhook()
    if not secreto:
        raise RuntimeError("Falta STRIPE_WEBHOOK_SECRET")
    stripe = _stripe()
    return stripe.Webhook.construct_event(cuerpo, firma, secreto)


def datos_de_pago(evento: dict) -> dict:
    """Del evento de Stripe saca a quien abonar y cuanto. {} si no aplica."""
    if (evento or {}).get("type") != "checkout.session.completed":
        return {}
    sesion = (evento.get("data") or {}).get("object") or {}
    if sesion.get("payment_status") != "paid":
        return {}
    meta = sesion.get("metadata") or {}
    # `pack_por_id` y no `RENDER_PACKS`: un pago en vuelo con un id retirado
    # tiene que abonar lo que se vendio (ver PACKS_RETIRADOS).
    pack = pack_por_id(meta.get("pack_id") or "")
    # Los renders se toman del catalogo del servidor, no de los metadatos, por
    # si alguien manipulara la sesion.
    renders = int(pack["renders"]) if pack else 0
    return {
        "sessionId": sesion.get("id") or "",
        "user_id": str(meta.get("user_id") or ""),
        "pack_id": meta.get("pack_id") or "",
        "renders": renders,
        "importe": round(float(sesion.get("amount_total") or 0) / 100, 2),
        "email": sesion.get("customer_email") or "",
        "plataforma": str(meta.get("plataforma") or "cooperativa"),
        "organization_id": str(meta.get("organization_id") or ""),
    }
