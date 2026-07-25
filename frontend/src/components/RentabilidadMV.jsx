import React, { useEffect, useMemo, useState } from 'react';
import { Plus, Trash2, Loader, Calculator, TrendingUp } from 'lucide-react';
import { authHeaders } from '../services/api';
import { CASCOS } from '../data/cascos';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const H = () => authHeaders({ 'Content-Type': 'application/json' });
const eur = (n) => (Number(n) || 0).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' €';

// Coste del casco ACB antracita (grafito 19): precio base x2 (punto) x -50% x -28%.
const cascoACB = (tipoAcb, ancho, alto) => {
  const pool = CASCOS.filter(c => c.tipo === tipoAcb && c.grosor === 19 && c.precios && c.precios.grafito != null);
  if (!pool.length) return { coste: 0, med: '' };
  let best = pool[0], bd = Infinity;
  for (const c of pool) {
    const d = Math.abs((c.ancho || 0) - ancho) * 3 + Math.abs((c.alto || 0) - alto);
    if (d < bd) { bd = d; best = c; }
  }
  return { coste: best.precios.grafito * 2 * 0.5 * 0.72, med: `${best.ancho}x${best.alto}` };
};

// Descompone un código MV (Fase 1: BAJO y ALTO) en componentes + coste.
const despiece = (item, p) => {
  const cod = item.cod, alturaAlto = item.altura; // altura solo para altos (70/90)
  const dio = /D\/I/.test(cod);
  let m;
  if ((m = cod.match(/^B(\d{2,3})/))) {
    const w = parseInt(m[1], 10) * 10;
    const wCasco = w < 300 ? 300 : w;
    const puertas = dio ? 1 : 2;
    const cc = cascoACB('Bajo Con Balda', wCasco, 800);
    const areaP = (w / 1000) * 0.713;               // frente ~713 mm alto
    return {
      fam: 'Bajo', med: cc.med, inc: w < 300 ? 'inc. corte 25→30' : '',
      casco: cc.coste, puerta: areaP * (Number(p.doorM2) || 0), puertas,
      bisagras: puertas * 2 * (Number(p.bisagra) || 0), patas: Number(p.pata4) || 0,
      colg: 0, soportes: 0, mo: Number(p.mano) || 0,
    };
  }
  if ((m = cod.match(/^A(\d{2,3})/))) {
    const w = parseInt(m[1], 10) * 10;
    const puertas = dio ? 1 : 2;
    const altoMm = (alturaAlto === '90' ? 900 : 700);
    const cc = cascoACB('Alto Con Balda', w, altoMm);
    const areaP = (w / 1000) * (altoMm / 1000);
    const baldas = alturaAlto === '90' ? 2 : 1;
    return {
      fam: 'Alto', med: cc.med, inc: '',
      casco: cc.coste, puerta: areaP * (Number(p.doorM2) || 0), puertas,
      bisagras: puertas * 2 * (Number(p.bisagra) || 0), patas: 0,
      colg: 2 * (Number(p.colgador) || 0), soportes: baldas * 4 * (Number(p.soporte) || 0),
      mo: Number(p.mano) || 0,
    };
  }
  return null;
};

