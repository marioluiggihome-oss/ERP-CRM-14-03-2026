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
