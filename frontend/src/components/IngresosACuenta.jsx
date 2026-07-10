/**
 * IngresosACuenta - Localiza por IA los ingresos a cuenta (anticipos del cliente)
 * a partir de un documento (PDF/imagen) y los registra. Cada usuario ve los suyos.
 */
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Sparkles, Trash2, X, Plus, RefreshCw, Banknote, UserPlus, Link2 } from 'lucide-react';
import { clientsAPI } from '../services/api';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const eur = (n) => (Number(n) || 0).toLocaleString('es-ES', { style: 'currency', currency: 'EUR' });
// Mismo criterio que se usa para pintar la etiqueta "PENDIENTE DE ASIGNACIÓN" en la fila.
const isPendiente = (i) => !i.targetRef && (i.pendiente || (!i.clientCode && !i.cliente));

const IngresosACuenta = ({ currentUser }) => {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  // Los ingresos ya vinculados a una FACTURA se consideran cobrados: salen de la
  // lista (la factura los refleja como Pagada) y se pueden ver con el toggle.
  const [verFacturados, setVerFacturados] = useState(false);
  const facturados = items.filter(i => i.targetType === 'factura');
  const [loading, setLoading] = useState(true);
  const [importing, setImporting] = useState(false);
  const [review, setReview] = useState(null); // { cliente, clientCode, proyecto, ingresos: [], targetId, fileB64, fileName, fileMime }
  const [saving, setSaving] = useState(false);
  const [asignables, setAsignables] = useState([]); // presupuestos/pedidos/facturas a los que asignar
  const [clients, setClients] = useState([]); // clientes a los que asignar directamente
  const [assign, setAssign] = useState(null); // { id, targetId, clientCode }
  const [assigning, setAssigning] = useState(false);

  const pendientes = useMemo(() => {
    const rows = items.filter(isPendiente);
    return { count: rows.length, total: rows.reduce((s, i) => s + (Number(i.importe) || 0), 0) };
  }, [items]);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const elevated = currentUser?.isAdmin || currentUser?.isGerente
        || currentUser?.isDirectorComercial || currentUser?.isResponsableDelegacion
        || currentUser?.isDirectorFabrica;
      const qs = (!elevated && currentUser?.id) ? `?userId=${encodeURIComponent(currentUser.id)}` : '';
      const r = await fetch(`${API_URL}/api/rentabilidad/ingresos${qs}`);
      if (r.ok) { const j = await r.json(); setItems(j.items || []); setTotal(j.total || 0); }
      const a = await fetch(`${API_URL}/api/rentabilidad/asignables${qs}`);
      if (a.ok) setAsignables(await a.json());
      const c = await clientsAPI.getAll(true).catch(() => []);
      setClients(c || []);
    } catch { /* noop */ } finally { setLoading(false); }
  }, [currentUser]);

  const verDoc = async (docId) => {
    try {
      const r = await fetch(`${API_URL}/api/rentabilidad/ingresos/doc/${docId}`);
      if (!r.ok) throw new Error();
      const d = await r.json();
      const w = window.open();
      if (w) w.document.write(`<iframe src="data:${d.mime};base64,${d.dataBase64}" style="width:100%;height:100%;border:0"></iframe>`);
    } catch { alert('No se pudo abrir el documento'); }
  };

  useEffect(() => { load(); }, [load]);

  const handleFile = async (e) => {
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
      const r = await fetch(`${API_URL}/api/rentabilidad/parse-ingresos`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fileBase64: b64 }),
      });
      const j = await r.json();
      if (!j.success) { alert('No se pudieron localizar ingresos: ' + (j.error || '')); return; }
      if (!(j.data.ingresos || []).length) { alert('La IA no encontró ingresos a cuenta en el documento.'); return; }
      setReview({
        cliente: j.data.cliente || '', clientCode: '', proyecto: j.data.proyecto || '', ingresos: j.data.ingresos,
        targetId: '', fileB64: b64, fileName: file.name, fileMime: file.type || 'application/octet-stream',
      });
    } catch (err) {
      alert('Error al leer el documento: ' + err.message);
    } finally { setImporting(false); }
  };

  const setRevLine = (i, field, val) => {
    const ingresos = [...review.ingresos];
    ingresos[i] = { ...ingresos[i], [field]: field === 'importe' ? (parseFloat(val) || 0) : val };
    setReview({ ...review, ingresos });
  };
  const removeRevLine = (i) => setReview({ ...review, ingresos: review.ingresos.filter((_, x) => x !== i) });

  const addManual = () => setReview({
    cliente: '', clientCode: '', proyecto: '',
    ingresos: [{ fecha: new Date().toISOString().slice(0, 10), importe: 0, concepto: 'Ingreso a cuenta', metodo: 'transferencia' }],
    targetId: '', fileB64: '', fileName: '', fileMime: '',
  });

  const createClientInline = async () => {
    const nombre = window.prompt('Nombre del cliente nuevo:');
    if (!nombre || !nombre.trim()) return;
    try {
      const created = await clientsAPI.create({ nombre: nombre.trim() });
      const codigo = created.codigo || created.code || '';
      const fresh = await clientsAPI.getAll(true).catch(() => []);
      setClients(fresh || []);
      if (codigo) setReview(r => ({ ...r, clientCode: codigo, cliente: r.cliente || nombre.trim() }));
    } catch (e) { alert('No se pudo crear el cliente: ' + e.message); }
  };

  const saveAll = async () => {
    if (!review?.ingresos?.length) { setReview(null); return; }
    const target = asignables.find(a => a.id === review.targetId);
    const client = clients.find(c => c.codigo === review.clientCode);
    // Si no se asigna ni a documento ni a cliente, queda PENDIENTE DE ASIGNACIÓN.
    const pendiente = !review.targetId && !review.clientCode;
    if (pendiente && !window.confirm('No has asignado este ingreso a ningún cliente ni documento.\n\n¿Guardarlo como PENDIENTE DE ASIGNACIÓN para asignarlo más tarde?')) return;
    setSaving(true);
    try {
      for (const ing of review.ingresos) {
        if (!ing.importe || Number(ing.importe) <= 0) continue;
        await fetch(`${API_URL}/api/rentabilidad/ingresos`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            ...ing, cliente: review.cliente || client?.nombre || '', proyecto: review.proyecto,
            clientCode: review.clientCode,
            targetId: review.targetId,
            targetType: target?.docType || '',
            targetRef: target?.ref || '',
            pendiente,
            docBase64: review.fileB64, docName: review.fileName, docMime: review.fileMime,
            createdBy: currentUser?.id, createdByName: currentUser?.clientName || currentUser?.username,
          }),
        });
      }
      setReview(null);
      await load();
    } catch (e) { alert('Error al registrar: ' + e.message); }
    finally { setSaving(false); }
  };

  const delIngreso = async (id) => {
    if (!window.confirm('¿Eliminar este ingreso a cuenta?')) return;
    await fetch(`${API_URL}/api/rentabilidad/ingresos/${id}`, { method: 'DELETE' });
    load();
  };

  // Asignar (o reasignar) despues un ingreso que quedo pendiente, sin borrarlo y recrearlo.
  const openAssign = (i) => setAssign({ id: i.id, targetId: i.targetId || '', clientCode: i.clientCode || '' });
  const doAssign = async () => {
    if (!assign.targetId && !assign.clientCode) { alert('Selecciona un cliente y/o un documento'); return; }
    setAssigning(true);
    try {
      const target = asignables.find(a => a.id === assign.targetId);
      const client = clients.find(c => c.codigo === assign.clientCode);
      const r = await fetch(`${API_URL}/api/rentabilidad/ingresos/${assign.id}`, {
        method: 'PATCH', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          targetId: assign.targetId, targetType: target?.docType || '', targetRef: target?.ref || '',
          clientCode: assign.clientCode, cliente: client?.nombre || '',
        }),
      });
      if (!r.ok) throw new Error();
      setAssign(null);
      await load();
    } catch { alert('No se pudo asignar el ingreso'); }
    finally { setAssigning(false); }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-5 flex-wrap gap-2">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 bg-teal-600 rounded-2xl flex items-center justify-center text-white"><Banknote size={22} /></div>
          <div>
            <h2 className="text-lg font-black text-slate-900 uppercase">Ingresos a cuenta</h2>
            <p className="text-xs text-slate-500">Anticipos del cliente localizados por IA desde un documento</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <label className={`px-4 py-2 rounded-xl font-bold text-sm flex items-center gap-2 cursor-pointer ${importing ? 'bg-purple-200 text-purple-500' : 'bg-purple-600 text-white hover:bg-purple-700'}`}>
            <Sparkles size={16} className={importing ? 'animate-pulse' : ''} />
            {importing ? 'Localizando…' : 'Localizar ingresos (IA)'}
            <input type="file" accept="image/*,application/pdf" className="hidden" onChange={handleFile} disabled={importing} />
          </label>
          <button onClick={addManual} className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-xl font-bold text-sm flex items-center gap-2">
            <Plus size={16} /> Registrar manual
          </button>
          <button onClick={load} className="px-4 py-2 bg-slate-100 hover:bg-slate-200 rounded-xl font-bold text-sm flex items-center gap-2">
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} /> Actualizar
          </button>
        </div>
      </div>

      <div className="flex flex-wrap gap-4 mb-5">
        <div className="bg-teal-600 text-white p-4 rounded-2xl inline-block min-w-[220px]">
          <p className="text-[10px] uppercase opacity-80">Total ingresos a cuenta</p>
          <p className="text-2xl font-black">{eur(total)}</p>
          <p className="text-[11px] opacity-80">{items.length} registro(s)</p>
        </div>
        {pendientes.count > 0 && (
          <div className="bg-orange-600 text-white p-4 rounded-2xl inline-block min-w-[220px]">
            <p className="text-[10px] uppercase opacity-80">Pendientes de asignar</p>
            <p className="text-2xl font-black">{eur(pendientes.total)}</p>
            <p className="text-[11px] opacity-80">{pendientes.count} registro(s) sin cliente ni documento</p>
          </div>
        )}
        {facturados.length > 0 && (
          <button onClick={() => setVerFacturados(v => !v)}
            className={`p-4 rounded-2xl inline-block min-w-[220px] text-left transition-colors ${verFacturados ? 'bg-blue-600 text-white' : 'bg-blue-50 text-blue-700 hover:bg-blue-100'}`}>
            <p className="text-[10px] uppercase opacity-80">Vinculados a factura (cobrados)</p>
            <p className="text-2xl font-black">{eur(facturados.reduce((s, i) => s + (Number(i.importe) || 0), 0))}</p>
            <p className="text-[11px] opacity-80">{facturados.length} registro(s) · {verFacturados ? 'ocultar' : 'ver'}</p>
          </button>
        )}
      </div>

      <div className="bg-white border border-slate-200 rounded-2xl overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-100 text-slate-600">
            <tr>
              <th className="text-left p-3 text-xs font-black uppercase">Fecha</th>
              <th className="text-left p-3 text-xs font-black uppercase">Cliente</th>
              <th className="text-left p-3 text-xs font-black uppercase">Proyecto</th>
              <th className="text-left p-3 text-xs font-black uppercase">Concepto</th>
              <th className="text-left p-3 text-xs font-black uppercase">Método</th>
              <th className="text-left p-3 text-xs font-black uppercase">Asignado a</th>
              <th className="text-center p-3 text-xs font-black uppercase">Doc</th>
              <th className="text-right p-3 text-xs font-black uppercase">Importe</th>
              <th className="p-3"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {(verFacturados ? items : items.filter(i => i.targetType !== 'factura')).map((i) => (
              <tr key={i.id} className="hover:bg-slate-50">
                <td className="p-3 text-slate-500">{i.fecha || '—'}</td>
                <td className="p-3 text-slate-700">
                  {i.cliente || '—'}
                  {i.clientCode && <span className="ml-1 px-1.5 py-0.5 bg-teal-100 text-teal-700 rounded text-[10px] font-black">{i.clientCode}</span>}
                </td>
                <td className="p-3 font-bold text-indigo-700">{i.projectRef || '—'}</td>
                <td className="p-3 text-slate-700">{i.concepto || '—'}</td>
                <td className="p-3 text-[11px] uppercase text-slate-500">{i.metodo || '—'}</td>
                <td className="p-3">
                  {i.targetRef ? (
                    <span className={`px-2 py-1 rounded-lg text-[11px] font-black ${i.targetType === 'factura' ? 'bg-blue-100 text-blue-700' : 'bg-amber-100 text-amber-700'}`}>
                      {(i.targetType || '').toUpperCase()} {i.targetRef}
                    </span>
                  ) : isPendiente(i) ? (
                    <div className="flex items-center gap-1.5">
                      <span className="px-2 py-1 rounded-lg text-[11px] font-black bg-orange-100 text-orange-700">PENDIENTE DE ASIGNACIÓN</span>
                      <button onClick={() => openAssign(i)} title="Asignar a un cliente o documento" className="px-2 py-1 bg-teal-600 hover:bg-teal-700 text-white rounded-lg text-[11px] font-bold flex items-center gap-1"><Link2 size={11} /> Asignar</button>
                    </div>
                  ) : <span className="text-slate-300">—</span>}
                </td>
                <td className="p-3 text-center">
                  {i.docId ? (
                    <button onClick={() => verDoc(i.docId)} title="Ver documento archivado" className="text-slate-500 hover:text-teal-600">📎</button>
                  ) : <span className="text-slate-300">—</span>}
                </td>
                <td className="p-3 text-right font-mono font-black text-teal-700">{eur(i.importe)}</td>
                <td className="p-3 text-right"><button onClick={() => delIngreso(i.id)} className="text-slate-300 hover:text-red-500"><Trash2 size={15} /></button></td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr><td colSpan={9} className="p-8 text-center text-slate-400">{loading ? 'Cargando…' : 'Sin ingresos a cuenta. Sube un documento y la IA los localizará.'}</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Modal de revisión de lo localizado por IA */}
      {review && (
        <div className="fixed inset-0 bg-black/60 z-[130] flex items-center justify-center p-4" onClick={() => setReview(null)}>
          <div className="bg-white rounded-3xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col" onClick={e => e.stopPropagation()}>
            <div className="bg-purple-600 text-white px-6 py-4 flex justify-between items-center">
              <h2 className="text-lg font-black flex items-center gap-2"><Sparkles size={18} /> Ingresos a cuenta localizados</h2>
              <button onClick={() => setReview(null)} className="p-2 hover:bg-white/20 rounded-xl"><X size={20} /></button>
            </div>
            <div className="p-6 overflow-auto space-y-3">
              <div className="grid grid-cols-2 gap-2">
                <div><label className="text-[10px] font-black text-slate-400 uppercase block mb-1">Nombre detectado (texto libre)</label>
                  <input value={review.cliente} onChange={e => setReview({ ...review, cliente: e.target.value })} className="w-full px-3 py-2 border rounded-lg text-sm" /></div>
                <div><label className="text-[10px] font-black text-slate-400 uppercase block mb-1">Proyecto / Expediente</label>
                  <input value={review.proyecto} onChange={e => setReview({ ...review, proyecto: e.target.value })} className="w-full px-3 py-2 border rounded-lg text-sm" /></div>
              </div>
              <p className="text-[11px] text-slate-400">Asigna el ingreso a un cliente final y/o a un presupuesto, pedido o factura (al menos uno).</p>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-[10px] font-black text-slate-400 uppercase block mb-1">Cliente final</label>
                  <div className="flex gap-1.5">
                    <select value={review.clientCode} onChange={e => setReview({ ...review, clientCode: e.target.value })}
                      className={`flex-1 px-3 py-2 border rounded-lg text-sm font-bold ${review.clientCode || review.targetId ? 'border-emerald-300' : 'border-red-300'}`}>
                      <option value="">— Sin cliente vinculado —</option>
                      {clients.map(c => (
                        <option key={c.codigo} value={c.codigo}>{c.codigo} · {c.nombre}</option>
                      ))}
                    </select>
                    <button type="button" onClick={createClientInline} title="Crear cliente nuevo"
                      className="px-2.5 bg-teal-600 hover:bg-teal-700 text-white rounded-lg"><UserPlus size={16} /></button>
                  </div>
                  {clients.length === 0 && (
                    <p className="text-[11px] text-amber-600 mt-1">Aún no hay clientes creados. Usa <UserPlus size={11} className="inline" /> para crear uno rápido.</p>
                  )}
                </div>
                <div>
                  <label className="text-[10px] font-black text-slate-400 uppercase block mb-1">Presupuesto / pedido / factura</label>
                  <select value={review.targetId} onChange={e => setReview({ ...review, targetId: e.target.value })}
                    className={`w-full px-3 py-2 border rounded-lg text-sm font-bold ${review.clientCode || review.targetId ? 'border-emerald-300' : 'border-red-300'}`}>
                    <option value="">— Sin documento vinculado —</option>
                    {asignables.map(a => (
                      <option key={a.id} value={a.id}>{(a.docType || '').toUpperCase()} · {a.ref || '(sin ref)'} · {a.cliente || ''}</option>
                    ))}
                  </select>
                  {asignables.length === 0 && (
                    <p className="text-[11px] text-amber-600 mt-1">No hay presupuestos/pedidos/facturas aún.</p>
                  )}
                </div>
              </div>
              <table className="w-full text-sm">
                <thead className="text-slate-500"><tr>
                  <th className="text-left p-2 text-xs uppercase">Fecha</th>
                  <th className="text-left p-2 text-xs uppercase">Concepto</th>
                  <th className="text-left p-2 text-xs uppercase">Método</th>
                  <th className="text-right p-2 text-xs uppercase">Importe</th><th></th>
                </tr></thead>
                <tbody className="divide-y divide-slate-100">
                  {review.ingresos.map((ing, i) => (
                    <tr key={i}>
                      <td className="p-1"><input value={ing.fecha} onChange={e => setRevLine(i, 'fecha', e.target.value)} className="w-28 px-2 py-1 border rounded text-sm" /></td>
                      <td className="p-1"><input value={ing.concepto} onChange={e => setRevLine(i, 'concepto', e.target.value)} className="w-full px-2 py-1 border rounded text-sm" /></td>
                      <td className="p-1">
                        <select value={ing.metodo} onChange={e => setRevLine(i, 'metodo', e.target.value)} className="px-2 py-1 border rounded text-sm">
                          {['transferencia', 'efectivo', 'tarjeta', 'otro'].map(m => <option key={m} value={m}>{m}</option>)}
                        </select>
                      </td>
                      <td className="p-1"><input type="number" step="0.01" value={ing.importe} onChange={e => setRevLine(i, 'importe', e.target.value)} className="w-24 px-2 py-1 border rounded text-sm text-right font-bold" /></td>
                      <td className="p-1 text-right"><button onClick={() => removeRevLine(i)} className="text-slate-300 hover:text-red-500"><Trash2 size={14} /></button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <button onClick={saveAll} disabled={saving} className="w-full py-3 bg-teal-600 hover:bg-teal-700 disabled:bg-teal-400 text-white rounded-xl font-black uppercase text-sm flex items-center justify-center gap-2">
                <Plus size={16} /> {saving ? 'Registrando…' : `Registrar ${review.ingresos.length} ingreso(s)`}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: asignar despues un ingreso pendiente (sin borrar y recrear) */}
      {assign && (
        <div className="fixed inset-0 bg-black/60 z-[130] flex items-center justify-center p-4" onClick={() => !assigning && setAssign(null)}>
          <div className="bg-white rounded-2xl w-full max-w-md overflow-hidden" onClick={e => e.stopPropagation()}>
            <div className="bg-teal-600 text-white px-5 py-3 flex items-center justify-between">
              <h3 className="font-black text-sm uppercase flex items-center gap-2"><Link2 size={16} /> Asignar ingreso</h3>
              <button onClick={() => setAssign(null)} className="p-1.5 hover:bg-white/20 rounded-lg"><X size={18} /></button>
            </div>
            <div className="p-5 space-y-3">
              <div>
                <label className="text-[10px] font-black text-slate-400 uppercase block mb-1">Cliente final</label>
                <select value={assign.clientCode} onChange={e => setAssign({ ...assign, clientCode: e.target.value })} className="w-full px-3 py-2 border rounded-lg text-sm font-bold">
                  <option value="">— Sin cliente vinculado —</option>
                  {clients.map(c => <option key={c.codigo} value={c.codigo}>{c.codigo} · {c.nombre}</option>)}
                </select>
              </div>
              <div>
                <label className="text-[10px] font-black text-slate-400 uppercase block mb-1">Presupuesto / pedido / factura</label>
                <select value={assign.targetId} onChange={e => setAssign({ ...assign, targetId: e.target.value })} className="w-full px-3 py-2 border rounded-lg text-sm font-bold">
                  <option value="">— Sin documento vinculado —</option>
                  {asignables.map(a => <option key={a.id} value={a.id}>{(a.docType || '').toUpperCase()} · {a.ref || '(sin ref)'} · {a.cliente || ''}</option>)}
                </select>
              </div>
              <button onClick={doAssign} disabled={assigning} className="w-full py-2.5 bg-teal-600 hover:bg-teal-700 disabled:opacity-50 text-white rounded-xl font-black text-sm">
                {assigning ? 'Asignando…' : 'Guardar asignación'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default IngresosACuenta;
