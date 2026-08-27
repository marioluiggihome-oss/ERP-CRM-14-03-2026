/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * TelemetryTab - Componente de Telemetría IA
 * Sincronización por Reconocimiento Óptico de fichas de catálogo
 */
import React, { useState, useEffect } from 'react';
import { Zap, FileImage, XCircle, Loader, RefreshCw, CheckCircle } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const TelemetryTab = ({ state, setState }) => {
  const [telemetryModule, setTelemetryModule] = useState('montada');
  const [telemetryFiles, setTelemetryFiles] = useState([]);
  const [isProcessingTelemetry, setIsProcessingTelemetry] = useState(false);
  const [telemetryLog, setTelemetryLog] = useState([]);
  const [telemetryProgress, setTelemetryProgress] = useState({ current: 0, total: 0 });
  const [existingCodes, setExistingCodes] = useState(new Set());
  const [telemetryResult, setTelemetryResult] = useState(null);
  
  const [telemetryLibrary, setTelemetryLibrary] = useState(() => {
    const saved = localStorage.getItem('telemetryLibrary');
    return saved === 'MV' ? 'MV' : 'ZC';
  });
  
  const [telemetryTariff, setTelemetryTariff] = useState(() => {
    const saved = localStorage.getItem('telemetryTariff');
    return saved || (telemetryLibrary === 'MV' ? 'T1' : 'Z1');
  });

  const handleLibraryChange = (lib) => {
    setTelemetryLibrary(lib);
    localStorage.setItem('telemetryLibrary', lib);
    const defaultTariff = lib === 'MV' ? 'T1' : 'Z1';
    setTelemetryTariff(defaultTariff);
    localStorage.setItem('telemetryTariff', defaultTariff);
  };

  const handleTariffChange = (tariff) => {
    setTelemetryTariff(tariff);
    localStorage.setItem('telemetryTariff', tariff);
  };

  const handleFileUpload = (e) => {
    const files = Array.from(e.target.files);
    setTelemetryFiles(prev => [
      ...prev, 
      ...files.map(f => ({ 
        id: Math.random().toString(36).slice(2), 
        file: f, 
        name: f.name, 
        preview: URL.createObjectURL(f) 
      }))
    ]);
  };

  const handleRemoveFile = (fileId) => {
    setTelemetryFiles(prev => prev.filter(x => x.id !== fileId));
  };

  const handleProcessTelemetry = async () => {
    setIsProcessingTelemetry(true);
    setTelemetryResult(null);
    setTelemetryLog([]);
    
    const addLog = (e) => setTelemetryLog(p => [...p, { ...e, time: new Date().toLocaleTimeString() }]);
    addLog({ type: 'info', msg: `Iniciando procesamiento de ${telemetryFiles.length} archivo(s)...` });
    
    try {
      const formData = new FormData();
      formData.append('module', telemetryModule);
      formData.append('library', telemetryLibrary || 'ZC');
      telemetryFiles.forEach(f => formData.append('files', f.file));
      
      addLog({ type: 'info', msg: 'Subiendo archivos al servidor...' });
      const startResponse = await fetch(`${API_URL}/api/telemetry/start-job`, {
        method: 'POST',
        body: formData
      });
      const startResult = await startResponse.json();
      
      if (!startResult.success) {
        addLog({ type: 'err', msg: `Error: ${startResult.error}` });
        setIsProcessingTelemetry(false);
        return;
      }
      
      const jobId = startResult.job_id;
      addLog({ type: 'ok', msg: `Job iniciado: ${jobId}` });
      addLog({ type: 'info', msg: 'Procesando en segundo plano...' });
      
      let completed = false;
      let lastLogCount = 0;
      
      while (!completed) {
        await new Promise(r => setTimeout(r, 2000));
        
        try {
          const statusResponse = await fetch(`${API_URL}/api/telemetry/job-status/${jobId}`);
          const status = await statusResponse.json();
          
          if (!status.success) {
            addLog({ type: 'err', msg: 'Error obteniendo estado' });
            continue;
          }
          
          if (status.logs && status.logs.length > lastLogCount) {
            const newLogs = status.logs.slice(lastLogCount);
            newLogs.forEach(log => {
              addLog({ type: log.type, msg: log.msg });
            });
            lastLogCount = status.logs.length;
          }
          
          setTelemetryProgress({ 
            current: status.processed_files, 
            total: status.total_files 
          });
          
          if (status.status === 'completed' || status.status === 'failed') {
            completed = true;
            
            if (status.status === 'completed') {
              const detectedTariffs = status.detected_tariffs?.join(', ') || 'T1';
              addLog({ type: 'ok', msg: `Tarifas detectadas: ${detectedTariffs}` });
              addLog({ type: 'ok', msg: `Completado: ${status.products_created} nuevos, ${status.products_updated} actualizados` });
              
              setTelemetryResult({ 
                ok: true, 
                newC: status.products_created, 
                dupC: status.products_updated 
              });
            } else {
              addLog({ type: 'err', msg: 'Procesamiento fallido' });
              if (status.errors && status.errors.length > 0) {
                status.errors.forEach(err => addLog({ type: 'err', msg: err }));
              }
              setTelemetryResult({ ok: false, newC: 0, dupC: 0 });
            }
          }
        } catch (pollError) {
          console.warn('Polling error:', pollError);
        }
      }
      
      setTelemetryFiles([]);
    } catch (err) {
      addLog({ type: 'err', msg: `Error: ${err.message}` });
      setTelemetryResult({ ok: false, newC: 0, dupC: 0 });
    } finally {
      setIsProcessingTelemetry(false);
    }
  };

  const handleReset = () => {
    setTelemetryResult(null);
    setTelemetryLog([]);
  };

  return (
    <div className="flex gap-6 h-[500px]">
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-gradient-to-br from-orange-500 to-yellow-500 rounded-xl">
            <Zap size={20} className="text-white" />
          </div>
          <div>
            <h3 className="text-lg font-black text-indigo-950 uppercase">Telemetría IA</h3>
            <p className="text-xs text-indigo-400">Sincronización por Reconocimiento Óptico</p>
          </div>
        </div>

        {/* Module Selector */}
        <div className="flex gap-2 mb-4">
          {['montada', 'despiece'].map(mod => (
            <button 
              key={mod} 
              onClick={() => setTelemetryModule(mod)} 
              disabled={isProcessingTelemetry}
              className={`flex-1 p-3 rounded-xl transition-all border-2 ${
                telemetryModule === mod 
                  ? (mod === 'montada' ? 'bg-orange-500 border-orange-400' : 'bg-indigo-500 border-indigo-400') + ' text-white' 
                  : 'bg-slate-50 border-slate-200 text-slate-600'
              }`}
            >
              <span className="font-black text-sm uppercase">{mod}</span>
            </button>
          ))}
        </div>

        {/* Library and Tariff Selectors */}
        <div className="flex gap-2 mb-4">
          {/* Library Selector */}
          <div className="flex-1 bg-gradient-to-r from-slate-50 to-slate-100 rounded-xl p-3 border border-slate-200">
            <p className="text-[10px] font-bold text-slate-500 uppercase mb-2">Librería de Catálogo</p>
            <div className="flex gap-2">
              {['ZC', 'MV'].map(lib => (
                <button 
                  key={lib} 
                  onClick={() => handleLibraryChange(lib)} 
                  disabled={isProcessingTelemetry}
                  className={`flex-1 py-2 px-3 rounded-lg transition-all font-black text-xs uppercase ${
                    telemetryLibrary === lib 
                      ? lib === 'ZC' 
                        ? 'bg-blue-600 text-white shadow-md' 
                        : 'bg-purple-600 text-white shadow-md'
                      : 'bg-white text-slate-500 border border-slate-200 hover:border-slate-400'
                  }`}
                >
                  {lib === 'ZC' ? 'ZC' : 'MV'}
                </button>
              ))}
            </div>
          </div>
          
          {/* Tariff Selector */}
          <div className="flex-1 bg-gradient-to-r from-slate-50 to-slate-100 rounded-xl p-3 border border-slate-200">
            {telemetryLibrary === 'MV' ? (
              <>
                <p className="text-[10px] font-bold text-purple-600 uppercase mb-2">
                  Detección Automática
                </p>
                <div className="w-full py-2 px-3 rounded-lg border border-purple-200 bg-purple-50 text-purple-700 font-bold text-xs">
                  La IA detectará la tarifa (T1-T21) desde el encabezado
                </div>
                <p className="text-[9px] text-purple-500 mt-1">
                  No necesitas seleccionar manualmente
                </p>
              </>
            ) : (
              <>
                <p className="text-[10px] font-bold text-slate-500 uppercase mb-2">
                  Zona ZC
                </p>
                <select
                  value={telemetryTariff}
                  onChange={(e) => handleTariffChange(e.target.value)}
                  disabled={isProcessingTelemetry}
                  className="w-full py-2 px-3 rounded-lg border border-slate-200 bg-white text-slate-700 font-bold text-xs focus:outline-none focus:ring-2 focus:ring-orange-500"
                >
                  {[...Array(12)].map((_, i) => (
                    <option key={`Z${i+1}`} value={`Z${i+1}`}>Zona Z{i+1}</option>
                  ))}
                </select>
                <p className="text-[9px] text-slate-400 mt-1">
                  Selecciona la zona de las imágenes a importar
                </p>
              </>
            )}
          </div>
        </div>

        {/* File Upload Area */}
        <div className="bg-slate-50 rounded-xl p-4 flex-1 flex flex-col border border-slate-200">
          <label className="flex-1 flex flex-col items-center justify-center border-2 border-dashed border-slate-300 rounded-xl p-4 cursor-pointer hover:border-orange-400 hover:bg-orange-50 transition-all min-h-[120px]">
            <FileImage size={36} className="text-slate-400 mb-2" />
            <p className="text-sm font-black text-slate-700 uppercase">Cargar fichas</p>
            <p className="text-xs text-slate-500">JPG, PNG, PDF</p>
            <input 
              type="file" 
              multiple 
              accept="image/*,application/pdf" 
              className="hidden" 
              disabled={isProcessingTelemetry}
              onChange={handleFileUpload} 
            />
          </label>

          {telemetryFiles.length > 0 && (
            <div className="mt-3 space-y-2">
              <div className="max-h-[80px] overflow-y-auto space-y-1">
                {telemetryFiles.map(f => (
                  <div key={f.id} className="bg-white border border-slate-200 rounded-lg p-2 flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-700 truncate flex-1">{f.name}</span>
                    <button onClick={() => handleRemoveFile(f.id)} className="p-1 hover:bg-red-100 rounded">
                      <XCircle size={14} className="text-red-500" />
                    </button>
                  </div>
                ))}
              </div>
              <button 
                disabled={isProcessingTelemetry} 
                className="w-full bg-gradient-to-r from-orange-500 to-orange-600 text-white py-3 rounded-xl font-black uppercase text-xs flex items-center justify-center gap-2 disabled:opacity-50"
                onClick={handleProcessTelemetry}
              >
                {isProcessingTelemetry ? (
                  <><Loader size={16} className="animate-spin" /> Procesando...</>
                ) : (
                  <><Zap size={16} /> Digitalizar</>
                )}
              </button>
            </div>
          )}

          {telemetryResult?.ok && (
            <div className="mt-3 bg-green-50 border border-green-200 rounded-xl p-3">
              <div className="flex items-center gap-2">
                <CheckCircle size={16} className="text-green-600" />
                <span className="font-black text-green-800 text-sm">Completado</span>
              </div>
              <p className="text-xs text-green-700 mt-1">
                {telemetryResult.newC} nuevo(s) - {telemetryResult.dupC} actualizado(s)
              </p>
              <button 
                onClick={handleReset} 
                className="mt-2 w-full bg-indigo-900 text-white py-2 rounded-lg font-bold text-xs flex items-center justify-center gap-2"
              >
                <RefreshCw size={14} /> Nueva
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Log Panel */}
      <div className="w-[280px] bg-indigo-950 rounded-2xl flex flex-col overflow-hidden">
        <div className="p-3 border-b border-indigo-800 flex items-center gap-2">
          <Zap size={14} className="text-orange-500" />
          <span className="text-xs font-black text-white uppercase">
            Log: {telemetryModule} ({telemetryLibrary})
          </span>
        </div>
        
        {isProcessingTelemetry && telemetryProgress.total > 0 && (
          <div className="px-3 py-2 bg-indigo-900/50">
            <div className="h-1 bg-indigo-800 rounded-full overflow-hidden">
              <div 
                className="h-full bg-orange-500 transition-all" 
                style={{ width: `${(telemetryProgress.current / telemetryProgress.total) * 100}%` }} 
              />
            </div>
          </div>
        )}
        
        <div className="flex-1 overflow-y-auto p-3 space-y-1 text-xs">
          {telemetryLog.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center">
              <Zap size={20} className="text-indigo-700 mb-2" />
              <p className="text-indigo-500">Sin actividad</p>
            </div>
          ) : (
            telemetryLog.map((e, i) => (
              e.type === 'new' || e.type === 'dup' ? (
                <div key={i} className="flex items-center gap-2 py-1 px-2 rounded bg-white/5">
                  <span className={`px-1.5 py-0.5 rounded text-[9px] font-black ${
                    e.type === 'new' ? 'bg-green-500' : 'bg-orange-500'
                  } text-white`}>
                    {e.type === 'new' ? 'NUEVO' : 'DUP'}
                  </span>
                  <span className="text-white/80 truncate flex-1">{e.code}</span>
                  <span className={e.type === 'new' ? 'text-green-400' : 'text-orange-400'}>{e.pts}</span>
                </div>
              ) : (
                <div key={i} className={`${
                  e.type === 'err' ? 'text-red-400' : 
                  e.type === 'ok' ? 'text-green-400' : 'text-white/60'
                }`}>
                  [{e.time}] {e.msg}
                </div>
              )
            ))
          )}
        </div>
        
        <div className="p-2 border-t border-indigo-800 flex justify-center gap-3 text-[9px]">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-green-500"></span> Nuevo
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-orange-500"></span> Duplicado
          </span>
        </div>
      </div>
    </div>
  );
};

export default TelemetryTab;
