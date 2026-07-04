/**
 * 3D Estudio — Módulo unificado de diseño de cocinas
 * ====================================================
 * Pestañas:
 *   1. Render 3D      → Render fotorrealista + estilos rápidos
 *   2. Plano 2D       → Plano técnico acotado
 *   3. Ficha Técnica  → Ficha de materiales y plazos
 *   4. Presentación   → HTML de presentación para cliente
 *   5. Instalaciones  → Puntos eléctricos, agua y gas
 *   6. Galería        → Renders guardados
 *
 * Funcionalidades migradas de AIRenderStudio:
 *   - Adjuntar render al presupuesto (localStorage → ResumenCocinas)
 *   - Guardar/abrir proyectos (persistencia en MongoDB via /api/ai-engine/designs)
 *   - Voz Web Speech API (se añade al texto, no lo pisa)
 *   - Comparativa croquis vs render (toggle lado a lado)
 *
 * Temas: Día / Noche / Auto (sistema operativo)
 */

import React, { useState, useRef, useCallback, useEffect } from 'react';
import {
  ChefHat, Image, FileText, Mic, MicOff, Upload,
  Download, Loader2, RefreshCw, Maximize2, X,
  CheckCircle, AlertCircle, Sparkles, Edit3, ZoomIn,
  Presentation, Eye, Sun, Moon, Monitor, Printer,
  Zap, Droplets, Flame, LayoutGrid, Wand2,
  Heart, Trash2, FolderOpen, Save, Stamp, ImagePlus,
  Send, Plus
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL || '';

// ─── Hook Web Speech API (voz que se AÑADE al texto, no lo pisa) ─────────────
function useSpeechRecognition() {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [isSupported, setIsSupported] = useState(false);
  const recognitionRef = useRef(null);
  const finalRef = useRef('');

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      setIsSupported(true);
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'es-ES';

      recognition.onresult = (event) => {
        let interimTranscript = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const result = event.results[i];
          if (result.isFinal) {
            finalRef.current += result[0].transcript;
          } else {
            interimTranscript += result[0].transcript;
          }
        }
        setTranscript(finalRef.current + interimTranscript);
      };

      recognition.onerror = () => setIsListening(false);
      recognition.onend = () => setIsListening(false);
      recognitionRef.current = recognition;
    }
  }, []);

  const startListening = useCallback(() => {
    if (recognitionRef.current) {
      finalRef.current = '';
      setTranscript('');
      try { recognitionRef.current.start(); } catch (_) {}
      setIsListening(true);
    }
  }, []);

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      setIsListening(false);
    }
  }, []);

  const resetTranscript = useCallback(() => {
    finalRef.current = '';
    setTranscript('');
  }, []);

  return { isListening, transcript, isSupported, startListening, stopListening, resetTranscript };
}

// ─── Temas ────────────────────────────────────────────────────────────────────
const THEMES = {
  day: {
    root:        'bg-white text-slate-800',
    header:      'bg-white border-b border-slate-200',
    sidebar:     'bg-slate-50 border-r border-slate-200',
    sidebarLabel:'text-slate-400',
    sidebarSect: 'text-slate-500',
    input:       'bg-white border border-slate-300 text-slate-800 placeholder-slate-400 focus:border-amber-500',
    select:      'bg-white border border-slate-300 text-slate-800 focus:border-amber-500',
    tabBar:      'bg-slate-50 border-b border-slate-200',
    tabActive:   'bg-amber-600 text-white',
    tabInactive: 'text-slate-500 hover:text-slate-800 hover:bg-slate-200',
    card:        'bg-white border border-slate-200',
    cardBorder:  'border-slate-200',
    pre:         'bg-slate-50 border border-slate-200 text-slate-700',
    micIdle:     'bg-slate-100 border border-slate-300 text-slate-500 hover:bg-amber-50 hover:text-amber-600 hover:border-amber-400',
    transcBg:    'bg-emerald-50 border border-emerald-200',
    transcText:  'text-emerald-700',
    transcLabel: 'text-emerald-600',
    statusLoad:  'bg-amber-50 text-amber-700 border border-amber-200',
    statusOk:    'bg-emerald-50 text-emerald-700 border border-emerald-200',
    statusErr:   'bg-red-50 text-red-700 border border-red-200',
    editBox:     'bg-slate-50 border border-slate-200',
    editLabel:   'text-amber-600',
    uploadBorder:'border-slate-300 hover:border-amber-400',
    uploadText:  'text-slate-400',
    dlBtn:       'bg-slate-100 border border-slate-200 text-slate-600 hover:bg-slate-200',
    presBtn:     'bg-amber-50 border border-amber-300 text-amber-700 hover:bg-amber-100',
    subtext:     'text-slate-500',
    code:        'text-amber-600 bg-amber-50',
    motorText:   'text-slate-400',
    title:       'text-slate-800',
    styleBtn:    'bg-slate-100 border border-slate-200 text-slate-600 hover:bg-amber-50 hover:border-amber-400 hover:text-amber-700',
    styleBtnAct: 'bg-amber-600 border border-amber-600 text-white',
    instCard:    'bg-slate-50 border border-slate-200',
    instBadge:   'bg-slate-200 text-slate-600',
    instElec:    'bg-yellow-50 border border-yellow-200 text-yellow-700',
    instWater:   'bg-blue-50 border border-blue-200 text-blue-700',
    instGas:     'bg-orange-50 border border-orange-200 text-orange-700',
    sectionBg:   'bg-slate-50 border border-slate-200',
  },
  night: {
    root:        'bg-[#0F0F0F] text-white',
    header:      'bg-[#111] border-b border-white/5',
    sidebar:     'bg-[#111] border-r border-white/5',
    sidebarLabel:'text-slate-600',
    sidebarSect: 'text-slate-600',
    input:       'bg-white/5 border border-white/10 text-white placeholder-slate-700 focus:border-amber-500/50',
    select:      'bg-[#1A1A1A] border border-white/10 text-white focus:border-amber-500/50',
    tabBar:      'bg-[#111] border-b border-white/5',
    tabActive:   'bg-amber-600 text-white',
    tabInactive: 'text-slate-500 hover:text-white hover:bg-white/5',
    card:        'bg-white/5 border border-white/10',
    cardBorder:  'border-white/10',
    pre:         'bg-white/5 border border-white/10 text-slate-300',
    micIdle:     'bg-white/5 border border-white/10 text-slate-400 hover:bg-amber-600/20 hover:text-amber-400 hover:border-amber-500/30',
    transcBg:    'bg-emerald-500/10 border border-emerald-500/20',
    transcText:  'text-slate-400',
    transcLabel: 'text-emerald-400',
    statusLoad:  'bg-amber-500/10 text-amber-400 border border-amber-500/20',
    statusOk:    'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20',
    statusErr:   'bg-red-500/10 text-red-400 border border-red-500/20',
    editBox:     'bg-white/5 border border-white/10',
    editLabel:   'text-amber-400',
    uploadBorder:'border-white/10 hover:border-amber-500/40',
    uploadText:  'text-slate-500',
    dlBtn:       'bg-black/70 border border-white/10 text-slate-300 hover:bg-black',
    presBtn:     'bg-amber-600/20 border border-amber-500/30 text-amber-400 hover:bg-amber-600/30',
    subtext:     'text-slate-500',
    code:        'text-amber-400 bg-amber-500/10',
    motorText:   'text-slate-600',
    title:       'text-white',
    styleBtn:    'bg-white/5 border border-white/10 text-slate-400 hover:bg-amber-600/20 hover:border-amber-500/30 hover:text-amber-400',
    styleBtnAct: 'bg-amber-600 border border-amber-600 text-white',
    instCard:    'bg-white/5 border border-white/10',
    instBadge:   'bg-white/10 text-slate-400',
    instElec:    'bg-yellow-500/10 border border-yellow-500/20 text-yellow-400',
    instWater:   'bg-blue-500/10 border border-blue-500/20 text-blue-400',
    instGas:     'bg-orange-500/10 border border-orange-500/20 text-orange-400',
    sectionBg:   'bg-white/5 border border-white/10',
  },
};

