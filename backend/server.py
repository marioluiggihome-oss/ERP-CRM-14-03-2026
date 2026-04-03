from fastapi import FastAPI, APIRouter, File, UploadFile, Form, HTTPException, BackgroundTasks, Request, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import hashlib
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict
import uuid
from datetime import datetime, timezone, timedelta
import base64
from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent
import json
import bcrypt
import jwt  # Para decodificar tokens en endpoints de export
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import asyncio
import xlsxwriter
from io import BytesIO
import resend  # Resend como alternativa a SendGrid
from services.security_middleware import SecurityMiddleware
# Servicios de seguridad
from services.jwt_service import (
    create_access_token,
    create_refresh_token,
    verify_access_token,
    verify_refresh_token,
    get_current_user,
    require_auth,
    require_admin,
    JWT_SECRET,
    JWT_ALGORITHM,
    get_token_from_request,
    security
)
from services.rate_limiter import limiter, get_limit, rate_limit_exceeded_handler
from services.audit_service import audit, AuditAction

# Routers modulares
from routes import (
    ia_lab_router,
    auth_router,
    auth_advanced_router,
    products_router,
    clients_router,
    projects_router,
    crm_router,
    despiece_budgeter_router,
    libraries_router,
    montajes_router,
    backup_router,
    armarios_router,
    digitalizador_router,
    crm_module_router,
    orders_router
)
from routes.fabrica import router as fabrica_router
from routes.dashboard import router as dashboard_router
from routes.factory_reports import router as factory_reports_router
from routes.backup import scheduler as backup_scheduler, start_backup_scheduler
from routes.admin import router as admin_router
from routes.exports import router as exports_router
from routes.maintenance import router as maintenance_router
from routes.telemetry import router as telemetry_router
from routes.users import router as users_router
from routes.settings import router as settings_router
from routes.materials import router as materials_router
from routes.expedient import router as expedient_router
from routes.shop_clients import router as shop_clients_router

# Servicios de backup y tracking
from services.backup_service import init_backup_service
from services.activity_tracker import init_activity_tracker, get_tracker, ActivityType

# Modelos compartidos
from models.schemas import (
    StatusCheck, StatusCheckCreate,
    UserModelInternal, UserResponse, UserCreate, UserUpdate,
    ZonePoints, ProductModel, ProductCreate,
    MaterialModel, MaterialCreate,
    BudgetItemModel, ProjectModel, ProjectCreate, ProjectUpdate,
    SettingsModel, SettingsUpdate,
    ClientModel, ClientCreate, ClientUpdate,
    ContactModel, ContactCreate, ContactUpdate,
    OpportunityModel, OpportunityCreate, OpportunityUpdate,
    CalendarEventModel, CalendarEventCreate, CalendarEventUpdate,
    ActivityModel, ActivityCreate, ActivityUpdate,
    DistributorRequest,
    # Despiece
    DespieceItemInput, DespieceRequest, ComponentPiece, FurnitureDespiece, DespieceResponse,
    # Digitalizador
    DigitalizadorMatchedProduct, DigitalizadorLine, DigitalizadorRequest, DigitalizadorResponse,
    DigitalizadorExportRequest, DigitalizadorSaveRequest, DigitalizadorHistoryItem,
    ExpedienteRequest, DigitalizadorToProjectRequest,
    # Armarios
    ArmarioModuleConfig, ArmarioProject, ArmarioProjectCreate, ArmarioProjectUpdate,
    IAConfigRequest, IARenderRequest, IALayoutRequest,
    # Maintenance
    MaintenanceActivateRequest, MaintenanceStatusResponse,
    # Montadores/Instaladores
    MontadorCreate, MontadorUpdate, MontadorResponse,
    MontajeCreate, MontajeUpdate, MontajeResponse
)


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

# Configurar Rate Limiter
app.state.limiter = limiter
app.add_exception_handler(429, rate_limit_exceeded_handler)
app.add_middleware(SecurityMiddleware)
# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Registrar routers modulares
api_router.include_router(ia_lab_router)
api_router.include_router(auth_advanced_router)
api_router.include_router(despiece_budgeter_router)
api_router.include_router(libraries_router)
api_router.include_router(fabrica_router)
api_router.include_router(montajes_router)
api_router.include_router(backup_router)
api_router.include_router(armarios_router)
api_router.include_router(digitalizador_router)
api_router.include_router(crm_module_router)
api_router.include_router(orders_router)
api_router.include_router(dashboard_router)
api_router.include_router(factory_reports_router)
api_router.include_router(admin_router)
api_router.include_router(exports_router)
api_router.include_router(maintenance_router)
api_router.include_router(telemetry_router)
api_router.include_router(users_router)
api_router.include_router(settings_router)
api_router.include_router(materials_router)
api_router.include_router(expedient_router)
api_router.include_router(shop_clients_router)
# Nota: auth, products, clients, projects están en server.py
# Se integrarán gradualmente para evitar conflictos

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
    """Verify a password against its hash (supports bcrypt, sha256, and plain text)"""
    # Si está vacío, rechazar
    if not password or not hashed:
        return False
    
    # Intento 1: bcrypt hash (empieza con $2b$ o $2a$)
    if hashed.startswith('$2b$') or hashed.startswith('$2a$'):
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except:
            pass
    
    # Intento 2: SHA256 hash (64 caracteres hexadecimales)
    if len(hashed) == 64:
        try:
            sha256_hash = hashlib.sha256(password.encode()).hexdigest()
            return sha256_hash == hashed
        except:
            pass
    
    # Intento 3: Plain text (para migración de datos antiguos)
    return password == hashed


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


# =============================================
# SISTEMA DE COLA DE TELEMETRÍA IA
# =============================================
from services.telemetry_queue import (
    create_telemetry_job, 
    get_job_status,
    get_audit_images,
    get_audit_image_detail,
    update_audit_notes
)

