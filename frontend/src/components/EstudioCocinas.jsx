/**
 * EstudioCocinas — Módulo Unificado de Diseño de Cocinas
 * ========================================================
 * Consolida en una sola interfaz por pestañas todas las capacidades
 * de diseño de cocinas del ERP:
 *
 *  Tab 1 · Proyectos       → KitchenDesigner3D (gestión completa de proyectos)
 *  Tab 2 · Render Studio   → AIRenderStudio (render por voz / texto / materiales)
 *  Tab 3 · Plano 2D        → Generación de plano técnico acotado (nuevo)
 *  Tab 4 · Presentación    → Ficha técnica + presentación HTML para cliente (nuevo)
 *
 * Los tabs 1 y 2 reutilizan los componentes existentes sin modificarlos.
 * Los tabs 3 y 4 son nuevos y llaman a /api/estudio-cocinas/*.
 */

import React, { useState, useRef, useCallback } from 'react';
import {
  LayoutDashboard, Wand2, Ruler, FileText,
  ChefHat, Upload, Download, Loader, Maximize2, X,
  RefreshCw, Mic, MicOff, CheckCircle, AlertCircle,
  Presentation, ClipboardList, Eye, Copy
} from 'lucide-react';
import { getToken } from '../services/api';

// Lazy-load de los componentes existentes para no romper nada
import KitchenDesigner3D from './KitchenDesigner3D';
import AIRenderStudio from './AIRenderStudio';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const authH = () => ({
  Authorization: `Bearer ${getToken()}`,
  'Content-Type': 'application/json',
});

// ─── Helpers ──────────────────────────────────────────────────────────────────

const readFileAsDataURL = (file) =>
  new Promise((res) => {
    const fr = new FileReader();
    fr.onload = () => res(String(fr.result));
    fr.onerror = () => res(null);
    fr.readAsDataURL(file);
  });

// ─── Tab 3: Plano 2D ──────────────────────────────────────────────────────────

