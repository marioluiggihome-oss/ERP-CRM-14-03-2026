/*
 * © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * RelacionReview — Panel de revisión de la relación de muebles importada del PDF
 * (o añadida a mano). Listado editable + BUSCADOR (texto o desplegable del catálogo
 * MV) para añadir los que falten + desglose de COSTE/MARGEN oculto tras un candado
 * 🔒 que solo se abre con Shift+clic (como en el resto del ERP).
 *
 * Props:
 *   muebles     : array inicial [{qty,cod,familia,tipo,ancho,alto,fondo,pvp,encontrado,raw}]
 *   onConfirm   : (muebles) => void
 *   onClose     : () => void
 *   apiUrl, authHeaders
 */
import React, { useState, useEffect, useMemo } from 'react';
import { X, Plus, Trash2, Search, Check, Loader, AlertTriangle, FileUp, Lock, Unlock } from 'lucide-react';
import { usePulsacionLarga, AYUDA_CANDADO } from '../utils/pulsacionLarga';
import { despiece, MV_COSTES_DEFAULT } from './RentabilidadMV';

const eur = (n) => (n == null ? '—' : `${Number(n).toFixed(2)} €`);

// Texto comparable: sin tildes y en minúsculas, para que "sobreencimera" case
// escribiéndolo con tilde o sin ella.
const norm = (s) => (s || '').toString()
  .normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();

// El número del código MV es el ancho en cm (B60D/I -> 60). Pero NO en todas las
// familias: los elementos lineales (COR, ZOC, MOSE…) y los techos (TEC100…TEC360)
// no lo llevan, y en EMC1M/E ese "1" significa Medio/Entero, no un ancho. Sacar
// "el primer número" pintaría «1 cm» en una encimera.
// Regla: ancho solo cuando el código lo lleva de verdad; si no, vacío.
const TIPOS_SIN_ANCHO = new Set(['ent_med', 'h355060']);
const PAT_ANCHO = /^[A-Z]+(\d{2,3})(?:D\/I|D|I)?$/;
const anchoDeCod = (cod, type) => {
  if (TIPOS_SIN_ANCHO.has(type)) return null;
  const m = PAT_ANCHO.exec(cod || '');
  return m ? Number(m[1]) : null;
};

// Precio orientativo de la lista. Solo si NO es ambiguo: con varias alturas se
// marca «desde», y los lineales (entero/medio) no llevan precio aquí — ese lo
// fija el servidor al añadirlos, que es quien sabe cuál toca.
const pvpDeItem = (val, pv) => {
  if (typeof val === 'number') return { eur: Math.round(val * pv * 100) / 100, desde: false };
  if (Array.isArray(val)) {
    const ns = val.filter(n => typeof n === 'number');
    if (!ns.length) return null;
    return { eur: Math.round(Math.min(...ns) * pv * 100) / 100, desde: true };
  }
  return null;
};

// Coste total de un mueble = suma de componentes del despiece × cantidad unitaria.
const costeDe = (m, p) => {
  const d = despiece({ cod: m.cod, altura: m.alto ? String(m.alto) : '', familia: m.familia }, p);
  return (d.casco || 0) + (d.puerta || 0) + (d.bisagras || 0) + (d.patas || 0) + (d.colg || 0)
    + (d.caj || 0) + (d.gav || 0) + (d.soportes || 0) + (d.mo || 0);
};

