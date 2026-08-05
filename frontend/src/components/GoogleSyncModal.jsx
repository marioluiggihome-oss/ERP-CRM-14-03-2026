/*
 * © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
import React, { useMemo, useState } from 'react';
import { Calendar, X, Loader2, Check } from 'lucide-react';
import { googleCalendarAPI } from '../services/api';

/**
 * Modal que pregunta al usuario si quiere guardar TAMBIÉN en su Google Calendar
 * el evento/tarea que acaba de crear en el ERP.
 *
 * Si el usuario tiene permiso en varios calendarios (CRM, agenda de montajes,
 * etc.), se le ofrece elegir el contexto, que se usa como etiqueta del evento
 * en Google para poder distinguirlos.
 *
 * Props:
 *  - event: { title, startDate, endDate, description, location, allDay, erpId } | null
 *            (si es null, no se muestra nada)
 *  - defaultContext: clave del contexto que disparó el guardado ('crm'|'montajes'|'prescriptor')
 *  - currentUser: para deducir a qué calendarios tiene acceso
 *  - onClose: () => void   (se llama al cerrar, tanto si sincroniza como si no)
 */
const ALL_CONTEXTS = [
  { key: 'crm', label: 'CRM' },
  { key: 'montajes', label: 'Agenda de montajes' },
  { key: 'prescriptor', label: 'Agenda de prescriptor' },
];

const GoogleSyncModal = ({ event, defaultContext = 'crm', currentUser, onClose }) => {
  const contexts = useMemo(() => {
    const u = currentUser || {};
    const out = [];
    if (u.canAccessCRM && !u.isTienda) out.push(ALL_CONTEXTS[0]);
    if (u.isFabrica || u.isDirectorFabrica) out.push(ALL_CONTEXTS[1]);
    if (u.isPrescriptor) out.push(ALL_CONTEXTS[2]);
    // Si por permisos no sale ninguno, permitimos al menos el contexto de origen.
    if (out.length === 0) {
      const fallback = ALL_CONTEXTS.find(c => c.key === defaultContext) || ALL_CONTEXTS[0];
      out.push(fallback);
    }
    return out;
  }, [currentUser, defaultContext]);

  const [selected, setSelected] = useState(
    contexts.find(c => c.key === defaultContext)?.key || contexts[0].key
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  if (!event) return null;

  const multi = contexts.length > 1;
  const contextLabel = contexts.find(c => c.key === selected)?.label || '';

  const handleConfirm = async () => {
    setSaving(true);
    setError(null);
    try {
      await googleCalendarAPI.createEvent({
        title: multi && contextLabel ? `[${contextLabel}] ${event.title}` : event.title,
        startDate: event.startDate,
        endDate: event.endDate || event.startDate,
        description: event.description || '',
        location: event.location || '',
        allDay: !!event.allDay,
        module: selected,
        erpId: event.erpId,
      });
      onClose?.();
    } catch (e) {
      setError(e.message || 'No se pudo guardar en Google Calendar');
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[10000] flex items-center justify-center bg-black/40 p-4" onClick={() => !saving && onClose?.()}>
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-50 rounded-xl">
              <Calendar size={20} className="text-blue-600" />
            </div>
            <div>
              <h3 className="font-bold text-slate-900">Guardar en Google Calendar</h3>
              <p className="text-xs text-slate-500">¿Quieres añadir también este evento a tu Google Calendar?</p>
            </div>
          </div>
          <button onClick={() => !saving && onClose?.()} className="text-slate-400 hover:text-slate-600">
            <X size={20} />
          </button>
        </div>

        <div className="bg-slate-50 rounded-xl px-4 py-3 mb-4">
          <p className="font-semibold text-slate-800 text-sm truncate">{event.title}</p>
          <p className="text-xs text-slate-500 mt-0.5">
            {event.allDay ? 'Todo el día' : (event.startDate || '')}
          </p>
        </div>

        {multi && (
          <div className="mb-4">
            <label className="block text-xs font-semibold text-slate-600 mb-1.5">¿En qué calendario lo registras?</label>
            <select
              value={selected}
              onChange={(e) => setSelected(e.target.value)}
              className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              {contexts.map(c => (
                <option key={c.key} value={c.key}>{c.label}</option>
              ))}
            </select>
            <p className="text-[11px] text-slate-400 mt-1">Se añade como etiqueta para distinguirlo en Google.</p>
          </div>
        )}

        {error && <p className="text-xs text-red-600 mb-3">{error}</p>}

        <div className="flex gap-2">
          <button
            onClick={() => !saving && onClose?.()}
            disabled={saving}
            className="flex-1 px-4 py-2.5 rounded-xl text-sm font-medium text-slate-600 bg-slate-100 hover:bg-slate-200 transition-colors disabled:opacity-50"
          >
            No, solo en el ERP
          </button>
          <button
            onClick={handleConfirm}
            disabled={saving}
            className="flex-1 inline-flex items-center justify-center gap-1.5 px-4 py-2.5 rounded-xl text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 transition-colors disabled:opacity-50"
          >
            {saving ? <Loader2 size={16} className="animate-spin" /> : <Check size={16} />}
            Sí, también en Google
          </button>
        </div>
      </div>
    </div>
  );
};

export default GoogleSyncModal;
