"""
Router para Proyectos/Presupuestos
"""
import logging
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Request, Depends

from config import db
from models.schemas import ProjectModel, ProjectCreate, ProjectUpdate
from services.jwt_service import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("", response_model=List[ProjectModel])
async def get_projects(
    user_id: str = None,
    client_code: str = None,
    status: str = None,
    skip: int = 0,
    limit: int = 50
):
    """Obtener proyectos/presupuestos con filtros"""
    query = {}
    
    if user_id:
        query["userId"] = user_id
    if client_code:
        query["clientCode"] = client_code
    if status:
        query["status"] = status
    
    projects = await db.projects.find(query, {"_id": 0}).sort("createdAt", -1).skip(skip).limit(limit).to_list(limit)
    return projects


@router.get("/by-client/{client_code}")
async def get_projects_by_client(client_code: str):
    """Obtener todos los presupuestos de un cliente"""
    projects = await db.projects.find(
        {"clientCode": client_code},
        {"_id": 0}
    ).sort("createdAt", -1).to_list(100)
    return projects


@router.get("/summary-by-client")
async def get_projects_summary_by_client():
    """Obtener resumen de presupuestos agrupados por cliente"""
    pipeline = [
        {"$match": {"clientCode": {"$ne": ""}}},
        {"$group": {
            "_id": "$clientCode",
            "count": {"$sum": 1},
            "totalValue": {"$sum": "$totalPvp"},
            "lastProject": {"$max": "$createdAt"}
        }},
        {"$sort": {"lastProject": -1}}
    ]
    results = await db.projects.aggregate(pipeline).to_list(100)
    return [
        {
            "clientCode": r["_id"],
            "projectCount": r["count"],
            "totalValue": r["totalValue"],
            "lastProjectDate": r["lastProject"]
        }
        for r in results
    ]


@router.get("/check-budget-number/{budget_number}")
async def check_budget_number(budget_number: str):
    """Verificar si un número de presupuesto ya existe"""
    existing = await db.projects.find_one({"budgetNumber": budget_number})
    return {"exists": existing is not None}


@router.get("/{project_id}", response_model=ProjectModel)
async def get_project(project_id: str):
    """Obtener un proyecto por ID"""
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return project


@router.post("", response_model=ProjectModel)
async def create_project(project: ProjectCreate, current_user: dict = Depends(get_current_user)):
    """Crear un nuevo proyecto/presupuesto"""
    project_dict = project.model_dump()
    project_dict["id"] = f"proj-{__import__('uuid').uuid4().hex[:8]}"
    project_dict["userId"] = current_user.get("id")
    project_dict["createdAt"] = datetime.now(timezone.utc)
    project_dict["updatedAt"] = datetime.now(timezone.utc)
    
    await db.projects.insert_one(project_dict)
    
    result = await db.projects.find_one({"id": project_dict["id"]}, {"_id": 0})
    return result


@router.put("/{project_id}", response_model=ProjectModel)
async def update_project(project_id: str, project: ProjectUpdate):
    """Actualizar un proyecto existente"""
    existing = await db.projects.find_one({"id": project_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    update_data = {k: v for k, v in project.model_dump().items() if v is not None}
    update_data["updatedAt"] = datetime.now(timezone.utc)
    
    await db.projects.update_one({"id": project_id}, {"$set": update_data})
    
    updated = await db.projects.find_one({"id": project_id}, {"_id": 0})
    return updated


@router.delete("/{project_id}")
async def delete_project(project_id: str):
    """Eliminar un proyecto"""
    result = await db.projects.delete_one({"id": project_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return {"success": True}
