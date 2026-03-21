from fastapi import FastAPI, APIRouter, File, UploadFile, Form, HTTPException, BackgroundTasks, Request, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
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
    crm_module_router
)
from routes.fabrica import router as fabrica_router
from routes.backup import scheduler as backup_scheduler, start_backup_scheduler

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
# Nota: auth, products, clients, projects están duplicados en server.py
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
    """Verify a password against its hash"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except:
        # If hash is invalid (plain text password from old data), compare directly
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


@api_router.post("/analyze-product-sheets")
async def analyze_product_sheets(
    module: str = Form(...),
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
        
        products = []
        detected_categories = set()
        
        for file in files:
            # Read file content
            content = await file.read()
            base64_image = base64.b64encode(content).decode('utf-8')
            
            # Create Gemini chat with vision
            chat = LlmChat(
                api_key=api_key,
                session_id=f"product-analysis-{uuid.uuid4()}",
                system_message="""Eres un experto en digitalización de tarifas técnicas de muebles de cocina ZONA COCINAS.
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
            ).with_model("gemini", "gemini-2.0-flash")
            
            # Create message with image
            user_message = UserMessage(
                text="""Analiza esta página de tarifa técnica de ZONA COCINAS.

INSTRUCCIONES:
1. Lee el ENCABEZADO de la página para identificar: ALTOS, BAJOS, SEMICOLUMNAS, COLUMNAS, PUERTAS, ACCESORIOS, etc.
2. Identifica la SERIE (ej: "ALTOS 35 FONDO 58", "BAJOS 70", "COLUMNAS 200")
3. Extrae TODOS los códigos de productos de la tabla (35A1P58350, 7B1P300, etc.)
4. Para cada producto, lee los 12 precios por zona (Z1 a Z12)
5. Decodifica las dimensiones del código

Responde ÚNICAMENTE con el JSON estructurado. No añadas explicaciones.""",
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
            "detectedCategories": list(detected_categories)
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
@limiter.limit(get_limit("user_create"))
async def create_user(request: Request, user: UserCreate):
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
    
    # Auditoría
    audit.log(
        AuditAction.USER_CREATE,
        resource_type="user",
        resource_id=user_data["id"],
        request=request,
        details={"username": user_data["username"]}
    )
    
    return user_to_response(user_data)

@api_router.put("/users/{user_id}", response_model=UserResponse)
@limiter.limit(get_limit("write"))
async def update_user(request: Request, user_id: str, user: UserUpdate):
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
        # Auditoría para cambio de contraseña
        audit.log(
            AuditAction.PASSWORD_CHANGE,
            resource_type="user",
            resource_id=user_id,
            request=request
        )
    
    if update_data:
        await db.users.update_one({"id": user_id}, {"$set": update_data})
    
    # Auditoría para actualización general
    audit.log(
        AuditAction.USER_UPDATE,
        resource_type="user",
        resource_id=user_id,
        request=request,
        details={"fields_updated": list(update_data.keys())}
    )
    
    updated = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
    return updated

@api_router.delete("/users/{user_id}")
@limiter.limit(get_limit("user_delete"))
async def delete_user(request: Request, user_id: str):
    """Eliminar un usuario"""
    if user_id == "admin":
        raise HTTPException(status_code=400, detail="No se puede eliminar el administrador principal")
    
    # Obtener info del usuario antes de eliminar para auditoría
    user_to_delete = await db.users.find_one({"id": user_id}, {"_id": 0, "username": 1})
    
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Auditoría
    audit.log(
        AuditAction.USER_DELETE,
        resource_type="user",
        resource_id=user_id,
        request=request,
        details={"deleted_username": user_to_delete.get("username") if user_to_delete else "unknown"}
    )
    
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
    username = credentials.get("username", "").upper().strip()
    password = credentials.get("password", "").strip()
    
    user = await db.users.find_one({"username": username}, {"_id": 0})
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
    
    # Crear tokens JWT
    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user.get("id"))
    
    # Auditoría: login exitoso
    audit.log_login_success(user.get("id"), username, request)
    
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

@api_router.get("/materials", response_model=List[MaterialModel])
async def get_materials(library: str = None):
    """Obtener todos los materiales, opcionalmente filtrados por biblioteca"""
    query = {}
    if library:
        query["library"] = library.upper()
    materials = await db.materials.find(query, {"_id": 0}).to_list(1000)
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
# ORDER CONFIRMATION SYSTEM
# ============================================