// ─── Estilos rápidos con prompts calibrados ───────────────────────────────────
const ESTILOS_RAPIDOS = [
  { id: 'nordico', label: 'Nórdico', emoji: '🌿', estilo: 'Nórdico', descripcion: 'Cocina nórdica escandinava con muebles de madera de roble natural, frentes lisos sin tiradores en blanco roto, encimera de cuarzo blanco con vetas sutiles, suelo de madera clara, paredes blancas, iluminación cálida empotrada y plantas aromáticas en la ventana. Ambiente minimalista y acogedor.', notas: 'Frentes: lacado blanco roto mate. Encimera: cuarzo blanco Silestone. Tiradores: push-to-open. Suelo: roble natural.' },
  { id: 'industrial', label: 'Industrial', emoji: '⚙️', estilo: 'Industrial', descripcion: 'Cocina industrial urbana con muebles de acero inoxidable cepillado, frentes de madera oscura de nogal, encimera de cemento pulido gris, suelo de microcemento, iluminación con focos de riel negro mate, baldosas de metro blancas en el frente, tuberías vistas y detalles en hierro negro.', notas: 'Frentes: madera nogal oscuro. Encimera: cemento pulido. Tiradores: barra acero inox. Grifo: industrial negro.' },
  { id: 'clasico', label: 'Clásico', emoji: '🏛️', estilo: 'Clásico', descripcion: 'Cocina clásica elegante con muebles de madera pintada en blanco perla con molduras y paneles decorativos, encimera de mármol Carrara con vetas grises, suelo de baldosa hidráulica, campana decorativa de madera lacada, cristaleras en muebles superiores, tiradores de latón dorado envejecido.', notas: 'Frentes: lacado blanco perla con molduras. Encimera: mármol Carrara. Tiradores: latón dorado. Campana: decorativa madera.' },
  { id: 'lacado_blanco', label: 'Lacado Blanco', emoji: '⬜', estilo: 'Minimalista', descripcion: 'Cocina minimalista de alto brillo con frentes lacados en blanco brillante, encimera de Dekton blanco ultra-compacto, suelo porcelánico de gran formato gris claro, sin tiradores con apertura push, electrodomésticos integrados y ocultos, iluminación LED lineal bajo muebles superiores.', notas: 'Frentes: lacado blanco alto brillo. Encimera: Dekton Zenith. Sin tiradores. Electrodomésticos: integrados.' },
  { id: 'madera_natural', label: 'Madera Natural', emoji: '🪵', estilo: 'Rústico', descripcion: 'Cocina de madera natural con frentes de roble macizo veteado, encimera de madera de teca aceitada, suelo de barro cocido, vigas de madera en el techo, campana de obra revestida en piedra natural, iluminación cálida con lámparas de forja, estantes abiertos de madera flotante.', notas: 'Frentes: roble macizo natural. Encimera: teca aceitada. Suelo: barro cocido. Campana: piedra natural.' },
  { id: 'contemporaneo', label: 'Contemporáneo', emoji: '✨', estilo: 'Contemporáneo', descripcion: 'Cocina contemporánea de diseño con combinación de frentes en grafito mate y madera de fresno, encimera de cuarzo negro con vetas doradas, isla central con barra de desayuno, iluminación colgante de diseño sobre la isla, suelo de porcelánico imitación piedra, grifo de cuello alto negro mate.', notas: 'Frentes: grafito mate + fresno natural. Encimera: cuarzo negro Silestone. Isla: con barra. Grifo: negro mate cuello alto.' },
  { id: 'japandi', label: 'Japandi', emoji: '🎍', estilo: 'Japandi', descripcion: 'Cocina Japandi que fusiona minimalismo japonés con calidez escandinava. Frentes lisos de madera de fresno claro con acabado natural, encimera de piedra caliza beige pulida, suelo de madera de bambú, paredes en blanco cálido, estantes abiertos de madera con cerámica artesanal, iluminación difusa con lámparas de papel washi, líneas puras sin ornamentación.', notas: 'Frentes: fresno claro natural. Encimera: piedra caliza beige. Tiradores: perfil integrado madera. Suelo: bambú. Estantes abiertos.' },
  { id: 'mediterraneo', label: 'Mediterráneo', emoji: '☀️', estilo: 'Mediterráneo', descripcion: 'Cocina mediterránea luminosa con muebles pintados en azul índigo deslavado, encimera de mármol blanco Macael, suelo de baldosa hidráulica con motivos geométricos en azul y blanco, paredes de estuco blanco texturizado, campana de obra encalada, estantes abiertos con cerámica artesanal, grifo de latón envejecido, ventana con contraventanas de madera.', notas: 'Frentes: lacado azul índigo mate. Encimera: mármol Macael. Suelo: hidráulico azul/blanco. Campana: obra encalada. Grifo: latón.' },
  { id: 'hightech', label: 'High-Tech', emoji: '🚀', estilo: 'High-Tech', descripcion: 'Cocina high-tech futurista con frentes de cristal ahumado negro retroiluminado, encimera de Dekton Kelya ultra-negro, isla con inducción invisible integrada en la superficie, suelo de resina epoxi gris antracita, iluminación LED RGB programable en zócalos y estantes, electrodomésticos con pantalla táctil integrada, grifo con sensor de movimiento.', notas: 'Frentes: cristal ahumado negro. Encimera: Dekton Kelya. Suelo: resina epoxi antracita. LED RGB. Electrodomésticos: pantalla táctil.' },
  { id: 'provenzal', label: 'Provenzal', emoji: '🌻', estilo: 'Provenzal', descripcion: 'Cocina provenzal francesa con muebles de madera pintada en verde salvia con pátina envejecida, encimera de piedra natural caliza con bordes redondeados, suelo de terracota hexagonal, campana de cobre martillado, fregadero cerámico tipo Belfast, estantes abiertos con cestas de mimbre, cortinas de lino natural en la ventana, tiradores de porcelana blanca.', notas: 'Frentes: madera pintada verde salvia patinado. Encimera: piedra caliza. Suelo: terracota. Campana: cobre. Fregadero: cerámico Belfast.' },
  { id: 'wabisabi', label: 'Wabi-Sabi', emoji: '🌊', estilo: 'Wabi-Sabi', descripcion: 'Cocina Wabi-Sabi que celebra la belleza de la imperfeción. Frentes de madera de cedro sin tratar con nudos visibles y veta irregular, encimera de hormigón pulido con bordes imperfectos, suelo de piedra natural irregular, paredes de arcilla cruda texturizada en tono arena, estantes de madera recuperada, cerámica artesanal hecha a mano, iluminación tenue con lámparas de fibra natural.', notas: 'Frentes: cedro sin tratar. Encimera: hormigón pulido artesanal. Suelo: piedra irregular. Paredes: arcilla cruda. Cerámica artesanal.' },
];

// ─── Distribuciones de cocina ─────────────────────────────────────────────────
const DISTRIBUCIONES = [
  { id: 'lineal', label: 'Lineal', icon: '━━━', paredes: 1, desc: 'Una sola pared' },
  { id: 'l', label: 'En L', icon: '┗━━', paredes: 2, desc: 'Dos paredes en esquina' },
  { id: 'u', label: 'En U', icon: '┗━┛', paredes: 3, desc: 'Tres paredes' },
  { id: 'paralela', label: 'Paralela', icon: '═══\n═══', paredes: 2, desc: 'Dos paredes enfrentadas' },
  { id: 'isla', label: 'Con Isla', icon: '━━━\n □', paredes: 1, desc: 'Pared + isla central' },
  { id: 'g', label: 'En G', icon: '┗━┓', paredes: 3, desc: 'Tres paredes + península' },
];

const ELEMENTOS_COCINA = [
  { id: 'fregadero', label: 'Fregadero', emoji: '🚰', ancho_default: 80 },
  { id: 'placa', label: 'Placa/Vitro', emoji: '🔥', ancho_default: 60 },
  { id: 'horno', label: 'Horno', emoji: '♨️', ancho_default: 60 },
  { id: 'frigorifico', label: 'Frigorífico', emoji: '🧊', ancho_default: 70 },
  { id: 'lavavajillas', label: 'Lavavajillas', emoji: '🫧', ancho_default: 60 },
  { id: 'campana', label: 'Campana', emoji: '💨', ancho_default: 60 },
  { id: 'microondas', label: 'Microondas', emoji: '📡', ancho_default: 60 },
  { id: 'columna_hornos', label: 'Col. Hornos', emoji: '🗄️', ancho_default: 60 },
];

function getSystemTheme() {
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'night' : 'day';
}

function getSavedThemeMode() {
  try { return localStorage.getItem('estudio3d_theme') || 'auto'; } catch { return 'auto'; }
}

// ─── Helper: llamada al backend ───────────────────────────────────────────────
function getToken() {
  try {
    return localStorage.getItem('luiggi_access_token')
      || localStorage.getItem('token')
      || localStorage.getItem('access_token')
      || sessionStorage.getItem('token')
      || '';
  } catch { return ''; }
}

async function apiPost(endpoint, body) {
  const res = await fetch(`${API}/api/estudio-cocinas${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${getToken()}` },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || `Error ${res.status}`);
  return data;
}

async function apiGet(endpoint) {
  const res = await fetch(`${API}/api/estudio-cocinas${endpoint}`, {
    headers: { Authorization: `Bearer ${getToken()}` },
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || `Error ${res.status}`);
  return data;
}

async function apiPostForm(endpoint, formData) {
  const res = await fetch(`${API}/api/estudio-cocinas${endpoint}`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${getToken()}` },
    body: formData,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || `Error ${res.status}`);
  return data;
}

/** Añade el token JWT como query param a URLs del proxy de assets (las <img> no envían cabeceras). */
function imgSrc(url) {
  if (!url) return '';
  if (url.startsWith('blob:')) return url;
  const t = getToken();
  let fullUrl = url;
  if (url.startsWith('/api/')) {
    fullUrl = `${API}${url}`;
  }
  if (!t) return fullUrl;
  return `${fullUrl}${fullUrl.includes('?') ? '&' : '?'}t=${encodeURIComponent(t)}`;
}

/** Descarga una imagen del proxy como blob URL para evitar problemas CORS en <img> */
async function fetchAsBlob(url) {
  try {
    const fullUrl = imgSrc(url);
    if (!fullUrl) return null;
    const resp = await fetch(fullUrl);
    if (!resp.ok) return null;
    const blob = await resp.blob();
    return URL.createObjectURL(blob);
  } catch {
    return null;
  }
}

/** Convierte una imagen (proxy URL o blob) a dataURL para guardar/PDF */
async function imageToDataUrl(url) {
  if (!url) return null;
  if (typeof url === 'string' && url.startsWith('data:')) return url;
  const fullUrl = imgSrc(url);
  const resp = await fetch(fullUrl);
  const blob = await resp.blob();
  return await new Promise((res, rej) => {
    const fr = new FileReader();
    fr.onload = () => res(fr.result);
    fr.onerror = rej;
    fr.readAsDataURL(blob);
  });
}

// ─── Badge de estado ──────────────────────────────────────────────────────────
function StatusBadge({ status, message, t }) {
  if (!message) return null;
  const cls = status === 'success' ? t.statusOk : status === 'error' ? t.statusErr : t.statusLoad;
  const icon = status === 'success'
    ? <CheckCircle size={13} className="flex-shrink-0" />
    : status === 'error'
    ? <AlertCircle size={13} className="flex-shrink-0" />
    : <Loader2 size={13} className="animate-spin flex-shrink-0" />;
  return (
    <div className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium ${cls}`}>
      {icon} {message}
    </div>
  );
}

// ─── Selector de tema ─────────────────────────────────────────────────────────
function ThemeSelector({ mode, onChange, t }) {
  const opts = [
    { id: 'day',   icon: <Sun size={13}/>,     label: 'Día' },
    { id: 'night', icon: <Moon size={13}/>,    label: 'Noche' },
    { id: 'auto',  icon: <Monitor size={13}/>, label: 'Auto' },
  ];
  return (
    <div className={`flex items-center gap-0.5 rounded-lg p-0.5 ${t.card}`}>
      {opts.map(o => (
        <button
          key={o.id}
          onClick={() => onChange(o.id)}
          title={o.label}
          className={`flex items-center gap-1 px-2 py-1 rounded-md text-[10px] font-black uppercase tracking-widest transition-all ${
            mode === o.id ? 'bg-amber-600 text-white' : `${t.tabInactive}`
          }`}
        >
          {o.icon} <span className="hidden sm:inline">{o.label}</span>
        </button>
      ))}
    </div>
  );
}

// ─── Botones de impresión / PDF ───────────────────────────────────────────────
function PrintPdfBar({ onPrint, onPdf, t, extraBtns }) {
  return (
    <div className="flex items-center gap-2 flex-wrap">
      <button onClick={onPrint} className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all ${t.dlBtn}`}>
        <Printer size={11}/> Imprimir
      </button>
      <button onClick={onPdf} className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all ${t.presBtn}`}>
        <Download size={11}/> Exportar PDF
      </button>
      {extraBtns}
    </div>
  );
}

