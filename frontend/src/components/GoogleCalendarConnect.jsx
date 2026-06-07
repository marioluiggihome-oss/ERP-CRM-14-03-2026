import React, { useEffect, useState, useCallback } from 'react';
import { Calendar, Link2, Unlink, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import { googleCalendarAPI } from '../services/api';

/**
 * Widget reutilizable para conectar/desconectar Google Calendar.
 * El aislamiento por usuario lo garantiza el backend (cada quien ve solo lo suyo).
 *
 * Props:
 *  - returnPath: ruta del front a la que volver tras el consentimiento (def. ruta actual)
 *  - onStatusChange: callback({ configured, connected, email }) cuando cambia el estado
 *  - compact: estilo reducido para barras de herramientas
 */
const GoogleCalendarConnect = ({ returnPath, onStatusChange, compact = false }) => {
  const [status, setStatus] = useState({ configured: false, connected: false, email: '' });
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [flash, setFlash] = useState(null); // { type: 'ok'|'err', msg }

  const refresh = useCallback(async () => {
    try {
      const s = await googleCalendarAPI.status();
      setStatus(s);
      onStatusChange?.(s);
    } catch {
      setStatus({ configured: false, connected: false, email: '' });
    } finally {
      setLoading(false);
    }
  }, [onStatusChange]);

  useEffect(() => {
    // Detectar el retorno del callback OAuth (?gcal=connected|error) y limpiar la URL.
    try {
      const params = new URLSearchParams(window.location.search);
      const gcal = params.get('gcal');
      if (gcal === 'connected') setFlash({ type: 'ok', msg: 'Google Calendar conectado' });
      else if (gcal === 'error') setFlash({ type: 'err', msg: 'No se pudo conectar con Google' });
      if (gcal) {
        params.delete('gcal');
        const qs = params.toString();
        window.history.replaceState({}, '', window.location.pathname + (qs ? `?${qs}` : ''));
        setTimeout(() => setFlash(null), 4000);
      }
    } catch { /* noop */ }
    refresh();
  }, [refresh]);

  const handleConnect = async () => {
    setBusy(true);
    try {
      const path = returnPath || (window.location.pathname + window.location.search);
      await googleCalendarAPI.connect(path); // redirige a Google
    } catch (e) {
      setFlash({ type: 'err', msg: e.message || 'Error al conectar' });
      setBusy(false);
    }
  };

  const handleDisconnect = async () => {
    if (!window.confirm('¿Desconectar tu Google Calendar de este ERP?')) return;
    setBusy(true);
    try {
      await googleCalendarAPI.disconnect();
      await refresh();
      setFlash({ type: 'ok', msg: 'Google Calendar desconectado' });
      setTimeout(() => setFlash(null), 4000);
    } catch (e) {
      setFlash({ type: 'err', msg: e.message || 'Error al desconectar' });
    } finally {
      setBusy(false);
    }
  };

  // Si la integración no está configurada en el servidor, no mostramos nada.
  if (loading || !status.configured) return null;

  return (
    <div className="flex items-center gap-2">
      {flash && (
        <span className={`hidden md:inline-flex items-center gap-1 text-xs font-medium px-2 py-1 rounded-lg ${
          flash.type === 'ok' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
        }`}>
          {flash.type === 'ok' ? <CheckCircle2 size={14} /> : <AlertCircle size={14} />}
          {flash.msg}
        </span>
      )}

      {status.connected ? (
        <div className="flex items-center gap-2">
          <span
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-green-700 bg-green-50 border border-green-200 px-2.5 py-1.5 rounded-lg"
            title={status.email ? `Conectado como ${status.email}` : 'Google Calendar conectado'}
          >
            <Calendar size={14} />
            {compact ? 'Google' : (status.email || 'Google Calendar')}
          </span>
          <button
            onClick={handleDisconnect}
            disabled={busy}
            className="inline-flex items-center gap-1 text-xs font-medium text-slate-500 hover:text-red-600 px-2 py-1.5 rounded-lg hover:bg-red-50 transition-colors disabled:opacity-50"
            title="Desconectar Google Calendar"
          >
            {busy ? <Loader2 size={14} className="animate-spin" /> : <Unlink size={14} />}
            {!compact && 'Desconectar'}
          </button>
        </div>
      ) : (
        <button
          onClick={handleConnect}
          disabled={busy}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-white bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-700 hover:to-blue-600 px-3 py-1.5 rounded-lg shadow-sm transition-colors disabled:opacity-50"
          title="Conectar tu Google Calendar"
        >
          {busy ? <Loader2 size={14} className="animate-spin" /> : <Link2 size={14} />}
          {compact ? 'Google' : 'Conectar Google Calendar'}
        </button>
      )}
    </div>
  );
};

export default GoogleCalendarConnect;
