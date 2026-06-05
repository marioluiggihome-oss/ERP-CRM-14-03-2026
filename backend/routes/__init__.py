"""
Routes package for LUIGGI HOME backend
"""
from .ia_lab import router as ia_lab_router
from .auth import router as auth_router
from .auth_advanced import router as auth_advanced_router
from .products import router as products_router
from .clients import router as clients_router
from .projects import router as projects_router
from .crm import router as crm_router
from .despiece_budgeter import router as despiece_budgeter_router
from .libraries import router as libraries_router
from .montajes import router as montajes_router
from .backup import router as backup_router
from .armarios import router as armarios_router
from .digitalizador import router as digitalizador_router
from .crm_module import router as crm_module_router
from .orders import router as orders_router
from .ai_engine import ai_engine_router

__all__ = [
    'ia_lab_router',
    'auth_router',
    'auth_advanced_router',
    'products_router',
    'clients_router',
    'projects_router',
    'crm_router',
    'despiece_budgeter_router',
    'libraries_router',
    'montajes_router',
    'backup_router',
    'armarios_router',
    'digitalizador_router',
    'crm_module_router',
    'orders_router',
    'ai_engine_router',
]
