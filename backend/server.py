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
    isActive: bool = True
    isAdmin: bool = False
    isRepresentative: bool = False
    linkedRepresentativeId: Optional[str] = None
    allowedModules: List[str] = ["montada"]
    allowedCatalogIds: List[str] = []
    commercialDiscount: float = 0
    canSeeCost: bool = False
    canSeeRetail: bool = True
    canUseAIAnalysis: bool = False
    canManageArticles: bool = False
    canViewTechnicalDespiece: bool = False
    useCustomBranding: bool = False
    canChangeLogo: bool = False

# User response model (without password)
class UserResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    username: str
    clientName: str
    isActive: bool = True
    isAdmin: bool = False
    isRepresentative: bool = False
    linkedRepresentativeId: Optional[str] = None
    allowedModules: List[str] = ["montada"]
    allowedCatalogIds: List[str] = []
    commercialDiscount: float = 0
    canSeeCost: bool = False
    canSeeRetail: bool = True
    canUseAIAnalysis: bool = False
    canManageArticles: bool = False
    canViewTechnicalDespiece: bool = False
    useCustomBranding: bool = False
    canChangeLogo: bool = False

class UserCreate(BaseModel):
    username: str
    password: str
    clientName: str
    isActive: bool = True
    isAdmin: bool = False
    isRepresentative: bool = False
    linkedRepresentativeId: Optional[str] = None
    allowedModules: List[str] = ["montada"]
    allowedCatalogIds: List[str] = []
    commercialDiscount: float = 0
    canSeeCost: bool = False
    canSeeRetail: bool = True
    canUseAIAnalysis: bool = False
    canManageArticles: bool = False
    canViewTechnicalDespiece: bool = False
    useCustomBranding: bool = False
    canChangeLogo: bool = False

class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    clientName: Optional[str] = None
    isActive: Optional[bool] = None
    isAdmin: Optional[bool] = None
    isRepresentative: Optional[bool] = None
    linkedRepresentativeId: Optional[str] = None
    allowedModules: Optional[List[str]] = None
    allowedCatalogIds: Optional[List[str]] = None
    commercialDiscount: Optional[float] = None
    canSeeCost: Optional[bool] = None
    canSeeRetail: Optional[bool] = None
    canUseAIAnalysis: Optional[bool] = None
    canManageArticles: Optional[bool] = None
    canViewTechnicalDespiece: Optional[bool] = None
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
                system_message="""Eres un experto en digitalización de fichas técnicas de muebles de cocina.
Analiza la imagen de la ficha técnica y extrae TODA la información visible con máximo detalle y precisión.

INSTRUCCIONES CRÍTICAS:
1. Lee TODO el texto visible en la imagen (OCR completo)
2. Identifica la estructura de la ficha (tablas, columnas, secciones)
3. Extrae TODOS los datos numéricos y códigos
4. Si ves una tabla de zonas (Z1-Z12), extrae TODOS los valores exactos
5. Si no ves zonas, solo extrae el punto base

Debes responder ÚNICAMENTE con un objeto JSON válido (sin markdown, sin comillas extras).
Formato exacto:
{
  "code": "CÓDIGO_EXACTO",
  "name": "Nombre completo del producto",
  "width": número_en_cm,
  "height": número_en_cm,
  "depth": número_en_cm,
  "category": "Categoría detectada",
  "series": "Serie o familia",
  "visualType": "Tipo visual (1P, 2P, HK-TOP, etc)",
  "points": número_base,
  "zonePoints": {
    "Z1": número, "Z2": número, "Z3": número, "Z4": número,
    "Z5": número, "Z6": número, "Z7": número, "Z8": número,
    "Z9": número, "Z10": número, "Z11": número, "Z12": número
  }
}

Si no encuentras zonas (para despiece), usa el mismo valor en todas las zonas.
IMPORTANTE: Responde SOLO el JSON, sin texto adicional."""
            ).with_model("gemini", "gemini-2.5-pro")
            
            # Create message with image
            user_message = UserMessage(
                text="Analiza esta ficha técnica de producto y extrae toda la información en el formato JSON especificado. Sé exhaustivo y preciso con todos los números y códigos.",
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
                
                product_data = json.loads(clean_response)
                
                # Add metadata
                product_data['id'] = f"AI-{module.upper()}-{uuid.uuid4().hex[:8]}"
                product_data['manufacturer'] = 'Luiggi Home Master'
                product_data['importedAt'] = datetime.utcnow().isoformat()
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