/*
 * © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * GestionGastos - Gastos de comerciales (estilo Tiquelia)
 * Escanea un ticket -> la IA detecta el tipo de gasto e importes -> editable.
 * Permite marcar tickets y generar INFORMES de cierre (mensual de dietas, etc.).
 * Cada comercial ve y gestiona SUS gastos.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { Sparkles, Trash2, X, Plus, RefreshCw, Wallet, Receipt, FileText, Printer, CheckSquare, Square } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const eur = (n) => (Number(n) || 0).toLocaleString('es-ES', { style: 'currency', currency: 'EUR' });

const TIPOS = {
  dieta: 'Dieta / Comida',
  combustible: 'Combustible / Gasoil',
  peaje: 'Peaje',
  parking: 'Parking',
  alojamiento: 'Alojamiento / Hotel',
  transporte: 'Transporte',
  material: 'Material / Oficina',
  representacion: 'Representación',
  otros: 'Otros',
};
const TIPO_COLOR = {
  dieta: 'bg-orange-100 text-orange-700',
  combustible: 'bg-red-100 text-red-700',
  peaje: 'bg-amber-100 text-amber-700',
  parking: 'bg-cyan-100 text-cyan-700',
  alojamiento: 'bg-purple-100 text-purple-700',
  transporte: 'bg-blue-100 text-blue-700',
  material: 'bg-slate-100 text-slate-700',
  representacion: 'bg-pink-100 text-pink-700',
  otros: 'bg-slate-100 text-slate-600',
};

const GestionGastos = ({ currentUser }) => {
  const [tab, setTab] = useState('tickets'); // 'tickets' | 'informes'
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [byType, setByType] = useState({});
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [review, setReview] = useState(null);
  const [saving, setSaving] = useState(false);
  const [mes, setMes] = useState('');
  const [selected, setSelected] = useState(() => new Set());
  const [informes, setInformes] = useState([]);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const qs = new URLSearchParams();
      if (currentUser?.id) qs.append('userId', currentUser.id);
      if (mes) qs.append('mes', mes);
      const r = await fetch(`${API_URL}/api/gastos?${qs.toString()}`);
      if (r.ok) { const j = await r.json(); setItems(j.items || []); setTotal(j.total || 0); setByType(j.byType || {}); }
      const qi = new URLSearchParams();
      if (currentUser?.id) qi.append('userId', currentUser.id);
      const ri = await fetch(`${API_URL}/api/gastos/informes?${qi.toString()}`);
      if (ri.ok) { const ji = await ri.json(); setInformes(ji.items || []); }
    } catch { /* noop */ } finally { setLoading(false); }
  }, [currentUser, mes]);

  useEffect(() => { load(); }, [load]);

  const handleFile = async (e) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;
    setScanning(true);
    try {
      const b64 = await new Promise((res, rej) => {
        const fr = new FileReader();
        fr.onload = () => res(fr.result);
        fr.onerror = rej;
        fr.readAsDataURL(file);
      });
      const r = await fetch(`${API_URL}/api/gastos/scan`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fileBase64: b64 }),
      });
      const j = await r.json();
      if (!j.success) { alert('No se pudo leer el ticket: ' + (j.error || '')); return; }
      setReview({ ...j.data, fileB64: b64, fileName: file.name, fileMime: file.type || 'application/octet-stream' });
    } catch (err) {
      alert('Error al escanear el ticket: ' + err.message);
    } finally { setScanning(false); }
  };

  const saveReview = async () => {
    if (!review) return;
    if (!review.importe || Number(review.importe) <= 0) { alert('Indica el importe'); return; }
    setSaving(true);
    try {
      const r = await fetch(`${API_URL}/api/gastos`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          tipo: review.tipo, importe: review.importe, base: review.base, iva: review.iva,
          fecha: review.fecha, proveedor: review.proveedor, descripcion: review.descripcion, litros: review.litros,
          docBase64: review.fileB64, docName: review.fileName, docMime: review.fileMime,
          userId: currentUser?.id, userName: currentUser?.clientName || currentUser?.username,
        }),
      });
      if (!r.ok) throw new Error('Error al guardar');
      setReview(null);
      await load();
    } catch (e) { alert('No se pudo guardar el gasto: ' + e.message); }
    finally { setSaving(false); }
  };

  const changeTipo = async (g, tipo) => {
    try {
      await fetch(`${API_URL}/api/gastos/${g.id}`, {
        method: 'PUT', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tipo }),
      });
      await load();
    } catch { alert('No se pudo cambiar el tipo'); }
  };

  const delGasto = async (id) => {
    if (!window.confirm('¿Eliminar este gasto?')) return;
    await fetch(`${API_URL}/api/gastos/${id}`, { method: 'DELETE' });
    load();
  };

  const verDoc = async (docId) => {
    try {
      const r = await fetch(`${API_URL}/api/gastos/doc/${docId}`);
      if (!r.ok) throw new Error();
      const d = await r.json();
      const w = window.open();
      if (w) w.document.write(`<iframe src="data:${d.mime};base64,${d.dataBase64}" style="width:100%;height:100%;border:0"></iframe>`);
    } catch { alert('No se pudo abrir el ticket'); }
  };

  // ── Selección de tickets para el informe ──
  const toggleSel = (id) => setSelected(prev => {
    const n = new Set(prev);
    n.has(id) ? n.delete(id) : n.add(id);
    return n;
  });
  const allSelected = items.length > 0 && items.every(g => selected.has(g.id));
  const toggleAll = () => setSelected(allSelected ? new Set() : new Set(items.map(g => g.id)));
  const selectedItems = items.filter(g => selected.has(g.id));
  const selectedTotal = selectedItems.reduce((s, g) => s + (Number(g.importe) || 0), 0);

  const crearInforme = async () => {
    if (selected.size === 0) { alert('Marca al menos un ticket'); return; }
    const nombre = window.prompt('Nombre del informe (ej: "Dietas Junio 2026"):', mes ? `Gastos ${mes}` : 'Cierre de gastos');
    if (!nombre) return;
    try {
      const r = await fetch(`${API_URL}/api/gastos/informes`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          nombre, gastoIds: Array.from(selected),
          userId: currentUser?.id, userName: currentUser?.clientName || currentUser?.username,
        }),
      });
      const j = await r.json();
      if (!r.ok) throw new Error(j.detail || 'Error');
      setSelected(new Set());
      await load();
      setTab('informes');
      alert('Informe creado: ' + (j.informe?.nombre || ''));
    } catch (e) { alert('No se pudo crear el informe: ' + e.message); }
  };

  const delInforme = async (id) => {
    if (!window.confirm('¿Eliminar este informe? Los tickets volverán a quedar disponibles.')) return;
    await fetch(`${API_URL}/api/gastos/informes/${id}`, { method: 'DELETE' });
    load();
  };

  const imprimirInforme = async (informeId) => {
    try {
      const r = await fetch(`${API_URL}/api/gastos/informes/${informeId}`);
      if (!r.ok) throw new Error();
      const inf = await r.json();
      const rows = (inf.gastos || []).map(g => `
        <tr>
          <td>${g.fecha || ''}</td>
          <td>${TIPOS[g.tipo] || g.tipo || ''}</td>
          <td>${(g.proveedor || '').replace(/</g, '&lt;')}</td>
          <td>${(g.descripcion || '').replace(/</g, '&lt;')}</td>
          <td style="text-align:right">${eur(g.importe)}</td>
        </tr>`).join('');
      const desglose = Object.entries(inf.byType || {}).map(([t, v]) =>
        `<tr><td colspan="4">${TIPOS[t] || t}</td><td style="text-align:right">${eur(v)}</td></tr>`).join('');
      const w = window.open();
      if (!w) { alert('Permite las ventanas emergentes para imprimir'); return; }
      w.document.write(`<!doctype html><html><head><meta charset="utf-8"><title>${inf.nombre}</title>
        <style>body{font-family:Arial,Helvetica,sans-serif;color:#1e293b;padding:24px}
        h1{font-size:20px;margin:0 0 2px} .sub{color:#64748b;font-size:12px;margin-bottom:16px}
        table{width:100%;border-collapse:collapse;font-size:12px;margin-top:8px}
        th,td{border-bottom:1px solid #e2e8f0;padding:6px 8px;text-align:left}
        th{background:#f1f5f9;text-transform:uppercase;font-size:10px}
        .tot{font-weight:800;font-size:14px} .box{margin-top:18px}
        </style></head><body>
        <h1>${inf.nombre}</h1>
        <div class="sub">Comercial: ${inf.userName || ''} · ${inf.numTickets || (inf.gastos||[]).length} tickets · ${inf.fechaDesde || ''} a ${inf.fechaHasta || ''}</div>
        <table><thead><tr><th>Fecha</th><th>Tipo</th><th>Proveedor</th><th>Descripción</th><th style="text-align:right">Importe</th></tr></thead>
        <tbody>${rows}</tbody></table>
        <div class="box"><table><thead><tr><th colspan="5">Resumen por tipo</th></tr></thead><tbody>${desglose}
        <tr class="tot"><td colspan="4">TOTAL</td><td style="text-align:right">${eur(inf.total)}</td></tr></tbody></table></div>
        </body></html>`);
      w.document.close();
      setTimeout(() => { try { w.print(); } catch (_) {} }, 400);
    } catch { alert('No se pudo abrir el informe'); }
  };

  return (
    <div className="p-4 sm:p-6 max-w-6xl mx-auto">
      <div className="hueco-logo-centrado flex items-center justify-between mb-5 flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-indigo-600 rounded-2xl flex items-center justify-center text-white"><Wallet size={24} /></div>
          <div>
            <h1 className="text-2xl font-black text-slate-900 uppercase">Gastos de Comercial</h1>
            <p className="text-sm text-slate-500">Escanea tickets y genera informes de cierre</p>
          </div>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          {tab === 'tickets' && <input type="month" value={mes} onChange={e => setMes(e.target.value)} className="px-3 py-2 border border-slate-200 rounded-xl text-sm" title="Filtrar por mes" />}
          <label className={`px-4 py-2 rounded-xl font-bold text-sm flex items-center gap-2 cursor-pointer ${scanning ? 'bg-purple-200 text-purple-500' : 'bg-purple-600 text-white hover:bg-purple-700'}`}>
            <Sparkles size={16} className={scanning ? 'animate-pulse' : ''} />
            {scanning ? 'Leyendo ticket…' : 'Escanear ticket (IA)'}
            <input type="file" accept="image/*,application/pdf" className="hidden" onChange={handleFile} disabled={scanning} />
          </label>
          <button onClick={load} className="px-4 py-2 bg-slate-100 hover:bg-slate-200 rounded-xl font-bold text-sm flex items-center gap-2">
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} /> Actualizar
          </button>
        </div>
      </div>

      {/* Pestañas */}
      <div className="flex gap-2 mb-5">
        <button onClick={() => setTab('tickets')} className={`px-4 py-2 rounded-xl font-bold text-sm ${tab === 'tickets' ? 'bg-slate-800 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}>Tickets</button>
        <button onClick={() => setTab('informes')} className={`px-4 py-2 rounded-xl font-bold text-sm flex items-center gap-2 ${tab === 'informes' ? 'bg-slate-800 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}><FileText size={15} /> Informes ({informes.length})</button>
      </div>

      {tab === 'tickets' && (<>
        {/* Totales */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
          <div className="bg-indigo-600 text-white p-4 rounded-2xl col-span-2 md:col-span-1">
            <p className="text-[10px] uppercase opacity-80">Total gastos</p>
            <p className="text-2xl font-black">{eur(total)}</p>
            <p className="text-[11px] opacity-80">{items.length} ticket(s)</p>
          </div>
          {Object.entries(byType).sort((a, b) => b[1] - a[1]).slice(0, 3).map(([t, v]) => (
            <div key={t} className="bg-white border border-slate-200 p-4 rounded-2xl">
              <p className="text-[10px] uppercase text-slate-400 font-bold">{TIPOS[t] || t}</p>
              <p className="text-xl font-black text-slate-800">{eur(v)}</p>
            </div>
          ))}
        </div>

        {/* Barra de selección → crear informe */}
        {selected.size > 0 && (
          <div className="flex items-center justify-between gap-3 bg-indigo-50 border border-indigo-200 rounded-xl px-4 py-2.5 mb-3 flex-wrap">
            <span className="text-sm font-bold text-indigo-800">{selected.size} ticket(s) marcados · {eur(selectedTotal)}</span>
            <div className="flex items-center gap-2">
              <button onClick={() => setSelected(new Set())} className="px-3 py-1.5 text-sm font-bold text-slate-500 hover:text-slate-700">Quitar selección</button>
              <button onClick={crearInforme} className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-bold flex items-center gap-2"><FileText size={15} /> Crear informe de gastos</button>
            </div>
          </div>
        )}

        <div className="bg-white border border-slate-200 rounded-2xl overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-100 text-slate-600">
              <tr>
                <th className="p-3 w-10 text-center">
                  <button onClick={toggleAll} title="Marcar todos">{allSelected ? <CheckSquare size={16} className="text-indigo-600" /> : <Square size={16} className="text-slate-400" />}</button>
                </th>
                <th className="text-left p-3 text-xs font-black uppercase">Fecha</th>
                <th className="text-left p-3 text-xs font-black uppercase">Tipo</th>
                <th className="text-left p-3 text-xs font-black uppercase">Proveedor</th>
                <th className="text-left p-3 text-xs font-black uppercase">Descripción</th>
                <th className="text-center p-3 text-xs font-black uppercase">Ticket</th>
                <th className="text-right p-3 text-xs font-black uppercase">Importe</th>
                <th className="p-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {items.map((g) => (
                <tr key={g.id} className={`hover:bg-slate-50 ${selected.has(g.id) ? 'bg-indigo-50/50' : ''}`}>
                  <td className="p-3 text-center">
                    <button onClick={() => toggleSel(g.id)}>{selected.has(g.id) ? <CheckSquare size={16} className="text-indigo-600" /> : <Square size={16} className="text-slate-300" />}</button>
                  </td>
                  <td className="p-3 text-slate-500 whitespace-nowrap">{g.fecha || '—'}</td>
                  <td className="p-3">
                    <select value={g.tipo || 'otros'} onChange={e => changeTipo(g, e.target.value)}
                      className={`px-2 py-1 rounded-lg text-[11px] font-black border-0 cursor-pointer ${TIPO_COLOR[g.tipo] || TIPO_COLOR.otros}`}>
                      {Object.entries(TIPOS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                    </select>
                    {g.informeNombre && <div className="text-[9px] text-slate-400 mt-0.5">en: {g.informeNombre}</div>}
                  </td>
                  <td className="p-3 text-slate-700">{g.proveedor || '—'}</td>
                  <td className="p-3 text-slate-500 text-xs">{g.descripcion || '—'}</td>
                  <td className="p-3 text-center">
                    {g.docId ? <button onClick={() => verDoc(g.docId)} title="Ver ticket" className="text-slate-500 hover:text-indigo-600">🧾</button> : <span className="text-slate-300">—</span>}
                  </td>
                  <td className="p-3 text-right font-mono font-black text-slate-800 whitespace-nowrap">{eur(g.importe)}</td>
                  <td className="p-3 text-right"><button onClick={() => delGasto(g.id)} className="text-slate-300 hover:text-red-500"><Trash2 size={15} /></button></td>
                </tr>
              ))}
              {items.length === 0 && (
                <tr><td colSpan={8} className="p-8 text-center text-slate-400">{loading ? 'Cargando…' : 'Sin gastos. Escanea un ticket y la IA lo clasificará.'}</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </>)}

      {tab === 'informes' && (
        <div className="bg-white border border-slate-200 rounded-2xl overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-100 text-slate-600">
              <tr>
                <th className="text-left p-3 text-xs font-black uppercase">Informe</th>
                <th className="text-left p-3 text-xs font-black uppercase">Periodo</th>
                <th className="text-center p-3 text-xs font-black uppercase">Tickets</th>
                <th className="text-right p-3 text-xs font-black uppercase">Total</th>
                <th className="p-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {informes.map((inf) => (
                <tr key={inf.id} className="hover:bg-slate-50">
                  <td className="p-3 font-bold text-indigo-700">{inf.nombre}</td>
                  <td className="p-3 text-slate-500 text-xs">{inf.fechaDesde || '—'} → {inf.fechaHasta || '—'}</td>
                  <td className="p-3 text-center">{inf.numTickets || (inf.gastoIds || []).length}</td>
                  <td className="p-3 text-right font-mono font-black text-slate-800">{eur(inf.total)}</td>
                  <td className="p-3 text-right whitespace-nowrap">
                    <button onClick={() => imprimirInforme(inf.id)} title="Ver / Imprimir" className="mr-2 px-2.5 py-1 bg-indigo-600 text-white rounded-lg text-[11px] font-bold hover:bg-indigo-700 inline-flex items-center gap-1"><Printer size={13} /> Imprimir</button>
                    <button onClick={() => delInforme(inf.id)} className="text-slate-300 hover:text-red-500"><Trash2 size={15} /></button>
                  </td>
                </tr>
              ))}
              {informes.length === 0 && (
                <tr><td colSpan={5} className="p-8 text-center text-slate-400">Sin informes. Marca tickets en la pestaña "Tickets" y pulsa "Crear informe de gastos".</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal de revisión del ticket escaneado */}
      {review && (
        <div className="fixed inset-0 bg-black/60 z-[130] flex items-center justify-center p-4" onClick={() => setReview(null)}>
          <div className="bg-white rounded-3xl w-full max-w-lg max-h-[92vh] overflow-auto" onClick={e => e.stopPropagation()}>
            <div className="bg-purple-600 text-white px-6 py-4 flex justify-between items-center">
              <h2 className="text-lg font-black flex items-center gap-2"><Receipt size={18} /> Ticket escaneado — revisa y ajusta</h2>
              <button onClick={() => setReview(null)} className="p-2 hover:bg-white/20 rounded-xl"><X size={20} /></button>
            </div>
            <div className="p-6 space-y-3">
              <div>
                <label className="text-[10px] font-black text-slate-400 uppercase block mb-1">Tipo de gasto</label>
                <select value={review.tipo} onChange={e => setReview({ ...review, tipo: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg text-sm font-bold">
                  {Object.entries(TIPOS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div><label className="text-[10px] font-black text-slate-400 uppercase block mb-1">Importe €</label>
                  <input type="number" step="0.01" value={review.importe} onChange={e => setReview({ ...review, importe: parseFloat(e.target.value) || 0 })} className="w-full px-3 py-2 border rounded-lg text-sm text-right font-bold" /></div>
                <div><label className="text-[10px] font-black text-slate-400 uppercase block mb-1">Fecha</label>
                  <input value={review.fecha} onChange={e => setReview({ ...review, fecha: e.target.value })} className="w-full px-3 py-2 border rounded-lg text-sm" /></div>
                <div><label className="text-[10px] font-black text-slate-400 uppercase block mb-1">Base €</label>
                  <input type="number" step="0.01" value={review.base} onChange={e => setReview({ ...review, base: parseFloat(e.target.value) || 0 })} className="w-full px-3 py-2 border rounded-lg text-sm text-right" /></div>
                <div><label className="text-[10px] font-black text-slate-400 uppercase block mb-1">IVA €</label>
                  <input type="number" step="0.01" value={review.iva} onChange={e => setReview({ ...review, iva: parseFloat(e.target.value) || 0 })} className="w-full px-3 py-2 border rounded-lg text-sm text-right" /></div>
              </div>
              <div><label className="text-[10px] font-black text-slate-400 uppercase block mb-1">Proveedor / Establecimiento</label>
                <input value={review.proveedor} onChange={e => setReview({ ...review, proveedor: e.target.value })} className="w-full px-3 py-2 border rounded-lg text-sm" /></div>
              <div><label className="text-[10px] font-black text-slate-400 uppercase block mb-1">Descripción</label>
                <input value={review.descripcion} onChange={e => setReview({ ...review, descripcion: e.target.value })} className="w-full px-3 py-2 border rounded-lg text-sm" /></div>
              <button onClick={saveReview} disabled={saving} className="w-full py-3 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white rounded-xl font-black uppercase text-sm flex items-center justify-center gap-2">
                <Plus size={16} /> {saving ? 'Guardando…' : 'Registrar gasto'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default GestionGastos;
