# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
Routes for AI Telemetry (Optical Recognition)
Extracted from server.py for better maintainability
"""
from fastapi import APIRouter, HTTPException, File, UploadFile, Form, Depends
from services.jwt_service import require_auth
from typing import List
import logging
import base64
import os

from services.telemetry_queue import (
    create_telemetry_job, 
    get_job_status, 
    get_audit_images, 
    get_audit_image_detail, 
    update_audit_notes
)

logger = logging.getLogger(__name__)

# CERRADO EN LA PUERTA. La dependencia va en el propio APIRouter y no
# endpoint a endpoint: asi el que se aniada maniana nace cerrado, que es
# justo lo que fallo hasta ahora — la telemetria de uso.
router = APIRouter(prefix="/telemetry", tags=["telemetry"],
                   dependencies=[Depends(require_auth)])


@router.post("/start-job")
async def start_telemetry_job(
    module: str = Form(...),
    library: str = Form("MV"),
    files: List[UploadFile] = File(...)
):
    """
    Inicia un job de procesamiento de telemetría en segundo plano.
    Devuelve inmediatamente un job_id para consultar el progreso.
    """
    try:
        from services.pdf_utils import is_pdf_bytes, pdf_base64_to_png_base64

        # Convertir archivos a base64
        files_data = []
        for file in files:
            content = await file.read()

            # Validar tipo
            magic_bytes = content[:8]
            is_jpeg = magic_bytes[:2] == b'\xff\xd8'
            is_png = magic_bytes[:8] == b'\x89PNG\r\n\x1a\n'
            is_gif = magic_bytes[:6] in (b'GIF87a', b'GIF89a')
            is_pdf = is_pdf_bytes(content)

            if is_pdf:
                # Los catálogos suelen venir en PDF (a veces escaneados). Cada
                # página se rasteriza a PNG para que la IA pueda analizarla.
                try:
                    pdf_b64 = base64.b64encode(content).decode('utf-8')
                    page_images = pdf_base64_to_png_base64(pdf_b64, dpi=150)
                except Exception as e:
                    logger.error(f"Error convirtiendo PDF {file.filename}: {e}")
                    page_images = []

                if not page_images:
                    logger.warning(f"PDF sin páginas convertibles: {file.filename}")
                    continue

                base_name = file.filename or "catalogo.pdf"
                for page_idx, page_b64 in enumerate(page_images):
                    files_data.append({
                        "filename": f"{base_name} (pág. {page_idx + 1})",
                        "base64": page_b64
                    })
                logger.info(f"PDF {base_name}: {len(page_images)} página(s) añadida(s) al job")
                continue

            if not (is_jpeg or is_png or is_gif):
                logger.warning(f"Skipping non-image file: {file.filename}")
                continue

            base64_image = base64.b64encode(content).decode('utf-8')
            files_data.append({
                "filename": file.filename,
                "base64": base64_image
            })

        if not files_data:
            return {"success": False, "error": "No se encontraron imágenes válidas"}
        
        # Crear job en la cola
        job_id = await create_telemetry_job(library, module, files_data)
        
        return {
            "success": True,
            "job_id": job_id,
            "message": f"Job iniciado con {len(files_data)} archivo(s)",
            "total_files": len(files_data)
        }
        
    except Exception as e:
        logger.error(f"Error starting telemetry job: {e}")
        return {"success": False, "error": str(e)}


@router.get("/job-status/{job_id}")
async def get_telemetry_job_status(job_id: str):
    """Obtiene el estado actual de un job de telemetría"""
    status = await get_job_status(job_id)
    if not status:
        return {"success": False, "error": "Job no encontrado"}
    return {"success": True, **status}


# =============================================
# AUDITORÍA DE TELEMETRÍA - Imágenes guardadas
# =============================================
@router.get("/audit")
async def list_audit_images(library: str = None, limit: int = 50, skip: int = 0):
    """Lista las imágenes guardadas para auditoría"""
    try:
        images = await get_audit_images(library=library, limit=limit, skip=skip)
        return {"success": True, "images": images, "count": len(images)}
    except Exception as e:
        logger.error(f"Error listing audit images: {e}")
        return {"success": False, "error": str(e)}


@router.get("/audit/{audit_id}")
async def get_audit_image(audit_id: str):
    """Obtiene el detalle de una imagen de auditoría, incluyendo la imagen base64"""
    try:
        record = await get_audit_image_detail(audit_id)
        if not record:
            return {"success": False, "error": "Registro no encontrado"}
        return {"success": True, "record": record}
    except Exception as e:
        logger.error(f"Error getting audit image: {e}")
        return {"success": False, "error": str(e)}


@router.put("/audit/{audit_id}/notes")
async def update_audit_image_notes(audit_id: str, notes: str = Form(...)):
    """Actualiza las notas de un registro de auditoría"""
    try:
        success = await update_audit_notes(audit_id, notes)
        return {"success": success}
    except Exception as e:
        logger.error(f"Error updating audit notes: {e}")
        return {"success": False, "error": str(e)}
