"""
Kitchen 3D Projects - API Router (v2)
========================================
Endpoints para gestión completa de proyectos de diseño de cocinas 3D.
Incluye:
- Gestión de proyectos (crear, listar, actualizar, eliminar)
- Subida ilimitada de fotos y vídeos con instrucciones
- Medidas de paredes proporcionadas por el usuario
- Muebles personalizables definidos por el usuario
- Generación de renders con IA
- Iteración rápida (cambio de materiales sin empezar de cero)
- Aprobación con generación de documentación técnica:
  - Plano de instalaciones (enchufes, tomas de agua con coordenadas)
  - Alzado alámbrico SVG con cotas
  - Despiece de muebles con valoración por biblioteca (ZC/MV)
"""
import logging
import time
import math
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from services.jwt_service import require_auth
from services.luiggi_ai import get_render_service

logger = logging.getLogger("kitchen_projects")

kitchen_projects_router = APIRouter(prefix="/kitchen-projects", tags=["Kitchen 3D Projects"])


# ─── Modelos ──────────────────────────────────────────────────────────────────

class KitchenProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    layout: Optional[str] = None
    cabinet_material: Optional[str] = None
    countertop_material: Optional[str] = None
    style: Optional[str] = None


class KitchenProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    layout: Optional[str] = None
    cabinet_material: Optional[str] = None
    countertop_material: Optional[str] = None
    style: Optional[str] = None


class MeasurementCreate(BaseModel):
    wall_label: str
    wall_width: Optional[float] = None
    wall_height: Optional[float] = None
    window_width: Optional[float] = None
    window_height: Optional[float] = None
    window_from_floor: Optional[float] = None
    window_from_left: Optional[float] = None
    door_width: Optional[float] = None
    door_height: Optional[float] = None
    door_from_left: Optional[float] = None
    notes: Optional[str] = None


class CabinetCreate(BaseModel):
    cabinet_type: str
    wall_label: Optional[str] = None
    width: Optional[float] = None
    height: Optional[float] = None
    depth: Optional[float] = None
    position_from_left: Optional[float] = None
    material: Optional[str] = None
    color: Optional[str] = None
    handle_type: Optional[str] = None
    notes: Optional[str] = None


class IterateRequest(BaseModel):
    change_description: str
    base_render_id: Optional[str] = None


class ApproveRequest(BaseModel):
    render_id: str
    library: str = Field(default="ZC", description="ZC o MV")


class ComposeRenderRequest(BaseModel):
    """Render fiel a partir de un PLANO EN PLANTA y un BOCETO por cada PARED."""
    floor_plan: Optional[str] = None          # plano en planta (dataURL/base64/PDF)
    wall_sketches: Optional[List[str]] = None  # bocetos por pared (dataURL/base64), en orden
    brief: Optional[str] = None               # acabados/colores/materiales/estilo deseados
    style: Optional[str] = None


# ─── Almacenamiento en memoria (MVP) ─────────────────────────────────────────

_projects_db: dict = {}
_project_counter = 0


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _get_user_projects(user_id: str) -> list:
    if user_id not in _projects_db:
        _projects_db[user_id] = []
    return _projects_db[user_id]


def _find_project(user_id: str, project_id: str):
    projects = _get_user_projects(user_id)
    for p in projects:
        if p["id"] == project_id:
            return p
    return None


def _get_user_id(user):
    return user.get("sub", user.get("id", "unknown"))


# ─── Valoración por biblioteca ───────────────────────────────────────────────

LIBRARY_PRICE_PER_POINT = {"ZC": 1.0, "MV": 1.15}

CABINET_BASE_POINTS = {
    "bajo": {30: 85, 40: 110, 45: 120, 50: 135, 60: 155, 70: 175, 80: 195, 90: 220, 100: 250, 120: 290},
    "bajo fregadero": {60: 170, 70: 190, 80: 210, 90: 240, 100: 270, 120: 310},
    "alto": {30: 65, 40: 80, 45: 88, 50: 95, 60: 115, 70: 130, 80: 150, 90: 170},
    "columna": {40: 250, 50: 290, 60: 340, 70: 380, 80: 420},
    "rincon": {90: 280, 100: 320},
}


