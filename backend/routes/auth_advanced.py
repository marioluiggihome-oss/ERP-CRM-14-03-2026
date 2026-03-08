"""
Router para Autenticación Avanzada - Registro con Email y 2FA
"""
import os
import re
import uuid
import base64
import secrets
import logging
import asyncio
from io import BytesIO
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Request, Depends, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

import bcrypt
import pyotp
import qrcode
import resend

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

# Configurar Resend
resend.api_key = os.environ.get('RESEND_API_KEY')


async def send_email_with_resend(to_email: str, subject: str, html_content: str) -> bool:
    """Enviar email usando Resend API (async/non-blocking)"""
    try:
        api_key = os.environ.get('RESEND_API_KEY')
        if not api_key:
            logger.warning("RESEND_API_KEY not configured, email not sent")
            return False
        
        resend.api_key = api_key
        
        # Resend con cuenta gratuita solo permite enviar a emails verificados
        # Usamos onboarding@resend.dev como remitente (dominio de prueba de Resend)
        params = {
            "from": "LUIGGI HOME <onboarding@resend.dev>",
            "to": [to_email],
            "subject": subject,
            "html": html_content
        }
        
        # Ejecutar en thread para mantener FastAPI non-blocking
        email = await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"Email sent to {to_email} via Resend: {email.get('id')}")
        return True
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error sending email with Resend to {to_email}: {error_msg}")
        
        # Si el error es por restricción de dominio, intentar enviar al email de backup
        if "only send testing emails to your own email" in error_msg:
            backup_email = os.environ.get('BACKUP_EMAIL', 'marioluiggihome@gmail.com')
            logger.info(f"Resend domain restriction - redirecting email to backup: {backup_email}")
            try:
                # Modificar el contenido para indicar el destinatario original
                modified_html = f'''
                <div style="background: #fef3c7; padding: 10px; margin-bottom: 15px; border-radius: 8px; border-left: 4px solid #f59e0b;">
                    <strong>📧 Email originalmente para:</strong> {to_email}
                </div>
                {html_content}
                '''
                params_backup = {
                    "from": "LUIGGI HOME <onboarding@resend.dev>",
                    "to": [backup_email],
                    "subject": f"[REDIRIGIDO] {subject}",
                    "html": modified_html
                }
                email = await asyncio.to_thread(resend.Emails.send, params_backup)
                logger.info(f"Email redirected to backup {backup_email} via Resend: {email.get('id')}")
                return True
            except Exception as e2:
                logger.error(f"Error sending to backup email: {e2}")
        return False


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


