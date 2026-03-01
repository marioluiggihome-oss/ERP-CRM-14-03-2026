"""
Modelos Pydantic para LUIGGI HOME
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict
from datetime import datetime, timezone
import uuid


# ============================================
# STATUS CHECK MODELS
# ============================================

class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StatusCheckCreate(BaseModel):
    client_name: str


# ============================================
# USER MODELS
# ============================================

class UserModelInternal(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: f"user-{uuid.uuid4().hex[:8]}")
    username: str
    password: str
    clientName: str
    linkedClientId: Optional[str] = None
    isActive: bool = True
    isAdmin: bool = False
    isGerente: bool = False
    isResponsableDelegacion: bool = False
    isRepresentative: bool = False
    isPrescriptor: bool = False
    isTienda: bool = False
    linkedRepresentativeId: Optional[str] = None
    allowedModules: List[str] = ["montada"]
    allowedCatalogIds: List[str] = []
    commercialDiscount: float = 0
    discountMontada: float = 0
    discountDespiece: float = 0
    canSeeCost: bool = False
    canSeeRetail: bool = True
    canUseAIAnalysis: bool = False
    canManageArticles: bool = False
    canViewTechnicalDespiece: bool = False
    canAccessCRM: bool = False
    canUseDigitalizador: bool = False
    canAccessArmarios: bool = False
    canAuthorizePermissions: bool = False
    useCustomBranding: bool = False
    canChangeLogo: bool = False


class UserResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    username: str
    clientName: str
    linkedClientId: Optional[str] = None
    isActive: bool = True
    isAdmin: bool = False
    isGerente: bool = False
    isResponsableDelegacion: bool = False
    isRepresentative: bool = False
    isPrescriptor: bool = False
    isTienda: bool = False
    linkedRepresentativeId: Optional[str] = None
    allowedModules: List[str] = ["montada"]
    allowedCatalogIds: List[str] = []
    commercialDiscount: float = 0
    discountMontada: float = 0
    discountDespiece: float = 0
    canSeeCost: bool = False
    canSeeRetail: bool = True
    canUseAIAnalysis: bool = False
    canManageArticles: bool = False
    canViewTechnicalDespiece: bool = False
    canAccessCRM: bool = False
    canUseDigitalizador: bool = False
    canAccessArmarios: bool = False
    canAuthorizePermissions: bool = False
    useCustomBranding: bool = False
    canChangeLogo: bool = False


class UserCreate(BaseModel):
    username: str
    password: str
    clientName: str
    linkedClientId: Optional[str] = None
    isActive: bool = True
    isAdmin: bool = False
    isGerente: bool = False
    isResponsableDelegacion: bool = False
    isRepresentative: bool = False
    isPrescriptor: bool = False
    isTienda: bool = False
    linkedRepresentativeId: Optional[str] = None
    allowedModules: List[str] = ["montada"]
    allowedCatalogIds: List[str] = []
    commercialDiscount: float = 0
    discountMontada: float = 0
    discountDespiece: float = 0
    canSeeCost: bool = False
    canSeeRetail: bool = True
    canUseAIAnalysis: bool = False
    canManageArticles: bool = False
    canViewTechnicalDespiece: bool = False
    canAccessCRM: bool = False
    canUseDigitalizador: bool = False
    canAccessArmarios: bool = False
    canAuthorizePermissions: bool = False
    useCustomBranding: bool = False
    canChangeLogo: bool = False


class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    clientName: Optional[str] = None
    linkedClientId: Optional[str] = None
    isActive: Optional[bool] = None
    isAdmin: Optional[bool] = None
    isGerente: Optional[bool] = None
    isResponsableDelegacion: Optional[bool] = None
    isRepresentative: Optional[bool] = None
    isPrescriptor: Optional[bool] = None
    isTienda: Optional[bool] = None
    linkedRepresentativeId: Optional[str] = None
    allowedModules: Optional[List[str]] = None
    allowedCatalogIds: Optional[List[str]] = None
    commercialDiscount: Optional[float] = None
    discountMontada: Optional[float] = None
    discountDespiece: Optional[float] = None
    canSeeCost: Optional[bool] = None
    canSeeRetail: Optional[bool] = None
    canUseAIAnalysis: Optional[bool] = None
    canManageArticles: Optional[bool] = None
    canViewTechnicalDespiece: Optional[bool] = None
    canAccessCRM: Optional[bool] = None
    canUseDigitalizador: Optional[bool] = None
    canAccessArmarios: Optional[bool] = None
    canAuthorizePermissions: Optional[bool] = None
    useCustomBranding: Optional[bool] = None
    canChangeLogo: Optional[bool] = None


# ============================================
# PRODUCT MODELS
# ============================================

class ZonePoints(BaseModel):
    model_config = ConfigDict(extra="ignore")
    Z1: float = 0
    Z2: float = 0
    Z3: float = 0
    Z4: float = 0
    Z5: float = 0
    Z6: float = 0
    Z7: float = 0
    Z8: float = 0
    Z9: float = 0
    Z10: float = 0
    Z11: float = 0
    Z12: float = 0


class ProductModel(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: f"prod-{uuid.uuid4().hex[:8]}")
    code: str
    name: str
    reference: Optional[str] = None
    category: str = ""
    series: str = ""
    programa: str = ""
    tipo_mueble: str = ""
    fondo: int = 35
    visualType: str = ""
    width: float = 0
    height: float = 0
    depth: float = 0
    ancho: Optional[float] = None
    alto: Optional[float] = None
    manufacturer: str = "Luiggi Home Master"
    points: float = 0
    zonePoints: Optional[ZonePoints] = None
    module: str = "montada"


class ProductCreate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    code: str
    name: str
    category: str = ""
    series: str = ""
    visualType: str = ""
    width: float = 0
    height: float = 0
    depth: float = 0
    manufacturer: str = "Luiggi Home Master"
    points: float = 0
    zonePoints: Optional[ZonePoints] = None
    module: str = "montada"


# ============================================
# MATERIAL MODELS
# ============================================

class MaterialModel(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: f"mat-{uuid.uuid4().hex[:8]}")
    name: str
    fixedIncrement: float = 0
    thickness: float = 16


class MaterialCreate(BaseModel):
    name: str
    fixedIncrement: float = 0
    thickness: float = 16


# ============================================
# PROJECT/BUDGET MODELS
# ============================================

class BudgetItemModel(BaseModel):
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
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: f"proj-{uuid.uuid4().hex[:8]}")
    userId: str
    clientCode: str = ""
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
    clientCode: str = ""
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
    clientCode: Optional[str] = None
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


# ============================================
# SETTINGS MODELS
# ============================================

class SettingsModel(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = "global-settings"
    pointValueMontada: float = 1.0
    pointValueDespiece: float = 0.88
    specialIncrementWidth: float = 45
    specialIncrementHeight: float = 45
    specialIncrementDepth: float = 45
    vigaCutIncrement: float = 0
    brandColor: str = "#ea580c"
    logo: Optional[str] = None
    defaultCarcassMaterialId: Optional[str] = None


class SettingsUpdate(BaseModel):
    pointValueMontada: Optional[float] = None
    pointValueDespiece: Optional[float] = None
    specialIncrementWidth: Optional[float] = None
    specialIncrementHeight: Optional[float] = None
    specialIncrementDepth: Optional[float] = None
    vigaCutIncrement: Optional[float] = None
    brandColor: Optional[str] = None
    logo: Optional[str] = None
    defaultCarcassMaterialId: Optional[str] = None


# ============================================
# CLIENT MODELS
# ============================================

class ClientModel(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: f"cli-{uuid.uuid4().hex[:8]}")
    code: str = ""
    name: str
    company: str = ""
    email: str = ""
    phone: str = ""
    address: str = ""
    city: str = ""
    province: str = ""
    postalCode: str = ""
    taxId: str = ""
    segment: str = "particular"
    status: str = "potential"
    value: float = 0.0
    notes: str = ""
    linkedUserId: Optional[str] = None
    assignedRepresentativeId: Optional[str] = None
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ClientCreate(BaseModel):
    code: str = ""
    name: str
    company: str = ""
    email: str = ""
    phone: str = ""
    address: str = ""
    city: str = ""
    province: str = ""
    postalCode: str = ""
    taxId: str = ""
    segment: str = "particular"
    status: str = "potential"
    value: float = 0.0
    notes: str = ""
    assignedRepresentativeId: Optional[str] = None


class ClientUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    company: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    postalCode: Optional[str] = None
    taxId: Optional[str] = None
    segment: Optional[str] = None
    status: Optional[str] = None
    value: Optional[float] = None
    notes: Optional[str] = None
    linkedUserId: Optional[str] = None
    assignedRepresentativeId: Optional[str] = None


# ============================================
# CRM MODELS
# ============================================

class ContactModel(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: f"cont-{uuid.uuid4().hex[:8]}")
    name: str
    company: str = ""
    email: str = ""
    phone: str = ""
    address: str = ""
    city: str = ""
    province: str = ""
    postalCode: str = ""
    segment: str = "particular"
    businessType: str = ""
    status: str = "new"
    stage: str = "lead"
    source: str = ""
    value: float = 0.0
    notes: str = ""
    prescriptorId: Optional[str] = None
    assignedToId: Optional[str] = None
    lastContactDate: Optional[datetime] = None
    nextFollowUp: Optional[datetime] = None
    tags: List[str] = []
    customValues: Dict = {}
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ContactCreate(BaseModel):
    name: str
    company: str = ""
    email: str = ""
    phone: str = ""
    address: str = ""
    city: str = ""
    province: str = ""
    postalCode: str = ""
    segment: str = "particular"
    businessType: str = ""
    status: str = "new"
    stage: str = "lead"
    source: str = ""
    value: float = 0.0
    notes: str = ""
    prescriptorId: Optional[str] = None
    assignedToId: Optional[str] = None


class ContactUpdate(BaseModel):
    name: Optional[str] = None
    company: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    postalCode: Optional[str] = None
    segment: Optional[str] = None
    businessType: Optional[str] = None
    status: Optional[str] = None
    stage: Optional[str] = None
    source: Optional[str] = None
    value: Optional[float] = None
    notes: Optional[str] = None
    prescriptorId: Optional[str] = None
    assignedToId: Optional[str] = None
    lastContactDate: Optional[datetime] = None
    nextFollowUp: Optional[datetime] = None
    tags: Optional[List[str]] = None


class OpportunityModel(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: f"opp-{uuid.uuid4().hex[:8]}")
    title: str
    contactId: str
    contactName: str = ""
    value: float = 0.0
    stage: str = "qualification"
    probability: int = 10
    expectedCloseDate: Optional[datetime] = None
    description: str = ""
    projectId: Optional[str] = None
    assignedToId: Optional[str] = None
    lostReason: str = ""
    wonDate: Optional[datetime] = None
    lostDate: Optional[datetime] = None
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class OpportunityCreate(BaseModel):
    title: str
    contactId: str
    contactName: str = ""
    value: float = 0.0
    stage: str = "qualification"
    probability: int = 10
    expectedCloseDate: Optional[datetime] = None
    description: str = ""
    projectId: Optional[str] = None
    assignedToId: Optional[str] = None


class OpportunityUpdate(BaseModel):
    title: Optional[str] = None
    contactId: Optional[str] = None
    contactName: Optional[str] = None
    value: Optional[float] = None
    stage: Optional[str] = None
    probability: Optional[int] = None
    expectedCloseDate: Optional[datetime] = None
    description: Optional[str] = None
    projectId: Optional[str] = None
    assignedToId: Optional[str] = None
    lostReason: Optional[str] = None


class CalendarEventModel(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: f"evt-{uuid.uuid4().hex[:8]}")
    title: str
    eventType: str = "meeting"
    startDate: datetime
    endDate: datetime
    allDay: bool = False
    location: str = ""
    description: str = ""
    contactId: Optional[str] = None
    contactName: str = ""
    opportunityId: Optional[str] = None
    assignedToId: Optional[str] = None
    completed: bool = False
    completedAt: Optional[datetime] = None
    reminderMinutes: int = 30
    color: str = "#3b82f6"
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CalendarEventCreate(BaseModel):
    title: str
    eventType: str = "meeting"
    startDate: datetime
    endDate: datetime
    allDay: bool = False
    location: str = ""
    description: str = ""
    contactId: Optional[str] = None
    contactName: str = ""
    opportunityId: Optional[str] = None
    assignedToId: Optional[str] = None
    reminderMinutes: int = 30
    color: str = "#3b82f6"


class CalendarEventUpdate(BaseModel):
    title: Optional[str] = None
    eventType: Optional[str] = None
    startDate: Optional[datetime] = None
    endDate: Optional[datetime] = None
    allDay: Optional[bool] = None
    location: Optional[str] = None
    description: Optional[str] = None
    contactId: Optional[str] = None
    contactName: Optional[str] = None
    opportunityId: Optional[str] = None
    assignedToId: Optional[str] = None
    completed: Optional[bool] = None
    reminderMinutes: Optional[int] = None
    color: Optional[str] = None


class ActivityModel(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: f"act-{uuid.uuid4().hex[:8]}")
    activityType: str
    description: str
    contactId: Optional[str] = None
    opportunityId: Optional[str] = None
    userId: str
    userName: str = ""
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ActivityCreate(BaseModel):
    activityType: str
    description: str
    contactId: Optional[str] = None
    opportunityId: Optional[str] = None


class ActivityUpdate(BaseModel):
    activityType: Optional[str] = None
    description: Optional[str] = None


# ============================================
# DISTRIBUTOR REQUEST MODEL
# ============================================

class DistributorRequest(BaseModel):
    businessName: str
    contactName: str
    email: str
    phone: str
    city: str
    province: str
    currentActivity: str
    monthlyVolume: str
    message: str = ""
