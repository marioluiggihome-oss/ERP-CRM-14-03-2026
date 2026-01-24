import React, { useState, useEffect } from 'react';
import { Wrench, Power, PowerOff, Shield, Clock, Download, AlertTriangle, CheckCircle, Loader, RefreshCw, Database } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const MaintenancePanel = ({ currentUser, onClose }) => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activating, setActivating] = useState(false);
  const [deactivating, setDeactivating] = useState(false);
  const [backups, setBackups] = useState([]);
  const [loadingBackups, setLoadingBackups] = useState(false);
  
  // Form state
  const [message, setMessage] = useState('Sistema en actualización. Volvemos pronto.');
  const [estimatedMinutes, setEstimatedMinutes] = useState(30);
  const [createBackup, setCreateBackup] = useState(true);

  // Load status
  const loadStatus = async () => {
    try {
      const response = await fetch(`${API_URL}/api/maintenance/status`);
      const data = await response.json();
      setStatus(data);
    } catch (err) {
      console.error('Error loading status:', err);
    } finally {
      setLoading(false);
    }
  };

  // Load backups
  const loadBackups = async () => {
    setLoadingBackups(true);
    try {
      const response = await fetch(`${API_URL}/api/maintenance/backups`);
      const data = await response.json();
      setBackups(data.backups || []);
    } catch (err) {
      console.error('Error loading backups:', err);
    } finally {
      setLoadingBackups(false);
    }
  };

  useEffect(() => {
    loadStatus();
    loadBackups();
  }, []);

  // Activate maintenance
  const handleActivate = async () => {
    if (!window.confirm('¿Activar modo mantenimiento? Los usuarios no podrán acceder al sistema.')) {
      return;
    }

    setActivating(true);
    try {
      const response = await fetch(`${API_URL}/api/maintenance/activate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          estimatedMinutes,
          adminUserId: currentUser.id,
          createBackup
        })
      });

      const data = await response.json();
      
      if (data.success) {
        alert('✅ Modo mantenimiento activado' + (createBackup ? '\n📦 Backup de seguridad creado' : ''));
        loadStatus();
        loadBackups();
      } else {
        alert('Error: ' + (data.detail || 'No se pudo activar'));
      }
    } catch (err) {
      console.error('Error activating:', err);
      alert('Error al activar modo mantenimiento');
    } finally {
      setActivating(false);
    }
  };

  // Deactivate maintenance
  const handleDeactivate = async () => {
    if (!window.confirm('¿Desactivar modo mantenimiento? El sistema volverá a estar operativo.')) {
      return;
    }

    setDeactivating(true);
    try {
      const response = await fetch(`${API_URL}/api/maintenance/deactivate?adminUserId=${currentUser.id}`, {
        method: 'POST'
      });

      const data = await response.json();
      
      if (data.success) {
        alert('✅ Sistema operativo. Modo mantenimiento desactivado.');
        loadStatus();
      } else {
        alert('Error: ' + (data.detail || 'No se pudo desactivar'));
      }
    } catch (err) {
      console.error('Error deactivating:', err);
      alert('Error al desactivar modo mantenimiento');
    } finally {
      setDeactivating(false);
    }
  };

  // Download backup
  const handleDownloadBackup = async (backupId) => {
    try {
      const response = await fetch(`${API_URL}/api/maintenance/backups/${backupId}/download`);
      const data = await response.json();
      
      if (data.success) {
        const blob = new Blob([JSON.stringify(data.backup, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${backupId}.json`;
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch (err) {
      console.error('Error downloading backup:', err);
      alert('Error al descargar backup');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader size={32} className="animate-spin text-indigo-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Current Status */}
      <div className={`rounded-2xl p-6 ${status?.active ? 'bg-orange-50 border-2 border-orange-200' : 'bg-green-50 border-2 border-green-200'}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            {status?.active ? (
              <div className="w-12 h-12 bg-orange-500 rounded-xl flex items-center justify-center">
                <Wrench size={24} className="text-white" />
              </div>
            ) : (
              <div className="w-12 h-12 bg-green-500 rounded-xl flex items-center justify-center">
                <CheckCircle size={24} className="text-white" />
              </div>
            )}
            <div>
              <h3 className="font-black text-lg text-gray-900">
                {status?.active ? 'MODO MANTENIMIENTO ACTIVO' : 'SISTEMA OPERATIVO'}
              </h3>
              <p className="text-sm text-gray-600">
                {status?.active 
                  ? `Activado por ${status.activatedBy} el ${new Date(status.activatedAt).toLocaleString('es-ES')}`
                  : 'El sistema está funcionando con normalidad'
                }
              </p>
            </div>
          </div>
          
          {status?.active && (
            <button
              onClick={handleDeactivate}
              disabled={deactivating}
              className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-xl font-bold text-sm uppercase tracking-wider flex items-center gap-2 disabled:opacity-50"
            >
              {deactivating ? <Loader size={18} className="animate-spin" /> : <Power size={18} />}
              Reactivar Sistema
            </button>
          )}
        </div>
        
        {status?.active && status?.preUpdateBackupId && (
          <div className="mt-4 p-3 bg-white/50 rounded-lg flex items-center gap-2 text-sm">
            <Shield size={16} className="text-green-600" />
            <span className="text-gray-700">Backup de seguridad: <strong>{status.preUpdateBackupId}</strong></span>
          </div>
        )}
      </div>

      {/* Activate Form - Only show when NOT in maintenance */}
      {!status?.active && (
        <div className="bg-white rounded-2xl border border-indigo-100 p-6">
          <h3 className="font-black text-lg text-indigo-950 mb-4 flex items-center gap-2">
            <PowerOff size={20} />
            Activar Modo Mantenimiento
          </h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-indigo-400 uppercase tracking-wider mb-1">
                Mensaje para usuarios
              </label>
              <input
                type="text"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                className="w-full border border-indigo-200 rounded-lg px-4 py-2 text-sm focus:border-orange-500 outline-none"
                placeholder="Sistema en actualización..."
              />
            </div>
            
            <div>
              <label className="block text-xs font-bold text-indigo-400 uppercase tracking-wider mb-1">
                Tiempo estimado (minutos)
              </label>
              <input
                type="number"
                value={estimatedMinutes}
                onChange={(e) => setEstimatedMinutes(parseInt(e.target.value) || 30)}
                min="5"
                max="480"
                className="w-32 border border-indigo-200 rounded-lg px-4 py-2 text-sm focus:border-orange-500 outline-none"
              />
            </div>
            
            <label className="flex items-center gap-3 cursor-pointer p-3 bg-indigo-50 rounded-lg">
              <input
                type="checkbox"
                checked={createBackup}
                onChange={(e) => setCreateBackup(e.target.checked)}
                className="w-5 h-5 rounded"
              />
              <div>
                <p className="font-bold text-indigo-900">Crear backup automático</p>
                <p className="text-xs text-indigo-400">Se guardará una copia de seguridad antes de la actualización</p>
              </div>
            </label>
            
            <div className="pt-4 border-t border-indigo-100">
              <button
                onClick={handleActivate}
                disabled={activating}
                className="bg-orange-600 hover:bg-orange-700 text-white px-6 py-3 rounded-xl font-bold text-sm uppercase tracking-wider flex items-center gap-2 disabled:opacity-50"
              >
                {activating ? <Loader size={18} className="animate-spin" /> : <AlertTriangle size={18} />}
                {activating ? 'Activando...' : 'Activar Mantenimiento'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Backup History */}
      <div className="bg-white rounded-2xl border border-indigo-100 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-black text-lg text-indigo-950 flex items-center gap-2">
            <Database size={20} />
            Backups Pre-Actualización
          </h3>
          <button
            onClick={loadBackups}
            disabled={loadingBackups}
            className="p-2 text-indigo-400 hover:text-indigo-600 transition-colors"
          >
            <RefreshCw size={18} className={loadingBackups ? 'animate-spin' : ''} />
          </button>
        </div>
        
        {backups.length === 0 ? (
          <p className="text-center text-indigo-400 py-6">No hay backups pre-actualización</p>
        ) : (
          <div className="space-y-2">
            {backups.map((backup) => (
              <div key={backup.id} className="flex items-center justify-between p-3 bg-indigo-50 rounded-lg">
                <div>
                  <p className="font-bold text-indigo-900 text-sm">{backup.id}</p>
                  <p className="text-xs text-indigo-400">
                    {new Date(backup.createdAt).toLocaleString('es-ES')} · Por: {backup.createdBy}
                  </p>
                </div>
                <button
                  onClick={() => handleDownloadBackup(backup.id)}
                  className="p-2 text-indigo-600 hover:bg-indigo-100 rounded-lg transition-colors"
                  title="Descargar backup"
                >
                  <Download size={18} />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default MaintenancePanel;
