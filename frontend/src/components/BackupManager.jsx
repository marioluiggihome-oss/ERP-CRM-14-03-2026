import React, { useState, useEffect, useRef } from 'react';
import { Download, Upload, Mail, Clock, CheckCircle2, AlertCircle, Loader2, HardDrive, RefreshCw, Cloud } from 'lucide-react';
import { backupAPI } from '../services/api';

const BackupManager = () => {
  const [status, setStatus] = useState(null);
  const [history, setHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    loadStatus();
    loadHistory();
  }, []);

  const loadStatus = async () => {
    try {
      const data = await backupAPI.getStatus();
      setStatus(data);
    } catch (err) {
      console.error('Error loading backup status:', err);
    }
  };

  const loadHistory = async () => {
    try {
      const data = await backupAPI.getHistory();
      setHistory(data);
    } catch (err) {
      console.error('Error loading backup history:', err);
    }
  };

  // ── Google Drive ────────────────────────────────────────────────────────
  const [drive, setDrive] = useState(null);
  useEffect(() => { backupAPI.driveEstado().then(setDrive).catch(() => setDrive(null)); }, []);

  const handleSubirDrive = async () => {
    setIsLoading(true); setMessage(null);
    try {
      const r = await backupAPI.driveSubirAhora();
      setMessage({ type: 'success',
        text: `☁️ Copia subida a Google Drive: ${r?.drive?.nombre || r?.filename || ''} (${(r?.size_mb || 0).toFixed?.(1) || r?.size_mb} MB, ${r?.documents || 0} documentos).` });
    } catch (e) {
      setMessage({ type: 'error', text: `❌ ${e?.message || 'No se pudo subir a Drive'}` });
    } finally { setIsLoading(false); }
  };

  // Descarga la copia completa AL INSTANTE (a prueba de disco efímero).
  const handleDescargarAhora = async () => {
    setIsLoading(true); setMessage(null);
    try {
      const r = await backupAPI.descargarAhora();
      setMessage({ type: 'success',
        text: `✅ Copia descargada: ${r.nombre} · ${r.colecciones} colecciones · ${r.documentos} documentos · ${r.tamanoMB} MB. Guárdala fuera del servidor.` });
    } catch (e) {
      setMessage({ type: 'error', text: `❌ No se pudo descargar la copia: ${e?.message || 'error'}` });
    } finally { setIsLoading(false); }
  };

  const handleManualBackup = async () => {
    setIsLoading(true);
    setMessage(null);
    try {
      const result = await backupAPI.triggerManual();
      setMessage({
        type: 'success',
        text: `✅ Backup enviado a ${result.message?.split(' ').pop() || 'tu email'}`
      });
      loadHistory();
    } catch (err) {
      setMessage({
        type: 'error',
        text: '❌ Error al enviar backup'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownloadBackup = async () => {
    setIsLoading(true);
    try {
      const data = await backupAPI.download();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `luiggi_home_backup_${new Date().toISOString().slice(0, 10)}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      setMessage({
        type: 'success',
        text: '✅ Backup descargado correctamente'
      });
    } catch (err) {
      setMessage({
        type: 'error',
        text: '❌ Error al descargar backup'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = async (event) => {
        try {
          const backupData = JSON.parse(event.target.result);
          if (!backupData.data) {
            throw new Error('Formato inválido');
          }
          
          if (window.confirm('⚠️ ¿Estás seguro de restaurar este backup?\n\nEsto reemplazará TODOS los datos actuales con los del backup.')) {
            setIsLoading(true);
            const result = await backupAPI.restore(backupData);
            setMessage({
              type: 'success',
              text: `✅ Backup restaurado: ${Object.values(result.restored || {}).reduce((a, b) => a + b, 0)} registros`
            });
            // Reload the page to refresh all data
            setTimeout(() => window.location.reload(), 2000);
          }
        } catch (err) {
          setMessage({
            type: 'error',
            text: '❌ Error: Archivo de backup inválido'
          });
        } finally {
          setIsLoading(false);
        }
      };
      reader.readAsText(file);
    }
    // Reset input
    e.target.value = '';
  };

  const formatDate = (isoString) => {
    return new Date(isoString).toLocaleString('es-ES', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="h-full bg-gradient-to-br from-slate-50 to-indigo-50/30 overflow-y-auto p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-indigo-950 rounded-2xl mb-4">
            <HardDrive className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-black text-indigo-950 uppercase tracking-wider">Archivo Maestro</h1>
          <p className="text-indigo-400 text-sm mt-2">Copia de seguridad y restauración de datos</p>
        </div>

        {/* Message */}
        {message && (
          <div className={`mb-6 p-4 rounded-xl flex items-center gap-3 ${
            message.type === 'success' 
              ? 'bg-green-50 border border-green-200 text-green-800'
              : 'bg-red-50 border border-red-200 text-red-800'
          }`}>
            {message.type === 'success' ? <CheckCircle2 size={20} /> : <AlertCircle size={20} />}
            <span className="font-bold">{message.text}</span>
          </div>
        )}

        {/* Action Buttons */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {/* Export Backup */}
          <button
            onClick={handleManualBackup}
            disabled={isLoading}
            className="group relative bg-indigo-950 hover:bg-indigo-900 text-white p-8 rounded-2xl transition-all shadow-xl hover:shadow-2xl disabled:opacity-50"
            data-testid="backup-email-btn"
          >
            <div className="flex flex-col items-center gap-4">
              {isLoading ? (
                <Loader2 className="w-12 h-12 animate-spin" />
              ) : (
                <Mail className="w-12 h-12 group-hover:scale-110 transition-transform" />
              )}
              <div className="text-center">
                <h3 className="font-black text-lg uppercase tracking-wider">Exportar Backup</h3>
                <p className="text-indigo-300 text-xs mt-1">Enviar copia de seguridad por email</p>
              </div>
            </div>
            <div className="absolute top-3 right-3 px-2 py-1 bg-orange-500 rounded-lg text-[8px] font-black uppercase">
              Recomendado
            </div>
          </button>

          {/* Descargar copia completa AHORA (no depende del disco del servidor) */}
          <button
            onClick={handleDescargarAhora}
            disabled={isLoading}
            className="group relative bg-emerald-600 hover:bg-emerald-500 text-white p-8 rounded-2xl transition-all disabled:opacity-50"
            data-testid="backup-download-now-btn"
          >
            <div className="flex flex-col items-center gap-4">
              {isLoading ? <Loader2 className="w-12 h-12 animate-spin" />
                         : <HardDrive className="w-12 h-12 group-hover:scale-110 transition-transform" />}
              <div className="text-center">
                <h3 className="font-black text-lg uppercase tracking-wider">Descargar copia completa</h3>
                <p className="text-emerald-100 text-xs mt-1">Toda la base de datos, a tu equipo, al instante</p>
              </div>
            </div>
            <div className="absolute top-3 right-3 px-2 py-1 bg-white text-emerald-700 rounded-lg text-[8px] font-black uppercase">
              A prueba de reinicios
            </div>
          </button>

          {/* Copia automática a Google Drive */}
          <button
            onClick={handleSubirDrive}
            disabled={isLoading || !drive?.configurado}
            title={drive?.configurado ? 'Genera una copia y la sube a tu carpeta de Drive'
                                      : 'Google Drive aún no está configurado'}
            className={`group relative p-8 rounded-2xl transition-all disabled:opacity-60 ${
              drive?.configurado ? 'bg-sky-600 hover:bg-sky-500 text-white'
                                 : 'bg-slate-200 text-slate-500 cursor-not-allowed'}`}
            data-testid="backup-drive-btn"
          >
            <div className="flex flex-col items-center gap-4">
              {isLoading ? <Loader2 className="w-12 h-12 animate-spin" />
                         : <Cloud className="w-12 h-12 group-hover:scale-110 transition-transform" />}
              <div className="text-center">
                <h3 className="font-black text-lg uppercase tracking-wider">Subir a Google Drive</h3>
                <p className={`text-xs mt-1 ${drive?.configurado ? 'text-sky-100' : 'text-slate-500'}`}>
                  {drive?.configurado
                    ? 'Copia diaria automática + subida manual'
                    : 'Sin configurar: falta la cuenta de servicio o la carpeta'}
                </p>
              </div>
            </div>
            {drive?.configurado && (
              <div className="absolute top-3 right-3 px-2 py-1 bg-white text-sky-700 rounded-lg text-[8px] font-black uppercase">
                Activo
              </div>
            )}
          </button>

          {/* Import Backup */}
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={isLoading}
            className="group bg-white hover:bg-indigo-50 border-2 border-dashed border-indigo-200 hover:border-indigo-400 text-indigo-950 p-8 rounded-2xl transition-all disabled:opacity-50"
            data-testid="backup-import-btn"
          >
            <div className="flex flex-col items-center gap-4">
              <Upload className="w-12 h-12 text-indigo-400 group-hover:text-indigo-600 group-hover:scale-110 transition-all" />
              <div className="text-center">
                <h3 className="font-black text-lg uppercase tracking-wider">Importar Backup</h3>
                <p className="text-indigo-400 text-xs mt-1">Restaurar desde archivo JSON</p>
              </div>
            </div>
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".json"
            onChange={handleFileSelect}
            className="hidden"
          />
        </div>

        {/* Download Button */}
        <div className="mb-8">
          <button
            onClick={handleDownloadBackup}
            disabled={isLoading}
            className="w-full bg-white hover:bg-slate-50 border border-indigo-100 text-indigo-950 p-4 rounded-xl transition-all flex items-center justify-center gap-3 disabled:opacity-50"
            data-testid="backup-download-btn"
          >
            <Download size={20} />
            <span className="font-bold">Descargar backup como archivo JSON</span>
          </button>
        </div>

        {/* Status Card */}
        {status && (
          <div className="bg-white rounded-2xl p-6 shadow-lg border border-indigo-50 mb-8">
            <div className="flex items-center gap-3 mb-4">
              <Clock className="text-indigo-600" size={20} />
              <h3 className="font-black text-indigo-950 uppercase tracking-wider">Backups Programados</h3>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {status.next_backups?.map((job, index) => (
                <div key={job.job_id} className="bg-indigo-50/50 rounded-xl p-4 flex items-center gap-4">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                    job.job_id.includes('morning') ? 'bg-yellow-100 text-yellow-600' : 'bg-indigo-100 text-indigo-600'
                  }`}>
                    {job.job_id.includes('morning') ? '🌅' : '🌙'}
                  </div>
                  <div>
                    <p className="font-bold text-indigo-950">
                      {job.job_id.includes('morning') ? 'Backup Mañana' : 'Backup Noche'}
                    </p>
                    <p className="text-xs text-indigo-400">
                      Próximo: {job.next_run ? formatDate(job.next_run) : 'No programado'}
                    </p>
                  </div>
                </div>
              ))}
            </div>
            
            <div className="mt-4 p-3 bg-green-50 rounded-lg flex items-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-xs text-green-700 font-bold">
                Email de destino: {status.backup_email}
              </span>
            </div>
          </div>
        )}

        {/* History */}
        {history.length > 0 && (
          <div className="bg-white rounded-2xl p-6 shadow-lg border border-indigo-50">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <RefreshCw className="text-indigo-600" size={20} />
                <h3 className="font-black text-indigo-950 uppercase tracking-wider">Historial de Backups</h3>
              </div>
              <button 
                onClick={loadHistory}
                className="text-indigo-400 hover:text-indigo-600 p-2"
              >
                <RefreshCw size={16} />
              </button>
            </div>
            
            <div className="space-y-2">
              {history.slice(0, 5).map((item) => (
                <div key={item.id} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs ${
                      item.status === 'success' 
                        ? 'bg-green-100 text-green-600' 
                        : 'bg-red-100 text-red-600'
                    }`}>
                      {item.status === 'success' ? '✓' : '✗'}
                    </div>
                    <div>
                      <p className="font-bold text-sm text-indigo-950">
                        Backup {item.type === 'manual' ? 'Manual' : 'Automático'}
                      </p>
                      <p className="text-xs text-indigo-400">
                        {formatDate(item.timestamp)} • {item.itemCount} registros
                      </p>
                    </div>
                  </div>
                  <span className={`text-xs font-bold px-2 py-1 rounded ${
                    item.status === 'success' 
                      ? 'bg-green-100 text-green-700' 
                      : 'bg-red-100 text-red-700'
                  }`}>
                    {item.status === 'success' ? 'Enviado' : 'Error'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Info Box */}
        <div className="mt-8 p-4 bg-amber-50 border border-amber-200 rounded-xl">
          <div className="flex gap-3">
            <span className="text-xl">💡</span>
            <div>
              <p className="font-bold text-amber-800 text-sm">Información importante</p>
              <ul className="text-xs text-amber-700 mt-2 space-y-1">
                <li>• Los backups automáticos se envían a las 8:00 y 20:00 horas</li>
                <li>• Guarda los archivos recibidos por email en tu Google Drive</li>
                <li>• Para restaurar, usa un archivo .json previamente exportado</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BackupManager;
