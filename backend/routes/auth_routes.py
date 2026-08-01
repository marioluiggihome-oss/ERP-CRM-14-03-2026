"""
Router de AUTENTICACIÓN — extraído tal cual de server.py (endpoints vivos, mismo orden de rutas).
"""
import io
import re
import csv
import uuid
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends, Request, Response
from fastapi.responses import StreamingResponse

from services.db_client import get_db as _get_db_singleton
db = _get_db_singleton()
from services.jwt_service import (
    get_current_user, require_auth, require_admin, ADMIN_ROLE_FLAGS,
    create_access_token, create_refresh_token, verify_refresh_token,
    verify_access_token, security,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Auth"])


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash (supports bcrypt, sha256, and plain text)"""
    # Si está vacío, rechazar
    if not password or not hashed:
        return False
    
    # Intento 1: bcrypt hash (empieza con $2b$ o $2a$)
    if hashed.startswith('$2b$') or hashed.startswith('$2a$'):
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception:
            return False
    
    # Intento 2: SHA256 hash (64 caracteres hexadecimales) - solo cuentas heredadas
    if len(hashed) == 64:
        try:
            sha256_hash = hashlib.sha256(password.encode()).hexdigest()
            return sha256_hash == hashed
        except Exception:
            pass

    # No se admite comparación en texto plano: si el hash no es bcrypt ni sha256, rechazar.
    return False


def user_to_response(user_doc: dict) -> dict:
    """Convert user document to response (excluding password)"""
    return {k: v for k, v in user_doc.items() if k != "password"}


import bcrypt
import hashlib
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from services.rate_limiter import limiter, get_limit
from services.activity_tracker import get_tracker, ActivityType
from services.audit_service import audit, AuditAction


@router.post("/auth/login")
@limiter.limit(get_limit("login"))
async def login(request: Request, credentials: dict):
    """Iniciar sesión con verificación de password hasheado + JWT + Auditoría"""
    username = credentials.get("username", "").strip()
    password = credentials.get("password", "").strip()
    
    # Buscar por username exacto o en mayúsculas (compatibilidad con cuentas antiguas)
    user = await db.users.find_one({"username": username}, {"_id": 0})
    if not user:
        # Intentar búsqueda en mayúsculas
        user = await db.users.find_one({"username": username.upper()}, {"_id": 0})
    if not user:
        # Intentar búsqueda case-insensitive (escapando metacaracteres regex)
        user = await db.users.find_one(
            {"username": {"$regex": f"^{re.escape(username)}$", "$options": "i"}},
            {"_id": 0}
        )
    
    if not user:
        # Auditoría: login fallido
        audit.log_login_failed(username, request, "user_not_found")
        raise HTTPException(status_code=401, detail="Credenciales no válidas")
    
    # Verify password (supports both hashed and plain text for migration)
    if not verify_password(password, user.get("password", "")):
        # Auditoría: login fallido
        audit.log_login_failed(username, request, "invalid_password")
        raise HTTPException(status_code=401, detail="Credenciales no válidas")
    
    if not user.get("isActive", True):
        # Auditoría: cuenta desactivada
        audit.log_login_failed(username, request, "account_disabled")
        raise HTTPException(status_code=401, detail="Cuenta desactivada")
    
    # Verificar fecha de caducidad del acceso
    expiration_date = user.get("accessExpirationDate")
    if expiration_date:
        try:
            exp_date = datetime.fromisoformat(expiration_date.replace('Z', '+00:00')) if isinstance(expiration_date, str) else expiration_date
            if exp_date.date() < datetime.now().date():
                audit.log_login_failed(username, request, "access_expired")
                raise HTTPException(
                    status_code=401, 
                    detail=f"Tu acceso expiró el {exp_date.strftime('%d/%m/%Y')}. Contacta con el administrador para renovar."
                )
        except (ValueError, AttributeError) as e:
            logger.warning(f"Error parsing expiration date for {username}: {e}")
    
    # ─── Sesión única: verificar si ya hay una sesión activa ───
    # Los usuarios admin/master (y el admin de division carpinteros) pueden tener
    # varias sesiones simultaneas.
    is_admin_user = any(user.get(flag) for flag in ("isAdmin", "isResponsableDelegacion", "isGerente", "isDirectorComercial", "isDirectorFabrica", "canManageCarpinteroUsers"))
    force = credentials.get("force", False)
    user_id = user.get("id")
    if not is_admin_user:
        existing_session = await db.active_sessions.find_one({"user_id": user_id})
        if existing_session and not force:
            return {
                "success": False,
                "sessionConflict": True,
                "message": f"Ya hay una sesión activa para este usuario (desde {existing_session.get('login_at', 'desconocido')}). Pulsa 'Forzar acceso' para cerrar la otra sesión."
            }
    else:
        existing_session = None  # admin: no bloquear multi-sesión
    # Limpiar sesión anterior si existe (forzado o nueva)
    if existing_session:
        await db.active_sessions.delete_many({"user_id": user_id})

    # Crear tokens JWT
    session_token = str(uuid.uuid4())
    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user.get("id"))

    # Registrar sesión activa
    await db.active_sessions.insert_one({
        "user_id": user_id,
        "username": username,
        "session_token": session_token,
        "login_at": datetime.now(timezone.utc).isoformat(),
        "ip": request.client.host if request.client else None,
    })
    
    # Auditoría: login exitoso
    audit.log_login_success(user.get("id"), username, request)
    
    # Tracking de actividad
    tracker = get_tracker()
    if tracker:
        await tracker.track(
            user_id=user.get("id"),
            username=username,
            activity_type=ActivityType.LOGIN,
            ip_address=request.client.host if request.client else None
        )
    
    # Return user without password + tokens
    return {
        "success": True, 
        "user": user_to_response(user),
        "tokens": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 86400  # 24 horas en segundos
        }
    }


@router.post("/auth/refresh")
@limiter.limit(get_limit("login"))
async def refresh_token(request: Request, data: dict):
    """Renovar access token usando refresh token"""
    refresh_token_str = data.get("refresh_token", "")
    
    if not refresh_token_str:
        raise HTTPException(status_code=400, detail="Refresh token requerido")
    
    try:
        payload = verify_refresh_token(refresh_token_str)
        user_id = payload.get("sub")
        
        # Obtener usuario actualizado
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="Usuario no encontrado")
        
        if not user.get("isActive", True):
            raise HTTPException(status_code=401, detail="Cuenta desactivada")
        
        # Crear nuevo access token
        new_access_token = create_access_token(user)
        
        # Auditoría
        audit.log(
            AuditAction.TOKEN_REFRESH,
            user_id=user_id,
            username=user.get("username"),
            resource_type="session",
            request=request
        )
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": 86400
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(status_code=401, detail="Token inválido")


@router.post("/auth/logout")
async def logout(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Cerrar sesión (invalida el token en el cliente) y limpia sesión activa"""
    user = None
    if credentials:
        try:
            payload = verify_access_token(credentials.credentials)
            user = {"id": payload.get("sub"), "username": payload.get("username")}
        except Exception:
            pass
    
    if user:
        # Limpiar sesión activa de la colección
        await db.active_sessions.delete_many({"user_id": user.get("id")})
        audit.log(
            AuditAction.LOGOUT,
            user_id=user.get("id"),
            username=user.get("username"),
            resource_type="session",
            request=request
        )
    
    return {"success": True, "message": "Sesión cerrada"}


@router.post("/auth/force-login")
@limiter.limit(get_limit("login"))
async def force_login(request: Request, credentials: dict):
    """Forzar login cerrando la sesión activa anterior"""
    credentials["force"] = True
    return await login(request, credentials)


@router.get("/auth/me")
async def get_current_user_info(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Obtener información del usuario actual desde el token"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Token requerido")
    
    try:
        payload = verify_access_token(credentials.credentials)
        user_id = payload.get("sub")
        
        # Obtener datos completos del usuario
        user = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        return {"success": True, "user": user}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get current user error: {e}")
        raise HTTPException(status_code=401, detail="Token inválido")

# ============================================
# PRODUCT ENDPOINTS
# ============================================
