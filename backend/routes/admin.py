"""
Endpoints de Administración del Sistema - LUIGGI HOME
- Backups
- Informes de uso
- Estadísticas del sistema
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from datetime import datetime, timedelta
from typing import Optional
import logging
import os

from motor.motor_asyncio import AsyncIOMotorClient

from services.backup_service import get_backup_service
from services.activity_tracker import get_tracker, ActivityType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])

# Conexión a BD (mismo patrón que el resto de routers)
_MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
_DB_NAME = os.environ.get('DB_NAME', 'luiggi_home')
_admin_client = AsyncIOMotorClient(_MONGO_URL)
_db = _admin_client[_DB_NAME]


# ==================== DIAGNÓSTICO DE BASE DE DATOS ====================

@router.get("/db-health")
async def db_health():
    """Diagnóstico de la base de datos: tamaño, límite y test de ESCRITURA real.

    Sirve para confirmar si los fallos al guardar (contactos, visitas,
    presupuestos) se deben a que la BD no acepta escrituras (p.ej. cuota de
    almacenamiento llena en Atlas). Hace un insert+delete de prueba.
    """
    out = {"ok": True}
    try:
        stats = await _db.command("dbStats", scale=1024 * 1024)  # MB
        out["storage"] = {
            "dataSize_MB": round(stats.get("dataSize", 0), 2),
            "storageSize_MB": round(stats.get("storageSize", 0), 2),
            "indexSize_MB": round(stats.get("indexSize", 0), 2),
            "objects": stats.get("objects", 0),
        }
        # Colecciones más grandes por nº de documentos
        sizes = {}
        for name in await _db.list_collection_names():
            try:
                sizes[name] = await _db[name].estimated_document_count()
            except Exception:
                pass
        out["top_collections"] = dict(sorted(sizes.items(), key=lambda x: -x[1])[:10])
    except Exception as e:
        out["storage_error"] = str(e)

    # Test de escritura real: si esto falla, ESE es el problema de guardado.
    try:
        test_doc = {"_diag": True, "ts": datetime.utcnow()}
        res = await _db._diag_write_test.insert_one(test_doc)
        await _db._diag_write_test.delete_one({"_id": res.inserted_id})
        out["write_test"] = "OK"
    except Exception as e:
        out["ok"] = False
        out["write_test"] = "FALLO"
        out["write_error"] = str(e)
        logger.error(f"db-health write test failed: {e}")

    return out


@router.post("/cleanup-telemetry")
async def cleanup_telemetry(days: int = 90):
    """Purga telemetría/actividad antigua para liberar espacio en la BD.

    Borra documentos de las colecciones de telemetría con más de `days` días.
    Útil si la BD se ha llenado por el registro de actividad sin tope.
    """
    cutoff = datetime.utcnow() - timedelta(days=days)
    deleted = {}
    # user_activity usa 'timestamp'; telemetry_audit puede usar 'timestamp' o 'createdAt'.
    for coll, field in [("user_activity", "timestamp"), ("telemetry_audit", "timestamp")]:
        try:
            r = await _db[coll].delete_many({field: {"$lt": cutoff}})
            deleted[coll] = r.deleted_count
        except Exception as e:
            deleted[coll] = f"error: {e}"
    return {"success": True, "cutoff_days": days, "deleted": deleted}


# ==================== BACKUP ENDPOINTS ====================

@router.post("/backup/create")
async def create_backup():
    """Crear un backup manual de la base de datos"""
    backup_service = get_backup_service()
    if not backup_service:
        raise HTTPException(status_code=500, detail="Servicio de backup no inicializado")
    
    result = await backup_service.create_backup()
    
    if result["success"]:
        return result
    else:
        raise HTTPException(status_code=500, detail=result.get("error", "Error creando backup"))


@router.get("/backup/list")
async def list_backups():
    """Listar todos los backups disponibles"""
    backup_service = get_backup_service()
    if not backup_service:
        raise HTTPException(status_code=500, detail="Servicio de backup no inicializado")
    
    return {
        "success": True,
        "backups": backup_service.list_backups(),
        "retention_days": 7
    }


@router.post("/backup/restore/{backup_name}")
async def restore_backup(backup_name: str):
    """Restaurar un backup específico (¡CUIDADO: sobrescribe datos actuales!)"""
    backup_service = get_backup_service()
    if not backup_service:
        raise HTTPException(status_code=500, detail="Servicio de backup no inicializado")
    
    result = await backup_service.restore_backup(backup_name)
    
    if result["success"]:
        return result
    else:
        raise HTTPException(status_code=500, detail=result.get("error", "Error restaurando backup"))


# ==================== USAGE REPORTS ENDPOINTS ====================

@router.get("/usage/report")
async def get_usage_report(days: int = 30):
    """Obtener informe completo de uso de la plataforma"""
    tracker = get_tracker()
    if not tracker:
        raise HTTPException(status_code=500, detail="Tracker de actividad no inicializado")
    
    return await tracker.get_usage_report(days=days)


@router.get("/usage/users")
async def get_user_stats(user_id: Optional[str] = None, days: int = 30):
    """Obtener estadísticas de uso por usuario"""
    tracker = get_tracker()
    if not tracker:
        raise HTTPException(status_code=500, detail="Tracker de actividad no inicializado")
    
    stats = await tracker.get_user_stats(user_id=user_id, days=days)
    return {
        "success": True,
        "period_days": days,
        "users": stats
    }


@router.get("/usage/timeline")
async def get_activity_timeline(
    user_id: Optional[str] = None,
    days: int = 30,
    limit: int = 100
):
    """Obtener timeline de actividades recientes"""
    tracker = get_tracker()
    if not tracker:
        raise HTTPException(status_code=500, detail="Tracker de actividad no inicializado")
    
    timeline = await tracker.get_activity_timeline(user_id=user_id, days=days, limit=limit)
    return {
        "success": True,
        "period_days": days,
        "activities": timeline
    }


@router.get("/usage/daily")
async def get_daily_activity(days: int = 30):
    """Obtener actividad diaria agregada"""
    tracker = get_tracker()
    if not tracker:
        raise HTTPException(status_code=500, detail="Tracker de actividad no inicializado")
    
    daily = await tracker.get_daily_activity(days=days)
    return {
        "success": True,
        "period_days": days,
        "daily_activity": daily
    }


@router.get("/usage/by-type")
async def get_activity_by_type(days: int = 30):
    """Obtener actividad agrupada por tipo"""
    tracker = get_tracker()
    if not tracker:
        raise HTTPException(status_code=500, detail="Tracker de actividad no inicializado")
    
    by_type = await tracker.get_activity_by_type(days=days)
    return {
        "success": True,
        "period_days": days,
        "activity_by_type": by_type
    }
