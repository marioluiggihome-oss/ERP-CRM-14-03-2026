"""
Pedidos del Presupuestador de Cascos (Grupo ACB). Módulo independiente:
guarda los pedidos de cascos por usuario. El catálogo vive en el frontend
(generado desde la tarifa oficial).
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from typing import Optional
import logging
import os
import uuid
from motor.motor_asyncio import AsyncIOMotorClient

try:
    from services.jwt_service import get_current_user, require_auth, ADMIN_ROLE_FLAGS
    _CASCOS_DEPS = [Depends(require_auth)]
except Exception:
    async def get_current_user():
        return None
    ADMIN_ROLE_FLAGS = ["isAdmin", "isGerente", "isDirectorComercial"]
    _CASCOS_DEPS = []

logger = logging.getLogger(__name__)
# Todos los pedidos de cascos requieren token válido (aislamiento por usuario dentro).
router = APIRouter(tags=["cascos"], dependencies=_CASCOS_DEPS)


def _safe_float(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default

mongo_url = os.environ.get('MONGO_URL')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'luiggi_home')]


@router.post("/cascos/orders")
async def create_casco_order(payload: dict, current_user: Optional[dict] = Depends(get_current_user)):
    """Crea (guarda) un pedido de cascos."""
    try:
        uid = (current_user or {}).get("id") or "anonymous"
        oid = (payload or {}).get("id") or f"casco-{uuid.uuid4().hex[:10]}"
        now = datetime.now(timezone.utc).isoformat()
        existing = await db.cascos_orders.find_one({"id": oid}, {"_id": 0, "createdAt": 1, "userId": 1})
        # Al re-guardar por id, comprobar propiedad (evita pisar el pedido de otro).
        if existing and not _can_access(existing, current_user):
            raise HTTPException(status_code=403, detail="Sin acceso a este pedido")
        doc = {
            "id": oid,
            "userId": (existing or {}).get("userId") or uid,  # nunca se toma del payload
            "kind": str(payload.get("kind") or "pedido"),   # 'presupuesto' | 'pedido' | 'compra'
            "expediente": str(payload.get("expediente") or ""),  # vínculo venta <-> compra
            "cliente": str(payload.get("cliente") or ""),
            "ref": str(payload.get("ref") or ""),
            "ivaRate": _safe_float(payload.get("ivaRate"), 21),
            "descuento": _safe_float(payload.get("descuento"), 0),
            "lines": payload.get("lines") or [],
            "total": _safe_float(payload.get("total"), 0),
            "createdByName": payload.get("createdByName", ""),
            "createdAt": (existing or {}).get("createdAt") or now,
            "updatedAt": now,
        }
        await db.cascos_orders.update_one({"id": oid}, {"$set": doc}, upsert=True)
        doc.pop("_id", None)
        return {"success": True, "order": doc}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create casco order error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cascos/orders")
async def list_casco_orders(userId: Optional[str] = None, kind: Optional[str] = None, expediente: Optional[str] = None, current_user: Optional[dict] = Depends(get_current_user)):
    """Lista los pedidos/presupuestos de cascos. Aislamiento por usuario (admin ve todos)."""
    try:
        query = {}
        if kind:
            query["kind"] = kind
        if expediente:
            query["expediente"] = expediente
        if current_user and current_user.get("id"):
            elevated = any(current_user.get(f) for f in ADMIN_ROLE_FLAGS)
            if not elevated:
                query["userId"] = current_user["id"]
        elif userId:
            query["userId"] = userId
        orders = await db.cascos_orders.find(query, {"_id": 0}).sort("createdAt", -1).to_list(500)
        return {"success": True, "orders": orders}
    except Exception as e:
        logger.error(f"List casco orders error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _can_access(order: dict, current_user: Optional[dict]) -> bool:
    """Admin/elevado ve todo; el resto solo sus propios pedidos."""
    if not current_user or not current_user.get("id"):
        return False  # sin usuario autenticado no hay acceso
    if any(current_user.get(f) for f in ADMIN_ROLE_FLAGS):
        return True
    return order.get("userId") == current_user["id"]


@router.get("/cascos/orders/{order_id}")
async def get_casco_order(order_id: str, current_user: Optional[dict] = Depends(get_current_user)):
    o = await db.cascos_orders.find_one({"id": order_id}, {"_id": 0})
    if not o:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    if not _can_access(o, current_user):
        raise HTTPException(status_code=403, detail="Sin acceso a este pedido")
    return o


@router.delete("/cascos/orders/{order_id}")
async def delete_casco_order(order_id: str, current_user: Optional[dict] = Depends(get_current_user)):
    o = await db.cascos_orders.find_one({"id": order_id}, {"_id": 0, "userId": 1})
    if o and not _can_access(o, current_user):
        raise HTTPException(status_code=403, detail="Sin acceso a este pedido")
    await db.cascos_orders.delete_one({"id": order_id})
    return {"success": True}


# ─── IMPORTADOR DE PROFORMA DE PROVEEDOR (solo MASTER) ──────────────────────────
def _es_master(user: Optional[dict]) -> bool:
    return bool(user and any(user.get(f) for f in ADMIN_ROLE_FLAGS + ["isPrimaryAdmin"]))


@router.post("/cascos/proforma")
async def importar_proforma(payload: dict, current_user: Optional[dict] = Depends(get_current_user)):
    """Detecta los muebles de un PDF de proforma de proveedor (multipágina).
    Solo MASTER. Devuelve la relación de muebles con código, descripción, color,
    herraje, medidas, cantidad, PVP proveedor y recuento de puertas/cajones/gavetas.
    Lee la capa de texto si existe; si el PDF es imagen, usa visión IA de respaldo."""
    if not _es_master(current_user):
        raise HTTPException(status_code=403, detail="Solo el master puede importar proformas de proveedor.")
    import base64 as _b64, re as _re
    raw = (payload or {}).get("pdfBase64") or (payload or {}).get("pdf") or ""
    if not raw:
        raise HTTPException(status_code=400, detail="Falta el PDF de la proforma.")
    m = _re.match(r"^data:[^;]+;base64,(.*)$", raw, _re.DOTALL)
    b64 = m.group(1) if m else raw
    try:
        pdf_bytes = _b64.b64decode(b64)
    except Exception:
        raise HTTPException(status_code=400, detail="PDF no válido.")

    from services.proforma_cascos import (
        parse_proforma_text, extract_pdf_text_all_pages, pdf_pages_to_png_b64,
    )
    # 1) Intento por CAPA DE TEXTO (rápido y exacto).
    items = []
    try:
        txt = extract_pdf_text_all_pages(pdf_bytes)
        if txt and len(txt.strip()) > 40:
            items = parse_proforma_text(txt)
    except Exception as e:
        logger.warning("proforma: fallo lectura de texto: %s", e)

    # 2) Respaldo por VISIÓN IA (PDF escaneado/imagen sin texto).
    if not items:
        try:
            from services.llm_vision import analyze_image_with_gemini, is_vision_available
            import json as _json
            if not is_vision_available():
                raise HTTPException(status_code=503, detail="El PDF es una imagen y la IA de visión no está configurada.")
            prompt = (
                "Esta imagen es una página de una PROFORMA de muebles de cocina (cascos). "
                "Extrae la tabla de artículos. Devuelve SOLO un JSON: {\"items\":[{\"n\":1,"
                "\"cod\":\"80GF/1P1GIN\",\"descripcion\":\"...\",\"material\":\"MELAMINA ... ZENIT - MERIVOBOX\","
                "\"largo\":800,\"ancho\":500,\"grueso\":580,\"cantidad\":1,\"pvp\":402.73}]}. "
                "'pvp' es la columna PRECIO. Si una fila no es un mueble, inclúyela igual."
            )
            pages = pdf_pages_to_png_b64(pdf_bytes)
            allrows = []
            for pg in pages:
                try:
                    t = await analyze_image_with_gemini(image_base64=pg, prompt=prompt, model="gemini-2.5-pro")
                    mm = _re.search(r"\{[\s\S]*\}", t or "")
                    if mm:
                        data = _json.loads(mm.group())
                        allrows.extend(data.get("items") or [])
                except Exception as e:
                    logger.warning("proforma visión página: %s", e)
            # Reutiliza los enriquecedores del parser de texto para color/herraje/frentes.
            from services.proforma_cascos import _color_y_herraje, _cuenta_frentes, _tipo_mueble
            for r in allrows:
                material = r.get("material") or ""
                color, blum = _color_y_herraje(material)
                desc = r.get("descripcion") or ""
                fr = _cuenta_frentes(desc)
                items.append({
                    "n": r.get("n"), "cod": r.get("cod") or "", "descripcion": desc,
                    "material": material, "color": color, "herrajeBlum": blum,
                    "largo": r.get("largo"), "ancho": r.get("ancho"), "grueso": r.get("grueso"),
                    "cantidad": r.get("cantidad") or 1.0, "pvp": r.get("pvp"), "total": r.get("pvp"),
                    "puertas": fr["puertas"], "cajones": fr["cajones"], "gavetas": fr["gavetas"],
                    "tipo": _tipo_mueble(desc), "esMueble": True,
                })
        except HTTPException:
            raise
        except Exception as e:
            logger.error("proforma visión: %s", e)

    if not items:
        raise HTTPException(status_code=422, detail="No se pudieron detectar muebles en la proforma.")
    return {"success": True, "items": items, "count": len(items)}


# ─── Tarifa MV (puntos) para el módulo de Rentabilidad ──────────────────────────
import json as _mvjson, os as _mvos
_MV_PATH = _mvos.path.join(_mvos.path.dirname(_mvos.path.dirname(__file__)), "data", "mv_tarifas_oficiales.json")


@router.get("/mv/tarifa")
async def mv_tarifa(tariff: str = "T1", current_user: Optional[dict] = Depends(get_current_user)):
    """Devuelve la tarifa MV pedida (por defecto T1) con sus códigos y puntos, y el
    valor de punto. Para el módulo de Rentabilidad Tarifa MV (solo master)."""
    if not _es_master(current_user):
        raise HTTPException(status_code=403, detail="Solo el master puede ver la tarifa MV.")
    try:
        with open(_MV_PATH, "r", encoding="utf-8") as f:
            data = _mvjson.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"No se pudo leer la tarifa MV: {e}")
    tfs = data.get("tariffs", {})
    if tariff not in tfs:
        raise HTTPException(status_code=404, detail=f"Tarifa {tariff} no encontrada.")
    return {
        "success": True,
        "tariff": tariff,
        "pointValue": data.get("_meta", {}).get("pointValue", 3.33),
        "familias": tfs[tariff],
    }
