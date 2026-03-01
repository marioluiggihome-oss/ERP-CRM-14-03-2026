import React, { useState, useRef } from 'react';
import { Sparkles, Upload, Wand2, AlertCircle, Loader2, Package, Check, Plus, X, FileImage, RefreshCw, Layers } from 'lucide-react';
import { getProductIcon } from './FurnitureIcons';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const Visualizer = ({ images, state, setState, onAddToBudget }) => {
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [error, setError] = useState(null);
  const [selectedImages, setSelectedImages] = useState([]);  // Array de imágenes
  const fileInputRef = useRef(null);
  
  const canUseAI = state.currentUser?.canUseAIAnalysis || state.currentUser?.isAdmin || state.currentUser?.isGerente;

  const handleImageUpload = (e) => {
    const files = Array.from(e.target.files);
    if (files.length === 0) return;
    
    // Procesar todas las imágenes seleccionadas
    const newImages = [];
    let loadedCount = 0;
    
    files.forEach((file, index) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        newImages[index] = {
          dataUrl: e.target.result,
          file: file,
          name: file.name
        };
        loadedCount++;
        
        // Cuando todas estén cargadas, actualizar el estado
        if (loadedCount === files.length) {
          setSelectedImages(prev => [...prev, ...newImages.filter(Boolean)]);
          setAnalysisResult(null);
          setError(null);
        }
      };
      reader.readAsDataURL(file);
    });
  };

  const removeImage = (index) => {
    setSelectedImages(prev => prev.filter((_, i) => i !== index));
  };

  const analyzeKitchenPlan = async () => {
    if (selectedImages.length === 0) return;
    
    setAnalyzing(true);
    setError(null);
    setAnalysisResult(null);

    try {
      const formData = new FormData();
      
      // Si es una sola imagen, usar el endpoint simple
      if (selectedImages.length === 1) {
        formData.append('file', selectedImages[0].file);
        
        const response = await fetch(`${API_URL}/api/ia-lab/analyze-kitchen-plan`, {
          method: 'POST',
          body: formData
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || `Error ${response.status}: Error al analizar el plano`);
        }

        const data = await response.json();
        setAnalysisResult(data.analysis);
      } else {
        // Múltiples imágenes - usar endpoint multi
        selectedImages.forEach((img, idx) => {
          formData.append('files', img.file);
        });
        
        const response = await fetch(`${API_URL}/api/ia-lab/analyze-kitchen-plan-multi`, {
          method: 'POST',
          body: formData
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || `Error ${response.status}: Error al analizar los planos`);
        }

        const data = await response.json();
        setAnalysisResult(data.analysis);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setAnalyzing(false);
    }
  };

  const addFurnitureToBudget = (furniture, showAlert = true) => {
    if (onAddToBudget) {
      // Pasar directamente el objeto de la IA con todas sus propiedades originales
      onAddToBudget(furniture, showAlert);
    }
  };

  const addAllFurnitureToBudget = () => {
    if (!analysisResult?.muebles_detectados?.length) return;
    
    const count = analysisResult.muebles_detectados.length;
    analysisResult.muebles_detectados.forEach((f, i) => {
      // Only show alert on the last one
      addFurnitureToBudget(f, false);
    });
    
    alert(`✅ Se han añadido ${count} muebles al presupuesto.\n\nVe a la pestaña "Presupuesto" para verlos.`);
  };

  const clearAll = () => {
    setSelectedImages([]);
    setAnalysisResult(null);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-indigo-50 to-purple-50 p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <div className="p-4 bg-purple-600 rounded-2xl shadow-xl">
            <Sparkles size={32} className="text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-black text-slate-900 uppercase tracking-tight">IA Lab - Analizador de Planos</h2>
            <p className="text-sm font-bold text-slate-400 uppercase tracking-wider">Detecta muebles automáticamente con Gemini Vision</p>
          </div>
        </div>
        {selectedImages.length > 0 && (
          <button
            onClick={clearAll}
            className="flex items-center gap-2 px-4 py-2 bg-slate-200 text-slate-700 rounded-lg font-bold text-sm hover:bg-slate-300"
          >
            <RefreshCw size={16} />
            Limpiar todo
          </button>
        )}
      </div>

      {!canUseAI && (
        <div className="mb-6 p-4 bg-orange-50 border border-orange-200 rounded-xl flex items-center gap-3">
          <AlertCircle size={20} className="text-orange-600" />
          <span className="text-xs font-black text-orange-800 uppercase">Módulo IA deshabilitado para tu usuario</span>
        </div>
      )}

      <div className="flex-1 grid grid-cols-2 gap-6 min-h-0 overflow-hidden">
        {/* Left: Upload & Image Preview */}
        <div className="bg-white rounded-2xl p-6 shadow-xl border border-indigo-100 flex flex-col overflow-hidden max-h-full">
          <h3 className="text-sm font-black text-indigo-900 uppercase tracking-widest mb-4 flex items-center gap-2 shrink-0">
            <FileImage size={16} className="text-purple-600" />
            Planos de Cocina
            {selectedImages.length > 0 && (
              <span className="ml-2 px-2 py-0.5 bg-purple-100 text-purple-700 rounded-full text-xs font-black">
                {selectedImages.length} {selectedImages.length === 1 ? 'pared' : 'paredes'}
              </span>
            )}
          </h3>
          
          {selectedImages.length === 0 ? (
            <label className="flex-1 min-h-0 border-4 border-dashed border-indigo-200 rounded-xl flex flex-col items-center justify-center cursor-pointer hover:border-purple-400 hover:bg-purple-50/50 transition-all group">
              <Layers size={48} className="text-indigo-300 group-hover:text-purple-600 transition-colors mb-4" />
              <p className="text-sm font-black text-indigo-900 uppercase">Subir planos (1 o más paredes)</p>
              <p className="text-xs text-indigo-400 mt-2">JPG, PNG - Selecciona varias imágenes a la vez</p>
              <input 
                ref={fileInputRef}
                type="file" 
                accept="image/*"
                multiple
                onChange={handleImageUpload}
                className="hidden"
                disabled={!canUseAI}
              />
            </label>
          ) : (
            <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
              {/* Images grid */}
              <div className="flex-1 min-h-0 overflow-auto">
                <div className={`grid gap-2 ${selectedImages.length === 1 ? 'grid-cols-1' : 'grid-cols-2'}`}>
                  {selectedImages.map((img, idx) => (
                    <div key={idx} className="relative rounded-xl overflow-hidden border-2 border-indigo-100 group">
                      <img 
                        src={img.dataUrl} 
                        alt={`Pared ${idx + 1}`} 
                        className="w-full h-auto object-contain bg-slate-100"
                        style={{ maxHeight: selectedImages.length === 1 ? '40vh' : '25vh' }}
                      />
                      <div className="absolute top-2 left-2 px-2 py-1 bg-indigo-900/80 text-white rounded-lg text-xs font-black">
                        PARED {idx + 1}
                      </div>
                      <button
                        onClick={() => removeImage(idx)}
                        className="absolute top-2 right-2 p-1 bg-red-500 text-white rounded-lg opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        <X size={14} />
                      </button>
                    </div>
                  ))}
                </div>
                
                {/* Add more images */}
                <label className="mt-2 border-2 border-dashed border-indigo-200 rounded-xl p-3 flex items-center justify-center cursor-pointer hover:border-purple-400 hover:bg-purple-50/50 transition-all">
                  <Plus size={16} className="text-indigo-400 mr-2" />
                  <span className="text-xs font-bold text-indigo-600 uppercase">Añadir más paredes</span>
                  <input 
                    type="file" 
                    accept="image/*"
                    multiple
                    onChange={handleImageUpload}
                    className="hidden"
                    disabled={!canUseAI}
                  />
                </label>
              </div>
              
              {/* Analyzing overlay */}
              {analyzing && (
                <div className="absolute inset-0 bg-indigo-950/80 flex flex-col items-center justify-center rounded-xl z-10">
                  <Loader2 className="w-12 h-12 text-purple-400 animate-spin mb-4" />
                  <p className="text-white font-black uppercase text-sm">Analizando {selectedImages.length} {selectedImages.length === 1 ? 'plano' : 'planos'}...</p>
                  <p className="text-purple-300 text-xs mt-2">Detectando muebles con IA</p>
                </div>
              )}
              
              {/* Button always visible at the bottom */}
              {!analyzing && !analysisResult && (
                <button
                  onClick={analyzeKitchenPlan}
                  className="mt-4 shrink-0 w-full py-4 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-xl font-black uppercase text-sm flex items-center justify-center gap-3 hover:from-purple-700 hover:to-indigo-700 shadow-lg transition-all"
                  data-testid="analyze-plan-btn"
                >
                  <Wand2 size={20} />
                  Analizar {selectedImages.length} {selectedImages.length === 1 ? 'Plano' : 'Planos'} con IA
                </button>
              )}
            </div>
          )}

          {error && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-xl flex items-center gap-2 text-red-700">
              <AlertCircle size={18} />
              <span className="text-sm font-bold">{error}</span>
            </div>
          )}
        </div>

        {/* Right: Analysis Results */}
        <div className="bg-white rounded-2xl p-6 shadow-xl border border-indigo-100 flex flex-col overflow-hidden">
          <h3 className="text-sm font-black text-indigo-900 uppercase tracking-widest mb-4 flex items-center gap-2">
            <Package size={16} className="text-purple-600" />
            Muebles Detectados
          </h3>

          {!analysisResult ? (
            <div className="flex-1 flex flex-col items-center justify-center text-slate-400">
              <Package size={64} className="opacity-30 mb-4" />
              <p className="font-bold text-sm">Sube un plano y analízalo</p>
              <p className="text-xs mt-1">La IA detectará los muebles automáticamente</p>
            </div>
          ) : (
            <div className="flex-1 flex flex-col overflow-hidden">
              {/* Summary */}
              {analysisResult.resumen && (
                <div className="mb-4">
                  {analysisResult.resumen.paredes_analizadas > 1 && (
                    <div className="mb-2 px-3 py-2 bg-purple-100 rounded-lg text-center">
                      <span className="text-xs font-black text-purple-700 uppercase">
                        {analysisResult.resumen.paredes_analizadas} paredes analizadas
                      </span>
                    </div>
                  )}
                  <div className="grid grid-cols-4 gap-2">
                    <div className="bg-indigo-50 rounded-lg p-3 text-center">
                      <p className="text-2xl font-black text-indigo-600">{analysisResult.resumen.total_altos || 0}</p>
                      <p className="text-[10px] font-bold text-indigo-400 uppercase">Altos</p>
                    </div>
                    <div className="bg-emerald-50 rounded-lg p-3 text-center">
                      <p className="text-2xl font-black text-emerald-600">{analysisResult.resumen.total_bajos || 0}</p>
                      <p className="text-[10px] font-bold text-emerald-400 uppercase">Bajos</p>
                    </div>
                    <div className="bg-orange-50 rounded-lg p-3 text-center">
                      <p className="text-2xl font-black text-orange-600">{analysisResult.resumen.total_columnas || 0}</p>
                      <p className="text-[10px] font-bold text-orange-400 uppercase">Columnas</p>
                    </div>
                    <div className="bg-purple-50 rounded-lg p-3 text-center">
                      <p className="text-2xl font-black text-purple-600">{analysisResult.muebles_detectados?.length || 0}</p>
                      <p className="text-[10px] font-bold text-purple-400 uppercase">Total</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Furniture List */}
              <div className="flex-1 overflow-y-auto space-y-2">
                {analysisResult.muebles_detectados?.map((furniture, idx) => (
                  <div 
                    key={idx}
                    className="border border-slate-200 rounded-xl p-3 hover:border-purple-400 hover:bg-purple-50/50 transition-all group"
                  >
                    <div className="flex items-center gap-3">
                      <div 
                        className="w-10 h-10 flex items-center justify-center text-indigo-600 bg-indigo-50 rounded-lg"
                        dangerouslySetInnerHTML={{ __html: getProductIcon(furniture.codigo_sugerido, furniture.subtipo) }}
                      />
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-black text-indigo-900 text-sm">{furniture.codigo_sugerido}</span>
                          {furniture.pared && (
                            <span className="text-[10px] px-2 py-0.5 rounded-full font-bold bg-slate-100 text-slate-600">
                              P{furniture.pared}
                            </span>
                          )}
                          <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${
                            furniture.confianza === 'ALTA' ? 'bg-emerald-100 text-emerald-700' :
                            furniture.confianza === 'MEDIA' ? 'bg-amber-100 text-amber-700' :
                            'bg-slate-100 text-slate-600'
                          }`}>
                            {furniture.confianza}
                          </span>
                        </div>
                        <p className="text-xs text-slate-500">
                          {furniture.tipo} {furniture.subtipo?.replace(/_/g, ' ')} • {furniture.ancho_estimado}×{furniture.alto_estimado}×{furniture.fondo_estimado}
                        </p>
                        {furniture.posicion && (
                          <p className="text-[10px] text-slate-400 italic">{furniture.posicion}</p>
                        )}
                      </div>
                      <button
                        onClick={() => addFurnitureToBudget(furniture)}
                        className="p-2 bg-emerald-500 text-white rounded-lg opacity-0 group-hover:opacity-100 transition-opacity"
                        title="Añadir al presupuesto"
                      >
                        <Plus size={16} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {/* Observations */}
              {analysisResult.observaciones && (
                <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-xl">
                  <p className="text-xs font-bold text-amber-800">💡 {analysisResult.observaciones}</p>
                </div>
              )}

              {/* Add All Button */}
              {analysisResult.muebles_detectados?.length > 0 && (
                <button
                  onClick={addAllFurnitureToBudget}
                  className="mt-4 w-full py-3 bg-emerald-600 text-white rounded-xl font-black uppercase text-sm flex items-center justify-center gap-2 hover:bg-emerald-700 transition-colors"
                >
                  <Plus size={18} />
                  Añadir todos al presupuesto ({analysisResult.muebles_detectados.length})
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Visualizer;
