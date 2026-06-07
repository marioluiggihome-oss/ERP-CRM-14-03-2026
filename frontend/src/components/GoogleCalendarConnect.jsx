import React, { useEffect, useState, useCallback } from 'react';
import { Unlink, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import { googleCalendarAPI } from '../services/api';

/**
 * Logo oficial multicolor de Google (la "G").
 */
const GoogleG = ({ size = 18 }) => (
  <svg width={size} height={size} viewBox="0 0 48 48" aria-hidden="true" className="shrink-0">
    <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
    <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
    <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
    <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
  </svg>
);

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
        <div className="flex items-center gap-1.5">
          {/* Pastilla "conectado" estilo Google */}
          <span
            className="inline-flex items-center gap-2 bg-white border border-slate-200 shadow-sm px-3 py-1.5 rounded-full"
            title={status.email ? `Conectado como ${status.email}` : 'Google Calendar conectado'}
          >
            <GoogleG size={16} />
            <span className="text-xs font-semibold text-slate-700">
              {compact ? 'Conectado' : (status.email || 'Google Calendar')}
            </span>
            <span className="w-2 h-2 rounded-full bg-green-500" />
          </span>
          <button
            onClick={handleDisconnect}
            disabled={busy}
            className="inline-flex items-center justify-center text-slate-400 hover:text-red-600 p-1.5 rounded-full hover:bg-red-50 transition-colors disabled:opacity-50"
            title="Desconectar Google Calendar"
          >
            {busy ? <Loader2 size={15} className="animate-spin" /> : <Unlink size={15} />}
          </button>
        </div>
      ) : (
        // Botón "Conectar" estilo oficial de Google (fondo blanco + logo a color)
        <button
          onClick={handleConnect}
          disabled={busy}
          className="inline-flex items-center gap-2.5 bg-white border border-slate-300 hover:bg-slate-50 active:bg-slate-100 text-slate-700 font-semibold rounded-full shadow-sm hover:shadow transition-all disabled:opacity-50 px-4 py-2"
          title="Conectar tu Google Calendar"
        >
          {busy ? <Loader2 size={18} className="animate-spin text-slate-500" /> : <GoogleG size={18} />}
          <span className="text-sm whitespace-nowrap">
            {compact ? 'Conectar Google' : 'Conectar Google Calendar'}
          </span>
        </button>
      )}
    </div>
  );
};

export default GoogleCalendarConnect;
