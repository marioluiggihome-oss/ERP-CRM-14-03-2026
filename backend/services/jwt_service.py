"""
JWT Authentication Service
Maneja la creación, validación y renovación de tokens JWT
"""
import jwt
import os
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Configuración JWT
# JWT_SECRET es OBLIGATORIO: sin él, la app no debe arrancar (evita secretos por defecto
# inseguros y secretos aleatorios distintos por proceso que invalidarían los tokens).
JWT_SECRET = os.environ.get('JWT_SECRET')
if not JWT_SECRET:
    raise RuntimeError(
        "La variable de entorno JWT_SECRET es obligatoria. "
        "Configúrala con un valor largo y aleatorio (p. ej. `openssl rand -hex 32`)."
    )
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24  # Token expira en 24 horas
JWT_REFRESH_EXPIRATION_DAYS = 7  # Refresh token expira en 7 días

security = HTTPBearer(auto_error=False)


def create_access_token(user_data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Crear un token de acceso JWT
    
    Args:
        user_data: Datos del usuario a incluir en el token
        expires_delta: Tiempo de expiración personalizado
    
    Returns:
        Token JWT codificado
    """
    to_encode = {
        "sub": user_data.get("id"),
        "username": user_data.get("username"),
        "isAdmin": user_data.get("isAdmin", False),
        "isResponsableDelegacion": user_data.get("isResponsableDelegacion", False),
        "isRepresentative": user_data.get("isRepresentative", False),
        "isTienda": user_data.get("isTienda", False),
        "isPrescriptor": user_data.get("isPrescriptor", False),
        "isGerente": user_data.get("isGerente", False),
        "isDirectorComercial": user_data.get("isDirectorComercial", False),
        "isDirectorFabrica": user_data.get("isDirectorFabrica", False),
        "iat": datetime.now(timezone.utc),
        "type": "access"
    }
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    
    to_encode["exp"] = expire
    
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """
    Crear un refresh token para renovar el access token
    
    Args:
        user_id: ID del usuario
    
    Returns:
        Refresh token JWT
    """
    expire = datetime.now(timezone.utc) + timedelta(days=JWT_REFRESH_EXPIRATION_DAYS)
    
    to_encode = {
        "sub": user_id,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh"
    }
    
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decodificar y validar un token JWT
    
    Args:
        token: Token JWT a decodificar
    
    Returns:
        Payload del token decodificado
    
    Raises:
        HTTPException: Si el token es inválido o ha expirado
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")


def verify_access_token(token: str) -> Dict[str, Any]:
    """
    Verificar que es un access token válido
    """
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Tipo de token inválido")
    return payload


def verify_refresh_token(token: str) -> Dict[str, Any]:
    """
    Verificar que es un refresh token válido
    """
    payload = decode_token(token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Tipo de token inválido")
    return payload


def _payload_to_user(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Construir el dict de usuario a partir del payload del token JWT."""
    return {
        "id": payload.get("sub"),
        "username": payload.get("username"),
        "isAdmin": payload.get("isAdmin", False),
        "isResponsableDelegacion": payload.get("isResponsableDelegacion", False),
        "isRepresentative": payload.get("isRepresentative", False),
        "isTienda": payload.get("isTienda", False),
        "isPrescriptor": payload.get("isPrescriptor", False),
        "isGerente": payload.get("isGerente", False),
        "isDirectorComercial": payload.get("isDirectorComercial", False),
        "isDirectorFabrica": payload.get("isDirectorFabrica", False),
    }


# Roles considerados "elevados" para acceso administrativo / de dirección.
ADMIN_ROLE_FLAGS = (
    "isAdmin",
    "isResponsableDelegacion",
    "isGerente",
    "isDirectorComercial",
    "isDirectorFabrica",
)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Optional[Dict[str, Any]]:
    """
    Dependency para obtener el usuario actual del token JWT

    Uso en endpoints:
        @router.get("/protected")
        async def protected_route(current_user: dict = Depends(get_current_user)):
            ...
    """
    if not credentials:
        return None

    try:
        payload = verify_access_token(credentials.credentials)
        return _payload_to_user(payload)
    except HTTPException:
        return None


async def require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Dependency que REQUIERE autenticación (lanza error si no hay token)

    Uso en endpoints:
        @router.get("/protected")
        async def protected_route(current_user: dict = Depends(require_auth)):
            ...
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="Autenticación requerida")

    payload = verify_access_token(credentials.credentials)
    return _payload_to_user(payload)


async def require_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Dependency que requiere un rol elevado (admin, responsable de delegación,
    gerente, director comercial o director de fábrica).
    """
    user = await require_auth(credentials)
    if not any(user.get(flag) for flag in ADMIN_ROLE_FLAGS):
        raise HTTPException(status_code=403, detail="Acceso denegado: se requiere rol de administrador")
    return user


def get_token_from_request(request: Request) -> Optional[str]:
    """
    Extraer token del header Authorization
    """
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:]
    return None
