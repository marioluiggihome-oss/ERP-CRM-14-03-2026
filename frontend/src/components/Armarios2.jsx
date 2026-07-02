import React, { useMemo, useRef, useState, useEffect } from 'react';
import { Hammer, Plus, Trash2, Download, Columns, Package, Ruler, Sparkles, Image as ImageIcon, Loader, Lock, Maximize2, X } from 'lucide-react';
import { getToken } from '../services/api';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const authH = () => ({ 'Authorization': `Bearer ${getToken()}`, 'Content-Type': 'application/json' });
const DOOR_TYPES = [['open', 'Sin puertas'], ['sliding', 'Corredera'], ['hinged', 'Batiente'], ['folding', 'Plegable'], ['coplanar', 'Coplanar']];

// ── Catálogo (tarifas reales Finsa) y precios de accesorios (opción B: determinista) ──
const MATERIALS = [
  { id: '010B', name: 'Blanco Standard', pricePerSqm: 28.0, color: '#ffffff' },
  { id: '25V', name: 'Roble Virginia', pricePerSqm: 38.5, color: '#d4b483' },
  { id: '17G', name: 'Pino Cervino', pricePerSqm: 36.2, color: '#e8e4d8' },
  { id: '453B', name: 'Boeta Blanco', pricePerSqm: 34.5, color: '#f5f5f5' },
  { id: '91Y', name: 'Roble Dafne', pricePerSqm: 39.0, color: '#e2d2ba' },
  { id: '231N', name: 'Negro Liso', pricePerSqm: 32.5, color: '#1a1a1a' },
  { id: '195G', name: 'Gris Sarela', pricePerSqm: 31.0, color: '#bcbcbc' },
];
const COMPONENT_PRICES = { shelf: 28, 'hanging-rod': 22, drawer: 115, 'divider-v': 65, 'shoe-rack': 110, 'pant-rack': 125, 'led-strip': 55 };
const LABELS = { shelf: 'Balda', 'hanging-rod': 'Barra colgador', drawer: 'Cajón', 'divider-v': 'Divisor vertical', 'shoe-rack': 'Zapatero', 'pant-rack': 'Pantalonero', 'led-strip': 'LED' };
const PALETTE = ['shelf', 'hanging-rod', 'drawer', 'shoe-rack', 'pant-rack', 'led-strip'];
const eur = (n) => `${(Number(n) || 0).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} €`;
// Oscurece/aclara un color hex una cantidad (-1..1) para dar volumen a los tableros.
const shade = (hex, amt) => {
  let h = String(hex || '#cccccc').replace('#', '');
  if (h.length === 3) h = h.split('').map(c => c + c).join('');
  const num = parseInt(h, 16);
  const cl = (v) => Math.max(0, Math.min(255, Math.round(v)));
  const r = cl((num >> 16) + 255 * amt), g = cl(((num >> 8) & 255) + 255 * amt), b = cl((num & 255) + 255 * amt);
  return `#${(r << 16 | g << 8 | b).toString(16).padStart(6, '0')}`;
};

let _cid = 0;
const nid = () => `c${Date.now().toString(36)}${(_cid++)}`;

