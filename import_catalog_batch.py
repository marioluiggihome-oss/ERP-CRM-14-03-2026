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
import base64
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient

# Import emergentintegrations
from emergentintegrations.llm.chat import LlmChat

# Configuration
MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = 'test_database'  # Usar la misma BD que el backend
PDF_PAGES_DIR = '/app/pdf_pages_235_300'
EMERGENT_KEY = 'sk-emergent-4A3Ed5d56521e792e1'

# Connect to MongoDB
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

EXTRACTION_PROMPT = """Analiza esta página del catálogo de muebles de cocina LUIGGI HOME.

Extrae TODOS los productos de la página en formato JSON. Para cada producto incluye:
- reference: Código de referencia completo (ej: "35A1P350", "22H2G1CB1P600", "FTE_CAJ_450")
- name: Nombre descriptivo completo del producto
- category: Categoría principal (ALTOS, BAJOS, COLUMNAS, SEMICOLUMNAS, FRENTES CAJÓN, ZÓCALOS, COSTADOS, ENCIMERAS, TIRADORES, HERRAJES, etc.)
- series: Serie específica del producto (ej: "ALTOS 70 FONDO 33", "BAJOS GOLA", "COLUMNAS 200")
- programa: Programa o acabado (ej: "GOLA", "ALUMINIO", "ESTÁNDAR", "Z1: Naturmel / Seda", etc.)
- width: Ancho en mm
- height: Alto en mm  
- depth: Profundidad/Fondo en mm
- visualType: Tipo visual para el icono (1P, 2P, 1C, 2C, VITRINA, HORNO, MICRO, FREGADERO, CAJONES, etc.)
- description: Descripción adicional si la hay (materiales, acabados, características)
- zonePoints: Objeto con TODOS los precios por zona como números (Z1, Z2, Z3, Z4, Z5, Z6, Z7, Z8, Z9, Z10, Z11, Z12)

IMPORTANTE sobre las zonas de precios:
- Extrae TODAS las columnas de precios que veas en la tabla
- Los valores deben ser números (sin símbolos de euro)
- Si una zona no tiene precio, no la incluyas

IMPORTANTE sobre el icono/visualType:
- Mira el dibujo/icono junto a cada producto
- 1P = 1 puerta, 2P = 2 puertas
- 1C = 1 cajón, 2C = 2 cajones, etc.
- VITRINA = con cristal
- Describe el tipo de mueble visualmente

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
      "series": "ALTOS 70 FONDO 33",
      "programa": "ESTÁNDAR",
      "width": 350,
      "height": 700,
      "depth": 330,
      "visualType": "1P",
      "description": "Mueble alto de 1 puerta con bisagras soft-close",
      "zonePoints": {"Z1": 85, "Z2": 90, "Z3": 95, "Z4": 100, "Z5": 105, "Z6": 110}
    }
  ],
  "pageInfo": "Descripción breve de qué contiene la página"
}
"""

async def process_page(page_path: str, page_num: int) -> dict:
    """Process a single catalog page using Gemini Vision"""
    try:
        print(f"\n📄 Procesando página {page_num}: {page_path}")
        
        # Import required classes
        from emergentintegrations.llm.chat import UserMessage, FileContentWithMimeType
        
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
        ).with_model("gemini", "gemini-2.0-flash")
        
        # Create user message with image
        user_msg = UserMessage(
            text=EXTRACTION_PROMPT,
            file_contents=[image_file]
        )
        
        # Get response (async)
        response_text = await chat.send_message(user_msg)
        response_text = response_text.strip()
        
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
        
        # Build product document with all fields
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
            "visualType": product.get("visualType", ""),
            "description": product.get("description", ""),
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



