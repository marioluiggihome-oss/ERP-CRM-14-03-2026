"""
Routes package for LUIGGI HOME backend
"""
from .ia_lab import router as ia_lab_router
from .auth import router as auth_router
from .products import router as products_router
from .clients import router as clients_router
from .projects import router as projects_router
from .crm import router as crm_router

__all__ = [
    'ia_lab_router',
    'auth_router',
    'products_router',
    'clients_router',
    'projects_router',
    'crm_router'
]
