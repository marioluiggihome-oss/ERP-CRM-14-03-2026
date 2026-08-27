# © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
Services package
"""
from .database import db, get_database, close_database
from .auth_service import hash_password, verify_password
from .email_service import send_email, send_backup_email, send_order_confirmation
from .jwt_service import (
    create_access_token, 
    create_refresh_token, 
    decode_token,
    verify_access_token,
    verify_refresh_token,
    get_current_user,
    require_auth,
    require_admin,
    get_token_from_request
)
from .rate_limiter import limiter, get_limit, rate_limit_exceeded_handler
from .audit_service import audit, AuditAction, AuditLogger
