"""
Router para CRM - Contactos, Oportunidades, Calendario, Actividades
"""
import logging
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Request, Depends

from config import db
from models.schemas import (
    ContactModel, ContactCreate, ContactUpdate,
    OpportunityModel, OpportunityCreate, OpportunityUpdate,
    CalendarEventModel, CalendarEventCreate, CalendarEventUpdate,
    ActivityModel, ActivityCreate, ActivityUpdate
)
from services.jwt_service import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/crm", tags=["CRM"])


# ============================================
# CONTACTS
# ============================================

@router.get("/contacts")
async def get_contacts(
    status: str = None,
    segment: str = None,
    business_type: str = None,
    prescriptor_id: str = None,
    assigned_to_id: str = None,
    search: str = None,
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """Obtener contactos con filtros - Cada comercial solo ve sus propios contactos"""
    query = {}
    
    # Si NO es admin, solo ve sus propios contactos
    if not current_user.get("isAdmin"):
        user_id = current_user.get("sub") or current_user.get("id")
        query["$or"] = [
            {"createdByUserId": user_id},
            {"assignedToId": user_id}
        ]
    
    if status:
        query["status"] = status
    if segment:
        query["segment"] = segment
    if business_type:
        query["businessType"] = business_type
    if prescriptor_id:
        query["prescriptorId"] = prescriptor_id
    if assigned_to_id:
        # Override the user filter if specific assignedTo is requested
        query["assignedToId"] = assigned_to_id
        if "$or" in query:
            del query["$or"]
    if search:
        search_query = [
            {"name": {"$regex": search, "$options": "i"}},
            {"company": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
            {"phone": {"$regex": search, "$options": "i"}}
        ]
        if "$or" in query:
            # Combine with existing $or using $and
            query = {"$and": [{"$or": query["$or"]}, {"$or": search_query}]}
            del query["$and"][0]["$or"]
        else:
            query["$or"] = search_query
    
    contacts = await db.contacts.find(query, {"_id": 0}).sort("createdAt", -1).skip(skip).limit(limit).to_list(limit)
    return contacts


@router.get("/contacts/{contact_id}")
async def get_contact(contact_id: str):
    """Obtener contacto por ID"""
    contact = await db.contacts.find_one({"id": contact_id}, {"_id": 0})
    if not contact:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")
    return contact


@router.post("/contacts")
async def create_contact(contact: ContactCreate, current_user: dict = Depends(get_current_user)):
    """Crear un nuevo contacto - Se asocia al comercial que lo crea"""
    contact_dict = contact.model_dump()
    contact_dict["id"] = f"cont-{__import__('uuid').uuid4().hex[:8]}"
    contact_dict["createdAt"] = datetime.now(timezone.utc)
    contact_dict["updatedAt"] = datetime.now(timezone.utc)
    
    # Guardar el ID del usuario que crea el contacto
    user_id = current_user.get("sub") or current_user.get("id")
    contact_dict["createdByUserId"] = user_id
    contact_dict["createdByUsername"] = current_user.get("username", "")
    
    # Si no tiene assignedToId, asignarlo al creador
    if not contact_dict.get("assignedToId"):
        contact_dict["assignedToId"] = user_id
    
    await db.contacts.insert_one(contact_dict)
    
    result = await db.contacts.find_one({"id": contact_dict["id"]}, {"_id": 0})
    return result


@router.put("/contacts/{contact_id}")
async def update_contact(contact_id: str, contact: ContactUpdate):
    """Actualizar contacto existente"""
    existing = await db.contacts.find_one({"id": contact_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")
    
    update_data = {k: v for k, v in contact.model_dump().items() if v is not None}
    update_data["updatedAt"] = datetime.now(timezone.utc)
    
    await db.contacts.update_one({"id": contact_id}, {"$set": update_data})
    
    updated = await db.contacts.find_one({"id": contact_id}, {"_id": 0})
    return updated


@router.delete("/contacts/{contact_id}")
async def delete_contact(contact_id: str):
    """Eliminar contacto"""
    result = await db.contacts.delete_one({"id": contact_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")
    return {"success": True}


# ============================================
# OPPORTUNITIES
# ============================================

@router.get("/opportunities")
async def get_opportunities(
    stage: str = None,
    contact_id: str = None,
    assigned_to_id: str = None,
    skip: int = 0,
    limit: int = 50
):
    """Obtener oportunidades con filtros"""
    query = {}
    
    if stage:
        query["stage"] = stage
    if contact_id:
        query["contactId"] = contact_id
    if assigned_to_id:
        query["assignedToId"] = assigned_to_id
    
    opportunities = await db.opportunities.find(query, {"_id": 0}).sort("createdAt", -1).skip(skip).limit(limit).to_list(limit)
    return opportunities


@router.get("/opportunities/{opp_id}")
async def get_opportunity(opp_id: str):
    """Obtener oportunidad por ID"""
    opp = await db.opportunities.find_one({"id": opp_id}, {"_id": 0})
    if not opp:
        raise HTTPException(status_code=404, detail="Oportunidad no encontrada")
    return opp


@router.post("/opportunities")
async def create_opportunity(opp: OpportunityCreate, current_user: dict = Depends(get_current_user)):
    """Crear una nueva oportunidad"""
    opp_dict = opp.model_dump()
    opp_dict["id"] = f"opp-{__import__('uuid').uuid4().hex[:8]}"
    opp_dict["createdAt"] = datetime.now(timezone.utc)
    opp_dict["updatedAt"] = datetime.now(timezone.utc)
    
    await db.opportunities.insert_one(opp_dict)
    
    result = await db.opportunities.find_one({"id": opp_dict["id"]}, {"_id": 0})
    return result


@router.put("/opportunities/{opp_id}")
async def update_opportunity(opp_id: str, opp: OpportunityUpdate):
    """Actualizar oportunidad existente"""
    existing = await db.opportunities.find_one({"id": opp_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Oportunidad no encontrada")
    
    update_data = {k: v for k, v in opp.model_dump().items() if v is not None}
    update_data["updatedAt"] = datetime.now(timezone.utc)
    
    # Marcar como ganada/perdida si cambia el stage
    if update_data.get("stage") == "won" and not existing.get("wonDate"):
        update_data["wonDate"] = datetime.now(timezone.utc)
    elif update_data.get("stage") == "lost" and not existing.get("lostDate"):
        update_data["lostDate"] = datetime.now(timezone.utc)
    
    await db.opportunities.update_one({"id": opp_id}, {"$set": update_data})
    
    updated = await db.opportunities.find_one({"id": opp_id}, {"_id": 0})
    return updated


@router.delete("/opportunities/{opp_id}")
async def delete_opportunity(opp_id: str):
    """Eliminar oportunidad"""
    result = await db.opportunities.delete_one({"id": opp_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Oportunidad no encontrada")
    return {"success": True}


# ============================================
# CALENDAR
# ============================================

@router.get("/calendar/event-types")
async def get_event_types():
    """Obtener tipos de eventos disponibles"""
    return [
        {"id": "meeting", "name": "Reunión", "color": "#3b82f6"},
        {"id": "call", "name": "Llamada", "color": "#22c55e"},
        {"id": "task", "name": "Tarea", "color": "#f59e0b"},
        {"id": "visit", "name": "Visita", "color": "#8b5cf6"},
        {"id": "deadline", "name": "Fecha límite", "color": "#ef4444"},
        {"id": "followup", "name": "Seguimiento", "color": "#06b6d4"}
    ]


@router.get("/calendar/events")
async def get_calendar_events(
    start_date: str = None,
    end_date: str = None,
    event_type: str = None,
    contact_id: str = None,
    assigned_to_id: str = None
):
    """Obtener eventos del calendario con filtros"""
    query = {}
    
    if start_date:
        query["startDate"] = {"$gte": datetime.fromisoformat(start_date.replace('Z', '+00:00'))}
    if end_date:
        if "startDate" in query:
            query["startDate"]["$lte"] = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        else:
            query["startDate"] = {"$lte": datetime.fromisoformat(end_date.replace('Z', '+00:00'))}
    if event_type:
        query["eventType"] = event_type
    if contact_id:
        query["contactId"] = contact_id
    if assigned_to_id:
        query["assignedToId"] = assigned_to_id
    
    events = await db.calendar_events.find(query, {"_id": 0}).sort("startDate", 1).to_list(500)
    return events


@router.post("/calendar/events")
async def create_calendar_event(event: CalendarEventCreate, current_user: dict = Depends(get_current_user)):
    """Crear un nuevo evento"""
    event_dict = event.model_dump()
    event_dict["id"] = f"evt-{__import__('uuid').uuid4().hex[:8]}"
    event_dict["createdAt"] = datetime.now(timezone.utc)
    event_dict["updatedAt"] = datetime.now(timezone.utc)
    
    await db.calendar_events.insert_one(event_dict)
    
    result = await db.calendar_events.find_one({"id": event_dict["id"]}, {"_id": 0})
    return result


@router.get("/calendar/events/{event_id}")
async def get_calendar_event(event_id: str):
    """Obtener evento por ID"""
    event = await db.calendar_events.find_one({"id": event_id}, {"_id": 0})
    if not event:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    return event


@router.put("/calendar/events/{event_id}")
async def update_calendar_event(event_id: str, event: CalendarEventUpdate):
    """Actualizar evento existente"""
    existing = await db.calendar_events.find_one({"id": event_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    
    update_data = {k: v for k, v in event.model_dump().items() if v is not None}
    update_data["updatedAt"] = datetime.now(timezone.utc)
    
    await db.calendar_events.update_one({"id": event_id}, {"$set": update_data})
    
    updated = await db.calendar_events.find_one({"id": event_id}, {"_id": 0})
    return updated


@router.delete("/calendar/events/{event_id}")
async def delete_calendar_event(event_id: str):
    """Eliminar evento"""
    result = await db.calendar_events.delete_one({"id": event_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    return {"success": True}


@router.post("/calendar/events/{event_id}/complete")
async def complete_calendar_event(event_id: str):
    """Marcar evento como completado"""
    existing = await db.calendar_events.find_one({"id": event_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    
    await db.calendar_events.update_one(
        {"id": event_id},
        {"$set": {
            "completed": True,
            "completedAt": datetime.now(timezone.utc),
            "updatedAt": datetime.now(timezone.utc)
        }}
    )
    
    updated = await db.calendar_events.find_one({"id": event_id}, {"_id": 0})
    return updated


# ============================================
# ACTIVITIES
# ============================================

@router.get("/activities")
async def get_activities(
    contact_id: str = None,
    opportunity_id: str = None,
    skip: int = 0,
    limit: int = 50
):
    """Obtener actividades con filtros"""
    query = {}
    
    if contact_id:
        query["contactId"] = contact_id
    if opportunity_id:
        query["opportunityId"] = opportunity_id
    
    activities = await db.activities.find(query, {"_id": 0}).sort("createdAt", -1).skip(skip).limit(limit).to_list(limit)
    return activities


@router.post("/activities")
async def create_activity(activity: ActivityCreate, current_user: dict = Depends(get_current_user)):
    """Crear una nueva actividad"""
    activity_dict = activity.model_dump()
    activity_dict["id"] = f"act-{__import__('uuid').uuid4().hex[:8]}"
    activity_dict["userId"] = current_user.get("id")
    activity_dict["userName"] = current_user.get("username", "")
    activity_dict["createdAt"] = datetime.now(timezone.utc)
    
    await db.activities.insert_one(activity_dict)
    
    result = await db.activities.find_one({"id": activity_dict["id"]}, {"_id": 0})
    return result


@router.put("/activities/{act_id}")
async def update_activity(act_id: str, activity: ActivityUpdate):
    """Actualizar actividad existente"""
    existing = await db.activities.find_one({"id": act_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")
    
    update_data = {k: v for k, v in activity.model_dump().items() if v is not None}
    
    await db.activities.update_one({"id": act_id}, {"$set": update_data})
    
    updated = await db.activities.find_one({"id": act_id}, {"_id": 0})
    return updated


@router.delete("/activities/{act_id}")
async def delete_activity(act_id: str):
    """Eliminar actividad"""
    result = await db.activities.delete_one({"id": act_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")
    return {"success": True}


# ============================================
# DASHBOARD
# ============================================

@router.get("/dashboard")
async def get_crm_dashboard(current_user: dict = Depends(get_current_user)):
    """Obtener datos del dashboard CRM"""
    # Contar contactos por estado
    contacts_pipeline = [
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    contacts_by_status = await db.contacts.aggregate(contacts_pipeline).to_list(20)
    
    # Contar oportunidades por etapa
    opps_pipeline = [
        {"$group": {"_id": "$stage", "count": {"$sum": 1}, "value": {"$sum": "$value"}}}
    ]
    opps_by_stage = await db.opportunities.aggregate(opps_pipeline).to_list(20)
    
    # Eventos próximos
    now = datetime.now(timezone.utc)
    upcoming_events = await db.calendar_events.find(
        {"startDate": {"$gte": now}, "completed": {"$ne": True}},
        {"_id": 0}
    ).sort("startDate", 1).limit(5).to_list(5)
    
    # Actividades recientes
    recent_activities = await db.activities.find(
        {},
        {"_id": 0}
    ).sort("createdAt", -1).limit(10).to_list(10)
    
    return {
        "contacts": {
            "total": await db.contacts.count_documents({}),
            "byStatus": {r["_id"]: r["count"] for r in contacts_by_status if r["_id"]}
        },
        "opportunities": {
            "total": await db.opportunities.count_documents({}),
            "byStage": {r["_id"]: {"count": r["count"], "value": r["value"]} for r in opps_by_stage if r["_id"]}
        },
        "upcomingEvents": upcoming_events,
        "recentActivities": recent_activities
    }
