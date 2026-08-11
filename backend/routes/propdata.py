# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
PropData AI — Prospección de obra nueva (promociones inmobiliarias) con Gemini.
Basado en el app de AI Studio "PropData AI": extrae promociones desde portales
(búsqueda con grounding) o desde una captura (visión). Uso comercial: localizar
promotores/obras a los que ofrecer cocinas.
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

router = APIRouter(tags=["propdata"], dependencies=_DEPS)


def _parse_json(text: str):
    if not text:
        return []
    m = re.search(r"```json\s*([\s\S]*?)```", text) or re.search(r"```\s*([\s\S]*?)```", text)
    raw = m.group(1) if m else text
    raw = raw.strip()
    try:
        data = json.loads(raw)
    except Exception:
        # buscar el primer array del texto
        a = re.search(r"\[[\s\S]*\]", raw)
        if not a:
            return []
        try:
            data = json.loads(a.group())
        except Exception:
            return []
    return data if isinstance(data, list) else data.get("developments", []) if isinstance(data, dict) else []


def _strip_json_blocks(text: str) -> str:
    return re.sub(r"```[\s\S]*?```", "", text or "").strip()


SEARCH_PROMPT = """Actúa como un experto analista en prospección inmobiliaria de obra nueva en España.
Busca información REAL Y ACTUAL en Google sobre promociones inmobiliarias de "obra nueva" en {location}{portal}.

INSTRUCCIONES CRÍTICAS DE BÚSQUEDA Y EXTRACCIÓN:
1. Realiza búsquedas activas sobre promociones en comercialización o construcción en {location}.
2. Para CADA promoción localizada, investiga los datos de contacto y detalles comerciales reales:
   - Nombre oficial del residencial / promoción.
   - Promotora, gestora o comercializadora responsable (ej: Neinor, Aedas Homes, Culmia, Metrovacesa, Libra Gestión, Kronos, etc.).
   - Teléfono oficial de información / caseta de ventas (busca activamente el número de contacto del promotor o comercializadora en su web o fichas).
   - Dirección física completa o calle/zona donde se ubica la obra.
   - URL real y directa de la promoción o ficha del portal (ej: https://... NO inventes enlaces).
   - Precio de partida ("Desde XXX.XXX €").
   - Fechas estimadas (inicio de obras / fecha prevista de entrega).
   - Tipo de vivienda (Pisos, Chalets, Unifamiliares, etc.).
   - Breve descripción del proyecto (número de viviendas, calidades, etc.).

Devuelve UNICAMENTE un bloque de código JSON con esta estructura exacta:
```json
[
  {{"name":"","promoter":"","phone":"","address":"","url":"","startDate":"","deliveryDate":"","type":"Piso","location":"","priceStart":"","description":""}}
]
```
Después del bloque JSON, añade un breve informe resumido de la situación de la obra nueva en esa zona."""

IMAGE_PROMPT = """Analiza esta captura de un portal inmobiliario e identifica las promociones de obra nueva listadas.
Para cada tarjeta/elemento extrae: nombre, promotor, teléfono, fechas de inicio/entrega, tipo de vivienda, ubicación, precio y una breve descripción.
Devuelve SOLO un bloque JSON con este formato:
```json
[
  {"name":"","promoter":"","phone":"","startDate":"","deliveryDate":"","type":"Piso","location":"","priceStart":"","description":""}
]
```"""


@router.post("/propdata/search")
async def propdata_search(payload: dict):
    location = str((payload or {}).get("location") or "").strip()
    portal = str((payload or {}).get("portal") or "").strip()
    if not location:
        raise HTTPException(status_code=400, detail="Indica una ubicación (ciudad/zona).")
    try:
        from services.llm_vision import search_with_gemini, is_vision_available
        if not is_vision_available():
            raise HTTPException(status_code=503, detail="IA no configurada. Falta la clave del motor de IA (contacta con el administrador).")
        portal_txt = f" listadas en portales como {portal} (o información general)" if portal else ""
        prompt = SEARCH_PROMPT.format(location=location, portal=portal_txt)
        text, sources, grounding_failed = await search_with_gemini(prompt)
        return {
            "developments": _parse_json(text),
            "summary": _strip_json_blocks(text) or "Análisis completado.",
            "groundingSources": sources,
            "groundingFailed": grounding_failed,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"propdata_search error: {e}")
        raise HTTPException(status_code=500, detail=f"No se pudo completar la búsqueda: {e}")


@router.post("/propdata/image")
async def propdata_image(payload: dict):
    img = (payload or {}).get("imageBase64") or ""
    if not img:
        raise HTTPException(status_code=400, detail="Falta la imagen.")
    try:
        from services.llm_vision import analyze_image_with_gemini, is_vision_available
        if not is_vision_available():
            raise HTTPException(status_code=503, detail="IA no configurada. Falta la clave del motor de IA (contacta con el administrador).")
        text = await analyze_image_with_gemini(image_base64=img, prompt=IMAGE_PROMPT, model="gemini-2.5-flash")
        return {"developments": _parse_json(text), "summary": _strip_json_blocks(text) or "Análisis de imagen completado."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"propdata_image error: {e}")
        raise HTTPException(status_code=500, detail=f"No se pudo analizar la imagen: {e}")
