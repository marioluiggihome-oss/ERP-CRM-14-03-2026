"""
Montajes (Instalaciones) Router
Endpoints para gestionar montadores e instalaciones
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from typing import Optional
import uuid
import logging
import os

from services.db_client import get_db as _get_db
from models.schemas import (
    MontadorCreate, MontadorUpdate, MontadorResponse,
    MontajeCreate, MontajeUpdate, MontajeResponse
)

try:
    from services.jwt_service import get_current_user, ADMIN_ROLE_FLAGS
except Exception:  # pragma: no cover
    async def get_current_user():
        return None
    ADMIN_ROLE_FLAGS = ["isAdmin"]

logger = logging.getLogger(__name__)

router = APIRouter(tags=["montajes"])

# Database connection


def _is_elevated(user: Optional[dict]) -> bool:
    """Master / dirección: ve TODO y puede filtrar por usuario o cliente."""
    return bool(user and any(user.get(f) for f in ADMIN_ROLE_FLAGS))


def _owner_filter(current_user: Optional[dict], user_id: Optional[str] = None) -> dict:
    """Devuelve el filtro de propietario a aplicar. El master ve todo (o filtra por
    user_id si lo indica); el resto solo ve lo suyo (createdByUserId)."""
    if _is_elevated(current_user):
        return {"createdByUserId": user_id} if user_id else {}
    uid = (current_user or {}).get("id")
    # Sin identificar → no devolver nada ajeno (privacidad por defecto)
    return {"createdByUserId": uid if uid else "__none__"}


# === MONTADORES (Instaladores) ===

@router.get("/montadores")
async def get_montadores(status: str = None, user_id: str = None,
                         current_user: Optional[dict] = Depends(get_current_user)):
    """Lista montadores. PRIVADO por usuario: cada uno ve los suyos; el master ve
    todos y puede filtrar por usuario (user_id)."""
    try:
        query = dict(_owner_filter(current_user, user_id))
        if status:
            query["status"] = status

        montadores = await _get_db().montadores.find(query, {"_id": 0}).sort("name", 1).to_list(500)

        # Añadir conteo de montajes por montador
        for m in montadores:
            count = await _get_db().montajes.count_documents({"montadorId": m.get("id", "")})
            m["totalMontajes"] = count

        return montadores
    except Exception as e:
        logger.error(f"Get montadores error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/montadores/{montador_id}")
async def get_montador(montador_id: str,
                       current_user: Optional[dict] = Depends(get_current_user)):
    """Get a specific montador by ID (respetando la privacidad por usuario)."""
    try:
        montador = await _get_db().montadores.find_one({"id": montador_id}, {"_id": 0})
        if not montador:
            raise HTTPException(status_code=404, detail="Montador no encontrado")
        if not _is_elevated(current_user) and montador.get("createdByUserId") != (current_user or {}).get("id"):
            raise HTTPException(status_code=404, detail="Montador no encontrado")

        # Añadir conteo de montajes
        montador["totalMontajes"] = await _get_db().montajes.count_documents({"montadorId": montador_id})

        return montador
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get montador error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/montadores")
async def create_montador(montador: MontadorCreate,
                          current_user: Optional[dict] = Depends(get_current_user)):
    """Create a new montador (sellando el propietario para la privacidad)."""
    try:
        now = datetime.now(timezone.utc).isoformat()
        montador_data = {
            "id": f"MON-{uuid.uuid4().hex[:8].upper()}",
            **montador.model_dump(),
            "createdByUserId": (current_user or {}).get("id"),
            "createdByName": (current_user or {}).get("name") or (current_user or {}).get("username") or "",
            "createdAt": now,
            "updatedAt": now
        }

        await _get_db().montadores.insert_one(montador_data)
        if "_id" in montador_data:
            del montador_data["_id"]

        return montador_data
    except Exception as e:
        logger.error(f"Create montador error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/montadores/{montador_id}")
async def update_montador(montador_id: str, montador: MontadorUpdate,
                          current_user: Optional[dict] = Depends(get_current_user)):
    """Update a montador (solo el dueño o el master)."""
    try:
        existing = await _get_db().montadores.find_one({"id": montador_id}, {"_id": 0})
        if not existing:
            raise HTTPException(status_code=404, detail="Montador no encontrado")
        if not _is_elevated(current_user) and existing.get("createdByUserId") != (current_user or {}).get("id"):
            raise HTTPException(status_code=403, detail="No autorizado")

        update_data = {k: v for k, v in montador.model_dump().items() if v is not None}
        update_data["updatedAt"] = datetime.now(timezone.utc).isoformat()

        await _get_db().montadores.update_one({"id": montador_id}, {"$set": update_data})

        updated = await _get_db().montadores.find_one({"id": montador_id}, {"_id": 0})
        return updated
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update montador error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/montadores/{montador_id}")
async def delete_montador(montador_id: str,
                          current_user: Optional[dict] = Depends(get_current_user)):
    """Delete a montador (solo el dueño o el master)."""
    try:
        existing = await _get_db().montadores.find_one({"id": montador_id}, {"_id": 0})
        if not existing:
            raise HTTPException(status_code=404, detail="Montador no encontrado")
        if not _is_elevated(current_user) and existing.get("createdByUserId") != (current_user or {}).get("id"):
            raise HTTPException(status_code=403, detail="No autorizado")
        await _get_db().montadores.delete_one({"id": montador_id})
        return {"success": True, "message": "Montador eliminado"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete montador error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# === MONTAJES (Instalaciones) ===

@router.get("/montajes")
async def get_montajes(
    status: str = None,
    montador_id: str = None,
    start_date: str = None,
    end_date: str = None,
    user_id: str = None,
    current_user: Optional[dict] = Depends(get_current_user)
):
    """Lista montajes. PRIVADO por usuario: cada uno ve los suyos; el master ve
    todos y puede filtrar por usuario (user_id) o por montador/cliente."""
    try:
        query = dict(_owner_filter(current_user, user_id))
        if status:
            query["status"] = status
        if montador_id:
            query["montadorId"] = montador_id
        if start_date and end_date:
            query["scheduledDate"] = {"$gte": start_date, "$lte": end_date}
        elif start_date:
            query["scheduledDate"] = {"$gte": start_date}
        elif end_date:
            query["scheduledDate"] = {"$lte": end_date}

        montajes = await _get_db().montajes.find(query, {"_id": 0}).sort("scheduledDate", 1).to_list(500)
        return montajes
    except Exception as e:
        logger.error(f"Get montajes error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/montajes/{montaje_id}")
async def get_montaje(montaje_id: str,
                      current_user: Optional[dict] = Depends(get_current_user)):
    """Get a specific montaje by ID (respetando la privacidad por usuario)."""
    try:
        montaje = await _get_db().montajes.find_one({"id": montaje_id}, {"_id": 0})
        if not montaje:
            raise HTTPException(status_code=404, detail="Montaje no encontrado")
        if not _is_elevated(current_user) and montaje.get("createdByUserId") != (current_user or {}).get("id"):
            raise HTTPException(status_code=404, detail="Montaje no encontrado")
        return montaje
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get montaje error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/montajes")
async def create_montaje(montaje: MontajeCreate,
                         current_user: Optional[dict] = Depends(get_current_user)):
    """Create a new montaje (sellando el propietario para la privacidad)."""
    try:
        now = datetime.now(timezone.utc).isoformat()

        # Obtener nombre del montador si no viene
        montador_name = montaje.montadorName
        if not montador_name and montaje.montadorId:
            montador = await _get_db().montadores.find_one({"id": montaje.montadorId}, {"_id": 0, "name": 1})
            if montador:
                montador_name = montador.get("name", "")

        montaje_data = {
            "id": f"MTJ-{uuid.uuid4().hex[:8].upper()}",
            **montaje.model_dump(),
            "montadorName": montador_name,
            "createdByUserId": (current_user or {}).get("id"),
            "createdByName": (current_user or {}).get("name") or (current_user or {}).get("username") or "",
            "createdAt": now,
            "updatedAt": now
        }

        await _get_db().montajes.insert_one(montaje_data)
        if "_id" in montaje_data:
            del montaje_data["_id"]

        return montaje_data
    except Exception as e:
        logger.error(f"Create montaje error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/montajes/{montaje_id}")
async def update_montaje(montaje_id: str, montaje: MontajeUpdate,
                         current_user: Optional[dict] = Depends(get_current_user)):
    """Update a montaje (solo el dueño o el master)."""
    try:
        existing = await _get_db().montajes.find_one({"id": montaje_id}, {"_id": 0})
        if not existing:
            raise HTTPException(status_code=404, detail="Montaje no encontrado")
        if not _is_elevated(current_user) and existing.get("createdByUserId") != (current_user or {}).get("id"):
            raise HTTPException(status_code=403, detail="No autorizado")

        update_data = {k: v for k, v in montaje.model_dump().items() if v is not None}
        update_data["updatedAt"] = datetime.now(timezone.utc).isoformat()

        # Actualizar nombre del montador si cambió el ID
        if "montadorId" in update_data:
            montador = await _get_db().montadores.find_one({"id": update_data["montadorId"]}, {"_id": 0, "name": 1})
            if montador:
                update_data["montadorName"] = montador.get("name", "")

        await _get_db().montajes.update_one({"id": montaje_id}, {"$set": update_data})

        updated = await _get_db().montajes.find_one({"id": montaje_id}, {"_id": 0})
        return updated
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update montaje error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/montajes/{montaje_id}")
async def delete_montaje(montaje_id: str,
                         current_user: Optional[dict] = Depends(get_current_user)):
    """Delete a montaje (solo el dueño o el master)."""
    try:
        existing = await _get_db().montajes.find_one({"id": montaje_id}, {"_id": 0})
        if not existing:
            raise HTTPException(status_code=404, detail="Montaje no encontrado")
        if not _is_elevated(current_user) and existing.get("createdByUserId") != (current_user or {}).get("id"):
            raise HTTPException(status_code=403, detail="No autorizado")
        await _get_db().montajes.delete_one({"id": montaje_id})
        return {"success": True, "message": "Montaje eliminado"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete montaje error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/montadores/{montador_id}/montajes")
async def get_montajes_by_montador(montador_id: str, status: str = None,
                                   current_user: Optional[dict] = Depends(get_current_user)):
    """Get all montajes for a specific montador (respetando la privacidad)."""
    try:
        query = {"montadorId": montador_id}
        if status:
            query["status"] = status
        if not _is_elevated(current_user):
            query["createdByUserId"] = (current_user or {}).get("id") or "__none__"

        montajes = await _get_db().montajes.find(query, {"_id": 0}).sort("scheduledDate", 1).to_list(100)
        return montajes
    except Exception as e:
        logger.error(f"Get montajes by montador error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
