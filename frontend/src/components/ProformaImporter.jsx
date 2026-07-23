import React, { useMemo, useRef, useState } from 'react';
import { Upload, Loader, FileText, Eye, EyeOff, Calculator } from 'lucide-react';
import { authHeaders } from '../services/api';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const getAuthHeaders = () => authHeaders({ 'Content-Type': 'application/json' });

// Importar PRESUPUESTO DE VENTA (solo MASTER). Sube el PDF con la relación de
// muebles, la IA detecta cada casco y su herraje (bisagras, patas, colgadores,
// guías). Tú metes la MANO DE OBRA (coste de producción) y el MARGEN en € que
// quieres ganar. Si el margen es 0, el resultado es tu coste.
const eur = (n) => (Number(n) || 0).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' €';

export default function ProformaImporter({ esMaster }) {
  const [oculto, setOculto] = useState(true);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState(null);
  const [items, setItems] = useState([]);
  const fileRef = useRef(null);

  // Precios de herraje (editables) + mano de obra y margen (TOTALES del trabajo).
  const [p, setP] = useState({
    bisagra: 7.46,   // € por bisagra BLUM (2 por puerta)
    pata: 1.20,      // € por pata (4 por mueble bajo/columna)
    colgador: 3.50,  // € por colgador (2 por mueble alto)
    guia: 90.27,     // € juego de guías/cajón BLUM (solo si el doc no lo incluye ya)
    manoObra: 0,     // € TOTAL de mano de obra (coste de producción)
    margen: 0,       // € TOTAL de margen a ganar (0 = coste)
  });
  const setNum = (k) => (e) => setP(prev => ({ ...prev, [k]: e.target.value === '' ? '' : Number(e.target.value) }));

  if (!esMaster) return null;

  const importar = async (file) => {
    if (!file) return;
    setCargando(true); setError(null); setItems([]);
    try {
      const b64 = await new Promise((res, rej) => {
        const fr = new FileReader(); fr.onload = () => res(fr.result); fr.onerror = rej; fr.readAsDataURL(file);
      });
      const r = await fetch(`${API_URL}/api/cascos/proforma`, {
        method: 'POST', headers: getAuthHeaders(), body: JSON.stringify({ pdfBase64: b64 }),
      });
      let d = {}; try { d = await r.json(); } catch { d = {}; }
      if (!r.ok) { setError(d.detail || d.error || `El servidor devolvió un error (${r.status}). Si el PDF es escaneado, la detección tarda más; reinténtalo.`); return; }
      if (d.success) setItems(d.items || []);
      else setError(d.detail || d.error || 'No se pudieron detectar los muebles.');
    } catch { setError('No se pudo conectar para analizar el PDF. Reinténtalo en unos segundos.'); }
    finally { setCargando(false); }
  };

  const calc = useMemo(() => {
    const rows = items.map(it => {
      const casco = Number(it.pvp) || 0;
      const bisagras = (it.puertas || 0) * 2 * (Number(p.bisagra) || 0);
      const patas = (it.tipo === 'bajo' || it.tipo === 'columna') ? 4 * (Number(p.pata) || 0) : 0;
      const colgadores = (it.tipo === 'alto') ? 2 * (Number(p.colgador) || 0) : 0;
      // Guías solo si el documento NO incluye ya el herraje BLUM (Merivobox).
      const guias = it.herrajeBlum ? 0 : ((it.cajones || 0) + (it.gavetas || 0)) * (Number(p.guia) || 0);
      const herraje = bisagras + patas + colgadores + guias;
      return { ...it, _casco: casco, _herraje: herraje, _bis: bisagras, _pat: patas, _col: colgadores, _gui: guias, _mat: casco + herraje };
    });
    const totMat = rows.reduce((a, r) => a + r._mat, 0);
    const totCasco = rows.reduce((a, r) => a + r._casco, 0);
    const totHerr = rows.reduce((a, r) => a + r._herraje, 0);
    const mo = Number(p.manoObra) || 0;
    const margen = Number(p.margen) || 0;
    const costeProduccion = totMat + mo;
    const precioVenta = costeProduccion + margen;
    return { rows, totMat, totCasco, totHerr, mo, margen, costeProduccion, precioVenta };
  }, [items, p]);

  return (
    <div className="bg-white border-2 border-amber-300 rounded-2xl overflow-hidden shadow-sm mb-4">
      <div className="flex items-center justify-between gap-3 px-4 py-3 bg-amber-50 border-b border-amber-200">
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-black uppercase tracking-widest text-amber-700 bg-amber-200 px-2 py-0.5 rounded">Solo master</span>
          <h3 className="text-sm font-black text-amber-900">Importar presupuesto de venta → coste / precio</h3>
        </div>
        <button onClick={() => setOculto(v => !v)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-black bg-white border border-amber-300 text-amber-800 hover:bg-amber-100">
          {oculto ? <><Eye size={14} /> Mostrar</> : <><EyeOff size={14} /> Ocultar</>}
        </button>
      </div>

      {!oculto && (
        <div className="p-4 space-y-4">
          <div className="flex items-center gap-3 flex-wrap">
            <button onClick={() => fileRef.current?.click()} disabled={cargando}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl font-black text-sm text-white bg-amber-600 hover:bg-amber-700 disabled:opacity-50">
              {cargando ? <Loader size={16} className="animate-spin" /> : <Upload size={16} />}
              {cargando ? 'Detectando muebles…' : 'Importar presupuesto de venta (PDF)'}
            </button>
            <input ref={fileRef} type="file" accept="application/pdf" className="hidden" onChange={e => importar(e.target.files?.[0])} />
            {items.length > 0 && <span className="text-xs font-bold text-slate-500 flex items-center gap-1"><FileText size={13} /> {items.length} líneas detectadas</span>}
          </div>
          {error && <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-sm text-red-700">{error}</div>}

          {items.length > 0 && (
            <>
              {/* Casillas: herraje + mano de obra + margen */}
              <div className="rounded-xl border border-slate-200 p-3">
                <div className="flex items-center gap-1.5 mb-2 text-slate-600"><Calculator size={14} /><span className="text-[11px] font-black uppercase tracking-wide">Herraje (precio unidad)</span></div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  {[['bisagra', 'Bisagra € (×2/puerta)'], ['pata', 'Pata € (×4/bajo)'], ['colgador', 'Colgador € (×2/alto)'], ['guia', 'Guía/cajón € (si no BLUM)']].map(([k, l]) => (
                    <label key={k} className="flex flex-col gap-1">
                      <span className="text-[10px] font-bold text-slate-400 uppercase">{l}</span>
                      <input type="number" step="any" value={p[k]} onChange={setNum(k)} className="px-2 py-1.5 border border-slate-200 rounded-lg text-sm" />
                    </label>
                  ))}
                </div>
                <div className="grid grid-cols-2 gap-2 mt-3">
                  <label className="flex flex-col gap-1">
                    <span className="text-[10px] font-black text-emerald-600 uppercase">Mano de obra € (coste producción)</span>
                    <input type="number" step="any" value={p.manoObra} onChange={setNum('manoObra')} className="px-2 py-1.5 border-2 border-emerald-200 rounded-lg text-sm font-bold" />
                  </label>
                  <label className="flex flex-col gap-1">
                    <span className="text-[10px] font-black text-indigo-600 uppercase">Margen € a ganar (0 = coste)</span>
                    <input type="number" step="any" value={p.margen} onChange={setNum('margen')} className="px-2 py-1.5 border-2 border-indigo-200 rounded-lg text-sm font-bold" />
                  </label>
                </div>
              </div>

              {/* Tabla de muebles detectados */}
              <div className="overflow-x-auto rounded-xl border border-slate-200">
                <table className="w-full text-xs" style={{ fontVariantNumeric: 'tabular-nums' }}>
                  <thead className="bg-slate-50 text-slate-500">
                    <tr className="text-left">
                      <th className="px-2 py-2">#</th><th className="px-2 py-2">Código</th><th className="px-2 py-2">Descripción</th>
                      <th className="px-2 py-2">Tipo</th><th className="px-2 py-2 text-center">P/C/G</th>
                      <th className="px-2 py-2 text-right">Casco</th><th className="px-2 py-2 text-right">Herraje</th>
                      <th className="px-2 py-2 text-right font-black">Coste mat.</th>
                    </tr>
                  </thead>
                  <tbody>
                    {calc.rows.map((r, i) => (
                      <tr key={i} className="border-t border-slate-100">
                        <td className="px-2 py-1.5">{r.n}</td>
                        <td className="px-2 py-1.5 font-mono">{r.cod}</td>
                        <td className="px-2 py-1.5 max-w-[200px] truncate" title={`${r.descripcion} · ${r.color}`}>{r.descripcion}{r.herrajeBlum && <span className="ml-1 text-[9px] font-black text-orange-600">BLUM</span>}</td>
                        <td className="px-2 py-1.5 capitalize text-slate-500">{r.tipo}</td>
                        <td className="px-2 py-1.5 text-center">{r.puertas}/{r.cajones}/{r.gavetas}</td>
                        <td className="px-2 py-1.5 text-right">{eur(r._casco)}</td>
                        <td className="px-2 py-1.5 text-right" title={`Bisagras ${eur(r._bis)} · Patas ${eur(r._pat)} · Colgadores ${eur(r._col)} · Guías ${eur(r._gui)}`}>{r._herraje ? eur(r._herraje) : '—'}</td>
                        <td className="px-2 py-1.5 text-right font-black text-slate-800">{eur(r._mat)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Resumen económico */}
              <div className="grid sm:grid-cols-2 gap-3">
                <div className="rounded-xl border border-slate-200 p-3 text-sm space-y-1">
                  <div className="flex justify-between"><span className="text-slate-500">Cascos</span><b>{eur(calc.totCasco)}</b></div>
                  <div className="flex justify-between"><span className="text-slate-500">Herraje (bisagras, patas, colgadores, guías)</span><b>{eur(calc.totHerr)}</b></div>
                  <div className="flex justify-between border-t border-slate-100 pt-1"><span className="text-slate-600 font-bold">Materiales</span><b>{eur(calc.totMat)}</b></div>
                  <div className="flex justify-between"><span className="text-emerald-600 font-bold">+ Mano de obra</span><b className="text-emerald-700">{eur(calc.mo)}</b></div>
                </div>
                <div className="rounded-xl border-2 border-indigo-200 bg-indigo-50/50 p-3 text-sm space-y-1">
                  <div className="flex justify-between"><span className="text-slate-600 font-bold">COSTE de producción</span><b className="text-slate-900">{eur(calc.costeProduccion)}</b></div>
                  <div className="flex justify-between"><span className="text-indigo-600 font-bold">+ Margen</span><b className="text-indigo-700">{eur(calc.margen)}</b></div>
                  <div className="flex justify-between border-t border-indigo-200 pt-1 text-base"><span className="font-black text-indigo-900">PRECIO DE VENTA</span><b className="text-indigo-900">{eur(calc.precioVenta)}</b></div>
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
