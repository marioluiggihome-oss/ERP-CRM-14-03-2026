"""
Luiggi Floor — división de suelo SPC porcelánico.

Catálogo de 3 colores (Roble Volare, Roble Fusión, Roble Vera), con precio por m²
y STOCK real en paquetes (cada paquete = 2,787 m²). El presupuestador del frontend
calcula paquetes/m²/precio; aquí se gestionan productos y stock.

Colección: floor_products
  { id, key, name, dims, swatchFrom, swatchTo, image, pricePerM2, stockPackages,
    m2PerPackage, updatedAt }
"""
from fastapi import APIRouter, HTTPException, Response, Depends
from datetime import datetime, timezone
from typing import Optional
import logging
import os
import uuid
import base64
import unicodedata
from urllib.parse import quote
from motor.motor_asyncio import AsyncIOMotorClient

try:
    from services.jwt_service import get_current_user, ADMIN_ROLE_FLAGS
except Exception:  # pragma: no cover - fallback si cambia la ruta
    async def get_current_user():
        return None
    ADMIN_ROLE_FLAGS = ["isAdmin"]

logger = logging.getLogger(__name__)
router = APIRouter(tags=["floor"])

# Estados de un pedido de Luiggi Floor
FLOOR_ORDER_STATES = ("presupuestado", "reservado", "entregado")
# Estados que descuentan stock (reservado y entregado retiran material del almacén)
_DEDUCT_STATES = ("reservado", "entregado")

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'luiggi_home')
client = AsyncIOMotorClient(MONGO_URL, serverSelectionTimeoutMS=5000, connectTimeoutMS=10000, maxPoolSize=5)
db = client[DB_NAME]

M2_PER_PACKAGE = 2.787

_SEED = [
    {"key": "volare", "name": "Roble Volare", "dims": "1524 × 228 × 6mm (5+1 IXPE)",
     "swatchFrom": "#d3b78f", "swatchTo": "#a9885f"},
    {"key": "fusion", "name": "Roble Fusión", "dims": "1524 × 228 × 6mm (5+1 IXPE)",
     "swatchFrom": "#aaa093", "swatchTo": "#857c70"},
    {"key": "vera", "name": "Roble Vera", "dims": "1524 × 228 × 6mm (5+1 IXPE)",
     "swatchFrom": "#dcbd97", "swatchTo": "#b48c66"},
]


async def _ensure_seed():
    n = await db.floor_products.count_documents({})
    if n == 0:
        now = datetime.now(timezone.utc).isoformat()
        for s in _SEED:
            await db.floor_products.insert_one({
                "id": f"floor-{s['key']}",
                "key": s["key"],
                "name": s["name"],
                "dims": s["dims"],
                "swatchFrom": s["swatchFrom"],
                "swatchTo": s["swatchTo"],
                "image": "",
                "pricePerM2": 37.95,  # precio base editable
                "stockPackages": 0.0,
                "m2PerPackage": M2_PER_PACKAGE,
                "createdAt": now,
                "updatedAt": now,
            })


@router.get("/floor/products")
async def list_floor_products():
    """Lista los 3 colores de suelo (los crea la primera vez)."""
    await _ensure_seed()
    items = await db.floor_products.find({}, {"_id": 0}).to_list(50)
    # Orden fijo: volare, fusion, vera
    order = {"volare": 0, "fusion": 1, "vera": 2}
    items.sort(key=lambda x: order.get(x.get("key"), 9))
    return {"items": items, "m2PerPackage": M2_PER_PACKAGE}


@router.put("/floor/products/{product_id}")
async def update_floor_product(product_id: str, payload: dict):
    """Actualiza SOLO foto, precio/m² y stock. El nombre, medidas y tono del color
    quedan FIJOS (los 3 colores no se modifican ni se añaden/eliminan)."""
    update = {}
    if "pricePerM2" in payload:
        try: update["pricePerM2"] = round(float(payload["pricePerM2"]), 2)
        except Exception: pass
    if "stockPackages" in payload:
        try: update["stockPackages"] = round(float(payload["stockPackages"]), 3)
        except Exception: pass
    if "image" in payload:
        update["image"] = str(payload["image"] or "")
    if not update:
        raise HTTPException(status_code=400, detail="Nada que actualizar")
    update["updatedAt"] = datetime.now(timezone.utc).isoformat()
    res = await db.floor_products.update_one({"id": product_id}, {"$set": update})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Color no encontrado")
    doc = await db.floor_products.find_one({"id": product_id}, {"_id": 0})
    return {"success": True, "product": doc}


