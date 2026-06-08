"""
Router para Productos del Catálogo
"""
import re
import logging
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from config import db
from models.schemas import ProductModel, ProductCreate, ZonePoints

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/products", tags=["Products"])
security = HTTPBearer(auto_error=False)  # JWT opcional

# Authentication dependency
from services.jwt_service import get_current_user as _get_current_user

async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """JWT opcional: si hay token lo valida, si no devuelve dict vacío (modo compatibilidad)."""
    if not credentials:
        return {"_compat_mode": True}
    user = await _get_current_user(credentials)
    if not user:
        return {"_compat_mode": True}
    return user


@router.get("", response_model=List[ProductModel])
async def get_products(
    module: str = None,
    category: str = None,
    search: str = None,
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """Obtener productos con filtros opcionales"""
    query = {}
    
    if module:
        query["module"] = module
    if category:
        query["category"] = category
    if search:
        _s = re.escape(search)
        query["$or"] = [
            {"name": {"$regex": _s, "$options": "i"}},
            {"code": {"$regex": _s, "$options": "i"}},
            {"reference": {"$regex": _s, "$options": "i"}}
        ]
    
    products = await db.products.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    return products


@router.get("/{product_id}", response_model=ProductModel)
async def get_product(product_id: str, current_user: dict = Depends(get_current_user)):
    """Obtener un producto por ID"""
    product = await db.products.find_one({"id": product_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product


@router.post("", response_model=ProductModel)
async def create_product(product: ProductCreate, current_user: dict = Depends(get_current_user)):
    """Crear un nuevo producto"""
    product_dict = product.model_dump()
    product_dict["id"] = f"prod-{__import__('uuid').uuid4().hex[:8]}"
    
    await db.products.insert_one(product_dict)
    return product_dict


@router.put("/{product_id}", response_model=ProductModel)
async def update_product(product_id: str, product: ProductCreate, current_user: dict = Depends(get_current_user)):
    """Actualizar un producto existente"""
    existing = await db.products.find_one({"id": product_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    update_data = product.model_dump()
    await db.products.update_one({"id": product_id}, {"$set": update_data})
    
    updated = await db.products.find_one({"id": product_id}, {"_id": 0})
    return updated


@router.patch("/{product_id}/zone-points")
async def update_zone_points(product_id: str, zone_points: ZonePoints, current_user: dict = Depends(get_current_user)):
    """Actualizar puntos por zona de un producto"""
    existing = await db.products.find_one({"id": product_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    await db.products.update_one(
        {"id": product_id},
        {"$set": {"zonePoints": zone_points.model_dump()}}
    )
    
    return {"success": True}


@router.delete("/{product_id}")
async def delete_product(product_id: str, current_user: dict = Depends(get_current_user)):
    """Eliminar un producto"""
    result = await db.products.delete_one({"id": product_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return {"success": True}


@router.get("/stats/count")
async def get_products_count(current_user: dict = Depends(get_current_user)):
    """Obtener conteo de productos por categoría"""
    pipeline = [
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    results = await db.products.aggregate(pipeline).to_list(100)
    return {
        "total": await db.products.count_documents({}),
        "by_category": {r["_id"]: r["count"] for r in results if r["_id"]}
    }
