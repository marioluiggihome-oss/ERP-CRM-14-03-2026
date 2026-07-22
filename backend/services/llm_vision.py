"""
LLM Vision Helper - Wrapper unificado para análisis de imágenes con Gemini.

Estrategia:
1. Si existe GEMINI_API_KEY en entorno → usa google-genai directamente (funciona desde cualquier servidor)
2. Si no, usa emergentintegrations con EMERGENT_LLM_KEY (solo dentro de plataforma Emergent)

De esta manera la app funciona tanto en preview (Emergent) como en producción (Railway).
"""
import os
import base64
import logging
import asyncio
from typing import Optional, List

logger = logging.getLogger(__name__)

# Modelo de visión/texto preferido, configurable por entorno SIN tocar código.
# Permite adoptar modelos más nuevos y baratos (p. ej. gemini-3.6-flash,
# gemini-3.5-flash-lite) poniendo GEMINI_VISION_MODEL en Railway. Si el modelo no
# existe para la clave, la lista de respaldo sigue con gemini-2.5-flash/pro.
GEMINI_VISION_MODEL = (os.environ.get("GEMINI_VISION_MODEL") or "").strip() or None

def _con_preferido(lista):
    """Antepone el modelo preferido (env) a la lista de candidatos, sin duplicar."""
    out = []
    for m in ([GEMINI_VISION_MODEL] if GEMINI_VISION_MODEL else []) + list(lista):
        if m and m not in out:
            out.append(m)
    return out

# Contador de consumo de IA (best-effort; nunca debe romper una llamada).
try:
    from services.ai_usage import record_ai_usage, record_ai_tokens, usage_from_response
except Exception:  # pragma: no cover
    async def record_ai_usage(*a, **k):
        return
    async def record_ai_tokens(*a, **k):
        return
    def usage_from_response(resp):
        return 0, 0

# Intentar importar google.genai (nuevo SDK)
try:
    from google import genai as google_genai
    from google.genai import types as google_genai_types
    GOOGLE_GENAI_AVAILABLE = True
except ImportError:
    google_genai = None
    google_genai_types = None
    GOOGLE_GENAI_AVAILABLE = False

# Intentar importar emergentintegrations (entorno Emergent)
try:
    from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent
    EMERGENT_AVAILABLE = True
except ImportError:
    LlmChat = None
    UserMessage = None
    ImageContent = None
    EMERGENT_AVAILABLE = False


def _clean_key(raw: Optional[str]) -> Optional[str]:
    """Limpia una API key de espacios, saltos de línea y comillas accidentales
    (causa típica de 401 al pegar el valor en el panel de variables)."""
    if not raw:
        return None
    key = raw.strip().strip('"').strip("'").strip()
    return key or None


def get_gemini_key() -> Optional[str]:
    """Devuelve la API key de Gemini si está disponible."""
    return _clean_key(os.environ.get('GEMINI_API_KEY'))


def get_emergent_key() -> Optional[str]:
    """Devuelve la EMERGENT_LLM_KEY si está disponible."""
    return _clean_key(os.environ.get('EMERGENT_LLM_KEY'))


def is_vision_available() -> bool:
    """¿Hay alguna forma de hacer Vision en este entorno?"""
    has_gemini = bool(get_gemini_key()) and GOOGLE_GENAI_AVAILABLE
    has_emergent = bool(get_emergent_key()) and EMERGENT_AVAILABLE
    return has_gemini or has_emergent


