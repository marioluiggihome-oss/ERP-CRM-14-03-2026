"""
Digitalizador Router - Reconocimiento Óptico de Presupuestos
Endpoints para digitalización de borradores con IA y gestión de expedientes
"""
from fastapi import APIRouter, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import uuid
import logging
import os
import json
import re

from models.schemas import (
    DigitalizadorMatchedProduct, DigitalizadorLine, DigitalizadorRequest, DigitalizadorResponse,
    DigitalizadorExportRequest, DigitalizadorSaveRequest, DigitalizadorHistoryItem,
    ExpedienteRequest, DigitalizadorToProjectRequest
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["digitalizador"])

# Database connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'luiggi_home')
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]


# ============================================
# EXPEDIENTE NUMBER GENERATION
# ============================================

@router.post("/digitalizador/generate-exp-number")
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
        result = await db.counters.find_one_and_update(
            {"_id": counter_id},
            {"$inc": {"seq": 1}},
            upsert=True,
            return_document=True
        )
        
        seq_number = result["seq"]
        
        # Format: {PREFIX}-YYYY-NNN (with padding for 3 digits, auto-expands if > 999)
        if seq_number < 1000:
            exp_number = f"{prefix}-{current_year}-{seq_number:03d}"
        else:
            exp_number = f"{prefix}-{current_year}-{seq_number}"
        
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
        raise HTTPException(status_code=500, detail=f"Error generando numero de expediente: {str(e)}")


