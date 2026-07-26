"""
Audit Logging Service
Registra todas las acciones importantes para seguridad y compliance
"""
import logging
import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from fastapi import Request
from enum import Enum

logger = logging.getLogger("audit")

# Configurar handler específico para auditoría (best-effort: si el path no es
# escribible, seguimos sin fichero — la persistencia real es en MongoDB).
try:
    audit_handler = logging.FileHandler("/var/log/luiggi_audit.log")
    audit_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))
    logger.addHandler(audit_handler)
except Exception:
    pass
logger.setLevel(logging.INFO)

# Persistencia en MongoDB (colección db.audit_log). Cliente SÍNCRONO (pymongo) para
# poder escribir desde el método estático `log()` sin depender del bucle asíncrono.
# El registro es best-effort: nunca debe romper la operación auditada.
try:
    from pymongo import MongoClient as _SyncMongoClient
    _audit_sync_client = _SyncMongoClient(
        os.environ.get("MONGO_URL", "mongodb://localhost:27017"),
        serverSelectionTimeoutMS=800,
    )
    _audit_db = _audit_sync_client[os.environ.get("DB_NAME", "luiggi_home")]
except Exception:  # pragma: no cover
    _audit_db = None


class AuditAction(str, Enum):
    """Tipos de acciones auditables"""
    # Autenticación
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILED = "LOGIN_FAILED"
    LOGOUT = "LOGOUT"
    TOKEN_REFRESH = "TOKEN_REFRESH"
    
    # Usuarios
    USER_CREATE = "USER_CREATE"
    USER_UPDATE = "USER_UPDATE"
    USER_DELETE = "USER_DELETE"
    USER_PERMISSION_CHANGE = "USER_PERMISSION_CHANGE"
    PASSWORD_CHANGE = "PASSWORD_CHANGE"
    
    # Datos sensibles
    CLIENT_VIEW = "CLIENT_VIEW"
    CLIENT_CREATE = "CLIENT_CREATE"
    CLIENT_UPDATE = "CLIENT_UPDATE"
    CLIENT_DELETE = "CLIENT_DELETE"
    
    # CRM
    CONTACT_VIEW = "CONTACT_VIEW"
    CONTACT_CREATE = "CONTACT_CREATE"
    CONTACT_UPDATE = "CONTACT_UPDATE"
    CONTACT_DELETE = "CONTACT_DELETE"
    OPPORTUNITY_CREATE = "OPPORTUNITY_CREATE"
    OPPORTUNITY_UPDATE = "OPPORTUNITY_UPDATE"
    
    # Proyectos/Presupuestos
    PROJECT_CREATE = "PROJECT_CREATE"
    PROJECT_UPDATE = "PROJECT_UPDATE"
    PROJECT_DELETE = "PROJECT_DELETE"
    PROJECT_EXPORT = "PROJECT_EXPORT"
    
    # Sistema
    BACKUP_CREATE = "BACKUP_CREATE"
    BACKUP_RESTORE = "BACKUP_RESTORE"
    SETTINGS_UPDATE = "SETTINGS_UPDATE"
    
    # Seguridad
    UNAUTHORIZED_ACCESS = "UNAUTHORIZED_ACCESS"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    SUSPICIOUS_ACTIVITY = "SUSPICIOUS_ACTIVITY"


class AuditLogger:
    """
    Logger de auditoría con contexto enriquecido
    """
    
    @staticmethod
    def _get_request_info(request: Optional[Request]) -> Dict[str, str]:
        """Extraer información relevante del request"""
        if not request:
            return {}
        
        return {
            "ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("User-Agent", "unknown")[:100],
            "path": str(request.url.path),
            "method": request.method
        }
    
    @staticmethod
    def log(
        action: AuditAction,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None,
        success: bool = True
    ):
        """
        Registrar una acción en el log de auditoría
        
        Args:
            action: Tipo de acción realizada
            user_id: ID del usuario que realiza la acción
            username: Nombre del usuario
            resource_type: Tipo de recurso afectado (user, client, project, etc.)
            resource_id: ID del recurso afectado
            details: Detalles adicionales
            request: Request de FastAPI para extraer IP/UA
            success: Si la acción fue exitosa
        """
        request_info = AuditLogger._get_request_info(request)
        
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action.value,
            "success": success,
            "user_id": user_id or "anonymous",
            "username": username or "anonymous",
            "resource_type": resource_type,
            "resource_id": resource_id,
            "ip": request_info.get("ip", "unknown"),
            "user_agent": request_info.get("user_agent", "unknown"),
            "path": request_info.get("path"),
            "method": request_info.get("method"),
            "details": details
        }
        
        # Formatear como string para el log
        log_msg = (
            f"{action.value} | "
            f"user={username or user_id or 'anonymous'} | "
            f"resource={resource_type}:{resource_id or 'N/A'} | "
            f"ip={request_info.get('ip', 'unknown')} | "
            f"success={success}"
        )
        
        if details:
            log_msg += f" | details={details}"
        
        if success:
            logger.info(log_msg)
        else:
            logger.warning(log_msg)

        # Persistir en MongoDB para que la auditoría sea CONSULTABLE (no solo en el
        # log del proceso, que en un entorno efímero se pierde). Best-effort.
        if _audit_db is not None:
            try:
                _audit_db.audit_log.insert_one(dict(log_entry))
            except Exception as e:
                logger.debug(f"audit persist failed: {e}")

        return log_entry
    
    @staticmethod
    def log_login_success(user_id: str, username: str, request: Request):
        """Log de login exitoso"""
        return AuditLogger.log(
            action=AuditAction.LOGIN_SUCCESS,
            user_id=user_id,
            username=username,
            resource_type="session",
            request=request,
            success=True
        )
    
    @staticmethod
    def log_login_failed(username: str, request: Request, reason: str = "invalid_credentials"):
        """Log de login fallido"""
        return AuditLogger.log(
            action=AuditAction.LOGIN_FAILED,
            username=username,
            resource_type="session",
            request=request,
            details={"reason": reason},
            success=False
        )
    
    @staticmethod
    def log_unauthorized_access(request: Request, reason: str):
        """Log de intento de acceso no autorizado"""
        return AuditLogger.log(
            action=AuditAction.UNAUTHORIZED_ACCESS,
            resource_type="system",
            request=request,
            details={"reason": reason},
            success=False
        )
    
    @staticmethod
    def log_data_access(
        action: AuditAction,
        user_id: str,
        username: str,
        resource_type: str,
        resource_id: str,
        request: Request
    ):
        """Log de acceso a datos"""
        return AuditLogger.log(
            action=action,
            user_id=user_id,
            username=username,
            resource_type=resource_type,
            resource_id=resource_id,
            request=request,
            success=True
        )


# Instancia global para uso fácil
audit = AuditLogger()
