import React, { useState } from 'react';
import { Sparkles, Upload, Wand2, AlertCircle } from 'lucide-react';

const Visualizer = ({ images, state, setState }) => {
  const [analyzing, setAnalyzing] = useState(false);
  const canUseAI = state.currentUser?.canUseAIAnalysis;

  const handleImageUpload = (e) => {
    const files = Array.from(e.target.files);
    const readers = files.map(file => {
      return new Promise((resolve) => {
        const reader = new FileReader();
        reader.onload = (e) => resolve(e.target.result);
        reader.readAsDataURL(file);
      });
    });

    Promise.all(readers).then(results => {
      const budgetKey = state.currentModule === 'montada' ? 'budgetItemsMontada' : 'budgetItemsDespiece';
      setState(prev => ({
        ...prev,
        uploadedImages: [...prev.uploadedImages, ...results]
      }));
    });
  };

  const mockAIAnalysis = () => {
    setAnalyzing(true);
    setTimeout(() => {
      alert('🤖 IA Lab: Funcionalidad de análisis disponible con integración Gemini AI');
      setAnalyzing(false);
    }, 2000);
  };

  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-indigo-50 to-purple-50 p-12">
      <div className="flex items-center gap-4 mb-8">
        <div className="p-4 bg-purple-600 rounded-2xl shadow-xl">
          <Sparkles size={32} className="text-white" />
        </div>
        <div>
          <h2 className="text-3xl font-black text-slate-900 uppercase tracking-tight">IA Lab Visualizador</h2>
          <p className="text-sm font-bold text-slate-400 uppercase tracking-wider">Análisis Inteligente de Planos & Renders</p>
        </div>
      </div>

      {!canUseAI && (
        <div className="mb-6 p-4 bg-orange-50 border border-orange-200 rounded-xl flex items-center gap-3">
          <AlertCircle size={20} className="text-orange-600" />
          <span className="text-xs font-black text-orange-800 uppercase">Módulo IA deshabilitado para tu usuario</span>
        </div>
      )}

      <div className="flex-1 grid grid-cols-2 gap-8">
        <div className="bg-white rounded-2xl p-8 shadow-xl border border-indigo-100 flex flex-col">
          <h3 className="text-sm font-black text-indigo-900 uppercase tracking-widest mb-4 flex items-center gap-2">
            <Upload size={16} className="text-purple-600" />
            Cargar Planos o Renders
          </h3>
          
          <label className="flex-1 border-4 border-dashed border-indigo-200 rounded-xl flex flex-col items-center justify-center cursor-pointer hover:border-purple-400 hover:bg-purple-50/50 transition-all group">
            <Upload size={48} className="text-indigo-300 group-hover:text-purple-600 transition-colors mb-4" />
            <p className="text-sm font-black text-indigo-900 uppercase">Click para subir imágenes</p>
            <p className="text-xs text-indigo-400 mt-2">JPG, PNG, PDF</p>
            <input 
              type="file" 
              multiple 
              accept="image/*" 
              onChange={handleImageUpload}
              className="hidden"
              disabled={!canUseAI}
            />
          </label>

          {images.length > 0 && (
            <div className="mt-4 grid grid-cols-3 gap-2">
              {images.map((img, idx) => (
                <div key={idx} className="aspect-square rounded-lg overflow-hidden border-2 border-indigo-100">
                  <img src={img} alt={`Upload ${idx}`} className="w-full h-full object-cover" />
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="bg-white rounded-2xl p-8 shadow-xl border border-purple-100">
          <h3 className="text-sm font-black text-indigo-900 uppercase tracking-widest mb-4 flex items-center gap-2">
            <Wand2 size={16} className="text-purple-600" />
            Análisis Automático
          </h3>
          
          <div className="space-y-4">
            <div className="p-6 bg-gradient-to-br from-purple-50 to-indigo-50 rounded-xl border border-purple-200">
              <p className="text-xs font-black text-purple-900 uppercase mb-2">Detección Automática</p>
              <p className="text-[10px] text-indigo-600 leading-relaxed">
                El sistema puede identificar muebles, medidas y distribución automáticamente usando Google Gemini AI.
              </p>
            </div>

            <button 
              onClick={mockAIAnalysis}
              disabled={!canUseAI || images.length === 0 || analyzing}
              className="w-full bg-gradient-to-r from-purple-600 to-indigo-600 text-white py-4 rounded-xl font-black uppercase text-xs tracking-widest shadow-xl hover:shadow-2xl transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {analyzing ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  Analizando...
                </>
              ) : (
                <>
                  <Sparkles size={18} />
                  Analizar con IA
                </>
              )}
            </button>

            <div className="p-4 bg-indigo-50 rounded-xl">
              <p className="text-[9px] font-black text-indigo-400 uppercase italic text-center">
                Requiere API Key de Google Gemini
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Visualizer;
