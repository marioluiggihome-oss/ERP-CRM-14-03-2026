"""
LUIGGI HOME ERP — Middleware de Seguridad Global
Protege TODAS las rutas. Solo /api/auth/* es pública.
"""
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import os
import jwt

logger = logging.getLogger(__name__)

RUTAS_PUBLICAS = [
    "/api/auth/login",
    "/api/auth/refresh",
    "/api/auth/logout",
    "/api/auth/2fa",
    "/api/auth/register",
    "/api/health",
    "/api/",
    "/docs",
    "/openapi.json",
    "/redoc",
]

JWT_SECRET = os.environ.get("JWT_SECRET", "")
JWT_ALGORITHM = "HS256"


class SecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if any(path.startswith(r) for r in RUTAS_PUBLICAS):
            return await call_next(request)

        if request.method == "OPTIONS":
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Autenticación requerida. Inicia sesión."}
            )

        token = auth_header[7:]
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            if payload.get("type") != "access":
                raise ValueError("Token inválido")
            request.state.current_user = {
                "id": payload.get("sub"),
                "username": payload.get("username"),
                "isAdmin": payload.get("isAdmin", False),
            }
        except jwt.ExpiredSignatureError:
            return JSONResponse(
                status_code=401,
                content={"detail": "Sesión expirada. Inicia sesión de nuevo."}
            )
        except Exception:
            return JSONResponse(
                status_code=401,
                content={"detail": "Token inválido. Inicia sesión."}
            )

        return await call_next(request)
