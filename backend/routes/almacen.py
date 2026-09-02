# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
almacen.py — EXISTENCIAS, RESERVAS Y PLAN DE COMPRA.

El motor de cálculo (`services/almacen.py`) y el armado de datos
(`services/almacen_datos.py`) son cálculo puro y están probados. Aquí solo se
lee y se escribe en la base de datos: ni una regla de negocio, para que lo que
decide se pueda seguir probando sin levantar Mongo.

DOS COLECCIONES
---------------
`almacen_stock`     — una ficha por referencia: {referencia, stock, minimo, ubicacion}
`almacen_reservas`  — lo apartado: {referencia, proyecto, cantidad, motivo}

POR QUÉ LA RESERVA LLEVA EL PROYECTO
------------------------------------
Porque «reservado» sin dueño no sirve: al mirar si a una cocina le falta
material hay que restar lo que tienen apartado LOS DEMÁS, no lo suyo. Sin el
proyecto en la reserva no se puede distinguir, y se acaba comprando material
que ya estaba apartado para esa misma obra.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime, timezone
import logging

from services import almacen, almacen_datos
from services.db_client import get_db as _get_db

logger = logging.getLogger(__name__)

from services.jwt_service import get_current_user, require_module_access
_DEPS = [Depends(require_module_access("canAccessAlmacen"))]

router = APIRouter(prefix="/almacen", tags=["almacen"], dependencies=_DEPS)


class FichaStock(BaseModel):
    referencia: str = Field(..., min_length=1)
    # `stock` y `minimo` admiten None A PROPÓSITO: «no se sabe» es un estado
    # legítimo y distinto de cero. Ver la nota de `almacen_datos`.
    stock: Optional[float] = None
    minimo: Optional[float] = None
    ubicacion: Optional[str] = ""


class Reserva(BaseModel):
    referencia: str = Field(..., min_length=1)
    proyecto: str = Field(..., min_length=1)
    cantidad: float = Field(..., gt=0)
    motivo: Optional[str] = ""


class PlanRequest(BaseModel):
    proyecto: str = Field(..., min_length=1)
    lineas: List[Dict] = Field(default_factory=list,
                               description="Líneas del despiece/pedido: {code|referencia, quantity|cantidad}")
    pedidos: Optional[Dict[str, float]] = Field(default=None,
                                                description="Lo que ya viene de camino, por referencia")


def _norm(v):
    return str(v or "").strip().upper()


# ─── Existencias ────────────────────────────────────────────────────────────

@router.get("/stock")
async def listar_stock():
    fichas = await _get_db().almacen_stock.find({}, {"_id": 0}).to_list(5000)
    return {"success": True, "fichas": fichas, "total": len(fichas)}


@router.put("/stock/{referencia}")
async def guardar_stock(referencia: str, ficha: FichaStock,
                        current_user: Optional[dict] = Depends(get_current_user)):
    """Da de alta o corrige la ficha de una referencia.

    La referencia se guarda NORMALIZADA (sin espacios, en mayúsculas) porque es
    la clave con la que se cruzan reservas y despiece: si una se guarda como
    « b60d » y otra como «B60D», no se encuentran y el plan de compra sale mal
    sin que nada falle.
    """
    ref = _norm(referencia)
    if not ref:
        raise HTTPException(status_code=422, detail="La referencia no puede estar vacía.")
    doc = {
        "referencia": ref,
        "stock": ficha.stock,
        "minimo": ficha.minimo,
        "ubicacion": (ficha.ubicacion or "").strip(),
        "actualizado": datetime.now(timezone.utc).isoformat(),
        "actualizadoPor": (current_user or {}).get("email") or "",
    }
    await _get_db().almacen_stock.update_one({"referencia": ref}, {"$set": doc}, upsert=True)
    return {"success": True, "ficha": doc}


@router.delete("/stock/{referencia}")
async def borrar_stock(referencia: str):
    r = await _get_db().almacen_stock.delete_one({"referencia": _norm(referencia)})
    return {"success": True, "borradas": r.deleted_count}


# ─── Reservas por proyecto ──────────────────────────────────────────────────

@router.get("/reservas")
async def listar_reservas(proyecto: Optional[str] = None):
    q = {"proyecto": _norm(proyecto)} if proyecto else {}
    reservas = await _get_db().almacen_reservas.find(q, {"_id": 0}).to_list(5000)
    return {"success": True, "reservas": reservas, "total": len(reservas)}


@router.post("/reservas")
async def crear_reserva(reserva: Reserva,
                        current_user: Optional[dict] = Depends(get_current_user)):
    """Aparta material para un proyecto.

    NO se comprueba aquí si hay stock suficiente, y es a propósito: apartar más
    de lo que hay es un dato real (se ha comprometido y hay que comprarlo), y
    el plan de compra lo va a decir. Bloquear la reserva escondería el problema
    en vez de enseñarlo.
    """
    doc = {
        "referencia": _norm(reserva.referencia),
        "proyecto": _norm(reserva.proyecto),
        "cantidad": float(reserva.cantidad),
        "motivo": (reserva.motivo or "").strip(),
        "creada": datetime.now(timezone.utc).isoformat(),
        "creadaPor": (current_user or {}).get("email") or "",
    }
    await _get_db().almacen_reservas.update_one(
        {"referencia": doc["referencia"], "proyecto": doc["proyecto"]},
        {"$set": doc}, upsert=True)
    return {"success": True, "reserva": doc}


@router.delete("/reservas")
async def borrar_reserva(referencia: str, proyecto: str):
    r = await _get_db().almacen_reservas.delete_one(
        {"referencia": _norm(referencia), "proyecto": _norm(proyecto)})
    return {"success": True, "borradas": r.deleted_count}


# ─── El enganche: del despiece al plan de compra ────────────────────────────

@router.post("/plan")
async def plan_de_compra(payload: PlanRequest):
    """Qué hay que comprar para este proyecto.

    Junta lo que necesita el despiece, lo que hay en la estantería, lo que
    tienen apartado LOS DEMÁS proyectos y lo que ya viene de camino. El cálculo
    lo hace el motor, que es quien sabe distinguir «no hay» de «no se sabe».
    """
    try:
        necesidades = almacen_datos.necesidades_del_despiece(payload.lineas)
        if not necesidades:
            raise HTTPException(
                status_code=422,
                detail=("Ninguna línea trae referencia, así que no hay nada que "
                        "cruzar con el almacén. Revisa que las líneas lleven código."))

        fichas = await _get_db().almacen_stock.find({}, {"_id": 0}).to_list(5000)
        reservas = await _get_db().almacen_reservas.find({}, {"_id": 0}).to_list(5000)

        lineas = almacen_datos.montar_lineas(
            necesidades, fichas, reservas, payload.proyecto, payload.pedidos)
        plan = almacen.plan_de_compra(lineas)

        # Las que nadie ha dado de alta van APARTE de las que están a cero: no
        # es lo mismo «existe y no queda» que «nadie la ha creado todavía», y
        # la acción a tomar es distinta.
        plan["sinFicha"] = almacen_datos.sin_ficha(necesidades, fichas)
        plan["reposicion"] = [
            l["referencia"] for l in lineas
            if almacen.necesita_reposicion(l["stock"], l["reservadoOtros"], l["minimo"])
        ]
        plan["lineas"] = lineas
        return {"success": True, **plan}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("plan de compra: %s", e, exc_info=True)
        raise HTTPException(status_code=500,
                            detail=f"No se pudo calcular el plan de compra: {e}")
