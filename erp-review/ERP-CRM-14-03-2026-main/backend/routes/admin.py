"""
Endpoints de Administración del Sistema - LUIGGI HOME
- Backups
- Informes de uso
- Estadísticas del sistema
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from datetime import datetime
from typing import Optional
import logging

from services.backup_service import get_backup_service
from services.activity_tracker import get_tracker, ActivityType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


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
