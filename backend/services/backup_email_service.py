"""
Servicio de backup de MongoDB por email
Colecciones críticas: users, projects, clients, products, opportunities
"""
import os
import json
import logging
import base64
from datetime import datetime, timezone

import resend

logger = logging.getLogger(__name__)

CRITICAL_COLLECTIONS = ["users", "projects", "clients", "products", "opportunities"]


async def run_email_backup(db) -> dict:
    """
    Exporta colecciones críticas de MongoDB y las envía por email como adjuntos JSON.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    results = {"success": [], "errors": [], "timestamp": timestamp}

    resend.api_key = os.environ.get("RESEND_API_KEY")
    if not resend.api_key:
        results["errors"].append("RESEND_API_KEY no configurado")
        return results

    admin_email = os.environ.get("ADMIN_EMAIL", "mario@luiggihome.es")
    attachments = []
    summary_lines = []

    for collection_name in CRITICAL_COLLECTIONS:
        try:
            collection = db[collection_name]
            documents = await collection.find({}, {"_id": 0}).to_list(50000)

            # Quitar passwords de users
            if collection_name == "users":
                for doc in documents:
                    doc.pop("password", None)

            json_content = json.dumps(documents, ensure_ascii=False, indent=2, default=str)
            encoded = base64.b64encode(json_content.encode("utf-8")).decode("utf-8")

            attachments.append({
                "filename": f"backup_{collection_name}_{timestamp}.json",
                "content": encoded,
            })

            summary_lines.append(f"✅ {collection_name}: {len(documents)} documentos")
            results["success"].append({
                "collection": collection_name,
                "documents": len(documents)
            })

        except Exception as e:
            logger.error(f"Error exportando {collection_name}: {e}")
            results["errors"].append(f"{collection_name}: {str(e)}")
            summary_lines.append(f"❌ {collection_name}: ERROR - {str(e)}")

    # Enviar email con todos los adjuntos
    try:
        resend.Emails.send({
            "from": "ERP Backup <onboarding@resend.dev>",
            "to": [admin_email],
            "subject": f"🗄️ Backup ERP Luiggi Home - {timestamp}",
            "html": f"""
                <h2>Backup automático ERP Luiggi Home</h2>
                <p><strong>Fecha:</strong> {timestamp}</p>
                <h3>Resumen:</h3>
                <pre>{"<br>".join(summary_lines)}</pre>
                <p>Se adjuntan {len(attachments)} archivos JSON con los datos de las colecciones críticas.</p>
                <p><small>Backup generado automáticamente por el sistema ERP.</small></p>
            """,
            "attachments": attachments
        })
        logger.info(f"✅ Email de backup enviado a {admin_email}")
        results["email_sent"] = True
        results["email_to"] = admin_email

    except Exception as e:
        logger.error(f"Error enviando email de backup: {e}")
        results["errors"].append(f"Email: {str(e)}")
        results["email_sent"] = False

    return results
