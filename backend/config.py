# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
Configuración centralizada para el backend de LUIGGI HOME.
El cliente MongoDB ahora usa el singleton de services/db_client.py para
evitar abrir pools adicionales. Las variables exportadas (db, client,
*_collection) se mantienen idénticas para compatibilidad con los módulos
que hacen `from config import db`.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB Configuration
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'test_database')

# Cliente y DB compartidos (singleton) — no se abre un pool adicional
from services.db_client import get_db as _get_db, get_client as _get_client
client = _get_client()
db = _get_db()

# Collections
users_collection = db['users']
products_collection = db['products']
projects_collection = db['projects']
clients_collection = db['clients']
materials_collection = db['materials']
settings_collection = db['settings']
orders_collection = db['orders']
status_checks_collection = db['status_checks']
counters_collection = db['counters']
backup_history_collection = db['backup_history']
distributor_requests_collection = db['distributor_requests']

# CRM Collections
contacts_collection = db['contacts']
opportunities_collection = db['opportunities']
calendar_events_collection = db['calendar_events']
activities_collection = db['activities']

# JWT Configuration
# JWT_SECRET es obligatorio (sin valor por defecto inseguro). Debe coincidir con el
# usado en services/jwt_service.py (misma variable de entorno).
JWT_SECRET = os.environ.get('JWT_SECRET')
if not JWT_SECRET:
    raise RuntimeError(
        "La variable de entorno JWT_SECRET es obligatoria. "
        "Configúrala con un valor largo y aleatorio (p. ej. `openssl rand -hex 32`)."
    )
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24
REFRESH_TOKEN_EXPIRATION_DAYS = 7
