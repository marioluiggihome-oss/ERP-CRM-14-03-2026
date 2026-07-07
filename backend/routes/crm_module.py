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
from services.jwt_service import get_current_user as jwt_get_current_user, require_auth
import re as _re

def _escape_regex(s: str) -> str:
    """Escapar caracteres especiales de regex para evitar ReDoS"""
    return _re.escape(str(s)) if s else s


logger = logging.getLogger(__name__)

# Seguridad: sin token, el "modo compatibilidad" de abajo (_get_user_or_none)
# trataba la peticion como admin (parametro isAdmin por defecto True), asi
# que cualquiera sin loguearse podia listar TODOS los contactos/oportunidades
# del CRM. Se exige login a nivel de router; la logica interna de permisos
# por propietario/rol (_can_modify, filtros de get_contacts) sigue igual y ya
# funciona bien una vez hay un usuario real verificado.
_CRM_DEPS = [Depends(require_auth)]

router = APIRouter(tags=["crm"], dependencies=_CRM_DEPS)
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


_ELEVATED_FLAGS = ("isAdmin", "isGerente", "isDirectorComercial",
                   "isResponsableDelegacion", "isDirectorFabrica")


def _can_modify(current_user, doc) -> bool:
    """¿Puede el usuario modificar/eliminar este documento?

    - Sin token (legacy) -> True (no romper flujos antiguos).
    - Admin/dirección -> True.
    - En otro caso, solo si es el dueño (creador o asignado).
    """
    if not current_user:
        return True
    if any(current_user.get(f) for f in _ELEVATED_FLAGS):
        return True
    uid = current_user.get("id")
    if not uid:
        return True
    owners = {doc.get("createdByUserId"), doc.get("createdBy"),
              doc.get("assignedTo"), doc.get("userId")}
    return uid in owners


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


@router.get("/crm/prescriptors")
async def get_prescriptors():
    """Lista de colaboradores/prescriptores (usuarios con isPrescriptor=True).

    El frontend (CRMContacts) usa id + clientName para el desplegable de
    colaboradores. Antes este endpoint no existía y daba 404.
    """
    try:
        users = await db.users.find(
            {"isPrescriptor": True, "isActive": {"$ne": False}},
            {"_id": 0, "id": 1, "clientName": 1, "username": 1}
        ).to_list(500)
        return users
    except Exception as e:
        logger.error(f"Get prescriptors error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/crm/opportunities")
async def create_opportunity(opp: OpportunityCreate, current_user: Optional[dict] = Depends(_get_user_or_none)):
    """Create a new opportunity"""
    try:
        opp_dict = opp.model_dump()
        opp_obj = OpportunityModel(**opp_dict)
        doc = opp_obj.model_dump()
        doc['createdAt'] = doc['createdAt'].isoformat()
        doc['updatedAt'] = doc['updatedAt'].isoformat()

        # Atribuir al creador para que el aislamiento por usuario lo muestre
        if current_user and current_user.get("id"):
            doc['createdByUserId'] = current_user["id"]
            if not doc.get("createdBy"):
                doc['createdBy'] = current_user["id"]

        await db.opportunities.insert_one(doc)
        doc.pop('_id', None)
        return doc
    except Exception as e:
        logger.error(f"Create opportunity error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/crm/opportunities/{opp_id}")
