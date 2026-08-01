"""
Router para gestión de Bibliotecas (Multi-Library System)
Permite administrar bibliotecas de productos (ZC, MV, etc.) y acceso de usuarios
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import os
import uuid

router = APIRouter(prefix="/libraries", tags=["libraries"])

try:
    from services.jwt_service import require_auth
except Exception:  # pragma: no cover
    async def require_auth():
        raise HTTPException(status_code=503, detail="Auth service unavailable")

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL')
client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=5000, connectTimeoutMS=10000, maxPoolSize=5)
db = client[os.environ.get('DB_NAME')]


# ============================================
# MODELOS
# ============================================

class Library(BaseModel):
    """Modelo de biblioteca de productos"""
    id: str = Field(default_factory=lambda: f"lib-{uuid.uuid4().hex[:8]}")
    code: str  # ZC, MV, etc.
    name: str  # Zona Cocinas, Muebles Valencia, etc.
    description: str = ""
    currency: str = "points"  # points, EUR, etc.
    pointValue: float = 1.0  # Valor de 1 punto en EUR
    isActive: bool = True
    productCount: int = 0
    # Sistema de precios: ZC usa "zonas" (Z1-Z12), MV usa "tarifas" (T1-T21)
    pricingSystem: str = "zones"  # "zones" para ZC, "tariffs" para MV
    priceLevels: List[str] = ["Z1", "Z2", "Z3", "Z4", "Z5", "Z6", "Z7", "Z8", "Z9", "Z10", "Z11", "Z12"]
    createdAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class LibraryCreate(BaseModel):
    code: str
    name: str
    description: str = ""
    currency: str = "points"
    pointValue: float = 1.0
    pricingSystem: str = "zones"  # "zones" o "tariffs"
    priceLevels: List[str] = ["Z1", "Z2", "Z3", "Z4", "Z5", "Z6", "Z7", "Z8", "Z9", "Z10", "Z11", "Z12"]


class LibraryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    currency: Optional[str] = None
    pointValue: Optional[float] = None
    isActive: Optional[bool] = None
    pricingSystem: Optional[str] = None
    priceLevels: Optional[List[str]] = None


class UserLibraryAccess(BaseModel):
    """Acceso de usuario a bibliotecas"""
    userId: str
    libraries: List[str]  # Lista de códigos de biblioteca: ["ZC", "MV"]


# ============================================
# ENDPOINTS DE BIBLIOTECAS
# ============================================

@router.get("")
async def get_libraries():
    """Obtener todas las bibliotecas disponibles"""
    libraries = await db.libraries.find({}, {"_id": 0}).to_list(100)
    
    # Si no hay bibliotecas, crear las predeterminadas
    if not libraries:
        # ZC: Sistema de ZONAS (Z1-Z12)
        zc_zones = ["Z1", "Z2", "Z3", "Z4", "Z5", "Z6", "Z7", "Z8", "Z9", "Z10", "Z11", "Z12"]
        
        # MV: Sistema de TARIFAS (T1-T21)
        mv_tariffs = [f"T{i}" for i in range(1, 22)]  # T1, T2, ..., T21
        
        default_libraries = [
            {
                "id": "lib-zc",
                "code": "ZC",
                "name": "ZC",
                "description": "Catálogo de muebles de cocina ZC - Sistema de ZONAS",
                "currency": "points",
                "pointValue": 1.0,
                "isActive": True,
                "productCount": await db.products.count_documents({"library": "ZC"}),
                "pricingSystem": "zones",
                "priceLevels": zc_zones,
                "createdAt": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": "lib-mv",
                "code": "MV",
                "name": "MV",
                "description": "Catálogo MV - Sistema de TARIFAS (T1-T21)",
                "currency": "points",
                "pointValue": 3.33,
                "isActive": False,
                "productCount": 0,
                "pricingSystem": "tariffs",
                "priceLevels": mv_tariffs,
                "createdAt": datetime.now(timezone.utc).isoformat()
            }
        ]
        await db.libraries.insert_many(default_libraries)
        libraries = default_libraries

    # Asegurar que la biblioteca ALV existe (se añade sin muebles, a la espera
    # de su catálogo).
    if not any(lib.get("code") == "ALV" for lib in libraries):
        alv = {
            "id": "lib-alv",
            "code": "ALV",
            "name": "ALV",
            "description": "Catálogo ALV",
            "currency": "points",
            "pointValue": 1.0,
            "isActive": True,
            "productCount": 0,
            "pricingSystem": "zones",
            "priceLevels": ["Z1", "Z2", "Z3", "Z4", "Z5", "Z6", "Z7", "Z8", "Z9", "Z10", "Z11", "Z12"],
            "createdAt": datetime.now(timezone.utc).isoformat()
        }
        await db.libraries.insert_one(alv)
        libraries.append(alv)

    # Normalizar nombres antiguos ("Zona Cocinas" / "Muebles Valencia") a "ZC" / "MV"
    rename_map = {"Zona Cocinas": "ZC", "Muebles Valencia": "MV"}
    for lib in libraries:
        new_name = rename_map.get(lib.get("name"))
        if new_name:
            lib["name"] = new_name
            await db.libraries.update_one({"code": lib.get("code")}, {"$set": {"name": new_name}})

    # Actualizar conteo de productos para cada biblioteca
    for lib in libraries:
        lib["productCount"] = await db.products.count_documents({"library": lib.get("code", "")})
    
    return libraries


@router.get("/{library_code}")
async def get_library(library_code: str):
    """Obtener una biblioteca por código"""
    library = await db.libraries.find_one({"code": library_code.upper()}, {"_id": 0})
    if not library:
        raise HTTPException(status_code=404, detail=f"Biblioteca '{library_code}' no encontrada")
    
    # Actualizar conteo de productos
    library["productCount"] = await db.products.count_documents({"library": library_code.upper()})
    
    return library


@router.post("")
async def create_library(library: LibraryCreate):
    """Crear una nueva biblioteca"""
    # Verificar que no existe
    existing = await db.libraries.find_one({"code": library.code.upper()})
    if existing:
        raise HTTPException(status_code=400, detail=f"Ya existe una biblioteca con código '{library.code}'")
    
    library_data = {
        "id": f"lib-{library.code.lower()}",
        "code": library.code.upper(),
        "name": library.name,
        "description": library.description,
        "currency": library.currency,
        "pointValue": library.pointValue,
        "isActive": True,
        "productCount": 0,
        "zones": library.zones,
        "createdAt": datetime.now(timezone.utc).isoformat()
    }
    
    await db.libraries.insert_one(library_data)
    library_data.pop("_id", None)
    return library_data


@router.put("/{library_code}")
async def update_library(library_code: str, update: LibraryUpdate):
    """Actualizar una biblioteca"""
    existing = await db.libraries.find_one({"code": library_code.upper()})
    if not existing:
        raise HTTPException(status_code=404, detail=f"Biblioteca '{library_code}' no encontrada")
    
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if update_data:
        await db.libraries.update_one({"code": library_code.upper()}, {"$set": update_data})
    
    return await db.libraries.find_one({"code": library_code.upper()}, {"_id": 0})


@router.delete("/{library_code}")
async def delete_library(library_code: str):
    """Eliminar una biblioteca (solo si no tiene productos)"""
    # No permitir eliminar ZC (biblioteca principal)
    if library_code.upper() == "ZC":
        raise HTTPException(status_code=400, detail="No se puede eliminar la biblioteca principal ZC")
    
    # Verificar si tiene productos
    product_count = await db.products.count_documents({"library": library_code.upper()})
    if product_count > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"No se puede eliminar: la biblioteca tiene {product_count} productos"
        )
    
    result = await db.libraries.delete_one({"code": library_code.upper()})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"Biblioteca '{library_code}' no encontrada")
    
    return {"message": f"Biblioteca '{library_code}' eliminada"}


# ============================================
# GESTIÓN DE ACCESO DE USUARIOS
# ============================================

@router.get("/users/{user_id}/access")
async def get_user_library_access(user_id: str):
    """Obtener las bibliotecas a las que tiene acceso un usuario"""
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    allowed_libraries = user.get("allowedLibraries", ["ZC"])
    
    # Obtener detalles de cada biblioteca
    libraries = []
    for lib_code in allowed_libraries:
        lib = await db.libraries.find_one({"code": lib_code}, {"_id": 0})
        if lib:
            lib["productCount"] = await db.products.count_documents({"library": lib_code})
            libraries.append(lib)
    
    return {
        "userId": user_id,
        "username": user.get("username"),
        "allowedLibraries": allowed_libraries,
        "libraries": libraries
    }


@router.put("/users/{user_id}/access")
async def update_user_library_access(user_id: str, access: UserLibraryAccess):
    """Actualizar las bibliotecas a las que tiene acceso un usuario"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Validar que todas las bibliotecas existen
    for lib_code in access.libraries:
        lib = await db.libraries.find_one({"code": lib_code.upper()})
        if not lib:
            raise HTTPException(status_code=400, detail=f"Biblioteca '{lib_code}' no existe")
    
    # Actualizar usuario
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"allowedLibraries": [l.upper() for l in access.libraries]}}
    )
    
    return {
        "message": "Acceso actualizado",
        "userId": user_id,
        "allowedLibraries": access.libraries
    }


