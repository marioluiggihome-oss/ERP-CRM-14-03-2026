import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Plus, Trash2, Loader, Calculator, TrendingUp, Upload, Lock, Unlock } from 'lucide-react';
import { authHeaders } from '../services/api';
import { CASCOS } from '../data/cascos';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const H = () => authHeaders({ 'Content-Type': 'application/json' });
const eur = (n) => (Number(n) || 0).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' €';

// Precio del color: antracita (grafito) preferente; si el tipo no lo tiene
// (columnas), el mejor disponible.
const COLOR_PRIO = ['grafito', 'aluminio', 'blancoEsp', 'blanco', 'roble', 'olmo', 'stone', 'spike'];
const precioColor = (c) => { if (!c || !c.precios) return null; for (const k of COLOR_PRIO) if (c.precios[k] != null) return c.precios[k]; return null; };

// Coste del casco ACB: precio base × 2 (valor punto) × −50% × −28% (= base × 0,72).
const cascoACB = (tipoAcb, ancho, alto) => {
  const pool = CASCOS.filter(c => c.tipo === tipoAcb && precioColor(c) != null);
  const p19 = pool.filter(c => c.grosor === 19);
  const use = p19.length ? p19 : pool;
  if (!use.length) return { coste: 0, med: '' };
  let best = use[0], bd = Infinity;
  for (const c of use) {
    const d = Math.abs((c.ancho || 0) - ancho) * 3 + Math.abs((c.alto || 0) - alto);
    if (d < bd) { bd = d; best = c; }
  }
  return { coste: (precioColor(best) || 0) * 2 * 0.5 * 0.72, med: `${best.ancho}x${best.alto}` };
};

