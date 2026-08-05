# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
Google Calendar - API Router (OAuth2 por usuario)
==================================================
Endpoints para que CADA usuario conecte su propia cuenta de Google Calendar
y sincronice eventos en ambos sentidos. Aislamiento estricto: todas las
operaciones usan el `userId` del token JWT del usuario autenticado; nadie
puede ver ni la conexión ni los eventos de otro usuario.

Rutas (bajo /api):
- GET  /api/google-calendar/status        → ¿configurado? ¿conectado? email
- GET  /api/google-calendar/connect        → URL de consentimiento de Google
- GET  /api/google-calendar/callback       → callback OAuth (redirige al front)
- POST /api/google-calendar/disconnect     → revoca y elimina la conexión
- GET  /api/google-calendar/events         → eventos del usuario (rango)
- POST /api/google-calendar/events         → crea evento (push ERP→Google)
- PUT  /api/google-calendar/events/{id}    → actualiza evento
- DELETE /api/google-calendar/events/{id}  → elimina evento
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from services.jwt_service import require_auth
from services import google_calendar_service as gcal

logger = logging.getLogger("google_calendar.router")

google_calendar_router = APIRouter(prefix="/google-calendar", tags=["Google Calendar"])


def _uid(user: dict) -> str:
    """ID del usuario autenticado (clave de aislamiento)."""
    return user.get("sub") or user.get("id")


class GEventBody(BaseModel):
    title: str = Field(..., description="Título del evento")
    startDate: str = Field(..., description="Inicio (YYYY-MM-DD o YYYY-MM-DDTHH:MM[:SS])")
    endDate: Optional[str] = Field(None, description="Fin; por defecto igual al inicio")
    description: str = ""
    location: str = ""
    allDay: bool = False
    # Vínculo opcional con un evento del ERP, para sincronizar y evitar duplicados.
    module: Optional[str] = Field(None, description="Módulo ERP de origen (crm, montajes, ...)")
    erpId: Optional[str] = Field(None, description="ID del evento en el ERP")


@google_calendar_router.get("/status")
async def status(user=Depends(require_auth)):
    """Estado de la integración para el usuario actual."""
    configured = gcal.is_configured()
    connected = False
    email = ""
    if configured:
        conn = await gcal.get_connection(_uid(user))
        if conn:
            connected = True
            email = conn.get("email", "")
    return {"configured": configured, "connected": connected, "email": email}


@google_calendar_router.get("/connect")
async def connect(request: Request, return_path: str = "/", user=Depends(require_auth)):
    """Devuelve la URL de consentimiento de Google para conectar la cuenta."""
    if not gcal.is_configured():
        raise HTTPException(status_code=503, detail="La integración con Google Calendar no está configurada.")
    redirect_uri = gcal.compute_redirect_uri(str(request.base_url))
    url = gcal.build_auth_url(_uid(user), return_path, redirect_uri)
    return {"url": url}


@google_calendar_router.get("/callback")
async def callback(request: Request, code: Optional[str] = None,
                   state: Optional[str] = None, error: Optional[str] = None):
    """
    Callback de Google. No usa cabecera de auth (es una redirección del
    navegador desde Google); el usuario se identifica por el `state` firmado.
    """
    payload = gcal.verify_state(state or "")
    return_path = (payload or {}).get("rp", "/")
    base = str(request.base_url)

    if error or not code or not payload:
        return RedirectResponse(gcal.frontend_redirect(base, return_path, "error"))

    user_id = payload.get("sub")
    redirect_uri = gcal.compute_redirect_uri(base)
    try:
        tokens = await gcal.exchange_code(code, redirect_uri)
        await gcal.save_connection_from_tokens(user_id, tokens)
        return RedirectResponse(gcal.frontend_redirect(base, return_path, "connected"))
    except Exception as e:
        logger.error(f"Error en callback de Google Calendar: {e}")
        return RedirectResponse(gcal.frontend_redirect(base, return_path, "error"))


@google_calendar_router.post("/disconnect")
async def disconnect(user=Depends(require_auth)):
    """Desconecta la cuenta de Google del usuario actual."""
    await gcal.disconnect(_uid(user))
    return {"success": True, "connected": False}


@google_calendar_router.get("/events")
async def list_events(start: Optional[str] = None, end: Optional[str] = None, user=Depends(require_auth)):
    """Lista los eventos de Google del usuario actual en el rango indicado."""
    try:
        events = await gcal.list_events(_uid(user), start, end)
        return {"success": True, "events": events}
    except gcal.NotConnectedError:
        return {"success": False, "connected": False, "events": []}
    except gcal.ReauthRequiredError:
        return {"success": False, "connected": False, "reauth": True, "events": []}
    except Exception as e:
        logger.error(f"Error listando eventos de Google: {e}")
        raise HTTPException(status_code=502, detail="No se pudieron obtener los eventos de Google.")


@google_calendar_router.post("/events")
async def create_event(body: GEventBody, user=Depends(require_auth)):
    """Crea un evento en el Google Calendar del usuario (push ERP→Google)."""
    uid = _uid(user)
    try:
        # Si el evento del ERP ya está vinculado, actualizamos en vez de duplicar.
        existing_gid = None
        if body.module and body.erpId:
            existing_gid = await gcal.get_link(uid, body.module, body.erpId)

        payload = body.model_dump()
        if existing_gid:
            result = await gcal.update_event(uid, existing_gid, payload)
        else:
            result = await gcal.create_event(uid, payload)
            if body.module and body.erpId:
                await gcal.set_link(uid, body.module, body.erpId, result["googleEventId"])
        return {"success": True, "event": result}
    except gcal.NotConnectedError:
        raise HTTPException(status_code=409, detail="No has conectado tu cuenta de Google Calendar.")
    except gcal.ReauthRequiredError:
        raise HTTPException(status_code=401, detail="Vuelve a conectar tu cuenta de Google Calendar.")
    except Exception as e:
        logger.error(f"Error creando evento en Google: {e}")
        raise HTTPException(status_code=502, detail="No se pudo guardar el evento en Google Calendar.")


@google_calendar_router.put("/events/{google_event_id}")
async def update_event(google_event_id: str, body: GEventBody, user=Depends(require_auth)):
    try:
        result = await gcal.update_event(_uid(user), google_event_id, body.model_dump())
        return {"success": True, "event": result}
    except gcal.NotConnectedError:
        raise HTTPException(status_code=409, detail="No has conectado tu cuenta de Google Calendar.")
    except gcal.ReauthRequiredError:
        raise HTTPException(status_code=401, detail="Vuelve a conectar tu cuenta de Google Calendar.")
    except Exception as e:
        logger.error(f"Error actualizando evento en Google: {e}")
        raise HTTPException(status_code=502, detail="No se pudo actualizar el evento en Google Calendar.")


@google_calendar_router.delete("/events/{google_event_id}")
async def delete_event(google_event_id: str, module: Optional[str] = None,
                       erpId: Optional[str] = None, user=Depends(require_auth)):
    uid = _uid(user)
    try:
        await gcal.delete_event(uid, google_event_id)
        if module and erpId:
            await gcal.remove_link(uid, module, erpId)
        return {"success": True}
    except gcal.NotConnectedError:
        raise HTTPException(status_code=409, detail="No has conectado tu cuenta de Google Calendar.")
    except gcal.ReauthRequiredError:
        raise HTTPException(status_code=401, detail="Vuelve a conectar tu cuenta de Google Calendar.")
    except Exception as e:
        logger.error(f"Error eliminando evento en Google: {e}")
        raise HTTPException(status_code=502, detail="No se pudo eliminar el evento en Google Calendar.")
