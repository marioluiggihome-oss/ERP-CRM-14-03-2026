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
from typing import Optional, List

logger = logging.getLogger(__name__)

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


def get_gemini_key() -> Optional[str]:
    """Devuelve la API key de Gemini si está disponible."""
    return os.environ.get('GEMINI_API_KEY')


def get_emergent_key() -> Optional[str]:
    """Devuelve la EMERGENT_LLM_KEY si está disponible."""
    return os.environ.get('EMERGENT_LLM_KEY')


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
    # Limpiar prefijo data: si viene
    if image_base64.startswith('data:'):
        # data:image/jpeg;base64,XXXX → XXXX
        header, image_base64 = image_base64.split(',', 1)
        # Detectar MIME del header
        if 'png' in header.lower():
            image_mime = 'image/png'
        elif 'jpeg' in header.lower() or 'jpg' in header.lower():
            image_mime = 'image/jpeg'
        elif 'webp' in header.lower():
            image_mime = 'image/webp'

    gemini_key = get_gemini_key()
    
    # Opción 1: google.genai directo (preferida en producción Railway)
    if gemini_key and GOOGLE_GENAI_AVAILABLE:
        try:
            return await _analyze_with_google_genai(
                image_base64, prompt, model, image_mime, gemini_key
            )
        except Exception as e:
            logger.error(f"google.genai falló: {e}", exc_info=True)
            # Continuar al fallback si hay emergent disponible
            if not (get_emergent_key() and EMERGENT_AVAILABLE):
                raise
    
    # Opción 2: emergentintegrations (entorno Emergent)
    emergent_key = get_emergent_key()
    if emergent_key and EMERGENT_AVAILABLE:
        return await _analyze_with_emergent(
            image_base64, prompt, session_id, model, emergent_key
        )
    
    raise RuntimeError(
        "Vision IA no disponible. Configura GEMINI_API_KEY en las variables de entorno. "
        "Obtén una gratis en https://aistudio.google.com/apikey"
    )


async def _analyze_with_google_genai(
    image_base64: str,
    prompt: str,
    model: str,
    image_mime: str,
    api_key: str,
) -> str:
    """Implementación con SDK oficial google-genai."""
    client = google_genai.Client(api_key=api_key)
    
    image_bytes = base64.b64decode(image_base64)
    
    # Mapear nombres de modelo Emergent → Google
    model_map = {
        "gemini-2.5-flash": "gemini-2.5-flash",
        "gemini-2.5-pro": "gemini-2.5-pro",
        "gemini-2.0-flash": "gemini-2.0-flash",
        "gemini-1.5-flash": "gemini-1.5-flash",
        "gemini-1.5-pro": "gemini-1.5-pro",
    }
    google_model = model_map.get(model, "gemini-2.5-flash")
    
    response = client.models.generate_content(
        model=google_model,
        contents=[
            google_genai_types.Part.from_bytes(
                data=image_bytes,
                mime_type=image_mime,
            ),
            prompt,
        ],
    )
    
    return response.text or ""


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
        model_map = {
            "gemini-2.5-flash": "gemini-2.5-flash",
            "gemini-2.5-pro": "gemini-2.5-pro",
            "gemini-2.0-flash": "gemini-2.0-flash",
        }
        google_model = model_map.get(model, "gemini-2.5-flash")
        
        contents = f"{system_message}\n\n{prompt}" if system_message else prompt
        response = client.models.generate_content(
            model=google_model,
            contents=contents,
        )
        return response.text or ""
    
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
