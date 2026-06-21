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
from urllib.parse import urlparse
from typing import Optional, List
import httpx
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Header
from fastapi.responses import Response
from pydantic import BaseModel, Field

from services.jwt_service import require_auth, verify_access_token
from services.luiggi_ai import get_engine, get_render_service, get_ai_config

logger = logging.getLogger("luiggi_ai.router")

ai_engine_router = APIRouter(prefix="/ai-engine", tags=["LuiggiAI Engine"])


# ─── Modelos de Request/Response ──────────────────────────────────────────────

class RenderRequest(BaseModel):
    """Solicitud de render 3D por descripción natural (voz/texto)."""
    description: str = Field(..., description="Descripción en lenguaje natural de la cocina")
    style: Optional[str] = Field(None, description="Estilo de render (photorealistic, warm, etc.)")
    layout: Optional[str] = Field(None, description="Layout override (L-shape, island, etc.)")
    referenceImage: Optional[str] = Field(None, description="Imagen/PDF de referencia en base64 para condicionar el render")
    referenceMime: Optional[str] = Field(None, description="MIME de la imagen de referencia")


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


@ai_engine_router.get("/diagnostics")
async def engine_diagnostics(user=Depends(require_auth)):
    """Diagnóstico del motor de render: ¿ve las claves (Manus/Gemini)? ¿conecta con
    el proveedor? No crea tareas ni gasta créditos: solo comprueba configuración y
    una conexión ligera."""
    import os
    config = get_ai_config()
    manus_key = getattr(config, "provider_api_key", "") or ""
    manus_present = bool(manus_key)

    try:
        from services.llm_vision import get_gemini_key, GOOGLE_GENAI_AVAILABLE
        gemini_present = bool(get_gemini_key())
        gemini_sdk = bool(GOOGLE_GENAI_AVAILABLE)
    except Exception:
        gemini_present, gemini_sdk = False, False

    provider = (os.environ.get("KITCHEN_RENDER_PROVIDER") or "manus").lower()

    # Conectividad con Manus (sin crear tareas): un GET ligero al proveedor.
    manus_reachable, manus_http_status, manus_error = None, None, None
    if manus_present:
        try:
            async with httpx.AsyncClient(timeout=10.0) as c:
                r = await c.get(config.provider_base_url,
                                headers={"Authorization": f"Bearer {manus_key}"})
                manus_reachable, manus_http_status = True, r.status_code
        except Exception as e:
            manus_reachable, manus_error = False, type(e).__name__

    if provider == "manus" and manus_present:
        effective = "manus"
    elif gemini_present and gemini_sdk:
        effective = "gemini"
    else:
        effective = "ninguno"

    return {
        "render_provider_config": provider,
        "effective_engine": effective,
        "manus": {
            "key_present": manus_present,
            "key_length": len(manus_key) if manus_present else 0,
            "reachable": manus_reachable,
            "http_status": manus_http_status,
            "error": manus_error,
        },
        "gemini": {"key_present": gemini_present, "sdk_available": gemini_sdk},
        "hint": (
            "El render usará MANUS." if effective == "manus"
            else "El render usará GEMINI (respaldo)." if effective == "gemini"
            else "Falta configurar MANUS_API_KEY (o GEMINI_API_KEY) en Railway."
        ),
    }


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
        reference_image=request.referenceImage,
        reference_mime=request.referenceMime,
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

    # Transcripción en servidor como fallback cuando el navegador no la soporta
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


# ─── Proxy de assets (white-label) ────────────────────────────────────────────
# Sirve las imágenes generadas a través de este backend para que el navegador
# del cliente nunca vea el dominio del proveedor subyacente. Solo se permiten
# URLs cuyo host pertenezca a la lista de dominios autorizados (evita SSRF).
_IMG_CONTENT_TYPES = ("image/", "application/pdf", "application/octet-stream")


@ai_engine_router.get("/asset")
async def proxy_asset(
    u: str,
    t: Optional[str] = None,
    authorization: Optional[str] = Header(None),
):
    """
    Descarga y reenvía un asset del proveedor ocultando su origen.

    Acepta el token JWT por cabecera `Authorization` o por query param `t`,
    porque las etiquetas <img> del navegador no pueden enviar cabeceras.
    """
    token = t
    if not token and authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Autenticación requerida")
    verify_access_token(token)  # lanza 401 si es inválido/expirado

    engine = get_engine()
    config = get_ai_config()

    try:
        original_url = engine.decode_proxy_token(u)
    except Exception:
        raise HTTPException(status_code=400, detail="Recurso no válido")

    host = ""
    try:
        parsed = urlparse(original_url)
        host = parsed.netloc.split("@")[-1].split(":")[0].lower()
    except Exception:
        host = ""

    if parsed.scheme not in ("http", "https") or not engine._is_provider_host(host):
        # Nunca permitir URLs arbitrarias (protección anti-SSRF).
        raise HTTPException(status_code=403, detail="Recurso no autorizado")

    # Solo el host de la API necesita el token de autorización; los CDN/buckets
    # usan URLs prefirmadas y rechazan cabeceras de auth extra.
    headers = {}
    api_host = urlparse(config.provider_base_url).netloc.split(":")[0].lower()
    if host == api_host:
        headers["Authorization"] = f"Bearer {config.provider_api_key}"

    try:
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            resp = await client.get(original_url, headers=headers)
    except Exception as e:
        logger.error(f"Proxy asset error: {e}")
        raise HTTPException(status_code=502, detail="No se pudo obtener el recurso")

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Recurso no disponible")

    content_type = resp.headers.get("content-type", "application/octet-stream")
    return Response(
        content=resp.content,
        media_type=content_type,
        headers={"Cache-Control": "private, max-age=3600"},
    )


# ==================== DESCRIBIR IMAGEN DE REFERENCIA (para el render) ====================
# Sube una imagen/PDF de referencia (foto de cocina, plano, estilo) y el motor
# de vision la describe para enriquecer la descripcion del render 3D. Usa una
# ruta de vision independiente del motor de render principal.
_REF_PROMPT = (
    "Eres un disenador de interiores y mobiliario a medida (cocinas, armarios "
    "empotrados, banos, dormitorios, estanterias, muebles a medida...). Describe "
    "esta imagen de referencia para generar un render 3D fotorrealista del MISMO "
    "tipo de elemento que aparece (no asumas que es una cocina): tipo de mueble o "
    "espacio, distribucion, materiales y acabados, color de puertas, tiradores, "
    "interior (baldas, columnas, cajones), suelo, pared, iluminacion y estilo. "
    "Devuelve un parrafo descriptivo en espanol, conciso y concreto, listo para "
    "usar como prompt de render. Solo el texto, sin encabezados."
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
            session_id=f"render-ref-{_uuid.uuid4().hex[:8]}", model="gemini-2.5-pro",
        )
        text = (resp or "").strip()
        if text.startswith("```"):
            text = text.strip("`").strip()
        if not text:
            return {"success": False, "error": "No se pudo interpretar la imagen de referencia. Pruebe con otra imagen."}
        # Sanitizar por si el motor de vision incluyera alguna marca propia.
        text = get_engine()._sanitize_response(text)
        return {"success": True, "description": text}
    except Exception as e:
        # Nunca exponer el detalle del proveedor al cliente: log interno + mensaje genérico.
        logger.error(f"describe-reference error: {e}")
        return {"success": False, "error": "No se pudo analizar la imagen de referencia. Inténtelo de nuevo."}
