/*
 * © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
import React, { useState, useEffect } from 'react';
import { Building2, Search, Image as ImageIcon, Loader, ExternalLink, Phone, MapPin, Calendar, Tag, Download, X, Clock, Printer, CheckCircle2, CircleDashed, ArrowLeft, FileText, Copy, Database } from 'lucide-react';
import { getToken } from '../services/api';
import ApolloProspeccion from './ApolloProspeccion';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const auth = () => ({ 'Authorization': `Bearer ${getToken()}`, 'Content-Type': 'application/json' });

const BADGES = [
  'bg-indigo-100 text-indigo-700', 'bg-emerald-100 text-emerald-700', 'bg-amber-100 text-amber-700',
  'bg-violet-100 text-violet-700', 'bg-sky-100 text-sky-700', 'bg-rose-100 text-rose-700',
  'bg-teal-100 text-teal-700', 'bg-fuchsia-100 text-fuchsia-700',
];
// Sanea la URL de la promoción: añade protocolo si falta y descarta enlaces
// inválidos (placeholders o texto sin dominio) para no acabar en el login del ERP.
const safeUrl = (u) => {
  let v = String(u || '').trim();
  if (!v) return null;
  if (/^https?:\/\//i.test(v)) { /* ok */ }
  else if (/^www\./i.test(v) || /^[\w-]+\.[a-z]{2,}(\/|$)/i.test(v)) v = 'https://' + v;
  else return null; // no parece una URL real
  if (/ejemplo|example|\.\.\.|no especificad|consultar/i.test(v) || v.length < 12) return null;
  return v;
};
const tipoBadge = (t) => {
  const s = String(t || 'Otro');
  let h = 0; for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0;
  return BADGES[h % BADGES.length];
};

/**
 * La ficha de UNA obra, encima del informe.
 *
 * POR QUÉ ASÍ Y NO EN UNA PESTAÑA NUEVA
 * -------------------------------------
 * Hasta ahora, de una promoción solo se podía «abrir» su enlace, y eso se lleva
 * a otra pestaña del navegador: se pierde de vista el informe —que ha costado
 * una búsqueda con IA— y volver es acordarse de qué pestaña era.
 *
 * Esta ficha se pinta ENCIMA (`absolute inset-0`), así que el informe de debajo
 * no se desmonta ni se vuelve a pedir: sigue exactamente donde estaba, con su
 * filtro, su scroll y sus marcas de visitada. Cerrarla es volver, sin más.
 *
 * El enlace a la web de la promoción sigue abriendo pestaña, porque eso es una
 * página de fuera y ahí no mandamos nosotros.
 */
