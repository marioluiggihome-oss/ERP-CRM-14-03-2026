/*
 * © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
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
  Send, Plus, ChevronLeft, ChevronRight, ClipboardList
} from 'lucide-react';
import FichaFabricacion from './FichaFabricacion';
import { jsPDF } from 'jspdf';

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
  // Las data:/blob: URLs son imágenes ya embebidas (p.ej. render Gemini): NO se
  // les puede añadir el token de proxy o se corrompen y no se ven.
  if (url.startsWith('blob:') || url.startsWith('data:')) return url;
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
    setDistribucion(d => {
      // Calcular posicion_cm acumulando anchos de elementos previos en la misma pared
      const elemsEnPared = d.elementos.filter(e => e.pared_idx === paredIdx);
      const posicion_cm = elemsEnPared.reduce((acc, e) => acc + (e.ancho || 60), 0);
      return {
        ...d,
        elementos: [...d.elementos, { id: elemId, label: elem.label, emoji: elem.emoji, pared_idx: paredIdx, ancho: elem.ancho_default, posicion_cm }]
      };
    });
  }, []);

  const removeElemento = useCallback((idx) => {
    setDistribucion(d => ({ ...d, elementos: d.elementos.filter((_, i) => i !== idx) }));
  }, []);

  const [render, setRender] = useState({ status: null, msg: '', imageUrl: null, originalUrl: null, croquis: null, croquisPrev: null, editMode: false, editTxt: '', fs: false });
  const [freeDesign, setFreeDesign] = useState(false);
  const [plano,  setPlano]  = useState({ status: null, msg: '', b64: null, fs: false });
  // Vista alámbrica (alzados acotados por pared) para el dossier técnico.
  const [alzado, setAlzado] = useState({ status: null, msg: '', b64: null, fs: false });
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

  // ── Permisos ──
  const isMaster = state?.currentUser?.isAdmin === true || state?.currentUser?.isPrimaryAdmin === true;

  // ── Motor IA (solo master ve IA2/IA3/IA4) ──
  // ia1=Gemini pro (default), ia2=Manus, ia3=Gemini flash (rápido), ia4=Gemini ultra-fotorrealista
  const [motorIA, setMotorIA] = useState('ia1');
  const providerDeMotor = () => motorIA === 'ia2' ? 'manus' : 'gemini';
  // Prompt extra según motor
  const promptExtraMotor = (base) => {
    if (motorIA === 'ia4') {
      return `ULTRA-PHOTOREALISTIC architectural visualization, 8K resolution, professional kitchen photography, shot with Canon EOS R5 85mm lens, f/2.8, golden hour natural light from window, physically-based rendering, subsurface scattering on surfaces, ray-traced reflections, volumetric light rays, micro-detail textures visible, interior design magazine quality. ${base}`;
    }
    if (motorIA === 'ia3') {
      return `${base}. Render fotorrealista rápido, buena calidad, iluminación natural.`;
    }
    return base;
  };

  // ── Comparativa A/B entre dos renders ──
  const [renderB, setRenderB] = useState({ status: null, msg: '', imageUrl: null });
  const [compareAB, setCompareAB] = useState(false);

  // ── Nuevas funcionalidades migradas ──
  const [attached, setAttached] = useState(false);       // Adjuntado al presupuesto
  const [compareOn, setCompareOn] = useState(false);     // Comparativa croquis vs render
  const [savedId, setSavedId] = useState(null);          // ID del proyecto guardado
  const [savedList, setSavedList] = useState(null);      // Lista de proyectos (null = modal oculto)
  const [savedSearch, setSavedSearch] = useState('');    // Buscador de proyectos por nombre/referencia
  const [busySave, setBusySave] = useState(false);       // Guardando proyecto
  // Panel lateral redimensionable/ocultable (solo pantallas grandes).
  const [panelW, setPanelW] = useState(224);
  const [panelHidden, setPanelHidden] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false); // Sidebar overlay en mobile
  // Panel derecho (acciones + proyecto) — solo desktop
  const [rightOpen, setRightOpen] = useState(true);      // visible u oculto
  const [rightExpanded, setRightExpanded] = useState(false); // normal (220px) o expandido (340px)
  const resizingPanel = useRef(false);
  const isWide = () => typeof window !== 'undefined' && window.innerWidth >= 1024;
  useEffect(() => {
    const onMove = (e) => { if (resizingPanel.current) setPanelW(Math.max(180, Math.min(520, e.clientX))); };
    const onUp = () => { if (resizingPanel.current) { resizingPanel.current = false; document.body.style.userSelect = ''; } };
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
    return () => { window.removeEventListener('mousemove', onMove); window.removeEventListener('mouseup', onUp); };
  }, []);

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
    // Revocar blob URL anterior para evitar memory leak
    if (render.imageUrl && render.imageUrl.startsWith('blob:')) {
      URL.revokeObjectURL(render.imageUrl);
    }
    setRender(s => ({ ...s, status: 'loading', msg: 'Generando render…', imageUrl: null }));
    try {
      // Con croquis, quitamos del texto de materiales/descripción los fragmentos que
      // meten distribución (isla, ventana…) para que NO alteren el diseño del croquis.
      const stripLayout = (t) => String(t || '')
        .split(/[.·|;]/).map(s => s.trim())
        .filter(s => s && !/^(isla|island|ventanal?|window)\b/i.test(s))
        .join('. ');
      const conCroquis = !!render.croquis && !freeDesign;

      // Construimos una descripción única y usamos el MISMO pipeline que la sección
      // "Estudio 3D" (endpoint /api/ai-engine/render, motor Gemini), que sí funciona.
      const partes = [];
      partes.push(conCroquis ? stripLayout(proy.descripcion) : proy.descripcion);
      const mats = conCroquis ? stripLayout(proy.notas) : proy.notas;
      if (mats && mats.trim()) partes.push(`Materiales y acabados: ${mats.trim()}`);
      if (!conCroquis && proy.medidas && proy.medidas.trim()) partes.push(`Distribución y medidas: ${proy.medidas.trim()}`);
      let descripcion = partes.filter(Boolean).join('. ');
      if (conCroquis) {
        descripcion = `Genera un render 3D fotorrealista RESPETANDO FIELMENTE el croquis/plano adjunto: misma distribución, mismos módulos (altos, bajos, columnas), mismas proporciones y posiciones. No añadas ni quites muebles, no añadas isla ni ventanas que no estén en el croquis. ${descripcion}`;
      }

      const descFinal = promptExtraMotor(descripcion);
      const res = await fetch(`${API}/api/ai-engine/render`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${getToken()}` },
        body: JSON.stringify({
          description: descFinal,
          style: proy.estilo || undefined,
          provider: providerDeMotor(),
          referenceImage: conCroquis ? render.croquis : undefined,
        }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || !data.success) throw new Error(data.error || data.detail || 'No se pudo generar el render');

      const u = data.result?.images?.[0] || data.imageUrl;
      if (!u) throw new Error('El motor no devolvió ninguna imagen');
      const shown = String(u).startsWith('data:') ? u : ((await fetchAsBlob(u)) || imgSrc(u));
      setRender(s => ({ ...s, status: 'success', msg: `Render generado [${motorIA.toUpperCase()}]`, imageUrl: shown, originalUrl: u }));
    } catch (err) {
      setRender(s => ({ ...s, status: 'error', msg: err.message }));
    }
    }, [proy, render.croquis, freeDesign, motorIA]);
  const editRender = useCallback(async () => {
    if (!render.editTxt.trim()) return;
    if (!render.imageUrl) {
      setRender(s => ({ ...s, status: 'error', msg: 'No hay render para editar. Genera uno primero.' }));
      return;
    }
    setRender(s => ({ ...s, status: 'loading', msg: 'Editando render…' }));
    try {
      // Mismo pipeline que "Estudio 3D": mandamos la imagen actual como referencia
      // (en base64) y una instrucción de edición fiel al motor Gemini.
      const prevB64 = await imageToDataUrl(render.imageUrl).catch(() => null);
      const res = await fetch(`${API}/api/ai-engine/render`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${getToken()}` },
        body: JSON.stringify({
          description: `Modifica el render adjunto manteniendo EXACTAMENTE el mismo diseño, distribución, encuadre, cámara e iluminación. Cambio solicitado: ${render.editTxt.trim()}. No cambies nada más.`,
          provider: 'gemini',
          referenceImage: prevB64 || undefined,
        }),
      });
      const r = await res.json().catch(() => ({}));
      if (!res.ok || !r.success) throw new Error(r.error || r.detail || 'No se pudo editar el render');
      const u = r.result?.images?.[0] || r.imageUrl;
      if (!u) throw new Error('El motor no devolvió ninguna imagen');
      const shown = String(u).startsWith('data:') ? u : ((await fetchAsBlob(u)) || imgSrc(u));
      setRender(s => ({ ...s, status: 'success', msg: 'Render editado', imageUrl: shown, originalUrl: u, editMode: false, editTxt: '' }));
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

  // ── Dossier PDF multipágina (portada + render + planta + alzados + ficha) ──
  const [dossierBusy, setDossierBusy] = useState(false);
  const generarDossier = useCallback(async () => {
    setDossierBusy(true);
    try {
      const dossierLogo = watermark.mode === 'custom' ? watermark.customLogo : defaultLogo;
      const loadSize = (src) => new Promise((res) => { const im = new window.Image(); im.onload = () => res({ w: im.width, h: im.height }); im.onerror = () => res({ w: 16, h: 9 }); im.src = src; });
      // Reunir láminas disponibles (al menos el render).
      const plates = [];
      if (render.imageUrl) plates.push({ title: 'Perspectiva · Render', img: await imageToDataUrl(render.imageUrl).catch(() => render.imageUrl) });
      if (plano.b64) plates.push({ title: 'Planta acotada', img: plano.b64 });
      if (alzado.b64) plates.push({ title: 'Alzados acotados · vista alámbrica', img: alzado.b64 });
      if (!plates.length) { alert('Genera al menos el render (y opcionalmente plano/alzados) antes del dossier.'); setDossierBusy(false); return; }
      for (const p of plates) p.size = await loadSize(p.img);

      const pdf = new jsPDF({ unit: 'mm', format: 'a4', orientation: 'landscape' });
      const W = pdf.internal.pageSize.getWidth(), H = pdf.internal.pageSize.getHeight();
      const fecha = new Date().toLocaleDateString('es-ES');
      const cliente = (proy.nombre_cliente || 'Cliente').toUpperCase();
      const proyecto = proy.descripcion ? proy.descripcion.slice(0, 60) : 'Cocina a medida';
      const fmtLogo = (l) => (l && l.includes('image/png')) ? 'PNG' : (l && l.includes('image/webp') ? 'WEBP' : 'JPEG');

      // ── Portada ──
      pdf.setFillColor(24, 24, 27); pdf.rect(0, 0, W, H, 'F');
      if (dossierLogo) { try { pdf.addImage(dossierLogo, fmtLogo(dossierLogo), W / 2 - 26, 30, 52, 24); } catch (_) {} }
      pdf.setTextColor(202, 169, 104); pdf.setFontSize(11); pdf.text('ESTUDIO DE COCINAS', W / 2, 68, { align: 'center' });
      pdf.setTextColor(255); pdf.setFontSize(30); pdf.setFont(undefined, 'bold');
      pdf.text('DOSSIER DE PROYECTO', W / 2, 92, { align: 'center' });
      pdf.setFont(undefined, 'normal'); pdf.setFontSize(14); pdf.setTextColor(230);
      pdf.text(cliente, W / 2, 108, { align: 'center' });
      pdf.setFontSize(10); pdf.setTextColor(170);
      pdf.text(`${proyecto}  ·  Estilo ${proy.estilo || '—'}  ·  ${fecha}`, W / 2, 118, { align: 'center' });
      pdf.setDrawColor(202, 169, 104); pdf.line(W / 2 - 30, 124, W / 2 + 30, 124);
      pdf.setFontSize(8); pdf.setTextColor(140);
      pdf.text('Documentación: render, planta acotada, alzados y ficha técnica.', W / 2, H - 14, { align: 'center' });

      // ── Una página por lámina, con cajetín tipo estudio a la derecha ──
      const bx = W - 62; // inicio del cajetín
      plates.forEach((p, i) => {
        pdf.addPage();
        pdf.setFillColor(255, 255, 255); pdf.rect(0, 0, W, H, 'F');
        // Imagen (contain) en el área izquierda
        const ax = 10, ay = 10, aw = bx - 16, ah = H - 20;
        const sc = Math.min(aw / p.size.w, ah / p.size.h);
        const iw = p.size.w * sc, ih = p.size.h * sc;
        try { pdf.addImage(p.img, 'PNG', ax + (aw - iw) / 2, ay + (ah - ih) / 2, iw, ih); } catch (_) {}
        // Cajetín derecho
        pdf.setDrawColor(30); pdf.line(bx, 10, bx, H - 10);
        let cy = 16;
        if (dossierLogo) { try { pdf.addImage(dossierLogo, fmtLogo(dossierLogo), bx + 4, cy, 40, 16); cy += 22; } catch (_) {} }
        const fld = (k, v) => { pdf.setFontSize(7); pdf.setTextColor(150); pdf.text(k.toUpperCase(), bx + 4, cy); pdf.setFontSize(9.5); pdf.setTextColor(30); pdf.text(pdf.splitTextToSize(String(v || '—'), 54), bx + 4, cy + 4.5); cy += 13; };
        fld('Cliente', cliente);
        fld('Proyecto', proyecto);
        fld('Descripción del plano', p.title);
        fld('Escala', 'Orientativa / cotas en cm');
        fld('Fecha', fecha);
        pdf.setFontSize(7); pdf.setTextColor(120);
        pdf.text(pdf.splitTextToSize('Cualquier discrepancia sobre las dimensiones debe consultarse con el responsable del proyecto antes de ejecutar.', 54), bx + 4, H - 34);
        pdf.setFontSize(9); pdf.setTextColor(160); pdf.text(`P${i}.${plates.length}`, W - 12, H - 10, { align: 'right' });
      });

      // ── Página de ficha técnica (materiales/acabados) si existe ──
      if (ficha.md) {
        pdf.addPage();
        pdf.setFillColor(255, 255, 255); pdf.rect(0, 0, W, H, 'F');
        pdf.setFontSize(14); pdf.setTextColor(24, 24, 27); pdf.setFont(undefined, 'bold');
        pdf.text('FICHA TÉCNICA', 14, 16); pdf.setFont(undefined, 'normal');
        const plain = ficha.md.replace(/[#*_`>-]/g, '').replace(/\n{2,}/g, '\n').trim();
        pdf.setFontSize(9.5); pdf.setTextColor(50);
        pdf.text(pdf.splitTextToSize(plain, W - 28), 14, 26);
      }

      pdf.save(`Dossier_${(proy.nombre_cliente || 'cocina').replace(/\s+/g, '_')}.pdf`);
    } catch (e) {
      alert('No se pudo generar el dossier: ' + (e.message || ''));
    } finally { setDossierBusy(false); }
    // eslint-disable-next-line
  }, [render.imageUrl, plano.b64, alzado.b64, ficha.md, proy, watermark, defaultLogo]);

  // ── Vista alámbrica (alzados por pared, con cotas) ──
  const genAlzado = useCallback(async () => {
    setAlzado(s => ({ ...s, status: 'loading', msg: 'Generando vista alámbrica…', b64: null }));
    try {
      const r = await apiPost('/alzado', { ...proy, distribucion_estructurada: distribucion });
      setAlzado(s => ({ ...s, status: 'success', msg: `Alzados generados (${r.paredes} pared/es)`, b64: r.alzadoBase64 }));
    } catch (err) {
      setAlzado(s => ({ ...s, status: 'error', msg: err.message }));
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
    { id: 'dossier', label: 'Ficha Fabricación', icon: <ClipboardList size={14}/> },
    { id: 'pres',   label: 'Presentación',  icon: <Presentation size={14}/> },
    { id: 'inst',   label: 'Instalaciones', icon: <Zap size={14}/> },
    { id: 'galeria', label: 'Galería',     icon: <FolderOpen size={14}/> },
  ];

  const ESTILOS = ['Moderno', 'Nórdico', 'Minimalista', 'Industrial', 'Clásico', 'Rústico', 'Contemporáneo', 'Japandi', 'Mediterráneo', 'High-Tech', 'Provenzal', 'Wabi-Sabi'];

  return (
    <div className={`flex flex-col h-full overflow-hidden transition-colors duration-200 ${t.root}`}>

      {/* Header */}
      <div className={`flex items-center gap-2 px-3 md:px-6 py-2.5 flex-shrink-0 ${t.header}`}>
        {/* Hamburguesa mobile */}
        <button onClick={() => setMobileMenuOpen(v => !v)}
          className={`lg:hidden flex items-center justify-center w-8 h-8 rounded-lg transition-all ${mobileMenuOpen ? 'bg-amber-600 text-white' : t.dlBtn}`}
          title="Abrir panel de proyecto">
          <LayoutGrid size={15}/>
        </button>
        <div className="p-1.5 rounded-xl bg-amber-600/20 hidden sm:flex">
          <ChefHat size={16} className="text-amber-500" />
        </div>
        <div className="flex-1 min-w-0">
          <h1 className={`text-xs font-black uppercase tracking-widest truncate ${t.title}`}>3D Estudio</h1>
          {proy.nombre_cliente && <p className={`text-[9px] truncate ${t.subtext}`}>{proy.nombre_cliente}</p>}
        </div>
        {/* Botones de proyecto — solo en mobile/tablet (en desktop van al panel derecho) */}
        <div className="flex lg:hidden items-center gap-1">
          <button onClick={openProjectList} title="Abrir proyecto" className={`flex items-center gap-1 px-2 py-1.5 rounded-lg text-[9px] font-black uppercase tracking-widest transition-all ${t.dlBtn}`}>
            <FolderOpen size={12}/> <span className="hidden md:inline">Proyectos</span>
          </button>
          <button onClick={saveProject} disabled={busySave} title="Guardar proyecto" className={`flex items-center gap-1 px-2 py-1.5 rounded-lg text-[9px] font-black uppercase tracking-widest transition-all ${savedId ? 'bg-emerald-600 text-white' : t.dlBtn}`}>
            {busySave ? <Loader2 size={12} className="animate-spin"/> : <Save size={12}/>}
          </button>
        </div>
        {/* Botón para abrir/cerrar panel derecho — solo desktop */}
        <button onClick={() => setRightOpen(v => !v)}
          className={`hidden lg:flex items-center justify-center w-8 h-8 rounded-lg transition-all ${rightOpen ? 'bg-amber-600/20 text-amber-600' : t.dlBtn}`}
          title={rightOpen ? 'Ocultar panel derecho' : 'Mostrar panel derecho'}>
          <ChevronRight size={15} className={`transition-transform ${rightOpen ? 'rotate-180' : ''}`}/>
        </button>
        <ThemeSelector mode={themeMode} onChange={handleThemeChange} t={t} />
      </div>

      {/* Overlay mobile para cerrar el sidebar al tocar fuera */}
      {mobileMenuOpen && (
        <div className="lg:hidden fixed inset-0 z-30 bg-black/40" onClick={() => setMobileMenuOpen(false)} />
      )}

      <div className="flex flex-1 overflow-hidden min-h-0 relative">

        {/* Sidebar — overlay en mobile, fijo en desktop */}
        <div className={`
          ${mobileMenuOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
          ${panelHidden ? 'lg:hidden' : ''}
          fixed lg:relative z-40 lg:z-auto
          top-0 left-0 h-full lg:h-auto
          w-72 lg:w-auto
          flex-shrink-0 min-h-0 p-4 flex flex-col gap-3 overflow-y-auto scrollbar-thin
          transition-transform duration-300 ease-in-out
          shadow-2xl lg:shadow-none
          ${t.sidebar}
        `} style={{overflowY:'auto', overflowX:'hidden', ...(isWide() && !panelHidden ? { width: panelW } : {})}}>
          {/* Cabecera del sidebar con botón de cierre en mobile */}
          <div className="flex items-center justify-between mb-1">
            <p className={`text-[9px] font-black uppercase tracking-widest ${t.sidebarSect}`}>Proyecto</p>
            <button onClick={() => setMobileMenuOpen(false)}
              className={`lg:hidden flex items-center justify-center w-7 h-7 rounded-lg transition-all ${t.dlBtn}`}
              title="Cerrar panel">
              <X size={14}/>
            </button>
          </div>

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
                      <p className={`text-[9px] font-black uppercase tracking-widest mt-1 ${t.sidebarSect}`}>Elementos por pared</p>
                      {distribucion.paredes.map((pared, pIdx) => (
                        <div key={pIdx} className={`rounded-lg p-1.5 mb-1 ${t.input}`}>
                          <p className={`text-[8px] font-bold mb-1 ${t.sidebarLabel}`}>{pared.nombre} ({pared.ancho}cm)</p>
                          <div className="flex flex-wrap gap-0.5 mb-1">
                            {ELEMENTOS_COCINA.map(e => (
                              <button key={e.id} onClick={() => addElemento(e.id, pIdx)}
                                className={`flex items-center gap-0.5 px-1 py-0.5 rounded text-[7px] font-medium transition-all ${t.input} hover:opacity-80`}
                                title={`Añadir ${e.label} (${e.ancho_default}cm) a ${pared.nombre}`}>
                                <span className="text-[10px]">{e.emoji}</span>
                              </button>
                            ))}
                          </div>
                          {distribucion.elementos.filter(el => el.pared_idx === pIdx).length > 0 && (
                            <div className="flex flex-col gap-0.5">
                              {distribucion.elementos.map((el, i) => el.pared_idx === pIdx ? (
                                <div key={i} className={`flex items-center gap-1 px-1 py-0.5 rounded text-[7px] ${t.card}`}>
                                  <span>{el.emoji}</span>
                                  <span className="flex-1 truncate">{el.label}</span>
                                  <span className={`${t.sidebarLabel}`}>{el.ancho}cm</span>
                                  <button onClick={() => removeElemento(i)} className="text-red-400 hover:text-red-300 text-[9px]">×</button>
                                </div>
                              ) : null)}
                            </div>
                          )}
                        </div>
                      ))}
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

        {/* Divisor redimensionable + ocultar panel (solo pantallas grandes) */}
        {!panelHidden ? (
          <div className="hidden lg:flex shrink-0 relative items-stretch">
            <div onMouseDown={() => { resizingPanel.current = true; document.body.style.userSelect = 'none'; }}
              title="Arrastra para redimensionar el panel"
              className="w-2 cursor-ew-resize bg-slate-200/40 hover:bg-amber-400/60 transition-colors duration-150 group">
              <div className="w-0.5 h-8 bg-slate-300 group-hover:bg-amber-500 rounded-full mx-auto mt-[calc(50%-1rem)] transition-colors"/>
            </div>
            <button onClick={() => setPanelHidden(true)} title="Ocultar panel lateral"
              className="absolute -right-3.5 top-1/2 -translate-y-1/2 z-10 w-7 h-14 bg-white border border-slate-200 rounded-r-xl flex items-center justify-center text-slate-400 hover:text-amber-600 hover:border-amber-400 shadow-md transition-all">
              <ChevronLeft size={14} />
            </button>
          </div>
        ) : (
          <button onClick={() => setPanelHidden(false)} title="Mostrar panel lateral"
            className="hidden lg:flex shrink-0 self-stretch items-center px-1.5 border-r border-slate-200 text-slate-400 hover:text-amber-600 hover:bg-amber-50 transition-all">
            <ChevronRight size={16} />
          </button>
        )}

        {/* Main */}
        <div className="flex-1 flex flex-col overflow-hidden min-h-0">

          {/* Tabs — scroll horizontal en mobile, iconos + labels en desktop */}
          <div className={`flex px-2 md:px-4 pt-2 gap-0.5 flex-shrink-0 overflow-x-auto scrollbar-none transition-colors duration-200 ${t.tabBar}`}
            style={{scrollbarWidth:'none', msOverflowStyle:'none'}}>
            {TABS.map(tb => (
              <button key={tb.id} onClick={() => setTab(tb.id)}
                className={`flex items-center gap-1 px-2 md:px-3 py-2 rounded-t-lg text-[9px] md:text-[10px] font-black uppercase tracking-widest transition-all flex-shrink-0 ${
                  tab === tb.id ? t.tabActive : t.tabInactive
                }`}>
                {tb.icon}
                <span className="hidden sm:inline">{tb.label}</span>
              </button>
            ))}
          </div>

          <div className="flex-1 min-h-0 overflow-y-auto p-3 md:p-5">

            {/* ── RENDER MANUS ── */}
            {tab === 'render' && (
              <div className="flex flex-col gap-4 max-w-2xl xl:max-w-3xl mx-auto">
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
                  <div className="grid grid-cols-3 sm:grid-cols-4 xl:grid-cols-6 gap-2">
                    {ESTILOS_RAPIDOS.map(s => (
                      <button key={s.id} onClick={() => applyStyle(s)}
                        className={`flex flex-col items-center gap-1 px-2 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${
                          selectedStyle === s.id ? t.styleBtnAct : t.styleBtn
                        }`}>
                        <span className="text-base">{s.emoji}</span>
                        <span className="text-center leading-tight">{s.label}</span>
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

                {/* Selector de motor IA — solo master */}
                {isMaster && (
                  <div className={`flex items-center gap-2 p-2 rounded-lg ${t.card}`}>
                    <span className={`text-[9px] font-black uppercase tracking-widest ${t.motorText} whitespace-nowrap`}>Motor</span>
                    <div className="flex bg-slate-100/10 rounded-lg p-0.5 gap-0.5 flex-1">
                      {[['ia1','IA 1','Motor principal (Gemini pro)'],['ia2','IA 2','Motor alternativo (Manus)'],['ia3','IA 3','Gemini flash — rápido'],['ia4','IA 4','Ultra-fotorrealista (prompt potenciado)']].map(([id,lbl,title]) => (
                        <button key={id} onClick={() => setMotorIA(id)} title={title}
                          className={`flex-1 py-1 rounded-md text-[9px] font-black transition-all ${
                            motorIA === id ? 'bg-indigo-600 text-white' : `${t.tabInactive}`
                          }`}>{lbl}</button>
                      ))}
                    </div>
                  </div>
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
                    <div className="flex items-center gap-1.5 flex-wrap">
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
                      {isMaster && (
                        <button onClick={() => setCompareAB(v => !v)}
                          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all ${
                            compareAB ? 'bg-indigo-600 text-white' : t.dlBtn
                          }`}
                          title="Comparativa A/B: genera un segundo render con el mismo prompt para comparar">
                          <Image size={11}/> A/B
                        </button>
                      )}
                    </div>
                    {/* Comparativa A/B — solo master */}
                    {isMaster && compareAB && (
                      <div className={`p-3 rounded-xl ${t.card} flex flex-col gap-2`}>
                        <div className="flex items-center justify-between">
                          <span className={`text-[9px] font-black uppercase tracking-widest ${t.motorText}`}>Comparativa A/B</span>
                          <button onClick={async () => {
                            setRenderB({ status: 'loading', msg: 'Generando render B…', imageUrl: null });
                            try {
                              const conCroquis = !!render.croquis && !freeDesign;
                              const partes = [proy.descripcion];
                              if (proy.notas?.trim()) partes.push(`Materiales: ${proy.notas.trim()}`);
                              if (!conCroquis && proy.medidas?.trim()) partes.push(`Medidas: ${proy.medidas.trim()}`);
                              let desc = partes.filter(Boolean).join('. ');
                              if (conCroquis) desc = `Genera un render 3D fotorrealista RESPETANDO el croquis adjunto. ${desc}`;
                              const descB = promptExtraMotor(desc);
                              const r = await fetch(`${API}/api/ai-engine/render`, {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${getToken()}` },
                                body: JSON.stringify({ description: descB, style: proy.estilo || undefined, provider: providerDeMotor(), referenceImage: conCroquis ? render.croquis : undefined }),
                              });
                              const d = await r.json().catch(() => ({}));
                              if (!r.ok || !d.success) throw new Error(d.error || 'Error en render B');
                              const u = d.result?.images?.[0] || d.imageUrl;
                              if (!u) throw new Error('Sin imagen');
                              const shown = String(u).startsWith('data:') ? u : ((await fetchAsBlob(u)) || imgSrc(u));
                              setRenderB({ status: 'success', msg: 'Render B listo', imageUrl: shown });
                            } catch (e) { setRenderB({ status: 'error', msg: e.message, imageUrl: null }); }
                          }} disabled={renderB.status === 'loading'}
                            className="flex items-center gap-1 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-lg text-[9px] font-black uppercase">
                            {renderB.status === 'loading' ? <Loader2 size={10} className="animate-spin"/> : <Sparkles size={10}/>} Generar B
                          </button>
                        </div>
                        {renderB.imageUrl && (
                          <div className="grid grid-cols-2 gap-2">
                            <div className="relative">
                              <img src={imgSrc(render.imageUrl)} alt="Render A" className="w-full rounded-lg object-contain"/>
                              <span className="absolute top-1 left-1 px-1.5 py-0.5 bg-amber-600 rounded text-[8px] font-black text-white">A</span>
                            </div>
                            <div className="relative">
                              <img src={imgSrc(renderB.imageUrl)} alt="Render B" className="w-full rounded-lg object-contain"/>
                              <span className="absolute top-1 left-1 px-1.5 py-0.5 bg-indigo-600 rounded text-[8px] font-black text-white">B</span>
                              <button onClick={() => { const a = document.createElement('a'); a.href = renderB.imageUrl; a.download = `render-B-${Date.now()}.png`; a.click(); }}
                                className="absolute bottom-1 right-1 p-1 bg-black/60 rounded text-white hover:bg-black">
                                <Download size={10}/>
                              </button>
                            </div>
                          </div>
                        )}
                        {renderB.status === 'error' && <p className="text-red-400 text-[9px]">{renderB.msg}</p>}
                      </div>
                    )}

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
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
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
              <div className="flex flex-col gap-4 max-w-2xl xl:max-w-3xl mx-auto">
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

                {/* ── Vista alámbrica: alzados acotados por pared (dossier / gremios) ── */}
                <div className={`mt-2 pt-4 border-t ${t.cardBorder}`}>
                  <h2 className={`text-sm font-black mb-1 ${t.title}`}>Vista alámbrica (alzados acotados)</h2>
                  <p className={`text-xs mb-3 ${t.subtext}`}>Alzado por pared en línea técnica con cotas de módulos y alturas (zócalo 10 · encimera 90 · altos 140–210). Para fábrica, electricistas y fontaneros.</p>
                  <button onClick={genAlzado} disabled={alzado.status === 'loading'}
                    className="flex items-center justify-center gap-2 w-full py-3 bg-slate-700 hover:bg-slate-600 disabled:opacity-50 rounded-xl text-sm font-black uppercase tracking-widest transition-all text-white">
                    {alzado.status === 'loading' ? <><Loader2 size={15} className="animate-spin"/> Generando alzados…</> : <><LayoutGrid size={15}/> Generar vista alámbrica</>}
                  </button>
                  <StatusBadge status={alzado.status} message={alzado.msg} t={t} />
                  {alzado.b64 && (
                    <>
                      <PrintPdfBar t={t} onPrint={() => handlePrint('alzado-print-area')} onPdf={() => handlePdfExport(`<img src="${alzado.b64}" style="width:100%"/>`, `alzados_${proy.nombre_cliente || 'cocina'}.pdf`)}
                        extraBtns={<a href={alzado.b64} download={`alzados_${proy.nombre_cliente || 'cocina'}.png`} className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all ${t.dlBtn}`}><Download size={11}/> PNG</a>} />
                      <div id="alzado-print-area" className={`relative group rounded-xl overflow-hidden border bg-white ${t.cardBorder}`}>
                        <img src={alzado.b64} alt="Alzados alámbricos" className="w-full object-contain" />
                        <div className="absolute top-2 right-2 flex gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button onClick={() => setAlzado(s => ({ ...s, fs: true }))} className={`p-1.5 rounded-lg ${t.dlBtn}`}><Maximize2 size={13}/></button>
                        </div>
                      </div>
                    </>
                  )}
                  {alzado.fs && (
                    <div className="fixed inset-0 bg-black/95 z-50 flex items-center justify-center p-4" onClick={() => setAlzado(s => ({ ...s, fs: false }))}>
                      <img src={alzado.b64} alt="Alzados" className="max-w-full max-h-full object-contain rounded-xl bg-white" />
                      <button className="absolute top-4 right-4 bg-white/10 p-2 rounded-full text-white"><X size={18}/></button>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* ── FICHA DE FABRICACIÓN (dossier técnico estilo estudio) ── */}
            {tab === 'dossier' && (
              <div className="max-w-3xl mx-auto">
                <FichaFabricacion proy={proy} logo={watermark.mode === 'custom' ? watermark.customLogo : defaultLogo} />
              </div>
            )}

            {/* ── FICHA TÉCNICA ── */}
            {tab === 'ficha' && (
              <div className="flex flex-col gap-4 max-w-2xl xl:max-w-3xl mx-auto">
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
              <div className="flex flex-col gap-4 max-w-2xl xl:max-w-4xl mx-auto">
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
                      <div className={`rounded-xl overflow-hidden border ${t.cardBorder}`} style={{ height: 'clamp(480px, 60vh, 800px)' }}>
                        <iframe srcDoc={pres.html} title="Presentación" className="w-full h-full" sandbox="allow-same-origin" />
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* ── INSTALACIONES ── */}
            {tab === 'inst' && (
              <div className="flex flex-col gap-4 max-w-2xl xl:max-w-3xl mx-auto">
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
                    <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-3">
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

        {/* ═══ PANEL DERECHO (solo desktop) ═══════════════════════════════════ */}
        <div className={`hidden lg:flex flex-col flex-shrink-0 transition-all duration-300 ease-in-out overflow-hidden border-l ${t.cardBorder} ${
          rightOpen ? (rightExpanded ? 'w-[340px]' : 'w-[220px]') : 'w-0'
        }`}>
          {rightOpen && (
            <div className={`flex flex-col h-full overflow-hidden ${t.sidebar}`}>
              {/* Cabecera del panel derecho */}
              <div className={`flex items-center justify-between px-3 py-2.5 flex-shrink-0 border-b ${t.cardBorder}`}>
                <p className={`text-[9px] font-black uppercase tracking-widest ${t.sidebarSect}`}>Acciones</p>
                <div className="flex items-center gap-1">
                  <button onClick={() => setRightExpanded(v => !v)}
                    title={rightExpanded ? 'Reducir panel' : 'Expandir panel'}
                    className={`flex items-center justify-center w-6 h-6 rounded transition-all ${t.dlBtn}`}>
                    <Maximize2 size={11}/>
                  </button>
                  <button onClick={() => setRightOpen(false)}
                    title="Ocultar panel"
                    className={`flex items-center justify-center w-6 h-6 rounded transition-all ${t.dlBtn}`}>
                    <X size={11}/>
                  </button>
                </div>
              </div>

              {/* Contenido scrollable */}
              <div className="flex-1 overflow-y-auto p-3 flex flex-col gap-4">

                {/* ── Proyecto ── */}
                <div className="flex flex-col gap-1.5">
                  <p className={`text-[8px] font-black uppercase tracking-widest ${t.sidebarSect}`}>Proyecto</p>
                  <button onClick={openProjectList}
                    className={`flex items-center gap-2 w-full px-3 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all ${t.dlBtn}`}>
                    <FolderOpen size={12}/> Abrir proyecto
                  </button>
                  <button onClick={saveProject} disabled={busySave}
                    className={`flex items-center gap-2 w-full px-3 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all ${
                      savedId ? 'bg-emerald-600 text-white' : t.dlBtn
                    }`}>
                    {busySave ? <Loader2 size={12} className="animate-spin"/> : <Save size={12}/>}
                    {savedId ? 'Guardado' : 'Guardar proyecto'}
                  </button>
                  <button onClick={() => { setProy({ nombre_cliente: '', descripcion: '', estilo: 'Moderno', medidas: '400x350cm isla 200x100cm', presupuesto: '', notas: '' }); setSavedId(null); setRender({ status: null, msg: '', imageUrl: null, originalUrl: null, croquis: null, croquisPrev: null, editMode: false, editTxt: '', fs: false }); setDistribucion(null); setSelectedStyle(null); setAttached(false); setCompareOn(false); setFreeDesign(false); setTranscrito(''); setBusySave(false); setWatermark({ mode: 'default', customLogo: null, customLogoPreview: null }); }}
                    className={`flex items-center gap-2 w-full px-3 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all ${t.dlBtn}`}>
                    <Plus size={12}/> Nuevo proyecto
                  </button>
                </div>

                {/* ── Exportar ── */}
                <div className="flex flex-col gap-1.5">
                  <p className={`text-[8px] font-black uppercase tracking-widest ${t.sidebarSect}`}>Exportar</p>
                  <button onClick={generarDossier} disabled={dossierBusy || !render.imageUrl}
                    className="flex items-center gap-2 w-full px-3 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all bg-slate-800 text-white hover:bg-slate-900 disabled:opacity-40">
                    {dossierBusy ? <Loader2 size={12} className="animate-spin"/> : <FileText size={12}/>} Dossier PDF
                  </button>
                  {render.imageUrl && (
                    <button onClick={downloadWithWatermark}
                      className={`flex items-center gap-2 w-full px-3 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all ${t.dlBtn}`}>
                      <Download size={12}/> Descargar PNG
                    </button>
                  )}
                </div>

                {/* ── Render (solo si hay imagen) ── */}
                {render.imageUrl && (
                  <div className="flex flex-col gap-1.5">
                    <p className={`text-[8px] font-black uppercase tracking-widest ${t.sidebarSect}`}>Render actual</p>
                    {/* Miniatura del render */}
                    <div className={`rounded-xl overflow-hidden border ${t.cardBorder} cursor-pointer`}
                      onClick={() => setRender(s => ({ ...s, fs: true }))}
                      title="Ver a pantalla completa">
                      <img src={imgSrc(render.imageUrl)} alt="Render" className="w-full object-cover" style={{maxHeight: rightExpanded ? '200px' : '130px'}}/>
                    </div>
                    <button onClick={guardarEnGaleria}
                      className="flex items-center gap-2 w-full px-3 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest bg-purple-600 hover:bg-purple-500 text-white transition-all">
                      <Save size={12}/> Guardar en galería
                    </button>
                    <button onClick={attachToBudget}
                      className={`flex items-center gap-2 w-full px-3 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all ${
                        attached ? 'bg-emerald-600 text-white' : 'bg-orange-500 hover:bg-orange-600 text-white'
                      }`}>
                      {attached ? <><CheckCircle size={12}/> Adjuntado</> : <><Send size={12}/> Al presupuesto</>}
                    </button>
                    {render.croquisPrev && (
                      <button onClick={() => setCompareOn(v => !v)}
                        className={`flex items-center gap-2 w-full px-3 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all ${
                          compareOn ? 'bg-slate-800 text-white' : t.dlBtn
                        }`}>
                        <Image size={12}/> {compareOn ? 'Ocultar comparativa' : 'Comparar croquis'}
                      </button>
                    )}
                    <button onClick={() => setRender(s => ({ ...s, editMode: !s.editMode }))}
                      className={`flex items-center gap-2 w-full px-3 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all ${
                        render.editMode ? 'bg-amber-600 text-white' : t.dlBtn
                      }`}>
                      <Edit3 size={12}/> {render.editMode ? 'Cancelar edición' : 'Editar render'}
                    </button>
                  </div>
                )}

                {/* ── Marca de agua (solo si hay render) ── */}
                {render.imageUrl && (
                  <div className="flex flex-col gap-1.5">
                    <p className={`text-[8px] font-black uppercase tracking-widest ${t.sidebarSect}`}>
                      <Stamp size={9} className="inline mr-1"/>Marca de agua
                    </p>
                    <div className="flex flex-col gap-1">
                      <button onClick={() => setWatermark(w => ({ ...w, mode: 'none' }))}
                        className={`flex items-center gap-2 w-full px-3 py-1.5 rounded-lg text-[9px] font-bold uppercase transition-all ${
                          watermark.mode === 'none' ? 'bg-red-500 text-white' : t.tabInactive
                        }`}>Sin marca</button>
                      <button onClick={() => setWatermark(w => ({ ...w, mode: 'default' }))}
                        className={`flex items-center gap-2 w-full px-3 py-1.5 rounded-lg text-[9px] font-bold uppercase transition-all ${
                          watermark.mode === 'default' ? 'bg-amber-600 text-white' : t.tabInactive
                        }`}>Logo ERP</button>
                      <button onClick={() => watermarkInputRef.current?.click()}
                        className={`flex items-center gap-2 w-full px-3 py-1.5 rounded-lg text-[9px] font-bold uppercase transition-all ${
                          watermark.mode === 'custom' ? 'bg-purple-600 text-white' : t.tabInactive
                        }`}>
                        <ImagePlus size={10}/> {watermark.customLogoPreview ? 'Cambiar logo' : 'Logo personalizado'}
                      </button>
                    </div>
                  </div>
                )}

                {/* ── Tema ── */}
                <div className="flex flex-col gap-1.5">
                  <p className={`text-[8px] font-black uppercase tracking-widest ${t.sidebarSect}`}>Apariencia</p>
                  <div className={`rounded-lg p-2 ${t.card}`}>
                    <ThemeSelector mode={themeMode} onChange={handleThemeChange} t={t} />
                  </div>
                </div>

              </div>
            </div>
          )}
        </div>
        {/* Botón flotante para reabrir el panel derecho cuando está cerrado */}
        {!rightOpen && (
          <button onClick={() => setRightOpen(true)}
            className={`hidden lg:flex absolute right-0 top-1/2 -translate-y-1/2 z-20 flex-col items-center justify-center w-6 h-20 rounded-l-xl shadow-lg border border-r-0 transition-all ${t.sidebar} ${t.cardBorder} hover:text-amber-600`}
            title="Mostrar panel de acciones">
            <ChevronLeft size={13}/>
          </button>
        )}

      </div>

      {/* Modal: Lista de proyectos guardados */}
      {Array.isArray(savedList) && (
        <div className="fixed inset-0 z-[9998] bg-black/50 flex items-center justify-center p-4" onClick={() => setSavedList(null)}>
          <div className={`rounded-2xl w-full max-w-lg max-h-[80vh] overflow-hidden flex flex-col ${t.root === 'bg-white text-slate-800' ? 'bg-white' : 'bg-[#1A1A1A]'}`} onClick={e => e.stopPropagation()}>
            <div className={`flex items-center justify-between px-5 py-4 border-b ${t.cardBorder}`}>
              <h3 className={`font-black ${t.title}`}>Mis proyectos 3D</h3>
              <button onClick={() => setSavedList(null)} className={`p-1.5 ${t.subtext} hover:opacity-70`}><X size={18} /></button>
            </div>
            {savedList.length > 0 && (
              <div className={`px-4 pt-3 pb-1`}>
                <input
                  autoFocus
                  value={savedSearch}
                  onChange={e => setSavedSearch(e.target.value)}
                  placeholder="Buscar por nombre o referencia…"
                  className={`w-full px-3 py-2 rounded-lg text-sm border ${t.cardBorder} ${t.card} ${t.title} focus:outline-none focus:ring-2 focus:ring-amber-500/40`}
                />
              </div>
            )}
            <div className="p-4 overflow-y-auto">
              {(() => {
                const q = savedSearch.trim().toLowerCase();
                const shown = q ? savedList.filter(d => `${d.cliente || ''} ${d.ref || ''}`.toLowerCase().includes(q)) : savedList;
                if (savedList.length === 0) return (
                <p className={`text-sm text-center py-8 ${t.subtext}`}>No tienes proyectos guardados todavía.</p>
                );
                if (shown.length === 0) return (
                <p className={`text-sm text-center py-8 ${t.subtext}`}>Sin resultados para “{savedSearch}”.</p>
                );
                return shown.map(d => (
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
                ));
              })()}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
