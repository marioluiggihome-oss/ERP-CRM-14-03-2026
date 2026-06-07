"""
Módulo de Facturación - LUIGGI HOME
Generación de facturas PDF, envío por email y gestión del ciclo de vida
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File as FastAPIFile
from fastapi.responses import StreamingResponse, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict
from pydantic import BaseModel
import logging
import os
import io
import uuid
import base64
from io import BytesIO

# PDF
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/invoices", tags=["Invoices"])
security = HTTPBearer(auto_error=False)

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'luiggi_home')
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]


# ─── Modelos ────────────────────────────────────────────────────────────────

class InvoiceLine(BaseModel):
    description: str
    quantity: float = 1
    unitPrice: float
    discount: float = 0       # % descuento
    vatRate: float = 21       # % IVA

class InvoiceCreate(BaseModel):
    # Referencia al presupuesto (opcional)
    projectId: Optional[str] = None
    budgetNumber: Optional[str] = None
    # Cliente
    clientName: str
    clientEmail: Optional[str] = None
    clientAddress: Optional[str] = None
    clientTaxId: Optional[str] = None     # NIF/CIF
    # Factura
    invoiceNumber: Optional[str] = None   # Si vacío, se genera automáticamente
    issueDate: Optional[str] = None       # ISO date, default hoy
    dueDate: Optional[str] = None         # Vencimiento, default +30d
    lines: List[InvoiceLine] = []
    notes: Optional[str] = None
    vatRate: float = 21
    # Estado
    status: str = "draft"               # draft | issued | paid | overdue | cancelled

class InvoiceUpdate(BaseModel):
    clientName: Optional[str] = None
    clientEmail: Optional[str] = None
    clientAddress: Optional[str] = None
    clientTaxId: Optional[str] = None
    dueDate: Optional[str] = None
    lines: Optional[List[InvoiceLine]] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    paidAt: Optional[str] = None


# ─── Helpers ────────────────────────────────────────────────────────────────

async def next_invoice_number() -> str:
    """Genera el siguiente número de factura FAC-YYYY-NNN"""
    year = datetime.now(timezone.utc).year
    prefix = f"FAC-{year}-"
    last = await db.invoices.find_one(
        {"invoiceNumber": {"$regex": f"^{prefix}"}},
        sort=[("invoiceNumber", -1)]
    )
    if last:
        try:
            last_num = int(last["invoiceNumber"].split("-")[-1])
        except:
            last_num = 0
    else:
        last_num = 0
    return f"{prefix}{last_num + 1:03d}"


def calc_totals(lines: list, default_vat: float = 21):
    """Calcula subtotal, descuento, base imponible, IVA y total"""
    subtotal = 0
    total_discount = 0
    total_vat = 0
    line_details = []
    for line in lines:
        qty = line.get("quantity", 1)
        price = line.get("unitPrice", 0)
        disc = line.get("discount", 0)
        vat = line.get("vatRate", default_vat)
        gross = qty * price
        disc_amt = gross * disc / 100
        net = gross - disc_amt
        vat_amt = net * vat / 100
        subtotal += gross
        total_discount += disc_amt
        total_vat += vat_amt
        line_details.append({**line, "_gross": gross, "_disc": disc_amt, "_net": net, "_vat": vat_amt})
    base = subtotal - total_discount
    total = base + total_vat
    return {
        "subtotal": round(subtotal, 2),
        "totalDiscount": round(total_discount, 2),
        "taxBase": round(base, 2),
        "totalVat": round(total_vat, 2),
        "total": round(total, 2),
        "lines": line_details
    }


def get_logo_img(logo_b64: str, w=50*mm, h=18*mm):
    if not logo_b64:
        return None
    try:
        data = logo_b64.split(",")[1] if "," in logo_b64 else logo_b64
        return Image(BytesIO(base64.b64decode(data)), width=w, height=h)
    except:
        return None


def generate_invoice_pdf(invoice: dict, settings: dict) -> bytes:
    """Genera el PDF de la factura"""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=15*mm, bottomMargin=15*mm)

    brand = settings.get("brandColor", "#ea580c")
    try:
        brand_color = colors.HexColor(brand)
    except:
        brand_color = colors.HexColor("#ea580c")

    styles = getSampleStyleSheet()
    title_style  = ParagraphStyle("T", parent=styles["Normal"], fontSize=22, fontName="Helvetica-Bold", textColor=brand_color)
    h2_style     = ParagraphStyle("H2", parent=styles["Normal"], fontSize=10, fontName="Helvetica-Bold", textColor=colors.HexColor("#1e293b"))
    normal_style = ParagraphStyle("N", parent=styles["Normal"], fontSize=9, textColor=colors.HexColor("#334155"), leading=13)
    small_style  = ParagraphStyle("S", parent=styles["Normal"], fontSize=8, textColor=colors.HexColor("#64748b"), leading=11)
    right_style  = ParagraphStyle("R", parent=styles["Normal"], fontSize=9, textColor=colors.HexColor("#334155"), alignment=TA_RIGHT)
    bold_right   = ParagraphStyle("BR", parent=styles["Normal"], fontSize=10, fontName="Helvetica-Bold", textColor=colors.HexColor("#1e293b"), alignment=TA_RIGHT)

    elems = []

    # ── CABECERA ──────────────────────────────────────────────────────────
    logo_img = get_logo_img(settings.get("logo", ""))
    company_info = [
        Paragraph(settings.get("companyName", "LUIGGI HOME"), h2_style),
        Paragraph(settings.get("companyAddress", ""), small_style),
        Paragraph(f"NIF/CIF: {settings.get('companyTaxId', '')}", small_style),
        Paragraph(settings.get("companyEmail", ""), small_style),
        Paragraph(settings.get("companyPhone", ""), small_style),
    ]

    invoice_info = [
        Paragraph("FACTURA", title_style),
        Paragraph(f"Nº {invoice.get('invoiceNumber', '')}", h2_style),
        Spacer(1, 3*mm),
        Paragraph(f"Fecha emisión: {invoice.get('issueDate', '')[:10]}", normal_style),
        Paragraph(f"Vencimiento: {invoice.get('dueDate', '')[:10]}", normal_style),
        Paragraph(f"Estado: {invoice.get('status','').upper()}", small_style),
    ]

    header_data = [[logo_img or Paragraph("", normal_style), Spacer(1,1), Table([[p] for p in invoice_info])]]
    header_table = Table([
        [Table([[p] for p in company_info]), "", Table([[p] for p in invoice_info])]
    ], colWidths=[80*mm, 20*mm, 70*mm])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 0),
    ]))
    elems.append(header_table)
    elems.append(Spacer(1, 5*mm))
    elems.append(HRFlowable(width="100%", thickness=1.5, color=brand_color))
    elems.append(Spacer(1, 5*mm))

    # ── DATOS CLIENTE ──────────────────────────────────────────────────────
    client_data = [
        [Paragraph("FACTURAR A:", ParagraphStyle("LBL", parent=styles["Normal"], fontSize=8, fontName="Helvetica-Bold", textColor=colors.HexColor("#94a3b8")))],
        [Paragraph(invoice.get("clientName", ""), h2_style)],
        [Paragraph(invoice.get("clientAddress", ""), normal_style)],
        [Paragraph(f"NIF/CIF: {invoice.get('clientTaxId', '')}", small_style)],
        [Paragraph(invoice.get("clientEmail", ""), small_style)],
    ]
    ref_data = []
    if invoice.get("budgetNumber"):
        ref_data.append([Paragraph("REFERENCIA PRESUPUESTO:", ParagraphStyle("LBL2", parent=styles["Normal"], fontSize=8, fontName="Helvetica-Bold", textColor=colors.HexColor("#94a3b8")))])
        ref_data.append([Paragraph(invoice["budgetNumber"], h2_style)])

    client_ref_table = Table([
        [Table(client_data), "", Table(ref_data) if ref_data else Paragraph("", normal_style)]
    ], colWidths=[100*mm, 10*mm, 60*mm])
    client_ref_table.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 0),
    ]))
    elems.append(client_ref_table)
    elems.append(Spacer(1, 8*mm))

    # ── LÍNEAS ─────────────────────────────────────────────────────────────
    totals = calc_totals(invoice.get("lines", []), invoice.get("vatRate", 21))

    header_row = [
        Paragraph("DESCRIPCIÓN", ParagraphStyle("TH", parent=styles["Normal"], fontSize=8, fontName="Helvetica-Bold", textColor=colors.white)),
        Paragraph("CANT.", ParagraphStyle("THR", parent=styles["Normal"], fontSize=8, fontName="Helvetica-Bold", textColor=colors.white, alignment=TA_RIGHT)),
        Paragraph("P. UNIT.", ParagraphStyle("THR2", parent=styles["Normal"], fontSize=8, fontName="Helvetica-Bold", textColor=colors.white, alignment=TA_RIGHT)),
        Paragraph("DTO.", ParagraphStyle("THR3", parent=styles["Normal"], fontSize=8, fontName="Helvetica-Bold", textColor=colors.white, alignment=TA_RIGHT)),
        Paragraph("IVA", ParagraphStyle("THR4", parent=styles["Normal"], fontSize=8, fontName="Helvetica-Bold", textColor=colors.white, alignment=TA_RIGHT)),
        Paragraph("TOTAL", ParagraphStyle("THR5", parent=styles["Normal"], fontSize=8, fontName="Helvetica-Bold", textColor=colors.white, alignment=TA_RIGHT)),
    ]
    rows = [header_row]
    for line in totals["lines"]:
        rows.append([
            Paragraph(line.get("description", ""), normal_style),
            Paragraph(f"{line.get('quantity',1):.0f}", right_style),
            Paragraph(f"{line.get('unitPrice',0):,.2f} €", right_style),
            Paragraph(f"{line.get('discount',0):.0f}%", right_style),
            Paragraph(f"{line.get('vatRate',21):.0f}%", right_style),
            Paragraph(f"{line.get('_net',0):,.2f} €", right_style),
        ])

    lines_table = Table(rows, colWidths=[85*mm, 18*mm, 24*mm, 15*mm, 14*mm, 24*mm])
    lines_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), brand_color),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")]),
        ("GRID", (0,0), (-1,-1), 0.3, colors.HexColor("#e2e8f0")),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ]))
    elems.append(lines_table)
    elems.append(Spacer(1, 5*mm))

    # ── TOTALES ────────────────────────────────────────────────────────────
    totals_data = [
        ["Base imponible", f"{totals['taxBase']:,.2f} €"],
        [f"IVA ({invoice.get('vatRate',21):.0f}%)", f"{totals['totalVat']:,.2f} €"],
    ]
    if totals["totalDiscount"] > 0:
        totals_data.insert(0, ["Descuento total", f"-{totals['totalDiscount']:,.2f} €"])
    totals_data.append(["TOTAL FACTURA", f"{totals['total']:,.2f} €"])

    totals_rows = []
    for i, (k, v) in enumerate(totals_data):
        is_last = i == len(totals_data) - 1
        totals_rows.append([
            Paragraph(k, bold_right if is_last else right_style),
            Paragraph(v, bold_right if is_last else right_style),
        ])

    totals_table = Table(totals_rows, colWidths=[120*mm, 40*mm], hAlign="RIGHT")
    totals_table.setStyle(TableStyle([
        ("LINEABOVE", (0, len(totals_rows)-1), (-1, len(totals_rows)-1), 1.5, brand_color),
        ("BACKGROUND", (0, len(totals_rows)-1), (-1, len(totals_rows)-1), colors.HexColor("#fef3c7")),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
        ("RIGHTPADDING", (0,0), (-1,-1), 8),
    ]))
    elems.append(totals_table)

    # ── NOTAS ──────────────────────────────────────────────────────────────
    if invoice.get("notes"):
        elems.append(Spacer(1, 8*mm))
        elems.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0")))
        elems.append(Spacer(1, 3*mm))
        elems.append(Paragraph("Notas:", h2_style))
        elems.append(Paragraph(invoice["notes"], small_style))

    # ── PIE ────────────────────────────────────────────────────────────────
    if settings.get("companyIban"):
        elems.append(Spacer(1, 6*mm))
        elems.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0")))
        elems.append(Spacer(1, 3*mm))
        elems.append(Paragraph(f"Datos bancarios: {settings.get('companyIban','')}", small_style))

    doc.build(elems)
    return buf.getvalue()


# ─── Endpoints ──────────────────────────────────────────────────────────────

@router.get("")
async def get_invoices(
    status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100
):
    """Listar facturas"""
    query = {}
    if status:
        query["status"] = status
    if search:
        import re as _re
        q = _re.escape(search)
        query["$or"] = [
            {"invoiceNumber": {"$regex": q, "$options": "i"}},
            {"clientName": {"$regex": q, "$options": "i"}},
            {"budgetNumber": {"$regex": q, "$options": "i"}},
        ]
    invoices = await db.invoices.find(query, {"_id": 0}).sort("createdAt", -1).limit(limit).to_list(limit)
    return invoices


@router.get("/next-number")
async def get_next_number():
    """Obtener el siguiente número de factura"""
    num = await next_invoice_number()
    return {"nextNumber": num}


@router.get("/stats")
async def get_invoice_stats():
    """Estadísticas de facturación"""
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()

    total = await db.invoices.count_documents({})
    draft = await db.invoices.count_documents({"status": "draft"})
    issued = await db.invoices.count_documents({"status": "issued"})
    paid = await db.invoices.count_documents({"status": "paid"})
    overdue = await db.invoices.count_documents({"status": "overdue"})

    # Total facturado este mes
    pipeline = [
        {"$match": {"status": {"$in": ["issued","paid"]}, "createdAt": {"$gte": month_start}}},
        {"$group": {"_id": None, "total": {"$sum": "$total"}}}
    ]
    month_result = await db.invoices.aggregate(pipeline).to_list(1)
    month_total = month_result[0]["total"] if month_result else 0

    # Total pendiente de cobro
    pipeline2 = [
        {"$match": {"status": "issued"}},
        {"$group": {"_id": None, "total": {"$sum": "$total"}}}
    ]
    pending_result = await db.invoices.aggregate(pipeline2).to_list(1)
    pending_total = pending_result[0]["total"] if pending_result else 0

    return {
        "total": total, "draft": draft, "issued": issued,
        "paid": paid, "overdue": overdue,
        "monthTotal": round(month_total, 2),
        "pendingTotal": round(pending_total, 2)
    }


@router.get("/{invoice_id}")
async def get_invoice(invoice_id: str):
    inv = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not inv:
        raise HTTPException(404, "Factura no encontrada")
    return inv


@router.post("")
async def create_invoice(invoice: InvoiceCreate):
    """Crear una nueva factura (manual o desde presupuesto)"""
    now = datetime.now(timezone.utc)

    # Número de factura
    inv_number = invoice.invoiceNumber or await next_invoice_number()

    # Fechas
    issue = invoice.issueDate or now.date().isoformat()
    due = invoice.dueDate or (now + timedelta(days=30)).date().isoformat()

    # Si viene de un presupuesto, enriquecer con sus datos
    lines = [l.model_dump() for l in invoice.lines]
    if invoice.projectId and not lines:
        project = await db.projects.find_one({"id": invoice.projectId}, {"_id": 0})
        if project:
            items_montada = project.get("itemsMontada", [])
            items_despiece = project.get("itemsDespiece", [])
            all_items = items_montada + items_despiece
            for item in all_items:
                lines.append({
                    "description": f"{item.get('productCode','')} - {item.get('productName','')}",
                    "quantity": item.get("quantity", 1),
                    "unitPrice": round(item.get("totalPoints", 0) / max(item.get("quantity", 1), 1), 2),
                    "discount": 0,
                    "vatRate": 21,
                })

    totals = calc_totals(lines, invoice.vatRate)

    doc = {
        "id": f"inv-{uuid.uuid4().hex[:8]}",
        "invoiceNumber": inv_number,
        "projectId": invoice.projectId,
        "budgetNumber": invoice.budgetNumber,
        "clientName": invoice.clientName,
        "clientEmail": invoice.clientEmail or "",
        "clientAddress": invoice.clientAddress or "",
        "clientTaxId": invoice.clientTaxId or "",
        "issueDate": issue,
        "dueDate": due,
        "lines": lines,
        "notes": invoice.notes or "",
        "vatRate": invoice.vatRate,
        "status": invoice.status,
        **{k: v for k, v in totals.items() if k != "lines"},
        "createdAt": now.isoformat(),
        "updatedAt": now.isoformat(),
    }

    await db.invoices.insert_one(doc)
    doc.pop("_id", None)

    # Si status=issued, marcar el presupuesto como facturado
    if invoice.projectId and invoice.status == "issued":
        await db.projects.update_one(
            {"id": invoice.projectId},
            {"$set": {"invoiceId": doc["id"], "invoiceNumber": inv_number}}
        )

    return doc


@router.post("/from-project/{project_id}")
async def create_invoice_from_project(project_id: str):
    """Crear factura automáticamente desde un presupuesto aceptado"""
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(404, "Presupuesto no encontrado")
    if project.get("status") not in ["aceptado", "en_fabricacion", "entregado"]:
        raise HTTPException(400, f"El presupuesto debe estar aceptado (estado actual: {project.get('status')})")

    # Construir líneas desde los items
    lines = []
    for item in project.get("itemsMontada", []) + project.get("itemsDespiece", []):
        qty = item.get("quantity", 1)
        total_pts = item.get("totalPoints", 0)
        unit = round(total_pts / max(qty, 1), 2)
        lines.append({
            "description": f"{item.get('productCode','')} · {item.get('productName','')}",
            "quantity": qty,
            "unitPrice": unit,
            "discount": 0,
            "vatRate": 21,
        })

    inv_number = await next_invoice_number()
    now = datetime.now(timezone.utc)
    totals = calc_totals(lines)

    # Intentar obtener datos del cliente
    client_name = project.get("customerName", "")
    client_addr = project.get("customerAddress", "")
    client_email = ""
    client_taxid = ""
    if project.get("clientCode"):
        client = await db.clients.find_one({"code": project["clientCode"]}, {"_id": 0})
        if client:
            client_email = client.get("email", "")
            client_taxid = client.get("taxId", client.get("cif", ""))

    doc = {
        "id": f"inv-{uuid.uuid4().hex[:8]}",
        "invoiceNumber": inv_number,
        "projectId": project_id,
        "budgetNumber": project.get("budgetNumber", ""),
        "clientName": client_name,
        "clientEmail": client_email,
        "clientAddress": client_addr,
        "clientTaxId": client_taxid,
        "issueDate": now.date().isoformat(),
        "dueDate": (now + timedelta(days=30)).date().isoformat(),
        "lines": lines,
        "notes": "",
        "vatRate": 21,
        "status": "issued",
        **{k: v for k, v in totals.items() if k != "lines"},
        "createdAt": now.isoformat(),
        "updatedAt": now.isoformat(),
    }

    await db.invoices.insert_one(doc)
    doc.pop("_id", None)

    await db.projects.update_one(
        {"id": project_id},
        {"$set": {"invoiceId": doc["id"], "invoiceNumber": inv_number}}
    )

    return doc


@router.put("/{invoice_id}")
async def update_invoice(invoice_id: str, update: InvoiceUpdate):
    inv = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not inv:
        raise HTTPException(404, "Factura no encontrada")

    data = {k: v for k, v in update.model_dump().items() if v is not None}
    if "lines" in data:
        totals = calc_totals(data["lines"], inv.get("vatRate", 21))
        data.update({k: v for k, v in totals.items() if k != "lines"})

    data["updatedAt"] = datetime.now(timezone.utc).isoformat()
    await db.invoices.update_one({"id": invoice_id}, {"$set": data})
    return await db.invoices.find_one({"id": invoice_id}, {"_id": 0})


@router.delete("/{invoice_id}")
async def delete_invoice(invoice_id: str):
    result = await db.invoices.delete_one({"id": invoice_id})
    if result.deleted_count == 0:
        raise HTTPException(404, "Factura no encontrada")
    return {"message": "Factura eliminada"}


@router.get("/{invoice_id}/pdf")
async def download_invoice_pdf(invoice_id: str):
    """Descargar PDF de la factura"""
    inv = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not inv:
        raise HTTPException(404, "Factura no encontrada")

    settings = await db.settings.find_one({"id": "global-settings"}, {"_id": 0}) or {}
    pdf = generate_invoice_pdf(inv, settings)

    return StreamingResponse(
        io.BytesIO(pdf),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=Factura_{inv['invoiceNumber']}.pdf"}
    )


@router.post("/{invoice_id}/send-email")
async def send_invoice_by_email(invoice_id: str, body: dict = {}):
    """Enviar factura por email al cliente"""
    from services.email_service import send_email

    inv = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not inv:
        raise HTTPException(404, "Factura no encontrada")

    to_email = body.get("email") or inv.get("clientEmail")
    if not to_email:
        raise HTTPException(400, "No hay email del cliente. Añádelo antes de enviar.")

    settings = await db.settings.find_one({"id": "global-settings"}, {"_id": 0}) or {}
    pdf = generate_invoice_pdf(inv, settings)

    company = settings.get("companyName", "LUIGGI HOME")
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
      <h2 style="color: #ea580c;">Factura {inv['invoiceNumber']}</h2>
      <p>Estimado/a <strong>{inv.get('clientName','')}</strong>,</p>
      <p>Adjuntamos la factura <strong>{inv['invoiceNumber']}</strong> por importe de <strong>{inv.get('total',0):,.2f} €</strong> (IVA incluido).</p>
      <p>Fecha de vencimiento: <strong>{inv.get('dueDate','')[:10]}</strong></p>
      {'<p><strong>Datos bancarios:</strong> ' + settings.get('companyIban','') + '</p>' if settings.get('companyIban') else ''}
      <p style="color: #64748b; font-size: 12px;">Un saludo,<br>{company}</p>
    </div>
    """

    sent = await send_email(
        to_email=to_email,
        subject=f"Factura {inv['invoiceNumber']} - {company}",
        html_content=html,
        attachments=[{
            "data": pdf,
            "filename": f"Factura_{inv['invoiceNumber']}.pdf",
            "type": "application/pdf"
        }]
    )

    if sent:
        await db.invoices.update_one(
            {"id": invoice_id},
            {"$set": {"sentAt": datetime.now(timezone.utc).isoformat(), "sentTo": to_email}}
        )
        return {"success": True, "message": f"Factura enviada a {to_email}"}
    else:
        raise HTTPException(500, "No se pudo enviar el email. Comprueba la configuración de SendGrid.")


