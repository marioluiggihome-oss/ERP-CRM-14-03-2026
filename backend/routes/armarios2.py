# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
Armarios 2 — Diseñador de armarios con IA (Gemini). Endpoints:
- /armarios2/plan : analiza un plano/foto y devuelve medidas (ancho/alto/fondo).
- /armarios2/render : genera (o edita) un render realista del armario.
Reutiliza la IA del servidor (services.llm_vision) con GEMINI_API_KEY.
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from typing import Optional
import os
import uuid
import json
import re
import logging
from services.db_client import get_db as _get_db

logger = logging.getLogger(__name__)

try:
    from services.jwt_service import require_auth, get_current_user, ADMIN_ROLE_FLAGS
    _DEPS = [Depends(require_auth)]
except Exception:
    async def get_current_user():
        return None
    ADMIN_ROLE_FLAGS = ["isAdmin", "isGerente", "isDirectorComercial"]
    _DEPS = []

router = APIRouter(tags=["armarios2"], dependencies=_DEPS)


@router.post("/armarios2/designs")
async def save_design(payload: dict, current_user: Optional[dict] = Depends(get_current_user)):
    """Guarda (o actualiza) un diseño de armario del usuario."""
    p = payload or {}
    oid = p.get("id") or f"arm-{uuid.uuid4().hex[:10]}"
    now = datetime.now(timezone.utc).isoformat()
    existing = await _get_db().armarios2_designs.find_one({"id": oid}, {"_id": 0, "createdAt": 1, "userId": 1})
    if existing and existing.get("userId") and current_user and current_user.get("id") \
       and existing["userId"] != current_user["id"] and not any(current_user.get(f) for f in ADMIN_ROLE_FLAGS):
        raise HTTPException(status_code=403, detail="Sin acceso a este diseño")
    doc = {
        "id": oid,
        "userId": (existing or {}).get("userId") or (current_user or {}).get("id") or "anonymous",
        "cliente": str(p.get("cliente") or ""),
        "ref": str(p.get("ref") or ""),
        "cfg": p.get("cfg") or {},
        "comps": p.get("comps") or [],
        "pvp": float(p.get("pvp") or 0),
        "createdByName": (current_user or {}).get("clientName") or (current_user or {}).get("username") or "",
        "createdAt": (existing or {}).get("createdAt") or now,
        "updatedAt": now,
    }
    await _get_db().armarios2_designs.update_one({"id": oid}, {"$set": doc}, upsert=True)
    doc.pop("_id", None)
    return {"success": True, "design": doc}


@router.get("/armarios2/designs")
async def list_designs(current_user: Optional[dict] = Depends(get_current_user)):
    query = {}
    if current_user and current_user.get("id") and not any(current_user.get(f) for f in ADMIN_ROLE_FLAGS):
        query["userId"] = current_user["id"]
    items = await _get_db().armarios2_designs.find(query, {"_id": 0, "cfg": 0, "comps": 0}).sort("updatedAt", -1).to_list(300)
    return {"success": True, "designs": items}


def _owns(doc, current_user) -> bool:
    if not doc:
        return False
    if any((current_user or {}).get(f) for f in ADMIN_ROLE_FLAGS):
        return True
    owner = doc.get("userId")
    return (not owner) or owner == (current_user or {}).get("id")


@router.get("/armarios2/designs/{design_id}")
async def get_design(design_id: str, current_user: Optional[dict] = Depends(get_current_user)):
    d = await _get_db().armarios2_designs.find_one({"id": design_id}, {"_id": 0})
    if not d:
        raise HTTPException(status_code=404, detail="Diseño no encontrado")
    if not _owns(d, current_user):
        raise HTTPException(status_code=403, detail="Sin acceso a este diseño")
    return d


@router.delete("/armarios2/designs/{design_id}")
async def delete_design(design_id: str, current_user: Optional[dict] = Depends(get_current_user)):
    d = await _get_db().armarios2_designs.find_one({"id": design_id}, {"_id": 0, "userId": 1})
    if not d:
        raise HTTPException(status_code=404, detail="Diseño no encontrado")
    if not _owns(d, current_user):
        raise HTTPException(status_code=403, detail="Sin acceso a este diseño")
    await _get_db().armarios2_designs.delete_one({"id": design_id})
    return {"success": True}


def _num(v):
    try:
        return int(round(float(v)))
    except (TypeError, ValueError):
        return None


