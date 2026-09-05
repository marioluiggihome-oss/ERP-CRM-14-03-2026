/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
import React, { useState, useMemo, useRef, useEffect } from 'react';
import { Box, Search, Plus, Trash2, Download, FolderOpen, Save, X, Loader, ClipboardList, List, LayoutGrid, Maximize2, Minimize2, PanelRightClose, PanelLeftOpen, ShoppingCart, Lock, Unlock, FileUp, ChevronDown, Package } from 'lucide-react';
import { CASCOS, CASCOS_GAMAS } from '../data/cascos';
import { ACB_PUERTAS, ACB_PUERTAS_SERIES, cantosDeSerieACB } from '../data/acbPuertas';
import { getToken } from '../services/api';
import { guardarSesion, leerSesion, irA } from '../services/navegacion';
import { usePulsacionLarga, AYUDA_CANDADO } from '../utils/pulsacionLarga';
import { aMilimetros } from '../utils/medidas';
import RentabilidadUnificada from './RentabilidadUnificada';
import RelacionReview from './RelacionReview';
import { valorPuntoCascos } from '../utils/valorPuntoCascos';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const eur = (n) => `${(Number(n) || 0).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} €`;
const auth = () => ({ 'Authorization': `Bearer ${getToken()}` });
// Normaliza para búsqueda sin acentos ni mayúsculas.
const norm = (s) => String(s || '').normalize('NFD').replace(/\p{Diacritic}/gu, '').toLowerCase().trim();

// Secciones por proveedor dentro de Cocina Desmontada. CASCOS ya operativo;
// el resto quedan listos para cargar su tarifa.
const SECCIONES = [
  { id: 'cascos', label: 'CASCOS', desc: 'Módulos / cuerpos de mueble' },
  // Los FRENTES del mismo proveedor (Canteado Industrial S.L.). Van pegados a
  // CASCOS a proposito: es el mismo pedido y el mismo albaran.
  { id: 'acbPuertas', label: 'ACB PUERTAS', desc: 'Frentes y puertas canteadas' },
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
        <rect x="0" y="0" width="200" height="84" rx="8" fill="#ce875e" />
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
        <text x="100" y="60" textAnchor="middle" fontFamily="Arial, Helvetica, sans-serif" fontSize="56" fontWeight="900" fill="#343c71" letterSpacing="1">GTV</text>
      </svg>
    );
  }
  if (id === 'emuca') {
    // "emuca" en gris con swoosh amarillo y claim.
    return (
      <svg height={height} viewBox="0 0 240 84" style={box} aria-label="emuca">
        <rect x="0" y="0" width="240" height="84" rx="8" fill="#ffffff" />
        <text x="12" y="52" fontFamily="Arial, Helvetica, sans-serif" fontSize="46" fontWeight="800" fill="#4d4d4f" letterSpacing="-1">emuca</text>
        <path d="M205 40 q10 -18 24 -14 q-6 10 -18 22 q-8 4 -6 -8 Z" fill="#e9c97e" />
        <circle cx="223" cy="20" r="3.5" fill="#ffffff" />
        <text x="12" y="72" fontFamily="Arial, Helvetica, sans-serif" fontSize="15" fill="#e9c97e" letterSpacing="1">where creation begins</text>
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
  const STROKE = '#4a5564', THIN = '#97a3b2';
  const detail = [];

  const shelvesAt = (n) => { for (let s = 1; s <= n; s++) detail.push(<line key={'s' + s} x1={x + 4} y1={y + (bh * s) / (n + 1)} x2={x + bw - 4} y2={y + (bh * s) / (n + 1)} stroke={THIN} strokeWidth="1.5" />); };

  if (t.includes('fregadero')) {
    // seno de fregadero + grifo
    detail.push(<rect key="b" x={x + bw * 0.18} y={cy - bh * 0.12} width={bw * 0.64} height={bh * 0.3} rx="3" fill="#e3e7f5" stroke={STROKE} strokeWidth="1.6" />);
    detail.push(<circle key="d" cx={cx} cy={cy + bh * 0.03} r="3" fill="none" stroke={STROKE} strokeWidth="1.4" />);
    detail.push(<path key="g" d={`M ${cx + bw * 0.22} ${cy - bh * 0.12} v -8 q 0 -5 -6 -5`} fill="none" stroke={STROKE} strokeWidth="1.6" />);
  } else if (t.includes('placa')) {
    // encimera con 4 fuegos
    [[-0.18, -0.06], [0.18, -0.06], [-0.18, 0.14], [0.18, 0.14]].forEach((p, i) =>
      detail.push(<circle key={'f' + i} cx={cx + bw * p[0]} cy={cy + bh * p[1]} r="5" fill="none" stroke={STROKE} strokeWidth="1.5" />));
  } else if (t.includes('horno')) {
    // horno: tirador + visor
    detail.push(<line key="h" x1={x + 6} y1={y + bh * 0.26} x2={x + bw - 6} y2={y + bh * 0.26} stroke={STROKE} strokeWidth="2" />);
    detail.push(<rect key="v" x={x + bw * 0.22} y={y + bh * 0.4} width={bw * 0.56} height={bh * 0.4} rx="2" fill="#e3e7f5" stroke={STROKE} strokeWidth="1.4" />);
  } else if (t.includes('bombona')) {
    // puerta con rejilla de ventilación
    [0.62, 0.7, 0.78].forEach((p, i) => detail.push(<line key={'r' + i} x1={x + bw * 0.3} y1={y + bh * p} x2={x + bw * 0.7} y2={y + bh * p} stroke={THIN} strokeWidth="1.6" />));
  } else if (t.includes('escurre')) {
    // escurreplatos: rejilla vertical
    for (let i = 1; i <= 5; i++) detail.push(<line key={'e' + i} x1={x + (bw * i) / 6} y1={y + 5} x2={x + (bw * i) / 6} y2={y + bh * 0.55} stroke={THIN} strokeWidth="1.4" />);
    shelvesAt(1);
  } else if (t.includes('campana')) {
    // campana extraíble: trapecio
    detail.push(<path key="c" d={`M ${x} ${y + bh} L ${x + bw * 0.25} ${y} L ${x + bw * 0.75} ${y} L ${x + bw} ${y + bh} Z`} fill="#f0f2fa" stroke={STROKE} strokeWidth="1.6" />);
  } else if (dibujo === 'angular' || t.includes('rincón') || t.includes('rincon') || t.includes('angular')) {
    // módulo en esquina
    detail.push(<path key="a" d={`M ${x} ${y} L ${x + bw * 0.55} ${y} L ${x + bw} ${y + bh * 0.45} L ${x + bw} ${y + bh} L ${x} ${y + bh} Z`} fill="#f2f5f8" stroke={STROKE} strokeWidth="1.6" />);
  } else if (dibujo === 'columna' || t.includes('columna') || t.includes('despensa')) {
    shelvesAt(alto >= 2000 ? 5 : 4);
  } else if (t.includes('cubretermo') || t.includes('termo')) {
    detail.push(<rect key="tm" x={x + bw * 0.3} y={cy - bh * 0.1} width={bw * 0.4} height={bh * 0.22} rx="2" fill="#e3e7f5" stroke={STROKE} strokeWidth="1.4" />);
  } else {
    // alto / bajo / transversal / sobre: baldas
    shelvesAt(alto >= 1300 ? 3 : alto >= 850 ? 2 : 1);
  }

  const showAngular = dibujo === 'angular' && !(t.includes('rincón') || t.includes('rincon') || t.includes('angular'));
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-full">
      <rect x={x} y={y} width={bw} height={bh} rx="2" fill="#f8fafb" stroke={STROKE} strokeWidth="2" />
      {detail}
      {showAngular && <line x1={x} y1={y} x2={x + bw / 2} y2={y + bh / 3} stroke={STROKE} strokeWidth="1.5" />}
      <text x={cx} y={y - 3} textAnchor="middle" fontSize="9" fill="#364150">{dim(ancho)} {unidad}</text>
      <text x={x - 3} y={cy} textAnchor="middle" fontSize="9" fill="#364150" transform={`rotate(-90 ${x - 3} ${cy})`}>{dim(alto)} {unidad}</text>
    </svg>
  );
}

