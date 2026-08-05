"""
Digitalizador Router - Reconocimiento Óptico de Presupuestos
Endpoints para digitalización de borradores con IA y gestión de expedientes
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
import uuid
import logging
import os
import json
import re

from services.db_client import get_db as _get_db
from models.schemas import (
    DigitalizadorMatchedProduct, DigitalizadorLine, DigitalizadorRequest, DigitalizadorResponse,
    DigitalizadorExportRequest, DigitalizadorSaveRequest, DigitalizadorHistoryItem,
    ExpedienteRequest, DigitalizadorToProjectRequest
)

logger = logging.getLogger(__name__)

# Seguridad: el modulo no exigia ningun token; presupuestos digitalizados y
# expedientes quedaban abiertos a cualquiera que conociera la URL.
try:
    from services.jwt_service import require_module_access
    _DIGITALIZADOR_DEPS = [Depends(require_module_access("canUseDigitalizador"))]
except Exception:  # pragma: no cover - fallback si no hay jwt_service
    _DIGITALIZADOR_DEPS = []

router = APIRouter(tags=["digitalizador"], dependencies=_DIGITALIZADOR_DEPS)

# Database connection


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
        result = await _get_db().counters.find_one_and_update(
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
        
        counter = await _get_db().counters.find_one({"_id": counter_id})
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
            net_line = line_price * (1 - line_discount / 100)
            # Respetar lineMarkup por línea: si está definido (incluso 0), usarlo; si no, usar globalMarkup
            effective_markup = line.lineMarkup if line.lineMarkup is not None else request.globalMarkup
            if effective_markup > 0:
                net_line = net_line * (1 + effective_markup / 100)
            total_neto += net_line
        
        total_con_iva = total_neto * (1 + request.ivaRate / 100)
        
        # Generate expediente number if not provided
        exp_number = request.expNumber
        if not exp_number:
            current_year = datetime.now().year
            result = await _get_db().counters.find_one_and_update(
                {"_id": f"expediente_{current_year}"},
                {"$inc": {"seq": 1}},
                upsert=True,
                return_document=True
            )
            seq = result["seq"]
            exp_number = f"EXP-{current_year}-{seq:03d}" if seq < 1000 else f"EXP-{current_year}-{seq}"
        
        # Si el expediente ya existe, se ACTUALIZA (re-guardar tras retocar la
        # cabecera o las líneas), en vez de rechazarlo.
        existing = await _get_db().digitalizador_history.find_one({"expNumber": exp_number})

        # Create history item
        history_item = {
            "id": (existing or {}).get("id") or f"digi-{uuid.uuid4().hex[:12]}",
            "expNumber": exp_number,
            "projectName": request.projectName,
            "customerName": request.customerName,
            "customerCode": request.customerCode,
            "customerEmail": request.customerEmail,
            "customerPhone": request.customerPhone,
            "acabado": request.acabado,
            "armazon": request.armazon,
            "costados": request.costados,
            "labelAcabado": request.labelAcabado,
            "labelArmazon": request.labelArmazon,
            "labelCostados": request.labelCostados,
            "validez": request.validez,
            "lines": [line.model_dump() for line in request.lines],
            "globalDiscount": request.globalDiscount,
            "globalMarkup": request.globalMarkup,
            "ivaRate": request.ivaRate,
            "documentTitle": request.documentTitle,
            "isValorado": request.isValorado,
            "showTotals": request.showTotals,
            "totalBruto": round(total_bruto, 2),
            "totalNeto": round(total_neto, 2),
            "totalConIva": round(total_con_iva, 2),
            "userId": request.userId,
            "createdAt": (existing or {}).get("createdAt") or datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat(),
        }

        if existing:
            await _get_db().digitalizador_history.update_one({"expNumber": exp_number}, {"$set": history_item})
        else:
            await _get_db().digitalizador_history.insert_one(history_item)
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
            _s = re.escape(search)
            query["$or"] = [
                {"expNumber": {"$regex": _s, "$options": "i"}},
                {"projectName": {"$regex": _s, "$options": "i"}},
                {"customerName": {"$regex": _s, "$options": "i"}}
            ]
        
        cursor = _get_db().digitalizador_history.find(query).sort("createdAt", -1).limit(limit)
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
        item = await _get_db().digitalizador_history.find_one({"id": item_id})
        
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
        result = await _get_db().digitalizador_history.delete_one({"id": item_id})
        
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
        
        await _get_db().projects.insert_one(project_data)
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
            raise HTTPException(status_code=503, detail="Vision IA no configurada. Falta la clave del motor de IA (contacta con el administrador).")
        
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

PRIMERO, CLASIFICA EL DOCUMENTO (elige uno):
  (A) PRESUPUESTO/FACTURA IMPRESO: tiene tabla con columnas (referencia, descripcion, precio, dto, total).
  (B) BOCETO A MANO: dibujo/croquis con medidas escritas a mano.
  (C) DISENO / ALZADO / PLANO DE COCINA: dibujo tecnico o render (2D o 3D) de la cocina, con los muebles
      dibujados en su sitio (vista de alzado de pared, planta, o perspectiva del diseno montado).

DETECCION DE MUEBLES EN DISENOS/ALZADOS/PLANOS (tipo C) — MUY IMPORTANTE:
- Recorre la cocina de IZQUIERDA a DERECHA y por FILAS (primero los muebles BAJOS, luego ALTOS, luego
  COLUMNAS), y crea UNA LINEA POR CADA MODULO/MUEBLE que veas dibujado. No agrupes varios modulos en una
  sola linea aunque sean iguales: si hay 3 bajos de 60, saca 3 lineas (o 1 linea con quantity 3 si son
  identicos y estan juntos).
- Identifica y nombra el TIPO de cada modulo. Tipos habituales de cocina:
  · Muebles BAJOS: bajo cajones, bajo puertas, bajo fregadero, bajo encimera, bajo rincon, bajo horno,
    bajo campana, botellero, bajo esquinero.
  · Muebles ALTOS: alto puertas, alto escurreplatos, alto campana, alto rincon, alto vitrina, alto abatible.
  · COLUMNAS y SEMICOLUMNAS: columna horno+microondas, columna despensero, columna frigorifico, columna escobero.
  · Complementos: encimera, peninsula, isla, zocalo, copete, costados/laterales vistos, remates, baldas.
  · ELECTRODOMESTICOS integrados o vistos: campana, placa, horno, microondas, lavavajillas, frigorifico,
    fregadero, grifo, vinoteca — sacalos tambien como lineas.
- Para cada modulo, pon en "description" el TIPO + el ANCHO (y alto si aparece), ej: "Mueble bajo 2 cajones 60",
  "Alto puertas 90 x 70", "Columna horno+micro 60 x 220". Si el ancho no esta rotulado, estimalo por
  proporcion con los muebles vecinos rotulados y marca la medida como aproximada (ej: "~45").
- Si el diseno lleva una LEYENDA, tabla de despiece o numeros de posicion junto a los muebles, usalos como
  fuente principal de tipos y medidas.
- No te dejes ningun modulo: cuenta las puertas/frentes y los tiradores para no saltarte muebles pequenos.
- No metas como muebles los elementos decorativos (plantas, cuadros, personas, texto de marca).

Extrae TODAS las lineas que encuentres, incluyendo:
- Piezas de muebles con dimensiones (ej: "Costado 113 x 60", "Pieza 69.8 x 44.7")
- Referencias de productos (ej: "Factory 01", "HB514AER4")
- Cualquier articulo con medidas o descripciones
- Electrodomesticos con sus codigos y descripciones

EXTRACCION COMPLETA (CRITICO para presupuestos impresos de varias paginas):
- Si el documento tiene articulos numerados de forma consecutiva en una columna
  '#' (por ejemplo del 1 al 55), extrae CADA numero de TODAS las paginas, sin
  saltarte ninguno y sin detenerte a la mitad. El JSON debe tener tantas lineas
  como numeros aparezcan.
- Une al campo "description" el texto tecnico que aparezca debajo de un articulo
  (ej: "Lados: 4C - Canto: BLANCO", "Mano: Izquierda"). Si ves "Mano: Izquierda/
  Derecha", inclúyelo en la descripcion.
- NO extraigas como articulos las filas de resumen/totales: "Total Lineas Bruto",
  "Base Imponible", "I.V.A.", "TOTAL DOCUMENTO", etc. Ignoralas.

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

        def _clean_json(text):
            t = text.strip() if isinstance(text, str) else str(text)
            if t.startswith("```"):
                t = t.split("```")[1]
                if t.startswith("json"):
                    t = t[4:]
            return t.strip()

        def _parse_json_loose(text):
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                m = re.search(r'\{[\s\S]*\}', text)
                try:
                    return json.loads(m.group()) if m else None
                except Exception:
                    return None

        # Detectar si es un PDF y, si es DIGITAL (tiene texto), extraer el texto de
        # TODAS las páginas y analizarlo como TEXTO. Es mucho más fiable que la
        # visión para tablas densas de varias páginas (el caso de los presupuestos
        # de proveedor). Si es escaneado/imagen, se usa visión por página.
        raw_b64 = request.imageBase64 or ""
        stripped_b64 = raw_b64.split(",", 1)[1] if raw_b64.startswith("data:") else raw_b64
        is_pdf = False
        pdf_text = ""
        try:
            from services.pdf_utils import is_pdf_base64, pdf_base64_to_text, pdf_base64_to_png_base64
            is_pdf = ("pdf" in raw_b64[:40].lower()) or is_pdf_base64(stripped_b64)
            if is_pdf:
                pdf_text = pdf_base64_to_text(stripped_b64) or ""
        except Exception as e:
            logger.warning(f"Digitalizador: detección/lectura de PDF: {e}")

        parsed = None

        if is_pdf and len(pdf_text.strip()) >= 100:
            # --- PDF DIGITAL: analizar TODO el texto (todas las páginas) de una vez ---
            from services.llm_vision import chat_with_gemini
            logger.info(f"Digitalizador: PDF de texto ({len(pdf_text)} chars) → modo texto")
            text_prompt = (
                extraction_prompt
                + "\n\nTEXTO COMPLETO DEL DOCUMENTO (incluye TODAS las páginas, "
                  "extrae las líneas de TODAS ellas):\n\n"
                + pdf_text[:60000]
            )
            try:
                resp = await chat_with_gemini(
                    prompt=text_prompt,
                    system_message="Eres un experto extrayendo líneas de presupuestos/facturas de muebles.",
                    model="gemini-2.5-flash",
                )
                parsed = _parse_json_loose(_clean_json(resp))
            except Exception as e:
                logger.warning(f"Digitalizador: fallo modo texto, se usará visión: {e}")
                parsed = None

        if parsed is None:
            # --- VISIÓN: imagen normal o PDF escaneado (sin capa de texto) ---
            page_images = []
            try:
                if is_pdf:
                    page_images = pdf_base64_to_png_base64(stripped_b64, dpi=150, max_pages=MAX_PDF_PAGES) or []
                    logger.info(f"Digitalizador: PDF escaneado, {len(page_images)} página(s) por visión")
            except Exception as e:
                logger.warning(f"Digitalizador: conversión PDF→imagen: {e}")
            if not page_images:
                page_images = [request.imageBase64]  # imagen normal o fallback

            merged_lines = []
            project_name = ""
            vision_error = None
            for pimg in page_images:
                try:
                    page_resp = await analyze_image_with_gemini(
                        image_base64=pimg,
                        prompt=extraction_prompt,
                        session_id=f"digitalizador-{uuid.uuid4().hex[:8]}",
                        model="gemini-2.5-flash",
                    )
                except Exception as e:
                    # Un fallo en una página (timeout, cuota IA…) no debe tumbar
                    # todo el análisis: se registra y se sigue con las demás.
                    vision_error = str(e)
                    logger.warning(f"Digitalizador: fallo IA en una página: {e}")
                    continue
                pp = _parse_json_loose(_clean_json(page_resp))
                if not pp:
                    continue
                if not project_name:
                    project_name = str(pp.get("projectName") or "")
                merged_lines.extend(pp.get("lines", []) or [])
            parsed = {"projectName": project_name, "lines": merged_lines}
            # Si no se obtuvo nada y hubo error de IA, devolver mensaje claro
            # (en vez de un 500 genérico "Error al analizar la imagen").
            if not merged_lines and vision_error:
                return DigitalizadorResponse(
                    success=False, projectName="", lines=[], rawText="",
                    error=f"La IA no pudo procesar el documento: {vision_error}"
                )

        # Texto crudo para depuración/registro (rawText de la respuesta).
        try:
            response_text = json.dumps(parsed, ensure_ascii=False)[:4000]
        except Exception:
            response_text = ""

        # Construir respuesta con emparejamiento de catálogo
        try:
            
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
                exact_match = await _get_db().products.find_one(
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
                regex_patterns = [{"code": {"$regex": re.escape(word), "$options": "i"}} for word in search_words if len(word) >= 3]
                regex_patterns.extend([{"name": {"$regex": re.escape(word), "$options": "i"}} for word in search_words if len(word) >= 3])
                
                if regex_patterns:
                    query = {"$and": [base_filter, {"$or": regex_patterns}]}
                    cursor = _get_db().products.find(query, {"_id": 0, "id": 1, "code": 1, "name": 1, "points": 1, "zonePoints": 1, "library": 1}).limit(limit * 3)
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
        # Devolver el motivo en la respuesta (success=False) en vez de un 500
        # genérico, para que el usuario vea qué ha fallado realmente.
        return DigitalizadorResponse(
            success=False, projectName="", lines=[], rawText="",
            error=f"Error analizando el documento: {str(e)}"
        )


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
        exact = await _get_db().products.find_one(exact_query, {"_id": 0})
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
        regex_patterns = [{"code": {"$regex": re.escape(word), "$options": "i"}} for word in search_words if len(word) >= 2]
        regex_patterns.extend([{"name": {"$regex": re.escape(word), "$options": "i"}} for word in search_words if len(word) >= 2])
        
        if regex_patterns:
            query = {"$and": [base_filter, {"$or": regex_patterns}]}
            cursor = _get_db().products.find(query, {"_id": 0}).limit(limit * 5)
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


# ============================================================================
# RESUMEN TOTALES — historial por usuario (guardar/listar/abrir/borrar)
# ============================================================================
@router.post("/resumen-totales")
async def save_resumen_totales(payload: dict):
    """Guarda (o actualiza) un Resumen Totales para consultarlo/modificarlo."""
    try:
        rid = (payload or {}).get("id") or f"rt-{uuid.uuid4().hex[:10]}"
        doc = {
            "id": rid,
            "userId": payload.get("userId") or "anonymous",
            "name": (payload.get("name") or "Resumen sin nombre").strip() or "Resumen sin nombre",
            "data": payload.get("data") or {},
            "updatedAt": datetime.now(timezone.utc).isoformat(),
        }
        existing = await _get_db().resumen_totales.find_one({"id": rid}, {"_id": 0, "createdAt": 1})
        doc["createdAt"] = (existing or {}).get("createdAt") or doc["updatedAt"]
        await _get_db().resumen_totales.update_one({"id": rid}, {"$set": doc}, upsert=True)
        return {"success": True, "id": rid, "name": doc["name"]}
    except Exception as e:
        logger.error(f"Save resumen-totales error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/resumen-totales")
async def list_resumen_totales(userId: str = None):
    """Lista los resúmenes guardados (por usuario)."""
    try:
        query = {"userId": userId} if userId else {}
        items = await _get_db().resumen_totales.find(query, {"_id": 0, "data": 0}).sort("updatedAt", -1).to_list(300)
        return {"success": True, "items": items}
    except Exception as e:
        logger.error(f"List resumen-totales error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/resumen-totales/{rid}")
async def get_resumen_totales(rid: str):
    item = await _get_db().resumen_totales.find_one({"id": rid}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Resumen no encontrado")
    return item


@router.delete("/resumen-totales/{rid}")
async def delete_resumen_totales(rid: str):
    await _get_db().resumen_totales.delete_one({"id": rid})
    return {"success": True}
