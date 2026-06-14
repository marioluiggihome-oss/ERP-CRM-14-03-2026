"""
Servicio de procesamiento de archivos asincrónico.
Maneja validación, compresión y almacenamiento de archivos.
"""

import os
import logging
import base64
from typing import Optional, List, Dict, Any
from fastapi import UploadFile
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class FileValidationConfig:
    \"\"\"Configuración de validación de archivos\"\"\"
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
    ALLOWED_MIME_TYPES = {
        \"application/pdf\",
        \"image/jpeg\",
        \"image/png\",
        \"image/gif\",
        \"application/msword\",
        \"application/vnd.openxmlformats-officedocument.wordprocessingml.document\",
        \"application/vnd.ms-excel\",
        \"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet\",
        \"text/plain\",
        \"application/zip\",
        \"application/x-rar-compressed\"
    }
    ALLOWED_EXTENSIONS = {
        \"pdf\", \"jpg\", \"jpeg\", \"png\", \"gif\",
        \"doc\", \"docx\", \"xls\", \"xlsx\",
        \"txt\", \"zip\", \"rar\"
    }


class FileService:
    \"\"\"Servicio para procesamiento de archivos\"\"\"
    
    def __init__(self, config: FileValidationConfig = None):
        self.config = config or FileValidationConfig()
    
    async def validate_and_process_file(
        self,
        file: UploadFile,
        max_size: Optional[int] = None
    ) -> Dict[str, Any]:
        \"\"\"
        Validar y procesar un archivo cargado.
        
        Validaciones:
        - Tamaño máximo
        - Tipo MIME permitido
        - Extensión permitida
        \"\"\"
        try:
            if not file or not file.filename:
                return {
                    \"success\": False,
                    \"error\": \"No se proporcionó archivo\"
                }
            
            # Validar extensión
            file_ext = file.filename.split('.')[-1].lower()
            if file_ext not in self.config.ALLOWED_EXTENSIONS:
                return {
                    \"success\": False,
                    \"error\": f\"Extensión no permitida: {file_ext}. Extensiones permitidas: {', '.join(self.config.ALLOWED_EXTENSIONS)}\"
                }
            
            # Leer contenido del archivo
            content = await file.read()
            
            # Validar tamaño
            max_size = max_size or self.config.MAX_FILE_SIZE
            if len(content) > max_size:
                return {
                    \"success\": False,
                    \"error\": f\"Archivo demasiado grande. Máximo: {max_size / 1024 / 1024:.1f} MB\"
                }
            
            # Validar tipo MIME
            mime_type = file.content_type or \"application/octet-stream\"
            if mime_type not in self.config.ALLOWED_MIME_TYPES:
                logger.warning(f\"Unexpected MIME type: {mime_type} for file {file.filename}\")
            
            # Procesar archivo
            return {
                \"success\": True,
                \"filename\": file.filename,
                \"content_type\": mime_type,
                \"size\": len(content),
                \"content\": content,
                \"encoded\": base64.b64encode(content).decode(),
                \"processed_at\": datetime.now(timezone.utc).isoformat()
            }
        
        except Exception as e:
            logger.error(f\"Error processing file {file.filename}: {str(e)}\", exc_info=True)
            return {
                \"success\": False,
                \"error\": f\"Error procesando archivo: {str(e)}\"
            }
    
    async def process_multiple_files(
        self,
        files: List[Optional[UploadFile]],
        max_size: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        \"\"\"Procesar múltiples archivos de forma asincrónica\"\"\"
        processed_files = []
        
        for file in files:
            if file and file.filename:
                result = await self.validate_and_process_file(file, max_size)
                if result[\"success\"]:
                    processed_files.append(result)
                else:
                    logger.warning(f\"Skipped file {file.filename}: {result['error']}\")
        
        return processed_files
    
    def get_file_info(self, processed_file: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"Extraer información del archivo procesado sin el contenido\"\"\"
        return {
            \"filename\": processed_file.get(\"filename\"),
            \"content_type\": processed_file.get(\"content_type\"),
            \"size\": processed_file.get(\"size\"),
            \"processed_at\": processed_file.get(\"processed_at\")
        }


# Singleton para reutilizar la instancia
_file_service: Optional[FileService] = None


def get_file_service(config: FileValidationConfig = None) -> FileService:
    \"\"\"Obtener instancia del servicio de archivos\"\"\"
    global _file_service
    if _file_service is None:
        _file_service = FileService(config)
    return _file_service
