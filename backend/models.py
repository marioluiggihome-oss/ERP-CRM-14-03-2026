"""
Modelos Pydantic para validación de entrada en endpoints críticos.
Reemplaza el uso de dict genéricos con esquemas fuertemente tipados.
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============================================
# AUTH MODELS
# ============================================

class LoginRequest(BaseModel):
    """Modelo para solicitud de login"""
    username: str = Field(..., min_length=1, max_length=255, description="Nombre de usuario")
    password: str = Field(..., min_length=1, max_length=255, description="Contraseña")

    @validator('username')
    def username_alphanumeric(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('El nombre de usuario solo puede contener letras, números, guiones y guiones bajos')
        return v


class RefreshTokenRequest(BaseModel):
    """Modelo para solicitud de refresco de token"""
    refresh_token: str = Field(..., min_length=1, description="Token de refresco")


# ============================================
# ORDER MODELS
# ============================================

class OrderItemRequest(BaseModel):
    """Modelo para un artículo en un pedido"""
    name: str = Field(..., min_length=1, max_length=255, description="Nombre del artículo")
    productName: Optional[str] = Field(None, max_length=255)
    code: Optional[str] = Field(None, max_length=100)
    productCode: Optional[str] = Field(None, max_length=100)
    quantity: int = Field(default=1, ge=1, le=10000, description="Cantidad")
    price: float = Field(default=0, ge=0, description="Precio unitario")
    totalPrice: Optional[float] = Field(None, ge=0)
    width: Optional[float] = Field(None, ge=0)
    customWidth: Optional[float] = Field(None, ge=0)
    height: Optional[float] = Field(None, ge=0)
    customHeight: Optional[float] = Field(None, ge=0)
    depth: Optional[float] = Field(None, ge=0)
    customDepth: Optional[float] = Field(None, ge=0)


class OrderConfirmRequest(BaseModel):
    """Modelo para confirmación de pedido (sin archivos adjuntos)"""
    budgetNumber: str = Field(..., min_length=1, max_length=100, description="Número de presupuesto")
    customerName: str = Field(..., min_length=1, max_length=255, description="Nombre del cliente")
    customerAddress: Optional[str] = Field(None, max_length=500, description="Dirección del cliente")
    totalAmount: float = Field(..., ge=0, description="Monto total")
    email: EmailStr = Field(..., description="Email del cliente")
    notes: Optional[str] = Field(None, max_length=2000, description="Notas adicionales")
    items: List[OrderItemRequest] = Field(default_factory=list, description="Artículos del pedido")
    doorColorLow: Optional[str] = Field(None, max_length=100)
    doorColorHigh: Optional[str] = Field(None, max_length=100)
    doorColorColumns: Optional[str] = Field(None, max_length=100)
    sideColor: Optional[str] = Field(None, max_length=100)
    carcassColor: Optional[str] = Field(None, max_length=100)
    globalFinish: Optional[str] = Field(None, max_length=100)
    distributorName: Optional[str] = Field(None, max_length=255)
    userId: Optional[str] = Field(None, max_length=100)
    projectReference: Optional[str] = Field(None, max_length=100)

    @validator('email')
    def email_lowercase(cls, v):
        return v.lower()

    @validator('totalAmount')
    def validate_total_amount(cls, v):
        if v < 0:
            raise ValueError('El monto total no puede ser negativo')
        return round(v, 2)


# ============================================
# USER MODELS
# ============================================

class UserCreateRequest(BaseModel):
    """Modelo para creación de usuario"""
    username: str = Field(..., min_length=1, max_length=255, description="Nombre de usuario")
    email: EmailStr = Field(..., description="Email del usuario")
    password: str = Field(..., min_length=8, max_length=255, description="Contraseña (mínimo 8 caracteres)")
    firstName: Optional[str] = Field(None, max_length=255)
    lastName: Optional[str] = Field(None, max_length=255)
    isAdmin: bool = Field(default=False)
    isActive: bool = Field(default=True)

    @validator('password')
    def password_strength(cls, v):
        """Validar fortaleza de contraseña"""
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        if not any(c.isupper() for c in v):
            raise ValueError('La contraseña debe contener al menos una mayúscula')
        if not any(c.isdigit() for c in v):
            raise ValueError('La contraseña debe contener al menos un dígito')
        return v


# ============================================
# CLIENT MODELS
# ============================================

class ClientCreateRequest(BaseModel):
    """Modelo para creación de cliente"""
    name: str = Field(..., min_length=1, max_length=255, description="Nombre del cliente")
    email: Optional[EmailStr] = Field(None, description="Email del cliente")
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    taxId: Optional[str] = Field(None, max_length=50, description="ID fiscal/NIF")
    activo: bool = Field(default=True)

    @validator('email')
    def email_lowercase(cls, v):
        if v:
            return v.lower()
        return v


# ============================================
# EXPEDIENT MODELS
# ============================================

class ExpedientNextRequest(BaseModel):
    """Modelo para solicitud de siguiente número de expediente"""
    client_code: Optional[str] = Field(None, max_length=50, description="Código de cliente (opcional)")


# ============================================
# ERROR MODELS
# ============================================

class ErrorResponse(BaseModel):
    """Modelo estándar para respuestas de error"""
    success: bool = False
    error: str = Field(..., description="Mensaje de error")
    detail: Optional[str] = Field(None, description="Detalle adicional del error")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SuccessResponse(BaseModel):
    """Modelo estándar para respuestas exitosas"""
    success: bool = True
    message: Optional[str] = Field(None, description="Mensaje de éxito")
    data: Optional[Dict[str, Any]] = Field(None, description="Datos de la respuesta")
