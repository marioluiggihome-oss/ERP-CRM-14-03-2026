"""
Servicio de email asincrónico con reintentos y fallback de proveedores.
Permite enviar emails sin bloquear la API principal.
"""

import os
import logging
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger(__name__)


class EmailProvider(str, Enum):
    \"\"\"Proveedores de email disponibles\"\"\"
    SENDGRID = \"sendgrid\"
    RESEND = \"resend\"


class EmailTemplate:
    \"\"\"Plantillas de email reutilizables\"\"\"
    
    @staticmethod
    def order_confirmation(
        budget_number: str,
        customer_name: str,
        email: str,
        items: List[Dict[str, Any]],
        total_amount: float,
        distributor_name: Optional[str] = None,
        notes: Optional[str] = None
    ) -> str:
        \"\"\"Generar HTML de confirmación de pedido\"\"\"
        
        items_html = \"\"
        for idx, item in enumerate(items, 1):
            item_name = item.get(\"name\") or item.get(\"productName\") or \"Producto\"
            item_qty = item.get(\"quantity\") or 1
            item_price = item.get(\"price\") or 0
            items_html += f\"\"\"
            <tr style=\"border-bottom: 1px solid #e2e8f0;\">
                <td style=\"padding: 12px; text-align: left;\">{idx}</td>
                <td style=\"padding: 12px; text-align: left;\">{item_name}</td>
                <td style=\"padding: 12px; text-align: center;\">{item_qty}</td>
                <td style=\"padding: 12px; text-align: right;\">{item_price:.2f} €</td>
            </tr>
            \"\"\"
        
        return f\"\"\"
        <html>
        <head>
            <meta charset=\"UTF-8\">
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #1e293b 0%, #334155 100%); color: white; padding: 30px; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f8fafc; padding: 30px; border: 1px solid #e2e8f0; border-top: none; }}
                .section {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .section h3 {{ color: #475569; margin-top: 0; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th {{ background: #f1f5f9; padding: 12px; text-align: left; }}
                .total {{ background: #065f46; color: white; padding: 20px; border-radius: 8px; text-align: right; }}
                .footer {{ background: #1e293b; color: white; padding: 20px; border-radius: 0 0 10px 10px; text-align: center; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class=\"header\">
                <h1 style=\"margin: 0; font-size: 24px;\">LUIGGI HOME</h1>
                <p style=\"margin: 10px 0 0 0; opacity: 0.8; font-size: 14px;\">Confirmacion de Pedido</p>
            </div>
            
            <div class=\"content\">
                <h2 style=\"color: #1e293b; margin-top: 0;\">Pedido #{budget_number}</h2>
                
                <div class=\"section\">
                    <h3>Datos del Cliente</h3>
                    <p><strong>Cliente:</strong> {customer_name}</p>
                    <p><strong>Email:</strong> {email}</p>
                    {f'<p><strong>Distribuidor:</strong> {distributor_name}</p>' if distributor_name else ''}
                </div>
                
                <div class=\"section\">
                    <h3>Articulos ({len(items)})</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Articulo</th>
                                <th style=\"text-align: center;\">Cantidad</th>
                                <th style=\"text-align: right;\">Precio</th>
                            </tr>
                        </thead>
                        <tbody>
                            {items_html}
                        </tbody>
                    </table>
                </div>
                
                <div class=\"total\">
                    <h2 style=\"margin: 0;\">TOTAL: {total_amount:,.2f} EUR</h2>
                </div>
                
                {f'<div style=\"background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin-top: 20px;\"><strong>Notas:</strong> {notes}</div>' if notes else ''}
            </div>
            
            <div class=\"footer\">
                <p style=\"margin: 0;\">LUIGGI HOME Master Design v2026</p>
                <p style=\"margin: 5px 0 0 0; opacity: 0.7;\">Sistema de Gestion de Presupuestos de Cocina</p>
            </div>
        </body>
        </html>
        \"\"\"


class EmailService:
    \"\"\"Servicio centralizado de email con reintentos y fallback\"\"\"
    
    def __init__(self):
        self.sendgrid_key = os.environ.get('SENDGRID_API_KEY')
        self.resend_key = os.environ.get('RESEND_API_KEY')
        self.max_retries = 3
        self.retry_delay = 2  # segundos
    
    async def send_order_confirmation(
        self,
        to_email: str,
        budget_number: str,
        customer_name: str,
        items: List[Dict[str, Any]],
        total_amount: float,
        distributor_name: Optional[str] = None,
        notes: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        sender_email: str = \"no-reply@luiggihome.com\"
    ) -> Dict[str, Any]:
        \"\"\"
        Enviar email de confirmación de pedido con reintentos.
        
        Intenta con SendGrid primero, luego con Resend como fallback.
        \"\"\"
        
        html_content = EmailTemplate.order_confirmation(
            budget_number=budget_number,
            customer_name=customer_name,
            email=to_email,
            items=items,
            total_amount=total_amount,
            distributor_name=distributor_name,
            notes=notes
        )
        
        subject = f\"Confirmacion Pedido #{budget_number} - {customer_name}\"
        
        # Intentar con SendGrid
        if self.sendgrid_key:
            result = await self._send_with_sendgrid(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                sender_email=sender_email,
                attachments=attachments
            )
            if result[\"success\"]:
                return result
        
        # Fallback a Resend
        if self.resend_key:
            result = await self._send_with_resend(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                attachments=attachments
            )
            if result[\"success\"]:
                return result
        
        # Si ambos fallan
        return {
            \"success\": False,
            \"provider\": None,
            \"error\": \"No hay proveedores de email disponibles\",
            \"timestamp\": datetime.now(timezone.utc).isoformat()
        }
    
    async def _send_with_sendgrid(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        sender_email: str,
        attachments: Optional[List[Dict[str, Any]]] = None,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        \"\"\"Enviar email usando SendGrid con reintentos\"\"\"
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
            
            message = Mail(
                from_email=sender_email,
                to_emails=to_email,
                subject=subject,
                html_content=html_content
            )
            
            # Añadir adjuntos si existen
            if attachments:
                for att in attachments:
                    try:
                        attachment = Attachment()
                        attachment.file_content = FileContent(att.get(\"encoded\"))
                        attachment.file_name = FileName(att.get(\"filename\"))
                        attachment.file_type = FileType(att.get(\"content_type\", \"application/octet-stream\"))
                        attachment.disposition = Disposition(\"attachment\")
                        message.add_attachment(attachment)
                    except Exception as e:
                        logger.warning(f\"Could not attach file {att.get('filename')}: {e}\")
            
            sg = SendGridAPIClient(self.sendgrid_key)
            response = sg.send(message)
            
            logger.info(f\"Email sent via SendGrid to {to_email} (status: {response.status_code})\")
            
            return {
                \"success\": True,
                \"provider\": EmailProvider.SENDGRID,
                \"status_code\": response.status_code,
                \"timestamp\": datetime.now(timezone.utc).isoformat()
            }
        
        except Exception as e:
            error_msg = str(e)[:200]
            logger.warning(f\"SendGrid failed: {error_msg}\")
            
            # Reintentar si no hemos alcanzado el máximo
            if retry_count < self.max_retries:
                logger.info(f\"Retrying SendGrid (attempt {retry_count + 1}/{self.max_retries})...\")
                await asyncio.sleep(self.retry_delay)
                return await self._send_with_sendgrid(
                    to_email=to_email,
                    subject=subject,
                    html_content=html_content,
                    sender_email=sender_email,
                    attachments=attachments,
                    retry_count=retry_count + 1
                )
            
            return {
                \"success\": False,
                \"provider\": EmailProvider.SENDGRID,
                \"error\": error_msg,
                \"timestamp\": datetime.now(timezone.utc).isoformat()
            }
    
    async def _send_with_resend(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        attachments: Optional[List[Dict[str, Any]]] = None,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        \"\"\"Enviar email usando Resend con reintentos\"\"\"
        try:
            import resend
            
            resend.api_key = self.resend_key
            
            # Nota: Resend no soporta adjuntos en el mismo formato que SendGrid
            # Se puede implementar si es necesario
            
            response = resend.Emails.send({
                \"from\": \"LUIGGI HOME <onboarding@resend.dev>\",
                \"to\": [to_email],
                \"subject\": subject,
                \"html\": html_content
            })
            
            logger.info(f\"Email sent via Resend to {to_email}\")
            
            return {
                \"success\": True,
                \"provider\": EmailProvider.RESEND,
                \"response_id\": response.get(\"id\"),
                \"timestamp\": datetime.now(timezone.utc).isoformat()
            }
        
        except Exception as e:
            error_msg = str(e)[:200]
            logger.warning(f\"Resend failed: {error_msg}\")
            
            # Reintentar si no hemos alcanzado el máximo
            if retry_count < self.max_retries:
                logger.info(f\"Retrying Resend (attempt {retry_count + 1}/{self.max_retries})...\")
                await asyncio.sleep(self.retry_delay)
                return await self._send_with_resend(
                    to_email=to_email,
                    subject=subject,
                    html_content=html_content,
                    attachments=attachments,
                    retry_count=retry_count + 1
                )
            
            return {
                \"success\": False,
                \"provider\": EmailProvider.RESEND,
                \"error\": error_msg,
                \"timestamp\": datetime.now(timezone.utc).isoformat()
            }


# Singleton para reutilizar la instancia
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    \"\"\"Obtener instancia del servicio de email\"\"\"
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
