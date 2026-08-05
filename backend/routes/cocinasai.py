"""
Cocinas IA 2 — Render fotorrealista de cocina a partir de planos/alzados (Gemini
image). Portado de "KitchAI Design Studio". Reutiliza services.llm_vision.
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from typing import Optional
import os
import uuid
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

router = APIRouter(tags=["cocinasai"], dependencies=_DEPS)



@router.post("/cocinasai/designs")
async def save_kdesign(payload: dict, current_user: Optional[dict] = Depends(get_current_user)):
    p = payload or {}
    oid = p.get("id") or f"kai-{uuid.uuid4().hex[:10]}"
    now = datetime.now(timezone.utc).isoformat()
    existing = await _get_db().cocinasai_designs.find_one({"id": oid}, {"_id": 0, "createdAt": 1, "userId": 1})
    if existing and existing.get("userId") and current_user and current_user.get("id") \
       and existing["userId"] != current_user["id"] and not any(current_user.get(f) for f in ADMIN_ROLE_FLAGS):
        raise HTTPException(status_code=403, detail="Sin acceso a este diseño")
    doc = {
        "id": oid,
        "userId": (existing or {}).get("userId") or (current_user or {}).get("id") or "anonymous",
        "cliente": str(p.get("cliente") or ""),
        "ref": str(p.get("ref") or ""),
        "kitchenType": str(p.get("kitchenType") or ""),
        "style": str(p.get("style") or ""),
        "notes": str(p.get("notes") or ""),
        "renders": (p.get("renders") or [])[:12],
        # Planos/alzados originales: se guardan para poder COMPARAR plano vs
        # render al reabrir el diseño.
        "plans": (p.get("plans") or [])[:6],
        "createdByName": (current_user or {}).get("clientName") or (current_user or {}).get("username") or "",
        "createdAt": (existing or {}).get("createdAt") or now,
        "updatedAt": now,
    }
    await _get_db().cocinasai_designs.update_one({"id": oid}, {"$set": doc}, upsert=True)
    doc.pop("_id", None)
    return {"success": True, "design": doc}


@router.get("/cocinasai/designs")
async def list_kdesigns(current_user: Optional[dict] = Depends(get_current_user)):
    query = {}
    if current_user and current_user.get("id") and not any(current_user.get(f) for f in ADMIN_ROLE_FLAGS):
        query["userId"] = current_user["id"]
    items = await _get_db().cocinasai_designs.find(query, {"_id": 0, "renders": 0, "plans": 0}).sort("updatedAt", -1).to_list(300)
    return {"success": True, "designs": items}


@router.get("/cocinasai/designs/{design_id}")
async def get_kdesign(design_id: str):
    d = await _get_db().cocinasai_designs.find_one({"id": design_id}, {"_id": 0})
    if not d:
        raise HTTPException(status_code=404, detail="Diseño no encontrado")
    return d


@router.delete("/cocinasai/designs/{design_id}")
async def delete_kdesign(design_id: str):
    await _get_db().cocinasai_designs.delete_one({"id": design_id})
    return {"success": True}


def _strip(b64):
    if isinstance(b64, str) and b64.startswith("data:"):
        return b64.split(",", 1)[1]
    return b64


@router.post("/cocinasai/design")
async def cocinasai_design(payload: dict, current_user: Optional[dict] = Depends(get_current_user)):
    """Genera un render de cocina a partir de uno o varios planos/alzados."""
    # ENFORCEMENT de créditos de IA por usuario
    try:
        from services.ai_usage import get_user_credits, consume_credits, mensaje_sin_creditos
        if current_user:
            credits = await get_user_credits(current_user)
            if not credits.get("ilimitado") and int(credits.get("restantes", 0) or 0) <= 0:
                raise HTTPException(
                    status_code=402,
                    detail=mensaje_sin_creditos(current_user, credits),
                )
            await consume_credits(current_user, "render")
    except HTTPException:
        raise
    except Exception:
        pass
    p = payload or {}
    plans = p.get("images") or ([p.get("imageBase64")] if p.get("imageBase64") else [])
    plans = [x for x in plans if x]
    kitchen_type = str(p.get("kitchenType") or "Cocina Sola")
    style = str(p.get("style") or "Moderno")
    notes = str(p.get("notes") or "")
    try:
        from services.llm_vision import generate_image_with_gemini, get_gemini_key, GOOGLE_GENAI_AVAILABLE
        if not (get_gemini_key() and GOOGLE_GENAI_AVAILABLE):
            raise HTTPException(status_code=503, detail="Generación de imágenes no disponible: falta la clave del motor de IA.")
        prompt = (
            "Actúa como experto en infoarquitectura y renderizado técnico. Convierte los planos técnicos "
            "(plantas y alzados) adjuntos en un render fotorrealista de alta gama respetando la planimetría: "
            "posición exacta de ventanas/puertas, escala y medidas, y ubicación de fregadero/cocción. "
            f"Tipo de estancia: {kitchen_type}. Estilo: {style}. Especificaciones del cliente: {notes or '—'}. "
            "Render fotorrealista estilo Octane/Corona, iluminación natural coherente con las ventanas, "
            "texturas premium (maderas, piedra técnica, lacados mate), presentación corporativa, formato 16:9."
        )
        refs = [{"data": _strip(x), "mime": "image/png"} for x in plans] if plans else None
        data_url = await generate_image_with_gemini(prompt=prompt, reference_images=refs)
        if not data_url:
            raise HTTPException(status_code=502, detail="La IA no devolvió imagen.")
        return {"imageUrl": data_url}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"cocinasai_design error: {e}")
        raise HTTPException(status_code=500, detail=f"No se pudo generar el render: {e}")


@router.post("/cocinasai/edit")
async def cocinasai_edit(payload: dict, current_user: Optional[dict] = Depends(get_current_user)):
    """Edita un render existente en lenguaje natural."""
    # ENFORCEMENT de créditos de IA por usuario
    try:
        from services.ai_usage import get_user_credits, consume_credits, mensaje_sin_creditos
        if current_user:
            credits = await get_user_credits(current_user)
            if not credits.get("ilimitado") and int(credits.get("restantes", 0) or 0) <= 0:
                raise HTTPException(
                    status_code=402,
                    detail=mensaje_sin_creditos(current_user, credits),
                )
            await consume_credits(current_user, "render")
    except HTTPException:
        raise
    except Exception:
        pass
    p = payload or {}
    prev = p.get("previousImageBase64")
    instruction = str(p.get("instruction") or "").strip()
    if not prev or not instruction:
        raise HTTPException(status_code=400, detail="Faltan la imagen o la instrucción.")
    try:
        from services.llm_vision import generate_image_with_gemini, get_gemini_key, GOOGLE_GENAI_AVAILABLE
        if not (get_gemini_key() and GOOGLE_GENAI_AVAILABLE):
            raise HTTPException(status_code=503, detail="Generación de imágenes no disponible: falta la clave del motor de IA.")
        # Imagen opcional de un ELEMENTO a incorporar (una puerta, un tirador, un
        # electrodoméstico…): viaja como referencia adicional al motor.
        elemento = p.get("elementImageBase64")
        elemento_note = ""
        extra_refs = None
        if elemento:
            extra_refs = [{"data": _strip(elemento), "mime": "image/png"}]
            elemento_note = (
                " Se adjunta una segunda imagen con un ELEMENTO concreto (p. ej. una puerta, "
                "un tirador o un electrodoméstico): incorpóralo o replícalo en la cocina "
                "respetando fielmente su forma, color y acabado."
            )
        prompt = (
            f"Revisión técnica de proyecto. Modifica este render siguiendo estrictamente: \"{instruction}\". "
            "Mantén muros, ventanas y puertas inalterados salvo que se pida explícitamente. "
            "Conserva la iluminación fotorrealista y la calidad de los materiales. Formato 16:9."
            + elemento_note
        )
        data_url = await generate_image_with_gemini(prompt=prompt, reference_image_base64=_strip(prev), reference_mime="image/png", reference_images=extra_refs)
        if not data_url:
            raise HTTPException(status_code=502, detail="La IA no devolvió imagen.")
        return {"imageUrl": data_url}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"cocinasai_edit error: {e}")
        raise HTTPException(status_code=500, detail=f"No se pudo editar el render: {e}")
