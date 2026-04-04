"""
Sistema de Cola de Procesamiento de Telemetría IA
Procesa imágenes de catálogos en segundo plano para evitar timeouts
"""
import asyncio
import uuid
import base64
from datetime import datetime, timezone
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging
import os
import json
import re

from motor.motor_asyncio import AsyncIOMotorClient
import google.generativeai as genai

logger = logging.getLogger(__name__)

# Conexión MongoDB
mongo_url = os.environ.get('MONGO_URL')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'luiggi_home')]

class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class TelemetryJob:
    job_id: str
    library: str  # MV o ZC
    module: str   # montada o despiece
    total_files: int
    processed_files: int = 0
    status: JobStatus = JobStatus.PENDING
    products_found: int = 0
    products_created: int = 0
    products_updated: int = 0
    errors: List[str] = field(default_factory=list)
    logs: List[Dict] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    detected_tariffs: List[str] = field(default_factory=list)
    current_file: str = ""

# Cola en memoria para jobs
jobs_queue: Dict[str, TelemetryJob] = {}
# Cola de archivos pendientes por job_id
files_queue: Dict[str, List[Dict]] = {}
# Flag para indicar si hay un worker procesando
processing_lock = asyncio.Lock()


async def create_telemetry_job(library: str, module: str, files_data: List[Dict]) -> str:
    """Crea un nuevo job de procesamiento y lo añade a la cola"""
    job_id = f"telemetry-{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()
    
    job = TelemetryJob(
        job_id=job_id,
        library=library,
        module=module,
        total_files=len(files_data),
        created_at=now,
        updated_at=now
    )
    
    jobs_queue[job_id] = job
    files_queue[job_id] = files_data
    
    # Iniciar procesamiento en background
    asyncio.create_task(process_job(job_id))
    
    logger.info(f"Created telemetry job {job_id} with {len(files_data)} files for library {library}")
    
    return job_id


async def get_job_status(job_id: str) -> Optional[Dict]:
    """Obtiene el estado actual de un job"""
    job = jobs_queue.get(job_id)
    if not job:
        return None
    
    return {
        "job_id": job.job_id,
        "library": job.library,
        "module": job.module,
        "status": job.status.value,
        "total_files": job.total_files,
        "processed_files": job.processed_files,
        "products_found": job.products_found,
        "products_created": job.products_created,
        "products_updated": job.products_updated,
        "errors": job.errors,
        "logs": job.logs[-20:],  # Últimos 20 logs
        "detected_tariffs": list(set(job.detected_tariffs)),
        "current_file": job.current_file,
        "progress_percent": round((job.processed_files / max(job.total_files, 1)) * 100, 1),
        "created_at": job.created_at,
        "updated_at": job.updated_at
    }


def add_job_log(job: TelemetryJob, log_type: str, message: str):
    """Añade un log al job"""
    job.logs.append({
        "type": log_type,
        "msg": message,
        "time": datetime.now(timezone.utc).strftime("%H:%M:%S")
    })
    job.updated_at = datetime.now(timezone.utc).isoformat()


