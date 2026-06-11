/**
 * KitchenDesigner3D - Panel de Diseño de Cocinas con Proyectos
 * ==============================================================
 * Componente completo para gestionar proyectos de cocinas 3D con:
 * - Gestión de proyectos (crear, listar, eliminar)
 * - Formulario de diseño con selección de materiales
 * - Subida de fotos de referencia
 * - Generación de renders con IA
 * - Iteración rápida (cambiar material sin empezar de cero)
 * - Historial de renders con comparativa antes/después
 * - Descarga de imágenes generadas
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  FolderOpen, Plus, Image, Loader, Download, Maximize2, X,
  Wand2, ArrowLeft, Trash2, RefreshCw, Layers, Palette, CheckCircle
} from 'lucide-react';
import { getToken } from '../services/api';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// ─── Catálogos de materiales ─────────────────────────────────────────────────
const LAYOUTS = [
  { id: 'L-shape', label: 'En L' },
  { id: 'U-shape', label: 'En U' },
  { id: 'straight', label: 'Lineal' },
  { id: 'island', label: 'Con Isla' },
  { id: 'galley', label: 'Pasillo' },
  { id: 'peninsula', label: 'Península' },
];

const CABINET_MATERIALS = [
  { id: 'white_matte', label: 'Blanco mate lacado' },
  { id: 'white_gloss', label: 'Blanco brillo lacado' },
  { id: 'oak_natural', label: 'Roble natural' },
  { id: 'oak_dark', label: 'Roble oscuro' },
  { id: 'walnut', label: 'Nogal' },
  { id: 'grey_matte', label: 'Gris mate' },
  { id: 'anthracite', label: 'Antracita' },
  { id: 'sage_green', label: 'Verde salvia' },
  { id: 'navy_blue', label: 'Azul marino' },
  { id: 'black_matte', label: 'Negro mate' },
];

const COUNTERTOP_MATERIALS = [
  { id: 'quartz_white', label: 'Cuarzo blanco' },
  { id: 'quartz_calacatta', label: 'Cuarzo Calacatta' },
  { id: 'marble_white', label: 'Mármol blanco Carrara' },
  { id: 'marble_black', label: 'Mármol negro Marquina' },
  { id: 'granite_black', label: 'Granito negro absoluto' },
  { id: 'wood_walnut', label: 'Madera de nogal' },
  { id: 'wood_oak', label: 'Madera de roble' },
  { id: 'concrete', label: 'Hormigón pulido' },
  { id: 'dekton', label: 'Dekton' },
  { id: 'stainless_steel', label: 'Acero inoxidable' },
];

const STYLES = [
  { id: 'photorealistic', label: 'Fotorrealista' },
  { id: 'architectural', label: 'Arquitectónico' },
  { id: 'minimalist', label: 'Minimalista' },
  { id: 'warm', label: 'Cálido' },
  { id: 'industrial', label: 'Industrial' },
  { id: 'magazine', label: 'Revista' },
];

// ─── Helpers ─────────────────────────────────────────────────────────────────
function assetSrc(url) {
  if (!url) return '';
  if (url.startsWith('data:')) return url;
  if (url.startsWith('http')) return url;
  return `${API_URL}${url}`;
}

async function apiCall(path, options = {}) {
  const token = getToken();
  const res = await fetch(`${API_URL}/api/kitchen-projects${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...(options.headers || {}),
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Error desconocido' }));
    throw new Error(err.detail || `Error ${res.status}`);
  }
  return res.json();
}

// ─── Componente Principal ────────────────────────────────────────────────────
export default function KitchenDesigner3D({ state }) {
  const [view, setView] = useState('list'); // list | new | detail
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Cargar proyectos
  const loadProjects = useCallback(async () => {
    try {
      setIsLoading(true);
      const data = await apiCall('');
      setProjects(data.projects || []);
    } catch (e) {
      setError(e.message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => { loadProjects(); }, [loadProjects]);

  // ─── Vista: Lista de Proyectos ───────────────────────────────────────────
  if (view === 'list') {
    return (
      <div className="h-full flex flex-col p-6 bg-slate-50">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-black text-slate-800">Diseñador de Cocinas 3D</h1>
            <p className="text-sm text-slate-500 mt-1">Gestiona tus proyectos y genera renders fotorrealistas</p>
          </div>
          <button
            onClick={() => setView('new')}
            className="flex items-center gap-2 px-5 py-2.5 bg-indigo-600 text-white rounded-xl font-bold text-sm hover:bg-indigo-700 transition-colors shadow-lg shadow-indigo-200"
          >
            <Plus size={18} /> Nuevo Proyecto
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-xl text-sm">{error}</div>
        )}

        {isLoading ? (
          <div className="flex-1 flex items-center justify-center">
            <Loader className="animate-spin text-indigo-500" size={32} />
          </div>
        ) : projects.length === 0 ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <div className="w-20 h-20 mx-auto mb-4 bg-indigo-100 rounded-2xl flex items-center justify-center">
                <FolderOpen size={36} className="text-indigo-500" />
              </div>
              <h3 className="font-bold text-slate-700 mb-2">Sin proyectos</h3>
              <p className="text-sm text-slate-500">Crea tu primer proyecto de cocina 3D</p>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 overflow-y-auto">
            {projects.map(project => (
              <div
                key={project.id}
                onClick={() => { setSelectedProject(project); setView('detail'); }}
                className="bg-white rounded-2xl p-5 border border-slate-200 hover:border-indigo-300 hover:shadow-lg transition-all cursor-pointer group"
              >
                <div className="flex items-start justify-between mb-3">
                  <h3 className="font-bold text-slate-800 group-hover:text-indigo-600 transition-colors">{project.name}</h3>
                  <span className={`text-[10px] font-bold uppercase px-2 py-1 rounded-full ${
                    project.status === 'completed' ? 'bg-green-100 text-green-700' :
                    project.status === 'generating' ? 'bg-amber-100 text-amber-700' :
                    'bg-slate-100 text-slate-500'
                  }`}>{project.status}</span>
                </div>
                <p className="text-xs text-slate-500 mb-3">{project.description || 'Sin descripción'}</p>
                <div className="flex items-center gap-2 text-xs text-slate-400">
                  <Layers size={12} /> {LAYOUTS.find(l => l.id === project.layout)?.label || project.layout}
                  <span className="mx-1">·</span>
                  <Image size={12} /> {project.renders?.length || 0} renders
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  // ─── Vista: Nuevo Proyecto ───────────────────────────────────────────────
  if (view === 'new') {
    return <NewProjectForm onBack={() => setView('list')} onCreated={(p) => {
      setSelectedProject(p);
      setView('detail');
      loadProjects();
    }} />;
  }

  // ─── Vista: Detalle de Proyecto ──────────────────────────────────────────
  if (view === 'detail' && selectedProject) {
    return <ProjectDetail
      project={selectedProject}
      onBack={() => { setView('list'); loadProjects(); }}
      onUpdate={(p) => setSelectedProject(p)}
    />;
  }

  return null;
}

// ─── Formulario de Nuevo Proyecto ────────────────────────────────────────────
function NewProjectForm({ onBack, onCreated }) {
  const [form, setForm] = useState({
    name: '',
    description: '',
    layout: 'L-shape',
    cabinet_material: 'white_matte',
    countertop_material: 'quartz_white',
    style: 'photorealistic',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name.trim()) return;
    setIsSubmitting(true);
    try {
      const data = await apiCall('', { method: 'POST', body: JSON.stringify(form) });
      onCreated(data.project);
    } catch (e) {
      alert(e.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="h-full flex flex-col p-6 bg-slate-50">
      <button onClick={onBack} className="flex items-center gap-2 text-sm text-slate-500 hover:text-slate-700 mb-6">
        <ArrowLeft size={16} /> Volver a proyectos
      </button>

      <h2 className="text-xl font-black text-slate-800 mb-6">Nuevo Proyecto de Cocina</h2>

      <form onSubmit={handleSubmit} className="max-w-2xl space-y-5 overflow-y-auto">
        <div>
          <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1.5">Nombre del proyecto *</label>
          <input
            type="text"
            value={form.name}
            onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
            className="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-indigo-300 focus:border-indigo-400 outline-none"
            placeholder="Ej: Cocina familia García"
            required
          />
        </div>

        <div>
          <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1.5">Descripción</label>
          <textarea
            value={form.description}
            onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
            className="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-indigo-300 focus:border-indigo-400 outline-none resize-none"
            rows={2}
            placeholder="Notas adicionales sobre el proyecto..."
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1.5">Distribución</label>
            <select
              value={form.layout}
              onChange={e => setForm(f => ({ ...f, layout: e.target.value }))}
              className="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-indigo-300 outline-none"
            >
              {LAYOUTS.map(l => <option key={l.id} value={l.id}>{l.label}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1.5">Estilo</label>
            <select
              value={form.style}
              onChange={e => setForm(f => ({ ...f, style: e.target.value }))}
              className="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-indigo-300 outline-none"
            >
              {STYLES.map(s => <option key={s.id} value={s.id}>{s.label}</option>)}
            </select>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1.5">Material muebles</label>
            <select
              value={form.cabinet_material}
              onChange={e => setForm(f => ({ ...f, cabinet_material: e.target.value }))}
              className="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-indigo-300 outline-none"
            >
              {CABINET_MATERIALS.map(m => <option key={m.id} value={m.id}>{m.label}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-bold text-slate-600 uppercase tracking-wider mb-1.5">Encimera</label>
            <select
              value={form.countertop_material}
              onChange={e => setForm(f => ({ ...f, countertop_material: e.target.value }))}
              className="w-full px-4 py-3 bg-white border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-indigo-300 outline-none"
            >
              {COUNTERTOP_MATERIALS.map(m => <option key={m.id} value={m.id}>{m.label}</option>)}
            </select>
          </div>
        </div>

        <button
          type="submit"
          disabled={isSubmitting || !form.name.trim()}
          className="w-full py-3.5 bg-indigo-600 text-white rounded-xl font-bold text-sm hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-lg shadow-indigo-200"
        >
          {isSubmitting ? <Loader className="animate-spin mx-auto" size={18} /> : 'Crear Proyecto'}
        </button>
      </form>
    </div>
  );
}

// ─── Detalle de Proyecto ─────────────────────────────────────────────────────
function ProjectDetail({ project, onBack, onUpdate }) {
  const [isGenerating, setIsGenerating] = useState(false);
  const [iterateText, setIterateText] = useState('');
  const [isIterating, setIsIterating] = useState(false);
  const [selectedRender, setSelectedRender] = useState(null);
  const [showFullscreen, setShowFullscreen] = useState(false);
  const [localProject, setLocalProject] = useState(project);

  const handleGenerate = async () => {
    setIsGenerating(true);
    try {
      const data = await apiCall(`/${localProject.id}/render`, { method: 'POST' });
      const updated = { ...localProject, renders: [...(localProject.renders || []), data.render], status: 'completed' };
      setLocalProject(updated);
      onUpdate(updated);
      setSelectedRender(data.render);
    } catch (e) {
      alert('Error al generar: ' + e.message);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleIterate = async () => {
    if (!iterateText.trim()) return;
    setIsIterating(true);
    try {
      const data = await apiCall(`/${localProject.id}/iterate`, {
        method: 'POST',
        body: JSON.stringify({ change_description: iterateText }),
      });
      const updated = { ...localProject, renders: [...(localProject.renders || []), data.render], status: 'completed' };
      setLocalProject(updated);
      onUpdate(updated);
      setSelectedRender(data.render);
      setIterateText('');
    } catch (e) {
      alert('Error en iteración: ' + e.message);
    } finally {
      setIsIterating(false);
    }
  };

  const handleDelete = async () => {
    if (!window.confirm('¿Eliminar este proyecto?')) return;
    try {
      await apiCall(`/${localProject.id}`, { method: 'DELETE' });
      onBack();
    } catch (e) {
      alert(e.message);
    }
  };

  const renders = localProject.renders || [];
  const latestRender = selectedRender || renders[renders.length - 1];
  const latestImage = latestRender?.result?.images?.[0] || latestRender?.result?.result?.images?.[0];

  return (
    <div className="h-full flex flex-col p-6 bg-slate-50">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <button onClick={onBack} className="flex items-center gap-2 text-sm text-slate-500 hover:text-slate-700">
          <ArrowLeft size={16} /> Proyectos
        </button>
        <button onClick={handleDelete} className="flex items-center gap-1.5 text-xs text-red-500 hover:text-red-700">
          <Trash2 size={14} /> Eliminar
        </button>
      </div>

      <div className="flex-1 flex gap-6 min-h-0">
        {/* Panel izquierdo: Info + Controles */}
        <div className="w-80 shrink-0 flex flex-col gap-4 overflow-y-auto">
          <div className="bg-white rounded-2xl p-5 border border-slate-200">
            <h2 className="font-black text-lg text-slate-800 mb-1">{localProject.name}</h2>
            <p className="text-xs text-slate-500 mb-4">{localProject.description || 'Sin descripción'}</p>

            <div className="space-y-2 text-xs">
              <div className="flex justify-between"><span className="text-slate-500">Distribución</span><span className="font-bold">{LAYOUTS.find(l => l.id === localProject.layout)?.label}</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Muebles</span><span className="font-bold">{CABINET_MATERIALS.find(m => m.id === localProject.cabinet_material)?.label}</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Encimera</span><span className="font-bold">{COUNTERTOP_MATERIALS.find(m => m.id === localProject.countertop_material)?.label}</span></div>
              <div className="flex justify-between"><span className="text-slate-500">Estilo</span><span className="font-bold">{STYLES.find(s => s.id === localProject.style)?.label}</span></div>
            </div>
          </div>

          {/* Generar render */}
          <button
            onClick={handleGenerate}
            disabled={isGenerating}
            className="w-full py-3 bg-indigo-600 text-white rounded-xl font-bold text-sm hover:bg-indigo-700 disabled:opacity-50 transition-colors flex items-center justify-center gap-2 shadow-lg shadow-indigo-200"
          >
            {isGenerating ? <><Loader className="animate-spin" size={16} /> Generando...</> : <><Wand2 size={16} /> Generar Render 3D</>}
          </button>

          {/* Iteración rápida */}
          {renders.length > 0 && (
            <div className="bg-white rounded-2xl p-4 border border-slate-200">
              <h4 className="text-xs font-bold text-slate-600 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <RefreshCw size={12} /> Iteración Rápida
              </h4>
              <p className="text-[11px] text-slate-400 mb-3">Describe el cambio que quieres aplicar al diseño actual</p>
              <textarea
                value={iterateText}
                onChange={e => setIterateText(e.target.value)}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs resize-none focus:ring-2 focus:ring-indigo-200 outline-none"
                rows={2}
                placeholder="Ej: Cambiar encimera a granito negro..."
              />
              <button
                onClick={handleIterate}
                disabled={isIterating || !iterateText.trim()}
                className="mt-2 w-full py-2 bg-purple-600 text-white rounded-lg text-xs font-bold hover:bg-purple-700 disabled:opacity-50 transition-colors flex items-center justify-center gap-1.5"
              >
                {isIterating ? <Loader className="animate-spin" size={12} /> : <Palette size={12} />}
                {isIterating ? 'Aplicando cambio...' : 'Aplicar Cambio'}
              </button>
            </div>
          )}

          {/* Historial */}
          {renders.length > 0 && (
            <div className="bg-white rounded-2xl p-4 border border-slate-200">
              <h4 className="text-xs font-bold text-slate-600 uppercase tracking-wider mb-3">Historial ({renders.length})</h4>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {renders.map((r, i) => (
                  <button
                    key={r.id || i}
                    onClick={() => setSelectedRender(r)}
                    className={`w-full text-left p-2 rounded-lg text-xs transition-colors ${
                      selectedRender?.id === r.id ? 'bg-indigo-50 border border-indigo-200' : 'hover:bg-slate-50'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-slate-700">
                        {r.is_iteration ? `Iteración: ${r.change_request?.substring(0, 30)}...` : `Render #${i + 1}`}
                      </span>
                      <CheckCircle size={12} className={r.status === 'completed' ? 'text-green-500' : 'text-slate-300'} />
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Panel derecho: Visualizador */}
        <div className="flex-1 bg-white rounded-2xl border border-slate-200 flex flex-col overflow-hidden">
          {latestImage ? (
            <>
              <div className="flex-1 relative flex items-center justify-center bg-slate-900 p-4">
                <img
                  src={assetSrc(latestImage)}
                  alt="Render 3D"
                  className="max-w-full max-h-full object-contain rounded-lg"
                />
                <div className="absolute top-3 right-3 flex gap-2">
                  <button
                    onClick={() => setShowFullscreen(true)}
                    className="p-2 bg-black/50 text-white rounded-lg hover:bg-black/70 transition-colors"
                  >
                    <Maximize2 size={16} />
                  </button>
                  <a
                    href={assetSrc(latestImage)}
                    download="render-cocina-3d.png"
                    className="p-2 bg-black/50 text-white rounded-lg hover:bg-black/70 transition-colors"
                  >
                    <Download size={16} />
                  </a>
                </div>
                <div className="absolute bottom-3 right-3 px-3 py-1.5 bg-black/60 backdrop-blur-sm rounded-lg">
                  <span className="text-[9px] font-black text-white/80 uppercase tracking-widest">
                    LuiggiAI Render Engine
                  </span>
                </div>
              </div>
              {latestRender?.duration_seconds && (
                <div className="p-3 border-t border-slate-100 flex items-center gap-4 text-xs text-slate-500">
                  <span>Tiempo: {latestRender.duration_seconds}s</span>
                  {latestRender.is_iteration && <span className="text-purple-600 font-bold">Iteración</span>}
                </div>
              )}
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center max-w-sm">
                <div className="w-20 h-20 mx-auto mb-6 bg-gradient-to-br from-indigo-100 to-purple-100 rounded-2xl flex items-center justify-center">
                  <Image size={36} className="text-indigo-500" />
                </div>
                <h3 className="font-black text-slate-700 uppercase tracking-wider mb-2">Visualizador 3D</h3>
                <p className="text-sm text-slate-500 leading-relaxed">
                  Haz clic en "Generar Render 3D" para crear una visualización fotorrealista de tu cocina con los materiales seleccionados.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Fullscreen Modal */}
      {showFullscreen && latestImage && (
        <div className="fixed inset-0 bg-black/95 z-[9999] flex items-center justify-center p-4" onClick={() => setShowFullscreen(false)}>
          <button className="absolute top-6 right-6 text-white/70 hover:text-white" onClick={() => setShowFullscreen(false)}>
            <X size={32} />
          </button>
          <img
            src={assetSrc(latestImage)}
            alt="Render 3D"
            className="max-w-full max-h-full object-contain rounded-xl shadow-2xl"
          />
        </div>
      )}
    </div>
  );
}
