"""
User models
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid


class UserModelInternal(BaseModel):
    """Internal user model with password"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: f"user-{uuid.uuid4().hex[:8]}")
    username: str
    password: str
    clientName: str
    linkedClientId: Optional[str] = None
    isActive: bool = True
    isAdmin: bool = False  # Director Comercial
    isResponsableDelegacion: bool = False
    isRepresentative: bool = False  # Comercial/Representante
    isPrescriptor: bool = False  # Colaborador comercial
    isTienda: bool = False  # Tienda/Punto de Venta
    linkedRepresentativeId: Optional[str] = None
    allowedModules: List[str] = ["montada"]
    allowedCatalogIds: List[str] = []
    commercialDiscount: float = 0
    canSeeCost: bool = False
    canSeeRetail: bool = True
    canUseAIAnalysis: bool = False
    canUseKitchenDesigner: bool = False
    canManageArticles: bool = False
    canViewTechnicalDespiece: bool = False
    canAccessCRM: bool = False
    canUseDigitalizador: bool = False
    canAccessArmarios: bool = False
    canAuthorizePermissions: bool = False
    useCustomBranding: bool = False
    canChangeLogo: bool = False


class UserResponse(BaseModel):
    """User response model without password"""
    model_config = ConfigDict(extra="ignore")
    id: str
    username: str
    clientName: str
    linkedClientId: Optional[str] = None
    isActive: bool = True
    isAdmin: bool = False
    isResponsableDelegacion: bool = False
    isRepresentative: bool = False
    isPrescriptor: bool = False
    isTienda: bool = False
    linkedRepresentativeId: Optional[str] = None
    allowedModules: List[str] = ["montada"]
    allowedCatalogIds: List[str] = []
    commercialDiscount: float = 0
    canSeeCost: bool = False
    canSeeRetail: bool = True
    canUseAIAnalysis: bool = False
    canUseKitchenDesigner: bool = False
    canManageArticles: bool = False
    canViewTechnicalDespiece: bool = False
    canAccessCRM: bool = False
    canUseDigitalizador: bool = False
    canAccessArmarios: bool = False
    canAuthorizePermissions: bool = False
    useCustomBranding: bool = False
    canChangeLogo: bool = False


class UserCreate(BaseModel):
    """User creation model"""
    username: str
    password: str
    clientName: str
    linkedClientId: Optional[str] = None
    isActive: bool = True
    isAdmin: bool = False
    isResponsableDelegacion: bool = False
    isRepresentative: bool = False
    isPrescriptor: bool = False
    isTienda: bool = False
    linkedRepresentativeId: Optional[str] = None
    allowedModules: List[str] = ["montada"]
    allowedCatalogIds: List[str] = []
    commercialDiscount: float = 0
    canSeeCost: bool = False
    canSeeRetail: bool = True
    canUseAIAnalysis: bool = False
    canUseKitchenDesigner: bool = False
    canManageArticles: bool = False
    canViewTechnicalDespiece: bool = False
    canAccessCRM: bool = False
    canUseDigitalizador: bool = False
    canAccessArmarios: bool = False
    canAuthorizePermissions: bool = False
    useCustomBranding: bool = False
    canChangeLogo: bool = False


class UserUpdate(BaseModel):
    """User update model"""
    username: Optional[str] = None
    password: Optional[str] = None
    clientName: Optional[str] = None
    linkedClientId: Optional[str] = None
    isActive: Optional[bool] = None
    isAdmin: Optional[bool] = None
    isResponsableDelegacion: Optional[bool] = None
    isRepresentative: Optional[bool] = None
    isPrescriptor: Optional[bool] = None
    isTienda: Optional[bool] = None
    linkedRepresentativeId: Optional[str] = None
    allowedModules: Optional[List[str]] = None
    allowedCatalogIds: Optional[List[str]] = None
    commercialDiscount: Optional[float] = None
    canSeeCost: Optional[bool] = None
    canSeeRetail: Optional[bool] = None
    canUseAIAnalysis: Optional[bool] = None
    canUseKitchenDesigner: Optional[bool] = None
    canManageArticles: Optional[bool] = None
    canViewTechnicalDespiece: Optional[bool] = None
    canAccessCRM: Optional[bool] = None
    canUseDigitalizador: Optional[bool] = None
    canAccessArmarios: Optional[bool] = None
    canAuthorizePermissions: Optional[bool] = None
    useCustomBranding: Optional[bool] = None
    canChangeLogo: Optional[bool] = None


def user_to_response(user_doc: dict) -> dict:
    """Convert user document to response (excluding password)"""
    return {k: v for k, v in user_doc.items() if k != "password"}
