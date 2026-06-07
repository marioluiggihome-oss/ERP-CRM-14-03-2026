"""
LuiggiAI Engine - Core
=======================
Motor central que gestiona la comunicación con la API del proveedor
subyacente, sanitiza respuestas y mantiene la abstracción white-label.
"""

import asyncio
import base64
import httpx
import logging
import re
import time
from typing import Optional, Dict, Any, List, Tuple
from urllib.parse import urlparse

from .config import get_ai_config

logger = logging.getLogger("luiggi_ai.core")

# Ruta pública del proxy de assets (sirve imágenes del proveedor ocultando su
# origen). Debe coincidir con el endpoint registrado en routes/ai_engine.py.
ASSET_PROXY_PATH = "/api/ai-engine/asset"

_URL_RE = re.compile(r'https?://[^\s"\'<>)\]}]+', re.IGNORECASE)
_IMG_EXT_RE = re.compile(r'\.(png|jpe?g|webp|gif|bmp|tiff?)(\?|#|$)', re.IGNORECASE)


class LuiggiAICore:
    """
    Motor central de LuiggiAI.
    Gestiona tareas, sanitiza respuestas y oculta el proveedor.
    """

    def __init__(self):
        self.config = get_ai_config()
        self._client: Optional[httpx.AsyncClient] = None
        self._task_cache: Dict[str, Any] = {}
        # Términos de sanitización ordenados por longitud descendente para que
        # las frases completas ("powered by manus") se reemplacen antes que las
        # palabras sueltas ("manus") y no queden restos.
        self._sanitize_pairs: List[Tuple[str, str]] = sorted(
            self.config.sanitize_replacements.items(),
            key=lambda kv: len(kv[0]),
            reverse=True,
        )

    async def _get_client(self) -> httpx.AsyncClient:
        """Obtiene o crea el cliente HTTP."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.config.provider_base_url,
                headers={
                    "Authorization": f"Bearer {self.config.provider_api_key}",
                    "Content-Type": "application/json",
                    "X-Client": self.config.brand_name,
                },
                timeout=120.0,
            )
        return self._client

    # ─── Sanitización / White-label ───────────────────────────────────────

    def _is_provider_host(self, host: str) -> bool:
        """True si el host pertenece a un dominio del proveedor subyacente."""
        host = (host or "").lower()
        return any(
            host == h or host.endswith("." + h)
            for h in self.config.provider_asset_hosts
        )

    def proxy_url(self, original_url: str) -> str:
        """
        Convierte una URL del proveedor en una URL del proxy interno, de modo
        que el navegador del cliente nunca vea el origen real.
        """
        token = base64.urlsafe_b64encode(original_url.encode("utf-8")).decode("ascii").rstrip("=")
        return f"{ASSET_PROXY_PATH}?u={token}"

    @staticmethod
    def decode_proxy_token(token: str) -> str:
        """Decodifica el token del proxy a la URL original (usado por el router)."""
        pad = "=" * (-len(token) % 4)
        return base64.urlsafe_b64decode((token + pad).encode("ascii")).decode("utf-8")

    def _rewrite_provider_urls(self, text: str) -> str:
        """Reescribe cualquier URL que apunte al proveedor para pasarla por el proxy."""
        if not text or "http" not in text:
            return text

        def _repl(m: "re.Match") -> str:
            url = m.group(0)
            try:
                host = urlparse(url).netloc.split("@")[-1].split(":")[0]
            except Exception:
                return url
            return self.proxy_url(url) if self._is_provider_host(host) else url

        return _URL_RE.sub(_repl, text)

    @staticmethod
    def _smart_case(matched: str, replacement: str) -> str:
        """Adapta la capitalización del reemplazo a la del término encontrado."""
        if matched.isupper():
            return replacement.upper()
        if matched[:1].isupper():
            return replacement[:1].upper() + replacement[1:]
        return replacement

    def _sanitize_response(self, text: str) -> str:
        """
        Sanitiza la respuesta eliminando cualquier referencia al proveedor:
        1) reescribe las URLs del proveedor para servirlas por el proxy interno,
        2) reemplaza nombres/marcas de forma insensible a mayúsculas y dando
           prioridad a las frases más largas.
        """
        if not text:
            return text
        result = self._rewrite_provider_urls(text)
        for term, replacement in self._sanitize_pairs:
            if not term:
                continue
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            result = pattern.sub(lambda m: self._smart_case(m.group(0), replacement), result)
        return result

    def _collect_image_urls(self, data: Any, out: List[str]) -> None:
        """Recorre la estructura y recolecta URLs de imagen del proveedor."""
        if isinstance(data, str):
            for url in _URL_RE.findall(data):
                host = ""
                try:
                    host = urlparse(url).netloc.split(":")[0]
                except Exception:
                    pass
                if _IMG_EXT_RE.search(url) or self._is_provider_host(host):
                    if url not in out:
                        out.append(url)
        elif isinstance(data, dict):
            for v in data.values():
                self._collect_image_urls(v, out)
        elif isinstance(data, list):
            for v in data:
                self._collect_image_urls(v, out)

    def _sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitiza recursivamente un diccionario."""
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = self._sanitize_response(value)
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self._sanitize_dict(item) if isinstance(item, dict)
                    else self._sanitize_response(item) if isinstance(item, str)
                    else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        return sanitized

    async def create_task(
        self,
        prompt: str,
        files: Optional[List[Dict]] = None,
        structured_output_schema: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Crea una tarea en el motor de IA.

        Args:
            prompt: Instrucción para el motor
            files: Lista de archivos adjuntos [{file_id: str}]
            structured_output_schema: Schema JSON para output estructurado

        Returns:
            Dict con task_id y estado
        """
        if not self.config.provider_api_key:
            return {
                "success": False,
                "error": "Motor IA no configurado. Contacte al administrador.",
                "engine": self.config.brand_name,
            }

        try:
            client = await self._get_client()

            payload = {
                "prompt": prompt,
            }

            if files:
                payload["files"] = files
            if structured_output_schema:
                payload["structured_output_schema"] = structured_output_schema

            response = await client.post("/task.create", json=payload)

            if response.status_code == 200:
                data = response.json()
                task_id = data.get("task_id") or data.get("id")
                self._task_cache[task_id] = {
                    "status": "running",
                    "created_at": time.time(),
                }
                return {
                    "success": True,
                    "task_id": task_id,
                    "engine": self.config.brand_name,
                    "version": self.config.brand_version,
                }
            else:
                logger.error(f"Error creating task: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": "Error al procesar la solicitud. Intente de nuevo.",
                    "engine": self.config.brand_name,
                }

        except httpx.TimeoutException:
            return {
                "success": False,
                "error": "Tiempo de espera agotado. La solicitud es muy compleja.",
                "engine": self.config.brand_name,
            }
        except Exception as e:
            logger.error(f"Unexpected error in create_task: {e}")
            return {
                "success": False,
                "error": "Error interno del motor. Contacte soporte.",
                "engine": self.config.brand_name,
            }

    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Consulta el estado de una tarea."""
        try:
            client = await self._get_client()
            response = await client.get(f"/task.get?task_id={task_id}")

            if response.status_code == 200:
                data = response.json()
                # Sanitizar toda la respuesta
                sanitized = self._sanitize_dict(data)
                sanitized["engine"] = self.config.brand_name
                return sanitized
            else:
                return {
                    "success": False,
                    "error": "No se pudo obtener el estado de la tarea.",
                    "engine": self.config.brand_name,
                }
        except Exception as e:
            logger.error(f"Error getting task status: {e}")
            return {
                "success": False,
                "error": "Error al consultar estado.",
                "engine": self.config.brand_name,
            }

    async def get_task_messages(self, task_id: str) -> Dict[str, Any]:
        """Obtiene los mensajes/resultados de una tarea completada."""
        try:
            client = await self._get_client()
            response = await client.get(f"/task.listMessages?task_id={task_id}")

            if response.status_code == 200:
                data = response.json()
                # Extraer URLs de imagen del proveedor ANTES de sanitizar y
                # servirlas por el proxy interno (oculta el origen real).
                raw_images: List[str] = []
                self._collect_image_urls(data, raw_images)
                sanitized = self._sanitize_dict(data)
                sanitized["engine"] = self.config.brand_name
                sanitized["images"] = [self.proxy_url(u) for u in raw_images]
                return {"success": True, **sanitized}
            else:
                return {
                    "success": False,
                    "error": "No se pudieron obtener los resultados.",
                    "engine": self.config.brand_name,
                }
        except Exception as e:
            logger.error(f"Error getting task messages: {e}")
            return {
                "success": False,
                "error": "Error al obtener resultados.",
                "engine": self.config.brand_name,
            }

    async def wait_for_completion(
        self, task_id: str, timeout: int = 300, poll_interval: int = 5
    ) -> Dict[str, Any]:
        """
        Espera a que una tarea se complete (polling).

        Args:
            task_id: ID de la tarea
            timeout: Tiempo máximo de espera en segundos
            poll_interval: Intervalo entre consultas

        Returns:
            Dict con resultado final
        """
        start = time.time()
        while time.time() - start < timeout:
            status = await self.get_task_status(task_id)

            task_status = status.get("status", "unknown")
            if task_status in ("completed", "done", "finished"):
                # Obtener mensajes/resultados
                messages = await self.get_task_messages(task_id)
                return {
                    "success": True,
                    "status": "completed",
                    "result": messages,
                    "engine": self.config.brand_name,
                    "duration_seconds": round(time.time() - start, 1),
                }
            elif task_status in ("failed", "error", "cancelled"):
                return {
                    "success": False,
                    "status": task_status,
                    "error": status.get("error", "La tarea falló."),
                    "engine": self.config.brand_name,
                }

            await asyncio.sleep(poll_interval)

        return {
            "success": False,
            "status": "timeout",
            "error": f"La tarea no se completó en {timeout} segundos.",
            "engine": self.config.brand_name,
        }

    async def upload_file(self, file_data: bytes, filename: str) -> Dict[str, Any]:
        """Sube un archivo al motor para procesamiento."""
        try:
            client = await self._get_client()
            files = {"file": (filename, file_data)}
            response = await client.post("/file.upload", files=files)

            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "file_id": data.get("file_id") or data.get("id"),
                    "engine": self.config.brand_name,
                }
            else:
                return {
                    "success": False,
                    "error": "Error al subir el archivo.",
                    "engine": self.config.brand_name,
                }
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            return {
                "success": False,
                "error": "Error al subir archivo.",
                "engine": self.config.brand_name,
            }

    async def close(self):
        """Cierra el cliente HTTP."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    def get_status(self) -> Dict[str, Any]:
        """Devuelve el estado del motor (health check)."""
        return {
            "engine": self.config.brand_name,
            "version": self.config.brand_version,
            "status": "active" if self.config.provider_api_key else "unconfigured",
            "capabilities": {
                "render_3d": self.config.render_enabled,
                "document_ai": self.config.document_ai_enabled,
                "voice_input": self.config.voice_enabled,
            },
        }


# Singleton
_engine: Optional[LuiggiAICore] = None


def get_engine() -> LuiggiAICore:
    """Obtiene la instancia del motor (singleton)."""
    global _engine
    if _engine is None:
        _engine = LuiggiAICore()
    return _engine