@api_router.post("/analyze-product-sheets")
async def analyze_product_sheets(
    module: str = Form(...),
    library: str = Form("ZC"),
    files: List[UploadFile] = File(...)
):
    """
    Analiza fichas de productos usando Gemini Vision API.
    Extrae: código, nombre, dimensiones, puntos por zona, categoría, serie.
    Detecta AUTOMÁTICAMENTE nuevas categorías desde el encabezado de la página.
    """
    try:
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            return {"error": "EMERGENT_LLM_KEY not configured"}
        
        # Log library being used
        logger.info(f"Analyzing product sheets for library: {library}")
        
        products = []
        detected_categories = set()
        skipped_files = []
        
        for file in files:
            # Read file content
            content = await file.read()
            
            # Determine file type and handle accordingly
            filename = file.filename.lower() if file.filename else ""
            content_type = file.content_type or ""
            
            # Check if it's a PDF - Gemini doesn't support PDFs directly
            if filename.endswith('.pdf') or 'pdf' in content_type.lower():
                logger.warning(f"PDF file detected: {file.filename}. PDFs are not directly supported by Gemini Vision. Please convert to JPG/PNG first.")
                skipped_files.append({"filename": file.filename, "reason": "PDFs no soportados. Convierte a JPG/PNG primero."})
                continue  # Skip PDF files for now
            
            # Validate image format
            valid_formats = ['.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp']
            is_valid_image = any(filename.endswith(fmt) for fmt in valid_formats)
            
            if not is_valid_image:
                # Try to detect from content type
                valid_mime_types = ['image/jpeg', 'image/png', 'image/webp', 'image/gif', 'image/bmp']
                if content_type.lower() not in valid_mime_types:
                    logger.warning(f"Unsupported file format: {file.filename} ({content_type}). Skipping.")
                    skipped_files.append({"filename": file.filename, "reason": f"Formato no soportado: {content_type}"})
                    continue
            
            # Validate that we have actual image data
            if len(content) < 100:
                logger.warning(f"File {file.filename} is too small to be a valid image. Skipping.")
                skipped_files.append({"filename": file.filename, "reason": "Archivo demasiado pequeño"})
                continue
            
            # Check magic bytes for common image formats
            magic_bytes = content[:8]
            is_jpeg = magic_bytes[:2] == b'\xff\xd8'
            is_png = magic_bytes[:8] == b'\x89PNG\r\n\x1a\n'
            is_gif = magic_bytes[:6] in (b'GIF87a', b'GIF89a')
            is_webp = magic_bytes[8:12] == b'WEBP' if len(content) > 12 else False
            
            if not (is_jpeg or is_png or is_gif or is_webp):
                # Check if it's actually a PDF masquerading as an image
                if magic_bytes[:4] == b'%PDF':
                    logger.warning(f"File {file.filename} is actually a PDF. PDFs are not supported. Please convert to JPG/PNG.")
                    skipped_files.append({"filename": file.filename, "reason": "Es un PDF. Convierte a JPG/PNG."})
                    continue
                logger.warning(f"File {file.filename} does not appear to be a valid image format. Attempting anyway...")
            
            base64_image = base64.b64encode(content).decode('utf-8')
            
            # Para MV, hacer múltiples pasadas para extraer todos los productos
            if library == 'MV':
                file_products = []
                extracted_codes = set()
                max_passes = 2  # 2 pasadas = hasta 100 productos por imagen (más rápido)
                detected_tariff = None  # Tarifa detectada automáticamente
                
                for pass_num in range(max_passes):
                    # Construir lista de códigos ya extraídos para excluirlos
                    exclude_list = ", ".join(list(extracted_codes)[:50]) if extracted_codes else "ninguno"
                    
                    system_prompt = f"""Eres un experto en digitalización de tarifas de muebles MV (MUEBLES VALENCIA).
Tu tarea es extraer productos de la tabla de tarifas.

═══════════════════════════════════════════════════════════════
PASO 0: DETECTAR NÚMERO DE TARIFA DESDE EL ENCABEZADO
═══════════════════════════════════════════════════════════════
IMPORTANTE: Lee el encabezado/título de la página para identificar el NÚMERO DE TARIFA.
Busca textos como:
- "TARIFA 1", "TARIFA 2", "TARIFA 3" ... "TARIFA 21"
- "T1", "T2", "T3" ... "T21"
- "PRECIO TARIFA 1", "PVP TARIFA 3", etc.

El número de tarifa es CRÍTICO para mapear correctamente los precios.
Si no encuentras un número de tarifa explícito, usa "T1" por defecto.

═══════════════════════════════════════════════════════════════
ESTRUCTURA DE TARIFAS MV:
═══════════════════════════════════════════════════════════════
- Las tablas tienen secciones: ALTO, ALTO CAMPANA, ALTO RINCON, ALTO VITRINA, BAJO, SEMICOLUMNA, COLUMNA, PUERTAS, etc.
- Cada producto tiene un código (A25D/I*, ASCE60D/I*, B30D/I*, etc.)
- Las columnas numéricas (70, 90, 127, 147, etc.) son ALTURAS en cm
- Los valores en las celdas son los PRECIOS

CÓDIGOS DE PRODUCTO MV:
- A = Alto (A25D/I*, A30D/I*, etc.)
- ASCE = Alto Campana Esquina
- AR = Alto Rincon
- AV = Alto Vitrina
- AD = Alto Decorativo
- AE = Alto Escurreplatos
- AM = Alto Microondas
- B = Bajo
- SC = Semicolumna
- C = Columna
- P = Puerta

FORMATO DE SALIDA (JSON):
{{
  "detectedTariff": "T3",
  "products": [
    {{
      "code": "A30D/I*-70",
      "name": "Alto 30 D/I 70cm",
      "category": "ALTO",
      "width": 300,
      "height": 700,
      "points": 45
    }}
  ]
}}

REGLAS:
1. Código = código_producto + "-" + altura (ej: "A30D/I*-70", "ASCE60D/I*-90")
2. points = precio de la celda
3. width = número en el código (A30 = 300mm, A60 = 600mm)
4. height = columna de altura en mm (70 = 700mm, 90 = 900mm)
5. "detectedTariff" debe ser el número de tarifa detectado del encabezado (T1, T2, T3... T21)

{"IMPORTANTE: NO incluyas estos códigos que ya fueron extraídos: " + exclude_list if extracted_codes else ""}

Extrae hasta 50 productos. Responde SOLO con JSON válido."""

                    chat = LlmChat(
                        api_key=api_key,
                        session_id=f"product-analysis-mv-{uuid.uuid4()}",
                        system_message=system_prompt
                    ).with_model("gemini", "gemini-2.0-flash")
                    
                    user_prompt = f"""Analiza esta página de TARIFA MV.
PRIMERO: Detecta el número de tarifa del encabezado (T1, T2, T3... T21).
{"SEGUNDO: Extrae productos DIFERENTES a los ya extraídos." if extracted_codes else "SEGUNDO: Extrae todos los productos que veas."}
Responde SOLO con JSON válido con "detectedTariff" y "products"."""
                    
                    user_message = UserMessage(
                        text=user_prompt,
                        file_contents=[ImageContent(image_base64=base64_image)]
                    )
                    
                    try:
                        response = await chat.send_message(user_message)
                        response_text = str(response).strip() if response else ""
                        
                        # Limpiar markdown
                        if response_text.startswith("```"):
                            response_text = response_text.split("```")[1]
                            if response_text.startswith("json"):
                                response_text = response_text[4:]
                        response_text = response_text.strip()
                        
                        parsed = json.loads(response_text)
                        new_products = parsed.get("products", [])
                        
                        # Detectar tarifa del primer pase
                        if pass_num == 0:
                            detected_tariff = parsed.get("detectedTariff", "T1")
                            # Validar formato de tarifa
                            if not detected_tariff or not detected_tariff.startswith("T"):
                                detected_tariff = "T1"
                            logger.info(f"MV Tarifa detectada automáticamente: {detected_tariff}")
                        
                        # Filtrar productos nuevos (no duplicados)
                        new_count = 0
                        for prod in new_products:
                            code = prod.get("code", "")
                            if code and code not in extracted_codes:
                                prod['id'] = f"AI-{module.upper()}-{uuid.uuid4().hex[:8]}"
                                prod['manufacturer'] = 'MV'
                                prod['module'] = module
                                prod['library'] = library
                                prod['importedAt'] = datetime.now(timezone.utc).isoformat()
                                prod['originalFilename'] = file.filename
                                # Usar tarifa detectada para zonePoints
                                prod['zonePoints'] = {detected_tariff: prod.get('points', 0)}
                                prod['detectedTariff'] = detected_tariff
                                file_products.append(prod)
                                extracted_codes.add(code)
                                new_count += 1
                        
                        logger.info(f"MV Pass {pass_num+1}: {new_count} nuevos productos (total: {len(file_products)}, tarifa: {detected_tariff})")
                        
                        # Si no encontró productos nuevos, terminar
                        if new_count == 0:
                            break
                            
                    except Exception as pass_error:
                        logger.warning(f"MV Pass {pass_num+1} error: {pass_error}")
                        break
                
                products.extend(file_products)
                logger.info(f"MV Total from {file.filename}: {len(file_products)} productos (tarifa detectada: {detected_tariff})")
                continue  # Saltar el procesamiento de ZC para este archivo
                
            else:
                # Código original para ZC
                system_prompt = """Eres un experto en digitalización de tarifas técnicas de muebles de cocina ZONA COCINAS.
Tu tarea es extraer TODOS los productos visibles en la imagen de forma estructurada.

═══════════════════════════════════════════════════════════════
PASO 1: DETECTAR CATEGORÍA PRINCIPAL DESDE EL ENCABEZADO
═══════════════════════════════════════════════════════════════
Lee el título/encabezado de CADA página para identificar la categoría.
El encabezado suele estar en la parte superior con formato:
"PROGRAMA ESTÁNDAR - [TIPO DE MÓDULO] - [SERIE/FONDO]"

CATEGORÍAS PRINCIPALES DEL CATÁLOGO ZONA COCINAS:

📦 MÓDULOS ALTOS (category: "ALTOS"):
   - "ALTOS 35 FONDO 58" → series: "ALTOS 35 F58"
   - "ALTOS 40 FONDO 33" → series: "ALTOS 40 F33"
   - "ALTOS ABATIBLES" → series: "ABATIBLES"
   - "ALTOS ESQUINEROS" → series: "ESQUINEROS"
   - Códigos empiezan por: 35A, 40A, 35AB, etc.

📦 MÓDULOS BAJOS (category: "BAJOS"):
   - "BAJOS 70 FONDO ESTÁNDAR" → series: "BAJOS 70"
   - "BAJOS 80 FONDO ESTÁNDAR" → series: "BAJOS 80"
   - "BAJOS FREGADERO" → series: "FREGADERO"
   - "BAJOS HORNO" → series: "HORNO"
   - "BAJOS ESQUINEROS" → series: "ESQUINEROS"
   - Códigos empiezan por: 7B, 8B, 70B, 80B, etc.

📦 SEMICOLUMNAS (category: "SEMICOLUMNAS"):
   - "SEMICOLUMNAS 135/140" → series: "SC 135-140"
   - "SEMICOLUMNAS 160/165" → series: "SC 160-165"
   - Códigos empiezan por: 135SC, 140SC, 160SC, etc.

📦 COLUMNAS (category: "COLUMNAS"):
   - "COLUMNAS 195/200" → series: "COL 195-200"
   - "COLUMNAS 215/220" → series: "COL 215-220"
   - "COLUMNAS DESPENSA" → series: "DESPENSA"
   - "COLUMNAS HORNO/MICRO" → series: "HORNO-MICRO"
   - Códigos empiezan por: 195C, 200C, 215C, etc.

🚪 PUERTAS Y VITRINAS (category: "PUERTAS"):
   - "PUERTAS" → series: "PUERTAS"
   - "VITRINAS" → series: "VITRINAS"
   - "PUERTAS LACADAS" → series: "LACADAS"
   - Códigos empiezan por: PTA_, VIT_, etc.

🔧 ACCESORIOS (category: "ACCESORIOS"):
   - "ACCESORIOS" → series: "ACCESORIOS"
   - "HERRAJES" → series: "HERRAJES"
   - "TIRADORES" → series: "TIRADORES"

📐 OTROS ELEMENTOS:
   - "ZÓCALOS Y CORNISAS" → category: "ZOCALOS"
   - "ENCIMERAS" → category: "ENCIMERAS"
   - "ELECTRODOMÉSTICOS" → category: "ELECTRO"
   - "COMPLEMENTOS" → category: "COMPLEMENTOS"

═══════════════════════════════════════════════════════════════
PASO 2: EXTRAER CÓDIGOS Y PRECIOS
═══════════════════════════════════════════════════════════════
Para CADA fila de la tabla:
1. Lee el CÓDIGO exacto (primera columna, ej: 35A1P58350)
2. Lee los 12 valores de precio Z1 a Z12 (de izquierda a derecha)

DECODIFICACIÓN DE CÓDIGOS:
- 35A1P58350: 35=altura(cm), A=alto, 1P=1puerta, 58=fondo(cm), 350=ancho(mm)
- 35A2P58600: 35=altura, A=alto, 2P=2puertas, 58=fondo, 600=ancho
- 7B1P300: 7=70cm altura, B=bajo, 1P=1puerta, 300=ancho(mm)
- 80B2P600: 80=80cm altura, B=bajo, 2P=2puertas, 600=ancho
- 135SC1P58450: 135=altura, SC=semicolumna, 1P=1puerta, 58=fondo, 450=ancho
- 200C2P60600: 200=altura, C=columna, 2P=2puertas, 60=fondo, 600=ancho
- PTA_ZC898X298: PTA=puerta, ZC=serie, 898=ancho(mm), 298=alto(mm)

═══════════════════════════════════════════════════════════════
FORMATO DE RESPUESTA JSON:
═══════════════════════════════════════════════════════════════
{
  "detectedCategory": "ALTOS|BAJOS|SEMICOLUMNAS|COLUMNAS|PUERTAS|ACCESORIOS|etc",
  "detectedSubcategory": "Serie o tipo específico del encabezado",
  "pageTitle": "Texto exacto del encabezado de la página",
  "products": [
    {
      "code": "CÓDIGO_EXACTO",
      "name": "Descripción: [Tipo] [Altura]cm [NºPuertas] [Ancho]mm",
      "category": "CATEGORÍA",
      "series": "Serie del encabezado",
      "visualType": "1P/2P/ABATIBLE/VITRINA/FREGADERO/etc",
      "width": ancho_mm,
      "height": altura_cm,
      "depth": fondo_cm,
      "points": valor_Z1,
      "zonePoints": {"Z1":n,"Z2":n,"Z3":n,"Z4":n,"Z5":n,"Z6":n,"Z7":n,"Z8":n,"Z9":n,"Z10":n,"Z11":n,"Z12":n}
    }
  ]
}

REGLAS CRÍTICAS:
✅ Lee el encabezado EXACTO de la página para determinar categoría
✅ Extrae TODOS los productos de la tabla, no solo algunos
✅ Los códigos deben ser EXACTOS como aparecen
✅ Z1 es el PRIMER precio de cada fila (columna después del código)
✅ Responde SOLO con JSON válido, sin explicaciones"""
            
            # Create Gemini chat with vision
            chat = LlmChat(
                api_key=api_key,
                session_id=f"product-analysis-{uuid.uuid4()}",
                system_message=system_prompt
            ).with_model("gemini", "gemini-2.0-flash")
            
            # Create message with image - different prompt for MV vs ZC
            if library == 'MV':
                user_prompt = """Analiza esta página de TARIFA MV.
Extrae los productos de la tabla siguiendo el formato JSON especificado.
MÁXIMO 30 productos. Si hay más, extrae solo los primeros 30.
Responde SOLO con JSON válido."""
            else:
                user_prompt = """Analiza esta página de tarifa técnica de ZONA COCINAS.

INSTRUCCIONES:
1. Lee el ENCABEZADO de la página para identificar: ALTOS, BAJOS, SEMICOLUMNAS, COLUMNAS, PUERTAS, ACCESORIOS, etc.
2. Identifica la SERIE (ej: "ALTOS 35 FONDO 58", "BAJOS 70", "COLUMNAS 200")
3. Extrae TODOS los códigos de productos de la tabla (35A1P58350, 7B1P300, etc.)
4. Para cada producto, lee los 12 precios por zona (Z1 a Z12)
5. Decodifica las dimensiones del código

Responde ÚNICAMENTE con el JSON estructurado. No añadas explicaciones."""
            
            # Create the user message with image
            user_message = UserMessage(
                text=user_prompt,
                file_contents=[ImageContent(image_base64=base64_image)]
            )
            
            # Get AI response
            response = await chat.send_message(user_message)
            
            # Parse JSON response
            try:
                # Clean response (remove markdown code blocks if present)
                clean_response = response.strip()
                
                # Handle markdown code blocks more robustly
                if '```json' in clean_response:
                    # Extract content between ```json and ```
                    start = clean_response.find('```json') + 7
                    end = clean_response.find('```', start)
                    if end == -1:
                        # No closing ```, take everything after ```json
                        clean_response = clean_response[start:].strip()
                    else:
                        clean_response = clean_response[start:end].strip()
                elif '```' in clean_response:
                    # Generic code block
                    start = clean_response.find('```') + 3
                    end = clean_response.find('```', start)
                    if end == -1:
                        clean_response = clean_response[start:].strip()
                    else:
                        clean_response = clean_response[start:end].strip()
                
                # Try to find JSON object or array
                import re
                if not clean_response.startswith('{') and not clean_response.startswith('['):
                    json_match = re.search(r'(\{[\s\S]*\}|\[[\s\S]*\])', clean_response)
                    if json_match:
                        clean_response = json_match.group(1)
                
                parsed_data = json.loads(clean_response)
                
                # Handle new format with detectedCategory
                if isinstance(parsed_data, dict) and 'products' in parsed_data:
                    # New format with category detection
                    file_category = parsed_data.get('detectedCategory', 'OTROS')
                    file_subcategory = parsed_data.get('detectedSubcategory', '')
                    product_list = parsed_data.get('products', [])
                    detected_categories.add(file_category)
                    logger.info(f"Detected category: {file_category}, subcategory: {file_subcategory}")
                elif isinstance(parsed_data, list):
                    # Old format - array of products
                    product_list = parsed_data
                    file_category = None
                    file_subcategory = None
                else:
                    # Single product
                    product_list = [parsed_data]
                    file_category = parsed_data.get('category', 'OTROS')
                    file_subcategory = None
                
                for product_data in product_list:
                    # Add metadata
                    product_data['id'] = f"AI-{module.upper()}-{uuid.uuid4().hex[:8]}"
                    product_data['manufacturer'] = 'Zona Cocinas'
                    product_data['module'] = module
                    product_data['library'] = library  # Usar la biblioteca seleccionada (MV o ZC)
                    product_data['importedAt'] = datetime.now(timezone.utc).isoformat()
                    product_data['originalFilename'] = file.filename
                    
                    # Apply detected category if product doesn't have one
                    if file_category and not product_data.get('category'):
                        product_data['category'] = file_category
                    if file_subcategory and not product_data.get('series'):
                        product_data['series'] = file_subcategory
                    
                    products.append(product_data)
                
            except json.JSONDecodeError as e:
                # Try to repair truncated JSON
                logger.warning(f"JSON parse error, attempting repair: {e}")
                try:
                    # Try to extract complete products from truncated response
                    import re
                    # Find all complete product objects
                    product_pattern = r'\{\s*"code":\s*"[^"]+",\s*"name":\s*"[^"]*",\s*"category":\s*"[^"]*"[^}]*"zonePoints":\s*\{[^}]+\}\s*\}'
                    found_products = re.findall(product_pattern, clean_response)
                    
                    if found_products:
                        logger.info(f"Recovered {len(found_products)} products from truncated response")
                        # Extract category from response
                        cat_match = re.search(r'"detectedCategory":\s*"([^"]+)"', clean_response)
                        file_category = cat_match.group(1) if cat_match else 'OTROS'
                        detected_categories.add(file_category)
                        
                        for prod_json in found_products:
                            try:
                                prod = json.loads(prod_json)
                                prod['id'] = f"AI-{module.upper()}-{uuid.uuid4().hex[:8]}"
                                prod['manufacturer'] = 'Zona Cocinas'
                                prod['module'] = module
                                prod['library'] = library  # Usar la biblioteca seleccionada (MV o ZC)
                                prod['importedAt'] = datetime.now(timezone.utc).isoformat()
                                prod['originalFilename'] = file.filename
                                if not prod.get('category'):
                                    prod['category'] = file_category
                                products.append(prod)
                            except:
                                pass
                    else:
                        # Could not recover
                        logger.error(f"Could not repair JSON: {response[:500]}")
                        products.append({
                            "error": f"No se pudo parsear la respuesta para {file.filename}",
                            "raw_response": response[:500]
                        })
                except Exception as repair_error:
                    logger.error(f"Error repairing JSON: {repair_error}. Original response: {response[:500]}")
                    products.append({
                        "error": f"No se pudo parsear la respuesta para {file.filename}",
                        "raw_response": response[:500]
                    })
        
        return {
            "success": True,
            "count": len(products),
            "products": products,
            "detectedCategories": list(detected_categories),
            "skippedFiles": skipped_files
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


# ============================================
# DISTRIBUTOR REQUEST ENDPOINTS
# ============================================

class DistributorRequest(BaseModel):
    """Solicitud de alta de distribuidor"""
    companyName: str
    contactName: str
    email: str
    phone: str
    city: str = ""
    province: str = ""
    message: str = ""


@api_router.post("/distributor/request")
@limiter.limit(get_limit("register"))
async def request_distributor(request: Request, data: DistributorRequest):
    """
    Recibir solicitud de alta de distribuidor y enviar email al administrador
    """
    try:
        # Guardar la solicitud en la base de datos
        request_data = {
            "id": f"dist-req-{uuid.uuid4().hex[:8]}",
            "companyName": data.companyName,
            "contactName": data.contactName,
            "email": data.email,
            "phone": data.phone,
            "city": data.city,
            "province": data.province,
            "message": data.message,
            "status": "pending",  # pending, approved, rejected
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "processedAt": None,
            "processedBy": None,
            "notes": ""
        }
        
        await db.distributor_requests.insert_one(request_data)
        
        # Enviar email al administrador
        admin_email = "mario@luiggihome.es"
        
        email_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #f8fafc; padding: 20px;">
            <div style="background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%); color: white; padding: 30px; border-radius: 16px 16px 0 0; text-align: center;">
                <h1 style="margin: 0; font-size: 24px;">LUIGGI HOME</h1>
                <p style="margin: 8px 0 0 0; opacity: 0.8; font-size: 14px;">Nueva Solicitud de Distribuidor</p>
            </div>
            
            <div style="background: white; padding: 30px; border-radius: 0 0 16px 16px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin-bottom: 20px; border-radius: 0 8px 8px 0;">
                    <p style="margin: 0; color: #92400e; font-weight: bold; font-size: 14px;">
                        ⚡ Nueva solicitud de alta pendiente de revisión
                    </p>
                </div>
                
                <h2 style="color: #1e1b4b; margin: 0 0 20px 0; font-size: 18px; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px;">
                    Datos del Solicitante
                </h2>
                
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 12px 0; border-bottom: 1px solid #f1f5f9; color: #64748b; font-size: 13px; width: 35%;">
                            <strong>Empresa:</strong>
                        </td>
                        <td style="padding: 12px 0; border-bottom: 1px solid #f1f5f9; color: #1e293b; font-size: 14px; font-weight: 600;">
                            {data.companyName}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 12px 0; border-bottom: 1px solid #f1f5f9; color: #64748b; font-size: 13px;">
                            <strong>Contacto:</strong>
                        </td>
                        <td style="padding: 12px 0; border-bottom: 1px solid #f1f5f9; color: #1e293b; font-size: 14px;">
                            {data.contactName}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 12px 0; border-bottom: 1px solid #f1f5f9; color: #64748b; font-size: 13px;">
                            <strong>Email:</strong>
                        </td>
                        <td style="padding: 12px 0; border-bottom: 1px solid #f1f5f9;">
                            <a href="mailto:{data.email}" style="color: #ea580c; text-decoration: none; font-weight: 600;">{data.email}</a>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 12px 0; border-bottom: 1px solid #f1f5f9; color: #64748b; font-size: 13px;">
                            <strong>Teléfono:</strong>
                        </td>
                        <td style="padding: 12px 0; border-bottom: 1px solid #f1f5f9;">
                            <a href="tel:{data.phone}" style="color: #ea580c; text-decoration: none; font-weight: 600;">{data.phone}</a>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 12px 0; border-bottom: 1px solid #f1f5f9; color: #64748b; font-size: 13px;">
                            <strong>Ubicación:</strong>
                        </td>
                        <td style="padding: 12px 0; border-bottom: 1px solid #f1f5f9; color: #1e293b; font-size: 14px;">
                            {data.city}{', ' + data.province if data.province else ''}{' - Sin especificar' if not data.city else ''}
                        </td>
                    </tr>
                </table>
                
                {f'''
                <div style="margin-top: 20px; padding: 15px; background: #f8fafc; border-radius: 8px;">
                    <p style="margin: 0 0 8px 0; color: #64748b; font-size: 12px; font-weight: bold; text-transform: uppercase;">Mensaje:</p>
                    <p style="margin: 0; color: #475569; font-size: 14px; line-height: 1.6;">{data.message}</p>
                </div>
                ''' if data.message else ''}
                
                <div style="margin-top: 30px; text-align: center;">
                    <p style="color: #94a3b8; font-size: 12px; margin: 0;">
                        Solicitud recibida el {datetime.now(timezone.utc).strftime('%d/%m/%Y a las %H:%M')} UTC
                    </p>
                </div>
            </div>
            
            <div style="text-align: center; padding: 20px; color: #94a3b8; font-size: 11px;">
                <p style="margin: 0;">LUIGGI HOME - Sistema de Presupuestos Profesional</p>
            </div>
        </div>
        """
        
        # Intentar enviar email
        sendgrid_key = os.environ.get('SENDGRID_API_KEY')
        if sendgrid_key:
            try:
                sg = SendGridAPIClient(sendgrid_key)
                message = Mail(
                    from_email=os.environ.get('SENDGRID_FROM_EMAIL', 'noreply@luiggihome.es'),
                    to_emails=admin_email,
                    subject=f"🏢 Nueva Solicitud de Distribuidor: {data.companyName}",
                    html_content=email_html
                )
                sg.send(message)
                logger.info(f"Distributor request email sent to {admin_email}")
            except Exception as e:
                logger.error(f"Error sending distributor request email: {e}")
        else:
            logger.warning("SendGrid not configured - distributor request email not sent")
        
        # Auditoría
        audit.log(
            AuditAction.USER_CREATE,
            resource_type="distributor_request",
            resource_id=request_data["id"],
            request=request,
            details={"company": data.companyName, "email": data.email}
        )
        
        if "_id" in request_data:
            del request_data["_id"]
        
        return {
            "success": True,
            "message": "Solicitud enviada correctamente",
            "requestId": request_data["id"]
        }
        
    except Exception as e:
        logger.error(f"Error processing distributor request: {e}")
        raise HTTPException(status_code=500, detail="Error al procesar la solicitud")


@api_router.get("/distributor/requests")
async def get_distributor_requests(
    status: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Obtener todas las solicitudes de distribuidores (solo admins)"""
    # Verificar que es admin
    if credentials:
        try:
            payload = verify_access_token(credentials.credentials)
            if not payload.get("isAdmin"):
                raise HTTPException(status_code=403, detail="Acceso denegado")
        except:
            raise HTTPException(status_code=401, detail="Token inválido")
    else:
        raise HTTPException(status_code=401, detail="Autenticación requerida")
    
    query = {}
    if status:
        query["status"] = status
    
    requests = await db.distributor_requests.find(query, {"_id": 0}).sort("createdAt", -1).to_list(500)
    return requests


@api_router.put("/distributor/requests/{request_id}")
async def update_distributor_request(
    request_id: str,
    data: dict,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Actualizar estado de una solicitud de distribuidor (solo admins)"""
    # Verificar que es admin
    if credentials:
        try:
            payload = verify_access_token(credentials.credentials)
            if not payload.get("isAdmin"):
                raise HTTPException(status_code=403, detail="Acceso denegado")
            admin_id = payload.get("sub")
            admin_username = payload.get("username")
        except:
            raise HTTPException(status_code=401, detail="Token inválido")
    else:
        raise HTTPException(status_code=401, detail="Autenticación requerida")
    
    existing = await db.distributor_requests.find_one({"id": request_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    
    update_data = {
        "status": data.get("status", existing.get("status")),
        "notes": data.get("notes", existing.get("notes", "")),
        "processedAt": datetime.now(timezone.utc).isoformat(),
        "processedBy": admin_username
    }
    
    await db.distributor_requests.update_one({"id": request_id}, {"$set": update_data})
    
    updated = await db.distributor_requests.find_one({"id": request_id}, {"_id": 0})
    return updated


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
    return {
        "segments": [
            {"id": "particular", "name": "Particular"},
            {"id": "profesional", "name": "Profesional"},
            {"id": "constructor", "name": "Constructor/Promotor"},
            {"id": "tienda", "name": "Tienda/Distribuidor"},
            {"id": "mayorista", "name": "Mayorista"}
        ]
    }

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
async def delete_client(client_id: str, force: bool = False):
    """Eliminar un cliente. Si force=True, desvincula usuarios automáticamente."""
    # Check if client has linked users
    linked_users = await db.users.count_documents({"linkedClientId": client_id})
    if linked_users > 0:
        if force:
            # Admin force delete: unlink users first
            await db.users.update_many(
                {"linkedClientId": client_id},
                {"$set": {"linkedClientId": None}}
            )
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"No se puede eliminar: {linked_users} usuario(s) vinculado(s). Use force=true para desvincular y eliminar."
            )
    
    result = await db.clients.delete_one({"id": client_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    if linked_users > 0 and force:
        return {"message": f"Cliente eliminado. {linked_users} usuario(s) desvinculado(s)."}
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
@limiter.limit(get_limit("login"))
async def login(request: Request, credentials: dict):
    """Iniciar sesión con verificación de password hasheado + JWT + Auditoría"""
    username = credentials.get("username", "").strip()
    password = credentials.get("password", "").strip()
    
    # Buscar por username exacto o en mayúsculas (compatibilidad con cuentas antiguas)
    user = await db.users.find_one({"username": username}, {"_id": 0})
    if not user:
        # Intentar búsqueda en mayúsculas
        user = await db.users.find_one({"username": username.upper()}, {"_id": 0})
    if not user:
        # Intentar búsqueda case-insensitive
        user = await db.users.find_one(
            {"username": {"$regex": f"^{username}$", "$options": "i"}}, 
            {"_id": 0}
        )
    
    if not user:
        # Auditoría: login fallido
        audit.log_login_failed(username, request, "user_not_found")
        raise HTTPException(status_code=401, detail="Credenciales no válidas")
    
    # Verify password (supports both hashed and plain text for migration)
    if not verify_password(password, user.get("password", "")):
        # Auditoría: login fallido
        audit.log_login_failed(username, request, "invalid_password")
        raise HTTPException(status_code=401, detail="Credenciales no válidas")
    
    if not user.get("isActive", True):
        # Auditoría: cuenta desactivada
        audit.log_login_failed(username, request, "account_disabled")
        raise HTTPException(status_code=401, detail="Cuenta desactivada")
    
    # Verificar fecha de caducidad del acceso
    expiration_date = user.get("accessExpirationDate")
    if expiration_date:
        try:
            exp_date = datetime.fromisoformat(expiration_date.replace('Z', '+00:00')) if isinstance(expiration_date, str) else expiration_date
            if exp_date.date() < datetime.now().date():
                audit.log_login_failed(username, request, "access_expired")
                raise HTTPException(
                    status_code=401, 
                    detail=f"Tu acceso expiró el {exp_date.strftime('%d/%m/%Y')}. Contacta con el administrador para renovar."
                )
        except (ValueError, AttributeError) as e:
            logger.warning(f"Error parsing expiration date for {username}: {e}")
    
    # Crear tokens JWT
    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user.get("id"))
    
    # Auditoría: login exitoso
    audit.log_login_success(user.get("id"), username, request)
    
    # Tracking de actividad
    tracker = get_tracker()
    if tracker:
        await tracker.track(
            user_id=user.get("id"),
            username=username,
            activity_type=ActivityType.LOGIN,
            ip_address=request.client.host if request.client else None
        )
    
    # Return user without password + tokens
    return {
        "success": True, 
        "user": user_to_response(user),
        "tokens": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 86400  # 24 horas en segundos
        }
    }


@api_router.post("/auth/refresh")
@limiter.limit(get_limit("login"))
async def refresh_token(request: Request, data: dict):
    """Renovar access token usando refresh token"""
    refresh_token_str = data.get("refresh_token", "")
    
    if not refresh_token_str:
        raise HTTPException(status_code=400, detail="Refresh token requerido")
    
    try:
        payload = verify_refresh_token(refresh_token_str)
        user_id = payload.get("sub")
        
        # Obtener usuario actualizado
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="Usuario no encontrado")
        
        if not user.get("isActive", True):
            raise HTTPException(status_code=401, detail="Cuenta desactivada")
        
        # Crear nuevo access token
        new_access_token = create_access_token(user)
        
        # Auditoría
        audit.log(
            AuditAction.TOKEN_REFRESH,
            user_id=user_id,
            username=user.get("username"),
            resource_type="session",
            request=request
        )
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": 86400
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(status_code=401, detail="Token inválido")


@api_router.post("/auth/logout")
async def logout(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Cerrar sesión (invalida el token en el cliente)"""
    user = None
    if credentials:
        try:
            payload = verify_access_token(credentials.credentials)
            user = {"id": payload.get("sub"), "username": payload.get("username")}
        except:
            pass
    
    if user:
        audit.log(
            AuditAction.LOGOUT,
            user_id=user.get("id"),
            username=user.get("username"),
            resource_type="session",
            request=request
        )
    
    return {"success": True, "message": "Sesión cerrada"}


@api_router.get("/auth/me")
async def get_current_user_info(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Obtener información del usuario actual desde el token"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Token requerido")
    
    try:
        payload = verify_access_token(credentials.credentials)
        user_id = payload.get("sub")
        
        # Obtener datos completos del usuario
        user = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        return {"success": True, "user": user}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get current user error: {e}")
        raise HTTPException(status_code=401, detail="Token inválido")

# ============================================
# PRODUCT ENDPOINTS
# ============================================

@api_router.get("/products")
async def get_products(module: Optional[str] = None, library: Optional[str] = None):
    """Obtener todos los productos, opcionalmente filtrados por módulo y biblioteca"""
    query = {}
    if module:
        query["module"] = module
    if library:
        query["library"] = library.upper()
    products = await db.products.find(query, {"_id": 0}).to_list(10000)
    
    # Asegurar que todos los productos tengan los campos mínimos requeridos
    for p in products:
        if not p.get('id'):
            p['id'] = f"prod-{p.get('code', 'unknown')[:8]}"
        if not p.get('points') and p.get('zonePoints'):
            zone_points = p['zonePoints']
            if isinstance(zone_points, dict):
                p['points'] = zone_points.get('Z1', 0) or list(zone_points.values())[0] if zone_points else 0
    
    return products


# Importar servicio de exportación de catálogo
from services.catalog_export import generate_catalog_excel_with_images, generate_catalog_pdf_with_images

@api_router.get("/products/export/excel")
async def export_products_to_excel(
    module: Optional[str] = None,
    category: Optional[str] = None,
    series: Optional[str] = None,
    programa: Optional[str] = None,
    tipo: Optional[str] = Query(default="montada", description="montada o despiece"),
    with_images: bool = True
):
    """
    Exportar catálogo de productos a Excel con imágenes SVG.
    - tipo=montada: Exporta productos de muebles ensamblados (colección 'products')
    - tipo=despiece: Exporta productos de tableros (colección 'despiece_products')
    Cambia ZONA por GRUPO (Z1→G1, Z2→G2, etc.)
    """
    if tipo == "despiece":
        # Exportar productos de DESPIECE (tableros)
        query = {}
        if category:
            query["category"] = category
        
        products = await db.despiece_products.find(query, {"_id": 0}).sort([("collection", 1), ("color", 1)]).to_list(10000)
        
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Catálogo Despiece')
        
        header_format = workbook.add_format({'bold': True, 'bg_color': '#7c3aed', 'font_color': 'white', 'align': 'center', 'valign': 'vcenter', 'border': 1})
        cell_format = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'border': 1})
        price_format = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'border': 1, 'num_format': '#,##0.00 €'})
        
        headers = ['CÓDIGO', 'NOMBRE', 'FABRICANTE', 'COLECCIÓN', 'COLOR', 'ACABADO', 'GROSOR', 'CATEGORÍA', 'G1 €/m²', 'G2 €/m²', 'G3 €/m²']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
            worksheet.set_column(col, col, 15 if col < 2 else 12)
        
        for row_num, product in enumerate(products, start=1):
            worksheet.write(row_num, 0, product.get('code', ''), cell_format)
            worksheet.write(row_num, 1, product.get('name', ''), cell_format)
            worksheet.write(row_num, 2, product.get('manufacturer', ''), cell_format)
            worksheet.write(row_num, 3, product.get('collection', ''), cell_format)
            worksheet.write(row_num, 4, product.get('color', ''), cell_format)
            worksheet.write(row_num, 5, product.get('finish', ''), cell_format)
            worksheet.write(row_num, 6, product.get('thickness', 0), cell_format)
            worksheet.write(row_num, 7, product.get('category', ''), cell_format)
            worksheet.write(row_num, 8, product.get('priceZ1', 0), price_format)
            worksheet.write(row_num, 9, product.get('priceZ2', 0), price_format)
            worksheet.write(row_num, 10, product.get('priceZ3', 0), price_format)
        
        workbook.close()
        output.seek(0)
        
        filename = f"catalogo_despiece_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    else:
        # Exportar productos de MONTADA (muebles)
        query = {}
        if module:
            query["module"] = module
        if category:
            query["category"] = category
        if series:
            query["series"] = series
        if programa:
            query["programa"] = programa
        
        products = await db.products.find(query, {"_id": 0}).sort([("programa", 1), ("category", 1), ("series", 1), ("code", 1)]).to_list(10000)
        
        if with_images:
            output = await generate_catalog_excel_with_images(products, module)
        else:
            # Versión sin imágenes (más rápida)
            output = BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            worksheet = workbook.add_worksheet('Catálogo Montada')
            
            header_format = workbook.add_format({'bold': True, 'bg_color': '#1e293b', 'font_color': 'white', 'align': 'center', 'valign': 'vcenter', 'border': 1})
            cell_format = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'border': 1})
            
            headers = ['REF', 'DESCRIPCIÓN', 'PROGRAMA', 'AN', 'AL', 'FO', 'CATEGORÍA', 'SERIE', 'G1', 'G2', 'G3', 'G4', 'G5', 'G6']
            for col, header in enumerate(headers):
                worksheet.write(0, col, header, header_format)
            
            for row_num, product in enumerate(products, start=1):
                worksheet.write(row_num, 0, product.get('code', ''), cell_format)
                worksheet.write(row_num, 1, product.get('name', ''), cell_format)
                worksheet.write(row_num, 2, product.get('programa', ''), cell_format)
                worksheet.write(row_num, 3, product.get('width', ''), cell_format)
                worksheet.write(row_num, 4, product.get('height', ''), cell_format)
                worksheet.write(row_num, 5, product.get('depth', ''), cell_format)
                worksheet.write(row_num, 6, product.get('category', ''), cell_format)
                worksheet.write(row_num, 7, product.get('series', ''), cell_format)
                zone_points = product.get('zonePoints', {}) or {}
                for i, zk in enumerate(['Z1', 'Z2', 'Z3', 'Z4', 'Z5', 'Z6']):
                    worksheet.write(row_num, 8 + i, zone_points.get(zk, 0) or 0, cell_format)
            
            workbook.close()
            output.seek(0)
        
        filename = f"catalogo_montada_{programa or 'completo'}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@api_router.get("/products/export/pdf")
