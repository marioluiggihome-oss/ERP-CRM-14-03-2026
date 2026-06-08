"""
Router para Clientes
"""
import logging
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends

from config import db
from models.schemas import ClientModel, ClientCreate, ClientUpdate
from services.jwt_service import get_current_user, ADMIN_ROLE_FLAGS
import re as _re

def _escape_regex(s: str) -> str:
    """Escapar caracteres especiales de regex para evitar ReDoS"""
    return _re.escape(str(s)) if s else s


def _is_elevated(user) -> bool:
    """Admin / dirección ven TODOS los clientes; el resto solo los suyos."""
    return bool(user and any(user.get(flag) for flag in ADMIN_ROLE_FLAGS))


def _owner_filter(user):
    """$or que limita a los clientes del usuario (creador o asignado)."""
    uid = user.get("id") if user else None
    if not uid:
        return None
    return {"$or": [
        {"createdByUserId": uid},
        {"assignedRepresentativeId": uid},
        {"linkedUserId": uid},
    ]}


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/clients", tags=["Clients"])


@router.get("")
async def get_clients(
    status: str = None,
    segment: str = None,
    search: str = None,
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """Obtener clientes con filtros.

    Cada usuario ve SOLO sus clientes (creados o asignados). Admin y roles de
    dirección (ADMIN_ROLE_FLAGS) ven todos.
    """
    filters = []
    if status:
        filters.append({"status": status})
    if segment:
        filters.append({"segment": segment})
    if search:
        filters.append({"$or": [
            {"name": {"$regex": _escape_regex(search), "$options": "i"}},
            {"company": {"$regex": _escape_regex(search), "$options": "i"}},
            {"email": {"$regex": _escape_regex(search), "$options": "i"}},
            {"code": {"$regex": _escape_regex(search), "$options": "i"}}
        ]})

    # Aislamiento por usuario (salvo admin/dirección)
    if not _is_elevated(current_user):
        of = _owner_filter(current_user)
        if of is not None:
            filters.append(of)

    query = {"$and": filters} if filters else {}
    clients = await db.clients.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    return clients


@router.get("/segments")
async def get_client_segments():
    """Obtener lista de segmentos disponibles"""
    return {
        "segments": [
            {"id": "particular", "name": "Particular"},
            {"id": "profesional", "name": "Profesional"},
            {"id": "constructor", "name": "Constructor/Promotor"},
            {"id": "tienda", "name": "Tienda/Distribuidor"},
            {"id": "mayorista", "name": "Mayorista"}
        ]
    }


@router.get("/{client_id}")
async def get_client(client_id: str):
    """Obtener cliente por ID"""
    client = await db.clients.find_one({"id": client_id}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return client


@router.post("")
async def create_client(client: ClientCreate, current_user: dict = Depends(get_current_user)):
    """Crear un nuevo cliente"""
    client_dict = client.model_dump()
    client_dict["id"] = f"cli-{__import__('uuid').uuid4().hex[:8]}"
    client_dict["createdAt"] = datetime.now(timezone.utc)
    client_dict["updatedAt"] = datetime.now(timezone.utc)

    # Sellar el creador para poder aislar por usuario (cada uno ve los suyos)
    uid = current_user.get("id") if current_user else None
    if uid:
        client_dict["createdByUserId"] = uid
        if not client_dict.get("assignedRepresentativeId"):
            client_dict["assignedRepresentativeId"] = uid

    # Verificar código único si se proporciona
    if client_dict.get("code"):
        existing = await db.clients.find_one({"code": client_dict["code"]})
        if existing:
            raise HTTPException(status_code=400, detail="El código de cliente ya existe")
    
    await db.clients.insert_one(client_dict)
    
    # Devolver sin _id
    result = await db.clients.find_one({"id": client_dict["id"]}, {"_id": 0})
    return result


@router.put("/{client_id}")
async def update_client(client_id: str, client: ClientUpdate):
    """Actualizar cliente existente"""
    existing = await db.clients.find_one({"id": client_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    update_data = {k: v for k, v in client.model_dump().items() if v is not None}
    update_data["updatedAt"] = datetime.now(timezone.utc)
    
    await db.clients.update_one({"id": client_id}, {"$set": update_data})
    
    updated = await db.clients.find_one({"id": client_id}, {"_id": 0})
    return updated


@router.delete("/{client_id}")
async def delete_client(client_id: str):
    """Eliminar cliente"""
    result = await db.clients.delete_one({"id": client_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return {"success": True}


@router.post("/{client_id}/activate")
async def activate_client(client_id: str):
    """Activar un cliente (cambiar status a 'active')"""
    existing = await db.clients.find_one({"id": client_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    await db.clients.update_one(
        {"id": client_id},
        {"$set": {"status": "active", "updatedAt": datetime.now(timezone.utc)}}
    )
    
    updated = await db.clients.find_one({"id": client_id}, {"_id": 0})
    return updated
