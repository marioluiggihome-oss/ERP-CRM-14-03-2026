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

    # Test de ESCRITURA real en las colecciones donde fallaba el guardado.
    # Inserta un documento de prueba (marcado con _diag) y lo borra. Si alguna
    # falla, ese es el problema y veremos el error exacto por colección.
    writes = {}
    for coll in ["contacts", "calendar_events", "projects", "diag_scratch"]:
        try:
            doc = {"id": f"_diag-{datetime.utcnow().timestamp()}", "_diag": True,
                   "name": "DIAG TEST", "ts": datetime.utcnow()}
            res = await _db[coll].insert_one(doc)
            await _db[coll].delete_one({"_id": res.inserted_id})
            writes[coll] = "OK"
        except Exception as e:
            writes[coll] = f"FALLO: {e}"
            out["ok"] = False
            logger.error(f"db-health write test '{coll}' failed: {e}")
    out["write_test"] = writes

    # Índices de cada colección (para detectar índices únicos que bloqueen
    # escrituras por duplicado).
    idx = {}
    for coll in ["contacts", "calendar_events", "projects"]:
        try:
            info = await _db[coll].index_information()
            idx[coll] = {name: {"keys": v.get("key"), "unique": v.get("unique", False)}
                         for name, v in info.items()}
        except Exception as e:
            idx[coll] = f"error: {e}"
    out["indexes"] = idx

    return out


@router.get("/recent-errors")
async def recent_errors(limit: int = 20):
    """Últimos errores de guardado (422/500) capturados por el servidor.

    Permite ver el error EXACTO de un fallo al crear contacto/visita/
    presupuesto sin necesidad de la consola del navegador: reproduce el fallo
    en la app y luego abre esta URL.
    """
    try:
        docs = await _db.error_log.find({}, {"_id": 0}).sort("ts", -1).to_list(limit)
        return {"count": len(docs), "errors": docs}
    except Exception as e:
        return {"count": 0, "errors": [], "error": str(e)}


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


# ==================== ALTA PUNTUAL DE USUARIO MONTAJES ====================
# Endpoint de UN SOLO USO, protegido por token, para crear/restablecer un
# usuario con acceso SOLO a Montajes (isMontador) cuando no se puede usar el
# panel. La contrasena se pasa por parametro (no se guarda en el codigo).
@router.get("/setup-montajes-user")
async def setup_montajes_user(token: str = "", username: str = "", password: str = ""):
    import re as _re
    import uuid as _uuid
    import bcrypt as _bcrypt
    from datetime import datetime as _dt, timezone as _tz

    if token != "LH-SETUP-MONTAJES-2026":
        raise HTTPException(status_code=403, detail="No autorizado")
    if not username or not password:
        raise HTTPException(status_code=400, detail="Faltan username y password")

    pwd_hash = _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")

    # Perfil montajes-only: isMontador=True y el resto de roles/accesos en False.
    montajes_fields = {
        "password": pwd_hash, "isActive": True, "isMontador": True,
        "isAdmin": False, "isPrimaryAdmin": False, "isGerente": False,
        "isDirectorComercial": False, "isDirectorFabrica": False,
        "isResponsableDelegacion": False, "isRepresentative": False,
        "isPrescriptor": False, "isTienda": False, "isFabrica": False,
        "canAccessCRM": False, "canUseDigitalizador": False,
        "canAccessArmarios": False, "canAccessFabrica": False,
        "canManageOrders": False, "canSetDeliveryDates": False,
        "canAuthorizePermissions": False, "canChangeLogo": False,
        "useCustomBranding": False, "canManageUsers": False,
    }

    existing = await _db.users.find_one(
        {"username": {"$regex": f"^{_re.escape(username)}$", "$options": "i"}}
    )
    if existing:
        await _db.users.update_one({"id": existing["id"]}, {"$set": montajes_fields})
        return {"action": "actualizado (ya existia)", "username": existing.get("username"),
                "id": existing.get("id"), "rol": "solo montajes"}

    user_data = {
        "id": f"user-{_uuid.uuid4().hex[:8]}",
        "username": username,
        "clientName": username,
        "allowedModules": [],
        "allowedLibraries": [],
        "allowedCatalogIds": [],
        "createdAt": _dt.now(_tz.utc).isoformat(),
        **montajes_fields,
    }
    await _db.users.insert_one(user_data)
    user_data.pop("_id", None)
    return {"action": "creado", "username": username, "id": user_data["id"],
            "rol": "solo montajes"}


# ==================== QUITAR PERMISO AGENDA DE NEGOCIOS (PRESCRIPTOR) ====================
# Endpoint puntual (token) para quitar a un usuario el permiso de Agenda de
# Negocios (isPrescriptor), que de forma exclusiva ocultaba el resto de
# funciones. Util cuando el propio usuario se ha quedado bloqueado en esa vista.
@router.get("/remove-agenda-permission")
async def remove_agenda_permission(token: str = "", username: str = ""):
    if token != "LH-SETUP-MONTAJES-2026":
        raise HTTPException(status_code=403, detail="No autorizado")
    if not username:
        raise HTTPException(status_code=400, detail="Falta username")
    import re as _re
    user = await _db.users.find_one(
        {"username": {"$regex": f"^{_re.escape(username)}$", "$options": "i"}}, {"_id": 0}
    )
    if not user:
        raise HTTPException(status_code=404, detail=f"Usuario '{username}' no encontrado")
    await _db.users.update_one({"id": user["id"]}, {"$set": {"isPrescriptor": False}})
    return {"action": "permiso de agenda de negocios retirado",
            "username": user.get("username"), "id": user.get("id")}