async def analyze_image_with_gemini(
    image_base64: str,
    prompt: str,
    session_id: str = "default",
    model: str = "gemini-2.5-flash",
    image_mime: str = "image/jpeg",
) -> str:
    """
    Analiza una imagen con Gemini Vision usando la mejor opción disponible.
    
    Args:
        image_base64: Imagen codificada en base64 (sin el prefijo "data:image/...;base64,")
        prompt: Texto del prompt para la IA
        session_id: ID de sesión (para tracking)
        model: Modelo de Gemini a usar (gemini-2.5-flash, gemini-2.5-pro)
        image_mime: MIME type de la imagen (image/jpeg, image/png)
    
    Returns:
        Texto de la respuesta de la IA
    
    Raises:
        RuntimeError si no hay forma de hacer Vision en el entorno actual
    """
    await record_ai_usage("vision")
    # Limpiar prefijo data: si viene
    is_pdf_header = False
    if image_base64.startswith('data:'):
        # data:image/jpeg;base64,XXXX → XXXX
        header, image_base64 = image_base64.split(',', 1)
        header_l = header.lower()
        # Detectar MIME del header
        if 'pdf' in header_l:
            is_pdf_header = True
        elif 'png' in header_l:
            image_mime = 'image/png'
        elif 'jpeg' in header_l or 'jpg' in header_l:
            image_mime = 'image/jpeg'
        elif 'webp' in header_l:
            image_mime = 'image/webp'

    # Si el contenido es un PDF (por header o por magic bytes), rasterizar la
    # primera página a PNG: Gemini Vision no acepta PDFs directamente aquí.
    try:
        from services.pdf_utils import is_pdf_base64, pdf_base64_to_png_base64
        if is_pdf_header or is_pdf_base64(image_base64):
            pages = pdf_base64_to_png_base64(image_base64, dpi=150, max_pages=1)
            if not pages:
                raise RuntimeError("No se pudo convertir el PDF a imagen.")
            image_base64 = pages[0]
            image_mime = 'image/png'
    except RuntimeError:
        raise
    except Exception as e:
        logger.warning(f"No se pudo evaluar/convertir PDF en vision: {e}")

    gemini_key = get_gemini_key()
    
    # SIEMPRE usar google-genai en producción Railway
    if gemini_key and GOOGLE_GENAI_AVAILABLE:
        return await _analyze_with_google_genai(
            image_base64, prompt, model, image_mime, gemini_key
        )
    
    # Fallback: emergentintegrations SOLO si estamos dentro de Emergent
    # (no funciona en Railway con plan free)
    emergent_key = get_emergent_key()
    if emergent_key and EMERGENT_AVAILABLE and not gemini_key:
        return await _analyze_with_emergent(
            image_base64, prompt, session_id, model, emergent_key
        )
    
    raise RuntimeError(
        "Vision IA no disponible. Falta la clave del motor de IA en el servidor."
    )


async def _analyze_with_google_genai(
    image_base64: str,
    prompt: str,
    model: str,
    image_mime: str,
    api_key: str,
) -> str:
    """Implementación con SDK oficial google-genai (async)."""
    import asyncio
    client = google_genai.Client(api_key=api_key)

    image_bytes = base64.b64decode(image_base64)

    # Lista ordenada de modelos a intentar. Si Google devuelve NOT_FOUND/404 para
    # uno (porque ese nombre fue renombrado/retirado), se prueba el siguiente.
    requested = model or "gemini-2.5-flash"
    candidates = []
    for m in _con_preferido([requested, "gemini-2.5-flash",
              "gemini-flash-latest", "gemini-2.5-pro"]):
        if m not in candidates:
            candidates.append(m)

    # Ejecutar en executor para no bloquear el event loop
    def _sync_call(model_name):
        response = client.models.generate_content(
            model=model_name,
            contents=[
                google_genai_types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=image_mime,
                ),
                prompt,
            ],
            # temperature=0 -> respuestas estables/repetibles para el mismo plano.
            # max_output_tokens alto: gemini-2.5-pro es un modelo "thinking" y, sin un
            # presupuesto amplio, el razonamiento agota la salida y TRUNCA el JSON
            # (se pierden muebles detectados). 16384 deja sitio de sobra para el
            # razonamiento + un listado largo de muebles.
            config=google_genai_types.GenerateContentConfig(temperature=0, max_output_tokens=16384),
        )
        return response

    loop = asyncio.get_event_loop()
    last_err = None
    for model_name in candidates:
        try:
            response = await loop.run_in_executor(None, _sync_call, model_name)
            it, ot = usage_from_response(response)
            await record_ai_tokens("vision", model_name, it, ot, 0, count=False)
            return response.text or ""
        except Exception as e:
            msg = str(e)
            if 'NOT_FOUND' in msg or '404' in msg or 'not found' in msg.lower() or 'not supported' in msg.lower():
                last_err = e
                logger.warning(f"Modelo Gemini '{model_name}' no disponible, probando siguiente: {msg[:120]}")
                continue
            raise
    raise last_err or RuntimeError("Ningún modelo de Gemini disponible para esta clave")


