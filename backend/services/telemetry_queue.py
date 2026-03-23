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

from motor.motor_asyncio import AsyncIOMotorClient
from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent

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
                # Procesar imagen con Gemini
                products, detected_tariff = await analyze_single_image(
                    base64_image, 
                    job.library, 
                    job.module, 
                    filename,
                    api_key
                )
                
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
            
            for tariff, products in products_by_tariff.items():
                created, updated = await save_products_batch(products, tariff, job.library)
                job.products_created += created
                job.products_updated += updated
                add_job_log(job, "info", f"📌 {tariff}: {created} nuevo(s), {updated} actualizado(s)")
        
        job.status = JobStatus.COMPLETED
        add_job_log(job, "ok", f"✅ Completado: {job.products_found} productos encontrados")
        
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
    
    for pass_num in range(max_passes):
        exclude_list = ", ".join(list(extracted_codes)[:50]) if extracted_codes else "ninguno"
        
        system_prompt = f"""Eres un experto en digitalización de tarifas de muebles MV (MUEBLES VALENCIA).

PASO 0: DETECTAR NÚMERO DE TARIFA
Lee el encabezado para identificar: "TARIFA 1", "TARIFA 2", etc. o "T1", "T2", etc.
Si no encuentras tarifa, usa "T1".

FORMATO DE SALIDA (JSON):
{{
  "detectedTariff": "T1",
  "products": [
    {{"code": "A30D/I*-70", "name": "Alto 30 D/I 70cm", "category": "ALTO", "width": 300, "height": 700, "points": 45}}
  ]
}}

REGLAS:
1. Código = código_producto + "-" + altura (ej: "A30D/I*-70")
2. points = precio de la celda
3. Extrae hasta 50 productos
4. "detectedTariff" = tarifa del encabezado

{"NO incluyas códigos ya extraídos: " + exclude_list if extracted_codes else ""}

Responde SOLO con JSON válido."""

        chat = LlmChat(
            api_key=api_key,
            session_id=f"telemetry-{uuid.uuid4().hex[:8]}",
            system_message=system_prompt
        ).with_model("gemini", "gemini-2.0-flash")
        
        user_message = UserMessage(
            text=f"Analiza esta página. {'Extrae productos DIFERENTES a los anteriores.' if extracted_codes else 'Extrae todos los productos.'}",
            file_contents=[ImageContent(image_base64=base64_image)]
        )
        
        try:
            response = await chat.send_message(user_message)
            response_text = str(response).strip() if response else ""
            
            # Limpiar markdown
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            response_text = response_text.strip()
            
            parsed = json.loads(response_text)
            new_products = parsed.get("products", [])
            
            if pass_num == 0:
                detected_tariff = parsed.get("detectedTariff", "T1")
                if not detected_tariff or not detected_tariff.startswith("T"):
                    detected_tariff = "T1"
            
            new_count = 0
            for prod in new_products:
                code = prod.get("code", "")
                if code and code not in extracted_codes:
                    prod['id'] = f"AI-{module.upper()}-{uuid.uuid4().hex[:8]}"
                    prod['manufacturer'] = 'MV' if library == 'MV' else 'Zona Cocinas'
                    prod['module'] = module
                    prod['library'] = library
                    prod['importedAt'] = datetime.now(timezone.utc).isoformat()
                    prod['originalFilename'] = filename
                    prod['zonePoints'] = {detected_tariff: prod.get('points', 0)}
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
    """Guarda productos usando upsert"""
    created = 0
    updated = 0
    
    for product in products:
        code = str(product.get("code", "")).upper().strip()
        if not code:
            continue
        
        points = float(product.get("points", 0) or 0)
        
        existing = await db.products.find_one({
            "code": code,
            "library": library
        })
        
        if existing:
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
        else:
            clean_data = {
                "id": product.get("id", f"prod-{uuid.uuid4().hex[:8]}"),
                "code": code,
                "name": str(product.get("name", "")),
                "category": str(product.get("category", "")),
                "series": str(product.get("series", "")),
                "visualType": str(product.get("visualType", "")),
                "width": float(product.get("width", 0) or 0),
                "height": float(product.get("height", 0) or 0),
                "depth": float(product.get("depth", 0) or 0),
                "manufacturer": str(product.get("manufacturer", "")),
                "module": str(product.get("module", "montada")),
                "library": library,
                "points": points,
                "zonePoints": {tariff: points}
            }
            await db.products.insert_one(clean_data)
            created += 1
    
    return created, updated
