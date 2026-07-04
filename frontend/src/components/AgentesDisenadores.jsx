/**
 * AgentesDisenadores.jsx
 * Panel de agentes diseñadores en paralelo — lanza 1-7 proyectos simultáneos,
 * cada uno con su propio agente IA que genera un render fotorrealista.
 * Hace polling automático cada 8 segundos hasta que todos completan.
 */
import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Sparkles, Plus, Trash2, Play, RefreshCw, Download, CheckCircle,
  AlertCircle, Clock, Loader, X, ChevronDown, ChevronUp, ZoomIn, Upload, Image
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL || '';

function getToken() {
  try {
    return localStorage.getItem('luiggi_access_token')
      || localStorage.getItem('token')
      || localStorage.getItem('access_token')
      || '';
  } catch { return ''; }
}

// Las imágenes del motor Manus llegan como ruta del proxy interno sin prefijo de
// API ni token; un <img> no puede enviar cabeceras, así que el JWT viaja por query.
// Las de Gemini (IA 2) son data URLs y se devuelven tal cual.
function imgSrc(url) {
  if (!url || typeof url !== 'string') return url;
  if (url.startsWith('data:') || url.startsWith('blob:') || url.startsWith('http')) return url;
  if (url.startsWith('/api/ai-engine/asset')) {
    const sep = url.includes('?') ? '&' : '?';
    return `${API}${url}${sep}t=${encodeURIComponent(getToken() || '')}`;
  }
  return url.startsWith('/api/') ? `${API}${url}` : url;
}

// Descarga robusta (blob) para servir tanto data URLs como rutas del proxy con token.
async function downloadImg(url, filename) {
  try {
    const resp = await fetch(imgSrc(url));
    const blob = await resp.blob();
    const href = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = href; a.download = filename || 'render.jpg';
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(href), 4000);
  } catch { window.open(imgSrc(url), '_blank'); }
}

async function apiPost(endpoint, body) {
  const res = await fetch(`${API}/api/estudio-cocinas${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${getToken()}` },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || `Error ${res.status}`);
  return data;
}