async def _analyze_with_emergent(
    image_base64: str,
    prompt: str,
    session_id: str,
    model: str,
    api_key: str,
) -> str:
    """Implementación con emergentintegrations (entorno Emergent)."""
    chat = LlmChat(
        api_key=api_key,
        session_id=session_id,
        system_message="Eres un asistente experto.",
    ).with_model("gemini", model)
    
    image_content = ImageContent(image_base64=image_base64)
    user_message = UserMessage(text=prompt, file_contents=[image_content])
    
    response = await chat.send_message(user_message)
    return response or ""


async def chat_with_gemini(
    prompt: str,
    system_message: str = "Eres un asistente experto.",
    session_id: str = "default",
    model: str = "gemini-2.5-flash",
) -> str:
    """Chat de texto sin imagen."""
    gemini_key = get_gemini_key()
    
    if gemini_key and GOOGLE_GENAI_AVAILABLE:
        client = google_genai.Client(api_key=gemini_key)

        # Lista ordenada de modelos a intentar. Si Google retira/renombra uno
        # (NOT_FOUND/404), se prueba el siguiente, igual que en visión.
        requested = model or "gemini-2.5-flash"
        candidates = []
        for m in _con_preferido([requested, "gemini-2.5-flash", "gemini-flash-latest", "gemini-2.5-pro"]):
            if m not in candidates:
                candidates.append(m)

        contents = f"{system_message}\n\n{prompt}" if system_message else prompt

        last_err = None
        for model_name in candidates:
            try:
                def _sync_call(_m=model_name, _c=contents):
                    return client.models.generate_content(model=_m, contents=_c)
                response = await asyncio.to_thread(_sync_call)
                it, ot = usage_from_response(response)
                await record_ai_tokens("text", model_name, it, ot, 0, count=True)
                return response.text or ""
            except Exception as e:
                msg = str(e)
                if 'NOT_FOUND' in msg or '404' in msg or 'not found' in msg.lower() or 'not supported' in msg.lower():
                    last_err = e
                    logger.warning(f"Modelo Gemini '{model_name}' no disponible, probando siguiente: {msg[:120]}")
                    continue
                raise
        raise last_err or RuntimeError("Ningún modelo de Gemini disponible para esta clave")
    
    emergent_key = get_emergent_key()
    if emergent_key and EMERGENT_AVAILABLE:
        chat = LlmChat(
            api_key=emergent_key,
            session_id=session_id,
            system_message=system_message,
        ).with_model("gemini", model)
        
        user_message = UserMessage(text=prompt)
        response = await chat.send_message(user_message)
        return response or ""
    
    raise RuntimeError(
        "Chat IA no disponible. Configura GEMINI_API_KEY en las variables de entorno."
    )


