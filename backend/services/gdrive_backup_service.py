"""
Servicio de backup de MongoDB a Google Drive
Colecciones críticas: users, projects, clients, products, opportunities
"""
import os
import json
import logging
from datetime import datetime, timezone
from io import BytesIO
from typing import List

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/drive.file']
FOLDER_ID = "1IhmzchwLX9c8gNrhbRIHVVvZhCrYt8_o"
CRITICAL_COLLECTIONS = ["users", "projects", "clients", "products", "opportunities"]


def get_drive_service():
    """Inicializa el cliente de Google Drive con la Service Account."""
    creds_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not creds_json:
        raise Exception("GOOGLE_SERVICE_ACCOUNT_JSON no configurado en Railway")
    
    creds_dict = json.loads(creds_json)
    credentials = service_account.Credentials.from_service_account_info(
        creds_dict, scopes=SCOPES
    )
    return build('drive', 'v3', credentials=credentials)


async def run_gdrive_backup(db) -> dict:
    """
    Exporta las colecciones críticas de MongoDB y las sube a Google Drive.
    Mantiene solo los últimos 7 backups por colección.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    results = {"success": [], "errors": [], "timestamp": timestamp}

    try:
        service = get_drive_service()
    except Exception as e:
        logger.error(f"Error conectando con Google Drive: {e}")
        results["errors"].append(f"Conexión Drive: {str(e)}")
        return results

    for collection_name in CRITICAL_COLLECTIONS:
        try:
            # Exportar colección a JSON
            collection = db[collection_name]
            documents = await collection.find({}, {"_id": 0}).to_list(50000)

            # Quitar passwords de users
            if collection_name == "users":
                for doc in documents:
                    doc.pop("password", None)

            json_content = json.dumps(documents, ensure_ascii=False, indent=2, default=str)
            file_bytes = BytesIO(json_content.encode("utf-8"))

            # Nombre del archivo
            filename = f"backup_{collection_name}_{timestamp}.json"

            # Subir a Google Drive
            file_metadata = {
                "name": filename,
                "parents": [FOLDER_ID]
            }
            media = MediaIoBaseUpload(file_bytes, mimetype="application/json")
            service.files().create(
                body=file_metadata,
                media_body=media,
                fields="id, name"
            ).execute()

            logger.info(f"✅ Backup subido: {filename} ({len(documents)} documentos)")
            results["success"].append({
                "collection": collection_name,
                "file": filename,
                "documents": len(documents)
            })

            # Limpiar backups antiguos (mantener últimos 7)
            await cleanup_old_backups(service, collection_name, keep=7)

        except Exception as e:
            logger.error(f"Error haciendo backup de {collection_name}: {e}")
            results["errors"].append(f"{collection_name}: {str(e)}")

    logger.info(f"Backup completado: {len(results['success'])} OK, {len(results['errors'])} errores")
    return results


async def cleanup_old_backups(service, collection_name: str, keep: int = 7):
    """Elimina backups antiguos manteniendo solo los más recientes."""
    try:
        query = f"'{FOLDER_ID}' in parents and name contains 'backup_{collection_name}_' and trashed=false"
        response = service.files().list(
            q=query,
            orderBy="createdTime desc",
            fields="files(id, name, createdTime)"
        ).execute()

        files = response.get("files", [])
        if len(files) > keep:
            for old_file in files[keep:]:
                service.files().delete(fileId=old_file["id"]).execute()
                logger.info(f"🗑️ Backup antiguo eliminado: {old_file['name']}")
    except Exception as e:
        logger.warning(f"Error limpiando backups antiguos de {collection_name}: {e}")
