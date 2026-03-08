from fastapi import FastAPI, APIRouter, File, UploadFile, Form, HTTPException, BackgroundTasks, Request, Depends
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
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import asyncio

# Servicios de seguridad
from services.jwt_service import (
    create_access_token,
    create_refresh_token,
    verify_access_token,
    verify_refresh_token,
    get_current_user,
    require_auth,
    require_admin,
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
    crm_router
)

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
    MaintenanceActivateRequest, MaintenanceStatusResponse
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
# Nota: auth, products, clients, projects, crm están duplicados en server.py
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
async def get_products(module: Optional[str] = None):
    """Obtener todos los productos, opcionalmente filtrados por módulo"""
    query = {}
    if module:
        query["module"] = module
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
        
        # Send email
        sg = SendGridAPIClient(sendgrid_key)
        response = sg.send(message)
        
        # Log the order confirmation
        order_record = {
            "id": f"order-{uuid.uuid4().hex[:8]}",
            "budgetNumber": budgetNumber,
            "customerName": customerName,
            "customerAddress": customerAddress,
            "totalAmount": float(totalAmount),
            "email": email,
            "notes": notes,
            "itemsCount": len(items_list),
            "attachmentsCount": sum(1 for a in attachments if a and a.filename),
            "confirmedAt": datetime.now(timezone.utc).isoformat(),
            "status": "confirmed"
        }
        await db.orders.insert_one(order_record)
        
        logger.info(f"Order confirmed: {budgetNumber} sent to {email}")
        
        return {
            "success": True,
            "message": f"Pedido confirmado y enviado a {email}",
            "orderId": order_record["id"]
        }
        
    except Exception as e:
        logger.error(f"Order confirmation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
@limiter.limit(get_limit("backup"))
async def trigger_manual_backup(request: Request, background_tasks: BackgroundTasks):
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
        
        # Auditoría
        audit.log(
            AuditAction.BACKUP_CREATE,
            resource_type="backup",
            resource_id=history_entry["id"],
            request=request,
            details={"type": "manual", "item_count": total_items}
        )
        
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
@limiter.limit(get_limit("export"))
async def download_backup(request: Request):
    """Download backup as JSON file (for manual save to Google Drive)"""
    try:
        backup_data = await create_backup_data()
        
        # Auditoría
        audit.log(
            AuditAction.BACKUP_CREATE,
            resource_type="backup",
            request=request,
            details={"type": "download"}
        )
        
        return backup_data
    except Exception as e:
        logger.error(f"Download backup error: {e}")
        raise HTTPException(status_code=500, detail=f"Error al descargar backup: {str(e)}")

@api_router.post("/backup/restore")
@limiter.limit(get_limit("backup"))
async def restore_backup(request: Request, backup_data: Dict):
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
async def get_contacts(
    status: Optional[str] = None, 
    search: Optional[str] = None, 
    assignedTo: Optional[str] = None, 
    isAdmin: Optional[bool] = True,
    requestingUserId: Optional[str] = None
):
    """Get all contacts with optional filters, including total value from opportunities
    
    SEGURIDAD: El parámetro isAdmin se VERIFICA contra la base de datos, no se confía en el cliente.
    
    Para usuarios NO admin (comerciales/representantes), devuelve:
    - Sus propios contactos asignados
    - Los contactos de sus tiendas vinculadas (linkedRepresentativeId)
    
    assignedTo: ID del usuario comercial para filtrar sus contactos asignados
    requestingUserId: ID del usuario que hace la petición (para verificar permisos)
    """
    try:
        # SEGURIDAD: Verificar rol del usuario en la base de datos
        verified_is_admin = False
        if requestingUserId:
            requesting_user = await db.users.find_one({"id": requestingUserId}, {"_id": 0})
            if requesting_user:
                verified_is_admin = (
                    requesting_user.get("isAdmin", False) or 
                    requesting_user.get("isResponsableDelegacion", False)
                )
        
        # Si el cliente dice que es admin pero la DB dice que no, usar la DB
        effective_is_admin = verified_is_admin if requestingUserId else isAdmin
        
        query = {}
        if status:
            query["status"] = status
        if search:
            search_filter = [
                {"name": {"$regex": search, "$options": "i"}},
                {"company": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}}
            ]
        
        # SEGURIDAD: Si NO es admin verificado y tiene assignedTo, filtrar por comercial + sus tiendas
        if not effective_is_admin and assignedTo:
            # Obtener las tiendas vinculadas a este comercial
            shops = await db.users.find(
                {"linkedRepresentativeId": assignedTo},
                {"id": 1, "_id": 0}
            ).to_list(100)
            shop_ids = [s["id"] for s in shops]
            
            # Incluir contactos del comercial Y de sus tiendas
            all_ids = [assignedTo] + shop_ids
            assigned_filter = {"$or": [
                {"assignedTo": {"$in": all_ids}},
                {"createdBy": {"$in": all_ids}}
            ]}
            
            # Combinar con búsqueda si existe
            if search:
                query["$and"] = [assigned_filter, {"$or": search_filter}]
            else:
                query.update(assigned_filter)
        elif search:
            query["$or"] = search_filter
        
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

