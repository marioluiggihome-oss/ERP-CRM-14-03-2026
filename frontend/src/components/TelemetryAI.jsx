import React, { useState } from 'react';
import { Zap, Upload, CheckCircle, XCircle, Loader, FileImage, AlertTriangle } from 'lucide-react';

const TelemetryAI = ({ state, setState }) => {
  const [selectedModule, setSelectedModule] = useState('montada');
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processResult, setProcessResult] = useState(null);

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

    try {
      // Prepare form data
      const formData = new FormData();
      formData.append('module', selectedModule);
      
      uploadedFiles.forEach(file => {
        formData.append('files', file.file);
      });

      // Call backend API
      const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
      const response = await fetch(`${BACKEND_URL}/api/analyze-product-sheets`, {
        method: 'POST',
        body: formData
      });

      const result = await response.json();

      if (result.success && result.products) {
        // Add products to catalog
        const catalogIndex = state.catalogs.findIndex(c => c.module === selectedModule);
        if (catalogIndex !== -1) {
          const updatedCatalogs = [...state.catalogs];
          const validProducts = result.products.filter(p => !p.error);
          
          updatedCatalogs[catalogIndex] = {
            ...updatedCatalogs[catalogIndex],
            products: [...updatedCatalogs[catalogIndex].products, ...validProducts]
          };
          
          setState(prev => ({ ...prev, catalogs: updatedCatalogs }));
        }

        setProcessResult({
          success: true,
          count: result.products.filter(p => !p.error).length,
          products: result.products
        });
      } else {
        setProcessResult({
          success: false,
          error: result.error || 'Error desconocido'
        });
      }

      setUploadedFiles([]);
      setIsProcessing(false);
      
    } catch (error) {
      console.error('Error processing files:', error);
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

  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-purple-900 via-indigo-900 to-slate-900 p-12 overflow-auto">
      <div className="flex items-center gap-4 mb-8">
        <div className="p-4 bg-gradient-to-br from-orange-500 to-yellow-500 rounded-2xl shadow-2xl">
          <Zap size={32} className="text-white" />
        </div>
        <div>
          <h2 className="text-3xl font-black text-white uppercase tracking-tight">TELEMETRÍA IA</h2>
          <p className="text-sm font-bold text-purple-300 uppercase tracking-wider">Sincronización Industrial por Reconocimiento Óptico</p>
        </div>
      </div>

      {/* Module Selection */}
      <div className="mb-6 flex gap-4">
        <button
          onClick={() => setSelectedModule('montada')}
          className={`flex-1 p-6 rounded-2xl transition-all border-4 ${
            selectedModule === 'montada'
              ? 'bg-gradient-to-br from-orange-500 to-orange-600 border-orange-400 shadow-2xl scale-105'
              : 'bg-white/10 border-white/20 hover:border-orange-400'
          }`}
        >
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-xl font-black text-white uppercase">CATÁLOGO MONTADA</h3>
            {selectedModule === 'montada' && <CheckCircle size={24} className="text-white" />}
          </div>
          <p className="text-sm text-white/80 font-bold">Digitalizar muebles terminados</p>
          <p className="text-xs text-white/60 mt-2">Soporta múltiples fichas de producto</p>
        </button>

        <button
          onClick={() => setSelectedModule('despiece')}
          className={`flex-1 p-6 rounded-2xl transition-all border-4 ${
            selectedModule === 'despiece'
              ? 'bg-gradient-to-br from-indigo-500 to-indigo-600 border-indigo-400 shadow-2xl scale-105'
              : 'bg-white/10 border-white/20 hover:border-indigo-400'
          }`}
        >
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-xl font-black text-white uppercase">CATÁLOGO DESPIECE</h3>
            {selectedModule === 'despiece' && <CheckCircle size={24} className="text-white" />}
          </div>
          <p className="text-sm text-white/80 font-bold">Digitalizar piezas industriales</p>
          <p className="text-xs text-white/60 mt-2">Soporta múltiples fichas de producto</p>
        </button>
      </div>

      {/* Upload Area */}
      <div className="bg-white rounded-2xl p-8 shadow-2xl mb-6">
        <h3 className="text-lg font-black text-indigo-950 uppercase mb-4 flex items-center gap-3">
          <Upload size={20} className="text-orange-600" />
          Subir Fichas de Productos
        </h3>

        <label className="block border-4 border-dashed border-indigo-200 rounded-xl p-12 text-center cursor-pointer hover:border-orange-500 hover:bg-orange-50 transition-all group">
          <FileImage size={64} className="mx-auto text-indigo-300 group-hover:text-orange-600 transition-colors mb-4" />
          <p className="text-lg font-black text-indigo-900 uppercase mb-2">Click para cargar fichas técnicas</p>
          <p className="text-sm text-indigo-500 font-bold">JPG, PNG, PDF - Hasta 10 archivos simultáneos</p>
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
          <div className="mt-6 space-y-3">
            <h4 className="text-sm font-black text-indigo-900 uppercase">Archivos Cargados ({uploadedFiles.length})</h4>
            <div className="grid grid-cols-2 gap-3">
              {uploadedFiles.map(file => (
                <div key={file.id} className="bg-indigo-50 border border-indigo-200 rounded-xl p-3 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {file.preview && (
                      <img src={file.preview} alt={file.name} className="w-12 h-12 object-cover rounded-lg" />
                    )}
                    <div>
                      <p className="text-xs font-black text-indigo-900 truncate max-w-[200px]">{file.name}</p>
                      <p className="text-[10px] text-indigo-500 font-bold">Pendiente de procesar</p>
                    </div>
                  </div>
                  <button
                    onClick={() => removeFile(file.id)}
                    className="p-2 hover:bg-red-100 rounded-lg transition-all"
                    disabled={isProcessing}
                  >
                    <XCircle size={16} className="text-red-600" />
                  </button>
                </div>
              ))}
            </div>

            <button
              onClick={handleProcessFiles}
              disabled={isProcessing || uploadedFiles.length === 0}
              className="w-full bg-gradient-to-r from-orange-600 to-orange-500 text-white py-4 rounded-xl font-black uppercase text-sm tracking-widest shadow-xl hover:shadow-2xl transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-3"
            >
              {isProcessing ? (
                <>
                  <Loader size={20} className="animate-spin" />
                  Procesando con IA...
                </>
              ) : (
                <>
                  <Zap size={20} />
                  Iniciar Digitalización IA
                </>
              )}
            </button>
          </div>
        )}
      </div>

      {/* Processing Result */}
      {processResult && (
        <div className={`rounded-2xl p-6 shadow-2xl ${processResult.success ? 'bg-green-500' : 'bg-red-500'}`}>
          <div className="flex items-center gap-4">
            {processResult.success ? (
              <CheckCircle size={48} className="text-white" />
            ) : (
              <XCircle size={48} className="text-white" />
            )}
            <div>
              <h3 className="text-2xl font-black text-white uppercase">
                {processResult.success ? '¡Importación Exitosa!' : 'Error en Importación'}
              </h3>
              <p className="text-white/90 font-bold">
                {processResult.success
                  ? `${processResult.count} productos digitalizados y agregados al catálogo ${selectedModule}`
                  : 'Ocurrió un error al procesar las fichas'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Warning */}
      <div className="mt-6 bg-yellow-500/20 border border-yellow-500 rounded-xl p-4 flex items-start gap-3">
        <AlertTriangle size={24} className="text-yellow-400 flex-shrink-0" />
        <div>
          <p className="text-sm font-black text-yellow-300 uppercase mb-1">Funcionalidad de IA Requerida</p>
          <p className="text-xs text-yellow-200">
            Esta función requiere integración con Google Gemini AI. Actualmente en modo DEMO.
            Para activarla en producción, se necesita configurar la API de Gemini Vision.
          </p>
        </div>
      </div>
    </div>
  );
};

export default TelemetryAI;