@router.post("/floor/products/{product_id}/stock")
async def adjust_floor_stock(product_id: str, payload: dict):
    """Ajusta el stock en paquetes (delta + o −), p. ej. entrada/salida de mercancía."""
    try:
        delta = float((payload or {}).get("delta") or 0)
    except Exception:
        delta = 0
    doc = await db.floor_products.find_one({"id": product_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Color no encontrado")
    nuevo = round(max(0.0, float(doc.get("stockPackages", 0) or 0) + delta), 3)
    await db.floor_products.update_one(
        {"id": product_id},
        {"$set": {"stockPackages": nuevo, "updatedAt": datetime.now(timezone.utc).isoformat()}},
    )
    return {"success": True, "stockPackages": nuevo}


# ============================================================================
# CATÁLOGOS / MATERIAL DESCARGABLE (PDFs para compartir con clientes)
# Colección: floor_docs { id, name, mime, dataBase64, size, createdAt }
# ============================================================================

@router.post("/floor/docs")
async def upload_floor_doc(payload: dict):
    """Sube un catálogo/PDF (base64) para descargar y compartir."""
    b64 = (payload or {}).get("fileBase64") or ""
    name = str((payload or {}).get("name") or "Catálogo").strip()
    if not b64:
        raise HTTPException(status_code=400, detail="Falta el archivo")
    mime = "application/octet-stream"
    if b64.startswith("data:"):
        header, b64 = b64.split(",", 1)
        if ";" in header and ":" in header:
            mime = header.split(":", 1)[1].split(";", 1)[0] or mime
    mime = str((payload or {}).get("mime") or mime)
    try:
        size = int(len(b64) * 3 / 4)
    except Exception:
        size = 0
    if size > 14 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="El archivo supera el tamaño máximo permitido (14MB)")
    doc = {
        "id": f"floordoc-{uuid.uuid4().hex[:8]}",
        "name": name,
        "mime": mime,
        "dataBase64": b64,
        "size": size,
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }
    try:
        await db.floor_docs.insert_one(doc)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"No se pudo guardar el archivo: {e}")
    return {"success": True, "id": doc["id"], "name": doc["name"], "mime": mime, "size": size}


@router.get("/floor/docs")
async def list_floor_docs():
    """Lista de catálogos (solo metadatos, sin el base64)."""
    items = await db.floor_docs.find({}, {"_id": 0, "dataBase64": 0}).sort("createdAt", -1).to_list(200)
    return {"items": items}


@router.get("/floor/docs/{doc_id}/file")
async def get_floor_doc_file(doc_id: str, download: bool = False):
    """Devuelve el archivo (público, para descargar/compartir con clientes)."""
    d = await db.floor_docs.find_one({"id": doc_id}, {"_id": 0})
    if not d:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    try:
        data = base64.b64decode(d.get("dataBase64", ""))
    except Exception:
        raise HTTPException(status_code=500, detail="Documento corrupto")
    name = (d.get("name") or "catalogo").replace('"', '')
    if not name.lower().endswith(".pdf") and "pdf" in (d.get("mime") or ""):
        name += ".pdf"
    disp = "attachment" if download else "inline"
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode() or "catalogo.pdf"
    encoded_name = quote(name)
    return Response(content=data, media_type=d.get("mime") or "application/pdf",
                    headers={
                        "Content-Disposition": f"{disp}; filename=\"{ascii_name}\"; filename*=UTF-8''{encoded_name}",
                        "Content-Length": str(len(data)),
                    })


@router.delete("/floor/docs/{doc_id}")
async def delete_floor_doc(doc_id: str):
    await db.floor_docs.delete_one({"id": doc_id})
    return {"success": True}


# ============================================================================
# AJUSTES DE LUIGGI FLOOR (logo de marca para cabecera y PDF)
# Colección: floor_settings  { id:'floor-settings', logo }
# ============================================================================

@router.get("/floor/settings")
async def get_floor_settings():
    s = await db.floor_settings.find_one({"id": "floor-settings"}, {"_id": 0})
    return s or {"id": "floor-settings", "logo": ""}


