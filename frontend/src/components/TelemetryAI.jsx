import React, { useState, useEffect, useRef } from 'react';
import { Zap, Upload, CheckCircle, XCircle, Loader, FileImage, RefreshCw, Copy, Plus } from 'lucide-react';
import { productsAPI } from '../services/api';

const TelemetryAI = ({ state, setState }) => {
  const [selectedModule, setSelectedModule] = useState('montada');
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processResult, setProcessResult] = useState(null);
  const [detectionLog, setDetectionLog] = useState([]);
  const [progress, setProgress] = useState({ current: 0, total: 0 });
  const [existingCodes, setExistingCodes] = useState(new Set());
  const logContainerRef = useRef(null);

  // Load existing product codes for duplicate detection
  useEffect(() => {
    const loadExistingProducts = async () => {
      try {
        const products = await productsAPI.getAll(selectedModule);
        const codes = new Set(products.map(p => p.code));
        setExistingCodes(codes);
      } catch (err) {
        console.error('Error loading existing products:', err);
      }
    };
    loadExistingProducts();
  }, [selectedModule]);

  // Auto-scroll log
  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [detectionLog]);

  const addToLog = (entry) => {
    setDetectionLog(prev => [...prev, { ...entry, timestamp: new Date().toLocaleTimeString() }]);
  };

  const handleFileUpload = (e) => {
    const files = Array.from(e.target.files);
    const newFiles = files.map(file => ({
      id: Math.random().toString(36).substr(2, 9),
      file,
      name: file.name,
      status: 'pending',
      preview: URL.createObjectURL(file)
    }));
    setUploadedFiles(prev => [...prev, ...newFiles]);
  };

  const handleProcessFiles = async () => {
    setIsProcessing(true);
    setProcessResult(null);
    setDetectionLog([]);
    setProgress({ current: 0, total: uploadedFiles.length });

    addToLog({ type: 'info', message: `Iniciando sincronización de ${uploadedFiles.length} archivo(s)...` });
    addToLog({ type: 'info', message: `Destino: ${selectedModule.toUpperCase()}` });

    try {
      // Prepare form data
      const formData = new FormData();
      formData.append('module', selectedModule);
      
      uploadedFiles.forEach(file => {
        formData.append('files', file.file);
      });

      addToLog({ type: 'processing', message: 'Enviando archivos al servidor...' });

      // Call backend API
      const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
      const response = await fetch(`${BACKEND_URL}/api/analyze-product-sheets`, {
        method: 'POST',
        body: formData
      });

      const result = await response.json();

      if (result.success && result.products) {
        addToLog({ type: 'info', message: `IA detectó ${result.products.length} producto(s)` });
        
        // Process each product and check for duplicates
        const newProducts = [];
        const duplicateProducts = [];
        const errorProducts = [];
        
        for (let i = 0; i < result.products.length; i++) {
          const product = result.products[i];
          setProgress({ current: i + 1, total: result.products.length });
          
          // Small delay for visual effect
          await new Promise(resolve => setTimeout(resolve, 150));
          
          if (product.error) {
            errorProducts.push(product);
            addToLog({
              type: 'error',
              code: product.code || 'ERROR',
              name: product.error,
              message: 'Error al procesar'
            });
          } else if (existingCodes.has(product.code)) {
            duplicateProducts.push(product);
            addToLog({
              type: 'duplicate',
              code: product.code,
              name: product.name,
              points: product.points || product.zonePoints?.Z1 || 0
            });
          } else {
            newProducts.push(product);
            addToLog({
              type: 'new',
              code: product.code,
              name: product.name,
              points: product.points || product.zonePoints?.Z1 || 0
            });
            // Add to existing codes for subsequent duplicate detection
            setExistingCodes(prev => new Set([...prev, product.code]));
          }
        }

        // Only add NEW products to the database
        if (newProducts.length > 0) {
          addToLog({ type: 'info', message: `Guardando ${newProducts.length} producto(s) nuevo(s)...` });
          
          try {
            // Save new products to database
            await productsAPI.bulkCreate(newProducts);
            addToLog({ type: 'success', message: `${newProducts.length} producto(s) guardado(s) correctamente` });
          } catch (saveError) {
            addToLog({ type: 'error', message: `Error al guardar: ${saveError.message}` });
          }
        }

        // Update local state
        const catalogIndex = state.catalogs.findIndex(c => c.module === selectedModule);
        if (catalogIndex !== -1 && newProducts.length > 0) {
          const updatedCatalogs = [...state.catalogs];
          updatedCatalogs[catalogIndex] = {
            ...updatedCatalogs[catalogIndex],
            products: [...updatedCatalogs[catalogIndex].products, ...newProducts]
          };
          setState(prev => ({ ...prev, catalogs: updatedCatalogs }));
        }

        // Summary
        addToLog({ type: 'divider' });
        addToLog({ 
          type: 'summary', 
          newCount: newProducts.length, 
          duplicateCount: duplicateProducts.length,
          errorCount: errorProducts.length
        });

        setProcessResult({
          success: true,
          newCount: newProducts.length,
          duplicateCount: duplicateProducts.length,
          errorCount: errorProducts.length,
          products: result.products
        });
      } else {
        addToLog({ type: 'error', message: result.error || 'Error desconocido' });
        setProcessResult({
          success: false,
          error: result.error || 'Error desconocido'
        });
      }

      setUploadedFiles([]);
      setIsProcessing(false);
      
    } catch (error) {
      console.error('Error processing files:', error);
      addToLog({ type: 'error', message: error.message });
      setProcessResult({
        success: false,
        error: error.message
      });
      setIsProcessing(false);
    }
  };

  const removeFile = (fileId) => {
    setUploadedFiles(prev => prev.filter(f => f.id !== fileId));
  };

  const resetProcess = () => {
    setProcessResult(null);
    setDetectionLog([]);
    setProgress({ current: 0, total: 0 });
  };

  // Render log entry
  const renderLogEntry = (entry, index) => {
    if (entry.type === 'divider') {
      return <div key={index} className="border-t border-white/20 my-3"></div>;
    }

    if (entry.type === 'summary') {
      return (
        <div key={index} className="bg-white/10 rounded-xl p-4 mt-4">
          <h4 className="text-white font-black uppercase text-sm mb-3">Resumen de Sincronización</h4>
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-green-500/30 rounded-lg p-3 text-center">
              <div className="text-2xl font-black text-green-400">{entry.newCount}</div>
              <div className="text-[10px] text-green-300 font-bold uppercase">Nuevos</div>
            </div>
            <div className="bg-orange-500/30 rounded-lg p-3 text-center">
              <div className="text-2xl font-black text-orange-400">{entry.duplicateCount}</div>
              <div className="text-[10px] text-orange-300 font-bold uppercase">Duplicados</div>
            </div>
            <div className="bg-red-500/30 rounded-lg p-3 text-center">
              <div className="text-2xl font-black text-red-400">{entry.errorCount}</div>
              <div className="text-[10px] text-red-300 font-bold uppercase">Errores</div>
            </div>
          </div>
        </div>
      );
    }

    if (entry.type === 'new' || entry.type === 'duplicate') {
      const isNew = entry.type === 'new';
      return (
        <div key={index} className="flex items-center gap-3 py-2 px-3 rounded-lg bg-white/5 hover:bg-white/10 transition-all">
          <div className={`w-8 h-8 rounded-full flex items-center justify-center font-black text-xs ${
            isNew ? 'bg-green-500 text-white' : 'bg-orange-500 text-white'
          }`}>
            {isNew ? <Plus size={14} /> : <Copy size={14} />}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="font-black text-white text-sm">{entry.code}</span>
              <span className={`px-2 py-0.5 rounded text-[9px] font-black uppercase ${
                isNew 
                  ? 'bg-green-500 text-white' 
                  : 'bg-orange-500 text-white'
              }`}>
                {isNew ? 'NUEVO' : 'DUPLICADO'}
              </span>
            </div>
            <p className="text-xs text-white/60 truncate">{entry.name}</p>
          </div>
          <div className="text-right">
            <div className="text-xs text-white/40 uppercase font-bold">Puntos</div>
            <div className={`text-lg font-black ${isNew ? 'text-green-400' : 'text-orange-400'}`}>
              {entry.points}
            </div>
          </div>
        </div>
      );
    }

    if (entry.type === 'error' && entry.code) {
      return (
        <div key={index} className="flex items-center gap-3 py-2 px-3 rounded-lg bg-red-500/20">
          <div className="w-8 h-8 rounded-full flex items-center justify-center bg-red-500 text-white">
            <XCircle size={14} />
          </div>
          <div className="flex-1">
            <span className="font-black text-white text-sm">{entry.code}</span>
            <span className="ml-2 px-2 py-0.5 rounded text-[9px] font-black uppercase bg-red-500 text-white">ERROR</span>
            <p className="text-xs text-red-300">{entry.name}</p>
          </div>
        </div>
      );
    }

    // Info, processing, success, error messages
    const iconMap = {
      info: <Zap size={14} className="text-blue-400" />,
      processing: <Loader size={14} className="text-yellow-400 animate-spin" />,
      success: <CheckCircle size={14} className="text-green-400" />,
      error: <XCircle size={14} className="text-red-400" />
    };

    const colorMap = {
      info: 'text-blue-300',
      processing: 'text-yellow-300',
      success: 'text-green-300',
      error: 'text-red-300'
    };

    return (
      <div key={index} className={`flex items-center gap-2 py-1 text-xs ${colorMap[entry.type] || 'text-white/60'}`}>
        {iconMap[entry.type]}
        <span className="text-white/40">[{entry.timestamp}]</span>
        <span className="font-bold">{entry.message}</span>
      </div>
    );
  };

  return (
    <div className="h-full flex bg-gradient-to-br from-purple-900 via-indigo-900 to-slate-900 overflow-hidden">
      {/* Left Panel - Upload */}
      <div className="flex-1 flex flex-col p-8 overflow-auto">
        {/* Header */}
        <div className="flex items-center gap-4 mb-6">
          <div className="p-3 bg-gradient-to-br from-orange-500 to-yellow-500 rounded-xl shadow-2xl">
            <Zap size={28} className="text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-black text-white uppercase tracking-tight">TELEMETRÍA IA</h2>
            <p className="text-xs font-bold text-purple-300 uppercase tracking-wider">Sincronización Industrial por Reconocimiento Óptico</p>
          </div>
        </div>

        {/* Module Selection */}
        <div className="mb-4 flex gap-3">
          <button
            onClick={() => setSelectedModule('montada')}
            disabled={isProcessing}
            className={`flex-1 p-4 rounded-xl transition-all border-2 ${
              selectedModule === 'montada'
                ? 'bg-gradient-to-br from-orange-500 to-orange-600 border-orange-400 shadow-xl'
                : 'bg-white/10 border-white/20 hover:border-orange-400'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-base font-black text-white uppercase">MONTADA</h3>
              {selectedModule === 'montada' && <CheckCircle size={18} className="text-white" />}
            </div>
            <p className="text-xs text-white/70 font-bold">Muebles terminados</p>
          </button>

          <button
            onClick={() => setSelectedModule('despiece')}
            disabled={isProcessing}
            className={`flex-1 p-4 rounded-xl transition-all border-2 ${
              selectedModule === 'despiece'
                ? 'bg-gradient-to-br from-indigo-500 to-indigo-600 border-indigo-400 shadow-xl'
                : 'bg-white/10 border-white/20 hover:border-indigo-400'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-base font-black text-white uppercase">DESPIECE</h3>
              {selectedModule === 'despiece' && <CheckCircle size={18} className="text-white" />}
            </div>
            <p className="text-xs text-white/70 font-bold">Piezas industriales</p>
          </button>
        </div>

        {/* Upload Area */}
        <div className="bg-white rounded-xl p-6 shadow-xl flex-1 flex flex-col">
          <h3 className="text-sm font-black text-indigo-950 uppercase mb-3 flex items-center gap-2">
            <Upload size={16} className="text-orange-600" />
            Subir Fichas de Productos
          </h3>

          <label className="flex-1 flex flex-col items-center justify-center border-3 border-dashed border-indigo-200 rounded-xl p-6 cursor-pointer hover:border-orange-500 hover:bg-orange-50 transition-all group min-h-[150px]">
            <FileImage size={48} className="text-indigo-300 group-hover:text-orange-600 transition-colors mb-3" />
            <p className="text-sm font-black text-indigo-900 uppercase mb-1">Click para cargar fichas</p>
            <p className="text-xs text-indigo-500 font-bold">JPG, PNG, PDF</p>
            <input
              type="file"
              multiple
              accept="image/*,application/pdf"
              onChange={handleFileUpload}
              className="hidden"
              disabled={isProcessing}
            />
          </label>

          {/* Uploaded Files */}
          {uploadedFiles.length > 0 && (
            <div className="mt-4 space-y-2">
              <h4 className="text-xs font-black text-indigo-900 uppercase">Archivos ({uploadedFiles.length})</h4>
              <div className="max-h-[120px] overflow-y-auto space-y-2">
                {uploadedFiles.map(file => (
                  <div key={file.id} className="bg-indigo-50 border border-indigo-200 rounded-lg p-2 flex items-center justify-between">
                    <div className="flex items-center gap-2 flex-1 min-w-0">
                      {file.preview && (
                        <img src={file.preview} alt={file.name} className="w-8 h-8 object-cover rounded" />
                      )}
                      <p className="text-xs font-bold text-indigo-900 truncate">{file.name}</p>
                    </div>
                    <button
                      onClick={() => removeFile(file.id)}
                      className="p-1 hover:bg-red-100 rounded transition-all"
                      disabled={isProcessing}
                    >
                      <XCircle size={14} className="text-red-600" />
                    </button>
                  </div>
                ))}
              </div>

              <button
                onClick={handleProcessFiles}
                disabled={isProcessing || uploadedFiles.length === 0}
                className="w-full bg-gradient-to-r from-orange-600 to-orange-500 text-white py-3 rounded-lg font-black uppercase text-xs tracking-widest shadow-lg hover:shadow-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {isProcessing ? (
                  <>
                    <Loader size={16} className="animate-spin" />
                    Procesando...
                  </>
                ) : (
                  <>
                    <Zap size={16} />
                    Iniciar Digitalización
                  </>
                )}
              </button>
            </div>
          )}

          {/* Success Result - New Sync Button */}
          {processResult && processResult.success && (
            <div className="mt-4">
              <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-3">
                <div className="flex items-center gap-2 mb-2">
                  <CheckCircle size={20} className="text-green-600" />
                  <h4 className="font-black text-green-800 uppercase text-sm">Sincronización Completada</h4>
                </div>
                <p className="text-xs text-green-700">
                  {processResult.newCount} nuevo(s) • {processResult.duplicateCount} duplicado(s) • {processResult.errorCount} error(es)
                </p>
              </div>
              <button
                onClick={resetProcess}
                className="w-full bg-indigo-950 text-white py-3 rounded-lg font-black uppercase text-xs tracking-widest flex items-center justify-center gap-2 hover:bg-indigo-900 transition-all"
              >
                <RefreshCw size={16} />
                Nueva Sincronización
              </button>
            </div>
          )}
        </div>

        {/* Info */}
        <div className="mt-4 bg-green-500/20 border border-green-500 rounded-lg p-3 flex items-start gap-2">
          <CheckCircle size={18} className="text-green-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-xs font-black text-green-300 uppercase">Gemini Vision AI Activo</p>
            <p className="text-[10px] text-green-200">
              Sistema de análisis inteligente con Google Gemini 2.5 Pro
            </p>
          </div>
        </div>
      </div>

      {/* Right Panel - Detection Log */}
      <div className="w-[400px] bg-indigo-950 border-l border-indigo-800 flex flex-col">
        {/* Log Header */}
        <div className="p-4 border-b border-indigo-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Zap size={16} className="text-orange-500" />
            <h3 className="text-sm font-black text-white uppercase tracking-wider">
              Log de Detección: {selectedModule}
            </h3>
          </div>
          {detectionLog.length > 0 && (
            <button
              onClick={() => setDetectionLog([])}
              className="p-1 hover:bg-white/10 rounded transition-all"
              title="Limpiar log"
            >
              <RefreshCw size={14} className="text-white/50" />
            </button>
          )}
        </div>

        {/* Progress Bar */}
        {isProcessing && progress.total > 0 && (
          <div className="px-4 py-2 bg-indigo-900/50">
            <div className="flex items-center justify-between text-xs text-white/60 mb-1">
              <span>Procesando productos...</span>
              <span>{progress.current}/{progress.total}</span>
            </div>
            <div className="h-1 bg-indigo-800 rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-orange-500 to-yellow-500 transition-all duration-300"
                style={{ width: `${(progress.current / progress.total) * 100}%` }}
              />
            </div>
          </div>
        )}

        {/* Log Content */}
        <div 
          ref={logContainerRef}
          className="flex-1 overflow-y-auto p-4 space-y-2"
        >
          {detectionLog.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center">
              <div className="w-16 h-16 rounded-full border-2 border-dashed border-indigo-700 flex items-center justify-center mb-4">
                <Zap size={24} className="text-indigo-600" />
              </div>
              <p className="text-sm font-bold text-indigo-400">Sin actividad</p>
              <p className="text-xs text-indigo-500 mt-1">Sube fichas técnicas para iniciar</p>
            </div>
          ) : (
            detectionLog.map((entry, index) => renderLogEntry(entry, index))
          )}
        </div>

        {/* Legend */}
        <div className="p-3 border-t border-indigo-800 flex items-center justify-center gap-4">
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-full bg-green-500"></div>
            <span className="text-[10px] text-white/60 font-bold uppercase">Nuevo</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-full bg-orange-500"></div>
            <span className="text-[10px] text-white/60 font-bold uppercase">Duplicado</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-3 h-3 rounded-full bg-red-500"></div>
            <span className="text-[10px] text-white/60 font-bold uppercase">Error</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TelemetryAI;
