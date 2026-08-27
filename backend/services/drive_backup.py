# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
drive_backup.py — Sube las copias de seguridad a Google Drive.

Por qué cuenta de servicio y no OAuth de usuario: la copia diaria corre sola, sin
nadie delante. Un token OAuth caduca o se revoca y la copia dejaría de subirse en
silencio; una cuenta de servicio no.

Configuración (variables de entorno en Railway):
  GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON  El JSON de la clave de la cuenta de servicio.
                                     Admite el JSON en crudo o codificado en base64.
  GOOGLE_DRIVE_FOLDER_ID             ID de la carpeta de Drive donde dejar las copias
                                     (de la URL: /drive/folders/<ESTE_ID>).
                                     Esa carpeta debe estar COMPARTIDA con el email
                                     de la cuenta de servicio, con permiso de Editor.
"""
import base64
import json
import logging
import os

logger = logging.getLogger("drive_backup")

SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def _leer_credenciales():
    """Devuelve el dict de credenciales de la cuenta de servicio, o None."""
    raw = (os.environ.get("GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON") or "").strip()
    if not raw:
        return None
    # Admite tanto el JSON pegado tal cual como en base64 (más cómodo en Railway,
    # que a veces maltrata los saltos de línea de la clave privada).
    if not raw.lstrip().startswith("{"):
        try:
            raw = base64.b64decode(raw).decode("utf-8")
        except Exception:
            logger.error("GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON no es JSON ni base64 válido.")
            return None
    try:
        return json.loads(raw)
    except Exception as e:
        logger.error("GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON ilegible: %s", e)
        return None


def esta_configurado() -> bool:
    return bool(_leer_credenciales()) and bool(os.environ.get("GOOGLE_DRIVE_FOLDER_ID"))


def estado() -> dict:
    """Estado de la integración, para mostrarlo en la app sin exponer secretos."""
    cred = _leer_credenciales()
    carpeta = (os.environ.get("GOOGLE_DRIVE_FOLDER_ID") or "").strip()
    return {
        "configurado": bool(cred) and bool(carpeta),
        "tieneCredenciales": bool(cred),
        "tieneCarpeta": bool(carpeta),
        "cuentaServicio": (cred or {}).get("client_email", ""),
        "carpetaId": carpeta,
    }


def _servicio():
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    cred = _leer_credenciales()
    if not cred:
        raise RuntimeError("Falta GOOGLE_DRIVE_SERVICE_ACCOUNT_JSON.")
    creds = service_account.Credentials.from_service_account_info(cred, scopes=SCOPES)
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def subir_fichero(ruta_local: str, nombre: str = None) -> dict:
    """Sube un fichero a la carpeta de Drive configurada.

    Devuelve {ok, id, nombre, enlace} o {ok: False, error}. No lanza excepción:
    el fallo al subir no debe tumbar el proceso de backup, pero SÍ debe verse.
    """
    from googleapiclient.http import MediaFileUpload

    carpeta = (os.environ.get("GOOGLE_DRIVE_FOLDER_ID") or "").strip()
    if not carpeta:
        return {"ok": False, "error": "Falta GOOGLE_DRIVE_FOLDER_ID."}
    if not os.path.exists(ruta_local):
        return {"ok": False, "error": f"No existe el fichero {ruta_local}."}

    try:
        servicio = _servicio()
        meta = {"name": nombre or os.path.basename(ruta_local), "parents": [carpeta]}
        # resumable=True: aguanta ficheros grandes y cortes de red.
        media = MediaFileUpload(ruta_local, mimetype="application/zip", resumable=True)
        f = servicio.files().create(
            body=meta, media_body=media, fields="id,name,webViewLink,size",
            supportsAllDrives=True,
        ).execute()
        logger.info("Copia subida a Drive: %s (%s bytes)", f.get("name"), f.get("size"))
        return {"ok": True, "id": f.get("id"), "nombre": f.get("name"),
                "enlace": f.get("webViewLink"), "tamano": f.get("size")}
    except Exception as e:
        logger.error("Fallo al subir la copia a Drive: %s", e)
        return {"ok": False, "error": str(e)}


def limpiar_antiguas(conservar: int = 30) -> dict:
    """Deja solo las `conservar` copias más recientes en la carpeta de Drive."""
    try:
        carpeta = (os.environ.get("GOOGLE_DRIVE_FOLDER_ID") or "").strip()
        if not carpeta:
            return {"ok": False, "error": "Falta GOOGLE_DRIVE_FOLDER_ID."}
        servicio = _servicio()
        res = servicio.files().list(
            q=f"'{carpeta}' in parents and trashed=false and name contains 'luiggi'",
            orderBy="createdTime desc", pageSize=200,
            fields="files(id,name,createdTime)", supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        ).execute()
        ficheros = res.get("files", [])
        borrados = 0
        for f in ficheros[conservar:]:
            try:
                servicio.files().delete(fileId=f["id"], supportsAllDrives=True).execute()
                borrados += 1
            except Exception as e:
                logger.warning("No se pudo borrar %s de Drive: %s", f.get("name"), e)
        return {"ok": True, "encontradas": len(ficheros), "borradas": borrados}
    except Exception as e:
        logger.error("limpiar_antiguas Drive: %s", e)
        return {"ok": False, "error": str(e)}
