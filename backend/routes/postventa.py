"""
postventa.py — Service Hub del CRM (fase 2): TICKETS DE POSTVENTA (incidencias de
montaje, garantías, reclamaciones) con estados, prioridad, SLA y comentarios.

Es la pata de "Service Hub" que faltaba frente a un HubSpot: registrar una
incidencia del cliente tras la venta, asignarla, seguir su estado con un SLA de
resolución y dejar traza de las comunicaciones.

Colecciones nuevas: db.tickets.
Reutiliza: db.contacts (para vincular el cliente).
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
_client = AsyncIOMotorClient(MONGO_URL)
db = _client[DB_NAME]

router = APIRouter(tags=["postventa"], dependencies=[Depends(require_auth)])

ESTADOS = ["abierto", "en_proceso", "espera_cliente", "resuelto", "cerrado"]
PRIORIDADES = ["baja", "media", "alta", "urgente"]
# SLA por prioridad (horas hasta el vencimiento objetivo de resolución).
_SLA_HORAS = {"urgente": 8, "alta": 24, "media": 72, "baja": 168}


def _now():
    return datetime.now(timezone.utc)


@router.get("/crm/tickets")
async def listar_tickets(estado: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    q = {}
    if estado and estado in ESTADOS:
        q["estado"] = estado
    tickets = await db.tickets.find(q, {"_id": 0}).sort("createdAt", -1).to_list(500)
    # Marca vencidos (SLA superado y no resuelto/cerrado).
    now = _now()
    for t in tickets:
        due = t.get("slaVence")
        t["vencido"] = bool(due and t.get("estado") not in ("resuelto", "cerrado")
                            and _parse(due) and _parse(due) < now)
    return {"success": True, "tickets": tickets, "estados": ESTADOS, "prioridades": PRIORIDADES}


def _parse(s):
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None


@router.get("/crm/tickets/stats")
async def stats_tickets(current_user: dict = Depends(get_current_user)):
    tickets = await db.tickets.find({}, {"_id": 0, "estado": 1, "slaVence": 1}).to_list(2000)
    now = _now()
    abiertos = sum(1 for t in tickets if t.get("estado") not in ("resuelto", "cerrado"))
    vencidos = sum(1 for t in tickets if t.get("estado") not in ("resuelto", "cerrado")
                   and t.get("slaVence") and _parse(t["slaVence"]) and _parse(t["slaVence"]) < now)
    por_estado = {}
    for t in tickets:
        por_estado[t.get("estado", "abierto")] = por_estado.get(t.get("estado", "abierto"), 0) + 1
    return {"success": True, "total": len(tickets), "abiertos": abiertos, "vencidos": vencidos, "porEstado": por_estado}


@router.post("/crm/tickets")
async def crear_ticket(payload: dict, current_user: dict = Depends(get_current_user)):
    p = payload or {}
    asunto = (p.get("asunto") or "").strip()
    if not asunto:
        raise HTTPException(status_code=400, detail="Falta el asunto de la incidencia.")
    prioridad = p.get("prioridad") if p.get("prioridad") in PRIORIDADES else "media"
    now = _now()
    sla = now + timedelta(hours=_SLA_HORAS.get(prioridad, 72))
    # Nº correlativo legible.
    n = await db.tickets.count_documents({}) + 1
    doc = {
        "id": f"tick-{uuid.uuid4().hex[:8]}",
        "numero": f"PV-{n:05d}",
        "asunto": asunto,
        "descripcion": p.get("descripcion") or "",
        "tipo": p.get("tipo") or "incidencia",   # incidencia | garantia | reclamacion | consulta
        "prioridad": prioridad,
        "estado": "abierto",
        "contactId": p.get("contactId") or None,
        "contactNombre": p.get("contactNombre") or "",
        "pedidoRef": p.get("pedidoRef") or "",
        "assignedToId": p.get("assignedToId") or current_user.get("id"),
        "assignedToNombre": p.get("assignedToNombre") or current_user.get("username", ""),
        "slaVence": sla.isoformat(),
        "comentarios": [],
        "createdAt": now.isoformat(),
        "updatedAt": now.isoformat(),
        "createdByUserId": current_user.get("id"),
        "createdByUsername": current_user.get("username", ""),
    }
    await db.tickets.insert_one(doc)
    doc.pop("_id", None)
    return {"success": True, "ticket": doc}


@router.patch("/crm/tickets/{ticket_id}")
async def actualizar_ticket(ticket_id: str, payload: dict, current_user: dict = Depends(get_current_user)):
    t = await db.tickets.find_one({"id": ticket_id}, {"_id": 0})
    if not t:
        raise HTTPException(status_code=404, detail="Ticket no encontrado.")
    upd = {"updatedAt": _now().isoformat()}
    for campo in ("asunto", "descripcion", "tipo", "contactId", "contactNombre", "pedidoRef", "assignedToId", "assignedToNombre"):
        if campo in payload:
            upd[campo] = payload[campo]
    if payload.get("estado") in ESTADOS:
        upd["estado"] = payload["estado"]
        if payload["estado"] in ("resuelto", "cerrado") and not t.get("resueltoAt"):
            upd["resueltoAt"] = _now().isoformat()
    if payload.get("prioridad") in PRIORIDADES:
        upd["prioridad"] = payload["prioridad"]
        # Recalcular SLA si sigue abierto.
        if t.get("estado") not in ("resuelto", "cerrado"):
            base = _parse(t.get("createdAt")) or _now()
            upd["slaVence"] = (base + timedelta(hours=_SLA_HORAS[payload["prioridad"]])).isoformat()
    await db.tickets.update_one({"id": ticket_id}, {"$set": upd})
    nuevo = await db.tickets.find_one({"id": ticket_id}, {"_id": 0})
    return {"success": True, "ticket": nuevo}


@router.post("/crm/tickets/{ticket_id}/comentario")
async def comentar_ticket(ticket_id: str, payload: dict, current_user: dict = Depends(get_current_user)):
    texto = (payload or {}).get("texto", "").strip()
    if not texto:
        raise HTTPException(status_code=400, detail="Comentario vacío.")
    com = {
        "id": f"c-{uuid.uuid4().hex[:6]}",
        "texto": texto,
        "autor": current_user.get("username", ""),
        "autorId": current_user.get("id"),
        "fecha": _now().isoformat(),
    }
    await db.tickets.update_one({"id": ticket_id}, {"$push": {"comentarios": com}, "$set": {"updatedAt": _now().isoformat()}})
    return {"success": True, "comentario": com}


@router.delete("/crm/tickets/{ticket_id}")
async def borrar_ticket(ticket_id: str, current_user: dict = Depends(get_current_user)):
    await db.tickets.delete_one({"id": ticket_id})
    return {"success": True}