def _estimate_cabinet_points(cabinet_type: str, width: float) -> int:
    ct = cabinet_type.lower()
    table = None
    for key in CABINET_BASE_POINTS:
        if key in ct:
            table = CABINET_BASE_POINTS[key]
            break
    if not table:
        table = CABINET_BASE_POINTS["bajo"]

    widths = sorted(table.keys())
    closest = min(widths, key=lambda w: abs(w - width))
    return table[closest]


def _generate_installation_plan(measurements: list, cabinets: list) -> dict:
    """Genera el plano de instalaciones con coordenadas de enchufes y tomas."""
    walls = []
    for m in measurements:
        wall_width = m.get("wall_width", 300) or 300
        wall_height = m.get("wall_height", 260) or 260
        wall_label = m.get("wall_label", "Pared")

        outlets = []
        water_connections = []

        # Enchufes estándar: uno cada ~120cm a 110cm del suelo
        num_outlets = max(2, int(wall_width / 120))
        spacing = wall_width / (num_outlets + 1)
        for i in range(num_outlets):
            outlets.append({
                "x": round(spacing * (i + 1)),
                "y": 110,
                "description": f"Enchufe {i+1} (línea encimera)"
            })

        # Tomas de agua para fregadero
        sink_cabinets = [c for c in cabinets if c.get("wall_label") == wall_label and "fregadero" in (c.get("cabinet_type", "")).lower()]
        for sc in sink_cabinets:
            pos = sc.get("position_from_left", 0) or 0
            w = sc.get("width", 80) or 80
            center_x = pos + w / 2
            water_connections.append({"x": round(center_x - 10), "y": 40, "description": "Toma agua fría"})
            water_connections.append({"x": round(center_x + 10), "y": 40, "description": "Toma agua caliente"})
            water_connections.append({"x": round(center_x), "y": 15, "description": "Desagüe"})

        wall_data = {
            "wall": wall_label,
            "dimensions": {"width": wall_width, "height": wall_height},
            "outlets": outlets,
            "waterConnections": water_connections,
        }

        if m.get("window_width"):
            wall_data["window"] = {
                "width": m["window_width"],
                "height": m.get("window_height", 100),
                "fromFloor": m.get("window_from_floor", 110),
                "fromLeft": m.get("window_from_left", 60),
            }
        if m.get("door_width"):
            wall_data["door"] = {
                "width": m["door_width"],
                "height": m.get("door_height", 210),
                "fromLeft": m.get("door_from_left", 0),
            }
        if m.get("notes"):
            wall_data["notes"] = m["notes"]

        walls.append(wall_data)

    return {"type": "installation_plan", "walls": walls}