def get_email_template(content: str, title: str = "LUIGGI HOME") -> str:
    """Genera una plantilla de email moderna con el logo de LUIGGI HOME"""
    # Logo SVG de LUIGGI HOME embebido en base64
    logo_svg = '''
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 60" width="200" height="60">
      <defs>
        <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style="stop-color:#1e1b4b"/>
          <stop offset="100%" style="stop-color:#4338ca"/>
        </linearGradient>
      </defs>
      <rect width="200" height="60" rx="8" fill="url(#bgGrad)"/>
      <text x="100" y="32" text-anchor="middle" font-family="Georgia, serif" font-size="28" font-weight="bold" font-style="italic" fill="white">luiggi</text>
      <text x="100" y="50" text-anchor="middle" font-family="Arial, sans-serif" font-size="14" font-weight="900" letter-spacing="4" fill="#f97316">HOME</text>
    </svg>
    '''
    import base64
    logo_base64 = base64.b64encode(logo_svg.strip().encode()).decode()
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f8fafc; padding: 40px 20px;">
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 16px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); overflow: hidden;">
                        <!-- Header con Logo -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #4338ca 100%); padding: 30px; text-align: center;">
                                <img src="data:image/svg+xml;base64,{logo_base64}" alt="LUIGGI HOME" style="max-width: 200px; height: auto;" />
                            </td>
                        </tr>
                        
                        <!-- Barra naranja decorativa -->
                        <tr>
                            <td style="background: linear-gradient(90deg, #ea580c 0%, #f97316 50%, #fb923c 100%); height: 6px;"></td>
                        </tr>
                        
                        <!-- Contenido -->
                        <tr>
                            <td style="padding: 40px;">
                                {content}
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="background-color: #f1f5f9; padding: 30px; text-align: center; border-top: 1px solid #e2e8f0;">
                                <p style="margin: 0 0 10px; font-size: 12px; color: #64748b;">
                                    LUIGGI HOME — Sistema de Gestión de Cocinas
                                </p>
                                <p style="margin: 0; font-size: 11px; color: #94a3b8;">
                                    Este es un mensaje automático. Por favor no responda a este correo.
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    '''


async def send_verification_email(email: str, code: str, name: str = "Usuario"):
    """Send verification email with modern design using Resend"""
    try:
        content = f'''
        <h2 style="margin: 0 0 20px; font-size: 24px; font-weight: 700; color: #1e293b;">
            ¡Hola {name}! 👋
        </h2>
        <p style="margin: 0 0 30px; font-size: 16px; color: #475569; line-height: 1.6;">
            Gracias por registrarte en <strong>LUIGGI HOME</strong>. Para completar tu registro, introduce el siguiente código de verificación:
        </p>
        
        <div style="background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); padding: 30px; text-align: center; margin: 0 0 30px; border-radius: 12px; border: 2px solid #e2e8f0;">
            <p style="margin: 0 0 10px; font-size: 12px; color: #64748b; text-transform: uppercase; letter-spacing: 2px;">Tu código de verificación</p>
            <span style="font-size: 42px; font-weight: 900; letter-spacing: 12px; color: #ea580c; font-family: monospace;">{code}</span>
        </div>
        
        <div style="background-color: #fef3c7; padding: 16px; border-radius: 8px; border-left: 4px solid #f59e0b; margin: 0 0 20px;">
            <p style="margin: 0; font-size: 14px; color: #92400e;">
                ⏰ <strong>Este código expira en 15 minutos.</strong>
            </p>
        </div>
        
        <p style="margin: 0; font-size: 13px; color: #94a3b8;">
            Si no solicitaste esta verificación, puedes ignorar este correo de forma segura.
        </p>
        '''
        
        html_content = get_email_template(content, "Verifica tu cuenta")
        
        return await send_email_with_resend(
            to_email=email,
            subject='🔐 Verifica tu cuenta - LUIGGI HOME',
            html_content=html_content
        )
    except Exception as e:
        logger.error(f"Error sending verification email: {e}")
        return False


async def send_admin_notification(new_user_email: str, new_user_name: str, registration_time: str):
    """Send notification to admin when a new user registers using Resend"""
    try:
        admin_email = os.environ.get('ADMIN_EMAIL', 'mario@luiggihome.es')
        
        content = f'''
        <div style="text-align: center; margin-bottom: 30px;">
            <span style="display: inline-block; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; padding: 8px 20px; border-radius: 20px; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px;">
                🎉 Nuevo Registro
            </span>
        </div>
        
        <h2 style="margin: 0 0 20px; font-size: 22px; font-weight: 700; color: #1e293b; text-align: center;">
            Se ha registrado un nuevo usuario
        </h2>
        
        <div style="background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); padding: 25px; border-radius: 12px; border: 2px solid #e2e8f0; margin: 0 0 25px;">
            <table width="100%" cellpadding="8" cellspacing="0">
                <tr>
                    <td style="font-size: 13px; color: #64748b; text-transform: uppercase; letter-spacing: 1px; width: 120px;">Nombre:</td>
                    <td style="font-size: 16px; font-weight: 600; color: #1e293b;">{new_user_name}</td>
                </tr>
                <tr>
                    <td style="font-size: 13px; color: #64748b; text-transform: uppercase; letter-spacing: 1px;">Email:</td>
                    <td style="font-size: 16px; font-weight: 600; color: #4338ca;">{new_user_email}</td>
                </tr>
                <tr>
                    <td style="font-size: 13px; color: #64748b; text-transform: uppercase; letter-spacing: 1px;">Fecha:</td>
                    <td style="font-size: 15px; color: #475569;">{registration_time}</td>
                </tr>
                <tr>
                    <td style="font-size: 13px; color: #64748b; text-transform: uppercase; letter-spacing: 1px;">Estado:</td>
                    <td>
                        <span style="display: inline-block; background-color: #fef3c7; color: #92400e; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600;">
                            ⏳ Pendiente de verificación
                        </span>
                    </td>
                </tr>
            </table>
        </div>
        
        <p style="margin: 0; font-size: 14px; color: #64748b; text-align: center;">
            El usuario recibirá un código para verificar su email.<br>
            Una vez verificado, podrás asignarle permisos desde el panel de administración.
        </p>
        '''
        
        html_content = get_email_template(content, "Nuevo Registro")
        
        return await send_email_with_resend(
            to_email=admin_email,
            subject=f'👤 Nuevo registro: {new_user_name} - LUIGGI HOME',
            html_content=html_content
        )
    except Exception as e:
        logger.error(f"Error sending admin notification: {e}")
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
    
    # Enviar email de verificación al usuario
    background_tasks.add_task(
        send_verification_email,
        data.email,
        verification_code,
        data.firstName
    )
    
    # Enviar notificación al administrador
    registration_time = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
    background_tasks.add_task(
        send_admin_notification,
        data.email,
        f"{data.firstName} {data.lastName}",
        registration_time
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
    """Enviar email de reset de contraseña con diseño moderno usando Resend"""
    try:
        content = f'''
        <h2 style="margin: 0 0 20px; font-size: 24px; font-weight: 700; color: #1e293b;">
            Hola {name} 🔑
        </h2>
        <p style="margin: 0 0 30px; font-size: 16px; color: #475569; line-height: 1.6;">
            Has solicitado restablecer tu contraseña en <strong>LUIGGI HOME</strong>. Usa el siguiente código para continuar:
        </p>
        
        <div style="background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%); padding: 30px; text-align: center; margin: 0 0 30px; border-radius: 12px; border: 2px solid #fecaca;">
            <p style="margin: 0 0 10px; font-size: 12px; color: #991b1b; text-transform: uppercase; letter-spacing: 2px;">Código de recuperación</p>
            <span style="font-size: 42px; font-weight: 900; letter-spacing: 12px; color: #dc2626; font-family: monospace;">{code}</span>
        </div>
        
        <div style="background-color: #fef3c7; padding: 16px; border-radius: 8px; border-left: 4px solid #f59e0b; margin: 0 0 20px;">
            <p style="margin: 0; font-size: 14px; color: #92400e;">
                ⏰ <strong>Este código expira en 30 minutos.</strong>
            </p>
        </div>
        
        <p style="margin: 0; font-size: 13px; color: #94a3b8;">
            Si no solicitaste este cambio, puedes ignorar este correo. Tu contraseña no será modificada.
        </p>
        '''
        
        html_content = get_email_template(content, "Recuperar contraseña")
        
        return await send_email_with_resend(
            to_email=email,
            subject='🔑 Recuperar contraseña - LUIGGI HOME',
            html_content=html_content
        )
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
    
    # Asegurar que expires tenga timezone
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    
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
