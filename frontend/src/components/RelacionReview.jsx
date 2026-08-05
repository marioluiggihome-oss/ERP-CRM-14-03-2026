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
import { despiece, MV_COSTES_DEFAULT } from './RentabilidadMV';

const eur = (n) => (n == null ? '—' : `${Number(n).toFixed(2)} €`);

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
  const [verCoste, setVerCoste] = useState(false); // candado: coste/margen solo con Shift+clic

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

  // Alturas seleccionables según el TIPO de familia (deja las otras medidas posibles).
  const OPCIONES_ALTURA = { h7090: [70, 90], h127147: [127, 147], h200220: [200, 220] };
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
      setMuebles(prev => [...prev, ...nuevos]);
      setBusca('');
    } catch (e) {
      setAviso(`Error al buscar (${e?.message || 'red'}).`);
    } finally { setBuscando(false); }
  };
  const añadirDelSelector = () => {
    if (!selCod) return;
    añadirTexto(`${Math.max(1, Number(selQty) || 1)} ${selCod}`);
  };

  const confirmar = () => {
    if (!muebles.length) return;
    onConfirm(muebles.map(m => ({ tipo: m.tipo, ancho: m.ancho, alto: m.alto, fondo: m.fondo, qty: m.qty || 1, cod: m.cod })));
  };

  const noEncontrados = muebles.filter(m => !m.encontrado).length;
  const candadoClick = (e) => { if (e.shiftKey) setVerCoste(v => !v); };
  const oculto = '•••';

  return (
    <div className="fixed inset-0 z-[60] bg-black/50 flex items-center justify-center p-3" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl max-h-[92vh] flex flex-col overflow-hidden" onClick={e => e.stopPropagation()}>
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
                  onKeyDown={e => { if (e.key === 'Enter') añadirTexto(busca); }}
                  placeholder='Ej. "1 b45d (altura 80)"  ·  "2 a60i"  ·  "1 asc60x90 d"'
                  className="w-full pl-9 pr-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-400 outline-none" />
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
                  <button onClick={candadoClick} title="Coste/Margen (solo master) — mantén Shift y haz clic"
                    className="inline-flex items-center gap-1 text-slate-400 hover:text-emerald-600">
                    {verCoste ? <Unlock size={12} /> : <Lock size={12} />} Coste
                  </button>
                </th>
                <th className="text-right">
                  <button onClick={candadoClick} className="text-slate-400 hover:text-emerald-600" title="Shift+clic para ver">Margen</button>
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
