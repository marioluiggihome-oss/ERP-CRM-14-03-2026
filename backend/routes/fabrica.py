"""
Portal de Fábrica - LUIGGI HOME
Sistema de órdenes de fabricación, importación de PDFs y gestión de producción
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime, timezone
import uuid
import logging
import base64
import os

# MongoDB
from motor.motor_asyncio import AsyncIOMotorClient
mongo_url = os.environ.get('MONGO_URL')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'luiggi_home')]

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/fabrica", tags=["Portal Fábrica"])


# ============================================
# MODELOS DE ÓRDENES DE FABRICACIÓN
# ============================================

class ManufacturingOrderItem(BaseModel):
    """Un mueble individual en la orden de fabricación"""
    id: str = Field(default_factory=lambda: f"moi-{uuid.uuid4().hex[:8]}")
    productCode: str
    productName: str
    quantity: int = 1
    width: float = 0  # cm
    height: float = 0  # cm
    depth: float = 0  # cm
    material: str = ""
    doorFinish: str = ""
    notes: str = ""
    # Despiece calculado
    despiece: List[Dict] = []
    # Estado del ítem
    status: str = "pending"  # pending, in_progress, cutting, assembling, finished


class ManufacturingOrder(BaseModel):
    """Orden de fabricación completa"""
    id: str = Field(default_factory=lambda: f"mfg-{uuid.uuid4().hex[:8]}")
    orderNumber: str = ""  # OF-2026-001
    # Información del origen
    sourceType: str = "manual"  # manual, pdf_import, budget_import
    sourceBudgetId: Optional[str] = None
    sourceFileName: Optional[str] = None
    # Cliente
    customerName: str = ""
    customerCode: str = ""
    contactPhone: str = ""
    deliveryAddress: str = ""
    # Fechas
    createdAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updatedAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    requestedDeliveryDate: Optional[str] = None
    estimatedDeliveryDate: Optional[str] = None
    actualDeliveryDate: Optional[str] = None
    # Estado
    status: str = "draft"  # draft, confirmed, in_production, ready, delivered, cancelled
    priority: str = "normal"  # low, normal, high, urgent
    # Ítems
    items: List[ManufacturingOrderItem] = []
    # Resumen
    totalPieces: int = 0
    totalArea: float = 0
    # Asignación
    assignedToUserId: Optional[str] = None
    assignedToName: Optional[str] = None
    # Notas
    internalNotes: str = ""
    productionNotes: str = ""
    deliveryNotes: str = ""
    # Metadata
    createdByUserId: str = ""
    createdByName: str = ""


class ManufacturingOrderCreate(BaseModel):
    customerName: str = ""
    customerCode: str = ""
    contactPhone: str = ""
    deliveryAddress: str = ""
    requestedDeliveryDate: Optional[str] = None
    priority: str = "normal"
    items: List[Dict] = []
    internalNotes: str = ""
    productionNotes: str = ""


class ManufacturingOrderUpdate(BaseModel):
    customerName: Optional[str] = None
    customerCode: Optional[str] = None
    contactPhone: Optional[str] = None
    deliveryAddress: Optional[str] = None
    requestedDeliveryDate: Optional[str] = None
    estimatedDeliveryDate: Optional[str] = None
    actualDeliveryDate: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    items: Optional[List[Dict]] = None
    assignedToUserId: Optional[str] = None
    assignedToName: Optional[str] = None
    internalNotes: Optional[str] = None
    productionNotes: Optional[str] = None
    deliveryNotes: Optional[str] = None


class PDFImportRequest(BaseModel):
    """Petición para importar PDF de presupuesto"""
    pdfBase64: str
    fileName: str = "presupuesto.pdf"


class PDFImportResult(BaseModel):
    """Resultado de importación de PDF"""
    success: bool
    message: str
    detectedItems: List[Dict] = []
    rawText: str = ""
    orderId: Optional[str] = None


# ============================================
# ENDPOINTS DE ÓRDENES DE FABRICACIÓN
# ============================================

@router.post("/orders", response_model=Dict)
async def create_manufacturing_order(order: ManufacturingOrderCreate, userId: str = "", userName: str = ""):
    """Crear nueva orden de fabricación"""
    try:
        # Generar número de orden
        current_year = datetime.now().year
        counter_id = f"manufacturing_order_{current_year}"
        
        result = await db.counters.find_one_and_update(
            {"_id": counter_id},
            {"$inc": {"seq": 1}},
            upsert=True,
            return_document=True
        )
        seq_number = result["seq"]
        order_number = f"OF-{current_year}-{seq_number:04d}"
        
        # Calcular totales
        total_pieces = 0
        total_area = 0
        items_with_ids = []
        
        for item in order.items:
            item_id = f"moi-{uuid.uuid4().hex[:8]}"
            items_with_ids.append({
                "id": item_id,
                **item,
                "status": "pending"
            })
            qty = item.get("quantity", 1)
            w = item.get("width", 0)
            h = item.get("height", 0)
            total_pieces += qty
            total_area += (w * h * qty) / 10000  # m²
        
        # Crear documento
        order_doc = {
            "id": f"mfg-{uuid.uuid4().hex[:8]}",
            "orderNumber": order_number,
            "sourceType": "manual",
            "customerName": order.customerName,
            "customerCode": order.customerCode,
            "contactPhone": order.contactPhone,
            "deliveryAddress": order.deliveryAddress,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat(),
            "requestedDeliveryDate": order.requestedDeliveryDate,
            "estimatedDeliveryDate": None,
            "actualDeliveryDate": None,
            "status": "draft",
            "priority": order.priority,
            "items": items_with_ids,
            "totalPieces": total_pieces,
            "totalArea": round(total_area, 3),
            "assignedToUserId": None,
            "assignedToName": None,
            "internalNotes": order.internalNotes,
            "productionNotes": order.productionNotes,
            "deliveryNotes": "",
            "createdByUserId": userId,
            "createdByName": userName
        }
        
        await db.manufacturing_orders.insert_one(order_doc)
        
        # Excluir _id de la respuesta
        order_doc.pop("_id", None)
        
        return {
            "success": True,
            "message": f"Orden {order_number} creada correctamente",
            "order": order_doc
        }
    except Exception as e:
        logger.error(f"Create manufacturing order error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders")
async def get_manufacturing_orders(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    skip: int = 0
):
    """Listar órdenes de fabricación"""
    try:
        query = {}
        
        if status:
            query["status"] = status
        if priority:
            query["priority"] = priority
        if search:
            query["$or"] = [
                {"orderNumber": {"$regex": search, "$options": "i"}},
                {"customerName": {"$regex": search, "$options": "i"}},
                {"customerCode": {"$regex": search, "$options": "i"}}
            ]
        
        cursor = db.manufacturing_orders.find(query, {"_id": 0}).sort("createdAt", -1).skip(skip).limit(limit)
        orders = await cursor.to_list(length=limit)
        
        total = await db.manufacturing_orders.count_documents(query)
        
        return {
            "orders": orders,
            "total": total,
            "limit": limit,
            "skip": skip
        }
    except Exception as e:
        logger.error(f"Get manufacturing orders error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders/{order_id}")
async def get_manufacturing_order(order_id: str):
    """Obtener una orden de fabricación específica"""
    try:
        order = await db.manufacturing_orders.find_one({"id": order_id}, {"_id": 0})
        if not order:
            raise HTTPException(status_code=404, detail="Orden no encontrada")
        return order
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get manufacturing order error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/orders/{order_id}")
async def update_manufacturing_order(order_id: str, update: ManufacturingOrderUpdate):
    """Actualizar orden de fabricación"""
    try:
        update_data = {k: v for k, v in update.model_dump().items() if v is not None}
        update_data["updatedAt"] = datetime.now(timezone.utc).isoformat()
        
        # Recalcular totales si se actualizan items
        if "items" in update_data:
            total_pieces = 0
            total_area = 0
            for item in update_data["items"]:
                qty = item.get("quantity", 1)
                w = item.get("width", 0)
                h = item.get("height", 0)
                total_pieces += qty
                total_area += (w * h * qty) / 10000
            update_data["totalPieces"] = total_pieces
            update_data["totalArea"] = round(total_area, 3)
        
        result = await db.manufacturing_orders.update_one(
            {"id": order_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Orden no encontrada")
        
        updated = await db.manufacturing_orders.find_one({"id": order_id}, {"_id": 0})
        return {
            "success": True,
            "message": "Orden actualizada",
            "order": updated
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update manufacturing order error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/orders/{order_id}")
async def delete_manufacturing_order(order_id: str):
    """Eliminar orden de fabricación"""
    try:
        result = await db.manufacturing_orders.delete_one({"id": order_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Orden no encontrada")
        return {"success": True, "message": "Orden eliminada"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete manufacturing order error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/orders/{order_id}/status")
async def update_order_status(order_id: str, status: str, notes: str = ""):
    """Actualizar estado de una orden"""
    valid_statuses = ["draft", "confirmed", "in_production", "ready", "delivered", "cancelled"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Estado inválido. Válidos: {valid_statuses}")
    
    try:
        update_data = {
            "status": status,
            "updatedAt": datetime.now(timezone.utc).isoformat()
        }
        
        # Si se marca como entregado, registrar fecha
        if status == "delivered":
            update_data["actualDeliveryDate"] = datetime.now(timezone.utc).isoformat()
        
        if notes:
            update_data["productionNotes"] = notes
        
        result = await db.manufacturing_orders.update_one(
            {"id": order_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Orden no encontrada")
        
        return {"success": True, "message": f"Estado actualizado a: {status}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update order status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/orders/{order_id}/delivery-date")
async def set_delivery_date(order_id: str, estimated_date: str, notes: str = ""):
    """Establecer fecha estimada de entrega"""
    try:
        update_data = {
            "estimatedDeliveryDate": estimated_date,
            "updatedAt": datetime.now(timezone.utc).isoformat()
        }
        
        if notes:
            update_data["deliveryNotes"] = notes
        
        result = await db.manufacturing_orders.update_one(
            {"id": order_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Orden no encontrada")
        
        return {"success": True, "message": f"Fecha de entrega establecida: {estimated_date}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Set delivery date error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# IMPORTACIÓN DE PDF
# ============================================

@router.post("/import-pdf", response_model=PDFImportResult)
async def import_budget_pdf(request: PDFImportRequest):
    """
    Importar PDF de presupuesto y detectar muebles automáticamente.
    Utiliza OCR/AI para extraer la información del presupuesto.
    """
    try:
        # Decodificar PDF
        try:
            pdf_bytes = base64.b64decode(request.pdfBase64)
        except Exception:
            raise HTTPException(status_code=400, detail="PDF base64 inválido")
        
        # Por ahora, retornamos una respuesta de placeholder
        # En la implementación completa, usaríamos Gemini Vision para analizar el PDF
        return PDFImportResult(
            success=True,
            message="PDF recibido. La importación automática con IA estará disponible próximamente.",
            detectedItems=[],
            rawText="",
            orderId=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Import PDF error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import-from-budget/{budget_id}")
async def import_from_budget(budget_id: str, userId: str = "", userName: str = ""):
    """Importar orden de fabricación desde un presupuesto existente"""
    try:
        # Buscar presupuesto
        project = await db.projects.find_one({"id": budget_id}, {"_id": 0})
        if not project:
            raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
        
        # Extraer items del presupuesto
        items_montada = project.get("itemsMontada", [])
        
        if not items_montada:
            raise HTTPException(status_code=400, detail="El presupuesto no tiene muebles montada")
        
        # Convertir items a formato de orden de fabricación
        order_items = []
        for item in items_montada:
            order_items.append({
                "productCode": item.get("productCode", item.get("customReference", "")),
                "productName": item.get("productName", item.get("name", "")),
                "quantity": item.get("quantity", 1),
                "width": item.get("customWidth", item.get("width", 0)),
                "height": item.get("customHeight", item.get("height", 0)),
                "depth": item.get("customDepth", item.get("depth", 0)),
                "material": "",
                "doorFinish": "",
                "notes": ""
            })
        
        # Crear la orden
        order_create = ManufacturingOrderCreate(
            customerName=project.get("customerName", ""),
            customerCode=project.get("clientCode", ""),
            items=order_items,
            internalNotes=f"Importado desde presupuesto: {project.get('budgetNumber', budget_id)}"
        )
        
        result = await create_manufacturing_order(order_create, userId, userName)
        
        # Marcar origen
        await db.manufacturing_orders.update_one(
            {"id": result["order"]["id"]},
            {"$set": {
                "sourceType": "budget_import",
                "sourceBudgetId": budget_id
            }}
        )
        
        result["order"]["sourceType"] = "budget_import"
        result["order"]["sourceBudgetId"] = budget_id
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Import from budget error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# ESTADÍSTICAS Y DASHBOARD
# ============================================

@router.get("/dashboard/stats")
async def get_factory_dashboard_stats():
    """Obtener estadísticas para el dashboard de fábrica"""
    try:
        # Contar por estado
        pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]
        status_counts = {}
        async for doc in db.manufacturing_orders.aggregate(pipeline):
            status_counts[doc["_id"]] = doc["count"]
        
        # Contar por prioridad
        pipeline_priority = [
            {"$match": {"status": {"$nin": ["delivered", "cancelled"]}}},
            {"$group": {"_id": "$priority", "count": {"$sum": 1}}}
        ]
        priority_counts = {}
        async for doc in db.manufacturing_orders.aggregate(pipeline_priority):
            priority_counts[doc["_id"]] = doc["count"]
        
        # Órdenes pendientes de entrega esta semana
        from datetime import timedelta
        today = datetime.now(timezone.utc)
        week_end = today + timedelta(days=7)
        
        pending_this_week = await db.manufacturing_orders.count_documents({
            "status": {"$in": ["confirmed", "in_production", "ready"]},
            "estimatedDeliveryDate": {
                "$gte": today.isoformat(),
                "$lte": week_end.isoformat()
            }
        })
        
        # Total de piezas en producción
        pipeline_pieces = [
            {"$match": {"status": "in_production"}},
            {"$group": {"_id": None, "total": {"$sum": "$totalPieces"}}}
        ]
        pieces_in_production = 0
        async for doc in db.manufacturing_orders.aggregate(pipeline_pieces):
            pieces_in_production = doc["total"]
        
        return {
            "byStatus": status_counts,
            "byPriority": priority_counts,
            "pendingThisWeek": pending_this_week,
            "piecesInProduction": pieces_in_production,
            "totalActive": sum(status_counts.get(s, 0) for s in ["draft", "confirmed", "in_production", "ready"])
        }
    except Exception as e:
        logger.error(f"Get factory stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders/{order_id}/despiece")
async def get_order_despiece(order_id: str):
    """Obtener el despiece completo de una orden para fabricación"""
    try:
        order = await db.manufacturing_orders.find_one({"id": order_id}, {"_id": 0})
        if not order:
            raise HTTPException(status_code=404, detail="Orden no encontrada")
        
        # Calcular despiece para cada ítem
        from server import calculate_furniture_despiece, DespieceItemInput
        
        despiece_items = []
        for item in order.get("items", []):
            despiece_input = DespieceItemInput(
                productId=item.get("id", ""),
                productCode=item.get("productCode", ""),
                productName=item.get("productName", ""),
                width=item.get("width", 60),
                height=item.get("height", 70),
                depth=item.get("depth", 58),
                quantity=item.get("quantity", 1),
                category=item.get("productName", "").upper()
            )
            
            carcass_material = item.get("material", "MELAMINA BLANCA")
            back_material = "Tablero 8mm"
            
            furniture_despiece = calculate_furniture_despiece(
                despiece_input,
                carcass_material,
                back_material,
                18  # grosor 18mm
            )
            
            despiece_items.append({
                "productId": item.get("id"),
                "productCode": item.get("productCode"),
                "productName": item.get("productName"),
                "quantity": item.get("quantity", 1),
                "dimensions": f"{item.get('width', 0)}×{item.get('height', 0)}×{item.get('depth', 0)} cm",
                "components": [
                    {
                        "name": c.name,
                        "material": c.material,
                        "length": c.length,
                        "width": c.width,
                        "thickness": c.thickness,
                        "quantity": c.quantity,
                        "notes": c.notes
                    }
                    for c in furniture_despiece.components
                ],
                "totalPanels": furniture_despiece.totalPanels,
                "totalArea": furniture_despiece.totalArea
            })
        
        # Calcular resumen
        total_panels = sum(d["totalPanels"] * d["quantity"] for d in despiece_items)
        total_area = sum(d["totalArea"] for d in despiece_items)
        
        return {
            "orderId": order_id,
            "orderNumber": order.get("orderNumber"),
            "customerName": order.get("customerName"),
            "items": despiece_items,
            "summary": {
                "totalFurniture": len(order.get("items", [])),
                "totalPanels": total_panels,
                "totalArea": round(total_area, 3)
            },
            "generatedAt": datetime.now(timezone.utc).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get order despiece error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