async def update_opportunity(opp_id: str, update: OpportunityUpdate, current_user: Optional[dict] = Depends(_get_user_or_none)):
    """Update an opportunity"""
    try:
        existing = await db.opportunities.find_one({"id": opp_id}, {"_id": 0})
        if not existing:
            raise HTTPException(status_code=404, detail="Oportunidad no encontrada")
        if not _can_modify(current_user, existing):
            raise HTTPException(status_code=403, detail="No tienes permiso para modificar esta oportunidad")

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
async def delete_opportunity(opp_id: str, current_user: Optional[dict] = Depends(_get_user_or_none)):
    """Delete an opportunity"""
    try:
        existing = await db.opportunities.find_one({"id": opp_id}, {"_id": 0})
        if not existing:
            raise HTTPException(status_code=404, detail="Oportunidad no encontrada")
        if not _can_modify(current_user, existing):
            raise HTTPException(status_code=403, detail="No tienes permiso para eliminar esta oportunidad")
        await db.opportunities.delete_one({"id": opp_id})
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
    limit: int = 200,
    current_user: Optional[dict] = Depends(_get_user_or_none)
):
    """Lista de actividades del día a día.

    UNIFICADA: incluye también los EVENTOS del calendario (visitas, reuniones…),
    para que todo el trabajo diario aparezca en un único listado.
    Aislada por usuario (admin/dirección ve todo; el resto, lo suyo).
    """
    try:
        query = {}
        if contactId:
            query["contactId"] = contactId
        if opportunityId:
            query["opportunityId"] = opportunityId
        if activityType:
            query["activityType"] = activityType  # el modelo guarda 'activityType'

        # Aislamiento por usuario
        elevated = bool(current_user and any(current_user.get(f) for f in _ELEVATED_FLAGS))
        uid = current_user.get("id") if current_user else None
        if uid and not elevated:
            owner = {"$or": [
                {"createdByUserId": uid}, {"userId": uid}, {"assignedTo": uid},
            ]}
            query = {"$and": [query, owner]} if query else owner

        activities = await db.activities.find(query, {"_id": 0}).sort("createdAt", -1).limit(limit).to_list(limit)

        # Unificación: añadir los eventos del calendario como actividades
        try:
            ev_query = {}
            if contactId:
                ev_query["contactId"] = contactId
            if uid and not elevated:
                ev_query["$or"] = [{"assignedTo": uid}, {"createdBy": uid}, {"createdByUserId": uid}]
            events = await db.calendar_events.find(ev_query, {"_id": 0}).sort("startDate", -1).limit(limit).to_list(limit)
            for e in events:
                sd = str(e.get("startDate") or "")
                etype = (e.get("eventType") or "visita")
                activities.append({
                    "id": e.get("id"),
                    "activityType": etype,
                    "type": etype,
                    "title": e.get("title") or "Evento",
                    "subject": e.get("title") or "",
                    "description": e.get("description", "") or "",
                    "date": sd[:10],
                    "time": sd[11:16] if len(sd) >= 16 else "",
                    "dueDate": sd[:10],
                    "contactId": e.get("contactId"),
                    "contactName": e.get("contactName", ""),
                    "assignedTo": e.get("assignedTo", ""),
                    "completed": e.get("completed", False),
                    "createdAt": e.get("createdAt") or sd,
                    "isCalendarEvent": True,
                })
        except Exception as ev_err:
            logger.warning(f"No se pudieron incluir eventos del calendario en actividades: {ev_err}")

        return activities
    except Exception as e:
        logger.error(f"Get activities error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/crm/activities")
