import React, { useMemo, useRef, useState } from 'react';
import { Upload, Loader, FileText, Eye, EyeOff, Calculator } from 'lucide-react';
import { authHeaders } from '../services/api';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const getAuthHeaders = () => authHeaders({ 'Content-Type': 'application/json' });

// Importador de PROFORMA de proveedor (solo MASTER). Sube un PDF con la relación
// de muebles, detecta cada mueble y calcula NUESTRO coste: casco (PVP × factor) +
// herraje BLUM (bisagras por puerta, cajones/gavetas si el PVP no lo incluye ya) +
// mano de obra por mueble. Pensado para Cocina Desmontada.
const eur = (n) => (Number(n) || 0).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' €';

export default function ProformaImporter({ esMaster }) {
  const [oculto, setOculto] = useState(true);   // arranca oculto; el master lo despliega
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState(null);
  const [items, setItems] = useState([]);
  const fileRef = useRef(null);

  // Parámetros de coste (editables por el master).
  const [p, setP] = useState({
    factorPvp: 100,    // % del PVP que es nuestro coste (100 = sin descuento)
    bisagra: 7.46,     // € por bisagra BLUM (2 por puerta)
    cajon: 90.27,      // € cajón BLUM ANTARO M
    gaveta: 127.49,    // € gaveta BLUM ANTARO D
    manoObra: 0,       // € mano de obra por mueble (se suma a cada mueble)
  });
  const setNum = (k) => (e) => setP(prev => ({ ...prev, [k]: e.target.value === '' ? '' : Number(e.target.value) }));

  if (!esMaster) return null;

  const subir = async (file) => {
    if (!file) return;
    setCargando(true); setError(null);
    try {
      const b64 = await new Promise((res, rej) => {
        const fr = new FileReader(); fr.onload = () => res(fr.result); fr.onerror = rej; fr.readAsDataURL(file);
      });
      const r = await fetch(`${API_URL}/api/cascos/proforma`, {
        method: 'POST', headers: getAuthHeaders(), body: JSON.stringify({ pdfBase64: b64 }),
      });
      const d = await r.json().catch(() => ({}));
      if (r.status === 403) { setError(d.detail || 'Solo el master puede importar proformas.'); return; }
      if (d.success) setItems(d.items || []);
      else setError(d.detail || d.error || 'No se pudieron detectar los muebles.');
    } catch { setError('Error al subir/analizar el PDF.'); }
    finally { setCargando(false); }
  };

  // Cálculo del coste por línea y totales.
  const calc = useMemo(() => {
    const f = (Number(p.factorPvp) || 0) / 100;
    const rows = items.map(it => {
      const casco = (Number(it.pvp) || 0) * f;
      const bisagras = (it.puertas || 0) * 2 * (Number(p.bisagra) || 0);
      // Si el PVP ya incluye herraje BLUM de cajón (Merivobox), no se vuelve a sumar.
      const drawers = it.herrajeBlum ? 0 : ((it.cajones || 0) * (Number(p.cajon) || 0) + (it.gavetas || 0) * (Number(p.gaveta) || 0));
      const mo = it.esMueble ? (Number(p.manoObra) || 0) : 0;
      const coste = casco + bisagras + drawers + mo;
      return { ...it, _casco: casco, _bisagras: bisagras, _drawers: drawers, _mo: mo, _coste: coste };
    });
    const tot = rows.reduce((a, r) => ({
      pvp: a.pvp + (Number(r.pvp) || 0), casco: a.casco + r._casco, bisagras: a.bisagras + r._bisagras,
      drawers: a.drawers + r._drawers, mo: a.mo + r._mo, coste: a.coste + r._coste,
    }), { pvp: 0, casco: 0, bisagras: 0, drawers: 0, mo: 0, coste: 0 });
    return { rows, tot };
  }, [items, p]);

  return (
    <div className="bg-white border-2 border-amber-300 rounded-2xl overflow-hidden shadow-sm mb-4">
      <div className="flex items-center justify-between gap-3 px-4 py-3 bg-amber-50 border-b border-amber-200">
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-black uppercase tracking-widest text-amber-700 bg-amber-200 px-2 py-0.5 rounded">Solo master</span>
          <h3 className="text-sm font-black text-amber-900">Importar proforma → coste nuestro</h3>
        </div>
        <button onClick={() => setOculto(v => !v)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-black bg-white border border-amber-300 text-amber-800 hover:bg-amber-100">
          {oculto ? <><Eye size={14} /> Mostrar</> : <><EyeOff size={14} /> Ocultar</>}
        </button>
      </div>

      {!oculto && (
        <div className="p-4 space-y-4">
          {/* Subir PDF */}
          <div className="flex items-center gap-3 flex-wrap">
            <button onClick={() => fileRef.current?.click()} disabled={cargando}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl font-black text-sm text-white bg-amber-600 hover:bg-amber-700 disabled:opacity-50">
              {cargando ? <Loader size={16} className="animate-spin" /> : <Upload size={16} />}
              {cargando ? 'Analizando PDF…' : 'Subir proforma (PDF)'}
            </button>
            <input ref={fileRef} type="file" accept="application/pdf" className="hidden"
              onChange={e => subir(e.target.files?.[0])} />
            {items.length > 0 && <span className="text-xs font-bold text-slate-500 flex items-center gap-1"><FileText size={13} /> {items.length} líneas detectadas</span>}
          </div>
          {error && <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-sm text-red-700">{error}</div>}

          {items.length > 0 && (
            <>
              {/* Parámetros de coste */}
              <div className="rounded-xl border border-slate-200 p-3">
                <div className="flex items-center gap-1.5 mb-2 text-slate-600"><Calculator size={14} /><span className="text-[11px] font-black uppercase tracking-wide">Parámetros de coste</span></div>
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
                  {[['factorPvp', '% del PVP'], ['bisagra', 'Bisagra BLUM €'], ['cajon', 'Cajón BLUM €'], ['gaveta', 'Gaveta BLUM €'], ['manoObra', 'Mano obra €/mueble']].map(([k, l]) => (
                    <label key={k} className="flex flex-col gap-1">
                      <span className="text-[10px] font-bold text-slate-400 uppercase">{l}</span>
                      <input type="number" step="any" value={p[k]} onChange={setNum(k)} className="px-2 py-1.5 border border-slate-200 rounded-lg text-sm" />
                    </label>
                  ))}
                </div>
                <p className="text-[10px] text-slate-400 mt-2">Bisagras = 2 × nº puertas. Cajones/gavetas solo se suman si el PVP <b>no</b> incluye ya el herraje BLUM (Merivobox). La mano de obra se suma a cada mueble.</p>
              </div>

              {/* Tabla */}
              <div className="overflow-x-auto rounded-xl border border-slate-200">
                <table className="w-full text-xs" style={{ fontVariantNumeric: 'tabular-nums' }}>
                  <thead className="bg-slate-50 text-slate-500">
                    <tr className="text-left">
                      <th className="px-2 py-2">#</th><th className="px-2 py-2">Código</th><th className="px-2 py-2">Descripción</th>
                      <th className="px-2 py-2 text-center">P/C/G</th><th className="px-2 py-2 text-right">PVP</th>
                      <th className="px-2 py-2 text-right">Casco</th><th className="px-2 py-2 text-right">Bisagras</th>
                      <th className="px-2 py-2 text-right">Cajón/gav.</th><th className="px-2 py-2 text-right">M.obra</th>
                      <th className="px-2 py-2 text-right font-black">Coste</th>
                    </tr>
                  </thead>
                  <tbody>
                    {calc.rows.map((r, i) => (
                      <tr key={i} className={`border-t border-slate-100 ${r.esMueble ? '' : 'text-slate-400'}`}>
                        <td className="px-2 py-1.5">{r.n}</td>
                        <td className="px-2 py-1.5 font-mono">{r.cod}</td>
                        <td className="px-2 py-1.5 max-w-[220px] truncate" title={`${r.descripcion} · ${r.color}`}>{r.descripcion}{r.herrajeBlum && <span className="ml-1 text-[9px] font-black text-orange-600">BLUM</span>}</td>
                        <td className="px-2 py-1.5 text-center">{r.puertas}/{r.cajones}/{r.gavetas}</td>
                        <td className="px-2 py-1.5 text-right">{eur(r.pvp)}</td>
                        <td className="px-2 py-1.5 text-right">{eur(r._casco)}</td>
                        <td className="px-2 py-1.5 text-right">{r._bisagras ? eur(r._bisagras) : '—'}</td>
                        <td className="px-2 py-1.5 text-right">{r._drawers ? eur(r._drawers) : '—'}</td>
                        <td className="px-2 py-1.5 text-right">{r._mo ? eur(r._mo) : '—'}</td>
                        <td className="px-2 py-1.5 text-right font-black text-slate-800">{eur(r._coste)}</td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot className="bg-amber-50 font-black text-slate-800">
                    <tr className="border-t-2 border-amber-300">
                      <td className="px-2 py-2" colSpan={4}>TOTALES ({items.length} líneas)</td>
                      <td className="px-2 py-2 text-right">{eur(calc.tot.pvp)}</td>
                      <td className="px-2 py-2 text-right">{eur(calc.tot.casco)}</td>
                      <td className="px-2 py-2 text-right">{eur(calc.tot.bisagras)}</td>
                      <td className="px-2 py-2 text-right">{eur(calc.tot.drawers)}</td>
                      <td className="px-2 py-2 text-right">{eur(calc.tot.mo)}</td>
                      <td className="px-2 py-2 text-right text-amber-800 text-sm">{eur(calc.tot.coste)}</td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
