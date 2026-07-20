import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  FileText, Upload, Sparkles, Plus, Trash2, X, Save, Euro,
  Receipt, ClipboardList, FileCheck, Eye, Loader2, RefreshCw,
  ArrowUp, ArrowDown, Filter, Files, ChevronLeft, ChevronRight, Truck, Users,
  Lock, Unlock
} from 'lucide-react';
import { clientsAPI, authHeaders } from '../services/api';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const TABS = [
  { key: 'presupuesto', label: 'Presupuesto', icon: ClipboardList, singular: 'presupuesto', plural: 'presupuestos' },
  { key: 'pedido', label: 'Pedido', icon: Receipt, singular: 'pedido', plural: 'pedidos' },
  { key: 'albaran', label: 'Albarán', icon: Truck, singular: 'albarán', plural: 'albaranes' },
  { key: 'factura', label: 'Factura de venta', icon: FileCheck, singular: 'factura', plural: 'facturas' },
];

const NEXT_DOC_TYPE = { presupuesto: 'pedido', pedido: 'albaran', albaran: 'factura' };

const eur = (n) => `${(Number(n) || 0).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} \u20AC`;
const normRef = (v) => String(v || '').toUpperCase().replace(/[^A-Z0-9]/g, '');
// Limpia la referencia visible: elimina espacios alrededor de '/' y al inicio/fin
// para que 'LG26 / 57' se guarde y filtre como 'LG26/57'
const cleanRef = (v) => String(v || '').trim().replace(/\s*\/\s*/g, '/').replace(/\s+/g, ' ');

const fileToB64 = (file) => new Promise((res, rej) => {
  const fr = new FileReader();
  fr.onload = () => res(fr.result);
  fr.onerror = rej;
  fr.readAsDataURL(file);
});

const openDoc = (dataUrl, mime) => {
  try {
    let b64 = dataUrl, m = mime || 'application/octet-stream';
    if (typeof dataUrl === 'string' && dataUrl.startsWith('data:')) {
      const comma = dataUrl.indexOf(',');
      m = dataUrl.slice(5, dataUrl.indexOf(';')) || m;
      b64 = dataUrl.slice(comma + 1);
    }
    const bin = atob(b64);
    const bytes = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    const url = URL.createObjectURL(new Blob([bytes], { type: m }));
    window.open(url, '_blank');
  } catch (e) {
    alert('No se pudo abrir el documento');
  }
};

// Extraer numero de referencia para ordenar numericamente (ej: "LG26 / 15" -> 15)
const extractRefNumber = (ref) => {
  if (!ref) return 999999;
  const match = ref.match(/(\d+)\s*$/);
  return match ? parseInt(match[1], 10) : 999999;
};

