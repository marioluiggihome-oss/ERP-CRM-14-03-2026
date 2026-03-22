"""
Orders Router - Sistema de Confirmación de Pedidos
Endpoints para confirmar pedidos, enviar emails y crear órdenes de fabricación
"""
from fastapi import APIRouter, HTTPException, Form, File, UploadFile
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
from typing import Optional
import uuid
import logging
import os
import json
import base64

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
import resend

logger = logging.getLogger(__name__)

router = APIRouter(tags=["orders"])

# Database connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'luiggi_home')
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]


# ============================================
# ORDER CONFIRMATION SYSTEM
# ============================================

@router.post("/orders/confirm")
async def confirm_order(
    budgetNumber: str = Form(...),
    customerName: str = Form(...),
    customerAddress: str = Form(""),
    totalAmount: str = Form(...),
    email: str = Form(...),
    notes: str = Form(""),
    items: str = Form("[]"),
    doorColorLow: str = Form(""),
    doorColorHigh: str = Form(""),
    doorColorColumns: str = Form(""),
    sideColor: str = Form(""),
    carcassColor: str = Form(""),
    globalFinish: str = Form(""),
    distributorName: str = Form(""),
    userId: str = Form(""),
    projectReference: str = Form(""),
    attachment_0: Optional[UploadFile] = File(None),
    attachment_1: Optional[UploadFile] = File(None),
    attachment_2: Optional[UploadFile] = File(None),
    attachment_3: Optional[UploadFile] = File(None),
    attachment_4: Optional[UploadFile] = File(None),
):
    """
    Confirma un pedido y envia un email con los detalles y archivos adjuntos.
    Crea automaticamente una orden de fabricacion.
    """
    try:
        sendgrid_key = os.environ.get('SENDGRID_API_KEY')
        if not sendgrid_key:
            raise HTTPException(status_code=500, detail="SendGrid API key not configured. Configure it in MASTER > Settings.")
        
        # Parse items
        try:
            items_list = json.loads(items) if items else []
        except json.JSONDecodeError:
            items_list = []
        
        # Build HTML email content
        items_html = ""
        for idx, item in enumerate(items_list, 1):
            item_name = item.get("name", item.get("productName", "Producto"))
            item_qty = item.get("quantity", 1)
            item_price = item.get("price", item.get("totalPrice", 0))
            items_html += f"""
            <tr style="border-bottom: 1px solid #e2e8f0;">
                <td style="padding: 12px; text-align: left;">{idx}</td>
                <td style="padding: 12px; text-align: left;">{item_name}</td>
                <td style="padding: 12px; text-align: center;">{item_qty}</td>
                <td style="padding: 12px; text-align: right;">{item_price:.2f} €</td>
            </tr>
            """
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #1e293b 0%, #334155 100%); color: white; padding: 30px; border-radius: 10px 10px 0 0;">
                <h1 style="margin: 0; font-size: 24px;">LUIGGI HOME</h1>
                <p style="margin: 10px 0 0 0; opacity: 0.8; font-size: 14px;">Confirmacion de Pedido</p>
            </div>
            
            <div style="background: #f8fafc; padding: 30px; border: 1px solid #e2e8f0; border-top: none;">
                <h2 style="color: #1e293b; margin-top: 0;">Pedido #{budgetNumber}</h2>
                
                <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #475569; margin-top: 0; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px;">Datos del Cliente</h3>
                    <p><strong>Cliente:</strong> {customerName}</p>
                    <p><strong>Direccion:</strong> {customerAddress or 'No especificada'}</p>
                    <p><strong>Email:</strong> {email}</p>
                    <p><strong>Distribuidor:</strong> {distributorName}</p>
                </div>
                
                <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #475569; margin-top: 0; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px;">Especificaciones</h3>
                    <p><strong>Color Puerta Bajo:</strong> {doorColorLow or 'N/A'}</p>
                    <p><strong>Color Puerta Alto:</strong> {doorColorHigh or 'N/A'}</p>
                    <p><strong>Color Puerta Columnas:</strong> {doorColorColumns or 'N/A'}</p>
                    <p><strong>Color Costados:</strong> {sideColor or 'N/A'}</p>
                    <p><strong>Color Armazon:</strong> {carcassColor or 'N/A'}</p>
                    <p><strong>Acabado:</strong> {globalFinish or 'N/A'}</p>
                </div>
                
                <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #475569; margin-top: 0; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px;">Articulos ({len(items_list)})</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="background: #f1f5f9;">
                                <th style="padding: 12px; text-align: left;">#</th>
                                <th style="padding: 12px; text-align: left;">Articulo</th>
                                <th style="padding: 12px; text-align: center;">Cantidad</th>
                                <th style="padding: 12px; text-align: right;">Precio</th>
                            </tr>
                        </thead>
                        <tbody>
                            {items_html}
                        </tbody>
                    </table>
                </div>
                
                <div style="background: #065f46; color: white; padding: 20px; border-radius: 8px; text-align: right;">
                    <h2 style="margin: 0;">TOTAL: {float(totalAmount):,.2f} EUR</h2>
                </div>
                
                {f'<div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin-top: 20px;"><strong>Notas:</strong> {notes}</div>' if notes else ''}
            </div>
            
            <div style="background: #1e293b; color: white; padding: 20px; border-radius: 0 0 10px 10px; text-align: center; font-size: 12px;">
                <p style="margin: 0;">LUIGGI HOME Master Design v2026</p>
                <p style="margin: 5px 0 0 0; opacity: 0.7;">Sistema de Gestion de Presupuestos de Cocina</p>
            </div>
        </body>
        </html>
        """
        
        # Get sender email from settings
        settings = await db.settings.find_one({"id": "global_settings"}, {"_id": 0})
        sender_email = settings.get("senderEmail", "no-reply@luiggihome.com") if settings else "no-reply@luiggihome.com"
        
        # Create SendGrid message
        message = Mail(
            from_email=sender_email,
            to_emails=email,
            subject=f"Confirmacion Pedido #{budgetNumber} - {customerName}",
            html_content=html_content
        )
        
        # Process attachments
        attachments = [attachment_0, attachment_1, attachment_2, attachment_3, attachment_4]
        for attachment in attachments:
            if attachment and attachment.filename:
                try:
                    content = await attachment.read()
                    encoded = base64.b64encode(content).decode()
                    
                    att = Attachment()
                    att.file_content = FileContent(encoded)
                    att.file_name = FileName(attachment.filename)
                    att.file_type = FileType(attachment.content_type or "application/octet-stream")
                    att.disposition = Disposition("attachment")
                    message.add_attachment(att)
                except Exception as att_error:
                    logger.warning(f"Could not attach file {attachment.filename}: {att_error}")
        
        # Try to send email
        email_sent = False
        email_provider = None
        
        try:
            sg = SendGridAPIClient(sendgrid_key)
            sg.send(message)
            email_sent = True
            email_provider = "SendGrid"
            logger.info(f"Email sent successfully via SendGrid to {email}")
        except Exception as sendgrid_error:
            error_str = str(sendgrid_error)
            logger.warning(f"SendGrid failed: {error_str[:200]}")
            
            # Try Resend as fallback
            resend_key = os.environ.get('RESEND_API_KEY')
            if resend_key:
                try:
                    resend.api_key = resend_key
                    resend_params = {
                        "from": "LUIGGI HOME <onboarding@resend.dev>",
                        "to": [email],
                        "subject": f"Confirmacion Pedido #{budgetNumber} - {customerName}",
                        "html": html_content
                    }
                    resend.Emails.send(resend_params)
                    email_sent = True
                    email_provider = "Resend"
                    logger.info(f"Email sent successfully via Resend to {email}")
                except Exception as resend_error:
                    logger.warning(f"Resend also failed: {resend_error}. Order will be saved without email.")
            else:
                logger.warning("No RESEND_API_KEY configured for fallback. Order saved without email.")
        
        # Save order record
        order_record = {
            "id": f"order-{uuid.uuid4().hex[:8]}",
            "budgetNumber": budgetNumber,
            "projectReference": projectReference,
            "customerName": customerName,
            "customerAddress": customerAddress,
            "totalAmount": float(totalAmount),
            "email": email,
            "notes": notes,
            "items": items_list,
            "itemsCount": len(items_list),
            "attachmentsCount": sum(1 for a in attachments if a and a.filename),
            "confirmedAt": datetime.now(timezone.utc).isoformat(),
            "status": "confirmed",
            "emailSent": email_sent,
            "emailProvider": email_provider if email_sent else None,
            "userId": userId,
            "distributorName": distributorName,
            "specifications": {
                "doorColorLow": doorColorLow,
                "doorColorHigh": doorColorHigh,
                "doorColorColumns": doorColorColumns,
                "sideColor": sideColor,
                "carcassColor": carcassColor,
                "globalFinish": globalFinish
            }
        }
        await db.orders.insert_one(order_record)
        
        # =============================================
        # CREATE MANUFACTURING ORDER AUTOMATICALLY
        # =============================================
        manufacturing_order_id = None
        manufacturing_number = None
        try:
            current_year = datetime.now().year
            counter_id = f"manufacturing_order_{current_year}"
            
            counter_result = await db.counters.find_one_and_update(
                {"_id": counter_id},
                {"$inc": {"seq": 1}},
                upsert=True,
                return_document=True
            )
            seq_number = counter_result["seq"]
            mfg_order_number = f"OF-{current_year}-{seq_number:04d}"
            
            # Generate global manufacturing number
            mfg_counter = await db.counters.find_one_and_update(
                {"_id": "manufacturing_number_global"},
                {"$inc": {"seq": 1}},
                upsert=True,
                return_document=True
            )
            manufacturing_number = mfg_counter["seq"]
            
            # Prepare manufacturing items
            mfg_items = []
            total_pieces = 0
            total_area = 0.0
            
            for item in items_list:
                item_id = f"moi-{uuid.uuid4().hex[:8]}"
                width = float(item.get("width", item.get("customWidth", 60)))
                height = float(item.get("height", item.get("customHeight", 70)))
                depth = float(item.get("depth", item.get("customDepth", 58)))
                qty = int(item.get("quantity", 1))
                
                mfg_items.append({
                    "id": item_id,
                    "productCode": item.get("code", item.get("productCode", "")),
                    "productName": item.get("name", item.get("productName", "")),
                    "quantity": qty,
                    "width": width,
                    "height": height,
                    "depth": depth,
                    "material": carcassColor or "",
                    "doorFinish": doorColorLow or doorColorHigh or "",
                    "notes": "",
                    "status": "pending",
                    "fabricationStatus": "pending"
                })
                total_pieces += qty
                total_area += (width * height * qty) / 10000  # m2
            
            # Create manufacturing order document
            mfg_order_doc = {
                "id": f"mfg-{uuid.uuid4().hex[:8]}",
                "orderNumber": mfg_order_number,
                "manufacturingNumber": manufacturing_number,
                "sourceType": "order_confirmation",
                "sourceBudgetId": None,
                "sourceOrderId": order_record["id"],
                "customerName": customerName,
                "customerCode": "",
                "contactPhone": "",
                "deliveryAddress": customerAddress,
                "createdAt": datetime.now(timezone.utc).isoformat(),
                "updatedAt": datetime.now(timezone.utc).isoformat(),
                "requestedDeliveryDate": None,
                "estimatedDeliveryDate": None,
                "actualDeliveryDate": None,
                "status": "confirmed",
                "priority": "normal",
                "items": mfg_items,
                "totalPieces": total_pieces,
                "totalArea": round(total_area, 3),
                "assignedToUserId": None,
                "assignedToName": None,
                "internalNotes": f"Creada automaticamente desde pedido #{budgetNumber}",
                "productionNotes": notes or "",
                "deliveryNotes": "",
                "createdByUserId": userId,
                "createdByName": distributorName or ""
            }
            
            await db.manufacturing_orders.insert_one(mfg_order_doc)
            manufacturing_order_id = mfg_order_doc["id"]
            
            # Update order with manufacturing reference
            await db.orders.update_one(
                {"id": order_record["id"]},
                {"$set": {
                    "manufacturingOrderId": manufacturing_order_id,
                    "manufacturingOrderNumber": mfg_order_number,
                    "manufacturingNumber": manufacturing_number
                }}
            )
            
            logger.info(f"Manufacturing order {mfg_order_number} (N FAB: {manufacturing_number}) created for order {budgetNumber}")
            
        except Exception as mfg_error:
            logger.error(f"Error creating manufacturing order: {mfg_error}")
        
        logger.info(f"Order confirmed: {budgetNumber}" + (f" sent via {email_provider} to {email}" if email_sent else " (email not sent)"))
        
        # Build response
        base_response = {
            "success": True,
            "orderId": order_record["id"],
            "manufacturingOrderId": manufacturing_order_id,
            "manufacturingNumber": manufacturing_number
        }
        
        if email_sent:
            return {
                **base_response,
                "message": f"Pedido confirmado y enviado a {email}" + (f" (via {email_provider})" if email_provider else "") + (f". Orden de fabricacion N FAB: {manufacturing_number} creada." if manufacturing_number else ""),
                "emailProvider": email_provider
            }
        else:
            return {
                **base_response,
                "message": f"Pedido confirmado." + (f" Orden de fabricacion N FAB: {manufacturing_number} creada." if manufacturing_number else "") + " El email no se pudo enviar (problema con SendGrid y Resend).",
                "warning": "Email no enviado"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Order confirmation error: {e}")
        error_msg = str(e)
        if "401" in error_msg or "Unauthorized" in error_msg:
            error_msg = "Error de autenticacion con SendGrid. Verifique que: 1) El API Key sea valido, 2) El remitente este verificado en SendGrid."
        elif "SENDGRID" in error_msg.upper():
            error_msg = "Servicio de email no configurado. Configure SendGrid en Panel Maestro > Configuracion."
        raise HTTPException(status_code=500, detail=error_msg)


# ============================================
# MIS PEDIDOS - Listar pedidos del usuario
# ============================================

@router.get("/orders")
async def get_user_orders(userId: Optional[str] = None, limit: int = 100):
    """
    Obtiene los pedidos confirmados. Si se pasa userId, filtra por usuario.
    Sincroniza el estado de fabricacion con fabrica_orders.
    """
    try:
        query = {}
        if userId:
            query["userId"] = userId
        
        orders = await db.orders.find(query, {"_id": 0}).sort("confirmedAt", -1).limit(limit).to_list(limit)
        
        # Sync fabrication status
        for order in orders:
            fab_order = await db.fabrica_orders.find_one(
                {"budgetNumber": order.get("budgetNumber")}, 
                {"_id": 0, "status": 1, "progress": 1}
            )
            if fab_order:
                fab_status_map = {
                    "draft": "pending",
                    "confirmed": "confirmed",
                    "in_progress": "in_production",
                    "completed": "ready",
                    "shipped": "shipped",
                    "delivered": "delivered"
                }
                order["fabricationStatus"] = fab_status_map.get(fab_order.get("status"), "confirmed")
                order["fabricationProgress"] = fab_order.get("progress", 0)
            else:
                order["fabricationStatus"] = "confirmed"
                order["fabricationProgress"] = 0
        
        return orders
    except Exception as e:
        logger.error(f"Error fetching orders: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders/{order_id}")
async def get_order_detail(order_id: str):
    """
    Obtiene el detalle de un pedido especifico
    """
    try:
        order = await db.orders.find_one({"id": order_id}, {"_id": 0})
        if not order:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")
        return order
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching order {order_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
