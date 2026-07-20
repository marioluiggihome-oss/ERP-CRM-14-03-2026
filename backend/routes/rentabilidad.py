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
from fastapi import APIRouter, HTTPException, Request, Depends
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import uuid
import logging
import os
import json
import re
from motor.motor_asyncio import AsyncIOMotorClient

logger = logging.getLogger(__name__)

# Seguridad: todo el módulo de Rentabilidad exige token válido y acceso al módulo
# (rol elevado o permiso canAccessRentabilidad), igual que la UI. Cierra el acceso
# anónimo a costes, ingresos, fichas, márgenes y documentos adjuntos.
try:
    from services.jwt_service import require_auth, ADMIN_ROLE_FLAGS

    async def require_rentabilidad(user: dict = Depends(require_auth)):
        if any(user.get(f) for f in ADMIN_ROLE_FLAGS) or user.get("canAccessRentabilidad"):
            return user
        raise HTTPException(status_code=403, detail="Sin acceso al módulo de Rentabilidad")
    _RENTA_DEPS = [Depends(require_rentabilidad)]
except Exception:  # pragma: no cover - fallback si no hay jwt_service
    ADMIN_ROLE_FLAGS = ()

    async def require_rentabilidad():
        return {}
    _RENTA_DEPS = []

router = APIRouter(tags=["rentabilidad"], dependencies=_RENTA_DEPS)

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'luiggi_home')
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

MAX_DOC_SIZE_MB = 15


def _is_elevated(user: dict) -> bool:
    return any((user or {}).get(f) for f in ADMIN_ROLE_FLAGS)


def _check_doc_size(b64: str, max_mb: int = MAX_DOC_SIZE_MB):
    """Rechaza documentos adjuntos (base64) por encima del limite, para no
    disparar el tamano de Mongo con lotes grandes de facturas escaneadas."""
    if not b64:
        return
    stripped = b64.split(",", 1)[1] if b64.startswith("data:") else b64
    size_mb = (len(stripped) * 3 / 4) / (1024 * 1024)  # tamano real aprox. del binario
    if size_mb > max_mb:
        raise HTTPException(
            status_code=413,
            detail=f"El documento pesa {size_mb:.1f}MB; el maximo permitido es {max_mb}MB",
        )


async def _log_deletion(entity: str, entity_id: str, before: Optional[dict], user: dict):
    """Auditoria minima de borrados: quien borro que y una copia del documento
    para poder recuperarlo si hace falta."""
    try:
        await db.rentabilidad_audit_log.insert_one({
            "id": f"aud-{uuid.uuid4().hex[:8]}",
            "action": "delete",
            "entity": entity,
            "entityId": entity_id,
            "before": before,
            "userId": (user or {}).get("id", ""),
            "userName": (user or {}).get("username", ""),
            "createdAt": datetime.now(timezone.utc).isoformat(),
        })
    except Exception as e:
        logger.error(f"No se pudo registrar auditoria de borrado ({entity}/{entity_id}): {e}")


# ----------------------------- COSTES POR PROYECTO -----------------------------

@router.get("/rentabilidad/articulo")
async def buscar_articulo_por_codigo(codigo: str = ""):
    """Busca un artículo por código exacto o parcial en la colección de productos.
    Devuelve código y nombre para rellenar el formulario de coste por código."""
    import re as _re
    try:
        if not codigo or len(codigo.strip()) < 2:
            return {"found": False, "results": []}
        q = codigo.strip()
        escaped = _re.escape(q)
        # Primero busca coincidencia exacta de código
        exact = await db.products.find_one(
            {"code": {"$regex": f"^{escaped}$", "$options": "i"}},
            {"_id": 0, "code": 1, "name": 1, "description": 1, "pvp": 1, "coste": 1}
        )
        if exact:
            return {
                "found": True,
                "results": [{
                    "code": exact.get("code", ""),
                    "name": exact.get("name") or exact.get("description") or "",
                    "pvp": float(exact.get("pvp", 0) or 0),
                    "coste": float(exact.get("coste", 0) or 0),
                }]
            }
        # Si no hay exacta, busca parcial (hasta 10 resultados)
        cursor = db.products.find(
            {"$or": [
                {"code": {"$regex": escaped, "$options": "i"}},
                {"name": {"$regex": escaped, "$options": "i"}},
            ]},
            {"_id": 0, "code": 1, "name": 1, "description": 1, "pvp": 1, "coste": 1}
        ).limit(10)
        results = await cursor.to_list(10)
        return {
            "found": len(results) > 0,
            "results": [{
                "code": r.get("code", ""),
                "name": r.get("name") or r.get("description") or "",
                "pvp": float(r.get("pvp", 0) or 0),
                "coste": float(r.get("coste", 0) or 0),
            } for r in results]
        }
    except Exception as e:
        logger.error(f"Buscar articulo error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/project-costs")
async def add_project_cost(cost: dict):
    """Registrar un coste/gasto asociado a un proyecto (por su referencia)."""
    try:
        ref = (cost.get("projectRef") or "").strip()
        if not ref:
            raise HTTPException(status_code=400, detail="Falta projectRef")
        ref = await _resolve_project_cost_ref(ref)
        _check_doc_size(cost.get("docBase64") or "")
        raw_categoria = str(cost.get("categoria") or "OTROS")
        categoria = _invoice_category(raw_categoria)
        doc = {
            "id": f"cost-{uuid.uuid4().hex[:8]}",
            "projectRef": ref,
            "proveedor": cost.get("proveedor", ""),
            "concepto": cost.get("concepto", ""),
            "categoria": categoria,
            # Si la IA/usuario mando una categoria que no es de las validas, se
            # normaliza a OTROS pero se conserva lo detectado para no maquillarlo.
            "categoriaOriginal": raw_categoria if categoria == "OTROS" and raw_categoria.strip().upper() != "OTROS" else "",
            "importe": float(cost.get("importe", 0) or 0),
            "fecha": cost.get("fecha", datetime.now(timezone.utc).strftime("%Y-%m-%d")),
            "source": cost.get("source", "manual"),
            "compraId": cost.get("compraId", ""),      # vínculo con pedido de compra (cascos)
            "expediente": cost.get("expediente", ""),  # expediente que relaciona venta y compra
            "docId": "",
            "createdAt": datetime.now(timezone.utc).isoformat(),
        }
        # Documento adjunto opcional (PDF/imagen de la factura del proveedor)
        b64 = cost.get("docBase64") or ""
        if b64:
            stripped = b64.split(",", 1)[1] if b64.startswith("data:") else b64
            cdoc_id = f"costdoc-{uuid.uuid4().hex[:8]}"
            await db.project_cost_docs.insert_one({
                "id": cdoc_id,
                "costId": doc["id"],
                "dataBase64": stripped,
                "mime": str(cost.get("docMime") or "application/octet-stream"),
                "filename": str(cost.get("docName") or "documento"),
                "createdAt": datetime.now(timezone.utc).isoformat(),
            })
            doc["docId"] = cdoc_id
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


