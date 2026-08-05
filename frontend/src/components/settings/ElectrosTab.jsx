/*
 * © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * ElectrosTab — Catálogo de electrodomésticos (Artículos → Electros)
 * El COSTE solo lo ve el master (isPrimaryAdmin). El resto de usuarios ve el
 * PVP (precio de venta al público). Si un electro no tiene PVP, no se muestra
 * precio. Los datos viven en la colección article_costs (campos pvp, marca,
 * categoria, esElectro). El coste = tarifa proveedor con su descuento.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { Search, Save, RefreshCw, Plus, Zap, Eye, EyeOff, Wand2, Trash2, Package, LayoutGrid, X, Check } from 'lucide-react';
import { authHeaders } from '../../services/api';

const BASE = process.env.REACT_APP_BACKEND_URL;
const eur = (n) => `${(Number(n) || 0).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} €`;

export default function ElectrosTab({ isMaster = false, isAdmin = false }) {
  const [view, setView] = useState('catalogo'); // 'catalogo' | 'bodegones'
  const [items, setItems] = useState([]);
  const [q, setQ] = useState('');
  const [marca, setMarca] = useState('');
  const [loading, setLoading] = useState(false);
  const [edits, setEdits] = useState({}); // codigoNorm -> { pvp, marca, categoria }
  const [savingCode, setSavingCode] = useState('');
  const [revealed, setRevealed] = useState({}); // codigoNorm -> true (coste revelado)
  const [nuevo, setNuevo] = useState({ codigo: '', nombre: '', marca: '', costeUnitario: '', pvp: '' });

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set('electros', 'true');
      if (q.trim()) params.set('q', q.trim());
      params.set('limit', '3000');
      const r = await fetch(`${BASE}/api/rentabilidad/article-costs?${params.toString()}`, { headers: authHeaders() });
      const data = await r.json();
      setItems(data.items || []);
      setEdits({});
    } catch { /* noop */ }
    finally { setLoading(false); }
  }, [q]);

  useEffect(() => { load(); }, [load]);

  const setEdit = (code, field, val) => setEdits(prev => ({ ...prev, [code]: { ...(prev[code] || {}), [field]: val } }));

  const guardar = async (art) => {
    const code = art.codigoNorm || art.codigo;
    const ed = edits[code] || {};
    const payload = {
      codigo: art.codigo,
      nombre: art.nombre,
      costeUnitario: art.costeUnitario,
      cantidad: art.cantidad,
      costeTotal: art.costeTotal,
      esElectro: true,
      pvp: ed.pvp !== undefined ? String(ed.pvp).replace(',', '.') : art.pvp,
      marca: ed.marca !== undefined ? ed.marca : art.marca,
      categoria: ed.categoria !== undefined ? ed.categoria : art.categoria,
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
    } catch { alert('Error al guardar'); }
    finally { setSavingCode(''); }
  };

  const detectar = async () => {
    if (!window.confirm('Auto-detectar electrodomésticos del catálogo por palabras clave (campana, combi, lavadora, placa, microondas, lavavajillas, frigo, horno…) y marcarlos como electros. ¿Continuar?')) return;
    try {
      const r = await fetch(`${BASE}/api/rentabilidad/article-costs/tag-electros`, {
        method: 'POST', headers: { ...authHeaders(), 'Content-Type': 'application/json' }, body: '{}',
      });
      const data = await r.json();
      if (!data.success) { alert(data.detail || 'No se pudo detectar'); return; }
      alert(`${data.tagged} electrodomésticos marcados.`);
      await load();
    } catch { alert('Error al detectar electros'); }
  };

  const cargarSiemens = async () => {
    if (!window.confirm('Cargar los 7 electros Siemens (coste = precio neto, PVP = coste + 10%). ¿Continuar?')) return;
    try {
      const r = await fetch(`${BASE}/api/rentabilidad/electros/seed-siemens`, {
        method: 'POST', headers: { ...authHeaders(), 'Content-Type': 'application/json' }, body: '{}',
      });
      const data = await r.json().catch(() => ({}));
      if (!r.ok || !data.success) { alert(data.detail || 'No se pudieron cargar'); return; }
      alert(`${data.cargados} electros Siemens cargados.`);
      await load();
    } catch { alert('Error al cargar los electros Siemens'); }
  };

  const quitarElectro = async (art) => {
    if (!window.confirm(`Quitar ${art.codigo} de Electros (no se borra del catálogo de costes).`)) return;
    try {
      await fetch(`${BASE}/api/rentabilidad/article-costs`, {
        method: 'POST', headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ codigo: art.codigo, nombre: art.nombre, costeUnitario: art.costeUnitario, esElectro: false }),
      });
      await load();
    } catch { alert('Error'); }
  };

  const crear = async () => {
    if (!nuevo.codigo.trim()) { alert('Indica el código'); return; }
    try {
      const r = await fetch(`${BASE}/api/rentabilidad/article-costs`, {
        method: 'POST', headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({
          codigo: nuevo.codigo.trim(), nombre: nuevo.nombre.trim(), marca: nuevo.marca.trim(),
          costeUnitario: String(nuevo.costeUnitario).replace(',', '.'),
          pvp: String(nuevo.pvp).replace(',', '.'), esElectro: true, source: 'manual',
        }),
      });
      const data = await r.json();
      if (!data.success) { alert(data.detail || 'No se pudo crear'); return; }
      setNuevo({ codigo: '', nombre: '', marca: '', costeUnitario: '', pvp: '' });
      await load();
    } catch { alert('Error al crear'); }
  };

  // ---- Bodegones ----
  const [bodegones, setBodegones] = useState([]);
  const [assign, setAssign] = useState(null); // bodegón en edición de artículos { ...bodegon, sel:Set }
  const [assignQ, setAssignQ] = useState('');

  const loadBodegones = useCallback(async () => {
    try {
      const r = await fetch(`${BASE}/api/rentabilidad/bodegones`, { headers: authHeaders() });
      const data = await r.json();
      setBodegones(data.items || []);
    } catch { /* noop */ }
  }, []);
  useEffect(() => { if (view === 'bodegones') loadBodegones(); }, [view, loadBodegones]);

  const crearBodegon = async (tipo) => {
    const nombre = window.prompt(tipo === 'oferta' ? 'Nombre de la oferta:' : 'Nombre del bodegón:', tipo === 'oferta' ? 'Oferta' : 'Bodegón');
    if (!nombre) return;
    try {
      await fetch(`${BASE}/api/rentabilidad/bodegones`, {
        method: 'POST', headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ nombre, tipo }),
      });
      await loadBodegones();
    } catch { alert('Error al crear el bodegón'); }
  };

  const borrarBodegon = async (b) => {
    if (!window.confirm(`¿Eliminar «${b.nombre}»? (no borra los artículos del catálogo)`)) return;
    try {
      await fetch(`${BASE}/api/rentabilidad/bodegones/${encodeURIComponent(b.id)}`, { method: 'DELETE', headers: authHeaders() });
      await loadBodegones();
    } catch { alert('Error'); }
  };

  const abrirAsignar = (b) => setAssign({ ...b, sel: new Set((b.articulos || []).map(a => a.codigoNorm)) });
  const toggleSel = (code) => setAssign(prev => {
    const s = new Set(prev.sel);
    if (s.has(code)) s.delete(code); else s.add(code);
    return { ...prev, sel: s };
  });
  const guardarAsignacion = async () => {
    try {
      await fetch(`${BASE}/api/rentabilidad/bodegones`, {
        method: 'POST', headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: assign.id, nombre: assign.nombre, tipo: assign.tipo, articleCodes: Array.from(assign.sel) }),
      });
      setAssign(null);
      await loadBodegones();
    } catch { alert('Error al guardar la asignación'); }
  };

  const marcas = Array.from(new Set(items.map(i => (i.marca || '').trim()).filter(Boolean))).sort();
  const shown = marca ? items.filter(i => (i.marca || '') === marca) : items;
  const margen = (art) => {
    const c = Number(art.costeUnitario) || 0, p = Number(edits[art.codigoNorm]?.pvp ?? art.pvp) || 0;
    if (!c || !p) return null;
    return Math.round((p - c) / c * 100);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h3 className="text-lg font-black text-slate-800 flex items-center gap-2"><Zap size={18} className="text-amber-500" /> Electros</h3>
          <p className="text-sm text-slate-500">
            Catálogo de electrodomésticos · {items.length} artículos.{' '}
            {isMaster ? 'Como master ves el coste.' : 'El coste solo lo ve el master; tú gestionas el PVP.'}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {isAdmin && (
            <button onClick={detectar} className="px-3 py-2 bg-amber-50 text-amber-700 hover:bg-amber-100 rounded-lg text-xs font-bold flex items-center gap-1.5">
              <Wand2 size={14} /> Detectar electros
            </button>
          )}
          {isMaster && (
            <button onClick={cargarSiemens} className="px-3 py-2 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 rounded-lg text-xs font-bold flex items-center gap-1.5">
              <Plus size={14} /> Cargar 7 Siemens
            </button>
          )}
          <button onClick={load} className="px-3 py-2 bg-slate-100 hover:bg-slate-200 rounded-lg"><RefreshCw size={16} className={loading ? 'animate-spin' : ''} /></button>
        </div>
      </div>

      {/* Conmutador Catálogo / Bodegones */}
      <div className="inline-flex rounded-xl bg-slate-100 p-1 text-xs font-black">
        <button onClick={() => setView('catalogo')} className={`px-4 py-2 rounded-lg flex items-center gap-1.5 ${view === 'catalogo' ? 'bg-white shadow text-slate-800' : 'text-slate-500'}`}><LayoutGrid size={14} /> Catálogo</button>
        <button onClick={() => setView('bodegones')} className={`px-4 py-2 rounded-lg flex items-center gap-1.5 ${view === 'bodegones' ? 'bg-white shadow text-slate-800' : 'text-slate-500'}`}><Package size={14} /> Bodegones</button>
      </div>

      {view === 'catalogo' && (<>
      {/* Buscador + filtro marca */}
      <div className="flex items-center gap-2 flex-wrap">
        <div className="relative flex-1 min-w-[220px]">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input value={q} onChange={e => setQ(e.target.value)} placeholder="Buscar por código o nombre…" className="w-full pl-9 pr-3 py-2 border border-slate-200 rounded-lg text-sm" />
        </div>
        <select value={marca} onChange={e => setMarca(e.target.value)} className="px-3 py-2 border border-slate-200 rounded-lg text-sm">
          <option value="">Todas las marcas</option>
          {marcas.map(m => <option key={m} value={m}>{m}</option>)}
        </select>
      </div>

      {/* Alta rápida (admin) */}
      {isAdmin && (
        <div className="flex items-center gap-2 flex-wrap bg-slate-50 border border-slate-200 rounded-xl p-3">
          <input value={nuevo.codigo} onChange={e => setNuevo({ ...nuevo, codigo: e.target.value })} placeholder="Código" className="px-2 py-1.5 border rounded-lg text-sm w-32" />
          <input value={nuevo.nombre} onChange={e => setNuevo({ ...nuevo, nombre: e.target.value })} placeholder="Nombre" className="px-2 py-1.5 border rounded-lg text-sm flex-1 min-w-[140px]" />
          <input value={nuevo.marca} onChange={e => setNuevo({ ...nuevo, marca: e.target.value })} placeholder="Marca" className="px-2 py-1.5 border rounded-lg text-sm w-28" />
          {isMaster && <input value={nuevo.costeUnitario} onChange={e => setNuevo({ ...nuevo, costeUnitario: e.target.value })} placeholder="Coste €" className="px-2 py-1.5 border rounded-lg text-sm w-24" />}
          <input value={nuevo.pvp} onChange={e => setNuevo({ ...nuevo, pvp: e.target.value })} placeholder="PVP €" className="px-2 py-1.5 border rounded-lg text-sm w-24" />
          <button onClick={crear} className="px-3 py-1.5 bg-emerald-600 text-white hover:bg-emerald-700 rounded-lg text-xs font-bold flex items-center gap-1"><Plus size={14} /> Añadir</button>
        </div>
      )}

      {/* Tabla */}
      <div className="border border-slate-200 rounded-xl overflow-hidden">
        <div className="max-h-[520px] overflow-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-100 text-slate-500 sticky top-0">
              <tr>
                <th className="text-left p-2 text-[10px] font-black uppercase">Código</th>
                <th className="text-left p-2 text-[10px] font-black uppercase">Nombre</th>
                <th className="text-left p-2 text-[10px] font-black uppercase">Marca</th>
                {isMaster && <th className="text-right p-2 text-[10px] font-black uppercase">Coste</th>}
                {isMaster && <th className="text-right p-2 text-[10px] font-black uppercase">Margen</th>}
                <th className="text-right p-2 text-[10px] font-black uppercase">PVP</th>
                {isAdmin && <th className="p-2"></th>}
              </tr>
            </thead>
            <tbody>
              {shown.map(art => {
                const code = art.codigoNorm || art.codigo;
                const ed = edits[code] || {};
                const dirty = ed.pvp !== undefined || ed.marca !== undefined || ed.categoria !== undefined;
                const mg = margen(art);
                return (
                  <tr key={code} className="border-t border-slate-100 hover:bg-slate-50">
                    <td className="p-2 font-mono text-xs font-bold text-slate-700">{art.codigo}</td>
                    <td className="p-2 text-xs text-slate-700">{art.nombre}</td>
                    <td className="p-2">
                      {isAdmin ? (
                        <input value={ed.marca !== undefined ? ed.marca : (art.marca || '')} onChange={e => setEdit(code, 'marca', e.target.value)}
                          className="w-24 px-1.5 py-1 border border-transparent hover:border-slate-200 focus:border-indigo-400 rounded text-xs" placeholder="—" />
                      ) : <span className="text-xs text-slate-500">{art.marca || '—'}</span>}
                    </td>
                    {isMaster && (
                      <td className="p-2 text-right whitespace-nowrap">
                        {revealed[code]
                          ? <span className="text-xs font-bold text-slate-700">{art.costeUnitario != null ? eur(art.costeUnitario) : '—'} <button onClick={() => setRevealed(p => ({ ...p, [code]: false }))} className="ml-1 text-slate-400"><EyeOff size={12} className="inline" /></button></span>
                          : <button onClick={() => setRevealed(p => ({ ...p, [code]: true }))} className="px-2 py-1 rounded text-[11px] bg-slate-100 hover:bg-slate-200 text-slate-600 font-bold inline-flex items-center gap-1"><Eye size={12} /> Coste</button>}
                      </td>
                    )}
                    {isMaster && (
                      <td className="p-2 text-right text-xs font-bold">
                        {mg == null ? <span className="text-slate-300">—</span> : <span className={mg > 0 ? 'text-emerald-600' : 'text-red-600'}>{mg}%</span>}
                      </td>
                    )}
                    <td className="p-2 text-right">
                      {isAdmin ? (
                        <input value={ed.pvp !== undefined ? ed.pvp : (art.pvp ?? '')} onChange={e => setEdit(code, 'pvp', e.target.value)}
                          className="w-24 px-1.5 py-1 border border-slate-200 focus:border-indigo-400 rounded text-xs text-right font-bold" placeholder="PVP" />
                      ) : (
                        art.pvp > 0 ? <span className="text-xs font-bold text-slate-800">{eur(art.pvp)}</span> : <span className="text-[11px] text-slate-400">sin precio</span>
                      )}
                    </td>
                    {isAdmin && (
                      <td className="p-2 whitespace-nowrap">
                        <button onClick={() => guardar(art)} disabled={!dirty || savingCode === code}
                          className={`px-2 py-1 rounded text-xs font-bold ${dirty ? 'bg-indigo-600 text-white hover:bg-indigo-700' : 'bg-slate-100 text-slate-400'}`}><Save size={13} /></button>
                        <button onClick={() => quitarElectro(art)} title="Quitar de Electros" className="px-2 py-1 ml-1 rounded text-xs bg-red-50 text-red-600 hover:bg-red-100"><Trash2 size={13} /></button>
                      </td>
                    )}
                  </tr>
                );
              })}
              {shown.length === 0 && !loading && (
                <tr><td colSpan={isMaster ? 7 : 4} className="p-6 text-center text-slate-400 text-sm">
                  Sin electros. {isAdmin ? 'Usa «Detectar electros» para marcar los del catálogo o añade uno nuevo.' : 'Aún no hay electrodomésticos.'}
                </td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
      </>)}

      {view === 'bodegones' && (
        <div className="space-y-4">
          {isAdmin && (
            <div className="flex items-center gap-2">
              <button onClick={() => crearBodegon('bodegon')} className="px-3 py-2 bg-emerald-600 text-white hover:bg-emerald-700 rounded-lg text-xs font-bold flex items-center gap-1.5"><Plus size={14} /> Nuevo bodegón</button>
              <button onClick={() => crearBodegon('oferta')} className="px-3 py-2 bg-amber-600 text-white hover:bg-amber-700 rounded-lg text-xs font-bold flex items-center gap-1.5"><Plus size={14} /> Nueva oferta</button>
              <span className="text-xs text-slate-400">Un artículo puede estar en varios bodegones.</span>
            </div>
          )}
          {bodegones.length === 0 && (
            <p className="text-sm text-slate-400 text-center py-8">No hay bodegones. {isAdmin ? 'Crea uno y asígnale artículos.' : ''}</p>
          )}
          <div className="grid gap-4 md:grid-cols-2">
            {bodegones.map(b => (
              <div key={b.id} className="border border-slate-200 rounded-xl overflow-hidden">
                <div className={`flex items-center justify-between px-4 py-3 ${b.tipo === 'oferta' ? 'bg-amber-50' : 'bg-slate-50'}`}>
                  <div>
                    <div className="font-black text-slate-800 text-sm flex items-center gap-2">
                      {b.nombre}
                      <span className={`px-1.5 py-0.5 rounded text-[9px] uppercase ${b.tipo === 'oferta' ? 'bg-amber-200 text-amber-800' : 'bg-slate-200 text-slate-600'}`}>{b.tipo === 'oferta' ? 'Oferta' : 'Bodegón'}</span>
                    </div>
                    <div className="text-[11px] text-slate-500">{b.nArts} artículos{b.tipo === 'bodegon' ? ` · ${b.conPvp} con PVP` : ' · valores individuales'}</div>
                  </div>
                  {isAdmin && (
                    <div className="flex items-center gap-1">
                      <button onClick={() => abrirAsignar(b)} className="px-2.5 py-1.5 bg-indigo-600 text-white rounded-lg text-[11px] font-bold hover:bg-indigo-700">Asignar artículos</button>
                      <button onClick={() => borrarBodegon(b)} className="p-1.5 text-red-400 hover:text-red-600 hover:bg-red-50 rounded-lg"><Trash2 size={14} /></button>
                    </div>
                  )}
                </div>
                <div className="p-3 space-y-1.5">
                  {(b.articulos || []).length === 0 ? (
                    <p className="text-xs text-slate-400 py-2">Sin artículos asignados.</p>
                  ) : b.articulos.map(a => (
                    <div key={a.codigoNorm} className="flex items-center justify-between gap-2 text-xs border-b border-slate-50 pb-1.5">
                      <div className="min-w-0">
                        <div className="font-bold text-slate-700 truncate">{a.nombre}</div>
                        <div className="text-[10px] text-slate-400 font-mono">{a.codigo}{a.marca ? ` · ${a.marca}` : ''}</div>
                      </div>
                      <div className="text-right whitespace-nowrap">
                        {a.pvp > 0 ? <span className="font-bold text-slate-800">{eur(a.pvp)}</span> : <span className="text-slate-400">sin PVP</span>}
                        {isMaster && a.costeUnitario != null && <span className="ml-2 text-[10px] text-slate-400">(coste {eur(a.costeUnitario)})</span>}
                      </div>
                    </div>
                  ))}
                </div>
                {b.tipo === 'bodegon' && (
                  <div className="flex items-center justify-between px-4 py-3 bg-slate-800 text-white">
                    <span className="text-xs font-bold uppercase tracking-wide">Total PVP</span>
                    <span className="font-black">{b.conPvp > 0 ? `${eur(b.totalPvp)} · ${b.conPvp}/${b.nArts}` : '—'}</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Modal asignar artículos a un bodegón */}
      {assign && (
        <div className="fixed inset-0 bg-black/40 z-[60] flex items-center justify-center p-4" onClick={() => setAssign(null)}>
          <div className="bg-white rounded-2xl w-full max-w-lg max-h-[85vh] flex flex-col overflow-hidden" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
              <div>
                <h4 className="font-black text-slate-800">Asignar artículos · {assign.nombre}</h4>
                <p className="text-[11px] text-slate-500">{assign.sel.size} seleccionados</p>
              </div>
              <button onClick={() => setAssign(null)} className="text-slate-400 hover:text-slate-600"><X size={18} /></button>
            </div>
            <div className="px-4 pt-3">
              <div className="relative">
                <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input value={assignQ} onChange={e => setAssignQ(e.target.value)} placeholder="Filtrar electros…" className="w-full pl-9 pr-3 py-2 border border-slate-200 rounded-lg text-sm" />
              </div>
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-1">
              {items.filter(a => {
                const s = assignQ.trim().toLowerCase();
                return !s || `${a.codigo} ${a.nombre} ${a.marca || ''}`.toLowerCase().includes(s);
              }).map(a => {
                const code = a.codigoNorm || a.codigo;
                const on = assign.sel.has(code);
                return (
                  <button key={code} onClick={() => toggleSel(code)}
                    className={`w-full flex items-center gap-2 text-left px-3 py-2 rounded-lg border text-xs ${on ? 'border-indigo-400 bg-indigo-50' : 'border-slate-200 hover:bg-slate-50'}`}>
                    <span className={`w-4 h-4 rounded flex items-center justify-center ${on ? 'bg-indigo-600 text-white' : 'border border-slate-300'}`}>{on && <Check size={12} />}</span>
                    <span className="flex-1 min-w-0">
                      <span className="font-bold text-slate-700 block truncate">{a.nombre}</span>
                      <span className="text-[10px] text-slate-400 font-mono">{a.codigo}{a.marca ? ` · ${a.marca}` : ''}</span>
                    </span>
                    <span className="text-slate-500 whitespace-nowrap">{a.pvp > 0 ? eur(a.pvp) : 'sin PVP'}</span>
                  </button>
                );
              })}
              {items.length === 0 && <p className="text-sm text-slate-400 text-center py-6">No hay electros en el catálogo.</p>}
            </div>
            <div className="flex items-center justify-end gap-2 px-5 py-3 border-t border-slate-100">
              <button onClick={() => setAssign(null)} className="px-3 py-2 text-xs font-bold text-slate-500 hover:text-slate-700">Cancelar</button>
              <button onClick={guardarAsignacion} className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-xs font-bold hover:bg-indigo-700 flex items-center gap-1.5"><Save size={14} /> Guardar</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
