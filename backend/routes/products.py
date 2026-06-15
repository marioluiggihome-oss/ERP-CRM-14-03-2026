"""
Router de PRODUCTOS — extraído tal cual de server.py (endpoints vivos, mismo orden de rutas).
"""
import io
import os
import base64
import xlsxwriter
from io import BytesIO
import re
import csv
import uuid
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends, Request, Response, File, UploadFile, Query
from fastapi.responses import StreamingResponse

from config import db
from services.jwt_service import (
    get_current_user, require_auth, require_admin, ADMIN_ROLE_FLAGS,
    create_access_token, create_refresh_token, verify_refresh_token,
)

try:
    from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent
except Exception:
    LlmChat = None
    UserMessage = None
    ImageContent = None

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Products"])

from models.schemas import ProductModel, ProductCreate, ZonePoints


@router.get("/products")
async def get_products(module: Optional[str] = None, library: Optional[str] = None, search: Optional[str] = None, limit: Optional[int] = None):
    """Obtener productos, filtrados por módulo, biblioteca y búsqueda de texto"""
    import re as _re
    query = {}
    if module:
        query["module"] = module
    if library:
        query["library"] = library.upper()
    if search and len(search) >= 2:
        escaped = _re.escape(search)
        query["$or"] = [
            {"code": {"$regex": escaped, "$options": "i"}},
            {"name": {"$regex": escaped, "$options": "i"}},
            {"description": {"$regex": escaped, "$options": "i"}},
        ]
    max_results = min(limit, 200) if limit else (50 if search else 10000)
    products = await db.products.find(query, {"_id": 0}).limit(max_results).to_list(max_results)
    
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

@router.get("/products/export/excel")
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


@router.get("/products/export/pdf")
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


@router.get("/products/export/library/{library_code}")
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


@router.get("/products/{product_id}", response_model=ProductModel)
async def get_product(product_id: str):
    """Obtener un producto por ID"""
    product = await db.products.find_one({"id": product_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product

@router.post("/products", response_model=ProductModel)
async def create_product(product: ProductCreate, current_user: dict = Depends(require_auth)):
    """Crear un nuevo producto"""
    product_obj = ProductModel(**product.model_dump())
    product_obj.code = product_obj.code.upper()
    
    # Set points from Z1 if zonePoints exists
    if product_obj.zonePoints:
        product_obj.points = product_obj.zonePoints.Z1
    
    await db.products.insert_one(product_obj.model_dump())
    return product_obj

@router.post("/products/bulk")
async def create_products_bulk(products: List[dict], current_user: dict = Depends(require_admin)):
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
                "manufacturer": str(product_data.get("manufacturer", "ZC")),
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

@router.post("/products/bulk-upsert")
async def bulk_upsert_products(data: dict, current_user: dict = Depends(require_admin)):
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
                    "manufacturer": str(product_data.get("manufacturer", "MV" if library == "MV" else "ZC")),
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


@router.put("/products/{product_id}", response_model=ProductModel)
async def update_product(product_id: str, product: ProductCreate, current_user: dict = Depends(require_auth)):
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

@router.patch("/products/{product_id}/zone-points")
async def update_product_zone_points(product_id: str, zone_points: dict, current_user: dict = Depends(require_auth)):
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

@router.delete("/products/{product_id}")
async def delete_product(product_id: str, current_user: dict = Depends(require_auth)):
    """Eliminar un producto"""
    result = await db.products.delete_one({"id": product_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return {"message": "Producto eliminado"}

@router.post("/catalog/extract-products")
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
            model="gemini/gemini-2.5-flash",
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

@router.post("/products/fix-heights")
async def fix_product_heights(current_user: dict = Depends(require_admin)):
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

@router.post("/products/fix-semicolumna-names")
async def fix_semicolumna_names(current_user: dict = Depends(require_admin)):
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

@router.post("/products/fix-names")
async def fix_product_names(current_user: dict = Depends(require_admin)):
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

@router.post("/products/fix-costados-depth")
async def fix_costados_depth(current_user: dict = Depends(require_admin)):
    """
    Corregir el grosor (depth/fondo) de paneles planos (costados, regletas,
    zócalos, techos, laterales, cornisas, estantes, etc.).
    Estos elementos son paneles de 18mm/cm de grueso, no 33 ni 58.
    Esos valores corresponden al fondo de los muebles ALTOS/BAJOS y se
    copiaron por error al importar el catálogo.
    """
    categories = [
        "COSTADOS", "COSTADO", "COSTADOS COLOR", "COSTADOS_COLOR", "COSTADOS MELAMINA", "COSTADOS_MELAMINA",
        "LATERAL", "LATERALES", "LATERAL COLOR", "LATERALES COLOR", "LATERALES_COLOR",
        "REGLETA", "REGLETAS", "REGLETA COLOR", "REGLETA MELAMINA",
        "ZOCALOS", "ZOCALO",
        "TECHO", "TECHO COLOR",
        "CORNISAS", "CORNISA",
        "ESTANTES", "ESTANTE",
        "BALDA AEREA", "BALDA",
        "ELEMENTOS", "ELEMENTOS LINEALES",
    ]

    result_depth = await db.products.update_many(
        {"category": {"$in": categories}, "depth": {"$in": [33, 33.0, 58, 58.0]}},
        {"$set": {"depth": 18}}
    )
    result_fondo = await db.products.update_many(
        {"category": {"$in": categories}, "fondo": {"$in": [33, 33.0, 58, 58.0]}},
        {"$set": {"fondo": 18}}
    )

    fixed_count = max(result_depth.modified_count, result_fondo.modified_count)

    return {
        "success": True,
        "fixed_count": fixed_count,
        "message": f"Se corrigió el grueso de {fixed_count} paneles (costados, regletas, zócalos, etc.) a 18cm"
    }

@router.delete("/products/bulk/delete")
async def delete_products_bulk(product_ids: List[str], current_user: dict = Depends(require_admin)):
    """Eliminar múltiples productos"""
    result = await db.products.delete_many({"id": {"$in": product_ids}})
    return {"message": f"{result.deleted_count} productos eliminados"}

# ============================================
# MATERIAL ENDPOINTS
# ============================================

# ============================================
# PROJECT/BUDGET ENDPOINTS
# ============================================
