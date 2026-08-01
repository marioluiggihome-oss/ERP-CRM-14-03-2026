"""
Routes for Maintenance Mode
Extracted from server.py for better maintainability
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta
from typing import Optional
import logging
import uuid
import json
import os

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from services.jwt_service import require_admin

load_dotenv()
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/maintenance", tags=["maintenance"])

# Database connection
MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME", "luiggi_home")
client = AsyncIOMotorClient(MONGO_URL, serverSelectionTimeoutMS=5000, connectTimeoutMS=10000)
db = client[DB_NAME]

# Global maintenance state (synced with DB)
maintenance_state = {
    "active": False,
    "message": "",
    "activatedAt": None,
    "activatedBy": None,
    "estimatedEndTime": None,
    "preUpdateBackupId": None
}


# Pydantic models
class MaintenanceActivateRequest(BaseModel):
    adminUserId: str
    message: str = "Sistema en mantenimiento. Volvemos pronto."
    estimatedMinutes: int = 30
    createBackup: bool = True


class MaintenanceStatusResponse(BaseModel):
    isActive: bool
    reason: str
    startedAt: Optional[str] = None
    estimatedEndAt: Optional[str] = None
    lastBackup: Optional[str] = None


@router.get("/status")
async def get_maintenance_status():
    """Get current maintenance mode status - accessible to everyone"""
    global maintenance_state
    
    # Sync with database on first call
    db_state = await db.system_settings.find_one({"key": "maintenance_mode"})
    if db_state:
        maintenance_state = db_state.get("value", maintenance_state)
    
    return MaintenanceStatusResponse(
        isActive=maintenance_state.get("active", False),
        reason=maintenance_state.get("message", ""),
        startedAt=maintenance_state.get("activatedAt"),
        estimatedEndAt=maintenance_state.get("estimatedEndTime"),
        lastBackup=maintenance_state.get("preUpdateBackupId")
    )


@router.post("/activate")
async def activate_maintenance_mode(request: MaintenanceActivateRequest, user=Depends(require_admin)):
    """Activate maintenance mode - ADMIN ONLY"""
    global maintenance_state
    
    try:
        # Verify admin user
        admin_user = await db.users.find_one({"id": request.adminUserId})
        if not admin_user or not admin_user.get("isAdmin"):
            raise HTTPException(status_code=403, detail="Solo administradores pueden activar modo mantenimiento")
        
        backup_id = None
        
        # Create pre-update backup if requested
        if request.createBackup:
            logger.info("Creating pre-update backup before maintenance mode...")
            
            # Collect all data
            backup_data = {
                "type": "pre_update_backup",
                "createdAt": datetime.now(timezone.utc).isoformat(),
                "createdBy": request.adminUserId,
                "reason": "Backup automático antes de actualización",
                "collections": {}
            }
            
            # Backup all important collections
            collections_to_backup = [
                "users", "products", "projects", "materials", "settings",
                "contacts", "opportunities", "activities", "catalogs",
                "digitalizador_history"
            ]
            
            for coll_name in collections_to_backup:
                try:
                    docs = await db[coll_name].find({}).to_list(length=None)
                    # Convert ObjectId to string
                    for doc in docs:
                        doc.pop('_id', None)
                    backup_data["collections"][coll_name] = docs
                    logger.info(f"  Backed up {len(docs)} documents from {coll_name}")
                except Exception as e:
                    logger.error(f"  Error backing up {coll_name}: {e}")
                    backup_data["collections"][coll_name] = []
            
            # Save backup to database
            backup_id = f"backup-preupdate-{uuid.uuid4().hex[:12]}"
            backup_record = {
                "id": backup_id,
                "type": "pre_update",
                "createdAt": datetime.now(timezone.utc).isoformat(),
                "createdBy": admin_user.get("username", "admin"),
                "data": backup_data,
                "size": len(json.dumps(backup_data, default=str))
            }
            
            await db.system_backups.insert_one(backup_record)
            logger.info(f"Pre-update backup created with ID: {backup_id}")
        
        # Calculate estimated end time
        estimated_end = datetime.now(timezone.utc) + timedelta(minutes=request.estimatedMinutes)
        
        # Update maintenance state
        maintenance_state = {
            "active": True,
            "message": request.message,
            "activatedAt": datetime.now(timezone.utc).isoformat(),
            "activatedBy": admin_user.get("username", "admin"),
            "estimatedEndTime": estimated_end.isoformat(),
            "preUpdateBackupId": backup_id
        }
        
        # Save to database for persistence
        await db.system_settings.update_one(
            {"key": "maintenance_mode"},
            {"$set": {"key": "maintenance_mode", "value": maintenance_state}},
            upsert=True
        )
        
        logger.info(f"Maintenance mode ACTIVATED by {admin_user.get('username')}")
        
        return {
            "success": True,
            "message": "Modo mantenimiento activado",
            "state": maintenance_state
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error activating maintenance mode: {e}")
        raise HTTPException(status_code=500, detail=f"Error activando modo mantenimiento: {str(e)}")


@router.post("/deactivate")
async def deactivate_maintenance_mode(adminUserId: str, user=Depends(require_admin)):
    """Deactivate maintenance mode - ADMIN ONLY"""
    global maintenance_state
    
    try:
        # Verify admin user
        admin_user = await db.users.find_one({"id": adminUserId})
        if not admin_user or not admin_user.get("isAdmin"):
            raise HTTPException(status_code=403, detail="Solo administradores pueden desactivar modo mantenimiento")
        
        # Update maintenance state
        maintenance_state = {
            "active": False,
            "message": "",
            "activatedAt": None,
            "activatedBy": None,
            "estimatedEndTime": None,
            "preUpdateBackupId": None
        }
        
        # Save to database
        await db.system_settings.update_one(
            {"key": "maintenance_mode"},
            {"$set": {"key": "maintenance_mode", "value": maintenance_state}},
            upsert=True
        )
        
        logger.info(f"Maintenance mode DEACTIVATED by {admin_user.get('username')}")
        
        return {
            "success": True,
            "message": "Modo mantenimiento desactivado. Sistema operativo."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deactivating maintenance mode: {e}")
        raise HTTPException(status_code=500, detail=f"Error desactivando modo mantenimiento: {str(e)}")


@router.get("/backups")
async def list_pre_update_backups(limit: int = 10, user=Depends(require_admin)):
    """List all pre-update backups (solo admin)."""
    try:
        cursor = db.system_backups.find({"type": "pre_update"}).sort("createdAt", -1).limit(limit)
        backups = await cursor.to_list(length=limit)
        
        # Return summary without full data
        result = []
        for b in backups:
            b.pop('_id', None)
            b.pop('data', None)  # Don't send full backup data in list
            result.append(b)
        
        return {
            "success": True,
            "backups": result,
            "count": len(result)
        }
    except Exception as e:
        logger.error(f"Error listing backups: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/backups/{backup_id}/download")
async def download_pre_update_backup(backup_id: str, user=Depends(require_admin)):
    """Download a specific pre-update backup"""
    try:
        backup = await db.system_backups.find_one({"id": backup_id})
        
        if not backup:
            raise HTTPException(status_code=404, detail="Backup no encontrado")
        
        backup.pop('_id', None)
        
        return {
            "success": True,
            "backup": backup
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading backup: {e}")
        raise HTTPException(status_code=500, detail=str(e))
