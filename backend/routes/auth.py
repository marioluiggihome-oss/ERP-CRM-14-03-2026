"""
Router para Autenticación - Login, Logout, Refresh Token
"""
import logging
import bcrypt
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config import db
from services.jwt_service import (
    create_access_token,
    create_refresh_token,
    verify_access_token,
    verify_refresh_token,
    security
)
from services.rate_limiter import limiter, get_limit
from services.audit_service import audit, AuditAction

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except:
        return password == hashed


def user_to_response(user_doc: dict) -> dict:
    """Convert user document to response (remove password)"""
    result = {k: v for k, v in user_doc.items() if k != "password"}
    return result


@router.post("/login")
@limiter.limit(get_limit("login"))
async def login(request: Request, credentials: dict):
    """Iniciar sesión con verificación de password hasheado + JWT + Auditoría"""
    username = credentials.get("username", "").upper().strip()
    password = credentials.get("password", "").strip()
    
    user = await db.users.find_one({"username": username}, {"_id": 0})
    if not user:
        audit.log_login_failed(username, request, "user_not_found")
        raise HTTPException(status_code=401, detail="Credenciales no válidas")
    
    if not verify_password(password, user.get("password", "")):
        audit.log_login_failed(username, request, "invalid_password")
        raise HTTPException(status_code=401, detail="Credenciales no válidas")
    
    if not user.get("isActive", True):
        audit.log_login_failed(username, request, "account_disabled")
        raise HTTPException(status_code=401, detail="Cuenta desactivada")
    
    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user.get("id"))
    
    audit.log_login_success(user.get("id"), username, request)
    
    return {
        "success": True, 
        "user": user_to_response(user),
        "tokens": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 86400
        }
    }


@router.post("/refresh")
@limiter.limit(get_limit("login"))
async def refresh_token(request: Request, data: dict):
    """Renovar access token usando refresh token"""
    refresh_token_str = data.get("refresh_token", "")
    
    if not refresh_token_str:
        raise HTTPException(status_code=400, detail="Refresh token requerido")
    
    try:
        payload = verify_refresh_token(refresh_token_str)
        user_id = payload.get("sub")
        
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="Usuario no encontrado")
        
        if not user.get("isActive", True):
            raise HTTPException(status_code=401, detail="Cuenta desactivada")
        
        new_access_token = create_access_token(user)
        
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


@router.post("/logout")
async def logout(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Cerrar sesión"""
    user = None
    if credentials:
        try:
            payload = verify_access_token(credentials.credentials)
            user = {"id": payload.get("sub"), "username": payload.get("username")}
        except:
            pass
    
    if user:
        audit.log(
            AuditAction.LOGOUT,
            user_id=user.get("id"),
            username=user.get("username"),
            resource_type="session",
            request=request
        )
    
    return {"success": True, "message": "Sesión cerrada"}


@router.get("/me")
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
        
        user = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        return {"success": True, "user": user}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get current user error: {e}")
        raise HTTPException(status_code=401, detail="Token inválido")