async def create_activity(activity: ActivityCreate, current_user: Optional[dict] = Depends(_get_user_or_none)):
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

        # Atribuir la actividad al usuario que la crea
        if current_user and current_user.get("id"):
            doc['createdByUserId'] = current_user["id"]
            if not doc.get("userId"):
                doc['userId'] = current_user["id"]

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
async def update_activity(activity_id: str, updates: dict, current_user: Optional[dict] = Depends(_get_user_or_none)):
    """Update an existing activity"""
    try:
        existing = await db.activities.find_one({"id": activity_id}, {"_id": 0})
        if not existing:
            raise HTTPException(status_code=404, detail="Actividad no encontrada")
        if not _can_modify(current_user, existing):
            raise HTTPException(status_code=403, detail="No tienes permiso para modificar esta actividad")

        updates.pop('id', None)
        updates.pop('_id', None)
        updates['updatedAt'] = datetime.now(timezone.utc).isoformat()

        await db.activities.update_one(
            {"id": activity_id},
            {"$set": updates}
        )

        doc = await db.activities.find_one({"id": activity_id}, {"_id": 0})
        return doc
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update activity error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/crm/activities/{activity_id}")
async def delete_activity(activity_id: str, current_user: Optional[dict] = Depends(_get_user_or_none)):
    """Delete an activity"""
    try:
        existing = await db.activities.find_one({"id": activity_id}, {"_id": 0})
        if not existing:
            raise HTTPException(status_code=404, detail="Actividad no encontrada")
        if not _can_modify(current_user, existing):
            raise HTTPException(status_code=403, detail="No tienes permiso para eliminar esta actividad")
        await db.activities.delete_one({"id": activity_id})
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
    userId: Optional[str] = None,
    contactId: Optional[str] = None,
    completed: Optional[bool] = None,
    current_user: Optional[dict] = Depends(_get_user_or_none)
):
    """Get calendar events with optional filters (aislado por usuario)."""
    try:
        # Usuario efectivo para aislamiento: admin/dirección ve todo
        elevated = bool(current_user and any(current_user.get(f) for f in _ELEVATED_FLAGS))
        scope_uid = (current_user.get("id") if current_user else None) or userId or assignedTo
        isolate = bool(scope_uid and not elevated)

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
        if isolate:
            query["$or"] = [
                {"assignedTo": scope_uid}, {"createdBy": scope_uid}, {"createdByUserId": scope_uid},
            ]

        events = await db.calendar_events.find(query, {"_id": 0}).sort("startDate", 1).to_list(500)

        # Incluir también las ACTIVIDADES del CRM (llamadas, visitas, reuniones...)
        # como eventos del calendario. Va en su propio try: si algo falla aquí,
        # los eventos "puros" del calendario deben seguir devolviéndose igualmente.
        try:
            act_query = {}
            if contactId:
                act_query["contactId"] = contactId
            if isolate:
                act_query["$or"] = [
                    {"assignedTo": scope_uid}, {"userId": scope_uid}, {"createdByUserId": scope_uid},
                ]
            activities = await db.activities.find(act_query, {"_id": 0}).to_list(500)

            ACT_COLORS = {
                'call': '#3b82f6', 'llamada': '#3b82f6',
                'visit': '#f97316', 'visita': '#f97316',
                'meeting': '#8b5cf6', 'reunion': '#8b5cf6', 'reunión': '#8b5cf6',
                'video': '#06b6d4', 'email': '#10b981', 'note': '#64748b', 'nota': '#64748b',
            }
            for a in activities:
                day = a.get('date') or a.get('dueDate')
                if not day:
                    ca = a.get('createdAt')
                    day = (ca[:10] if isinstance(ca, str) else None)
                if not day:
                    continue
                t = a.get('time') or a.get('dueTime') or '09:00'
                day_s = str(day)
                start_iso = f"{day_s}T{t}:00" if len(day_s) == 10 else day_s
                if start and day_s[:10] < str(start)[:10]:
                    continue
                if end and day_s[:10] > str(end)[:10]:
                    continue
                atype = (a.get('activityType') or a.get('type') or 'note').lower()
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
                    "isActivity": True,
                })
        except Exception as act_err:
            logger.warning(f"No se pudieron incluir actividades en el calendario: {act_err}")

        # Normalizar startDate a string para que el frontend no falle al parsear
        for ev in events:
            sd = ev.get('startDate')
            if sd is not None and not isinstance(sd, str):
                try:
                    ev['startDate'] = sd.isoformat()
                except Exception:
                    ev['startDate'] = str(sd)
            ed = ev.get('endDate')
            if ed is not None and not isinstance(ed, str):
                try:
                    ev['endDate'] = ed.isoformat()
                except Exception:
                    ev['endDate'] = str(ed)

        events.sort(key=lambda e: str(e.get('startDate') or ''))
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
        # Guardar TODAS las fechas como string ISO (consistencia con consultas y
        # con las actividades; evita el lio string vs fecha BSON).
        for k in ('startDate', 'endDate', 'createdAt', 'updatedAt', 'completedAt'):
            if isinstance(doc.get(k), datetime):
                doc[k] = doc[k].isoformat()
        # El usuario asignado puede venir como assignedTo o assignedToId: unificar
        # ambos para que filtros y recordatorios por email funcionen.
        owner = doc.get('assignedTo') or doc.get('assignedToId')
        doc['assignedTo'] = owner
        doc['assignedToId'] = owner

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
        if result.deleted_count:
            return {"message": "Evento eliminado", "id": event_id}
        # Puede ser una ACTIVIDAD del CRM (también sale en el calendario)
        act = await db.activities.delete_one({"id": event_id})
        if act.deleted_count:
            return {"message": "Actividad eliminada", "id": event_id}
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete calendar event error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/crm/calendar/events/{event_id}/complete")
async def complete_calendar_event(event_id: str):
    """Mark a calendar event as completed"""
    now_iso = datetime.now(timezone.utc).isoformat()
    result = await db.calendar_events.update_one(
        {"id": event_id},
        {"$set": {"completed": True, "completedAt": now_iso, "updatedAt": now_iso}}
    )
    if result.matched_count:
        return {"message": "Evento completado", "id": event_id}
    # Si no es un evento "puro", puede ser una ACTIVIDAD del CRM (también salen
    # en el calendario): marcarla como completada allí.
    act = await db.activities.update_one(
        {"id": event_id},
        {"$set": {"completed": True, "completedAt": now_iso}}
    )
    if act.matched_count:
        return {"message": "Actividad completada", "id": event_id}
    raise HTTPException(status_code=404, detail="Evento no encontrado")


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
        
        # Valor del pipeline abierto (oportunidades no ganadas/perdidas)
        pipe_val = await db.opportunities.aggregate([
            {"$match": {**base_filter, "stage": {"$nin": ["won", "lost"]}}},
            {"$group": {"_id": None, "total": {"$sum": "$value"}}}
        ]).to_list(1)
        pipeline_value = pipe_val[0]["total"] if pipe_val else 0

        # Oportunidades perdidas este mes
        lost_this_month = await db.opportunities.count_documents({
            **base_filter, "stage": "lost",
            "closedAt": {"$gte": datetime.now(timezone.utc).replace(day=1).isoformat()}
        })

        # Top oportunidades abiertas (previsión ponderada, riesgo y ranking)
        top_opportunities = await db.opportunities.find(
            {**base_filter, "stage": {"$nin": ["won", "lost"]}},
            {"_id": 0, "id": 1, "title": 1, "company": 1, "contactName": 1,
             "stage": 1, "value": 1, "probability": 1}
        ).sort("value", -1).limit(20).to_list(20)

        # Actividades recientes / pendientes
        recent_activities = await db.activities.find(
            base_filter if base_filter else {},
            {"_id": 0}
        ).sort("createdAt", -1).limit(10).to_list(10)

        # Eventos de hoy (startDate empieza por la fecha de hoy)
        _today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        events_today = await db.calendar_events.count_documents({
            **base_filter, "startDate": {"$regex": f"^{_today}"}
        })

        # Próximos eventos
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
            "wonValueThisMonth": revenue_this_month,
            "revenueThisMonth": revenue_this_month,  # compat
            "lostThisMonth": lost_this_month,
            "pipelineValue": pipeline_value,
            "pipelineByStage": by_stage,
            "byStage": by_stage,  # compat
            "topOpportunities": top_opportunities,
            "upcomingActivities": recent_activities,
            "recentActivities": recent_activities,  # compat
            "eventsToday": events_today,
            "upcomingEvents": upcoming_events,
        }
    except Exception as e:
        logger.error(f"Get CRM dashboard error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/crm/analytics/inactive-clients")
