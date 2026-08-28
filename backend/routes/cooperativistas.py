# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
EL ÁREA DEL COOPERATIVISTA, Y LA ASIGNACIÓN DE PEDIDOS.

Siete rutas y ni una más:

  GET  /api/cooperativistas/mi-area        lo que ve un montador o un comercial
  GET  /api/cooperativistas/socios         quién es socio, para elegirlo (master)
  GET  /api/cooperativistas/pedidos        pedidos y su asignación de hoy (master)
  POST /api/cooperativistas/asignar        el master pone quién vendió y quién montó
  GET  /api/cooperativistas/liquidacion    lo que hay que pagar este mes (master)
  POST /api/cooperativistas/aplicar-sugerencias  el montador que dice la agenda
  POST /api/cooperativistas/liquidar       cierra el mes: paga y congela (master)

EL FILTRO NO SE ESCRIBE AQUÍ. Sale de `area_cooperativista.filtro_de(user)`, que
lo construye a partir del usuario del token. Nunca de un parámetro de la
petición: si el «de quién son los pedidos» viajara en la URL, cualquiera
cambiaría el número y vería la nómina del compañero. Es el mismo fallo que tenía
el motor de render antes del 25/08 —la pantalla ofrecía lo correcto y la API se
fiaba de lo que le mandaran—, y se arregla igual: decidiéndolo en el servidor a
partir de quién eres.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from routes.cascos import _es_master
from services import area_cooperativista as AC
from services import comisiones as C
from services import enlace_documentos as ED
from services import enlace_montador as EM
from services import origen_pedidos as OP
from services import liquidaciones as L
from services.jwt_service import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/cooperativistas", tags=["cooperativistas"])


def _db():
    from server import db
    return db


async def _guardar_en_el_pedido(pedido_id: str, cambios: dict,
                                condicion: Optional[dict] = None):
    """Escribe en el pedido, esté en la colección que esté.

    Cocina Desmontada guarda en `cascos_orders` y las secciones de siempre en
    `orders`. Escribir siempre en `orders` —como se hacía— dejaba SIN EFECTO
    asignar un comercial o liquidar un pedido de Desmontada: la llamada
    respondía que sí y no cambiaba nada, que es la peor forma de fallar.

    Devuelve cuántos documentos se han modificado. La condición viaja dentro del
    `update` para que dos pulsaciones a la vez no puedan pisarse.
    """
    consulta = {"id": pedido_id, **(condicion or {})}
    tocados = 0
    for coleccion in (_db().orders, _db().cascos_orders):
        try:
            r = await coleccion.update_one(consulta, {"$set": cambios})
            tocados += r.modified_count
        except Exception as e:                               # noqa: BLE001
            logger.error(f"no se pudo escribir en {pedido_id}: {e}")
    return tocados


async def _pedidos_de_la_cooperativa(filtro: Optional[dict] = None) -> list:
    """Los pedidos que cuentan: Cocina Montada 3 y Cocina Desmontada, y ni uno más.

    El master, 28/08: «solo lista los pedidos que se hayan realizado desde
    Cocina Montada 3 o Cocina Desmontada». El ERP los guarda en sitios
    distintos: Desmontada en `cascos_orders` y las secciones VIEJAS en `orders`.
    Salían todos, incluidos los de la primera sección de fábrica.

    La lista es BLANCA (`services/origen_pedidos.py`): se dice qué entra, no qué
    se excluye. Con una lista negra, una sección nueva del ERP entraría sola en
    la nómina el día que alguien la añada.
    """
    f = filtro or {}
    try:
        de_orders = await _db().orders.find(f, {"_id": 0}).to_list(2000)
    except Exception as e:                                   # noqa: BLE001
        logger.error(f"no se pudieron leer los pedidos: {e}")
        de_orders = []
    try:
        crudos_cascos = await _db().cascos_orders.find(
            {**f, "kind": OP.KIND_PEDIDO}, {"_id": 0}).to_list(2000)
    except Exception as e:                                   # noqa: BLE001
        logger.error(f"no se pudieron leer los pedidos de Cocina Desmontada: {e}")
        crudos_cascos = []
    de_cascos = [OP.normaliza_pedido_de_cascos(d) for d in crudos_cascos]
    return OP.solo_los_que_cuentan(de_orders + de_cascos)


