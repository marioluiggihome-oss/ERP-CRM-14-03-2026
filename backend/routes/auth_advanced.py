"""
Router para Autenticación Avanzada - Registro con Email y 2FA
"""
import os
import re
import uuid
import base64
import secrets
import logging
from io import BytesIO
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Request, Depends, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

import bcrypt
import pyotp
import qrcode

from config import db
from models.schemas import (
    UserRegisterRequest, UserRegisterResponse,
    EmailVerificationRequest,
    Enable2FARequest, Enable2FAResponse,
    Verify2FARequest, Login2FARequest,
    PasswordResetRequest, PasswordResetConfirmRequest,
    UserProfileUpdate
)
from services.jwt_service import (
    create_access_token,
    create_refresh_token,
    verify_access_token,
    security
)
from services.rate_limiter import limiter, get_limit

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


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password: str) -> tuple[bool, str]:
    """Validate password strength"""
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres"
    if not re.search(r'[A-Z]', password):
        return False, "La contraseña debe contener al menos una mayúscula"
    if not re.search(r'[a-z]', password):
        return False, "La contraseña debe contener al menos una minúscula"
    if not re.search(r'[0-9]', password):
        return False, "La contraseña debe contener al menos un número"
    return True, ""


def generate_verification_code() -> str:
    """Generate a 6-digit verification code"""
    return ''.join([str(secrets.randbelow(10)) for _ in range(6)])


def generate_backup_codes(count: int = 8) -> list[str]:
    """Generate backup codes for 2FA recovery"""
    return [secrets.token_hex(4).upper() for _ in range(count)]


async def send_verification_email(email: str, code: str, name: str = "Usuario"):
    """Send verification email (placeholder - integrate with SendGrid)"""
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
        
        api_key = os.environ.get('SENDGRID_API_KEY')
        if not api_key:
            logger.warning("SendGrid API key not configured, verification email not sent")
            return False
        
        message = Mail(
            from_email='noreply@luiggihome.com',
            to_emails=email,
            subject='Verifica tu cuenta - LUIGGI HOME',
            html_content=f'''
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #ea580c;">¡Hola {name}!</h2>
                <p>Tu código de verificación es:</p>
                <div style="background: #f3f4f6; padding: 20px; text-align: center; margin: 20px 0; border-radius: 8px;">
                    <span style="font-size: 32px; font-weight: bold; letter-spacing: 8px; color: #1e293b;">{code}</span>
                </div>
                <p>Este código expira en 15 minutos.</p>
                <p style="color: #64748b; font-size: 12px;">Si no solicitaste esta verificación, ignora este correo.</p>
            </div>
            '''
        )
        
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        logger.info(f"Verification email sent to {email}: {response.status_code}")
        return True
    except Exception as e:
        logger.error(f"Error sending verification email: {e}")
        return False


@router.post("/register", response_model=UserRegisterResponse)
@limiter.limit("5/minute")
async def register_user(request: Request, data: UserRegisterRequest, background_tasks: BackgroundTasks):
    """
    Registrar nuevo usuario con email.
    Envía código de verificación por email.
    """
    # Validar email
    if not validate_email(data.email):
        raise HTTPException(status_code=400, detail="Formato de email inválido")
    
    # Validar contraseñas
    if data.password != data.confirmPassword:
        raise HTTPException(status_code=400, detail="Las contraseñas no coinciden")
    
    valid, msg = validate_password(data.password)
    if not valid:
        raise HTTPException(status_code=400, detail=msg)
    
    # Verificar si el email ya existe
    existing = await db.users.find_one({"email": data.email.lower()})
    if existing:
        raise HTTPException(status_code=400, detail="Este email ya está registrado")
    
    # Generar código de verificación
    verification_code = generate_verification_code()
    verification_expires = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    # Crear usuario pendiente de verificación
    user_id = f"user-{uuid.uuid4().hex[:8]}"
    username = data.email.split('@')[0].upper()[:20]
    
    # Asegurar username único
    base_username = username
    counter = 1
    while await db.users.find_one({"username": username}):
        username = f"{base_username}{counter}"
        counter += 1
    
    user_doc = {
        "id": user_id,
        "email": data.email.lower(),
        "username": username,
        "password": hash_password(data.password),
        "firstName": data.firstName,
        "lastName": data.lastName,
        "clientName": f"{data.firstName} {data.lastName}",
        "company": data.company,
        "phone": data.phone,
        "isActive": False,  # Pendiente de verificación
        "isEmailVerified": False,
        "emailVerificationCode": verification_code,
        "emailVerificationExpires": verification_expires,
        "isAdmin": False,
        "isGerente": False,
        "isResponsableDelegacion": False,
        "isRepresentative": False,
        "isPrescriptor": False,
        "isTienda": False,
        "allowedModules": ["montada"],
        "allowedCatalogIds": [],
        "commercialDiscount": 0,
        "discountMontada": 0,
        "discountDespiece": 0,
        "canSeeCost": False,
        "canSeeRetail": True,
        "canUseAIAnalysis": False,
        "canManageArticles": False,
        "canViewTechnicalDespiece": False,
        "canAccessCRM": False,
        "canUseDigitalizador": False,
        "canAccessArmarios": False,
        "canAuthorizePermissions": False,
        "useCustomBranding": False,
        "canChangeLogo": False,
        # 2FA fields
        "twoFactorEnabled": False,
        "twoFactorSecret": None,
        "twoFactorBackupCodes": [],
        "createdAt": datetime.now(timezone.utc),
        "updatedAt": datetime.now(timezone.utc)
    }
    
    await db.users.insert_one(user_doc)
    
    # Enviar email de verificación en background
    background_tasks.add_task(
        send_verification_email,
        data.email,
        verification_code,
        data.firstName
    )
    
    logger.info(f"User registered: {data.email}")
    
    return UserRegisterResponse(
        success=True,
        message="Registro exitoso. Revisa tu correo para verificar tu cuenta.",
        userId=user_id,
        requiresEmailVerification=True
    )


