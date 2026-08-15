/*
 * © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * SecurityTab - Componente de Seguridad 2FA
 * Gestión de autenticación de dos factores
 */
import React from 'react';
import { Shield, XCircle, RefreshCw, AlertTriangle } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const SecurityTab = ({ state, setState }) => {
  const has2FAEnabled = state.currentUser?.has2FAEnabled;

  // ── Sesiones abiertas (solo master) ──────────────────────────────────────
  const u = state.currentUser || {};
  const esMaster = !!(u.isAdmin || u.isPrimaryAdmin || u.isMaster);
  const [sesiones, setSesiones] = React.useState(null);
  const [ultimoCierre, setUltimoCierre] = React.useState(null);
  const [cargando, setCargando] = React.useState(false);

  const cabeceras = () => ({
    'Content-Type': 'application/json',
    Authorization: `Bearer ${state.token}`,
  });

  const cargarSesiones = async () => {
    setCargando(true);
    try {
      const r = await fetch(`${API_URL}/api/auth/sesiones`, { headers: cabeceras() });
      const d = await r.json();
      if (d.success) { setSesiones(d.sesiones || []); setUltimoCierre(d.ultimoCierre || null); }
      else alert(d.detail || 'No se pudieron leer las sesiones.');
    } catch { alert('Error de conexión al leer las sesiones.'); }
    finally { setCargando(false); }
  };

  const cerrarTodas = async () => {
    // Se avisa de lo que de verdad va a pasar: también echa a quien lo pulsa.
    if (!window.confirm(
      'Se va a echar del ERP a TODOS los usuarios, tú incluido.\n\n' +
      'Todo el mundo tendrá que volver a entrar con su contraseña.\n\n¿Seguir?')) return;
    setCargando(true);
    try {
      const r = await fetch(`${API_URL}/api/auth/sesiones/cerrar-todas`, {
        method: 'POST', headers: cabeceras(),
        body: JSON.stringify({ motivo: 'cerrado desde el Panel Maestro' }),
      });
      const d = await r.json();
      if (d.success) { alert(d.mensaje || 'Sesiones cerradas.'); setSesiones([]); }
      else alert(d.detail || 'No se pudieron cerrar las sesiones.');
    } catch { alert('Error de conexión al cerrar las sesiones.'); }
    finally { setCargando(false); }
  };

  const cerrarUno = async (userId, nombre) => {
    if (!userId) return;
    if (!window.confirm(`¿Echar del ERP a ${nombre || userId}? Tendrá que volver a entrar.`)) return;
    setCargando(true);
    try {
      const r = await fetch(`${API_URL}/api/auth/sesiones/cerrar/${encodeURIComponent(userId)}`, {
        method: 'POST', headers: cabeceras(),
      });
      const d = await r.json();
      if (d.success) { alert(d.mensaje || 'Sesión cerrada.'); await cargarSesiones(); }
      else alert(d.detail || 'No se pudo cerrar esa sesión.');
    } catch { alert('Error de conexión.'); }
    finally { setCargando(false); }
  };

  const handleSetup2FA = () => {
    setState(prev => ({ ...prev, show2FASetup: true }));
  };

  const handleDisable2FA = async () => {
    if (!window.confirm('¿Estás seguro de que quieres desactivar la autenticación 2FA? Tu cuenta será menos segura.')) {
      return;
    }

    try {
      const response = await fetch(`${API_URL}/api/auth-advanced/2fa/disable-simple`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${state.token}`
        },
        body: JSON.stringify({ userId: state.currentUser?.id })
      });
      const data = await response.json();
      
      if (data.success) {
        setState(prev => ({ 
          ...prev, 
          currentUser: { ...prev.currentUser, has2FAEnabled: false }
        }));
        alert('2FA desactivado correctamente');
      } else {
        alert(data.detail || 'Error al desactivar 2FA');
      }
    } catch (err) {
      alert('Error de conexión');
    }
  };

  const handleRegenerateBackupCodes = async () => {
    if (!window.confirm('¿Generar nuevos códigos de respaldo? Los códigos anteriores quedarán invalidados.')) {
      return;
    }

    try {
      const response = await fetch(`${API_URL}/api/auth-advanced/2fa/regenerate-backup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${state.token}`
        },
        body: JSON.stringify({ userId: state.currentUser?.id })
      });
      const data = await response.json();
      
      if (data.success && data.backupCodes) {
        alert('Nuevos códigos de respaldo:\n\n' + data.backupCodes.join('\n') + '\n\nGuárdalos en un lugar seguro.');
      } else {
        alert(data.detail || 'Error al regenerar códigos');
      }
    } catch (err) {
      alert('Error de conexión');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <div className="p-4 bg-emerald-100 rounded-2xl">
          <Shield size={32} className="text-emerald-600" />
        </div>
        <div>
          <h3 className="text-2xl font-black text-slate-800 uppercase tracking-wider">Seguridad 2FA</h3>
          <p className="text-slate-500">Gestiona la autenticación de dos factores para tu cuenta</p>
        </div>
      </div>

      {/* SESIONES ABIERTAS (solo master). Hasta ahora «cerrar sesión» solo
          vaciaba una tabla que únicamente se mira AL ENTRAR: el token seguía
          valiendo 24 h, así que quien estaba dentro seguía dentro. */}
      {esMaster && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="bg-gradient-to-r from-rose-700 to-rose-800 text-white px-6 py-4 flex items-center justify-between">
            <h4 className="font-black uppercase tracking-wider">Sesiones abiertas</h4>
            <button onClick={cargarSesiones} disabled={cargando}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/15 hover:bg-white/25 text-xs font-bold">
              <RefreshCw size={14} className={cargando ? 'animate-spin' : ''} /> Actualizar
            </button>
          </div>
          <div className="p-6 space-y-4">
            {ultimoCierre && (
              <p className="text-xs text-slate-500">
                Último cierre general: <b className="text-slate-700">{new Date(ultimoCierre).toLocaleString('es-ES')}</b>
              </p>
            )}
            {sesiones === null ? (
              <p className="text-sm text-slate-400">Pulsa «Actualizar» para ver quién está dentro.</p>
            ) : sesiones.length === 0 ? (
              <p className="text-sm text-slate-500">No hay ninguna sesión registrada.</p>
            ) : (
              <div className="border border-slate-200 rounded-xl divide-y divide-slate-100 max-h-72 overflow-y-auto">
                {sesiones.map((s, i) => (
                  <div key={i} className="flex items-center justify-between px-4 py-2.5 gap-3">
                    <div className="min-w-0">
                      <p className="font-bold text-slate-800 truncate">{s.username || s.user_id}</p>
                      <p className="text-[11px] text-slate-400">
                        Desde {s.login_at ? new Date(s.login_at).toLocaleString('es-ES') : '—'}
                        {s.ip ? ` · ${s.ip}` : ''}
                      </p>
                    </div>
                    <button onClick={() => cerrarUno(s.user_id, s.username)}
                      className="shrink-0 px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-rose-100 text-slate-600 hover:text-rose-700 text-xs font-bold">
                      Echar
                    </button>
                  </div>
                ))}
              </div>
            )}
            <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl">
              <div className="flex items-start gap-3">
                <AlertTriangle size={18} className="text-rose-600 shrink-0 mt-0.5" />
                <div className="min-w-0">
                  <p className="font-bold text-rose-900">Cerrar TODAS las sesiones</p>
                  <p className="text-sm text-rose-700 mb-3">
                    Echa del ERP a todos los usuarios <b>en el acto</b>, tú incluido.
                    Todo el mundo tendrá que volver a entrar. No hace falta reiniciar nada.
                  </p>
                  <button onClick={cerrarTodas} disabled={cargando}
                    className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-700 disabled:opacity-50 text-white font-black text-sm">
                    Cerrar todas las sesiones
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Estado actual del 2FA */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="bg-gradient-to-r from-slate-800 to-slate-900 text-white px-6 py-4">
          <h4 className="font-black uppercase tracking-wider">Estado de 2FA</h4>
        </div>
        <div className="p-6">
          <div className="flex items-center justify-between p-4 bg-slate-50 rounded-xl">
            <div className="flex items-center gap-4">
              <div className={`p-3 rounded-xl ${has2FAEnabled ? 'bg-emerald-100' : 'bg-amber-100'}`}>
                <Shield size={24} className={has2FAEnabled ? 'text-emerald-600' : 'text-amber-600'} />
              </div>
              <div>
                <p className="font-bold text-slate-800">
                  {has2FAEnabled ? 'Autenticación 2FA Activada' : 'Autenticación 2FA Desactivada'}
                </p>
                <p className="text-sm text-slate-500">
                  {has2FAEnabled 
                    ? 'Tu cuenta está protegida con autenticación de dos factores' 
                    : 'Activa 2FA para mayor seguridad en tu cuenta'}
                </p>
              </div>
            </div>
            <div className={`px-4 py-2 rounded-lg font-bold uppercase text-sm ${
              has2FAEnabled 
                ? 'bg-emerald-100 text-emerald-700' 
                : 'bg-amber-100 text-amber-700'
            }`}>
              {has2FAEnabled ? 'Activo' : 'Inactivo'}
            </div>
          </div>
        </div>
      </div>

      {/* Acciones 2FA */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="bg-gradient-to-r from-emerald-600 to-emerald-700 text-white px-6 py-4">
          <h4 className="font-black uppercase tracking-wider">Acciones</h4>
        </div>
        <div className="p-6 space-y-4">
          {!has2FAEnabled ? (
            <div className="bg-emerald-50 rounded-xl p-4 border border-emerald-200">
              <h5 className="font-bold text-emerald-800 mb-2">Activar Autenticación 2FA</h5>
              <p className="text-sm text-emerald-600 mb-4">
                Añade una capa extra de seguridad a tu cuenta. Necesitarás una app autenticadora como Google Authenticator o Authy.
              </p>
              <button
                onClick={handleSetup2FA}
                className="bg-emerald-600 text-white px-6 py-3 rounded-xl font-bold uppercase text-sm hover:bg-emerald-700 transition-colors flex items-center gap-2"
                data-testid="enable-2fa-btn"
              >
                <Shield size={18} />
                Configurar 2FA
              </button>
            </div>
          ) : (
            <>
              <div className="bg-slate-50 rounded-xl p-4 border border-slate-200">
                <h5 className="font-bold text-slate-800 mb-2">Desactivar 2FA</h5>
                <p className="text-sm text-slate-600 mb-4">
                  No recomendado. Si desactivas 2FA, tu cuenta será menos segura.
                </p>
                <button
                  onClick={handleDisable2FA}
                  className="bg-red-100 text-red-700 px-6 py-3 rounded-xl font-bold uppercase text-sm hover:bg-red-200 transition-colors flex items-center gap-2"
                  data-testid="disable-2fa-btn"
                >
                  <XCircle size={18} />
                  Desactivar 2FA
                </button>
              </div>

              <div className="bg-amber-50 rounded-xl p-4 border border-amber-200">
                <h5 className="font-bold text-amber-800 mb-2">Regenerar Códigos de Respaldo</h5>
                <p className="text-sm text-amber-600 mb-4">
                  Genera nuevos códigos de respaldo si has perdido los anteriores o los has usado todos.
                </p>
                <button
                  onClick={handleRegenerateBackupCodes}
                  className="bg-amber-600 text-white px-6 py-3 rounded-xl font-bold uppercase text-sm hover:bg-amber-700 transition-colors flex items-center gap-2"
                  data-testid="regenerate-backup-btn"
                >
                  <RefreshCw size={18} />
                  Regenerar Códigos
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Información adicional */}
      <div className="bg-blue-50 rounded-xl p-6 border border-blue-200">
        <h5 className="font-bold text-blue-800 mb-3 flex items-center gap-2">
          <AlertTriangle size={18} />
          Información Importante
        </h5>
        <ul className="text-sm text-blue-700 space-y-2">
          <li>La autenticación 2FA añade una capa extra de seguridad a tu cuenta.</li>
          <li>Necesitarás tu teléfono cada vez que inicies sesión.</li>
          <li>Guarda los códigos de respaldo en un lugar seguro (no en el móvil).</li>
          <li>Si pierdes acceso a tu autenticador, usa un código de respaldo para entrar.</li>
        </ul>
      </div>
    </div>
  );
};

export default SecurityTab;
