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

# Authentication dependency
from services.jwt_service import get_current_user as _get_current_user, ADMIN_ROLE_FLAGS
from services.db_client import get_db as _get_db


def _is_user_manager(user: dict) -> bool:
    """True si el usuario puede gestionar usuarios (rol elevado o permiso explícito)."""
    if not user or user.get("_compat_mode"):
        return False
    if any(user.get(f) for f in ADMIN_ROLE_FLAGS):
        return True
    return bool(user.get("canManageUsers") or user.get("canAuthorizePermissions"))


async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """JWT opcional: para GET (lectura). Si hay token lo valida, si no devuelve dict compat."""
    if not credentials:
        return {"_compat_mode": True}
    user = await _get_current_user(credentials)
    if not user:
        return {"_compat_mode": True}
    return user


async def require_authenticated_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """JWT obligatorio para escrituras (POST/PUT/DELETE). Lanza 401 si no hay token válido."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Autenticación requerida")
    user = await _get_current_user(credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    return user


async def require_user_manager(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """Gestión de usuarios: exige token válido y rol/permiso de administración."""
    user = await require_authenticated_user(credentials)
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
async def get_users(current_user: dict = Depends(get_current_user)):
    """Obtener todos los usuarios (sin passwords). Si no hay JWT, oculta campos sensibles."""
    users = await _get_db().users.find({}, {"_id": 0, "password": 0}).to_list(1000)
    if not _is_user_manager(current_user):
        users = [filter_sensitive_user_fields(u) for u in users]
    return users


@router.get("/{user_id}")
async def get_user(user_id: str, current_user: dict = Depends(get_current_user)):
    """Obtener un usuario por ID (sin password). Si no hay JWT, oculta campos sensibles."""
    user = await _get_db().users.find_one({"id": user_id}, {"_id": 0, "password": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if not _is_user_manager(current_user):
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

    user_data = user.model_dump()

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
    user_to_delete = await _get_db().users.find_one({"id": user_id}, {"_id": 0, "username": 1, "isAdmin": 1, "isGerente": 1})

    # SEGURIDAD: sin JWT no se puede borrar usuarios con rol admin/gerente
    if current_user.get("_compat_mode") and user_to_delete:
        if user_to_delete.get("isAdmin") or user_to_delete.get("isGerente"):
            raise HTTPException(status_code=403, detail="Eliminar admin/gerente requiere autenticación")
    
    result = await _get_db().users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    logger.info(f"User deleted: {user_to_delete.get('username') if user_to_delete else user_id}")
    
    return {"message": "Usuario eliminado"}


# ---------------------------------------------------------------------------
# Division Carpinteros & Ebanistas: el admin de la division (isCarpintero +
# canManageCarpinteroUsers) puede crear y gestionar UNICAMENTE los usuarios
# vinculados a el (linkedCarpinteroAdminId). Los usuarios creados heredan el
# perfil carpintero, su landing y los permisos por defecto de la division.
# Rutas con dos segmentos para no chocar con /{user_id}.
# ---------------------------------------------------------------------------
async def require_carpintero_admin(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """Admin de la division carpinteros (o gestor de usuarios global).
    El JWT no lleva los flags de carpintero, asi que se cargan de la BD."""
    user = await require_authenticated_user(credentials)
    if _is_user_manager(user):
        return user
    full = await _get_db().users.find_one(
        {"id": user.get("id")},
        {"_id": 0, "id": 1, "username": 1, "isCarpintero": 1, "canManageCarpinteroUsers": 1,
         "carpinteroLandingUrl": 1, "canUseCascos": 1},
    ) or {}
    if full.get("isCarpintero") and full.get("canManageCarpinteroUsers"):
        # Fusiona los flags reales para que los endpoints tengan id + landing + permisos.
        return {**user, **full}
    raise HTTPException(status_code=403, detail="Se requiere permiso de gestion de usuarios de la division")


@router.get("/carpinteros/mine")
async def carpintero_users(current_user: dict = Depends(require_carpintero_admin)):
    """Usuarios vinculados al admin carpintero autenticado."""
    users = await _get_db().users.find(
        {"linkedCarpinteroAdminId": current_user.get("id")},
        {"_id": 0, "password": 0},
    ).to_list(500)
    return users


@router.get("/carpinteros/stats")
async def carpintero_stats(current_user: dict = Depends(require_carpintero_admin), adminId: Optional[str] = None):
    """Estadisticas de la division carpinteros. El master (gestor global) ve
    TODOS los carpinteros (o los de un adminId concreto); el admin de division
    solo los suyos. Por usuario: ultimo login, nº de accesos y renders del mes."""
    from datetime import datetime, timezone
    # Ambito
    if _is_user_manager(current_user):
        q = {"isCarpintero": True}
        if adminId:
            q["linkedCarpinteroAdminId"] = adminId
    else:
        q = {"$or": [{"linkedCarpinteroAdminId": current_user.get("id")}, {"id": current_user.get("id")}]}
    users = await _get_db().users.find(q, {"_id": 0, "password": 0}).to_list(1000)
    ids = [u.get("id") for u in users if u.get("id")]

    # Logins (colección user_activity, activityType=login)
    logins_count = {}
    last_login = {}
    try:
        cur = _get_db().user_activity.find({"userId": {"$in": ids}, "activityType": "login"}, {"_id": 0, "userId": 1, "timestamp": 1})
        async for a in cur:
            uid = a.get("userId")
            logins_count[uid] = logins_count.get(uid, 0) + 1
            ts = a.get("timestamp")
            ts = ts.isoformat() if hasattr(ts, "isoformat") else str(ts)
            if uid not in last_login or ts > last_login[uid]:
                last_login[uid] = ts
    except Exception as e:
        logger.warning("stats logins: %s", e)

    # Renders del mes en curso (ai_credits)
    month = datetime.now(timezone.utc).strftime("%Y-%m")
    renders = {}
    try:
        cur = _get_db().ai_credits.find({"user_id": {"$in": [str(i) for i in ids]}, "month": month}, {"_id": 0})
        async for c in cur:
            renders[str(c.get("user_id"))] = int(c.get("consumed", 0) or 0)
    except Exception as e:
        logger.warning("stats renders: %s", e)

    items = []
    for u in users:
        uid = u.get("id")
        items.append({
            "id": uid, "username": u.get("username"), "clientName": u.get("clientName", ""),
            "isActive": u.get("isActive", True),
            "esAdmin": bool(u.get("canManageCarpinteroUsers")),
            "logins": logins_count.get(uid, 0),
            "ultimoLogin": last_login.get(uid, ""),
            "rendersMes": renders.get(str(uid), 0),
        })
    items.sort(key=lambda x: x.get("ultimoLogin") or "", reverse=True)
    activos_mes = sum(1 for i in items if i["rendersMes"] > 0 or i["logins"] > 0)
    return {
        "success": True, "month": month, "total": len(items),
        "activos": sum(1 for i in items if i["isActive"]),
        "conActividad": activos_mes,
        "rendersTotales": sum(i["rendersMes"] for i in items),
        "items": items,
    }


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
    doc = {
        "id": f"user-{uuid.uuid4().hex[:8]}",
        "username": username,
        "password": hash_password(password),
        "clientName": str(payload.get("clientName", "")).strip(),
        "isActive": True,
        # Herencia de la division (el admin define los permisos por defecto):
        "isCarpintero": True,
        "linkedCarpinteroAdminId": current_user.get("id"),
        "carpinteroLandingUrl": str(payload.get("carpinteroLandingUrl") or current_user.get("carpinteroLandingUrl") or ""),
        "canUseCascos": bool(current_user.get("canUseCascos")),
    }
    await _get_db().users.insert_one(doc)
    logger.info("Carpintero user created: %s (by %s)", username, current_user.get("username"))
    return {k: v for k, v in doc.items() if k != "password"}


@router.put("/carpinteros/toggle/{user_id}")
async def carpintero_toggle_user(user_id: str, current_user: dict = Depends(require_carpintero_admin)):
    """Activa/desactiva un usuario de la division (solo los vinculados al admin)."""
    u = await _get_db().users.find_one({"id": user_id, "linkedCarpinteroAdminId": current_user.get("id")}, {"_id": 0})
    if not u:
        raise HTTPException(status_code=404, detail="Usuario no encontrado en tu division")
    new_active = not bool(u.get("isActive", True))
    await _get_db().users.update_one({"id": user_id}, {"$set": {"isActive": new_active}})
    return {"success": True, "isActive": new_active}


@router.delete("/carpinteros/remove/{user_id}")
async def carpintero_delete_user(user_id: str, current_user: dict = Depends(require_carpintero_admin)):
    """Elimina un usuario de la division (solo los vinculados al admin)."""
    res = await _get_db().users.delete_one({"id": user_id, "linkedCarpinteroAdminId": current_user.get("id")})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado en tu division")
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


async def require_studio3k_admin(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    user = await require_authenticated_user(credentials)
    if _is_user_manager(user):
        return user
    full = await _get_db().users.find_one(
        {"id": user.get("id")},
        {"_id": 0, "id": 1, "username": 1, "isStudio3k": 1,
         "canManageStudio3kUsers": 1, "studio3kLandingUrl": 1,
         "canUseKitchenDesigner": 1, "canUseCocinasAI": 1,
         "canUseAIAnalysis": 1, "estudio3dTipos": 1},
    ) or {}
    if full.get("isStudio3k") and full.get("canManageStudio3kUsers"):
        return {**user, **full}
    raise HTTPException(status_code=403, detail="Se requiere permiso de gestión de usuarios Studio3K")


@router.get("/studio3k/mine")
async def studio3k_users(current_user: dict = Depends(require_studio3k_admin)):
    """Usuarios vinculados al administrador Studio3K autenticado."""
    users = await _get_db().users.find(
        {"linkedStudio3kAdminId": current_user.get("id")},
        {"_id": 0, "password": 0},
    ).to_list(500)
    return users


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
    doc = {
        "id": f"user-{uuid.uuid4().hex[:8]}",
        "username": username,
        "password": hash_password(password),
        "clientName": str(payload.get("clientName", "")).strip(),
        "isActive": True,
        "isStudio3k": True,
        "linkedStudio3kAdminId": current_user.get("id"),
        "studio3kLandingUrl": str(payload.get("studio3kLandingUrl") or current_user.get("studio3kLandingUrl") or ""),
        "canUseKitchenDesigner": bool(current_user.get("canUseKitchenDesigner")),
        "canUseCocinasAI": bool(current_user.get("canUseCocinasAI")),
        "canUseAIAnalysis": bool(current_user.get("canUseAIAnalysis")),
        # Los usuarios del estudio heredan los tipos contratados por su admin.
        # Vacío mantiene la compatibilidad de "todos los tipos".
        "estudio3dTipos": _tipos_estudio3d(current_user.get("estudio3dTipos")),
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
    u = await _get_db().users.find_one(
        {"id": user_id, "linkedStudio3kAdminId": current_user.get("id")},
        {"_id": 0, "id": 1, "isActive": 1},
    )
    if not u:
        raise HTTPException(status_code=404, detail="Usuario no encontrado en tu estudio")
    new_active = not bool(u.get("isActive", True))
    await _get_db().users.update_one({"id": user_id}, {"$set": {"isActive": new_active}})
    return {"success": True, "isActive": new_active}


@router.delete("/studio3k/remove/{user_id}")
async def studio3k_delete_user(user_id: str, current_user: dict = Depends(require_studio3k_admin)):
    """Elimina un usuario únicamente dentro de su estudio Studio3K."""
    res = await _get_db().users.delete_one(
        {"id": user_id, "linkedStudio3kAdminId": current_user.get("id")}
    )
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado en tu estudio")
    return {"success": True}