@router.get("/project-costs/doc/{doc_id}")
async def get_project_cost_doc(doc_id: str):
    """Devuelve el documento adjunto de un coste (factura del proveedor)."""
    d = await db.project_cost_docs.find_one({"id": doc_id}, {"_id": 0})
    if not d:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return d


@router.delete("/project-costs/{cost_id}")
async def delete_project_cost(cost_id: str, user: dict = Depends(require_rentabilidad)):
    try:
        existing = await db.project_costs.find_one({"id": cost_id}, {"_id": 0})
        await db.project_cost_docs.delete_many({"costId": cost_id})
        res = await db.project_costs.delete_one({"id": cost_id})
        if existing:
            await _log_deletion("project_cost", cost_id, existing, user)
        return {"success": True, "deleted": res.deleted_count}
    except Exception as e:
        logger.error(f"Delete project cost error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ----------------------------- RENTABILIDAD -----------------------------

def _enrich_row(row, ref, costs_by_cat, cobrado_by_target, alerta_pct, order=None):
    """Anade al row de rentabilidad las metricas de controller: cobrado/pendiente
    de cobro (cruce con ingresos a cuenta), alerta de margen bajo, desglose de
    coste por categoria, y desviacion venta pedido vs venta facturada real."""
    cobrado = 0.0
    for tid in [row.get("projectId"), row.get("orderId"), row.get("albaranId"), row.get("invoiceId")]:
        if tid and tid in cobrado_by_target:
            cobrado += cobrado_by_target[tid]
    row["cobrado"] = round(cobrado, 2)
    row["pendienteCobro"] = round(row["venta"] - cobrado, 2)
    row["alertaMargen"] = bool(row["venta"] > 0 and row["margenPct"] < alerta_pct)
    row["costesPorCategoria"] = {k: round(v, 2) for k, v in costs_by_cat.get(ref, {}).items()}
    if order:
        venta_pedido = float(order.get("totalAmount", 0) or 0)
        row["ventaPedido"] = round(venta_pedido, 2)
        row["desviacionVenta"] = round(row["venta"] - venta_pedido, 2)
    return row


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
             "orderId": 1, "orderRef": 1, "albaranId": 1, "albaranRef": 1,
             "invoiceId": 1, "invoiceNumber": 1, "internalReference": 1}
        ).sort("createdAt", -1).to_list(3000)

        # Agregar costes por projectRef (== budgetNumber u otra ref ya normalizada),
        # tanto el total como el desglose por categoria (MOBILIARIO, TRANSPORTE...).
        costs_agg = {}
        costs_by_cat = {}
        async for c in db.project_costs.find({}, {"_id": 0, "projectRef": 1, "importe": 1, "categoria": 1}):
            ref = c.get("projectRef")
            importe = float(c.get("importe", 0) or 0)
            cat = str(c.get("categoria") or "OTROS").upper()
            costs_agg[ref] = costs_agg.get(ref, 0) + importe
            costs_by_cat.setdefault(ref, {})
            costs_by_cat[ref][cat] = costs_by_cat[ref].get(cat, 0) + importe

        # Ingresos a cuenta (cobros) ya registrados, para poder calcular el
        # pendiente de cobro por documento (venta facturada - cobrado a cuenta).
        cobrado_by_target = {}
        async for ing in db.ingresos_cuenta.find({}, {"_id": 0, "targetId": 1, "ingresos": 1, "importe": 1}):
            tid = ing.get("targetId")
            if not tid:
                continue
            monto = float(ing.get("importe", 0) or 0)
            if not monto and isinstance(ing.get("ingresos"), list):
                monto = sum(float(i.get("importe", 0) or 0) for i in ing["ingresos"])
            cobrado_by_target[tid] = cobrado_by_target.get(tid, 0) + monto

        MARGEN_ALERTA_PCT = 15.0

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
                "albaranId": p.get("albaranId", ""),
                "albaranRef": p.get("albaranRef", ""),
                "invoiceId": p.get("invoiceId", ""),
                "invoiceNumber": p.get("invoiceNumber", ""),
                "internalReference": p.get("internalReference", ""),
                "origen": "presupuesto",
                "venta": round(venta, 2),
                "coste": round(coste, 2),
                "margen": round(margen, 2),
                "margenPct": round(margen_pct, 1),
            })
            order_for_dev = orders_by_id.get(order_id) if order_id else None
            _enrich_row(rows[-1], ref, costs_by_cat, cobrado_by_target, MARGEN_ALERTA_PCT, order_for_dev)

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
            _enrich_row(rows[-1], ref, costs_by_cat, cobrado_by_target, MARGEN_ALERTA_PCT, None)

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
            _enrich_row(rows[-1], ref, costs_by_cat, cobrado_by_target, MARGEN_ALERTA_PCT, None)

        rows.sort(key=lambda r: r.get("fecha") or "", reverse=True)

        tot_margen = tot_venta - tot_coste
        tot_cobrado = sum(r.get("cobrado", 0) for r in rows)
        tot_pendiente = sum(r.get("pendienteCobro", 0) for r in rows)
        alertas = [r for r in rows if r.get("alertaMargen")]
        # Pipeline: documentos aun no facturados (margen esperado de lo que esta en curso).
        pipeline_rows = [r for r in rows if not r.get("invoiceId")]
        pipeline_venta = sum(r.get("venta", 0) for r in pipeline_rows)
        pipeline_margen = sum(r.get("margen", 0) for r in pipeline_rows)

        return {
            "rows": rows,
            "totales": {
                "venta": round(tot_venta, 2),
                "coste": round(tot_coste, 2),
                "margen": round(tot_margen, 2),
                "margenPct": round((tot_margen / tot_venta * 100) if tot_venta > 0 else 0, 1),
                "proyectos": len(rows),
                "cobrado": round(tot_cobrado, 2),
                "pendienteCobro": round(tot_pendiente, 2),
                "alertasMargen": len(alertas),
                "pipeline": {
                    "documentos": len(pipeline_rows),
                    "venta": round(pipeline_venta, 2),
                    "margen": round(pipeline_margen, 2),
                },
            },
        }
    except Exception as e:
        logger.error(f"Get rentabilidad error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rentabilidad/por-periodo")