const Cascos = ({ state, setState }) => {
  const currentUser = state?.currentUser;
  const esMasterCascos = !!(currentUser?.isAdmin || currentUser?.isPrimaryAdmin || currentUser?.isGerente);
  // Rentabilidad va MÁS cerrado que el resto de Cascos: ahí están el coste real,
  // el descuento de proveedor y el margen. Un gerente entra a Cascos, pero a
  // esto NO: solo el master.
  const esMasterRenta = !!(currentUser?.isAdmin || currentUser?.isPrimaryAdmin || currentUser?.isMaster);
  const [showRenta, setShowRenta] = useState(false); // módulo unificado de rentabilidad (Alvic/MV, solo master)
  const [presupuestoBloqueado, setPresupuestoBloqueado] = useState(false); // bloquear edición del presupuesto
  const [importandoRel, setImportandoRel] = useState(false); // importar relación de muebles (PDF nomenclaturas)
  const [relacionRevisar, setRelacionRevisar] = useState(null); // muebles detectados pendientes de revisar
  const [relacionNoLeidas, setRelacionNoLeidas] = useState([]);  // lo escrito que el lector no entendio
  const [descargandoPdf, setDescargandoPdf] = useState(false);
  const [menuImportar, setMenuImportar] = useState(false);   // menú de vías de importación
  const [sistemaRenta, setSistemaRenta] = useState(null);    // 'alvic' | 'mv' al abrir desde el menú
  const relacionInputRef = useRef(null);

  // Rentabilidad se abría SOLO con Shift+clic, y una tablet no tiene tecla
  // Shift: en tablet el margen no estaba protegido, estaba inalcanzable. Ahora
  // se abre igual manteniendo pulsado el candado.
  const candadoRenta = usePulsacionLarga(() => {
    if (esMasterRenta) { setSistemaRenta('mv'); setShowRenta(v => !v); }
  });

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
      // Se guarda también lo que el lector NO ha sabido interpretar, para
      // enseñarlo: si no, esas líneas valen 0 € y el total sale corto sin avisar.
      setRelacionNoLeidas(d.noLeidas || []);
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
  // ── ACB PUERTAS ──────────────────────────────────────────────────────────
  const [seriePuerta, setSeriePuerta] = useState(ACB_PUERTAS_SERIES[0].id);
  // EL CANTO ES PARTE DEL PRECIO, no un adorno: en las series Touch el canto
  // ALMA cuesta siempre mas que el PVC. Al cambiar de serie se vuelve al canto
  // que esa serie SI fabrica — si no, se quedaria pedido un «alma» en una serie
  // que solo hace PVC y la matriz saldria vacia sin decir por que.
  const [cantoPuerta, setCantoPuerta] = useState('pvc');
  const cantosSerie = cantosDeSerieACB(seriePuerta);
  const cantoActivo = cantosSerie.some(c => c.id === cantoPuerta) ? cantoPuerta : cantosSerie[0].id;
  const [qBlum, setQBlum] = useState(''); // búsqueda en el catálogo BLUM
  const [cart, setCart] = useState([]);
  // El carrito sobrevive a salir a otro módulo y volver: si no, ir al analizador
  // a comprobar una medida vaciaba el pedido a medio montar.
  const sesionRef = useRef(null);
  sesionRef.current = { cart };
  const estadoRef = useRef(state); estadoRef.current = state;
  const setEstadoRef = useRef(setState); setEstadoRef.current = setState;
  useEffect(() => {
    const g = leerSesion(estadoRef.current, 'cascos');
    if (g?.cart?.length) setCart(g.cart);
    return () => {
      const f = setEstadoRef.current;
      if (f) guardarSesion(f, 'cascos', sesionRef.current);
    };
  }, []);
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
  const [descProveedor, setDescProveedor] = useState(() => {
    try { return Number(localStorage.getItem('cascos_descProveedor')) || 0; } catch { return 0; }
  });
  useEffect(() => {
    try { localStorage.setItem('cascos_descProveedor', String(descProveedor)); } catch { /* noop */ }
  }, [descProveedor]);
  // Centros de envío configurados en Ajustes (uno por línea: "Nombre — Dirección").
  const centros = String(state?.settings?.centrosEnvio || '').split('\n').map(l => l.trim()).filter(Boolean);
  const [centroEnvio, setCentroEnvio] = useState('');
  /* EN COCINA DESMONTADA NO HAY PVP: EL PRECIO ES LA TARIFA (master, 31/08).
   *
   * «En cocina desmontada conseguimos precios de cascos sueltos y no hay pvp»,
   * y «en cocina montada del presupuestador sí hay pvp, en cocina desmontada
   * no».
   *
   * Aquí se multiplicaba por el valor del punto, así que un tablero de 246,00 €
   * de tarifa ACB salía a 492,00 € — el doble de lo que se cobra. Se ve en la
   * pantalla del catálogo, se añade al presupuesto y se manda al cliente: no
   * hay ningún error que saltar, solo un presupuesto por el doble.
   *
   * EL VALOR DEL PUNTO NO DESAPARECE, cambia de sitio: en el Presupuestador
   * (Cocina Montada) sí se usa, pero para calcular el COSTE —tarifa × 2, luego
   * −50 % y −28 %—, no para el precio de venta. Aquí no pinta nada.
   *
   * Sobre este precio actúa después el descuento comercial del cliente, que
   * viene de su ficha de usuario (`descuento`, más abajo).
   */
  const pc = (base) => (base == null ? null : Math.round(base * 100) / 100);

  /* EL VALOR DEL PUNTO SIGUE HACIENDO FALTA, PERO NO PARA EL PRECIO. Lo usan
   * el panel de Rentabilidad y el importador de proformas, que calculan COSTES
   * —ahí sí se parte del PVP y se aplican los descuentos—. Lo que ya no hace es
   * multiplicar lo que se le cobra al cliente. */
  const coef = valorPuntoCascos(state);
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

  // Recalcular precios de cascos en carrito al cambiar el color activo (Bug #3 de la auditoría)
  useEffect(() => {
    if (!colorActivo) return;
    setCart(prev => {
      let changed = false;
      const next = prev.map(l => {
        if (l.accesorio || !l.grosor) return l;
        const match = CASCOS.find(c => c.tipo === l.tipo && String(c.grosor) === String(l.grosor) && c.alto === l.alto && c.ancho === l.ancho);
        if (match && match.precios && match.precios[colorActivo] != null) {
          const newBase = match.precios[colorActivo];
          const newPrecio = pc(newBase);
          const newLabel = colorLabel(colorActivo);
          if (l.color !== colorActivo || l.precioBase !== newBase || l.precio !== newPrecio) {
            changed = true;
            const newSig = `${match.id}|${colorActivo}`;
            return {
              ...l,
              sig: newSig,
              color: colorActivo,
              colorLabel: newLabel,
              precioBase: newBase,
              precio: newPrecio
            };
          }
        }
        return l;
      });
      return changed ? next : prev;
    });
  }, [colorActivo, coef]);

  // Volcado de MUEBLES desde el Diseñador 3D: empareja cada mueble detectado con
  // el catálogo CASCOS (misma familia bajo/alto/columna + ancho más cercano) y lo
  // precia con el color/grosor/gama activos. Si no hay match, entra estimado a 0€.
  useEffect(() => {
    const cabs = state?.cascosPendingCabinets;
    if (!cabs || !cabs.length) return;
    // famOf: detecta la familia del mueble usando tipo, familia Y descripcion
    // porque el campo tipo solo llega como 'BAJO'/'ALTO'/'COLUMNA' (genérico)
    // mientras que familia y descripcion tienen el tipo específico (BAJO_FREGADERO, etc.)
    const famOf = (det) => {
      // Aceptar tanto un string (tipo) como un objeto mueble completo
      const t = typeof det === 'string' ? det : (det?.tipo || '');
      const extra = typeof det === 'object' ? `${det?.familia || ''} ${det?.descripcion || ''}` : '';
      const s = norm(t + ' ' + extra);
      if (/alto|altillo|sobre\s*encimera|sobre\s*columna|cubretermo|escurre|campana|vitrina/.test(s)) return 'alto';
      if (/columna|semicolumna/.test(s)) return 'columna';
      // Tipos específicos de bajo — deben emparejarse con su casco exacto
      if (/fregadero|placa/.test(s)) return 'bajo_fregadero';
      if (/horno/.test(s)) return 'bajo_horno';
      return 'bajo';
    };
    const pool = CASCOS.filter(m => (m.gama || 'kit') === gama && String(m.grosor) === String(grosorActivo) && m.precios[colorActivo] != null);
    const lines = cabs.map((det, idx) => {
      const fam = famOf(det);
      // Mapear familia del mueble al tipo de casco exacto
      const tipoCascoExacto = fam === 'bajo_fregadero' ? 'Bajo Fregadero'
        : fam === 'bajo_horno' ? 'Bajo Horno'
        : null;
      let cand = tipoCascoExacto
        ? pool.filter(m => m.tipo === tipoCascoExacto)
        : pool.filter(m => famOf(m) === fam);
      // Si no hay cascos del tipo exacto, caer al tipo genérico de la familia
      if (!cand.length && tipoCascoExacto) cand = pool.filter(m => famOf(m.tipo) === 'bajo');
      if (!cand.length) cand = pool;
      // A MILÍMETROS ANTES DE COMPARAR. El catálogo está en mm y hay orígenes
      // que mandan cm: comparar 60 contra 600 no da error, da el casco más
      // estrecho del catálogo — y el presupuesto sale con muebles que nadie ha
      // pedido, con la misma pinta que uno bueno.
      const anchoDet = aMilimetros(det.ancho);
      const altoDet = aMilimetros(det.alto);
      const fondoDet = aMilimetros(det.fondo);
      // Manda el ANCHO; con el ancho igualado, decide el ALTO; y en último
      // término el fondo. Un bajo de 80 de alto y uno de 70 no son el mismo
      // mueble, y hasta ahora el alto no pintaba nada: una columna de 220 se
      // emparejaba con una de 200 sin que nadie lo notara.
      const distancia = (m) => {
        const dAncho = Math.abs((Number(m.ancho) || 0) - anchoDet);
        const dAlto = altoDet ? Math.abs((Number(m.alto) || 0) - altoDet) : 0;
        const dFondo = fondoDet ? Math.abs((Number(m.fondo) || 0) - fondoDet) : 0;
        return [dAncho, dAlto, dFondo];
      };
      let best = null, bd = null;
      for (const m of cand) {
        const d = distancia(m);
        if (!bd || d[0] < bd[0] || (d[0] === bd[0] && (d[1] < bd[1] || (d[1] === bd[1] && d[2] < bd[2])))) {
          bd = d; best = m;
        }
      }
      // Si el ancho pedido y el del casco no se parecen ni de lejos, esto NO es
      // un emparejamiento: es el catálogo diciendo que no tiene esa medida.
      // Antes se colaba como bueno y el presupuesto no decía nada.
      const SIN_PARECIDO_MM = 60;   // 6 cm: más de eso ya es otro mueble
      if (best && anchoDet && bd[0] > SIN_PARECIDO_MM) best = null;
      if (best) {
        const base = best.precios[colorActivo];
        return { key: `vk-${Date.now()}-${idx}`, sig: `${best.id}|${colorActivo}`, tipo: best.tipo, grosor: best.grosor, dibujo: best.dibujo, fondo: best.fondo, alto: best.alto, ancho: best.ancho, color: colorActivo, colorLabel: colorLabel(colorActivo), gama: best.gama || 'kit', precio: pc(base), precioBase: base, qty: det.qty || 1 };
      }
      // Sin casco que se le parezca: entra con SUS medidas y a 0 €, marcado como
      // estimado. Vale más una línea que se ve que está sin precio que una línea
      // con el casco equivocado y un precio que parece bueno.
      return { key: `vk-${Date.now()}-${idx}`, sig: `estimado|${norm(det.tipo)}|${anchoDet}|${altoDet}`, tipo: det.tipo, grosor: grosorActivo, dibujo: null, fondo: fondoDet, alto: altoDet, ancho: anchoDet, color: colorActivo, colorLabel: colorLabel(colorActivo), gama, precio: 0, precioBase: 0, qty: det.qty || 1, estimado: true };
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
  const SWATCH = { blanco: '#f2f5f8', aluminio: '#cdd5de', grafito: '#202023', blancoHidrofugo: '#f6f6f4', robleAurora: '#d2c7b4', spike: '#a9928e', stone: '#c6c2ba', roble: '#a08269', olmo: '#9a7e67', blancoEsp: '#f8fafb' };

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
  /** LA MATRIZ DE LA SERIE ELEGIDA: filas de alto, columnas de ancho.
   *
   *  Se pinta igual que viene en la tarifa del proveedor a proposito. Asi se
   *  puede cotejar celda a celda contra el PDF, que es lo que hay que poder
   *  hacer con una tarifa: comprobarla, no fiarse. */
  const matrizPuertas = useMemo(() => {
    const filas = ACB_PUERTAS.filter(f => f.serie === seriePuerta && f.canto === cantoActivo);
    const anchos = [...new Set(filas.map(f => f.ancho))].sort((a, b) => a - b);
    const grupos = [];
    filas.forEach(f => {
      const clave = f.altos.join('&');
      let g = grupos.find(x => x.clave === clave);
      if (!g) { g = { clave, altos: f.altos, precios: {} }; grupos.push(g); }
      g.precios[f.ancho] = f.precio;
    });
    grupos.sort((a, b) => a.altos[0] - b.altos[0]);
    return { anchos, grupos };
  }, [seriePuerta, cantoActivo]);

  const serieObj = ACB_PUERTAS_SERIES.find(s => s.id === seriePuerta) || ACB_PUERTAS_SERIES[0];

  /** Anade un frente al mismo carrito que los cascos: es el mismo pedido. */
  const addPuertaToCart = (altos, ancho, precio) => {
    const alto = altos[0];
    const sig = `acbp|${seriePuerta}|${cantoActivo}|${altos.join('&')}|${ancho}`;
    setCart(prev => {
      const i = prev.findIndex(l => l.sig === sig);
      if (i >= 0) { const c = [...prev]; c[i] = { ...c[i], qty: (c[i].qty || 1) + 1 }; return c; }
      return [...prev, {
        key: `${sig}-${Date.now()}`, sig, puerta: true,
        tipo: `Frente ${serieObj.label}`,
        // Las DOS medidas del grupo viajan en la descripcion: un «1198 & 1298»
        // no es un alto, son dos al mismo precio, y al proveedor hay que
        // decirle cual se quiere.
        gama: 'acbPuertas', serie: seriePuerta, serieLabel: serieObj.label,
        canto: cantoActivo,
        cantoLabel: (cantosSerie.find(c => c.id === cantoActivo) || {}).label || '',
        altos, alto, ancho,
        precio: pc(precio), precioBase: precio, qty: 1,
      }];
    });
  };

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
  /** El precio de TARIFA de una línea, que es lo que se le pide al proveedor.
   *
   *  Desde que el precio de venta ES la tarifa, los dos coinciden. El respaldo
   *  sigue haciendo falta para los presupuestos GUARDADOS antes de hoy: aquellos
   *  llevan dentro un `precio` que era la tarifa × 2, y su `precioBase` con la
   *  tarifa buena. Por eso se lee primero `precioBase` — sin él, reabrir un
   *  pedido viejo pediría al proveedor por el doble. */
  const baseDe = (l) => (l.precioBase != null ? l.precioBase : (l.precio || 0));
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

    const defaultFechaRec = new Date(Date.now() + 5 * 86400000).toISOString().split('T')[0];
    const fechaRecResp = window.prompt('Fecha estimada de recepción del material en taller (YYYY-MM-DD)', defaultFechaRec);
    const fechaEstRecepcion = (fechaRecResp && fechaRecResp.trim()) ? fechaRecResp.trim() : defaultFechaRec;

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
    pdf.text(`Fecha Pedido: ${new Date().toLocaleDateString('es-ES')}  ·  Est. Recepción: ${fechaEstRecepcion}`, W - M, 29, { align: 'right' });
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
      const payloadCompra = {
        kind: 'compra', expediente, cliente, ref, ivaRate, descuento: d, lines: cart, total: Math.round(totP * 100) / 100,
        fechaEstRecepcion,
        fechaEntrega: new Date(Date.now() + 10 * 86400000).toISOString().split('T')[0],
        cascosEstado: 'pedido', puertasEstado: 'pedido', herrajesEstado: 'pedido', accesoriosEstado: 'pedido',
        userId: currentUser?.id, createdByName: currentUser?.clientName || currentUser?.username
      };
      await fetch(`${API_URL}/api/cascos/orders`, {
        method: 'POST', headers: { ...auth(), 'Content-Type': 'application/json' },
        body: JSON.stringify(payloadCompra),
      });

      // Sincronizar en el almacén de órdenes de taller
      try {
        const ofId = `OF-EXT-${expediente.replace(/[^a-zA-Z0-9]/g, '')}`;
        const ofPayload = {
          id: ofId,
          cliente: cliente || 'Cliente General',
          ref: ref || 'Pedido Cascos Proveedor',
          tipo: 'Cocina Desmontada',
          tarifa: `Descuento ${d}%`,
          casco: cart[0] ? (acabadoOf(cart[0])) : 'Estándar',
          origen: 'EXTERNO',
          modulos: cart.reduce((s, x) => s + (Number(x.qty) || 1), 0),
          fechaInicio: new Date().toISOString().split('T')[0],
          fechaEstRecepcion: fechaEstRecepcion,
          fechaEntrega: new Date(Date.now() + 10 * 86400000).toISOString().split('T')[0],
          cascosEstado: 'pedido', puertasEstado: 'pedido', herrajesEstado: 'pedido', accesoriosEstado: 'pedido',
          prioridad: 'NORMAL',
        };
        const guardadas = JSON.parse(localStorage.getItem('ordenes_fabricacion_taller') || '[]');
        const actualizadas = [ofPayload, ...guardadas.filter(x => x.id !== ofId)];
        localStorage.setItem('ordenes_fabricacion_taller', JSON.stringify(actualizadas));
      } catch (e) { console.error('Error guardando OF en taller:', e); }

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
  // BORRAR MIRA LA RESPUESTA. Antes se quitaba la fila de la lista pasara lo
  // que pasara: un `catch {}` vacío y ningún `r.ok`. Con un 403 —o con el 409
  // de un pedido ya liquidado, que NO se puede borrar porque lleva dentro lo
  // que se pagó por él— el pedido seguía en la base de datos y de la pantalla
  // desaparecía igual. Se creía borrado y volvía en cuanto alguien recargaba.
  const deleteOrder = async (id) => {
    if (!window.confirm('¿Eliminar este documento? No se puede deshacer.')) return;
    try {
      const r = await fetch(`${API_URL}/api/cascos/orders/${id}`, { method: 'DELETE', headers: auth() });
      if (!r.ok) {
        const d = await r.json().catch(() => ({}));
        alert(d.detail || 'No se ha podido eliminar.');
        return;
      }
      setOrders(prev => (prev || []).filter(x => x.id !== id));
    } catch {
      alert('No se ha podido eliminar: no hay conexión con el servidor.');
    }
  };

  return (
    <div className="h-full flex flex-col p-4 sm:p-6 pb-32 lg:pb-6 bg-[#ede9df] overflow-y-auto">
      <div className="hueco-logo rounded-2xl bg-gradient-to-r from-indigo-600 via-violet-600 to-cyan-600 text-white px-4 py-2.5 mb-4 shadow-lg flex items-center justify-between gap-3 flex-wrap">
        <h1 className="text-base sm:text-lg font-black flex items-center gap-2 whitespace-nowrap"><Box size={18} /> Cocina Desmontada</h1>
        <div className="flex items-center gap-1.5 flex-wrap">
          <button onClick={() => openHistory('presupuesto')} className="flex items-center gap-1.5 px-2.5 py-1.5 bg-white/15 hover:bg-white/25 text-white rounded-lg font-bold text-xs" title="Ventas: presupuestos"><FolderOpen size={15} /> Presupuestos</button>
          <button onClick={() => openHistory('pedido')} className="flex items-center gap-1.5 px-2.5 py-1.5 bg-white/15 hover:bg-white/25 text-white rounded-lg font-bold text-xs" title="Pedidos de venta (cliente)"><ClipboardList size={15} /> Pedidos Ventas</button>
          <button onClick={() => openHistory('compra')} className="flex items-center gap-1.5 px-2.5 py-1.5 bg-white/15 hover:bg-white/25 text-white rounded-lg font-bold text-xs" title="Pedidos de compra (proveedor)"><Download size={15} /> Pedidos Compras</button>
          {isAdmin && (
          <button onClick={generarCatalogo} disabled={genCat} title="Descargar catálogo en puntos (PDF)" className="flex items-center gap-1.5 px-2.5 py-1.5 bg-white/15 hover:bg-white/25 text-white rounded-lg font-bold text-xs disabled:opacity-50">{genCat ? <Loader size={15} className="animate-spin" /> : <Download size={15} />} Catálogo</button>
          )}
          <button onClick={nuevoPedido} className="flex items-center gap-1.5 px-2.5 py-1.5 bg-white text-accion-700 rounded-lg font-bold text-xs hover:bg-accion-50"><Plus size={15} /> Nuevo</button>
          {/* IMPORTAR: todas las vías de entrada agrupadas y VISIBLES (solo master).
              Antes la de Alvic estaba enterrada tras el candado + Shift + selector,
              así que no se encontraba. Sigue siendo master-only: el cliente no la ve. */}
          {esMasterCascos && (
            <div className="flex items-center gap-2 relative">
              <input ref={relacionInputRef} type="file" accept="application/pdf" className="hidden" onChange={(e) => importarRelacion(e.target.files?.[0])} />
              <button onClick={() => setMenuImportar(v => !v)}
                title="Importar muebles: pegado masivo, plantilla PDF o presupuesto Alvic"
                className="flex items-center gap-1.5 px-2.5 py-1.5 bg-white/15 hover:bg-white/25 text-white rounded-lg font-bold text-xs">
                {importandoRel ? <Loader size={15} className="animate-spin" /> : <FileUp size={15} />} Importar
                <ChevronDown size={13} className={menuImportar ? 'rotate-180 transition-transform' : 'transition-transform'} />
              </button>
              {menuImportar && (
                <>
                  <div className="fixed inset-0 z-40" onClick={() => setMenuImportar(false)} />
                  <div className="absolute right-0 top-full mt-1 z-50 w-72 bg-white rounded-xl shadow-2xl ring-1 ring-black/10 overflow-hidden text-slate-700">
                    <button onClick={() => { setMenuImportar(false); setRelacionRevisar([]); }}
                      className="w-full text-left px-3 py-2.5 hover:bg-indigo-50 flex items-start gap-2.5 border-b border-slate-100">
                      <List size={16} className="text-dato-600 mt-0.5 shrink-0" />
                      <span>
                        <span className="block text-xs font-black text-slate-800">Pegado Masivo / Relación en pantalla</span>
                        <span className="block text-[10px] text-slate-500">Pega textos de WhatsApp, notas de obra o móntalos a mano</span>
                      </span>
                    </button>
                    <button onClick={() => { setMenuImportar(false); relacionInputRef.current?.click(); }}
                      className="w-full text-left px-3 py-2.5 hover:bg-accion-50 flex items-start gap-2.5 border-b border-slate-100">
                      <FileUp size={16} className="text-dato-600 mt-0.5 shrink-0" />
                      <span>
                        <span className="block text-xs font-black text-slate-800">Desde plantilla (PDF nomenclaturas)</span>
                        <span className="block text-[10px] text-slate-500">Sube la plantilla rellenada con los códigos MV</span>
                      </span>
                    </button>
                    {esMasterRenta && (
                    <button onClick={() => { setMenuImportar(false); setSistemaRenta('alvic'); setShowRenta(true); }}
                      className="w-full text-left px-3 py-2.5 hover:bg-accion-50 flex items-start gap-2.5 border-b border-slate-100">
                      <Package size={16} className="text-dato-600 mt-0.5 shrink-0" />
                      <span>
                        <span className="block text-xs font-black text-slate-800">Desde presupuesto Alvic (PDF)</span>
                        <span className="block text-[10px] text-slate-500">Proforma Alvic → equivalencia de cascos ACB</span>
                      </span>
                    </button>
                    )}
                    <button onClick={() => { setMenuImportar(false); descargarNomenclaturas(); }}
                      disabled={descargandoPdf}
                      className="w-full text-left px-3 py-2.5 hover:bg-slate-50 flex items-start gap-2.5 disabled:opacity-50">
                      <Download size={16} className="text-slate-500 mt-0.5 shrink-0" />
                      <span>
                        <span className="block text-xs font-black text-slate-800">Descargar plantilla en blanco</span>
                        <span className="block text-[10px] text-slate-500">PDF rellenable con las 56 familias</span>
                      </span>
                    </button>
                  </div>
                </>
              )}
              {/* Panel Rentabilidad/Alvic a pantalla completa.
                   Antes colgaba del botón Importar como un desplegable de 700px:
                   una tabla de 16 columnas metida en esa ventanita era imposible
                   de usar, y encima la recortaba el contenedor. */}
              {showRenta && esMasterRenta && (
                /* `text-slate-900` NO es decoración: este panel cuelga, en el
                   DOM, de la barra de cabecera de arriba, que lleva `text-white`.
                   `position: fixed` cambia dónde se PINTA, pero no corta la
                   HERENCIA de CSS, así que el color blanco seguía bajando hasta
                   aquí. Todo lo que no declara su propio color lo heredaba —y
                   los `<input>` no lo declaran—, de modo que el master escribía
                   el descuento, la mano de obra o el margen y veía la casilla
                   vacía: letra blanca sobre fondo blanco. El menú desplegable de
                   al lado ya se defendía así con `text-slate-700`.

                   A pantalla completa (sin `max-w`) porque la tabla tiene 17
                   columnas: recortada a 1400 px obligaba a hacer scroll lateral
                   para leer una sola línea. */
                <div className="fixed inset-0 z-[9998] bg-slate-900/60 p-1.5 sm:p-3 flex text-slate-900"
                  onMouseDown={(e) => { if (e.target === e.currentTarget) setShowRenta(false); }}>
                  <div className="w-full h-full flex flex-col min-h-0">
                    <RentabilidadUnificada
                      esMaster={esMasterRenta}
                      sistemaInicial={sistemaRenta}
                      valorPunto={coef}
                      onClose={() => setShowRenta(false)}
                      onVolcarDesmontada={(muebles) => {
                        setState(p => ({ ...p, cascosPendingCabinets: muebles }));
                        setShowRenta(false);
                      }}
                      onVolcarMontada={(muebles) => {
                        setState(p => ({ ...p, cocinaMontadaPendingMuebles: muebles, currentTab: 'cocinaMontada3' }));
                        setShowRenta(false);
                      }}
                    />
                  </div>
                </div>
              )}
            </div>
          )}
          {/* Candado (solo master):
               - Clic normal = bloquear/desbloquear edición del presupuesto
               - Shift+clic = abrir/cerrar panel de Rentabilidad */}
          {esMasterCascos && (
            <button
              {...candadoRenta.props}
              onClick={(e) => {
                // La pulsación larga ya ha abierto Rentabilidad: el clic que
                // llega al soltar no debe además bloquear el presupuesto.
                if (candadoRenta.consumir()) return;
                if (e.shiftKey) { if (esMasterRenta) { setSistemaRenta('mv'); setShowRenta(v => !v); } }
                else { setPresupuestoBloqueado(v => !v); }
              }}
              title={`${presupuestoBloqueado ? 'Desbloquear' : 'Bloquear'} edición del presupuesto${esMasterRenta ? ` · Rentabilidad: ${AYUDA_CANDADO}` : ''}`}
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
          noLeidas={relacionNoLeidas}
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

      {/* Módulo unificado de rentabilidad: ahora se muestra como dropdown bajo el botón Importar */}

      <div className="flex flex-col lg:flex-row gap-5 items-start">
        {/* Buscador + resultados */}
        {!panelExpanded && (
        <div className="flex-1 min-w-0 w-full space-y-4">
          {/* Pestañas por proveedor */}
          <div className="flex gap-1 bg-white/60 rounded-xl p-1 border border-slate-200 overflow-x-auto">
            {SECCIONES.map(s => (
              <button key={s.id} onClick={() => setSeccion(s.id)}
                className={`flex-1 min-w-[88px] px-3 py-2 rounded-lg text-sm font-black transition-colors flex items-center justify-center gap-1.5 ${seccion === s.id ? (s.id === 'blum' ? 'bg-accion-500 text-white shadow' : s.id === 'gtv' ? 'bg-accion-700 text-white shadow' : s.id === 'emuca' ? 'bg-slate-700 text-white shadow' : 'bg-accion-600 text-white shadow') : 'text-slate-500 hover:bg-slate-100'}`}>
                {s.id === 'cascos' ? s.label : <ProviderLogo id={s.id} height={18} />}
              </button>
            ))}
          </div>

          {seccion === 'cascos' ? (<>
          <div className="bg-white rounded-2xl border border-slate-200 p-4">
            <div className="relative mb-3">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input value={q} onChange={e => setQ(e.target.value)} placeholder="Buscar por palabra: fregadero, campana, altillo, columna…"
                className="w-full pl-9 pr-9 py-2.5 border border-slate-200 rounded-xl text-sm focus:border-accion-400 outline-none" />
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
                <label className="text-[10px] font-black text-slate-400 uppercase mb-1 flex items-center gap-1.5">Color <span className="inline-block w-5 h-5 rounded-full border-2 border-white ring-1 ring-slate-300 shadow" style={{ background: SWATCH[colorActivo] || '#e3e8ee' }} /></label>
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
                  className="px-2.5 py-1 rounded-lg text-xs font-bold bg-accion-50 text-accion-700 hover:bg-accion-100">{lab}</button>
              ))}
              <button type="button" onClick={() => { setQ(''); setTipo(''); setAltoMin(''); setAltoMax(''); setAnchoMin(''); setAnchoMax(''); }}
                className="px-2.5 py-1 rounded-lg text-xs font-bold bg-slate-100 text-slate-600 hover:bg-slate-200 flex items-center gap-1"><X size={12} /> Limpiar</button>
            </div>
            <div className="flex items-center justify-between gap-2 flex-wrap">
              <p className="text-[11px] text-slate-400 flex items-center gap-1"><Search size={12} /> {resultados.length} cascos encontrados</p>
              <div className="flex items-center gap-2 flex-wrap">
              <button type="button" onClick={toggleUnidad} title="Cambiar unidad (cm / mm)"
                className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-black bg-slate-100 text-slate-600 hover:bg-slate-200 transition-colors">
                <span className={unidad === 'cm' ? 'text-dato-700' : ''}>cm</span><span className="text-slate-300">/</span><span className={unidad === 'mm' ? 'text-dato-700' : ''}>mm</span>
              </button>
              <div className="flex items-center gap-1 bg-slate-100 rounded-lg p-1">
                <button type="button" onClick={() => setVista('iconos')} title="Vista de iconos"
                  className={`flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-bold transition-colors ${vista === 'iconos' ? 'bg-white text-accion-700 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}><LayoutGrid size={14} /> Iconos</button>
                <button type="button" onClick={() => setVista('lista')} title="Vista de lista"
                  className={`flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-bold transition-colors ${vista === 'lista' ? 'bg-white text-accion-700 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}><List size={14} /> Lista</button>
              </div>
              </div>
            </div>
          </div>

          {vista === 'lista' ? (
          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
            <div className="max-h-[55vh] overflow-y-auto divide-y divide-slate-100">
              {resultados.map(m => (
                <button key={m.id} type="button" onClick={() => addToCart(m)}
                  className="w-full text-left flex items-center gap-3 p-3 odd:bg-white even:bg-[#f7f1e3] hover:bg-accion-50 transition-colors cursor-pointer group">
                  <div className="w-14 h-20 shrink-0 bg-slate-50 rounded border border-slate-100"><CascoDibujo dibujo={m.dibujo} tipo={m.tipo} alto={m.alto} ancho={m.ancho} fondo={m.fondo} unidad={unidad} /></div>
                  <div className="flex-1 min-w-0">
                    <p className="font-bold text-slate-800 text-sm sm:text-base truncate flex items-center gap-1.5"><span className="inline-block w-5 h-5 rounded-full border-2 border-white ring-1 ring-slate-300 shadow shrink-0" style={{ background: SWATCH[colorActivo] || '#e3e8ee' }} title={colorLabel(colorActivo)} />{nombre(m)} <span className="text-slate-400 font-normal text-xs">{m.grosor}mm</span></p>
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
                  className="relative flex flex-col items-center text-center border border-slate-200 rounded-xl p-2.5 hover:border-accion-400 hover:bg-accion-50 hover:shadow-md transition-all cursor-pointer group">
                  <div className="relative w-full h-24 bg-slate-50 rounded-lg border border-slate-100 mb-2"><CascoDibujo dibujo={m.dibujo} tipo={m.tipo} alto={m.alto} ancho={m.ancho} fondo={m.fondo} unidad={unidad} /><span className="absolute top-1.5 right-1.5 w-6 h-6 rounded-full border-2 border-white ring-1 ring-slate-300 shadow" style={{ background: SWATCH[colorActivo] || '#e3e8ee' }} title={colorLabel(colorActivo)} /></div>
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
          </>) : seccion === 'acbPuertas' ? (
          /* ─────────── ACB PUERTAS ───────────
             Los FRENTES del mismo proveedor que los cascos. Se pinta la matriz
             tal como viene en su tarifa —altos en filas, anchos en columnas—
             para poder COTEJARLA celda a celda contra el PDF. Con una tarifa
             hay que poder comprobarla, no fiarse de ella. */
          <div data-testid="acb-puertas" className="bg-white rounded-2xl border border-slate-200 p-4">
            <div className="flex items-center gap-3 flex-wrap mb-3">
              <div className="flex-1 min-w-[220px]">
                <label className="text-[10px] font-black text-slate-400 uppercase block mb-1">Serie</label>
                <select value={seriePuerta} onChange={e => setSeriePuerta(e.target.value)}
                  data-testid="acb-puertas-serie"
                  className="w-full px-2 py-2 border border-slate-200 rounded-lg text-sm bg-white">
                  {ACB_PUERTAS_SERIES.map(s2 => <option key={s2.id} value={s2.id}>{s2.label}</option>)}
                </select>
              </div>
              {cantosSerie.length > 1 && (
                <div className="min-w-[150px]">
                  <label className="text-[10px] font-black text-slate-400 uppercase block mb-1">Canto</label>
                  <select value={cantoActivo} onChange={e => setCantoPuerta(e.target.value)}
                    data-testid="acb-puertas-canto"
                    className="w-full px-2 py-2 border border-slate-200 rounded-lg text-sm bg-white">
                    {cantosSerie.map(c => <option key={c.id} value={c.id}>{c.label}</option>)}
                  </select>
                </div>
              )}
              <div className="flex-[2] min-w-[240px] text-[11px] text-slate-500 self-end pb-1">
                <div><span className="font-black text-slate-600">Acabados:</span> {serieObj.acabados}</div>
                <div><span className="font-black text-slate-600">Canto:</span> {serieObj.canto}</div>
              </div>
            </div>

            {/* LA LETRA PEQUENA DE LA TARIFA, DONDE SE VE. Son las tres cosas
                que cambian el precio de verdad y no estan en ninguna casilla:
                el tirador gola aparte, los montados que no lo admiten y los
                frentes pequenos que salen lisos aunque pidas otra cosa. */}
            {serieObj.nota && (
              <div data-testid="acb-puertas-nota"
                className="mb-3 px-3 py-2 rounded-lg bg-aviso-50 border border-aviso-200 text-[11px] text-aviso-800 font-bold">
                {serieObj.nota}
              </div>
            )}

            <div className="overflow-x-auto">
              <table className="w-full text-[11px] whitespace-nowrap">
                <thead className="bg-slate-50 text-slate-500 border-b border-slate-200">
                  <tr>
                    <th className="text-left py-2 px-2 font-black uppercase sticky left-0 bg-slate-50">Alto × ancho</th>
                    {matrizPuertas.anchos.map(w => (
                      <th key={w} className="text-right py-2 px-2 font-black">{med(w)}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {matrizPuertas.grupos.map(g => (
                    <tr key={g.clave} className="hover:bg-slate-50/60">
                      <td className="py-1.5 px-2 font-black text-slate-700 sticky left-0 bg-white">
                        {g.altos.map(med).join(' · ')}
                      </td>
                      {matrizPuertas.anchos.map(w => {
                        const precio = g.precios[w];
                        /* SIN PRECIO NO HAY BOTON. La casilla que el PDF deja
                           en «----» es que ACB NO FABRICA esa medida en esta
                           serie: se rotula «--», nunca 0,00 EUR. Un cero seria
                           un frente gratis en el escandallo (regla 7). */
                        if (precio == null) {
                          return <td key={w} className="py-1.5 px-2 text-right text-slate-300"
                            title="ACB no fabrica esta medida en esta serie">--</td>;
                        }
                        return (
                          <td key={w} className="py-1.5 px-1 text-right">
                            <button type="button"
                              onClick={() => addPuertaToCart(g.altos, w, precio)}
                              data-testid="acb-puertas-add"
                              title={`Añadir ${serieObj.label} ${g.altos.join(' o ')} x ${w} mm`}
                              className="w-full px-2 py-1 rounded-md font-mono font-bold text-slate-700 hover:bg-accion-600 hover:text-white transition-colors">
                              {eur(precio)}
                            </button>
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="mt-3 text-[10px] text-slate-400">
              Medidas en {unidad === 'cm' ? 'centímetros' : 'milímetros'}. Precios de TARIFA, antes del descuento de ACB.
              Un alto con dos medidas (1198 · 1298) son dos frentes al mismo precio: al pedir hay que decir cuál.
            </div>
          </div>
          ) : (seccion === 'blum' || seccion === 'gtv' || seccion === 'emuca') && totalMarcaSec > 0 ? (
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
                    className="group text-left border border-slate-200 rounded-xl p-3 hover:border-accion-300 hover:bg-accion-50/40 transition-colors">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-[10px] font-black text-orange-700 bg-orange-50 border border-orange-100 rounded px-1.5 py-0.5">{p.ref}</span>
                      <span className="text-[10px] font-bold text-slate-400 uppercase">{p.cat}</span>
                    </div>
                    <p className="text-xs font-bold text-slate-700 mt-1.5 leading-snug">{p.nombre}</p>
                    <div className="flex items-center justify-between mt-2">
                      <p className="font-black text-dato-700 text-sm">{eur(p.precio)}</p>
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
            className="hidden lg:flex shrink-0 self-stretch items-center px-2 bg-white border border-slate-200 rounded-2xl text-slate-400 hover:text-accion-600">
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
              <button onClick={() => setPanelExpanded(v => !v)} title={panelExpanded ? 'Volver a ver el buscador' : 'Ver el presupuesto en grande'} className="p-1.5 text-slate-400 hover:text-accion-600">{panelExpanded ? <Minimize2 size={16} /> : <Maximize2 size={16} />}</button>
              {!panelExpanded && <button onClick={() => setPanelCollapsed(true)} title="Ocultar presupuesto" className="p-1.5 text-slate-400 hover:text-accion-600"><PanelRightClose size={16} /></button>}
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
                      <span className="inline-block w-5 h-5 rounded-full border-2 border-white ring-1 ring-slate-300 shadow shrink-0" style={{ background: SWATCH[l.color] || '#e3e8ee' }} />
                      <span className="text-[11px] font-black text-indigo-800 truncate">{acabadoOf(l)}</span>
                    </span>
                  )}
                  <p className="text-[10px] text-slate-400 mt-0.5">{l.accesorio ? eur(l.precio) : `${med(l.alto)}×${med(l.ancho)}×${med(l.fondo)} ${unidad} · ${eur(l.precio)}`}</p>
                </div>
                <input type="number" value={l.qty} onChange={e => setQty(l.key, e.target.value)} className="w-12 px-1 py-1 border border-slate-200 rounded text-sm text-center" />
                <span className="w-20 text-right text-xs font-bold text-slate-700">{eur(l.precio * l.qty)}</span>
                <button onClick={() => removeLine(l.key)} className="text-slate-300 hover:text-error-500"><Trash2 size={14} /></button>
              </div>
            ))}
            {cart.length === 0 && <p className="text-center text-slate-400 text-xs py-6">Añade cascos desde el buscador.</p>}
          </div>
          <div className="border-t border-slate-100 pt-3 space-y-1 text-sm">
            <div className="flex justify-between text-slate-500"><span>Bruto líneas</span><span className="font-bold">{eur(bruto)}</span></div>
            <div className="flex justify-between text-slate-500 items-center"><span className="flex items-center gap-1">Descuento <input type="number" value={descuento} disabled={!isAdmin} title={isAdmin ? 'Editable (master)' : 'Descuento asignado por el administrador'} onChange={e => setDescuento(Math.min(100, Math.max(0, Number(e.target.value) || 0)))} className="w-16 px-2 py-0.5 border border-slate-200 rounded text-center disabled:bg-slate-100 disabled:text-slate-400" />%</span><span className="font-bold text-dato-500">-{eur(dto)}</span></div>
            <div className="flex justify-between text-slate-500"><span>Base imponible</span><span className="font-bold">{eur(subtotal)}</span></div>
            <div className="flex justify-between text-slate-500 items-center"><span className="flex items-center gap-1">IVA <input type="number" value={ivaRate} onChange={e => setIvaRate(Number(e.target.value) || 0)} className="w-16 px-2 py-0.5 border border-slate-200 rounded text-center" />%</span><span className="font-bold">{eur(iva)}</span></div>
            <div className="flex justify-between text-slate-900 text-lg font-black pt-1 bg-orange-50 -mx-1 px-2 rounded-lg py-1"><span>TOTAL</span><span className="text-dato-600">{eur(total)}</span></div>
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
            <button onClick={guardarPresupuesto} disabled={saving || !cart.length} className="flex items-center justify-center gap-2 px-4 py-2.5 bg-accion-600 text-white rounded-xl font-bold text-sm hover:bg-accion-700 disabled:opacity-50">{saving ? <Loader size={16} className="animate-spin" /> : <Save size={16} />} Guardar presupuesto</button>
            <div className="grid grid-cols-2 gap-2">
              <button onClick={generarPedido} disabled={saving || !cart.length} className="flex items-center justify-center gap-2 px-3 py-2.5 bg-ok-600 text-white rounded-xl font-black text-sm hover:bg-ok-700 disabled:opacity-50" title="Crear un PEDIDO: cuenta para la cooperativa y genera comisión" data-testid="cascos-crear-pedido"><ClipboardList size={16} /> Crear pedido</button>
              <button onClick={exportarPDF} disabled={!cart.length} className="flex items-center justify-center gap-2 px-3 py-2.5 bg-accion-600 text-white rounded-xl font-bold text-sm hover:bg-accion-700 disabled:opacity-50"><Download size={16} /> PDF</button>
            </div>
            <button onClick={pedidoProveedor} disabled={!cart.length} className="flex items-center justify-center gap-2 px-4 py-2.5 bg-slate-800 text-white rounded-xl font-bold text-sm hover:bg-slate-900 disabled:opacity-50"><ClipboardList size={16} /> Pedido a proveedor</button>

            {/* EL ATAJO A LA OBRA. El expediente y el almacén ya sabían leer un
                pedido de cascos, pero desde aquí no había forma de llegar: para
                ver cómo iba la obra que acabas de presupuestar tenías que
                salir, entrar en otro módulo y buscarla por el nombre.

                Solo aparece con el pedido GUARDADO: sin id no hay obra que
                abrir, y un botón que a veces lleva a un sitio vacío se deja de
                pulsar. */}
            {savedId && (
              <div className="grid grid-cols-2 gap-2 pt-1 border-t border-slate-200">
                <button
                  onClick={() => irA(setState, 'expediente')}
                  title="Ver el expediente de esta obra: en qué punto está y qué falta"
                  className="flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl font-bold text-sm border border-slate-300 text-slate-700 hover:bg-slate-50">
                  <ClipboardList size={16} /> Expediente
                </button>
                <button
                  onClick={() => irA(setState, 'almacen')}
                  title="Qué material de este pedido hay en el almacén y qué hay que comprar"
                  className="flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl font-bold text-sm border border-slate-300 text-slate-700 hover:bg-slate-50">
                  <Package size={16} /> Almacén
                </button>
              </div>
            )}
          </div>
        </div>
        )}
      </div>

      {/* Botón flotante (móvil): ir al presupuesto */}
      <button onClick={() => { setPanelCollapsed(false); window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' }); }}
        className="lg:hidden fixed bottom-5 right-5 z-40 flex items-center gap-2 px-4 py-3 bg-accion-600 text-white rounded-full shadow-2xl font-bold text-sm">
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
                    {o.expediente && <span className="inline-block mt-0.5 px-1.5 py-0.5 rounded bg-dato-100 text-dato-700 text-[9px] font-black" title="Código que vincula la venta con su compra a proveedor">🔗 {o.expediente}</span>}
                  </div>
                  <span className="text-sm font-black text-slate-800">{eur(o.total)}</span>
                  <button onClick={() => loadOrder(o)} className="px-3 py-1.5 bg-accion-600 text-white rounded-lg text-xs font-bold hover:bg-accion-700">Abrir</button>
                  {puedeVerVinculados && o.expediente && (
                    <button onClick={() => verVinculada(o)} title="Abrir la venta/compra vinculada" className="px-2 py-1.5 bg-accion-500 text-white rounded-lg text-xs font-bold hover:bg-accion-600">🔗 Vinculada</button>
                  )}
                  <button onClick={() => deleteOrder(o.id)} className="p-1.5 text-error-400 hover:text-error-600 hover:bg-error-50 rounded-lg"><Trash2 size={15} /></button>
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