@router.post("/users/bulk-access")
async def bulk_update_library_access(updates: List[UserLibraryAccess]):
    """Actualizar acceso a bibliotecas para múltiples usuarios"""
    results = []
    for update in updates:
        try:
            user = await db.users.find_one({"id": update.userId})
            if user:
                await db.users.update_one(
                    {"id": update.userId},
                    {"$set": {"allowedLibraries": [l.upper() for l in update.libraries]}}
                )
                results.append({"userId": update.userId, "status": "updated"})
            else:
                results.append({"userId": update.userId, "status": "not_found"})
        except Exception as e:
            results.append({"userId": update.userId, "status": "error", "error": str(e)})
    
    return {"results": results}


# ============================================
# PRODUCTOS POR BIBLIOTECA
# ============================================

@router.get("/{library_code}/products")
async def get_library_products(
    library_code: str,
    module: Optional[str] = None,
    category: Optional[str] = None,
    programa: Optional[str] = None,
    series: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(default=500, le=5000),
    skip: int = Query(default=0, ge=0)
):
    """Obtener productos de una biblioteca específica"""
    query = {"library": library_code.upper()}
    
    if module:
        query["module"] = module
    if category:
        query["category"] = {"$regex": category, "$options": "i"}
    if programa:
        query["programa"] = {"$regex": programa, "$options": "i"}
    if series:
        query["series"] = {"$regex": series, "$options": "i"}
    if search:
        query["$or"] = [
            {"code": {"$regex": search, "$options": "i"}},
            {"name": {"$regex": search, "$options": "i"}}
        ]
    
    total = await db.products.count_documents(query)
    products = await db.products.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    
    return {
        "library": library_code.upper(),
        "total": total,
        "skip": skip,
        "limit": limit,
        "products": products
    }