// Reglas de descomposición por familia MV (Fase 2). Cada regla dice: tipo de casco
// ACB, altura, si lleva patas/colgadores, cuántas puertas (dio=según D/I), cajones,
// gavetas, baldas. 'dio' = 1 si el código lleva D/I, 2 si no.
const RULES = {
  BAJO: { casco: 'Bajo Con Balda', alto: 800, patas: 1, puertas: 'dio', baldas: 1 },
  BAJO_FREGADERO: { casco: 'Bajo Fregadero', alto: 800, patas: 1, puertas: 'dio' },
  BAJO_RINCON_CIEGO: { casco: 'Bajo Con Balda', alto: 800, patas: 1, puertas: 1 },
  BAJO_RINCON_ESCUADRA: { casco: 'Bajo Con Balda', alto: 800, patas: 1, puertas: 2 },
  BAJO_HORNO: { casco: 'Bajo Con Balda', alto: 800, patas: 1, puertas: 0, cajFn: c => /BHC|BHZ/.test(c) ? 1 : 0, gavFn: c => /BHG/.test(c) ? 1 : 0 },
  BAJO_TERMINAL: { casco: 'Bajo Con Balda', alto: 800, patas: 1, puertasFn: c => /BTP/.test(c) ? 1 : 0, baldas: 1 },
  BAJO_PUERTA_CAJON: { casco: 'Bajo Con Balda', alto: 800, patas: 1, puertas: 'dio', cajones: 1 },
  BAJO_5_CAJONES: { casco: 'Bajo Con Balda', alto: 800, patas: 1, puertas: 0, cajones: 5 },
  BAJO_3CAJ_1GAV: { casco: 'Bajo Con Balda', alto: 800, patas: 1, puertas: 0, cajones: 3, gavetas: 1 },
  BAJO_2GAV_1CAJ: { casco: 'Bajo Con Balda', alto: 800, patas: 1, puertas: 0, cajones: 1, gavetas: 2 },
  BAJO_2CAJ_1GAV_1FRENTE: { casco: 'Bajo Con Balda', alto: 800, patas: 1, puertas: 0, cajones: 2, gavetas: 1 },
  BAJO_2GAV_1FRENTE: { casco: 'Bajo Con Balda', alto: 800, patas: 1, puertas: 0, gavetas: 2 },
  ALTO: { casco: 'Alto Con Balda', altoSel: true, colg: 1, puertas: 'dio', baldasSel: true },
  ALTO_DECORATIVO: { casco: 'Alto Con Balda', altoSel: true, colg: 1, puertas: 0, baldasSel: true },
  ALTO_VITRINA: { casco: 'Alto Con Balda', altoSel: true, colg: 1, puertas: 'dio', vitrina: true },
  ALTO_ESCURREPLATOS: { casco: 'Alto Con Balda', altoSel: true, colg: 1, puertas: 'dio' },
  ALTO_MICROONDAS: { casco: 'Alto Con Balda', altoSel: true, colg: 1, puertas: 'dio' },
  ALTO_CAMPANA: { casco: 'Alto Con Balda', altoSel: true, colg: 1, puertas: 'dio' },
  ALTO_CALENTADOR: { casco: 'Alto Con Balda', altoSel: true, colg: 1, puertas: 'dio' },
  ALTO_CALDERA: { casco: 'Alto Con Balda', altoSel: true, colg: 1, puertas: 'dio' },
  ALTO_SOBREFRIGO: { casco: 'Alto Con Balda', altoSel: true, colg: 1, puertas: 'dio' },
  ALTO_TERMINAL: { casco: 'Alto Con Balda', altoSel: true, colg: 1, puertas: 1 },
  ALTO_RINCON_CIEGO: { casco: 'Alto Con Balda', altoSel: true, colg: 1, puertas: 1 },
  ALTO_RINCON_ESCUADRA: { casco: 'Alto Con Balda', altoSel: true, colg: 1, puertas: 2 },
  ALTO_RINCON_CHAFLAN: { casco: 'Alto Con Balda', altoSel: true, colg: 1, puertas: 1 },
  ALTO_ABATIBLE: { casco: 'Alto Con Balda', altoSel: true, colg: 1, puertas: 2 },
  ALTO_COMBINADO: { casco: 'Alto Con Balda', altoSel: true, colg: 1, puertas: 2 },
  ALTO_COMBINADO_PLUS: { casco: 'Alto Con Balda', altoSel: true, colg: 1, puertas: 2 },
  ALTO_COMBINADO_PLUS_J: { casco: 'Alto Con Balda', altoSel: true, colg: 1, puertas: 2 },
  ALTILLO: { casco: 'Alto Con Balda', altoSel: true, colg: 1, puertas: 1 },
  ALTILLO_VITRINA: { casco: 'Alto Con Balda', altoSel: true, colg: 1, puertas: 1, vitrina: true },
  COLUMNA_DESPENSERO: { casco: 'Columna Despensa', altoCol: true, patas: 1, puertas: 2, baldas: 4 },
  COLUMNA_FRIGO: { casco: 'Columna Despensa', altoCol: true, patas: 1, puertas: 2 },
  COLUMNA_HORNO: { casco: 'Columna Despensa', altoCol: true, patas: 1, puertas: 2 },
  COLUMNA_HORNO_MICRO: { casco: 'Columna Despensa', altoCol: true, patas: 1, puertas: 2 },
  MEDIACOLUMNA: { casco: 'Semicolumna Despensa', alto: 1300, patas: 1, puertas: 'dio', baldas: 2 },
  MEDIA_PUERTA_GAVETA: { casco: 'Semicolumna Despensa', alto: 1300, patas: 1, puertas: 1, gavetas: 1 },
  MEDIACOLUMNA_HORNO: { casco: 'Semicolumna Despensa', alto: 1300, patas: 1, puertas: 1 },
  MEDIACOLUMNA_VITRINA: { casco: 'Semicolumna Despensa', alto: 1300, patas: 1, puertas: 'dio', vitrina: true },
  MEDIACOL_VITRINA_GAVETA: { casco: 'Semicolumna Despensa', alto: 1300, patas: 1, puertas: 1, gavetas: 1, vitrina: true },
};
const RULE_GENERICA = { casco: 'Bajo Con Balda', alto: 800, patas: 1, puertas: 1, generica: true };