async def rentabilidad_por_periodo(userId: Optional[str] = None):
    """Agrupa la rentabilidad por mes (YYYY-MM) para ver la evolucion de venta,
    coste y margen en el tiempo, en vez de solo el acumulado total."""
    data = await get_rentabilidad(userId=userId)
    meses = {}
    for r in data["rows"]:
        fecha = str(r.get("fecha") or "")[:7]
        if not fecha:
            fecha = "sin-fecha"
        m = meses.setdefault(fecha, {"periodo": fecha, "venta": 0.0, "coste": 0.0, "margen": 0.0, "documentos": 0})
        m["venta"] += r.get("venta", 0)
        m["coste"] += r.get("coste", 0)
        m["margen"] += r.get("margen", 0)
        m["documentos"] += 1
    out = sorted(meses.values(), key=lambda m: m["periodo"])
    for m in out:
        m["venta"] = round(m["venta"], 2)
        m["coste"] = round(m["coste"], 2)
        m["margen"] = round(m["margen"], 2)
        m["margenPct"] = round((m["margen"] / m["venta"] * 100) if m["venta"] > 0 else 0, 1)
    return {"periodos": out}


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


_INBOX_PROMPT = (
    "Eres el clasificador de la bandeja de entrada de un ERP de cocinas. Analiza el documento y decide QUÉ ES y DÓNDE colocarlo.\n"
    "Tipos posibles (campo kind):\n"
    "- 'venta': presupuesto, pedido, albarán o factura DE VENTA (emitida al cliente). Indica docType: presupuesto|pedido|albaran|factura.\n"
    "- 'coste': factura o ticket DE PROVEEDOR (compra/gasto imputable a un proyecto).\n"
    "- 'ingreso': justificante de pago/anticipo del cliente (ingreso a cuenta, transferencia recibida).\n"
    "Extrae: cliente (si venta/ingreso), proveedor (si coste), ref/numero, fecha (YYYY-MM-DD), total (número), "
    "projectRef (referencia de obra/proyecto si aparece), categoria (solo coste: MOBILIARIO|ELECTRODOMESTICOS|ENCIMERA|TRANSPORTE|MONTAJE|SUBCONTRATA|OTROS), "
    "y lines (lista de {concepto, importe}). Añade un 'resumen' de una frase.\n"
    "Devuelve SOLO un bloque JSON: {\"kind\":\"\",\"docType\":\"\",\"cliente\":\"\",\"proveedor\":\"\",\"ref\":\"\",\"fecha\":\"\",\"total\":0,\"projectRef\":\"\",\"categoria\":\"\",\"lines\":[],\"resumen\":\"\"}."
)


@router.post("/rentabilidad/inbox-classify")
async def inbox_classify(payload: dict):
    """Bandeja IA: clasifica un documento arrastrado (venta/coste/ingreso), extrae
    sus datos y propone dónde colocarlo, para que el usuario lo autorice."""
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
        if is_pdf:
            text = pdf_base64_to_text(stripped) or ""
            if len(text.strip()) >= 50:
                resp = await chat_with_gemini(prompt=_INBOX_PROMPT + "\n\nTEXTO:\n\n" + text[:30000],
                                              system_message="Clasificas documentos de un ERP.", model="gemini-2.5-flash")
                parsed = _parse_json_loose(_clean_json(resp))
        if parsed is None:
            img = stripped
            image_mime = mime if mime and mime.startswith("image/") else "image/jpeg"
            if is_pdf:
                pages = pdf_base64_to_png_base64(stripped, dpi=180, max_pages=1) or []
                if pages:
                    img = pages[0]; image_mime = "image/png"
            resp = await analyze_image_with_gemini(image_base64=img, prompt=_INBOX_PROMPT,
                                                   session_id=f"inbox-{uuid.uuid4().hex[:8]}", model="gemini-2.5-flash", image_mime=image_mime)
            parsed = _parse_json_loose(_clean_json(resp))
        if not parsed:
            return {"success": False, "error": "No se pudo clasificar el documento"}
        kind = str(parsed.get("kind") or "").lower()
        if kind not in ("venta", "coste", "ingreso"):
            kind = "coste" if parsed.get("proveedor") else "venta"
            parsed["kind"] = kind
        return {"success": True, "proposal": parsed}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"inbox_classify error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
  "docType": "presupuesto|pedido|albaran|factura",   // deducelo del documento (albaran = nota de entrega/entrega de mercancia)
  "ref": "numero del documento (ej LG26/38) o vacio",
  "cliente": "nombre del cliente",
  "clienteCodigo": "numero o codigo de cliente si aparece impreso en el documento (ej Cliente: 12345), si no aparece deja vacio",
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


async def _cobrado_por_ficha_map():
    """Suma ingresos_cuenta por ficha: por targetId (vinculo directo) y tambien
    por referencia normalizada (fallback si el ingreso se registro contra la
    ref y no contra el id de la ficha)."""
    m = {}
    async for ing in db.ingresos_cuenta.find({}, {"_id": 0, "targetId": 1, "targetRef": 1, "importe": 1}):
        monto = float(ing.get("importe", 0) or 0)
        tid = ing.get("targetId")
        if tid:
            m[tid] = m.get(tid, 0.0) + monto
        tref = _normalize_ref(ing.get("targetRef") or "")
        if tref:
            key = f"ref:{tref}"
            m[key] = m.get(key, 0.0) + monto
    return m


async def _costes_proyecto_map():
    """Total de project_costs (costes de Rentabilidad > Por proyecto) por
    referencia normalizada, para poder avisar en la ficha 'Por lineas' de que
    ya hay coste cargado aunque las lineas de la ficha no lo reflejen."""
    m = {}
    async for c in db.project_costs.find({}, {"_id": 0, "projectRef": 1, "importe": 1}):
        ref = _normalize_ref(c.get("projectRef"))
        if not ref:
            continue
        m[ref] = m.get(ref, 0.0) + float(c.get("importe", 0) or 0)
    return m


