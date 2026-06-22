/**
 * KitchenDesigner3D v2 - Panel Completo de Diseño de Cocinas
 * ===========================================================
 * Componente completo para gestionar proyectos de cocinas 3D con:
 * - Gestión de proyectos (crear, listar, eliminar)
 * - Subida ilimitada de fotos y vídeos con instrucciones
 * - Medidas de paredes proporcionadas por el usuario
 * - Editor de muebles personalizable (tipo, posición, medidas, acabado)
 * - Materiales y colores como campo libre (sin catálogo cerrado)
 * - Generación de renders con IA
 * - Iteración rápida (cambiar material sin empezar de cero)
 * - Aprobación con generación de documentación técnica:
 *   - Plano de instalaciones (enchufes, tomas de agua con coordenadas)
 *   - Alzado alámbrico SVG con cotas
 *   - Despiece de muebles con valoración por biblioteca (ZC/MV)
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  FolderOpen, Plus, Image, Loader, Download, Maximize2, X,
  Wand2, ArrowLeft, Trash2, RefreshCw, Layers, Palette, CheckCircle,
  Upload, Video, Ruler, Box, FileText, ChevronRight, ChevronDown
} from 'lucide-react';
import { getToken } from '../services/api';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// ─── Helpers ─────────────────────────────────────────────────────────────────
function assetSrc(url) {
  if (!url) return '';
  if (url.startsWith('data:')) return url;
  let full = url.startsWith('http') ? url : `${API_URL}${url}`;
  // El proxy de assets (imágenes de Manus) exige el JWT por query param,
  // porque las etiquetas <img> del navegador no pueden enviar cabeceras.
  if (full.includes('/api/ai-engine/asset') && !/[?&]t=/.test(full)) {
    const tok = getToken();
    if (tok) full += (full.includes('?') ? '&' : '?') + 't=' + encodeURIComponent(tok);
  }
  return full;
}

// Extrae la URL/imagen de un render sea cual sea la forma que devuelva el backend.
// Backend actual: render.result.result.images[0]. Se cubren también formas planas.
function renderImageSrc(r) {
  const res = (r && r.result) || {};
  const inner = res.result || {};
  const url =
    res.image_url ||
    (Array.isArray(res.images) && res.images[0]) ||
    inner.image_url ||
    (Array.isArray(inner.images) && inner.images[0]) ||
    '';
  return url || '';
}

async function apiCall(path, options = {}) {
  const token = getToken();
  const headers = { 'Authorization': `Bearer ${token}`, ...(options.headers || {}) };
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }
  const res = await fetch(`${API_URL}/api/kitchen-projects${path}`, { ...options, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Error desconocido' }));
    throw new Error(err.detail || `Error ${res.status}`);
  }
  return res.json();
}

// ─── Componente Principal ────────────────────────────────────────────────────
export default function KitchenDesigner3D({ state }) {
  const [view, setView] = useState('list');
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [diag, setDiag] = useState(null);
  const [diagLoading, setDiagLoading] = useState(false);

  const runDiagnostics = useCallback(async () => {
    setDiagLoading(true);
    setDiag(null);
    try {
      const res = await fetch(`${API_URL}/api/ai-engine/diagnostics`, {
        headers: { 'Authorization': `Bearer ${getToken()}` },
      });
      const data = await res.json();
      setDiag(data);
    } catch (e) {
      setDiag({ error: 'No se pudo conectar con el backend.' });
    } finally {
      setDiagLoading(false);
    }
  }, []);

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
          <div className="flex items-center gap-2">
            <button
              onClick={runDiagnostics}
              disabled={diagLoading}
              title="Comprueba si el motor de render (Manus/Gemini) está configurado"
              className="flex items-center gap-2 px-4 py-2.5 bg-white border border-slate-200 text-slate-600 rounded-xl font-bold text-sm hover:bg-slate-50 transition-colors"
            >
              {diagLoading ? <Loader size={16} className="animate-spin" /> : <Wand2 size={16} />} Diagnóstico IA
            </button>
            <button
              onClick={() => setView('new')}
              className="flex items-center gap-2 px-5 py-2.5 bg-indigo-600 text-white rounded-xl font-bold text-sm hover:bg-indigo-700 transition-colors shadow-lg shadow-indigo-200"
            >
              <Plus size={18} /> Nuevo Proyecto
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>
        )}

        {diag && (
          <div className="mb-4 p-4 bg-white border border-slate-200 rounded-xl text-sm">
            <div className="flex items-center justify-between mb-2">
              <span className="font-black text-slate-700">Diagnóstico del motor de render</span>
              <button onClick={() => setDiag(null)} className="text-slate-400 hover:text-slate-600"><X size={16} /></button>
            </div>
            {diag.error ? (
              <p className="text-red-600">{diag.error}</p>
            ) : (
              <div className="space-y-1.5">
                <p className="font-bold text-slate-800">
                  {diag.effective_engine === 'manus' && <span className="text-green-600">✅ Usará MANUS</span>}
                  {diag.effective_engine === 'gemini' && <span className="text-amber-600">🟡 Usará GEMINI (respaldo)</span>}
                  {diag.effective_engine === 'ninguno' && <span className="text-red-600">❌ Sin motor: faltan claves</span>}
                </p>
                <p><b>Manus:</b> {diag.manus?.key_present ? `clave puesta (${diag.manus.key_length} car.)` : 'sin clave'}
                  {diag.manus?.key_present && (diag.manus.reachable ? ` · conecta (HTTP ${diag.manus.http_status})` : ` · NO conecta (${diag.manus.error || 'error'})`)}</p>
                <p><b>Gemini:</b> {diag.gemini?.key_present ? 'clave puesta' : 'sin clave'} · SDK {diag.gemini?.sdk_available ? 'ok' : 'no'}</p>
                <p className="text-slate-500">{diag.hint}</p>
              </div>
            )}
          </div>
        )}

        {isLoading ? (
          <div className="flex-1 flex items-center justify-center">
            <Loader className="animate-spin text-indigo-500" size={32} />
          </div>
        ) : projects.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center text-slate-400">
            <FolderOpen size={48} className="mb-3" />
            <p className="text-lg font-medium">No hay proyectos aún</p>
            <p className="text-sm">Crea tu primer proyecto para empezar a diseñar</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {projects.map(p => (
              <div
                key={p.id}
                onClick={() => { setSelectedProject(p); setView('detail'); }}
                className="bg-white rounded-xl border border-slate-200 p-5 cursor-pointer hover:shadow-lg hover:border-indigo-300 transition-all"
              >
                <div className="flex items-start justify-between mb-3">
                  <h3 className="font-bold text-slate-800 truncate">{p.name}</h3>
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                    p.status === 'approved' ? 'bg-green-100 text-green-700' :
                    p.status === 'completed' ? 'bg-blue-100 text-blue-700' :
                    p.status === 'generating' ? 'bg-yellow-100 text-yellow-700' :
                    'bg-slate-100 text-slate-600'
                  }`}>{p.status}</span>
                </div>
                {p.description && <p className="text-sm text-slate-500 line-clamp-2 mb-3">{p.description}</p>}
                <div className="flex items-center gap-3 text-xs text-slate-400">
                  <span className="flex items-center gap-1"><Image size={12} /> {(p.files || []).length} archivos</span>
                  <span className="flex items-center gap-1"><Box size={12} /> {(p.cabinets || []).length} muebles</span>
                  <span className="flex items-center gap-1"><Layers size={12} /> {(p.renders || []).length} renders</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  // ─── Vista: Nuevo Proyecto ─────────────────────────────────────────────────
  if (view === 'new') {
    return <NewProjectForm onBack={() => setView('list')} onCreated={(p) => { setSelectedProject(p); setView('detail'); loadProjects(); }} />;
  }

  // ─── Vista: Detalle de Proyecto ────────────────────────────────────────────
  if (view === 'detail' && selectedProject) {
    return <ProjectDetail project={selectedProject} onBack={() => { setView('list'); loadProjects(); }} onUpdate={(p) => setSelectedProject(p)} />;
  }

  return null;
}


// ═══════════════════════════════════════════════════════════════════════════════
// FORMULARIO NUEVO PROYECTO
// ═══════════════════════════════════════════════════════════════════════════════
function NewProjectForm({ onBack, onCreated }) {
  const [form, setForm] = useState({ name: '', description: '', layout: '', cabinet_material: '', countertop_material: '', style: '' });
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
      <button onClick={onBack} className="flex items-center gap-2 text-slate-600 hover:text-slate-800 mb-6">
        <ArrowLeft size={18} /> Volver a proyectos
      </button>

      <div className="max-w-2xl mx-auto w-full">
        <h2 className="text-2xl font-black text-slate-800 mb-2">Nuevo Proyecto de Cocina</h2>
        <p className="text-slate-500 mb-6">Crea el proyecto y luego añade fotos, medidas y muebles desde el panel de detalle.</p>

        <form onSubmit={handleSubmit} className="bg-white rounded-xl border border-slate-200 p-6 space-y-5">
          <div>
            <label className="block text-sm font-bold text-slate-700 mb-1">Nombre del proyecto *</label>
            <input type="text" value={form.name} onChange={e => setForm({...form, name: e.target.value})}
              className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="Ej: Cocina familia García" required />
          </div>

          <div>
            <label className="block text-sm font-bold text-slate-700 mb-1">Descripción / Instrucciones</label>
            <textarea value={form.description} onChange={e => setForm({...form, description: e.target.value})}
              className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              rows={3} placeholder="Describe lo que quieres para esta cocina..." />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-bold text-slate-700 mb-1">Distribución</label>
              <input type="text" value={form.layout} onChange={e => setForm({...form, layout: e.target.value})}
                className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Ej: En L, En U, Lineal..." />
            </div>
            <div>
              <label className="block text-sm font-bold text-slate-700 mb-1">Estilo</label>
              <input type="text" value={form.style} onChange={e => setForm({...form, style: e.target.value})}
                className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Ej: Moderno, Nórdico, Industrial..." />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-bold text-slate-700 mb-1">Material muebles</label>
              <input type="text" value={form.cabinet_material} onChange={e => setForm({...form, cabinet_material: e.target.value})}
                className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Ej: Blanco mate, Roble natural..." />
            </div>
            <div>
              <label className="block text-sm font-bold text-slate-700 mb-1">Material encimera</label>
              <input type="text" value={form.countertop_material} onChange={e => setForm({...form, countertop_material: e.target.value})}
                className="w-full px-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                placeholder="Ej: Cuarzo Calacatta, Granito negro..." />
            </div>
          </div>

          <button type="submit" disabled={isSubmitting}
            className="w-full py-3 bg-indigo-600 text-white rounded-xl font-bold hover:bg-indigo-700 disabled:opacity-50 transition-colors">
            {isSubmitting ? 'Creando...' : 'Crear Proyecto'}
          </button>
        </form>
      </div>
    </div>
  );
}


// ═══════════════════════════════════════════════════════════════════════════════
// DETALLE DE PROYECTO
// ═══════════════════════════════════════════════════════════════════════════════
function ProjectDetail({ project: initialProject, onBack, onUpdate }) {
  const [project, setProject] = useState(initialProject);
  const [activeTab, setActiveTab] = useState('files');
  const [isLoading, setIsLoading] = useState(false);

  const refreshProject = async () => {
    try {
      const data = await apiCall(`/${project.id}`);
      setProject(data.project);
      onUpdate(data.project);
    } catch (e) { /* ignore */ }
  };

  const tabs = [
    { id: 'files', label: 'Fotos/Vídeos', icon: Image },
    { id: 'measurements', label: 'Medidas', icon: Ruler },
    { id: 'cabinets', label: 'Muebles', icon: Box },
    { id: 'renders', label: 'Renders', icon: Wand2 },
    { id: 'docs', label: 'Doc. Técnica', icon: FileText },
  ];

  return (
    <div className="h-full flex flex-col p-6 bg-slate-50">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <button onClick={onBack} className="p-2 hover:bg-slate-200 rounded-lg transition-colors">
            <ArrowLeft size={18} />
          </button>
          <div>
            <h1 className="text-xl font-black text-slate-800">{project.name}</h1>
            <p className="text-sm text-slate-500">{project.description || 'Sin descripción'}</p>
          </div>
        </div>
        <span className={`text-xs px-3 py-1 rounded-full font-bold ${
          project.status === 'approved' ? 'bg-green-100 text-green-700' :
          project.status === 'completed' ? 'bg-blue-100 text-blue-700' :
          'bg-slate-100 text-slate-600'
        }`}>{project.status?.toUpperCase()}</span>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-4 bg-white rounded-xl border border-slate-200 p-1">
        {tabs.map(tab => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === tab.id ? 'bg-indigo-600 text-white' : 'text-slate-600 hover:bg-slate-100'
            }`}>
            <tab.icon size={16} /> {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-auto">
        {activeTab === 'files' && <FilesTab project={project} onRefresh={refreshProject} />}
        {activeTab === 'measurements' && <MeasurementsTab project={project} onRefresh={refreshProject} />}
        {activeTab === 'cabinets' && <CabinetsTab project={project} onRefresh={refreshProject} />}
        {activeTab === 'renders' && <RendersTab project={project} onRefresh={refreshProject} />}
        {activeTab === 'docs' && <TechnicalDocsTab project={project} onRefresh={refreshProject} />}
      </div>
    </div>
  );
}


// ─── Tab: Archivos ───────────────────────────────────────────────────────────
function FilesTab({ project, onRefresh }) {
  const [uploading, setUploading] = useState(false);
  const [wallLabel, setWallLabel] = useState('');

  const handleUpload = async (e, fileType) => {
    const files = Array.from(e.target.files);
    if (!files.length) return;
    setUploading(true);
    try {
      for (const file of files) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('file_type', fileType);
        if (wallLabel) formData.append('wall_label', wallLabel);
        await apiCall(`/${project.id}/files`, {
          method: 'POST',
          body: formData,
          headers: {},
        });
      }
      await onRefresh();
    } catch (e) {
      alert(e.message);
    } finally {
      setUploading(false);
    }
  };

  const files = project.files || [];

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6">
      <h3 className="text-lg font-bold text-slate-800 mb-4">Fotos y Vídeos del Espacio</h3>
      <p className="text-sm text-slate-500 mb-4">Sube todas las fotos de las paredes que necesites. También puedes subir un vídeo con instrucciones de voz.</p>

      <div className="flex items-center gap-3 mb-4">
        <input type="text" value={wallLabel} onChange={e => setWallLabel(e.target.value)}
          className="px-3 py-2 border border-slate-300 rounded-lg text-sm"
          placeholder="Etiqueta pared (ej: Pared A)" />
      </div>

      <div className="flex gap-3 mb-6">
        <label className="flex items-center gap-2 px-4 py-2.5 bg-indigo-50 text-indigo-700 rounded-lg cursor-pointer hover:bg-indigo-100 transition-colors font-medium text-sm">
          <Upload size={16} /> Subir Fotos
          <input type="file" multiple accept="image/*" className="hidden" onChange={e => handleUpload(e, 'photo')} />
        </label>
        <label className="flex items-center gap-2 px-4 py-2.5 bg-purple-50 text-purple-700 rounded-lg cursor-pointer hover:bg-purple-100 transition-colors font-medium text-sm">
          <Video size={16} /> Subir Vídeo
          <input type="file" accept="video/*" className="hidden" onChange={e => handleUpload(e, 'video')} />
        </label>
        {uploading && <Loader className="animate-spin text-indigo-500" size={20} />}
      </div>

      {files.length === 0 ? (
        <div className="text-center py-8 text-slate-400">
          <Image size={40} className="mx-auto mb-2" />
          <p>No hay archivos subidos aún</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {files.map(f => (
            <div key={f.id} className="border border-slate-200 rounded-lg p-3 text-center">
              {f.file_type === 'video' ? (
                <Video size={32} className="mx-auto text-purple-500 mb-2" />
              ) : (
                <Image size={32} className="mx-auto text-indigo-500 mb-2" />
              )}
              <p className="text-xs text-slate-600 truncate">{f.file_name}</p>
              {f.wall_label && <span className="text-xs bg-slate-100 px-2 py-0.5 rounded mt-1 inline-block">{f.wall_label}</span>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}


// ─── Tab: Medidas ────────────────────────────────────────────────────────────
function MeasurementsTab({ project, onRefresh }) {
  const [form, setForm] = useState({
    wall_label: '', wall_width: '', wall_height: '',
    window_width: '', window_height: '', window_from_floor: '', window_from_left: '',
    door_width: '', door_height: '', door_from_left: '', notes: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.wall_label.trim()) return;
    setIsSubmitting(true);
    try {
      const payload = {};
      for (const [key, val] of Object.entries(form)) {
        if (val === '' || val === null) continue;
        payload[key] = ['wall_label', 'notes'].includes(key) ? val : parseFloat(val) || null;
      }
      payload.wall_label = form.wall_label;
      await apiCall(`/${project.id}/measurements`, { method: 'POST', body: JSON.stringify(payload) });
      setForm({ wall_label: '', wall_width: '', wall_height: '', window_width: '', window_height: '', window_from_floor: '', window_from_left: '', door_width: '', door_height: '', door_from_left: '', notes: '' });
      await onRefresh();
    } catch (e) {
      alert(e.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const measurements = project.measurements || [];

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6">
      <h3 className="text-lg font-bold text-slate-800 mb-4">Medidas de Paredes</h3>
      <p className="text-sm text-slate-500 mb-4">Introduce las medidas reales de cada pared (en cm). Incluye ventanas y puertas si las hay.</p>

      <form onSubmit={handleSubmit} className="space-y-4 mb-6 border-b border-slate-200 pb-6">
        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="text-xs font-bold text-slate-600">Nombre pared *</label>
            <input type="text" value={form.wall_label} onChange={e => setForm({...form, wall_label: e.target.value})}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" placeholder="Pared A" required />
          </div>
          <div>
            <label className="text-xs font-bold text-slate-600">Ancho (cm)</label>
            <input type="number" value={form.wall_width} onChange={e => setForm({...form, wall_width: e.target.value})}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" placeholder="300" />
          </div>
          <div>
            <label className="text-xs font-bold text-slate-600">Alto (cm)</label>
            <input type="number" value={form.wall_height} onChange={e => setForm({...form, wall_height: e.target.value})}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" placeholder="260" />
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          <div>
            <label className="text-xs font-bold text-slate-600">Ventana ancho</label>
            <input type="number" value={form.window_width} onChange={e => setForm({...form, window_width: e.target.value})}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
          </div>
          <div>
            <label className="text-xs font-bold text-slate-600">Ventana alto</label>
            <input type="number" value={form.window_height} onChange={e => setForm({...form, window_height: e.target.value})}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
          </div>
          <div>
            <label className="text-xs font-bold text-slate-600">Ventana desde suelo</label>
            <input type="number" value={form.window_from_floor} onChange={e => setForm({...form, window_from_floor: e.target.value})}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
          </div>
          <div>
            <label className="text-xs font-bold text-slate-600">Ventana desde izq.</label>
            <input type="number" value={form.window_from_left} onChange={e => setForm({...form, window_from_left: e.target.value})}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
          </div>
        </div>

        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="text-xs font-bold text-slate-600">Puerta ancho</label>
            <input type="number" value={form.door_width} onChange={e => setForm({...form, door_width: e.target.value})}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
          </div>
          <div>
            <label className="text-xs font-bold text-slate-600">Puerta alto</label>
            <input type="number" value={form.door_height} onChange={e => setForm({...form, door_height: e.target.value})}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
          </div>
          <div>
            <label className="text-xs font-bold text-slate-600">Puerta desde izq.</label>
            <input type="number" value={form.door_from_left} onChange={e => setForm({...form, door_from_left: e.target.value})}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
          </div>
        </div>

        <div>
          <label className="text-xs font-bold text-slate-600">Notas</label>
          <input type="text" value={form.notes} onChange={e => setForm({...form, notes: e.target.value})}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" placeholder="Ej: Tiene un pilar a 80cm..." />
        </div>

        <button type="submit" disabled={isSubmitting}
          className="px-5 py-2 bg-indigo-600 text-white rounded-lg font-bold text-sm hover:bg-indigo-700 disabled:opacity-50">
          {isSubmitting ? 'Guardando...' : 'Añadir Medida'}
        </button>
      </form>

      {measurements.length > 0 && (
        <div className="space-y-3">
          {measurements.map(m => (
            <div key={m.id} className="border border-slate-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-bold text-slate-700">{m.wall_label}</h4>
                <span className="text-xs bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded">{m.wall_width || '?'} x {m.wall_height || '?'} cm</span>
              </div>
              <div className="flex flex-wrap gap-2 text-xs text-slate-500">
                {m.window_width && <span>🪟 Ventana: {m.window_width}x{m.window_height}cm</span>}
                {m.door_width && <span>🚪 Puerta: {m.door_width}x{m.door_height}cm</span>}
                {m.notes && <span>📝 {m.notes}</span>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}


// ─── Tab: Muebles ────────────────────────────────────────────────────────────
function CabinetsTab({ project, onRefresh }) {
  const [form, setForm] = useState({
    cabinet_type: '', wall_label: '', width: '', height: '', depth: '',
    position_from_left: '', material: '', color: '', handle_type: '', notes: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.cabinet_type.trim()) return;
    setIsSubmitting(true);
    try {
      const payload = {};
      for (const [key, val] of Object.entries(form)) {
        if (val === '' || val === null) continue;
        if (['width', 'height', 'depth', 'position_from_left'].includes(key)) {
          payload[key] = parseFloat(val) || null;
        } else {
          payload[key] = val;
        }
      }
      await apiCall(`/${project.id}/cabinets`, { method: 'POST', body: JSON.stringify(payload) });
      setForm({ cabinet_type: '', wall_label: '', width: '', height: '', depth: '', position_from_left: '', material: '', color: '', handle_type: '', notes: '' });
      await onRefresh();
    } catch (e) {
      alert(e.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (cabinetId) => {
    if (!confirm('¿Eliminar este mueble?')) return;
    try {
      await apiCall(`/${project.id}/cabinets/${cabinetId}`, { method: 'DELETE' });
      await onRefresh();
    } catch (e) {
      alert(e.message);
    }
  };

  const cabinets = project.cabinets || [];

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6">
      <h3 className="text-lg font-bold text-slate-800 mb-4">Muebles de la Cocina</h3>
      <p className="text-sm text-slate-500 mb-4">Define cada módulo exactamente como lo necesitas. Escribe libremente el tipo, material y color.</p>

      <form onSubmit={handleSubmit} className="space-y-4 mb-6 border-b border-slate-200 pb-6">
        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="text-xs font-bold text-slate-600">Tipo de mueble *</label>
            <input type="text" value={form.cabinet_type} onChange={e => setForm({...form, cabinet_type: e.target.value})}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
              placeholder="Ej: Bajo fregadero, Alto, Columna..." required />
          </div>
          <div>
            <label className="text-xs font-bold text-slate-600">Pared</label>
            <input type="text" value={form.wall_label} onChange={e => setForm({...form, wall_label: e.target.value})}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" placeholder="Pared A" />
          </div>
          <div>
            <label className="text-xs font-bold text-slate-600">Posición desde izq. (cm)</label>
            <input type="number" value={form.position_from_left} onChange={e => setForm({...form, position_from_left: e.target.value})}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" placeholder="0" />
          </div>
        </div>

        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="text-xs font-bold text-slate-600">Ancho (cm)</label>
            <input type="number" value={form.width} onChange={e => setForm({...form, width: e.target.value})}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" placeholder="60" />
          </div>
          <div>
            <label className="text-xs font-bold text-slate-600">Alto (cm)</label>
            <input type="number" value={form.height} onChange={e => setForm({...form, height: e.target.value})}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" placeholder="70" />
          </div>
          <div>
            <label className="text-xs font-bold text-slate-600">Fondo (cm)</label>
            <input type="number" value={form.depth} onChange={e => setForm({...form, depth: e.target.value})}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" placeholder="58" />
          </div>
        </div>

        <div className="grid grid-cols-3 gap-3">
          <div>
            <label className="text-xs font-bold text-slate-600">Material</label>
            <input type="text" value={form.material} onChange={e => setForm({...form, material: e.target.value})}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" placeholder="Ej: Melamina, Lacado..." />
          </div>
          <div>
            <label className="text-xs font-bold text-slate-600">Color</label>
            <input type="text" value={form.color} onChange={e => setForm({...form, color: e.target.value})}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" placeholder="Ej: Blanco mate, Roble..." />
          </div>
          <div>
            <label className="text-xs font-bold text-slate-600">Tirador</label>
            <input type="text" value={form.handle_type} onChange={e => setForm({...form, handle_type: e.target.value})}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" placeholder="Ej: Gola, Barra negra..." />
          </div>
        </div>

        <div>
          <label className="text-xs font-bold text-slate-600">Notas</label>
          <input type="text" value={form.notes} onChange={e => setForm({...form, notes: e.target.value})}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" placeholder="Ej: Con cajones interiores..." />
        </div>

        <button type="submit" disabled={isSubmitting}
          className="px-5 py-2 bg-indigo-600 text-white rounded-lg font-bold text-sm hover:bg-indigo-700 disabled:opacity-50">
          {isSubmitting ? 'Añadiendo...' : 'Añadir Mueble'}
        </button>
      </form>

      {cabinets.length > 0 && (
        <div className="space-y-2">
          {cabinets.map(c => (
            <div key={c.id} className="flex items-center justify-between border border-slate-200 rounded-lg p-3">
              <div>
                <span className="font-bold text-slate-700 text-sm">{c.cabinet_type}</span>
                <span className="text-xs text-slate-500 ml-2">
                  {c.width && `${c.width}x${c.height || '?'}x${c.depth || '?'}cm`}
                  {c.wall_label && ` · ${c.wall_label}`}
                  {c.material && ` · ${c.material}`}
                  {c.color && ` · ${c.color}`}
                </span>
              </div>
              <button onClick={() => handleDelete(c.id)} className="p-1.5 text-red-400 hover:text-red-600 hover:bg-red-50 rounded">
                <Trash2 size={14} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}


// ─── Tab: Renders ────────────────────────────────────────────────────────────
function RendersTab({ project, onRefresh }) {
  const [isGenerating, setIsGenerating] = useState(false);
  const [iterateText, setIterateText] = useState('');
  const [isIterating, setIsIterating] = useState(false);
  // Render fiel: plano en planta + un boceto por cada pared
  const [floorPlan, setFloorPlan] = useState(null);
  const [sketches, setSketches] = useState([]); // [{label, data}]
  const [composeBrief, setComposeBrief] = useState('');
  const [isComposing, setIsComposing] = useState(false);

  const handleGenerate = async () => {
    setIsGenerating(true);
    try {
      await apiCall(`/${project.id}/render`, { method: 'POST' });
      await onRefresh();
    } catch (e) {
      alert(e.message);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleIterate = async () => {
    if (!iterateText.trim()) return;
    setIsIterating(true);
    try {
      await apiCall(`/${project.id}/iterate`, {
        method: 'POST',
        body: JSON.stringify({ change_description: iterateText }),
      });
      setIterateText('');
      await onRefresh();
    } catch (e) {
      alert(e.message);
    } finally {
      setIsIterating(false);
    }
  };

  const fileToDataUrl = (file) => new Promise((res, rej) => {
    const fr = new FileReader(); fr.onload = () => res(fr.result); fr.onerror = rej; fr.readAsDataURL(file);
  });
  const onFloorPlan = async (e) => {
    const f = e.target.files?.[0]; e.target.value = '';
    if (f) setFloorPlan(await fileToDataUrl(f));
  };
  const onAddSketch = async (e) => {
    const f = e.target.files?.[0]; e.target.value = '';
    if (f) { const data = await fileToDataUrl(f); setSketches(prev => [...prev, { label: `Pared ${prev.length + 1}`, data }]); }
  };
  const handleCompose = async () => {
    if (!floorPlan && sketches.length === 0) { alert('Adjunta el plano en planta o al menos un boceto de pared.'); return; }
    setIsComposing(true);
    try {
      const labelNote = sketches.length
        ? 'Bocetos por pared (en orden): ' + sketches.map((s, i) => `${i + 1}) ${s.label || 'pared'}`).join('; ') + '.'
        : '';
      await apiCall(`/${project.id}/render-compose`, {
        method: 'POST',
        body: JSON.stringify({
          floor_plan: floorPlan,
          wall_sketches: sketches.map(s => s.data),
          brief: [composeBrief, labelNote].filter(Boolean).join(' '),
        }),
      });
      await onRefresh();
    } catch (e) {
      alert(e.message);
    } finally {
      setIsComposing(false);
    }
  };

  const renders = project.renders || [];

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6">
      <h3 className="text-lg font-bold text-slate-800 mb-4">Renders 3D</h3>

      <div className="flex gap-3 mb-4">
        <button onClick={handleGenerate} disabled={isGenerating}
          className="flex items-center gap-2 px-5 py-2.5 bg-indigo-600 text-white rounded-lg font-bold text-sm hover:bg-indigo-700 disabled:opacity-50">
          {isGenerating ? <Loader className="animate-spin" size={16} /> : <Wand2 size={16} />}
          {isGenerating ? 'Generando...' : 'Generar Render'}
        </button>
      </div>

      {/* Render FIEL: plano en planta + un boceto por pared (IA multi-referencia) */}
      <div className="mb-5 rounded-xl border-2 border-indigo-100 bg-indigo-50/40 p-4">
        <div className="flex items-center gap-2 mb-1">
          <Wand2 size={16} className="text-indigo-600" />
          <h4 className="font-bold text-slate-800 text-sm">Render fiel: plano + bocetos por pared</h4>
        </div>
        <p className="text-xs text-slate-500 mb-3">Sube el plano en planta y un boceto de cada pared; la IA genera un render fotorrealista fiel a la distribución y a cada pared.</p>

        {/* Plano en planta */}
        <div className="mb-3">
          <span className="block text-[11px] font-bold text-slate-600 uppercase tracking-wide mb-1">Plano en planta</span>
          {floorPlan ? (
            <div className="relative inline-block">
              <img src={floorPlan} alt="Plano" className="h-24 rounded-lg border border-slate-200 object-cover" />
              <button onClick={() => setFloorPlan(null)} className="absolute -top-2 -right-2 bg-white border border-slate-200 rounded-full p-0.5 shadow" title="Quitar"><X size={12} /></button>
            </div>
          ) : (
            <label className="inline-flex items-center gap-2 px-3 py-2 bg-white border-2 border-dashed border-slate-300 rounded-lg text-xs font-bold text-slate-600 cursor-pointer hover:border-indigo-400">
              <Upload size={14} /> Subir plano (imagen o PDF)
              <input type="file" accept="image/*,application/pdf" onChange={onFloorPlan} className="hidden" />
            </label>
          )}
        </div>

        {/* Bocetos por pared */}
        <div className="mb-3">
          <span className="block text-[11px] font-bold text-slate-600 uppercase tracking-wide mb-1">Bocetos por pared</span>
          <div className="flex flex-wrap gap-3">
            {sketches.map((s, i) => (
              <div key={i} className="w-28">
                <div className="relative">
                  <img src={s.data} alt={`Boceto ${i + 1}`} className="h-20 w-28 rounded-lg border border-slate-200 object-cover" />
                  <button onClick={() => setSketches(prev => prev.filter((_, idx) => idx !== i))} className="absolute -top-2 -right-2 bg-white border border-slate-200 rounded-full p-0.5 shadow" title="Quitar"><X size={12} /></button>
                </div>
                <input value={s.label} onChange={e => setSketches(prev => prev.map((x, idx) => idx === i ? { ...x, label: e.target.value } : x))}
                  className="mt-1 w-full px-2 py-1 border border-slate-200 rounded text-[11px]" placeholder={`Pared ${i + 1}`} />
              </div>
            ))}
            <label className="h-20 w-28 flex flex-col items-center justify-center gap-1 bg-white border-2 border-dashed border-slate-300 rounded-lg text-[11px] font-bold text-slate-500 cursor-pointer hover:border-indigo-400">
              <Upload size={14} /> Añadir boceto
              <input type="file" accept="image/*" onChange={onAddSketch} className="hidden" />
            </label>
          </div>
        </div>

        {/* Brief de acabados */}
        <textarea value={composeBrief} onChange={e => setComposeBrief(e.target.value)} rows={2}
          className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm mb-3"
          placeholder="Acabados deseados: colores, materiales, estilo… (ej: 'frentes verde salvia mate, encimera porcelánico blanco, tiradores gola negros, suelo madera clara')" />

        <button onClick={handleCompose} disabled={isComposing}
          className="flex items-center gap-2 px-5 py-2.5 bg-emerald-600 text-white rounded-lg font-bold text-sm hover:bg-emerald-700 disabled:opacity-50">
          {isComposing ? <Loader className="animate-spin" size={16} /> : <Wand2 size={16} />}
          {isComposing ? 'Generando render fiel…' : 'Generar render fiel (IA)'}
        </button>
      </div>

      {renders.length > 0 && (
        <div className="mb-4 flex gap-2">
          <input type="text" value={iterateText} onChange={e => setIterateText(e.target.value)}
            className="flex-1 px-3 py-2 border border-slate-300 rounded-lg text-sm"
            placeholder="Describe el cambio (ej: 'cambiar encimera a granito negro')" />
          <button onClick={handleIterate} disabled={isIterating || !iterateText.trim()}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg font-bold text-sm hover:bg-purple-700 disabled:opacity-50">
            {isIterating ? 'Iterando...' : 'Iterar'}
          </button>
        </div>
      )}

      {renders.length === 0 ? (
        <div className="text-center py-8 text-slate-400">
          <Wand2 size={40} className="mx-auto mb-2" />
          <p>No hay renders generados aún</p>
          <p className="text-xs mt-1">Añade fotos, medidas y muebles, luego genera el render</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {renders.map(r => {
            const img = renderImageSrc(r);
            return (
            <div key={r.id} className="border border-slate-200 rounded-lg overflow-hidden">
              {img ? (
                <a href={assetSrc(img)} target="_blank" rel="noreferrer" title="Ver a tamaño completo">
                  <img src={assetSrc(img)} alt="Render" className="w-full h-48 object-cover hover:opacity-90 transition-opacity" />
                </a>
              ) : (
                <div className="w-full h-48 bg-slate-100 flex flex-col items-center justify-center text-slate-400 gap-1">
                  <Image size={32} />
                  <span className="text-[10px]">{r.status === 'failed' ? 'Render fallido' : 'Sin imagen'}</span>
                </div>
              )}
              <div className="p-3">
                <div className="flex items-center justify-between">
                  <span className={`text-xs px-2 py-0.5 rounded ${r.status === 'completed' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                    {r.status}
                  </span>
                  {r.is_iteration && <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded">Iteración</span>}
                </div>
                {r.change_request && <p className="text-xs text-slate-500 mt-1">Cambio: {r.change_request}</p>}
              </div>
            </div>
            );
          })}
        </div>
      )}
    </div>
  );
}


