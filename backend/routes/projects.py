"""
Router de PROYECTOS — extraído tal cual de server.py (endpoints vivos, mismo orden de rutas).
"""
import io
import re
import csv
import uuid
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends, Request, Response
from fastapi.responses import StreamingResponse

from services.db_client import get_db as _get_db_singleton
db = _get_db_singleton()
from services.jwt_service import (
    get_current_user, require_auth, require_admin, ADMIN_ROLE_FLAGS,
    create_access_token, create_refresh_token, verify_refresh_token,
)

from services.activity_tracker import get_tracker, ActivityType

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Projects"])

from models.schemas import ProjectModel, ProjectCreate, ProjectUpdate


@router.get("/projects", response_model=List[ProjectModel])
async def get_projects(
    user_id: Optional[str] = None,
    client_code: Optional[str] = None,
    include_all: Optional[bool] = False
):
    """
    Obtener proyectos/presupuestos.
    - user_id: Filtrar por usuario
    - client_code: Filtrar por código de cliente (para ver solo presupuestos de ese cliente)
    - include_all: Si es True, devuelve todos (requiere permisos de admin/gerente)
    
    Por defecto, cada usuario solo ve sus propios presupuestos.
    Si tiene permisos especiales (isAdmin, isGerente, isDirectorComercial), puede ver todos.
    """
    query = {}
    
    # Filtrar por código de cliente si se especifica
    if client_code:
        query["clientCode"] = client_code
    
    # Filtrar por usuario si se especifica
    if user_id and not include_all:
        query["userId"] = user_id
    
    projects = await db.projects.find(query, {"_id": 0}).to_list(1000)
    return projects

@router.get("/projects/by-client/{client_code}")
async def get_projects_by_client(client_code: str):
    """
    Obtener todos los presupuestos de un cliente específico.
    Útil para ver el historial de presupuestos de un cliente.
    """
    projects = await db.projects.find(
        {"clientCode": client_code.upper()},
        {"_id": 0}
    ).sort("createdAt", -1).to_list(500)
    
    return {
        "clientCode": client_code.upper(),
        "totalProjects": len(projects),
        "projects": projects
    }

@router.get("/projects/summary-by-client")
async def get_projects_summary_by_client():
    """
    Obtener resumen de presupuestos agrupados por código de cliente.
    Para vista de administrador/gerente.
    """
    pipeline = [
        {
            "$group": {
                "_id": "$clientCode",
                "count": {"$sum": 1},
                "totalPvp": {"$sum": "$totalPvp"},
                "lastProject": {"$max": "$createdAt"},
                "projects": {"$push": {"id": "$id", "budgetNumber": "$budgetNumber", "status": "$status"}}
            }
        },
        {"$sort": {"lastProject": -1}}
    ]
    
    summary = await db.projects.aggregate(pipeline).to_list(500)
    
    return {
        "totalClients": len(summary),
        "clients": summary
    }


@router.get("/projects/{project_id}", response_model=ProjectModel)
async def get_project(project_id: str):
    """Obtener un proyecto por ID"""
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return project

@router.get("/projects/check-budget-number/{budget_number}")
async def check_budget_number(budget_number: str):
    """Verificar si ya existe un presupuesto con este número"""
    project = await db.projects.find_one({"budgetNumber": budget_number}, {"_id": 0})
    if project:
        return {
            "exists": True,
            "projectId": project.get("id"),
            "customerName": project.get("customerName", "Sin nombre"),
            "createdAt": project.get("createdAt")
        }
    return {"exists": False}