async def process_job(job_id: str):
    """Procesa un job de telemetría en segundo plano"""
    job = jobs_queue.get(job_id)
    if not job:
        return
    
    job.status = JobStatus.PROCESSING
    add_job_log(job, "info", f"Iniciando procesamiento de {job.total_files} archivo(s)...")
    
    files_data = files_queue.get(job_id, [])
    all_products = []
    
    # Obtener API key
    api_key = os.environ.get("EMERGENT_LLM_KEY", "")
    if not api_key:
        job.status = JobStatus.FAILED
        add_job_log(job, "err", "API key no configurada")
        return
    
    try:
        for idx, file_data in enumerate(files_data):
            filename = file_data.get("filename", f"archivo_{idx+1}")
            base64_image = file_data.get("base64", "")
            
            job.current_file = filename
            job.processed_files = idx + 1
            add_job_log(job, "info", f"📄 Procesando {idx+1}/{job.total_files}: {filename}")
            
            if not base64_image:
                add_job_log(job, "err", f"⚠️ {filename}: Sin datos de imagen")
                continue
            
            try:
                # Guardar imagen para auditoría ANTES de procesarla
                audit_id = await save_image_for_audit(
                    job_id=job_id,
                    filename=filename,
                    base64_image=base64_image,
                    library=job.library,
                    module=job.module
                )
                add_job_log(job, "info", f"💾 Imagen guardada para auditoría: {audit_id[:12]}...")
                
                # Procesar imagen con Gemini
                products, detected_tariff = await analyze_single_image(
                    base64_image, 
                    job.library, 
                    job.module, 
                    filename,
                    api_key
                )
                
                # Actualizar registro de auditoría con resultados
                await update_audit_record(audit_id, products, detected_tariff)
                
                if products:
                    all_products.extend(products)
                    job.products_found += len(products)
                    if detected_tariff:
                        job.detected_tariffs.append(detected_tariff)
                    add_job_log(job, "ok", f"✅ {filename}: {len(products)} productos ({detected_tariff or 'T1'})")
                else:
                    add_job_log(job, "warn", f"⚠️ {filename}: Sin productos detectados")
                    
            except Exception as e:
                error_msg = str(e)[:100]
                job.errors.append(f"{filename}: {error_msg}")
                add_job_log(job, "err", f"❌ {filename}: {error_msg}")
        
        # Guardar productos en la base de datos
        if all_products:
            add_job_log(job, "info", f"💾 Guardando {len(all_products)} productos...")
            
            # Agrupar por tarifa detectada
            products_by_tariff = {}
            for p in all_products:
                tariff = p.get('detectedTariff', 'T1')
                if tariff not in products_by_tariff:
                    products_by_tariff[tariff] = []
                products_by_tariff[tariff].append(p)
            
            # Mostrar resumen de tarifas detectadas
            tariffs_summary = ", ".join([f"{t}({len(prods)})" for t, prods in sorted(products_by_tariff.items())])
            add_job_log(job, "info", f"📊 Tarifas: {tariffs_summary}")
            
            for tariff, products in products_by_tariff.items():
                created, updated = await save_products_batch(products, tariff, job.library)
                job.products_created += created
                job.products_updated += updated
                add_job_log(job, "ok", f"✅ {tariff}: {created} nuevo(s), {updated} fusionado(s)")
        
        job.status = JobStatus.COMPLETED
        total_tarifas = list(set(job.detected_tariffs))
        add_job_log(job, "ok", f"🎉 Completado: {job.products_found} productos, {len(total_tarifas)} tarifa(s)")
        
    except Exception as e:
        job.status = JobStatus.FAILED
        job.errors.append(str(e))
        add_job_log(job, "err", f"❌ Error fatal: {str(e)[:100]}")
        logger.error(f"Job {job_id} failed: {e}")
    
    finally:
        job.current_file = ""
        # Limpiar archivos de la cola
        if job_id in files_queue:
            del files_queue[job_id]


