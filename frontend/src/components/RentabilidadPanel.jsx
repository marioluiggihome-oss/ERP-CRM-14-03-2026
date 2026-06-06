/**
 * RentabilidadPanel - Cuenta de resultados por proyecto (cocina)
 * Cruza Ventas (presupuestos) con Costes (facturas/gastos) -> Margen.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { TrendingUp, Plus, Trash2, RefreshCw, X, Euro } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const eur = (n) => (Number(n) || 0).toLocaleString('es-ES', { style: 'currency', currency: 'EUR' });

const RentabilidadPanel = ({ currentUser }) => {
  const [data, setData] = useState({ rows: [], totales: {} });
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [costModal, setCostModal] = useState(null); // proyecto seleccionado para añadir/ver costes
  const [costs, setCosts] = useState([]);
  const [form, setForm] = useState({ proveedor: '', concepto: '', categoria: 'MOBILIARIO', importe: '' });

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await fetch(`${API_URL}/api/rentabilidad`);
      if (r.ok) setData(await r.json());
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const openCosts = async (row) => {
    setCostModal(row);
    try {
      const r = await fetch(`${API_URL}/api/project-costs?projectRef=${encodeURIComponent(row.ref)}`);
      setCosts(r.ok ? await r.json() : []);
    } catch (e) { setCosts([]); }
  };

  const addCost = async () => {
    if (!form.importe || Number(form.importe) <= 0) { alert('Indica el importe'); return; }
    try {
      const r = await fetch(`${API_URL}/api/project-costs`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...form, importe: Number(form.importe), projectRef: costModal.ref, source: 'manual' })
      });
      if (r.ok) {
        setForm({ proveedor: '', concepto: '', categoria: 'MOBILIARIO', importe: '' });
        await openCosts(costModal);
        load();
      }
    } catch (e) { alert('Error al guardar el coste'); }
  };

  const delCost = async (id) => {
    await fetch(`${API_URL}/api/project-costs/${id}`, { method: 'DELETE' });
    await openCosts(costModal);
    load();
  };

  const rows = data.rows.filter(r =>
    !search || (r.ref || '').toLowerCase().includes(search.toLowerCase())
    || (r.cliente || '').toLowerCase().includes(search.toLowerCase()));
  const t = data.totales || {};

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-emerald-600 rounded-2xl flex items-center justify-center text-white"><TrendingUp size={24} /></div>
          <div>
            <h1 className="text-2xl font-black text-slate-900 uppercase">Rentabilidad por Proyecto</h1>
            <p className="text-sm text-slate-500">Venta − Coste = Margen por cocina</p>
          </div>
        </div>
        <button onClick={load} className="px-4 py-2 bg-slate-100 hover:bg-slate-200 rounded-xl font-bold text-sm flex items-center gap-2">
          <RefreshCw size={16} className={loading ? 'animate-spin' : ''} /> Actualizar
        </button>
      </div>

      {/* Totales */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-indigo-600 text-white p-4 rounded-2xl"><p className="text-[10px] uppercase opacity-80">Venta total</p><p className="text-2xl font-black">{eur(t.venta)}</p></div>
        <div className="bg-orange-600 text-white p-4 rounded-2xl"><p className="text-[10px] uppercase opacity-80">Coste total</p><p className="text-2xl font-black">{eur(t.coste)}</p></div>
        <div className={`${(t.margen || 0) >= 0 ? 'bg-emerald-600' : 'bg-red-600'} text-white p-4 rounded-2xl`}><p className="text-[10px] uppercase opacity-80">Margen total</p><p className="text-2xl font-black">{eur(t.margen)}</p><p className="text-[11px] opacity-80">{t.margenPct}%</p></div>
        <div className="bg-slate-800 text-white p-4 rounded-2xl"><p className="text-[10px] uppercase opacity-80">Proyectos</p><p className="text-2xl font-black">{t.proyectos || 0}</p></div>
      </div>

      <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Buscar por nº de proyecto o cliente…"
        className="w-full mb-4 px-4 py-2.5 border border-slate-200 rounded-xl text-sm outline-none focus:border-emerald-500" />

      <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-slate-100 text-slate-600">
            <tr>
              <th className="text-left p-3 text-xs font-black uppercase">Proyecto</th>
              <th className="text-left p-3 text-xs font-black uppercase">Cliente</th>
              <th className="text-right p-3 text-xs font-black uppercase">Venta</th>
              <th className="text-right p-3 text-xs font-black uppercase">Coste</th>
              <th className="text-right p-3 text-xs font-black uppercase">Margen</th>
              <th className="text-right p-3 text-xs font-black uppercase">%</th>
              <th className="text-center p-3 text-xs font-black uppercase">Costes</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {rows.map((r) => (
              <tr key={r.projectId} className="hover:bg-slate-50">
                <td className="p-3 font-black text-indigo-700">{r.ref || '—'}</td>
                <td className="p-3 text-slate-700">{r.cliente || '—'}</td>
                <td className="p-3 text-right font-mono">{eur(r.venta)}</td>
                <td className="p-3 text-right font-mono text-orange-600">{eur(r.coste)}</td>
                <td className={`p-3 text-right font-mono font-black ${r.margen >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>{eur(r.margen)}</td>
                <td className={`p-3 text-right font-bold ${r.margen >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>{r.margenPct}%</td>
                <td className="p-3 text-center">
                  <button onClick={() => openCosts(r)} className="px-3 py-1.5 bg-emerald-50 text-emerald-700 rounded-lg text-xs font-bold hover:bg-emerald-100 flex items-center gap-1 mx-auto">
                    <Plus size={12} /> Coste
                  </button>
                </td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr><td colSpan={7} className="p-8 text-center text-slate-400">{loading ? 'Cargando…' : 'Sin proyectos'}</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Modal de costes de un proyecto */}
      {costModal && (
        <div className="fixed inset-0 bg-black/60 z-[120] flex items-center justify-center p-4" onClick={() => setCostModal(null)}>
          <div className="bg-white rounded-3xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col" onClick={e => e.stopPropagation()}>
            <div className="bg-emerald-600 text-white px-6 py-4 flex justify-between items-center">
              <div>
                <h2 className="text-lg font-black">Costes — {costModal.ref}</h2>
                <p className="text-xs text-emerald-100">{costModal.cliente} · Venta {eur(costModal.venta)}</p>
              </div>
              <button onClick={() => setCostModal(null)} className="p-2 hover:bg-white/20 rounded-xl"><X size={20} /></button>
            </div>
            <div className="p-6 overflow-auto space-y-4">
              {/* Formulario de alta de coste */}
              <div className="grid grid-cols-2 md:grid-cols-5 gap-2 items-end bg-slate-50 p-3 rounded-xl">
                <input value={form.proveedor} onChange={e => setForm({ ...form, proveedor: e.target.value })} placeholder="Proveedor" className="px-2 py-2 border rounded-lg text-sm" />
                <input value={form.concepto} onChange={e => setForm({ ...form, concepto: e.target.value })} placeholder="Concepto" className="px-2 py-2 border rounded-lg text-sm" />
                <select value={form.categoria} onChange={e => setForm({ ...form, categoria: e.target.value })} className="px-2 py-2 border rounded-lg text-sm">
                  {['MOBILIARIO','ELECTRODOMÉSTICOS','ENCIMERA','TRANSPORTE','MONTAJE','SUBCONTRATA','OTROS'].map(c => <option key={c}>{c}</option>)}
                </select>
                <input type="number" step="0.01" value={form.importe} onChange={e => setForm({ ...form, importe: e.target.value })} placeholder="€" className="px-2 py-2 border rounded-lg text-sm text-right" />
                <button onClick={addCost} className="px-3 py-2 bg-emerald-600 text-white rounded-lg font-bold text-sm flex items-center justify-center gap-1"><Plus size={14} /> Añadir</button>
              </div>
              {/* Lista de costes */}
              <table className="w-full text-sm">
                <thead className="text-slate-500"><tr><th className="text-left p-2 text-xs uppercase">Proveedor</th><th className="text-left p-2 text-xs uppercase">Concepto</th><th className="text-left p-2 text-xs uppercase">Cat.</th><th className="text-right p-2 text-xs uppercase">Importe</th><th></th></tr></thead>
                <tbody className="divide-y divide-slate-100">
                  {costs.map(c => (
                    <tr key={c.id}>
                      <td className="p-2 font-medium">{c.proveedor || '—'}</td>
                      <td className="p-2 text-slate-600">{c.concepto || '—'}</td>
                      <td className="p-2 text-[11px] text-slate-500">{c.categoria}</td>
                      <td className="p-2 text-right font-mono font-bold text-orange-600">{eur(c.importe)}</td>
                      <td className="p-2 text-right"><button onClick={() => delCost(c.id)} className="text-red-400 hover:text-red-600"><Trash2 size={14} /></button></td>
                    </tr>
                  ))}
                  {costs.length === 0 && <tr><td colSpan={5} className="p-4 text-center text-slate-400">Sin costes aún</td></tr>}
                </tbody>
              </table>
              <div className="bg-slate-900 text-white rounded-xl p-4 flex justify-between items-center">
                <span className="text-xs uppercase text-slate-400">Coste total · Margen</span>
                <span className="font-black">
                  {eur(costs.reduce((s, c) => s + (Number(c.importe) || 0), 0))}
                  {' · '}
                  <span className={costModal.venta - costs.reduce((s, c) => s + (Number(c.importe) || 0), 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}>
                    {eur(costModal.venta - costs.reduce((s, c) => s + (Number(c.importe) || 0), 0))}
                  </span>
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RentabilidadPanel;