async def get_inactive_clients_analytics(
    days_without_offer: int = 30,
    days_without_purchase: int = 60,
    current_user: Optional[dict] = Depends(_get_user_or_none),
):
    """Clientes sin presupuesto / sin compra reciente (alertas del Panel CRM).

    Devuelve {summary, withoutRecentOffer[], withoutRecentPurchase[]} ya filtrado
    por usuario (admin/dirección ve todo).
    """
    try:
        verified_is_admin = False
        verified_user_id = None
        if current_user and current_user.get("id"):
            verified_user_id = current_user["id"]
            du = await db.users.find_one({"id": verified_user_id}, {"_id": 0})
            if du:
                verified_is_admin = bool(
                    du.get("isAdmin") or du.get("isGerente")
                    or du.get("isDirectorComercial") or du.get("isResponsableDelegacion")
                )
        base_filter = {}
        if not verified_is_admin and verified_user_id:
            shops = await db.users.find({"linkedRepresentativeId": verified_user_id}, {"id": 1, "_id": 0}).to_list(100)
            all_ids = [verified_user_id] + [s["id"] for s in shops]
            base_filter["$or"] = [{"assignedTo": {"$in": all_ids}}, {"createdByUserId": {"$in": all_ids}}]

        contacts = await db.contacts.find(
            base_filter, {"_id": 0, "id": 1, "name": 1, "company": 1, "email": 1}
        ).to_list(2000)
        opps = await db.opportunities.find(
            base_filter, {"_id": 0, "contactId": 1, "createdAt": 1, "stage": 1, "closedAt": 1}
        ).to_list(8000)

        last_offer, last_purchase = {}, {}
        for o in opps:
            cid = o.get("contactId")
            if not cid:
                continue
            ca = o.get("createdAt") or ""
            if ca and ca > last_offer.get(cid, ""):
                last_offer[cid] = ca
            if o.get("stage") == "won":
                cl = o.get("closedAt") or o.get("createdAt") or ""
                if cl and cl > last_purchase.get(cid, ""):
                    last_purchase[cid] = cl

        def _days_since(iso):
            if not iso:
                return None
            try:
                d = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
                if d.tzinfo is None:
                    d = d.replace(tzinfo=timezone.utc)
                return (datetime.now(timezone.utc) - d).days
            except Exception:
                return None

        without_offer, without_purchase = [], []
        for c in contacts:
            cid = c.get("id")
            d_off = _days_since(last_offer.get(cid))
            if d_off is None or d_off >= days_without_offer:
                without_offer.append({**c, "daysWithoutOffer": d_off if d_off is not None else 9999})
            d_pur = _days_since(last_purchase.get(cid))
            if d_pur is None or d_pur >= days_without_purchase:
                without_purchase.append({**c, "daysWithoutPurchase": d_pur if d_pur is not None else 9999})

        without_offer.sort(key=lambda x: -x["daysWithoutOffer"])
        without_purchase.sort(key=lambda x: -x["daysWithoutPurchase"])
        return {
            "summary": {
                "totalWithoutOffer30Days": len(without_offer),
                "totalWithoutPurchase60Days": len(without_purchase),
            },
            "withoutRecentOffer": without_offer[:50],
            "withoutRecentPurchase": without_purchase[:50],
        }
    except Exception as e:
        logger.error(f"Inactive clients analytics error: {e}")
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


