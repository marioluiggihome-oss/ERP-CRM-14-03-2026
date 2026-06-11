"""
Kitchen 3D Projects - API Router
==================================
Endpoints para gestión de proyectos de diseño de cocinas 3D.
Permite crear, listar, actualizar y eliminar proyectos, así como
gestionar renders con iteración rápida (cambio de materiales sin
empezar de cero).

Endpoints:
- GET    /api/kitchen-projects              → Listar proyectos del usuario
- POST   /api/kitchen-projects              → Crear nuevo proyecto
- GET    /api/kitchen-projects/{id}         → Detalle de proyecto
- PUT    /api/kitchen-projects/{id}         → Actualizar proyecto
- DELETE /api/kitchen-projects/{id}         → Eliminar proyecto
- POST   /api/kitchen-projects/{id}/render  → Generar render para proyecto
- POST   /api/kitchen-projects/{id}/iterate → Iteración rápida (cambiar material/color)
- GET    /api/kitchen-projects/{id}/renders → Historial de renders del proyecto
"""
import logging
import time
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from services.jwt_service import require_auth
from services.luiggi_ai import get_render_service

logger = logging.getLogger("kitchen_projects")

kitchen_projects_router = APIRouter(prefix="/kitchen-projects", tags=["Kitchen 3D Projects"])


# ─── Modelos ──────────────────────────────────────────────────────────────────

