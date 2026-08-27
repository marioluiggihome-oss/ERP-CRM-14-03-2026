/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
import React from 'react';
import { Database, RefreshCw, HardDrive, Download, Loader, AlertTriangle, Clock } from 'lucide-react';

/**
 * BackupsTab - Pestaña de gestión de copias de seguridad
 */
const BackupsTab = ({
  backups,
  loadingBackups,
  loadBackups,
  creatingBackup,
  createManualBackup,
  isExportingDB,
  handleExportDatabase
}) => {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gradient-to-br from-orange-500 to-red-500 rounded-xl">
            <Database size={20} className="text-white" />
          </div>
          <div>
            <h3 className="text-lg font-black text-indigo-950 uppercase">Copias de Seguridad</h3>
            <p className="text-xs text-indigo-400">Gestión de backups del sistema</p>
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={loadBackups}
            disabled={loadingBackups}
            className="flex items-center gap-2 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold uppercase transition-colors"
          >
            <RefreshCw size={14} className={loadingBackups ? 'animate-spin' : ''} />
            Actualizar
          </button>
          <button
            onClick={createManualBackup}
            disabled={creatingBackup}
            className="flex items-center gap-2 px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-xl text-xs font-bold uppercase transition-colors"
            data-testid="create-backup-btn"
          >
            {creatingBackup ? <Loader size={14} className="animate-spin" /> : <HardDrive size={14} />}
            Crear Backup Manual
          </button>
          <button
            onClick={handleExportDatabase}
            disabled={isExportingDB}
            className="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold uppercase transition-colors"
            data-testid="export-database-btn"
          >
            {isExportingDB ? <Loader size={14} className="animate-spin" /> : <Download size={14} />}
            Exportar a Excel
          </button>
        </div>
      </div>

      {/* Info Box */}
      <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
        <div className="flex items-start gap-3">
          <AlertTriangle size={18} className="text-amber-600 shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-bold text-amber-800">Sistema de Backups Automáticos</p>
            <p className="text-xs text-amber-700 mt-1">
              Los backups automáticos se crean diariamente a las 03:00. También se crean automáticamente antes de activar el modo mantenimiento.
            </p>
          </div>
        </div>
      </div>

      {/* Backups Table */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="px-4 py-3 text-left text-[10px] font-black text-slate-500 uppercase tracking-wider">Fecha</th>
              <th className="px-4 py-3 text-left text-[10px] font-black text-slate-500 uppercase tracking-wider">Tipo</th>
              <th className="px-4 py-3 text-left text-[10px] font-black text-slate-500 uppercase tracking-wider">Creado Por</th>
              <th className="px-4 py-3 text-left text-[10px] font-black text-slate-500 uppercase tracking-wider">Archivo</th>
              <th className="px-4 py-3 text-center text-[10px] font-black text-slate-500 uppercase tracking-wider">Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {loadingBackups ? (
              <tr>
                <td colSpan={5} className="p-8 text-center">
                  <Loader size={24} className="animate-spin mx-auto text-indigo-500" />
                </td>
              </tr>
            ) : backups.length === 0 ? (
              <tr>
                <td colSpan={5} className="p-8 text-center text-slate-400">
                  <Database size={40} className="mx-auto mb-3 opacity-50" />
                  <p className="font-medium">No hay backups registrados</p>
                </td>
              </tr>
            ) : (
              backups.slice(0, 20).map(backup => (
                <tr key={backup.id} className="hover:bg-slate-50">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <Clock size={14} className="text-slate-400" />
                      <span className="text-sm font-medium text-slate-900">
                        {new Date(backup.createdAt).toLocaleString('es-ES')}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded-lg text-xs font-bold ${
                      backup.type === 'manual' ? 'bg-blue-100 text-blue-700' :
                      backup.type === 'auto' ? 'bg-green-100 text-green-700' :
                      'bg-orange-100 text-orange-700'
                    }`}>
                      {backup.type === 'manual' ? 'MANUAL' : 
                       backup.type === 'auto' ? 'AUTOMÁTICO' : 'PRE-UPDATE'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-slate-600">{backup.createdBy || 'Sistema'}</td>
                  <td className="px-4 py-3">
                    <span className="text-xs font-mono text-slate-500 truncate block max-w-[200px]">
                      {backup.path?.split('/').pop() || backup.id}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    <button
                      onClick={() => {
                        if (window.confirm('¿Restaurar este backup? Se sobrescribirán los datos actuales.')) {
                          alert('Función de restauración pendiente de implementar');
                        }
                      }}
                      className="p-1.5 text-slate-400 hover:text-orange-600 hover:bg-orange-50 rounded-lg transition-colors"
                      title="Restaurar"
                    >
                      <RefreshCw size={14} />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {backups.length > 20 && (
        <p className="text-xs text-slate-400 text-center">
          Mostrando los últimos 20 backups de {backups.length} totales
        </p>
      )}
    </div>
  );
};

export default BackupsTab;
