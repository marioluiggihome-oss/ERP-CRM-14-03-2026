# © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
# Software propietario y confidencial. Ver LICENSE.
# Prohibida su copia, distribución, modificación o uso sin autorización
# escrita del titular.
"""
Servicio de integración con Google Calendar (OAuth2 por usuario)
================================================================
Cada usuario conecta SU PROPIA cuenta de Google. Los tokens y los eventos
quedan estrictamente aislados por `userId`: ningún usuario puede ver ni la
conexión ni los eventos de otro. Todas las operaciones reciben el `user_id`
del usuario autenticado y filtran SIEMPRE por ese campo.

Implementación 100% REST vía httpx (asíncrona), sin librerías cliente de
Google, para no bloquear el event loop ni añadir dependencias.
"""

import os
import time
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from urllib.parse import urlencode

import httpx
import jwt  # PyJWT (mismo paquete que usa jwt_service)

from config import JWT_SECRET, JWT_ALGORITHM
from services.db_client import get_db as _get_db_gcal
db = _get_db_gcal()

logger = logging.getLogger("google_calendar")

# ─── Endpoints de Google ──────────────────────────────────────────────────────
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_REVOKE_URL = "https://oauth2.googleapis.com/revoke"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
GOOGLE_CALENDAR_API = "https://www.googleapis.com/calendar/v3"

# Permisos: leer/escribir eventos del propio calendario + email para mostrar
# con qué cuenta se ha conectado.
SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
]

DEFAULT_TIMEZONE = os.environ.get("GOOGLE_CALENDAR_TIMEZONE", "Europe/Madrid")

# ─── Colecciones (aisladas por usuario) ────────────────────────────────────────
# google_calendar_connections: { userId, email, refresh_token, access_token,
#                                expiry(epoch), scope, connectedAt }
# google_calendar_links: { userId, module, erpId, googleEventId } — mapa para
#                         sincronizar ERP↔Google y evitar duplicados.
CONNECTIONS = db.google_calendar_connections
LINKS = db.google_calendar_links

# ─── Configuración OAuth (desde entorno) ───────────────────────────────────────
CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", "")
# Debe coincidir EXACTAMENTE con el registrado en Google Cloud Console.
REDIRECT_URI_ENV = os.environ.get("GOOGLE_OAUTH_REDIRECT_URI", "")
# URL del frontend para redirigir tras el callback (si no se fija, se usa el
# host de la propia petición).
FRONTEND_URL = os.environ.get("FRONTEND_URL", "").rstrip("/")


class NotConfiguredError(Exception):
    """La integración no tiene credenciales OAuth configuradas."""


class NotConnectedError(Exception):
    """El usuario no ha conectado su cuenta de Google."""


class ReauthRequiredError(Exception):
    """El refresh token ya no es válido; el usuario debe reconectar."""


def is_configured() -> bool:
    return bool(CLIENT_ID and CLIENT_SECRET)


def compute_redirect_uri(request_base_url: str) -> str:
    """Redirect URI usado en el flujo OAuth (env tiene prioridad)."""
    if REDIRECT_URI_ENV:
        return REDIRECT_URI_ENV
    base = (request_base_url or "").rstrip("/")
    return f"{base}/api/google-calendar/callback"


def frontend_redirect(request_base_url: str, return_path: str, status: str) -> str:
    """URL absoluta a la que devolver el navegador tras el callback."""
    base = FRONTEND_URL or (request_base_url or "").rstrip("/")
    path = return_path if (return_path or "").startswith("/") else "/"
    sep = "&" if "?" in path else "?"
    return f"{base}{path}{sep}gcal={status}"


# ─── State firmado (CSRF + vínculo con el usuario) ─────────────────────────────