@router.post("/{library_code}/import-tariffs")
async def import_tariffs(library_code: str, dry_run: bool = True, wipe: bool = False,
                         current_user: dict = Depends(require_auth)):
    """Carga las tarifas oficiales (data/mv_tarifas_oficiales.json) en los productos MV.

    - dry_run=true (por defecto): solo SIMULA y devuelve el informe (no escribe nada).
    - dry_run=false: aplica. Con wipe=true borra antes los productos MV y reconstruye
      (recomendado para eliminar duplicados fantasma). Solo administradores.
    """
    if not (current_user or {}).get("isAdmin"):
        raise HTTPException(status_code=403, detail="Solo administradores")
    if library_code.upper() != "MV":
        raise HTTPException(status_code=400, detail="Solo disponible para la biblioteca MV")

    from services.mv_tariff_importer import load_data, expand_tariffs, build_report
    try:
        data = load_data()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"No se pudo leer el JSON de tarifas: {e}")

    products = expand_tariffs(data)
    report = build_report(products)

    if dry_run:
        report["dry_run"] = True
        report["mensaje"] = "Simulación: no se ha escrito nada. Usa dry_run=false para aplicar."
        return report

    now = datetime.now(timezone.utc).isoformat()
    if wipe:
        await db.products.delete_many({"library": "MV"})
    inserted, updated = 0, 0
    for p in products:
        p["updatedAt"] = now
        res = await db.products.update_one(
            {"library": "MV", "code": p["code"]}, {"$set": p}, upsert=True
        )
        if res.upserted_id:
            inserted += 1
        else:
            updated += 1
    report.update({"dry_run": False, "wipe": wipe, "insertados": inserted, "actualizados": updated})
    return report


@router.get("/{library_code}/stats")
async def get_library_stats(library_code: str):
    """Obtener estadísticas de una biblioteca"""
    query = {"library": library_code.upper()}
    
    total = await db.products.count_documents(query)
    categories = await db.products.distinct("category", query)
    programas = await db.products.distinct("programa", query)
    series = await db.products.distinct("series", query)
    
    return {
        "library": library_code.upper(),
        "totalProducts": total,
        "categories": sorted([c for c in categories if c]),
        "programas": sorted([p for p in programas if p]),
        "seriesCount": len([s for s in series if s])
    }


# ============================================
# IMPORTACIÓN DE PRODUCTOS A BIBLIOTECA
# ============================================

@router.post("/{library_code}/import")
async def import_products_to_library(library_code: str, products: List[Dict]):
    """Importar productos a una biblioteca específica"""
    created = 0
    updated = 0
    errors = []
    
    for idx, prod in enumerate(products):
        try:
            code = prod.get("code", "").upper().strip()
            if not code:
                errors.append(f"Producto {idx}: código vacío")
                continue
            
            # Añadir biblioteca al producto
            prod["library"] = library_code.upper()
            
            # Verificar si ya existe en esta biblioteca
            existing = await db.products.find_one({
                "code": code,
                "library": library_code.upper()
            })
            
            if existing:
                # Actualizar
                await db.products.update_one(
                    {"code": code, "library": library_code.upper()},
                    {"$set": prod}
                )
                updated += 1
            else:
                # Crear nuevo
                prod["id"] = f"prod-{uuid.uuid4().hex[:8]}"
                prod["createdAt"] = datetime.now(timezone.utc).isoformat()
                await db.products.insert_one(prod)
                created += 1
                
        except Exception as e:
            errors.append(f"Producto {idx} ({prod.get('code', '?')}): {str(e)}")
    
    # Actualizar conteo en biblioteca
    await db.libraries.update_one(
        {"code": library_code.upper()},
        {"$set": {"productCount": await db.products.count_documents({"library": library_code.upper()})}}
    )
    
    return {
        "library": library_code.upper(),
        "created": created,
        "updated": updated,
        "errors": errors[:20],  # Limitar errores mostrados
        "total": len(products)
    }