def _apply_ficha_extras(f, cobrado_map, costes_map):
    """Anade a la ficha: cobrado/pendienteCobro (cruce con ingresos a cuenta) y
    costesProyecto (coste ya registrado en Rentabilidad para ese projectRef)."""
    tt = f.get("totals") or _ficha_totals(f.get("lines", []))
    cobrado = cobrado_map.get(f.get("id")) or cobrado_map.get(f"ref:{_normalize_ref(f.get('ref'))}") or 0.0
    f["cobrado"] = round(cobrado, 2)
    f["pendienteCobro"] = round((tt.get("venta") or 0) - cobrado, 2)
    proj_ref = _normalize_ref(f.get("projectRef") or f.get("ref"))
    f["costesProyecto"] = round(costes_map.get(proj_ref, 0.0), 2)
    return f


@router.post("/rentabilidad/split-pdf-pages")
async def split_pdf_pages(payload: dict):
    """Divide un PDF de varias paginas en un PDF por pagina. Pensado para cuando
    llega un archivo combinado con muchas facturas dentro (una por pagina, como
    en una exportacion/historico): sin esto, parse-sale-doc intentaba leer las
    N facturas como si fueran un solo documento y fallaba."""
    b64 = (payload or {}).get("fileBase64") or ""
    if not b64:
        raise HTTPException(status_code=400, detail="Falta el archivo (fileBase64)")
    stripped = b64.split(",", 1)[1] if b64.startswith("data:") else b64
    try:
        from services.pdf_utils import is_pdf_base64, split_pdf_to_pages_base64
        if not is_pdf_base64(stripped):
            return {"success": True, "pages": [b64]}
        pages = split_pdf_to_pages_base64(stripped)
        if not pages:
            return {"success": True, "pages": [b64]}
        return {"success": True, "pages": [f"data:application/pdf;base64,{p}" for p in pages]}
    except Exception as e:
        logger.error(f"split_pdf_pages error: {e}")
        return {"success": False, "error": str(e), "pages": [b64]}


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
                "clienteCodigo": str(parsed.get("clienteCodigo") or ""),
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


# ------------------- CATALOGO DE COSTES POR ARTICULO (coste medio ponderado) -------------------
# Coste unitario por articulo calculado como Coste_total / Cantidad del informe de
# ventas del proveedor (coste medio ponderado). El catalogo vive en la coleccion
# `article_costs` de MongoDB (editable y auditable desde el master); la primera vez
# se SIEMBRA automaticamente desde el CSV validado backend/data/costes_unitarios.csv.
# Permite alimentar el coste de las lineas de una ficha casando por la referencia
# del articulo (linea.ref == codigo).
import csv as _csv

_ARTICLE_COSTS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "costes_unitarios.csv")


def _read_costs_csv() -> List[Dict[str, Any]]:
    """Lee el CSV validado y devuelve la lista de articulos con coste unitario."""
    rows: List[Dict[str, Any]] = []
    try:
        with open(_ARTICLE_COSTS_PATH, encoding="utf-8") as fh:
            for r in _csv.DictReader(fh, delimiter=";"):
                cu = (r.get("coste_unitario") or "").strip()
                cod = (r.get("codigo") or "").strip()
                if not cod:
                    continue
                try:
                    coste_unit = float(cu) if cu else None
                except Exception:
                    coste_unit = None
                def _f(x):
                    try:
                        return float(x)
                    except Exception:
                        return None
                rows.append({
                    "codigo": cod,
                    "codigoNorm": _normalize_ref(cod),
                    "nombre": (r.get("nombre") or "").strip(),
                    "cantidad": _f(r.get("cantidad")),
                    "costeTotal": _f(r.get("coste_total")),
                    "costeUnitario": round(coste_unit, 4) if coste_unit is not None else None,
                    "revisar": (r.get("revisar") or "").strip(),
                    "source": "csv",
                })
    except FileNotFoundError:
        logger.warning("costes_unitarios.csv no encontrado en %s", _ARTICLE_COSTS_PATH)
    return rows


async def _seed_article_costs_if_empty():
    """Siembra la coleccion article_costs desde el CSV solo si esta vacia."""
    try:
        if await db.article_costs.estimated_document_count() > 0:
            return
        rows = _read_costs_csv()
        if not rows:
            return
        now = datetime.now(timezone.utc).isoformat()
        docs = []
        for r in rows:
            if not r.get("codigoNorm"):
                continue
            docs.append({**r, "updatedAt": now, "updatedBy": "seed"})
        if docs:
            await db.article_costs.insert_many(docs)
            logger.info("article_costs sembrado con %d articulos desde CSV", len(docs))
    except Exception as e:
        logger.error("No se pudo sembrar article_costs: %s", e)


async def _article_costs_map() -> Dict[str, Any]:
    """Devuelve {codigoNorm: articulo} con coste unitario desde MongoDB."""
    await _seed_article_costs_if_empty()
    by_code: Dict[str, Any] = {}
    async for a in db.article_costs.find({"costeUnitario": {"$ne": None}}, {"_id": 0}):
        norm = a.get("codigoNorm") or _normalize_ref(a.get("codigo"))
        if norm:
            by_code[norm] = a
    return by_code


@router.get("/rentabilidad/article-costs")
async def article_costs(q: Optional[str] = None, limit: int = 1000, soloRevisar: bool = False):
    """Lista/busca el catalogo de costes unitarios por articulo (desde MongoDB)."""
    await _seed_article_costs_if_empty()
    query: Dict[str, Any] = {}
    if soloRevisar:
        query["revisar"] = {"$nin": ["", None]}
    if q:
        nq = re.escape(q.strip())
        query["$or"] = [
            {"codigo": {"$regex": nq, "$options": "i"}},
            {"nombre": {"$regex": nq, "$options": "i"}},
        ]
    total = await db.article_costs.count_documents(query)
    items = await db.article_costs.find(query, {"_id": 0}).sort("codigo", 1).to_list(max(1, min(limit, 5000)))
    return {"total": total, "items": items}


