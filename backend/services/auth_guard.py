"""
Guard de autenticación global (Fase 2).

Centraliza la allowlist de rutas públicas y el flag de activación que usa el
middleware de `server.py`. Se mantiene SIN dependencias pesadas (solo `os`) para
poder testear la lógica de allowlist de forma aislada.

Activación: variable de entorno ENFORCE_GLOBAL_AUTH.
  - Desactivado (por defecto): "0" / vacío / "false" / "off"  -> el backend se
    comporta como hasta ahora (solo protegen los endpoints con Depends(...)).
  - Activado: "1" / "true" / "yes" / "on" -> TODO /api/* exige un JWT válido
    salvo las rutas de PUBLIC_API_PATHS.

Rollback instantáneo: poner ENFORCE_GLOBAL_AUTH=0 y redeplegar.
"""
import os

# Rutas públicas (accesibles sin token). Todo lo que el frontend necesita ANTES
# de tener sesión: login / registro / verificación / recuperación / refresh, el
# estado de mantenimiento (lo consulta la pantalla de carga) y el formulario
# público de solicitud de distribuidor de la página de login. La raíz "/api/"
# es el health-check.
PUBLIC_API_PATHS = frozenset({
    "/api",
    "/api/auth/login",
    "/api/auth/login-email",
    "/api/auth/refresh",
    "/api/auth/logout",
    "/api/auth/register",
    "/api/auth/verify-email",
    "/api/auth/resend-verification",
    "/api/auth/forgot-password",
    "/api/auth/reset-password",
    "/api/maintenance/status",
    "/api/distributor/request",
    "/api/settings/public-logo",
})

_TRUTHY = ("1", "true", "yes", "on")


def is_global_auth_enabled() -> bool:
    """¿Está activada la exigencia de auth global? (lee ENFORCE_GLOBAL_AUTH)."""
    return os.environ.get("ENFORCE_GLOBAL_AUTH", "0").strip().lower() in _TRUTHY


def is_public_api_path(path: str) -> bool:
    """True si `path` es una ruta pública (no requiere token).

    Se normaliza quitando la barra final (excepto la raíz) para que tanto
    "/api/auth/login" como "/api/auth/login/" se traten igual. La comparación es
    exacta, de modo que "/api/distributor/requests" (admin) NO coincide con la
    pública "/api/distributor/request".
    """
    p = path[:-1] if (len(path) > 1 and path.endswith("/")) else path
    return p in PUBLIC_API_PATHS
