import React, { useState, useMemo, useRef, useEffect } from 'react';
import { Box, Search, Plus, Trash2, Download, FolderOpen, Save, X, Loader, ClipboardList, List, LayoutGrid, Maximize2, Minimize2, PanelRightClose, PanelLeftOpen, ShoppingCart, Lock, Unlock, FileUp, ChevronDown, Package } from 'lucide-react';
import { CASCOS, CASCOS_GAMAS } from '../data/cascos';
import { getToken } from '../services/api';
import RentabilidadUnificada from './RentabilidadUnificada';
import RelacionReview from './RelacionReview';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const eur = (n) => `${(Number(n) || 0).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} €`;
const auth = () => ({ 'Authorization': `Bearer ${getToken()}` });
// Normaliza para búsqueda sin acentos ni mayúsculas.
const norm = (s) => String(s || '').normalize('NFD').replace(/\p{Diacritic}/gu, '').toLowerCase().trim();

// Secciones por proveedor dentro de Cocina Desmontada. CASCOS ya operativo;
// el resto quedan listos para cargar su tarifa.
const SECCIONES = [
  { id: 'cascos', label: 'CASCOS', desc: 'Módulos / cuerpos de mueble' },
  { id: 'blum', label: 'BLUM', desc: 'Bisagras, cajones y gavetas' },
  { id: 'gtv', label: 'GTV', desc: 'Cajones y gavetas' },
  { id: 'emuca', label: 'EMUCA', desc: 'Bisagras' },
];

// Catálogo de HERRAJE (Blum · GTV · Emuca). Precio = tarifa/PVP SIN descuento
// (el descuento de proveedor se aplica luego). Importado de tarifas/albaranes.
const BLUM_PRODUCTOS = [
  // ── BLUM ──────────────────────────────────────────────────────────────────
  { ref: '25-3DO500B03A', nombre: 'Blum Set Gaveta ANTARO D Gris Orión LN.500mm 30Kg', precio: 127.494, cat: 'Cajones', marca: 'Blum' },
  { ref: '25-3MO500B03A', nombre: 'Blum Set Cajón ANTARO M Gris Orión LN.500mm 30Kg', precio: 90.27, cat: 'Cajones', marca: 'Blum' },
  { ref: '402-FCAB47090', nombre: 'Blum Fondo Cajón/Gaveta ANTARO Gr./Bl. F-50 M-90', precio: 24.37, cat: 'Fondos y traseras', marca: 'Blum' },
  { ref: '402-TCBM47090', nombre: 'Blum Trasera Cajón "M" ANTARO Gr./Bl. F-50 M-90', precio: 10.38, cat: 'Fondos y traseras', marca: 'Blum' },
  { ref: '402-TGBD47090', nombre: 'Blum Trasera Gaveta "D" ANTARO Gr./Bl. F-50 M-90', precio: 22.28, cat: 'Fondos y traseras', marca: 'Blum' },
  { ref: '17-71B3550 NIQ', nombre: 'Blum Bisagra Recta 110º Blumotion Atornillar Níquel', precio: 7.458, cat: 'Bisagras', marca: 'Blum' },
  { ref: '17-71T3550 NIQ', nombre: 'Blum Bisagra Recta 110º Con Muelle Atornillar Níquel', precio: 4.305, cat: 'Bisagras', marca: 'Blum' },
  { ref: '17-70T3580T LN', nombre: 'Blum Bisagra Recta 110º Sin Muelle Taco 8mm Níquel', precio: 4.883, cat: 'Bisagras', marca: 'Blum' },
  { ref: '17-71B758E NIQ', nombre: 'Blum Bisagra Recta 155º Ang.0º Blumotion Taco 8mm EXPANDO Níquel', precio: 19.438, cat: 'Bisagras', marca: 'Blum' },
  { ref: '17-79B9550 NIQ', nombre: 'Blum Bisagra 95º Rincón Ciego Blumotion Atornillar Níquel', precio: 17.177, cat: 'Bisagras', marca: 'Blum' },
  { ref: '17-173H7100 NQ', nombre: 'Blum Base Bisagra Cruz Excéntrica Alt.0mm Atornillar Níquel', precio: 1.323, cat: 'Bases', marca: 'Blum' },
  { ref: '17-173L6130 NQ', nombre: 'Blum Base Bisagra Cruz Altura 3mm Atornillar Níquel', precio: 0.789, cat: 'Bases', marca: 'Blum' },
  // ── GTV (AXIS PRO) ──────────────────────────────────────────────────────────
  { ref: '25-AXP084500G', nombre: 'GTV Set Cajón AXIS PRO 40Kg Fondo 500mm H-84 Gris Antracita', precio: 43.055, cat: 'Cajones', marca: 'GTV' },
  { ref: '25-AXP167500G', nombre: 'GTV Set Gaveta AXIS PRO 40Kg Fondo 500mm H-167 Gris Antracita', precio: 56.65, cat: 'Cajones', marca: 'GTV' },
  { ref: '25-AXP199500G', nombre: 'GTV Set Gaveta AXIS PRO 40Kg Fondo 500mm H-199 Gris Antracita', precio: 65.966, cat: 'Cajones', marca: 'GTV' },
  { ref: '402-FCAV47090', nombre: 'GTV Fondo Cajón/Gaveta AXIS PRO F-50 M-90', precio: 23.95, cat: 'Fondos y traseras', marca: 'GTV' },
  { ref: '402-TCAV47090', nombre: 'GTV Trasera Cajón AXIS PRO F-50 M-90', precio: 11.44, cat: 'Fondos y traseras', marca: 'GTV' },
  { ref: '402-TGDV47090', nombre: 'GTV Trasera Gaveta 199mm AXIS PRO F-50 M-90', precio: 21.38, cat: 'Fondos y traseras', marca: 'GTV' },
  // ── EMUCA ───────────────────────────────────────────────────────────────────
  { ref: '1711116', nombre: 'Emuca Bisagra clip gas recta con regulación + base s/t', precio: 1.01, cat: 'Bisagras', marca: 'Emuca' },
];

// Logotipos de proveedor (wordmarks SVG inline en colores de marca; sin hotlinking
// externo para evitar problemas de CSP / enlaces rotos).
function ProviderLogo({ id, height = 20 }) {
  const box = { display: 'inline-flex', alignItems: 'center' };
  if (id === 'blum') {
    // Caja naranja, "blum" en blanco itálico con flecha ascendente y ®.
    return (
      <svg height={height} viewBox="0 0 200 84" style={box} aria-label="blum">
        <rect x="0" y="0" width="200" height="84" rx="8" fill="#ee7203" />
        <path d="M30 60 L30 24 M30 24 L22 33 M30 24 L38 33" fill="none" stroke="#ffffff" strokeWidth="7" strokeLinecap="round" strokeLinejoin="round" />
        <text x="34" y="62" fontFamily="Arial, Helvetica, sans-serif" fontSize="52" fontStyle="italic" fontWeight="900" fill="#ffffff" letterSpacing="-1">blum</text>
        <text x="182" y="30" fontFamily="Arial, sans-serif" fontSize="11" fill="#ffffff">®</text>
      </svg>
    );
  }
  if (id === 'gtv') {
    // "GTV" en azul corporativo.
    return (
      <svg height={height} viewBox="0 0 200 84" style={box} aria-label="GTV">
        <rect x="0" y="0" width="200" height="84" rx="8" fill="#ffffff" />
        <text x="100" y="60" textAnchor="middle" fontFamily="Arial, Helvetica, sans-serif" fontSize="56" fontWeight="900" fill="#2e3192" letterSpacing="1">GTV</text>
      </svg>
    );
  }
  if (id === 'emuca') {
    // "emuca" en gris con swoosh amarillo y claim.
    return (
      <svg height={height} viewBox="0 0 240 84" style={box} aria-label="emuca">
        <rect x="0" y="0" width="240" height="84" rx="8" fill="#ffffff" />
        <text x="12" y="52" fontFamily="Arial, Helvetica, sans-serif" fontSize="46" fontWeight="800" fill="#4d4d4f" letterSpacing="-1">emuca</text>
        <path d="M205 40 q10 -18 24 -14 q-6 10 -18 22 q-8 4 -6 -8 Z" fill="#fdc300" />
        <circle cx="223" cy="20" r="3.5" fill="#ffffff" />
        <text x="12" y="72" fontFamily="Arial, Helvetica, sans-serif" fontSize="15" fill="#fdc300" letterSpacing="1">where creation begins</text>
      </svg>
    );
  }
  return null;
}

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

