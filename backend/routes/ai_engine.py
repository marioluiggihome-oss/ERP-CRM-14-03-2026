"""
LuiggiAI Engine - API Router
==============================
Endpoints públicos del motor de IA white-label.
Todos los endpoints requieren autenticación JWT.

Endpoints:
- GET  /api/ai-engine/status         → Health check del motor
- GET  /api/ai-engine/materials      → Catálogo de materiales
- POST /api/ai-engine/render         → Generar render 3D (texto libre o voz)
- POST /api/ai-engine/render/params  → Generar render 3D (parámetros explícitos)
- POST /api/ai-engine/transcribe     → Transcribir audio a texto
- POST /api/ai-engine/analyze        → Analizar documento
- GET  /api/ai-engine/task/{task_id} → Consultar estado de tarea
"""

import logging
import io
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field

from services.jwt_service import require_auth
from services.luiggi_ai import get_engine, get_render_service, get_ai_config

logger = logging.getLogger("luiggi_ai.router")

ai_engine_router = APIRouter(prefix="/ai-engine", tags=["LuiggiAI Engine"])


# ─── Modelos de Request/Response ──────────────────────────────────────────────

class RenderRequest(BaseModel):
    """Solicitud de render 3D por descripción natural (voz/texto)."""
    description: str = Field(..., description="Descripción en lenguaje natural de la cocina")
    style: Optional[str] = Field(None, description="Estilo de render (photorealistic, warm, etc.)")
    layout: Optional[str] = Field(None, description="Layout override (L-shape, island, etc.)")


class RenderParamsRequest(BaseModel):
    """Solicitud de render 3D con parámetros explícitos."""
    layout: str = Field(default="L-shape", description="Distribución de la cocina")
    countertop: str = Field(default="quartz_white", description="Material de encimera")
    cabinets: str = Field(default="white_matte", description="Material de muebles")
    handles: str = Field(default="bar_black", description="Estilo de tiradores")
    floor: str = Field(default="wood_oak", description="Material del suelo")
    lighting: str = Field(default="natural", description="Tipo de iluminación")
    style: str = Field(default="photorealistic", description="Estilo de renderizado")
    additional_details: Optional[str] = Field(None, description="Detalles adicionales")


class AnalyzeRequest(BaseModel):
    """Solicitud de análisis de documento."""
    analysis_type: str = Field(default="general", description="Tipo: general, catalog, invoice, technical")
    questions: Optional[List[str]] = Field(None, description="Preguntas específicas")


class TaskResponse(BaseModel):
    """Respuesta estándar del motor."""
    success: bool
    engine: str = "LuiggiAI"
    task_id: Optional[str] = None
    status: Optional[str] = None
    result: Optional[dict] = None
    error: Optional[str] = None


# ─── Endpoints ────────────────────────────────────────────────────────────────

@ai_engine_router.get("/status")
async def get_engine_status(user=Depends(require_auth)):
    """Health check del motor LuiggiAI."""
    engine = get_engine()
    status = engine.get_status()
    status["user"] = user.get("username", "unknown")
    return status


@ai_engine_router.get("/materials")
async def get_materials_catalog(user=Depends(require_auth)):
    """Devuelve el catálogo completo de materiales disponibles para renders."""
    service = get_render_service()
    return service.get_materials_catalog()


@ai_engine_router.post("/render")
async def generate_render_natural(request: RenderRequest, user=Depends(require_auth)):
    """
    Genera un render 3D a partir de una descripción en lenguaje natural.
    Acepta texto libre o transcripción de voz.

    Ejemplo: "Quiero una cocina en L con encimera de mármol blanco,
    muebles de roble natural y tiradores negros"
    """
    service = get_render_service()

    # Construir overrides desde parámetros opcionales
    overrides = {}
    if request.style:
        overrides["style"] = request.style
    if request.layout:
        overrides["layout"] = request.layout

    result = await service.generate_render(
        description=request.description,
        params_override=overrides if overrides else None,
    )

    logger.info(f"Render solicitado por {user.get('username')}: {request.description[:80]}...")
    return result


@ai_engine_router.post("/render/params")
async def generate_render_params(request: RenderParamsRequest, user=Depends(require_auth)):
    """
    Genera un render 3D a partir de parámetros explícitos (formulario).
    Usar cuando el usuario selecciona materiales desde el catálogo.
    """
    service = get_render_service()

    result = await service.generate_render_from_params(
        layout=request.layout,
        countertop=request.countertop,
        cabinets=request.cabinets,
        handles=request.handles,
        floor=request.floor,
        lighting=request.lighting,
        style=request.style,
        additional_details=request.additional_details,
    )

    logger.info(f"Render (params) solicitado por {user.get('username')}")
    return result


@ai_engine_router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(..., description="Archivo de audio (webm, wav, mp3)"),
    user=Depends(require_auth),
):
    """
    Transcribe un archivo de audio a texto.
    Útil como fallback cuando Web Speech API no está disponible.
    """
    config = get_ai_config()

    if not config.voice_enabled:
        raise HTTPException(status_code=503, detail="Transcripción de voz no habilitada")

    # Validar tipo de archivo
    allowed_types = ["audio/webm", "audio/wav", "audio/mp3", "audio/mpeg", "audio/ogg"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de archivo no soportado: {file.content_type}"
        )

    # Leer archivo
    audio_data = await file.read()

    # Usar OpenAI Whisper como fallback del navegador
    try:
        import openai
        client = openai.AsyncOpenAI(api_key=config.whisper_api_key)

        audio_file = io.BytesIO(audio_data)
        audio_file.name = file.filename or "audio.webm"

        transcript = await client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="es",
        )

        return {
            "success": True,
            "text": transcript.text,
            "engine": config.brand_name,
            "method": "server_transcription",
        }

    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="Servicio de transcripción no disponible. Use la transcripción del navegador."
        )
    except Exception as e:
        logger.error(f"Error en transcripción: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error al transcribir audio. Intente de nuevo."
        )


