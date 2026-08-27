/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
import React, { useState, useEffect } from 'react';
import { Wrench, Clock, RefreshCw, Shield, AlertTriangle } from 'lucide-react';
import Logo from './Logo';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const MaintenanceScreen = ({ onCheckAgain }) => {
  const [status, setStatus] = useState(null);
  const [checking, setChecking] = useState(false);
  const [countdown, setCountdown] = useState(null);

  const checkStatus = async () => {
    setChecking(true);
    try {
      const response = await fetch(`${API_URL}/api/maintenance/status`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      setStatus(data);
      
      // If not in maintenance, reload the page
      if (!data.active) {
        window.location.reload();
      }
      
      // Calculate countdown
      if (data.estimatedEndTime) {
        const end = new Date(data.estimatedEndTime);
        const now = new Date();
        const diff = Math.max(0, Math.floor((end - now) / 1000 / 60));
        setCountdown(diff);
      }
    } catch (err) {
      console.error('Error checking status:', err);
    } finally {
      setChecking(false);
    }
  };

  useEffect(() => {
    checkStatus();
    
    // Check every 30 seconds
    const interval = setInterval(checkStatus, 30000);
    
    // Update countdown every minute
    const countdownInterval = setInterval(() => {
      setCountdown(prev => prev ? Math.max(0, prev - 1) : null);
    }, 60000);
    
    return () => {
      clearInterval(interval);
      clearInterval(countdownInterval);
    };
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-950 via-indigo-900 to-indigo-950 flex items-center justify-center p-8">
      <div className="max-w-lg w-full">
        {/* Logo */}
        <div className="flex justify-center mb-8">
          <div className="bg-white/10 backdrop-blur-xl rounded-3xl p-6">
            <Logo className="h-16 w-auto" />
          </div>
        </div>

        {/* Main Card */}
        <div className="bg-white/10 backdrop-blur-xl rounded-3xl p-8 text-center border border-white/10">
          {/* Icon */}
          <div className="w-20 h-20 bg-orange-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
            <Wrench size={40} className="text-orange-400 animate-pulse" />
          </div>

          {/* Title */}
          <h1 className="text-3xl font-black text-white uppercase tracking-tight mb-2">
            Sistema en Actualización
          </h1>

          {/* Message */}
          <p className="text-indigo-200 text-lg mb-6">
            {status?.message || 'Estamos mejorando el sistema para ti. Volvemos pronto.'}
          </p>

          {/* Info Box */}
          <div className="bg-indigo-950/50 rounded-2xl p-6 mb-6 space-y-4">
            {status?.activatedBy && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-indigo-300 flex items-center gap-2">
                  <Shield size={16} />
                  Iniciado por:
                </span>
                <span className="text-white font-bold">{status.activatedBy}</span>
              </div>
            )}
            
            {status?.activatedAt && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-indigo-300 flex items-center gap-2">
                  <Clock size={16} />
                  Inicio:
                </span>
                <span className="text-white font-bold">
                  {new Date(status.activatedAt).toLocaleString('es-ES')}
                </span>
              </div>
            )}
            
            {countdown !== null && countdown > 0 && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-indigo-300 flex items-center gap-2">
                  <RefreshCw size={16} />
                  Tiempo estimado:
                </span>
                <span className="text-orange-400 font-black text-lg">
                  ~{countdown} min
                </span>
              </div>
            )}
          </div>

          {/* Backup Notice */}
          {status?.preUpdateBackupId && (
            <div className="bg-green-500/20 border border-green-500/30 rounded-xl p-4 mb-6">
              <div className="flex items-center justify-center gap-2 text-green-300 text-sm">
                <Shield size={16} />
                <span>Backup de seguridad realizado antes de la actualización</span>
              </div>
            </div>
          )}

          {/* Refresh Button */}
          <button
            onClick={checkStatus}
            disabled={checking}
            className="bg-white/10 hover:bg-white/20 text-white px-6 py-3 rounded-xl font-bold uppercase tracking-wider text-sm transition-all flex items-center gap-2 mx-auto disabled:opacity-50"
          >
            <RefreshCw size={18} className={checking ? 'animate-spin' : ''} />
            {checking ? 'Comprobando...' : 'Comprobar Estado'}
          </button>

          <p className="text-indigo-400 text-xs mt-4">
            La página se actualizará automáticamente cuando el sistema esté disponible
          </p>
        </div>

        {/* Footer */}
        <p className="text-center text-indigo-400/50 text-xs mt-8">
          Sistema ERP/CRM
        </p>
      </div>
    </div>
  );
};

export default MaintenanceScreen;
