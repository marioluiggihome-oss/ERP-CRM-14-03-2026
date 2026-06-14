"""
Manejador centralizado de errores para FastAPI.
Proporciona respuestas consistentes y logging automático de errores.
"""

import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Excepción base para errores de API"""
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        detail: Optional[str] = None,
        error_code: Optional[str] = None
    ):
        self.message = message
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code or "INTERNAL_ERROR"
        super().__init__(self.message)


class ValidationError(APIError):
    """Error de validación de datos"""
    def __init__(self, message: str, detail: Optional[str] = None):
        super().__init__(message, status_code=422, detail=detail, error_code="VALIDATION_ERROR")


class AuthenticationError(APIError):
    """Error de autenticación"""
    def __init__(self, message: str = "Autenticación requerida", detail: Optional[str] = None):
        super().__init__(message, status_code=401, detail=detail, error_code="AUTHENTICATION_ERROR")


class AuthorizationError(APIError):
    """Error de autorización"""
    def __init__(self, message: str = "Acceso denegado", detail: Optional[str] = None):
        super().__init__(message, status_code=403, detail=detail, error_code="AUTHORIZATION_ERROR")


class NotFoundError(APIError):
    """Error de recurso no encontrado"""
    def __init__(self, message: str = "Recurso no encontrado", detail: Optional[str] = None):
        super().__init__(message, status_code=404, detail=detail, error_code="NOT_FOUND")


class ConflictError(APIError):
    """Error de conflicto (ej. recurso duplicado)"""
    def __init__(self, message: str, detail: Optional[str] = None):
        super().__init__(message, status_code=409, detail=detail, error_code="CONFLICT")


class DatabaseError(APIError):
    """Error de base de datos"""
    def __init__(self, message: str = "Error de base de datos", detail: Optional[str] = None):
        super().__init__(message, status_code=500, detail=detail, error_code="DATABASE_ERROR")


class ExternalServiceError(APIError):
    """Error de servicio externo (ej. SendGrid)"""
    def __init__(self, message: str, detail: Optional[str] = None):
        super().__init__(message, status_code=503, detail=detail, error_code="SERVICE_UNAVAILABLE")


def build_error_response(
    error: Exception,
    status_code: int = 500,
    request_id: Optional[str] = None
) -> Dict[str, Any]:
    """Construir una respuesta de error consistente"""
    return {
        "success": False,
        "error": str(error),
        "status_code": status_code,
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": request_id
    }


async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """Manejador para errores de API personalizados"""
    request_id = request.headers.get("X-Request-ID", "unknown")
    
    # Log del error
    log_level = logging.WARNING if exc.status_code < 500 else logging.ERROR
    logger.log(
        log_level,
        f"API Error [{exc.error_code}] {exc.status_code}: {exc.message}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "detail": exc.detail
        }
    )
    
    response_data = {
        "success": False,
        "error": exc.message,
        "error_code": exc.error_code,
        "status_code": exc.status_code,
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": request_id
    }
    
    if exc.detail:
        response_data["detail"] = exc.detail
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_data
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Manejador para errores de validación de Pydantic"""
    request_id = request.headers.get("X-Request-ID", "unknown")
    
    # Extraer detalles de validación
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(x) for x in error["loc"][1:]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.warning(
        f"Validation Error: {len(errors)} field(s) failed validation",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "errors": errors
        }
    )
    
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "error": "Errores de validación",
            "error_code": "VALIDATION_ERROR",
            "status_code": 422,
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id,
            "validation_errors": errors
        }
    )


async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Manejador genérico para excepciones no capturadas"""
    request_id = request.headers.get("X-Request-ID", "unknown")
    
    logger.error(
        f"Unhandled Exception: {type(exc).__name__}: {str(exc)}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method
        },
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Error interno del servidor",
            "error_code": "INTERNAL_ERROR",
            "status_code": 500,
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_id
        }
    )


def setup_error_handlers(app: FastAPI):
    """Registrar todos los manejadores de error en la aplicación FastAPI"""
    app.add_exception_handler(APIError, api_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, generic_error_handler)
