from fastapi import FastAPI, APIRouter, File, UploadFile, Form, HTTPException, BackgroundTasks
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict
import uuid
from datetime import datetime, timezone
import base64
from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent
import json
import bcrypt
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import asyncio


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# ============================================
# MAINTENANCE MODE STATE
# ============================================
# Estado del modo mantenimiento (en memoria, se sincroniza con BD)
maintenance_state = {
    "active": False,
    "message": "Sistema en actualización. Volvemos pronto.",
    "activatedAt": None,
    "activatedBy": None,
    "estimatedEndTime": None,
    "preUpdateBackupId": None
}


# ============================================
# PASSWORD UTILITIES
# ============================================

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except:
        # If hash is invalid (plain text password from old data), compare directly
        return password == hashed


# ============================================
# MODELS
# ============================================

class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

# User Model (internal with password)
class UserModelInternal(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: f"user-{uuid.uuid4().hex[:8]}")
    username: str
    password: str
    clientName: str
    linkedClientId: Optional[str] = None  # Vinculación con cliente activo
    isActive: bool = True
    isAdmin: bool = False  # Director Comercial (antes Administrador)
    isResponsableDelegacion: bool = False  # Responsable de Delegación - reporta al Director Comercial
    isRepresentative: bool = False  # Comercial/Representante
    isPrescriptor: bool = False  # Colaborador comercial - solo aporta contactos
    isTienda: bool = False  # Tienda/Punto de Venta - solo acceso al presupuestador
    linkedRepresentativeId: Optional[str] = None  # Para tiendas: vinculado a Comercial/Responsable/Director
    allowedModules: List[str] = ["montada"]
    allowedCatalogIds: List[str] = []
    commercialDiscount: float = 0
    canSeeCost: bool = False
    canSeeRetail: bool = True
    canUseAIAnalysis: bool = False
    canManageArticles: bool = False
    canViewTechnicalDespiece: bool = False
    canAccessCRM: bool = False
    canUseDigitalizador: bool = False
    canAccessArmarios: bool = False  # Acceso a sección de Armarios
    canAuthorizePermissions: bool = False  # Responsable Delegación puede autorizar permisos
    useCustomBranding: bool = False
    canChangeLogo: bool = False

# User response model (without password)
class UserResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    username: str
    clientName: str
    linkedClientId: Optional[str] = None
    isActive: bool = True
    isAdmin: bool = False  # Director Comercial
    isResponsableDelegacion: bool = False  # Responsable Delegación
    isRepresentative: bool = False
    isPrescriptor: bool = False
    isTienda: bool = False  # Tienda/Punto de Venta
    linkedRepresentativeId: Optional[str] = None
    allowedModules: List[str] = ["montada"]
    allowedCatalogIds: List[str] = []
    commercialDiscount: float = 0
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
    isAdmin: bool = False  # Director Comercial
    isResponsableDelegacion: bool = False  # Responsable Delegación
    isRepresentative: bool = False
    isPrescriptor: bool = False
    isTienda: bool = False  # Tienda/Punto de Venta
    linkedRepresentativeId: Optional[str] = None
    allowedModules: List[str] = ["montada"]
    allowedCatalogIds: List[str] = []
    commercialDiscount: float = 0
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
    isAdmin: Optional[bool] = None  # Director Comercial
    isResponsableDelegacion: Optional[bool] = None  # Responsable Delegación
    isRepresentative: Optional[bool] = None
    isPrescriptor: Optional[bool] = None
    isTienda: Optional[bool] = None  # Tienda/Punto de Venta
    linkedRepresentativeId: Optional[str] = None
    allowedModules: Optional[List[str]] = None
    allowedCatalogIds: Optional[List[str]] = None
    commercialDiscount: Optional[float] = None
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

# Product Model
class ZonePoints(BaseModel):
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
    category: str = ""
    series: str = ""
    visualType: str = ""
    width: float = 0
    height: float = 0
    depth: float = 0
    manufacturer: str = "Luiggi Home Master"
    points: float = 0
    zonePoints: Optional[ZonePoints] = None
    module: str = "montada"  # montada or despiece

class ProductCreate(BaseModel):
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

# Material Model
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

# Budget Item Model
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

# Project/Budget Model
class ProjectModel(BaseModel):
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
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "draft"  # draft, completed, archived

class ProjectCreate(BaseModel):
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
    status: str = "draft"

class ProjectUpdate(BaseModel):
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
    status: Optional[str] = None

# Settings Model
class SettingsModel(BaseModel):
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
    pointValueMontada: Optional[float] = None
    pointValueDespiece: Optional[float] = None
    specialIncrementWidth: Optional[float] = None
    specialIncrementHeight: Optional[float] = None
    specialIncrementDepth: Optional[float] = None
    brandColor: Optional[str] = None
    logo: Optional[str] = None

class StatusCheckCreate(BaseModel):
    client_name: str

# ============================================
# CLIENT MODELS - Clientes (Potenciales y Activos)
# ============================================

# Segmentos de clientes
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
    """Modelo para clientes (potenciales y activos)"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: f"cli-{uuid.uuid4().hex[:8]}")
    tipo: str = "potencial"  # 'potencial' o 'activo'
    codigo: str = ""  # Código del programa de gestión (vacío si potencial)
    nombre: str  # Nombre comercial / Razón social
    cif: str = ""  # CIF/NIF
    segmento: str = ""  # Segmento de cliente (ver CLIENT_SEGMENTS)
    direccion: str = ""
    localidad: str = ""
    provincia: str = ""
    codigoPostal: str = ""
    telefono: str = ""
    email: str = ""
    descuento: float = 0  # Descuento personalizado (%)
    activo: bool = True
    notas: str = ""
    # Vinculaciones
    origenCrmContactId: str = ""  # ID del contacto CRM original (si viene del CRM)
    usuarioVinculadoId: str = ""  # ID del usuario del sistema (si tiene acceso)
    # Metadata
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    convertidoAt: Optional[datetime] = None  # Fecha de conversión a activo

class ClientCreate(BaseModel):
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

# ============================================
# CRM MODELS - Contactos, Oportunidades, Actividades
# ============================================

class ContactModel(BaseModel):
    """Modelo para contactos/clientes del CRM"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: f"contact-{uuid.uuid4().hex[:8]}")
    name: str
    email: str = ""
    phone: str = ""
    company: str = ""
    position: str = ""
    address: str = ""
    notes: str = ""
    tags: List[str] = []
    source: str = ""  # web, referral, cold_call, prescriptor, etc.
    status: str = "active"  # active, inactive, lead, customer
    segment: str = ""  # Segmento: PROMOTOR, CONSTRUCTOR, etc.
    prescriptorId: str = ""  # ID del prescriptor que refirió este contacto
    prescriptorName: str = ""  # Nombre del prescriptor
    assignedTo: str = ""  # ID del comercial/representante asignado
    totalValue: float = 0  # Valor total de oportunidades ganadas
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    createdBy: str = ""
    # Link to project for kitchen budgets
    linkedProjectIds: List[str] = []
    # Flag para indicar si fue convertido a cliente
    convertedToClientId: Optional[str] = None

class ContactCreate(BaseModel):
    name: str
    email: str = ""
    phone: str = ""
    company: str = ""
    position: str = ""
    address: str = ""
    notes: str = ""
    tags: List[str] = []
    source: str = ""
    status: str = "lead"
    segment: str = ""
    prescriptorId: str = ""
    prescriptorName: str = ""
    assignedTo: str = ""  # ID del comercial/representante asignado

class ContactUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    position: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    source: Optional[str] = None
    status: Optional[str] = None
    segment: Optional[str] = None
    prescriptorId: Optional[str] = None
    prescriptorName: Optional[str] = None
    assignedTo: Optional[str] = None  # ID del comercial/representante asignado
    totalValue: Optional[float] = None
    linkedProjectIds: Optional[List[str]] = None

class OpportunityModel(BaseModel):
    """Modelo para oportunidades de venta (pipeline)"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: f"opp-{uuid.uuid4().hex[:8]}")
    title: str
    description: str = ""
    contactId: str  # Link to contact
    contactName: str = ""
    company: str = ""
    value: float = 0  # Valor en euros
    probability: int = 20  # Probabilidad de cierre (0-100)
    stage: str = "lead"  # lead, contacted, proposal, negotiation, won, lost
    expectedCloseDate: Optional[str] = None
    notes: str = ""
    tags: List[str] = []
    assignedTo: str = ""  # User assigned
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    closedAt: Optional[datetime] = None
    createdBy: str = ""
    # Link to project/budget
    linkedProjectId: Optional[str] = None
    linkedProjectNumber: Optional[str] = None

class OpportunityCreate(BaseModel):
    title: str
    description: str = ""
    contactId: str
    contactName: str = ""
    company: str = ""
    value: float = 0
    probability: int = 20
    stage: str = "lead"
    expectedCloseDate: Optional[str] = None
    notes: str = ""
    tags: List[str] = []
    assignedTo: str = ""
    linkedProjectId: Optional[str] = None
    linkedProjectNumber: Optional[str] = None

class OpportunityUpdate(BaseModel):
    title: Optional[str] = None

# ============================================
# CALENDAR EVENT MODELS
# ============================================

class CalendarEventModel(BaseModel):
    """Modelo para eventos del calendario CRM"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: f"evt-{uuid.uuid4().hex[:8]}")
    title: str
    description: str = ""
    eventType: str = "cita"  # cita, seguimiento, llamada, reunion, otro
    startDate: str  # ISO format datetime
    endDate: str  # ISO format datetime
    allDay: bool = False
    # Linked entities
    contactId: Optional[str] = None
    contactName: Optional[str] = None
    opportunityId: Optional[str] = None
    opportunityTitle: Optional[str] = None
    # Assignment
    assignedTo: str  # User ID
    assignedToName: str = ""
    createdBy: str
    createdByName: str = ""
    # Status
    completed: bool = False
    completedAt: Optional[str] = None
    reminder: Optional[int] = None  # Minutes before event
    # Metadata
    color: Optional[str] = None  # Custom color for the event
    location: Optional[str] = None
    notes: str = ""
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CalendarEventCreate(BaseModel):
    title: str
    description: str = ""
    eventType: str = "cita"
    startDate: str
    endDate: str
    allDay: bool = False
    contactId: Optional[str] = None
    contactName: Optional[str] = None
    opportunityId: Optional[str] = None
    opportunityTitle: Optional[str] = None
    assignedTo: str
    assignedToName: str = ""
    reminder: Optional[int] = None
    color: Optional[str] = None
    location: Optional[str] = None
    notes: str = ""

class CalendarEventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    eventType: Optional[str] = None
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    allDay: Optional[bool] = None
    contactId: Optional[str] = None
    contactName: Optional[str] = None
    opportunityId: Optional[str] = None
    opportunityTitle: Optional[str] = None
    assignedTo: Optional[str] = None
    assignedToName: Optional[str] = None
    completed: Optional[bool] = None
    reminder: Optional[int] = None
    color: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None

# Activity model (existing)
    description: Optional[str] = None
    contactId: Optional[str] = None
    contactName: Optional[str] = None
    company: Optional[str] = None
    value: Optional[float] = None
    probability: Optional[int] = None
    stage: Optional[str] = None
    expectedCloseDate: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    assignedTo: Optional[str] = None
    linkedProjectId: Optional[str] = None
    linkedProjectNumber: Optional[str] = None

class ActivityModel(BaseModel):
    """Modelo para actividades y tareas del CRM"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: f"act-{uuid.uuid4().hex[:8]}")
    type: str  # call, meeting, email, task, note
    title: str
    description: str = ""
    contactId: Optional[str] = None
    contactName: str = ""
    opportunityId: Optional[str] = None
    opportunityTitle: str = ""
    dueDate: Optional[str] = None
    dueTime: Optional[str] = None
    completed: bool = False
    completedAt: Optional[datetime] = None
    priority: str = "medium"  # low, medium, high
    assignedTo: str = ""
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    createdBy: str = ""

class ActivityCreate(BaseModel):
    type: str
    title: str
    description: str = ""
    contactId: Optional[str] = None
    contactName: str = ""
    opportunityId: Optional[str] = None
    opportunityTitle: str = ""
    dueDate: Optional[str] = None
    dueTime: Optional[str] = None
    priority: str = "medium"
    assignedTo: str = ""

class ActivityUpdate(BaseModel):
    type: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    contactId: Optional[str] = None
    contactName: Optional[str] = None
    opportunityId: Optional[str] = None
    opportunityTitle: Optional[str] = None
    dueDate: Optional[str] = None
    dueTime: Optional[str] = None
    completed: Optional[bool] = None
    priority: Optional[str] = None
    assignedTo: Optional[str] = None

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Hello World"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    
    # Convert to dict and serialize datetime to ISO string for MongoDB
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    
    _ = await db.status_checks.insert_one(doc)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    # Exclude MongoDB's _id field from the query results
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    
    # Convert ISO string timestamps back to datetime objects
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    
    return status_checks

@api_router.post("/ia-lab/analyze-kitchen-plan")
async def analyze_kitchen_plan(file: UploadFile = File(...)):
    """
    Analiza un plano de cocina usando Gemini Vision y detecta los muebles.
    Devuelve una lista de muebles con sus códigos estimados.
    """
    try:
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="EMERGENT_LLM_KEY not configured")
        
        # Read the image
        file_content = await file.read()
        base64_image = base64.b64encode(file_content).decode('utf-8')
        mime_type = file.content_type or 'image/png'
        
        analysis_prompt = """Analiza este plano/diseño de cocina y detecta TODOS los muebles visibles.

IDENTIFICA:
1. Muebles ALTOS (armarios de pared superiores)
2. Muebles BAJOS (armarios de base con encimera)
3. COLUMNAS (muebles de altura completa - despensas, hornos)
4. SEMICOLUMNAS (muebles de media altura)
5. Electrodomésticos integrados (horno, microondas, nevera)

Para cada mueble detectado, proporciona:
- tipo: ALTO/BAJO/COLUMNA/SEMICOLUMNA/ELECTRODOMESTICO
- subtipo: 1_PUERTA, 2_PUERTAS, CAJON, VITRINA, HORNO, FREGADERO, etc.
- ancho_estimado: ancho en mm (300, 350, 400, 450, 500, 600, 800, 900, etc.)
- alto_estimado: altura en cm (35, 40, 45, 60, 70, 80, 90, 110, 130, etc.)
- fondo_estimado: fondo en cm (33, 58, 60)
- posicion: descripción de ubicación (ej: "esquina izquierda", "sobre fregadero")
- codigo_sugerido: código de referencia estimado (ej: "35A1P400" para Alto 35cm 1 Puerta 40cm)
- confianza: ALTA/MEDIA/BAJA

Responde SOLO con JSON válido:
{
  "muebles_detectados": [
    {
      "tipo": "ALTO",
      "subtipo": "1_PUERTA",
      "ancho_estimado": 400,
      "alto_estimado": 35,
      "fondo_estimado": 33,
      "posicion": "sobre fregadero",
      "codigo_sugerido": "35A1P400",
      "confianza": "ALTA"
    }
  ],
  "resumen": {
    "total_altos": 0,
    "total_bajos": 0,
    "total_columnas": 0,
    "total_semicolumnas": 0,
    "metros_lineales_estimados": 0
  },
  "observaciones": "Notas adicionales sobre el plano"
}"""

        # Use Gemini Vision
        chat = LlmChat(
            api_key=api_key,
            model="gemini/gemini-2.0-flash",
            session_id=f"kitchen-plan-{uuid.uuid4().hex[:8]}",
            system_prompt="Eres un experto en diseño de cocinas. Analiza planos y detecta muebles con precisión."
        )
        
        image_content = ImageContent(
            data=base64_image,
            media_type=mime_type
        )
        
        response = await chat.send_message_async(
            UserMessage(content=[analysis_prompt, image_content])
        )
        
        # Parse response
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        # Clean JSON from markdown
        if '```json' in response_text:
            response_text = response_text.split('```json')[1].split('```')[0]
        elif '```' in response_text:
            response_text = response_text.split('```')[1].split('```')[0]
        
        response_text = response_text.strip()
        
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError:
            import re
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = {"error": "No se pudo analizar el plano", "raw_response": response_text[:500]}
        
        logger.info(f"Kitchen plan analyzed: {len(data.get('muebles_detectados', []))} furniture items detected")
        return {"success": True, "analysis": data}
        
    except Exception as e:
        logger.error(f"Kitchen plan analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/analyze-product-sheets")
async def analyze_product_sheets(
    module: str = Form(...),
    files: List[UploadFile] = File(...)
):
    """
    Analiza fichas de productos usando Gemini Vision API.
    Extrae: código, nombre, dimensiones, puntos por zona, categoría, serie.
    """
    try:
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            return {"error": "EMERGENT_LLM_KEY not configured"}
        
        products = []
        
        for file in files:
            # Read file content
            content = await file.read()
            base64_image = base64.b64encode(content).decode('utf-8')
            
            # Create Gemini chat with vision
            chat = LlmChat(
                api_key=api_key,
                session_id=f"product-analysis-{uuid.uuid4()}",
                system_message="""Eres un experto en digitalización de tarifas técnicas de muebles de cocina.
