/*
 * © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
 * Gestor Comercial Integrado: Presupuestos, Pedidos, Albaranes y Facturas de Venta.
 */
import React, { useState, useEffect, useMemo } from 'react';
import {
  FileText, Plus, Download, Send, CheckCircle, XCircle, Clock,
  Search, Loader2, Trash2, Edit2, X, Save, AlertTriangle,
  ArrowUpRight, Receipt, Filter, Copy, Users, Truck, ClipboardList,
  Sparkles, Layers, ArrowRight, PackageCheck, FileSpreadsheet, Box
} from 'lucide-react';
import { invoicesAPI, clientsAPI } from '../services/api';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const DOC_TYPES = {
  presupuesto: { label: 'Presupuesto', prefix: 'PRE-2026', color: 'bg-amber-100 text-amber-900 border-amber-300', icon: FileText },
  pedido:      { label: 'Pedido Venta', prefix: 'PED-2026', color: 'bg-blue-100 text-blue-900 border-blue-300',     icon: ClipboardList },
  albaran:     { label: 'Albarán',      prefix: 'ALB-2026', color: 'bg-purple-100 text-purple-900 border-purple-300', icon: Truck },
  factura:     { label: 'Factura',      prefix: 'FACT-2026',color: 'bg-emerald-100 text-emerald-900 border-emerald-300', icon: Receipt },
};

const STATUS_CONFIG = {
  draft:     { label: 'Borrador',  color: 'bg-slate-100 text-slate-600',   icon: FileText },
  issued:    { label: 'Emitido',   color: 'bg-blue-100 text-blue-700',     icon: Send },
  paid:      { label: 'Cobrado / Facturado', color: 'bg-emerald-100 text-emerald-700', icon: CheckCircle },
  overdue:   { label: 'Vencido',   color: 'bg-rose-100 text-rose-700',     icon: AlertTriangle },
  cancelled: { label: 'Cancelado', color: 'bg-slate-100 text-slate-400',   icon: XCircle },
};

const fmt = (v) => new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR' }).format(v || 0);
const fmtDate = (d) => d ? new Date(d).toLocaleDateString('es-ES') : '—';

const EMPTY_FORM = {
  docType: 'factura', // presupuesto | pedido | albaran | factura
  clientName: '', clientEmail: '', clientAddress: '', clientTaxId: '',
  invoiceNumber: '', issueDate: new Date().toISOString().split('T')[0],
  dueDate: new Date(Date.now() + 30*864e5).toISOString().split('T')[0],
  vatRate: 21, irpfRate: 0, notes: '', status: 'draft',
  lines: [{ description: '', quantity: 1, unitPrice: 0, discount: 0, vatRate: 21 }]
};

