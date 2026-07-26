/**
 * CRMPostventa — Service Hub (fase 2): tickets de postventa (incidencias de
 * montaje, garantías, reclamaciones) con estados, prioridad, SLA y comentarios.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { LifeBuoy, Plus, Loader, Clock, AlertTriangle, CheckCircle, Trash2, MessageSquare, Send, X } from 'lucide-react';
import { authHeaders } from '../services/api';

const API = process.env.REACT_APP_BACKEND_URL;
const H = () => authHeaders({ 'Content-Type': 'application/json' });

const ESTADO_LABEL = { abierto: 'Abierto', en_proceso: 'En proceso', espera_cliente: 'Espera cliente', resuelto: 'Resuelto', cerrado: 'Cerrado' };
const ESTADO_COLOR = { abierto: 'bg-blue-100 text-blue-700', en_proceso: 'bg-amber-100 text-amber-700', espera_cliente: 'bg-purple-100 text-purple-700', resuelto: 'bg-emerald-100 text-emerald-700', cerrado: 'bg-slate-200 text-slate-600' };
const PRIO_COLOR = { baja: 'text-slate-400', media: 'text-blue-500', alta: 'text-orange-500', urgente: 'text-red-600' };
const TIPOS = [{ v: 'incidencia', l: 'Incidencia montaje' }, { v: 'garantia', l: 'Garantía' }, { v: 'reclamacion', l: 'Reclamación' }, { v: 'consulta', l: 'Consulta' }];

const fmt = (s) => { try { return new Date(s).toLocaleDateString('es-ES', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }); } catch { return ''; } };

export default function CRMPostventa() {
  const [tickets, setTickets] = useState([]);
  const [stats, setStats] = useState(null);
  const [estados, setEstados] = useState(['abierto', 'en_proceso', 'espera_cliente', 'resuelto', 'cerrado']);
  const [prioridades, setPrioridades] = useState(['baja', 'media', 'alta', 'urgente']);
  const [filtro, setFiltro] = useState('');
  const [cargando, setCargando] = useState(false);
  const [nuevo, setNuevo] = useState(null); // formulario alta
  const [detalle, setDetalle] = useState(null);
  const [coment, setComent] = useState('');

  const cargar = useCallback(async () => {
    setCargando(true);
    try {
      const url = `${API}/api/crm/tickets${filtro ? `?estado=${filtro}` : ''}`;
      const [tr, sr] = await Promise.all([
        fetch(url, { headers: authHeaders() }).then(r => r.json()),
        fetch(`${API}/api/crm/tickets/stats`, { headers: authHeaders() }).then(r => r.json()),
      ]);
      if (tr.success) { setTickets(tr.tickets || []); setEstados(tr.estados || estados); setPrioridades(tr.prioridades || prioridades); }
      if (sr.success) setStats(sr);
    } catch { /* noop */ } finally { setCargando(false); }
  }, [filtro]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { cargar(); }, [cargar]);

  const crear = async () => {
    if (!nuevo.asunto?.trim()) return;
    const r = await fetch(`${API}/api/crm/tickets`, { method: 'POST', headers: H(), body: JSON.stringify(nuevo) });
    const d = await r.json();
    if (d.success) { setNuevo(null); cargar(); }
  };
  const cambiar = async (t, campos) => {
    const r = await fetch(`${API}/api/crm/tickets/${t.id}`, { method: 'PATCH', headers: H(), body: JSON.stringify(campos) });
    const d = await r.json();
    if (d.success) { setTickets(prev => prev.map(x => x.id === t.id ? { ...x, ...d.ticket } : x)); if (detalle?.id === t.id) setDetalle(d.ticket); cargar(); }
  };
  const borrar = async (t) => { if (!window.confirm(`¿Borrar ${t.numero}?`)) return; await fetch(`${API}/api/crm/tickets/${t.id}`, { method: 'DELETE', headers: authHeaders() }); setDetalle(null); cargar(); };
  const comentar = async () => {
    if (!coment.trim() || !detalle) return;
    const r = await fetch(`${API}/api/crm/tickets/${detalle.id}/comentario`, { method: 'POST', headers: H(), body: JSON.stringify({ texto: coment }) });
    const d = await r.json();
    if (d.success) { setDetalle(dt => ({ ...dt, comentarios: [...(dt.comentarios || []), d.comentario] })); setComent(''); }
  };

  return (
    <div className="p-4 sm:p-6 space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2"><LifeBuoy className="text-cyan-600" size={22} /><h2 className="text-xl font-black text-slate-800">Postventa — Tickets de servicio</h2></div>
        <button onClick={() => setNuevo({ asunto: '', descripcion: '', tipo: 'incidencia', prioridad: 'media', contactNombre: '', pedidoRef: '' })}
          className="flex items-center gap-1.5 px-4 py-2 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg font-bold text-sm"><Plus size={16} /> Nueva incidencia</button>
      </div>

      {/* KPIs */}
      {stats && (
        <div className="grid grid-cols-3 gap-3">
          <div className="bg-white rounded-xl border border-slate-200 p-3"><div className="text-2xl font-black text-slate-800">{stats.abiertos}</div><div className="text-xs text-slate-400 font-bold uppercase">Abiertos</div></div>
          <div className="bg-white rounded-xl border border-slate-200 p-3"><div className="text-2xl font-black text-red-600">{stats.vencidos}</div><div className="text-xs text-slate-400 font-bold uppercase">Vencidos SLA</div></div>
          <div className="bg-white rounded-xl border border-slate-200 p-3"><div className="text-2xl font-black text-slate-800">{stats.total}</div><div className="text-xs text-slate-400 font-bold uppercase">Total</div></div>
        </div>
      )}

      {/* Filtro */}
      <div className="flex gap-1.5 flex-wrap">
        <button onClick={() => setFiltro('')} className={`px-3 py-1 rounded-full text-xs font-bold ${!filtro ? 'bg-slate-800 text-white' : 'bg-slate-100 text-slate-600'}`}>Todos</button>
        {estados.map(e => <button key={e} onClick={() => setFiltro(e)} className={`px-3 py-1 rounded-full text-xs font-bold ${filtro === e ? 'bg-slate-800 text-white' : 'bg-slate-100 text-slate-600'}`}>{ESTADO_LABEL[e]}</button>)}
      </div>

      {/* Lista */}
      {cargando ? <div className="text-center py-8 text-slate-400"><Loader className="animate-spin inline" /></div> : (
        <div className="space-y-2">
          {!tickets.length && <p className="text-center text-slate-400 py-8 text-sm">No hay tickets{filtro ? ' en este estado' : ''}.</p>}
          {tickets.map(t => (
            <div key={t.id} onClick={() => setDetalle(t)} className="bg-white rounded-xl border border-slate-200 p-3 flex items-center justify-between gap-3 cursor-pointer hover:border-cyan-300 flex-wrap">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono text-slate-400">{t.numero}</span>
                  <span className={`text-[10px] font-black uppercase px-2 py-0.5 rounded-full ${ESTADO_COLOR[t.estado]}`}>{ESTADO_LABEL[t.estado]}</span>
                  <AlertTriangle size={13} className={PRIO_COLOR[t.prioridad]} title={`Prioridad ${t.prioridad}`} />
                  {t.vencido && <span className="text-[10px] font-black text-red-600 flex items-center gap-0.5"><Clock size={11} /> VENCIDO</span>}
                </div>
                <div className="font-bold text-slate-800 text-sm truncate">{t.asunto}</div>
                <div className="text-xs text-slate-400 truncate">{t.contactNombre || 'Sin cliente'}{t.pedidoRef ? ` · ${t.pedidoRef}` : ''} · SLA {fmt(t.slaVence)}</div>
              </div>
              <button onClick={(e) => { e.stopPropagation(); borrar(t); }} className="p-1.5 text-slate-300 hover:text-red-600"><Trash2 size={15} /></button>
            </div>
          ))}
        </div>
      )}

      {/* Alta */}
      {nuevo && (
        <div className="fixed inset-0 z-[60] bg-black/50 flex items-center justify-center p-3" onClick={() => setNuevo(null)}>
          <div className="bg-white rounded-2xl w-full max-w-lg p-5 space-y-3" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between"><h3 className="font-black text-slate-800">Nueva incidencia</h3><button onClick={() => setNuevo(null)}><X size={18} /></button></div>
            <input autoFocus value={nuevo.asunto} onChange={e => setNuevo({ ...nuevo, asunto: e.target.value })} placeholder="Asunto de la incidencia *" className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm" />
            <textarea value={nuevo.descripcion} onChange={e => setNuevo({ ...nuevo, descripcion: e.target.value })} rows={3} placeholder="Descripción" className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm" />
            <div className="grid grid-cols-2 gap-2">
              <select value={nuevo.tipo} onChange={e => setNuevo({ ...nuevo, tipo: e.target.value })} className="border border-slate-300 rounded-lg px-2 py-2 text-sm bg-white">{TIPOS.map(t => <option key={t.v} value={t.v}>{t.l}</option>)}</select>
              <select value={nuevo.prioridad} onChange={e => setNuevo({ ...nuevo, prioridad: e.target.value })} className="border border-slate-300 rounded-lg px-2 py-2 text-sm bg-white">{prioridades.map(p => <option key={p} value={p}>{p}</option>)}</select>
              <input value={nuevo.contactNombre} onChange={e => setNuevo({ ...nuevo, contactNombre: e.target.value })} placeholder="Cliente" className="border border-slate-300 rounded-lg px-3 py-2 text-sm" />
              <input value={nuevo.pedidoRef} onChange={e => setNuevo({ ...nuevo, pedidoRef: e.target.value })} placeholder="Ref. pedido" className="border border-slate-300 rounded-lg px-3 py-2 text-sm" />
            </div>
            <button onClick={crear} disabled={!nuevo.asunto?.trim()} className="w-full py-2 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg font-bold text-sm disabled:opacity-50">Crear ticket</button>
          </div>
        </div>
      )}

      {/* Detalle */}
      {detalle && (
        <div className="fixed inset-0 z-[60] bg-black/50 flex items-center justify-center p-3" onClick={() => setDetalle(null)}>
          <div className="bg-white rounded-2xl w-full max-w-xl max-h-[92vh] flex flex-col overflow-hidden" onClick={e => e.stopPropagation()}>
            <div className="px-5 py-3.5 bg-slate-800 text-white flex items-center justify-between">
              <div><span className="text-xs font-mono text-slate-300">{detalle.numero}</span><h3 className="font-black">{detalle.asunto}</h3></div>
              <button onClick={() => setDetalle(null)}><X size={18} /></button>
            </div>
            <div className="p-5 overflow-y-auto space-y-3">
              {detalle.descripcion && <p className="text-sm text-slate-600 whitespace-pre-wrap">{detalle.descripcion}</p>}
              <div className="grid grid-cols-2 gap-2">
                <label className="text-xs font-bold text-slate-500">Estado
                  <select value={detalle.estado} onChange={e => cambiar(detalle, { estado: e.target.value })} className="w-full mt-0.5 border border-slate-300 rounded-lg px-2 py-1.5 text-sm bg-white">
                    {estados.map(e => <option key={e} value={e}>{ESTADO_LABEL[e]}</option>)}
                  </select>
                </label>
                <label className="text-xs font-bold text-slate-500">Prioridad
                  <select value={detalle.prioridad} onChange={e => cambiar(detalle, { prioridad: e.target.value })} className="w-full mt-0.5 border border-slate-300 rounded-lg px-2 py-1.5 text-sm bg-white">
                    {prioridades.map(p => <option key={p} value={p}>{p}</option>)}
                  </select>
                </label>
              </div>
              <div className="text-xs text-slate-400">{detalle.contactNombre || 'Sin cliente'}{detalle.pedidoRef ? ` · ${detalle.pedidoRef}` : ''} · creado {fmt(detalle.createdAt)} · SLA {fmt(detalle.slaVence)}</div>

              {/* Comentarios */}
              <div className="border-t border-slate-100 pt-3">
                <div className="flex items-center gap-1.5 text-slate-500 text-xs font-bold mb-2"><MessageSquare size={13} /> Seguimiento</div>
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {(detalle.comentarios || []).map(c => (
                    <div key={c.id} className="bg-slate-50 rounded-lg px-3 py-1.5"><div className="text-sm text-slate-700">{c.texto}</div><div className="text-[10px] text-slate-400">{c.autor} · {fmt(c.fecha)}</div></div>
                  ))}
                  {!(detalle.comentarios || []).length && <p className="text-xs text-slate-400">Sin comentarios.</p>}
                </div>
                <div className="flex gap-2 mt-2">
                  <input value={coment} onChange={e => setComent(e.target.value)} onKeyDown={e => { if (e.key === 'Enter') comentar(); }} placeholder="Añadir comentario…" className="flex-1 border border-slate-300 rounded-lg px-3 py-1.5 text-sm" />
                  <button onClick={comentar} className="px-3 py-1.5 bg-slate-700 text-white rounded-lg"><Send size={15} /></button>
                </div>
              </div>
              {(detalle.estado === 'resuelto' || detalle.estado === 'cerrado') && (
                <div className="flex items-center gap-1.5 text-emerald-600 text-sm font-bold"><CheckCircle size={16} /> Incidencia {ESTADO_LABEL[detalle.estado].toLowerCase()}</div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
