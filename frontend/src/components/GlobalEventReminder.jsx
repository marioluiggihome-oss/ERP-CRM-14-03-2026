/*
 * © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
import React, { useEffect, useRef, useState } from 'react';
import { Clock, X, User, CalendarClock, MapPin, AlignLeft, CalendarDays } from 'lucide-react';
import { crmCalendarAPI } from '../services/api';
import { format, parseISO } from 'date-fns';
import { es } from 'date-fns/locale';

/**
 * Aviso GLOBAL de eventos próximos. Se monta una sola vez (en App), así que el
 * pop-up aparece en CUALQUIER pantalla. Al pulsar "Ver" abre el DETALLE del
 * evento (aquí mismo, sin tener que ir al calendario). La notificación del
 * navegador, al pulsarla, también abre ese detalle.
 *
 * Props:
 *  - currentUser
 *  - onOpenCalendar: () => void  (navegar al CRM/Calendario, opcional)
 */
const GlobalEventReminder = ({ currentUser, onOpenCalendar }) => {
  const [reminder, setReminder] = useState(null); // toast
  const [detail, setDetail] = useState(null);     // modal con el evento abierto
  const notified = useRef(new Set());
  const eventsRef = useRef([]);

  useEffect(() => {
    if (!currentUser?.id) return;
    let cancelled = false;

    if (typeof Notification !== 'undefined' && Notification.permission === 'default') {
      try { Notification.requestPermission(); } catch { /* noop */ }
    }

    const fetchEvents = async () => {
      try {
        const now = new Date();
        const start = format(now, "yyyy-MM-dd'T'00:00:00");
        const end = format(new Date(now.getTime() + 2 * 24 * 3600 * 1000), "yyyy-MM-dd'T'23:59:59");
        const data = await crmCalendarAPI.getEvents({ userId: currentUser.id, startDate: start, endDate: end });
        if (!cancelled) eventsRef.current = Array.isArray(data) ? data : [];
      } catch { /* noop */ }
    };

    const check = () => {
      const now = new Date();
      for (const evt of eventsRef.current) {
        if (!evt?.startDate || evt.completed || notified.current.has(evt.id)) continue;
        let s;
        try { s = parseISO(evt.startDate); } catch { continue; }
        const diff = (s.getTime() - now.getTime()) / 60000;
        const remind = Number(evt.reminderMinutes ?? evt.reminder ?? 15);
        if (diff <= remind && diff >= -2) {
          notified.current.add(evt.id);
          setReminder(evt);
          try {
            if (typeof Notification !== 'undefined' && Notification.permission === 'granted') {
              const n = new Notification(`Recordatorio: ${evt.title}`, {
                body: format(s, "EEEE d 'a las' HH:mm", { locale: es }),
              });
              n.onclick = () => { try { window.focus(); } catch { /* noop */ } setDetail(evt); setReminder(null); };
            }
          } catch { /* noop */ }
          break;
        }
      }
    };

    fetchEvents();
    check();
    const fId = setInterval(fetchEvents, 5 * 60 * 1000);
    const cId = setInterval(check, 30 * 1000);
    return () => { cancelled = true; clearInterval(fId); clearInterval(cId); };
  }, [currentUser?.id]);

  const fmtWhen = (e) => {
    try { return format(parseISO(e.startDate), "EEEE d 'de' MMMM, HH:mm", { locale: es }); } catch { return ''; }
  };

  return (
    <>
      {/* Toast de aviso */}
      {reminder && (
        <div className="fixed bottom-4 right-4 z-[9999] w-80 bg-white rounded-2xl shadow-2xl border border-indigo-200 p-4">
          <div className="flex items-start gap-3">
            <div className="p-2 bg-indigo-100 rounded-xl shrink-0"><CalendarClock size={18} className="text-indigo-600" /></div>
            <div className="flex-1 min-w-0">
              <p className="text-[10px] font-black text-indigo-500 uppercase">Recordatorio de evento</p>
              <p className="font-bold text-slate-800 truncate">{reminder.title}</p>
              <p className="text-xs text-slate-500 flex items-center gap-1"><Clock size={11} /> {fmtWhen(reminder)}</p>
            </div>
            <button onClick={() => setReminder(null)} className="text-slate-300 hover:text-slate-600 shrink-0"><X size={16} /></button>
          </div>
          <div className="flex gap-2 mt-3">
            <button
              onClick={() => { setDetail(reminder); setReminder(null); }}
              className="flex-1 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-bold"
            >
              Ver evento
            </button>
            <button onClick={() => setReminder(null)} className="flex-1 py-2 bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-lg text-xs font-bold">
              Cerrar
            </button>
          </div>
        </div>
      )}

      {/* Detalle del evento (se abre al pulsar "Ver") */}
      {detail && (
        <div className="fixed inset-0 z-[10000] flex items-center justify-center bg-black/40 p-4" onClick={() => setDetail(null)}>
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden" onClick={(e) => e.stopPropagation()}>
            <div className="px-5 py-4 text-white flex items-start justify-between gap-2"
              style={{ background: detail.color || '#4f46e5' }}>
              <div className="min-w-0">
                <p className="text-[10px] font-black uppercase opacity-80">Evento</p>
                <h3 className="text-lg font-black leading-tight truncate">{detail.title}</h3>
              </div>
              <button onClick={() => setDetail(null)} className="shrink-0 hover:bg-white/20 rounded-lg p-1"><X size={18} /></button>
            </div>
            <div className="p-5 space-y-3">
              <p className="flex items-center gap-2 text-sm text-slate-700"><Clock size={15} className="text-slate-400" /> {fmtWhen(detail)}</p>
              {detail.contactName && <p className="flex items-center gap-2 text-sm text-slate-700"><User size={15} className="text-slate-400" /> {detail.contactName}</p>}
              {detail.location && <p className="flex items-center gap-2 text-sm text-slate-700"><MapPin size={15} className="text-slate-400" /> {detail.location}</p>}
              {detail.description && <p className="flex items-start gap-2 text-sm text-slate-600"><AlignLeft size={15} className="text-slate-400 mt-0.5 shrink-0" /> {detail.description}</p>}
              <div className="flex gap-2 pt-1">
                <button
                  onClick={() => { const e = detail; setDetail(null); onOpenCalendar?.(e); }}
                  className="flex-1 inline-flex items-center justify-center gap-1.5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-bold"
                >
                  <CalendarDays size={15} /> Ir al calendario
                </button>
                <button onClick={() => setDetail(null)} className="px-4 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-xl text-sm font-bold">
                  Cerrar
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default GlobalEventReminder;
