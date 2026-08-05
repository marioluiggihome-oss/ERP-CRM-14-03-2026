# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
Orders Router - Sistema de Confirmación de Pedidos
Endpoints para confirmar pedidos, enviar emails y crear órdenes de fabricación
"""
from fastapi import APIRouter, HTTPException, Form, File, UploadFile, Depends
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

# Autenticación obligatoria en todo el router. Los pedidos se filtran por el
# usuario del token (no por un userId de query/form manipulable). Admin ve todo.
try:
    from services.jwt_service import require_auth, get_current_user, ADMIN_ROLE_FLAGS
    _DEPS = [Depends(require_auth)]
except Exception:  # pragma: no cover
    async def get_current_user():
        return None
    ADMIN_ROLE_FLAGS = ["isAdmin", "isGerente", "isDirectorComercial"]
    _DEPS = []

def _is_admin(user) -> bool:
    return bool(user) and any(user.get(f) for f in ADMIN_ROLE_FLAGS)

router = APIRouter(tags=["orders"], dependencies=_DEPS)

# Database connection


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
    current_user: Optional[dict] = Depends(get_current_user),
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
        # La propiedad del pedido la fija el usuario autenticado, no el Form.
        userId = (current_user or {}).get("id") or userId
        # Clave de SendGrid: primero de los ajustes (MASTER > Settings), luego del entorno.
        _email_settings = await _get_db().settings.find_one({"id": "global-settings"}, {"_id": 0}) or {}
        sendgrid_key = _email_settings.get('sendgridApiKey') or os.environ.get('SENDGRID_API_KEY')
        # No cortar aquí si falta SendGrid: el pedido DEBE guardarse igualmente.
        # El envío de email es best-effort (SendGrid -> Resend) más abajo; si no hay
        # ninguno configurado, el pedido se confirma igual y se avisa de que no se envió.
        
        # Parse items
        try:
            items_list = json.loads(items) if items else []
        except json.JSONDecodeError:
            items_list = []

        # Tipo de pedido: armario / cocina / mixto (para etiquetar y no aplicar
        # specs de cocina a los armarios).
        _kinds = {(it.get("itemType") or "cocina") for it in items_list}
        if _kinds == {"armario"}:
            order_kind = "armario"
        elif "armario" in _kinds:
            order_kind = "mixto"
        else:
            order_kind = "cocina"

        # =============================================
        # PRE-PROCESAR ARCHIVOS ADJUNTOS (leer una vez y reutilizar)
        # =============================================
        attachments = [attachment_0, attachment_1, attachment_2, attachment_3, attachment_4]
        processed_attachments = []
        for attachment in attachments:
            if attachment and attachment.filename:
                try:
                    content = await attachment.read()
                    if content:  # Solo si hay contenido
                        processed_attachments.append({
                            "filename": attachment.filename,
                            "content_type": attachment.content_type or "application/octet-stream",
                            "content": content,
                            "encoded": base64.b64encode(content).decode()
                        })
                        logger.info(f"Attachment processed: {attachment.filename} ({len(content)} bytes)")
                except Exception as e:
                    logger.warning(f"Could not process attachment {attachment.filename}: {e}")
        
        logger.info(f"Total attachments processed: {len(processed_attachments)}")
        
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
        
        # Email remitente desde ajustes (reutiliza el doc ya leído arriba)
        sender_email = _email_settings.get("emailSender") or _email_settings.get("senderEmail") or "no-reply@luiggihome.com"
        
        # Create SendGrid message
        message = Mail(
            from_email=sender_email,
            to_emails=email,
            subject=f"Confirmacion Pedido #{budgetNumber} - {customerName}",
            html_content=html_content
        )
        
        # Add pre-processed attachments to email
        for patt in processed_attachments:
            try:
                att = Attachment()
                att.file_content = FileContent(patt["encoded"])
                att.file_name = FileName(patt["filename"])
                att.file_type = FileType(patt["content_type"])
                att.disposition = Disposition("attachment")
                message.add_attachment(att)
                logger.info(f"Attachment added to email: {patt['filename']}")
            except Exception as att_error:
                logger.warning(f"Could not attach file {patt['filename']}: {att_error}")
        
        # Try to send email
        email_sent = False
        email_provider = None
        
        try:
            sg = SendGridAPIClient(sendgrid_key)
            sg.send(message)
            email_sent = True
            email_provider = "SendGrid"
            logger.info(f"Email sent successfully via SendGrid to {email} with {len(processed_attachments)} attachments")
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
        
        # Convertir processed_attachments para guardar en DB
        saved_attachments = [
            {
                "filename": patt["filename"],
                "content_type": patt["content_type"],
                "data": patt["encoded"]
            }
            for patt in processed_attachments
        ]
        
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
            "orderKind": order_kind,
            "attachmentsCount": len(processed_attachments),
            "attachments": saved_attachments,  # Guardar adjuntos para reenvío
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
        await _get_db().orders.insert_one(order_record)
        
        # =============================================
        # CREATE MANUFACTURING ORDER AUTOMATICALLY
        # =============================================
        manufacturing_order_id = None
        manufacturing_number = None
        try:
            current_year = datetime.now().year
            counter_id = f"manufacturing_order_{current_year}"
            
            counter_result = await _get_db().counters.find_one_and_update(
                {"_id": counter_id},
                {"$inc": {"seq": 1}},
                upsert=True,
                return_document=True
            )
            seq_number = counter_result["seq"]
            mfg_order_number = f"OF-{current_year}-{seq_number:04d}"
            
            # Generate global manufacturing number
            mfg_counter = await _get_db().counters.find_one_and_update(
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
                is_armario = (item.get("itemType") == "armario")
                # Si la línea trae medidas (armario), se usan; si no, defaults de cocina.
                def _dim(*keys, default):
                    for k in keys:
                        v = item.get(k)
                        if v not in (None, "", 0, "0"):
                            return float(v)
                    return float(default)
                width = _dim("width", "customWidth", default=(0 if is_armario else 60))
                height = _dim("height", "customHeight", default=(0 if is_armario else 70))
                depth = _dim("depth", "customDepth", default=(0 if is_armario else 58))
                qty = int(item.get("quantity", 1))
                # El armario usa su propio acabado (color de armario), no el armazón de cocina.
                item_material = (item.get("finish") if is_armario else carcassColor) or carcassColor or ""

                mfg_items.append({
                    "id": item_id,
                    "productCode": item.get("code", item.get("productCode", "")),
                    "productName": item.get("name", item.get("productName", "")),
                    "quantity": qty,
                    "width": width,
                    "height": height,
                    "depth": depth,
                    "material": item_material,
                    "doorFinish": (item.get("finish") if is_armario else (doorColorLow or doorColorHigh)) or "",
                    "itemType": item.get("itemType") or "cocina",
                    "notes": "Armario a medida" if is_armario else "",
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
                "orderKind": order_kind,
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
            
            await _get_db().manufacturing_orders.insert_one(mfg_order_doc)
            manufacturing_order_id = mfg_order_doc["id"]
            
            # Update order with manufacturing reference
            await _get_db().orders.update_one(
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
                "message": "Pedido confirmado." + (f" Orden de fabricacion N FAB: {manufacturing_number} creada." if manufacturing_number else "") + " El email no se pudo enviar (problema con SendGrid y Resend).",
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
async def get_user_orders(limit: int = 100, current_user: Optional[dict] = Depends(get_current_user)):
    """
    Pedidos confirmados del usuario autenticado (admin/dirección ven todos).
    Sincroniza el estado de fabricacion con fabrica_orders.
    """
    try:
        query = {} if _is_admin(current_user) else {"userId": (current_user or {}).get("id")}

        orders = await _get_db().orders.find(query, {"_id": 0}).sort("confirmedAt", -1).limit(limit).to_list(limit)
        
        # Sync fabrication status
        for order in orders:
            fab_order = await _get_db().fabrica_orders.find_one(
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
async def get_order_detail(order_id: str, current_user: Optional[dict] = Depends(get_current_user)):
    """Detalle de un pedido (solo su propietario o admin/dirección)."""
    try:
        order = await _get_db().orders.find_one({"id": order_id}, {"_id": 0})
        if not order:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")
        owner = order.get("userId") or order.get("createdByUserId")
        if not _is_admin(current_user) and owner and owner != (current_user or {}).get("id"):
            raise HTTPException(status_code=403, detail="Sin acceso a este pedido")
        return order
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching order {order_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))



# ============================================
# ENVIAR COPIA DE PEDIDO CON ADJUNTOS
# ============================================

from pydantic import BaseModel
from services.db_client import get_db as _get_db

class SendCopyRequest(BaseModel):
    """Request para enviar copia de pedido"""
    recipient_email: str
    include_attachments: bool = True
    additional_message: str = ""


@router.post("/orders/{order_id}/send-copy")
async def send_order_copy(order_id: str, request: SendCopyRequest, current_user: Optional[dict] = Depends(get_current_user)):
    """
    Envía una copia del pedido a un email especificado.
    Incluye los archivos adjuntos del cliente si están disponibles.
    """
    try:
        # Obtener pedido
        order = await _get_db().orders.find_one({"id": order_id}, {"_id": 0})
        if not order:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")
        owner = order.get("userId") or order.get("createdByUserId")
        if not _is_admin(current_user) and owner and owner != (current_user or {}).get("id"):
            raise HTTPException(status_code=403, detail="Sin acceso a este pedido")

        sendgrid_key = os.environ.get('SENDGRID_API_KEY')
        if not sendgrid_key:
            raise HTTPException(status_code=500, detail="SendGrid API key not configured")
        
        # Construir contenido del email
        budget_number = order.get('budgetNumber', 'N/A')
        customer_name = order.get('customerName', 'Sin especificar')
        customer_address = order.get('customerAddress', '')
        total_amount = order.get('totalAmount', 0)
        notes = order.get('notes', '')
        items = order.get('items', [])
        specs = order.get('specifications', {})
        confirmed_at = order.get('confirmedAt', '')
        
        # Construir tabla de items
        items_html = ""
        for idx, item in enumerate(items, 1):
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
        
        additional_msg = ""
        if request.additional_message:
            additional_msg = f'<div style="background: #e0f2fe; border-left: 4px solid #0ea5e9; padding: 15px; margin: 20px 0;"><strong>Mensaje adicional:</strong> {request.additional_message}</div>'
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #1e293b 0%, #334155 100%); color: white; padding: 30px; border-radius: 10px 10px 0 0;">
                <h1 style="margin: 0; font-size: 24px;">LUIGGI HOME</h1>
                <p style="margin: 10px 0 0 0; opacity: 0.8; font-size: 14px;">Copia de Pedido Confirmado</p>
            </div>
            
            <div style="background: #f8fafc; padding: 30px; border: 1px solid #e2e8f0; border-top: none;">
                <h2 style="color: #1e293b; margin-top: 0;">Pedido #{budget_number}</h2>
                
                {additional_msg}
                
                <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #475569; margin-top: 0; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px;">Datos del Cliente</h3>
                    <p><strong>Cliente:</strong> {customer_name}</p>
                    <p><strong>Direccion:</strong> {customer_address or 'No especificada'}</p>
                    <p><strong>Confirmado:</strong> {confirmed_at[:10] if confirmed_at else 'N/A'}</p>
                </div>
                
                <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #475569; margin-top: 0; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px;">Especificaciones</h3>
                    <p><strong>Color Puerta Bajo:</strong> {specs.get('doorColorLow', 'N/A')}</p>
                    <p><strong>Color Puerta Alto:</strong> {specs.get('doorColorHigh', 'N/A')}</p>
                    <p><strong>Color Puerta Columnas:</strong> {specs.get('doorColorColumns', 'N/A')}</p>
                    <p><strong>Color Costados:</strong> {specs.get('sideColor', 'N/A')}</p>
                    <p><strong>Color Armazon:</strong> {specs.get('carcassColor', 'N/A')}</p>
                    <p><strong>Acabado:</strong> {specs.get('globalFinish', 'N/A')}</p>
                </div>
                
                <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #475569; margin-top: 0; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px;">Articulos ({len(items)})</h3>
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
                    <h2 style="margin: 0;">TOTAL: {total_amount:,.2f} €</h2>
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
        
        # Obtener email del remitente desde configuración
        settings = await _get_db().settings.find_one({"id": "global-settings"}, {"_id": 0}) or {}
        sender_email = settings.get("emailSender") or settings.get("senderEmail") or "no-reply@luiggihome.com"
        
        # Crear mensaje
        message = Mail(
            from_email=sender_email,
            to_emails=request.recipient_email,
            subject=f"Copia Pedido #{budget_number} - {customer_name}",
            html_content=html_content
        )
        
        # Adjuntar archivos guardados si se solicita
        attachments_sent = 0
        if request.include_attachments:
            saved_attachments = order.get('attachments', [])
            for att_data in saved_attachments:
                try:
                    att = Attachment()
                    att.file_content = FileContent(att_data.get('data', ''))
                    att.file_name = FileName(att_data.get('filename', 'adjunto'))
                    att.file_type = FileType(att_data.get('content_type', 'application/octet-stream'))
                    att.disposition = Disposition("attachment")
                    message.add_attachment(att)
                    attachments_sent += 1
                except Exception as e:
                    logger.warning(f"Could not attach saved file: {e}")
        
        # Enviar email
        try:
            sg = SendGridAPIClient(sendgrid_key)
            sg.send(message)
            logger.info(f"Order copy sent to {request.recipient_email} with {attachments_sent} attachments")
            
            return {
                "success": True,
                "message": f"Copia enviada a {request.recipient_email}" + (f" con {attachments_sent} adjunto(s)" if attachments_sent > 0 else ""),
                "attachmentsSent": attachments_sent
            }
        except Exception as e:
            logger.error(f"Error sending order copy: {e}")
            
            # Intentar con Resend como fallback
            resend_key = os.environ.get('RESEND_API_KEY')
            if resend_key:
                try:
                    resend.api_key = resend_key
                    resend.Emails.send({
                        "from": "LUIGGI HOME <onboarding@resend.dev>",
                        "to": [request.recipient_email],
                        "subject": f"Copia Pedido #{budget_number} - {customer_name}",
                        "html": html_content
                    })
                    return {
                        "success": True,
                        "message": f"Copia enviada a {request.recipient_email} via Resend (sin adjuntos)",
                        "attachmentsSent": 0,
                        "warning": "Adjuntos no disponibles con Resend"
                    }
                except Exception as resend_error:
                    raise HTTPException(status_code=500, detail=f"Error enviando email: {str(resend_error)}")
            
            raise HTTPException(status_code=500, detail=f"Error enviando email: {str(e)}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending order copy: {e}")
        raise HTTPException(status_code=500, detail=str(e))
