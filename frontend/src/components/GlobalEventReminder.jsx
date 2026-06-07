import React, { useEffect, useRef, useState } from 'react';
import { Clock, X, User, CalendarClock } from 'lucide-react';
import { crmCalendarAPI } from '../services/api';
import { format, parseISO } from 'date-fns';
import { es } from 'date-fns/locale';

/**
 * Aviso GLOBAL de eventos próximos. Se monta una sola vez (en App), así que el
 * pop-up aparece en CUALQUIER pantalla del programa. Sondea los eventos del
 * usuario cada pocos minutos y, cuando uno está a punto de empezar (según su
 * recordatorio), muestra un toast. Al pulsar "Ver" navega al CRM/Calendario.
 *
 * Props:
 *  - currentUser: usuario actual (para traer SUS eventos)
 *  - onOpenCalendar: () => void  → navega al CRM/calendario
 */
const GlobalEventReminder = ({ currentUser, onOpenCalendar }) => {
  const [reminder, setReminder] = useState(null);
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
              new Notification(`Recordatorio: ${evt.title}`, {
                body: format(s, "EEEE d 'a las' HH:mm", { locale: es }),
              });
            }
          } catch { /* noop */ }
          break;
        }
      }
    };

    fetchEvents();
    check();
    const fId = setInterval(fetchEvents, 5 * 60 * 1000); // recargar eventos cada 5 min
    const cId = setInterval(check, 30 * 1000);            // comprobar cada 30 s
    return () => { cancelled = true; clearInterval(fId); clearInterval(cId); };
  }, [currentUser?.id]);

  if (!reminder) return null;

  let when = '';
  try { when = format(parseISO(reminder.startDate), "EEEE d 'a las' HH:mm", { locale: es }); } catch { /* noop */ }

  return (
    <div className="fixed bottom-4 right-4 z-[9999] w-80 bg-white rounded-2xl shadow-2xl border border-indigo-200 p-4 animate-in">
      <div className="flex items-start gap-3">
        <div className="p-2 bg-indigo-100 rounded-xl shrink-0"><CalendarClock size={18} className="text-indigo-600" /></div>
        <div className="flex-1 min-w-0">
          <p className="text-[10px] font-black text-indigo-500 uppercase">Recordatorio de evento</p>
          <p className="font-bold text-slate-800 truncate">{reminder.title}</p>
          <p className="text-xs text-slate-500 flex items-center gap-1"><Clock size={11} /> {when}</p>
          {reminder.contactName && <p className="text-xs text-slate-400 flex items-center gap-1 mt-0.5"><User size={11} />{reminder.contactName}</p>}
        </div>
        <button onClick={() => setReminder(null)} className="text-slate-300 hover:text-slate-600 shrink-0"><X size={16} /></button>
      </div>
      <div className="flex gap-2 mt-3">
        <button
          onClick={() => { onOpenCalendar?.(); setReminder(null); }}
          className="flex-1 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-bold"
        >
          Ver en calendario
        </button>
        <button onClick={() => setReminder(null)} className="flex-1 py-2 bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-lg text-xs font-bold">
          Cerrar
        </button>
      </div>
    </div>
  );
};

export default GlobalEventReminder;
