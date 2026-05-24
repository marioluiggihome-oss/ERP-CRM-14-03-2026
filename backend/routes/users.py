"""
Routes for User Management
Extracted from server.py for better maintainability
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
import logging
import uuid
import os
import bcrypt

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])
security = HTTPBearer()

# Database connection
MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME", "luiggi_home")
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]


# Pydantic models
class UserCreate(BaseModel):
    username: str
    password: str
    clientName: str = ""
    commercialDiscount: float = 0
    isAdmin: bool = False
    isRepresentative: bool = False
    isResponsableDelegacion: bool = False
    isTienda: bool = False
    isDirectorFabrica: bool = False
    canSeeCost: bool = False
    canAccessCRM: bool = False
    canUseAIAnalysis: bool = False
    allowedModules: List[str] = []
    provinciaCode: Optional[str] = None
    accessExpirationDate: Optional[str] = None


class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    clientName: Optional[str] = None
    commercialDiscount: Optional[float] = None
    isAdmin: Optional[bool] = None
    isRepresentative: Optional[bool] = None
    isResponsableDelegacion: Optional[bool] = None
    isTienda: Optional[bool] = None
    isDirectorFabrica: Optional[bool] = None
    canSeeCost: Optional[bool] = None
    canAccessCRM: Optional[bool] = None
    canUseAIAnalysis: Optional[bool] = None
    allowedModules: Optional[List[str]] = None
    provinciaCode: Optional[str] = None
    accessExpirationDate: Optional[str] = None
    isActive: Optional[bool] = None


class UserResponse(BaseModel):
    id: str
    username: str
    clientName: str = ""
    commercialDiscount: float = 0
    isAdmin: bool = False
    isRepresentative: bool = False
    isResponsableDelegacion: bool = False
    isTienda: bool = False
    isDirectorFabrica: bool = False
    canSeeCost: bool = False
    canAccessCRM: bool = False
    canUseAIAnalysis: bool = False
    allowedModules: List[str] = []
    provinciaCode: Optional[str] = None
    accessExpirationDate: Optional[str] = None
    isActive: bool = True

    class Config:
        extra = "allow"


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def user_to_response(user_data: dict) -> dict:
    """Convert user dict to response (remove password)"""
    response = {k: v for k, v in user_data.items() if k != "password"}
    return response

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token and return current user"""
    from routes.auth import verify_token
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    return payload


@router.get("")
async def get_users(current_user: dict = Depends(get_current_user)):
    """Obtener todos los usuarios (sin passwords)"""
    users = await db.users.find({}, {"_id": 0, "password": 0}).to_list(1000)
    return users


@router.get("/{user_id}")
async def get_user(user_id: str, current_user: dict = Depends(get_current_user)):
    """Obtener un usuario por ID (sin password)"""
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


@router.post("", response_model=UserResponse)
async def create_user(user: UserCreate, current_user: dict = Depends(get_current_user)):
    """Crear un nuevo usuario con password hasheado"""
    # Check if username exists (case insensitive)
    existing = await db.users.find_one({"username": {"$regex": f"^{user.username}$", "$options": "i"}})
    if existing:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya existe")
    
    user_data = user.model_dump()
    user_data["id"] = f"user-{uuid.uuid4().hex[:8]}"
    user_data["username"] = user_data["username"]  # Keep original case for email-style usernames
    user_data["password"] = hash_password(user_data["password"])
    user_data["isActive"] = True
    
    await db.users.insert_one(user_data)
    
    logger.info(f"User created: {user_data['username']}")
    
    return user_to_response(user_data)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user: UserUpdate, current_user: dict = Depends(get_current_user)):
    """Actualizar un usuario"""
    existing = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    update_data = {k: v for k, v in user.model_dump().items() if v is not None}
    
    # Hash password if provided
    if "password" in update_data and update_data["password"]:
        update_data["password"] = hash_password(update_data["password"])
        logger.info(f"Password changed for user: {user_id}")
    
    if update_data:
        await db.users.update_one({"id": user_id}, {"$set": update_data})
    
    logger.info(f"User updated: {user_id}, fields: {list(update_data.keys())}")
    
    updated = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
    return updated


@router.delete("/{user_id}")
async def delete_user(user_id: str, current_user: dict = Depends(get_current_user)):
    """Eliminar un usuario"""
    if user_id == "admin":
        raise HTTPException(status_code=400, detail="No se puede eliminar el administrador principal")
    
    # Get user info before deletion
    user_to_delete = await db.users.find_one({"id": user_id}, {"_id": 0, "username": 1})
    
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    logger.info(f"User deleted: {user_to_delete.get('username') if user_to_delete else user_id}")
    
    return {"message": "Usuario eliminado"}