const Invoices = ({ currentUser, state }) => {
  const [invoices, setInvoices] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [docTypeFilter, setDocTypeFilter] = useState('TODOS');
  const [statusFilter, setStatusFilter] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [sendingEmail, setSendingEmail] = useState(null);
  const [loadError, setLoadError] = useState(false);

  // Volcado / Importación desde app
  const [showVolcadoModal, setShowVolcadoModal] = useState(false);
  const [presupuestosLocales, setPresupuestosLocales] = useState([]);

  useEffect(() => { load(); }, [statusFilter]);

  const load = async () => {
    setLoading(true);
    let failed = false;
    try {
      const [invs, st] = await Promise.all([
        invoicesAPI.getAll(statusFilter || null).catch(() => { failed = true; return []; }),
        invoicesAPI.getStats().catch(() => ({ monthTotal:0, pendingTotal:0, issued:0, paid:0, overdue:0 }))
      ]);

      // Recuperar documentos guardados localmente para asegurar sincronización
      const docsGuardados = JSON.parse(localStorage.getItem('documentos_gestor_comercial') || '[]');
      const combinados = [...(Array.isArray(invs) ? invs : [])];
      
      docsGuardados.forEach(d => {
        if (!combinados.some(x => x.id === d.id || x.invoiceNumber === d.invoiceNumber)) {
          combinados.push(d);
        }
      });

      setInvoices(combinados);
      setStats(st || {});
      setLoadError(failed && combinados.length === 0);
    } catch (e) {
      console.error('Gestor Comercial load error:', e);
      setInvoices([]);
      setLoadError(true);
    }
    finally { setLoading(false); }
  };

  const guardarLocalmente = (doc) => {
    try {
      const prev = JSON.parse(localStorage.getItem('documentos_gestor_comercial') || '[]');
      const next = [doc, ...prev.filter(x => x.id !== doc.id && x.invoiceNumber !== doc.invoiceNumber)];
      localStorage.setItem('documentos_gestor_comercial', JSON.stringify(next));
    } catch {}
  };

  const openNew = async (tipo = 'factura') => {
    const randomNum = Math.floor(100 + Math.random() * 900);
    const prefix = DOC_TYPES[tipo]?.prefix || 'FACT-2026';
    const num = `${prefix}-${randomNum}`;
    setForm({ ...EMPTY_FORM, docType: tipo, invoiceNumber: num });
    setEditingId(null);
    setShowModal(true);
  };

  const openEdit = (inv) => {
    setForm({
      docType: inv.docType || 'factura',
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

  // 🔒 VERIFICACIÓN DE PERMISOS: Solo Admin o el Usuario Asignado pueden validar o modificar cobros
  const puedeRegistrarPago = (doc) => {
    if (!currentUser) return true;
    if (currentUser.isAdmin || currentUser.isGerente || currentUser.canAuthorizePermissions || currentUser.isMaster) return true;
    const asignado = doc.createdByName || doc.vendedor || doc.usuario || '';
    const miNombre = currentUser.clientName || currentUser.username || currentUser.email || '';
    const esAsignado = doc.userId === currentUser.id || (asignado && miNombre && asignado.toLowerCase() === miNombre.toLowerCase());
    return esAsignado;
  };

  // Modal para adjuntar comprobante de pago
  const [modalPago, setModalPago] = useState(null); // { doc, tipo: 'senial' | 'total', importe: number }
  const [metodoPago, setMetodoPago] = useState('Transferencia Bancaria');
  const [comprobanteAdjunto, setComprobanteAdjunto] = useState(null); // { name, type, data }
  const [verComprobanteModal, setVerComprobanteModal] = useState(null);

  const abrirModalPago = (doc, tipo = 'senial') => {
    if (!puedeRegistrarPago(doc)) {
      alert(`⚠️ No tienes permisos para registrar pagos en este documento.\n\nSolo un Administrador o el usuario asignado (${doc.createdByName || doc.vendedor || 'Responsable'}) pueden validar cobros.`);
      return;
    }
    const importe = tipo === 'senial' ? (doc.total || 0) * 0.5 : (doc.senialPagada ? (doc.total || 0) * 0.5 : doc.total);
    setModalPago({ doc, tipo, importe });
    setMetodoPago('Transferencia Bancaria');
    setComprobanteAdjunto(null);
  };

  const handleComprobanteFile = (file) => {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      setComprobanteAdjunto({
        name: file.name,
        type: file.type,
        data: e.target.result
      });
    };
    reader.readAsDataURL(file);
  };

  const confirmarCobroConComprobante = async () => {
    if (!modalPago) return;
    const { doc, tipo, importe } = modalPago;
    const esSenial = tipo === 'senial';
    const randomNum = Math.floor(100 + Math.random() * 900);
    const nuevoNum = esSenial ? `PED-2026-${randomNum}` : doc.invoiceNumber;

    const fechaCobro = new Date().toLocaleDateString('es-ES');
    const usuarioCobro = currentUser?.clientName || currentUser?.username || 'Usuario';

    const registroComprobante = comprobanteAdjunto ? {
      name: comprobanteAdjunto.name,
      type: comprobanteAdjunto.type,
      data: comprobanteAdjunto.data,
      fecha: fechaCobro,
      usuario: usuarioCobro,
      metodo: metodoPago,
      importe: importe
    } : (doc.comprobantePago || null);

    const docActualizado = {
      ...doc,
      docType: esSenial ? 'pedido' : doc.docType,
      invoiceNumber: nuevoNum,
      status: esSenial ? 'partially_paid' : 'paid',
      senialPagada: true,
      senialImporte: esSenial ? importe : (doc.senialImporte || (doc.total * 0.5)),
      comprobantePago: registroComprobante,
      notes: `${esSenial ? 'Señal 50%' : '100% Liquidado'} (${fmt(importe)}) registrado por ${usuarioCobro} vía ${metodoPago} el ${fechaCobro}. ${doc.notes || ''}`
    };

    try { await invoicesAPI.update(doc.id, docActualizado); } catch { guardarLocalmente(docActualizado); }
    alert(`✓ ¡${esSenial ? 'Señal 50%' : 'Pago 100%'} (${fmt(importe)}) registrado con comprobante adjunto!`);
    setModalPago(null);
    load();
  };

  // 🔄 CONVERSIÓN DE DOCUMENTOS EN 1-CLIC CON REGLA 50% / 50%
  const convertirDocumento = async (doc, nuevoTipo) => {
    const conf = DOC_TYPES[nuevoTipo];
    if (!conf) return;

    // Regla estricta: El 50% restante DEBE abonarse antes de entregar el material (Albarán)
    let pagadoAlbaran = doc.status === 'paid';
    if (nuevoTipo === 'albaran' && !pagadoAlbaran) {
      const rest = (doc.total || 0) * 0.5;
      const ok = window.confirm(
        `⚠️ REGLA DE ENTREGA: El 50% restante (${fmt(rest)}) debe abonarse antes de entregar el material.\n\n¿Registrar ahora el pago del 50% restante (${fmt(rest)}) y autorizar la salida del Albarán de Entrega?`
      );
      if (!ok) return;
      pagadoAlbaran = true;
    } else {
      if (!window.confirm(`¿Convertir ${doc.invoiceNumber} (${DOC_TYPES[doc.docType || 'factura']?.label}) a nuevo ${conf.label}?`)) return;
    }

    const randomNum = Math.floor(100 + Math.random() * 900);
    const nuevoNum = `${conf.prefix}-${randomNum}`;

    const nuevoDoc = {
      ...doc,
      id: `doc-${Date.now()}`,
      docType: nuevoTipo,
      invoiceNumber: nuevoNum,
      issueDate: new Date().toISOString().split('T')[0],
      dueDate: new Date(Date.now() + 30 * 864e5).toISOString().split('T')[0],
      status: pagadoAlbaran ? 'paid' : (doc.status || 'draft'),
      budgetNumber: doc.invoiceNumber,
      notes: `Generado a partir de ${doc.invoiceNumber} (${DOC_TYPES[doc.docType || 'factura']?.label}). 50% señal + 50% restante previo a la entrega. ${doc.notes || ''}`
    };

    try {
      await invoicesAPI.create(nuevoDoc);
    } catch {
      guardarLocalmente(nuevoDoc);
    }

    alert(`✓ ¡Creado ${conf.label} ${nuevoNum} con éxito!${nuevoTipo === 'albaran' ? ' (100% Abonado y Autorizado para entrega)' : ''}`);
    load();
  };

  // 📥 VOLCADO DE PRESUPUESTOS DESDE OTROS MÓDULOS (Cocina Montada 3, Cascos, CRM)
  const abrirVolcado = async () => {
    setShowVolcadoModal(true);
    const lista = [];

    // 1. Órdenes de fabricación / Taller
    try {
      const ofs = JSON.parse(localStorage.getItem('ordenes_fabricacion_taller') || '[]');
      ofs.forEach(o => {
        lista.push({
          origen: 'Fábrica / Taller',
          id: o.id,
          cliente: o.cliente,
          ref: o.ref,
          fecha: o.fechaInicio || new Date().toISOString().split('T')[0],
          muebles: o.muebles || [],
          casco: o.casco,
          total: (o.modulos || 1) * 150
        });
      });
    } catch {}

    // 2. Presupuestos backend
    try {
      const r = await fetch(`${API_URL}/api/presupuestos`);
      if (r.ok) {
        const data = await r.json();
        (data.presupuestos || data || []).forEach(p => {
          lista.push({
            origen: 'Cocina Montada 3',
            id: p.id || p._id,
            cliente: p.cliente,
            ref: p.referencia || p.ref,
            fecha: p.fecha ? p.fecha.split('T')[0] : new Date().toISOString().split('T')[0],
            muebles: p.muebles || [],
            total: p.total || p.subtotal || 0,
            acabadoPuerta: p.acabadoPuerta,
            acabadoCasco: p.acabadoCasco
          });
        });
      }
    } catch {}

    setPresupuestosLocales(lista);
  };

  const aplicarVolcadoEnGestor = (item, destinoTipo = 'presupuesto') => {
    const conf = DOC_TYPES[destinoTipo];
    const randomNum = Math.floor(100 + Math.random() * 900);
    const num = `${conf.prefix}-${randomNum}`;

    const lineasVolcadas = (item.muebles && item.muebles.length > 0)
      ? item.muebles.map(m => ({
          description: `Módulo ${m.cod || 'Cocina'} (${m.ancho || 60}x${m.alto || 80} cm) ${m.mano ? `Mano ${m.mano}` : ''} ${m.obs ? `- ${m.obs}` : ''}`,
          quantity: Number(m.qty) || 1,
          unitPrice: Number(m.pvp) || 120,
          discount: 0,
          vatRate: 21
        }))
      : [{
          description: `Proyecto de Cocina ${item.ref || item.id} - ${item.acabadoPuerta || 'Acabado Estándar'}`,
          quantity: 1,
          unitPrice: Number(item.total) || 2500,
          discount: 0,
          vatRate: 21
        }];

    setForm({
      ...EMPTY_FORM,
      docType: destinoTipo,
      invoiceNumber: num,
      clientName: item.cliente || 'Cliente General',
      notes: `Volcado desde ${item.origen} (Ref: ${item.ref || item.id})`,
      lines: lineasVolcadas
    });

    setShowVolcadoModal(false);
    setShowModal(true);
  };

  // Selector de cliente
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

  // Totales desglosados
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
        await invoicesAPI.update(editingId, form).catch(() => guardarLocalmente({ ...form, id: editingId }));
      } else {
        await invoicesAPI.create(form).catch(() => guardarLocalmente({ ...form, id: `doc-${Date.now()}` }));
      }
      setShowModal(false);
      load();
    } catch (e) { alert(e.message); }
    finally { setSaving(false); }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('¿Eliminar este documento comercial?')) return;
    try { await invoicesAPI.delete(id); } catch {}
    try {
      const prev = JSON.parse(localStorage.getItem('documentos_gestor_comercial') || '[]');
      localStorage.setItem('documentos_gestor_comercial', JSON.stringify(prev.filter(x => x.id !== id)));
    } catch {}
    load();
  };

  const handleStatus = async (inv, status) => {
    try { await invoicesAPI.changeStatus(inv.id, status); load(); }
    catch (e) { alert(e.message); }
  };

  const addLine = () => setForm(f => ({ ...f, lines: [...f.lines, { description: '', quantity: 1, unitPrice: 0, discount: 0, vatRate: 21 }] }));
  const removeLine = (i) => setForm(f => ({ ...f, lines: f.lines.filter((_, idx) => idx !== i) }));
  const updateLine = (i, field, value) => setForm(f => ({ ...f, lines: f.lines.map((l, idx) => idx === i ? { ...l, [field]: value } : l) }));

  // 🖨️ GENERADOR DE PDF MULTIDOCUMENTO PROFESIONAL
  const exportarPDFDocumento = async (inv) => {
    try {
      const { jsPDF } = await import('jspdf');
      const autoTable = (await import('jspdf-autotable')).default;
      const pdf = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
      const W = pdf.internal.pageSize.getWidth();
      const M = 14;

      const tipoConf = DOC_TYPES[inv.docType || 'factura'] || DOC_TYPES.factura;
      const tituloDoc = tipoConf.label.toUpperCase();
      const companyBrand = state?.settings?.companyName || currentUser?.empresa || 'FÁBRICA DE COCINAS Y MOBILIARIO';

      // Cabecera elegante
      pdf.setFillColor(15, 23, 42); // slate-900
      pdf.rect(0, 0, W, 25, 'F');
      pdf.setFontSize(14);
      pdf.setFont(undefined, 'bold');
      pdf.setTextColor(255, 255, 255);
      pdf.text(companyBrand, M, 14);

      pdf.setFontSize(11);
      pdf.setTextColor(251, 146, 60); // orange
      pdf.text(`${tituloDoc}: ${inv.invoiceNumber}`, W - M, 14, { align: 'right' });

      // Datos Cliente & Fecha
      let y = 34;
      pdf.setFillColor(248, 250, 252);
      pdf.roundedRect(M, y, W - (M * 2), 24, 3, 3, 'F');

      pdf.setFontSize(9.5);
      pdf.setFont(undefined, 'bold');
      pdf.setTextColor(30, 41, 59);
      pdf.text(`Cliente: ${inv.clientName || 'General'}`, M + 4, y + 8);
      pdf.setFont(undefined, 'normal');
      pdf.setTextColor(100, 116, 139);
      pdf.text(`NIF/CIF: ${inv.clientTaxId || '—'}  ·  Email: ${inv.clientEmail || '—'}`, M + 4, y + 14);
      pdf.text(`Dirección: ${inv.clientAddress || '—'}`, M + 4, y + 20);

      pdf.setFontSize(8.5);
      pdf.setFont(undefined, 'bold');
      pdf.setTextColor(30, 41, 59);
      pdf.text(`Fecha Emisión: ${fmtDate(inv.issueDate)}`, W - M - 4, y + 8, { align: 'right' });
      pdf.text(`Vencimiento: ${fmtDate(inv.dueDate)}`, W - M - 4, y + 14, { align: 'right' });

      y += 30;

      // Tabla de líneas
      const tableLines = (inv.lines || []).map(l => [
        l.description || 'Artículo/Servicio',
        String(l.quantity || 1),
        fmt(l.unitPrice),
        `${l.discount || 0}%`,
        `${l.vatRate || 21}%`,
        fmt((l.quantity || 1) * (l.unitPrice || 0) * (1 - (l.discount || 0)/100))
      ]);

      autoTable(pdf, {
        startY: y,
        head: [['Descripción / Módulo', 'Cant', 'Precio Ud.', 'Dto', 'IVA', 'Subtotal']],
        body: tableLines,
        styles: { fontSize: 8.5, cellPadding: 2.5 },
        headStyles: { fillColor: [30, 41, 59], textColor: [255, 255, 255], fontStyle: 'bold' },
        alternateRowStyles: { fillColor: [248, 250, 252] },
        columnStyles: { 0: { cellWidth: 90 }, 1: { halign: 'center' }, 2: { halign: 'right' }, 3: { halign: 'center' }, 4: { halign: 'center' }, 5: { halign: 'right' } },
        margin: { left: M, right: M },
      });

      let finalY = (pdf.lastAutoTable?.finalY || y + 20) + 8;

      // Totales
      const bx = W - M - 70;
      pdf.setFontSize(9);
      pdf.setFont(undefined, 'normal');
      pdf.setTextColor(51, 65, 85);
      pdf.text('Base Imponible:', bx, finalY);
      pdf.text(fmt(inv.totalBase || inv.total * 0.8), W - M, finalY, { align: 'right' });
      finalY += 5;

      pdf.text('IVA Total:', bx, finalY);
      pdf.text(fmt(inv.totalVat || inv.total * 0.2), W - M, finalY, { align: 'right' });
      finalY += 6;

      pdf.setFillColor(249, 115, 22);
      pdf.roundedRect(bx - 3, finalY, 73, 10, 2, 2, 'F');
      pdf.setFontSize(11);
      pdf.setFont(undefined, 'bold');
      pdf.setTextColor(255, 255, 255);
      pdf.text('TOTAL DOCUMENTO:', bx + 2, finalY + 7);
      pdf.text(fmt(inv.total), W - M - 2, finalY + 7, { align: 'right' });

      // Condición comercial de pago: 50% Señal + 50% Entrega
      finalY += 12;
      pdf.setFontSize(8.5);
      pdf.setFont(undefined, 'bold');
      pdf.setTextColor(30, 41, 59);
      pdf.text('CONDICIONES Y FORMA DE PAGO COMERCIAL:', M, finalY);
      pdf.setFont(undefined, 'normal');
      pdf.setTextColor(71, 85, 105);
      pdf.text(`1. Señal inicial del 50% a la confirmación del pedido: ${fmt((inv.total || 0) * 0.5)}`, M, finalY + 4.5);
      pdf.text(`2. 50% restante a la entrega de mercancía / finalización de instalación: ${fmt((inv.total || 0) * 0.5)}`, M, finalY + 9);

      // Pie de página y firma para Albaranes / Presupuestos
      if (inv.docType === 'albaran') {
        pdf.setFontSize(8);
        pdf.setTextColor(100);
        pdf.text('RECIBÍ Y CONFORMIDAD DE ENTREGA:', M, finalY + 16);
        pdf.rect(M, finalY + 19, 80, 20, 'D');
        pdf.text('Firma y DNI Receptor', M + 4, finalY + 36);
      }

      pdf.save(`${inv.invoiceNumber}_${(inv.clientName || 'Cliente').replace(/\s+/g, '_')}.pdf`);
    } catch (e) {
      alert(`Error al exportar PDF: ${e.message}`);
    }
  };

  const filtered = invoices.filter(inv => {
    const matchTipo = docTypeFilter === 'TODOS' || (inv.docType || 'factura') === docTypeFilter;
    const matchBusqueda = !search ||
      inv.invoiceNumber?.toLowerCase().includes(search.toLowerCase()) ||
      inv.clientName?.toLowerCase().includes(search.toLowerCase());
    return matchTipo && matchBusqueda;
  });

  return (
    <div className="h-full flex flex-col bg-slate-100 overflow-y-auto p-4 sm:p-6 pb-36 space-y-4">
      {/* Cabecera Principal. `hueco-logo` le deja sitio al botón flotante del
          logo: con el menú plegado se le comía el icono y el principio del
          título. */}
      <div className="hueco-logo bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white rounded-3xl p-6 shadow-xl border border-slate-800 flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-orange-600 border border-orange-400/40 flex items-center justify-center shadow-lg shadow-orange-600/30">
            <Receipt size={26} className="text-white" />
          </div>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-black text-white tracking-tight">Gestor Comercial & Facturación</h1>
              <span className="px-2.5 py-0.5 rounded-full bg-orange-500/20 border border-orange-400/30 text-orange-300 text-xs font-black uppercase">
                {invoices.length} Documentos Totales
              </span>
            </div>
            <p className="text-sm text-indigo-200/80 font-medium">
              Gestión unificada de Presupuestos, Pedidos de Venta, Albaranes de Entrega y Facturación Fiscal
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={abrirVolcado}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-2xl font-black text-xs shadow-lg transition-all border border-indigo-400/30"
            title="Volcar un presupuesto de Cocina Montada 3, Cascos o Taller directo al gestor"
          >
            <Sparkles size={16} /> Volcar Presupuesto
          </button>

          <div className="relative group">
            <button className="flex items-center gap-2 px-4 py-2 bg-orange-500 hover:bg-orange-600 text-white rounded-2xl font-black text-xs shadow-lg transition-all">
              <Plus size={16} /> + Crear Documento
            </button>

            <div className="absolute right-0 mt-1 hidden group-hover:block w-48 bg-white rounded-2xl shadow-2xl ring-1 ring-black/10 overflow-hidden text-slate-800 z-50">
              <button onClick={() => openNew('presupuesto')} className="w-full text-left px-3.5 py-2.5 hover:bg-orange-50 font-bold text-xs flex items-center gap-2">
                📄 Presupuesto
              </button>
              <button onClick={() => openNew('pedido')} className="w-full text-left px-3.5 py-2.5 hover:bg-orange-50 font-bold text-xs flex items-center gap-2">
                📋 Pedido Venta
              </button>
              <button onClick={() => openNew('albaran')} className="w-full text-left px-3.5 py-2.5 hover:bg-orange-50 font-bold text-xs flex items-center gap-2">
                🚚 Albarán Entrega
              </button>
              <button onClick={() => openNew('factura')} className="w-full text-left px-3.5 py-2.5 hover:bg-orange-50 font-bold text-xs flex items-center gap-2">
                🧾 Factura Venta
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Pestañas por Tipo de Documento Comercial */}
      <div className="bg-white rounded-3xl p-3 border border-slate-200 shadow-sm flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-1.5 flex-wrap">
          <button
            onClick={() => setDocTypeFilter('TODOS')}
            className={`px-3.5 py-2 rounded-2xl text-xs font-black transition-all ${docTypeFilter === 'TODOS' ? 'bg-slate-900 text-white shadow-md' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}
          >
            📑 Todos ({invoices.length})
          </button>
          <button
            onClick={() => setDocTypeFilter('presupuesto')}
            className={`px-3.5 py-2 rounded-2xl text-xs font-black transition-all flex items-center gap-1.5 ${docTypeFilter === 'presupuesto' ? 'bg-amber-500 text-white shadow-md' : 'bg-amber-50 text-amber-900 border border-amber-200 hover:bg-amber-100'}`}
          >
            📄 Presupuestos ({invoices.filter(x => (x.docType || 'factura') === 'presupuesto').length})
          </button>
          <button
            onClick={() => setDocTypeFilter('pedido')}
            className={`px-3.5 py-2 rounded-2xl text-xs font-black transition-all flex items-center gap-1.5 ${docTypeFilter === 'pedido' ? 'bg-blue-600 text-white shadow-md' : 'bg-blue-50 text-blue-900 border border-blue-200 hover:bg-blue-100'}`}
          >
            📋 Pedidos ({invoices.filter(x => x.docType === 'pedido').length})
          </button>
          <button
            onClick={() => setDocTypeFilter('albaran')}
            className={`px-3.5 py-2 rounded-2xl text-xs font-black transition-all flex items-center gap-1.5 ${docTypeFilter === 'albaran' ? 'bg-purple-600 text-white shadow-md' : 'bg-purple-50 text-purple-900 border border-purple-200 hover:bg-purple-100'}`}
          >
            🚚 Albaranes ({invoices.filter(x => x.docType === 'albaran').length})
          </button>
          <button
            onClick={() => setDocTypeFilter('factura')}
            className={`px-3.5 py-2 rounded-2xl text-xs font-black transition-all flex items-center gap-1.5 ${docTypeFilter === 'factura' ? 'bg-emerald-600 text-white shadow-md' : 'bg-emerald-50 text-emerald-900 border border-emerald-200 hover:bg-emerald-100'}`}
          >
            🧾 Facturas ({invoices.filter(x => (x.docType || 'factura') === 'factura').length})
          </button>
        </div>

        <div className="flex items-center gap-2">
          <Search size={16} className="text-slate-400" />
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Buscar documento, cliente, NIF…"
            className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-bold outline-none w-52"
          />
        </div>
      </div>

      {/* Lista de Documentos */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden divide-y divide-slate-100">
        {loading ? (
          <div className="flex items-center justify-center h-40">
            <Loader2 className="w-8 h-8 text-orange-500 animate-spin" />
          </div>
        ) : filtered.length === 0 ? (
          <div className="p-12 text-center text-slate-400">
            <Receipt className="w-12 h-12 mx-auto mb-2 text-slate-300" />
            <p className="font-black text-slate-700">Sin documentos en esta categoría</p>
            <p className="text-xs text-slate-400 mt-1">Crea un presupuesto, pedido, albarán o factura para comenzar</p>
          </div>
        ) : (
          filtered.map(inv => {
            const tConf = DOC_TYPES[inv.docType || 'factura'] || DOC_TYPES.factura;
            const sConf = STATUS_CONFIG[inv.status] || STATUS_CONFIG.draft;
            const TIcon = tConf.icon;
            
            const estaPagado = inv.status === 'paid';
            const estaVencido = inv.status === 'issued' && inv.dueDate && new Date(inv.dueDate) < new Date();

            return (
              <div key={inv.id} className="p-4 hover:bg-slate-50 transition-colors flex items-center justify-between gap-4 flex-wrap">
                <div className="flex items-center gap-3">
                  <div className={`p-3 rounded-2xl border ${tConf.color} shrink-0`}>
                    <TIcon size={20} />
                  </div>
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-mono font-black text-sm text-slate-900">{inv.invoiceNumber}</span>
                      <span className={`px-2 py-0.5 rounded-md text-[10px] font-black uppercase border ${tConf.color}`}>{tConf.label}</span>
                      
                      {/* Badge de Estado de Pago Destacado */}
                      {estaPagado ? (
                        <span className="px-2.5 py-0.5 rounded-md text-[10px] font-black uppercase bg-emerald-600 text-white flex items-center gap-1 shadow-sm">
                          <CheckCircle size={12} /> 💳 100% PAGADO / LIQUIDADO
                        </span>
                      ) : (inv.status === 'partially_paid' || inv.senialPagada) ? (
                        <span className="px-2.5 py-0.5 rounded-md text-[10px] font-black uppercase bg-blue-600 text-white flex items-center gap-1 shadow-sm">
                          <CheckCircle size={12} /> 💳 SEÑAL 50% COBRADA ({fmt((inv.total || 0) * 0.5)})
                        </span>
                      ) : estaVencido ? (
                        <span className="px-2.5 py-0.5 rounded-md text-[10px] font-black uppercase bg-rose-100 text-rose-800 border border-rose-300 flex items-center gap-1">
                          <AlertTriangle size={12} /> 🚨 VENCIDO (IMPAGADO)
                        </span>
                      ) : (
                        <span className={`px-2 py-0.5 rounded-md text-[10px] font-black uppercase ${sConf.color}`}>
                          ⏳ PENDIENTE SEÑAL 50%
                        </span>
                      )}
                    </div>
                    <h4 className="font-black text-sm text-slate-800 mt-0.5">{inv.clientName}</h4>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Emisión: {fmtDate(inv.issueDate)} · Vence: {fmtDate(inv.dueDate)} {inv.notes ? `· ${inv.notes}` : ''}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-4 flex-wrap">
                  <div className="text-right">
                    <p className="text-lg font-black text-slate-900">{fmt(inv.total)}</p>
                    <p className="text-[10px] font-bold text-slate-400">
                      {(inv.status === 'partially_paid' || inv.senialPagada)
                        ? `Pendiente (50%): ${fmt((inv.total || 0) * 0.5)}`
                        : `Base ${fmt(inv.totalBase || inv.total * 0.8)}`}
                    </p>
                  </div>

                  {/* Acciones & Pipeline de Conversión */}
                  <div className="flex items-center gap-1.5 flex-wrap">
                    {/* Botón para ver comprobante de pago archivado */}
                    {inv.comprobantePago && (
                      <button
                        onClick={() => setVerComprobanteModal(inv.comprobantePago)}
                        className="px-2.5 py-1.5 rounded-xl bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 text-xs font-bold transition-all flex items-center gap-1"
                        title="Ver comprobante de pago / pantallazo archivado"
                      >
                        📎 Comprobante
                      </button>
                    )}

                    {/* Botón para Cobrar Señal 50% y Confirmar Pedido en Presupuestos */}
                    {(inv.docType === 'presupuesto' || !inv.docType) && !inv.senialPagada && (
                      <button
                        onClick={() => abrirModalPago(inv, 'senial')}
                        className="px-3 py-1.5 rounded-xl bg-amber-500 hover:bg-amber-600 text-white text-xs font-black shadow-md transition-all flex items-center gap-1.5"
                        title="Registrar cobro de la señal del 50% con comprobante y confirmar automáticamente como Pedido de Venta"
                      >
                        <CheckCircle size={13} /> 💳 Cobrar 50% Señal ({fmt((inv.total || 0) * 0.5)}) ➔ Confirmar Pedido
                      </button>
                    )}

                    {/* Botón directo de 1 clic para Cambiar Estado de Pago Total */}
                    {estaPagado ? (
                      <button
                        onClick={() => {
                          if (!puedeRegistrarPago(inv)) {
                            alert(`⚠️ Solo el Administrador o el usuario asignado (${inv.createdByName || 'Responsable'}) pueden modificar estados de pago.`);
                            return;
                          }
                          handleStatus(inv, 'issued');
                        }}
                        className="px-2.5 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold transition-all flex items-center gap-1"
                        title="Marcar este pedido/factura como pendiente de cobro"
                      >
                        ↩️ Pendiente
                      </button>
                    ) : (
                      <button
                        onClick={() => abrirModalPago(inv, 'total')}
                        className="px-2.5 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-black shadow-md transition-all flex items-center gap-1"
                        title="Marcar este pedido/factura como 100% PAGADO adjuntando comprobante"
                      >
                        <CheckCircle size={13} /> 💳 Liquidar 100%
                      </button>
                    )}
                    {/* Botones de Conversión rápida */}
                    {(inv.docType === 'presupuesto' || !inv.docType) && (
                      <button
                        onClick={() => convertirDocumento(inv, 'pedido')}
                        className="px-2.5 py-1.5 rounded-xl bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-200 text-xs font-bold transition-all flex items-center gap-1"
                        title="Convertir este presupuesto a Pedido de Venta"
                      >
                        <ArrowRight size={13} /> Pedido
                      </button>
                    )}

                    {inv.docType === 'pedido' && (
                      <>
                        <button
                          onClick={() => convertirDocumento(inv, 'albaran')}
                          className="px-2.5 py-1.5 rounded-xl bg-purple-50 text-purple-700 hover:bg-purple-100 border border-purple-200 text-xs font-bold transition-all flex items-center gap-1"
                          title="Generar Albarán de Entrega"
                        >
                          <Truck size={13} /> Albarán
                        </button>
                        <button
                          onClick={() => convertirDocumento(inv, 'factura')}
                          className="px-2.5 py-1.5 rounded-xl bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border border-emerald-200 text-xs font-bold transition-all flex items-center gap-1"
                          title="Facturar este pedido"
                        >
                          <Receipt size={13} /> Facturar
                        </button>
                      </>
                    )}

                    {inv.docType === 'albaran' && (
                      <button
                        onClick={() => convertirDocumento(inv, 'factura')}
                        className="px-2.5 py-1.5 rounded-xl bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border border-emerald-200 text-xs font-bold transition-all flex items-center gap-1"
                        title="Convertir albarán en Factura de Venta"
                      >
                        <Receipt size={13} /> Facturar Albarán
                      </button>
                    )}

                    {/* Descarga PDF */}
                    <button
                      onClick={() => exportarPDFDocumento(inv)}
                      className="p-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl transition-all"
                      title="Descargar PDF Oficial"
                    >
                      <Download size={15} />
                    </button>

                    <button
                      onClick={() => openEdit(inv)}
                      className="p-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-600 rounded-xl transition-all"
                      title="Editar"
                    >
                      <Edit2 size={15} />
                    </button>

                    <button
                      onClick={() => handleDelete(inv.id)}
                      className="p-2 bg-rose-50 hover:bg-rose-100 text-rose-500 rounded-xl transition-all"
                      title="Eliminar"
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Modal Volcar Presupuestos de App */}
      {showVolcadoModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl p-6 shadow-2xl max-w-2xl w-full max-h-[85vh] overflow-y-auto space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-black text-slate-900 text-base flex items-center gap-2">
                <Sparkles size={18} className="text-indigo-600" /> Volcar Presupuestos a Gestor Comercial
              </h3>
              <button onClick={() => setShowVolcadoModal(false)} className="p-1.5 text-slate-400 hover:bg-slate-100 rounded-xl">
                <X size={18} />
              </button>
            </div>

            <p className="text-xs text-slate-500">
              Selecciona un presupuesto guardado en la aplicación para cargarlo automáticamente en el gestor:
            </p>

            <div className="space-y-2 max-h-96 overflow-y-auto divide-y divide-slate-100">
              {presupuestosLocales.map((p, idx) => (
                <div key={p.id || idx} className="pt-2.5 flex items-center justify-between gap-3">
                  <div>
                    <span className="text-[10px] font-black uppercase text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded-md">{p.origen}</span>
                    <h4 className="font-black text-sm text-slate-800 mt-1">{p.cliente} · <span className="text-slate-500 font-normal">{p.ref}</span></h4>
                    <p className="text-xs text-slate-400">Fecha: {p.fecha} · Total: {fmt(p.total)}</p>
                  </div>

                  <div className="flex items-center gap-1.5">
                    <button
                      onClick={() => aplicarVolcadoEnGestor(p, 'presupuesto')}
                      className="px-3 py-1.5 rounded-xl bg-amber-500 text-white font-bold text-xs hover:bg-amber-600 transition-all"
                    >
                      📄 Presupuesto
                    </button>
                    <button
                      onClick={() => aplicarVolcadoEnGestor(p, 'pedido')}
                      className="px-3 py-1.5 rounded-xl bg-blue-600 text-white font-bold text-xs hover:bg-blue-700 transition-all"
                    >
                      📋 Pedido
                    </button>
                  </div>
                </div>
              ))}
              {presupuestosLocales.length === 0 && (
                <p className="p-6 text-center text-slate-400 text-xs">No se encontraron presupuestos en la memoria local.</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Modal Crear / Editar Documento */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl p-6 shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-black text-slate-900 text-base">
                {editingId ? 'Editar Documento' : `Nuevo ${DOC_TYPES[form.docType]?.label || 'Documento'}`}
              </h3>
              <button onClick={() => setShowModal(false)} className="p-1.5 text-slate-400 hover:bg-slate-100 rounded-xl">
                <X size={18} />
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              <div>
                <label className="block text-slate-600 font-bold mb-1">Tipo de Documento:</label>
                <select
                  value={form.docType}
                  onChange={e => setForm(f => ({ ...f, docType: e.target.value }))}
                  className="w-full px-3 py-2 border border-slate-200 rounded-xl font-bold text-slate-800 bg-white"
                >
                  <option value="presupuesto">📄 Presupuesto Comercial</option>
                  <option value="pedido">📋 Pedido de Venta</option>
                  <option value="albaran">🚚 Albarán de Entrega</option>
                  <option value="factura">🧾 Factura de Venta</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-600 font-bold mb-1">Número Documento:</label>
                <input
                  value={form.invoiceNumber}
                  onChange={e => setForm(f => ({ ...f, invoiceNumber: e.target.value }))}
                  className="w-full px-3 py-2 border border-slate-200 rounded-xl font-bold font-mono text-slate-800"
                />
              </div>

              <div>
                <label className="block text-slate-600 font-bold mb-1">Cliente:</label>
                <div className="flex items-center gap-1.5">
                  <input
                    value={form.clientName}
                    onChange={e => setForm(f => ({ ...f, clientName: e.target.value }))}
                    placeholder="Nombre del cliente"
                    className="w-full px-3 py-2 border border-slate-200 rounded-xl font-bold text-slate-800"
                  />
                  <button onClick={openClientPicker} className="p-2 bg-indigo-50 text-indigo-600 rounded-xl hover:bg-indigo-100 shrink-0">
                    <Users size={16} />
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-slate-600 font-bold mb-1">NIF/CIF Cliente:</label>
                <input
                  value={form.clientTaxId}
                  onChange={e => setForm(f => ({ ...f, clientTaxId: e.target.value }))}
                  placeholder="B12345678"
                  className="w-full px-3 py-2 border border-slate-200 rounded-xl font-bold text-slate-800"
                />
              </div>
            </div>

            {/* Lineas de Módulos / Artículos */}
            <div className="space-y-2 pt-2 border-t border-slate-100">
              <div className="flex items-center justify-between">
                <span className="text-xs font-black uppercase text-slate-400">Líneas de Módulos / Artículos</span>
                <button onClick={addLine} className="text-xs font-bold text-orange-600 hover:text-orange-700 flex items-center gap-1">
                  <Plus size={14} /> Añadir Línea
                </button>
              </div>

              {form.lines.map((l, idx) => (
                <div key={idx} className="grid grid-cols-12 gap-2 items-center text-xs">
                  <input
                    value={l.description}
                    onChange={e => updateLine(idx, 'description', e.target.value)}
                    placeholder="Descripción mueble/módulo"
                    className="col-span-5 px-3 py-1.5 border border-slate-200 rounded-xl font-bold"
                  />
                  <input
                    type="number"
                    value={l.quantity}
                    onChange={e => updateLine(idx, 'quantity', parseFloat(e.target.value) || 0)}
                    placeholder="Cant"
                    className="col-span-2 px-2 py-1.5 border border-slate-200 rounded-xl font-bold text-center"
                  />
                  <input
                    type="number"
                    value={l.unitPrice}
                    onChange={e => updateLine(idx, 'unitPrice', parseFloat(e.target.value) || 0)}
                    placeholder="Precio €"
                    className="col-span-3 px-2 py-1.5 border border-slate-200 rounded-xl font-bold"
                  />
                  <button onClick={() => removeLine(idx)} className="col-span-2 p-1.5 text-rose-500 hover:bg-rose-50 rounded-xl">
                    <Trash2 size={15} />
                  </button>
                </div>
              ))}
            </div>

            <div className="flex justify-end gap-2 pt-4 border-t border-slate-100">
              <button onClick={() => setShowModal(false)} className="px-4 py-2 rounded-xl border border-slate-200 font-bold text-xs">
                Cancelar
              </button>
              <button onClick={handleSave} disabled={saving} className="px-5 py-2 rounded-xl bg-orange-500 text-white font-black text-xs shadow-md">
                {saving ? 'Guardando…' : 'Guardar Documento'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Picker de Clientes */}
      {clientPicker && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl p-5 max-w-md w-full space-y-3">
            <div className="flex justify-between items-center border-b pb-2">
              <h4 className="font-bold text-sm">Seleccionar Cliente CRM</h4>
              <button onClick={() => setClientPicker(false)}><X size={16} /></button>
            </div>
            <div className="space-y-1 max-h-60 overflow-y-auto">
              {clientList.map((c, i) => (
                <button key={i} onClick={() => pickClient(c)} className="w-full text-left p-2 hover:bg-orange-50 rounded-xl text-xs font-bold block">
                  {c.nombre} · <span className="text-slate-400 font-normal">{c.cif || c.nif || ''}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Modal Registrar Cobro y Adjuntar Comprobante (PDF / Pantallazo) */}
      {modalPago && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl p-6 shadow-2xl max-w-lg w-full space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-black text-slate-900 text-base flex items-center gap-2">
                <CheckCircle className="text-emerald-600" size={20} /> Registrar Cobro & Adjuntar Comprobante
              </h3>
              <button onClick={() => setModalPago(null)} className="p-1.5 text-slate-400 hover:bg-slate-100 rounded-xl">
                <X size={18} />
              </button>
            </div>

            <div className="bg-emerald-50 border border-emerald-200 p-3 rounded-2xl text-xs font-bold text-emerald-900 flex justify-between items-center">
              <span>Documento: {modalPago.doc.invoiceNumber}</span>
              <span className="font-mono text-base font-black text-emerald-700">{fmt(modalPago.importe)}</span>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-700 font-bold mb-1">Método de Pago:</label>
                <select
                  value={metodoPago}
                  onChange={e => setMetodoPago(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-xl font-bold text-slate-800 bg-white"
                >
                  <option value="Transferencia Bancaria">🏦 Transferencia Bancaria</option>
                  <option value="Tarjeta de Crédito / TPV">💳 Tarjeta de Crédito / TPV</option>
                  <option value="Efectivo / Contado">💶 Efectivo / Contado</option>
                  <option value="Financiación">📑 Financiación / Recibo</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-700 font-bold mb-1">
                  Adjuntar Comprobante (PDF o Pantallazo de Pago):
                </label>
                <input
                  type="file"
                  accept="application/pdf,image/*"
                  onChange={e => handleComprobanteFile(e.target.files?.[0])}
                  className="w-full text-xs font-semibold file:mr-3 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-black file:bg-indigo-600 file:text-white hover:file:bg-indigo-700"
                />
                {comprobanteAdjunto && (
                  <p className="mt-1.5 text-[11px] font-bold text-emerald-600 flex items-center gap-1">
                    ✓ Archivo listo: {comprobanteAdjunto.name}
                  </p>
                )}
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
              <button onClick={() => setModalPago(null)} className="px-4 py-2.5 rounded-xl border border-slate-200 font-bold text-xs">
                Cancelar
              </button>
              <button
                onClick={confirmarCobroConComprobante}
                className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-black text-xs shadow-md flex items-center gap-2"
              >
                <CheckCircle size={15} /> Confirmar & Archivar Cobro
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal Visualizador de Comprobante Archivado */}
      {verComprobanteModal && (
        <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4" onClick={() => setVerComprobanteModal(null)}>
          <div className="bg-white rounded-3xl p-6 shadow-2xl max-w-2xl w-full max-h-[85vh] overflow-y-auto space-y-4" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h3 className="font-black text-slate-900 text-base">Comprobante de Pago Archivado</h3>
                <p className="text-xs text-slate-500 font-medium">
                  Registrado por {verComprobanteModal.usuario} el {verComprobanteModal.fecha} vía {verComprobanteModal.metodo} ({fmt(verComprobanteModal.importe)})
                </p>
              </div>
              <button onClick={() => setVerComprobanteModal(null)} className="p-1.5 text-slate-400 hover:bg-slate-100 rounded-xl">
                <X size={18} />
              </button>
            </div>

            {verComprobanteModal.data ? (
              verComprobanteModal.type?.includes('image') || verComprobanteModal.data.startsWith('data:image') ? (
                <img src={verComprobanteModal.data} alt="Comprobante" className="w-full rounded-2xl border border-slate-200 max-h-96 object-contain" />
              ) : (
                <iframe src={verComprobanteModal.data} title="Comprobante PDF" className="w-full h-96 rounded-2xl border border-slate-200" />
              )
            ) : (
              <p className="text-center text-slate-400 py-8 text-xs font-bold">Comprobante validado electrónicamente sin archivo adjunto.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Invoices;
