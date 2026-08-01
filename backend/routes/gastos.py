"""
Gestión de gastos de comerciales (estilo Etiquelia).

Escanea un ticket/factura (foto o PDF), la IA detecta el TIPO de gasto y los
importes, y el comercial puede ajustarlo. Controla dietas, combustible (gasoil),
peajes, parking, alojamiento, transporte y demás gastos de representación.

Colecciones:
- gastos       { id, userId, userName, tipo, importe, base, iva, fecha, proveedor,
                 descripcion, kms, docId, createdAt, updatedAt }
- gasto_docs   { id, gastoId, dataBase64, mime, filename, createdAt }
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone
from typing import Optional
import uuid
import logging
import os
import json
import re
from services.db_client import get_db as _get_db

logger = logging.getLogger(__name__)

# Seguridad: el modulo no exigia ningun token; cualquiera que conociera la URL
# podia ver los tickets/gastos (importes, proveedores) de cualquier comercial.
try:
    from services.jwt_service import require_module_access
    _GASTOS_DEPS = [Depends(require_module_access("canAccessGastos"))]
except Exception:  # pragma: no cover - fallback si no hay jwt_service
    _GASTOS_DEPS = []

router = APIRouter(tags=["gastos"], dependencies=_GASTOS_DEPS)


# Tipos de gasto admitidos (clave interna -> etiqueta)
TIPOS_GASTO = {
    "dieta": "Dieta / Comida",
    "combustible": "Combustible / Gasoil",
    "peaje": "Peaje",
    "parking": "Parking",
    "alojamiento": "Alojamiento / Hotel",
    "transporte": "Transporte (tren/avión/taxi)",
    "material": "Material / Oficina",
    "representacion": "Representación",
    "otros": "Otros",
}
_VALID_TIPOS = set(TIPOS_GASTO.keys())


_SCAN_PROMPT = """Eres un experto en clasificar tickets y facturas de gastos de
comerciales (dietas/comidas, combustible/gasoil, peajes, parking, hoteles,
transporte, material...). Analiza el ticket y responde SOLO con JSON válido:
{
  "tipo": "dieta|combustible|peaje|parking|alojamiento|transporte|material|representacion|otros",
  "importe": 0,            // TOTAL pagado (con IVA) como número decimal con punto
  "base": 0,               // base imponible si aparece, si no 0
  "iva": 0,                // cuota de IVA si aparece, si no 0
  "fecha": "YYYY-MM-DD",   // fecha del ticket
  "proveedor": "nombre del establecimiento/emisor",
  "descripcion": "resumen breve de lo consumido/comprado",
  "litros": 0              // si es combustible y aparecen litros, si no 0
}
Reglas: importes en número con punto decimal, sin símbolo de moneda. Clasifica el
TIPO por el establecimiento y los conceptos (gasolinera->combustible, restaurante/bar->dieta,
autopista/AP->peaje, hotel->alojamiento, renfe/iberia/taxi->transporte). Si no estás
seguro, usa "otros".
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


def _num(v):
    try:
        return round(float(v), 2)
    except Exception:
        return 0.0


@router.post("/gastos/scan")
async def scan_ticket(payload: dict):
    """Lee un ticket/factura (PDF o imagen) y detecta el tipo de gasto e importes."""
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
            if len(text.strip()) >= 40:
                resp = await chat_with_gemini(
                    prompt=_SCAN_PROMPT + "\n\nTEXTO DEL TICKET:\n\n" + text[:20000],
                    system_message="Clasificas tickets de gastos de comerciales.",
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
                image_base64=img, prompt=_SCAN_PROMPT,
                session_id=f"gasto-{uuid.uuid4().hex[:8]}", model="gemini-2.5-flash",
            )
            parsed = _parse_json_loose(_clean_json(resp))

        if not parsed:
            return {"success": False, "error": "No se pudieron extraer datos del ticket"}

        tipo = str(parsed.get("tipo") or "otros").lower().strip()
        if tipo not in _VALID_TIPOS:
            tipo = "otros"
        return {
            "success": True,
            "data": {
                "tipo": tipo,
                "importe": _num(parsed.get("importe")),
                "base": _num(parsed.get("base")),
                "iva": _num(parsed.get("iva")),
                "fecha": str(parsed.get("fecha") or datetime.now(timezone.utc).strftime("%Y-%m-%d")),
                "proveedor": str(parsed.get("proveedor") or ""),
                "descripcion": str(parsed.get("descripcion") or ""),
                "litros": _num(parsed.get("litros")),
            },
        }
    except Exception as e:
        logger.error(f"Scan ticket error: {e}")
        return {"success": False, "error": str(e)}