Tu tarea es extraer TODOS los productos visibles en la imagen de forma estructurada.

INFORMACIÓN A IDENTIFICAR DE CADA PÁGINA:
1. ENCABEZADO DE PÁGINA: Busca texto como "PROGRAMA ESTANDAR - MODULOS [TIPO] - [SERIE]"
   - Tipo: ALTOS, BAJOS, COLUMNAS, SEMICOLUMNAS, etc.
   - Serie: ALTOS 35 FONDO 58, BAJOS 70 FONDO ESTÁNDAR, etc.

2. CATEGORÍAS DE PRODUCTOS: Identifica los grupos como:
   - "Alto 1 puerta", "Alto 2 puertas", "Alto 1 Vitrina", etc.
   - "Bajo 1 puerta", "Bajo fregadero", etc.

3. REFERENCIAS Y ZONAS DE PRECIO:
   - Las referencias son códigos como: 35A1P58350, 7B1P300, 45A2V58600
   - Cada producto tiene 12 zonas de precio (Z1 a Z12)
   - Los precios van en orden horizontal para cada producto

FORMATO DE RESPUESTA - Array JSON con TODOS los productos:
[
  {
    "code": "CÓDIGO_EXACTO",
    "name": "Nombre descriptivo completo",
    "category": "ALTO/BAJO/COLUMNA/SEMICOLUMNA",
    "series": "Serie completa (ej: ALTOS 35 FONDO 58)",
    "visualType": "1P/2P/1V/2V/ABATIBLE/etc",
    "width": ancho_en_mm,
    "height": alto_en_cm,
    "depth": fondo_en_cm,
    "points": valor_Z1,
    "zonePoints": {"Z1": n, "Z2": n, "Z3": n, "Z4": n, "Z5": n, "Z6": n, "Z7": n, "Z8": n, "Z9": n, "Z10": n, "Z11": n, "Z12": n}
  }
]

REGLAS CRÍTICAS:
- Extrae TODOS los productos visibles, no solo el primero
- Respeta el orden de las filas (Z1 es el primer precio de cada fila)
- El ancho (width) se extrae del final del código: 35A1P58350 = 350mm, 35A1P581200 = 1200mm
- La altura se extrae del prefijo: 35 = 35cm, 40 = 40cm, 7B = 70cm (bajo)
- Responde SOLO con el array JSON, sin explicaciones adicionales"""
            ).with_model("gemini", "gemini-2.5-pro")
            
            # Create message with image
            user_message = UserMessage(
                text="Analiza esta página de tarifa técnica de cocina. Extrae TODOS los productos visibles con sus 12 zonas de precio. Responde SOLO con el array JSON de productos.",
                file_contents=[ImageContent(image_base64=base64_image)]
            )
            
            # Get AI response
            response = await chat.send_message(user_message)
            
            # Parse JSON response
            try:
                # Clean response (remove markdown code blocks if present)
                clean_response = response.strip()
                if clean_response.startswith('```'):
                    clean_response = clean_response.split('```')[1]
                    if clean_response.startswith('json'):
                        clean_response = clean_response[4:]
                clean_response = clean_response.strip()
                
                parsed_data = json.loads(clean_response)
                
                # Handle both single object and array
                if isinstance(parsed_data, list):
                    product_list = parsed_data
                else:
                    product_list = [parsed_data]
                
                for product_data in product_list:
                    # Add metadata
                    product_data['id'] = f"AI-{module.upper()}-{uuid.uuid4().hex[:8]}"
                    product_data['manufacturer'] = 'Zona Cocinas'
                    product_data['module'] = module
                    product_data['importedAt'] = datetime.now(timezone.utc).isoformat()
                    product_data['originalFilename'] = file.filename
                    
                    products.append(product_data)
                
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON from Gemini: {e}. Response: {response}")
                products.append({
                    "error": f"No se pudo parsear la respuesta para {file.filename}",
                    "raw_response": response[:500]
                })
        
        return {
            "success": True,
            "count": len(products),
            "products": products
        }
        
    except Exception as e:
        logger.error(f"Error in analyze_product_sheets: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

# ============================================
# USER ENDPOINTS
# ============================================

def user_to_response(user_doc: dict) -> dict:
    """Convert user document to response (excluding password)"""
    return {k: v for k, v in user_doc.items() if k != "password"}

@api_router.get("/users", response_model=List[UserResponse])
async def get_users():
    """Obtener todos los usuarios (sin passwords)"""
    users = await db.users.find({}, {"_id": 0, "password": 0}).to_list(1000)
    return users

@api_router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    """Obtener un usuario por ID (sin password)"""
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user

@api_router.post("/users", response_model=UserResponse)
async def create_user(user: UserCreate):
    """Crear un nuevo usuario con password hasheado"""
    # Check if username exists
    existing = await db.users.find_one({"username": user.username.upper()})
    if existing:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya existe")
    
    user_data = user.model_dump()
    user_data["id"] = f"user-{uuid.uuid4().hex[:8]}"
    user_data["username"] = user_data["username"].upper()
    user_data["password"] = hash_password(user_data["password"])
    
    await db.users.insert_one(user_data)
    return user_to_response(user_data)

@api_router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user: UserUpdate):
    """Actualizar un usuario"""
    existing = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    update_data = {k: v for k, v in user.model_dump().items() if v is not None}
    if "username" in update_data:
        update_data["username"] = update_data["username"].upper()
    
    # Hash password if provided
    if "password" in update_data and update_data["password"]:
        update_data["password"] = hash_password(update_data["password"])
    
    if update_data:
        await db.users.update_one({"id": user_id}, {"$set": update_data})
    
    updated = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
    return updated

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str):
    """Eliminar un usuario"""
    if user_id == "admin":
        raise HTTPException(status_code=400, detail="No se puede eliminar el administrador principal")
    
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"message": "Usuario eliminado"}

# ============================================
# CLIENT ENDPOINTS - Clientes Activos
# ============================================

@api_router.get("/clients")
async def get_clients(activo: Optional[bool] = None, search: Optional[str] = None):
    """Obtener todos los clientes activos"""
    query = {}
    if activo is not None:
        query["activo"] = activo
    
    clients = await db.clients.find(query, {"_id": 0}).to_list(5000)
    
    if search:
        search_lower = search.lower()
        clients = [c for c in clients if 
            search_lower in c.get("codigo", "").lower() or
            search_lower in c.get("nombre", "").lower() or
            search_lower in c.get("cif", "").lower() or
            search_lower in c.get("localidad", "").lower()
        ]
    
    return clients

@api_router.get("/clients/segments")
async def get_client_segments():
    """Obtener lista de segmentos de clientes disponibles"""
    return {"segments": CLIENT_SEGMENTS}

@api_router.get("/clients/{client_id}")
async def get_client(client_id: str):
    """Obtener un cliente por ID"""
    client = await db.clients.find_one({"id": client_id}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return client

@api_router.post("/clients")
async def create_client(client: ClientCreate):
    """Crear un nuevo cliente"""
    # Check if codigo exists (only if codigo is not empty)
    if client.codigo and client.codigo.strip():
        existing = await db.clients.find_one({"codigo": client.codigo.upper()})
        if existing:
            raise HTTPException(status_code=400, detail="El código de cliente ya existe")
    
    client_data = client.model_dump()
    client_data["id"] = f"cli-{uuid.uuid4().hex[:8]}"
    client_data["codigo"] = client_data["codigo"].upper()
    client_data["createdAt"] = datetime.now(timezone.utc).isoformat()
    client_data["updatedAt"] = datetime.now(timezone.utc).isoformat()
    
    await db.clients.insert_one(client_data)
    
    # Return without _id
    if "_id" in client_data:
        del client_data["_id"]
    return client_data

@api_router.put("/clients/{client_id}")
async def update_client(client_id: str, client: ClientUpdate):
    """Actualizar un cliente"""
    existing = await db.clients.find_one({"id": client_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    update_data = {k: v for k, v in client.model_dump().items() if v is not None}
    
    if "codigo" in update_data:
        update_data["codigo"] = update_data["codigo"].upper()
        # Check if new codigo conflicts with another client
        conflict = await db.clients.find_one({
            "codigo": update_data["codigo"],
            "id": {"$ne": client_id}
        })
        if conflict:
            raise HTTPException(status_code=400, detail="El código de cliente ya existe")
    
    update_data["updatedAt"] = datetime.now(timezone.utc).isoformat()
    
    if update_data:
        await db.clients.update_one({"id": client_id}, {"$set": update_data})
    
    updated = await db.clients.find_one({"id": client_id}, {"_id": 0})
    return updated

@api_router.delete("/clients/{client_id}")
async def delete_client(client_id: str):
    """Eliminar un cliente"""
    # Check if client has linked users
    linked_users = await db.users.count_documents({"linkedClientId": client_id})
    if linked_users > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"No se puede eliminar: {linked_users} usuario(s) vinculado(s)"
        )
    
    result = await db.clients.delete_one({"id": client_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return {"message": "Cliente eliminado"}

@api_router.post("/clients/import-csv")
async def import_clients_csv(data: dict):
    """Importar clientes desde CSV (lista de objetos)"""
    clients_data = data.get("clients", [])
    if not clients_data:
        raise HTTPException(status_code=400, detail="No hay datos para importar")
    
    imported = 0
    updated = 0
    errors = []
    
    for idx, client_row in enumerate(clients_data):
        try:
            codigo = str(client_row.get("codigo", "")).upper().strip()
            if not codigo:
                errors.append(f"Fila {idx+1}: Código vacío")
                continue
            
            client_doc = {
                "codigo": codigo,
                "nombre": str(client_row.get("nombre", "")).strip(),
                "cif": str(client_row.get("cif", "")).strip(),
                "direccion": str(client_row.get("direccion", "")).strip(),
                "localidad": str(client_row.get("localidad", "")).strip(),
                "provincia": str(client_row.get("provincia", "")).strip(),
                "codigoPostal": str(client_row.get("codigoPostal", client_row.get("cp", ""))).strip(),
                "telefono": str(client_row.get("telefono", "")).strip(),
                "email": str(client_row.get("email", "")).strip(),
                "descuento": float(client_row.get("descuento", 0)),
                "activo": client_row.get("activo", True) in [True, "true", "True", 1, "1", "SI", "si", "Sí"],
                "notas": str(client_row.get("notas", "")).strip(),
                "updatedAt": datetime.now(timezone.utc).isoformat()
            }
            
            # Check if exists
            existing = await db.clients.find_one({"codigo": codigo})
            if existing:
                await db.clients.update_one({"codigo": codigo}, {"$set": client_doc})
                updated += 1
            else:
                client_doc["id"] = f"cli-{uuid.uuid4().hex[:8]}"
                client_doc["createdAt"] = datetime.now(timezone.utc).isoformat()
                await db.clients.insert_one(client_doc)
                imported += 1
                
        except Exception as e:
            errors.append(f"Fila {idx+1}: {str(e)}")
    
    return {
        "imported": imported,
        "updated": updated,
        "errors": errors,
        "total": len(clients_data)
    }

@api_router.post("/clients/from-contact/{contact_id}")
async def create_client_from_contact(contact_id: str):
    """Convertir un contacto del CRM en cliente potencial"""
    # Get contact from CRM
    contact = await db.contacts.find_one({"id": contact_id}, {"_id": 0})
    if not contact:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")
    
    # Check if already converted
    existing = await db.clients.find_one({"origenCrmContactId": contact_id})
    if existing:
        raise HTTPException(status_code=400, detail="Este contacto ya fue convertido a cliente")
    
    # Create client from contact data
    client_data = {
        "id": f"cli-{uuid.uuid4().hex[:8]}",
        "tipo": "potencial",
        "codigo": "",  # Sin código hasta que se active
        "nombre": contact.get("name", ""),
        "cif": "",
        "segmento": "",
        "direccion": contact.get("address", ""),
        "localidad": "",
        "provincia": "",
        "codigoPostal": "",
        "telefono": contact.get("phone", ""),
        "email": contact.get("email", ""),
        "descuento": 0,
        "activo": True,
        "notas": f"Convertido desde contacto CRM: {contact.get('company', '')}\n{contact.get('notes', '')}",
        "origenCrmContactId": contact_id,
        "usuarioVinculadoId": "",
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "convertidoAt": None
    }
    
    await db.clients.insert_one(client_data)
    
    # Update contact to mark as converted
    await db.contacts.update_one(
        {"id": contact_id},
        {"$set": {"convertedToClientId": client_data["id"], "status": "customer"}}
    )
    
    if "_id" in client_data:
        del client_data["_id"]
    return client_data

@api_router.post("/clients/{client_id}/activate")
async def activate_client(client_id: str, data: dict):
    """Activar un cliente potencial asignándole código"""
    codigo = data.get("codigo", "").upper().strip()
    if not codigo:
        raise HTTPException(status_code=400, detail="El código es obligatorio para activar")
    
    # Check client exists
    client = await db.clients.find_one({"id": client_id}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    if client.get("tipo") == "activo":
        raise HTTPException(status_code=400, detail="El cliente ya está activo")
    
    # Check code not in use
    existing = await db.clients.find_one({"codigo": codigo, "id": {"$ne": client_id}})
    if existing:
        raise HTTPException(status_code=400, detail="El código ya está en uso por otro cliente")
    
    # Activate
    await db.clients.update_one(
        {"id": client_id},
        {"$set": {
            "tipo": "activo",
            "codigo": codigo,
            "convertidoAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    updated = await db.clients.find_one({"id": client_id}, {"_id": 0})
    return updated

@api_router.post("/clients/{client_id}/link-user")
async def link_client_to_user(client_id: str, data: dict):
    """Vincular un cliente a un usuario del sistema"""
    user_id = data.get("userId", "")
    
    # Verify client exists
    client = await db.clients.find_one({"id": client_id}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    if user_id:
        # Verify user exists
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Update user with client link
        await db.users.update_one(
            {"id": user_id},
            {"$set": {"linkedClientId": client_id}}
        )
    
    # Update client with user link
    await db.clients.update_one(
        {"id": client_id},
        {"$set": {
            "usuarioVinculadoId": user_id,
            "updatedAt": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    updated = await db.clients.find_one({"id": client_id}, {"_id": 0})
    return updated

@api_router.post("/auth/login")
async def login(credentials: dict):
    """Iniciar sesión con verificación de password hasheado"""
    username = credentials.get("username", "").upper().strip()
    password = credentials.get("password", "").strip()
    
    user = await db.users.find_one({"username": username}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Credenciales no válidas")
    
    # Verify password (supports both hashed and plain text for migration)
    if not verify_password(password, user.get("password", "")):
        raise HTTPException(status_code=401, detail="Credenciales no válidas")
    
    if not user.get("isActive", True):
        raise HTTPException(status_code=401, detail="Cuenta desactivada")
    
    # Return user without password
    return {"success": True, "user": user_to_response(user)}

# ============================================
# PRODUCT ENDPOINTS
# ============================================

@api_router.get("/products", response_model=List[ProductModel])
async def get_products(module: Optional[str] = None):
    """Obtener todos los productos, opcionalmente filtrados por módulo"""
    query = {}
    if module:
        query["module"] = module
    products = await db.products.find(query, {"_id": 0}).to_list(10000)
    return products

@api_router.get("/products/{product_id}", response_model=ProductModel)
async def get_product(product_id: str):
    """Obtener un producto por ID"""
    product = await db.products.find_one({"id": product_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product

@api_router.post("/products", response_model=ProductModel)
async def create_product(product: ProductCreate):
    """Crear un nuevo producto"""
    product_obj = ProductModel(**product.model_dump())
    product_obj.code = product_obj.code.upper()
    
    # Set points from Z1 if zonePoints exists
    if product_obj.zonePoints:
        product_obj.points = product_obj.zonePoints.Z1
    
    await db.products.insert_one(product_obj.model_dump())
    return product_obj

@api_router.post("/products/bulk", response_model=List[ProductModel])
async def create_products_bulk(products: List[ProductCreate]):
    """Crear múltiples productos"""
    created = []
    for product in products:
        product_obj = ProductModel(**product.model_dump())
        product_obj.code = product_obj.code.upper()
        if product_obj.zonePoints:
            product_obj.points = product_obj.zonePoints.Z1
        await db.products.insert_one(product_obj.model_dump())
        created.append(product_obj)
    return created

@api_router.put("/products/{product_id}", response_model=ProductModel)
async def update_product(product_id: str, product: ProductCreate):
    """Actualizar un producto"""
    existing = await db.products.find_one({"id": product_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    update_data = product.model_dump()
    update_data["code"] = update_data["code"].upper()
    if update_data.get("zonePoints"):
        update_data["points"] = update_data["zonePoints"]["Z1"]
    
    await db.products.update_one({"id": product_id}, {"$set": update_data})
    updated = await db.products.find_one({"id": product_id}, {"_id": 0})
    return updated

@api_router.delete("/products/{product_id}")
async def delete_product(product_id: str):
    """Eliminar un producto"""
    result = await db.products.delete_one({"id": product_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return {"message": "Producto eliminado"}

@api_router.post("/catalog/extract-products")
async def extract_products_from_catalog(file: UploadFile = File(...)):
    """
    Extraer productos de una imagen de catálogo/tarifa usando Gemini Vision.
    """
    try:
        # Read the image
        file_content = await file.read()
        base64_image = base64.b64encode(file_content).decode('utf-8')
        
        # Detect mime type
        mime_type = file.content_type or 'image/png'
        
        # Create prompt for extraction
        extraction_prompt = """Analiza esta imagen de un catálogo/tarifa de muebles de cocina.
        
