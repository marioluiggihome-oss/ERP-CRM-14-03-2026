import React, { useState, useMemo, useRef, useEffect } from 'react';
import { Plus, Trash2, Download, Layers, FileText, Save, FolderOpen, X, Loader, ChevronUp, ChevronDown, GripVertical, AlignLeft, AlignCenter, AlignRight, Move, RotateCcw } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Cuentas bancarias para reflejar en el presupuesto (titular PUBLIOFERTA S.L.).
const BANCOS = [
  { id: 'santander', nombre: 'Banco Santander', titular: 'PUBLIOFERTA S.L.', iban: 'ES13 0049 5558 0020 1635 1274', swift: 'BSCHESMM' },
  { id: 'bbva', nombre: 'BBVA', titular: 'PUBLIOFERTA S.L.', iban: 'ES38 0182 5581 9302 0159 9858', swift: 'BBVAESMMXXX' },
];

// Resumen por cocinas: junta partidas a mano (Muebles, Electrodomésticos,
// Encimera…) por cada cocina, suma totales y forma de pago, y lo presenta /
// exporta a PDF con el logotipo. Pensado para presentar al cliente.

const eur = (n) => `${(Number(n) || 0).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} €`;
const uid = () => Math.random().toString(36).slice(2, 9);

const ResumenCocinas = ({ state }) => {
  const today = new Date().toLocaleDateString('es-ES');
  const [cliente, setCliente] = useState('');
  const [fecha, setFecha] = useState(today);
  const [cocinas, setCocinas] = useState([
    { id: uid(), nombre: 'COCINA PRINCIPAL', lineas: [
      { id: uid(), concepto: 'MUEBLES', importe: '' },
      { id: uid(), concepto: 'ELECTRODOMÉSTICOS', importe: '' },
      { id: uid(), concepto: 'ENCIMERA', importe: '' },
    ] },
  ]);
  const [pagos, setPagos] = useState([
    { id: uid(), label: '50% al hacer pedido', percent: 50 },
    { id: uid(), label: '45% a la entrega de materiales', percent: 45 },
    { id: uid(), label: '5% al terminar', percent: 5 },
  ]);
  const [exporting, setExporting] = useState(false);
  const [ivaIncluido, setIvaIncluido] = useState(true); // los importes ya llevan IVA
  const [ivaRate, setIvaRate] = useState(21);            // tipo de IVA
  const [bancoId, setBancoId] = useState('');     // cuenta bancaria elegida
  const [docName, setDocName] = useState('');     // nombre con el que se guarda
  const [savedId, setSavedId] = useState(null);
  const [savedList, setSavedList] = useState(null); // null = oculto
  const [busy, setBusy] = useState(false);
  // Alineación del contenido en pantalla (izquierda/centro/derecha), recordada.
  const [align, setAlign] = useState(() => (typeof localStorage !== 'undefined' && localStorage.getItem('resumen_align')) || 'center');
  const alignCls = align === 'left' ? 'mr-auto ml-0' : align === 'right' ? 'ml-auto mr-0' : 'mx-auto';
  const setAlignPersist = (a) => { setAlign(a); try { localStorage.setItem('resumen_align', a); } catch (_) {} };
  // Desplazamiento horizontal fino (arrastrar), en píxeles, recordado.
  const [offsetX, setOffsetX] = useState(() => Number((typeof localStorage !== 'undefined' && localStorage.getItem('resumen_offsetX')) || 0) || 0);
  const dragPos = useRef(null);
  const startDrag = (e) => {
    const cx = e.clientX ?? (e.touches && e.touches[0]?.clientX) ?? 0;
    dragPos.current = { startX: cx, startOffset: offsetX };
    const onMove = (ev) => {
      if (!dragPos.current) return;
      const x = ev.clientX ?? (ev.touches && ev.touches[0]?.clientX) ?? 0;
      const next = Math.max(-600, Math.min(600, dragPos.current.startOffset + (x - dragPos.current.startX)));
      setOffsetX(next);
    };
    const onUp = () => {
      dragPos.current = null;
      try { localStorage.setItem('resumen_offsetX', String(offsetXRef.current)); } catch (_) {}
      window.removeEventListener('mousemove', onMove); window.removeEventListener('mouseup', onUp);
      window.removeEventListener('touchmove', onMove); window.removeEventListener('touchend', onUp);
    };
    window.addEventListener('mousemove', onMove); window.addEventListener('mouseup', onUp);
    window.addEventListener('touchmove', onMove); window.addEventListener('touchend', onUp);
  };
  const offsetXRef = useRef(offsetX);
  offsetXRef.current = offsetX;
  const resetPos = () => { setOffsetX(0); setAlignPersist('center'); try { localStorage.setItem('resumen_offsetX', '0'); } catch (_) {} };
  // Render 3D adjuntado desde Estudio 3D (se incluye en el PDF si el usuario quiere).
  const [render3d, setRender3d] = useState(null);
  useEffect(() => {
    try { const raw = localStorage.getItem('render3d_attach'); if (raw) setRender3d(JSON.parse(raw)); } catch (_) {}
  }, []);
  const quitarRender3d = () => { setRender3d(null); try { localStorage.removeItem('render3d_attach'); } catch (_) {} };
  const dragStyle = offsetX ? { transform: `translateX(${offsetX}px)` } : undefined;
  const uidUser = state?.currentUser?.id || 'anonymous';
  // Origen del arrastre (drag & drop). {kind:'linea'|'pago', cid, id}
  const dragRef = useRef(null);
  const [dragKey, setDragKey] = useState(null); // para feedback visual de la fila arrastrada

  // ── guardar / historial ──
  const saveResumen = async () => {
    const name = (docName || cliente || '').trim();
    if (!name) { alert('Pon un nombre (o cliente) para guardar el resumen.'); return; }
    setBusy(true);
    try {
      const r = await fetch(`${API_URL}/api/resumen-totales`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: savedId || undefined, userId: uidUser, name, data: { cliente, fecha, cocinas, pagos, bancoId, ivaIncluido, ivaRate } }),
      });
      const d = await r.json();
      if (d.id) { setSavedId(d.id); setDocName(name); alert('✅ Resumen guardado. Lo tienes en "Mis resúmenes".'); }
      else alert('No se pudo guardar.');
    } catch { alert('Error al guardar el resumen.'); }
    finally { setBusy(false); }
  };
  const openList = async () => {
    try {
      const r = await fetch(`${API_URL}/api/resumen-totales?userId=${encodeURIComponent(uidUser)}`);
      const d = await r.json();
      setSavedList(d.items || []);
    } catch { alert('No se pudo cargar la lista.'); }
  };
  const loadResumen = async (id) => {
    try {
      const r = await fetch(`${API_URL}/api/resumen-totales/${id}`);
      const doc = await r.json();
      const data = doc.data || {};
      setCliente(data.cliente || ''); setFecha(data.fecha || today);
      setCocinas(data.cocinas || []); setPagos(data.pagos || []); setBancoId(data.bancoId || '');
      setIvaIncluido(data.ivaIncluido !== false); setIvaRate(data.ivaRate ?? 21);
      setSavedId(doc.id); setDocName(doc.name || ''); setSavedList(null);
    } catch { alert('No se pudo abrir el resumen.'); }
  };
  const nuevoResumen = () => {
    if (!window.confirm('¿Empezar un resumen nuevo en blanco? Se perderá lo no guardado.')) return;
    setCliente(''); setFecha(today); setDocName(''); setSavedId(null);
    setCocinas([{ id: uid(), nombre: 'COCINA PRINCIPAL', lineas: [
      { id: uid(), concepto: 'MUEBLES', importe: '' },
      { id: uid(), concepto: 'ELECTRODOMÉSTICOS', importe: '' },
      { id: uid(), concepto: 'ENCIMERA', importe: '' },
    ] }]);
    setPagos([
      { id: uid(), label: '50% al hacer pedido', percent: 50 },
      { id: uid(), label: '45% a la entrega de materiales', percent: 45 },
      { id: uid(), label: '5% al terminar', percent: 5 },
    ]);
    setIvaIncluido(true); setIvaRate(21);
  };

  const deleteResumen = async (id, name) => {
    if (!window.confirm(`¿Eliminar "${name || ''}"?`)) return;
    try {
      await fetch(`${API_URL}/api/resumen-totales/${id}`, { method: 'DELETE' });
      setSavedList(prev => (prev || []).filter(it => it.id !== id));
      if (savedId === id) setSavedId(null);
    } catch { alert('No se pudo eliminar.'); }
  };

  const cocinaTotal = (c) => (c.lineas || []).reduce((s, l) => s + (Number(l.importe) || 0), 0);
  const totalGeneral = useMemo(() => cocinas.reduce((s, c) => s + cocinaTotal(c), 0), [cocinas]);
  // Desglose de impuestos. Si el IVA va incluido, base = total / (1+tipo); si no,
  // el total mostrado es base y el IVA se suma aparte.
  const r = (Number(ivaRate) || 0) / 100;
  const baseImponible = ivaIncluido ? totalGeneral / (1 + r) : totalGeneral;
  const cuotaIva = ivaIncluido ? totalGeneral - baseImponible : totalGeneral * r;
  const totalConIva = baseImponible + cuotaIva;

  // ── edición ──
  const addCocina = () => setCocinas(prev => [...prev, { id: uid(), nombre: `COCINA ${prev.length + 1}`, lineas: [
    { id: uid(), concepto: 'MUEBLES', importe: '' },
    { id: uid(), concepto: 'ELECTRODOMÉSTICOS', importe: '' },
    { id: uid(), concepto: 'ENCIMERA', importe: '' },
  ] }]);
  const removeCocina = (id) => setCocinas(prev => prev.filter(c => c.id !== id));
  const setCocinaNombre = (id, nombre) => setCocinas(prev => prev.map(c => c.id === id ? { ...c, nombre } : c));
  const addLinea = (cid) => setCocinas(prev => prev.map(c => c.id === cid ? { ...c, lineas: [...c.lineas, { id: uid(), concepto: '', importe: '' }] } : c));
  const removeLinea = (cid, lid) => setCocinas(prev => prev.map(c => c.id === cid ? { ...c, lineas: c.lineas.filter(l => l.id !== lid) } : c));
  // Helpers de reordenación (intercambio por flechas / colocación por arrastre).
  const swap = (arr, i, j) => { const a = [...arr]; [a[i], a[j]] = [a[j], a[i]]; return a; };
  // Coloca el elemento fromId justo en la posición del toId (arrastrar y soltar).
  const reorder = (arr, fromId, toId) => {
    const from = arr.findIndex(x => x.id === fromId);
    const to = arr.findIndex(x => x.id === toId);
    if (from < 0 || to < 0 || from === to) return arr;
    const a = [...arr];
    const [m] = a.splice(from, 1);
    a.splice(to, 0, m);
    return a;
  };

  // ── Partidas (dentro de una cocina) ──
  const moveLinea = (cid, lid, dir) => setCocinas(prev => prev.map(c => {
    if (c.id !== cid) return c;
    const i = c.lineas.findIndex(l => l.id === lid); const j = i + dir;
    if (i < 0 || j < 0 || j >= c.lineas.length) return c;
    return { ...c, lineas: swap(c.lineas, i, j) };
  }));
  const reorderLinea = (cid, fromId, toId) => setCocinas(prev => prev.map(c =>
    c.id === cid ? { ...c, lineas: reorder(c.lineas, fromId, toId) } : c));

  // ── Cocinas ──
  const moveCocina = (id, dir) => setCocinas(prev => {
    const i = prev.findIndex(c => c.id === id); const j = i + dir;
    if (i < 0 || j < 0 || j >= prev.length) return prev;
    return swap(prev, i, j);
  });
  const reorderCocina = (fromId, toId) => setCocinas(prev => reorder(prev, fromId, toId));

  // ── Drag & drop genérico ──
  const onDragStartRow = (kind, cid, id) => (e) => { dragRef.current = { kind, cid, id }; setDragKey(id); e.dataTransfer.effectAllowed = 'move'; };
  const onDropRow = (kind, cid, toId) => (e) => {
    e.preventDefault(); const d = dragRef.current; dragRef.current = null; setDragKey(null);
    if (!d || d.kind !== kind || d.id === toId) return;
    if (kind === 'linea') { if (d.cid !== cid) return; reorderLinea(cid, d.id, toId); }
    else if (kind === 'cocina') reorderCocina(d.id, toId);
    else if (kind === 'pago') reorderPagoDD(d.id, toId);
  };
  const allowDrop = (e) => e.preventDefault();
  const setLinea = (cid, lid, field, val) => setCocinas(prev => prev.map(c => c.id === cid ? { ...c, lineas: c.lineas.map(l => l.id === lid ? { ...l, [field]: val } : l) } : c));

  const addPago = () => setPagos(prev => [...prev, { id: uid(), label: '', percent: 0 }]);
  const removePago = (id) => setPagos(prev => prev.filter(p => p.id !== id));
  const setPago = (id, field, val) => setPagos(prev => prev.map(p => p.id === id ? { ...p, [field]: val } : p));
  const movePago = (id, dir) => setPagos(prev => {
    const i = prev.findIndex(p => p.id === id); const j = i + dir;
    if (i < 0 || j < 0 || j >= prev.length) return prev;
    return swap(prev, i, j);
  });
  const reorderPagoDD = (fromId, toId) => setPagos(prev => reorder(prev, fromId, toId));

  // ── PDF ──
  const exportPDF = async () => {
    setExporting(true);
    try {
      const { jsPDF } = await import('jspdf');
      const pdf = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
      const W = pdf.internal.pageSize.getWidth();
      const pageH = pdf.internal.pageSize.getHeight();
      const M = 16;
      let y = 16;
      const logo = state?.logo;
      if (logo && typeof logo === 'string' && logo.startsWith('data:')) {
        try {
          const fmt = logo.includes('image/png') ? 'PNG' : (logo.includes('image/webp') ? 'WEBP' : 'JPEG');
          pdf.addImage(logo, fmt, M, y, 34, 17);
        } catch (_) { /* omitir */ }
      } else {
        pdf.setFontSize(16); pdf.setTextColor(30); pdf.setFont(undefined, 'bold');
        pdf.text('LUIGGI HOME', M, y + 9); pdf.setFont(undefined, 'normal');
      }
      pdf.setFontSize(17); pdf.setTextColor(30, 27, 65); pdf.setFont(undefined, 'bold');
      pdf.text('PRESUPUESTO', W - M, y + 6, { align: 'right' });
      pdf.setFont(undefined, 'normal'); pdf.setFontSize(10); pdf.setTextColor(120);
      pdf.text(fecha || today, W - M, y + 12, { align: 'right' });
      y += 24;
      if (cliente) { pdf.setFontSize(12); pdf.setTextColor(30, 27, 75); pdf.setFont(undefined, 'bold'); pdf.text(cliente, M, y); pdf.setFont(undefined, 'normal'); y += 8; }

      const ensure = (need) => { if (y + need > pageH - M) { pdf.addPage(); y = 18; } };

      cocinas.forEach(c => {
        ensure(14 + c.lineas.length * 7 + 10);
        pdf.setFillColor(30, 27, 65); pdf.roundedRect(M, y, W - 2 * M, 8, 1.5, 1.5, 'F');
        pdf.setFontSize(11); pdf.setTextColor(255); pdf.setFont(undefined, 'bold');
        pdf.text((c.nombre || 'COCINA').toUpperCase(), M + 3, y + 5.5);
        pdf.setFont(undefined, 'normal'); y += 12;
        pdf.setFontSize(10.5); pdf.setTextColor(60);
        c.lineas.forEach(l => {
          pdf.text(l.concepto || '', M + 4, y);
          pdf.text(eur(l.importe), W - M - 2, y, { align: 'right' });
          y += 6.5;
        });
        // total cocina
        pdf.setDrawColor(210); pdf.line(W - M - 70, y - 2, W - M - 2, y - 2);
        pdf.setFont(undefined, 'bold'); pdf.setTextColor(30, 27, 65);
        pdf.text('TOTAL', W - M - 70, y + 3);
        pdf.text(eur(cocinaTotal(c)), W - M - 2, y + 3, { align: 'right' });
        pdf.setFont(undefined, 'normal');
        y += 12;
      });

      // Desglose de impuestos (base + IVA)
      ensure(16);
      pdf.setFontSize(10.5); pdf.setTextColor(60);
      pdf.text('Base imponible', M + 4, y);
      pdf.text(eur(baseImponible), W - M - 2, y, { align: 'right' }); y += 6;
      pdf.text(`IVA (${ivaRate}%)`, M + 4, y);
      pdf.text(eur(cuotaIva), W - M - 2, y, { align: 'right' }); y += 8;

      // total general (caja naranja)
      ensure(18);
      pdf.setFillColor(234, 120, 40); pdf.roundedRect(M, y, W - 2 * M, 13, 2, 2, 'F');
      pdf.setFontSize(12); pdf.setTextColor(255); pdf.setFont(undefined, 'bold');
      pdf.text(`TOTAL GENERAL (IVA ${ivaRate}% incl.)`, M + 4, y + 8.5);
      pdf.setFontSize(14); pdf.text(eur(totalConIva), W - M - 3, y + 8.5, { align: 'right' });
      pdf.setFont(undefined, 'normal'); y += 20;

      // forma de pago
      const pagosValidos = pagos.filter(p => p.label || p.percent);
      if (pagosValidos.length) {
        ensure(10 + pagosValidos.length * 7);
        pdf.setFontSize(11); pdf.setTextColor(30, 27, 65); pdf.setFont(undefined, 'bold');
        pdf.text('Forma de pago:', M, y); pdf.setFont(undefined, 'normal'); y += 7;
        pdf.setFontSize(10.5); pdf.setTextColor(60);
        pagosValidos.forEach(p => {
          pdf.text(p.label || '', M + 4, y);
          pdf.text(eur(totalConIva * (Number(p.percent) || 0) / 100), W - M - 2, y, { align: 'right' });
          y += 6.5;
        });
      }

      // Cuenta bancaria elegida (datos para el pago).
      const banco = BANCOS.find(b => b.id === bancoId);
      if (banco) {
        ensure(20);
        y += 4;
        pdf.setFontSize(11); pdf.setTextColor(30, 27, 65); pdf.setFont(undefined, 'bold');
        pdf.text('Forma de pago: Transferencia a:', M, y); pdf.setFont(undefined, 'normal'); y += 6;
        pdf.setFontSize(10.5); pdf.setTextColor(60);
        pdf.text(`${banco.nombre} — Titular: ${banco.titular}`, M + 4, y); y += 6;
        pdf.setFont(undefined, 'bold'); pdf.text(`IBAN: ${banco.iban}`, M + 4, y);
        pdf.setFont(undefined, 'normal');
        if (banco.swift) pdf.text(`SWIFT: ${banco.swift}`, W - M - 2, y, { align: 'right' });
        y += 6;
      }

      // Render 3D adjunto (si lo hay): en página aparte a tamaño grande.
      if (render3d?.image) {
        try {
          pdf.addPage();
          const props = pdf.getImageProperties(render3d.image);
          const areaW = W - 2 * M, areaH = pageH - 40;
          const ratio = Math.min(areaW / props.width, areaH / props.height);
          const iw = props.width * ratio, ih = props.height * ratio;
          pdf.setFontSize(13); pdf.setTextColor(30, 27, 65); pdf.setFont(undefined, 'bold');
          pdf.text('Propuesta de diseño 3D', M, 20); pdf.setFont(undefined, 'normal');
          pdf.addImage(render3d.image, 'PNG', M + (areaW - iw) / 2, 26, iw, ih);
        } catch (_) { /* omitir si la imagen no es válida */ }
      }

      pdf.save(`Presupuesto_${(cliente || 'cocinas').replace(/\s+/g, '_')}.pdf`);
    } catch (e) {
      alert('No se pudo generar el PDF: ' + (e.message || ''));
    } finally { setExporting(false); }
  };

  return (
    <div className="h-full min-h-screen flex flex-col p-6 bg-slate-50 overflow-y-auto">
      <div style={dragStyle} className={`w-full max-w-4xl ${alignCls} flex items-center justify-between mb-1 gap-3 flex-wrap`}>
        <h1 className="text-2xl font-black text-slate-800 ml-16 flex items-center gap-2"><Layers size={22} /> Resumen Totales</h1>
        <div className="flex items-center gap-2 flex-wrap">
          <input value={docName} onChange={e => setDocName(e.target.value)} placeholder="Nombre del resumen…"
            className="px-3 py-2 border border-slate-300 rounded-xl text-sm w-48" />
          <button onClick={nuevoResumen} className="flex items-center gap-2 px-4 py-2.5 bg-white border border-slate-200 text-slate-600 rounded-xl font-bold text-sm hover:bg-slate-50">
            <Plus size={16} /> Nuevo
          </button>
          <button onClick={openList} className="flex items-center gap-2 px-4 py-2.5 bg-white border border-slate-200 text-slate-600 rounded-xl font-bold text-sm hover:bg-slate-50">
            <FolderOpen size={16} /> Mis resúmenes
          </button>
          <button onClick={saveResumen} disabled={busy} className="flex items-center gap-2 px-4 py-2.5 bg-emerald-600 text-white rounded-xl font-bold text-sm hover:bg-emerald-700 disabled:opacity-50">
            {busy ? <Loader size={16} className="animate-spin" /> : <Save size={16} />} Guardar
          </button>
          <button onClick={exportPDF} disabled={exporting}
            className="flex items-center gap-2 px-5 py-2.5 bg-indigo-600 text-white rounded-xl font-bold text-sm hover:bg-indigo-700 disabled:opacity-50">
            <Download size={16} /> {exporting ? 'Generando…' : 'Exportar / Imprimir PDF'}
          </button>
        </div>
      </div>

      {/* Mis resúmenes guardados */}
      {Array.isArray(savedList) && (
        <div className="fixed inset-0 z-[200] bg-black/50 flex items-center justify-center p-4" onClick={() => setSavedList(null)}>
          <div className="bg-white rounded-2xl w-full max-w-lg max-h-[80vh] overflow-hidden flex flex-col" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
              <h3 className="font-black text-slate-800">Mis resúmenes</h3>
              <button onClick={() => setSavedList(null)} className="p-1.5 text-slate-400 hover:text-slate-700"><X size={18} /></button>
            </div>
            <div className="p-4 overflow-y-auto">
              {savedList.length === 0 ? (
                <p className="text-sm text-slate-400 text-center py-8">No tienes resúmenes guardados todavía.</p>
              ) : savedList.map(it => (
                <div key={it.id} className="flex items-center gap-3 border border-slate-200 rounded-xl p-2 mb-2 hover:bg-slate-50">
                  <div className="flex-1 min-w-0">
                    <p className="font-bold text-slate-700 text-sm truncate">{it.name}</p>
                    {it.updatedAt && <p className="text-[10px] text-slate-400">{new Date(it.updatedAt).toLocaleString('es-ES')}</p>}
                  </div>
                  <button onClick={() => loadResumen(it.id)} className="px-3 py-1.5 bg-indigo-600 text-white rounded-lg text-xs font-bold hover:bg-indigo-700">Abrir</button>
                  <button onClick={() => deleteResumen(it.id, it.name)} className="p-1.5 text-red-400 hover:text-red-600 hover:bg-red-50 rounded-lg"><Trash2 size={16} /></button>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
      <div style={dragStyle} className={`w-full max-w-4xl ${alignCls} flex items-center gap-3 mb-5`}>
        <p className="text-sm text-slate-500 flex-1">Junta partidas por cocina, suma totales y forma de pago, y preséntalo con tu logo.</p>
        <div className="flex items-center gap-1 bg-white border border-slate-200 rounded-lg p-1 shrink-0" title="Colocar el contenido a la izquierda, centro o derecha">
          {[['left', AlignLeft, 'Izquierda'], ['center', AlignCenter, 'Centro'], ['right', AlignRight, 'Derecha']].map(([a, Icon, lbl]) => (
            <button key={a} onClick={() => setAlignPersist(a)} title={lbl}
              className={`p-1.5 rounded-md ${align === a ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:bg-slate-100'}`}><Icon size={15} /></button>
          ))}
          <span className="w-px h-5 bg-slate-200 mx-0.5" />
          <button onMouseDown={startDrag} onTouchStart={startDrag} title="Arrastra para mover el contenido a un lado u otro"
            className="p-1.5 rounded-md text-slate-400 hover:bg-slate-100 cursor-grab active:cursor-grabbing"><Move size={15} /></button>
          {(offsetX !== 0 || align !== 'center') && (
            <button onClick={resetPos} title="Volver al centro" className="p-1.5 rounded-md text-slate-400 hover:bg-slate-100"><RotateCcw size={14} /></button>
          )}
        </div>
      </div>

      <div style={dragStyle} className={`bg-white rounded-2xl border border-slate-200 p-6 w-full max-w-4xl ${alignCls} space-y-6`}>
        {/* Cliente + fecha */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="text-xs font-black text-slate-500 uppercase block mb-1">Cliente / Proyecto</label>
            <input value={cliente} onChange={e => setCliente(e.target.value)} placeholder="Cliente / proyecto"
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm font-bold" />
          </div>
          <div>
            <label className="text-xs font-black text-slate-500 uppercase block mb-1">Fecha</label>
            <input value={fecha} onChange={e => setFecha(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm" />
          </div>
        </div>

        {/* Cocinas */}
        {cocinas.map((c, ci) => (
          <div key={c.id} onDragOver={allowDrop} onDrop={onDropRow('cocina', null, c.id)}
            className={`rounded-xl border border-slate-200 overflow-hidden ${dragKey === c.id ? 'opacity-50' : ''}`}>
            <div className="flex items-center gap-2 bg-slate-800 px-3 py-2">
              <span draggable onDragStart={onDragStartRow('cocina', null, c.id)} onDragEnd={() => { dragRef.current = null; setDragKey(null); }}
                className="cursor-grab active:cursor-grabbing text-slate-400 hover:text-white" title="Arrastra para reordenar la cocina"><GripVertical size={16} /></span>
              <div className="flex flex-col -my-1">
                <button onClick={() => moveCocina(c.id, -1)} disabled={ci === 0} title="Subir cocina"
                  className="text-slate-400 hover:text-white disabled:opacity-30 disabled:hover:text-slate-400"><ChevronUp size={13} /></button>
                <button onClick={() => moveCocina(c.id, 1)} disabled={ci === cocinas.length - 1} title="Bajar cocina"
                  className="text-slate-400 hover:text-white disabled:opacity-30 disabled:hover:text-slate-400"><ChevronDown size={13} /></button>
              </div>
              <input value={c.nombre} onChange={e => setCocinaNombre(c.id, e.target.value)}
                className="flex-1 bg-transparent text-white font-black uppercase text-sm outline-none placeholder-slate-400" placeholder="NOMBRE COCINA" />
              <button onClick={() => removeCocina(c.id)} className="text-slate-300 hover:text-red-400" title="Quitar cocina"><Trash2 size={15} /></button>
            </div>
            <div className="p-3 space-y-2">
              {c.lineas.map((l, i) => (
                <div key={l.id} onDragOver={allowDrop} onDrop={onDropRow('linea', c.id, l.id)}
                  className={`flex items-center gap-2 rounded-lg ${dragKey === l.id ? 'opacity-50' : ''}`}>
                  <span draggable onDragStart={onDragStartRow('linea', c.id, l.id)} onDragEnd={() => { dragRef.current = null; setDragKey(null); }}
                    className="cursor-grab active:cursor-grabbing text-slate-300 hover:text-indigo-600" title="Arrastra para reordenar la partida"><GripVertical size={15} /></span>
                  <div className="flex flex-col -my-1">
                    <button onClick={() => moveLinea(c.id, l.id, -1)} disabled={i === 0} title="Subir partida"
                      className="text-slate-300 hover:text-indigo-600 disabled:opacity-30 disabled:hover:text-slate-300"><ChevronUp size={14} /></button>
                    <button onClick={() => moveLinea(c.id, l.id, 1)} disabled={i === c.lineas.length - 1} title="Bajar partida"
                      className="text-slate-300 hover:text-indigo-600 disabled:opacity-30 disabled:hover:text-slate-300"><ChevronDown size={14} /></button>
                  </div>
                  <input value={l.concepto} onChange={e => setLinea(c.id, l.id, 'concepto', e.target.value)} placeholder="Concepto (ej. MUEBLES)"
                    className="flex-1 px-3 py-1.5 border border-slate-200 rounded-lg text-sm" />
                  <input type="number" value={l.importe} onChange={e => setLinea(c.id, l.id, 'importe', e.target.value)} placeholder="0,00"
                    className="w-32 px-3 py-1.5 border border-slate-200 rounded-lg text-sm text-right" />
                  <button onClick={() => removeLinea(c.id, l.id)} className="p-1.5 text-slate-300 hover:text-red-500" title="Quitar partida"><Trash2 size={14} /></button>
                </div>
              ))}
              <div className="flex items-center justify-between pt-1">
                <button onClick={() => addLinea(c.id)} className="flex items-center gap-1 text-xs font-bold text-indigo-600 hover:text-indigo-800"><Plus size={14} /> Añadir partida</button>
                <div className="text-sm font-black text-slate-800">TOTAL: <span className="text-indigo-700">{eur(cocinaTotal(c))}</span></div>
              </div>
            </div>
          </div>
        ))}
        <button onClick={addCocina} className="flex items-center gap-2 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg font-bold text-sm"><Plus size={16} /> Añadir cocina</button>

        {/* Impuestos */}
        <div className="rounded-xl border border-slate-200 p-3 flex flex-wrap items-center gap-x-4 gap-y-2">
          <label className="flex items-center gap-2 text-sm font-bold text-slate-600 cursor-pointer">
            <input type="checkbox" checked={ivaIncluido} onChange={e => setIvaIncluido(e.target.checked)} className="w-4 h-4 accent-orange-600" />
            Los importes ya incluyen IVA
          </label>
          <div className="flex items-center gap-1 text-sm text-slate-600">
            <span className="font-bold">Tipo IVA</span>
            <input type="number" value={ivaRate} onChange={e => setIvaRate(e.target.value)} className="w-16 px-2 py-1 border border-slate-200 rounded-lg text-right" />
            <span className="text-slate-400">%</span>
          </div>
          <div className="ml-auto text-right text-sm text-slate-500">
            <span>Base imponible: <b className="text-slate-700">{eur(baseImponible)}</b></span>
            <span className="mx-2">·</span>
            <span>IVA ({ivaRate}%): <b className="text-slate-700">{eur(cuotaIva)}</b></span>
          </div>
        </div>

        {/* Total general */}
        <div className="rounded-xl bg-gradient-to-r from-orange-500 to-orange-600 text-white px-5 py-4 flex items-center justify-between">
          <div>
            <span className="font-black uppercase tracking-wide">Total general</span>
            <span className="block text-xs font-bold text-orange-100 normal-case">IVA ({ivaRate}%) incluido</span>
          </div>
          <span className="text-2xl font-black">{eur(totalConIva)}</span>
        </div>

        {/* Render 3D adjunto desde Estudio 3D */}
        {render3d?.image && (
          <div className="rounded-xl border border-orange-200 bg-orange-50/50 p-3">
            <div className="flex items-center justify-between mb-2">
              <p className="text-xs font-black text-orange-600 uppercase">Render 3D adjunto (se incluye en el PDF)</p>
              <button onClick={quitarRender3d} className="text-slate-400 hover:text-red-500" title="Quitar render"><Trash2 size={15} /></button>
            </div>
            <img src={render3d.image} alt="Render 3D" className="max-h-48 rounded-lg border border-orange-200" />
            {render3d.cliente && <p className="text-[11px] text-slate-500 mt-1">{render3d.cliente}{render3d.ref ? ` · ${render3d.ref}` : ''}</p>}
          </div>
        )}

        {/* Forma de pago */}
        <div className="rounded-xl border border-slate-200 p-3">
          <p className="text-xs font-black text-slate-500 uppercase mb-2">Forma de pago</p>
          <div className="space-y-2">
            {pagos.map((p, pi) => (
              <div key={p.id} onDragOver={allowDrop} onDrop={onDropRow('pago', null, p.id)}
                className={`flex items-center gap-2 rounded-lg ${dragKey === p.id ? 'opacity-50' : ''}`}>
                <span draggable onDragStart={onDragStartRow('pago', null, p.id)} onDragEnd={() => { dragRef.current = null; setDragKey(null); }}
                  className="cursor-grab active:cursor-grabbing text-slate-300 hover:text-indigo-600" title="Arrastra para reordenar el plazo"><GripVertical size={15} /></span>
                <div className="flex flex-col -my-1">
                  <button onClick={() => movePago(p.id, -1)} disabled={pi === 0} title="Subir plazo"
                    className="text-slate-300 hover:text-indigo-600 disabled:opacity-30 disabled:hover:text-slate-300"><ChevronUp size={14} /></button>
                  <button onClick={() => movePago(p.id, 1)} disabled={pi === pagos.length - 1} title="Bajar plazo"
                    className="text-slate-300 hover:text-indigo-600 disabled:opacity-30 disabled:hover:text-slate-300"><ChevronDown size={14} /></button>
                </div>
                <input value={p.label} onChange={e => setPago(p.id, 'label', e.target.value)} placeholder="Ej: 50% al hacer pedido"
                  className="flex-1 px-3 py-1.5 border border-slate-200 rounded-lg text-sm" />
                <div className="flex items-center gap-1">
                  <input type="number" value={p.percent} onChange={e => setPago(p.id, 'percent', e.target.value)}
                    className="w-16 px-2 py-1.5 border border-slate-200 rounded-lg text-sm text-right" />
                  <span className="text-xs text-slate-400">%</span>
                </div>
                <span className="w-32 text-right text-sm font-bold text-slate-700">{eur(totalConIva * (Number(p.percent) || 0) / 100)}</span>
                <button onClick={() => removePago(p.id)} className="p-1.5 text-slate-300 hover:text-red-500"><Trash2 size={14} /></button>
              </div>
            ))}
            <button onClick={addPago} className="flex items-center gap-1 text-xs font-bold text-indigo-600 hover:text-indigo-800"><Plus size={14} /> Añadir plazo</button>
          </div>
        </div>

        {/* Cuenta bancaria para el pago */}
        <div className="rounded-xl border border-slate-200 p-3">
          <p className="text-xs font-black text-slate-500 uppercase mb-2">Forma de pago: Transferencia a:</p>
          <div className="flex flex-wrap items-center gap-2">
            <select value={bancoId} onChange={e => setBancoId(e.target.value)}
              className="px-3 py-2 border border-slate-300 rounded-lg text-sm font-bold bg-white">
              <option value="">— Sin cuenta —</option>
              {BANCOS.map(b => <option key={b.id} value={b.id}>{b.nombre}</option>)}
            </select>
            {(() => { const b = BANCOS.find(x => x.id === bancoId); return b ? (
              <span className="text-xs text-slate-500">{b.titular} · <span className="font-bold text-slate-700">{b.iban}</span></span>
            ) : <span className="text-[11px] text-slate-400">Elige la cuenta que se mostrará en el presupuesto.</span>; })()}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResumenCocinas;