async def _familia_por_codigo() -> dict:
    """`código de producto` → familia MV (`B60D/I` → «BAJO»).

    Las líneas de un pedido guardan el CÓDIGO, no la familia, y sin la familia
    no se puede saber qué cuenta para la comisión: puertas y costados no
    incentivan. La familia vive en el catálogo, en `category`.
    """
    try:
        productos = await _db().products.find(
            {}, {"_id": 0, "code": 1, "category": 1}).to_list(20000)
    except Exception as e:                                   # noqa: BLE001
        logger.error(f"no se pudo leer el catálogo para clasificar líneas: {e}")
        return {}
    fuera = {}
    for pr in productos:
        cod = str((pr or {}).get("code") or "").strip().upper()
        cat = str((pr or {}).get("category") or "").strip().upper()
        if cod and cat:
            fuera[cod] = cat
    return fuera


async def _documentos():
    """Albaranes y facturas de Gestión Comercial, para saber qué se ha servido.

    Sin esto ningún pedido consolida nunca: `liquidaciones` espera `servidoAt` y
    `cobradoAt` en el pedido y no los escribe nadie — el ERP los tiene, pero en
    el albarán y en la factura (`services/enlace_documentos.py`).
    """
    try:
        return await _db().invoices.find({}, {"_id": 0}).to_list(5000)
    except Exception as e:                                   # noqa: BLE001
        logger.error(f"no se pudieron leer los documentos: {e}")
        return []


@router.get("/mi-area")
async def mi_area(current_user: Optional[dict] = Depends(get_current_user)):
    """Los tres montones de un cooperativista: en progreso, a cobrar y pagado."""
    filtro = AC.filtro_de(current_user)
    if filtro is None:
        raise HTTPException(
            status_code=403,
            detail="Esta área es de los cooperativistas: montadores y comerciales.")
    try:
        pedidos = ED.enriquecer_todos(
            await _pedidos_de_la_cooperativa(filtro), await _documentos())
    except Exception as e:                                   # noqa: BLE001
        logger.error(f"mi-area: no se pudieron leer los pedidos: {e}")
        raise HTTPException(status_code=500, detail="No se pudo leer tu área.")

    mano = 0.0
    if AC.rol_de(current_user) == AC.MONTADOR:
        # La comisión del montador ES la mano de obra por mueble que teclea el
        # master en Rentabilidad MV (CLAUDE.md, regla 16). No tiene fórmula
        # propia a propósito: dos números para lo mismo acaban sin cuadrar.
        try:
            aj = await _db().settings.find_one({"id": "global-settings"}, {"_id": 0}) or {}
            # Su cifra si la tiene, si no la de la casa (services/comisiones.py).
            mano = C.mano_de_obra_de(current_user, aj)
        except Exception:                                    # noqa: BLE001
            mano = C.mano_de_obra_de(current_user)

    return {"success": True,
            "area": AC.panel_de(current_user, pedidos, mano,
                                await _familia_por_codigo())}


@router.get("/socios")
async def socios(current_user: Optional[dict] = Depends(get_current_user)):
    """Quién es socio cooperativista, para poder elegirlo al asignar. SOLO master.

    Va cerrado por lo mismo que `asignar`: esta lista es «quién cobra en esta
    casa». Y sale por la lista BLANCA de `socio_publico`, no volcando el usuario
    entero — dentro del documento hay contraseña, descuentos y permisos.
    """
    if not _es_master(current_user):
        raise HTTPException(status_code=403, detail="La lista de socios es del master.")
    try:
        usuarios = await _db().users.find({}, {"_id": 0}).to_list(2000)
    except Exception as e:                                   # noqa: BLE001
        logger.error(f"socios: no se pudieron leer los usuarios: {e}")
        raise HTTPException(status_code=500, detail="No se pudo leer la lista de socios.")
    return {"success": True, "socios": AC.socios_de(usuarios)}


@router.get("/pedidos")
async def pedidos_para_asignar(current_user: Optional[dict] = Depends(get_current_user)):
    """Los pedidos y quién los tiene asignados hoy. SOLO master.

    Los que están SIN ASIGNAR van primero: son los que no le pagan a nadie, y
    son justo los que hay que ver. Un pedido servido y cobrado sin comercial ni
    montador no da ningún error — simplemente no aparece en la nómina de nadie,
    y de eso no se entera nunca el que tenía que cobrar.
    """
    if not _es_master(current_user):
        raise HTTPException(
            status_code=403,
            detail="Asignar comercial o montador es del master: decide quién cobra.")
    try:
        crudos = await _pedidos_de_la_cooperativa()
        crudos.sort(key=lambda o: str(o.get("confirmedAt") or ""), reverse=True)
        usuarios = await _db().users.find({}, {"_id": 0}).to_list(2000)
    except Exception as e:                                   # noqa: BLE001
        logger.error(f"pedidos: no se pudieron leer: {e}")
        raise HTTPException(status_code=500, detail="No se pudieron leer los pedidos.")

    socios = AC.socios_de(usuarios)
    nombres = {f["id"]: f["nombre"]
               for f in socios["comerciales"] + socios["montadores"]}
    try:
        montajes = await _db().montajes.find({}, {"_id": 0}).to_list(5000)
    except Exception as e:                                   # noqa: BLE001
        logger.error(f"pedidos: no se pudieron leer los montajes: {e}")
        montajes = []
    # La agenda ya sabe quién montó cada cocina. Se PROPONE; asignar sigue
    # siendo del master (services/enlace_montador.py).
    propuestas = EM.sugerencias(crudos, montajes, usuarios)

    familias = await _familia_por_codigo()
    lista = [AC.pedido_para_asignar(o, nombres, familias) for o in crudos]
    for fila in lista:
        fila["sugerencia"] = propuestas.get(fila["pedidoId"])
    lista.sort(key=lambda p: (not p["sinAsignar"], p["fecha"]), reverse=False)
    lista.sort(key=lambda p: p["sinAsignar"], reverse=True)
    return {"success": True, "pedidos": lista, "socios": socios,
            "sinAsignar": sum(1 for p in lista if p["sinAsignar"]),
            "sugerencias": sum(1 for p in lista if p.get("sugerencia"))}