async def search_with_gemini(
    prompt: str,
    model: str = "gemini-2.5-flash",
):
    """Genera texto con Gemini usando Google Search (grounding). Devuelve
    (texto, fuentes[{uri,title}]). Si la búsqueda falla por cuota/permiso, hace
    fallback a generación sin búsqueda. Requiere GEMINI_API_KEY + google-genai."""
    gemini_key = get_gemini_key()
    if not (gemini_key and GOOGLE_GENAI_AVAILABLE):
        raise RuntimeError("IA no disponible. Configura GEMINI_API_KEY en las variables de entorno.")
    client = google_genai.Client(api_key=gemini_key)
    requested = model or "gemini-2.5-flash"
    candidates = []
    for m in _con_preferido([requested, "gemini-2.5-flash", "gemini-flash-latest", "gemini-2.5-pro"]):
        if m not in candidates:
            candidates.append(m)

    def _sync(model_name, with_search):
        cfg = None
        if with_search:
            try:
                tool = google_genai_types.Tool(google_search=google_genai_types.GoogleSearch())
                cfg = google_genai_types.GenerateContentConfig(tools=[tool])
            except Exception:
                cfg = None
        return client.models.generate_content(model=model_name, contents=prompt, config=cfg)

    def _sources(resp):
        out = []
        try:
            for cand in (getattr(resp, "candidates", None) or []):
                gm = getattr(cand, "grounding_metadata", None)
                for ch in (getattr(gm, "grounding_chunks", None) or []):
                    web = getattr(ch, "web", None)
                    if web and getattr(web, "uri", None):
                        out.append({"uri": web.uri, "title": getattr(web, "title", "") or web.uri})
        except Exception:
            pass
        return out

    last_err = None
    for model_name in candidates:
        try:
            resp = await asyncio.to_thread(_sync, model_name, True)
            it, ot = usage_from_response(resp)
            await record_ai_tokens("search", model_name, it, ot, 0, count=True)
            return (resp.text or "", _sources(resp), False)
        except Exception as e:
            msg = str(e)
            if 'NOT_FOUND' in msg or '404' in msg or 'not found' in msg.lower() or 'not supported' in msg.lower():
                last_err = e; continue
            # Cuota/permiso de Google Search → fallback sin búsqueda
            if any(x in msg for x in ('RESOURCE_EXHAUSTED', 'quota', 'PERMISSION_DENIED', 'permission', '429', '403')):
                try:
                    resp = await asyncio.to_thread(_sync, model_name, False)
                    it, ot = usage_from_response(resp)
                    await record_ai_tokens("search", model_name, it, ot, 0, count=True)
                    return (resp.text or "", [], True)
                except Exception as e2:
                    last_err = e2; continue
            raise
    raise last_err or RuntimeError("Ningún modelo de Gemini disponible para esta clave")


# ============================================================================
# GENERACIÓN DE IMÁGENES (render) con Gemini — usado por Render 3D y Armarios
# ============================================================================

# Modelos de imagen candidatos (cascada ante retirada/renombrado de modelos)
GEMINI_IMAGE_MODELS = [
    "gemini-3-pro-image-preview",
    "gemini-2.5-flash-image",
    "gemini-2.5-flash-image-preview",
]


def _extract_inline_image(response) -> Optional[str]:
    """Extrae la primera imagen de una respuesta de google-genai como data URL."""
    try:
        for cand in (getattr(response, "candidates", None) or []):
            content = getattr(cand, "content", None)
            for part in (getattr(content, "parts", None) or []):
                inline = getattr(part, "inline_data", None)
                data = getattr(inline, "data", None) if inline else None
                if data:
                    mime = getattr(inline, "mime_type", None) or "image/png"
                    if isinstance(data, (bytes, bytearray)):
                        b64 = base64.b64encode(data).decode("ascii")
                    else:
                        b64 = str(data)  # algunas versiones ya devuelven base64
                    return f"data:{mime};base64,{b64}"
    except Exception as e:
        logger.warning(f"No se pudo extraer imagen de la respuesta: {e}")
    return None


async def generate_text_with_gemini(prompt: str, model: str = "gemini-2.5-pro",
                                    temperature: float = 0.6) -> Optional[str]:
    """Genera TEXTO con Gemini (modelo potente por defecto, con cascada de respaldo).

    Se usa, por ejemplo, para expandir un brief de render en una especificación
    detallada. Devuelve None si no hay clave/SDK o si todos los modelos fallan.
    """
    import asyncio
    key = get_gemini_key()
    if not (key and GOOGLE_GENAI_AVAILABLE):
        return None
    client = google_genai.Client(api_key=key)
    candidates = []
    for m in [model, "gemini-2.5-flash", "gemini-flash-latest"]:
        if m not in candidates:
            candidates.append(m)

    def _sync_call(model_name):
        cfg = google_genai_types.GenerateContentConfig(temperature=temperature)
        resp = client.models.generate_content(model=model_name, contents=[prompt], config=cfg)
        return (resp.text or "").strip()

    loop = asyncio.get_event_loop()
    for model_name in candidates:
        try:
            txt = await loop.run_in_executor(None, _sync_call, model_name)
            if txt:
                return txt
        except Exception as e:
            msg = str(e)
            logger.warning(f"generate_text_with_gemini: modelo '{model_name}' falló: {msg[:140]}")
            continue
    return None