# ============================================================================
# PARTE DIARIO POR VOZ (IA) — solo informes relativos al CRM
# Colección: crm_reports
# ============================================================================

_REPORT_SYSTEM = (
    "Eres un asistente que SOLO redacta partes/informes de actividad COMERCIAL del "
    "CRM: visitas a clientes, llamadas y gestiones comerciales. A partir del dictado "
    "del comercial, estructura un informe claro y profesional en español. Responde "
    "SOLO con JSON válido con esta forma:\n"
    '{ "titulo": "Parte de visitas", '
    '"visitas": [ {"cliente":"","hora":"","resumen":"","resultado":"","proximaAccion":""} ], '
    '"resumen": "resumen general de la jornada" }\n'
    "Extrae una entrada por cada visita/gestión mencionada. Si el dictado NO trata de "
    "visitas o gestión comercial, devuelve \"visitas\": [] y en \"resumen\" indica "
    "amablemente que esta herramienta solo genera informes relativos al CRM."
)


@router.post("/crm/voice-report")
async def crm_voice_report(payload: dict, current_user: Optional[dict] = Depends(_get_user_or_none)):
    """Genera un parte/informe de visitas a partir del dictado (voz transcrita)."""
    import json
    import re as _re2
    transcript = str((payload or {}).get("transcript") or "").strip()
    if not transcript:
        raise HTTPException(status_code=400, detail="Dicta o escribe lo que quieres incluir en el informe")
    periodo_label = str(payload.get("periodoLabel") or "")
    try:
        from services.llm_vision import chat_with_gemini
        resp = await chat_with_gemini(
            prompt=f"Periodo del informe: {periodo_label}\n\nDictado del comercial:\n{transcript[:8000]}",
            system_message=_REPORT_SYSTEM,
            model="gemini-2.5-flash",
        )
        t = (resp or "").strip()
        if t.startswith("```"):
            t = t.split("```")[1]
            if t.startswith("json"):
                t = t[4:]
        try:
            data = json.loads(t.strip())
        except Exception:
            m = _re2.search(r'\{[\s\S]*\}', t)
            data = json.loads(m.group()) if m else {}
    except Exception as e:
        logger.error(f"CRM voice report IA error: {e}")
        raise HTTPException(status_code=502, detail="La IA no pudo generar el informe. Inténtalo de nuevo.")

    visitas = data.get("visitas") or []
    now = datetime.now(timezone.utc)
    uid = (current_user.get("id") if current_user else None) or str(payload.get("userId") or "")
    doc = {
        "id": f"crmrep-{uuid.uuid4().hex[:8]}",
        "userId": uid,
        "userName": str(payload.get("userName") or (current_user.get("username") if current_user else "")),
        "titulo": str(data.get("titulo") or "Parte de visitas"),
        "periodo": str(payload.get("periodo") or "hoy"),
        "periodoLabel": periodo_label,
        "visitas": visitas,
        "resumen": str(data.get("resumen") or ""),
        "totalVisitas": len(visitas),
        "rawTranscript": transcript,
        "fecha": now.strftime("%Y-%m-%d"),
        "createdAt": now.isoformat(),
    }
    await db.crm_reports.insert_one(doc)
    doc.pop("_id", None)
    return {"success": True, "report": doc}