async function apiGet(endpoint) {
  const res = await fetch(`${API}/api/estudio-cocinas${endpoint}`, {
    headers: { Authorization: `Bearer ${getToken()}` },
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || `Error ${res.status}`);
  return data;
}

const ESTILOS = ['Moderno', 'Nórdico', 'Industrial', 'Clásico', 'Lacado Blanco', 'Madera Natural', 'Contemporáneo'];

// Comprime/redimensiona una imagen (foto/croquis) a un tamaño manejable antes de
// enviarla en base64. Una foto de móvil son varios MB y hace que la petición JSON
// se corte ("NetworkError"); aquí la reducimos a ~1600px y JPEG de calidad media.
function compressImage(file, maxDim = 1600, quality = 0.82) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const img = new window.Image();
      img.onload = () => {
        let { width, height } = img;
        if (width > maxDim || height > maxDim) {
          const r = Math.min(maxDim / width, maxDim / height);
          width = Math.round(width * r); height = Math.round(height * r);
        }
        try {
          const canvas = document.createElement('canvas');
          canvas.width = width; canvas.height = height;
          canvas.getContext('2d').drawImage(img, 0, 0, width, height);
          resolve(canvas.toDataURL('image/jpeg', quality));
        } catch (e) { resolve(reader.result); } // si falla el canvas, usa el original
      };
      img.onerror = () => resolve(reader.result);
      img.src = reader.result;
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

const PROYECTO_VACIO = () => ({
  id: Date.now() + Math.random(),
  nombre_cliente: '',
  medidas: '400×350cm',
  estilo: 'Moderno',
  descripcion: '',
  presupuesto: '',
  notas: '',
  croquis: null,
  croquisPrev: null,
});

function StatusIcon({ status }) {
  if (status === 'running') return <Loader size={16} className="animate-spin text-amber-500" />;
  if (status === 'completed') return <CheckCircle size={16} className="text-emerald-500" />;
  if (status === 'error') return <AlertCircle size={16} className="text-rose-500" />;
  return <Clock size={16} className="text-slate-400" />;
}

function ProyectoCard({ proyecto, index, onChange, onRemove, canRemove }) {
  const [expanded, setExpanded] = useState(index === 0);
  const fileRef = useRef(null);

  const onFileChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const dataUrl = await compressImage(file);
      onChange({ ...proyecto, croquis: file, croquisPrev: dataUrl });
    } catch {
      const reader = new FileReader();
      reader.onload = () => onChange({ ...proyecto, croquis: file, croquisPrev: reader.result });
      reader.readAsDataURL(file);
    }
  };

  const removeCroquis = (e) => {
    e.stopPropagation();
    onChange({ ...proyecto, croquis: null, croquisPrev: null });
  };
  return (
    <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-sm">
      <div
        className="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-slate-50"
        onClick={() => setExpanded(e => !e)}
      >
        <div className="w-7 h-7 rounded-full bg-amber-100 text-amber-700 flex items-center justify-center text-xs font-black flex-shrink-0">
          {index + 1}
        </div>
        <span className="flex-1 font-bold text-slate-700 text-sm truncate">
          {proyecto.nombre_cliente || `Proyecto ${index + 1}`}
        </span>
        <span className="text-xs text-slate-400 hidden sm:block">{proyecto.estilo} · {proyecto.medidas}</span>
        {canRemove && (
          <button
            onClick={e => { e.stopPropagation(); onRemove(); }}
            className="p-1 text-rose-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg"
          >
            <Trash2 size={14} />
          </button>
        )}
        {expanded ? <ChevronUp size={16} className="text-slate-400" /> : <ChevronDown size={16} className="text-slate-400" />}
      </div>

      {expanded && (
        <div className="px-4 pb-4 grid grid-cols-1 sm:grid-cols-2 gap-3 border-t border-slate-100 pt-3">
          <div>
            <label className="text-[10px] font-black text-slate-400 uppercase tracking-wider block mb-1">Cliente *</label>
            <input
              value={proyecto.nombre_cliente}
              onChange={e => onChange({ ...proyecto, nombre_cliente: e.target.value })}
              placeholder="Nombre del cliente"
              className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-400"
            />
          </div>
          <div>
            <label className="text-[10px] font-black text-slate-400 uppercase tracking-wider block mb-1">Medidas</label>
            <input
              value={proyecto.medidas}
              onChange={e => onChange({ ...proyecto, medidas: e.target.value })}
              placeholder="400×350cm isla 200×100cm"
              className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-400"
            />
          </div>
          <div>
            <label className="text-[10px] font-black text-slate-400 uppercase tracking-wider block mb-1">Estilo</label>
            <select
              value={proyecto.estilo}
              onChange={e => onChange({ ...proyecto, estilo: e.target.value })}
              className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-400 bg-white"
            >
              {ESTILOS.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <div>
            <label className="text-[10px] font-black text-slate-400 uppercase tracking-wider block mb-1">Presupuesto</label>
            <input
              value={proyecto.presupuesto}
              onChange={e => onChange({ ...proyecto, presupuesto: e.target.value })}
              placeholder="Ej: 18.000€"
              className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-400"
            />
          </div>
          <div className="sm:col-span-2">
            <label className="text-[10px] font-black text-slate-400 uppercase tracking-wider block mb-1">Descripción</label>
            <textarea
              value={proyecto.descripcion}
              onChange={e => onChange({ ...proyecto, descripcion: e.target.value })}
              placeholder="Encimera calacatta, puertas en zenit by alvic, perfil gola…"
              rows={2}
              className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-400 resize-none"
            />
          </div>
          <div className="sm:col-span-2">
            <label className="text-[10px] font-black text-slate-400 uppercase tracking-wider block mb-1">Materiales / Notas</label>
            <input
              value={proyecto.notas}
              onChange={e => onChange({ ...proyecto, notas: e.target.value })}
              placeholder="Encimera silestone, frentes lacados en mate…"
              className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-400"
            />
          </div>
          {/* Subida de croquis/plano */}
          <div className="sm:col-span-2">
            <label className="text-[10px] font-black text-slate-400 uppercase tracking-wider block mb-1">Croquis / Plano / Foto</label>
            {proyecto.croquisPrev ? (
              <div className="relative inline-block">
                <img src={proyecto.croquisPrev} alt="Croquis" className="h-20 rounded-lg object-contain border border-slate-200" />
                <button onClick={removeCroquis} className="absolute -top-1.5 -right-1.5 bg-rose-500 text-white rounded-full p-0.5 shadow">
                  <X size={10} />
                </button>
              </div>
            ) : (
              <button
                type="button"
                onClick={() => fileRef.current?.click()}
                className="flex items-center gap-2 px-3 py-2 border-2 border-dashed border-slate-300 rounded-xl text-sm text-slate-500 hover:border-amber-400 hover:text-amber-600 transition-colors w-full justify-center"
              >
                <Upload size={14} /> Subir croquis a boli, foto o plano
              </button>
            )}
            <input ref={fileRef} type="file" accept="image/*" className="hidden" onChange={onFileChange} />
          </div>
        </div>
      )}
    </div>
  );
}

