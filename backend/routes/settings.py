"""
Routes for Global Settings
Extracted from server.py for better maintainability
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List
import logging
import os

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["settings"])
security = HTTPBearer(auto_error=False)  # JWT opcional (compat con frontend viejo)

# Database connection
MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME", "luiggi_home")
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Authentication dependency
from services.jwt_service import get_current_user as _get_current_user

async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """JWT opcional: si hay token lo valida, si no devuelve dict vacío (modo compatibilidad)."""
    if not credentials:
        return {"_compat_mode": True}
    user = await _get_current_user(credentials)
    if not user:
        return {"_compat_mode": True}
    return user


# Pydantic models
class SettingsModel(BaseModel):
    id: str = "global-settings"
    companyName: str = "LUIGGI HOME"
    companyAddress: str = ""
    companyPhone: str = ""
    companyEmail: str = ""
    companyNIF: str = ""
    logo: Optional[str] = None
    defaultIVA: float = 21.0
    defaultDiscount: float = 0.0
    currency: str = "EUR"
    defaultMeasureUnit: str = "cm"
    
    # Pricing configuration
    defaultZone: str = "Z1"
    defaultTariff: str = "T1"
    
    # Manufacturing defaults
    defaultCarcassMaterial: str = "Melamina Blanca 18mm"
    defaultBackMaterial: str = "Tablero 8mm"
    defaultGrosor: int = 18
    defaultBackThickness: int = 8
    
    # Email settings
    emailNotifications: bool = False
    emailSender: str = ""
    emailSenderName: str = "LUIGGI HOME"
    
    # Backup settings
    backupRetentionDays: int = 30

    class Config:
        extra = "allow"


class SettingsUpdate(BaseModel):
    companyName: Optional[str] = None
    companyAddress: Optional[str] = None
    companyPhone: Optional[str] = None
    companyEmail: Optional[str] = None
    companyNIF: Optional[str] = None
    logo: Optional[str] = None
    defaultIVA: Optional[float] = None
    defaultDiscount: Optional[float] = None
    currency: Optional[str] = None
    defaultMeasureUnit: Optional[str] = None
    defaultZone: Optional[str] = None
    defaultTariff: Optional[str] = None
    defaultCarcassMaterial: Optional[str] = None
    defaultBackMaterial: Optional[str] = None
    defaultGrosor: Optional[int] = None
    defaultBackThickness: Optional[int] = None
    emailNotifications: Optional[bool] = None
    emailSender: Optional[str] = None
    emailSenderName: Optional[str] = None
    backupRetentionDays: Optional[int] = None

    class Config:
        extra = "allow"


@router.get("")
async def get_settings(current_user: dict = Depends(get_current_user)):
    """Obtener configuración global"""
    settings = await db.settings.find_one({"id": "global-settings"}, {"_id": 0})
    if not settings:
        return {}
    return settings


@router.put("")
async def update_settings(settings: SettingsUpdate, current_user: dict = Depends(get_current_user)):
    """Actualizar configuración global"""
    update_data = {k: v for k, v in settings.model_dump().items() if v is not None}
    
    if update_data:
        await db.settings.update_one(
            {"id": "global-settings"}, 
            {"$set": update_data},
            upsert=True
        )
    
    updated = await db.settings.find_one({"id": "global-settings"}, {"_id": 0})
    if not updated:
        return {}
    return updated


@router.get("/logo")
async def get_logo(current_user: dict = Depends(get_current_user)):
    """Logo EFECTIVO del usuario: su logo propio si tiene marca personalizada
    (useCustomBranding) y ha subido uno; en caso contrario, el logo global."""
    uid = current_user.get("id") if current_user else None
    if uid:
        user = await db.users.find_one({"id": uid}, {"_id": 0, "logo": 1, "useCustomBranding": 1})
        if user and user.get("useCustomBranding") and user.get("logo"):
            return {"logo": user["logo"], "scope": "user"}
    settings = await db.settings.find_one({"id": "global-settings"}, {"_id": 0, "logo": 1})
    return {"logo": settings.get("logo") if settings else None, "scope": "global"}


@router.put("/logo")
async def update_logo(payload: dict, current_user: dict = Depends(get_current_user)):
    """Guardar logo.

    - Si el usuario tiene permiso de marca propia (canChangeLogo o
      useCustomBranding): se guarda en SU ficha → logo POR USUARIO, que saldrá
      en sus documentos.
    - Si es admin (sin marca propia): actualiza el logo GLOBAL (por defecto).
    """
    if not isinstance(payload, dict) or "logo" not in payload:
        raise HTTPException(status_code=400, detail="Falta el logo")
    logo = payload.get("logo") or ""  # "" = borrar el logo

    uid = current_user.get("id") if current_user else None
    user = await db.users.find_one({"id": uid}, {"_id": 0}) if uid else None
    is_admin = bool(current_user.get("isAdmin") or (user and user.get("isAdmin")))
    can_brand = bool(user and (user.get("canChangeLogo") or user.get("useCustomBranding")))

    if not (is_admin or can_brand):
        raise HTTPException(status_code=403, detail="No tienes permiso para cambiar el logo")

    if can_brand:
        # Logo propio del usuario (marca personalizada activada)
        await db.users.update_one(
            {"id": uid}, {"$set": {"logo": logo, "useCustomBranding": True}}
        )
        return {"success": True, "scope": "user", "message": "Logo personal actualizado"}

    # Admin sin marca propia → logo global por defecto
    await db.settings.update_one(
        {"id": "global-settings"}, {"$set": {"logo": logo}}, upsert=True
    )
    return {"success": True, "scope": "global", "message": "Logo global actualizado"}