async def analyze_single_image(base64_image: str, library: str, module: str, filename: str, api_key: str) -> tuple:
    """Analiza una sola imagen y devuelve los productos y la tarifa detectada"""
    products = []
    detected_tariff = None
    extracted_codes = set()
    max_passes = 2

    # Configurar Gemini con la API key
    genai.configure(api_key=api_key)

    for pass_num in range(max_passes):
        exclude_list = ", ".join(list(extracted_codes)[:50]) if extracted_codes else "ninguno"

        system_prompt = f"""Eres un experto en digitalización de tarifas de muebles de cocina MV (MUEBLES VALENCIA).

PASO 1: DETECTAR NÚMERO DE TARIFA
Busca en el encabezado: "TARIFA 1", "TARIFA 2", "T1", "T2", etc. hasta T21.
Si no encuentras, usa "T1".

PASO 2: ENTENDER LA ESTRUCTURA DE LA TABLA
Las tablas de catálogo MV tienen estas estructuras:

**ALTOS (códigos que empiezan por A):**
- Tienen DOS columnas de precios: "70" y "90" (alturas en cm)
- Profundidad fija: 33 cm
- DEBES crear DOS productos por cada fila:
  - code="CODIGO-70", height=70, depth=33
  - code="CODIGO-90", height=90, depth=33

**COLUMNAS (códigos que empiezan por C, CD, CH, etc.):**
- Tienen DOS columnas de precios: "200" y "220" (alturas en cm)
- Profundidad fija: 58 cm
- DEBES crear DOS productos por cada fila:
  - code="CODIGO-200", height=200, depth=58
  - code="CODIGO-220", height=220, depth=58

**BAJOS (códigos que empiezan por B):**
- Una sola columna de precio en el catálogo
- Profundidad fija: 58 cm
- IMPORTANTE: Aunque solo hay UNA columna de precio, DEBES crear DOS productos con el MISMO precio:
  - code="CODIGO-H70", height=70, depth=58, points=PRECIO
  - code="CODIGO-H80", height=80, depth=58, points=PRECIO (mismo precio que H70)

PASO 3: FORMATO DE SALIDA (JSON):
{{
  "detectedTariff": "T4",
  "products": [
    {{"code": "A30D/I-70", "name": "Alto 30 D/I", "category": "ALTO", "width": 30, "height": 70, "depth": 33, "points": 45}},
    {{"code": "A30D/I-90", "name": "Alto 30 D/I", "category": "ALTO", "width": 30, "height": 90, "depth": 33, "points": 52}},
    {{"code": "CD60-200", "name": "Columna Despensero 60", "category": "COLUMNA", "width": 60, "height": 200, "depth": 58, "points": 320}},
    {{"code": "CD60-220", "name": "Columna Despensero 60", "category": "COLUMNA", "width": 60, "height": 220, "depth": 58, "points": 355}},
    {{"code": "B60-H70", "name": "Bajo 60", "category": "BAJO", "width": 60, "height": 70, "depth": 58, "points": 89}},
    {{"code": "B60-H80", "name": "Bajo 60", "category": "BAJO", "width": 60, "height": 80, "depth": 58, "points": 89}}
  ]
}}

REGLAS CRÍTICAS:
1. Las dimensiones SIEMPRE en CENTÍMETROS
2. Para ALTOS: SIEMPRE crea DOS productos (-70 y -90)
3. Para COLUMNAS: SIEMPRE crea DOS productos (-200 y -220)
4. Para BAJOS: SIEMPRE crea DOS productos (-H70 y -H80) con el MISMO precio
5. points = el precio NUMÉRICO de la celda
6. Extrae hasta 60 productos por pasada
7. category debe ser: ALTO, BAJO, COLUMNA, RINCON, SOBRE, CAMPANA, MODULO

{"NO incluyas estos códigos ya extraídos: " + exclude_list if extracted_codes else "Primera pasada: extrae TODOS los productos visibles con TODAS sus variantes de altura."}

Responde SOLO con JSON válido, sin texto adicional."""

        try:
            # Decodificar imagen
            image_bytes = base64.b64decode(base64_image)

            # Detectar mime type
            magic = image_bytes[:8]
            if magic[:2] == b'\xff\xd8':
                mime_type = "image/jpeg"
            elif magic[:8] == b'\x89PNG\r\n\x1a\n':
                mime_type = "image/png"
            elif magic[:6] in (b'GIF87a', b'GIF89a'):
                mime_type = "image/gif"
            else:
                mime_type = "image/jpeg"  # fallback

            # Crear modelo con instrucción de sistema
            model = genai.GenerativeModel(
                model_name=os.environ.get("GEMINI_MODEL", "gemini-1.5-flash"),
                system_instruction=system_prompt
            )

            user_text = (
                "IMPORTANTE: Extrae productos DIFERENTES a los anteriores."
                if extracted_codes
                else "Extrae TODOS los productos visibles, incluyendo variantes de altura si las hay."
            )

            # Llamada a Gemini (síncrona en thread)
            image_part = {"mime_type": mime_type, "data": image_bytes}
            response = await asyncio.to_thread(
                model.generate_content,
                [user_text, image_part]
            )

            response_text = response.text.strip() if response and response.text else ""

            # Limpiar markdown si viene envuelto
            if "```" in response_text:
                parts = response_text.split("```")
                for part in parts:
                    part = part.strip()
                    if part.startswith("json"):
                        part = part[4:].strip()
                    if part.startswith("{"):
                        response_text = part
                        break

            response_text = response_text.strip()

            parsed = json.loads(response_text)
            new_products = parsed.get("products", [])

            if pass_num == 0:
                detected_tariff = parsed.get("detectedTariff", "T1")
                if detected_tariff:
                    detected_tariff = detected_tariff.upper().strip()
                    match = re.search(r'(\d+)', detected_tariff)
                    if match:
                        detected_tariff = f"T{match.group(1)}"
                if not detected_tariff or not detected_tariff.startswith("T"):
                    detected_tariff = "T1"

            new_count = 0
            for prod in new_products:
                code = prod.get("code", "")
                if code and code not in extracted_codes:
                    code = code.upper().strip()

                    width = float(prod.get("width", 0) or 0)
                    height = float(prod.get("height", 0) or 0)
                    depth = float(prod.get("depth", 0) or 0)
                    category = str(prod.get("category", "")).upper()

                    if width > 300:
                        width = width / 10
                    if height >= 700 and height not in [200, 220]:
                        height = height / 10
                    if depth > 300:
                        depth = depth / 10

                    if depth == 0 or depth < 20:
                        if category in ['ALTO', 'RINCON'] or code.startswith('A'):
                            depth = 33.0
                        elif category in ['BAJO', 'COLUMNA'] or code.startswith('B') or code.startswith('C'):
                            depth = 58.0
                        else:
                            depth = 58.0

                    if height == 0 or height < 30:
                        height_match = re.search(r'-H?(\d+)$', code, re.IGNORECASE)
                        if height_match:
                            height = float(height_match.group(1))
                        elif category == 'ALTO' or (code.startswith('A') and not code.startswith('AC')):
                            height = 70.0
                        elif category == 'COLUMNA' or code.startswith('C'):
                            height = 200.0
                        elif category == 'BAJO' or code.startswith('B'):
                            height = 70.0
                        else:
                            height = 70.0

                    prod['code'] = code
                    prod['width'] = width
                    prod['height'] = height
                    prod['depth'] = depth
                    prod['category'] = category
                    prod['id'] = f"AI-{module.upper()}-{uuid.uuid4().hex[:8]}"
                    prod['manufacturer'] = 'MV' if library == 'MV' else 'Zona Cocinas'
                    prod['module'] = module
                    prod['library'] = library
                    prod['importedAt'] = datetime.now(timezone.utc).isoformat()
                    prod['originalFilename'] = filename
                    prod['zonePoints'] = {detected_tariff: float(prod.get('points', 0) or 0)}
                    prod['detectedTariff'] = detected_tariff
                    products.append(prod)
                    extracted_codes.add(code)
                    new_count += 1

            if new_count == 0:
                break

        except Exception as e:
            logger.warning(f"Pass {pass_num+1} error for {filename}: {e}")
            break

    return products, detected_tariff


