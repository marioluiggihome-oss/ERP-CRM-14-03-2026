/**
 * RentabilidadPanel - Cuenta de resultados por proyecto (cocina)
 * Cruza Ventas (presupuestos) con Costes (facturas/gastos) -> Margen.
 */
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { TrendingUp, Plus, Trash2, RefreshCw, X, Euro, Upload, Sparkles, ArrowUp, ArrowDown, Filter, PackageCheck, Receipt, Truck, FolderOpen, Banknote, ShoppingCart, Tag } from 'lucide-react';
import { getToken } from '../services/api';
import RentabilidadLineas from './RentabilidadLineas';
import ReportGenerator from './ReportGenerator';
import IngresosACuenta from './IngresosACuenta';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const eur = (n) => (Number(n) || 0).toLocaleString('es-ES', { style: 'currency', currency: 'EUR' });
const normRef = (v) => String(v || '').toUpperCase().replace(/[^A-Z0-9]/g, '');
const projectLabel = (r) => {
  const aliases = [r.orderRef && `Pedido ${r.orderRef}`, r.invoiceNumber && `Factura ${r.invoiceNumber}`, r.internalReference && `Int. ${r.internalReference}`].filter(Boolean).join(' · ');
  return `${r.ref || '-'} - ${r.cliente || 'Sin cliente'}${aliases ? ` (${aliases})` : ''}`;
};