@router.post("/asignar")
async def asignar(payload: dict, current_user: Optional[dict] = Depends(get_current_user)):
    """Quién vendió y quién montó un pedido. SOLO el master.

    Va cerrado porque esto decide quién cobra: cambiar el comercial de un pedido
    es mover una comisión de un bolsillo a otro.
    """
    if not _es_master(current_user):
        raise HTTPException(
            status_code=403,
            detail="Asignar comercial o montador es del master: decide quién cobra.")

    pedido_id = (payload or {}).get("pedidoId")
    if not pedido_id:
        raise HTTPException(status_code=400, detail="Falta el pedido.")

    cambios = {}
    for clave in ("comercialUserId", "montadorUserId"):
        if clave in (payload or {}):
            cambios[clave] = str(payload.get(clave) or "")
    if not cambios:
        raise HTTPException(status_code=400, detail="No hay nada que asignar.")

    if not await _guardar_en_el_pedido(pedido_id, cambios):
        raise HTTPException(
            status_code=404,
            detail="Ese pedido no existe o ya estaba asignado a esa persona.")
    return {"success": True, "pedidoId": pedido_id, "asignado": cambios}


@router.post("/liquidar")
async def liquidar(payload: dict, current_user: Optional[dict] = Depends(get_current_user)):
    """Cierra el mes de un cooperativista: paga y CONGELA. SOLO el master.

    Hasta ahora `liquidadoEn` se leía en todas partes y no lo escribía nadie, así
    que el estado LIQUIDADA no existía: la misma comisión podía entrar en la
    liquidación de septiembre, la de octubre y la de noviembre, y el ERP no
    tenía forma de saberlo. «Liquidada = ya pagada, no vuelve a entrar nunca»
    (CLAUDE.md, regla 17) era una intención escrita, no una barrera.

    Al cerrar se guarda EN CADA PEDIDO lo que se ha pagado por él. Desde ese
    momento esos euros no se recalculan: cambiar mañana la mano de obra de un
    montador ya no mueve hacia atrás lo que se le pagó en agosto.

    ES IDEMPOTENTE: un pedido que ya lleva `liquidadoEn` se salta. Volver a
    pulsar no paga dos veces, que es el error que no se puede permitir aquí.
    """
    if not _es_master(current_user):
        raise HTTPException(status_code=403, detail="Liquidar es del master.")

    usuario = str(payload.get("usuario") or "").strip()
    periodo = str(payload.get("periodo") or "").strip()
    if not usuario or not periodo:
        raise HTTPException(status_code=400, detail="Faltan el periodo o el usuario.")

    u = await _db().users.find_one({"id": usuario}, {"_id": 0})
    if not u:
        raise HTTPException(status_code=404, detail="Ese usuario no existe.")
    rol = AC.rol_de(u)
    if not rol:
        raise HTTPException(status_code=400, detail="Ese usuario no es cooperativista.")

    filtro = AC.filtro_de(u)
    try:
        crudos = ED.enriquecer_todos(
            await _pedidos_de_la_cooperativa(filtro), await _documentos())
        aj = await _db().settings.find_one({"id": "global-settings"}, {"_id": 0}) or {}
    except Exception as e:                                   # noqa: BLE001
        logger.error(f"liquidar: no se pudieron leer los pedidos: {e}")
        raise HTTPException(status_code=500, detail="No se pudo leer la liquidación.")

    mano = C.mano_de_obra_de(u, aj) if rol == AC.MONTADOR else 0.0
    familias = await _familia_por_codigo()

    pagados, total, ya_estaban = [], 0.0, 0
    for crudo in crudos:
        if crudo.get("liquidadoEn"):
            ya_estaban += 1
            continue
        n = AC.normaliza_pedido(crudo, mano, familias)
        if L.estado_de(n) != L.CONSOLIDADA:
            continue
        if L.periodo_de_consolidacion(n) != periodo:
            continue
        congelada = L.congelar(n, rol, periodo)
        try:
            await _guardar_en_el_pedido(
                crudo.get("id"),
                {"liquidadoEn": periodo, L.CONGELADA: congelada},
                {"liquidadoEn": {"$in": [None, ""]}})
        except Exception as e:                               # noqa: BLE001
            logger.error(f"liquidar: no se pudo cerrar {crudo.get('id')}: {e}")
            raise HTTPException(
                status_code=500,
                detail="No se pudo cerrar la liquidación; no se ha pagado nada más.")
        pagados.append({"pedidoId": crudo.get("id"), "euros": congelada["euros"],
                        "muebles": congelada["muebles"]})
        total += congelada["euros"]

    return {"success": True, "periodo": periodo, "rol": rol,
            "pedidos": pagados, "total": round(total, 2),
            "yaLiquidados": ya_estaban}


