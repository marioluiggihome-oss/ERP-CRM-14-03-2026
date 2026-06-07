"""
Payment Tracker - Gestión de cobros parciales y conciliación
Permite registrar pagos parciales, calcular deuda pendiente,
y detectar facturas vencidas automáticamente.
"""
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
import uuid


class PaymentTracker:
    """Gestiona cobros parciales y estado de pago de facturas"""

    def __init__(self, db):
        """
        Args:
            db: Instancia de base de datos MongoDB (motor async)
        """
        self.db = db

    async def register_payment(
        self,
        invoice_id: str,
        amount: float,
        payment_method: str = "transferencia",
        reference: Optional[str] = None,
        notes: Optional[str] = None
    ) -> dict:
        """
        Registra un cobro parcial o total para una factura.

        Args:
            invoice_id: ID de la factura
            amount: Importe del cobro
            payment_method: Método de pago
            reference: Referencia bancaria o número de recibo
            notes: Notas adicionales

        Returns:
            Documento del pago registrado
        """
        invoice = await self.db.invoices.find_one({"id": invoice_id}, {"_id": 0})
        if not invoice:
            raise ValueError("Factura no encontrada")

        if invoice.get("status") == "cancelled":
            raise ValueError("No se puede registrar un cobro en una factura anulada")

        # Calcular total ya cobrado
        existing_payments = await self.db.payments.find(
            {"invoiceId": invoice_id, "status": "confirmed"}
        ).to_list(100)
        total_paid = sum(p.get("amount", 0) for p in existing_payments)

        invoice_total = invoice.get("total", 0)
        remaining = invoice_total - total_paid

        if amount > remaining + 0.01:  # Tolerancia de 1 céntimo
            raise ValueError(
                f"El importe ({amount:.2f}€) supera el pendiente ({remaining:.2f}€)"
            )

        # Crear registro de pago
        now = datetime.now(timezone.utc)
        payment = {
            "id": f"pay-{uuid.uuid4().hex[:8]}",
            "invoiceId": invoice_id,
            "invoiceNumber": invoice.get("invoiceNumber", ""),
            "clientName": invoice.get("clientName", ""),
            "amount": round(amount, 2),
            "paymentMethod": payment_method,
            "reference": reference or "",
            "notes": notes or "",
            "status": "confirmed",
            "paidAt": now.isoformat(),
            "createdAt": now.isoformat(),
        }

        await self.db.payments.insert_one(payment)
        payment.pop("_id", None)

        # Actualizar estado de la factura
        new_total_paid = total_paid + amount
        if new_total_paid >= invoice_total - 0.01:
            # Factura completamente pagada
            await self.db.invoices.update_one(
                {"id": invoice_id},
                {"$set": {
                    "status": "paid",
                    "paidAt": now.isoformat(),
                    "totalPaid": round(new_total_paid, 2),
                    "updatedAt": now.isoformat()
                }}
            )
        else:
            # Pago parcial
            await self.db.invoices.update_one(
                {"id": invoice_id},
                {"$set": {
                    "status": "partial",
                    "totalPaid": round(new_total_paid, 2),
                    "updatedAt": now.isoformat()
                }}
            )

        return payment

    async def get_payments(self, invoice_id: str) -> List[dict]:
        """Obtiene todos los pagos de una factura"""
        payments = await self.db.payments.find(
            {"invoiceId": invoice_id},
            {"_id": 0}
        ).sort("paidAt", -1).to_list(100)
        return payments

    async def get_balance(self, invoice_id: str) -> dict:
        """Calcula el balance de una factura (total, pagado, pendiente)"""
        invoice = await self.db.invoices.find_one({"id": invoice_id}, {"_id": 0})
        if not invoice:
            raise ValueError("Factura no encontrada")

        payments = await self.db.payments.find(
            {"invoiceId": invoice_id, "status": "confirmed"},
            {"_id": 0}
        ).to_list(100)

        total_paid = sum(p.get("amount", 0) for p in payments)
        invoice_total = invoice.get("total", 0)

        return {
            "invoiceId": invoice_id,
            "invoiceNumber": invoice.get("invoiceNumber", ""),
            "total": round(invoice_total, 2),
            "totalPaid": round(total_paid, 2),
            "remaining": round(invoice_total - total_paid, 2),
            "paymentCount": len(payments),
            "isPaid": total_paid >= invoice_total - 0.01,
            "payments": payments
        }

    async def cancel_payment(self, payment_id: str, reason: str = "") -> dict:
        """Anula un pago registrado"""
        payment = await self.db.payments.find_one({"id": payment_id}, {"_id": 0})
        if not payment:
            raise ValueError("Pago no encontrado")

        now = datetime.now(timezone.utc)
        await self.db.payments.update_one(
            {"id": payment_id},
            {"$set": {
                "status": "cancelled",
                "cancelledAt": now.isoformat(),
                "cancelReason": reason,
            }}
        )

        # Recalcular estado de la factura
        invoice_id = payment.get("invoiceId")
        confirmed = await self.db.payments.find(
            {"invoiceId": invoice_id, "status": "confirmed"}
        ).to_list(100)
        total_paid = sum(p.get("amount", 0) for p in confirmed)

        invoice = await self.db.invoices.find_one({"id": invoice_id}, {"_id": 0})
        invoice_total = invoice.get("total", 0) if invoice else 0

        if total_paid <= 0:
            new_status = "issued"
        elif total_paid >= invoice_total - 0.01:
            new_status = "paid"
        else:
            new_status = "partial"

        await self.db.invoices.update_one(
            {"id": invoice_id},
            {"$set": {"status": new_status, "totalPaid": round(total_paid, 2), "updatedAt": now.isoformat()}}
        )

        return {"message": "Pago anulado", "newInvoiceStatus": new_status}

    async def check_overdue_invoices(self) -> List[dict]:
        """
        Detecta y marca facturas vencidas.
        Debe ejecutarse periódicamente (cron diario).
        """
        now = datetime.now(timezone.utc)
        today = now.date().isoformat()

        # Buscar facturas emitidas o parciales con fecha vencimiento pasada
        overdue_filter = {
            "status": {"$in": ["issued", "partial"]},
            "dueDate": {"$lt": today}
        }

        overdue_invoices = await self.db.invoices.find(
            overdue_filter, {"_id": 0}
        ).to_list(500)

        updated_ids = []
        for inv in overdue_invoices:
            await self.db.invoices.update_one(
                {"id": inv["id"]},
                {"$set": {"status": "overdue", "updatedAt": now.isoformat()}}
            )
            updated_ids.append(inv["id"])

        return overdue_invoices

    async def get_aging_report(self) -> dict:
        """
        Genera informe de antigüedad de deuda (aging report).
        Clasifica facturas pendientes por tramos de vencimiento.
        """
        now = datetime.now(timezone.utc)
        today = now.date()

        pending_filter = {"status": {"$in": ["issued", "partial", "overdue"]}}
        invoices = await self.db.invoices.find(pending_filter, {"_id": 0}).to_list(1000)

        aging = {
            "current": {"count": 0, "amount": 0},       # No vencidas
            "1_30": {"count": 0, "amount": 0},           # 1-30 días vencidas
            "31_60": {"count": 0, "amount": 0},          # 31-60 días
            "61_90": {"count": 0, "amount": 0},          # 61-90 días
            "over_90": {"count": 0, "amount": 0},        # +90 días
        }

        for inv in invoices:
            due_str = inv.get("dueDate", "")[:10]
            try:
                due_date = datetime.strptime(due_str, "%Y-%m-%d").date()
            except:
                continue

            remaining = inv.get("total", 0) - inv.get("totalPaid", 0)
            days_overdue = (today - due_date).days

            if days_overdue <= 0:
                aging["current"]["count"] += 1
                aging["current"]["amount"] += remaining
            elif days_overdue <= 30:
                aging["1_30"]["count"] += 1
                aging["1_30"]["amount"] += remaining
            elif days_overdue <= 60:
                aging["31_60"]["count"] += 1
                aging["31_60"]["amount"] += remaining
            elif days_overdue <= 90:
                aging["61_90"]["count"] += 1
                aging["61_90"]["amount"] += remaining
            else:
                aging["over_90"]["count"] += 1
                aging["over_90"]["amount"] += remaining

        # Redondear importes
        for key in aging:
            aging[key]["amount"] = round(aging[key]["amount"], 2)

        total_pending = sum(v["amount"] for v in aging.values())
        return {
            "aging": aging,
            "totalPending": round(total_pending, 2),
            "totalInvoices": sum(v["count"] for v in aging.values()),
            "generatedAt": now.isoformat()
        }
