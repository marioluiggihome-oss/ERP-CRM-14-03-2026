from fastapi import FastAPI, APIRouter, File, UploadFile, Form, HTTPException
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


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

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

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()