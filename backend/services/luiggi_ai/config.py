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
    brand_name: str = "LuiggiAI"
    brand_version: str = "1.0.0"
    brand_description: str = "Motor de Inteligencia Artificial para diseño y gestión"

    # ─── API del proveedor subyacente (oculto) ─────────────────────────────
    provider_api_key: str = field(default_factory=lambda: os.environ.get("MANUS_API_KEY", ""))
    provider_base_url: str = "https://api.manus.im/v2"

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

    # ─── Palabras/frases prohibidas en respuestas (sanitización) ──────────
    sanitize_terms: List[str] = field(default_factory=lambda: [
        "manus",
        "Manus",
        "MANUS",
        "manus.im",
        "powered by manus",
        "created by manus",
        "manus team",
        "manus ai",
    ])

    # ─── Reemplazos en respuestas ─────────────────────────────────────────
    sanitize_replacements: Dict[str, str] = field(default_factory=lambda: {
        "manus": "LuiggiAI",
        "Manus": "LuiggiAI",
        "MANUS": "LUIGGIAI",
        "manus.im": "luiggihome.es",
        "powered by manus": "powered by LuiggiAI",
        "created by manus": "developed by LuiggiAI",
        "manus team": "LuiggiAI team",
        "manus ai": "LuiggiAI",
    })

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