@router.get("/floor/public-logo")
async def get_floor_public_logo():
    """Logo de marca Luiggi Floor para la pantalla de login (público, solo lectura).

    Expone únicamente el logo de Luiggi Floor (el que se muestra antes de iniciar
    sesión, como acceso directo a la división de suelo). No revela ningún otro ajuste.
    """
    s = await db.floor_settings.find_one({"id": "floor-settings"}, {"_id": 0, "logo": 1})
    return {"logo": s.get("logo") if s else None}


@router.put("/floor/settings")
async def update_floor_settings(payload: dict):
    update = {}
    if "logo" in payload:
        update["logo"] = str(payload["logo"] or "")
    if not update:
        raise HTTPException(status_code=400, detail="Nada que actualizar")
    update["updatedAt"] = datetime.now(timezone.utc).isoformat()
    await db.floor_settings.update_one(
        {"id": "floor-settings"}, {"$set": {"id": "floor-settings", **update}}, upsert=True
    )
    return {"success": True}


# ============================================================================
# PEDIDOS DE LUIGGI FLOOR
# Colección: floor_orders
#   { id, cliente, items[], base, iva, total, estado, stockDeducted,
#     createdByUserId, createdByName, createdAt, updatedAt }
# Estados: presupuestado (sin stock) | reservado (descuenta stock) | entregado
# Aislamiento: cada usuario ve SOLO sus pedidos; admin/dirección ven todos y
# pueden modificar estado (lo reservado descuenta stock).
# ============================================================================

def _is_elevated(user: Optional[dict]) -> bool:
    return bool(user and any(user.get(f) for f in ADMIN_ROLE_FLAGS))


async def _apply_stock_for_state(order: dict, new_state: str):
    """Reconcilia el stock según el estado: descuenta paquetes cuando pasa a
    reservado/entregado y los devuelve si vuelve a presupuestado."""
    currently_deducted = bool(order.get("stockDeducted"))
    should_deduct = new_state in _DEDUCT_STATES
    if should_deduct == currently_deducted:
        return currently_deducted  # sin cambios
    # Signo: -1 para descontar, +1 para devolver
    sign = -1.0 if should_deduct else 1.0
    for it in (order.get("items") or []):
        pid = it.get("productId") or it.get("id")
        try:
            paquetes = float(it.get("paquetes") or 0)
        except Exception:
            paquetes = 0.0
        if not pid or paquetes <= 0:
            continue
        prod = await db.floor_products.find_one({"id": pid}, {"_id": 0})
        if not prod:
            continue
        nuevo = round(max(0.0, float(prod.get("stockPackages", 0) or 0) + sign * paquetes), 3)
        await db.floor_products.update_one(
            {"id": pid},
            {"$set": {"stockPackages": nuevo, "updatedAt": datetime.now(timezone.utc).isoformat()}},
        )
    return should_deduct


@router.post("/floor/orders")
async def create_floor_order(payload: dict, current_user: Optional[dict] = Depends(get_current_user)):
    """Graba un pedido de Luiggi Floor. Por defecto en estado 'presupuestado'.
    Si se crea directamente como 'reservado', descuenta stock."""
    p = payload or {}
    estado = str(p.get("estado") or "presupuestado").lower()
    if estado not in FLOOR_ORDER_STATES:
        estado = "presupuestado"
    items = p.get("items") or []
    if not isinstance(items, list) or not items:
        raise HTTPException(status_code=400, detail="El pedido no tiene líneas")
    now = datetime.now(timezone.utc).isoformat()
    order = {
        "id": f"floorord-{uuid.uuid4().hex[:8]}",
        "cliente": str(p.get("cliente") or "").strip(),
        "clienteDatos": (p.get("clienteDatos") if isinstance(p.get("clienteDatos"), dict) else {}),
        "items": items,
        "base": round(float(p.get("base") or 0), 2),
        "iva": round(float(p.get("iva") or 0), 2),
        "total": round(float(p.get("total") or 0), 2),
        "notas": str(p.get("notas") or ""),
        "estado": estado,
        "stockDeducted": False,
        "createdByUserId": (current_user or {}).get("id"),
        "createdByName": (current_user or {}).get("name") or (current_user or {}).get("username") or "—",
        "createdAt": now,
        "updatedAt": now,
    }
    order["stockDeducted"] = await _apply_stock_for_state(order, estado)
    await db.floor_orders.insert_one(dict(order))
    order.pop("_id", None)
    return {"success": True, "order": order}


