import React, { useState } from 'react';
import { Building2, Search, Image as ImageIcon, Loader, ExternalLink, Phone, MapPin, Calendar, Tag, Download, X } from 'lucide-react';
import { getToken } from '../services/api';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const auth = () => ({ 'Authorization': `Bearer ${getToken()}`, 'Content-Type': 'application/json' });

const TIPO_COLOR = {
  Piso: 'bg-indigo-100 text-indigo-700', Chalet: 'bg-emerald-100 text-emerald-700',
  Adosado: 'bg-amber-100 text-amber-700', Ático: 'bg-violet-100 text-violet-700', Otro: 'bg-slate-100 text-slate-600',
};

const PropData = ({ state }) => {
  const [mode, setMode] = useState('search'); // 'search' | 'image'
  const [portal, setPortal] = useState('');
  const [location, setLocation] = useState('');
  const [img, setImg] = useState(null); // {b64, name}
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null); // {developments, summary, groundingSources, groundingFailed}
  const [error, setError] = useState('');

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

  const devs = result?.developments || [];

  // Distribución por tipo (mini-gráfico sin dependencias)
  const porTipo = devs.reduce((a, d) => { const t = d.type || 'Otro'; a[t] = (a[t] || 0) + 1; return a; }, {});
  const maxTipo = Math.max(1, ...Object.values(porTipo));

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

  return (
    <div className="h-full flex flex-col p-4 sm:p-6 pb-24 bg-slate-50 overflow-y-auto">
      <div className="rounded-2xl bg-gradient-to-r from-sky-600 via-indigo-600 to-violet-600 text-white px-4 py-3 mb-4 shadow-lg flex items-center gap-3 flex-wrap">
        <h1 className="ml-14 sm:ml-2 text-base sm:text-lg font-black flex items-center gap-2"><Building2 size={18} /> Prospección de Obra Nueva</h1>
        <p className="hidden sm:block text-xs text-white/80">Localiza promociones y promotores a los que ofrecer cocinas · IA (Gemini)</p>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 p-4 mb-4">
        <div className="flex gap-1 bg-slate-100 rounded-lg p-1 w-fit mb-4">
          <button onClick={() => setMode('search')} className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-bold ${mode === 'search' ? 'bg-white text-indigo-700 shadow-sm' : 'text-slate-500'}`}><Search size={15} /> Buscar por zona</button>
          <button onClick={() => setMode('image')} className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-bold ${mode === 'image' ? 'bg-white text-indigo-700 shadow-sm' : 'text-slate-500'}`}><ImageIcon size={15} /> Desde captura</button>
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

          <div className="flex items-center justify-between gap-2 flex-wrap">
            <p className="text-sm font-black text-slate-700">{devs.length} promociones encontradas</p>
            {devs.length > 0 && <button onClick={exportCSV} className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 text-white rounded-lg text-xs font-bold hover:bg-emerald-700"><Download size={14} /> Exportar CSV</button>}
          </div>

          {Object.keys(porTipo).length > 0 && (
            <div className="bg-white rounded-2xl border border-slate-200 p-4">
              <p className="text-[10px] font-black text-slate-400 uppercase mb-2">Por tipo de vivienda</p>
              <div className="space-y-1.5">
                {Object.entries(porTipo).sort((a, b) => b[1] - a[1]).map(([t, n]) => (
                  <div key={t} className="flex items-center gap-2">
                    <span className="w-20 text-xs font-bold text-slate-600 shrink-0">{t}</span>
                    <div className="flex-1 bg-slate-100 rounded-full h-3"><div className="bg-indigo-500 h-3 rounded-full" style={{ width: `${(n / maxTipo) * 100}%` }} /></div>
                    <span className="w-6 text-xs font-black text-slate-700 text-right">{n}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="grid md:grid-cols-2 gap-3">
            {devs.map((d, i) => (
              <div key={i} className="bg-white rounded-2xl border border-slate-200 p-4 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between gap-2">
                  <div className="min-w-0">
                    <p className="font-black text-slate-800 truncate">{d.name || 'Promoción'}</p>
                    <p className="text-xs text-slate-500 truncate">{d.promoter || '—'}</p>
                  </div>
                  <span className={`px-2 py-0.5 rounded-lg text-[10px] font-black shrink-0 ${TIPO_COLOR[d.type] || TIPO_COLOR.Otro}`}>{d.type || 'Otro'}</span>
                </div>
                <div className="mt-2 space-y-1 text-[12px] text-slate-600">
                  {d.location && <p className="flex items-center gap-1.5"><MapPin size={13} className="text-slate-400" /> {d.location}</p>}
                  {d.address && <p className="flex items-center gap-1.5"><MapPin size={13} className="text-slate-300" /> {d.address}</p>}
                  {d.phone && <p className="flex items-center gap-1.5"><Phone size={13} className="text-slate-400" /> <a href={`tel:${d.phone}`} className="text-indigo-600 font-bold">{d.phone}</a></p>}
                  {(d.startDate || d.deliveryDate) && <p className="flex items-center gap-1.5"><Calendar size={13} className="text-slate-400" /> {d.startDate || '—'} → {d.deliveryDate || '—'}</p>}
                  {d.priceStart && <p className="flex items-center gap-1.5"><Tag size={13} className="text-slate-400" /> desde {d.priceStart}</p>}
                </div>
                {d.description && <p className="mt-2 text-[11px] text-slate-400 line-clamp-2">{d.description}</p>}
                {d.url && <a href={d.url} target="_blank" rel="noreferrer" className="mt-2 inline-flex items-center gap-1 text-xs font-bold text-indigo-600 hover:underline">Ver promoción <ExternalLink size={12} /></a>}
              </div>
            ))}
          </div>

          {result.summary && (
            <div className="bg-white rounded-2xl border border-slate-200 p-4">
              <p className="text-[10px] font-black text-slate-400 uppercase mb-1">Resumen del mercado</p>
              <p className="text-sm text-slate-600 whitespace-pre-line">{result.summary}</p>
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
    </div>
  );
};

export default PropData;