Extrae TODOS los productos visibles con la siguiente información:
- codigo_referencia: el código del producto (ej: 35A1P350, 7B1PX300, PTA_ZC89X290)
- nombre: descripción del producto
- puntos_por_zona: objeto con las zonas Z1 a Z12 y sus puntos correspondientes

Responde SOLO con un JSON válido en este formato:
{
  "products": [
    {
      "codigo_referencia": "CODIGO",
      "nombre": "Descripción del mueble",
      "puntos_por_zona": {
        "Z1": 60, "Z2": 62, "Z3": 66, "Z4": 69, "Z5": 76, "Z6": 87,
        "Z7": 93, "Z8": 96, "Z9": 101, "Z10": 122, "Z11": 129, "Z12": 158
      }
    }
  ]
}

Si no hay 12 zonas, incluye solo las que aparezcan. Extrae TODOS los productos de la tabla."""

        # Use Gemini Vision
        chat = LlmChat(
            api_key=os.environ.get('EMERGENT_LLM_KEY'),
            model="gemini/gemini-2.0-flash",
            session_id=f"catalog-extract-{uuid.uuid4().hex[:8]}",
            system_prompt="Eres un extractor de datos de catálogos de muebles. Responde SOLO con JSON válido."
        )
        
        image_content = ImageContent(
            data=base64_image,
            media_type=mime_type
        )
        
        response = await chat.send_message_async(
            UserMessage(content=[extraction_prompt, image_content])
        )
        
        # Parse response
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        # Clean JSON from markdown
        if '```json' in response_text:
            response_text = response_text.split('```json')[1].split('```')[0]
        elif '```' in response_text:
            response_text = response_text.split('```')[1].split('```')[0]
        
        response_text = response_text.strip()
        
        try:
            data = json.loads(response_text)
            products = data.get('products', [])
        except json.JSONDecodeError:
            # Try to find JSON in response
            import re
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                data = json.loads(json_match.group())
                products = data.get('products', [])
            else:
                products = []
        
        logger.info(f"Extracted {len(products)} products from catalog image")
        return {"success": True, "products": products}
        
    except Exception as e:
        logger.error(f"Catalog extraction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/products/fix-heights")
async def fix_product_heights():
    """
    Corregir alturas de productos que están en decímetros en vez de centímetros.
    Multiplica por 10 las alturas que son <= 30 (11, 12, 13, 14, 16, 20, 22, 24)
    """
    # Alturas que deberían multiplicarse por 10
    heights_to_fix = [11, 12, 13, 14, 16, 20, 22, 24]
    
    fixed_count = 0
    for h in heights_to_fix:
        result = await db.products.update_many(
            {"height": h},
            {"$mul": {"height": 10}}
        )
        fixed_count += result.modified_count
        logger.info(f"Fixed {result.modified_count} products with height {h} -> {h*10}")
    
    # También corregir fondos si es necesario (33 -> 330 sería incorrecto, pero 33cm es normal)
    # Los fondos de 33 parecen correctos (330mm = 33cm)
    
    return {
        "success": True,
        "fixed_count": fixed_count,
        "message": f"Se corrigieron {fixed_count} productos"
    }

@api_router.post("/products/fix-semicolumna-names")
async def fix_semicolumna_names():
    """
    Corregir nombres de semicolumnas: 11cm -> 110cm, 12cm -> 120cm, etc.
    """
    fixes = {
        "Semicolumna 11cm": "Semicolumna 110cm",
        "Semicolumna 12cm": "Semicolumna 120cm",
        "Semicolumna 13cm": "Semicolumna 130cm",
        "Semicolumna 14cm": "Semicolumna 140cm",
        "Semicolumna 16cm": "Semicolumna 160cm",
        "Semicolumna 20cm": "Semicolumna 200cm",
        "Semicolumna 22cm": "Semicolumna 220cm",
        "Semicolumna 24cm": "Semicolumna 240cm",
    }
    
    fixed_count = 0
    for wrong, correct in fixes.items():
        # Find products with wrong name pattern
        cursor = db.products.find({"name": {"$regex": wrong, "$options": "i"}})
        products = await cursor.to_list(1000)
        
        for p in products:
            new_name = p['name'].replace(wrong, correct)
            await db.products.update_one(
                {"id": p['id']},
                {"$set": {"name": new_name}}
            )
            fixed_count += 1
            logger.info(f"Fixed: {p['code']}: {p['name']} -> {new_name}")
    
    return {
        "success": True,
        "fixed_count": fixed_count,
        "message": f"Se corrigieron {fixed_count} nombres de semicolumnas"
    }

@api_router.post("/products/fix-names")
async def fix_product_names():
    """
    Corregir nombres de productos para unificar unidades a centímetros.
    - Convierte '580cm' a '58cm', '330cm' a '33cm'
    - Convierte 'XXXmm' a 'XXcm' en anchos
    """
    import re
    
    products = await db.products.find({}, {"_id": 0}).to_list(10000)
    fixed_count = 0
    
    for p in products:
        name = p.get('name', '')
        original_name = name
        
        # Corregir fondos incorrectos (580cm -> 58cm, 330cm -> 33cm)
        name = re.sub(r'580\s*cm', '58cm', name, flags=re.IGNORECASE)
        name = re.sub(r'330\s*cm', '33cm', name, flags=re.IGNORECASE)
        
        # Convertir anchos de mm a cm (400mm -> 40cm, 350mm -> 35cm, etc.)
        def mm_to_cm(match):
            mm_val = int(match.group(1))
            cm_val = mm_val // 10
            return f'{cm_val}cm'
        
        name = re.sub(r'(\d{3,4})\s*mm', mm_to_cm, name, flags=re.IGNORECASE)
        
        # También en el código si tiene unidades
        code = p.get('code', '')
        
        if name != original_name:
            await db.products.update_one(
                {"id": p['id']},
                {"$set": {"name": name}}
            )
            fixed_count += 1
    
    return {
        "success": True,
        "fixed_count": fixed_count,
        "message": f"Se corrigieron {fixed_count} nombres de productos"
    }

@api_router.delete("/products/bulk/delete")
async def delete_products_bulk(product_ids: List[str]):
    """Eliminar múltiples productos"""
    result = await db.products.delete_many({"id": {"$in": product_ids}})
    return {"message": f"{result.deleted_count} productos eliminados"}

# ============================================
# MATERIAL ENDPOINTS
# ============================================

@api_router.get("/materials", response_model=List[MaterialModel])
async def get_materials():
    """Obtener todos los materiales"""
    materials = await db.materials.find({}, {"_id": 0}).to_list(1000)
    return materials

@api_router.post("/materials", response_model=MaterialModel)
async def create_material(material: MaterialCreate):
    """Crear un nuevo material"""
    material_obj = MaterialModel(**material.model_dump())
    await db.materials.insert_one(material_obj.model_dump())
    return material_obj

@api_router.put("/materials/{material_id}", response_model=MaterialModel)
async def update_material(material_id: str, material: MaterialCreate):
    """Actualizar un material"""
    existing = await db.materials.find_one({"id": material_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Material no encontrado")
    
    await db.materials.update_one({"id": material_id}, {"$set": material.model_dump()})
    updated = await db.materials.find_one({"id": material_id}, {"_id": 0})
    return updated

@api_router.delete("/materials/{material_id}")
async def delete_material(material_id: str):
    """Eliminar un material"""
    # Check if it's the last one
    count = await db.materials.count_documents({})
    if count <= 1:
        raise HTTPException(status_code=400, detail="Debe existir al menos un material")
    
    result = await db.materials.delete_one({"id": material_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Material no encontrado")
    return {"message": "Material eliminado"}

# ============================================
# SETTINGS ENDPOINTS
# ============================================

@api_router.get("/expedient/next")
async def get_next_expedient_number():
    """
    Obtener el siguiente número de expediente correlativo.
    Formato: EXP-AAAA-NNNNN (ej: EXP-2026-00001)
    """
    try:
        year = datetime.now().year
        
        # Obtener o crear el contador de expedientes
        counter = await db.system_counters.find_one({"key": f"expedient_{year}"})
        
        if not counter:
            # Crear contador para el año actual empezando en 1
            counter = {
                "key": f"expedient_{year}",
                "value": 0,
                "year": year
            }
            await db.system_counters.insert_one(counter)
        
        # Incrementar el contador atómicamente
        result = await db.system_counters.find_one_and_update(
            {"key": f"expedient_{year}"},
            {"$inc": {"value": 1}},
            return_document=True
        )
        
        next_number = result["value"]
        expedient = f"EXP-{year}-{next_number:05d}"
        
        return {
            "success": True,
            "expedient": expedient,
            "number": next_number,
            "year": year
        }
    except Exception as e:
        logger.error(f"Error getting next expedient: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo número de expediente: {str(e)}")

@api_router.get("/expedient/current")
async def get_current_expedient_info():
    """Obtener información del contador de expedientes actual"""
    try:
        year = datetime.now().year
        counter = await db.system_counters.find_one({"key": f"expedient_{year}"})
        
        current = counter["value"] if counter else 0
        
        return {
            "success": True,
            "year": year,
            "currentCount": current,
            "nextExpedient": f"EXP-{year}-{current + 1:05d}"
        }
    except Exception as e:
        logger.error(f"Error getting expedient info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/settings", response_model=SettingsModel)
async def get_settings():
    """Obtener configuración global"""
    settings = await db.settings.find_one({"id": "global-settings"}, {"_id": 0})
    if not settings:
        # Return defaults
        return SettingsModel()
    return settings

@api_router.put("/settings", response_model=SettingsModel)
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

# ============================================
# PROJECT/BUDGET ENDPOINTS
# ============================================

@api_router.get("/projects", response_model=List[ProjectModel])
async def get_projects(user_id: Optional[str] = None):
    """Obtener proyectos, opcionalmente filtrados por usuario"""
    query = {}
    if user_id:
        query["userId"] = user_id
    projects = await db.projects.find(query, {"_id": 0}).to_list(1000)
    return projects

@api_router.get("/admin/all-work")
async def get_all_work_for_admin():
    """
    [ADMIN ONLY] Obtener todos los trabajos de todos los usuarios.
    Incluye proyectos, oportunidades y digitalizaciones.
    """
    # Get all projects grouped by user
    projects = await db.projects.find({}, {"_id": 0}).to_list(5000)
    
    # Get all opportunities
    opportunities = await db.opportunities.find({}, {"_id": 0}).to_list(5000)
    
    # Get all digitalizador history
    digitalizaciones = await db.digitalizador_history.find({}, {"_id": 0}).to_list(5000)
    
    # Get all users for reference
    users = await db.users.find({}, {"_id": 0, "password": 0}).to_list(500)
    users_map = {u["id"]: u for u in users}
    
    # Enrich projects with user info
    for proj in projects:
        user = users_map.get(proj.get("userId", ""))
        proj["userName"] = user.get("username", "Desconocido") if user else "Desconocido"
        proj["userClientName"] = user.get("clientName", "") if user else ""
    
    # Enrich opportunities with user info
    for opp in opportunities:
        user = users_map.get(opp.get("assignedTo", ""))
        opp["userName"] = user.get("username", "Desconocido") if user else "Sin asignar"
    
    # Enrich digitalizaciones with user info
    for dig in digitalizaciones:
        user = users_map.get(dig.get("createdBy", ""))
        dig["userName"] = user.get("username", "Desconocido") if user else "Desconocido"
    
    return {
        "projects": projects,
        "opportunities": opportunities,
        "digitalizaciones": digitalizaciones,
        "users": users,
        "summary": {
            "totalProjects": len(projects),
            "totalOpportunities": len(opportunities),
            "totalDigitalizaciones": len(digitalizaciones),
            "totalUsers": len(users)
        }
    }

@api_router.get("/admin/metrics")
async def get_admin_metrics():
    """
    [DIRECTOR COMERCIAL ONLY] Métricas completas del sistema por delegación y comercial.
    Incluye ventas, oportunidades, rendimiento de comerciales, etc.
    """
    from datetime import timedelta
    
    # Get all users
    users = await db.users.find({}, {"_id": 0, "password": 0}).to_list(500)
    users_map = {u["id"]: u for u in users}
    
    # Separar usuarios por rol
    directores = [u for u in users if u.get("isAdmin")]
    responsables = [u for u in users if u.get("isResponsableDelegacion")]
    comerciales = [u for u in users if u.get("isRepresentative")]
    tiendas = [u for u in users if u.get("isTienda")]
    colaboradores = [u for u in users if u.get("isPrescriptor")]
    
    # Get all opportunities
    opportunities = await db.opportunities.find({}, {"_id": 0}).to_list(5000)
    
    # Get all projects
    projects = await db.projects.find({}, {"_id": 0}).to_list(5000)
    
    # Get all contacts
    contacts = await db.contacts.find({}, {"_id": 0}).to_list(5000)
    
    # Calcular métricas por comercial/responsable
    metrics_by_user = {}
    
    for user in comerciales + responsables:
        user_id = user["id"]
        
        # Oportunidades asignadas a este usuario
        user_opps = [o for o in opportunities if o.get("assignedTo") == user_id]
        won_opps = [o for o in user_opps if o.get("stage") == "won"]
        active_opps = [o for o in user_opps if o.get("stage") not in ["won", "lost"]]
        
        # Valor total
        total_value = sum(o.get("value", 0) for o in won_opps)
        pipeline_value = sum(o.get("value", 0) for o in active_opps)
        
        # Contactos asignados
        user_contacts = [c for c in contacts if c.get("assignedTo") == user_id]
        
        # Tiendas bajo su gestión
        user_shops = [t for t in tiendas if t.get("linkedRepresentativeId") == user_id]
        
        # Proyectos de sus tiendas
        shop_ids = [s["id"] for s in user_shops]
        user_projects = [p for p in projects if p.get("userId") in shop_ids or p.get("userId") == user_id]
        
        metrics_by_user[user_id] = {
            "userId": user_id,
            "userName": user.get("clientName", user.get("username", "Desconocido")),
            "role": "Resp. Delegación" if user.get("isResponsableDelegacion") else "Comercial",
            "totalOpportunities": len(user_opps),
            "wonOpportunities": len(won_opps),
            "activeOpportunities": len(active_opps),
            "totalValue": total_value,
            "pipelineValue": pipeline_value,
            "conversionRate": round(len(won_opps) / len(user_opps) * 100, 1) if user_opps else 0,
            "totalContacts": len(user_contacts),
            "totalShops": len(user_shops),
            "totalProjects": len(user_projects),
            "shops": [{"id": s["id"], "name": s.get("clientName", s.get("username"))} for s in user_shops]
        }
    
    # Métricas globales
    all_won = [o for o in opportunities if o.get("stage") == "won"]
    all_active = [o for o in opportunities if o.get("stage") not in ["won", "lost"]]
    
    global_metrics = {
        "totalUsers": len(users),
        "totalDirectores": len(directores),
        "totalResponsables": len(responsables),
        "totalComerciales": len(comerciales),
        "totalTiendas": len(tiendas),
        "totalColaboradores": len(colaboradores),
        "totalOpportunities": len(opportunities),
        "wonOpportunities": len(all_won),
        "activeOpportunities": len(all_active),
        "totalValue": sum(o.get("value", 0) for o in all_won),
        "pipelineValue": sum(o.get("value", 0) for o in all_active),
        "totalProjects": len(projects),
        "totalContacts": len(contacts),
        "conversionRate": round(len(all_won) / len(opportunities) * 100, 1) if opportunities else 0
    }
    
    # Top performers (ordenados por valor total)
    top_performers = sorted(
        metrics_by_user.values(), 
        key=lambda x: x["totalValue"], 
        reverse=True
    )[:10]
    
    return {
        "global": global_metrics,
        "byUser": list(metrics_by_user.values()),
        "topPerformers": top_performers,
        "roleBreakdown": {
            "directores": len(directores),
            "responsables": len(responsables),
            "comerciales": len(comerciales),
            "tiendas": len(tiendas),
            "colaboradores": len(colaboradores)
        }
    }

@api_router.get("/commercial/my-shops-work")
async def get_commercial_shops_work(commercial_id: str):
    """
    [COMERCIAL ONLY] Obtener todos los trabajos de las tiendas asignadas a este comercial.
    """
    # Get users (shops) assigned to this commercial
    shops = await db.users.find(
        {"linkedRepresentativeId": commercial_id},
        {"_id": 0, "password": 0}
    ).to_list(500)
    
    shop_ids = [s["id"] for s in shops]
    
    # Get projects from these shops
    projects = await db.projects.find(
        {"userId": {"$in": shop_ids}},
        {"_id": 0}
    ).to_list(5000)
    
    # Get opportunities assigned to or created by these shops
    opportunities = await db.opportunities.find(
        {"$or": [
            {"assignedTo": {"$in": shop_ids}},
            {"createdBy": {"$in": shop_ids}}
        ]},
        {"_id": 0}
    ).to_list(5000)
    
    # Enrich with shop info
    shops_map = {s["id"]: s for s in shops}
    
    for proj in projects:
        shop = shops_map.get(proj.get("userId", ""))
        proj["shopName"] = shop.get("clientName", "Desconocido") if shop else "Desconocido"
        proj["shopUsername"] = shop.get("username", "") if shop else ""
    
    for opp in opportunities:
        shop = shops_map.get(opp.get("assignedTo", ""))
        opp["shopName"] = shop.get("clientName", "Sin asignar") if shop else "Sin asignar"
    
    return {
        "shops": shops,
        "projects": projects,
        "opportunities": opportunities,
        "summary": {
            "totalShops": len(shops),
            "totalProjects": len(projects),
            "totalOpportunities": len(opportunities)
        }
    }

@api_router.get("/projects/{project_id}", response_model=ProjectModel)
async def get_project(project_id: str):
    """Obtener un proyecto por ID"""
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return project

@api_router.post("/projects", response_model=ProjectModel)
async def create_project(project: ProjectCreate, user_id: str):
    """Crear un nuevo proyecto"""
    project_data = project.model_dump()
    project_data["id"] = f"proj-{uuid.uuid4().hex[:8]}"
    project_data["userId"] = user_id
    project_data["createdAt"] = datetime.now(timezone.utc).isoformat()
    project_data["updatedAt"] = datetime.now(timezone.utc).isoformat()
    
    await db.projects.insert_one(project_data)
    return project_data

@api_router.put("/projects/{project_id}", response_model=ProjectModel)
async def update_project(project_id: str, project: ProjectUpdate):
    """Actualizar un proyecto"""
    existing = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    update_data = {k: v for k, v in project.model_dump().items() if v is not None}
    update_data["updatedAt"] = datetime.now(timezone.utc).isoformat()
    
    if update_data:
        await db.projects.update_one({"id": project_id}, {"$set": update_data})
    
    updated = await db.projects.find_one({"id": project_id}, {"_id": 0})
    return updated

@api_router.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    """Eliminar un proyecto"""
    result = await db.projects.delete_one({"id": project_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return {"message": "Proyecto eliminado"}

# ============================================
# INIT DATA (seed admin user if needed)
# ============================================

@api_router.post("/init")
async def init_data():
    """Inicializar datos base (admin user con password hasheado)"""
    # Check if admin exists
    admin = await db.users.find_one({"id": "admin"})
    if not admin:
        admin_data = {
            "id": "admin",
            "username": "MARIO",
            "password": hash_password("MARIO"),  # Hash the password
            "clientName": "LUIGGI MASTER DESIGN",
            "isActive": True,
            "isAdmin": True,
            "isRepresentative": False,
            "linkedRepresentativeId": None,
            "allowedModules": ["montada", "despiece"],
            "allowedCatalogIds": ["cat-m-base", "cat-d-base"],
            "commercialDiscount": 45,
            "canSeeCost": True,
            "canSeeRetail": True,
            "canUseAIAnalysis": True,
            "canManageArticles": True,
            "canViewTechnicalDespiece": True,
            "canAccessCRM": True,
            "useCustomBranding": True,
            "canChangeLogo": True
        }
        await db.users.insert_one(admin_data)
        return {"message": "Admin creado", "admin": user_to_response(admin_data)}
    
    # If admin exists with plain text password, update to hashed
    if admin.get("password") and not admin["password"].startswith("$2"):
        hashed = hash_password(admin["password"])
        await db.users.update_one({"id": "admin"}, {"$set": {"password": hashed}})
        return {"message": "Admin password actualizado a hash"}
    
    return {"message": "Admin ya existe"}

# ============================================
# BACKUP SYSTEM
# ============================================

# Scheduler for automatic backups
scheduler = AsyncIOScheduler()

async def create_backup_data():
    """Creates a JSON backup of all database collections"""
    backup = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0",
        "data": {}
    }
    
    # Export all collections
    collections = ["users", "products", "materials", "projects", "settings", "status_checks"]
    
    for collection_name in collections:
        try:
            docs = await db[collection_name].find({}, {"_id": 0}).to_list(10000)
            backup["data"][collection_name] = docs
            logger.info(f"Backup: {collection_name} - {len(docs)} documentos")
        except Exception as e:
            logger.error(f"Error backing up {collection_name}: {e}")
            backup["data"][collection_name] = []
    
    return backup

def send_backup_email(backup_data: dict, backup_type: str = "automático"):
    """Sends backup via SendGrid email with JSON attachment"""
    try:
        sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')
        backup_email = os.environ.get('BACKUP_EMAIL', 'marioluiggihome@gmail.com')
        
        if not sendgrid_api_key:
            logger.error("SENDGRID_API_KEY not configured")
            return False
        
        # Create JSON content
        json_content = json.dumps(backup_data, indent=2, ensure_ascii=False, default=str)
        encoded_content = base64.b64encode(json_content.encode('utf-8')).decode('utf-8')
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"luiggi_home_backup_{timestamp}.json"
        
        # Count items
        total_items = sum(len(backup_data.get("data", {}).get(col, [])) for col in backup_data.get("data", {}).keys())
        
        # Create email message
        message = Mail(
            from_email=backup_email,
            to_emails=backup_email,
            subject=f"🏠 LUIGGI HOME - Backup {backup_type} ({timestamp})",
            html_content=f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #1e293b 0%, #334155 100%); color: white; padding: 30px; border-radius: 10px 10px 0 0;">
                    <h1 style="margin: 0; font-size: 24px;">🏠 LUIGGI HOME</h1>
                    <p style="margin: 10px 0 0 0; opacity: 0.8; font-size: 14px;">Copia de Seguridad {backup_type.upper()}</p>
                </div>
                
                <div style="background: #f8fafc; padding: 30px; border: 1px solid #e2e8f0; border-top: none;">
                    <h2 style="color: #1e293b; margin-top: 0;">✅ Backup completado</h2>
                    
                    <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                        <tr style="background: #e2e8f0;">
                            <td style="padding: 10px; font-weight: bold;">📅 Fecha</td>
                            <td style="padding: 10px;">{datetime.now().strftime("%d/%m/%Y %H:%M:%S")}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; font-weight: bold;">📦 Total registros</td>
                            <td style="padding: 10px;">{total_items}</td>
                        </tr>
                        <tr style="background: #e2e8f0;">
                            <td style="padding: 10px; font-weight: bold;">📄 Archivo</td>
                            <td style="padding: 10px;">{filename}</td>
                        </tr>
                    </table>
                    
                    <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0;">
                        <strong>⚠️ Importante:</strong> Guarda este archivo en tu Google Drive para mantener tus datos seguros.
                    </div>
                    
                    <h3 style="color: #1e293b;">📊 Detalle del backup:</h3>
                    <ul style="list-style: none; padding: 0;">
                        {"".join([f'<li style="padding: 5px 0;">• {col}: {len(backup_data.get("data", {}).get(col, []))} registros</li>' for col in backup_data.get("data", {}).keys()])}
                    </ul>
                </div>
                
                <div style="background: #1e293b; color: white; padding: 20px; border-radius: 0 0 10px 10px; text-align: center; font-size: 12px;">
                    <p style="margin: 0;">LUIGGI HOME Master Design v2026</p>
                    <p style="margin: 5px 0 0 0; opacity: 0.7;">Sistema de Gestión de Presupuestos de Cocina</p>
                </div>
            </body>
            </html>
            """
        )
        
        # Create attachment
        attachment = Attachment()
        attachment.file_content = FileContent(encoded_content)
        attachment.file_name = FileName(filename)
        attachment.file_type = FileType('application/json')
        attachment.disposition = Disposition('attachment')
        message.attachment = attachment
        
        # Send email
        sg = SendGridAPIClient(sendgrid_api_key)
        response = sg.send(message)
        
        if response.status_code == 202:
            logger.info(f"Backup email sent successfully to {backup_email}")
            return True
        else:
            logger.error(f"Backup email failed with status {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending backup email: {e}")
        return False

