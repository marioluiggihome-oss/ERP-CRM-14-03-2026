# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
EL ÁREA DEL COOPERATIVISTA, Y LA ASIGNACIÓN DE PEDIDOS.

Seis rutas y ni una más:

  GET  /api/cooperativistas/mi-area        lo que ve un montador o un comercial
  GET  /api/cooperativistas/socios         quién es socio, para elegirlo (master)
  GET  /api/cooperativistas/pedidos        pedidos y su asignación de hoy (master)
  POST /api/cooperativistas/asignar        el master pone quién vendió y quién montó
  GET  /api/cooperativistas/liquidacion    lo que hay que pagar este mes (master)
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
from services import liquidaciones as L
from services.jwt_service import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/cooperativistas", tags=["cooperativistas"])


def _db():
    from server import db
    return db


@router.get("/mi-area")
async def mi_area(current_user: Optional[dict] = Depends(get_current_user)):
    """Los tres montones de un cooperativista: en progreso, a cobrar y pagado."""
    filtro = AC.filtro_de(current_user)
    if filtro is None:
        raise HTTPException(
            status_code=403,
            detail="Esta área es de los cooperativistas: montadores y comerciales.")
    try:
        pedidos = await _db().orders.find(filtro, {"_id": 0}).to_list(1000)
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

    return {"success": True, "area": AC.panel_de(current_user, pedidos, mano)}


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
        crudos = await _db().orders.find({}, {"_id": 0}).sort("confirmedAt", -1).to_list(1000)
        usuarios = await _db().users.find({}, {"_id": 0}).to_list(2000)
    except Exception as e:                                   # noqa: BLE001
        logger.error(f"pedidos: no se pudieron leer: {e}")
        raise HTTPException(status_code=500, detail="No se pudieron leer los pedidos.")

    socios = AC.socios_de(usuarios)
    nombres = {f["id"]: f["nombre"]
               for f in socios["comerciales"] + socios["montadores"]}
    lista = [AC.pedido_para_asignar(o, nombres) for o in crudos]
    lista.sort(key=lambda p: (not p["sinAsignar"], p["fecha"]), reverse=False)
    lista.sort(key=lambda p: p["sinAsignar"], reverse=True)
    return {"success": True, "pedidos": lista, "socios": socios,
            "sinAsignar": sum(1 for p in lista if p["sinAsignar"])}


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

    r = await _db().orders.update_one({"id": pedido_id}, {"$set": cambios})
    if not r.matched_count:
        raise HTTPException(status_code=404, detail="Ese pedido no existe.")
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
        crudos = await _db().orders.find(filtro, {"_id": 0}).to_list(2000)
        aj = await _db().settings.find_one({"id": "global-settings"}, {"_id": 0}) or {}
    except Exception as e:                                   # noqa: BLE001
        logger.error(f"liquidar: no se pudieron leer los pedidos: {e}")
        raise HTTPException(status_code=500, detail="No se pudo leer la liquidación.")

    mano = C.mano_de_obra_de(u, aj) if rol == AC.MONTADOR else 0.0

    pagados, total, ya_estaban = [], 0.0, 0
    for crudo in crudos:
        if crudo.get("liquidadoEn"):
            ya_estaban += 1
            continue
        n = AC.normaliza_pedido(crudo, mano)
        if L.estado_de(n) != L.CONSOLIDADA:
            continue
        if L.periodo_de_consolidacion(n) != periodo:
            continue
        congelada = L.congelar(n, rol, periodo)
        try:
            await _db().orders.update_one(
                {"id": crudo.get("id"), "liquidadoEn": {"$in": [None, ""]}},
                {"$set": {"liquidadoEn": periodo, L.CONGELADA: congelada}})
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
    pedidos = await _db().orders.find(filtro, {"_id": 0}).to_list(2000)
    mano = 0.0
    if rol == AC.MONTADOR:
        aj = await _db().settings.find_one({"id": "global-settings"}, {"_id": 0}) or {}
        # La del montador que se está liquidando, no la de quien mira.
        mano = C.mano_de_obra_de(u, aj)
    normalizados = [AC.normaliza_pedido(p, mano) for p in pedidos]
    return {"success": True, "liquidacion": L.liquidacion_del_mes(normalizados, rol, periodo)}