@router.post("/projects", response_model=ProjectModel)
async def create_project(project: ProjectCreate, user_id: str, client_code: Optional[str] = None, current_user: dict = Depends(require_auth)):
    """
    Crear un nuevo proyecto/presupuesto.
    El client_code se usa para agrupar presupuestos por cliente.
    """
    project_data = project.model_dump()
    project_data["id"] = f"proj-{uuid.uuid4().hex[:8]}"
    project_data["userId"] = user_id
    
    # Usar clientCode del proyecto o del parámetro
    if client_code and not project_data.get("clientCode"):
        project_data["clientCode"] = client_code.upper()
    elif project_data.get("clientCode"):
        project_data["clientCode"] = project_data["clientCode"].upper()
    
    project_data["createdAt"] = datetime.now(timezone.utc).isoformat()
    project_data["updatedAt"] = datetime.now(timezone.utc).isoformat()
    
    await db.projects.insert_one(project_data)
    # insert_one añade _id (ObjectId no serializable). Quitarlo antes de devolver.
    project_data.pop("_id", None)
    
    # Tracking de actividad
    tracker = get_tracker()
    if tracker:
        user = await db.users.find_one({"id": user_id}, {"_id": 0, "username": 1})
        await tracker.track(
            user_id=user_id,
            username=user.get("username") if user else "unknown",
            activity_type=ActivityType.BUDGET_CREATE,
            details={"projectId": project_data["id"], "budgetNumber": project_data.get("budgetNumber")}
        )
    
    logger.info(f"Proyecto creado: {project_data['id']} para cliente: {project_data.get('clientCode', 'SIN CLIENTE')}")
    return project_data

@router.put("/projects/{project_id}", response_model=ProjectModel)
async def update_project(project_id: str, project: ProjectUpdate, current_user: dict = Depends(require_auth)):
    """Actualizar un proyecto guardando snapshot de versión anterior"""
    existing = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    update_data = {k: v for k, v in project.model_dump().items() if v is not None}
    now = datetime.now(timezone.utc)
    update_data["updatedAt"] = now

    # Guardar snapshot de la versión anterior si cambian items o totales
    items_changed = (
        "itemsMontada" in update_data or
        "itemsDespiece" in update_data or
        "totalPvp" in update_data
    )
    if items_changed:
        snapshot = {
            "versionAt": existing.get("updatedAt", existing.get("createdAt", now.isoformat())),
            "savedAt": now.isoformat(),
            "totalPvp": existing.get("totalPvp", 0),
            "totalCoste": existing.get("totalCoste", 0),
            "margen": existing.get("margen", 0),
            "totalConIVA": existing.get("totalConIVA", 0),
            "itemsMontada": existing.get("itemsMontada", []),
            "itemsDespiece": existing.get("itemsDespiece", []),
            "status": existing.get("status", "borrador"),
        }
        await db.projects.update_one(
            {"id": project_id},
            {"$push": {"versions": snapshot}}
        )

    if update_data:
        await db.projects.update_one({"id": project_id}, {"$set": update_data})

    # Tracking de actividad
    tracker = get_tracker()
    if tracker and existing.get("userId"):
        user = await db.users.find_one({"id": existing["userId"]}, {"_id": 0, "username": 1})
        await tracker.track(
            user_id=existing["userId"],
            username=user.get("username") if user else "unknown",
            activity_type=ActivityType.BUDGET_UPDATE,
            details={"projectId": project_id}
        )

    updated = await db.projects.find_one({"id": project_id}, {"_id": 0})
    return updated


@router.post("/projects/{project_id}/clone")
async def clone_project(project_id: str, user_id: str, body: dict = {}, current_user: dict = Depends(require_auth)):
    """
    Duplicar un presupuesto existente como nuevo borrador.
    Copia todos los items, colores y materiales.
    El nuevo presupuesto parte como 'borrador' con número autogenerado.
    """
    original = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not original:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    now = datetime.now(timezone.utc)
    new_budget_number = body.get("budgetNumber") or f"{original.get('budgetNumber', 'COPIA')}-COPIA"

    new_project = {
        "id": f"proj-{uuid.uuid4().hex[:8]}",
        "userId": user_id,
        "clientCode": original.get("clientCode", ""),
        "budgetNumber": new_budget_number,
        "customerName": original.get("customerName", ""),
        "customerAddress": original.get("customerAddress", ""),
        "internalReference": original.get("internalReference", ""),
        "itemsMontada": original.get("itemsMontada", []),
        "itemsDespiece": original.get("itemsDespiece", []),
        "doorColorLow": original.get("doorColorLow", ""),
        "doorColorHigh": original.get("doorColorHigh", ""),
        "doorColorColumns": original.get("doorColorColumns", ""),
        "sideColor": original.get("sideColor", ""),
        "selectedCarcassMaterialId": original.get("selectedCarcassMaterialId"),
        "totalPvp": original.get("totalPvp", 0),
        "totalCoste": original.get("totalCoste", 0),
        "margen": original.get("margen", 0),
        "descuentoAplicado": original.get("descuentoAplicado", 0),
        "totalConIVA": original.get("totalConIVA", 0),
        "ivaRate": original.get("ivaRate", 21.0),
        "status": "borrador",
        "validUntil": (now.replace(microsecond=0) + timedelta(days=30)).isoformat(),
        "statusHistory": [{
            "from": "—",
            "to": "borrador",
            "at": now.isoformat(),
            "by": "sistema",
            "note": f"Clonado de {original.get('budgetNumber', project_id)}"
        }],
        "versions": [],
        "createdAt": now,
        "updatedAt": now,
        "clonedFrom": project_id,
    }

    await db.projects.insert_one(new_project)
    new_project.pop("_id", None)
    return new_project

