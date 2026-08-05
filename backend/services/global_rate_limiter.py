# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
Global Rate Limiting Middleware
================================
Aplica rate limiting automático a TODOS los endpoints según su tipo,
sin necesidad de decorar cada endpoint individualmente.

Reglas:
- Endpoints de autenticación (/auth/*): 5/min
- Endpoints de exportación (/export*, /products/export*): 10/min
- Endpoints de IA (/ai-engine/*, /analyze*): 10/min
- Endpoints de escritura (POST, PUT, DELETE, PATCH): 30/min
- Endpoints de lectura (GET): 100/min
"""

import time
import logging
from collections import defaultdict
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class GlobalRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware que aplica rate limiting global basado en IP + ruta.
    Usa un token bucket algorithm en memoria (adecuado para single-instance).
    """

    def __init__(self, app, default_rpm: int = 60):
        super().__init__(app)
        self.default_rpm = default_rpm
        # {client_key: {"tokens": float, "last_refill": float}}
        self.buckets = defaultdict(lambda: {"tokens": 0, "last_refill": 0})
        # Reglas por patrón de ruta
        self.rules = [
            # (path_prefix, method, max_requests_per_minute)
            ("/api/auth/login", "POST", 5),
            ("/api/auth/refresh", "POST", 10),
            ("/api/distributor/request", "POST", 3),
            ("/api/products/export", "GET", 10),
            ("/api/ai-engine", None, 10),  # None = cualquier método
            ("/api/analyze", "POST", 10),
            # IA (visión / generación) y exports masivos: caros en coste/tiempo,
            # se limitan más que el resto. Prefijos específicos para no afectar al
            # CRUD normal (p. ej. /api/invoices/... sigue al límite por defecto).
            ("/api/ia-lab", None, 10),            # análisis de planos de cocina con IA
            ("/api/armarios/ia", None, 10),       # generación de layout de armarios con IA
            ("/api/invoices/export", None, 10),   # export contable
            ("/api/export", None, 10),            # exports masivos (clientes/presupuestos/crm/usuarios)
            ("/api/backup", None, 5),
            ("/api/admin", None, 20),
            # Sondeo del análisis de proforma: es una lectura de un solo documento
            # y se repite cada pocos segundos mientras dura el trabajo. Va en su
            # propia categoría para no gastar el cupo general del usuario.
            ("/api/cascos/proforma/job", "GET", 120),
        ]
        # Whitelist - rutas que no se limitan
        self.whitelist = [
            "/api/",  # root health
            "/api/status",
            "/docs",
            "/openapi.json",
        ]

    def _get_client_key(self, request: Request, path: str) -> str:
        """Genera una clave única por cliente + categoría de ruta."""
        ip = request.client.host if request.client else "unknown"
        # Agrupar por categoría de ruta para no mezclar límites
        category = "default"
        for prefix, _, _ in self.rules:
            if path.startswith(prefix):
                category = prefix
                break
        return f"{ip}:{category}"

    def _get_limit_for_request(self, path: str, method: str) -> int:
        """Determina el límite RPM para una ruta y método dados."""
        for prefix, rule_method, rpm in self.rules:
            if path.startswith(prefix):
                if rule_method is None or rule_method == method:
                    return rpm

        # Límites por defecto según método HTTP
        if method in ("POST", "PUT", "DELETE", "PATCH"):
            return 30
        return 100  # GET

    def _check_rate_limit(self, key: str, max_rpm: int) -> bool:
        """
        Token bucket: devuelve True si la request está permitida.
        """
        now = time.time()
        bucket = self.buckets[key]

        if bucket["last_refill"] == 0:
            bucket["tokens"] = max_rpm
            bucket["last_refill"] = now

        # Refill tokens basado en tiempo transcurrido
        elapsed = now - bucket["last_refill"]
        refill = elapsed * (max_rpm / 60.0)  # tokens por segundo
        bucket["tokens"] = min(max_rpm, bucket["tokens"] + refill)
        bucket["last_refill"] = now

        if bucket["tokens"] >= 1:
            bucket["tokens"] -= 1
            return True
        return False

    def _cleanup_old_buckets(self):
        """Limpia buckets inactivos para evitar memory leak."""
        now = time.time()
        stale_keys = [
            k for k, v in self.buckets.items()
            if now - v["last_refill"] > 300  # 5 minutos sin actividad
        ]
        for k in stale_keys:
            del self.buckets[k]

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        method = request.method

        # No limitar whitelist
        if any(path == wl for wl in self.whitelist):
            return await call_next(request)

        # No limitar OPTIONS (CORS preflight)
        if method == "OPTIONS":
            return await call_next(request)

        # Obtener límite y verificar
        max_rpm = self._get_limit_for_request(path, method)
        client_key = self._get_client_key(request, path)

        if not self._check_rate_limit(client_key, max_rpm):
            logger.warning(
                f"Global rate limit exceeded: {request.client.host} -> {method} {path}"
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "detail": "Demasiadas solicitudes. Por favor, espere un momento.",
                    "limit": f"{max_rpm}/minute",
                },
                headers={"Retry-After": "60"},
            )

        # Cleanup periódico (cada ~100 requests)
        if len(self.buckets) > 500:
            self._cleanup_old_buckets()

        response = await call_next(request)

        # Añadir headers informativos de rate limit
        response.headers["X-RateLimit-Limit"] = str(max_rpm)
        response.headers["X-RateLimit-Remaining"] = str(
            int(self.buckets[client_key]["tokens"])
        )

        return response
