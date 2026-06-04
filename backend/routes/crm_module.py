"""
CRM Router - Customer Relationship Management
Endpoints para gestión de contactos, oportunidades, actividades y calendario
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone, timedelta
from typing import Optional
import uuid
import logging
import os

from models.schemas import (
    ContactModel, ContactCreate, ContactUpdate,
    OpportunityModel, OpportunityCreate, OpportunityUpdate,
    CalendarEventModel, CalendarEventCreate, CalendarEventUpdate,
    ActivityModel, ActivityCreate, ActivityUpdate
)
from services.jwt_service import get_current_user as jwt_get_current_user
import re as _re

def _escape_regex(s: str) -> str:
    """Escapar caracteres especiales de regex para evitar ReDoS"""
    return _re.escape(str(s)) if s else s


logger = logging.getLogger(__name__)

router = APIRouter(tags=["crm"])
_optional_bearer = HTTPBearer(auto_error=False)

# Database connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'luiggi_home')
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]


async def _get_user_or_none(credentials=Depends(_optional_bearer)):
    """Resolve current user from JWT. Returns None if no/invalid token (graceful for legacy callers)."""
    if not credentials:
        return None
    try:
        return await jwt_get_current_user(credentials)
    except Exception:
        return None


# ============================================
# CRM API ENDPOINTS - Contactos
# ============================================

@router.get("/crm/contacts")
async def get_contacts(
    status: Optional[str] = None, 
    search: Optional[str] = None, 
    assignedTo: Optional[str] = None, 
    isAdmin: Optional[bool] = True,
    requestingUserId: Optional[str] = None,
    current_user: Optional[dict] = Depends(_get_user_or_none)
):
    """Get all contacts with optional filters, including total value from opportunities.

    SECURITY (JWT-based isolation):
    - Si hay un JWT válido, se ignoran los params `isAdmin`/`requestingUserId` y
      la decisión de admin viene del token + lookup en DB.
    - Un comercial (no admin) SOLO ve contactos donde createdByUserId == su id
      o assignedToId == su id.
    """
    try:
        # SEGURIDAD: Resolver rol del usuario actual (preferir JWT sobre query params)
        verified_is_admin = False
        verified_user_id = None
        if current_user and current_user.get("id"):
            verified_user_id = current_user["id"]
            db_user = await db.users.find_one({"id": verified_user_id}, {"_id": 0})
            if db_user:
                verified_is_admin = bool(
                    db_user.get("isAdmin") or
                    db_user.get("isGerente") or
                    db_user.get("isDirectorComercial") or
                    db_user.get("isResponsableDelegacion")
                )
        elif requestingUserId:
            # Fallback legado: confiar en requestingUserId pero verificar en DB
            verified_user_id = requestingUserId
            db_user = await db.users.find_one({"id": requestingUserId}, {"_id": 0})
            if db_user:
                verified_is_admin = bool(
                    db_user.get("isAdmin") or
                    db_user.get("isGerente") or
                    db_user.get("isDirectorComercial") or
                    db_user.get("isResponsableDelegacion")
                )
        else:
            # Sin token y sin requestingUserId: comportamiento anterior (compat)
            verified_is_admin = bool(isAdmin)
        
        query = {}
        if status:
            query["status"] = status
        search_filter = None
        if search:
            search_filter = [
                {"name": {"$regex": _escape_regex(search), "$options": "i"}},
                {"company": {"$regex": _escape_regex(search), "$options": "i"}},
                {"email": {"$regex": _escape_regex(search), "$options": "i"}}
            ]
        
        # SEGURIDAD: Si NO es admin, filtrar por createdByUserId/assignedToId del usuario
        if not verified_is_admin and verified_user_id:
            # Incluir tiendas vinculadas a este comercial (compat con flujo anterior)
            shops = await db.users.find(
                {"linkedRepresentativeId": verified_user_id},
                {"id": 1, "_id": 0}
            ).to_list(100)
            shop_ids = [s["id"] for s in shops]
            all_ids = [verified_user_id] + shop_ids

            isolation_filter = {"$or": [
                {"createdByUserId": {"$in": all_ids}},
                {"assignedToId": {"$in": all_ids}},
                {"assignedTo": {"$in": all_ids}},
                {"createdBy": {"$in": all_ids}}
            ]}

            if search_filter:
                query["$and"] = [isolation_filter, {"$or": search_filter}]
            else:
                query.update(isolation_filter)
        elif not verified_is_admin and assignedTo:
            # Compatibilidad legada cuando no hay token: filtrar por assignedTo
            shops = await db.users.find(
                {"linkedRepresentativeId": assignedTo},
                {"id": 1, "_id": 0}
            ).to_list(100)
            shop_ids = [s["id"] for s in shops]
            all_ids = [assignedTo] + shop_ids
            assigned_filter = {"$or": [
                {"assignedTo": {"$in": all_ids}},
                {"createdBy": {"$in": all_ids}},
                {"assignedToId": {"$in": all_ids}},
                {"createdByUserId": {"$in": all_ids}}
            ]}
            if search_filter:
                query["$and"] = [assigned_filter, {"$or": search_filter}]
            else:
                query.update(assigned_filter)
        elif search_filter:
            query["$or"] = search_filter
        
        contacts = await db.contacts.find(query, {"_id": 0}).sort("createdAt", -1).to_list(1000)
        
        # Calcular totalValue para cada contacto
        if contacts:
            contact_ids = [c.get("id") for c in contacts]
            opportunities = await db.opportunities.find(
                {"contactId": {"$in": contact_ids}},
                {"_id": 0, "contactId": 1, "value": 1}
            ).to_list(5000)
            
            values_by_contact = {}
            for opp in opportunities:
                cid = opp.get("contactId")
                if cid:
                    if cid not in values_by_contact:
                        values_by_contact[cid] = 0
                    values_by_contact[cid] += opp.get("value", 0)
            
            for contact in contacts:
                contact["totalValue"] = values_by_contact.get(contact.get("id"), 0)
        
        return contacts
    except Exception as e:
        logger.error(f"Get contacts error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/crm/contacts/by-prescriptor/{prescriptor_id}")
async def get_contacts_by_prescriptor(prescriptor_id: str):
    """Contactos creados por un prescriptor (Agenda de Negocios).

    Los devuelve por prescriptorId; tambien incluye los que tenga asociados como
    creador (createdByUserId) por si se guardaron antes de fijar el prescriptor.
    """
    try:
        contacts = await db.contacts.find(
            {"$or": [
                {"prescriptorId": prescriptor_id},
                {"createdByUserId": prescriptor_id},
            ]},
            {"_id": 0},
        ).sort("createdAt", -1).to_list(1000)
        return contacts
    except Exception as e:
        logger.error(f"Get contacts by prescriptor error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/crm/contacts/{contact_id}")
async def get_contact(contact_id: str, current_user: Optional[dict] = Depends(_get_user_or_none)):
    """Get a single contact by ID — solo el propietario o admin puede verlo"""
    contact = await db.contacts.find_one({"id": contact_id}, {"_id": 0})
    if not contact:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")

    if current_user and current_user.get("id"):
        db_user = await db.users.find_one({"id": current_user["id"]}, {"_id": 0})
        is_admin = db_user and bool(
            db_user.get("isAdmin") or db_user.get("isGerente") or
            db_user.get("isDirectorComercial") or db_user.get("isResponsableDelegacion")
        )
        if not is_admin:
            uid = current_user["id"]
            # Obtener tiendas vinculadas a este comercial
            shops = await db.users.find({"linkedRepresentativeId": uid}, {"id": 1, "_id": 0}).to_list(100)
            allowed_ids = {uid} | {s["id"] for s in shops}
            owner_ids = {
                contact.get("createdByUserId"),
                contact.get("assignedToId"),
                contact.get("assignedTo"),
                contact.get("createdBy"),
            }
            if not owner_ids.intersection(allowed_ids):
                raise HTTPException(status_code=403, detail="No tienes permiso para ver este contacto")

    return contact


@router.post("/crm/contacts")
async def create_contact(
    contact: ContactCreate,
    current_user: Optional[dict] = Depends(_get_user_or_none)
):
    """Create a new contact. Si hay JWT, se asocia al usuario creador."""
    try:
        contact_dict = contact.model_dump()
        contact_obj = ContactModel(**contact_dict)
        doc = contact_obj.model_dump()
        doc['createdAt'] = doc['createdAt'].isoformat()
        doc['updatedAt'] = doc['updatedAt'].isoformat()

        # Aislamiento: guardar autor y por defecto asignar al creador
        if current_user and current_user.get("id"):
            user_id = current_user["id"]
            doc['createdByUserId'] = user_id
            doc['createdByUsername'] = current_user.get("username", "")
            if not doc.get('assignedToId'):
                doc['assignedToId'] = user_id

        await db.contacts.insert_one(doc)
        doc.pop('_id', None)
        return doc
    except Exception as e:
        logger.error(f"Create contact error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/crm/contacts/{contact_id}")
async def update_contact(contact_id: str, update: ContactUpdate, current_user: Optional[dict] = Depends(_get_user_or_none)):
    """Update a contact — solo el propietario o admin puede modificarlo"""
    try:
        existing = await db.contacts.find_one({"id": contact_id}, {"_id": 0})
        if not existing:
            raise HTTPException(status_code=404, detail="Contacto no encontrado")

        if current_user and current_user.get("id"):
            db_user = await db.users.find_one({"id": current_user["id"]}, {"_id": 0})
            is_admin = db_user and bool(
                db_user.get("isAdmin") or db_user.get("isGerente") or
                db_user.get("isDirectorComercial") or db_user.get("isResponsableDelegacion")
            )
            if not is_admin:
                uid = current_user["id"]
                shops = await db.users.find({"linkedRepresentativeId": uid}, {"id": 1, "_id": 0}).to_list(100)
                allowed_ids = {uid} | {s["id"] for s in shops}
                owner_ids = {
                    existing.get("createdByUserId"),
                    existing.get("assignedToId"),
                    existing.get("assignedTo"),
                    existing.get("createdBy"),
                }
                if not owner_ids.intersection(allowed_ids):
                    raise HTTPException(status_code=403, detail="No tienes permiso para modificar este contacto")

        update_data = {k: v for k, v in update.model_dump().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=400, detail="No hay datos para actualizar")

        update_data["updatedAt"] = datetime.now(timezone.utc).isoformat()

        await db.contacts.update_one({"id": contact_id}, {"$set": update_data})
        updated = await db.contacts.find_one({"id": contact_id}, {"_id": 0})
        return updated
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update contact error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/crm/contacts/{contact_id}")
async def delete_contact(contact_id: str, current_user: Optional[dict] = Depends(_get_user_or_none)):
    """Delete a contact — solo el propietario o admin puede borrarlo"""
    try:
        existing = await db.contacts.find_one({"id": contact_id}, {"_id": 0})
        if not existing:
            raise HTTPException(status_code=404, detail="Contacto no encontrado")

        if current_user and current_user.get("id"):
            db_user = await db.users.find_one({"id": current_user["id"]}, {"_id": 0})
            is_admin = db_user and bool(
                db_user.get("isAdmin") or db_user.get("isGerente") or
                db_user.get("isDirectorComercial") or db_user.get("isResponsableDelegacion")
            )
            if not is_admin:
                uid = current_user["id"]
                shops = await db.users.find({"linkedRepresentativeId": uid}, {"id": 1, "_id": 0}).to_list(100)
                allowed_ids = {uid} | {s["id"] for s in shops}
                owner_ids = {
                    existing.get("createdByUserId"),
                    existing.get("assignedToId"),
                    existing.get("assignedTo"),
                    existing.get("createdBy"),
                }
                if not owner_ids.intersection(allowed_ids):
                    raise HTTPException(status_code=403, detail="No tienes permiso para eliminar este contacto")

        await db.opportunities.delete_many({"contactId": contact_id})
        await db.activities.delete_many({"contactId": contact_id})
        result = await db.contacts.delete_one({"id": contact_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Contacto no encontrado")
        return {"message": "Contacto eliminado", "id": contact_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete contact error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# PRESCRIPTOR NOTES (Calendar Notes)
# ============================================

@router.get("/crm/contacts/{contact_id}/notes")
async def get_contact_notes(contact_id: str):
    """Get notes for a contact (from activities with type 'note' or 'prescriptor_note')"""
    try:
        notes = await db.activities.find(
            {
                "contactId": contact_id,
                "type": {"$in": ["note", "prescriptor_note"]}
            },
            {"_id": 0}
        ).sort("createdAt", -1).to_list(100)
        return notes
    except Exception as e:
        logger.error(f"Get contact notes error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/crm/contacts/{contact_id}/notes")
async def create_contact_note(contact_id: str, note: ActivityCreate):
    """Create a note for a contact"""
    try:
        note_dict = note.model_dump()
        note_dict["contactId"] = contact_id
        note_dict["type"] = note_dict.get("type") or "prescriptor_note"
        
        note_obj = ActivityModel(**note_dict)
        doc = note_obj.model_dump()
        doc['createdAt'] = doc['createdAt'].isoformat()
        doc['updatedAt'] = doc['updatedAt'].isoformat()
        
        await db.activities.insert_one(doc)
        doc.pop('_id', None)
        return doc
    except Exception as e:
        logger.error(f"Create contact note error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# CRM API ENDPOINTS - Oportunidades
# ============================================

@router.get("/crm/opportunities")
async def get_opportunities(
    stage: Optional[str] = None,
    contactId: Optional[str] = None,
    search: Optional[str] = None,
    assignedTo: Optional[str] = None,
    isAdmin: Optional[bool] = True,
    requestingUserId: Optional[str] = None,
    current_user: Optional[dict] = Depends(_get_user_or_none)
):
    """Get opportunities — cada usuario solo ve las suyas, admin ve todas"""
    try:
        verified_is_admin = False
        verified_user_id = None

        if current_user and current_user.get("id"):
            verified_user_id = current_user["id"]
            db_user = await db.users.find_one({"id": verified_user_id}, {"_id": 0})
            if db_user:
                verified_is_admin = bool(
                    db_user.get("isAdmin") or db_user.get("isGerente") or
                    db_user.get("isDirectorComercial") or db_user.get("isResponsableDelegacion")
                )
        elif requestingUserId:
            verified_user_id = requestingUserId
            requesting_user = await db.users.find_one({"id": requestingUserId}, {"_id": 0})
            if requesting_user:
                verified_is_admin = bool(
                    requesting_user.get("isAdmin") or
                    requesting_user.get("isResponsableDelegacion")
                )

        query = {}
        if stage:
            query["stage"] = stage
        if contactId:
            query["contactId"] = contactId

        search_filter = None
        if search:
            search_filter = [
                {"title": {"$regex": _escape_regex(search), "$options": "i"}},
                {"description": {"$regex": _escape_regex(search), "$options": "i"}},
                {"contactName": {"$regex": _escape_regex(search), "$options": "i"}}
            ]

        if not verified_is_admin and verified_user_id:
            shops = await db.users.find(
                {"linkedRepresentativeId": verified_user_id},
                {"id": 1, "_id": 0}
            ).to_list(100)
            all_ids = [verified_user_id] + [s["id"] for s in shops]
            isolation_filter = {"$or": [
                {"assignedTo": {"$in": all_ids}},
                {"createdBy": {"$in": all_ids}},
                {"createdByUserId": {"$in": all_ids}},
            ]}
            if search_filter:
                query["$and"] = [isolation_filter, {"$or": search_filter}]
            else:
                query.update(isolation_filter)
        elif search_filter:
            query["$or"] = search_filter

        opportunities = await db.opportunities.find(query, {"_id": 0}).sort("updatedAt", -1).to_list(1000)
        return opportunities
    except Exception as e:
        logger.error(f"Get opportunities error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/crm/opportunities/{opp_id}")
async def get_opportunity(opp_id: str, current_user: Optional[dict] = Depends(_get_user_or_none)):
    """Get a single opportunity — solo propietario o admin"""
    opp = await db.opportunities.find_one({"id": opp_id}, {"_id": 0})
    if not opp:
        raise HTTPException(status_code=404, detail="Oportunidad no encontrada")

    if current_user and current_user.get("id"):
        db_user = await db.users.find_one({"id": current_user["id"]}, {"_id": 0})
        is_admin = db_user and bool(
            db_user.get("isAdmin") or db_user.get("isGerente") or
            db_user.get("isDirectorComercial") or db_user.get("isResponsableDelegacion")
        )
        if not is_admin:
            uid = current_user["id"]
            shops = await db.users.find({"linkedRepresentativeId": uid}, {"id": 1, "_id": 0}).to_list(100)
            allowed_ids = {uid} | {s["id"] for s in shops}
            owner_ids = {opp.get("assignedTo"), opp.get("createdBy"), opp.get("createdByUserId")}
            if not owner_ids.intersection(allowed_ids):
                raise HTTPException(status_code=403, detail="No tienes permiso para ver esta oportunidad")

    return opp


@router.post("/crm/opportunities")
async def create_opportunity(opp: OpportunityCreate):
    """Create a new opportunity"""
    try:
        opp_dict = opp.model_dump()
        opp_obj = OpportunityModel(**opp_dict)
        doc = opp_obj.model_dump()
        doc['createdAt'] = doc['createdAt'].isoformat()
        doc['updatedAt'] = doc['updatedAt'].isoformat()
        
        await db.opportunities.insert_one(doc)
        doc.pop('_id', None)
        return doc
    except Exception as e:
        logger.error(f"Create opportunity error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/crm/opportunities/{opp_id}")
async def update_opportunity(opp_id: str, update: OpportunityUpdate):
    """Update an opportunity"""
    try:
        update_data = {k: v for k, v in update.model_dump().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=400, detail="No hay datos para actualizar")
        
        update_data["updatedAt"] = datetime.now(timezone.utc).isoformat()
        
        # Handle stage change
        if "stage" in update_data:
            if update_data["stage"] in ["won", "lost"]:
                update_data["closedAt"] = datetime.now(timezone.utc).isoformat()
        
        result = await db.opportunities.update_one(
            {"id": opp_id},
            {"$set": update_data}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Oportunidad no encontrada")
        
        updated = await db.opportunities.find_one({"id": opp_id}, {"_id": 0})
        return updated
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update opportunity error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/crm/opportunities/{opp_id}")
async def delete_opportunity(opp_id: str):
    """Delete an opportunity"""
    try:
        result = await db.opportunities.delete_one({"id": opp_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Oportunidad no encontrada")
        return {"message": "Oportunidad eliminada", "id": opp_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete opportunity error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# CRM API ENDPOINTS - Analisis de Clientes Inactivos
# ============================================

@router.get("/crm/contacts/inactive")
async def get_inactive_contacts(days: int = 30, assignedTo: Optional[str] = None, isAdmin: Optional[bool] = True, current_user: Optional[dict] = Depends(_get_user_or_none)):
    """Get contacts that haven't had any activity in the specified days — filtrado por JWT"""
    try:
        cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

        # Resolver admin desde JWT
        verified_is_admin = False
        verified_user_id = None
        if current_user and current_user.get("id"):
            verified_user_id = current_user["id"]
            db_user = await db.users.find_one({"id": verified_user_id}, {"_id": 0})
            if db_user:
                verified_is_admin = bool(
                    db_user.get("isAdmin") or db_user.get("isGerente") or
                    db_user.get("isDirectorComercial") or db_user.get("isResponsableDelegacion")
                )
        elif assignedTo:
            verified_user_id = assignedTo
            db_user = await db.users.find_one({"id": assignedTo}, {"_id": 0})
            if db_user:
                verified_is_admin = bool(db_user.get("isAdmin") or db_user.get("isGerente"))

        query = {}
        if not verified_is_admin and verified_user_id:
            shops = await db.users.find({"linkedRepresentativeId": verified_user_id}, {"id": 1, "_id": 0}).to_list(100)
            all_ids = [verified_user_id] + [s["id"] for s in shops]
            query["$or"] = [
                {"assignedTo": {"$in": all_ids}},
                {"createdByUserId": {"$in": all_ids}},
            ]

        contacts = await db.contacts.find(query, {"_id": 0}).to_list(1000)
        
        inactive = []
        for contact in contacts:
            last_activity = await db.activities.find_one(
                {"contactId": contact["id"]},
                {"_id": 0, "createdAt": 1},
                sort=[("createdAt", -1)]
            )
            
            is_inactive = True
            if last_activity:
                if last_activity.get("createdAt", "") > cutoff_date:
                    is_inactive = False
            
            if is_inactive:
                contact["lastActivityDate"] = last_activity.get("createdAt") if last_activity else None
                inactive.append(contact)
        
        return inactive
    except Exception as e:
        logger.error(f"Get inactive contacts error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# CRM API ENDPOINTS - Actividades
# ============================================

@router.get("/crm/activities")
async def get_activities(
    contactId: Optional[str] = None,
    opportunityId: Optional[str] = None,
    activityType: Optional[str] = None,
    limit: int = 100
):
    """Get activities with optional filters"""
    try:
        query = {}
        if contactId:
            query["contactId"] = contactId
        if opportunityId:
            query["opportunityId"] = opportunityId
        if activityType:
            query["type"] = activityType
        
        activities = await db.activities.find(query, {"_id": 0}).sort("createdAt", -1).limit(limit).to_list(limit)
        return activities
    except Exception as e:
        logger.error(f"Get activities error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/crm/activities")
async def create_activity(activity: ActivityCreate):
    """Create a new activity"""
    try:
        act_dict = activity.model_dump()
        # El formulario envía la fecha/hora en dueDate/dueTime. Poblar también
        # date/time (que es lo que leen las vistas) para que no salga "Invalid
        # Date" y la fecha aparezca correctamente en lista y dashboard.
        if not act_dict.get("date") and act_dict.get("dueDate"):
            act_dict["date"] = act_dict["dueDate"]
        if not act_dict.get("time") and act_dict.get("dueTime"):
            act_dict["time"] = act_dict["dueTime"]
        act_obj = ActivityModel(**act_dict)
        doc = act_obj.model_dump()
        doc['createdAt'] = doc['createdAt'].isoformat()
        doc['updatedAt'] = doc['updatedAt'].isoformat()
        
        await db.activities.insert_one(doc)
        doc.pop('_id', None)
        
        # Update contact's lastContactedAt
        if activity.contactId:
            await db.contacts.update_one(
                {"id": activity.contactId},
                {"$set": {
                    "lastContactedAt": datetime.now(timezone.utc).isoformat(),
                    "updatedAt": datetime.now(timezone.utc).isoformat()
                }}
            )
        
        return doc
    except Exception as e:
        logger.error(f"Create activity error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/crm/activities/{activity_id}")
async def update_activity(activity_id: str, updates: dict):
    """Update an existing activity"""
    try:
        updates.pop('id', None)
        updates.pop('_id', None)
        updates['updatedAt'] = datetime.now(timezone.utc).isoformat()

        result = await db.activities.update_one(
            {"id": activity_id},
            {"$set": updates}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Actividad no encontrada")

        doc = await db.activities.find_one({"id": activity_id}, {"_id": 0})
        return doc
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update activity error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/crm/activities/{activity_id}")
async def delete_activity(activity_id: str):
    """Delete an activity"""
    try:
        result = await db.activities.delete_one({"id": activity_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Actividad no encontrada")
        return {"message": "Actividad eliminada", "id": activity_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete activity error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# CRM CALENDAR EVENTS
# ============================================

@router.get("/crm/calendar/events")
async def get_calendar_events(
    start: Optional[str] = None,
    end: Optional[str] = None,
    assignedTo: Optional[str] = None,
    contactId: Optional[str] = None,
    completed: Optional[bool] = None
):
    """Get calendar events with optional filters"""
    try:
        query = {}
        if start and end:
            query["startDate"] = {"$gte": start, "$lte": end}
        elif start:
            query["startDate"] = {"$gte": start}
        elif end:
            query["startDate"] = {"$lte": end}
        
        if assignedTo:
            query["assignedTo"] = assignedTo
        if contactId:
            query["contactId"] = contactId
        if completed is not None:
            query["completed"] = completed
        
        events = await db.calendar_events.find(query, {"_id": 0}).sort("startDate", 1).to_list(500)

        # Incluir también las ACTIVIDADES del CRM (llamadas, visitas, reuniones...)
        # como eventos del calendario, para que se vean en él. Se mapean sobre la marcha.
        act_query = {}
        if assignedTo:
            act_query["$or"] = [{"assignedTo": assignedTo}, {"userId": assignedTo}]
        if contactId:
            act_query["contactId"] = contactId
        activities = await db.activities.find(act_query, {"_id": 0}).to_list(500)

        ACT_COLORS = {
            'call': '#3b82f6', 'llamada': '#3b82f6',
            'visit': '#f97316', 'visita': '#f97316',
            'meeting': '#8b5cf6', 'reunion': '#8b5cf6', 'reunión': '#8b5cf6',
            'video': '#06b6d4', 'email': '#10b981', 'note': '#64748b', 'nota': '#64748b',
        }
        for a in activities:
            # Fecha de la actividad: usa 'date'/'time', con fallbacks a dueDate/createdAt
            day = a.get('date') or a.get('dueDate')
            if not day:
                ca = a.get('createdAt')
                day = (ca[:10] if isinstance(ca, str) else None)
            if not day:
                continue
            t = a.get('time') or a.get('dueTime') or '09:00'
            start_iso = f"{day}T{t}:00" if len(str(day)) == 10 else str(day)
            # Filtrar por rango si se pidió (comparación por prefijo de fecha)
            if start and day < start[:10]:
                continue
            if end and day > end[:10]:
                continue
            atype = (a.get('type') or 'note').lower()
            events.append({
                "id": a.get('id'),
                "title": a.get('title') or a.get('subject') or atype.upper(),
                "description": a.get('description') or a.get('notes') or '',
                "eventType": atype,
                "startDate": start_iso,
                "endDate": start_iso,
                "allDay": False,
                "contactId": a.get('contactId'),
                "contactName": a.get('contactName', ''),
                "assignedTo": a.get('assignedTo') or a.get('userId', ''),
                "completed": a.get('completed', False),
                "color": ACT_COLORS.get(atype, '#64748b'),
                "isActivity": True,  # marca para distinguirlo de un evento "puro"
            })

        events.sort(key=lambda e: e.get('startDate') or '')
        return events
    except Exception as e:
        logger.error(f"Get calendar events error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/crm/calendar/events")
async def create_calendar_event(event: CalendarEventCreate, createdBy: str = "", createdByName: str = ""):
    """Create a new calendar event"""
    try:
        evt_dict = event.model_dump()
        evt_dict["createdBy"] = createdBy
        evt_dict["createdByName"] = createdByName
        evt_obj = CalendarEventModel(**evt_dict)
        doc = evt_obj.model_dump()
        doc['createdAt'] = doc['createdAt'].isoformat()
        doc['updatedAt'] = doc['updatedAt'].isoformat()
        
        await db.calendar_events.insert_one(doc)
        doc.pop('_id', None)
        return doc
    except Exception as e:
        logger.error(f"Create calendar event error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/crm/calendar/events/{event_id}")
async def get_calendar_event(event_id: str):
    """Get a single calendar event"""
    event = await db.calendar_events.find_one({"id": event_id}, {"_id": 0})
    if not event:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    return event


@router.put("/crm/calendar/events/{event_id}")
async def update_calendar_event(event_id: str, update: CalendarEventUpdate):
    """Update a calendar event"""
    try:
        update_data = {k: v for k, v in update.model_dump().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=400, detail="No hay datos para actualizar")
        
        update_data["updatedAt"] = datetime.now(timezone.utc).isoformat()
        
        # Handle completion
        if update_data.get('completed') == True:
            update_data["completedAt"] = datetime.now(timezone.utc).isoformat()
        
        result = await db.calendar_events.update_one(
            {"id": event_id},
            {"$set": update_data}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Evento no encontrado")
        
        updated = await db.calendar_events.find_one({"id": event_id}, {"_id": 0})
        return updated
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update calendar event error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/crm/calendar/events/{event_id}")
async def delete_calendar_event(event_id: str):
    """Delete a calendar event"""
    try:
        result = await db.calendar_events.delete_one({"id": event_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Evento no encontrado")
        return {"message": "Evento eliminado", "id": event_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete calendar event error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/crm/calendar/events/{event_id}/complete")
async def complete_calendar_event(event_id: str):
    """Mark a calendar event as completed"""
    result = await db.calendar_events.update_one(
        {"id": event_id},
        {"$set": {
            "completed": True,
            "completedAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat()
        }}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    return {"message": "Evento completado", "id": event_id}


@router.post("/crm/calendar/create-from-opportunity/{opp_id}")
async def create_reminder_from_opportunity(
    opp_id: str,
    event_type: str = "seguimiento",
    days_from_now: int = 7,
    reminder_title: Optional[str] = None,
    user_id: str = "",
    user_name: str = ""
):
    """Crear recordatorio automatico desde una oportunidad"""
    try:
        opp = await db.opportunities.find_one({"id": opp_id}, {"_id": 0})
        if not opp:
            raise HTTPException(status_code=404, detail="Oportunidad no encontrada")
        
        reminder_date = datetime.now(timezone.utc) + timedelta(days=days_from_now)
        
        event_data = {
            "id": f"evt-{uuid.uuid4().hex[:8]}",
            "title": reminder_title or f"Seguimiento: {opp.get('title', 'Sin titulo')}",
            "description": f"Recordatorio automatico de seguimiento para oportunidad {opp.get('title')}",
            "eventType": event_type,
            "startDate": reminder_date.strftime("%Y-%m-%dT09:00:00"),
            "endDate": reminder_date.strftime("%Y-%m-%dT10:00:00"),
            "allDay": False,
            "contactId": opp.get("contactId"),
            "contactName": opp.get("contactName"),
            "opportunityId": opp_id,
            "opportunityTitle": opp.get("title"),
            "assignedTo": user_id or opp.get("assignedTo", ""),
            "assignedToName": user_name or opp.get("assignedToName", ""),
            "completed": False,
            "createdBy": user_id,
            "createdByName": user_name,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat()
        }
        
        await db.calendar_events.insert_one(event_data)
        event_data.pop('_id', None)
        
        return {
            "success": True,
            "event": event_data,
            "message": f"Recordatorio creado para {reminder_date.strftime('%d/%m/%Y')}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create reminder from opportunity error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# CRM DASHBOARD STATS
# ============================================

@router.get("/crm/dashboard")
async def get_crm_dashboard(assignedTo: Optional[str] = None, isAdmin: Optional[bool] = True, current_user: Optional[dict] = Depends(_get_user_or_none)):
    """Get CRM dashboard statistics — filtrado por JWT"""
    try:
        # Resolver admin desde JWT
        verified_is_admin = False
        verified_user_id = None
        if current_user and current_user.get("id"):
            verified_user_id = current_user["id"]
            db_user = await db.users.find_one({"id": verified_user_id}, {"_id": 0})
            if db_user:
                verified_is_admin = bool(
                    db_user.get("isAdmin") or db_user.get("isGerente") or
                    db_user.get("isDirectorComercial") or db_user.get("isResponsableDelegacion")
                )
        elif assignedTo:
            verified_user_id = assignedTo
            db_user = await db.users.find_one({"id": assignedTo}, {"_id": 0})
            if db_user:
                verified_is_admin = bool(db_user.get("isAdmin") or db_user.get("isGerente"))

        base_filter = {}
        if not verified_is_admin and verified_user_id:
            shops = await db.users.find({"linkedRepresentativeId": verified_user_id}, {"id": 1, "_id": 0}).to_list(100)
            all_ids = [verified_user_id] + [s["id"] for s in shops]
            base_filter["$or"] = [
                {"assignedTo": {"$in": all_ids}},
                {"createdByUserId": {"$in": all_ids}},
            ]
        
        total_contacts = await db.contacts.count_documents(base_filter)
        
        opp_filter = {**base_filter, "stage": {"$nin": ["won", "lost"]}}
        active_opportunities = await db.opportunities.count_documents(opp_filter)
        
        won_filter = {
            **base_filter,
            "stage": "won",
            "closedAt": {"$gte": datetime.now(timezone.utc).replace(day=1).isoformat()}
        }
        won_this_month = await db.opportunities.count_documents(won_filter)
        
        pipeline = [
            {"$match": {**base_filter, "stage": "won", "closedAt": {"$gte": datetime.now(timezone.utc).replace(day=1).isoformat()}}},
            {"$group": {"_id": None, "total": {"$sum": "$value"}}}
        ]
        revenue_result = await db.opportunities.aggregate(pipeline).to_list(1)
        revenue_this_month = revenue_result[0]["total"] if revenue_result else 0
        
        # Opportunities by stage
        stage_pipeline = [
            {"$match": base_filter},
            {"$group": {"_id": "$stage", "count": {"$sum": 1}, "value": {"$sum": "$value"}}}
        ]
        stages = await db.opportunities.aggregate(stage_pipeline).to_list(10)
        by_stage = {s["_id"]: {"count": s["count"], "value": s["value"]} for s in stages}
        
        # Recent activities
        recent_activities = await db.activities.find(
            base_filter if base_filter else {},
            {"_id": 0}
        ).sort("createdAt", -1).limit(10).to_list(10)
        
        # Upcoming events
        upcoming_filter = {
            **base_filter,
            "startDate": {"$gte": datetime.now(timezone.utc).isoformat()},
            "completed": False
        }
        upcoming_events = await db.calendar_events.find(
            upcoming_filter,
            {"_id": 0}
        ).sort("startDate", 1).limit(5).to_list(5)
        
        return {
            "totalContacts": total_contacts,
            "activeOpportunities": active_opportunities,
            "wonThisMonth": won_this_month,
            "revenueThisMonth": revenue_this_month,
            "byStage": by_stage,
            "recentActivities": recent_activities,
            "upcomingEvents": upcoming_events
        }
    except Exception as e:
        logger.error(f"Get CRM dashboard error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# CRM - Create Opportunity from Project/Budget
# ============================================

@router.post("/crm/opportunities/from-project/{project_id}")
async def create_opportunity_from_project(project_id: str, businessType: str = "cocina"):
    """Create a CRM opportunity from an existing project/budget"""
    try:
        project = await db.projects.find_one({"id": project_id}, {"_id": 0})
        if not project:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        
        # Calculate total value
        total_value = 0
        for item in project.get("itemsMontada", []):
            total_value += item.get("totalPrice", 0)
        for item in project.get("itemsDespiece", []):
            total_value += item.get("totalPrice", 0)
        
        # Check if contact exists or create one
        customer_name = project.get("customerName", "Cliente sin nombre")
        contact = await db.contacts.find_one({"name": customer_name}, {"_id": 0})
        
        if not contact:
            contact = ContactModel(
                name=customer_name,
                address=project.get("customerAddress", ""),
                status="customer"
            ).model_dump()
            contact['createdAt'] = contact['createdAt'].isoformat()
            contact['updatedAt'] = contact['updatedAt'].isoformat()
            await db.contacts.insert_one(contact)
        
        contact_id = contact.get("id")
        
        # Create opportunity
        opp = OpportunityModel(
            title=f"Presupuesto {project.get('budgetNumber', project_id[:8])} - {customer_name}",
            description=f"Referencia interna: {project.get('internalReference', '')}",
            contactId=contact_id,
            contactName=customer_name,
            value=total_value,
            probability=50,
            stage="proposal",
            linkedProjectId=project_id,
            linkedProjectNumber=project.get("budgetNumber", ""),
            businessType=businessType
        ).model_dump()
        opp['createdAt'] = opp['createdAt'].isoformat()
        opp['updatedAt'] = opp['updatedAt'].isoformat()
        
        await db.opportunities.insert_one(opp)
        
        # Update contact with businessTypes
        await db.contacts.update_one(
            {"id": contact_id},
            {"$addToSet": {"businessTypes": businessType}}
        )
        
        opp.pop('_id', None)
        return {
            "opportunity": opp,
            "contact": contact,
            "message": "Oportunidad creada desde presupuesto"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create opportunity from project error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# NOTAS / CALENDARIO DEL PRESCRIPTOR (Agenda de Negocios)
# La Agenda usa estos endpoints para el calendario de notas. Antes no existian
# (la pestana Calendario fallaba con 404). Se guardan en prescriptor_notes.
# ============================================================
@router.get("/prescriptor/notes")
async def get_prescriptor_notes(prescriptor_id: str = "", start: str = "", end: str = ""):
    """Notas del prescriptor, opcionalmente filtradas por rango de fechas (date)."""
    try:
        query = {}
        if prescriptor_id:
            query["prescriptorId"] = prescriptor_id
        if start and end:
            query["date"] = {"$gte": start, "$lte": end}
        elif start:
            query["date"] = {"$gte": start}
        notes = await db.prescriptor_notes.find(query, {"_id": 0}).sort("date", 1).to_list(2000)
        return notes
    except Exception as e:
        logger.error(f"Get prescriptor notes error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/prescriptor/notes")
async def create_prescriptor_note(note: dict):
    """Crear una nota del prescriptor."""
    try:
        doc = {**(note or {})}
        doc["id"] = f"pnote-{uuid.uuid4().hex[:8]}"
        doc["createdAt"] = datetime.now(timezone.utc).isoformat()
        doc["updatedAt"] = doc["createdAt"]
        await db.prescriptor_notes.insert_one(doc)
        doc.pop("_id", None)
        return doc
    except Exception as e:
        logger.error(f"Create prescriptor note error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/prescriptor/notes/{note_id}")
async def update_prescriptor_note(note_id: str, note: dict):
    """Actualizar una nota del prescriptor."""
    try:
        update_data = {k: v for k, v in (note or {}).items() if k not in ("id", "_id", "createdAt")}
        update_data["updatedAt"] = datetime.now(timezone.utc).isoformat()
        await db.prescriptor_notes.update_one({"id": note_id}, {"$set": update_data})
        updated = await db.prescriptor_notes.find_one({"id": note_id}, {"_id": 0})
        if not updated:
            raise HTTPException(status_code=404, detail="Nota no encontrada")
        return updated
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update prescriptor note error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/prescriptor/notes/{note_id}")
async def delete_prescriptor_note(note_id: str):
    """Eliminar una nota del prescriptor."""
    try:
        res = await db.prescriptor_notes.delete_one({"id": note_id})
        return {"success": True, "deleted": res.deleted_count}
    except Exception as e:
        logger.error(f"Delete prescriptor note error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
