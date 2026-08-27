# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
Router para el módulo DESPIECE - Presupuestador de tableros
Gestiona productos de fabricantes como ALVIC con parámetros específicos
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Dict
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timezone
import os
import uuid
from services.db_client import get_db as _get_db

# Seguridad: el modulo no exigia ningun token. No hay un permiso granular
# especifico para este presupuestador (a diferencia de Gastos/Fabrica), asi
# que se exige al menos estar logueado en vez de dejarlo abierto del todo.
try:
    from services.jwt_service import require_auth
    _DESPIECE_DEPS = [Depends(require_auth)]
except Exception:  # pragma: no cover - fallback si no hay jwt_service
    _DESPIECE_DEPS = []

router = APIRouter(prefix="/despiece-budgeter", tags=["despiece-budgeter"], dependencies=_DESPIECE_DEPS)

# MongoDB connection

# ============================================
# MODELOS
# ============================================

class DespieceProduct(BaseModel):
    """Producto de despiece (tablero/panel)"""
    id: str = Field(default_factory=lambda: f"desp-{uuid.uuid4().hex[:8]}")
    code: str
    name: str
    manufacturer: str  # ALVIC, FINSA, EGGER, etc.
    collection: str = ""  # Colección/Modelo (LUXE, ZENIT, SYNCRON, etc.)
    color: str = ""  # Nombre del color
    colorCode: str = ""  # Código del color
    finish: str = ""  # Acabado (Brillo, Mate, Textura, etc.)
    thickness: float = 18  # Grosor en mm
    format: str = ""  # Formato del tablero (2440x1220, 2800x2070, etc.)
    material: str = ""  # MDF, Aglomerado, Compacto, etc.
    # Precios por zona/grupo
    priceZ1: float = 0
    priceZ2: float = 0
    priceZ3: float = 0
    priceZ4: float = 0
    priceZ5: float = 0
    priceZ6: float = 0
    # Precio base por m2
    pricePerM2: float = 0
    # Disponibilidad
    available: bool = True
    leadTime: int = 0  # Días de entrega
    minOrder: float = 1  # Pedido mínimo (m2 o unidades)
    # Metadata
    imageUrl: str = ""
    category: str = "TABLERO"  # TABLERO, CANTO, COMPACTO, etc.
    createdAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class DespieceProductCreate(BaseModel):
    code: str
    name: str
    manufacturer: str
    collection: str = ""
    color: str = ""
    colorCode: str = ""
    finish: str = ""
    thickness: float = 18
    format: str = ""
    material: str = ""
    priceZ1: float = 0
    priceZ2: float = 0
    priceZ3: float = 0
    priceZ4: float = 0
    priceZ5: float = 0
    priceZ6: float = 0
    pricePerM2: float = 0
    available: bool = True
    leadTime: int = 0
    minOrder: float = 1
    imageUrl: str = ""
    category: str = "TABLERO"


class DespieceBudgetItem(BaseModel):
    """Línea de presupuesto de despiece"""
    id: str = Field(default_factory=lambda: f"dbi-{uuid.uuid4().hex[:8]}")
    productId: str
    productCode: str
    productName: str
    manufacturer: str
    color: str
    finish: str
    thickness: float
    # Dimensiones del corte
    width: float  # mm
    height: float  # mm
    quantity: int = 1
    # Cantos
    cantoL1: bool = False  # Canto largo 1
    cantoL2: bool = False  # Canto largo 2
    cantoW1: bool = False  # Canto ancho 1
    cantoW2: bool = False  # Canto ancho 2
    cantoType: str = ""  # Tipo de canto (mismo color, aluminio, etc.)
    # Precios calculados
    areaM2: float = 0
    unitPrice: float = 0
    totalPrice: float = 0
    notes: str = ""

    @field_validator("width", "height")
    @classmethod
    def _must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Las dimensiones del corte deben ser mayores que cero")
        return v

    @field_validator("quantity")
    @classmethod
    def _quantity_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("La cantidad debe ser mayor que cero")
        return v


