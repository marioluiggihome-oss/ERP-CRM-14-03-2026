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
import re
import bcrypt

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])
security = HTTPBearer(auto_error=False)  # NO exigir token (acepta sin)

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
    discountMontada: float = 0
    discountDespiece: float = 0
    discountDesmontada: float = 0
    isAdmin: bool = False
    isRepresentative: bool = False
    isResponsableDelegacion: bool = False
    isTienda: bool = False
    isDirectorFabrica: bool = False
    canSeeCost: bool = False
    canAccessCRM: bool = False
    canUseAIAnalysis: bool = False
    canUseKitchenDesigner: bool = False
    allowedModules: List[str] = []
    provinciaCode: Optional[str] = None
    accessExpirationDate: Optional[str] = None

    class Config:
        extra = "allow"


class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    clientName: Optional[str] = None
    commercialDiscount: Optional[float] = None
    discountMontada: Optional[float] = None
    discountDespiece: Optional[float] = None
    discountDesmontada: Optional[float] = None
    isAdmin: Optional[bool] = None
    isRepresentative: Optional[bool] = None
    isResponsableDelegacion: Optional[bool] = None
    isTienda: Optional[bool] = None
    isDirectorFabrica: Optional[bool] = None
    canSeeCost: Optional[bool] = None
    canAccessCRM: Optional[bool] = None
    canUseAIAnalysis: Optional[bool] = None
    canUseKitchenDesigner: Optional[bool] = None
    allowedModules: Optional[List[str]] = None
    provinciaCode: Optional[str] = None
    accessExpirationDate: Optional[str] = None
    isActive: Optional[bool] = None

    class Config:
        extra = "allow"


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
    canUseKitchenDesigner: bool = False
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
    """Convert user dict to response (remove password and Mongo _id)"""
    response = {k: v for k, v in user_data.items() if k not in ("password", "_id")}
    return response

# Authentication dependency
from services.jwt_service import get_current_user as _get_current_user, ADMIN_ROLE_FLAGS


def _is_user_manager(user: dict) -> bool:
    """True si el usuario puede gestionar usuarios (rol elevado o permiso explícito)."""
    if not user or user.get("_compat_mode"):
        return False
    if any(user.get(f) for f in ADMIN_ROLE_FLAGS):
        return True
    return bool(user.get("canManageUsers") or user.get("canAuthorizePermissions"))


async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """JWT opcional: para GET (lectura). Si hay token lo valida, si no devuelve dict compat."""
    if not credentials:
        return {"_compat_mode": True}
    user = await _get_current_user(credentials)
    if not user:
        return {"_compat_mode": True}
    return user


