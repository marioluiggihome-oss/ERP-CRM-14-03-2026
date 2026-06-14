"""
Endpoint mejorado de confirmación de pedidos.
Utiliza Pydantic para validación, transacciones atómicas y manejo centralizado de errores.
"""

import logging
from fastapi import APIRouter, HTTPException, File, UploadFile, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from typing import Optional, List
import base64

from models import OrderConfirmRequest
from error_handler import (
    ValidationError, ExternalServiceError, DatabaseError, AuthenticationError
)\nfrom orders_service import OrderService, get_order_service
from config import db

logger = logging.getLogger(__name__)
router = APIRouter(tags=["orders"])


# ============================================
# HELPER FUNCTIONS
# ============================================

async def process_uploaded_files(
    attachment_0: Optional[UploadFile] = None,
    attachment_1: Optional[UploadFile] = None,
    attachment_2: Optional[UploadFile] = None,
    attachment_3: Optional[UploadFile] = None,
    attachment_4: Optional[UploadFile] = None,
) -> List[dict]:
    \"\"\"Procesar archivos adjuntos cargados\"\"\"
    attachments = [attachment_0, attachment_1, attachment_2, attachment_3, attachment_4]
    processed_attachments = []
    
    for attachment in attachments:
        if attachment and attachment.filename:
            try:
                content = await attachment.read()
                if content:
                    processed_attachments.append({
                        "filename": attachment.filename,
                        "content_type": attachment.content_type or "application/octet-stream",
                        "content": content,
                        "encoded": base64.b64encode(content).decode()
                    })
                    logger.info(f"Attachment processed: {attachment.filename} ({len(content)} bytes)")
            except Exception as e:
                logger.warning(f"Could not process attachment {attachment.filename}: {e}")
    
    return processed_attachments


