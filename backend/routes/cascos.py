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
    from services.jwt_service import get_current_user, ADMIN_ROLE_FLAGS
except Exception:
    async def get_current_user():
        return None
    ADMIN_ROLE_FLAGS = ["isAdmin", "isGerente", "isDirectorComercial"]

logger = logging.getLogger(__name__)
router = APIRouter(tags=["cascos"])

mongo_url = os.environ.get('MONGO_URL')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'luiggi_home')]


@router.post("/cascos/orders")
async def create_casco_order(payload: dict, current_user: Optional[dict] = Depends(get_current_user)):
    """Crea (guarda) un pedido de cascos."""
    try:
        oid = (payload or {}).get("id") or f"casco-{uuid.uuid4().hex[:10]}"
        now = datetime.now(timezone.utc).isoformat()
        existing = await db.cascos_orders.find_one({"id": oid}, {"_id": 0, "createdAt": 1})
        doc = {
            "id": oid,
            "userId": payload.get("userId") or (current_user or {}).get("id") or "anonymous",
            "kind": str(payload.get("kind") or "pedido"),   # 'presupuesto' | 'pedido'
            "cliente": str(payload.get("cliente") or ""),
            "ref": str(payload.get("ref") or ""),
            "ivaRate": float(payload.get("ivaRate") or 21),
            "descuento": float(payload.get("descuento") or 0),
            "lines": payload.get("lines") or [],
            "total": float(payload.get("total") or 0),
            "createdByName": payload.get("createdByName", ""),
            "createdAt": (existing or {}).get("createdAt") or now,
            "updatedAt": now,
        }
        await db.cascos_orders.update_one({"id": oid}, {"$set": doc}, upsert=True)
        doc.pop("_id", None)
        return {"success": True, "order": doc}
    except Exception as e:
        logger.error(f"Create casco order error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cascos/orders")
async def list_casco_orders(userId: Optional[str] = None, kind: Optional[str] = None, current_user: Optional[dict] = Depends(get_current_user)):
    """Lista los pedidos/presupuestos de cascos. Aislamiento por usuario (admin ve todos)."""
    try:
        query = {}
        if kind:
            query["kind"] = kind
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


@router.get("/cascos/orders/{order_id}")
async def get_casco_order(order_id: str, current_user: Optional[dict] = Depends(get_current_user)):
    o = await db.cascos_orders.find_one({"id": order_id}, {"_id": 0})
    if not o:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return o


@router.delete("/cascos/orders/{order_id}")
async def delete_casco_order(order_id: str, current_user: Optional[dict] = Depends(get_current_user)):
    await db.cascos_orders.delete_one({"id": order_id})
    return {"success": True}
