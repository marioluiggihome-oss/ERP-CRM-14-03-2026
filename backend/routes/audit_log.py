"""
audit_log.py — Consulta del registro de auditoría persistido (solo admin).
Lee db.audit_log, que ahora alimenta services.audit_service (login, accesos,
cambios, borrados… con usuario, IP, fecha).
"""
import logging
import os
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from services.db_client import get_db as _get_db

try:
    from services.jwt_service import get_current_user, require_auth, ADMIN_ROLE_FLAGS
    _DEPS = [Depends(require_auth)]
except Exception:  # pragma: no cover
    async def get_current_user():
        return None
    ADMIN_ROLE_FLAGS = ["isAdmin", "isGerente"]
    _DEPS = []

logger = logging.getLogger(__name__)

router = APIRouter(tags=["audit"], dependencies=_DEPS)


def _is_admin(user):
    return bool(user and any(user.get(f) for f in list(ADMIN_ROLE_FLAGS) + ["isPrimaryAdmin"]))


@router.get("/audit")
async def listar_auditoria(action: Optional[str] = None, user: Optional[str] = None,
                           success: Optional[bool] = None, desde: Optional[str] = None,
                           hasta: Optional[str] = None, limit: int = 200, skip: int = 0,
                           current_user: dict = Depends(get_current_user)):
    if not _is_admin(current_user):
        raise HTTPException(status_code=403, detail="Solo administración puede ver la auditoría.")
    q = {}
    if action:
        q["action"] = action
    if user:
        q["$or"] = [{"username": {"$regex": user, "$options": "i"}}, {"user_id": user}]
    if success is not None:
        q["success"] = bool(success)
    if desde or hasta:
        rango = {}
        if desde:
            rango["$gte"] = desde
        if hasta:
            rango["$lte"] = hasta
        q["timestamp"] = rango
    eventos = await _get_db().audit_log.find(q, {"_id": 0}).sort("timestamp", -1).skip(int(skip)).limit(min(int(limit), 1000)).to_list(1000)
    return {"success": True, "eventos": eventos}


@router.get("/audit/actions")
async def acciones_distintas(current_user: dict = Depends(get_current_user)):
    if not _is_admin(current_user):
        raise HTTPException(status_code=403, detail="Solo administración.")
    acciones = await _get_db().audit_log.distinct("action")
    return {"success": True, "acciones": sorted([a for a in acciones if a])}
