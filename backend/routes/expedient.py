# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
Routes for Expedient Number Generation
Extracted from server.py for better maintainability
"""
from fastapi import APIRouter, HTTPException, Depends
from services.jwt_service import require_auth
from datetime import datetime
import logging
import os

from dotenv import load_dotenv
from services.db_client import get_db as _get_db

load_dotenv()
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/expedient", tags=["expedient"])

# Database connection


@router.get("/next")
async def get_next_expedient_number(client_code: str = None, current_user: dict = Depends(require_auth)):
    """
    Obtener el siguiente número de expediente correlativo por cliente.
    Formato: EXP-AAAA-CLIENTE-NNN (ej: EXP-2026-LEON01-001)
    Si no hay código de cliente, usa formato legacy: EXP-AAAA-NNNNN
    """
    try:
        year = datetime.now().year
        
        if client_code and client_code.strip():
            # Nuevo formato: por cliente
            client_code = client_code.strip().upper()
            counter_key = f"expedient_{year}_{client_code}"
            
            # Obtener o crear el contador para este cliente
            counter = await _get_db().system_counters.find_one({"key": counter_key})
            
            if not counter:
                counter = {
                    "key": counter_key,
                    "value": 0,
                    "year": year,
                    "clientCode": client_code
                }
                await _get_db().system_counters.insert_one(counter)
            
            # Incrementar el contador atómicamente
            result = await _get_db().system_counters.find_one_and_update(
                {"key": counter_key},
                {"$inc": {"value": 1}},
                return_document=True
            )
            
            next_number = result["value"]
            expedient = f"EXP-{year}-{client_code}-{next_number:03d}"
            
            return {
                "success": True,
                "expedient": expedient,
                "number": next_number,
                "year": year,
                "clientCode": client_code
            }
        else:
            # Formato legacy (sin código de cliente)
            counter_key = f"expedient_{year}"
            counter = await _get_db().system_counters.find_one({"key": counter_key})
            
            if not counter:
                counter = {
                    "key": counter_key,
                    "value": 0,
                    "year": year
                }
                await _get_db().system_counters.insert_one(counter)
            
            result = await _get_db().system_counters.find_one_and_update(
                {"key": counter_key},
                {"$inc": {"value": 1}},
                return_document=True
            )
            
            next_number = result["value"]
            expedient = f"EXP-{year}-{next_number:05d}"
            
            return {
                "success": True,
                "expedient": expedient,
                "number": next_number,
                "year": year
            }
    except Exception as e:
        logger.error(f"Error getting next expedient: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo número de expediente: {str(e)}")


@router.get("/current")
async def get_current_expedient_info(current_user: dict = Depends(require_auth)):
    """Obtener información del contador de expedientes actual"""
    try:
        year = datetime.now().year
        counter = await _get_db().system_counters.find_one({"key": f"expedient_{year}"})
        
        current = counter["value"] if counter else 0
        
        return {
            "success": True,
            "year": year,
            "currentCount": current,
            "nextExpedient": f"EXP-{year}-{current + 1:05d}"
        }
    except Exception as e:
        logger.error(f"Error getting expedient info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/counters")
async def get_all_counters(current_user: dict = Depends(require_auth)):
    """Obtener todos los contadores de expedientes (por cliente)"""
    try:
        year = datetime.now().year
        counters = await _get_db().system_counters.find(
            {"key": {"$regex": f"^expedient_{year}"}},
            {"_id": 0}
        ).to_list(1000)
        
        return {
            "success": True,
            "year": year,
            "counters": counters
        }
    except Exception as e:
        logger.error(f"Error getting counters: {e}")
        raise HTTPException(status_code=500, detail=str(e))
