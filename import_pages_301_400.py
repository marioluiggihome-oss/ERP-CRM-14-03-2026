#!/usr/bin/env python3
"""
Batch catalog import script for LUIGGI HOME - Pages 301-400
Processes PDF pages from the catalog using Gemini Vision to extract product data
"""

import os
import sys
import json
import asyncio
import uuid
import re
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient

# Import emergentintegrations
from emergentintegrations.llm.chat import LlmChat, UserMessage, FileContentWithMimeType

# Configuration
MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = 'test_database'
PDF_PAGES_DIR = '/app/pdf_pages_301_400'
EMERGENT_KEY = os.environ.get('EMERGENT_LLM_KEY', 'sk-emergent-4A3Ed5d56521e792e1')

# Connect to MongoDB
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

EXTRACTION_PROMPT = """Analiza esta página del catálogo de muebles de cocina LUIGGI HOME.

Extrae TODOS los productos de la página en formato JSON. Para cada producto incluye:
- reference: Código de referencia completo (ej: "G8A1P350", "G11SC1P400")
- name: Nombre descriptivo completo del producto
- category: Categoría (usa las categorías EXACTAS según el programa):
  * Para GOLA: "ALTOS GOLA", "BAJOS GOLA", "SEMICOLUMNAS GOLA", "COLUMNAS GOLA"
  * Para ESTÁNDAR: "ALTOS", "BAJOS", "SEMICOLUMNAS", "COLUMNAS", "SOBREMÓDULOS", "VITRINAS", "COSTADOS", "ESTANTES", "REGLETAS", "PUERTAS", "CORNISAS", "ZOCALOS"
  * Para ALUMINIO: "ALTOS ALUMINIO", "BAJOS ALUMINIO", "SEMICOLUMNAS ALUMINIO"
- series: Serie específica del producto (ej: "ALTO 80 FONDO 33", "ALTO 110 FONDO 58")
- programa: "GOLA", "ALUMINIO" o "ESTÁNDAR"
- width: Ancho en mm (extrae del código - últimos 3-4 dígitos generalmente indican el ancho en cm x 10)
- height: Alto en mm (basado en la serie o encabezado)
- depth: Profundidad/Fondo en mm (del encabezado de la sección)
- points: Valor de puntos de la columna PUNTOS (el último valor de la fila generalmente)
- zonePoints: Objeto con TODOS los valores por zona como números {Z1: valor, Z2: valor, ...}

REGLAS PARA EXTRAER DIMENSIONES:
- El código tiene el ancho: G8A1P350 -> 350mm de ancho
- La serie indica alto y fondo: "ALTO 80 FONDO 33" -> 800mm alto, 330mm fondo
- Si el código empieza con G (GOLA), el programa es GOLA
- Si empieza con A13 o similar (ALUMINIO), el programa es ALUMINIO
- Si empieza con número o letra sin G, generalmente es ESTÁNDAR

IMPORTANTE:
- Extrae TODOS los productos de la tabla
- Los valores de zonas son los números en columnas Z1-Z12
- PUNTOS suele ser la última columna
- Responde SOLO con JSON válido

Formato de respuesta:
{
  "products": [
    {
      "reference": "G8A1P350",
      "name": "Alto Gola 1 puerta 35cm",
      "category": "ALTOS GOLA",
      "series": "ALTO 80 FONDO 33",
      "programa": "GOLA",
      "width": 350,
      "height": 800,
      "depth": 330,
      "points": 179,
      "zonePoints": {"Z1": 116, "Z2": 119, "Z3": 124}
    }
  ],
  "pageInfo": "Descripción de la página"
}
"""

def extract_dimensions_from_code(code: str, series: str = None) -> dict:
    """Extract dimensions from product code and series"""
    dims = {"width": 0, "height": 0, "depth": 0}
    
    if not code:
        return dims
    
    code = code.upper()
    
    # Extract width from code (last 3-4 digits usually)
    width_match = re.search(r'(\d{3,4})$', code)
    if width_match:
        width_val = int(width_match.group(1))
        # If it's 3 digits, multiply by 10 for mm, if 4 digits it's already mm
        if width_val < 200:
            dims["width"] = width_val * 10
        else:
            dims["width"] = width_val
    
    # Extract from series if available
    if series:
        series = series.upper()
        # Height from series like "ALTO 80" or "110"
        height_match = re.search(r'(?:ALTO\s*)?(\d{2,3})', series)
        if height_match:
            height_val = int(height_match.group(1))
            dims["height"] = height_val * 10 if height_val < 300 else height_val
        
        # Depth from series like "FONDO 33" or "FONDO 58"
        depth_match = re.search(r'FONDO\s*(\d{2,3})', series)
        if depth_match:
            depth_val = int(depth_match.group(1))
            dims["depth"] = depth_val * 10 if depth_val < 100 else depth_val
    
    return dims

