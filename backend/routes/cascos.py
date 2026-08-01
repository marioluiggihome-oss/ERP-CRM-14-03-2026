"""
Pedidos del Presupuestador de Cascos (Grupo ACB). Módulo independiente:
guarda los pedidos de cascos por usuario. El catálogo vive en el frontend
(generado desde la tarifa oficial).
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timedelta, timezone
from typing import Optional
import logging
import os
import uuid

try:
    from services.jwt_service import get_current_user, require_auth, ADMIN_ROLE_FLAGS
    _CASCOS_DEPS = [Depends(require_auth)]
except Exception:
    async def get_current_user():
        return None
    ADMIN_ROLE_FLAGS = ["isAdmin", "isGerente", "isDirectorComercial"]
    _CASCOS_DEPS = []

logger = logging.getLogger(__name__)
# Todos los pedidos de cascos requieren token válido (aislamiento por usuario dentro).
router = APIRouter(tags=["cascos"], dependencies=_CASCOS_DEPS)


def _safe_float(v, default=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default

# Este backend abre un cliente de Mongo por modulo (unos 40 en total), cada uno
# con su propio pool. Un modulo poco usado como este tiene que abrir conexion
# nueva cuando se le llama y, si el cluster va justo de conexiones, la peticion
# se quedaba colgada los 30 s del timeout por defecto hasta que la cortaba la
# pasarela: en el navegador eso se ve como un "Failed to fetch" sin explicacion.
# Con 5 s falla rapido y con un error legible, y el pool se limita para no
# acaparar conexiones del cluster.


@router.post("/cascos/orders")
async def create_casco_order(payload: dict, current_user: Optional[dict] = Depends(get_current_user)):
    """Crea (guarda) un pedido de cascos."""
    try:
        uid = (current_user or {}).get("id") or "anonymous"
        oid = (payload or {}).get("id") or f"casco-{uuid.uuid4().hex[:10]}"
        now = datetime.now(timezone.utc).isoformat()
        existing = await _get_db().cascos_orders.find_one({"id": oid}, {"_id": 0, "createdAt": 1, "userId": 1})
        # Al re-guardar por id, comprobar propiedad (evita pisar el pedido de otro).
        if existing and not _can_access(existing, current_user):
            raise HTTPException(status_code=403, detail="Sin acceso a este pedido")
        doc = {
            "id": oid,
            "userId": (existing or {}).get("userId") or uid,  # nunca se toma del payload
            "kind": str(payload.get("kind") or "pedido"),   # 'presupuesto' | 'pedido' | 'compra'
            "expediente": str(payload.get("expediente") or ""),  # vínculo venta <-> compra
            "cliente": str(payload.get("cliente") or ""),
            "ref": str(payload.get("ref") or ""),
            "ivaRate": _safe_float(payload.get("ivaRate"), 21),
            "descuento": _safe_float(payload.get("descuento"), 0),
            "lines": payload.get("lines") or [],
            "total": _safe_float(payload.get("total"), 0),
            "createdByName": payload.get("createdByName", ""),
            "createdAt": (existing or {}).get("createdAt") or now,
            "updatedAt": now,
        }
        await _get_db().cascos_orders.update_one({"id": oid}, {"$set": doc}, upsert=True)
        doc.pop("_id", None)
        return {"success": True, "order": doc}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create casco order error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cascos/orders")
async def list_casco_orders(userId: Optional[str] = None, kind: Optional[str] = None, expediente: Optional[str] = None, current_user: Optional[dict] = Depends(get_current_user)):
    """Lista los pedidos/presupuestos de cascos. Aislamiento por usuario (admin ve todos)."""
    try:
        query = {}
        if kind:
            query["kind"] = kind
        if expediente:
            query["expediente"] = expediente
        if current_user and current_user.get("id"):
            elevated = any(current_user.get(f) for f in ADMIN_ROLE_FLAGS)
            if not elevated:
                query["userId"] = current_user["id"]
        elif userId:
            query["userId"] = userId
        orders = await _get_db().cascos_orders.find(query, {"_id": 0}).sort("createdAt", -1).to_list(500)
        return {"success": True, "orders": orders}
    except Exception as e:
        logger.error(f"List casco orders error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _can_access(order: dict, current_user: Optional[dict]) -> bool:
    """Admin/elevado ve todo; el resto solo sus propios pedidos."""
    if not current_user or not current_user.get("id"):
        return False  # sin usuario autenticado no hay acceso
    if any(current_user.get(f) for f in ADMIN_ROLE_FLAGS):
        return True
    return order.get("userId") == current_user["id"]


@router.get("/cascos/orders/{order_id}")
async def get_casco_order(order_id: str, current_user: Optional[dict] = Depends(get_current_user)):
    o = await _get_db().cascos_orders.find_one({"id": order_id}, {"_id": 0})
    if not o:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    if not _can_access(o, current_user):
        raise HTTPException(status_code=403, detail="Sin acceso a este pedido")
    return o


@router.delete("/cascos/orders/{order_id}")
async def delete_casco_order(order_id: str, current_user: Optional[dict] = Depends(get_current_user)):
    o = await _get_db().cascos_orders.find_one({"id": order_id}, {"_id": 0, "userId": 1})
    if o and not _can_access(o, current_user):
        raise HTTPException(status_code=403, detail="Sin acceso a este pedido")
    await _get_db().cascos_orders.delete_one({"id": order_id})
    return {"success": True}


# ─── IMPORTADOR DE PROFORMA DE PROVEEDOR (solo MASTER) ──────────────────────────
def _es_master(user: Optional[dict]) -> bool:
    return bool(user and any(user.get(f) for f in list(ADMIN_ROLE_FLAGS) + ["isPrimaryAdmin"]))


_TAREAS_PROFORMA = set()
# Estado de los analisis de proforma en curso: {job_id: {...}}. En memoria, no en
# Mongo (ver _job_set). Se limpia solo en _job_limpiar.
_JOBS = {}

_PROMPT_PROFORMA = (
    "Esta imagen es una página de una PROFORMA de muebles de cocina (cascos). "
    "Extrae la tabla de artículos. Devuelve SOLO un JSON: {\"items\":[{\"n\":1,"
    "\"cod\":\"80GF/1P1GIN\",\"descripcion\":\"...\",\"material\":\"MELAMINA ... ZENIT - MERIVOBOX\","
    "\"largo\":800,\"ancho\":500,\"grueso\":580,\"cantidad\":1,\"pvp\":402.73}]}. "
    "'pvp' es la columna PRECIO. Si una fila no es un mueble, inclúyela igual. "
    "La página puede estar girada 90º: léela en la orientación en que el texto tenga sentido. "
    "Copia los números EXACTAMENTE como aparecen; si un dato no se lee, pon null. NO lo inventes."
)


def _filas_a_items(allrows: list) -> list:
    """Enriquece las filas crudas de la IA con color/herraje/frentes/tipo."""
    from services.proforma_cascos import _color_y_herraje, _cuenta_frentes, _tipo_mueble
    items = []
    for r in allrows:
        material = r.get("material") or ""
        color, blum = _color_y_herraje(material)
        desc = r.get("descripcion") or ""
        fr = _cuenta_frentes(desc)
        items.append({
            "n": r.get("n"), "cod": r.get("cod") or "", "descripcion": desc,
            "material": material, "color": color, "herrajeBlum": blum,
            "largo": r.get("largo"), "ancho": r.get("ancho"), "grueso": r.get("grueso"),
            "cantidad": r.get("cantidad") or 1.0, "pvp": r.get("pvp"), "total": r.get("pvp"),
            "puertas": fr["puertas"], "cajones": fr["cajones"], "gavetas": fr["gavetas"],
            "tipo": _tipo_mueble(desc), "esMueble": True,
        })
    return items


async def _proforma_pagina_ia(idx: int, pg: str, timeout: float) -> tuple:
    """Lee una página con visión IA. Si el modelo 'pro' falla o tarda, reintenta
    con 'flash', que es bastante más rápido. Devuelve (idx, filas)."""
    import asyncio as _asyncio, re as _re, json as _json
    from services.llm_vision import analyze_image_with_gemini
    for modelo in ("gemini-2.5-pro", "gemini-2.5-flash"):
        try:
            t = await _asyncio.wait_for(
                analyze_image_with_gemini(image_base64=pg, prompt=_PROMPT_PROFORMA,
                                          model=modelo, image_mime="image/png"),
                timeout=timeout,
            )
            mm = _re.search(r"\{[\s\S]*\}", t or "")
            if mm:
                filas = (_json.loads(mm.group()).get("items")) or []
                if filas:
                    return idx, filas
        except _asyncio.TimeoutError:
            logger.warning("proforma visión: página %d agotó %ss con %s", idx + 1, timeout, modelo)
        except Exception as e:
            logger.warning("proforma visión página %d (%s): %s", idx + 1, modelo, e)
    return idx, []


async def _proforma_job(job_id: str, pdf_bytes: bytes):
    """Procesa la proforma en segundo plano y va dejando el estado en Mongo.

    El trabajo se saca de la petición HTTP a propósito: leer varias páginas con
    visión IA puede tardar minutos y ninguna pasarela aguanta una petición
    abierta tanto rato — de ahí el "Failed to fetch" del navegador. El frontend
    arranca el trabajo, recibe un id al instante y va preguntando por el estado.
    """
    import asyncio as _asyncio
    from services.proforma_cascos import pdf_pages_to_png_b64
    try:
        pages = await _asyncio.get_running_loop().run_in_executor(
            None, pdf_pages_to_png_b64, pdf_bytes)
        if not pages:
            await _job_set(job_id, estado="error", error="El PDF no tiene páginas legibles.")
            return
        await _job_set(job_id, total=len(pages))

        allrows, hechas = [], 0
        tareas = [_asyncio.ensure_future(_proforma_pagina_ia(i, pg, 90.0))
                  for i, pg in enumerate(pages)]
        resultados = []
        for fut in _asyncio.as_completed(tareas):
            try:
                resultados.append(await fut)
            except Exception as e:
                logger.warning("proforma job %s: página perdida: %s", job_id, e)
            hechas += 1
            await _job_set(job_id, hechas=hechas)
        for _idx, filas in sorted(resultados, key=lambda x: x[0]):
            allrows.extend(filas)

        items = _filas_a_items(allrows)
        if items:
            await _job_set(job_id, estado="listo", items=items, count=len(items))
        else:
            await _job_set(job_id, estado="error",
                           error="La IA no consiguió leer ninguna línea de artículos en el PDF.")
    except Exception as e:
        logger.error("proforma job %s: %s", job_id, e)
        await _job_set(job_id, estado="error", error=f"Error al analizar el PDF: {e}")


async def _job_set(job_id: str, **campos):
    """Actualiza el estado del trabajo.

    El estado vive EN MEMORIA a proposito. Antes iba a Mongo para que el sondeo
    funcionase aunque lo atendiera otro worker, pero el servicio corre con una
    sola replica y a cambio metia una escritura en Mongo dentro de la peticion:
    si el cluster tardaba en dar conexion, el POST se colgaba y el navegador solo
    veia un "Failed to fetch". Analizar un PDF no necesita base de datos, asi que
    ya no depende de ella. (Si algun dia hay varias replicas, habra que volver a
    un almacen compartido.)
    """
    job = _JOBS.get(job_id)
    if job is None:
        return
    job.update(campos)
    job["updatedAt"] = datetime.now(timezone.utc).isoformat()


def _job_limpiar():
    """Descarta los trabajos viejos para que el diccionario no crezca sin fin."""
    limite = datetime.now(timezone.utc) - timedelta(hours=2)
    for jid, j in list(_JOBS.items()):
        try:
            if datetime.fromisoformat(j.get("createdAt")) < limite:
                _JOBS.pop(jid, None)
        except Exception:
            _JOBS.pop(jid, None)


@router.post("/cascos/proforma")
async def importar_proforma(payload: dict, current_user: Optional[dict] = Depends(get_current_user)):
    """Detecta los muebles de un PDF de proforma de proveedor (multipágina).
    Solo MASTER. Devuelve la relación de muebles con código, descripción, color,
    herraje, medidas, cantidad, PVP proveedor y recuento de puertas/cajones/gavetas.

    Si el PDF trae capa de texto se resuelve al momento (`estado: 'listo'`). Si es
    un PDF de imagen o de texto vectorizado hay que pasar por visión IA, que tarda
    demasiado para una petición HTTP: se lanza un trabajo en segundo plano y se
    devuelve `estado: 'procesando'` con un `jobId` que el frontend va sondeando.
    """
    if not _es_master(current_user):
        raise HTTPException(status_code=403, detail="Solo el master puede importar proformas de proveedor.")
    import base64 as _b64, re as _re, asyncio as _asyncio
    raw = (payload or {}).get("pdfBase64") or (payload or {}).get("pdf") or ""
    if not raw:
        raise HTTPException(status_code=400, detail="Falta el PDF de la proforma.")
    m = _re.match(r"^data:[^;]+;base64,(.*)$", raw, _re.DOTALL)
    b64 = m.group(1) if m else raw
    if len(b64) > 40 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="El PDF es demasiado grande (máximo unos 30 MB).")
    try:
        pdf_bytes = _b64.b64decode(b64)
    except Exception:
        raise HTTPException(status_code=400, detail="PDF no válido.")

    from services.proforma_cascos import parse_proforma_text, extract_pdf_text_all_pages
    # 1) Intento por CAPA DE TEXTO (rápido y exacto): se responde en el acto.
    # Va al executor porque PyMuPDF es código nativo bloqueante y el servidor
    # corre con una sola réplica: un PDF pesado congelaría a todos los usuarios.
    items = []
    try:
        txt = await _asyncio.get_running_loop().run_in_executor(
            None, extract_pdf_text_all_pages, pdf_bytes)
        if txt and len(txt.strip()) > 40:
            items = parse_proforma_text(txt)
    except Exception as e:
        logger.warning("proforma: fallo lectura de texto: %s", e)
    if items:
        return {"success": True, "estado": "listo", "items": items, "count": len(items)}

    # 2) Sin capa de texto -> visión IA en segundo plano.
    from services.llm_vision import is_vision_available
    if not is_vision_available():
        raise HTTPException(status_code=503, detail="El PDF es una imagen y la IA de visión no está configurada.")

    job_id = f"prof-{uuid.uuid4().hex[:12]}"
    ahora = datetime.now(timezone.utc).isoformat()
    _job_limpiar()
    _JOBS[job_id] = {
        "id": job_id, "estado": "procesando", "hechas": 0, "total": 0,
        "items": [], "error": "", "userId": (current_user or {}).get("id") or "",
        "createdAt": ahora, "updatedAt": ahora,
    }
    # Se guarda la referencia: una tarea suelta puede llevársela el recolector.
    tarea = _asyncio.ensure_future(_proforma_job(job_id, pdf_bytes))
    _TAREAS_PROFORMA.add(tarea)
    tarea.add_done_callback(_TAREAS_PROFORMA.discard)
    return {"success": True, "estado": "procesando", "jobId": job_id}


@router.get("/cascos/proforma/ping")
async def proforma_ping(current_user: Optional[dict] = Depends(get_current_user)):
    """Endpoint de diagnóstico: confirma que el importador está disponible y
    si la visión IA está configurada. El frontend lo sondea para distinguir
    'servidor caido' de 'ruta no desplegada aún' de 'falta clave de IA'."""
    from services.llm_vision import is_vision_available
    return {
        "ok": True,
        "vision": is_vision_available(),
        "master": _es_master(current_user),
    }


@router.get("/cascos/proforma/job/{job_id}")
async def estado_proforma(job_id: str, current_user: Optional[dict] = Depends(get_current_user)):
    """Estado de un trabajo de importación de proforma (sondeo del frontend)."""
    if not _es_master(current_user):
        raise HTTPException(status_code=403, detail="Solo el master puede importar proformas de proveedor.")
    job = _JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="El análisis ha caducado. Vuelve a subir el PDF.")
    return {
        "success": job.get("estado") != "error",
        "estado": job.get("estado") or "procesando",
        "hechas": job.get("hechas") or 0,
        "total": job.get("total") or 0,
        "items": job.get("items") or [],
        "count": len(job.get("items") or []),
        "detail": job.get("error") or "",
    }


# ─── Tarifa MV (puntos) para el módulo de Rentabilidad ──────────────────────────
import json as _mvjson, os as _mvos
from services.db_client import get_db as _get_db
_MV_PATH = _mvos.path.join(_mvos.path.dirname(_mvos.path.dirname(__file__)), "data", "mv_tarifas_oficiales.json")


@router.get("/cascos/mv/tarifa")
async def mv_tarifa(tariff: str = "T1", current_user: Optional[dict] = Depends(get_current_user)):
    """Devuelve la tarifa MV pedida (por defecto T1) con sus códigos y puntos, y el
    valor de punto. Para el módulo de Rentabilidad Tarifa MV (solo master)."""
    if not _es_master(current_user):
        raise HTTPException(status_code=403, detail="Solo el master puede ver la tarifa MV.")
    try:
        with open(_MV_PATH, "r", encoding="utf-8") as f:
            data = _mvjson.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"No se pudo leer la tarifa MV: {e}")
    tfs = data.get("tariffs", {})
    if tariff not in tfs:
        raise HTTPException(status_code=404, detail=f"Tarifa {tariff} no encontrada.")
    return {
        "success": True,
        "tariff": tariff,
        "pointValue": data.get("_meta", {}).get("pointValue", 3.33),
        "familias": tfs[tariff],
    }


@router.post("/cascos/mv/detectar-pdf")
async def mv_detectar_pdf(payload: dict, current_user: Optional[dict] = Depends(get_current_user)):
    """Detecta códigos de muebles MV en un PDF (relación/presupuesto) para el módulo
    de Rentabilidad MV. Devuelve los códigos candidatos; el frontend los valida
    contra la tarifa. Solo master."""
    if not _es_master(current_user):
        raise HTTPException(status_code=403, detail="Solo el master puede importar relaciones MV.")
    import base64 as _b64, re as _re
    raw = (payload or {}).get("pdfBase64") or ""
    m = _re.match(r"^data:[^;]+;base64,(.*)$", raw, _re.DOTALL)
    b64 = m.group(1) if m else raw
    if not b64:
        raise HTTPException(status_code=400, detail="Falta el PDF.")
    try:
        pdf_bytes = _b64.b64decode(b64)
    except Exception:
        raise HTTPException(status_code=400, detail="PDF no válido.")

    from services.proforma_cascos import extract_pdf_text_all_pages, pdf_pages_to_png_b64
    text = ""
    try:
        text = extract_pdf_text_all_pages(pdf_bytes) or ""
    except Exception as e:
        logger.warning("mv detectar: texto %s", e)
    # Respaldo por visión IA si el PDF es imagen.
    if len(text.strip()) < 30:
        try:
            from services.llm_vision import analyze_image_with_gemini, is_vision_available
            if is_vision_available():
                pages = pdf_pages_to_png_b64(pdf_bytes)
                prompt = ("Esta imagen es un presupuesto/relación de muebles de cocina. Extrae SOLO los "
                          "CÓDIGOS de mueble (tipo B60, A60, BCG40, CD60, D/I si aparece) y su cantidad. "
                          "Devuelve un JSON: {\"lineas\":[{\"cod\":\"B60\",\"cant\":1}]}.")
                import json as _json
                for pg in pages:
                    t = await analyze_image_with_gemini(image_base64=pg, prompt=prompt,
                                                        model="gemini-2.5-flash", image_mime="image/png")
                    mm = _re.search(r"\{[\s\S]*\}", t or "")
                    if mm:
                        text += " " + " ".join(f"{it.get('cod','')} x{it.get('cant',1)}" for it in (_json.loads(mm.group()).get("lineas") or []))
        except Exception as e:
            logger.warning("mv detectar visión: %s", e)

    # Candidatos: token tipo LETRAS+DIGITOS (+ D/I opcional). El frontend valida.
    cands = _re.findall(r"\b([A-Z]{1,5}\d{2,3}(?:D/I|D|I)?)\b", (text or "").upper())
    # Cantidades "x2" contiguas
    lineas = []
    seen = {}
    for c in cands:
        seen[c] = seen.get(c, 0) + 1
    return {"success": True, "codigos": list(seen.keys()), "conteo": seen}


@router.post("/cascos/mv/detectar-relacion")
async def mv_detectar_relacion(payload: dict, current_user: Optional[dict] = Depends(get_current_user)):
    """Lee una RELACIÓN de muebles MV escrita en el PDF de nomenclaturas rellenable
    (o cualquier PDF con esa notación: '1 b25d + 1b30d (altura 80)', '1asc60x90 d'…)
    y devuelve los muebles emparejados con la tarifa MV (código canónico, tipo,
    ancho, alto, puntos y PVP). Pensado para VOLCAR al Presupuestador / Cocina
    Desmontada sin necesidad de un dibujo. Solo master."""
    if not _es_master(current_user):
        raise HTTPException(status_code=403, detail="Solo el master puede importar relaciones MV.")
    import base64 as _b64, re as _re
    tariff = (payload or {}).get("tariff") or "T1"
    texto = (payload or {}).get("texto")
    # Vía TEXTO: para el buscador "añadir a mano" (p. ej. "1 b45d (altura 80)").
    if texto:
        try:
            from services.mv_relacion import parse_relacion_text
            muebles = parse_relacion_text(str(texto), tariff)
        except Exception as e:
            logger.error("mv detectar-relacion texto: %s", e)
            raise HTTPException(status_code=500, detail=f"No se pudo leer la relación: {e}")
        if not muebles:
            raise HTTPException(status_code=422, detail="No se reconoció ningún mueble. Escríbelo como '1 b60i (altura 80)'.")
        return {
            "success": True, "muebles": muebles, "count": len(muebles),
            "totalUnidades": sum(int(x.get("qty") or 1) for x in muebles),
            "totalPvp": round(sum((x.get("pvp") or 0) * int(x.get("qty") or 1) for x in muebles), 2),
        }
    # Vía PDF.
    raw = (payload or {}).get("pdfBase64") or ""
    m = _re.match(r"^data:[^;]+;base64,(.*)$", raw, _re.DOTALL)
    b64 = m.group(1) if m else raw
    if not b64:
        raise HTTPException(status_code=400, detail="Falta el PDF de la relación.")
    try:
        pdf_bytes = _b64.b64decode(b64)
    except Exception:
        raise HTTPException(status_code=400, detail="PDF no válido.")
    try:
        from services.mv_relacion import detectar_relacion_pdf
        muebles = detectar_relacion_pdf(pdf_bytes, tariff)
    except Exception as e:
        logger.error("mv detectar-relacion: %s", e)
        raise HTTPException(status_code=500, detail=f"No se pudo leer la relación: {e}")
    if not muebles:
        raise HTTPException(
            status_code=422,
            detail="No se detectó ninguna relación de muebles. Rellena los recuadros con la notación (p. ej. '1 b60i + 1 a60d (altura 80)').",
        )
    return {
        "success": True,
        "muebles": muebles,
        "count": len(muebles),
        "totalUnidades": sum(int(x.get("qty") or 1) for x in muebles),
        "totalPvp": round(sum((x.get("pvp") or 0) * int(x.get("qty") or 1) for x in muebles), 2),
    }


@router.get("/cascos/mv/nomenclaturas-pdf")
async def nomenclaturas_pdf(current_user: Optional[dict] = Depends(get_current_user)):
    """Descarga el catálogo de nomenclaturas MV en PDF RELLENABLE (56 familias con
    dibujo, códigos, anchos y recuadros editables). Solo master."""
    if not _es_master(current_user):
        raise HTTPException(status_code=403, detail="Solo el master puede descargar las nomenclaturas.")
    import io as _io
    from fastapi.responses import StreamingResponse
    try:
        from services.nomenclaturas_pdf import build_nomenclaturas_pdf
        pdf = build_nomenclaturas_pdf()
    except Exception as e:
        logger.error("nomenclaturas pdf: %s", e)
        raise HTTPException(status_code=500, detail=f"No se pudo generar el PDF: {e}")
    return StreamingResponse(
        _io.BytesIO(pdf),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="Nomenclaturas_MV_rellenable.pdf"'},
    )


# ─── PROYECTOS DE PROFORMA ALVIC (guardar/cargar con metadatos) ─────────────────
@router.post("/cascos/proforma/proyectos")
async def guardar_proforma_proyecto(payload: dict, current_user: Optional[dict] = Depends(get_current_user)):
    """Guarda un proyecto de proforma Alvic (items + overrides + parámetros de costes). Solo MASTER."""
    if not _es_master(current_user):
        raise HTTPException(status_code=403, detail="Solo el master puede guardar proyectos de proforma.")
    uid = (current_user or {}).get("id") or "anonymous"
    pid = (payload or {}).get("id") or f"prof-{uuid.uuid4().hex[:10]}"
    now = datetime.now(timezone.utc).isoformat()
    existing = await _get_db().proforma_proyectos.find_one({"id": pid}, {"_id": 0, "createdAt": 1})
    doc = {
        "id": pid,
        "userId": uid,
        "nombre": str((payload or {}).get("nombre") or "Sin nombre"),
        "items": (payload or {}).get("items") or [],
        "overrides": (payload or {}).get("overrides") or {},
        "parametros": (payload or {}).get("parametros") or {},
        "precioM2Puerta": (payload or {}).get("precioM2Puerta") or "",
        "createdAt": (existing or {}).get("createdAt") or now,
        "updatedAt": now,
    }
    await _get_db().proforma_proyectos.update_one({"id": pid}, {"$set": doc}, upsert=True)
    doc.pop("_id", None)
    return {"success": True, "proyecto": doc}


@router.get("/cascos/proforma/proyectos")
async def listar_proforma_proyectos(current_user: Optional[dict] = Depends(get_current_user)):
    """Lista los proyectos de proforma del usuario actual. Solo MASTER."""
    if not _es_master(current_user):
        raise HTTPException(status_code=403, detail="Solo el master puede ver proyectos de proforma.")
    uid = (current_user or {}).get("id") or ""
    query = {"userId": uid} if uid else {}
    proyectos = await _get_db().proforma_proyectos.find(query, {"_id": 0}).sort("updatedAt", -1).to_list(200)
    return {"success": True, "proyectos": proyectos}


@router.get("/cascos/proforma/proyectos/{proyecto_id}")
async def obtener_proforma_proyecto(proyecto_id: str, current_user: Optional[dict] = Depends(get_current_user)):
    """Obtiene un proyecto de proforma por ID. Solo MASTER."""
    if not _es_master(current_user):
        raise HTTPException(status_code=403, detail="Solo el master puede ver proyectos de proforma.")
    doc = await _get_db().proforma_proyectos.find_one({"id": proyecto_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado.")
    return {"success": True, "proyecto": doc}


@router.delete("/cascos/proforma/proyectos/{proyecto_id}")
async def borrar_proforma_proyecto(proyecto_id: str, current_user: Optional[dict] = Depends(get_current_user)):
    """Borra un proyecto de proforma. Solo MASTER."""
    if not _es_master(current_user):
        raise HTTPException(status_code=403, detail="Solo el master puede borrar proyectos de proforma.")
    await _get_db().proforma_proyectos.delete_one({"id": proyecto_id})
    return {"success": True}
