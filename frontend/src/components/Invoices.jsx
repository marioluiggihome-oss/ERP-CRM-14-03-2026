/*
 * © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
import React, { useState, useEffect } from 'react';
import {
  FileText, Plus, Download, Send, CheckCircle, XCircle, Clock,
  Euro, Search, Loader2, Trash2, Edit2, X, Save, AlertTriangle,
  ArrowUpRight, Receipt, Filter, Copy, Users
} from 'lucide-react';
import { invoicesAPI, clientsAPI } from '../services/api';

const STATUS_CONFIG = {
  draft:     { label: 'Borrador',  color: 'bg-slate-100 text-slate-600',   icon: FileText },
  issued:    { label: 'Emitida',   color: 'bg-blue-100 text-blue-700',     icon: Send },
  paid:      { label: 'Pagada',    color: 'bg-green-100 text-green-700',   icon: CheckCircle },
  overdue:   { label: 'Vencida',   color: 'bg-red-100 text-red-700',       icon: AlertTriangle },
  cancelled: { label: 'Cancelada', color: 'bg-slate-100 text-slate-400',   icon: XCircle },
};

const fmt = (v) => new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR' }).format(v || 0);
const fmtDate = (d) => d ? new Date(d).toLocaleDateString('es-ES') : '—';

const EMPTY_FORM = {
  clientName: '', clientEmail: '', clientAddress: '', clientTaxId: '',
  invoiceNumber: '', issueDate: new Date().toISOString().split('T')[0],
  dueDate: new Date(Date.now() + 30*864e5).toISOString().split('T')[0],
  vatRate: 21, irpfRate: 0, notes: '', status: 'draft',
  lines: [{ description: '', quantity: 1, unitPrice: 0, discount: 0, vatRate: 21 }]
};

const Invoices = ({ currentUser }) => {
  const [invoices, setInvoices] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [sendingEmail, setSendingEmail] = useState(null);
  const [loadError, setLoadError] = useState(false);

  useEffect(() => { load(); }, [statusFilter]);

  const load = async () => {
    setLoading(true);
    let failed = false;
    try {
      const [invs, st] = await Promise.all([
        invoicesAPI.getAll(statusFilter || null).catch(() => { failed = true; return []; }),
        invoicesAPI.getStats().catch(() => ({ monthTotal:0, pendingTotal:0, issued:0, paid:0, overdue:0 }))
      ]);
      setInvoices(Array.isArray(invs) ? invs : []);
      setStats(st || {});
      setLoadError(failed);
    } catch (e) {
      console.error('Invoices load error:', e);
      setInvoices([]);
      setLoadError(true);
    }
    finally { setLoading(false); }
  };

  const openNew = async () => {
    const { nextNumber } = await invoicesAPI.getNextNumber();
    setForm({ ...EMPTY_FORM, invoiceNumber: nextNumber });
    setEditingId(null);
    setShowModal(true);
  };

  const openEdit = (inv) => {
    setForm({
      clientName: inv.clientName || '', clientEmail: inv.clientEmail || '',
      clientAddress: inv.clientAddress || '', clientTaxId: inv.clientTaxId || '',
      invoiceNumber: inv.invoiceNumber || '', issueDate: inv.issueDate || '',
      dueDate: inv.dueDate || '', vatRate: inv.vatRate || 21, irpfRate: inv.irpfRate || 0,
      notes: inv.notes || '', status: inv.status || 'draft',
      lines: inv.lines?.length ? inv.lines : EMPTY_FORM.lines
    });
    setEditingId(inv.id);
    setShowModal(true);
  };

  // Duplicar factura (como en Holded): copia datos y líneas como nuevo borrador.
  const duplicateInvoice = async (inv) => {
    let nextNumber = '';
    try { nextNumber = (await invoicesAPI.getNextNumber())?.nextNumber || ''; } catch { /* */ }
    const today = new Date().toISOString().split('T')[0];
    setForm({
      clientName: inv.clientName || '', clientEmail: inv.clientEmail || '',
      clientAddress: inv.clientAddress || '', clientTaxId: inv.clientTaxId || '',
      invoiceNumber: nextNumber, issueDate: today,
      dueDate: new Date(Date.now() + 30 * 864e5).toISOString().split('T')[0],
      vatRate: inv.vatRate || 21, irpfRate: inv.irpfRate || 0, notes: inv.notes || '', status: 'draft',
      lines: inv.lines?.length ? inv.lines.map(l => ({ ...l })) : EMPTY_FORM.lines,
    });
    setEditingId(null);
    setShowModal(true);
  };

  // Cargar cliente desde los clientes importados (rellena los datos de la factura).
  const [clientPicker, setClientPicker] = useState(false);
  const [clientList, setClientList] = useState([]);
  const [clientQ, setClientQ] = useState('');
  const openClientPicker = async () => {
    setClientPicker(true);
    try { setClientList(await clientsAPI.getAll(true) || []); } catch { setClientList([]); }
  };
  const pickClient = (c) => {
    setForm(f => ({
      ...f,
      clientName: c.nombre || f.clientName,
      clientTaxId: c.cif || c.nif || c.codigo || f.clientTaxId,
      clientEmail: c.email || f.clientEmail,
      clientAddress: c.direccion || f.clientAddress,
    }));
    setClientPicker(false);
  };

  // Totales desglosados (base imponible, IVA, total) — estilo Holded.
  const totalsBreakdown = () => {
    let base = 0, vat = 0;
    (form.lines || []).forEach(l => {
      const net = (l.quantity || 0) * (l.unitPrice || 0) * (1 - (l.discount || 0) / 100);
      base += net; vat += net * ((l.vatRate ?? 21) / 100);
    });
    const irpf = base * ((Number(form.irpfRate) || 0) / 100);
    return { base, vat, irpf, total: base + vat - irpf };
  };

  const handleSave = async () => {
    if (!form.clientName) { alert('El nombre del cliente es obligatorio'); return; }
    if (!form.lines.some(l => l.description && l.unitPrice > 0)) { alert('Añade al menos una línea con descripción e importe'); return; }
    setSaving(true);
    try {
      if (editingId) {
        await invoicesAPI.update(editingId, form);
      } else {
        await invoicesAPI.create(form);
      }
      setShowModal(false);
      load();
    } catch (e) { alert(e.message); }
    finally { setSaving(false); }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('¿Eliminar esta factura?')) return;
    await invoicesAPI.delete(id);
    load();
  };

  const handleStatus = async (inv, status) => {
    try { await invoicesAPI.changeStatus(inv.id, status); load(); }
    catch (e) { alert(e.message); }
  };

  const handleSendEmail = async (inv) => {
    const email = inv.clientEmail || window.prompt('Email del cliente:');
    if (!email) return;
    setSendingEmail(inv.id);
    try {
      await invoicesAPI.sendEmail(inv.id, email);
      alert(`✅ Factura enviada a ${email}`);
      load();
    } catch (e) { alert(e.message); }
    finally { setSendingEmail(null); }
  };

  const addLine = () => setForm(f => ({ ...f, lines: [...f.lines, { description: '', quantity: 1, unitPrice: 0, discount: 0, vatRate: 21 }] }));
  const removeLine = (i) => setForm(f => ({ ...f, lines: f.lines.filter((_, idx) => idx !== i) }));
  const updateLine = (i, field, value) => setForm(f => ({ ...f, lines: f.lines.map((l, idx) => idx === i ? { ...l, [field]: value } : l) }));

  const calcTotal = () => {
    return form.lines.reduce((sum, l) => {
      const net = (l.quantity || 0) * (l.unitPrice || 0) * (1 - (l.discount || 0) / 100);
      return sum + net * (1 + (l.vatRate || 21) / 100);
    }, 0);
  };

  const filtered = invoices.filter(inv =>
    !search || inv.invoiceNumber?.toLowerCase().includes(search.toLowerCase()) ||
    inv.clientName?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="h-full flex flex-col bg-slate-50">
      {/* Header */}
      <div className="hueco-logo bg-white border-b border-slate-100 px-4 sm:px-6 py-4">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-orange-500 rounded-xl shadow">
              <Receipt className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-black text-slate-900 uppercase">Facturación</h2>
              <p className="text-[10px] font-bold text-slate-400 uppercase">{invoices.length} facturas</p>
            </div>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)}
              className="px-3 py-2 bg-white border border-slate-200 rounded-xl text-xs font-bold outline-none">
              <option value="">Todos los estados</option>
              {Object.entries(STATUS_CONFIG).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
            </select>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-300 w-4 h-4" />
              <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Buscar..."
                className="pl-9 pr-4 py-2 border border-slate-200 rounded-xl text-xs font-bold outline-none w-48" />
            </div>
            <button onClick={openNew}
              className="flex items-center gap-2 px-4 py-2 bg-orange-500 text-white rounded-xl font-black text-xs hover:bg-orange-600 transition-all shadow">
              <Plus className="w-4 h-4" /> Nueva Factura
            </button>
          </div>
        </div>

        {/* Stats */}
        {stats && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4">
            {[
              { label: 'Este mes', value: fmt(stats.monthTotal), color: 'text-indigo-600' },
              { label: 'Pendiente cobro', value: fmt(stats.pendingTotal), color: 'text-orange-600' },
              { label: 'Vencido', value: fmt(invoices.filter(x => x.status === 'issued' && x.dueDate && new Date(x.dueDate) < new Date()).reduce((s, x) => s + (x.total || 0), 0)), color: 'text-red-600' },
              { label: 'Pagadas', value: stats.paid, color: 'text-green-600' },
            ].map((s, i) => (
              <div key={i} className="bg-slate-50 rounded-xl p-3 border border-slate-100">
                <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest">{s.label}</p>
                <p className={`text-lg font-black ${s.color} mt-0.5`}>{s.value}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Lista */}
      <div className="flex-1 overflow-auto p-4 sm:p-6">
        {loading ? (
          <div className="flex items-center justify-center h-40">
            <Loader2 className="w-8 h-8 text-orange-400 animate-spin" />
          </div>
        ) : loadError ? (
          <div className="flex flex-col items-center justify-center h-48 text-center">
            <AlertTriangle className="w-12 h-12 text-amber-400 mb-3" />
            <p className="font-black text-slate-700 text-sm uppercase">No se pudieron cargar las facturas</p>
            <p className="text-xs text-slate-400 mt-2 max-w-sm">
              No hay conexión con el servidor. Comprueba que el backend está en marcha y que
              <span className="font-mono"> REACT_APP_BACKEND_URL</span> está configurado.
            </p>
            <button onClick={load} className="mt-4 px-4 py-2 bg-orange-500 text-white rounded-xl text-xs font-black">Reintentar</button>
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-40 text-slate-300">
            <Receipt className="w-12 h-12 mb-2" />
            <p className="font-black text-slate-400">Sin facturas</p>
            <p className="text-xs text-slate-300 mt-1">Crea tu primera factura</p>
          </div>
        ) : (
          <div className="space-y-3">
            {filtered.map(inv => {
              const cfg = STATUS_CONFIG[inv.status] || STATUS_CONFIG.draft;
              const Icon = cfg.icon;
              const isOverdue = inv.status === 'issued' && inv.dueDate && new Date(inv.dueDate) < new Date();
              return (
                <div key={inv.id} className={`bg-white rounded-2xl shadow-sm border transition-all hover:shadow-md ${isOverdue ? 'border-red-200' : 'border-slate-100'}`}>
                  <div className="p-4 flex items-center gap-4 flex-wrap">
                    {/* Número y cliente */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1 flex-wrap">
                        <span className="font-black text-slate-900 text-sm">{inv.invoiceNumber}</span>
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-lg text-[9px] font-black uppercase ${cfg.color}`}>
                          <Icon className="w-2.5 h-2.5" /> {cfg.label}
                        </span>
                        {isOverdue && <span className="text-[9px] font-black text-red-600 bg-red-50 px-2 py-0.5 rounded-lg">VENCIDA</span>}
                        {inv.sentAt && <span className="text-[9px] font-black text-slate-400 bg-slate-50 px-2 py-0.5 rounded-lg">Enviada</span>}
                      </div>
                      <p className="font-bold text-slate-700 text-sm truncate">{inv.clientName}</p>
                      <div className="flex gap-4 mt-1">
                        <span className="text-[10px] text-slate-400">Emisión: {fmtDate(inv.issueDate)}</span>
                        <span className={`text-[10px] font-bold ${isOverdue ? 'text-red-500' : 'text-slate-400'}`}>Vence: {fmtDate(inv.dueDate)}</span>
                        {inv.budgetNumber && <span className="text-[10px] text-indigo-400">Pres: {inv.budgetNumber}</span>}
                      </div>
                    </div>

                    {/* Total */}
                    <div className="text-right flex-shrink-0">
                      <p className="text-xl font-black text-slate-900">{fmt(inv.total)}</p>
                      <p className="text-[10px] text-slate-400">IVA {fmt(inv.totalVat)}</p>
                    </div>

                    {/* Acciones */}
                    <div className="flex items-center gap-1.5 flex-shrink-0">
                      <button onClick={() => invoicesAPI.downloadPdf(inv.id)}
                        className="p-2 bg-slate-50 text-slate-600 rounded-xl hover:bg-slate-100 transition-all" title="Descargar PDF">
                        <Download className="w-4 h-4" />
                      </button>
                      <button onClick={() => handleSendEmail(inv)} disabled={sendingEmail === inv.id}
                        className="p-2 bg-blue-50 text-blue-600 rounded-xl hover:bg-blue-100 transition-all" title="Enviar por email">
                        {sendingEmail === inv.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                      </button>
                      {inv.status === 'draft' && (
                        <button onClick={() => handleStatus(inv, 'issued')}
                          className="p-2 bg-orange-50 text-orange-600 rounded-xl hover:bg-orange-100 transition-all" title="Emitir factura">
                          <ArrowUpRight className="w-4 h-4" />
                        </button>
                      )}
                      {inv.status === 'issued' && (
                        <button onClick={() => handleStatus(inv, 'paid')}
                          className="p-2 bg-green-50 text-green-600 rounded-xl hover:bg-green-100 transition-all" title="Marcar como pagada">
                          <CheckCircle className="w-4 h-4" />
                        </button>
                      )}
                      <button onClick={() => duplicateInvoice(inv)}
                        className="p-2 bg-slate-50 text-slate-600 rounded-xl hover:bg-slate-100 transition-all" title="Duplicar factura">
                        <Copy className="w-4 h-4" />
                      </button>
                      <button onClick={() => openEdit(inv)}
                        className="p-2 bg-indigo-50 text-indigo-600 rounded-xl hover:bg-indigo-100 transition-all" title="Editar">
                        <Edit2 className="w-4 h-4" />
                      </button>
                      <button onClick={() => handleDelete(inv.id)}
                        className="p-2 bg-red-50 text-red-500 rounded-xl hover:bg-red-100 transition-all" title="Eliminar">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Modal crear/editar */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-end sm:items-center justify-center z-50 p-0 sm:p-4">
          <div className="bg-white rounded-t-3xl sm:rounded-2xl shadow-2xl w-full sm:max-w-2xl max-h-[95vh] flex flex-col">
            {/* Modal header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
              <h3 className="font-black text-slate-900 uppercase text-sm">
                {editingId ? 'Editar Factura' : 'Nueva Factura'}
              </h3>
              <button onClick={() => setShowModal(false)} className="p-2 hover:bg-slate-100 rounded-xl">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-6 space-y-5">
              {/* Número y fechas */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="text-[10px] font-black text-slate-400 uppercase">Nº Factura</label>
                  <input value={form.invoiceNumber} onChange={e => setForm(f => ({ ...f, invoiceNumber: e.target.value }))}
                    className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-xl text-sm font-bold outline-none focus:border-orange-400" />
                </div>
                <div>
                  <label className="text-[10px] font-black text-slate-400 uppercase">Fecha Emisión</label>
                  <input type="date" value={form.issueDate} onChange={e => setForm(f => ({ ...f, issueDate: e.target.value }))}
                    className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-xl text-sm font-bold outline-none focus:border-orange-400" />
                </div>
                <div>
                  <label className="text-[10px] font-black text-slate-400 uppercase">Vencimiento</label>
                  <input type="date" value={form.dueDate} onChange={e => setForm(f => ({ ...f, dueDate: e.target.value }))}
                    className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-xl text-sm font-bold outline-none focus:border-orange-400" />
                </div>
              </div>

              {/* Cliente */}
              <div className="bg-slate-50 rounded-2xl p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <p className="text-[10px] font-black text-slate-400 uppercase">Datos del Cliente</p>
                  <button onClick={openClientPicker} type="button" className="flex items-center gap-1 text-[10px] font-black text-indigo-600 hover:text-indigo-700"><Users className="w-3.5 h-3.5" /> Cargar cliente</button>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="text-[10px] font-black text-slate-400 uppercase">Nombre *</label>
                    <input value={form.clientName} onChange={e => setForm(f => ({ ...f, clientName: e.target.value }))}
                      className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-xl text-sm font-bold outline-none focus:border-orange-400 bg-white" />
                  </div>
                  <div>
                    <label className="text-[10px] font-black text-slate-400 uppercase">NIF/CIF</label>
                    <input value={form.clientTaxId} onChange={e => setForm(f => ({ ...f, clientTaxId: e.target.value }))}
                      className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-xl text-sm font-bold outline-none focus:border-orange-400 bg-white" />
                  </div>
                  <div>
                    <label className="text-[10px] font-black text-slate-400 uppercase">Email</label>
                    <input type="email" value={form.clientEmail} onChange={e => setForm(f => ({ ...f, clientEmail: e.target.value }))}
                      className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-xl text-sm font-bold outline-none focus:border-orange-400 bg-white" />
                  </div>
                  <div>
                    <label className="text-[10px] font-black text-slate-400 uppercase">Dirección</label>
                    <input value={form.clientAddress} onChange={e => setForm(f => ({ ...f, clientAddress: e.target.value }))}
                      className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-xl text-sm font-bold outline-none focus:border-orange-400 bg-white" />
                  </div>
                </div>
              </div>

              {/* Líneas */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <p className="text-[10px] font-black text-slate-400 uppercase">Líneas de Factura</p>
                  <button onClick={addLine} className="text-[10px] font-black text-orange-600 hover:text-orange-700 flex items-center gap-1">
                    <Plus className="w-3 h-3" /> Añadir línea
                  </button>
                </div>
                <div className="space-y-2">
                  {form.lines.map((line, i) => (
                    <div key={i} className="grid grid-cols-12 gap-2 items-center">
                      <input value={line.description} onChange={e => updateLine(i, 'description', e.target.value)}
                        placeholder="Descripción" className="col-span-5 px-3 py-2 border border-slate-200 rounded-xl text-xs font-bold outline-none focus:border-orange-400" />
                      <input type="number" value={line.quantity} onChange={e => updateLine(i, 'quantity', parseFloat(e.target.value) || 0)}
                        placeholder="Cant" className="col-span-1 px-2 py-2 border border-slate-200 rounded-xl text-xs font-bold outline-none focus:border-orange-400 text-center" />
                      <input type="number" value={line.unitPrice} onChange={e => updateLine(i, 'unitPrice', parseFloat(e.target.value) || 0)}
                        placeholder="Precio" className="col-span-2 px-2 py-2 border border-slate-200 rounded-xl text-xs font-bold outline-none focus:border-orange-400" />
                      <input type="number" value={line.discount} onChange={e => updateLine(i, 'discount', parseFloat(e.target.value) || 0)}
                        placeholder="Dto%" className="col-span-1 px-2 py-2 border border-slate-200 rounded-xl text-xs font-bold outline-none focus:border-orange-400 text-center" />
                      <input type="number" value={line.vatRate} onChange={e => updateLine(i, 'vatRate', parseFloat(e.target.value) || 21)}
                        placeholder="IVA%" className="col-span-1 px-2 py-2 border border-slate-200 rounded-xl text-xs font-bold outline-none focus:border-orange-400 text-center" />
                      <div className="col-span-1 text-right">
                        <span className="text-xs font-black text-slate-700">
                          {fmt(line.quantity * line.unitPrice * (1 - line.discount/100))}
                        </span>
                      </div>
                      <button onClick={() => removeLine(i)} className="col-span-1 p-1 text-red-400 hover:text-red-600">
                        <X className="w-3 h-3" />
                      </button>
                    </div>
                  ))}
                </div>
                {(() => { const t = totalsBreakdown(); return (
                  <div className="mt-3 flex justify-end">
                    <div className="w-full sm:w-72 space-y-1 text-sm">
                      <div className="flex justify-between text-slate-500"><span>Base imponible</span><span className="font-bold">{fmt(t.base)}</span></div>
                      <div className="flex justify-between text-slate-500"><span>IVA</span><span className="font-bold">{fmt(t.vat)}</span></div>
                      <div className="flex justify-between items-center text-slate-500">
                        <span className="flex items-center gap-1">Retención IRPF <input type="number" step="0.01" value={form.irpfRate} onChange={e => setForm(f => ({ ...f, irpfRate: parseFloat(e.target.value) || 0 }))} className="w-14 px-1.5 py-0.5 border border-slate-200 rounded text-center" />%</span>
                        <span className="font-bold text-rose-500">-{fmt(t.irpf)}</span>
                      </div>
                      <div className="flex justify-between text-slate-900 text-lg font-black border-t border-slate-200 pt-1"><span>Total</span><span className="text-orange-600">{fmt(t.total)}</span></div>
                    </div>
                  </div>
                ); })()}
              </div>

              {/* Notas */}
              <div>
                <label className="text-[10px] font-black text-slate-400 uppercase">Notas / Condiciones de pago</label>
                <textarea value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} rows={3}
                  className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-xl text-sm outline-none focus:border-orange-400 resize-none" />
              </div>
            </div>

            {/* Modal footer */}
            <div className="flex gap-3 px-6 py-4 border-t border-slate-100">
              <button onClick={() => setShowModal(false)} className="flex-1 py-2.5 border border-slate-200 text-slate-600 rounded-xl font-black text-xs hover:bg-slate-50">
                Cancelar
              </button>
              <button onClick={() => { setForm(f => ({ ...f, status: 'draft' })); setTimeout(handleSave, 0); }}
                disabled={saving} className="flex-1 py-2.5 border border-orange-300 text-orange-600 rounded-xl font-black text-xs hover:bg-orange-50">
                Guardar borrador
              </button>
              <button onClick={() => { setForm(f => ({ ...f, status: 'issued' })); setTimeout(handleSave, 0); }}
                disabled={saving} className="flex-1 py-2.5 bg-orange-500 text-white rounded-xl font-black text-xs hover:bg-orange-600 flex items-center justify-center gap-2">
                {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                Emitir Factura
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Selector de cliente importado */}
      {clientPicker && (() => {
        const qn = clientQ.trim().toLowerCase();
        const list = (clientList || []).filter(c => !qn ||
          (c.nombre || '').toLowerCase().includes(qn) ||
          String(c.cif || c.nif || c.codigo || '').toLowerCase().includes(qn));
        return (
          <div className="fixed inset-0 bg-black/50 z-[60] flex items-center justify-center p-4" onClick={() => setClientPicker(false)}>
            <div className="bg-white rounded-2xl w-full max-w-lg max-h-[80vh] flex flex-col overflow-hidden" onClick={e => e.stopPropagation()}>
              <div className="flex items-center justify-between px-5 py-3 border-b border-slate-100">
                <h3 className="font-black text-slate-800 text-sm uppercase flex items-center gap-2"><Users className="w-4 h-4" /> Clientes ({(clientList || []).length})</h3>
                <button onClick={() => setClientPicker(false)} className="p-1.5 hover:bg-slate-100 rounded-lg"><X className="w-4 h-4" /></button>
              </div>
              <div className="p-3 border-b border-slate-100">
                <input value={clientQ} onChange={e => setClientQ(e.target.value)} placeholder="Buscar por nombre o NIF…" autoFocus
                  className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm outline-none focus:border-orange-400" />
              </div>
              <div className="overflow-auto divide-y divide-slate-100">
                {list.map((c, k) => (
                  <button key={c.id || k} onClick={() => pickClient(c)} className="w-full text-left px-4 py-2.5 hover:bg-orange-50 flex items-center justify-between gap-2">
                    <span className="font-bold text-slate-700 text-sm truncate">{c.nombre || '—'}</span>
                    <span className="text-[11px] text-slate-400 shrink-0">{c.cif || c.nif || c.codigo || ''}</span>
                  </button>
                ))}
                {list.length === 0 && <p className="p-6 text-center text-slate-400 text-sm">Sin clientes.</p>}
              </div>
            </div>
          </div>
        );
      })()}
    </div>
  );
};

export default Invoices;