const FichaObra = ({ d, estado, onEstado, mapUrl, onVolver }) => {
  // Escape cierra: es lo que espera cualquiera que haya abierto una ficha.
  useEffect(() => {
    const h = (e) => { if (e.key === 'Escape') onVolver(); };
    window.addEventListener('keydown', h);
    return () => window.removeEventListener('keydown', h);
  }, [onVolver]);

  const [copiado, setCopiado] = useState(false);
  const copiar = async () => {
    const txt = [
      d.name, d.promoter, d.type, d.address, d.location,
      d.phone ? `Tel: ${d.phone}` : '',
      d.priceStart ? `Desde ${d.priceStart}` : '',
      [d.startDate, d.deliveryDate].filter(Boolean).join(' → '),
    ].filter(Boolean).join('\n');
    try { await navigator.clipboard.writeText(txt); setCopiado(true); setTimeout(() => setCopiado(false), 1800); } catch { /* sin portapapeles */ }
  };

  const Dato = ({ icon, label, valor, children }) => (!valor && !children) ? null : (
    <div className="flex items-start gap-2.5 py-2 border-b border-slate-100 last:border-0">
      <span className="text-slate-300 mt-0.5 shrink-0">{icon}</span>
      <div className="min-w-0">
        <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{label}</p>
        <div className="text-sm text-slate-700 font-semibold break-words">{children || valor}</div>
      </div>
    </div>
  );

  const imprimirFicha = () => {
    const w = window.open('', '_blank');
    if (!w) return;
    w.document.write(`<!DOCTYPE html><html><head><title>Ficha · ${d.name || 'Promoción'}</title><style>
      body { font-family: system-ui, -apple-system, sans-serif; color: #111726; padding: 32px; max-width: 800px; margin: 0 auto; line-height: 1.5; }
      .header { border-bottom: 2px solid #e3e8ee; padding-bottom: 16px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: flex-start; }
      h1 { color: #1f203b; font-size: 24px; margin: 0 0 4px 0; font-weight: 900; }
      .promoter { color: #4a5564; font-weight: 700; font-size: 14px; }
      .badge { padding: 4px 10px; background: #e3e7f5; color: #3b3f7d; border-radius: 6px; font-size: 12px; font-weight: 800; text-transform: uppercase; }
      .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px; }
      .item { border: 1px solid #f2f5f8; background: #f8fafb; padding: 12px; border-radius: 8px; }
      .label { text-transform: uppercase; font-size: 10px; font-weight: 800; color: #687485; letter-spacing: 0.5px; margin-bottom: 4px; }
      .value { font-size: 14px; color: #111726; font-weight: 700; word-break: break-word; }
      .full { grid-column: span 2; }
      .footer { margin-top: 30px; font-size: 11px; color: #97a3b2; text-align: center; border-top: 1px solid #e3e8ee; padding-top: 12px; }
      @media print { body { padding: 0; } }
    </style></head><body>
      <div class="header">
        <div>
          <h1>${d.name || 'Promoción de Obra Nueva'}</h1>
          <div class="promoter">${d.promoter || 'Promotor sin identificar'}</div>
        </div>
        <span class="badge">${d.type || 'Viviendas'}</span>
      </div>
      <div class="grid">
        <div class="item"><div class="label">Zona / Municipio</div><div class="value">${d.location || '—'}</div></div>
        <div class="item"><div class="label">Dirección / Ubicación</div><div class="value">${d.address || '—'}</div></div>
        <div class="item"><div class="label">Teléfono de contacto</div><div class="value">${d.phone || '—'}</div></div>
        <div class="item"><div class="label">Precio de partida</div><div class="value">${d.priceStart || '—'}</div></div>
        <div class="item full"><div class="label">Fechas estimadas (Inicio → Entrega)</div><div class="value">${(d.startDate || d.deliveryDate) ? `${d.startDate || '—'} → ${d.deliveryDate || '—'}` : '—'}</div></div>
        <div class="item full"><div class="label">Descripción de la promoción</div><div class="value">${d.description || '—'}</div></div>
        ${safeUrl(d.url) ? `<div class="item full"><div class="label">Web de la promoción</div><div class="value">${safeUrl(d.url)}</div></div>` : ''}
      </div>
      <div class="footer">Informe de prospección comercial de obra nueva · Luiggi Home ERP</div>
      <script>window.onload = function() { window.print(); };</script>
    </body></html>`);
    w.document.close();
  };

  return (
    <div className="absolute inset-0 z-30 bg-sky-50 overflow-y-auto p-4 sm:p-6 pb-24">
      {/* La vuelta, arriba del todo y pegada: es lo primero que se busca. */}
      <div className="sticky top-0 -mx-4 sm:-mx-6 -mt-4 sm:-mt-6 mb-4 px-4 sm:px-6 py-3 bg-white/95 backdrop-blur border-b border-slate-200 flex items-center gap-3 flex-wrap z-10">
        <button onClick={onVolver}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-xl font-bold text-sm hover:bg-indigo-700 shadow-sm">
          <ArrowLeft size={16} /> Volver al informe
        </button>
        <span className="text-[11px] text-slate-400 font-bold hidden sm:inline">El informe sigue abierto detrás</span>
        <button onClick={imprimirFicha} className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border border-indigo-200">
          <Printer size={15} /> Imprimir ficha
        </button>
        <button onClick={onVolver} title="Cerrar (Esc)" className="ml-auto p-2 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100"><X size={18} /></button>
      </div>

      <div className="max-w-3xl mx-auto space-y-4">
        <div className="bg-white rounded-2xl border border-slate-200 p-5">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <h2 className="text-xl font-black text-slate-900 break-words">{d.name || 'Promoción'}</h2>
              <p className="text-sm text-slate-500 font-bold">{d.promoter || 'Promotor sin identificar'}</p>
            </div>
            <span className={`px-2.5 py-1 rounded-lg text-[11px] font-black shrink-0 ${tipoBadge(d.type)}`}>{d.type || 'Otro'}</span>
          </div>

          <div className="mt-3">
            <Dato icon={<MapPin size={15} />} label="Zona" valor={d.location} />
            <Dato icon={<MapPin size={15} />} label="Dirección" valor={d.address} />
            <Dato icon={<Phone size={15} />} label="Teléfono">
              {d.phone ? <a href={`tel:${d.phone}`} className="text-indigo-600 font-black">{d.phone}</a> : null}
            </Dato>
            <Dato icon={<Tag size={15} />} label="Precio de partida" valor={d.priceStart} />
            <Dato icon={<Calendar size={15} />} label="Fechas"
              valor={(d.startDate || d.deliveryDate) ? `${d.startDate || '—'} → ${d.deliveryDate || '—'}` : ''} />
            <Dato icon={<FileText size={15} />} label="Descripción" valor={d.description} />
          </div>

          {/* Lo que NO consta se dice, no se rellena con un guion y ya está: es
              la lista de lo que hay que averiguar antes de llamar. */}
          {(() => {
            const faltan = [
              !d.promoter && 'promotor', !d.phone && 'teléfono', !d.address && 'dirección',
              !d.priceStart && 'precio', !(d.startDate || d.deliveryDate) && 'fechas',
            ].filter(Boolean);
            return faltan.length ? (
              <p className="mt-3 text-[11px] font-bold text-amber-700 bg-amber-50 border border-amber-200 rounded-xl px-3 py-2">
                Sin datos de: {faltan.join(', ')}. La búsqueda no los encontró — hay que confirmarlos antes de ofrecer nada.
              </p>
            ) : null;
          })()}
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 p-4 flex flex-wrap items-center gap-2">
          <button onClick={() => onEstado('visited')}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold ${estado === 'visited' ? 'bg-emerald-600 text-white' : 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100'}`}>
            <CheckCircle2 size={15} /> Visitada
          </button>
          <button onClick={() => onEstado('todo')}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold ${estado === 'todo' ? 'bg-sky-600 text-white' : 'bg-sky-50 text-sky-700 hover:bg-sky-100'}`}>
            <CircleDashed size={15} /> Por visitar
          </button>
          <button onClick={copiar} className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold bg-slate-100 text-slate-700 hover:bg-slate-200">
            <Copy size={15} /> {copiado ? 'Copiado' : 'Copiar datos'}
          </button>
          <button onClick={imprimirFicha} className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold bg-indigo-50 text-indigo-700 hover:bg-indigo-100 border border-indigo-200">
            <Printer size={15} /> Imprimir ficha
          </button>
          <div className="ml-auto flex items-center gap-2">
            <a href={mapUrl} target="_blank" rel="noreferrer" className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold bg-white border border-slate-200 text-slate-700 hover:bg-slate-50">
              <MapPin size={15} className="text-rose-500" /> Ver en mapa
            </a>
            {safeUrl(d.url) && (
              <a href={safeUrl(d.url)} target="_blank" rel="noreferrer" className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold bg-indigo-50 text-indigo-700 hover:bg-indigo-100">
                Web de la promoción <ExternalLink size={13} />
              </a>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

const PropData = ({ state }) => {
  const [mode, setMode] = useState('search'); // 'search' | 'image'
  const [ficha, setFicha] = useState(null); // la obra abierta, encima del informe
  const [portal, setPortal] = useState('');
  const [location, setLocation] = useState('');
  const [img, setImg] = useState(null); // {b64, name}
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null); // {developments, summary, groundingSources, groundingFailed}
  const [error, setError] = useState('');
  const [tipoFilter, setTipoFilter] = useState('all'); // all | pisos | chalets | otros
  const [estados, setEstados] = useState(() => { try { return JSON.parse(localStorage.getItem('propdata_estados') || '{}'); } catch { return {}; } });
  const [historial, setHistorial] = useState(() => { try { return JSON.parse(localStorage.getItem('propdata_historial') || '[]'); } catch { return []; } });
  const [showHist, setShowHist] = useState(false);

  const keyOf = (d) => `${(d.name || '').toLowerCase()}|${(d.location || d.address || '').toLowerCase()}`;
  const setEstado = (d, v) => setEstados(prev => {
    const k = keyOf(d); const next = { ...prev }; if (next[k] === v) delete next[k]; else next[k] = v;
    localStorage.setItem('propdata_estados', JSON.stringify(next)); return next;
  });
  const guardarHistorial = (loc, port, n) => setHistorial(prev => {
    const entry = { location: loc, portal: port, count: n, at: new Date().toISOString() };
    const next = [entry, ...prev.filter(h => !(h.location === loc && h.portal === port))].slice(0, 15);
    localStorage.setItem('propdata_historial', JSON.stringify(next)); return next;
  });
  const mapUrl = (d) => `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent([d.address, d.location, d.name].filter(Boolean).join(', ') || d.name || '')}`;

  const imprimir = () => {
    const rows = devs.map(d => `
      <div class="obra">
        <div class="top"><b>${d.name || 'Promoción'}</b><span class="tag">${d.type || ''}</span></div>
        <div class="sub">${d.promoter || ''}</div>
        <div class="det">${[d.location, d.address].filter(Boolean).join(' · ')}</div>
        <div class="det">${d.phone ? '☎ ' + d.phone + '  ' : ''}${d.priceStart ? 'desde ' + d.priceStart : ''}</div>
        <div class="det">${[d.startDate, d.deliveryDate].filter(Boolean).join(' → ')}</div>
      </div>`).join('');
    const w = window.open('', '_blank');
    if (!w) return;
    w.document.write(`<html><head><title>Obra nueva · ${location}</title><style>
      body{font-family:Arial,sans-serif;color:#212934;padding:24px}
      h1{color:#343765;font-size:20px;margin:0 0 4px} .meta{color:#687485;font-size:12px;margin-bottom:16px}
      .obra{border:1px solid #e3e8ee;border-radius:10px;padding:10px 12px;margin-bottom:8px;break-inside:avoid}
      .top{display:flex;justify-content:space-between;font-size:14px} .tag{color:#654da8;font-weight:700;font-size:11px}
      .sub{color:#4a5564;font-size:12px} .det{color:#687485;font-size:11px;margin-top:2px}
      @media print{.no-print{display:none}}
    </style></head><body>
      <h1>Promociones de obra nueva — ${location}</h1>
      <div class="meta">${devs.length} promociones${portal ? ' · ' + portal : ''} · ${new Date().toLocaleDateString('es-ES')}</div>
      ${rows}
      <script>window.onload=()=>window.print()<\/script>
    </body></html>`);
    w.document.close();
  };

  const readFile = (file) => new Promise((res) => {
    const fr = new FileReader();
    fr.onload = () => res(String(fr.result));
    fr.onerror = () => res(null);
    fr.readAsDataURL(file);
  });

  const buscar = async () => {
    if (!location.trim()) { setError('Indica una ciudad o zona.'); return; }
    setLoading(true); setError(''); setResult(null);
    try {
      const r = await fetch(`${API_URL}/api/propdata/search`, { method: 'POST', headers: auth(), body: JSON.stringify({ location, portal }) });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail || 'Error');
      setResult(d);
      guardarHistorial(location.trim(), portal.trim(), (d.developments || []).length);
    } catch (e) { setError(e.message || 'No se pudo completar la búsqueda.'); }
    finally { setLoading(false); }
  };

  const analizarImagen = async () => {
    if (!img?.b64) { setError('Sube una captura del portal.'); return; }
    setLoading(true); setError(''); setResult(null);
    try {
      const r = await fetch(`${API_URL}/api/propdata/image`, { method: 'POST', headers: auth(), body: JSON.stringify({ imageBase64: img.b64 }) });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail || 'Error');
      setResult(d);
    } catch (e) { setError(e.message || 'No se pudo analizar la imagen.'); }
    finally { setLoading(false); }
  };

  const devsAll = result?.developments || [];

  // Categoría: pisos (piso/ático/estudio/dúplex) vs chalets (chalet/adosado/pareado/villa/unifamiliar)
  const catOf = (t) => {
    const s = String(t || '').toLowerCase();
    if (/(chalet|adosad|paread|unifamiliar|villa)/.test(s)) return 'chalets';
    if (/(piso|[aá]tico|estudio|d[uú]plex|apartament|vivienda)/.test(s)) return 'pisos';
    return 'otros';
  };
  const nPisos = devsAll.filter(d => catOf(d.type) === 'pisos').length;
  const nChalets = devsAll.filter(d => catOf(d.type) === 'chalets').length;
  const nOtros = devsAll.length - nPisos - nChalets;
  const devs = tipoFilter === 'all' ? devsAll : devsAll.filter(d => catOf(d.type) === tipoFilter);

  // Distribución por tipo (mini-gráfico sin dependencias) — sobre lo visible
  const porTipo = devs.reduce((a, d) => { const t = d.type || 'Otro'; a[t] = (a[t] || 0) + 1; return a; }, {});
  const maxTipo = Math.max(1, ...Object.values(porTipo));
  // Lo que predomina (tipo concreto más repetido en toda la búsqueda)
  const porTipoAll = devsAll.reduce((a, d) => { const t = d.type || 'Otro'; a[t] = (a[t] || 0) + 1; return a; }, {});
  const predomina = Object.entries(porTipoAll).sort((a, b) => b[1] - a[1])[0];
  const catPredomina = nChalets > nPisos ? 'Chalets' : nPisos > 0 ? 'Pisos' : '—';

  const exportCSV = () => {
    const cols = ['name', 'promoter', 'type', 'location', 'priceStart', 'phone', 'address', 'startDate', 'deliveryDate', 'url'];
    const head = ['Promoción', 'Promotor', 'Tipo', 'Ubicación', 'Precio', 'Teléfono', 'Dirección', 'Inicio', 'Entrega', 'URL'];
    const esc = (v) => `"${String(v ?? '').replace(/"/g, '""')}"`;
    const rows = devs.map(d => cols.map(c => esc(d[c])).join(';'));
    const csv = [head.join(';'), ...rows].join('\n');
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' }));
    a.download = `promociones_${(location || 'obranueva').replace(/\s+/g, '_')}.csv`;
    a.click();
  };

  // Acentos de color por tarjeta (se alternan para que cada obra destaque)
  const ACCENTS = [
    'border-l-indigo-400 bg-indigo-50/40', 'border-l-emerald-400 bg-emerald-50/40',
    'border-l-amber-400 bg-amber-50/40', 'border-l-sky-400 bg-sky-50/50',
    'border-l-fuchsia-400 bg-fuchsia-50/40', 'border-l-rose-400 bg-rose-50/40',
    'border-l-teal-400 bg-teal-50/40', 'border-l-violet-400 bg-violet-50/40',
  ];

  return (
    // El informe vive aquí debajo y NO se desmonta al abrir una ficha: la ficha
    // se pinta encima. Por eso volver de una obra deja el informe tal cual —
    // mismo filtro, mismo scroll— en vez de tener que buscarlo otra vez.
    <div className="h-full relative">
    <div className="h-full flex flex-col p-4 sm:p-6 pb-24 bg-sky-50 overflow-y-auto">
      <div className="hueco-logo rounded-2xl bg-gradient-to-r from-sky-600 via-indigo-600 to-violet-600 text-white px-4 py-3 mb-4 shadow-lg flex items-center justify-between gap-3 flex-wrap">
        <div>
          <h1 className="text-base sm:text-lg font-black flex items-center gap-2"><Building2 size={18} /> Obra Nueva y Prescripción</h1>
          <p className="hidden sm:block text-xs text-white/80">Localiza promociones, arquitectos, interioristas y constructoras · IA</p>
        </div>
        <div className="flex gap-1.5 bg-black/20 p-1 rounded-xl backdrop-blur">
          <button onClick={() => setMode('database')} className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-black transition-all ${mode === 'database' ? 'bg-white text-indigo-900 shadow-md ring-2 ring-amber-400' : 'text-white/80 hover:text-white hover:bg-white/10'}`}>
            <Database size={14} className="text-amber-400" /> BASE DE DATOS
          </button>
          <button onClick={() => setMode('search')} className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-black transition-all ${mode === 'search' ? 'bg-white text-indigo-900 shadow-md' : 'text-white/80 hover:text-white hover:bg-white/10'}`}>
            <Search size={14} /> Obra Nueva
          </button>
          <button onClick={() => setMode('image')} className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-black transition-all ${mode === 'image' ? 'bg-white text-indigo-900 shadow-md' : 'text-white/80 hover:text-white hover:bg-white/10'}`}>
            <ImageIcon size={14} /> Desde Captura
          </button>
        </div>
      </div>

      {mode === 'database' ? (
        <div className="flex-1 -mx-4 sm:-mx-6 -mb-24 mt-[-10px] bg-slate-50">
          <ApolloProspeccion currentUser={state?.currentUser} />
        </div>
      ) : (
      <>
      <div className="bg-white rounded-2xl border border-slate-200 p-4 mb-4">
        <div className="flex items-center justify-between gap-2 mb-4 flex-wrap">
          <div className="flex gap-1 bg-slate-100 rounded-lg p-1 w-fit">
            <button onClick={() => setMode('search')} className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-bold ${mode === 'search' ? 'bg-white text-indigo-700 shadow-sm' : 'text-slate-500'}`}><Search size={15} /> Buscar por zona</button>
            <button onClick={() => setMode('image')} className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-bold ${mode === 'image' ? 'bg-white text-indigo-700 shadow-sm' : 'text-slate-500'}`}><ImageIcon size={15} /> Desde captura</button>
          </div>
          {historial.length > 0 && (
            <div className="relative">
              <button onClick={() => setShowHist(v => !v)} className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 rounded-lg text-xs font-bold text-slate-600 hover:bg-slate-200"><Clock size={14} /> Historial ({historial.length})</button>
              {showHist && (
                <div className="absolute right-0 mt-1 w-72 max-h-72 overflow-auto bg-white border border-slate-200 rounded-xl shadow-xl z-20 p-1">
                  {historial.map((h, i) => (
                    <button key={i} onClick={() => { setMode('search'); setLocation(h.location); setPortal(h.portal || ''); setShowHist(false); }} className="w-full text-left px-3 py-2 rounded-lg hover:bg-sky-50 flex items-center justify-between gap-2">
                      <span className="text-sm font-bold text-slate-700 truncate">{h.location}{h.portal ? ` · ${h.portal}` : ''}</span>
                      <span className="text-[10px] text-slate-400 shrink-0">{h.count} · {new Date(h.at).toLocaleDateString('es-ES')}</span>
                    </button>
                  ))}
                  <button onClick={() => { setHistorial([]); localStorage.removeItem('propdata_historial'); setShowHist(false); }} className="w-full text-center text-[11px] text-rose-500 font-bold py-1.5 hover:bg-rose-50 rounded-lg">Borrar historial</button>
                </div>
              )}
            </div>
          )}
        </div>

        {mode === 'search' ? (
          <div className="grid sm:grid-cols-[1fr_1fr_auto] gap-3 items-end">
            <div>
              <label className="text-[10px] font-black text-slate-400 uppercase block mb-1">Ciudad / zona *</label>
              <input value={location} onChange={e => setLocation(e.target.value)} placeholder="Ej.: Cádiz, Chiclana, Sevilla Este…" className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm outline-none focus:border-indigo-400" />
            </div>
            <div>
              <label className="text-[10px] font-black text-slate-400 uppercase block mb-1">Portal (opcional)</label>
              <input value={portal} onChange={e => setPortal(e.target.value)} placeholder="Idealista, Fotocasa…" className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm outline-none focus:border-indigo-400" />
            </div>
            <button onClick={buscar} disabled={loading} className="flex items-center justify-center gap-2 px-5 py-2.5 bg-indigo-600 text-white rounded-xl font-bold text-sm hover:bg-indigo-700 disabled:opacity-50">{loading ? <Loader size={16} className="animate-spin" /> : <Search size={16} />} Buscar</button>
          </div>
        ) : (
          <div className="flex flex-wrap items-center gap-3">
            <label className="flex items-center gap-2 px-3 py-2 bg-slate-100 rounded-xl text-sm font-bold text-slate-600 cursor-pointer hover:bg-slate-200">
              <ImageIcon size={16} /> {img ? 'Cambiar captura' : 'Subir captura del portal'}
              <input type="file" accept="image/*" className="hidden" onChange={async e => { const f = e.target.files?.[0]; setImg(f ? { b64: await readFile(f), name: f.name } : null); }} />
            </label>
            {img && <span className="text-xs text-slate-500 truncate max-w-[200px]">{img.name}</span>}
            <button onClick={analizarImagen} disabled={loading || !img} className="flex items-center gap-2 px-5 py-2.5 bg-indigo-600 text-white rounded-xl font-bold text-sm hover:bg-indigo-700 disabled:opacity-50">{loading ? <Loader size={16} className="animate-spin" /> : <ImageIcon size={16} />} Analizar</button>
          </div>
        )}
        {error && <p className="mt-3 text-sm text-rose-600 font-bold">{error}</p>}
      </div>

      {loading && <div className="text-center text-slate-400 py-10 text-sm flex items-center justify-center gap-2"><Loader className="animate-spin" size={18} /> Analizando con IA…</div>}

      {result && (
        <div className="space-y-4">
          {result.groundingFailed && <div className="bg-amber-50 border border-amber-200 text-amber-700 rounded-xl px-4 py-2 text-xs font-bold">⚠️ Sin búsqueda web en tiempo real (límite de cuota): resultados orientativos/simulados.</div>}

          {/* KPIs */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            <div className="rounded-2xl p-4 text-white shadow-lg bg-gradient-to-br from-slate-700 to-slate-900">
              <p className="text-[9px] font-black text-white/60 uppercase tracking-widest">Promociones</p>
              <p className="text-3xl font-black mt-0.5">{devsAll.length}</p>
            </div>
            <div className="rounded-2xl p-4 text-white shadow-lg bg-gradient-to-br from-fuchsia-500 to-indigo-600">
              <p className="text-[9px] font-black text-white/70 uppercase tracking-widest">Predomina</p>
              <p className="text-lg font-black mt-0.5 leading-tight truncate">{predomina ? predomina[0] : '—'}</p>
              <p className="text-[11px] text-white/80">{predomina ? `${predomina[1]} de ${devsAll.length} · ${catPredomina}` : ''}</p>
            </div>
            <div className="rounded-2xl p-4 text-white shadow-lg bg-gradient-to-br from-sky-500 to-cyan-600">
              <p className="text-[9px] font-black text-white/70 uppercase tracking-widest">Pisos</p>
              <p className="text-3xl font-black mt-0.5">{nPisos}</p>
            </div>
            <div className="rounded-2xl p-4 text-white shadow-lg bg-gradient-to-br from-emerald-500 to-teal-600">
              <p className="text-[9px] font-black text-white/70 uppercase tracking-widest">Chalets</p>
              <p className="text-3xl font-black mt-0.5">{nChalets}</p>
            </div>
          </div>

          {/* Filtro + export */}
          <div className="flex items-center justify-between gap-2 flex-wrap">
            <div className="flex items-center gap-1 bg-white border border-slate-200 rounded-xl p-1">
              {[['all', `Todos (${devsAll.length})`], ['pisos', `Pisos (${nPisos})`], ['chalets', `Chalets (${nChalets})`], ...(nOtros ? [['otros', `Otros (${nOtros})`]] : [])].map(([k, lab]) => (
                <button key={k} onClick={() => setTipoFilter(k)} className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-colors ${tipoFilter === k ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-500 hover:bg-slate-100'}`}>{lab}</button>
              ))}
            </div>
            {devs.length > 0 && <div className="flex items-center gap-2">
              <button onClick={imprimir} className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-700 text-white rounded-lg text-xs font-bold hover:bg-slate-800"><Printer size={14} /> Imprimir</button>
              <button onClick={exportCSV} className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 text-white rounded-lg text-xs font-bold hover:bg-emerald-700"><Download size={14} /> Exportar CSV</button>
            </div>}
          </div>

          {Object.keys(porTipo).length > 0 && (
            <div className="bg-white rounded-2xl border border-slate-200 p-4">
              <p className="text-[10px] font-black text-slate-400 uppercase mb-2">Por tipo de vivienda</p>
              <div className="space-y-1.5">
                {Object.entries(porTipo).sort((a, b) => b[1] - a[1]).map(([t, n], bi) => {
                  const bars = ['bg-indigo-500', 'bg-emerald-500', 'bg-amber-500', 'bg-sky-500', 'bg-fuchsia-500', 'bg-rose-500', 'bg-teal-500', 'bg-violet-500'];
                  return (
                    <div key={t} className="flex items-center gap-2">
                      <span className="w-28 text-xs font-bold text-slate-600 shrink-0 truncate" title={t}>{t}</span>
                      <div className="flex-1 bg-slate-100 rounded-full h-3"><div className={`${bars[bi % bars.length]} h-3 rounded-full`} style={{ width: `${(n / maxTipo) * 100}%` }} /></div>
                      <span className="w-6 text-xs font-black text-slate-700 text-right">{n}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          <div className="grid md:grid-cols-2 gap-3">
            {devs.map((d, i) => {
              const est = estados[keyOf(d)];
              const ring = est === 'visited' ? 'border-l-emerald-500 bg-emerald-50/60 ring-1 ring-emerald-200' : est === 'todo' ? 'border-l-sky-500 bg-sky-50/70 ring-1 ring-sky-200' : ACCENTS[i % ACCENTS.length];
              return (
              <div key={i} className={`rounded-2xl border border-slate-200 border-l-4 p-4 hover:shadow-md transition-shadow ${ring}`}>
                <div className="flex items-start justify-between gap-2">
                  {/* El nombre abre la ficha AQUÍ DENTRO. Antes lo único que se
                      podía abrir de una obra era su web, y eso se lleva a otra
                      pestaña y deja el informe atrás. */}
                  <button onClick={() => setFicha(d)} className="min-w-0 text-left group">
                    <p className="font-black text-slate-800 truncate group-hover:text-indigo-700 group-hover:underline">{d.name || 'Promoción'}</p>
                    <p className="text-xs text-slate-500 truncate">{d.promoter || '—'}</p>
                  </button>
                  <span className={`px-2 py-0.5 rounded-lg text-[10px] font-black shrink-0 ${tipoBadge(d.type)}`}>{d.type || 'Otro'}</span>
                </div>
                <div className="mt-2 space-y-1 text-[12px] text-slate-600">
                  {d.location && <p className="flex items-center gap-1.5"><MapPin size={13} className="text-slate-400" /> {d.location}</p>}
                  {d.address && <p className="flex items-center gap-1.5"><MapPin size={13} className="text-slate-300" /> {d.address}</p>}
                  {d.phone && <p className="flex items-center gap-1.5"><Phone size={13} className="text-slate-400" /> <a href={`tel:${d.phone}`} className="text-indigo-600 font-bold">{d.phone}</a></p>}
                  {(d.startDate || d.deliveryDate) && <p className="flex items-center gap-1.5"><Calendar size={13} className="text-slate-400" /> {d.startDate || '—'} → {d.deliveryDate || '—'}</p>}
                  {d.priceStart && <p className="flex items-center gap-1.5"><Tag size={13} className="text-slate-400" /> desde {d.priceStart}</p>}
                </div>
                {d.description && <p className="mt-2 text-[11px] text-slate-400 line-clamp-2">{d.description}</p>}
                <div className="mt-2 flex items-center gap-2 flex-wrap">
                  <button onClick={() => setFicha(d)} className="inline-flex items-center gap-1 px-2.5 py-1 bg-indigo-600 text-white rounded-lg text-xs font-bold hover:bg-indigo-700"><FileText size={13} /> Ficha</button>
                  <a href={mapUrl(d)} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 px-2.5 py-1 bg-white border border-slate-200 rounded-lg text-xs font-bold text-slate-700 hover:bg-slate-50"><MapPin size={13} className="text-rose-500" /> Ver en mapa</a>
                  {safeUrl(d.url) && <a href={safeUrl(d.url)} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-xs font-bold text-indigo-600 hover:underline">Promoción <ExternalLink size={12} /></a>}
                  <div className="ml-auto flex items-center gap-1">
                    <button onClick={() => setEstado(d, 'visited')} title="Visitada" className={`p-1.5 rounded-lg ${est === 'visited' ? 'bg-emerald-600 text-white' : 'bg-emerald-50 text-emerald-600 hover:bg-emerald-100'}`}><CheckCircle2 size={15} /></button>
                    <button onClick={() => setEstado(d, 'todo')} title="Por visitar" className={`p-1.5 rounded-lg ${est === 'todo' ? 'bg-sky-600 text-white' : 'bg-sky-50 text-sky-600 hover:bg-sky-100'}`}><CircleDashed size={15} /></button>
                  </div>
                </div>
              </div>
              );
            })}
          </div>

          {result.summary && (
            <div className="bg-white rounded-2xl border border-slate-200 p-5">
              <p className="text-[10px] font-black text-indigo-500 uppercase tracking-widest mb-3">Resumen del mercado</p>
              <div className="space-y-2.5">
                {result.summary.split('\n').map(l => l.trim()).filter(Boolean).map((line, i) => {
                  const h = line.match(/^#{1,4}\s+(.*)$/);
                  if (h) return <h4 key={i} className="text-sm font-black text-slate-800 pt-1">{h[1]}</h4>;
                  const parts = line.replace(/^[-*]\s+/, '• ').split(/(\*\*[^*]+\*\*)/g).map((p, k) => p.startsWith('**') && p.endsWith('**') ? <b key={k} className="text-slate-800">{p.slice(2, -2)}</b> : p);
                  return <p key={i} className="text-sm text-slate-600 leading-relaxed">{parts}</p>;
                })}
              </div>
            </div>
          )}

          {(result.groundingSources || []).length > 0 && (
            <div className="bg-white rounded-2xl border border-slate-200 p-4">
              <p className="text-[10px] font-black text-slate-400 uppercase mb-2">Fuentes</p>
              <div className="flex flex-wrap gap-2">
                {result.groundingSources.map((s, i) => (
                  <a key={i} href={s.uri} target="_blank" rel="noreferrer" className="text-[11px] text-indigo-600 hover:underline inline-flex items-center gap-1 max-w-[240px] truncate"><ExternalLink size={11} /> {s.title || s.uri}</a>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
      </>
      )}
    </div>

    {ficha && (
      <FichaObra
        d={ficha}
        estado={estados[keyOf(ficha)]}
        onEstado={(v) => setEstado(ficha, v)}
        mapUrl={mapUrl(ficha)}
        onVolver={() => setFicha(null)}
      />
    )}
    </div>
  );
};

export default PropData;
