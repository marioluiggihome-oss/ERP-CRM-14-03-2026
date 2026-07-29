import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Upload, Loader, FileText, Calculator } from 'lucide-react';
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
// VALOR DE PUNTO de Cocina Desmontada: el precio del presupuestador = precio base
// del catálogo × 2,0. El coste = ese precio × -50% × -28% (el -50% deshace el x2).
const _PUNTO = 2.0;
// Medidas del mueble Alvic: ancho (del prefijo del código, cm), alto (Largo) y
// fondo (Grueso), en mm.
const _medidas_mm = (it) => {
  const m = /^(\d{2,3})/.exec(it.cod || '');
  const ancho = m ? parseInt(m[1], 10) * 10 : (Number(it.ancho) || 600);
  const alto = Number(it.largo) || 0;    // en la proforma, "Largo" es la altura del mueble
  const fondo = Number(it.grueso) || 0;  // "Grueso" es el fondo
  return { ancho, alto, fondo };
};
// Empareja con el casco ACB del mismo tipo, minimizando la distancia en ancho
// (peso alto), alto y fondo. Antracita (grafito 19) preferente.
const _match_acb = (it) => {
  const tipoAcb = _TIPO_ACB(it.descripcion, it.tipo);
  if (!tipoAcb) return null;
  const { ancho, alto, fondo } = _medidas_mm(it);
  let pool = CASCOS.filter(c => c.tipo === tipoAcb && c.grosor === 19 && c.precios && c.precios.grafito != null);
  if (!pool.length) pool = CASCOS.filter(c => c.tipo === tipoAcb && _precio_color(c) != null);
  if (!pool.length) return null;
  let best = pool[0], bd = Infinity;
  for (const c of pool) {
    const d = Math.abs((c.ancho || 0) - ancho) * 3
      + (alto ? Math.abs((c.alto || 0) - alto) : 0)
      + (fondo ? Math.abs((c.fondo || 0) - fondo) : 0);
    if (d < bd) { bd = d; best = c; }
  }
  const pc = _precio_color(best);
  const base = pc ? pc.precio : 0;
  return { ...best, _base: base, _precio: base * _PUNTO, _color: pc ? pc.color : '', _colorLbl: pc ? (_COLOR_LBL[pc.color] || pc.color) : '' };
};

// Importar PRESUPUESTO DE VENTA (solo MASTER). Sube el PDF con la relación de
// muebles, la IA detecta cada casco y su herraje (bisagras, patas, colgadores,
// guías). Tú metes la MANO DE OBRA (coste de producción) y el MARGEN en € que
// quieres ganar. Si el margen es 0, el resultado es tu coste.
const eur = (n) => (Number(n) || 0).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' €';

// Ante un fallo de red, distingue "el servidor no responde" de "falla solo esta
// ruta". Sin esto, "Failed to fetch" obliga a adivinar dónde está el problema.
const _diagnostico = async (e) => {
  const motivo = e?.message || 'error de red';
  if (!API_URL) {
    return 'La aplicación no tiene configurada la dirección del servidor (REACT_APP_BACKEND_URL). Avisa al administrador.';
  }
  if (window.location.protocol === 'https:' && String(API_URL).startsWith('http:')) {
    return `El navegador bloquea la llamada: la web va por HTTPS y el servidor está configurado en HTTP (${API_URL}). Avisa al administrador.`;
  }
  // Se prueban tres cosas y se informa del resultado de cada una, porque cada
  // combinación apunta a una causa distinta y "Failed to fetch" no distingue.
  const probar = async (url, opts) => {
    try {
      const r = await fetch(url, opts);
      let d = {}; try { d = await r.json(); } catch { d = {}; }
      return { estado: r.status, detail: d.detail || '' };
    } catch (err) { return { estado: 0, detail: err?.message || 'error de red' }; }
  };

  const ping = await probar(`${API_URL}/api/`, { method: 'GET' });
  if (ping.estado === 0) {
    return `El servidor no responde (${motivo}). Está caído o terminando de desplegarse: espera un minuto y reinténtalo. Si sigue igual, revisa el despliegue del backend en Railway.`;
  }

  // ¿Existe ya la ruta del análisis en segundo plano? Frontend y backend son
  // servicios distintos en Railway y no se despliegan a la vez.
  const sondeo = await probar(`${API_URL}/api/cascos/proforma/job/_ping`, { headers: getAuthHeaders() });
  if (sondeo.estado === 404 && /not found/i.test(sondeo.detail)) {
    return 'El backend todavía sirve la versión anterior: por eso la petición se queda colgada hasta que se corta. Espera a que termine de desplegarse el backend en Railway y vuelve a probar.';
  }
  if (sondeo.estado === 0) {
    return `Falla cualquier petición con cabecera de sesión: el servidor contesta a una consulta simple (${ping.estado}) pero rechaza las autenticadas (${sondeo.detail}). Suele ser un problema de CORS o de sesión caducada: vuelve a entrar en el ERP y reinténtalo.`;
  }
  // El servidor está vivo y acepta peticiones autenticadas: el que revienta es
  // el envío del PDF. Lo más probable es que el proceso se caiga al recibirlo.
  return `El envío del PDF corta la conexión (${motivo}), aunque el servidor responde bien a lo demás (comprobación ${ping.estado}, sondeo ${sondeo.estado}). Avisa: hay que mirar los logs del backend en Railway justo al reproducirlo.`;
};

