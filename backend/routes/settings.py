# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
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

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["settings"])
security = HTTPBearer(auto_error=False)  # JWT opcional (compat con frontend viejo)

# Database connection

# Authentication dependency
from services.jwt_service import get_current_user as _get_current_user, require_admin
from services.db_client import get_db as _get_db

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
    companyName: str = ""          # vacío: la marca la pone cada instalación
    companyAddress: str = ""
    companyPhone: str = ""
    companyEmail: str = ""
    companyNIF: str = ""
    logo: Optional[str] = None
    marcaBlanca: bool = False  # Modo marca blanca: logo neutro genérico en toda la app
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
    # La comision del montador ES esta mano de obra por mueble (CLAUDE.md,
    # regla 16). No tiene formula propia a proposito: dos numeros para lo mismo
    # acaban sin cuadrar. Son 17 € (master, 28/08) y es la cifra DE LA CASA: el
    # montador que tenga la suya propia cobra la suya (services/comisiones.py,
    # `mano_de_obra_de`).
    manoObraPorMueble: float = 17.0
    defaultEdgeBandingPriceMl: float = 1.77  # Precio canto €/ml (configurable, usado en despiece y presupuestador)
    
    # Email settings
    emailNotifications: bool = False
    emailSender: str = ""
    emailSenderName: str = ""      # vacío: sin membrete ajeno
    
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
    marcaBlanca: Optional[bool] = None
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
    defaultEdgeBandingPriceMl: Optional[float] = None
    emailNotifications: Optional[bool] = None
    emailSender: Optional[str] = None
    emailSenderName: Optional[str] = None
    sendgridApiKey: Optional[str] = None
    resendApiKey: Optional[str] = None
    backupRetentionDays: Optional[int] = None

    class Config:
        extra = "allow"


@router.get("")
async def get_settings(current_user: dict = Depends(get_current_user)):
    """Obtener configuración global"""
    settings = await _get_db().settings.find_one({"id": "global-settings"}, {"_id": 0})
    if not settings:
        return {}
    # No exponer secretos al frontend: solo indicar si están configurados.
    settings["sendgridConfigured"] = bool(settings.get("sendgridApiKey"))
    settings["resendConfigured"] = bool(settings.get("resendApiKey"))
    settings.pop("sendgridApiKey", None)
    settings.pop("resendApiKey", None)
    return settings


@router.put("")
async def update_settings(settings: SettingsUpdate, current_user: dict = Depends(require_admin)):
    """Actualizar configuración global"""
    update_data = {k: v for k, v in settings.model_dump().items() if v is not None}
    
    if update_data:
        await _get_db().settings.update_one(
            {"id": "global-settings"}, 
            {"$set": update_data},
            upsert=True
        )
    
    updated = await _get_db().settings.find_one({"id": "global-settings"}, {"_id": 0})
    if not updated:
        return {}
    # No reflejar secretos en la respuesta (igual que en GET)
    updated["sendgridConfigured"] = bool(updated.get("sendgridApiKey"))
    updated["resendConfigured"] = bool(updated.get("resendApiKey"))
    updated.pop("sendgridApiKey", None)
    updated.pop("resendApiKey", None)
    return updated


@router.get("/public-logo")
async def get_public_logo():
    """Logo corporativo GLOBAL para la pantalla de login (público, solo lectura).

    Devuelve únicamente el logo global (el que se muestra antes de iniciar
    sesión). No expone ningún otro ajuste sensible (email, claves, etc.).
    """
    settings = await _get_db().settings.find_one({"id": "global-settings"}, {"_id": 0, "logo": 1, "marcaBlanca": 1, "companyName": 1})
    settings = settings or {}
    return {
        "logo": settings.get("logo"),
        "marcaBlanca": bool(settings.get("marcaBlanca")),
        "companyName": settings.get("companyName") or "",
    }


@router.get("/logo")
async def get_logo(current_user: dict = Depends(get_current_user)):
    """Logo EFECTIVO del usuario: su logo propio si tiene marca personalizada
    (useCustomBranding) y ha subido uno; en caso contrario, el logo global."""
    uid = current_user.get("id") if current_user else None
    if uid:
        user = await _get_db().users.find_one({"id": uid}, {"_id": 0, "logo": 1, "useCustomBranding": 1})
        if user and user.get("useCustomBranding") and user.get("logo"):
            return {"logo": user["logo"], "scope": "user"}
    settings = await _get_db().settings.find_one({"id": "global-settings"}, {"_id": 0, "logo": 1})
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
    user = await _get_db().users.find_one({"id": uid}, {"_id": 0}) if uid else None
    is_admin = bool(current_user.get("isAdmin") or (user and user.get("isAdmin")))
    can_brand = bool(user and (user.get("canChangeLogo") or user.get("useCustomBranding")))

    if not (is_admin or can_brand):
        raise HTTPException(status_code=403, detail="No tienes permiso para cambiar el logo")

    if can_brand:
        # Logo propio del usuario (marca personalizada activada)
        await _get_db().users.update_one(
            {"id": uid}, {"$set": {"logo": logo, "useCustomBranding": True}}
        )
        return {"success": True, "scope": "user", "message": "Logo personal actualizado"}

    # Admin sin marca propia → logo global por defecto
    await _get_db().settings.update_one(
        {"id": "global-settings"}, {"$set": {"logo": logo}}, upsert=True
    )
    return {"success": True, "scope": "global", "message": "Logo global actualizado"}
