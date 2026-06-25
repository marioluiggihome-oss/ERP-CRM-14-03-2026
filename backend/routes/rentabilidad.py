"""
Rentabilidad por proyecto (cocina): cruza VENTAS (presupuestos/proyectos) con
COSTES (facturas/gastos de proveedor) para obtener la cuenta de resultados por
cocina: Venta - Coste = Margen (EUR y %).

Modelo de datos:
- Ventas: se leen de la coleccion `projects` (presupuestos), campo totalPvp y
  budgetNumber/clientCode/customerName.
- Costes: coleccion nueva `project_costs`, un documento por gasto:
    { id, projectRef, proveedor, concepto, categoria, importe, fecha,
      createdAt, source }  (source: 'manual' | 'ia' | 'factura')
"""
from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import uuid
import logging
import os
import json
import re
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)
router = APIRouter(tags=["rentabilidad"])

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'luiggi_home')
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]


# ----------------------------- COSTES POR PROYECTO -----------------------------

@router.post("/project-costs")
async def add_project_cost(cost: dict):
    """Registrar un coste/gasto asociado a un proyecto (por su referencia)."""
    try:
        ref = (cost.get("projectRef") or "").strip()
        if not ref:
            raise HTTPException(status_code=400, detail="Falta projectRef")
        ref = await _resolve_project_cost_ref(ref)
        doc = {
            "id": f"cost-{uuid.uuid4().hex[:8]}",
            "projectRef": ref,
            "proveedor": cost.get("proveedor", ""),
            "concepto": cost.get("concepto", ""),
            "categoria": cost.get("categoria", "OTROS"),
            "importe": float(cost.get("importe", 0) or 0),
            "fecha": cost.get("fecha", datetime.now(timezone.utc).strftime("%Y-%m-%d")),
            "source": cost.get("source", "manual"),
            "createdAt": datetime.now(timezone.utc).isoformat(),
        }
        await db.project_costs.insert_one(doc)
        doc.pop("_id", None)
        return doc
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Add project cost error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/project-costs")
async def list_project_costs(projectRef: Optional[str] = None):
    """Listar costes; si se pasa projectRef, solo los de ese proyecto."""
    try:
        query = {"projectRef": projectRef} if projectRef else {}
        costs = await db.project_costs.find(query, {"_id": 0}).sort("fecha", -1).to_list(2000)
        return costs
    except Exception as e:
        logger.error(f"List project costs error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/project-costs/{cost_id}")