async def process_page(page_path: str, page_num: int) -> dict:
    """Process a single catalog page using Gemini Vision"""
    try:
        print(f"\n📄 Procesando página {page_num}: {page_path}")
        
        # Create image file content
        image_file = FileContentWithMimeType(
            file_path=page_path,
            mime_type="image/jpeg"
        )
        
        # Create chat instance with Gemini model
        chat = LlmChat(
            api_key=EMERGENT_KEY,
            session_id=f"catalog-import-{page_num}",
            system_message="Eres un asistente que extrae información de productos de catálogos de muebles de cocina. Respondes siempre en JSON válido."
        )
        
        # Create message with image
        user_message = UserMessage(
            text=EXTRACTION_PROMPT,
            files=[image_file]
        )
        
        # Get response with timeout
        response = await asyncio.wait_for(
            chat.send_message(user_message, model="gemini"),
            timeout=90
        )
        
        # Parse response
        response_text = response.text.strip()
        
        # Remove markdown code block if present
        if response_text.startswith('```'):
            lines = response_text.split('\n')
            response_text = '\n'.join(lines[1:-1] if lines[-1] == '```' else lines[1:])
        
        # Parse JSON
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError:
            # Try to find JSON in response
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                data = json.loads(json_match.group())
            else:
                print(f"  ❌ Error parsing JSON from page {page_num}")
                return {"products": [], "pageInfo": "Error parsing", "page_num": page_num}
        
        products = data.get("products", [])
        print(f"  ✓ Encontrados {len(products)} productos")
        
        return {
            "products": products,
            "pageInfo": data.get("pageInfo", ""),
            "page_num": page_num
        }
        
    except asyncio.TimeoutError:
        print(f"  ⏰ Timeout en página {page_num}")
        return {"products": [], "pageInfo": "Timeout", "page_num": page_num}
    except Exception as e:
        print(f"  ❌ Error en página {page_num}: {str(e)}")
        return {"products": [], "pageInfo": str(e), "page_num": page_num}

async def save_products(products: list, page_num: int) -> int:
    """Save products to MongoDB"""
    saved = 0
    for product in products:
        try:
            # Generate unique ID
            product_id = str(uuid.uuid4())[:8]
            
            # Get reference/code
            code = product.get("reference", "")
            if not code:
                continue
            
            # Extract dimensions
            series = product.get("series", "")
            dims = extract_dimensions_from_code(code, series)
            
            # Override with extracted values if available
            width = product.get("width", dims["width"]) or dims["width"]
            height = product.get("height", dims["height"]) or dims["height"]
            depth = product.get("depth", dims["depth"]) or dims["depth"]
            
            # Create product document
            doc = {
                "id": product_id,
                "code": code,
                "reference": code,
                "name": product.get("name", code),
                "category": product.get("category", "OTROS"),
                "series": series,
                "programa": product.get("programa", "ESTÁNDAR"),
                "width": width,
                "height": height,
                "depth": depth,
                "points": product.get("points", 0),
                "zonePoints": product.get("zonePoints", {}),
                "module": "montada",
                "page_number": page_num
            }
            
            # Check for duplicates
            existing = await db.products.find_one({"code": code})
            if existing:
                # Update existing
                await db.products.update_one(
                    {"code": code},
                    {"$set": doc}
                )
                print(f"    ↻ Actualizado: {code}")
            else:
                # Insert new
                await db.products.insert_one(doc)
                print(f"    + Nuevo: {code}")
            
            saved += 1
            
        except Exception as e:
            print(f"    ❌ Error guardando producto: {str(e)}")
    
    return saved

async def process_batch(start_page: int, end_page: int):
    """Process a batch of pages"""
    print(f"\n{'='*60}")
    print(f"PROCESANDO PÁGINAS {start_page} - {end_page}")
    print(f"{'='*60}")
    
    total_products = 0
    failed_pages = []
    
    for page_num in range(start_page, end_page + 1):
        page_path = f"{PDF_PAGES_DIR}/page_{page_num}.jpg"
        
        if not os.path.exists(page_path):
            print(f"⚠️  Página {page_num} no encontrada")
            continue
        
        # Process page
        result = await process_page(page_path, page_num)
        products = result.get("products", [])
        
        if products:
            saved = await save_products(products, page_num)
            total_products += saved
        else:
            if "Error" in result.get("pageInfo", "") or "Timeout" in result.get("pageInfo", ""):
                failed_pages.append(page_num)
        
        # Small delay between pages
        await asyncio.sleep(1)
    
    print(f"\n{'='*60}")
    print(f"RESUMEN: {total_products} productos guardados")
    if failed_pages:
        print(f"⚠️  Páginas fallidas: {failed_pages}")
    print(f"{'='*60}")
    
    return {"total": total_products, "failed": failed_pages}

async def main():
    """Main entry point"""
    # Check arguments
    if len(sys.argv) < 3:
        print("Uso: python import_pages_301_400.py <start_page> <end_page>")
        print("Ejemplo: python import_pages_301_400.py 301 310")
        return
    
    start_page = int(sys.argv[1])
    end_page = int(sys.argv[2])
    
    # Validate range
    if start_page < 301 or end_page > 400:
        print("Error: Las páginas deben estar entre 301 y 400")
        return
    
    # Get initial count
    initial_count = await db.products.count_documents({})
    print(f"\n📊 Productos en BD antes: {initial_count}")
    
    # Process batch
    result = await process_batch(start_page, end_page)
    
    # Get final count
    final_count = await db.products.count_documents({})
    print(f"\n📊 Productos en BD después: {final_count}")
    print(f"📈 Nuevos productos: {final_count - initial_count}")

if __name__ == "__main__":
    asyncio.run(main())