def make_state(user_id: str, return_path: str) -> str:
    """Firma un state corto que ata el consentimiento al usuario concreto."""
    payload = {
        "sub": user_id,
        "rp": return_path or "/",
        "type": "gcal_state",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_state(state: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(state, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "gcal_state":
            return None
        return payload
    except Exception:
        return None


def build_auth_url(user_id: str, return_path: str, redirect_uri: str) -> str:
    """Construye la URL de consentimiento de Google."""
    if not is_configured():
        raise NotConfiguredError()
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",       # para obtener refresh_token
        "prompt": "consent",            # fuerza refresh_token en cada conexión
        "include_granted_scopes": "true",
        "state": make_state(user_id, return_path),
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


# ─── Intercambio / refresco de tokens ──────────────────────────────────────────

async def exchange_code(code: str, redirect_uri: str) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(GOOGLE_TOKEN_URL, data={
            "code": code,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        })
    resp.raise_for_status()
    return resp.json()


async def _refresh_token(refresh_token: str) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(GOOGLE_TOKEN_URL, data={
            "refresh_token": refresh_token,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "refresh_token",
        })
    if resp.status_code in (400, 401):
        # invalid_grant → el usuario revocó el acceso o el token caducó.
        raise ReauthRequiredError()
    resp.raise_for_status()
    return resp.json()


async def _get_userinfo_email(access_token: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
        if resp.status_code == 200:
            return resp.json().get("email", "")
    except Exception as e:
        logger.warning(f"No se pudo obtener el email de Google: {e}")
    return ""


# ─── Conexiones (por usuario) ──────────────────────────────────────────────────

async def get_connection(user_id: str) -> Optional[Dict[str, Any]]:
    return await CONNECTIONS.find_one({"userId": user_id}, {"_id": 0})

async def is_connected(user_id: str) -> bool:
    return await CONNECTIONS.count_documents({"userId": user_id}, limit=1) > 0


async def save_connection_from_tokens(user_id: str, tokens: Dict[str, Any]) -> Dict[str, Any]:
    """Guarda/actualiza la conexión del usuario a partir del token de Google."""
    access_token = tokens.get("access_token", "")
    refresh_token = tokens.get("refresh_token")  # puede no venir en re-consentimientos
    expires_in = int(tokens.get("expires_in", 3600))
    expiry = time.time() + expires_in
    email = await _get_userinfo_email(access_token)

    doc: Dict[str, Any] = {
        "userId": user_id,
        "access_token": access_token,
        "expiry": expiry,
        "scope": tokens.get("scope", " ".join(SCOPES)),
        "email": email,
        "connectedAt": datetime.now(timezone.utc).isoformat(),
    }
    if refresh_token:
        doc["refresh_token"] = refresh_token

    # upsert preservando el refresh_token previo si Google no lo reenvía.
    await CONNECTIONS.update_one({"userId": user_id}, {"$set": doc}, upsert=True)
    return {"connected": True, "email": email}


async def disconnect(user_id: str) -> None:
    """Revoca el acceso en Google y elimina la conexión y los vínculos del usuario."""
    conn = await CONNECTIONS.find_one({"userId": user_id})
    token = (conn or {}).get("refresh_token") or (conn or {}).get("access_token")
    if token:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                await client.post(GOOGLE_REVOKE_URL, data={"token": token})
        except Exception as e:
            logger.warning(f"No se pudo revocar el token en Google: {e}")
    await CONNECTIONS.delete_one({"userId": user_id})
    await LINKS.delete_many({"userId": user_id})


async def _valid_access_token(user_id: str) -> str:
    """Devuelve un access_token válido para el usuario, refrescándolo si hace falta."""
    conn = await CONNECTIONS.find_one({"userId": user_id})
    if not conn:
        raise NotConnectedError()
    if conn.get("access_token") and (conn.get("expiry", 0) - 60) > time.time():
        return conn["access_token"]

    refresh = conn.get("refresh_token")
    if not refresh:
        raise ReauthRequiredError()
    tokens = await _refresh_token(refresh)
    access_token = tokens.get("access_token", "")
    expiry = time.time() + int(tokens.get("expires_in", 3600))
    await CONNECTIONS.update_one(
        {"userId": user_id},
        {"$set": {"access_token": access_token, "expiry": expiry}},
    )
    return access_token


# ─── Mapa de vínculos ERP ↔ Google (por usuario) ───────────────────────────────

async def get_link(user_id: str, module: str, erp_id: str) -> Optional[str]:
    doc = await LINKS.find_one({"userId": user_id, "module": module, "erpId": erp_id})
    return (doc or {}).get("googleEventId")

async def set_link(user_id: str, module: str, erp_id: str, google_event_id: str) -> None:
    await LINKS.update_one(
        {"userId": user_id, "module": module, "erpId": erp_id},
        {"$set": {"googleEventId": google_event_id}},
        upsert=True,
    )

async def remove_link(user_id: str, module: str, erp_id: str) -> None:
    await LINKS.delete_one({"userId": user_id, "module": module, "erpId": erp_id})


# ─── Normalización de fechas ────────────────────────────────────────────────────

def _to_google_time(value: str, all_day: bool) -> Dict[str, str]:
    """Convierte una fecha ERP ('YYYY-MM-DD' o 'YYYY-MM-DDTHH:MM[:SS]') al formato Google."""
    if all_day:
        return {"date": str(value)[:10]}
    v = str(value)
    if len(v) == 16:        # 'YYYY-MM-DDTHH:MM'
        v = v + ":00"
    return {"dateTime": v, "timeZone": DEFAULT_TIMEZONE}


def _parse_dt(v):
    """Parsea 'YYYY-MM-DD[THH:MM[:SS]]' de forma tolerante (acepta hora vacía/mala)."""
    if not v:
        return None
    s = str(v).strip().replace(" ", "T")
    date_part = s[:10]
    try:
        datetime.fromisoformat(date_part + "T00:00:00")
    except Exception:
        return None
    hh = mm = ss = 0
    if len(s) > 10:
        bits = s[11:].split(":")
        if len(bits) >= 2 and bits[0].strip().isdigit() and bits[1].strip().isdigit():
            hh = int(bits[0]); mm = int(bits[1])
            ss = int(bits[2]) if len(bits) >= 3 and bits[2].strip().isdigit() else 0
    try:
        return datetime.fromisoformat(f"{date_part}T{hh:02d}:{mm:02d}:{ss:02d}")
    except Exception:
        return None


def _google_times(start_val, end_val, all_day):
    """Devuelve (start, end) en formato Google garantizando fin > inicio.

    Google rechaza eventos con hora cuyo fin sea <= inicio (error 400). Si el
    fin falta o es inválido/igual, se usa inicio + 1 hora.
    """
    if all_day:
        s = str(start_val or "")[:10]
        e = (str(end_val)[:10] if end_val else "") or s
        return {"date": s}, {"date": e}
    s_dt = _parse_dt(start_val) or datetime.now()
    e_dt = _parse_dt(end_val)
    if e_dt is None or e_dt <= s_dt:
        e_dt = s_dt + timedelta(hours=1)
    fmt = "%Y-%m-%dT%H:%M:%S"
    return (
        {"dateTime": s_dt.strftime(fmt), "timeZone": DEFAULT_TIMEZONE},
        {"dateTime": e_dt.strftime(fmt), "timeZone": DEFAULT_TIMEZONE},
    )


def _from_google_event(item: Dict[str, Any]) -> Dict[str, Any]:
    """Normaliza un evento de Google al formato que consume el calendario del ERP."""
    start = item.get("start", {}) or {}
    end = item.get("end", {}) or {}
    all_day = "date" in start
    return {
        "id": item.get("id"),
        "googleEventId": item.get("id"),
        "title": item.get("summary", "(sin título)"),
        "description": item.get("description", "") or "",
        "location": item.get("location", "") or "",
        "startDate": start.get("dateTime") or start.get("date"),
        "endDate": end.get("dateTime") or end.get("date"),
        "allDay": all_day,
        "htmlLink": item.get("htmlLink", ""),
        "source": "google",     # marca para distinguirlo de los eventos del ERP
        "color": "#16a34a",     # verde Google, solo lectura en el ERP
        "readOnlyFromGoogle": True,
    }


# ─── CRUD de eventos en el calendario del usuario ──────────────────────────────

async def list_events(user_id: str, time_min: Optional[str], time_max: Optional[str]) -> List[Dict[str, Any]]:
    """Lista los eventos del calendario principal del usuario en un rango."""
    access_token = await _valid_access_token(user_id)
    params = {
        "singleEvents": "true",
        "orderBy": "startTime",
        "maxResults": "250",
    }
    if time_min:
        params["timeMin"] = _ensure_rfc3339(time_min, end=False)
    if time_max:
        params["timeMax"] = _ensure_rfc3339(time_max, end=True)

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{GOOGLE_CALENDAR_API}/calendars/primary/events",
            headers={"Authorization": f"Bearer {access_token}"},
            params=params,
        )
    resp.raise_for_status()
    items = resp.json().get("items", [])
    return [_from_google_event(it) for it in items if it.get("status") != "cancelled"]


async def create_event(user_id: str, event: Dict[str, Any]) -> Dict[str, Any]:
    """Crea un evento en el calendario del usuario. Devuelve el evento normalizado."""
    access_token = await _valid_access_token(user_id)
    all_day = bool(event.get("allDay"))
    start_g, end_g = _google_times(event.get("startDate"), event.get("endDate"), all_day)
    body = {
        "summary": event.get("title", "Evento"),
        "description": event.get("description", "") or "",
        "location": event.get("location", "") or "",
        "start": start_g,
        "end": end_g,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{GOOGLE_CALENDAR_API}/calendars/primary/events",
            headers={"Authorization": f"Bearer {access_token}"},
            json=body,
        )
    if resp.status_code >= 400:
        logger.error(f"Google create_event {resp.status_code}: {resp.text[:300]} | body={body}")
    resp.raise_for_status()
    return _from_google_event(resp.json())


async def update_event(user_id: str, google_event_id: str, event: Dict[str, Any]) -> Dict[str, Any]:
    access_token = await _valid_access_token(user_id)
    all_day = bool(event.get("allDay"))
    start_g, end_g = _google_times(event.get("startDate"), event.get("endDate"), all_day)
    body = {
        "summary": event.get("title", "Evento"),
        "description": event.get("description", "") or "",
        "location": event.get("location", "") or "",
        "start": start_g,
        "end": end_g,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.put(
            f"{GOOGLE_CALENDAR_API}/calendars/primary/events/{google_event_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            json=body,
        )
    if resp.status_code >= 400:
        logger.error(f"Google update_event {resp.status_code}: {resp.text[:300]} | body={body}")
    resp.raise_for_status()
    return _from_google_event(resp.json())


async def delete_event(user_id: str, google_event_id: str) -> None:
    access_token = await _valid_access_token(user_id)
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.delete(
            f"{GOOGLE_CALENDAR_API}/calendars/primary/events/{google_event_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
    # 410 = ya estaba borrado; lo tratamos como éxito idempotente.
    if resp.status_code not in (200, 204, 410):
        resp.raise_for_status()


def _ensure_rfc3339(value: str, end: bool) -> str:
    """Convierte 'YYYY-MM-DD' a un instante RFC3339 con offset para la API de Google."""
    v = str(value)
    if len(v) == 10:  # solo fecha
        v = f"{v}T23:59:59Z" if end else f"{v}T00:00:00Z"
    elif len(v) == 16:
        v = v + ":00"
    # Si no trae zona/offset, añadimos 'Z' (UTC) para que Google lo acepte.
    if "T" in v and not (v.endswith("Z") or "+" in v[11:] or v[11:].count("-") > 0):
        v = v + "Z"
    return v
