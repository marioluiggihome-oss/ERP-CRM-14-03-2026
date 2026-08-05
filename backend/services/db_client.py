# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
Cliente MongoDB singleton compartido para todo el backend.

ANTES: cada módulo (routes/*.py, services/*.py) creaba su propio
AsyncIOMotorClient, lo que resultaba en ~43 pools de conexión abiertos
simultáneamente (~40-285 conexiones reales en MongoDB Atlas).

AHORA: un único cliente con un único pool. Todos los módulos importan
`get_db()` o `get_collection()` de aquí y comparten el mismo pool.

Resultado: ~5-10 conexiones reales en Atlas en lugar de ~40.

Uso:
    from services.db_client import get_db, get_collection

    db = get_db()
    col = get_collection("renders_galeria")
    # o directamente:
    col = db["renders_galeria"]
"""
import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

_MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
_DB_NAME = os.environ.get("DB_NAME", "luiggi_home")

# Un único cliente para todo el proceso. Motor es thread-safe y async-safe:
# es seguro compartirlo entre todos los módulos y coroutines.
#
# maxPoolSize=100: suficiente para el tráfico del ERP con una sola réplica.
# serverSelectionTimeoutMS=5000: falla rápido si el cluster no responde.
# connectTimeoutMS=10000: tiempo máximo para abrir el socket TCP.
# minPoolSize=2: mantiene 2 conexiones siempre abiertas para evitar
#   la latencia de apertura en la primera petición tras inactividad.
_client: AsyncIOMotorClient = AsyncIOMotorClient(
    _MONGO_URL,
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=10000,
    maxPoolSize=100,
    minPoolSize=2,
)

_db: AsyncIOMotorDatabase = _client[_DB_NAME]


def get_client() -> AsyncIOMotorClient:
    """Devuelve el cliente MongoDB compartido."""
    return _client


def get_db() -> AsyncIOMotorDatabase:
    """Devuelve la base de datos compartida."""
    return _db


def get_collection(name: str):
    """Devuelve una colección de la base de datos compartida."""
    return _db[name]
