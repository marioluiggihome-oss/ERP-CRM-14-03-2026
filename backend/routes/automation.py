"""
automation.py — Automatizaciones / Workflows del CRM (fase 4): reglas
"disparador → acción" sobre la base de contactos (estilo HubSpot Workflows),
evaluadas bajo demanda (botón "Ejecutar") y al entrar en el CRM.

Disparadores (trigger):
  - lead_sin_contacto : contactos en etapas lead/contacted sin actividad en N días.
  - followup_vencido  : contactos cuyo nextFollowUp ya pasó.
Acciones (action):
  - crear_tarea   : crea una actividad/tarea de seguimiento y pone nextFollowUp.
  - enviar_email  : envía un email de plantilla al contacto (SendGrid).
  - cambiar_etapa : cambia la etapa (stage) del contacto.

Para no repetir acciones se registra cada ejecución en db.automation_events y se
respeta un enfriamiento (cooldownDays, 7 por defecto) por regla+contacto.

Colecciones nuevas: db.automations, db.automation_events.
Reutiliza: db.contacts, db.activities, services.email_service.send_email.
"""
import logging
import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorClient

from services.jwt_service import get_current_user, require_auth

logger = logging.getLogger(__name__)

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "luiggi_home")
_client = AsyncIOMotorClient(MONGO_URL, serverSelectionTimeoutMS=5000, connectTimeoutMS=10000)
db = _client[DB_NAME]

router = APIRouter(tags=["automation"], dependencies=[Depends(require_auth)])

TRIGGERS = ["lead_sin_contacto", "followup_vencido"]
ACCIONES = ["crear_tarea", "enviar_email", "cambiar_etapa"]


def _now():
    return datetime.now(timezone.utc)


def _parse(s):
    try:
        return datetime.fromisoformat(s) if isinstance(s, str) else s
    except Exception:
        return None


def _render(txt, c):
    nombre = (c.get("name") or "").strip()
    reps = {
        "{{nombre}}": nombre or "cliente",
        "{{primernombre}}": nombre.split(" ")[0] if nombre else "hola",
        "{{empresa}}": c.get("company") or "",
        "{{ciudad}}": c.get("city") or "",
        "{{provincia}}": c.get("province") or "",
    }
    out = txt or ""
    for k, v in reps.items():
        out = out.replace(k, str(v))
    return out


# ── CRUD de reglas ──────────────────────────────────────────────────────────
@router.get("/crm/automation/rules")
async def listar_reglas(current_user: dict = Depends(get_current_user)):
    reglas = await db.automations.find({}, {"_id": 0}).sort("createdAt", -1).to_list(200)
    return {"success": True, "rules": reglas, "triggers": TRIGGERS, "acciones": ACCIONES}


@router.post("/crm/automation/rules")
async def crear_regla(payload: dict, current_user: dict = Depends(get_current_user)):
    p = payload or {}
    if p.get("trigger") not in TRIGGERS:
        raise HTTPException(status_code=400, detail="Disparador no válido.")
    if p.get("action") not in ACCIONES:
        raise HTTPException(status_code=400, detail="Acción no válida.")
    doc = {
        "id": f"auto-{uuid.uuid4().hex[:8]}",
        "name": (p.get("name") or "").strip() or "Automatización",
        "active": bool(p.get("active", True)),
        "trigger": p.get("trigger"),
        "action": p.get("action"),
        "params": p.get("params") or {},          # dias, stages, subject/html, texto, diasFollowup, stage
        "cooldownDays": int(p.get("cooldownDays") or 7),
        "createdAt": _now().isoformat(),
        "createdByUserId": current_user.get("id"),
    }
    await db.automations.insert_one(doc)
    doc.pop("_id", None)
    return {"success": True, "rule": doc}


@router.patch("/crm/automation/rules/{rule_id}")
async def actualizar_regla(rule_id: str, payload: dict, current_user: dict = Depends(get_current_user)):
    upd = {}
    for k in ("name", "active", "trigger", "action", "params", "cooldownDays"):
        if k in payload:
            upd[k] = payload[k]
    if not upd:
        raise HTTPException(status_code=400, detail="Nada que actualizar.")
    await db.automations.update_one({"id": rule_id}, {"$set": upd})
    r = await db.automations.find_one({"id": rule_id}, {"_id": 0})
    if not r:
        raise HTTPException(status_code=404, detail="Regla no encontrada.")
    return {"success": True, "rule": r}


@router.delete("/crm/automation/rules/{rule_id}")
async def borrar_regla(rule_id: str, current_user: dict = Depends(get_current_user)):
    await db.automations.delete_one({"id": rule_id})
    return {"success": True}