const RentabilidadPanel = ({ currentUser }) => {
  const [view, setView] = useState('lineas'); // 'lineas' (por líneas/documentos) por defecto | 'proyecto' | 'informes'
  // Navegación desde el informe a un documento concreto (y botón de retroceso al informe).
  const [openRef, setOpenRef] = useState(null);
  const [cameFromReport, setCameFromReport] = useState(false);
  const [data, setData] = useState({ rows: [], totales: {} });
  const [loading, setLoading] = useState(true);
  const [costModal, setCostModal] = useState(null);
  const [costs, setCosts] = useState([]);
  const [form, setForm] = useState({ proveedor: '', concepto: '', categoria: 'MOBILIARIO', importe: '' });
  const [importing, setImporting] = useState(false);
  const [invoice, setInvoice] = useState(null);
  const [analytics, setAnalytics] = useState({ bySupplier: [], byCategory: [], byMonth: [] });
  const [periodos, setPeriodos] = useState([]);

  // Filtros por columna
  const [columnFilters, setColumnFilters] = useState({
    ref: '',
    cliente: '',
    fechaDesde: '',
    fechaHasta: '',
    ventaMin: '',
    ventaMax: '',
    costeMin: '',
    costeMax: '',
    margenMin: '',
    margenMax: '',
  });

  // Ordenación
  const [sortColumn, setSortColumn] = useState('ref');
  const [sortDirection, setSortDirection] = useState('asc');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await fetch(`${API_URL}/api/rentabilidad`);
      if (r.ok) setData(await r.json());
      const a = await fetch(`${API_URL}/api/rentabilidad/analytics`);
      if (a.ok) setAnalytics(await a.json());
      const per = await fetch(`${API_URL}/api/rentabilidad/por-periodo`);
      if (per.ok) setPeriodos((await per.json()).periodos || []);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const [compras, setCompras] = useState(null); // null = panel oculto
  const [compraCat, setCompraCat] = useState('MOBILIARIO');
  const openCosts = async (row) => {
    setCostModal(row);
    setCompras(null);
    try {
      const r = await fetch(`${API_URL}/api/project-costs?projectRef=${encodeURIComponent(row.ref)}`);
      setCosts(r.ok ? await r.json() : []);
    } catch (e) { setCosts([]); }
  };

  // Carga las compras (pedidos a proveedor de Cocina Desmontada) para asociar como coste.
  const cargarCompras = async () => {
    if (compras) { setCompras(null); return; }
    try {
      const tok = getToken();
      const r = await fetch(`${API_URL}/api/cascos/orders?kind=compra`, { headers: tok ? { Authorization: `Bearer ${tok}` } : {} });
      const d = r.ok ? await r.json() : { orders: [] };
      const mine = normRef(costModal?.ref);
      const list = (d.orders || []).sort((a, b) => (normRef(b.ref) === mine) - (normRef(a.ref) === mine));
      setCompras(list);
    } catch (e) { setCompras([]); }
  };

  // Asocia una compra como coste del proyecto, aplicando la partida elegida (importe = total de la compra).
  const asociarCompra = async (o) => {
    try {
      const r = await fetch(`${API_URL}/api/project-costs`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          projectRef: costModal.ref,
          proveedor: o.createdByName || 'Cascos (ACB)',
          concepto: `Compra cascos ${o.expediente || ''} · ${(o.lines || []).length} líneas`.trim(),
          categoria: compraCat,
          importe: Number(o.total) || 0,
          source: 'compra', compraId: o.id, expediente: o.expediente || '',
        }),
      });
      if (r.ok) { setCompras(null); await openCosts(costModal); load(); }
      else alert('No se pudo asociar la compra.');
    } catch (e) { alert('No se pudo asociar la compra.'); }
  };

  const [costFile, setCostFile] = useState(null); // { b64, mime, name }
  const readFile = (file) => new Promise((res) => {
    const fr = new FileReader();
    fr.onload = () => res({ b64: String(fr.result), mime: file.type || 'application/octet-stream', name: file.name });
    fr.onerror = () => res(null);
    fr.readAsDataURL(file);
  });
  const addCost = async () => {
    if (!form.importe || Number(form.importe) <= 0) { alert('Indica el importe'); return; }
    try {
      const body = { ...form, importe: Number(form.importe), projectRef: costModal.ref, source: 'manual' };
      if (costFile) { body.docBase64 = costFile.b64; body.docMime = costFile.mime; body.docName = costFile.name; }
      const r = await fetch(`${API_URL}/api/project-costs`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
      if (r.ok) {
        setForm({ proveedor: '', concepto: '', categoria: 'MOBILIARIO', importe: '' });
        setCostFile(null);
        await openCosts(costModal);
        load();
      }
    } catch (e) { alert('Error al guardar el coste'); }
  };
  // Visor del documento adjunto a un coste (factura de proveedor)
  const verCostDoc = async (docId) => {
    try {
      const r = await fetch(`${API_URL}/api/project-costs/doc/${docId}`);
      if (!r.ok) { alert('Documento no disponible'); return; }
      const j = await r.json();
      const b64 = j.dataBase64 || '';
      if (!b64) { alert('Documento no disponible'); return; }
      const src = b64.startsWith('data:') ? b64 : `data:${j.mime || 'application/pdf'};base64,${b64}`;
      const w = window.open(); if (w) { w.document.write(`<iframe src="${src}" style="width:100%;height:100%;border:0"></iframe>`); } else window.open(src, '_blank');
    } catch { alert('Documento no disponible'); }
  };

  // ---- Documentos del proyecto: entregas a cuenta, compras y ventas ----
  const [docsModal, setDocsModal] = useState(null); // row
  const [docsTab, setDocsTab] = useState('cuenta');
  const [docsData, setDocsData] = useState({ cuenta: [], compras: [], ventas: [] });
  const [docsLoading, setDocsLoading] = useState(false);
  const openDocs = async (row) => {
    setDocsModal(row); setDocsTab('cuenta'); setDocsLoading(true);
    setDocsData({ cuenta: [], compras: [], ventas: [] });
    const refN = normRef(row.ref);
    try {
      const tok = getToken();
      const authH = tok ? { Authorization: `Bearer ${tok}` } : {};
      const [ing, costs, cascos] = await Promise.all([
        fetch(`${API_URL}/api/rentabilidad/ingresos`).then(r => r.ok ? r.json() : { items: [] }).catch(() => ({ items: [] })),
        fetch(`${API_URL}/api/project-costs?projectRef=${encodeURIComponent(row.ref)}`).then(r => r.ok ? r.json() : []).catch(() => []),
        fetch(`${API_URL}/api/cascos/orders`, { headers: authH }).then(r => r.ok ? r.json() : { orders: [] }).catch(() => ({ orders: [] })),
      ]);
      const cuenta = (ing.items || []).filter(i => normRef(i.projectRef) === refN);
      const cascosAll = (cascos.orders || []).filter(o => normRef(o.ref) === refN);
      const ventas = cascosAll.filter(o => o.kind !== 'compra');
      const comprasCascos = cascosAll.filter(o => o.kind === 'compra');
      setDocsData({ cuenta, compras: costs || [], ventas, comprasCascos });
    } catch (e) { /* noop */ } finally { setDocsLoading(false); }
  };
  const verIngresoDoc = async (docId) => {
    try {
      const r = await fetch(`${API_URL}/api/rentabilidad/ingresos/doc/${docId}`);
      if (!r.ok) { alert('Documento no disponible'); return; }
      const j = await r.json();
      const b64 = j.dataBase64 || '';
      if (!b64) { alert('Documento no disponible'); return; }
      const mime = j.mime || 'application/pdf';
      const src = b64.startsWith('data:') ? b64 : `data:${mime};base64,${b64}`;
      const w = window.open(); if (w) { w.document.write(`<iframe src="${src}" style="width:100%;height:100%;border:0"></iframe>`); } else window.open(src, '_blank');
    } catch { alert('Documento no disponible'); }
  };

  const delCost = async (id) => {
    await fetch(`${API_URL}/api/project-costs/${id}`, { method: 'DELETE' });
    await openCosts(costModal);
    load();
  };

  // ---- Conversiones: presupuesto -> pedido -> factura ----
  const [converting, setConverting] = useState('');
  // Modal de conversión (pedido o factura) con campos serie + número
  const [convModal, setConvModal] = useState(null); // { row, tipo: 'pedido'|'factura', serie: '', numero: '' }

  const openConvModal = (row, tipo) => setConvModal({ row, tipo, serie: '', numero: '' });

  const CONV_ENDPOINTS = {
    pedido: 'presupuesto-to-pedido',
    albaran: 'pedido-to-albaran',
    factura: 'pedido-to-factura',
  };
  const CONV_BODY = {
    pedido: (serie, numero) => ({ orderSerie: serie, orderNumber: numero }),
    albaran: (serie, numero) => ({ albaranSerie: serie, albaranNumber: numero }),
    factura: (serie, numero) => ({ invoiceSerie: serie, invoiceNumber: numero }),
  };

  const doConversion = async () => {
    const { row, tipo, serie, numero } = convModal;
    setConvModal(null);
    setConverting(row.projectId);
    try {
      const res = await fetch(`${API_URL}/api/rentabilidad/${CONV_ENDPOINTS[tipo]}/${row.projectId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(CONV_BODY[tipo](serie, numero)),
      });
      const j = await res.json();
      if (!res.ok) throw new Error(j.detail || 'Error');
      if (tipo === 'albaran') alert('Albarán creado: ' + (j.albaranRef || ''));
      if (tipo === 'factura') alert('Factura creada: ' + (j.invoiceNumber || ''));
      await load();
    } catch (e) { alert(`No se pudo convertir a ${tipo}: ` + e.message); }
    finally { setConverting(''); }
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
      if (!r.ok || !j.success) { alert('No se pudo leer la factura: ' + (j.error || j.detail || '')); return; }
      const detected = (j.data.proyecto || '').trim();
      const backendRef = j.data.projectRef || '';
      const detectedNorm = normRef(detected);
      const match = data.rows.find(row => {
        const aliases = [row.ref, row.orderRef, row.invoiceNumber, row.internalReference, row.projectId].filter(Boolean).map(normRef);
        return detectedNorm && aliases.some(a => a && (a === detectedNorm || a.includes(detectedNorm) || detectedNorm.includes(a)));
      });
      setInvoice({
        ...j.data,
        projectRef: backendRef || (match ? match.ref : ''),
        projectMatches: j.data.projectMatches || [],
      });
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

  // Filtrado y ordenación
  const filteredRows = useMemo(() => {
    let rows = [...(data.rows || [])];

    // Filtros por columna
    if (columnFilters.ref) {
      rows = rows.filter(r => (r.ref || '').toLowerCase().includes(columnFilters.ref.toLowerCase()));
    }
    if (columnFilters.cliente) {
      rows = rows.filter(r => (r.cliente || '').toLowerCase().includes(columnFilters.cliente.toLowerCase()));
    }
    if (columnFilters.fechaDesde) {
      rows = rows.filter(r => (r.fecha || '') >= columnFilters.fechaDesde);
    }
    if (columnFilters.fechaHasta) {
      rows = rows.filter(r => (r.fecha || '') <= columnFilters.fechaHasta);
    }
    if (columnFilters.ventaMin) {
      rows = rows.filter(r => (r.venta || 0) >= Number(columnFilters.ventaMin));
    }
    if (columnFilters.ventaMax) {
      rows = rows.filter(r => (r.venta || 0) <= Number(columnFilters.ventaMax));
    }
    if (columnFilters.costeMin) {
      rows = rows.filter(r => (r.coste || 0) >= Number(columnFilters.costeMin));
    }
    if (columnFilters.costeMax) {
      rows = rows.filter(r => (r.coste || 0) <= Number(columnFilters.costeMax));
    }
    if (columnFilters.margenMin) {
      rows = rows.filter(r => (r.margen || 0) >= Number(columnFilters.margenMin));
    }
    if (columnFilters.margenMax) {
      rows = rows.filter(r => (r.margen || 0) <= Number(columnFilters.margenMax));
    }

    // Ordenación
    rows.sort((a, b) => {
      let va, vb;
      switch (sortColumn) {
        case 'ref': va = (a.ref || '').toLowerCase(); vb = (b.ref || '').toLowerCase(); break;
        case 'cliente': va = (a.cliente || '').toLowerCase(); vb = (b.cliente || '').toLowerCase(); break;
        case 'fecha': va = a.fecha || ''; vb = b.fecha || ''; break;
        case 'venta': va = a.venta || 0; vb = b.venta || 0; break;
        case 'coste': va = a.coste || 0; vb = b.coste || 0; break;
        case 'margen': va = a.margen || 0; vb = b.margen || 0; break;
        case 'margenPct': va = a.margenPct || 0; vb = b.margenPct || 0; break;
        default: va = a.ref || ''; vb = b.ref || '';
      }
      if (va < vb) return sortDirection === 'asc' ? -1 : 1;
      if (va > vb) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });

    return rows;
  }, [data.rows, columnFilters, sortColumn, sortDirection]);

  const handleSort = (col) => {
    if (sortColumn === col) {
      setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(col);
      setSortDirection('asc');
    }
  };

  const clearColumnFilters = () => {
    setColumnFilters({
      ref: '', cliente: '', fechaDesde: '', fechaHasta: '',
      ventaMin: '', ventaMax: '', costeMin: '', costeMax: '',
      margenMin: '', margenMax: '',
    });
  };

  const hasActiveFilters = Object.values(columnFilters).some(v => v !== '');

  const t = data.totales || {};

  // Componente de cabecera de columna con ordenación
  const SortHeader = ({ col, label, align = 'left' }) => (
    <th
      className={`p-3 text-xs font-black uppercase cursor-pointer hover:bg-slate-200 select-none text-${align}`}
      onClick={() => handleSort(col)}
    >
      <div className={`flex items-center gap-1 ${align === 'right' ? 'justify-end' : ''}`}>
        {label}
        {sortColumn === col ? (
          sortDirection === 'asc' ? <ArrowUp size={12} className="text-indigo-600" /> : <ArrowDown size={12} className="text-indigo-600" />
        ) : (
          <ArrowUp size={10} className="text-slate-300" />
        )}
      </div>
    </th>
  );

  return (
    <div className="h-full overflow-y-auto p-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-emerald-600 rounded-2xl flex items-center justify-center text-white"><TrendingUp size={24} /></div>
          <div>
            <h1 className="text-2xl font-black text-slate-900 uppercase">Rentabilidad por Proyecto</h1>
            <p className="text-sm text-slate-500">Venta - Coste = Margen por cocina</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {view === 'proyecto' && (
            <label className={`px-4 py-2 rounded-xl font-bold text-sm flex items-center gap-2 cursor-pointer ${importing ? 'bg-purple-200 text-purple-500' : 'bg-purple-600 text-white hover:bg-purple-700'}`}>
              <Sparkles size={16} className={importing ? 'animate-pulse' : ''} />
              {importing ? 'Leyendo factura de coste...' : 'Importar factura de coste (IA)'}
              <input type="file" accept="image/*,application/pdf" className="hidden" onChange={handleInvoiceFile} disabled={importing} />
            </label>
          )}
          <button onClick={load} className="px-4 py-2 bg-slate-100 hover:bg-slate-200 rounded-xl font-bold text-sm flex items-center gap-2">
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} /> Actualizar
          </button>
        </div>
      </div>

      {/* Conmutador de vista - Por líneas (documentos) por defecto */}
      <div className="flex gap-2 mb-5">
        <button onClick={() => setView('lineas')} className={`px-4 py-2 rounded-xl font-bold text-sm ${view === 'lineas' ? 'bg-slate-800 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}>Por líneas (documentos)</button>
        {/* "Por proyecto" desactivada temporalmente: la tabla no cuadraba bien, se retoma mas adelante */}
        <button onClick={() => setView('ingresos')} className={`px-4 py-2 rounded-xl font-bold text-sm ${view === 'ingresos' ? 'bg-slate-800 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}>Ingresos a cuenta</button>
        <button onClick={() => setView('informes')} className={`px-4 py-2 rounded-xl font-bold text-sm ${view === 'informes' ? 'bg-slate-800 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}>Generador de informes</button>
      </div>

      {view === 'ingresos' && <IngresosACuenta currentUser={currentUser} />}

      {view === 'informes' && <ReportGenerator onOpenDocument={(ref) => { setOpenRef(ref); setCameFromReport(true); setView('lineas'); }} />}

      {view === 'lineas' && <RentabilidadLineas currentUser={currentUser}
        openRef={openRef}
        onOpenedRef={() => setOpenRef(null)}
        onBackToReport={cameFromReport ? () => { setCameFromReport(false); setView('informes'); } : null} />}

      {view === 'proyecto' && currentUser?.isAdmin && (<>
      {/* Modal: revisar factura leida por IA antes de registrar */}
      {invoice && (
        <div className="fixed inset-0 bg-black/60 z-[130] flex items-center justify-center p-4" onClick={() => setInvoice(null)}>
          <div className="bg-white rounded-3xl w-full max-w-lg overflow-hidden" onClick={e => e.stopPropagation()}>
            <div className="bg-purple-600 text-white px-6 py-4 flex justify-between items-center">
              <h2 className="text-lg font-black flex items-center gap-2"><Sparkles size={18} /> Factura leida - revisa y asigna</h2>
              <button onClick={() => setInvoice(null)} className="p-2 hover:bg-white/20 rounded-xl"><X size={20} /></button>
            </div>
            <div className="p-6 space-y-3">
              <div>
                <label className="text-[10px] font-black text-slate-400 uppercase block mb-1">Proyecto (obligatorio)</label>
                <select value={invoice.projectRef} onChange={e => setInvoice({ ...invoice, projectRef: e.target.value })}
                  className={`w-full px-3 py-2 border rounded-lg text-sm font-bold ${invoice.projectRef ? 'border-emerald-300' : 'border-red-300'}`}>
                  <option value="">- Selecciona proyecto -</option>
                  {data.rows.map(r => <option key={r.projectId} value={r.ref}>{projectLabel(r)}</option>)}
                </select>
                {invoice.proyecto && !invoice.projectRef && (
                  <p className="text-[11px] text-amber-600 mt-1">La IA detecto "{invoice.proyecto}" pero no coincide de forma segura con ningun proyecto. Seleccionalo a mano.</p>
                )}
                {Array.isArray(invoice.projectMatches) && invoice.projectMatches.length > 0 && (
                  <div className="mt-2 rounded-xl border border-purple-100 bg-purple-50 p-2">
                    <p className="text-[10px] font-black text-purple-700 uppercase mb-1">Sugerencias detectadas</p>
                    <div className="space-y-1">
                      {invoice.projectMatches.slice(0, 3).map(m => (
                        <button key={`${m.projectId}-${m.projectRef}`} type="button" onClick={() => setInvoice({ ...invoice, projectRef: m.projectRef })}
                          className={`w-full text-left px-2 py-1.5 rounded-lg text-[11px] font-bold border ${invoice.projectRef === m.projectRef ? 'bg-emerald-100 border-emerald-300 text-emerald-800' : 'bg-white border-purple-100 text-slate-700 hover:border-purple-300'}`}>
                          {m.projectRef} · {m.cliente || 'Sin cliente'} <span className="font-normal text-slate-400">({m.score}% por {m.matchedBy || 'referencia'})</span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div><label className="text-[10px] font-black text-slate-400 uppercase block mb-1">Proveedor</label>
                  <input value={invoice.proveedor} onChange={e => setInvoice({ ...invoice, proveedor: e.target.value })} className="w-full px-3 py-2 border rounded-lg text-sm" /></div>
                <div><label className="text-[10px] font-black text-slate-400 uppercase block mb-1">Importe</label>
                  <input type="number" step="0.01" value={invoice.importe} onChange={e => setInvoice({ ...invoice, importe: e.target.value })} className="w-full px-3 py-2 border rounded-lg text-sm text-right font-bold" /></div>
                <div><label className="text-[10px] font-black text-slate-400 uppercase block mb-1">Fecha</label>
                  <input value={invoice.fecha} onChange={e => setInvoice({ ...invoice, fecha: e.target.value })} className="w-full px-3 py-2 border rounded-lg text-sm" /></div>
                <div><label className="text-[10px] font-black text-slate-400 uppercase block mb-1">Categoria</label>
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
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        <div className="bg-indigo-600 text-white p-4 rounded-2xl"><p className="text-[10px] uppercase opacity-80">Venta total</p><p className="text-2xl font-black">{eur(t.venta)}</p></div>
        <div className="bg-orange-600 text-white p-4 rounded-2xl"><p className="text-[10px] uppercase opacity-80">Coste total</p><p className="text-2xl font-black">{eur(t.coste)}</p></div>
        <div className={`${(t.margen || 0) >= 0 ? 'bg-emerald-600' : 'bg-red-600'} text-white p-4 rounded-2xl`}><p className="text-[10px] uppercase opacity-80">Margen total</p><p className="text-2xl font-black">{eur(t.margen)}</p><p className="text-[11px] opacity-80">{t.margenPct}%</p></div>
        <div className="bg-slate-800 text-white p-4 rounded-2xl"><p className="text-[10px] uppercase opacity-80">Proyectos</p><p className="text-2xl font-black">{t.proyectos || 0}</p></div>
      </div>

      {/* Métricas de controller: cobro pendiente, alertas de margen y pipeline */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white border border-slate-200 p-4 rounded-2xl">
          <p className="text-[10px] uppercase text-slate-400 font-black">Cobrado (ingresos a cuenta)</p>
          <p className="text-xl font-black text-emerald-600">{eur(t.cobrado)}</p>
        </div>
        <div className="bg-white border border-slate-200 p-4 rounded-2xl">
          <p className="text-[10px] uppercase text-slate-400 font-black">Pendiente de cobro</p>
          <p className={`text-xl font-black ${(t.pendienteCobro || 0) > 0 ? 'text-amber-600' : 'text-slate-700'}`}>{eur(t.pendienteCobro)}</p>
        </div>
        <div className="bg-white border border-slate-200 p-4 rounded-2xl">
          <p className="text-[10px] uppercase text-slate-400 font-black">Alertas margen bajo (&lt;15%)</p>
          <p className={`text-xl font-black ${(t.alertasMargen || 0) > 0 ? 'text-red-600' : 'text-slate-700'}`}>{t.alertasMargen || 0}</p>
        </div>
        <div className="bg-white border border-slate-200 p-4 rounded-2xl">
          <p className="text-[10px] uppercase text-slate-400 font-black">Pipeline (sin facturar)</p>
          <p className="text-xl font-black text-indigo-600">{eur(t.pipeline?.venta)}</p>
          <p className="text-[11px] text-slate-400">{t.pipeline?.documentos || 0} documentos · margen esperado {eur(t.pipeline?.margen)}</p>
        </div>
      </div>

      {/* Evolución mensual: venta/coste/margen por periodo */}
      {periodos.length > 0 && (
        <div className="bg-white border border-slate-200 rounded-2xl p-4 mb-6 overflow-x-auto">
          <h3 className="text-xs font-black text-slate-600 uppercase mb-3">Evolución mensual (venta - coste = margen)</h3>
          <table className="w-full text-sm min-w-[480px]">
            <thead className="text-slate-400">
              <tr>
                <th className="text-left p-1.5 text-[10px] font-black uppercase">Mes</th>
                <th className="text-right p-1.5 text-[10px] font-black uppercase">Venta</th>
                <th className="text-right p-1.5 text-[10px] font-black uppercase">Coste</th>
                <th className="text-right p-1.5 text-[10px] font-black uppercase">Margen</th>
                <th className="text-right p-1.5 text-[10px] font-black uppercase">%</th>
                <th className="text-right p-1.5 text-[10px] font-black uppercase">Docs</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {periodos.slice(-12).map(m => (
                <tr key={m.periodo}>
                  <td className="p-1.5 font-bold text-slate-700">{m.periodo}</td>
                  <td className="p-1.5 text-right font-mono">{eur(m.venta)}</td>
                  <td className="p-1.5 text-right font-mono text-orange-600">{eur(m.coste)}</td>
                  <td className={`p-1.5 text-right font-mono font-bold ${m.margen >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>{eur(m.margen)}</td>
                  <td className={`p-1.5 text-right font-bold ${m.margen >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>{m.margenPct}%</td>
                  <td className="p-1.5 text-right text-slate-400">{m.documentos}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Barra de filtros activos */}
      {hasActiveFilters && (
        <div className="flex items-center gap-2 mb-3 px-2">
          <Filter size={14} className="text-indigo-500" />
          <span className="text-xs font-bold text-slate-500">Filtros activos</span>
          <button onClick={clearColumnFilters} className="text-xs text-red-500 hover:text-red-700 font-bold ml-2 underline">
            Limpiar todos
          </button>
          <span className="text-xs text-slate-400 ml-auto">{filteredRows.length} de {data.rows.length} proyectos</span>
        </div>
      )}

      <div className="bg-white border border-slate-200 rounded-2xl overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-100 text-slate-600">
            <tr>
              <SortHeader col="ref" label="Proyecto" />
              <SortHeader col="cliente" label="Cliente" />
              <SortHeader col="fecha" label="Fecha" />
              <SortHeader col="venta" label="Venta" align="right" />
              <SortHeader col="coste" label="Coste" align="right" />
              <SortHeader col="margen" label="Margen" align="right" />
              <SortHeader col="margenPct" label="%" align="right" />
              <th className="text-right p-3 text-xs font-black uppercase">Pendiente cobro</th>
              <th className="text-center p-3 text-xs font-black uppercase">Costes</th>
              <th className="text-center p-3 text-xs font-black uppercase">Documento</th>
            </tr>
            {/* Fila de filtros por columna */}
            <tr className="bg-slate-50 border-t border-slate-200">
              <th className="p-1.5">
                <input
                  value={columnFilters.ref}
                  onChange={e => setColumnFilters(prev => ({ ...prev, ref: e.target.value }))}
                  placeholder="Filtrar..."
                  className="w-full px-2 py-1 text-xs border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-400 font-normal"
                />
              </th>
              <th className="p-1.5">
                <input
                  value={columnFilters.cliente}
                  onChange={e => setColumnFilters(prev => ({ ...prev, cliente: e.target.value }))}
                  placeholder="Filtrar..."
                  className="w-full px-2 py-1 text-xs border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-400 font-normal"
                />
              </th>
              <th className="p-1.5">
                <div className="flex gap-1">
                  <input
                    type="date"
                    value={columnFilters.fechaDesde}
                    onChange={e => setColumnFilters(prev => ({ ...prev, fechaDesde: e.target.value }))}
                    className="w-full px-1 py-1 text-[10px] border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-400 font-normal"
                    title="Desde"
                  />
                </div>
              </th>
              <th className="p-1.5">
                <div className="flex gap-0.5">
                  <input
                    type="number"
                    value={columnFilters.ventaMin}
                    onChange={e => setColumnFilters(prev => ({ ...prev, ventaMin: e.target.value }))}
                    placeholder="Min"
                    className="w-1/2 px-1 py-1 text-[10px] border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-400 font-normal text-right"
                  />
                  <input
                    type="number"
                    value={columnFilters.ventaMax}
                    onChange={e => setColumnFilters(prev => ({ ...prev, ventaMax: e.target.value }))}
                    placeholder="Max"
                    className="w-1/2 px-1 py-1 text-[10px] border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-400 font-normal text-right"
                  />
                </div>
              </th>
              <th className="p-1.5">
                <div className="flex gap-0.5">
                  <input
                    type="number"
                    value={columnFilters.costeMin}
                    onChange={e => setColumnFilters(prev => ({ ...prev, costeMin: e.target.value }))}
                    placeholder="Min"
                    className="w-1/2 px-1 py-1 text-[10px] border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-400 font-normal text-right"
                  />
                  <input
                    type="number"
                    value={columnFilters.costeMax}
                    onChange={e => setColumnFilters(prev => ({ ...prev, costeMax: e.target.value }))}
                    placeholder="Max"
                    className="w-1/2 px-1 py-1 text-[10px] border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-400 font-normal text-right"
                  />
                </div>
              </th>
              <th className="p-1.5">
                <div className="flex gap-0.5">
                  <input
                    type="number"
                    value={columnFilters.margenMin}
                    onChange={e => setColumnFilters(prev => ({ ...prev, margenMin: e.target.value }))}
                    placeholder="Min"
                    className="w-1/2 px-1 py-1 text-[10px] border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-400 font-normal text-right"
                  />
                  <input
                    type="number"
                    value={columnFilters.margenMax}
                    onChange={e => setColumnFilters(prev => ({ ...prev, margenMax: e.target.value }))}
                    placeholder="Max"
                    className="w-1/2 px-1 py-1 text-[10px] border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-400 font-normal text-right"
                  />
                </div>
              </th>
              <th className="p-1.5"></th>
              <th className="p-1.5"></th>
              <th className="p-1.5">
                {hasActiveFilters && (
                  <button onClick={clearColumnFilters} className="text-[10px] text-red-500 hover:text-red-700 font-bold">
                    <X size={14} />
                  </button>
                )}
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {filteredRows.map((r) => (
              <tr key={r.projectId || r.orderId || r.invoiceId || r.ref} className={`hover:bg-slate-50 ${r.alertaMargen ? 'bg-red-50/60' : ''}`}>
                <td className="p-3 font-black text-indigo-700">
                  {r.alertaMargen && <span title="Margen bajo (<15%)" className="inline-block mr-1 text-red-500">⚠</span>}
                  {r.ref || '-'}
                </td>
                <td className="p-3 text-slate-700">{r.cliente || '-'}</td>
                <td className="p-3 text-slate-500 text-xs">{r.fecha || '-'}</td>
                <td className="p-3 text-right font-mono">{eur(r.venta)}</td>
                <td className="p-3 text-right font-mono text-orange-600">{eur(r.coste)}</td>
                <td className={`p-3 text-right font-mono font-black ${r.margen >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>{eur(r.margen)}</td>
                <td className={`p-3 text-right font-bold ${r.alertaMargen ? 'text-red-600' : r.margen >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>{r.margenPct}%</td>
                <td className={`p-3 text-right font-mono ${(r.pendienteCobro || 0) > 0 ? 'text-amber-600 font-bold' : 'text-slate-400'}`}>{eur(r.pendienteCobro)}</td>
                <td className="p-3 text-center">
                  <div className="flex items-center justify-center gap-1.5">
                    <button onClick={() => openCosts(r)} className="px-3 py-1.5 bg-emerald-50 text-emerald-700 rounded-lg text-xs font-bold hover:bg-emerald-100 flex items-center gap-1">
                      <Plus size={12} /> Coste
                    </button>
                    <button onClick={() => openDocs(r)} className="px-3 py-1.5 bg-indigo-50 text-indigo-700 rounded-lg text-xs font-bold hover:bg-indigo-100 flex items-center gap-1" title="Entregas a cuenta, compras y ventas del proyecto">
                      <FolderOpen size={12} /> Docs
                    </button>
                  </div>
                </td>
                <td className="p-3 text-center">
                  {r.invoiceId ? (
                    <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded-lg text-[11px] font-black flex items-center gap-1 mx-auto w-fit"><Receipt size={11} /> FACTURA {r.invoiceNumber || ''}</span>
                  ) : r.albaranId && r.projectId ? (
                    <div className="flex items-center justify-center gap-1.5">
                      <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded-lg text-[11px] font-black flex items-center gap-1"><Truck size={11} /> ALBARÁN {r.albaranRef || ''}</span>
                      <button onClick={() => openConvModal(r, 'factura')} disabled={converting === r.projectId}
                        className="px-2.5 py-1 bg-blue-600 text-white rounded-lg text-[11px] font-bold hover:bg-blue-700 disabled:opacity-50">→ Factura</button>
                    </div>
                  ) : r.albaranId ? (
                    <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded-lg text-[11px] font-black flex items-center gap-1 mx-auto w-fit"><Truck size={11} /> ALBARÁN {r.albaranRef || ''}</span>
                  ) : r.orderId && r.projectId ? (
                    <div className="flex items-center justify-center gap-1.5">
                      <span className="px-2 py-1 bg-amber-100 text-amber-700 rounded-lg text-[11px] font-black flex items-center gap-1"><PackageCheck size={11} /> PEDIDO {r.orderRef || ''}</span>
                      <button onClick={() => openConvModal(r, 'albaran')} disabled={converting === r.projectId}
                        className="px-2.5 py-1 bg-purple-600 text-white rounded-lg text-[11px] font-bold hover:bg-purple-700 disabled:opacity-50">→ Albarán</button>
                    </div>
                  ) : r.orderId ? (
                    <span className="px-2 py-1 bg-amber-100 text-amber-700 rounded-lg text-[11px] font-black flex items-center gap-1 mx-auto w-fit"><PackageCheck size={11} /> PEDIDO {r.orderRef || ''}</span>
                  ) : r.projectId ? (
                    <button onClick={() => openConvModal(r, 'pedido')} disabled={converting === r.projectId}
                      className="px-2.5 py-1 bg-indigo-600 text-white rounded-lg text-[11px] font-bold hover:bg-indigo-700 disabled:opacity-50">→ Pedido</button>
                  ) : (
                    <span className="px-2 py-1 bg-slate-100 text-slate-500 rounded-lg text-[11px] font-bold">SIN PRESUPUESTO</span>
                  )}
                </td>
              </tr>
            ))}
            {filteredRows.length === 0 && (
              <tr><td colSpan={10} className="p-8 text-center text-slate-400">{loading ? 'Cargando...' : hasActiveFilters ? 'Sin resultados con estos filtros' : 'Sin proyectos'}</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {/* ===== ANALISIS ===== */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mt-6">
        {/* Cocinas menos rentables */}
        <div className="bg-white border border-slate-200 rounded-2xl p-4">
          <h3 className="text-xs font-black text-red-600 uppercase mb-3">Cocinas menos rentables</h3>
          {[...data.rows].filter(r => r.coste > 0).sort((a, b) => a.margenPct - b.margenPct).slice(0, 5).map((r, i) => (
            <div key={r.projectId} className="flex justify-between items-center py-1.5 border-b border-slate-50 last:border-0">
              <span className="text-sm font-medium text-slate-700 truncate">{i + 1}. {r.ref || r.cliente || '-'}</span>
              <span className={`text-sm font-black ${r.margenPct >= 0 ? 'text-amber-600' : 'text-red-600'}`}>{r.margenPct}%</span>
            </div>
          ))}
          {data.rows.filter(r => r.coste > 0).length === 0 && <p className="text-sm text-slate-400">Registra costes para ver el ranking</p>}
        </div>
        {/* Gasto por proveedor */}
        <div className="bg-white border border-slate-200 rounded-2xl p-4">
          <h3 className="text-xs font-black text-orange-600 uppercase mb-3">Gasto por proveedor</h3>
          {analytics.bySupplier.slice(0, 6).map((s, i) => (
            <div key={i} className="flex justify-between items-center py-1.5 border-b border-slate-50 last:border-0">
              <span className="text-sm text-slate-700 truncate">{s.nombre}</span>
              <span className="text-sm font-bold text-orange-600 font-mono">{eur(s.total)}</span>
            </div>
          ))}
          {analytics.bySupplier.length === 0 && <p className="text-sm text-slate-400">Sin costes aun</p>}
        </div>
        {/* Gasto por categoria */}
        <div className="bg-white border border-slate-200 rounded-2xl p-4">
          <h3 className="text-xs font-black text-indigo-600 uppercase mb-3">Gasto por categoria</h3>
          {analytics.byCategory.map((c, i) => (
            <div key={i} className="flex justify-between items-center py-1.5 border-b border-slate-50 last:border-0">
              <span className="text-sm text-slate-700 truncate">{c.nombre}</span>
              <span className="text-sm font-bold text-indigo-600 font-mono">{eur(c.total)}</span>
            </div>
          ))}
          {analytics.byCategory.length === 0 && <p className="text-sm text-slate-400">Sin costes aun</p>}
        </div>
      </div>

      {/* Modal de costes de un proyecto */}
      {costModal && (
        <div className="fixed inset-0 bg-black/60 z-[120] flex items-center justify-center p-4" onClick={() => setCostModal(null)}>
          <div className="bg-white rounded-3xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col" onClick={e => e.stopPropagation()}>
            <div className="bg-emerald-600 text-white px-6 py-4 flex justify-between items-center">
              <div>
                <h2 className="text-lg font-black">Costes - {costModal.ref}</h2>
                <p className="text-xs text-emerald-100">{costModal.cliente} - Venta {eur(costModal.venta)}</p>
              </div>
              <button onClick={() => setCostModal(null)} className="p-2 hover:bg-white/20 rounded-xl"><X size={20} /></button>
            </div>
            <div className="p-6 overflow-auto space-y-4">
              {/* Formulario de alta de coste */}
              <div className="grid grid-cols-2 md:grid-cols-5 gap-2 items-end bg-slate-50 p-3 rounded-xl">
                <input value={form.proveedor} onChange={e => setForm({ ...form, proveedor: e.target.value })} placeholder="Proveedor" className="px-2 py-2 border rounded-lg text-sm" />
                <input value={form.concepto} onChange={e => setForm({ ...form, concepto: e.target.value })} placeholder="Concepto" className="px-2 py-2 border rounded-lg text-sm" />
                <select value={form.categoria} onChange={e => setForm({ ...form, categoria: e.target.value })} className="px-2 py-2 border rounded-lg text-sm">
                  {['MOBILIARIO','ELECTRODOMESTICOS','ENCIMERA','TRANSPORTE','MONTAJE','SUBCONTRATA','OTROS'].map(c => <option key={c}>{c}</option>)}
                </select>
                <input type="number" step="0.01" value={form.importe} onChange={e => setForm({ ...form, importe: e.target.value })} placeholder="EUR" className="px-2 py-2 border rounded-lg text-sm text-right" />
                <button onClick={addCost} className="px-3 py-2 bg-emerald-600 text-white rounded-lg font-bold text-sm flex items-center justify-center gap-1"><Plus size={14} /> Anadir</button>
                <label className="col-span-2 md:col-span-5 flex items-center gap-2 text-xs text-slate-500 cursor-pointer">
                  <span className="px-2 py-1.5 bg-white border border-slate-200 rounded-lg font-bold text-slate-600 hover:bg-slate-100">📎 Adjuntar PDF/foto (opcional)</span>
                  <input type="file" accept="application/pdf,image/*" className="hidden" onChange={async e => { const f = e.target.files?.[0]; setCostFile(f ? await readFile(f) : null); }} />
                  {costFile && <span className="text-emerald-700 font-bold truncate">{costFile.name} <button type="button" onClick={() => setCostFile(null)} className="text-red-400 ml-1">✕</button></span>}
                </label>
              </div>

              {/* Asociar una compra (pedido a proveedor de Cocina Desmontada) como coste por partida */}
              <div className="border border-indigo-100 rounded-xl p-3 bg-indigo-50/40">
                <div className="flex items-center justify-between gap-2 flex-wrap">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-black text-indigo-800 uppercase">Asociar compra</span>
                    <span className="text-[11px] text-slate-500">aplica el total a una partida</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <select value={compraCat} onChange={e => setCompraCat(e.target.value)} className="px-2 py-1.5 border rounded-lg text-xs" title="Partida a la que se imputa la compra">
                      {['MOBILIARIO','ELECTRODOMESTICOS','ENCIMERA','TRANSPORTE','MONTAJE','SUBCONTRATA','OTROS'].map(c => <option key={c}>{c}</option>)}
                    </select>
                    <button onClick={cargarCompras} className="px-3 py-1.5 bg-indigo-600 text-white rounded-lg font-bold text-xs flex items-center gap-1"><PackageCheck size={13} /> {compras ? 'Ocultar' : 'Buscar compras'}</button>
                  </div>
                </div>
                {Array.isArray(compras) && (
                  <div className="mt-3 max-h-48 overflow-y-auto divide-y divide-indigo-100">
                    {compras.length === 0 && <p className="text-xs text-slate-400 py-3 text-center">No hay pedidos de compra guardados.</p>}
                    {compras.map(o => {
                      const match = normRef(o.ref) && normRef(o.ref) === normRef(costModal.ref);
                      return (
                        <div key={o.id} className="flex items-center gap-2 py-2">
                          <div className="flex-1 min-w-0">
                            <p className="text-xs font-bold text-slate-700 truncate">{o.cliente || 'Sin cliente'}{o.ref ? ` · ${o.ref}` : ''} {match && <span className="ml-1 px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-700 text-[9px] font-black">↔ coincide</span>}</p>
                            <p className="text-[10px] text-slate-400">{o.expediente ? `🔗 ${o.expediente} · ` : ''}{(o.lines || []).length} líneas · {o.createdAt ? new Date(o.createdAt).toLocaleDateString('es-ES') : ''}</p>
                          </div>
                          <span className="text-xs font-black text-slate-800">{eur(o.total)}</span>
                          <button onClick={() => asociarCompra(o)} className="px-2.5 py-1.5 bg-emerald-600 text-white rounded-lg text-[11px] font-bold hover:bg-emerald-700">Asociar</button>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
              {/* Lista de costes */}
              <table className="w-full text-sm">
                <thead className="text-slate-500"><tr><th className="text-left p-2 text-xs uppercase">Proveedor</th><th className="text-left p-2 text-xs uppercase">Concepto</th><th className="text-left p-2 text-xs uppercase">Cat.</th><th className="text-right p-2 text-xs uppercase">Importe</th><th></th></tr></thead>
                <tbody className="divide-y divide-slate-100">
                  {costs.map(c => (
                    <tr key={c.id}>
                      <td className="p-2 font-medium">{c.proveedor || '-'}</td>
                      <td className="p-2 text-slate-600">{c.concepto || '-'}{c.expediente && <span className="ml-1 px-1.5 py-0.5 rounded bg-amber-100 text-amber-700 text-[9px] font-black">🔗 {c.expediente}</span>}</td>
                      <td className="p-2 text-[11px] text-slate-500">{c.categoria}</td>
                      <td className="p-2 text-right font-mono font-bold text-orange-600">{eur(c.importe)}</td>
                      <td className="p-2 text-right whitespace-nowrap">
                        {c.docId && <button onClick={() => verCostDoc(c.docId)} title="Ver documento adjunto" className="text-slate-500 hover:text-indigo-600 mr-2">📎</button>}
                        <button onClick={() => delCost(c.id)} className="text-red-400 hover:text-red-600"><Trash2 size={14} /></button>
                      </td>
                    </tr>
                  ))}
                  {costs.length === 0 && <tr><td colSpan={5} className="p-4 text-center text-slate-400">Sin costes aun</td></tr>}
                </tbody>
              </table>
              <div className="bg-slate-900 text-white rounded-xl p-4 flex justify-between items-center">
                <span className="text-xs uppercase text-slate-400">Coste total - Margen</span>
                <span className="font-black">
                  {eur(costs.reduce((s, c) => s + (Number(c.importe) || 0), 0))}
                  {' - '}
                  <span className={costModal.venta - costs.reduce((s, c) => s + (Number(c.importe) || 0), 0) >= 0 ? 'text-emerald-400' : 'text-red-400'}>
                    {eur(costModal.venta - costs.reduce((s, c) => s + (Number(c.importe) || 0), 0))}
                  </span>
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal de DOCUMENTOS del proyecto: entregas a cuenta, compras y ventas */}
      {docsModal && (() => {
        const sum = (arr, f) => arr.reduce((s, x) => s + (Number(f(x)) || 0), 0);
        const comprasTot = sum(docsData.compras || [], c => c.importe);
        const ventaTot = docsModal.venta || 0;
        const cuentaTot = sum(docsData.cuenta || [], i => i.importe);
        const TABS = [
          { id: 'cuenta', label: 'Entregas a cuenta', icon: Banknote, n: (docsData.cuenta || []).length },
          { id: 'compras', label: 'Compras', icon: ShoppingCart, n: (docsData.compras || []).length },
          { id: 'ventas', label: 'Ventas', icon: Tag, n: (docsData.ventas || []).length },
        ];
        return (
        <div className="fixed inset-0 bg-black/60 z-[130] flex items-center justify-center p-4" onClick={() => setDocsModal(null)}>
          <div className="bg-white rounded-3xl w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col" onClick={e => e.stopPropagation()}>
            <div className="bg-indigo-700 text-white px-6 py-4 flex justify-between items-center">
              <div>
                <h2 className="text-lg font-black">Documentos · {docsModal.ref}</h2>
                <p className="text-xs text-indigo-200">{docsModal.cliente} · Venta {eur(ventaTot)} · A cuenta {eur(cuentaTot)} · Compras {eur(comprasTot)}</p>
              </div>
              <button onClick={() => setDocsModal(null)} className="p-2 hover:bg-white/20 rounded-xl"><X size={20} /></button>
            </div>
            <div className="flex gap-1 px-4 pt-3 bg-slate-50">
              {TABS.map(t => (
                <button key={t.id} onClick={() => setDocsTab(t.id)}
                  className={`flex items-center gap-1.5 px-4 py-2 rounded-t-xl text-sm font-bold ${docsTab === t.id ? 'bg-white text-indigo-700 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}>
                  <t.icon size={15} /> {t.label} <span className="text-[10px] bg-slate-200 text-slate-600 rounded-full px-1.5">{t.n}</span>
                </button>
              ))}
            </div>
            <div className="p-5 overflow-auto">
              {docsLoading && <p className="text-center text-slate-400 py-8 text-sm">Cargando…</p>}

              {!docsLoading && docsTab === 'cuenta' && (
                (docsData.cuenta || []).length === 0 ? <p className="text-center text-slate-400 py-8 text-sm">Sin entregas a cuenta para este proyecto.</p> :
                <table className="w-full text-sm"><thead className="text-slate-500"><tr><th className="text-left p-2 text-xs uppercase">Fecha</th><th className="text-left p-2 text-xs uppercase">Cliente</th><th className="text-right p-2 text-xs uppercase">Importe</th><th className="p-2"></th></tr></thead>
                  <tbody className="divide-y divide-slate-100">{docsData.cuenta.map((i, k) => (
                    <tr key={k}><td className="p-2 text-slate-500">{i.fecha || '—'}</td><td className="p-2">{i.cliente || '—'}</td>
                      <td className="p-2 text-right font-mono font-bold text-teal-700">{eur(i.importe)}</td>
                      <td className="p-2 text-right">{i.docId && <button onClick={() => verIngresoDoc(i.docId)} title="Ver documento" className="text-slate-500 hover:text-teal-600">📎</button>}</td></tr>
                  ))}</tbody></table>
              )}

              {!docsLoading && docsTab === 'compras' && (
                ((docsData.compras || []).length === 0 && (docsData.comprasCascos || []).length === 0) ? <p className="text-center text-slate-400 py-8 text-sm">Sin compras asociadas. Asóciala desde el botón “Coste”.</p> :
                <table className="w-full text-sm"><thead className="text-slate-500"><tr><th className="text-left p-2 text-xs uppercase">Proveedor</th><th className="text-left p-2 text-xs uppercase">Concepto / Partida</th><th className="text-right p-2 text-xs uppercase">Importe</th><th className="p-2"></th></tr></thead>
                  <tbody className="divide-y divide-slate-100">{(docsData.compras || []).map((c, k) => (
                    <tr key={k}><td className="p-2 font-medium">{c.proveedor || '—'}</td>
                      <td className="p-2 text-slate-600">{c.concepto || '—'} <span className="text-[10px] text-slate-400">· {c.categoria}</span>{c.expediente && <span className="ml-1 px-1.5 py-0.5 rounded bg-amber-100 text-amber-700 text-[9px] font-black">🔗 {c.expediente}</span>}</td>
                      <td className="p-2 text-right font-mono font-bold text-orange-600">{eur(c.importe)}</td>
                      <td className="p-2 text-right">{c.docId && <button onClick={() => verCostDoc(c.docId)} title="Ver documento" className="text-slate-500 hover:text-indigo-600">📎</button>}</td></tr>
                  ))}
                  {(docsData.comprasCascos || []).map((o, k) => (
                    <tr key={'cc' + k} className="bg-amber-50/40"><td className="p-2 font-medium">Cascos (ACB)</td>
                      <td className="p-2 text-slate-600">Pedido a proveedor · {(o.lines || []).length} líneas {o.expediente && <span className="ml-1 px-1.5 py-0.5 rounded bg-amber-100 text-amber-700 text-[9px] font-black">🔗 {o.expediente}</span>} <span className="text-[9px] text-slate-400">(no imputado como coste)</span></td>
                      <td className="p-2 text-right font-mono font-bold text-slate-500">{eur(o.total)}</td>
                      <td className="p-2"></td></tr>
                  ))}</tbody></table>
              )}

              {!docsLoading && docsTab === 'ventas' && (
                <>
                  <div className="flex flex-wrap gap-2 mb-3">
                    {docsModal.orderRef && <span className="px-2 py-1 bg-indigo-100 text-indigo-700 rounded-lg text-[11px] font-black">Pedido {docsModal.orderRef}</span>}
                    {docsModal.invoiceNumber && <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded-lg text-[11px] font-black">Factura {docsModal.invoiceNumber}</span>}
                    {docsModal.albaranRef && <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded-lg text-[11px] font-black">Albarán {docsModal.albaranRef}</span>}
                  </div>
                  {(docsData.ventas || []).length === 0 ? <p className="text-center text-slate-400 py-6 text-sm">Sin documentos de venta de Cocina Desmontada para este proyecto.</p> :
                  <table className="w-full text-sm"><thead className="text-slate-500"><tr><th className="text-left p-2 text-xs uppercase">Tipo</th><th className="text-left p-2 text-xs uppercase">Fecha</th><th className="text-right p-2 text-xs uppercase">Total</th></tr></thead>
                    <tbody className="divide-y divide-slate-100">{docsData.ventas.map((o, k) => (
                      <tr key={k}><td className="p-2 font-medium">{o.kind === 'pedido' ? 'Pedido' : 'Presupuesto'} cascos {o.expediente && <span className="px-1.5 py-0.5 rounded bg-amber-100 text-amber-700 text-[9px] font-black">🔗 {o.expediente}</span>}</td>
                        <td className="p-2 text-slate-500">{o.createdAt ? new Date(o.createdAt).toLocaleDateString('es-ES') : '—'}</td>
                        <td className="p-2 text-right font-mono font-bold text-emerald-700">{eur(o.total)}</td></tr>
                    ))}</tbody></table>}
                </>
              )}
            </div>
          </div>
        </div>
        );
      })()}

      {/* Modal de conversión: presupuesto → pedido → albarán → factura. SIEMPRE
          pregunta el número del documento de destino, dejando huella de origen/destino. */}
      {convModal && (() => {
        const CONV_META = {
          pedido: { label: 'Pedido', icon: PackageCheck, theme: 'bg-indigo-700 hover:bg-indigo-800' },
          albaran: { label: 'Albarán', icon: Truck, theme: 'bg-purple-700 hover:bg-purple-800' },
          factura: { label: 'Factura', icon: Receipt, theme: 'bg-blue-700 hover:bg-blue-800' },
        };
        const meta = CONV_META[convModal.tipo];
        const Icon = meta.icon;
        return (
        <div className="fixed inset-0 bg-black/60 z-[140] flex items-center justify-center p-4" onClick={() => setConvModal(null)}>
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm overflow-hidden" onClick={e => e.stopPropagation()}>
            <div className={`px-6 py-4 text-white flex items-center gap-3 ${meta.theme.split(' ')[0]}`}>
              <Icon size={20} />
              <div>
                <h3 className="font-black uppercase text-sm">Convertir a {meta.label}</h3>
                <p className="text-[11px] opacity-80">{convModal.row.ref} · {convModal.row.cliente}</p>
              </div>
              <button onClick={() => setConvModal(null)} className="ml-auto hover:bg-white/20 rounded-lg p-1"><X size={18} /></button>
            </div>
            <div className="p-6 space-y-4">
              <p className="text-xs text-slate-500">
                Indica la serie y el número del {meta.label.toLowerCase()}.
                Si los dejas en blanco, se generará automáticamente.
              </p>
              <div className="flex gap-3">
                <div className="w-24">
                  <label className="text-[10px] font-black text-slate-400 uppercase block mb-1">Serie</label>
                  <input value={convModal.serie} onChange={e => setConvModal(p => ({ ...p, serie: e.target.value }))}
                    placeholder="LG" className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm font-bold focus:outline-none focus:border-indigo-400" />
                </div>
                <div className="flex-1">
                  <label className="text-[10px] font-black text-slate-400 uppercase block mb-1">Número</label>
                  <input value={convModal.numero} onChange={e => setConvModal(p => ({ ...p, numero: e.target.value }))}
                    placeholder="2026/001" className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm font-bold focus:outline-none focus:border-indigo-400" />
                </div>
              </div>
              {convModal.serie && convModal.numero && (
                <p className="text-xs font-black text-indigo-700 text-center">
                  Referencia: {convModal.serie}/{convModal.numero}
                </p>
              )}
              <button onClick={doConversion}
                className={`w-full py-3 text-white rounded-xl font-black uppercase text-sm flex items-center justify-center gap-2 ${meta.theme}`}>
                <Icon size={16} />
                Confirmar
              </button>
            </div>
          </div>
        </div>
        );
      })()}
      </>)}
    </div>
  );
};

export default RentabilidadPanel;
