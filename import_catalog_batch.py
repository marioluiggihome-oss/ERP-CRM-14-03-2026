#!/usr/bin/env python3
"""
Batch catalog import script for LUIGGI HOME
Processes PDF pages from the catalog using Gemini Vision to extract product data
"""

import os
import sys
import json
import asyncio
import uuid
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient

# Add emergentintegrations
sys.path.insert(0, '/app/backend')

from emergentintegrations.llm.chat import chat, Message

# Configuration
MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = 'luiggi_home'
PDF_PAGES_DIR = '/app/pdf_pages_95_234'
EMERGENT_KEY = 'sk-emergent-4A3Ed5d56521e792e1'

# Connect to MongoDB
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

EXTRACTION_PROMPT = """Analiza esta página del catálogo de muebles de cocina LUIGGI HOME.

Extrae TODOS los productos de la página en formato JSON. Para cada producto incluye:
- reference: Código de referencia (ej: "35A1P350", "22H2G1CB1P600")
- name: Nombre descriptivo completo
- category: Categoría (ALTOS, BAJOS, COLUMNAS, FRENTES CAJÓN, etc.)
- series: Serie del producto si se indica
- programa: Programa o línea (Z1, Z2, etc.) si se indica
- width: Ancho en mm si se indica
- height: Alto en mm si se indica  
- depth: Profundidad en mm si se indica
- zonePoints: Objeto con puntos por zona (Z1, Z2, Z3...) como números

Si hay tabla de precios por zonas, extrae los valores numéricos para cada zona.
Si no encuentras productos válidos, devuelve una lista vacía.

IMPORTANTE: Responde SOLO con el JSON, sin texto adicional ni markdown.

Formato de respuesta:
{
  "products": [
    {
      "reference": "35A1P350",
      "name": "Alto 1 puerta 35cm",
      "category": "ALTOS",
      "series": "ALTOS 35",
      "programa": "Z1: Naturmel",
      "width": 350,
      "height": 700,
      "depth": 330,
      "zonePoints": {"Z1": 85, "Z2": 90, "Z3": 95}
    }
  ],
  "pageInfo": "Descripción breve de qué contiene la página"
}
"""

async def process_page(page_path: str, page_num: int) -> dict:
    """Process a single catalog page using Gemini Vision"""
    try:
        print(f"\n📄 Procesando página {page_num}: {page_path}")
        
        # Read image as base64
        with open(page_path, 'rb') as f:
            import base64
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        # Use Gemini Vision via emergent
        messages = [
            Message(
                role="user",
                content=[
                    {"type": "text", "text": EXTRACTION_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_data}"
                        }
                    }
                ]
            )
        ]
        
        response = await chat(
            api_key=EMERGENT_KEY,
            model="gemini-2.0-flash",
            messages=messages,
            max_tokens=4000
        )
        
        response_text = response.content.strip()
        
        # Clean up response
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        response_text = response_text.strip()
        
        # Parse JSON
        data = json.loads(response_text)
        products = data.get("products", [])
        page_info = data.get("pageInfo", "")
        
        print(f"   ✅ Extraídos {len(products)} productos - {page_info[:60]}...")
        
        return {
            "success": True,
            "products": products,
            "page_num": page_num,
            "page_info": page_info
        }
        
    except json.JSONDecodeError as e:
        print(f"   ❌ Error parsing JSON: {e}")
        return {"success": False, "products": [], "page_num": page_num, "error": str(e)}
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return {"success": False, "products": [], "page_num": page_num, "error": str(e)}


async def import_product(product: dict, page_num: int) -> bool:
    """Import or update a single product in the database"""
    try:
        reference = product.get("reference", "").strip()
        if not reference or len(reference) < 3:
            return False
        
        # Build product document
        doc = {
            "id": f"prod-{uuid.uuid4().hex[:8]}",
            "code": reference.upper(),
            "reference": reference.upper(),
            "name": product.get("name", ""),
            "category": product.get("category", ""),
            "series": product.get("series", ""),
            "programa": product.get("programa", ""),
            "width": product.get("width"),
            "height": product.get("height"),
            "depth": product.get("depth"),
            "zonePoints": product.get("zonePoints", {}),
            "page_number": page_num,
            "module": "montada"
        }
        
        # Calculate points from Z1 or first available zone
        zone_points = doc.get("zonePoints", {})
        if zone_points:
            doc["points"] = zone_points.get("Z1", list(zone_points.values())[0] if zone_points else 0)
        
        # Update or insert
        result = await db.products.update_one(
            {"code": doc["code"]},
            {"$set": doc},
            upsert=True
        )
        
        return True
        
    except Exception as e:
        print(f"      Error importing {product.get('reference')}: {e}")
        return False


async def run_import(start_page: int = 1, end_page: int = None, batch_size: int = 5):
    """Run the catalog import process"""
    
    # Get list of page images
    pages_dir = Path(PDF_PAGES_DIR)
    page_files = sorted(pages_dir.glob("page-*.jpg"), key=lambda x: int(x.stem.split('-')[1]))
    
    if end_page is None:
        end_page = len(page_files)
    
    total_pages = end_page - start_page + 1
    print(f"\n🚀 Iniciando importación del catálogo")
    print(f"   📁 Directorio: {PDF_PAGES_DIR}")
    print(f"   📄 Páginas: {start_page} a {end_page} ({total_pages} páginas)")
    print(f"   📦 Batch size: {batch_size}")
    
    total_products = 0
    total_imported = 0
    errors = []
    
    # Process pages in batches
    page_indices = list(range(start_page - 1, end_page))
    
    for batch_start in range(0, len(page_indices), batch_size):
        batch = page_indices[batch_start:batch_start + batch_size]
        
        print(f"\n📦 Procesando batch {batch_start//batch_size + 1}/{(len(page_indices) + batch_size - 1)//batch_size}")
        
        for idx in batch:
            if idx >= len(page_files):
                continue
                
            page_file = page_files[idx]
            page_num = 95 + idx  # Pages in PDF start at 95
            
            result = await process_page(str(page_file), page_num)
            
            if result["success"]:
                products = result["products"]
                total_products += len(products)
                
                for product in products:
                    if await import_product(product, page_num):
                        total_imported += 1
            else:
                errors.append({"page": page_num, "error": result.get("error")})
            
            # Small delay to avoid rate limits
            await asyncio.sleep(1)
        
        # Status update
        current_count = await db.products.count_documents({})
        print(f"   📊 Productos en BD: {current_count}")
    
    # Final summary
    print(f"\n✅ IMPORTACIÓN COMPLETADA")
    print(f"   📄 Páginas procesadas: {total_pages}")
    print(f"   📦 Productos encontrados: {total_products}")
    print(f"   ✅ Productos importados: {total_imported}")
    print(f"   ❌ Errores: {len(errors)}")
    
    if errors:
        print(f"\n   Páginas con errores:")
        for err in errors[:10]:
            print(f"      - Página {err['page']}: {err['error'][:50]}...")
    
    final_count = await db.products.count_documents({})
    print(f"\n   📊 Total productos en BD: {final_count}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Import catalog pages')
    parser.add_argument('--start', type=int, default=1, help='Start page number')
    parser.add_argument('--end', type=int, default=None, help='End page number')
    parser.add_argument('--batch', type=int, default=5, help='Batch size')
    
    args = parser.parse_args()
    
    asyncio.run(run_import(args.start, args.end, args.batch))