async def send_order_confirmation_email(
    order_id: str,
    order_data: OrderConfirmRequest,
    service: OrderService,
    attachments: Optional[List[dict]] = None
):
    \"\"\"
    Tarea de fondo para enviar email de confirmación de pedido.
    Se ejecuta de forma asincrónica sin bloquear la respuesta HTTP.
    \"\"\"
    try:
        import os
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
        import resend
        
        sendgrid_key = os.environ.get('SENDGRID_API_KEY')
        
        # Construir contenido HTML del email
        items_html = \"\"
        for idx, item in enumerate(order_data.items, 1):
            item_name = item.name or item.productName or \"Producto\"
            item_qty = item.quantity or 1
            item_price = item.price or 0
            items_html += f\"\"\"
            <tr style=\"border-bottom: 1px solid #e2e8f0;\">
                <td style=\"padding: 12px; text-align: left;\">{idx}</td>
                <td style=\"padding: 12px; text-align: left;\">{item_name}</td>
                <td style=\"padding: 12px; text-align: center;\">{item_qty}</td>
                <td style=\"padding: 12px; text-align: right;\">{item_price:.2f} €</td>
            </tr>
            \"\"\"
        
        html_content = f\"\"\"
        <html>
        <body style=\"font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px;\">
            <div style=\"background: linear-gradient(135deg, #1e293b 0%, #334155 100%); color: white; padding: 30px; border-radius: 10px 10px 0 0;\">
                <h1 style=\"margin: 0; font-size: 24px;\">LUIGGI HOME</h1>
                <p style=\"margin: 10px 0 0 0; opacity: 0.8; font-size: 14px;\">Confirmacion de Pedido</p>
            </div>
            
            <div style=\"background: #f8fafc; padding: 30px; border: 1px solid #e2e8f0; border-top: none;\">
                <h2 style=\"color: #1e293b; margin-top: 0;\">Pedido #{order_data.budgetNumber}</h2>
                
                <div style=\"background: white; padding: 20px; border-radius: 8px; margin: 20px 0;\">
                    <h3 style=\"color: #475569; margin-top: 0; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px;\">Datos del Cliente</h3>
                    <p><strong>Cliente:</strong> {order_data.customerName}</p>
                    <p><strong>Email:</strong> {order_data.email}</p>
                    <p><strong>Distribuidor:</strong> {order_data.distributorName or 'N/A'}</p>
                </div>
                
                <div style=\"background: white; padding: 20px; border-radius: 8px; margin: 20px 0;\">
                    <h3 style=\"color: #475569; margin-top: 0; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px;\">Articulos ({len(order_data.items)})</h3>
                    <table style=\"width: 100%; border-collapse: collapse;\">
                        <thead>
                            <tr style=\"background: #f1f5f9;\">
                                <th style=\"padding: 12px; text-align: left;\">#</th>
                                <th style=\"padding: 12px; text-align: left;\">Articulo</th>
                                <th style=\"padding: 12px; text-align: center;\">Cantidad</th>
                                <th style=\"padding: 12px; text-align: right;\">Precio</th>
                            </tr>
                        </thead>
                        <tbody>
                            {items_html}
                        </tbody>
                    </table>
                </div>
                
                <div style=\"background: #065f46; color: white; padding: 20px; border-radius: 8px; text-align: right;\">
                    <h2 style=\"margin: 0;\">TOTAL: {order_data.totalAmount:,.2f} EUR</h2>
                </div>
            </div>
        </body>
        </html>
        \"\"\"
        
        # Obtener email del remitente desde configuración
        settings = await db.settings.find_one({\"id\": \"global_settings\"}, {\"_id\": 0})
        sender_email = settings.get(\"senderEmail\", \"no-reply@luiggihome.com\") if settings else \"no-reply@luiggihome.com\"
        
        # Intentar enviar con SendGrid
        email_sent = False
        email_provider = None
        
        if sendgrid_key:
            try:
                message = Mail(
                    from_email=sender_email,
                    to_emails=order_data.email,
                    subject=f\"Confirmacion Pedido #{order_data.budgetNumber} - {order_data.customerName}\",
                    html_content=html_content
                )
                
                # Añadir adjuntos
                if attachments:
                    for att in attachments:
                        attachment = Attachment()
                        attachment.file_content = FileContent(att[\"encoded\"])
                        attachment.file_name = FileName(att[\"filename\"])
                        attachment.file_type = FileType(att[\"content_type\"])
                        attachment.disposition = Disposition(\"attachment\")
                        message.add_attachment(attachment)
                
                sg = SendGridAPIClient(sendgrid_key)
                sg.send(message)
                email_sent = True
                email_provider = \"SendGrid\"
                logger.info(f\"Email sent via SendGrid to {order_data.email}\")
            except Exception as e:
                logger.warning(f\"SendGrid failed: {str(e)[:200]}\")
        
        # Fallback a Resend si SendGrid falló
        if not email_sent:
            resend_key = os.environ.get('RESEND_API_KEY')
            if resend_key:
                try:
                    resend.api_key = resend_key
                    resend.Emails.send({
                        \"from\": \"LUIGGI HOME <onboarding@resend.dev>\",
                        \"to\": [order_data.email],
                        \"subject\": f\"Confirmacion Pedido #{order_data.budgetNumber} - {order_data.customerName}\",
                        \"html\": html_content
                    })
                    email_sent = True
                    email_provider = \"Resend\"
                    logger.info(f\"Email sent via Resend to {order_data.email}\")
                except Exception as e:
                    logger.warning(f\"Resend also failed: {str(e)}\")
        
        # Actualizar estado de email en el pedido
        await service.update_order_email_status(order_id, email_sent, email_provider)
        
    except Exception as e:
        logger.error(f\"Error in background email task: {str(e)}\", exc_info=True)


# ============================================
# ENDPOINTS
# ============================================

@router.post(\"/orders/confirm\")
async def confirm_order(
    order_data: OrderConfirmRequest,
    background_tasks: BackgroundTasks,
    attachment_0: Optional[UploadFile] = File(None),
    attachment_1: Optional[UploadFile] = File(None),
    attachment_2: Optional[UploadFile] = File(None),
    attachment_3: Optional[UploadFile] = File(None),
    attachment_4: Optional[UploadFile] = File(None),
):
    \"\"\"
    Confirmar un pedido de forma atómica.
    
    Operaciones:
    1. Validar datos con Pydantic
    2. Procesar archivos adjuntos
    3. Crear pedido y orden de fabricación en transacción atómica
    4. Enviar email en tarea de fondo (BackgroundTasks)
    
    Respuesta inmediata: Pedido confirmado
    Tarea de fondo: Envío de email
    \"\"\"
    try:
        # Procesar archivos adjuntos
        attachments = await process_uploaded_files(
            attachment_0, attachment_1, attachment_2, attachment_3, attachment_4
        )
        
        # Obtener servicio de pedidos
        order_service = await get_order_service(db)
        
        # Crear sesión para transacción
        async with await db.client.start_session() as session:
            async with session.start_transaction():
                # Confirmar pedido de forma atómica
                result = await order_service.confirm_order_atomic(
                    order_data,
                    attachments=attachments,
                    session=session
                )
        
        # Programar envío de email como tarea de fondo
        background_tasks.add_task(
            send_order_confirmation_email,
            result[\"order_id\"],
            order_data,
            order_service,
            attachments
        )
        
        return {
            \"success\": True,
            \"message\": \"Pedido confirmado exitosamente. Email será enviado en breve.\",
            \"order_id\": result[\"order_id\"],
            \"budgetNumber\": order_data.budgetNumber,
            \"manufacturing_order_id\": result[\"manufacturing_order_id\"]
        }
    
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=e.message)
    except Exception as e:
        logger.error(f\"Unexpected error in confirm_order: {str(e)}\", exc_info=True)
        raise HTTPException(status_code=500, detail=\"Error interno del servidor\")
