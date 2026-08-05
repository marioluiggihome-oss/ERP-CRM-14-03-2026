# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
Database configuration and connection management.
Ahora delega en el singleton de services/db_client.py para evitar
crear un cliente MongoDB adicional.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection — usa el singleton compartido
from services.db_client import get_db as _get_db, get_client as _get_client

db = _get_db()
client = _get_client()


async def get_database():
    """Get database instance"""
    return _get_db()


async def close_database():
    """Close database connection (no-op: el singleton gestiona el ciclo de vida)"""
    pass
