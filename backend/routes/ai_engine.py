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

_db = _get_db()  # cliente MongoDB compartido (singleton)


# ─── Proyectos de render 3D (guardar / historial persistente) ─────────────────
@ai_engine_router.post("/designs")
async def save_render_design(payload: dict, current_user: Optional[dict] = Depends(get_current_user)):
    """Guarda (o actualiza) un proyecto de render 3D del usuario."""
    p = payload or {}
    oid = p.get("id") or f"r3d-{uuid.uuid4().hex[:10]}"
    now = datetime.now(timezone.utc).isoformat()
    existing = await _db.render3d_designs.find_one({"id": oid}, {"_id": 0, "createdAt": 1, "userId": 1})
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
        "createdByName": (current_user or {}).get("clientName") or (current_user or {}).get("username") or "",
        "createdAt": (existing or {}).get("createdAt") or now,
        "updatedAt": now,
    }
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
    description: str = Field(..., description="Descripción en lenguaje natural de la cocina")
    style: Optional[str] = Field(None, description="Estilo de render (photorealistic, warm, etc.)")
    layout: Optional[str] = Field(None, description="Layout override (L-shape, island, etc.)")
    referenceImage: Optional[str] = Field(None, description="Imagen/PDF de referencia en base64 para condicionar el render")
    referenceMime: Optional[str] = Field(None, description="MIME de la imagen de referencia")
    referenceImages: Optional[List[str]] = Field(None, description="Imágenes adicionales (elemento a copiar: puerta, mueble…) en base64/data URL")
    provider: Optional[str] = Field(None, description="Motor de render: manus | gemini (opcional; por defecto manus)")
    projectType: Optional[str] = Field(None, description="Tipo de proyecto elegido por el usuario: cocina|armario|bano|otro. Fuerza el sujeto del render.")
    roomPhoto: Optional[bool] = Field(False, description="La imagen de referencia es una FOTO de la estancia REAL (vacía o a reformar): diseñar el mueble DENTRO de ella respetando su arquitectura.")


class RenderComposeRequest(BaseModel):
    """Render combinando un PLANO EN PLANTA + un BOCETO por cada PARED."""
    description: str = Field("", description="Brief del acabado/estilo deseado")
    style: Optional[str] = Field(None, description="Estilo de render")
    floorPlan: Optional[str] = Field(None, description="Plano en planta (base64/dataURL/PDF)")
    wallSketches: Optional[list] = Field(None, description="Bocetos por pared (lista base64/dataURL)")


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
    status["user"] = user.get("username", "unknown")
    return status


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
                                headers={"Authorization": f"Bearer {manus_key}"})
                manus_reachable, manus_http_status = True, r.status_code
        except Exception as e:
            manus_reachable, manus_error = False, type(e).__name__

    if provider == "manus" and manus_present:
        effective = "manus"
    elif gemini_present and gemini_sdk:
        effective = "gemini"
    else:
        effective = "ninguno"

    return {
        "render_provider_config": provider,
        "effective_engine": effective,
        "manus": {
            "key_present": manus_present,
            "key_length": len(manus_key) if manus_present else 0,
            "reachable": manus_reachable,
            "http_status": manus_http_status,
            "error": manus_error,
        },
        "gemini": {"key_present": gemini_present, "sdk_available": gemini_sdk},
        "hint": (
            "El render usará MANUS." if effective == "manus"
            else "El render usará GEMINI (respaldo)." if effective == "gemini"
            else "Falta configurar la clave del motor de IA en el servidor."
        ),
    }


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
    # ENFORCEMENT de créditos de IA por usuario. Admin/master = ilimitado.
    # Defensivo: si el contador falla por un error interno, NO se bloquea; solo
    # se bloquea cuando realmente no quedan créditos (restantes <= 0).
    try:
        from services.ai_usage import get_user_credits, consume_credits
        credits = await get_user_credits(user)
        if not credits.get("ilimitado") and int(credits.get("restantes", 0) or 0) <= 0:
            raise HTTPException(
                status_code=402,
                detail=(f"Sin créditos de IA: has agotado tu bolsa mensual "
                        f"({int(credits.get('asignados', 0) or 0)}). Contacta con tu administrador."),
            )
        await consume_credits(user, "render")
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
        provider=request.provider,
        reference_images=request.referenceImages,
        project_type=request.projectType,
        room_photo=bool(request.roomPhoto),
    )

    logger.info(f"Render solicitado por {user.get('username')}: {request.description[:80]}...")
    return result


@ai_engine_router.get("/my-credits")
async def my_ai_credits(user=Depends(require_auth)):
    """Estado de créditos de IA del usuario actual (asignados/consumidos/restantes/ilimitado)."""
    from services.ai_usage import get_user_credits
    return await get_user_credits(user)


