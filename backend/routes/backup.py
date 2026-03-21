"""
Backup Router - Sistema de copias de seguridad
Endpoints para gestionar backups automáticos y manuales
"""
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from typing import Dict
import uuid
import logging
import os
import json
import base64
import asyncio

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from services.rate_limiter import limiter, get_limit
from services.audit_service import audit, AuditAction

logger = logging.getLogger(__name__)

router = APIRouter(tags=["backup"])

# Database connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'luiggi_home')
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

# Scheduler for automatic backups
scheduler = AsyncIOScheduler()


# Backup History Model
class BackupHistoryModel(BaseModel):
    id: str = Field(default_factory=lambda: f"backup-{uuid.uuid4().hex[:8]}")
    timestamp: str
    type: str  # manual, scheduled
    status: str  # success, failed
    itemCount: int
    sentTo: str


async def create_backup_data():
    """Creates a JSON backup of all database collections"""
    backup = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "2.0",
        "data": {}
    }
    
    # Export all important collections
    collections = [
        "users", 
        "products",           # Productos MONTADA (muebles)
        "despiece_products",  # Productos DESPIECE (tableros)
        "materials", 
        "projects", 
        "settings",
        "clients",
        "opportunities",
        "activities",
        "calendar_events",
        "orders",
        "armario_projects",
        "status_checks"
    ]
    
    for collection_name in collections:
        try:
            docs = await db[collection_name].find({}, {"_id": 0}).to_list(50000)
            backup["data"][collection_name] = docs
            logger.info(f"Backup: {collection_name} - {len(docs)} documentos")
        except Exception as e:
            logger.error(f"Error backing up {collection_name}: {e}")
            backup["data"][collection_name] = []
    
    return backup