@router.post("/verify-email")
@limiter.limit("10/minute")
async def verify_email(request: Request, data: EmailVerificationRequest):
    """Verificar email con código"""
    user = await db.users.find_one({"email": data.email.lower()})
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if user.get("isEmailVerified"):
        return {"success": True, "message": "Email ya verificado"}
    
    stored_code = user.get("emailVerificationCode")
    expires = user.get("emailVerificationExpires")
    
    if not stored_code or not expires:
        raise HTTPException(status_code=400, detail="No hay código de verificación pendiente")
    
    # Asegurar que expires tenga timezone
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    
    if datetime.now(timezone.utc) > expires:
        raise HTTPException(status_code=400, detail="El código ha expirado. Solicita uno nuevo.")
    
    if data.code != stored_code:
        raise HTTPException(status_code=400, detail="Código incorrecto")
    
    # Activar usuario
    await db.users.update_one(
        {"email": data.email.lower()},
        {
            "$set": {
                "isActive": True,
                "isEmailVerified": True,
                "emailVerificationCode": None,
                "emailVerificationExpires": None,
                "updatedAt": datetime.now(timezone.utc)
            }
        }
    )
    
    logger.info(f"Email verified: {data.email}")
    
    return {"success": True, "message": "Email verificado correctamente. Ya puedes iniciar sesión."}


@router.post("/resend-verification")
@limiter.limit("3/minute")
async def resend_verification(request: Request, data: dict, background_tasks: BackgroundTasks):
    """Reenviar código de verificación"""
    email = data.get("email", "").lower()
    
    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if user.get("isEmailVerified"):
        return {"success": True, "message": "Email ya verificado"}
    
    # Generar nuevo código
    verification_code = generate_verification_code()
    verification_expires = datetime.now(timezone.utc) + timedelta(minutes=15)
    
    await db.users.update_one(
        {"email": email},
        {
            "$set": {
                "emailVerificationCode": verification_code,
                "emailVerificationExpires": verification_expires,
                "updatedAt": datetime.now(timezone.utc)
            }
        }
    )
    
    # Enviar email
    background_tasks.add_task(
        send_verification_email,
        email,
        verification_code,
        user.get("firstName", "Usuario")
    )
    
    return {"success": True, "message": "Código reenviado. Revisa tu correo."}


@router.post("/login-email")
@limiter.limit("10/minute")
async def login_with_email(request: Request, data: Login2FARequest):
    """
    Login con email y contraseña.
    Si 2FA está habilitado, requiere código TOTP.
    """
    email = data.email.lower()
    
    user = await db.users.find_one(
        {"$or": [{"email": email}, {"username": email.upper()}]},
        {"_id": 0}
    )
    
    if not user:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    
    if not verify_password(data.password, user.get("password", "")):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    
    if not user.get("isActive", False):
        if not user.get("isEmailVerified", False):
            raise HTTPException(status_code=401, detail="Por favor verifica tu email primero")
        raise HTTPException(status_code=401, detail="Cuenta desactivada")
    
    # Verificar 2FA si está habilitado
    if user.get("twoFactorEnabled"):
        if not data.totpCode:
            return {
                "success": False,
                "requires2FA": True,
                "message": "Se requiere código de autenticación de dos factores"
            }
        
        # Verificar código TOTP
        totp = pyotp.TOTP(user.get("twoFactorSecret"))
        if not totp.verify(data.totpCode, valid_window=1):
            # Verificar códigos de respaldo
            backup_codes = user.get("twoFactorBackupCodes", [])
            if data.totpCode.upper() in backup_codes:
                # Usar y eliminar código de respaldo
                backup_codes.remove(data.totpCode.upper())
                await db.users.update_one(
                    {"id": user["id"]},
                    {"$set": {"twoFactorBackupCodes": backup_codes}}
                )
                logger.info(f"Backup code used for {email}")
            else:
                raise HTTPException(status_code=401, detail="Código 2FA inválido")
    
    # Generar tokens
    access_token = create_access_token(user)
    refresh_token = create_refresh_token(user.get("id"))
    
    # Eliminar campos sensibles
    safe_user = {k: v for k, v in user.items() if k not in ["password", "twoFactorSecret", "twoFactorBackupCodes", "emailVerificationCode"]}
    
    logger.info(f"User logged in: {email}")
    
    return {
        "success": True,
        "user": safe_user,
        "tokens": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 86400
        }
    }


