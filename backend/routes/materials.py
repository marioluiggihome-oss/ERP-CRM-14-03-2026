# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
Routes for Materials Management
Extracted from server.py for better maintainability
"""
from fastapi import APIRouter, HTTPException, Depends
from services.jwt_service import require_auth
from pydantic import BaseModel
from typing import List, Optional
import logging
import uuid
import os

from dotenv import load_dotenv
from services.db_client import get_db as _get_db

load_dotenv()
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/materials", tags=["materials"])

# Database connection


# Pydantic models
class MaterialCreate(BaseModel):
    name: str
    type: str = "carcass"  # carcass, back, shelf, door, countertop
    thickness: float = 18.0
    pricePerM2: float = 0.0
    library: str = "ZC"
    color: str = ""
    finish: str = ""
    description: str = ""


class MaterialModel(BaseModel):
    id: str = ""
    name: str
    type: str = "carcass"
    thickness: float = 18.0
    pricePerM2: float = 0.0
    library: str = "ZC"
    color: str = ""
    finish: str = ""
    description: str = ""

    def __init__(self, **data):
        if not data.get("id"):
            data["id"] = f"mat-{uuid.uuid4().hex[:8]}"
        super().__init__(**data)

    class Config:
        extra = "allow"


@router.get("", response_model=List[MaterialModel])
async def get_materials(library: str = None, current_user: dict = Depends(require_auth)):
    """Obtener todos los materiales, opcionalmente filtrados por biblioteca"""
    query = {}
    if library:
        query["library"] = library.upper()
    materials = await _get_db().materials.find(query, {"_id": 0}).to_list(1000)
    return materials


@router.post("", response_model=MaterialModel)
async def create_material(material: MaterialCreate, user=Depends(require_auth)):
    """Crear un nuevo material"""
    material_obj = MaterialModel(**material.model_dump())
    await _get_db().materials.insert_one(material_obj.model_dump())
    logger.info(f"Material created: {material_obj.name}")
    return material_obj


@router.put("/{material_id}", response_model=MaterialModel)
async def update_material(material_id: str, material: MaterialCreate, user=Depends(require_auth)):
    """Actualizar un material"""
    existing = await _get_db().materials.find_one({"id": material_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Material no encontrado")
    
    await _get_db().materials.update_one({"id": material_id}, {"$set": material.model_dump()})
    updated = await _get_db().materials.find_one({"id": material_id}, {"_id": 0})
    logger.info(f"Material updated: {material_id}")
    return updated


@router.delete("/{material_id}")
async def delete_material(material_id: str, user=Depends(require_auth)):
    """Eliminar un material"""
    # Check if it's the last one
    count = await _get_db().materials.count_documents({})
    if count <= 1:
        raise HTTPException(status_code=400, detail="Debe existir al menos un material")
    
    result = await _get_db().materials.delete_one({"id": material_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Material no encontrado")
    
    logger.info(f"Material deleted: {material_id}")
    return {"message": "Material eliminado"}