async def save_products_batch(products: List[Dict], tariff: str, library: str) -> tuple:
    """Guarda productos usando upsert inteligente - fusiona tarifas si el producto ya existe"""
    created = 0
    updated = 0

    for product in products:
        code = str(product.get("code", "")).upper().strip()
        if not code:
            continue

        points = float(product.get("points", 0) or 0)

        existing = await db.products.find_one({"code": code, "library": library})

        if existing:
            current_zones = existing.get("zonePoints", {}) or {}
            current_zones[tariff] = points

            update_fields = {
                "zonePoints": current_zones,
                "points": current_zones.get("T1", current_zones.get("Z1", points))
            }

            new_width = float(product.get("width", 0) or 0)
            new_height = float(product.get("height", 0) or 0)
            new_depth = float(product.get("depth", 0) or 0)
            existing_width = existing.get("width", 0) or 0
            existing_height = existing.get("height", 0) or 0
            existing_depth = existing.get("depth", 0) or 0

            if (existing_width == 0 or existing_width > 300) and new_width > 0 and new_width <= 300:
                update_fields["width"] = new_width
            if (existing_height == 0 or existing_height > 300) and new_height > 0 and new_height <= 300:
                update_fields["height"] = new_height
            if (existing_depth == 0 or existing_depth > 300) and new_depth > 0 and new_depth <= 300:
                update_fields["depth"] = new_depth
            if not existing.get("category") and product.get("category"):
                update_fields["category"] = str(product.get("category", "")).upper()

            await db.products.update_one(
                {"code": code, "library": library},
                {"$set": update_fields}
            )
            updated += 1
        else:
            width = float(product.get("width", 0) or 0)
            height = float(product.get("height", 0) or 0)
            depth = float(product.get("depth", 0) or 0)
            category = str(product.get("category", "")).upper()

            if width > 300:
                width = width / 10
            if height > 300:
                height = height / 10
            if depth > 300:
                depth = depth / 10

            if depth == 0 or depth < 20:
                if category in ['ALTO', 'RINCON'] or code.startswith('A'):
                    depth = 33.0
                elif category in ['BAJO', 'COLUMNA'] or code.startswith('B') or code.startswith('C'):
                    depth = 58.0
                else:
                    depth = 58.0

            clean_data = {
                "id": product.get("id", f"prod-{uuid.uuid4().hex[:8]}"),
                "code": code,
                "name": str(product.get("name", "")),
                "category": category,
                "series": str(product.get("series", "")),
                "visualType": str(product.get("visualType", "")),
                "width": width,
                "height": height,
                "depth": depth,
                "manufacturer": str(product.get("manufacturer", "")),
                "module": str(product.get("module", "montada")),
                "library": library,
                "points": points,
                "zonePoints": {tariff: points},
                "importedAt": datetime.now(timezone.utc).isoformat()
            }
            await db.products.insert_one(clean_data)
            created += 1

    return created, updated


