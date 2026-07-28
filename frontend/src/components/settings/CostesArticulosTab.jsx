/**
 * CostesArticulosTab — Catálogo de costes por artículo (coste medio ponderado)
 * Zona del máster para auditar, actualizar y modificar los costes que alimentan
 * las líneas del módulo de Rentabilidad. Los datos viven en MongoDB (colección
 * article_costs) y se siembran la primera vez desde el CSV validado.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { Search, Save, Trash2, RefreshCw, Plus, AlertTriangle, History, Sparkles } from 'lucide-react';
import { authHeaders } from '../../services/api';
import ArticleCostsIAModal from '../ArticleCostsIAModal';

const BASE = process.env.REACT_APP_BACKEND_URL;

const eur = (n) => `${(Number(n) || 0).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 4 })} €`;

export default function CostesArticulosTab() {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [q, setQ] = useState('');
  const [soloRevisar, setSoloRevisar] = useState(false);
  const [loading, setLoading] = useState(false);
  const [edits, setEdits] = useState({}); // codigoNorm -> { costeUnitario, nombre, revisar }
  const [savingCode, setSavingCode] = useState('');
  const [nuevo, setNuevo] = useState({ codigo: '', nombre: '', costeUnitario: '' });
  const [audit, setAudit] = useState(null); // { codigo, items }

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (q.trim()) params.set('q', q.trim());
      if (soloRevisar) params.set('soloRevisar', 'true');
      params.set('limit', '2000');
      const r = await fetch(`${BASE}/api/rentabilidad/article-costs?${params.toString()}`, { headers: authHeaders() });
      const data = await r.json();
      setItems(data.items || []);
      setTotal(data.total || 0);
      setEdits({});
    } catch { /* noop */ }
    finally { setLoading(false); }
  }, [q, soloRevisar]);

  useEffect(() => { load(); }, [load]);

  const setEdit = (code, field, val) => {
    setEdits(prev => ({ ...prev, [code]: { ...(prev[code] || {}), [field]: val } }));
  };

  const guardar = async (art) => {
    const code = art.codigoNorm || art.codigo;
    const ed = edits[code] || {};
    const payload = {
      codigo: art.codigo,
      nombre: ed.nombre !== undefined ? ed.nombre : art.nombre,
      costeUnitario: ed.costeUnitario !== undefined ? String(ed.costeUnitario).replace(',', '.') : art.costeUnitario,
      cantidad: art.cantidad,
      costeTotal: art.costeTotal,
      revisar: ed.revisar !== undefined ? ed.revisar : art.revisar,
    };
    setSavingCode(code);
    try {
      const r = await fetch(`${BASE}/api/rentabilidad/article-costs`, {
        method: 'POST', headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await r.json();
      if (!data.success) { alert(data.detail || 'No se pudo guardar'); return; }
      await load();
    } catch { alert('Error al guardar el coste'); }
    finally { setSavingCode(''); }
  };

  const borrar = async (art) => {
    if (!window.confirm(`¿Eliminar del catálogo el artículo ${art.codigo}?`)) return;
    try {
      await fetch(`${BASE}/api/rentabilidad/article-costs/${encodeURIComponent(art.codigo)}`, {
        method: 'DELETE', headers: authHeaders(),
      });
      await load();
    } catch { alert('Error al eliminar'); }
  };

  const crear = async () => {
    if (!nuevo.codigo.trim()) { alert('Indica el código del artículo'); return; }
    try {
      const r = await fetch(`${BASE}/api/rentabilidad/article-costs`, {
        method: 'POST', headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({
          codigo: nuevo.codigo.trim(), nombre: nuevo.nombre.trim(),
          costeUnitario: String(nuevo.costeUnitario).replace(',', '.'), source: 'manual',
        }),
      });
      const data = await r.json();
      if (!data.success) { alert(data.detail || 'No se pudo crear'); return; }
      setNuevo({ codigo: '', nombre: '', costeUnitario: '' });
      await load();
    } catch { alert('Error al crear el artículo'); }
  };

  const reseed = async (replace) => {
    const msg = replace
      ? 'RECARGA COMPLETA: borra el catálogo actual y lo vuelve a sembrar desde el CSV.\n\n⚠️ Se pierden las ediciones manuales. ¿Continuar?'
      : 'Recargar desde el CSV (upsert): añade/actualiza artículos del CSV, respetando el resto. ¿Continuar?';
    if (!window.confirm(msg)) return;
    try {
      const r = await fetch(`${BASE}/api/rentabilidad/article-costs/reseed`, {
        method: 'POST', headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ replace }),
      });
      const data = await r.json();
      if (!data.success) { alert(data.detail || 'No se pudo recargar'); return; }
      alert(`Catálogo recargado (${data.mode}): ${data.count} artículos.`);
      await load();
    } catch { alert('Error al recargar el catálogo'); }
  };

  const verAudit = async (art) => {
    try {
      const r = await fetch(`${BASE}/api/rentabilidad/article-costs/audit?codigo=${encodeURIComponent(art.codigo)}&limit=50`, { headers: authHeaders() });
      const data = await r.json();
      setAudit({ codigo: art.codigo, items: data.items || [] });
    } catch { alert('No se pudo cargar el histórico'); }
  };

  const revisarCount = items.filter(i => i.revisar).length;

  // Subir con IA: pega una captura/PDF/Excel de un pedido/tarifa de proveedor +
  // una orden en texto libre. Modal compartido con el editor de fichas de
  // Rentabilidad (ArticleCostsIAModal).
  const [showIA, setShowIA] = useState(false);

  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h3 className="text-lg font-black text-slate-800">Costes de artículos</h3>
          <p className="text-sm text-slate-500">Coste medio ponderado por artículo · alimenta las líneas de Rentabilidad. {total} artículos en catálogo.</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => setShowIA(true)} className="px-3 py-2 bg-gradient-to-r from-fuchsia-600 to-indigo-600 text-white hover:opacity-90 rounded-lg text-xs font-bold flex items-center gap-1.5">
            <Sparkles size={14} /> Subir con IA (captura + orden)
          </button>
          <button onClick={() => reseed(false)} className="px-3 py-2 bg-slate-100 hover:bg-slate-200 rounded-lg text-xs font-bold flex items-center gap-1.5">
            <RefreshCw size={14} /> Recargar CSV (upsert)
          </button>
          <button onClick={() => reseed(true)} className="px-3 py-2 bg-red-50 text-red-700 hover:bg-red-100 rounded-lg text-xs font-bold flex items-center gap-1.5">
            <AlertTriangle size={14} /> Recarga completa
          </button>
        </div>
      </div>

      {/* Buscador + filtros */}
      <div className="flex items-center gap-2 flex-wrap">
        <div className="relative flex-1 min-w-[220px]">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            value={q} onChange={e => setQ(e.target.value)}
            placeholder="Buscar por código o nombre…"
            className="w-full pl-9 pr-3 py-2 border border-slate-200 rounded-lg text-sm"
          />
        </div>
        <label className="flex items-center gap-2 text-xs font-bold text-slate-600 cursor-pointer select-none">
          <input type="checkbox" checked={soloRevisar} onChange={e => setSoloRevisar(e.target.checked)} />
          Solo a revisar {revisarCount > 0 && <span className="px-1.5 py-0.5 bg-amber-100 text-amber-700 rounded">{revisarCount}</span>}
        </label>
        <button onClick={load} className="px-3 py-2 bg-slate-100 hover:bg-slate-200 rounded-lg">
          <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
        </button>
      </div>

      {/* Alta rápida */}
      <div className="flex items-center gap-2 flex-wrap bg-slate-50 border border-slate-200 rounded-xl p-3">
        <input value={nuevo.codigo} onChange={e => setNuevo({ ...nuevo, codigo: e.target.value })} placeholder="Código" className="px-2 py-1.5 border rounded-lg text-sm w-40" />
        <input value={nuevo.nombre} onChange={e => setNuevo({ ...nuevo, nombre: e.target.value })} placeholder="Nombre" className="px-2 py-1.5 border rounded-lg text-sm flex-1 min-w-[160px]" />
        <input value={nuevo.costeUnitario} onChange={e => setNuevo({ ...nuevo, costeUnitario: e.target.value })} placeholder="Coste unit. €" className="px-2 py-1.5 border rounded-lg text-sm w-32" />
        <button onClick={crear} className="px-3 py-1.5 bg-emerald-600 text-white hover:bg-emerald-700 rounded-lg text-xs font-bold flex items-center gap-1"><Plus size={14} /> Añadir</button>
      </div>

      {/* Tabla */}
      <div className="border border-slate-200 rounded-xl overflow-hidden">
        <div className="max-h-[520px] overflow-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-100 text-slate-500 sticky top-0">
              <tr>
                <th className="text-left p-2 text-[10px] font-black uppercase">Código</th>
                <th className="text-left p-2 text-[10px] font-black uppercase">Nombre</th>
                <th className="text-right p-2 text-[10px] font-black uppercase">Cant.</th>
                <th className="text-right p-2 text-[10px] font-black uppercase">Coste total</th>
                <th className="text-right p-2 text-[10px] font-black uppercase">Coste unit.</th>
                <th className="text-left p-2 text-[10px] font-black uppercase">Revisar</th>
                <th className="p-2"></th>
              </tr>
            </thead>
            <tbody>
              {items.map(art => {
                const code = art.codigoNorm || art.codigo;
                const ed = edits[code] || {};
                const dirty = ed.costeUnitario !== undefined || ed.nombre !== undefined || ed.revisar !== undefined;
                return (
                  <tr key={code} className={`border-t border-slate-100 ${art.revisar ? 'bg-amber-50' : ''}`}>
                    <td className="p-2 font-mono text-xs font-bold text-slate-700">{art.codigo}</td>
                    <td className="p-2">
                      <input
                        value={ed.nombre !== undefined ? ed.nombre : (art.nombre || '')}
                        onChange={e => setEdit(code, 'nombre', e.target.value)}
                        className="w-full px-1.5 py-1 border border-transparent hover:border-slate-200 focus:border-indigo-400 rounded text-xs"
                      />
                    </td>
                    <td className="p-2 text-right text-xs text-slate-500">{art.cantidad ?? '—'}</td>
                    <td className="p-2 text-right text-xs text-slate-500">{art.costeTotal != null ? eur(art.costeTotal) : '—'}</td>
                    <td className="p-2 text-right">
                      <input
                        value={ed.costeUnitario !== undefined ? ed.costeUnitario : (art.costeUnitario ?? '')}
                        onChange={e => setEdit(code, 'costeUnitario', e.target.value)}
                        className="w-24 px-1.5 py-1 border border-slate-200 focus:border-indigo-400 rounded text-xs text-right font-bold"
                      />
                    </td>
                    <td className="p-2">
                      <input
                        value={ed.revisar !== undefined ? ed.revisar : (art.revisar || '')}
                        onChange={e => setEdit(code, 'revisar', e.target.value)}
                        className="w-32 px-1.5 py-1 border border-transparent hover:border-slate-200 rounded text-[11px] text-amber-700"
                      />
                    </td>
                    <td className="p-2 whitespace-nowrap">
                      <button onClick={() => guardar(art)} disabled={!dirty || savingCode === code}
                        className={`px-2 py-1 rounded text-xs font-bold ${dirty ? 'bg-indigo-600 text-white hover:bg-indigo-700' : 'bg-slate-100 text-slate-400'}`}>
                        <Save size={13} />
                      </button>
                      <button onClick={() => verAudit(art)} title="Histórico de cambios" className="px-2 py-1 ml-1 rounded text-xs bg-slate-100 hover:bg-slate-200"><History size={13} /></button>
                      <button onClick={() => borrar(art)} title="Eliminar" className="px-2 py-1 ml-1 rounded text-xs bg-red-50 text-red-600 hover:bg-red-100"><Trash2 size={13} /></button>
                    </td>
                  </tr>
                );
              })}
              {items.length === 0 && !loading && (
                <tr><td colSpan={7} className="p-6 text-center text-slate-400 text-sm">Sin artículos. Usa «Recargar CSV» para sembrar el catálogo.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal histórico de auditoría */}
      {audit && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" onClick={() => setAudit(null)}>
          <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[80vh] overflow-auto p-5" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-black text-slate-800">Histórico de cambios · {audit.codigo}</h4>
              <button onClick={() => setAudit(null)} className="text-slate-400 hover:text-slate-600">✕</button>
            </div>
            {audit.items.length === 0 ? (
              <p className="text-sm text-slate-400">Sin cambios registrados.</p>
            ) : (
              <div className="space-y-2">
                {audit.items.map((a, i) => (
                  <div key={i} className="text-xs border border-slate-200 rounded-lg p-2">
                    <div className="text-slate-400">{a.createdAt?.slice(0, 19).replace('T', ' ')} · {a.userName || '—'}</div>
                    <div className="text-slate-700">
                      Coste unit.: <b>{a.before?.costeUnitario ?? '—'}</b> → <b className="text-indigo-600">{a.after?.costeUnitario ?? '—'}</b>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {showIA && (
        <ArticleCostsIAModal
          onClose={() => setShowIA(false)}
          onSaved={() => load()}
        />
      )}
    </div>
  );
}