async def delete_project_cost(cost_id: str):
    try:
        res = await db.project_costs.delete_one({"id": cost_id})
        return {"success": True, "deleted": res.deleted_count}
    except Exception as e:
        logger.error(f"Delete project cost error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ----------------------------- RENTABILIDAD -----------------------------

@router.get("/rentabilidad")
async def get_rentabilidad(userId: Optional[str] = None):
    """Cuenta de resultados: Venta - Coste = Margen.

    Une presupuestos (`projects`) con sus costes (`project_costs`, por ref).
    Si un presupuesto ya tiene factura asociada (`invoiceId`), la venta se toma
    del importe REAL de esa factura (puede haberse editado tras la conversion)
    en lugar del totalPvp congelado del presupuesto. Ademas se incluyen como
    filas independientes los PEDIDOS y FACTURAS que no provienen de ningun
    presupuesto (creados directamente en Pedidos/Facturas), que antes eran
    invisibles para este informe.
    """
    try:
        query = {}
        if userId:
            query["userId"] = userId
        projects = await db.projects.find(
            query,
            {"_id": 0, "id": 1, "budgetNumber": 1, "customerName": 1, "clientCode": 1,
             "totalPvp": 1, "totalConIVA": 1, "createdAt": 1, "userId": 1, "status": 1,
             "orderId": 1, "orderRef": 1, "invoiceId": 1, "invoiceNumber": 1, "internalReference": 1}
        ).sort("createdAt", -1).to_list(3000)

        # Agregar costes por projectRef (== budgetNumber u otra ref ya normalizada)
        costs_agg = {}
        async for c in db.project_costs.find({}, {"_id": 0, "projectRef": 1, "importe": 1}):
            ref = c.get("projectRef")
            costs_agg[ref] = costs_agg.get(ref, 0) + float(c.get("importe", 0) or 0)

        # Facturas y pedidos actuales, para poder: (a) usar el importe REAL y
        # actualizado de la factura cuando un presupuesto la tenga asociada, y
        # (b) detectar las que NO vienen de ningun presupuesto.
        invoices_by_id = {}
        async for inv in db.invoices.find({}, {"_id": 0}):
            invoices_by_id[inv.get("id")] = inv

        orders_by_id = {}
        async for o in db.orders.find({}, {"_id": 0}):
            orders_by_id[o.get("id")] = o

        linked_invoice_ids = set()
        linked_order_ids = set()

        rows = []
        tot_venta = tot_coste = 0.0
        for p in projects:
            ref = p.get("budgetNumber") or ""
            invoice_id = p.get("invoiceId")
            order_id = p.get("orderId")
            inv = invoices_by_id.get(invoice_id) if invoice_id else None
            if inv:
                # Importe real de la factura (sin IVA) en vez del totalPvp congelado.
                venta = float(inv.get("taxBase", inv.get("subtotal", 0)) or 0)
                linked_invoice_ids.add(invoice_id)
            else:
                venta = float(p.get("totalPvp", 0) or 0)
            if order_id:
                linked_order_ids.add(order_id)
            coste = float(costs_agg.get(ref, 0))
            margen = venta - coste
            margen_pct = (margen / venta * 100) if venta > 0 else 0
            tot_venta += venta
            tot_coste += coste
            rows.append({
                "projectId": p.get("id"),
                "ref": ref,
                "cliente": p.get("customerName", ""),
                "clientCode": p.get("clientCode", ""),
                "fecha": p.get("createdAt", ""),
                "status": p.get("status", ""),
                "orderId": p.get("orderId", ""),
                "orderRef": p.get("orderRef", ""),
                "invoiceId": p.get("invoiceId", ""),
                "invoiceNumber": p.get("invoiceNumber", ""),
                "internalReference": p.get("internalReference", ""),
                "origen": "presupuesto",
                "venta": round(venta, 2),
                "coste": round(coste, 2),
                "margen": round(margen, 2),
                "margenPct": round(margen_pct, 1),
            })

        # Pedidos creados directamente (sin presupuesto de origen), p.ej. desde
        # confirmacion de pedido de cocina. Si ya estan facturados se omiten
        # aqui porque se contabilizan como factura mas abajo (evita duplicar).
        for oid, o in orders_by_id.items():
            if oid in linked_order_ids or o.get("sourceProjectId"):
                continue
            if o.get("invoiceId"):
                continue
            ref = o.get("budgetNumber") or oid
            venta = float(o.get("totalAmount", 0) or 0)
            coste = float(costs_agg.get(ref, 0))
            margen = venta - coste
            margen_pct = (margen / venta * 100) if venta > 0 else 0
            tot_venta += venta
            tot_coste += coste
            rows.append({
                "projectId": None,
                "ref": ref,
                "cliente": o.get("customerName", ""),
                "clientCode": "",
                "fecha": o.get("createdAt", o.get("confirmedAt", "")),
                "status": o.get("status", ""),
                "orderId": oid,
                "orderRef": ref,
                "invoiceId": "",
                "invoiceNumber": "",
                "internalReference": "",
                "origen": "pedido",
                "venta": round(venta, 2),
                "coste": round(coste, 2),
                "margen": round(margen, 2),
                "margenPct": round(margen_pct, 1),
            })

        # Facturas creadas directamente (sin presupuesto de origen).
        for iid, inv in invoices_by_id.items():
            if iid in linked_invoice_ids or inv.get("projectId"):
                continue
            ref = inv.get("budgetNumber") or inv.get("invoiceNumber") or iid
            venta = float(inv.get("taxBase", inv.get("subtotal", 0)) or 0)
            coste = float(costs_agg.get(ref, 0))
            margen = venta - coste
            margen_pct = (margen / venta * 100) if venta > 0 else 0
            tot_venta += venta
            tot_coste += coste
            rows.append({
                "projectId": None,
                "ref": ref,
                "cliente": inv.get("clientName", ""),
                "clientCode": "",
                "fecha": inv.get("createdAt", inv.get("issueDate", "")),
                "status": inv.get("status", ""),
                "orderId": "",
                "orderRef": "",
                "invoiceId": iid,
                "invoiceNumber": inv.get("invoiceNumber", ""),
                "internalReference": "",
                "origen": "factura",
                "venta": round(venta, 2),
                "coste": round(coste, 2),
                "margen": round(margen, 2),
                "margenPct": round(margen_pct, 1),
            })

        rows.sort(key=lambda r: r.get("fecha") or "", reverse=True)

        tot_margen = tot_venta - tot_coste
        return {
            "rows": rows,
            "totales": {
                "venta": round(tot_venta, 2),
                "coste": round(tot_coste, 2),
                "margen": round(tot_margen, 2),
                "margenPct": round((tot_margen / tot_venta * 100) if tot_venta > 0 else 0, 1),
                "proyectos": len(rows),
            },
        }
    except Exception as e:
        logger.error(f"Get rentabilidad error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ----------------------------- IMPORTAR FACTURA (IA) -----------------------------

_INVOICE_PROMPT = """Eres un experto en facturas de proveedor de muebles/cocinas.
Extrae los datos de la siguiente FACTURA y responde SOLO con JSON valido:
{
  "proveedor": "nombre del proveedor/emisor",
  "fecha": "YYYY-MM-DD",
  "importe": 0,                // IMPORTE TOTAL de la factura (con IVA) como numero decimal
  "base": 0,                   // base imponible si aparece (numero), si no 0
  "concepto": "resumen breve de lo facturado",
  "categoria": "MOBILIARIO|ELECTRODOMESTICOS|ENCIMERA|TRANSPORTE|MONTAJE|SUBCONTRATA|OTROS",
  "proyecto": "nº de expediente/proyecto si aparece (ej EXP-2026-001 o similar), si no vacio"
}
Importante: los importes en numero con punto decimal, sin simbolo de moneda.
"""


def _clean_json(text):
    t = (text or "").strip()
    if t.startswith("```"):
        t = t.split("```")[1]
        if t.startswith("json"):
            t = t[4:]
    return t.strip()


def _parse_json_loose(text):
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r'\{[\s\S]*\}', text or "")
        try:
            return json.loads(m.group()) if m else None
        except Exception:
            return None


def _data_url_mime(data_url: str) -> str:
    """Devuelve el MIME real de un data URL, si viene informado."""
    if not data_url or not data_url.startswith("data:"):
        return ""
    try:
        return data_url.split(";", 1)[0].split(":", 1)[1].lower()
    except Exception:
        return ""


def _safe_float(value: Any) -> float:
    """Convierte importes de factura escritos como 1.234,56 / 1234.56 / 1,234.56."""
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    if not s:
        return 0.0
    s = re.sub(r"[^0-9,.-]", "", s)
    if not s or s in {"-", ",", "."}:
        return 0.0
    if "," in s and "." in s:
        # Formato europeo habitual: 1.234,56; si la coma va despues del punto, es decimal.
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except Exception:
        return 0.0


def _normalize_date(value: Any) -> str:
    """Normaliza fechas frecuentes de factura a YYYY-MM-DD, manteniendo fecha actual como fallback."""
    fallback = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    s = str(value or "").strip()
    if not s:
        return fallback
    if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        return s
    m = re.match(r"^(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})$", s)
    if m:
        d, mo, y = m.groups()
        if len(y) == 2:
            y = "20" + y
        try:
            return datetime(int(y), int(mo), int(d)).strftime("%Y-%m-%d")
        except Exception:
            return fallback
    return fallback


def _normalize_ref(value: Any) -> str:
    """Normaliza referencias para comparar sin guiones, espacios ni mayusculas."""
    return re.sub(r"[^A-Z0-9]", "", str(value or "").upper())


def _invoice_category(value: Any) -> str:
    allowed = {"MOBILIARIO", "ELECTRODOMESTICOS", "ENCIMERA", "TRANSPORTE", "MONTAJE", "SUBCONTRATA", "OTROS"}
    cat = str(value or "OTROS").upper().replace("É", "E").strip()
    return cat if cat in allowed else "OTROS"


async def _resolve_project_cost_ref(ref: str) -> str:
    """Convierte alias de pedido/factura/referencia interna a budgetNumber cuando existe."""
    norm = _normalize_ref(ref)
    if not norm:
        return ref
    projection = {"_id": 0, "id": 1, "budgetNumber": 1, "orderRef": 1, "internalReference": 1, "invoiceNumber": 1}
    async for p in db.projects.find({}, projection):
        aliases = [p.get("budgetNumber"), p.get("orderRef"), p.get("internalReference"), p.get("invoiceNumber"), p.get("id")]
        if any(_normalize_ref(a) == norm for a in aliases if a):
            return p.get("budgetNumber") or p.get("orderRef") or p.get("internalReference") or p.get("id") or ref
    return ref


async def _find_project_matches(detected_ref: str, limit: int = 6) -> List[Dict[str, Any]]:
    """Busca coincidencias de proyecto usando presupuesto, pedido, factura e ids internos.

    Devuelve siempre `projectRef` como budgetNumber porque project_costs se agregan contra
    esa referencia. Esto evita que una factura detectada por orderRef/invoiceNumber quede
    registrada contra una clave que luego RENTAB no suma.
    """
    needle = _normalize_ref(detected_ref)
    if not needle:
        return []

    projection = {"_id": 0, "id": 1, "budgetNumber": 1, "customerName": 1, "internalReference": 1,
                  "orderRef": 1, "invoiceNumber": 1, "createdAt": 1}
    projects = await db.projects.find({}, projection).sort("createdAt", -1).to_list(3000)
    scored = []
    for p in projects:
        aliases = [p.get("budgetNumber"), p.get("orderRef"), p.get("internalReference"), p.get("invoiceNumber"), p.get("id")]
        norm_aliases = [_normalize_ref(a) for a in aliases if a]
        if not norm_aliases:
            continue
        score = 0
        matched_by = ""
        for alias, norm in zip([a for a in aliases if a], norm_aliases):
            if not norm:
                continue
            if needle == norm:
                score = max(score, 100)
                matched_by = str(alias)
            elif needle in norm or norm in needle:
                local = 80 if min(len(needle), len(norm)) >= 5 else 60
                if local > score:
                    score = local
                    matched_by = str(alias)
        if score > 0:
            project_ref = p.get("budgetNumber") or p.get("orderRef") or p.get("internalReference") or p.get("id") or ""
            scored.append({
                "projectId": p.get("id"),
                "projectRef": project_ref,
                "ref": project_ref,
                "budgetNumber": p.get("budgetNumber") or "",
                "orderRef": p.get("orderRef") or "",
                "invoiceNumber": p.get("invoiceNumber") or "",
                "internalReference": p.get("internalReference") or "",
                "cliente": p.get("customerName") or "",
                "score": score,
                "matchedBy": matched_by,
            })
    scored.sort(key=lambda x: x.get("score", 0), reverse=True)
    return scored[:limit]


@router.post("/rentabilidad/parse-invoice")
async def parse_invoice(payload: dict):
    """Lee una factura de proveedor (PDF/imagen en base64) con IA y devuelve los
    datos extraidos (proveedor, importe, concepto, fecha, categoria, proyecto)
    para que el usuario los revise antes de registrar el coste."""
    b64 = (payload or {}).get("fileBase64") or ""
    if not b64:
        raise HTTPException(status_code=400, detail="Falta el archivo (fileBase64)")
    mime = _data_url_mime(b64)
    stripped = b64.split(",", 1)[1] if b64.startswith("data:") else b64
    try:
        from services.pdf_utils import is_pdf_base64, pdf_base64_to_text, pdf_base64_to_png_base64
        from services.llm_vision import chat_with_gemini, analyze_image_with_gemini

        parsed = None
        is_pdf = (mime == "application/pdf") or ("pdf" in b64[:60].lower()) or is_pdf_base64(stripped)
        logger.info(f"parse_invoice: is_pdf={is_pdf}, mime={mime or 'desconocido'}, b64_len={len(stripped)}")
        if is_pdf:
            text = pdf_base64_to_text(stripped) or ""
            logger.info(f"parse_invoice: text extracted len={len(text.strip())}")
            if len(text.strip()) >= 50:
                resp = await chat_with_gemini(
                    prompt=_INVOICE_PROMPT + "\n\nTEXTO DE LA FACTURA:\n\n" + text[:30000],
                    system_message="Extraes datos de facturas de proveedor.",
                    model="gemini-2.5-flash",
                )
                parsed = _parse_json_loose(_clean_json(resp))
        if parsed is None:
            # Escaneada o imagen: usar vision sobre la primera pagina/imagen.
            img = stripped
            image_mime = mime if mime and mime.startswith("image/") else "image/jpeg"
            if is_pdf:
                pages = pdf_base64_to_png_base64(stripped, dpi=180, max_pages=1) or []
                if pages:
                    img = pages[0]
                    image_mime = "image/png"
            resp = await analyze_image_with_gemini(
                image_base64=img, prompt=_INVOICE_PROMPT,
                session_id=f"invoice-{uuid.uuid4().hex[:8]}", model="gemini-2.5-flash",
                image_mime=image_mime,
            )
            parsed = _parse_json_loose(_clean_json(resp))

        if not parsed:
            return {"success": False, "error": "No se pudieron extraer datos de la factura"}

        detected_project = str(parsed.get("proyecto") or "").strip()
        project_matches = await _find_project_matches(detected_project)
        selected_project_ref = project_matches[0]["projectRef"] if project_matches and project_matches[0].get("score", 0) >= 80 else ""
        importe = _safe_float(parsed.get("importe")) or _safe_float(parsed.get("total")) or _safe_float(parsed.get("base"))

        return {
            "success": True,
            "data": {
                "proveedor": str(parsed.get("proveedor") or ""),
                "fecha": _normalize_date(parsed.get("fecha")),
                "importe": round(float(importe or 0), 2),
                "concepto": str(parsed.get("concepto") or ""),
                "categoria": _invoice_category(parsed.get("categoria")),
                "proyecto": detected_project,
                "projectRef": selected_project_ref,
                "projectMatches": project_matches,
            },
        }
    except Exception as e:
        logger.error(f"Parse invoice error: {e}", exc_info=True)
        return {"success": False, "error": f"Error procesando la factura: {str(e)[:200]}"}


# ----------------------------- ANALITICA DE RENTABILIDAD -----------------------------

@router.get("/rentabilidad/analytics")
async def rentabilidad_analytics():
    """Analitica de costes: gasto por proveedor, por categoria y por mes.
    Responde a: '¿que proveedor reduce mi margen?' y la evolucion mensual."""
    try:
        by_supplier, by_category, by_month = {}, {}, {}
        async for c in db.project_costs.find({}, {"_id": 0, "proveedor": 1, "categoria": 1, "importe": 1, "fecha": 1}):
            imp = float(c.get("importe", 0) or 0)
            prov = (c.get("proveedor") or "(sin proveedor)").strip() or "(sin proveedor)"
            cat = (c.get("categoria") or "OTROS").strip() or "OTROS"
            mes = (c.get("fecha") or "")[:7] or "(sin fecha)"
            by_supplier[prov] = by_supplier.get(prov, 0) + imp
            by_category[cat] = by_category.get(cat, 0) + imp
            by_month[mes] = by_month.get(mes, 0) + imp

        def top(d):
            return [{"nombre": k, "total": round(v, 2)} for k, v in sorted(d.items(), key=lambda x: -x[1])]

        return {
            "bySupplier": top(by_supplier),
            "byCategory": top(by_category),
            "byMonth": [{"mes": k, "total": round(v, 2)} for k, v in sorted(by_month.items())],
        }
    except Exception as e:
        logger.error(f"Rentabilidad analytics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# RENTABILIDAD POR LINEAS (ficha por expediente: presupuesto/pedido/factura)
# ----------------------------------------------------------------------------
# Flujo:
#  1) Subir documento de VENTA (presupuesto/pedido/factura) -> IA extrae LINEAS.
#  2) Subir pantallazo(s) de COSTE -> IA empareja el coste con cada linea.
#  3) Margen por linea (venta - coste). Se guarda la ficha + los documentos
#     subidos, que quedan consultables al abrir la ficha.
# Colecciones: sale_fichas (la ficha con sus lineas) y sale_ficha_docs (los
# archivos subidos, en base64, para poder consultarlos despues).
# ============================================================================

_SALE_LINES_PROMPT = """Eres un experto en presupuestos, pedidos y facturas de VENTA de muebles/cocinas y electrodomesticos.
Extrae la cabecera y TODAS las lineas del documento y responde SOLO con JSON valido:
{
  "docType": "presupuesto|pedido|factura",   // deducelo del documento
  "ref": "numero del documento (ej LG26/38) o vacio",
  "cliente": "nombre del cliente",
  "fecha": "YYYY-MM-DD",
  "lineas": [
    {
      "ref": "referencia/codigo del articulo si aparece, si no vacio",
      "concepto": "descripcion de la linea",
      "cantidad": 1,
      "venta": 0   // IMPORTE de VENTA de esa linea (con su descuento aplicado), numero decimal sin simbolo
    }
  ]
}
Incluye tambien las lineas de servicios (montaje, transporte, fabricacion, etc.).
Si una linea no tiene importe, pon venta: 0. Numeros con punto decimal, sin moneda.
"""

_COST_MATCH_PROMPT_HEAD = """Eres un experto en costes de muebles/cocinas. Te doy:
1) Una lista de LINEAS de un documento de venta (cada una con un indice).
2) Una imagen/pantallazo con COSTES (factura de proveedor, lista de precios, portal...).
Lee los costes de la imagen y EMPAREJA cada coste con la linea de venta que le corresponde
(por referencia o por nombre del producto). Responde SOLO con JSON valido:
{
  "asignaciones": [
    { "indice": 0, "coste": 0.0, "confianza": "alta|media|baja" }
  ]
}
Solo incluye las lineas para las que encuentres un coste en la imagen. El "indice" es el
de la lista que te paso. Numeros con punto decimal, sin simbolo de moneda.

LINEAS DE VENTA:
"""


def _ficha_totals(lines):
    venta = sum(float(l.get("venta", 0) or 0) for l in lines)
    coste = sum(float(l.get("coste", 0) or 0) for l in lines)
    margen = venta - coste
    return {
        "venta": round(venta, 2),
        "coste": round(coste, 2),
        "margen": round(margen, 2),
        "margenPct": round((margen / venta * 100) if venta > 0 else 0, 1),
    }


@router.post("/rentabilidad/parse-sale-doc")
async def parse_sale_doc(payload: dict):
    """Lee un documento de venta (presupuesto/pedido/factura) y extrae sus lineas."""
    b64 = (payload or {}).get("fileBase64") or ""
    if not b64:
        raise HTTPException(status_code=400, detail="Falta el archivo (fileBase64)")
    stripped = b64.split(",", 1)[1] if b64.startswith("data:") else b64
    try:
        from services.pdf_utils import is_pdf_base64, pdf_base64_to_text, pdf_base64_to_png_base64
        from services.llm_vision import chat_with_gemini, analyze_image_with_gemini

        parsed = None
        is_pdf = ("pdf" in b64[:40].lower()) or is_pdf_base64(stripped)
        logger.info(f"parse_sale_doc: is_pdf={is_pdf}, b64_len={len(b64)}")
        if is_pdf:
            text = pdf_base64_to_text(stripped) or ""
            logger.info(f"parse_sale_doc: text extracted, len={len(text.strip())}")
            if len(text.strip()) >= 50:
                resp = await chat_with_gemini(
                    prompt=_SALE_LINES_PROMPT + "\n\nTEXTO DEL DOCUMENTO:\n\n" + text[:30000],
                    system_message="Extraes lineas de documentos de venta.",
                )
                logger.info(f"parse_sale_doc: gemini text resp len={len(resp or '')}")
                parsed = _parse_json_loose(_clean_json(resp))
        if parsed is None:
            logger.info("parse_sale_doc: falling back to vision")
            img = stripped
            if is_pdf:
                pages = pdf_base64_to_png_base64(stripped, dpi=150, max_pages=1) or []
                if pages:
                    img = pages[0]
            resp = await analyze_image_with_gemini(
                image_base64=img, prompt=_SALE_LINES_PROMPT,
                session_id=f"saledoc-{uuid.uuid4().hex[:8]}",
            )
            logger.info(f"parse_sale_doc: vision resp len={len(resp or '')}")
            parsed = _parse_json_loose(_clean_json(resp))

        if not parsed or not isinstance(parsed.get("lineas"), list):
            logger.warning(f"parse_sale_doc: parsed={parsed}")
            return {"success": False, "error": "No se pudieron extraer las lineas del documento"}

        lines = []
        for l in parsed.get("lineas", []):
            lines.append({
                "id": f"ln-{uuid.uuid4().hex[:6]}",
                "ref": str(l.get("ref") or ""),
                "concepto": str(l.get("concepto") or ""),
                "cantidad": float(l.get("cantidad") or 1),
                "venta": round(float(l.get("venta") or 0), 2),
                "coste": 0.0,
            })
        logger.info(f"parse_sale_doc: success, {len(lines)} lineas")
        return {
            "success": True,
            "data": {
                "docType": str(parsed.get("docType") or "factura"),
                "ref": str(parsed.get("ref") or ""),
                "cliente": str(parsed.get("cliente") or ""),
                "fecha": str(parsed.get("fecha") or datetime.now(timezone.utc).strftime("%Y-%m-%d")),
                "lines": lines,
            },
        }
    except Exception as e:
        logger.error(f"Parse sale doc error: {e}", exc_info=True)
        return {"success": False, "error": f"Error procesando el documento: {str(e)[:200]}"}


@router.post("/rentabilidad/match-line-costs")
async def match_line_costs(payload: dict):
    """Lee un pantallazo de costes y lo empareja con las lineas de venta dadas."""
    b64 = (payload or {}).get("fileBase64") or ""
    lines = (payload or {}).get("lines") or []
    if not b64:
        raise HTTPException(status_code=400, detail="Falta el archivo (fileBase64)")
    if not lines:
        raise HTTPException(status_code=400, detail="Faltan las lineas de venta")
    stripped = b64.split(",", 1)[1] if b64.startswith("data:") else b64
    try:
        from services.pdf_utils import is_pdf_base64, pdf_base64_to_png_base64
        from services.llm_vision import analyze_image_with_gemini

        # Construir el listado indexado de lineas para el prompt
        listado = "\n".join(
            f"{i}. [{(l.get('ref') or '').strip()}] {(l.get('concepto') or '').strip()}"
            for i, l in enumerate(lines)
        )
        prompt = _COST_MATCH_PROMPT_HEAD + listado

        img = stripped
        if ("pdf" in b64[:40].lower()) or is_pdf_base64(stripped):
            pages = pdf_base64_to_png_base64(stripped, dpi=150, max_pages=1) or []
            if pages:
                img = pages[0]

        resp = await analyze_image_with_gemini(
            image_base64=img, prompt=prompt,
            session_id=f"costmatch-{uuid.uuid4().hex[:8]}",
        )
        parsed = _parse_json_loose(_clean_json(resp)) or {}
        asignaciones = parsed.get("asignaciones") or []

        # Aplicar costes sobre una copia de las lineas
        out_lines = [dict(l) for l in lines]
        applied = 0
        for a in asignaciones:
            try:
                idx = int(a.get("indice"))
            except Exception:
                continue
            if 0 <= idx < len(out_lines):
                out_lines[idx]["coste"] = round(float(a.get("coste") or 0), 2)
                out_lines[idx]["_match"] = a.get("confianza", "media")
                applied += 1

        return {"success": True, "lines": out_lines, "matched": applied,
                "totals": _ficha_totals(out_lines)}
    except Exception as e:
        logger.error(f"Match line costs error: {e}")
        return {"success": False, "error": "No se pudo leer el pantallazo de costes. Intentalo de nuevo."}


# ----------------------------- FICHAS (guardado) -----------------------------

@router.get("/rentabilidad/fichas")
async def list_fichas(userId: Optional[str] = None):
    """Lista las fichas de rentabilidad por lineas (resumen)."""
    try:
        query = {"createdBy": userId} if userId else {}
        fichas = await db.sale_fichas.find(query, {"_id": 0}).sort("createdAt", -1).to_list(2000)
        for f in fichas:
            f["totals"] = _ficha_totals(f.get("lines", []))
            f["numDocs"] = await db.sale_ficha_docs.count_documents({"fichaId": f.get("id")})
        return fichas
    except Exception as e:
        logger.error(f"List fichas error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rentabilidad/fichas/{ficha_id}")
async def get_ficha(ficha_id: str):
    """Detalle de una ficha + metadatos de sus documentos (sin el base64)."""
    f = await db.sale_fichas.find_one({"id": ficha_id}, {"_id": 0})
    if not f:
        raise HTTPException(status_code=404, detail="Ficha no encontrada")
    f["totals"] = _ficha_totals(f.get("lines", []))
    docs = await db.sale_ficha_docs.find(
        {"fichaId": ficha_id}, {"_id": 0, "dataBase64": 0}
    ).sort("uploadedAt", 1).to_list(100)
    f["docs"] = docs
    return f


@router.post("/rentabilidad/fichas")
async def save_ficha(payload: dict):
    """Crea o actualiza una ficha de rentabilidad por lineas."""
    try:
        fid = (payload or {}).get("id") or f"fic-{uuid.uuid4().hex[:8]}"
        lines = payload.get("lines") or []
        norm_lines = []
        for l in lines:
            venta = round(float(l.get("venta") or 0), 2)
            coste = round(float(l.get("coste") or 0), 2)
            norm_lines.append({
                "id": l.get("id") or f"ln-{uuid.uuid4().hex[:6]}",
                "ref": str(l.get("ref") or ""),
                "concepto": str(l.get("concepto") or ""),
                "cantidad": float(l.get("cantidad") or 1),
                "venta": venta,
                "coste": coste,
                "margen": round(venta - coste, 2),
            })
        doc = {
            "id": fid,
            "ref": str(payload.get("ref") or ""),
            "docType": str(payload.get("docType") or "factura"),
            "cliente": str(payload.get("cliente") or ""),
            "fecha": str(payload.get("fecha") or datetime.now(timezone.utc).strftime("%Y-%m-%d")),
            "projectRef": str(payload.get("projectRef") or ""),
            "lines": norm_lines,
            "createdBy": payload.get("createdBy", ""),
            "createdByName": payload.get("createdByName", ""),
            "updatedAt": datetime.now(timezone.utc).isoformat(),
        }
        existing = await db.sale_fichas.find_one({"id": fid}, {"_id": 0, "createdAt": 1})
        doc["createdAt"] = (existing or {}).get("createdAt") or doc["updatedAt"]
        await db.sale_fichas.update_one({"id": fid}, {"$set": doc}, upsert=True)
        doc["totals"] = _ficha_totals(norm_lines)
        return {"success": True, "ficha": doc}
    except Exception as e:
        logger.error(f"Save ficha error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/rentabilidad/fichas/{ficha_id}")
async def delete_ficha(ficha_id: str):
    try:
        await db.sale_fichas.delete_one({"id": ficha_id})
        await db.sale_ficha_docs.delete_many({"fichaId": ficha_id})
        return {"success": True}
    except Exception as e:
        logger.error(f"Delete ficha error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ----------------------------- DOCUMENTOS DE LA FICHA -----------------------------

@router.post("/rentabilidad/fichas/{ficha_id}/docs")
async def add_ficha_doc(ficha_id: str, payload: dict):
    """Guarda un documento (venta o coste) asociado a la ficha para consultarlo luego."""
    b64 = (payload or {}).get("fileBase64") or ""
    if not b64:
        raise HTTPException(status_code=400, detail="Falta el archivo (fileBase64)")
    # Detectar mime del prefijo data: si viene
    mime = "application/octet-stream"
    if b64.startswith("data:"):
        try:
            mime = b64.split(";", 1)[0].split(":", 1)[1] or mime
        except Exception:
            pass
    doc = {
        "id": f"doc-{uuid.uuid4().hex[:8]}",
        "fichaId": ficha_id,
        "kind": str(payload.get("kind") or "venta"),   # 'venta' | 'coste'
        "filename": str(payload.get("filename") or "documento"),
        "mime": mime,
        "dataBase64": b64,
        "uploadedAt": datetime.now(timezone.utc).isoformat(),
    }
    await db.sale_ficha_docs.insert_one(doc)
    return {"success": True, "id": doc["id"], "kind": doc["kind"],
            "filename": doc["filename"], "mime": doc["mime"], "uploadedAt": doc["uploadedAt"]}


@router.get("/rentabilidad/fichas/{ficha_id}/docs/{doc_id}")
async def get_ficha_doc(ficha_id: str, doc_id: str):
    """Devuelve el documento (base64) para consultarlo/descargarlo."""
    d = await db.sale_ficha_docs.find_one({"id": doc_id, "fichaId": ficha_id}, {"_id": 0})
    if not d:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return d


@router.delete("/rentabilidad/fichas/{ficha_id}/docs/{doc_id}")
async def delete_ficha_doc(ficha_id: str, doc_id: str):
    await db.sale_ficha_docs.delete_one({"id": doc_id, "fichaId": ficha_id})
    return {"success": True}


# ============================================================================
# CONVERSIONES:  presupuesto  ->  pedido  ->  factura
# Crean el registro real y actualizan el estado del proyecto/pedido.
# ============================================================================

@router.post("/rentabilidad/presupuesto-to-pedido/{project_id}")
async def presupuesto_to_pedido(project_id: str, request: Request):
    """Convierte un presupuesto (project) en PEDIDO (order). Acepta body JSON opcional
    con {orderSerie, orderNumber} para personalizar el número de pedido."""
    body = {}
    try:
        body = await request.json()
    except Exception:
        pass

    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Presupuesto no encontrado")
    if project.get("orderId"):
        raise HTTPException(status_code=400, detail="Este presupuesto ya tiene un pedido asociado")

    # Número de pedido: serie + número indicados por el usuario, o el del presupuesto
    order_serie = str(body.get("orderSerie") or "").strip()
    order_number = str(body.get("orderNumber") or "").strip()
    if order_serie and order_number:
        pedido_ref = f"{order_serie}/{order_number}"
    elif order_number:
        pedido_ref = order_number
    else:
        pedido_ref = project.get("budgetNumber", "")

    now = datetime.now(timezone.utc)
    items = (project.get("itemsMontada") or []) + (project.get("itemsDespiece") or [])
    order = {
        "id": f"order-{uuid.uuid4().hex[:8]}",
        "budgetNumber": pedido_ref,
        "orderSerie": order_serie,
        "orderNumber": order_number,
        "projectReference": project.get("internalReference", ""),
        "customerName": project.get("customerName", ""),
        "customerAddress": project.get("customerAddress", ""),
        "totalAmount": float(project.get("totalPvp", 0) or 0),
        "items": items,
        "itemsCount": len(items),
        "status": "confirmed",
        "userId": project.get("userId", ""),
        "sourceProjectId": project_id,
        "origin": "rentabilidad",
        "confirmedAt": now.isoformat(),
        "createdAt": now.isoformat(),
        "specifications": {
            "doorColorLow": project.get("doorColorLow", ""),
            "doorColorHigh": project.get("doorColorHigh", ""),
            "doorColorColumns": project.get("doorColorColumns", ""),
            "sideColor": project.get("sideColor", ""),
        },
    }
    await db.orders.insert_one(order)
    await db.projects.update_one(
        {"id": project_id},
        {"$set": {
            "status": "aceptado",
            "orderId": order["id"],
            "orderRef": pedido_ref,
            "acceptedAt": now.isoformat(),
            "updatedAt": now.isoformat(),
        }},
    )
    return {"success": True, "orderId": order["id"], "orderRef": pedido_ref, "message": f"Presupuesto convertido en pedido {pedido_ref}"}


@router.post("/rentabilidad/pedido-to-factura/{project_id}")
async def pedido_to_factura(project_id: str, request: Request):
    """Convierte el PEDIDO de un proyecto en FACTURA. Acepta body JSON opcional
    con {invoiceSerie, invoiceNumber} para personalizar el número de factura."""
    body = {}
    try:
        body = await request.json()
    except Exception:
        pass

    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    if project.get("invoiceId"):
        raise HTTPException(status_code=400, detail="Este pedido ya está facturado")
    if not project.get("orderId"):
        raise HTTPException(status_code=400, detail="Primero pasa el presupuesto a pedido")

    invoice_serie = str(body.get("invoiceSerie") or "").strip()
    invoice_number = str(body.get("invoiceNumber") or "").strip()
    custom_inv_number = None
    if invoice_serie and invoice_number:
        custom_inv_number = f"{invoice_serie}/{invoice_number}"
    elif invoice_number:
        custom_inv_number = invoice_number

    # Asegurar un estado válido para emitir factura
    if project.get("status") not in ["aceptado", "en_fabricacion", "entregado"]:
        await db.projects.update_one({"id": project_id}, {"$set": {"status": "aceptado"}})

    from routes.invoices import create_invoice_from_project
    doc = await create_invoice_from_project(project_id, inv_number_override=custom_inv_number)

    now = datetime.now(timezone.utc)
    await db.projects.update_one(
        {"id": project_id},
        {"$set": {"status": "facturado", "updatedAt": now.isoformat()}},
    )
    if project.get("orderId"):
        await db.orders.update_one(
            {"id": project["orderId"]},
            {"$set": {"status": "facturado", "invoiceId": doc.get("id"),
                      "invoiceNumber": doc.get("invoiceNumber")}},
        )
    return {"success": True, "invoiceId": doc.get("id"),
            "invoiceNumber": doc.get("invoiceNumber"), "message": "Pedido facturado"}


# ============================================================================
# INGRESOS A CUENTA (anticipos del cliente) — localizados por IA de un documento
# Coleccion: ingresos_cuenta  { id, fecha, importe, concepto, metodo, cliente,
#                               projectRef, createdBy, createdByName, createdAt }
# ============================================================================

_INGRESOS_PROMPT = """Eres un experto en documentos de cobro de empresas de
muebles/cocinas. Localiza en el documento TODOS los INGRESOS A CUENTA / ANTICIPOS
/ PAGOS A CUENTA del cliente (señales, entregas a cuenta, transferencias o pagos
parciales recibidos). Responde SOLO con JSON valido:
{
  "cliente": "nombre del cliente si aparece, si no vacio",
  "proyecto": "nº de expediente/presupuesto si aparece (ej EXP-2026-001), si no vacio",
  "ingresos": [
    {"fecha": "YYYY-MM-DD", "importe": 0, "concepto": "descripcion (ej: señal, a cuenta, transferencia)", "metodo": "transferencia|efectivo|tarjeta|otro"}
  ],
  "total": 0
}
Importes en numero con punto decimal, sin simbolo de moneda. 'total' es la suma de
los ingresos a cuenta localizados. Si no encuentras ninguno, devuelve "ingresos": [].
"""


@router.post("/rentabilidad/parse-ingresos")
async def parse_ingresos(payload: dict):
    """Lee un documento (PDF/imagen) y localiza con IA los ingresos a cuenta."""
    b64 = (payload or {}).get("fileBase64") or ""
    if not b64:
        raise HTTPException(status_code=400, detail="Falta el archivo (fileBase64)")
    stripped = b64.split(",", 1)[1] if b64.startswith("data:") else b64
    try:
        from services.pdf_utils import is_pdf_base64, pdf_base64_to_text, pdf_base64_to_png_base64
        from services.llm_vision import chat_with_gemini, analyze_image_with_gemini

        parsed = None
        is_pdf = ("pdf" in b64[:40].lower()) or is_pdf_base64(stripped)
        if is_pdf:
            text = pdf_base64_to_text(stripped) or ""
            if len(text.strip()) >= 50:
                resp = await chat_with_gemini(
                    prompt=_INGRESOS_PROMPT + "\n\nTEXTO DEL DOCUMENTO:\n\n" + text[:30000],
                    system_message="Localizas ingresos a cuenta/anticipos en documentos.",
                    model="gemini-2.5-flash",
                )
                parsed = _parse_json_loose(_clean_json(resp))
        if parsed is None:
            img = stripped
            if is_pdf:
                pages = pdf_base64_to_png_base64(stripped, dpi=150, max_pages=1) or []
                if pages:
                    img = pages[0]
            resp = await analyze_image_with_gemini(
                image_base64=img, prompt=_INGRESOS_PROMPT,
                session_id=f"ingresos-{uuid.uuid4().hex[:8]}", model="gemini-2.5-flash",
            )
            parsed = _parse_json_loose(_clean_json(resp))

        if not parsed:
            return {"success": False, "error": "No se pudieron localizar ingresos a cuenta"}

        ingresos = []
        for it in (parsed.get("ingresos") or []):
            try:
                imp = float(it.get("importe") or 0)
            except Exception:
                imp = 0
            if imp <= 0:
                continue
            ingresos.append({
                "fecha": str(it.get("fecha") or datetime.now(timezone.utc).strftime("%Y-%m-%d")),
                "importe": round(imp, 2),
                "concepto": str(it.get("concepto") or "Ingreso a cuenta"),
                "metodo": str(it.get("metodo") or "otro"),
            })
        return {
            "success": True,
            "data": {
                "cliente": str(parsed.get("cliente") or ""),
                "proyecto": str(parsed.get("proyecto") or ""),
                "ingresos": ingresos,
                "total": round(sum(i["importe"] for i in ingresos), 2),
            },
        }
    except Exception as e:
        logger.error(f"Parse ingresos error: {e}")
        return {"success": False, "error": str(e)}


@router.get("/rentabilidad/ingresos")
async def list_ingresos(userId: Optional[str] = None):
    """Lista los ingresos a cuenta (cada usuario los suyos si se pasa userId)."""
    query = {"createdBy": userId} if userId else {}
    items = await db.ingresos_cuenta.find(query, {"_id": 0}).sort("fecha", -1).to_list(3000)
    total = round(sum(float(i.get("importe", 0) or 0) for i in items), 2)
    return {"items": items, "total": total}


@router.get("/rentabilidad/asignables")
async def list_asignables(userId: Optional[str] = None):
    """Documentos a los que asignar un ingreso a cuenta: PRESUPUESTOS, PEDIDOS y FACTURAS.
    Combina sale_fichas (documentos IA) + projects (presupuestos normales)."""
    q_fichas = {"docType": {"$in": ["presupuesto", "pedido", "factura"]}}
    if userId:
        q_fichas["createdBy"] = userId
    fichas = await db.sale_fichas.find(
        q_fichas, {"_id": 0, "id": 1, "docType": 1, "ref": 1, "cliente": 1}
    ).sort("createdAt", -1).to_list(3000)

    # También incluir presupuestos de la colección projects
    q_proj = {}
    if userId:
        q_proj["userId"] = userId
    projects = await db.projects.find(
        q_proj, {"_id": 0, "id": 1, "budgetNumber": 1, "customerName": 1, "internalReference": 1, "orderRef": 1}
    ).sort("createdAt", -1).to_list(3000)

    presupuestos = []
    for p in projects:
        ref = p.get("orderRef") or p.get("budgetNumber") or p.get("internalReference") or p.get("id")
        presupuestos.append({
            "id": p["id"],
            "docType": "pedido" if p.get("orderRef") else "presupuesto",
            "ref": ref,
            "cliente": p.get("customerName", ""),
        })

    # Combinar: fichas primero, luego proyectos (deduplicar por ref)
    seen_refs = {f.get("ref") for f in fichas if f.get("ref")}
    for p in presupuestos:
        if p.get("ref") not in seen_refs:
            fichas.append(p)
            seen_refs.add(p.get("ref"))

    return fichas


@router.post("/rentabilidad/ingresos")
async def create_ingreso(payload: dict):
    """Registra un ingreso a cuenta. SIEMPRE se asigna a un pedido o factura y se
    archiva el documento del que se detectó."""
    try:
        imp = float((payload or {}).get("importe") or 0)
    except Exception:
        imp = 0
    if imp <= 0:
        raise HTTPException(status_code=400, detail="Importe inválido")

    target_id = str((payload or {}).get("targetId") or "")
    if not target_id:
        raise HTTPException(status_code=400, detail="El ingreso debe asignarse a un pedido o una factura")

    now = datetime.now(timezone.utc)
    iid = f"ing-{uuid.uuid4().hex[:8]}"

    # Archivar el documento (si viene en base64) en su propia colección
    doc_id = ""
    doc_b64 = (payload or {}).get("docBase64") or ""
    if doc_b64:
        stripped = doc_b64.split(",", 1)[1] if doc_b64.startswith("data:") else doc_b64
        doc_id = f"ingdoc-{uuid.uuid4().hex[:8]}"
        await db.ingreso_docs.insert_one({
            "id": doc_id,
            "ingresoId": iid,
            "dataBase64": stripped,
            "mime": str(payload.get("docMime") or "application/octet-stream"),
            "filename": str(payload.get("docName") or "documento"),
            "createdBy": payload.get("createdBy", ""),
            "createdAt": now.isoformat(),
        })

    doc = {
        "id": iid,
        "fecha": str(payload.get("fecha") or now.strftime("%Y-%m-%d")),
        "importe": round(imp, 2),
        "concepto": str(payload.get("concepto") or "Ingreso a cuenta"),
        "metodo": str(payload.get("metodo") or "otro"),
        "cliente": str(payload.get("cliente") or ""),
        "projectRef": str(payload.get("projectRef") or payload.get("proyecto") or ""),
        "targetType": str(payload.get("targetType") or ""),   # pedido | factura
        "targetId": target_id,                                  # id de la ficha
        "targetRef": str(payload.get("targetRef") or ""),
        "docId": doc_id,
        "docName": str(payload.get("docName") or ""),
        "createdBy": payload.get("createdBy", ""),
        "createdByName": payload.get("createdByName", ""),
        "createdAt": now.isoformat(),
    }
    await db.ingresos_cuenta.insert_one(doc)
    doc.pop("_id", None)
    return {"success": True, "ingreso": doc}


@router.get("/rentabilidad/ingresos/doc/{doc_id}")
async def get_ingreso_doc(doc_id: str):
    """Devuelve el documento archivado de un ingreso (para consultarlo)."""
    d = await db.ingreso_docs.find_one({"id": doc_id}, {"_id": 0})
    if not d:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return d


@router.delete("/rentabilidad/ingresos/{ingreso_id}")
async def delete_ingreso(ingreso_id: str):
    await db.ingresos_cuenta.delete_one({"id": ingreso_id})
    await db.ingreso_docs.delete_many({"ingresoId": ingreso_id})
    return {"success": True}
