"""
Routes for Global Settings
Extracted from server.py for better maintainability
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import logging
import os

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["settings"])

# Database connection
MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME", "luiggi_home")
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]


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


@router.get("", response_model=SettingsModel)
async def get_settings():
    """Obtener configuración global"""
    settings = await db.settings.find_one({"id": "global-settings"}, {"_id": 0})
    if not settings:
        # Return defaults
        return SettingsModel()
    return settings


@router.put("", response_model=SettingsModel)
async def update_settings(settings: SettingsUpdate):
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
        return SettingsModel()
    return updated


@router.get("/logo")
async def get_logo():
    """Obtener solo el logo de la empresa"""
    settings = await db.settings.find_one({"id": "global-settings"}, {"_id": 0, "logo": 1})
    return {"logo": settings.get("logo") if settings else None}


@router.put("/logo")
async def update_logo(logo: str):
    """Actualizar solo el logo de la empresa"""
    await db.settings.update_one(
        {"id": "global-settings"},
        {"$set": {"logo": logo}},
        upsert=True
    )
    return {"success": True, "message": "Logo actualizado"}
