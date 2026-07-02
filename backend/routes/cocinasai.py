"""
Cocinas IA 2 — Render fotorrealista de cocina a partir de planos/alzados (Gemini
image). Portado de "KitchAI Design Studio". Reutiliza services.llm_vision.
"""
from fastapi import APIRouter, HTTPException, Depends
import logging

logger = logging.getLogger(__name__)

try:
    from services.jwt_service import require_auth
    _DEPS = [Depends(require_auth)]
except Exception:
    _DEPS = []

router = APIRouter(tags=["cocinasai"], dependencies=_DEPS)


def _strip(b64):
    if isinstance(b64, str) and b64.startswith("data:"):
        return b64.split(",", 1)[1]
    return b64


@router.post("/cocinasai/design")
async def cocinasai_design(payload: dict):
    """Genera un render de cocina a partir de uno o varios planos/alzados."""
    p = payload or {}
    plans = p.get("images") or ([p.get("imageBase64")] if p.get("imageBase64") else [])
    plans = [x for x in plans if x]
    kitchen_type = str(p.get("kitchenType") or "Cocina Sola")
    style = str(p.get("style") or "Moderno")
    notes = str(p.get("notes") or "")
    try:
        from services.llm_vision import generate_image_with_gemini, get_gemini_key, GOOGLE_GENAI_AVAILABLE
        if not (get_gemini_key() and GOOGLE_GENAI_AVAILABLE):
            raise HTTPException(status_code=503, detail="Generación de imágenes no disponible: configura GEMINI_API_KEY.")
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
async def cocinasai_edit(payload: dict):
    """Edita un render existente en lenguaje natural."""
    p = payload or {}
    prev = p.get("previousImageBase64")
    instruction = str(p.get("instruction") or "").strip()
    if not prev or not instruction:
        raise HTTPException(status_code=400, detail="Faltan la imagen o la instrucción.")
    try:
        from services.llm_vision import generate_image_with_gemini, get_gemini_key, GOOGLE_GENAI_AVAILABLE
        if not (get_gemini_key() and GOOGLE_GENAI_AVAILABLE):
            raise HTTPException(status_code=503, detail="Generación de imágenes no disponible: configura GEMINI_API_KEY.")
        prompt = (
            f"Revisión técnica de proyecto. Modifica este render siguiendo estrictamente: \"{instruction}\". "
            "Mantén muros, ventanas y puertas inalterados salvo que se pida explícitamente. "
            "Conserva la iluminación fotorrealista y la calidad de los materiales. Formato 16:9."
        )
        data_url = await generate_image_with_gemini(prompt=prompt, reference_image_base64=_strip(prev), reference_mime="image/png")
        if not data_url:
            raise HTTPException(status_code=502, detail="La IA no devolvió imagen.")
        return {"imageUrl": data_url}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"cocinasai_edit error: {e}")
        raise HTTPException(status_code=500, detail=f"No se pudo editar el render: {e}")
