/**
 * AIRenderStudio - Componente de Render 3D con Voz + Texto
 * =========================================================
 * Permite al usuario describir una cocina por voz (micrófono) o texto,
 * y genera un render 3D fotorrealista usando el motor LuiggiAI.
 *
 * Características:
 * - Entrada por voz (Web Speech API) con indicador visual
 * - Entrada por texto libre
 * - Selector de materiales (formulario)
 * - Vista previa del render generado
 * - Historial de renders
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Mic, MicOff, Send, Image, Loader, Palette, RotateCcw, Download, Maximize2, X, Volume2, Wand2 } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// ─── Hook para Web Speech API ────────────────────────────────────────────────
function useSpeechRecognition() {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [isSupported, setIsSupported] = useState(false);
  const recognitionRef = useRef(null);
  // Acumulado SOLO de los resultados finales. El texto interino (en progreso)
  // NO se acumula: se muestra final + interino actual. Asi no se repite.
  const finalRef = useRef('');

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      setIsSupported(true);
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'es-ES';

      recognition.onresult = (event) => {
        let interimTranscript = '';
        // Recorrer SOLO los resultados nuevos desde resultIndex.
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const result = event.results[i];
          if (result.isFinal) {
            finalRef.current += result[0].transcript;  // los finales se acumulan UNA vez
          } else {
            interimTranscript += result[0].transcript;  // el interino es solo el actual
          }
        }
        // Mostrar lo confirmado + lo que se esta diciendo ahora (sin repetir).
        setTranscript(finalRef.current + interimTranscript);
      };

      recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = recognition;
    }
  }, []);

  const startListening = useCallback(() => {
    if (recognitionRef.current) {
      finalRef.current = '';
      setTranscript('');
      try { recognitionRef.current.start(); } catch (_) {}
      setIsListening(true);
    }
  }, []);

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      setIsListening(false);
    }
  }, []);

  const resetTranscript = useCallback(() => {
    finalRef.current = '';
    setTranscript('');
  }, []);

  return { isListening, transcript, isSupported, startListening, stopListening, resetTranscript, setTranscript };
}

// ─── Catálogo de materiales (sincronizado con backend) ───────────────────────
const MATERIALS = {
  layouts: [
    { id: 'L-shape', label: 'En L', icon: '⌐' },
    { id: 'U-shape', label: 'En U', icon: '⊔' },
    { id: 'island', label: 'Con Isla', icon: '◻' },
    { id: 'straight', label: 'Lineal', icon: '—' },
    { id: 'galley', label: 'Pasillo', icon: '‖' },
    { id: 'peninsula', label: 'Península', icon: '⊏' },
  ],
  countertops: [
    { id: 'marble_white', label: 'Mármol Blanco' },
    { id: 'marble_black', label: 'Mármol Negro' },
    { id: 'granite_black', label: 'Granito Negro' },
    { id: 'quartz_white', label: 'Cuarzo Blanco' },
    { id: 'quartz_calacatta', label: 'Cuarzo Calacatta' },
    { id: 'wood_walnut', label: 'Madera Nogal' },
    { id: 'wood_oak', label: 'Madera Roble' },
    { id: 'concrete', label: 'Hormigón' },
    { id: 'dekton', label: 'Dekton' },
    { id: 'stainless_steel', label: 'Acero Inoxidable' },
  ],
  cabinets: [
    { id: 'oak_natural', label: 'Roble Natural' },
    { id: 'oak_dark', label: 'Roble Oscuro' },
    { id: 'walnut', label: 'Nogal' },
    { id: 'white_matte', label: 'Blanco Mate' },
    { id: 'white_gloss', label: 'Blanco Brillo' },
    { id: 'grey_matte', label: 'Gris Mate' },
    { id: 'anthracite', label: 'Antracita' },
    { id: 'sage_green', label: 'Verde Sage' },
    { id: 'navy_blue', label: 'Azul Navy' },
    { id: 'black_matte', label: 'Negro Mate' },
  ],
  handles: [
    { id: 'none', label: 'Sin Tirador (Push)' },
    { id: 'integrated', label: 'Integrado (Gola)' },
    { id: 'bar_black', label: 'Barra Negro' },
    { id: 'bar_brass', label: 'Barra Latón' },
    { id: 'bar_chrome', label: 'Barra Cromado' },
    { id: 'knob_black', label: 'Pomo Negro' },
    { id: 'knob_brass', label: 'Pomo Latón' },
  ],
  floors: [
    { id: 'wood_oak', label: 'Roble' },
    { id: 'wood_walnut', label: 'Nogal Espiga' },
    { id: 'tile_white', label: 'Porcelánico Blanco' },
    { id: 'tile_grey', label: 'Porcelánico Gris' },
    { id: 'tile_terracotta', label: 'Terracota' },
    { id: 'marble_white', label: 'Mármol' },
    { id: 'concrete', label: 'Hormigón Pulido' },
  ],
  styles: [
    { id: 'photorealistic', label: 'Fotorrealista' },
    { id: 'architectural', label: 'Arquitectónico' },
    { id: 'magazine', label: 'Revista' },
    { id: 'minimalist', label: 'Minimalista' },
    { id: 'warm', label: 'Cálido' },
    { id: 'industrial', label: 'Industrial' },
  ],
};

// ─── Componente Principal ────────────────────────────────────────────────────
export default function AIRenderStudio({ state }) {
  const [mode, setMode] = useState('natural'); // 'natural' | 'params'
  const [description, setDescription] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [renderResult, setRenderResult] = useState(null);
  const [renderHistory, setRenderHistory] = useState([]);
  const [error, setError] = useState(null);
  const [showFullscreen, setShowFullscreen] = useState(false);
  const [params, setParams] = useState({
    layout: 'L-shape',
    countertop: 'quartz_white',
    cabinets: 'white_matte',
    handles: 'bar_black',
    floor: 'wood_oak',
    style: 'photorealistic',
    additional_details: '',
  });

  const { isListening, transcript, isSupported, startListening, stopListening, resetTranscript, setTranscript } = useSpeechRecognition();
  const textareaRef = useRef(null);

  // Sincronizar transcript de voz con el campo de descripción
  useEffect(() => {
    if (transcript) {
      setDescription(transcript);
    }
  }, [transcript]);

  const getAuthHeaders = () => {
    const token = localStorage.getItem('luiggi_access_token');
    return { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };
  };

  // ─── Generar render por descripción natural ─────────────────────────────
  const handleGenerateNatural = async () => {
    if (!description.trim()) return;
    setIsGenerating(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/api/ai-engine/render`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          description: description.trim(),
          style: params.style,
        }),
      });

      const data = await response.json();

      if (data.success) {
        setRenderResult(data);
        setRenderHistory(prev => [{ ...data, description, timestamp: new Date() }, ...prev].slice(0, 10));
      } else {
        setError(data.error || 'Error al generar el render');
      }
    } catch (err) {
      setError('Error de conexión. Verifique su conexión a internet.');
    } finally {
      setIsGenerating(false);
    }
  };

  // ─── Generar render por parámetros ──────────────────────────────────────
  const handleGenerateParams = async () => {
    setIsGenerating(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/api/ai-engine/render/params`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(params),
      });

      const data = await response.json();

      if (data.success) {
        setRenderResult(data);
        setRenderHistory(prev => [{ ...data, description: 'Parámetros manuales', timestamp: new Date() }, ...prev].slice(0, 10));
      } else {
        setError(data.error || 'Error al generar el render');
      }
    } catch (err) {
      setError('Error de conexión. Verifique su conexión a internet.');
    } finally {
      setIsGenerating(false);
    }
  };

  // ─── Toggle micrófono ───────────────────────────────────────────────────
  const toggleMic = () => {
    if (isListening) {
      stopListening();
    } else {
      resetTranscript();
      startListening();
    }
  };

  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-slate-50 to-slate-100 overflow-hidden">
      {/* Header */}
      <div className="shrink-0 px-8 py-5 bg-white border-b border-slate-200 shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl shadow-lg">
              <Wand2 size={20} className="text-white" />
            </div>
            <div>
              <h1 className="text-lg font-black text-slate-900 uppercase tracking-wide">Render 3D Studio</h1>
              <p className="text-xs text-slate-500 font-medium">Powered by LuiggiAI Engine</p>
            </div>
          </div>

          {/* Mode Toggle */}
          <div className="flex bg-slate-100 rounded-xl p-1">
            <button
              onClick={() => setMode('natural')}
              className={`px-4 py-2 rounded-lg text-xs font-bold uppercase tracking-wider transition-all ${
                mode === 'natural' ? 'bg-white shadow text-indigo-600' : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              <Volume2 size={14} className="inline mr-1.5" />
              Voz / Texto
            </button>
            <button
              onClick={() => setMode('params')}
              className={`px-4 py-2 rounded-lg text-xs font-bold uppercase tracking-wider transition-all ${
                mode === 'params' ? 'bg-white shadow text-indigo-600' : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              <Palette size={14} className="inline mr-1.5" />
              Materiales
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Panel izquierdo - Entrada */}
        <div className="w-[420px] shrink-0 border-r border-slate-200 bg-white flex flex-col overflow-y-auto">
          {mode === 'natural' ? (
            /* ─── Modo Voz/Texto ─── */
            <div className="flex-1 flex flex-col p-6 gap-5">
              <div className="text-center">
                <p className="text-sm text-slate-600 font-medium">
                  Describe la cocina que quieres. Puedes hablar o escribir.
                </p>
              </div>

              {/* Botón de micrófono grande */}
              <div className="flex justify-center">
                <button
                  onClick={toggleMic}
                  disabled={!isSupported}
                  className={`w-24 h-24 rounded-full flex items-center justify-center transition-all duration-300 shadow-xl ${
                    isListening
                      ? 'bg-red-500 text-white animate-pulse scale-110 shadow-red-300'
                      : isSupported
                        ? 'bg-gradient-to-br from-indigo-500 to-purple-600 text-white hover:scale-105 hover:shadow-2xl'
                        : 'bg-slate-200 text-slate-400 cursor-not-allowed'
                  }`}
                  title={isListening ? 'Detener grabación' : 'Iniciar grabación de voz'}
                >
                  {isListening ? <MicOff size={36} /> : <Mic size={36} />}
                </button>
              </div>

              {isListening && (
                <div className="text-center">
                  <span className="inline-flex items-center gap-2 px-4 py-2 bg-red-50 text-red-600 rounded-full text-xs font-bold uppercase tracking-wider">
                    <span className="w-2 h-2 bg-red-500 rounded-full animate-ping" />
                    Escuchando...
                  </span>
                </div>
              )}

              {!isSupported && (
                <p className="text-center text-xs text-amber-600 bg-amber-50 rounded-lg p-3">
                  Tu navegador no soporta reconocimiento de voz. Usa Chrome o Edge, o escribe tu descripción.
                </p>
              )}

              {/* Campo de texto */}
              <div className="flex-1 flex flex-col">
                <label className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">
                  Descripción de la cocina
                </label>
                <textarea
                  ref={textareaRef}
                  value={description}
                  onChange={(e) => { setDescription(e.target.value); setTranscript(e.target.value); }}
                  placeholder="Ej: Quiero una cocina en L con encimera de mármol blanco, muebles de roble natural, tiradores negros y suelo de madera..."
                  className="flex-1 min-h-[150px] p-4 border border-slate-200 rounded-xl text-sm text-slate-700 resize-none focus:outline-none focus:ring-2 focus:ring-indigo-300 focus:border-indigo-400 transition-all"
                />
              </div>

              {/* Selector de estilo rápido */}
              <div>
                <label className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 block">
                  Estilo de render
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {MATERIALS.styles.map(s => (
                    <button
                      key={s.id}
                      onClick={() => setParams(p => ({ ...p, style: s.id }))}
                      className={`px-3 py-2 rounded-lg text-xs font-bold transition-all ${
                        params.style === s.id
                          ? 'bg-indigo-100 text-indigo-700 ring-2 ring-indigo-300'
                          : 'bg-slate-50 text-slate-600 hover:bg-slate-100'
                      }`}
                    >
                      {s.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Botón generar */}
              <button
                onClick={handleGenerateNatural}
                disabled={!description.trim() || isGenerating}
                className="w-full py-4 bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-black uppercase tracking-wider rounded-xl shadow-lg hover:shadow-xl hover:scale-[1.02] transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 flex items-center justify-center gap-3"
              >
                {isGenerating ? (
                  <>
                    <Loader size={18} className="animate-spin" />
                    Generando render...
                  </>
                ) : (
                  <>
                    <Send size={18} />
                    Generar Render 3D
                  </>
                )}
              </button>
            </div>
          ) : (
            /* ─── Modo Parámetros/Materiales ─── */
            <div className="flex-1 flex flex-col p-6 gap-4 overflow-y-auto">
              {/* Layout */}
              <div>
                <label className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 block">Distribución</label>
                <div className="grid grid-cols-3 gap-2">
                  {MATERIALS.layouts.map(l => (
                    <button
                      key={l.id}
                      onClick={() => setParams(p => ({ ...p, layout: l.id }))}
                      className={`px-3 py-3 rounded-lg text-xs font-bold transition-all flex flex-col items-center gap-1 ${
                        params.layout === l.id
                          ? 'bg-indigo-100 text-indigo-700 ring-2 ring-indigo-300'
                          : 'bg-slate-50 text-slate-600 hover:bg-slate-100'
                      }`}
                    >
                      <span className="text-lg">{l.icon}</span>
                      {l.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Encimera */}
              <div>
                <label className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 block">Encimera</label>
                <select
                  value={params.countertop}
                  onChange={(e) => setParams(p => ({ ...p, countertop: e.target.value }))}
                  className="w-full p-3 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
                >
                  {MATERIALS.countertops.map(m => <option key={m.id} value={m.id}>{m.label}</option>)}
                </select>
              </div>

              {/* Muebles */}
              <div>
                <label className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 block">Muebles</label>
                <select
                  value={params.cabinets}
                  onChange={(e) => setParams(p => ({ ...p, cabinets: e.target.value }))}
                  className="w-full p-3 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
                >
                  {MATERIALS.cabinets.map(m => <option key={m.id} value={m.id}>{m.label}</option>)}
                </select>
              </div>

              {/* Tiradores */}
              <div>
                <label className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 block">Tiradores</label>
                <select
                  value={params.handles}
                  onChange={(e) => setParams(p => ({ ...p, handles: e.target.value }))}
                  className="w-full p-3 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
                >
                  {MATERIALS.handles.map(m => <option key={m.id} value={m.id}>{m.label}</option>)}
                </select>
              </div>

              {/* Suelo */}
              <div>
                <label className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 block">Suelo</label>
                <select
                  value={params.floor}
                  onChange={(e) => setParams(p => ({ ...p, floor: e.target.value }))}
                  className="w-full p-3 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
                >
                  {MATERIALS.floors.map(m => <option key={m.id} value={m.id}>{m.label}</option>)}
                </select>
              </div>

              {/* Estilo */}
              <div>
                <label className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 block">Estilo</label>
                <div className="grid grid-cols-3 gap-2">
                  {MATERIALS.styles.map(s => (
                    <button
                      key={s.id}
                      onClick={() => setParams(p => ({ ...p, style: s.id }))}
                      className={`px-3 py-2 rounded-lg text-xs font-bold transition-all ${
                        params.style === s.id
                          ? 'bg-indigo-100 text-indigo-700 ring-2 ring-indigo-300'
                          : 'bg-slate-50 text-slate-600 hover:bg-slate-100'
                      }`}
                    >
                      {s.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Detalles adicionales */}
              <div>
                <label className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 block">Detalles adicionales</label>
                <textarea
                  value={params.additional_details}
                  onChange={(e) => setParams(p => ({ ...p, additional_details: e.target.value }))}
                  placeholder="Ej: ventana grande con vistas, electrodomésticos integrados..."
                  className="w-full p-3 border border-slate-200 rounded-xl text-sm resize-none h-20 focus:outline-none focus:ring-2 focus:ring-indigo-300"
                />
              </div>

              {/* Botón generar */}
              <button
                onClick={handleGenerateParams}
                disabled={isGenerating}
                className="w-full py-4 bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-black uppercase tracking-wider rounded-xl shadow-lg hover:shadow-xl hover:scale-[1.02] transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-3 shrink-0"
              >
                {isGenerating ? (
                  <>
                    <Loader size={18} className="animate-spin" />
                    Generando render...
                  </>
                ) : (
                  <>
                    <Image size={18} />
                    Generar Render 3D
                  </>
                )}
              </button>
            </div>
          )}
        </div>

        {/* Panel derecho - Resultado */}
        <div className="flex-1 flex flex-col p-6 overflow-hidden">
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700 flex items-center gap-2">
              <span className="text-red-500 font-bold">Error:</span> {error}
              <button onClick={() => setError(null)} className="ml-auto text-red-400 hover:text-red-600">
                <X size={16} />
              </button>
            </div>
          )}

          {isGenerating ? (
            /* Estado de carga */
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <div className="relative w-32 h-32 mx-auto mb-6">
                  <div className="absolute inset-0 border-4 border-indigo-200 rounded-full animate-ping opacity-20" />
                  <div className="absolute inset-2 border-4 border-indigo-300 rounded-full animate-pulse opacity-40" />
                  <div className="absolute inset-4 border-4 border-t-indigo-600 border-r-transparent border-b-transparent border-l-transparent rounded-full animate-spin" />
                  <div className="absolute inset-0 flex items-center justify-center">
                    <Wand2 size={32} className="text-indigo-600" />
                  </div>
                </div>
                <p className="text-lg font-black text-slate-700 uppercase tracking-wider">Generando render</p>
                <p className="text-sm text-slate-500 mt-2">LuiggiAI está creando tu diseño 3D...</p>
                <p className="text-xs text-slate-400 mt-1">Esto puede tardar hasta 30 segundos</p>
              </div>
            </div>
          ) : renderResult ? (
            /* Resultado del render */
            <div className="flex-1 flex flex-col gap-4 overflow-hidden">
              <div className="flex items-center justify-between shrink-0">
                <h3 className="font-black text-slate-700 uppercase tracking-wider text-sm">Resultado</h3>
                <div className="flex gap-2">
                  <button
                    onClick={() => setShowFullscreen(true)}
                    className="p-2 bg-slate-100 rounded-lg hover:bg-slate-200 transition-colors"
                    title="Ver en pantalla completa"
                  >
                    <Maximize2 size={16} className="text-slate-600" />
                  </button>
                  <button
                    onClick={() => { setRenderResult(null); setDescription(''); }}
                    className="p-2 bg-slate-100 rounded-lg hover:bg-slate-200 transition-colors"
                    title="Nuevo render"
                  >
                    <RotateCcw size={16} className="text-slate-600" />
                  </button>
                </div>
              </div>

              {/* Imagen del render */}
              <div className="flex-1 bg-slate-900 rounded-2xl overflow-hidden shadow-2xl flex items-center justify-center relative">
                {renderResult?.result?.images?.[0] ? (
                  <img
                    src={renderResult.result.images[0]}
                    alt="Render 3D de cocina"
                    className="w-full h-full object-contain"
                  />
                ) : (
                  <div className="text-center p-8">
                    <Image size={48} className="text-slate-600 mx-auto mb-4" />
                    <p className="text-slate-400 text-sm">
                      {renderResult?.status === 'completed'
                        ? 'Render completado. La imagen se está procesando.'
                        : 'Render en proceso...'}
                    </p>
                    {renderResult?.prompt_used && (
                      <p className="text-slate-500 text-xs mt-4 max-w-md mx-auto italic">
                        "{renderResult.prompt_used.substring(0, 200)}..."
                      </p>
                    )}
                  </div>
                )}

                {/* Badge del motor */}
                <div className="absolute bottom-3 right-3 px-3 py-1.5 bg-black/60 backdrop-blur-sm rounded-lg">
                  <span className="text-[9px] font-black text-white/80 uppercase tracking-widest">
                    LuiggiAI Render Engine
                  </span>
                </div>
              </div>

              {/* Info del render */}
              {renderResult?.duration_seconds && (
                <div className="shrink-0 flex items-center gap-4 text-xs text-slate-500">
                  <span>Tiempo: {renderResult.duration_seconds}s</span>
                  {renderResult?.parsed_params?.layout && (
                    <span>Layout: {renderResult.parsed_params.layout}</span>
                  )}
                  <span className="ml-auto font-bold text-indigo-500">{renderResult.engine}</span>
                </div>
              )}
            </div>
          ) : (
            /* Estado vacío */
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center max-w-sm">
                <div className="w-20 h-20 mx-auto mb-6 bg-gradient-to-br from-indigo-100 to-purple-100 rounded-2xl flex items-center justify-center">
                  <Image size={36} className="text-indigo-500" />
                </div>
                <h3 className="font-black text-slate-700 uppercase tracking-wider mb-2">Render 3D Studio</h3>
                <p className="text-sm text-slate-500 leading-relaxed">
                  Describe tu cocina ideal usando voz o texto, o selecciona materiales manualmente.
                  LuiggiAI generará un render fotorrealista en segundos.
                </p>
              </div>
            </div>
          )}

          {/* Historial de renders */}
          {renderHistory.length > 0 && !isGenerating && (
            <div className="shrink-0 mt-4 border-t border-slate-200 pt-4">
              <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Historial reciente</h4>
              <div className="flex gap-3 overflow-x-auto pb-2">
                {renderHistory.map((item, i) => (
                  <button
                    key={i}
                    onClick={() => setRenderResult(item)}
                    className="shrink-0 w-16 h-16 bg-slate-200 rounded-xl overflow-hidden hover:ring-2 hover:ring-indigo-300 transition-all"
                    title={item.description}
                  >
                    {item?.result?.images?.[0] ? (
                      <img src={item.result.images[0]} alt="" className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-slate-400">
                        <Image size={16} />
                      </div>
                    )}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Fullscreen Modal */}
      {showFullscreen && renderResult?.result?.images?.[0] && (
        <div className="fixed inset-0 bg-black/95 z-[9999] flex items-center justify-center p-4" onClick={() => setShowFullscreen(false)}>
          <button className="absolute top-6 right-6 text-white/70 hover:text-white" onClick={() => setShowFullscreen(false)}>
            <X size={32} />
          </button>
          <img
            src={renderResult.result.images[0]}
            alt="Render 3D"
            className="max-w-full max-h-full object-contain rounded-xl shadow-2xl"
          />
        </div>
      )}
    </div>
  );
}