@router.get("/crm/reports")
async def list_crm_reports(userId: Optional[str] = None):
    q = {"userId": userId} if userId else {}
    items = await db.crm_reports.find(q, {"_id": 0, "rawTranscript": 0}).sort("createdAt", -1).to_list(1000)
    return {"items": items}


@router.get("/crm/reports/{report_id}")
async def get_crm_report(report_id: str):
    r = await db.crm_reports.find_one({"id": report_id}, {"_id": 0})
    if not r:
        raise HTTPException(status_code=404, detail="Informe no encontrado")
    return r


@router.delete("/crm/reports/{report_id}")
async def delete_crm_report(report_id: str):
    await db.crm_reports.delete_one({"id": report_id})
    return {"success": True}


def _esc(s):
    return str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _crm_report_html(r: dict) -> str:
    """Maquetación bonita del informe CRM para email/impresión."""
    rows = "".join(
        f"<tr><td style='font-weight:700'>{_esc(v.get('cliente'))}</td>"
        f"<td>{_esc(v.get('hora'))}</td>"
        f"<td>{_esc(v.get('resumen'))}</td>"
        f"<td>{_esc(v.get('resultado'))}</td>"
        f"<td>{_esc(v.get('proximaAccion'))}</td></tr>"
        for v in (r.get("visitas") or [])
    ) or "<tr><td colspan='5' style='color:#94a3b8'>Sin visitas</td></tr>"
    return f"""<!doctype html><html><head><meta charset="utf-8"></head>
<body style="margin:0;background:#f1f5f9;font-family:Arial,Helvetica,sans-serif;color:#1e293b">
  <div style="max-width:760px;margin:0 auto;background:#fff">
    <div style="background:linear-gradient(135deg,#3730a3,#6d28d9);color:#fff;padding:22px 28px">
      <div style="font-size:12px;letter-spacing:2px;opacity:.85;text-transform:uppercase">Luiggi Home · Informe CRM</div>
      <h1 style="margin:4px 0 0;font-size:22px">{_esc(r.get('titulo'))}</h1>
      <div style="font-size:13px;opacity:.9;margin-top:4px">{_esc(r.get('periodoLabel'))} · {_esc(r.get('userName'))} · {r.get('totalVisitas',0)} visita(s)</div>
    </div>
    <div style="padding:24px 28px">
      <table style="width:100%;border-collapse:collapse;font-size:13px">
        <thead><tr style="background:#f1f5f9;text-align:left">
          <th style="padding:8px;text-transform:uppercase;font-size:10px">Cliente</th>
          <th style="padding:8px;text-transform:uppercase;font-size:10px">Hora</th>
          <th style="padding:8px;text-transform:uppercase;font-size:10px">Resumen</th>
          <th style="padding:8px;text-transform:uppercase;font-size:10px">Resultado</th>
          <th style="padding:8px;text-transform:uppercase;font-size:10px">Próxima acción</th>
        </tr></thead>
        <tbody>{rows}</tbody>
      </table>
      <div style="margin-top:18px;padding:14px 16px;background:#f8fafc;border-left:4px solid #6d28d9;border-radius:6px">
        <div style="font-size:10px;text-transform:uppercase;color:#6d28d9;font-weight:800;margin-bottom:4px">Resumen de la jornada</div>
        <div style="font-size:13px;color:#334155">{_esc(r.get('resumen'))}</div>
      </div>
      <div style="margin-top:18px;color:#94a3b8;font-size:11px;text-align:center">Generado por Luiggi Home ERP · CRM</div>
    </div>
  </div>
</body></html>"""


@router.post("/crm/reports/{report_id}/email")
async def email_crm_report(report_id: str, payload: dict):
    to = str((payload or {}).get("to") or "").strip()
    if not to:
        raise HTTPException(status_code=400, detail="Falta el correo del destinatario")
    r = await db.crm_reports.find_one({"id": report_id}, {"_id": 0})
    if not r:
        raise HTTPException(status_code=404, detail="Informe no encontrado")
    try:
        from routes.auth_advanced import send_email_with_resend
        ok = await send_email_with_resend(
            to, f"Luiggi Home — Informe CRM: {r.get('titulo', '')}", _crm_report_html(r)
        )
    except Exception as e:
        logger.error(f"Email CRM report error: {e}")
        ok = False
    if not ok:
        raise HTTPException(status_code=502, detail="No se pudo enviar el email (revisa la configuración de correo).")
    return {"success": True}
