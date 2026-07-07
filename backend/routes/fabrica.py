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
import json
import asyncio

# MongoDB
from motor.motor_asyncio import AsyncIOMotorClient
mongo_url = os.environ.get('MONGO_URL')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'luiggi_home')]

# Gemini Vision para análisis de PDF
try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

logger = logging.getLogger(__name__)

# Seguridad: el modulo no exigia ningun token; datos de produccion/ordenes de
# fabricacion quedaban abiertos a cualquiera que conociera la URL.
try:
    from services.jwt_service import require_module_access
    _FABRICA_DEPS = [Depends(require_module_access("canAccessFabrica"))]
except Exception:  # pragma: no cover - fallback si no hay jwt_service
    _FABRICA_DEPS = []

router = APIRouter(prefix="/fabrica", tags=["Portal Fábrica"], dependencies=_FABRICA_DEPS)

# Emergent LLM Key para Gemini
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')


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
    manufacturingNumber: Optional[int] = None  # Número secuencial de fabricación
    # Información del origen
    sourceType: str = "manual"  # manual, pdf_import, budget_import, order_confirmation
    sourceBudgetId: Optional[str] = None
    sourceOrderId: Optional[str] = None
    sourceFileName: Optional[str] = None
    # Asignación de Fábrica
    factoryType: str = "internal"  # internal (propia) o external (subcontratada)
    factoryId: Optional[str] = None  # ID de la fábrica asignada
    factoryName: Optional[str] = None  # Nombre de la fábrica
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
    # Asignación de fábrica
    factoryType: str = "internal"  # internal o external
    factoryId: Optional[str] = None
    factoryName: Optional[str] = None


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
    # Asignación de fábrica
    factoryType: Optional[str] = None
    factoryId: Optional[str] = None
    factoryName: Optional[str] = None


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
        # Generar número de orden (formato: OF-2026-0001)
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
        
        # Generar número de fabricación secuencial global (más corto, para uso interno)
        mfg_counter = await db.counters.find_one_and_update(
            {"_id": "manufacturing_number_global"},
            {"$inc": {"seq": 1}},
            upsert=True,
            return_document=True
        )
        manufacturing_number = mfg_counter["seq"]
        
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
            "manufacturingNumber": manufacturing_number,  # Número de fabricación secuencial
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
            "createdByName": userName,
            # Asignación de fábrica
            "factoryType": order.factoryType or "internal",
            "factoryId": order.factoryId,
            "factoryName": order.factoryName
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


# Fases de la hoja de ruta de taller (en orden de proceso)
PRODUCTION_PHASES = ["corte", "cantear", "montar", "herraje", "qc", "embalaje"]


