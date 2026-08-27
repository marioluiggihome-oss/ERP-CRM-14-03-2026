# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
LuiggiAI Engine
===============
Motor de inteligencia artificial white-label para el ERP.
Proporciona capacidades de render 3D, análisis de documentos,
y procesamiento inteligente bajo la marca LuiggiAI.
"""

from .config import get_ai_config, AIConfig
from .engine_core import LuiggiAICore, get_engine
from .render_3d import Render3DService, get_render_service

__all__ = [
    "get_ai_config",
    "AIConfig",
    "LuiggiAICore",
    "get_engine",
    "Render3DService",
    "get_render_service",
]