const Armarios2 = ({ state }) => {
  const isAdmin = state?.currentUser?.isAdmin === true;
  const [fullImg, setFullImg] = useState(null);
  const [cfg, setCfg] = useState({
    width: 2000, height: 2400, depth: 600, thickness: 19,
    materialId: '010B', projectType: 'armario', doorType: 'open', adminMargin: 40, cliente: '', ref: '',
  });
  const [planLoading, setPlanLoading] = useState(false);
  const [renders, setRenders] = useState([]);
  const [renderLoading, setRenderLoading] = useState(false);
  const [editText, setEditText] = useState('');
  const [aiError, setAiError] = useState('');
  const [comps, setComps] = useState([
    { id: nid(), type: 'divider-v', x: 50 },
    { id: nid(), type: 'shelf', y: 30, sectionIndex: 0 },
    { id: nid(), type: 'hanging-rod', y: 12, sectionIndex: 1 },
  ]);
  const [selId, setSelId] = useState(null);
  const [activeSection, setActiveSection] = useState(0);
  const set = (k, v) => setCfg(c => ({ ...c, [k]: v }));
  const material = MATERIALS.find(m => m.id === cfg.materialId) || MATERIALS[0];

  // Secciones (entre divisores verticales)
  const boundaries = useMemo(() => {
    const xs = comps.filter(c => c.type === 'divider-v').map(c => c.x).sort((a, b) => a - b);
    return [0, ...xs, 100];
  }, [comps]);
  const numSections = boundaries.length - 1;
  useEffect(() => { if (activeSection >= numSections) setActiveSection(0); }, [numSections, activeSection]);

  // ── SVG + arrastre ──
  const svgRef = useRef(null);
  const box = useRef(null);
  const [drag, setDrag] = useState(null); // {id, axis}
  const PAD = 44, MAXH = 460;
  const [W, setW] = useState(560);
  useEffect(() => {
    const on = () => { if (box.current) setW(Math.max(300, Math.min(760, box.current.clientWidth - 24))); };
    on(); window.addEventListener('resize', on); return () => window.removeEventListener('resize', on);
  }, []);
  const ratio = cfg.height / cfg.width;
  // Encaja el dibujo dentro del ancho disponible y de una altura máxima; luego se centra.
  let innerW = W - PAD * 2;
  let innerH = innerW * ratio;
  if (innerH > MAXH) { innerH = MAXH; innerW = innerH / ratio; }
  const vbW = innerW + PAD * 2;
  const vbH = innerH + PAD * 2;

  const onMove = (e) => {
    if (!drag || !svgRef.current) return;
    const r = svgRef.current.getBoundingClientRect();
    const cx = ('touches' in e ? e.touches[0].clientX : e.clientX);
    const cy = ('touches' in e ? e.touches[0].clientY : e.clientY);
    // El SVG puede estar escalado (maxWidth); mapear por fracción del área interior en px reales.
    const padPxX = (PAD / vbW) * r.width, innerPxW = (innerW / vbW) * r.width;
    const padPxY = (PAD / vbH) * r.height, innerPxH = (innerH / vbH) * r.height;
    if (drag.axis === 'y') {
      let p = ((cy - r.top - padPxY) / innerPxH) * 100;
      p = Math.max(2, Math.min(98, p));
      setComps(cs => cs.map(c => c.id === drag.id ? { ...c, y: Math.round(p) } : c));
    } else {
      let p = ((cx - r.left - padPxX) / innerPxW) * 100;
      p = Math.max(8, Math.min(92, p));
      setComps(cs => cs.map(c => c.id === drag.id ? { ...c, x: Math.round(p) } : c));
    }
  };
  useEffect(() => {
    if (!drag) return;
    const up = () => setDrag(null);
    window.addEventListener('mouseup', up); window.addEventListener('touchend', up);
    return () => { window.removeEventListener('mouseup', up); window.removeEventListener('touchend', up); };
  }, [drag]);

  const addComp = (type) => {
    if (type === 'divider-v') { setComps(cs => [...cs, { id: nid(), type, x: 50 }]); return; }
    const c = { id: nid(), type, y: 40, sectionIndex: activeSection };
    setComps(cs => [...cs, c]); setSelId(c.id);
  };
  const delComp = (id) => { setComps(cs => cs.filter(c => c.id !== id)); if (selId === id) setSelId(null); };

  // ── Presupuesto determinista (opción B) ──
  const budget = useMemo(() => {
    const priceSqm = material.pricePerSqm * (cfg.thickness / 19);
    const areaM2 = (cfg.width * cfg.height * 3) / 1e6; // costados+techo+base aprox
    const baseCost = areaM2 * priceSqm;
    let accesorios = 0; const counts = {};
    comps.forEach(c => { accesorios += COMPONENT_PRICES[c.type] || 0; counts[c.type] = (counts[c.type] || 0) + 1; });
    const structAdj = cfg.projectType === 'vestidor' ? 0.9 : 1.0;
    const coste = (baseCost * structAdj + accesorios + 350) * 1.35; // montaje/herrajes/transporte
    const pvp = coste * (1 + (Number(cfg.adminMargin) || 0) / 100);
    // Despiece
    const t = cfg.thickness; const cut = [
      { p: 'Costado Izq.', q: 1, w: cfg.depth, h: cfg.height },
      { p: 'Costado Der.', q: 1, w: cfg.depth, h: cfg.height },
      { p: 'Techo', q: 1, w: cfg.depth, h: cfg.width - t * 2 },
      { p: 'Base', q: 1, w: cfg.depth, h: cfg.width - t * 2 },
    ];
    comps.forEach(c => {
      if (c.type === 'divider-v') cut.push({ p: 'Divisor vertical', q: 1, w: cfg.depth, h: cfg.height - t * 2 });
      else if (c.type === 'shelf') cut.push({ p: 'Balda', q: 1, w: cfg.depth - 10, h: 400 });
      else if (c.type === 'drawer') cut.push({ p: 'Frente cajón', q: 1, w: 400, h: 180 });
    });
    return { baseCost, accesorios, coste, pvp: Math.round(pvp), counts, cut };
  }, [cfg, comps, material]);

  const readFile = (file) => new Promise((res) => { const fr = new FileReader(); fr.onload = () => res(String(fr.result)); fr.onerror = () => res(null); fr.readAsDataURL(file); });

  const subirPlano = async (file) => {
    if (!file) return;
    setPlanLoading(true); setAiError('');
    try {
      const b64 = await readFile(file);
      const r = await fetch(`${API_URL}/api/armarios2/plan`, { method: 'POST', headers: authH(), body: JSON.stringify({ imageBase64: b64 }) });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail || 'Error');
      setCfg(c => ({ ...c, width: d.width || c.width, height: d.height || c.height, depth: d.depth || c.depth }));
    } catch (e) { setAiError(e.message || 'No se pudo analizar el plano.'); }
    finally { setPlanLoading(false); }
  };

  const interiorResumen = () => {
    const byType = {};
    comps.filter(c => c.type !== 'divider-v').forEach(c => { byType[c.type] = (byType[c.type] || 0) + 1; });
    const secc = comps.filter(c => c.type === 'divider-v').length + 1;
    return `${secc} secciones. ` + Object.entries(byType).map(([t, n]) => `${n} ${LABELS[t] || t}`).join(', ');
  };

  const generarRender = async (edit) => {
    setRenderLoading(true); setAiError('');
    try {
      const prev = edit && renders.length ? renders[renders.length - 1] : null;
      const r = await fetch(`${API_URL}/api/armarios2/render`, {
        method: 'POST', headers: authH(),
        body: JSON.stringify({
          width: cfg.width, height: cfg.height, depth: cfg.depth,
          material: material.name, projectType: cfg.projectType, doorType: cfg.doorType,
          interior: interiorResumen(), editInstruction: edit || '', previousImageBase64: prev,
        }),
      });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail || 'Error');
      if (d.imageUrl) setRenders(rs => [...rs, d.imageUrl]);
      setEditText('');
    } catch (e) { setAiError(e.message || 'No se pudo generar el render.'); }
    finally { setRenderLoading(false); }
  };

  const exportCut = () => {
    const rows = budget.cut.map(x => [x.p, x.q, x.w, x.h, material.name].join(';'));
    const csv = ['Pieza;Uds;Ancho(mm);Alto(mm);Material', ...rows].join('\n');
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' }));
    a.download = `despiece_armario_${(cfg.ref || 'proyecto')}.csv`; a.click();
  };

  // Serializa el SVG del diseño a una imagen (para ampliar/descargar)
  const svgToDataUrl = () => {
    const svg = svgRef.current; if (!svg) return null;
    const xml = new XMLSerializer().serializeToString(svg);
    return 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(xml)));
  };
  const descargarDiseno = () => {
    const url = svgToDataUrl(); if (!url) return;
    const img = new Image();
    img.onload = () => {
      const c = document.createElement('canvas'); c.width = vbW * 2; c.height = vbH * 2;
      const ctx = c.getContext('2d'); ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, c.width, c.height);
      ctx.drawImage(img, 0, 0, c.width, c.height);
      const a = document.createElement('a'); a.href = c.toDataURL('image/png'); a.download = `armario_${cfg.ref || 'diseno'}.png`; a.click();
    };
    img.src = url;
  };

  // Render helpers
  const secX = (i) => [PAD + (boundaries[i] / 100) * innerW, PAD + (boundaries[i + 1] / 100) * innerW];

  return (
    <div className="h-full flex flex-col p-4 sm:p-6 pb-24 bg-slate-50 overflow-y-auto">
      <div className="rounded-2xl bg-gradient-to-r from-purple-600 via-fuchsia-600 to-rose-500 text-white px-4 py-3 mb-4 shadow-lg flex items-center gap-3 flex-wrap">
        <h1 className="ml-14 sm:ml-2 text-base sm:text-lg font-black flex items-center gap-2"><Hammer size={18} /> Armarios 2 · Interior a medida</h1>
        <p className="hidden sm:block text-xs text-white/80">Arrastra baldas, barras y cajones a la altura que quieras. Presupuesto por tarifas.</p>
      </div>

      <div className="grid lg:grid-cols-[1fr_360px] gap-4 items-start">
        {/* Configurador */}
        <div ref={box} className="space-y-4">
          {/* Medidas y material */}
          <div className="bg-white rounded-2xl border border-slate-200 p-4 grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[['Ancho (mm)', 'width'], ['Alto (mm)', 'height'], ['Fondo (mm)', 'depth']].map(([lab, k]) => (
              <div key={k}><label className="text-[10px] font-black text-slate-400 uppercase block mb-1">{lab}</label>
                <input type="number" value={cfg[k]} onChange={e => set(k, Number(e.target.value) || 0)} className="w-full px-2 py-2 border border-slate-200 rounded-lg text-sm" /></div>
            ))}
            <div><label className="text-[10px] font-black text-slate-400 uppercase block mb-1">Grosor</label>
              <select value={cfg.thickness} onChange={e => set('thickness', Number(e.target.value))} className="w-full px-2 py-2 border border-slate-200 rounded-lg text-sm bg-white">
                {[16, 19, 25].map(t => <option key={t} value={t}>{t} mm</option>)}
              </select></div>
            <div className="col-span-2"><label className="text-[10px] font-black text-slate-400 uppercase block mb-1">Material</label>
              <select value={cfg.materialId} onChange={e => set('materialId', e.target.value)} className="w-full px-2 py-2 border border-slate-200 rounded-lg text-sm bg-white">
                {MATERIALS.map(m => <option key={m.id} value={m.id}>{m.name} · {m.pricePerSqm}€/m²</option>)}
              </select></div>
            <div><label className="text-[10px] font-black text-slate-400 uppercase block mb-1">Tipo</label>
              <select value={cfg.projectType} onChange={e => set('projectType', e.target.value)} className="w-full px-2 py-2 border border-slate-200 rounded-lg text-sm bg-white">
                <option value="armario">Armario</option><option value="vestidor">Vestidor</option>
              </select></div>
            <div><label className="text-[10px] font-black text-slate-400 uppercase block mb-1">Puerta</label>
              <select value={cfg.doorType} onChange={e => set('doorType', e.target.value)} className="w-full px-2 py-2 border border-slate-200 rounded-lg text-sm bg-white">
                {DOOR_TYPES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
              </select></div>
            <div><label className="text-[10px] font-black text-slate-400 uppercase mb-1 flex items-center gap-1">Margen % <Lock size={10} className="text-slate-400" /></label>
              {isAdmin
                ? <input type="number" value={cfg.adminMargin} onChange={e => set('adminMargin', Number(e.target.value) || 0)} className="w-full px-2 py-2 border border-slate-200 rounded-lg text-sm" />
                : <div className="w-full px-2 py-2 border border-slate-200 rounded-lg text-sm bg-slate-50 text-slate-400 flex items-center gap-1" title="Solo el administrador ve/edita el margen"><Lock size={12} /> Oculto</div>}
            </div>
            <label className="col-span-2 flex items-center justify-center gap-2 px-3 py-2 bg-slate-100 rounded-lg text-xs font-bold text-slate-600 cursor-pointer hover:bg-slate-200">
              {planLoading ? <Loader size={14} className="animate-spin" /> : <Ruler size={14} />} Medidas desde plano (IA)
              <input type="file" accept="image/*,application/pdf" className="hidden" onChange={e => { const f = e.target.files?.[0]; if (f) subirPlano(f); }} />
            </label>
          </div>

          {/* Paleta */}
          <div className="bg-white rounded-2xl border border-slate-200 p-3 flex flex-wrap items-center gap-2">
            <button onClick={() => addComp('divider-v')} className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 text-white rounded-lg text-xs font-bold"><Columns size={14} /> Divisor</button>
            <span className="text-slate-300">|</span>
            {numSections > 1 && (
              <div className="flex items-center gap-1">
                <span className="text-[10px] font-black text-slate-400 uppercase">Añadir en:</span>
                {Array.from({ length: numSections }).map((_, i) => (
                  <button key={i} onClick={() => setActiveSection(i)} className={`w-6 h-6 rounded text-xs font-black ${activeSection === i ? 'bg-fuchsia-600 text-white' : 'bg-slate-100 text-slate-500'}`}>{i + 1}</button>
                ))}
              </div>
            )}
            {PALETTE.map(t => (
              <button key={t} onClick={() => addComp(t)} className="flex items-center gap-1.5 px-3 py-1.5 bg-fuchsia-50 text-fuchsia-700 rounded-lg text-xs font-bold hover:bg-fuchsia-100"><Plus size={13} /> {LABELS[t]}</button>
            ))}
          </div>

          {/* Visor 2D con arrastre */}
          <div className="bg-gradient-to-b from-white to-slate-50 rounded-2xl border border-slate-200 p-3 shadow-sm">
            <div className="flex items-center justify-between mb-1 px-1">
              <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Alzado · interior a medida</span>
              <div className="flex items-center gap-1.5">
                <button onClick={() => setFullImg(svgToDataUrl())} title="Ampliar" className="p-1.5 rounded-lg bg-slate-100 text-slate-600 hover:bg-slate-200"><Maximize2 size={14} /></button>
                <button onClick={descargarDiseno} title="Descargar diseño" className="p-1.5 rounded-lg bg-slate-100 text-slate-600 hover:bg-slate-200"><Download size={14} /></button>
              </div>
            </div>
            <svg ref={svgRef} viewBox={`0 0 ${vbW} ${vbH}`} width={vbW} height={vbH} style={{ maxWidth: '100%', height: 'auto' }} className="select-none touch-none mx-auto block"
              onMouseMove={onMove} onTouchMove={onMove}>
              <defs>
                <linearGradient id="mat" x1="0" y1="0" x2="1" y2="1">
                  <stop offset="0%" stopColor={shade(material.color, 0.10)} />
                  <stop offset="100%" stopColor={shade(material.color, -0.06)} />
                </linearGradient>
                <linearGradient id="slab" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={shade(material.color, -0.12)} />
                  <stop offset="100%" stopColor={shade(material.color, -0.28)} />
                </linearGradient>
                <filter id="sh" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="0" dy="3" stdDeviation="4" floodColor="#0f172a" floodOpacity="0.18" /></filter>
              </defs>
              {/* Fondo trasero + carcasa con marco (costados/techo/base) */}
              <rect x={PAD} y={PAD} width={innerW} height={innerH} rx="4" fill="url(#mat)" stroke="#1e293b" strokeWidth="1.5" filter="url(#sh)" />
              {(() => { const t = Math.max(6, cfg.thickness * 0.5); return (<g fill={shade(material.color, -0.22)} stroke="#1e293b" strokeWidth="0.6">
                <rect x={PAD} y={PAD} width={t} height={innerH} /><rect x={PAD + innerW - t} y={PAD} width={t} height={innerH} />
                <rect x={PAD} y={PAD} width={innerW} height={t} /><rect x={PAD} y={PAD + innerH - t} width={innerW} height={t} />
              </g>); })()}
              {/* Sombreado suave por sección */}
              {Array.from({ length: numSections }).map((_, i) => { const [a, b] = secX(i); return i % 2 ? <rect key={i} x={a} y={PAD} width={b - a} height={innerH} fill="#000" opacity="0.03" /> : null; })}
              {/* Cotas */}
              <text x={PAD + innerW / 2} y={PAD - 16} textAnchor="middle" fontSize="12" fontWeight="800" fill="#334155">{cfg.width} mm</text>
              <text x={PAD - 16} y={PAD + innerH / 2} textAnchor="middle" fontSize="12" fontWeight="800" fill="#334155" transform={`rotate(-90 ${PAD - 16} ${PAD + innerH / 2})`}>{cfg.height} mm</text>

              {/* Divisores verticales (arrastre X) */}
              {comps.filter(c => c.type === 'divider-v').map(c => {
                const x = PAD + (c.x / 100) * innerW; const sel = selId === c.id; const tw = Math.max(5, cfg.thickness * 0.45);
                return (
                  <g key={c.id} onMouseDown={() => { setDrag({ id: c.id, axis: 'x' }); setSelId(c.id); }} onTouchStart={() => { setDrag({ id: c.id, axis: 'x' }); setSelId(c.id); }} style={{ cursor: 'ew-resize' }}>
                    <rect x={x - 8} y={PAD} width={16} height={innerH} fill="transparent" />
                    <rect x={x - tw / 2} y={PAD + 4} width={tw} height={innerH - 8} rx="1" fill={sel ? '#c026d3' : 'url(#slab)'} stroke={sel ? '#a21caf' : '#1e293b'} strokeWidth="0.8" />
                  </g>
                );
              })}

              {/* Componentes horizontales por sección (arrastre Y) */}
              {comps.filter(c => c.type !== 'divider-v').map(c => {
                const si = Math.min(c.sectionIndex ?? 0, numSections - 1);
                const [x1, x2] = secX(si); const w = (x2 - x1) - 10; const xx = x1 + 5;
                const y = PAD + ((c.y ?? 40) / 100) * innerH; const sel = selId === c.id;
                const st = sel ? '#c026d3' : '#1e293b';
                let shape;
                if (c.type === 'shelf') shape = <rect x={xx} y={y - 3} width={w} height={6} rx="1" fill={sel ? '#c026d3' : 'url(#slab)'} stroke={st} strokeWidth="0.8" />;
                else if (c.type === 'drawer') { const dh = Math.min(30, innerH * 0.11); shape = <g><rect x={xx} y={y} width={w} height={dh} rx="2" fill={sel ? '#c026d3' : 'url(#slab)'} stroke={st} strokeWidth="1" /><rect x={xx + w / 2 - 12} y={y + dh / 2 - 1.5} width="24" height="3" rx="1.5" fill="#0f172a" opacity="0.5" /></g>; }
                else if (c.type === 'hanging-rod') shape = <g><line x1={xx} y1={y} x2={xx + w} y2={y} stroke={sel ? '#c026d3' : '#334155'} strokeWidth="2.5" strokeLinecap="round" />{[0.25, 0.5, 0.75].map((f, k) => <path key={k} d={`M ${xx + w * f} ${y} q -5 6 0 12 q 5 -6 0 -12`} fill="none" stroke="#64748b" strokeWidth="1.4" />)}</g>;
                else if (c.type === 'led-strip') shape = <g><line x1={xx} y1={y} x2={xx + w} y2={y} stroke="#fbbf24" strokeWidth="6" opacity="0.35" strokeLinecap="round" /><line x1={xx} y1={y} x2={xx + w} y2={y} stroke="#f59e0b" strokeWidth="2" strokeDasharray="7 4" strokeLinecap="round" /></g>;
                else if (c.type === 'shoe-rack') shape = <g>{[0, 1, 2].map(k => <line key={k} x1={xx} y1={y + k * 7} x2={xx + w} y2={y + k * 7 - 5} stroke={sel ? '#c026d3' : '#10b981'} strokeWidth="2.5" strokeLinecap="round" />)}</g>;
                else if (c.type === 'pant-rack') shape = <g><line x1={xx} y1={y} x2={xx + w} y2={y} stroke={sel ? '#c026d3' : '#14b8a6'} strokeWidth="2" />{[0.15, 0.35, 0.55, 0.75].map((f, k) => <line key={k} x1={xx + w * f} y1={y} x2={xx + w * f} y2={y + 16} stroke="#14b8a6" strokeWidth="2" strokeLinecap="round" />)}</g>;
                else shape = <line x1={xx} y1={y} x2={xx + w} y2={y} stroke={st} strokeWidth="4" strokeLinecap="round" />;
                return (
                  <g key={c.id} onMouseDown={() => { setDrag({ id: c.id, axis: 'y' }); setSelId(c.id); }} onTouchStart={() => { setDrag({ id: c.id, axis: 'y' }); setSelId(c.id); }} style={{ cursor: 'ns-resize' }}>
                    <rect x={xx} y={y - 9} width={w} height={22} fill="transparent" />
                    {shape}
                    {sel && <text x={xx + 2} y={y - 12} fontSize="10" fontWeight="800" fill="#c026d3">{LABELS[c.type]} · {Math.round((100 - (c.y ?? 40)) / 100 * cfg.height)}mm</text>}
                  </g>
                );
              })}
            </svg>
            {selId && (
              <div className="flex items-center justify-between mt-2 px-1">
                <span className="text-xs font-bold text-slate-500">Seleccionado: {LABELS[(comps.find(c => c.id === selId) || {}).type] || '—'} · arrastra para mover</span>
                <button onClick={() => delComp(selId)} className="flex items-center gap-1 text-xs font-bold text-rose-600 hover:text-rose-700"><Trash2 size={13} /> Eliminar</button>
              </div>
            )}
          </div>
        </div>

        <div className="space-y-4">
        {/* Render IA */}
        <div className="bg-white rounded-2xl border border-slate-200 p-4">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-black text-slate-800 flex items-center gap-2 text-sm"><Sparkles size={16} className="text-fuchsia-600" /> Render IA</h3>
            <button onClick={() => generarRender('')} disabled={renderLoading} className="flex items-center gap-1.5 px-3 py-1.5 bg-fuchsia-600 text-white rounded-lg text-xs font-bold hover:bg-fuchsia-700 disabled:opacity-50">{renderLoading ? <Loader size={14} className="animate-spin" /> : <ImageIcon size={14} />} Generar</button>
          </div>
          {renders.length > 0 ? (
            <>
              <img src={renders[renders.length - 1]} alt="Render armario" className="w-full rounded-xl border border-slate-100" />
              <div className="flex gap-2 mt-2">
                <input value={editText} onChange={e => setEditText(e.target.value)} placeholder="Editar: 'puertas correderas negras'…" className="flex-1 px-3 py-2 border border-slate-200 rounded-lg text-xs" onKeyDown={e => { if (e.key === 'Enter' && editText.trim()) generarRender(editText.trim()); }} />
                <button onClick={() => editText.trim() && generarRender(editText.trim())} disabled={renderLoading || !editText.trim()} className="px-3 py-2 bg-slate-800 text-white rounded-lg text-xs font-bold disabled:opacity-50">Editar</button>
              </div>
            </>
          ) : (
            <p className="text-xs text-slate-400 text-center py-6">Genera una imagen realista del armario con la configuración actual.</p>
          )}
          {aiError && <p className="text-xs text-rose-600 font-bold mt-2">{aiError}</p>}
        </div>

        {/* Presupuesto */}
        <div className="bg-white rounded-2xl border border-slate-200 p-4 h-fit lg:sticky lg:top-4">
          <h3 className="font-black text-slate-800 flex items-center gap-2 mb-3"><Package size={18} /> Presupuesto</h3>
          <input value={cfg.cliente} onChange={e => set('cliente', e.target.value)} placeholder="Cliente" className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm mb-2" />
          <input value={cfg.ref} onChange={e => set('ref', e.target.value)} placeholder="Referencia" className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm mb-3" />
          <div className="space-y-1 text-sm">
            <div className="flex justify-between text-slate-500"><span>Estructura ({material.name})</span><span className="font-bold">{eur(budget.baseCost)}</span></div>
            <div className="flex justify-between text-slate-500"><span>Accesorios interior</span><span className="font-bold">{eur(budget.accesorios)}</span></div>
            <div className="flex justify-between text-slate-500"><span>Coste producción</span><span className="font-bold">{eur(budget.coste)}</span></div>
            <div className="flex justify-between text-slate-900 text-xl font-black pt-1 bg-orange-50 -mx-1 px-2 rounded-lg py-1"><span>PVP</span><span className="text-orange-600">{eur(budget.pvp)}</span></div>
          </div>
          <div className="mt-3 border-t border-slate-100 pt-2">
            <p className="text-[10px] font-black text-slate-400 uppercase mb-1">Interior</p>
            {Object.entries(budget.counts).map(([t, n]) => <div key={t} className="flex justify-between text-[11px] text-slate-500"><span>{LABELS[t] || t}</span><span>×{n}</span></div>)}
          </div>
          <button onClick={exportCut} className="mt-3 w-full flex items-center justify-center gap-2 px-3 py-2 bg-slate-800 text-white rounded-xl font-bold text-sm hover:bg-slate-900"><Download size={15} /> Despiece (CSV)</button>
          <p className="text-[10px] text-slate-400 mt-2">PDF: próxima fase. Precios por tarifas (opción B).</p>
        </div>
        </div>
      </div>

      {fullImg && (
        <div className="fixed inset-0 bg-black/80 z-[200] flex items-center justify-center p-4" onClick={() => setFullImg(null)}>
          <img src={fullImg} alt="Diseño armario" className="max-w-full max-h-full object-contain bg-white rounded-xl p-4" onClick={e => e.stopPropagation()} />
          <button onClick={() => setFullImg(null)} className="absolute top-4 right-4 p-2 bg-white/20 text-white rounded-xl"><X size={22} /></button>
          <button onClick={descargarDiseno} className="absolute bottom-4 right-4 flex items-center gap-2 px-4 py-2 bg-white text-slate-900 rounded-xl font-bold"><Download size={16} /> Descargar</button>
        </div>
      )}
    </div>
  );
};

export default Armarios2;
