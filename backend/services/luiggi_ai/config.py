# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
LuiggiAI Engine - Configuración
================================
Configuración centralizada del motor de IA white-label.
Todos los nombres, marcas y referencias al proveedor subyacente
se gestionan aquí para mantener la abstracción.
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, List

logger = logging.getLogger("luiggi_ai")


@dataclass
class AIConfig:
    """Configuración del motor LuiggiAI."""

    # ─── Branding White-Label ──────────────────────────────────────────────
    # El nombre del motor viaja en CADA respuesta de la API (`engine`) y se veia
    # en pantalla. Neutro por defecto y ajustable por variable de entorno, para
    # que no salga el nombre de la casa ni en el navegador ni en un render
    # compartido con un cliente.
    brand_name: str = field(default_factory=lambda: os.environ.get("AI_BRAND_NAME", "Motor 3D"))
    brand_version: str = "1.0.0"
    brand_description: str = "Motor de Inteligencia Artificial para diseño y gestión"

    # ─── API del proveedor subyacente (oculto) ─────────────────────────────
    provider_api_key: str = field(default_factory=lambda: os.environ.get("MANUS_API_KEY", ""))
    provider_base_url: str = "https://api.manus.ai/v2"

    # Dominios del proveedor cuyos assets (imágenes/archivos) deben servirse
    # SIEMPRE a través del proxy interno para que el navegador del cliente no
    # vea nunca el origen real. Cualquier URL que apunte aquí se reescribe.
    provider_asset_hosts: List[str] = field(default_factory=lambda: [
        "manus.ai",
        "manus.im",
        "manus.computer",
        "manuscdn.com",
        "amazonaws.com",  # buckets del proveedor
        "googleapis.com",
        "storage.googleapis.com",
    ])

    # ─── Configuración de render 3D ───────────────────────────────────────
    render_enabled: bool = True
    render_default_style: str = "photorealistic"
    render_default_resolution: str = "1024x1024"
    render_max_per_day: int = 50

    # ─── Configuración de análisis de documentos ──────────────────────────
    document_ai_enabled: bool = True
    max_file_size_mb: int = 25

    # ─── Configuración de voz (Speech-to-Text) ────────────────────────────
    voice_enabled: bool = True
    voice_provider: str = "browser"  # "browser" (Web Speech API) o "whisper"
    whisper_api_key: str = field(default_factory=lambda: os.environ.get("OPENAI_API_KEY", ""))

    # ─── Rate Limiting específico del motor IA ─────────────────────────────
    max_requests_per_minute: int = 10
    max_concurrent_tasks: int = 3

    # ─── Reemplazos en respuestas (sanitización white-label) ──────────────
    # IMPORTANTE: la sanitización se aplica de forma INSENSIBLE A MAYÚSCULAS y
    # dando prioridad a las claves más largas (frase completa antes que palabra
    # suelta), por lo que el orden de este diccionario NO importa. Las URLs que
    # apunten al proveedor se reescriben aparte (proxy), no aquí.
    #
    # Cubre el proveedor de render (Manus) y los proveedores auxiliares de
    # visión/voz (Google Gemini, OpenAI/Whisper) por si algún mensaje de error
    # o respuesta se filtrara hacia el cliente.
    sanitize_replacements: Dict[str, str] = field(default_factory=lambda: {
        # Proveedor de render
        "powered by manus": "powered by LuiggiAI",
        "created by manus": "developed by LuiggiAI",
        "manus team": "LuiggiAI team",
        "manuscdn.com": "luiggihome.es",
        "manus.computer": "luiggihome.es",
        "manus.ai": "luiggihome.es",
        "manus.im": "luiggihome.es",
        "manus ai": "LuiggiAI",
        "manus": "LuiggiAI",
        # Proveedores de visión / voz
        "google generative ai": "LuiggiAI",
        "generativelanguage": "LuiggiAI",
        "googleapis.com": "luiggihome.es",
        "gemini": "LuiggiAI",
        "google ai": "LuiggiAI",
        "openai": "LuiggiAI",
        "whisper": "LuiggiAI Voice",
        "gpt-4": "LuiggiAI",
        "gpt-3": "LuiggiAI",
        "anthropic": "LuiggiAI",
        "claude": "LuiggiAI",
    })

    def provider_auth_headers(self) -> Dict[str, str]:
        """Cabeceras de autenticación de la API del proveedor.

        ÚNICO sitio donde se escribe el nombre de la cabecera. La API del
        proveedor NO usa `Authorization: Bearer`, sino una cabecera propia; con
        el esquema equivocado responde 401 aunque la clave sea correcta.

        Estaba copiado en cuatro sitios y dos lo tenían mal: el diagnóstico
        (daba 401 falsos y hacía creer que la clave estaba caducada) y el proxy
        de assets (las imágenes servidas desde el host de la API salían rotas).
        Se centraliza para que no vuelva a divergir.
        """
        return {"x-manus-api-key": self.provider_api_key}

    def validate(self) -> bool:
        """Valida que la configuración mínima esté presente."""
        if not self.provider_api_key:
            logger.warning(
                "LuiggiAI: MANUS_API_KEY no configurada. "
                "El motor funcionará en modo limitado (solo prompts locales)."
            )
            return False
        return True


# Singleton
_config: Optional[AIConfig] = None


def get_ai_config() -> AIConfig:
    """Obtiene la configuración del motor (singleton)."""
    global _config
    if _config is None:
        _config = AIConfig()
        _config.validate()
    return _config
