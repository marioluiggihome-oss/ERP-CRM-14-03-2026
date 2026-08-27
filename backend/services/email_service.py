# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
Email service using SendGrid
"""
import os
import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
import base64
from services.marca import con_marca, nombre_comercial

logger = logging.getLogger(__name__)


def get_sendgrid_client():
    """Get SendGrid client if API key is configured"""
    api_key = os.environ.get('SENDGRID_API_KEY')
    if not api_key:
        return None
    return SendGridAPIClient(api_key)


async def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    from_email: str = None,
    attachments: list = None
) -> bool:
    """
    Send an email using SendGrid
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        html_content: HTML body content
        from_email: Sender email (defaults to env SENDGRID_FROM_EMAIL)
        attachments: List of attachment dicts with 'data', 'filename', 'type'
    
    Returns:
        bool: True if sent successfully
    """
    sg = get_sendgrid_client()
    if not sg:
        logger.warning("SendGrid not configured - email not sent")
        return False
    
    # SIN REMITENTE CONFIGURADO NO SE ENVÍA, y esto no es celo: aquí había un
    # `'noreply@luiggihome.com'` de reserva, así que una instalación sin
    # configurar mandaba los correos de sus clientes DESDE EL DOMINIO DE OTRA
    # EMPRESA. Eso no es un detalle de marca: es suplantación, rebota por SPF y
    # deja el rastro en la bandeja del destinatario. Mejor no enviar y decirlo.
    sender = (from_email or os.environ.get('SENDGRID_FROM_EMAIL') or '').strip()
    if not sender:
        logger.error(
            "No hay remitente de correo configurado (SENDGRID_FROM_EMAIL). "
            "No se envía: mandar desde un dominio ajeno es peor que no mandar.")
        return False

    
    message = Mail(
        from_email=sender,
        to_emails=to_email,
        subject=subject,
        html_content=html_content
    )
    
    # Add attachments if any
    if attachments:
        for att in attachments:
            attachment = Attachment(
                FileContent(base64.b64encode(att['data']).decode() if isinstance(att['data'], bytes) else att['data']),
                FileName(att['filename']),
                FileType(att.get('type', 'application/octet-stream')),
                Disposition('attachment')
            )
            message.add_attachment(attachment)
    
    try:
        response = sg.send(message)
        logger.info(f"Email sent to {to_email}: {response.status_code}")
        return response.status_code in [200, 201, 202]
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return False


async def send_backup_email(to_email: str, backup_data: bytes, backup_name: str) -> bool:
    """Send database backup via email"""
    return await send_email(
        to_email=to_email,
        subject=con_marca(f"Backup: {backup_name}", separador=" - "),
        html_content=f"""
        <h2>Backup de Base de Datos</h2>
        <p>Se adjunta el backup: <strong>{backup_name}</strong></p>
        <p>Fecha: {backup_name.split('_')[-1].replace('.json', '') if '_' in backup_name else 'N/A'}</p>
        """,
        attachments=[{
            'data': backup_data,
            'filename': backup_name,
            'type': 'application/json'
        }]
    )


async def send_order_confirmation(
    to_email: str,
    order_data: dict,
    attachments: list = None
) -> bool:
    """Send order confirmation email"""
    # El membrete solo existe si hay marca configurada. Con una marca vacía se
    # pinta el bloque sin `<h1>` en vez de un `<h1></h1>` hueco: un correo sin
    # membrete es correcto, uno con una caja vacía arriba parece roto.
    _marca = nombre_comercial()
    MARCA_H1 = f'<h1 style="margin: 0;">{_marca}</h1>' if _marca else ''
    MARCA_PIE = f'<p style="margin: 0;">{_marca}</p>' if _marca else ''
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: #1e1b4b; color: white; padding: 20px; text-align: center;">
            {MARCA_H1}
            <p style="margin: 5px 0 0 0; opacity: 0.8;">Confirmación de Pedido</p>
        </div>
        
        <div style="padding: 20px; background: #f8fafc;">
            <h2 style="color: #1e1b4b;">Pedido #{order_data.get('budgetNumber', 'N/A')}</h2>
            
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 8px 0; border-bottom: 1px solid #e2e8f0;"><strong>Cliente:</strong></td>
                    <td style="padding: 8px 0; border-bottom: 1px solid #e2e8f0;">{order_data.get('customerName', 'N/A')}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; border-bottom: 1px solid #e2e8f0;"><strong>Total:</strong></td>
                    <td style="padding: 8px 0; border-bottom: 1px solid #e2e8f0; color: #ea580c; font-weight: bold;">
                        {order_data.get('totalAmount', '0.00')} €
                    </td>
                </tr>
            </table>
            
            {f'<div style="margin-top: 20px; padding: 15px; background: #fff; border-radius: 8px;"><strong>Notas:</strong><br>{order_data.get("notes", "")}</div>' if order_data.get('notes') else ''}
        </div>
        
        <div style="padding: 15px; background: #1e1b4b; color: white; text-align: center; font-size: 12px;">
            {MARCA_PIE}
        </div>
    </div>
    """
    
    return await send_email(
        to_email=to_email,
        subject=f"Confirmación Pedido #{order_data.get('budgetNumber', '')} - {order_data.get('customerName', '')}",
        html_content=html,
        attachments=attachments
    )
