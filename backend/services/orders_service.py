"""
Servicio mejorado de pedidos con transacciones MongoDB y validación robusta.
Reemplaza la lógica del endpoint /orders/confirm con mejor estructura y atomicidad.
"""

import uuid
import json
import base64
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorSession

from models import OrderItemRequest, OrderConfirmRequest
from error_handler import DatabaseError, ExternalServiceError, ValidationError

logger = logging.getLogger(__name__)


class OrderService:
    """Servicio para gestión de pedidos con transacciones atómicas"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    async def confirm_order_atomic(
        self,
        order_data: OrderConfirmRequest,
        attachments: Optional[List[Dict[str, Any]]] = None,
        session: Optional[AsyncIOMotorSession] = None
    ) -> Dict[str, Any]:
        """
        Confirmar un pedido de forma atómica con transacción.
        
        Operaciones atómicas:
        1. Crear documento de pedido
        2. Incrementar contador de órdenes de fabricación
        3. Crear orden de fabricación
        
        Si alguna operación falla, la transacción se revierte.
        """
        try:
            # Validar que no exista un pedido duplicado
            existing_order = await self.db.orders.find_one(
                {"budgetNumber": order_data.budgetNumber},
                session=session
            )
            if existing_order:
                raise ValidationError(
                    f"Ya existe un pedido con número {order_data.budgetNumber}",
                    detail="Intenta con un número de presupuesto diferente"
                )
            
            # Preparar datos del pedido
            order_record = self._prepare_order_record(order_data, attachments)
            
            # Preparar datos de la orden de fabricación
            manufacturing_order = await self._prepare_manufacturing_order(
                order_data,
                session=session
            )
            
            # Ejecutar operaciones dentro de la transacción
            result = await self.db.orders.insert_one(order_record, session=session)
            order_id = result.inserted_id
            
            # Incrementar contador de órdenes de fabricación
            manufacturing_order["order_id"] = str(order_id)
            mfg_result = await self.db.manufacturing_orders.insert_one(
                manufacturing_order,
                session=session
            )
            
            logger.info(
                f"Order confirmed atomically: {order_data.budgetNumber}",
                extra={
                    "order_id": str(order_id),
                    "manufacturing_order_id": str(mfg_result.inserted_id),
                    "items_count": len(order_data.items)
                }
            )
            
            return {
                "success": True,
                "order_id": str(order_id),
                "budgetNumber": order_data.budgetNumber,
                "manufacturing_order_id": str(mfg_result.inserted_id),
                "status": "confirmed",
                "message": "Pedido confirmado exitosamente"
            }
        
        except ValidationError:
            raise
        except Exception as e:
            logger.error(
                f"Error confirming order: {str(e)}",
                exc_info=True
            )
            raise DatabaseError(
                "Error al confirmar el pedido",
                detail=str(e)
            )
    
    def _prepare_order_record(
        self,
        order_data: OrderConfirmRequest,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Preparar el documento de pedido para inserción en BD"""
        saved_attachments = []
        if attachments:
            saved_attachments = [
                {
                    "filename": att.get("filename"),
                    "content_type": att.get("content_type"),
                    "data": att.get("encoded")
                }
                for att in attachments
            ]
        
        return {
            "id": f"order-{uuid.uuid4().hex[:8]}",
            "budgetNumber": order_data.budgetNumber,
            "projectReference": order_data.projectReference or "",
            "customerName": order_data.customerName,
            "customerAddress": order_data.customerAddress or "",
            "totalAmount": order_data.totalAmount,
            "email": order_data.email,
            "notes": order_data.notes or "",
            "items": [item.dict() for item in order_data.items],
            "itemsCount": len(order_data.items),
            "attachmentsCount": len(saved_attachments),
            "attachments": saved_attachments,
            "confirmedAt": datetime.now(timezone.utc).isoformat(),
            "status": "confirmed",
            "emailSent": False,  # Se establecerá después del envío en BackgroundTask
            "emailProvider": None,
            "userId": order_data.userId or "",
            "distributorName": order_data.distributorName or "",
            "specifications": {
                "doorColorLow": order_data.doorColorLow or "",
                "doorColorHigh": order_data.doorColorHigh or "",
                "doorColorColumns": order_data.doorColorColumns or "",
                "sideColor": order_data.sideColor or "",
                "carcassColor": order_data.carcassColor or "",
                "globalFinish": order_data.globalFinish or ""
            }
        }
    
    async def _prepare_manufacturing_order(
        self,
        order_data: OrderConfirmRequest,
        session: Optional[AsyncIOMotorSession] = None
    ) -> Dict[str, Any]:
        """Preparar la orden de fabricación correlativa"""
        current_year = datetime.now().year
        
        # Incrementar contador anual de órdenes de fabricación
        counter_id = f"manufacturing_order_{current_year}"
        counter_result = await self.db.counters.find_one_and_update(
            {"_id": counter_id},
            {"$inc": {"seq": 1}},
            upsert=True,
            return_document=True,
            session=session
        )
        seq_number = counter_result["seq"]
        mfg_order_number = f"OF-{current_year}-{seq_number:04d}"
        
        # Incrementar contador global
        global_counter = await self.db.counters.find_one_and_update(
            {"_id": "manufacturing_number_global"},
            {"$inc": {"seq": 1}},
            upsert=True,
            return_document=True,
            session=session
        )
        manufacturing_number = global_counter["seq"]
        
        # Preparar ítems de fabricación
        mfg_items = []
        total_pieces = 0
        total_area = 0.0
        
        for item in order_data.items:
            item_id = f"moi-{uuid.uuid4().hex[:8]}"
            width = float(item.width or item.customWidth or 60)
            height = float(item.height or item.customHeight or 70)
            depth = float(item.depth or item.customDepth or 58)
            qty = int(item.quantity or 1)
            
            mfg_items.append({
                "id": item_id,
                "productCode": item.code or item.productCode or "",
                "productName": item.name or item.productName or "",
                "quantity": qty,
                "width": width,
                "height": height,
                "depth": depth,
                "material": order_data.carcassColor or "",
                "doorFinish": order_data.doorColorLow or order_data.doorColorHigh or "",
                "notes": "",
                "status": "pending",
                "fabricationStatus": "pending"
            })
            
            total_pieces += qty
            total_area += (width * height * qty) / 10000  # m²
        
        return {
            "id": f"mfg-{uuid.uuid4().hex[:8]}",
            "manufacturingNumber": mfg_order_number,
            "globalNumber": manufacturing_number,
            "budgetNumber": order_data.budgetNumber,
            "customerName": order_data.customerName,
            "distributorName": order_data.distributorName or "",
            "items": mfg_items,
            "totalPieces": total_pieces,
            "totalArea": round(total_area, 2),
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "status": "pending",
            "fabricationStatus": "pending"
        }
    
    async def update_order_email_status(
        self,
        order_id: str,
        email_sent: bool,
        email_provider: Optional[str] = None,
        session: Optional[AsyncIOMotorSession] = None
    ) -> bool:
        """Actualizar el estado de envío de email después de BackgroundTask"""
        try:
            result = await self.db.orders.update_one(
                {"id": order_id},
                {
                    "$set": {
                        "emailSent": email_sent,
                        "emailProvider": email_provider,
                        "emailSentAt": datetime.now(timezone.utc).isoformat() if email_sent else None
                    }
                },
                session=session
            )
            
            if result.matched_count == 0:
                logger.warning(f"Order not found for email status update: {order_id}")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Error updating order email status: {str(e)}", exc_info=True)
            return False


async def get_order_service(db: AsyncIOMotorDatabase) -> OrderService:
    """Factory function para obtener el servicio de pedidos"""
    return OrderService(db)
