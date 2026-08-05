# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
Client models
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime, timezone
import uuid


# Client segments
CLIENT_SEGMENTS = [
    "PROMOTOR",
    "CONSTRUCTOR",
    "PROMOTOR-CONSTRUCTOR",
    "DECORADOR-INTERIORISTA",
    "ESTUDIO DE COCINA",
    "TIENDA DE MUEBLES",
    "TIENDA DE COCINA Y BAÑOS",
    "TIENDA DE ARMARIOS",
    "ARQUITECTO",
    "REFORMISTA",
    "USUARIO FINAL",
    "OTRO"
]


class ClientModel(BaseModel):
    """Client model (potential and active)"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: f"cli-{uuid.uuid4().hex[:8]}")
    tipo: str = "potencial"  # 'potencial' or 'activo'
    codigo: str = ""
    nombre: str
    cif: str = ""
    segmento: str = ""
    direccion: str = ""
    localidad: str = ""
    provincia: str = ""
    codigoPostal: str = ""
    telefono: str = ""
    email: str = ""
    descuento: float = 0
    activo: bool = True
    notas: str = ""
    origenCrmContactId: str = ""
    usuarioVinculadoId: str = ""
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    convertidoAt: Optional[datetime] = None


class ClientCreate(BaseModel):
    """Client creation model"""
    tipo: str = "potencial"
    codigo: str = ""
    nombre: str
    cif: str = ""
    segmento: str = ""
    direccion: str = ""
    localidad: str = ""
    provincia: str = ""
    codigoPostal: str = ""
    telefono: str = ""
    email: str = ""
    descuento: float = 0
    activo: bool = True
    notas: str = ""
    origenCrmContactId: str = ""
    usuarioVinculadoId: str = ""


class ClientUpdate(BaseModel):
    """Client update model"""
    tipo: Optional[str] = None
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    cif: Optional[str] = None
    segmento: Optional[str] = None
    direccion: Optional[str] = None
    localidad: Optional[str] = None
    provincia: Optional[str] = None
    codigoPostal: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    descuento: Optional[float] = None
    activo: Optional[bool] = None
    notas: Optional[str] = None
    origenCrmContactId: Optional[str] = None
    usuarioVinculadoId: Optional[str] = None
    convertidoAt: Optional[datetime] = None