@router.get("/gastos/tipos")
async def get_tipos():
    """Catálogo de tipos de gasto."""
    return [{"key": k, "label": v} for k, v in TIPOS_GASTO.items()]


@router.get("/gastos")
async def list_gastos(userId: Optional[str] = None, mes: Optional[str] = None):
    """Lista de gastos (cada comercial los suyos si se pasa userId).

    mes opcional 'YYYY-MM' para filtrar por mes.
    """
    query = {}
    if userId:
        query["userId"] = userId
    if mes:
        query["fecha"] = {"$regex": f"^{re.escape(mes)}"}
    items = await _get_db().gastos.find(query, {"_id": 0}).sort("fecha", -1).to_list(5000)
    total = round(sum(float(i.get("importe", 0) or 0) for i in items), 2)
    by_type = {}
    for i in items:
        t = i.get("tipo") or "otros"
        by_type[t] = round(by_type.get(t, 0) + float(i.get("importe", 0) or 0), 2)
    return {"items": items, "total": total, "byType": by_type, "tipos": TIPOS_GASTO}


@router.post("/gastos")
async def create_gasto(payload: dict):
    """Registra un gasto (opcionalmente archiva el ticket)."""
    imp = _num((payload or {}).get("importe"))
    if imp <= 0:
        raise HTTPException(status_code=400, detail="Importe inválido")
    tipo = str(payload.get("tipo") or "otros").lower().strip()
    if tipo not in _VALID_TIPOS:
        tipo = "otros"
    now = datetime.now(timezone.utc)
    gid = f"gasto-{uuid.uuid4().hex[:8]}"

    doc_id = ""
    doc_b64 = (payload or {}).get("docBase64") or ""
    if doc_b64:
        stripped = doc_b64.split(",", 1)[1] if doc_b64.startswith("data:") else doc_b64
        doc_id = f"gastodoc-{uuid.uuid4().hex[:8]}"
        await _get_db().gasto_docs.insert_one({
            "id": doc_id, "gastoId": gid,
            "dataBase64": stripped,
            "mime": str(payload.get("docMime") or "application/octet-stream"),
            "filename": str(payload.get("docName") or "ticket"),
            "createdAt": now.isoformat(),
        })

    doc = {
        "id": gid,
        "userId": str(payload.get("userId") or ""),
        "userName": str(payload.get("userName") or ""),
        "tipo": tipo,
        "importe": imp,
        "base": _num(payload.get("base")),
        "iva": _num(payload.get("iva")),
        "fecha": str(payload.get("fecha") or now.strftime("%Y-%m-%d")),
        "proveedor": str(payload.get("proveedor") or ""),
        "descripcion": str(payload.get("descripcion") or ""),
        "litros": _num(payload.get("litros")),
        "kms": _num(payload.get("kms")),
        "docId": doc_id,
        "createdAt": now.isoformat(),
        "updatedAt": now.isoformat(),
    }
    await _get_db().gastos.insert_one(doc)
    doc.pop("_id", None)
    return {"success": True, "gasto": doc}