@router.post("/rentabilidad/article-costs")
async def upsert_article_cost(payload: dict, user: dict = Depends(require_rentabilidad)):
    """Crea o modifica el coste de un articulo (master). Guarda auditoria del cambio."""
    cod = (payload or {}).get("codigo", "").strip()
    if not cod:
        raise HTTPException(status_code=400, detail="Falta el codigo del articulo")
    norm = _normalize_ref(cod)
    prev = await db.article_costs.find_one({"codigoNorm": norm}, {"_id": 0})
    def _f(x, d=None):
        try:
            return float(x)
        except Exception:
            return d
    coste_unit = _f(payload.get("costeUnitario"))
    doc = {
        "codigo": cod,
        "codigoNorm": norm,
        "nombre": str(payload.get("nombre") or (prev or {}).get("nombre") or "").strip(),
        "cantidad": _f(payload.get("cantidad"), (prev or {}).get("cantidad")),
        "costeTotal": _f(payload.get("costeTotal"), (prev or {}).get("costeTotal")),
        "costeUnitario": round(coste_unit, 4) if coste_unit is not None else (prev or {}).get("costeUnitario"),
        "revisar": str(payload.get("revisar", (prev or {}).get("revisar") or "")).strip(),
        "source": "manual",
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "updatedBy": (user or {}).get("username", ""),
    }
    await db.article_costs.update_one({"codigoNorm": norm}, {"$set": doc}, upsert=True)
    # Auditoria: registra el antes/despues de cada cambio de coste.
    try:
        await db.article_costs_audit.insert_one({
            "id": f"acaud-{uuid.uuid4().hex[:8]}",
            "codigo": cod, "codigoNorm": norm,
            "before": prev, "after": doc,
            "userId": (user or {}).get("id", ""),
            "userName": (user or {}).get("username", ""),
            "createdAt": datetime.now(timezone.utc).isoformat(),
        })
    except Exception as e:
        logger.error("No se pudo auditar cambio de coste %s: %s", cod, e)
    return {"success": True, "article": doc, "created": prev is None}


@router.delete("/rentabilidad/article-costs/{codigo}")
async def delete_article_cost(codigo: str, user: dict = Depends(require_rentabilidad)):
    """Elimina un articulo del catalogo de costes (master)."""
    norm = _normalize_ref(codigo)
    prev = await db.article_costs.find_one({"codigoNorm": norm}, {"_id": 0})
    res = await db.article_costs.delete_one({"codigoNorm": norm})
    if prev:
        await _log_deletion("article_cost", codigo, prev, user)
    return {"success": True, "deleted": res.deleted_count}


@router.get("/rentabilidad/article-costs/audit")
async def article_costs_audit(codigo: Optional[str] = None, limit: int = 100, user: dict = Depends(require_rentabilidad)):
    """Historial de cambios del catalogo de costes (auditoria)."""
    query = {"codigoNorm": _normalize_ref(codigo)} if codigo else {}
    items = await db.article_costs_audit.find(query, {"_id": 0}).sort("createdAt", -1).to_list(max(1, min(limit, 1000)))
    return {"total": len(items), "items": items}


@router.post("/rentabilidad/article-costs/reseed")
async def reseed_article_costs(payload: Optional[dict] = None, user: dict = Depends(require_rentabilidad)):
    """Recarga el catalogo desde el CSV validado. Con replace=true BORRA y vuelve a
    sembrar (pierde ediciones manuales); si no, hace upsert respetando lo existente."""
    replace = bool((payload or {}).get("replace"))
    rows = _read_costs_csv()
    if not rows:
        raise HTTPException(status_code=404, detail="No se encontro el CSV de costes")
    now = datetime.now(timezone.utc).isoformat()
    uname = (user or {}).get("username", "")
    if replace:
        await db.article_costs.delete_many({})
        docs = [{**r, "updatedAt": now, "updatedBy": uname or "reseed"} for r in rows if r.get("codigoNorm")]
        if docs:
            await db.article_costs.insert_many(docs)
        return {"success": True, "mode": "replace", "count": len(docs)}
    upserts = 0
    for r in rows:
        if not r.get("codigoNorm"):
            continue
        await db.article_costs.update_one(
            {"codigoNorm": r["codigoNorm"]},
            {"$set": {**r, "updatedAt": now, "updatedBy": uname or "reseed"}},
            upsert=True,
        )
        upserts += 1
    return {"success": True, "mode": "upsert", "count": upserts}


@router.post("/rentabilidad/apply-article-costs")
async def apply_article_costs(payload: dict):
    """Alimenta el coste de cada linea a partir del coste unitario (coste medio
    ponderado) del articulo, casando por la referencia de la linea:
        coste_linea = coste_unitario * cantidad.
    Por defecto solo rellena lineas con coste 0 (no pisa un coste ya puesto a
    mano); con force=true recalcula TODAS las que tengan articulo en catalogo.
    Devuelve las lineas actualizadas y un resumen (casadas, a revisar, sin coste)."""
    by_code = await _article_costs_map()
    lines = (payload or {}).get("lines") or []
    force = bool((payload or {}).get("force"))
    out: List[Dict[str, Any]] = []
    matched = 0
    revisar = 0
    sin_coste: List[str] = []
    for l in lines:
        nl = dict(l)
        ref = _normalize_ref(l.get("ref") or "")
        art = by_code.get(ref) if ref else None
        cur = float(l.get("coste") or 0)
        if art and (force or cur == 0):
            cant = float(l.get("cantidad") or 1) or 1
            nl["coste"] = round(art["costeUnitario"] * cant, 2)
            nl["costeUnitario"] = art["costeUnitario"]
            nl["costeFuente"] = "catalogo"
            if art.get("revisar"):
                nl["costeRevisar"] = art["revisar"]
                revisar += 1
            matched += 1
        elif not art and cur == 0:
            sin_coste.append((l.get("ref") or l.get("concepto") or "").strip())
        out.append(nl)
    return {
        "success": True,
        "lines": out,
        "matched": matched,
        "revisar": revisar,
        "sinCoste": sin_coste,
        "totals": _ficha_totals(out),
    }


# ----------------------------- FICHAS (guardado) -----------------------------

@router.get("/rentabilidad/fichas")
async def list_fichas(userId: Optional[str] = None):
    """Lista las fichas de rentabilidad por lineas (resumen)."""
    try:
        query = {"createdBy": userId} if userId else {}
        fichas = await db.sale_fichas.find(query, {"_id": 0}).sort("createdAt", -1).to_list(2000)
        cobrado_map = await _cobrado_por_ficha_map()
        costes_map = await _costes_proyecto_map()
        for f in fichas:
            f["totals"] = _ficha_totals(f.get("lines", []))
            f["numDocs"] = await db.sale_ficha_docs.count_documents({"fichaId": f.get("id")})
            _apply_ficha_extras(f, cobrado_map, costes_map)
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
    cobrado_map = await _cobrado_por_ficha_map()
    costes_map = await _costes_proyecto_map()
    _apply_ficha_extras(f, cobrado_map, costes_map)
    docs = await db.sale_ficha_docs.find(
        {"fichaId": ficha_id}, {"_id": 0, "dataBase64": 0}
    ).sort("uploadedAt", 1).to_list(100)
    f["docs"] = docs
    return f


