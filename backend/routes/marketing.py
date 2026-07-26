"""
marketing.py — Marketing Hub del CRM (fase 1): SEGMENTACIÓN de la base de
contactos + CAMPAÑAS de email (envío por SendGrid) con estadísticas básicas.

Aporta al ERP la pata de "Marketing Hub" que hasta ahora faltaba frente a un
HubSpot: definir un segmento con filtros sobre los contactos del CRM, previsualizar
a cuántos alcanza, redactar una campaña con variables ({{nombre}}, {{empresa}}) y
enviarla a todos los contactos con email del segmento, guardando el resultado.

Colecciones nuevas: db.campaigns.
Reutiliza: db.contacts (CRM), services.email_service.send_email (SendGrid).
"""
import logging
import os
import re
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorClient

from services.jwt_service import get_current_user, require_auth

logger = logging.getLogger(__name__)

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "luiggi_home")
_client = AsyncIOMotorClient(MONGO_URL)
db = _client[DB_NAME]

router = APIRouter(tags=["marketing"], dependencies=[Depends(require_auth)])


# ── Segmentación ────────────────────────────────────────────────────────────
def _build_query(filtros: dict) -> dict:
    """Construye la query de MongoDB para un segmento a partir de los filtros.
    Todos los filtros son opcionales; se combinan con AND. Campos soportados del
    contacto: segment, stage, status, source, province, city, businessType, tags,
    valueMin/valueMax (sobre `value`), conEmail."""
    q = {}
    f = filtros or {}

    def eq(campo, clave=None):
        v = f.get(clave or campo)
        if v not in (None, "", "todos", "all"):
            q[campo] = v

    eq("segment")
    eq("stage")
    eq("status")
    eq("source")
    eq("businessType")
    # Provincia / ciudad: coincidencia parcial insensible a mayúsculas.
    for campo in ("province", "city"):
        v = f.get(campo)
        if v:
            q[campo] = {"$regex": re.escape(str(v)), "$options": "i"}
    # Etiquetas: el contacto debe tener alguna de las etiquetas pedidas.
    tags = f.get("tags")
    if tags:
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",") if t.strip()]
        if tags:
            q["tags"] = {"$in": tags}
    # Valor (importe potencial) mínimo/máximo.
    vmin, vmax = f.get("valueMin"), f.get("valueMax")
    if vmin not in (None, "") or vmax not in (None, ""):
        rango = {}
        if vmin not in (None, ""):
            rango["$gte"] = float(vmin)
        if vmax not in (None, ""):
            rango["$lte"] = float(vmax)
        q["value"] = rango
    # Solo contactos con email (por defecto sí, para campañas de email).
    if f.get("conEmail", True):
        q["email"] = {"$nin": ["", None]}
    return q


async def _contactos_segmento(filtros: dict, proj=None, limit: int = 5000):
    query = _build_query(filtros)
    cur = db.contacts.find(query, proj or {"_id": 0, "id": 1, "name": 1, "email": 1, "company": 1})
    return await cur.to_list(limit)


@router.post("/crm/marketing/segment/preview")
async def segment_preview(payload: dict, current_user: dict = Depends(get_current_user)):
    """Previsualiza un segmento: número de contactos y una muestra."""
    filtros = (payload or {}).get("filtros") or payload or {}
    contactos = await _contactos_segmento(filtros)
    con_email = [c for c in contactos if (c.get("email") or "").strip()]
    return {
        "success": True,
        "total": len(contactos),
        "conEmail": len(con_email),
        "muestra": con_email[:12],
    }


# ── Campañas ────────────────────────────────────────────────────────────────
def _render(plantilla: str, contacto: dict) -> str:
    """Sustituye variables {{nombre}} {{empresa}} {{ciudad}} {{provincia}} en el
    cuerpo/asunto con los datos del contacto."""
    nombre = (contacto.get("name") or "").strip()
    primer = nombre.split(" ")[0] if nombre else ""
    reps = {
        "{{nombre}}": nombre or "cliente",
        "{{primernombre}}": primer or "hola",
        "{{empresa}}": contacto.get("company") or "",
        "{{ciudad}}": contacto.get("city") or "",
        "{{provincia}}": contacto.get("province") or "",
    }
    out = plantilla or ""
    for k, v in reps.items():
        out = out.replace(k, str(v))
    return out


