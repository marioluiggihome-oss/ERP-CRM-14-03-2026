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
from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
from typing import Optional
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
    """Cuenta de resultados por proyecto: Venta (presupuesto) - Coste = Margen.

    Une cada proyecto con sus costes (por budgetNumber == projectRef).
    """
    try:
        query = {}
        if userId:
            query["userId"] = userId
        projects = await db.projects.find(
            query,
            {"_id": 0, "id": 1, "budgetNumber": 1, "customerName": 1, "clientCode": 1,
             "totalPvp": 1, "totalConIVA": 1, "createdAt": 1, "userId": 1, "status": 1}
        ).sort("createdAt", -1).to_list(3000)

        # Agregar costes por projectRef (== budgetNumber)
        costs_agg = {}
        async for c in db.project_costs.find({}, {"_id": 0, "projectRef": 1, "importe": 1}):
            ref = c.get("projectRef")
            costs_agg[ref] = costs_agg.get(ref, 0) + float(c.get("importe", 0) or 0)

        rows = []
        tot_venta = tot_coste = 0.0
        for p in projects:
            ref = p.get("budgetNumber") or ""
            venta = float(p.get("totalPvp", 0) or 0)
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
                "venta": round(venta, 2),
                "coste": round(coste, 2),
                "margen": round(margen, 2),
                "margenPct": round(margen_pct, 1),
            })

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


@router.post("/rentabilidad/parse-invoice")
async def parse_invoice(payload: dict):
    """Lee una factura de proveedor (PDF/imagen en base64) con IA y devuelve los
    datos extraidos (proveedor, importe, concepto, fecha, categoria, proyecto)
    para que el usuario los revise antes de registrar el coste."""
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
                    prompt=_INVOICE_PROMPT + "\n\nTEXTO DE LA FACTURA:\n\n" + text[:30000],
                    system_message="Extraes datos de facturas de proveedor.",
                    model="gemini-2.0-flash",
                )
                parsed = _parse_json_loose(_clean_json(resp))
        if parsed is None:
            # Escaneada o imagen: usar vision sobre la primera pagina/imagen.
            img = stripped
            if is_pdf:
                pages = pdf_base64_to_png_base64(stripped, dpi=150, max_pages=1) or []
                if pages:
                    img = pages[0]
            resp = await analyze_image_with_gemini(
                image_base64=img, prompt=_INVOICE_PROMPT,
                session_id=f"invoice-{uuid.uuid4().hex[:8]}", model="gemini-2.0-flash",
            )
            parsed = _parse_json_loose(_clean_json(resp))

        if not parsed:
            return {"success": False, "error": "No se pudieron extraer datos de la factura"}

        return {
            "success": True,
            "data": {
                "proveedor": str(parsed.get("proveedor") or ""),
                "fecha": str(parsed.get("fecha") or datetime.now(timezone.utc).strftime("%Y-%m-%d")),
                "importe": float(parsed.get("importe") or parsed.get("base") or 0),
                "concepto": str(parsed.get("concepto") or ""),
                "categoria": str(parsed.get("categoria") or "OTROS").upper(),
                "proyecto": str(parsed.get("proyecto") or ""),
            },
        }
    except Exception as e:
        logger.error(f"Parse invoice error: {e}")
        return {"success": False, "error": str(e)}