function TabPlano2D() {
  const [form, setForm] = useState({
    nombre_cliente: '',
    estilo: 'Moderno',
    medidas: '',
    notas: '',
    presupuesto: '',
  });
  const [croquis, setCroquis] = useState(null); // dataURL
  const [planoB64, setPlanoB64] = useState(null);
  const [medidas_parseadas, setMedidasParseadas] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [fullscreen, setFullscreen] = useState(false);
  const fileRef = useRef();

  const ESTILOS = ['Moderno', 'Nórdico', 'Minimalista', 'Industrial', 'Clásico', 'Rústico'];

  const handleCroquis = async (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    const b64 = await readFileAsDataURL(f);
    setCroquis(b64);
  };

  const generar = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API_URL}/api/estudio-cocinas/plano-2d`, {
        method: 'POST',
        headers: authH(),
        body: JSON.stringify({ ...form, croquis_b64: croquis }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Error generando plano');
      setPlanoB64(data.planoBase64);
      setMedidasParseadas(data.medidas_parseadas);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const descargar = () => {
    if (!planoB64) return;
    const a = document.createElement('a');
    a.href = planoB64;
    a.download = `plano_${form.nombre_cliente || 'cocina'}_${Date.now()}.png`;
    a.click();
  };

  return (
    <div className="flex flex-col lg:flex-row gap-6 h-full">
      {/* Panel izquierdo: formulario */}
      <div className="lg:w-80 shrink-0 flex flex-col gap-4">
        <div className="bg-white rounded-2xl p-5 shadow-sm border border-slate-100">
          <h3 className="font-black text-slate-800 uppercase tracking-wider text-sm mb-4 flex items-center gap-2">
            <Ruler size={16} className="text-amber-500" /> Datos del Proyecto
          </h3>

          <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Cliente</label>
          <input
            className="w-full border border-slate-200 rounded-xl px-3 py-2 text-sm mb-3 focus:outline-none focus:ring-2 focus:ring-amber-300"
            placeholder="Nombre del cliente"
            value={form.nombre_cliente}
            onChange={e => setForm(f => ({ ...f, nombre_cliente: e.target.value }))}
          />

          <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Estilo</label>
          <select
            className="w-full border border-slate-200 rounded-xl px-3 py-2 text-sm mb-3 focus:outline-none focus:ring-2 focus:ring-amber-300"
            value={form.estilo}
            onChange={e => setForm(f => ({ ...f, estilo: e.target.value }))}
          >
            {ESTILOS.map(s => <option key={s}>{s}</option>)}
          </select>

          <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">
            Medidas <span className="text-slate-400 font-normal normal-case">(texto libre)</span>
          </label>
          <input
            className="w-full border border-slate-200 rounded-xl px-3 py-2 text-sm mb-1 focus:outline-none focus:ring-2 focus:ring-amber-300"
            placeholder='Ej: "4x3m isla 2x1m" o "400x300cm"'
            value={form.medidas}
            onChange={e => setForm(f => ({ ...f, medidas: e.target.value }))}
          />
          {medidas_parseadas && (
            <p className="text-[10px] text-slate-400 mb-3">
              Interpretado: {medidas_parseadas.ancho}×{medidas_parseadas.alto} cm · isla {medidas_parseadas.isla_w}×{medidas_parseadas.isla_h} cm
            </p>
          )}

          <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Notas</label>
          <textarea
            className="w-full border border-slate-200 rounded-xl px-3 py-2 text-sm mb-3 resize-none focus:outline-none focus:ring-2 focus:ring-amber-300"
            rows={2}
            placeholder="Notas adicionales..."
            value={form.notas}
            onChange={e => setForm(f => ({ ...f, notas: e.target.value }))}
          />

          {/* Croquis opcional */}
          <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">
            Croquis <span className="text-slate-400 font-normal normal-case">(opcional)</span>
          </label>
          <div
            className="border-2 border-dashed border-slate-200 rounded-xl p-3 text-center cursor-pointer hover:border-amber-300 transition-colors mb-4"
            onClick={() => fileRef.current?.click()}
          >
            {croquis ? (
              <img src={croquis} alt="croquis" className="w-full h-20 object-contain rounded-lg" />
            ) : (
              <div className="text-slate-400 text-xs">
                <Upload size={20} className="mx-auto mb-1" />
                Subir foto del croquis
              </div>
            )}
          </div>
          <input ref={fileRef} type="file" accept="image/*" className="hidden" onChange={handleCroquis} />

          <button
            onClick={generar}
            disabled={loading}
            className="w-full bg-gradient-to-r from-amber-500 to-orange-500 text-white font-black uppercase tracking-wider text-sm py-3 rounded-xl hover:opacity-90 transition-opacity disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {loading ? <><Loader size={16} className="animate-spin" /> Generando...</> : <><Ruler size={16} /> Generar Plano 2D</>}
          </button>

          {error && (
            <div className="mt-3 bg-red-50 text-red-600 text-xs rounded-xl p-3 flex items-start gap-2">
              <AlertCircle size={14} className="shrink-0 mt-0.5" /> {error}
            </div>
          )}
        </div>
      </div>

      {/* Panel derecho: resultado */}
      <div className="flex-1 bg-white rounded-2xl shadow-sm border border-slate-100 flex flex-col overflow-hidden">
        {planoB64 ? (
          <>
            <div className="flex items-center justify-between p-4 border-b border-slate-100">
              <span className="text-sm font-bold text-slate-700 flex items-center gap-2">
                <CheckCircle size={16} className="text-green-500" /> Plano generado
              </span>
              <div className="flex gap-2">
                <button onClick={descargar} className="text-xs bg-slate-100 hover:bg-slate-200 px-3 py-1.5 rounded-lg flex items-center gap-1 font-bold text-slate-600 transition-colors">
                  <Download size={13} /> Descargar PNG
                </button>
                <button onClick={() => setFullscreen(true)} className="text-xs bg-slate-100 hover:bg-slate-200 px-3 py-1.5 rounded-lg flex items-center gap-1 font-bold text-slate-600 transition-colors">
                  <Maximize2 size={13} /> Pantalla completa
                </button>
                <button onClick={generar} disabled={loading} className="text-xs bg-amber-100 hover:bg-amber-200 px-3 py-1.5 rounded-lg flex items-center gap-1 font-bold text-amber-700 transition-colors">
                  <RefreshCw size={13} /> Regenerar
                </button>
              </div>
            </div>
            <div className="flex-1 p-4 flex items-center justify-center bg-slate-50">
              <img src={planoB64} alt="Plano 2D" className="max-w-full max-h-full object-contain rounded-xl shadow-lg" />
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-center p-8">
            <div>
              <div className="w-20 h-20 mx-auto mb-6 bg-gradient-to-br from-amber-100 to-orange-100 rounded-2xl flex items-center justify-center">
                <Ruler size={36} className="text-amber-500" />
              </div>
              <h3 className="font-black text-slate-700 uppercase tracking-wider mb-2">Plano 2D Técnico</h3>
              <p className="text-sm text-slate-500 max-w-sm leading-relaxed">
                Introduce las medidas de la cocina y genera automáticamente un plano técnico acotado listo para presentar al cliente.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Fullscreen */}
      {fullscreen && planoB64 && (
        <div className="fixed inset-0 bg-black/95 z-[9999] flex items-center justify-center p-4" onClick={() => setFullscreen(false)}>
          <button className="absolute top-6 right-6 text-white/70 hover:text-white"><X size={32} /></button>
          <img src={planoB64} alt="Plano 2D" className="max-w-full max-h-full object-contain rounded-xl shadow-2xl" />
        </div>
      )}
    </div>
  );
}

// ─── Tab 4: Presentación / Ficha Técnica ─────────────────────────────────────

function TabPresentacion() {
  const [form, setForm] = useState({
    nombre_cliente: '',
    estilo: 'Moderno',
    medidas: '',
    descripcion: '',
    notas: '',
    presupuesto: '',
  });
  const [modo, setModo] = useState('presentacion'); // 'presentacion' | 'ficha'
  const [resultado, setResultado] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [copiado, setCopiado] = useState(false);

  const ESTILOS = ['Moderno', 'Nórdico', 'Minimalista', 'Industrial', 'Clásico', 'Rústico'];

  const generar = async () => {
    setLoading(true);
    setError('');
    setResultado(null);
    try {
      const endpoint = modo === 'presentacion' ? 'presentacion' : 'ficha-tecnica';
      const res = await fetch(`${API_URL}/api/estudio-cocinas/${endpoint}`, {
        method: 'POST',
        headers: authH(),
        body: JSON.stringify(form),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Error generando documento');
      setResultado(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const descargar = () => {
    if (!resultado) return;
    if (modo === 'presentacion') {
      const blob = new Blob([resultado.presentacionHtml], { type: 'text/html' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `propuesta_${form.nombre_cliente || 'cocina'}_${Date.now()}.html`;
      a.click();
      URL.revokeObjectURL(url);
    } else {
      const blob = new Blob([resultado.fichaMarkdown], { type: 'text/markdown' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `ficha_${form.nombre_cliente || 'cocina'}_${Date.now()}.md`;
      a.click();
      URL.revokeObjectURL(url);
    }
  };

  const copiar = () => {
    const texto = modo === 'presentacion' ? resultado?.presentacionHtml : resultado?.fichaMarkdown;
    if (!texto) return;
    navigator.clipboard.writeText(texto).then(() => {
      setCopiado(true);
      setTimeout(() => setCopiado(false), 2000);
    });
  };

  return (
    <div className="flex flex-col lg:flex-row gap-6 h-full">
      {/* Panel izquierdo */}
      <div className="lg:w-80 shrink-0 flex flex-col gap-4">
        <div className="bg-white rounded-2xl p-5 shadow-sm border border-slate-100">
          <h3 className="font-black text-slate-800 uppercase tracking-wider text-sm mb-4 flex items-center gap-2">
            <FileText size={16} className="text-indigo-500" /> Tipo de Documento
          </h3>

          <div className="flex gap-2 mb-4">
            {[
              { id: 'presentacion', label: 'Presentación', icon: Presentation },
              { id: 'ficha', label: 'Ficha Técnica', icon: ClipboardList },
            ].map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => { setModo(id); setResultado(null); }}
                className={`flex-1 flex flex-col items-center gap-1 p-3 rounded-xl text-xs font-bold uppercase tracking-wider transition-all ${
                  modo === id
                    ? 'bg-indigo-600 text-white shadow-lg scale-105'
                    : 'bg-slate-100 text-slate-500 hover:bg-slate-200'
                }`}
              >
                <Icon size={18} />
                {label}
              </button>
            ))}
          </div>

          <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Cliente</label>
          <input
            className="w-full border border-slate-200 rounded-xl px-3 py-2 text-sm mb-3 focus:outline-none focus:ring-2 focus:ring-indigo-300"
            placeholder="Nombre del cliente"
            value={form.nombre_cliente}
            onChange={e => setForm(f => ({ ...f, nombre_cliente: e.target.value }))}
          />

          <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Estilo</label>
          <select
            className="w-full border border-slate-200 rounded-xl px-3 py-2 text-sm mb-3 focus:outline-none focus:ring-2 focus:ring-indigo-300"
            value={form.estilo}
            onChange={e => setForm(f => ({ ...f, estilo: e.target.value }))}
          >
            {ESTILOS.map(s => <option key={s}>{s}</option>)}
          </select>

          <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Medidas</label>
          <input
            className="w-full border border-slate-200 rounded-xl px-3 py-2 text-sm mb-3 focus:outline-none focus:ring-2 focus:ring-indigo-300"
            placeholder='Ej: "4x3m isla 2x1m"'
            value={form.medidas}
            onChange={e => setForm(f => ({ ...f, medidas: e.target.value }))}
          />

          <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Descripción</label>
          <textarea
            className="w-full border border-slate-200 rounded-xl px-3 py-2 text-sm mb-3 resize-none focus:outline-none focus:ring-2 focus:ring-indigo-300"
            rows={2}
            placeholder="Descripción del proyecto..."
            value={form.descripcion}
            onChange={e => setForm(f => ({ ...f, descripcion: e.target.value }))}
          />

          <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Presupuesto</label>
          <input
            className="w-full border border-slate-200 rounded-xl px-3 py-2 text-sm mb-4 focus:outline-none focus:ring-2 focus:ring-indigo-300"
            placeholder='Ej: "15.000 – 20.000 €"'
            value={form.presupuesto}
            onChange={e => setForm(f => ({ ...f, presupuesto: e.target.value }))}
          />

          <button
            onClick={generar}
            disabled={loading}
            className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-black uppercase tracking-wider text-sm py-3 rounded-xl hover:opacity-90 transition-opacity disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {loading
              ? <><Loader size={16} className="animate-spin" /> Generando...</>
              : <><FileText size={16} /> Generar {modo === 'presentacion' ? 'Presentación' : 'Ficha'}</>
            }
          </button>

          {error && (
            <div className="mt-3 bg-red-50 text-red-600 text-xs rounded-xl p-3 flex items-start gap-2">
              <AlertCircle size={14} className="shrink-0 mt-0.5" /> {error}
            </div>
          )}
        </div>
      </div>

      {/* Panel derecho: preview */}
      <div className="flex-1 bg-white rounded-2xl shadow-sm border border-slate-100 flex flex-col overflow-hidden">
        {resultado ? (
          <>
            <div className="flex items-center justify-between p-4 border-b border-slate-100 shrink-0">
              <span className="text-sm font-bold text-slate-700 flex items-center gap-2">
                <CheckCircle size={16} className="text-green-500" />
                {modo === 'presentacion' ? `Presentación — ${resultado.cliente}` : `Ficha Técnica — ${resultado.referencia}`}
              </span>
              <div className="flex gap-2">
                <button onClick={copiar} className="text-xs bg-slate-100 hover:bg-slate-200 px-3 py-1.5 rounded-lg flex items-center gap-1 font-bold text-slate-600 transition-colors">
                  {copiado ? <><CheckCircle size={13} className="text-green-500" /> Copiado</> : <><Copy size={13} /> Copiar</>}
                </button>
                <button onClick={descargar} className="text-xs bg-indigo-100 hover:bg-indigo-200 px-3 py-1.5 rounded-lg flex items-center gap-1 font-bold text-indigo-700 transition-colors">
                  <Download size={13} /> Descargar
                </button>
                <button onClick={generar} disabled={loading} className="text-xs bg-slate-100 hover:bg-slate-200 px-3 py-1.5 rounded-lg flex items-center gap-1 font-bold text-slate-600 transition-colors">
                  <RefreshCw size={13} /> Regenerar
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-auto">
              {modo === 'presentacion' ? (
                <iframe
                  srcDoc={resultado.presentacionHtml}
                  title="Presentación cliente"
                  className="w-full h-full border-0"
                  sandbox="allow-same-origin"
                />
              ) : (
                <pre className="p-6 text-xs text-slate-700 font-mono leading-relaxed whitespace-pre-wrap overflow-auto">
                  {resultado.fichaMarkdown}
                </pre>
              )}
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-center p-8">
            <div>
              <div className="w-20 h-20 mx-auto mb-6 bg-gradient-to-br from-indigo-100 to-purple-100 rounded-2xl flex items-center justify-center">
                <FileText size={36} className="text-indigo-500" />
              </div>
              <h3 className="font-black text-slate-700 uppercase tracking-wider mb-2">
                {modo === 'presentacion' ? 'Presentación para Cliente' : 'Ficha Técnica'}
              </h3>
              <p className="text-sm text-slate-500 max-w-sm leading-relaxed">
                {modo === 'presentacion'
                  ? 'Genera una presentación HTML profesional lista para enviar o mostrar al cliente en pantalla.'
                  : 'Genera una ficha técnica completa con materiales, electrodomésticos, plazos y presupuesto.'
                }
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Componente Principal ─────────────────────────────────────────────────────

const TABS = [
  { id: 'proyectos',    label: 'Proyectos 3D',   icon: LayoutDashboard, color: 'emerald' },
  { id: 'render',       label: 'Render Studio',   icon: Wand2,           color: 'purple'  },
  { id: 'plano',        label: 'Plano 2D',        icon: Ruler,           color: 'amber'   },
  { id: 'presentacion', label: 'Presentación',    icon: FileText,        color: 'indigo'  },
];

const COLOR_MAP = {
  emerald: { active: 'bg-emerald-600 text-white shadow-xl scale-105', icon: 'text-emerald-500' },
  purple:  { active: 'bg-purple-600 text-white shadow-xl scale-105',  icon: 'text-purple-500'  },
  amber:   { active: 'bg-amber-500 text-white shadow-xl scale-105',   icon: 'text-amber-500'   },
  indigo:  { active: 'bg-indigo-600 text-white shadow-xl scale-105',  icon: 'text-indigo-500'  },
};

export default function EstudioCocinas({ state }) {
  const [activeTab, setActiveTab] = useState('proyectos');

  return (
    <div className="h-full flex flex-col bg-slate-50 overflow-hidden">
      {/* Header */}
      <div className="shrink-0 bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 text-white px-4 sm:px-6 py-3 flex items-center gap-3 flex-wrap shadow-lg">
        <ChefHat size={20} className="text-amber-400 shrink-0" />
        <div>
          <h1 className="text-sm font-black uppercase tracking-widest leading-none">Estudio de Cocinas</h1>
          <p className="text-[9px] text-slate-400 uppercase tracking-widest mt-0.5">Diseño · Render · Planos · Presentaciones</p>
        </div>
        <div className="ml-auto flex items-center gap-2 flex-wrap">
          {TABS.map(({ id, label, icon: Icon, color }) => {
            const isActive = activeTab === id;
            const colors = COLOR_MAP[color];
            return (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-[10px] font-black uppercase tracking-wider transition-all duration-200 ${
                  isActive ? colors.active : 'text-slate-400 hover:text-white hover:bg-white/10'
                }`}
              >
                <Icon size={13} className={isActive ? '' : colors.icon} />
                <span className="hidden sm:inline">{label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Contenido */}
      <div className="flex-1 overflow-auto p-4 sm:p-6">
        {activeTab === 'proyectos' && (
          <KitchenDesigner3D state={state} />
        )}
        {activeTab === 'render' && (
          <AIRenderStudio state={state} />
        )}
        {activeTab === 'plano' && (
          <TabPlano2D />
        )}
        {activeTab === 'presentacion' && (
          <TabPresentacion />
        )}
      </div>
    </div>
  );
}
