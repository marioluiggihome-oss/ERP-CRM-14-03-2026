/**
 * 3D Estudio — Módulo unificado de diseño de cocinas
 * ====================================================
 * Todas las capacidades de IA (render, edición, transcripción)
 * pasan exclusivamente por Manus API a través del backend LuiggiAI.
 *
 * Pestañas:
 *   1. Render Manus   → Render fotorrealista por texto, voz o croquis
 *   2. Plano 2D       → Plano técnico acotado desde medidas en texto libre
 *   3. Ficha Técnica  → Ficha de materiales y plazos en Markdown
 *   4. Presentación   → HTML de presentación para cliente
 *
 * Temas: Día / Noche / Auto (sistema operativo)
 */

import React, { useState, useRef, useCallback, useEffect } from 'react';
import {
  ChefHat, Image, FileText, Mic, MicOff, Upload,
  Download, Loader2, RefreshCw, Maximize2, X,
  CheckCircle, AlertCircle, Sparkles, Edit3, ZoomIn,
  Presentation, Eye, Sun, Moon, Monitor
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL || '';

// ─── Temas ────────────────────────────────────────────────────────────────────
const THEMES = {
  day: {
    root:        'bg-white text-slate-800',
    header:      'bg-white border-b border-slate-200',
    sidebar:     'bg-slate-50 border-r border-slate-200',
    sidebarLabel:'text-slate-400',
    sidebarSect: 'text-slate-500',
    input:       'bg-white border border-slate-300 text-slate-800 placeholder-slate-400 focus:border-amber-500',
    select:      'bg-white border border-slate-300 text-slate-800 focus:border-amber-500',
    tabBar:      'bg-slate-50 border-b border-slate-200',
    tabActive:   'bg-amber-600 text-white',
    tabInactive: 'text-slate-500 hover:text-slate-800 hover:bg-slate-200',
    card:        'bg-white border border-slate-200',
    cardBorder:  'border-slate-200',
    pre:         'bg-slate-50 border border-slate-200 text-slate-700',
    micIdle:     'bg-slate-100 border border-slate-300 text-slate-500 hover:bg-amber-50 hover:text-amber-600 hover:border-amber-400',
    transcBg:    'bg-emerald-50 border border-emerald-200',
    transcText:  'text-emerald-700',
    transcLabel: 'text-emerald-600',
    statusLoad:  'bg-amber-50 text-amber-700 border border-amber-200',
    statusOk:    'bg-emerald-50 text-emerald-700 border border-emerald-200',
    statusErr:   'bg-red-50 text-red-700 border border-red-200',
    editBox:     'bg-slate-50 border border-slate-200',
    editLabel:   'text-amber-600',
    uploadBorder:'border-slate-300 hover:border-amber-400',
    uploadText:  'text-slate-400',
    dlBtn:       'bg-slate-100 border border-slate-200 text-slate-600 hover:bg-slate-200',
    presBtn:     'bg-amber-50 border border-amber-300 text-amber-700 hover:bg-amber-100',
    subtext:     'text-slate-500',
    code:        'text-amber-600 bg-amber-50',
    motorText:   'text-slate-400',
    title:       'text-slate-800',
  },
  night: {
    root:        'bg-[#0F0F0F] text-white',
    header:      'bg-[#111] border-b border-white/5',
    sidebar:     'bg-[#111] border-r border-white/5',
    sidebarLabel:'text-slate-600',
    sidebarSect: 'text-slate-600',
    input:       'bg-white/5 border border-white/10 text-white placeholder-slate-700 focus:border-amber-500/50',
    select:      'bg-[#1A1A1A] border border-white/10 text-white focus:border-amber-500/50',
    tabBar:      'bg-[#111] border-b border-white/5',
    tabActive:   'bg-amber-600 text-white',
    tabInactive: 'text-slate-500 hover:text-white hover:bg-white/5',
    card:        'bg-white/5 border border-white/10',
    cardBorder:  'border-white/10',
    pre:         'bg-white/5 border border-white/10 text-slate-300',
    micIdle:     'bg-white/5 border border-white/10 text-slate-400 hover:bg-amber-600/20 hover:text-amber-400 hover:border-amber-500/30',
    transcBg:    'bg-emerald-500/10 border border-emerald-500/20',
    transcText:  'text-slate-400',
    transcLabel: 'text-emerald-400',
    statusLoad:  'bg-amber-500/10 text-amber-400 border border-amber-500/20',
    statusOk:    'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20',
    statusErr:   'bg-red-500/10 text-red-400 border border-red-500/20',
    editBox:     'bg-white/5 border border-white/10',
    editLabel:   'text-amber-400',
    uploadBorder:'border-white/10 hover:border-amber-500/40',
    uploadText:  'text-slate-500',
    dlBtn:       'bg-black/70 border border-white/10 text-slate-300 hover:bg-black',
    presBtn:     'bg-amber-600/20 border border-amber-500/30 text-amber-400 hover:bg-amber-600/30',
    subtext:     'text-slate-500',
    code:        'text-amber-400 bg-amber-500/10',
    motorText:   'text-slate-600',
    title:       'text-white',
  },
};

function getSystemTheme() {
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'night' : 'day';
}

function getSavedThemeMode() {
  try { return localStorage.getItem('estudio3d_theme') || 'auto'; } catch { return 'auto'; }
}

// ─── Helper: llamada al backend ───────────────────────────────────────────────
function getToken() {
  try { return localStorage.getItem('token') || sessionStorage.getItem('token') || ''; } catch { return ''; }
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

async function apiPostForm(endpoint, formData) {
  const res = await fetch(`${API}/api/estudio-cocinas${endpoint}`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${getToken()}` },
    body: formData,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || `Error ${res.status}`);
  return data;
}

// ─── Badge de estado ──────────────────────────────────────────────────────────
function StatusBadge({ status, message, t }) {
  if (!message) return null;
  const cls = status === 'success' ? t.statusOk : status === 'error' ? t.statusErr : t.statusLoad;
  const icon = status === 'success'
    ? <CheckCircle size={13} className="flex-shrink-0" />
    : status === 'error'
    ? <AlertCircle size={13} className="flex-shrink-0" />
    : <Loader2 size={13} className="animate-spin flex-shrink-0" />;
  return (
    <div className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium ${cls}`}>
      {icon} {message}
    </div>
  );
}

// ─── Selector de tema ─────────────────────────────────────────────────────────
function ThemeSelector({ mode, onChange, t }) {
  const opts = [
    { id: 'day',   icon: <Sun size={13}/>,     label: 'Día' },
    { id: 'night', icon: <Moon size={13}/>,    label: 'Noche' },
    { id: 'auto',  icon: <Monitor size={13}/>, label: 'Auto' },
  ];
  return (
    <div className={`flex items-center gap-0.5 rounded-lg p-0.5 ${t.card}`}>
      {opts.map(o => (
        <button
          key={o.id}
          onClick={() => onChange(o.id)}
          title={o.label}
          className={`flex items-center gap-1 px-2 py-1 rounded-md text-[10px] font-black uppercase tracking-widest transition-all ${
            mode === o.id ? 'bg-amber-600 text-white' : `${t.tabInactive}`
          }`}
        >
          {o.icon} <span className="hidden sm:inline">{o.label}</span>
        </button>
      ))}
    </div>
  );
}

// ─── Componente principal ─────────────────────────────────────────────────────
export default function EstudioCocinas() {
  const [tab, setTab] = useState('render');
  const [themeMode, setThemeMode] = useState(getSavedThemeMode);
  const [systemTheme, setSystemTheme] = useState(getSystemTheme);

  // Escuchar cambios del sistema para modo Auto
  useEffect(() => {
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = e => setSystemTheme(e.matches ? 'night' : 'day');
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, []);

  const handleThemeChange = useCallback(mode => {
    setThemeMode(mode);
    try { localStorage.setItem('estudio3d_theme', mode); } catch {}
  }, []);

  const activeTheme = themeMode === 'auto' ? systemTheme : themeMode;
  const t = THEMES[activeTheme];

  const [proy, setProy] = useState({
    nombre_cliente: '',
    descripcion: '',
    estilo: 'Moderno',
    medidas: '400x350cm isla 200x100cm',
    presupuesto: '',
    notas: '',
  });

  const [render, setRender] = useState({ status: null, msg: '', imageUrl: null, croquis: null, croquisPrev: null, editMode: false, editTxt: '', fs: false });
  const [plano,  setPlano]  = useState({ status: null, msg: '', b64: null, fs: false });
  const [ficha,  setFicha]  = useState({ status: null, msg: '', md: '', ref: '' });
  const [pres,   setPres]   = useState({ status: null, msg: '', html: '', preview: false });
  const [rec,    setRec]    = useState(false);
  const [transcrito, setTranscrito] = useState('');
  const mrRef     = useRef(null);
  const chunksRef = useRef([]);
  const croquisRef = useRef(null);

  // ── Croquis ──
  const onCroquis = useCallback(e => {
    const f = e.target.files?.[0];
    if (!f) return;
    const fr = new FileReader();
    fr.onload = ev => setRender(s => ({ ...s, croquis: ev.target.result, croquisPrev: ev.target.result }));
    fr.readAsDataURL(f);
  }, []);

  // ── Voz ──
  const startRec = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream);
      chunksRef.current = [];
      mr.ondataavailable = e => chunksRef.current.push(e.data);
      mr.onstop = async () => {
        stream.getTracks().forEach(t => t.stop());
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        const fd = new FormData();
        fd.append('audio', blob, 'nota.webm');
        setRender(s => ({ ...s, status: 'loading', msg: 'Transcribiendo audio con Manus…' }));
        try {
          const r = await apiPostForm('/transcribir', fd);
          setTranscrito(r.texto || '');
          setProy(p => ({ ...p, descripcion: r.texto || p.descripcion }));
          setRender(s => ({ ...s, status: 'success', msg: 'Audio transcrito' }));
        } catch (err) {
          setRender(s => ({ ...s, status: 'error', msg: err.message }));
        }
      };
      mr.start();
      mrRef.current = mr;
      setRec(true);
    } catch {
      setRender(s => ({ ...s, status: 'error', msg: 'No se pudo acceder al micrófono' }));
    }
  }, []);

  const stopRec = useCallback(() => { mrRef.current?.stop(); setRec(false); }, []);

  // ── Render ──
  const genRender = useCallback(async () => {
    if (!proy.descripcion.trim()) {
      setRender(s => ({ ...s, status: 'error', msg: 'Escribe o dicta una descripción' }));
      return;
    }
    setRender(s => ({ ...s, status: 'loading', msg: 'Enviando a Manus… puede tardar 1-3 minutos', imageUrl: null }));
    try {
      const r = await apiPost('/render', {
        descripcion: proy.descripcion,
        estilo: proy.estilo,
        materiales: proy.notas,
        distribucion: proy.medidas,
        croquis_b64: render.croquis || null,
        modo_async: false,
      });
      setRender(s => ({ ...s, status: 'success', msg: 'Render generado por Manus', imageUrl: r.imageUrl }));
    } catch (err) {
      setRender(s => ({ ...s, status: 'error', msg: err.message }));
    }
  }, [proy, render.croquis]);

  const editRender = useCallback(async () => {
    if (!render.editTxt.trim()) return;
    setRender(s => ({ ...s, status: 'loading', msg: 'Editando render con Manus…' }));
    try {
      const r = await apiPost('/render/editar', { render_url: render.imageUrl, instruccion: render.editTxt, modo_async: false });
      setRender(s => ({ ...s, status: 'success', msg: 'Render editado', imageUrl: r.imageUrl, editMode: false, editTxt: '' }));
    } catch (err) {
      setRender(s => ({ ...s, status: 'error', msg: err.message }));
    }
  }, [render.imageUrl, render.editTxt]);

  // ── Plano ──
  const genPlano = useCallback(async () => {
    if (!proy.medidas.trim()) {
      setPlano(s => ({ ...s, status: 'error', msg: 'Introduce las medidas' }));
      return;
    }
    setPlano(s => ({ ...s, status: 'loading', msg: 'Generando plano técnico…', b64: null }));
    try {
      const r = await apiPost('/plano-2d', proy);
      setPlano(s => ({ ...s, status: 'success', msg: 'Plano generado', b64: r.planoBase64 }));
    } catch (err) {
      setPlano(s => ({ ...s, status: 'error', msg: err.message }));
    }
  }, [proy]);

  // ── Ficha ──
  const genFicha = useCallback(async () => {
    setFicha(s => ({ ...s, status: 'loading', msg: 'Generando ficha técnica…' }));
    try {
      const r = await apiPost('/ficha-tecnica', proy);
      setFicha(s => ({ ...s, status: 'success', msg: `Ficha generada · ${r.referencia}`, md: r.fichaMarkdown, ref: r.referencia }));
    } catch (err) {
      setFicha(s => ({ ...s, status: 'error', msg: err.message }));
    }
  }, [proy]);

  // ── Presentación ──
  const genPres = useCallback(async () => {
    setPres(s => ({ ...s, status: 'loading', msg: 'Generando presentación…' }));
    try {
      const r = await apiPost('/presentacion', proy);
      setPres(s => ({ ...s, status: 'success', msg: 'Presentación lista', html: r.presentacionHtml }));
    } catch (err) {
      setPres(s => ({ ...s, status: 'error', msg: err.message }));
    }
  }, [proy]);

  const dl = (content, name, type) => {
    const a = Object.assign(document.createElement('a'), {
      href: URL.createObjectURL(new Blob([content], { type })),
      download: name,
    });
    a.click();
  };

  const TABS = [
    { id: 'render', label: 'Render Manus', icon: <Sparkles size={14}/> },
    { id: 'plano',  label: 'Plano 2D',     icon: <Image size={14}/> },
    { id: 'ficha',  label: 'Ficha Técnica', icon: <FileText size={14}/> },
    { id: 'pres',   label: 'Presentación',  icon: <Presentation size={14}/> },
  ];

  const ESTILOS = ['Moderno', 'Nórdico', 'Minimalista', 'Industrial', 'Clásico', 'Rústico', 'Contemporáneo'];

  return (
    <div className={`flex flex-col h-full overflow-hidden transition-colors duration-200 ${t.root}`}>

      {/* Header */}
      <div className={`flex items-center gap-3 px-6 py-3 flex-shrink-0 ${t.header}`}>
        <div className="p-2 rounded-xl bg-amber-600/20">
          <ChefHat size={18} className="text-amber-500" />
        </div>
        <div className="flex-1">
          <h1 className={`text-xs font-black uppercase tracking-widest ${t.title}`}>3D Estudio</h1>
          <p className={`text-[9px] font-medium ${t.motorText}`}>Motor: LuiggiAI · Manus API</p>
        </div>
        <ThemeSelector mode={themeMode} onChange={handleThemeChange} t={t} />
      </div>

      <div className="flex flex-1 overflow-hidden min-h-0">

        {/* Sidebar */}
        <div className={`w-56 flex-shrink-0 p-4 flex flex-col gap-3 overflow-y-auto scrollbar-thin transition-colors duration-200 ${t.sidebar}`} style={{overflowY:'auto', overflowX:'hidden'}}>
          <p className={`text-[9px] font-black uppercase tracking-widest ${t.sidebarSect}`}>Proyecto</p>

          {[
            { key: 'nombre_cliente', label: 'Cliente',    ph: 'Nombre del cliente',        type: 'input' },
            { key: 'medidas',        label: 'Medidas',    ph: '400x350cm isla 200x100cm',  type: 'input' },
            { key: 'presupuesto',    label: 'Presupuesto', ph: 'Ej: 18.000€',              type: 'input' },
          ].map(f => (
            <div key={f.key}>
              <label className={`text-[9px] uppercase tracking-wider font-bold ${t.sidebarLabel}`}>{f.label}</label>
              <input
                className={`w-full mt-1 rounded-lg px-2 py-1.5 text-xs focus:outline-none transition-colors duration-200 ${t.input}`}
                placeholder={f.ph}
                value={proy[f.key]}
                onChange={e => setProy(p => ({ ...p, [f.key]: e.target.value }))}
              />
            </div>
          ))}

          <div>
            <label className={`text-[9px] uppercase tracking-wider font-bold ${t.sidebarLabel}`}>Estilo</label>
            <select
              className={`w-full mt-1 rounded-lg px-2 py-1.5 text-xs focus:outline-none transition-colors duration-200 ${t.select}`}
              value={proy.estilo}
              onChange={e => setProy(p => ({ ...p, estilo: e.target.value }))}>
              {ESTILOS.map(s => <option key={s}>{s}</option>)}
            </select>
          </div>

          <div>
            <label className={`text-[9px] uppercase tracking-wider font-bold ${t.sidebarLabel}`}>Descripción</label>
            <textarea
              className={`w-full mt-1 rounded-lg px-2 py-1.5 text-xs focus:outline-none resize-none transition-colors duration-200 ${t.input}`}
              rows={4} placeholder="Describe la cocina o dicta por voz…"
              value={proy.descripcion}
              onChange={e => setProy(p => ({ ...p, descripcion: e.target.value }))} />
          </div>

          <div>
            <label className={`text-[9px] uppercase tracking-wider font-bold ${t.sidebarLabel}`}>Materiales / Notas</label>
            <textarea
              className={`w-full mt-1 rounded-lg px-2 py-1.5 text-xs focus:outline-none resize-none transition-colors duration-200 ${t.input}`}
              rows={2} placeholder="Encimera silestone, frentes lacados…"
              value={proy.notas}
              onChange={e => setProy(p => ({ ...p, notas: e.target.value }))} />
          </div>

          <button
            onClick={rec ? stopRec : startRec}
            className={`flex items-center justify-center gap-2 w-full py-2 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${
              rec ? 'bg-red-600 text-white animate-pulse' : t.micIdle
            }`}
          >
            {rec ? <><MicOff size={13}/> Detener</> : <><Mic size={13}/> Dictar</>}
          </button>

          {transcrito && (
            <div className={`rounded-lg p-2 ${t.transcBg}`}>
              <p className={`text-[9px] font-bold mb-1 ${t.transcLabel}`}>Transcripción:</p>
              <p className={`text-[9px] leading-relaxed ${t.transcText}`}>{transcrito.slice(0, 180)}{transcrito.length > 180 ? '…' : ''}</p>
            </div>
          )}
        </div>

        {/* Main */}
        <div className="flex-1 flex flex-col overflow-hidden min-h-0">

          {/* Tabs */}
          <div className={`flex px-4 pt-2 gap-1 flex-shrink-0 transition-colors duration-200 ${t.tabBar}`}>
            {TABS.map(tb => (
              <button key={tb.id} onClick={() => setTab(tb.id)}
                className={`flex items-center gap-1.5 px-3 py-2 rounded-t-lg text-[10px] font-black uppercase tracking-widest transition-all ${
                  tab === tb.id ? t.tabActive : t.tabInactive
                }`}>
                {tb.icon} {tb.label}
              </button>
            ))}
          </div>

          <div className="flex-1 overflow-y-auto p-5">

            {/* ── RENDER MANUS ── */}
            {tab === 'render' && (
              <div className="flex flex-col gap-4 max-w-2xl mx-auto">
                <div>
                  <h2 className={`text-sm font-black mb-1 ${t.title}`}>Render fotorrealista con Manus</h2>
                  <p className={`text-xs ${t.subtext}`}>Escribe o dicta la descripción. Sube un croquis a boli para mayor precisión.</p>
                </div>

                <div className={`border-2 border-dashed rounded-xl p-5 text-center cursor-pointer transition-colors ${t.uploadBorder}`}
                  onClick={() => croquisRef.current?.click()}>
                  {render.croquisPrev ? (
                    <div className="relative inline-block">
                      <img src={render.croquisPrev} alt="Croquis" className="max-h-32 mx-auto rounded-lg object-contain" />
                      <button className="absolute -top-2 -right-2 bg-red-600 rounded-full p-0.5"
                        onClick={e => { e.stopPropagation(); setRender(s => ({ ...s, croquis: null, croquisPrev: null })); }}>
                        <X size={10} className="text-white"/>
                      </button>
                    </div>
                  ) : (
                    <>
                      <Upload size={22} className={`mx-auto mb-2 ${t.uploadText}`} />
                      <p className={`text-xs ${t.uploadText}`}>Sube un croquis a boli (opcional)</p>
                    </>
                  )}
                  <input ref={croquisRef} type="file" accept="image/*" className="hidden" onChange={onCroquis} />
                </div>

                <button onClick={genRender} disabled={render.status === 'loading'}
                  className="flex items-center justify-center gap-2 w-full py-3 bg-amber-600 hover:bg-amber-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl text-sm font-black uppercase tracking-widest transition-all text-white">
                  {render.status === 'loading'
                    ? <><Loader2 size={15} className="animate-spin"/> Generando con Manus…</>
                    : <><Sparkles size={15}/> Generar Render</>}
                </button>

                <StatusBadge status={render.status} message={render.msg} t={t} />

                {render.imageUrl && (
                  <div className={`relative group rounded-xl overflow-hidden border ${t.cardBorder}`}>
                    <img src={render.imageUrl} alt="Render Manus" className="w-full object-contain" />
                    <div className="absolute top-2 right-2 flex gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button onClick={() => setRender(s => ({ ...s, fs: true }))} className={`p-1.5 rounded-lg ${t.dlBtn}`}><ZoomIn size={13}/></button>
                      <a href={render.imageUrl} download="render_cocina.png" className={`p-1.5 rounded-lg block ${t.dlBtn}`}><Download size={13}/></a>
                      <button onClick={() => setRender(s => ({ ...s, editMode: !s.editMode }))} className="bg-amber-600/80 p-1.5 rounded-lg hover:bg-amber-600 text-white"><Edit3 size={13}/></button>
                    </div>
                  </div>
                )}

                {render.editMode && render.imageUrl && (
                  <div className={`rounded-xl p-4 flex flex-col gap-3 ${t.editBox}`}>
                    <p className={`text-[10px] font-black uppercase tracking-widest ${t.editLabel}`}>Editar render con Manus</p>
                    <input className={`w-full rounded-lg px-3 py-2 text-xs focus:outline-none transition-colors ${t.input}`}
                      placeholder="Ej: Cambia los muebles a blanco mate"
                      value={render.editTxt} onChange={e => setRender(s => ({ ...s, editTxt: e.target.value }))} />
                    <button onClick={editRender} disabled={render.status === 'loading'}
                      className="flex items-center justify-center gap-2 py-2 bg-amber-600 hover:bg-amber-500 disabled:opacity-50 rounded-xl text-xs font-black uppercase tracking-widest text-white">
                      <RefreshCw size={12}/> Aplicar edición
                    </button>
                  </div>
                )}

                {render.fs && (
                  <div className="fixed inset-0 bg-black/95 z-50 flex items-center justify-center p-4" onClick={() => setRender(s => ({ ...s, fs: false }))}>
                    <img src={render.imageUrl} alt="Render" className="max-w-full max-h-full object-contain rounded-xl" />
                    <button className="absolute top-4 right-4 bg-white/10 p-2 rounded-full text-white"><X size={18}/></button>
                  </div>
                )}
              </div>
            )}

            {/* ── PLANO 2D ── */}
            {tab === 'plano' && (
              <div className="flex flex-col gap-4 max-w-2xl mx-auto">
                <div>
                  <h2 className={`text-sm font-black mb-1 ${t.title}`}>Plano técnico acotado</h2>
                  <p className={`text-xs ${t.subtext}`}>Usa las medidas del panel izquierdo. Formato: <code className={`px-1 rounded ${t.code}`}>400x350cm isla 200x100cm</code></p>
                </div>
                <button onClick={genPlano} disabled={plano.status === 'loading'}
                  className="flex items-center justify-center gap-2 w-full py-3 bg-amber-600 hover:bg-amber-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl text-sm font-black uppercase tracking-widest transition-all text-white">
                  {plano.status === 'loading' ? <><Loader2 size={15} className="animate-spin"/> Generando plano…</> : <><Image size={15}/> Generar Plano 2D</>}
                </button>
                <StatusBadge status={plano.status} message={plano.msg} t={t} />
                {plano.b64 && (
                  <div className={`relative group rounded-xl overflow-hidden border ${t.cardBorder}`}>
                    <img src={plano.b64} alt="Plano 2D" className="w-full object-contain" />
                    <div className="absolute top-2 right-2 flex gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button onClick={() => setPlano(s => ({ ...s, fs: true }))} className={`p-1.5 rounded-lg ${t.dlBtn}`}><Maximize2 size={13}/></button>
                      <a href={plano.b64} download={`plano_${proy.nombre_cliente || 'cocina'}.png`} className={`p-1.5 rounded-lg block ${t.dlBtn}`}><Download size={13}/></a>
                    </div>
                  </div>
                )}
                {plano.fs && (
                  <div className="fixed inset-0 bg-black/95 z-50 flex items-center justify-center p-4" onClick={() => setPlano(s => ({ ...s, fs: false }))}>
                    <img src={plano.b64} alt="Plano" className="max-w-full max-h-full object-contain rounded-xl" />
                    <button className="absolute top-4 right-4 bg-white/10 p-2 rounded-full text-white"><X size={18}/></button>
                  </div>
                )}
              </div>
            )}

            {/* ── FICHA TÉCNICA ── */}
            {tab === 'ficha' && (
              <div className="flex flex-col gap-4 max-w-2xl mx-auto">
                <div>
                  <h2 className={`text-sm font-black mb-1 ${t.title}`}>Ficha técnica del proyecto</h2>
                  <p className={`text-xs ${t.subtext}`}>Genera una ficha con materiales, electrodomésticos, instalaciones y plazos.</p>
                </div>
                <button onClick={genFicha} disabled={ficha.status === 'loading'}
                  className="flex items-center justify-center gap-2 w-full py-3 bg-amber-600 hover:bg-amber-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl text-sm font-black uppercase tracking-widest transition-all text-white">
                  {ficha.status === 'loading' ? <><Loader2 size={15} className="animate-spin"/> Generando ficha…</> : <><FileText size={15}/> Generar Ficha Técnica</>}
                </button>
                <StatusBadge status={ficha.status} message={ficha.msg} t={t} />
                {ficha.md && (
                  <div className="relative">
                    <button onClick={() => dl(ficha.md, `ficha_${ficha.ref || 'cocina'}.md`, 'text/markdown')}
                      className={`absolute top-3 right-3 p-1.5 rounded-lg flex items-center gap-1 text-[10px] ${t.dlBtn}`}>
                      <Download size={11}/> .md
                    </button>
                    <pre className={`rounded-xl p-5 text-xs leading-relaxed overflow-x-auto whitespace-pre-wrap font-mono ${t.pre}`}>
                      {ficha.md}
                    </pre>
                  </div>
                )}
              </div>
            )}

            {/* ── PRESENTACIÓN ── */}
            {tab === 'pres' && (
              <div className="flex flex-col gap-4 max-w-2xl mx-auto">
                <div>
                  <h2 className={`text-sm font-black mb-1 ${t.title}`}>Presentación para cliente</h2>
                  <p className={`text-xs ${t.subtext}`}>Genera una presentación HTML de alta calidad lista para mostrar en pantalla o imprimir como PDF.</p>
                </div>
                <button onClick={genPres} disabled={pres.status === 'loading'}
                  className="flex items-center justify-center gap-2 w-full py-3 bg-amber-600 hover:bg-amber-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl text-sm font-black uppercase tracking-widest transition-all text-white">
                  {pres.status === 'loading' ? <><Loader2 size={15} className="animate-spin"/> Generando…</> : <><Presentation size={15}/> Generar Presentación</>}
                </button>
                <StatusBadge status={pres.status} message={pres.msg} t={t} />
                {pres.html && (
                  <div className="flex flex-col gap-3">
                    <div className="flex gap-2 flex-wrap">
                      <button onClick={() => setPres(s => ({ ...s, preview: !s.preview }))}
                        className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-black uppercase tracking-widest transition-all ${t.dlBtn}`}>
                        <Eye size={12}/> {pres.preview ? 'Ocultar' : 'Vista previa'}
                      </button>
                      <button onClick={() => dl(pres.html, `presentacion_${proy.nombre_cliente || 'cliente'}.html`, 'text/html')}
                        className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-black uppercase tracking-widest transition-all ${t.presBtn}`}>
                        <Download size={12}/> Descargar HTML
                      </button>
                    </div>
                    {pres.preview && (
                      <div className={`rounded-xl overflow-hidden border ${t.cardBorder}`} style={{ height: '560px' }}>
                        <iframe srcDoc={pres.html} title="Presentación" className="w-full h-full" sandbox="allow-same-origin" />
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

          </div>
        </div>
      </div>
    </div>
  );
}