@router.get("/digitalizador/current-exp-sequence")
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
            "nextNumber": f"{prefix}-{current_year}-{current_seq + 1:03d}" if current_seq + 1 < 1000 else f"{prefix}-{current_year}-{current_seq + 1}"
        }
    except Exception as e:
        logger.error(f"Get current expediente sequence error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# DIGITALIZADOR SAVE/HISTORY
# ============================================

@router.post("/digitalizador/save")
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
        
        # Apply markup if exists
        if request.globalMarkup > 0:
            total_neto = total_neto * (1 + request.globalMarkup / 100)
        
        total_con_iva = total_neto * (1 + request.ivaRate / 100)
        
        # Generate expediente number if not provided
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
        
        # Check if expediente number already exists
        existing = await db.digitalizador_history.find_one({"expNumber": exp_number})
        if existing:
            raise HTTPException(status_code=400, detail=f"El numero de expediente {exp_number} ya existe. Por favor genera uno nuevo.")
        
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Save digitalizador budget error: {e}")
        raise HTTPException(status_code=500, detail=f"Error guardando presupuesto: {str(e)}")


@router.get("/digitalizador/history")
async def get_digitalizador_history(userId: str = None, search: str = None, limit: int = 50):
    """Get digitalizador history, optionally filtered by user or search term"""
    try:
        query = {}
        
        if userId:
            query["userId"] = userId
        
        if search:
            query["$or"] = [
                {"expNumber": {"$regex": search, "$options": "i"}},
                {"projectName": {"$regex": search, "$options": "i"}},
                {"customerName": {"$regex": search, "$options": "i"}}
            ]
        
        cursor = db.digitalizador_history.find(query).sort("createdAt", -1).limit(limit)
        history = []
        
        async for item in cursor:
            item.pop('_id', None)
            history.append(item)
        
        return {"success": True, "history": history}
    except Exception as e:
        logger.error(f"Get digitalizador history error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/digitalizador/history/{item_id}")
async def get_digitalizador_item(item_id: str):
    """Get a specific digitalizador history item"""
    try:
        item = await db.digitalizador_history.find_one({"id": item_id})
        
        if not item:
            raise HTTPException(status_code=404, detail="Item no encontrado")
        
        item.pop('_id', None)
        return {"success": True, "item": item}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get digitalizador item error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/digitalizador/history/{item_id}")
async def delete_digitalizador_item(item_id: str):
    """Delete a digitalizador history item"""
    try:
        result = await db.digitalizador_history.delete_one({"id": item_id})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Item no encontrado")
        
        return {"success": True, "message": "Item eliminado"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete digitalizador item error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# SAVE TO PRESUPUESTOS (MAIN PROJECTS)
# ============================================

@router.post("/presupuestos")
async def save_digitalizador_to_presupuestos(request: DigitalizadorToProjectRequest):
    """
    Save a digitalizador budget to the main projects collection.
    This allows digitalized budgets to be managed alongside regular budgets.
    """
    try:
        # Convert digitalizador lines to project items format
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
        
        # Create the project/budget
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


# ============================================
# IA ANALYSIS
# ============================================

# Límite máximo de imagen: 10 MB (base64 ≈ 13.3MB de string)
MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10MB
MAX_BASE64_LENGTH = MAX_IMAGE_BYTES * 4 // 3  # ~13.3M chars
# Tope de páginas a analizar por PDF. Cada página es una llamada a la IA, así
# que un PDF enorme podría tardar tanto que la petición caduque (timeout). Se
# procesan hasta este número y se informa si el PDF tiene más.
MAX_PDF_PAGES = 25


@router.post("/digitalizador/analyze")
async def analyze_draft(request: DigitalizadorRequest):
    """
    Analyze a draft image using Gemini Vision to extract budget lines.
    Returns structured data with quantities, descriptions, and dimensions.
    """
    # Validar tamaño de imagen para evitar DoS
    if request.imageBase64 and len(request.imageBase64) > MAX_BASE64_LENGTH:
        raise HTTPException(status_code=413, detail=f"Imagen demasiado grande. Máximo {MAX_IMAGE_BYTES // 1024 // 1024}MB.")

    try:
        from services.llm_vision import analyze_image_with_gemini, is_vision_available
        
        if not is_vision_available():
            raise HTTPException(status_code=503, detail="Vision IA no configurada. Añade GEMINI_API_KEY en variables de entorno (https://aistudio.google.com/apikey)")
        
        # Prepare the prompt for Gemini Vision
        extraction_prompt = """Analiza esta imagen de un presupuesto o boceto de cocina/muebles.

IMPORTANTE - CONTEXTO DE MEDIDAS DE MUEBLES DE COCINA:
- Los muebles ALTOS suelen medir entre 30-90 cm de alto (tipico: 70-80 cm)
- Los muebles BAJOS suelen medir entre 70-90 cm de alto
- Las COLUMNAS y SEMICOLUMNAS miden entre 110-220 cm de alto (tipico: 200-220 cm)
- Los COSTADOS suelen medir entre 30-220 cm de alto segun el tipo de mueble
- El ANCHO tipico es 30-120 cm
- El FONDO tipico es 30-65 cm

REGLAS DE INTERPRETACION:
- Si ves "70x45" o "70 x 45", son centimetros (70cm x 45cm)
- Si ves "110" o "220" solos, probablemente son ALTURAS en centimetros (110cm, 220cm), NO 11cm o 22cm
- Si ves medidas como "35.5" o "69.8", son centimetros con decimales
- Las medidas escritas a mano pueden parecer que les falta un digito - usa el contexto para interpretar

Extrae TODAS las lineas que encuentres, incluyendo:
- Piezas de muebles con dimensiones (ej: "Costado 113 x 60", "Pieza 69.8 x 44.7")
- Referencias de productos (ej: "Factory 01", "HB514AER4")
- Cualquier articulo con medidas o descripciones
- Electrodomesticos con sus codigos y descripciones

Para cada linea encontrada, devuelve en formato JSON:
{
  "projectName": "nombre del proyecto o cliente si lo encuentras",
  "lines": [
    {
      "quantity": 1,
      "reference": "referencia o codigo si existe",
      "description": "descripcion completa del articulo incluyendo medidas CORRECTAS en centimetros",
      "price": 0,
      "discount": 0
    }
  ]
}

PRECIOS (MUY IMPORTANTE):
- Si el documento es un presupuesto/factura con columnas (PRECIO, DTOS/DTO%, TOTAL),
  extrae para cada linea:
  - "price": el PRECIO UNITARIO (columna PRECIO), como numero decimal con punto
    (ej: 187.46). NO el total de la linea, sino el precio por unidad.
  - "discount": el descuento de esa linea en % (columna DTOS o DTO%), como numero
    (ej: 40 para 40%). Si no hay descuento, pon 0.
- Respeta la fila: cada linea tiene su PRECIO, su DTOS y su TOTAL alineados; no
  mezcles valores de filas distintas. Si una fila no tiene descuento, el siguiente
  numero suele ser directamente el TOTAL (price = total en ese caso).
- Si es un boceto a mano sin precios, deja price=0 y discount=0.

IMPORTANTE:
- Incluye las medidas en la descripcion tal como aparecen (ej: "Costado 110 x 60")
- Si hay un nombre de cliente o proyecto, ponlo en projectName
- Responde SOLO con el JSON, sin texto adicional ni explicaciones"""

        # Determinar las imágenes a analizar. Si es un PDF, convertir TODAS las
        # páginas a PNG y analizar cada una (Gemini Vision procesa una imagen por
        # llamada). Si es una imagen normal, se usa tal cual.
        page_images = []
        try:
            from services.pdf_utils import is_pdf_base64, pdf_base64_to_png_base64
            raw_b64 = request.imageBase64 or ""
            stripped_b64 = raw_b64.split(",", 1)[1] if raw_b64.startswith("data:") else raw_b64
            is_pdf = ("pdf" in raw_b64[:40].lower()) or is_pdf_base64(stripped_b64)
            if is_pdf:
                page_images = pdf_base64_to_png_base64(stripped_b64, dpi=150, max_pages=None) or []
                logger.info(f"Digitalizador: PDF con {len(page_images)} página(s)")
        except Exception as e:
            logger.warning(f"Digitalizador: no se pudo convertir PDF multipágina: {e}")
            page_images = []
        if not page_images:
            page_images = [request.imageBase64]  # imagen normal o fallback

        # Tope de seguridad para no exceder el tiempo de la petición.
        total_pages = len(page_images)
        pages_truncated = total_pages > MAX_PDF_PAGES
        if pages_truncated:
            logger.warning(f"Digitalizador: PDF con {total_pages} páginas, se procesan las primeras {MAX_PDF_PAGES}")
            page_images = page_images[:MAX_PDF_PAGES]

        def _clean_json(text):
            t = text.strip() if isinstance(text, str) else str(text)
            if t.startswith("```"):
                t = t.split("```")[1]
                if t.startswith("json"):
                    t = t[4:]
            return t.strip()

        # Analizar cada página y JUNTAR las líneas de todas
        merged_lines = []
        project_name = ""
        response_text = ""
        for pimg in page_images:
            page_resp = await analyze_image_with_gemini(
                image_base64=pimg,
                prompt=extraction_prompt,
                session_id=f"digitalizador-{uuid.uuid4().hex[:8]}",
                model="gemini-2.0-flash",
            )
            response_text = _clean_json(page_resp)
            try:
                page_parsed = json.loads(response_text)
            except json.JSONDecodeError:
                m = re.search(r'\{[\s\S]*\}', response_text)
                if not m:
                    continue
                page_parsed = json.loads(m.group())
            if not project_name:
                project_name = str(page_parsed.get("projectName") or "")
            merged_lines.extend(page_parsed.get("lines", []) or [])

        # Try to parse JSON from response
        try:
            parsed = {"projectName": project_name, "lines": merged_lines}
            
            # Helper function for fuzzy search in catalog
            async def search_catalog_fuzzy(search_text: str, limit: int = 3, library: str = "ZC"):
                """Search products by reference or description using fuzzy matching"""
                if not search_text or len(search_text) < 2:
                    return []
                
                search_upper = search_text.upper().strip()
                search_words = search_upper.split()
                
                matches = []
                
                # Filter by library
                base_filter = {"library": library}
                
                # Search by exact code match first
                exact_query = {**base_filter, "code": search_upper}
                exact_match = await db.products.find_one(
                    exact_query,
                    {"_id": 0, "id": 1, "code": 1, "name": 1, "points": 1, "zonePoints": 1}
                )
                if exact_match:
                    price = exact_match.get("points", 0) or 0
                    if exact_match.get("zonePoints"):
                        if library == "MV":
                            price = exact_match["zonePoints"].get("T1", price)
                        else:
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
                    query = {"$and": [base_filter, {"$or": regex_patterns}]}
                    cursor = db.products.find(query, {"_id": 0, "id": 1, "code": 1, "name": 1, "points": 1, "zonePoints": 1, "library": 1}).limit(limit * 3)
                    products = await cursor.to_list(limit * 3)
                    
                    for p in products:
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
                        
                        if score > 0.2:
                            price = p.get("points", 0) or 0
                            if p.get("zonePoints"):
                                if library == "MV":
                                    price = p["zonePoints"].get("T1", price)
                                else:
                                    price = p["zonePoints"].get("Z1", price)
                            matches.append(DigitalizadorMatchedProduct(
                                id=p.get("id", ""),
                                code=p.get("code", ""),
                                name=p.get("name", ""),
                                price=float(price),
                                score=score
                            ))
                    
                    matches.sort(key=lambda x: x.score, reverse=True)
                    return matches[:limit]
                
                return []
            
            # Build response lines with catalog matching
            active_library = request.library or "ZC"
            
            extracted_lines = []
            for idx, line in enumerate(parsed.get("lines", [])):
                reference = str(line.get("reference") or "")
                description = str(line.get("description") or "")
                
                # Search for matching products
                search_text = reference if reference else description
                matched_products = await search_catalog_fuzzy(search_text, library=active_library)
                
                if not matched_products and description:
                    matched_products = await search_catalog_fuzzy(description, library=active_library)
                
                # Precio y descuento vienen del PDF/imagen (no del catálogo, ya que
                # los códigos de proveedor no están en el catálogo del usuario).
                pdf_price = float(line.get("price") or 0)
                pdf_discount = float(line.get("discount") or 0)

                extracted_lines.append(DigitalizadorLine(
                    id=f"LINE-{uuid.uuid4().hex[:8]}",
                    quantity=int(line.get("quantity") or 1),
                    reference=reference,
                    description=description,
                    price=pdf_price,
                    discount=pdf_discount,
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


# ============================================
# CATALOG SEARCH
# ============================================

@router.get("/digitalizador/search-catalog")
async def search_digitalizador_catalog(q: str, limit: int = 5, library: str = "ZC"):
    """
    Search product catalog for digitalizador autocomplete.
    Returns matching products with scores.
    """
    try:
        if not q or len(q) < 2:
            return {"products": []}
        
        search_upper = q.upper().strip()
        search_words = search_upper.split()
        
        results = []
        
        # Filter by library
        base_filter = {"library": library}
        
        # First try exact code match
        exact_query = {**base_filter, "code": search_upper}
        exact = await db.products.find_one(exact_query, {"_id": 0})
        if exact:
            price = exact.get("points", 0) or 0
            if exact.get("zonePoints"):
                if library == "MV":
                    price = exact["zonePoints"].get("T1", price)
                else:
                    price = exact["zonePoints"].get("Z1", price)
            return {"products": [{
                "id": exact.get("id", ""),
                "code": exact.get("code", ""),
                "name": exact.get("name", ""),
                "category": exact.get("category", ""),
                "price": float(price),
                "score": 1.0
            }]}
        
        # Search by partial matches
        regex_patterns = [{"code": {"$regex": word, "$options": "i"}} for word in search_words if len(word) >= 2]
        regex_patterns.extend([{"name": {"$regex": word, "$options": "i"}} for word in search_words if len(word) >= 2])
        
        if regex_patterns:
            query = {"$and": [base_filter, {"$or": regex_patterns}]}
            cursor = db.products.find(query, {"_id": 0}).limit(limit * 5)
            products = await cursor.to_list(limit * 5)
            
            for p in products:
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
                        if library == "MV":
                            price = p["zonePoints"].get("T1", price)
                        else:
                            price = p["zonePoints"].get("Z1", price)
                    results.append({
                        "id": p.get("id", ""),
                        "code": p.get("code", ""),
                        "name": p.get("name", ""),
                        "category": p.get("category", ""),
                        "price": float(price),
                        "score": score
                    })
        
        results.sort(key=lambda x: x["score"], reverse=True)
        return {"products": results[:limit]}
        
    except Exception as e:
        logger.error(f"Catalog search error: {e}")
        return {"products": [], "error": str(e)}


# ============================================
# EXPORT CSV
# ============================================

@router.post("/digitalizador/export-csv")
async def export_digitalizador_csv(request: DigitalizadorExportRequest):
    """
    Export digitalizador lines to CSV format for cutting machine.
    Format: "CODE";THICKNESS;"DESCRIPTION";WIDTH;HEIGHT;ORIENTATION;0;0;"CODE"
    """
    try:
        csv_lines = []
        
        for line in request.lines:
            # Try to extract dimensions from description
            dim_match = re.search(r'(\d+(?:\.\d+)?)\s*[xX×]\s*(\d+(?:\.\d+)?)', line.description)
            
            if dim_match:
                width = int(float(dim_match.group(1)))
                height = int(float(dim_match.group(2)))
            else:
                width = 0
                height = 0
            
            # Build CSV line
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
