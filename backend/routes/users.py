# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
Routes for User Management
Extracted from server.py for better maintainability
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional
import logging
import uuid
import os
import re
import bcrypt

from dotenv import load_dotenv
from services.master import es_master
from services.plataformas import (
    CARPINTER,
    COOPERATIVA,
    STUDIO3K,
    normalizar_usuario_plataforma,
    organizacion_de,
    plataforma_de,
)

load_dotenv()
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])
security = HTTPBearer(auto_error=False)  # NO exigir token (acepta sin)

# Database connection


# Pydantic models
class UserCreate(BaseModel):
    username: str
    password: str
    clientName: str = ""
    commercialDiscount: float = 0
    discountMontada: float = 0
    discountDespiece: float = 0
    discountDesmontada: float = 0
    isAdmin: bool = False
    isRepresentative: bool = False
    isResponsableDelegacion: bool = False
    isTienda: bool = False
    isDirectorFabrica: bool = False
    canSeeCost: bool = False
    canAccessCRM: bool = False
    canAccessInvoices: bool = False
    canAccessElectros: bool = False
    canAccessExpediente: bool = False
    canAccessAlmacen: bool = False
    canAccessBackup: bool = False
    canAccessPlanificacion: bool = False
    canAccessRentabilidad: bool = False
    isController: bool = False
    canViewAllDocuments: bool = False
    canUseAIAnalysis: bool = False
    canUseKitchenDesigner: bool = False
    allowedModules: List[str] = []
    provinciaCode: Optional[str] = None
    accessExpirationDate: Optional[str] = None

    class Config:
        extra = "allow"


class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    clientName: Optional[str] = None
    commercialDiscount: Optional[float] = None
    discountMontada: Optional[float] = None
    discountDespiece: Optional[float] = None
    discountDesmontada: Optional[float] = None
    isAdmin: Optional[bool] = None
    isRepresentative: Optional[bool] = None
    isResponsableDelegacion: Optional[bool] = None
    isTienda: Optional[bool] = None
    isDirectorFabrica: Optional[bool] = None
    canSeeCost: Optional[bool] = None
    canAccessCRM: Optional[bool] = None
    canAccessInvoices: Optional[bool] = None
    canAccessElectros: Optional[bool] = None
    canAccessExpediente: Optional[bool] = None
    canAccessAlmacen: Optional[bool] = None
    canAccessBackup: Optional[bool] = None
    canAccessPlanificacion: Optional[bool] = None
    canAccessRentabilidad: Optional[bool] = None
    isController: Optional[bool] = None
    canViewAllDocuments: Optional[bool] = None
    canUseAIAnalysis: Optional[bool] = None
    canUseKitchenDesigner: Optional[bool] = None
    allowedModules: Optional[List[str]] = None
    provinciaCode: Optional[str] = None
    accessExpirationDate: Optional[str] = None
    isActive: Optional[bool] = None

    class Config:
        extra = "allow"


class UserResponse(BaseModel):
    id: str
    username: str
    clientName: str = ""
    commercialDiscount: float = 0
    isAdmin: bool = False
    isRepresentative: bool = False
    isResponsableDelegacion: bool = False
    isTienda: bool = False
    isDirectorFabrica: bool = False
    canSeeCost: bool = False
    canAccessCRM: bool = False
    canAccessInvoices: bool = False
    canAccessElectros: bool = False
    canAccessExpediente: bool = False
    canAccessAlmacen: bool = False
    canAccessBackup: bool = False
    canAccessPlanificacion: bool = False
    canAccessRentabilidad: bool = False
    isController: bool = False
    canViewAllDocuments: bool = False
    canUseAIAnalysis: bool = False
    canUseKitchenDesigner: bool = False
    allowedModules: List[str] = []
    provinciaCode: Optional[str] = None
    accessExpirationDate: Optional[str] = None
    isActive: bool = True

    class Config:
        extra = "allow"


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def user_to_response(user_data: dict) -> dict:
    """Convert user dict to response (remove password and Mongo _id)"""
    response = {k: v for k, v in user_data.items() if k not in ("password", "_id")}
    return response