@router.post("/armarios2/plan")
async def armarios2_plan(payload: dict):
    """Analiza un plano/foto de hueco y devuelve medidas en mm + descripción."""
    img = (payload or {}).get("imageBase64") or ""
    if not img:
        raise HTTPException(status_code=400, detail="Falta la imagen del plano.")
    try:
        from services.llm_vision import analyze_image_with_gemini, is_vision_available
        if not is_vision_available():
            raise HTTPException(status_code=503, detail="IA no configurada. Falta la clave del motor de IA (contacta con el administrador).")
        prompt = (
            "Eres un técnico de medición de armarios. Analiza este plano o foto del hueco donde irá el armario. "
            "Deduce las medidas en MILÍMETROS (ancho, alto y fondo del hueco). Si el fondo no se aprecia, usa 600. "
            "Describe brevemente la distribución sugerida (secciones, baldas, barras). "
            "Devuelve SOLO un bloque JSON con: {\"width\":mm, \"height\":mm, \"depth\":mm, \"layout\":\"texto\"}."
        )
        text = await analyze_image_with_gemini(image_base64=img, prompt=prompt, model="gemini-2.5-pro")
        m = re.search(r"\{[\s\S]*\}", text or "")
        data = {}
        if m:
            try:
                data = json.loads(m.group())
            except Exception:
                data = {}
        return {
            "width": _num(data.get("width")) or 2000,
            "height": _num(data.get("height")) or 2400,
            "depth": _num(data.get("depth")) or 600,
            "layout": str(data.get("layout") or ""),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"armarios2_plan error: {e}")
        raise HTTPException(status_code=500, detail=f"No se pudo analizar el plano: {e}")


@router.post("/armarios2/render")
async def armarios2_render(payload: dict):
    """Genera o edita un render realista del armario a partir de la configuración
    y, opcionalmente, una imagen previa (para edición en lenguaje natural)."""
    p = payload or {}
    try:
        from services.llm_vision import generate_image_with_gemini, get_gemini_key, GOOGLE_GENAI_AVAILABLE
        if not (get_gemini_key() and GOOGLE_GENAI_AVAILABLE):
            raise HTTPException(status_code=503, detail="Generación de imágenes no disponible: falta la clave del motor de IA.")
        w = _num(p.get("width")) or 2000
        h = _num(p.get("height")) or 2400
        d = _num(p.get("depth")) or 600
        material = str(p.get("material") or "melamina blanco mate")
        tipo = "vestidor abierto" if p.get("projectType") == "vestidor" else "armario"
        door = str(p.get("doorType") or "open")
        door_es = {"sliding": "puertas correderas", "hinged": "puertas batientes", "folding": "puertas plegables", "coplanar": "puertas coplanares", "open": "sin puertas (interior visible)"}.get(door, "sin puertas")
        interior = str(p.get("interior") or "")
        edit = str(p.get("editInstruction") or "").strip()
        prev = p.get("previousImageBase64")
        reference_is_sketch = bool(p.get("referenceIsSketch"))

        if edit and prev:
            prompt = (
                f"Edita este render de {tipo} manteniendo el estilo y encuadre. Cambio pedido: {edit}. "
                "Fotorrealista, iluminación de catálogo, fondo neutro."
            )
        elif reference_is_sketch and prev:
            prompt = (
                f"La imagen de referencia es un CROQUIS a escala de un {tipo} de {w}x{h}x{d} mm. "
                "Genera un render fotorrealista RESPETANDO FIELMENTE esa distribución: mismas secciones, "
                "mismas baldas, cajones, barras y proporciones y en las mismas posiciones. No añadas ni "
                "quites elementos. "
                f"Material de los frentes/cuerpo: '{material}', {door_es}. "
                f"{('Detalle del interior: ' + interior + '. ') if interior else ''}"
                "Vista frontal ligeramente en perspectiva, iluminación de catálogo, fondo neutro, alta calidad, "
                "estilo mueble a medida español."
            )
        else:
            prompt = (
                f"Render fotorrealista de un {tipo} de {w}x{h}x{d} mm en material '{material}', {door_es}. "
                f"{('Interior: ' + interior + '. ') if interior else ''}"
                "Vista frontal ligeramente en perspectiva, iluminación de catálogo, fondo neutro, alta calidad, estilo mueble a medida español."
            )
        data_url = await generate_image_with_gemini(
            prompt=prompt,
            reference_image_base64=(prev.split(',', 1)[1] if isinstance(prev, str) and prev.startswith('data:') else prev) if prev else None,
        )
        return {"imageUrl": data_url}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"armarios2_render error: {e}")
        raise HTTPException(status_code=500, detail=f"No se pudo generar el render: {e}")