class DespieceBudget(BaseModel):
    """Presupuesto completo de despiece"""
    id: str = Field(default_factory=lambda: f"dbud-{uuid.uuid4().hex[:8]}")
    budgetNumber: str
    customerName: str = ""
    customerAddress: str = ""
    projectRef: str = ""
    # Parámetros globales del presupuesto
    manufacturer: str = ""
    collection: str = ""
    mainColor: str = ""
    mainFinish: str = ""
    # Items
    items: List[DespieceBudgetItem] = []
    # Totales
    totalArea: float = 0
    totalPrice: float = 0
    discount: float = 0
    finalPrice: float = 0
    # Metadata
    userId: str = ""
    status: str = "draft"
    createdAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updatedAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ============================================
# ENDPOINTS DE PRODUCTOS
# ============================================

@router.get("/products")
async def get_despiece_products(
    manufacturer: Optional[str] = None,
    collection: Optional[str] = None,
    color: Optional[str] = None,
    finish: Optional[str] = None,
    thickness: Optional[float] = None,
    category: Optional[str] = None,
    type: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(default=500, le=2000)
):
    """Obtener productos de despiece con filtros"""
    import re
    query = {}
    
    if manufacturer:
        # Escapar caracteres especiales de regex
        safe_manufacturer = re.escape(manufacturer)
        query["manufacturer"] = {"$regex": safe_manufacturer, "$options": "i"}
    if collection:
        # Escapar caracteres especiales de regex
        safe_collection = re.escape(collection)
        query["collection"] = {"$regex": safe_collection, "$options": "i"}
    if color:
        query["$or"] = [
            {"color": {"$regex": color, "$options": "i"}},
            {"colorCode": {"$regex": color, "$options": "i"}}
        ]
    if finish:
        query["finish"] = {"$regex": finish, "$options": "i"}
    if thickness:
        query["thickness"] = thickness
    if category:
        query["category"] = category
    if type:
        query["type"] = type
    if search:
        query["$or"] = [
            {"code": {"$regex": search, "$options": "i"}},
            {"name": {"$regex": search, "$options": "i"}},
            {"color": {"$regex": search, "$options": "i"}},
            {"colorCode": {"$regex": search, "$options": "i"}}
        ]
    
    products = await _get_db().despiece_products.find(query, {"_id": 0}).sort([("type", 1), ("collection", 1), ("height", 1), ("width", 1)]).limit(limit).to_list(limit)
    return products


@router.get("/products/filters")
async def get_despiece_filters(manufacturer: str = None, collection: str = None):
    """Obtener opciones de filtros disponibles (fabricantes, colecciones, colores, etc.)
    Opcionalmente filtrar por fabricante o colección para obtener valores relacionados"""
    
    # Filtro base
    base_filter = {}
    if manufacturer:
        base_filter["manufacturer"] = manufacturer
    if collection:
        base_filter["collection"] = collection
    
    # Obtener valores únicos de cada campo
    manufacturers = await _get_db().despiece_products.distinct("manufacturer")
    
    # Colecciones filtradas por fabricante si se especifica
    collections = await _get_db().despiece_products.distinct("collection", base_filter if manufacturer else {})
    
    # Colores filtrados por fabricante y/o colección
    color_filter = {}
    if manufacturer:
        color_filter["manufacturer"] = manufacturer
    if collection:
        color_filter["collection"] = collection
    colors = await _get_db().despiece_products.distinct("color", color_filter if color_filter else {})
    
    # Otros filtros
    finishes = await _get_db().despiece_products.distinct("finish", base_filter if manufacturer else {})
    thicknesses = await _get_db().despiece_products.distinct("thickness", base_filter if manufacturer else {})
    categories = await _get_db().despiece_products.distinct("category", base_filter if manufacturer else {})
    
    return {
        "manufacturers": sorted([m for m in manufacturers if m]),
        "collections": sorted([c for c in collections if c]),
        "finishes": sorted([f for f in finishes if f]),
        "thicknesses": sorted([t for t in thicknesses if t]),
        "colors": sorted([c for c in colors if c])[:100],  # Limitar colores
        "categories": sorted([c for c in categories if c])
    }