_CONTROLLER_ROLE_FIELDS = {
    "isAdmin", "isPrimaryAdmin", "isGerente", "isDirectorComercial",
    "isResponsableDelegacion", "isDirectorFabrica", "isRepresentative",
    "isComercial", "isPrescriptor", "isTienda", "isFabrica", "isMontador",
    "floorOnly", "crmOnly", "canManageCarpinteroUsers",
}


def enforce_controller_only(data: dict) -> dict:
    """Normaliza CONTROLLER para que solo consulte Rentabilidad y adjuntos."""
    if data.get("isController") is not True:
        return data
    for key in list(data):
        if key.startswith("can") or key in _CONTROLLER_ROLE_FIELDS:
            data[key] = False
    data.update({
        "isController": True,
        "canAccessRentabilidad": True,
        "canViewAllDocuments": False,
        "allowedModules": [],
        "allowedLibraries": [],
        "allowedCatalogIds": [],
    })
    return data


def controller_only_updates(existing: dict) -> dict:
    """Devuelve únicamente campos de acceso mutables para persistir el perfil."""
    normalized = enforce_controller_only({**existing, "isController": True})
    array_fields = {"allowedModules", "allowedLibraries", "allowedCatalogIds"}
    return {
        key: value for key, value in normalized.items()
        if key.startswith("can") or key in _CONTROLLER_ROLE_FIELDS
        or key == "isController" or key in array_fields
    }

# Authentication dependency
from services.jwt_service import get_current_user as _get_current_user, ADMIN_ROLE_FLAGS
from services.db_client import get_db as _get_db


def _is_user_manager(user: dict) -> bool:
    """True si el usuario puede gestionar usuarios (rol elevado o permiso explícito)."""
    if not user or user.get("_compat_mode"):
        return False
    if es_master(user):
        return True
    if any(user.get(f) for f in ADMIN_ROLE_FLAGS):
        return True
    return bool(user.get("canManageUsers") or user.get("canAuthorizePermissions"))


def _es_admin_delegado(user: dict) -> bool:
    plataforma = plataforma_de(user)
    if plataforma == CARPINTER:
        return bool(user.get("canManageCarpinteroUsers"))
    if plataforma == STUDIO3K:
        return bool(user.get("canManageStudio3kUsers"))
    return False


def _puede_ver_usuario(current_user: dict, target: dict) -> bool:
    """Scope del directorio: MASTER todo; plataformas comerciales, solo tenant.

    La red histórica conserva su comportamiento para no romper asignaciones y
    agendas. Una cuenta comercial normal solo recibe su propia ficha; su gestor
    delegado recibe únicamente las cuentas de su organización y marca.
    """
    if es_master(current_user):
        return True
    current_platform = plataforma_de(current_user)
    target_platform = plataforma_de(target)
    if current_platform in (CARPINTER, STUDIO3K):
        if target_platform != current_platform:
            return False
        if _es_admin_delegado(current_user):
            return organizacion_de(target) == organizacion_de(current_user)
        return str(target.get("id") or "") == str(current_user.get("id") or "")
    if _is_user_manager(current_user):
        return target_platform == COOPERATIVA
    return target_platform == COOPERATIVA


async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """JWT opcional: para GET (lectura). Si hay token lo valida, si no devuelve dict compat."""
    if not credentials:
        return {"_compat_mode": True}
    user = await _get_current_user(credentials)
    if not user:
        return {"_compat_mode": True}
    return user


