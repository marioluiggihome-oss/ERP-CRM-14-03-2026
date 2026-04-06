"""
Products router
"""
from fastapi import APIRouter, HTTPException, File, UploadFile
from typing import List, Optional
import uuid
import logging
import base64
import json
import os

from models.product import ProductModel, ProductCreate, ZonePoints
from services.database import db

router = APIRouter(prefix="/api", tags=["products"])
logger = logging.getLogger(__name__)


@router.get("/products", response_model=List[ProductModel])
async def get_products(module: Optional[str] = None):
    """Get all products, optionally filtered by module"""
    query = {}
    if module:
        query["module"] = module
    products = await db.products.find(query, {"_id": 0}).to_list(10000)
    return products


@router.get("/products/{product_id}", response_model=ProductModel)
async def get_product(product_id: str):
    """Get a product by ID"""
    product = await db.products.find_one({"id": product_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product


@router.post("/products", response_model=ProductModel)
async def create_product(product: ProductCreate):
    """Create a new product"""
    product_obj = ProductModel(**product.model_dump())
    product_obj.code = product_obj.code.upper()
    
    if product_obj.zonePoints:
        product_obj.points = product_obj.zonePoints.Z1
    
    await db.products.insert_one(product_obj.model_dump())
    return product_obj


@router.post("/products/bulk")
async def create_products_bulk(products: List[dict]):
    """Create multiple products - accepts flexible data from AI importer"""
    created = []
    errors = []
    duplicates = 0
    
    for idx, product_data in enumerate(products):
        try:
            clean_data = {
                "code": str(product_data.get("code", "")).upper().strip(),
                "name": str(product_data.get("name", "")),
                "category": str(product_data.get("category", "")),
                "series": str(product_data.get("series", "")),
                "visualType": str(product_data.get("visualType", "")),
                "width": float(product_data.get("width", 0) or 0),
                "height": float(product_data.get("height", 0) or 0),
                "depth": float(product_data.get("depth", 0) or 0),
                "manufacturer": str(product_data.get("manufacturer", "Zona Cocinas")),
                "points": float(product_data.get("points", 0) or 0),
                "module": str(product_data.get("module", "montada"))
            }
            
            if not clean_data["code"]:
                errors.append(f"Producto {idx}: código vacío")
                continue
            
            existing = await db.products.find_one({"code": clean_data["code"]})
            if existing:
                duplicates += 1
                continue
            
            zone_points_data = product_data.get("zonePoints")
            if zone_points_data and isinstance(zone_points_data, dict):
                clean_data["zonePoints"] = {
                    f"Z{i}": float(zone_points_data.get(f"Z{i}", 0) or 0) for i in range(1, 13)
                }
                clean_data["points"] = clean_data["zonePoints"]["Z1"]
            
            clean_data["id"] = f"prod-{uuid.uuid4().hex[:8]}"
            await db.products.insert_one(clean_data)
            clean_data.pop("_id", None)
            created.append(clean_data)
            
        except Exception as e:
            logger.error(f"Error creating product {idx}: {e}")
            errors.append(f"Producto {idx} ({product_data.get('code', '?')}): {str(e)}")
    
    logger.info(f"Bulk create: {len(created)} created, {duplicates} duplicates, {len(errors)} errors")
    
    return {
        "created": len(created),
        "duplicates": duplicates,
        "errors": errors,
        "products": created
    }


@router.put("/products/{product_id}", response_model=ProductModel)
async def update_product(product_id: str, product: ProductCreate):
    """Update a product"""
    existing = await db.products.find_one({"id": product_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    update_data = product.model_dump()
    update_data["code"] = update_data["code"].upper()
    if update_data.get("zonePoints"):
        update_data["points"] = update_data["zonePoints"]["Z1"]
    
    await db.products.update_one({"id": product_id}, {"$set": update_data})
    updated = await db.products.find_one({"id": product_id}, {"_id": 0})
    return updated


@router.delete("/products/{product_id}")
async def delete_product(product_id: str):
    """Delete a product"""
    result = await db.products.delete_one({"id": product_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return {"message": "Producto eliminado"}


@router.delete("/products/bulk/delete")
async def delete_products_bulk(product_ids: List[str]):
    """Delete multiple products"""
    if not product_ids:
        return {"deleted": 0}
    
    result = await db.products.delete_many({"id": {"$in": product_ids}})
    return {"deleted": result.deleted_count}
