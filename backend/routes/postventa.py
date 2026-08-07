# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
postventa.py — Service Hub del CRM (fase 2): TICKETS DE POSTVENTA (incidencias de
montaje, garantías, reclamaciones) con estados, prioridad, SLA y comentarios.

Es la pata de "Service Hub" que faltaba frente a un HubSpot: registrar una
incidencia del cliente tras la venta, asignarla, seguir su estado con un SLA de
resolución y dejar traza de las comunicaciones.

Colecciones nuevas: _get_db().tickets.
Reutiliza: _get_db().contacts (para vincular el cliente).
"""
import logging
import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends

from services.jwt_service import get_current_user, require_auth
from services.db_client import get_db as _get_db

logger = logging.getLogger(__name__)


router = APIRouter(tags=["postventa"], dependencies=[Depends(require_auth)])

ESTADOS = ["abierto", "en_proceso", "espera_cliente", "resuelto", "cerrado"]
PRIORIDADES = ["baja", "media", "alta", "urgente"]
# SLA por prioridad (horas hasta el vencimiento objetivo de resolución).
_SLA_HORAS = {"urgente": 8, "alta": 24, "media": 72, "baja": 168}

# ─── CAUSA de la incidencia ──────────────────────────────────────────────────
# El "tipo" dice QUÉ es (incidencia, garantía, reclamación). La CAUSA dice DE
# DÓNDE VIENE, que es lo único que permite corregir el origen en vez de apagar
# fuegos. Sin este campo la pregunta "¿de dónde salen nuestros fallos?" solo se
# puede contestar por intuición, y la intuición siempre culpa a fábrica.
CAUSAS = {
    "pieza_incorrecta":  "Pieza incorrecta",
    "pieza_danada":      "Pieza dañada",
    "medida_incorrecta": "Medida incorrecta",
    "falta_material":    "Falta material",
    "error_diseno":      "Error de diseño",
    "error_fabricacion": "Error de fabricación",
    "error_proveedor":   "Error de proveedor",
    "error_medicion":    "Error de medición",
    "problema_obra":     "Problema de obra",
    "cambio_cliente":    "Cambio pedido por el cliente",
}


def _now():
    return datetime.now(timezone.utc)


def falta_causa_para_cerrar(estado_nuevo, causa_final) -> bool:
    """True si se intenta CERRAR sin haber dicho de dónde vino el fallo.

    Solo cierra; los demás estados no la exigen. Función pura, para poder
    probar la regla sin levantar la base de datos.
    """
    return estado_nuevo == "cerrado" and causa_final not in CAUSAS


@router.get("/crm/tickets")
async def listar_tickets(estado: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    q = {}
    if estado and estado in ESTADOS:
        q["estado"] = estado
    tickets = await _get_db().tickets.find(q, {"_id": 0}).sort("createdAt", -1).to_list(500)
    # Marca vencidos (SLA superado y no resuelto/cerrado).
    now = _now()
    for t in tickets:
        due = t.get("slaVence")
        t["vencido"] = bool(due and t.get("estado") not in ("resuelto", "cerrado")
                            and _parse(due) and _parse(due) < now)
    return {"success": True, "tickets": tickets, "estados": ESTADOS,
            "prioridades": PRIORIDADES, "causas": CAUSAS}


def _parse(s):
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None


def resumen_causas(tickets):
    """Reparto de incidencias por CAUSA, en bruto y en porcentaje.

    El porcentaje se calcula SOLO sobre las incidencias clasificadas, y se
    devuelve aparte cuántas no lo están (`sinCausa`). Repartir el 100 % entre
    las clasificadas mientras la mitad está sin clasificar daría un número que
    parece exacto y no lo es: si hay 10 tickets y solo 2 llevan causa, decir
    "50 % son de medición" sobre 1 de esos 2 es una cifra inventada con forma
    de dato. Quien lea el informe tiene que ver sobre cuántos se calcula.

    Función pura (sin base de datos) para poder probarla.
    """
    por_causa, sin_causa = {}, 0
    for t in tickets:
        c = t.get("causa")
        if c in CAUSAS:
            por_causa[c] = por_causa.get(c, 0) + 1
        else:
            sin_causa += 1

    clasificados = sum(por_causa.values())
    porcentajes = {
        c: round(n * 100 / clasificados, 1) for c, n in por_causa.items()
    } if clasificados else {}

    orden = sorted(por_causa.items(), key=lambda kv: (-kv[1], kv[0]))
    return {
        "porCausa": por_causa,
        "porCausaPct": porcentajes,
        "clasificados": clasificados,
        "sinCausa": sin_causa,
        "principal": orden[0][0] if orden else None,
        "etiquetas": CAUSAS,
    }


@router.get("/crm/tickets/stats")
async def stats_tickets(current_user: dict = Depends(get_current_user)):
    tickets = await _get_db().tickets.find(
        {}, {"_id": 0, "estado": 1, "slaVence": 1, "causa": 1}).to_list(2000)
    now = _now()
    abiertos = sum(1 for t in tickets if t.get("estado") not in ("resuelto", "cerrado"))
    vencidos = sum(1 for t in tickets if t.get("estado") not in ("resuelto", "cerrado")
                   and t.get("slaVence") and _parse(t["slaVence"]) and _parse(t["slaVence"]) < now)
    por_estado = {}
    for t in tickets:
        por_estado[t.get("estado", "abierto")] = por_estado.get(t.get("estado", "abierto"), 0) + 1
    return {"success": True, "total": len(tickets), "abiertos": abiertos, "vencidos": vencidos,
            "porEstado": por_estado, **resumen_causas(tickets)}


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
    n = await _get_db().tickets.count_documents({}) + 1
    doc = {
        "id": f"tick-{uuid.uuid4().hex[:8]}",
        "numero": f"PV-{n:05d}",
        "asunto": asunto,
        "descripcion": p.get("descripcion") or "",
        "tipo": p.get("tipo") or "incidencia",   # incidencia | garantia | reclamacion | consulta
        # La causa NO se pide al abrir: cuando entra la incidencia casi nunca se
        # sabe de dónde viene. Se exige al CERRAR, que es cuando ya se sabe.
        "causa": p.get("causa") if p.get("causa") in CAUSAS else None,
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
    await _get_db().tickets.insert_one(doc)
    doc.pop("_id", None)
    return {"success": True, "ticket": doc}


@router.patch("/crm/tickets/{ticket_id}")
async def actualizar_ticket(ticket_id: str, payload: dict, current_user: dict = Depends(get_current_user)):
    t = await _get_db().tickets.find_one({"id": ticket_id}, {"_id": 0})
    if not t:
        raise HTTPException(status_code=404, detail="Ticket no encontrado.")
    upd = {"updatedAt": _now().isoformat()}
    for campo in ("asunto", "descripcion", "tipo", "contactId", "contactNombre", "pedidoRef", "assignedToId", "assignedToNombre"):
        if campo in payload:
            upd[campo] = payload[campo]
    if "causa" in payload:
        c = payload["causa"]
        if c not in CAUSAS and c not in (None, ""):
            raise HTTPException(status_code=400, detail=f"Causa no válida: {c}")
        upd["causa"] = c or None

    if payload.get("estado") in ESTADOS:
        # CERRAR exige causa. Es el único momento en que se sabe de verdad de
        # dónde vino, y es la puerta que impide que el campo se quede vacío y la
        # estadística no valga nada. Un solo control, y al final: pedirla antes
        # solo consigue que se rellene a boleo para pasar de pantalla.
        if falta_causa_para_cerrar(payload["estado"], upd.get("causa", t.get("causa"))):
            raise HTTPException(
                status_code=400,
                detail="Para cerrar la incidencia hay que indicar la causa "
                       "(de dónde vino el fallo).",
            )
        upd["estado"] = payload["estado"]
        if payload["estado"] in ("resuelto", "cerrado") and not t.get("resueltoAt"):
            upd["resueltoAt"] = _now().isoformat()
    if payload.get("prioridad") in PRIORIDADES:
        upd["prioridad"] = payload["prioridad"]
        # Recalcular SLA si sigue abierto.
        if t.get("estado") not in ("resuelto", "cerrado"):
            base = _parse(t.get("createdAt")) or _now()
            upd["slaVence"] = (base + timedelta(hours=_SLA_HORAS[payload["prioridad"]])).isoformat()
    await _get_db().tickets.update_one({"id": ticket_id}, {"$set": upd})
    nuevo = await _get_db().tickets.find_one({"id": ticket_id}, {"_id": 0})
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
    await _get_db().tickets.update_one({"id": ticket_id}, {"$push": {"comentarios": com}, "$set": {"updatedAt": _now().isoformat()}})
    return {"success": True, "comentario": com}


@router.delete("/crm/tickets/{ticket_id}")
async def borrar_ticket(ticket_id: str, current_user: dict = Depends(get_current_user)):
    await _get_db().tickets.delete_one({"id": ticket_id})
    return {"success": True}