@ai_engine_router.post("/render/compose")
async def generate_render_compose(request: RenderComposeRequest, user=Depends(require_auth)):
    """Genera un render fotorrealista combinando un PLANO EN PLANTA (distribución)
    y un BOCETO por cada PARED (diseño de esa pared), fiel a ambos a la vez."""
    service = get_render_service()
    overrides = {}
    if request.style:
        overrides["style"] = request.style
    result = await service.generate_render_composed(
        description=request.description or "",
        floor_plan=request.floorPlan,
        wall_sketches=request.wallSketches or [],
        params_override=overrides or None,
    )
    logger.info(
        f"Render compuesto por {user.get('username')}: "
        f"plano={bool(request.floorPlan)} bocetos={len(request.wallSketches or [])}"
    )
    return result


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
    # Permiso específico: el giro 360º solo está disponible si el usuario tiene
    # canUseRender360 (o es un rol elevado). El JWT no lleva el flag, se comprueba en BD.
    allowed = any(user.get(f) for f in ADMIN_ROLE_FLAGS)
    if not allowed:
        try:
            full = await _db.users.find_one({"id": user.get("id")}, {"_id": 0, "canUseRender360": 1}) or {}
            allowed = bool(full.get("canUseRender360"))
        except Exception:
            allowed = False
    if not allowed:
        raise HTTPException(status_code=403, detail="No tienes activado el permiso de giro 360º. Pídeselo a tu administrador.")

    n = max(2, min(int(request.n or 6), 6))
    # Enforcement de créditos: cada vista cuesta un render. Bloquea solo si no hay
    # créditos suficientes; el contador nunca bloquea por error interno.
    try:
        from services.ai_usage import get_user_credits, consume_credits
        credits = await get_user_credits(user)
        if not credits.get("ilimitado"):
            restantes = int(credits.get("restantes", 0) or 0)
            if restantes <= 0:
                raise HTTPException(status_code=402, detail="Sin créditos de IA para generar el giro 360º.")
            n = min(n, restantes)
        for _ in range(n):
            await consume_credits(user, "render")
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
        provider=request.provider,
    )
    logger.info(f"Orbit 360º por {user.get('username')}: {result.get('count', 0)} vistas")
    return result


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
    return result


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
        return final

    raise HTTPException(status_code=500, detail=result.get("error", "Error al analizar"))


@ai_engine_router.get("/task/{task_id}")
async def get_task_status(task_id: str, user=Depends(require_auth)):
    """Consulta el estado de una tarea en curso."""
    engine = get_engine()
    result = await engine.get_task_status(task_id)
    return result


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
        headers["Authorization"] = f"Bearer {config.provider_api_key}"

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
    "Eres un disenador de interiores y mobiliario a medida (cocinas, armarios "
    "empotrados, banos, dormitorios, estanterias, muebles a medida...). Analiza "
    "esta imagen de referencia para generar un render 3D fotorrealista del MISMO "
    "tipo de elemento que aparece (no asumas que es una cocina).\n\n"
    "Si la imagen es un CROQUIS o PLANO MANUSCRITO (dibujo a mano con medidas), "
    "interpreta FIELMENTE:\n"
    "- La FORMA de la distribucion (lineal, L, U, isla, etc.)\n"
    "- Cada MODULO dibujado de izquierda a derecha y su MEDIDA en cm\n"
    "- Los ELECTRODOMESTICOS y su posicion exacta (fregadero, lavavajillas, "
    "lavadora, horno, placa, campana, frigorifico)\n"
    "- Las COLUMNAS (alto) y su contenido\n"
    "- Los MATERIALES y ACABADOS escritos (ej: Sincron Noce, Alhambra, etc.)\n"
    "- El COLOR del casco (ej: casco blanco)\n"
    "- Los TIRADORES mencionados\n"
    "- Las medidas totales (ancho total, alto de bajos, alto de altos)\n\n"
    "Si la imagen es una FOTO, describe: tipo de mueble o espacio, distribucion, "
    "materiales y acabados, color de puertas, tiradores, interior (baldas, columnas, "
    "cajones), suelo, pared, iluminacion y estilo.\n\n"
    "Devuelve un parrafo descriptivo en espanol, MUY DETALLADO y CONCRETO, "
    "especificando cada modulo con su medida y posicion exacta, listo para "
    "usar como prompt de render. Incluye TODAS las medidas que puedas leer. "
    "Solo el texto, sin encabezados."
)


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
        _m = _re.match(r"^data:image/[^;]+;base64,(.*)$", img, _re.DOTALL)
        _raw = _m.group(1) if _m else img
        _im = _PILImg.open(_iox.BytesIO(_b64x.b64decode(_raw))).convert("RGB")
        if _im.width > 1600:
            _h = round(_im.height * 1600 / _im.width)
            _im = _im.resize((1600, _h), _PILImg.LANCZOS)
        _buf = _iox.BytesIO()
        _im.save(_buf, format="JPEG", quality=88, optimize=True)  # baseline, sin perfil raro
        img = "data:image/jpeg;base64," + _b64x.b64encode(_buf.getvalue()).decode()
    except Exception as _e:
        logger.warning("detect-installations: no se pudo normalizar la imagen: %s", _e)
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
                "Usa coordenadas normalizadas: x=0 borde izquierdo, x=1 borde derecho, y=0 arriba, y=1 abajo de la "
                "imagen. Antes de devolver, VERIFICA que cada (x,y) coincide con el píxel del elemento descrito y "
                "corrígelo si se ha desplazado. Prefiere pocos puntos bien colocados a muchos mal colocados.\n\n"
                "Devuelve SOLO un bloque JSON: {\"puntos\":[{\"tipo\":\"enchufe|agua|desague|gas\",\"x\":0.0-1.0,\"y\":0.0-1.0,\"nota\":\"texto corto\"}]}. "
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
            out.append({"type": tipo, "x": round(x * 100, 2), "y": round(y * 100, 2), "nota": str(it.get("nota") or "")[:60]})
        return {"success": True, "marks": out}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"detect-installations error: {e}")
        # Muestra el motivo real (recortado) para poder diagnosticar desde la app.
        raise HTTPException(status_code=500, detail=f"No se pudieron detectar las instalaciones: {str(e)[:180]}")
