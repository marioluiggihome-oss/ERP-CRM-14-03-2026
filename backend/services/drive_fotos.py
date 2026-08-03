"""
drive_fotos.py — Las fotos de los proyectos del Estudio 3D, en Google Drive.

Por qué: cada render guardado ocupa unos 300 KB en la base de datos y el plan de
MongoDB Atlas son 5 GB. Con las fotos en Drive, en la base de datos queda solo
una miniatura (~25 KB) y el enlace, y el archivo grande vive en una carpeta por
proyecto que además se puede abrir desde el propio Drive de la empresa.

Reutiliza la MISMA cuenta de servicio que las copias de seguridad
(`services/drive_backup.py`), así que no hay que configurar nada nuevo salvo,
si se quiere, una carpeta distinta:

  GOOGLE_DRIVE_RENDERS_FOLDER_ID   Carpeta donde crear una subcarpeta por
                                   proyecto. Si no se indica, se usa la misma
                                   carpeta de las copias (GOOGLE_DRIVE_FOLDER_ID).

Todo lo de aquí es SÍNCRONO (la librería de Google lo es): quien lo llame desde
código async debe usar `asyncio.to_thread`, como hace el servicio de copias.

Ninguna función lanza excepción hacia arriba: si Drive falla, devuelven
`{"ok": False, "error": ...}` y quien llama guarda la foto en la base de datos
como siempre. Una caída de Google no puede impedir guardar el trabajo.
"""
import base64
import io
import logging
import os
import re

from services import drive_backup

logger = logging.getLogger("drive_fotos")

MIME_CARPETA = "application/vnd.google-apps.folder"


def esta_configurado() -> bool:
    """Hay credenciales y carpeta donde escribir."""
    return bool(drive_backup._leer_credenciales()) and bool(_carpeta_raiz())


def _carpeta_raiz() -> str:
    return (os.environ.get("GOOGLE_DRIVE_RENDERS_FOLDER_ID")
            or os.environ.get("GOOGLE_DRIVE_FOLDER_ID") or "").strip()


def _limpia(nombre: str, por_defecto: str) -> str:
    """Nombre de carpeta/fichero utilizable: sin barras ni comillas."""
    limpio = re.sub(r'[\\/:*?"<>|]+', "-", str(nombre or "")).strip(" .-")
    return (limpio or por_defecto)[:120]


def carpeta_de_proyecto(nombre: str) -> dict:
    """Busca la carpeta del proyecto en Drive y, si no está, la crea."""
    raiz = _carpeta_raiz()
    if not raiz:
        return {"ok": False, "error": "Falta GOOGLE_DRIVE_FOLDER_ID."}
    nombre = _limpia(nombre, "Proyecto 3D")
    try:
        servicio = drive_backup._servicio()
        # El nombre va entre comillas simples en la consulta: se escapan las que traiga.
        seguro = nombre.replace("'", "\\'")
        res = servicio.files().list(
            q=f"'{raiz}' in parents and mimeType='{MIME_CARPETA}' "
              f"and name='{seguro}' and trashed=false",
            fields="files(id,name)", pageSize=5,
            supportsAllDrives=True, includeItemsFromAllDrives=True,
        ).execute()
        existentes = res.get("files", [])
        if existentes:
            return {"ok": True, "id": existentes[0]["id"], "nombre": nombre, "creada": False}
        carpeta = servicio.files().create(
            body={"name": nombre, "mimeType": MIME_CARPETA, "parents": [raiz]},
            fields="id,name", supportsAllDrives=True,
        ).execute()
        return {"ok": True, "id": carpeta["id"], "nombre": nombre, "creada": True}
    except Exception as e:
        logger.error("No se pudo preparar la carpeta '%s' en Drive: %s", nombre, e)
        return {"ok": False, "error": str(e)}


def trocear_data_url(data_url: str):
    """Separa una data URL en (bytes, mime). Devuelve (None, None) si no lo es."""
    if not isinstance(data_url, str) or not data_url.startswith("data:"):
        return None, None
    try:
        cabecera, datos = data_url.split(",", 1)
        mime = cabecera[5:].split(";")[0] or "image/jpeg"
        return base64.b64decode(datos), mime
    except Exception:
        return None, None


def subir_imagen(data_url: str, nombre: str, carpeta_id: str) -> dict:
    """Sube una imagen (data URL) a la carpeta indicada de Drive."""
    from googleapiclient.http import MediaIoBaseUpload

    datos, mime = trocear_data_url(data_url)
    if not datos:
        return {"ok": False, "error": "La imagen no es una data URL válida."}
    if not carpeta_id:
        return {"ok": False, "error": "Sin carpeta de proyecto en Drive."}
    extension = {"image/png": ".png", "image/webp": ".webp"}.get(mime, ".jpg")
    try:
        servicio = drive_backup._servicio()
        media = MediaIoBaseUpload(io.BytesIO(datos), mimetype=mime, resumable=False)
        f = servicio.files().create(
            body={"name": _limpia(nombre, "render") + extension, "parents": [carpeta_id]},
            media_body=media, fields="id,name,webViewLink,size", supportsAllDrives=True,
        ).execute()
        return {"ok": True, "id": f.get("id"), "nombre": f.get("name"),
                "enlace": f.get("webViewLink"), "tamano": f.get("size")}
    except Exception as e:
        logger.error("Fallo al subir una foto a Drive: %s", e)
        return {"ok": False, "error": str(e)}


def descargar_imagen(file_id: str) -> dict:
    """Descarga el contenido de una foto de Drive."""
    from googleapiclient.http import MediaIoBaseDownload

    try:
        servicio = drive_backup._servicio()
        meta = servicio.files().get(
            fileId=file_id, fields="mimeType,name", supportsAllDrives=True).execute()
        buf = io.BytesIO()
        bajada = MediaIoBaseDownload(buf, servicio.files().get_media(fileId=file_id))
        terminado = False
        while not terminado:
            _, terminado = bajada.next_chunk()
        return {"ok": True, "datos": buf.getvalue(),
                "mime": meta.get("mimeType") or "image/jpeg", "nombre": meta.get("name")}
    except Exception as e:
        logger.error("Fallo al descargar la foto %s de Drive: %s", file_id, e)
        return {"ok": False, "error": str(e)}


def a_papelera(file_id: str) -> dict:
    """Manda la foto a la papelera de Drive (recuperable), no la borra a fuego."""
    try:
        servicio = drive_backup._servicio()
        servicio.files().update(fileId=file_id, body={"trashed": True},
                                supportsAllDrives=True).execute()
        return {"ok": True}
    except Exception as e:
        logger.warning("No se pudo mandar a la papelera de Drive %s: %s", file_id, e)
        return {"ok": False, "error": str(e)}
