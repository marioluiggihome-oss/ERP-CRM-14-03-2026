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

# Inicializar cliente MongoDB
client = AsyncIOMotorClient(MONGO_URL)
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
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-super-secret-jwt-key-change-in-production')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24
REFRESH_TOKEN_EXPIRATION_DAYS = 7
