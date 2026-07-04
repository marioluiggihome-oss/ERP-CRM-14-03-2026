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
import { Mic, MicOff, Send, Image, Loader, Palette, RotateCcw, Download, Maximize2, X, Volume2, Wand2, CheckCircle, Save, FolderOpen, FileText, Trash2, Plus } from 'lucide-react';
import { getToken } from '../services/api';
import { DOOR_FINISHES, MV_TARIFFS } from '../constants';
import { avgEurPerMl } from '../utils/pricing';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// ─── Hook para Web Speech API ────────────────────────────────────────────────
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
];

// Frases rápidas para enriquecer la descripción con un clic (detalles habituales).
const QUICK_PHRASES = [
  'isla central', 'península abierta al salón', 'columna de horno y microondas',
  'campana de isla', 'encimera volada para taburetes', 'zona de office con banco',
  'luz LED bajo los altos', 'fregadero bajo encimera', 'vinoteca integrada',
  'despensa/columna de almacenaje', 'copete a juego con la encimera', 'zócalo retranqueado',
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
export default function AIRenderStudio({ state, setState }) {
  const isMaster = state?.currentUser?.isAdmin === true;
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
  const [refImage, setRefImage] = useState(null); // imagen/PDF de referencia (base64) para que el modelo la "vea"
  const [floorPlan, setFloorPlan] = useState(null);    // plano en planta (dataURL)
  const [wallSketches, setWallSketches] = useState([]); // bocetos por pared (dataURL[])
  const [isGenerating, setIsGenerating] = useState(false);
  const [renderResult, setRenderResult] = useState(null);
  const [renderHistory, setRenderHistory] = useState([]);
  const [error, setError] = useState(null);
  const [showFullscreen, setShowFullscreen] = useState(false);
  const [analyzingRef, setAnalyzingRef] = useState(false);
  // Guardado de proyectos (cliente + referencia) y descarga.
  const [cliente, setCliente] = useState('');
  const [ref, setRef] = useState('');
  const [savedId, setSavedId] = useState(null);
  const [savedList, setSavedList] = useState(null); // null = oculto
  const [busy, setBusy] = useState(false);
  const [downloading, setDownloading] = useState(false);
  // Captura de medidas de la estancia (para proporción/escala reales).
  const [medidas, setMedidas] = useState({ ancho: '', fondo: '', altura: '', aberturas: '' });
  // Edición del render en lenguaje natural (iterar sin empezar de cero).
  const [editInstruction, setEditInstruction] = useState('');
  const [editing, setEditing] = useState(false);
  // Electrodomésticos, cámara y nº de variaciones (Tanda 3).
  const [electros, setElectros] = useState([]);
  const [camera, setCamera] = useState('eyelevel');
  const [variantCount, setVariantCount] = useState(1);
  // Motor de render: 'ia1' = Gemini (por defecto, más fiel), 'ia2' = Manus. Sin exponer nombres.
  const [motor, setMotor] = useState('ia1');
  const providerOf = () => (motor === 'ia2' ? 'manus' : 'gemini');
  const [attached, setAttached] = useState(false);
  const [compareOn, setCompareOn] = useState(false); // ver referencia vs render
  const [imgError, setImgError] = useState(false);    // la imagen del render no cargó
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
  useEffect(() => { setImgError(false); }, [renderResult]);

  // La transcripción se concatena al texto base (lo escrito antes de dictar).
  useEffect(() => {
    if (transcript) {
      const base = baseTextRef.current;
      setDescription(base ? `${base.trim()} ${transcript}` : transcript);
    }
  }, [transcript]);

  const getAuthHeaders = () => {
    const token = getToken();
    return { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };
  };

  // Las imágenes del render se sirven por el proxy interno (marca blanca). Como
  // un <img> no puede enviar cabeceras, el token JWT viaja como query param.
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
    return extra ? `${extra}\n${desc}` : desc;
  };

  // Estimación de precio ORIENTATIVA a partir de medidas + materiales + equipamiento.
  const estimarPrecio = () => {
    const anchoM = (Number(medidas.ancho) || 0) / 100;
    const fondoM = (Number(medidas.fondo) || 0) / 100;
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
      lib: cat?.lib, group: cat?.group,
    };
  };
  const toggleElectro = (id) => setElectros(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  // Aplica una plantilla: rellena la descripción (si está vacía) y ajusta ambiente.
  const applyPreset = (p) => {
    setDescription(prev => prev.trim() ? `${prev.trim()}\n${p.desc}` : p.desc);
    setParams(prm => ({ ...prm, style: p.style, lighting: p.lighting }));
    setCamera(p.camera);
    setElectros(p.electros || []);
  };
  // Añade una frase rápida al final de la descripción.
  const addPhrase = (t) => setDescription(prev => {
    const has = prev.toLowerCase().includes(t.toLowerCase());
    if (has) return prev;
    return prev.trim() ? `${prev.trim()}, ${t}` : t;
  });

  // Paleta rápida de colores de mueble para generar variantes de color en 1 clic.
  const COLORS_VARIANTES = [
    { label: 'Blanco mate', hex: '#f1f5f9' },
    { label: 'Antracita', hex: '#3f3f46' },
    { label: 'Azul navy', hex: '#1e293b' },
    { label: 'Verde sage', hex: '#8a9a5b' },
    { label: 'Roble natural', hex: '#c8a26a' },
    { label: 'Negro mate', hex: '#18181b' },
  ];

  // Genera una variante del render actual cambiando SOLO el color de los muebles.
  const colorVariant = async (colorLabel) => {
    const img = currentImage();
    if (!img || editing) return;
    setEditing(true); setError(null);
    try {
      const dataUrl = await imageToDataUrl(img);
      const response = await fetch(`${API_URL}/api/ai-engine/render`, {
        method: 'POST', headers: getAuthHeaders(),
        body: JSON.stringify({
          description: `Cambia ÚNICAMENTE el color/acabado de los frentes de los muebles a "${colorLabel}", manteniendo EXACTAMENTE el mismo diseño, distribución, encimera, tiradores, electrodomésticos, suelo, cámara e iluminación. No cambies nada más.`,
          style: params.style,
          provider: providerOf(),
          referenceImage: dataUrl,
        }),
      });
      const data = await response.json();
      if (data.success) {
        const merged = { ...data, description: `${renderResult?.description || description}\n[Color] ${colorLabel}` };
        setRenderResult(merged);
        setRenderHistory(prev => [{ ...merged, timestamp: new Date() }, ...prev].slice(0, 12));
      } else setError(data.error || 'No se pudo generar la variante de color');
    } catch { setError('Error de conexión al generar la variante.'); }
    finally { setEditing(false); }
  };

  // ─── Editar el render existente en lenguaje natural ─────────────────────────
  const editRender = async () => {
    const img = currentImage();
    if (!img || !editInstruction.trim()) return;
    setEditing(true); setError(null);
    try {
      const dataUrl = await imageToDataUrl(img);
      const response = await fetch(`${API_URL}/api/ai-engine/render`, {
        method: 'POST', headers: getAuthHeaders(),
        body: JSON.stringify({
          description: `Modifica el render adjunto manteniendo el mismo diseño, encuadre e iluminación. Cambio solicitado: ${editInstruction.trim()}. No cambies nada más.`,
          style: params.style,
          provider: providerOf(),
          referenceImage: dataUrl,
        }),
      });
      const data = await response.json();
      if (data.success) {
        const merged = { ...data, description: `${renderResult?.description || description}\n[Edición] ${editInstruction.trim()}` };
        setRenderResult(merged);
        setRenderHistory(prev => [{ ...merged, timestamp: new Date() }, ...prev].slice(0, 10));
        setEditInstruction('');
      } else setError(data.error || 'No se pudo editar el render');
    } catch { setError('Error de conexión al editar el render.'); }
    finally { setEditing(false); }
  };

  const nombreArchivo = (ext) => {
    const base = (cliente || ref || 'render-3d').trim().replace(/\s+/g, '_').replace(/[^\w\-]/g, '');
    return `${base || 'render-3d'}.${ext}`;
  };

  // ─── Descargar el render (PNG) ──────────────────────────────────────────────
  const downloadRender = async () => {
    const img = currentImage();
    if (!img) return;
    setDownloading(true);
    try {
      const dataUrl = await imageToDataUrl(img);
      const a = document.createElement('a');
      a.href = dataUrl; a.download = nombreArchivo('png');
      document.body.appendChild(a); a.click(); a.remove();
    } catch { setError('No se pudo descargar la imagen.'); }
    finally { setDownloading(false); }
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
      } else { pdf.setFontSize(15); pdf.setTextColor(30); pdf.setFont(undefined, 'bold'); pdf.text('LUIGGI HOME', M, 17); pdf.setFont(undefined, 'normal'); }
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

  // ─── Guardar / abrir proyectos ──────────────────────────────────────────────
  const saveDesign = async () => {
    const img = currentImage();
    if (!img) { setError('Genera un render antes de guardar.'); return; }
    if (!(cliente || ref).trim()) { setError('Pon un cliente o referencia para guardar el proyecto.'); return; }
    setBusy(true); setError(null);
    try {
      const r = await fetch(`${API_URL}/api/ai-engine/designs`, {
        method: 'POST', headers: getAuthHeaders(),
        body: JSON.stringify({ id: savedId || undefined, cliente, ref, description: renderResult?.description || description, style: params.style, images: [img] }),
      });
      const d = await r.json();
      if (d.success) { setSavedId(d.design.id); }
      else setError(d.error || 'No se pudo guardar.');
    } catch { setError('Error al guardar el proyecto.'); }
    finally { setBusy(false); }
  };
  const openList = async () => {
    try {
      const r = await fetch(`${API_URL}/api/ai-engine/designs`, { headers: getAuthHeaders() });
      const d = await r.json();
      setSavedList(d.designs || []);
    } catch { setError('No se pudo cargar la lista.'); }
  };
  const loadDesign = (dsg) => {
    setCliente(dsg.cliente || ''); setRef(dsg.ref || ''); setDescription(dsg.description || '');
    if (dsg.style) setParams(p => ({ ...p, style: dsg.style }));
    setSavedId(dsg.id); setSavedList(null);
    if (dsg.images?.[0]) setRenderResult({ success: true, result: { images: dsg.images }, description: dsg.description });
  };
  const deleteDesign = async (id) => {
    if (!window.confirm('¿Eliminar este proyecto guardado?')) return;
    try {
      await fetch(`${API_URL}/api/ai-engine/designs/${id}`, { method: 'DELETE', headers: getAuthHeaders() });
      setSavedList(prev => (prev || []).filter(x => x.id !== id));
      if (savedId === id) setSavedId(null);
    } catch { setError('No se pudo eliminar.'); }
  };
  // ─── Adjuntar el render al presupuesto (Resumen Totales) ────────────────────
  const attachToBudget = async () => {
    const img = currentImage();
    if (!img) return;
    setDownloading(true);
    try {
      const dataUrl = await imageToDataUrl(img);
      localStorage.setItem('render3d_attach', JSON.stringify({ image: dataUrl, cliente, ref, ts: Date.now() }));
      setAttached(true);
      setTimeout(() => setAttached(false), 4000);
    } catch { setError('No se pudo adjuntar el render.'); }
    finally { setDownloading(false); }
  };

  const nuevoProyecto = () => {
    setCliente(''); setRef(''); setSavedId(null); setRenderResult(null);
    setDescription(''); setRefImage(null); setFloorPlan(null); setWallSketches([]); setError(null);
  };

  // ─── Subir imagen/PDF de referencia → la IA la describe y enriquece el prompt ───
  const handleReferenceUpload = async (e) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;
    setAnalyzingRef(true);
    setError(null);
    try {
      const b64 = await new Promise((res, rej) => {
        const fr = new FileReader();
        fr.onload = () => res(fr.result);
        fr.onerror = rej;
        fr.readAsDataURL(file);
      });
      const response = await fetch(`${API_URL}/api/ai-engine/describe-reference`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ fileBase64: b64 }),
      });
      // Guardar la imagen para pasársela TAMBIÉN al generador (no solo el texto),
      // así el render respeta distribución, proporciones y medidas de la referencia.
      setRefImage(b64);
      const data = await response.json();
      if (data.success && data.description) {
        setDescription(prev => {
          const next = prev?.trim()
            ? `${prev.trim()}\n\n[Referencia subida] ${data.description}`
            : data.description;
          return next;
        });
      } else {
        setError(data.error || 'No se pudo leer la imagen de referencia');
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

    const n = Math.max(1, Math.min(3, variantCount));
    const oneRender = async (i) => {
      const hint = n > 1 ? ` (Variación ${i + 1} de ${n}: propón una composición e iluminación ligeramente distintas, mismo brief y materiales.)` : '';
      const response = await fetch(`${API_URL}/api/ai-engine/render`, {
        method: 'POST', headers: getAuthHeaders(),
        body: JSON.stringify({
          description: conMedidas(description.trim()) + hint,
          style: params.style,
          provider: providerOf(),
          referenceImage: refImage || undefined,
        }),
      });
      return response.json();
    };

    try {
      const results = await Promise.all(Array.from({ length: n }, (_, i) => oneRender(i).catch(() => null)));
      const ok = results.filter(d => d && d.success);
      if (ok.length) {
        setRenderResult(ok[0]);
        setRenderHistory(prev => [...ok.map(d => ({ ...d, description, timestamp: new Date() })), ...prev].slice(0, 12));
      } else {
        setError((results.find(Boolean) || {}).error || 'Error al generar el render');
      }
    } catch (err) {
      setError('Error de conexión. Verifique su conexión a internet.');
    } finally {
      setIsGenerating(false);
    }
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
      {/* Header */}
      <div className="shrink-0 px-4 sm:px-8 py-4 sm:py-5 bg-white border-b border-slate-200 shadow-sm">
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl shadow-lg">
              <Wand2 size={20} className="text-white" />
            </div>
            <div>
              <h1 className="text-lg font-black text-slate-900 uppercase tracking-wide">Estudio 3D</h1>
              <p className="text-xs text-slate-500 font-medium">Powered by LuiggiAI Engine</p>
            </div>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            {/* Cliente / referencia del proyecto */}
            <input value={cliente} onChange={e => setCliente(e.target.value)} placeholder="Cliente"
              className="px-3 py-2 border border-slate-200 rounded-lg text-sm w-36" />
            <input value={ref} onChange={e => setRef(e.target.value)} placeholder="Referencia"
              className="px-3 py-2 border border-slate-200 rounded-lg text-sm w-28" />
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

      {/* Barra temporal de accesos a otras herramientas (solo master) */}
      {isMaster && setState && (
        <div className="shrink-0 flex items-center gap-2 flex-wrap px-4 sm:px-8 py-2 bg-amber-50 border-b border-amber-200">
          <span className="text-[10px] font-black text-amber-700 uppercase tracking-wider">Otras herramientas (temporal · master)</span>
          {OTRAS_HERRAMIENTAS.map(h => (
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
        <div className="w-full lg:w-[420px] shrink-0 border-b lg:border-b-0 lg:border-r border-slate-200 bg-white flex flex-col lg:overflow-y-auto">
          {mode === 'natural' ? (
            /* ─── Modo Voz/Texto ─── */
            <div className="flex-1 flex flex-col p-6 gap-5">
              {/* PASO 1 — Describe el diseño */}
              <StepHeader n={1} title="Describe el diseño" hint="Cocina, armario, baño o mueble a medida. Puedes hablar o escribir." />

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
                    {analyzingRef ? 'Analizando…' : 'Subir imagen de referencia'}
                    <input type="file" accept="image/*,application/pdf" className="hidden" onChange={handleReferenceUpload} disabled={analyzingRef} />
                  </label>
                </div>
                {refImage && (
                  <div className="flex items-center gap-2 mb-2 text-[11px] font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-lg px-3 py-1.5 w-fit">
                    <CheckCircle size={13} /> Referencia adjunta — el render la respetará
                    <button onClick={() => setRefImage(null)} className="ml-1 text-emerald-500 hover:text-red-500" title="Quitar referencia"><X size={13} /></button>
                  </div>
                )}
                <textarea
                  ref={textareaRef}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Describe lo que quieres: cocina, armario empotrado, baño, dormitorio, estantería... Ej: 'Armario empotrado con puertas blancas lacadas, tirador fresado en los laterales color madera, interior con columna de baldas'"
                  className="flex-1 min-h-[150px] p-4 border border-slate-200 rounded-xl text-sm text-slate-700 resize-none focus:outline-none focus:ring-2 focus:ring-indigo-300 focus:border-indigo-400 transition-all"
                />
                <div className="flex flex-wrap gap-1.5 mt-2">
                  {QUICK_PHRASES.map(t => (
                    <button key={t} onClick={() => addPhrase(t)}
                      className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-500 hover:bg-slate-200"
                      title="Añadir a la descripción">+ {t}</button>
                  ))}
                </div>
              </div>

              {/* PASO 2 — Estilo y ambiente (agrupado) */}
              <div className="rounded-xl border border-slate-200 p-3 flex flex-col gap-3">
                <StepHeader n={2} title="Estilo y ambiente" hint="Aspecto, punto de vista e iluminación del render." />
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
              </div>

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

              {/* PASO 3 — Medidas de la estancia (opcional, para escala real) */}
              <div className="rounded-xl border border-slate-200 bg-slate-50/60 p-3 flex flex-col gap-2.5">
                <StepHeader n={3} title="Medidas de la estancia" hint="Opcional, pero da escala y proporción reales al render." />
                <div className="grid grid-cols-3 gap-2">
                  <label className="flex flex-col gap-1">
                    <span className="text-[10px] font-bold text-slate-400 uppercase">Ancho (cm)</span>
                    <input type="number" value={medidas.ancho} onChange={e => setMedidas(m => ({ ...m, ancho: e.target.value }))} placeholder="360" className="px-2 py-1.5 border border-slate-200 rounded-lg text-sm" />
                  </label>
                  <label className="flex flex-col gap-1">
                    <span className="text-[10px] font-bold text-slate-400 uppercase">Fondo (cm)</span>
                    <input type="number" value={medidas.fondo} onChange={e => setMedidas(m => ({ ...m, fondo: e.target.value }))} placeholder="300" className="px-2 py-1.5 border border-slate-200 rounded-lg text-sm" />
                  </label>
                  <label className="flex flex-col gap-1">
                    <span className="text-[10px] font-bold text-slate-400 uppercase">Techo (cm)</span>
                    <input type="number" value={medidas.altura} onChange={e => setMedidas(m => ({ ...m, altura: e.target.value }))} placeholder="250" className="px-2 py-1.5 border border-slate-200 rounded-lg text-sm" />
                  </label>
                </div>
                <input value={medidas.aberturas} onChange={e => setMedidas(m => ({ ...m, aberturas: e.target.value }))}
                  placeholder="Ventanas/puertas: ej. ventana 120 cm en pared izquierda, puerta al fondo"
                  className="px-3 py-1.5 border border-slate-200 rounded-lg text-sm" />
              </div>

              {/* PASO 4 — Plano + bocetos por pared (opcional, máxima fidelidad) */}
              <div className="rounded-xl border border-indigo-100 bg-indigo-50/50 p-3 flex flex-col gap-2.5">
                <StepHeader n={4} title="Plano + bocetos (opcional)" hint="Para máxima fidelidad: sube el plano en planta y un boceto por cada pared." />
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
              </div>

              {/* Separador entre las dos vías de generación */}
              <div className="flex items-center gap-2 text-[10px] font-black text-slate-300 uppercase tracking-widest">
                <span className="flex-1 h-px bg-slate-200" /> o <span className="flex-1 h-px bg-slate-200" />
              </div>

              {/* Precio orientativo (estimación, no presupuesto) */}
              {(() => { const e = estimarPrecio(); return (
                <div className="rounded-xl border border-emerald-200 bg-emerald-50/60 p-3">
                  <div className="flex items-center justify-between">
                    <p className="text-[11px] font-black text-emerald-700 uppercase tracking-wider">Precio orientativo</p>
                    <p className="text-sm font-black text-emerald-700">{eur0(e.min)} – {eur0(e.max)}</p>
                  </div>
                  <p className="text-[10px] text-slate-500 mt-1">≈ {e.ml} m.l. · muebles {eur0(e.muebles)} · encimera {eur0(e.encimera)} · electro {eur0(e.electro)} · montaje {eur0(e.montaje)}</p>
                  <p className="text-[10px] text-slate-400 mt-1">{e.deCatalogo ? `Muebles ≈ ${eur0(e.precioMuebleMl)}/m.l. (librería ${e.lib}, bloque ${e.group}) según tu catálogo del Presupuestador 1.` : 'Precios medios orientativos (activa un catálogo en el Presupuestador 1 para usar tus tarifas).'} El precio exacto se cierra en el Presupuestador 1, mueble a mueble.</p>
                  {setState && (
                    <button onClick={() => setState(p => ({ ...p, currentTab: 'budget', renderReturn: true }))}
                      className="mt-2 w-full flex items-center justify-center gap-2 px-3 py-2 bg-emerald-600 text-white rounded-lg text-xs font-bold hover:bg-emerald-700">
                      <FileText size={14} /> Presupuestar en Presupuestador 1
                    </button>
                  )}
                </div>
              ); })()}

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

        {/* Panel derecho - Resultado */}
        <div className="flex-1 flex flex-col p-4 sm:p-6 min-h-[60vh] lg:min-h-0 lg:overflow-hidden">
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
                <p className="text-sm text-slate-500 mt-2">LuiggiAI está creando tu diseño 3D...</p>
                <p className="text-xs text-slate-400 mt-1">Esto puede tardar hasta 30 segundos</p>
              </div>
            </div>
          ) : renderResult ? (
            /* Resultado del render */
            <div className="flex-1 flex flex-col gap-4 overflow-hidden">
              <div className="flex items-center justify-between shrink-0">
                <h3 className="font-black text-slate-700 uppercase tracking-wider text-sm">Resultado</h3>
                <div className="flex gap-2">
                  <button onClick={downloadRender} disabled={downloading || !currentImage()}
                    className="flex items-center gap-1.5 px-3 py-2 bg-indigo-600 text-white rounded-lg text-xs font-bold hover:bg-indigo-700 disabled:opacity-50" title="Descargar imagen (PNG)">
                    {downloading ? <Loader size={14} className="animate-spin" /> : <Download size={14} />} Descargar
                  </button>
                  <button onClick={exportPDF} disabled={downloading || !currentImage()}
                    className="flex items-center gap-1.5 px-3 py-2 bg-purple-600 text-white rounded-lg text-xs font-bold hover:bg-purple-700 disabled:opacity-50" title="Exportar PDF de presentación con logo">
                    <FileText size={14} /> PDF
                  </button>
                  <button onClick={attachToBudget} disabled={downloading || !currentImage()}
                    className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-bold disabled:opacity-50 ${attached ? 'bg-emerald-600 text-white' : 'bg-orange-500 text-white hover:bg-orange-600'}`} title="Adjuntar este render al presupuesto (Resumen Totales)">
                    {attached ? <><CheckCircle size={14} /> Adjuntado</> : <><Send size={14} /> Al presupuesto</>}
                  </button>
                  {refImage && (
                    <button onClick={() => setCompareOn(v => !v)}
                      className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-bold ${compareOn ? 'bg-slate-800 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}
                      title="Comparar la referencia con el render">
                      <Image size={14} /> Comparar
                    </button>
                  )}
                  <button
                    onClick={() => setShowFullscreen(true)}
                    className="p-2 bg-slate-100 rounded-lg hover:bg-slate-200 transition-colors"
                    title="Ver en pantalla completa"
                  >
                    <Maximize2 size={16} className="text-slate-600" />
                  </button>
                  <button
                    onClick={() => { setRenderResult(null); setDescription(''); }}
                    className="p-2 bg-slate-100 rounded-lg hover:bg-slate-200 transition-colors"
                    title="Nuevo render"
                  >
                    <RotateCcw size={16} className="text-slate-600" />
                  </button>
                </div>
              </div>

              {/* Comparativa referencia vs render */}
              {compareOn && refImage && renderResult?.result?.images?.[0] ? (
                <div className="flex-1 grid grid-cols-2 gap-3 overflow-hidden">
                  <div className="bg-slate-900 rounded-2xl overflow-hidden flex items-center justify-center relative">
                    <img src={refImage} alt="Referencia" className="w-full h-full object-contain" />
                    <span className="absolute top-2 left-2 px-2 py-1 bg-black/60 rounded text-[10px] font-black text-white uppercase tracking-widest">Referencia</span>
                  </div>
                  <div className="bg-slate-900 rounded-2xl overflow-hidden flex items-center justify-center relative">
                    <img src={assetSrc(renderResult.result.images[0])} alt="Render" className="w-full h-full object-contain" />
                    <span className="absolute top-2 left-2 px-2 py-1 bg-indigo-600 rounded text-[10px] font-black text-white uppercase tracking-widest">Render</span>
                  </div>
                </div>
              ) : (
              /* Imagen del render */
              <div className="flex-1 bg-slate-900 rounded-2xl overflow-hidden shadow-2xl flex items-center justify-center relative">
                {renderResult?.result?.images?.[0] && !imgError ? (
                  <img
                    src={assetSrc(renderResult.result.images[0])}
                    alt="Render 3D de cocina"
                    className="w-full h-full object-contain"
                    onError={() => setImgError(true)}
                  />
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
                    LuiggiAI Render Engine
                  </span>
                </div>
              </div>
              )}

              {/* Variantes de color en 1 clic */}
              {currentImage() && (
                <div className="shrink-0 flex items-center gap-2 flex-wrap bg-white border border-slate-200 rounded-xl p-2">
                  <span className="text-[11px] font-black text-slate-500 uppercase tracking-wider ml-1">Variar color</span>
                  {COLORS_VARIANTES.map(c => (
                    <button key={c.label} onClick={() => colorVariant(c.label)} disabled={editing}
                      title={`Muebles en ${c.label}`}
                      className="w-7 h-7 rounded-full border-2 border-white ring-1 ring-slate-300 shadow hover:scale-110 transition-transform disabled:opacity-40"
                      style={{ background: c.hex }} />
                  ))}
                  {editing && <span className="text-[11px] text-slate-400 flex items-center gap-1"><Loader size={12} className="animate-spin" /> generando…</span>}
                </div>
              )}

              {/* Editar el render en lenguaje natural */}
              {currentImage() && (
                <div className="shrink-0 flex items-center gap-2 bg-white border border-slate-200 rounded-xl p-2">
                  <Wand2 size={16} className="text-purple-500 shrink-0 ml-1" />
                  <input value={editInstruction} onChange={e => setEditInstruction(e.target.value)}
                    onKeyDown={e => { if (e.key === 'Enter' && !editing && editInstruction.trim()) editRender(); }}
                    placeholder="Editar: p. ej. 'haz la isla más grande', 'cambia los muebles a azul navy', 'añade una campana de isla'"
                    className="flex-1 px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-300" />
                  <button onClick={editRender} disabled={editing || !editInstruction.trim()}
                    className="flex items-center gap-1.5 px-4 py-2 bg-purple-600 text-white rounded-lg text-xs font-bold hover:bg-purple-700 disabled:opacity-50 shrink-0">
                    {editing ? <><Loader size={14} className="animate-spin" /> Aplicando…</> : <><Send size={14} /> Aplicar cambio</>}
                  </button>
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
              <h3 className="font-black text-slate-800">Mis proyectos 3D</h3>
              <button onClick={() => setSavedList(null)} className="p-1.5 text-slate-400 hover:text-slate-700"><X size={18} /></button>
            </div>
            <div className="p-4 overflow-y-auto">
              {savedList.length === 0 ? (
                <p className="text-sm text-slate-400 text-center py-8">No tienes proyectos guardados todavía.</p>
              ) : savedList.map(d => (
                <div key={d.id} className="flex items-center gap-3 border border-slate-200 rounded-xl p-2 mb-2 hover:bg-slate-50">
                  <div className="w-12 h-12 shrink-0 bg-slate-200 rounded-lg overflow-hidden">
                    {d.images?.[0] ? <img src={assetSrc(d.images[0])} alt="" className="w-full h-full object-cover" /> : <div className="w-full h-full flex items-center justify-center text-slate-400"><Image size={16} /></div>}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-bold text-slate-700 text-sm truncate">{d.cliente || 'Sin cliente'}{d.ref ? ` · ${d.ref}` : ''}</p>
                    {d.updatedAt && <p className="text-[10px] text-slate-400">{new Date(d.updatedAt).toLocaleString('es-ES')}</p>}
                  </div>
                  <button onClick={() => loadDesign(d)} className="px-3 py-1.5 bg-indigo-600 text-white rounded-lg text-xs font-bold hover:bg-indigo-700">Abrir</button>
                  <button onClick={() => deleteDesign(d.id)} className="p-1.5 text-red-400 hover:text-red-600 hover:bg-red-50 rounded-lg"><Trash2 size={16} /></button>
                </div>
              ))}
            </div>
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
    </div>
  );
}