@router.patch("/{invoice_id}/status")
async def change_invoice_status(invoice_id: str, body: dict):
    """Cambiar estado de la factura"""
    valid = ["draft", "issued", "paid", "overdue", "cancelled", "partial"]
    new_status = body.get("status")
    if new_status not in valid:
        raise HTTPException(400, f"Estado inválido. Válidos: {valid}")

    now = datetime.now(timezone.utc).isoformat()
    update = {"status": new_status, "updatedAt": now}
    if new_status == "paid":
        update["paidAt"] = body.get("paidAt", now)

    await db.invoices.update_one({"id": invoice_id}, {"$set": update})
    return await db.invoices.find_one({"id": invoice_id}, {"_id": 0})


# ═══════════════════════════════════════════════════════════════════════════════
# FACTURA ELECTRÓNICA (FacturaE 3.2.2)
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/{invoice_id}/facturae")
async def download_facturae_xml(invoice_id: str):
    """Descargar factura en formato FacturaE 3.2.2 (XML)"""
    from services.facturacion import FacturaeGenerator

    inv = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not inv:
        raise HTTPException(404, "Factura no encontrada")

    settings = await db.settings.find_one({"id": "global-settings"}, {"_id": 0}) or {}

    generator = FacturaeGenerator(settings)
    # Determinar tipo por la serie
    inv_number = inv.get("invoiceNumber", "")
    if inv_number.startswith("REC-"):
        inv_type = "rectificativa"
    elif inv_number.startswith("PRO-"):
        inv_type = "proforma"
    else:
        inv_type = "factura"

    xml_content = generator.generate(inv, inv_type)

    return Response(
        content=xml_content.encode("utf-8"),
        media_type="application/xml",
        headers={"Content-Disposition": f"attachment; filename=FacturaE_{inv_number}.xml"}
    )