@api_router.get("/crm/contacts/{contact_id}/custom-values")
async def get_contact_custom_values(contact_id: str):
    """Get custom budget values for a specific contact/client"""
    try:
        contact = await db.contacts.find_one({"id": contact_id}, {"_id": 0})
        if not contact:
            raise HTTPException(status_code=404, detail="Contacto no encontrado")
        
        return {
            "contactId": contact_id,
            "contactName": contact.get("name", ""),
            "customCarcassMaterialId": contact.get("customCarcassMaterialId"),
            "customWidthIncrement": contact.get("customWidthIncrement"),
            "customHeightIncrement": contact.get("customHeightIncrement"),
            "customDepthIncrement": contact.get("customDepthIncrement"),
            "customVigaCutIncrement": contact.get("customVigaCutIncrement"),
            "customPointValueMontada": contact.get("customPointValueMontada"),
            "customPointValueDespiece": contact.get("customPointValueDespiece")
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get contact custom values error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/crm/contacts/{contact_id}/custom-values")
async def update_contact_custom_values(contact_id: str, values: dict):
    """Update custom budget values for a contact - ADMIN ONLY
    
    Allows admin to set personalized values for:
    - customCarcassMaterialId: Material armazón específico
    - customWidthIncrement: Incremento corte ancho
    - customHeightIncrement: Incremento corte alto
    - customDepthIncrement: Incremento corte fondo
    - customVigaCutIncrement: Incremento corte viga
    - customPointValueMontada: Valor punto montada
    - customPointValueDespiece: Valor punto despiece
    """
    try:
        # Only allow updating custom fields
        allowed_fields = [
            "customCarcassMaterialId", "customWidthIncrement", "customHeightIncrement",
            "customDepthIncrement", "customVigaCutIncrement", 
            "customPointValueMontada", "customPointValueDespiece"
        ]
        
        update_data = {k: v for k, v in values.items() if k in allowed_fields}
        update_data["updatedAt"] = datetime.now(timezone.utc)
        
        result = await db.contacts.update_one(
            {"id": contact_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Contacto no encontrado")
        
        logger.info(f"Custom values updated for contact {contact_id}: {update_data}")
        return {"success": True, "message": "Valores personalizados actualizados"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update contact custom values error: {e}")
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
async def get_opportunities(stage: Optional[str] = None, contactId: Optional[str] = None, assignedTo: Optional[str] = None, isAdmin: Optional[bool] = True, businessType: Optional[str] = None, moduleType: Optional[str] = None):
    """Get all opportunities with optional filters
    
    Para usuarios NO admin (comerciales/representantes), devuelve:
    - Sus propias oportunidades asignadas
    - Las oportunidades de sus tiendas vinculadas (linkedRepresentativeId)
    
    assignedTo: ID del usuario comercial para filtrar sus oportunidades
    isAdmin: Si es False, solo devuelve oportunidades del comercial y sus tiendas
    businessType: cocina, armarios o None para todos
    moduleType: montada, despiece o None para todos (solo aplica si businessType=cocina)
    """
    try:
        query = {}
        if stage:
            query["stage"] = stage
        if contactId:
            query["contactId"] = contactId
        if businessType:
            query["businessType"] = businessType
        if moduleType:
            query["moduleType"] = moduleType
        
        # IMPORTANTE: Si NO es admin y tiene assignedTo, filtrar por comercial + sus tiendas
        if not isAdmin and assignedTo:
            # Obtener las tiendas vinculadas a este comercial
            shops = await db.users.find(
                {"linkedRepresentativeId": assignedTo},
                {"id": 1, "_id": 0}
            ).to_list(100)
            shop_ids = [s["id"] for s in shops]
            
            # Incluir oportunidades del comercial Y de sus tiendas
            all_ids = [assignedTo] + shop_ids
            query["$or"] = [
                {"assignedTo": {"$in": all_ids}},
                {"createdBy": {"$in": all_ids}}
            ]
        
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
async def create_opportunity_from_project(project_id: str, businessType: str = "cocina"):
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
        
        # Determine business type label for title
        type_label = "Cocina" if businessType == "cocina" else "Armarios" if businessType == "armarios" else "Cocina/Armarios"
        
        # Create opportunity
        opp = OpportunityModel(
            title=f"Presupuesto {type_label} - {customer_name}",
            description=f"Presupuesto #{project.get('budgetNumber', '')}",
            contactId=contact_id,
            contactName=customer_name,
            value=total_value,
            probability=50,
            stage="proposal",
            linkedProjectId=project_id,
            linkedProjectNumber=project.get("budgetNumber", ""),
            businessType=businessType
        ).model_dump()
        opp['createdAt'] = opp['createdAt'].isoformat()
        opp['updatedAt'] = opp['updatedAt'].isoformat()
        
        await db.opportunities.insert_one(opp)
        
        # Link project to contact
        await db.contacts.update_one(
            {"id": contact_id},
            {"$addToSet": {"linkedProjectIds": project_id}}
        )
        
        # Update contact with businessTypes
        await db.contacts.update_one(
            {"id": contact_id},
            {"$addToSet": {"businessTypes": businessType}}
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


def calculate_furniture_despiece(
    item: DespieceItemInput,
    carcass_material: str,
    back_material: str,
    grosor: float
) -> FurnitureDespiece:
    """
    Calculate the despiece (bill of materials) for a single furniture piece.
    
    REGLA FUNDAMENTAL:
    - VERTICALES (laterales/costados): Usan el ALTO COMPLETO del mueble
    - HORIZONTALES (tapas, estantes): Se les descuenta el GROSOR del casco (x2)
    
    Standard furniture components:
    - LATERAL IZQUIERDO: height x depth (ALTO COMPLETO)
    - LATERAL DERECHO: height x depth (ALTO COMPLETO)
    - TAPA SUPERIOR: (width - 2*grosor) x depth (entre laterales)
    - TAPA INFERIOR: (width - 2*grosor) x depth (entre laterales)
    - TRASERA: (width - 2*grosor) x (height - 6mm) (encajada en ranuras)
    - BALDA/ESTANTE: (width - 2*grosor) x (depth - 3mm) - optional shelves
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
    
    def add_component(name: str, short: str, material: str, length: float, width: float, thickness: float = grosor, qty: int = 1, notes: str = ""):
        nonlocal component_id
        component_id += 1
        area = (length * width * qty) / 1_000_000  # Convert mm² to m²
        components.append(ComponentPiece(
            id=f"CMP-{item.productId[:8]}-{component_id:03d}",
            name=name,
            nameShort=short,
            material=material,
            length=round(length, 1),
            width=round(width, 1),
            thickness=round(thickness, 1),
            quantity=qty,
            area=round(area, 4),
            notes=notes
        ))
    
    # =============================================
    # VERTICALES - Usan el ALTO COMPLETO
    # =============================================
    
    # LATERAL IZQUIERDO (Side panel - full height)
    add_component(
        "Lateral izquierdo", "LAT-I",
        carcass_material,
        h, d, g, 1,  # ALTO COMPLETO x FONDO
        "Canto frontal visto"
    )
    
    # LATERAL DERECHO (Side panel - full height)
    add_component(
        "Lateral derecho", "LAT-D",
        carcass_material,
        h, d, g, 1,  # ALTO COMPLETO x FONDO
        "Canto frontal visto"
    )
    
    # =============================================
    # HORIZONTALES - Descontar grosor de los laterales
    # =============================================
    
    # Ancho interior (entre laterales)
    ancho_interior = w - (2 * g)
    
    # TAPA SUPERIOR (Top panel - between sides)
    add_component(
        "Tapa superior", "TAPA-S", 
        carcass_material,
        ancho_interior, d, g, 1,
        "Canto frontal visto"
    )
    
    # TAPA INFERIOR (Bottom panel) - not always present in ALTOS
    if not is_alto:
        add_component(
            "Tapa inferior", "TAPA-I",
            carcass_material,
            ancho_interior, d, g, 1,
            "Canto frontal visto" if is_bajo else ""
        )
    else:
        # ALTOS use a narrower bottom rail
        add_component(
            "Travesaño inferior", "TRAV-I",
            carcass_material,
            ancho_interior, 80, g, 1,  # 80mm rail
            "Travesaño de sujeción"
        )
    
    # TRASERA (Back panel) - siempre más fina (8mm o 6mm)
    back_thickness = 8 if g >= 18 else 6
    back_height = h - 6  # Encajada en ranuras (3mm arriba y abajo)
    add_component(
        "Trasera modulo", "TRAS",
        back_material,
        ancho_interior + 6, back_height, back_thickness, 1,
        "Panel trasero encastrado"
    )
    
    # BALDAS / ESTANTES (Shelves) - estimate based on height
    # Los estantes son HORIZONTALES, descontar grosor de laterales
    shelf_count = 0
    if h >= 700:  # Tall units get more shelves
        shelf_count = 2 if h < 1200 else 3 if h < 1800 else 4
    elif h >= 350:
        shelf_count = 1
    
    if shelf_count > 0:
        shelf_length = ancho_interior  # Entre laterales
        shelf_width = d - 20  # Ligeramente retranqueado del frontal
        add_component(
            "Balda interior", "BALDA",
            carcass_material,
            shelf_length, shelf_width, g, shelf_count,
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


@api_router.post("/digitalizador/generate-exp-number")
async def generate_expediente_number(request: ExpedienteRequest):
    """
    Generate a unique expediente number using atomic MongoDB operation.
    Format: {CLIENTE}-{YYYY}-{NNN} (e.g., CLI001-2026-001)
    Each client has their own independent sequence.
    If no clientCode provided, uses global EXP prefix.
    Thread-safe for concurrent users.
    """
    try:
        current_year = datetime.now().year
        userId = request.userId
        clientCode = request.clientCode
        
        # Use client code or default to EXP for global numbering
        prefix = clientCode.upper() if clientCode else "EXP"
        counter_id = f"expediente_{prefix}_{current_year}"
        
        # Atomic find_and_modify to get next sequence number
        # Uses upsert to create the counter if it doesn't exist
        result = await db.counters.find_one_and_update(
            {"_id": counter_id},
            {"$inc": {"seq": 1}},
            upsert=True,
            return_document=True  # Return the document AFTER the update
        )
        
        seq_number = result["seq"]
        
        # Format: {PREFIX}-YYYY-NNN (with padding for 3 digits, auto-expands if > 999)
        if seq_number < 1000:
            exp_number = f"{prefix}-{current_year}-{seq_number:03d}"
        else:
            exp_number = f"{prefix}-{current_year}-{seq_number}"
        
        # Log for audit
        logger.info(f"Generated expediente number: {exp_number} for user: {userId}, client: {clientCode}")
        
        return {
            "success": True,
            "expNumber": exp_number,
            "clientCode": prefix,
            "year": current_year,
            "sequence": seq_number
        }
    except Exception as e:
        logger.error(f"Generate expediente number error: {e}")
        raise HTTPException(status_code=500, detail=f"Error generando número de expediente: {str(e)}")


@api_router.get("/digitalizador/current-exp-sequence")
async def get_current_expediente_sequence(clientCode: str = None):
    """Get the current expediente sequence number for a client (or global if no client)"""
    try:
        current_year = datetime.now().year
        prefix = clientCode.upper() if clientCode else "EXP"
        counter_id = f"expediente_{prefix}_{current_year}"
        
        counter = await db.counters.find_one({"_id": counter_id})
        
        current_seq = counter["seq"] if counter else 0
        
        return {
            "clientCode": prefix,
            "year": current_year,
            "currentSequence": current_seq,
            "nextExpNumber": f"{prefix}-{current_year}-{(current_seq + 1):03d}"
        }
    except Exception as e:
        logger.error(f"Get current expediente sequence error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
        
        # Aplicar incremento de margen si existe
        if request.globalMarkup > 0:
            total_neto = total_neto * (1 + request.globalMarkup / 100)
        
        total_con_iva = total_neto * (1 + request.ivaRate / 100)
        
        # Generar número de expediente si no viene proporcionado
        exp_number = request.expNumber
        if not exp_number:
            current_year = datetime.now().year
            result = await db.counters.find_one_and_update(
                {"_id": f"expediente_{current_year}"},
                {"$inc": {"seq": 1}},
                upsert=True,
                return_document=True
            )
            seq = result["seq"]
            exp_number = f"EXP-{current_year}-{seq:03d}" if seq < 1000 else f"EXP-{current_year}-{seq}"
        
        # Verificar que el número de expediente no exista ya
        existing = await db.digitalizador_history.find_one({"expNumber": exp_number})
        if existing:
            raise HTTPException(status_code=400, detail=f"El número de expediente {exp_number} ya existe. Por favor genera uno nuevo.")
        
        # Create history item
        history_item = {
            "id": f"digi-{uuid.uuid4().hex[:12]}",
            "expNumber": exp_number,
            "projectName": request.projectName,
            "customerName": request.customerName,
            "acabado": request.acabado,
            "armazon": request.armazon,
            "costados": request.costados,
            "lines": [line.model_dump() for line in request.lines],
            "globalDiscount": request.globalDiscount,
            "globalMarkup": request.globalMarkup,
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
            "item": history_item,
            "expNumber": exp_number
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



@api_router.post("/presupuestos")
async def save_digitalizador_to_presupuestos(request: DigitalizadorToProjectRequest):
    """
    Save a digitalizador budget to the main projects collection.
    This allows digitalized budgets to be managed alongside regular budgets.
    """
    try:
        # Convertir líneas del digitalizador al formato de items del proyecto
        items_montada = []
        for line in request.lines:
            item = {
                "id": f"digi-item-{uuid.uuid4().hex[:8]}",
                "productId": line.id,
                "productCode": line.reference or "DIGI",
                "productName": line.description,
                "quantity": line.quantity,
                "customWidth": 0,
                "customHeight": 0,
                "customDepth": 0,
                "manualPrice": line.price,
                "discount": line.discount,
                "isManual": line.isManual,
                "fromDigitalizador": True,
                "notes": ""
            }
            items_montada.append(item)
        
        # Crear el proyecto/presupuesto
        project_data = {
            "id": f"proj-digi-{uuid.uuid4().hex[:8]}",
            "userId": request.userId or "anonymous",
            "budgetNumber": request.expNumber,
            "customerName": request.customerName,
            "customerAddress": "",
            "internalReference": request.projectName,
            "itemsMontada": items_montada,
            "itemsDespiece": [],
            "doorColorLow": "",
            "doorColorHigh": "",
            "doorColorColumns": "",
            "sideColor": request.costados,
            "selectedCarcassMaterialId": request.armazon,
            "globalFinish": request.acabado,
            "globalDiscount": request.globalDiscount,
            "globalMarkup": request.globalMarkup,
            "ivaRate": request.ivaRate,
            "totalPvp": request.totalPvp,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat(),
            "status": "draft",
            "source": "digitalizador"
        }
        
        await db.projects.insert_one(project_data)
        project_data.pop('_id', None)
        
        logger.info(f"Digitalizador budget saved to projects: {request.expNumber}")
        
        return {
            "success": True,
            "message": "Presupuesto guardado en proyectos",
            "project": project_data
        }
    except Exception as e:
        logger.error(f"Save digitalizador to presupuestos error: {e}")
        raise HTTPException(status_code=500, detail=f"Error guardando presupuesto: {str(e)}")


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
            
            # Helper function for fuzzy search in catalog
            async def search_catalog_fuzzy(search_text: str, limit: int = 3):
                """Search products by reference or description using fuzzy matching"""
                if not search_text or len(search_text) < 2:
                    return []
                
                search_upper = search_text.upper().strip()
                search_words = search_upper.split()
                
                matches = []
                
                # Search by exact code match first
                exact_match = await db.products.find_one(
                    {"code": search_upper},
                    {"_id": 0, "id": 1, "code": 1, "name": 1, "points": 1, "zonePoints": 1}
                )
                if exact_match:
                    price = exact_match.get("points", 0) or 0
                    if exact_match.get("zonePoints"):
                        price = exact_match["zonePoints"].get("Z1", price)
                    matches.append(DigitalizadorMatchedProduct(
                        id=exact_match.get("id", ""),
                        code=exact_match.get("code", ""),
                        name=exact_match.get("name", ""),
                        price=float(price),
                        score=1.0
                    ))
                    return matches
                
                # Search by partial code or name match
                regex_patterns = [{"code": {"$regex": word, "$options": "i"}} for word in search_words if len(word) >= 3]
                regex_patterns.extend([{"name": {"$regex": word, "$options": "i"}} for word in search_words if len(word) >= 3])
                
                if regex_patterns:
                    query = {"$or": regex_patterns}
                    cursor = db.products.find(query, {"_id": 0, "id": 1, "code": 1, "name": 1, "points": 1, "zonePoints": 1}).limit(limit * 3)
                    products = await cursor.to_list(limit * 3)
                    
                    for p in products:
                        # Calculate match score based on word matches
                        code = (p.get("code", "") or "").upper()
                        name = (p.get("name", "") or "").upper()
                        
                        score = 0
                        for word in search_words:
                            if word in code:
                                score += 0.5
                            if word in name:
                                score += 0.3
                        
                        # Bonus for code prefix match
                        if code.startswith(search_upper[:3] if len(search_upper) >= 3 else search_upper):
                            score += 0.2
                        
                        score = min(score, 0.95)  # Cap at 0.95 for non-exact matches
                        
                        if score > 0.2:
                            price = p.get("points", 0) or 0
                            if p.get("zonePoints"):
                                price = p["zonePoints"].get("Z1", price)
                            matches.append(DigitalizadorMatchedProduct(
                                id=p.get("id", ""),
                                code=p.get("code", ""),
                                name=p.get("name", ""),
                                price=float(price),
                                score=score
                            ))
                    
                    # Sort by score and limit
                    matches.sort(key=lambda x: x.score, reverse=True)
                    return matches[:limit]
                
                return []
            
            # Build response lines with catalog matching
            extracted_lines = []
            for idx, line in enumerate(parsed.get("lines", [])):
                reference = str(line.get("reference") or "")
                description = str(line.get("description") or "")
                
                # Search for matching products
                search_text = reference if reference else description
                matched_products = await search_catalog_fuzzy(search_text)
                
                # If no match by reference, try by description keywords
                if not matched_products and description:
                    matched_products = await search_catalog_fuzzy(description)
                
                extracted_lines.append(DigitalizadorLine(
                    id=f"LINE-{uuid.uuid4().hex[:8]}",
                    quantity=int(line.get("quantity") or 1),
                    reference=reference,
                    description=description,
                    price=float(line.get("price") or 0),
                    discount=0,
                    isManual=False,
                    matchedProducts=matched_products
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


@api_router.get("/digitalizador/search-catalog")
async def search_digitalizador_catalog(q: str, limit: int = 5):
    """
    Search products in catalog for digitalizador autocomplete.
    Returns matching products with fuzzy search.
    """
    try:
        if not q or len(q) < 2:
            return {"products": []}
        
        search_upper = q.upper().strip()
        search_words = search_upper.split()
        
        results = []
        
        # Search by exact code match first
        exact_match = await db.products.find_one(
            {"code": search_upper},
            {"_id": 0, "id": 1, "code": 1, "name": 1, "points": 1, "zonePoints": 1, "category": 1}
        )
        if exact_match:
            price = exact_match.get("points", 0) or 0
            if exact_match.get("zonePoints"):
                price = exact_match["zonePoints"].get("Z1", price)
            results.append({
                "id": exact_match.get("id", ""),
                "code": exact_match.get("code", ""),
                "name": exact_match.get("name", ""),
                "category": exact_match.get("category", ""),
                "price": float(price),
                "score": 1.0
            })
        
        # Search by partial code or name match
        regex_patterns = []
        for word in search_words:
            if len(word) >= 2:
                regex_patterns.append({"code": {"$regex": word, "$options": "i"}})
                regex_patterns.append({"name": {"$regex": word, "$options": "i"}})
        
        if regex_patterns:
            query = {"$or": regex_patterns}
            cursor = db.products.find(
                query,
                {"_id": 0, "id": 1, "code": 1, "name": 1, "points": 1, "zonePoints": 1, "category": 1}
            ).limit(limit * 3)
            products = await cursor.to_list(limit * 3)
            
            for p in products:
                # Skip if already in results
                if any(r["code"] == p.get("code") for r in results):
                    continue
                
                code = (p.get("code", "") or "").upper()
                name = (p.get("name", "") or "").upper()
                
                score = 0
                for word in search_words:
                    if word in code:
                        score += 0.5
                    if word in name:
                        score += 0.3
                
                if code.startswith(search_upper[:3] if len(search_upper) >= 3 else search_upper):
                    score += 0.2
                
                score = min(score, 0.95)
                
                if score > 0.1:
                    price = p.get("points", 0) or 0
                    if p.get("zonePoints"):
                        price = p["zonePoints"].get("Z1", price)
                    results.append({
                        "id": p.get("id", ""),
                        "code": p.get("code", ""),
                        "name": p.get("name", ""),
                        "category": p.get("category", ""),
                        "price": float(price),
                        "score": score
                    })
        
        # Sort by score and limit
        results.sort(key=lambda x: x["score"], reverse=True)
        return {"products": results[:limit]}
        
    except Exception as e:
        logger.error(f"Catalog search error: {e}")
        return {"products": [], "error": str(e)}


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
        
        # ===== PRODUCTOS =====
        ws_products = wb.create_sheet("Productos")
        
        products = await db.products.find({}, {'_id': 0}).to_list(10000)
        prod_headers = ['Código', 'Nombre', 'Categoría', 'Serie', 'Ancho', 'Alto', 'Fondo', 'Puntos', 'Z1', 'Z2', 'Z3', 'Z4']
        for col, header in enumerate(prod_headers, 1):
            cell = ws_products.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
        
        for row_num, p in enumerate(products, 2):
            zp = p.get('zonePoints', {}) or {}
            ws_products.cell(row=row_num, column=1, value=p.get('code', ''))
            ws_products.cell(row=row_num, column=2, value=p.get('name', ''))
            ws_products.cell(row=row_num, column=3, value=p.get('category', ''))
            ws_products.cell(row=row_num, column=4, value=p.get('series', ''))
            ws_products.cell(row=row_num, column=5, value=p.get('width', 0))
            ws_products.cell(row=row_num, column=6, value=p.get('height', 0))
            ws_products.cell(row=row_num, column=7, value=p.get('depth', 0))
            ws_products.cell(row=row_num, column=8, value=p.get('points', 0))
            ws_products.cell(row=row_num, column=9, value=zp.get('Z1', 0))
            ws_products.cell(row=row_num, column=10, value=zp.get('Z2', 0))
            ws_products.cell(row=row_num, column=11, value=zp.get('Z3', 0))
            ws_products.cell(row=row_num, column=12, value=zp.get('Z4', 0))
        
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
        await log_audit("database_export", user_id, "admin", True, {"tables": ["users", "products", "projects"]})
        
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
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
        
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user or not user.get("isAdmin"):
            raise HTTPException(status_code=403, detail="Solo administradores pueden exportar")
        
        # Obtener clientes
        clients = await db.clients.find({}).to_list(length=None)
        
        if not clients:
            raise HTTPException(status_code=404, detail="No hay clientes para exportar")
        
        # Crear Excel
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
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
        
        user = await db.users.find_one({"_id": ObjectId(user_id)})
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
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
        
        user = await db.users.find_one({"_id": ObjectId(user_id)})
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
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
        
        user = await db.users.find_one({"_id": ObjectId(user_id)})
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


# ============================================
# ARMARIOS - PROYECTOS
# ============================================


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


@api_router.post("/crm/opportunities/from-armario/{project_id}")
async def create_opportunity_from_armario(project_id: str):
    """Create a CRM opportunity from an armario project"""
    try:
        # Get the armario project
        project = await db.armario_projects.find_one({"id": project_id}, {"_id": 0})
        if not project:
            raise HTTPException(status_code=404, detail="Proyecto de armario no encontrado")
        
        # Calculate project total value from despiece if available
        total_value = project.get("totalPrice", 0)
        
        # Use customer name or project name
        customer_name = project.get("customerName", project.get("name", "Cliente sin nombre"))
        
        # Check if contact exists or create one
        contact = await db.contacts.find_one({"name": customer_name}, {"_id": 0})
        
        if not contact:
            # Create new contact
            contact = ContactModel(
                name=customer_name,
                status="customer"
            ).model_dump()
            contact['createdAt'] = contact['createdAt'].isoformat()
            contact['updatedAt'] = contact['updatedAt'].isoformat()
            await db.contacts.insert_one(contact)
        
        contact_id = contact.get("id")
        
        # Create opportunity
        opp = OpportunityModel(
            title=f"Presupuesto Armarios - {customer_name}",
            description=f"Proyecto: {project.get('name', '')} - {project.get('width', 0)}x{project.get('height', 0)}cm",
            contactId=contact_id,
            contactName=customer_name,
            value=total_value,
            probability=50,
            stage="proposal",
            linkedProjectId=project_id,
            linkedProjectNumber=project.get("name", ""),
            businessType="armarios"
        ).model_dump()
        opp['createdAt'] = opp['createdAt'].isoformat()
        opp['updatedAt'] = opp['updatedAt'].isoformat()
        
        await db.opportunities.insert_one(opp)
        
        # Update contact with businessTypes
        await db.contacts.update_one(
            {"id": contact_id},
            {"$addToSet": {"businessTypes": "armarios"}}
        )
        
        opp.pop('_id', None)
        return {
            "opportunity": opp,
            "contact": contact,
            "message": "Oportunidad de armarios creada"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create opportunity from armario error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# ARMARIOS - IA CONFIGURACIÓN Y RENDER
# ============================================


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



@api_router.post("/armarios/ia/generate-layout")
async def ia_generate_layout(request: IALayoutRequest):
    """
    Generate wardrobe interior layout from natural language instructions.
    Uses AI to interpret the user's description and create module configurations.
    """
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        import json
        
        api_key = os.environ.get("EMERGENT_LLM_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="Clave de IA no configurada")
        
        chat = LlmChat(
            api_key=api_key,
            session_id=f"armario-layout-{uuid.uuid4()}",
            system_message="""Eres un diseñador de interiores de armarios experto.
Tu trabajo es interpretar las instrucciones del usuario y convertirlas en una configuración JSON para el armario.

Reglas de diseño:
- "maletero" o "trunk" va siempre arriba (primeros 30cm)
- "perchero" o "barra" o "hanging" va en la parte central-alta
- "cajones" o "drawers" van en la parte baja (últimos 50-80cm)
- "baldas" o "shelves" pueden ir en cualquier posición
- "zapatero" o "shoe rack" va en la parte baja
- "pantalonero" va en zona media-baja
- "joyero" va en zona media

Debes responder ÚNICAMENTE con un JSON válido sin explicaciones."""
        ).with_model("gemini", "gemini-2.0-flash")
        
        prompt = f"""El usuario quiere configurar un armario con {request.modules} módulos.
Dimensiones: {request.width}mm ancho x {request.height}mm alto x {request.depth}mm fondo.

INSTRUCCIONES DEL USUARIO:
"{request.instruction}"

Genera una configuración JSON con este formato exacto:
{{
  "moduleConfigs": [
    {{
      "shelves": número_de_baldas,
      "drawers": número_de_cajones,
      "hangingRods": número_de_barras_perchero (0, 1 o 2 para doble altura),
      "hangingHeight": altura_perchero_mm (1200 normal, 1000 para doble altura),
      "shoesRack": true/false,
      "trousersRack": true/false,
      "tieRack": true/false,
      "jewelryTray": true/false,
      "trunk": true/false (maletero arriba),
      "mirrorDoor": true/false
    }}
    // ... un objeto por cada módulo (total: {request.modules})
  ],
  "extras": {{
    "led": true/false (si menciona iluminación),
    "mirror": true/false (si menciona espejo)
  }}
}}

Interpreta las instrucciones del usuario y genera la configuración. Si no especifica algo para un módulo, usa valores por defecto sensatos (2 baldas, 1 barra).
Responde SOLO con el JSON, sin texto adicional."""

        msg = UserMessage(text=prompt)
        response = await chat.send_message(msg)
        
        # Limpiar la respuesta de posibles markdown
        json_text = response.strip()
        if json_text.startswith('```json'):
            json_text = json_text[7:]
        if json_text.startswith('```'):
            json_text = json_text[3:]
        if json_text.endswith('```'):
            json_text = json_text[:-3]
        json_text = json_text.strip()
        
        try:
            result = json.loads(json_text)
            
            # Validar que tiene la estructura correcta
            if 'moduleConfigs' not in result:
                return {"success": False, "error": "Respuesta IA no contiene moduleConfigs"}
            
            # Asegurar que hay la cantidad correcta de módulos
            while len(result['moduleConfigs']) < request.modules:
                result['moduleConfigs'].append({
                    "shelves": 2,
                    "drawers": 0,
                    "hangingRods": 1,
                    "hangingHeight": 1200
                })
            
            # Limitar al número de módulos solicitado
            result['moduleConfigs'] = result['moduleConfigs'][:request.modules]
            
            logger.info(f"IA layout generated for {request.modules} modules")
            
            return {
                "success": True,
                "moduleConfigs": result['moduleConfigs'],
                "extras": result.get('extras', {})
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing IA response: {e}")
            return {"success": False, "error": f"Error interpretando respuesta IA: {str(e)}"}
            
    except Exception as e:
        logger.error(f"Error en IA generate layout: {e}")
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
            system_message="You are a professional interior designer creating photorealistic renders of wardrobes. You must follow specifications EXACTLY."
        )
        
        chat.with_model("gemini", "gemini-3-pro-image-preview").with_params(modalities=["image", "text"])  # Nano Banana model
        
        # Construir descripción del tipo de puerta
        door_type_desc = {
            "sliding": "PUERTAS CORREDERAS (sliding doors on rails, overlap when open)",
            "hinged": "PUERTAS ABATIBLES CON BISAGRAS (traditional hinged doors with handles)",
            "folding": "PUERTAS PLEGABLES (bi-fold doors)"
        }.get(request.doorType, "PUERTAS CORREDERAS")
        
        # Describir interior DETALLADAMENTE por módulo
        interior_desc = []
        for i, mod in enumerate(request.moduleConfigs):
            items = []
            if mod.get('hangingRods', 0) > 0:
                rod_count = mod['hangingRods']
                items.append(f"{rod_count} chrome hanging rod{'s' if rod_count > 1 else ''}")
            if mod.get('shelves', 0) > 0:
                shelf_count = mod['shelves']
                items.append(f"{shelf_count} horizontal shelf{'ves' if shelf_count > 1 else ''}")
            if mod.get('drawers', 0) > 0:
                drawer_count = mod['drawers']
                items.append(f"{drawer_count} soft-close drawer{'s' if drawer_count > 1 else ''}")
            if mod.get('shoesRack'):
                items.append("angled shoe rack")
            if mod.get('trousersRack'):
                items.append("pull-out trouser rack")
            if mod.get('mirrorDoor'):
                items.append("full-length mirror on door interior")
            
            module_desc = f"Module {i+1} (from left): {', '.join(items) if items else 'empty space'}"
            interior_desc.append(module_desc)
        
        # Usar el número de puertas de la configuración del usuario
        doors_count = request.numDoors
        door_width = request.width / doors_count
        
        prompt = f"""Create a PHOTOREALISTIC interior design photograph of a BUILT-IN WARDROBE/CLOSET.

CRITICAL - FOLLOW THESE SPECIFICATIONS EXACTLY:

📐 DIMENSIONS:
- Total width: {request.width}mm ({request.width/10}cm / {round(request.width/25.4, 1)} inches)
- Total height: {request.height}mm ({request.height/10}cm)
- Depth: {request.depth}mm ({request.depth/10}cm)
- Number of interior modules/sections: {request.modules} modules

🚪 DOORS - CRITICAL - PAY ATTENTION:
- EXACT NUMBER OF DOORS: {doors_count} doors (this is mandatory!)
- Door type: {door_type_desc}
- Each door width: approximately {round(door_width)}mm
- Door color/finish: {request.exteriorColorName} (hex: {request.exteriorColorHex})
- Handle/knob style: {request.handleColorName} color handles
- Show doors 50% OPEN to reveal interior organization

🎨 COLORS - MATCH EXACTLY:
- EXTERIOR FINISH (doors): {request.exteriorColorName} (hex color: {request.exteriorColorHex})
- INTERIOR COLOR (shelves, back panel): {request.interiorColorName}
- All visible melamine surfaces should match these colors

📦 INTERIOR ORGANIZATION - FOLLOW EXACTLY:
{chr(10).join(interior_desc)}

🏠 ROOM SETTING:
- Room style: {request.roomStyle}
- Soft natural daylight from left side
- Wardrobe built into wall alcove
- Hardwood or laminate flooring visible
- Neutral wall color that complements the wardrobe

📸 IMAGE REQUIREMENTS:
- Professional interior photography style, NOT a 3D render or sketch
- Camera angle: 3/4 view from front-left to show interior through open doors
- High-end quality materials: melamine, chrome hardware, soft-close systems
- Realistic shadows and reflections
- Some clothing items neatly organized inside
- 4K quality, magazine-worthy composition

IMPORTANT: The wardrobe MUST have EXACTLY {doors_count} {request.doorType} doors. DO NOT add more or fewer doors.
Generate ONE high-quality photorealistic image."""

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
    """Configure scheduled backups and database indexes on startup"""
    # Crear índice único para números de expediente
    try:
        await db.digitalizador_history.create_index("expNumber", unique=True, sparse=True)
        logger.info("Índice único creado para expNumber en digitalizador_history")
    except Exception as e:
        logger.warning(f"Error creando índice expNumber (puede que ya exista): {e}")
    
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