def send_backup_email(backup_data: dict, backup_type: str = "automático"):
    """Sends backup via SendGrid email with JSON attachment"""
    try:
        sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')
        backup_email = os.environ.get('BACKUP_EMAIL', 'marioluiggihome@gmail.com')
        
        if not sendgrid_api_key:
            logger.error("SENDGRID_API_KEY not configured")
            return False
        
        # Create JSON content
        json_content = json.dumps(backup_data, indent=2, ensure_ascii=False, default=str)
        encoded_content = base64.b64encode(json_content.encode('utf-8')).decode('utf-8')
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"luiggi_home_backup_{timestamp}.json"
        
        # Count items
        total_items = sum(len(backup_data.get("data", {}).get(col, [])) for col in backup_data.get("data", {}).keys())
        
        # Create email message
        message = Mail(
            from_email=backup_email,
            to_emails=backup_email,
            subject=f"LUIGGI HOME - Backup {backup_type} ({timestamp})",
            html_content=f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #1e293b 0%, #334155 100%); color: white; padding: 30px; border-radius: 10px 10px 0 0;">
                    <h1 style="margin: 0; font-size: 24px;">LUIGGI HOME</h1>
                    <p style="margin: 10px 0 0 0; opacity: 0.8; font-size: 14px;">Copia de Seguridad {backup_type.upper()}</p>
                </div>
                
                <div style="background: #f8fafc; padding: 30px; border: 1px solid #e2e8f0; border-top: none;">
                    <h2 style="color: #1e293b; margin-top: 0;">Backup completado</h2>
                    
                    <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                        <tr style="background: #e2e8f0;">
                            <td style="padding: 10px; font-weight: bold;">Fecha</td>
                            <td style="padding: 10px;">{datetime.now().strftime("%d/%m/%Y %H:%M:%S")}</td>
                        </tr>
                        <tr>
                            <td style="padding: 10px; font-weight: bold;">Total registros</td>
                            <td style="padding: 10px;">{total_items}</td>
                        </tr>
                        <tr style="background: #e2e8f0;">
                            <td style="padding: 10px; font-weight: bold;">Archivo</td>
                            <td style="padding: 10px;">{filename}</td>
                        </tr>
                    </table>
                    
                    <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0;">
                        <strong>Importante:</strong> Guarda este archivo en tu Google Drive para mantener tus datos seguros.
                    </div>
                    
                    <h3 style="color: #1e293b;">Detalle del backup:</h3>
                    <ul style="list-style: none; padding: 0;">
                        {"".join([f'<li style="padding: 5px 0;">- {col}: {len(backup_data.get("data", {}).get(col, []))} registros</li>' for col in backup_data.get("data", {}).keys()])}
                    </ul>
                </div>
                
                <div style="background: #1e293b; color: white; padding: 20px; border-radius: 0 0 10px 10px; text-align: center; font-size: 12px;">
                    <p style="margin: 0;">LUIGGI HOME Master Design v2026</p>
                    <p style="margin: 5px 0 0 0; opacity: 0.7;">Sistema de Gestion de Presupuestos de Cocina</p>
                </div>
            </body>
            </html>
            """
        )
        
        # Create attachment
        attachment = Attachment()
        attachment.file_content = FileContent(encoded_content)
        attachment.file_name = FileName(filename)
        attachment.file_type = FileType('application/json')
        attachment.disposition = Disposition('attachment')
        message.attachment = attachment
        
        # Send email
        sg = SendGridAPIClient(sendgrid_api_key)
        response = sg.send(message)
        
        if response.status_code == 202:
            logger.info(f"Backup email sent successfully to {backup_email}")
            return True
        else:
            logger.error(f"Backup email failed with status {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending backup email: {e}")
        return False


async def scheduled_backup_task():
    """Async task for scheduled backups"""
    logger.info("Starting scheduled backup...")
    try:
        backup_data = await create_backup_data()
        # Run email sending in thread pool since SendGrid is sync
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, send_backup_email, backup_data, "automatico")
        if result:
            logger.info("Scheduled backup completed successfully")
        else:
            logger.error("Scheduled backup failed to send email")
    except Exception as e:
        logger.error(f"Scheduled backup error: {e}")


def start_backup_scheduler():
    """Start the backup scheduler with cron jobs"""
    # Schedule backup at 8:00 and 20:00 every day
    scheduler.add_job(
        scheduled_backup_task,
        CronTrigger(hour=8, minute=0),
        id='backup_morning',
        replace_existing=True
    )
    scheduler.add_job(
        scheduled_backup_task,
        CronTrigger(hour=20, minute=0),
        id='backup_evening',
        replace_existing=True
    )
    scheduler.start()
    logger.info("Backup scheduler started - backups at 8:00 and 20:00")


# ============================================
# BACKUP API ENDPOINTS
# ============================================

@router.post("/backup/manual")
@limiter.limit(get_limit("backup"))
async def trigger_manual_backup(request: Request, background_tasks: BackgroundTasks):
    """Trigger a manual backup and send via email"""
    try:
        backup_data = await create_backup_data()
        
        # Count items
        total_items = sum(len(backup_data.get("data", {}).get(col, [])) for col in backup_data.get("data", {}).keys())
        
        # Send email in background
        background_tasks.add_task(send_backup_email, backup_data, "manual")
        
        # Save to backup history
        history_entry = {
            "id": f"backup-{uuid.uuid4().hex[:8]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "manual",
            "status": "success",
            "itemCount": total_items,
            "sentTo": os.environ.get('BACKUP_EMAIL', 'marioluiggihome@gmail.com')
        }
        await db.backup_history.insert_one(history_entry)
        
        # Auditoria
        audit.log(
            AuditAction.BACKUP_CREATE,
            resource_type="backup",
            resource_id=history_entry["id"],
            request=request,
            details={"type": "manual", "item_count": total_items}
        )
        
        return {
            "status": "success",
            "message": f"Backup enviado a {history_entry['sentTo']}",
            "itemCount": total_items,
            "timestamp": history_entry['timestamp']
        }
    except Exception as e:
        logger.error(f"Manual backup error: {e}")
        raise HTTPException(status_code=500, detail=f"Error al crear backup: {str(e)}")


@router.get("/backup/download")
@limiter.limit(get_limit("export"))
async def download_backup(request: Request):
    """Download backup as JSON file (for manual save to Google Drive)"""
    try:
        backup_data = await create_backup_data()
        
        # Auditoria
        audit.log(
            AuditAction.BACKUP_CREATE,
            resource_type="backup",
            request=request,
            details={"type": "download"}
        )
        
        return backup_data
    except Exception as e:
        logger.error(f"Download backup error: {e}")
        raise HTTPException(status_code=500, detail=f"Error al descargar backup: {str(e)}")


@router.post("/backup/restore")
@limiter.limit(get_limit("backup"))
async def restore_backup(request: Request, backup_data: Dict):
    """Restore data from a backup file"""
    try:
        if "data" not in backup_data:
            raise HTTPException(status_code=400, detail="Formato de backup invalido")
        
        restored_counts = {}
        
        # Colecciones permitidas para restaurar
        allowed_collections = [
            "users", "products", "despiece_products", "materials", 
            "projects", "settings", "clients", "opportunities",
            "activities", "calendar_events", "orders", "armario_projects"
        ]
        
        for collection_name, documents in backup_data["data"].items():
            if collection_name in allowed_collections:
                # Clear existing data
                await db[collection_name].delete_many({})
                
                # Insert backup data
                if documents:
                    await db[collection_name].insert_many(documents)
                
                restored_counts[collection_name] = len(documents)
                logger.info(f"Restored {collection_name}: {len(documents)} documents")
        
        return {
            "status": "success",
            "message": "Backup restaurado correctamente",
            "restored": restored_counts
        }
    except Exception as e:
        logger.error(f"Restore backup error: {e}")
        raise HTTPException(status_code=500, detail=f"Error al restaurar backup: {str(e)}")


@router.get("/backup/history")
async def get_backup_history():
    """Get backup history"""
    try:
        history = await db.backup_history.find({}, {"_id": 0}).sort("timestamp", -1).to_list(50)
        return history
    except Exception as e:
        logger.error(f"Get backup history error: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener historial: {str(e)}")


@router.get("/backup/status")
async def get_backup_status():
    """Get backup scheduler status"""
    jobs = scheduler.get_jobs()
    return {
        "scheduler_running": scheduler.running,
        "next_backups": [
            {
                "job_id": job.id,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None
            }
            for job in jobs
        ],
        "backup_email": os.environ.get('BACKUP_EMAIL', 'marioluiggihome@gmail.com')
    }
