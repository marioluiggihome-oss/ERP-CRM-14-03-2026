"""
Configuración centralizada para el backend de LUIGGI HOME
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB Configuration
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'test_database')

# Inicializar cliente MongoDB.
# serverSelectionTimeoutMS=5000: si el cluster tarda más de 5 s en dar conexión,
# la operación falla con un error claro en lugar de quedarse colgada hasta que
# la pasarela de Railway corta la petición con un "Failed to fetch" opaco.
# connectTimeoutMS=10000: tiempo máximo para abrir el socket TCP.
# maxPoolSize=20: limita las conexiones concurrentes para no saturar el cluster.
client = AsyncIOMotorClient(
    MONGO_URL,
    serverSelectionTimeoutMS=5000,
    connectTimeoutMS=10000,
    maxPoolSize=20,
)
db = client[DB_NAME]

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
