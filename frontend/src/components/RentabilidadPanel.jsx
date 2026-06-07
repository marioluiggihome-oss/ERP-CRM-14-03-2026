/**
 * RentabilidadPanel - Cuenta de resultados por proyecto (cocina)
 * Cruza Ventas (presupuestos) con Costes (facturas/gastos) -> Margen.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { TrendingUp, Plus, Trash2, RefreshCw, X, Euro, Upload, Sparkles } from 'lucide-react';
import RentabilidadLineas from './RentabilidadLineas';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const eur = (n) => (Number(n) || 0).toLocaleString('es-ES', { style: 'currency', currency: 'EUR' });

const RentabilidadPanel = ({ currentUser }) => {
  const [view, setView] = useState('lineas'); // 'lineas' | 'proyecto'
  const [data, setData] = useState({ rows: [], totales: {} });
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [costModal, setCostModal] = useState(null); // proyecto seleccionado para añadir/ver costes
  const [costs, setCosts] = useState([]);
  const [form, setForm] = useState({ proveedor: '', concepto: '', categoria: 'MOBILIARIO', importe: '' });
  // Importar factura por IA
  const [importing, setImporting] = useState(false);
  const [invoice, setInvoice] = useState(null); // datos extraidos + projectRef elegido
  const [analytics, setAnalytics] = useState({ bySupplier: [], byCategory: [], byMonth: [] });

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await fetch(`${API_URL}/api/rentabilidad`);
      if (r.ok) setData(await r.json());
      const a = await fetch(`${API_URL}/api/rentabilidad/analytics`);
      if (a.ok) setAnalytics(await a.json());
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

  // ---- Importar factura por IA ----
  const handleInvoiceFile = async (e) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;
    setImporting(true);
    try {
      const b64 = await new Promise((res, rej) => {
        const fr = new FileReader();
        fr.onload = () => res(fr.result);
        fr.onerror = rej;
        fr.readAsDataURL(file);
      });
      const r = await fetch(`${API_URL}/api/rentabilidad/parse-invoice`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fileBase64: b64 }),
      });
      const j = await r.json();
      if (!j.success) { alert('No se pudo leer la factura: ' + (j.error || '')); return; }
      // Intentar casar el proyecto detectado con uno existente
      const detected = (j.data.proyecto || '').trim();
      const match = data.rows.find(row => row.ref && detected &&
        row.ref.toLowerCase() === detected.toLowerCase());
      setInvoice({ ...j.data, projectRef: match ? match.ref : '' });
    } catch (err) {
      alert('Error al importar la factura: ' + err.message);
    } finally {
      setImporting(false);
    }
  };

  const saveInvoiceCost = async () => {
    if (!invoice.projectRef) { alert('Selecciona el proyecto al que asignar la factura'); return; }
    if (!invoice.importe || Number(invoice.importe) <= 0) { alert('Indica el importe'); return; }
    try {
      const r = await fetch(`${API_URL}/api/project-costs`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          projectRef: invoice.projectRef, proveedor: invoice.proveedor,
          concepto: invoice.concepto, categoria: invoice.categoria,
          importe: Number(invoice.importe), fecha: invoice.fecha, source: 'factura',
        }),
      });
      if (r.ok) { setInvoice(null); load(); }
      else alert('Error al registrar el coste');
    } catch (e) { alert('Error: ' + e.message); }
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
        <div className="flex items-center gap-2">
          <label className={`px-4 py-2 rounded-xl font-bold text-sm flex items-center gap-2 cursor-pointer ${importing ? 'bg-purple-200 text-purple-500' : 'bg-purple-600 text-white hover:bg-purple-700'}`}>
            <Sparkles size={16} className={importing ? 'animate-pulse' : ''} />
            {importing ? 'Leyendo factura…' : 'Importar factura (IA)'}
            <input type="file" accept="image/*,application/pdf" className="hidden" onChange={handleInvoiceFile} disabled={importing} />
          </label>
          <button onClick={load} className="px-4 py-2 bg-slate-100 hover:bg-slate-200 rounded-xl font-bold text-sm flex items-center gap-2">
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} /> Actualizar
          </button>
        </div>
      </div>

      {/* Conmutador de vista (orden lógico arriba del todo) */}
      <div className="flex gap-2 mb-5">
        <button onClick={() => setView('lineas')} className={`px-4 py-2 rounded-xl font-bold text-sm ${view === 'lineas' ? 'bg-slate-800 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}>Por líneas (documentos)</button>
        <button onClick={() => setView('proyecto')} className={`px-4 py-2 rounded-xl font-bold text-sm ${view === 'proyecto' ? 'bg-slate-800 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}>Por proyecto</button>
      </div>

      {view === 'lineas' && <RentabilidadLineas currentUser={currentUser} />}

      {view === 'proyecto' && (<>
      {/* Modal: revisar factura leída por IA antes de registrar */}
      {invoice && (
        <div className="fixed inset-0 bg-black/60 z-[130] flex items-center justify-center p-4" onClick={() => setInvoice(null)}>
          <div className="bg-white rounded-3xl w-full max-w-lg overflow-hidden" onClick={e => e.stopPropagation()}>
            <div className="bg-purple-600 text-white px-6 py-4 flex justify-between items-center">
              <h2 className="text-lg font-black flex items-center gap-2"><Sparkles size={18} /> Factura leída — revisa y asigna</h2>
              <button onClick={() => setInvoice(null)} className="p-2 hover:bg-white/20 rounded-xl"><X size={20} /></button>
            </div>
            <div className="p-6 space-y-3">
              <div>
                <label className="text-[10px] font-black text-slate-400 uppercase block mb-1">Proyecto (obligatorio)</label>
                <select value={invoice.projectRef} onChange={e => setInvoice({ ...invoice, projectRef: e.target.value })}
                  className={`w-full px-3 py-2 border rounded-lg text-sm font-bold ${invoice.projectRef ? 'border-emerald-300' : 'border-red-300'}`}>
                  <option value="">— Selecciona proyecto —</option>
                  {data.rows.map(r => <option key={r.projectId} value={r.ref}>{r.ref} · {r.cliente}</option>)}
                </select>
                {invoice.proyecto && !invoice.projectRef && (
                  <p className="text-[11px] text-amber-600 mt-1">La IA detectó "{invoice.proyecto}" pero no coincide con ningún proyecto. Selecciónalo a mano.</p>
                )}
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div><label className="text-[10px] font-black text-slate-400 uppercase block mb-1">Proveedor</label>
                  <input value={invoice.proveedor} onChange={e => setInvoice({ ...invoice, proveedor: e.target.value })} className="w-full px-3 py-2 border rounded-lg text-sm" /></div>
                <div><label className="text-[10px] font-black text-slate-400 uppercase block mb-1">Importe €</label>
                  <input type="number" step="0.01" value={invoice.importe} onChange={e => setInvoice({ ...invoice, importe: e.target.value })} className="w-full px-3 py-2 border rounded-lg text-sm text-right font-bold" /></div>
                <div><label className="text-[10px] font-black text-slate-400 uppercase block mb-1">Fecha</label>
                  <input value={invoice.fecha} onChange={e => setInvoice({ ...invoice, fecha: e.target.value })} className="w-full px-3 py-2 border rounded-lg text-sm" /></div>
                <div><label className="text-[10px] font-black text-slate-400 uppercase block mb-1">Categoría</label>
                  <select value={invoice.categoria} onChange={e => setInvoice({ ...invoice, categoria: e.target.value })} className="w-full px-3 py-2 border rounded-lg text-sm">
                    {['MOBILIARIO','ELECTRODOMESTICOS','ENCIMERA','TRANSPORTE','MONTAJE','SUBCONTRATA','OTROS'].map(c => <option key={c}>{c}</option>)}
                  </select></div>
              </div>
              <div><label className="text-[10px] font-black text-slate-400 uppercase block mb-1">Concepto</label>
                <input value={invoice.concepto} onChange={e => setInvoice({ ...invoice, concepto: e.target.value })} className="w-full px-3 py-2 border rounded-lg text-sm" /></div>
              <button onClick={saveInvoiceCost} className="w-full py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-black uppercase text-sm flex items-center justify-center gap-2">
                <Plus size={16} /> Registrar coste en el proyecto
              </button>
            </div>
          </div>
        </div>
      )}

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

      {/* ===== ANÁLISIS ===== */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mt-6">
        {/* Cocinas menos rentables */}
        <div className="bg-white border border-slate-200 rounded-2xl p-4">
          <h3 className="text-xs font-black text-red-600 uppercase mb-3">🔻 Cocinas menos rentables</h3>
          {[...data.rows].filter(r => r.coste > 0).sort((a, b) => a.margenPct - b.margenPct).slice(0, 5).map((r, i) => (
            <div key={r.projectId} className="flex justify-between items-center py-1.5 border-b border-slate-50 last:border-0">
              <span className="text-sm font-medium text-slate-700 truncate">{i + 1}. {r.ref || r.cliente || '—'}</span>
              <span className={`text-sm font-black ${r.margenPct >= 0 ? 'text-amber-600' : 'text-red-600'}`}>{r.margenPct}%</span>
            </div>
          ))}
          {data.rows.filter(r => r.coste > 0).length === 0 && <p className="text-sm text-slate-400">Registra costes para ver el ranking</p>}
        </div>
        {/* Gasto por proveedor */}
        <div className="bg-white border border-slate-200 rounded-2xl p-4">
          <h3 className="text-xs font-black text-orange-600 uppercase mb-3">🏷️ Gasto por proveedor</h3>
          {analytics.bySupplier.slice(0, 6).map((s, i) => (
            <div key={i} className="flex justify-between items-center py-1.5 border-b border-slate-50 last:border-0">
              <span className="text-sm text-slate-700 truncate">{s.nombre}</span>
              <span className="text-sm font-bold text-orange-600 font-mono">{eur(s.total)}</span>
            </div>
          ))}
          {analytics.bySupplier.length === 0 && <p className="text-sm text-slate-400">Sin costes aún</p>}
        </div>
        {/* Gasto por categoría */}
        <div className="bg-white border border-slate-200 rounded-2xl p-4">
          <h3 className="text-xs font-black text-indigo-600 uppercase mb-3">📦 Gasto por categoría</h3>
          {analytics.byCategory.map((c, i) => (
            <div key={i} className="flex justify-between items-center py-1.5 border-b border-slate-50 last:border-0">
              <span className="text-sm text-slate-700 truncate">{c.nombre}</span>
              <span className="text-sm font-bold text-indigo-600 font-mono">{eur(c.total)}</span>
            </div>
          ))}
          {analytics.byCategory.length === 0 && <p className="text-sm text-slate-400">Sin costes aún</p>}
        </div>
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
      </>)}
    </div>
  );
};

export default RentabilidadPanel;
