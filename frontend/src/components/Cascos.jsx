import React, { useState, useMemo } from 'react';
import { Box, Search, Plus, Trash2, Download, FolderOpen, Save, X, Loader, ClipboardList, List, LayoutGrid } from 'lucide-react';
import { CASCOS, CASCOS_GAMAS } from '../data/cascos';
import { getToken } from '../services/api';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const eur = (n) => `${(Number(n) || 0).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} €`;
const auth = () => ({ 'Authorization': `Bearer ${getToken()}` });

// Dibujo esquemático (SVG) reconocible según el tipo de casco.
function CascoDibujo({ dibujo, tipo, alto, ancho, fondo, unidad = 'mm' }) {
  const W = 120, H = 150, pad = 10;
  const f = unidad === 'cm' ? 10 : 1;
  const dim = (mm) => { const v = mm / f; return Number.isInteger(v) ? v : Math.round(v * 10) / 10; };
  const ratio = Math.min(2.2, Math.max(0.4, (alto || 700) / (ancho || 600)));
  const bw = W - pad * 2;
  const bh = Math.min(H - pad * 2, bw * ratio);
  const x = pad, y = (H - bh) / 2;
  const cx = x + bw / 2, cy = y + bh / 2;
  const t = (tipo || '').toLowerCase();
  const STROKE = '#475569', THIN = '#94a3b8';
  const detail = [];

  const shelvesAt = (n) => { for (let s = 1; s <= n; s++) detail.push(<line key={'s' + s} x1={x + 4} y1={y + (bh * s) / (n + 1)} x2={x + bw - 4} y2={y + (bh * s) / (n + 1)} stroke={THIN} strokeWidth="1.5" />); };

  if (t.includes('fregadero')) {
    // seno de fregadero + grifo
    detail.push(<rect key="b" x={x + bw * 0.18} y={cy - bh * 0.12} width={bw * 0.64} height={bh * 0.3} rx="3" fill="#e0e7ff" stroke={STROKE} strokeWidth="1.6" />);
    detail.push(<circle key="d" cx={cx} cy={cy + bh * 0.03} r="3" fill="none" stroke={STROKE} strokeWidth="1.4" />);
    detail.push(<path key="g" d={`M ${cx + bw * 0.22} ${cy - bh * 0.12} v -8 q 0 -5 -6 -5`} fill="none" stroke={STROKE} strokeWidth="1.6" />);
  } else if (t.includes('placa')) {
    // encimera con 4 fuegos
    [[-0.18, -0.06], [0.18, -0.06], [-0.18, 0.14], [0.18, 0.14]].forEach((p, i) =>
      detail.push(<circle key={'f' + i} cx={cx + bw * p[0]} cy={cy + bh * p[1]} r="5" fill="none" stroke={STROKE} strokeWidth="1.5" />));
  } else if (t.includes('horno')) {
    // horno: tirador + visor
    detail.push(<line key="h" x1={x + 6} y1={y + bh * 0.26} x2={x + bw - 6} y2={y + bh * 0.26} stroke={STROKE} strokeWidth="2" />);
    detail.push(<rect key="v" x={x + bw * 0.22} y={y + bh * 0.4} width={bw * 0.56} height={bh * 0.4} rx="2" fill="#e0e7ff" stroke={STROKE} strokeWidth="1.4" />);
  } else if (t.includes('bombona')) {
    // puerta con rejilla de ventilación
    [0.62, 0.7, 0.78].forEach((p, i) => detail.push(<line key={'r' + i} x1={x + bw * 0.3} y1={y + bh * p} x2={x + bw * 0.7} y2={y + bh * p} stroke={THIN} strokeWidth="1.6" />));
  } else if (t.includes('escurre')) {
    // escurreplatos: rejilla vertical
    for (let i = 1; i <= 5; i++) detail.push(<line key={'e' + i} x1={x + (bw * i) / 6} y1={y + 5} x2={x + (bw * i) / 6} y2={y + bh * 0.55} stroke={THIN} strokeWidth="1.4" />);
    shelvesAt(1);
  } else if (t.includes('campana')) {
    // campana extraíble: trapecio
    detail.push(<path key="c" d={`M ${x} ${y + bh} L ${x + bw * 0.25} ${y} L ${x + bw * 0.75} ${y} L ${x + bw} ${y + bh} Z`} fill="#eef2ff" stroke={STROKE} strokeWidth="1.6" />);
  } else if (dibujo === 'angular' || t.includes('rincón') || t.includes('rincon') || t.includes('angular')) {
    // módulo en esquina
    detail.push(<path key="a" d={`M ${x} ${y} L ${x + bw * 0.55} ${y} L ${x + bw} ${y + bh * 0.45} L ${x + bw} ${y + bh} L ${x} ${y + bh} Z`} fill="#f1f5f9" stroke={STROKE} strokeWidth="1.6" />);
  } else if (dibujo === 'columna' || t.includes('columna') || t.includes('despensa')) {
    shelvesAt(alto >= 2000 ? 5 : 4);
  } else if (t.includes('cubretermo') || t.includes('termo')) {
    detail.push(<rect key="tm" x={x + bw * 0.3} y={cy - bh * 0.1} width={bw * 0.4} height={bh * 0.22} rx="2" fill="#e0e7ff" stroke={STROKE} strokeWidth="1.4" />);
  } else {
    // alto / bajo / transversal / sobre: baldas
    shelvesAt(alto >= 1300 ? 3 : alto >= 850 ? 2 : 1);
  }

  const showAngular = dibujo === 'angular' && !(t.includes('rincón') || t.includes('rincon') || t.includes('angular'));
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-full">
      <rect x={x} y={y} width={bw} height={bh} rx="2" fill="#f8fafc" stroke={STROKE} strokeWidth="2" />
      {detail}
      {showAngular && <line x1={x} y1={y} x2={x + bw / 2} y2={y + bh / 3} stroke={STROKE} strokeWidth="1.5" />}
      <text x={cx} y={y - 3} textAnchor="middle" fontSize="9" fill="#334155">{dim(ancho)} {unidad}</text>
      <text x={x - 3} y={cy} textAnchor="middle" fontSize="9" fill="#334155" transform={`rotate(-90 ${x - 3} ${cy})`}>{dim(alto)} {unidad}</text>
    </svg>
  );
}