class KitchenProjectCreate(BaseModel):
    """Crear un nuevo proyecto de cocina."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    layout: str = Field(default="L-shape", description="L-shape, U-shape, galley, island, straight")
    cabinet_material: str = Field(default="white_matte")
    countertop_material: str = Field(default="quartz_white")
    style: str = Field(default="photorealistic")
    handle_style: str = Field(default="bar_black")
    floor_material: str = Field(default="wood_oak")
    lighting: str = Field(default="natural")


class KitchenProjectUpdate(BaseModel):
    """Actualizar un proyecto existente."""
    name: Optional[str] = None
    description: Optional[str] = None
    layout: Optional[str] = None
    cabinet_material: Optional[str] = None
    countertop_material: Optional[str] = None
    style: Optional[str] = None
    handle_style: Optional[str] = None
    floor_material: Optional[str] = None
    lighting: Optional[str] = None


class IterateRequest(BaseModel):
    """Solicitud de iteración rápida sobre un render existente."""
    change_description: str = Field(..., description="Descripción del cambio deseado (ej: 'cambiar encimera a granito negro')")
    base_render_id: Optional[str] = Field(None, description="ID del render base para iterar")


# ─── Almacenamiento en memoria (para MVP; migrar a MongoDB después) ───────────

_projects_db: dict = {}  # user_id -> list of projects
_project_counter = 0


def _get_user_projects(user_id: str) -> list:
    """Obtiene los proyectos del usuario."""
    if user_id not in _projects_db:
        _projects_db[user_id] = []
    return _projects_db[user_id]


def _find_project(user_id: str, project_id: str):
    """Busca un proyecto por ID."""
    projects = _get_user_projects(user_id)
    for p in projects:
        if p["id"] == project_id:
            return p
    return None


# ─── Endpoints ────────────────────────────────────────────────────────────────

@kitchen_projects_router.get("")
async def list_projects(user=Depends(require_auth)):
    """Lista todos los proyectos del usuario autenticado."""
    user_id = user.get("sub", user.get("id", "unknown"))
    projects = _get_user_projects(user_id)
    return {"projects": projects, "total": len(projects)}


@kitchen_projects_router.post("")
async def create_project(data: KitchenProjectCreate, user=Depends(require_auth)):
    """Crea un nuevo proyecto de cocina."""
    global _project_counter
    user_id = user.get("sub", user.get("id", "unknown"))
    _project_counter += 1

    project = {
        "id": f"kp_{_project_counter}_{int(time.time())}",
        "user_id": user_id,
        "name": data.name,
        "description": data.description,
        "layout": data.layout,
        "cabinet_material": data.cabinet_material,
        "countertop_material": data.countertop_material,
        "style": data.style,
        "handle_style": data.handle_style,
        "floor_material": data.floor_material,
        "lighting": data.lighting,
        "status": "draft",
        "photo_urls": [],
        "renders": [],
        "created_at": time.time(),
        "updated_at": time.time(),
    }

    _get_user_projects(user_id).append(project)
    return {"project": project}


@kitchen_projects_router.get("/{project_id}")
async def get_project(project_id: str, user=Depends(require_auth)):
    """Obtiene el detalle de un proyecto."""
    user_id = user.get("sub", user.get("id", "unknown"))
    project = _find_project(user_id, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return {"project": project}


@kitchen_projects_router.put("/{project_id}")
async def update_project(project_id: str, data: KitchenProjectUpdate, user=Depends(require_auth)):
    """Actualiza un proyecto existente."""
    user_id = user.get("sub", user.get("id", "unknown"))
    project = _find_project(user_id, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    update_data = data.model_dump(exclude_none=True)
    for key, value in update_data.items():
        project[key] = value
    project["updated_at"] = time.time()

    return {"project": project}


@kitchen_projects_router.delete("/{project_id}")
async def delete_project(project_id: str, user=Depends(require_auth)):
    """Elimina un proyecto."""
    user_id = user.get("sub", user.get("id", "unknown"))
    projects = _get_user_projects(user_id)
    project = _find_project(user_id, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    projects.remove(project)
    return {"success": True, "message": "Proyecto eliminado"}


@kitchen_projects_router.post("/{project_id}/render")
async def generate_project_render(project_id: str, user=Depends(require_auth)):
    """Genera un render 3D para el proyecto con sus parámetros actuales."""
    user_id = user.get("sub", user.get("id", "unknown"))
    project = _find_project(user_id, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    project["status"] = "generating"
    render_service = get_render_service()

    try:
        result = await render_service.generate_render_from_params(
            layout=project["layout"],
            countertop=project["countertop_material"],
            cabinets=project["cabinet_material"],
            handles=project["handle_style"],
            floor=project["floor_material"],
            lighting=project["lighting"],
            style=project["style"],
            additional_details=project.get("description"),
        )

        render_entry = {
            "id": f"r_{int(time.time())}",
            "status": result.get("status", "completed"),
            "result": result,
            "params": {
                "layout": project["layout"],
                "cabinet_material": project["cabinet_material"],
                "countertop_material": project["countertop_material"],
                "style": project["style"],
            },
            "created_at": time.time(),
        }

        project["renders"].append(render_entry)
        project["status"] = "completed" if result.get("success") else "failed"
        project["updated_at"] = time.time()

        return {"render": render_entry}

    except Exception as e:
        logger.error(f"Error generando render para proyecto {project_id}: {e}")
        project["status"] = "failed"
        raise HTTPException(status_code=500, detail="Error al generar el render")


@kitchen_projects_router.post("/{project_id}/iterate")
async def iterate_render(project_id: str, data: IterateRequest, user=Depends(require_auth)):
    """
    Iteración rápida: modifica un aspecto del diseño sin empezar de cero.
    Usa la descripción del cambio para regenerar con los parámetros actualizados.
    """
    user_id = user.get("sub", user.get("id", "unknown"))
    project = _find_project(user_id, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    project["status"] = "generating"
    render_service = get_render_service()

    # Construir descripción completa con el cambio solicitado
    base_description = (
        f"Cocina con distribución {project['layout']}, "
        f"muebles de {project['cabinet_material']}, "
        f"encimera de {project['countertop_material']}, "
        f"estilo {project['style']}. "
        f"CAMBIO SOLICITADO: {data.change_description}"
    )

    try:
        result = await render_service.generate_render(
            description=base_description,
            params_override=None,
        )

        render_entry = {
            "id": f"r_{int(time.time())}",
            "status": result.get("status", "completed"),
            "result": result,
            "change_request": data.change_description,
            "is_iteration": True,
            "created_at": time.time(),
        }

        project["renders"].append(render_entry)
        project["status"] = "completed" if result.get("success") else "failed"
        project["updated_at"] = time.time()

        return {"render": render_entry}

    except Exception as e:
        logger.error(f"Error en iteración para proyecto {project_id}: {e}")
        project["status"] = "failed"
        raise HTTPException(status_code=500, detail="Error en la iteración")


@kitchen_projects_router.get("/{project_id}/renders")
async def list_renders(project_id: str, user=Depends(require_auth)):
    """Lista el historial de renders de un proyecto."""
    user_id = user.get("sub", user.get("id", "unknown"))
    project = _find_project(user_id, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    return {"renders": project["renders"], "total": len(project["renders"])}
