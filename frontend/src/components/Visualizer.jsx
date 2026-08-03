import React, { useState, useRef, useEffect } from 'react';
import { Sparkles, Upload, Wand2, AlertCircle, Loader2, Package, Check, Plus, X, FileImage, RefreshCw, Layers } from 'lucide-react';
import { getProductIcon } from './FurnitureIcons';
import { getToken } from '../services/api';
import DOMPurify from 'dompurify';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Sanitize HTML to prevent XSS attacks
const sanitizeHTML = (html) => DOMPurify.sanitize(html, { USE_PROFILES: { html: true } });

// Una cota que no se conoce se deja en blanco, NUNCA con un número plausible:
// un ancho inventado acaba en un mueble mal pedido en fábrica.
const cota = (mm) => {
  const v = Number(mm);
  return Number.isFinite(v) && v > 0 ? Math.round(v) : '?';
};

const Visualizer = ({ images, state, setState, onAddToBudget }) => {
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [error, setError] = useState(null);
  const [selectedImages, setSelectedImages] = useState([]);  // Array de imágenes
  const [dumpChoice, setDumpChoice] = useState(null);  // { productos, opts } pendientes de elegir presupuestador
  const [dumpTarget, setDumpTarget] = useState(null);  // elección recordada en la sesión: 'p1' | 'p2'
  const fileInputRef = useRef(null);
  const [autoRun, setAutoRun] = useState(false); // analizar automáticamente un render entrante

  const canUseAI = state.currentUser?.canUseAIAnalysis || state.currentUser?.isAdmin || state.currentUser?.isGerente;

  // Render entrante desde Estudio 3D ("Al presupuesto"): lo cargamos y analizamos
  // automáticamente para volcar los muebles al presupuesto.
  useEffect(() => {
    const dataUrl = state?.analyzeRender;
    if (!dataUrl) return;
    if (setState) setState(p => { const { analyzeRender, ...rest } = p; return rest; });
    fetch(dataUrl).then(r => r.blob()).then(blob => {
      const file = new File([blob], 'render.png', { type: blob.type || 'image/png' });
      setSelectedImages([{ dataUrl, file, name: 'render.png' }]);
      setAnalysisResult(null); setError(null); setAutoRun(true);
    }).catch(() => setError('No se pudo cargar el render para analizar.'));
  }, [state?.analyzeRender]);

  // Cuando el render entrante ya está cargado, dispara el análisis una vez.
  useEffect(() => {
    if (autoRun && selectedImages.length > 0) { setAutoRun(false); analyzeKitchenPlan(); }
  }, [autoRun, selectedImages]);

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
    
    // Obtener la biblioteca activa del estado
    const activeLibrary = state?.currentLibrary || 'ZC';

    try {
      const formData = new FormData();
      
      // Agregar la biblioteca activa al FormData
      formData.append('library', activeLibrary);
      
      // Si es una sola imagen, usar el endpoint simple
      if (selectedImages.length === 1) {
        formData.append('file', selectedImages[0].file);
        
        const response = await fetch(`${API_URL}/api/ia-lab/analyze-kitchen-plan`, {
          method: 'POST',
          headers: { Authorization: `Bearer ${getToken()}` },
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
          headers: { Authorization: `Bearer ${getToken()}` },
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

  // Push de bajo nivel a P1 (Presupuestador 2 / ZC, budgetItemsMontada). Sin routing.
  const pushToP1 = (furniture) => {
    if (!onAddToBudget) return;
    onAddToBudget({
      ...furniture,
      code: furniture.codigo_catalogo || furniture.codigo_sugerido,
      name: furniture.nombre_catalogo,
      points: furniture.puntos,
      price: furniture.precio_pvp,
      width: furniture.ancho_real || furniture.ancho_estimado,
      height: furniture.alto_real || furniture.alto_estimado * 10,
      depth: furniture.fondo_real || furniture.fondo_estimado * 10,
      category: furniture.categoria,
      programa: furniture.programa,
      productId: furniture.product_id,
      cantidad: furniture.cantidad || 1,
      qty: furniture.cantidad || 1
    }, false);
  };

  // Vuelca la lista al presupuestador elegido. Recuerda la elección (dumpTarget)
  // para no volver a preguntar. opts.navigate: ir a la pestaña; opts.notify: avisar.
  const doDump = (productos, target, opts = {}) => {
    const { navigate = true, notify = true } = opts;
    if (target === 'p2') {
      const lines = productos.map(f => ({
        code: f.codigo_catalogo || f.codigo_sugerido || 'MV',
        name: f.nombre_catalogo || `${f.tipo || ''} ${f.subtipo || ''}`.trim() || 'Mueble',
        price: Number(f.precio_pvp) || 0,
        qty: Number(f.cantidad) || 1,
        width: f.ancho_real || f.ancho_estimado,
        height: f.alto_real || f.alto_estimado,
        depth: f.fondo_real || f.fondo_estimado,
      }));
      setState(p => ({
        ...p,
        p2PendingLines: [...(p.p2PendingLines || []), ...lines],  // acumula (no pisa)
        ...(navigate ? { currentTab: 'presupuestador2' } : {}),
      }));
    } else {
      productos.forEach(pushToP1);
      if (navigate) setState(p => ({ ...p, currentTab: 'budget' }));
    }
    setDumpTarget(target);
    setDumpChoice(null);
    if (notify) {
      const totalUnidades = productos.reduce((sum, f) => sum + (Number(f.cantidad) || 1), 0);
      const totalPvp = productos.reduce((sum, f) => sum + (f.precio_pvp || 0) * (Number(f.cantidad) || 1), 0);
      alert(`✅ ${totalUnidades} producto(s) añadido(s) al ${target === 'p2' ? 'Presupuestador (principal)' : 'Presupuestador 2'}.\n\nTotal: ${totalPvp.toLocaleString('es-ES')}€`);
    }
  };

  // Decide a qué presupuestador volcar: el recordado, el único activo, o pregunta.
  const resolveAndDump = (productos, opts = {}) => {
    const canP1 = state?.currentUser?.canUsePresupuestador1 !== false; // Presupuestador 2 (ZC)
    const canP2 = state?.currentUser?.canUsePresupuestador2 !== false; // Presupuestador principal (MV)
    if (!canP1 && !canP2) {
      alert('No tienes ningún presupuestador activo para volcar los muebles.');
      return;
    }
    if (dumpTarget && ((dumpTarget === 'p1' && canP1) || (dumpTarget === 'p2' && canP2))) {
      doDump(productos, dumpTarget, opts);
      return;
    }
    if (canP1 && canP2) {
      setDumpChoice({ productos, opts });  // abre el diálogo de elección
      return;
    }
    doDump(productos, canP2 ? 'p2' : 'p1', opts);
  };

  // Añadir UN mueble (botón ✓ de cada fila): silencioso, sin cambiar de pestaña.
  const addFurnitureToBudget = (furniture) => {
    if (!furniture.producto_encontrado) {
      alert('⚠️ Este producto no se encontró en el catálogo. No se puede añadir al presupuesto.');
      return;
    }
    resolveAndDump([furniture], { navigate: false, notify: false });
  };

  // Añadir TODOS los detectados del catálogo (botón inferior).
  const addAllFurnitureToBudget = () => {
    if (!analysisResult?.muebles_detectados?.length) return;
    const productosEncontrados = analysisResult.muebles_detectados.filter(f => f.producto_encontrado);
    if (productosEncontrados.length === 0) {
      alert('⚠️ No hay productos del catálogo para añadir.\n\nRevisa manualmente los productos no encontrados.');
      return;
    }
    resolveAndDump(productosEncontrados, { navigate: true, notify: true });
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
            <p className="text-sm font-bold text-slate-400 uppercase tracking-wider">Detecta muebles automáticamente con IA</p>
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
            {/* Catálogo: selector ZC/MV si el usuario tiene ambas activas; si no, indicador */}
            {(() => {
              const allowed = state?.allowedLibraries || [];
              const hasBoth = allowed.includes('ZC') && allowed.includes('MV');
              const current = state?.currentLibrary || allowed[0] || 'ZC';
              if (hasBoth) {
                return (
                  <span className="ml-auto flex items-center gap-1 bg-slate-100 rounded-full p-0.5" title="Catálogo con el que se leerán los muebles del plano">
                    <span className="text-[9px] font-black text-slate-400 uppercase pl-2">Catálogo</span>
                    {['ZC', 'MV'].map(lib => (
                      <button key={lib} type="button" onClick={() => setState(p => ({ ...p, currentLibrary: lib }))}
                        className={`px-2.5 py-0.5 rounded-full text-xs font-black transition-colors ${
                          current === lib
                            ? (lib === 'MV' ? 'bg-emerald-600 text-white' : 'bg-blue-600 text-white')
                            : 'text-slate-500 hover:bg-white'}`}>
                        {lib}
                      </button>
                    ))}
                  </span>
                );
              }
              return (
                <span className={`ml-auto px-2 py-0.5 rounded-full text-xs font-black ${
                  current === 'MV' ? 'bg-emerald-100 text-emerald-700' : 'bg-blue-100 text-blue-700'
                }`}>
                  Catálogo: {current}
                </span>
              );
            })()}
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
          <h3 className="text-sm font-black text-indigo-900 uppercase tracking-widest mb-4 flex items-center gap-2 shrink-0">
            <Package size={16} className="text-purple-600" />
            Muebles Detectados
          </h3>

          {!analysisResult ? (
            <div className="flex-1 flex flex-col items-center justify-center text-slate-400">
              <Package size={64} className="opacity-30 mb-4" />
              <p className="font-bold text-sm">Sube un plano y analízalo</p>
              <p className="text-xs mt-1">La IA detectará los muebles automáticamente</p>
            </div>
          ) : analysisResult.error ? (
            <div className="flex-1 flex flex-col items-center justify-center text-slate-400 p-6">
              <AlertCircle size={64} className="text-orange-400 mb-4" />
              <p className="font-bold text-sm text-orange-600 text-center">La IA no pudo analizar esta imagen</p>
              <p className="text-xs text-slate-500 mt-2 text-center max-w-md">{analysisResult.raw_response || analysisResult.error}</p>
              <p className="text-xs text-slate-400 mt-4 text-center">Sube una imagen de un plano de cocina real para obtener mejores resultados</p>
            </div>
          ) : (
            <>
              {/* Summary Stats - Fixed at top */}
              {analysisResult.resumen && (
                <div className="mb-3 shrink-0">
                  {analysisResult.resumen.paredes_analizadas > 1 && (
                    <div className="mb-2 px-3 py-2 bg-purple-100 rounded-lg text-center">
                      <span className="text-xs font-black text-purple-700 uppercase">
                        {analysisResult.resumen.paredes_analizadas} paredes analizadas
                      </span>
                    </div>
                  )}
                  <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
                    <div className="bg-indigo-50 rounded-lg p-2 text-center">
                      <p className="text-xl font-black text-indigo-600">{analysisResult.resumen.total_altos || 0}</p>
                      <p className="text-[10px] font-bold text-indigo-400 uppercase">Altos</p>
                    </div>
                    <div className="bg-emerald-50 rounded-lg p-2 text-center">
                      <p className="text-xl font-black text-emerald-600">{analysisResult.resumen.total_bajos || 0}</p>
                      <p className="text-[10px] font-bold text-emerald-400 uppercase">Bajos</p>
                    </div>
                    <div className="bg-orange-50 rounded-lg p-2 text-center">
                      <p className="text-xl font-black text-orange-600">{analysisResult.resumen.total_columnas || 0}</p>
                      <p className="text-[10px] font-bold text-orange-400 uppercase">Columnas</p>
                    </div>
                    <div className="bg-purple-50 rounded-lg p-2 text-center">
                      <p className="text-xl font-black text-purple-600">{(analysisResult.muebles_detectados || []).reduce((s, m) => s + (Number(m.cantidad) || 1), 0)}</p>
                      <p className="text-[10px] font-bold text-purple-400 uppercase">Total</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Furniture List - Scrollable middle section */}
              <div className="flex-1 overflow-y-auto space-y-2 min-h-0 mb-3">
                {(!analysisResult.muebles_detectados || analysisResult.muebles_detectados.length === 0) ? (
                  <div className="flex flex-col items-center justify-center h-full text-slate-400 p-6">
                    <Package size={48} className="opacity-30 mb-3" />
                    <p className="font-bold text-sm text-center">No se detectaron muebles</p>
                    <p className="text-xs mt-1 text-center">Prueba con otra imagen de plano de cocina</p>
                  </div>
                ) : (
                  analysisResult.muebles_detectados.map((furniture, idx) => (
                  <div 
                    key={idx}
                    className={`border rounded-xl p-3 hover:border-purple-400 hover:bg-purple-50/50 transition-all group ${
                      furniture.producto_encontrado ? 'border-emerald-200 bg-emerald-50/30' : 'border-orange-200 bg-orange-50/30'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div 
                        className={`w-10 h-10 flex items-center justify-center rounded-lg ${
                          furniture.producto_encontrado ? 'text-emerald-600 bg-emerald-100' : 'text-orange-600 bg-orange-100'
                        }`}
                        dangerouslySetInnerHTML={{ __html: sanitizeHTML(getProductIcon(furniture.codigo_catalogo || furniture.codigo_sugerido, furniture.subtipo)) }}
                      />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-black text-indigo-900 text-sm">{furniture.codigo_catalogo || furniture.codigo_sugerido}</span>
                          {(Number(furniture.cantidad) || 1) > 1 && (
                            <span className="text-[11px] px-2 py-0.5 rounded-full font-black bg-indigo-600 text-white">
                              ×{furniture.cantidad}
                            </span>
                          )}
                          {furniture.pared && (
                            <span className="text-[10px] px-2 py-0.5 rounded-full font-bold bg-slate-100 text-slate-600">
                              P{furniture.pared}
                            </span>
                          )}
                          {furniture.producto_encontrado ? (
                            <span className="text-[10px] px-2 py-0.5 rounded-full font-bold bg-emerald-100 text-emerald-700">
                              ✓ CATÁLOGO
                            </span>
                          ) : (
                            <span className="text-[10px] px-2 py-0.5 rounded-full font-bold bg-orange-100 text-orange-700">
                              ⚠ NO ENCONTRADO
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-slate-600 font-medium truncate">
                          {furniture.nombre_catalogo || `${furniture.tipo} ${furniture.subtipo?.replace(/_/g, ' ')}`}
                        </p>
                        <p className="text-[10px] text-slate-400">
                          {/* Ancho × alto × fondo, TODO en mm. Antes se dividía
                              entre 10 lo que ya venía en cm y salían cotas
                              imposibles: "600×7×3.3 mm". Lo que no se sabe se
                              deja en «?», nunca con un número inventado. */}
                          {cota(furniture.ancho_real ?? furniture.ancho_estimado)}×
                          {cota(furniture.alto_real ?? (furniture.alto_estimado ? furniture.alto_estimado * 10 : null))}×
                          {cota(furniture.fondo_real ?? (furniture.fondo_estimado ? furniture.fondo_estimado * 10 : null))} mm
                          {furniture.categoria && ` • ${furniture.categoria}`}
                        </p>
                      </div>
                      <div className="text-right shrink-0">
                        {furniture.precio_pvp > 0 ? (
                          <>
                            <p className="font-black text-emerald-600 text-lg">
                              {((Number(furniture.precio_pvp) || 0) * (Number(furniture.cantidad) || 1)).toLocaleString('es-ES')}€
                            </p>
                            {(Number(furniture.cantidad) || 1) > 1 && (
                              <p className="text-[10px] text-slate-400">{furniture.precio_pvp}€/ud</p>
                            )}
                          </>
                        ) : (
                          <p className="font-bold text-orange-500 text-sm">Sin precio</p>
                        )}
                      </div>
                      <button
                        onClick={() => addFurnitureToBudget(furniture)}
                        disabled={!furniture.producto_encontrado}
                        className={`p-2 rounded-lg transition-opacity ${
                          furniture.producto_encontrado 
                            ? 'bg-emerald-500 text-white opacity-0 group-hover:opacity-100' 
                            : 'bg-slate-300 text-slate-500 cursor-not-allowed opacity-50'
                        }`}
                        title={furniture.producto_encontrado ? "Añadir al presupuesto" : "Producto no disponible en catálogo"}
                      >
                        <Plus size={16} />
                      </button>
                    </div>
                  </div>
                  ))
                )}
              </div>

              {/* Fixed Bottom Section - Price Summary, Observations, Add Button */}
              <div className="shrink-0 space-y-2 border-t border-slate-200 pt-3">
                {/* Price Summary */}
                {(() => {
                  const rp = analysisResult.resumen_precios || analysisResult.resumen?.resumen_precios;
                  if (!rp) return null;
                  // Total en EUROS del backend (Σ precio_pvp × cantidad): es el mismo que el
                  // precio por línea y el que se vuelca al presupuesto. Antes se recalculaba
                  // como puntos × valor-de-punto-del-frontend y daba un total incoherente.
                  const lib = (analysisResult.library || 'ZC').toUpperCase();
                  const pointValue = (state?.libraryPointValues?.[lib])
                    ?? (state?.currentModule === 'despiece' ? state?.pointValueDespiece : state?.pointValueMontada)
                    ?? 1;
                  const estimado = Math.round(Number(rp.total_pvp ?? ((rp.total_puntos ?? 0) * pointValue)));
                  return (
                  <div className="p-3 bg-gradient-to-r from-emerald-50 to-teal-50 border border-emerald-200 rounded-xl">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-bold text-emerald-800">{rp.mensaje}</p>
                        {(rp.productos_no_encontrados > 0) && (
                          <p className="text-xs text-orange-600 mt-1">
                            ⚠ {rp.productos_no_encontrados} mueble(s) requieren revisión manual
                          </p>
                        )}
                        {(rp.electrodomesticos > 0) && (
                          <p className="text-xs text-slate-500 mt-1">
                            🔌 {rp.electrodomesticos} electrodoméstico(s) detectados (no son muebles del catálogo)
                          </p>
                        )}
                      </div>
                      <div className="text-right">
                        <p className="text-[10px] text-emerald-600 uppercase font-bold">Total Estimado</p>
                        <p className="text-xl font-black text-emerald-700">
                          {estimado.toLocaleString('es-ES')}€
                        </p>
                      </div>
                    </div>
                  </div>
                  );
                })()}

                {/* Observations */}
                {analysisResult.observaciones && (
                  <div className="p-2 bg-amber-50 border border-amber-200 rounded-lg">
                    <p className="text-xs font-bold text-amber-800">💡 {analysisResult.observaciones}</p>
                  </div>
                )}

                {/* Add All Button */}
                {analysisResult.muebles_detectados?.length > 0 && ((analysisResult.resumen_precios || analysisResult.resumen?.resumen_precios)?.productos_encontrados > 0) && (() => {
                  const rp = analysisResult.resumen_precios || analysisResult.resumen?.resumen_precios;
                  const lib = (analysisResult.library || 'ZC').toUpperCase();
                  const pointValue = (state?.libraryPointValues?.[lib])
                    ?? (state?.currentModule === 'despiece' ? state?.pointValueDespiece : state?.pointValueMontada)
                    ?? 1;
                  const estimado = Math.round(Number(rp.total_pvp ?? ((rp.total_puntos ?? 0) * pointValue)));
                  return (
                  <button
                    onClick={addAllFurnitureToBudget}
                    data-testid="add-all-to-budget-btn"
                    className="w-full py-3 bg-emerald-600 text-white rounded-xl font-black uppercase text-sm flex items-center justify-center gap-2 hover:bg-emerald-700 transition-colors shadow-lg"
                  >
                    <Plus size={18} />
                    + AÑADIR {rp.productos_encontrados} PRODUCTOS AL PRESUPUESTO ({estimado.toLocaleString('es-ES')}€)
                  </button>
                  );
                })()}
              </div>
            </>
          )}
        </div>
      </div>

      {/* Diálogo: elegir presupuestador cuando el usuario tiene los dos activos */}
      {dumpChoice && (
        <div className="fixed inset-0 z-[80] bg-black/50 flex items-center justify-center p-4" onClick={() => setDumpChoice(null)}>
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6" onClick={e => e.stopPropagation()}>
            <h3 className="text-lg font-black text-slate-900 mb-1">¿A qué presupuestador?</h3>
            <p className="text-sm text-slate-500 mb-4">Tienes los dos activos. Elige dónde volcar los {dumpChoice.productos.reduce((s, f) => s + (Number(f.cantidad) || 1), 0)} muebles detectados.</p>
            <div className="grid grid-cols-1 gap-2">
              <button onClick={() => doDump(dumpChoice.productos, 'p2', dumpChoice.opts)}
                className="w-full px-4 py-3 rounded-xl bg-orange-600 text-white font-black uppercase text-sm hover:bg-orange-700 transition-colors">
                Presupuestador (principal · MV)
              </button>
              <button onClick={() => doDump(dumpChoice.productos, 'p1', dumpChoice.opts)}
                className="w-full px-4 py-3 rounded-xl bg-indigo-600 text-white font-black uppercase text-sm hover:bg-indigo-700 transition-colors">
                Presupuestador 2 (ZC)
              </button>
              <button onClick={() => setDumpChoice(null)}
                className="w-full px-4 py-2 rounded-xl bg-slate-100 text-slate-600 font-bold text-sm hover:bg-slate-200 transition-colors">
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Visualizer;
