"""
Armarios Router - Proyectos de Armarios con IA
Endpoints para gestionar proyectos de armarios empotrados con configuración e IA
"""
from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
from typing import Optional
import uuid
import logging
import os
import json
import re

from models.schemas import (
    ArmarioModuleConfig, ArmarioProject, ArmarioProjectCreate, ArmarioProjectUpdate,
    IAConfigRequest, IARenderRequest, IALayoutRequest,
    ContactModel, OpportunityModel
)

logger = logging.getLogger(__name__)

# Autenticación: todos los endpoints exigen token. Los proyectos se filtran por
# el usuario autenticado (no por un userId de query manipulable). Admin ve todo.
try:
    from services.jwt_service import require_auth, get_current_user, ADMIN_ROLE_FLAGS
    _DEPS = [Depends(require_auth)]
except Exception:  # pragma: no cover - fallback si el servicio no está disponible
    async def get_current_user():
        return None
    ADMIN_ROLE_FLAGS = ["isAdmin", "isGerente", "isDirectorComercial"]
    _DEPS = []

def _is_admin(user) -> bool:
    return bool(user) and any(user.get(f) for f in ADMIN_ROLE_FLAGS)

router = APIRouter(tags=["armarios"], dependencies=_DEPS)

# Database connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'luiggi_home')
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]


# ============================================
# ARMARIOS - PROYECTOS CRUD
# ============================================

@router.post("/armarios/projects")
async def create_armario_project(project: ArmarioProjectCreate, current_user: Optional[dict] = Depends(get_current_user)):
    """Crear nuevo proyecto de armario (propiedad = usuario autenticado)."""
    try:
        project_dict = project.model_dump()
        project_dict["id"] = str(uuid.uuid4())
        project_dict["userId"] = (current_user or {}).get("id") or "anonymous"
        project_dict["createdAt"] = datetime.now(timezone.utc).isoformat()
        project_dict["updatedAt"] = datetime.now(timezone.utc).isoformat()

        await db.armario_projects.insert_one(project_dict)
        project_dict.pop("_id", None)
        return {"success": True, "project": project_dict}
    except Exception as e:
        logger.error(f"Error creating armario project: {e}")
        raise HTTPException(status_code=500, detail="No se pudo crear el proyecto")


@router.get("/armarios/projects")
async def get_armario_projects(current_user: Optional[dict] = Depends(get_current_user)):
    """Lista de proyectos del usuario autenticado (admin ve todos)."""
    try:
        query = {} if _is_admin(current_user) else {"userId": (current_user or {}).get("id") or "anonymous"}
        projects = await db.armario_projects.find(
            query,
            {"_id": 0}
        ).sort("updatedAt", -1).to_list(100)
        return {"success": True, "projects": projects}
    except Exception as e:
        logger.error(f"Error getting armario projects: {e}")
        raise HTTPException(status_code=500, detail="No se pudieron cargar los proyectos")