@router.patch("/orders/{order_id}/phase")
async def update_order_phase(order_id: str, phase: str, done: bool = True):
    """Marcar/desmarcar una FASE de la hoja de ruta de taller de una orden.

    Fases: corte → cantear → montar → herraje → qc → embalaje.
    Guarda en productionPhases.{fase} = ISO timestamp (hecha) o None (pendiente).
    """
    phase = (phase or "").lower().strip()
    if phase not in PRODUCTION_PHASES:
        raise HTTPException(status_code=400, detail=f"Fase inválida. Válidas: {PRODUCTION_PHASES}")
    try:
        order = await db.manufacturing_orders.find_one({"id": order_id}, {"_id": 0, "productionPhases": 1})
        if not order:
            raise HTTPException(status_code=404, detail="Orden no encontrada")
        phases = order.get("productionPhases") or {}
        phases[phase] = datetime.now(timezone.utc).isoformat() if done else None
        await db.manufacturing_orders.update_one(
            {"id": order_id},
            {"$set": {"productionPhases": phases, "updatedAt": datetime.now(timezone.utc).isoformat()}}
        )
        completed = [p for p in PRODUCTION_PHASES if phases.get(p)]
        return {"success": True, "productionPhases": phases,
                "progress": round(len(completed) / len(PRODUCTION_PHASES) * 100)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update order phase error: {e}")
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
# IMPORTACIÓN DE PDF CON IA
# ============================================

async def analyze_pdf_with_gemini(pdf_bytes: bytes, filename: str) -> Dict:
    """
    Analizar PDF de presupuesto con Gemini Vision para detectar muebles.
    """
    if not GEMINI_AVAILABLE:
        return {
            "success": False,
            "message": "Gemini Vision no disponible. Instale google-genai.",
            "items": []
        }
    
    try:
        # Inicializar cliente Gemini con Emergent Key
        gemini_client = genai.Client(api_key=EMERGENT_LLM_KEY)
        
        # Prompt para extraer muebles de cocina del presupuesto
        prompt = """Analiza este documento PDF de presupuesto de cocina y extrae todos los muebles.

Para cada mueble encontrado, extrae:
1. Código del mueble (ej: B60, A100, CH60)
2. Descripción/nombre del mueble
3. Ancho en centímetros
4. Alto en centímetros
5. Fondo/profundidad en centímetros
6. Cantidad
7. Precio si está disponible

IMPORTANTE:
- Las medidas deben estar en centímetros (cm)
- Si el código incluye el ancho (ej: B60 = bajo de 60cm), usa esa medida
- Códigos comunes: B=Bajo, A=Alto, CH=Columna/Alto, RE=Rinconera, FR=Fregadero

Devuelve un JSON con esta estructura exacta:
{
    "muebles": [
        {
            "codigo": "B60",
            "nombre": "BAJO 60 2P",
            "ancho": 60,
            "alto": 70,
            "fondo": 58,
            "cantidad": 1,
            "precio": 0
        }
    ],
    "cliente": "nombre del cliente si aparece",
    "total_muebles": 5,
    "notas": "observaciones adicionales"
}

Si no puedes identificar una medida específica, usa valores estándar:
- Bajos: alto=70, fondo=58
- Altos: alto=90, fondo=33
- Columnas: alto según nombre (H180=180cm), fondo=58"""

        # Ejecutar análisis con Gemini
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    types.Part.from_bytes(
                        data=pdf_bytes,
                        mime_type="application/pdf",
                    ),
                    prompt
                ]
            )
        )
        
        # Parsear respuesta JSON
        response_text = response.text
        
        # Limpiar respuesta si tiene markdown
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]
        
        result = json.loads(response_text.strip())
        
        return {
            "success": True,
            "message": f"Se detectaron {len(result.get('muebles', []))} muebles",
            "items": result.get("muebles", []),
            "cliente": result.get("cliente", ""),
            "total": result.get("total_muebles", 0),
            "notas": result.get("notas", "")
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing Gemini response: {e}")
        return {
            "success": False,
            "message": f"Error al parsear respuesta de IA: {str(e)}",
            "items": [],
            "rawText": response_text if 'response_text' in dir() else ""
        }
    except Exception as e:
        logger.error(f"Gemini analysis error: {e}")
        return {
            "success": False,
            "message": f"Error en análisis con IA: {str(e)}",
            "items": []
        }


@router.post("/import-pdf", response_model=PDFImportResult)
async def import_budget_pdf(request: PDFImportRequest):
    """
    Importar PDF de presupuesto y detectar muebles automáticamente con IA.
    Utiliza Gemini Vision para extraer la información del presupuesto.
    """
    try:
        # Decodificar PDF
        try:
            pdf_bytes = base64.b64decode(request.pdfBase64)
        except Exception:
            raise HTTPException(status_code=400, detail="PDF base64 inválido")
        
        # Analizar PDF con Gemini Vision
        analysis = await analyze_pdf_with_gemini(pdf_bytes, request.fileName)
        
        if not analysis["success"]:
            return PDFImportResult(
                success=False,
                message=analysis["message"],
                detectedItems=[],
                rawText=analysis.get("rawText", ""),
                orderId=None
            )
        
        # Convertir items detectados al formato esperado
        detected_items = []
        for item in analysis.get("items", []):
            detected_items.append({
                "productCode": item.get("codigo", ""),
                "productName": item.get("nombre", ""),
                "width": item.get("ancho", 60),
                "height": item.get("alto", 70),
                "depth": item.get("fondo", 58),
                "quantity": item.get("cantidad", 1),
                "price": item.get("precio", 0)
            })
        
        return PDFImportResult(
            success=True,
            message=f"PDF analizado correctamente. Se detectaron {len(detected_items)} muebles.",
            detectedItems=detected_items,
            rawText=analysis.get("notas", ""),
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
            grosor = item.get("grosor") or item.get("thickness") or 18  # mm, 18 si el ítem no lo especifica
            back_thickness = item.get("backThickness") or 8  # mm
            back_material = item.get("backMaterial") or f"Tablero {int(back_thickness)}mm"

            furniture_despiece = calculate_furniture_despiece(
                despiece_input,
                carcass_material,
                back_material,
                grosor,
                back_thickness
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



# ============================================
# GESTIÓN DE FÁBRICAS
# ============================================

class FactoryCreate(BaseModel):
    """Crear nueva fábrica"""
    name: str
    code: str
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None


class FactoryUpdate(BaseModel):
    """Actualizar fábrica"""
    name: Optional[str] = None
    code: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    isActive: Optional[bool] = None


@router.get("/factories")
async def get_factories():
    """Obtener lista de todas las fábricas"""
    try:
        factories = await db.factories.find({}).to_list(100)
        for f in factories:
            f['_id'] = str(f.get('_id', ''))
            if '_id' in f and f['_id'] == '':
                del f['_id']
        return factories
    except Exception as e:
        logger.error(f"Get factories error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/factories/{factory_id}")
async def get_factory(factory_id: str):
    """Obtener una fábrica por ID"""
    try:
        factory = await db.factories.find_one({"id": factory_id})
        if not factory:
            raise HTTPException(status_code=404, detail="Fábrica no encontrada")
        
        factory['_id'] = str(factory.get('_id', ''))
        if '_id' in factory and factory['_id'] == '':
            del factory['_id']
        return factory
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get factory error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/factories")
async def create_factory(factory: FactoryCreate):
    """Crear nueva fábrica"""
    try:
        # Verificar si ya existe una fábrica con el mismo código
        existing = await db.factories.find_one({"code": factory.code.upper()})
        if existing:
            raise HTTPException(status_code=400, detail=f"Ya existe una fábrica con código {factory.code}")
        
        factory_doc = {
            "id": f"fab-{uuid.uuid4().hex[:8]}",
            "name": factory.name,
            "code": factory.code.upper(),
            "address": factory.address,
            "phone": factory.phone,
            "email": factory.email,
            "isActive": True,
            "createdAt": datetime.now(timezone.utc).isoformat()
        }
        
        await db.factories.insert_one(factory_doc)
        
        # Remover _id de MongoDB para la respuesta
        factory_doc.pop('_id', None)
        
        logger.info(f"Factory created: {factory.name} ({factory.code})")
        return factory_doc
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create factory error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/factories/{factory_id}")
async def update_factory(factory_id: str, update: FactoryUpdate):
    """Actualizar fábrica"""
    try:
        update_data = {k: v for k, v in update.model_dump().items() if v is not None}
        if not update_data:
            raise HTTPException(status_code=400, detail="No hay datos para actualizar")
        
        # Si se actualiza el código, verificar que no exista
        if "code" in update_data:
            update_data["code"] = update_data["code"].upper()
            existing = await db.factories.find_one({
                "code": update_data["code"],
                "id": {"$ne": factory_id}
            })
            if existing:
                raise HTTPException(status_code=400, detail=f"Ya existe una fábrica con código {update_data['code']}")
        
        result = await db.factories.update_one(
            {"id": factory_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Fábrica no encontrada")
        
        updated = await db.factories.find_one({"id": factory_id})
        updated.pop('_id', None)
        
        return updated
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update factory error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/factories/{factory_id}")
async def delete_factory(factory_id: str):
    """Eliminar fábrica (soft delete)"""
    try:
        # Verificar que no hay usuarios asignados a esta fábrica
        users_count = await db.users.count_documents({"factoryId": factory_id})
        if users_count > 0:
            raise HTTPException(
                status_code=400, 
                detail=f"No se puede eliminar: hay {users_count} usuario(s) asignado(s) a esta fábrica"
            )
        
        result = await db.factories.update_one(
            {"id": factory_id},
            {"$set": {"isActive": False}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Fábrica no encontrada")
        
        return {"message": "Fábrica desactivada correctamente"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete factory error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# SEED: Crear fábricas por defecto
# ============================================

async def seed_default_factories():
    """Crear fábricas SALAMANCA y ZAMORA si no existen.
    
    Busca por `id` (no por code) para evitar duplicados cuando el code se ha cambiado
    manualmente en la UI (p.ej. "37" en lugar de "SAL").
    """
    default_factories = [
        {
            "id": "fab-salamanca",
            "name": "FÁBRICA SALAMANCA",
            "code": "SAL",
            "address": "Polígono Industrial Salamanca",
            "phone": "",
            "email": "",
            "isActive": True,
            "createdAt": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": "fab-zamora",
            "name": "FÁBRICA ZAMORA",
            "code": "ZAM",
            "address": "Polígono Industrial Zamora",
            "phone": "",
            "email": "",
            "isActive": True,
            "createdAt": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    for factory in default_factories:
        # Buscar por id que es el campo único (no por code que puede haber cambiado)
        existing = await db.factories.find_one({"id": factory["id"]})
        if not existing:
            try:
                await db.factories.insert_one(factory)
                logger.info(f"Created default factory: {factory['name']}")
            except Exception as e:
                # Si falla por duplicado (raza), no romper el arranque
                logger.debug(f"Skip seed factory {factory['id']}: {e}")


# Ejecutar seed al importar el módulo
try:
    loop = asyncio.get_event_loop()
    if loop.is_running():
        asyncio.create_task(seed_default_factories())
    else:
        loop.run_until_complete(seed_default_factories())
except RuntimeError:
    pass  # Ya hay un event loop corriendo
