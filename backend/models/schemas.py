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
# FACTORY MODELS (Fábricas)
# ============================================

class FactoryModel(BaseModel):
    """Modelo para representar una fábrica"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: f"fab-{uuid.uuid4().hex[:8]}")
    name: str  # Nombre de la fábrica (ej: "SALAMANCA", "ZAMORA")
    code: str  # Código corto (ej: "SAL", "ZAM")
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    isActive: bool = True
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class FactoryCreate(BaseModel):
    name: str
    code: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None


class FactoryResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    code: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    isActive: bool = True
    createdAt: datetime


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
    isDirectorComercial: bool = False
    isDirectorFabrica: bool = False  # Director de Fábrica - ve Dashboard Fábrica y gestiona producción
    isResponsableDelegacion: bool = False
    isRepresentative: bool = False
    isPrescriptor: bool = False
    isTienda: bool = False
    isFabrica: bool = False  # Rol de fábrica - acceso a órdenes de fabricación
    factoryId: Optional[str] = None  # ID de la fábrica asignada (si es usuario de fábrica)
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
    canAccessFabrica: bool = False  # Acceso al portal de fábrica
    canAccessMontajes: bool = False  # Acceso a la agenda de montajes
    canManageOrders: bool = False  # Gestión de órdenes de fabricación
    canSetDeliveryDates: bool = False  # Puede establecer plazos de entrega
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
    isDirectorComercial: bool = False
    isDirectorFabrica: bool = False  # Director de Fábrica - ve Dashboard Fábrica y gestiona producción
    isResponsableDelegacion: bool = False
    isRepresentative: bool = False
    isPrescriptor: bool = False
    isTienda: bool = False
    isFabrica: bool = False  # Rol de fábrica
    factoryId: Optional[str] = None  # ID de la fábrica asignada
    factoryName: Optional[str] = None  # Nombre de la fábrica (para mostrar en UI)
    linkedRepresentativeId: Optional[str] = None
    allowedModules: List[str] = ["montada"]
    allowedLibraries: List[str] = ["ZC"]  # Tarifas/Bibliotecas activas
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
    canAccessFabrica: bool = False  # Acceso al portal de fábrica
    canManageOrders: bool = False  # Gestión de órdenes de fabricación
    canSetDeliveryDates: bool = False  # Puede establecer plazos de entrega
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
    isDirectorComercial: bool = False
    isDirectorFabrica: bool = False  # Director de Fábrica - ve Dashboard Fábrica y gestiona producción
    isResponsableDelegacion: bool = False
    isRepresentative: bool = False
    isPrescriptor: bool = False
    isTienda: bool = False
    isFabrica: bool = False  # Rol de fábrica
    factoryId: Optional[str] = None  # ID de la fábrica asignada
    isMontador: bool = False  # Rol de montador
    montadorId: Optional[str] = None  # ID del montador asignado
    linkedRepresentativeId: Optional[str] = None
    allowedModules: List[str] = ["montada"]
    allowedLibraries: List[str] = ["ZC"]  # Tarifas/Bibliotecas activas
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
    canAccessFabrica: bool = False  # Acceso al portal de fábrica
    canManageOrders: bool = False  # Gestión de órdenes de fabricación
    canSetDeliveryDates: bool = False  # Puede establecer plazos de entrega
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
    isDirectorComercial: Optional[bool] = None
    isDirectorFabrica: Optional[bool] = None  # Director de Fábrica
    isResponsableDelegacion: Optional[bool] = None
    isRepresentative: Optional[bool] = None
    isPrescriptor: Optional[bool] = None
    isTienda: Optional[bool] = None
    isFabrica: Optional[bool] = None  # Rol de fábrica
    factoryId: Optional[str] = None  # ID de la fábrica asignada
    isMontador: Optional[bool] = None  # Rol de montador
    montadorId: Optional[str] = None  # ID del montador asignado
    linkedRepresentativeId: Optional[str] = None
    allowedModules: Optional[List[str]] = None
    allowedLibraries: Optional[List[str]] = None  # Tarifas/Bibliotecas activas
    allowedCatalogIds: Optional[List[str]] = None
    commercialDiscount: Optional[float] = None
    discountMontada: Optional[float] = None
    discountDespiece: Optional[float] = None
    canSeeCost: Optional[bool] = None
    canAccessFabrica: Optional[bool] = None  # Acceso al portal de fábrica
    canManageOrders: Optional[bool] = None  # Gestión de órdenes de fabricación
    canSetDeliveryDates: Optional[bool] = None  # Puede establecer plazos de entrega
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
    library: str = "ZC"  # Biblioteca asociada (ZC, MV)


class MaterialCreate(BaseModel):
    name: str
    fixedIncrement: float = 0
    thickness: float = 16
    library: str = "ZC"


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
    totalCoste: float = 0.0
    margen: float = 0.0
    descuentoAplicado: float = 0.0
    totalConIVA: float = 0.0
    ivaRate: float = 21.0
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "borrador"
    sentAt: Optional[datetime] = None
    acceptedAt: Optional[datetime] = None
    rejectedAt: Optional[datetime] = None
    deliveredAt: Optional[datetime] = None
    validUntil: Optional[datetime] = None
    statusHistory: List[Dict] = []
    versions: List[Dict] = []


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
    totalCoste: float = 0.0
    margen: float = 0.0
    descuentoAplicado: float = 0.0
    totalConIVA: float = 0.0
    ivaRate: float = 21.0
    status: str = "borrador"
    validUntil: Optional[datetime] = None


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
    totalCoste: Optional[float] = None
    margen: Optional[float] = None
    descuentoAplicado: Optional[float] = None
    totalConIVA: Optional[float] = None
    ivaRate: Optional[float] = None
    status: Optional[str] = None
    validUntil: Optional[datetime] = None


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
    # Incrementos especiales por biblioteca
    librarySpecialIncrements: Optional[Dict] = None
    # Corte de viga por biblioteca  
    libraryVigaCutIncrements: Optional[Dict] = None
    brandColor: str = "#ea580c"
    logo: Optional[str] = None
    defaultCarcassMaterialId: Optional[str] = None
    # Módulos del sistema
    montajesEnabled: bool = False


class SettingsUpdate(BaseModel):
    pointValueMontada: Optional[float] = None
    pointValueDespiece: Optional[float] = None
    specialIncrementWidth: Optional[float] = None
    specialIncrementHeight: Optional[float] = None
    specialIncrementDepth: Optional[float] = None
    vigaCutIncrement: Optional[float] = None
    librarySpecialIncrements: Optional[Dict] = None
    libraryVigaCutIncrements: Optional[Dict] = None
    brandColor: Optional[str] = None
    logo: Optional[str] = None
    defaultCarcassMaterialId: Optional[str] = None
    montajesEnabled: Optional[bool] = None
    companyName: Optional[str] = None
    companyTaxId: Optional[str] = None
    companyAddress: Optional[str] = None
    companyPhone: Optional[str] = None
    companyEmail: Optional[str] = None
    companyIban: Optional[str] = None


# ============================================
# CLIENT MODELS
# ============================================

class ClientModel(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: f"cli-{uuid.uuid4().hex[:8]}")
    code: str = ""  # Código interno del sistema
    externalCode: str = ""  # Código del programa de gestión externo
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
    externalCode: str = ""  # Código del programa de gestión externo
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
    externalCode: Optional[str] = None  # Código del programa de gestión externo
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
    userId: Optional[str] = ""
    userName: str = ""
    title: Optional[str] = None
    dueDate: Optional[str] = None
    dueTime: Optional[str] = None
    completed: bool = False
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ActivityCreate(BaseModel):
    activityType: str
    description: str
    contactId: Optional[str] = None
    opportunityId: Optional[str] = None
    userId: Optional[str] = None
    userName: Optional[str] = ""
    dueDate: Optional[str] = None
    dueTime: Optional[str] = None
    title: Optional[str] = None


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



# ============================================
# DESPIECE MODELS
# ============================================

class DespieceItemInput(BaseModel):
    """Input for a single furniture item to calculate despiece"""
    productId: str
    productCode: str
    productName: str
    width: float
    height: float
    depth: float
    quantity: int = 1
    category: str = ""


class DespieceRequest(BaseModel):
    """Request to calculate despiece for multiple items"""
    items: List[DespieceItemInput]
    carcassMaterial: str = "Melamina Blanca"
    backPanelMaterial: str = "Tablero 8mm"
    grosor: float = 18
    backThickness: float = 8  # Grosor de trasera en mm
    doorToleranceHeight: float = 2  # Tolerancia alto puerta en mm
    doorToleranceWidth: float = 3   # Tolerancia ancho puerta en mm


class ComponentPiece(BaseModel):
    """A single piece/component in the despiece"""
    id: str
    name: str
    nameShort: str
    material: str
    length: float
    width: float
    thickness: float = 18
    quantity: int
    area: float
    notes: str = ""


class FurnitureDespiece(BaseModel):
    """Despiece for a single furniture piece"""
    productId: str
    productCode: str
    productName: str
    category: str
    originalWidth: float
    originalHeight: float
    originalDepth: float
    itemQuantity: int
    components: List[ComponentPiece]
    totalPanels: int
    totalArea: float


class DespieceResponse(BaseModel):
    """Full despiece response"""
    items: List[FurnitureDespiece]
    summary: Dict
    generatedAt: str


# ============================================
# DIGITALIZADOR MODELS
# ============================================

class DigitalizadorMatchedProduct(BaseModel):
    """A product matched from the catalog"""
    id: str
    code: str
    name: str
    price: float = 0
    score: float = 0


class DigitalizadorLine(BaseModel):
    """A single line extracted from the draft"""
    id: str
    quantity: int = 1
    reference: str = ""
    description: str
    price: float = 0
    discount: float = 0
    isManual: bool = False
    matchedProducts: List[DigitalizadorMatchedProduct] = []


class DigitalizadorRequest(BaseModel):
    """Request to analyze a draft image"""
    imageBase64: str
    filename: str = "draft.jpg"
    library: str = "ZC"  # Biblioteca activa (ZC o MV)


class DigitalizadorResponse(BaseModel):
    """Response with extracted lines"""
    success: bool
    projectName: str = ""
    lines: List[DigitalizadorLine]
    rawText: str = ""
    error: Optional[str] = None


class DigitalizadorExportRequest(BaseModel):
    """Request to export to CSV for cutting machine"""
    lines: List[DigitalizadorLine]
    materialCode: str = "40-ESTEITEX16"
    materialThickness: float = 16.0


class DigitalizadorSaveRequest(BaseModel):
    """Request to save a digitalized budget to history"""
    projectName: str
    customerName: str = ""
    acabado: str = ""
    armazon: str = ""
    costados: str = ""
    lines: List[DigitalizadorLine]
    globalDiscount: float = 0
    globalMarkup: float = 0
    ivaRate: float = 21
    userId: str
    expNumber: str = ""


class DigitalizadorHistoryItem(BaseModel):
    """A saved digitalized budget"""
    id: str
    projectName: str
    customerName: str
    acabado: str
    armazon: str
    costados: str
    lines: List[DigitalizadorLine]
    globalDiscount: float
    globalMarkup: float = 0
    ivaRate: float
    totalBruto: float
    totalNeto: float
    totalConIva: float
    userId: str
    createdAt: str
    filename: str = ""


class ExpedienteRequest(BaseModel):
    """Request to generate expediente number"""
    userId: Optional[str] = None
    clientCode: Optional[str] = None


class DigitalizadorToProjectRequest(BaseModel):
    """Request to convert digitalizador item to project"""
    historyItemId: str
    userId: str


# ============================================
# ARMARIOS MODELS
# ============================================

class ArmarioModuleConfig(BaseModel):
    """Configuración de un módulo de armario"""
    id: int
    shelves: int = 4
    drawers: int = 0
    hangingRods: int = 1
    hangingHeight: int = 1200
    extras: Dict = {}


class ArmarioProject(BaseModel):
    """Proyecto de armario completo"""
    name: str
    customerName: str = ""
    projectRef: str = ""
    width: int = 2400
    height: int = 2400
    depth: int = 600
    modules: int = 3
    doorType: str = "sliding"
    exteriorColor: str = "010"
    interiorColor: str = "010"
    handleColor: str = "231"
    endLeft: str = "standard"
    endRight: str = "standard"
    moduleConfigs: List[ArmarioModuleConfig] = []
    extras: Dict = {}
    ivaRate: float = 21.0
    customAccessories: List[Dict] = []
    totalPrice: float = 0.0
    totalArea: float = 0.0


class ArmarioProjectCreate(ArmarioProject):
    pass


class ArmarioProjectUpdate(BaseModel):
    name: Optional[str] = None
    customerName: Optional[str] = None
    projectRef: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    depth: Optional[int] = None
    modules: Optional[int] = None
    doorType: Optional[str] = None
    exteriorColor: Optional[str] = None
    interiorColor: Optional[str] = None
    handleColor: Optional[str] = None
    endLeft: Optional[str] = None
    endRight: Optional[str] = None
    moduleConfigs: Optional[List[ArmarioModuleConfig]] = None
    extras: Optional[Dict] = None
    ivaRate: Optional[float] = None
    customAccessories: Optional[List[Dict]] = None
    totalPrice: Optional[float] = None
    totalArea: Optional[float] = None


class IAConfigRequest(BaseModel):
    """Request for IA configuration"""
    prompt: str
    currentConfig: Dict


class IARenderRequest(BaseModel):
    """Request to render armario with IA"""
    width: int
    height: int
    depth: int
    modules: int
    moduleConfigs: List[Dict]
    doorType: str = "sliding"
    numDoors: int = 3
    exteriorColorName: str = "Blanco Standard"
    exteriorColorHex: str = "#FFFFFF"
    interiorColorName: str = "Blanco"
    handleColorName: str = "Plata"
    roomStyle: str = "Moderno"


class IALayoutRequest(BaseModel):
    """Request for IA layout generation"""
    prompt: str
    width: int
    height: int
    depth: int
    modules: int


# ============================================
# MAINTENANCE MODELS
# ============================================

class MaintenanceActivateRequest(BaseModel):
    """Request to activate maintenance mode"""
    reason: str = "Mantenimiento programado"
    estimatedDuration: int = 60
    backupFirst: bool = True


class MaintenanceStatusResponse(BaseModel):
    """Response for maintenance status"""
    isActive: bool
    reason: str = ""
    startedAt: Optional[str] = None
    estimatedEndAt: Optional[str] = None
    lastBackup: Optional[str] = None



# ============================================
# AUTHENTICATION & 2FA MODELS
# ============================================

class UserRegisterRequest(BaseModel):
    """Request to register a new user with email"""
    email: str
    password: str
    confirmPassword: str
    firstName: str
    lastName: str
    company: str = ""
    phone: str = ""


class UserRegisterResponse(BaseModel):
    """Response after successful registration"""
    success: bool
    message: str
    userId: str = ""
    requiresEmailVerification: bool = True


class EmailVerificationRequest(BaseModel):
    """Request to verify email with code"""
    email: str
    code: str


class Enable2FARequest(BaseModel):
    """Request to enable 2FA"""
    userId: str


class Enable2FAResponse(BaseModel):
    """Response with 2FA setup info"""
    success: bool
    secret: str = ""
    qrCodeUrl: str = ""
    backupCodes: List[str] = []


class Verify2FARequest(BaseModel):
    """Request to verify 2FA code"""
    userId: str
    code: str


class Login2FARequest(BaseModel):
    """Request for login with 2FA"""
    email: str
    password: str
    totpCode: str = ""


class PasswordResetRequest(BaseModel):
    """Request to reset password"""
    email: str


class PasswordResetConfirmRequest(BaseModel):
    """Request to confirm password reset with code"""
    email: str
    code: str
    newPassword: str
    confirmPassword: str


class UserProfileUpdate(BaseModel):
    """Update user profile"""
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None



# ==========================================
# AGENDA DE MONTAJES (Montadores/Instaladores)
# ==========================================

class MontadorBase(BaseModel):
    """Base model for montadores (installers)"""
    name: str
    phone: str = ""
    email: str = ""
    company: str = ""  # Empresa/autónomo
    specialty: str = ""  # Especialidad: cocinas, armarios, etc.
    zone: str = ""  # Zona de trabajo
    address: str = ""
    notes: str = ""
    status: str = "active"  # active, inactive, vacation
    rating: float = 0  # 0-5 estrellas
    tags: List[str] = []


class MontadorCreate(MontadorBase):
    """Create a new montador"""
    pass


class MontadorUpdate(BaseModel):
    """Update montador - all fields optional"""
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None
    specialty: Optional[str] = None
    zone: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    rating: Optional[float] = None
    tags: Optional[List[str]] = None


class MontadorResponse(MontadorBase):
    """Response with montador data"""
    id: str
    createdAt: str = ""
    updatedAt: str = ""
    totalMontajes: int = 0


class MontajeBase(BaseModel):
    """Base model for montajes (installations)"""
    montadorId: str
    montadorName: str = ""
    clientName: str
    clientPhone: str = ""
    clientAddress: str
    projectDescription: str = ""
    expectedDeliveryDate: str = ""  # Fecha prevista de recepción de cocina
    scheduledDate: str  # Fecha de montaje comprometida
    scheduledTime: str = ""  # HH:MM
    estimatedDuration: str = ""  # e.g., "2 días"
    status: str = "pendiente"  # pendiente, en_curso, completado, cancelado
    budgetId: str = ""  # ID del presupuesto asociado
    budgetRef: str = ""  # Referencia del presupuesto
    notes: str = ""
    assignedBy: str = ""  # Usuario que asignó el montaje


class MontajeCreate(MontajeBase):
    """Create a new montaje"""
    pass


class MontajeUpdate(BaseModel):
    """Update montaje - all fields optional"""
    montadorId: Optional[str] = None
    montadorName: Optional[str] = None
    clientName: Optional[str] = None
    clientPhone: Optional[str] = None
    clientAddress: Optional[str] = None
    projectDescription: Optional[str] = None
    expectedDeliveryDate: Optional[str] = None
    scheduledDate: Optional[str] = None
    scheduledTime: Optional[str] = None
    estimatedDuration: Optional[str] = None
    status: Optional[str] = None
    budgetId: Optional[str] = None
    budgetRef: Optional[str] = None
    notes: Optional[str] = None


class MontajeResponse(MontajeBase):
    """Response with montaje data"""
    id: str
    createdAt: str = ""
    updatedAt: str = ""
