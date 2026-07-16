"""
Endpoints de Administración del Sistema - LUIGGI HOME
- Backups
- Informes de uso
- Estadísticas del sistema
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from datetime import datetime, timedelta
from typing import Optional
import logging
import os

from motor.motor_asyncio import AsyncIOMotorClient

from services.backup_service import get_backup_service
from services.activity_tracker import get_tracker, ActivityType
from services.jwt_service import require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])

# Conexión a BD (mismo patrón que el resto de routers)
_MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
_DB_NAME = os.environ.get('DB_NAME', 'luiggi_home')
_admin_client = AsyncIOMotorClient(_MONGO_URL)
_db = _admin_client[_DB_NAME]


# ==================== DIAGNÓSTICO DE BASE DE DATOS ====================

@router.get("/db-health")
async def db_health(user=Depends(require_admin)):
    """Diagnóstico de la base de datos: tamaño, límite y test de ESCRITURA real.

    Sirve para confirmar si los fallos al guardar (contactos, visitas,
    presupuestos) se deben a que la BD no acepta escrituras (p.ej. cuota de
    almacenamiento llena en Atlas). Hace un insert+delete de prueba.
    """
    out = {"ok": True}
    try:
        stats = await _db.command("dbStats", scale=1024 * 1024)  # MB
        out["storage"] = {
            "dataSize_MB": round(stats.get("dataSize", 0), 2),
            "storageSize_MB": round(stats.get("storageSize", 0), 2),
            "indexSize_MB": round(stats.get("indexSize", 0), 2),
            "objects": stats.get("objects", 0),
        }
        # Colecciones más grandes por nº de documentos
        sizes = {}
        for name in await _db.list_collection_names():
            try:
                sizes[name] = await _db[name].estimated_document_count()
            except Exception:
                pass
        out["top_collections"] = dict(sorted(sizes.items(), key=lambda x: -x[1])[:10])
    except Exception as e:
        out["storage_error"] = str(e)

    # Test de ESCRITURA real en las colecciones donde fallaba el guardado.
    # Inserta un documento de prueba (marcado con _diag) y lo borra. Si alguna
    # falla, ese es el problema y veremos el error exacto por colección.
    writes = {}
    for coll in ["contacts", "calendar_events", "projects", "diag_scratch"]:
        try:
            doc = {"id": f"_diag-{datetime.utcnow().timestamp()}", "_diag": True,
                   "name": "DIAG TEST", "ts": datetime.utcnow()}
            res = await _db[coll].insert_one(doc)
            await _db[coll].delete_one({"_id": res.inserted_id})
            writes[coll] = "OK"
        except Exception as e:
            writes[coll] = f"FALLO: {e}"
            out["ok"] = False
            logger.error(f"db-health write test '{coll}' failed: {e}")
    out["write_test"] = writes

    # Índices de cada colección (para detectar índices únicos que bloqueen
    # escrituras por duplicado).
    idx = {}
    for coll in ["contacts", "calendar_events", "projects"]:
        try:
            info = await _db[coll].index_information()
            idx[coll] = {name: {"keys": v.get("key"), "unique": v.get("unique", False)}
                         for name, v in info.items()}
        except Exception as e:
            idx[coll] = f"error: {e}"
    out["indexes"] = idx

    return out


@router.get("/recent-errors")
async def recent_errors(limit: int = 20, user=Depends(require_admin)):
    """Últimos errores de guardado (422/500) capturados por el servidor.

    Permite ver el error EXACTO de un fallo al crear contacto/visita/
    presupuesto sin necesidad de la consola del navegador: reproduce el fallo
    en la app y luego abre esta URL.
    """
    try:
        docs = await _db.error_log.find({}, {"_id": 0}).sort("ts", -1).to_list(limit)
        return {"count": len(docs), "errors": docs}
    except Exception as e:
        return {"count": 0, "errors": [], "error": str(e)}


@router.post("/cleanup-telemetry")
async def cleanup_telemetry(days: int = 90, user=Depends(require_admin)):
    """Purga telemetría/actividad antigua para liberar espacio en la BD.

    Borra documentos de las colecciones de telemetría con más de `days` días.
    Útil si la BD se ha llenado por el registro de actividad sin tope.
    """
    cutoff = datetime.utcnow() - timedelta(days=days)
    deleted = {}
    # user_activity usa 'timestamp'; telemetry_audit puede usar 'timestamp' o 'createdAt'.
    for coll, field in [("user_activity", "timestamp"), ("telemetry_audit", "timestamp")]:
        try:
            r = await _db[coll].delete_many({field: {"$lt": cutoff}})
            deleted[coll] = r.deleted_count
        except Exception as e:
            deleted[coll] = f"error: {e}"
    return {"success": True, "cutoff_days": days, "deleted": deleted}


# ==================== BACKUP ENDPOINTS ====================

@router.post("/backup/create")
async def create_backup(user=Depends(require_admin)):
    """Crear un backup manual de la base de datos (solo ADMIN)"""
    backup_service = get_backup_service()
    if not backup_service:
        raise HTTPException(status_code=500, detail="Servicio de backup no inicializado")
    
    result = await backup_service.create_backup()
    
    if result["success"]:
        return result
    else:
        raise HTTPException(status_code=500, detail=result.get("error", "Error creando backup"))


@router.get("/backup/list")
async def list_backups(user=Depends(require_admin)):
    """Listar todos los backups disponibles (solo ADMIN)"""
    backup_service = get_backup_service()
    if not backup_service:
        raise HTTPException(status_code=500, detail="Servicio de backup no inicializado")
    
    return {
        "success": True,
        "backups": backup_service.list_backups(),
        "retention_days": 7
    }


@router.post("/backup/restore/{backup_name}")
async def restore_backup(backup_name: str, user=Depends(require_admin)):
    """Restaurar un backup específico (solo ADMIN; ¡sobrescribe datos!)"""
    backup_service = get_backup_service()
    if not backup_service:
        raise HTTPException(status_code=500, detail="Servicio de backup no inicializado")
    
    result = await backup_service.restore_backup(backup_name)
    
    if result["success"]:
        return result
    else:
        raise HTTPException(status_code=500, detail=result.get("error", "Error restaurando backup"))


# ==================== USAGE REPORTS ENDPOINTS ====================

@router.get("/usage/report")
async def get_usage_report(days: int = 30, user=Depends(require_admin)):
    """Obtener informe completo de uso de la plataforma"""
    tracker = get_tracker()
    if not tracker:
        raise HTTPException(status_code=500, detail="Tracker de actividad no inicializado")
    
    return await tracker.get_usage_report(days=days)


@router.get("/usage/users")
async def get_user_stats(user_id: Optional[str] = None, days: int = 30, user=Depends(require_admin)):
    """Obtener estadísticas de uso por usuario"""
    tracker = get_tracker()
    if not tracker:
        raise HTTPException(status_code=500, detail="Tracker de actividad no inicializado")
    
    stats = await tracker.get_user_stats(user_id=user_id, days=days)
    return {
        "success": True,
        "period_days": days,
        "users": stats
    }


@router.get("/usage/timeline")
async def get_activity_timeline(
    user_id: Optional[str] = None,
    days: int = 30,
    limit: int = 100,
    user=Depends(require_admin)
):
    """Obtener timeline de actividades recientes"""
    tracker = get_tracker()
    if not tracker:
        raise HTTPException(status_code=500, detail="Tracker de actividad no inicializado")
    
    timeline = await tracker.get_activity_timeline(user_id=user_id, days=days, limit=limit)
    return {
        "success": True,
        "period_days": days,
        "activities": timeline
    }


@router.get("/usage/daily")
async def get_daily_activity(days: int = 30, user=Depends(require_admin)):
    """Obtener actividad diaria agregada"""
    tracker = get_tracker()
    if not tracker:
        raise HTTPException(status_code=500, detail="Tracker de actividad no inicializado")
    
    daily = await tracker.get_daily_activity(days=days)
    return {
        "success": True,
        "period_days": days,
        "daily_activity": daily
    }


@router.get("/usage/by-type")
async def get_activity_by_type(days: int = 30, user=Depends(require_admin)):
    """Obtener actividad agrupada por tipo"""
    tracker = get_tracker()
    if not tracker:
        raise HTTPException(status_code=500, detail="Tracker de actividad no inicializado")
    
    by_type = await tracker.get_activity_by_type(days=days)
    return {
        "success": True,
        "period_days": days,
        "activity_by_type": by_type
    }


# ─── Consumo de IA (contador + umbral + coste estimado), solo master ─────────
from services.ai_usage import get_usage_summary, set_config


@router.get("/ai-usage")
async def ai_usage(user=Depends(require_admin)):
    """Resumen del consumo de IA del mes en curso, histórico, coste estimado y alerta."""
    return {"success": True, **(await get_usage_summary())}


@router.post("/ai-usage/threshold")
async def ai_usage_config(payload: dict, user=Depends(require_admin)):
    """Fija umbral de alerta, coste por tipo de llamada (€) y URL del panel del proveedor."""
    await set_config(payload or {})
    return {"success": True, **(await get_usage_summary())}


@router.post("/ai-usage/probe")
async def ai_usage_probe(payload: dict = None, user=Depends(require_admin)):
    """Medidor en tiempo real: lanza UNA petición real a Gemini y devuelve los
    tokens exactos (entrada/salida) y el coste en € de esa llamada. Sirve para
    comprobar al momento cuánto cuesta una petición sin mirar la factura.
    payload: {prompt?, model?}"""
    from services.ai_usage import cost_of, record_ai_tokens
    p = payload or {}
    prompt = str(p.get("prompt") or "Responde solo con la palabra: OK").strip()
    model = str(p.get("model") or "gemini-2.5-flash").strip()
    try:
        from services.llm_vision import get_gemini_key
        from google import genai as google_genai
        key = get_gemini_key()
        if not key:
            raise HTTPException(status_code=400, detail="No hay clave del motor de IA configurada en el servidor")
        client = google_genai.Client(api_key=key)
        import asyncio
        def _call():
            return client.models.generate_content(model=model, contents=prompt)
        resp = await asyncio.get_event_loop().run_in_executor(None, _call)
        um = getattr(resp, "usage_metadata", None)
        in_tok = int(getattr(um, "prompt_token_count", 0) or 0)
        out_tok = int(getattr(um, "candidates_token_count", 0) or 0)
        eur = cost_of(model, in_tok, out_tok, 0)
        # Se registra también en el contador del mes (cuenta como una llamada real).
        await record_ai_tokens("probe", model, in_tok, out_tok, 0, str((user or {}).get("id", "")))
        return {
            "success": True,
            "model": model,
            "input_tokens": in_tok,
            "output_tokens": out_tok,
            "total_tokens": in_tok + out_tok,
            "cost_eur": round(eur, 6),
            "cost_eur_1000": round(eur * 1000, 4),  # coste si se repitiera 1.000 veces
            "text": (getattr(resp, "text", "") or "")[:200],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ai-usage probe error: {e}")
        raise HTTPException(status_code=500, detail=f"No se pudo medir la petición: {str(e)[:200]}")


# ─── Planes de Suscripción SaaS ──────────────────────────────────────────────
SUBSCRIPTION_PLANS = {
    "starter": {
        "id": "starter", "name": "Starter", "price": 79, "color": "#6366f1",
        "aiCreditsMonthly": 10,
        "description": "Autónomos y carpinteros. 10 renders/mes.",
        "features": ["CRM ilimitado", "Presupuestador", "Pedidos y Albaranes", "Rentabilidad básica", "10 renders IA/mes", "30 bocetos IA/mes", "50 docs clasificación IA/mes"],
    },
    "profesional": {
        "id": "profesional", "name": "Profesional", "price": 179, "color": "#0891b2",
        "aiCreditsMonthly": 40,
        "description": "Tiendas de cocinas y estudios de interiorismo.",
        "features": ["Todo Starter", "Estudio 3D completo", "Armarios IA", "Digitalizador OCR", "Obra Nueva IA", "40 renders IA/mes", "150 bocetos IA/mes", "200 docs clasificación IA/mes", "Panel de Mando"],
    },
    "business": {
        "id": "business", "name": "Business", "price": 349, "color": "#059669",
        "aiCreditsMonthly": 120,
        "description": "Fabricantes y tiendas grandes.",
        "features": ["Todo Profesional", "Fábrica y Producción", "Agentes IA", "120 renders IA/mes", "500 bocetos IA/mes", "Clasificación ilimitada", "Marca blanca", "Soporte prioritario"],
    },
    "enterprise": {
        "id": "enterprise", "name": "Enterprise", "price": 699, "color": "#7c3aed",
        "aiCreditsMonthly": 400,
        "description": "Grandes superficies y franquicias.",
        "features": ["Todo Business", "400 renders IA/mes", "IA sin límites prácticos", "API propia", "Onboarding dedicado", "SLA garantizado", "Usuarios ilimitados"],
    },
    "custom": {
        "id": "custom", "name": "Personalizado", "price": 0, "color": "#64748b",
        "aiCreditsMonthly": 0,
        "description": "Plan personalizado con créditos a medida.",
        "features": ["Configuración a medida"],
    },
}

@router.get("/subscription/plans")
async def get_subscription_plans(user=Depends(require_admin)):
    return {"success": True, "plans": list(SUBSCRIPTION_PLANS.values())}

@router.get("/subscription/users")
async def get_subscription_users(user=Depends(require_admin)):
    from config import db as main_db
    users = await main_db.users.find({}, {"_id": 0, "password": 0}).to_list(None)
    result = []
    for u in users:
        plan_id = u.get("subscriptionPlan", "")
        plan = SUBSCRIPTION_PLANS.get(plan_id, {})
        result.append({
            "id": u.get("id"), "username": u.get("username"),
            "clientName": u.get("clientName", ""), "isActive": u.get("isActive", True),
            "subscriptionPlan": plan_id, "planName": plan.get("name", "Sin plan"),
            "planColor": plan.get("color", "#64748b"),
            "aiCreditsMonthly": u.get("aiCreditsMonthly", 0),
            "subscriptionStartDate": u.get("subscriptionStartDate", ""),
            "subscriptionNotes": u.get("subscriptionNotes", ""),
        })
    return {"success": True, "users": result}

@router.post("/subscription/assign")
async def assign_subscription(payload: dict, user=Depends(require_admin)):
    """Asigna un plan a uno o varios usuarios. payload: {user_ids, plan_id, custom_credits?, notes?}"""
    from config import db as main_db
    user_ids = payload.get("user_ids", [])
    plan_id = payload.get("plan_id", "")
    custom_credits = payload.get("custom_credits", None)
    notes = payload.get("notes", "")
    if not user_ids:
        raise HTTPException(status_code=400, detail="Se requiere al menos un user_id")
    plan = SUBSCRIPTION_PLANS.get(plan_id)
    if not plan and plan_id not in ("", "custom"):
        raise HTTPException(status_code=400, detail=f"Plan '{plan_id}' no existe")
    credits = custom_credits if custom_credits is not None else (plan.get("aiCreditsMonthly", 0) if plan else 0)
    update_fields = {
        "subscriptionPlan": plan_id, "aiCreditsMonthly": credits,
        "subscriptionStartDate": datetime.utcnow().strftime("%Y-%m-%d"),
    }
    if notes:
        update_fields["subscriptionNotes"] = notes
    updated = 0
    for uid in user_ids:
        res = await main_db.users.update_one({"id": uid}, {"$set": update_fields})
        if res.modified_count:
            updated += 1
    return {"success": True, "updated": updated, "plan": plan.get("name", plan_id) if plan else plan_id, "aiCreditsMonthly": credits}

@router.get("/subscription/credits-usage")
async def get_credits_usage(user=Depends(require_admin)):
    """Consumo de créditos de IA de todos los usuarios en el mes actual."""
    from config import db as main_db
    from services.ai_usage import _month
    month = _month()
    credits_docs = await main_db.ai_credits.find({"month": month}, {"_id": 0}).to_list(None)
    credits_map = {d["user_id"]: d.get("consumed", 0) for d in credits_docs}
    users = await main_db.users.find({}, {"_id": 0, "password": 0}).to_list(None)
    result = []
    for u in users:
        uid = str(u.get("id", ""))
        assigned = int(u.get("aiCreditsMonthly", 0) or 0)
        consumed = int(credits_map.get(uid, 0))
        plan_id = u.get("subscriptionPlan", "")
        plan = SUBSCRIPTION_PLANS.get(plan_id, {})
        if assigned <= 0:
            assigned = plan.get("aiCreditsMonthly", 0)
        remaining = max(assigned - consumed, 0)
        pct = round(consumed / assigned * 100, 1) if assigned > 0 else 0
        result.append({
            "id": uid, "username": u.get("username"), "clientName": u.get("clientName", ""),
            "subscriptionPlan": plan_id, "planName": plan.get("name", "Sin plan"),
            "planColor": plan.get("color", "#64748b"),
            "assigned": assigned, "consumed": consumed, "remaining": remaining,
            "pct": pct, "over": assigned > 0 and consumed >= assigned,
        })
    return {"success": True, "month": month, "users": result}
