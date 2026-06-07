"""
Backup and Export System for LUIGGI HOME
Exports all data and code in ZIP format
Includes daily automated backups with email notification
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse, JSONResponse
from services.jwt_service import require_admin
import os
import zipfile
import shutil
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import json
from bson import ObjectId, json_util
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import resend
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/backup", tags=["Backup"])

# Scheduler for automated backups
scheduler = AsyncIOScheduler()

# Email configuration
BACKUP_EMAIL = os.environ.get('BACKUP_EMAIL', 'marioluiggihome@gmail.com')
RESEND_API_KEY = os.environ.get('RESEND_API_KEY')

def start_backup_scheduler():
    """Start the backup scheduler if not already running"""
    if not scheduler.running:
        # Schedule daily backup at 3:00 AM
        scheduler.add_job(
            daily_backup_job,
            CronTrigger(hour=3, minute=0),
            id='daily_backup',
            replace_existing=True
        )
        scheduler.start()
        logger.info("✅ Backup scheduler started - Daily backup at 3:00 AM")

async def daily_backup_job():
    """Execute daily backup and send email"""
    try:
        logger.info("🔄 Starting daily backup...")
        result = await create_daily_backup_with_email()
        logger.info(f"✅ Daily backup completed: {result}")
    except Exception as e:
        logger.error(f"❌ Daily backup failed: {e}")

async def create_daily_backup_with_email():
    """Create backup and send via email"""
    from motor.motor_asyncio import AsyncIOMotorClient
    
    MONGO_URL = os.environ.get('MONGO_URL')
    DB_NAME = os.environ.get('DB_NAME', 'luiggi_home')
    
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"luiggi_backup_{timestamp}"
    temp_dir = f"/tmp/{backup_name}"
    os.makedirs(temp_dir, exist_ok=True)
    
    # Export MongoDB
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    collections = await db.list_collection_names()
    
    total_docs = 0
    for coll_name in collections:
        docs = await db[coll_name].find({}).to_list(length=None)
        json_docs = json.loads(json_util.dumps(docs))
        with open(f"{temp_dir}/{coll_name}.json", 'w', encoding='utf-8') as f:
            json.dump(json_docs, f, ensure_ascii=False)
        total_docs += len(docs)
    
    client.close()
    
    # Create ZIP
    zip_path = f"{BACKUP_DIR}/{backup_name}.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in os.listdir(temp_dir):
            zipf.write(f"{temp_dir}/{file}", file)
    
    shutil.rmtree(temp_dir)
    size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    
    # Send email with backup info
    if RESEND_API_KEY:
        try:
            resend.api_key = RESEND_API_KEY
            
            # Read backup file for attachment (if small enough)
            attachment_data = None
            if size_mb < 10:  # Only attach if less than 10MB
                with open(zip_path, 'rb') as f:
                    import base64
                    attachment_data = base64.b64encode(f.read()).decode('utf-8')
            
            email_body = f"""
            <h2>🔒 Backup Diario - LUIGGI HOME ERP</h2>
            <p><strong>Fecha:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
            <p><strong>Archivo:</strong> {backup_name}.zip</p>
            <p><strong>Tamaño:</strong> {size_mb:.2f} MB</p>
            <p><strong>Documentos:</strong> {total_docs}</p>
            <p><strong>Colecciones:</strong> {len(collections)}</p>
            <hr>
            <p>{'El backup está adjunto a este email.' if attachment_data else 'El backup es demasiado grande para adjuntar. Descárgalo desde el panel de administración.'}</p>
            <p style="color: #666; font-size: 12px;">Este es un backup automático generado por el sistema LUIGGI HOME ERP.</p>
            """
            
            email_params = {
                "from": "LUIGGI HOME <backups@luiggihome.es>",
                "to": [BACKUP_EMAIL],
                "subject": f"🔒 Backup Diario LUIGGI HOME - {datetime.now().strftime('%d/%m/%Y')}",
                "html": email_body
            }
            
            if attachment_data:
                email_params["attachments"] = [{
                    "filename": f"{backup_name}.zip",
                    "content": attachment_data
                }]
            
            resend.Emails.send(email_params)
            logger.info(f"📧 Backup email sent to {BACKUP_EMAIL}")
        except Exception as e:
            logger.error(f"Failed to send backup email: {e}")
    
    # Keep only last 7 backups
    cleanup_old_backups(7)
    
    return {"filename": f"{backup_name}.zip", "size_mb": size_mb, "documents": total_docs}

def cleanup_old_backups(keep_count=7):
    """Remove old backups, keeping only the most recent ones"""
    try:
        backups = []
        for f in os.listdir(BACKUP_DIR):
            if f.endswith('.zip') and f.startswith('luiggi_backup_'):
                filepath = os.path.join(BACKUP_DIR, f)
                backups.append((filepath, os.path.getctime(filepath)))
        
        # Sort by creation time, newest first
        backups.sort(key=lambda x: x[1], reverse=True)
        
        # Remove old backups
        for filepath, _ in backups[keep_count:]:
            os.remove(filepath)
            logger.info(f"🗑️ Removed old backup: {filepath}")
    except Exception as e:
        logger.error(f"Failed to cleanup old backups: {e}")

MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME', 'luiggi_home')
BACKUP_DIR = '/app/backups'

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)

@router.get("/status")
async def backup_status():
    """Check backup system status and list existing backups"""
    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        backups = []
        for f in os.listdir(BACKUP_DIR):
            if f.endswith('.zip'):
                filepath = os.path.join(BACKUP_DIR, f)
                size_mb = os.path.getsize(filepath) / (1024 * 1024)
                backups.append({
                    "filename": f,
                    "size_mb": round(size_mb, 2),
                    "created": datetime.fromtimestamp(os.path.getctime(filepath)).isoformat()
                })
        return {"status": "ready", "existing_backups": sorted(backups, key=lambda x: x['created'], reverse=True)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/create")
async def create_full_backup():
    """Create a complete backup of code and database"""
    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"luiggi_home_backup_{timestamp}"
        temp_dir = f"/tmp/{backup_name}"
        
        # Create temp directory structure
        os.makedirs(f"{temp_dir}/database", exist_ok=True)
        os.makedirs(f"{temp_dir}/code", exist_ok=True)
        
        # 1. Export MongoDB collections
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        
        collections = await db.list_collection_names()
        db_stats = {}
        
        for collection_name in collections:
            try:
                collection = db[collection_name]
                documents = await collection.find({}).to_list(length=None)
                
                # Convert to JSON-serializable format
                json_docs = json.loads(json_util.dumps(documents))
                
                # Save to file
                with open(f"{temp_dir}/database/{collection_name}.json", 'w', encoding='utf-8') as f:
                    json.dump(json_docs, f, ensure_ascii=False, indent=2)
                
                db_stats[collection_name] = len(documents)
            except Exception as e:
                db_stats[collection_name] = f"Error: {str(e)}"
        
        client.close()
        
        # 2. Copy code (excluding node_modules, __pycache__, .git, backups)
        def should_exclude(path):
            excludes = ['node_modules', '__pycache__', '.git', 'backups', 'build', '.next', 'venv', '.emergent']
            return any(exc in path for exc in excludes)
        
        # Copy backend
        for item in os.listdir('/app/backend'):
            src = f'/app/backend/{item}'
            if not should_exclude(src):
                dst = f'{temp_dir}/code/backend/{item}'
                if os.path.isdir(src):
                    shutil.copytree(src, dst, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
                else:
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    shutil.copy2(src, dst)
        
        # Copy frontend (excluding node_modules and build)
        for item in os.listdir('/app/frontend'):
            src = f'/app/frontend/{item}'
            if not should_exclude(src) and item not in ['node_modules', 'build']:
                dst = f'{temp_dir}/code/frontend/{item}'
                if os.path.isdir(src):
                    shutil.copytree(src, dst, ignore=shutil.ignore_patterns('node_modules', 'build', '.cache'))
                else:
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    shutil.copy2(src, dst)
        
        # Copy memory/docs if exists
        if os.path.exists('/app/memory'):
            shutil.copytree('/app/memory', f'{temp_dir}/code/memory', ignore=shutil.ignore_patterns('__pycache__'))
        
        # 3. Create info file
        info = {
            "backup_date": datetime.now().isoformat(),
            "database_name": DB_NAME,
            "collections_exported": db_stats,
            "total_collections": len(collections),
            "app_name": "LUIGGI HOME ERP"
        }
        with open(f"{temp_dir}/backup_info.json", 'w', encoding='utf-8') as f:
            json.dump(info, f, ensure_ascii=False, indent=2)
        
        # 4. Create ZIP file
        zip_path = f"{BACKUP_DIR}/{backup_name}.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_name = os.path.relpath(file_path, temp_dir)
                    zipf.write(file_path, arc_name)
        
        # 5. Cleanup temp directory
        shutil.rmtree(temp_dir)
        
        # Get final size
        size_mb = os.path.getsize(zip_path) / (1024 * 1024)
        
        return {
            "success": True,
            "filename": f"{backup_name}.zip",
            "size_mb": round(size_mb, 2),
            "collections_exported": db_stats,
            "download_url": f"/api/backup/download/{backup_name}.zip"
        }
        
    except Exception as e:
        import traceback
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}

@router.get("/download/{filename}")
async def download_backup(filename: str):
    """Download a backup file"""
    filepath = os.path.join(BACKUP_DIR, filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Backup file not found")
    
    if not filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    return FileResponse(
        path=filepath,
        filename=filename,
        media_type='application/zip'
    )

@router.delete("/delete/{filename}")
async def delete_backup(filename: str):
    """Delete a backup file"""
    filepath = os.path.join(BACKUP_DIR, filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Backup file not found")
    
    os.remove(filepath)
    return {"success": True, "message": f"Backup {filename} deleted"}

@router.api_route("/send-email", methods=["GET", "POST"])
async def send_backup_email():
    """Crear backup completo (JSON de toda la BD) y enviarlo por email.

    Acepta GET y POST para que funcione tanto desde el boton del panel (POST)
    como pegando la URL en el navegador (GET).
    """
    try:
        result = await create_daily_backup_with_email()
        return {
            "success": True,
            "message": f"Backup creado y enviado a {BACKUP_EMAIL}",
            "backup": result
        }
    except Exception as e:
        import traceback
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}

@router.get("/scheduler-status")
async def get_scheduler_status():
    """Get backup scheduler status"""
    jobs = []
    if scheduler.running:
        for job in scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "next_run": str(job.next_run_time) if job.next_run_time else None
            })
    return {
        "scheduler_running": scheduler.running,
        "backup_email": BACKUP_EMAIL,
        "jobs": jobs
    }

@router.get("/download-part/{filename}")
async def download_backup_part(filename: str):
    """Download a backup part file"""
    filepath = os.path.join(BACKUP_DIR, "parts", filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Backup part not found")
    
    return FileResponse(
        path=filepath,
        filename=filename,
        media_type='application/octet-stream'
    )

@router.get("/download-collections/{filename}")
async def download_collections_backup(filename: str):
    """Download collections backup file"""
    filepath = os.path.join(BACKUP_DIR, filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Collections backup not found")
    
    return FileResponse(
        path=filepath,
        filename=filename,
        media_type='application/zip'
    )

@router.get("/list-parts")
async def list_backup_parts():
    """List available backup parts"""
    parts_dir = os.path.join(BACKUP_DIR, "parts")
    if not os.path.exists(parts_dir):
        return {"parts": []}
    
    parts = []
    for f in sorted(os.listdir(parts_dir)):
        filepath = os.path.join(parts_dir, f)
        size_mb = os.path.getsize(filepath) / (1024 * 1024)
        parts.append({
            "filename": f,
            "size_mb": round(size_mb, 2),
            "download_url": f"/api/backup/download-part/{f}"
        })
    return {"parts": parts}

@router.get("/export-db-only")
async def export_database_only(user=Depends(require_admin)):
    """Export only the database (smaller file) — solo ADMIN (vuelca toda la BD)"""
    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"luiggi_db_backup_{timestamp}"
        temp_dir = f"/tmp/{backup_name}"
        os.makedirs(temp_dir, exist_ok=True)
        
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        
        collections = await db.list_collection_names()
        db_stats = {}
        
        for collection_name in collections:
            try:
                collection = db[collection_name]
                documents = await collection.find({}).to_list(length=None)
                json_docs = json.loads(json_util.dumps(documents))
                
                with open(f"{temp_dir}/{collection_name}.json", 'w', encoding='utf-8') as f:
                    json.dump(json_docs, f, ensure_ascii=False, indent=2)
                
                db_stats[collection_name] = len(documents)
            except Exception as e:
                db_stats[collection_name] = f"Error: {str(e)}"
        
        client.close()
        
        # Create ZIP
        zip_path = f"{BACKUP_DIR}/{backup_name}.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in os.listdir(temp_dir):
                zipf.write(f"{temp_dir}/{file}", file)
        
        shutil.rmtree(temp_dir)
        size_mb = os.path.getsize(zip_path) / (1024 * 1024)
        
        return {
            "success": True,
            "filename": f"{backup_name}.zip",
            "size_mb": round(size_mb, 2),
            "collections_exported": db_stats,
            "download_url": f"/api/backup/download/{backup_name}.zip"
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}