// ─── Tab: Documentación Técnica ──────────────────────────────────────────────
function TechnicalDocsTab({ project, onRefresh }) {
  const [library, setLibrary] = useState('ZC');
  const [isApproving, setIsApproving] = useState(false);
  const [expandedDoc, setExpandedDoc] = useState(null);

  const handleApprove = async () => {
    const renders = project.renders || [];
    if (!renders.length) {
      alert('Genera al menos un render antes de aprobar');
      return;
    }
    const measurements = project.measurements || [];
    if (!measurements.length) {
      alert('Añade medidas de al menos una pared antes de aprobar');
      return;
    }

    setIsApproving(true);
    try {
      await apiCall(`/${project.id}/approve`, {
        method: 'POST',
        body: JSON.stringify({ render_id: renders[renders.length - 1].id, library }),
      });
      await onRefresh();
    } catch (e) {
      alert(e.message);
    } finally {
      setIsApproving(false);
    }
  };

  const docs = project.technical_docs || [];

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6">
      <h3 className="text-lg font-bold text-slate-800 mb-4">Documentación Técnica</h3>

      {project.status !== 'approved' ? (
        <div className="mb-6">
          <p className="text-sm text-slate-500 mb-4">
            Cuando estés satisfecho con el diseño, aprueba el proyecto para generar automáticamente:
            plano de instalaciones, alzado alámbrico con cotas y despiece con valoración.
          </p>
          <div className="flex items-center gap-3">
            <select value={library} onChange={e => setLibrary(e.target.value)}
              className="px-3 py-2 border border-slate-300 rounded-lg text-sm">
              <option value="ZC">Biblioteca ZC (1.00€/punto)</option>
              <option value="MV">Biblioteca MV (1.15€/punto)</option>
            </select>
            <button onClick={handleApprove} disabled={isApproving}
              className="flex items-center gap-2 px-5 py-2.5 bg-green-600 text-white rounded-lg font-bold text-sm hover:bg-green-700 disabled:opacity-50">
              {isApproving ? <Loader className="animate-spin" size={16} /> : <CheckCircle size={16} />}
              {isApproving ? 'Generando docs...' : 'Aprobar y Generar Documentación'}
            </button>
          </div>
        </div>
      ) : null}

      {docs.length === 0 && project.status === 'approved' && (
        <p className="text-slate-500 text-sm">Documentación generada. Revisa los documentos a continuación.</p>
      )}

      {docs.length > 0 && (
        <div className="space-y-4">
          {docs.map(doc => (
            <div key={doc.id} className="border border-slate-200 rounded-lg overflow-hidden">
              <button
                onClick={() => setExpandedDoc(expandedDoc === doc.id ? null : doc.id)}
                className="w-full flex items-center justify-between p-4 hover:bg-slate-50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <FileText size={18} className="text-indigo-600" />
                  <span className="font-bold text-slate-700">
                    {doc.doc_type === 'installation_plan' && 'Plano de Instalaciones'}
                    {doc.doc_type === 'wireframe_elevation' && 'Alzado Alámbrico con Cotas'}
                    {doc.doc_type === 'cabinet_breakdown' && 'Despiece y Valoración'}
                  </span>
                  {doc.total_value && (
                    <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded font-bold">
                      {doc.total_value.toFixed(2)}€
                    </span>
                  )}
                </div>
                {expandedDoc === doc.id ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
              </button>

              {expandedDoc === doc.id && (
                <div className="p-4 border-t border-slate-200 bg-slate-50">
                  {doc.doc_type === 'installation_plan' && (
                    <div className="space-y-3">
                      {(doc.content?.walls || []).map((wall, i) => (
                        <div key={i} className="bg-white p-3 rounded-lg border border-slate-200">
                          <h5 className="font-bold text-sm text-slate-700 mb-2">{wall.wall} ({wall.dimensions?.width}x{wall.dimensions?.height}cm)</h5>
                          {wall.outlets?.length > 0 && (
                            <div className="mb-2">
                              <span className="text-xs font-bold text-amber-700">Enchufes:</span>
                              {wall.outlets.map((o, j) => (
                                <span key={j} className="text-xs ml-2 bg-amber-50 px-2 py-0.5 rounded">
                                  {o.description}: x={o.x}cm, y={o.y}cm
                                </span>
                              ))}
                            </div>
                          )}
                          {wall.waterConnections?.length > 0 && (
                            <div>
                              <span className="text-xs font-bold text-blue-700">Tomas agua:</span>
                              {wall.waterConnections.map((w, j) => (
                                <span key={j} className="text-xs ml-2 bg-blue-50 px-2 py-0.5 rounded">
                                  {w.description}: x={w.x}cm, y={w.y}cm
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}

                  {doc.doc_type === 'wireframe_elevation' && (
                    <div className="space-y-4">
                      {(doc.content?.walls || []).map((svg, i) => (
                        <div key={i} className="bg-white p-3 rounded-lg border border-slate-200 overflow-x-auto"
                          dangerouslySetInnerHTML={{ __html: svg }} />
                      ))}
                    </div>
                  )}

                  {doc.doc_type === 'cabinet_breakdown' && (
                    <div>
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b border-slate-300">
                            <th className="text-left py-2 px-2 font-bold text-slate-700">Mueble</th>
                            <th className="text-left py-2 px-2 font-bold text-slate-700">Pared</th>
                            <th className="text-left py-2 px-2 font-bold text-slate-700">Medidas</th>
                            <th className="text-left py-2 px-2 font-bold text-slate-700">Material</th>
                            <th className="text-right py-2 px-2 font-bold text-slate-700">Puntos</th>
                            <th className="text-right py-2 px-2 font-bold text-slate-700">Precio</th>
                          </tr>
                        </thead>
                        <tbody>
                          {(doc.content?.items || []).map((item, i) => (
                            <tr key={i} className="border-b border-slate-100">
                              <td className="py-2 px-2">{item.cabinetType}</td>
                              <td className="py-2 px-2 text-slate-500">{item.wall}</td>
                              <td className="py-2 px-2 text-slate-500">{item.dimensions}</td>
                              <td className="py-2 px-2 text-slate-500">{item.material}</td>
                              <td className="py-2 px-2 text-right">{item.points}</td>
                              <td className="py-2 px-2 text-right font-bold">{item.price?.toFixed(2)}€</td>
                            </tr>
                          ))}
                        </tbody>
                        <tfoot>
                          <tr className="border-t-2 border-slate-300">
                            <td colSpan={4} className="py-2 px-2 font-bold text-slate-800">TOTAL ({doc.content?.items?.[0]?.library || 'ZC'})</td>
                            <td className="py-2 px-2 text-right font-bold">{doc.content?.totalPoints}</td>
                            <td className="py-2 px-2 text-right font-black text-lg text-green-700">{doc.content?.totalPrice?.toFixed(2)}€</td>
                          </tr>
                        </tfoot>
                      </table>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
