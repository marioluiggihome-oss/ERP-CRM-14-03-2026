# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
electro_fichas.py — LAS MEDIDAS DE LOS ELECTRODOMÉSTICOS.

El catálogo de electrodomésticos (`article_costs`) guarda código, nombre, marca
y precio. Ninguna medida. Aquí se guardan las que hacen falta para poder decir
si un aparato entra en un hueco, en una colección aparte para NO tocar el
catálogo, que lo usan el presupuesto y la rentabilidad.

El cálculo está en `services/electro_hueco.py` y está probado. Aquí solo se lee
y se escribe.

DE DÓNDE SALEN ESTAS MEDIDAS
----------------------------
De la ficha técnica del fabricante, y por eso la ficha guarda `fuente`: el día
que un horno no entre habrá que saber si el 560 lo puso el fabricante o lo
tecleó alguien de memoria. Sin ese campo, las dos cosas se parecen demasiado.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime, timezone
import logging

from services import electro_hueco
from services.db_client import get_db as _get_db

logger = logging.getLogger(__name__)

try:
    from services.jwt_service import require_auth, get_current_user
    _DEPS = [Depends(require_auth)]
except Exception:  # pragma: no cover - entorno de pruebas sin auth
    _DEPS = []

    async def get_current_user():
        return None

router = APIRouter(prefix="/electros", tags=["electros"], dependencies=_DEPS)


class FichaElectro(BaseModel):
    codigo: str = Field(..., min_length=1)
    marca: Optional[str] = ""
    modelo: Optional[str] = ""
    # Las medidas del HUECO que pide el fabricante, no las del aparato. Todas
    # admiten None: «no consta» es un estado legítimo y el motor lo trata
    # distinto de un cero.
    anchoHueco: Optional[float] = None
    altoHueco: Optional[float] = None
    fondoHueco: Optional[float] = None
    ventilacionFondo: Optional[float] = None
    ventilacionSuperior: Optional[float] = None
    tipoInstalacion: Optional[str] = ""
    fuente: Optional[str] = Field(default="", description="De dónde salen estas medidas")


class ComprobarRequest(BaseModel):
    aparatos: List[Dict] = Field(default_factory=list,
                                 description="[{codigo|ficha, hueco:{ancho,alto,fondo}, donde}]")


def _norm(v):
    return str(v or "").strip().upper()


@router.get("/fichas")
async def listar_fichas():
    fichas = await _get_db().electro_fichas.find({}, {"_id": 0}).to_list(5000)
    return {"success": True, "fichas": fichas, "total": len(fichas)}


@router.put("/fichas/{codigo}")
async def guardar_ficha(codigo: str, ficha: FichaElectro,
                        current_user: Optional[dict] = Depends(get_current_user)):
    cod = _norm(codigo)
    if not cod:
        raise HTTPException(status_code=422, detail="El código no puede estar vacío.")
    doc = {**ficha.model_dump(), "codigo": cod,
           "actualizado": datetime.now(timezone.utc).isoformat(),
           "actualizadoPor": (current_user or {}).get("email") or ""}
    await _get_db().electro_fichas.update_one({"codigo": cod}, {"$set": doc}, upsert=True)
    # Se devuelve si la ficha sirve YA para comprobar algo: guardarla a medias
    # y que parezca completa es cómo se acaba confiando en una comprobación que
    # nunca se hizo.
    return {"success": True, "ficha": doc,
            "sirveParaComprobar": electro_hueco.ficha_completa(doc)}


@router.delete("/fichas/{codigo}")
async def borrar_ficha(codigo: str):
    r = await _get_db().electro_fichas.delete_one({"codigo": _norm(codigo)})
    return {"success": True, "borradas": r.deleted_count}


@router.post("/comprobar")
async def comprobar_huecos(payload: ComprobarRequest):
    """¿Entra cada aparato en el hueco que le ha dejado el diseño?

    Cada aparato puede venir con su `ficha` dentro o solo con el `codigo`, y en
    ese caso se busca. Si no hay ficha, el resultado NO es «no cabe»: es
    «pendiente de validación», que es la verdad y lleva a otra acción — llamar
    al proveedor, no rehacer el diseño.
    """
    try:
        codigos = [_norm(a.get("codigo")) for a in payload.aparatos if a.get("codigo")]
        guardadas = {}
        if codigos:
            for f in await _get_db().electro_fichas.find(
                    {"codigo": {"$in": codigos}}, {"_id": 0}).to_list(1000):
                guardadas[f["codigo"]] = f

        aparatos = []
        for a in payload.aparatos:
            ficha = a.get("ficha") or guardadas.get(_norm(a.get("codigo"))) or {}
            aparatos.append({"ficha": ficha, "hueco": a.get("hueco") or {},
                             "donde": a.get("donde") or a.get("codigo") or ""})

        return {"success": True, **electro_hueco.revisar(aparatos)}
    except Exception as e:
        logger.error("comprobar huecos: %s", e, exc_info=True)
        raise HTTPException(status_code=500,
                            detail=f"No se pudo comprobar los huecos: {e}")
