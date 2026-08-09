# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
plan_negocio.py — EL PLAN DE NEGOCIO DE LA FÁBRICA. SOLO EL MASTER.

Aquí solo se lee y se escribe en la base de datos. Las cuentas están en
`services/plan_negocio.py`, que es cálculo puro y está protegido por sus
candados: así lo que decide el plan se puede probar sin levantar Mongo.

POR QUÉ ESTO ESTÁ MÁS CERRADO QUE EL RESTO
------------------------------------------
Por aquí pasan el coste de compra del casco, el descuento del proveedor, el
margen por canal y la estructura de la empresa. Eso no lo ve un gerente ni un
director comercial: lo ve el MASTER. La lista ancha de roles (`ADMIN_ROLE_FLAGS`)
incluye perfiles que entran a Cascos y no pueden entrar a esto.

Y la guarda va AQUÍ, no solo en la pantalla: si estuviera solo en la pantalla,
bastaría con llamar a la API a mano para leerlo entero.

UNA COLECCIÓN
-------------
`planes_negocio` — un documento por plan: {planId, datos, actualizado, por}
`datos` es lo que el master escribe. Lo calculado NO se guarda: se recalcula al
leer, para que no pueda quedarse un resultado viejo al lado de un dato nuevo.
"""
from fastapi import APIRouter, HTTPException, Depends, Response
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import io
import logging

from services import plan_negocio as motor
from services.db_client import get_db as _get_db

logger = logging.getLogger(__name__)

try:
    from services.jwt_service import require_auth, get_current_user
    _DEPS = [Depends(require_auth)]
except Exception:  # pragma: no cover - entorno de pruebas sin auth
    _DEPS = []

    async def get_current_user():
        return None

router = APIRouter(prefix="/plan-negocio", tags=["plan-negocio"], dependencies=_DEPS)

# MASTER de verdad. Ver la nota de arriba: `isGerente` e `isDirectorComercial`
# sirven para ver Cascos, no para ver el coste de compra ni el margen.
_MASTER_FLAGS = ("isAdmin", "isPrimaryAdmin", "isMaster")


def _es_master(user: Optional[dict]) -> bool:
    return bool(user and any(user.get(f) for f in _MASTER_FLAGS))


def _exigir_master(user: Optional[dict]):
    if not _es_master(user):
        raise HTTPException(
            status_code=403,
            detail="El plan de negocio es solo del master: lleva costes de compra y márgenes.")


class Plan(BaseModel):
    """Lo que el master escribe. Todo opcional A PROPÓSITO.

    Un plan de negocio se rellena a lo largo de semanas, y obligar a tenerlo
    todo para poder guardar es la forma segura de que nadie guarde nada — o de
    que alguien meta un número de relleno para que le deje pasar, que es peor.
    """
    capacidad: Optional[Dict[str, Any]] = None
    referencias: Optional[list] = None
    b2c: Optional[Dict[str, Any]] = None
    repartoB2B: Optional[float] = None
    estructura: Optional[Dict[str, Any]] = None
    inversion: Optional[Dict[str, Any]] = None
    plazoEntregaSemanas: Optional[float] = None
    escenarios: Optional[list] = None
    notas: Optional[str] = ""


def _vacio() -> dict:
    """Un plan recién empezado.

    Solo lleva lo que el master YA decidió (2 personas, 3 muebles/hora, 7 h/día,
    L-V, 1.600 h/año y las seis referencias). Ni un precio, ni un gasto: eso no
    se sabe todavía, y una cifra de ejemplo en una casilla acaba viajando al
    plan final sin que nadie recuerde de dónde salió.
    """
    return {
        "capacidad": {"personas": 2, "mueblesHora": 3, "horasDia": 7,
                      "diasSemana": 5, "horasAno": 1600, "costeHoraPersona": None},
        # `costeMaterialesMueble` es la forma normal de empezar: un solo número
        # por mueble. El desglose en ocho partidas está para cuando haga falta
        # saber DÓNDE está el coste, no para tener que rellenarlo hoy.
        "referencias": [{"nombre": n, "costeMaterialesMueble": None,
                         **{c: None for c in motor.COSTES_DE_MATERIAL},
                         "precioB2B": None, "precioB2C": None} for n in motor.REFERENCIAS],
        "b2c": {c: None for c in motor.COSTES_B2C},
        "repartoB2B": None,
        "estructura": {k: None for k in (
            "Salarios fabricación", "Salario administración", "Salario comercial",
            "Alquiler de nave", "Suministros", "Maquinaria (amortización)",
            "Vehículos", "Software y ERP", "Seguros", "Gestoría",
            "Marketing", "Logística", "Otros gastos")},
        "inversion": {k: None for k in (
            "Maquinaria", "Instalaciones", "Utillaje", "Informática",
            "Vehículo", "Stock de cascos", "Stock de producto terminado",
            "Stock de herrajes", "Fianzas y constitución", "Tesorería de arranque")},
        "plazoEntregaSemanas": None,
        "escenarios": [
            {"nombre": "Inicial", "personas": 2, "mueblesHora": 3},
            # La productividad de 3 y 4 personas se MIDE cuando pase. Dejarla en
            # blanco no es un descuido: es la única respuesta honesta hoy.
            {"nombre": "Crecimiento", "personas": 3, "mueblesHora": None},
            {"nombre": "Escalado", "personas": 4, "mueblesHora": None},
        ],
        "notas": "",
    }


@router.get("")
async def leer(planId: str = "principal",
               current_user: Optional[dict] = Depends(get_current_user)):
    """El plan guardado, con las cuentas hechas al vuelo."""
    _exigir_master(current_user)
    doc = await _get_db().planes_negocio.find_one({"planId": planId}, {"_id": 0})
    datos = (doc or {}).get("datos") or _vacio()
    return {
        "success": True,
        "planId": planId,
        "datos": datos,
        "resultado": motor.calcular(datos),
        "actualizado": (doc or {}).get("actualizado"),
        "por": (doc or {}).get("por"),
        "nuevo": doc is None,
    }


@router.put("")
async def guardar(plan: Plan, planId: str = "principal",
                  current_user: Optional[dict] = Depends(get_current_user)):
    """Guarda lo escrito y devuelve las cuentas rehechas.

    Se devuelve el resultado recalculado a propósito: así la pantalla no puede
    quedarse enseñando un número viejo al lado de un dato nuevo.
    """
    _exigir_master(current_user)
    datos = plan.model_dump(exclude_none=False)
    await _get_db().planes_negocio.update_one(
        {"planId": planId},
        {"$set": {"planId": planId, "datos": datos,
                  "actualizado": datetime.now(timezone.utc).isoformat(),
                  "por": (current_user or {}).get("username") or ""}},
        upsert=True,
    )
    return {"success": True, "datos": datos, "resultado": motor.calcular(datos)}


@router.post("/calcular")
async def calcular_sin_guardar(plan: Plan,
                               current_user: Optional[dict] = Depends(get_current_user)):
    """Las cuentas de un plan que todavía no se quiere guardar.

    Sirve para probar «¿y si subo el precio un 5 %?» sin dejar rastro. Un plan
    de negocio se hace tanteando, y tener que guardar para poder mirar acaba
    ensuciando el plan bueno con pruebas.
    """
    _exigir_master(current_user)
    return {"success": True, "resultado": motor.calcular(plan.model_dump(exclude_none=False))}


@router.get("/excel")
async def descargar_excel(planId: str = "principal",
                          current_user: Optional[dict] = Depends(get_current_user)):
    """El mismo plan, en una hoja de cálculo de verdad.

    Con FÓRMULAS, no con los resultados pegados: fuera del ERP tiene que seguir
    recalculando cuando se toque una casilla. Un Excel con números fijos es una
    foto, y una foto de un plan de negocio se queda vieja el primer día.
    """
    _exigir_master(current_user)
    doc = await _get_db().planes_negocio.find_one({"planId": planId}, {"_id": 0})
    datos = (doc or {}).get("datos") or _vacio()
    try:
        from services.plan_negocio_excel import construir
    except Exception as e:  # pragma: no cover
        logger.error("No se pudo cargar el generador de Excel: %s", e)
        raise HTTPException(status_code=500, detail="No se pudo generar el Excel.")

    buf = io.BytesIO()
    construir(datos).save(buf)
    buf.seek(0)
    return Response(
        content=buf.read(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="plan_negocio.xlsx"'},
    )