def _generate_wireframe_svg(wall_label: str, wall_width: float, wall_height: float, cabinets: list, measurement: dict) -> str:
    """Genera un SVG de alzado alámbrico con cotas."""
    scale = 2.0
    margin = 60
    svg_w = wall_width * scale + margin * 2
    svg_h = wall_height * scale + margin * 2 + 40

    elements = []
    elements.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_w} {svg_h}" width="{min(svg_w, 800)}" height="{min(svg_h, 400)}">')
    elements.append('<style>text{font-family:monospace;font-size:11px;fill:#333}line,rect{stroke:#555;fill:none}rect.wall{fill:#f8f8f8;stroke:#333;stroke-width:2}.cabinet{fill:#e8e8ff;stroke:#4444aa;stroke-width:1.5}.window{fill:#cceeff;stroke:#0088cc;stroke-width:1.5;stroke-dasharray:4 2}.door{fill:#ffe8cc;stroke:#cc6600;stroke-width:1.5}.dim{stroke:#999;stroke-width:0.8;marker-end:url(#arrow)}</style>')
    elements.append('<defs><marker id="arrow" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6" fill="#999"/></marker></defs>')

    # Wall rectangle
    wx, wy = margin, margin + 20
    elements.append(f'<rect class="wall" x="{wx}" y="{wy}" width="{wall_width*scale}" height="{wall_height*scale}"/>')

    # Title
    elements.append(f'<text x="{svg_w/2}" y="16" text-anchor="middle" font-weight="bold" font-size="13">{wall_label} — {wall_width} x {wall_height} cm</text>')

    # Cabinets
    wall_cabs = [c for c in cabinets if c.get("wall_label") == wall_label]
    countertop_y = 87  # cm from floor
    for cab in wall_cabs:
        ct = (cab.get("cabinet_type") or "").lower()
        cw = cab.get("width", 60) or 60
        ch = cab.get("height", 70) or 70
        pos = cab.get("position_from_left", 0) or 0

        if "alto" in ct:
            cy_cm = wall_height - 220  # altos a 220cm desde suelo
            cx = wx + pos * scale
            cy = wy + cy_cm * scale
        elif "columna" in ct:
            cy_cm = 0
            ch = cab.get("height", 220) or 220
            cx = wx + pos * scale
            cy = wy + (wall_height - ch) * scale
        else:
            cy_cm = wall_height - countertop_y
            cx = wx + pos * scale
            cy = wy + cy_cm * scale

        elements.append(f'<rect class="cabinet" x="{cx}" y="{cy}" width="{cw*scale}" height="{ch*scale}"/>')
        elements.append(f'<text x="{cx + cw*scale/2}" y="{cy + ch*scale/2 + 4}" text-anchor="middle" font-size="9">{cab.get("cabinet_type","")}</text>')
        elements.append(f'<text x="{cx + cw*scale/2}" y="{cy + ch*scale/2 + 16}" text-anchor="middle" font-size="8" fill="#666">{cw}x{ch}cm</text>')

    # Window
    if measurement.get("window_width"):
        ww = measurement["window_width"]
        wh = measurement.get("window_height", 100) or 100
        wfl = measurement.get("window_from_floor", 110) or 110
        wfr = measurement.get("window_from_left", 60) or 60
        vx = wx + wfr * scale
        vy = wy + (wall_height - wfl - wh) * scale
        elements.append(f'<rect class="window" x="{vx}" y="{vy}" width="{ww*scale}" height="{wh*scale}"/>')
        elements.append(f'<text x="{vx + ww*scale/2}" y="{vy + wh*scale/2}" text-anchor="middle" font-size="9" fill="#0088cc">Ventana {ww}x{wh}</text>')

    # Door
    if measurement.get("door_width"):
        dw = measurement["door_width"]
        dh = measurement.get("door_height", 210) or 210
        dfl = measurement.get("door_from_left", 0) or 0
        dx = wx + dfl * scale
        dy = wy + (wall_height - dh) * scale
        elements.append(f'<rect class="door" x="{dx}" y="{dy}" width="{dw*scale}" height="{dh*scale}"/>')
        elements.append(f'<text x="{dx + dw*scale/2}" y="{dy + dh*scale/2}" text-anchor="middle" font-size="9" fill="#cc6600">Puerta {dw}x{dh}</text>')

    # Dimension lines
    dim_y = wy + wall_height * scale + 25
    elements.append(f'<line class="dim" x1="{wx}" y1="{dim_y}" x2="{wx + wall_width*scale}" y2="{dim_y}"/>')
    elements.append(f'<text x="{wx + wall_width*scale/2}" y="{dim_y + 15}" text-anchor="middle">{wall_width} cm</text>')

    dim_x = wx - 25
    elements.append(f'<line class="dim" x1="{dim_x}" y1="{wy}" x2="{dim_x}" y2="{wy + wall_height*scale}"/>')
    elements.append(f'<text x="{dim_x - 5}" y="{wy + wall_height*scale/2}" text-anchor="middle" transform="rotate(-90,{dim_x-5},{wy + wall_height*scale/2})">{wall_height} cm</text>')

    elements.append('</svg>')
    return '\n'.join(elements)


def _generate_cabinet_breakdown(cabinets: list, library: str, default_material: str = "") -> dict:
    """Genera el despiece con valoración por puntos."""
    price_per_point = LIBRARY_PRICE_PER_POINT.get(library, 1.0)
    items = []
    total_points = 0

    for cab in cabinets:
        width = cab.get("width", 60) or 60
        points = _estimate_cabinet_points(cab.get("cabinet_type", "bajo"), width)
        price = round(points * price_per_point, 2)
        total_points += points

        items.append({
            "cabinetType": cab.get("cabinet_type", ""),
            "wall": cab.get("wall_label", ""),
            "dimensions": f"{width}x{cab.get('height', '?')}x{cab.get('depth', '?')} cm",
            "material": cab.get("material") or default_material or "Sin especificar",
            "color": cab.get("color") or "Sin especificar",
            "points": points,
            "price": price,
            "library": library,
        })

    return {
        "items": items,
        "totalPoints": total_points,
        "totalPrice": round(total_points * price_per_point, 2),
        "pricePerPoint": price_per_point,
    }


