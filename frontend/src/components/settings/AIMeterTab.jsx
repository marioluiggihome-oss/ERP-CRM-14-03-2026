/**
 * AIMeterTab — Medidor de consumo de IA por cliente (mes en curso).
 * Muestra, por usuario con plan/cupo: renders del plan + packs extra, consumidos,
 * restantes, % de uso y coste estimado. Permite conceder packs de renders al
 * cliente que agota su cupo. Solo Admin/Master.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { Zap, RefreshCw, Plus, AlertTriangle, TrendingUp, X } from 'lucide-react';
import { authHeaders } from '../../services/api';

const BASE = process.env.REACT_APP_BACKEND_URL;
const eur = (n) => `${(Number(n) || 0).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} €`;

export default function AIMeterTab() {
  const [data, setData] = useState({ clients: [], cost_render: 0.12, month: '' });
  const [packs, setPacks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [granting, setGranting] = useState(null); // user row para el popover
  const [soloCarpinteros, setSoloCarpinteros] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [r1, r2] = await Promise.all([
        fetch(`${BASE}/api/admin/ai-usage/clients`, { headers: authHeaders() }),
        fetch(`${BASE}/api/admin/render-packs`, { headers: authHeaders() }),
      ]);
      const d1 = await r1.json(); const d2 = await r2.json();
      setData(d1.success ? d1 : { clients: [], cost_render: 0.12, month: '' });
      setPacks(d2.success ? d2.packs : []);
    } catch { /* noop */ }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { load(); }, [load]);

  const grant = async (userId, pack) => {
    try {
      const r = await fetch(`${BASE}/api/admin/render-packs/grant`, {
        method: 'POST', headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, pack_id: pack.id }),
      });
      const d = await r.json();
      if (!d.success) { alert(d.detail || 'No se pudo conceder el pack'); return; }
      setGranting(null);
      await load();
    } catch { alert('Error al conceder el pack'); }
  };

  const clients = (data.clients || []).filter(c => !soloCarpinteros || c.isCarpintero);
  const totalConsumidos = clients.reduce((s, c) => s + (c.consumidos || 0), 0);
  const totalCoste = clients.reduce((s, c) => s + (c.coste_estimado || 0), 0);
  const agotados = clients.filter(c => c.agotado).length;
  const barColor = (c) => c.agotado ? 'bg-red-500' : c.pct >= 80 ? 'bg-amber-500' : 'bg-emerald-500';

  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h3 className="text-lg font-black text-slate-800 flex items-center gap-2"><Zap size={18} className="text-amber-500" /> Consumo de IA por cliente</h3>
          <p className="text-sm text-slate-500">Renders del mes en curso ({data.month}). Coste por render ≈ {eur(data.cost_render)}.</p>
        </div>
        <div className="flex items-center gap-2">
          <label className="flex items-center gap-2 text-xs font-bold text-slate-600 cursor-pointer">
            <input type="checkbox" checked={soloCarpinteros} onChange={e => setSoloCarpinteros(e.target.checked)} /> Solo carpinteros
          </label>
          <button onClick={load} className="px-3 py-2 bg-slate-100 hover:bg-slate-200 rounded-lg"><RefreshCw size={16} className={loading ? 'animate-spin' : ''} /></button>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-3">
          <div className="text-[10px] font-black text-slate-400 uppercase">Renders consumidos</div>
          <div className="text-2xl font-black text-slate-800">{totalConsumidos}</div>
        </div>
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-3">
          <div className="text-[10px] font-black text-slate-400 uppercase flex items-center gap-1"><TrendingUp size={11} /> Coste IA estimado</div>
          <div className="text-2xl font-black text-emerald-600">{eur(totalCoste)}</div>
        </div>
        <div className={`rounded-xl p-3 border ${agotados ? 'bg-red-50 border-red-200' : 'bg-slate-50 border-slate-200'}`}>
          <div className="text-[10px] font-black text-slate-400 uppercase flex items-center gap-1"><AlertTriangle size={11} /> Cupo agotado</div>
          <div className={`text-2xl font-black ${agotados ? 'text-red-600' : 'text-slate-800'}`}>{agotados}</div>
        </div>
      </div>

      {/* Tabla */}
      <div className="border border-slate-200 rounded-xl overflow-hidden">
        <div className="max-h-[460px] overflow-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-100 text-slate-500 sticky top-0">
              <tr>
                <th className="text-left p-2 text-[10px] font-black uppercase">Cliente</th>
                <th className="text-left p-2 text-[10px] font-black uppercase">Plan</th>
                <th className="text-left p-2 text-[10px] font-black uppercase w-[38%]">Consumo</th>
                <th className="text-right p-2 text-[10px] font-black uppercase">Coste</th>
                <th className="p-2"></th>
              </tr>
            </thead>
            <tbody>
              {clients.map(c => (
                <tr key={c.id} className={`border-t border-slate-100 ${c.agotado ? 'bg-red-50/50' : ''}`}>
                  <td className="p-2">
                    <div className="font-bold text-slate-700 text-xs">{c.clientName || c.username}</div>
                    <div className="text-[10px] text-slate-400">{c.username}{c.isCarpintero ? ' · 🪚' : ''}</div>
                  </td>
                  <td className="p-2 text-xs text-slate-500">{c.planName}</td>
                  <td className="p-2">
                    {c.isAdmin && c.asignados === -1 ? (
                      <div className="flex items-center gap-2">
                        <span className="text-[11px] font-bold text-violet-600">{c.consumidos} usados</span>
                        <span className="text-[10px] bg-violet-100 text-violet-700 px-2 py-0.5 rounded-full font-bold">Ilimitado</span>
                      </div>
                    ) : (
                      <>
                        <div className="flex justify-between text-[11px] text-slate-500 mb-1">
                          <span>{c.consumidos} / {c.total}{c.extra > 0 ? ` (+${c.extra} pack)` : ''}</span>
                          <span className={c.agotado ? 'text-red-600 font-bold' : c.pct >= 80 ? 'text-amber-600 font-semibold' : 'text-slate-500'}>{c.pct}%</span>
                        </div>
                        <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
                          <div className={`h-full ${barColor(c)} rounded-full`} style={{ width: `${Math.min(c.pct, 100)}%` }} />
                        </div>
                      </>
                    )}
                  </td>
                  <td className="p-2 text-right text-xs font-bold text-slate-600">{eur(c.coste_estimado)}</td>
                  <td className="p-2 whitespace-nowrap relative">
                    {!c.isAdmin && <button onClick={() => setGranting(granting === c.id ? null : c.id)}
                      className="px-2 py-1 rounded text-[11px] font-bold bg-orange-600 text-white hover:bg-orange-700 inline-flex items-center gap-1"><Plus size={12} /> Pack</button>}
                    {granting === c.id && (
                      <div className="absolute right-2 top-9 z-10 bg-white border border-slate-200 rounded-xl shadow-xl p-2 w-52">
                        <div className="flex items-center justify-between px-1 pb-1">
                          <span className="text-[10px] font-black text-slate-400 uppercase">Conceder pack</span>
                          <button onClick={() => setGranting(null)} className="text-slate-400 hover:text-slate-600"><X size={13} /></button>
                        </div>
                        {packs.map(p => (
                          <button key={p.id} onClick={() => grant(c.id, p)}
                            className="w-full flex items-center justify-between px-2 py-1.5 rounded-lg hover:bg-orange-50 text-xs">
                            <span className="font-bold text-slate-700">+{p.renders} renders</span>
                            <span className="text-slate-500">{eur(p.price)}</span>
                          </button>
                        ))}
                      </div>
                    )}
                  </td>
                </tr>
              ))}
              {clients.length === 0 && !loading && (
                <tr><td colSpan={5} className="p-6 text-center text-slate-400 text-sm">Sin consumo de IA este mes.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
      <p className="text-[11px] text-slate-400">Los packs suman renders al cupo del mes en curso del cliente. Coste real por render ≈ {eur(data.cost_render)}; los packs se venden con amplio margen.</p>
    </div>
  );
}