async def save_image_for_audit(job_id: str, filename: str, base64_image: str, library: str, module: str) -> str:
    """Guarda la imagen en la colección 'telemetry_audit' para auditoría futura."""
    audit_id = f"audit-{uuid.uuid4().hex[:12]}"

    audit_record = {
        "id": audit_id,
        "job_id": job_id,
        "filename": filename,
        "library": library,
        "module": module,
        "image_base64": base64_image,
        "status": "processing",
        "detected_tariff": None,
        "products_extracted": [],
        "products_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "processed_at": None,
        "notes": ""
    }

    await db.telemetry_audit.insert_one(audit_record)
    logger.info(f"Image saved for audit: {audit_id} - {filename}")

    return audit_id


async def update_audit_record(audit_id: str, products: List[Dict], detected_tariff: str):
    """Actualiza el registro de auditoría con los productos extraídos."""
    products_summary = [
        {
            "code": p.get("code"),
            "name": p.get("name"),
            "points": p.get("points"),
            "width": p.get("width"),
            "height": p.get("height"),
            "depth": p.get("depth"),
            "category": p.get("category")
        }
        for p in products
    ] if products else []

    await db.telemetry_audit.update_one(
        {"id": audit_id},
        {"$set": {
            "status": "completed",
            "detected_tariff": detected_tariff,
            "products_extracted": products_summary,
            "products_count": len(products_summary),
            "processed_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    logger.info(f"Audit record updated: {audit_id} - {len(products_summary)} products")


async def get_audit_images(library: str = None, limit: int = 50, skip: int = 0) -> List[Dict]:
    """Obtiene imágenes de auditoría para revisión (sin base64 para ahorrar memoria)."""
    query = {}
    if library:
        query["library"] = library

    cursor = db.telemetry_audit.find(
        query,
        {"image_base64": 0}
    ).sort("created_at", -1).skip(skip).limit(limit)

    return await cursor.to_list(length=limit)


async def get_audit_image_detail(audit_id: str) -> Optional[Dict]:
    """Obtiene el detalle completo de una imagen de auditoría, incluyendo el base64."""
    record = await db.telemetry_audit.find_one({"id": audit_id})
    if record:
        record.pop("_id", None)
    return record


async def update_audit_notes(audit_id: str, notes: str) -> bool:
    """Permite añadir notas a un registro de auditoría."""
    result = await db.telemetry_audit.update_one(
        {"id": audit_id},
        {"$set": {"notes": notes, "reviewed_at": datetime.now(timezone.utc).isoformat()}}
    )
    return result.modified_count > 0