async def run_specific_pages(file_numbers: list, page_offset: int = 235):
    """Process specific page files that had errors
    
    Args:
        file_numbers: List of file numbers to process (e.g., [37, 38, 40])
        page_offset: Offset for page numbering
    """
    pages_dir = Path(PDF_PAGES_DIR)
    
    print(f"\n🔄 Reprocesando páginas específicas")
    print(f"   📁 Directorio: {PDF_PAGES_DIR}")
    print(f"   📄 Archivos: {file_numbers}")
    
    total_products = 0
    total_imported = 0
    errors = []
    
    for file_num in file_numbers:
        # Find the file
        page_file = pages_dir / f"page-{file_num:02d}.jpg"
        if not page_file.exists():
            page_file = pages_dir / f"page-{file_num}.jpg"
        
        if not page_file.exists():
            print(f"   ❌ Archivo no encontrado: page-{file_num}.jpg")
            continue
        
        page_num = page_offset + file_num - 1  # Real page number
        
        result = await process_page(str(page_file), page_num)
        
        if result["success"]:
            products = result["products"]
            total_products += len(products)
            
            for product in products:
                if await import_product(product, page_num):
                    total_imported += 1
        else:
            errors.append({"page": page_num, "file": page_file.name, "error": result.get("error")})
        
        await asyncio.sleep(1)
    
    # Summary
    print(f"\n✅ REPROCESAMIENTO COMPLETADO")
    print(f"   📄 Páginas procesadas: {len(file_numbers)}")
    print(f"   📦 Productos encontrados: {total_products}")
    print(f"   ✅ Productos importados: {total_imported}")
    print(f"   ❌ Errores: {len(errors)}")
    
    if errors:
        print(f"\n   Páginas con errores:")
        for err in errors:
            print(f"      - Página {err['page']} ({err['file']}): {err['error'][:50]}...")
    
    final_count = await db.products.count_documents({})
    print(f"\n   📊 Total productos en BD: {final_count}")


async def run_import(start_page: int = 1, end_page: int = None, batch_size: int = 5, page_offset: int = 235):
    """Run the catalog import process
    
    Args:
        start_page: Start file number (1-based)
        end_page: End file number
        batch_size: Number of pages per batch
        page_offset: Offset to calculate real page number (e.g., 235 for pages 235-300)
    """
    
    # Get list of page images
    pages_dir = Path(PDF_PAGES_DIR)
    page_files = sorted(pages_dir.glob("page-*.jpg"), key=lambda x: int(x.stem.split('-')[1]))
    
    if end_page is None:
        end_page = len(page_files)
    
    total_pages = end_page - start_page + 1
    print(f"\n🚀 Iniciando importación del catálogo")
    print(f"   📁 Directorio: {PDF_PAGES_DIR}")
    print(f"   📄 Archivos: {start_page} a {end_page} ({total_pages} páginas)")
    print(f"   📄 Páginas del catálogo: {page_offset + start_page - 1} a {page_offset + end_page - 1}")
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
            page_num = page_offset + idx  # Real page number in catalog
            
            result = await process_page(str(page_file), page_num)
            
            if result["success"]:
                products = result["products"]
                total_products += len(products)
                
                for product in products:
                    if await import_product(product, page_num):
                        total_imported += 1
            else:
                errors.append({"page": page_num, "file": page_file.name, "error": result.get("error")})
            
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
        for err in errors[:15]:
            print(f"      - Página {err['page']} ({err['file']}): {err['error'][:50]}...")
    
    final_count = await db.products.count_documents({})
    print(f"\n   📊 Total productos en BD: {final_count}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Import catalog pages')
    parser.add_argument('--start', type=int, default=1, help='Start file number (1-based)')
    parser.add_argument('--end', type=int, default=None, help='End file number')
    parser.add_argument('--batch', type=int, default=5, help='Batch size')
    parser.add_argument('--offset', type=int, default=235, help='Page number offset (e.g., 235 for pages 235-300)')
    parser.add_argument('--pages', type=str, default=None, help='Specific pages to process (comma-separated file numbers, e.g., "37,38,40")')
    
    args = parser.parse_args()
    
    if args.pages:
        # Process specific pages
        specific_pages = [int(p.strip()) for p in args.pages.split(',')]
        asyncio.run(run_specific_pages(specific_pages, args.offset))
    else:
        asyncio.run(run_import(args.start, args.end, args.batch, args.offset))