@router.get("/products/{product_id}")
async def get_despiece_product(product_id: str):
    """Obtener un producto de despiece por ID"""
    product = await _get_db().despiece_products.find_one({"id": product_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product


@router.post("/products")
async def create_despiece_product(product: DespieceProductCreate):
    """Crear un nuevo producto de despiece"""
    product_data = product.model_dump()
    product_data["id"] = f"desp-{uuid.uuid4().hex[:8]}"
    product_data["createdAt"] = datetime.now(timezone.utc).isoformat()
    
    await _get_db().despiece_products.insert_one(product_data)
    product_data.pop("_id", None)
    return product_data


@router.post("/products/bulk")
async def create_despiece_products_bulk(products: List[Dict]):
    """Crear múltiples productos de despiece"""
    created = 0
    updated = 0
    errors = []
    
    for idx, prod in enumerate(products):
        try:
            code = prod.get("code", "").upper().strip()
            if not code:
                errors.append(f"Producto {idx}: código vacío")
                continue
            
            # Verificar si ya existe
            existing = await _get_db().despiece_products.find_one({"code": code})
            
            product_data = {
                "id": f"desp-{uuid.uuid4().hex[:8]}" if not existing else existing.get("id"),
                "code": code,
                "name": prod.get("name", ""),
                "manufacturer": prod.get("manufacturer", "ALVIC"),
                "collection": prod.get("collection", ""),
                "color": prod.get("color", ""),
                "colorCode": prod.get("colorCode", ""),
                "finish": prod.get("finish", ""),
                "thickness": float(prod.get("thickness", 18)),
                "format": prod.get("format", ""),
                "material": prod.get("material", ""),
                "priceZ1": float(prod.get("priceZ1", 0)),
                "priceZ2": float(prod.get("priceZ2", 0)),
                "priceZ3": float(prod.get("priceZ3", 0)),
                "priceZ4": float(prod.get("priceZ4", 0)),
                "priceZ5": float(prod.get("priceZ5", 0)),
                "priceZ6": float(prod.get("priceZ6", 0)),
                "pricePerM2": float(prod.get("pricePerM2", 0)),
                "available": prod.get("available", True),
                "leadTime": int(prod.get("leadTime", 0)),
                "minOrder": float(prod.get("minOrder", 1)),
                "imageUrl": prod.get("imageUrl", ""),
                "category": prod.get("category", "TABLERO"),
                "createdAt": existing.get("createdAt") if existing else datetime.now(timezone.utc).isoformat()
            }
            
            if existing:
                await _get_db().despiece_products.update_one({"code": code}, {"$set": product_data})
                updated += 1
            else:
                await _get_db().despiece_products.insert_one(product_data)
                created += 1
                
        except Exception as e:
            errors.append(f"Producto {idx} ({prod.get('code', '?')}): {str(e)}")
    
    return {
        "created": created,
        "updated": updated,
        "errors": errors,
        "total": len(products)
    }


@router.delete("/products/{product_id}")
async def delete_despiece_product(product_id: str):
    """Eliminar un producto de despiece"""
    result = await _get_db().despiece_products.delete_one({"id": product_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return {"message": "Producto eliminado"}


# ============================================
# ENDPOINTS DE PRESUPUESTOS
# ============================================

@router.get("/budgets")
async def get_despiece_budgets(
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(default=100, le=500)
):
    """Obtener presupuestos de despiece"""
    query = {}
    if user_id:
        query["userId"] = user_id
    if status:
        query["status"] = status
    
    budgets = await _get_db().despiece_budgets.find(query, {"_id": 0}).sort("createdAt", -1).limit(limit).to_list(limit)
    return budgets


@router.get("/budgets/{budget_id}")
async def get_despiece_budget(budget_id: str):
    """Obtener un presupuesto de despiece por ID"""
    budget = await _get_db().despiece_budgets.find_one({"id": budget_id}, {"_id": 0})
    if not budget:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    return budget


@router.post("/budgets")
async def create_despiece_budget(budget: dict):
    """Crear un nuevo presupuesto de despiece"""
    budget_data = {
        "id": f"dbud-{uuid.uuid4().hex[:8]}",
        "budgetNumber": budget.get("budgetNumber", ""),
        "customerName": budget.get("customerName", ""),
        "customerAddress": budget.get("customerAddress", ""),
        "projectRef": budget.get("projectRef", ""),
        "manufacturer": budget.get("manufacturer", ""),
        "collection": budget.get("collection", ""),
        "mainColor": budget.get("mainColor", ""),
        "mainFinish": budget.get("mainFinish", ""),
        "items": budget.get("items", []),
        "totalArea": float(budget.get("totalArea", 0)),
        "totalPrice": float(budget.get("totalPrice", 0)),
        "discount": float(budget.get("discount", 0)),
        "finalPrice": float(budget.get("finalPrice", 0)),
        "userId": budget.get("userId", ""),
        "status": budget.get("status", "draft"),
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat()
    }
    
    await _get_db().despiece_budgets.insert_one(budget_data)
    budget_data.pop("_id", None)
    return budget_data


@router.put("/budgets/{budget_id}")
async def update_despiece_budget(budget_id: str, budget: dict):
    """Actualizar un presupuesto de despiece"""
    existing = await _get_db().despiece_budgets.find_one({"id": budget_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    
    update_data = {k: v for k, v in budget.items() if v is not None}
    update_data["updatedAt"] = datetime.now(timezone.utc).isoformat()
    
    await _get_db().despiece_budgets.update_one({"id": budget_id}, {"$set": update_data})
    updated = await _get_db().despiece_budgets.find_one({"id": budget_id}, {"_id": 0})
    return updated


@router.delete("/budgets/{budget_id}")
async def delete_despiece_budget(budget_id: str):
    """Eliminar un presupuesto de despiece"""
    result = await _get_db().despiece_budgets.delete_one({"id": budget_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    return {"message": "Presupuesto eliminado"}


# ============================================
# SEED DATA - Productos ALVIC de muestra
# ============================================

@router.post("/seed-alvic")
async def seed_alvic_products():
    """Poblar la base de datos con productos ALVIC de muestra"""
    
    # Productos de muestra basados en la tarifa ALVIC
    sample_products = [
        # LUXE by ALVIC - Lacados brillo
        {"code": "LUXE-BL-001", "name": "LUXE Blanco Brillo", "manufacturer": "ALVIC", "collection": "LUXE", "color": "Blanco", "colorCode": "001", "finish": "Brillo", "thickness": 18, "format": "2750x1240", "material": "MDF Lacado", "priceZ1": 85.50, "priceZ2": 88.20, "priceZ3": 91.00, "category": "TABLERO"},
        {"code": "LUXE-NE-002", "name": "LUXE Negro Brillo", "manufacturer": "ALVIC", "collection": "LUXE", "color": "Negro", "colorCode": "002", "finish": "Brillo", "thickness": 18, "format": "2750x1240", "material": "MDF Lacado", "priceZ1": 85.50, "priceZ2": 88.20, "priceZ3": 91.00, "category": "TABLERO"},
        {"code": "LUXE-GR-003", "name": "LUXE Gris Brillo", "manufacturer": "ALVIC", "collection": "LUXE", "color": "Gris", "colorCode": "003", "finish": "Brillo", "thickness": 18, "format": "2750x1240", "material": "MDF Lacado", "priceZ1": 89.00, "priceZ2": 92.00, "priceZ3": 95.00, "category": "TABLERO"},
        {"code": "LUXE-RO-004", "name": "LUXE Rojo Brillo", "manufacturer": "ALVIC", "collection": "LUXE", "color": "Rojo", "colorCode": "004", "finish": "Brillo", "thickness": 18, "format": "2750x1240", "material": "MDF Lacado", "priceZ1": 92.00, "priceZ2": 95.00, "priceZ3": 98.00, "category": "TABLERO"},
        
        # ZENIT by ALVIC - Supermatte
        {"code": "ZENIT-BL-101", "name": "ZENIT Blanco Supermatte", "manufacturer": "ALVIC", "collection": "ZENIT", "color": "Blanco", "colorCode": "101", "finish": "Supermatte", "thickness": 18, "format": "2750x1240", "material": "MDF", "priceZ1": 78.00, "priceZ2": 80.50, "priceZ3": 83.00, "category": "TABLERO"},
        {"code": "ZENIT-NE-102", "name": "ZENIT Negro Supermatte", "manufacturer": "ALVIC", "collection": "ZENIT", "color": "Negro", "colorCode": "102", "finish": "Supermatte", "thickness": 18, "format": "2750x1240", "material": "MDF", "priceZ1": 78.00, "priceZ2": 80.50, "priceZ3": 83.00, "category": "TABLERO"},
        {"code": "ZENIT-AN-103", "name": "ZENIT Antracita Supermatte", "manufacturer": "ALVIC", "collection": "ZENIT", "color": "Antracita", "colorCode": "103", "finish": "Supermatte", "thickness": 18, "format": "2750x1240", "material": "MDF", "priceZ1": 78.00, "priceZ2": 80.50, "priceZ3": 83.00, "category": "TABLERO"},
        {"code": "ZENIT-TA-104", "name": "ZENIT Taupe Supermatte", "manufacturer": "ALVIC", "collection": "ZENIT", "color": "Taupe", "colorCode": "104", "finish": "Supermatte", "thickness": 18, "format": "2750x1240", "material": "MDF", "priceZ1": 82.00, "priceZ2": 84.50, "priceZ3": 87.00, "category": "TABLERO"},
        
        # SYNCRON by ALVIC - Texturas madera
        {"code": "SYNC-ROB-201", "name": "SYNCRON Roble Natural", "manufacturer": "ALVIC", "collection": "SYNCRON", "color": "Roble Natural", "colorCode": "201", "finish": "Textura Madera", "thickness": 18, "format": "2750x1240", "material": "Melamina", "priceZ1": 45.00, "priceZ2": 47.00, "priceZ3": 49.00, "category": "TABLERO"},
        {"code": "SYNC-NOG-202", "name": "SYNCRON Nogal", "manufacturer": "ALVIC", "collection": "SYNCRON", "color": "Nogal", "colorCode": "202", "finish": "Textura Madera", "thickness": 18, "format": "2750x1240", "material": "Melamina", "priceZ1": 45.00, "priceZ2": 47.00, "priceZ3": 49.00, "category": "TABLERO"},
        {"code": "SYNC-OLM-203", "name": "SYNCRON Olmo", "manufacturer": "ALVIC", "collection": "SYNCRON", "color": "Olmo", "colorCode": "203", "finish": "Textura Madera", "thickness": 18, "format": "2750x1240", "material": "Melamina", "priceZ1": 45.00, "priceZ2": 47.00, "priceZ3": 49.00, "category": "TABLERO"},
        {"code": "SYNC-CEN-204", "name": "SYNCRON Ceniza", "manufacturer": "ALVIC", "collection": "SYNCRON", "color": "Ceniza", "colorCode": "204", "finish": "Textura Madera", "thickness": 18, "format": "2750x1240", "material": "Melamina", "priceZ1": 48.00, "priceZ2": 50.00, "priceZ3": 52.00, "category": "TABLERO"},
        
        # BASIK by ALVIC - Melaminas básicas
        {"code": "BASIK-BL-301", "name": "BASIK Blanco", "manufacturer": "ALVIC", "collection": "BASIK", "color": "Blanco", "colorCode": "301", "finish": "Liso", "thickness": 18, "format": "2440x1220", "material": "Melamina", "priceZ1": 28.00, "priceZ2": 29.50, "priceZ3": 31.00, "category": "TABLERO"},
        {"code": "BASIK-NE-302", "name": "BASIK Negro", "manufacturer": "ALVIC", "collection": "BASIK", "color": "Negro", "colorCode": "302", "finish": "Liso", "thickness": 18, "format": "2440x1220", "material": "Melamina", "priceZ1": 28.00, "priceZ2": 29.50, "priceZ3": 31.00, "category": "TABLERO"},
        {"code": "BASIK-GR-303", "name": "BASIK Gris", "manufacturer": "ALVIC", "collection": "BASIK", "color": "Gris", "colorCode": "303", "finish": "Liso", "thickness": 18, "format": "2440x1220", "material": "Melamina", "priceZ1": 28.00, "priceZ2": 29.50, "priceZ3": 31.00, "category": "TABLERO"},
        
        # CANTOS - Cantos de diferentes tipos
        {"code": "CANTO-ABS-BL", "name": "Canto ABS Blanco 22x0.8", "manufacturer": "ALVIC", "collection": "CANTOS", "color": "Blanco", "colorCode": "C001", "finish": "ABS", "thickness": 0.8, "format": "22mm", "material": "ABS", "priceZ1": 0.85, "priceZ2": 0.90, "priceZ3": 0.95, "category": "CANTO"},
        {"code": "CANTO-ABS-NE", "name": "Canto ABS Negro 22x0.8", "manufacturer": "ALVIC", "collection": "CANTOS", "color": "Negro", "colorCode": "C002", "finish": "ABS", "thickness": 0.8, "format": "22mm", "material": "ABS", "priceZ1": 0.85, "priceZ2": 0.90, "priceZ3": 0.95, "category": "CANTO"},
        {"code": "CANTO-LUXE-BL", "name": "Canto LUXE Blanco Brillo 22x1", "manufacturer": "ALVIC", "collection": "LUXE", "color": "Blanco", "colorCode": "C101", "finish": "Brillo", "thickness": 1.0, "format": "22mm", "material": "PVC", "priceZ1": 2.50, "priceZ2": 2.65, "priceZ3": 2.80, "category": "CANTO"},
    ]
    
    created = 0
    updated = 0
    
    for prod in sample_products:
        existing = await _get_db().despiece_products.find_one({"code": prod["code"]})
        prod["id"] = existing.get("id") if existing else f"desp-{uuid.uuid4().hex[:8]}"
        prod["createdAt"] = existing.get("createdAt") if existing else datetime.now(timezone.utc).isoformat()
        
        if existing:
            await _get_db().despiece_products.update_one({"code": prod["code"]}, {"$set": prod})
            updated += 1
        else:
            await _get_db().despiece_products.insert_one(prod)
            created += 1
    
    return {
        "message": "Productos ALVIC de muestra insertados",
        "created": created,
        "updated": updated,
        "total": len(sample_products)
    }


@router.get("/stats")
async def get_despiece_stats():
    """Obtener estadísticas del módulo despiece"""
    total_products = await _get_db().despiece_products.count_documents({})
    total_budgets = await _get_db().despiece_budgets.count_documents({})
    manufacturers = await _get_db().despiece_products.distinct("manufacturer")
    collections = await _get_db().despiece_products.distinct("collection")
    
    return {
        "totalProducts": total_products,
        "totalBudgets": total_budgets,
        "manufacturers": len(manufacturers),
        "collections": len(collections),
        "manufacturersList": manufacturers,
        "collectionsList": collections
    }


@router.post("/seed-syncron")
async def seed_syncron_products():
    """
    Poblar la base de datos con productos SYNCRON (puertas, costados, regletas)
    con matriz de precios Alto × Ancho
    """
    
    # Matriz de precios SYNCRON extraída de la tarifa
    # Estructura: {alto: {ancho: precio}}
    syncron_price_matrix = {
        # Alturas de 296 a 2196
        296: {156: 16.26, 196: 18.15, 246: 21.29, 296: 22.74, 346: 26.32, 396: 27.47, 446: 32.02, 496: 35.45, 596: 39.40, 696: 46.45, 796: 49.79, 896: 52.95, 996: 58.64, 1096: 64.85, 1196: 70.08},
        396: {156: 18.89, 196: 21.49, 246: 24.07, 296: 27.47, 346: 29.60, 396: 31.74, 446: 38.54, 496: 39.91, 596: 47.22, 696: 54.52, 796: 61.10, 896: 66.72, 996: 75.22, 1096: 82.76, 1196: 87.93},
        496: {156: 21.88, 196: 25.22, 246: 27.85, 296: 31.33, 346: 34.83, 396: 38.31, 446: 44.93, 496: 47.20, 596: 56.44, 696: 64.79, 796: 73.52, 896: 81.88, 996: 92.04, 1096: 101.76, 1196: 109.28},
        596: {156: 24.75, 196: 27.47, 246: 31.17, 296: 34.88, 346: 38.90, 396: 42.35, 446: 50.63, 496: 54.28, 596: 65.30, 696: 76.47, 796: 87.00, 896: 95.88, 996: 107.53, 1096: 118.43, 1196: 128.50},
        696: {156: 27.62, 196: 31.56, 246: 35.81, 296: 40.91, 346: 45.26, 396: 49.97, 446: 58.85, 496: 63.88, 596: 76.27, 696: 89.65, 796: 102.02, 896: 113.20, 996: 126.65, 1096: 140.98, 1196: 150.42},
        796: {156: 31.05, 196: 35.90, 246: 40.79, 296: 46.22, 346: 51.56, 396: 57.13, 446: 67.24, 496: 74.16, 596: 88.02, 696: 102.50, 796: 116.28, 896: 130.10, 996: 145.45, 1096: 160.81, 1196: 174.25},
        896: {156: 33.93, 196: 39.40, 246: 44.56, 296: 50.79, 346: 56.40, 396: 62.80, 446: 74.49, 496: 81.54, 596: 97.57, 696: 113.40, 796: 129.89, 896: 145.11, 996: 161.15, 1096: 178.08, 1196: 192.07},
        996: {156: 37.31, 196: 43.17, 246: 48.62, 296: 55.45, 346: 61.92, 396: 68.45, 446: 81.30, 496: 89.23, 596: 106.72, 696: 124.11, 796: 141.58, 896: 158.05, 996: 175.44, 1096: 193.54, 1196: 211.71},
        1096: {156: 40.26, 196: 46.94, 246: 53.30, 296: 60.78, 346: 67.62, 396: 74.50, 446: 88.64, 496: 97.64, 596: 116.48, 696: 135.04, 796: 153.58, 896: 172.05, 996: 191.30, 1096: 210.86, 1196: 229.51},
        1196: {156: 43.65, 196: 50.67, 246: 57.66, 296: 66.00, 346: 73.33, 396: 80.67, 446: 96.21, 496: 105.62, 596: 126.50, 696: 148.36, 796: 167.62, 896: 187.91, 996: 208.87, 1096: 230.51, 1196: 250.91},
        1296: {156: 47.11, 196: 55.19, 246: 63.15, 296: 72.29, 346: 80.23, 396: 88.33, 446: 104.63, 496: 114.87, 596: 138.05, 696: 161.30, 796: 183.60, 896: 205.40, 996: 228.20, 1096: 252.14, 1196: 275.15},
        1396: {156: 50.27, 196: 59.13, 246: 68.40, 296: 78.29, 346: 87.07, 396: 96.23, 446: 113.40, 496: 125.17, 596: 150.70, 696: 176.10, 796: 200.94, 896: 225.23, 996: 250.01, 1096: 275.53, 1196: 298.85},
        1496: {156: 53.60, 196: 62.78, 246: 72.76, 296: 83.64, 346: 93.09, 396: 103.14, 446: 122.50, 496: 133.90, 596: 161.40, 696: 189.39, 796: 216.60, 896: 243.40, 996: 270.43, 1096: 298.23, 1196: 324.78},
        1596: {156: 56.70, 196: 67.10, 246: 77.44, 296: 89.10, 346: 99.55, 396: 110.23, 446: 130.05, 496: 143.08, 596: 172.64, 696: 202.25, 796: 231.38, 896: 260.68, 996: 289.68, 1096: 319.98, 1196: 349.25},
        1696: {156: 60.08, 196: 70.90, 246: 82.16, 296: 94.56, 346: 105.87, 396: 117.35, 446: 138.67, 496: 152.66, 596: 184.22, 696: 215.23, 796: 247.06, 896: 277.85, 996: 309.36, 1096: 341.02, 1196: 371.43},
        1796: {156: 63.40, 196: 74.85, 246: 86.80, 296: 100.50, 346: 112.20, 396: 124.45, 446: 146.70, 496: 161.95, 596: 195.21, 696: 228.78, 796: 262.16, 896: 295.20, 996: 328.50, 1096: 362.48, 1196: 395.50},
        1896: {156: 66.35, 196: 78.40, 246: 91.45, 296: 105.78, 346: 118.62, 396: 131.60, 446: 155.20, 496: 171.10, 596: 206.90, 696: 242.31, 796: 278.15, 896: 313.45, 996: 349.05, 1096: 385.30, 1196: 420.25},
        1996: {156: 69.80, 196: 82.50, 246: 96.15, 296: 111.45, 346: 125.05, 396: 138.95, 446: 163.87, 496: 180.75, 596: 218.50, 696: 256.20, 796: 293.85, 896: 331.50, 996: 369.35, 1096: 407.55, 1196: 444.90},
        2096: {156: 73.10, 196: 86.30, 246: 100.85, 296: 116.70, 346: 131.40, 396: 146.15, 446: 172.60, 496: 190.25, 596: 230.10, 696: 269.70, 796: 309.55, 896: 349.45, 996: 389.50, 1096: 429.70, 1196: 469.50},
        2196: {156: 76.45, 196: 90.25, 246: 105.60, 296: 122.15, 346: 137.80, 396: 153.55, 446: 181.25, 496: 199.90, 596: 241.80, 696: 283.40, 796: 325.30, 896: 367.30, 996: 409.60, 1096: 451.85, 1196: 494.10}
    }
    
    # Categorías de productos SYNCRON
    categories_syncron = [
        {"prefix": "SYNC-PUERTA", "name": "PUERTA SYNCRON", "category": "PUERTA"},
        {"prefix": "SYNC-COSTADO", "name": "COSTADO SYNCRON", "category": "COSTADO"},
        {"prefix": "SYNC-REGLETA", "name": "REGLETA SYNCRON", "category": "REGLETA"}
    ]
    
    created = 0
    updated = 0
    
    for cat_info in categories_syncron:
        for alto, anchos in syncron_price_matrix.items():
            for ancho, precio in anchos.items():
                code = f"{cat_info['prefix']}-{alto}x{ancho}"
                
                product_data = {
                    "code": code,
                    "name": f"{cat_info['name']} {alto}×{ancho}mm",
                    "manufacturer": "ALVIC",
                    "collection": "SYNCRON",
                    "color": "Varios",
                    "colorCode": "SYNC",
                    "finish": "Textura Madera",
                    "thickness": 18,
                    "format": f"{alto}x{ancho}",
                    "material": "Melamina",
                    "width": ancho,
                    "height": alto,
                    "priceZ1": precio,
                    "priceZ2": round(precio * 1.05, 2),
                    "priceZ3": round(precio * 1.10, 2),
                    "pricePerM2": round(precio / ((alto/1000) * (ancho/1000)), 2) if alto > 0 and ancho > 0 else 0,
                    "available": True,
                    "leadTime": 5,
                    "minOrder": 1,
                    "imageUrl": "",
                    "category": cat_info['category']
                }
                
                existing = await _get_db().despiece_products.find_one({"code": code})
                product_data["id"] = existing.get("id") if existing else f"desp-{uuid.uuid4().hex[:8]}"
                product_data["createdAt"] = existing.get("createdAt") if existing else datetime.now(timezone.utc).isoformat()
                
                if existing:
                    await _get_db().despiece_products.update_one({"code": code}, {"$set": product_data})
                    updated += 1
                else:
                    await _get_db().despiece_products.insert_one(product_data)
                    created += 1
    
    return {
        "message": "Productos SYNCRON importados correctamente",
        "created": created,
        "updated": updated,
        "total": created + updated,
        "categories": ["PUERTA", "COSTADO", "REGLETA"],
        "heights": list(syncron_price_matrix.keys()),
        "widths": list(syncron_price_matrix[296].keys())
    }
