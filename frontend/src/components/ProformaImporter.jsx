import React, { useMemo, useRef, useState } from 'react';
import { Upload, Loader, FileText, Eye, EyeOff, Calculator } from 'lucide-react';
import { authHeaders } from '../services/api';
import { CASCOS as _CASCOS_RAW } from '../data/cascos';

const CASCOS = Array.isArray(_CASCOS_RAW) ? _CASCOS_RAW : [];

const API_URL = process.env.REACT_APP_BACKEND_URL;
const getAuthHeaders = () => authHeaders({ 'Content-Type': 'application/json' });

// ── Equivalencia Alvic → casco ACB ──────────────────────────────────────────
// Mapa de la descripción Alvic al TIPO de casco del catálogo ACB (cascos.js).
const _TIPO_ACB = (desc, tipo) => {
  const t = (desc || '').toUpperCase();
  if (/PUERTA DE INTEGRACION|^PTA |ZOCALO|ZÓCALO|^REG |REGLETA|COPETE|COSTADO/.test(t)) return null; // no es casco
  if (t.includes('FREGADERO')) return 'Bajo Fregadero';
  // Placa/rincón bajo: usan el mismo casco estructural "Bajo Con Balda".
  if (t.includes('BAJO')) return 'Bajo Con Balda';
  // Semicolumna y columna (horno/micro/despensa) → casco estructural de columna.
  if (/SEMICOLUMNA/.test(t)) return 'Semicolumna Despensa';
  if (/COLUMNA/.test(t)) return 'Columna Despensa';
  // Sobremódulo = alto pequeño.
  if (/SOBREMODULO|SOBREMÓDULO|SOBRE MODULO|SOBRE COLUMNA/.test(t)) return 'Alto Con Balda';
  if (t.includes('ALTO') && t.includes('PLATERO')) return 'Alto Platero Con Balda';
  if (t.includes('ALTO') || t.includes('ALTILLO')) return 'Alto Con Balda';
  return tipo === 'bajo' ? 'Bajo Con Balda' : (tipo === 'alto' ? 'Alto Con Balda' : (tipo === 'columna' ? 'Columna Despensa' : null));
};
// Prioridad de color: ANTRACITA (grafito) primero; luego el mejor disponible.
const _COLOR_PRIO = ['grafito', 'aluminio', 'blancoEsp', 'blanco', 'roble', 'olmo', 'stone', 'spike', 'robleAurora', 'blancoHidrofugo'];
const _COLOR_LBL = { grafito: 'Antracita', aluminio: 'Aluminio', blancoEsp: 'Blanco', blanco: 'Blanco', roble: 'Roble', olmo: 'Olmo' };
const _precio_color = (c) => {
  if (!c || !c.precios) return null;
  for (const col of _COLOR_PRIO) if (c.precios[col] != null) return { precio: c.precios[col], color: col };
  return null;
};
// Ancho del mueble: del prefijo numérico del código Alvic (cm) o de las medidas.
const _ancho_mm = (it) => {
  const m = /^(\d{2,3})/.exec(it.cod || '');
  const porCodigo = m ? parseInt(m[1], 10) * 10 : 0;
  const cand = [porCodigo, Number(it.ancho) || 0, Number(it.largo) || 0].filter(v => v >= 150 && v <= 1200);
  return cand[0] || porCodigo || 600;
};
// Busca el casco ACB (gama kit, 16mm) del tipo indicado más cercano en ancho.
const _match_acb = (it) => {
  const tipoAcb = _TIPO_ACB(it.descripcion, it.tipo);
  if (!tipoAcb) return null;
  const w = _ancho_mm(it);
  // Preferente: ANTRACITA (grafito) 19mm. Si el tipo no lo tiene (columnas),
  // el mejor color disponible de ese tipo.
  let pool = CASCOS.filter(c => c.tipo === tipoAcb && c.grosor === 19 && c.precios && c.precios.grafito != null);
  if (!pool.length) pool = CASCOS.filter(c => c.tipo === tipoAcb && _precio_color(c) != null);
  if (!pool.length) return null;
  let best = pool[0], bd = Infinity;
  for (const c of pool) { const d = Math.abs((c.ancho || 0) - w); if (d < bd) { bd = d; best = c; } }
  const pc = _precio_color(best);
  return { ...best, _precio: pc ? pc.precio : 0, _color: pc ? pc.color : '', _colorLbl: pc ? (_COLOR_LBL[pc.color] || pc.color) : '' };
};

