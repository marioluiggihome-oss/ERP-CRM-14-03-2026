"""
Montajes (Instalaciones) Router
Endpoints para gestionar montadores e instalaciones
"""
from fastapi import APIRouter, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import uuid
import logging
import os

from models.schemas import (
    MontadorCreate, MontadorUpdate, MontadorResponse,
    MontajeCreate, MontajeUpdate, MontajeResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["montajes"])

# Database connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'luiggi_home')
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]


# === MONTADORES (Instaladores) ===

@router.get("/montadores")
async def get_montadores(status: str = None):
    """Get all montadores (installers), optionally filtered by status"""
    try:
        query = {}
        if status:
            query["status"] = status
        
        montadores = await db.montadores.find(query, {"_id": 0}).sort("name", 1).to_list(500)
        
        # Añadir conteo de montajes por montador
        for m in montadores:
            count = await db.montajes.count_documents({"montadorId": m.get("id", "")})
            m["totalMontajes"] = count
        
        return montadores
    except Exception as e:
        logger.error(f"Get montadores error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/montadores/{montador_id}")
async def get_montador(montador_id: str):
    """Get a specific montador by ID"""
    try:
        montador = await db.montadores.find_one({"id": montador_id}, {"_id": 0})
        if not montador:
            raise HTTPException(status_code=404, detail="Montador no encontrado")
        
        # Añadir conteo de montajes
        montador["totalMontajes"] = await db.montajes.count_documents({"montadorId": montador_id})
        
        return montador
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get montador error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/montadores")
async def create_montador(montador: MontadorCreate):
    """Create a new montador"""
    try:
        now = datetime.now(timezone.utc).isoformat()
        montador_data = {
            "id": f"MON-{uuid.uuid4().hex[:8].upper()}",
            **montador.model_dump(),
            "createdAt": now,
            "updatedAt": now
        }
        
        await db.montadores.insert_one(montador_data)
        if "_id" in montador_data:
            del montador_data["_id"]
        
        return montador_data
    except Exception as e:
        logger.error(f"Create montador error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/montadores/{montador_id}")
async def update_montador(montador_id: str, montador: MontadorUpdate):
    """Update a montador"""
    try:
        update_data = {k: v for k, v in montador.model_dump().items() if v is not None}
        update_data["updatedAt"] = datetime.now(timezone.utc).isoformat()
        
        result = await db.montadores.update_one(
            {"id": montador_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Montador no encontrado")
        
        updated = await db.montadores.find_one({"id": montador_id}, {"_id": 0})
        return updated
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update montador error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/montadores/{montador_id}")
async def delete_montador(montador_id: str):
    """Delete a montador"""
    try:
        result = await db.montadores.delete_one({"id": montador_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Montador no encontrado")
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
    end_date: str = None
):
    """Get all montajes (installations), with optional filters"""
    try:
        query = {}
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
        
        montajes = await db.montajes.find(query, {"_id": 0}).sort("scheduledDate", 1).to_list(500)
        return montajes
    except Exception as e:
        logger.error(f"Get montajes error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/montajes/{montaje_id}")
async def get_montaje(montaje_id: str):
    """Get a specific montaje by ID"""
    try:
        montaje = await db.montajes.find_one({"id": montaje_id}, {"_id": 0})
        if not montaje:
            raise HTTPException(status_code=404, detail="Montaje no encontrado")
        return montaje
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get montaje error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/montajes")
async def create_montaje(montaje: MontajeCreate):
    """Create a new montaje (installation appointment)"""
    try:
        now = datetime.now(timezone.utc).isoformat()
        
        # Obtener nombre del montador si no viene
        montador_name = montaje.montadorName
        if not montador_name and montaje.montadorId:
            montador = await db.montadores.find_one({"id": montaje.montadorId}, {"_id": 0, "name": 1})
            if montador:
                montador_name = montador.get("name", "")
        
        montaje_data = {
            "id": f"MTJ-{uuid.uuid4().hex[:8].upper()}",
            **montaje.model_dump(),
            "montadorName": montador_name,
            "createdAt": now,
            "updatedAt": now
        }
        
        await db.montajes.insert_one(montaje_data)
        if "_id" in montaje_data:
            del montaje_data["_id"]
        
        return montaje_data
    except Exception as e:
        logger.error(f"Create montaje error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/montajes/{montaje_id}")
async def update_montaje(montaje_id: str, montaje: MontajeUpdate):
    """Update a montaje"""
    try:
        update_data = {k: v for k, v in montaje.model_dump().items() if v is not None}
        update_data["updatedAt"] = datetime.now(timezone.utc).isoformat()
        
        # Actualizar nombre del montador si cambió el ID
        if "montadorId" in update_data:
            montador = await db.montadores.find_one({"id": update_data["montadorId"]}, {"_id": 0, "name": 1})
            if montador:
                update_data["montadorName"] = montador.get("name", "")
        
        result = await db.montajes.update_one(
            {"id": montaje_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Montaje no encontrado")
        
        updated = await db.montajes.find_one({"id": montaje_id}, {"_id": 0})
        return updated
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update montaje error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/montajes/{montaje_id}")
async def delete_montaje(montaje_id: str):
    """Delete a montaje"""
    try:
        result = await db.montajes.delete_one({"id": montaje_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Montaje no encontrado")
        return {"success": True, "message": "Montaje eliminado"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete montaje error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/montadores/{montador_id}/montajes")
async def get_montajes_by_montador(montador_id: str, status: str = None):
    """Get all montajes for a specific montador"""
    try:
        query = {"montadorId": montador_id}
        if status:
            query["status"] = status
        
        montajes = await db.montajes.find(query, {"_id": 0}).sort("scheduledDate", 1).to_list(100)
        return montajes
    except Exception as e:
        logger.error(f"Get montajes by montador error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
