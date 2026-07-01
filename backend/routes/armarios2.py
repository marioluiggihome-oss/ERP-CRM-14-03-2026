"""
Armarios 2 — Diseñador de armarios con IA (Gemini). Endpoints:
- /armarios2/plan : analiza un plano/foto y devuelve medidas (ancho/alto/fondo).
- /armarios2/render : genera (o edita) un render realista del armario.
Reutiliza la IA del servidor (services.llm_vision) con GEMINI_API_KEY.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
import json
import re
import logging

logger = logging.getLogger(__name__)

try:
    from services.jwt_service import require_auth
    _DEPS = [Depends(require_auth)]
except Exception:
    _DEPS = []

router = APIRouter(tags=["armarios2"], dependencies=_DEPS)


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
            raise HTTPException(status_code=503, detail="IA no configurada. Añade GEMINI_API_KEY en variables de entorno.")
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
            raise HTTPException(status_code=503, detail="Generación de imágenes no disponible: configura GEMINI_API_KEY.")
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

        if edit and prev:
            prompt = (
                f"Edita este render de {tipo} manteniendo el estilo y encuadre. Cambio pedido: {edit}. "
                "Fotorrealista, iluminación de catálogo, fondo neutro."
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
