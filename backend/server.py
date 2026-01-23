from fastapi import FastAPI, APIRouter, File, UploadFile, Form
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List
import uuid
from datetime import datetime, timezone
import base64
from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent
import json


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


# Define Models
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")  # Ignore MongoDB's _id field
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

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