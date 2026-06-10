"""
Luiggi Floor — división de suelo SPC porcelánico.

Catálogo de 3 colores (Roble Volare, Roble Fusión, Roble Vera), con precio por m²
y STOCK real en paquetes (cada paquete = 2,787 m²). El presupuestador del frontend
calcula paquetes/m²/precio; aquí se gestionan productos y stock.

Colección: floor_products
  { id, key, name, dims, swatchFrom, swatchTo, image, pricePerM2, stockPackages,
    m2PerPackage, updatedAt }
"""
from fastapi import APIRouter, HTTPException, Response
from datetime import datetime, timezone
from typing import Optional
import logging
import os
import uuid
import base64
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)
router = APIRouter(tags=["floor"])

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'luiggi_home')
client = AsyncIOMotorClient(MONGO_URL)
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
    """Actualiza precio/m², stock (paquetes), nombre, imagen o swatch de un color."""
    update = {}
    if "pricePerM2" in payload:
        try: update["pricePerM2"] = round(float(payload["pricePerM2"]), 2)
        except Exception: pass
    if "stockPackages" in payload:
        try: update["stockPackages"] = round(float(payload["stockPackages"]), 3)
        except Exception: pass
    for k in ("name", "dims", "image", "swatchFrom", "swatchTo"):
        if k in payload:
            update[k] = str(payload[k] or "")
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
    doc = {
        "id": f"floordoc-{uuid.uuid4().hex[:8]}",
        "name": name,
        "mime": mime,
        "dataBase64": b64,
        "size": size,
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }
    await db.floor_docs.insert_one(doc)
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
    return Response(content=data, media_type=d.get("mime") or "application/pdf",
                    headers={"Content-Disposition": f'{disp}; filename="{name}"'})


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