const Cascos = ({ state }) => {
  const currentUser = state?.currentUser;
  const [gama, setGama] = useState('kit');
  const [tipo, setTipo] = useState('');
  const [grosor, setGrosor] = useState('16');
  const [color, setColor] = useState('blanco');
  const [altoMin, setAltoMin] = useState('');
  const [altoMax, setAltoMax] = useState('');
  const [anchoMin, setAnchoMin] = useState('');
  const [anchoMax, setAnchoMax] = useState('');
  // Por defecto: iconos en móvil/tablet, lista en ordenador (≥1024px).
  const [vista, setVista] = useState(() => (typeof window !== 'undefined' && window.innerWidth >= 1024) ? 'lista' : 'iconos'); // 'lista' | 'iconos'
  // Unidad de medida para mostrar/filtrar (los datos están en mm). Por defecto cm.
  const [unidad, setUnidad] = useState('cm'); // 'cm' | 'mm'
  const uFactor = unidad === 'cm' ? 10 : 1;
  // Convierte mm a la unidad activa para mostrar (cm con hasta 1 decimal si no es entero).
  const med = (mm) => { const v = mm / uFactor; return Number.isInteger(v) ? v : Math.round(v * 10) / 10; };
  // Cambia de unidad convirtiendo los valores de los filtros para conservar su significado.
  const toggleUnidad = () => {
    const next = unidad === 'cm' ? 'mm' : 'cm';
    const conv = (s) => { const n = Number(s); if (!s || isNaN(n)) return s; return String(next === 'mm' ? n * 10 : n / 10); };
    setAltoMin(conv); setAltoMax(conv); setAnchoMin(conv); setAnchoMax(conv);
    setUnidad(next);
  };
  const [cart, setCart] = useState([]);
  const [cliente, setCliente] = useState('');
  const [ref, setRef] = useState('');
  const [ivaRate, setIvaRate] = useState(21);
  // Descuento por defecto: el asignado al usuario para Des-Montada (el master puede cambiarlo libremente).
  const isAdmin = currentUser?.isAdmin === true;
  const userDtoDesmontada = Number(currentUser?.discountDesmontada ?? currentUser?.commercialDiscount ?? 0) || 0;
  const [descuento, setDescuento] = useState(userDtoDesmontada);
  // Valor de punto (coeficiente) configurable en Master (Cocina Des-Montada); multiplica el precio de tarifa.
  const coef = Number(state?.pointValueDesmontada ?? state?.settings?.cascosPointValue) || 1;
  const pc = (base) => (base == null ? null : Math.round(base * coef * 100) / 100);
  const [saving, setSaving] = useState(false);
  const [orders, setOrders] = useState(null); // null oculto

  const gamaObj = CASCOS_GAMAS.find(g => g.id === gama) || CASCOS_GAMAS[0];
  const grosores = gamaObj.grosores;
  // Si el grosor activo no pertenece a la gama, usar el primero de la gama
  const grosorActivo = grosores.map(String).includes(String(grosor)) ? grosor : String(grosores[0]);
  const colores = (gamaObj.colores[grosorActivo] || gamaObj.colores[Number(grosorActivo)] || []);
  // Si cambia la gama/grosor y el color no aplica, ajustar
  const colorOk = colores.some(c => c.id === color);
  const colorActivo = colorOk ? color : (colores[0]?.id || '');

  // Tipos disponibles según la gama/grosor seleccionados (catálogo dinámico)
  const tiposGama = useMemo(() => {
    const set = new Set(CASCOS.filter(m => (m.gama || 'kit') === gama && String(m.grosor) === String(grosorActivo)).map(m => m.tipo));
    return [...set].sort((a, b) => a.localeCompare(b));
  }, [gama, grosorActivo]);

  const resultados = useMemo(() => {
    return CASCOS.filter(m => (m.gama || 'kit') === gama)
      .filter(m => String(m.grosor) === String(grosorActivo))
      .filter(m => !tipo || m.tipo === tipo)
      .filter(m => (m.precios[colorActivo] != null)) // disponible en ese color
      .filter(m => !altoMin || m.alto >= Number(altoMin) * uFactor)
      .filter(m => !altoMax || m.alto <= Number(altoMax) * uFactor)
      .filter(m => !anchoMin || m.ancho >= Number(anchoMin) * uFactor)
      .filter(m => !anchoMax || m.ancho <= Number(anchoMax) * uFactor)
      .sort((a, b) => a.tipo.localeCompare(b.tipo) || a.alto - b.alto || a.ancho - b.ancho);
  }, [gama, tipo, grosorActivo, colorActivo, altoMin, altoMax, anchoMin, anchoMax, uFactor]);

  const colorLabel = (cid) => {
    for (const g of CASCOS_GAMAS) for (const gr of Object.keys(g.colores)) {
      const f = g.colores[gr].find(c => c.id === cid);
      if (f) return f.label;
    }
    return cid;
  };
  const gamaLabelOf = (gid) => CASCOS_GAMAS.find(g => g.id === gid)?.label || '';
  // Acabado legible para diferenciar líneas mezcladas en el pedido.
  const acabadoOf = (l) => {
    const g = l.gama || 'kit';
    return g === 'kit' ? `${l.colorLabel} · ${l.grosor}mm` : `${gamaLabelOf(g)} · ${l.grosor}mm`;
  };
  // Muestra de color para el punto identificativo de cada acabado.
  const SWATCH = { blanco: '#f1f5f9', aluminio: '#cbd5e1', grafito: '#374151', blancoHidrofugo: '#eef2ff', robleAurora: '#c8a063', spike: '#9ca3af', stone: '#a8a29e', roble: '#b07c4f', olmo: '#a8794e', blancoEsp: '#f8fafc' };

  const addToCart = (m) => {
    const precio = pc(m.precios[colorActivo]);
    const line = {
      key: `${m.id}-${colorActivo}-${Date.now()}`,
      tipo: m.tipo, grosor: m.grosor, dibujo: m.dibujo,
      fondo: m.fondo, alto: m.alto, ancho: m.ancho,
      color: colorActivo, colorLabel: colorLabel(colorActivo), gama: m.gama || 'kit',
      precio, qty: 1,
    };
    setCart(prev => [...prev, line]);
  };
  const setQty = (key, q) => setCart(prev => prev.map(l => l.key === key ? { ...l, qty: Math.max(1, parseInt(q) || 1) } : l));
  const removeLine = (key) => setCart(prev => prev.filter(l => l.key !== key));

  const bruto = cart.reduce((s, l) => s + (l.precio || 0) * l.qty, 0);
  const dto = bruto * ((Number(descuento) || 0) / 100);
  const subtotal = bruto - dto;            // base imponible tras descuento
  const iva = subtotal * (ivaRate / 100);
  const total = subtotal + iva;

  const [savedId, setSavedId] = useState(null);
  const [histKind, setHistKind] = useState('presupuesto');

  const nuevoPedido = () => {
    if (!window.confirm('¿Vaciar el presupuesto actual?')) return;
    setCart([]); setCliente(''); setRef(''); setDescuento(userDtoDesmontada); setSavedId(null);
  };

  // Guarda como presupuesto o pedido (mismo almacén, distinto 'kind').
  const guardar = async (kind) => {
    if (!cart.length) { alert('Añade cascos primero.'); return null; }
    setSaving(true);
    try {
      const r = await fetch(`${API_URL}/api/cascos/orders`, {
        method: 'POST', headers: { ...auth(), 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: savedId || undefined, kind, cliente, ref, ivaRate, descuento,
          lines: cart, total: Math.round(total * 100) / 100,
          userId: currentUser?.id, createdByName: currentUser?.clientName || currentUser?.username,
        }),
      });
      if (!r.ok) throw new Error('Error');
      const d = await r.json();
      if (d.order?.id) setSavedId(d.order.id);
      return d.order;
    } catch { alert('No se pudo guardar.'); return null; }
    finally { setSaving(false); }
  };
  const guardarPresupuesto = async () => { const o = await guardar('presupuesto'); if (o) alert('✅ Presupuesto de cascos guardado.'); };

  // Generar pedido (guardar) + PDF
  const exportarPDF = async () => {
    const { jsPDF } = await import('jspdf');
    const autoTable = (await import('jspdf-autotable')).default;
    const pdf = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
    const W = pdf.internal.pageSize.getWidth(); const M = 14;
    const logo = state?.logo;
    if (logo && typeof logo === 'string' && logo.startsWith('data:')) {
      try { const fmt = logo.includes('png') ? 'PNG' : logo.includes('webp') ? 'WEBP' : 'JPEG'; pdf.addImage(logo, fmt, M, 12, 32, 16); } catch {}
    } else { pdf.setFontSize(15); pdf.setFont(undefined, 'bold'); pdf.text('LUIGGI HOME', M, 22); pdf.setFont(undefined, 'normal'); }
    pdf.setFontSize(16); pdf.setTextColor(30, 27, 65); pdf.setFont(undefined, 'bold');
    pdf.text('PRESUPUESTO COCINA DESMONTADA', W - M, 18, { align: 'right' }); pdf.setFont(undefined, 'normal');
    pdf.setFontSize(10); pdf.setTextColor(120);
    pdf.text(`${cliente || ''}${ref ? '  ·  Ref. ' + ref : ''}`, W - M, 24, { align: 'right' });
    pdf.text(new Date().toLocaleDateString('es-ES'), W - M, 29, { align: 'right' });
    autoTable(pdf, {
      startY: 38,
      head: [['Ud.', 'Módulo', 'Acabado', `Medidas F×Al×An (${unidad})`, 'Precio', 'Importe']],
      body: cart.map(l => [String(l.qty), l.tipo, acabadoOf(l), `${med(l.fondo)}×${med(l.alto)}×${med(l.ancho)}`, eur(l.precio), eur(l.precio * l.qty)]),
      styles: { fontSize: 8.5, cellPadding: 1.8 },
      headStyles: { fillColor: [49, 46, 129], textColor: [255, 255, 255] },
      alternateRowStyles: { fillColor: [245, 245, 250] },
      columnStyles: { 0: { halign: 'center', cellWidth: 12 }, 4: { halign: 'right' }, 5: { halign: 'right' } },
      margin: { left: M, right: M },
    });
    let y = (pdf.lastAutoTable?.finalY || 38) + 8;
    const bx = W - M - 70;
    pdf.setFontSize(10); pdf.setTextColor(40);
    pdf.text('Bruto líneas', bx, y); pdf.text(eur(bruto), W - M, y, { align: 'right' }); y += 6;
    if (Number(descuento) > 0) { pdf.text(`Descuento ${descuento}%`, bx, y); pdf.text('-' + eur(dto), W - M, y, { align: 'right' }); y += 6; }
    pdf.text('Base imponible', bx, y); pdf.text(eur(subtotal), W - M, y, { align: 'right' }); y += 6;
    pdf.text(`IVA ${ivaRate}%`, bx, y); pdf.text(eur(iva), W - M, y, { align: 'right' }); y += 4;
    pdf.setFillColor(234, 120, 40); pdf.roundedRect(bx - 4, y, 74 + 4, 11, 2, 2, 'F');
    pdf.setFontSize(13); pdf.setTextColor(255); pdf.setFont(undefined, 'bold');
    pdf.text('TOTAL', bx, y + 7.5); pdf.text(eur(total), W - M, y + 7.5, { align: 'right' });
    pdf.save(`Cascos_${(cliente || 'presupuesto').replace(/\s+/g, '_')}.pdf`);
  };

  const generarPedido = async () => {
    const o = await guardar('pedido');
    if (o) { alert('✅ Pedido de cascos guardado.'); await exportarPDF(); }
  };

  // Catálogo completo maquetado (Luiggi Home) con precios en PUNTOS, paginado y
  // ordenado según nuestro catálogo: gama → grosor → tipo → medidas.
  const [genCat, setGenCat] = useState(false);
  const generarCatalogo = async () => {
    setGenCat(true);
    try {
      const { jsPDF } = await import('jspdf');
      const autoTable = (await import('jspdf-autotable')).default;
      const pdf = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
      const W = pdf.internal.pageSize.getWidth();
      const Hp = pdf.internal.pageSize.getHeight();
      const M = 14, tableTop = 28;
      const logo = state?.logo;
      const drawHeader = () => {
        if (logo && typeof logo === 'string' && logo.startsWith('data:')) {
          try { const fmt = logo.includes('png') ? 'PNG' : logo.includes('webp') ? 'WEBP' : 'JPEG'; pdf.addImage(logo, fmt, M, 7, 30, 15); } catch {}
        } else { pdf.setFontSize(13); pdf.setFont(undefined, 'bold'); pdf.setTextColor(30, 27, 65); pdf.text('LUIGGI HOME', M, 15); pdf.setFont(undefined, 'normal'); }
        pdf.setFontSize(11); pdf.setTextColor(49, 46, 129); pdf.setFont(undefined, 'bold');
        pdf.text('CATÁLOGO DE CASCOS · COCINA DESMONTADA', W - M, 13, { align: 'right' });
        pdf.setFont(undefined, 'normal'); pdf.setFontSize(8); pdf.setTextColor(150);
        pdf.text(`Precios en PUNTOS · medidas en ${unidad}`, W - M, 18, { align: 'right' });
        pdf.setTextColor(40);
      };
      const ptsFmt = (n) => (n == null ? '—' : Number(n).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 }));
      const medStr = (m) => `${med(m.fondo)}×${med(m.alto)}×${med(m.ancho)}`;
      let y = tableTop;
      for (const g of CASCOS_GAMAS) {
        for (const gr of g.grosores) {
          const colors = g.colores[gr] || g.colores[Number(gr)] || [];
          const mods = CASCOS.filter(m => (m.gama || 'kit') === g.id && String(m.grosor) === String(gr));
          if (!mods.length) continue;
          const tipos = [...new Set(mods.map(m => m.tipo))].sort((a, b) => a.localeCompare(b));
          if (y > Hp - 45) { pdf.addPage(); y = tableTop; }
          pdf.setFillColor(30, 27, 65); pdf.rect(M, y, W - 2 * M, 8, 'F');
          pdf.setTextColor(255); pdf.setFontSize(10); pdf.setFont(undefined, 'bold');
          pdf.text(`${g.label}  ·  ${gr} mm`, M + 2, y + 5.5); pdf.setFont(undefined, 'normal'); pdf.setTextColor(40);
          y += 11;
          for (const tp of tipos) {
            const tmods = mods.filter(m => m.tipo === tp).sort((a, b) => a.alto - b.alto || a.ancho - b.ancho);
            autoTable(pdf, {
              startY: y,
              head: [[`${tp} — Medidas F×Al×An (${unidad})`, ...colors.map(c => c.label)]],
              body: tmods.map(m => [medStr(m), ...colors.map(c => ptsFmt(m.precios[c.id]))]),
              styles: { fontSize: 7.5, cellPadding: 1.4, lineColor: [226, 232, 240], lineWidth: 0.1 },
              headStyles: { fillColor: [234, 120, 40], textColor: [255, 255, 255], fontSize: 7.5 },
              alternateRowStyles: { fillColor: [245, 245, 250] },
              columnStyles: { 0: { cellWidth: 56, fontStyle: 'bold' } },
              margin: { left: M, right: M, top: tableTop },
              didDrawPage: drawHeader,
            });
            y = (pdf.lastAutoTable?.finalY || y) + 5;
            if (y > Hp - 28) { pdf.addPage(); y = tableTop; }
          }
        }
      }
      const n = pdf.getNumberOfPages();
      for (let i = 1; i <= n; i++) {
        pdf.setPage(i); pdf.setFontSize(8); pdf.setTextColor(150);
        pdf.text('Luiggi Home · Cocina Desmontada', M, Hp - 6);
        pdf.text(`Página ${i} de ${n}`, W / 2, Hp - 6, { align: 'center' });
      }
      pdf.save('Catalogo_Cascos_LuiggiHome.pdf');
    } catch (e) { alert('No se pudo generar el catálogo.'); }
    finally { setGenCat(false); }
  };

  const openHistory = async (kind) => {
    setHistKind(kind);
    try {
      const r = await fetch(`${API_URL}/api/cascos/orders?kind=${kind}&userId=${encodeURIComponent(currentUser?.id || '')}`, { headers: auth() });
      const d = await r.json();
      setOrders(d.orders || []);
    } catch { alert('No se pudo cargar el historial.'); }
  };

  const loadOrder = (o) => {
    setCliente(o.cliente || ''); setRef(o.ref || ''); setIvaRate(o.ivaRate ?? 21);
    setDescuento(o.descuento || 0); setCart(o.lines || []); setSavedId(o.id); setOrders(null);
  };
  const deleteOrder = async (id) => {
    if (!window.confirm('¿Eliminar?')) return;
    try { await fetch(`${API_URL}/api/cascos/orders/${id}`, { method: 'DELETE', headers: auth() }); setOrders(prev => (prev || []).filter(x => x.id !== id)); } catch {}
  };

  return (
    <div className="h-full flex flex-col p-4 sm:p-6 pb-32 lg:pb-6 bg-slate-50 overflow-y-auto">
      <div className="rounded-2xl bg-gradient-to-r from-indigo-600 via-violet-600 to-cyan-600 text-white p-5 mb-5 shadow-lg flex items-center justify-between gap-3 flex-wrap">
        <div className="ml-16 sm:ml-16">
          <h1 className="text-xl sm:text-2xl font-black flex items-center gap-2"><Box size={22} /> Cocina Desmontada</h1>
          <p className="text-xs sm:text-sm text-white/80">Presupuestador de cascos: busca por tipo y medidas, monta el presupuesto y genera el pedido.</p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <button onClick={() => openHistory('presupuesto')} className="flex items-center gap-2 px-3 sm:px-4 py-2.5 bg-white/15 hover:bg-white/25 text-white rounded-xl font-bold text-xs sm:text-sm"><FolderOpen size={16} /> Presupuestos</button>
          <button onClick={() => openHistory('pedido')} className="flex items-center gap-2 px-3 sm:px-4 py-2.5 bg-white/15 hover:bg-white/25 text-white rounded-xl font-bold text-xs sm:text-sm"><ClipboardList size={16} /> Pedidos</button>
          <button onClick={generarCatalogo} disabled={genCat} title="Descargar catálogo en puntos (PDF)" className="flex items-center gap-2 px-3 sm:px-4 py-2.5 bg-white/15 hover:bg-white/25 text-white rounded-xl font-bold text-xs sm:text-sm disabled:opacity-50">{genCat ? <Loader size={16} className="animate-spin" /> : <Download size={16} />} Catálogo</button>
          <button onClick={nuevoPedido} className="flex items-center gap-2 px-3 sm:px-4 py-2.5 bg-white text-indigo-700 rounded-xl font-bold text-xs sm:text-sm hover:bg-indigo-50"><Plus size={16} /> Nuevo</button>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-5">
        {/* Buscador + resultados */}
        <div className="lg:col-span-2 space-y-4">
          <div className="bg-white rounded-2xl border border-slate-200 p-4">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-3">
              <div className="col-span-2 sm:col-span-2">
                <label className="text-[10px] font-black text-slate-400 uppercase block mb-1">Gama</label>
                <select value={gama} onChange={e => { setGama(e.target.value); setTipo(''); }} className="w-full px-2 py-2 border border-slate-200 rounded-lg text-sm bg-white">
                  {CASCOS_GAMAS.map(g => <option key={g.id} value={g.id}>{g.label}</option>)}
                </select>
              </div>
              <div>
                <label className="text-[10px] font-black text-slate-400 uppercase block mb-1">Grosor</label>
                <select value={grosorActivo} onChange={e => setGrosor(e.target.value)} disabled={grosores.length <= 1} className="w-full px-2 py-2 border border-slate-200 rounded-lg text-sm bg-white disabled:bg-slate-50 disabled:text-slate-400">
                  {grosores.map(gr => <option key={gr} value={String(gr)}>{gr} mm</option>)}
                </select>
              </div>
              <div>
                <label className="text-[10px] font-black text-slate-400 uppercase block mb-1">Color</label>
                <select value={colorActivo} onChange={e => setColor(e.target.value)} disabled={colores.length <= 1} className="w-full px-2 py-2 border border-slate-200 rounded-lg text-sm bg-white disabled:bg-slate-50 disabled:text-slate-400">
                  {colores.map(c => <option key={c.id} value={c.id}>{c.label}</option>)}
                </select>
              </div>
              <div className="col-span-2 sm:col-span-2">
                <label className="text-[10px] font-black text-slate-400 uppercase block mb-1">Tipo</label>
                <select value={tipo} onChange={e => setTipo(e.target.value)} className="w-full px-2 py-2 border border-slate-200 rounded-lg text-sm bg-white">
                  <option value="">Todos los tipos</option>
                  {tiposGama.map(t => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
              <div>
                <label className="text-[10px] font-black text-slate-400 uppercase block mb-1">Alto ({unidad})</label>
                <div className="flex gap-1">
                  <input value={altoMin} onChange={e => setAltoMin(e.target.value)} placeholder="mín" className="w-full px-2 py-2 border border-slate-200 rounded-lg text-sm" />
                  <input value={altoMax} onChange={e => setAltoMax(e.target.value)} placeholder="máx" className="w-full px-2 py-2 border border-slate-200 rounded-lg text-sm" />
                </div>
              </div>
              <div className="sm:col-span-1">
                <label className="text-[10px] font-black text-slate-400 uppercase block mb-1">Ancho ({unidad})</label>
                <div className="flex gap-1">
                  <input value={anchoMin} onChange={e => setAnchoMin(e.target.value)} placeholder="mín" className="w-full px-2 py-2 border border-slate-200 rounded-lg text-sm" />
                  <input value={anchoMax} onChange={e => setAnchoMax(e.target.value)} placeholder="máx" className="w-full px-2 py-2 border border-slate-200 rounded-lg text-sm" />
                </div>
              </div>
            </div>
            <div className="flex items-center justify-between gap-2 flex-wrap">
              <p className="text-[11px] text-slate-400 flex items-center gap-1"><Search size={12} /> {resultados.length} cascos encontrados</p>
              <div className="flex items-center gap-2 flex-wrap">
              <button type="button" onClick={toggleUnidad} title="Cambiar unidad (cm / mm)"
                className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-black bg-slate-100 text-slate-600 hover:bg-slate-200 transition-colors">
                <span className={unidad === 'cm' ? 'text-indigo-700' : ''}>cm</span><span className="text-slate-300">/</span><span className={unidad === 'mm' ? 'text-indigo-700' : ''}>mm</span>
              </button>
              <div className="flex items-center gap-1 bg-slate-100 rounded-lg p-1">
                <button type="button" onClick={() => setVista('iconos')} title="Vista de iconos"
                  className={`flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-bold transition-colors ${vista === 'iconos' ? 'bg-white text-indigo-700 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}><LayoutGrid size={14} /> Iconos</button>
                <button type="button" onClick={() => setVista('lista')} title="Vista de lista"
                  className={`flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-bold transition-colors ${vista === 'lista' ? 'bg-white text-indigo-700 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}><List size={14} /> Lista</button>
              </div>
              </div>
            </div>
          </div>

          {vista === 'lista' ? (
          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
            <div className="max-h-[55vh] overflow-y-auto divide-y divide-slate-100">
              {resultados.map(m => (
                <button key={m.id} type="button" onClick={() => addToCart(m)}
                  className="w-full text-left flex items-center gap-3 p-3 hover:bg-indigo-50 transition-colors cursor-pointer group">
                  <div className="w-14 h-20 shrink-0 bg-slate-50 rounded border border-slate-100"><CascoDibujo dibujo={m.dibujo} tipo={m.tipo} alto={m.alto} ancho={m.ancho} fondo={m.fondo} unidad={unidad} /></div>
                  <div className="flex-1 min-w-0">
                    <p className="font-bold text-slate-800 text-sm sm:text-base truncate">{m.tipo} <span className="text-slate-400 font-normal text-xs">{m.grosor}mm</span></p>
                    <div className="flex flex-wrap gap-1.5 mt-1.5">
                      {[['Fondo', m.fondo], ['Alto', m.alto], ['Ancho', m.ancho]].map(([lab, val]) => (
                        <span key={lab} className="inline-flex items-baseline gap-1 px-2.5 py-1 bg-slate-100 rounded-lg">
                          <span className="text-[9px] font-black text-slate-400 uppercase tracking-wide">{lab}</span>
                          <span className="text-sm sm:text-base font-black text-slate-700 leading-none">{med(val)}</span>
                        </span>
                      ))}
                      <span className="inline-flex items-center px-1.5 text-[10px] font-bold text-slate-400 uppercase">{unidad}</span>
                    </div>
                  </div>
                  <div className="text-right shrink-0 flex flex-col items-end">
                    <p className="font-black text-indigo-700 text-base sm:text-lg">{eur(pc(m.precios[colorActivo]))}</p>
                    <span className="mt-1.5 inline-flex items-center gap-1 px-3 py-1.5 bg-indigo-600 text-white rounded-lg text-xs font-bold group-hover:bg-indigo-700"><Plus size={13} /> Añadir</span>
                  </div>
                </button>
              ))}
              {resultados.length === 0 && <p className="p-8 text-center text-slate-400 text-sm">No hay cascos con esos filtros.</p>}
            </div>
          </div>
          ) : (
          <div className="bg-white rounded-2xl border border-slate-200 p-3">
            <div className="max-h-[60vh] overflow-y-auto grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
              {resultados.map(m => (
                <button key={m.id} type="button" onClick={() => addToCart(m)}
                  className="relative flex flex-col items-center text-center border border-slate-200 rounded-xl p-2.5 hover:border-indigo-400 hover:bg-indigo-50 hover:shadow-md transition-all cursor-pointer group">
                  <div className="w-full h-24 bg-slate-50 rounded-lg border border-slate-100 mb-2"><CascoDibujo dibujo={m.dibujo} tipo={m.tipo} alto={m.alto} ancho={m.ancho} fondo={m.fondo} unidad={unidad} /></div>
                  <p className="font-bold text-slate-800 text-xs leading-tight line-clamp-2">{m.tipo}</p>
                  <p className="text-[10px] text-slate-400 mt-0.5">{med(m.alto)}×{med(m.ancho)} {unidad} · {m.grosor}mm</p>
                  <p className="font-black text-indigo-700 text-sm mt-1">{eur(pc(m.precios[colorActivo]))}</p>
                  <span className="mt-1.5 inline-flex items-center justify-center gap-1 w-full px-2 py-1 bg-indigo-600 text-white rounded-lg text-[11px] font-bold group-hover:bg-indigo-700"><Plus size={12} /> Añadir</span>
                </button>
              ))}
              {resultados.length === 0 && <p className="col-span-full p-8 text-center text-slate-400 text-sm">No hay cascos con esos filtros.</p>}
            </div>
          </div>
          )}
        </div>

        {/* Presupuesto */}
        <div className="bg-white rounded-2xl border border-slate-200 p-4 h-fit">
          <h3 className="font-black text-slate-800 mb-3 flex items-center gap-2"><ClipboardList size={18} /> Presupuesto</h3>
          <div className="grid grid-cols-1 gap-2 mb-3">
            <input value={cliente} onChange={e => setCliente(e.target.value)} placeholder="Cliente" className="px-3 py-2 border border-slate-200 rounded-lg text-sm" />
            <input value={ref} onChange={e => setRef(e.target.value)} placeholder="Referencia" className="px-3 py-2 border border-slate-200 rounded-lg text-sm" />
          </div>
          <div className="space-y-2 max-h-[40vh] overflow-y-auto mb-3">
            {cart.map(l => (
              <div key={l.key} className="flex items-center gap-2 border border-slate-100 rounded-lg p-2">
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-bold text-slate-700 truncate">{l.tipo}</p>
                  <p className="text-[10px] font-bold text-slate-600 truncate flex items-center gap-1">
                    <span className="inline-block w-2.5 h-2.5 rounded-full border border-slate-300 shrink-0" style={{ background: SWATCH[l.color] || '#e2e8f0' }} />
                    {acabadoOf(l)}
                  </p>
                  <p className="text-[10px] text-slate-400">{med(l.alto)}×{med(l.ancho)} {unidad} · {eur(l.precio)}</p>
                </div>
                <input type="number" value={l.qty} onChange={e => setQty(l.key, e.target.value)} className="w-12 px-1 py-1 border border-slate-200 rounded text-sm text-center" />
                <span className="w-20 text-right text-xs font-bold text-slate-700">{eur(l.precio * l.qty)}</span>
                <button onClick={() => removeLine(l.key)} className="text-slate-300 hover:text-red-500"><Trash2 size={14} /></button>
              </div>
            ))}
            {cart.length === 0 && <p className="text-center text-slate-400 text-xs py-6">Añade cascos desde el buscador.</p>}
          </div>
          <div className="border-t border-slate-100 pt-3 space-y-1 text-sm">
            <div className="flex justify-between text-slate-500"><span>Bruto líneas</span><span className="font-bold">{eur(bruto)}</span></div>
            <div className="flex justify-between text-slate-500 items-center"><span className="flex items-center gap-1">Descuento <input type="number" value={descuento} disabled={!isAdmin} title={isAdmin ? 'Editable (master)' : 'Descuento asignado por el administrador'} onChange={e => setDescuento(Number(e.target.value) || 0)} className="w-12 px-1 py-0.5 border border-slate-200 rounded text-center disabled:bg-slate-100 disabled:text-slate-400" />%</span><span className="font-bold text-rose-500">-{eur(dto)}</span></div>
            <div className="flex justify-between text-slate-500"><span>Base imponible</span><span className="font-bold">{eur(subtotal)}</span></div>
            <div className="flex justify-between text-slate-500 items-center"><span className="flex items-center gap-1">IVA <input type="number" value={ivaRate} onChange={e => setIvaRate(Number(e.target.value) || 0)} className="w-12 px-1 py-0.5 border border-slate-200 rounded text-center" />%</span><span className="font-bold">{eur(iva)}</span></div>
            <div className="flex justify-between text-slate-900 text-lg font-black pt-1 bg-orange-50 -mx-1 px-2 rounded-lg py-1"><span>TOTAL</span><span className="text-orange-600">{eur(total)}</span></div>
          </div>
          <div className="grid grid-cols-1 gap-2 mt-3">
            <button onClick={guardarPresupuesto} disabled={saving || !cart.length} className="flex items-center justify-center gap-2 px-4 py-2.5 bg-cyan-600 text-white rounded-xl font-bold text-sm hover:bg-cyan-700 disabled:opacity-50">{saving ? <Loader size={16} className="animate-spin" /> : <Save size={16} />} Guardar presupuesto</button>
            <div className="grid grid-cols-2 gap-2">
              <button onClick={generarPedido} disabled={saving || !cart.length} className="flex items-center justify-center gap-2 px-3 py-2.5 bg-emerald-600 text-white rounded-xl font-bold text-sm hover:bg-emerald-700 disabled:opacity-50"><ClipboardList size={16} /> Pedido</button>
              <button onClick={exportarPDF} disabled={!cart.length} className="flex items-center justify-center gap-2 px-3 py-2.5 bg-indigo-600 text-white rounded-xl font-bold text-sm hover:bg-indigo-700 disabled:opacity-50"><Download size={16} /> PDF</button>
            </div>
          </div>
        </div>
      </div>

      {/* Historial de pedidos */}
      {Array.isArray(orders) && (
        <div className="fixed inset-0 z-[200] bg-black/50 flex items-center justify-center p-4" onClick={() => setOrders(null)}>
          <div className="bg-white rounded-2xl w-full max-w-lg max-h-[80vh] overflow-hidden flex flex-col" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
              <h3 className="font-black text-slate-800">{histKind === 'pedido' ? 'Pedidos' : 'Presupuestos'} de cascos</h3>
              <button onClick={() => setOrders(null)} className="p-1.5 text-slate-400 hover:text-slate-700"><X size={18} /></button>
            </div>
            <div className="p-4 overflow-y-auto">
              {orders.length === 0 ? <p className="text-sm text-slate-400 text-center py-8">No hay {histKind === 'pedido' ? 'pedidos' : 'presupuestos'} guardados.</p> : orders.map(o => (
                <div key={o.id} className="flex items-center gap-3 border border-slate-200 rounded-xl p-2 mb-2 hover:bg-slate-50">
                  <div className="flex-1 min-w-0">
                    <p className="font-bold text-slate-700 text-sm truncate">{o.cliente || 'Sin cliente'}{o.ref ? ` · ${o.ref}` : ''}</p>
                    <p className="text-[10px] text-slate-400">{o.createdAt ? new Date(o.createdAt).toLocaleString('es-ES') : ''} · {(o.lines || []).length} líneas</p>
                  </div>
                  <span className="text-sm font-black text-slate-800">{eur(o.total)}</span>
                  <button onClick={() => loadOrder(o)} className="px-3 py-1.5 bg-indigo-600 text-white rounded-lg text-xs font-bold hover:bg-indigo-700">Abrir</button>
                  <button onClick={() => deleteOrder(o.id)} className="p-1.5 text-red-400 hover:text-red-600 hover:bg-red-50 rounded-lg"><Trash2 size={15} /></button>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Cascos;