function ResultadoCard({ agente, onZoom }) {
  const statusColor = {
    running: 'border-amber-300 bg-amber-50',
    completed: 'border-emerald-300 bg-emerald-50',
    error: 'border-rose-300 bg-rose-50',
    pending: 'border-slate-200 bg-slate-50',
  }[agente.status] || 'border-slate-200 bg-slate-50';

  return (
    <div className={`rounded-2xl border-2 overflow-hidden ${statusColor} transition-all duration-300`}>
      <div className="flex items-center gap-2 px-4 py-3">
        <StatusIcon status={agente.status} />
        <span className="font-bold text-slate-800 text-sm flex-1 truncate">{agente.nombre_cliente}</span>
        <span className="text-xs text-slate-500">{agente.estilo}</span>
      </div>

      {agente.status === 'running' && (
        <div className="px-4 pb-4">
          <div className="h-1.5 bg-amber-200 rounded-full overflow-hidden">
            <div className="h-full bg-amber-500 rounded-full animate-pulse" style={{ width: '60%' }} />
          </div>
          <p className="text-xs text-amber-700 mt-2 font-medium">Generando render… puede tardar 1-3 minutos</p>
        </div>
      )}

      {agente.status === 'completed' && agente.imageUrl && (
        <div className="relative group">
          <img
            src={imgSrc(agente.imageUrl)}
            alt={`Render ${agente.nombre_cliente}`}
            className="w-full object-cover"
            style={{ maxHeight: '220px', objectFit: 'cover' }}
          />
          <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-all flex items-center justify-center gap-2 opacity-0 group-hover:opacity-100">
            <button
              onClick={() => onZoom(agente.imageUrl, agente.nombre_cliente)}
              className="p-2 bg-white rounded-xl shadow-lg hover:bg-slate-100"
            >
              <ZoomIn size={18} className="text-slate-800" />
            </button>
            <button
              onClick={() => downloadImg(agente.imageUrl, `render_${agente.nombre_cliente.replace(/\s+/g, '_')}.jpg`)}
              className="p-2 bg-white rounded-xl shadow-lg hover:bg-slate-100"
            >
              <Download size={18} className="text-slate-800" />
            </button>
          </div>
          <div className="px-4 py-2 bg-white border-t border-slate-100 flex items-center justify-between">
            <span className="text-xs text-emerald-600 font-bold">✓ Completado</span>
            {agente.duracion_segundos && (
              <span className="text-xs text-slate-400">{agente.duracion_segundos}s</span>
            )}
          </div>
        </div>
      )}

      {agente.status === 'completed' && !agente.imageUrl && (
        <div className="px-4 pb-4">
          <p className="text-xs text-slate-500 italic">El agente completó pero no generó imagen. Intenta de nuevo.</p>
        </div>
      )}

      {agente.status === 'error' && (
        <div className="px-4 pb-4">
          <p className="text-xs text-rose-600 font-medium">{agente.error || 'Error desconocido'}</p>
        </div>
      )}
    </div>
  );
}

