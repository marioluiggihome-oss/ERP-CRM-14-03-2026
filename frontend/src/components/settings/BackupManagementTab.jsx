/**
 * BackupManagementTab - Gestión de copias de seguridad
 * Crear, listar y restaurar backups de la base de datos
 */
import React, { useState, useEffect } from 'react';
import { Database, Download, Upload, RefreshCw, Trash2, Clock, HardDrive, Shield, AlertTriangle, CheckCircle } from 'lucide-react';
import { getToken } from '../../services/api';

// Los endpoints de backup requieren sesión de ADMIN: enviar el token JWT.
const authHeader = () => {
  const t = getToken();
  return t ? { Authorization: `Bearer ${t}` } : {};
};

const BackupManagementTab = () => {
  const [backups, setBackups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [restoring, setRestoring] = useState(null);
  const [message, setMessage] = useState(null);

  const fetchBackups = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/backup/list`, { headers: authHeader() });
      if (!response.ok) throw new Error('Error cargando backups');
      const data = await response.json();
      setBackups(data.backups || []);
    } catch (err) {
      setMessage({ type: 'error', text: err.message });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBackups();
  }, []);

  const createBackup = async () => {
    setCreating(true);
    setMessage(null);
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/backup/create`, {
        method: 'POST', headers: authHeader()
      });
      const data = await response.json();
      
      if (data.success) {
        setMessage({ type: 'success', text: `Backup creado: ${data.backup_name} (${data.size_mb} MB)` });
        fetchBackups();
      } else {
        throw new Error(data.detail || data.error || 'Error creando backup');
      }
    } catch (err) {
      setMessage({ type: 'error', text: err.message });
    } finally {
      setCreating(false);
    }
  };

  const restoreBackup = async (backupName) => {
    if (!window.confirm(`⚠️ ATENCIÓN: Restaurar "${backupName}" SOBRESCRIBIRÁ todos los datos actuales.\n\n¿Estás seguro de continuar?`)) {
      return;
    }
    
    setRestoring(backupName);
    setMessage(null);
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/backup/restore/${encodeURIComponent(backupName)}`, {
        method: 'POST', headers: authHeader()
      });
      const data = await response.json();
      
      if (data.success) {
        setMessage({ type: 'success', text: `Backup restaurado exitosamente: ${backupName}` });
      } else {
        throw new Error(data.detail || data.error || 'Error restaurando backup');
      }
    } catch (err) {
      setMessage({ type: 'error', text: err.message });
    } finally {
      setRestoring(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-black text-slate-800 flex items-center gap-2">
            <Database className="w-6 h-6 text-blue-500" />
            Copias de Seguridad
          </h2>
          <p className="text-sm text-slate-500">Gestión de backups de la base de datos</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={fetchBackups}
            disabled={loading}
            className="bg-slate-100 hover:bg-slate-200 text-slate-700 px-4 py-2 rounded-lg font-bold text-sm flex items-center gap-2 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Actualizar
          </button>
          <button
            onClick={createBackup}
            disabled={creating}
            className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg font-bold text-sm flex items-center gap-2 transition-colors disabled:opacity-50"
          >
            {creating ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Creando...
              </>
            ) : (
              <>
                <Download className="w-4 h-4" />
                Crear Backup Ahora
              </>
            )}
          </button>
        </div>
      </div>

      {/* Mensaje de estado */}
      {message && (
        <div className={`flex items-center gap-3 p-4 rounded-xl ${
          message.type === 'success' ? 'bg-emerald-50 border border-emerald-200 text-emerald-700' : 'bg-red-50 border border-red-200 text-red-700'
        }`}>
          {message.type === 'success' ? (
            <CheckCircle className="w-5 h-5 flex-shrink-0" />
          ) : (
            <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          )}
          <p className="font-bold text-sm">{message.text}</p>
          <button onClick={() => setMessage(null)} className="ml-auto text-sm underline">Cerrar</button>
        </div>
      )}

      {/* Info panel */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
        <div className="flex items-start gap-3">
          <Shield className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-bold text-blue-800">Backup Automático Programado</p>
            <p className="text-sm text-blue-600 mt-1">
              Se ejecuta automáticamente todos los días a las <strong>3:00 AM</strong>. 
              Los backups se retienen durante <strong>30 días</strong>.
            </p>
          </div>
        </div>
      </div>

      {/* Lista de backups */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <div className="bg-slate-50 px-4 py-3 border-b border-slate-200">
          <h3 className="font-black text-slate-700 flex items-center gap-2">
            <HardDrive className="w-5 h-5 text-slate-500" />
            Backups Disponibles ({backups.length})
          </h3>
        </div>
        
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <RefreshCw className="w-6 h-6 text-blue-500 animate-spin" />
            <span className="ml-3 text-slate-600 font-bold">Cargando...</span>
          </div>
        ) : backups.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-slate-400">
            <Database className="w-12 h-12 mb-3" />
            <p className="font-bold">No hay backups disponibles</p>
            <p className="text-sm">Crea el primer backup usando el botón de arriba</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {backups.map((backup, idx) => (
              <div key={backup.name} className="flex items-center justify-between px-4 py-3 hover:bg-slate-50 transition-colors">
                <div className="flex items-center gap-4">
                  <div className="bg-blue-100 p-2 rounded-lg">
                    <Database className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <p className="font-black text-slate-800">{backup.name}</p>
                    <div className="flex items-center gap-4 text-xs text-slate-500 mt-1">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {new Date(backup.created).toLocaleString('es-ES')}
                      </span>
                      <span className="flex items-center gap-1">
                        <HardDrive className="w-3 h-3" />
                        {backup.size_mb} MB
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => restoreBackup(backup.name)}
                    disabled={restoring === backup.name}
                    className="bg-amber-100 hover:bg-amber-200 text-amber-700 px-3 py-1.5 rounded-lg font-bold text-xs flex items-center gap-1 transition-colors disabled:opacity-50"
                    title="Restaurar este backup"
                  >
                    {restoring === backup.name ? (
                      <>
                        <RefreshCw className="w-3 h-3 animate-spin" />
                        Restaurando...
                      </>
                    ) : (
                      <>
                        <Upload className="w-3 h-3" />
                        Restaurar
                      </>
                    )}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Advertencia */}
      <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-bold text-amber-800">Precaución al Restaurar</p>
            <p className="text-sm text-amber-600 mt-1">
              Restaurar un backup <strong>sobrescribirá todos los datos actuales</strong>. 
              Se recomienda crear un backup antes de restaurar otro más antiguo.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BackupManagementTab;