const Cascos = ({ state, setState }) => {
  const currentUser = state?.currentUser;
  const esMasterCascos = !!(currentUser?.isAdmin || currentUser?.isPrimaryAdmin || currentUser?.isGerente);
  const [showRenta, setShowRenta] = useState(false); // módulo unificado de rentabilidad (Alvic/MV, solo master)
  const [presupuestoBloqueado, setPresupuestoBloqueado] = useState(false); // bloquear edición del presupuesto
  const [importandoRel, setImportandoRel] = useState(false); // importar relación de muebles (PDF nomenclaturas)
  const [relacionRevisar, setRelacionRevisar] = useState(null); // muebles detectados pendientes de revisar
  const [descargandoPdf, setDescargandoPdf] = useState(false);
  const [menuImportar, setMenuImportar] = useState(false);   // menú de vías de importación
  const [sistemaRenta, setSistemaRenta] = useState(null);    // 'alvic' | 'mv' al abrir desde el menú
  const relacionInputRef = useRef(null);

  // Descarga el PDF de nomenclaturas rellenable (56 familias) desde el backend.
  const descargarNomenclaturas = async () => {
    setDescargandoPdf(true);
    try {
      const r = await fetch(`${API_URL}/api/cascos/mv/nomenclaturas-pdf`, { headers: auth() });
      if (!r.ok) { alert('No se pudo descargar el PDF de nomenclaturas.'); return; }
      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; a.download = 'Nomenclaturas_MV_rellenable.pdf';
      document.body.appendChild(a); a.click(); a.remove();
      URL.revokeObjectURL(url);
    } catch (e) {
      alert(`No se pudo descargar (${e?.message || 'error de red'}).`);
    } finally { setDescargandoPdf(false); }
  };

  // Importa una RELACIÓN de muebles MV escrita en el PDF de nomenclaturas rellenable
  // (o cualquier PDF con esa notación) y la vuelca al presupuesto SIN necesidad de
  // dibujo. El backend empareja cada código con la tarifa MV; el useEffect de
  // `cascosPendingCabinets` casa cada mueble con el catálogo por tipo+ancho y lo precia.
  const importarRelacion = async (file) => {
    if (!file) return;
    setImportandoRel(true);
    try {
      const b64 = await new Promise((res, rej) => {
        const fr = new FileReader(); fr.onload = () => res(fr.result); fr.onerror = rej; fr.readAsDataURL(file);
      });
      const r = await fetch(`${API_URL}/api/cascos/mv/detectar-relacion`, {
        method: 'POST', headers: { ...auth(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ pdfBase64: b64 }),
      });
      let d = {}; try { d = await r.json(); } catch { d = {}; }
      if (!r.ok || !d.success) { alert(d.detail || 'No se pudo leer la relación del PDF.'); return; }
      if (!(d.muebles || []).length) { alert('No se detectaron muebles en la relación.'); return; }
      // Abrir panel de REVISIÓN (editar cantidades, borrar, buscar y añadir más).
      setRelacionRevisar(d.muebles);
    } catch (e) {
      alert(`No se pudo conectar para leer la relación (${e?.message || 'error de red'}).`);
    } finally {
      setImportandoRel(false);
      if (relacionInputRef.current) relacionInputRef.current.value = '';
    }
  };
  const [seccion, setSeccion] = useState('cascos'); // proveedor activo: cascos | blum | gtv | emuca
  const [gama, setGama] = useState('kit');
  const [q, setQ] = useState(''); // búsqueda por palabras (fregadero, campana, altillo…)
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
  const [qBlum, setQBlum] = useState(''); // búsqueda en el catálogo BLUM
  const [cart, setCart] = useState([]);
  // Consume el herraje estimado que llega desde el diseñador 3D (líneas de plano).
  useEffect(() => {
    const pend = state?.cascosPendingLines;
    if (pend && pend.length) {
      // Fusiona por sig (como addToCart) para que un segundo volcado sume
      // cantidades en lugar de crear líneas de herraje duplicadas.
      setCart(prev => {
        const next = [...prev];
        for (const l of pend) {
          const i = next.findIndex(x => x.sig === l.sig);
          if (i >= 0) next[i] = { ...next[i], qty: (next[i].qty || 1) + (l.qty || 1) };
          else next.push(l);
        }
        return next;
      });
      if (setState) setState(p => ({ ...p, cascosPendingLines: null }));
    }
  }, [state?.cascosPendingLines, setState]);
  const [cliente, setCliente] = useState('');
  const [ref, setRef] = useState('');
  const [ivaRate, setIvaRate] = useState(21);
  // Descuento por defecto: el asignado al usuario para Des-Montada (el master puede cambiarlo libremente).
  const isAdmin = currentUser?.isAdmin === true;
  const userDtoDesmontada = Number(currentUser?.discountDesmontada ?? currentUser?.commercialDiscount ?? 0) || 0;
  const [descuento, setDescuento] = useState(userDtoDesmontada);
  const [descProveedor, setDescProveedor] = useState(0); // descuento comercial del proveedor
  // Centros de envío configurados en Ajustes (uno por línea: "Nombre — Dirección").
  const centros = String(state?.settings?.centrosEnvio || '').split('\n').map(l => l.trim()).filter(Boolean);
  const [centroEnvio, setCentroEnvio] = useState('');
  // Valor de punto (coeficiente) configurable en Master (Cocina Des-Montada); multiplica el precio de tarifa.
  const coef = Number(state?.pointValueDesmontada ?? state?.settings?.cascosPointValue) || 1;
  const pc = (base) => (base == null ? null : Math.round(base * coef * 100) / 100);
  const [saving, setSaving] = useState(false);
  const [orders, setOrders] = useState(null); // null oculto
  // Panel de presupuesto: redimensionable (arrastrar) y ocultable, como en Cocina Montada.
  const [panelExpanded, setPanelExpanded] = useState(false); // ver presupuesto en grande (oculta buscador)
  const [panelCollapsed, setPanelCollapsed] = useState(false); // ocultar presupuesto
  const [panelWidth, setPanelWidth] = useState(384);
  const isResizing = useRef(false);
  useEffect(() => {
    const onMove = (e) => { if (isResizing.current) setPanelWidth(Math.max(300, Math.min(680, window.innerWidth - e.clientX - 24))); };
    const onUp = () => { isResizing.current = false; };
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
    return () => { window.removeEventListener('mousemove', onMove); window.removeEventListener('mouseup', onUp); };
  }, []);
  const isWide = () => typeof window !== 'undefined' && window.innerWidth >= 1024;

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
      .filter(m => !q || norm(m.tipo).includes(norm(q))) // búsqueda por palabras
      .filter(m => (m.precios[colorActivo] != null)) // disponible en ese color
      .filter(m => !altoMin || m.alto >= Number(altoMin) * uFactor)
      .filter(m => !altoMax || m.alto <= Number(altoMax) * uFactor)
      .filter(m => !anchoMin || m.ancho >= Number(anchoMin) * uFactor)
      .filter(m => !anchoMax || m.ancho <= Number(anchoMax) * uFactor)
      .sort((a, b) => a.tipo.localeCompare(b.tipo) || a.alto - b.alto || a.ancho - b.ancho);
  }, [gama, tipo, q, grosorActivo, colorActivo, altoMin, altoMax, anchoMin, anchoMax, uFactor]);

  const colorLabel = (cid) => {
    for (const g of CASCOS_GAMAS) for (const gr of Object.keys(g.colores)) {
      const f = g.colores[gr].find(c => c.id === cid);
      if (f) return f.label;
    }
    return cid;
  };
  const gamaLabelOf = (gid) => CASCOS_GAMAS.find(g => g.id === gid)?.label || '';

  // Volcado de MUEBLES desde el Diseñador 3D: empareja cada mueble detectado con
  // el catálogo CASCOS (misma familia bajo/alto/columna + ancho más cercano) y lo
  // precia con el color/grosor/gama activos. Si no hay match, entra estimado a 0€.
  useEffect(() => {
    const cabs = state?.cascosPendingCabinets;
    if (!cabs || !cabs.length) return;
    const famOf = (t) => {
      const s = norm(t);
      if (/alto|altillo|sobre\s*encimera|sobre\s*columna|cubretermo|escurre|campana|vitrina/.test(s)) return 'alto';
      if (/columna|semicolumna/.test(s)) return 'columna';
      return 'bajo';
    };
    const pool = CASCOS.filter(m => (m.gama || 'kit') === gama && String(m.grosor) === String(grosorActivo) && m.precios[colorActivo] != null);
    const lines = cabs.map((det, idx) => {
      const fam = famOf(det.tipo);
      let cand = pool.filter(m => famOf(m.tipo) === fam);
      if (!cand.length) cand = pool;
      const target = Number(det.ancho) || 0;
      let best = null, bd = Infinity;
      for (const m of cand) { const d = Math.abs((Number(m.ancho) || 0) - target); if (d < bd) { bd = d; best = m; } }
      if (best) {
        const base = best.precios[colorActivo];
        return { key: `vk-${Date.now()}-${idx}`, sig: `${best.id}|${colorActivo}`, tipo: best.tipo, grosor: best.grosor, dibujo: best.dibujo, fondo: best.fondo, alto: best.alto, ancho: best.ancho, color: colorActivo, colorLabel: colorLabel(colorActivo), gama: best.gama || 'kit', precio: pc(base), precioBase: base, qty: det.qty || 1 };
      }
      return { key: `vk-${Date.now()}-${idx}`, sig: `estimado|${norm(det.tipo)}|${det.ancho}`, tipo: det.tipo, grosor: grosorActivo, dibujo: null, fondo: det.fondo || 0, alto: det.alto || 0, ancho: det.ancho || 0, color: colorActivo, colorLabel: colorLabel(colorActivo), gama, precio: 0, precioBase: 0, qty: det.qty || 1, estimado: true };
    });
    setCart(prev => {
      const next = [...prev];
      for (const l of lines) {
        const i = next.findIndex(x => x.sig === l.sig);
        if (i >= 0) next[i] = { ...next[i], qty: (next[i].qty || 1) + (l.qty || 1) };
        else next.push(l);
      }
      return next;
    });
    if (setState) setState(p => ({ ...p, cascosPendingCabinets: null }));
  }, [state?.cascosPendingCabinets, gama, grosorActivo, colorActivo, setState]);
  // Acabado legible para diferenciar líneas mezcladas en el pedido.
  const acabadoOf = (l) => {
    if (l.accesorio) return l.ref || 'BLUM';
    const g = l.gama || 'kit';
    return g === 'kit' ? `${l.colorLabel} · ${l.grosor}mm` : `${gamaLabelOf(g)} · ${l.grosor}mm`;
  };
  // Cadena de medidas para una línea (accesorios BLUM no tienen dimensiones).
  const dimStr = (l) => l.accesorio ? '—' : `${med(l.alto)}×${med(l.ancho)}×${med(l.fondo)}`;
  // Muestra de color para el punto identificativo de cada acabado.
  const SWATCH = { blanco: '#f1f5f9', aluminio: '#cbd5e1', grafito: '#202023', blancoHidrofugo: '#f6f6f4', robleAurora: '#d9c6a4', spike: '#b58d86', stone: '#c9c2b3', roble: '#b07c4f', olmo: '#a8794e', blancoEsp: '#f8fafc' };

  const addToCart = (m) => {
    const base = m.precios[colorActivo];        // precio de tarifa (puntos)
    const precio = pc(base);
    const sig = `${m.id}|${colorActivo}`;       // mismo módulo + mismo acabado
    setCart(prev => {
      const i = prev.findIndex(l => l.sig === sig);
      if (i >= 0) { const c = [...prev]; c[i] = { ...c[i], qty: (c[i].qty || 1) + 1 }; return c; }
      return [...prev, {
        key: `${sig}-${Date.now()}`, sig,
        tipo: m.tipo, grosor: m.grosor, dibujo: m.dibujo,
        fondo: m.fondo, alto: m.alto, ancho: m.ancho,
        color: colorActivo, colorLabel: colorLabel(colorActivo), gama: m.gama || 'kit',
        precio, precioBase: base, qty: 1,
      }];
    });
  };
  // Resultados del catálogo BLUM filtrados por texto (ref o nombre).
  // Productos del proveedor de la sección activa (Blum / GTV / Emuca), no mezclados.
  const resultadosBlum = useMemo(() => {
    const t = norm(qBlum);
    const marcaSec = seccion === 'gtv' ? 'GTV' : seccion === 'emuca' ? 'Emuca' : 'Blum';
    return BLUM_PRODUCTOS.filter(p => (p.marca || 'Blum') === marcaSec && (!t || norm(p.ref).includes(t) || norm(p.nombre).includes(t)));
  }, [qBlum, seccion]);
  const totalMarcaSec = useMemo(() => {
    const marcaSec = seccion === 'gtv' ? 'GTV' : seccion === 'emuca' ? 'Emuca' : 'Blum';
    return BLUM_PRODUCTOS.filter(p => (p.marca || 'Blum') === marcaSec).length;
  }, [seccion]);

  // Añade un accesorio BLUM al presupuesto. Precio = tarifa (sin descuento); el
  // descuento se aplica luego globalmente. No lleva medidas ni acabado de color.
  const addBlumToCart = (p) => {
    const sig = `blum|${p.ref}`;
    setCart(prev => {
      const i = prev.findIndex(l => l.sig === sig);
      if (i >= 0) { const c = [...prev]; c[i] = { ...c[i], qty: (c[i].qty || 1) + 1 }; return c; }
      return [...prev, {
        key: `${sig}-${Date.now()}`, sig, accesorio: true,
        tipo: p.nombre, ref: p.ref, gama: 'blum',
        precio: p.precio, precioBase: p.precio, qty: 1,
      }];
    });
  };

  // Nombre del casco, con la altura cuando es relevante (columnas/altillos),
  // para distinguir variantes como 200 vs 220 de altura.
  const altoSensible = (tp) => /columna|semicolumna|altillo/i.test(tp || '');
  // Quita rangos de altura del nombre (p. ej. "2000/2200", "1300/1500", "X580")
  // porque la altura real se muestra aparte, de forma independiente.
  const limpiaTipo = (tp) => String(tp || '').replace(/\s*\d{3,4}\/\d{3,4}\s*/g, ' ').replace(/\s*X\d{2,4}\s*/gi, ' ').replace(/\s{2,}/g, ' ').trim();
  const nombre = (m) => altoSensible(m.tipo) ? `${limpiaTipo(m.tipo)} · ${med(m.alto)} ${unidad} alto` : m.tipo;
  // Precio base (tarifa) de una línea, con respaldo para pedidos antiguos.
  const baseDe = (l) => (l.precioBase != null ? l.precioBase : (coef ? (l.precio || 0) / coef : (l.precio || 0)));
  const setQty = (key, q) => setCart(prev => prev.map(l => l.key === key ? { ...l, qty: Math.max(1, parseInt(q) || 1) } : l));
  const removeLine = (key) => setCart(prev => prev.filter(l => l.key !== key));

  const bruto = cart.reduce((s, l) => s + (l.precio || 0) * l.qty, 0);
  const dto = bruto * ((Number(descuento) || 0) / 100);
  const subtotal = bruto - dto;            // base imponible tras descuento
  const iva = subtotal * (ivaRate / 100);
  const total = subtotal + iva;

  const [savedId, setSavedId] = useState(null);
  const [savedKind, setSavedKind] = useState(null); // tipo del documento cargado/guardado (evita pisar entre presupuesto/pedido)
  const [histKind, setHistKind] = useState('presupuesto');
  // Expediente: código común que vincula la VENTA con su COMPRA a proveedor.
  const nuevoExpediente = () => `EXP-${Date.now().toString(36).toUpperCase()}`;
  const [expediente, setExpediente] = useState(nuevoExpediente);

  const nuevoPedido = () => {
    if (!window.confirm('¿Vaciar el presupuesto actual?')) return;
    setCart([]); setCliente(''); setRef(''); setDescuento(userDtoDesmontada); setSavedId(null); setSavedKind(null); setExpediente(nuevoExpediente());
  };

  // Guarda como presupuesto o pedido (mismo almacén, distinto 'kind').
  const guardar = async (kind) => {
    if (!cart.length) { alert('Añade cascos primero.'); return null; }
    setSaving(true);
    try {
      const r = await fetch(`${API_URL}/api/cascos/orders`, {
        method: 'POST', headers: { ...auth(), 'Content-Type': 'application/json' },
        body: JSON.stringify({
          id: (savedId && kind === savedKind) ? savedId : undefined, kind, expediente, cliente, ref, ivaRate, descuento,
          lines: cart, total: Math.round(total * 100) / 100,
          userId: currentUser?.id, createdByName: currentUser?.clientName || currentUser?.username,
        }),
      });
      if (!r.ok) throw new Error('Error');
      const d = await r.json();
      if (d.order?.id) { setSavedId(d.order.id); setSavedKind(kind); }
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
    } else { pdf.setFontSize(15); pdf.setFont(undefined, 'bold'); pdf.setFont(undefined, 'normal'); }
    pdf.setFontSize(16); pdf.setTextColor(30, 27, 65); pdf.setFont(undefined, 'bold');
    pdf.text('PRESUPUESTO COCINA DESMONTADA', W - M, 18, { align: 'right' }); pdf.setFont(undefined, 'normal');
    pdf.setFontSize(10); pdf.setTextColor(120);
    pdf.text(`${cliente || ''}${ref ? '  ·  Ref. ' + ref : ''}`, W - M, 24, { align: 'right' });
    pdf.text(new Date().toLocaleDateString('es-ES'), W - M, 29, { align: 'right' });
    autoTable(pdf, {
      startY: 38,
      head: [['Ud.', 'Módulo', 'Acabado', `Medidas Al×An×F (${unidad})`, 'Precio', 'Importe']],
      body: cart.map(l => [String(l.qty), nombre(l), acabadoOf(l), dimStr(l), eur(l.precio), eur(l.precio * l.qty)]),
      styles: { fontSize: 8.5, cellPadding: 1.8 },
      headStyles: { fillColor: [49, 46, 129], textColor: [255, 255, 255] },
      alternateRowStyles: { fillColor: [245, 245, 250] },
      columnStyles: { 0: { halign: 'center', cellWidth: 12 }, 2: { fontStyle: 'bold', textColor: [49, 46, 129] }, 4: { halign: 'right' }, 5: { halign: 'right' } },
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

  // Pedido a PROVEEDOR: pide el descuento comercial y genera el PDF a precio de
  // tarifa (puntos/€ base) con ese descuento aplicado. No usa el valor de punto.
  const pedidoProveedor = async () => {
    if (!cart.length) { alert('Añade cascos primero.'); return; }
    const resp = window.prompt('Descuento comercial del proveedor (%)', String(descProveedor || 0));
    if (resp === null) return;
    const d = Math.min(100, Math.max(0, Number(String(resp).replace(',', '.')) || 0));
    setDescProveedor(d);
    const { jsPDF } = await import('jspdf');
    const autoTable = (await import('jspdf-autotable')).default;
    const pdf = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
    const W = pdf.internal.pageSize.getWidth(); const M = 14;
    const logo = state?.logo;
    if (logo && typeof logo === 'string' && logo.startsWith('data:')) {
      try { const fmt = logo.includes('png') ? 'PNG' : logo.includes('webp') ? 'WEBP' : 'JPEG'; pdf.addImage(logo, fmt, M, 12, 32, 16); } catch {}
    } else { pdf.setFontSize(15); pdf.setFont(undefined, 'bold'); pdf.setFont(undefined, 'normal'); }
    pdf.setFontSize(16); pdf.setTextColor(30, 27, 65); pdf.setFont(undefined, 'bold');
    pdf.text('PEDIDO A PROVEEDOR', W - M, 18, { align: 'right' }); pdf.setFont(undefined, 'normal');
    pdf.setFontSize(10); pdf.setTextColor(120);
    pdf.text(`${cliente ? 'Ref. cliente: ' + cliente : ''}${ref ? '  ·  ' + ref : ''}`, W - M, 24, { align: 'right' });
    pdf.text(new Date().toLocaleDateString('es-ES'), W - M, 29, { align: 'right' });
    // Datos de entrega / comprador (empresa) tomados de Ajustes
    const cs = state?.settings || {};
    const entrega = centroEnvio || cs.companyAddress;
    const buyer = [cs.companyName || '', entrega, cs.companyTaxId ? `CIF: ${cs.companyTaxId}` : '', cs.companyPhone].filter(Boolean);
    pdf.setFontSize(8); pdf.setTextColor(110); pdf.setFont(undefined, 'bold');
    pdf.text('DATOS DE ENTREGA / COMPRADOR', M, 36); pdf.setFont(undefined, 'normal'); pdf.setTextColor(70);
    let yc = 40; buyer.forEach(l => { pdf.text(String(l), M, yc); yc += 4; });
    const tableStart = Math.max(38, yc + 2);
    const brutoP = cart.reduce((s, l) => s + baseDe(l) * l.qty, 0);
    const dtoP = brutoP * (d / 100);
    const subP = brutoP - dtoP;
    const ivaP = subP * (ivaRate / 100);
    const totP = subP + ivaP;
    // Guardar en historial de COMPRAS (proveedor)
    try {
      await fetch(`${API_URL}/api/cascos/orders`, {
        method: 'POST', headers: { ...auth(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ kind: 'compra', expediente, cliente, ref, ivaRate, descuento: d, lines: cart, total: Math.round(totP * 100) / 100, userId: currentUser?.id, createdByName: currentUser?.clientName || currentUser?.username }),
      });
    } catch {}
    autoTable(pdf, {
      startY: tableStart,
      head: [['Ud.', 'Módulo', 'Acabado', `Medidas Al×An×F (${unidad})`, 'Tarifa', 'Importe']],
      body: cart.map(l => [String(l.qty), nombre(l), acabadoOf(l), dimStr(l), eur(baseDe(l)), eur(baseDe(l) * l.qty)]),
      styles: { fontSize: 8.5, cellPadding: 1.8 },
      headStyles: { fillColor: [30, 27, 65], textColor: [255, 255, 255] },
      alternateRowStyles: { fillColor: [245, 245, 250] },
      columnStyles: { 0: { halign: 'center', cellWidth: 12 }, 2: { fontStyle: 'bold', textColor: [49, 46, 129] }, 4: { halign: 'right' }, 5: { halign: 'right' } },
      margin: { left: M, right: M },
    });
    let y = (pdf.lastAutoTable?.finalY || 38) + 8;
    const bx = W - M - 70;
    pdf.setFontSize(10); pdf.setTextColor(40);
    pdf.text('Bruto tarifa', bx, y); pdf.text(eur(brutoP), W - M, y, { align: 'right' }); y += 6;
    pdf.text(`Descuento comercial ${d}%`, bx, y); pdf.text('-' + eur(dtoP), W - M, y, { align: 'right' }); y += 6;
    pdf.text('Base', bx, y); pdf.text(eur(subP), W - M, y, { align: 'right' }); y += 6;
    pdf.text(`IVA ${ivaRate}%`, bx, y); pdf.text(eur(ivaP), W - M, y, { align: 'right' }); y += 4;
    pdf.setFillColor(30, 27, 65); pdf.roundedRect(bx - 4, y, 74 + 4, 11, 2, 2, 'F');
    pdf.setFontSize(13); pdf.setTextColor(255); pdf.setFont(undefined, 'bold');
    pdf.text('TOTAL', bx, y + 7.5); pdf.text(eur(totP), W - M, y + 7.5, { align: 'right' });
    pdf.save(`PedidoProveedor_${(cliente || 'cascos').replace(/\s+/g, '_')}.pdf`);
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
        } else { pdf.setFontSize(13); pdf.setFont(undefined, 'bold'); pdf.setTextColor(30, 27, 65); pdf.setFont(undefined, 'normal'); }
        pdf.setFontSize(11); pdf.setTextColor(49, 46, 129); pdf.setFont(undefined, 'bold');
        pdf.text('CATÁLOGO DE CASCOS · COCINA DESMONTADA', W - M, 13, { align: 'right' });
        pdf.setFont(undefined, 'normal'); pdf.setFontSize(8); pdf.setTextColor(150);
        pdf.text(`Precios en PUNTOS · medidas en ${unidad}`, W - M, 18, { align: 'right' });
        pdf.setTextColor(40);
      };
      const ptsFmt = (n) => (n == null ? '—' : Number(n).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 }));
      const medStr = (m) => `${med(m.alto)}×${med(m.ancho)}×${med(m.fondo)}`;
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
              head: [[`${tp} — Medidas Al×An×F (${unidad})`, ...colors.map(c => c.label)]],
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
        pdf.text('Cocina Desmontada', M, Hp - 6);
        pdf.text(`Página ${i} de ${n}`, W / 2, Hp - 6, { align: 'center' });
      }
      pdf.save('Catalogo_Cascos.pdf');
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
    setCart(o.lines || []); setOrders(null);
    if (o.expediente) setExpediente(o.expediente);
    if (o.kind === 'compra') { setDescProveedor(o.descuento || 0); setSavedId(null); setSavedKind(null); }
    else { setDescuento(o.descuento || 0); setSavedId(o.id); setSavedKind(o.kind); }  // solo reusa id dentro del mismo tipo
  };
  // Permiso para ver el documento vinculado (venta<->compra): master o usuarios autorizados.
  const puedeVerVinculados = isAdmin || currentUser?.canVerVinculadosCascos === true;
  const verVinculada = async (o) => {
    if (!o.expediente) { alert('Este documento no tiene venta/compra vinculada.'); return; }
    try {
      const r = await fetch(`${API_URL}/api/cascos/orders?expediente=${encodeURIComponent(o.expediente)}`, { headers: auth() });
      const d = await r.json();
      const list = (d.orders || []).filter(x => x.id !== o.id);
      // Si veo una compra, busco su venta (pedido/presupuesto); si veo una venta, busco la compra.
      const target = o.kind === 'compra'
        ? (list.find(x => x.kind === 'pedido') || list.find(x => x.kind === 'presupuesto'))
        : (list.find(x => x.kind === 'compra'));
      if (!target) { alert('Aún no hay documento vinculado a este expediente.'); return; }
      loadOrder(target);
    } catch { alert('No se pudo cargar el documento vinculado.'); }
  };
  const deleteOrder = async (id) => {
    if (!window.confirm('¿Eliminar?')) return;
    try { await fetch(`${API_URL}/api/cascos/orders/${id}`, { method: 'DELETE', headers: auth() }); setOrders(prev => (prev || []).filter(x => x.id !== id)); } catch {}
  };

  return (
    <div className="h-full flex flex-col p-4 sm:p-6 pb-32 lg:pb-6 bg-[#f0e9d8] overflow-y-auto">
      <div className="rounded-2xl bg-gradient-to-r from-indigo-600 via-violet-600 to-cyan-600 text-white px-4 py-2.5 mb-4 shadow-lg flex items-center justify-between gap-3 flex-wrap">
        <h1 className="ml-14 sm:ml-2 text-base sm:text-lg font-black flex items-center gap-2 whitespace-nowrap"><Box size={18} /> Cocina Desmontada</h1>
        <div className="flex items-center gap-1.5 flex-wrap">
          <button onClick={() => openHistory('presupuesto')} className="flex items-center gap-1.5 px-2.5 py-1.5 bg-white/15 hover:bg-white/25 text-white rounded-lg font-bold text-xs" title="Ventas: presupuestos"><FolderOpen size={15} /> Presupuestos</button>
          <button onClick={() => openHistory('pedido')} className="flex items-center gap-1.5 px-2.5 py-1.5 bg-white/15 hover:bg-white/25 text-white rounded-lg font-bold text-xs" title="Pedidos de venta (cliente)"><ClipboardList size={15} /> Pedidos Ventas</button>
          <button onClick={() => openHistory('compra')} className="flex items-center gap-1.5 px-2.5 py-1.5 bg-white/15 hover:bg-white/25 text-white rounded-lg font-bold text-xs" title="Pedidos de compra (proveedor)"><Download size={15} /> Pedidos Compras</button>
          {isAdmin && (
          <button onClick={generarCatalogo} disabled={genCat} title="Descargar catálogo en puntos (PDF)" className="flex items-center gap-1.5 px-2.5 py-1.5 bg-white/15 hover:bg-white/25 text-white rounded-lg font-bold text-xs disabled:opacity-50">{genCat ? <Loader size={15} className="animate-spin" /> : <Download size={15} />} Catálogo</button>
          )}
          <button onClick={nuevoPedido} className="flex items-center gap-1.5 px-2.5 py-1.5 bg-white text-indigo-700 rounded-lg font-bold text-xs hover:bg-indigo-50"><Plus size={15} /> Nuevo</button>
          {/* IMPORTAR: todas las vías de entrada agrupadas y VISIBLES (solo master).
              Antes la de Alvic estaba enterrada tras el candado + Shift + selector,
              así que no se encontraba. Sigue siendo master-only: el cliente no la ve. */}
          {esMasterCascos && (
            <div className="relative">
              <input ref={relacionInputRef} type="file" accept="application/pdf" className="hidden" onChange={(e) => importarRelacion(e.target.files?.[0])} />
              <button onClick={() => setMenuImportar(v => !v)}
                title="Importar muebles: en pantalla, desde la plantilla PDF o desde un presupuesto Alvic"
                className="flex items-center gap-1.5 px-2.5 py-1.5 bg-white/15 hover:bg-white/25 text-white rounded-lg font-bold text-xs">
                {importandoRel ? <Loader size={15} className="animate-spin" /> : <FileUp size={15} />} Importar
                <ChevronDown size={13} className={menuImportar ? 'rotate-180 transition-transform' : 'transition-transform'} />
              </button>
              {menuImportar && (
                <>
                  <div className="fixed inset-0 z-40" onClick={() => setMenuImportar(false)} />
                  <div className="absolute right-0 mt-1 z-50 w-72 bg-white rounded-xl shadow-2xl ring-1 ring-black/10 overflow-hidden text-slate-700">
                    <button onClick={() => { setMenuImportar(false); setRelacionRevisar([]); }}
                      className="w-full text-left px-3 py-2.5 hover:bg-indigo-50 flex items-start gap-2.5">
                      <List size={16} className="text-indigo-600 mt-0.5 shrink-0" />
                      <span>
                        <span className="block text-xs font-black">Relación en pantalla</span>
                        <span className="block text-[10px] text-slate-400">Montar los muebles a mano, sin PDF</span>
                      </span>
                    </button>
                    <button onClick={() => { setMenuImportar(false); relacionInputRef.current?.click(); }}
                      className="w-full text-left px-3 py-2.5 hover:bg-indigo-50 flex items-start gap-2.5 border-t border-slate-100">
                      <FileUp size={16} className="text-indigo-600 mt-0.5 shrink-0" />
                      <span>
                        <span className="block text-xs font-black">Desde plantilla (PDF nomenclaturas)</span>
                        <span className="block text-[10px] text-slate-400">Sube la plantilla rellenada con los códigos MV</span>
                      </span>
                    </button>
                    <button onClick={() => { setMenuImportar(false); setSistemaRenta('alvic'); setShowRenta(true); }}
                      className="w-full text-left px-3 py-2.5 hover:bg-amber-50 flex items-start gap-2.5 border-t border-slate-100">
                      <Package size={16} className="text-amber-600 mt-0.5 shrink-0" />
                      <span>
                        <span className="block text-xs font-black">Desde presupuesto Alvic (PDF)</span>
                        <span className="block text-[10px] text-slate-400">Proforma Alvic → equivalencia de cascos ACB</span>
                      </span>
                    </button>
                    <button onClick={() => { setMenuImportar(false); descargarNomenclaturas(); }}
                      disabled={descargandoPdf}
                      className="w-full text-left px-3 py-2.5 hover:bg-slate-50 flex items-start gap-2.5 border-t border-slate-100 disabled:opacity-50">
                      <Download size={16} className="text-slate-500 mt-0.5 shrink-0" />
                      <span>
                        <span className="block text-xs font-black">Descargar plantilla en blanco</span>
                        <span className="block text-[10px] text-slate-400">PDF rellenable con las 56 familias</span>
                      </span>
                    </button>
                  </div>
                </>
              )}
            </div>
          )}
          {/* Candado (solo master):
               - Clic normal = bloquear/desbloquear edición del presupuesto
               - Shift+clic = abrir/cerrar panel de Rentabilidad */}
          {esMasterCascos && (
            <button
              onClick={(e) => {
                if (e.shiftKey) { setShowRenta(v => !v); }
                else { setPresupuestoBloqueado(v => !v); }
              }}
              title={presupuestoBloqueado ? 'Desbloquear edición del presupuesto (Shift+clic = Rentabilidad)' : 'Bloquear edición del presupuesto (Shift+clic = Rentabilidad)'}
              className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg font-black text-xs transition-colors ${
                presupuestoBloqueado
                  ? 'bg-red-500 text-white hover:bg-red-600'
                  : showRenta ? 'bg-emerald-400 text-emerald-900' : 'bg-emerald-500/90 text-white hover:bg-emerald-500'
              }`}>
              {presupuestoBloqueado ? <Lock size={15} /> : <Unlock size={15} />}
              {presupuestoBloqueado && <span className="text-[10px] font-black">Bloqueado</span>}
            </button>
          )}
        </div>
      </div>

      {/* Panel de revisión de la relación importada (editar, buscar y añadir, volcar). */}
      {relacionRevisar && (
        <RelacionReview
          muebles={relacionRevisar}
          apiUrl={API_URL}
          authHeaders={auth}
          onClose={() => setRelacionRevisar(null)}
          onConfirm={(cabs) => {
            setState(p => ({ ...p, cascosPendingCabinets: cabs }));
            setRelacionRevisar(null);
            alert(`✅ ${cabs.reduce((s, m) => s + (m.qty || 1), 0)} mueble(s) volcados al presupuesto.\n\nSe emparejan con el catálogo por tipo y ancho; ajusta acabado, gama o cantidad si hace falta.`);
          }}
        />
      )}

      {/* Módulo unificado de rentabilidad (Alvic/MV). Oculto tras el candado (solo master). */}
      {esMasterCascos && showRenta && <RentabilidadUnificada esMaster={true} sistemaInicial={sistemaRenta} />}

      <div className="flex flex-col lg:flex-row gap-5 items-start">
        {/* Buscador + resultados */}
        {!panelExpanded && (
        <div className="flex-1 min-w-0 w-full space-y-4">
          {/* Pestañas por proveedor */}
          <div className="flex gap-1 bg-white/60 rounded-xl p-1 border border-slate-200 overflow-x-auto">
            {SECCIONES.map(s => (
              <button key={s.id} onClick={() => setSeccion(s.id)}
                className={`flex-1 min-w-[88px] px-3 py-2 rounded-lg text-sm font-black transition-colors flex items-center justify-center gap-1.5 ${seccion === s.id ? (s.id === 'blum' ? 'bg-orange-500 text-white shadow' : s.id === 'gtv' ? 'bg-blue-700 text-white shadow' : s.id === 'emuca' ? 'bg-slate-700 text-white shadow' : 'bg-indigo-600 text-white shadow') : 'text-slate-500 hover:bg-slate-100'}`}>
                {s.id === 'cascos' ? s.label : <ProviderLogo id={s.id} height={18} />}
              </button>
            ))}
          </div>

          {seccion === 'cascos' ? (<>
          <div className="bg-white rounded-2xl border border-slate-200 p-4">
            <div className="relative mb-3">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input value={q} onChange={e => setQ(e.target.value)} placeholder="Buscar por palabra: fregadero, campana, altillo, columna…"
                className="w-full pl-9 pr-9 py-2.5 border border-slate-200 rounded-xl text-sm focus:border-indigo-400 outline-none" />
              {q && <button type="button" onClick={() => setQ('')} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-300 hover:text-slate-600"><X size={16} /></button>}
            </div>
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
                <label className="text-[10px] font-black text-slate-400 uppercase mb-1 flex items-center gap-1.5">Color <span className="inline-block w-5 h-5 rounded-full border-2 border-white ring-1 ring-slate-300 shadow" style={{ background: SWATCH[colorActivo] || '#e2e8f0' }} /></label>
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
            {/* Accesos rápidos a las medidas más usadas */}
            <div className="flex items-center gap-1.5 flex-wrap mb-3">
              <span className="text-[10px] font-black text-slate-400 uppercase mr-1">Rápido:</span>
              {[['Altos 90', 900], ['Altos 70', 700], ['Bajos 80', 800], ['Bajos 70', 700]].map(([lab, mm], i) => (
                <button key={i} type="button" onClick={() => { setAltoMin(String(med(mm))); setAltoMax(String(med(mm))); }}
                  className="px-2.5 py-1 rounded-lg text-xs font-bold bg-indigo-50 text-indigo-700 hover:bg-indigo-100">{lab}</button>
              ))}
              <button type="button" onClick={() => { setQ(''); setTipo(''); setAltoMin(''); setAltoMax(''); setAnchoMin(''); setAnchoMax(''); }}
                className="px-2.5 py-1 rounded-lg text-xs font-bold bg-slate-100 text-slate-600 hover:bg-slate-200 flex items-center gap-1"><X size={12} /> Limpiar</button>
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
                  className="w-full text-left flex items-center gap-3 p-3 odd:bg-white even:bg-[#f7f1e3] hover:bg-indigo-50 transition-colors cursor-pointer group">
                  <div className="w-14 h-20 shrink-0 bg-slate-50 rounded border border-slate-100"><CascoDibujo dibujo={m.dibujo} tipo={m.tipo} alto={m.alto} ancho={m.ancho} fondo={m.fondo} unidad={unidad} /></div>
                  <div className="flex-1 min-w-0">
                    <p className="font-bold text-slate-800 text-sm sm:text-base truncate flex items-center gap-1.5"><span className="inline-block w-5 h-5 rounded-full border-2 border-white ring-1 ring-slate-300 shadow shrink-0" style={{ background: SWATCH[colorActivo] || '#e2e8f0' }} title={colorLabel(colorActivo)} />{nombre(m)} <span className="text-slate-400 font-normal text-xs">{m.grosor}mm</span></p>
                    <div className="flex flex-wrap gap-1.5 mt-1.5">
                      {[['Alto', m.alto], ['Ancho', m.ancho], ['Fondo', m.fondo]].map(([lab, val]) => (
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
                  <div className="relative w-full h-24 bg-slate-50 rounded-lg border border-slate-100 mb-2"><CascoDibujo dibujo={m.dibujo} tipo={m.tipo} alto={m.alto} ancho={m.ancho} fondo={m.fondo} unidad={unidad} /><span className="absolute top-1.5 right-1.5 w-6 h-6 rounded-full border-2 border-white ring-1 ring-slate-300 shadow" style={{ background: SWATCH[colorActivo] || '#e2e8f0' }} title={colorLabel(colorActivo)} /></div>
                  <p className="font-bold text-slate-800 text-xs leading-tight line-clamp-2">{nombre(m)}</p>
                  <p className="text-[10px] text-slate-400 mt-0.5">{med(m.alto)}×{med(m.ancho)}×{med(m.fondo)} {unidad} · {m.grosor}mm</p>
                  <p className="font-black text-indigo-700 text-sm mt-1">{eur(pc(m.precios[colorActivo]))}</p>
                  <span className="mt-1.5 inline-flex items-center justify-center gap-1 w-full px-2 py-1 bg-indigo-600 text-white rounded-lg text-[11px] font-bold group-hover:bg-indigo-700"><Plus size={12} /> Añadir</span>
                </button>
              ))}
              {resultados.length === 0 && <p className="col-span-full p-8 text-center text-slate-400 text-sm">No hay cascos con esos filtros.</p>}
            </div>
          </div>
          )}
          </>) : (seccion === 'blum' || seccion === 'gtv' || seccion === 'emuca') && totalMarcaSec > 0 ? (
            <div className="bg-white rounded-2xl border border-slate-200 p-4">
              <div className="flex items-center justify-between gap-3 mb-3">
                <ProviderLogo id={seccion} height={24} />
                <span className="text-xs text-slate-400">{resultadosBlum.length} de {totalMarcaSec} artículos</span>
              </div>
              <div className="relative mb-3">
                <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input value={qBlum} onChange={e => setQBlum(e.target.value)} placeholder="Buscar por referencia o descripción (bisagra, base, 110º…)"
                  className="w-full pl-9 pr-3 py-2 border border-slate-200 rounded-lg text-sm" />
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {resultadosBlum.map(p => (
                  <button key={p.ref} onClick={() => addBlumToCart(p)}
                    className="group text-left border border-slate-200 rounded-xl p-3 hover:border-orange-300 hover:bg-orange-50/40 transition-colors">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-[10px] font-black text-orange-700 bg-orange-50 border border-orange-100 rounded px-1.5 py-0.5">{p.ref}</span>
                      <span className="text-[10px] font-bold text-slate-400 uppercase">{p.cat}</span>
                    </div>
                    <p className="text-xs font-bold text-slate-700 mt-1.5 leading-snug">{p.nombre}</p>
                    <div className="flex items-center justify-between mt-2">
                      <p className="font-black text-orange-700 text-sm">{eur(p.precio)}</p>
                      <span className="inline-flex items-center gap-1 px-2 py-1 bg-orange-600 text-white rounded-lg text-[11px] font-bold group-hover:bg-orange-700"><Plus size={12} /> Añadir</span>
                    </div>
                  </button>
                ))}
                {resultadosBlum.length === 0 && <p className="col-span-full p-8 text-center text-slate-400 text-sm">No hay artículos con esa búsqueda.</p>}
              </div>
              <p className="text-[10px] text-slate-400 mt-3">Precios de tarifa sin descuento. El descuento se aplica en el presupuesto (campo «Descuento»).</p>
            </div>
          ) : (
            <div className="bg-white rounded-2xl border border-slate-200 p-10 text-center">
              <div className="mx-auto mb-4 flex items-center justify-center"><ProviderLogo id={seccion} height={44} /></div>
              <p className="text-sm text-slate-500 mt-1">{(SECCIONES.find(s => s.id === seccion) || {}).desc}</p>
              <p className="text-xs text-slate-400 mt-3 max-w-sm mx-auto">Catálogo en preparación. En cuanto carguemos la tarifa de este proveedor podrás buscar sus productos y añadirlos al mismo presupuesto.</p>
            </div>
          )}
        </div>
        )}

        {/* Presupuesto — redimensionable y ocultable */}
        {panelCollapsed ? (
          <button onClick={() => setPanelCollapsed(false)} title="Mostrar presupuesto"
            className="hidden lg:flex shrink-0 self-stretch items-center px-2 bg-white border border-slate-200 rounded-2xl text-slate-400 hover:text-indigo-600">
            <PanelLeftOpen size={20} />
          </button>
        ) : (
        <div className={`relative bg-white rounded-2xl border border-slate-200 p-4 h-fit w-full ${panelExpanded ? 'lg:flex-1' : 'lg:shrink-0'}`}
          style={!panelExpanded && isWide() ? { width: panelWidth, maxWidth: panelWidth } : undefined}>
          <div className="hidden lg:block absolute top-3 bottom-3 -left-0.5 w-1.5 cursor-ew-resize hover:bg-indigo-400/50 rounded-full z-10"
            onMouseDown={() => { isResizing.current = true; }} title="Arrastra para redimensionar" />
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-black text-slate-800 flex items-center gap-2"><ClipboardList size={18} /> Presupuesto <span className="px-1.5 py-0.5 rounded bg-amber-100 text-amber-700 text-[9px] font-black" title="Expediente: vincula esta venta con su compra a proveedor">🔗 {expediente}</span></h3>
            <div className="hidden lg:flex items-center gap-1">
              <button onClick={() => setPanelExpanded(v => !v)} title={panelExpanded ? 'Volver a ver el buscador' : 'Ver el presupuesto en grande'} className="p-1.5 text-slate-400 hover:text-indigo-600">{panelExpanded ? <Minimize2 size={16} /> : <Maximize2 size={16} />}</button>
              {!panelExpanded && <button onClick={() => setPanelCollapsed(true)} title="Ocultar presupuesto" className="p-1.5 text-slate-400 hover:text-indigo-600"><PanelRightClose size={16} /></button>}
            </div>
          </div>
          <div className="grid grid-cols-1 gap-2 mb-3">
            <input value={cliente} onChange={e => setCliente(e.target.value)} placeholder="Cliente" className="px-3 py-2 border border-slate-200 rounded-lg text-sm" />
            <input value={ref} onChange={e => setRef(e.target.value)} placeholder="Referencia" className="px-3 py-2 border border-slate-200 rounded-lg text-sm" />
          </div>
          <div className="space-y-2 max-h-[40vh] overflow-y-auto mb-3">
            {cart.map(l => (
              <div key={l.key} className="flex items-center gap-2 border border-slate-100 rounded-lg p-2">
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-bold text-slate-700 truncate">{l.accesorio ? l.tipo : nombre(l)}</p>
                  {l.accesorio ? (
                    <span className="mt-0.5 inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-orange-50 border border-orange-100 max-w-full">
                      <ProviderLogo id="blum" height={12} />
                      <span className="text-[10px] font-black text-orange-700 truncate">{l.ref}</span>
                    </span>
                  ) : (
                    <span className="mt-0.5 inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-indigo-50 border border-indigo-100 max-w-full">
                      <span className="inline-block w-5 h-5 rounded-full border-2 border-white ring-1 ring-slate-300 shadow shrink-0" style={{ background: SWATCH[l.color] || '#e2e8f0' }} />
                      <span className="text-[11px] font-black text-indigo-800 truncate">{acabadoOf(l)}</span>
                    </span>
                  )}
                  <p className="text-[10px] text-slate-400 mt-0.5">{l.accesorio ? eur(l.precio) : `${med(l.alto)}×${med(l.ancho)}×${med(l.fondo)} ${unidad} · ${eur(l.precio)}`}</p>
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
            <div className="flex justify-between text-slate-500 items-center"><span className="flex items-center gap-1">Descuento <input type="number" value={descuento} disabled={!isAdmin} title={isAdmin ? 'Editable (master)' : 'Descuento asignado por el administrador'} onChange={e => setDescuento(Math.min(100, Math.max(0, Number(e.target.value) || 0)))} className="w-16 px-2 py-0.5 border border-slate-200 rounded text-center disabled:bg-slate-100 disabled:text-slate-400" />%</span><span className="font-bold text-rose-500">-{eur(dto)}</span></div>
            <div className="flex justify-between text-slate-500"><span>Base imponible</span><span className="font-bold">{eur(subtotal)}</span></div>
            <div className="flex justify-between text-slate-500 items-center"><span className="flex items-center gap-1">IVA <input type="number" value={ivaRate} onChange={e => setIvaRate(Number(e.target.value) || 0)} className="w-16 px-2 py-0.5 border border-slate-200 rounded text-center" />%</span><span className="font-bold">{eur(iva)}</span></div>
            <div className="flex justify-between text-slate-900 text-lg font-black pt-1 bg-orange-50 -mx-1 px-2 rounded-lg py-1"><span>TOTAL</span><span className="text-orange-600">{eur(total)}</span></div>
          </div>
          {centros.length > 0 && (
            <div className="mt-3">
              <label className="text-[10px] font-black text-slate-400 uppercase block mb-1">Centro de envío (para pedido a proveedor)</label>
              <select value={centroEnvio} onChange={e => setCentroEnvio(e.target.value)} className="w-full px-2 py-2 border border-slate-200 rounded-lg text-sm bg-white">
                <option value="">— Usar dirección fiscal —</option>
                {centros.map((c, i) => <option key={i} value={c}>{c}</option>)}
              </select>
            </div>
          )}
          <div className="grid grid-cols-1 gap-2 mt-3">
            <button onClick={guardarPresupuesto} disabled={saving || !cart.length} className="flex items-center justify-center gap-2 px-4 py-2.5 bg-cyan-600 text-white rounded-xl font-bold text-sm hover:bg-cyan-700 disabled:opacity-50">{saving ? <Loader size={16} className="animate-spin" /> : <Save size={16} />} Guardar presupuesto</button>
            <div className="grid grid-cols-2 gap-2">
              <button onClick={generarPedido} disabled={saving || !cart.length} className="flex items-center justify-center gap-2 px-3 py-2.5 bg-emerald-600 text-white rounded-xl font-bold text-sm hover:bg-emerald-700 disabled:opacity-50"><ClipboardList size={16} /> Pedido</button>
              <button onClick={exportarPDF} disabled={!cart.length} className="flex items-center justify-center gap-2 px-3 py-2.5 bg-indigo-600 text-white rounded-xl font-bold text-sm hover:bg-indigo-700 disabled:opacity-50"><Download size={16} /> PDF</button>
            </div>
            <button onClick={pedidoProveedor} disabled={!cart.length} className="flex items-center justify-center gap-2 px-4 py-2.5 bg-slate-800 text-white rounded-xl font-bold text-sm hover:bg-slate-900 disabled:opacity-50"><ClipboardList size={16} /> Pedido a proveedor</button>
          </div>
        </div>
        )}
      </div>

      {/* Botón flotante (móvil): ir al presupuesto */}
      <button onClick={() => { setPanelCollapsed(false); window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' }); }}
        className="lg:hidden fixed bottom-5 right-5 z-40 flex items-center gap-2 px-4 py-3 bg-indigo-600 text-white rounded-full shadow-2xl font-bold text-sm">
        <ShoppingCart size={18} /> {cart.length}
      </button>

      {/* Historial de pedidos */}
      {Array.isArray(orders) && (
        <div className="fixed inset-0 z-[200] bg-black/50 flex items-center justify-center p-4" onClick={() => setOrders(null)}>
          <div className="bg-white rounded-2xl w-full max-w-lg max-h-[80vh] overflow-hidden flex flex-col" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
              <h3 className="font-black text-slate-800">{histKind === 'compra' ? 'Pedidos Compras (proveedor)' : histKind === 'pedido' ? 'Pedidos Ventas (cliente)' : 'Presupuestos (ventas)'} de cascos</h3>
              <button onClick={() => setOrders(null)} className="p-1.5 text-slate-400 hover:text-slate-700"><X size={18} /></button>
            </div>
            <div className="p-4 overflow-y-auto">
              {orders.length === 0 ? <p className="text-sm text-slate-400 text-center py-8">No hay {histKind === 'compra' ? 'compras' : histKind === 'pedido' ? 'pedidos' : 'presupuestos'} guardados.</p> : orders.map(o => (
                <div key={o.id} className="flex items-center gap-3 border border-slate-200 rounded-xl p-2 mb-2 hover:bg-slate-50">
                  <div className="flex-1 min-w-0">
                    <p className="font-bold text-slate-700 text-sm truncate">{o.cliente || 'Sin cliente'}{o.ref ? ` · ${o.ref}` : ''}</p>
                    <p className="text-[10px] text-slate-400">{o.createdAt ? new Date(o.createdAt).toLocaleString('es-ES') : ''} · {(o.lines || []).length} líneas</p>
                    {o.expediente && <span className="inline-block mt-0.5 px-1.5 py-0.5 rounded bg-amber-100 text-amber-700 text-[9px] font-black" title="Código que vincula la venta con su compra a proveedor">🔗 {o.expediente}</span>}
                  </div>
                  <span className="text-sm font-black text-slate-800">{eur(o.total)}</span>
                  <button onClick={() => loadOrder(o)} className="px-3 py-1.5 bg-indigo-600 text-white rounded-lg text-xs font-bold hover:bg-indigo-700">Abrir</button>
                  {puedeVerVinculados && o.expediente && (
                    <button onClick={() => verVinculada(o)} title="Abrir la venta/compra vinculada" className="px-2 py-1.5 bg-amber-500 text-white rounded-lg text-xs font-bold hover:bg-amber-600">🔗 Vinculada</button>
                  )}
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