@router.delete("/projects/{project_id}")
async def delete_project(project_id: str, current_user: dict = Depends(require_auth)):
    """Eliminar un proyecto"""
    result = await db.projects.delete_one({"id": project_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return {"message": "Proyecto eliminado"}


@router.patch("/projects/{project_id}/status")
async def change_project_status(project_id: str, body: dict, current_user: dict = Depends(require_auth)):
    """
    Cambiar el estado de un presupuesto con historial de transiciones.
    
    Estados válidos: borrador, enviado, aceptado, en_fabricacion, entregado, rechazado
    Transiciones permitidas:
      borrador       → enviado
      enviado        → aceptado, rechazado
      aceptado       → en_fabricacion, rechazado
      en_fabricacion → entregado
      rechazado      → borrador  (reabrir)
      entregado      → (estado final)
    """
    VALID_TRANSITIONS = {
        "borrador":       ["enviado"],
        "draft":          ["enviado"],  # compatibilidad con registros antiguos
        "enviado":        ["aceptado", "rechazado"],
        "aceptado":       ["en_fabricacion", "rechazado"],
        "en_fabricacion": ["entregado"],
        "rechazado":      ["borrador"],
        "entregado":      [],
    }

    new_status = body.get("status")
    changed_by = body.get("changedBy", "sistema")
    note = body.get("note", "")

    if not new_status:
        raise HTTPException(status_code=400, detail="Campo 'status' requerido")

    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    current_status = project.get("status", "borrador")
    allowed = VALID_TRANSITIONS.get(current_status, [])

    if new_status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Transición no permitida: '{current_status}' → '{new_status}'. Permitidas: {allowed}"
        )

    now = datetime.now(timezone.utc)

    # Campos de fecha según nuevo estado
    date_fields = {}
    if new_status == "enviado":
        date_fields["sentAt"] = now
    elif new_status == "aceptado":
        date_fields["acceptedAt"] = now
    elif new_status == "rechazado":
        date_fields["rejectedAt"] = now
    elif new_status == "entregado":
        date_fields["deliveredAt"] = now
    elif new_status == "borrador":
        # Al reabrir, limpiar fecha de rechazo
        date_fields["rejectedAt"] = None

    # Entrada de historial
    history_entry = {
        "from": current_status,
        "to": new_status,
        "at": now.isoformat(),
        "by": changed_by,
        "note": note
    }

    update_data = {
        "status": new_status,
        "updatedAt": now,
        **date_fields
    }

    await db.projects.update_one(
        {"id": project_id},
        {
            "$set": update_data,
            "$push": {"statusHistory": history_entry}
        }
    )

    updated = await db.projects.find_one({"id": project_id}, {"_id": 0})
    return updated


@router.get("/projects/{project_id}/status-history")
async def get_project_status_history(project_id: str):
    """Obtener el historial de cambios de estado de un presupuesto"""
    project = await db.projects.find_one({"id": project_id}, {"_id": 0, "statusHistory": 1, "status": 1, "budgetNumber": 1})
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return {
        "budgetNumber": project.get("budgetNumber"),
        "currentStatus": project.get("status"),
        "history": project.get("statusHistory", [])
    }


# ============================================
# INIT DATA (seed admin user if needed)
# ============================================