@router.put("/gastos/{gasto_id}")
async def update_gasto(gasto_id: str, payload: dict):
    """Edita un gasto (importe, tipo, fecha, proveedor...)."""
    existing = await _get_db().gastos.find_one({"id": gasto_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Gasto no encontrado")
    allowed = ("tipo", "importe", "base", "iva", "fecha", "proveedor", "descripcion", "litros", "kms")
    update = {}
    for k in allowed:
        if k in payload:
            if k in ("importe", "base", "iva", "litros", "kms"):
                update[k] = _num(payload[k])
            elif k == "tipo":
                t = str(payload[k] or "otros").lower().strip()
                update[k] = t if t in _VALID_TIPOS else "otros"
            else:
                update[k] = str(payload[k] or "")
    if not update:
        raise HTTPException(status_code=400, detail="Nada que actualizar")
    update["updatedAt"] = datetime.now(timezone.utc).isoformat()
    await _get_db().gastos.update_one({"id": gasto_id}, {"$set": update})
    doc = await _get_db().gastos.find_one({"id": gasto_id}, {"_id": 0})
    return {"success": True, "gasto": doc}


@router.delete("/gastos/{gasto_id}")
async def delete_gasto(gasto_id: str):
    await _get_db().gastos.delete_one({"id": gasto_id})
    await _get_db().gasto_docs.delete_many({"gastoId": gasto_id})
    return {"success": True}


@router.get("/gastos/doc/{doc_id}")
async def get_gasto_doc(doc_id: str):
    d = await _get_db().gasto_docs.find_one({"id": doc_id}, {"_id": 0})
    if not d:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    return d


# ============================================================================
# INFORMES / CIERRES DE GASTOS  (marcas tickets y los agrupas en un informe)
# Colección: gasto_informes { id, userId, userName, nombre, gastoIds, total,
#                             byType, fechaDesde, fechaHasta, createdAt }
# ============================================================================

@router.post("/gastos/informes")
async def create_informe(payload: dict):
    """Crea un informe de gastos asociando los tickets marcados (cierre mensual)."""
    nombre = str((payload or {}).get("nombre") or "").strip()
    gasto_ids = list((payload or {}).get("gastoIds") or [])
    if not nombre:
        raise HTTPException(status_code=400, detail="Indica un nombre para el informe")
    if not gasto_ids:
        raise HTTPException(status_code=400, detail="Marca al menos un ticket")

    gastos = await _get_db().gastos.find({"id": {"$in": gasto_ids}}, {"_id": 0}).to_list(5000)
    if not gastos:
        raise HTTPException(status_code=404, detail="No se encontraron los gastos indicados")

    total = round(sum(float(g.get("importe", 0) or 0) for g in gastos), 2)
    by_type = {}
    fechas = []
    for g in gastos:
        t = g.get("tipo") or "otros"
        by_type[t] = round(by_type.get(t, 0) + float(g.get("importe", 0) or 0), 2)
        if g.get("fecha"):
            fechas.append(str(g["fecha"])[:10])
    fechas.sort()

    now = datetime.now(timezone.utc)
    iid = f"inf-{uuid.uuid4().hex[:8]}"
    doc = {
        "id": iid,
        "userId": str(payload.get("userId") or ""),
        "userName": str(payload.get("userName") or ""),
        "nombre": nombre,
        "gastoIds": [g.get("id") for g in gastos],
        "total": total,
        "byType": by_type,
        "numTickets": len(gastos),
        "fechaDesde": fechas[0] if fechas else "",
        "fechaHasta": fechas[-1] if fechas else "",
        "createdAt": now.isoformat(),
    }
    await _get_db().gasto_informes.insert_one(doc)
    doc.pop("_id", None)
    # Marcar los gastos como incluidos en este informe (cierre)
    await _get_db().gastos.update_many(
        {"id": {"$in": doc["gastoIds"]}},
        {"$set": {"informeId": iid, "informeNombre": nombre}},
    )
    return {"success": True, "informe": doc}


@router.get("/gastos/informes")
async def list_informes(userId: Optional[str] = None):
    query = {"userId": userId} if userId else {}
    items = await _get_db().gasto_informes.find(query, {"_id": 0}).sort("createdAt", -1).to_list(2000)
    return {"items": items}


@router.get("/gastos/informes/{informe_id}")
async def get_informe(informe_id: str):
    inf = await _get_db().gasto_informes.find_one({"id": informe_id}, {"_id": 0})
    if not inf:
        raise HTTPException(status_code=404, detail="Informe no encontrado")
    gastos = await _get_db().gastos.find({"id": {"$in": inf.get("gastoIds", [])}}, {"_id": 0}).sort("fecha", 1).to_list(5000)
    inf["gastos"] = gastos
    return inf


@router.delete("/gastos/informes/{informe_id}")
async def delete_informe(informe_id: str):
    inf = await _get_db().gasto_informes.find_one({"id": informe_id}, {"_id": 0})
    if inf:
        # Desmarcar los gastos para que vuelvan a estar disponibles
        await _get_db().gastos.update_many(
            {"id": {"$in": inf.get("gastoIds", [])}},
            {"$unset": {"informeId": "", "informeNombre": ""}},
        )
    await _get_db().gasto_informes.delete_one({"id": informe_id})
    return {"success": True}