// Ancho (mm) del prefijo numérico del código.
const anchoDe = (cod) => { const m = (cod || '').match(/(\d{2,3})/); return m ? parseInt(m[1], 10) * 10 : 600; };

// Descompone un código MV según la regla de su familia.
const despiece = (item, p) => {
  const cod = item.cod, altura = item.altura, familia = item.familia;
  const R = RULES[familia] || RULE_GENERICA;
  const dio = /D\/I/.test(cod);
  const w = anchoDe(cod);
  const wCasco = w < 300 ? 300 : w;
  const altoMm = R.altoSel ? (altura === '90' ? 900 : 700) : (R.altoCol ? (altura === '220' ? 2200 : 2000) : (R.alto || 800));
  const cc = cascoACB(R.casco, wCasco, altoMm);
  // Puertas
  let puertas = 0;
  if (R.puertasFn) puertas = R.puertasFn(cod);
  else if (R.puertas === 'dio') puertas = dio ? 1 : 2;
  else puertas = R.puertas || 0;
  const cajones = (R.cajFn ? R.cajFn(cod) : (R.cajones || 0));
  const gavetas = (R.gavFn ? R.gavFn(cod) : (R.gavetas || 0));
  const baldas = R.baldasSel ? (altura === '90' ? 2 : 1) : (R.baldas || 0);
  // Puerta: superficie × €/m² (+30% si es vitrina, por cristal/perfil)
  const altoFrente = R.altoCol ? altoMm : (R.altoSel ? altoMm : 713);
  const areaP = puertas > 0 ? (w / 1000) * (altoFrente / 1000) : 0;
  const doorRate = (Number(p.doorM2) || 0) * (R.vitrina ? 1.3 : 1);
  return {
    fam: familia, med: cc.med, inc: w < 300 ? 'inc. corte' : '',
    casco: cc.coste,
    puerta: areaP * doorRate, puertas,
    bisagras: puertas * 2 * (Number(p.bisagra) || 0),
    patas: R.patas ? (Number(p.pata4) || 0) : 0,
    colg: R.colg ? 2 * (Number(p.colgador) || 0) : 0,
    caj: cajones * (Number(p.cajon) || 0), gav: gavetas * (Number(p.gaveta) || 0),
    soportes: baldas * 4 * (Number(p.soporte) || 0),
    mo: Number(p.mano) || 0, generica: R.generica || false,
  };
};