const RentabilidadLineas = ({ currentUser, openRef, onOpenedRef, onBackToReport }) => {
  const [docType, setDocType] = useState('factura');
  const [converting, setConverting] = useState('');
  const [fichas, setFichas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editor, setEditor] = useState(null);
  const [viewing, setViewing] = useState(null);
  // Desbloqueo master: las fichas con visto bueno del controller quedan bloqueadas
  // (no se pueden modificar, borrar ni desmarcar). Solo el master las desbloquea
  // manteniendo pulsada la tecla Shift un rato (secuencia que solo él conoce).
  const esMaster = !!(currentUser?.isAdmin || currentUser?.isPrimaryAdmin || currentUser?.isMaster);
  const [masterUnlock, setMasterUnlock] = useState(false);
  const [parsing, setParsing] = useState(false);
  const [parsingMulti, setParsingMulti] = useState(false);
  const [multiProgress, setMultiProgress] = useState({ current: 0, total: 0 });
  const [matching, setMatching] = useState(false);
  const [feeding, setFeeding] = useState(false);
  const [saving, setSaving] = useState(false);

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

  // Ordenacion
  const [sortColumn, setSortColumn] = useState('fecha');
  const [sortDirection, setSortDirection] = useState('desc');

  // Paginacion
  const [pageSize, setPageSize] = useState(25);
  const [currentPage, setCurrentPage] = useState(1);
  // Clientes ya importados (para consultar y filtrar la tabla por cliente)
  const [clientsModal, setClientsModal] = useState(false);
  const [clients, setClients] = useState([]);
  const [clientsQ, setClientsQ] = useState('');
  const openClients = async () => {
    setClientsModal(true);
    try { const c = await clientsAPI.getAll(); setClients(c || []); } catch { setClients([]); }
  };

  // ── Revisión de controller: marcar/desmarcar que la factura y sus márgenes han sido revisados ──
  const [togglingRevision, setTogglingRevision] = useState('');
  const toggleRevision = async (e, f) => {
    e.stopPropagation();
    const yaRevisada = !!f.revisada;
    // Desmarcar el visto bueno del controller: solo el master con el desbloqueo activo.
    if (yaRevisada && !(esMaster && masterUnlock)) {
      alert('Ficha con visto bueno del controller: bloqueada.\n\nPara desmarcarla, el master debe mantener pulsada la tecla Shift un par de segundos (desbloqueo) y volver a intentarlo.');
      return;
    }
    // No dejar dar el visto bueno a una VENTA real con margen 0/negativo o sin costes.
    // Los ABONOS/rectificativas (venta total ≤ 0) sí se pueden revisar (su margen negativo es correcto).
    if (!yaRevisada) {
      const tt = f.totals || totals(f.lines);
      const esAbono = (Number(tt.venta) || 0) <= 0;
      const faltanCostes = (tt.venta > 0) && !(tt.coste > 0) && !((f.costesProyecto || 0) > 0);
      if (!esAbono && (Number(tt.margen) || 0) <= 0) {
        alert(`No se puede marcar como REVISADA: el margen es ${eur(tt.margen)} (0 o negativo).\n\nRevisa/corrige la venta o el coste de las líneas antes de dar el visto bueno.`);
        return;
      }
      if (faltanCostes) {
        alert('No se puede marcar como REVISADA: la factura tiene venta pero NO tiene costes cargados (el margen no es real).\n\nAlimenta los costes (💰) o asígnalos antes de dar el visto bueno.');
        return;
      }
    }
    const accion = yaRevisada ? 'desmarcar la revisión' : 'marcar como REVISADA';
    if (!window.confirm(`¿Deseas ${accion} la factura "${f.ref || f.id}"?`)) return;
    setTogglingRevision(f.id);
    try {
      const r = await fetch(`${API_URL}/api/rentabilidad/fichas/${f.id}/revision`, {
        method: 'PATCH',
        headers: authHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({ revisada: !yaRevisada }),
      });
      if (!r.ok) {
        const err = await r.json().catch(() => ({}));
        throw new Error(err.detail || `Error ${r.status}`);
      }
      // Actualizar la ficha en local sin recargar todo
      const data = await r.json();
      setFichas(prev => prev.map(x => x.id === f.id
        ? { ...x, revisada: data.revisada, revisadaPor: data.revisadaPor, revisadaAt: data.revisadaAt }
        : x
      ));
    } catch (err) {
      alert('Error al cambiar revisión: ' + err.message);
    } finally {
      setTogglingRevision('');
    }
  };

  // ── Bandeja IA: arrastrar documento → clasificar → autorizar destino ──
  const [inbox, setInbox] = useState(null); // { fileB64, mime, name, loading, prop, saving, error }
  const [dragOver, setDragOver] = useState(false);
  const readAsB64 = (file) => new Promise((res) => { const fr = new FileReader(); fr.onload = () => res(String(fr.result)); fr.onerror = () => res(null); fr.readAsDataURL(file); });
  const clasificarDoc = async (file) => {
    if (!file) return;
    const b64 = await readAsB64(file);
    setInbox({ fileB64: b64, mime: file.type, name: file.name, loading: true, prop: null, error: '' });
    try {
      const r = await fetch(`${API_URL}/api/rentabilidad/inbox-classify`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ fileBase64: b64 }) });
      const d = await r.json();
      if (!r.ok || !d.success) throw new Error(d.detail || d.error || 'No se pudo clasificar');
      setInbox(s => ({ ...s, loading: false, prop: { ...d.proposal, clientCode: '' } }));
    } catch (e) { setInbox(s => ({ ...s, loading: false, error: e.message })); }
  };
  const setProp = (k, v) => setInbox(s => ({ ...s, prop: { ...s.prop, [k]: v } }));
  const confirmarInbox = async () => {
    const p = inbox?.prop; if (!p) return;
    setInbox(s => ({ ...s, saving: true, error: '' }));
    try {
      if (p.kind === 'coste') {
        const importe = Number(p.total) || 0;
        const target = (fichas || []).find(f => normRef(f.ref) === normRef(p.projectRef || ''));
        // Opción B: si se elige una factura de venta Y una línea, el coste SE SUMA al coste
        // de esa línea (o crea una línea nueva de coste) y baja su margen. Se guarda la ficha.
        const repMulti = p.costeMulti && p.costeReparto && Object.values(p.costeReparto).some(v => Number(v) > 0);
        if (target && (p.costeLineId || repMulti)) {
          // Aviso claro si la factura destino tiene el visto bueno del controller (bloqueada).
          if (bloqueada(target)) {
            setInbox(s => ({ ...s, saving: false, error: `La factura ${target.ref} está revisada por el controller (bloqueada). Desbloquéala (master, manteniendo Shift) o quítale el visto bueno antes de asignarle costes.` }));
            return;
          }
          const fr = await fetch(`${API_URL}/api/rentabilidad/fichas/${target.id}`);
          const full = await fr.json();
          let lines = (full.lines || []).map(l => ({ ...l }));
          if (repMulti) {
            // Repartir el coste entre varias líneas: sumar a cada una su importe asignado.
            const rep = p.costeReparto || {};
            lines = lines.map(l => { const add = Number(rep[l.id]) || 0; return add ? { ...l, coste: (Number(l.coste) || 0) + add } : l; });
          } else if (p.costeLineId === '__new__') {
            lines.push({ id: `ln-${Date.now()}`, ref: '', concepto: `Coste ${p.proveedor || ''}`.trim() || (p.resumen || 'Coste proveedor'), cantidad: 1, venta: 0, coste: importe });
          } else {
            lines = lines.map(l => l.id === p.costeLineId ? { ...l, coste: (Number(l.coste) || 0) + importe } : l);
          }
          const sr = await fetch(`${API_URL}/api/rentabilidad/fichas`, { method: 'POST', headers: authHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({ ...full, lines }) });
          if (!sr.ok) throw new Error((await sr.json().catch(() => ({}))).detail || 'No se pudo guardar el coste en la factura');
          // adjuntar la factura del proveedor como documento de coste de la ficha
          try { await fetch(`${API_URL}/api/rentabilidad/fichas/${target.id}/docs`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ fileBase64: inbox.fileB64, docMime: inbox.mime, docName: inbox.name, kind: 'coste' }) }); } catch {}
        } else {
          const r = await fetch(`${API_URL}/api/project-costs`, { method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ projectRef: p.projectRef || p.ref, proveedor: p.proveedor || '', concepto: p.resumen || p.ref || 'Factura proveedor', categoria: p.categoria || 'OTROS', importe, source: 'ia', docBase64: inbox.fileB64, docMime: inbox.mime, docName: inbox.name }) });
          if (!r.ok) throw new Error((await r.json()).detail || 'Error');
        }
      } else if (p.kind === 'ingreso') {
        const r = await fetch(`${API_URL}/api/rentabilidad/ingresos`, { method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ importe: Number(p.total) || 0, cliente: p.cliente || '', clientCode: p.clientCode || '', projectRef: p.projectRef || '', fecha: p.fecha || '', docBase64: inbox.fileB64, docMime: inbox.mime, docName: inbox.name, createdBy: currentUser?.id }) });
        if (!r.ok) throw new Error((await r.json()).detail || 'Error');
      } else { // venta
        const lines = (p.lines && p.lines.length) ? p.lines.map(l => ({ concepto: l.concepto || '', venta: Number(l.importe || l.venta) || 0, coste: 0 })) : [{ concepto: p.resumen || 'Documento', venta: Number(p.total) || 0, coste: 0 }];
        const r = await fetch(`${API_URL}/api/rentabilidad/fichas`, { method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ docType: p.docType || 'factura', ref: cleanRef(p.ref || ''), cliente: p.cliente || '', clienteCodigo: p.clientCode || '', fecha: p.fecha || '', lines, projectRef: p.projectRef || '', createdBy: currentUser?.id, createdByName: currentUser?.clientName || currentUser?.username }) });
        if (!r.ok) throw new Error((await r.json()).detail || 'Error');
        const created = await r.json().catch(() => ({}));
        const fid = created?.ficha?.id;
        if (fid && inbox.fileB64) { try { await fetch(`${API_URL}/api/rentabilidad/fichas/${fid}/docs`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ fileBase64: inbox.fileB64, docMime: inbox.mime, docName: inbox.name }) }); } catch {} }
      }
      setInbox(null); load();
    } catch (e) { setInbox(s => ({ ...s, saving: false, error: e.message })); }
  };

  const load = useCallback(async () => {
    setLoading(true);
    try {
      // Cada usuario ve SOLO sus documentos (los que sube). Admin/dirección ven todos.
      const elevated = currentUser?.isAdmin || currentUser?.isGerente
        || currentUser?.isDirectorComercial || currentUser?.isResponsableDelegacion
        || currentUser?.isDirectorFabrica;
      const qs = (!elevated && currentUser?.id) ? `?userId=${encodeURIComponent(currentUser.id)}` : '';
      const r = await fetch(`${API_URL}/api/rentabilidad/fichas${qs}`);
      setFichas(await r.json());
    } catch { /* noop */ } finally { setLoading(false); }
    // Cuenta de clientes en vivo (ademas de la lista que se abre bajo demanda con "Clientes"),
    // para ver crecer el numero mientras se importan facturas que dan de alta clientes nuevos.
    try { const c = await clientsAPI.getAll(); setClients(c || []); } catch { /* noop */ }
  }, [currentUser]);

  useEffect(() => { load(); }, [load]);

  // Coste EFECTIVO: en un abono (línea con venta negativa) el coste también resta
  // (se revierte la venta, no se vuelve a costar la mercancía). Así el margen neto cuadra.
  const costeEfectivo = (venta, coste) => (Number(venta) || 0) < 0 ? -Math.abs(Number(coste) || 0) : (Number(coste) || 0);
  const totals = (lines) => {
    const venta = (lines || []).reduce((s, l) => s + (Number(l.venta) || 0), 0);
    const coste = (lines || []).reduce((s, l) => s + costeEfectivo(l.venta, l.coste), 0);
    const margen = venta - coste;
    // % unificado = incremento sobre el coste (margen / coste), coherente con el resto de la app
    return { venta, coste, margen, margenPct: coste > 0 ? (margen / coste * 100) : 0 };
  };

  // Normaliza el tipo de documento detectado por la IA a uno de los 4 válidos.
  const VALID_DOCTYPES = ['presupuesto', 'pedido', 'albaran', 'factura'];
  const normDocType = (t) => {
    const s = (t || '').toString().trim().toLowerCase()
      .normalize('NFD').replace(/[\u0300-\u036f]/g, ''); // quita acentos (albarán→albaran)
    if (s.includes('presup')) return 'presupuesto';
    if (s.includes('pedido')) return 'pedido';
    if (s.includes('albar')) return 'albaran';
    if (s.includes('factur')) return 'factura';
    return VALID_DOCTYPES.includes(s) ? s : '';
  };

  // ── Subir UN documento de venta ──
  const handleSaleDoc = async (e) => {
    const file = e.target.files?.[0]; e.target.value = '';
    if (!file) return;
    setParsing(true);
    try {
      const b64 = await fileToB64(file);
      const r = await fetch(`${API_URL}/api/rentabilidad/parse-sale-doc`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fileBase64: b64 }),
      });
      if (!r.ok) { alert(`Error del servidor (${r.status}): ${r.statusText}`); return; }
      const data = await r.json();
      if (!data.success) { alert(data.error || 'No se pudo leer el documento'); return; }
      setEditor({
        ref: cleanRef(data.data.ref || ''),
        cliente: data.data.cliente || '',
        clienteCodigo: data.data.clienteCodigo || '',
        fecha: data.data.fecha || '',
        docType: normDocType(data.data.docType) || docType,
        lines: data.data.lines || [],
        saleDoc: { b64, name: file.name },
        costDocs: [],
        existingDocs: [],
      });
    } catch (err) { alert(`Error al subir el documento: ${err?.message || err}`); }
    finally { setParsing(false); }
  };

  // ── Subir VARIAS facturas a la vez ──
  const handleMultiUpload = async (e) => {
    const files = Array.from(e.target.files || []);
    e.target.value = '';
    if (files.length === 0) return;

    setParsingMulti(true);
    setMultiProgress({ current: 0, total: files.length });

    // Expandir cada archivo: si es un PDF combinado con varias facturas dentro
    // (una por pagina, como en una exportacion/historico), se separa en un
    // documento por pagina para leer cada factura por separado. Si no es PDF
    // o tiene una sola pagina, se procesa igual que antes (1 documento).
    const docs = []; // { b64, name }
    for (const file of files) {
      const b64 = await fileToB64(file);
      const isPdf = file.type === 'application/pdf' || /\.pdf$/i.test(file.name);
      if (!isPdf) { docs.push({ b64, name: file.name }); continue; }
      try {
        const sr = await fetch(`${API_URL}/api/rentabilidad/split-pdf-pages`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ fileBase64: b64 }),
        });
        const sd = await sr.json();
        const pages = (sd.success && Array.isArray(sd.pages) && sd.pages.length) ? sd.pages : [b64];
        pages.forEach((pageB64, idx) => docs.push({
          b64: pageB64,
          name: pages.length > 1 ? `${file.name} (pág ${idx + 1}/${pages.length})` : file.name,
        }));
      } catch {
        docs.push({ b64, name: file.name });
      }
    }

    setMultiProgress({ current: 0, total: docs.length });

    let successCount = 0;
    let errorCount = 0;
    let completedCount = 0;   // ya existia pero le faltaba algun campo y se ha rellenado
    let duplicateCount = 0;   // ya existia completa: se omite tal cual
    let clientesCreados = 0;  // clientes nuevos dados de alta automaticamente al detectarlos en la factura
    // Fichas existentes indexadas por docType|ref normalizada, para detectar duplicados
    // y completar campos que falten en vez de descartar la factura repetida. Se va
    // ampliando con lo que se guarda en este mismo lote (por si se repite dentro del lote).
    const existingByKey = new Map(
      (fichas || []).map(f => [`${f.docType || 'factura'}|${normRef(f.ref)}`, f])
    );

    for (let i = 0; i < docs.length; i++) {
      setMultiProgress({ current: i + 1, total: docs.length });
      const b64 = docs[i].b64;
      try {
        const r = await fetch(`${API_URL}/api/rentabilidad/parse-sale-doc`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ fileBase64: b64 }),
        });
        const data = await r.json();
        if (!data.success) { errorCount++; continue; }

        const resolvedDocType = normDocType(data.data.docType) || docType;
        const refKey = normRef(data.data.ref);
        const existing = refKey ? existingByKey.get(`${resolvedDocType}|${refKey}`) : null;

        if (existing) {
          // Ya existe: en vez de descartarla, rellena en la ficha guardada los campos
          // que falten (cliente, codigo, fecha, lineas) con lo leido en la repetida.
          const clienteFill = !existing.cliente && data.data.cliente;
          const codigoFill = !existing.clienteCodigo && data.data.clienteCodigo;
          const fechaFill = !existing.fecha && data.data.fecha;
          const lineasFill = (!existing.lines || existing.lines.length === 0) && (data.data.lines || []).length > 0;

          if (!clienteFill && !codigoFill && !fechaFill && !lineasFill) {
            duplicateCount++; continue;
          }

          const merged = {
            id: existing.id,
            ref: cleanRef(existing.ref),
            docType: resolvedDocType,
            cliente: clienteFill ? data.data.cliente : (existing.cliente || ''),
            clienteCodigo: codigoFill ? data.data.clienteCodigo : (existing.clienteCodigo || ''),
            fecha: fechaFill ? data.data.fecha : (existing.fecha || ''),
            lines: lineasFill ? (data.data.lines || []) : (existing.lines || []),
            createdBy: existing.createdBy || currentUser?.id,
            createdByName: existing.createdByName || currentUser?.clientName || currentUser?.username,
          };
          const saveR = await fetch(`${API_URL}/api/rentabilidad/fichas`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(merged),
          });
          const saveData = await saveR.json();
          if (saveData?.ficha) existingByKey.set(`${resolvedDocType}|${refKey}`, saveData.ficha);
          if (saveData?.clientCreated) clientesCreados++;
          // Deja constancia del documento repetido que aporto el dato que faltaba.
          if (existing.id) {
            await fetch(`${API_URL}/api/rentabilidad/fichas/${existing.id}/docs`, {
              method: 'POST', headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ fileBase64: b64, filename: docs[i].name, kind: 'venta' }),
            });
          }
          completedCount++;
          continue;
        }

        // Guardar directamente la ficha
        const fichaData = {
          ref: cleanRef(data.data.ref || ''),
          cliente: data.data.cliente || '',
          clienteCodigo: data.data.clienteCodigo || '',
          fecha: data.data.fecha || '',
          docType: resolvedDocType,
          lines: data.data.lines || [],
          createdBy: currentUser?.id,
          createdByName: currentUser?.clientName || currentUser?.username,
        };

        const saveR = await fetch(`${API_URL}/api/rentabilidad/fichas`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(fichaData),
        });
        const saveData = await saveR.json();
        const fid = saveData?.ficha?.id;

        // Guardar el documento asociado
        if (fid) {
          await fetch(`${API_URL}/api/rentabilidad/fichas/${fid}/docs`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ fileBase64: b64, filename: docs[i].name, kind: 'venta' }),
          });
        }
        if (refKey && saveData?.ficha) existingByKey.set(`${resolvedDocType}|${refKey}`, saveData.ficha);
        if (saveData?.clientCreated) clientesCreados++;
        successCount++;
      } catch {
        errorCount++;
      }
    }

    setParsingMulti(false);
    setMultiProgress({ current: 0, total: 0 });
    load();

    if (errorCount > 0 || duplicateCount > 0 || completedCount > 0 || clientesCreados > 0) {
      alert(`Importacion completada: ${successCount} nuevas, ${completedCount} duplicadas completadas (rellenado un campo que faltaba), ${duplicateCount} duplicadas exactas (omitidas), ${errorCount} con errores, ${clientesCreados} clientes nuevos dados de alta.`);
    }
  };

  // ── Subir pantallazo de costes (archivo o pegado con Ctrl+V) ──
  const procesarCostShot = async (file) => {
    if (!file || !editor) return;
    setMatching(true);
    try {
      const b64 = await fileToB64(file);
      const r = await fetch(`${API_URL}/api/rentabilidad/match-line-costs`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fileBase64: b64, lines: editor.lines }),
      });
      const data = await r.json();
      if (!data.success) { alert(data.error || 'No se pudo leer el pantallazo'); return; }
      setEditor({
        ...editor,
        lines: data.lines,
        costDocs: [...editor.costDocs, { b64, name: file.name || 'pegado.png' }],
      });
    } catch { alert('Error al leer el pantallazo'); }
    finally { setMatching(false); }
  };
  const handleCostShot = async (e) => {
    const file = e.target.files?.[0]; e.target.value = '';
    await procesarCostShot(file);
  };
  // Pegar (Ctrl+V) una imagen del portapapeles cuando el editor está abierto:
  // se procesa como el pantallazo de costes (IA empareja).
  useEffect(() => {
    if (!editor) return;
    const onPaste = (e) => {
      const items = (e.clipboardData && e.clipboardData.items) || [];
      for (let i = 0; i < items.length; i++) {
        if (items[i].type && items[i].type.startsWith('image/')) {
          const file = items[i].getAsFile();
          if (file) { e.preventDefault(); procesarCostShot(file); break; }
        }
      }
    };
    window.addEventListener('paste', onPaste);
    return () => window.removeEventListener('paste', onPaste);
  }, [editor]);

  // ── Alimentar costes desde el catálogo (coste medio ponderado por artículo) ──
  const handleAutoCostes = async () => {
    if (!editor || !(editor.lines || []).length) return;
    const hasCostes = (editor.lines || []).some(l => Number(l.coste) > 0);
    let force = false;
    if (hasCostes) {
      const r = window.confirm('Algunas líneas ya tienen coste.\n\nAceptar = recalcular TODAS desde el catálogo.\nCancelar = solo rellenar las que están a 0.');
      force = r;
    }
    setFeeding(true);
    try {
      const r = await fetch(`${API_URL}/api/rentabilidad/apply-article-costs`, {
        method: 'POST', headers: authHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({ lines: editor.lines, force }),
      });
      const data = await r.json();
      if (!data.success) { alert(data.error || 'No se pudieron aplicar los costes'); return; }
      setEditor({ ...editor, lines: data.lines });
      const rev = data.revisar ? ` · ${data.revisar} a revisar` : '';
      const sin = (data.sinCoste || []).filter(Boolean);
      const sinTxt = sin.length ? `\n\nSin coste en catálogo (${sin.length}): ${sin.slice(0, 12).join(', ')}${sin.length > 12 ? '…' : ''}` : '';
      alert(`Costes alimentados: ${data.matched} de ${editor.lines.length} líneas${rev}.${sinTxt}`);
    } catch { alert('Error al alimentar los costes'); }
    finally { setFeeding(false); }
  };

  // Normaliza separador decimal: acepta tanto coma como punto
  const parseDecimal = (val) => {
    if (val === '' || val === null || val === undefined) return 0;
    const normalized = String(val).replace(',', '.');
    const parsed = parseFloat(normalized);
    return isNaN(parsed) ? 0 : parsed;
  };
  // Secuencia de desbloqueo master: mantener Shift pulsada ~2,5s activa el
  // desbloqueo durante 30s (solo master). Deja modificar/borrar/desmarcar fichas
  // revisadas por el controller.
  useEffect(() => {
    if (!esMaster) return;
    let hold = null, expiry = null;
    const down = (e) => {
      if (e.key === 'Shift' && !hold && !masterUnlock) {
        hold = setTimeout(() => {
          setMasterUnlock(true);
          if (expiry) clearTimeout(expiry);
          expiry = setTimeout(() => setMasterUnlock(false), 30000);
        }, 2500);
      }
    };
    const up = (e) => { if (e.key === 'Shift' && hold) { clearTimeout(hold); hold = null; } };
    window.addEventListener('keydown', down);
    window.addEventListener('keyup', up);
    return () => { window.removeEventListener('keydown', down); window.removeEventListener('keyup', up); if (hold) clearTimeout(hold); if (expiry) clearTimeout(expiry); };
  }, [esMaster, masterUnlock]);
  // Una ficha revisada está bloqueada salvo que el master haya activado el desbloqueo.
  const bloqueada = (f) => !!(f?.revisada) && !(esMaster && masterUnlock);

  // Asigna el código de cliente del editor a TODAS las fichas de ese cliente.
  const aplicarCodigoATodas = async () => {
    if (!editor?.cliente || !(editor.clienteCodigo || '').trim()) return;
    if (!window.confirm(`¿Asignar el código «${editor.clienteCodigo}» a TODAS las fichas de ${editor.cliente}?`)) return;
    try {
      const r = await fetch(`${API_URL}/api/rentabilidad/fichas/assign-client-code`, {
        method: 'POST', headers: authHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({ cliente: editor.cliente, codigo: editor.clienteCodigo }),
      });
      const data = await r.json().catch(() => ({}));
      if (!r.ok) { alert(data.detail || 'No se pudo asignar el código'); return; }
      alert(`Código asignado a ${data.updated} ficha(s) de ${editor.cliente}.`);
      await load();
    } catch { alert('Error al asignar el código'); }
  };

  const setLine = (i, field, val) => {
    const lines = [...editor.lines];
    const isText = field === 'concepto' || field === 'ref';
    // Para campos numéricos guardamos el valor raw mientras se escribe (para no
    // interrumpir la edición) y sólo convertimos a número al guardar.
    lines[i] = { ...lines[i], [field]: isText ? val : val };
    setEditor({ ...editor, lines });
  };
  // Al salir del campo numérico (blur) normalizamos el valor a número
  const blurLine = (i, field, val) => {
    const lines = [...editor.lines];
    lines[i] = { ...lines[i], [field]: parseDecimal(val) };
    setEditor({ ...editor, lines });
  };
  const addLine = () => setEditor({ ...editor, lines: [...editor.lines, { id: `ln-${Date.now()}`, ref: '', concepto: '', cantidad: 1, venta: 0, coste: 0 }] });
  const removeLine = (i) => setEditor({ ...editor, lines: editor.lines.filter((_, x) => x !== i) });

  // Busca un documento del MISMO tipo con el MISMO número (para avisar de duplicado).
  const findDup = (dType, ref, excludeId) => {
    const rn = normRef(ref); if (!rn) return null;
    return (fichas || []).find(f => f.id !== excludeId && (f.docType || 'factura') === dType && normRef(f.ref) === rn) || null;
  };
  // Devuelve el id a usar (sobreescribir) o '' (nuevo), o null si el usuario cancela.
  const resolverNumero = (dType, ref, excludeId) => {
    const dup = findDup(dType, ref, excludeId);
    if (!dup) return '';
    const label = TABS.find(t => t.key === dType)?.label || dType;
    const ok = window.confirm(`Ya existe un ${label.toLowerCase()} con el número «${ref}» (cliente: ${dup.cliente || '—'}).\n\n¿Sobreescribirlo?\n\nAceptar = sobreescribir · Cancelar = no guardar.`);
    return ok ? dup.id : null;
  };

  const saveFicha = async () => {
    if (!editor) return;
    if (editor.docType === 'factura' && editor.cliente) {
      try {
        const cr = await fetch(`${API_URL}/api/rentabilidad/check-client?nombre=${encodeURIComponent(editor.cliente)}&codigo=${encodeURIComponent(editor.clienteCodigo || '')}`);
        const cd = await cr.json();
        if (!cd.exists) {
          const ok = window.confirm(`No existe ningun cliente con ${editor.clienteCodigo ? `el codigo "${editor.clienteCodigo}"` : `el nombre "${editor.cliente}"`}.\nSe va a crear un cliente nuevo: ${editor.cliente}${editor.clienteCodigo ? ` (codigo ${editor.clienteCodigo})` : ''}.\n\n¿Continuar?`);
          if (!ok) return;
        }
      } catch { /* si falla la comprobacion, seguimos con el guardado normal */ }
    }
    // Aviso de numeración duplicada (solo al crear uno nuevo)
    let overwriteId = editor.id;
    if (!editor.id) {
      const res = resolverNumero(editor.docType, editor.ref, editor.id);
      if (res === null) return; // usuario canceló
      overwriteId = res || undefined;
    }
    setSaving(true);
    try {
      const r = await fetch(`${API_URL}/api/rentabilidad/fichas`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: overwriteId, ref: cleanRef(editor.ref), cliente: editor.cliente, clienteCodigo: editor.clienteCodigo || '', fecha: editor.fecha,
          docType: editor.docType,
          // Normalizar separador decimal (coma o punto) antes de guardar
          lines: (editor.lines || []).map(l => ({
            ...l,
            venta: parseDecimal(l.venta),
            coste: parseDecimal(l.coste),
          })),
          createdBy: currentUser?.id, createdByName: currentUser?.clientName || currentUser?.username,
        }),
      });
      const data = await r.json();
      const fid = data?.ficha?.id;
      if (fid) {
        const uploads = [];
        if (editor.saleDoc) uploads.push({ ...editor.saleDoc, kind: 'venta' });
        (editor.costDocs || []).forEach(d => uploads.push({ ...d, kind: 'coste' }));
        for (const u of uploads) {
          await fetch(`${API_URL}/api/rentabilidad/fichas/${fid}/docs`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ fileBase64: u.b64, filename: u.name, kind: u.kind }),
          });
        }
      }
      if (data?.clientCreated) {
        alert(`Cliente creado: ${data.clientCreated.nombre} (codigo ${data.clientCreated.codigo}).`);
      }
      setEditor(null);
      load();
    } catch { alert('Error al guardar la ficha'); }
    finally { setSaving(false); }
  };

  const openFicha = async (id) => {
    try {
      const r = await fetch(`${API_URL}/api/rentabilidad/fichas/${id}`);
      setViewing(await r.json());
    } catch { /* noop */ }
  };

  // Navegación desde el Generador de informes: abre automáticamente el documento
  // cuya referencia coincide con openRef.
  useEffect(() => {
    if (!openRef) return;
    const target = normRef(openRef);
    const f = (fichas || []).find(x => normRef(x.ref) === target);
    if (f) { openFicha(f.id); if (onOpenedRef) onOpenedRef(); }
  }, [openRef, fichas]);

  const viewDoc = async (fichaId, docId) => {
    try {
      const r = await fetch(`${API_URL}/api/rentabilidad/fichas/${fichaId}/docs/${docId}`);
      const d = await r.json();
      openDoc(d.dataBase64, d.mime);
    } catch { alert('No se pudo abrir el documento'); }
  };

  // ── Convertir documento al siguiente tipo: presupuesto → pedido → albarán → factura ──
  const convertFicha = async (f) => {
    const cur = f.docType || 'factura';
    const next = NEXT_DOC_TYPE[cur] || null;
    if (!next) return;
    const nextLabel = TABS.find(t => t.key === next)?.label || next;
    const newRef = window.prompt(`Serie/número del nuevo ${nextLabel.toLowerCase()} (a partir de "${f.ref || ''}"):`, f.ref || '');
    if (newRef === null) return; // cancelado
    const destRef0 = (newRef.trim() || f.ref || '');
    const overwriteId = resolverNumero(next, destRef0);
    if (overwriteId === null) return; // usuario canceló ante duplicado
    setConverting(f.id);
    try {
      // Traer la ficha completa (con sus líneas) por si la lista no las incluye
      let full = f;
      try { const d = await fetch(`${API_URL}/api/rentabilidad/fichas/${f.id}`); if (d.ok) full = await d.json(); } catch { /* usa f */ }
      const destRef = newRef.trim() || full.ref;
      const r = await fetch(`${API_URL}/api/rentabilidad/fichas`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: overwriteId || undefined,
          ref: destRef, cliente: full.cliente,
          fecha: new Date().toISOString().slice(0, 10),
          docType: next, lines: full.lines || [], projectRef: full.projectRef || '',
          createdBy: currentUser?.id, createdByName: currentUser?.clientName || currentUser?.username,
          // Trazabilidad: de qué documento procede este nuevo
          origenId: full.id, origenRef: full.ref || '', origenType: cur,
        }),
      });
      if (!r.ok) throw new Error('Error');
      const created = await r.json().catch(() => ({}));
      const newId = created?.ficha?.id;
      // Marcar en el documento de origen a qué se ha convertido
      try {
        await fetch(`${API_URL}/api/rentabilidad/fichas/${full.id}/trace`, {
          method: 'PATCH', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ convertidoAId: newId || '', convertidoARef: destRef, convertidoAType: next }),
        });
      } catch { /* no crítico */ }
      setDocType(next);
      setCurrentPage(1);
      await load();
    } catch (e) { alert('No se pudo convertir: ' + (e.message || '')); }
    finally { setConverting(''); }
  };

  // Salta al documento vinculado (origen/destino): cambia de pestaña y filtra por su ref.
  const irADocumento = (tipo, ref) => {
    if (tipo) setDocType(tipo);
    setColumnFilters(prev => ({ ...prev, ref: ref || '' }));
    setCurrentPage(1);
  };

  const removeFicha = async (id) => {
    const f = (fichas || []).find(x => x.id === id);
    if (bloqueada(f)) {
      alert('Ficha con visto bueno del controller: bloqueada.\n\nSolo el master puede borrarla: mantén pulsada la tecla Shift un par de segundos (desbloqueo) y vuelve a intentarlo.');
      return;
    }
    if (!window.confirm('Eliminar esta ficha y sus documentos?')) return;
    const r = await fetch(`${API_URL}/api/rentabilidad/fichas/${id}`, { method: 'DELETE', headers: authHeaders() });
    if (!r.ok) { const e = await r.json().catch(() => ({})); alert(e.detail || 'No se pudo borrar'); return; }
    load();
  };

  // ── Informe PDF: fichas con margen 0 o negativo (aviso previo al visto bueno) ──
  const exportarRevisionMargen = async () => {
    const rows = baseFiltered.filter(margenNegativo);
    if (rows.length === 0) { alert('No hay documentos con margen 0 o negativo en el listado actual.'); return; }
    try {
      const { jsPDF } = await import('jspdf');
      const autoTable = (await import('jspdf-autotable')).default;
      const clean = (s) => String(s ?? '').normalize('NFKC');
      const hoy = new Date();
      const fechaStr = hoy.toLocaleDateString('es-ES');
      const fechaFile = hoy.toISOString().slice(0, 10);

      const pdf = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
      const W = pdf.internal.pageSize.getWidth();
      const M = 14;

      // Cabecera de marca (logo si existe; si no, texto). Marca blanca.
      const logo = currentUser?.logo || null;
      const drawHeader = () => {
        const hy = 14;
        if (logo && typeof logo === 'string' && logo.startsWith('data:')) {
          try {
            const fmt = logo.includes('image/png') ? 'PNG' : (logo.includes('image/webp') ? 'WEBP' : 'JPEG');
            pdf.addImage(logo, fmt, M, hy, 32, 16);
          } catch (_) { /* logo no incrustable */ }
        } else {
          pdf.setFontSize(15); pdf.setTextColor(30); pdf.setFont(undefined, 'bold');
          pdf.text('LUIGGI HOME', M, hy + 8); pdf.setFont(undefined, 'normal');
        }
        pdf.setFontSize(13); pdf.setTextColor(185, 28, 28); pdf.setFont(undefined, 'bold');
        pdf.text('Revisión de margen — artículos con margen 0 o negativo', W - M, hy + 4, { align: 'right' });
        pdf.setFont(undefined, 'normal');
        pdf.setFontSize(9); pdf.setTextColor(120);
        pdf.text(`${fechaStr}   ·   ${rows.length} documento(s)`, W - M, hy + 10, { align: 'right' });
      };
      drawHeader();

      const head = [['Nº / Ref', 'Cliente', 'Fecha', 'Coste', 'Venta', 'Margen', '% s/Coste']];
      const acc = { venta: 0, coste: 0, margen: 0 };
      const body = rows.map(f => {
        const tt = f.totals || totals(f.lines);
        acc.venta += tt.venta || 0; acc.coste += tt.coste || 0; acc.margen += tt.margen || 0;
        return [
          clean(f.ref || '-'),
          clean(f.cliente || '-') + (f.clienteCodigo ? ` (${f.clienteCodigo})` : ''),
          f.fecha || '-',
          eur(tt.coste), eur(tt.venta), eur(tt.margen),
          `${(Number(tt.margenPct) || 0).toFixed(1)}%`,
        ];
      });

      autoTable(pdf, {
        startY: 40,
        head, body,
        styles: { fontSize: 8.5, cellPadding: 1.8, overflow: 'linebreak', valign: 'middle' },
        headStyles: { fillColor: [185, 28, 28], textColor: [255, 255, 255], fontStyle: 'bold' },
        alternateRowStyles: { fillColor: [253, 242, 242] },
        columnStyles: {
          0: { cellWidth: 24 }, 1: { cellWidth: 'auto' }, 2: { cellWidth: 20 },
          3: { cellWidth: 24, halign: 'right' }, 4: { cellWidth: 24, halign: 'right' },
          5: { cellWidth: 24, halign: 'right' }, 6: { cellWidth: 18, halign: 'right' },
        },
        margin: { top: 32, left: M, right: M },
        didDrawPage: (data) => { if (data.pageNumber > 1) drawHeader(); },
      });

      let y = (pdf.lastAutoTable?.finalY || 40) + 8;
      pdf.setFillColor(30, 27, 45); pdf.rect(M, y, W - 2 * M, 16, 'F');
      pdf.setTextColor(255); pdf.setFontSize(9); pdf.setFont(undefined, 'bold');
      pdf.text(`TOTAL (${rows.length} doc.)`, M + 3, y + 10);
      pdf.text(`Venta: ${eur(acc.venta)}`, M + 55, y + 10);
      pdf.text(`Coste: ${eur(acc.coste)}`, M + 105, y + 10);
      pdf.setTextColor(acc.margen >= 0 ? 110 : 255, acc.margen >= 0 ? 231 : 120, acc.margen >= 0 ? 183 : 120);
      pdf.text(`Margen: ${eur(acc.margen)}`, M + 150, y + 10);
      pdf.setFont(undefined, 'normal');

      pdf.save(`revision_margen_${fechaFile}.pdf`);
    } catch (e) {
      alert('No se pudo generar el PDF: ' + (e?.message || e));
    }
  };

  // Informe PDF a nivel de LÍNEA: líneas sin coste (precio de coste = 0) o con
  // margen 0/negativo, en todas las fichas del listado actual, para revisarlas
  // antes del visto bueno. Cada línea indica su ficha, artículo y el motivo.
  const exportarRevisionLineas = async () => {
    const items = [];
    (baseFiltered || []).forEach(f => {
      (f.lines || []).forEach(l => {
        const venta = Number(l.venta) || 0;
        const coste = Number(l.coste) || 0;
        const margen = venta - coste;
        const sinCoste = coste <= 0;
        const margenMalo = margen <= 0;
        if (!sinCoste && !margenMalo) return;
        items.push({
          ficha: f.ref || '-', cliente: f.cliente || '-',
          ref: l.ref || '-', concepto: l.concepto || '-',
          cantidad: Number(l.cantidad) || 0, venta, coste, margen,
          motivo: sinCoste ? (margenMalo && venta <= 0 ? 'SIN VENTA/COSTE' : 'SIN COSTE') : 'MARGEN ≤ 0',
        });
      });
    });
    if (items.length === 0) { alert('No hay líneas sin coste ni con margen ≤ 0 en el listado actual.'); return; }
    try {
      const { jsPDF } = await import('jspdf');
      const autoTable = (await import('jspdf-autotable')).default;
      const clean = (s) => String(s ?? '').normalize('NFKC');
      const hoy = new Date();
      const fechaStr = hoy.toLocaleDateString('es-ES');
      const fechaFile = hoy.toISOString().slice(0, 10);
      const pdf = new jsPDF({ orientation: 'landscape', unit: 'mm', format: 'a4' });
      const W = pdf.internal.pageSize.getWidth();
      const M = 12;
      const logo = currentUser?.logo || null;
      const drawHeader = () => {
        const hy = 12;
        if (logo && typeof logo === 'string' && logo.startsWith('data:')) {
          try {
            const fmt = logo.includes('image/png') ? 'PNG' : (logo.includes('image/webp') ? 'WEBP' : 'JPEG');
            pdf.addImage(logo, fmt, M, hy, 30, 15);
          } catch (_) { /* logo no incrustable */ }
        } else {
          pdf.setFontSize(14); pdf.setTextColor(30); pdf.setFont(undefined, 'bold');
          pdf.text('LUIGGI HOME', M, hy + 8); pdf.setFont(undefined, 'normal');
        }
        pdf.setFontSize(12); pdf.setTextColor(185, 28, 28); pdf.setFont(undefined, 'bold');
        pdf.text('Revisión de líneas — sin coste o margen ≤ 0', W - M, hy + 4, { align: 'right' });
        pdf.setFont(undefined, 'normal');
        pdf.setFontSize(9); pdf.setTextColor(120);
        pdf.text(`${fechaStr}   ·   ${items.length} línea(s)`, W - M, hy + 10, { align: 'right' });
      };
      drawHeader();
      const head = [['Ficha', 'Ref art.', 'Concepto', 'Cant', 'Venta', 'Coste', 'Margen', 'Motivo']];
      const body = items.map(it => [
        clean(it.ficha), clean(it.ref), clean(it.concepto),
        String(it.cantidad), eur(it.venta), eur(it.coste), eur(it.margen), it.motivo,
      ]);
      autoTable(pdf, {
        startY: 34, head, body,
        styles: { fontSize: 8, cellPadding: 1.5, overflow: 'linebreak', valign: 'middle' },
        headStyles: { fillColor: [185, 28, 28], textColor: [255, 255, 255], fontStyle: 'bold' },
        alternateRowStyles: { fillColor: [253, 242, 242] },
        columnStyles: {
          0: { cellWidth: 30 }, 1: { cellWidth: 34 }, 2: { cellWidth: 'auto' },
          3: { cellWidth: 14, halign: 'right' }, 4: { cellWidth: 24, halign: 'right' },
          5: { cellWidth: 24, halign: 'right' }, 6: { cellWidth: 24, halign: 'right' },
          7: { cellWidth: 30 },
        },
        margin: { top: 30, left: M, right: M },
        didDrawPage: (data) => { if (data.pageNumber > 1) drawHeader(); },
      });
      pdf.save(`revision_lineas_${fechaFile}.pdf`);
    } catch (e) {
      alert('No se pudo generar el PDF: ' + (e?.message || e));
    }
  };

  // Modo "Revisar margen": aísla las fichas con margen 0 o negativo antes del visto bueno.
  const [reviewMode, setReviewMode] = useState(false);
  // Filtro por Check Controller: 'todas' | 'revisadas' | 'pendientes' (falta por revisar).
  const [controllerFilter, setControllerFilter] = useState('todas');
  // Margen de una ficha (usa totals precalculados si existen, si no los calcula).
  const margenDe = (f) => (f.totals?.margen ?? totals(f.lines).margen);
  const margenNegativo = (f) => (Number(margenDe(f)) || 0) <= 0;

  // Filtrado y ordenacion
  const baseFiltered = useMemo(() => {
    let rows = fichas.filter(f => (f.docType || 'factura') === docType);

    // Aplicar filtros por columna
    if (columnFilters.ref) {
      // Usa normRef en ambos lados: elimina espacios, barras y convierte a mayúsculas
      // Así 'LG26/61' encuentra 'LG26 / 61' y viceversa
      const refQ = normRef(columnFilters.ref);
      rows = rows.filter(f => normRef(f.ref).includes(refQ));
    }
    if (columnFilters.cliente) {
      // Filtra por NOMBRE o por CÓDIGO de cliente (p. ej. "4273").
      const q = columnFilters.cliente.toLowerCase();
      rows = rows.filter(f =>
        (f.cliente || '').toLowerCase().includes(q) ||
        String(f.clienteCodigo || f.clientCode || '').toLowerCase().includes(q)
      );
    }
    if (columnFilters.fechaDesde) {
      rows = rows.filter(f => (f.fecha || '') >= columnFilters.fechaDesde);
    }
    if (columnFilters.fechaHasta) {
      rows = rows.filter(f => (f.fecha || '') <= columnFilters.fechaHasta);
    }
    if (columnFilters.ventaMin) {
      rows = rows.filter(f => { const tt = f.totals || totals(f.lines); return (tt.venta || 0) >= Number(columnFilters.ventaMin); });
    }
    if (columnFilters.ventaMax) {
      rows = rows.filter(f => { const tt = f.totals || totals(f.lines); return (tt.venta || 0) <= Number(columnFilters.ventaMax); });
    }
    if (columnFilters.costeMin) {
      rows = rows.filter(f => { const tt = f.totals || totals(f.lines); return (tt.coste || 0) >= Number(columnFilters.costeMin); });
    }
    if (columnFilters.costeMax) {
      rows = rows.filter(f => { const tt = f.totals || totals(f.lines); return (tt.coste || 0) <= Number(columnFilters.costeMax); });
    }
    if (columnFilters.margenMin) {
      rows = rows.filter(f => { const tt = f.totals || totals(f.lines); return (tt.margen || 0) >= Number(columnFilters.margenMin); });
    }
    if (columnFilters.margenMax) {
      rows = rows.filter(f => { const tt = f.totals || totals(f.lines); return (tt.margen || 0) <= Number(columnFilters.margenMax); });
    }
    // Filtro por Check Controller (revisada por el controller)
    if (controllerFilter === 'revisadas') {
      rows = rows.filter(f => !!f.revisada);
    } else if (controllerFilter === 'pendientes') {
      rows = rows.filter(f => !f.revisada);
    }

    // Ordenacion
    rows.sort((a, b) => {
      let va, vb;
      const ta = a.totals || totals(a.lines);
      const tb = b.totals || totals(b.lines);
      switch (sortColumn) {
        case 'ref':
          va = extractRefNumber(a.ref);
          vb = extractRefNumber(b.ref);
          break;
        case 'cliente':
          va = (a.cliente || '').toLowerCase();
          vb = (b.cliente || '').toLowerCase();
          break;
        case 'fecha':
          va = a.fecha || '';
          vb = b.fecha || '';
          break;
        case 'venta':
          va = ta.venta || 0;
          vb = tb.venta || 0;
          break;
        case 'coste':
          va = ta.coste || 0;
          vb = tb.coste || 0;
          break;
        case 'margen':
          va = ta.margen || 0;
          vb = tb.margen || 0;
          break;
        default:
          va = extractRefNumber(a.ref);
          vb = extractRefNumber(b.ref);
      }
      if (va < vb) return sortDirection === 'asc' ? -1 : 1;
      if (va > vb) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });

    return rows;
  }, [fichas, docType, columnFilters, sortColumn, sortDirection, controllerFilter]);

  // Fichas con margen 0 o negativo dentro del listado ya filtrado (para el contador y el PDF).
  const marginBadFichas = useMemo(() => baseFiltered.filter(margenNegativo), [baseFiltered]);

  // Facturas que faltan por controlar (Check Controller pendiente). Solo facturas de venta.
  // Respeta los filtros activos (cliente, fechas, importes) y la pestaña actual: cuenta lo
  // que el controller está viendo, no el total global.
  const pendientesControl = useMemo(() => {
    const facturas = (baseFiltered || []).filter(f => (f.docType || 'factura') === 'factura' && !f.revisada);
    const lineas = facturas.reduce((s, f) => s + ((f.lines || []).length), 0);
    return { docs: facturas.length, lineas };
  }, [baseFiltered]);

  // Lista final que se pinta: si el modo revisión está activo, solo las de margen ≤ 0.
  const filteredAndSorted = useMemo(
    () => (reviewMode ? marginBadFichas : baseFiltered),
    [reviewMode, marginBadFichas, baseFiltered]
  );

  // Paginacion sobre los datos filtrados y ordenados
  const totalPages = Math.max(1, Math.ceil(filteredAndSorted.length / pageSize));
  const safePage = Math.min(currentPage, totalPages);
  const paginatedRows = filteredAndSorted.slice((safePage - 1) * pageSize, safePage * pageSize);

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
    setCurrentPage(1);
  };

  const hasActiveFilters = Object.values(columnFilters).some(v => v !== '');

  // Totales del listado FILTRADO (respeta pestaña de tipo + todos los filtros de columna).
  // Se excluyen las fichas ya convertidas a otro documento (convertidoAId): su importe
  // ya vive en el documento destino, sumarla aqui tambien duplicaria la venta.
  const [showTotals, setShowTotals] = useState(false);
  // Candado: oculta la columna MARGEN para privacidad
  const [hideMargen, setHideMargen] = useState(false);
  const filteredTotals = useMemo(() => {
    return filteredAndSorted.filter(f => !f.convertidoAId).reduce((acc, f) => {
      const tt = f.totals || totals(f.lines);
      acc.venta += tt.venta || 0;
      acc.coste += tt.coste || 0;
      acc.margen += tt.margen || 0;
      acc.pendienteCobro += Number(f.pendienteCobro) || 0;
      return acc;
    }, { venta: 0, coste: 0, margen: 0, pendienteCobro: 0 });
  }, [filteredAndSorted]);

  const et = editor ? totals(editor.lines) : null;

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
    <div>
      {/* Botón de retroceso al Generador de informes (cuando llegas desde ahí) */}
      {onBackToReport && (
        <button onClick={onBackToReport}
          className="mb-3 px-4 py-2 bg-indigo-600 text-white rounded-xl font-bold text-sm hover:bg-indigo-700 inline-flex items-center gap-2">
          ← Volver al informe
        </button>
      )}
      {/* Pestanas */}
      <div className="flex items-center gap-2 mb-4 flex-wrap">
        {TABS.map(t => {
          const Icon = t.icon;
          return (
            <button key={t.key} onClick={() => { setDocType(t.key); setCurrentPage(1); }}
              className={`px-4 py-2 rounded-xl font-bold text-sm flex items-center gap-2 transition-all ${
                docType === t.key ? 'bg-emerald-600 text-white shadow' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}>
              <Icon size={16} /> {t.label}
            </button>
          );
        })}
        <div className="ml-auto flex items-center gap-2">
          <button onClick={openClients} className="px-4 py-2 rounded-xl font-bold text-sm flex items-center gap-2 bg-indigo-600 text-white hover:bg-indigo-700">
            <Users size={16} /> Clientes {clients.length > 0 && <span className="px-1.5 py-0.5 bg-white/20 rounded text-[11px]">{clients.length}</span>}
          </button>
          <label className="px-4 py-2 rounded-xl font-bold text-sm flex items-center gap-2 bg-gradient-to-r from-fuchsia-600 to-indigo-600 text-white hover:opacity-90 cursor-pointer">
            <Sparkles size={16} /> Bandeja IA
            <input type="file" accept="image/*,application/pdf" className="hidden" onChange={e => { const f = e.target.files?.[0]; if (f) clasificarDoc(f); }} />
          </label>
          {/* Multi-upload: subir varios documentos del tipo activo a la vez */}
          <label className={`px-4 py-2 rounded-xl font-bold text-sm flex items-center gap-2 cursor-pointer ${parsingMulti ? 'bg-green-200 text-green-600' : 'bg-green-600 text-white hover:bg-green-700'}`}>
            <Files size={16} className={parsingMulti ? 'animate-pulse' : ''} />
            {parsingMulti ? `Importando ${multiProgress.current}/${multiProgress.total}...` : `Subir varios ${TABS.find(t => t.key === docType)?.plural || 'documentos'}`}
            <input type="file" accept="image/*,application/pdf" className="hidden" multiple onChange={handleMultiUpload} disabled={parsingMulti || parsing} />
          </label>
          {/* Single upload: el tipo de documento se toma de la pestana activa */}
          <label className={`px-4 py-2 rounded-xl font-bold text-sm flex items-center gap-2 cursor-pointer ${parsing ? 'bg-purple-200 text-purple-500' : 'bg-purple-600 text-white hover:bg-purple-700'}`}>
            <Sparkles size={16} className={parsing ? 'animate-pulse' : ''} />
            {parsing ? 'Leyendo...' : `Subir ${TABS.find(t => t.key === docType)?.singular || 'documento'}`}
            <input type="file" accept="image/*,application/pdf" className="hidden" onChange={handleSaleDoc} disabled={parsing || parsingMulti} />
          </label>
          <button onClick={() => setShowTotals(s => !s)} className={`px-4 py-2 rounded-xl font-bold text-sm flex items-center gap-2 ${showTotals ? 'bg-emerald-700 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}>
            <Euro size={16} /> Totales
          </button>
          {esMaster && masterUnlock && (
            <span className="px-3 py-2 rounded-xl font-black text-xs bg-red-600 text-white flex items-center gap-1.5 animate-pulse" title="Desbloqueo master activo 30s: puedes modificar/borrar/desmarcar fichas revisadas">
              <Unlock size={14} /> Desbloqueo master activo
            </span>
          )}
          {/* Contador fijo: facturas que faltan por controlar (Check Controller). Al pulsar, filtra. */}
          <button onClick={() => { setControllerFilter('pendientes'); setCurrentPage(1); }}
            title="Facturas de venta sin el visto bueno del controller. Pulsa para filtrarlas."
            className={`px-4 py-2 rounded-xl font-bold text-sm flex items-center gap-2 ${pendientesControl.docs > 0 ? 'bg-amber-500 text-white hover:bg-amber-600' : 'bg-emerald-100 text-emerald-700'}`}>
            {pendientesControl.docs > 0
              ? <>⚠ Faltan por controlar: {pendientesControl.docs} <span className="opacity-80 font-normal">({pendientesControl.lineas} líneas)</span></>
              : <>✅ Todo controlado</>}
          </button>
          {/* Filtro por Check Controller: ver revisadas o las que faltan por revisar/generar */}
          <select value={controllerFilter} onChange={e => { setControllerFilter(e.target.value); setCurrentPage(1); }}
            title="Filtrar por estado del Check Controller"
            className={`px-3 py-2 rounded-xl font-bold text-sm border ${controllerFilter === 'pendientes' ? 'bg-amber-100 text-amber-800 border-amber-300' : controllerFilter === 'revisadas' ? 'bg-emerald-100 text-emerald-800 border-emerald-300' : 'bg-slate-100 text-slate-600 border-slate-200'}`}>
            <option value="todas">Check Controller: todas</option>
            <option value="pendientes">❓ Faltan por revisar</option>
            <option value="revisadas">✅ Revisadas</option>
          </select>
          {/* Revisar margen: aísla las fichas con margen 0 o negativo (aviso previo al visto bueno). */}
          <button onClick={() => { setReviewMode(s => !s); setCurrentPage(1); }}
            className={`px-4 py-2 rounded-xl font-bold text-sm flex items-center gap-2 ${reviewMode ? 'bg-red-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}>
            <Eye size={16} /> Revisar margen
            {marginBadFichas.length > 0 && (
              <span className={`px-1.5 py-0.5 rounded text-[11px] ${reviewMode ? 'bg-white/20' : 'bg-red-100 text-red-700'}`}>{marginBadFichas.length}</span>
            )}
          </button>
          <button onClick={exportarRevisionMargen} disabled={marginBadFichas.length === 0}
            className="px-4 py-2 rounded-xl font-bold text-sm flex items-center gap-2 bg-slate-800 text-white hover:bg-slate-900 disabled:opacity-40 disabled:cursor-not-allowed">
            <FileText size={16} /> Informe PDF (margen ≤ 0)
          </button>
          <button onClick={exportarRevisionLineas}
            title="PDF con las líneas sin coste o con margen 0/negativo de todas las fichas del listado"
            className="px-4 py-2 rounded-xl font-bold text-sm flex items-center gap-2 bg-amber-600 text-white hover:bg-amber-700">
            <FileText size={16} /> Líneas sin coste / margen ≤ 0
          </button>
          <button onClick={load} className="px-3 py-2 bg-slate-100 hover:bg-slate-200 rounded-xl">
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      {/* Totales del listado filtrado (pestaña + filtros de columna activos) */}
      {showTotals && (
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 mb-4">
          <div className="bg-orange-600 text-white p-3 rounded-2xl"><p className="text-[10px] uppercase opacity-80">Total coste</p><p className="text-xl font-black">{eur(filteredTotals.coste)}</p></div>
          <div className="bg-indigo-600 text-white p-3 rounded-2xl"><p className="text-[10px] uppercase opacity-80">Total venta</p><p className="text-xl font-black">{eur(filteredTotals.venta)}</p></div>
          <div className={`${filteredTotals.margen >= 0 ? 'bg-emerald-600' : 'bg-red-600'} text-white p-3 rounded-2xl`}><p className="text-[10px] uppercase opacity-80">Total margen</p><p className="text-xl font-black">{eur(filteredTotals.margen)}</p></div>
          <div className="bg-slate-800 text-white p-3 rounded-2xl"><p className="text-[10px] uppercase opacity-80">Documentos {hasActiveFilters ? '(filtrados)' : ''}</p><p className="text-xl font-black">{filteredAndSorted.length}</p></div>
        </div>
      )}

      {/* Bandeja IA: zona de arrastrar y soltar */}
      <div
        onDragOver={e => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={e => { e.preventDefault(); setDragOver(false); const f = e.dataTransfer.files?.[0]; if (f) clasificarDoc(f); }}
        className={`mb-4 rounded-2xl border-2 border-dashed px-4 py-3 flex items-center justify-center gap-2 text-sm font-bold transition-colors ${dragOver ? 'border-fuchsia-500 bg-fuchsia-50 text-fuchsia-700' : 'border-slate-200 text-slate-400'}`}>
        <Sparkles size={16} /> Arrastra aquí un documento (factura, pedido, albarán, ingreso…) y la IA detectará qué es y dónde colocarlo.
      </div>

      {/* Aviso del modo revisión de margen */}
      {reviewMode && (
        <div className="flex items-center gap-2 mb-3 px-3 py-2 rounded-xl bg-red-50 border border-red-200">
          <Eye size={16} className="text-red-600" />
          <span className="text-sm font-black text-red-700">
            Revisión de margen · {marginBadFichas.length} con margen 0 o negativo
          </span>
          <span className="text-xs text-red-500">Revísalos antes de dar el visto bueno.</span>
          <button onClick={() => setReviewMode(false)} className="text-xs text-slate-500 hover:text-slate-700 font-bold ml-auto underline">
            Salir de revisión
          </button>
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
          <span className="text-xs text-slate-400 ml-auto">{filteredAndSorted.length} resultados</span>
        </div>
      )}

      {/* Tabla */}
      <div className="bg-white border border-slate-200 rounded-2xl overflow-x-auto">
        <table className="w-full text-sm min-w-[1080px]">
          <thead className="bg-slate-100 text-slate-600">
            <tr>
              <SortHeader col="ref" label="N. / Ref" />
              <SortHeader col="cliente" label="Cliente" />
              <SortHeader col="fecha" label="Fecha" />
              <SortHeader col="coste" label="Coste" align="right" />
              <SortHeader col="venta" label="Venta" align="right" />
              {/* Cabecera MARGEN con botón candado */}
              <th className="text-right p-3 text-xs font-black uppercase">
                <span className="inline-flex items-center gap-1.5">
                  {!hideMargen && <SortHeader col="margen" label="Margen" align="right" />}
                  {hideMargen && <span className="text-slate-400 italic">Margen</span>}
                  <button
                    onClick={() => setHideMargen(h => !h)}
                    title={hideMargen ? 'Mostrar margen' : 'Ocultar margen (privacidad)'}
                    className={`p-0.5 rounded transition-colors ${
                      hideMargen ? 'text-red-500 hover:text-red-700' : 'text-slate-400 hover:text-slate-600'
                    }`}
                  >
                    {hideMargen ? <Lock size={12} /> : <Unlock size={12} />}
                  </button>
                </span>
              </th>
              <th className="text-right p-3 text-xs font-black uppercase">% Incr. C→V</th>
              <th className="text-center p-3 text-xs font-black uppercase">Docs</th>
              <th className="p-3"></th>
            </tr>
            {/* Fila de filtros */}
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
                  placeholder="Nombre o código…"
                  className="w-full px-2 py-1 text-xs border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-400 font-normal"
                />
              </th>
              <th className="p-1.5">
                <div className="flex gap-1">
                  <input
                    type="date"
                    value={columnFilters.fechaDesde}
                    onChange={e => setColumnFilters(prev => ({ ...prev, fechaDesde: e.target.value }))}
                    className="w-1/2 px-1 py-1 text-[10px] border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-400 font-normal"
                    title="Desde"
                  />
                  <input
                    type="date"
                    value={columnFilters.fechaHasta}
                    onChange={e => setColumnFilters(prev => ({ ...prev, fechaHasta: e.target.value }))}
                    className="w-1/2 px-1 py-1 text-[10px] border border-slate-200 rounded-lg focus:outline-none focus:border-indigo-400 font-normal"
                    title="Hasta"
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
                  <button onClick={clearColumnFilters} className="text-red-500 hover:text-red-700">
                    <X size={14} />
                  </button>
                )}
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {paginatedRows.map(f => {
              const tt = f.totals || totals(f.lines);
              // Alerta de margen bajo (<15%) solo tiene sentido si hay venta y coste registrados.
              const alertaMargen = tt.venta > 0 && tt.coste > 0 && tt.margenPct < 15;
              // Margen 0 o negativo: aviso SIEMPRE visible (borde rojo + icono) para no dar
              // por bueno un documento sin margen. Se resalta aunque el modo revisión esté off.
              const margenCero = (Number(tt.margen) || 0) <= 0;
              // Ya convertida a otro documento: se atenua porque su importe ya no cuenta
              // en los totales (vive en el documento de destino), evita doble lectura.
              const yaConvertida = !!f.convertidoAId;
              return (
                <tr key={f.id} className={`hover:bg-slate-50 cursor-pointer ${margenCero ? 'bg-red-100/70 border-l-4 border-red-500' : alertaMargen ? 'bg-red-50/60' : ''} ${yaConvertida ? 'opacity-50' : ''}`} onClick={() => openFicha(f.id)}>
                  <td className="p-3 font-black text-indigo-700">
                    {margenCero
                      ? <span title="Margen 0 o negativo — revisar antes del visto bueno" className="inline-block mr-1 text-red-600">⚠</span>
                      : alertaMargen && <span title="Margen bajo (<15%)" className="inline-block mr-1 text-red-500">⚠</span>}
                    {f.ref || '-'}
                    {f.origenRef && <button type="button" onClick={(e) => { e.stopPropagation(); irADocumento(f.origenType, f.origenRef); }} title="Ir al documento de origen" className="block text-[9px] font-bold text-slate-400 hover:text-indigo-600 hover:underline mt-0.5">↑ {(f.origenType || '').charAt(0).toUpperCase() + (f.origenType || '').slice(1)} {f.origenRef}</button>}
                    {f.convertidoARef && <button type="button" onClick={(e) => { e.stopPropagation(); irADocumento(f.convertidoAType, f.convertidoARef); }} title="Ir al documento de destino" className="block text-[9px] font-bold text-emerald-600 hover:text-emerald-800 hover:underline mt-0.5">→ {(f.convertidoAType || '').charAt(0).toUpperCase() + (f.convertidoAType || '').slice(1)} {f.convertidoARef}</button>}
                  </td>
                  <td className="p-3 text-slate-700">
                    {f.cliente || '-'}
                    {f.clienteCodigo && <span className="ml-1.5 text-[10px] font-bold text-indigo-500">({f.clienteCodigo})</span>}
                  </td>
                  <td className="p-3 text-slate-500">{f.fecha || '-'}</td>
                  <td className="p-3 text-right font-mono text-orange-600">
                    {eur(tt.coste)}
                    {/* Aviso: hay venta pero ningún coste emparejado (ni en líneas ni en costes de proyecto) */}
                    {tt.venta > 0 && !(tt.coste > 0) && !((f.costesProyecto || 0) > 0) && (
                      <span title="Esta ficha no tiene costes emparejados: el margen mostrado no es real."
                        className="block mt-0.5 text-[9px] font-black uppercase tracking-wide text-amber-700 bg-amber-100 rounded px-1.5 py-0.5 inline-block">⚠ Faltan costes</span>
                    )}
                  </td>
                  <td className="p-3 text-right font-mono">{eur(tt.venta)}</td>
                  {/* Celda MARGEN — oculta si hideMargen */}
                  <td className={`p-3 text-right font-mono font-black ${alertaMargen ? 'text-red-600' : tt.margen >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                    {hideMargen ? <span className="text-slate-300 select-none tracking-widest">••••</span> : eur(tt.margen)}
                  </td>
                  {/* Columna % Incremento Coste→Venta (Margen/Coste) */}
                  <td className="p-3 text-right font-mono text-slate-600 text-xs">
                    {tt.coste > 0 ? `${(((tt.venta - tt.coste) / tt.coste) * 100).toFixed(1)}%` : '—'}
                  </td>
                  <td className="p-3 text-center text-slate-500">{f.numDocs || 0} 📎</td>
                  <td className="p-3 text-right whitespace-nowrap" onClick={(e) => e.stopPropagation()}>
                    {f.revisada && f.revisadaPor && (
                      <span className="block text-[9px] font-bold text-emerald-600 mb-0.5" title="Revisado por el controller">
                        ✅ {f.revisadaPor}{f.revisadaAt ? ` · ${String(f.revisadaAt).slice(0, 10)}` : ''}
                      </span>
                    )}
                    {NEXT_DOC_TYPE[f.docType || 'factura'] && (
                      <button onClick={() => convertFicha(f)} disabled={converting === f.id}
                        className="mr-2 px-2.5 py-1 bg-indigo-600 text-white rounded-lg text-[11px] font-bold hover:bg-indigo-700 disabled:opacity-50">
                        → {TABS.find(t => t.key === NEXT_DOC_TYPE[f.docType || 'factura'])?.label}
                      </button>
                    )}
                    {/* Botón de revisión de controller: ❓✔ = pendiente de revisar | ✅ = ya revisada */}
                    {f.docType === 'factura' && (
                      <button
                        onClick={(e) => toggleRevision(e, f)}
                        disabled={togglingRevision === f.id}
                        title={f.revisada
                          ? `Revisada por ${f.revisadaPor || 'controller'}${f.revisadaAt ? ' el ' + f.revisadaAt.slice(0,10) : ''} — pulsa para desmarcar`
                          : 'Marcar como revisada por el controller (márgenes verificados)'}
                        className={`mr-2 px-2.5 py-1 rounded-lg text-[11px] font-bold disabled:opacity-50 flex items-center gap-1 transition-colors ${
                          f.revisada
                            ? 'bg-emerald-100 text-emerald-700 border border-emerald-300 hover:bg-emerald-200'
                            : 'bg-amber-100 text-amber-700 border border-amber-300 hover:bg-amber-200'
                        }`}
                      >
                        {togglingRevision === f.id
                          ? <Loader2 size={11} className="animate-spin" />
                          : f.revisada ? '✅' : '❓✔'}
                        {f.revisada ? 'Revisada' : 'Check Controller'}
                      </button>
                    )}
                    {bloqueada(f) ? (
                      <span title="Factura con visto bueno del controller: bloqueada. Solo el master puede borrarla (mantén Shift ~2,5s)."
                        className="inline-flex text-slate-300 cursor-not-allowed"><Lock size={15} /></span>
                    ) : (
                      <button onClick={(e) => { e.stopPropagation(); removeFicha(f.id); }}
                        title="Eliminar" className="text-slate-300 hover:text-red-500"><Trash2 size={15} /></button>
                    )}
                  </td>
                </tr>
              );
            })}
            {filteredAndSorted.length === 0 && (
              <tr><td colSpan={9} className="p-8 text-center text-slate-400">
                {loading ? 'Cargando...' : hasActiveFilters ? 'Sin resultados con estos filtros' : `Sin ${TABS.find(t => t.key === docType)?.label.toLowerCase()}. Sube un documento de venta para empezar.`}
              </td></tr>
            )}
          </tbody>
          {showTotals && filteredAndSorted.length > 0 && (
            <tfoot>
              <tr className="bg-slate-50 border-t-2 border-slate-200 font-black text-slate-800">
                <td colSpan={3} className="p-3 text-xs uppercase tracking-wide text-slate-500">Total {hasActiveFilters ? '(filtrado)' : ''} · {filteredAndSorted.length} doc.</td>
                <td className="p-3 text-right font-mono">{eur(filteredTotals.coste)}</td>
                <td className="p-3 text-right font-mono">{eur(filteredTotals.venta)}</td>
                <td className="p-3 text-right font-mono text-emerald-700">
                  {hideMargen ? <span className="text-slate-300 select-none tracking-widest">••••</span> : eur(filteredTotals.margen)}
                </td>
                {/* Total % Incremento Coste→Venta ponderado */}
                <td className="p-3 text-right font-mono text-slate-600 text-xs">
                  {filteredTotals.coste > 0 ? `${(((filteredTotals.venta - filteredTotals.coste) / filteredTotals.coste) * 100).toFixed(1)}%` : '—'}
                </td>
                <td colSpan={2}></td>
              </tr>
            </tfoot>
          )}
        </table>
      </div>

      {/* Barra de paginacion */}
      {filteredAndSorted.length > 0 && (
        <div className="flex flex-wrap items-center justify-between gap-3 mt-3 px-2">
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500 font-bold">Filas:</span>
            {[25, 50, 100, 500, 1000].map(size => (
              <button
                key={size}
                onClick={() => { setPageSize(size); setCurrentPage(1); }}
                className={`px-2.5 py-1 rounded-lg text-xs font-bold transition-all ${
                  pageSize === size ? 'bg-indigo-600 text-white shadow' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                {size}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500">
              Mostrando {((safePage - 1) * pageSize) + 1}-{Math.min(safePage * pageSize, filteredAndSorted.length)} de {filteredAndSorted.length}
            </span>
            <button
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={safePage <= 1}
              className="p-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <ChevronLeft size={14} />
            </button>
            <span className="text-xs font-bold text-slate-700">Pág {safePage}/{totalPages}</span>
            <button
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={safePage >= totalPages}
              className="p-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <ChevronRight size={14} />
            </button>
          </div>
        </div>
      )}

      {/* ── Bandeja IA: revisión y autorización ── */}
      {inbox && (
        <div className="fixed inset-0 bg-black/60 z-[150] flex items-center justify-center p-4" onClick={() => !inbox.saving && setInbox(null)}>
          <div className="bg-white rounded-2xl w-full max-w-lg overflow-hidden" onClick={e => e.stopPropagation()}>
            <div className="bg-gradient-to-r from-fuchsia-600 to-indigo-600 text-white px-5 py-3 flex items-center justify-between">
              <h3 className="font-black text-sm uppercase flex items-center gap-2"><Sparkles size={16} /> Bandeja IA · Propuesta</h3>
              <button onClick={() => setInbox(null)} className="p-1.5 hover:bg-white/20 rounded-lg"><X size={18} /></button>
            </div>
            <div className="p-5 space-y-3">
              {inbox.loading ? (
                <p className="text-center text-slate-400 py-8 text-sm flex items-center justify-center gap-2"><Loader2 className="animate-spin" size={18} /> Analizando «{inbox.name}»…</p>
              ) : inbox.error && !inbox.prop ? (
                <p className="text-rose-600 font-bold text-sm py-4">{inbox.error}</p>
              ) : inbox.prop && (() => { const p = inbox.prop;
                const targetFicha = p.kind === 'coste' ? (fichas || []).find(f => normRef(f.ref) === normRef(p.projectRef || '')) : null;
                return (
                <>
                  <p className="text-xs text-slate-500 bg-slate-50 rounded-lg p-2">{p.resumen || 'Documento analizado.'}</p>
                  <div className="grid grid-cols-2 gap-2">
                    <div><label className="text-[10px] font-black text-slate-400 uppercase">Destino</label>
                      <select value={p.kind} onChange={e => setProp('kind', e.target.value)} className="w-full px-2 py-2 border rounded-lg text-sm">
                        <option value="venta">Venta (ficha)</option><option value="coste">Coste (proveedor)</option><option value="ingreso">Ingreso a cuenta</option>
                      </select></div>
                    {p.kind === 'venta' && <div><label className="text-[10px] font-black text-slate-400 uppercase">Tipo</label>
                      <select value={p.docType || 'factura'} onChange={e => setProp('docType', e.target.value)} className="w-full px-2 py-2 border rounded-lg text-sm">
                        {['presupuesto', 'pedido', 'albaran', 'factura'].map(t => <option key={t} value={t}>{t}</option>)}
                      </select></div>}
                    {p.kind === 'coste' && <div><label className="text-[10px] font-black text-slate-400 uppercase">Partida</label>
                      <select value={p.categoria || 'OTROS'} onChange={e => setProp('categoria', e.target.value)} className="w-full px-2 py-2 border rounded-lg text-sm">
                        {['MOBILIARIO', 'ELECTRODOMESTICOS', 'ENCIMERA', 'TRANSPORTE', 'MONTAJE', 'SUBCONTRATA', 'OTROS'].map(c => <option key={c}>{c}</option>)}
                      </select></div>}
                    <div><label className="text-[10px] font-black text-slate-400 uppercase">{p.kind === 'coste' ? 'Proveedor' : 'Cliente'}</label>
                      <input value={p.kind === 'coste' ? (p.proveedor || '') : (p.cliente || '')} onChange={e => setProp(p.kind === 'coste' ? 'proveedor' : 'cliente', e.target.value)} className="w-full px-2 py-2 border rounded-lg text-sm" /></div>
                    <div><label className="text-[10px] font-black text-slate-400 uppercase">{p.kind === 'coste' ? 'Asignar a venta (Nº/Ref)' : 'Proyecto (ref)'}</label>
                      <input list="inbox-fichas-datalist" value={p.projectRef || ''} onChange={e => setProp('projectRef', e.target.value)} placeholder="Escribe o elige LG26/…" className="w-full px-2 py-2 border rounded-lg text-sm" />
                      <datalist id="inbox-fichas-datalist">
                        {Array.from(new Map((fichas || []).filter(f => f.ref).map(f => [normRef(f.ref), f])).values())
                          .map(f => <option key={f.id} value={f.ref}>{f.ref}{f.cliente ? ` — ${f.cliente}` : ''}</option>)}
                      </datalist>
                      {p.kind === 'coste' && <p className="text-[10px] text-slate-400 mt-0.5">Elige la factura de venta a la que pertenece este coste.</p>}
                    </div>
                    {/* Coste → línea(s) concreta(s) de esa factura (para que reste en su margen) */}
                    {p.kind === 'coste' && targetFicha && (() => {
                      const imp = Number(p.total) || 0;
                      const rep = p.costeReparto || {};
                      const suma = Object.values(rep).reduce((s, v) => s + (Number(v) || 0), 0);
                      return (
                      <div className="col-span-2">
                        <div className="flex items-center justify-between">
                          <label className="text-[10px] font-black text-slate-400 uppercase">Asignar el coste a {p.costeMulti ? 'varias líneas' : 'la línea'}</label>
                          <button type="button" onClick={() => setProp('costeMulti', !p.costeMulti)} className="text-[10px] font-bold text-indigo-600 hover:text-indigo-800">
                            {p.costeMulti ? '↩ Una sola línea' : '⇄ Repartir en varias líneas'}
                          </button>
                        </div>
                        {!p.costeMulti ? (
                          <select value={p.costeLineId || ''} onChange={e => setProp('costeLineId', e.target.value)} className="w-full px-2 py-2 border rounded-lg text-sm">
                            <option value="">— Como coste de proyecto (no resta en líneas) —</option>
                            {(targetFicha.lines || []).map(l => (
                              <option key={l.id} value={l.id}>{(l.concepto || l.ref || 'Línea').slice(0, 60)} · venta {eur(l.venta)}{Number(l.coste) ? ` · coste actual ${eur(l.coste)}` : ''}</option>
                            ))}
                            <option value="__new__">➕ Añadir como línea nueva de coste</option>
                          </select>
                        ) : (
                          <div className="border border-slate-200 rounded-lg p-2 max-h-44 overflow-auto space-y-1">
                            {(targetFicha.lines || []).map(l => (
                              <div key={l.id} className="flex items-center gap-2">
                                <span className="flex-1 text-[11px] text-slate-600 truncate" title={l.concepto}>{(l.concepto || l.ref || 'Línea')} · venta {eur(l.venta)}</span>
                                <input type="number" step="0.01" value={rep[l.id] ?? ''} placeholder="0"
                                  onChange={e => setProp('costeReparto', { ...rep, [l.id]: e.target.value })}
                                  className="w-24 px-1.5 py-1 border rounded text-xs text-right" />
                                <span className="text-[10px] text-slate-400">€</span>
                              </div>
                            ))}
                            <div className="flex items-center justify-between pt-1 border-t border-slate-100 text-[11px]">
                              <button type="button" onClick={() => {
                                const ls = (targetFicha.lines || []);
                                if (!ls.length) return;
                                const each = Math.floor((imp / ls.length) * 100) / 100;
                                const nrep = {}; ls.forEach((l, i) => { nrep[l.id] = i === ls.length - 1 ? +(imp - each * (ls.length - 1)).toFixed(2) : each; });
                                setProp('costeReparto', nrep);
                              }} className="text-indigo-600 font-bold">Repartir a partes iguales</button>
                              <span className={Math.abs(suma - imp) <= 0.02 ? 'text-emerald-600 font-bold' : 'text-amber-600 font-bold'}>Suma: {eur(suma)} / {eur(imp)}</span>
                            </div>
                          </div>
                        )}
                        {!p.costeMulti && p.costeLineId && p.costeLineId !== '__new__' && <p className="text-[10px] text-emerald-600 mt-0.5">El importe se sumará al coste de esa línea y bajará su margen.</p>}
                        {p.costeMulti && Math.abs(suma - imp) > 0.02 && <p className="text-[10px] text-amber-600 mt-0.5">⚠ La suma repartida no cuadra con el importe ({eur(imp)}).</p>}
                      </div>
                      );
                    })()}
                    {p.kind === 'ingreso' && <div><label className="text-[10px] font-black text-slate-400 uppercase">Código cliente</label>
                      <input value={p.clientCode || ''} onChange={e => setProp('clientCode', e.target.value)} className="w-full px-2 py-2 border rounded-lg text-sm" /></div>}
                    <div><label className="text-[10px] font-black text-slate-400 uppercase">Nº / Ref</label>
                      <input value={p.ref || ''} onChange={e => setProp('ref', e.target.value)} className="w-full px-2 py-2 border rounded-lg text-sm" /></div>
                    <div><label className="text-[10px] font-black text-slate-400 uppercase">Importe €</label>
                      <input type="number" step="0.01" value={p.total || 0} onChange={e => setProp('total', e.target.value)} className="w-full px-2 py-2 border rounded-lg text-sm text-right" /></div>
                  </div>
                  {inbox.error && <p className="text-rose-600 font-bold text-xs">{inbox.error}</p>}
                  <button onClick={confirmarInbox} disabled={inbox.saving} className="w-full py-2.5 bg-emerald-600 text-white rounded-xl font-black text-sm hover:bg-emerald-700 disabled:opacity-50 flex items-center justify-center gap-2">
                    {inbox.saving ? <Loader2 className="animate-spin" size={16} /> : <FileCheck size={16} />} Autorizar y colocar
                  </button>
                </>
              ); })()}
            </div>
          </div>
        </div>
      )}

      {/* ── Clientes importados ── */}
      {clientsModal && (() => {
        const qn = clientsQ.trim().toLowerCase();
        const list = (clients || []).filter(c => !qn ||
          (c.nombre || '').toLowerCase().includes(qn) ||
          String(c.codigo || c.clientCode || '').toLowerCase().includes(qn) ||
          (c.email || '').toLowerCase().includes(qn));
        return (
        <div className="fixed inset-0 bg-black/60 z-[150] flex items-center justify-center p-4" onClick={() => setClientsModal(false)}>
          <div className="bg-white rounded-3xl w-full max-w-2xl max-h-[85vh] overflow-hidden flex flex-col" onClick={e => e.stopPropagation()}>
            <div className="bg-indigo-700 text-white px-6 py-4 flex justify-between items-center shrink-0">
              <h2 className="text-lg font-black flex items-center gap-2"><Users size={18} /> Clientes importados ({(clients || []).length})</h2>
              <button onClick={() => setClientsModal(false)} className="p-2 hover:bg-white/20 rounded-xl"><X size={20} /></button>
            </div>
            <div className="p-4 border-b border-slate-100">
              <input value={clientsQ} onChange={e => setClientsQ(e.target.value)} placeholder="Buscar por nombre, código o email…"
                className="w-full px-3 py-2 border border-slate-200 rounded-xl text-sm outline-none focus:border-indigo-400" autoFocus />
            </div>
            <div className="overflow-auto">
              <table className="w-full text-sm">
                <thead className="bg-slate-50 text-slate-500 sticky top-0"><tr>
                  <th className="text-left p-2.5 text-[10px] font-black uppercase">Nombre</th>
                  <th className="text-left p-2.5 text-[10px] font-black uppercase">Código</th>
                  <th className="text-left p-2.5 text-[10px] font-black uppercase">Contacto</th>
                  <th className="p-2.5"></th>
                </tr></thead>
                <tbody className="divide-y divide-slate-100">
                  {list.map((c, k) => (
                    <tr key={c.id || k} className="hover:bg-slate-50">
                      <td className="p-2.5 font-bold text-slate-700">{c.nombre || '—'}</td>
                      <td className="p-2.5 text-slate-500">{c.codigo || c.clientCode || '—'}</td>
                      <td className="p-2.5 text-slate-500 text-xs">{[c.email, c.telefono || c.phone].filter(Boolean).join(' · ') || '—'}</td>
                      <td className="p-2.5 text-right"><button onClick={() => { setColumnFilters(prev => ({ ...prev, cliente: c.nombre || '' })); setCurrentPage(1); setClientsModal(false); }}
                        className="px-3 py-1.5 bg-indigo-600 text-white rounded-lg text-xs font-bold hover:bg-indigo-700">Ver documentos</button></td>
                    </tr>
                  ))}
                  {list.length === 0 && <tr><td colSpan={4} className="p-8 text-center text-slate-400 text-sm">Sin clientes.</td></tr>}
                </tbody>
              </table>
            </div>
          </div>
        </div>
        );
      })()}

      {/* ── Editor de ficha ── */}
      {editor && (
        <div className="fixed inset-0 bg-black/60 z-[140] flex items-center justify-center p-3 sm:p-6" onClick={() => !saving && setEditor(null)}>
          <div className="bg-white rounded-3xl w-full max-w-6xl max-h-[95vh] overflow-hidden flex flex-col" onClick={e => e.stopPropagation()}>
            <div className="bg-emerald-600 text-white px-6 py-4 flex justify-between items-center shrink-0">
              <h2 className="text-lg font-black flex items-center gap-2"><FileText size={18} /> {TABS.find(t => t.key === editor.docType)?.label} - lineas y costes</h2>
              <button onClick={() => !saving && setEditor(null)} className="p-2 hover:bg-white/20 rounded-xl"><X size={20} /></button>
            </div>
            <div className="p-5 overflow-y-auto">
              {/* Cabecera editable */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-4">
                <div><label className="text-[10px] font-black text-slate-400 uppercase">N. / Ref</label>
                  <input value={editor.ref} onChange={e => setEditor({ ...editor, ref: e.target.value })} className="w-full px-2 py-1.5 border rounded-lg text-sm" /></div>
                <div><label className="text-[10px] font-black text-slate-400 uppercase">Cliente</label>
                  <input value={editor.cliente} onChange={e => setEditor({ ...editor, cliente: e.target.value })} className="w-full px-2 py-1.5 border rounded-lg text-sm" /></div>
                <div><label className="text-[10px] font-black text-slate-400 uppercase">Codigo cliente</label>
                  <input value={editor.clienteCodigo || ''} onChange={e => setEditor({ ...editor, clienteCodigo: e.target.value })} placeholder="ej. 12345" className="w-full px-2 py-1.5 border rounded-lg text-sm" />
                  {editor.cliente && (editor.clienteCodigo || '').trim() && (
                    <button type="button" onClick={aplicarCodigoATodas}
                      className="mt-1 text-[10px] font-bold text-indigo-600 hover:text-indigo-800 underline">
                      Aplicar código a todas las fichas de {editor.cliente}
                    </button>
                  )}</div>
                <div><label className="text-[10px] font-black text-slate-400 uppercase">Fecha</label>
                  <input value={editor.fecha} onChange={e => setEditor({ ...editor, fecha: e.target.value })} className="w-full px-2 py-1.5 border rounded-lg text-sm" /></div>
                <div><label className="text-[10px] font-black text-slate-400 uppercase">Estado</label>
                  <select value={editor.docType} onChange={e => setEditor({ ...editor, docType: e.target.value })} className="w-full px-2 py-1.5 border rounded-lg text-sm font-bold">
                    {TABS.map(t => <option key={t.key} value={t.key}>{t.label}</option>)}
                  </select></div>
              </div>

              {/* Acciones de coste */}
              <div className="flex items-center gap-2 mb-2">
                <label className={`px-3 py-1.5 rounded-lg font-bold text-xs flex items-center gap-1.5 cursor-pointer ${matching ? 'bg-blue-200 text-blue-500' : 'bg-blue-600 text-white hover:bg-blue-700'}`}>
                  <Sparkles size={14} className={matching ? 'animate-pulse' : ''} />
                  {matching ? 'Emparejando...' : 'Subir pantallazo de costes (IA empareja · o pega con Ctrl+V)'}
                  <input type="file" accept="image/*,application/pdf" className="hidden" onChange={handleCostShot} disabled={matching} />
                </label>
                <button onClick={handleAutoCostes} disabled={feeding} title="Rellena el coste de cada línea con el coste medio ponderado del catálogo, casando por la referencia del artículo" className={`px-3 py-1.5 rounded-lg font-bold text-xs flex items-center gap-1.5 ${feeding ? 'bg-emerald-200 text-emerald-500' : 'bg-emerald-600 text-white hover:bg-emerald-700'}`}>
                  <span className={feeding ? 'animate-pulse' : ''}>💰</span>
                  {feeding ? 'Alimentando...' : 'Alimentar costes (catálogo)'}
                </button>
                <button onClick={addLine} className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 rounded-lg text-xs font-bold flex items-center gap-1"><Plus size={14} /> Anadir linea</button>
              </div>

              {/* Tabla de lineas editable */}
              <div className="border border-slate-200 rounded-xl overflow-hidden">
                <table className="w-full text-sm table-fixed">
                  <colgroup>
                    <col style={{ width: '150px' }} />
                    <col />
                    <col style={{ width: '46px' }} />
                    <col style={{ width: '82px' }} />
                    <col style={{ width: '85px' }} />
                    <col style={{ width: '85px' }} />
                    <col style={{ width: '82px' }} />
                    <col style={{ width: '54px' }} />
                    <col style={{ width: '32px' }} />
                  </colgroup>
                  <thead className="bg-slate-100 text-slate-500">
                    <tr>
                      <th className="text-left p-2 text-[10px] font-black uppercase">Ref</th>
                      <th className="text-left p-2 text-[10px] font-black uppercase">Concepto</th>
                      <th className="text-right p-2 text-[10px] font-black uppercase">Cant.</th>
                      <th className="text-right p-2 text-[10px] font-black uppercase">Coste ud.</th>
                      <th className="text-right p-2 text-[10px] font-black uppercase">Coste</th>
                      <th className="text-right p-2 text-[10px] font-black uppercase">Venta</th>
                      <th className="text-right p-2 text-[10px] font-black uppercase">Beneficio</th>
                      <th className="text-right p-2 text-[10px] font-black uppercase">%</th>
                      <th className="p-2"></th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {editor.lines.map((l, i) => {
                      const cEf = costeEfectivo(l.venta, l.coste);   // en abonos (venta<0) el coste resta
                      const m = (Number(l.venta) || 0) - cEf;
                      // % = incremento sobre el coste (cuánto se sube el coste hasta la venta)
                      const mpct = Math.abs(cEf) > 0 ? (m / Math.abs(cEf) * 100) : null;
                      const cant = Number(l.cantidad) || 1;
                      const costeUd = cant > 0 ? (Number(l.coste) || 0) / cant : (Number(l.coste) || 0);
                      return (
                        <tr key={l.id || i}>
                          <td className="p-1"><input value={l.ref} onChange={e => setLine(i, 'ref', e.target.value)} className="w-full px-1.5 py-1 border rounded text-xs" /></td>
                          <td className="p-1"><input value={l.concepto} onChange={e => setLine(i, 'concepto', e.target.value)} className="w-full px-1.5 py-1 border rounded text-xs" /></td>
                          <td className="p-1"><input
                            type="text" inputMode="decimal"
                            value={l.cantidad ?? 1}
                            onChange={e => setLine(i, 'cantidad', e.target.value)}
                            onBlur={e => blurLine(i, 'cantidad', e.target.value)}
                            className="w-full px-1.5 py-1 border rounded text-xs text-right"
                          /></td>
                          <td className="p-1"><input
                            type="text" inputMode="decimal"
                            value={l.costeUdRaw ?? (costeUd ? String(costeUd) : '')}
                            title="Coste unitario (Coste ÷ Cantidad). Editable: recalcula el coste total × cantidad."
                            onChange={e => { const lines = [...editor.lines]; lines[i] = { ...lines[i], costeUdRaw: e.target.value }; setEditor({ ...editor, lines }); }}
                            onBlur={e => { const v = parseDecimal(e.target.value); const lines = [...editor.lines]; const c = Number(lines[i].cantidad) || 1; lines[i] = { ...lines[i], coste: Number((v * c).toFixed(2)), costeUdRaw: undefined }; setEditor({ ...editor, lines }); }}
                            className="w-full px-1.5 py-1 border rounded text-xs text-right text-slate-600"
                          /></td>
                          <td className="p-1"><input
                            type="text" inputMode="decimal"
                            value={l.coste}
                            onChange={e => setLine(i, 'coste', e.target.value)}
                            onBlur={e => blurLine(i, 'coste', e.target.value)}
                            placeholder="0"
                            className={`w-full px-1.5 py-1 border rounded text-xs text-right ${l._match ? 'bg-blue-50 border-blue-200' : ''}`}
                          /></td>
                          <td className="p-1"><input
                            type="text" inputMode="decimal"
                            value={l.venta}
                            onChange={e => setLine(i, 'venta', e.target.value)}
                            onBlur={e => blurLine(i, 'venta', e.target.value)}
                            placeholder="0"
                            className="w-full px-1.5 py-1 border rounded text-xs text-right"
                          /></td>
                          <td className={`p-1 text-right font-mono font-bold ${m >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>{eur(m)}</td>
                          <td className={`p-1 text-right font-mono font-bold text-xs ${m >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>{mpct === null ? '—' : `${mpct.toFixed(1)}%`}</td>
                          <td className="p-1 text-center"><button onClick={() => removeLine(i)} className="text-slate-300 hover:text-red-500"><Trash2 size={13} /></button></td>
                        </tr>
                      );
                    })}
                    {editor.lines.length === 0 && <tr><td colSpan={9} className="p-4 text-center text-slate-400 text-xs">Sin lineas</td></tr>}
                  </tbody>
                </table>
              </div>

              {/* Totales del editor */}
              {et && (
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-4">
                  <div className="bg-orange-50 p-3 rounded-xl text-center"><p className="text-[10px] uppercase text-orange-500 font-black">Coste</p><p className="text-lg font-black text-orange-700">{eur(et.coste)}</p></div>
                  <div className="bg-indigo-50 p-3 rounded-xl text-center"><p className="text-[10px] uppercase text-indigo-500 font-black">Venta</p><p className="text-lg font-black text-indigo-700">{eur(et.venta)}</p></div>
                  <div className={`${et.margen >= 0 ? 'bg-emerald-50' : 'bg-red-50'} p-3 rounded-xl text-center`}><p className={`text-[10px] uppercase font-black ${et.margen >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>Beneficio ({et.coste > 0 ? (et.margen / et.coste * 100).toFixed(1) : '0.0'}%)</p><p className={`text-lg font-black ${et.margen >= 0 ? 'text-emerald-700' : 'text-red-700'}`}>{eur(et.margen)}</p></div>
                </div>
              )}
            </div>
            <div className="p-4 border-t shrink-0">
              <button onClick={saveFicha} disabled={saving} className="w-full py-3 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white rounded-xl font-black uppercase text-sm flex items-center justify-center gap-2">
                {saving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />} Guardar ficha
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Consulta de ficha ── */}
      {viewing && (
        <div className="fixed inset-0 bg-black/60 z-[140] flex items-center justify-center p-4" onClick={() => setViewing(null)}>
          <div className="bg-white rounded-3xl w-full max-w-3xl max-h-[92vh] overflow-hidden flex flex-col" onClick={e => e.stopPropagation()}>
            <div className="bg-slate-800 text-white px-6 py-4 flex justify-between items-center shrink-0">
              <div>
                <h2 className="text-lg font-black">{viewing.ref || 'Ficha'} - {viewing.cliente}</h2>
                <p className="text-xs opacity-70">{TABS.find(t => t.key === viewing.docType)?.label} - {viewing.fecha}</p>
              </div>
              <div className="flex items-center gap-2">
                {onBackToReport && (
                  <button onClick={() => { setViewing(null); onBackToReport(); }}
                    className="px-3 py-1.5 bg-indigo-500 hover:bg-indigo-400 rounded-lg text-xs font-bold">← Volver al informe</button>
                )}
                <button onClick={() => {
                    if (bloqueada(viewing)) { alert('Ficha con visto bueno del controller: bloqueada.\n\nSolo el master puede modificarla: mantén pulsada la tecla Shift un par de segundos (desbloqueo) y vuelve a intentarlo.'); return; }
                    setViewing(null); setEditor({ ...viewing, saleDoc: null, costDocs: [], existingDocs: viewing.docs || [] });
                  }}
                  className="px-3 py-1.5 bg-white/15 hover:bg-white/25 rounded-lg text-xs font-bold">{bloqueada(viewing) ? '🔒 Editar' : 'Editar'}</button>
                <button onClick={() => setViewing(null)} className="p-2 hover:bg-white/20 rounded-xl"><X size={20} /></button>
              </div>
            </div>
            <div className="p-5 overflow-y-auto">
              {/* Documentos asociados */}
              <h3 className="text-xs font-black text-slate-500 uppercase mb-2">Documentos asociados</h3>
              <div className="flex flex-wrap gap-2 mb-5">
                {(viewing.docs || []).length === 0 && <p className="text-sm text-slate-400">Sin documentos.</p>}
                {(viewing.docs || []).map(d => (
                  <button key={d.id} onClick={() => viewDoc(viewing.id, d.id)}
                    className={`px-3 py-2 rounded-lg text-xs font-bold flex items-center gap-1.5 border ${d.kind === 'venta' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-blue-50 text-blue-700 border-blue-200'} hover:shadow`}>
                    <Eye size={14} /> {d.kind === 'venta' ? 'Venta' : 'Coste'}: {d.filename}
                  </button>
                ))}
              </div>

              {/* Lineas */}
              <div className="border border-slate-200 rounded-xl overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-slate-100 text-slate-500"><tr>
                    <th className="text-left p-2 text-[10px] font-black uppercase">Concepto</th>
                    <th className="text-right p-2 text-[10px] font-black uppercase">Coste</th>
                    <th className="text-right p-2 text-[10px] font-black uppercase">Venta</th>
                    <th className="text-right p-2 text-[10px] font-black uppercase">Margen</th>
                    <th className="text-right p-2 text-[10px] font-black uppercase">%</th>
                  </tr></thead>
                  <tbody className="divide-y divide-slate-100">
                    {(viewing.lines || []).map((l, i) => {
                      const cEf = costeEfectivo(l.venta, l.coste);   // abono: coste resta
                      const m = (Number(l.venta) || 0) - cEf;
                      const mpct = Math.abs(cEf) > 0 ? (m / Math.abs(cEf) * 100) : null;
                      return (<tr key={l.id || i}>
                        <td className="p-2">{l.ref ? <span className="text-slate-400 mr-1">[{l.ref}]</span> : null}{l.concepto}{(Number(l.venta) || 0) < 0 && <span className="ml-1 text-[9px] font-bold text-amber-600">(abono)</span>}</td>
                        <td className="p-2 text-right font-mono text-orange-600">{eur(cEf)}</td>
                        <td className="p-2 text-right font-mono">{eur(l.venta)}</td>
                        <td className={`p-2 text-right font-mono font-bold ${m >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>{eur(m)}</td>
                        <td className={`p-2 text-right font-mono font-bold text-xs ${m >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>{mpct === null ? '—' : `${mpct.toFixed(1)}%`}</td>
                      </tr>);
                    })}
                  </tbody>
                </table>
              </div>
              {viewing.totals && (
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-4">
                  <div className="bg-orange-50 p-3 rounded-xl text-center"><p className="text-[10px] uppercase text-orange-500 font-black">Coste</p><p className="text-lg font-black text-orange-700">{eur(viewing.totals.coste)}</p></div>
                  <div className="bg-indigo-50 p-3 rounded-xl text-center"><p className="text-[10px] uppercase text-indigo-500 font-black">Venta</p><p className="text-lg font-black text-indigo-700">{eur(viewing.totals.venta)}</p></div>
                  <div className={`${viewing.totals.margen >= 0 ? 'bg-emerald-50' : 'bg-red-50'} p-3 rounded-xl text-center`}><p className={`text-[10px] uppercase font-black ${viewing.totals.margen >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>Margen ({viewing.totals.coste > 0 ? (viewing.totals.margen / viewing.totals.coste * 100).toFixed(1) : '0.0'}%)</p><p className={`text-lg font-black ${viewing.totals.margen >= 0 ? 'text-emerald-700' : 'text-red-700'}`}>{eur(viewing.totals.margen)}</p></div>
                </div>
              )}
              {(viewing.costesProyecto || 0) > 0 && (viewing.costesProyecto !== viewing.totals?.coste) && (
                <p className="text-xs text-indigo-600 font-bold mt-1">
                  Este proyecto ya tiene {eur(viewing.costesProyecto)} de coste registrado en Rentabilidad &gt; Costes por proyecto — revisa si coincide con el coste de estas líneas antes de dar el margen por bueno.
                </p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RentabilidadLineas;