async def require_authenticated_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
):
    """JWT obligatorio y coherente con la entrada pública de plataforma."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Autenticación requerida")
    user = await _get_current_user(credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    from services.plataformas import entrada_permitida, suscripcion_permitida
    if not entrada_permitida(user, request.headers.get("x-platform-entry")):
        raise HTTPException(status_code=403, detail="Sesión no válida para este acceso")
    if not suscripcion_permitida(user):
        raise HTTPException(status_code=403, detail="Suscripción no activa")
    return user


async def require_user_manager(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
):
    """Gestión de usuarios: exige token válido y rol/permiso de administración."""
    user = await require_authenticated_user(request, credentials)
    if not _is_user_manager(user):
        raise HTTPException(status_code=403, detail="Se requiere rol de administrador para gestionar usuarios")
    return user


# Campos sensibles que se ocultan si no hay token JWT (modo compat con frontend viejo)
SENSITIVE_USER_FIELDS = {
    "linkedClientId", "accessExpirationDate", "commercialDiscount",
    "discountMontada", "discountDespiece", "discountDesmontada", "allowedCatalogIds",
}


def filter_sensitive_user_fields(user_data: dict) -> dict:
    """Quita campos sensibles del usuario antes de devolverlos sin auth."""
    return {k: v for k, v in user_data.items() if k not in SENSITIVE_USER_FIELDS}


@router.get("")
async def get_users(current_user: dict = Depends(require_authenticated_user)):
    """Directorio filtrado por alcance; nunca expone usuarios de otra plataforma."""
    users = await _get_db().users.find({}, {"_id": 0, "password": 0}).to_list(1000)
    users = [u for u in users if _puede_ver_usuario(current_user, u)]
    if not (_is_user_manager(current_user) or _es_admin_delegado(current_user)):
        users = [filter_sensitive_user_fields(u) for u in users]
    return users


@router.get("/{user_id}")
async def get_user(user_id: str, current_user: dict = Depends(require_authenticated_user)):
    """Obtiene una ficha solo cuando pertenece al alcance del solicitante."""
    user = await _get_db().users.find_one({"id": user_id}, {"_id": 0, "password": 0})
    if not user or not _puede_ver_usuario(current_user, user):
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if not (_is_user_manager(current_user) or _es_admin_delegado(current_user)):
        user = filter_sensitive_user_fields(user)
    return user


@router.post("", response_model=UserResponse)
async def create_user(user: UserCreate, current_user: dict = Depends(require_user_manager)):
    """Crear un nuevo usuario con password hasheado.

    SEGURIDAD: Sin JWT, no se pueden crear usuarios con roles elevados (Admin, Gerente, etc.)
    ni permisos peligrosos (canManageUsers, canAuthorizePermissions, etc.)."""
    # Check if username exists (case insensitive)
    existing = await _get_db().users.find_one({"username": {"$regex": f"^{re.escape(user.username)}$", "$options": "i"}})
    if existing:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya existe")

    user_data = enforce_controller_only(user.model_dump())

    # SEGURIDAD: Si no hay JWT (modo compat), forzar a usuario sin privilegios elevados
    if current_user.get("_compat_mode"):
        DANGEROUS_FIELDS = {
            "isAdmin", "isPrimaryAdmin", "isGerente", "isDirectorComercial",
            "isResponsableDelegacion", "isDirectorFabrica",
            "canManageUsers", "canAuthorizePermissions",
            "canChangeLogo", "canManageSettings",
        }
        for f in DANGEROUS_FIELDS:
            if user_data.get(f):
                user_data[f] = False
                logger.warning(f"Compat mode: forced {f}=False at user create for '{user.username}'")

    user_data["id"] = f"user-{uuid.uuid4().hex[:8]}"
    user_data["username"] = user_data["username"]  # Keep original case for email-style usernames
    user_data["password"] = hash_password(user_data["password"])
    user_data["isActive"] = True
    user_data.update(normalizar_usuario_plataforma(user_data))
    if plataforma_de(user_data) in (CARPINTER, STUDIO3K) and not es_master(current_user):
        raise HTTPException(status_code=403, detail="Solo MASTER puede crear cuentas raíz de plataforma")
    
    await _get_db().users.insert_one(user_data)
    
    logger.info(f"User created: {user_data['username']} (compat={current_user.get('_compat_mode', False)})")
    
    return user_to_response(user_data)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user: UserUpdate, current_user: dict = Depends(require_user_manager)):
    """Actualizar un usuario.

    SEGURIDAD: Sin JWT, no se pueden elevar permisos del usuario editado ni cambiar
    el usuario admin principal."""
    existing = await _get_db().users.find_one({"id": user_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # SEGURIDAD: sin JWT no se puede modificar el admin principal
    if current_user.get("_compat_mode") and user_id == "admin":
        raise HTTPException(status_code=403, detail="Modificar admin principal requiere autenticación")

    update_data = {k: v for k, v in user.model_dump().items() if v is not None}
    target_platform = plataforma_de({**existing, **update_data})
    if (plataforma_de(existing) in (CARPINTER, STUDIO3K) or target_platform in (CARPINTER, STUDIO3K)) and not es_master(current_user):
        raise HTTPException(status_code=403, detail="Solo MASTER puede editar cuentas comerciales desde la gestión global")
    update_data.update(normalizar_usuario_plataforma(update_data, existing))
    if update_data.get("isController") is True:
        update_data.update(controller_only_updates({**existing, **update_data}))

    # SEGURIDAD: sin JWT, bloquear elevación de permisos
    if current_user.get("_compat_mode"):
        DANGEROUS_FIELDS = {
            "isAdmin", "isPrimaryAdmin", "isGerente", "isDirectorComercial",
            "isResponsableDelegacion", "isDirectorFabrica",
            "canManageUsers", "canAuthorizePermissions",
        }
        for f in DANGEROUS_FIELDS:
            if f in update_data and update_data[f] and not existing.get(f):
                # Intento de elevar privilegios → bloqueado
                update_data.pop(f, None)
                logger.warning(f"Compat mode: blocked privilege escalation {f}=True on user '{user_id}'")
    
    # Hash password if provided
    if "password" in update_data and update_data["password"]:
        update_data["password"] = hash_password(update_data["password"])
        logger.info(f"Password changed for user: {user_id}")
    
    if update_data:
        await _get_db().users.update_one({"id": user_id}, {"$set": update_data})
    
    logger.info(f"User updated: {user_id}, fields: {list(update_data.keys())}")
    
    updated = await _get_db().users.find_one({"id": user_id}, {"_id": 0, "password": 0})
    return updated


@router.delete("/{user_id}")
async def delete_user(user_id: str, current_user: dict = Depends(require_user_manager)):
    """Eliminar un usuario.

    SEGURIDAD: Sin JWT, no se puede borrar el admin principal ni otros admins."""
    if user_id == "admin":
        raise HTTPException(status_code=400, detail="No se puede eliminar el administrador principal")

    # Get user info before deletion
    user_to_delete = await _get_db().users.find_one({"id": user_id}, {"_id": 0, "password": 0})
    if user_to_delete and plataforma_de(user_to_delete) in (CARPINTER, STUDIO3K) and not es_master(current_user):
        raise HTTPException(status_code=403, detail="Solo MASTER puede eliminar cuentas comerciales desde la gestión global")

    # SEGURIDAD: sin JWT no se puede borrar usuarios con rol admin/gerente
    if current_user.get("_compat_mode") and user_to_delete:
        if user_to_delete.get("isAdmin") or user_to_delete.get("isGerente"):
            raise HTTPException(status_code=403, detail="Eliminar admin/gerente requiere autenticación")
    
    result = await _get_db().users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    logger.info(f"User deleted: {user_to_delete.get('username') if user_to_delete else user_id}")
    
    return {"message": "Usuario eliminado"}


def _linked_admin_field(plataforma: str) -> str:
    return "linkedStudio3kAdminId" if plataforma == STUDIO3K else "linkedCarpinteroAdminId"


def _manager_flag(plataforma: str) -> str:
    return "canManageStudio3kUsers" if plataforma == STUDIO3K else "canManageCarpinteroUsers"


async def _platform_users(plataforma: str, current_user: dict, admin_id: Optional[str] = None, include_root: bool = True) -> list[dict]:
    """Usuarios del tenant delegado o, para MASTER, de toda la plataforma."""
    linked_field = _linked_admin_field(plataforma)
    if es_master(current_user):
        users = await _get_db().users.find({}, {"_id": 0, "password": 0}).to_list(2000)
        users = [u for u in users if plataforma_de(u) == plataforma]
        if admin_id:
            users = [u for u in users if str(u.get("id") or "") == admin_id
                     or str(u.get(linked_field) or "") == admin_id
                     or str(u.get("organizationId") or "") == admin_id]
        return users

    organization_id = organizacion_de(current_user)
    users = await _get_db().users.find(
        {"$or": [
            {linked_field: current_user.get("id")},
            {"organizationId": organization_id},
            {"id": current_user.get("id")},
        ]},
        {"_id": 0, "password": 0},
    ).to_list(1000)
    users = [u for u in users if plataforma_de(u) == plataforma and organizacion_de(u) == organization_id]
    if not include_root:
        users = [u for u in users if str(u.get("id") or "") != str(current_user.get("id") or "")]
    return users


def _subscription_status(user: dict) -> str:
    if not user.get("isActive", True):
        return "inactive"
    expiration = user.get("accessExpirationDate")
    if expiration:
        try:
            from datetime import datetime, timezone
            value = datetime.fromisoformat(str(expiration).replace("Z", "+00:00"))
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            if value.date() < datetime.now(timezone.utc).date():
                return "expired"
        except (TypeError, ValueError):
            return "invalid_expiration"
    return "active" if user.get("subscriptionPlan") else "unconfigured"


async def _platform_stats(plataforma: str, current_user: dict, admin_id: Optional[str] = None) -> dict:
    """Actividad y cuota mensual filtradas por marca y organización."""
    from datetime import datetime, timezone

    users = await _platform_users(plataforma, current_user, admin_id=admin_id, include_root=True)
    ids = [str(u.get("id")) for u in users if u.get("id")]
    logins_count, last_login, credits_by_user, balance_by_user = {}, {}, {}, {}

    try:
        cursor = _get_db().user_activity.find(
            {"userId": {"$in": ids}, "activityType": "login"},
            {"_id": 0, "userId": 1, "timestamp": 1},
        )
        async for activity in cursor:
            uid = str(activity.get("userId") or "")
            logins_count[uid] = logins_count.get(uid, 0) + 1
            timestamp = activity.get("timestamp")
            timestamp = timestamp.isoformat() if hasattr(timestamp, "isoformat") else str(timestamp or "")
            if uid not in last_login or timestamp > last_login[uid]:
                last_login[uid] = timestamp
    except Exception as exc:
        logger.warning("platform stats logins: %s", exc)

    month = datetime.now(timezone.utc).strftime("%Y-%m")
    try:
        cursor = _get_db().ai_credits.find(
            {"user_id": {"$in": ids}, "month": month},
            {"_id": 0},
        )
        async for credit in cursor:
            credits_by_user[str(credit.get("user_id") or "")] = credit
        cursor = _get_db().ai_credit_balance.find(
            {"user_id": {"$in": ids}},
            {"_id": 0, "user_id": 1, "saldo": 1},
        )
        async for balance in cursor:
            balance_by_user[str(balance.get("user_id") or "")] = max(int(balance.get("saldo", 0) or 0), 0)
    except Exception as exc:
        logger.warning("platform stats credits: %s", exc)

    items = []
    for user in users:
        uid = str(user.get("id") or "")
        credit = credits_by_user.get(uid, {})
        consumed = int(credit.get("consumed", 0) or 0)
        extra_month = int(credit.get("extra", 0) or 0)
        spent_balance = int(credit.get("gastado_saldo", 0) or 0)
        assigned = max(int(user.get("aiCreditsMonthly", 0) or 0), 0)
        balance = balance_by_user.get(uid, 0)
        consumed_plan = max(consumed - spent_balance, 0)
        remaining = max(assigned + extra_month - consumed_plan, 0) + balance
        total_available = assigned + extra_month + balance
        percent = round(consumed / total_available * 100, 1) if total_available > 0 else 0
        items.append({
            "id": uid,
            "username": user.get("username"),
            "clientName": user.get("clientName", ""),
            "isActive": user.get("isActive", True),
            "esAdmin": bool(user.get(_manager_flag(plataforma))),
            "plataforma": plataforma,
            "organizationId": organizacion_de(user),
            "linkedAdminId": user.get(_linked_admin_field(plataforma), ""),
            "subscriptionPlan": user.get("subscriptionPlan", ""),
            "subscriptionStatus": _subscription_status(user),
            "subscriptionStartDate": user.get("subscriptionStartDate", ""),
            "accessExpirationDate": user.get("accessExpirationDate", ""),
            "cuotaMensual": assigned,
            "saldoComprado": balance,
            "restantes": remaining,
            "porcentaje": percent,
            "logins": logins_count.get(uid, 0),
            "ultimoLogin": last_login.get(uid, ""),
            "rendersMes": consumed,
        })
    items.sort(key=lambda item: item.get("ultimoLogin") or "", reverse=True)
    return {
        "success": True,
        "platform": plataforma,
        "organizationId": "all" if es_master(current_user) and not admin_id else (admin_id or organizacion_de(current_user)),
        "month": month,
        "total": len(items),
        "activos": sum(1 for item in items if item["isActive"]),
        "conActividad": sum(1 for item in items if item["rendersMes"] > 0 or item["logins"] > 0),
        "rendersTotales": sum(item["rendersMes"] for item in items),
        "cuotaTotal": sum(item["cuotaMensual"] + item["saldoComprado"] for item in items),
        "restantesTotal": sum(item["restantes"] for item in items),
        "items": items,
    }


async def _platform_target(user_id: str, plataforma: str, current_user: dict) -> dict:
    target = await _get_db().users.find_one({"id": user_id}, {"_id": 0, "password": 0})
    if not target or plataforma_de(target) != plataforma:
        raise HTTPException(status_code=404, detail="Usuario no encontrado en esta plataforma")
    if not es_master(current_user):
        linked_field = _linked_admin_field(plataforma)
        if str(target.get(linked_field) or "") != str(current_user.get("id") or ""):
            raise HTTPException(status_code=404, detail="Usuario no encontrado en tu organización")
    return target


async def _delegated_owner(payload: dict, plataforma: str, current_user: dict) -> dict:
    """Administrador raíz bajo el que se crea una cuenta delegada."""
    if not es_master(current_user):
        return current_user
    admin_id = str((payload or {}).get("adminId") or "").strip()
    if not admin_id:
        raise HTTPException(status_code=400, detail="MASTER debe seleccionar una organización administradora")
    owner = await _get_db().users.find_one({"id": admin_id}, {"_id": 0, "password": 0})
    if not owner or plataforma_de(owner) != plataforma or not owner.get(_manager_flag(plataforma)):
        raise HTTPException(status_code=400, detail="La organización administradora no es válida para esta plataforma")
    return owner


# ---------------------------------------------------------------------------
# Division Carpinteros & Ebanistas: el admin de la division (isCarpintero +
# canManageCarpinteroUsers) puede crear y gestionar UNICAMENTE los usuarios
# vinculados a el (linkedCarpinteroAdminId). Los usuarios creados heredan el
# perfil carpintero, su landing y los permisos por defecto de la division.
# Rutas con dos segmentos para no chocar con /{user_id}.
# ---------------------------------------------------------------------------
async def require_carpintero_admin(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
):
    """Admin de la division carpinteros (o gestor de usuarios global).
    El JWT no lleva los flags de carpintero, asi que se cargan de la BD."""
    user = await require_authenticated_user(request, credentials)
    if es_master(user):
        return user
    full = await _get_db().users.find_one(
        {"id": user.get("id")},
        {"_id": 0, "password": 0},
    ) or {}
    if full.get("isCarpintero") and full.get("canManageCarpinteroUsers"):
        # Fusiona los flags reales para que los endpoints tengan id + landing + permisos.
        return {**user, **full}
    raise HTTPException(status_code=403, detail="Se requiere permiso de gestion de usuarios de la division")


@router.get("/carpinteros/mine")
async def carpintero_users(current_user: dict = Depends(require_carpintero_admin), adminId: Optional[str] = None):
    """Usuarios CARPINTER.IO: global para MASTER, tenant propio para el gestor."""
    return await _platform_users(
        CARPINTER,
        current_user,
        admin_id=adminId,
        include_root=es_master(current_user),
    )


@router.get("/carpinteros/stats")
async def carpintero_stats(current_user: dict = Depends(require_carpintero_admin), adminId: Optional[str] = None):
    """Actividad, suscripción y consumo CARPINTER.IO dentro del scope autorizado."""
    return await _platform_stats(CARPINTER, current_user, admin_id=adminId)


@router.post("/carpinteros/create")
async def carpintero_create_user(payload: dict, current_user: dict = Depends(require_carpintero_admin)):
    """Crea un usuario de la division carpinteros, vinculado al admin.
    Hereda perfil carpintero, landing y permisos por defecto; nunca roles elevados."""
    username = str((payload or {}).get("username", "")).strip()
    password = str((payload or {}).get("password", ""))
    if not username or not password:
        raise HTTPException(status_code=400, detail="Usuario y contrasena son obligatorios")
    existing = await _get_db().users.find_one({"username": {"$regex": f"^{re.escape(username)}$", "$options": "i"}})
    if existing:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya existe")
    owner = await _delegated_owner(payload, CARPINTER, current_user)
    doc = {
        "id": f"user-{uuid.uuid4().hex[:8]}",
        "username": username,
        "password": hash_password(password),
        "clientName": str(payload.get("clientName", "")).strip(),
        "isActive": True,
        # Herencia de la division (el admin define los permisos por defecto):
        "isCarpintero": True,
        "plataforma": "carpinter",
        "linkedCarpinteroAdminId": owner.get("id"),
        "organizationId": organizacion_de(owner),
        "carpinteroLandingUrl": str(payload.get("carpinteroLandingUrl") or owner.get("carpinteroLandingUrl") or ""),
        "canUseCascos": bool(owner.get("canUseCascos")),
        "subscriptionPlan": owner.get("subscriptionPlan", ""),
        "aiCreditsMonthly": int(owner.get("aiCreditsMonthly", 0) or 0),
        "accessExpirationDate": owner.get("accessExpirationDate"),
    }
    await _get_db().users.insert_one(doc)
    logger.info("Carpintero user created: %s (by %s)", username, current_user.get("username"))
    return {k: v for k, v in doc.items() if k != "password"}


@router.put("/carpinteros/toggle/{user_id}")
async def carpintero_toggle_user(user_id: str, current_user: dict = Depends(require_carpintero_admin)):
    """Activa/desactiva un usuario de la division (solo los vinculados al admin)."""
    u = await _platform_target(user_id, CARPINTER, current_user)
    new_active = not bool(u.get("isActive", True))
    await _get_db().users.update_one({"id": user_id}, {"$set": {"isActive": new_active}})
    return {"success": True, "isActive": new_active}


@router.delete("/carpinteros/remove/{user_id}")
async def carpintero_delete_user(user_id: str, current_user: dict = Depends(require_carpintero_admin)):
    """Elimina un usuario de la division (solo los vinculados al admin)."""
    await _platform_target(user_id, CARPINTER, current_user)
    res = await _get_db().users.delete_one({"id": user_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado en esta plataforma")
    return {"success": True}


# ---------------------------------------------------------------------------
# Studio3K: cada estudio/tienda tiene un administrador principal y usuarios
# vinculados únicamente a ese administrador. Es el mismo patrón de aislamiento
# empleado por carpinter.io, pero con acceso por defecto a Estudio 3D.
# ---------------------------------------------------------------------------
ESTUDIO3D_TIPOS_VALIDOS = {"cocina", "armario", "bano", "otro"}


def _tipos_estudio3d(value) -> list[str]:
    """Normaliza los tipos contratados; una lista vacía conserva el acceso total."""
    if not isinstance(value, list):
        return []
    return [str(tipo).strip().lower() for tipo in value if str(tipo).strip().lower() in ESTUDIO3D_TIPOS_VALIDOS]


async def require_studio3k_admin(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
):
    user = await require_authenticated_user(request, credentials)
    if es_master(user):
        return user
    full = await _get_db().users.find_one(
        {"id": user.get("id")},
        {"_id": 0, "password": 0},
    ) or {}
    if full.get("isStudio3k") and full.get("canManageStudio3kUsers"):
        return {**user, **full}
    raise HTTPException(status_code=403, detail="Se requiere permiso de gestión de usuarios Studio3K")


@router.get("/studio3k/mine")
async def studio3k_users(current_user: dict = Depends(require_studio3k_admin), adminId: Optional[str] = None):
    """Usuarios STUDIO3K.IO: global para MASTER, tenant propio para el gestor."""
    return await _platform_users(
        STUDIO3K,
        current_user,
        admin_id=adminId,
        include_root=es_master(current_user),
    )


@router.get("/studio3k/stats")
async def studio3k_stats(current_user: dict = Depends(require_studio3k_admin), adminId: Optional[str] = None):
    """Actividad, suscripción y consumo STUDIO3K.IO dentro del scope autorizado."""
    return await _platform_stats(STUDIO3K, current_user, admin_id=adminId)


@router.post("/studio3k/create")
async def studio3k_create_user(payload: dict, current_user: dict = Depends(require_studio3k_admin)):
    """Crea un usuario del estudio vinculado a su administrador Studio3K."""
    username = str((payload or {}).get("username", "")).strip()
    password = str((payload or {}).get("password", ""))
    if not username or not password:
        raise HTTPException(status_code=400, detail="Usuario y contraseña son obligatorios")
    existing = await _get_db().users.find_one({"username": {"$regex": f"^{re.escape(username)}$", "$options": "i"}})
    if existing:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya existe")
    owner = await _delegated_owner(payload, STUDIO3K, current_user)
    doc = {
        "id": f"user-{uuid.uuid4().hex[:8]}",
        "username": username,
        "password": hash_password(password),
        "clientName": str(payload.get("clientName", "")).strip(),
        "isActive": True,
        "isStudio3k": True,
        "plataforma": "studio3k",
        "linkedStudio3kAdminId": owner.get("id"),
        "organizationId": organizacion_de(owner),
        "studio3kLandingUrl": str(payload.get("studio3kLandingUrl") or owner.get("studio3kLandingUrl") or ""),
        "canUseKitchenDesigner": bool(owner.get("canUseKitchenDesigner")),
        "canUseCocinasAI": bool(owner.get("canUseCocinasAI")),
        "canUseAIAnalysis": bool(owner.get("canUseAIAnalysis")),
        "subscriptionPlan": owner.get("subscriptionPlan", ""),
        "aiCreditsMonthly": int(owner.get("aiCreditsMonthly", 0) or 0),
        "accessExpirationDate": owner.get("accessExpirationDate"),
        # Los usuarios del estudio heredan los tipos contratados por su admin.
        # Vacío mantiene la compatibilidad de "todos los tipos".
        "estudio3dTipos": _tipos_estudio3d(owner.get("estudio3dTipos")),
        # El acceso al Estudio 3D lo dan los permisos específicos. Dejar la
        # lista vacía mantiene al usuario dentro del portal privado Studio3K.
        "allowedModules": [],
    }
    await _get_db().users.insert_one(doc)
    logger.info("Studio3K user created: %s (by %s)", username, current_user.get("username"))
    return {k: v for k, v in doc.items() if k != "password"}


@router.put("/studio3k/toggle/{user_id}")
async def studio3k_toggle_user(user_id: str, current_user: dict = Depends(require_studio3k_admin)):
    """Activa o desactiva un usuario únicamente dentro de su estudio Studio3K."""
    u = await _platform_target(user_id, STUDIO3K, current_user)
    new_active = not bool(u.get("isActive", True))
    await _get_db().users.update_one({"id": user_id}, {"$set": {"isActive": new_active}})
    return {"success": True, "isActive": new_active}


@router.delete("/studio3k/remove/{user_id}")
async def studio3k_delete_user(user_id: str, current_user: dict = Depends(require_studio3k_admin)):
    """Elimina un usuario únicamente dentro de su estudio Studio3K."""
    await _platform_target(user_id, STUDIO3K, current_user)
    res = await _get_db().users.delete_one({"id": user_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado en esta plataforma")
    return {"success": True}