// ─── Componente principal ─────────────────────────────────────────────────────
export default function EstudioCocinas({ state, setState }) {
  const [tab, setTab] = useState('render');
  const [themeMode, setThemeMode] = useState(getSavedThemeMode);
  const [systemTheme, setSystemTheme] = useState(getSystemTheme);

  useEffect(() => {
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = e => setSystemTheme(e.matches ? 'night' : 'day');
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, []);

  const handleThemeChange = useCallback(mode => {
    setThemeMode(mode);
    try { localStorage.setItem('estudio3d_theme', mode); } catch {}
  }, []);

  const activeTheme = themeMode === 'auto' ? systemTheme : themeMode;
  const t = THEMES[activeTheme];

  const [proy, setProy] = useState({
    nombre_cliente: '',
    descripcion: '',
    estilo: 'Moderno',
    medidas: '400x350cm isla 200x100cm',
    presupuesto: '',
    notas: '',
  });

  const [selectedStyle, setSelectedStyle] = useState(null);

  // ── Orden del sidebar (drag & drop, persistido en localStorage) ──
  const DEFAULT_SIDEBAR_ORDER = ['cliente', 'presupuesto', 'medidas', 'distribucion', 'estilo', 'descripcion', 'notas'];
  const [sidebarOrder, setSidebarOrder] = useState(() => {
    try {
      const saved = localStorage.getItem('estudio_sidebar_order');
      if (saved) { const arr = JSON.parse(saved); if (Array.isArray(arr) && arr.length === 7) return arr; }
    } catch(e) {}
    return DEFAULT_SIDEBAR_ORDER;
  });
  const [dragField, setDragField] = useState(null);

  // ── Distribución estructurada (null = modo texto libre) ──
  const [distribucion, setDistribucion] = useState(null);

  const handleDistChange = useCallback((tipo) => {
    if (distribucion && distribucion.tipo === tipo) { setDistribucion(null); return; }
    let paredes = [];
    switch (tipo) {
      case 'lineal': paredes = [{ nombre: 'Pared principal', ancho: 400, alto: 240 }]; break;
      case 'l': paredes = [{ nombre: 'Pared larga', ancho: 400, alto: 240 }, { nombre: 'Pared corta', ancho: 250, alto: 240 }]; break;
      case 'u': paredes = [{ nombre: 'Pared izquierda', ancho: 250, alto: 240 }, { nombre: 'Pared fondo', ancho: 400, alto: 240 }, { nombre: 'Pared derecha', ancho: 250, alto: 240 }]; break;
      case 'paralela': paredes = [{ nombre: 'Pared norte', ancho: 400, alto: 240 }, { nombre: 'Pared sur', ancho: 400, alto: 240 }]; break;
      case 'isla': paredes = [{ nombre: 'Pared principal', ancho: 400, alto: 240 }]; break;
      case 'g': paredes = [{ nombre: 'Pared izquierda', ancho: 250, alto: 240 }, { nombre: 'Pared fondo', ancho: 400, alto: 240 }, { nombre: 'Pared derecha', ancho: 200, alto: 240 }]; break;
      default: paredes = [{ nombre: 'Pared principal', ancho: 400, alto: 240 }];
    }
    const isla = (tipo === 'isla') ? { ancho: 120, largo: 200 } : { ancho: 0, largo: 0 };
    setDistribucion({ tipo, paredes, isla, elementos: [] });
    const medStr = paredes.map(p => `${p.nombre}: ${p.ancho}cm`).join(' | ') + (isla.ancho > 0 ? ` | Isla: ${isla.ancho}x${isla.largo}cm` : '');
    setProy(p => ({ ...p, medidas: medStr }));
  }, [distribucion]);

  const updatePared = useCallback((idx, field, value) => {
    setDistribucion(d => {
      const paredes = [...d.paredes];
      paredes[idx] = { ...paredes[idx], [field]: parseInt(value) || 0 };
      const medStr = paredes.map(p => `${p.nombre}: ${p.ancho}cm`).join(' | ') + (d.isla.ancho > 0 ? ` | Isla: ${d.isla.ancho}x${d.isla.largo}cm` : '');
      setProy(p => ({ ...p, medidas: medStr }));
      return { ...d, paredes };
    });
  }, []);

  const updateIsla = useCallback((field, value) => {
    setDistribucion(d => {
      const isla = { ...d.isla, [field]: parseInt(value) || 0 };
      const medStr = d.paredes.map(p => `${p.nombre}: ${p.ancho}cm`).join(' | ') + (isla.ancho > 0 ? ` | Isla: ${isla.ancho}x${isla.largo}cm` : '');
      setProy(p => ({ ...p, medidas: medStr }));
      return { ...d, isla };
    });
  }, []);

  const addElemento = useCallback((elemId, paredIdx) => {
    const elem = ELEMENTOS_COCINA.find(e => e.id === elemId);
    if (!elem) return;
    setDistribucion(d => ({
      ...d,
      elementos: [...d.elementos, { id: elemId, label: elem.label, emoji: elem.emoji, pared_idx: paredIdx, ancho: elem.ancho_default }]
    }));
  }, []);

  const removeElemento = useCallback((idx) => {
    setDistribucion(d => ({ ...d, elementos: d.elementos.filter((_, i) => i !== idx) }));
  }, []);

  const [render, setRender] = useState({ status: null, msg: '', imageUrl: null, originalUrl: null, croquis: null, croquisPrev: null, editMode: false, editTxt: '', fs: false });
  const [freeDesign, setFreeDesign] = useState(false);
  const [plano,  setPlano]  = useState({ status: null, msg: '', b64: null, fs: false });
  const [ficha,  setFicha]  = useState({ status: null, msg: '', md: '', ref: '' });
  const [pres,   setPres]   = useState({ status: null, msg: '', html: '', preview: false });
  const [inst,   setInst]   = useState({ status: null, msg: '', data: null });
  const [rec,    setRec]    = useState(false);
  const [transcrito, setTranscrito] = useState('');
  const [galeria, setGaleria] = useState({ renders: [], total: 0, page: 1, loading: false, fsImg: null });

  // ── Marca de agua ──
  const [watermark, setWatermark] = useState({ mode: 'default', customLogo: null, customLogoPreview: null });
  const watermarkInputRef = useRef(null);
  const defaultLogo = state?.logo || null;

  // ── Nuevas funcionalidades migradas ──
  const [attached, setAttached] = useState(false);       // Adjuntado al presupuesto
  const [compareOn, setCompareOn] = useState(false);     // Comparativa croquis vs render
  const [savedId, setSavedId] = useState(null);          // ID del proyecto guardado
  const [savedList, setSavedList] = useState(null);      // Lista de proyectos (null = modal oculto)
  const [busySave, setBusySave] = useState(false);       // Guardando proyecto

  // ── Web Speech API (voz que se añade al texto) ──
  const { isListening, transcript: speechTranscript, isSupported: speechSupported, startListening, stopListening } = useSpeechRecognition();
  const baseTextRef = useRef('');

  // Cuando la transcripción cambia, se AÑADE al texto de descripción (no lo pisa)
  useEffect(() => {
    if (speechTranscript) {
      const base = baseTextRef.current;
      setProy(p => ({ ...p, descripcion: base ? `${base.trim()} ${speechTranscript}` : speechTranscript }));
    }
  }, [speechTranscript]);

  const handleCustomLogoUpload = useCallback((e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      setWatermark(w => ({ ...w, mode: 'custom', customLogo: ev.target.result, customLogoPreview: ev.target.result }));
    };
    reader.readAsDataURL(file);
  }, []);

  /** Aplica marca de agua a una imagen (blob URL o data URL) y devuelve un nuevo blob URL */
  const applyWatermark = useCallback(async (imgUrl) => {
    if (watermark.mode === 'none') return imgUrl;
    const logoSrc = watermark.mode === 'custom' ? watermark.customLogo : defaultLogo;
    if (!logoSrc) return imgUrl;

    return new Promise((resolve) => {
      const img = new window.Image();
      img.crossOrigin = 'anonymous';
      img.onload = () => {
        const canvas = document.createElement('canvas');
        canvas.width = img.naturalWidth;
        canvas.height = img.naturalHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0);
        const logo = new window.Image();
        logo.crossOrigin = 'anonymous';
        logo.onload = () => {
          const logoW = Math.round(canvas.width * 0.15);
          const logoH = Math.round(logoW * (logo.naturalHeight / logo.naturalWidth));
          const padding = Math.round(canvas.width * 0.02);
          const x = canvas.width - logoW - padding;
          const y = canvas.height - logoH - padding;
          ctx.fillStyle = 'rgba(255,255,255,0.7)';
          ctx.roundRect(x - 8, y - 8, logoW + 16, logoH + 16, 8);
          ctx.fill();
          ctx.globalAlpha = 0.85;
          ctx.drawImage(logo, x, y, logoW, logoH);
          ctx.globalAlpha = 1.0;
          canvas.toBlob((blob) => {
            resolve(blob ? URL.createObjectURL(blob) : imgUrl);
          }, 'image/png');
        };
        logo.onerror = () => resolve(imgUrl);
        logo.src = logoSrc;
      };
      img.onerror = () => resolve(imgUrl);
      img.src = imgUrl;
    });
  }, [watermark.mode, watermark.customLogo, defaultLogo]);

  const downloadWithWatermark = useCallback(async () => {
    if (!render.imageUrl) return;
    const finalUrl = await applyWatermark(render.imageUrl);
    const a = document.createElement('a');
    a.href = finalUrl;
    a.download = `render_${proy.nombre_cliente || 'cocina'}.png`;
    a.click();
  }, [render.imageUrl, applyWatermark, proy.nombre_cliente]);

  const mrRef     = useRef(null);
  const chunksRef = useRef([]);
  const croquisRef = useRef(null);
  const printRef  = useRef(null);

  // ── Galería de renders ──
  const loadGaleria = useCallback(async (page = 1) => {
    setGaleria(g => ({ ...g, loading: true }));
    try {
      const data = await apiGet(`/galeria?page=${page}&limit=12`);
      setGaleria(g => ({ ...g, renders: data.renders || [], total: data.total || 0, page: data.page || 1, loading: false }));
    } catch {
      setGaleria(g => ({ ...g, loading: false }));
    }
  }, []);

  const guardarEnGaleria = useCallback(async () => {
    if (!render.imageUrl) return;
    try {
      await apiPost('/galeria/guardar', {
        image_url: render.originalUrl || render.imageUrl,
        cliente: proy.nombre_cliente,
        descripcion: proy.descripcion,
        estilo: proy.estilo,
        medidas: proy.medidas,
        presupuesto: proy.presupuesto,
      });
      setRender(s => ({ ...s, status: 'success', msg: 'Render guardado en galería' }));
    } catch (err) {
      setRender(s => ({ ...s, status: 'error', msg: err.message }));
    }
  }, [render.imageUrl, render.originalUrl, proy]);

  const toggleFavorito = useCallback(async (id) => {
    try {
      const res = await fetch(`${API}/api/estudio-cocinas/galeria/${id}/favorito`, {
        method: 'PATCH', headers: { Authorization: `Bearer ${getToken()}` },
      });
      if (res.ok) loadGaleria(galeria.page);
    } catch {}
  }, [galeria.page, loadGaleria]);

  const eliminarRender = useCallback(async (id) => {
    if (!window.confirm('¿Eliminar este render de la galería?')) return;
    try {
      const res = await fetch(`${API}/api/estudio-cocinas/galeria/${id}`, {
        method: 'DELETE', headers: { Authorization: `Bearer ${getToken()}` },
      });
      if (res.ok) loadGaleria(galeria.page);
    } catch {}
  }, [galeria.page, loadGaleria]);

  useEffect(() => {
    if (tab === 'galeria') loadGaleria(1);
  }, [tab, loadGaleria]);

  // ── Estilo rápido ──
  const applyStyle = useCallback(style => {
    setSelectedStyle(style.id);
    setProy(p => ({
      ...p,
      estilo: style.estilo,
      notas: style.notas,
      // Con croquis subido, el estilo solo aporta acabado/materiales: NO se pisa la
      // descripción (que puede llevar tu diseño) para no alterar la distribución.
      descripcion: render.croquis ? p.descripcion : style.descripcion,
    }));
  }, [render.croquis]);

  // ── Croquis ──
  const onCroquis = useCallback(e => {
    const f = e.target.files?.[0];
    if (!f) return;
    const fr = new FileReader();
    fr.onload = ev => setRender(s => ({ ...s, croquis: ev.target.result, croquisPrev: ev.target.result }));
    fr.readAsDataURL(f);
  }, []);

  // ── Voz (grabación de audio para transcripción backend) ──
  const startRec = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream);
      chunksRef.current = [];
      mr.ondataavailable = e => chunksRef.current.push(e.data);
      mr.onstop = async () => {
        stream.getTracks().forEach(t => t.stop());
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        const fd = new FormData();
        fd.append('audio', blob, 'nota.webm');
        setRender(s => ({ ...s, status: 'loading', msg: 'Transcribiendo audio…' }));
        try {
          const r = await apiPostForm('/transcribir', fd);
          setTranscrito(r.texto || '');
          setProy(p => ({ ...p, descripcion: p.descripcion ? `${p.descripcion} ${r.texto || ''}` : (r.texto || '') }));
          setRender(s => ({ ...s, status: 'success', msg: 'Audio transcrito' }));
        } catch (err) {
          setRender(s => ({ ...s, status: 'error', msg: err.message }));
        }
      };
      mr.start();
      mrRef.current = mr;
      setRec(true);
    } catch {
      setRender(s => ({ ...s, status: 'error', msg: 'No se pudo acceder al micrófono' }));
    }
  }, []);

  const stopRec = useCallback(() => { mrRef.current?.stop(); setRec(false); }, []);

  // ── Render (modo asíncrono con polling) ──
  const genRender = useCallback(async () => {
    if (!proy.descripcion.trim()) {
      setRender(s => ({ ...s, status: 'error', msg: 'Escribe o dicta una descripción' }));
      return;
    }
    setRender(s => ({ ...s, status: 'loading', msg: 'Generando render… puede tardar 1-3 minutos', imageUrl: null }));
    try {
      // Con croquis, quitamos del texto de materiales/descripción los fragmentos que
      // meten distribución (isla, ventana…) para que NO alteren el diseño del croquis,
      // y no enviamos medidas/distribución (que también pueden llevar "isla").
      const stripLayout = (t) => String(t || '')
        .split(/[.·|;]/).map(s => s.trim())
        .filter(s => s && !/^(isla|island|ventanal?|window)\b/i.test(s))
        .join('. ');
      const conCroquis = !!render.croquis && !freeDesign;
      const r = await apiPost('/render', {
        descripcion: conCroquis ? stripLayout(proy.descripcion) : proy.descripcion,
        estilo: proy.estilo,
        materiales: conCroquis ? stripLayout(proy.notas) : proy.notas,
        distribucion: conCroquis ? '' : proy.medidas,
        distribucion_estructurada: conCroquis ? null : distribucion,
        croquis_b64: render.croquis || null,
        modo_async: true,
        free_design: freeDesign,
      });

      // Motor Gemini (IA 1): la imagen vuelve directa (data URL), sin tarea que sondear.
      if (r.imageUrl && !r.task_id) {
        const u = r.imageUrl;
        const shown = String(u).startsWith('data:') ? u : ((await fetchAsBlob(u)) || imgSrc(u));
        setRender(s => ({ ...s, status: 'success', msg: 'Render generado correctamente', imageUrl: shown, originalUrl: u }));
        return;
      }

      if (!r.task_id) throw new Error(r.error || 'No se pudo iniciar el render');

      const taskId = r.task_id;
      const maxAttempts = 38;
      let attempts = 0;
      const poll = async () => {
        attempts++;
        if (attempts > maxAttempts) {
          setRender(s => ({ ...s, status: 'error', msg: 'El render tardó demasiado. Inténtalo de nuevo.' }));
          return;
        }
        try {
          const estado = await apiGet(`/tarea/${taskId}`);
          if (estado.status === 'stopped') {
            const resultado = await apiGet(`/tarea/${taskId}/resultado`);
            const originalProxyUrl = resultado.imageUrl;
            const blobUrl = await fetchAsBlob(originalProxyUrl);
            setRender(s => ({ ...s, status: 'success', msg: 'Render generado correctamente', imageUrl: blobUrl || imgSrc(originalProxyUrl), originalUrl: originalProxyUrl }));
          } else if (estado.status === 'error') {
            setRender(s => ({ ...s, status: 'error', msg: estado.error || 'Error al generar el render' }));
          } else {
            setTimeout(poll, 8000);
          }
        } catch (pollErr) {
          setTimeout(poll, 8000);
        }
      };
      setTimeout(poll, 8000);
    } catch (err) {
      setRender(s => ({ ...s, status: 'error', msg: err.message }));
    }
  }, [proy, render.croquis, freeDesign, distribucion]);

  const editRender = useCallback(async () => {
    if (!render.editTxt.trim()) return;
    setRender(s => ({ ...s, status: 'loading', msg: 'Editando render…' }));
    try {
      // Enviar la imagen actual en base64 para que el motor la "vea" y edite
      // manteniendo la coherencia (antes solo mandaba una URL que no podía descargar).
      const prevB64 = await imageToDataUrl(render.imageUrl).catch(() => null);
      const r = await apiPost('/render/editar', {
        render_b64: prevB64 || undefined,
        render_url: render.originalUrl || render.imageUrl,
        instruccion: render.editTxt,
        modo_async: false,
      });
      const blobUrl = await fetchAsBlob(r.imageUrl);
      setRender(s => ({ ...s, status: 'success', msg: 'Render editado', imageUrl: blobUrl || imgSrc(r.imageUrl), originalUrl: r.imageUrl, editMode: false, editTxt: '' }));
    } catch (err) {
      setRender(s => ({ ...s, status: 'error', msg: err.message }));
    }
  }, [render.imageUrl, render.originalUrl, render.editTxt]);

  // ── MIGRADO: Adjuntar render al presupuesto ──
  const attachToBudget = useCallback(async () => {
    if (!render.imageUrl) return;
    try {
      const dataUrl = await imageToDataUrl(render.imageUrl);
      localStorage.setItem('render3d_attach', JSON.stringify({
        image: dataUrl,
        cliente: proy.nombre_cliente,
        ref: `${proy.estilo} - ${proy.medidas}`,
        ts: Date.now()
      }));
      setAttached(true);
      setTimeout(() => setAttached(false), 4000);
      setRender(s => ({ ...s, status: 'success', msg: 'Render adjuntado al presupuesto' }));
    } catch (err) {
      setRender(s => ({ ...s, status: 'error', msg: 'No se pudo adjuntar el render' }));
    }
  }, [render.imageUrl, proy]);

  // ── MIGRADO: Guardar proyecto en MongoDB ──
  const saveProject = useCallback(async () => {
    if (!render.imageUrl && !proy.descripcion.trim()) {
      setRender(s => ({ ...s, status: 'error', msg: 'No hay datos para guardar' }));
      return;
    }
    setBusySave(true);
    try {
      const images = render.originalUrl ? [render.originalUrl] : [];
      const res = await fetch(`${API}/api/ai-engine/designs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${getToken()}` },
        body: JSON.stringify({
          id: savedId || undefined,
          cliente: proy.nombre_cliente,
          ref: `${proy.estilo} - ${proy.medidas}`,
          description: proy.descripcion,
          style: proy.estilo,
          images,
        }),
      });
      const d = await res.json();
      if (d.success) {
        setSavedId(d.design.id);
        setRender(s => ({ ...s, status: 'success', msg: 'Proyecto guardado correctamente' }));
      } else {
        setRender(s => ({ ...s, status: 'error', msg: d.error || 'No se pudo guardar' }));
      }
    } catch (err) {
      setRender(s => ({ ...s, status: 'error', msg: 'Error al guardar el proyecto' }));
    }
    setBusySave(false);
  }, [render.imageUrl, render.originalUrl, proy, savedId]);

  // ── MIGRADO: Abrir lista de proyectos ──
  const openProjectList = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/ai-engine/designs`, {
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      const d = await res.json();
      setSavedList(d.designs || []);
    } catch {
      setRender(s => ({ ...s, status: 'error', msg: 'No se pudo cargar la lista de proyectos' }));
    }
  }, []);

  const loadProject = useCallback((dsg) => {
    setProy(p => ({
      ...p,
      nombre_cliente: dsg.cliente || '',
      descripcion: dsg.description || '',
      estilo: dsg.style || 'Moderno',
    }));
    setSavedId(dsg.id);
    setSavedList(null);
    if (dsg.images?.[0]) {
      fetchAsBlob(dsg.images[0]).then(blobUrl => {
        setRender(s => ({ ...s, imageUrl: blobUrl || imgSrc(dsg.images[0]), originalUrl: dsg.images[0], status: 'success', msg: 'Proyecto cargado' }));
      });
    }
  }, []);

  const deleteProject = useCallback(async (id) => {
    if (!window.confirm('¿Eliminar este proyecto guardado?')) return;
    try {
      await fetch(`${API}/api/ai-engine/designs/${id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      setSavedList(prev => (prev || []).filter(x => x.id !== id));
      if (savedId === id) setSavedId(null);
    } catch {}
  }, [savedId]);

  // ── Plano ──
  const genPlano = useCallback(async () => {
    if (!proy.medidas.trim()) { setPlano(s => ({ ...s, status: 'error', msg: 'Introduce las medidas' })); return; }
    setPlano(s => ({ ...s, status: 'loading', msg: 'Generando plano técnico…', b64: null }));
    try {
      const r = await apiPost('/plano-2d', { ...proy, distribucion_estructurada: distribucion });
      setPlano(s => ({ ...s, status: 'success', msg: 'Plano generado', b64: r.planoBase64 }));
    } catch (err) {
      setPlano(s => ({ ...s, status: 'error', msg: err.message }));
    }
  }, [proy, distribucion]);

  // ── Ficha ──
  const genFicha = useCallback(async () => {
    setFicha(s => ({ ...s, status: 'loading', msg: 'Generando ficha técnica…' }));
    try {
      const r = await apiPost('/ficha-tecnica', { ...proy, distribucion_estructurada: distribucion });
      setFicha(s => ({ ...s, status: 'success', msg: `Ficha generada · ${r.referencia}`, md: r.fichaMarkdown, ref: r.referencia }));
    } catch (err) {
      setFicha(s => ({ ...s, status: 'error', msg: err.message }));
    }
  }, [proy, distribucion]);

  // ── Presentación ──
  const genPres = useCallback(async () => {
    setPres(s => ({ ...s, status: 'loading', msg: 'Generando presentación…' }));
    try {
      const r = await apiPost('/presentacion', { ...proy, distribucion_estructurada: distribucion });
      setPres(s => ({ ...s, status: 'success', msg: 'Presentación lista', html: r.presentacionHtml }));
    } catch (err) {
      setPres(s => ({ ...s, status: 'error', msg: err.message }));
    }
  }, [proy, distribucion]);

  // ── Instalaciones ──
  const genInstalaciones = useCallback(async () => {
    setInst(s => ({ ...s, status: 'loading', msg: 'Generando plan de instalaciones…' }));
    try {
      const r = await apiPost('/instalaciones', {
        medidas: proy.medidas, descripcion: proy.descripcion, estilo: proy.estilo,
        nombre_cliente: proy.nombre_cliente, distribucion_estructurada: distribucion,
      });
      setInst(s => ({ ...s, status: 'success', msg: 'Plan de instalaciones generado', data: r }));
    } catch (err) {
      setInst(s => ({ ...s, status: 'error', msg: err.message }));
    }
  }, [proy, distribucion]);

  // ── Helpers ──
  const dl = (content, name, type) => {
    const a = Object.assign(document.createElement('a'), {
      href: URL.createObjectURL(new Blob([content], { type })), download: name,
    });
    a.click();
  };

  const handlePrint = useCallback((contentId) => {
    const el = document.getElementById(contentId);
    if (!el) { window.print(); return; }
    const w = window.open('', '_blank');
    w.document.write(`<html><head><title>3D Estudio - ${proy.nombre_cliente || 'Proyecto'}</title><style>body{font-family:sans-serif;padding:20px;color:#333}pre{white-space:pre-wrap;font-size:12px}img{max-width:100%}@media print{button{display:none}}</style></head><body>${el.innerHTML}</body></html>`);
    w.document.close(); w.print();
  }, [proy.nombre_cliente]);

  const handlePdfExport = useCallback((content, filename) => {
    const w = window.open('', '_blank');
    const isHtml = content && content.trim().startsWith('<');
    w.document.write(`<html><head><title>${filename}</title><style>body{font-family:sans-serif;padding:30px;color:#333;max-width:900px;margin:0 auto}pre{white-space:pre-wrap;font-size:12px;background:#f5f5f5;padding:15px;border-radius:8px}img{max-width:100%;border-radius:8px}h1,h2,h3{color:#b45309}@media print{button{display:none}}</style></head><body><h2 style="color:#b45309;margin-bottom:4px">3D Estudio — ${proy.nombre_cliente || 'Proyecto'}</h2><p style="color:#999;font-size:12px;margin-bottom:20px">${new Date().toLocaleDateString('es-ES')}</p>${isHtml ? content : `<pre>${content}</pre>`}<script>window.onload=()=>{window.print()}<\/script></body></html>`);
    w.document.close();
  }, [proy.nombre_cliente]);

  const TABS = [
    { id: 'render', label: 'Render 3D', icon: <Sparkles size={14}/> },
    { id: 'plano',  label: 'Plano 2D',     icon: <Image size={14}/> },
    { id: 'ficha',  label: 'Ficha Técnica', icon: <FileText size={14}/> },
    { id: 'pres',   label: 'Presentación',  icon: <Presentation size={14}/> },
    { id: 'inst',   label: 'Instalaciones', icon: <Zap size={14}/> },
    { id: 'galeria', label: 'Galería',     icon: <FolderOpen size={14}/> },
  ];

  const ESTILOS = ['Moderno', 'Nórdico', 'Minimalista', 'Industrial', 'Clásico', 'Rústico', 'Contemporáneo', 'Japandi', 'Mediterráneo', 'High-Tech', 'Provenzal', 'Wabi-Sabi'];

  return (
    <div className={`flex flex-col h-full overflow-hidden transition-colors duration-200 ${t.root}`}>

      {/* Header */}
      <div className={`flex items-center gap-3 px-6 py-3 flex-shrink-0 ${t.header}`}>
        <div className="p-2 rounded-xl bg-amber-600/20">
          <ChefHat size={18} className="text-amber-500" />
        </div>
        <div className="flex-1">
          <h1 className={`text-xs font-black uppercase tracking-widest ${t.title}`}>3D Estudio</h1>
        </div>
        {/* Botones de proyecto */}
        <div className="flex items-center gap-1.5">
          <button onClick={openProjectList} title="Abrir proyecto" className={`flex items-center gap-1 px-2 py-1.5 rounded-lg text-[9px] font-black uppercase tracking-widest transition-all ${t.dlBtn}`}>
            <FolderOpen size={12}/> <span className="hidden md:inline">Proyectos</span>
          </button>
          <button onClick={saveProject} disabled={busySave} title="Guardar proyecto" className={`flex items-center gap-1 px-2 py-1.5 rounded-lg text-[9px] font-black uppercase tracking-widest transition-all ${savedId ? 'bg-emerald-600 text-white' : t.dlBtn}`}>
            {busySave ? <Loader2 size={12} className="animate-spin"/> : <Save size={12}/>} <span className="hidden md:inline">{savedId ? 'Guardado' : 'Guardar'}</span>
          </button>
          <button onClick={() => { setProy({ nombre_cliente: '', descripcion: '', estilo: 'Moderno', medidas: '400x350cm isla 200x100cm', presupuesto: '', notas: '' }); setSavedId(null); setRender({ status: null, msg: '', imageUrl: null, originalUrl: null, croquis: null, croquisPrev: null, editMode: false, editTxt: '', fs: false }); setDistribucion(null); setSelectedStyle(null); }} title="Nuevo proyecto" className={`flex items-center gap-1 px-2 py-1.5 rounded-lg text-[9px] font-black uppercase tracking-widest transition-all ${t.dlBtn}`}>
            <Plus size={12}/> <span className="hidden md:inline">Nuevo</span>
          </button>
        </div>
        <ThemeSelector mode={themeMode} onChange={handleThemeChange} t={t} />
      </div>

      <div className="flex flex-1 overflow-hidden min-h-0">

        {/* Sidebar */}
        <div className={`w-56 flex-shrink-0 p-4 flex flex-col gap-3 overflow-y-auto scrollbar-thin transition-colors duration-200 ${t.sidebar}`} style={{overflowY:'auto', overflowX:'hidden'}}>
          <p className={`text-[9px] font-black uppercase tracking-widest ${t.sidebarSect}`}>Proyecto</p>

          {/* Campos reordenables */}
          {sidebarOrder.map((fieldId) => {
            const dragHandleProps = {
              draggable: true,
              onDragStart: (e) => { e.dataTransfer.setData('text/plain', fieldId); setDragField(fieldId); },
              onDragEnd: () => setDragField(null),
              onDragOver: (e) => { e.preventDefault(); },
              onDrop: (e) => {
                e.preventDefault();
                const from = e.dataTransfer.getData('text/plain');
                if (from === fieldId) return;
                setSidebarOrder(prev => {
                  const arr = [...prev];
                  const fi = arr.indexOf(from), ti = arr.indexOf(fieldId);
                  arr.splice(fi, 1); arr.splice(ti, 0, from);
                  localStorage.setItem('estudio_sidebar_order', JSON.stringify(arr));
                  return arr;
                });
                setDragField(null);
              },
            };
            const dragStyle = dragField === fieldId ? { opacity: 0.4 } : {};
            const handleClass = `cursor-grab active:cursor-grabbing text-[8px] ${t.sidebarLabel} select-none`;

            switch (fieldId) {
              case 'cliente':
                return <div key={fieldId} {...dragHandleProps} style={dragStyle}>
                  <label className={`text-[9px] uppercase tracking-wider font-bold ${t.sidebarLabel}`}><span className={handleClass}>≡ </span>Cliente</label>
                  <input className={`w-full mt-1 rounded-lg px-2 py-1.5 text-xs focus:outline-none transition-colors duration-200 ${t.input}`}
                    placeholder="Nombre del cliente" value={proy.nombre_cliente}
                    onChange={e => setProy(p => ({ ...p, nombre_cliente: e.target.value }))} />
                </div>;
              case 'presupuesto':
                return <div key={fieldId} {...dragHandleProps} style={dragStyle}>
                  <label className={`text-[9px] uppercase tracking-wider font-bold ${t.sidebarLabel}`}><span className={handleClass}>≡ </span>Presupuesto</label>
                  <input className={`w-full mt-1 rounded-lg px-2 py-1.5 text-xs focus:outline-none transition-colors duration-200 ${t.input}`}
                    placeholder="Ej: 18.000€" value={proy.presupuesto}
                    onChange={e => setProy(p => ({ ...p, presupuesto: e.target.value }))} />
                </div>;
              case 'medidas':
                return <div key={fieldId} {...dragHandleProps} style={dragStyle}>
                  <label className={`text-[9px] uppercase tracking-wider font-bold ${t.sidebarLabel}`}><span className={handleClass}>≡ </span>Medidas</label>
                  <input className={`w-full mt-1 rounded-lg px-2 py-1.5 text-xs focus:outline-none transition-colors duration-200 ${t.input}`}
                    placeholder="Ej: 400x350cm isla 200x100cm" value={proy.medidas}
                    onChange={e => setProy(p => ({ ...p, medidas: e.target.value }))} />
                </div>;
              case 'distribucion':
                return <div key={fieldId} {...dragHandleProps} style={dragStyle}>
                  <p className={`text-[9px] font-black uppercase tracking-widest mt-2 ${t.sidebarSect}`}><span className={handleClass}>≡ </span>Distribución <span className={`font-normal ${t.sidebarLabel}`}>(opcional)</span></p>
                  <div className="grid grid-cols-3 gap-1">
                    {DISTRIBUCIONES.map(d => (
                      <button key={d.id} onClick={() => handleDistChange(d.id)}
                        className={`flex flex-col items-center gap-0.5 p-1.5 rounded-lg text-[8px] font-bold transition-all ${
                          distribucion && distribucion.tipo === d.id ? 'bg-amber-600 text-white' : `${t.input} hover:opacity-80`
                        }`}>
                        <span className="text-sm leading-none whitespace-pre">{d.icon}</span>
                        <span>{d.label}</span>
                      </button>
                    ))}
                  </div>
                  {distribucion && (
                    <>
                      <div className="flex flex-col gap-1.5 mt-2">
                        {distribucion.paredes.map((p, i) => (
                          <div key={i} className={`rounded-lg p-1.5 ${t.input}`}>
                            <p className={`text-[8px] font-bold ${t.sidebarLabel}`}>{p.nombre}</p>
                            <div className="flex gap-1 mt-1">
                              <input type="number" className={`w-full rounded px-1.5 py-0.5 text-[10px] ${t.input}`}
                                value={p.ancho} onChange={e => updatePared(i, 'ancho', e.target.value)} />
                              <span className={`text-[8px] self-center ${t.sidebarLabel}`}>cm</span>
                            </div>
                          </div>
                        ))}
                        {distribucion.tipo === 'isla' && (
                          <div className={`rounded-lg p-1.5 ${t.input}`}>
                            <p className={`text-[8px] font-bold ${t.sidebarLabel}`}>Isla central</p>
                            <div className="flex gap-1 mt-1">
                              <input type="number" className={`w-1/2 rounded px-1.5 py-0.5 text-[10px] ${t.input}`}
                                placeholder="Ancho" value={distribucion.isla.ancho} onChange={e => updateIsla('ancho', e.target.value)} />
                              <span className={`text-[8px] self-center ${t.sidebarLabel}`}>×</span>
                              <input type="number" className={`w-1/2 rounded px-1.5 py-0.5 text-[10px] ${t.input}`}
                                placeholder="Largo" value={distribucion.isla.largo} onChange={e => updateIsla('largo', e.target.value)} />
                              <span className={`text-[8px] self-center ${t.sidebarLabel}`}>cm</span>
                            </div>
                          </div>
                        )}
                      </div>
                      <p className={`text-[9px] font-black uppercase tracking-widest mt-1 ${t.sidebarSect}`}>Elementos</p>
                      <div className="flex flex-wrap gap-1">
                        {ELEMENTOS_COCINA.map(e => (
                          <button key={e.id} onClick={() => addElemento(e.id, 0)}
                            className={`flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[8px] font-medium transition-all ${t.input} hover:opacity-80`}
                            title={`Añadir ${e.label} (${e.ancho_default}cm)`}>
                            <span>{e.emoji}</span>
                          </button>
                        ))}
                      </div>
                      {distribucion.elementos.length > 0 && (
                        <div className="flex flex-col gap-0.5">
                          {distribucion.elementos.map((el, i) => (
                            <div key={i} className={`flex items-center gap-1 px-1.5 py-0.5 rounded text-[8px] ${t.input}`}>
                              <span>{el.emoji}</span>
                              <span className="flex-1 truncate">{el.label}</span>
                              <span className={`${t.sidebarLabel}`}>{el.ancho}cm</span>
                              <button onClick={() => removeElemento(i)} className="text-red-400 hover:text-red-300 text-[10px]">×</button>
                            </div>
                          ))}
                        </div>
                      )}
                    </>
                  )}
                </div>;
              case 'estilo':
                return <div key={fieldId} {...dragHandleProps} style={dragStyle}>
                  <label className={`text-[9px] uppercase tracking-wider font-bold ${t.sidebarLabel}`}><span className={handleClass}>≡ </span>Estilo</label>
                  <select className={`w-full mt-1 rounded-lg px-2 py-1.5 text-xs focus:outline-none transition-colors duration-200 ${t.select}`}
                    value={proy.estilo} onChange={e => setProy(p => ({ ...p, estilo: e.target.value }))}>
                    {ESTILOS.map(s => <option key={s}>{s}</option>)}
                  </select>
                </div>;
              case 'descripcion':
                return <div key={fieldId} {...dragHandleProps} style={dragStyle}>
                  <label className={`text-[9px] uppercase tracking-wider font-bold ${t.sidebarLabel}`}><span className={handleClass}>≡ </span>Descripción</label>
                  <textarea
                    className={`w-full mt-1 rounded-lg px-2 py-1.5 text-xs focus:outline-none resize-none transition-colors duration-200 ${t.input}`}
                    rows={6} placeholder="Describe la cocina o dicta por voz…"
                    value={proy.descripcion}
                    onChange={e => setProy(p => ({ ...p, descripcion: e.target.value }))} />
                </div>;
              case 'notas':
                return <div key={fieldId} {...dragHandleProps} style={dragStyle}>
                  <label className={`text-[9px] uppercase tracking-wider font-bold ${t.sidebarLabel}`}><span className={handleClass}>≡ </span>Materiales / Notas</label>
                  <textarea
                    className={`w-full mt-1 rounded-lg px-2 py-1.5 text-xs focus:outline-none resize-none transition-colors duration-200 ${t.input}`}
                    rows={4} placeholder="Encimera silestone, frentes lacados…"
                    value={proy.notas}
                    onChange={e => setProy(p => ({ ...p, notas: e.target.value }))} />
                </div>;
              default: return null;
            }
          })}

          {/* Botones de voz */}
          <div className="flex gap-1">
            {/* Grabación backend (transcripción IA) */}
            <button
              onClick={rec ? stopRec : startRec}
              className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-xl text-[9px] font-black uppercase tracking-widest transition-all ${
                rec ? 'bg-red-600 text-white animate-pulse' : t.micIdle
              }`}
              title="Grabar audio y transcribir con IA"
            >
              {rec ? <><MicOff size={12}/> Parar</> : <><Mic size={12}/> Grabar</>}
            </button>
            {/* Web Speech API (tiempo real, se añade al texto) */}
            {speechSupported && (
              <button
                onClick={() => {
                  if (isListening) { stopListening(); }
                  else { baseTextRef.current = proy.descripcion; startListening(); }
                }}
                className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-xl text-[9px] font-black uppercase tracking-widest transition-all ${
                  isListening ? 'bg-emerald-600 text-white animate-pulse' : t.micIdle
                }`}
                title="Dictar en tiempo real (se añade al texto)"
              >
                {isListening ? <><MicOff size={12}/> Dictando…</> : <><Mic size={12}/> Dictar</>}
              </button>
            )}
          </div>

          {transcrito && (
            <div className={`rounded-lg p-2 ${t.transcBg}`}>
              <p className={`text-[9px] font-bold mb-1 ${t.transcLabel}`}>Transcripción:</p>
              <p className={`text-[9px] leading-relaxed ${t.transcText}`}>{transcrito.slice(0, 180)}{transcrito.length > 180 ? '…' : ''}</p>
            </div>
          )}
        </div>

        {/* Main */}
        <div className="flex-1 flex flex-col overflow-hidden min-h-0">

          {/* Tabs */}
          <div className={`flex px-4 pt-2 gap-1 flex-shrink-0 transition-colors duration-200 ${t.tabBar}`}>
            {TABS.map(tb => (
              <button key={tb.id} onClick={() => setTab(tb.id)}
                className={`flex items-center gap-1.5 px-3 py-2 rounded-t-lg text-[10px] font-black uppercase tracking-widest transition-all ${
                  tab === tb.id ? t.tabActive : t.tabInactive
                }`}>
                {tb.icon} {tb.label}
              </button>
            ))}
          </div>

          <div className="flex-1 overflow-y-auto p-5">

            {/* ── RENDER MANUS ── */}
            {tab === 'render' && (
              <div className="flex flex-col gap-4 max-w-2xl mx-auto">
                <div>
                  <h2 className={`text-sm font-black mb-1 ${t.title}`}>Render fotorrealista 3D</h2>
                  <p className={`text-xs ${t.subtext}`}>Elige un estilo rápido o escribe tu propia descripción. Sube un croquis para mayor precisión.</p>
                </div>

                {/* Estilos rápidos */}
                <div className={`rounded-xl p-4 ${t.sectionBg}`}>
                  <div className="flex items-center gap-2 mb-3">
                    <Wand2 size={13} className="text-amber-500"/>
                    <p className={`text-[10px] font-black uppercase tracking-widest text-amber-500`}>Estilos Rápidos</p>
                  </div>
                  <div className="grid grid-cols-3 gap-2">
                    {ESTILOS_RAPIDOS.map(s => (
                      <button key={s.id} onClick={() => applyStyle(s)}
                        className={`flex flex-col items-center gap-1 px-2 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${
                          selectedStyle === s.id ? t.styleBtnAct : t.styleBtn
                        }`}>
                        <span className="text-base">{s.emoji}</span>
                        <span>{s.label}</span>
                      </button>
                    ))}
                  </div>
                  {selectedStyle && (
                    <p className={`text-[9px] mt-2 ${t.subtext}`}>
                      Prompt calibrado aplicado. Puedes editar la descripción antes de generar.
                    </p>
                  )}
                </div>

                {/* Croquis */}
                <div className={`border-2 border-dashed rounded-xl p-5 text-center cursor-pointer transition-colors ${t.uploadBorder}`}
                  onClick={() => croquisRef.current?.click()}>
                  {render.croquisPrev ? (
                    <div className="relative inline-block">
                      <img src={render.croquisPrev} alt="Croquis" className="max-h-32 mx-auto rounded-lg object-contain" />
                      <button className="absolute -top-2 -right-2 bg-red-600 rounded-full p-0.5"
                        onClick={e => { e.stopPropagation(); setRender(s => ({ ...s, croquis: null, croquisPrev: null })); }}>
                        <X size={10} className="text-white"/>
                      </button>
                    </div>
                  ) : (
                    <>
                      <Upload size={22} className={`mx-auto mb-2 ${t.uploadText}`} />
                      <p className={`text-xs ${t.uploadText}`}>Sube un croquis a boli (opcional)</p>
                    </>
                  )}
                  <input ref={croquisRef} type="file" accept="image/*" className="hidden" onChange={onCroquis} />
                </div>

                {/* Toggle: Respetar plano vs Diseño libre IA */}
                <div className={`flex items-center gap-2 p-2 rounded-lg ${t.card}`}>
                  <button onClick={() => setFreeDesign(false)}
                    className={`flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all ${
                      !freeDesign ? 'bg-amber-600 text-white shadow-lg' : `${t.tabInactive}`
                    }`}>
                    <LayoutGrid size={12}/> Respetar plano
                  </button>
                  <button onClick={() => setFreeDesign(true)}
                    className={`flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all ${
                      freeDesign ? 'bg-purple-600 text-white shadow-lg' : `${t.tabInactive}`
                    }`}>
                    <Wand2 size={12}/> Diseño libre IA
                  </button>
                </div>
                {freeDesign && (
                  <p className="text-[10px] text-purple-500 font-medium px-1">
                    La IA generará un diseño a su criterio sin seguir el plano adjunto
                  </p>
                )}

                <button onClick={genRender} disabled={render.status === 'loading'}
                  className="flex items-center justify-center gap-2 w-full py-3 bg-amber-600 hover:bg-amber-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl text-sm font-black uppercase tracking-widest transition-all text-white">
                  {render.status === 'loading'
                    ? <><Loader2 size={15} className="animate-spin"/> Generando render…</>
                    : <><Sparkles size={15}/> Generar Render</>}
                </button>

                <StatusBadge status={render.status} message={render.msg} t={t} />

                {render.imageUrl && (
                  <>
                    {/* Barra de acciones del render */}
                    <div className="flex items-center gap-2 flex-wrap">
                      <button onClick={downloadWithWatermark}
                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all ${t.dlBtn}`}>
                        <Download size={11}/> PNG
                      </button>
                      <button onClick={guardarEnGaleria}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-widest bg-purple-600 hover:bg-purple-500 text-white transition-all">
                        <Save size={11}/> Galería
                      </button>
                      <button onClick={attachToBudget}
                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all ${
                          attached ? 'bg-emerald-600 text-white' : 'bg-orange-500 hover:bg-orange-600 text-white'
                        }`}
                        title="Adjuntar este render al presupuesto (Resumen Totales)">
                        {attached ? <><CheckCircle size={11}/> Adjuntado</> : <><Send size={11}/> Al presupuesto</>}
                      </button>
                      {render.croquisPrev && (
                        <button onClick={() => setCompareOn(v => !v)}
                          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all ${
                            compareOn ? 'bg-slate-800 text-white' : t.dlBtn
                          }`}
                          title="Comparar croquis original con el render">
                          <Image size={11}/> Comparar
                        </button>
                      )}
                      <button onClick={() => setRender(s => ({ ...s, editMode: !s.editMode }))}
                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all ${render.editMode ? 'bg-amber-600 text-white' : t.dlBtn}`}>
                        <Edit3 size={11}/> Editar
                      </button>
                    </div>

                    {/* Selector de marca de agua */}
                    <div className={`flex items-center gap-3 flex-wrap p-2 rounded-lg ${t.card}`}>
                      <span className={`text-[10px] font-black uppercase tracking-widest ${t.sidebarLabel}`}>
                        <Stamp size={11} className="inline mr-1"/> Marca:
                      </span>
                      <div className="flex items-center gap-1">
                        <button onClick={() => setWatermark(w => ({ ...w, mode: 'none' }))}
                          className={`px-2 py-1 rounded text-[9px] font-bold uppercase transition-all ${watermark.mode === 'none' ? 'bg-red-500 text-white' : `${t.tabInactive}`}`}>Sin marca</button>
                        <button onClick={() => setWatermark(w => ({ ...w, mode: 'default' }))}
                          className={`px-2 py-1 rounded text-[9px] font-bold uppercase transition-all ${watermark.mode === 'default' ? 'bg-amber-600 text-white' : `${t.tabInactive}`}`}>
                          Logo ERP
                        </button>
                        <button onClick={() => watermarkInputRef.current?.click()}
                          className={`px-2 py-1 rounded text-[9px] font-bold uppercase transition-all ${watermark.mode === 'custom' ? 'bg-purple-600 text-white' : `${t.tabInactive}`}`}>
                          <ImagePlus size={10} className="inline mr-1"/>
                          {watermark.customLogoPreview ? 'Cambiar' : 'Personalizar'}
                        </button>
                        <input ref={watermarkInputRef} type="file" accept="image/*" className="hidden" onChange={handleCustomLogoUpload}/>
                      </div>
                    </div>

                    {/* Comparativa croquis vs render */}
                    {compareOn && render.croquisPrev ? (
                      <div className="grid grid-cols-2 gap-3">
                        <div className={`rounded-xl overflow-hidden border ${t.cardBorder} relative`}>
                          <img src={render.croquisPrev} alt="Croquis original" className="w-full object-contain" />
                          <span className={`absolute top-2 left-2 px-2 py-1 bg-black/60 rounded text-[9px] font-black text-white uppercase tracking-widest`}>Croquis</span>
                        </div>
                        <div className={`rounded-xl overflow-hidden border ${t.cardBorder} relative`}>
                          <img src={imgSrc(render.imageUrl)} alt="Render 3D" className="w-full object-contain" />
                          <span className={`absolute top-2 left-2 px-2 py-1 bg-amber-600 rounded text-[9px] font-black text-white uppercase tracking-widest`}>Render</span>
                        </div>
                      </div>
                    ) : (
                      <div id="render-print-area" className={`relative group rounded-xl overflow-hidden border ${t.cardBorder}`}>
                        <img src={imgSrc(render.imageUrl)} alt="Render 3D" className="w-full object-contain" />
                        <div className="absolute top-2 right-2 flex gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button onClick={() => setRender(s => ({ ...s, fs: true }))} className={`p-1.5 rounded-lg ${t.dlBtn}`}><ZoomIn size={13}/></button>
                        </div>
                      </div>
                    )}
                  </>
                )}

                {/* Editor de render en lenguaje natural */}
                {render.editMode && render.imageUrl && (
                  <div className={`rounded-xl p-4 flex flex-col gap-3 ${t.editBox}`}>
                    <p className={`text-[10px] font-black uppercase tracking-widest ${t.editLabel}`}>Editar render en lenguaje natural</p>
                    <div className="flex gap-2">
                      <input className={`flex-1 rounded-lg px-3 py-2 text-xs focus:outline-none transition-colors ${t.input}`}
                        placeholder="Ej: Cambia los muebles a blanco mate, haz la isla más grande…"
                        value={render.editTxt} onChange={e => setRender(s => ({ ...s, editTxt: e.target.value }))}
                        onKeyDown={e => { if (e.key === 'Enter' && render.editTxt.trim()) editRender(); }} />
                      <button onClick={editRender} disabled={render.status === 'loading' || !render.editTxt.trim()}
                        className="flex items-center gap-1.5 px-4 py-2 bg-amber-600 hover:bg-amber-500 disabled:opacity-50 rounded-xl text-xs font-black uppercase tracking-widest text-white">
                        <Send size={12}/> Aplicar
                      </button>
                    </div>
                  </div>
                )}

                {render.fs && (
                  <div className="fixed inset-0 bg-black/95 z-50 flex items-center justify-center p-4" onClick={() => setRender(s => ({ ...s, fs: false }))}>
                    <img src={imgSrc(render.imageUrl)} alt="Render" className="max-w-full max-h-full object-contain rounded-xl" />
                    <button className="absolute top-4 right-4 bg-white/10 p-2 rounded-full text-white"><X size={18}/></button>
                  </div>
                )}
              </div>
            )}

            {/* ── PLANO 2D ── */}
            {tab === 'plano' && (
              <div className="flex flex-col gap-4 max-w-2xl mx-auto">
                <div>
                  <h2 className={`text-sm font-black mb-1 ${t.title}`}>Plano técnico acotado</h2>
                  <p className={`text-xs ${t.subtext}`}>Usa las medidas del panel izquierdo. Formato: <code className={`px-1 rounded ${t.code}`}>400x350cm isla 200x100cm</code></p>
                </div>
                <button onClick={genPlano} disabled={plano.status === 'loading'}
                  className="flex items-center justify-center gap-2 w-full py-3 bg-amber-600 hover:bg-amber-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl text-sm font-black uppercase tracking-widest transition-all text-white">
                  {plano.status === 'loading' ? <><Loader2 size={15} className="animate-spin"/> Generando plano…</> : <><Image size={15}/> Generar Plano 2D</>}
                </button>
                <StatusBadge status={plano.status} message={plano.msg} t={t} />
                {plano.b64 && (
                  <>
                    <PrintPdfBar t={t} onPrint={() => handlePrint('plano-print-area')} onPdf={() => handlePdfExport(`<img src="${plano.b64}" style="width:100%"/>`, `plano_${proy.nombre_cliente || 'cocina'}.pdf`)}
                      extraBtns={<a href={plano.b64} download={`plano_${proy.nombre_cliente || 'cocina'}.png`} className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all ${t.dlBtn}`}><Download size={11}/> PNG</a>} />
                    <div id="plano-print-area" className={`relative group rounded-xl overflow-hidden border ${t.cardBorder}`}>
                      <img src={plano.b64} alt="Plano 2D" className="w-full object-contain" />
                      <div className="absolute top-2 right-2 flex gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button onClick={() => setPlano(s => ({ ...s, fs: true }))} className={`p-1.5 rounded-lg ${t.dlBtn}`}><Maximize2 size={13}/></button>
                      </div>
                    </div>
                  </>
                )}
                {plano.fs && (
                  <div className="fixed inset-0 bg-black/95 z-50 flex items-center justify-center p-4" onClick={() => setPlano(s => ({ ...s, fs: false }))}>
                    <img src={plano.b64} alt="Plano" className="max-w-full max-h-full object-contain rounded-xl" />
                    <button className="absolute top-4 right-4 bg-white/10 p-2 rounded-full text-white"><X size={18}/></button>
                  </div>
                )}
              </div>
            )}

            {/* ── FICHA TÉCNICA ── */}
            {tab === 'ficha' && (
              <div className="flex flex-col gap-4 max-w-2xl mx-auto">
                <div>
                  <h2 className={`text-sm font-black mb-1 ${t.title}`}>Ficha técnica del proyecto</h2>
                  <p className={`text-xs ${t.subtext}`}>Genera una ficha con materiales, electrodomésticos, instalaciones y plazos.</p>
                </div>
                <button onClick={genFicha} disabled={ficha.status === 'loading'}
                  className="flex items-center justify-center gap-2 w-full py-3 bg-amber-600 hover:bg-amber-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl text-sm font-black uppercase tracking-widest transition-all text-white">
                  {ficha.status === 'loading' ? <><Loader2 size={15} className="animate-spin"/> Generando ficha…</> : <><FileText size={15}/> Generar Ficha Técnica</>}
                </button>
                <StatusBadge status={ficha.status} message={ficha.msg} t={t} />
                {ficha.md && (
                  <>
                    <PrintPdfBar t={t} onPrint={() => handlePrint('ficha-print-area')} onPdf={() => handlePdfExport(ficha.md, `ficha_${ficha.ref || 'cocina'}.pdf`)}
                      extraBtns={<button onClick={() => dl(ficha.md, `ficha_${ficha.ref || 'cocina'}.md`, 'text/markdown')} className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all ${t.dlBtn}`}><Download size={11}/> .md</button>} />
                    <div id="ficha-print-area">
                      <pre className={`rounded-xl p-5 text-xs leading-relaxed overflow-x-auto whitespace-pre-wrap font-mono ${t.pre}`}>{ficha.md}</pre>
                    </div>
                  </>
                )}
              </div>
            )}

            {/* ── PRESENTACIÓN ── */}
            {tab === 'pres' && (
              <div className="flex flex-col gap-4 max-w-2xl mx-auto">
                <div>
                  <h2 className={`text-sm font-black mb-1 ${t.title}`}>Presentación para cliente</h2>
                  <p className={`text-xs ${t.subtext}`}>Genera una presentación HTML de alta calidad lista para mostrar en pantalla o imprimir como PDF.</p>
                </div>
                <button onClick={genPres} disabled={pres.status === 'loading'}
                  className="flex items-center justify-center gap-2 w-full py-3 bg-amber-600 hover:bg-amber-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl text-sm font-black uppercase tracking-widest transition-all text-white">
                  {pres.status === 'loading' ? <><Loader2 size={15} className="animate-spin"/> Generando…</> : <><Presentation size={15}/> Generar Presentación</>}
                </button>
                <StatusBadge status={pres.status} message={pres.msg} t={t} />
                {pres.html && (
                  <div className="flex flex-col gap-3">
                    <PrintPdfBar t={t} onPrint={() => handlePdfExport(pres.html, `presentacion_${proy.nombre_cliente || 'cliente'}.pdf`)} onPdf={() => handlePdfExport(pres.html, `presentacion_${proy.nombre_cliente || 'cliente'}.pdf`)}
                      extraBtns={<>
                        <button onClick={() => setPres(s => ({ ...s, preview: !s.preview }))} className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all ${t.dlBtn}`}><Eye size={11}/> {pres.preview ? 'Ocultar' : 'Vista previa'}</button>
                        <button onClick={() => dl(pres.html, `presentacion_${proy.nombre_cliente || 'cliente'}.html`, 'text/html')} className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all ${t.presBtn}`}><Download size={11}/> HTML</button>
                      </>} />
                    {pres.preview && (
                      <div className={`rounded-xl overflow-hidden border ${t.cardBorder}`} style={{ height: '560px' }}>
                        <iframe srcDoc={pres.html} title="Presentación" className="w-full h-full" sandbox="allow-same-origin" />
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* ── INSTALACIONES ── */}
            {tab === 'inst' && (
              <div className="flex flex-col gap-4 max-w-2xl mx-auto">
                <div>
                  <h2 className={`text-sm font-black mb-1 ${t.title}`}>Plan de instalaciones</h2>
                  <p className={`text-xs ${t.subtext}`}>Genera el plan de puntos eléctricos, agua, desagüe y gas según la distribución de la cocina.</p>
                </div>
                <button onClick={genInstalaciones} disabled={inst.status === 'loading'}
                  className="flex items-center justify-center gap-2 w-full py-3 bg-amber-600 hover:bg-amber-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl text-sm font-black uppercase tracking-widest transition-all text-white">
                  {inst.status === 'loading' ? <><Loader2 size={15} className="animate-spin"/> Generando plan…</> : <><LayoutGrid size={15}/> Generar Plan de Instalaciones</>}
                </button>
                <StatusBadge status={inst.status} message={inst.msg} t={t} />
                {inst.data && (
                  <>
                    <PrintPdfBar t={t} onPrint={() => handlePrint('inst-print-area')} onPdf={() => handlePdfExport(JSON.stringify(inst.data, null, 2), `instalaciones_${proy.nombre_cliente || 'cocina'}.pdf`)} />
                    <div id="inst-print-area" className="flex flex-col gap-4">
                      {inst.data.electrica && (
                        <div className={`rounded-xl p-4 ${t.instCard}`}>
                          <div className="flex items-center gap-2 mb-3">
                            <div className={`flex items-center gap-1.5 px-2 py-1 rounded-lg text-[10px] font-black uppercase tracking-widest ${t.instElec}`}><Zap size={11}/> Instalación Eléctrica</div>
                          </div>
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                            {(inst.data.electrica.puntos || []).map((p, i) => (
                              <div key={i} className={`flex items-start gap-2 p-2 rounded-lg ${t.instElec}`}>
                                <Zap size={11} className="flex-shrink-0 mt-0.5"/>
                                <div><p className="text-[10px] font-bold">{p.tipo || `Punto ${i+1}`}</p><p className="text-[9px] opacity-70">{p.ubicacion || ''}</p></div>
                              </div>
                            ))}
                            {inst.data.electrica.circuitos && (<div className={`col-span-2 p-2 rounded-lg ${t.instElec}`}><p className="text-[10px] font-bold mb-1">Circuitos</p><p className="text-[9px]">{inst.data.electrica.circuitos}</p></div>)}
                          </div>
                        </div>
                      )}
                      {inst.data.fontaneria && (
                        <div className={`rounded-xl p-4 ${t.instCard}`}>
                          <div className="flex items-center gap-2 mb-3">
                            <div className={`flex items-center gap-1.5 px-2 py-1 rounded-lg text-[10px] font-black uppercase tracking-widest ${t.instWater}`}><Droplets size={11}/> Fontanería</div>
                          </div>
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                            {(inst.data.fontaneria.puntos || []).map((p, i) => (
                              <div key={i} className={`flex items-start gap-2 p-2 rounded-lg ${t.instWater}`}>
                                <Droplets size={11} className="flex-shrink-0 mt-0.5"/>
                                <div><p className="text-[10px] font-bold">{p.tipo || `Punto ${i+1}`}</p><p className="text-[9px] opacity-70">{p.ubicacion || ''}</p></div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      {inst.data.gas && (
                        <div className={`rounded-xl p-4 ${t.instCard}`}>
                          <div className="flex items-center gap-2 mb-3">
                            <div className={`flex items-center gap-1.5 px-2 py-1 rounded-lg text-[10px] font-black uppercase tracking-widest ${t.instGas}`}><Flame size={11}/> Gas</div>
                          </div>
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                            {(inst.data.gas.puntos || []).map((p, i) => (
                              <div key={i} className={`flex items-start gap-2 p-2 rounded-lg ${t.instGas}`}>
                                <Flame size={11} className="flex-shrink-0 mt-0.5"/>
                                <div><p className="text-[10px] font-bold">{p.tipo || `Punto ${i+1}`}</p><p className="text-[9px] opacity-70">{p.ubicacion || ''}</p></div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      {inst.data.notas && (
                        <div className={`rounded-xl p-4 ${t.instCard}`}>
                          <p className={`text-[10px] font-black uppercase tracking-widest mb-2 ${t.subtext}`}>Notas técnicas</p>
                          <p className={`text-xs leading-relaxed ${t.subtext}`}>{inst.data.notas}</p>
                        </div>
                      )}
                      {!inst.data.electrica && !inst.data.fontaneria && !inst.data.gas && (
                        <pre className={`rounded-xl p-4 text-xs whitespace-pre-wrap font-mono ${t.pre}`}>{JSON.stringify(inst.data, null, 2)}</pre>
                      )}
                    </div>
                  </>
                )}
              </div>
            )}

            {/* ── GALERÍA DE RENDERS ── */}
            {tab === 'galeria' && (
              <div className="flex flex-col gap-4 max-w-4xl mx-auto">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className={`text-sm font-black mb-1 ${t.title}`}>Galería de Renders</h2>
                    <p className={`text-xs ${t.subtext}`}>Renders guardados de tus proyectos.</p>
                  </div>
                  <button onClick={() => loadGaleria(1)} className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-widest bg-amber-600 hover:bg-amber-500 text-white transition-all">
                    <RefreshCw size={11}/> Actualizar
                  </button>
                </div>
                {galeria.loading && (<div className="flex items-center justify-center py-10"><Loader2 size={24} className="animate-spin text-amber-500" /></div>)}
                {!galeria.loading && galeria.renders.length === 0 && (
                  <div className={`text-center py-12 rounded-xl ${t.card}`}>
                    <FolderOpen size={32} className="mx-auto mb-3 text-slate-400" />
                    <p className={`text-sm font-bold ${t.subtext}`}>Aún no hay renders guardados</p>
                    <p className={`text-xs mt-1 ${t.subtext}`}>Genera un render y pulsa "Galería" para añadirlo aquí.</p>
                  </div>
                )}
                {!galeria.loading && galeria.renders.length > 0 && (
                  <>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                      {galeria.renders.map(r => (
                        <div key={r._id} className={`relative group rounded-xl overflow-hidden border ${t.cardBorder} transition-shadow hover:shadow-lg`}>
                          <img src={imgSrc(r.image_url)} alt={r.cliente || 'Render'} className="w-full h-40 object-cover cursor-pointer"
                            onClick={() => setGaleria(g => ({ ...g, fsImg: r.image_url }))} />
                          <div className="absolute bottom-1 left-1 bg-black/50 text-white text-[8px] font-black px-1.5 py-0.5 rounded uppercase tracking-widest">3D Estudio</div>
                          <div className="absolute top-1.5 right-1.5 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button onClick={() => toggleFavorito(r._id)} className={`p-1 rounded-lg ${r.favorito ? 'bg-red-500 text-white' : 'bg-white/80 text-slate-600 hover:bg-red-100'}`}><Heart size={11} fill={r.favorito ? 'currentColor' : 'none'} /></button>
                            <button onClick={() => eliminarRender(r._id)} className="p-1 rounded-lg bg-white/80 text-slate-600 hover:bg-red-100 hover:text-red-600"><Trash2 size={11} /></button>
                            <a href={imgSrc(r.image_url)} download className="p-1 rounded-lg bg-white/80 text-slate-600 hover:bg-emerald-100"><Download size={11} /></a>
                          </div>
                          <div className="p-2">
                            <p className={`text-[10px] font-bold truncate ${t.title}`}>{r.cliente || 'Sin cliente'}</p>
                            <p className={`text-[9px] ${t.subtext}`}>{r.estilo} · {r.fecha}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                    {galeria.total > 12 && (
                      <div className="flex justify-center gap-2 mt-4">
                        <button disabled={galeria.page <= 1} onClick={() => loadGaleria(galeria.page - 1)} className={`px-3 py-1 rounded-lg text-xs font-bold ${galeria.page <= 1 ? 'opacity-30' : 'hover:bg-slate-200'} ${t.card}`}>← Anterior</button>
                        <span className={`px-3 py-1 text-xs font-bold ${t.subtext}`}>Pág {galeria.page}</span>
                        <button disabled={galeria.page * 12 >= galeria.total} onClick={() => loadGaleria(galeria.page + 1)} className={`px-3 py-1 rounded-lg text-xs font-bold ${galeria.page * 12 >= galeria.total ? 'opacity-30' : 'hover:bg-slate-200'} ${t.card}`}>Siguiente →</button>
                      </div>
                    )}
                  </>
                )}
                {galeria.fsImg && (
                  <div className="fixed inset-0 bg-black/95 z-50 flex items-center justify-center p-4" onClick={() => setGaleria(g => ({ ...g, fsImg: null }))}>
                    <img src={imgSrc(galeria.fsImg)} alt="Render" className="max-w-full max-h-full object-contain rounded-xl" />
                    <button className="absolute top-4 right-4 bg-white/10 p-2 rounded-full text-white hover:bg-white/20"><X size={18}/></button>
                  </div>
                )}
              </div>
            )}

          </div>
        </div>
      </div>

      {/* Modal: Lista de proyectos guardados */}
      {Array.isArray(savedList) && (
        <div className="fixed inset-0 z-[9998] bg-black/50 flex items-center justify-center p-4" onClick={() => setSavedList(null)}>
          <div className={`rounded-2xl w-full max-w-lg max-h-[80vh] overflow-hidden flex flex-col ${t.root === 'bg-white text-slate-800' ? 'bg-white' : 'bg-[#1A1A1A]'}`} onClick={e => e.stopPropagation()}>
            <div className={`flex items-center justify-between px-5 py-4 border-b ${t.cardBorder}`}>
              <h3 className={`font-black ${t.title}`}>Mis proyectos 3D</h3>
              <button onClick={() => setSavedList(null)} className={`p-1.5 ${t.subtext} hover:opacity-70`}><X size={18} /></button>
            </div>
            <div className="p-4 overflow-y-auto">
              {savedList.length === 0 ? (
                <p className={`text-sm text-center py-8 ${t.subtext}`}>No tienes proyectos guardados todavía.</p>
              ) : savedList.map(d => (
                <div key={d.id} className={`flex items-center gap-3 border rounded-xl p-2 mb-2 ${t.cardBorder} hover:opacity-90`}>
                  <div className={`w-12 h-12 shrink-0 rounded-lg overflow-hidden ${t.card}`}>
                    {d.images?.[0] ? <img src={imgSrc(d.images[0])} alt="" className="w-full h-full object-cover" /> : <div className="w-full h-full flex items-center justify-center"><Image size={16} className={t.subtext} /></div>}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className={`font-bold text-sm truncate ${t.title}`}>{d.cliente || 'Sin cliente'}{d.ref ? ` · ${d.ref}` : ''}</p>
                    {d.updatedAt && <p className={`text-[10px] ${t.subtext}`}>{new Date(d.updatedAt).toLocaleString('es-ES')}</p>}
                  </div>
                  <button onClick={() => loadProject(d)} className="px-3 py-1.5 bg-amber-600 text-white rounded-lg text-xs font-bold hover:bg-amber-500">Abrir</button>
                  <button onClick={() => deleteProject(d.id)} className="p-1.5 text-red-400 hover:text-red-600 hover:bg-red-50 rounded-lg"><Trash2 size={16} /></button>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