async def _ensure_client_for_invoice(nombre: str, codigo: str = ""):
    """Si una factura trae un cliente que no existe en db.clients, lo busca
    primero por el codigo que viene impreso en la factura (si lo hay) y si no
    por nombre. Solo se CREA un cliente nuevo cuando la factura trae un codigo
    de cliente fiable (usa ese MISMO codigo, no se autogenera ningun numero
    correlativo); sin codigo NO se crea nada automaticamente (evita altas por
    un nombre mal detectado por la IA, p.ej. el comercial en vez del cliente
    real) y se deja para que el controller lo cree a mano si corresponde.
    Devuelve {id, codigo, nombre, created} del cliente existente o recien
    creado, o None si no hay coincidencia y no hay codigo para crear uno."""
    nombre = (nombre or "").strip()
    codigo = (codigo or "").strip()
    if not nombre and not codigo:
        return None

    if codigo:
        existing = await db.clients.find_one(
            {"codigo": {"$regex": f"^{re.escape(codigo)}$", "$options": "i"}},
            {"_id": 0, "id": 1, "codigo": 1, "nombre": 1},
        )
        if existing:
            return {**existing, "created": False}

    if nombre:
        existing = await db.clients.find_one(
            {"nombre": {"$regex": f"^{re.escape(nombre)}$", "$options": "i"}},
            {"_id": 0, "id": 1, "codigo": 1, "nombre": 1},
        )
        if existing:
            return {**existing, "created": False}

    if not nombre or not codigo:
        return None

    client_doc = {
        "id": f"cli-{uuid.uuid4().hex[:8]}",
        "codigo": codigo,
        "nombre": nombre,
        "activo": True,   # para que aparezca en los listados de clientes activos
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "origenAutoFactura": True,
    }
    await db.clients.insert_one(client_doc)
    return {"id": client_doc["id"], "codigo": codigo, "nombre": nombre, "created": True}


@router.get("/rentabilidad/check-client")
async def check_client(nombre: str = "", codigo: str = ""):
    """Comprueba si un cliente (por codigo o nombre) ya existe, sin crearlo.
    Lo usa el frontend para avisar antes de guardar una factura si se va a
    crear un cliente nuevo."""
    nombre = (nombre or "").strip()
    codigo = (codigo or "").strip()
    existing = None
    if codigo:
        existing = await db.clients.find_one(
            {"codigo": {"$regex": f"^{re.escape(codigo)}$", "$options": "i"}},
            {"_id": 0, "id": 1, "codigo": 1, "nombre": 1},
        )
    if not existing and nombre:
        existing = await db.clients.find_one(
            {"nombre": {"$regex": f"^{re.escape(nombre)}$", "$options": "i"}},
            {"_id": 0, "id": 1, "codigo": 1, "nombre": 1},
        )
    return {"exists": bool(existing), "client": existing}


@router.post("/rentabilidad/fichas")
async def save_ficha(payload: dict, user: dict = Depends(require_rentabilidad)):
    """Crea o actualiza una ficha de rentabilidad por lineas."""
    try:
        fid = (payload or {}).get("id") or f"fic-{uuid.uuid4().hex[:8]}"
        # Ficha con visto bueno del controller: BLOQUEADA para modificaciones.
        # Solo el master puede modificarla (la UI exige el desbloqueo con Shift).
        if (payload or {}).get("id"):
            _prev = await db.sale_fichas.find_one({"id": fid}, {"_id": 0, "revisada": 1})
            if _prev and _prev.get("revisada") and not _is_elevated(user):
                raise HTTPException(status_code=403, detail="Ficha revisada por el controller: bloqueada. Solo el master puede modificarla.")
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
        existing = await db.sale_fichas.find_one({"id": fid}, {"_id": 0})
        doc["createdAt"] = (existing or {}).get("createdAt") or doc["updatedAt"]
        # Trazabilidad de conversión (documento de origen y de destino); se preserva si ya existía.
        for k in ("origenId", "origenRef", "origenType", "convertidoAId", "convertidoARef", "convertidoAType"):
            doc[k] = str(payload.get(k) or (existing or {}).get(k) or "")

        clienteCodigo = str(payload.get("clienteCodigo") or "")
        client_created = None
        if doc["docType"] == "factura" and doc["cliente"]:
            client_match = await _ensure_client_for_invoice(doc["cliente"], clienteCodigo)
            if client_match:
                doc["clienteId"] = client_match["id"]
                doc["clienteCodigo"] = client_match["codigo"]
                if client_match.get("created"):
                    client_created = {"codigo": client_match["codigo"], "nombre": client_match["nombre"]}
        else:
            doc["clienteCodigo"] = clienteCodigo

        await db.sale_fichas.update_one({"id": fid}, {"$set": doc}, upsert=True)
        doc["totals"] = _ficha_totals(norm_lines)
        return {"success": True, "ficha": doc, "clientCreated": client_created}
    except Exception as e:
        logger.error(f"Save ficha error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rentabilidad/fichas/assign-client-code")
async def assign_client_code(payload: dict, user: dict = Depends(require_rentabilidad)):
    """Asigna un código de cliente a TODAS las fichas de un cliente (por nombre).
    Útil cuando las fichas se crearon sin código y luego se conoce el código real."""
    cliente = str((payload or {}).get("cliente") or "").strip()
    codigo = str((payload or {}).get("codigo") or "").strip()
    if not cliente or not codigo:
        raise HTTPException(status_code=400, detail="Falta el cliente o el código")
    # Respeta el bloqueo del controller: a un no-master no se le tocan las fichas revisadas.
    query = {"cliente": cliente}
    if not _is_elevated(user):
        query["revisada"] = {"$ne": True}
    res = await db.sale_fichas.update_many(query, {"$set": {"clienteCodigo": codigo}})
    # Si el cliente existe en la ficha pero no en db.clients, lo damos de alta con ese código.
    try:
        await _ensure_client_for_invoice(cliente, codigo)
    except Exception as e:
        logger.warning("assign_client_code: no se pudo crear/enlazar cliente %s: %s", cliente, e)
    return {"success": True, "updated": res.modified_count}