async def require_authenticated_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """JWT obligatorio para escrituras (POST/PUT/DELETE). Lanza 401 si no hay token válido."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Autenticación requerida")
    user = await _get_current_user(credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    return user


async def require_user_manager(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """Gestión de usuarios: exige token válido y rol/permiso de administración."""
    user = await require_authenticated_user(credentials)
    if not _is_user_manager(user):
        raise HTTPException(status_code=403, detail="Se requiere rol de administrador para gestionar usuarios")
    return user


# Campos sensibles que se ocultan si no hay token JWT (modo compat con frontend viejo)
SENSITIVE_USER_FIELDS = {
    "linkedClientId", "accessExpirationDate", "commercialDiscount",
    "discountMontada", "discountDespiece", "discountDesmontada", "allowedCatalogIds",
}


def filter_sensitive_user_fields(user_data: dict) -> dict:
    """Quita campos sensibles del usuario antes de devolverlos sin auth."""
    return {k: v for k, v in user_data.items() if k not in SENSITIVE_USER_FIELDS}


@router.get("")
async def get_users(current_user: dict = Depends(get_current_user)):
    """Obtener todos los usuarios (sin passwords). Si no hay JWT, oculta campos sensibles."""
    users = await db.users.find({}, {"_id": 0, "password": 0}).to_list(1000)
    if not _is_user_manager(current_user):
        users = [filter_sensitive_user_fields(u) for u in users]
    return users


@router.get("/{user_id}")
async def get_user(user_id: str, current_user: dict = Depends(get_current_user)):
    """Obtener un usuario por ID (sin password). Si no hay JWT, oculta campos sensibles."""
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if not _is_user_manager(current_user):
        user = filter_sensitive_user_fields(user)
    return user


@router.post("", response_model=UserResponse)
async def create_user(user: UserCreate, current_user: dict = Depends(require_user_manager)):
    """Crear un nuevo usuario con password hasheado.

    SEGURIDAD: Sin JWT, no se pueden crear usuarios con roles elevados (Admin, Gerente, etc.)
    ni permisos peligrosos (canManageUsers, canAuthorizePermissions, etc.)."""
    # Check if username exists (case insensitive)
    existing = await db.users.find_one({"username": {"$regex": f"^{re.escape(user.username)}$", "$options": "i"}})
    if existing:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya existe")

    user_data = user.model_dump()

    # SEGURIDAD: Si no hay JWT (modo compat), forzar a usuario sin privilegios elevados
    if current_user.get("_compat_mode"):
        DANGEROUS_FIELDS = {
            "isAdmin", "isPrimaryAdmin", "isGerente", "isDirectorComercial",
            "isResponsableDelegacion", "isDirectorFabrica",
            "canManageUsers", "canAuthorizePermissions",
            "canChangeLogo", "canManageSettings",
        }
        for f in DANGEROUS_FIELDS:
            if user_data.get(f):
                user_data[f] = False
                logger.warning(f"Compat mode: forced {f}=False at user create for '{user.username}'")

    user_data["id"] = f"user-{uuid.uuid4().hex[:8]}"
    user_data["username"] = user_data["username"]  # Keep original case for email-style usernames
    user_data["password"] = hash_password(user_data["password"])
    user_data["isActive"] = True
    
    await db.users.insert_one(user_data)
    
    logger.info(f"User created: {user_data['username']} (compat={current_user.get('_compat_mode', False)})")
    
    return user_to_response(user_data)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user: UserUpdate, current_user: dict = Depends(require_user_manager)):
    """Actualizar un usuario.

    SEGURIDAD: Sin JWT, no se pueden elevar permisos del usuario editado ni cambiar
    el usuario admin principal."""
    existing = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # SEGURIDAD: sin JWT no se puede modificar el admin principal
    if current_user.get("_compat_mode") and user_id == "admin":
        raise HTTPException(status_code=403, detail="Modificar admin principal requiere autenticación")

    update_data = {k: v for k, v in user.model_dump().items() if v is not None}

    # SEGURIDAD: sin JWT, bloquear elevación de permisos
    if current_user.get("_compat_mode"):
        DANGEROUS_FIELDS = {
            "isAdmin", "isPrimaryAdmin", "isGerente", "isDirectorComercial",
            "isResponsableDelegacion", "isDirectorFabrica",
            "canManageUsers", "canAuthorizePermissions",
        }
        for f in DANGEROUS_FIELDS:
            if f in update_data and update_data[f] and not existing.get(f):
                # Intento de elevar privilegios → bloqueado
                update_data.pop(f, None)
                logger.warning(f"Compat mode: blocked privilege escalation {f}=True on user '{user_id}'")
    
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
async def delete_user(user_id: str, current_user: dict = Depends(require_user_manager)):
    """Eliminar un usuario.

    SEGURIDAD: Sin JWT, no se puede borrar el admin principal ni otros admins."""
    if user_id == "admin":
        raise HTTPException(status_code=400, detail="No se puede eliminar el administrador principal")

    # Get user info before deletion
    user_to_delete = await db.users.find_one({"id": user_id}, {"_id": 0, "username": 1, "isAdmin": 1, "isGerente": 1})

    # SEGURIDAD: sin JWT no se puede borrar usuarios con rol admin/gerente
    if current_user.get("_compat_mode") and user_to_delete:
        if user_to_delete.get("isAdmin") or user_to_delete.get("isGerente"):
            raise HTTPException(status_code=403, detail="Eliminar admin/gerente requiere autenticación")
    
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    logger.info(f"User deleted: {user_to_delete.get('username') if user_to_delete else user_id}")
    
    return {"message": "Usuario eliminado"}