export default function RelacionReview({ muebles: inicial, noLeidas, onConfirm, onClose, apiUrl, authHeaders }) {
  const [muebles, setMuebles] = useState(() => (inicial || []).map((m, i) => ({ ...m, _k: `${m.cod || 'x'}-${i}-${m.raw || ''}` })));
  const [busca, setBusca] = useState('');
  const [buscando, setBuscando] = useState(false);
  const [aviso, setAviso] = useState('');
  const [verCoste, setVerCoste] = useState(false); // candado: coste/margen tras un gesto deliberado
  const [pistaCandado, setPistaCandado] = useState(''); // cómo se abre, para quien no lo sepa

  // Costes de componentes (los mismos que Rentabilidad MV, vía localStorage).
  const p = useMemo(() => {
    try { const s = JSON.parse(localStorage.getItem('mv_costes') || 'null'); return s ? { ...MV_COSTES_DEFAULT, ...s } : MV_COSTES_DEFAULT; }
    catch { return MV_COSTES_DEFAULT; }
  }, []);

  // Catálogo MV para el desplegable (familia -> códigos) y valor de punto.
  const [familias, setFamilias] = useState(null);
  const [pv, setPv] = useState(3.33);
  const [selFam, setSelFam] = useState('');
  const [selCod, setSelCod] = useState('');
  const [selQty, setSelQty] = useState(1);
  useEffect(() => {
    fetch(`${apiUrl}/api/cascos/mv/tarifa?tariff=T1`, { headers: authHeaders() })
      .then(r => r.json()).then(d => { if (d.success) { setFamilias(d.familias); setPv(d.pointValue || 3.33); } }).catch(() => {});
  }, [apiUrl, authHeaders]);
  const codigosFam = useMemo(() => {
    if (!familias || !selFam) return [];
    const it = familias[selFam]?.items;
    return it && typeof it === 'object' ? Object.keys(it) : [];
  }, [familias, selFam]);

  // ─── Buscador local sobre el catálogo YA cargado ────────────────────────
  // Las 358 referencias de la tarifa llegan con la primera petición y estaban
  // ahí sin usar: solo alimentaban dos desplegables encadenados (53 familias y
  // luego hasta 12 códigos). Para añadir un mueble había que saberse el código
  // de memoria o navegar los dos desplegables. Ahora se filtran en el sitio,
  // sin pedirle nada al servidor, y se puede buscar por PALABRA ("fregadero")
  // igual que en el buscador de cascos de detrás.
  const catalogo = useMemo(() => {
    if (!familias) return [];
    const out = [];
    for (const [fam, info] of Object.entries(familias)) {
      const items = info?.items;
      if (!items || typeof items !== 'object') continue;
      for (const [cod, val] of Object.entries(items)) {
        const desc = (val && typeof val === 'object' && !Array.isArray(val)) ? val.desc : null;
        const etiqueta = fam.replace(/_/g, ' ');
        out.push({
          cod, familia: fam, etiqueta, desc,
          ancho: anchoDeCod(cod, info.type),
          precio: pvpDeItem(val, pv),
          busca: norm(`${cod} ${etiqueta} ${desc || ''}`),
        });
      }
    }
    return out;
  }, [familias, pv]);

  const [sel, setSel] = useState(0);
  const [foco, setFoco] = useState(false);
  const sugerencias = useMemo(() => {
    const q = norm(busca).trim();
    if (!q || !catalogo.length) return [];
    // Si ya viene escrito como expresión ("2 b60i (altura 80)") no se sugiere:
    // eso lo interpreta el servidor, que entiende cantidades, manos y alturas.
    if (/^\s*\d+\s*\S/.test(busca) || busca.includes('(')) return [];
    const term = q.split(/\s+/).filter(Boolean);
    const hits = catalogo.filter(c => term.every(t => c.busca.includes(t)));
    hits.sort((a, b) => {
      const ap = a.cod.toLowerCase().startsWith(q) ? 0 : 1;
      const bp = b.cod.toLowerCase().startsWith(q) ? 0 : 1;
      return ap - bp || a.cod.localeCompare(b.cod);
    });
    return hits.slice(0, 40);
  }, [busca, catalogo]);
  useEffect(() => { setSel(0); }, [busca]);

  // Alturas seleccionables según el TIPO de familia (deja las otras medidas posibles).
  // El primero de cada lista es el que sale por defecto. En los altos manda el
  // 90: es la altura de la casa, y el 70 es la excepción — no al revés.
  const OPCIONES_ALTURA = { h7090: [90, 70], h127147: [127, 147], h200220: [200, 220] };
  const alturasDe = (m) => {
    const t = familias?.[m.familia]?.type;
    return OPCIONES_ALTURA[t] || null; // null = altura fija (p. ej. bajos a 80)
  };
  // Recalcula los PUNTOS/PVP de un código para una altura dada (según su tipo de familia).
  const puntosLocal = (m, alto) => {
    const info = familias?.[m.familia];
    const e = info?.items?.[m.cod];
    if (e == null) return m.pvp;
    if (Array.isArray(e)) {
      const t = info.type;
      let i = 0;
      if (t === 'h7090') i = alto >= 85 ? 1 : 0;
      else if (t === 'h127147') i = alto > 137 ? 1 : 0;
      else if (t === 'h200220') i = alto > 210 ? 1 : 0;
      return Math.round((e[i] || e[0]) * pv * 100) / 100;
    }
    return typeof e === 'number' ? Math.round(e * pv * 100) / 100 : m.pvp;
  };

  const setQty = (k, v) => setMuebles(prev => prev.map(m => m._k === k ? { ...m, qty: Math.max(1, Number(v) || 1) } : m));
  const setAlto = (k, v) => setMuebles(prev => prev.map(m => {
    if (m._k !== k) return m;
    const alto = Number(v) || null;
    return { ...m, alto, pvp: puntosLocal(m, alto) };
  }));
  const quitar = (k) => setMuebles(prev => prev.filter(m => m._k !== k));

  // LA ALTURA POR DEFECTO SE APLICA AL DATO, NO SOLO AL DESPLEGABLE.
  //
  // Antes el desplegable enseñaba la primera altura de la lista, pero el mueble
  // se quedaba SIN altura por dentro y con el precio que hubiera venido. O sea
  // que se veía «90» y se cobraba otra cosa, sin que nada avisara. Aquí se le
  // pone la altura de la casa de verdad y se recalcula su PVP con ella.
  //
  // No es inventarse una medida: es el estándar de la casa, decidido a mano, y
  // la fila queda marcada para que se vea que esa altura NO venía en la
  // relación del cliente.
  useEffect(() => {
    if (!familias) return;
    setMuebles(prev => {
      let cambia = false;
      const sig = prev.map(m => {
        if (m.alto) return m;
        const opciones = OPCIONES_ALTURA[familias?.[m.familia]?.type];
        if (!opciones) return m;           // altura fija: no hay nada que elegir
        cambia = true;
        return { ...m, alto: opciones[0], _altoDeLaCasa: true, pvp: puntosLocal(m, opciones[0]) };
      });
      return cambia ? sig : prev;
    });
    // Depende solo de que llegue el catálogo y de que haya filas nuevas: la
    // función de dentro se protege sola (si ya tiene altura, no toca nada).
  }, [familias, muebles.length]);   // eslint-disable-line

  const filas = muebles.map(m => {
    const coste = m.encontrado ? costeDe(m, p) : 0;
    const pvp = Number(m.pvp) || 0;
    const margen = pvp - coste;
    const margenPct = pvp > 0 ? (margen / pvp) * 100 : 0;
    return { ...m, coste, margen, margenPct };
  });
  const totalUds = muebles.reduce((s, m) => s + (Number(m.qty) || 1), 0);
  const totalPvp = filas.reduce((s, m) => s + m.pvp * (Number(m.qty) || 1), 0);
  const totalCoste = filas.reduce((s, m) => s + m.coste * (Number(m.qty) || 1), 0);
  const totalMargen = totalPvp - totalCoste;
  const totalMargenPct = totalPvp > 0 ? (totalMargen / totalPvp) * 100 : 0;

  // Une los nuevos con los que ya hay: mismo código y misma altura = suma de
  // unidades. Distinta altura son muebles distintos y van en filas separadas.
  const fundir = (prev, nuevos) => {
    const out = [...prev];
    for (const n of nuevos) {
      const i = out.findIndex(m => m.cod && n.cod && m.cod === n.cod
        && (m.alto ?? null) === (n.alto ?? null));
      if (i >= 0) out[i] = { ...out[i], qty: (Number(out[i].qty) || 1) + (Number(n.qty) || 1) };
      else out.push(n);
    }
    return out;
  };

  // Añadir por TEXTO (buscador libre) o desde el desplegable.
  const añadirTexto = async (texto) => {
    const t = (texto || '').trim();
    if (!t) return;
    setBuscando(true); setAviso('');
    try {
      const r = await fetch(`${apiUrl}/api/cascos/mv/detectar-relacion`, {
        method: 'POST', headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ texto: t }),
      });
      let d = {}; try { d = await r.json(); } catch { d = {}; }
      if (!r.ok || !d.success) { setAviso(d.detail || 'No se reconoció el mueble. Escríbelo como "1 b60i (altura 80)".'); return; }
      const nuevos = (d.muebles || []).map((m, i) => ({ ...m, _k: `add-${Date.now()}-${i}` }));
      // Si el mueble ya está (mismo código Y misma altura), se suman unidades en
      // vez de abrir otra fila. Las unidades multiplican coste, herraje y pedido
      // al proveedor: dos filas de B60D con 1 ud cada una se leen mal de un
      // vistazo y es fácil corregir solo una.
      setMuebles(prev => fundir(prev, nuevos));
      setBusca('');
    } catch (e) {
      setAviso(`Error al buscar (${e?.message || 'red'}).`);
    } finally { setBuscando(false); }
  };
  const añadirDelSelector = () => {
    if (!selCod) return;
    añadirTexto(`${Math.max(1, Number(selQty) || 1)} ${selCod}`);
  };
  // Elegir una sugerencia añade UNA unidad. Volver a elegir la misma suma otra,
  // porque los duplicados se funden: pulsar dos veces es la forma rápida de
  // poner 2, sin soltar el teclado.
  const añadirSugerencia = (c) => { if (c) añadirTexto(`1 ${c.cod}`); };
  const teclaBuscador = (e) => {
    if (!sugerencias.length) { if (e.key === 'Enter') añadirTexto(busca); return; }
    if (e.key === 'ArrowDown') { e.preventDefault(); setSel(s => (s + 1) % sugerencias.length); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setSel(s => (s - 1 + sugerencias.length) % sugerencias.length); }
    else if (e.key === 'Enter') { e.preventDefault(); añadirSugerencia(sugerencias[sel]); }
    else if (e.key === 'Escape') { e.preventDefault(); setBusca(''); }
  };

  const confirmar = () => {
    if (!muebles.length) return;
    onConfirm(muebles.map(m => ({ tipo: m.tipo, ancho: m.ancho, alto: m.alto, fondo: m.fondo, qty: m.qty || 1, cod: m.cod })));
  };

  const noEncontrados = muebles.filter(m => !m.encontrado).length;

  // El candado del coste/margen. Se abre manteniendo pulsado o con Shift+clic:
  // en tablet no hay tecla Shift, así que con Shift solo el margen era
  // sencillamente inalcanzable — el botón se tocaba y no pasaba nada.
  const candadoLargo = usePulsacionLarga(() => { setPistaCandado(''); setVerCoste(v => !v); });
  const candadoClick = (e) => {
    if (candadoLargo.consumir()) return;   // ya lo ha abierto la pulsación
    if (e.shiftKey || verCoste) { setPistaCandado(''); setVerCoste(v => !v); return; }
    // Un toque suelto no lo abre — pero sí dice CÓMO se abre. Un botón que no
    // hace nada al tocarlo parece roto.
    setPistaCandado(AYUDA_CANDADO + ' para ver coste y margen.');
  };
  const oculto = '•••';

  return (
    // A TODA LA PANTALLA. Con `max-w-4xl` la lista de muebles se quedaba en una
    // columna estrecha en medio, con la mitad del monitor en gris al lado y la
    // tabla haciendo scroll para nada. Aquí se revisa una relación entera antes
    // de volcarla: cuanto más se ve de golpe, menos se cuela.
    <div className="fixed inset-0 z-[60] bg-black/50 flex items-stretch justify-center p-2 sm:p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-2xl w-full h-full flex flex-col overflow-hidden" onClick={e => e.stopPropagation()}>
        {/* Cabecera */}
        <div className="px-5 py-3.5 bg-gradient-to-r from-indigo-600 to-violet-600 text-white flex items-center justify-between">
          <h3 className="font-black flex items-center gap-2"><FileUp size={18} /> Revisar relación de muebles</h3>
          <button onClick={onClose} className="p-1.5 hover:bg-white/20 rounded-lg"><X size={18} /></button>
        </div>

        {/* Añadir: buscador libre + desplegable del catálogo */}
        <div className="px-5 pt-4 space-y-2">
          <div>
            <label className="text-[11px] font-bold text-slate-500 uppercase">Añadir escribiendo</label>
            <div className="flex gap-2 mt-1">
              <div className="relative flex-1">
                <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input value={busca} onChange={e => setBusca(e.target.value)}
                  onKeyDown={teclaBuscador}
                  onFocus={() => setFoco(true)}
                  onBlur={() => setTimeout(() => setFoco(false), 120)}
                  placeholder='Código o palabra: "b60", "fregadero", "1 b45d (altura 80)"'
                  className="w-full pl-9 pr-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-400 outline-none" />
                {/* Sugerencias del catálogo, filtradas aquí mismo. El ancho solo
                    se pinta cuando el código lo lleva de verdad: en cornisas,
                    zócalos, encimeras y techos se deja vacío antes que poner
                    una cota que no es. */}
                {foco && sugerencias.length > 0 && (
                  <ul className="absolute z-10 left-0 right-0 top-full mt-1 max-h-64 overflow-y-auto bg-white border border-slate-200 rounded-lg shadow-xl">
                    {sugerencias.map((c, i) => (
                      <li key={c.familia + c.cod}>
                        <button type="button"
                          onMouseEnter={() => setSel(i)}
                          onClick={() => añadirSugerencia(c)}
                          className={`w-full text-left px-3 py-1.5 flex items-baseline gap-2 ${i === sel ? 'bg-indigo-50' : 'hover:bg-slate-50'}`}>
                          <span className="font-black text-indigo-900 text-xs w-24 shrink-0">{c.cod}</span>
                          <span className="text-[11px] text-slate-500 truncate flex-1">
                            {c.desc || c.etiqueta.toLowerCase()}
                          </span>
                          {c.ancho != null && (
                            <span className="text-[11px] text-slate-400 shrink-0">{c.ancho} cm</span>
                          )}
                          {c.precio && (
                            <span className="text-[11px] font-bold text-slate-600 shrink-0 w-20 text-right">
                              {c.precio.desde ? 'desde ' : ''}{c.precio.eur.toFixed(2)} €
                            </span>
                          )}
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
              <button onClick={() => añadirTexto(busca)} disabled={buscando || !busca.trim()}
                className="flex items-center gap-1.5 px-3.5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-bold text-sm disabled:opacity-50">
                {buscando ? <Loader size={15} className="animate-spin" /> : <Plus size={15} />} Añadir
              </button>
            </div>
          </div>
          <div>
            <label className="text-[11px] font-bold text-slate-500 uppercase">…o eligiendo del catálogo MV</label>
            <div className="flex gap-2 mt-1 flex-wrap">
              <select value={selFam} onChange={e => { setSelFam(e.target.value); setSelCod(''); }}
                className="flex-1 min-w-[140px] px-2 py-2 border border-slate-300 rounded-lg text-sm bg-white">
                <option value="">Familia…</option>
                {familias && Object.keys(familias).filter(f => (familias[f]?.items && Object.keys(familias[f].items).length)).map(f => (
                  <option key={f} value={f}>{f.replace(/_/g, ' ')}</option>
                ))}
              </select>
              <select value={selCod} onChange={e => setSelCod(e.target.value)} disabled={!codigosFam.length}
                className="flex-1 min-w-[120px] px-2 py-2 border border-slate-300 rounded-lg text-sm bg-white disabled:bg-slate-100">
                <option value="">Código…</option>
                {codigosFam.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
              <input type="number" min="1" value={selQty} onChange={e => setSelQty(e.target.value)}
                className="w-16 text-center border border-slate-300 rounded-lg px-1 py-2 text-sm" title="Cantidad" />
              <button onClick={añadirDelSelector} disabled={!selCod || buscando}
                className="flex items-center gap-1.5 px-3.5 py-2 bg-slate-700 hover:bg-slate-800 text-white rounded-lg font-bold text-sm disabled:opacity-50">
                <Plus size={15} /> Añadir
              </button>
            </div>
          </div>
          {aviso && <p className="text-xs text-amber-700 flex items-center gap-1"><AlertTriangle size={13} /> {aviso}</p>}
        </div>

        {/* Listado */}
        <div className="px-5 py-3 overflow-y-auto flex-1">
          {pistaCandado && (
            <p className="text-[11px] font-bold text-emerald-800 bg-emerald-50 border border-emerald-200 rounded-lg px-3 py-1.5 mb-2 flex items-center gap-1.5">
              <Lock size={12} /> {pistaCandado}
            </p>
          )}
          {noEncontrados > 0 && (
            <p className="text-[11px] text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-1.5 mb-2">
              {noEncontrados} mueble(s) sin código de tarifa (van igualmente, precio a ajustar).
            </p>
          )}
          {/* Lo que se escribió en el PDF y el lector NO ha sabido interpretar.
              Antes se descartaba sin decir nada: el total salía corto y parecía
              correcto. Se enseña tal cual, con el recuadro del que viene. */}
          {(noLeidas || []).length > 0 && (
            <div className="text-[11px] text-red-700 bg-red-50 border border-red-200 rounded-lg px-3 py-2 mb-2">
              <b>{noLeidas.length} anotación(es) del PDF sin leer</b> — NO están en los totales:
              {noLeidas.map((n, i) => (
                <span key={i} className="block mt-0.5">
                  · {n.recuadro ? <b>{n.recuadro}: </b> : null}«{n.texto}» — {n.motivo}
                  {n.sugerencia ? <> · ¿querías decir <b>{n.sugerencia}</b>?</> : null}
                </span>
              ))}
              <span className="block mt-1 text-red-600">
                Añádelas a mano con el buscador de aquí arriba.
              </span>
            </div>
          )}
          <table className="w-full text-sm">
            <thead>
              <tr className="text-[10px] uppercase text-slate-400 border-b border-slate-200">
                <th className="text-left py-1.5">Código</th>
                <th className="text-left">Tipo</th>
                <th className="text-right">Ancho</th>
                <th className="text-center">Alto</th>
                <th className="text-center">Uds</th>
                <th className="text-right">PVP MV</th>
                <th className="text-right whitespace-nowrap">
                  <button onClick={candadoClick} {...candadoLargo.props}
                    title={`Coste y margen (solo master) — ${AYUDA_CANDADO}`}
                    className="inline-flex items-center gap-1 text-slate-400 hover:text-emerald-600">
                    {verCoste ? <Unlock size={12} /> : <Lock size={12} />} Coste
                  </button>
                </th>
                <th className="text-right">
                  <button onClick={candadoClick} {...candadoLargo.props}
                    className="text-slate-400 hover:text-emerald-600" title={AYUDA_CANDADO}>Margen</button>
                </th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {filas.map(m => (
                <tr key={m._k} className="border-b border-slate-100">
                  <td className="py-1.5 font-black text-indigo-900">
                    {m.cod || <span className="text-amber-600">{(m.raw || '¿?').toUpperCase()}</span>}
                  </td>
                  <td className="text-slate-500 text-xs">{m.tipo}</td>
                  <td className="text-right text-slate-600">{m.ancho} cm</td>
                  <td className="text-center">
                    {alturasDe(m) ? (
                      <select value={m.alto || alturasDe(m)[0]} onChange={e => setAlto(m._k, e.target.value)}
                        className="border border-slate-300 rounded px-1 py-0.5 text-sm bg-white">
                        {alturasDe(m).map(a => <option key={a} value={a}>{a}</option>)}
                      </select>
                    ) : (
                      <span className="text-slate-500 text-xs">{m.alto ? `${m.alto}` : '—'}</span>
                    )}
                  </td>
                  <td className="text-center">
                    <input type="number" min="1" value={m.qty || 1} onChange={e => setQty(m._k, e.target.value)}
                      className="w-14 text-center border border-slate-300 rounded px-1 py-0.5 text-sm" />
                  </td>
                  <td className="text-right text-slate-700 font-semibold">{eur(m.pvp)}</td>
                  <td className="text-right text-slate-600">{verCoste ? (m.encontrado ? eur(m.coste) : '—') : oculto}</td>
                  <td className={`text-right font-bold ${verCoste ? (m.margenPct >= 40 ? 'text-emerald-600' : m.margenPct >= 25 ? 'text-amber-600' : 'text-red-600') : 'text-slate-400'}`}>
                    {verCoste ? (m.encontrado ? `${m.margenPct.toFixed(0)}%` : '—') : oculto}
                  </td>
                  <td className="text-right">
                    <button onClick={() => quitar(m._k)} className="p-1 text-slate-400 hover:text-red-600"><Trash2 size={15} /></button>
                  </td>
                </tr>
              ))}
              {!filas.length && (
                <tr><td colSpan={9} className="text-center text-slate-400 py-6 text-sm">No hay muebles. Añade alguno arriba.</td></tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pie */}
        <div className="px-5 py-3.5 border-t border-slate-200 flex items-center justify-between gap-3 bg-slate-50 flex-wrap">
          <div className="text-sm text-slate-600">
            <span className="font-black text-slate-800">{totalUds}</span> uds ·
            <span className="font-black text-slate-800"> {eur(totalPvp)}</span> <span className="text-xs text-slate-400">PVP MV</span>
            {verCoste && (
              <span className="ml-2 text-xs">
                · coste <span className="font-bold text-slate-700">{eur(totalCoste)}</span>
                · margen <span className={`font-black ${totalMargenPct >= 40 ? 'text-emerald-600' : totalMargenPct >= 25 ? 'text-amber-600' : 'text-red-600'}`}>{totalMargenPct.toFixed(0)}%</span>
              </span>
            )}
          </div>
          <div className="flex gap-2">
            <button onClick={onClose} className="px-4 py-2 text-slate-600 hover:bg-slate-200 rounded-lg font-bold text-sm">Cancelar</button>
            <button onClick={confirmar} disabled={!muebles.length}
              className="flex items-center gap-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-black text-sm disabled:opacity-50">
              <Check size={16} /> Volcar {totalUds} al presupuesto
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