async def scheduled_backup_task():
    """Async task for scheduled backups"""
    logger.info("Starting scheduled backup...")
    try:
        backup_data = await create_backup_data()
        # Run email sending in thread pool since SendGrid is sync
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, send_backup_email, backup_data, "automático")
        if result:
            logger.info("Scheduled backup completed successfully")
        else:
            logger.error("Scheduled backup failed to send email")
    except Exception as e:
        logger.error(f"Scheduled backup error: {e}")

# Backup History Model
class BackupHistoryModel(BaseModel):
    id: str = Field(default_factory=lambda: f"backup-{uuid.uuid4().hex[:8]}")
    timestamp: str
    type: str  # manual, scheduled
    status: str  # success, failed
    itemCount: int
    sentTo: str

# ============================================
# BACKUP API ENDPOINTS
# ============================================

@api_router.post("/backup/manual")
async def trigger_manual_backup(background_tasks: BackgroundTasks):
    """Trigger a manual backup and send via email"""
    try:
        backup_data = await create_backup_data()
        
        # Count items
        total_items = sum(len(backup_data.get("data", {}).get(col, [])) for col in backup_data.get("data", {}).keys())
        
        # Send email in background
        background_tasks.add_task(send_backup_email, backup_data, "manual")
        
        # Save to backup history
        history_entry = {
            "id": f"backup-{uuid.uuid4().hex[:8]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "manual",
            "status": "success",
            "itemCount": total_items,
            "sentTo": os.environ.get('BACKUP_EMAIL', 'marioluiggihome@gmail.com')
        }
        await db.backup_history.insert_one(history_entry)
        
        return {
            "status": "success",
            "message": f"Backup enviado a {history_entry['sentTo']}",
            "itemCount": total_items,
            "timestamp": history_entry['timestamp']
        }
    except Exception as e:
        logger.error(f"Manual backup error: {e}")
        raise HTTPException(status_code=500, detail=f"Error al crear backup: {str(e)}")

@api_router.get("/backup/download")
async def download_backup():
    """Download backup as JSON file (for manual save to Google Drive)"""
    try:
        backup_data = await create_backup_data()
        return backup_data
    except Exception as e:
        logger.error(f"Download backup error: {e}")
        raise HTTPException(status_code=500, detail=f"Error al descargar backup: {str(e)}")

@api_router.post("/backup/restore")
async def restore_backup(backup_data: Dict):
    """Restore data from a backup file"""
    try:
        if "data" not in backup_data:
            raise HTTPException(status_code=400, detail="Formato de backup inválido")
        
        restored_counts = {}
        
        for collection_name, documents in backup_data["data"].items():
            if collection_name in ["users", "products", "materials", "projects", "settings"]:
                # Clear existing data
                await db[collection_name].delete_many({})
                
                # Insert backup data
                if documents:
                    await db[collection_name].insert_many(documents)
                
                restored_counts[collection_name] = len(documents)
                logger.info(f"Restored {collection_name}: {len(documents)} documents")
        
        return {
            "status": "success",
            "message": "Backup restaurado correctamente",
            "restored": restored_counts
        }
    except Exception as e:
        logger.error(f"Restore backup error: {e}")
        raise HTTPException(status_code=500, detail=f"Error al restaurar backup: {str(e)}")

@api_router.get("/backup/history")
async def get_backup_history():
    """Get backup history"""
    try:
        history = await db.backup_history.find({}, {"_id": 0}).sort("timestamp", -1).to_list(50)
        return history
    except Exception as e:
        logger.error(f"Get backup history error: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener historial: {str(e)}")

@api_router.get("/backup/status")
async def get_backup_status():
    """Get backup scheduler status"""
    jobs = scheduler.get_jobs()
    return {
        "scheduler_running": scheduler.running,
        "next_backups": [
            {
                "job_id": job.id,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None
            }
            for job in jobs
        ],
        "backup_email": os.environ.get('BACKUP_EMAIL', 'marioluiggihome@gmail.com')
    }

# ============================================
# CRM API ENDPOINTS - Contactos
# ============================================

@api_router.get("/crm/contacts")
async def get_contacts(status: Optional[str] = None, search: Optional[str] = None, assignedTo: Optional[str] = None, isAdmin: Optional[bool] = True):
    """Get all contacts with optional filters, including total value from opportunities
    
    Para usuarios NO admin (comerciales/representantes), solo devuelve contactos asignados a ellos.
    assignedTo: ID del usuario comercial para filtrar sus contactos asignados
    isAdmin: Si es False, solo devuelve contactos del comercial asignado
    """
    try:
        query = {}
        if status:
            query["status"] = status
        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"company": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}}
            ]
        
        # IMPORTANTE: Si NO es admin y tiene assignedTo, filtrar solo sus contactos
        if not isAdmin and assignedTo:
            query["assignedTo"] = assignedTo
        
        contacts = await db.contacts.find(query, {"_id": 0}).sort("createdAt", -1).to_list(1000)
        
        # Calcular totalValue para cada contacto basado en sus oportunidades
        if contacts:
            contact_ids = [c.get("id") for c in contacts]
            # Obtener todas las oportunidades de estos contactos
            opportunities = await db.opportunities.find(
                {"contactId": {"$in": contact_ids}},
                {"_id": 0, "contactId": 1, "value": 1}
            ).to_list(5000)
            
            # Agrupar valores por contactId
            values_by_contact = {}
            for opp in opportunities:
                cid = opp.get("contactId")
                if cid:
                    if cid not in values_by_contact:
                        values_by_contact[cid] = 0
                    values_by_contact[cid] += opp.get("value", 0)
            
            # Añadir totalValue a cada contacto
            for contact in contacts:
                contact["totalValue"] = values_by_contact.get(contact.get("id"), 0)
        
        return contacts
    except Exception as e:
        logger.error(f"Get contacts error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/crm/contacts/{contact_id}")
async def get_contact(contact_id: str):
    """Get a single contact by ID"""
    contact = await db.contacts.find_one({"id": contact_id}, {"_id": 0})
    if not contact:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")
    return contact

@api_router.post("/crm/contacts")
async def create_contact(contact: ContactCreate):
    """Create a new contact"""
    try:
        contact_dict = contact.model_dump()
        contact_obj = ContactModel(**contact_dict)
        doc = contact_obj.model_dump()
        doc['createdAt'] = doc['createdAt'].isoformat()
        doc['updatedAt'] = doc['updatedAt'].isoformat()
        
        await db.contacts.insert_one(doc)
        doc.pop('_id', None)
        return doc
    except Exception as e:
        logger.error(f"Create contact error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/crm/contacts/{contact_id}")