@router.get("/{invoice_id}/sii-json")
async def get_sii_json(invoice_id: str):
    """Obtener JSON para envío al SII de la AEAT"""
    from services.facturacion import AccountingExporter

    inv = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not inv:
        raise HTTPException(404, "Factura no encontrada")

    settings = await db.settings.find_one({"id": "global-settings"}, {"_id": 0}) or {}
    exporter = AccountingExporter()
    sii_data = exporter.export_sii_json([inv], settings)
    return sii_data


# ═══════════════════════════════════════════════════════════════════════════════
# EXPORTACIÓN CONTABLE
# ═══════════════════════════════════════════════════════════════════════════════

class ExportRequest(BaseModel):
    format: str = "csv"  # csv | a3 | sage | sii
    dateFrom: Optional[str] = None
    dateTo: Optional[str] = None
    status: Optional[str] = None


@router.post("/export/accounting")
async def export_accounting(req: ExportRequest):
    """Exportar facturas en formato contable (CSV estándar, a3, Sage, SII)"""
    from services.facturacion import AccountingExporter

    query = {}
    if req.status:
        query["status"] = req.status
    if req.dateFrom:
        query["issueDate"] = {"$gte": req.dateFrom}
    if req.dateTo:
        if "issueDate" in query:
            query["issueDate"]["$lte"] = req.dateTo
        else:
            query["issueDate"] = {"$lte": req.dateTo}

    invoices = await db.invoices.find(query, {"_id": 0}).sort("issueDate", 1).to_list(5000)
    if not invoices:
        raise HTTPException(404, "No hay facturas para exportar con esos filtros")

    exporter = AccountingExporter()
    settings = await db.settings.find_one({"id": "global-settings"}, {"_id": 0}) or {}

    if req.format == "a3":
        content = exporter.export_a3_format(invoices)
        filename = f"facturas_a3_{datetime.now().strftime('%Y%m%d')}.txt"
        media_type = "text/plain"
    elif req.format == "sage":
        content = exporter.export_sage_format(invoices)
        filename = f"facturas_sage_{datetime.now().strftime('%Y%m%d')}.csv"
        media_type = "text/csv"
    elif req.format == "sii":
        import json
        sii_data = exporter.export_sii_json(invoices, settings)
        content = json.dumps(sii_data, ensure_ascii=False, indent=2)
        filename = f"facturas_sii_{datetime.now().strftime('%Y%m%d')}.json"
        media_type = "application/json"
    else:
        content = exporter.export_csv_standard(invoices)
        filename = f"facturas_contabilidad_{datetime.now().strftime('%Y%m%d')}.csv"
        media_type = "text/csv"

    return Response(
        content=content.encode("utf-8"),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ═══════════════════════════════════════════════════════════════════════════════
# COBROS PARCIALES
# ═══════════════════════════════════════════════════════════════════════════════

class PaymentCreate(BaseModel):
    amount: float
    paymentMethod: str = "transferencia"
    reference: Optional[str] = None
    notes: Optional[str] = None


@router.post("/{invoice_id}/payments")
async def register_payment(invoice_id: str, payment: PaymentCreate):
    """Registrar un cobro parcial o total"""
    from services.facturacion import PaymentTracker
    tracker = PaymentTracker(db)
    try:
        result = await tracker.register_payment(
            invoice_id=invoice_id,
            amount=payment.amount,
            payment_method=payment.paymentMethod,
            reference=payment.reference,
            notes=payment.notes
        )
        return result
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/{invoice_id}/payments")
async def get_payments(invoice_id: str):
    """Obtener historial de cobros de una factura"""
    from services.facturacion import PaymentTracker
    tracker = PaymentTracker(db)
    try:
        return await tracker.get_balance(invoice_id)
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.delete("/payments/{payment_id}")
async def cancel_payment(payment_id: str, body: dict = {}):
    """Anular un cobro registrado"""
    from services.facturacion import PaymentTracker
    tracker = PaymentTracker(db)
    try:
        return await tracker.cancel_payment(payment_id, body.get("reason", ""))
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.get("/reports/aging")
async def get_aging_report():
    """Informe de antigüedad de deuda"""
    from services.facturacion import PaymentTracker
    tracker = PaymentTracker(db)
    return await tracker.get_aging_report()


@router.post("/check-overdue")
async def check_overdue():
    """Detectar y marcar facturas vencidas (ejecutar periódicamente)"""
    from services.facturacion import PaymentTracker
    tracker = PaymentTracker(db)
    overdue = await tracker.check_overdue_invoices()
    return {"message": f"{len(overdue)} facturas marcadas como vencidas", "count": len(overdue)}


# ═══════════════════════════════════════════════════════════════════════════════
# SERIES DE FACTURACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/series/next")
async def get_next_number_by_series(series: str = "FAC"):
    """Obtener siguiente número por serie (FAC, REC, PRO)"""
    year = datetime.now(timezone.utc).year
    prefix = f"{series}-{year}-"
    last = await db.invoices.find_one(
        {"invoiceNumber": {"$regex": f"^{prefix}"}},
        sort=[("invoiceNumber", -1)]
    )
    if last:
        try:
            last_num = int(last["invoiceNumber"].split("-")[-1])
        except:
            last_num = 0
    else:
        last_num = 0
    return {"series": series, "nextNumber": f"{prefix}{last_num + 1:03d}"}


# ═══════════════════════════════════════════════════════════════════════════════
# ARCHIVOS ADJUNTOS
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/{invoice_id}/attachments")
async def upload_attachment(invoice_id: str, file: UploadFile = FastAPIFile(...)):
    """Subir archivo adjunto a una factura (albarán, contrato, foto, etc.)"""
    inv = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not inv:
        raise HTTPException(404, "Factura no encontrada")

    # Leer archivo
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:  # Max 10MB
        raise HTTPException(400, "Archivo demasiado grande (máx. 10MB)")

    # Guardar como base64 en MongoDB (para simplicidad)
    attachment = {
        "id": f"att-{uuid.uuid4().hex[:8]}",
        "filename": file.filename,
        "contentType": file.content_type,
        "size": len(content),
        "data": base64.b64encode(content).decode("utf-8"),
        "uploadedAt": datetime.now(timezone.utc).isoformat()
    }

    await db.invoices.update_one(
        {"id": invoice_id},
        {"$push": {"attachments": attachment}}
    )

    return {
        "id": attachment["id"],
        "filename": attachment["filename"],
        "size": attachment["size"],
        "uploadedAt": attachment["uploadedAt"]
    }


@router.get("/{invoice_id}/attachments")
async def list_attachments(invoice_id: str):
    """Listar archivos adjuntos de una factura"""
    inv = await db.invoices.find_one({"id": invoice_id}, {"_id": 0, "attachments": 1})
    if not inv:
        raise HTTPException(404, "Factura no encontrada")
    attachments = inv.get("attachments", [])
    # No devolver el contenido base64 en el listado
    return [{k: v for k, v in a.items() if k != "data"} for a in attachments]


@router.get("/{invoice_id}/attachments/{attachment_id}")
async def download_attachment(invoice_id: str, attachment_id: str):
    """Descargar un archivo adjunto"""
    inv = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not inv:
        raise HTTPException(404, "Factura no encontrada")

    attachments = inv.get("attachments", [])
    attachment = next((a for a in attachments if a["id"] == attachment_id), None)
    if not attachment:
        raise HTTPException(404, "Adjunto no encontrado")

    content = base64.b64decode(attachment["data"])
    return Response(
        content=content,
        media_type=attachment.get("contentType", "application/octet-stream"),
        headers={"Content-Disposition": f"attachment; filename={attachment['filename']}"}
    )


@router.delete("/{invoice_id}/attachments/{attachment_id}")
async def delete_attachment(invoice_id: str, attachment_id: str):
    """Eliminar un archivo adjunto"""
    result = await db.invoices.update_one(
        {"id": invoice_id},
        {"$pull": {"attachments": {"id": attachment_id}}}
    )
    if result.modified_count == 0:
        raise HTTPException(404, "Adjunto no encontrado")
    return {"message": "Adjunto eliminado"}
