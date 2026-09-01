# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
LuiggiAI Engine - API Router
==============================
Endpoints públicos del motor de IA white-label.
Todos los endpoints requieren autenticación JWT.

Endpoints:
- GET  /api/ai-engine/status         → Health check del motor
- GET  /api/ai-engine/materials      → Catálogo de materiales
- POST /api/ai-engine/render         → Generar render 3D (texto libre o voz)
- POST /api/ai-engine/render/params  → Generar render 3D (parámetros explícitos)
- POST /api/ai-engine/transcribe     → Transcribir audio a texto
- POST /api/ai-engine/analyze        → Analizar documento
- GET  /api/ai-engine/task/{task_id} → Consultar estado de tarea
"""

import asyncio
import hashlib
import logging
import io
import os
import uuid
from datetime import datetime, timezone
from urllib.parse import urlparse
from typing import Optional, List
import httpx
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Header
from fastapi.responses import Response
from pydantic import BaseModel, Field

from services.jwt_service import require_auth, verify_access_token
from services.luiggi_ai import get_engine, get_render_service, get_ai_config
from services.db_client import get_db as _get_db

try:
    from services.jwt_service import get_current_user, ADMIN_ROLE_FLAGS
except Exception:  # pragma: no cover
    async def get_current_user():
        return None
    ADMIN_ROLE_FLAGS = ["isAdmin", "isGerente", "isDirectorComercial"]

logger = logging.getLogger("luiggi_ai.router")

ai_engine_router = APIRouter(prefix="/ai-engine", tags=["LuiggiAI Engine"])

# Metadatos útiles para diagnóstico interno que no deben viajar al navegador.
# Se conservan en logs/servicios y se eliminan únicamente de la respuesta pública.
_CAMPOS_TECNICOS_RENDER = {
    "engine", "provider", "prompt_used", "model", "model_used",
    "motor", "motorUsado", "motorDeRespaldo", "modelo_pedido",
}


def limpiar_respuesta_render(valor):
    """Retira proveedor/modelo/prompt de una respuesta antes de exponerla."""
    if isinstance(valor, list):
        return [limpiar_respuesta_render(item) for item in valor]
    if not isinstance(valor, dict):
        return valor
    limpia = {}
    for clave, contenido in valor.items():
        if clave in _CAMPOS_TECNICOS_RENDER:
            continue
        if clave in {"error", "detail", "message"} and isinstance(contenido, str):
            if any(p in contenido.lower() for p in (
                "gemini", "manus", "openai", "anthropic", "claude", "flux",
                "banana", "motor", "modelo", "proveedor", "provider",
            )):
                limpia[clave] = "No se pudo completar la operación. Inténtalo de nuevo."
                continue
        limpia[clave] = limpiar_respuesta_render(contenido)
    return limpia

_db = _get_db()  # cliente MongoDB compartido (singleton)


# ─── Permisos por tipo de proyecto de Estudio 3D ────────────────────────────
_ESTUDIO3D_TIPOS = {"cocina", "armario", "bano", "otro"}
_ESTUDIO3D_ALIASES = {
    "cocina": "cocina", "kitchen": "cocina",
    "armario": "armario", "vestidor": "armario", "closet": "armario",
    "bano": "bano", "baño": "bano", "bathroom": "bano",
    "otro": "otro", "mueble": "otro", "furniture": "otro",
}


def _normalizar_tipo_estudio3d(value: Optional[str]) -> str:
    return _ESTUDIO3D_ALIASES.get(str(value or "cocina").strip().lower(), "cocina")


def _tipos_contratados(value) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(tipo).strip().lower() for tipo in value if str(tipo).strip().lower() in _ESTUDIO3D_TIPOS]


async def exigir_tipo_estudio3d(user: dict, project_type: Optional[str]) -> str:
    """Bloquea por API los renders de tipos que el cliente no tiene contratados."""
    tipo = _normalizar_tipo_estudio3d(project_type)
    if any(user.get(flag) for flag in ADMIN_ROLE_FLAGS):
        return tipo
    full = await _db.users.find_one(
        {"id": user.get("id")},
        {"_id": 0, "estudio3dTipos": 1, "linkedStudio3kAdminId": 1},
    ) or {}
    permitidos = _tipos_contratados(full.get("estudio3dTipos"))
    if not permitidos and full.get("linkedStudio3kAdminId"):
        admin_estudio = await _db.users.find_one(
            {"id": full.get("linkedStudio3kAdminId")},
            {"_id": 0, "estudio3dTipos": 1},
        ) or {}
        permitidos = _tipos_contratados(admin_estudio.get("estudio3dTipos"))
    if permitidos and tipo not in permitidos:
        etiquetas = {"cocina": "Cocina", "armario": "Armario / Vestidor", "bano": "Baño", "otro": "Otro mueble"}
        disponibles = ", ".join(etiquetas.get(item, item) for item in permitidos)
        raise HTTPException(
            status_code=403,
            detail=f"No tienes contratado el tipo «{etiquetas[tipo]}». Tipos disponibles: {disponibles}.",
        )
    return tipo


# ─── Proyectos de render 3D (guardar / historial persistente) ─────────────────
@ai_engine_router.post("/designs")
async def save_render_design(payload: dict, current_user: Optional[dict] = Depends(get_current_user)):
    """Guarda (o actualiza) un proyecto de render 3D del usuario."""
    p = payload or {}
    oid = p.get("id") or f"r3d-{uuid.uuid4().hex[:10]}"
    now = datetime.now(timezone.utc).isoformat()
    # `medidas`, `distribucion` y `tipo3d` van en la proyección A PROPÓSITO: de
    # ellas se parte para no pisarlas cuando esta llamada no las traiga. Si se
    # quitan de aquí, la conservación de abajo lee `None` y las borra siempre.
    existing = await _db.render3d_designs.find_one(
        {"id": oid},
        {"_id": 0, "createdAt": 1, "userId": 1,
         "medidas": 1, "distribucion": 1, "tipo3d": 1, "relacionMV": 1})
    if existing and existing.get("userId") and current_user and current_user.get("id") \
       and existing["userId"] != current_user["id"] and not any(current_user.get(f) for f in ADMIN_ROLE_FLAGS):
        raise HTTPException(status_code=403, detail="Sin acceso a este proyecto")
    doc = {
        "id": oid,
        "userId": (existing or {}).get("userId") or (current_user or {}).get("id") or "anonymous",
        "cliente": str(p.get("cliente") or ""),
        "ref": str(p.get("ref") or ""),
        "description": str(p.get("description") or ""),
        "style": str(p.get("style") or ""),
        "images": (p.get("images") or [])[:12],
        "referenceImage": p.get("referenceImage") or None,  # plano/referencia para comparar
        # ── LAS MEDIDAS SE GUARDAN CON EL PROYECTO ────────────────────────────
        # Antes no. El botón decía «Guardar el proyecto (cliente, referencia,
        # MEDIDAS, renders e historial)» y esta lista blanca no las recogía, así
        # que se quedaban solo en la sesión del navegador. Mientras no cerraras
        # la pestaña no se notaba; al reabrir el proyecto otro día, el ancho, el
        # fondo y la altura salían vacíos.
        #
        # Y ahí es donde se torcían las cotas: sin el ancho real, la pared deja
        # de estar anclada, `validar_distribucion` no tiene contra qué cuadrar y
        # todos los módulos pasan de medida ESCRITA a ESTIMADA («~»). Los
        # números cambiaban solos de una sesión a otra sin que nadie tocara
        # nada. El master, 24/08: «mírate el último proyecto guardado, lo que
        # pasa con las medidas».
        #
        # Va también la DISTRIBUCIÓN: detectarla y corregirla a mano módulo por
        # módulo es el trabajo de una tarde, y se perdía entero al cerrar.
        # Se conserva lo que ya hubiera si esta llamada no las trae (ver abajo).
        "medidas": (existing or {}).get("medidas"),
        "distribucion": (existing or {}).get("distribucion"),
        "tipo3d": (existing or {}).get("tipo3d"),
        # LA RELACIÓN MV, con las MANOS ya decididas. La mano D/I y el «dos
        # puertas» no se leen del diseño: los elige el master mueble a mueble, y
        # son justo lo que no puede llegar sin decidir al taller —un código
        # acabado en «D/I» se acierta la mitad de las veces y la otra mitad es
        # un frente desmontado y taladrado otra vez en casa del cliente—. Se
        # perdían al cerrar el proyecto. Van también las ALTURAS elegidas, que
        # mandan en el precio.
        "relacionMV": (existing or {}).get("relacionMV"),
        "createdByName": (current_user or {}).get("clientName") or (current_user or {}).get("username") or "",
        "createdAt": (existing or {}).get("createdAt") or now,
        "updatedAt": now,
    }
    # SOLO SE PISA LO QUE VENGA EN ESTA LLAMADA. Como se guarda con `$set` del
    # documento entero, meter las claves nuevas a secas habría BORRADO las
    # medidas de un proyecto cada vez que algo guardara sin mandarlas. Por eso
    # arriba se parte de lo que ya había y aquí solo se sustituye lo que llega.
    if isinstance(p.get("medidas"), dict):
        doc["medidas"] = p["medidas"]
    if isinstance(p.get("distribucion"), dict):
        doc["distribucion"] = p["distribucion"]
    if p.get("tipo3d"):
        doc["tipo3d"] = str(p["tipo3d"])
    if isinstance(p.get("relacionMV"), dict):
        doc["relacionMV"] = p["relacionMV"]

    await _db.render3d_designs.update_one({"id": oid}, {"$set": doc}, upsert=True)
    doc.pop("_id", None)
    return {"success": True, "design": doc}


@ai_engine_router.get("/designs")
async def list_render_designs(current_user: Optional[dict] = Depends(get_current_user)):
    query = {}
    if current_user and current_user.get("id") and not any(current_user.get(f) for f in ADMIN_ROLE_FLAGS):
        query["userId"] = current_user["id"]
    # La lista NO devuelve imágenes: cada diseño guarda su render/referencia como
    # base64 (cientos de KB cada uno); devolver una imagen por 300 diseños disparaba
    # el payload a cientos de MB y la petición se caía ("Failed to fetch"/timeout).
    # Solo metadatos ligeros + `hasImage`; la imagen y la referencia se cargan al
    # ABRIR el diseño (endpoint de detalle GET /designs/{id}).
    items = await _db.render3d_designs.find(
        query, {"_id": 0, "images": 0, "referenceImage": 0, "referenceImages": 0}
    ).sort("updatedAt", -1).to_list(300)
    for it in items:
        it["hasImage"] = True  # se resuelve al abrir; la lista muestra un placeholder
    return {"success": True, "designs": items}


@ai_engine_router.get("/designs/{design_id}")
async def get_render_design(design_id: str, current_user: Optional[dict] = Depends(get_current_user)):
    """Detalle completo de un diseño (incluye referenceImage) para abrir/comparar."""
    doc = await _db.render3d_designs.find_one({"id": design_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Diseño no encontrado")
    return {"success": True, "design": doc}


# ─── Historial de imágenes DEL PROYECTO ───────────────────────────────────────
# Cada render, variante, plano o lámina que se genera dentro de un proyecto se
# guarda como un documento propio en `render3d_images`, NO dentro del proyecto.
#
# Por qué separado: una imagen a 1600px en JPEG base64 ocupa ~250-400 KB. Un
# proyecto con 40 imágenes dentro del mismo documento se acerca al límite de
# 16 MB de MongoDB y, mucho antes, hace que el POST de guardado pese tanto que
# el proxy lo rechaza (era el "Error al guardar" de los renders grandes). Con un
# documento por imagen, cada subida es pequeña y el listado se pagina.
MAX_IMGS_PROYECTO = 120      # tope por proyecto (~30 MB); evita crecer sin freno
MAX_BYTES_IMAGEN = 6_000_000  # una sola imagen no puede pasar de ~6 MB


async def _design_accesible(design_id: str, current_user: Optional[dict]) -> dict:
    """Devuelve el proyecto o lanza 404/403. Solo el dueño o un admin entran."""
    doc = await _db.render3d_designs.find_one(
        {"id": design_id},
        {"_id": 0, "userId": 1, "id": 1, "cliente": 1, "ref": 1, "driveFolderId": 1})
    if not doc:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    if current_user and current_user.get("id") and doc.get("userId"):
        es_dueno = doc["userId"] == current_user["id"]
        es_admin = any(current_user.get(f) for f in ADMIN_ROLE_FLAGS)
        if not es_dueno and not es_admin:
            raise HTTPException(status_code=403, detail="Sin acceso a este proyecto")
    return doc


def _huella(data_url: str) -> str:
    """Identifica una imagen por su contenido, para no guardarla dos veces."""
    return hashlib.sha1((data_url or "").encode("utf-8", "ignore")).hexdigest()


# ─── Fotos en Google Drive ────────────────────────────────────────────────────
# Si hay Drive configurado (la misma cuenta de servicio de las copias de
# seguridad), la foto GRANDE se sube a una carpeta por proyecto y en la base de
# datos queda solo la miniatura (~25 KB) y el enlace. Así el Estudio 3D no se
# come el espacio de MongoDB y las fotos quedan también en el Drive de la casa.
#
# Si Drive no está configurado, o falla, la foto se guarda entera en la base de
# datos como hasta ahora: un problema con Google NO puede impedir guardar.
def _drive_disponible() -> bool:
    try:
        from services import drive_fotos
        return drive_fotos.esta_configurado()
    except Exception:
        return False


async def _carpeta_drive_del_proyecto(doc: dict) -> Optional[str]:
    """Id de la carpeta del proyecto en Drive; la crea la primera vez."""
    if doc.get("driveFolderId"):
        return doc["driveFolderId"]
    from services import drive_fotos
    nombre = " · ".join([x for x in [doc.get("cliente"), doc.get("ref")] if x]) or doc.get("id")
    res = await asyncio.to_thread(drive_fotos.carpeta_de_proyecto, nombre)
    if not res.get("ok"):
        logger.warning("Sin carpeta de Drive para %s: %s", doc.get("id"), res.get("error"))
        return None
    await _db.render3d_designs.update_one(
        {"id": doc["id"]}, {"$set": {"driveFolderId": res["id"], "driveFolderNombre": res.get("nombre")}})
    doc["driveFolderId"] = res["id"]
    return res["id"]


@ai_engine_router.post("/designs/{design_id}/imagenes")
async def add_design_images(design_id: str, payload: dict,
                            current_user: Optional[dict] = Depends(get_current_user)):
    """Añade imágenes al historial del proyecto. Repetir una imagen no la duplica."""
    doc = await _design_accesible(design_id, current_user)
    entrantes = (payload or {}).get("imagenes") or []
    if not isinstance(entrantes, list):
        raise HTTPException(status_code=400, detail="Formato de imágenes no válido")

    ya = await _db.render3d_images.count_documents({"designId": design_id})
    hueco = max(MAX_IMGS_PROYECTO - ya, 0)
    now = datetime.now(timezone.utc).isoformat()
    guardadas, repetidas, descartadas = [], 0, 0
    usar_drive = _drive_disponible()
    carpeta = await _carpeta_drive_del_proyecto(doc) if usar_drive else None
    fallos_drive = []
    # Un resultado por cada imagen recibida, en el mismo orden: así el navegador
    # sabe qué id le corresponde a cada foto y puede borrarla luego una a una.
    resultados = []

    for indice, item in enumerate(entrantes[:24]):  # tope por petición, que el JSON no se dispare
        if len(guardadas) >= hueco:
            resultados.append({"indice": indice, "estado": "lleno"})
            continue
        src = (item or {}).get("dataUrl") or ""
        if not isinstance(src, str) or not src.strip():
            resultados.append({"indice": indice, "estado": "vacia"})
            continue
        if len(src) > MAX_BYTES_IMAGEN:
            descartadas += 1
            resultados.append({"indice": indice, "estado": "demasiado_grande"})
            continue
        h = _huella(src)
        previa = await _db.render3d_images.find_one({"designId": design_id, "hash": h}, {"_id": 0, "id": 1})
        if previa:
            repetidas += 1
            resultados.append({"indice": indice, "estado": "repetida", "id": previa.get("id")})
            continue
        img = {
            "id": f"img-{uuid.uuid4().hex[:12]}",
            "designId": design_id,
            "userId": doc.get("userId") or (current_user or {}).get("id") or "anonymous",
            "hash": h,
            "dataUrl": src,
            "descripcion": str((item or {}).get("descripcion") or "")[:400],
            "tipo": str((item or {}).get("tipo") or "render")[:40],
            "createdAt": str((item or {}).get("createdAt") or now),
            "guardadaEn": now,
        }

        # A Drive la foto grande; en la base de datos, la miniatura y el enlace.
        # Sin miniatura no se sube: quedaría un historial sin nada que enseñar.
        miniatura = (item or {}).get("miniatura")
        if usar_drive and carpeta and isinstance(miniatura, str) and miniatura.startswith("data:"):
            from services import drive_fotos
            nombre = f"{now[:19].replace(':', '-')}_{img['tipo']}_{img['id']}"
            sub = await asyncio.to_thread(drive_fotos.subir_imagen, src, nombre, carpeta)
            if sub.get("ok"):
                img["dataUrl"] = miniatura          # lo que se ve en el historial
                img["driveId"] = sub["id"]
                img["driveEnlace"] = sub.get("enlace")
                img["enDrive"] = True
            else:
                # Drive ha fallado: se guarda entera aquí y se deja constancia.
                img["driveError"] = str(sub.get("error"))[:300]
                fallos_drive.append(sub.get("error"))

        await _db.render3d_images.insert_one(img)
        guardadas.append(img["id"])
        resultados.append({"indice": indice, "estado": "guardada", "id": img["id"],
                           "enDrive": bool(img.get("enDrive"))})

    total = await _db.render3d_images.count_documents({"designId": design_id})
    if guardadas:
        await _db.render3d_designs.update_one(
            {"id": design_id}, {"$set": {"numImagenes": total, "updatedAt": now}})
    return {"success": True, "guardadas": len(guardadas), "repetidas": repetidas,
            "descartadas": descartadas, "total": total, "resultados": resultados,
            "lleno": total >= MAX_IMGS_PROYECTO,
            "drive": bool(usar_drive and carpeta),
            "driveAviso": (f"{len(fallos_drive)} foto(s) no se pudieron subir a Drive; "
                           f"están guardadas en el ERP. {fallos_drive[0]}"
                           if fallos_drive else None)}


@ai_engine_router.get("/designs/{design_id}/imagenes")
async def list_design_images(design_id: str, desde: int = 0, limite: int = 12,
                             current_user: Optional[dict] = Depends(get_current_user)):
    """Historial de imágenes del proyecto, de la más nueva a la más antigua.

    Se pagina porque devolver 40 imágenes de golpe son decenas de MB y la
    petición se cae. `limite` está acotado a 24 por respuesta.
    """
    await _design_accesible(design_id, current_user)
    desde = max(int(desde or 0), 0)
    limite = min(max(int(limite or 12), 1), 24)
    total = await _db.render3d_images.count_documents({"designId": design_id})
    items = await _db.render3d_images.find(
        {"designId": design_id}, {"_id": 0, "hash": 0, "userId": 0, "driveId": 0}
    ).sort("guardadaEn", -1).skip(desde).limit(limite).to_list(limite)
    return {"success": True, "imagenes": items, "total": total,
            "desde": desde, "hayMas": desde + len(items) < total}


@ai_engine_router.get("/designs/{design_id}/imagenes/{imagen_id}/archivo")
async def get_design_image_file(design_id: str, imagen_id: str, t: Optional[str] = None,
                                current_user: Optional[dict] = Depends(get_current_user)):
    """Devuelve la foto a tamaño completo (de Drive o de la base de datos).

    Acepta el token por query param `t` además de por cabecera, porque una
    etiqueta <img> del navegador no puede mandar cabeceras. Las fotos NO se
    publican en Drive con enlace abierto: se sirven por aquí, con sesión.
    """
    usuario = current_user
    if not usuario and t:
        from services.jwt_service import _payload_to_user
        usuario = _payload_to_user(verify_access_token(t))  # 401 si no vale
    await _design_accesible(design_id, usuario)
    img = await _db.render3d_images.find_one({"designId": design_id, "id": imagen_id}, {"_id": 0})
    if not img:
        raise HTTPException(status_code=404, detail="Foto no encontrada")

    if img.get("driveId"):
        from services import drive_fotos
        res = await asyncio.to_thread(drive_fotos.descargar_imagen, img["driveId"])
        if res.get("ok"):
            return Response(content=res["datos"], media_type=res.get("mime") or "image/jpeg",
                            headers={"Cache-Control": "private, max-age=3600"})
        # Drive caído: se devuelve la miniatura antes que un error en pantalla.
        logger.warning("Foto %s no descargable de Drive: %s", imagen_id, res.get("error"))

    from services import drive_fotos
    datos, mime = drive_fotos.trocear_data_url(img.get("dataUrl") or "")
    if not datos:
        raise HTTPException(status_code=404, detail="La foto no tiene contenido")
    return Response(content=datos, media_type=mime or "image/jpeg",
                    headers={"Cache-Control": "private, max-age=3600"})


@ai_engine_router.delete("/designs/{design_id}/imagenes/{imagen_id}")
async def delete_design_image(design_id: str, imagen_id: str,
                              current_user: Optional[dict] = Depends(get_current_user)):
    """Quita UNA imagen del historial guardado del proyecto."""
    await _design_accesible(design_id, current_user)
    img = await _db.render3d_images.find_one({"designId": design_id, "id": imagen_id},
                                             {"_id": 0, "driveId": 1})
    # En Drive va a la PAPELERA, no se borra a fuego: 30 días para recuperarla si
    # el borrado fue un descuido.
    if img and img.get("driveId"):
        from services import drive_fotos
        await asyncio.to_thread(drive_fotos.a_papelera, img["driveId"])
    res = await _db.render3d_images.delete_one({"designId": design_id, "id": imagen_id})
    total = await _db.render3d_images.count_documents({"designId": design_id})
    await _db.render3d_designs.update_one({"id": design_id}, {"$set": {"numImagenes": total}})
    return {"success": True, "borradas": getattr(res, "deleted_count", 0), "total": total}


@ai_engine_router.delete("/designs/{design_id}")
async def delete_render_design(design_id: str, current_user: Optional[dict] = Depends(get_current_user)):
    # Validar propiedad: solo el dueño o un admin puede borrar
    doc = await _db.render3d_designs.find_one({"id": design_id}, {"_id": 0, "userId": 1})
    if not doc:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    if current_user and current_user.get("id") and doc.get("userId"):
        is_owner = doc["userId"] == current_user["id"]
        is_admin = any(current_user.get(f) for f in ADMIN_ROLE_FLAGS)
        if not is_owner and not is_admin:
            raise HTTPException(status_code=403, detail="Sin permiso para eliminar este proyecto")
    await _db.render3d_designs.delete_one({"id": design_id})
    # El historial de imágenes vive en otra colección: si no se borra aquí, se
    # queda ocupando espacio para siempre sin proyecto al que pertenecer.
    # Los archivos que estén en Google Drive NO se tocan: son de la empresa y
    # allí siguen viéndose en su carpeta. Borrar un proyecto del ERP no puede
    # llevarse por delante el archivo de fotos del cliente.
    await _db.render3d_images.delete_many({"designId": design_id})
    return {"success": True}


# ─── Modelos de Request/Response ──────────────────────────────────────────────

class RenderRequest(BaseModel):
    """Solicitud de render 3D por descripción natural (voz/texto)."""
    description: Optional[str] = Field("", description="Descripción en lenguaje natural de la cocina")
    style: Optional[str] = Field(None, description="Estilo de render (photorealistic, warm, etc.)")
    layout: Optional[str] = Field(None, description="Layout override (L-shape, island, etc.)")
    referenceImage: Optional[str] = Field(None, description="Imagen/PDF de referencia en base64 para condicionar el render")
    referenceMime: Optional[str] = Field(None, description="MIME de la imagen de referencia")
    referenceImages: Optional[List[str]] = Field(None, description="Imágenes adicionales (elemento a copiar: puerta, mueble…) en base64/data URL")
    provider: Optional[str] = Field(None, description="Motor de render: julio11 (IA0 histórica) | gemini (IA1) | manus | otros motores de master")
    projectType: Optional[str] = Field(None, description="Tipo de proyecto elegido por el usuario: cocina|armario|bano|otro. Fuerza el sujeto del render.")
    roomPhoto: Optional[bool] = Field(False, description="La imagen de referencia es una FOTO de la estancia REAL (vacía o a reformar): diseñar el mueble DENTRO de ella respetando su arquitectura.")
    editingRender: Optional[bool] = Field(False, description="La referencia es un render que ha generado el propio ERP y se le esta aplicando un cambio. Marca la PROCEDENCIA: asi no hay que adivinar si es un croquis, y una cocina blanca no se toma por un dibujo a mano.")


class RenderComposeRequest(BaseModel):
    """Render combinando un PLANO EN PLANTA + un BOCETO por cada PARED."""
    description: str = Field("", description="Brief del acabado/estilo deseado")
    style: Optional[str] = Field(None, description="Estilo de render")
    floorPlan: Optional[str] = Field(None, description="Plano en planta (base64/dataURL/PDF)")
    wallSketches: Optional[list] = Field(None, description="Bocetos por pared (lista base64/dataURL)")
    referenceImages: Optional[list] = Field(
        None, description="Referencias de ACABADO (foto de estilo). Se usan A LA VEZ que el plano")
    provider: Optional[str] = Field(None, description="Motor elegido en pantalla (IA 0/1/2/3/4)")
    projectType: Optional[str] = Field(None, description="cocina|armario|bano|otro")


class RenderParamsRequest(BaseModel):
    """Solicitud de render 3D con parámetros explícitos."""
    layout: str = Field(default="L-shape", description="Distribución de la cocina")
    countertop: str = Field(default="quartz_white", description="Material de encimera")
    cabinets: str = Field(default="white_matte", description="Material de muebles")
    handles: str = Field(default="bar_black", description="Estilo de tiradores")
    floor: str = Field(default="wood_oak", description="Material del suelo")
    lighting: str = Field(default="natural", description="Tipo de iluminación")
    style: str = Field(default="photorealistic", description="Estilo de renderizado")
    additional_details: Optional[str] = Field(None, description="Detalles adicionales")
    projectType: Optional[str] = Field(None, description="cocina|armario|bano|otro")


class AnalyzeRequest(BaseModel):
    """Solicitud de análisis de documento."""
    analysis_type: str = Field(default="general", description="Tipo: general, catalog, invoice, technical")
    questions: Optional[List[str]] = Field(None, description="Preguntas específicas")


class TaskResponse(BaseModel):
    """Respuesta estándar del motor."""
    success: bool
    engine: str = "LuiggiAI"
    task_id: Optional[str] = None
    status: Optional[str] = None
    result: Optional[dict] = None
    error: Optional[str] = None


# ─── Endpoints ────────────────────────────────────────────────────────────────

@ai_engine_router.get("/status")
async def get_engine_status(user=Depends(require_auth)):
    """Health check del motor LuiggiAI."""
    engine = get_engine()
    status = engine.get_status()
    disponible = bool(status) and str(status.get("status", "")).lower() not in {"error", "failed", "unavailable"}
    return {"success": disponible, "status": "available" if disponible else "unavailable"}


@ai_engine_router.get("/diagnostics")
async def engine_diagnostics(user=Depends(require_auth)):
    """Diagnóstico del motor de render: ¿ve las claves (Manus/Gemini)? ¿conecta con
    el proveedor? No crea tareas ni gasta créditos: solo comprueba configuración y
    una conexión ligera."""
    import os
    config = get_ai_config()
    manus_key = getattr(config, "provider_api_key", "") or ""
    manus_present = bool(manus_key)

    try:
        from services.llm_vision import get_gemini_key, GOOGLE_GENAI_AVAILABLE
        gemini_present = bool(get_gemini_key())
        gemini_sdk = bool(GOOGLE_GENAI_AVAILABLE)
    except Exception:
        gemini_present, gemini_sdk = False, False

    provider = (os.environ.get("KITCHEN_RENDER_PROVIDER") or "manus").lower()

    # Conectividad con Manus (sin crear tareas): un GET ligero al proveedor.
    manus_reachable, manus_http_status, manus_error = None, None, None
    if manus_present:
        try:
            async with httpx.AsyncClient(timeout=10.0) as c:
                r = await c.get(config.provider_base_url,
                                headers=config.provider_auth_headers())
                manus_reachable, manus_http_status = True, r.status_code
        except Exception as e:
            manus_reachable, manus_error = False, type(e).__name__

    if provider == "manus" and manus_present:
        effective = "manus"
    elif gemini_present and gemini_sdk:
        effective = "gemini"
    else:
        effective = "ninguno"

    # Con la cabecera correcta, un 401/403 ya significa de verdad que la clave no
    # vale. Antes se enviaba `Authorization: Bearer`, que el proveedor rechaza
    # siempre, y el 401 no distinguía una clave caducada de una clave buena.
    manus_auth_ok = None
    if manus_http_status is not None:
        manus_auth_ok = manus_http_status not in (401, 403)

    disponible = effective != "ninguno"
    return {"success": disponible, "status": "available" if disponible else "unavailable"}


@ai_engine_router.get("/materials")
async def get_materials_catalog(user=Depends(require_auth)):
    """Devuelve el catálogo completo de materiales disponibles para renders."""
    service = get_render_service()
    return service.get_materials_catalog()


@ai_engine_router.post("/render")
async def generate_render_natural(request: RenderRequest, user=Depends(require_auth)):
    """
    Genera un render 3D a partir de una descripción en lenguaje natural.
    Acepta texto libre o transcripción de voz.

    Ejemplo: "Quiero una cocina en L con encimera de mármol blanco,
    muebles de roble natural y tiradores negros"
    """
    request.projectType = await exigir_tipo_estudio3d(user, request.projectType)
    # ENFORCEMENT de créditos de IA por usuario. Admin/master = ilimitado.
    # Defensivo: si el contador falla por un error interno, NO se bloquea; solo
    # se bloquea cuando realmente no quedan créditos (restantes <= 0).
    try:
        from services.ai_usage import get_user_credits, consume_credits, mensaje_sin_creditos
        credits = await get_user_credits(user)
        if not credits.get("ilimitado") and int(credits.get("restantes", 0) or 0) <= 0:
            raise HTTPException(
                status_code=402,
                detail=mensaje_sin_creditos(user, credits),
            )
        # SE COBRA POR EL MOTOR QUE SE VA A USAR DE VERDAD, no por el pedido:
        # `motor_permitido` ya ha rebajado a IA 1 a quien no sea master, y sería
        # absurdo cobrarle el 3,3x de un motor que no va a llegar a tocar.
        await consume_credits(user, "render",
                              motor=motor_permitido(user, request.provider))
    except HTTPException:
        raise
    except Exception:
        pass  # error interno del contador: nunca bloquea la generación
    # Registro de uso de IA POR USUARIO (alimenta la columna "IA" del ranking y
    # el consumo por usuario). Best-effort: nunca bloquea el render.
    try:
        from services.activity_tracker import get_tracker, ActivityType
        _tr = get_tracker()
        if _tr and user and user.get("id"):
            await _tr.track(user.get("id"), user.get("username") or user.get("clientName") or "", ActivityType.AI_TELEMETRY, {"kind": "render"})
    except Exception:
        pass
    # Amueblado virtual (roomPhoto): requiere permiso específico canUseAmueblado
    # (o rol elevado). El JWT no lleva el flag, se comprueba en BD.
    if request.roomPhoto:
        allowed = any(user.get(f) for f in ADMIN_ROLE_FLAGS)
        if not allowed:
            try:
                full = await _db.users.find_one({"id": user.get("id")}, {"_id": 0, "canUseAmueblado": 1}) or {}
                allowed = bool(full.get("canUseAmueblado"))
            except Exception:
                allowed = False
        if not allowed:
            raise HTTPException(status_code=403, detail="No tienes activado el permiso de amueblado virtual. Pídeselo a tu administrador.")

    service = get_render_service()

    # Construir overrides desde parámetros opcionales
    overrides = {}
    if request.style:
        overrides["style"] = request.style
    if request.layout:
        overrides["layout"] = request.layout

    result = await service.generate_render(
        description=request.description,
        params_override=overrides if overrides else None,
        reference_image=request.referenceImage,
        reference_mime=request.referenceMime,
        provider=motor_permitido(user, request.provider),
        reference_images=request.referenceImages,
        project_type=request.projectType,
        room_photo=bool(request.roomPhoto),
        editing_render=bool(request.editingRender),
    )

    logger.info(f"Render solicitado por {user.get('username')}: {request.description[:80]}...")
    return limpiar_respuesta_render(result)


# ─── El MOTOR de render lo elige el master, y se comprueba AQUÍ ──────────────
#
# La pantalla ya lo hacía bien: el desplegable de motores solo se le pinta al
# master, y a todos los demás les ofrece «IA 1» a secas. El problema es que el
# motor viaja en el CUERPO de la petición, y aquí se pasaba tal cual a
# `generate_render` sin mirar quién lo mandaba. O sea que cualquier usuario con
# la sesión iniciada podía pedir `banana_pro` —la IA 7, que cuesta 3,3 veces más
# por render— desde fuera de la pantalla.
#
# Lo dice el propio repositorio en `routes/cascos.py`, a cuenta de la tarifa MV:
# esconder un botón no cierra una API. Pues esto es lo mismo con el motor.
#
# Se usa la MISMA puerta que el MV (`_es_master` de `routes/cascos.py`) y no
# `ADMIN_ROLE_FLAGS`, que es más ancha: por ahí pasan gerente y director
# comercial, y los motores de pruebas son del master (CLAUDE.md, regla 1).
MOTOR_DE_PRODUCCION = "gemini"


def motor_permitido(user, pedido):
    """Qué motor se usa de verdad. Para quien no es master, siempre el de producción."""
    from routes.cascos import _es_master
    if not pedido:
        return None            # sin motor pedido, manda el de por defecto de siempre
    if _es_master(user):
        return pedido
    if str(pedido).strip().lower() != MOTOR_DE_PRODUCCION:
        logger.info(
            "%s ha pedido el motor '%s' sin ser master; se rinde con %s.",
            (user or {}).get("username") or "un usuario", pedido, MOTOR_DE_PRODUCCION)
    return MOTOR_DE_PRODUCCION


@ai_engine_router.get("/my-credits")
async def my_ai_credits(user=Depends(require_auth)):
    """Estado de créditos de IA del usuario actual (asignados/consumidos/restantes/ilimitado)."""
    from services.ai_usage import get_user_credits
    return await get_user_credits(user)


@ai_engine_router.post("/render/compose")
async def generate_render_compose(request: RenderComposeRequest, user=Depends(require_auth)):
    """Genera un render fotorrealista combinando un PLANO EN PLANTA (distribución)
    y un BOCETO por cada PARED (diseño de esa pared), fiel a ambos a la vez."""
    request.projectType = await exigir_tipo_estudio3d(user, request.projectType)
    service = get_render_service()
    overrides = {}
    if request.style:
        overrides["style"] = request.style
    result = await service.generate_render_composed(
        description=request.description or "",
        floor_plan=request.floorPlan,
        wall_sketches=request.wallSketches or [],
        reference_images=request.referenceImages or [],
        params_override=overrides or None,
        provider=motor_permitido(user, request.provider),
        project_type=request.projectType,
    )
    logger.info(
        f"Render compuesto por {user.get('username')}: "
        f"plano={bool(request.floorPlan)} bocetos={len(request.wallSketches or [])} "
        f"referencias={len(request.referenceImages or [])}"
    )
    return limpiar_respuesta_render(result)


class OrbitRequest(BaseModel):
    referenceImage: str = Field(..., description="Render base (base64/data URL) del que orbitar")
    referenceMime: Optional[str] = Field(None, description="MIME de la imagen base")
    projectType: Optional[str] = Field(None, description="cocina|armario|bano|otro")
    n: Optional[int] = Field(6, description="Número de vistas (2-6)")
    provider: Optional[str] = None


@ai_engine_router.post("/render/orbit")
async def generate_render_orbit(request: OrbitRequest, user=Depends(require_auth)):
    """Genera varias vistas de la MISMA cocina a distintos ángulos, a partir de un
    render base, para un visor orbital (girar con el ratón). Consume créditos de IA
    (una vista = un render)."""
    request.projectType = await exigir_tipo_estudio3d(user, request.projectType)
    # Permiso específico: el giro 360º solo está disponible si el usuario tiene
    # canUseRender360 (o es un rol elevado). El JWT no lleva el flag, se comprueba en BD.
    allowed = True  # Activado para todos los usuarios del ERP

    n = max(2, min(int(request.n or 6), 6))
    # Enforcement de créditos: cada vista cuesta un render. Bloquea solo si no hay
    # créditos suficientes; el contador nunca bloquea por error interno.
    try:
        from services.ai_usage import get_user_credits, consume_credits, mensaje_sin_creditos
        credits = await get_user_credits(user)
        if not credits.get("ilimitado"):
            restantes = int(credits.get("restantes", 0) or 0)
            if restantes <= 0:
                raise HTTPException(status_code=402, detail="Sin créditos disponibles para generar el giro 360º.")
            n = min(n, restantes)
        for _ in range(n):
            await consume_credits(user, "render",
                                  motor=motor_permitido(user, getattr(request, "provider", None)))
    except HTTPException:
        raise
    except Exception:
        pass
    try:
        from services.activity_tracker import get_tracker, ActivityType
        _tr = get_tracker()
        if _tr and user and user.get("id"):
            await _tr.track(user.get("id"), user.get("username") or "", ActivityType.AI_TELEMETRY, {"kind": "orbit", "n": n})
    except Exception:
        pass

    service = get_render_service()
    result = await service.generate_orbit_views(
        reference_image=request.referenceImage,
        reference_mime=request.referenceMime,
        project_type=request.projectType,
        n=n,
        provider=motor_permitido(user, request.provider),
    )
    logger.info(f"Orbit 360º por {user.get('username')}: {result.get('count', 0)} vistas")
    return limpiar_respuesta_render(result)


class UpscaleRequest(BaseModel):
    imageBase64: str = Field(..., description="Imagen (base64/data URL) a escalar a 4K")
    width: Optional[int] = Field(3840, description="Ancho objetivo en px (por defecto 3840 = 4K UHD)")


@ai_engine_router.post("/render/upscale-4k")
async def upscale_render_4k(request: UpscaleRequest, user=Depends(require_auth)):
    """Escala una imagen a resolución 4K (3840 px de ancho por defecto) con
    remuestreo Lanczos y un realce de nitidez suave. Determinista y sin coste de
    IA: garantiza dimensiones reales 4K para impresión/entrega al cliente."""
    # Permiso específico: exportar a 4K requiere canUse4K (o rol elevado).
    allowed = any(user.get(f) for f in ADMIN_ROLE_FLAGS)
    if not allowed:
        try:
            full = await _db.users.find_one({"id": user.get("id")}, {"_id": 0, "canUse4K": 1}) or {}
            allowed = bool(full.get("canUse4K"))
        except Exception:
            allowed = False
    if not allowed:
        raise HTTPException(status_code=403, detail="No tienes activado el permiso de exportación 4K. Pídeselo a tu administrador.")

    import base64 as _b64, io as _io, re as _re
    raw = request.imageBase64 or ""
    m = _re.match(r"^data:image/[^;]+;base64,(.*)$", raw, _re.DOTALL)
    b64 = m.group(1) if m else raw
    try:
        data = _b64.b64decode(b64)
    except Exception:
        raise HTTPException(status_code=400, detail="Imagen no válida.")
    try:
        from PIL import Image, ImageFilter
        im = Image.open(_io.BytesIO(data)).convert("RGB")
        target_w = max(1280, min(int(request.width or 3840), 7680))
        if im.width < target_w:
            target_h = round(im.height * target_w / im.width)
            im = im.resize((target_w, target_h), Image.LANCZOS)
        # Realce de detalle suave tras el reescalado.
        im = im.filter(ImageFilter.UnsharpMask(radius=2.2, percent=110, threshold=2))
        out = _io.BytesIO()
        im.save(out, format="JPEG", quality=94, subsampling=0)
        out.seek(0)
        b = _b64.b64encode(out.read()).decode("utf-8")
        return {"success": True, "image": f"data:image/jpeg;base64,{b}", "width": im.width, "height": im.height}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"upscale-4k error: {e}")
        raise HTTPException(status_code=500, detail="No se pudo escalar la imagen a 4K.")


@ai_engine_router.post("/render/params")
async def generate_render_params(request: RenderParamsRequest, user=Depends(require_auth)):
    """
    Genera un render 3D a partir de parámetros explícitos (formulario).
    Usar cuando el usuario selecciona materiales desde el catálogo.
    """
    tipo = await exigir_tipo_estudio3d(user, request.projectType)
    if tipo != "cocina":
        raise HTTPException(
            status_code=400,
            detail="El render por parámetros actuales solo está disponible para Cocina. Usa descripción o plano para el tipo contratado.",
        )
    service = get_render_service()

    result = await service.generate_render_from_params(
        layout=request.layout,
        countertop=request.countertop,
        cabinets=request.cabinets,
        handles=request.handles,
        floor=request.floor,
        lighting=request.lighting,
        style=request.style,
        additional_details=request.additional_details,
    )

    logger.info(f"Render (params) solicitado por {user.get('username')}")
    return limpiar_respuesta_render(result)


@ai_engine_router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(..., description="Archivo de audio (webm, wav, mp3)"),
    user=Depends(require_auth),
):
    """
    Transcribe un archivo de audio a texto.
    Útil como fallback cuando Web Speech API no está disponible.
    """
    config = get_ai_config()

    if not config.voice_enabled:
        raise HTTPException(status_code=503, detail="Transcripción de voz no habilitada")

    # Validar tipo de archivo
    allowed_types = ["audio/webm", "audio/wav", "audio/mp3", "audio/mpeg", "audio/ogg"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de archivo no soportado: {file.content_type}"
        )

    # Leer archivo
    audio_data = await file.read()

    # Transcripción en servidor como fallback cuando el navegador no la soporta
    try:
        import openai
        client = openai.AsyncOpenAI(api_key=config.whisper_api_key)

        audio_file = io.BytesIO(audio_data)
        audio_file.name = file.filename or "audio.webm"

        transcript = await client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="es",
        )

        return {
            "success": True,
            "text": transcript.text,
            "engine": config.brand_name,
            "method": "server_transcription",
        }

    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="Servicio de transcripción no disponible. Use la transcripción del navegador."
        )
    except Exception as e:
        logger.error(f"Error en transcripción: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error al transcribir audio. Intente de nuevo."
        )


@ai_engine_router.post("/analyze")
async def analyze_document(
    file: UploadFile = File(..., description="Documento a analizar (PDF, imagen, etc.)"),
    analysis_type: str = Form(default="general"),
    questions: Optional[str] = Form(default=None, description="Preguntas separadas por |"),
    user=Depends(require_auth),
):
    """
    Analiza un documento y extrae información relevante.
    Tipos: general, catalog, invoice, technical
    """
    config = get_ai_config()

    if not config.document_ai_enabled:
        raise HTTPException(status_code=503, detail="Análisis de documentos no habilitado")

    # Validar tamaño
    file_data = await file.read()
    max_bytes = config.max_file_size_mb * 1024 * 1024
    if len(file_data) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Archivo demasiado grande. Máximo: {config.max_file_size_mb}MB"
        )

    engine = get_engine()

    # Subir archivo
    upload_result = await engine.upload_file(file_data, file.filename)
    if not upload_result.get("success"):
        raise HTTPException(status_code=500, detail="Error al procesar el archivo")

    file_id = upload_result["file_id"]

    # Construir prompt según tipo de análisis
    prompts = {
        "general": f"Analiza el documento '{file.filename}' y proporciona un resumen detallado.",
        "catalog": (
            f"Extrae todos los productos del catálogo '{file.filename}': "
            f"referencia, nombre, dimensiones, materiales, precio. Formato JSON."
        ),
        "invoice": (
            f"Extrae datos de la factura '{file.filename}': "
            f"emisor, receptor, fecha, líneas, importes, IVA, total. Formato JSON."
        ),
        "technical": (
            f"Extrae especificaciones técnicas de '{file.filename}': "
            f"medidas, materiales, instrucciones. Formato estructurado."
        ),
    }

    prompt = prompts.get(analysis_type, prompts["general"])

    # Añadir preguntas específicas
    if questions:
        question_list = [q.strip() for q in questions.split("|") if q.strip()]
        if question_list:
            prompt += "\n\nPreguntas específicas:\n" + "\n".join(f"- {q}" for q in question_list)

    result = await engine.create_task(
        prompt=prompt,
        files=[{"file_id": file_id}],
    )

    if result.get("success"):
        task_id = result["task_id"]
        final = await engine.wait_for_completion(task_id, timeout=120)
        logger.info(f"Análisis '{analysis_type}' solicitado por {user.get('username')}")
        return limpiar_respuesta_render(final)

    error = limpiar_respuesta_render({"error": result.get("error", "Error al analizar")})["error"]
    raise HTTPException(status_code=500, detail=error)


@ai_engine_router.get("/task/{task_id}")
async def get_task_status(task_id: str, user=Depends(require_auth)):
    """Consulta el estado de una tarea en curso."""
    engine = get_engine()
    result = await engine.get_task_status(task_id)
    return limpiar_respuesta_render(result)


# ─── Proxy de assets (white-label) ────────────────────────────────────────────
# Sirve las imágenes generadas a través de este backend para que el navegador
# del cliente nunca vea el dominio del proveedor subyacente. Solo se permiten
# URLs cuyo host pertenezca a la lista de dominios autorizados (evita SSRF).
_IMG_CONTENT_TYPES = ("image/", "application/pdf", "application/octet-stream")


@ai_engine_router.get("/asset")
async def proxy_asset(
    u: str,
    t: Optional[str] = None,
    authorization: Optional[str] = Header(None),
):
    """
    Descarga y reenvía un asset del proveedor ocultando su origen.

    Acepta el token JWT por cabecera `Authorization` o por query param `t`,
    porque las etiquetas <img> del navegador no pueden enviar cabeceras.
    """
    token = t
    if not token and authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Autenticación requerida")
    verify_access_token(token)  # lanza 401 si es inválido/expirado

    engine = get_engine()
    config = get_ai_config()

    try:
        original_url = engine.decode_proxy_token(u)
    except Exception:
        raise HTTPException(status_code=400, detail="Recurso no válido")

    host = ""
    parsed = None
    try:
        parsed = urlparse(original_url)
        host = parsed.netloc.split("@")[-1].split(":")[0].lower()
    except Exception:
        host = ""

    if parsed is None or parsed.scheme not in ("http", "https") or not engine._is_provider_host(host):
        # Nunca permitir URLs arbitrarias (protección anti-SSRF).
        raise HTTPException(status_code=403, detail="Recurso no autorizado")

    # Solo el host de la API necesita el token de autorización; los CDN/buckets
    # usan URLs prefirmadas y rechazan cabeceras de auth extra.
    headers = {}
    api_host = urlparse(config.provider_base_url).netloc.split(":")[0].lower()
    if host == api_host:
        headers.update(config.provider_auth_headers())

    try:
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            resp = await client.get(original_url, headers=headers)
    except Exception as e:
        logger.error(f"Proxy asset error: {e}")
        raise HTTPException(status_code=502, detail="No se pudo obtener el recurso")

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Recurso no disponible")

    content_type = resp.headers.get("content-type", "application/octet-stream")
    return Response(
        content=resp.content,
        media_type=content_type,
        headers={
            "Cache-Control": "private, max-age=3600",
            "Access-Control-Allow-Origin": "*",
        },
    )


# ==================== DESCRIBIR IMAGEN DE REFERENCIA (para el render) ====================
# Sube una imagen/PDF de referencia (foto de cocina, plano, estilo) y el motor
# de vision la describe para enriquecer la descripcion del render 3D. Usa una
# ruta de vision independiente del motor de render principal.
_REF_PROMPT = (
    "Eres un proyectista y diseñador de interiores experto en mobiliario a medida (cocinas, armarios, baños, etc.). "
    "Analiza esta imagen de referencia o croquis para generar un render 3D fotorrealista del MISMO elemento que aparece.\n\n"
    "REGLA CRÍTICA SOBRE LA DISTRIBUCIÓN (RESPETAR ESTRICTAMENTE):\n"
    "- Si la imagen muestra dos frentes de muebles en ángulo de 90° formando una ESQUINA EN L (por ejemplo, fregadero/placa/lavavajillas en una pared y caldera/micro/lavadora/frigorífico en la pared lateral en ángulo), LA DISTRIBUCIÓN ES OBLIGATORIAMENTE 'EN L' (cocina en L con esquina). Queda PROHIBIDO escribir 'distribución lineal' si los muebles se disponen en dos paredes en esquina.\n"
    "- Si sólo hay muebles a lo largo de una única línea recta de pared, indica 'distribución lineal'. Si hay 3 frentes, 'distribución en U'.\n\n"
    "Si la imagen es un CROQUIS o PLANO MANUSCRITO (dibujo a mano con medidas), interpreta FIELMENTE:\n"
    "- La FORMA REAL de la distribución (especifica explícitamente si es una cocina en L con esquina)\n"
    "- Cada MÓDULO dibujado por pared de izquierda a derecha y su MEDIDA en cm (ej. 60 cm, 90 cm, 35 cm)\n"
    "- Los ELECTRODOMÉSTICOS y su posición exacta en cada pared (fregadero, lavavajillas, lavadora, horno, microondas, caldera, placa, campana, frigorífico, cafetera de encimera en la esquina)\n"
    "- PEQUEÑOS ELECTRODOMÉSTICOS Y DETALLES DE ENCIMERA: si hay una cafetera sobre la encimera o en la esquina, la caldera en la pared superior, o tomas de enchufe sobre encimera, INCLÚYELOS EXPLÍCITAMENTE en la descripción\n"
    "- Las COLUMNAS (alto) y su contenido (columna micro, columna combi, pilar)\n"
    "- Los MATERIALES, ACABADOS y COLORES escritos en el plano\n"
    "- Las medidas de cada pared (ancho de Pared 1, ancho de Pared 2 en esquina)\n\n"
    "Devuelve un párrafo descriptivo en español, MUY DETALLADO y CONCRETO, "
    "especificando la distribución real (En L o Lineal) y cada módulo con su medida y posición exacta. "
    "Incluye TODAS las medidas que puedas leer. Solo el texto, sin encabezados."
)


def _recortar_si_es_una_pagina(b64: str, mime: str = "image/png") -> str:
    """Saca el DIBUJO de dentro de la página, si lo que llega es una página.

    POR QUÉ ESTO TIENE QUE ESTAR TAMBIÉN AQUÍ (24/08/2026)
    -----------------------------------------------------
    El recorte existía desde el 18/08, pero SOLO en el camino de RENDERIZAR
    (`render_3d.py`). El camino de DESCRIBIR recibía la página entera, y se
    notaba en lo que devolvía. Caso real del master: un pantallazo de un
    presupuesto —barra de estado, título, el dibujo, tres líneas de precio,
    total y barra de Android— y la descripción salió diciendo «sistema METOD de
    IKEA» y «frentes de la marca CUBRO».

    Eso NO estaba en el dibujo: estaba en las líneas de precio («Elementos
    IKEA», «Elementos CUBRO»). El modelo no lo dedujo de la cocina, lo LEYÓ del
    presupuesto — y «METOD» ni siquiera aparecía en la página, o sea que además
    bordó encima. En la misma descripción se inventó «300 cm» repartidos en
    cinco módulos de 60 (el dibujo no lleva ni una cota) y un «frigorífico
    combi» que no está dibujado por ningún lado.

    Con el dibujo recortado nada de eso es alcanzable: las líneas de precio
    dejan de existir y la cocina pasa a ocupar la imagen entera en vez de un
    tercio de la altura.

    ES SEGURO PARA LAS FOTOS. `recortar_dibujo_base64` solo recorta cuando
    reconoce un dibujo dentro de una página; con una referencia de acabado
    —una foto de una cocina real— devuelve la imagen tal cual. Comprobado
    contra los dos renders del master: `recortó=False`, mismas dimensiones.
    """
    try:
        from services.recorte_croquis import recortar_dibujo_base64
        recortado, hubo = recortar_dibujo_base64(b64, mime)
        if hubo:
            logger.info("Dibujo recortado de la página antes de describirlo.")
            return recortado
    except Exception as e:
        logger.warning("No se pudo recortar el dibujo, se describe la imagen entera: %s", e)
    return b64


@ai_engine_router.post("/pdf-preview")
async def pdf_preview(payload: dict, user=Depends(require_auth)):
    """Devuelve la primera página de un PDF como PNG para la vista Comparar."""
    b64 = (payload or {}).get("fileBase64") or ""
    if not b64:
        raise HTTPException(status_code=400, detail="Falta el archivo")
    stripped = b64.split(",", 1)[1] if b64.startswith("data:") else b64
    try:
        from services.pdf_utils import is_pdf_base64, pdf_base64_to_png_base64
        if not (("pdf" in b64[:60].lower()) or is_pdf_base64(stripped)):
            raise HTTPException(status_code=400, detail="El archivo no es un PDF válido")
        pages = pdf_base64_to_png_base64(stripped, dpi=180, max_pages=1) or []
        if not pages:
            raise HTTPException(status_code=422, detail="No se pudo preparar la vista previa")
        page = pages[0]
        if not page.startswith("data:"):
            page = f"data:image/png;base64,{page}"
        return {"success": True, "image": page}
    except HTTPException:
        raise
    except Exception as e:
        logger.warning("No se pudo preparar la vista previa del PDF: %s", e)
        raise HTTPException(status_code=422, detail="No se pudo preparar la vista previa")


@ai_engine_router.post("/describe-reference")
async def describe_reference(payload: dict, user=Depends(require_auth)):
    """Describe una imagen/PDF de referencia (base64) para el render 3D."""
    b64 = (payload or {}).get("fileBase64") or ""
    if not b64:
        raise HTTPException(status_code=400, detail="Falta el archivo (fileBase64)")
    stripped = b64.split(",", 1)[1] if b64.startswith("data:") else b64
    try:
        from services.pdf_utils import is_pdf_base64, pdf_base64_to_png_base64
        from services.llm_vision import analyze_image_with_gemini
        img = stripped
        # Si es un PDF, rasterizar la primera pagina.
        try:
            if ("pdf" in b64[:40].lower()) or is_pdf_base64(stripped):
                pages = pdf_base64_to_png_base64(stripped, dpi=150, max_pages=1) or []
                if pages:
                    img = pages[0]
        except Exception:
            pass
        img = _recortar_si_es_una_pagina(img)
        import uuid as _uuid
        resp = await analyze_image_with_gemini(
            image_base64=img, prompt=_REF_PROMPT,
            session_id=f"render-ref-{_uuid.uuid4().hex[:8]}", model="gemini-2.5-pro",
        )
        text = (resp or "").strip()
        if text.startswith("```"):
            text = text.strip("`").strip()
        if not text:
            return {"success": False, "error": "No se pudo interpretar la imagen de referencia. Pruebe con otra imagen."}
        # Sanitizar por si el motor de vision incluyera alguna marca propia.
        text = get_engine()._sanitize_response(text)
        return {"success": True, "description": text}
    except Exception as e:
        # Nunca exponer el detalle del proveedor al cliente: log interno + mensaje genérico.
        logger.error(f"describe-reference error: {e}")
        return {"success": False, "error": "No se pudo analizar la imagen de referencia. Inténtelo de nuevo."}


@ai_engine_router.post("/describe-project")
async def describe_project(payload: dict, user=Depends(require_auth)):
    """Describe el proyecto ENTERO a partir de TODOS los dibujos a la vez.

    Por qué no vale describir imagen por imagen: el plano en planta da la
    distribución y cada alzado da UNA pared. Analizados por separado, cada uno
    parece una cocina distinta ("distribución lineal") y nadie ata el conjunto:
    ni que es en L, ni qué pared va con cuál, ni dónde está la torre de
    columnas. Aquí van todas juntas, cada una con su papel.
    """
    from services.llm_vision import analyze_images_with_gemini

    p = payload or {}
    plano = p.get("floorPlan")
    alzados = p.get("wallSketches") or []
    referencias = p.get("referenceImages") or []
    if not (plano or alzados or referencias):
        raise HTTPException(status_code=400, detail="No hay ningún dibujo que analizar.")

    # Mismo tope que el render compuesto: 7 imágenes juntas. Más allá no es que
    # falle, es que cada dibujo recibe menos atención y la descripción se
    # generaliza.
    MAX_JUNTAS = 7
    imagenes = []
    if plano:
        # El plano y los alzados SÍ se recortan: son dibujos, y muchas veces
        # llegan dentro de un pantallazo de página. Las REFERENCIAS DE ACABADO
        # no —son fotos— aunque el recorte también las dejaría en paz; no se
        # tocan para que quede dicho que ahí no hay nada que recortar.
        plano = _recortar_si_es_una_pagina(plano)
        imagenes.append({"data": plano, "papel":
                         "PLANO EN PLANTA acotado. Manda en la DISTRIBUCIÓN: forma de la "
                         "cocina (lineal, en L, en U, con isla), qué pared es cada una, el "
                         "orden de los muebles en cada pared, sus anchos y las cotas. Las "
                         "medidas escritas en el plano son la verdad."})
    for i, a in enumerate(alzados, start=1):
        if len(imagenes) >= MAX_JUNTAS:
            break
        imagenes.append({"data": _recortar_si_es_una_pagina(a), "papel":
                         f"ALZADO de la PARED {i}: el diseño de esa pared (muebles altos, "
                         f"bajos, columnas, electrodomésticos y acabados)."})
    for r in (referencias or [])[:2]:
        if len(imagenes) >= MAX_JUNTAS:
            break
        imagenes.append({"data": r, "papel":
                         "REFERENCIA DE ACABADO: materiales, color y tirador. NO aporta "
                         "distribución."})

    try:
        from services.criterios_cocina import CRITERIOS_ANALISIS
    except Exception:
        CRITERIOS_ANALISIS = ""

    prompt = (
        "Eres un diseñador de cocinas con un arquitecto técnico al lado. Tienes "
        "VARIAS vistas del MISMO proyecto: descríbelo como UNA sola cocina, no una "
        "por imagen.\n\n"
        "Escribe un párrafo continuo, en español, que sirva de brief para generar un "
        "render fotorrealista, con este contenido y en este orden:\n"
        "1. Distribución del conjunto (lineal, en L, en U, con isla o península) y "
        "medidas totales de cada tramo, tomadas del plano.\n"
        "2. Pared por pared, de izquierda a derecha: los muebles en su orden real con "
        "su ancho, qué lleva cada uno (puertas, cajones, gavetas), y los "
        "electrodomésticos con su sitio exacto.\n"
        "3. La torre de columnas, si la hay, y qué contiene.\n"
        "4. Acabados: color y material de los frentes, encimera, tirador o gola, "
        "zócalo y, si se ve, el suelo.\n"
        "5. Ventanas y puertas de paso que condicionen la composición.\n\n"
        "REGLAS:\n"
        "- NO te inventes NINGUNA medida. Usa solo las que estén escritas en el plano; "
        "si una no está, no la menciones. Una cota inventada acaba en un mueble mal "
        "fabricado.\n"
        "- NO añadas electrodomésticos, muebles ni elementos que no aparezcan.\n"
        "- Si dos vistas se contradicen, manda el plano en la distribución y el alzado "
        "en el diseño de su pared; dilo en una frase al final.\n"
        "- Nada de listas ni títulos: texto corrido, claro y breve.\n"
        + CRITERIOS_ANALISIS
    )

    try:
        texto = await analyze_images_with_gemini(
            imagenes, prompt, session_id=f"proyecto-{uuid.uuid4().hex[:8]}",
            model="gemini-2.5-pro")
    except Exception as e:
        logger.error("describe-project: %s", e)
        return {"success": False, "error": "No se pudo analizar el conjunto de dibujos."}

    texto = (texto or "").strip().strip("`").strip()
    if not texto:
        return {"success": False, "error": "No se pudo interpretar los dibujos."}
    # Se devuelve el DESGLOSE de lo que se ha mirado de verdad. Sin esto no hay
    # forma de saber si la IA leyó los cinco dibujos o solo el primero.
    return {"success": True, "description": get_engine()._sanitize_response(texto),
            "imagenes": len(imagenes),
            "analizado": {
                "plano": bool(plano) and any("PLANO" in i["papel"] for i in imagenes),
                "alzados": sum(1 for i in imagenes if i["papel"].startswith("ALZADO")),
                "referencias": sum(1 for i in imagenes if i["papel"].startswith("REFERENCIA")),
                "descartados": max(len(alzados) + len(referencias) + (1 if plano else 0) - len(imagenes), 0),
            }}


@ai_engine_router.post("/detect-installations")
async def detect_installations(payload: dict, current_user: Optional[dict] = Depends(get_current_user)):
    """Analiza un render de cocina con IA y devuelve los puntos de instalación
    (enchufes, tomas de agua, desagüe, gas) con coordenadas normalizadas 0-1,
    para señalarlos automáticamente sobre la imagen (esquema para gremios)."""
    import json as _json, re as _re
    p = payload or {}
    img = p.get("imageBase64") or p.get("image") or ""
    tipo_proyecto = str(p.get("tipo") or "cocina").lower().strip()
    if not img:
        raise HTTPException(status_code=400, detail="Falta la imagen del render.")
    # Reducir la imagen si es muy grande (p. ej. un render 4K): una imagen enorme
    # dispara timeouts y errores en la llamada de visión. 1600px de ancho es de sobra
    # para localizar las tomas.
    # SIEMPRE se re-codifica a un JPEG estándar (baseline) con PIL: así se normaliza
    # cualquier imagen que Gemini rechace ("Unable to process input image") por venir
    # de un canvas/formato raro, y de paso se reduce el tamaño.
    try:
        import base64 as _b64x, io as _iox
        from PIL import Image as _PILImg
        _m = _re.match(r"^data:[^;]+;base64,(.*)$", img.strip(), _re.DOTALL)
        _raw = (_m.group(1) if _m else img).strip()
        _raw_clean = _re.sub(r"\s+", "", _raw)
        _im = _PILImg.open(_iox.BytesIO(_b64x.b64decode(_raw_clean))).convert("RGB")
        if _im.width > 1600:
            _h = round(_im.height * 1600 / _im.width)
            _im = _im.resize((1600, _h), _PILImg.LANCZOS)
        _buf = _iox.BytesIO()
        _im.save(_buf, format="JPEG", quality=88, optimize=True)  # baseline, sin perfil raro
        img = "data:image/jpeg;base64," + _b64x.b64encode(_buf.getvalue()).decode()
    except Exception as _e:
        # Antes esto solo dejaba un aviso en el log y se llamaba a Gemini
        # IGUALMENTE con la imagen que no se había podido preparar. El master
        # veía entonces un "400 INVALID_ARGUMENT: Unable to process input image"
        # con un enlace a la documentación de Google, que no dice nada de lo que
        # pasó de verdad ni de qué hacer. Si la imagen no se puede leer aquí, no
        # hay nada que analizar: se corta y se dice en castellano.
        logger.warning("detect-installations: no se pudo normalizar la imagen: %s", _e)
        raise HTTPException(
            status_code=400,
            detail="No se pudo leer la imagen del render (llegó vacía o en un "
                   "formato que no se reconoce). Vuelve a generar el render e "
                   "inténtalo otra vez.",
        )
    try:
        from services.llm_vision import analyze_image_with_gemini, is_vision_available
        if not is_vision_available():
            raise HTTPException(status_code=503, detail="IA no configurada. Falta la clave del motor de IA (contacta con el administrador).")
        # Prompt y tipos válidos según el tipo de proyecto (cocina / armario / baño / otro).
        if tipo_proyecto == "armario":
            valid = {"enchufe", "luz", "datos", "tv"}
            prompt = (
                "Eres instalador y proyectista de armarios/vestidores. Analiza esta imagen (render de un armario o "
                "vestidor) y localiza los PUNTOS DE INSTALACIÓN necesarios:\n"
                "- 'enchufe': tomas de corriente interiores o próximas (zona de cajones, caja fuerte, plancha).\n"
                "- 'luz': iluminación LED interior (baldas, barras de colgar, sensor de puerta).\n"
                "- 'datos': toma de red si hay zona de escritorio/tv.\n"
                "- 'tv': toma de TV/antena si procede.\n\n"
                "Devuelve SOLO un bloque JSON: {\"puntos\":[{\"tipo\":\"enchufe|luz|datos|tv\",\"x\":0.0-1.0,\"y\":0.0-1.0,\"nota\":\"texto corto\"}]}. "
                "Sin puntos claros, devuelve {\"puntos\":[]}."
            )
        elif tipo_proyecto in ("bano", "baño"):
            valid = {"enchufe", "agua", "desague", "lavadora", "luz", "toallero"}
            prompt = (
                "Eres instalador y proyectista de baños. Analiza esta imagen (render de un baño o mueble de baño) "
                "y localiza los PUNTOS DE INSTALACIÓN necesarios, deduciéndolos de los elementos visibles:\n"
                "- 'agua': tomas de agua fría/caliente del lavabo, ducha/bañera y bidé.\n"
                "- 'desague': desagües del lavabo, ducha/bañera e inodoro.\n"
                "- 'lavadora': toma de lavadora si aparece.\n"
                "- 'enchufe': tomas junto al espejo/lavabo (secador, maquinilla).\n"
                "- 'luz': puntos de luz (espejo, techo).\n"
                "- 'toallero': toallero eléctrico o radiador si aparece.\n\n"
                "Devuelve SOLO un bloque JSON: {\"puntos\":[{\"tipo\":\"enchufe|agua|desague|lavadora|luz|toallero\",\"x\":0.0-1.0,\"y\":0.0-1.0,\"nota\":\"texto corto\"}]}. "
                "Sin puntos claros, devuelve {\"puntos\":[]}."
            )
        elif tipo_proyecto == "otro":
            valid = {"enchufe", "luz", "datos", "tv"}
            prompt = (
                "Eres instalador y proyectista de mueble a medida. Analiza esta imagen y localiza los PUNTOS DE "
                "INSTALACIÓN visibles: 'enchufe' (tomas de corriente), 'luz' (iluminación), 'datos' (red), 'tv' (antena).\n"
                "Devuelve SOLO un bloque JSON: {\"puntos\":[{\"tipo\":\"enchufe|luz|datos|tv\",\"x\":0.0-1.0,\"y\":0.0-1.0,\"nota\":\"texto corto\"}]}. "
                "Sin puntos claros, devuelve {\"puntos\":[]}."
            )
        else:
            valid = {"enchufe", "agua", "desague", "gas"}
            prompt = (
                "Eres instalador y proyectista de cocinas. Analiza esta imagen (render de una cocina) "
                "y localiza los PUNTOS DE INSTALACIÓN necesarios, deduciéndolos de los elementos visibles.\n\n"
                "MÉTODO OBLIGATORIO para acertar la posición (muy importante):\n"
                "1. Identifica primero, en píxeles de ESTA imagen, la línea superior de la encimera (donde la "
                "encimera se une a la pared/salpicadero) y la línea inferior de los muebles altos.\n"
                "2. Cada punto debe caer SIEMPRE sobre una superficie real visible (el salpicadero de pared, el "
                "frontal de un electrodoméstico o el interior de un mueble). NUNCA lo pongas flotando en el aire, "
                "sobre el techo, sobre el suelo, ni fuera del mueble.\n"
                "3. Los 'enchufe' de encimera van en la franja de salpicadero: JUSTO por encima de la línea de la "
                "encimera y por debajo de los muebles altos (a un tercio de esa franja). Los enchufes de "
                "electrodoméstico van centrados sobre el frontal visible de ese electrodoméstico.\n"
                "4. 'agua' y 'desague' van BAJO el fregadero, a la altura del mueble bajo (parte inferior), "
                "centrados en el ancho del fregadero.\n\n"
                "TIPOS:\n"
                "- 'enchufe': tomas sobre la encimera (pequeño electrodoméstico) y detrás de cada electrodoméstico "
                "visible (horno, microondas, placa de inducción, frigorífico, lavavajillas, campana, vinoteca).\n"
                "- 'agua': toma de agua fría/caliente bajo el fregadero (y en isla si hay segundo fregadero).\n"
                "- 'desague': desagüe bajo el fregadero (y lavavajillas).\n"
                "- 'gas': solo si hay placa de GAS (llama). Si la placa es de inducción/vitrocerámica, NO pongas gas.\n\n"
                "REPARTE LOS PUNTOS POR TODA LA COCINA:\n"
                "- Recorre la cocina de IZQUIERDA A DERECHA y no te dejes ningún tramo. Si hay dos "
                "paredes (cocina en L), pon puntos en LAS DOS: amontonarlos todos en un lado deja "
                "media cocina sin instalación y el electricista pica donde no es.\n"
                "- Dos puntos distintos NUNCA van en el mismo sitio. Si el horno y el microondas "
                "están uno encima del otro, sepáralos en vertical, cada uno sobre su aparato.\n"
                "- No repitas el mismo punto dos veces.\n\n"
                "ALTURA DE CADA TOMA (`alto_cm`, desde el suelo acabado). NO todas van a 110:\n"
                "- Enchufe sobre encimera: 110. Campana: 220. Placa de inducción: 60 (en el mueble "
                "de al lado, nunca detrás de la placa). Horno y microondas de columna: 60 sobre el "
                "suelo o dentro del mueble contiguo. Frigorífico: 170. Lavavajillas y lavadora: 60, "
                "en el mueble de al lado, NO detrás del aparato (quedaría inaccesible).\n"
                "- Agua fría/caliente del fregadero: 50. Desagüe: 40. Gas: 50.\n\n"
                "Usa coordenadas normalizadas: x=0 borde izquierdo, x=1 borde derecho, y=0 arriba, y=1 abajo de la "
                "imagen. Antes de devolver, VERIFICA que cada (x,y) coincide con el píxel del elemento descrito y "
                "corrígelo si se ha desplazado. Prefiere pocos puntos bien colocados a muchos mal colocados.\n\n"
                "Devuelve SOLO un bloque JSON: {\"puntos\":[{\"tipo\":\"enchufe|agua|desague|gas\",\"x\":0.0-1.0,\"y\":0.0-1.0,\"alto_cm\":110,\"nota\":\"texto corto\"}]}. "
                "Sin puntos claros, devuelve {\"puntos\":[]}."
            )
        text = await analyze_image_with_gemini(image_base64=img, prompt=prompt, model="gemini-2.5-flash")
        m = _re.search(r"\{[\s\S]*\}", text or "")
        data = {}
        if m:
            try:
                data = _json.loads(m.group())
            except Exception:
                data = {}
        out = []
        for it in (data.get("puntos") or [])[:40]:
            tipo = str(it.get("tipo") or "").lower().strip()
            if tipo not in valid:
                continue
            try:
                x = max(0.0, min(1.0, float(it.get("x"))))
                y = max(0.0, min(1.0, float(it.get("y"))))
            except (TypeError, ValueError):
                continue
            out.append({"type": tipo, "x": round(x * 100, 2), "y": round(y * 100, 2),
                        "alto_cm": it.get("alto_cm"),
                        "nota": str(it.get("nota") or "")[:60]})
        # Que dos marcas no se pisen NO es cosa del modelo de visión: es
        # geometría, y la geometría se calcula. Aquí se tiran los duplicados y se
        # separan las que chocan, que es lo que dejaba el plano ilegible.
        from services.marcas_instalaciones import ordenar_marcas
        return {"success": True, "marks": ordenar_marcas(out)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"detect-installations error: {e}")
        # Muestra el motivo real (recortado) para poder diagnosticar desde la app.
        raise HTTPException(status_code=500, detail=f"No se pudieron detectar las instalaciones: {str(e)[:180]}")


@ai_engine_router.post("/parse-valued-supplier-order")
async def parse_valued_supplier_order(payload: dict, current_user: Optional[dict] = Depends(get_current_user)):
    """Analiza una foto, pantallazo (Ctrl+V) o PDF de un pedido valorado de proveedor de puertas/costados/regletas
    usando Gemini 2.5 Flash Vision. Extrae códigos, descripciones, medidas (alto/ancho en mm), cantidades y precios,
    y devuelve la estructura normalizada para actualizar el proyecto en tiempo real."""
    import json as _json, re as _re
    p = payload or {}
    img = p.get("imageBase64") or p.get("image") or ""
    if not img:
        raise HTTPException(status_code=400, detail="Falta la imagen o archivo del pedido valorado.")
    try:
        import base64 as _b64x, io as _iox
        from PIL import Image as _PILImg
        _m = _re.match(r"^data:[^;]+;base64,(.*)$", img.strip(), _re.DOTALL)
        _raw = (_m.group(1) if _m else img).strip()
        _raw_clean = _re.sub(r"\s+", "", _raw)
        _im = _PILImg.open(_iox.BytesIO(_b64x.b64decode(_raw_clean))).convert("RGB")
        if _im.width > 2000:
            _h = round(_im.height * 2000 / _im.width)
            _im = _im.resize((2000, _h), _PILImg.LANCZOS)
        _buf = _iox.BytesIO()
        _im.save(_buf, format="JPEG", quality=90, optimize=True)
        img = "data:image/jpeg;base64," + _b64x.b64encode(_buf.getvalue()).decode()
    except Exception as _e:
        logger.warning("parse-valued-supplier-order: error al procesar imagen: %s", _e)

    try:
        from services.llm_vision import analyze_image_with_gemini, is_vision_available
        if not is_vision_available():
            raise HTTPException(status_code=503, detail="IA no disponible.")

        prompt = (
            "Analyze this valued kitchen supplier order / proforma / invoice / doors & side panels cut list.\n"
            "Read every row of doors, side panels (costados), filler strips (regletas), and drawer fronts.\n"
            "Extract a JSON list of line items with extreme accuracy:\n"
            "{\n"
            '  "referenciaProveedor": "order reference if present",\n'
            '  "proveedor": "supplier name if present",\n'
            '  "items": [\n'
            '    {\n'
            '      "cod": "item code or model",\n'
            '      "descripcion": "item description or type",\n'
            '      "cant": number,\n'
            '      "alto": number_in_mm,\n'
            '      "ancho": number_in_mm,\n'
            '      "largo": number_in_mm_if_regleta,\n'
            '      "pm2": price_per_m2_number_or_null,\n'
            '      "costeTotal": total_line_price_in_eur_number_or_null\n'
            '    }\n'
            '  ]\n'
            "}\n\n"
            "Important: heights and widths MUST be numbers in millimeters (mm). Convert cm to mm if needed (e.g. 70cm -> 700mm). Output ONLY valid JSON."
        )

        text = await analyze_image_with_gemini(image_base64=img, prompt=prompt, model="gemini-2.5-flash")
        m = _re.search(r"\{[\s\S]*\}", text or "")
        data = _json.loads(m.group()) if m else {}
        items = data.get("items") or []
        return {
            "success": True,
            "referenciaProveedor": data.get("referenciaProveedor") or "",
            "proveedor": data.get("proveedor") or "",
            "items": items
        }
    except Exception as e:
        logger.error(f"parse-valued-supplier-order error: {e}")
        raise HTTPException(status_code=500, detail=f"Error al analizar pedido valorado: {str(e)[:180]}")