async def export_products_to_pdf(
    module: Optional[str] = None,
    category: Optional[str] = None,
    series: Optional[str] = None
):
    """
    Exportar catálogo de productos a PDF con imágenes SVG.
    Cambia ZONA por GRUPO (Z1→G1, Z2→G2, etc.)
    Limitado a 500 productos por rendimiento (usar Excel para catálogo completo).
    """
    query = {}
    if module:
        query["module"] = module
    if category:
        query["category"] = category
    if series:
        query["series"] = series
    
    products = await db.products.find(query, {"_id": 0}).sort([("category", 1), ("series", 1), ("code", 1)]).to_list(10000)
    
    output = await generate_catalog_pdf_with_images(products, module)
    
    filename = f"catalogo_luiggi_{module or 'completo'}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    
    return StreamingResponse(
        output,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@api_router.get("/products/export/library/{library_code}")
async def export_library_catalog(library_code: str):
    """
    Exportar catálogo completo de una biblioteca específica (ZC o MV) a Excel.
    - ZC: Exporta con columnas Z1-Z12 (puntos por zona)
    - MV: Exporta con columnas T1-T21 (puntos por tarifa)
    """
    library_code = library_code.upper()
    
    # Validar biblioteca
    if library_code not in ['ZC', 'MV']:
        raise HTTPException(status_code=400, detail=f"Biblioteca '{library_code}' no válida. Use 'ZC' o 'MV'.")
    
    # Obtener productos de la biblioteca
    query = {"library": library_code}
    products = await db.products.find(query, {"_id": 0}).sort([
        ("category", 1), ("series", 1), ("code", 1)
    ]).to_list(10000)
    
    if not products:
        raise HTTPException(status_code=404, detail=f"No se encontraron productos para la biblioteca {library_code}")
    
    # Crear Excel
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet(f'Catálogo {library_code}')
    
    # Formatos
    header_format = workbook.add_format({
        'bold': True, 
        'bg_color': '#1e3a5f' if library_code == 'ZC' else '#2d5016',
        'font_color': 'white', 
        'align': 'center', 
        'valign': 'vcenter', 
        'border': 1,
        'font_size': 10
    })
    cell_format = workbook.add_format({
        'align': 'center', 
        'valign': 'vcenter', 
        'border': 1,
        'font_size': 9
    })
    text_format = workbook.add_format({
        'align': 'left', 
        'valign': 'vcenter', 
        'border': 1,
        'font_size': 9
    })
    number_format = workbook.add_format({
        'align': 'center', 
        'valign': 'vcenter', 
        'border': 1,
        'font_size': 9,
        'num_format': '0'
    })
    
    # Definir columnas según biblioteca
    if library_code == 'ZC':
        # ZC usa zonas Z1-Z12
        zone_headers = ['Z1', 'Z2', 'Z3', 'Z4', 'Z5', 'Z6', 'Z7', 'Z8', 'Z9', 'Z10', 'Z11', 'Z12']
        headers = ['REF', 'DESCRIPCIÓN', 'CATEGORÍA', 'SERIE', 'AN', 'AL', 'FO'] + zone_headers
    else:
        # MV usa tarifas T1-T21
        tariff_headers = [f'T{i}' for i in range(1, 22)]
        headers = ['REF', 'DESCRIPCIÓN', 'CATEGORÍA', 'SERIE', 'AN', 'AL', 'FO'] + tariff_headers
    
    # Escribir encabezados
    col_widths = [12, 35, 20, 15, 6, 6, 6] + [6] * (len(headers) - 7)
    for col, (header, width) in enumerate(zip(headers, col_widths)):
        worksheet.write(0, col, header, header_format)
        worksheet.set_column(col, col, width)
    
    # Escribir datos
    for row_num, product in enumerate(products, start=1):
        # Datos básicos
        worksheet.write(row_num, 0, product.get('code', ''), cell_format)
        worksheet.write(row_num, 1, product.get('name', ''), text_format)
        worksheet.write(row_num, 2, product.get('category', ''), cell_format)
        worksheet.write(row_num, 3, product.get('series', ''), cell_format)
        worksheet.write(row_num, 4, product.get('width', 0) or 0, number_format)
        worksheet.write(row_num, 5, product.get('height', 0) or 0, number_format)
        worksheet.write(row_num, 6, product.get('depth', 0) or 0, number_format)
        
        # Puntos por zona/tarifa
        zone_points = product.get('zonePoints', {}) or {}
        if library_code == 'ZC':
            for i, zk in enumerate(['Z1', 'Z2', 'Z3', 'Z4', 'Z5', 'Z6', 'Z7', 'Z8', 'Z9', 'Z10', 'Z11', 'Z12']):
                worksheet.write(row_num, 7 + i, zone_points.get(zk, 0) or 0, number_format)
        else:
            for i in range(1, 22):
                tk = f'T{i}'
                worksheet.write(row_num, 7 + i - 1, zone_points.get(tk, 0) or 0, number_format)
    
    # Ajustar altura de filas
    worksheet.set_default_row(18)
    worksheet.set_row(0, 25)  # Header más alto
    
    # Congelar encabezados
    worksheet.freeze_panes(1, 0)
    
    workbook.close()
    output.seek(0)
    
    filename = f"catalogo_{library_code}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


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

@api_router.post("/products/bulk")
async def create_products_bulk(products: List[dict]):
    """Crear múltiples productos - acepta datos flexibles del importador IA"""
    created = []
    errors = []
    duplicates = 0
    
    for idx, product_data in enumerate(products):
        try:
            # Clean and normalize the data
            clean_data = {
                "code": str(product_data.get("code", "")).upper().strip(),
                "name": str(product_data.get("name", "")),
                "category": str(product_data.get("category", "")),
                "series": str(product_data.get("series", "")),
                "visualType": str(product_data.get("visualType", "")),
                "width": float(product_data.get("width", 0) or 0),
                "height": float(product_data.get("height", 0) or 0),
                "depth": float(product_data.get("depth", 0) or 0),
                "manufacturer": str(product_data.get("manufacturer", "Zona Cocinas")),
                "points": float(product_data.get("points", 0) or 0),
                "module": str(product_data.get("module", "montada"))
            }
            
            if not clean_data["code"]:
                errors.append(f"Producto {idx}: código vacío")
                continue
            
            # Check for duplicates
            existing = await db.products.find_one({"code": clean_data["code"]})
            if existing:
                duplicates += 1
                continue
            
            # Handle zonePoints
            zone_points_data = product_data.get("zonePoints")
            if zone_points_data and isinstance(zone_points_data, dict):
                clean_data["zonePoints"] = {
                    f"Z{i}": float(zone_points_data.get(f"Z{i}", 0) or 0) for i in range(1, 13)
                }
                clean_data["points"] = clean_data["zonePoints"]["Z1"]
            
            # Create product with new ID
            clean_data["id"] = f"prod-{uuid.uuid4().hex[:8]}"
            
            # Insert into database (MongoDB adds _id)
            await db.products.insert_one(clean_data)
            
            # Remove _id before adding to response
            clean_data.pop("_id", None)
            created.append(clean_data)
            
        except Exception as e:
            logger.error(f"Error creating product {idx}: {e}")
            errors.append(f"Producto {idx} ({product_data.get('code', '?')}): {str(e)}")
    
    logger.info(f"Bulk create: {len(created)} created, {duplicates} duplicates, {len(errors)} errors")
    
    return {
        "created": len(created),
        "duplicates": duplicates,
        "errors": errors,
        "products": created
    }

@api_router.post("/products/bulk-upsert")
async def bulk_upsert_products(data: dict):
    """
    Crear productos nuevos o actualizar zonePoints de productos existentes.
    Para MV: actualiza la tarifa específica (T1, T2, ... T21) en zonePoints.
    Para ZC: actualiza la zona específica (Z1-Z12) en zonePoints.
    """
    products = data.get("products", [])
    tariff = data.get("tariff", "T1")  # T1-T21 para MV, Z1-Z12 para ZC
    library = data.get("library", "MV")
    
    created = 0
    updated = 0
    errors = []
    
    for idx, product_data in enumerate(products):
        try:
            code = str(product_data.get("code", "")).upper().strip()
            if not code:
                errors.append(f"Producto {idx}: código vacío")
                continue
            
            # Obtener el precio/puntos del producto
            points = float(product_data.get("points", 0) or 0)
            zone_points = product_data.get("zonePoints", {})
            
            # Si zonePoints tiene T1 o Z1, usar ese valor
            if library == "MV":
                points = float(zone_points.get("T1", points) or points)
            else:
                points = float(zone_points.get("Z1", points) or points)
            
            # Buscar si el producto ya existe (por código Y biblioteca)
            existing = await db.products.find_one({
                "code": code,
                "library": library
            })
            
            if existing:
                # ACTUALIZAR: merge del zonePoints con la nueva tarifa
                current_zones = existing.get("zonePoints", {}) or {}
                current_zones[tariff] = points
                
                await db.products.update_one(
                    {"code": code, "library": library},
                    {"$set": {
                        "zonePoints": current_zones,
                        "points": current_zones.get("T1", current_zones.get("Z1", points))
                    }}
                )
                updated += 1
                logger.info(f"Actualizado {code} con {tariff}={points}")
            else:
                # CREAR: nuevo producto con zonePoints inicial
                clean_data = {
                    "id": f"prod-{uuid.uuid4().hex[:8]}",
                    "code": code,
                    "name": str(product_data.get("name", "")),
                    "category": str(product_data.get("category", "")),
                    "series": str(product_data.get("series", "")),
                    "visualType": str(product_data.get("visualType", "")),
                    "width": float(product_data.get("width", 0) or 0),
                    "height": float(product_data.get("height", 0) or 0),
                    "depth": float(product_data.get("depth", 0) or 0),
                    "manufacturer": str(product_data.get("manufacturer", "MV" if library == "MV" else "Zona Cocinas")),
                    "module": str(product_data.get("module", "montada")),
                    "library": library,
                    "points": points,
                    "zonePoints": {tariff: points}
                }
                
                await db.products.insert_one(clean_data)
                created += 1
                logger.info(f"Creado {code} con {tariff}={points}")
                
        except Exception as e:
            logger.error(f"Error upserting product {idx}: {e}")
            errors.append(f"Producto {idx} ({product_data.get('code', '?')}): {str(e)}")
    
    logger.info(f"Bulk upsert: {created} created, {updated} updated, {len(errors)} errors")
    
    return {
        "created": created,
        "updated": updated,
        "errors": errors,
        "tariff": tariff
    }


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

@api_router.patch("/products/{product_id}/zone-points")
async def update_product_zone_points(product_id: str, zone_points: dict):
    """Actualizar solo los zonePoints de un producto"""
    existing = await db.products.find_one({"id": product_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    # Merge existing zonePoints with new ones
    current_zones = existing.get("zonePoints", {}) or {}
    updated_zones = {**current_zones, **zone_points}
    
    # Update points to match Z1
    points = updated_zones.get("Z1", existing.get("points", 0))
    
    await db.products.update_one(
        {"id": product_id}, 
        {"$set": {"zonePoints": updated_zones, "points": points}}
    )
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

# ============================================
# PROJECT/BUDGET ENDPOINTS
# ============================================

@api_router.get("/projects", response_model=List[ProjectModel])
async def get_projects(
    user_id: Optional[str] = None,
    client_code: Optional[str] = None,
    include_all: Optional[bool] = False
):
    """
    Obtener proyectos/presupuestos.
    - user_id: Filtrar por usuario
    - client_code: Filtrar por código de cliente (para ver solo presupuestos de ese cliente)
    - include_all: Si es True, devuelve todos (requiere permisos de admin/gerente)
    
    Por defecto, cada usuario solo ve sus propios presupuestos.
    Si tiene permisos especiales (isAdmin, isGerente, isDirectorComercial), puede ver todos.
    """
    query = {}
    
    # Filtrar por código de cliente si se especifica
    if client_code:
        query["clientCode"] = client_code
    
    # Filtrar por usuario si se especifica
    if user_id and not include_all:
        query["userId"] = user_id
    
    projects = await db.projects.find(query, {"_id": 0}).to_list(1000)
    return projects

@api_router.get("/projects/by-client/{client_code}")
async def get_projects_by_client(client_code: str):
    """
    Obtener todos los presupuestos de un cliente específico.
    Útil para ver el historial de presupuestos de un cliente.
    """
    projects = await db.projects.find(
        {"clientCode": client_code.upper()},
        {"_id": 0}
    ).sort("createdAt", -1).to_list(500)
    
    return {
        "clientCode": client_code.upper(),
        "totalProjects": len(projects),
        "projects": projects
    }

@api_router.get("/projects/summary-by-client")
async def get_projects_summary_by_client():
    """
    Obtener resumen de presupuestos agrupados por código de cliente.
    Para vista de administrador/gerente.
    """
    pipeline = [
        {
            "$group": {
                "_id": "$clientCode",
                "count": {"$sum": 1},
                "totalPvp": {"$sum": "$totalPvp"},
                "lastProject": {"$max": "$createdAt"},
                "projects": {"$push": {"id": "$id", "budgetNumber": "$budgetNumber", "status": "$status"}}
            }
        },
        {"$sort": {"lastProject": -1}}
    ]
    
    summary = await db.projects.aggregate(pipeline).to_list(500)
    
    return {
        "totalClients": len(summary),
        "clients": summary
    }

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


@api_router.get("/admin/metrics/trends")
async def get_admin_metrics_trends():
    """
    [DIRECTOR COMERCIAL ONLY] Métricas de tendencias mensuales.
    Devuelve datos agrupados por mes para gráficos de ventas y pipeline.
    """
    from datetime import timedelta
    from collections import defaultdict
    
    # Get all opportunities
    opportunities = await db.opportunities.find({}, {"_id": 0}).to_list(5000)
    
    # Agrupar por mes
    monthly_data = defaultdict(lambda: {
        "won": 0,
        "wonValue": 0,
        "lost": 0,
        "lostValue": 0,
        "created": 0,
        "createdValue": 0,
        "cocina": 0,
        "cocinaValue": 0,
        "armarios": 0,
        "armariosValue": 0
    })
    
    for opp in opportunities:
        # Extraer mes de creación
        created_at = opp.get("createdAt", "")
        if isinstance(created_at, str) and len(created_at) >= 7:
            month_key = created_at[:7]  # YYYY-MM
        else:
            continue
        
        value = opp.get("value", 0)
        stage = opp.get("stage", "")
        business_type = opp.get("businessType", "cocina")
        
        monthly_data[month_key]["created"] += 1
        monthly_data[month_key]["createdValue"] += value
        
        if stage == "won":
            monthly_data[month_key]["won"] += 1
            monthly_data[month_key]["wonValue"] += value
        elif stage == "lost":
            monthly_data[month_key]["lost"] += 1
            monthly_data[month_key]["lostValue"] += value
        
        # Por tipo de negocio
        if business_type == "cocina":
            monthly_data[month_key]["cocina"] += 1
            monthly_data[month_key]["cocinaValue"] += value
        elif business_type == "armarios":
            monthly_data[month_key]["armarios"] += 1
            monthly_data[month_key]["armariosValue"] += value
    
    # Convertir a lista ordenada
    trends = []
    for month, data in sorted(monthly_data.items()):
        trends.append({
            "month": month,
            "monthLabel": get_month_label(month),
            **data
        })
    
    # Tomar los últimos 12 meses
    trends = trends[-12:] if len(trends) > 12 else trends
    
    # Pipeline por etapa (embudo)
    stage_counts = defaultdict(lambda: {"count": 0, "value": 0})
    for opp in opportunities:
        stage = opp.get("stage", "lead")
        if stage not in ["won", "lost"]:
            stage_counts[stage]["count"] += 1
            stage_counts[stage]["value"] += opp.get("value", 0)
    
    funnel_data = [
        {"stage": "lead", "name": "Nuevo", "count": stage_counts["lead"]["count"], "value": stage_counts["lead"]["value"]},
        {"stage": "contacted", "name": "Contactado", "count": stage_counts["contacted"]["count"], "value": stage_counts["contacted"]["value"]},
        {"stage": "proposal", "name": "Propuesta", "count": stage_counts["proposal"]["count"], "value": stage_counts["proposal"]["value"]},
        {"stage": "negotiation", "name": "Negociación", "count": stage_counts["negotiation"]["count"], "value": stage_counts["negotiation"]["value"]}
    ]
    
    # Distribución por tipo de negocio
    business_type_data = {
        "cocina": {"count": 0, "value": 0, "won": 0, "wonValue": 0},
        "armarios": {"count": 0, "value": 0, "won": 0, "wonValue": 0}
    }
    for opp in opportunities:
        bt = opp.get("businessType", "cocina")
        if bt in business_type_data:
            business_type_data[bt]["count"] += 1
            business_type_data[bt]["value"] += opp.get("value", 0)
            if opp.get("stage") == "won":
                business_type_data[bt]["won"] += 1
                business_type_data[bt]["wonValue"] += opp.get("value", 0)
    
    return {
        "monthly": trends,
        "funnel": funnel_data,
        "byBusinessType": business_type_data
    }


def get_month_label(month_str: str) -> str:
    """Convierte YYYY-MM a etiqueta legible como 'Ene 25'"""
    months_es = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    try:
        year, month = month_str.split("-")
        return f"{months_es[int(month)-1]} {year[2:]}"
    except:
        return month_str


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

@api_router.get("/projects/check-budget-number/{budget_number}")
async def check_budget_number(budget_number: str):
    """Verificar si ya existe un presupuesto con este número"""
    project = await db.projects.find_one({"budgetNumber": budget_number}, {"_id": 0})
    if project:
        return {
            "exists": True,
            "projectId": project.get("id"),
            "customerName": project.get("customerName", "Sin nombre"),
            "createdAt": project.get("createdAt")
        }
    return {"exists": False}

@api_router.post("/projects", response_model=ProjectModel)
async def create_project(project: ProjectCreate, user_id: str, client_code: Optional[str] = None):
    """
    Crear un nuevo proyecto/presupuesto.
    El client_code se usa para agrupar presupuestos por cliente.
    """
    project_data = project.model_dump()
    project_data["id"] = f"proj-{uuid.uuid4().hex[:8]}"
    project_data["userId"] = user_id
    
    # Usar clientCode del proyecto o del parámetro
    if client_code and not project_data.get("clientCode"):
        project_data["clientCode"] = client_code.upper()
    elif project_data.get("clientCode"):
        project_data["clientCode"] = project_data["clientCode"].upper()
    
    project_data["createdAt"] = datetime.now(timezone.utc).isoformat()
    project_data["updatedAt"] = datetime.now(timezone.utc).isoformat()
    
    await db.projects.insert_one(project_data)
    
    # Tracking de actividad
    tracker = get_tracker()
    if tracker:
        user = await db.users.find_one({"id": user_id}, {"_id": 0, "username": 1})
        await tracker.track(
            user_id=user_id,
            username=user.get("username") if user else "unknown",
            activity_type=ActivityType.BUDGET_CREATE,
            details={"projectId": project_data["id"], "budgetNumber": project_data.get("budgetNumber")}
        )
    
    logger.info(f"Proyecto creado: {project_data['id']} para cliente: {project_data.get('clientCode', 'SIN CLIENTE')}")
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
    
    # Tracking de actividad
    tracker = get_tracker()
    if tracker and existing.get("userId"):
        user = await db.users.find_one({"id": existing["userId"]}, {"_id": 0, "username": 1})
        await tracker.track(
            user_id=existing["userId"],
            username=user.get("username") if user else "unknown",
            activity_type=ActivityType.BUDGET_UPDATE,
            details={"projectId": project_id}
        )
    
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
    
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# DESPIECE (BILL OF MATERIALS) API
# ============================================


def calculate_furniture_despiece(
    item: DespieceItemInput,
    carcass_material: str,
    back_material: str,
    grosor: float,
    back_thickness: float = 8,  # Grosor de trasera en mm
    door_tolerance_height: float = 2,  # Tolerancia alto puerta en mm
    door_tolerance_width: float = 3    # Tolerancia ancho puerta en mm
) -> FurnitureDespiece:
    """
    Calculate the despiece (bill of materials) for a single furniture piece.
    
    TODAS LAS MEDIDAS EN CENTÍMETROS (cm)
    
    REGLA FUNDAMENTAL:
    - VERTICALES (laterales/costados): Usan el ALTO COMPLETO del mueble
    - HORIZONTALES (tapas, estantes): Se les descuenta el GROSOR del casco (x2)
    
    Standard furniture components:
    - LATERAL IZQUIERDO: height x depth (ALTO COMPLETO)
    - LATERAL DERECHO: height x depth (ALTO COMPLETO)
    - TAPA SUPERIOR: (width - 2*grosor) x depth (entre laterales)
    - TAPA INFERIOR: (width - 2*grosor) x depth (entre laterales)
    - TRASERA: (width - 2*grosor) x (height - 0.6cm) (encajada en ranuras)
    - BALDA/ESTANTE: (width - 2*grosor) x (depth - 2cm) - optional shelves
    """
    
    # Todas las dimensiones en cm
    w = float(item.width)   # Ancho en cm
    h = float(item.height)  # Alto en cm  
    d = float(item.depth)   # Fondo en cm
    g = grosor / 10  # Grosor viene en mm, convertir a cm (18mm = 1.8cm)
    back_g = back_thickness / 10  # Grosor trasera en cm (8mm = 0.8cm)
    
    # =============================================
    # REGLAS DE CÁLCULO SEGÚN DOCUMENTO:
    # =============================================
    # 1. LATERALES (verticales): 
    #    - Largo = Alto exterior completo
    #    - Ancho = Fondo exterior - Grosor trasera
    # 
    # 2. HORIZONTALES (tapas, estantes):
    #    - Largo = Ancho exterior - (2 × Grosor lateral)
    #    - Ancho = Fondo exterior - Grosor trasera
    #
    # 3. TRASERA:
    #    - Largo = Ancho exterior - (2 × Grosor lateral) [encaja entre laterales]
    #    - Alto = Alto exterior - margen ranuras (0.6cm)
    #
    # 4. ESTANTES:
    #    - Largo = Ancho interior - margen soportes
    #    - Ancho = Fondo interior - margen frontal
    # =============================================
    
    # Medidas calculadas
    fondo_interior = d - back_g  # Fondo menos trasera para laterales y horizontales
    ancho_interior = w - (2 * g)  # Ancho menos los dos laterales
    
    components = []
    component_id = 0
    
    # Determine furniture type - Soportar nomenclaturas ZC y MV
    code_upper = item.productCode.upper()
    name_upper = item.productName.upper()
    category_upper = item.category.upper()
    
    # ALTOS - ZC: A, 9A | MV: A, ASCE, ASC, AR, ARI, ARU, ARC, AD, AV, AE, AM, AMF, ACA, ACC, ASF, AT, ATP, AA, AC, ACP, ACPJ
    #         MV también: L (ALTILLO), LV, S (SOBREENCIMERA), SV, SC, SVC, BOA, BOS
    alto_prefixes = ['ASCE', 'ASC', 'ARI', 'ARU', 'ARC', 'AD', 'AV', 'AE', 'AMF', 'AM', 'ACA', 'ACC', 'ASF', 'ATP', 'AT', 'AA', 'ACPJ', 'ACP', 'AC', 'AR', 'LD', 'LV', 'SVC', 'SV', 'SC', 'BOA', 'BOS']
    is_alto = (
        "ALTO" in name_upper or "ALTO" in category_upper or
        any(code_upper.startswith(p) for p in alto_prefixes) or
        code_upper.startswith('9A') or
        (code_upper.startswith('A') and len(code_upper) > 1 and code_upper[1].isdigit()) or
        (code_upper.startswith('L') and len(code_upper) > 1 and code_upper[1].isdigit()) or
        (code_upper.startswith('S') and len(code_upper) > 1 and code_upper[1].isdigit()) or
        "ALTILLO" in name_upper or "SOBREENCIMERA" in name_upper
    )
    
    # BAJOS - ZC: B, 9B | MV: B, BF, BRI, BRU, BR, BH, BHC, BHZ, BHG, BT, BTP, BPC, BC, BCG, BGC, BCGF, BGF
    bajo_prefixes = ['BRI', 'BRU', 'BR', 'BHZ', 'BHG', 'BHC', 'BH', 'BTP', 'BT', 'BPC', 'BCGF', 'BCG', 'BGF', 'BGC', 'BC', 'BF']
    is_bajo = (
        "BAJO" in name_upper or "BAJO" in category_upper or
        any(code_upper.startswith(p) for p in bajo_prefixes) or
        code_upper.startswith('9B') or
        (code_upper.startswith('B') and len(code_upper) > 1 and code_upper[1].isdigit()) or
        "FREGADERO" in name_upper or "HORNO" in name_upper
    )
    
    # COLUMNAS - ZC: C | MV: CD, CE, CF, CH, CHPC, CHGC, CHC, CHM, CHMG, CHMC, CHMCG, BOC
    #            MV también: M (MEDIA COLUMNA), MV, MPG, MVG, MPH, MPM, MGHM, MCHM
    columna_prefixes = ['CD', 'CE', 'CF', 'CHPC', 'CHGC', 'CHC', 'CHMCG', 'CHMG', 'CHMC', 'CHM', 'CH', 'BOC', 'MGHM', 'MCHM', 'MPG', 'MVG', 'MPH', 'MPM']
    is_columna = (
        "COLUMNA" in name_upper or "COLUMNA" in category_upper or
        "SEMICOLUMNA" in name_upper or "MEDIACOLUMNA" in name_upper or
        any(code_upper.startswith(p) for p in columna_prefixes) or
        (code_upper.startswith('C') and len(code_upper) > 1 and code_upper[1].isdigit()) or
        (code_upper.startswith('M') and len(code_upper) > 1 and code_upper[1].isdigit()) or
        (code_upper.startswith('MV') and len(code_upper) > 2 and code_upper[2].isdigit())
    )
    
    # Tipos especiales
    is_fregadero = "FREGADERO" in name_upper or "FREG" in code_upper
    is_horno = "HORNO" in name_upper or "BH" in code_upper[:2]
    is_rincon = "RINCON" in name_upper or "RINCÓN" in name_upper or code_upper.startswith('BR') or code_upper.startswith('AR')
    
    def add_component(name: str, short: str, material: str, length_cm: float, width_cm: float, thickness_cm: float = None, qty: int = 1, notes: str = ""):
        nonlocal component_id
        component_id += 1
        if thickness_cm is None:
            thickness_cm = g
        # Área en m² (cm² / 10000)
        area = (length_cm * width_cm * qty) / 10_000
        components.append(ComponentPiece(
            id=f"CMP-{item.productId[:8]}-{component_id:03d}",
            name=name,
            nameShort=short,
            material=material,
            length=round(length_cm, 1),  # cm
            width=round(width_cm, 1),    # cm
            thickness=round(thickness_cm * 10, 1),  # Mostrar grosor en mm
            quantity=qty,
            area=round(area, 4),
            notes=notes
        ))
    
    # =============================================
    # VERTICALES - LATERALES (costados)
    # Largo = ALTO COMPLETO del mueble
    # Ancho = FONDO - GROSOR TRASERA
    # =============================================
    
    # LATERAL IZQUIERDO (Side panel - full height)
    # Para muebles de rincón, el lateral tiene forma especial
    lateral_fondo = fondo_interior if not is_rincon else fondo_interior - 5  # Rincón: lateral más corto
    add_component(
        "Lateral izquierdo", "LAT-I",
        carcass_material,
        h, lateral_fondo, g, 1,  # ALTO COMPLETO x (FONDO - TRASERA)
        "1L canto" + (" (rincón)" if is_rincon else "")
    )
    
    # LATERAL DERECHO (Side panel - full height)
    add_component(
        "Lateral derecho", "LAT-D",
        carcass_material,
        h, lateral_fondo, g, 1,  # ALTO COMPLETO x (FONDO - TRASERA)
        "1L canto" + (" (rincón)" if is_rincon else "")
    )
    
    # =============================================
    # HORIZONTALES - TAPAS (superior e inferior)
    # Largo = ANCHO - (2 × GROSOR LATERAL) = ancho_interior
    # Ancho = FONDO - GROSOR TRASERA = fondo_interior
    # =============================================
    
    # TAPA SUPERIOR (Top panel - between sides)
    # Los fregaderos NO tienen tapa superior (hueco para la encimera)
    if not is_fregadero:
        add_component(
            "Tapa superior", "TAPA-S", 
            carcass_material,
            ancho_interior, fondo_interior, g, 1,
            "1L canto"
        )
    else:
        # Fregadero: travesaños frontales y traseros en lugar de tapa
        add_component(
            "Travesaño frontal", "TRAV-F",
            carcass_material,
            ancho_interior, 8, g, 1,  # 8cm de ancho
            "Travesaño para fregadero"
        )
        add_component(
            "Travesaño trasero", "TRAV-T",
            carcass_material,
            ancho_interior, 8, g, 1,
            "Travesaño para fregadero"
        )
    
    # TAPA INFERIOR (Bottom panel) - varía según tipo de mueble
    if is_alto:
        # ALTOS usan un travesaño inferior estrecho (8cm de ancho)
        add_component(
            "Travesaño inferior", "TRAV-I",
            carcass_material,
            ancho_interior, 8, g, 1,
            ""
        )
    elif is_horno:
        # Hornos: travesaños laterales para soporte del horno
        add_component(
            "Travesaño inferior horno", "TRAV-H",
            carcass_material,
            ancho_interior, 10, g, 1,
            "Soporte para horno empotrado"
        )
    else:
        # Bajos y columnas: tapa inferior completa
        add_component(
            "Tapa inferior", "TAPA-I",
            carcass_material,
            ancho_interior, fondo_interior, g, 1,
            "1L canto" if is_bajo else ""
        )
    
    # =============================================
    # TRASERA (Back panel)
    # Largo = ANCHO INTERIOR (entre laterales)
    # Alto = ALTO - margen ranuras (0.6cm total)
    # =============================================
    back_height = h - 0.6  # Encajada en ranuras (0.3cm arriba y abajo)
    add_component(
        "Trasera modulo", "TRAS",
        back_material,
        ancho_interior, back_height, back_g, 1,
        f"Tablero {int(back_thickness)}mm"
    )
    
    # =============================================
    # BALDAS / ESTANTES (Shelves)
    # Largo = ANCHO INTERIOR - margen soportes (0.5cm)
    # Ancho = FONDO INTERIOR - margen frontal (2cm retranqueo)
    # =============================================
    shelf_count = 0
    
    # Columnas: más estantes debido a su altura
    if is_columna:
        if h >= 200:  # Columna completa
            shelf_count = 5
        elif h >= 140:  # Media columna
            shelf_count = 3
        else:
            shelf_count = 2
    # Altos: normalmente 1-2 estantes
    elif is_alto:
        if h >= 90:
            shelf_count = 2
        elif h >= 60:
            shelf_count = 1
        else:
            shelf_count = 0
    # Bajos: normalmente 1 estante
    elif is_bajo:
        if is_fregadero or is_horno:
            shelf_count = 0  # Fregaderos y hornos sin estantes
        elif h >= 70:
            shelf_count = 2
        else:
            shelf_count = 1
    # Genérico: basado en altura
    elif h >= 70:
        shelf_count = 2 if h < 120 else 3 if h < 180 else 4
    elif h >= 35:
        shelf_count = 1
    
    if shelf_count > 0:
        shelf_length = ancho_interior - 0.5  # Entre laterales menos margen soportes
        shelf_width = fondo_interior - 2  # Retranqueado 2cm del frontal
        add_component(
            "Balda interior", "BALDA",
            carcass_material,
            shelf_length, shelf_width, g, shelf_count,
            "Regulable con soportes"
        )
    
    # =============================================
    # PUERTAS - Calcular dimensiones de puertas
    # =============================================
    # Detectar si el mueble tiene puertas según su nombre/categoría/código
    
    # Detectar cantidad de puertas
    has_doors = False
    num_doors = 0
    
    # Patrones para detectar puertas:
    # ZC: 1P, 2P, 3P, 4P (ej: 9A1P300, 9B2P600)
    # MV: Similar pero también D/I (derecha/izquierda)
    
    # 4P = 4 puertas (columnas grandes)
    if "4P" in name_upper or "4P" in code_upper:
        has_doors = True
        num_doors = 4
    # 3P = 3 puertas
    elif "3P" in name_upper or "3P" in code_upper:
        has_doors = True
        num_doors = 3
    # 2P = 2 puertas
    elif "2P" in name_upper or "2P" in code_upper:
        has_doors = True
        num_doors = 2
    # 1P = 1 puerta
    elif "1P" in name_upper or "1P" in code_upper:
        has_doors = True
        num_doors = 1
    # D/I = 1 puerta (derecha/izquierda)
    elif "/I" in name_upper or "/D" in name_upper or "D/I" in name_upper:
        has_doors = True
        num_doors = 1
    elif "PUERTA" in name_upper or "PTA" in code_upper:
        has_doors = True
        num_doors = 1
    # Muebles especiales SIN puertas
    elif is_fregadero or "MICROONDAS" in name_upper or "ESTANTERIA" in name_upper or "HUECO" in name_upper:
        has_doors = False
        num_doors = 0
    # Muebles que normalmente tienen puertas pero no lo especifican
    elif is_alto or is_bajo or is_columna:
        has_doors = True
        # Estimar número de puertas según el ancho
        if w <= 45:
            num_doors = 1
        elif w <= 90:
            num_doors = 2
        elif w <= 120:
            num_doors = 3
        else:
            num_doors = 4
    
    # Calcular dimensiones de puerta si tiene puertas
    if has_doors and num_doors > 0:
        # =============================================
        # PUERTAS - Según documento:
        # Alto puerta = Alto mueble - toleranciaAlto (configurable, por defecto 2mm)
        # Ancho puerta (1P) = Ancho mueble - toleranciaAncho (configurable, por defecto 3mm)
        # Ancho puerta (2P) = (Ancho mueble - toleranciaAncho entre puertas) / 2
        # =============================================
        door_height_tolerance = door_tolerance_height / 10  # Convertir mm a cm
        door_width_tolerance = door_tolerance_width / 10    # Convertir mm a cm
        door_gap_between = door_width_tolerance             # Separación entre puertas = tolerancia ancho
        door_edge_tolerance = door_width_tolerance / 2      # Tolerancia lateral = tolerancia/2
        
        # Alto de puerta: altura del mueble - tolerancia
        door_height = h - door_height_tolerance
        
        # Ancho de puerta según número de puertas
        if num_doors == 1:
            # Puerta única = ancho total - tolerancia
            door_width = w - door_width_tolerance
        elif num_doors == 2:
            # Dos puertas = (ancho - separación entre puertas) / 2
            door_width = (w - door_gap_between) / 2
        elif num_doors == 3:
            # Tres puertas
            door_width = (w - (2 * door_gap_between)) / 3
        else:  # 4 o más puertas
            door_width = (w - ((num_doors - 1) * door_gap_between)) / num_doors
        
        # Grosor típico de puerta: 19mm (1.9cm)
        door_thickness_cm = 1.9
        door_thickness_cm = 1.9
        
        # Agregar puerta(s) al despiece
        add_component(
            f"Puerta {'(' + str(num_doors) + ' uds)' if num_doors > 1 else ''}",
            "PUERTA",
            "PUERTA COLOR",  # Material especial para puertas (se reemplaza con acabado)
            round(door_height, 1), round(door_width, 1), door_thickness_cm, num_doors,
            f"Puerta acabado a elegir. {num_doors} puerta{'s' if num_doors > 1 else ''}"
        )
    
    # =============================================
    # HERRAJES - Según tipo de mueble
    # =============================================
    
    # COLGADORES - Solo para muebles ALTOS (1 juego = 2 colgadores)
    if is_alto:
        add_component(
            "Juego de colgadores",
            "COLG",
            "HERRAJE",
            0, 0, 0, 1,
            "1 juego = 2 colgadores para mueble alto de pared"
        )
    
    # BISAGRAS - Según número de puertas y altura del MUEBLE
    if has_doors and num_doors > 0:
        # Regla: 
        # - Muebles de hasta 90cm de alto (altos normales): 2 bisagras por puerta
        # - Muebles de más de 90cm de alto (semicolumnas, columnas, despenseros): 3 bisagras por puerta
        bisagras_por_puerta = 2 if h <= 90 else 3
        total_bisagras = bisagras_por_puerta * num_doors
        add_component(
            f"Bisagras",
            "BISAG",
            "HERRAJE",
            0, 0, 0, total_bisagras,
            f"{bisagras_por_puerta} bisagras por puerta (mueble {h}cm alto)"
        )
        
        # TIRADORES - 1 por puerta
        add_component(
            "Tiradores",
            "TIRAD",
            "HERRAJE",
            0, 0, 0, num_doors,
            "1 tirador por puerta"
        )
    
    # SOPORTES DE BALDA - 4 por balda
    if shelf_count > 0:
        add_component(
            "Soportes de balda",
            "SOPORT",
            "HERRAJE",
            0, 0, 0, shelf_count * 4,
            "4 soportes por balda"
        )
    
    # PATAS/ZÓCALO - Solo para BAJOS y COLUMNAS
    if is_bajo or is_columna:
        # 4 patas para muebles estándar, 6 para anchos > 80cm
        num_patas = 6 if w > 80 else 4
        add_component(
            "Patas regulables",
            "PATAS",
            "HERRAJE",
            0, 0, 0, num_patas,
            f"{num_patas} patas de 10-15cm regulables"
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
                request.grosor,
                request.backThickness,
                request.doorToleranceHeight,
                request.doorToleranceWidth
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
# DATABASE EXPORT API (Admin Only)
# ============================================

from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter
import io

@api_router.get("/admin/export-database")
async def export_database(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Exportar toda la base de datos a Excel.
    Solo accesible para Director Comercial (admin).
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="Token requerido")
    
    try:
        # Verify admin role
        payload = verify_access_token(credentials.credentials)
        user_id = payload.get("sub")
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        
        if not user or user.get('role') != 'director_comercial':
            raise HTTPException(status_code=403, detail="Solo el Director Comercial puede exportar la base de datos")
        
        # Create workbook
        wb = Workbook()
        
        # Styles
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
        
        # ===== USUARIOS =====
        ws_users = wb.active
        ws_users.title = "Usuarios"
        
        users = await db.users.find({}, {'_id': 0, 'password': 0}).to_list(1000)
        user_headers = ['ID', 'Usuario', 'Nombre', 'Rol', 'Email', 'Teléfono', 'Delegación', 'Activo']
        for col, header in enumerate(user_headers, 1):
            cell = ws_users.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
        
        for row_num, u in enumerate(users, 2):
            ws_users.cell(row=row_num, column=1, value=u.get('id', ''))
            ws_users.cell(row=row_num, column=2, value=u.get('username', ''))
            ws_users.cell(row=row_num, column=3, value=u.get('fullName', ''))
            ws_users.cell(row=row_num, column=4, value=u.get('role', ''))
            ws_users.cell(row=row_num, column=5, value=u.get('email', ''))
            ws_users.cell(row=row_num, column=6, value=u.get('phone', ''))
            ws_users.cell(row=row_num, column=7, value=u.get('delegation', ''))
            ws_users.cell(row=row_num, column=8, value='Sí' if u.get('isActive', True) else 'No')
        
        # ===== PRODUCTOS MONTADA =====
        ws_products = wb.create_sheet("Productos Montada")
        
        products = await db.products.find({}, {'_id': 0}).to_list(10000)
        prod_headers = ['Código', 'Nombre', 'Programa', 'Categoría', 'Serie', 'Ancho', 'Alto', 'Fondo', 'Puntos', 'Z1', 'Z2', 'Z3', 'Z4']
        for col, header in enumerate(prod_headers, 1):
            cell = ws_products.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
        
        for row_num, p in enumerate(products, 2):
            zp = p.get('zonePoints', {}) or {}
            ws_products.cell(row=row_num, column=1, value=p.get('code', ''))
            ws_products.cell(row=row_num, column=2, value=p.get('name', ''))
            ws_products.cell(row=row_num, column=3, value=p.get('programa', ''))
            ws_products.cell(row=row_num, column=4, value=p.get('category', ''))
            ws_products.cell(row=row_num, column=5, value=p.get('series', ''))
            ws_products.cell(row=row_num, column=6, value=p.get('width', 0))
            ws_products.cell(row=row_num, column=7, value=p.get('height', 0))
            ws_products.cell(row=row_num, column=8, value=p.get('depth', 0))
            ws_products.cell(row=row_num, column=9, value=p.get('points', 0))
            ws_products.cell(row=row_num, column=10, value=zp.get('Z1', 0))
            ws_products.cell(row=row_num, column=11, value=zp.get('Z2', 0))
            ws_products.cell(row=row_num, column=12, value=zp.get('Z3', 0))
            ws_products.cell(row=row_num, column=13, value=zp.get('Z4', 0))
        
        # ===== PRODUCTOS DESPIECE (Tableros) =====
        ws_despiece = wb.create_sheet("Productos Despiece")
        
        despiece_products = await db.despiece_products.find({}, {'_id': 0}).to_list(10000)
        desp_headers = ['Código', 'Nombre', 'Fabricante', 'Colección', 'Color', 'Acabado', 'Grosor', 'Categoría', 'Precio Z1', 'Precio Z2', 'Precio Z3']
        for col, header in enumerate(desp_headers, 1):
            cell = ws_despiece.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
        
        for row_num, p in enumerate(despiece_products, 2):
            ws_despiece.cell(row=row_num, column=1, value=p.get('code', ''))
            ws_despiece.cell(row=row_num, column=2, value=p.get('name', ''))
            ws_despiece.cell(row=row_num, column=3, value=p.get('manufacturer', ''))
            ws_despiece.cell(row=row_num, column=4, value=p.get('collection', ''))
            ws_despiece.cell(row=row_num, column=5, value=p.get('color', ''))
            ws_despiece.cell(row=row_num, column=6, value=p.get('finish', ''))
            ws_despiece.cell(row=row_num, column=7, value=p.get('thickness', 0))
            ws_despiece.cell(row=row_num, column=8, value=p.get('category', ''))
            ws_despiece.cell(row=row_num, column=9, value=p.get('priceZ1', 0))
            ws_despiece.cell(row=row_num, column=10, value=p.get('priceZ2', 0))
            ws_despiece.cell(row=row_num, column=11, value=p.get('priceZ3', 0))
        
        # ===== PROYECTOS =====
        ws_projects = wb.create_sheet("Proyectos")
        
        projects = await db.projects.find({}, {'_id': 0, 'itemsMontada': 0, 'itemsDespiece': 0}).to_list(1000)
        proj_headers = ['Nº Expediente', 'Cliente', 'Dirección', 'Total PVP', 'Estado', 'Comercial']
        for col, header in enumerate(proj_headers, 1):
            cell = ws_projects.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
        
        for row_num, p in enumerate(projects, 2):
            ws_projects.cell(row=row_num, column=1, value=p.get('budgetNumber', ''))
            ws_projects.cell(row=row_num, column=2, value=p.get('customerName', ''))
            ws_projects.cell(row=row_num, column=3, value=p.get('customerAddress', ''))
            ws_projects.cell(row=row_num, column=4, value=p.get('totalPvp', 0))
            ws_projects.cell(row=row_num, column=5, value=p.get('status', 'activo'))
            ws_projects.cell(row=row_num, column=6, value=p.get('savedBy', ''))
        
        # Adjust column widths
        for ws in wb.worksheets:
            for col in range(1, ws.max_column + 1):
                ws.column_dimensions[get_column_letter(col)].width = 18
        
        # Save to bytes
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        
        # Log audit
        await log_audit("database_export", user_id, "admin", True, {"tables": ["users", "products_montada", "products_despiece", "projects"]})
        
        filename = f"LUIGGI_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database export error: {e}")
        raise HTTPException(status_code=500, detail=f"Error exportando base de datos: {str(e)}")

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


# Include the router in the main app (AFTER all endpoints are defined)
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', 'http://localhost:3000').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# STARTUP / SHUTDOWN EVENTS
# ============================================

@app.on_event("startup")
async def startup_event():
    """Configure scheduled backups and database indexes on startup"""
    # =============================================
    # ÍNDICES DE BASE DE DATOS - Fortalecer integridad
    # =============================================
    try:
        # Índice único para expedientes
        await db.digitalizador_history.create_index("expNumber", unique=True, sparse=True)
        logger.info("Índice único creado para expNumber en digitalizador_history")
        
        # Índices para usuarios
        await db.users.create_index("username", unique=True)
        await db.users.create_index("email", sparse=True)
        await db.users.create_index("factoryId", sparse=True)
        logger.info("Índices de usuarios creados")
        
        # Índices para pedidos (fabrica_orders)
        await db.fabrica_orders.create_index("id", unique=True)
        await db.fabrica_orders.create_index("budgetNumber")
        await db.fabrica_orders.create_index("status")
        await db.fabrica_orders.create_index("factoryId", sparse=True)
        await db.fabrica_orders.create_index("createdAt")
        await db.fabrica_orders.create_index([("status", 1), ("factoryId", 1)])  # Índice compuesto
        logger.info("Índices de fabrica_orders creados")
        
        # Índices para presupuestos
        await db.budgets.create_index("id", unique=True)
        await db.budgets.create_index("createdAt")
        await db.budgets.create_index("userId", sparse=True)
        logger.info("Índices de budgets creados")
        
        # Índices para clientes
        await db.clients.create_index("id", unique=True)
        await db.clients.create_index("name")
        await db.clients.create_index("email", sparse=True)
        logger.info("Índices de clients creados")
        
        # Índices para catálogos y productos
        await db.catalogs.create_index("id", unique=True)
        await db.catalogs.create_index("libraryId")
        logger.info("Índices de catalogs creados")
        
        # Índices para fábricas
        await db.factories.create_index("id", unique=True)
        await db.factories.create_index("code", unique=True)
        logger.info("Índices de factories creados")
        
        # Índices para historial de cambios (order_history)
        await db.order_history.create_index("orderId")
        await db.order_history.create_index("timestamp")
        await db.order_history.create_index([("orderId", 1), ("timestamp", -1)])  # Para consultas de timeline
        logger.info("Índices de order_history creados")
        
        logger.info("✅ Todos los índices de base de datos configurados correctamente")
        
    except Exception as e:
        logger.warning(f"Error creando índices (algunos pueden ya existir): {e}")
    
    # =============================================
    # CREAR/ACTUALIZAR USUARIO MASTER
    # =============================================
    try:
        hashed_password = bcrypt.hashpw("Mario2025*".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        master_user = {
            "id": "user-master-mario",
            "username": "MARIO",
            "password": hashed_password,
            "email": "mario@luiggihome.es",
            "clientName": "ADMINISTRADOR MASTER",
            "phone": "",
            "province": "",
            "isAdmin": True,
            "isGerente": True,
            "isDirectorComercial": True,
            "isDirectorFabrica": True,
            "isResponsableDelegacion": True,
            "isComercial": False,
            "isTienda": False,
            "isPrescriptor": False,
            "canManageArticles": True,
            "canViewMetrics": True,
            "canExportData": True,
            "canManageUsers": True,
            "canManageClients": True,
            "canManageProducts": True,
            "canManageSettings": True,
            "canViewAllOrders": True,
            "canEditAllOrders": True,
            "canDeleteOrders": True,
            "canAccessTelemetry": True,
            "canAccessBackups": True,
            "canAccessMaintenance": True,
            "canAccessArmarios": True,
            "allowedModules": ["montada", "despiece", "armarios"],
            "active": True,
            "isActive": True,
            "createdAt": datetime.now(timezone.utc),
            "updatedAt": datetime.now(timezone.utc)
        }
        
        # Usar upsert para crear o actualizar
        await db.users.update_one(
            {"username": "MARIO"},
            {"$set": master_user},
            upsert=True
        )
        logger.info("✅ Usuario MASTER (MARIO) configurado - Contraseña: Mario2025*")
    except Exception as e:
        logger.warning(f"Error configurando usuario master: {e}")
    
    # =============================================
    # INICIALIZAR SERVICIOS DE BACKUP Y TRACKING
    # =============================================
    try:
        # Inicializar servicio de backup con programador diario (3:00 AM)
        backup_svc = init_backup_service(mongo_url, os.environ['DB_NAME'])
        await backup_svc.start_scheduler(hour=3)
        logger.info("✅ Servicio de backup diario iniciado (3:00 AM)")
        
        # Inicializar tracker de actividad
        tracker = init_activity_tracker(db)
        await tracker.setup_indexes()
        logger.info("✅ Tracker de actividad de usuarios iniciado")
        
    except Exception as e:
        logger.warning(f"Error inicializando servicios de backup/tracking: {e}")
    
    # Start backup scheduler from backup module
    start_backup_scheduler()

@app.on_event("shutdown")
async def shutdown_db_client():
    backup_scheduler.shutdown()
    client.close()
