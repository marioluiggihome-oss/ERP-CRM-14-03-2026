"""
LuiggiAI Engine - Core
=======================
Motor central que gestiona la comunicación con la API del proveedor
subyacente, sanitiza respuestas y mantiene la abstracción white-label.

API v2: https://api.manus.ai/v2
  - POST /v2/task.create        → {"message": {"content": [{"type":"text","text":"..."}]}}
  - GET  /v2/task.detail        → ?task_id=xxx   (status: running|stopped|waiting|error)
  - GET  /v2/task.listMessages  → ?task_id=xxx   (mensajes y adjuntos del agente)
  - POST /v2/file.upload        → multipart form
Auth: header x-manus-api-key: {key}
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
                base_url="https://api.manus.ai",
                headers={
                    "x-manus-api-key": self.config.provider_api_key,
                    "Content-Type": "application/json",
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
        Crea una tarea en el motor de IA usando la API v2 de Manus.

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

            # Formato correcto API v2: message.content como array de ContentPart
            content = [{"type": "text", "text": prompt}]

            # Adjuntar archivos si los hay (file_id o file_url)
            if files:
                for f in files:
                    if f.get("file_id"):
                        content.append({
                            "type": "file",
                            "file_id": f["file_id"]
                        })
                    elif f.get("file_url"):
                        content.append({
                            "type": "file",
                            "file_url": f["file_url"]
                        })

            payload: Dict[str, Any] = {
                "message": {
                    "content": content,
                },
                "hide_in_task_list": True,  # No aparece en la lista de tareas del usuario
            }

            if structured_output_schema:
                payload["structured_output_schema"] = structured_output_schema

            response = await client.post("/v2/task.create", json=payload)

            if response.status_code == 200:
                data = response.json()
                if not data.get("ok"):
                    err = data.get("error", {})
                    logger.error(f"Manus API error: {err}")
                    return {
                        "success": False,
                        "error": err.get("message", "Error al crear tarea"),
                        "engine": self.config.brand_name,
                    }
                task_id = data.get("task_id")
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
                err_text = response.text
                logger.error(f"Error creating task: {response.status_code} - {err_text}")
                try:
                    err_json = response.json()
                    err_msg = err_json.get("error", {}).get("message", "Error al procesar la solicitud.")
                except Exception:
                    err_msg = "Error al procesar la solicitud. Intente de nuevo."
                return {
                    "success": False,
                    "error": err_msg,
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
        """
        Consulta el estado de una tarea usando task.detail.
        Devuelve status: running | stopped | waiting | error
        """
        try:
            client = await self._get_client()
            response = await client.get(f"/v2/task.detail", params={"task_id": task_id})

            if response.status_code == 200:
                data = response.json()
                if not data.get("ok"):
                    return {
                        "success": False,
                        "error": "No se pudo obtener el estado de la tarea.",
                        "engine": self.config.brand_name,
                    }
                task = data.get("task", {})
                return {
                    "success": True,
                    "status": task.get("status", "unknown"),
                    "task_id": task_id,
                    "engine": self.config.brand_name,
                }
            else:
                return {
                    "success": False,
                    "error": "No se pudo obtener el estado de la tarea.",
                    "status": "error",
                    "engine": self.config.brand_name,
                }
        except Exception as e:
            logger.error(f"Error getting task status: {e}")
            return {
                "success": False,
                "error": "Error al consultar estado.",
                "status": "error",
                "engine": self.config.brand_name,
            }

    async def get_task_messages(self, task_id: str) -> Dict[str, Any]:
        """
        Obtiene los mensajes/resultados de una tarea usando task.listMessages.
        Extrae imágenes de los adjuntos del assistant_message.
        """
        try:
            client = await self._get_client()
            response = await client.get(
                "/v2/task.listMessages",
                params={"task_id": task_id, "order": "asc", "limit": 50}
            )

            if response.status_code == 200:
                data = response.json()
                if not data.get("ok"):
                    return {
                        "success": False,
                        "error": "No se pudieron obtener los resultados.",
                        "engine": self.config.brand_name,
                    }

                messages = data.get("messages", [])

                # Extraer URLs de imagen de los adjuntos del asistente
                raw_images: List[str] = []
                assistant_text = ""

                for msg in messages:
                    msg_type = msg.get("type", "")

                    if msg_type == "assistant_message":
                        am = msg.get("assistant_message", {})
                        if am.get("content"):
                            assistant_text = am["content"]
                        for att in am.get("attachments", []):
                            url = att.get("url", "")
                            ct = att.get("content_type", "")
                            if url and (att.get("type") == "image" or "image" in ct or _IMG_EXT_RE.search(url)):
                                if url not in raw_images:
                                    raw_images.append(url)

                    elif msg_type == "error_message":
                        em = msg.get("error_message", {})
                        logger.warning(f"Task error message: {em}")

                # También buscar imágenes en el texto (URLs inline)
                self._collect_image_urls(assistant_text, raw_images)

                sanitized_text = self._sanitize_response(assistant_text)

                return {
                    "success": True,
                    "content": sanitized_text,
                    "images": [self.proxy_url(u) for u in raw_images],
                    "raw_images": raw_images,
                    "engine": self.config.brand_name,
                }
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
        Espera a que una tarea se complete (polling sobre task.detail).
        Estados terminales: stopped | error
        Estado de progreso: running | waiting

        Args:
            task_id: ID de la tarea
            timeout: Tiempo máximo de espera en segundos
            poll_interval: Intervalo entre consultas

        Returns:
            Dict con resultado final
        """
        start = time.time()
        while time.time() - start < timeout:
            status_resp = await self.get_task_status(task_id)

            task_status = status_resp.get("status", "unknown")

            if task_status == "stopped":
                # Tarea completada — obtener mensajes
                messages = await self.get_task_messages(task_id)
                return {
                    "success": True,
                    "status": "completed",
                    "result": messages,
                    "engine": self.config.brand_name,
                    "duration_seconds": round(time.time() - start, 1),
                }
            elif task_status == "error":
                return {
                    "success": False,
                    "status": "error",
                    "error": status_resp.get("error", "La tarea falló."),
                    "engine": self.config.brand_name,
                }
            elif task_status == "waiting":
                # El agente necesita confirmación — para renders no interactivos
                # esto no debería ocurrir, pero si ocurre esperamos un poco más
                logger.info(f"Task {task_id} is waiting for user input")

            # running o waiting → seguir esperando
            await asyncio.sleep(poll_interval)

        return {
            "success": False,
            "status": "timeout",
            "error": f"La tarea no se completó en {timeout} segundos.",
            "engine": self.config.brand_name,
        }

    async def upload_file(self, file_data: bytes, filename: str) -> Dict[str, Any]:
        """Sube un archivo al motor para procesamiento usando file.upload."""
        try:
            # Para file.upload necesitamos multipart, sin el header Content-Type JSON
            if self._client is None or self._client.is_closed:
                self._client = httpx.AsyncClient(
                    base_url="https://api.manus.ai",
                    headers={"x-manus-api-key": self.config.provider_api_key},
                    timeout=120.0,
                )
            client = self._client

            files = {"file": (filename, file_data, "image/png")}
            response = await client.post("/v2/file.upload", files=files)

            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    return {
                        "success": True,
                        "file_id": data.get("file_id") or data.get("id"),
                        "engine": self.config.brand_name,
                    }
                else:
                    return {
                        "success": False,
                        "error": data.get("error", {}).get("message", "Error al subir el archivo."),
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
    """Obtiene la instancia singleton del motor."""
    global _engine
    if _engine is None:
        _engine = LuiggiAICore()
    return _engine
