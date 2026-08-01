/**
 * AIRenderStudio - Componente de Render 3D con Voz + Texto
 * =========================================================
 * Permite al usuario describir una cocina por voz (micrófono) o texto,
 * y genera un render 3D fotorrealista usando el motor LuiggiAI.
 *
 * Características:
 * - Entrada por voz (Web Speech API) con indicador visual
 * - Entrada por texto libre
 * - Selector de materiales (formulario)
 * - Vista previa del render generado
 * - Historial de renders
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Mic, MicOff, Send, Image, Loader, Palette, RotateCcw, RotateCw, Download, Maximize2, X, Volume2, Wand2, CheckCircle, Save, FolderOpen, FileText, Trash2, Plus, ChevronLeft, ChevronRight, Upload, Share2, BookOpen, Layers, Sparkles, PlugZap, Droplet, Waves, Flame, Lightbulb, Tv, Wifi, Fan, Lamp, Ruler, Box, Zap } from 'lucide-react';
import { getToken } from '../services/api';
import { DOOR_FINISHES, MV_TARIFFS } from '../constants';
import { avgEurPerMl } from '../utils/pricing';
import { COLORES_1, COLORES_2, COLORES_3, porGama } from '../data/finishes';
import RecargarRenders from './RecargarRenders';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Tipos de marca de instalaciones para señalar sobre el render (gremios).
// `h` = altura estándar de la instalación (cm desde el suelo), que se muestra
// como COTA junto a cada punto. `Icon` = icono (no letras).
// Cada instalación indica en qué tipos de proyecto tiene sentido (`tipos`). Así la
// paleta de marcado y la detección automática se adaptan a cocina / armario / baño.
const MARK_TYPES = {
  enchufe:  { label: 'Enchufe', color: '#f59e0b', h: 110, Icon: PlugZap, tipos: ['cocina', 'armario', 'bano', 'otro'] },
  agua:     { label: 'Toma agua', color: '#0ea5e9', h: 50, Icon: Droplet, tipos: ['cocina', 'bano'] },
  desague:  { label: 'Desagüe', color: '#64748b', h: 40, Icon: Waves, tipos: ['cocina', 'bano'] },
  lavadora: { label: 'Toma lavadora', color: '#0891b2', h: 90, Icon: Droplet, tipos: ['cocina', 'bano'] },
  gas:      { label: 'Gas', color: '#ef4444', h: 55, Icon: Flame, tipos: ['cocina'] },
  luz:      { label: 'Punto de luz', color: '#eab308', h: 220, Icon: Lightbulb, tipos: ['cocina', 'armario', 'bano', 'otro'] },
  campana:  { label: 'Luz campana', color: '#334155', h: 160, Icon: Fan, tipos: ['cocina'] },
  vitrina:  { label: 'Luz vitrina', color: '#a855f7', h: 160, Icon: Lamp, tipos: ['cocina'] },
  toallero: { label: 'Toallero / radiador', color: '#f97316', h: 120, Icon: Flame, tipos: ['bano'] },
  tv:       { label: 'TV / antena', color: '#8b5cf6', h: 120, Icon: Tv, tipos: ['cocina', 'armario', 'otro'] },
  datos:    { label: 'Datos / red', color: '#10b981', h: 30, Icon: Wifi, tipos: ['cocina', 'armario', 'bano', 'otro'] },
};

// ─── Hook para Web Speech API ────────────────────────────────────────────────
// Reduce una imagen grande (foto de móvil) antes de guardarla/enviarla: evita
// que un base64 enorme sature memoria y tumbe la pestaña al analizarla/renderizar.
// Si el archivo no es una imagen rasterizable (p. ej. PDF), devuelve el original.
const downscaleImage = (file, maxDim = 1600, quality = 0.85) => new Promise((resolve, reject) => {
  const fr = new FileReader();
  fr.onload = () => {
    const original = fr.result;
    try {
      const img = new window.Image();
      img.onload = () => {
        try {
          const scale = Math.min(1, maxDim / Math.max(img.width, img.height));
          if (scale >= 1) { resolve(original); return; } // ya es pequeña
          const w = Math.round(img.width * scale), h = Math.round(img.height * scale);
          const canvas = document.createElement('canvas');
          canvas.width = w; canvas.height = h;
          canvas.getContext('2d').drawImage(img, 0, 0, w, h);
          resolve(canvas.toDataURL('image/jpeg', quality));
        } catch (_) { resolve(original); }
      };
      img.onerror = () => resolve(original); // no es imagen (PDF u otro) → original
      img.src = original;
    } catch (_) { resolve(original); }
  };
  fr.onerror = reject;
  fr.readAsDataURL(file);
});

function useSpeechRecognition() {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [isSupported, setIsSupported] = useState(false);
  const recognitionRef = useRef(null);
  // Acumulado SOLO de los resultados finales. El texto interino (en progreso)
  // NO se acumula: se muestra final + interino actual. Asi no se repite.
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
        // Recorrer SOLO los resultados nuevos desde resultIndex.
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const result = event.results[i];
          if (result.isFinal) {
            finalRef.current += result[0].transcript;  // los finales se acumulan UNA vez
          } else {
            interimTranscript += result[0].transcript;  // el interino es solo el actual
          }
        }
        // Mostrar lo confirmado + lo que se esta diciendo ahora (sin repetir).
        setTranscript(finalRef.current + interimTranscript);
      };

      recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

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

  return { isListening, transcript, isSupported, startListening, stopListening, resetTranscript, setTranscript };
}

// ─── Catálogo de materiales (sincronizado con backend) ───────────────────────
const MATERIALS = {
  layouts: [
    { id: 'L-shape', label: 'En L', icon: '⌐' },
    { id: 'U-shape', label: 'En U', icon: '⊔' },
    { id: 'island', label: 'Con Isla', icon: '◻' },
    { id: 'straight', label: 'Lineal', icon: '—' },
    { id: 'galley', label: 'Pasillo', icon: '‖' },
    { id: 'peninsula', label: 'Península', icon: '⊏' },
  ],
  countertops: [
    // Acabados reales de Luiggi Home (los más presupuestados) ─────────────
    { id: 'neolith_iron_corten', label: 'Neolith Iron Corten', erp: true },
    { id: 'neolith_calacatta', label: 'Neolith Calacatta', erp: true },
    { id: 'dekton_kelya', label: 'Dekton Kelya', erp: true },
    { id: 'dekton_sirius', label: 'Dekton Sirius (negro)', erp: true },
    { id: 'silestone_blanco', label: 'Silestone Blanco', erp: true },
    { id: 'porcelanico_marmol', label: 'Porcelánico efecto mármol', erp: true },
    // Genéricos ───────────────────────────────────────────────────────────
    { id: 'marble_white', label: 'Mármol Blanco' },
    { id: 'marble_black', label: 'Mármol Negro' },
    { id: 'granite_black', label: 'Granito Negro' },
    { id: 'quartz_white', label: 'Cuarzo Blanco' },
    { id: 'quartz_calacatta', label: 'Cuarzo Calacatta' },
    { id: 'wood_walnut', label: 'Madera Nogal' },
    { id: 'wood_oak', label: 'Madera Roble' },
    { id: 'concrete', label: 'Hormigón' },
    { id: 'dekton', label: 'Dekton' },
    { id: 'stainless_steel', label: 'Acero Inoxidable' },
  ],
  cabinets: [
    // Puertas reales de Luiggi Home ─────────────────────────────────────────
    { id: 'zenit_antracita', label: 'Puerta Zenit Antracita', erp: true },
    { id: 'mattdeco_cashmere', label: 'Puerta Mattdeco Cashmere', erp: true },
    { id: 'mattdeco_blanco', label: 'Puerta Mattdeco Blanco', erp: true },
    { id: 'spike', label: 'Puerta Spike', erp: true },
    { id: 'roble_aurora', label: 'Roble Aurora', erp: true },
    // Genéricos ─────────────────────────────────────────────────────────────
    { id: 'oak_natural', label: 'Roble Natural' },
    { id: 'oak_dark', label: 'Roble Oscuro' },
    { id: 'walnut', label: 'Nogal' },
    { id: 'white_matte', label: 'Blanco Mate' },
    { id: 'white_gloss', label: 'Blanco Brillo' },
    { id: 'grey_matte', label: 'Gris Mate' },
    { id: 'anthracite', label: 'Antracita' },
    { id: 'sage_green', label: 'Verde Sage' },
    { id: 'navy_blue', label: 'Azul Navy' },
    { id: 'black_matte', label: 'Negro Mate' },
  ],
  handles: [
    // Tiradores reales de Luiggi Home ───────────────────────────────────────
    { id: 'mallorca_negro', label: 'Tirador Mallorca Negro', erp: true },
    { id: 'gola', label: 'Perfil Gola (integrado)', erp: true },
    { id: 'fresado', label: 'Fresado (uñero)', erp: true },
    // Genéricos ─────────────────────────────────────────────────────────────
    { id: 'none', label: 'Sin Tirador (Push)' },
    { id: 'integrated', label: 'Integrado (Gola)' },
    { id: 'bar_black', label: 'Barra Negro' },
    { id: 'bar_brass', label: 'Barra Latón' },
    { id: 'bar_chrome', label: 'Barra Cromado' },
    { id: 'knob_black', label: 'Pomo Negro' },
    { id: 'knob_brass', label: 'Pomo Latón' },
  ],
  floors: [
    { id: 'wood_oak', label: 'Roble' },
    { id: 'wood_walnut', label: 'Nogal Espiga' },
    { id: 'tile_white', label: 'Porcelánico Blanco' },
    { id: 'tile_grey', label: 'Porcelánico Gris' },
    { id: 'tile_terracotta', label: 'Terracota' },
    { id: 'marble_white', label: 'Mármol' },
    { id: 'concrete', label: 'Hormigón Pulido' },
  ],
  styles: [
    { id: 'photorealistic', label: 'Fotorrealista' },
    { id: 'architectural', label: 'Arquitectónico' },
    { id: 'magazine', label: 'Revista' },
    { id: 'minimalist', label: 'Minimalista' },
    { id: 'warm', label: 'Cálido' },
    { id: 'industrial', label: 'Industrial' },
  ],
  appliances: [
    { id: 'fregadero_bajo', label: 'Fregadero bajo encimera', prompt: 'fregadero bajo encimera' },
    { id: 'grifo_extraible', label: 'Grifo extraíble', prompt: 'grifo monomando extraíble' },
    { id: 'placa_induccion', label: 'Placa de inducción', prompt: 'placa de inducción integrada en la encimera' },
    { id: 'campana_isla', label: 'Campana de isla', prompt: 'campana extractora de isla suspendida del techo' },
    { id: 'campana_decorativa', label: 'Campana decorativa', prompt: 'campana decorativa de pared' },
    { id: 'campana_integrada', label: 'Campana integrada', prompt: 'campana integrada oculta en el mueble' },
    { id: 'horno', label: 'Horno', prompt: 'horno empotrado en columna' },
    { id: 'microondas', label: 'Microondas', prompt: 'microondas empotrado' },
    { id: 'nevera_integrada', label: 'Nevera integrada', prompt: 'frigorífico integrado tras puerta de mueble' },
    { id: 'nevera_libre', label: 'Nevera libre (inox)', prompt: 'frigorífico americano de acero inoxidable' },
    { id: 'lavavajillas', label: 'Lavavajillas integrado', prompt: 'lavavajillas integrado' },
    { id: 'vinoteca', label: 'Vinoteca', prompt: 'vinoteca climatizada' },
  ],
  cameras: [
    { id: 'eyelevel', label: 'A la altura de los ojos', prompt: 'cámara a la altura de los ojos (1,6 m), vista desde la entrada de la estancia' },
    { id: 'wide', label: 'Gran angular', prompt: 'objetivo gran angular que muestra toda la estancia en una sola toma' },
    { id: 'aerial', label: 'Cenital elevada', prompt: 'vista ligeramente cenital y elevada, tipo axonométrica, para mostrar la distribución' },
    { id: 'detail', label: 'Detalle zona trabajo', prompt: 'plano de detalle de la zona de trabajo (encimera, fregadero y placa)' },
  ],
  lighting: [
    { id: 'natural', label: 'Natural (día)', prompt: 'luz natural de día entrando por las ventanas, cálida y equilibrada' },
    { id: 'sunset', label: 'Atardecer cálido', prompt: 'luz cálida de atardecer, tonos dorados, ambiente acogedor' },
    { id: 'neutral', label: 'Neutra estudio', prompt: 'iluminación neutra de estudio/catálogo, sin sombras duras' },
    { id: 'night', label: 'Nocturna', prompt: 'ambiente nocturno con la iluminación de la cocina encendida (luces LED bajo altos y focos)' },
    { id: 'bright', label: 'Muy iluminada', prompt: 'estancia muy luminosa y clara, luz difusa abundante' },
  ],
};

// Plantillas rápidas: escenas premium que los comerciales usan a menudo. Un clic
// rellena la descripción base y ajusta estilo, iluminación, cámara y equipamiento.
const PRESETS = [
  { id: 'blanca_isla', label: '⬜ Blanca con isla', desc: 'Cocina moderna con isla central, muebles lacados blanco mate sin tiradores (apertura push), encimera de piedra técnica blanca con canto recto e isla con zona de fregadero y taburetes.', style: 'photorealistic', lighting: 'natural', camera: 'wide', electros: ['fregadero_bajo', 'placa_induccion', 'campana_isla', 'horno', 'nevera_integrada'] },
  { id: 'antracita_office', label: '⬛ Antracita + office', desc: 'Cocina en L con office, frentes antracita mate, columna de horno y microondas, encimera oscura tipo Dekton, tirador gola integrado y banco de office con mesa.', style: 'photorealistic', lighting: 'sunset', camera: 'eyelevel', electros: ['fregadero_bajo', 'placa_induccion', 'campana_decorativa', 'horno', 'microondas'] },
  { id: 'madera_u', label: '🟫 Madera cálida en U', desc: 'Cocina en U de estilo cálido, frentes de roble natural con veta visible, encimera clara, tirador tipo uñero y luz LED bajo los muebles altos.', style: 'warm', lighting: 'sunset', camera: 'wide', electros: ['fregadero_bajo', 'placa_induccion', 'campana_integrada', 'horno'] },
  { id: 'min_negra', label: '◼ Minimalista negra', desc: 'Cocina minimalista lineal, frentes negro mate sin tiradores, encimera de piedra técnica negra continua con copete, campana integrada y electrodomésticos enrasados.', style: 'minimalist', lighting: 'neutral', camera: 'eyelevel', electros: ['fregadero_bajo', 'placa_induccion', 'campana_integrada', 'horno', 'nevera_integrada'] },
  { id: 'peninsula_gris', label: '▦ Península gris', desc: 'Cocina con península abierta al salón, frentes gris mate, encimera de cuarzo claro con canto recto, tiradores tipo barra negros y taburetes en la península.', style: 'magazine', lighting: 'bright', camera: 'wide', electros: ['fregadero_bajo', 'placa_induccion', 'campana_isla', 'horno', 'lavavajillas'] },
  // Tendencia 2026
  { id: 'warm_minimalism', label: '🌾 Warm Minimalism', desc: 'Cocina minimalista cálida con madera clara, líneas puras sin tiradores, encimera de piedra natural beige, iluminación indirecta y texturas orgánicas. Tendencia 2026.', style: 'warm', lighting: 'natural', camera: 'wide', electros: ['fregadero_bajo', 'placa_induccion', 'campana_integrada', 'horno'] },
  { id: 'joydrenching', label: '🎨 Joydrenching', desc: 'Cocina vibrante con color saturado en los frentes (terracota, verde bosque o azul profundo), combinada con madera y latón. Estilo atrevido y alegre, tendencia 2026.', style: 'magazine', lighting: 'bright', camera: 'eyelevel', electros: ['fregadero_bajo', 'placa_induccion', 'campana_decorativa', 'horno', 'vinoteca'] },
  { id: 'dark_luxury', label: '🔮 Dark Luxury', desc: 'Cocina de lujo oscura con frentes negros o antracita texturizados, encimera de mármol oscuro con veta dorada, grifoía negra mate y detalles en latón cepillado. Tendencia 2026.', style: 'photorealistic', lighting: 'night', camera: 'eyelevel', electros: ['fregadero_bajo', 'placa_induccion', 'campana_isla', 'horno', 'vinoteca', 'nevera_integrada'] },
  { id: 'japandi_2026', label: '🌿 Japandi', desc: 'Cocina Japandi con madera de fresno claro, líneas horizontales, cerámica artesanal en salpicadero, muebles bajos sin tiradores y altos abiertos con estantes. Tendencia 2026.', style: 'minimalist', lighting: 'natural', camera: 'wide', electros: ['fregadero_bajo', 'placa_induccion', 'campana_integrada', 'horno'] },
  { id: 'curvas_suaves', label: '➰ Curvas suaves', desc: 'Cocina con isla de bordes redondeados, frentes curvos en los extremos, colores suaves (crema, rosa empolvado), encimera con canto redondeado y campana esférica. Tendencia 2026.', style: 'architectural', lighting: 'bright', camera: 'wide', electros: ['fregadero_bajo', 'placa_induccion', 'campana_isla', 'horno', 'lavavajillas'] },
  // Armarios
  { id: 'vestidor_lujo', label: '👔 Vestidor', desc: 'Vestidor amplio con armarios empotrados de suelo a techo, puertas correderas lacadas blanco mate con tirador integrado, interior con barra doble, zapatero extraíble, cajones con divisores y espejo de cuerpo entero. Iluminación LED interior automática.', style: 'photorealistic', lighting: 'neutral', camera: 'wide', electros: [] },
  { id: 'corredera_moderna', label: '🚪 Corredera moderna', desc: 'Armario con puertas correderas de 3 hojas, acabado madera roble con franja central en cristal gris, perfil de aluminio negro mate, interior con módulos de estantes y barras a dos alturas.', style: 'minimalist', lighting: 'natural', camera: 'eyelevel', electros: [] },
  { id: 'dormitorio_completo', label: '🛏 Dormitorio completo', desc: 'Dormitorio con armario empotrado de pared a pared con puertas abatibles blancas, cabecero integrado con mesitas, y armario rinconero aprovechando toda la pared. Interior organizado con accesorios.', style: 'warm', lighting: 'sunset', camera: 'wide', electros: [] },
];

// Frases rápidas para enriquecer la descripción con un clic (detalles habituales).
const QUICK_PHRASES = [
  'isla central', 'península abierta al salón', 'columna de horno y microondas',
  'campana de isla', 'encimera volada para taburetes', 'zona de office con banco',
  'luz LED bajo los altos', 'fregadero bajo encimera', 'vinoteca integrada',
  'despensa/columna de almacenaje', 'copete a juego con la encimera', 'zócalo retranqueado',
  // Armarios
  'puertas correderas', 'interior con barra doble', 'zapatero extraíble',
  'cajones con divisores', 'espejo de cuerpo entero', 'LED interior automático',
  'rinconero aprovechando esquina', 'altillo con puertas abatibles',
];

// ─── Estimación de precio ORIENTATIVA (no es presupuesto) ────────────────────
// Precios medios por metro lineal / unidad; sirven para dar una cifra de partida
// al comercial. El presupuesto real se cierra en Resumen Totales / Cocina Desmontada.
const PRECIO_MUEBLE_ML = { premium: 980, medio: 730, base: 560 };
const CAB_TIER = {
  zenit_antracita: 'premium', mattdeco_cashmere: 'premium', mattdeco_blanco: 'premium',
  spike: 'premium', roble_aurora: 'premium', walnut: 'premium',
  oak_natural: 'medio', oak_dark: 'medio', white_gloss: 'medio', anthracite: 'medio',
  navy_blue: 'medio', sage_green: 'medio', black_matte: 'medio',
  white_matte: 'base', grey_matte: 'base',
};
const PRECIO_ELECTRO = {
  placa_induccion: 500, horno: 600, microondas: 300, campana_isla: 700,
  campana_decorativa: 400, campana_integrada: 350, nevera_integrada: 950,
  nevera_libre: 800, lavavajillas: 500, fregadero_bajo: 220, grifo_extraible: 150, vinoteca: 600,
};
function precioEncimeraMl(id) {
  const s = String(id || '').toLowerCase();
  if (s.includes('neolith') || s.includes('dekton')) return 350;
  if (s.includes('marble') || s.includes('marmol') || s.includes('calacatta')) return 400;
  if (s.includes('silestone') || s.includes('quartz') || s.includes('cuarzo')) return 260;
  if (s.includes('wood') || s.includes('madera')) return 210;
  if (s.includes('concrete') || s.includes('steel')) return 300;
  return 190; // porcelánico / genérico
}
const eur0 = (n) => `${Math.round(Number(n) || 0).toLocaleString('es-ES')} €`;

// Precio orientativo €/metro lineal de los muebles del Presupuestador 1, RESPETANDO
// la librería activa (MV = tarifas T1..T21 / ZC = zonas Z1..Z12), el bloque de tarifa
// según el acabado activo y el valor de punto POR librería. Mediana robusta.
function catalogoPrecioMuebleMl(state) {
  try {
    const cats = state?.catalogs || [];
    const active = state?.activeCatalogIds || [];
    if (!cats.length) return null;
    const lib = state?.currentLibrary || 'ZC';
    const isMV = lib === 'MV';
    const pv = Number(state?.libraryPointValues?.[lib]) || Number(state?.pointValueMontada) || 0;
    if (!pv) return null;
    // Columna de tarifa/zona activa según el acabado (globalFinish); si no, base.
    const finishName = state?.globalFinish;
    const table = isMV ? MV_TARIFFS : DOOR_FINISHES;
    const group = (table.find(f => f.name === finishName) || {}).group || (isMV ? 'T1' : 'Z1');
    const prods = cats
      .filter(c => active.includes(c.id) && (c.module === 'montada' || !c.module))
      .flatMap(c => c.products || []);
    // Usa el MISMO motor de precio del Presupuestador 1 (fuente única).
    const eurMl = avgEurPerMl(prods, { library: lib, finishName, pointValue: pv });
    if (!eurMl) return null;
    return { eurMl: Math.round(eurMl), lib, group };
  } catch { return null; }
}

// Cabecera de paso numerada para ordenar la petición de datos del render.
function StepHeader({ n, title, hint }) {
  return (
    <div className="flex items-start gap-2.5">
      <span className="shrink-0 w-6 h-6 rounded-full bg-indigo-600 text-white text-xs font-black flex items-center justify-center">{n}</span>
      <div className="leading-tight">
        <p className="text-xs font-black text-slate-700 uppercase tracking-wider">{title}</p>
        {hint && <p className="text-[11px] text-slate-400 font-medium">{hint}</p>}
      </div>
    </div>
  );
}

// ─── Componente Principal ────────────────────────────────────────────────────
// Tipos de mueble del Estudio 3D (deben coincidir con SettingsModal · ESTUDIO_3D_TIPOS).
const ESTUDIO_3D_TIPOS = [
  { id: 'cocina', label: 'Cocina' },
  { id: 'armario', label: 'Armario / Vestidor' },
  { id: 'bano', label: 'Baño' },
  { id: 'otro', label: 'Otro mueble' },
];

// Palabras clave que delatan un tipo de proyecto. Se usan para BLOQUEAR el render
// cuando el texto describe un tipo que el usuario NO tiene permitido (permisos por
// partidas). "otro" no tiene palabras: nunca bloquea. Búsqueda por límite de palabra.
const TIPO_KEYWORDS = {
  cocina: ['cocina', 'encimera', 'fregadero', 'placa', 'vitroceramica', 'vitrocerámica', 'induccion', 'inducción', 'campana', 'horno', 'fogon', 'fogón', 'isla de cocina', 'office'],
  armario: ['armario', 'armarios', 'vestidor', 'ropero', 'closet', 'clóset', 'baldas', 'zapatero', 'perchero', 'cajonera', 'barra de colgar'],
  bano: ['baño', 'bano', 'lavabo', 'inodoro', 'wc', 'ducha', 'bañera', 'banera', 'bidet', 'bidé', 'mampara', 'toallero', 'aseo'],
  otro: [],
};

// Ejemplo de la caja de descripción según el tipo de proyecto (no menciona tipos
// que el usuario no tiene contratados).
const PLACEHOLDER_TIPO = {
  cocina: "Describe tu cocina. Ej: 'Cocina en L blanca mate con isla, encimera de cuarzo, tiradores negros y columna de horno y microondas'",
  armario: "Describe tu armario o vestidor. Ej: 'Armario empotrado con puertas blancas lacadas, interior con columna de baldas, barras de colgar y cajonera'",
  bano: "Describe tu baño. Ej: 'Mueble de baño suspendido en roble, lavabo sobre encimera, espejo con luz y columna auxiliar'",
  otro: "Describe el mueble a medida. Ej: 'Estantería de salón a medida en roble con módulos cerrados y hueco para TV'",
};

export default function AIRenderStudio({ state, setState }) {
  const isMaster = state?.currentUser?.isAdmin === true;
  // Permiso específico para el giro 360º (o rol master). Si no lo tiene, ni se muestra el botón.
  const canUseRender360 = isMaster || state?.currentUser?.canUseRender360 === true;
  // Permiso específico para exportar a 4K (o rol master).
  const canUse4K = isMaster || state?.currentUser?.canUse4K === true;
  // Permiso específico para el amueblado virtual (o rol master).
  const canUseAmueblado = isMaster || state?.currentUser?.canUseAmueblado === true;
  // Permisos por partidas: qué tipos de mueble puede renderizar este usuario.
  // Admin o lista vacía/ausente = todos permitidos (compatibilidad hacia atrás).
  const tiposPermitidos = (() => {
    const sel = state?.currentUser?.estudio3dTipos;
    if (isMaster || !Array.isArray(sel) || sel.length === 0) return ESTUDIO_3D_TIPOS;
    return ESTUDIO_3D_TIPOS.filter(t => sel.includes(t.id));
  })();
  const [tipo3d, setTipo3d] = useState((tiposPermitidos[0] || ESTUDIO_3D_TIPOS[0]).id);
  const tipoActual = ESTUDIO_3D_TIPOS.find(t => t.id === tipo3d) || ESTUDIO_3D_TIPOS[0];
  const permitidoIds = tiposPermitidos.map(t => t.id);
  // Bloqueo por contenido: devuelve el tipo NO permitido que describe el texto, o null.
  // El master (todos los tipos) nunca se bloquea.
  const tipoNoPermitidoEnTexto = (texto) => {
    if (!texto || permitidoIds.length >= ESTUDIO_3D_TIPOS.length) return null;
    const t = ` ${texto.toLowerCase()} `;
    for (const tp of ESTUDIO_3D_TIPOS) {
      if (permitidoIds.includes(tp.id)) continue;
      const kws = TIPO_KEYWORDS[tp.id] || [];
      if (kws.some(k => t.includes(` ${k} `) || t.includes(` ${k},`) || t.includes(` ${k}.`) || t.includes(`${k}s `))) return tp;
    }
    return null;
  };
  // Cuenta coincidencias de palabras clave de un tipo en el texto.
  const contarTipo = (t, tid) => (TIPO_KEYWORDS[tid] || []).filter(k =>
    t.includes(` ${k} `) || t.includes(` ${k},`) || t.includes(` ${k}.`) || t.includes(`${k}s `)).length;
  // Tipo que MEJOR describe el texto (el de más coincidencias), o null.
  const tipoDelTexto = (texto) => {
    if (!texto) return null;
    const t = ` ${texto.toLowerCase()} `;
    let best = null, bestN = 0;
    for (const tp of ESTUDIO_3D_TIPOS) { const n = contarTipo(t, tp.id); if (n > bestN) { bestN = n; best = tp.id; } }
    return bestN > 0 ? best : null;
  };
  // Guard unificado: la descripción DEBE encajar con el tipo seleccionado y estar
  // permitida. Devuelve un mensaje de error (string) o null si todo correcto.
  // Aplica también al master: no se puede pedir un armario con "Cocina" elegida.
  const guardTipo = (texto) => {
    const det = tipoDelTexto(texto);
    if (!det || det === tipo3d) {
      // No se detecta otro tipo (o coincide): solo queda el filtro de permisos.
      const bloqueo = tipoNoPermitidoEnTexto(texto);
      return bloqueo ? `No puedes diseñar «${bloqueo.label}»: tu usuario no tiene ese tipo contratado. Solo puedes diseñar: ${tiposPermitidos.map(t => t.label).join(', ')}.` : null;
    }
    // El texto describe un tipo DISTINTO al seleccionado.
    const detLabel = ESTUDIO_3D_TIPOS.find(t => t.id === det).label;
    if (permitidoIds.includes(det)) {
      return `Tu descripción parece de «${detLabel}» pero tienes seleccionado «${tipoActual.label}». Cambia el «Tipo de proyecto» a «${detLabel}» (o ajusta la descripción) para generar el render.`;
    }
    return `No puedes diseñar «${detLabel}»: tu usuario no tiene ese tipo contratado. Solo puedes diseñar: ${tiposPermitidos.map(t => t.label).join(', ')}.`;
  };
  // Accesos temporales a otras herramientas de diseño (para el master), mientras
  // se unifica todo en Estudio 3D + Agentes.
  const OTRAS_HERRAMIENTAS = [
    { tab: 'agentesDisenadores', label: 'Agentes' },
    { tab: 'cocinasai', label: 'Cocinas IA 2' },
    { tab: 'kitchenDesigner', label: 'Diseñador 3D' },
    { tab: 'estudioCocinas', label: 'Estudio técnico' },
  ];
  const irA = (tab) => setState && setState(p => ({ ...p, currentTab: tab }));
  const [mode, setMode] = useState('natural'); // 'natural' | 'params'
  const [description, setDescription] = useState('');
  const [refImage, setRefImage] = useState(null); // imagen/PDF de referencia (base64) PRINCIPAL para que el modelo la "vea"
  const [refImages, setRefImages] = useState([]); // TODAS las referencias subidas (p.ej. una por pared) → un render por cada una
  const [originalRef, setOriginalRef] = useState(null); // PRIMERA imagen subida: se conserva para "Comparar" pase lo que pase
  const [floorPlan, setFloorPlan] = useState(null);    // plano en planta (dataURL)
  const [wallSketches, setWallSketches] = useState([]); // bocetos por pared (dataURL[])
  const [isGenerating, setIsGenerating] = useState(false);
  const [renderResult, setRenderResult] = useState(null);
  const [renderHistory, setRenderHistory] = useState([]);
  const [error, setError] = useState(null);
  // Créditos de IA del usuario (bolsa mensual ligada a su suscripción).
  const [aiCredits, setAiCredits] = useState(null);
  const [showFullscreen, setShowFullscreen] = useState(false);
  const [analyzingRef, setAnalyzingRef] = useState(false);
  // Guardado de proyectos (cliente + referencia) y descarga.
  const [cliente, setCliente] = useState('');
  const [ref, setRef] = useState('');
  const [savedId, setSavedId] = useState(null);
  const [savedList, setSavedList] = useState(null); // null = oculto
  const [savedSearch, setSavedSearch] = useState(''); // Buscador de proyectos por nombre/referencia
  const [selMode, setSelMode] = useState(false);      // modo "unir proyectos" (selección múltiple)
  const [selIds, setSelIds] = useState([]);           // ids de proyectos seleccionados para unir
  const [busy, setBusy] = useState(false);
  const [downloading, setDownloading] = useState(false);
  // Captura de medidas de la estancia (para proporción/escala reales).
  const [medidas, setMedidas] = useState({ ancho: '', fondo: '', altura: '', aberturas: '' });
  // Edición del render en lenguaje natural (iterar sin empezar de cero).
  const [editInstruction, setEditInstruction] = useState('');
  const [editLines, setEditLines] = useState([]); // multi-línea: instrucciones adicionales
  const [editing, setEditing] = useState(false);
  // Imagen de un ELEMENTO a copiar (una puerta, un mueble…) para incorporarlo.
  const [editRefImage, setEditRefImage] = useState(null);
  // Electrodomésticos, cámara y nº de variaciones (Tanda 3).
  const [electros, setElectros] = useState([]);
  const [camera, setCamera] = useState('eyelevel');
  const [variantCount, setVariantCount] = useState(1);
  // Motor de render: 'ia1' = Gemini (por defecto, más fiel), 'ia2' = Manus. Sin exponer nombres.
  const [motor, setMotor] = useState('ia1');
  const providerOf = () => (motor === 'ia2' ? 'manus' : 'gemini');
  const [attached, setAttached] = useState(false);
  const [compareOn, setCompareOn] = useState(false); // ver referencia vs render
  // Marcado de instalaciones sobre el render (para electricista/fontanero).
  const [markTool, setMarkTool] = useState(null);   // 'enchufe'|'agua'|'desague'|'gas'|null
  const [marks, setMarks] = useState([]);           // [{x,y,type}] en % del render
  const [detecting, setDetecting] = useState(false);
  const [schematic, setSchematic] = useState(false); // vista esquema (render atenuado)
  const [editMark, setEditMark] = useState(null);    // índice de la marca en edición
  const [showInstall, setShowInstall] = useState(false); // panel de instalaciones/planos plegado
  const [showOtras, setShowOtras] = useState(false); // barra master "otras herramientas" plegada
  const [watermarkOn, setWatermarkOn] = useState(false); // marca de agua con logo personalizado al descargar
  const markH = (mk) => (mk.h != null ? mk.h : MARK_TYPES[mk.type].h); // altura efectiva (cm)
  // Selector de color por catálogo (pestañas Colores 1/2 + gamas colapsables).
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [colorTab, setColorTab] = useState('c1');
  const [openGama, setOpenGama] = useState(null);
  const paletteData = colorTab === 'c1' ? COLORES_1 : colorTab === 'c2' ? COLORES_2 : COLORES_3;
  const gamas = porGama(paletteData);
  // Panel izquierdo redimensionable/ocultable (solo en pantallas grandes).
  const [panelW, setPanelW] = useState(420);
  const [panelHidden, setPanelHidden] = useState(false);
  // Saldo de renders y compra de packs (no caducan). Se abre solo al pulsar.
  const [verRecarga, setVerRecarga] = useState(false);
  const resizingPanel = useRef(false);
  // UX móvil: colapso de secciones avanzadas por defecto
  const [showEstilo, setShowEstilo] = useState(false);
  const [showPlanos, setShowPlanos] = useState(false);
  const [showMedidas, setShowMedidas] = useState(false);
  // Ref para auto-scroll al panel de render en móvil
  const renderPanelRef = useRef(null);
  const isWide = () => typeof window !== 'undefined' && window.innerWidth >= 1024;
  useEffect(() => {
    const onMove = (e) => { if (resizingPanel.current) setPanelW(Math.max(300, Math.min(760, e.clientX - 8))); };
    const onUp = () => { if (resizingPanel.current) { resizingPanel.current = false; document.body.style.userSelect = ''; } };
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
    return () => { window.removeEventListener('mousemove', onMove); window.removeEventListener('mouseup', onUp); };
  }, []);
  const [imgError, setImgError] = useState(false);    // la imagen del render no cargó
  // Visor orbital 360º: vistas de la misma cocina a distintos ángulos, girables con el ratón
  const [orbitFrames, setOrbitFrames] = useState([]);   // [dataURL] izquierda→derecha
  const [orbitIndex, setOrbitIndex] = useState(0);
  const [orbitLoading, setOrbitLoading] = useState(false);
  const [orbitOn, setOrbitOn] = useState(false);
  // Visor interactivo: zoom + pan
  const [interactiveMode, setInteractiveMode] = useState(false);
  const [zoom, setZoom] = useState(1);
  const [panX, setPanX] = useState(0);
  const [panY, setPanY] = useState(0);
  // Plan de instalaciones (colapsable)
  const [showInstallPlan, setShowInstallPlan] = useState(false);
  const [params, setParams] = useState({
    layout: 'L-shape',
    countertop: 'quartz_white',
    cabinets: 'white_matte',
    handles: 'bar_black',
    floor: 'wood_oak',
    style: 'photorealistic',
    lighting: 'natural',
    additional_details: '',
  });

  const { isListening, transcript, isSupported, startListening, stopListening, resetTranscript, setTranscript } = useSpeechRecognition();
  const textareaRef = useRef(null);
  // Texto que había en el campo al empezar a dictar: la voz se AÑADE a él, no lo pisa.
  const baseTextRef = useRef('');

  // Al cambiar de render, reseteamos el aviso de imagen no cargada.
  useEffect(() => { setImgError(false); setMarks([]); setMarkTool(null); setSchematic(false); setEditMark(null); setShowInstall(false); }, [renderResult]);

  // Preset entrante (p. ej. desde el Presupuestador de Armarios): fija el tipo y
  // rellena la descripción para arrancar el render de ese mueble. Se consume una vez.
  useEffect(() => {
    const preset = state?.estudio3dPreset;
    if (!preset) return;
    if (preset.tipo) setTipo3d(preset.tipo);
    if (preset.description) setDescription(preset.description);
    if (preset.cliente) setCliente(preset.cliente);
    if (preset.ref) setRef(preset.ref);
    if (setState) setState(p => { const { estudio3dPreset, ...rest } = p; return rest; });
  }, [state?.estudio3dPreset]); // eslint-disable-line

  // Detección AUTOMÁTICA de instalaciones con IA (analiza el render y coloca las
  // marcas de enchufes/agua/desagüe/gas donde irían).
  const detectInstalaciones = async (srcArg) => {
    const src = srcArg || currentImage(); if (!src || detecting) return;
    setDetecting(true); setError(null);
    try {
      // Reducir la imagen antes de enviar (un render 4K rompe la petición por tamaño).
      const dataUrl = await shrinkForSave(src);
      const r = await fetch(`${API_URL}/api/ai-engine/detect-installations`, {
        method: 'POST', headers: getAuthHeaders(), body: JSON.stringify({ imageBase64: dataUrl, tipo: tipo3d }),
      });
      if (!r.ok) { const e = await r.json().catch(() => ({})); throw new Error(e.detail || `Error ${r.status}`); }
      const d = await r.json();
      if (d.success) {
        // Filtra las marcas a las instalaciones que tienen sentido en este tipo
        // (p. ej. no dejar gas/campana en un baño aunque la IA lo devuelva).
        const validas = (d.marks || []).filter(m => MARK_TYPES[m.type]?.tipos?.includes(tipo3d));
        setMarks(validas); setMarkTool(null);
        if (validas.length) setSchematic(true);
        else setError('La IA no localizó puntos claros; márcalos a mano.');
      } else setError(d.detail || d.error || 'No se pudieron detectar las instalaciones.');
    } catch (e) { setError(`Error al detectar instalaciones: ${e?.message || 'fallo de conexión'}`); }
    finally { setDetecting(false); }
  };

  // Genera un GIRO 360º: varias vistas de la misma cocina a distintos ángulos para
  // moverla con el ratón (arrastrar izquierda/derecha).
  const generarOrbita = async () => {
    const src = currentImage(); if (!src || orbitLoading) return;
    setOrbitLoading(true); setError(null);
    try {
      const dataUrl = await imageToDataUrl(src);
      const r = await fetch(`${API_URL}/api/ai-engine/render/orbit`, {
        method: 'POST', headers: getAuthHeaders(),
        body: JSON.stringify({ referenceImage: dataUrl, projectType: tipo3d, n: 6 }),
      });
      const d = await r.json();
      if (d.success && (d.images || []).length >= 2) {
        setOrbitFrames(d.images); setOrbitIndex(Math.floor(d.images.length / 2)); setOrbitOn(true);
        setInteractiveMode(false);
      } else if (r.status === 402) {
        setError(d.detail || 'Sin créditos de IA para generar el giro 360º.');
      } else {
        setError(d.detail || d.error || 'No se pudo generar el giro. Inténtalo de nuevo.');
      }
    } catch { setError('Error al generar el giro 360º.'); }
    finally { setOrbitLoading(false); }
  };

  // Coloca una marca de instalación en el punto pulsado del render (% del box).
  const placeMark = (e) => {
    if (editMark !== null) { setEditMark(null); return; } // clic fuera cierra el editor
    if (!markTool || interactiveMode) return;
    const r = e.currentTarget.getBoundingClientRect();
    const x = ((e.clientX - r.left) / r.width) * 100;
    const y = ((e.clientY - r.top) / r.height) * 100;
    setMarks(m => [...m, { x, y, type: markTool }]);
  };

  // Descarga el render con las marcas de instalaciones "quemadas" y una leyenda.
  const descargarConMarcas = async () => {
    const src = currentImage(); if (!src) return;
    const dataUrl = await imageToDataUrl(src);
    const el = document.getElementById('render-annot-img');
    const cw = el?.offsetWidth || 1280, ch = el?.offsetHeight || 720;
    const im = new window.Image();
    im.onload = () => {
      const cv = document.createElement('canvas'); cv.width = cw; cv.height = ch;
      const ctx = cv.getContext('2d');
      ctx.fillStyle = '#e2e8f0'; ctx.fillRect(0, 0, cw, ch);
      const sc = Math.min(cw / im.width, ch / im.height);
      const dw = im.width * sc, dh = im.height * sc, dx = (cw - dw) / 2, dy = (ch - dh) / 2;
      ctx.drawImage(im, dx, dy, dw, dh);
      marks.forEach((mk) => {
        const t = MARK_TYPES[mk.type]; const x = mk.x / 100 * cw, y = mk.y / 100 * ch;
        // Punto (círculo de color, sin letra)
        ctx.beginPath(); ctx.arc(x, y, 8, 0, Math.PI * 2); ctx.fillStyle = t.color; ctx.fill();
        ctx.lineWidth = 2; ctx.strokeStyle = '#fff'; ctx.stroke();
        // Cota de altura junto al punto (usa la altura editada si la hay)
        const cota = `${markH(mk)} cm`;
        ctx.font = 'bold 11px sans-serif'; const tw = ctx.measureText(cota).width;
        ctx.fillStyle = 'rgba(255,255,255,.92)'; ctx.fillRect(x + 11, y - 8, tw + 8, 16);
        ctx.fillStyle = t.color; ctx.textAlign = 'left'; ctx.textBaseline = 'middle'; ctx.fillText(cota, x + 15, y + 0.5);
      });
      // Leyenda con color, nombre y altura estándar (sin letras)
      const used = [...new Set(marks.map(m => m.type))];
      let ly = ch - 10 - used.length * 18;
      used.forEach((tp) => {
        const t = MARK_TYPES[tp];
        ctx.fillStyle = 'rgba(0,0,0,.6)'; ctx.fillRect(10, ly - 12, 210, 18);
        ctx.beginPath(); ctx.arc(24, ly - 3, 6, 0, Math.PI * 2); ctx.fillStyle = t.color; ctx.fill();
        ctx.fillStyle = '#fff'; ctx.textAlign = 'left'; ctx.font = '11px sans-serif'; ctx.textBaseline = 'middle';
        ctx.fillText(`${t.label} · h ${t.h} cm · x${marks.filter(m => m.type === tp).length}`, 36, ly - 2.5);
        ly += 18;
      });
      const a = document.createElement('a'); a.href = cv.toDataURL('image/png');
      a.download = `render_instalaciones_${(cliente || ref || 'cocina').replace(/\s+/g, '_')}.png`; a.click();
    };
    im.src = dataUrl;
  };

  // Convierte un color hex (#rrggbb) a {r,g,b} para jsPDF.
  const hexToRgb = (hex) => {
    const m = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex || '');
    return m ? { r: parseInt(m[1], 16), g: parseInt(m[2], 16), b: parseInt(m[3], 16) } : { r: 100, g: 116, b: 139 };
  };

  // Devuelve la imagen del render con las marcas de instalaciones "quemadas"
  // (punto + cota de altura), en alta resolución, como dataURL. Reutilizable para
  // descargar o para el PDF de gremio.
  const renderMarcadoDataUrl = (scale = 2) => new Promise(async (resolve) => {
    const src = currentImage(); if (!src) return resolve(null);
    const dataUrl = await imageToDataUrl(src);
    const el = document.getElementById('render-annot-img');
    const cw = (el?.offsetWidth || 1280) * scale, ch = (el?.offsetHeight || 720) * scale;
    const im = new window.Image();
    im.onload = () => {
      const cv = document.createElement('canvas'); cv.width = cw; cv.height = ch;
      const ctx = cv.getContext('2d');
      ctx.fillStyle = '#e2e8f0'; ctx.fillRect(0, 0, cw, ch);
      const sc = Math.min(cw / im.width, ch / im.height);
      const dw = im.width * sc, dh = im.height * sc, dx = (cw - dw) / 2, dy = (ch - dh) / 2;
      ctx.drawImage(im, dx, dy, dw, dh);
      marks.forEach((mk) => {
        const t = MARK_TYPES[mk.type]; const x = mk.x / 100 * cw, y = mk.y / 100 * ch;
        ctx.beginPath(); ctx.arc(x, y, 8 * scale, 0, Math.PI * 2); ctx.fillStyle = t.color; ctx.fill();
        ctx.lineWidth = 2 * scale; ctx.strokeStyle = '#fff'; ctx.stroke();
        const cota = `${markH(mk)} cm`;
        ctx.font = `bold ${11 * scale}px sans-serif`; const tw = ctx.measureText(cota).width;
        ctx.fillStyle = 'rgba(255,255,255,.92)'; ctx.fillRect(x + 11 * scale, y - 8 * scale, tw + 8 * scale, 16 * scale);
        ctx.fillStyle = t.color; ctx.textAlign = 'left'; ctx.textBaseline = 'middle'; ctx.fillText(cota, x + 15 * scale, y + 0.5);
      });
      resolve(cv.toDataURL('image/png'));
    };
    im.onerror = () => resolve(null);
    im.src = dataUrl;
  });

  // ─── PDF de ESQUEMA PARA EL GREMIO (fontanero/electricista) ─────────────────
  const esquemaGremioPDF = async () => {
    if (!currentImage()) return;
    if (!marks.length) { setError('No hay tomas marcadas. Pulsa «Detectar auto (IA)» o márcalas a mano antes de generar el esquema.'); return; }
    setDownloading(true);
    try {
      const img = await renderMarcadoDataUrl(2);
      if (!img) { setError('No se pudo preparar la imagen del esquema.'); return; }
      const { jsPDF } = await import('jspdf');
      const pdf = new jsPDF({ orientation: 'landscape', unit: 'mm', format: 'a4' });
      const W = pdf.internal.pageSize.getWidth(), H = pdf.internal.pageSize.getHeight(), M = 12;
      // Cabecera
      const logo = state?.logo;
      if (logo && typeof logo === 'string' && logo.startsWith('data:')) {
        try { const fmt = logo.includes('image/png') ? 'PNG' : (logo.includes('image/webp') ? 'WEBP' : 'JPEG'); pdf.addImage(logo, fmt, M, 8, 28, 14); } catch (_) {}
      }
      pdf.setFont(undefined, 'bold'); pdf.setFontSize(15); pdf.setTextColor(20, 30, 60);
      pdf.text('ESQUEMA DE INSTALACIONES — GREMIO', W - M, 14, { align: 'right' });
      pdf.setFont(undefined, 'normal'); pdf.setFontSize(9); pdf.setTextColor(110);
      const sub = [cliente && `Cliente: ${cliente}`, ref && `Ref: ${ref}`, new Date().toLocaleDateString('es-ES')].filter(Boolean).join('   ·   ');
      pdf.text(sub, W - M, 20, { align: 'right' });
      // Imagen del render con marcas (columna izquierda)
      const imgW = W * 0.66 - M, areaY = 28, areaH = H - areaY - 14;
      const props = pdf.getImageProperties(img);
      const ratio = Math.min(imgW / props.width, areaH / props.height);
      const iw = props.width * ratio, ih = props.height * ratio;
      pdf.addImage(img, 'PNG', M, areaY, iw, ih);
      // Tabla de tomas (columna derecha)
      const tx = M + imgW + 6; let ty = areaY + 2;
      pdf.setFont(undefined, 'bold'); pdf.setFontSize(10); pdf.setTextColor(20, 30, 60);
      pdf.text('TOMAS A DEJAR', tx, ty); ty += 6;
      pdf.setFontSize(7.5); pdf.setTextColor(130); pdf.setFont(undefined, 'normal');
      pdf.text('Alturas orientativas desde suelo terminado.', tx, ty); ty += 6;
      const used = [...new Set(marks.map(m => m.type))];
      used.forEach((tp) => {
        const t = MARK_TYPES[tp]; const n = marks.filter(m => m.type === tp).length;
        const rgb = hexToRgb(t.color);
        pdf.setFillColor(rgb.r, rgb.g, rgb.b); pdf.circle(tx + 2, ty - 1.2, 1.8, 'F');
        pdf.setTextColor(40); pdf.setFont(undefined, 'bold'); pdf.setFontSize(9);
        pdf.text(`${t.label}`, tx + 6, ty);
        pdf.setFont(undefined, 'normal'); pdf.setTextColor(110); pdf.setFontSize(8);
        pdf.text(`x${n}   ·   h ${t.h} cm`, tx + 6, ty + 4);
        ty += 9.5;
      });
      // Total y pie
      ty += 2; pdf.setDrawColor(220); pdf.line(tx, ty, W - M, ty); ty += 5;
      pdf.setFont(undefined, 'bold'); pdf.setFontSize(9); pdf.setTextColor(20, 30, 60);
      pdf.text(`Total puntos: ${marks.length}`, tx, ty);
      pdf.setFontSize(7); pdf.setTextColor(150); pdf.setFont(undefined, 'normal');
      pdf.text(pdf.splitTextToSize('Esquema orientativo generado por IA para coordinación con el gremio. Verificar in situ.', W - M - tx), tx, H - 12);
      pdf.save(`esquema_gremio_${(cliente || ref || 'cocina').replace(/\s+/g, '_')}.pdf`);
    } catch (e) { setError('No se pudo generar el esquema: ' + (e.message || '')); }
    finally { setDownloading(false); }
  };

  // La transcripción se concatena al texto base (lo escrito antes de dictar).
  useEffect(() => {
    if (transcript) {
      const base = baseTextRef.current;
      setDescription(base ? `${base.trim()} ${transcript}` : transcript);
    }
  }, [transcript]);

  // Dictado independiente para el cuadro de EDICIÓN (cambios sobre el render).
  const editSp = useSpeechRecognition();
  const editBaseRef = useRef('');
  useEffect(() => {
    if (editSp.transcript) {
      const base = editBaseRef.current;
      setEditInstruction(base ? `${base.trim()} ${editSp.transcript}` : editSp.transcript);
    }
  }, [editSp.transcript]);
  const toggleEditMic = () => {
    if (editSp.isListening) { editSp.stopListening(); return; }
    editBaseRef.current = editInstruction || '';
    editSp.resetTranscript();
    editSp.startListening();
  };
  // Sube una imagen de elemento (puerta, mueble…) para copiarla en la cocina.
  const onEditRefUpload = async (e) => {
    const f = e.target.files?.[0]; e.target.value = '';
    if (!f) return;
    try { setEditRefImage(await downscaleImage(f)); }
    catch { setError('No se pudo leer la imagen del elemento.'); }
  };
  // Pegar una imagen del portapapeles (Ctrl+V):
  // - Si NO hay render generado todavía → se usa como REFERENCIA principal (mismo flujo que subir archivo).
  // - Si YA hay render → se usa como elemento de edición (editRefImage).
  const captureClipboardImage = async (e) => {
    const items = (e.clipboardData || e.originalEvent?.clipboardData)?.items || [];
    for (const it of items) {
      if (it.type && it.type.startsWith('image/')) {
        const file = it.getAsFile();
        if (!file) continue;
        e.preventDefault();
        try {
          const b64 = await downscaleImage(file);
          if (!renderResult) {
            // Sin render → añadir como referencia (varias pegadas = varias referencias)
            setAnalyzingRef(true);
            try { await addReference(b64, 'pegada'); }
            finally { setAnalyzingRef(false); }
          } else {
            // Con render → usar como elemento de edición
            setEditRefImage(b64);
          }
        } catch { setError('No se pudo pegar la imagen.'); }
        return true;
      }
    }
    return false;
  };
  // Ctrl+V en cualquier parte del Estudio pega una imagen del portapapeles como
  // elemento (no interfiere con pegar texto: solo actúa si hay imagen).
  useEffect(() => {
    const handler = (e) => { captureClipboardImage(e); };
    window.addEventListener('paste', handler);
    return () => window.removeEventListener('paste', handler);
    // eslint-disable-next-line
  }, []);

  const getAuthHeaders = () => {
    const token = getToken();
    return { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };
  };

  // Créditos de IA del usuario: se consultan al montar y tras cada generación.
  const fetchCredits = useCallback(async () => {
    try {
      const r = await fetch(`${API_URL}/api/ai-engine/my-credits`, { headers: getAuthHeaders() });
      if (r.ok) setAiCredits(await r.json());
    } catch { /* silencioso: el contador nunca rompe la UI */ }
  }, []);
  useEffect(() => { fetchCredits(); }, [fetchCredits]);

  // Las imágenes del render se sirven por el proxy interno (marca blanca). Como
  // un <img> no puede enviar cabeceras, el token JWT viaja como query param.
  // Al cambiar el render base, descarta el giro 360º anterior (era de otra cocina).
  useEffect(() => {
    setOrbitFrames([]); setOrbitOn(false); setOrbitIndex(0);
  }, [renderResult?.result?.images?.[0]]); // eslint-disable-line

  const assetSrc = (path) => {
    if (!path) return path;
    if (typeof path === 'string' && path.startsWith('/api/ai-engine/asset')) {
      const token = getToken() || '';
      return `${API_URL}${path}&t=${encodeURIComponent(token)}`;
    }
    return path;
  };

  // Descarga la imagen del render (o de una miniatura) como dataURL, para
  // guardar/PDF. Sirve tanto para dataURL directas como para el proxy con token.
  const imageToDataUrl = async (path) => {
    if (!path) return null;
    if (typeof path === 'string' && path.startsWith('data:')) return path;
    const resp = await fetch(assetSrc(path));
    const blob = await resp.blob();
    return await new Promise((res, rej) => {
      const fr = new FileReader();
      fr.onload = () => res(fr.result);
      fr.onerror = rej;
      fr.readAsDataURL(blob);
    });
  };

  const currentImage = () => renderResult?.result?.images?.[0] || null;

  // Construye una frase con las medidas de la estancia para dar escala real al
  // render (proporción de muebles, altura de altos, pasillos, etc.).
  const medidasTexto = () => {
    const parts = [];
    if (medidas.ancho) parts.push(`ancho ${medidas.ancho} cm`);
    if (medidas.fondo) parts.push(`fondo ${medidas.fondo} cm`);
    if (medidas.altura) parts.push(`altura de techo ${medidas.altura} cm`);
    let t = '';
    if (parts.length) t += `Medidas reales de la estancia: ${parts.join(', ')}. Respeta estas proporciones y la escala del mobiliario. `;
    if (medidas.aberturas.trim()) t += `Ventanas/puertas: ${medidas.aberturas.trim()}. `;
    return t;
  };
  // Electrodomésticos y punto de vista → frase para el prompt.
  const electrosTexto = () => {
    const sel = MATERIALS.appliances.filter(a => electros.includes(a.id)).map(a => a.prompt);
    return sel.length ? `Incluye estos electrodomésticos: ${sel.join(', ')}. ` : '';
  };
  const camaraTexto = () => {
    const c = MATERIALS.cameras.find(x => x.id === camera);
    return c ? `Punto de vista: ${c.prompt}. ` : '';
  };
  const luzTexto = () => {
    const l = MATERIALS.lighting.find(x => x.id === params.lighting);
    return l ? `Iluminación: ${l.prompt}. ` : '';
  };
  const conMedidas = (desc) => {
    const extra = `${medidasTexto()}${electrosTexto()}${camaraTexto()}${luzTexto()}`.trim();
    const conExtra = extra ? `${extra}\n${desc}` : desc;
    // Contexto de tipo de mueble (permisos por partidas): guía al motor de IA.
    return `[Tipo de proyecto: ${tipoActual.label}]\n${conExtra}`;
  };

  // Estimación de precio ORIENTATIVA a partir de medidas + materiales + equipamiento.
  const estimarPrecio = () => {
    const anchoM = (Number(medidas.ancho) || 0) / 100;
    const fondoM = (Number(medidas.fondo) || 0) / 100;
    const sinMedidas = !anchoM && !fondoM;
    let ml = anchoM + (fondoM > 0 ? fondoM : 0);
    if (!ml) ml = 4; // por defecto si no hay medidas
    ml = Math.min(Math.max(ml, 2), 14);
    const tier = CAB_TIER[params.cabinets] || 'medio';
    const cat = catalogoPrecioMuebleMl(state); // {eurMl, lib, group} del Presupuestador 1
    const precioMuebleMl = (cat && cat.eurMl) || PRECIO_MUEBLE_ML[tier] || PRECIO_MUEBLE_ML.medio;
    const muebles = ml * precioMuebleMl;
    const encimera = ml * precioEncimeraMl(params.countertop);
    const electro = electros.reduce((s, id) => s + (PRECIO_ELECTRO[id] || 0), 0);
    const tiradores = (params.handles === 'none' || params.handles === 'gola') ? ml * 45 : ml * 25;
    const montaje = 350;
    const subtotal = muebles + encimera + electro + tiradores + montaje;
    const round100 = (v) => Math.round(v / 100) * 100;
    return {
      ml: Math.round(ml * 10) / 10,
      muebles, encimera, electro, tiradores, montaje,
      min: round100(subtotal * 0.9), max: round100(subtotal * 1.15),
      deCatalogo: !!(cat && cat.eurMl), precioMuebleMl,
      lib: cat?.lib, group: cat?.group, sinMedidas,
    };
  };
  const toggleElectro = (id) => setElectros(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  // Aplica una plantilla: rellena la descripción (si está vacía) y ajusta ambiente.
  // Las plantillas rápidas son de COCINA y generan DESDE CERO: se fija el tipo a
  // cocina y se limpia cualquier imagen de referencia/edición previa (p.ej. un
  // armario anterior) para que NO entre en modo edición y salga una cocina.
  const applyPreset = (p) => {
    setDescription(prev => prev.trim() ? `${prev.trim()}\n${p.desc}` : p.desc);
    setParams(prm => ({ ...prm, style: p.style, lighting: p.lighting }));
    setCamera(p.camera);
    setElectros(p.electros || []);
    setTipo3d('cocina');
    setRefImage(null); setRefImages([]); setEditRefImage(null); setOriginalRef(null);
  };
  // Añade una frase rápida al final de la descripción.
  const addPhrase = (t) => setDescription(prev => {
    const has = prev.toLowerCase().includes(t.toLowerCase());
    if (has) return prev;
    return prev.trim() ? `${prev.trim()}, ${t}` : t;
  });

  // Genera una variante del render actual cambiando SOLO el color de los muebles.
  const colorVariant = async (colorInput) => {
    const img = currentImage();
    if (!img || editing) return;
    // Acepta una etiqueta simple o un objeto de acabado {label, modelo, forma}.
    const fin = (colorInput && typeof colorInput === 'object') ? colorInput : { label: colorInput };
    const colorLabel = fin.label || '';
    // Si el acabado lleva modelo+forma de puerta, se lo indicamos al render para
    // que cambie también la forma del frente, no solo el color.
    const cambio = (fin.modelo || fin.forma)
      ? `Cambia los frentes de los muebles al modelo de puerta "${fin.modelo || colorLabel}" (forma: ${fin.forma || 'según catálogo'})${fin.material ? `, en ${fin.material}` : ''}, con acabado/color "${colorLabel}". Respeta EXACTAMENTE la misma distribución, medidas, encimera, electrodomésticos, suelo, cámara e iluminación; solo cambian los frentes (forma y color).`
      : `Cambia ÚNICAMENTE el color/acabado de los frentes de los muebles a "${colorLabel}", manteniendo EXACTAMENTE el mismo diseño, distribución, encimera, tiradores, electrodomésticos, suelo, cámara e iluminación. No cambies nada más.`;
    setEditing(true); setError(null);
    try {
      const dataUrl = await imageToDataUrl(img);
      const response = await fetch(`${API_URL}/api/ai-engine/render`, {
        method: 'POST', headers: getAuthHeaders(),
        body: JSON.stringify({
          description: cambio,
          style: params.style,
          provider: providerOf(),
          referenceImage: dataUrl,
        }),
      });
      const data = await response.json();
      if (data.success) {
        const etiqueta = (fin.modelo || fin.forma) ? `${fin.modelo || ''} · ${colorLabel}`.trim() : colorLabel;
        let finalImg = data.result?.images?.[0];
        try { finalImg = await keepResolution(await imageToDataUrl(finalImg), dataUrl); } catch { /* si falla, se usa la original */ }
        const merged = { ...data, result: { ...data.result, images: [finalImg] }, description: `${renderResult?.description || description}\n[Puerta] ${etiqueta}` };
        setRenderResult(merged);
        setRenderHistory(prev => [{ ...merged, timestamp: new Date() }, ...prev].slice(0, 12));
      } else setError(data.error || 'No se pudo generar la variante de color');
    } catch { setError('Error de conexión al generar la variante.'); }
    finally { setEditing(false); }
  };

  // Construye el prompt de la LÁMINA TÉCNICA según el tipo de proyecto. Cada tipo
  // tiene su propia composición y sus reglas (la campana solo aplica a cocina).
  const fichaPromptPorTipo = (tid) => {
    // REGLA DE ORO (ver CLAUDE.md): un modelo de IMAGEN nunca escribe cotas — las
    // inventa. Esta lámina es solo la PARTE GRÁFICA (vistas limpias sin números);
    // las medidas reales las dibuja el motor vectorial determinista del backend.
    const base = 'Composición de lámina de estudio profesional, fondo claro, estilo dibujo técnico limpio. Formato 16:9.';
    const SIN_COTAS = '\nPROHIBIDO ESCRIBIR MEDIDAS: no dibujes líneas de cota, ni cifras, ni números, ni etiquetas de dimensión, ni escalas, ni texto de medidas en ninguna parte de la imagen. Las cotas se añaden aparte con un plano vectorial acotado. Si dibujas números, la lámina se descarta.';
    if (tid === 'armario') {
      return (
        'Crea una LÁMINA de ESTE armario/vestidor (usa la imagen adjunta como referencia FIEL: mismos módulos, acabados y distribución interior). ' + base + '\n'
        + '- ARRIBA: el FRENTE/ALZADO del armario, con los módulos claramente separados.\n'
        + '- CENTRO: el ALZADO INTERIOR (puertas abiertas) mostrando baldas, barras de colgar, cajones y altillos.\n'
        + '- ABAJO CENTRO: la PLANTA (vista cenital).\n'
        + '- DERECHA: recuadro "ACABADOS" (frentes, tiradores, interior, iluminación LED, detalles).\n'
        + 'REGLAS: NO dibujes campana, placa ni fregadero (es un armario). Baldas y barras a alturas ergonómicas coherentes.' + SIN_COTAS
      );
    }
    if (tid === 'bano') {
      return (
        'Crea una LÁMINA de ESTE mueble/espacio de baño (usa la imagen adjunta como referencia FIEL: mismos elementos, acabados y distribución). ' + base + '\n'
        + '- ARRIBA: el FRENTE/ALZADO con los elementos claramente separados.\n'
        + '- CENTRO/ABAJO: la PLANTA (vista cenital).\n'
        + '- DERECHA: recuadro "ACABADOS Y SANITARIOS" (mueble, encimera/lavabo, grifería, espejo, mampara, iluminación).\n'
        + 'REGLAS: NO dibujes campana, placa ni cocina.' + SIN_COTAS
      );
    }
    if (tid === 'otro') {
      return (
        'Crea una LÁMINA de ESTE mueble a medida (usa la imagen adjunta como referencia FIEL: mismos módulos, acabados y distribución). ' + base + '\n'
        + '- ARRIBA: el FRENTE/ALZADO con los módulos separados.\n'
        + '- CENTRO/ABAJO: la PLANTA (vista cenital).\n'
        + '- DERECHA: recuadro "ACABADOS" (frentes, tiradores, interior, iluminación, detalles).\n'
        + 'REGLAS: dibuja solo lo que aparece en el render.' + SIN_COTAS
      );
    }
    // Cocina (por defecto)
    return (
      'Crea una LÁMINA de ESTA cocina (usa la imagen adjunta como referencia FIEL del diseño, mismos muebles, acabados y distribución). ' + base + '\n'
      + '- ARRIBA: el FRENTE/ALZADO de la cocina con cada módulo claramente separado.\n'
      + '- CENTRO/ABAJO: la PLANTA (vista cenital) de la cocina.\n'
      + '- DERECHA: recuadro "ACABADOS SUGERIDOS" (puertas, encimera, tirador, salpicadero, iluminación, detalles).\n'
      + 'REGLAS TÉCNICAS OBLIGATORIAS del alzado:\n'
      + '  · La CAMPANA extractora va SIEMPRE centrada JUSTO ENCIMA de la placa/cocina (zona de cocción), con el MISMO ancho que esa zona; NUNCA la dibujes reflejada ni desplazada sobre otro módulo.\n'
      + '  · Los muebles ALTOS se alinean verticalmente con los BAJOS: cada módulo alto encima del bajo que le corresponde.'
      + SIN_COTAS
    );
  };

  // Llama a un endpoint POST JSON y devuelve el JSON. Si el backend responde con
  // error (401/404/422/500/503…) lanza un Error con el MOTIVO legible (el campo
  // `detail`/`error` del backend) para que NUNCA falle en silencio y el usuario
  // vea por qué. Marca blanca: los mensajes del backend ya evitan citar el motor.
  const postJson = async (path, bodyObj) => {
    const res = await fetch(`${API_URL}${path}`, {
      method: 'POST', headers: getAuthHeaders(),
      body: typeof bodyObj === 'string' ? bodyObj : JSON.stringify(bodyObj),
    });
    let data = null;
    try { data = await res.json(); } catch { data = null; }
    if (!res.ok) {
      const motivo = (data && (data.detail || data.error)) || `Error ${res.status} al llamar al servicio.`;
      throw new Error(typeof motivo === 'string' ? motivo : `Error ${res.status}.`);
    }
    return data;
  };

  // Genera los planos EXACTOS (planta acotada + alzado alámbrico) a partir de una
  // distribución detectada. Devuelve las láminas listas para el historial. Si un
  // endpoint falla, propaga el error (con motivo) en lugar de tragárselo.
  // Vista ALÁMBRICA en blanco y negro (estilo CAD tipo TeoWin), con o sin cotas.
  // Es el mismo motor vectorial determinista: nunca hay medidas inventadas.
  const generarVistaAlambrica = async (conCotas) => {
    if (editing) return;
    setEditing(true); setError(null);
    try {
      let distribucion = null;
      const img = currentImage();
      if (img) {
        const dataUrl = await imageToDataUrl(img);
        const dj = await postJson('/api/estudio-cocinas/detect-distribucion', { imageBase64: dataUrl, medidas });
        if (dj?.success) distribucion = dj.distribucion;
      }
      if (!distribucion && (description || '').trim()) {
        const dt = await postJson('/api/estudio-cocinas/distribucion-desde-texto', { descripcion: description, medidas });
        if (dt?.success) distribucion = dt.distribucion;
      }
      if (!distribucion) {
        setError('Necesito un render o una descripción con los módulos para dibujar la vista alámbrica.');
        return;
      }
      const ar = await postJson('/api/estudio-cocinas/alzado', {
        nombre_cliente: cliente || 'Cliente',
        distribucion_estructurada: distribucion,
        con_cotas: !!conCotas,
        monocromo: true,
      });
      if (!ar?.alzadoBase64) { setError('No se pudo generar la vista alámbrica.'); return; }
      const lamina = {
        success: true,
        result: { images: [ar.alzadoBase64] },
        description: conCotas ? 'Vista alámbrica B/N (con medidas)' : 'Vista alámbrica B/N (sin medidas)',
        timestamp: new Date(),
      };
      setRenderResult(lamina);
      setRenderHistory(prev => [lamina, ...prev].slice(0, 14));
      if (ar.avisos?.length) setError(`Vista generada. Revisa: ${ar.avisos.join(' · ')}`);
    } catch (e) {
      setError(`Error al generar la vista alámbrica: ${e?.message || 'error desconocido'}.`);
    } finally { setEditing(false); }
  };

  const generarPlanosExactos = async (distribucion) => {
    const body = JSON.stringify({ nombre_cliente: cliente || 'Cliente', distribucion_estructurada: distribucion });
    const [pr, ar] = await Promise.all([
      postJson('/api/estudio-cocinas/plano-2d', body),
      postJson('/api/estudio-cocinas/alzado', body),
    ]);
    const extra = [];
    if (pr?.planoBase64) extra.push({ success: true, result: { images: [pr.planoBase64] }, description: 'Planta acotada (exacta)', timestamp: new Date() });
    if (ar?.alzadoBase64) extra.push({ success: true, result: { images: [ar.alzadoBase64] }, description: 'Alzado alámbrico acotado (exacto)', timestamp: new Date() });
    return extra;
  };

  // ─── Editar el render existente en lenguaje natural ─────────────────────────
  // Lámina técnica: alzado con cotas + planta + listado de medidas + acabados,
  // generada a partir del render actual (estilo ficha de estudio profesional).
  const generarFichaTecnica = async () => {
    const img = currentImage();
    if (!img || editing) return;
    // Sin el ancho REAL no hay cotas fiables: las medidas se estimarían. Antes de
    // dibujar nada, se exige la escala real (regla: nunca inventar medidas).
    const anchoReal = Number(String(medidas?.ancho ?? '').replace(',', '.')) || 0;
    if (tipo3d === 'cocina' && !anchoReal) {
      setError('Indica arriba el ANCHO REAL de la estancia (cm) antes de generar la ficha: sin esa escala las cotas no serían medidas reales.');
      return;
    }
    setEditing(true); setError(null);
    try {
      const dataUrl = await imageToDataUrl(img);

      // 1º LO IMPORTANTE: planta + alzado VECTORIALES ACOTADOS (deterministas,
      // calculados desde medidas reales y validados por geometría de fabricación).
      let exactosOk = false;
      if (tipo3d === 'cocina') {
        try {
          const dj = await postJson('/api/estudio-cocinas/detect-distribucion', { imageBase64: dataUrl, medidas });
          if (dj?.success && dj.distribucion) {
            const extra = await generarPlanosExactos(dj.distribucion);
            if (extra.length) {
              exactosOk = true;
              setRenderResult(extra[0]);
              setRenderHistory(prev => [...extra, ...prev].slice(0, 14));
              if (dj.avisos?.length) setError(`Planos acotados generados. Revisa: ${dj.avisos.join(' · ')}`);
            }
          }
        } catch (e) {
          setError(`No se pudieron generar los planos acotados: ${e?.message || 'error desconocido'}.`);
        }
      }

      // 2º La lámina gráfica de la IA: SIN cotas (los números los pone el vectorial).
      const desc = fichaPromptPorTipo(tipo3d);
      const response = await fetch(`${API_URL}/api/ai-engine/render`, {
        method: 'POST', headers: getAuthHeaders(),
        body: JSON.stringify({ description: desc, style: params.style, provider: providerOf(), referenceImage: dataUrl }),
      });
      const data = await response.json();
      if (data.success) {
        const merged = { ...data, description: 'Lámina de presentación (sin cotas; las medidas van en el plano acotado)' };
        if (!exactosOk) setRenderResult(merged);
        setRenderHistory(prev => [{ ...merged, timestamp: new Date() }, ...prev].slice(0, 14));
      } else if (!exactosOk) {
        setError(data.error || 'No se pudo generar la ficha técnica.');
      }
    } catch (e) { setError(`Error al generar la ficha técnica: ${e?.message || 'error desconocido'}.`); }
    finally { setEditing(false); }
  };

  // Genera SOLO los planos técnicos EXACTOS (planta acotada + alzado alámbrico)
  // a partir del render: detecta la distribución con IA y los dibuja vectoriales.
  const generarPlanosTecnicos = async () => {
    const img = currentImage(); if (!img || editing) return;
    setEditing(true); setError(null);
    try {
      const dataUrl = await imageToDataUrl(img);
      const dj = await postJson('/api/estudio-cocinas/detect-distribucion', { imageBase64: dataUrl, medidas });
      if (!dj?.success || !dj.distribucion) { setError(dj?.detail || 'No se pudo deducir la distribución del render para dibujar los planos.'); return; }
      const extra = await generarPlanosExactos(dj.distribucion);
      if (!extra.length) { setError('No se pudieron generar los planos técnicos (respuesta vacía del servicio).'); return; }
      // Los planos técnicos NO sustituyen a la propuesta de diseño 3D en la vista
      // principal: se añaden como láminas en el historial para poder abrirlos.
      setRenderHistory(prev => [...extra, ...prev].slice(0, 14));
    } catch (e) { setError(`Error al generar los planos técnicos: ${e?.message || 'error desconocido'}.`); }
    finally { setEditing(false); }
  };

  // Alzado técnico EXACTO desde LA DESCRIPCIÓN escrita (no desde el render). Útil
  // cuando el render fotorrealista no respeta un módulo (p. ej. "1 cajón + 2 gavetas"):
  // el alzado vectorial se dibuja de forma determinista con el recuento exacto pedido.
  const generarAlzadoDesdeTexto = async () => {
    const desc = (description || '').trim();
    if (!desc) { setError('Escribe la descripción del diseño (con los módulos) para generar el alzado exacto.'); return; }
    if (editing) return;
    setEditing(true); setError(null);
    try {
      const dj = await postJson('/api/estudio-cocinas/distribucion-desde-texto', { descripcion: desc, medidas });
      if (!dj?.success || !dj.distribucion) { setError(dj?.detail || 'No se pudo interpretar la descripción para dibujar el alzado.'); return; }
      const extra = await generarPlanosExactos(dj.distribucion);
      if (!extra.length) { setError('No se pudo generar el alzado (respuesta vacía del servicio).'); return; }
      setRenderHistory(prev => [...extra, ...prev].slice(0, 14));
    } catch (e) { setError(`Error al generar el alzado desde la descripción: ${e?.message || 'error desconocido'}.`); }
    finally { setEditing(false); }
  };

  // Evita PERDER resolución entre peticiones: si el nuevo render sale más pequeño
  // que la imagen de la que partimos, lo reescala (Lanczos aprox. vía canvas) para
  // que nunca baje de la resolución previa. Devuelve un dataURL.
  const keepResolution = (newSrc, refSrc) => new Promise((resolve) => {
    if (!newSrc || !refSrc) return resolve(newSrc);
    const ref = new window.Image();
    ref.onload = () => {
      const nw = new window.Image();
      nw.onload = () => {
        if (nw.width >= ref.width && nw.height >= ref.height) return resolve(newSrc);
        const scale = Math.max(ref.width / nw.width, ref.height / nw.height);
        const cw = Math.round(nw.width * scale), ch = Math.round(nw.height * scale);
        const cv = document.createElement('canvas'); cv.width = cw; cv.height = ch;
        const ctx = cv.getContext('2d');
        ctx.imageSmoothingEnabled = true; ctx.imageSmoothingQuality = 'high';
        ctx.drawImage(nw, 0, 0, cw, ch);
        try { resolve(cv.toDataURL('image/png')); } catch { resolve(newSrc); }
      };
      nw.onerror = () => resolve(newSrc);
      nw.src = newSrc;
    };
    ref.onerror = () => resolve(newSrc);
    ref.src = refSrc;
  });

  // ─── Visita de decorador/a: pasa el render por el "ojo" de un decorador
  // profesional. Mejora estilismo, iluminación, textiles, materiales y atmósfera
  // SIN tocar la estructura, los muebles ni las medidas. ────────────────────────
  const visitaDecorador = async () => {
    const img = currentImage();
    if (!img || editing) return;
    setEditing(true); setError(null);
    try {
      const dataUrl = await imageToDataUrl(img);
      const desc = (
        `Aplica el TOQUE DE UN DECORADOR/A PROFESIONAL a este ${tipoActual.label.toLowerCase()} usando la imagen `
        + 'adjunta como referencia FIEL. REGLA ABSOLUTA: NO cambies NADA del mobiliario. Los muebles, módulos, '
        + 'puertas y frentes, tiradores, encimera, electrodomésticos, distribución, medidas, MATERIALES, ACABADOS '
        + 'y COLORES deben quedar EXACTAMENTE IGUALES que en la referencia, pixel a pixel en su forma y color. '
        + 'NO recolores, NO cambies el material ni el acabado de ningún mueble ni de la encimera, NO añadas ni '
        + 'quites ni muevas ni redimensiones módulos, NO reorganices nada. '
        + 'Lo ÚNICO que puedes mejorar es el AMBIENTE de la estancia alrededor del mueble: iluminación más cálida '
        + 'y equilibrada, y complementos decorativos SUELTOS que no forman parte del mueble (plantas, un cuadro en '
        + 'la pared, textiles, fruteros, algún objeto sobre la encimera). Estos complementos no deben tapar ni '
        + 'alterar los muebles. Misma cámara, misma perspectiva, fotorrealista y de alta calidad.'
      );
      const response = await fetch(`${API_URL}/api/ai-engine/render`, {
        method: 'POST', headers: getAuthHeaders(),
        body: JSON.stringify({ description: desc, style: params.style, provider: providerOf(), referenceImage: dataUrl }),
      });
      const data = await response.json();
      if (data.success) {
        let finalImg = data.result?.images?.[0];
        try { finalImg = await keepResolution(await imageToDataUrl(finalImg), dataUrl); } catch { /* si falla, se usa la original */ }
        const merged = { ...data, result: { ...data.result, images: [finalImg] }, description: `${renderResult?.description || description}\n[Visita de decorador/a]` };
        setRenderResult(merged);
        setRenderHistory(prev => [{ ...merged, timestamp: new Date() }, ...prev].slice(0, 12));
      } else setError(data.error || 'No se pudo aplicar la visita de decorador/a.');
    } catch { setError('Error de conexión en la visita de decorador/a.'); }
    finally { setEditing(false); }
  };

  // ─── HD: pasada de restauración/super-resolución. Recupera nitidez tras muchas
  // ediciones (generation-loss) SIN cambiar nada del diseño. ────────────────────
  const mejorarResolucion = async () => {
    const img = currentImage();
    if (!img || editing) return;
    setEditing(true); setError(null);
    try {
      const dataUrl = await imageToDataUrl(img);
      const desc = (
        'Reprocesa esta imagen a ALTA RESOLUCIÓN y máxima nitidez fotorrealista. '
        + 'NO cambies absolutamente NADA del diseño: mismos muebles, colores, materiales, '
        + 'distribución, encuadre, perspectiva e iluminación. Solo mejora la DEFINICIÓN, el '
        + 'enfoque y el detalle fino, eliminando el suavizado, el ruido y cualquier pixelado '
        + 'acumulado. Resultado limpio y nítido, misma composición exacta.'
      );
      const response = await fetch(`${API_URL}/api/ai-engine/render`, {
        method: 'POST', headers: getAuthHeaders(),
        body: JSON.stringify({ description: desc, style: params.style, provider: providerOf(), referenceImage: dataUrl }),
      });
      const data = await response.json();
      if (data.success) {
        const merged = { ...data, description: `${renderResult?.description || description}\n[HD · nitidez mejorada]` };
        setRenderResult(merged);
        setRenderHistory(prev => [{ ...merged, timestamp: new Date() }, ...prev].slice(0, 12));
      } else setError(data.error || 'No se pudo mejorar la resolución.');
    } catch { setError('Error de conexión al mejorar la resolución.'); }
    finally { setEditing(false); }
  };

  // Genera la imagen a resolución 4K real (3840 px): primero un pase de nitidez con
  // IA para añadir detalle fino, y después un reescalado determinista a 4K. La deja
  // como render actual y la descarga automáticamente.
  const generar4K = async () => {
    const img = currentImage();
    if (!img || editing) return;
    setEditing(true); setError(null);
    try {
      const dataUrl = await imageToDataUrl(img);
      // 1) Pase de nitidez con IA (misma composición, más detalle).
      let base = dataUrl;
      try {
        const desc = (
          'Reprocesa esta imagen a MÁXIMA nitidez y detalle fotorrealista SIN cambiar '
          + 'nada del diseño: mismos muebles, colores, materiales, distribución, encuadre, '
          + 'perspectiva e iluminación. Solo mejora definición y detalle fino.'
        );
        const rr = await fetch(`${API_URL}/api/ai-engine/render`, {
          method: 'POST', headers: getAuthHeaders(),
          body: JSON.stringify({ description: desc, style: params.style, provider: providerOf(), referenceImage: dataUrl }),
        });
        const rd = await rr.json();
        if (rd.success) base = await imageToDataUrl(rd.result?.images?.[0]);
      } catch { /* si el pase de IA falla, se escala igualmente la imagen actual */ }
      // 2) Reescalado determinista a 4K (3840 px).
      const up = await fetch(`${API_URL}/api/ai-engine/render/upscale-4k`, {
        method: 'POST', headers: getAuthHeaders(),
        body: JSON.stringify({ imageBase64: base, width: 3840 }),
      });
      const ud = await up.json();
      if (ud.success && ud.image) {
        const merged = { ...(renderResult || {}), result: { images: [ud.image] }, description: `${renderResult?.description || description}\n[4K · ${ud.width}×${ud.height}]` };
        setRenderResult(merged);
        setRenderHistory(prev => [{ ...merged, timestamp: new Date() }, ...prev].slice(0, 12));
        // Descarga automática del 4K.
        try {
          const a = document.createElement('a');
          a.href = ud.image; a.download = `render-4k-${Date.now()}.jpg`;
          document.body.appendChild(a); a.click(); a.remove();
        } catch { /* descarga best-effort */ }
      } else setError(ud.detail || ud.error || 'No se pudo generar la versión 4K.');
    } catch { setError('Error al generar la versión 4K.'); }
    finally { setEditing(false); }
  };

  const editRender = async () => {
    const img = currentImage();
    // Combina la instrucción principal + líneas adicionales (multi-línea).
    const allLines = [editInstruction.trim(), ...editLines.map(l => l.trim())].filter(Boolean);
    if (!img || (!allLines.length && !editRefImage)) return;
    // Instantánea de lo que se APLICA ahora, para luego borrar SOLO eso y conservar
    // lo que el usuario escriba mientras se procesa (poder encolar órdenes).
    const snapMain = editInstruction;
    const snapLines = [...editLines];
    setEditing(true); setError(null);
    try {
      const dataUrl = await imageToDataUrl(img);
      const cambio = allLines.length
        ? allLines.join('. ')
        : (editRefImage ? 'Incorpora a la cocina el elemento de la imagen de referencia adicional (respeta su forma, color y acabado).' : '');
      const response = await fetch(`${API_URL}/api/ai-engine/render`, {
        method: 'POST', headers: getAuthHeaders(),
        body: JSON.stringify({
          description: `Modifica el render adjunto manteniendo el mismo diseño, encuadre e iluminación. Cambios solicitados: ${cambio}. No cambies nada más.`,
          style: params.style,
          provider: providerOf(),
          referenceImage: dataUrl,
          referenceImages: editRefImage ? [editRefImage] : undefined,
        }),
      });
      const data = await response.json();
      if (data.success) {
        let finalImg = data.result?.images?.[0];
        try { finalImg = await keepResolution(await imageToDataUrl(finalImg), dataUrl); } catch { /* si falla, se usa la original */ }
        const merged = { ...data, result: { ...data.result, images: [finalImg] }, description: `${renderResult?.description || description}\n[Edición] ${cambio}` };
        setRenderResult(merged);
        setRenderHistory(prev => [{ ...merged, timestamp: new Date() }, ...prev].slice(0, 10));
        // Borra SOLO lo que se aplicó; conserva lo escrito después (órdenes en cola).
        setEditInstruction(prev => (prev === snapMain ? '' : prev));
        setEditLines(prev => {
          const rem = [...snapLines];
          return prev.filter(l => {
            const i = rem.indexOf(l);
            if (i !== -1) { rem.splice(i, 1); return false; } // línea aplicada → quitar
            return true;                                       // escrita después → conservar
          });
        });
        setEditRefImage(null);
      } else setError(data.error || 'No se pudo editar el render');
    } catch { setError('Error de conexión al editar el render.'); }
    finally { setEditing(false); }
  };

  const nombreArchivo = (ext) => {
    const base = (cliente || ref || 'render-3d').trim().replace(/\s+/g, '_').replace(/[^\w\-]/g, '');
    return `${base || 'render-3d'}.${ext}`;
  };

  // Estampa el logo personalizado como MARCA DE AGUA sobre una imagen (dataURL) y
  // devuelve el nuevo dataURL. Si no hay logo o la marca está desactivada, devuelve
  // la imagen tal cual. El logo se coloca abajo a la derecha, semitransparente.
  const stampWatermark = async (dataUrl) => {
    let logo = state?.logo;
    if (!watermarkOn || !logo) return dataUrl;
    // El logo debe ser data: para no contaminar el canvas (cross-origin).
    if (!String(logo).startsWith('data:')) {
      try { logo = await imageToDataUrl(logo); } catch { return dataUrl; }
    }
    return new Promise((resolve) => {
    const base = new window.Image();
    base.crossOrigin = 'anonymous';
    base.onload = () => {
      const lg = new window.Image();
      lg.crossOrigin = 'anonymous';
      lg.onload = () => {
        const cv = document.createElement('canvas');
        cv.width = base.naturalWidth; cv.height = base.naturalHeight;
        const ctx = cv.getContext('2d');
        ctx.drawImage(base, 0, 0);
        // Logo a ~18% del ancho, margen del 3%, opacidad 0.5.
        const lw = cv.width * 0.18;
        const lh = lw * (lg.naturalHeight / lg.naturalWidth || 0.4);
        const m = cv.width * 0.03;
        ctx.globalAlpha = 0.5;
        ctx.drawImage(lg, cv.width - lw - m, cv.height - lh - m, lw, lh);
        ctx.globalAlpha = 1;
        try { resolve(cv.toDataURL('image/png')); } catch { resolve(dataUrl); }
      };
      lg.onerror = () => resolve(dataUrl);
      lg.src = logo;
    };
    base.onerror = () => resolve(dataUrl);
    base.src = dataUrl;
    });
  };

  // ─── Descargar el render (PNG) ──────────────────────────────────────────────
  const downloadRender = async () => {
    const img = currentImage();
    if (!img) return;
    setDownloading(true);
    try {
      const dataUrl = await stampWatermark(await imageToDataUrl(img));
      const a = document.createElement('a');
      a.href = dataUrl; a.download = nombreArchivo('png');
      document.body.appendChild(a); a.click(); a.remove();
    } catch { setError('No se pudo descargar la imagen.'); }
    finally { setDownloading(false); }
  };

  // ─── Descargar TODO de seguido: el render actual + todo el historial ─────────
  // (renders, variantes, planos, láminas). Cada imagen se descarga como PNG.
  const descargarTodo = async () => {
    // Reúne imágenes sin duplicar, empezando por el render actual.
    const items = [];
    const push = (src, etiqueta) => { if (src && !items.some(x => x.src === src)) items.push({ src, etiqueta }); };
    push(currentImage(), renderResult?.description || 'render');
    (renderHistory || []).forEach((h, i) => push(h?.result?.images?.[0], h?.description || `historial-${i + 1}`));
    if (!items.length) return;
    setDownloading(true);
    try {
      const base = (cliente || ref || 'estudio-3d').trim().replace(/\s+/g, '_').replace(/[^\w\-]/g, '') || 'estudio-3d';
      for (let i = 0; i < items.length; i++) {
        try {
          const dataUrl = await stampWatermark(await imageToDataUrl(items[i].src));
          const a = document.createElement('a');
          a.href = dataUrl;
          a.download = `${base}_${String(i + 1).padStart(2, '0')}.png`;
          document.body.appendChild(a); a.click(); a.remove();
          // Pausa breve para que el navegador no bloquee la descarga múltiple.
          await new Promise(r => setTimeout(r, 350));
        } catch { /* si una imagen falla, seguimos con las demás */ }
      }
    } finally { setDownloading(false); }
  };

  // ─── Exportar PDF de presentación (con logo) ────────────────────────────────
  const exportPDF = async () => {
    const img = currentImage();
    if (!img) return;
    setDownloading(true);
    try {
      const dataUrl = await imageToDataUrl(img);
      const { jsPDF } = await import('jspdf');
      const pdf = new jsPDF({ orientation: 'landscape', unit: 'mm', format: 'a4' });
      const W = pdf.internal.pageSize.getWidth();
      const H = pdf.internal.pageSize.getHeight();
      const M = 12;
      // Cabecera: logo o nombre
      const logo = state?.logo;
      if (logo && typeof logo === 'string' && logo.startsWith('data:')) {
        try { const fmt = logo.includes('image/png') ? 'PNG' : (logo.includes('image/webp') ? 'WEBP' : 'JPEG'); pdf.addImage(logo, fmt, M, 8, 30, 15); } catch (_) {}
      } else { pdf.setFontSize(15); pdf.setTextColor(30); pdf.setFont(undefined, 'bold'); pdf.setFont(undefined, 'normal'); }
      pdf.setFontSize(16); pdf.setTextColor(60, 40, 120); pdf.setFont(undefined, 'bold');
      pdf.text('PROPUESTA DE DISEÑO 3D', W - M, 15, { align: 'right' });
      pdf.setFont(undefined, 'normal'); pdf.setFontSize(10); pdf.setTextColor(120);
      if (cliente) pdf.text(cliente, W - M, 21, { align: 'right' });
      pdf.text(new Date().toLocaleDateString('es-ES'), W - M, 26, { align: 'right' });
      // Imagen del render (encajada manteniendo proporción)
      const areaY = 32, areaH = H - areaY - 16, areaW = W - 2 * M;
      const props = pdf.getImageProperties(dataUrl);
      const ratio = Math.min(areaW / props.width, areaH / props.height);
      const iw = props.width * ratio, ih = props.height * ratio;
      pdf.addImage(dataUrl, 'PNG', M + (areaW - iw) / 2, areaY, iw, ih);
      // Pie con descripción
      const desc = (renderResult?.description || description || '').trim();
      if (desc) { pdf.setFontSize(8.5); pdf.setTextColor(110); pdf.text(pdf.splitTextToSize(desc, W - 2 * M).slice(0, 2), M, H - 8); }
      pdf.save(nombreArchivo('pdf'));
    } catch (e) { setError('No se pudo generar el PDF: ' + (e.message || '')); }
    finally { setDownloading(false); }
  };

  // ─── Compartir por WhatsApp ────────────────────────────────────────────────
  const shareWhatsApp = async () => {
    const img = currentImage();
    if (!img) return;
    try {
      const dataUrl = await imageToDataUrl(img);
      const text = `✨ Propuesta de diseño 3D${cliente ? ` para ${cliente}` : ''}\n${(renderResult?.description || description || '').substring(0, 200)}`;
      // Intentar Web Share API (móvil)
      if (navigator.share && navigator.canShare) {
        const blob = await (await fetch(dataUrl)).blob();
        const file = new File([blob], nombreArchivo('png'), { type: 'image/png' });
        if (navigator.canShare({ files: [file] })) {
          await navigator.share({ text, files: [file] });
          return;
        }
      }
      // Fallback: abrir WhatsApp Web con texto
      const encoded = encodeURIComponent(text);
      window.open(`https://wa.me/?text=${encoded}`, '_blank');
    } catch (e) {
      if (e.name !== 'AbortError') setError('No se pudo compartir por WhatsApp.');
    }
  };

  // ─── Dossier PDF multi-página (portada + render + especificaciones) ─────────
  const exportDossierPDF = async () => {
    const img = currentImage();
    if (!img) return;
    setDownloading(true);
    try {
      const dataUrl = await imageToDataUrl(img);
      const { jsPDF } = await import('jspdf');
      const pdf = new jsPDF({ orientation: 'landscape', unit: 'mm', format: 'a4' });
      const W = pdf.internal.pageSize.getWidth();
      const H = pdf.internal.pageSize.getHeight();
      const M = 12;
      // Página 1: Portada
      const logo = state?.logo;
      if (logo && typeof logo === 'string' && logo.startsWith('data:')) {
        try { const fmt = logo.includes('image/png') ? 'PNG' : 'JPEG'; pdf.addImage(logo, fmt, M, M, 40, 20); } catch (_) {}
      } else { pdf.setFontSize(20); pdf.setTextColor(30); pdf.setFont(undefined, 'bold'); pdf.setFont(undefined, 'normal'); }
      pdf.setFontSize(24); pdf.setTextColor(60, 40, 120); pdf.setFont(undefined, 'bold');
      pdf.text('PROPUESTA DE DISEÑO 3D', W / 2, H / 2 - 10, { align: 'center' });
      pdf.setFont(undefined, 'normal'); pdf.setFontSize(14); pdf.setTextColor(80);
      if (cliente) pdf.text(cliente, W / 2, H / 2 + 5, { align: 'center' });
      if (ref) pdf.text(`Ref: ${ref}`, W / 2, H / 2 + 14, { align: 'center' });
      pdf.setFontSize(10); pdf.setTextColor(140);
      pdf.text(new Date().toLocaleDateString('es-ES', { day: '2-digit', month: 'long', year: 'numeric' }), W / 2, H - 20, { align: 'center' });
      // Página 2: Render
      pdf.addPage();
      const props = pdf.getImageProperties(dataUrl);
      const areaW = W - 2 * M, areaH = H - 2 * M;
      const ratio = Math.min(areaW / props.width, areaH / props.height);
      const iw = props.width * ratio, ih = props.height * ratio;
      pdf.addImage(dataUrl, 'PNG', M + (areaW - iw) / 2, M + (areaH - ih) / 2, iw, ih);
      // Página 3: Especificaciones
      pdf.addPage('a4', 'portrait');
      const Wp = pdf.internal.pageSize.getWidth();
      let y = 20;
      pdf.setFontSize(14); pdf.setTextColor(60, 40, 120); pdf.setFont(undefined, 'bold');
      pdf.text('ESPECIFICACIONES DEL DISEÑO', M, y); y += 10;
      pdf.setFont(undefined, 'normal'); pdf.setFontSize(10); pdf.setTextColor(60);
      const specs = [
        ['Distribución', MATERIALS.layouts.find(l => l.id === params.layout)?.label || params.layout],
        ['Encimera', MATERIALS.countertops.find(c => c.id === params.countertop)?.label || params.countertop],
        ['Muebles', MATERIALS.cabinets.find(c => c.id === params.cabinets)?.label || params.cabinets],
        ['Tiradores', MATERIALS.handles.find(h => h.id === params.handles)?.label || params.handles],
        ['Suelo', MATERIALS.floors.find(f => f.id === params.floor)?.label || params.floor],
        ['Estilo', MATERIALS.styles.find(s => s.id === params.style)?.label || params.style],
        ['Iluminación', MATERIALS.lighting.find(l => l.id === params.lighting)?.label || params.lighting],
      ];
      if (medidas.ancho) specs.push(['Ancho estancia', `${medidas.ancho} cm`]);
      if (medidas.fondo) specs.push(['Fondo estancia', `${medidas.fondo} cm`]);
      if (medidas.altura) specs.push(['Altura techo', `${medidas.altura} cm`]);
      const selElectros = MATERIALS.appliances.filter(a => electros.includes(a.id)).map(a => a.label);
      if (selElectros.length) specs.push(['Electrodomésticos', selElectros.join(', ')]);
      specs.forEach(([k, v]) => {
        pdf.setFont(undefined, 'bold'); pdf.text(`${k}:`, M, y);
        pdf.setFont(undefined, 'normal'); pdf.text(v, M + 45, y);
        y += 7;
      });
      y += 5;
      const desc = (renderResult?.description || description || '').trim();
      if (desc) {
        pdf.setFont(undefined, 'bold'); pdf.text('Descripción:', M, y); y += 6;
        pdf.setFont(undefined, 'normal'); pdf.setFontSize(9);
        const lines = pdf.splitTextToSize(desc, Wp - 2 * M);
        lines.slice(0, 20).forEach(l => { pdf.text(l, M, y); y += 5; });
      }
      pdf.save(nombreArchivo('pdf'));
    } catch (e) { setError('No se pudo generar el dossier PDF: ' + (e.message || '')); }
    finally { setDownloading(false); }
  };

  // ─── Guardar / abrir proyectos ──────────────────────────────────────────────
  // Reduce el render a un tamaño razonable ANTES de guardarlo: una data URL de
  // un render grande (p.ej. 2K) puede pesar varios MB y el servidor/proxy
  // rechaza el JSON → "Error al guardar". Para archivo basta 1600px JPEG.
  const shrinkForSave = async (src) => {
    const dataUrl = await imageToDataUrl(src);
    if (!dataUrl || !String(dataUrl).startsWith('data:image')) return dataUrl;
    return await new Promise((resolve) => {
      const im = new window.Image();
      im.onload = () => {
        try {
          const maxDim = 1600;
          const scale = Math.min(1, maxDim / Math.max(im.width, im.height));
          const w = Math.round(im.width * scale), h = Math.round(im.height * scale);
          const c = document.createElement('canvas'); c.width = w; c.height = h;
          c.getContext('2d').drawImage(im, 0, 0, w, h);
          resolve(c.toDataURL('image/jpeg', 0.85));
        } catch (_) { resolve(dataUrl); }
      };
      im.onerror = () => resolve(dataUrl);
      im.src = dataUrl;
    });
  };

  const saveDesign = async () => {
    const img = currentImage();
    if (!img) { setError('Genera un render antes de guardar.'); return; }
    if (!(cliente || ref).trim()) { setError('Pon un cliente o referencia para guardar el proyecto.'); return; }
    setBusy(true); setError(null);
    try {
      const imgSave = await shrinkForSave(img);
      // Guardar también la referencia/plano subido para poder comparar al reabrir
      let refSave = null;
      if (refImage) {
        try { refSave = await shrinkForSave(refImage); } catch (_) { refSave = refImage; }
      }
      const r = await fetch(`${API_URL}/api/ai-engine/designs`, {
        method: 'POST', headers: getAuthHeaders(),
        body: JSON.stringify({ id: savedId || undefined, cliente, ref, description: renderResult?.description || description, style: params.style, images: [imgSave], referenceImage: refSave }),
      });
      let d = null;
      try { d = await r.json(); } catch (_) { d = null; }
      if (d?.success) { setSavedId(d.design.id); }
      else setError(d?.error || d?.detail || `No se pudo guardar (HTTP ${r.status}).`);
    } catch { setError('Error de conexión al guardar el proyecto.'); }
    finally { setBusy(false); }
  };
  const openList = async () => {
    try {
      const r = await fetch(`${API_URL}/api/ai-engine/designs`, { headers: getAuthHeaders() });
      if (!r.ok) { const e = await r.json().catch(() => ({})); throw new Error(e.detail || `Error ${r.status}`); }
      const d = await r.json();
      setSavedList(d.designs || []);
    } catch (e) { setError(`No se pudo cargar la lista de proyectos: ${e.message || 'error de conexión'}`); }
  };
  const loadDesign = async (dsg) => {
    setCliente(dsg.cliente || ''); setRef(dsg.ref || ''); setDescription(dsg.description || '');
    if (dsg.style) setParams(p => ({ ...p, style: dsg.style }));
    setSavedId(dsg.id); setSavedList(null);
    if (dsg.images?.[0]) setRenderResult({ success: true, result: { images: dsg.images }, description: dsg.description });
    // La lista ya no trae el referenceImage (payload); se carga el detalle completo
    // para poder Comparar con el plano/referencia original guardado.
    setRefImage(null); setOriginalRef(null);
    try {
      const r = await fetch(`${API_URL}/api/ai-engine/designs/${dsg.id}`, { headers: getAuthHeaders() });
      if (r.ok) {
        const d = await r.json();
        const full = d.design || {};
        if (full.images?.length) setRenderResult({ success: true, result: { images: full.images }, description: full.description });
        if (full.referenceImage) { setRefImage(full.referenceImage); setOriginalRef(full.referenceImage); }
      }
    } catch { /* si falla el detalle, se queda con la miniatura de la lista */ }
  };
  const deleteDesign = async (id) => {
    if (!window.confirm('¿Eliminar este proyecto guardado?')) return;
    try {
      await fetch(`${API_URL}/api/ai-engine/designs/${id}`, { method: 'DELETE', headers: getAuthHeaders() });
      setSavedList(prev => (prev || []).filter(x => x.id !== id));
      if (savedId === id) setSavedId(null);
    } catch { setError('No se pudo eliminar.'); }
  };
  // ─── UNIR proyectos: junta las imágenes de varios proyectos guardados (mismo
  // cliente) en un proyecto nuevo, para tenerlas todas juntas. El usuario elige
  // cuáles. No borra los originales. ──────────────────────────────────────────
  const unirProyectos = async () => {
    const ids = selIds.slice();
    if (ids.length < 2) { setError('Selecciona al menos 2 proyectos para unir.'); return; }
    setBusy(true); setError(null);
    try {
      // Trae el detalle (con imágenes) de cada proyecto seleccionado.
      const detalles = [];
      for (const id of ids) {
        const r = await fetch(`${API_URL}/api/ai-engine/designs/${id}`, { headers: getAuthHeaders() });
        if (r.ok) { const d = await r.json(); if (d?.design) detalles.push(d.design); }
      }
      if (!detalles.length) { setError('No se pudieron cargar los proyectos a unir.'); return; }
      const imgs = detalles.flatMap(d => d.images || []).filter(Boolean);
      if (!imgs.length) { setError('Los proyectos seleccionados no tienen imágenes guardadas.'); return; }
      const clienteU = detalles[0].cliente || cliente || 'Cliente';
      const refsU = [...new Set(detalles.map(d => d.ref).filter(Boolean))].join(' + ');
      const r = await fetch(`${API_URL}/api/ai-engine/designs`, {
        method: 'POST', headers: getAuthHeaders(),
        body: JSON.stringify({
          cliente: clienteU, ref: refsU || 'Proyecto unido',
          description: `Proyecto unido (${detalles.length} proyectos, ${imgs.length} imágenes)`,
          images: imgs, referenceImage: detalles[0].referenceImage || null,
        }),
      });
      const d = await r.json().catch(() => null);
      if (d?.success) { setSelMode(false); setSelIds([]); await openList(); }
      else setError(d?.error || d?.detail || 'No se pudo unir los proyectos.');
    } catch { setError('Error de conexión al unir los proyectos.'); }
    finally { setBusy(false); }
  };

  // ─── Adjuntar el render al presupuesto (Resumen Totales) ────────────────────
  // Volcado a presupuesto dual (P1/P2): si el usuario tiene ambos, muestra modal.
  const [showDualModal, setShowDualModal] = useState(null); // null | 'choosing'
  const attachToBudget = async () => {
    const img = currentImage();
    if (!img) return;
    // Armario → Presupuestador de Armarios (adjunta el render).
    if (tipo3d === 'armario') { await doAttach('armarios'); return; }
    // Cocina → Analizador de Planos: detecta los muebles del render y los vuelca
    // al presupuesto con la librería (precios correctos). Requiere acceso al Lab IA.
    if (tipo3d === 'cocina' && setState && state?.currentUser?.canUseAIAnalysis) {
      setDownloading(true);
      try {
        const dataUrl = await imageToDataUrl(img);
        setAttached(true); setTimeout(() => setAttached(false), 4000);
        setState(p => ({ ...p, analyzeRender: dataUrl, currentTab: 'visualizer' }));
      } catch { setError('No se pudo enviar el render al analizador.'); }
      finally { setDownloading(false); }
      return;
    }
    // Baño/otro (o sin acceso al Lab): adjunta el render a Cocina Montada.
    await doAttach('presupuestador2');
  };
  const doAttach = async (destTab) => {
    const img = currentImage();
    if (!img) return;
    setDownloading(true); setShowDualModal(null);
    try {
      const dataUrl = await imageToDataUrl(img);
      localStorage.setItem('render3d_attach', JSON.stringify({ image: dataUrl, cliente, ref, ts: Date.now() }));
      setAttached(true);
      setTimeout(() => setAttached(false), 4000);
      if (setState) setState(p => ({ ...p, currentTab: destTab, renderReturn: true }));
    } catch { setError('No se pudo adjuntar el render.'); }
    finally { setDownloading(false); }
  };

  const nuevoProyecto = () => {
    setCliente(''); setRef(''); setSavedId(null); setRenderResult(null); setRenderHistory([]);
    setDescription(''); setRefImage(null); setRefImages([]); setOriginalRef(null); setFloorPlan(null); setWallSketches([]);
    setEditInstruction(''); setEditLines([]); setEditRefImage(null);
    setMarks([]); setMarkTool(null); setSchematic(false);
    setOrbitFrames([]); setOrbitOn(false); setOrbitIndex(0);
    setSavedList(null); setSelMode(false); setSelIds([]); setError(null);
  };

  // ─── Subir imagen/PDF de referencia → la IA la describe y enriquece el prompt ───
  // Añade una referencia (base64 ya reducido) al array y la describe con la IA.
  // Se reutiliza tanto para subir archivos como para pegar del portapapeles.
  const addReference = async (b64, etiqueta = 'subida') => {
    setRefImages(prev => [...prev, b64]);
    setRefImage(b64);                       // principal = última añadida (compat con render single/comparar)
    setOriginalRef(prev => prev || b64);    // conserva la PRIMERA subida para Comparar
    try {
      const response = await fetch(`${API_URL}/api/ai-engine/describe-reference`, {
        method: 'POST', headers: getAuthHeaders(),
        body: JSON.stringify({ fileBase64: b64 }),
      });
      const data = await response.json();
      if (data.success && data.description) {
        setDescription(prev => prev?.trim()
          ? `${prev.trim()}\n\n[Referencia ${etiqueta}] ${data.description}`
          : data.description);
      }
    } catch (_) { /* la imagen ya está adjunta aunque falle la descripción */ }
  };

  // Quita una referencia del array (y reajusta la principal).
  const removeReference = (i) => setRefImages(prev => {
    const next = prev.filter((_, idx) => idx !== i);
    setRefImage(next[next.length - 1] || null);
    return next;
  });

  const handleReferenceUpload = async (e) => {
    const files = Array.from(e.target.files || []); // MÚLTIPLES: una imagen por pared, etc.
    e.target.value = '';
    if (!files.length) return;
    setAnalyzingRef(true);
    setError(null);
    try {
      for (const file of files) {
        const b64 = await downscaleImage(file);
        await addReference(b64, 'subida');
      }
    } catch (err) {
      setError('No se pudo subir la imagen de referencia. Inténtelo de nuevo.');
    } finally {
      setAnalyzingRef(false);
    }
  };

  // ─── Plano en planta + bocetos por pared → render fiel ───────────────────
  const fileToDataUrl = (file) => new Promise((res, rej) => {
    const fr = new FileReader();
    fr.onload = () => res(fr.result);
    fr.onerror = rej;
    fr.readAsDataURL(file);
  });
  const handleFloorPlanUpload = async (e) => {
    const file = e.target.files?.[0]; e.target.value = '';
    if (!file) return;
    try { setFloorPlan(await fileToDataUrl(file)); } catch { setError('No se pudo leer el plano.'); }
  };
  const handleAddWallSketch = async (e) => {
    const file = e.target.files?.[0]; e.target.value = '';
    if (!file) return;
    try { const b64 = await fileToDataUrl(file); setWallSketches(prev => [...prev, b64]); }
    catch { setError('No se pudo leer el boceto.'); }
  };
  const removeWallSketch = (i) => setWallSketches(prev => prev.filter((_, idx) => idx !== i));
  const handleGenerateComposed = async () => {
    if (!floorPlan && wallSketches.length === 0) return;
    const err = guardTipo(description);
    if (err) { setError(err); return; }
    setIsGenerating(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/api/ai-engine/render/compose`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          description: conMedidas(description.trim()),
          style: params.style,
          floorPlan: floorPlan || undefined,
          wallSketches,
        }),
      });
      const data = await response.json();
      if (data.success) {
        setRenderResult(data);
        setRenderHistory(prev => [{ ...data, description, timestamp: new Date() }, ...prev].slice(0, 10));
      } else {
        setError(data.error || 'Error al generar el render');
      }
    } catch (err) {
      setError('Error de conexión. Verifique su conexión a internet.');
    } finally {
      setIsGenerating(false);
    }
  };

  // ─── Generar render por descripción natural ─────────────────────────────
  const handleGenerateNatural = async () => {
    if (!description.trim()) return;
    const err = guardTipo(description);
    if (err) { setError(err); return; }
    // Guardarraíl: si hay plano o bocetos subidos, este botón los IGNORARÍA.
    // Evitamos que el render salga genérico sin respetar el plano.
    if (floorPlan || wallSketches.length > 0) {
      const usePlan = window.confirm(
        'Has subido un plano o boceto, pero "Generar desde la descripción" NO lo usa.\n\n' +
        'Aceptar = generar RESPETANDO el plano/bocetos (recomendado).\n' +
        'Cancelar = generar solo desde el texto (ignora el plano).'
      );
      if (usePlan) { await handleGenerateComposed(); return; }
    }
        setIsGenerating(true);
    setError(null);
    // Auto-scroll al panel de render en móvil
    if (window.innerWidth < 1024 && renderPanelRef.current) {
      setPanelHidden(true);
      setTimeout(() => renderPanelRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
    }
    // ── VARIAS REFERENCIAS → un render por cada imagen ────────────────────
    const refs = refImages.length ? refImages : (refImage ? [refImage] : []);
    if (refs.length > 1) {
      try {
        const outputs = [];
        let noCreditsMsg = null;
        for (let i = 0; i < refs.length; i++) {
          const response = await fetch(`${API_URL}/api/ai-engine/render`, {
            method: 'POST', headers: getAuthHeaders(),
            body: JSON.stringify({
              description: conMedidas(description.trim()),
              style: params.style,
              provider: providerOf(),
              projectType: tipo3d,
              referenceImage: refs[i],
            }),
          });
          // 402 = sin créditos: se detiene y se muestra el mensaje del backend.
          if (response.status === 402) {
            const d = await response.json().catch(() => ({}));
            noCreditsMsg = d.detail || 'Sin créditos de IA.';
            break;
          }
          const data = await response.json();
          if (data && data.success) outputs.push({ ...data, description: `Render ${i + 1}`, timestamp: new Date() });
        }
        if (outputs.length) {
          setRenderResult(outputs[0]);
          setRenderHistory(prev => [...outputs, ...prev].slice(0, 12));
          if (noCreditsMsg) setError(noCreditsMsg);
        } else if (noCreditsMsg) {
          setError(noCreditsMsg);
        } else {
          setError('Error al generar los renders');
        }
      } catch (err) {
        setError('Error de conexión. Verifique su conexión a internet.');
      } finally {
        setIsGenerating(false);
        fetchCredits();
      }
      return;
    }

    const n = Math.max(1, Math.min(3, variantCount));
    const oneRender = async (i) => {
      const hint = n > 1 ? ` (Variación ${i + 1} de ${n}: propón una composición e iluminación ligeramente distintas, mismo brief y materiales.)` : '';
      const response = await fetch(`${API_URL}/api/ai-engine/render`, {
        method: 'POST', headers: getAuthHeaders(),
        body: JSON.stringify({
          description: conMedidas(description.trim()) + hint,
          style: params.style,
          provider: providerOf(),
          projectType: tipo3d,
          referenceImage: refImage || undefined,
        }),
      });
      // 402 = sin créditos de IA: propaga el detalle del backend.
      if (response.status === 402) {
        const d = await response.json().catch(() => ({}));
        const e = new Error(d.detail || 'Sin créditos de IA.');
        e.noCredits = true;
        throw e;
      }
      return response.json();
    };

    try {
      const settled = await Promise.allSettled(Array.from({ length: n }, (_, i) => oneRender(i)));
      const results = settled.map(s => s.status === 'fulfilled' ? s.value : null);
      const noCreditsErr = settled.find(s => s.status === 'rejected' && s.reason?.noCredits);
      const ok = results.filter(d => d && d.success);
      if (ok.length) {
        setRenderResult(ok[0]);
        setRenderHistory(prev => [...ok.map(d => ({ ...d, description, timestamp: new Date() })), ...prev].slice(0, 12));
      } else if (noCreditsErr) {
        setError(noCreditsErr.reason.message);
      } else {
        setError((results.find(Boolean) || {}).error || 'Error al generar el render');
      }
    } catch (err) {
      setError('Error de conexión. Verifique su conexión a internet.');
    } finally {
      setIsGenerating(false);
      fetchCredits();
    }
  };

  // ─── Amueblado virtual: diseñar el mueble SOBRE la foto de la estancia real ──
  const amueblarEstanciaReal = async () => {
    if (!refImage) { setError('Sube primero la FOTO de la estancia real (botón «Subir imagen(es) de referencia»).'); return; }
    if (isGenerating) return;
    setIsGenerating(true); setError(null);
    try {
      const response = await fetch(`${API_URL}/api/ai-engine/render`, {
        method: 'POST', headers: getAuthHeaders(),
        body: JSON.stringify({
          description: conMedidas(description.trim()) || 'cocina moderna funcional bien equipada',
          style: params.style, provider: providerOf(), projectType: tipo3d,
          // 1ª imagen = estancia real; imágenes extra = croquis a lápiz de dónde van los muebles.
          referenceImage: refImage, roomPhoto: true,
          referenceImages: (refImages && refImages.length > 1) ? refImages.slice(1) : undefined,
        }),
      });
      if (response.status === 402) { const d = await response.json().catch(() => ({})); setError(d.detail || 'Sin créditos de IA.'); return; }
      const data = await response.json();
      if (data.success) {
        const merged = { ...data, description: 'Amueblado virtual sobre estancia real' };
        setRenderResult(merged);
        setRenderHistory(prev => [{ ...merged, timestamp: new Date() }, ...prev].slice(0, 12));
        setSchematic(false); setMarks([]);  // el amueblado es solo el render; instalaciones = paso aparte
      } else setError(data.error || 'No se pudo amueblar la estancia.');
    } catch { setError('Error al amueblar la estancia.'); }
    finally { setIsGenerating(false); fetchCredits(); }
  };

  // ─── Generar render por parámetros ──────────────────────────────────────
  const handleGenerateParams = async () => {
    setIsGenerating(true);
    setError(null);

    try {
      const response = await fetch(`${API_URL}/api/ai-engine/render/params`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(params),
      });

      const data = await response.json();

      if (data.success) {
        setRenderResult(data);
        setRenderHistory(prev => [{ ...data, description: 'Parámetros manuales', timestamp: new Date() }, ...prev].slice(0, 10));
      } else {
        setError(data.error || 'Error al generar el render');
      }
    } catch (err) {
      setError('Error de conexión. Verifique su conexión a internet.');
    } finally {
      setIsGenerating(false);
    }
  };

  // ─── Toggle micrófono ───────────────────────────────────────────────────
  const toggleMic = () => {
    if (isListening) {
      stopListening();
    } else {
      baseTextRef.current = description || '';  // conserva lo ya escrito
      resetTranscript();
      startListening();
    }
  };

  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-slate-50 to-slate-100 overflow-hidden">
      {/* Header (el hueco para el logo flotante lo reserva <main> al colapsar) */}
      <div className="shrink-0 px-4 sm:px-8 py-4 sm:py-5 bg-white border-b border-slate-200 shadow-sm">
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl shadow-lg">
              <Wand2 size={20} className="text-white" />
            </div>
            <div>
              <h1 className="text-lg font-black text-slate-900 uppercase tracking-wide">Estudio 3D</h1>
              <p className="text-xs text-slate-500 font-medium">Powered by Motor de IA</p>
            </div>
            {/* Créditos de IA del usuario (bolsa mensual). Admin/master = ilimitado. */}
            {aiCredits && (
              <span
                title="Créditos de IA disponibles este mes"
                className={`ml-1 inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-black ${
                  aiCredits.ilimitado
                    ? 'bg-indigo-100 text-indigo-700'
                    : (aiCredits.restantes <= 0 ? 'bg-red-100 text-red-700' : 'bg-emerald-100 text-emerald-700')
                }`}
              >
                <Sparkles size={12} />
                {aiCredits.ilimitado ? 'Créditos: ilimitado' : `Créditos: ${aiCredits.restantes} restantes`}
              </span>
            )}
          </div>

          <div className="flex items-center gap-2 flex-wrap w-full sm:w-auto">
            {/* Cliente / referencia del proyecto */}
            <input value={cliente} onChange={e => setCliente(e.target.value)} placeholder="Cliente"
              className="px-3 py-2 border border-slate-200 rounded-lg text-sm flex-1 min-w-0 sm:flex-none sm:w-36" />
            <input value={ref} onChange={e => setRef(e.target.value)} placeholder="Referencia"
              className="px-3 py-2 border border-slate-200 rounded-lg text-sm flex-1 min-w-0 sm:flex-none sm:w-28" />
            <button onClick={nuevoProyecto} title="Nuevo proyecto" className="flex items-center gap-1.5 px-3 py-2 bg-white border border-slate-200 text-slate-600 rounded-lg font-bold text-xs hover:bg-slate-50"><Plus size={14} /> Nuevo</button>
            <button onClick={openList} title="Mis proyectos guardados" className="flex items-center gap-1.5 px-3 py-2 bg-white border border-slate-200 text-slate-600 rounded-lg font-bold text-xs hover:bg-slate-50"><FolderOpen size={14} /> Proyectos</button>
            <button onClick={saveDesign} disabled={busy} className="flex items-center gap-1.5 px-3 py-2 bg-emerald-600 text-white rounded-lg font-bold text-xs hover:bg-emerald-700 disabled:opacity-50">{busy ? <Loader size={14} className="animate-spin" /> : <Save size={14} />} Guardar</button>
          </div>

          {/* Mode Toggle */}
          <div className="flex bg-slate-100 rounded-xl p-1">
            <button
              onClick={() => setMode('natural')}
              className={`px-4 py-2 rounded-lg text-xs font-bold uppercase tracking-wider transition-all ${
                mode === 'natural' ? 'bg-white shadow text-indigo-600' : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              <Volume2 size={14} className="inline mr-1.5" />
              Voz / Texto
            </button>
            <button
              onClick={() => setMode('params')}
              className={`px-4 py-2 rounded-lg text-xs font-bold uppercase tracking-wider transition-all ${
                mode === 'params' ? 'bg-white shadow text-indigo-600' : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              <Palette size={14} className="inline mr-1.5" />
              Materiales
            </button>
          </div>
        </div>
      </div>

      {/* Barra temporal de accesos a otras herramientas (solo master) — plegada por defecto */}
      {isMaster && setState && (
        <div className="shrink-0 flex items-center gap-2 flex-wrap px-4 sm:px-8 py-1.5 bg-amber-50 border-b border-amber-200">
          <button onClick={() => setShowOtras(s => !s)}
            className="flex items-center gap-1 text-[10px] font-black text-amber-700 uppercase tracking-wider hover:text-amber-900">
            <ChevronRight size={12} className={`transition-transform ${showOtras ? 'rotate-90' : ''}`} />
            Otras herramientas (temporal · master)
          </button>
          {showOtras && OTRAS_HERRAMIENTAS.map(h => (
            <button key={h.tab} onClick={() => irA(h.tab)}
              className="px-2.5 py-1 rounded-full text-[11px] font-bold bg-white border border-amber-200 text-amber-700 hover:bg-amber-100">
              {h.label}
            </button>
          ))}
        </div>
      )}

      {/* Content */}
      <div className="flex-1 flex flex-col lg:flex-row overflow-y-auto lg:overflow-hidden">
        {/* Panel izquierdo - Entrada */}
        <div className={`${panelHidden ? 'hidden' : ''} w-full lg:w-auto shrink-0 border-b lg:border-b-0 lg:border-r border-slate-200 bg-white flex flex-col min-h-0 overflow-y-auto max-h-[55vh] lg:max-h-none`}
          style={isWide() && !panelHidden ? { width: panelW } : undefined}>
          {mode === 'natural' ? (
            /* ─── Modo Voz/Texto ─── */
            <div className="flex-1 flex flex-col p-6 gap-5">
              {/* PASO 1 — Describe el diseño */}
              <StepHeader n={1} title="Describe el diseño" hint={`${tipoActual.label}. Puedes hablar o escribir.`} />

              {/* Tipo de proyecto (permisos por partidas). Solo se ofrecen los tipos permitidos. */}
              <div className="flex flex-col gap-1.5">
                <p className="text-[10px] font-black text-slate-400 uppercase tracking-wider">Tipo de proyecto</p>
                {tiposPermitidos.length > 1 ? (
                  <div className="flex flex-wrap gap-1.5">
                    {tiposPermitidos.map(tp => (
                      <button key={tp.id} onClick={() => setTipo3d(tp.id)}
                        className={`px-3 py-1.5 rounded-full text-[11px] font-bold border transition-colors ${tipo3d === tp.id ? 'bg-indigo-600 text-white border-indigo-600' : 'bg-white text-slate-500 border-slate-200 hover:bg-slate-50'}`}>
                        {tp.label}
                      </button>
                    ))}
                  </div>
                ) : (
                  <span className="self-start px-3 py-1.5 rounded-full text-[11px] font-black bg-indigo-50 text-indigo-700 border border-indigo-100">{tipoActual.label}</span>
                )}
              </div>

              {/* Plantillas rápidas (arranque en 1 clic) */}
              <div className="flex flex-col gap-1.5">
                <p className="text-[10px] font-black text-slate-400 uppercase tracking-wider">Plantillas rápidas</p>
                <div className="flex gap-1.5 overflow-x-auto pb-1 -mx-1 px-1">
                  {PRESETS.map(p => (
                    <button key={p.id} onClick={() => applyPreset(p)} title={p.desc}
                      className="shrink-0 px-3 py-1.5 rounded-full text-[11px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-100 hover:bg-indigo-100 whitespace-nowrap">
                      {p.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Botón de micrófono grande */}
              <div className="flex justify-center">
                <button
                  onClick={toggleMic}
                  disabled={!isSupported}
                  className={`w-24 h-24 rounded-full flex items-center justify-center transition-all duration-300 shadow-xl ${
                    isListening
                      ? 'bg-red-500 text-white animate-pulse scale-110 shadow-red-300'
                      : isSupported
                        ? 'bg-gradient-to-br from-indigo-500 to-purple-600 text-white hover:scale-105 hover:shadow-2xl'
                        : 'bg-slate-200 text-slate-400 cursor-not-allowed'
                  }`}
                  title={isListening ? 'Detener grabación' : 'Iniciar grabación de voz'}
                >
                  {isListening ? <MicOff size={36} /> : <Mic size={36} />}
                </button>
              </div>

              {isListening && (
                <div className="text-center">
                  <span className="inline-flex items-center gap-2 px-4 py-2 bg-red-50 text-red-600 rounded-full text-xs font-bold uppercase tracking-wider">
                    <span className="w-2 h-2 bg-red-500 rounded-full animate-ping" />
                    Escuchando...
                  </span>
                </div>
              )}

              {!isSupported && (
                <p className="text-center text-xs text-amber-600 bg-amber-50 rounded-lg p-3">
                  Tu navegador no soporta reconocimiento de voz. Usa Chrome o Edge, o escribe tu descripción.
                </p>
              )}

              {/* Campo de texto */}
              <div className="flex-1 flex flex-col">
                <div className="flex items-center justify-between mb-2">
                  <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">
                    Descripción del diseño
                  </label>
                  <label className={`text-[11px] font-bold flex items-center gap-1.5 cursor-pointer px-3 py-1.5 rounded-lg ${analyzingRef ? 'bg-purple-200 text-purple-500' : 'bg-purple-100 text-purple-700 hover:bg-purple-200'}`}>
                    <Image size={14} className={analyzingRef ? 'animate-pulse' : ''} />
                    {analyzingRef ? 'Analizando…' : 'Subir imagen(es) de referencia'}
                    <input type="file" accept="image/*,application/pdf" multiple className="hidden" onChange={handleReferenceUpload} disabled={analyzingRef} />
                  </label>
                </div>
                {refImages.length > 0 && (
                  <div className="mb-2">
                    <div className="flex items-center gap-2 text-[11px] font-bold text-emerald-700 mb-1.5">
                      <CheckCircle size={13} />
                      {refImages.length === 1
                        ? 'Referencia adjunta — el render la respetará'
                        : `${refImages.length} referencias — se generará un render por cada una`}
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {refImages.map((img, i) => (
                        <div key={i} className="relative w-16 h-16 rounded-lg overflow-hidden border border-emerald-200 bg-slate-50">
                          {typeof img === 'string' && img.startsWith('data:image') ? (
                            <img src={img} alt={`Referencia ${i + 1}`} className="w-full h-full object-cover" />
                          ) : (
                            <div className="w-full h-full flex items-center justify-center text-emerald-600"><FileText size={20} /></div>
                          )}
                          <button
                            onClick={() => removeReference(i)}
                            className="absolute top-0.5 right-0.5 bg-white/90 rounded-full text-slate-500 hover:text-red-500 shadow"
                            title="Quitar referencia"><X size={13} /></button>
                        </div>
                      ))}
                    </div>
                    {/* Amueblado virtual: botón específico (solo con permiso). */}
                    {canUseAmueblado && (
                    <button onClick={amueblarEstanciaReal} disabled={isGenerating || !refImage}
                      title="Trata la foto como la estancia REAL (vacía o a reformar) y diseña el mueble dentro, respetando paredes, ventanas, suelo y perspectiva."
                      className="mt-2 w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-[12px] font-black text-white bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500 disabled:opacity-50 shadow-sm">
                      {isGenerating ? <Loader size={15} className="animate-spin" /> : <Sparkles size={15} />}
                      Amueblar esta estancia real (foto)
                    </button>
                    )}
                  </div>
                )}
                {/* Medidas de la estancia — colapsable en móvil */}
                <div className="mb-2 rounded-xl border border-indigo-100 bg-indigo-50/50 flex flex-col">
                  <button onClick={() => setShowMedidas(v => !v)}
                    className="flex items-center justify-between p-2.5 text-left w-full">
                    <div className="flex items-center gap-1.5">
                      <Maximize2 size={13} className="text-indigo-500" />
                      <span className="text-[11px] font-black text-indigo-700 uppercase tracking-wider">Medidas de la estancia</span>
                      <span className="text-[10px] text-indigo-400 hidden sm:inline">— escala real para render y planos acotados</span>
                    </div>
                    <span className="text-indigo-400 shrink-0 ml-2">{showMedidas ? '▲' : '▼'}</span>
                  </button>
                  {showMedidas && <div className="px-2.5 pb-2.5 flex flex-col gap-2">
                  <div className="grid grid-cols-3 gap-2">
                    <label className="flex flex-col gap-1">
                      <span className="text-[10px] font-bold text-slate-400 uppercase">Ancho (cm)</span>
                      <input type="number" value={medidas.ancho} onChange={e => setMedidas(m => ({ ...m, ancho: e.target.value }))} placeholder="360" className="px-2 py-1.5 border border-slate-200 rounded-lg text-sm bg-white" />
                    </label>
                    <label className="flex flex-col gap-1">
                      <span className="text-[10px] font-bold text-slate-400 uppercase">Fondo (cm)</span>
                      <input type="number" value={medidas.fondo} onChange={e => setMedidas(m => ({ ...m, fondo: e.target.value }))} placeholder="300" className="px-2 py-1.5 border border-slate-200 rounded-lg text-sm bg-white" />
                    </label>
                    <label className="flex flex-col gap-1">
                      <span className="text-[10px] font-bold text-slate-400 uppercase">Techo (cm)</span>
                      <input type="number" value={medidas.altura} onChange={e => setMedidas(m => ({ ...m, altura: e.target.value }))} placeholder="250" className="px-2 py-1.5 border border-slate-200 rounded-lg text-sm bg-white" />
                    </label>
                  </div>
                  <input value={medidas.aberturas} onChange={e => setMedidas(m => ({ ...m, aberturas: e.target.value }))}
                    placeholder="Ventanas/puertas: ej. ventana 120 cm en pared izquierda, puerta al fondo"
                    className="px-3 py-1.5 border border-slate-200 rounded-lg text-sm bg-white" />
                  </div>}
                </div>
                <textarea
                  ref={textareaRef}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder={PLACEHOLDER_TIPO[tipo3d] || PLACEHOLDER_TIPO.otro}
                  className="flex-1 min-h-[190px] p-4 border border-slate-200 rounded-xl text-[15px] leading-relaxed text-slate-800 resize-y focus:outline-none focus:ring-2 focus:ring-indigo-300 focus:border-indigo-400 transition-all"
                  style={{ fontFamily: 'system-ui, sans-serif' }}
                />
                <div className="flex flex-wrap gap-1.5 mt-2">
                  {QUICK_PHRASES.map(t => (
                    <button key={t} onClick={() => addPhrase(t)}
                      className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-500 hover:bg-slate-200"
                      title="Añadir a la descripción">+ {t}</button>
                  ))}
                </div>
              </div>

              {/* PASO 2 — Estilo y ambiente (agrupado) - colapsable en móvil */}
              <div className="rounded-xl border border-slate-200 flex flex-col">
                <button onClick={() => setShowEstilo(v => !v)}
                  className="flex items-center justify-between p-3 text-left w-full">
                  <StepHeader n={2} title="Estilo y ambiente" hint="Aspecto, punto de vista e iluminación del render." />
                  <span className="text-slate-400 shrink-0 ml-2">{showEstilo ? '▲' : '▼'}</span>
                </button>
              {showEstilo && <div className="px-3 pb-3 flex flex-col gap-3">
                <div>
                  <p className="text-[10px] font-black text-slate-400 uppercase tracking-wider mb-1.5">Estilo</p>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                    {MATERIALS.styles.map(s => (
                      <button key={s.id} onClick={() => setParams(p => ({ ...p, style: s.id }))}
                        className={`px-3 py-2 rounded-lg text-xs font-bold transition-all ${params.style === s.id ? 'bg-indigo-100 text-indigo-700 ring-2 ring-indigo-300' : 'bg-slate-50 text-slate-600 hover:bg-slate-100'}`}>
                        {s.label}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-[10px] font-black text-slate-400 uppercase tracking-wider mb-1.5">Punto de vista (cámara)</p>
                  <div className="grid grid-cols-2 gap-2">
                    {MATERIALS.cameras.map(c => (
                      <button key={c.id} onClick={() => setCamera(c.id)}
                        className={`px-3 py-2 rounded-lg text-xs font-bold transition-all ${camera === c.id ? 'bg-indigo-100 text-indigo-700 ring-2 ring-indigo-300' : 'bg-slate-50 text-slate-600 hover:bg-slate-100'}`}>
                        {c.label}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-[10px] font-black text-slate-400 uppercase tracking-wider mb-1.5">Iluminación</p>
                  <div className="flex flex-wrap gap-1.5">
                    {MATERIALS.lighting.map(l => (
                      <button key={l.id} onClick={() => setParams(p => ({ ...p, lighting: l.id }))}
                        className={`px-2.5 py-1 rounded-full text-[11px] font-bold transition-all ${params.lighting === l.id ? 'bg-amber-500 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}>
                        {l.label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>}

              {/* Equipamiento */}
              <div className="rounded-xl border border-slate-200 p-3 flex flex-col gap-2">
                <p className="text-[11px] font-black text-slate-500 uppercase tracking-wider">Electrodomésticos</p>
                <div className="flex flex-wrap gap-1.5">
                  {MATERIALS.appliances.map(a => (
                    <button key={a.id} onClick={() => toggleElectro(a.id)}
                      className={`px-2.5 py-1 rounded-full text-[11px] font-bold transition-all ${electros.includes(a.id) ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}>
                      {a.label}
                    </button>
                  ))}
                </div>
                </div>
              </div>
              {/* PASO 3 — Plano + bocetos por pared (opcional, máxima fidelidad) - colapsable */}
              <div className="rounded-xl border border-indigo-100 bg-indigo-50/50 flex flex-col">
                <button onClick={() => setShowPlanos(v => !v)}
                  className="flex items-center justify-between p-3 text-left w-full">
                  <StepHeader n={3} title="Plano + bocetos (opcional)" hint="Para máxima fidelidad: sube el plano en planta y un boceto por cada pared." />
                  <span className="text-indigo-400 shrink-0 ml-2">{showPlanos ? '▲' : '▼'}</span>
                </button>
              {showPlanos && <div className="px-3 pb-3 flex flex-col gap-2.5">
                <p className="text-[11px] text-slate-500">
                  El render seguirá la distribución del plano y el diseño de cada pared, con el acabado descrito en el paso 1.
                </p>
                <label className={`text-[11px] font-bold flex items-center justify-center gap-1.5 cursor-pointer px-3 py-2 rounded-lg ${floorPlan ? 'bg-emerald-100 text-emerald-700' : 'bg-white text-indigo-700 ring-1 ring-indigo-200 hover:bg-indigo-50'}`}>
                  {floorPlan ? <><CheckCircle size={13} /> Plano en planta cargado</> : <><Image size={13} /> Subir plano en planta</>}
                  <input type="file" accept="image/*,application/pdf" className="hidden" onChange={handleFloorPlanUpload} />
                </label>
                {floorPlan && (
                  <button onClick={() => setFloorPlan(null)} className="text-[10px] text-slate-400 hover:text-red-500 self-start">Quitar plano</button>
                )}
                {wallSketches.map((s, i) => (
                  <div key={i} className="flex items-center gap-2 text-[11px] font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-lg px-3 py-1.5">
                    <CheckCircle size={13} /> Boceto pared {i + 1}
                    <button onClick={() => removeWallSketch(i)} className="ml-auto text-emerald-500 hover:text-red-500" title="Quitar boceto"><X size={13} /></button>
                  </div>
                ))}
                <label className="text-[11px] font-bold flex items-center justify-center gap-1.5 cursor-pointer px-3 py-2 rounded-lg bg-white text-indigo-700 ring-1 ring-indigo-200 hover:bg-indigo-50">
                  <Image size={13} /> Añadir boceto de pared
                  <input type="file" accept="image/*" className="hidden" onChange={handleAddWallSketch} />
                </label>
                <button
                  onClick={handleGenerateComposed}
                  disabled={isGenerating || (!floorPlan && wallSketches.length === 0)}
                  className="w-full py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-black uppercase tracking-wider text-xs rounded-xl shadow hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                                    {isGenerating ? <><Loader size={15} className="animate-spin" /> Generando…</> : <><Send size={15} /> Generar render (plano + bocetos)</>}
                </button>
              </div>}
              </div>
              {/* Separador entre las dos vías de generación */}
              <div className="flex items-center gap-2 text-[10px] font-black text-slate-300 uppercase tracking-widest">
                <span className="flex-1 h-px bg-slate-200" /> o <span className="flex-1 h-px bg-slate-200" />
              </div>


              {/* Plan de Instalaciones */}
              {currentImage() && (
                <div className="rounded-xl border border-slate-200 p-3">
                  <button onClick={() => setShowInstallPlan(v => !v)}
                    className="w-full flex items-center justify-between text-[11px] font-black text-slate-600 uppercase tracking-wider">
                    <span>Plan de Instalaciones</span>
                    <span className="text-slate-400">{showInstallPlan ? '▲' : '▼'}</span>
                  </button>
                  {showInstallPlan && (
                    <div className="mt-3 grid grid-cols-2 sm:grid-cols-3 gap-2">
                      {[
                        { label: 'Puntos eléctricos', color: 'bg-yellow-400', icon: '⚡', count: Math.max(4, electros.length + 2) },
                        { label: 'Tomas de agua', color: 'bg-blue-400', icon: '💧', count: electros.includes('fregadero_bajo') || electros.includes('lavavajillas') ? 2 : 1 },
                        { label: 'Desagüe', color: 'bg-slate-500', icon: '🚨', count: electros.includes('fregadero_bajo') || electros.includes('lavavajillas') ? 2 : 1 },
                        { label: 'Gas', color: 'bg-orange-400', icon: '🔥', count: 0 },
                        { label: 'Ventilación', color: 'bg-emerald-400', icon: '🌬️', count: electros.some(e => e.includes('campana')) ? 1 : 0 },
                        { label: 'LED / Iluminación', color: 'bg-purple-400', icon: '💡', count: 2 },
                      ].map(item => (
                        <div key={item.label} className="flex items-center gap-2 p-2 rounded-lg bg-slate-50 border border-slate-100">
                          <span className={`w-3 h-3 rounded-full ${item.color}`} />
                          <div>
                            <p className="text-[10px] font-bold text-slate-700">{item.icon} {item.label}</p>
                            <p className="text-[10px] text-slate-500">{item.count} punto{item.count !== 1 ? 's' : ''}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Acción principal — barra fija siempre visible */}
              <div className="sticky bottom-0 -mx-6 px-6 pt-3 pb-1 bg-gradient-to-t from-white via-white to-white/70 backdrop-blur flex flex-col gap-2">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-[11px] font-black text-slate-500 uppercase tracking-wider">Motor</span>
                  <div className="flex bg-slate-100 rounded-lg p-1">
                    {[['ia1', 'IA 1'], ['ia2', 'IA 2']].map(([id, lbl]) => (
                      <button key={id} onClick={() => setMotor(id)} title={id === 'ia1' ? 'Motor principal' : 'Motor alternativo (más rápido y estable)'}
                        className={`px-3 py-1.5 rounded-md text-xs font-black transition-all ${motor === id ? 'bg-indigo-600 text-white' : 'text-slate-500 hover:bg-slate-200'}`}>{lbl}</button>
                    ))}
                  </div>
                </div>
                <div className="flex items-center justify-between gap-2">
                  <span className="text-[11px] font-black text-slate-500 uppercase tracking-wider">Variaciones</span>
                  <div className="flex bg-slate-100 rounded-lg p-1">
                    {[1, 2, 3].map(n => (
                      <button key={n} onClick={() => setVariantCount(n)}
                        className={`w-9 py-1.5 rounded-md text-xs font-black transition-all ${variantCount === n ? 'bg-indigo-600 text-white' : 'text-slate-500 hover:bg-slate-200'}`}>{n}</button>
                    ))}
                  </div>
                </div>
                <button
                  onClick={handleGenerateNatural}
                  disabled={!description.trim() || isGenerating}
                  className="w-full py-4 bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-black uppercase tracking-wider rounded-xl shadow-lg hover:shadow-xl hover:scale-[1.02] transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 flex items-center justify-center gap-3"
                >
                  {isGenerating ? (
                    <><Loader size={18} className="animate-spin" /> Generando {variantCount > 1 ? `${variantCount} variaciones` : 'render'}...</>
                  ) : (
                    <><Send size={18} /> {variantCount > 1 ? `Generar ${variantCount} variaciones` : 'Generar desde la descripción'}</>
                  )}
                </button>
              </div>
            </div>
          ) : (
            /* ─── Modo Parámetros/Materiales ─── */
            <div className="flex-1 flex flex-col p-6 gap-4 overflow-y-auto">
              {/* Layout */}
              <div>
                <label className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 block">Distribución</label>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                  {MATERIALS.layouts.map(l => (
                    <button
                      key={l.id}
                      onClick={() => setParams(p => ({ ...p, layout: l.id }))}
                      className={`px-3 py-3 rounded-lg text-xs font-bold transition-all flex flex-col items-center gap-1 ${
                        params.layout === l.id
                          ? 'bg-indigo-100 text-indigo-700 ring-2 ring-indigo-300'
                          : 'bg-slate-50 text-slate-600 hover:bg-slate-100'
                      }`}
                    >
                      <span className="text-lg">{l.icon}</span>
                      {l.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Encimera */}
              <div>
                <label className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 block">Encimera</label>
                <select
                  value={params.countertop}
                  onChange={(e) => setParams(p => ({ ...p, countertop: e.target.value }))}
                  className="w-full p-3 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
                >
                  {MATERIALS.countertops.map(m => <option key={m.id} value={m.id}>{m.erp ? "★ " : ""}{m.label}</option>)}
                </select>
              </div>

              {/* Muebles */}
              <div>
                <label className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 block">Muebles</label>
                <select
                  value={params.cabinets}
                  onChange={(e) => setParams(p => ({ ...p, cabinets: e.target.value }))}
                  className="w-full p-3 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
                >
                  {MATERIALS.cabinets.map(m => <option key={m.id} value={m.id}>{m.erp ? "★ " : ""}{m.label}</option>)}
                </select>
              </div>

              {/* Tiradores */}
              <div>
                <label className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 block">Tiradores</label>
                <select
                  value={params.handles}
                  onChange={(e) => setParams(p => ({ ...p, handles: e.target.value }))}
                  className="w-full p-3 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
                >
                  {MATERIALS.handles.map(m => <option key={m.id} value={m.id}>{m.erp ? "★ " : ""}{m.label}</option>)}
                </select>
              </div>

              {/* Suelo */}
              <div>
                <label className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 block">Suelo</label>
                <select
                  value={params.floor}
                  onChange={(e) => setParams(p => ({ ...p, floor: e.target.value }))}
                  className="w-full p-3 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300"
                >
                  {MATERIALS.floors.map(m => <option key={m.id} value={m.id}>{m.erp ? "★ " : ""}{m.label}</option>)}
                </select>
              </div>

              {/* Estilo */}
              <div>
                <label className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 block">Estilo</label>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                  {MATERIALS.styles.map(s => (
                    <button
                      key={s.id}
                      onClick={() => setParams(p => ({ ...p, style: s.id }))}
                      className={`px-3 py-2 rounded-lg text-xs font-bold transition-all ${
                        params.style === s.id
                          ? 'bg-indigo-100 text-indigo-700 ring-2 ring-indigo-300'
                          : 'bg-slate-50 text-slate-600 hover:bg-slate-100'
                      }`}
                    >
                      {s.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Detalles adicionales */}
              <div>
                <label className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 block">Detalles adicionales</label>
                <textarea
                  value={params.additional_details}
                  onChange={(e) => setParams(p => ({ ...p, additional_details: e.target.value }))}
                  placeholder="Ej: ventana grande con vistas, electrodomésticos integrados..."
                  className="w-full p-3 border border-slate-200 rounded-xl text-sm resize-none h-20 focus:outline-none focus:ring-2 focus:ring-indigo-300"
                />
              </div>

              {/* Botón generar */}
              <button
                onClick={handleGenerateParams}
                disabled={isGenerating}
                className="w-full py-4 bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-black uppercase tracking-wider rounded-xl shadow-lg hover:shadow-xl hover:scale-[1.02] transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-3 shrink-0"
              >
                {isGenerating ? (
                  <>
                    <Loader size={18} className="animate-spin" />
                    Generando render...
                  </>
                ) : (
                  <>
                    <Image size={18} />
                    Generar Render 3D
                  </>
                )}
              </button>
            </div>
          )}
        </div>

        {/* Divisor redimensionable + ocultar panel (solo pantallas grandes) */}
        {!panelHidden ? (
          <div className="hidden lg:flex shrink-0 relative items-stretch">
            <div onMouseDown={() => { resizingPanel.current = true; document.body.style.userSelect = 'none'; }}
              title="Arrastra para redimensionar"
              className="w-1.5 cursor-ew-resize bg-slate-100 hover:bg-indigo-400 transition-colors" />
            <button onClick={() => setPanelHidden(true)} title="Ocultar panel de características"
              className="absolute -right-3 top-1/2 -translate-y-1/2 z-10 w-6 h-12 bg-white border border-slate-200 rounded-r-lg flex items-center justify-center text-slate-400 hover:text-indigo-600 shadow">
              <ChevronLeft size={15} />
            </button>
          </div>
        ) : (
          <button onClick={() => setPanelHidden(false)} title="Mostrar panel de características"
            className="hidden lg:flex shrink-0 self-stretch items-center px-1 bg-white border-r border-slate-200 text-slate-400 hover:text-indigo-600">
            <ChevronRight size={18} />
          </button>
        )}

        {/* Panel derecho - Resultado */}
        <div ref={renderPanelRef} className="flex-1 flex flex-col p-4 sm:p-6 min-h-[60vh] lg:min-h-0 lg:overflow-hidden">
          {/* Mostrar/ocultar el panel de opciones en móvil y tablet para dar sitio al render */}
          <button onClick={() => setPanelHidden(v => !v)}
            className="lg:hidden self-start mb-3 flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-black bg-white border border-slate-200 text-slate-600 hover:bg-slate-50 shadow-sm">
            {panelHidden ? <><ChevronRight size={14} /> Mostrar opciones</> : <><ChevronLeft size={14} /> Ocultar opciones</>}
          </button>
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700 flex items-center gap-2">
              <span className="text-red-500 font-bold">Error:</span> {error}
              <button onClick={() => setError(null)} className="ml-auto text-red-400 hover:text-red-600">
                <X size={16} />
              </button>
            </div>
          )}

          {isGenerating ? (
            /* Estado de carga */
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <div className="relative w-32 h-32 mx-auto mb-6">
                  <div className="absolute inset-0 border-4 border-indigo-200 rounded-full animate-ping opacity-20" />
                  <div className="absolute inset-2 border-4 border-indigo-300 rounded-full animate-pulse opacity-40" />
                  <div className="absolute inset-4 border-4 border-t-indigo-600 border-r-transparent border-b-transparent border-l-transparent rounded-full animate-spin" />
                  <div className="absolute inset-0 flex items-center justify-center">
                    <Wand2 size={32} className="text-indigo-600" />
                  </div>
                </div>
                <p className="text-lg font-black text-slate-700 uppercase tracking-wider">Generando render</p>
                <p className="text-sm text-slate-500 mt-2">El motor de IA está creando tu diseño 3D...</p>
                <p className="text-xs text-slate-400 mt-1">Esto puede tardar hasta 30 segundos</p>
              </div>
            </div>
          ) : renderResult ? (
            /* Resultado del render */
            <div className="flex-1 flex flex-col gap-2 overflow-hidden">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between shrink-0 gap-2">
                <h3 className="font-black text-slate-700 uppercase tracking-wider text-xs">Resultado</h3>
                <div className="flex gap-1.5 flex-wrap justify-start sm:justify-end">
                  <button onClick={visitaDecorador} disabled={editing || downloading || !currentImage()}
                    title="Aplica el toque de un decorador/a profesional: estilismo, iluminación, textiles y ambiente premium — sin cambiar los muebles"
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-black text-white bg-gradient-to-r from-fuchsia-600 to-violet-600 hover:from-fuchsia-500 hover:to-violet-500 shadow-sm disabled:opacity-50">
                    {editing ? <Loader size={14} className="animate-spin" /> : <Sparkles size={14} />} Visita de decorador/a
                  </button>
                  <button onClick={mejorarResolucion} disabled={editing || downloading || !currentImage()}
                    title="Recupera nitidez y resolución tras varias ediciones, sin cambiar el diseño"
                    className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-[11px] font-bold bg-slate-100 text-slate-700 hover:bg-slate-200 disabled:opacity-50">
                    {editing ? <Loader size={14} className="animate-spin" /> : <Wand2 size={14} />} HD
                  </button>
                  {canUse4K && (
                  <button onClick={generar4K} disabled={editing || downloading || !currentImage()}
                    title="Genera y descarga la imagen a resolución 4K real (3840 px): nitidez con IA + reescalado a 4K"
                    className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-[11px] font-black text-white bg-gradient-to-r from-slate-800 to-slate-900 hover:from-slate-700 hover:to-slate-800 shadow-sm disabled:opacity-50">
                    {editing ? <Loader size={14} className="animate-spin" /> : <Maximize2 size={14} />} 4K
                  </button>
                  )}
                  <button onClick={downloadRender} disabled={downloading || !currentImage()}
                    className="flex items-center gap-1 px-2.5 py-1.5 bg-indigo-600 text-white rounded-lg text-[11px] font-bold hover:bg-indigo-700 disabled:opacity-50" title="Descargar imagen (PNG)">
                    {downloading ? <Loader size={14} className="animate-spin" /> : <Download size={14} />} Descargar
                  </button>
                  <button onClick={descargarTodo} disabled={downloading || !currentImage()}
                    className="flex items-center gap-1 px-2.5 py-1.5 bg-indigo-500 text-white rounded-lg text-[11px] font-bold hover:bg-indigo-600 disabled:opacity-50" title="Descargar de seguido el render actual y todo el historial (renders, variantes, planos y láminas)">
                    {downloading ? <Loader size={14} className="animate-spin" /> : <Download size={14} />} Descargar todo
                  </button>
                  <button onClick={() => setWatermarkOn(v => !v)}
                    title={state?.logo ? (watermarkOn ? 'Marca de agua ACTIVADA: tu logo se estampa al descargar' : 'Activar marca de agua con tu logo al descargar') : 'Sube tu logo en Ajustes para usar marca de agua'}
                    className={`flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-[11px] font-bold transition-colors ${watermarkOn ? 'bg-slate-800 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'} disabled:opacity-40`}
                    disabled={!state?.logo}>
                    <Image size={14} /> Marca de agua
                  </button>
                  <button onClick={exportPDF} disabled={downloading || !currentImage()}
                    className="flex items-center gap-1 px-2.5 py-1.5 bg-purple-600 text-white rounded-lg text-[11px] font-bold hover:bg-purple-700 disabled:opacity-50" title="Exportar PDF de presentación con logo">
                    <FileText size={14} /> PDF
                  </button>
                  <button onClick={exportDossierPDF} disabled={downloading || !currentImage()}
                    className="flex items-center gap-1 px-2.5 py-1.5 bg-violet-600 text-white rounded-lg text-[11px] font-bold hover:bg-violet-700 disabled:opacity-50" title="Dossier PDF multi-página (portada + render + especificaciones)">
                    <BookOpen size={14} /> Dossier
                  </button>
                  <button onClick={shareWhatsApp} disabled={downloading || !currentImage()}
                    className="flex items-center gap-1 px-2.5 py-1.5 bg-green-600 text-white rounded-lg text-[11px] font-bold hover:bg-green-700 disabled:opacity-50" title="Compartir por WhatsApp">
                    <Share2 size={14} /> WhatsApp
                  </button>
                  <button onClick={attachToBudget} disabled={downloading || !currentImage()}
                    className={`flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-[11px] font-bold disabled:opacity-50 ${attached ? 'bg-emerald-600 text-white' : 'bg-orange-500 text-white hover:bg-orange-600'}`}
                    title={tipo3d === 'armario' ? 'Enviar este render al Presupuestador de Armarios' : 'Adjuntar este render al presupuesto (Cocina Montada)'}>
                    {attached ? <><CheckCircle size={14} /> Adjuntado</> : <><Send size={14} /> {tipo3d === 'armario' ? 'Al presup. armarios' : 'Al presupuesto'}</>}
                  </button>
                  {(originalRef || refImage) && (
                    <button onClick={() => setCompareOn(v => !v)}
                      className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-bold ${compareOn ? 'bg-slate-800 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}
                      title="Comparar la imagen original subida con el render">
                      <Image size={14} /> Comparar
                    </button>
                  )}
                  {canUseRender360 && (orbitFrames.length >= 2 ? (
                    <button
                      onClick={() => setOrbitOn(v => !v)}
                      className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-bold transition-colors ${orbitOn ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}
                      title="Visor 360º: arrastra para girar la cocina"
                    >
                      <RotateCw size={14} /> 360º
                    </button>
                  ) : (
                    <button
                      onClick={generarOrbita}
                      disabled={orbitLoading}
                      className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-bold bg-slate-100 text-slate-600 hover:bg-slate-200 disabled:opacity-50 transition-colors"
                      title="Genera un giro 360º de la cocina para moverla con el ratón (consume créditos de IA)"
                    >
                      {orbitLoading ? <Loader size={14} className="animate-spin" /> : <RotateCw size={14} />}
                      {orbitLoading ? 'Generando…' : 'Generar 360º'}
                    </button>
                  ))}
                  <button
                    onClick={() => { setInteractiveMode(v => !v); setOrbitOn(false); if (!interactiveMode) { setZoom(1); setPanX(0); setPanY(0); } }}
                    className={`p-2 rounded-lg transition-colors ${interactiveMode ? 'bg-indigo-600 text-white' : 'bg-slate-100 hover:bg-slate-200'}`}
                    title={interactiveMode ? 'Desactivar visor interactivo' : 'Visor interactivo (zoom + pan)'}
                  >
                    <Layers size={16} className={interactiveMode ? 'text-white' : 'text-slate-600'} />
                  </button>
                  <button
                    onClick={() => setShowFullscreen(true)}
                    className="p-1.5 bg-slate-100 rounded-lg hover:bg-slate-200 transition-colors"
                    title="Ver en pantalla completa"
                  >
                    <Maximize2 size={16} className="text-slate-600" />
                  </button>
                  <button
                    onClick={() => { setRenderResult(null); setDescription(''); }}
                    className="p-1.5 bg-slate-100 rounded-lg hover:bg-slate-200 transition-colors"
                    title="Nuevo render"
                  >
                    <RotateCcw size={16} className="text-slate-600" />
                  </button>
                </div>
              </div>

              {/* Comparativa referencia vs render */}
              {compareOn && (originalRef || refImage) && renderResult?.result?.images?.[0] ? (
                <div className="flex-1 grid grid-cols-2 gap-3 min-h-[350px]">
                  <div className="bg-slate-100 rounded-2xl overflow-hidden flex items-center justify-center relative p-3" style={{ minHeight: '300px' }}>
                    {(originalRef || refImage).startsWith('data:image') ? (
                      <img src={originalRef || refImage} alt="Referencia original" className="max-w-full max-h-[500px] object-contain rounded-lg" />
                    ) : (
                      <div className="text-center p-4">
                        <FileText size={40} className="text-slate-400 mx-auto mb-2" />
                        <p className="text-xs text-slate-500 font-bold">Referencia (PDF)</p>
                        <p className="text-[10px] text-slate-400 mt-1">No se puede previsualizar un PDF en la comparativa</p>
                      </div>
                    )}
                    <span className="absolute top-2 left-2 px-2 py-1 bg-black/60 rounded text-[10px] font-black text-white uppercase tracking-widest">Referencia</span>
                  </div>
                  <div className="bg-slate-100 rounded-2xl overflow-hidden flex items-center justify-center relative p-3" style={{ minHeight: '300px' }}>
                    <img src={assetSrc(renderResult.result.images[0])} alt="Render" className="max-w-full max-h-[500px] object-contain rounded-lg" />
                    <span className="absolute top-2 left-2 px-2 py-1 bg-indigo-600 rounded text-[10px] font-black text-white uppercase tracking-widest">Render</span>
                  </div>
                </div>
              ) : (
              /* Imagen del render */
              <>
              {renderResult?.result?.images?.[0] && !imgError && !interactiveMode && (
                <div className="shrink-0 mb-2">
                  {/* Botón que despliega el panel: oculto por defecto para no saturar la vista */}
                  <button onClick={() => setShowInstall(s => !s)}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-[11px] font-black transition-all ${showInstall ? 'bg-indigo-600 text-white' : 'bg-white/70 backdrop-blur text-slate-600 hover:bg-white'}`}>
                    <PlugZap size={13} /> Instalaciones y planos técnicos
                    <ChevronRight size={13} className={`transition-transform ${showInstall ? 'rotate-90' : ''}`} />
                  </button>
                  {showInstall && (
                  <div className="mt-2 flex items-center gap-1.5 flex-wrap bg-white/70 backdrop-blur rounded-xl px-2 py-1.5">
                  <span className="text-[10px] font-black text-slate-500 uppercase tracking-wide mr-1">Instalaciones:</span>
                  <button onClick={detectInstalaciones} disabled={detecting}
                    className="px-2.5 py-1 rounded-lg text-[11px] font-black bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-1.5">
                    {detecting ? <Loader size={12} className="animate-spin" /> : <Sparkles size={12} />} {detecting ? 'Detectando…' : 'Detectar auto (IA)'}
                  </button>
                  <button onClick={() => setSchematic(s => !s)}
                    className={`px-2.5 py-1 rounded-lg text-[11px] font-bold flex items-center gap-1 ${schematic ? 'bg-slate-800 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}>
                    ▦ Esquema
                  </button>
                  <button onClick={generarFichaTecnica} disabled={editing}
                    className="px-2.5 py-1 rounded-lg text-[11px] font-black bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-50 flex items-center gap-1.5">
                    {editing ? <Loader size={12} className="animate-spin" /> : <Layers size={12} />} Alzado + planta + medidas
                  </button>
                  {tipo3d === 'cocina' && (
                  <button onClick={generarPlanosTecnicos} disabled={editing}
                    title="Planta acotada + alzado alámbrico EXACTOS (vectoriales, con cotas). Modelado para cocina."
                    className="px-2.5 py-1 rounded-lg text-[11px] font-black bg-slate-700 text-white hover:bg-slate-800 disabled:opacity-50 flex items-center gap-1.5">
                    {editing ? <Loader size={12} className="animate-spin" /> : <FileText size={12} />} Planta + alzado (técnico)
                  </button>
                  )}
                  {tipo3d === 'cocina' && (
                  <button onClick={generarAlzadoDesdeTexto} disabled={editing}
                    title="Alzado técnico EXACTO desde tu descripción (respeta cajones/gavetas por módulo, aunque el render no lo haga)."
                    className="px-2.5 py-1 rounded-lg text-[11px] font-black bg-amber-600 text-white hover:bg-amber-700 disabled:opacity-50 flex items-center gap-1.5">
                    {editing ? <Loader size={12} className="animate-spin" /> : <FileText size={12} />} Alzado desde mi descripción
                  </button>
                  )}
                  {tipo3d === 'cocina' && (
                  <>
                    <button onClick={() => generarVistaAlambrica(true)} disabled={editing}
                      title="Vista alámbrica en blanco y negro (estilo CAD) CON medidas acotadas."
                      className="px-2.5 py-1 rounded-lg text-[11px] font-black bg-zinc-900 text-white hover:bg-black disabled:opacity-50 flex items-center gap-1.5">
                      {editing ? <Loader size={12} className="animate-spin" /> : <Ruler size={12} />} Alámbrica c/ medidas
                    </button>
                    <button onClick={() => generarVistaAlambrica(false)} disabled={editing}
                      title="Vista alámbrica en blanco y negro (estilo CAD) SIN medidas, dibujo limpio."
                      className="px-2.5 py-1 rounded-lg text-[11px] font-black bg-white text-zinc-900 ring-1 ring-zinc-900 hover:bg-zinc-100 disabled:opacity-50 flex items-center gap-1.5">
                      {editing ? <Loader size={12} className="animate-spin" /> : <Box size={12} />} Alámbrica s/ medidas
                    </button>
                  </>
                  )}
                  <span className="w-px h-4 bg-slate-300 mx-0.5" />
                  <span className="text-[10px] font-black text-slate-400 uppercase tracking-wide">Manual:</span>
                  {Object.entries(MARK_TYPES).filter(([, t]) => t.tipos.includes(tipo3d)).map(([id, t]) => { const Ic = t.Icon; return (
                    <button key={id} onClick={() => setMarkTool(markTool === id ? null : id)}
                      className={`px-2.5 py-1 rounded-lg text-[11px] font-bold flex items-center gap-1.5 transition-all ${markTool === id ? 'text-white ring-2 ring-offset-1' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}
                      style={markTool === id ? { background: t.color } : undefined}>
                      <span className="w-4 h-4 rounded-full text-white flex items-center justify-center" style={{ background: t.color }}><Ic size={10} /></span>
                      {t.label}
                    </button>
                  ); })}
                  {marks.length > 0 && <>
                    <button onClick={() => setMarks(m => m.slice(0, -1))} className="px-2 py-1 rounded-lg text-[11px] font-bold bg-slate-100 text-slate-600 hover:bg-slate-200">Deshacer</button>
                    <button onClick={() => { setMarks([]); setMarkTool(null); }} className="px-2 py-1 rounded-lg text-[11px] font-bold bg-slate-100 text-slate-600 hover:bg-slate-200">Limpiar</button>
                    <button onClick={descargarConMarcas} className="px-2.5 py-1 rounded-lg text-[11px] font-black bg-slate-800 text-white hover:bg-slate-900 flex items-center gap-1"><Download size={12} /> Descargar con marcas</button>
                    <button onClick={esquemaGremioPDF} disabled={downloading} title="PDF con las tomas marcadas, sus alturas y leyenda para el fontanero/electricista" className="px-2.5 py-1 rounded-lg text-[11px] font-black bg-emerald-700 text-white hover:bg-emerald-800 disabled:opacity-50 flex items-center gap-1"><FileText size={12} /> Esquema gremio (PDF)</button>
                    <span className="text-[10px] text-slate-400">{marks.length} marca(s)</span>
                  </>}
                  {markTool && marks.length === 0 && <span className="text-[10px] text-indigo-600 font-bold">Haz clic en el render para colocar «{MARK_TYPES[markTool].label}»</span>}
                  </div>
                  )}
                </div>
              )}
              <div className="flex-1 bg-gradient-to-br from-slate-100 to-slate-200 rounded-2xl overflow-hidden shadow-2xl flex items-center justify-center relative"
                onWheel={e => { if (interactiveMode) { e.preventDefault(); setZoom(z => Math.max(0.5, Math.min(5, z + (e.deltaY > 0 ? -0.2 : 0.2)))); } }}
                onMouseDown={e => { if (interactiveMode && e.button === 0) { e.preventDefault(); const startX = e.clientX - panX; const startY = e.clientY - panY; const onMove = (ev) => { setPanX(ev.clientX - startX); setPanY(ev.clientY - startY); }; const onUp = () => { window.removeEventListener('mousemove', onMove); window.removeEventListener('mouseup', onUp); }; window.addEventListener('mousemove', onMove); window.addEventListener('mouseup', onUp); } }}
              >
                {orbitOn && orbitFrames.length >= 2 ? (
                  <div
                    className="w-full h-full flex items-center justify-center select-none"
                    style={{ cursor: 'ew-resize', touchAction: 'none' }}
                    onMouseDown={e => {
                      e.preventDefault();
                      const startX = e.clientX; const startIdx = orbitIndex; const N = orbitFrames.length;
                      const step = Math.max(18, (e.currentTarget.offsetWidth || 600) / (N * 2)); // px por fotograma
                      const onMove = (ev) => {
                        const delta = Math.round((ev.clientX - startX) / step);
                        let i = (startIdx + delta) % N; if (i < 0) i += N;
                        setOrbitIndex(i);
                      };
                      const onUp = () => { window.removeEventListener('mousemove', onMove); window.removeEventListener('mouseup', onUp); };
                      window.addEventListener('mousemove', onMove); window.addEventListener('mouseup', onUp);
                    }}
                  >
                    <img
                      src={assetSrc(orbitFrames[orbitIndex])}
                      alt={`Vista ${orbitIndex + 1} de ${orbitFrames.length}`}
                      draggable={false}
                      className="max-w-full max-h-full object-contain pointer-events-none"
                    />
                    <div className="absolute bottom-3 left-1/2 -translate-x-1/2 flex items-center gap-2 bg-black/55 backdrop-blur px-3 py-1.5 rounded-full">
                      <RotateCw size={13} className="text-white/80" />
                      <span className="text-[11px] font-bold text-white">Arrastra para girar · {orbitIndex + 1}/{orbitFrames.length}</span>
                    </div>
                    <div className="absolute bottom-3 right-3 flex gap-1">
                      {orbitFrames.map((_, i) => (
                        <button key={i} onClick={() => setOrbitIndex(i)}
                          className={`w-2 h-2 rounded-full transition-all ${i === orbitIndex ? 'bg-white scale-125' : 'bg-white/40 hover:bg-white/70'}`} />
                      ))}
                    </div>
                  </div>
                ) : renderResult?.result?.images?.[0] && !imgError ? (
                  <>
                  <img
                    id="render-annot-img"
                    src={assetSrc(renderResult.result.images[0])}
                    alt="Render 3D de cocina"
                    className="max-w-full max-h-full object-contain transition-transform"
                    style={{
                      ...(interactiveMode ? { transform: `scale(${zoom}) translate(${panX / zoom}px, ${panY / zoom}px)`, cursor: 'grab' } : (markTool ? { cursor: 'crosshair' } : {})),
                      ...(schematic ? { filter: 'grayscale(1) brightness(1.22) contrast(0.82)' } : {}),
                    }}
                    onError={() => setImgError(true)}
                    onClick={placeMark}
                  />
                  {/* Capa de marcas de instalaciones: icono + cota de altura (editable) */}
                  {!interactiveMode && marks.map((mk, i) => {
                    const t = MARK_TYPES[mk.type]; const Ic = t.Icon;
                    return (
                      <div key={i} className="absolute z-10 flex flex-col items-center"
                        style={{ left: `${mk.x}%`, top: `${mk.y}%`, transform: 'translate(-50%,-50%)' }}>
                        <button onClick={(e) => { e.stopPropagation(); setEditMark(editMark === i ? null : i); }}
                          title={`${t.label} · altura ${markH(mk)} cm — clic para editar`}
                          className={`w-7 h-7 rounded-full text-white flex items-center justify-center shadow-lg ring-2 ${editMark === i ? 'ring-indigo-500' : 'ring-white'}`}
                          style={{ background: t.color }}>
                          <Ic size={15} />
                        </button>
                        <span className="mt-0.5 px-1.5 py-[1px] rounded bg-white/90 text-[9px] font-black text-slate-700 shadow whitespace-nowrap leading-tight">{markH(mk)} cm</span>

                        {/* Editor de la marca */}
                        {editMark === i && (
                          <div className="absolute top-8 z-20 bg-white rounded-xl shadow-2xl border border-slate-200 p-2 w-56" onClick={(e) => e.stopPropagation()}>
                            <div className="flex items-center justify-between mb-1.5">
                              <span className="text-[10px] font-black text-slate-500 uppercase tracking-wide">Editar punto</span>
                              <button onClick={() => setEditMark(null)} className="text-slate-400 hover:text-slate-700"><X size={13} /></button>
                            </div>
                            <label className="flex items-center gap-2 mb-2">
                              <span className="text-[11px] font-bold text-slate-500 w-12">Altura</span>
                              <input type="number" min="0" max="300" value={markH(mk)}
                                onChange={(e) => { const v = e.target.value === '' ? '' : Math.max(0, Math.min(300, parseInt(e.target.value) || 0)); setMarks(m => m.map((x, j) => j === i ? { ...x, h: v === '' ? null : v } : x)); }}
                                className="flex-1 px-2 py-1 border border-slate-200 rounded-lg text-sm" />
                              <span className="text-[11px] text-slate-400">cm</span>
                            </label>
                            <div className="grid grid-cols-4 gap-1.5 mb-2">
                              {Object.entries(MARK_TYPES).filter(([, tt]) => tt.tipos.includes(tipo3d)).map(([id, tt]) => { const TI = tt.Icon; return (
                                <button key={id} title={tt.label} onClick={() => setMarks(m => m.map((x, j) => j === i ? { ...x, type: id } : x))}
                                  className={`h-8 rounded-lg flex items-center justify-center ${mk.type === id ? 'text-white ring-2 ring-offset-1' : 'bg-slate-100 text-slate-500 hover:bg-slate-200'}`}
                                  style={mk.type === id ? { background: tt.color } : undefined}><TI size={15} /></button>
                              ); })}
                            </div>
                            <button onClick={() => { setMarks(m => m.filter((_, j) => j !== i)); setEditMark(null); }}
                              className="w-full flex items-center justify-center gap-1.5 px-2 py-1.5 bg-rose-50 text-rose-600 rounded-lg text-[11px] font-bold hover:bg-rose-100"><Trash2 size={13} /> Quitar punto</button>
                          </div>
                        )}
                      </div>
                    );
                  })}
                  </>
                ) : imgError ? (
                  <div className="text-center p-8 max-w-sm">
                    <Image size={40} className="text-slate-500 mx-auto mb-3" />
                    <p className="text-slate-300 text-sm font-bold mb-1">No se pudo cargar la imagen del render</p>
                    <p className="text-slate-500 text-xs">El motor devolvió el render pero la imagen no se pudo mostrar. Vuelve a generar; si persiste, avísanos para revisar el motor.</p>
                  </div>
                ) : (
                  <div className="text-center p-8">
                    <Image size={48} className="text-slate-600 mx-auto mb-4" />
                    <p className="text-slate-400 text-sm">
                      {renderResult?.status === 'completed'
                        ? 'Render completado. La imagen se está procesando.'
                        : 'Render en proceso...'}
                    </p>
                    {renderResult?.prompt_used && (
                      <p className="text-slate-500 text-xs mt-4 max-w-md mx-auto italic">
                        "{renderResult.prompt_used.substring(0, 200)}..."
                      </p>
                    )}
                  </div>
                )}

                {/* Badge del motor */}
                <div className="absolute bottom-3 right-3 px-3 py-1.5 bg-black/60 backdrop-blur-sm rounded-lg">
                  <span className="text-[9px] font-black text-white/80 uppercase tracking-widest">
                    Render 3D IA
                  </span>
                </div>
              </div>
              </>
              )}

              {/* Cambio de color/acabado: solo el CATÁLOGO completo por gama. */}
              {currentImage() && (
                <div className="shrink-0 bg-white border border-slate-200 rounded-xl p-2">
                  <div className="flex items-center gap-2 flex-wrap">
                    <button onClick={() => setPaletteOpen(o => !o)}
                      className={`px-3 py-1.5 rounded-lg text-[11px] font-black flex items-center gap-1.5 ${paletteOpen ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-700 hover:bg-slate-200'}`}>
                      <Palette size={13} /> Catálogo de colores {paletteOpen ? '▾' : '▸'}
                    </button>
                    {editing && <span className="text-[11px] text-slate-400 flex items-center gap-1"><Loader size={12} className="animate-spin" /> generando…</span>}
                  </div>

                  {paletteOpen && (
                    <div className="mt-2 border-t border-slate-100 pt-2">
                      <div className="flex gap-1 mb-2">
                        {[['c1', 'ALVIC'], ['c2', 'ACB'], ['c3', 'PORTASUR']].map(([id, lbl]) => (
                          <button key={id} onClick={() => { setColorTab(id); setOpenGama(null); }}
                            className={`px-3 py-1 rounded-lg text-[11px] font-black ${colorTab === id ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}>
                            {lbl}
                          </button>
                        ))}
                      </div>
                      <div className="max-h-64 overflow-y-auto pr-1 flex flex-col gap-1">
                        {gamas.length === 0 && <p className="text-[11px] text-slate-400 py-2">Sin colores en esta pestaña todavía.</p>}
                        {gamas.map(g => (
                          <div key={g.gama} className="rounded-lg border border-slate-100">
                            <button onClick={() => setOpenGama(o => o === g.gama ? null : g.gama)}
                              className="w-full flex items-center justify-between px-2.5 py-1.5 text-[11px] font-black text-slate-700 hover:bg-slate-50">
                              <span>{g.gama} <span className="text-slate-400 font-bold">({g.items.length})</span></span>
                              <span className="text-slate-400">{openGama === g.gama ? '▾' : '▸'}</span>
                            </button>
                            {openGama === g.gama && (
                              <div className="px-2.5 pb-2 grid grid-cols-1 gap-1">
                                {g.items.map(c => (
                                  <button key={c.label} onClick={() => colorVariant(c.modelo || c.forma ? { ...c, label: `${g.gama.replace(/\s*\(.*\)$/, '')} ${c.label}`.trim() } : `${g.gama.replace(/\s*\(.*\)$/, '')} ${c.label}`.trim())} disabled={editing}
                                    title={c.forma ? `${c.modelo || c.label} — ${c.forma}` : `Muebles en ${c.label}`}
                                    className="flex items-center gap-2 text-left px-1.5 py-1 rounded hover:bg-indigo-50 disabled:opacity-40">
                                    <span className="w-5 h-5 rounded-full border-2 border-white ring-1 ring-slate-300 shadow shrink-0" style={{ background: c.bg }} />
                                    <span className="text-[11px] text-slate-600 truncate">{c.label}</span>
                                  </button>
                                ))}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Editar el render en lenguaje natural (con dictado y elemento por imagen) */}
              {currentImage() && (
                <div className="shrink-0 flex items-center gap-2 bg-white border border-slate-200 rounded-xl p-2 flex-wrap">
                  <Wand2 size={16} className="text-purple-500 shrink-0 ml-1" />
                  {/* Miniatura del elemento subido (a copiar en la cocina) */}
                  {editRefImage && (
                    <div className="relative shrink-0">
                      <img src={editRefImage} alt="Elemento" className="h-9 w-9 object-cover rounded-lg border border-purple-200" />
                      <button onClick={() => setEditRefImage(null)} title="Quitar elemento"
                        className="absolute -top-1.5 -right-1.5 bg-white border border-slate-300 rounded-full p-0.5 shadow"><X size={10} /></button>
                    </div>
                  )}
                  <input value={editInstruction} onChange={e => setEditInstruction(e.target.value)}
                    onKeyDown={e => { if (e.key === 'Enter' && !editing && (editInstruction.trim() || editRefImage)) editRender(); }}
                    onPaste={captureClipboardImage}
                    placeholder={editRefImage ? "Opcional: dónde/cómo colocar el elemento…" : "Editar o pega una imagen (Ctrl+V): 'cambia a azul navy', 'añade campana de isla'…"}
                    className="flex-1 min-w-[140px] px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-300" />
                  {/* Micro: dictar el cambio */}
                  {editSp.isSupported && (
                    <button onClick={toggleEditMic} title={editSp.isListening ? 'Detener dictado' : 'Dictar el cambio'}
                      className={`shrink-0 p-2 rounded-lg border ${editSp.isListening ? 'bg-red-500 text-white border-red-500 animate-pulse' : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'}`}>
                      {editSp.isListening ? <MicOff size={16} /> : <Mic size={16} />}
                    </button>
                  )}
                  {/* Subir una imagen de elemento (puerta, mueble…) a copiar */}
                  <label title="Subir imagen de un elemento (puerta, mueble…) para copiarlo en la cocina"
                    className="shrink-0 p-2 rounded-lg border bg-white text-slate-600 border-slate-200 hover:bg-slate-50 cursor-pointer">
                    <Upload size={16} />
                    <input type="file" accept="image/*" className="hidden" onChange={onEditRefUpload} />
                  </label>
                  {/* Botón + para añadir líneas de edición */}
                  <button onClick={() => setEditLines(prev => [...prev, ''])} title="Añadir otra instrucción de edición"
                    className="shrink-0 p-2 rounded-lg border bg-white text-purple-600 border-purple-200 hover:bg-purple-50">
                    <Plus size={16} />
                  </button>
                  <button onClick={editRender} disabled={editing || (!editInstruction.trim() && !editLines.some(l => l.trim()) && !editRefImage)}
                    className="flex items-center gap-1.5 px-4 py-2 bg-purple-600 text-white rounded-lg text-xs font-bold hover:bg-purple-700 disabled:opacity-50 shrink-0">
                    {editing ? <><Loader size={14} className="animate-spin" /> Aplicando…</> : <><Send size={14} /> Aplicar {editLines.length > 0 ? `${editLines.length + 1} cambios` : 'cambio'}</>}
                  </button>
                </div>
              )}
              {/* Líneas adicionales de edición (multi-línea) */}
              {editLines.length > 0 && currentImage() && (
                <div className="shrink-0 flex flex-col gap-1.5 bg-purple-50 border border-purple-100 rounded-xl p-2">
                  {editLines.map((line, idx) => (
                    <div key={idx} className="flex items-center gap-2">
                      <span className="text-[10px] font-bold text-purple-400 w-4 text-center">{idx + 2}</span>
                      <input value={line} onChange={e => { const copy = [...editLines]; copy[idx] = e.target.value; setEditLines(copy); }}
                        placeholder={`Cambio adicional ${idx + 2}...`}
                        className="flex-1 px-3 py-1.5 border border-purple-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-300" />
                      <button onClick={() => setEditLines(prev => prev.filter((_, i) => i !== idx))} title="Eliminar línea"
                        className="shrink-0 p-1 text-red-400 hover:text-red-600 hover:bg-red-50 rounded"><X size={14} /></button>
                    </div>
                  ))}
                </div>
              )}

              {/* Info del render */}
              {renderResult?.duration_seconds && (
                <div className="shrink-0 flex items-center gap-4 text-xs text-slate-500">
                  <span>Tiempo: {renderResult.duration_seconds}s</span>
                  {renderResult?.parsed_params?.layout && (
                    <span>Layout: {renderResult.parsed_params.layout}</span>
                  )}
                  <span className="ml-auto font-bold text-indigo-500">{renderResult.engine}</span>
                </div>
              )}
            </div>
          ) : (
            /* Estado vacío */
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center max-w-md">
                <div className="w-20 h-20 mx-auto mb-6 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl flex items-center justify-center shadow-lg">
                  <Wand2 size={36} className="text-white" />
                </div>
                <h3 className="font-black text-slate-800 uppercase tracking-wider mb-2 text-lg">Estudio 3D</h3>
                <p className="text-sm text-slate-500 leading-relaxed mb-6">
                  Describe tu diseño (cocina, armario, baño, mueble a medida…) por voz o texto, o elige materiales.
                  Genera un render fotorrealista en segundos y preséntalo al cliente.
                </p>
                <div className="grid grid-cols-3 gap-3 text-left">
                  {[
                    { n: '1', t: 'Describe', d: 'Voz o texto' },
                    { n: '2', t: 'Ajusta', d: 'Estilo y medidas' },
                    { n: '3', t: 'Genera', d: 'Descarga o PDF' },
                  ].map(s => (
                    <div key={s.n} className="rounded-xl border border-slate-200 bg-white p-3">
                      <span className="w-6 h-6 rounded-full bg-indigo-600 text-white text-xs font-black flex items-center justify-center mb-2">{s.n}</span>
                      <p className="text-xs font-black text-slate-700">{s.t}</p>
                      <p className="text-[11px] text-slate-400">{s.d}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Historial de renders */}
          {renderHistory.length > 0 && !isGenerating && (
            <div className="shrink-0 mt-4 border-t border-slate-200 pt-4">
              <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">Historial reciente</h4>
              <div className="flex gap-3 overflow-x-auto pb-2">
                {renderHistory.map((item, i) => (
                  <div key={i} className="relative shrink-0 group">
                    <button
                      onClick={() => setRenderResult(item)}
                      className="w-16 h-16 bg-slate-200 rounded-xl overflow-hidden hover:ring-2 hover:ring-indigo-300 transition-all block"
                      title={item.description}
                    >
                      {item?.result?.images?.[0] ? (
                        <img src={assetSrc(item.result.images[0])} alt="" className="w-full h-full object-cover" />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-slate-400">
                          <Image size={16} />
                        </div>
                      )}
                    </button>
                    <button onClick={() => setRenderHistory(prev => prev.filter((_, idx) => idx !== i))}
                      className="absolute -top-1.5 -right-1.5 w-5 h-5 bg-white border border-slate-200 rounded-full flex items-center justify-center text-slate-400 hover:text-red-500 shadow opacity-0 group-hover:opacity-100 transition-opacity"
                      title="Quitar del historial"><X size={11} /></button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Mis proyectos guardados */}
      {Array.isArray(savedList) && (
        <div className="fixed inset-0 z-[9998] bg-black/50 flex items-center justify-center p-4" onClick={() => setSavedList(null)}>
          <div className="bg-white rounded-2xl w-full max-w-lg max-h-[80vh] overflow-hidden flex flex-col" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
              <h3 className="font-black text-slate-800 shrink-0">Mis proyectos 3D</h3>
              <div className="flex items-center gap-2">
                <button onClick={nuevoProyecto}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-black bg-indigo-600 text-white hover:bg-indigo-700">
                  <Plus size={14} /> Proyecto nuevo
                </button>
                <button onClick={() => { setSelMode(v => !v); setSelIds([]); }}
                  title="Selecciona varios proyectos del mismo cliente y únelos en uno solo (todas las imágenes juntas)"
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-black ${selMode ? 'bg-amber-600 text-white hover:bg-amber-700' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}>
                  <Layers size={14} /> {selMode ? 'Cancelar' : 'Unir'}
                </button>
                <button onClick={() => { setSavedList(null); setSelMode(false); setSelIds([]); }} className="p-1.5 text-slate-400 hover:text-slate-700"><X size={18} /></button>
              </div>
            </div>
            {savedList.length > 0 && (
              <div className="px-4 pt-3 pb-1">
                <input
                  autoFocus
                  value={savedSearch}
                  onChange={e => setSavedSearch(e.target.value)}
                  placeholder="Buscar por nombre o referencia…"
                  className="w-full px-3 py-2 rounded-lg text-sm border border-slate-200 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500/40"
                />
              </div>
            )}
            <div className="p-4 overflow-y-auto">
              {(() => {
                const q = savedSearch.trim().toLowerCase();
                const shown = q ? savedList.filter(d => `${d.cliente || ''} ${d.ref || ''}`.toLowerCase().includes(q)) : savedList;
                if (savedList.length === 0) return (
                <p className="text-sm text-slate-400 text-center py-8">No tienes proyectos guardados todavía.</p>
                );
                if (shown.length === 0) return (
                <p className="text-sm text-slate-400 text-center py-8">Sin resultados para “{savedSearch}”.</p>
                );
                const toggleSel = (id) => setSelIds(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
                return shown.map(d => (
                <div key={d.id} onClick={() => selMode && toggleSel(d.id)}
                  className={`flex items-center gap-3 border rounded-xl p-2 mb-2 ${selMode ? 'cursor-pointer' : ''} ${selMode && selIds.includes(d.id) ? 'border-amber-400 bg-amber-50' : 'border-slate-200 hover:bg-slate-50'}`}>
                  {selMode && (
                    <input type="checkbox" readOnly checked={selIds.includes(d.id)} className="w-4 h-4 shrink-0 rounded accent-amber-600" />
                  )}
                  <div className="w-12 h-12 shrink-0 bg-slate-200 rounded-lg overflow-hidden">
                    {d.images?.[0] ? <img src={assetSrc(d.images[0])} alt="" className="w-full h-full object-cover" /> : <div className="w-full h-full flex items-center justify-center text-slate-400"><Image size={16} /></div>}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-bold text-slate-700 text-sm truncate">{d.cliente || 'Sin cliente'}{d.ref ? ` · ${d.ref}` : ''}</p>
                    {d.updatedAt && <p className="text-[10px] text-slate-400">{new Date(d.updatedAt).toLocaleString('es-ES')}</p>}
                  </div>
                  {!selMode && <>
                  <button onClick={() => loadDesign(d)} className="px-3 py-1.5 bg-indigo-600 text-white rounded-lg text-xs font-bold hover:bg-indigo-700">Abrir</button>
                  <button onClick={() => deleteDesign(d.id)} className="p-1.5 text-red-400 hover:text-red-600 hover:bg-red-50 rounded-lg"><Trash2 size={16} /></button>
                  </>}
                </div>
                ));
              })()}
            </div>
            {selMode && (
              <div className="px-4 py-3 border-t border-slate-100 flex items-center gap-3">
                <span className="text-xs text-slate-500 flex-1">{selIds.length} seleccionado(s) · se creará un proyecto nuevo con todas sus imágenes.</span>
                <button onClick={unirProyectos} disabled={busy || selIds.length < 2}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-black bg-amber-600 text-white hover:bg-amber-700 disabled:opacity-50">
                  {busy ? <Loader size={14} className="animate-spin" /> : <Layers size={14} />} Unir y guardar juntos
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Modal volcado dual P1/P2 */}
      {showDualModal === 'choosing' && (
        <div className="fixed inset-0 bg-black/60 z-[9998] flex items-center justify-center p-4" onClick={() => setShowDualModal(null)}>
          <div className="bg-white rounded-2xl shadow-2xl p-6 max-w-sm w-full" onClick={e => e.stopPropagation()}>
            <h3 className="font-black text-slate-800 text-sm uppercase tracking-wider mb-4 text-center">Volcar render al presupuesto</h3>
            <p className="text-xs text-slate-500 text-center mb-4">Tienes ambos presupuestadores activos. Elige dónde enviar el render:</p>
            <div className="flex gap-3">
              <button onClick={() => doAttach('presupuestador2')}
                className="flex-1 py-3 rounded-xl bg-emerald-600 text-white font-bold text-sm hover:bg-emerald-700 transition-colors">
                Cocina Montada (P1)
              </button>
              <button onClick={() => doAttach('budget')}
                className="flex-1 py-3 rounded-xl bg-indigo-600 text-white font-bold text-sm hover:bg-indigo-700 transition-colors">
                Cocina Montada 2 (P2)
              </button>
            </div>
            <button onClick={() => setShowDualModal(null)} className="mt-3 w-full text-xs text-slate-400 hover:text-slate-600 text-center">Cancelar</button>
          </div>
        </div>
      )}

      {/* Fullscreen Modal */}
      {showFullscreen && renderResult?.result?.images?.[0] && (
        <div className="fixed inset-0 bg-black/95 z-[9999] flex items-center justify-center p-4" onClick={() => setShowFullscreen(false)}>
          <button className="absolute top-6 right-6 text-white/70 hover:text-white" onClick={() => setShowFullscreen(false)}>
            <X size={32} />
          </button>
          <img
            src={assetSrc(renderResult.result.images[0])}
            alt="Render 3D"
            className="max-w-full max-h-full object-contain rounded-xl shadow-2xl"
          />
        </div>
      )}

      {/* Saldo de renders: acceso siempre visible, para poder recargar
          sin salir del estudio cuando se agota el cupo. */}
      <button onClick={() => setVerRecarga(true)} title="Tus renders de IA"
        className="fixed bottom-4 right-4 z-[60] px-3 py-2 rounded-full bg-amber-600 hover:bg-amber-700 text-white text-xs font-black shadow-lg flex items-center gap-1.5">
        <Zap size={14} /> Mis renders
      </button>
      <RecargarRenders abierto={verRecarga} onClose={() => setVerRecarga(false)} />
    </div>
  );
}