export default function RentabilidadMV({ esMaster, seed }) {
  const [pv, setPv] = useState(3.33);
  const [familias, setFamilias] = useState(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState(null);
  const [lineas, setLineas] = useState([]);   // [{cod, altura, puntos, cant}]
  const [sel, setSel] = useState('');
  const [alturaSel, setAlturaSel] = useState('70');
  const [pvpVisible, setPvpVisible] = useState(false);       // clic en candado → ver PVP
  const [margenVisible, setMargenVisible] = useState(false); // Shift+clic → ver también coste/margen
  const [cant, setCant] = useState(1);
  // Costes de componentes (editables).
  const P_DEFAULT = { doorM2: 30, bisagra: 3.07, pata4: 0.64, colgador: 3.50, soporte: 0.30, mano: 20, cajon: 41.34, gaveta: 54.37 };
  const [p, setP] = useState(() => {
    try { const s = JSON.parse(localStorage.getItem('mv_costes') || 'null'); return s ? { ...P_DEFAULT, ...s } : P_DEFAULT; } catch { return P_DEFAULT; }
  });
  useEffect(() => { try { localStorage.setItem('mv_costes', JSON.stringify(p)); } catch { /* noop */ } }, [p]);
  const setNum = (k) => (e) => setP(prev => ({ ...prev, [k]: e.target.value === '' ? '' : Number(e.target.value) }));

  useEffect(() => {
    if (!esMaster) return;
    setCargando(true);
    fetch(`${API_URL}/api/cascos/mv/tarifa?tariff=T1`, { headers: H() })
      .then(r => r.json())
      .then(d => { if (d.success) { setFamilias(d.familias); setPv(d.pointValue || 3.33); } else setError(d.detail || 'No se pudo cargar la tarifa MV.'); })
      .catch(() => setError('Error al cargar la tarifa MV.'))
      .finally(() => setCargando(false));
  }, [esMaster]);

  // Índice código → { familia, entry, type }. Cubre TODAS las familias con items.
  const codeIndex = useMemo(() => {
    const idx = {};
    if (!familias) return idx;
    Object.entries(familias).forEach(([fam, v]) => {
      if (v && v.items) Object.entries(v.items).forEach(([cod, entry]) => { idx[cod] = { familia: fam, entry, type: v.type }; });
    });
    return idx;
  }, [familias]);

  const familiaDe = (cod) => codeIndex[cod]?.familia || null;

  // Resuelve los puntos según el tipo de familia (single, dual, h7090, h127147, h200220).
  const puntosDe = (cod, altura) => {
    const it = codeIndex[cod]; if (!it) return 0;
    const e = it.entry;
    if (!Array.isArray(e)) return e;
    if (it.type === 'h7090') return e[altura === '90' ? 1 : 0];
    if (it.type === 'h200220') return e[altura === '220' ? 1 : 0];
    if (it.type === 'h127147') return e[altura === '147' ? 1 : 0];
    if (it.type === 'dual') return e[0]; // fregadero: precio normal (idx 0)
    return e[0];
  };
  // Opciones de altura según la familia del código.
  const alturasDe = (cod) => {
    const t = codeIndex[cod]?.type;
    if (t === 'h7090') return ['70', '90'];
    if (t === 'h200220') return ['200', '220'];
    if (t === 'h127147') return ['127', '147'];
    return [];
  };

  const anadir = () => {
    if (!sel) return;
    const alts = alturasDe(sel);
    const altura = alts.length ? alturaSel : '';
    setLineas(prev => [...prev, { cod: sel, familia: familiaDe(sel), altura, puntos: puntosDe(sel, altura), cant: Math.max(1, Number(cant) || 1) }]);
  };

  // Carga muebles precargados (p.ej. "coger del diseño" de Estudio 3D).
  const seedKey = JSON.stringify(seed || []);
  useEffect(() => {
    if (!familias || !seed || !seed.length) return;
    const nuevas = [];
    seed.forEach(s => {
      if (!codeIndex[s.cod]) return;
      const alts = alturasDe(s.cod);
      const altura = s.altura || (alts.length ? alts[alts.length - 1] : '');
      nuevas.push({ cod: s.cod, familia: familiaDe(s.cod), altura, puntos: puntosDe(s.cod, altura), cant: Math.max(1, Number(s.cant) || 1) });
    });
    if (nuevas.length) setLineas(nuevas);
  }, [seedKey, familias]); // eslint-disable-line

  // Importar una relación de muebles desde PDF: detecta los códigos y los añade.
  const fileRef = useRef(null);
  const [importando, setImportando] = useState(false);
  const [noSoportados, setNoSoportados] = useState([]);
  const importarPDF = async (file) => {
    if (!file || !familias) return;
    setImportando(true); setError(null); setNoSoportados([]);
    try {
      const b64 = await new Promise((res, rej) => { const fr = new FileReader(); fr.onload = () => res(fr.result); fr.onerror = rej; fr.readAsDataURL(file); });
      const r = await fetch(`${API_URL}/api/cascos/mv/detectar-pdf`, { method: 'POST', headers: H(), body: JSON.stringify({ pdfBase64: b64 }) });
      const d = await r.json().catch(() => ({}));
      if (!r.ok || !d.success) { setError(d.detail || 'No se pudieron detectar muebles en el PDF.'); return; }
      const nuevas = [], noSop = [];
      (d.codigos || []).forEach(c => {
        const cant = (d.conteo && d.conteo[c]) || 1;
        if (codeIndex[c]) {
          const alts = alturasDe(c);
          const altura = alts.length ? alts[alts.length - 1] : ''; // por defecto la mayor (90/220/147)
          nuevas.push({ cod: c, familia: familiaDe(c), altura, puntos: puntosDe(c, altura), cant });
        } else noSop.push(c);
      });
      if (nuevas.length) setLineas(prev => [...prev, ...nuevas]);
      setNoSoportados(noSop);
      if (!nuevas.length) setError('No se reconoció ningún código de bajo/alto en el PDF.');
    } catch { setError('Error al importar el PDF.'); }
    finally { setImportando(false); }
  };

  const calc = useMemo(() => {
    const rows = lineas.map(l => {
      const d = despiece({ cod: l.cod, altura: l.altura, familia: l.familia }, p) || {};
      const coste = (d.casco || 0) + (d.puerta || 0) + (d.bisagras || 0) + (d.patas || 0) + (d.colg || 0) + (d.caj || 0) + (d.gav || 0) + (d.soportes || 0) + (d.mo || 0);
      const pvp = (Number(l.puntos) || 0) * pv;
      return { ...l, ...d, costeUd: coste, pvpUd: pvp, coste: coste * l.cant, pvp: pvp * l.cant, margen: (pvp - coste) * l.cant };
    });
    const tot = rows.reduce((a, r) => ({ pvp: a.pvp + r.pvp, coste: a.coste + r.coste, margen: a.margen + r.margen }), { pvp: 0, coste: 0, margen: 0 });
    return { rows, tot };
  }, [lineas, p, pv]);

  if (!esMaster) return null;

  return (
    <div className="bg-white border-2 border-emerald-300 rounded-2xl overflow-hidden shadow-sm mb-4">
      <div className="flex items-center gap-2 px-4 py-3 bg-emerald-50 border-b border-emerald-200">
        <span className="text-[10px] font-black uppercase tracking-widest text-emerald-700 bg-emerald-200 px-2 py-0.5 rounded">Solo master</span>
        <h3 className="text-sm font-black text-emerald-900 flex items-center gap-1.5"><TrendingUp size={15} /> Rentabilidad Tarifa MV</h3>
        <button
          onClick={(e) => { if (e.shiftKey) setMargenVisible(v => !v); else setPvpVisible(v => !v); }}
          title="Clic: ver/ocultar PVP · Shift+clic: ver/ocultar coste y margen"
          className={`ml-auto flex items-center gap-1 px-2 py-1 rounded-lg text-[10px] font-black ${margenVisible ? 'bg-emerald-600 text-white' : (pvpVisible ? 'bg-emerald-200 text-emerald-800' : 'bg-white border border-emerald-300 text-emerald-700')}`}>
          {(pvpVisible || margenVisible) ? <Unlock size={12} /> : <Lock size={12} />} {margenVisible ? 'Coste' : (pvpVisible ? 'PVP' : 'Ver')}
        </button>
        <span className="text-[11px] text-emerald-500">punto {pv} €</span>
      </div>
      <div className="p-4 space-y-4">
        {cargando && <div className="text-sm text-slate-500 flex items-center gap-2"><Loader size={14} className="animate-spin" /> Cargando tarifa MV…</div>}
        {error && <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-sm text-red-700">{error}</div>}

        {/* Añadir mueble */}
        {familias && (
          <div className="flex items-end gap-2 flex-wrap bg-slate-50 border border-slate-200 rounded-xl p-3">
            <label className="flex flex-col gap-1">
              <span className="text-[10px] font-bold text-slate-400 uppercase">Código MV (bajo/alto)</span>
              <select value={sel} onChange={e => setSel(e.target.value)} className="px-2 py-1.5 border border-slate-200 rounded-lg text-sm min-w-[200px]">
                <option value="">Elegir…</option>
                {Object.entries(familias).filter(([, v]) => v && v.items).map(([fam, v]) => (
                  <optgroup key={fam} label={fam.replace(/_/g, ' ')}>
                    {Object.keys(v.items).map(c => <option key={c} value={c}>{c}</option>)}
                  </optgroup>
                ))}
              </select>
            </label>
            {alturasDe(sel).length > 0 && (
              <label className="flex flex-col gap-1">
                <span className="text-[10px] font-bold text-slate-400 uppercase">Altura</span>
                <select value={alturaSel} onChange={e => setAlturaSel(e.target.value)} className="px-2 py-1.5 border border-slate-200 rounded-lg text-sm">
                  {alturasDe(sel).map(h => <option key={h} value={h}>{h}</option>)}
                </select>
              </label>
            )}
            <label className="flex flex-col gap-1">
              <span className="text-[10px] font-bold text-slate-400 uppercase">Cant.</span>
              <input type="number" min="1" value={cant} onChange={e => setCant(e.target.value)} className="px-2 py-1.5 border border-slate-200 rounded-lg text-sm w-16" />
            </label>
            <button onClick={anadir} disabled={!sel} className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-black bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-50"><Plus size={14} /> Añadir</button>
            <span className="w-px h-8 bg-slate-200 mx-1" />
            <button onClick={() => fileRef.current?.click()} disabled={importando} className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-black bg-slate-800 text-white hover:bg-slate-900 disabled:opacity-50">
              {importando ? <Loader size={14} className="animate-spin" /> : <Upload size={14} />} {importando ? 'Detectando…' : 'Importar PDF'}
            </button>
            <input ref={fileRef} type="file" accept="application/pdf" className="hidden" onChange={e => importarPDF(e.target.files?.[0])} />
            {lineas.length > 0 && (
              <button onClick={() => setLineas([])} className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-bold bg-slate-100 text-slate-600 hover:bg-slate-200"><Trash2 size={14} /> Vaciar</button>
            )}
          </div>
        )}
        {noSoportados.length > 0 && (
          <div className="p-2.5 rounded-lg bg-amber-50 border border-amber-200 text-[11px] text-amber-800">
            <b>Códigos detectados aún no soportados</b> (Fase 2: cajoneras, columnas, rincones…): {noSoportados.join(', ')}
          </div>
        )}

        {/* Parámetros de coste */}
        <div className="rounded-xl border border-slate-200 p-3">
          <div className="flex items-center gap-1.5 mb-2 text-slate-600"><Calculator size={14} /><span className="text-[11px] font-black uppercase tracking-wide">Costes de componente (editables)</span></div>
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2">
            {[['doorM2', 'Puerta €/m²'], ['bisagra', 'Bisagra €'], ['cajon', 'Cajón €'], ['gaveta', 'Gaveta €'], ['pata4', 'Patas (4) €'], ['colgador', 'Colgador €'], ['soporte', 'Soporte balda €'], ['mano', 'Mano obra €']].map(([k, l]) => (
              <label key={k} className="flex flex-col gap-1">
                <span className="text-[10px] font-bold text-slate-400 uppercase">{l}</span>
                <input type="number" step="any" value={p[k]} onChange={setNum(k)} className="px-2 py-1.5 border border-slate-200 rounded-lg text-sm" />
              </label>
            ))}
          </div>
          <p className="text-[10px] text-slate-400 mt-2">Casco = ACB antracita (base ×2 −50% −28%). Puerta = superficie × €/m² (provisional, carga tu tarifa Alvic). Bisagras 2/puerta. Patas en bajos; colgadores + soportes en altos.</p>
        </div>

        {/* Tabla */}
        {calc.rows.length > 0 && (
          <div className="overflow-x-auto rounded-xl border border-slate-200">
            <table className="w-full text-xs" style={{ fontVariantNumeric: 'tabular-nums' }}>
              <thead className="bg-slate-50 text-slate-500">
                <tr className="text-left">
                  <th className="px-2 py-2">Código</th><th className="px-2 py-2 text-center">Cant.</th>
                  <th className="px-2 py-2 text-right">Casco</th><th className="px-2 py-2 text-right">Puerta</th><th className="px-2 py-2 text-right">Bisag.</th>
                  <th className="px-2 py-2 text-right">Otros</th><th className="px-2 py-2 text-right">M.O.</th>
                  <th className="px-2 py-2 text-right">Coste</th><th className="px-2 py-2 text-right">PVP</th><th className="px-2 py-2 text-right font-black">Margen</th><th className="px-2 py-2"></th>
                </tr>
              </thead>
              <tbody>
                {calc.rows.map((r, i) => (
                  <tr key={i} className="border-t border-slate-100">
                    <td className="px-2 py-1.5 font-mono">{r.cod}{r.altura ? `/${r.altura}` : ''} <span className="text-[9px] text-slate-400">{r.puntos}pts · {r.med}{r.inc ? ' ⚠' : ''}</span></td>
                    <td className="px-2 py-1.5 text-center">
                      <input type="number" min="1" value={r.cant}
                        onChange={e => { const v = Math.max(1, Number(e.target.value) || 1); setLineas(prev => prev.map((x, j) => j === i ? { ...x, cant: v } : x)); }}
                        className="w-12 px-1 py-0.5 border border-slate-200 rounded text-center text-xs" />
                    </td>
                    <td className="px-2 py-1.5 text-right">{margenVisible ? eur(r.casco * r.cant) : '•••'}</td>
                    <td className="px-2 py-1.5 text-right">{margenVisible ? eur(r.puerta * r.cant) : '•••'}</td>
                    <td className="px-2 py-1.5 text-right">{margenVisible ? eur(r.bisagras * r.cant) : '•••'}</td>
                    <td className="px-2 py-1.5 text-right" title={`Patas ${eur(r.patas)} · Colg ${eur(r.colg)} · Cajones ${eur(r.caj)} · Gavetas ${eur(r.gav)} · Soportes ${eur(r.soportes)}`}>{margenVisible ? eur((r.patas + r.colg + r.caj + r.gav + r.soportes) * r.cant) : '•••'}{r.generica && <span className="text-[9px] text-amber-600 ml-1">aprox</span>}</td>
                    <td className="px-2 py-1.5 text-right">{margenVisible ? eur(r.mo * r.cant) : '•••'}</td>
                    <td className="px-2 py-1.5 text-right font-bold">{margenVisible ? eur(r.coste) : '•••'}</td>
                    <td className="px-2 py-1.5 text-right text-slate-500">{pvpVisible ? eur(r.pvp) : '•••'}</td>
                    <td className={`px-2 py-1.5 text-right font-black ${r.margen >= 0 ? 'text-emerald-700' : 'text-red-600'}`}>{margenVisible ? <>{eur(r.margen)} <span className="text-[9px]">({r.pvp ? Math.round(r.margen / r.pvp * 100) : 0}%)</span></> : '•••'}</td>
                    <td className="px-2 py-1.5"><button onClick={() => setLineas(prev => prev.filter((_, j) => j !== i))} className="text-red-400 hover:text-red-600"><Trash2 size={13} /></button></td>
                  </tr>
                ))}
              </tbody>
              <tfoot className="bg-emerald-50 font-black text-slate-800">
                <tr className="border-t-2 border-emerald-300">
                  <td className="px-2 py-2" colSpan={7}>TOTAL COCINA</td>
                  <td className="px-2 py-2 text-right">{margenVisible ? eur(calc.tot.coste) : '•••'}</td>
                  <td className="px-2 py-2 text-right">{pvpVisible ? eur(calc.tot.pvp) : '•••'}</td>
                  <td className="px-2 py-2 text-right text-emerald-800">{margenVisible ? <>{eur(calc.tot.margen)} <span className="text-[10px]">({calc.tot.pvp ? Math.round(calc.tot.margen / calc.tot.pvp * 100) : 0}%)</span></> : '•••'}</td>
                  <td></td>
                </tr>
              </tfoot>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