@ai_engine_router.post("/analyze")
async def analyze_document(
    file: UploadFile = File(..., description="Documento a analizar (PDF, imagen, etc.)"),
    analysis_type: str = Form(default="general"),
    questions: Optional[str] = Form(default=None, description="Preguntas separadas por |"),
    user=Depends(require_auth),
):
    """
    Analiza un documento y extrae información relevante.
    Tipos: general, catalog, invoice, technical
    """
    config = get_ai_config()

    if not config.document_ai_enabled:
        raise HTTPException(status_code=503, detail="Análisis de documentos no habilitado")

    # Validar tamaño
    file_data = await file.read()
    max_bytes = config.max_file_size_mb * 1024 * 1024
    if len(file_data) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Archivo demasiado grande. Máximo: {config.max_file_size_mb}MB"
        )

    engine = get_engine()

    # Subir archivo
    upload_result = await engine.upload_file(file_data, file.filename)
    if not upload_result.get("success"):
        raise HTTPException(status_code=500, detail="Error al procesar el archivo")

    file_id = upload_result["file_id"]

    # Construir prompt según tipo de análisis
    prompts = {
        "general": f"Analiza el documento '{file.filename}' y proporciona un resumen detallado.",
        "catalog": (
            f"Extrae todos los productos del catálogo '{file.filename}': "
            f"referencia, nombre, dimensiones, materiales, precio. Formato JSON."
        ),
        "invoice": (
            f"Extrae datos de la factura '{file.filename}': "
            f"emisor, receptor, fecha, líneas, importes, IVA, total. Formato JSON."
        ),
        "technical": (
            f"Extrae especificaciones técnicas de '{file.filename}': "
            f"medidas, materiales, instrucciones. Formato estructurado."
        ),
    }

    prompt = prompts.get(analysis_type, prompts["general"])

    # Añadir preguntas específicas
    if questions:
        question_list = [q.strip() for q in questions.split("|") if q.strip()]
        if question_list:
            prompt += "\n\nPreguntas específicas:\n" + "\n".join(f"- {q}" for q in question_list)

    result = await engine.create_task(
        prompt=prompt,
        files=[{"file_id": file_id}],
    )

    if result.get("success"):
        task_id = result["task_id"]
        final = await engine.wait_for_completion(task_id, timeout=120)
        logger.info(f"Análisis '{analysis_type}' solicitado por {user.get('username')}")
        return final

    raise HTTPException(status_code=500, detail=result.get("error", "Error al analizar"))


@ai_engine_router.get("/task/{task_id}")
async def get_task_status(task_id: str, user=Depends(require_auth)):
    """Consulta el estado de una tarea en curso."""
    engine = get_engine()
    result = await engine.get_task_status(task_id)
    return result


# ==================== DESCRIBIR IMAGEN DE REFERENCIA (para el render) ====================
# Sube una imagen/PDF de referencia (foto de cocina, plano, estilo) y la IA de
# vision (Gemini) la describe para enriquecer la descripcion del render 3D.
# Independiente del motor Manus, para que funcione con la GEMINI_API_KEY.
_REF_PROMPT = (
    "Eres un disenador de cocinas. Describe esta imagen de referencia para "
    "generar un render 3D fotorrealista de cocina: distribucion, materiales y "
    "acabados de muebles, color de puertas, encimera, tiradores, suelo, pared, "
    "iluminacion y estilo. Devuelve un parrafo descriptivo en espanol, conciso "
    "y concreto, listo para usar como prompt de render. Solo el texto, sin "
    "encabezados."
)


@ai_engine_router.post("/describe-reference")
async def describe_reference(payload: dict, user=Depends(require_auth)):
    """Describe una imagen/PDF de referencia (base64) para el render 3D."""
    b64 = (payload or {}).get("fileBase64") or ""
    if not b64:
        raise HTTPException(status_code=400, detail="Falta el archivo (fileBase64)")
    stripped = b64.split(",", 1)[1] if b64.startswith("data:") else b64
    try:
        from services.pdf_utils import is_pdf_base64, pdf_base64_to_png_base64
        from services.llm_vision import analyze_image_with_gemini
        img = stripped
        # Si es un PDF, rasterizar la primera pagina.
        try:
            if ("pdf" in b64[:40].lower()) or is_pdf_base64(stripped):
                pages = pdf_base64_to_png_base64(stripped, dpi=150, max_pages=1) or []
                if pages:
                    img = pages[0]
        except Exception:
            pass
        import uuid as _uuid
        resp = await analyze_image_with_gemini(
            image_base64=img, prompt=_REF_PROMPT,
            session_id=f"render-ref-{_uuid.uuid4().hex[:8]}", model="gemini-2.0-flash",
        )
        text = (resp or "").strip()
        if text.startswith("```"):
            text = text.strip("`").strip()
        return {"success": True, "description": text}
    except Exception as e:
        logger.error(f"describe-reference error: {e}")
        return {"success": False, "error": str(e)}