async def update_contact(contact_id: str, contact: ContactUpdate):
    """Update an existing contact"""
    try:
        update_data = {k: v for k, v in contact.model_dump().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=400, detail="No hay datos para actualizar")
        
        update_data['updatedAt'] = datetime.now(timezone.utc).isoformat()
        
        result = await db.contacts.update_one(
            {"id": contact_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Contacto no encontrado")
        
        updated = await db.contacts.find_one({"id": contact_id}, {"_id": 0})
        return updated
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update contact error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/crm/contacts/{contact_id}")
async def delete_contact(contact_id: str):
    """Delete a contact"""
    result = await db.contacts.delete_one({"id": contact_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")
    return {"message": "Contacto eliminado", "id": contact_id}

@api_router.get("/crm/contacts/by-prescriptor/{prescriptor_id}")
async def get_contacts_by_prescriptor(prescriptor_id: str):
    """Get all contacts referred by a specific prescriptor"""
    try:
        contacts = await db.contacts.find(
            {"prescriptorId": prescriptor_id},
            {"_id": 0}
        ).sort("createdAt", -1).to_list(1000)
        return contacts
    except Exception as e:
        logger.error(f"Get contacts by prescriptor error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/crm/prescriptors")
async def get_prescriptors():
    """Get all users who are prescriptors"""
    try:
        prescriptors = await db.users.find(
            {"isPrescriptor": True, "isActive": True},
            {"_id": 0, "password": 0}
        ).to_list(100)
        return prescriptors
    except Exception as e:
        logger.error(f"Get prescriptors error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/crm/prescriptors/{prescriptor_id}/stats")
async def get_prescriptor_stats(prescriptor_id: str):
    """Get statistics for a prescriptor's referred contacts"""
    try:
        # Get all contacts referred by this prescriptor
        contacts = await db.contacts.find(
            {"prescriptorId": prescriptor_id},
            {"_id": 0}
        ).to_list(1000)
        
        # Count by segment
        segments_count = {}
        for contact in contacts:
            seg = contact.get("segment", "SIN SEGMENTO")
            segments_count[seg] = segments_count.get(seg, 0) + 1
        
        # Count by status
        status_count = {}
        for contact in contacts:
            status = contact.get("status", "lead")
            status_count[status] = status_count.get(status, 0) + 1
        
        # Count converted to client
        converted_count = len([c for c in contacts if c.get("convertedToClientId")])
        
        # Get opportunities value from these contacts
        contact_ids = [c.get("id") for c in contacts]
        opportunities = await db.opportunities.find(
            {"contactId": {"$in": contact_ids}},
            {"_id": 0, "value": 1, "stage": 1}
        ).to_list(1000)
        
        total_value = sum(o.get("value", 0) for o in opportunities)
        won_value = sum(o.get("value", 0) for o in opportunities if o.get("stage") == "won")
        
        return {
            "totalContacts": len(contacts),
            "convertedToClient": converted_count,
            "bySegment": segments_count,
            "byStatus": status_count,
            "totalOpportunitiesValue": total_value,
            "wonOpportunitiesValue": won_value
        }
    except Exception as e:
        logger.error(f"Get prescriptor stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# PRESCRIPTOR NOTES (Calendar Notes)
# ============================================

class PrescriptorNoteCreate(BaseModel):
    title: str = ""
    content: str = ""
    date: str  # YYYY-MM-DD format
    prescriptorId: str
    prescriptorName: str = ""
    contactId: Optional[str] = None
    contactName: Optional[str] = None

class PrescriptorNoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    date: Optional[str] = None
    contactId: Optional[str] = None
    contactName: Optional[str] = None

@api_router.get("/prescriptor/notes")
async def get_prescriptor_notes(
    prescriptor_id: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
    view_all: bool = False
):
    """Get calendar notes for a prescriptor or all prescriptors (admin)"""
    try:
        query = {}
        
        # If not viewing all, filter by prescriptor
        if not view_all:
            query["prescriptorId"] = prescriptor_id
        
        # Date range filter
        if start and end:
            query["date"] = {"$gte": start, "$lte": end}
        
        notes = await db.prescriptor_notes.find(query, {"_id": 0}).sort("date", 1).to_list(500)
        return notes
    except Exception as e:
        logger.error(f"Get prescriptor notes error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/prescriptor/notes")
async def create_prescriptor_note(note: PrescriptorNoteCreate):
    """Create a new calendar note for prescriptor"""
    try:
        note_dict = note.model_dump()
        note_dict["id"] = f"pnote-{uuid.uuid4().hex[:8]}"
        note_dict["createdAt"] = datetime.now(timezone.utc).isoformat()
        note_dict["updatedAt"] = datetime.now(timezone.utc).isoformat()
        
        await db.prescriptor_notes.insert_one(note_dict)
        note_dict.pop("_id", None)
        return note_dict
    except Exception as e:
        logger.error(f"Create prescriptor note error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/prescriptor/notes/{note_id}")
async def update_prescriptor_note(note_id: str, note: PrescriptorNoteUpdate):
    """Update a prescriptor calendar note"""
    try:
        update_data = {k: v for k, v in note.model_dump().items() if v is not None}
        update_data["updatedAt"] = datetime.now(timezone.utc).isoformat()
        
        result = await db.prescriptor_notes.update_one(
            {"id": note_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Nota no encontrada")
        
        updated = await db.prescriptor_notes.find_one({"id": note_id}, {"_id": 0})
        return updated
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update prescriptor note error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/prescriptor/notes/{note_id}")
async def delete_prescriptor_note(note_id: str):
    """Delete a prescriptor calendar note"""
    try:
        result = await db.prescriptor_notes.delete_one({"id": note_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Nota no encontrada")
        return {"message": "Nota eliminada correctamente"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete prescriptor note error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/prescriptor/notes/all")
async def get_all_prescriptor_notes(
    start: Optional[str] = None,
    end: Optional[str] = None
):
    """Get all prescriptor notes (for admin CRM calendar view)"""
    try:
        query = {}
        if start and end:
            query["date"] = {"$gte": start, "$lte": end}
        
        notes = await db.prescriptor_notes.find(query, {"_id": 0}).sort("date", 1).to_list(1000)
        return notes
    except Exception as e:
        logger.error(f"Get all prescriptor notes error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# CRM API ENDPOINTS - Oportunidades
# ============================================

@api_router.get("/crm/opportunities")
async def get_opportunities(stage: Optional[str] = None, contactId: Optional[str] = None, assignedTo: Optional[str] = None, isAdmin: Optional[bool] = True):
    """Get all opportunities with optional filters
    
    Para usuarios NO admin (comerciales/representantes), solo devuelve oportunidades asignadas a ellos.
    assignedTo: ID del usuario comercial para filtrar sus oportunidades
    isAdmin: Si es False, solo devuelve oportunidades del comercial asignado
    """
    try:
        query = {}
        if stage:
            query["stage"] = stage
        if contactId:
            query["contactId"] = contactId
        
        # IMPORTANTE: Si NO es admin y tiene assignedTo, filtrar solo sus oportunidades
        if not isAdmin and assignedTo:
            query["assignedTo"] = assignedTo
        
        opportunities = await db.opportunities.find(query, {"_id": 0}).sort("createdAt", -1).to_list(1000)
        return opportunities
    except Exception as e:
        logger.error(f"Get opportunities error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/crm/opportunities/{opp_id}")
async def get_opportunity(opp_id: str):
    """Get a single opportunity by ID"""
    opp = await db.opportunities.find_one({"id": opp_id}, {"_id": 0})
    if not opp:
        raise HTTPException(status_code=404, detail="Oportunidad no encontrada")
    return opp

@api_router.post("/crm/opportunities")
async def create_opportunity(opportunity: OpportunityCreate):
    """Create a new opportunity"""
    try:
        opp_dict = opportunity.model_dump()
        opp_obj = OpportunityModel(**opp_dict)
        doc = opp_obj.model_dump()
        doc['createdAt'] = doc['createdAt'].isoformat()
        doc['updatedAt'] = doc['updatedAt'].isoformat()
        if doc.get('closedAt'):
            doc['closedAt'] = doc['closedAt'].isoformat()
        
        await db.opportunities.insert_one(doc)
        doc.pop('_id', None)
        return doc
    except Exception as e:
        logger.error(f"Create opportunity error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/crm/opportunities/{opp_id}")
async def update_opportunity(opp_id: str, opportunity: OpportunityUpdate):
    """Update an existing opportunity"""
    try:
        update_data = {k: v for k, v in opportunity.model_dump().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=400, detail="No hay datos para actualizar")
        
        update_data['updatedAt'] = datetime.now(timezone.utc).isoformat()
        
        # If stage changed to won/lost, set closedAt
        if update_data.get('stage') in ['won', 'lost']:
            update_data['closedAt'] = datetime.now(timezone.utc).isoformat()
        
        result = await db.opportunities.update_one(
            {"id": opp_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Oportunidad no encontrada")
        
        updated = await db.opportunities.find_one({"id": opp_id}, {"_id": 0})
        return updated
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update opportunity error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/crm/opportunities/{opp_id}")
async def delete_opportunity(opp_id: str):
    """Delete an opportunity"""
    result = await db.opportunities.delete_one({"id": opp_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Oportunidad no encontrada")
    return {"message": "Oportunidad eliminada", "id": opp_id}

# ============================================
# CRM API ENDPOINTS - Análisis de Clientes Inactivos
# ============================================

@api_router.get("/crm/analytics/inactive-clients")
async def get_inactive_clients(days_without_offer: int = 30, days_without_purchase: int = 60):
    """
    Analiza clientes/contactos sin actividad reciente.
    - Sin oferta: Contactos sin oportunidades nuevas en X días
    - Sin compra: Contactos sin oportunidades 'won' en Y días
    """
    from datetime import datetime, timedelta, timezone
    
    now = datetime.now(timezone.utc)
    offer_cutoff = now - timedelta(days=days_without_offer)
    purchase_cutoff = now - timedelta(days=days_without_purchase)
    
    # Get all contacts
    contacts = await db.contacts.find({}, {"_id": 0}).to_list(5000)
    
    # Get all opportunities
    opportunities = await db.opportunities.find({}, {"_id": 0}).to_list(5000)
    
    # Create lookup maps
    # Last offer (any opportunity) per contact
    last_offer_by_contact = {}
    # Last purchase (won opportunity) per contact  
    last_purchase_by_contact = {}
    
    for opp in opportunities:
        contact_id = opp.get("contactId")
        if not contact_id:
            continue
            
        created_at_str = opp.get("createdAt", "")
        try:
            if isinstance(created_at_str, str):
                created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
            else:
                created_at = created_at_str
        except:
            continue
        
        # Track last offer (any opportunity)
        if contact_id not in last_offer_by_contact or created_at > last_offer_by_contact[contact_id]["date"]:
            last_offer_by_contact[contact_id] = {"date": created_at, "opp": opp}
        
        # Track last purchase (won opportunities only)
        if opp.get("stage") == "won":
            won_at_str = opp.get("updatedAt", opp.get("createdAt", ""))
            try:
                if isinstance(won_at_str, str):
                    won_at = datetime.fromisoformat(won_at_str.replace('Z', '+00:00'))
                else:
                    won_at = won_at_str
            except:
                continue
                
            if contact_id not in last_purchase_by_contact or won_at > last_purchase_by_contact[contact_id]["date"]:
                last_purchase_by_contact[contact_id] = {"date": won_at, "opp": opp}
    
    # Build result lists
    without_recent_offer = []
    without_recent_purchase = []
    
    for contact in contacts:
        contact_id = contact.get("id")
        contact_info = {
            "id": contact_id,
            "name": contact.get("name", ""),
            "company": contact.get("company", ""),
            "email": contact.get("email", ""),
            "phone": contact.get("phone", ""),
            "status": contact.get("status", "")
        }
        
        # Check without offer
        if contact_id in last_offer_by_contact:
            last_offer = last_offer_by_contact[contact_id]
            if last_offer["date"] < offer_cutoff:
                days_ago = (now - last_offer["date"]).days
                contact_info["lastOfferDate"] = last_offer["date"].isoformat()
                contact_info["lastOfferTitle"] = last_offer["opp"].get("title", "")
                contact_info["daysWithoutOffer"] = days_ago
                without_recent_offer.append(contact_info.copy())
        else:
            # Never had an offer
            contact_created = contact.get("createdAt", "")
            if contact_created:
                try:
                    if isinstance(contact_created, str):
                        created = datetime.fromisoformat(contact_created.replace('Z', '+00:00'))
                    else:
                        created = contact_created
                    days_since_created = (now - created).days
                    if days_since_created >= days_without_offer:
                        contact_info["lastOfferDate"] = None
                        contact_info["lastOfferTitle"] = "Nunca"
                        contact_info["daysWithoutOffer"] = days_since_created
                        without_recent_offer.append(contact_info.copy())
                except:
                    pass
        
        # Check without purchase
        if contact_id in last_purchase_by_contact:
            last_purchase = last_purchase_by_contact[contact_id]
            if last_purchase["date"] < purchase_cutoff:
                days_ago = (now - last_purchase["date"]).days
                contact_info["lastPurchaseDate"] = last_purchase["date"].isoformat()
                contact_info["lastPurchaseValue"] = last_purchase["opp"].get("value", 0)
                contact_info["daysWithoutPurchase"] = days_ago
                without_recent_purchase.append(contact_info.copy())
        else:
            # Never purchased - only include if they've had at least one offer
            if contact_id in last_offer_by_contact:
                contact_info["lastPurchaseDate"] = None
                contact_info["lastPurchaseValue"] = 0
                contact_info["daysWithoutPurchase"] = 9999  # Never purchased
                without_recent_purchase.append(contact_info.copy())
    
    # Sort by days without activity (descending)
    without_recent_offer.sort(key=lambda x: x.get("daysWithoutOffer", 0), reverse=True)
    without_recent_purchase.sort(key=lambda x: x.get("daysWithoutPurchase", 0), reverse=True)
    
    return {
        "withoutRecentOffer": without_recent_offer[:50],  # Top 50
        "withoutRecentPurchase": without_recent_purchase[:50],  # Top 50
        "summary": {
            "totalWithoutOffer30Days": len([c for c in without_recent_offer if c.get("daysWithoutOffer", 0) >= 30]),
            "totalWithoutPurchase60Days": len([c for c in without_recent_purchase if c.get("daysWithoutPurchase", 0) >= 60]),
            "totalWithoutPurchase90Days": len([c for c in without_recent_purchase if c.get("daysWithoutPurchase", 0) >= 90])
        }
    }

# ============================================
# CRM API ENDPOINTS - Actividades
# ============================================

@api_router.get("/crm/activities")
async def get_activities(type: Optional[str] = None, contactId: Optional[str] = None, opportunityId: Optional[str] = None, completed: Optional[bool] = None):
    """Get all activities with optional filters"""
    try:
        query = {}
        if type:
            query["type"] = type
        if contactId:
            query["contactId"] = contactId
        if opportunityId:
            query["opportunityId"] = opportunityId
        if completed is not None:
            query["completed"] = completed
        
        activities = await db.activities.find(query, {"_id": 0}).sort("dueDate", 1).to_list(1000)
        return activities
    except Exception as e:
        logger.error(f"Get activities error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/crm/activities")
async def create_activity(activity: ActivityCreate):
    """Create a new activity"""
    try:
        act_dict = activity.model_dump()
        act_obj = ActivityModel(**act_dict)
        doc = act_obj.model_dump()
        doc['createdAt'] = doc['createdAt'].isoformat()
        if doc.get('completedAt'):
            doc['completedAt'] = doc['completedAt'].isoformat()
        
        await db.activities.insert_one(doc)
        doc.pop('_id', None)
        return doc
    except Exception as e:
        logger.error(f"Create activity error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/crm/activities/{act_id}")
async def update_activity(act_id: str, activity: ActivityUpdate):
    """Update an existing activity"""
    try:
        update_data = {k: v for k, v in activity.model_dump().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=400, detail="No hay datos para actualizar")
        
        # If completed changed to True, set completedAt
        if update_data.get('completed') == True:
            update_data['completedAt'] = datetime.now(timezone.utc).isoformat()
        
        result = await db.activities.update_one(
            {"id": act_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Actividad no encontrada")
        
        updated = await db.activities.find_one({"id": act_id}, {"_id": 0})
        return updated
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update activity error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/crm/activities/{act_id}")
async def delete_activity(act_id: str):
    """Delete an activity"""
    result = await db.activities.delete_one({"id": act_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Actividad no encontrada")
    return {"message": "Actividad eliminada", "id": act_id}

# ============================================
# CRM CALENDAR API ENDPOINTS
# ============================================

EVENT_TYPES = {
    "cita": {"name": "Cita/Visita", "color": "#3b82f6"},
    "seguimiento": {"name": "Seguimiento", "color": "#f59e0b"},
    "llamada": {"name": "Llamada", "color": "#10b981"},
    "reunion": {"name": "Reunión", "color": "#8b5cf6"},
    "otro": {"name": "Otro", "color": "#6b7280"}
}

@api_router.get("/crm/calendar/event-types")
async def get_event_types():
    """Get available event types"""
    return EVENT_TYPES

@api_router.get("/crm/calendar/events")
async def get_calendar_events(
    userId: Optional[str] = None,
    startDate: Optional[str] = None,
    endDate: Optional[str] = None,
    eventType: Optional[str] = None,
    viewAll: bool = False,
    commercialId: Optional[str] = None
):
    """
    Get calendar events with visibility rules:
    - Normal user: only their events (assignedTo = userId)
    - Admin with viewAll=true: all events
    - Commercial with commercialId: events from their assigned shops
    """
    try:
        query = {}
        
        # Date range filter
        if startDate:
            query["startDate"] = {"$gte": startDate}
        if endDate:
            if "startDate" in query:
                query["startDate"]["$lte"] = endDate
            else:
                query["startDate"] = {"$lte": endDate}
        
        # Event type filter
        if eventType:
            query["eventType"] = eventType
        
        # Visibility rules
        if viewAll:
            # Admin sees all - no user filter
            pass
        elif commercialId:
            # Commercial sees their shops' events
            # First get the shops assigned to this commercial
            shops = await db.users.find(
                {"linkedRepresentativeId": commercialId},
                {"id": 1, "_id": 0}
            ).to_list(100)
            shop_ids = [s["id"] for s in shops]
            shop_ids.append(commercialId)  # Include commercial's own events
            query["assignedTo"] = {"$in": shop_ids}
        elif userId:
            # Normal user sees only their events
            query["assignedTo"] = userId
        
        events = await db.calendar_events.find(query, {"_id": 0}).sort("startDate", 1).to_list(5000)
        return events
    except Exception as e:
        logger.error(f"Get calendar events error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/crm/calendar/events")
async def create_calendar_event(event: CalendarEventCreate, createdBy: str = "", createdByName: str = ""):
    """Create a new calendar event"""
    try:
        evt_dict = event.model_dump()
        evt_dict["createdBy"] = createdBy
        evt_dict["createdByName"] = createdByName
        evt_obj = CalendarEventModel(**evt_dict)
        doc = evt_obj.model_dump()
        doc['createdAt'] = doc['createdAt'].isoformat()
        doc['updatedAt'] = doc['updatedAt'].isoformat()
        
        await db.calendar_events.insert_one(doc)
        doc.pop('_id', None)
        return doc
    except Exception as e:
        logger.error(f"Create calendar event error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/crm/calendar/events/{event_id}")
async def get_calendar_event(event_id: str):
    """Get a single calendar event"""
    event = await db.calendar_events.find_one({"id": event_id}, {"_id": 0})
    if not event:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    return event

@api_router.put("/crm/calendar/events/{event_id}")
async def update_calendar_event(event_id: str, update: CalendarEventUpdate):
    """Update a calendar event"""
    try:
        update_data = {k: v for k, v in update.model_dump().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=400, detail="No hay datos para actualizar")
        
        update_data["updatedAt"] = datetime.now(timezone.utc).isoformat()
        
        # If marking as completed, set completedAt
        if update_data.get("completed") == True:
            update_data["completedAt"] = datetime.now(timezone.utc).isoformat()
        
        result = await db.calendar_events.update_one(
            {"id": event_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Evento no encontrado")
        
        updated = await db.calendar_events.find_one({"id": event_id}, {"_id": 0})
        return updated
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update calendar event error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/crm/calendar/events/{event_id}")
async def delete_calendar_event(event_id: str):
    """Delete a calendar event"""
    result = await db.calendar_events.delete_one({"id": event_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    return {"message": "Evento eliminado", "id": event_id}

@api_router.post("/crm/calendar/events/{event_id}/complete")
async def complete_calendar_event(event_id: str):
    """Mark a calendar event as completed"""
    result = await db.calendar_events.update_one(
        {"id": event_id},
        {"$set": {
            "completed": True,
            "completedAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat()
        }}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    return {"message": "Evento completado", "id": event_id}

@api_router.post("/crm/calendar/create-from-opportunity/{opp_id}")
async def create_reminder_from_opportunity(
    opp_id: str,
    event_type: str = "seguimiento",
    days_from_now: int = 7,
    reminder_title: Optional[str] = None,
    user_id: str = "",
    user_name: str = ""
):
    """
    Crear recordatorio automático desde una oportunidad.
    Útil para programar seguimientos de presupuestos enviados.
    """
    try:
        # Get the opportunity
        opp = await db.opportunities.find_one({"id": opp_id}, {"_id": 0})
        if not opp:
            raise HTTPException(status_code=404, detail="Oportunidad no encontrada")
        
        # Calculate reminder date
        reminder_date = datetime.now(timezone.utc) + timedelta(days=days_from_now)
        
        # Create the calendar event
        event_data = {
            "id": f"evt-{uuid.uuid4().hex[:8]}",
            "title": reminder_title or f"Seguimiento: {opp.get('title', 'Sin título')}",
            "description": f"Recordatorio automático de seguimiento para oportunidad {opp.get('title')}",
            "eventType": event_type,
            "startDate": reminder_date.strftime("%Y-%m-%dT09:00:00"),
            "endDate": reminder_date.strftime("%Y-%m-%dT10:00:00"),
            "allDay": False,
            "contactId": opp.get("contactId"),
            "contactName": opp.get("contactName"),
            "opportunityId": opp_id,
            "opportunityTitle": opp.get("title"),
            "assignedTo": user_id or opp.get("assignedTo", ""),
            "assignedToName": user_name or opp.get("assignedToName", ""),
            "createdBy": user_id,
            "createdByName": user_name,
            "completed": False,
            "location": "",
            "notes": f"Valor de oportunidad: {opp.get('value', 0)}€\nEtapa: {opp.get('stage', '')}",
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat()
        }
        
        await db.calendar_events.insert_one(event_data)
        event_data.pop('_id', None)
        
        return {
            "success": True,
            "message": f"Recordatorio creado para {reminder_date.strftime('%d/%m/%Y')}",
            "event": event_data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create reminder from opportunity error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# CRM DASHBOARD STATS
# ============================================

@api_router.get("/crm/dashboard")
async def get_crm_dashboard(assignedTo: Optional[str] = None, isAdmin: Optional[bool] = True):
    """Get CRM dashboard statistics
    
    Para usuarios NO admin (comerciales/representantes), solo muestra datos de sus contactos y oportunidades.
    """
    try:
        # Filtro base según permisos
        base_filter = {}
        if not isAdmin and assignedTo:
            base_filter["assignedTo"] = assignedTo
        
        # Count totals (filtrado por usuario si aplica)
        total_contacts = await db.contacts.count_documents(base_filter)
        
        opp_filter = {**base_filter, "stage": {"$nin": ["won", "lost"]}}
        active_opportunities = await db.opportunities.count_documents(opp_filter)
        
        won_filter = {
            **base_filter,
            "stage": "won",
            "closedAt": {"$gte": datetime.now(timezone.utc).replace(day=1).isoformat()}
        }
        won_this_month = await db.opportunities.count_documents(won_filter)
        
        # Calculate pipeline value (filtrado)
        pipeline_filter = {**base_filter, "stage": {"$nin": ["won", "lost"]}}
        pipeline_opps = await db.opportunities.find(
            pipeline_filter,
            {"value": 1, "_id": 0}
        ).to_list(1000)
        pipeline_value = sum(opp.get("value", 0) for opp in pipeline_opps)
        
        # Top opportunities (filtrado)
        top_filter = {**base_filter, "stage": {"$nin": ["lost"]}}
        top_opportunities = await db.opportunities.find(
            top_filter,
            {"_id": 0}
        ).sort("value", -1).limit(5).to_list(5)
        
        # Upcoming activities (filtrado por usuario si aplica)
        activity_filter = {"completed": False}
        if not isAdmin and assignedTo:
            activity_filter["userId"] = assignedTo
        upcoming_activities = await db.activities.find(
            activity_filter,
            {"_id": 0}
        ).sort("dueDate", 1).limit(5).to_list(5)
        
        # Recent activity log (filtrado)
        recent_filter = {}
        if not isAdmin and assignedTo:
            recent_filter["userId"] = assignedTo
        recent_activities = await db.activities.find(
            recent_filter,
            {"_id": 0}
        ).sort("createdAt", -1).limit(10).to_list(10)
        
        return {
            "totalContacts": total_contacts,
            "activeOpportunities": active_opportunities,
            "wonThisMonth": won_this_month,
            "pipelineValue": pipeline_value,
            "topOpportunities": top_opportunities,
            "upcomingActivities": upcoming_activities,
            "recentActivities": recent_activities
        }
    except Exception as e:
        logger.error(f"Get CRM dashboard error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================
# CRM - Create Opportunity from Project/Budget
# ============================================

@api_router.post("/crm/opportunities/from-project/{project_id}")
async def create_opportunity_from_project(project_id: str):
    """Create a CRM opportunity from an existing project/budget"""
    try:
        # Get the project
        project = await db.projects.find_one({"id": project_id}, {"_id": 0})
        if not project:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        
        # Calculate project total value
        total_value = 0
        for item in project.get("itemsMontada", []):
            total_value += item.get("totalPrice", 0)
        for item in project.get("itemsDespiece", []):
            total_value += item.get("totalPrice", 0)
        
        # Check if contact exists or create one
        customer_name = project.get("customerName", "Cliente sin nombre")
        contact = await db.contacts.find_one({"name": customer_name}, {"_id": 0})
        
        if not contact:
            # Create new contact
            contact = ContactModel(
                name=customer_name,
                address=project.get("customerAddress", ""),
                status="customer"
            ).model_dump()
            contact['createdAt'] = contact['createdAt'].isoformat()
            contact['updatedAt'] = contact['updatedAt'].isoformat()
            await db.contacts.insert_one(contact)
        
        contact_id = contact.get("id")
        
        # Create opportunity
        opp = OpportunityModel(
            title=f"Presupuesto Cocina - {customer_name}",
            description=f"Presupuesto #{project.get('budgetNumber', '')}",
            contactId=contact_id,
            contactName=customer_name,
            value=total_value,
            probability=50,
            stage="proposal",
            linkedProjectId=project_id,
            linkedProjectNumber=project.get("budgetNumber", "")
        ).model_dump()
        opp['createdAt'] = opp['createdAt'].isoformat()
        opp['updatedAt'] = opp['updatedAt'].isoformat()
        
        await db.opportunities.insert_one(opp)
        
        # Link project to contact
        await db.contacts.update_one(
            {"id": contact_id},
            {"$addToSet": {"linkedProjectIds": project_id}}
        )
        
        opp.pop('_id', None)
        return {
            "opportunity": opp,
            "contact": contact,
            "message": "Oportunidad creada desde presupuesto"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create opportunity from project error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# DESPIECE (BILL OF MATERIALS) API
# ============================================

class DespieceItemInput(BaseModel):
    """Input for a single furniture item to calculate despiece"""
    productId: str
    productCode: str
    productName: str
    width: float  # in mm
    height: float  # in mm
    depth: float  # in mm
    quantity: int = 1
    category: str = ""  # ALTO, BAJO, COLUMNA, etc.

class DespieceRequest(BaseModel):
    """Request to calculate despiece for multiple items"""
    items: List[DespieceItemInput]
    carcassMaterial: str = "Melamina Blanca"
    backPanelMaterial: str = "Tablero 8mm"  # Trasera siempre 8mm
    grosor: float = 18  # Thickness in mm for carcass panels

class ComponentPiece(BaseModel):
    """A single piece/component in the despiece"""
    id: str
    name: str  # e.g., "Tapa Superior", "Lateral Izquierdo"
    nameShort: str  # e.g., "TAPA", "LAT-I"
    material: str
    width: float  # in mm
    height: float  # in mm
    quantity: int
    area: float  # in m²
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
    totalArea: float  # in m²

class DespieceResponse(BaseModel):
    """Full despiece response"""
    items: List[FurnitureDespiece]
    summary: Dict
    generatedAt: str

def calculate_furniture_despiece(
    item: DespieceItemInput,
    carcass_material: str,
    back_material: str,
    grosor: float
) -> FurnitureDespiece:
    """
    Calculate the despiece (bill of materials) for a single furniture piece.
    
    Standard furniture components:
    - TAPA SUPERIOR: width x depth (top cover)
    - TAPA INFERIOR: width x depth (bottom cover) 
    - LATERAL IZQUIERDO: (height - 2*grosor) x depth
    - LATERAL DERECHO: (height - 2*grosor) x depth
    - TRASERA: width x (height - 2*grosor) (back panel, 8mm)
    - BALDA/ESTANTE: (width - 2*grosor) x (depth - 3mm) - optional shelves
    
    For ALTOS (wall cabinets):
    - Usually no bottom cover (open for mounting)
    
    For BAJOS (base cabinets):
    - Standard configuration with possible kick plate
    """
    
    w = item.width  # Width in mm
    h = item.height * 10  # Height comes in cm, convert to mm  
    d = item.depth * 10  # Depth comes in cm, convert to mm
    g = grosor  # Panel thickness
    
    components = []
    component_id = 0
    
    # Determine furniture type
    is_alto = "ALTO" in item.category.upper() or "ALTO" in item.productName.upper()
    is_bajo = "BAJO" in item.category.upper() or "BAJO" in item.productName.upper()
    is_columna = "COLUMNA" in item.category.upper() or "COLUMNA" in item.productName.upper()
    
    def add_component(name: str, short: str, material: str, width: float, height: float, qty: int = 1, notes: str = ""):
        nonlocal component_id
        component_id += 1
        area = (width * height * qty) / 1_000_000  # Convert mm² to m²
        components.append(ComponentPiece(
            id=f"CMP-{item.productId[:8]}-{component_id:03d}",
            name=name,
            nameShort=short,
            material=material,
            width=round(width, 1),
            height=round(height, 1),
            quantity=qty,
            area=round(area, 4),
            notes=notes
        ))
    
    # TAPA SUPERIOR (Top panel)
    add_component(
        "TAPA SUPERIOR", "TAPA-S", 
        carcass_material,
        w, d, 1,
        "Canto frontal visto"
    )
    
    # TAPA INFERIOR (Bottom panel) - not always present in ALTOS
    if not is_alto:
        add_component(
            "TAPA INFERIOR", "TAPA-I",
            carcass_material,
            w, d, 1,
            "Canto frontal visto" if is_bajo else ""
        )
    else:
        # ALTOS use a narrower bottom rail
        add_component(
            "TRAVESAÑO INFERIOR", "TRAV-I",
            carcass_material,
            w - (2 * g), 80, 1,  # 80mm rail
            "Travesaño de sujeción"
        )
    
    # LATERALES (Side panels)
    lateral_height = h - (2 * g) if not is_alto else h - g - 80  # Account for rail in ALTOS
    add_component(
        "LATERAL IZQUIERDO", "LAT-I",
        carcass_material,
        lateral_height, d, 1,
        "Canto frontal visto"
    )
    add_component(
        "LATERAL DERECHO", "LAT-D",
        carcass_material,
        lateral_height, d, 1,
        "Canto frontal visto"
    )
    
    # TRASERA (Back panel) - siempre 8mm
    back_width = w - (2 * g) + 6  # Recessed into grooves (3mm each side)
    back_height = h - (2 * g) + 6 if not is_alto else h - g - 80 + 6
    add_component(
        "TRASERA", "TRAS",
        back_material,
        back_width, back_height, 1,
        "Tablero 8mm encastrado"
    )
    
    # BALDAS / ESTANTES (Shelves) - estimate based on height
    shelf_count = 0
    if h >= 700:  # Tall units get more shelves
        shelf_count = 2 if h < 1200 else 3 if h < 1800 else 4
    elif h >= 350:
        shelf_count = 1
    
    if shelf_count > 0:
        shelf_width = w - (2 * g)
        shelf_depth = d - 20  # Slightly recessed
        add_component(
            f"BALDA INTERIOR", "BALDA",
            carcass_material,
            shelf_width, shelf_depth, shelf_count,
            "Regulable con soportes"
        )
    
    # Calculate totals
    total_panels = sum(c.quantity for c in components)
    total_area = sum(c.area for c in components)
    
    return FurnitureDespiece(
        productId=item.productId,
        productCode=item.productCode,
        productName=item.productName,
        category=item.category,
        originalWidth=item.width,
        originalHeight=item.height,
        originalDepth=item.depth,
        itemQuantity=item.quantity,
        components=components,
        totalPanels=total_panels,
        totalArea=round(total_area * item.quantity, 4)
    )

@api_router.post("/despiece/calculate", response_model=DespieceResponse)
async def calculate_despiece(request: DespieceRequest):
    """
    Calculate the bill of materials (despiece) for a list of furniture items.
    Returns cutting lists and assembly orders.
    """
    try:
        despiece_items = []
        
        for item in request.items:
            furniture_despiece = calculate_furniture_despiece(
                item,
                request.carcassMaterial,
                request.backPanelMaterial,
                request.grosor
            )
            despiece_items.append(furniture_despiece)
        
        # Calculate summary
        total_pieces = sum(d.totalPanels * d.itemQuantity for d in despiece_items)
        total_area = sum(d.totalArea for d in despiece_items)
        total_furniture = sum(d.itemQuantity for d in despiece_items)
        
        # Group by material
        material_summary = {}
        for d in despiece_items:
            for comp in d.components:
                mat = comp.material
                if mat not in material_summary:
                    material_summary[mat] = {"pieces": 0, "area": 0}
                material_summary[mat]["pieces"] += comp.quantity * d.itemQuantity
                material_summary[mat]["area"] += comp.area * d.itemQuantity
        
        # Round areas
        for mat in material_summary:
            material_summary[mat]["area"] = round(material_summary[mat]["area"], 3)
        
        return DespieceResponse(
            items=despiece_items,
            summary={
                "totalFurniture": total_furniture,
                "totalPieces": total_pieces,
                "totalArea": round(total_area, 3),
                "byMaterial": material_summary
            },
            generatedAt=datetime.now(timezone.utc).isoformat()
        )
    except Exception as e:
        logger.error(f"Calculate despiece error: {e}")
        raise HTTPException(status_code=500, detail=f"Error calculando despiece: {str(e)}")


# ============================================
# DIGITALIZADOR DE BORRADORES API
# ============================================

class DigitalizadorLine(BaseModel):
    """A single line extracted from the draft"""
    id: str
    quantity: int = 1
    reference: str = ""
    description: str
    price: float = 0
    discount: float = 0
    isManual: bool = False

class DigitalizadorRequest(BaseModel):
    """Request to analyze a draft image"""
    imageBase64: str
    filename: str = "draft.jpg"

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

# Modelo para guardar presupuesto digitalizado en historial
class DigitalizadorSaveRequest(BaseModel):
    """Request to save a digitalized budget to history"""
    projectName: str
    customerName: str = ""
    acabado: str = ""
    armazon: str = ""
    costados: str = ""
    lines: List[DigitalizadorLine]
    globalDiscount: float = 0
    ivaRate: float = 21
    userId: str
    
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
    ivaRate: float
    totalBruto: float
    totalNeto: float
    totalConIva: float
    userId: str
    createdAt: str
    filename: str = ""

@api_router.post("/digitalizador/save")
async def save_digitalizador_budget(request: DigitalizadorSaveRequest):
    """Save a digitalized budget to history"""
    try:
        # Calculate totals
        total_bruto = sum(line.price * line.quantity for line in request.lines)
        
        total_neto = 0
        for line in request.lines:
            line_price = line.price * line.quantity
            line_discount = line.discount if line.isManual else max(line.discount, request.globalDiscount)
            total_neto += line_price * (1 - line_discount / 100)
        
        total_con_iva = total_neto * (1 + request.ivaRate / 100)
        
        # Create history item
        history_item = {
            "id": f"digi-{uuid.uuid4().hex[:12]}",
            "projectName": request.projectName,
            "customerName": request.customerName,
            "acabado": request.acabado,
            "armazon": request.armazon,
            "costados": request.costados,
            "lines": [line.model_dump() for line in request.lines],
            "globalDiscount": request.globalDiscount,
            "ivaRate": request.ivaRate,
            "totalBruto": round(total_bruto, 2),
            "totalNeto": round(total_neto, 2),
            "totalConIva": round(total_con_iva, 2),
            "userId": request.userId,
            "createdAt": datetime.now(timezone.utc).isoformat()
        }
        
        await db.digitalizador_history.insert_one(history_item)
        history_item.pop('_id', None)
        
        return {
            "success": True,
            "message": "Presupuesto guardado en historial",
            "item": history_item
        }
    except Exception as e:
        logger.error(f"Save digitalizador budget error: {e}")
        raise HTTPException(status_code=500, detail=f"Error guardando presupuesto: {str(e)}")

@api_router.get("/digitalizador/history")
async def get_digitalizador_history(userId: str = None, search: str = None, limit: int = 50):
    """Get digitalizador history, optionally filtered by user or search term"""
    try:
        query = {}
        
        if userId:
            query["userId"] = userId
        
        if search:
            query["$or"] = [
                {"projectName": {"$regex": search, "$options": "i"}},
                {"customerName": {"$regex": search, "$options": "i"}}
            ]
        
        cursor = db.digitalizador_history.find(query).sort("createdAt", -1).limit(limit)
        items = await cursor.to_list(length=limit)
        
        for item in items:
            item.pop('_id', None)
        
        return {
            "success": True,
            "items": items,
            "count": len(items)
        }
    except Exception as e:
        logger.error(f"Get digitalizador history error: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo historial: {str(e)}")

@api_router.get("/digitalizador/history/{item_id}")
async def get_digitalizador_item(item_id: str):
    """Get a specific digitalizador history item"""
    try:
        item = await db.digitalizador_history.find_one({"id": item_id})
        
        if not item:
            raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
        
        item.pop('_id', None)
        
        return {
            "success": True,
            "item": item
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get digitalizador item error: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo presupuesto: {str(e)}")

@api_router.delete("/digitalizador/history/{item_id}")
async def delete_digitalizador_item(item_id: str):
    """Delete a digitalizador history item"""
    try:
        result = await db.digitalizador_history.delete_one({"id": item_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
        
        return {
            "success": True,
            "message": "Presupuesto eliminado"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete digitalizador item error: {e}")
        raise HTTPException(status_code=500, detail=f"Error eliminando presupuesto: {str(e)}")

@api_router.post("/digitalizador/analyze")
async def analyze_draft(request: DigitalizadorRequest):
    """
    Analyze a draft image using Gemini Vision to extract budget lines.
    Returns structured data with quantities, descriptions, and dimensions.
    """
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent
        
        # Prepare the prompt for Gemini Vision - IMPROVED for correct dimension reading
        extraction_prompt = """Analiza esta imagen de un presupuesto o boceto de cocina/muebles.

IMPORTANTE - CONTEXTO DE MEDIDAS DE MUEBLES DE COCINA:
- Los muebles ALTOS suelen medir entre 30-90 cm de alto (típico: 70-80 cm)
- Los muebles BAJOS suelen medir entre 70-90 cm de alto
- Las COLUMNAS y SEMICOLUMNAS miden entre 110-220 cm de alto (típico: 200-220 cm)
- Los COSTADOS suelen medir entre 30-220 cm de alto según el tipo de mueble
- El ANCHO típico es 30-120 cm
- El FONDO típico es 30-65 cm

REGLAS DE INTERPRETACIÓN:
- Si ves "70x45" o "70 x 45", son centímetros (70cm x 45cm)
- Si ves "110" o "220" solos, probablemente son ALTURAS en centímetros (110cm, 220cm), NO 11cm o 22cm
- Si ves medidas como "35.5" o "69.8", son centímetros con decimales
- Las medidas escritas a mano pueden parecer que les falta un dígito - usa el contexto para interpretar

Extrae TODAS las líneas que encuentres, incluyendo:
- Piezas de muebles con dimensiones (ej: "Costado 113 x 60", "Pieza 69.8 x 44.7")
- Referencias de productos (ej: "Factory 01", "HB514AER4")
- Cualquier artículo con medidas o descripciones
- Electrodomésticos con sus códigos y descripciones

Para cada línea encontrada, devuelve en formato JSON:
{
  "projectName": "nombre del proyecto o cliente si lo encuentras",
  "lines": [
    {
      "quantity": 1,
      "reference": "referencia o código si existe",
      "description": "descripción completa del artículo incluyendo medidas CORRECTAS en centímetros"
    }
  ]
}

IMPORTANTE: 
- Incluye las medidas en la descripción tal como aparecen (ej: "Costado 110 x 60")
- Si hay un nombre de cliente o proyecto, ponlo en projectName
- Responde SOLO con el JSON, sin texto adicional ni explicaciones"""

        # Initialize Gemini Vision chat
        llm_key = os.environ.get('EMERGENT_LLM_KEY')
        if not llm_key:
            raise HTTPException(status_code=500, detail="API key not configured")
        
        # Initialize chat with correct syntax - use with_model()
        chat = LlmChat(
            api_key=llm_key,
            session_id=f"digitalizador-{uuid.uuid4().hex[:8]}",
            system_message="Eres un asistente experto en extraer información de imágenes de presupuestos de cocinas."
        ).with_model("gemini", "gemini-2.0-flash")
        
        # Create image content using ImageContent with image_base64
        image_content = ImageContent(
            image_base64=request.imageBase64
        )
        
        # Send request with UserMessage that contains text and file_contents
        response = await chat.send_message(UserMessage(
            text=extraction_prompt,
            file_contents=[image_content]
        ))
        
        response_text = response.strip() if isinstance(response, str) else str(response)
        
        # Try to parse JSON from response
        try:
            # Clean up response - remove markdown code blocks if present
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            response_text = response_text.strip()
            
            parsed = json.loads(response_text)
            
            # Build response lines
            extracted_lines = []
            for idx, line in enumerate(parsed.get("lines", [])):
                # Ensure no None values - use 'or' to convert None to default
                extracted_lines.append(DigitalizadorLine(
                    id=f"LINE-{uuid.uuid4().hex[:8]}",
                    quantity=int(line.get("quantity") or 1),
                    reference=str(line.get("reference") or ""),
                    description=str(line.get("description") or ""),
                    price=float(line.get("price") or 0),
                    discount=0,
                    isManual=False
                ))
            
            return DigitalizadorResponse(
                success=True,
                projectName=str(parsed.get("projectName") or ""),
                lines=extracted_lines,
                rawText=response_text
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response: {response_text}")
            # Return raw text if parsing fails
            return DigitalizadorResponse(
                success=False,
                projectName="",
                lines=[],
                rawText=response_text,
                error=f"Error parsing response: {str(e)}"
            )
            
    except Exception as e:
        logger.error(f"Digitalizador analyze error: {e}")
        raise HTTPException(status_code=500, detail=f"Error analizando imagen: {str(e)}")


@api_router.post("/digitalizador/export-csv")
async def export_digitalizador_csv(request: DigitalizadorExportRequest):
    """
    Export digitalizador lines to CSV format for cutting machine.
    Format: "CODE";THICKNESS;"DESCRIPTION";WIDTH;HEIGHT;ORIENTATION;0;0;"CODE"
    """
    try:
        import re
        
        csv_lines = []
        
        for line in request.lines:
            # Try to extract dimensions from description
            # Pattern: "NNN x NNN" or "NNN.N x NNN.N"
            dim_match = re.search(r'(\d+(?:\.\d+)?)\s*[xX×]\s*(\d+(?:\.\d+)?)', line.description)
            
            if dim_match:
                width = int(float(dim_match.group(1)))
                height = int(float(dim_match.group(2)))
            else:
                width = 0
                height = 0
            
            # Build CSV line
            # Format: "CODE";THICKNESS;"DESCRIPTION";WIDTH;HEIGHT;ORIENTATION;0;0;"CODE"
            thickness_str = f"{request.materialThickness:.1f}".replace(".", ",")
            csv_line = f'"{request.materialCode}";{thickness_str};"{line.description}";{width};{height};1;0;0;"{request.materialCode}"'
            
            # Add line for each quantity
            for _ in range(line.quantity):
                csv_lines.append(csv_line)
        
        csv_content = "\n".join(csv_lines)
        
        return {
            "success": True,
            "csv": csv_content,
            "lineCount": len(csv_lines)
        }
        
    except Exception as e:
        logger.error(f"Export CSV error: {e}")
        raise HTTPException(status_code=500, detail=f"Error exportando CSV: {str(e)}")


# ============================================
# MAINTENANCE MODE API
# ============================================

class MaintenanceActivateRequest(BaseModel):
    """Request to activate maintenance mode"""
    message: str = "Sistema en actualización. Volvemos pronto."
    estimatedMinutes: int = 30
    adminUserId: str
    createBackup: bool = True

class MaintenanceStatusResponse(BaseModel):
    """Response with maintenance status"""
    active: bool
    message: str
    activatedAt: Optional[str] = None
    activatedBy: Optional[str] = None
    estimatedEndTime: Optional[str] = None
    preUpdateBackupId: Optional[str] = None

@api_router.get("/maintenance/status")
async def get_maintenance_status():
    """Get current maintenance mode status - accessible to everyone"""
    global maintenance_state
    
    # Sync with database on first call
    db_state = await db.system_settings.find_one({"key": "maintenance_mode"})
    if db_state:
        maintenance_state = db_state.get("value", maintenance_state)
    
    return MaintenanceStatusResponse(
        active=maintenance_state.get("active", False),
        message=maintenance_state.get("message", ""),
        activatedAt=maintenance_state.get("activatedAt"),
        activatedBy=maintenance_state.get("activatedBy"),
        estimatedEndTime=maintenance_state.get("estimatedEndTime"),
        preUpdateBackupId=maintenance_state.get("preUpdateBackupId")
    )

@api_router.post("/maintenance/activate")
async def activate_maintenance_mode(request: MaintenanceActivateRequest):
    """Activate maintenance mode - ADMIN ONLY"""
    global maintenance_state
    
    try:
        # Verify admin user
        admin_user = await db.users.find_one({"id": request.adminUserId})
        if not admin_user or not admin_user.get("isAdmin"):
            raise HTTPException(status_code=403, detail="Solo administradores pueden activar modo mantenimiento")
        
        backup_id = None
        
        # Create pre-update backup if requested
        if request.createBackup:
            logger.info("Creating pre-update backup before maintenance mode...")
            
            # Collect all data
            backup_data = {
                "type": "pre_update_backup",
                "createdAt": datetime.now(timezone.utc).isoformat(),
                "createdBy": request.adminUserId,
                "reason": "Backup automático antes de actualización",
                "collections": {}
            }
            
            # Backup all important collections
            collections_to_backup = [
                "users", "products", "projects", "materials", "settings",
                "contacts", "opportunities", "activities", "catalogs",
                "digitalizador_history"
            ]
            
            for coll_name in collections_to_backup:
                try:
                    docs = await db[coll_name].find({}).to_list(length=None)
                    # Convert ObjectId to string
                    for doc in docs:
                        doc.pop('_id', None)
                    backup_data["collections"][coll_name] = docs
                    logger.info(f"  Backed up {len(docs)} documents from {coll_name}")
                except Exception as e:
                    logger.error(f"  Error backing up {coll_name}: {e}")
                    backup_data["collections"][coll_name] = []
            
            # Save backup to database
            backup_id = f"backup-preupdate-{uuid.uuid4().hex[:12]}"
            backup_record = {
                "id": backup_id,
                "type": "pre_update",
                "createdAt": datetime.now(timezone.utc).isoformat(),
                "createdBy": admin_user.get("username", "admin"),
                "data": backup_data,
                "size": len(json.dumps(backup_data))
            }
            
            await db.system_backups.insert_one(backup_record)
            logger.info(f"Pre-update backup created with ID: {backup_id}")
        
        # Calculate estimated end time
        from datetime import timedelta
        estimated_end = datetime.now(timezone.utc) + timedelta(minutes=request.estimatedMinutes)
        
        # Update maintenance state
        maintenance_state = {
            "active": True,
            "message": request.message,
            "activatedAt": datetime.now(timezone.utc).isoformat(),
            "activatedBy": admin_user.get("username", "admin"),
            "estimatedEndTime": estimated_end.isoformat(),
            "preUpdateBackupId": backup_id
        }
        
        # Save to database for persistence
        await db.system_settings.update_one(
            {"key": "maintenance_mode"},
            {"$set": {"key": "maintenance_mode", "value": maintenance_state}},
            upsert=True
        )
        
        logger.info(f"Maintenance mode ACTIVATED by {admin_user.get('username')}")
        
        return {
            "success": True,
            "message": "Modo mantenimiento activado",
            "state": maintenance_state
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error activating maintenance mode: {e}")
        raise HTTPException(status_code=500, detail=f"Error activando modo mantenimiento: {str(e)}")

@api_router.post("/maintenance/deactivate")
async def deactivate_maintenance_mode(adminUserId: str):
    """Deactivate maintenance mode - ADMIN ONLY"""
    global maintenance_state
    
    try:
        # Verify admin user
        admin_user = await db.users.find_one({"id": adminUserId})
        if not admin_user or not admin_user.get("isAdmin"):
            raise HTTPException(status_code=403, detail="Solo administradores pueden desactivar modo mantenimiento")
        
        # Update maintenance state
        maintenance_state = {
            "active": False,
            "message": "",
            "activatedAt": None,
            "activatedBy": None,
            "estimatedEndTime": None,
            "preUpdateBackupId": None
        }
        
        # Save to database
        await db.system_settings.update_one(
            {"key": "maintenance_mode"},
            {"$set": {"key": "maintenance_mode", "value": maintenance_state}},
            upsert=True
        )
        
        logger.info(f"Maintenance mode DEACTIVATED by {admin_user.get('username')}")
        
        return {
            "success": True,
            "message": "Modo mantenimiento desactivado. Sistema operativo."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating maintenance mode: {e}")
        raise HTTPException(status_code=500, detail=f"Error desactivando modo mantenimiento: {str(e)}")

@api_router.get("/maintenance/backups")
async def list_pre_update_backups(limit: int = 10):
    """List all pre-update backups"""
    try:
        cursor = db.system_backups.find({"type": "pre_update"}).sort("createdAt", -1).limit(limit)
        backups = await cursor.to_list(length=limit)
        
        # Return summary without full data
        result = []
        for b in backups:
            b.pop('_id', None)
            b.pop('data', None)  # Don't send full backup data in list
            result.append(b)
        
        return {
            "success": True,
            "backups": result,
            "count": len(result)
        }
    except Exception as e:
        logger.error(f"Error listing backups: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/maintenance/backups/{backup_id}/download")
async def download_pre_update_backup(backup_id: str):
    """Download a specific pre-update backup"""
    try:
        backup = await db.system_backups.find_one({"id": backup_id})
        
        if not backup:
            raise HTTPException(status_code=404, detail="Backup no encontrado")
        
        backup.pop('_id', None)
        
        return {
            "success": True,
            "backup": backup
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading backup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/products/fix-data")
async def fix_product_data():
    """
    Fix product data:
    1. Semicolumnas series: 11 -> 110, 12 -> 120, etc.
    2. Bajos fondo: 33 -> 58 (para muebles bajos estándar)
    """
    try:
        results = {
            "series_fixed": 0,
            "depth_fixed": 0,
            "errors": []
        }
        
        # 1. Fix semicolumnas series names
        series_mapping = {
            "SEMICOLUMNAS 11 FONDO ESTANDAR": "SEMICOLUMNAS 110 FONDO ESTANDAR",
            "SEMICOLUMNAS 12 FONDO ESTANDAR": "SEMICOLUMNAS 120 FONDO ESTANDAR",
            "SEMICOLUMNAS 13 FONDO ESTANDAR": "SEMICOLUMNAS 130 FONDO ESTANDAR",
            "SEMICOLUMNAS 14 FONDO ESTANDAR": "SEMICOLUMNAS 140 FONDO ESTANDAR",
            "SEMICOLUMNAS 16 FONDO ESTANDAR": "SEMICOLUMNAS 160 FONDO ESTANDAR",
            "GOLA - SEMICOLUMNAS 11 FONDO ESTANDAR": "GOLA - SEMICOLUMNAS 110 FONDO ESTANDAR",
            "GOLA - SEMICOLUMNAS 12 FONDO ESTANDAR": "GOLA - SEMICOLUMNAS 120 FONDO ESTANDAR",
            "GOLA - SEMICOLUMNAS 13 FONDO ESTANDAR": "GOLA - SEMICOLUMNAS 130 FONDO ESTANDAR",
            "GOLA - SEMICOLUMNAS 14 FONDO ESTANDAR": "GOLA - SEMICOLUMNAS 140 FONDO ESTANDAR",
            "GOLA - SEMICOLUMNAS 16 FONDO ESTANDAR": "GOLA - SEMICOLUMNAS 160 FONDO ESTANDAR",
        }
        
        for old_series, new_series in series_mapping.items():
            result = await db.products.update_many(
                {"series": old_series},
                {"$set": {"series": new_series}}
            )
            results["series_fixed"] += result.modified_count
            logger.info(f"Fixed series: {old_series} -> {new_series} ({result.modified_count} products)")
        
        # 2. Fix bajos fondo - Muebles BAJOS con fondo 33 -> 58
        # Pero NO los ALTOS que tienen fondo 33 correctamente
        # Criteria: codigo empieza con 7B, 8B (bajos 70cm, 80cm) y NO son ALTOS
        bajo_codes = ["7B", "8B"]  # Códigos que empiezan con estos son BAJOS
        
        for code_prefix in bajo_codes:
            result = await db.products.update_many(
                {
                    "code": {"$regex": f"^{code_prefix}"},
                    "depth": 33.0
                },
                {"$set": {"depth": 58.0}}
            )
            results["depth_fixed"] += result.modified_count
            logger.info(f"Fixed depth for {code_prefix}* products: {result.modified_count}")
        
        # También buscar productos con "Bajo" en el nombre que tengan fondo 33
        result = await db.products.update_many(
            {
                "name": {"$regex": "^Bajo", "$options": "i"},
                "depth": 33.0
            },
            {"$set": {"depth": 58.0}}
        )
        results["depth_fixed"] += result.modified_count
        
        return {
            "success": True,
            "message": "Datos de productos corregidos",
            "results": results
        }
    except Exception as e:
        logger.error(f"Error fixing product data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# ARMARIOS - PROYECTOS
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

@api_router.post("/armarios/projects")
async def create_armario_project(project: ArmarioProjectCreate, userId: str = ""):
    """Crear nuevo proyecto de armario"""
    try:
        project_dict = project.model_dump()
        project_dict["id"] = str(uuid.uuid4())
        project_dict["userId"] = userId
        project_dict["createdAt"] = datetime.now(timezone.utc).isoformat()
        project_dict["updatedAt"] = datetime.now(timezone.utc).isoformat()
        
        await db.armario_projects.insert_one(project_dict)
        
        # Remover _id de MongoDB
        project_dict.pop("_id", None)
        
        return {"success": True, "project": project_dict}
    except Exception as e:
        logger.error(f"Error creating armario project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/armarios/projects")
async def get_armario_projects(userId: str = ""):
    """Obtener lista de proyectos de armarios"""
    try:
        query = {}
        if userId:
            query["userId"] = userId
        
        projects = await db.armario_projects.find(
            query,
            {"_id": 0}
        ).sort("updatedAt", -1).to_list(100)
        
        return {"success": True, "projects": projects}
    except Exception as e:
        logger.error(f"Error getting armario projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/armarios/projects/{project_id}")
async def get_armario_project(project_id: str):
    """Obtener un proyecto de armario específico"""
    try:
        project = await db.armario_projects.find_one(
            {"id": project_id},
            {"_id": 0}
        )
        
        if not project:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        
        return {"success": True, "project": project}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting armario project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/armarios/projects/{project_id}")
async def update_armario_project(project_id: str, update: ArmarioProjectUpdate):
    """Actualizar un proyecto de armario"""
    try:
        update_dict = {k: v for k, v in update.model_dump().items() if v is not None}
        update_dict["updatedAt"] = datetime.now(timezone.utc).isoformat()
        
        result = await db.armario_projects.update_one(
            {"id": project_id},
            {"$set": update_dict}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        
        # Obtener proyecto actualizado
        project = await db.armario_projects.find_one(
            {"id": project_id},
            {"_id": 0}
        )
        
        return {"success": True, "project": project}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating armario project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/armarios/projects/{project_id}")
async def delete_armario_project(project_id: str):
    """Eliminar un proyecto de armario"""
    try:
        result = await db.armario_projects.delete_one({"id": project_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        
        return {"success": True, "message": "Proyecto eliminado"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting armario project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# ARMARIOS - IA CONFIGURACIÓN Y RENDER
# ============================================

class IAConfigRequest(BaseModel):
    """Solicitud para configurar armario con IA"""
    instruction: str  # Ej: "Quiero un armario para una pareja con mucha ropa de colgar"
    current_config: Dict = {}

class IARenderRequest(BaseModel):
    """Solicitud para generar render del armario"""
    width: int
    height: int
    depth: int
    modules: int
    doorType: str
    exteriorColorName: str
    exteriorColorHex: str
    interiorColorName: str
    handleColorName: str
    moduleConfigs: List[Dict] = []
    roomStyle: str = "moderno"  # moderno, clásico, nórdico, minimalista

@api_router.post("/armarios/ia/configure")
async def ia_configure_armario(request: IAConfigRequest):
    """Usar IA para configurar la distribución de módulos del armario"""
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        api_key = os.environ.get("EMERGENT_LLM_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="Clave de IA no configurada")
        
        chat = LlmChat(
            api_key=api_key,
            session_id=f"armario-config-{uuid.uuid4()}",
            system_message="""Eres un diseñador experto en armarios empotrados. Tu trabajo es configurar la distribución óptima de módulos de un armario basándote en las necesidades del usuario.

DEBES responder SIEMPRE en formato JSON con esta estructura exacta:
{
  "modules": 3,
  "doorType": "sliding",
  "moduleConfigs": [
    {"id": 1, "shelves": 4, "drawers": 0, "hangingRods": 1, "hangingHeight": 1200, "extras": {}},
    {"id": 2, "shelves": 6, "drawers": 3, "hangingRods": 0, "hangingHeight": 0, "extras": {"jewelryTray": true}},
    {"id": 3, "shelves": 2, "drawers": 0, "hangingRods": 2, "hangingHeight": 1000, "extras": {"shoesRack": true}}
  ],
  "extras": {"softClose": true, "led": true, "mirror": false},
  "explanation": "Descripción breve de la configuración"
}

Tipos de puerta: "sliding" (corredera), "hinged" (abatible), "folding" (plegable)
Extras por módulo: shoesRack, trousersRack, jewelryTray, tieRack, pulloutBasket
Extras generales: softClose, led, mirror, antiFingerprint

Considera:
- Ropa de colgar larga (vestidos, abrigos): barras a 1600mm
- Ropa de colgar corta (camisas): barras a 1000-1200mm
- Barras dobles para maximizar espacio: hangingRods: 2, hangingHeight: 1000
- Cajones para ropa interior, calcetines, etc.
- Baldas para ropa doblada, bolsos
- Zapatero para zapatos
- Pantalonero para pantalones"""
        )
        
        chat.with_model("gemini", "gemini-3-flash-preview")
        
        # Construir prompt
        prompt = f"""El usuario quiere configurar un armario con estas instrucciones:

"{request.instruction}"

Configuración actual del armario:
- Ancho: {request.current_config.get('width', 2400)}mm
- Alto: {request.current_config.get('height', 2400)}mm
- Fondo: {request.current_config.get('depth', 600)}mm
- Módulos actuales: {request.current_config.get('modules', 3)}

Genera la configuración óptima en formato JSON."""

        msg = UserMessage(text=prompt)
        response = await chat.send_message(msg)
        
        # Parsear respuesta JSON
        import json
        import re
        
        # Get text content from response - handle different response types
        logger.info(f"IA raw response: {response}, type: {type(response)}")
        
        if response is None:
            return {"success": False, "error": "La IA no generó respuesta"}
        
        if isinstance(response, str):
            response_text = response
        elif hasattr(response, 'content'):
            response_text = response.content
        else:
            response_text = str(response)
        
        if not response_text or response_text == "None":
            return {"success": False, "error": "La IA no generó respuesta válida"}
        
        logger.info(f"IA response text: {response_text[:200] if response_text else 'None'}")
        
        # Extraer JSON de la respuesta
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            config = json.loads(json_match.group())
            return {"success": True, "config": config}
        else:
            return {"success": False, "error": "No se pudo generar configuración", "raw_response": response_text}
            
    except Exception as e:
        logger.error(f"Error en IA configuración: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/armarios/ia/render")
async def ia_render_armario(request: IARenderRequest):
    """Generar render realista del armario usando IA"""
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        import base64
        
        api_key = os.environ.get("EMERGENT_LLM_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="Clave de IA no configurada")
        
        chat = LlmChat(
            api_key=api_key,
            session_id=f"armario-render-{uuid.uuid4()}",
            system_message="You are a professional interior designer creating photorealistic renders of wardrobes."
        )
        
        chat.with_model("gemini", "gemini-3-pro-image-preview").with_params(modalities=["image", "text"])  # Nano Banana model
        
        # Construir descripción del armario
        door_type_desc = {
            "sliding": "puertas correderas de panel completo",
            "hinged": "puertas abatibles con tiradores",
            "folding": "puertas plegables"
        }.get(request.doorType, "puertas correderas")
        
        # Describir interior
        interior_desc = []
        for i, mod in enumerate(request.moduleConfigs[:3]):
            items = []
            if mod.get('hangingRods', 0) > 0:
                items.append(f"{mod['hangingRods']} barra(s) para colgar ropa")
            if mod.get('shelves', 0) > 0:
                items.append(f"{mod['shelves']} baldas")
            if mod.get('drawers', 0) > 0:
                items.append(f"{mod['drawers']} cajones")
            if items:
                interior_desc.append(f"Módulo {i+1}: {', '.join(items)}")
        
        prompt = f"""Create a photorealistic interior design render of a modern built-in wardrobe/closet with the following specifications:

DIMENSIONS: {request.width}mm width x {request.height}mm height x {request.depth}mm depth

EXTERIOR:
- Color: {request.exteriorColorName} (hex: {request.exteriorColorHex})
- Door type: {door_type_desc}
- Handle color: {request.handleColorName}
- {request.modules} modules/sections

INTERIOR CONFIGURATION:
{chr(10).join(interior_desc) if interior_desc else "Multiple shelves and hanging rods"}

STYLE: {request.roomStyle} bedroom style, soft natural lighting, high-end quality materials

The wardrobe should be shown with doors partially open to reveal the interior organization. Include realistic materials like melamine, soft-close drawers, and chrome hanging rods. The image should look like a professional interior design photograph, not a 3D render or sketch.

Generate a single high-quality photorealistic image."""

        msg = UserMessage(text=prompt)
        text_response, images = await chat.send_message_multimodal_response(msg)
        
        if images and len(images) > 0:
            # Devolver la imagen en base64
            return {
                "success": True,
                "image": {
                    "data": images[0]["data"],
                    "mime_type": images[0].get("mime_type", "image/png")
                },
                "description": text_response[:500] if text_response else None
            }
        else:
            return {
                "success": False,
                "error": "No se pudo generar la imagen",
                "text_response": text_response
            }
            
    except Exception as e:
        logger.error(f"Error en IA render: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Include the router in the main app (AFTER all endpoints are defined)
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# STARTUP / SHUTDOWN EVENTS
# ============================================

@app.on_event("startup")
async def startup_event():
    """Configure scheduled backups on startup"""
    # Schedule backups at 8:00 AM and 8:00 PM (Spain timezone approx)
    scheduler.add_job(
        scheduled_backup_task,
        CronTrigger(hour=8, minute=0),
        id="backup_morning",
        replace_existing=True
    )
    scheduler.add_job(
        scheduled_backup_task,
        CronTrigger(hour=20, minute=0),
        id="backup_evening",
        replace_existing=True
    )
    scheduler.start()
    logger.info("Backup scheduler started - backups at 8:00 and 20:00")

@app.on_event("shutdown")
async def shutdown_db_client():
    scheduler.shutdown()
    client.close()