# ── Evaluación ──────────────────────────────────────────────────────────────
async def _contactos_trigger(regla: dict):
    p = regla.get("params") or {}
    trig = regla.get("trigger")
    now = _now()
    if trig == "lead_sin_contacto":
        dias = int(p.get("dias") or 7)
        stages = p.get("stages") or ["lead", "contacted"]
        limite = now - timedelta(days=dias)
        cs = await db.contacts.find({"stage": {"$in": stages}}, {"_id": 0}).to_list(5000)
        out = []
        for c in cs:
            ref = _parse(c.get("lastContactDate")) or _parse(c.get("createdAt"))
            if ref is None or ref < limite:
                out.append(c)
        return out
    if trig == "followup_vencido":
        cs = await db.contacts.find({"nextFollowUp": {"$nin": [None, ""]}}, {"_id": 0}).to_list(5000)
        return [c for c in cs if (_parse(c.get("nextFollowUp")) and _parse(c["nextFollowUp"]) < now)]
    return []


async def _ya_ejecutada(rule_id, contact_id, cooldown_days):
    corte = _now() - timedelta(days=cooldown_days)
    ev = await db.automation_events.find_one({
        "ruleId": rule_id, "contactId": contact_id,
        "at": {"$gte": corte.isoformat()},
    })
    return ev is not None


async def _ejecutar_accion(regla, contacto, current_user, incluir_email):
    p = regla.get("params") or {}
    accion = regla.get("action")
    if accion == "crear_tarea":
        dias_fu = int(p.get("diasFollowup") or 3)
        due = (_now() + timedelta(days=dias_fu)).date().isoformat()
        act = {
            "id": f"act-{uuid.uuid4().hex[:8]}",
            "activityType": "task",
            "description": _render(p.get("texto") or f"Seguimiento automático: {regla.get('name')}", contacto),
            "contactId": contacto.get("id"),
            "userId": current_user.get("id"),
            "userName": current_user.get("username", "Automatización"),
            "title": regla.get("name"),
            "dueDate": due,
            "completed": False,
            "source": "automation",
            "createdAt": _now().isoformat(),
            "updatedAt": _now().isoformat(),
        }
        await db.activities.insert_one(act)
        await db.contacts.update_one({"id": contacto["id"]}, {"$set": {"nextFollowUp": due, "updatedAt": _now().isoformat()}})
        return True
    if accion == "cambiar_etapa":
        stage = p.get("stage")
        if not stage:
            return False
        await db.contacts.update_one({"id": contacto["id"]}, {"$set": {"stage": stage, "updatedAt": _now().isoformat()}})
        return True
    if accion == "enviar_email":
        if not incluir_email:
            return False  # el envío de emails solo se dispara desde el botón manual
        email = (contacto.get("email") or "").strip()
        if not email:
            return False
        from services.email_service import send_email
        ok = await send_email(
            to_email=email,
            subject=_render(p.get("subject") or "Luiggi Home", contacto),
            html_content=_render(p.get("html") or "", contacto),
        )
        return bool(ok)
    return False


@router.post("/crm/automation/run")
async def ejecutar(payload: dict = None, current_user: dict = Depends(get_current_user)):
    """Evalúa todas las reglas activas y ejecuta sus acciones (respetando el
    enfriamiento). `incluirEmail=false` (por defecto en el disparo automático al
    entrar) omite las acciones de envío de email; el botón manual lo pone a true."""
    incluir_email = bool((payload or {}).get("incluirEmail", False))
    reglas = await db.automations.find({"active": True}, {"_id": 0}).to_list(200)
    resumen = []
    for regla in reglas:
        contactos = await _contactos_trigger(regla)
        hechas, saltadas = 0, 0
        for c in contactos:
            cid = c.get("id")
            if not cid:
                continue
            if await _ya_ejecutada(regla["id"], cid, regla.get("cooldownDays", 7)):
                saltadas += 1
                continue
            ok = await _ejecutar_accion(regla, c, current_user, incluir_email)
            if ok:
                await db.automation_events.insert_one({
                    "ruleId": regla["id"], "contactId": cid,
                    "action": regla.get("action"), "at": _now().isoformat(),
                })
                hechas += 1
            else:
                saltadas += 1
        resumen.append({
            "ruleId": regla["id"], "name": regla.get("name"),
            "trigger": regla.get("trigger"), "action": regla.get("action"),
            "coincidencias": len(contactos), "ejecutadas": hechas, "saltadas": saltadas,
        })
    return {"success": True, "incluirEmail": incluir_email, "resumen": resumen}