@api_router.post("/orders/confirm")
async def confirm_order(
    budgetNumber: str = Form(...),
    customerName: str = Form(...),
    customerAddress: str = Form(""),
    totalAmount: str = Form(...),
    email: str = Form(...),
    notes: str = Form(""),
    items: str = Form("[]"),
    doorColorLow: str = Form(""),
    doorColorHigh: str = Form(""),
    doorColorColumns: str = Form(""),
    sideColor: str = Form(""),
    carcassColor: str = Form(""),
    globalFinish: str = Form(""),
    distributorName: str = Form(""),
    userId: str = Form(""),
    projectReference: str = Form(""),
    attachment_0: Optional[UploadFile] = File(None),
    attachment_1: Optional[UploadFile] = File(None),
    attachment_2: Optional[UploadFile] = File(None),
    attachment_3: Optional[UploadFile] = File(None),
    attachment_4: Optional[UploadFile] = File(None),
):
    """
    Confirma un pedido y envía un email con los detalles y archivos adjuntos.
    """
    try:
        sendgrid_key = os.environ.get('SENDGRID_API_KEY')
        if not sendgrid_key:
            raise HTTPException(status_code=500, detail="SENDGRID_API_KEY no configurada. Configure el API key en Panel Maestro > Configuración.")
        
        # Parse items
        try:
            items_list = json.loads(items)
        except:
            items_list = []
        
        # Build items table HTML
        items_html = ""
        for item in items_list:
            items_html += f"""
            <tr>
                <td style="padding: 12px 8px; border-bottom: 1px solid #fed7aa; font-weight: bold; color: #ea580c;">{item.get('code', '-')}</td>
                <td style="padding: 12px 8px; border-bottom: 1px solid #fed7aa; color: #1e293b;">{item.get('name', '-')}</td>
                <td style="padding: 12px 8px; border-bottom: 1px solid #fed7aa; text-align: center; font-weight: bold;">{item.get('quantity', 1)}</td>
                <td style="padding: 12px 8px; border-bottom: 1px solid #fed7aa; text-align: right; font-weight: bold; color: #1e293b;">{item.get('price', 0):.2f} €</td>
            </tr>
            """
        
        # Build specifications HTML
        specs_html = ""
        specs = []
        if globalFinish:
            specs.append(f"<strong>Acabado Global:</strong> {globalFinish}")
        if carcassColor:
            specs.append(f"<strong>Armazón:</strong> {carcassColor}")
        if doorColorLow:
            specs.append(f"<strong>Puertas Bajos:</strong> {doorColorLow}")
        if doorColorHigh:
            specs.append(f"<strong>Puertas Altos:</strong> {doorColorHigh}")
        if doorColorColumns:
            specs.append(f"<strong>Puertas Columnas:</strong> {doorColorColumns}")
        if sideColor:
            specs.append(f"<strong>Costados/Vistos:</strong> {sideColor}")
        
        if specs:
            specs_html = f"""
            <div style="background: #fff7ed; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ea580c;">
                <h3 style="color: #ea580c; margin: 0 0 15px 0; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">Especificaciones de Acabados</h3>
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; font-size: 13px; color: #64748b;">
                    {''.join([f'<div>{s}</div>' for s in specs])}
                </div>
            </div>
            """
        
        # Current date
        from datetime import datetime
        fecha_actual = datetime.now().strftime("%d/%m/%Y")
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 0; background: #f1f5f9;">
            <!-- Header con Logo -->
            <div style="background: linear-gradient(135deg, #1e293b 0%, #334155 100%); padding: 30px 40px; border-radius: 12px 12px 0 0;">
                <table style="width: 100%;">
                    <tr>
                        <td>
                            <h1 style="margin: 0; color: #ea580c; font-size: 28px; font-weight: 800; font-style: italic;">LUIGGI HOME</h1>
                            {f'<p style="margin: 5px 0 0; color: #94a3b8; font-size: 12px; text-transform: uppercase; letter-spacing: 1px;">{distributorName}</p>' if distributorName else ''}
                        </td>
                        <td style="text-align: right;">
                            <div style="background: #ea580c; color: white; padding: 15px 25px; border-radius: 8px; display: inline-block;">
                                <p style="margin: 0; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; opacity: 0.9;">Confirmación de Pedido</p>
                                <p style="margin: 5px 0 0; font-size: 20px; font-weight: 800;">#{budgetNumber}</p>
                            </div>
                        </td>
                    </tr>
                </table>
            </div>
            
            <!-- Contenido Principal -->
            <div style="background: white; padding: 40px; border: 1px solid #e2e8f0; border-top: none;">
                
                <!-- Datos del Cliente -->
                <div style="background: #f8fafc; padding: 25px; border-radius: 8px; margin-bottom: 30px;">
                    <table style="width: 100%;">
                        <tr>
                            <td style="width: 60%;">
                                <p style="margin: 0 0 5px; color: #64748b; font-size: 11px; text-transform: uppercase; letter-spacing: 1px;">Cliente</p>
                                <p style="margin: 0; color: #1e293b; font-size: 18px; font-weight: 700;">{customerName}</p>
                                {f'<p style="margin: 8px 0 0; color: #64748b; font-size: 13px;">{customerAddress}</p>' if customerAddress else ''}
                            </td>
                            <td style="width: 40%; text-align: right;">
                                <p style="margin: 0 0 5px; color: #64748b; font-size: 11px; text-transform: uppercase; letter-spacing: 1px;">Fecha</p>
                                <p style="margin: 0; color: #1e293b; font-size: 14px; font-weight: 600;">{fecha_actual}</p>
                            </td>
                        </tr>
                    </table>
                </div>
                
                <!-- Tabla de Artículos -->
                <h2 style="color: #1e293b; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; margin: 0 0 15px; padding-bottom: 10px; border-bottom: 2px solid #ea580c;">
                    Artículos del Pedido
                </h2>
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 25px;">
                    <thead>
                        <tr style="background: #1e293b;">
                            <th style="padding: 12px 8px; text-align: left; color: white; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;">Ref.</th>
                            <th style="padding: 12px 8px; text-align: left; color: white; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;">Descripción</th>
                            <th style="padding: 12px 8px; text-align: center; color: white; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;">Ud.</th>
                            <th style="padding: 12px 8px; text-align: right; color: white; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;">Importe</th>
                        </tr>
                    </thead>
                    <tbody style="background: #fffbeb;">
                        {items_html}
                    </tbody>
                </table>
                
                <!-- Total -->
                <div style="background: linear-gradient(135deg, #ea580c 0%, #dc2626 100%); padding: 20px 25px; border-radius: 8px; margin-bottom: 25px;">
                    <table style="width: 100%;">
                        <tr>
                            <td style="color: white; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">Total Pedido</td>
                            <td style="text-align: right; color: white; font-size: 28px; font-weight: 800;">{float(totalAmount):,.2f} €</td>
                        </tr>
                    </table>
                </div>
                
                <!-- Especificaciones de Acabados -->
                {specs_html}
                
                <!-- Notas -->
                {f'''
                <div style="background: #f8fafc; padding: 20px; border-radius: 8px; margin-top: 20px; border: 1px solid #e2e8f0;">
                    <h3 style="color: #64748b; margin: 0 0 10px; font-size: 12px; text-transform: uppercase; letter-spacing: 1px;">Observaciones</h3>
                    <p style="margin: 0; color: #1e293b; font-size: 14px; line-height: 1.6;">{notes}</p>
                </div>
                ''' if notes else ''}
                
            </div>
            
            <!-- Footer -->
            <div style="background: #1e293b; color: white; padding: 25px 40px; border-radius: 0 0 12px 12px; text-align: center;">
                <p style="margin: 0; color: #94a3b8; font-size: 12px;">
                    Este pedido ha sido confirmado a través de <strong style="color: #ea580c;">LUIGGI HOME</strong> - Sistema de Gestión de Cocinas
                </p>
                <p style="margin: 10px 0 0; color: #64748b; font-size: 11px;">
                    © {datetime.now().year} LUIGGI HOME. Todos los derechos reservados.
                </p>
            </div>
        </body>
        </html>
        """
        
        # Create email
        from_email = os.environ.get('BACKUP_EMAIL', 'marioluiggihome@gmail.com')
        message = Mail(
            from_email=from_email,
            to_emails=email,
            subject=f'✅ Confirmación Pedido #{budgetNumber} - {customerName}',
            html_content=html_content
        )
        
        # Add attachments
        attachments = [attachment_0, attachment_1, attachment_2, attachment_3, attachment_4]
        for attachment in attachments:
            if attachment and attachment.filename:
                file_content = await attachment.read()
                encoded_content = base64.b64encode(file_content).decode()
                
                attached_file = Attachment(
                    FileContent(encoded_content),
                    FileName(attachment.filename),
                    FileType(attachment.content_type or 'application/octet-stream'),
                    Disposition('attachment')
                )
                message.add_attachment(attached_file)
        
        # =============================================
        # ENVÍO DE EMAIL - Con fallback a Resend
        # =============================================
        email_sent = False
        email_provider = None
        
        # Intentar con SendGrid primero
        try:
            sg = SendGridAPIClient(sendgrid_key)
            response = sg.send(message)
            email_sent = True
            email_provider = "SendGrid"
            logger.info(f"Email sent successfully via SendGrid to {email}")
        except Exception as sendgrid_error:
            error_str = str(sendgrid_error)
            logger.warning(f"SendGrid failed: {error_str[:200]}")
            
            # Intentar con Resend como fallback
            resend_key = os.environ.get('RESEND_API_KEY')
            if resend_key:
                try:
                    resend.api_key = resend_key
                    # Usar remitente por defecto de Resend (no requiere verificación)
                    resend_params = {
                        "from": "LUIGGI HOME <onboarding@resend.dev>",
                        "to": [email],
                        "subject": f"✅ Confirmación Pedido #{budgetNumber} - {customerName}",
                        "html": html_content
                    }
                    resend_response = resend.Emails.send(resend_params)
                    email_sent = True
                    email_provider = "Resend"
                    logger.info(f"Email sent successfully via Resend to {email}")
                except Exception as resend_error:
                    logger.warning(f"Resend also failed: {resend_error}. Order will be saved without email.")
            else:
                logger.warning(f"No RESEND_API_KEY configured for fallback. Order saved without email.")
        
        # Log the order confirmation (save it regardless of email status)
        order_record = {
            "id": f"order-{uuid.uuid4().hex[:8]}",
            "budgetNumber": budgetNumber,
            "projectReference": projectReference,
            "customerName": customerName,
            "customerAddress": customerAddress,
            "totalAmount": float(totalAmount),
            "email": email,
            "notes": notes,
            "items": items_list,  # Guardar los items completos
            "itemsCount": len(items_list),
            "attachmentsCount": sum(1 for a in attachments if a and a.filename),
            "confirmedAt": datetime.now(timezone.utc).isoformat(),
            "status": "confirmed",
            "emailSent": email_sent,
            "emailProvider": email_provider if email_sent else None,
            "userId": userId,
            "distributorName": distributorName,
            "specifications": {
                "doorColorLow": doorColorLow,
                "doorColorHigh": doorColorHigh,
                "doorColorColumns": doorColorColumns,
                "sideColor": sideColor,
                "carcassColor": carcassColor,
                "globalFinish": globalFinish
            }
        }
        await db.orders.insert_one(order_record)
        
        # =============================================
        # CREAR ORDEN DE FABRICACIÓN AUTOMÁTICAMENTE
        # =============================================
        manufacturing_order_id = None
        manufacturing_number = None
        try:
            # Generar número de orden de fabricación
            current_year = datetime.now().year
            counter_id = f"manufacturing_order_{current_year}"
            
            counter_result = await db.counters.find_one_and_update(
                {"_id": counter_id},
                {"$inc": {"seq": 1}},
                upsert=True,
                return_document=True
            )
            seq_number = counter_result["seq"]
            mfg_order_number = f"OF-{current_year}-{seq_number:04d}"
            
            # Generar número de fabricación secuencial global
            mfg_counter = await db.counters.find_one_and_update(
                {"_id": "manufacturing_number_global"},
                {"$inc": {"seq": 1}},
                upsert=True,
                return_document=True
            )
            manufacturing_number = mfg_counter["seq"]
            
            # Preparar items para la orden de fabricación
            mfg_items = []
            total_pieces = 0
            total_area = 0.0
            
            for item in items_list:
                item_id = f"moi-{uuid.uuid4().hex[:8]}"
                width = float(item.get("width", item.get("customWidth", 60)))
                height = float(item.get("height", item.get("customHeight", 70)))
                depth = float(item.get("depth", item.get("customDepth", 58)))
                qty = int(item.get("quantity", 1))
                
                mfg_items.append({
                    "id": item_id,
                    "productCode": item.get("code", item.get("productCode", "")),
                    "productName": item.get("name", item.get("productName", "")),
                    "quantity": qty,
                    "width": width,
                    "height": height,
                    "depth": depth,
                    "material": carcassColor or "",
                    "doorFinish": doorColorLow or doorColorHigh or "",
                    "notes": "",
                    "status": "pending",
                    "fabricationStatus": "pending"
                })
                total_pieces += qty
                total_area += (width * height * qty) / 10000  # m²
            
            # Crear documento de orden de fabricación
            mfg_order_doc = {
                "id": f"mfg-{uuid.uuid4().hex[:8]}",
                "orderNumber": mfg_order_number,
                "manufacturingNumber": manufacturing_number,
                "sourceType": "order_confirmation",
                "sourceBudgetId": None,
                "sourceOrderId": order_record["id"],
                "customerName": customerName,
                "customerCode": "",
                "contactPhone": "",
                "deliveryAddress": customerAddress,
                "createdAt": datetime.now(timezone.utc).isoformat(),
                "updatedAt": datetime.now(timezone.utc).isoformat(),
                "requestedDeliveryDate": None,
                "estimatedDeliveryDate": None,
                "actualDeliveryDate": None,
                "status": "confirmed",  # Directamente confirmada (viene de pedido)
                "priority": "normal",
                "items": mfg_items,
                "totalPieces": total_pieces,
                "totalArea": round(total_area, 3),
                "assignedToUserId": None,
                "assignedToName": None,
                "internalNotes": f"Creada automáticamente desde pedido #{budgetNumber}",
                "productionNotes": notes or "",
                "deliveryNotes": "",
                "createdByUserId": userId,
                "createdByName": distributorName or ""
            }
            
            await db.manufacturing_orders.insert_one(mfg_order_doc)
            manufacturing_order_id = mfg_order_doc["id"]
            
            # Actualizar el pedido con referencia a la orden de fabricación
            await db.orders.update_one(
                {"id": order_record["id"]},
                {"$set": {
                    "manufacturingOrderId": manufacturing_order_id,
                    "manufacturingOrderNumber": mfg_order_number,
                    "manufacturingNumber": manufacturing_number
                }}
            )
            
            logger.info(f"Manufacturing order {mfg_order_number} (Nº FAB: {manufacturing_number}) created for order {budgetNumber}")
            
        except Exception as mfg_error:
            logger.error(f"Error creating manufacturing order: {mfg_error}")
            # No fallar el pedido si la orden de fabricación no se puede crear
        
        logger.info(f"Order confirmed: {budgetNumber}" + (f" sent via {email_provider} to {email}" if email_sent else " (email not sent)"))
        
        # Construir respuesta con información de la orden de fabricación
        base_response = {
            "success": True,
            "orderId": order_record["id"],
            "manufacturingOrderId": manufacturing_order_id,
            "manufacturingNumber": manufacturing_number
        }
        
        if email_sent:
            return {
                **base_response,
                "message": f"Pedido confirmado y enviado a {email}" + (f" (vía {email_provider})" if email_provider else "") + (f". Orden de fabricación Nº FAB: {manufacturing_number} creada." if manufacturing_number else ""),
                "emailProvider": email_provider
            }
        else:
            return {
                **base_response,
                "message": f"Pedido confirmado." + (f" Orden de fabricación Nº FAB: {manufacturing_number} creada." if manufacturing_number else "") + " El email no se pudo enviar (problema con SendGrid y Resend). Contacte con soporte técnico.",
                "warning": "Email no enviado"
            }
        
    except Exception as e:
        logger.error(f"Order confirmation error: {e}")
        error_msg = str(e)
        if "401" in error_msg or "Unauthorized" in error_msg:
            error_msg = "Error de autenticación con SendGrid. Verifique que: 1) El API Key sea válido, 2) El remitente esté verificado en SendGrid (Sender Authentication), 3) El dominio esté verificado. Visite https://app.sendgrid.com/settings/sender_auth"
        elif "SENDGRID" in error_msg.upper():
            error_msg = "Servicio de email no configurado. Configure SendGrid en Panel Maestro > Configuración."
        raise HTTPException(status_code=500, detail=error_msg)

# ============================================
# MIS PEDIDOS - Listar pedidos del usuario
# ============================================

@api_router.get("/orders")
async def get_user_orders(userId: Optional[str] = None, limit: int = 100):
    """
    Obtiene los pedidos confirmados. Si se pasa userId, filtra por usuario.
    Sincroniza el estado de fabricación con fabrica_orders.
    """
    try:
        query = {}
        if userId:
            query["userId"] = userId
        
        orders = await db.orders.find(query, {"_id": 0}).sort("confirmedAt", -1).limit(limit).to_list(limit)
        
        # Sincronizar estado de fabricación con fabrica_orders
        for order in orders:
            # Buscar si existe una orden de fábrica para este presupuesto
            fab_order = await db.fabrica_orders.find_one(
                {"budgetNumber": order.get("budgetNumber")}, 
                {"_id": 0, "status": 1, "progress": 1}
            )
            if fab_order:
                # Mapear estado de fábrica a estado del pedido
                fab_status_map = {
                    "draft": "pending",
                    "confirmed": "confirmed",
                    "in_progress": "in_production",
                    "completed": "ready",
                    "shipped": "shipped",
                    "delivered": "delivered"
                }
                order["fabricationStatus"] = fab_status_map.get(fab_order.get("status"), "confirmed")
                order["fabricationProgress"] = fab_order.get("progress", 0)
            else:
                order["fabricationStatus"] = "confirmed"
                order["fabricationProgress"] = 0
        
        return orders
    except Exception as e:
        logger.error(f"Error fetching orders: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/orders/{order_id}")
async def get_order_detail(order_id: str):
    """
    Obtiene el detalle de un pedido específico
    """
    try:
        order = await db.orders.find_one({"id": order_id}, {"_id": 0})
        if not order:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")
        return order
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching order {order_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# DESPIECE (BILL OF MATERIALS) API
# ============================================


def calculate_furniture_despiece(
    item: DespieceItemInput,
    carcass_material: str,
    back_material: str,
    grosor: float,
    back_thickness: float = 8  # Grosor de trasera en mm
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
    # VERTICALES - Usan el ALTO COMPLETO
    # =============================================
    
    # LATERAL IZQUIERDO (Side panel - full height)
    # Para muebles de rincón, el lateral tiene forma especial
    lateral_fondo = d if not is_rincon else d - 5  # Rincón: lateral más corto
    add_component(
        "Lateral izquierdo", "LAT-I",
        carcass_material,
        h, lateral_fondo, g, 1,  # ALTO COMPLETO x FONDO (en cm)
        "1L canto" + (" (rincón)" if is_rincon else "")
    )
    
    # LATERAL DERECHO (Side panel - full height)
    add_component(
        "Lateral derecho", "LAT-D",
        carcass_material,
        h, lateral_fondo, g, 1,  # ALTO COMPLETO x FONDO (en cm)
        "1L canto" + (" (rincón)" if is_rincon else "")
    )
    
    # =============================================
    # HORIZONTALES - Descontar grosor de los laterales
    # =============================================
    
    # Ancho interior (entre laterales) en cm
    ancho_interior = w - (2 * g)
    
    # TAPA SUPERIOR (Top panel - between sides)
    # Los fregaderos NO tienen tapa superior (hueco para la encimera)
    if not is_fregadero:
        add_component(
            "Tapa superior", "TAPA-S", 
            carcass_material,
            ancho_interior, d, g, 1,
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
            ancho_interior, d, g, 1,
            "1L canto" if is_bajo else ""
        )
    
    # TRASERA (Back panel) - grosor configurable desde armazón
    # Convertir mm a cm (ej: 8mm = 0.8cm)
    back_thickness_cm = back_thickness / 10
    back_height = h - 0.6  # Encajada en ranuras (0.3cm arriba y abajo)
    add_component(
        "Trasera modulo", "TRAS",
        back_material,
        ancho_interior, back_height, back_thickness_cm, 1,
        f"Tablero {int(back_thickness)}mm"
    )
    
    # BALDAS / ESTANTES (Shelves) - según tipo de mueble y altura
    # Los estantes son HORIZONTALES, descontar grosor de laterales
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
        shelf_length = ancho_interior  # Entre laterales
        shelf_width = d - 2  # Ligeramente retranqueado del frontal (2cm)
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
        # TOLERANCIAS CORRECTAS:
        # - Alto: 2mm menos que el alto del mueble (0.2 cm)
        # - Ancho: 3mm menos que el ancho correspondiente (0.3 cm)
        door_height_tolerance = 0.2  # 2mm en cm
        door_width_tolerance = 0.3   # 3mm en cm
        
        # Alto de puerta: altura del mueble - 2mm
        door_height = h - door_height_tolerance
        
        # Ancho de puerta según número de puertas
        if num_doors == 2:
            # Cada puerta = mitad del ancho - 3mm
            door_width = (w / 2) - door_width_tolerance
        else:
            # Puerta única = ancho total - 3mm
            door_width = w - door_width_tolerance
        
        # Grosor típico de puerta: 19mm (1.9cm)
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
                request.backThickness
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



# ============================================
# EXPORT SPECIFIC COLLECTIONS TO EXCEL
# ============================================

@api_router.get("/export/clientes")
async def export_clientes_excel(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Exportar clientes a Excel"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("sub")
        
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user or not user.get("isAdmin"):
            raise HTTPException(status_code=403, detail="Solo administradores pueden exportar")
        
        # Obtener clientes
        clients = await db.clients.find({}).to_list(length=None)
        
        # Crear Excel (vacío si no hay clientes)
        import pandas as pd
        from io import BytesIO
        
        data = []
        for c in clients:
            data.append({
                'NOMBRE': c.get('name', ''),
                'EMPRESA': c.get('company', ''),
                'EMAIL': c.get('email', ''),
                'TELEFONO': c.get('phone', ''),
                'DIRECCION': c.get('address', ''),
                'CIUDAD': c.get('city', ''),
                'CP': c.get('postalCode', ''),
                'TIPO': c.get('type', ''),
                'SEGMENTO': c.get('segment', ''),
                'COMERCIAL': c.get('assignedTo', ''),
                'ESTADO': 'Activo' if c.get('isActive') else 'Potencial',
                'NOTAS': c.get('notes', ''),
                'CREADO': str(c.get('createdAt', ''))[:10],
            })
        
        df = pd.DataFrame(data)
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Clientes')
        output.seek(0)
        
        filename = f"LUIGGI_Clientes_{datetime.now().strftime('%Y%m%d')}.xlsx"
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")
    except Exception as e:
        logger.error(f"Export clientes error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/export/presupuestos")
async def export_presupuestos_excel(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Exportar presupuestos a Excel"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("sub")
        
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=403, detail="Usuario no encontrado")
        
        # Obtener proyectos/presupuestos
        projects = await db.projects.find({}).to_list(length=None)
        
        if not projects:
            raise HTTPException(status_code=404, detail="No hay presupuestos para exportar")
        
        import pandas as pd
        from io import BytesIO
        
        data = []
        for p in projects:
            # Calcular totales
            items = p.get('items', [])
            total_pvp = sum(item.get('totalPrice', 0) for item in items)
            total_coste = sum(item.get('costPrice', 0) * item.get('quantity', 1) for item in items)
            
            data.append({
                'EXPEDIENTE': p.get('expediente', ''),
                'REFERENCIA': p.get('projectReference', ''),
                'CLIENTE': p.get('clientName', ''),
                'COMERCIAL': p.get('userName', ''),
                'FECHA': str(p.get('createdAt', ''))[:10],
                'TOTAL_PVP': round(total_pvp, 2),
                'TOTAL_COSTE': round(total_coste, 2),
                'MARGEN': round(total_pvp - total_coste, 2),
                'NUM_ARTICULOS': len(items),
                'ZONA': p.get('zone', ''),
                'ACABADO': p.get('finish', ''),
                'ESTADO': p.get('status', 'borrador'),
            })
        
        df = pd.DataFrame(data)
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Presupuestos')
        output.seek(0)
        
        filename = f"LUIGGI_Presupuestos_{datetime.now().strftime('%Y%m%d')}.xlsx"
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")
    except Exception as e:
        logger.error(f"Export presupuestos error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/export/crm")
async def export_crm_excel(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Exportar datos CRM a Excel (oportunidades, actividades, calendario)"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("sub")
        
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user or not user.get("canAccessCRM"):
            raise HTTPException(status_code=403, detail="Sin acceso a CRM")
        
        import pandas as pd
        from io import BytesIO
        
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Oportunidades
            opportunities = await db.crm_opportunities.find({}).to_list(length=None)
            if opportunities:
                opp_data = []
                for o in opportunities:
                    opp_data.append({
                        'TITULO': o.get('title', ''),
                        'CLIENTE': o.get('clientName', ''),
                        'VALOR': o.get('value', 0),
                        'ETAPA': o.get('stage', ''),
                        'PROBABILIDAD': o.get('probability', 0),
                        'COMERCIAL': o.get('assignedTo', ''),
                        'FECHA_CIERRE': str(o.get('expectedCloseDate', ''))[:10],
                        'CREADO': str(o.get('createdAt', ''))[:10],
                    })
                pd.DataFrame(opp_data).to_excel(writer, index=False, sheet_name='Oportunidades')
            
            # Actividades
            activities = await db.crm_activities.find({}).to_list(length=None)
            if activities:
                act_data = []
                for a in activities:
                    act_data.append({
                        'TIPO': a.get('type', ''),
                        'TITULO': a.get('title', ''),
                        'DESCRIPCION': a.get('description', ''),
                        'CLIENTE': a.get('clientName', ''),
                        'COMERCIAL': a.get('userName', ''),
                        'FECHA': str(a.get('date', ''))[:10],
                        'COMPLETADA': 'Sí' if a.get('completed') else 'No',
                    })
                pd.DataFrame(act_data).to_excel(writer, index=False, sheet_name='Actividades')
            
            # Eventos calendario
            events = await db.crm_calendar.find({}).to_list(length=None)
            if events:
                evt_data = []
                for e in events:
                    evt_data.append({
                        'TITULO': e.get('title', ''),
                        'TIPO': e.get('type', ''),
                        'INICIO': str(e.get('start', '')),
                        'FIN': str(e.get('end', '')),
                        'CLIENTE': e.get('clientName', ''),
                        'COMERCIAL': e.get('userName', ''),
                        'NOTAS': e.get('notes', ''),
                    })
                pd.DataFrame(evt_data).to_excel(writer, index=False, sheet_name='Calendario')
        
        output.seek(0)
        
        filename = f"LUIGGI_CRM_{datetime.now().strftime('%Y%m%d')}.xlsx"
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")
    except Exception as e:
        logger.error(f"Export CRM error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/export/usuarios")
async def export_usuarios_excel(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Exportar usuarios a Excel (solo admin)"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("sub")
        
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user or not user.get("isAdmin"):
            raise HTTPException(status_code=403, detail="Solo administradores")
        
        users = await db.users.find({}).to_list(length=None)
        
        import pandas as pd
        from io import BytesIO
        
        data = []
        for u in users:
            rol = "Director" if u.get('isAdmin') else \
                  "Resp. Delegación" if u.get('isResponsableDelegacion') else \
                  "Comercial" if u.get('isRepresentative') else \
                  "Tienda" if u.get('isTienda') else "Colaborador"
            
            data.append({
                'USUARIO': u.get('username', ''),
                'NOMBRE_CLIENTE': u.get('clientName', ''),
                'ROL': rol,
                'ACTIVO': 'Sí' if u.get('isActive') else 'No',
                'DESCUENTO': u.get('commercialDiscount', 0),
                'MODULOS': ', '.join(u.get('allowedModules', [])),
                'VER_COSTE': 'Sí' if u.get('canSeeCost') else 'No',
                'CRM': 'Sí' if u.get('canAccessCRM') else 'No',
                'IA_LAB': 'Sí' if u.get('canUseAIAnalysis') else 'No',
            })
        
        df = pd.DataFrame(data)
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Usuarios')
        output.seek(0)
        
        filename = f"LUIGGI_Usuarios_{datetime.now().strftime('%Y%m%d')}.xlsx"
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")
    except Exception as e:
        logger.error(f"Export usuarios error: {e}")
        raise HTTPException(status_code=500, detail=str(e))



# ============================================
# MAINTENANCE MODE API
# ============================================


@api_router.get("/maintenance/status")
async def get_maintenance_status():
    """Get current maintenance mode status - accessible to everyone"""
    global maintenance_state
    
    # Sync with database on first call
    db_state = await db.system_settings.find_one({"key": "maintenance_mode"})
    if db_state:
        maintenance_state = db_state.get("value", maintenance_state)
    
    return MaintenanceStatusResponse(
        isActive=maintenance_state.get("active", False),
        reason=maintenance_state.get("message", ""),
        startedAt=maintenance_state.get("activatedAt"),
        estimatedEndAt=maintenance_state.get("estimatedEndTime"),
        lastBackup=maintenance_state.get("preUpdateBackupId")
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
    
    # Start backup scheduler from backup module
    start_backup_scheduler()

@app.on_event("shutdown")
async def shutdown_db_client():
    backup_scheduler.shutdown()
    client.close()