export default function RentabilidadMV({ esMaster }) {
  const [pv, setPv] = useState(3.33);
  const [familias, setFamilias] = useState(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState(null);
  const [lineas, setLineas] = useState([]);   // [{cod, altura, puntos, cant}]
  const [sel, setSel] = useState('');
  const [alturaSel, setAlturaSel] = useState('70');
  const [cant, setCant] = useState(1);
  // Costes de componentes (editables).
  const [p, setP] = useState({
    doorM2: 30,   // € coste puerta/frente por m2
    bisagra: 3.07, pata4: 0.64, colgador: 3.50, soporte: 0.30, mano: 20,
  });
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

  const puntosDe = (cod, altura) => {
    if (!familias) return 0;
    const bajo = familias.BAJO?.items || {};
    if (bajo[cod] != null) return bajo[cod];
    // ALTO tipo h7090: items[cod] = [puntos70, puntos90]
    const alto = familias.ALTO;
    if (alto?.items && alto.items[cod] != null) {
      const v = alto.items[cod];
      return Array.isArray(v) ? v[altura === '90' ? 1 : 0] : v;
    }
    return 0;
  };

  const anadir = () => {
    if (!sel) return;
    const esAlto = /^A/.test(sel);
    const puntos = puntosDe(sel, alturaSel);
    setLineas(prev => [...prev, { cod: sel, altura: esAlto ? alturaSel : '', puntos, cant: Math.max(1, Number(cant) || 1) }]);
  };

  const calc = useMemo(() => {
    const rows = lineas.map(l => {
      const d = despiece({ cod: l.cod, altura: l.altura }, p) || {};
      const coste = (d.casco || 0) + (d.puerta || 0) + (d.bisagras || 0) + (d.patas || 0) + (d.colg || 0) + (d.soportes || 0) + (d.mo || 0);
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
        <span className="text-[11px] text-emerald-500 ml-auto">valor punto {pv} €</span>
      </div>
      <div className="p-4 space-y-4">
        {cargando && <div className="text-sm text-slate-500 flex items-center gap-2"><Loader size={14} className="animate-spin" /> Cargando tarifa MV…</div>}
        {error && <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-sm text-red-700">{error}</div>}

        {/* Añadir mueble */}
        {familias && (
          <div className="flex items-end gap-2 flex-wrap bg-slate-50 border border-slate-200 rounded-xl p-3">
            <label className="flex flex-col gap-1">
              <span className="text-[10px] font-bold text-slate-400 uppercase">Código MV (bajo/alto)</span>
              <select value={sel} onChange={e => setSel(e.target.value)} className="px-2 py-1.5 border border-slate-200 rounded-lg text-sm min-w-[160px]">
                <option value="">Elegir…</option>
                <optgroup label="BAJOS">
                  {Object.keys(familias.BAJO?.items || {}).map(c => <option key={c} value={c}>{c} · {familias.BAJO.items[c]} pts</option>)}
                </optgroup>
                {familias.ALTO?.items && (
                  <optgroup label="ALTOS (70/90)">
                    {Object.keys(familias.ALTO.items).map(c => <option key={c} value={c}>{c}</option>)}
                  </optgroup>
                )}
              </select>
            </label>
            {/^A/.test(sel) && (
              <label className="flex flex-col gap-1">
                <span className="text-[10px] font-bold text-slate-400 uppercase">Altura</span>
                <select value={alturaSel} onChange={e => setAlturaSel(e.target.value)} className="px-2 py-1.5 border border-slate-200 rounded-lg text-sm">
                  <option value="70">70</option><option value="90">90</option>
                </select>
              </label>
            )}
            <label className="flex flex-col gap-1">
              <span className="text-[10px] font-bold text-slate-400 uppercase">Cant.</span>
              <input type="number" min="1" value={cant} onChange={e => setCant(e.target.value)} className="px-2 py-1.5 border border-slate-200 rounded-lg text-sm w-16" />
            </label>
            <button onClick={anadir} disabled={!sel} className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-black bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-50"><Plus size={14} /> Añadir</button>
          </div>
        )}

        {/* Parámetros de coste */}
        <div className="rounded-xl border border-slate-200 p-3">
          <div className="flex items-center gap-1.5 mb-2 text-slate-600"><Calculator size={14} /><span className="text-[11px] font-black uppercase tracking-wide">Costes de componente (editables)</span></div>
          <div className="grid grid-cols-2 sm:grid-cols-6 gap-2">
            {[['doorM2', 'Puerta €/m²'], ['bisagra', 'Bisagra €'], ['pata4', 'Patas (4) €'], ['colgador', 'Colgador €'], ['soporte', 'Soporte balda €'], ['mano', 'Mano obra €']].map(([k, l]) => (
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
                    <td className="px-2 py-1.5 text-center">{r.cant}</td>
                    <td className="px-2 py-1.5 text-right">{eur(r.casco * r.cant)}</td>
                    <td className="px-2 py-1.5 text-right">{eur(r.puerta * r.cant)}</td>
                    <td className="px-2 py-1.5 text-right">{eur(r.bisagras * r.cant)}</td>
                    <td className="px-2 py-1.5 text-right">{eur((r.patas + r.colg + r.soportes) * r.cant)}</td>
                    <td className="px-2 py-1.5 text-right">{eur(r.mo * r.cant)}</td>
                    <td className="px-2 py-1.5 text-right font-bold">{eur(r.coste)}</td>
                    <td className="px-2 py-1.5 text-right text-slate-500">{eur(r.pvp)}</td>
                    <td className={`px-2 py-1.5 text-right font-black ${r.margen >= 0 ? 'text-emerald-700' : 'text-red-600'}`}>{eur(r.margen)} <span className="text-[9px]">({r.pvp ? Math.round(r.margen / r.pvp * 100) : 0}%)</span></td>
                    <td className="px-2 py-1.5"><button onClick={() => setLineas(prev => prev.filter((_, j) => j !== i))} className="text-red-400 hover:text-red-600"><Trash2 size={13} /></button></td>
                  </tr>
                ))}
              </tbody>
              <tfoot className="bg-emerald-50 font-black text-slate-800">
                <tr className="border-t-2 border-emerald-300">
                  <td className="px-2 py-2" colSpan={7}>TOTAL COCINA</td>
                  <td className="px-2 py-2 text-right">{eur(calc.tot.coste)}</td>
                  <td className="px-2 py-2 text-right">{eur(calc.tot.pvp)}</td>
                  <td className="px-2 py-2 text-right text-emerald-800">{eur(calc.tot.margen)} <span className="text-[10px]">({calc.tot.pvp ? Math.round(calc.tot.margen / calc.tot.pvp * 100) : 0}%)</span></td>
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