@router.get("/floor/orders")
async def list_floor_orders(estado: Optional[str] = None,
                            current_user: Optional[dict] = Depends(get_current_user)):
    """Lista pedidos. Aislamiento: cada usuario ve los suyos; admin/dirección ven todos."""
    query = {}
    if estado and estado in FLOOR_ORDER_STATES:
        query["estado"] = estado
    if not _is_elevated(current_user) and current_user and current_user.get("id"):
        query["createdByUserId"] = current_user["id"]
    items = await db.floor_orders.find(query, {"_id": 0}).sort("createdAt", -1).to_list(2000)
    return {"items": items, "isAdmin": _is_elevated(current_user)}


@router.put("/floor/orders/{order_id}")
async def update_floor_order(order_id: str, payload: dict,
                             current_user: Optional[dict] = Depends(get_current_user)):
    """Modifica un pedido. Cambiar el estado a 'reservado'/'entregado' descuenta
    stock; volver a 'presupuestado' lo devuelve. Sólo admin/dirección puede
    cambiar estado o editar pedidos ajenos; el dueño puede editar los suyos en
    estado 'presupuestado'."""
    order = await db.floor_orders.find_one({"id": order_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    elevated = _is_elevated(current_user)
    is_owner = current_user and order.get("createdByUserId") == current_user.get("id")
    if not elevated and not is_owner:
        raise HTTPException(status_code=403, detail="No autorizado")

    p = payload or {}
    update = {}
    # Cambio de estado: sólo admin/dirección (descuenta o devuelve stock)
    new_state = str(p.get("estado") or "").lower()
    if new_state and new_state in FLOOR_ORDER_STATES and new_state != order.get("estado"):
        if not elevated:
            raise HTTPException(status_code=403, detail="Sólo el administrador cambia el estado")
        update["stockDeducted"] = await _apply_stock_for_state(order, new_state)
        update["estado"] = new_state

    # La observación del pedido (notas) se puede editar SIEMPRE (dueño o admin):
    # es una nota para tener en cuenta al servir, no afecta a stock ni precio.
    if "notas" in p:
        update["notas"] = str(p.get("notas") or "")
    if "clienteDatos" in p and isinstance(p["clienteDatos"], dict):
        update["clienteDatos"] = p["clienteDatos"]

    # Edición de campos básicos (el dueño sólo si sigue 'presupuestado')
    if not order.get("estado") == "presupuestado" and not elevated:
        # ya reservado/entregado: el dueño no edita líneas
        pass
    else:
        for k in ("cliente",):
            if k in p:
                update[k] = str(p.get(k) or "")
        for k in ("base", "iva", "total"):
            if k in p:
                try: update[k] = round(float(p.get(k) or 0), 2)
                except Exception: pass
        if "items" in p and isinstance(p["items"], list):
            update["items"] = p["items"]

    if not update:
        raise HTTPException(status_code=400, detail="Nada que actualizar")
    update["updatedAt"] = datetime.now(timezone.utc).isoformat()
    await db.floor_orders.update_one({"id": order_id}, {"$set": update})
    doc = await db.floor_orders.find_one({"id": order_id}, {"_id": 0})
    return {"success": True, "order": doc}


@router.delete("/floor/orders/{order_id}")
async def delete_floor_order(order_id: str, current_user: Optional[dict] = Depends(get_current_user)):
    """Elimina un pedido (devolviendo stock si estaba reservado). Admin o dueño
    (si está en 'presupuestado')."""
    order = await db.floor_orders.find_one({"id": order_id}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    elevated = _is_elevated(current_user)
    is_owner = current_user and order.get("createdByUserId") == current_user.get("id")
    if not elevated and not (is_owner and order.get("estado") == "presupuestado"):
        raise HTTPException(status_code=403, detail="No autorizado")
    # Devolver stock si estaba descontado
    if order.get("stockDeducted"):
        await _apply_stock_for_state(order, "presupuestado")
    await db.floor_orders.delete_one({"id": order_id})
    return {"success": True}
