"""
LUIGGI HOME - Backend API
Punto de entrada principal refactorizado
"""
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pathlib import Path
import os
import logging

# Cargar variables de entorno
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title="LUIGGI HOME API",
    description="Backend API para el sistema ERP de cocinas LUIGGI HOME",
    version="2.0.0"
)

# Router principal con prefijo /api
api_router = APIRouter(prefix="/api")

# Importar routers modulares
from routes.ia_lab import router as ia_lab_router

# Registrar routers
api_router.include_router(ia_lab_router)

# Incluir el router principal en la app
app.include_router(api_router)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@api_router.get("/")
async def root():
    return {"message": "LUIGGI HOME API v2.0"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0"}