@router.patch("/rentabilidad/fichas/{ficha_id}/trace")
async def trace_ficha(ficha_id: str, payload: dict):
    """Marca en la ficha de origen a qué documento se convirtió (trazabilidad)."""
    upd = {k: str(v or "") for k, v in (payload or {}).items()
           if k in ("convertidoAId", "convertidoARef", "convertidoAType", "origenId", "origenRef", "origenType")}
    if upd:
        await db.sale_fichas.update_one({"id": ficha_id}, {"$set": upd})
    return {"success": True}


@router.patch("/rentabilidad/fichas/{ficha_id}/revision")
async def toggle_revision(ficha_id: str, payload: dict, user: dict = Depends(require_rentabilidad)):
    """Marca o desmarca la ficha como revisada por el controller/director.
    Guarda quién la revisó y cuándo. Enviar {revisada: true} para marcar,
    {revisada: false} para desmarcar."""
    try:
        revisada = bool((payload or {}).get("revisada", True))
        # Desmarcar una ficha ya revisada solo lo puede hacer un usuario elevado
        # (master/dirección). El controller puede marcar, pero no desmarcar.
        if not revisada and not _is_elevated(user):
            raise HTTPException(status_code=403, detail="Solo el master puede quitar el visto bueno del controller")
        # No dar el visto bueno a una factura con margen 0/negativo o sin costes cargados.
        if revisada:
            fic = await db.sale_fichas.find_one({"id": ficha_id}, {"_id": 0, "lines": 1})
            tt = _ficha_totals((fic or {}).get("lines", []))
            if (tt.get("margen") or 0) <= 0:
                raise HTTPException(status_code=400, detail="No se puede marcar como revisada: el margen es 0 o negativo. Revisa venta/costes.")
            if (tt.get("venta") or 0) > 0 and not (tt.get("coste") or 0) > 0:
                raise HTTPException(status_code=400, detail="No se puede marcar como revisada: la factura no tiene costes cargados (margen no real).")
        now = datetime.now(timezone.utc).isoformat()
        upd = {
            "revisada": revisada,
            "revisadaPor": (
                (user or {}).get("name") or
                (user or {}).get("username") or
                (user or {}).get("email") or ""
            ) if revisada else "",
            "revisadaAt": now if revisada else "",
            "updatedAt": now,
        }
        await db.sale_fichas.update_one({"id": ficha_id}, {"$set": upd})
        return {
            "success": True,
            "revisada": revisada,
            "revisadaPor": upd["revisadaPor"],
            "revisadaAt": upd["revisadaAt"],
        }
    except Exception as e:
        logger.error(f"Toggle revision error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/rentabilidad/fichas/{ficha_id}")
async def delete_ficha(ficha_id: str, user: dict = Depends(require_rentabilidad)):
    try:
        existing = await db.sale_fichas.find_one({"id": ficha_id}, {"_id": 0})
        if existing and existing.get("createdBy") and not _is_elevated(user) and existing.get("createdBy") != (user or {}).get("id"):
            raise HTTPException(status_code=403, detail="No puedes borrar un documento de otro usuario")
        # Ficha con visto bueno del controller: BLOQUEADA. Solo el master puede
        # borrarla (la UI exige la secuencia de desbloqueo con la tecla Shift).
        if existing and existing.get("revisada") and not _is_elevated(user):
            raise HTTPException(status_code=403, detail="Ficha revisada por el controller: bloqueada. Solo el master puede borrarla.")
        await db.sale_fichas.delete_one({"id": ficha_id})
        await db.sale_ficha_docs.delete_many({"fichaId": ficha_id})
        if existing:
            await _log_deletion("sale_ficha", ficha_id, existing, user)
        return {"success": True}
    except HTTPException:
        raise
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
    _check_doc_size(b64)
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


@router.post("/rentabilidad/pedido-to-albaran/{project_id}")
async def pedido_to_albaran(project_id: str, request: Request):
    """Convierte el PEDIDO de un proyecto en ALBARÁN (nota de entrega). SIEMPRE
    pide serie + número de albarán (si se dejan en blanco se genera uno). Deja
    huella bidireccional: el proyecto/pedido guarda albaranId/albaranRef y el
    albarán guarda de dónde viene (sourceProjectId/sourceOrderId)."""
    body = {}
    try:
        body = await request.json()
    except Exception:
        pass

    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    if project.get("albaranId"):
        raise HTTPException(status_code=400, detail="Este pedido ya tiene un albarán asociado")
    if not project.get("orderId"):
        raise HTTPException(status_code=400, detail="Primero pasa el presupuesto a pedido")

    albaran_serie = str(body.get("albaranSerie") or "").strip()
    albaran_number = str(body.get("albaranNumber") or "").strip()
    if albaran_serie and albaran_number:
        albaran_ref = f"{albaran_serie}/{albaran_number}"
    elif albaran_number:
        albaran_ref = albaran_number
    else:
        albaran_ref = f"ALB-{uuid.uuid4().hex[:6].upper()}"

    order = await db.orders.find_one({"id": project["orderId"]}, {"_id": 0})
    now = datetime.now(timezone.utc)
    albaran = {
        "id": f"alb-{uuid.uuid4().hex[:8]}",
        "albaranRef": albaran_ref,
        "albaranSerie": albaran_serie,
        "albaranNumber": albaran_number,
        "sourceProjectId": project_id,
        "sourceOrderId": project.get("orderId"),
        "orderRef": project.get("orderRef", ""),
        "budgetNumber": project.get("budgetNumber", ""),
        "customerName": project.get("customerName", ""),
        "customerAddress": project.get("customerAddress", ""),
        "items": (order or {}).get("items", []),
        "totalAmount": float((order or {}).get("totalAmount", 0) or project.get("totalPvp", 0) or 0),
        "status": "entregado",
        "userId": project.get("userId", ""),
        "createdAt": now.isoformat(),
    }
    await db.delivery_notes.insert_one(albaran)
    await db.projects.update_one(
        {"id": project_id},
        {"$set": {
            "albaranId": albaran["id"],
            "albaranRef": albaran_ref,
            "updatedAt": now.isoformat(),
        }},
    )
    await db.orders.update_one(
        {"id": project["orderId"]},
        {"$set": {"albaranId": albaran["id"], "albaranRef": albaran_ref}},
    )
    return {"success": True, "albaranId": albaran["id"], "albaranRef": albaran_ref,
            "message": f"Pedido convertido en albarán {albaran_ref}"}