async def _load_owned_project(project_id: str, current_user: Optional[dict], fields=None):
    """Carga un proyecto y verifica que el usuario es propietario o admin."""
    project = await db.armario_projects.find_one({"id": project_id}, fields if fields is not None else {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    owner = project.get("userId")
    if not _is_admin(current_user) and owner and owner != ((current_user or {}).get("id")):
        raise HTTPException(status_code=403, detail="Sin acceso a este proyecto")
    return project


@router.get("/armarios/projects/{project_id}")
async def get_armario_project(project_id: str, current_user: Optional[dict] = Depends(get_current_user)):
    """Obtener un proyecto de armario específico (solo propietario o admin)."""
    try:
        project = await _load_owned_project(project_id, current_user)
        return {"success": True, "project": project}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting armario project: {e}")
        raise HTTPException(status_code=500, detail="No se pudo cargar el proyecto")


@router.put("/armarios/projects/{project_id}")
async def update_armario_project(project_id: str, update: ArmarioProjectUpdate, current_user: Optional[dict] = Depends(get_current_user)):
    """Actualizar un proyecto de armario (solo propietario o admin)."""
    try:
        await _load_owned_project(project_id, current_user, {"_id": 0, "userId": 1})
        update_data = {k: v for k, v in update.model_dump().items() if v is not None}
        update_data.pop("userId", None)  # la propiedad no se cambia desde el cliente
        update_data["updatedAt"] = datetime.now(timezone.utc).isoformat()

        await db.armario_projects.update_one({"id": project_id}, {"$set": update_data})
        updated_project = await db.armario_projects.find_one({"id": project_id}, {"_id": 0})
        return {"success": True, "project": updated_project}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating armario project: {e}")
        raise HTTPException(status_code=500, detail="No se pudo actualizar el proyecto")


@router.delete("/armarios/projects/{project_id}")
async def delete_armario_project(project_id: str, current_user: Optional[dict] = Depends(get_current_user)):
    """Eliminar un proyecto de armario (solo propietario o admin)."""
    try:
        await _load_owned_project(project_id, current_user, {"_id": 0, "userId": 1})
        await db.armario_projects.delete_one({"id": project_id})
        return {"success": True, "message": "Proyecto eliminado"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting armario project: {e}")
        raise HTTPException(status_code=500, detail="No se pudo eliminar el proyecto")


@router.post("/crm/opportunities/from-armario/{project_id}")
async def create_opportunity_from_armario(project_id: str):
    """Create a CRM opportunity from an armario project"""
    try:
        # Get the armario project
        project = await db.armario_projects.find_one({"id": project_id}, {"_id": 0})
        if not project:
            raise HTTPException(status_code=404, detail="Proyecto de armario no encontrado")
        
        # Calculate project total value from despiece if available
        total_value = project.get("totalPrice", 0)
        
        # Use customer name or project name
        customer_name = project.get("customerName", project.get("name", "Cliente sin nombre"))
        
        # Check if contact exists or create one
        contact = await db.contacts.find_one({"name": customer_name}, {"_id": 0})
        
        if not contact:
            # Create new contact
            contact = ContactModel(
                name=customer_name,
                status="customer"
            ).model_dump()
            contact['createdAt'] = contact['createdAt'].isoformat()
            contact['updatedAt'] = contact['updatedAt'].isoformat()
            await db.contacts.insert_one(contact)
        
        contact_id = contact.get("id")
        
        # Create opportunity
        opp = OpportunityModel(
            title=f"Presupuesto Armarios - {customer_name}",
            description=f"Proyecto: {project.get('name', '')} - {project.get('width', 0)}x{project.get('height', 0)}cm",
            contactId=contact_id,
            contactName=customer_name,
            value=total_value,
            probability=50,
            stage="proposal",
            linkedProjectId=project_id,
            linkedProjectNumber=project.get("name", ""),
            businessType="armarios"
        ).model_dump()
        opp['createdAt'] = opp['createdAt'].isoformat()
        opp['updatedAt'] = opp['updatedAt'].isoformat()
        
        await db.opportunities.insert_one(opp)
        
        # Update contact with businessTypes
        await db.contacts.update_one(
            {"id": contact_id},
            {"$addToSet": {"businessTypes": "armarios"}}
        )
        
        opp.pop('_id', None)
        return {
            "opportunity": opp,
            "contact": contact,
            "message": "Oportunidad de armarios creada"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create opportunity from armario error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# ARMARIOS - IA CONFIGURACION Y RENDER
# ============================================

@router.post("/armarios/ia/configure")
async def ia_configure_armario(request: IAConfigRequest):
    """Usar IA para configurar la distribucion de modulos del armario"""
    try:
        try:
            from emergentintegrations.llm.chat import LlmChat, UserMessage
        except ImportError:
            raise HTTPException(status_code=503, detail="AI service not available in this environment")
        
        api_key = os.environ.get("EMERGENT_LLM_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="Clave de IA no configurada")
        
        chat = LlmChat(
            api_key=api_key,
            session_id=f"armario-config-{uuid.uuid4()}",
            system_message="""Eres un disenador experto en armarios empotrados. Tu trabajo es configurar la distribucion optima de modulos de un armario basandote en las necesidades del usuario.

DEBES responder SIEMPRE en formato JSON con esta estructura exacta:
{
  "modules": 3,
  "doorType": "sliding",
  "moduleConfigs": [
    {"id": 1, "shelves": 4, "drawers": 0, "hangingRods": 1, "hangingHeight": 1200, "extras": {}},
    {"id": 2, "shelves": 6, "drawers": 3, "hangingRods": 0, "hangingHeight": 0, "extras": {"jewelryTray": true}},
    {"id": 3, "shelves": 2, "drawers": 0, "hangingRods": 2, "hangingHeight": 1000, "extras": {"shoesRack": true}}
  ],
  "extras": {"softClose": true, "led": true, "mirror": false},
  "explanation": "Descripcion breve de la configuracion"
}

Tipos de puerta: "sliding" (corredera), "hinged" (abatible), "folding" (plegable)
Extras por modulo: shoesRack, trousersRack, jewelryTray, tieRack, pulloutBasket
Extras generales: softClose, led, mirror, antiFingerprint

Considera:
- Ropa de colgar larga (vestidos, abrigos): barras a 1600mm
- Ropa de colgar corta (camisas): barras a 1000-1200mm
- Barras dobles para maximizar espacio: hangingRods: 2, hangingHeight: 1000
- Cajones para ropa interior, calcetines, etc.
- Baldas para ropa doblada, bolsos
- Zapatero para zapatos
- Pantalonero para pantalones"""
        )
        
        chat.with_model("gemini", "gemini-3-flash-preview")
        
        # Construir prompt
        prompt = f"""El usuario quiere configurar un armario con estas instrucciones:

"{request.instruction}"

Configuracion actual del armario:
- Ancho: {request.current_config.get('width', 2400)}mm
- Alto: {request.current_config.get('height', 2400)}mm
- Fondo: {request.current_config.get('depth', 600)}mm
- Modulos actuales: {request.current_config.get('modules', 3)}

Genera la configuracion optima en formato JSON."""

        msg = UserMessage(text=prompt)
        response = await chat.send_message(msg)
        
        # Parsear respuesta JSON
        # Get text content from response - handle different response types
        logger.info(f"IA raw response: {response}, type: {type(response)}")
        
        if response is None:
            return {"success": False, "error": "La IA no genero respuesta"}
        
        if isinstance(response, str):
            response_text = response
        elif hasattr(response, 'content'):
            response_text = response.content
        else:
            response_text = str(response)
        
        if not response_text or response_text == "None":
            return {"success": False, "error": "La IA no genero respuesta valida"}
        
        logger.info(f"IA response text: {response_text[:200] if response_text else 'None'}")
        
        # Extraer JSON de la respuesta
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            config = json.loads(json_match.group())
            return {"success": True, "config": config}
        else:
            return {"success": False, "error": "No se pudo generar configuracion", "raw_response": response_text}
            
    except Exception as e:
        logger.error(f"Error en IA configuracion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/armarios/ia/generate-layout")
async def ia_generate_layout(request: IALayoutRequest):
    """
    Generate wardrobe interior layout from natural language instructions.
    Uses AI to interpret the user's description and create module configurations.
    """
    try:
        try:
            from emergentintegrations.llm.chat import LlmChat, UserMessage
        except ImportError:
            raise HTTPException(status_code=503, detail="AI service not available in this environment")
        
        api_key = os.environ.get("EMERGENT_LLM_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="Clave de IA no configurada")
        
        chat = LlmChat(
            api_key=api_key,
            session_id=f"armario-layout-{uuid.uuid4()}",
            system_message="""Eres un disenador de interiores de armarios experto.
Tu trabajo es interpretar las instrucciones del usuario y convertirlas en una configuracion JSON para el armario.

Reglas de diseno:
- "maletero" o "trunk" va siempre arriba (primeros 30cm)
- "perchero" o "barra" o "hanging" va en la parte central-alta
- "cajones" o "drawers" van en la parte baja (ultimos 50-80cm)
- "baldas" o "shelves" pueden ir en cualquier posicion
- "zapatero" o "shoe rack" va en la parte baja
- "pantalonero" va en zona media-baja
- "joyero" va en zona media

Debes responder UNICAMENTE con un JSON valido sin explicaciones."""
        ).with_model("gemini", "gemini-2.5-flash")
        
        prompt = f"""El usuario quiere configurar un armario con {request.modules} modulos.
Dimensiones: {request.width}mm ancho x {request.height}mm alto x {request.depth}mm fondo.

INSTRUCCIONES DEL USUARIO:
"{request.instruction}"

Genera una configuracion JSON con este formato exacto:
{{
  "moduleConfigs": [
    {{
      "shelves": numero_de_baldas,
      "drawers": numero_de_cajones,
      "hangingRods": numero_de_barras_perchero (0, 1 o 2 para doble altura),
      "hangingHeight": altura_perchero_mm (1200 normal, 1000 para doble altura),
      "shoesRack": true/false,
      "trousersRack": true/false,
      "tieRack": true/false,
      "jewelryTray": true/false,
      "trunk": true/false (maletero arriba),
      "mirrorDoor": true/false
    }}
    // ... un objeto por cada modulo (total: {request.modules})
  ],
  "extras": {{
    "led": true/false (si menciona iluminacion),
    "mirror": true/false (si menciona espejo)
  }}
}}

Interpreta las instrucciones del usuario y genera la configuracion. Si no especifica algo para un modulo, usa valores por defecto sensatos (2 baldas, 1 barra).
Responde SOLO con el JSON, sin texto adicional."""

        msg = UserMessage(text=prompt)
        response = await chat.send_message(msg)
        
        # Limpiar la respuesta de posibles markdown
        json_text = response.strip()
        if json_text.startswith('```json'):
            json_text = json_text[7:]
        if json_text.startswith('```'):
            json_text = json_text[3:]
        if json_text.endswith('```'):
            json_text = json_text[:-3]
        json_text = json_text.strip()
        
        try:
            result = json.loads(json_text)
            
            # Validar que tiene la estructura correcta
            if 'moduleConfigs' not in result:
                return {"success": False, "error": "Respuesta IA no contiene moduleConfigs"}
            
            # Asegurar que hay la cantidad correcta de modulos
            while len(result['moduleConfigs']) < request.modules:
                result['moduleConfigs'].append({
                    "shelves": 2,
                    "drawers": 0,
                    "hangingRods": 1,
                    "hangingHeight": 1200
                })
            
            # Limitar al numero de modulos solicitado
            result['moduleConfigs'] = result['moduleConfigs'][:request.modules]
            
            logger.info(f"IA layout generated for {request.modules} modules")
            
            return {
                "success": True,
                "moduleConfigs": result['moduleConfigs'],
                "extras": result.get('extras', {})
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing IA response: {e}")
            return {"success": False, "error": f"Error interpretando respuesta IA: {str(e)}"}
            
    except Exception as e:
        logger.error(f"Error en IA generate layout: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/armarios/ia/render")
async def ia_render_armario(request: IARenderRequest):
    """Generar render realista del armario usando IA"""
    try:
        from services.llm_vision import generate_image_with_gemini

        # Construir descripcion del tipo de puerta
        door_type_desc = {
            "sliding": "PUERTAS CORREDERAS (sliding doors on rails, overlap when open)",
            "hinged": "PUERTAS ABATIBLES CON BISAGRAS (traditional hinged doors with handles)",
            "folding": "PUERTAS PLEGABLES (bi-fold doors)"
        }.get(request.doorType, "PUERTAS CORREDERAS")
        
        # Etiqueta legible para cada token del orden de piezas (de arriba a abajo).
        _tok_label = {
            'maletero': "top 'maletero' storage box (full-width compartment at the very top)",
            'rod': "horizontal chrome hanging rod",
            'shelf': "horizontal shelf",
            'drawer': "soft-close drawer",
        }

        # Describir interior DETALLADAMENTE por modulo
        interior_desc = []
        for i, mod in enumerate(request.moduleConfigs):
            # Si llega el orden explicito (layout), describir de ARRIBA a ABAJO.
            layout = mod.get('layout') or []
            if layout:
                seq = [_tok_label.get(t, t) for t in layout]
                order_txt = "; ".join(f"{n+1}) {d}" for n, d in enumerate(seq))
                interior_desc.append(
                    f"Module {i+1} (from left), TOP to BOTTOM in this EXACT order: {order_txt}."
                )
                continue
            items = []
            if mod.get('maletero'):
                items.append("a top 'maletero' storage box")
            if mod.get('hangingRods', 0) > 0:
                rod_count = mod['hangingRods']
                items.append(f"{rod_count} chrome hanging rod{'s' if rod_count > 1 else ''}")
            if mod.get('shelves', 0) > 0:
                shelf_count = mod['shelves']
                items.append(f"{shelf_count} horizontal shelf{'ves' if shelf_count > 1 else ''}")
            if mod.get('drawers', 0) > 0:
                drawer_count = mod['drawers']
                items.append(f"{drawer_count} soft-close drawer{'s' if drawer_count > 1 else ''}")
            if mod.get('shoesRack'):
                items.append("angled shoe rack")
            if mod.get('trousersRack'):
                items.append("pull-out trouser rack")
            if mod.get('mirrorDoor'):
                items.append("full-length mirror on door interior")
            
            module_desc = f"Module {i+1} (from left): {', '.join(items) if items else 'empty space'}"
            interior_desc.append(module_desc)
        
        # Usar el numero de puertas de la configuracion del usuario
        doors_count = request.numDoors
        door_width = request.width / doors_count
        doors_open = getattr(request, "doorsOpen", True)
        open_door_index = getattr(request, "openDoorIndex", None)

        def _ordinal(n):
            return {1: "1st", 2: "2nd", 3: "3rd"}.get(n, f"{n}th")

        if doors_open:
            if open_door_index is not None and 0 <= open_door_index < doors_count:
                door_num = open_door_index + 1
                if request.doorType == "sliding":
                    doors_state_desc = (
                        f"Door panel #{door_num} (the {_ordinal(door_num)} door counting "
                        f"from the LEFT) is OPEN: slide it all the way out of view, fully "
                        f"behind the nearest end panel or completely off-frame to the side, "
                        f"so it does NOT visibly overlap or stack in front of any other "
                        f"panel. The interior behind door #{door_num} must be completely "
                        f"unobstructed and clearly visible. The other {doors_count - 1} "
                        f"door panels stay normally CLOSED in their own positions. The "
                        f"wardrobe still has EXACTLY {doors_count} door panels in total — "
                        f"never duplicate, remove or add panels."
                    )
                else:
                    doors_state_desc = (
                        f"Door #{door_num} (the {_ordinal(door_num)} door counting from "
                        f"the LEFT) is swung fully open on its hinges to reveal the "
                        f"interior behind it; the other {doors_count - 1} doors stay "
                        f"closed. Do NOT add, duplicate or remove any door panel — exactly "
                        f"{doors_count} doors total."
                    )
            elif request.doorType == "sliding":
                doors_state_desc = (
                    f"Show the doors PARTIALLY OPEN by sliding ONE single door panel "
                    f"sideways so it overlaps and hides behind an adjacent panel, revealing "
                    f"the interior behind the gap. The wardrobe still has EXACTLY "
                    f"{doors_count} door panels in total (overlapping counts as the same "
                    f"panel, never duplicate or add extra panels to fake an open look)."
                )
            else:
                doors_state_desc = (
                    f"Show ONE of the {doors_count} doors swung open on its hinges to "
                    f"reveal the interior; the remaining doors stay closed. Do NOT add, "
                    f"duplicate or remove any door panel — exactly {doors_count} doors total."
                )
        else:
            doors_state_desc = (
                f"Show ALL {doors_count} doors fully CLOSED. NONE of the interior (shelves, "
                f"drawers, hanging rods, clothes, maletero) must be visible — it is completely "
                f"hidden behind the closed door panels. The photo shows ONLY the clean, flat "
                f"closed exterior front of the wardrobe (door panels, handles, frame), with "
                f"zero gaps revealing the inside."
            )


        # Si el frontend manda el esquema/plano AUTOGENERADO del configurador
        # (blueprintImage), es el plano AUTORITATIVO: el modelo debe
        # reproducirlo tal cual (puertas, divisiones, baldas, cajones, barras,
        # maletero y proporciones). La referenceImage (si la hay) es solo una
        # foto de inspiración de estilo, no estructural.
        has_blueprint = bool(getattr(request, "blueprintImage", None))
        blueprint_block = ""
        if has_blueprint:
            blueprint_block = """
BLUEPRINT (FIRST IMAGE) - THIS IS MANDATORY:
- The FIRST image provided is a SCHEMATIC ELEVATION of THIS EXACT wardrobe,
  drawn with the doors "transparent" (dashed red lines) purely so the
  INTERNAL layout is visible for reference. It is NOT a depiction of the
  final photo's door state — it does NOT mean the doors are open in the
  photo. Whether each door is OPEN or CLOSED in the final image is defined
  ONLY by the "DOORS - CRITICAL" section below; follow that section, not the
  blueprint, for the door state.
- It is the AUTHORITATIVE BLUEPRINT for everything else. Reproduce it EXACTLY
  in photorealistic form.
- Same number of doors and same door widths.
- Same vertical module divisions (in the same positions).
- Same count, order and vertical position of every shelf, drawer, hanging rod,
  top "maletero" storage box and accessory, module by module — this interior
  must be reproduced even behind a CLOSED door (it defines what is hidden).
- Same width:height proportions. DO NOT add, remove, move or resize anything.
- Only add realistic materials, light and textures. NEVER invent a different
  interior.
"""

        has_consistency = bool(getattr(request, "consistencyImage", None))
        consistency_block = ""
        if has_consistency:
            consistency_block = """
CONSISTENCY REFERENCE (LAST IMAGE) - THIS IS MANDATORY:
- The LAST image provided is a previously generated PHOTO of THIS SAME EXACT
  wardrobe, from another view / with a different door open.
- Treat it as THE SAME physical wardrobe in THE SAME room. The interior MUST be
  IDENTICAL to it: same exact shelves, drawers, hanging rods, maletero, the same
  colors and materials, the same wood/melamine finish and grain, the same wall
  color, the same floor, the same lighting and the same folded clothes in the
  same places.
- The ONLY thing that may differ from that reference is WHICH door is open or
  closed (per the DOORS section). Everything else must look like the very same
  wardrobe photographed again, not a different design.
"""

        prompt = f"""Create a PHOTOREALISTIC interior design photograph of a BUILT-IN WARDROBE/CLOSET.

CRITICAL - FOLLOW THESE SPECIFICATIONS EXACTLY. This is a technical product
render: accuracy to the specification matters more than artistic freedom.
{blueprint_block}{consistency_block}
DIMENSIONS:
- Total width: {request.width}mm ({request.width/10}cm / {round(request.width/25.4, 1)} inches)
- Total height: {request.height}mm ({request.height/10}cm)
- Depth: {request.depth}mm ({request.depth/10}cm)
- Number of interior modules/sections: {request.modules} modules

DOORS - CRITICAL - PAY ATTENTION:
- EXACT NUMBER OF DOORS: {doors_count} doors (this is mandatory!)
- Door type: {door_type_desc}
- Each door width: approximately {round(door_width)}mm
- Door color/finish: {request.exteriorColorName} (hex: {request.exteriorColorHex})
- Handle/knob style: {request.handleColorName} color handles
- {doors_state_desc}

COLORS - MATCH EXACTLY:
- EXTERIOR FINISH (doors): {request.exteriorColorName} (hex color: {request.exteriorColorHex})
- INTERIOR COLOR (shelves, back panel): {request.interiorColorName}
- All visible melamine surfaces should match these colors

INTERIOR ORGANIZATION - FOLLOW EXACTLY:
{chr(10).join(interior_desc)}

ROOM SETTING:
- Room style: {request.roomStyle}
- Soft natural daylight from left side
- Wardrobe built into wall alcove
- Hardwood or laminate flooring visible
- Neutral wall color that complements the wardrobe

IMAGE REQUIREMENTS:
- Professional interior photography style, NOT a 3D render or sketch
- Camera angle: 3/4 view from front-left{' to show interior through the open door' if doors_open else ', showing the closed front'}
- High-end quality materials: melamine, chrome hardware, soft-close systems
- Realistic shadows and reflections
- A few neatly folded clothing items are allowed but MUST NOT hide or change the
  interior structure (shelves, drawers, rods, maletero) defined above
- 4K quality, clean professional composition

IMPORTANT: The wardrobe MUST have EXACTLY {doors_count} {request.doorType} doors and the
EXACT interior layout described{' and shown in the blueprint' if has_blueprint else ''}. DO NOT add, remove or rearrange anything.
Generate ONE high-quality photorealistic image."""

        reference_images = []
        if has_blueprint:
            reference_images.append({
                "data": request.blueprintImage,
                "mime": getattr(request, "blueprintMime", None) or "image/png",
            })
        if getattr(request, "referenceImage", None):
            reference_images.append({
                "data": request.referenceImage,
                "mime": getattr(request, "referenceMime", None) or "image/png",
            })
        # La imagen de consistencia va LA ÚLTIMA (coincide con "LAST IMAGE" del prompt).
        if has_consistency:
            reference_images.append({
                "data": request.consistencyImage,
                "mime": getattr(request, "consistencyMime", None) or "image/png",
            })

        try:
            data_url = await generate_image_with_gemini(
                prompt,
                reference_images=reference_images,
            )
        except Exception as e:
            logger.error(f"Error generando render de armario: {e}")
            return {"success": False, "error": "No se pudo generar la imagen. Inténtalo de nuevo."}

        # data_url = 'data:image/png;base64,XXXX' → separar mime y base64 para el frontend
        mime = "image/png"
        b64 = data_url
        if isinstance(data_url, str) and data_url.startswith("data:"):
            head, b64 = data_url.split(",", 1)
            mime = head[5:].split(";", 1)[0] or mime
        return {
            "success": True,
            "image": {"data": b64, "mime_type": mime},
        }

    except Exception as e:
        logger.error(f"Error en IA render: {e}")
        raise HTTPException(status_code=500, detail=str(e))
