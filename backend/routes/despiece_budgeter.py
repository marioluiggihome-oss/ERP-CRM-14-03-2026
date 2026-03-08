"""
Router para el módulo DESPIECE - Presupuestador de tableros
Gestiona productos de fabricantes como ALVIC con parámetros específicos
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import os
import uuid

router = APIRouter(prefix="/api/despiece-budgeter", tags=["despiece-budgeter"])

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME')]

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
    search: Optional[str] = None,
    limit: int = Query(default=500, le=2000)
):
    """Obtener productos de despiece con filtros"""
    query = {}
    
    if manufacturer:
        query["manufacturer"] = {"$regex": manufacturer, "$options": "i"}
    if collection:
        query["collection"] = {"$regex": collection, "$options": "i"}
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
    if search:
        query["$or"] = [
            {"code": {"$regex": search, "$options": "i"}},
            {"name": {"$regex": search, "$options": "i"}},
            {"color": {"$regex": search, "$options": "i"}},
            {"colorCode": {"$regex": search, "$options": "i"}}
        ]
    
    products = await db.despiece_products.find(query, {"_id": 0}).limit(limit).to_list(limit)
    return products


@router.get("/products/filters")
async def get_despiece_filters():
    """Obtener opciones de filtros disponibles (fabricantes, colecciones, colores, etc.)"""
    # Obtener valores únicos de cada campo
    manufacturers = await db.despiece_products.distinct("manufacturer")
    collections = await db.despiece_products.distinct("collection")
    finishes = await db.despiece_products.distinct("finish")
    thicknesses = await db.despiece_products.distinct("thickness")
    colors = await db.despiece_products.distinct("color")
    categories = await db.despiece_products.distinct("category")
    
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
    product = await db.despiece_products.find_one({"id": product_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product


@router.post("/products")
async def create_despiece_product(product: DespieceProductCreate):
    """Crear un nuevo producto de despiece"""
    product_data = product.model_dump()
    product_data["id"] = f"desp-{uuid.uuid4().hex[:8]}"
    product_data["createdAt"] = datetime.now(timezone.utc).isoformat()
    
    await db.despiece_products.insert_one(product_data)
    del product_data["_id"] if "_id" in product_data else None
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
            existing = await db.despiece_products.find_one({"code": code})
            
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
                await db.despiece_products.update_one({"code": code}, {"$set": product_data})
                updated += 1
            else:
                await db.despiece_products.insert_one(product_data)
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
    result = await db.despiece_products.delete_one({"id": product_id})
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
    
    budgets = await db.despiece_budgets.find(query, {"_id": 0}).sort("createdAt", -1).limit(limit).to_list(limit)
    return budgets


@router.get("/budgets/{budget_id}")
async def get_despiece_budget(budget_id: str):
    """Obtener un presupuesto de despiece por ID"""
    budget = await db.despiece_budgets.find_one({"id": budget_id}, {"_id": 0})
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
    
    await db.despiece_budgets.insert_one(budget_data)
    del budget_data["_id"] if "_id" in budget_data else None
    return budget_data


@router.put("/budgets/{budget_id}")
async def update_despiece_budget(budget_id: str, budget: dict):
    """Actualizar un presupuesto de despiece"""
    existing = await db.despiece_budgets.find_one({"id": budget_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    
    update_data = {k: v for k, v in budget.items() if v is not None}
    update_data["updatedAt"] = datetime.now(timezone.utc).isoformat()
    
    await db.despiece_budgets.update_one({"id": budget_id}, {"$set": update_data})
    updated = await db.despiece_budgets.find_one({"id": budget_id}, {"_id": 0})
    return updated


@router.delete("/budgets/{budget_id}")
async def delete_despiece_budget(budget_id: str):
    """Eliminar un presupuesto de despiece"""
    result = await db.despiece_budgets.delete_one({"id": budget_id})
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
        existing = await db.despiece_products.find_one({"code": prod["code"]})
        prod["id"] = existing.get("id") if existing else f"desp-{uuid.uuid4().hex[:8]}"
        prod["createdAt"] = existing.get("createdAt") if existing else datetime.now(timezone.utc).isoformat()
        
        if existing:
            await db.despiece_products.update_one({"code": prod["code"]}, {"$set": prod})
            updated += 1
        else:
            await db.despiece_products.insert_one(prod)
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
    total_products = await db.despiece_products.count_documents({})
    total_budgets = await db.despiece_budgets.count_documents({})
    manufacturers = await db.despiece_products.distinct("manufacturer")
    collections = await db.despiece_products.distinct("collection")
    
    return {
        "totalProducts": total_products,
        "totalBudgets": total_budgets,
        "manufacturers": len(manufacturers),
        "collections": len(collections),
        "manufacturersList": manufacturers,
        "collectionsList": collections
    }