async def generate_image_with_gemini(
    prompt: str,
    reference_image_base64: Optional[str] = None,
    reference_mime: str = "image/png",
    reference_images: Optional[list] = None,
) -> str:
    """
    Genera una imagen con Gemini a partir de un prompt (y opcionalmente una
    imagen de referencia). Devuelve un data URL 'data:image/png;base64,...'.

    Funciona en Railway usando GEMINI_API_KEY (SDK google-genai). Lanza
    RuntimeError si no hay forma de generar imagen en este entorno.
    """
    await record_ai_usage("render")
    import asyncio

    key = get_gemini_key()
    if not (key and GOOGLE_GENAI_AVAILABLE):
        raise RuntimeError("Generación de imágenes no disponible: configura GEMINI_API_KEY.")

    client = google_genai.Client(api_key=key)

    contents = []
    # Lista unificada de imágenes de referencia: admite VARIAS (p.ej. plano en
    # planta + un boceto por cada pared), además de la referencia única clásica.
    refs = []
    for it in (reference_images or []):
        if not it:
            continue
        if isinstance(it, dict):
            data, mime = it.get("data"), (it.get("mime") or "image/png")
        else:
            data, mime = it, "image/png"
        if data:
            refs.append((data, mime))
    if reference_image_base64:
        refs.append((reference_image_base64, reference_mime or "image/png"))
    for data, mime in refs:
        try:
            ref = data
            if isinstance(ref, str) and ref.startswith("data:"):
                ref = ref.split(",", 1)[1]
            img_bytes = base64.b64decode(ref)
            contents.append(google_genai_types.Part.from_bytes(data=img_bytes, mime_type=mime))
        except Exception as e:
            logger.warning(f"Imagen de referencia ignorada: {e}")
    contents.append(prompt)

    # Encuadre 16:9 apaisado (por defecto el modelo genera cuadrado y recorta la
    # cocina). Se aplica de forma defensiva: si la versión del SDK no soporta
    # ImageConfig/aspect_ratio, se cae al config normal sin romper.
    # Encuadre 16:9 apaisado (config probada y estable). Se aplica de forma
    # defensiva: si la versión del SDK no soporta ImageConfig/aspect_ratio, se
    # cae al config normal sin romper.
    def _make_cfg(model_name=None):
        try:
            return google_genai_types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
                image_config=google_genai_types.ImageConfig(aspect_ratio="16:9"),
            )
        except Exception:
            return google_genai_types.GenerateContentConfig(response_modalities=["IMAGE", "TEXT"])

    def _sync_call(model_name):
        cfg = _make_cfg(model_name)
        resp = client.models.generate_content(model=model_name, contents=contents, config=cfg)
        return _extract_inline_image(resp), resp

    loop = asyncio.get_event_loop()
    last_err = None
    for model_name in GEMINI_IMAGE_MODELS:
        try:
            data_url, resp = await asyncio.wait_for(
                loop.run_in_executor(None, _sync_call, model_name), timeout=90
            )
            if data_url:
                it, ot = usage_from_response(resp)
                await record_ai_tokens("render", model_name, it, ot, 1, count=False)
                return data_url
            last_err = RuntimeError(f"'{model_name}' no devolvió imagen")
            logger.warning(f"Modelo de imagen '{model_name}' no devolvió imagen, probando siguiente")
        except asyncio.TimeoutError:
            last_err = RuntimeError(f"'{model_name}' tardó demasiado en responder")
            logger.warning(f"Modelo de imagen '{model_name}' agotó el tiempo de espera (90s)")
            continue
        except Exception as e:
            last_err = e
            logger.warning(f"Modelo de imagen '{model_name}' falló: {str(e)[:140]}")
            continue
    raise RuntimeError(f"No se pudo generar la imagen. {last_err or ''}".strip())
