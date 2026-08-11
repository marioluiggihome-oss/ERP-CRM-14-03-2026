# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
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


# ─── EXPEDIENTE DE UNA OBRA DE COCINA DESMONTADA ────────────────────────────
#
# «Desmontada tiene que tener expediente también». No se convierte el pedido en
# proyecto —eso duplicaría la obra en dos sitios y al día siguiente uno de los
# dos estaría desactualizado—: se TRADUCE al vuelo y los motores de siempre
# hacen el resto. Ver `services/expediente_origen.py`.

async def _pedido_o_404(order_id: str, current_user: Optional[dict]) -> dict:
    doc = await _get_db().cascos_orders.find_one({"id": order_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Ese pedido de cascos no existe.")
    if not _can_access(doc, current_user):
        raise HTTPException(status_code=403, detail="Sin acceso a este pedido")
    return doc


@router.get("/cascos/orders/{order_id}/expediente")
async def expediente_de_pedido(order_id: str, current_user: Optional[dict] = Depends(get_current_user)):
    """El expediente de una obra de Cocina Desmontada.

    Mismo expediente, misma validación y mismas medidas que Cocina Montada: lo
    único que cambia es de dónde salen los datos.
    """
    pedido = await _pedido_o_404(order_id, current_user)
    vista = expediente_origen.desde_pedido_casco(pedido)
    pendientes = cambios_sin_aprobar(vista.get("cambios"))
    val = validar(vista, pendientes_cambios=len(pendientes))
    return {"success": True,
            "origen": vista["origen"], "origenEtiqueta": vista["origenEtiqueta"],
            **montar_expediente(vista, val, pendientes, current_user)}


@router.get("/cascos/orders/{order_id}/medidas")
async def medidas_de_pedido(order_id: str, tolerancia: float = 0,
                            current_user: Optional[dict] = Depends(get_current_user)):
    pedido = await _pedido_o_404(order_id, current_user)
    return {"success": True, **medicion_obra.revisar(pedido.get("medidas"), tolerancia)}


@router.put("/cascos/orders/{order_id}/medidas")
async def guardar_medidas_de_pedido(order_id: str, payload: dict,
                                    current_user: Optional[dict] = Depends(get_current_user)):
    """Guarda la lista de medidas SIN tocar niveles.

    Se escriben en el propio pedido, con `$set` de un solo campo: así el
    trabajo de la pantalla de Cocina Desmontada no las pisa al volver a
    guardar, ni ellas pisan lo suyo.
    """
    await _pedido_o_404(order_id, current_user)
    medidas = payload.get("medidas")
    if not isinstance(medidas, list):
        raise HTTPException(status_code=422, detail="Hace falta una lista de medidas.")
    sin_clave = [i for i, m in enumerate(medidas) if not str((m or {}).get("clave") or "").strip()]
    if sin_clave:
        raise HTTPException(
            status_code=422,
            detail=f"Estas medidas no tienen nombre y no se podrían volver a encontrar: {sin_clave}.")
    await _get_db().cascos_orders.update_one({"id": order_id}, {"$set": {"medidas": medidas}})
    return {"success": True, **medicion_obra.revisar(medidas)}


async def _nivel_de_medida(order_id: str, clave: str, payload: dict,
                           current_user: Optional[dict], accion: str):
    """Tomar o confirmar. Es la misma operación con distinto nombre, y por eso
    está escrita una vez."""
    pedido = await _pedido_o_404(order_id, current_user)
    medidas = list(pedido.get("medidas") or [])
    idx = next((i for i, m in enumerate(medidas)
                if str((m or {}).get("clave") or "").strip() == clave), None)
    if idx is None:
        raise HTTPException(status_code=404, detail=f"Este pedido no tiene ninguna medida «{clave}».")

    quien = (current_user or {}).get("username") or (current_user or {}).get("email") or ""
    ahora = datetime.now(timezone.utc).isoformat()
    fn = medicion_obra.tomar if accion == "tomar" else medicion_obra.confirmar
    try:
        medidas[idx] = fn(medidas[idx], payload.get("valor"), quien=quien, cuando=ahora)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    await _get_db().cascos_orders.update_one({"id": order_id}, {"$set": {"medidas": medidas}})
    return {"success": True, "medida": medicion_obra.revisar_una(medidas[idx]),
            **medicion_obra.revisar(medidas)}


@router.post("/cascos/orders/{order_id}/medidas/{clave}/tomar")
async def tomar_medida_de_pedido(order_id: str, clave: str, payload: dict,
                                 current_user: Optional[dict] = Depends(get_current_user)):
    return await _nivel_de_medida(order_id, clave, payload, current_user, "tomar")


@router.post("/cascos/orders/{order_id}/medidas/{clave}/confirmar")
async def confirmar_medida_de_pedido(order_id: str, clave: str, payload: dict,
                                     current_user: Optional[dict] = Depends(get_current_user)):
    return await _nivel_de_medida(order_id, clave, payload, current_user, "confirmar")


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
# OJO: master de verdad, no "rol alto". ADMIN_ROLE_FLAGS incluye isGerente e
# isDirectorComercial, que sirven para ver Cascos pero NO para esto: por aquí
# pasan la tarifa del proveedor, el descuento y el margen. La pantalla ya lo
# cierra a master, y si aquí se dejara la lista ancha el cierre sería de adorno
# (basta llamar a la API a mano).
_MASTER_FLAGS = ("isAdmin", "isPrimaryAdmin", "isMaster")


def _es_master(user: Optional[dict]) -> bool:
    return bool(user and any(user.get(f) for f in _MASTER_FLAGS))


_TAREAS_PROFORMA = set()
# Estado de los analisis de proforma en curso: {job_id: {...}}. En memoria, no en
# Mongo (ver _job_set). Se limpia solo en _job_limpiar.
_JOBS = {}

_PROMPT_PROFORMA = (
    "Esta imagen es una página de una PROFORMA de muebles de cocina (cascos). "
    "Extrae la tabla de artículos. Devuelve SOLO un JSON: {\"items\":[{\"n\":1,"
    "\"cod\":\"80GF/1P1GIN\",\"descripcion\":\"...\",\"material\":\"MELAMINA ... ZENIT - MERIVOBOX\","
    "\"largo\":800,\"ancho\":500,\"grueso\":580,\"cantidad\":1,\"pvp\":402.73,\"importe\":402.73}]}. "
    "'pvp' es la columna PRECIO (por unidad) e 'importe' es el TOTAL de la fila "
    "(precio × cantidad); si la tabla solo trae una de las dos, pon null en la otra. "
    "'cantidad' son las unidades de la fila: cópiala, es la que multiplica el importe. "
    "Si una fila no es un mueble, inclúyela igual. "
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
        # Total de la linea: manda el importe de la proforma; si no viene, se
        # calcula precio x unidades. Antes era `total = pvp` a secas, asi que
        # una fila de 2 unidades contaba como una y el total salia corto.
        try:
            uds = float(r.get("cantidad") or 1.0) or 1.0
        except (TypeError, ValueError):
            uds = 1.0
        try:
            precio = float(r.get("pvp")) if r.get("pvp") is not None else None
        except (TypeError, ValueError):
            precio = None
        try:
            importe = float(r.get("importe")) if r.get("importe") is not None else None
        except (TypeError, ValueError):
            importe = None
        total = importe if importe is not None else (precio * uds if precio is not None else None)
        items.append({
            "n": r.get("n"), "cod": r.get("cod") or "", "descripcion": desc,
            "material": material, "color": color, "herrajeBlum": blum,
            "largo": r.get("largo"), "ancho": r.get("ancho"), "grueso": r.get("grueso"),
            "cantidad": uds, "pvp": precio, "total": total,
            "puertas": fr["puertas"], "cajones": fr["cajones"], "gavetas": fr["gavetas"],
            "tipo": _tipo_mueble(desc), "esMueble": True,
        })
    return items


def _frentes_mv(m: dict) -> tuple:
    """Puertas, cajones y gavetas de un mueble MV.

    Regla de la casa (memoria del proyecto): un código con D/I lleva 1 puerta y
    uno sin D/I lleva 2; los cajones y gavetas van en el nombre de la familia
    (BAJO_3CAJ_1GAV). De aquí salen las bisagras del cálculo de herraje.
    """
    import re as _re
    fam = (m.get("familia") or "").upper()
    cajones = sum(int(x) for x in _re.findall(r"(\d)\s*CAJ", fam))
    gavetas = sum(int(x) for x in _re.findall(r"(\d)\s*GAV", fam))
    if cajones or gavetas:
        return 0, cajones, gavetas
    cod = (m.get("cod") or "").upper()
    puertas = 1 if ("D/I" in cod or m.get("mano")) else 2
    return puertas, 0, 0


def _relacion_mv_como_items(pdf_bytes: bytes):
    """Lee la plantilla de nomenclaturas MV rellenada y la deja con la misma
    forma que las líneas de una proforma, para que el resto del importador
    (equivalencia ACB, herraje, mano de obra, pedidos) funcione igual.

    Devuelve None si el PDF no es una relación MV.
    """
    from services.mv_relacion import detectar_relacion, extract_campos
    # SOLO se trata como relación MV si el PDF trae RECUADROS RELLENADOS, que es
    # lo que identifica a la plantilla de nomenclaturas. Sin este freno, una
    # proforma normal con una línea del tipo "2 BAJO 600" se colaría por aquí y
    # se leería con la tarifa MV en vez de con el lector de proformas.
    if not extract_campos(pdf_bytes):
        return None
    leido = detectar_relacion(pdf_bytes)
    muebles = leido.get("muebles") or []
    if not muebles:
        return None
    # Y además la mayoría tiene que existir de verdad en la tarifa: si casi nada
    # encaja, esto no era una relación MV.
    encontrados = sum(1 for m in muebles if m.get("encontrado"))
    if encontrados * 2 < len(muebles):
        return None
    # Lo que se escribió y NO se supo leer viaja con el resultado: es preferible
    # decir "esto no lo he entendido" a dejarlo caer en silencio.
    no_leidas = leido.get("noLeidas") or []
    items = []
    for n, m in enumerate(muebles, start=1):
        fam = (m.get("familia") or m.get("tipo") or "").replace("_", " ").strip()
        ancho_cm = m.get("ancho")
        desc = " ".join(x for x in [fam, str(ancho_cm) if ancho_cm else ""] if x).strip()
        puertas, cajones, gavetas = _frentes_mv(m)
        items.append({
            "n": n,
            "cod": m.get("cod") or (m.get("raw") or "").upper(),
            "descripcion": desc or (m.get("raw") or "").upper(),
            "material": "", "color": "", "herrajeBlum": False,
            # La tarifa MV va en cm y el resto del importador trabaja en mm.
            "largo": (m["alto"] * 10) if m.get("alto") else None,
            "ancho": (ancho_cm * 10) if ancho_cm else None,
            "grueso": (m["fondo"] * 10) if m.get("fondo") else None,
            "cantidad": float(m.get("qty") or 1),
            # El PVP de MV es precio de VENTA, no el coste de un proveedor: no se
            # mete en la columna de la proforma para no mezclar tarifas. Viaja
            # aparte, por si hace falta compararlo.
            "pvp": None, "total": None,
            "pvpMv": m.get("pvp"), "puntosMv": m.get("pts"),
            "puertas": puertas, "cajones": cajones, "gavetas": gavetas,
            "tipo": (m.get("tipo") or "").lower() or None,
            "esMueble": True, "origen": "mv", "encontrado": bool(m.get("encontrado")),
        })
    return {"items": items, "noLeidas": no_leidas}


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

    # 0) ¿Es la PLANTILLA DE NOMENCLATURAS MV rellenada? Lo que se escribe en los
    #    recuadros amarillos vive en los campos del formulario (AcroForm), NO en
    #    el texto de la página: la visión IA no los ve y se inventaba las líneas
    #    (todas a 48 €, sin código ni descripción). Aquí se leen de forma
    #    determinista contra la tarifa MV, sin IA de por medio.
    try:
        mv = await _asyncio.get_running_loop().run_in_executor(
            None, _relacion_mv_como_items, pdf_bytes)
    except Exception as e:
        logger.warning("proforma: fallo al probar la relación MV: %s", e)
        mv = None
    if mv and mv.get("items"):
        return {"success": True, "estado": "listo", "origen": "mv",
                "items": mv["items"], "count": len(mv["items"]),
                "noLeidas": mv.get("noLeidas") or []}

    # 1) Intento por CAPA DE TEXTO (rápido y exacto): se responde en el acto.
    # Va al executor porque PDFium es código nativo bloqueante y el servidor
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
from services import expediente_origen, medicion_obra
from services.validacion_fabricacion import validar
from services.expediente import montar as montar_expediente
from services.cambios_proyecto import cambios_sin_aprobar
_MV_PATH = _mvos.path.join(_mvos.path.dirname(_mvos.path.dirname(__file__)), "data", "mv_tarifas_oficiales.json")


@router.get("/cascos/mv/tarifas")
async def mv_tarifas(current_user: Optional[dict] = Depends(get_current_user)):
    """Las tarifas MV disponibles, CADA UNA CON SUS ACABADOS.

    Hasta ahora la pantalla pedía siempre T1, escrito a fuego: se presupuestaba
    todo a la tarifa más barata aunque la cocina fuera un ZENIT (T4) o un FENIX
    (T5). No daba ningún error — daba un presupuesto barato.

    Se devuelven los acabados porque es lo que se sabe al presupuestar: nadie
    dice «esta cocina es una T4», dice «esta cocina es ZENIT». Elegir por número
    de tarifa es pedirle al comercial que se sepa la tabla de memoria.
    """
def _can_use_mv(user: Optional[dict]) -> bool:
    return True


@router.get("/cascos/mv/tarifas")
async def mv_tarifas(current_user: Optional[dict] = Depends(get_current_user)):
    """Las tarifas MV disponibles, CADA UNA CON SUS ACABADOS.

    Hasta ahora la pantalla pedía siempre T1, escrito a fuego: se presupuestaba
    todo a la tarifa más barata aunque la cocina fuera un ZENIT (T4) o un FENIX
    (T5). No daba ningún error — daba un presupuesto barato.

    Se devuelven los acabados porque es lo que se sabe al presupuestar: nadie
    dice «esta cocina es una T4», dice «esta cocina es ZENIT». Elegir por número
    de tarifa es pedirle al comercial que se sepa la tabla de memoria.
    """
    if not _can_use_mv(current_user):
        raise HTTPException(status_code=403, detail="Sin permiso para consultar tarifas MV.")
    try:
        with open(_MV_PATH, "r", encoding="utf-8") as f:
            data = _mvjson.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"No se pudo leer la tarifa MV: {e}")

    acabados_meta = (data.get("_meta", {}) or {}).get("acabados", {}) or {}
    tarifas = []
    for clave in data.get("tariffs", {}):
        # `_inc` no es un acabado: son incrementos (metalizado, difuminado).
        acabados = [a for a in (acabados_meta.get(clave) or {}) if not a.startswith("_")]
        tarifas.append({
            "tarifa": clave,
            "acabados": acabados,
            "n": int(clave[1:]) if clave[1:].isdigit() else 999,
        })
    tarifas.sort(key=lambda t: t["n"])
    return {
        "success": True,
        "pointValue": data.get("_meta", {}).get("pointValue", 3.33),
        "tarifas": [{"tarifa": t["tarifa"], "acabados": t["acabados"]} for t in tarifas],
    }


@router.get("/cascos/mv/tarifa")
async def mv_tarifa(tariff: str = "T1", current_user: Optional[dict] = Depends(get_current_user)):
    """Devuelve la tarifa MV pedida (por defecto T1) con sus códigos y puntos, y el
    valor de punto. Para el módulo de Rentabilidad Tarifa MV."""
    if not _can_use_mv(current_user):
        raise HTTPException(status_code=403, detail="Sin permiso para ver la tarifa MV.")
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
    if not _can_use_mv(current_user):
        raise HTTPException(status_code=403, detail="Sin permiso para importar o analizar relaciones MV.")
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
        from services.mv_relacion import detectar_relacion
        leido = detectar_relacion(pdf_bytes, tariff)
        muebles = leido.get("muebles") or []
        no_leidas = leido.get("noLeidas") or []
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
        # Lo escrito que no se ha sabido leer. Sin esto, esas lineas valian 0 y
        # el total salia corto sin que nadie se enterase.
        "noLeidas": no_leidas,
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
        # Retoques hechos linea a linea en la tabla: mano de obra, precio de
        # puerta, medidas corregidas, destino de pedido y lineas descartadas.
        # Sin guardarlos, al reabrir el proyecto se perdia el trabajo manual.
        "moLinea": (payload or {}).get("moLinea") or {},
        "puertaLinea": (payload or {}).get("puertaLinea") or {},
        "destinoLinea": (payload or {}).get("destinoLinea") or {},
        "excluidas": (payload or {}).get("excluidas") or {},
        "puertasEditadas": (payload or {}).get("puertasEditadas") or {},
        "deletedRows": (payload or {}).get("deletedRows") or [],
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