@router.post("/crm/marketing/campaigns")
async def crear_campaign(payload: dict, current_user: dict = Depends(get_current_user)):
    """Crea (o guarda como borrador) una campaña de email."""
    p = payload or {}
    if not (p.get("subject") or "").strip():
        raise HTTPException(status_code=400, detail="Falta el asunto de la campaña.")
    doc = {
        "id": f"camp-{uuid.uuid4().hex[:8]}",
        "name": (p.get("name") or "").strip() or (p.get("subject") or "Campaña"),
        "subject": p.get("subject") or "",
        "html": p.get("html") or "",
        "filtros": p.get("filtros") or {},
        "status": "borrador",
        "sentCount": 0,
        "failCount": 0,
        "recipients": [],
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "sentAt": None,
        "createdByUserId": current_user.get("id"),
        "createdByUsername": current_user.get("username", ""),
    }
    await db.campaigns.insert_one(doc)
    doc.pop("_id", None)
    return {"success": True, "campaign": doc}


@router.get("/crm/marketing/campaigns")
async def listar_campaigns(current_user: dict = Depends(get_current_user)):
    camps = await db.campaigns.find({}, {"_id": 0}).sort("createdAt", -1).to_list(200)
    return {"success": True, "campaigns": camps}


@router.get("/crm/marketing/campaigns/{campaign_id}")
async def detalle_campaign(campaign_id: str, current_user: dict = Depends(get_current_user)):
    c = await db.campaigns.find_one({"id": campaign_id}, {"_id": 0})
    if not c:
        raise HTTPException(status_code=404, detail="Campaña no encontrada.")
    return {"success": True, "campaign": c}


@router.delete("/crm/marketing/campaigns/{campaign_id}")
async def borrar_campaign(campaign_id: str, current_user: dict = Depends(get_current_user)):
    await db.campaigns.delete_one({"id": campaign_id})
    return {"success": True}


@router.post("/crm/marketing/campaigns/{campaign_id}/send")
async def enviar_campaign(campaign_id: str, payload: dict = None, current_user: dict = Depends(get_current_user)):
    """Envía la campaña a todos los contactos con email del segmento. Devuelve el
    recuento de envíos correctos/fallidos. Idempotente por estado (no reenvía una
    ya enviada salvo que se fuerce)."""
    c = await db.campaigns.find_one({"id": campaign_id}, {"_id": 0})
    if not c:
        raise HTTPException(status_code=404, detail="Campaña no encontrada.")
    forzar = bool((payload or {}).get("forzar"))
    if c.get("status") == "enviada" and not forzar:
        raise HTTPException(status_code=409, detail="La campaña ya se envió. Usa 'forzar' para reenviar.")

    from services.email_service import send_email
    if not os.environ.get("SENDGRID_API_KEY"):
        raise HTTPException(status_code=503, detail="Email no configurado (falta SENDGRID_API_KEY). Contacta con el administrador.")

    contactos = await _contactos_segmento(
        c.get("filtros") or {},
        proj={"_id": 0, "id": 1, "name": 1, "email": 1, "company": 1, "city": 1, "province": 1},
    )
    destinatarios = [c2 for c2 in contactos if (c2.get("email") or "").strip()]
    if not destinatarios:
        raise HTTPException(status_code=422, detail="El segmento no tiene contactos con email.")

    ok, fail, enviados = 0, 0, []
    for ct in destinatarios:
        try:
            asunto = _render(c.get("subject") or "", ct)
            cuerpo = _render(c.get("html") or "", ct)
            sent = await send_email(to_email=ct["email"], subject=asunto, html_content=cuerpo)
            if sent:
                ok += 1
                enviados.append({"id": ct.get("id"), "email": ct["email"], "name": ct.get("name")})
            else:
                fail += 1
        except Exception as e:
            logger.warning("campaña %s envío a %s: %s", campaign_id, ct.get("email"), e)
            fail += 1

    await db.campaigns.update_one(
        {"id": campaign_id},
        {"$set": {
            "status": "enviada",
            "sentCount": ok,
            "failCount": fail,
            "recipients": enviados,
            "sentAt": datetime.now(timezone.utc).isoformat(),
        }},
    )
    return {"success": True, "sentCount": ok, "failCount": fail, "total": len(destinatarios)}