@router.post("/aplicar-sugerencias")
async def aplicar_sugerencias(current_user: Optional[dict] = Depends(get_current_user)):
    """Pone el montador que dice la agenda, en los pedidos que no tienen ninguno.

    SOLO el master, y solo porque es él quien pulsa: la sugerencia sale de la
    agenda de montajes, pero aplicarla es una decisión suya (regla 20).

    NO PISA NADA. Solo se tocan los pedidos SIN montador, y la condición va
    dentro del `update`, para que dos pulsaciones a la vez no puedan cambiarle
    el montador a un pedido que acaba de asignarse.
    """
    if not _es_master(current_user):
        raise HTTPException(
            status_code=403,
            detail="Asignar comercial o montador es del master: decide quién cobra.")
    try:
        pedidos = await _pedidos_de_la_cooperativa()
        usuarios = await _db().users.find({}, {"_id": 0}).to_list(2000)
        montajes = await _db().montajes.find({}, {"_id": 0}).to_list(5000)
    except Exception as e:                                   # noqa: BLE001
        logger.error(f"aplicar-sugerencias: no se pudo leer: {e}")
        raise HTTPException(status_code=500, detail="No se pudo leer la agenda.")

    propuestas = EM.sugerencias(pedidos, montajes, usuarios)
    puestos = []
    for pedido_id, s in propuestas.items():
        if not pedido_id:
            continue
        try:
            tocados = await _guardar_en_el_pedido(
                pedido_id, {"montadorUserId": s["montadorUserId"]},
                {"montadorUserId": {"$in": [None, ""]}})
        except Exception as e:                               # noqa: BLE001
            logger.error(f"aplicar-sugerencias: {pedido_id}: {e}")
            continue
        if tocados:
            puestos.append({"pedidoId": pedido_id, "nombre": s["nombre"]})
    return {"success": True, "asignados": puestos, "total": len(puestos)}


@router.get("/liquidacion")
async def liquidacion(periodo: str, usuario: str,
                      current_user: Optional[dict] = Depends(get_current_user)):
    """Lo que hay que pagarle a alguien este mes. SOLO el master.

    Aquí SÍ viaja el usuario en la petición, y por eso está cerrado al master: es
    la vista de quien paga, no la de quien cobra.
    """
    if not _es_master(current_user):
        raise HTTPException(status_code=403, detail="La liquidación es del master.")
    if not periodo or not usuario:
        raise HTTPException(status_code=400, detail="Faltan el periodo o el usuario.")

    u = await _db().users.find_one({"id": usuario}, {"_id": 0})
    if not u:
        raise HTTPException(status_code=404, detail="Ese usuario no existe.")
    rol = AC.rol_de(u)
    if not rol:
        raise HTTPException(status_code=400, detail="Ese usuario no es cooperativista.")

    filtro = AC.filtro_de(u)
    pedidos = ED.enriquecer_todos(
        await _pedidos_de_la_cooperativa(filtro), await _documentos())
    mano = 0.0
    if rol == AC.MONTADOR:
        aj = await _db().settings.find_one({"id": "global-settings"}, {"_id": 0}) or {}
        # La del montador que se está liquidando, no la de quien mira.
        mano = C.mano_de_obra_de(u, aj)
    familias = await _familia_por_codigo()
    normalizados = [AC.normaliza_pedido(p, mano, familias) for p in pedidos]
    return {"success": True, "liquidacion": L.liquidacion_del_mes(normalizados, rol, periodo)}
