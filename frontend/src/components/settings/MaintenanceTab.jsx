/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
import React from 'react';
import { Wrench, CheckCircle, Power, Loader, Shield, AlertTriangle, Database, RefreshCw, Download } from 'lucide-react';

/**
 * MaintenanceTab - Pestaña de modo mantenimiento
 */
const MaintenanceTab = ({
  maintenanceStatus,
  maintenanceLoading,
  maintenanceMessage,
  setMaintenanceMessage,
  maintenanceMinutes,
  setMaintenanceMinutes,
  maintenanceCreateBackup,
  setMaintenanceCreateBackup,
  maintenanceActivating,
  maintenanceDeactivating,
  handleActivateMaintenance,
  handleDeactivateMaintenance,
  maintenanceBackups,
  loadMaintenanceBackups,
  handleDownloadMaintenanceBackup
}) => {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-gradient-to-br from-red-500 to-orange-500 rounded-xl">
          <Wrench size={20} className="text-white" />
        </div>
        <div>
          <h3 className="text-lg font-black text-indigo-950 uppercase">Modo Mantenimiento</h3>
          <p className="text-xs text-slate-400">Gestiona el acceso al sistema durante actualizaciones</p>
        </div>
      </div>

      {maintenanceLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader size={32} className="animate-spin text-indigo-600" />
        </div>
      ) : (
        <>
          {/* Current Status */}
          <div className={`rounded-2xl p-6 ${maintenanceStatus?.active ? 'bg-orange-50 border-2 border-orange-200' : 'bg-green-50 border-2 border-green-200'}`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                {maintenanceStatus?.active ? (
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
                    {maintenanceStatus?.active ? 'MODO MANTENIMIENTO ACTIVO' : 'SISTEMA OPERATIVO'}
                  </h3>
                  <p className="text-sm text-gray-600">
                    {maintenanceStatus?.active 
                      ? `Activado por ${maintenanceStatus.activatedBy} el ${new Date(maintenanceStatus.activatedAt).toLocaleString('es-ES')}`
                      : 'El sistema está funcionando con normalidad'
                    }
                  </p>
                </div>
              </div>
              
              {maintenanceStatus?.active && (
                <button
                  onClick={handleDeactivateMaintenance}
                  disabled={maintenanceDeactivating}
                  className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-xl font-bold text-sm uppercase tracking-wider flex items-center gap-2 disabled:opacity-50"
                >
                  {maintenanceDeactivating ? <Loader size={18} className="animate-spin" /> : <Power size={18} />}
                  Reactivar Sistema
                </button>
              )}
            </div>
            
            {maintenanceStatus?.active && maintenanceStatus?.preUpdateBackupId && (
              <div className="mt-4 p-3 bg-white/50 rounded-lg flex items-center gap-2 text-sm">
                <Shield size={16} className="text-green-600" />
                <span className="text-gray-700">Backup de seguridad: <strong>{maintenanceStatus.preUpdateBackupId}</strong></span>
              </div>
            )}
          </div>

          {/* Activate Form - Only show when NOT in maintenance */}
          {!maintenanceStatus?.active && (
            <div className="bg-white rounded-2xl border border-indigo-100 p-6">
              <h3 className="font-black text-lg text-indigo-950 mb-4 flex items-center gap-2">
                <AlertTriangle size={20} className="text-orange-500" />
                Activar Modo Mantenimiento
              </h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-indigo-400 uppercase tracking-wider mb-1">
                    Mensaje para usuarios
                  </label>
                  <input
                    type="text"
                    value={maintenanceMessage}
                    onChange={(e) => setMaintenanceMessage(e.target.value)}
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
                    value={maintenanceMinutes}
                    onChange={(e) => setMaintenanceMinutes(parseInt(e.target.value) || 30)}
                    min="5"
                    max="480"
                    className="w-32 border border-indigo-200 rounded-lg px-4 py-2 text-sm focus:border-orange-500 outline-none"
                  />
                </div>
                
                <label className="flex items-center gap-3 cursor-pointer p-3 bg-indigo-50 rounded-lg">
                  <input
                    type="checkbox"
                    checked={maintenanceCreateBackup}
                    onChange={(e) => setMaintenanceCreateBackup(e.target.checked)}
                    className="w-5 h-5 rounded"
                  />
                  <div>
                    <p className="font-bold text-indigo-900">Crear backup automático</p>
                    <p className="text-xs text-indigo-400">Se guardará una copia de seguridad antes de la actualización</p>
                  </div>
                </label>
                
                <div className="pt-4 border-t border-indigo-100">
                  <button
                    onClick={handleActivateMaintenance}
                    disabled={maintenanceActivating}
                    className="bg-orange-600 hover:bg-orange-700 text-white px-6 py-3 rounded-xl font-bold text-sm uppercase tracking-wider flex items-center gap-2 disabled:opacity-50"
                  >
                    {maintenanceActivating ? <Loader size={18} className="animate-spin" /> : <AlertTriangle size={18} />}
                    {maintenanceActivating ? 'Activando...' : 'Activar Mantenimiento'}
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
                onClick={loadMaintenanceBackups}
                className="p-2 text-indigo-400 hover:text-indigo-600 transition-colors"
              >
                <RefreshCw size={18} />
              </button>
            </div>
            
            {maintenanceBackups.length === 0 ? (
              <p className="text-center text-indigo-400 py-6">No hay backups pre-actualización</p>
            ) : (
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {maintenanceBackups.map((backup) => (
                  <div key={backup.id} className="flex items-center justify-between p-3 bg-indigo-50 rounded-lg">
                    <div>
                      <p className="font-bold text-indigo-900 text-sm">{backup.id}</p>
                      <p className="text-xs text-indigo-400">
                        {new Date(backup.createdAt).toLocaleString('es-ES')} · Por: {backup.createdBy}
                      </p>
                    </div>
                    <button
                      onClick={() => handleDownloadMaintenanceBackup(backup.id)}
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
        </>
      )}
    </div>
  );
};

export default MaintenanceTab;
