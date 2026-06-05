"""
LuiggiAI Engine - Core
=======================
Motor central que gestiona la comunicación con la API del proveedor
subyacente, sanitiza respuestas y mantiene la abstracción white-label.
"""

import asyncio
import httpx
import logging
import time
from typing import Optional, Dict, Any, List

from .config import get_ai_config

logger = logging.getLogger("luiggi_ai.core")


class LuiggiAICore:
    """
    Motor central de LuiggiAI.
    Gestiona tareas, sanitiza respuestas y oculta el proveedor.
    """

    def __init__(self):
        self.config = get_ai_config()
        self._client: Optional[httpx.AsyncClient] = None
        self._task_cache: Dict[str, Any] = {}

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

    def _sanitize_response(self, text: str) -> str:
        """
        Sanitiza la respuesta eliminando cualquier referencia al proveedor.
        """
        if not text:
            return text
        result = text
        for term, replacement in self.config.sanitize_replacements.items():
            result = result.replace(term, replacement)
        return result

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
                sanitized = self._sanitize_dict(data)
                sanitized["engine"] = self.config.brand_name
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
