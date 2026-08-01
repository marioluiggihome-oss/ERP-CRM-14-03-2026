"""
Recordatorios de calendario por EMAIL
=====================================
Programador que, cada pocos minutos, revisa los eventos próximos del calendario
y envía un correo al usuario asignado (una sola vez por evento). Funciona aunque
nadie tenga la app abierta (corre en el servidor).

Marca cada evento con `reminderEmailed: True` para no reenviar.
"""

import logging
from datetime import datetime, timedelta

try:
    from zoneinfo import ZoneInfo
    _TZ = ZoneInfo("Europe/Madrid")
except Exception:  # pragma: no cover
    _TZ = None

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from services.db_client import get_db as _get_db_singleton
db = _get_db_singleton()
from services.email_service import send_email

logger = logging.getLogger("calendar_reminders")

_scheduler = AsyncIOScheduler()


def _now_local_naive() -> datetime:
    """Hora actual en zona Europe/Madrid como naive (para comparar con las
    fechas del calendario, que se guardan en hora local sin zona)."""
    if _TZ is not None:
        return datetime.now(_TZ).replace(tzinfo=None)
    return datetime.now()


async def _send(to_email: str, subject: str, html: str) -> bool:
    ok = False
    try:
        ok = await send_email(to_email, subject, html)
    except Exception as e:
        logger.warning(f"send_email (SendGrid) falló: {e}")
    if not ok:
        try:
            from routes.auth_advanced import send_email_with_resend
            ok = await send_email_with_resend(to_email, subject, html)
        except Exception as e:
            logger.warning(f"Resend falló: {e}")
    return ok


def _build_html(evt: dict, start: datetime, name: str = "") -> str:
    fecha = start.strftime("%d/%m/%Y a las %H:%M")
    title = evt.get("title", "Evento")
    desc = evt.get("description", "") or ""
    contact = evt.get("contactName", "") or ""
    location = evt.get("location", "") or ""
    saludo = f"Hola {name}," if name else "Hola,"
    extra = ""
    if contact:
        extra += f"<p style='margin:4px 0;color:#475569'><b>Contacto:</b> {contact}</p>"
    if location:
        extra += f"<p style='margin:4px 0;color:#475569'><b>Lugar:</b> {location}</p>"
    if desc:
        extra += f"<p style='margin:8px 0;color:#475569'>{desc}</p>"
    return f"""
    <div style="font-family:Arial,sans-serif;max-width:520px;margin:0 auto;padding:24px;background:#f8fafc;border-radius:16px">
      <p style="font-size:12px;font-weight:800;color:#6366f1;text-transform:uppercase;letter-spacing:1px;margin:0">Recordatorio de evento</p>
      <h2 style="margin:6px 0 2px;color:#0f172a">{title}</h2>
      <p style="margin:0 0 14px;color:#64748b;font-weight:700">📅 {fecha}</p>
      <p style="margin:0 0 8px;color:#334155">{saludo} tienes este evento próximamente:</p>
      {extra}
      <p style="margin:18px 0 0;font-size:12px;color:#94a3b8">Luiggi Home ERP · erp.luiggihome.es</p>
    </div>
    """


async def check_and_send_reminders():
    """Busca eventos cuyo recordatorio acaba de llegar y avisa por email."""
    try:
        now_local = _now_local_naive()
        cursor = db.calendar_events.find({
            "completed": {"$ne": True},
            "reminderEmailed": {"$ne": True},
            "assignedTo": {"$nin": [None, ""]},
        }, {"_id": 0})
        async for evt in cursor:
            start_raw = evt.get("startDate")
            if not start_raw:
                continue
            try:
                start = datetime.fromisoformat(str(start_raw).replace("Z", "").split("+")[0])
            except Exception:
                continue
            remind = int(evt.get("reminderMinutes") or evt.get("reminder") or 30)
            diff_min = (start - now_local).total_seconds() / 60.0
            # Avisar cuando estamos dentro de la ventana del recordatorio y no muy pasado
            if not (-5 <= diff_min <= remind):
                continue

            uid = evt.get("assignedTo")
            user = await db.users.find_one(
                {"id": uid}, {"_id": 0, "email": 1, "username": 1, "clientName": 1}
            )
            to_email = (user or {}).get("email") or (user or {}).get("username")
            evt_id = evt.get("id")
            if not to_email or "@" not in str(to_email):
                # Sin email válido: marcar para no reintentar indefinidamente
                if evt_id:
                    await db.calendar_events.update_one({"id": evt_id}, {"$set": {"reminderEmailed": True}})
                continue

            name = (user or {}).get("clientName") or ""
            subject = f"Recordatorio: {evt.get('title', 'Evento')}"
            await _send(to_email, subject, _build_html(evt, start, name))
            if evt_id:
                await db.calendar_events.update_one({"id": evt_id}, {"$set": {"reminderEmailed": True}})
            logger.info(f"Recordatorio enviado a {to_email} para evento {evt_id}")
    except Exception as e:
        logger.error(f"check_and_send_reminders error: {e}")


def start_reminder_scheduler():
    """Arranca el programador de recordatorios (cada 2 minutos)."""
    if _scheduler.running:
        return
    _scheduler.add_job(
        check_and_send_reminders,
        IntervalTrigger(minutes=2),
        id="calendar_reminders",
        replace_existing=True,
        max_instances=1,
    )
    _scheduler.start()
    logger.info("✅ Programador de recordatorios de calendario iniciado (cada 2 min)")