# ============================================
# 2FA ENDPOINTS
# ============================================

@router.post("/2fa/enable", response_model=Enable2FAResponse)
async def enable_2fa(data: Enable2FARequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Habilitar autenticación de dos factores.
    Genera secret y QR code para configurar en app autenticador.
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="Token requerido")
    
    try:
        payload = verify_access_token(credentials.credentials)
        token_user_id = payload.get("sub")
    except:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    # Verificar que el usuario existe
    user = await db.users.find_one({"id": data.userId})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # Solo el propio usuario puede habilitar su 2FA
    if token_user_id != data.userId:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    if user.get("twoFactorEnabled"):
        raise HTTPException(status_code=400, detail="2FA ya está habilitado")
    
    # Generar secret
    secret = pyotp.random_base32()
    
    # Generar códigos de respaldo
    backup_codes = generate_backup_codes(8)
    
    # Generar URI para QR
    totp = pyotp.TOTP(secret)
    email = user.get("email", user.get("username", "user"))
    provisioning_uri = totp.provisioning_uri(
        name=email,
        issuer_name="LUIGGI HOME"
    )
    
    # Generar QR code como base64
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()
    qr_url = f"data:image/png;base64,{qr_base64}"
    
    # Guardar secret temporalmente (no activar hasta verificar)
    await db.users.update_one(
        {"id": data.userId},
        {
            "$set": {
                "twoFactorSecret": secret,
                "twoFactorBackupCodes": backup_codes,
                "twoFactorPending": True,
                "updatedAt": datetime.now(timezone.utc)
            }
        }
    )
    
    logger.info(f"2FA setup initiated for user: {data.userId}")
    
    return Enable2FAResponse(
        success=True,
        secret=secret,
        qrCodeUrl=qr_url,
        backupCodes=backup_codes
    )


@router.post("/2fa/verify")
async def verify_2fa_setup(data: Verify2FARequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verificar y activar 2FA con código TOTP.
    Debe llamarse después de /2fa/enable para confirmar configuración.
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="Token requerido")
    
    try:
        payload = verify_access_token(credentials.credentials)
        token_user_id = payload.get("sub")
    except:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    if token_user_id != data.userId:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    user = await db.users.find_one({"id": data.userId})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    secret = user.get("twoFactorSecret")
    if not secret:
        raise HTTPException(status_code=400, detail="Primero debes iniciar la configuración de 2FA")
    
    # Verificar código
    totp = pyotp.TOTP(secret)
    if not totp.verify(data.code, valid_window=1):
        raise HTTPException(status_code=400, detail="Código incorrecto")
    
    # Activar 2FA
    await db.users.update_one(
        {"id": data.userId},
        {
            "$set": {
                "twoFactorEnabled": True,
                "twoFactorPending": False,
                "updatedAt": datetime.now(timezone.utc)
            }
        }
    )
    
    logger.info(f"2FA enabled for user: {data.userId}")
    
    return {"success": True, "message": "Autenticación de dos factores activada correctamente"}


@router.post("/2fa/disable")
async def disable_2fa(data: Verify2FARequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Desactivar 2FA. Requiere código TOTP para confirmar.
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="Token requerido")
    
    try:
        payload = verify_access_token(credentials.credentials)
        token_user_id = payload.get("sub")
    except:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    if token_user_id != data.userId:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    user = await db.users.find_one({"id": data.userId})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if not user.get("twoFactorEnabled"):
        return {"success": True, "message": "2FA no está habilitado"}
    
    # Verificar código
    totp = pyotp.TOTP(user.get("twoFactorSecret"))
    if not totp.verify(data.code, valid_window=1):
        # Verificar código de respaldo
        backup_codes = user.get("twoFactorBackupCodes", [])
        if data.code.upper() not in backup_codes:
            raise HTTPException(status_code=400, detail="Código incorrecto")
    
    # Desactivar 2FA
    await db.users.update_one(
        {"id": data.userId},
        {
            "$set": {
                "twoFactorEnabled": False,
                "twoFactorSecret": None,
                "twoFactorBackupCodes": [],
                "twoFactorPending": False,
                "updatedAt": datetime.now(timezone.utc)
            }
        }
    )
    
    logger.info(f"2FA disabled for user: {data.userId}")
    
    return {"success": True, "message": "Autenticación de dos factores desactivada"}


