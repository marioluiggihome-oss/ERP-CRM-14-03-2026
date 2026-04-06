"""
Servicio de Backup Automático para LUIGGI HOME
- Backup diario de MongoDB
- Retención configurable
- Logs de operaciones
"""
import os
import asyncio
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
import logging
import json
import shutil

logger = logging.getLogger(__name__)

BACKUP_DIR = Path("/app/backups")
BACKUP_RETENTION_DAYS = 30  # Mantener backups de los últimos 30 días

class BackupService:
    def __init__(self, mongo_url: str, db_name: str):
        self.mongo_url = mongo_url
        self.db_name = db_name
        self.backup_dir = BACKUP_DIR
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self._scheduler_task = None
        
    async def create_backup(self) -> dict:
        """Crear un backup completo de la base de datos"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"luiggi_backup_{timestamp}"
        backup_path = self.backup_dir / backup_name
        
        try:
            # Crear directorio para este backup
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Ejecutar mongodump
            cmd = [
                "mongodump",
                f"--uri={self.mongo_url}",
                f"--db={self.db_name}",
                f"--out={backup_path}"
            ]
            
            logger.info(f"Iniciando backup: {backup_name}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                # Comprimir el backup
                archive_path = f"{backup_path}.tar.gz"
                shutil.make_archive(str(backup_path), 'gztar', backup_path)
                
                # Eliminar directorio sin comprimir
                shutil.rmtree(backup_path)
                
                # Obtener tamaño del archivo
                size_bytes = os.path.getsize(archive_path)
                size_mb = round(size_bytes / (1024 * 1024), 2)
                
                result = {
                    "success": True,
                    "backup_name": f"{backup_name}.tar.gz",
                    "path": archive_path,
                    "size_mb": size_mb,
                    "timestamp": datetime.now().isoformat(),
                    "message": f"Backup creado exitosamente: {size_mb} MB"
                }
                
                logger.info(f"Backup completado: {archive_path} ({size_mb} MB)")
                
                # Limpiar backups antiguos
                await self.cleanup_old_backups()
                
                return result
            else:
                error_msg = stderr.decode() if stderr else "Error desconocido"
                logger.error(f"Error en mongodump: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error creando backup: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def cleanup_old_backups(self):
        """Eliminar backups más antiguos que BACKUP_RETENTION_DAYS"""
        try:
            cutoff_date = datetime.now() - timedelta(days=BACKUP_RETENTION_DAYS)
            deleted_count = 0
            
            for file in self.backup_dir.glob("luiggi_backup_*.tar.gz"):
                # Extraer fecha del nombre del archivo
                try:
                    date_str = file.stem.replace("luiggi_backup_", "").split("_")[0]
                    file_date = datetime.strptime(date_str, "%Y%m%d")
                    
                    if file_date < cutoff_date:
                        file.unlink()
                        deleted_count += 1
                        logger.info(f"Backup antiguo eliminado: {file.name}")
                except (ValueError, OSError):
                    continue
            
            if deleted_count > 0:
                logger.info(f"Limpieza completada: {deleted_count} backups antiguos eliminados")
                
        except Exception as e:
            logger.error(f"Error en limpieza de backups: {str(e)}")
    
    def list_backups(self) -> list:
        """Listar todos los backups disponibles"""
        backups = []
        for file in sorted(self.backup_dir.glob("luiggi_backup_*.tar.gz"), reverse=True):
            try:
                size_bytes = file.stat().st_size
                size_mb = round(size_bytes / (1024 * 1024), 2)
                created = datetime.fromtimestamp(file.stat().st_mtime)
                
                backups.append({
                    "name": file.name,
                    "size_mb": size_mb,
                    "created": created.isoformat(),
                    "path": str(file)
                })
            except (OSError, IOError):
                continue
        
        return backups
    
    async def restore_backup(self, backup_name: str) -> dict:
        """Restaurar un backup específico"""
        backup_path = self.backup_dir / backup_name
        
        if not backup_path.exists():
            return {"success": False, "error": "Backup no encontrado"}
        
        try:
            # Extraer el archivo
            extract_dir = self.backup_dir / "restore_temp"
            shutil.unpack_archive(backup_path, extract_dir)
            
            # Encontrar el directorio de la base de datos
            db_dir = extract_dir / f"luiggi_backup_{backup_name.replace('.tar.gz', '').replace('luiggi_backup_', '')}" / self.db_name
            
            if not db_dir.exists():
                # Buscar en subdirectorios
                for d in extract_dir.rglob(self.db_name):
                    if d.is_dir():
                        db_dir = d
                        break
            
            # Ejecutar mongorestore
            cmd = [
                "mongorestore",
                f"--uri={self.mongo_url}",
                f"--db={self.db_name}",
                "--drop",  # Eliminar colecciones existentes antes de restaurar
                str(db_dir)
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            # Limpiar directorio temporal
            shutil.rmtree(extract_dir)
            
            if process.returncode == 0:
                return {
                    "success": True,
                    "message": f"Backup {backup_name} restaurado exitosamente"
                }
            else:
                return {
                    "success": False,
                    "error": stderr.decode() if stderr else "Error desconocido"
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def start_scheduler(self, hour: int = 3):
        """Iniciar el programador de backups diarios (por defecto a las 3:00 AM)"""
        async def scheduler_loop():
            while True:
                now = datetime.now()
                # Calcular tiempo hasta la próxima ejecución
                next_run = now.replace(hour=hour, minute=0, second=0, microsecond=0)
                if next_run <= now:
                    next_run += timedelta(days=1)
                
                wait_seconds = (next_run - now).total_seconds()
                logger.info(f"Próximo backup programado para: {next_run.isoformat()}")
                
                await asyncio.sleep(wait_seconds)
                
                # Ejecutar backup
                logger.info("Ejecutando backup programado...")
                result = await self.create_backup()
                
                if result["success"]:
                    logger.info(f"Backup programado completado: {result['backup_name']}")
                else:
                    logger.error(f"Error en backup programado: {result.get('error')}")
        
        self._scheduler_task = asyncio.create_task(scheduler_loop())
        logger.info(f"Programador de backups iniciado (diario a las {hour}:00)")
    
    def stop_scheduler(self):
        """Detener el programador de backups"""
        if self._scheduler_task:
            self._scheduler_task.cancel()
            logger.info("Programador de backups detenido")


# Instancia global (se inicializa en server.py)
backup_service: BackupService = None

def init_backup_service(mongo_url: str, db_name: str) -> BackupService:
    global backup_service
    backup_service = BackupService(mongo_url, db_name)
    return backup_service

def get_backup_service() -> BackupService:
    """Obtener instancia del servicio de backup"""
    return backup_service