// Importar PRESUPUESTO DE VENTA (solo MASTER). Sube el PDF con la relación de
// muebles, la IA detecta cada casco y su herraje (bisagras, patas, colgadores,
// guías). Tú metes la MANO DE OBRA (coste de producción) y el MARGEN en € que
// quieres ganar. Si el margen es 0, el resultado es tu coste.
const eur = (n) => (Number(n) || 0).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' €';

export default function ProformaImporter({ esMaster }) {
  const [oculto, setOculto] = useState(false);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState(null);
  const [items, setItems] = useState([]);
  const fileRef = useRef(null);

  // Precios de herraje (editables) + mano de obra y margen (TOTALES del trabajo).
  const [p, setP] = useState({
    desc1: 50,       // 1er descuento sobre la tarifa del casco (ACB: -50% deshace el punto x2)
    desc2: 28,       // 2º descuento sobre la tarifa del casco (ACB: -28% real)
    bisagra: 7.46,   // € por bisagra BLUM (2 por puerta)
    pata: 1.20,      // € por pata (4 por mueble bajo/columna)
    colgador: 3.50,  // € por colgador (2 por mueble alto)
    cajon: 90.27,    // € cajón BLUM ANTARO M (por cada cajón)
    gaveta: 127.49,  // € gaveta BLUM ANTARO D (por cada gaveta)
    manoObra: 0,     // € TOTAL de mano de obra (coste de producción)
    margen: 0,       // € TOTAL de margen a ganar (0 = coste)
  });
  const setNum = (k) => (e) => setP(prev => ({ ...prev, [k]: e.target.value === '' ? '' : Number(e.target.value) }));

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
    } catch (e) { setError(`No se pudo conectar para analizar el PDF (${e?.message || 'error de red'}). Si el PDF es escaneado tarda más; reinténtalo.`); }
    finally { setCargando(false); }
  };

  const calc = useMemo(() => {
    const facCasco = (1 - (Number(p.desc1) || 0) / 100) * (1 - (Number(p.desc2) || 0) / 100);
    const rows = items.map(it => {
      const acb = _match_acb(it);                              // casco ACB equivalente (antracita 19)
      const precioAcb = acb ? (Number(acb._precio) || 0) : 0;
      const casco = precioAcb * facCasco;                      // coste = tarifa ACB -50% -28%
      const bisagras = (it.puertas || 0) * 2 * (Number(p.bisagra) || 0);
      const patas = (it.tipo === 'bajo' || it.tipo === 'columna') ? 4 * (Number(p.pata) || 0) : 0;
      const colgadores = (it.tipo === 'alto') ? 2 * (Number(p.colgador) || 0) : 0;
      // Cajones y gavetas SIEMPRE con BLUM (precios separados).
      const guias = (it.cajones || 0) * (Number(p.cajon) || 0) + (it.gavetas || 0) * (Number(p.gaveta) || 0);
      const herraje = bisagras + patas + colgadores + guias;
      return { ...it, _acb: acb, _precioAcb: precioAcb, _casco: casco, _herraje: herraje, _bis: bisagras, _pat: patas, _col: colgadores, _gui: guias, _mat: casco + herraje };
    });
    const totMat = rows.reduce((a, r) => a + r._mat, 0);
    const totCasco = rows.reduce((a, r) => a + r._casco, 0);
    const totHerr = rows.reduce((a, r) => a + r._herraje, 0);
    const totPuertas = rows.reduce((a, r) => a + (r.puertas || 0), 0);   // a cotizar aparte
    const sinMatch = rows.filter(r => r.esMueble && !r._acb).length;
    const mo = Number(p.manoObra) || 0;
    const margen = Number(p.margen) || 0;
    const costeProduccion = totMat + mo;
    const precioVenta = costeProduccion + margen;
    return { rows, totMat, totCasco, totHerr, totPuertas, sinMatch, mo, margen, costeProduccion, precioVenta };
  }, [items, p]);

  // Guard DESPUÉS de todos los hooks (evita el error de nº de hooks al llegar el usuario).
  if (!esMaster) return null;

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
                <div className="flex items-center gap-1.5 mb-2 text-slate-600"><Calculator size={14} /><span className="text-[11px] font-black uppercase tracking-wide">Coste del casco (descuentos sobre tarifa)</span></div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-3">
                  {[['desc1', 'Dto casco 1 % (−50)'], ['desc2', 'Dto casco 2 % (−28)']].map(([k, l]) => (
                    <label key={k} className="flex flex-col gap-1">
                      <span className="text-[10px] font-bold text-slate-400 uppercase">{l}</span>
                      <input type="number" step="any" value={p[k]} onChange={setNum(k)} className="px-2 py-1.5 border-2 border-amber-200 rounded-lg text-sm font-bold" />
                    </label>
                  ))}
                </div>
                <div className="flex items-center gap-1.5 mb-2 text-slate-600"><span className="text-[11px] font-black uppercase tracking-wide">Herraje (precio unidad) · cajones y gavetas siempre con BLUM</span></div>
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
                  {[['bisagra', 'Bisagra € (×2/puerta)'], ['pata', 'Pata € (×4/bajo)'], ['colgador', 'Colgador € (×2/alto)'], ['cajon', 'Cajón BLUM €'], ['gaveta', 'Gaveta BLUM €']].map(([k, l]) => (
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
                      <th className="px-2 py-2">Casco ACB (equiv.)</th><th className="px-2 py-2 text-center">P/C/G</th>
                      <th className="px-2 py-2 text-right">Tarifa ACB</th><th className="px-2 py-2 text-right">Casco coste</th><th className="px-2 py-2 text-right">Herraje</th>
                      <th className="px-2 py-2 text-right font-black">Coste mat.</th>
                    </tr>
                  </thead>
                  <tbody>
                    {calc.rows.map((r, i) => (
                      <tr key={i} className="border-t border-slate-100">
                        <td className="px-2 py-1.5">{r.n}</td>
                        <td className="px-2 py-1.5 font-mono">{r.cod}</td>
                        <td className="px-2 py-1.5 max-w-[200px] truncate" title={`${r.descripcion} · ${r.color}`}>{r.descripcion}{r.herrajeBlum && <span className="ml-1 text-[9px] font-black text-orange-600">BLUM</span>}</td>
                        <td className="px-2 py-1.5 text-slate-600">{r._acb ? `${r._acb.tipo} ${r._acb.ancho} · ${r._acb._colorLbl} ${r._acb.grosor}` : (r.esMueble ? <span className="text-red-500 font-bold">sin equivalencia</span> : '—')}</td>
                        <td className="px-2 py-1.5 text-center">{r.puertas}/{r.cajones}/{r.gavetas}</td>
                        <td className="px-2 py-1.5 text-right text-slate-400">{r._precioAcb ? eur(r._precioAcb) : '—'}</td>
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
                  <div className="flex justify-between"><span className="text-slate-500">Cascos ACB (antracita 19, −{p.desc1}% −{p.desc2}%)</span><b>{eur(calc.totCasco)}</b></div>
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
              <div className="rounded-lg bg-amber-50 border border-amber-200 px-3 py-2 text-xs text-amber-800">
                <b>Puertas a cotizar aparte:</b> {calc.totPuertas} puerta(s) — no incluidas en el coste (el casco ACB va desnudo).
                {calc.sinMatch > 0 && <span className="block mt-1 text-red-600"><b>{calc.sinMatch}</b> mueble(s) sin equivalencia ACB automática — revísalos.</span>}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
