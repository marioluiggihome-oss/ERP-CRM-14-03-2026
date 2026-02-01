"""
Project models
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict
from datetime import datetime, timezone
import uuid


class BudgetItemModel(BaseModel):
    """Budget item model"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: f"item-{uuid.uuid4().hex[:8]}")
    productId: str
    productCode: str
    productName: str
    quantity: int = 1
    customWidth: Optional[float] = None
    customHeight: Optional[float] = None
    customDepth: Optional[float] = None
    unitPoints: float = 0
    totalPoints: float = 0
    unitPrice: float = 0
    totalPrice: float = 0
    module: str = "montada"


class ProjectModel(BaseModel):
    """Project/Budget model"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: f"proj-{uuid.uuid4().hex[:8]}")
    userId: str
    budgetNumber: str
    customerName: str = ""
    customerAddress: str = ""
    internalReference: str = ""
    itemsMontada: List[Dict] = []
    itemsDespiece: List[Dict] = []
    doorColorLow: str = ""
    doorColorHigh: str = ""
    doorColorColumns: str = ""
    sideColor: str = ""
    selectedCarcassMaterialId: Optional[str] = None
    totalPvp: float = 0.0
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "draft"


class ProjectCreate(BaseModel):
    """Project creation model"""
    budgetNumber: str
    customerName: str = ""
    customerAddress: str = ""
    internalReference: str = ""
    itemsMontada: List[Dict] = []
    itemsDespiece: List[Dict] = []
    doorColorLow: str = ""
    doorColorHigh: str = ""
    doorColorColumns: str = ""
    sideColor: str = ""
    selectedCarcassMaterialId: Optional[str] = None
    totalPvp: float = 0.0
    status: str = "draft"


class ProjectUpdate(BaseModel):
    """Project update model"""
    budgetNumber: Optional[str] = None
    customerName: Optional[str] = None
    customerAddress: Optional[str] = None
    internalReference: Optional[str] = None
    itemsMontada: Optional[List[Dict]] = None
    itemsDespiece: Optional[List[Dict]] = None
    doorColorLow: Optional[str] = None
    doorColorHigh: Optional[str] = None
    doorColorColumns: Optional[str] = None
    sideColor: Optional[str] = None
    selectedCarcassMaterialId: Optional[str] = None
    totalPvp: Optional[float] = None
    status: Optional[str] = None


class SettingsModel(BaseModel):
    """Global settings model"""
    model_config = ConfigDict(extra="ignore")
    id: str = "global-settings"
    pointValueMontada: float = 1.0
    pointValueDespiece: float = 0.88
    specialIncrementWidth: float = 45
    specialIncrementHeight: float = 45
    specialIncrementDepth: float = 45
    brandColor: str = "#ea580c"
    logo: Optional[str] = None


class SettingsUpdate(BaseModel):
    """Settings update model"""
    pointValueMontada: Optional[float] = None
    pointValueDespiece: Optional[float] = None
    specialIncrementWidth: Optional[float] = None
    specialIncrementHeight: Optional[float] = None
    specialIncrementDepth: Optional[float] = None
    brandColor: Optional[str] = None
    logo: Optional[str] = None