export default function ProformaImporter({ esMaster }) {
  const [cargando, setCargando] = useState(false);
  const [progreso, setProgreso] = useState('');
  const [error, setError] = useState(null);
  const [items, setItems] = useState([]);
  const fileRef = useRef(null);

  // Costes reales de herraje = Set + Fondo (columna de coste de la tarifa).
  const HERRAJE = {
    blum: { cajon: 41.34, gaveta: 54.37 },   // Set 31,59/44,62 + Fondo 9,75
    gtv: { cajon: 24.65, gaveta: 29.41 },     // Set AXIS 15,07/19,83 + Fondo 9,58
  };
  const BISAGRA = { blum: 3.07, emuca: 1.01 }; // BLUM Blumotion 2,61 + base 0,46 · EMUCA 1,01
  const [marcaCaj, setMarcaCaj] = useState('blum');  // marca de cajones/gavetas
  const [marcaBis, setMarcaBis] = useState('blum');  // marca de bisagras
  const P_DEFAULT = { desc1: 50, desc2: 28, bisagra: BISAGRA.blum, pata: 1.20, colgador: 3.50, cajon: HERRAJE.blum.cajon, gaveta: HERRAJE.blum.gaveta, manoObra: 0, margen: 0 };
  const [p, setP] = useState(() => {
    try { const s = JSON.parse(localStorage.getItem('alvic_costes') || 'null'); return s ? { ...P_DEFAULT, ...s } : P_DEFAULT; } catch { return P_DEFAULT; }
  });
  useEffect(() => { try { localStorage.setItem('alvic_costes', JSON.stringify(p)); } catch { /* noop */ } }, [p]);
  const setNum = (k) => (e) => setP(prev => ({ ...prev, [k]: e.target.value === '' ? '' : Number(e.target.value) }));
  const cambiarMarcaCaj = (m) => { setMarcaCaj(m); setP(prev => ({ ...prev, cajon: HERRAJE[m].cajon, gaveta: HERRAJE[m].gaveta })); };
  const cambiarMarcaBis = (m) => { setMarcaBis(m); setP(prev => ({ ...prev, bisagra: BISAGRA[m] })); };

  const importar = async (file) => {
    if (!file) return;
    setCargando(true); setError(null); setItems([]); setProgreso('');
    try {
      const b64 = await new Promise((res, rej) => {
        const fr = new FileReader(); fr.onload = () => res(fr.result); fr.onerror = rej; fr.readAsDataURL(file);
      });
      // El arranque responde en el acto: o devuelve los muebles (PDF con capa de
      // texto) o un jobId que se va sondeando. Así ninguna petición se queda
      // abierta minutos esperando a la IA, que es lo que cortaba la conexión.
      const r = await fetch(`${API_URL}/api/cascos/proforma`, {
        method: 'POST', headers: getAuthHeaders(), body: JSON.stringify({ pdfBase64: b64 }),
      });
      let d = {}; try { d = await r.json(); } catch { d = {}; }
      if (!r.ok) { setError(d.detail || d.error || `El servidor devolvió un error (${r.status}).`); return; }

      if (d.estado === 'procesando' && d.jobId) {
        setProgreso('Leyendo el PDF…');
        const inicio = Date.now();
        // Sondeo cada 3 s, hasta 10 min. Cada petición es instantánea.
        while (Date.now() - inicio < 600000) {
          await new Promise(res => setTimeout(res, 3000));
          const q = await fetch(`${API_URL}/api/cascos/proforma/job/${d.jobId}`, { headers: getAuthHeaders() });
          let j = {}; try { j = await q.json(); } catch { j = {}; }
          if (!q.ok) { setError(j.detail || `El servidor devolvió un error (${q.status}).`); return; }
          if (j.total) setProgreso(`Analizando página ${Math.min(j.hechas + 1, j.total)} de ${j.total}…`);
          if (j.estado === 'listo') { setItems(j.items || []); return; }
          if (j.estado === 'error') { setError(j.detail || 'No se pudieron detectar los muebles.'); return; }
        }
        setError('El análisis está tardando demasiado. Prueba a subir solo las páginas con la tabla de partidas.');
        return;
      }

      if (d.success) setItems(d.items || []);
      else setError(d.detail || d.error || 'No se pudieron detectar los muebles.');
    } catch (e) {
      // "Failed to fetch" no dice NADA por sí solo: puede ser el servidor caído,
      // un despliegue a medias o un problema solo de esta ruta. Se comprueba el
      // servidor con una petición mínima para dar un diagnóstico de verdad.
      setError(await _diagnostico(e));
    }
    finally { setCargando(false); setProgreso(''); }
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
      </div>

      {(
        <div className="p-4 space-y-4">
          <div className="flex items-center gap-3 flex-wrap">
            <button onClick={() => fileRef.current?.click()} disabled={cargando}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl font-black text-sm text-white bg-amber-600 hover:bg-amber-700 disabled:opacity-50">
              {cargando ? <Loader size={16} className="animate-spin" /> : <Upload size={16} />}
              {cargando ? (progreso || 'Detectando muebles…') : 'Importar presupuesto de venta (PDF)'}
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
                <div className="flex items-center gap-3 mb-2 flex-wrap">
                  <span className="text-[11px] font-black uppercase tracking-wide text-slate-600">Herraje (coste real = set + fondo)</span>
                  <label className="text-[11px] font-bold text-slate-500 flex items-center gap-1">Cajones/gavetas:
                    <select value={marcaCaj} onChange={e => cambiarMarcaCaj(e.target.value)} className="border border-slate-200 rounded px-1.5 py-0.5 text-xs font-bold">
                      <option value="blum">BLUM</option><option value="gtv">GTV</option>
                    </select>
                  </label>
                  <label className="text-[11px] font-bold text-slate-500 flex items-center gap-1">Bisagras:
                    <select value={marcaBis} onChange={e => cambiarMarcaBis(e.target.value)} className="border border-slate-200 rounded px-1.5 py-0.5 text-xs font-bold">
                      <option value="blum">BLUM</option><option value="emuca">EMUCA</option>
                    </select>
                  </label>
                </div>
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
