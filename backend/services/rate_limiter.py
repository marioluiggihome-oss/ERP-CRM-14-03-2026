"""
Rate Limiting Service
Protege contra ataques de fuerza bruta y abuso de API
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

# Configuración del limiter
limiter = Limiter(key_func=get_remote_address)

# Límites por tipo de endpoint
RATE_LIMITS = {
    # Autenticación - más restrictivo para prevenir fuerza bruta
    "login": "5/minute",
    "register": "3/minute",
    
    # Endpoints sensibles
    "password_change": "3/minute",
    "user_create": "10/minute",
    "user_delete": "5/minute",
    
    # Endpoints de lectura - más permisivos
    "read": "100/minute",
    "list": "60/minute",
    
    # Endpoints de escritura
    "write": "30/minute",
    "bulk_write": "10/minute",
    
    # AI endpoints - costosos
    "ai_analysis": "10/minute",
    "ai_generation": "5/minute",
    
    # Exports y backups
    "export": "10/minute",
    "backup": "5/minute",
    
    # Default
    "default": "60/minute"
}


def get_limit(limit_type: str) -> str:
    """Obtener el límite para un tipo de operación"""
    return RATE_LIMITS.get(limit_type, RATE_LIMITS["default"])


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Handler personalizado para cuando se excede el rate limit
    """
    logger.warning(f"Rate limit exceeded: {request.client.host} - {request.url.path}")
    
    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "detail": "Demasiadas solicitudes. Por favor, espere un momento antes de intentar de nuevo.",
            "retry_after": str(exc.detail).split("per")[0].strip() if exc.detail else "1 minute"
        }
    )


def get_client_identifier(request: Request) -> str:
    """
    Obtener identificador único del cliente para rate limiting
    Combina IP + User Agent para mejor identificación
    """
    ip = get_remote_address(request)
    user_agent = request.headers.get("User-Agent", "unknown")[:50]
    return f"{ip}:{hash(user_agent) % 10000}"
