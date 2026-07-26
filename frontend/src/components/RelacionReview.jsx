/**
 * RelacionReview — Panel de revisión de la relación de muebles importada del PDF
 * (o añadida a mano). Muestra los muebles detectados en un listado editable
 * (cantidad, borrar), un BUSCADOR para añadir los que no se hayan detectado, y un
 * botón para volcar todo al presupuesto de Cocina Desmontada.
 *
 * Props:
 *   muebles     : array inicial de muebles detectados [{qty,cod,tipo,ancho,alto,fondo,pvp,encontrado,raw}]
 *   onConfirm   : (muebles) => void   -> volcar al presupuesto
 *   onClose     : () => void
 *   apiUrl, authHeaders : para el buscador (endpoint detectar-relacion vía texto)
 */
import React, { useState } from 'react';
import { X, Plus, Trash2, Search, Check, Loader, AlertTriangle, FileUp } from 'lucide-react';

const eur = (n) => (n == null ? '—' : `${Number(n).toFixed(2)} €`);

export default function RelacionReview({ muebles: inicial, onConfirm, onClose, apiUrl, authHeaders }) {
  const [muebles, setMuebles] = useState(() => (inicial || []).map((m, i) => ({ ...m, _k: `${m.cod || 'x'}-${i}-${m.raw || ''}` })));
  const [busca, setBusca] = useState('');
  const [buscando, setBuscando] = useState(false);
  const [aviso, setAviso] = useState('');

  const setQty = (k, v) => setMuebles(prev => prev.map(m => m._k === k ? { ...m, qty: Math.max(1, Number(v) || 1) } : m));
  const quitar = (k) => setMuebles(prev => prev.filter(m => m._k !== k));

  const totalUds = muebles.reduce((s, m) => s + (Number(m.qty) || 1), 0);
  const totalPvp = muebles.reduce((s, m) => s + (Number(m.pvp) || 0) * (Number(m.qty) || 1), 0);

  const añadir = async () => {
    const texto = busca.trim();
    if (!texto) return;
    setBuscando(true); setAviso('');
    try {
      const r = await fetch(`${apiUrl}/api/cascos/mv/detectar-relacion`, {
        method: 'POST', headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ texto }),
      });
      let d = {}; try { d = await r.json(); } catch { d = {}; }
      if (!r.ok || !d.success) { setAviso(d.detail || 'No se reconoció el mueble. Escríbelo como "1 b60i (altura 80)".'); return; }
      const nuevos = (d.muebles || []).map((m, i) => ({ ...m, _k: `add-${Date.now()}-${i}` }));
      setMuebles(prev => [...prev, ...nuevos]);
      setBusca('');
    } catch (e) {
      setAviso(`Error al buscar (${e?.message || 'red'}).`);
    } finally {
      setBuscando(false);
    }
  };

  const confirmar = () => {
    if (!muebles.length) return;
    onConfirm(muebles.map(m => ({ tipo: m.tipo, ancho: m.ancho, alto: m.alto, fondo: m.fondo, qty: m.qty || 1, cod: m.cod })));
  };

  const noEncontrados = muebles.filter(m => !m.encontrado).length;

  return (
    <div className="fixed inset-0 z-[60] bg-black/50 flex items-center justify-center p-3" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] flex flex-col overflow-hidden" onClick={e => e.stopPropagation()}>
        {/* Cabecera */}
        <div className="px-5 py-3.5 bg-gradient-to-r from-indigo-600 to-violet-600 text-white flex items-center justify-between">
          <h3 className="font-black flex items-center gap-2"><FileUp size={18} /> Revisar relación de muebles</h3>
          <button onClick={onClose} className="p-1.5 hover:bg-white/20 rounded-lg"><X size={18} /></button>
        </div>

        {/* Buscador para añadir a mano */}
        <div className="px-5 pt-4">
          <label className="text-[11px] font-bold text-slate-500 uppercase">Añadir mueble (si falta alguno)</label>
          <div className="flex gap-2 mt-1">
            <div className="relative flex-1">
              <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input value={busca} onChange={e => setBusca(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') añadir(); }}
                placeholder='Ej. "1 b45d (altura 80)"  ·  "2 a60i"  ·  "1 asc60x90 d"'
                className="w-full pl-9 pr-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-400 outline-none" />
            </div>
            <button onClick={añadir} disabled={buscando || !busca.trim()}
              className="flex items-center gap-1.5 px-3.5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-bold text-sm disabled:opacity-50">
              {buscando ? <Loader size={15} className="animate-spin" /> : <Plus size={15} />} Añadir
            </button>
          </div>
          {aviso && <p className="text-xs text-amber-700 mt-1.5 flex items-center gap-1"><AlertTriangle size={13} /> {aviso}</p>}
        </div>

        {/* Listado */}
        <div className="px-5 py-3 overflow-y-auto flex-1">
          {noEncontrados > 0 && (
            <p className="text-[11px] text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-3 py-1.5 mb-2">
              {noEncontrados} mueble(s) sin código de tarifa (van igualmente, precio a ajustar).
            </p>
          )}
          <table className="w-full text-sm">
            <thead>
              <tr className="text-[10px] uppercase text-slate-400 border-b border-slate-200">
                <th className="text-left py-1.5">Código</th>
                <th className="text-left">Tipo</th>
                <th className="text-right">Ancho</th>
                <th className="text-right">Alto</th>
                <th className="text-center">Uds</th>
                <th className="text-right">PVP MV</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {muebles.map(m => (
                <tr key={m._k} className="border-b border-slate-100">
                  <td className="py-1.5 font-black text-indigo-900">
                    {m.cod || <span className="text-amber-600">{(m.raw || '¿?').toUpperCase()}</span>}
                  </td>
                  <td className="text-slate-500 text-xs">{m.tipo}</td>
                  <td className="text-right text-slate-600">{m.ancho} cm</td>
                  <td className="text-right text-slate-600">{m.alto ? `${m.alto} cm` : '—'}</td>
                  <td className="text-center">
                    <input type="number" min="1" value={m.qty || 1} onChange={e => setQty(m._k, e.target.value)}
                      className="w-14 text-center border border-slate-300 rounded px-1 py-0.5 text-sm" />
                  </td>
                  <td className="text-right text-slate-700 font-semibold">{eur(m.pvp)}</td>
                  <td className="text-right">
                    <button onClick={() => quitar(m._k)} className="p-1 text-slate-400 hover:text-red-600"><Trash2 size={15} /></button>
                  </td>
                </tr>
              ))}
              {!muebles.length && (
                <tr><td colSpan={7} className="text-center text-slate-400 py-6 text-sm">No hay muebles. Añade alguno con el buscador.</td></tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pie */}
        <div className="px-5 py-3.5 border-t border-slate-200 flex items-center justify-between gap-3 bg-slate-50">
          <div className="text-sm text-slate-600">
            <span className="font-black text-slate-800">{totalUds}</span> uds ·
            <span className="font-black text-slate-800"> {eur(totalPvp)}</span> <span className="text-xs text-slate-400">PVP MV orientativo</span>
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