@router.get("/2fa/status/{user_id}")
async def get_2fa_status(user_id: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Obtener estado de 2FA de un usuario"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Token requerido")
    
    try:
        payload = verify_access_token(credentials.credentials)
        token_user_id = payload.get("sub")
    except:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    if token_user_id != user_id:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "twoFactorEnabled": 1, "twoFactorBackupCodes": 1})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return {
        "enabled": user.get("twoFactorEnabled", False),
        "backupCodesRemaining": len(user.get("twoFactorBackupCodes", []))
    }


# ============================================
# PASSWORD RESET
# ============================================

@router.post("/forgot-password")
@limiter.limit("3/minute")
async def forgot_password(request: Request, data: PasswordResetRequest, background_tasks: BackgroundTasks):
    """Solicitar reset de contraseña"""
    email = data.email.lower()
    
    user = await db.users.find_one({"email": email})
    
    # No revelar si el email existe
    if not user:
        return {"success": True, "message": "Si el email existe, recibirás instrucciones para resetear tu contraseña"}
    
    # Generar código
    reset_code = generate_verification_code()
    reset_expires = datetime.now(timezone.utc) + timedelta(minutes=30)
    
    await db.users.update_one(
        {"email": email},
        {
            "$set": {
                "passwordResetCode": reset_code,
                "passwordResetExpires": reset_expires,
                "updatedAt": datetime.now(timezone.utc)
            }
        }
    )
    
    # Enviar email
    background_tasks.add_task(
        send_reset_email,
        email,
        reset_code,
        user.get("firstName", "Usuario")
    )
    
    return {"success": True, "message": "Si el email existe, recibirás instrucciones para resetear tu contraseña"}


async def send_reset_email(email: str, code: str, name: str):
    """Enviar email de reset de contraseña"""
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
        
        api_key = os.environ.get('SENDGRID_API_KEY')
        if not api_key:
            logger.warning("SendGrid not configured")
            return False
        
        message = Mail(
            from_email='noreply@luiggihome.com',
            to_emails=email,
            subject='Recuperar contraseña - LUIGGI HOME',
            html_content=f'''
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #ea580c;">Hola {name}</h2>
                <p>Has solicitado restablecer tu contraseña. Tu código es:</p>
                <div style="background: #f3f4f6; padding: 20px; text-align: center; margin: 20px 0; border-radius: 8px;">
                    <span style="font-size: 32px; font-weight: bold; letter-spacing: 8px; color: #1e293b;">{code}</span>
                </div>
                <p>Este código expira en 30 minutos.</p>
                <p style="color: #64748b; font-size: 12px;">Si no solicitaste este cambio, ignora este correo.</p>
            </div>
            '''
        )
        
        sg = SendGridAPIClient(api_key)
        sg.send(message)
        return True
    except Exception as e:
        logger.error(f"Error sending reset email: {e}")
        return False


@router.post("/reset-password")
@limiter.limit("5/minute")
async def reset_password(request: Request, data: PasswordResetConfirmRequest):
    """Confirmar reset de contraseña con código"""
    email = data.email.lower()
    
    if data.newPassword != data.confirmPassword:
        raise HTTPException(status_code=400, detail="Las contraseñas no coinciden")
    
    valid, msg = validate_password(data.newPassword)
    if not valid:
        raise HTTPException(status_code=400, detail=msg)
    
    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    stored_code = user.get("passwordResetCode")
    expires = user.get("passwordResetExpires")
    
    if not stored_code or not expires:
        raise HTTPException(status_code=400, detail="No hay solicitud de reset pendiente")
    
    if datetime.now(timezone.utc) > expires:
        raise HTTPException(status_code=400, detail="El código ha expirado")
    
    if data.code != stored_code:
        raise HTTPException(status_code=400, detail="Código incorrecto")
    
    # Actualizar contraseña
    await db.users.update_one(
        {"email": email},
        {
            "$set": {
                "password": hash_password(data.newPassword),
                "passwordResetCode": None,
                "passwordResetExpires": None,
                "updatedAt": datetime.now(timezone.utc)
            }
        }
    )
    
    logger.info(f"Password reset for: {email}")
    
    return {"success": True, "message": "Contraseña actualizada correctamente"}