export default function AgentesDisenadores({ state }) {
  const [proyectos, setProyectos] = useState([PROYECTO_VACIO()]);
  const [agentes, setAgentes] = useState([]); // resultados con task_id + status
  const [lanzando, setLanzando] = useState(false);
  const [error, setError] = useState('');
  const [zoom, setZoom] = useState(null); // { url, nombre }
  const [motor, setMotor] = useState('ia1'); // 'ia1' = principal, 'ia2' = alternativo
  const pollingRef = useRef(null);

  // Polling automático cada 8 segundos mientras haya agentes en running
  const hacerPolling = useCallback(async (agentesActuales) => {
    const pendientes = agentesActuales.filter(a => a.status === 'running' && a.task_id);
    if (pendientes.length === 0) return agentesActuales;

    try {
      const resp = await apiPost('/agentes/lote-estado', {
        task_ids: pendientes.map(a => a.task_id),
      });
      const mapaEstados = {};
      (resp.agentes || []).forEach(r => { mapaEstados[r.task_id] = r; });

      return agentesActuales.map(a => {
        if (!a.task_id || !mapaEstados[a.task_id]) return a;
        const nuevo = mapaEstados[a.task_id];
        return { ...a, ...nuevo };
      });
    } catch (e) {
      return agentesActuales;
    }
  }, []);

  useEffect(() => {
    const hayRunning = agentes.some(a => a.status === 'running');
    if (!hayRunning) {
      if (pollingRef.current) clearInterval(pollingRef.current);
      return;
    }

    pollingRef.current = setInterval(async () => {
      setAgentes(prev => {
        hacerPolling(prev).then(actualizados => {
          setAgentes(actualizados);
        });
        return prev;
      });
    }, 8000);

    return () => { if (pollingRef.current) clearInterval(pollingRef.current); };
  }, [agentes, hacerPolling]);

  const lanzarAgentes = async () => {
    const validos = proyectos.filter(p => p.nombre_cliente.trim());
    if (validos.length === 0) {
      setError('Añade al menos un proyecto con nombre de cliente.');
      return;
    }
    setError('');
    setLanzando(true);
    setAgentes([]);

    try {
      // Preparar proyectos con croquis en base64
      const proyectosPayload = validos.map(p => ({
        nombre_cliente: p.nombre_cliente,
        medidas: p.medidas,
        estilo: p.estilo,
        descripcion: p.descripcion,
        presupuesto: p.presupuesto,
        notas: p.notas,
        croquis_b64: p.croquisPrev || null,
      }));
      const resp = await apiPost('/agentes/lanzar', { proyectos: proyectosPayload, provider: motor === 'ia2' ? 'gemini' : 'manus' });
      const agentesIniciales = (resp.agentes || []).map(a => ({
        ...a,
        estilo: validos.find(p => p.nombre_cliente === a.nombre_cliente)?.estilo || 'Moderno',
      }));
      setAgentes(agentesIniciales);
    } catch (e) {
      setError(e.message || 'Error al lanzar los agentes');
    } finally {
      setLanzando(false);
    }
  };

  const agregarProyecto = () => {
    if (proyectos.length >= 7) return;
    setProyectos(p => [...p, PROYECTO_VACIO()]);
  };

  const eliminarProyecto = (id) => {
    setProyectos(p => p.filter(x => x.id !== id));
  };

  const actualizarProyecto = (id, datos) => {
    setProyectos(p => p.map(x => x.id === id ? { ...x, ...datos } : x));
  };

  const completados = agentes.filter(a => a.status === 'completed').length;
  const running = agentes.filter(a => a.status === 'running').length;
  const hayResultados = agentes.length > 0;

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* Header */}
      <div className="bg-gradient-to-r from-amber-600 to-orange-600 px-4 sm:px-6 py-3 sm:py-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center">
            <Sparkles size={22} className="text-white" />
          </div>
          <div>
            <h1 className="text-xl font-black text-white">Agentes Diseñadores</h1>
            <p className="text-amber-100 text-xs">Lanza hasta 7 proyectos de diseño en paralelo con IA</p>
          </div>
        </div>
        {hayResultados && (
          <div className="flex items-center gap-3 text-sm">
            <span className="bg-white/20 px-3 py-1 rounded-full font-bold">
              {completados}/{agentes.length} completados
            </span>
            {running > 0 && (
              <span className="flex items-center gap-1.5 bg-amber-500/30 px-3 py-1 rounded-full font-bold">
                <Loader size={13} className="animate-spin" /> {running} en proceso
              </span>
            )}
          </div>
        )}
      </div>

      <div className="max-w-7xl mx-auto px-3 sm:px-4 py-4 sm:py-6 grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
        {/* Panel izquierdo: configuración de proyectos */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-black text-slate-300 uppercase tracking-wider">
              Proyectos ({proyectos.length}/7)
            </h2>
            <button
              onClick={agregarProyecto}
              disabled={proyectos.length >= 7}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-amber-600 text-white rounded-xl text-xs font-bold hover:bg-amber-700 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <Plus size={14} /> Añadir proyecto
            </button>
          </div>

          <div className="space-y-3">
            {proyectos.map((p, i) => (
              <ProyectoCard
                key={p.id}
                proyecto={p}
                index={i}
                onChange={datos => actualizarProyecto(p.id, datos)}
                onRemove={() => eliminarProyecto(p.id)}
                canRemove={proyectos.length > 1}
              />
            ))}
          </div>

          {error && (
            <div className="flex items-center gap-2 px-4 py-3 bg-rose-900/30 border border-rose-700 rounded-xl text-rose-300 text-sm">
              <AlertCircle size={16} className="flex-shrink-0" />
              {error}
            </div>
          )}

          <div className="flex items-center justify-between gap-2 px-1">
            <span className="text-[11px] font-black text-slate-400 uppercase tracking-wider">Motor</span>
            <div className="flex bg-slate-800 rounded-lg p-1">
              {[['ia1', 'IA 1'], ['ia2', 'IA 2']].map(([id, lbl]) => (
                <button key={id} onClick={() => setMotor(id)} title={id === 'ia1' ? 'Motor principal' : 'Motor alternativo (más rápido y estable)'}
                  className={`px-3 py-1 rounded-md text-xs font-black transition-all ${motor === id ? 'bg-amber-500 text-white' : 'text-slate-400 hover:bg-slate-700'}`}>{lbl}</button>
              ))}
            </div>
          </div>

          <button
            onClick={lanzarAgentes}
            disabled={lanzando || proyectos.filter(p => p.nombre_cliente.trim()).length === 0}
            className="w-full flex items-center justify-center gap-2 py-3 sm:py-4 bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-2xl font-black text-sm sm:text-base hover:from-amber-600 hover:to-orange-600 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-amber-900/30 transition-all"
          >
            {lanzando
              ? <><Loader size={18} className="animate-spin" /> Lanzando agentes…</>
              : <><Play size={18} /> Lanzar {proyectos.filter(p => p.nombre_cliente.trim()).length} agente{proyectos.filter(p => p.nombre_cliente.trim()).length !== 1 ? 's' : ''} en paralelo</>
            }
          </button>

          <p className="text-xs text-slate-500 text-center">
            Cada agente genera un render fotorrealista de forma independiente.
            El proceso puede tardar 1-3 minutos por proyecto.
          </p>
        </div>

        {/* Panel derecho: resultados */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-black text-slate-300 uppercase tracking-wider">
              Resultados
            </h2>
            {hayResultados && running > 0 && (
              <button
                onClick={() => hacerPolling(agentes).then(setAgentes)}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-700 text-slate-300 rounded-xl text-xs font-bold hover:bg-slate-600"
              >
                <RefreshCw size={13} /> Actualizar
              </button>
            )}
          </div>

          {!hayResultados && (
            <div className="flex flex-col items-center justify-center h-48 sm:h-64 bg-slate-900 rounded-2xl border border-slate-800 text-slate-500">
              <Sparkles size={40} className="mb-3 opacity-30" />
              <p className="text-sm font-medium">Los renders aparecerán aquí</p>
              <p className="text-xs mt-1 opacity-70">Configura los proyectos y pulsa Lanzar</p>
            </div>
          )}

          {hayResultados && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {agentes.map(a => (
                <ResultadoCard
                  key={a.task_id || a.nombre_cliente}
                  agente={a}
                  onZoom={(url, nombre) => setZoom({ url, nombre })}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Modal zoom */}
      {zoom && (
        <div
          className="fixed inset-0 bg-black/90 z-[200] flex items-center justify-center p-4"
          onClick={() => setZoom(null)}
        >
          <div className="relative max-w-4xl w-full" onClick={e => e.stopPropagation()}>
            <img
              src={imgSrc(zoom.url)}
              alt={zoom.nombre}
              className="w-full rounded-2xl shadow-2xl"
            />
            <div className="absolute top-3 left-3 bg-black/60 text-white px-3 py-1.5 rounded-xl text-sm font-bold backdrop-blur">
              {zoom.nombre}
            </div>
            <button
              onClick={() => setZoom(null)}
              className="absolute top-3 right-3 p-2 bg-black/60 text-white rounded-xl hover:bg-black/80 backdrop-blur"
            >
              <X size={18} />
            </button>
            <button
              onClick={(e) => { e.stopPropagation(); downloadImg(zoom.url, `render_${zoom.nombre.replace(/\s+/g, '_')}.jpg`); }}
              className="absolute bottom-3 right-3 flex items-center gap-2 px-4 py-2 bg-amber-500 text-white rounded-xl font-bold text-sm hover:bg-amber-600"
            >
              <Download size={15} /> Descargar
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