@router.post("/rentabilidad/pedido-to-factura/{project_id}")
async def pedido_to_factura(project_id: str, request: Request):
    """Convierte el ALBARÁN de un proyecto en FACTURA. SIEMPRE pide serie +
    número de factura (si se dejan en blanco se genera uno). Deja huella
    bidireccional: el proyecto/pedido/albarán guardan invoiceId/invoiceNumber y
    la factura guarda de dónde viene (sourceDeliveryNoteId/sourceOrderId)."""
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
    if not project.get("albaranId"):
        raise HTTPException(status_code=400, detail="Primero pasa el pedido a albarán")

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
    await db.delivery_notes.update_one(
        {"id": project["albaranId"]},
        {"$set": {"status": "facturado", "invoiceId": doc.get("id"),
                  "invoiceNumber": doc.get("invoiceNumber")}},
    )
    await db.invoices.update_one(
        {"id": doc.get("id")},
        {"$set": {
            "sourceDeliveryNoteId": project.get("albaranId"),
            "albaranRef": project.get("albaranRef", ""),
            "sourceOrderId": project.get("orderId", ""),
            "orderRef": project.get("orderRef", ""),
        }},
    )
    return {"success": True, "invoiceId": doc.get("id"),
            "invoiceNumber": doc.get("invoiceNumber"), "message": "Albarán facturado"}


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
    q_fichas = {"docType": {"$in": ["presupuesto", "pedido", "albaran", "factura"]}}
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
    """Registra un ingreso a cuenta. SIEMPRE debe quedar asignado a un CLIENTE
    y/o a un documento (presupuesto, pedido o factura); se archiva el
    documento del que se detectó si lo hay."""
    try:
        imp = float((payload or {}).get("importe") or 0)
    except Exception:
        imp = 0
    if imp <= 0:
        raise HTTPException(status_code=400, detail="Importe inválido")

    target_id = str((payload or {}).get("targetId") or "")
    client_code = str((payload or {}).get("clientCode") or "")
    if not target_id and not client_code:
        raise HTTPException(
            status_code=400,
            detail="El ingreso debe asignarse a un cliente y/o a un presupuesto, pedido o factura",
        )

    now = datetime.now(timezone.utc)
    iid = f"ing-{uuid.uuid4().hex[:8]}"

    # Archivar el documento (si viene en base64) en su propia colección
    doc_id = ""
    doc_b64 = (payload or {}).get("docBase64") or ""
    _check_doc_size(doc_b64)
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
        "clientCode": client_code,                              # vinculo directo a db.clients
        "projectRef": str(payload.get("projectRef") or payload.get("proyecto") or ""),
        "targetType": str(payload.get("targetType") or ""),   # presupuesto | pedido | factura
        "targetId": target_id,                                  # id de la ficha
        "targetRef": str(payload.get("targetRef") or ""),
        # Pendiente de asignación: aún no se ha vinculado a documento ni cliente.
        "pendiente": bool(payload.get("pendiente")) or (not target_id and not client_code),
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


@router.patch("/rentabilidad/ingresos/{ingreso_id}")
async def update_ingreso(ingreso_id: str, payload: dict):
    """Asigna (o reasigna) un ingreso a cuenta a un cliente y/o documento sin
    tener que borrarlo y recrearlo — pensado para resolver los que quedaron
    'pendientes de asignación'."""
    existing = await db.ingresos_cuenta.find_one({"id": ingreso_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Ingreso no encontrado")
    target_id = str((payload or {}).get("targetId") or "")
    client_code = str((payload or {}).get("clientCode") or "")
    upd = {
        "clientCode": client_code,
        "targetId": target_id,
        "targetType": str((payload or {}).get("targetType") or ""),
        "targetRef": str((payload or {}).get("targetRef") or ""),
        "pendiente": not target_id and not client_code,
    }
    if (payload or {}).get("cliente"):
        upd["cliente"] = str(payload.get("cliente"))
    if (payload or {}).get("projectRef"):
        upd["projectRef"] = str(payload.get("projectRef"))
    await db.ingresos_cuenta.update_one({"id": ingreso_id}, {"$set": upd})
    updated = await db.ingresos_cuenta.find_one({"id": ingreso_id}, {"_id": 0})
    return {"success": True, "ingreso": updated}


@router.delete("/rentabilidad/ingresos/{ingreso_id}")
async def delete_ingreso(ingreso_id: str, user: dict = Depends(require_rentabilidad)):
    existing = await db.ingresos_cuenta.find_one({"id": ingreso_id}, {"_id": 0})
    if existing and existing.get("createdBy") and not _is_elevated(user) and existing.get("createdBy") != (user or {}).get("id"):
        raise HTTPException(status_code=403, detail="No puedes borrar un ingreso de otro usuario")
    await db.ingresos_cuenta.delete_one({"id": ingreso_id})
    await db.ingreso_docs.delete_many({"ingresoId": ingreso_id})
    if existing:
        await _log_deletion("ingreso_cuenta", ingreso_id, existing, user)
    return {"success": True}


# ── Migración: limpiar espacios en refs de fichas existentes ─────────────────
@router.post("/rentabilidad/admin/normalize-refs")
async def normalize_refs(user: dict = Depends(require_rentabilidad)):
    """Elimina espacios alrededor de '/' en el campo ref de todas las fichas.
    Convierte 'LG26 / 61' → 'LG26/61' para que el filtro funcione correctamente.
    Solo accesible para administradores o usuarios con permisos elevados.
    """
    import re as _re
    if not _is_elevated(user):
        raise HTTPException(status_code=403, detail="Solo administradores pueden ejecutar migraciones")

    def _clean_ref(v: str) -> str:
        return _re.sub(r'\s*/\s*', '/', str(v or '').strip())

    cursor = db.fichas_rentabilidad.find({}, {"_id": 0, "id": 1, "ref": 1})
    updated = 0
    skipped = 0
    async for doc in cursor:
        original = doc.get("ref") or ""
        cleaned = _clean_ref(original)
        if cleaned != original:
            await db.fichas_rentabilidad.update_one(
                {"id": doc["id"]},
                {"$set": {"ref": cleaned}}
            )
            updated += 1
        else:
            skipped += 1

    return {
        "success": True,
        "updated": updated,
        "skipped": skipped,
        "message": f"Normalizadas {updated} referencias. {skipped} ya estaban correctas."
    }