# ─── Endpoints: Proyectos ────────────────────────────────────────────────────

@kitchen_projects_router.get("")
async def list_projects(user=Depends(require_auth)):
    user_id = _get_user_id(user)
    projects = _get_user_projects(user_id)
    return {"projects": projects, "total": len(projects)}


@kitchen_projects_router.post("")
async def create_project(data: KitchenProjectCreate, user=Depends(require_auth)):
    global _project_counter
    user_id = _get_user_id(user)
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
        "status": "draft",
        "files": [],
        "measurements": [],
        "cabinets": [],
        "renders": [],
        "technical_docs": [],
        "created_at": time.time(),
        "updated_at": time.time(),
    }

    _get_user_projects(user_id).append(project)
    return {"project": project}


@kitchen_projects_router.get("/{project_id}")
async def get_project(project_id: str, user=Depends(require_auth)):
    user_id = _get_user_id(user)
    project = _find_project(user_id, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return {"project": project}


@kitchen_projects_router.put("/{project_id}")
async def update_project(project_id: str, data: KitchenProjectUpdate, user=Depends(require_auth)):
    user_id = _get_user_id(user)
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
    user_id = _get_user_id(user)
    projects = _get_user_projects(user_id)
    project = _find_project(user_id, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    projects.remove(project)
    return {"success": True, "message": "Proyecto eliminado"}


# ─── Endpoints: Archivos (fotos/vídeos ilimitados) ───────────────────────────

@kitchen_projects_router.post("/{project_id}/files")
async def upload_file(
    project_id: str,
    file: UploadFile = File(...),
    wall_label: Optional[str] = Form(None),
    file_type: str = Form("photo"),
    user=Depends(require_auth)
):
    """Sube una foto o vídeo asociado al proyecto. Sin límite de archivos."""
    user_id = _get_user_id(user)
    project = _find_project(user_id, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    # Validar MIME
    allowed_images = ["image/jpeg", "image/png", "image/webp", "image/heic"]
    allowed_videos = ["video/mp4", "video/webm", "video/quicktime", "video/x-msvideo"]
    content_type = file.content_type or ""

    if file_type == "photo" and content_type not in allowed_images:
        raise HTTPException(status_code=400, detail=f"Formato de imagen no soportado: {content_type}")
    if file_type == "video" and content_type not in allowed_videos:
        raise HTTPException(status_code=400, detail=f"Formato de vídeo no soportado: {content_type}")

    # En producción se subiría a S3; aquí guardamos metadata
    file_entry = {
        "id": f"f_{int(time.time())}_{len(project['files'])}",
        "file_name": file.filename,
        "file_type": file_type,
        "wall_label": wall_label,
        "mime_type": content_type,
        "uploaded_at": time.time(),
    }

    project["files"].append(file_entry)
    project["updated_at"] = time.time()
    return {"file": file_entry}


@kitchen_projects_router.get("/{project_id}/files")
async def list_files(project_id: str, user=Depends(require_auth)):
    user_id = _get_user_id(user)
    project = _find_project(user_id, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return {"files": project.get("files", [])}


# ─── Endpoints: Medidas ──────────────────────────────────────────────────────

@kitchen_projects_router.post("/{project_id}/measurements")
async def add_measurement(project_id: str, data: MeasurementCreate, user=Depends(require_auth)):
    """Añade medidas de una pared al proyecto."""
    user_id = _get_user_id(user)
    project = _find_project(user_id, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    measurement = {
        "id": f"m_{int(time.time())}_{len(project['measurements'])}",
        **data.model_dump(),
        "created_at": time.time(),
    }

    project["measurements"].append(measurement)
    project["updated_at"] = time.time()
    return {"measurement": measurement}


@kitchen_projects_router.get("/{project_id}/measurements")
async def list_measurements(project_id: str, user=Depends(require_auth)):
    user_id = _get_user_id(user)
    project = _find_project(user_id, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return {"measurements": project.get("measurements", [])}


# ─── Endpoints: Muebles ──────────────────────────────────────────────────────

@kitchen_projects_router.post("/{project_id}/cabinets")
async def add_cabinet(project_id: str, data: CabinetCreate, user=Depends(require_auth)):
    """Añade un mueble personalizado al proyecto."""
    user_id = _get_user_id(user)
    project = _find_project(user_id, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    cabinet = {
        "id": f"c_{int(time.time())}_{len(project['cabinets'])}",
        **data.model_dump(),
        "created_at": time.time(),
    }

    project["cabinets"].append(cabinet)
    project["updated_at"] = time.time()
    return {"cabinet": cabinet}


@kitchen_projects_router.delete("/{project_id}/cabinets/{cabinet_id}")
async def delete_cabinet(project_id: str, cabinet_id: str, user=Depends(require_auth)):
    user_id = _get_user_id(user)
    project = _find_project(user_id, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    project["cabinets"] = [c for c in project["cabinets"] if c["id"] != cabinet_id]
    project["updated_at"] = time.time()
    return {"success": True}


@kitchen_projects_router.get("/{project_id}/cabinets")
async def list_cabinets(project_id: str, user=Depends(require_auth)):
    user_id = _get_user_id(user)
    project = _find_project(user_id, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return {"cabinets": project.get("cabinets", [])}


# ─── Endpoints: Renders ──────────────────────────────────────────────────────

@kitchen_projects_router.post("/{project_id}/render")
async def generate_project_render(project_id: str, user=Depends(require_auth)):
    """Genera un render 3D respetando las indicaciones exactas del usuario."""
    user_id = _get_user_id(user)
    project = _find_project(user_id, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    project["status"] = "generating"
    render_service = get_render_service()

    # Construir prompt detallado con muebles y medidas
    cabinet_desc = ""
    for cab in project.get("cabinets", []):
        cabinet_desc += f"\n- {cab['cabinet_type']} ({cab.get('width','?')}x{cab.get('height','?')}cm) en {cab.get('wall_label','?')}"
        if cab.get("material"):
            cabinet_desc += f", material: {cab['material']}"
        if cab.get("color"):
            cabinet_desc += f", color: {cab['color']}"

    try:
        result = await render_service.generate_render_from_params(
            layout=project.get("layout", "L-shape"),
            countertop=project.get("countertop_material", "cuarzo blanco"),
            cabinets=project.get("cabinet_material", "blanco mate"),
            handles="integrado",
            floor="porcelánico efecto madera",
            lighting="natural",
            style=project.get("style", "fotorrealista"),
            additional_details=f"{project.get('description', '')} Muebles específicos: {cabinet_desc}" if cabinet_desc else project.get("description"),
        )

        render_entry = {
            "id": f"r_{int(time.time())}",
            "status": result.get("status", "completed"),
            "result": result,
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


@kitchen_projects_router.post("/{project_id}/render-compose")
async def generate_project_render_composed(project_id: str, data: ComposeRenderRequest, user=Depends(require_auth)):
    """Render fotorrealista FIEL combinando el plano en planta + un boceto por pared.

    Reutiliza el motor de imagen multi-referencia (Gemini 2.5 Flash Image) para que
    el render respete a la vez la distribución del plano y el diseño de cada pared.
    """
    user_id = _get_user_id(user)
    project = _find_project(user_id, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    sketches = [s for s in (data.wall_sketches or []) if s]
    if not data.floor_plan and not sketches:
        raise HTTPException(status_code=400, detail="Adjunta el plano en planta o al menos un boceto de pared.")

    project["status"] = "generating"
    render_service = get_render_service()

    # Brief: descripción del proyecto + muebles + acabados + texto libre del usuario.
    cabinet_desc = ""
    for cab in project.get("cabinets", []):
        cabinet_desc += f"\n- {cab['cabinet_type']} ({cab.get('width','?')}x{cab.get('height','?')}cm) en {cab.get('wall_label','?')}"
        if cab.get("material"):
            cabinet_desc += f", material: {cab['material']}"
        if cab.get("color"):
            cabinet_desc += f", color: {cab['color']}"
    parts = [
        project.get("description") or "",
        data.brief or "",
        f"Frentes: {project.get('cabinet_material','')}." if project.get("cabinet_material") else "",
        f"Encimera: {project.get('countertop_material','')}." if project.get("countertop_material") else "",
        f"Muebles específicos:{cabinet_desc}" if cabinet_desc else "",
    ]
    description = " ".join(p for p in parts if p).strip() or "Cocina moderna fotorrealista"

    try:
        result = await render_service.generate_render_composed(
            description=description,
            floor_plan=data.floor_plan,
            wall_sketches=sketches,
            params_override={"style": data.style or project.get("style", "fotorrealista")},
        )
        render_entry = {
            "id": f"r_{int(time.time())}",
            "status": result.get("status", "completed"),
            "result": result,
            "is_composed": True,
            "created_at": time.time(),
        }
        project["renders"].append(render_entry)
        project["status"] = "completed" if result.get("success") else "failed"
        project["updated_at"] = time.time()
        return {"render": render_entry}

    except Exception as e:
        logger.error(f"Error en render compuesto del proyecto {project_id}: {e}")
        project["status"] = "failed"
        raise HTTPException(status_code=500, detail="Error al generar el render")


@kitchen_projects_router.post("/{project_id}/iterate")
async def iterate_render(project_id: str, data: IterateRequest, user=Depends(require_auth)):
    """Iteración rápida: modifica un aspecto sin empezar de cero."""
    user_id = _get_user_id(user)
    project = _find_project(user_id, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    project["status"] = "generating"
    render_service = get_render_service()

    base_description = (
        f"Cocina con distribución {project.get('layout','')}, "
        f"muebles de {project.get('cabinet_material','')}, "
        f"encimera de {project.get('countertop_material','')}, "
        f"estilo {project.get('style','')}. "
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
    user_id = _get_user_id(user)
    project = _find_project(user_id, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return {"renders": project["renders"], "total": len(project["renders"])}


# ─── Endpoints: Aprobación y Documentación Técnica ───────────────────────────

@kitchen_projects_router.post("/{project_id}/approve")
async def approve_project(project_id: str, data: ApproveRequest, user=Depends(require_auth)):
    """
    Aprueba un diseño y genera automáticamente:
    - Plano de instalaciones (enchufes, tomas de agua con coordenadas)
    - Alzado alámbrico SVG con cotas por cada pared
    - Despiece de muebles con valoración por biblioteca (ZC/MV)
    """
    user_id = _get_user_id(user)
    project = _find_project(user_id, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")

    measurements = project.get("measurements", [])
    cabinets = project.get("cabinets", [])

    if not measurements:
        raise HTTPException(status_code=400, detail="Añade medidas de al menos una pared antes de aprobar")

    # 1. Plano de instalaciones
    installation_plan = _generate_installation_plan(measurements, cabinets)

    # 2. Alzado alámbrico SVG por pared
    wireframe_svgs = []
    for m in measurements:
        ww = m.get("wall_width", 300) or 300
        wh = m.get("wall_height", 260) or 260
        wall_label = m.get("wall_label", "Pared")
        svg = _generate_wireframe_svg(wall_label, ww, wh, cabinets, m)
        wireframe_svgs.append(svg)

    # 3. Despiece con valoración
    breakdown = _generate_cabinet_breakdown(
        cabinets, data.library, project.get("cabinet_material", "")
    )

    # Guardar documentos técnicos
    technical_docs = [
        {
            "id": f"td_plan_{int(time.time())}",
            "doc_type": "installation_plan",
            "content": installation_plan,
            "library": data.library,
            "created_at": time.time(),
        },
        {
            "id": f"td_wireframe_{int(time.time())}",
            "doc_type": "wireframe_elevation",
            "content": {"walls": wireframe_svgs},
            "library": data.library,
            "created_at": time.time(),
        },
        {
            "id": f"td_breakdown_{int(time.time())}",
            "doc_type": "cabinet_breakdown",
            "content": breakdown,
            "library": data.library,
            "total_value": breakdown["totalPrice"],
            "created_at": time.time(),
        },
    ]

    project["technical_docs"] = technical_docs
    project["status"] = "approved"
    project["updated_at"] = time.time()

    return {
        "success": True,
        "technical_docs": technical_docs,
        "total_value": breakdown["totalPrice"],
    }


@kitchen_projects_router.get("/{project_id}/technical-docs")
async def get_technical_docs(project_id: str, user=Depends(require_auth)):
    """Obtiene la documentación técnica generada tras la aprobación."""
    user_id = _get_user_id(user)
    project = _find_project(user_id, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return {"technical_docs": project.get("technical_docs", [])}
