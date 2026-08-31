/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * CocinaMontada3.jsx — Módulo Oficial de Presupuestación Rápida de Cocina Montada 3.
 * 
 * Funcionalidades avanzadas:
 *   - Pegado masivo multilínea (WhatsApp, Email, Hojas de corte)
 *   - Paleta interactiva de adición rápida (Bajos, Altos, Columnas, Gaveteros, Lineales)
 *   - Buscador predictivo en tiempo real con sinónimos en lenguaje natural
 *   - Conmutador de tarifas dinámico (T1 a T5) con matriz comparativa en vivo
 *   - Muestrario interactivo de acabados para puertas y cascos con swatches de color
 *   - Selector de cliente CRM, descuentos comerciales y selector de IVA (0%, 10%, 21%)
 *   - Desglose de costes y márgenes con candado 🔒 (Casco neto ACB, puertas por tarifa, herrajes y MO)
 *   - Escandallo técnico para taller con cálculo de tableros, bisagras y tiempos
 *   - Lanzamiento directo de orden de fabricación al módulo de Producción
 *   - Exportación a PDF oficial de alta resolución con jsPDF y copia formateada para WhatsApp
 */
import React, { useState, useEffect, useMemo, useRef } from 'react';
import { 
  FileText, Plus, Trash2, Search, Check, Loader, AlertTriangle, 
  Download, Save, FolderOpen, Lock, Unlock, Sparkles, RefreshCw,
  Copy, Layers, ArrowUpDown, ChevronRight, HelpCircle, Package,
  ClipboardList, CheckCircle2, ChevronDown, Boxes, Box, X, Printer, FileUp,
  User, Percent, Receipt, Phone, Building2, Tag, Calendar, ArrowLeft,
  Palette, Factory, Hammer, Clock, Wrench, ShieldCheck, Play, List, ShoppingCart
} from 'lucide-react';
import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';
import { getToken } from '../services/api';
import { usePulsacionLarga, AYUDA_CANDADO } from '../utils/pulsacionLarga';
import BotonPantallaCompleta from './BotonPantallaCompleta';
import { despiece, MV_COSTES_DEFAULT, getFactorDesmontada, tieneDespieceReal } from './RentabilidadMV';
import RelacionReview from './RelacionReview';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const eur = (n) => (n == null ? '—' : `${Number(n).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} €`);

const norm = (s) => (s || '').toString()
  .normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();

const TIPOS_SIN_ANCHO = new Set(['ent_med', 'h355060']);
const PAT_ANCHO = /^[A-Z]+(\d{2,3})(?:D\/I|D|I)?$/;
const anchoDeCod = (cod, type) => {
  if (TIPOS_SIN_ANCHO.has(type)) return null;
  const m = PAT_ANCHO.exec(cod || '');
  return m ? Number(m[1]) : null;
};

const pvpDeItem = (val, pv) => {
  if (typeof val === 'number') return { eur: Math.round(val * pv * 100) / 100, desde: false };
  if (Array.isArray(val)) {
    const ns = val.filter(n => typeof n === 'number');
    if (!ns.length) return null;
    return { eur: Math.round(Math.min(...ns) * pv * 100) / 100, desde: true };
  }
  return null;
};

/** Los herrajes de una línea: lo que `despiece` mete en el coste bajo ese
 *  nombre. Se suma AQUÍ y no en la plantilla para que el desglose de pantalla
 *  no pueda separarse de lo que suma el cálculo — que es justo lo que hacía
 *  que el total no cuadrara con lo que se veía. */
export const herrajesDe = (m) => {
  const d = (m || {}).despiece || {};
  return ['bisagras', 'patas', 'colg', 'caj', 'gav', 'soportes']
    .reduce((t, k) => t + (Number(d[k]) || 0), 0);
};

/** LA DESCRIPCIÓN DE UNA LÍNEA, EN UN SOLO SITIO.
 *
 *  Lo que el master escribe a mano, y si no ha escrito nada, la familia de
 *  tarifa. Vive aquí y no repetida en cada plantilla porque la usan la tabla,
 *  la ficha y el PDF: escrita tres veces, el día que se cambie una la pantalla
 *  diría una cosa y el presupuesto del cliente otra — que es el fallo que este
 *  proyecto ya tuvo con el rótulo de los tramos de comisión.
 *
 *  OJO: esto es un RÓTULO. `familia` sigue siendo lo que decide el despiece, el
 *  coste y si la línea comisiona; escribir aquí no la toca. */
export const descDe = (m) =>
  (m?.desc || '').trim() || m?.familia?.replace(/_/g, ' ') || m?.tipo || 'Mueble';

const costeDetalladoDe = (m, p, tarifa, pvVal, acabadoCasco) => {
  return despiece({ cod: m.cod, altura: m.alto ? String(m.alto) : '', familia: m.familia }, p, tarifa, pvVal, acabadoCasco);
};

const PALETA_RAPIDA = [
  { grupo: 'Bajos', items: [
    { label: 'B60', expr: '1 b60d', desc: 'Bajo 1P 60' },
    { label: 'B45', expr: '1 b45d', desc: 'Bajo 1P 45' },
    { label: 'B90 (2P)', expr: '1 b90', desc: 'Bajo 2P 90' },
    { label: 'BF60 Freg.', expr: '1 bf60', desc: 'Fregadero 60' },
    { label: 'BF90 Freg.', expr: '1 bf90', desc: 'Fregadero 90' },
    { label: 'BGF80 (2 Gav)', expr: '1 bgf80', desc: '2 Gavetas 80' },
    { label: 'BGF90 (2 Gav)', expr: '1 bgf90', desc: '2 Gavetas 90' },
    { label: 'BCG60 (3C+1G)', expr: '1 bcg60', desc: 'Cajonero 60' },
    { label: 'BR90 Rincón', expr: '1 br90', desc: 'Rincón Ciego 90' },
    { label: 'BH60 Horno', expr: '1 bh60', desc: 'Bajo Horno 60' },
  ]},
  { grupo: 'Altos', items: [
    { label: 'A60 (h90)', expr: '1 a60d (altura 90)', desc: 'Alto 1P 60 h90' },
    { label: 'A45 (h90)', expr: '1 a45d (altura 90)', desc: 'Alto 1P 45 h90' },
    { label: 'A90 (2P h90)', expr: '1 a90 (altura 90)', desc: 'Alto 2P 90 h90' },
    { label: 'ASC60 Camp.', expr: '1 asc60d (altura 90)', desc: 'Campana 60' },
    { label: 'ASCE90 Camp.', expr: '1 asce90 (altura 90)', desc: 'Campana 90' },
    { label: 'AA60 Abat.', expr: '1 aa60 (altura 90)', desc: 'Abatible 60' },
    { label: 'AA90 Abat.', expr: '1 aa90 (altura 90)', desc: 'Abatible 90' },
    { label: 'AV60 Vitrina', expr: '1 av60d (altura 90)', desc: 'Vitrina 60' },
    { label: 'AR65 Rincón', expr: '1 ar65d (altura 90)', desc: 'Rincón 65' },
  ]},
  { grupo: 'Columnas', items: [
    { label: 'CD60 Desp.', expr: '1 cd60d (altura 200)', desc: 'Despensero 60' },
    { label: 'CH60 Horno', expr: '1 ch60 (altura 200)', desc: 'Columna Horno 60' },
    { label: 'CHM60 H+M', expr: '1 chm60 (altura 200)', desc: 'Horno + Micro 60' },
    { label: 'CF60 Frigo', expr: '1 cf60 (altura 200)', desc: 'Frigo Integrable 60' },
  ]},
  { grupo: 'Lineales y Remates', items: [
    { label: 'Costado Bajo', expr: '1 ccb', desc: 'Costado Bajo' },
    { label: 'Costado Alto', expr: '1 cca', desc: 'Costado Alto' },
    { label: 'Costado Col.', expr: '1 ccc', desc: 'Costado Columna' },
    { label: 'Zócalo Alum.', expr: '1 zoc', desc: 'Tira Zócalo' },
    { label: 'Copete', expr: '1 cop', desc: 'Tira Copete' },
  ]}
];

const TARIFAS_NOMBRES = {
  T1:  'Sincro / Melamina Texturada (Base)',
  T2:  'Estratificado Mate / Laminado Color',
  T3:  'Lacado Seda / Brillo',
  T4:  'ZENIT Supermate Antihuella',
  T5:  'FENIX NTM Alta Resistencia',
  T6:  'Policromado / Vitrina Aluminio',
  T7:  'Policromado Plus / Madera Natural',
  T8:  'Lacado Antibacteriano / Premium',
  T9:  'Madera Maciza / Chapa Natural',
  T10: 'Madera Textura / Grabado Relieve',
  T11: 'Alta Gama Mate Extreme',
  T12: 'Madera Exótica / Derbi',
  T13: 'Laminado Especial / Acabado Técnico',
  T14: 'Superpremium Lacado Ultramate',
  T15: 'Laca Efecto Tela / Textil',
  T16: 'Marbella Lacado Porcelana',
  T17: 'Efecto Cemento / Microcemento',
  T18: 'Lacado Metalizado / Brillo Extremo',
  T19: 'Serie Exclusiva Premium A',
  T20: 'Serie Exclusiva Premium B',
  T21: 'Colección Élite / Alta Costura',
};

const MUESTRARIO_PUERTAS = {
  T1: [
    { id: 't1-roble', nombre: 'Roble Sincro', color: '#a8917c' },
    { id: 't1-nogal', nombre: 'Nogal Pacific', color: '#645044' },
    { id: 't1-gris', nombre: 'Gris Texturado', color: '#8e9092' },
    { id: 't1-blanco', nombre: 'Blanco Polar', color: '#f3f4f6' }
  ],
  T2: [
    { id: 't2-blanco-seda', nombre: 'Blanco Seda', color: '#f9fafb' },
    { id: 't2-cashmere', nombre: 'Cashmere Seda', color: '#d8cfc4' },
    { id: 't2-verde', nombre: 'Verde Oliva Seda', color: '#6c756b' },
    { id: 't2-antracita', nombre: 'Antracita Seda', color: '#39414e' }
  ],
  T3: [
    { id: 't3-blanco-brillo', nombre: 'Blanco Puro Brillo', color: '#ffffff' },
    { id: 't3-blanco-mate', nombre: 'Blanco Seda Mate', color: '#f2f5f8' },
    { id: 't3-negro', nombre: 'Negro Carbón Lacado', color: '#212937' },
    { id: 't3-azul', nombre: 'Azul Noche Lacado', color: '#2d406d' }
  ],
  T4: [
    { id: 't4-zenit-blanco', nombre: 'ZENIT Blanco Supermate', color: '#fafafa' },
    { id: 't4-zenit-antracita', nombre: 'ZENIT Antracita Metal', color: '#364150' },
    { id: 't4-zenit-basalto', nombre: 'ZENIT Gris Basalto', color: '#4a5564' },
    { id: 't4-zenit-croma', nombre: 'ZENIT Croma Oro', color: '#705741' }
  ],
  T5: [
    { id: 't5-fenix-negro', nombre: 'FENIX Nero Ingo (Antihuella)', color: '#111726' },
    { id: 't5-fenix-blanco', nombre: 'FENIX Bianco Kos', color: '#ffffff' },
    { id: 't5-fenix-londra', nombre: 'FENIX Grigio Londra', color: '#52525a' },
    { id: 't5-fenix-verde', nombre: 'FENIX Verde Comodoro', color: '#323937' }
  ]
};

const MUESTRARIO_CASCOS = [
  { id: 'grafito-19', nombre: 'Grafito Antracita (19mm)', color: '#364150', grosor: 19 },
  { id: 'blanco-hidro-19', nombre: 'Blanco Hidrófugo (19mm)', color: '#f8fafb', grosor: 19 },
  { id: 'roble-aurora-19', nombre: 'Roble Aurora (19mm)', color: '#b79e84', grosor: 19 },
  { id: 'spike-19', nombre: 'Spike (19mm)', color: '#56534f', grosor: 19 },
  { id: 'stone-19', nombre: 'Stone (19mm)', color: '#77716d', grosor: 19 },
  { id: 'blanco-16', nombre: 'Blanco En Kit (16mm)', color: '#ffffff', grosor: 16 },
  { id: 'aluminio-16', nombre: 'Aluminio Textura (16mm)', color: '#97a3b2', grosor: 16 },
  { id: 'roble-natural-16', nombre: 'Roble Natural (16mm)', color: '#896c50', grosor: 16 },
  { id: 'olmo-18', nombre: 'Olmo (18mm)', color: '#5f4837', grosor: 18 },
  { id: 'esp-blanco-16', nombre: 'Especial Blanco (16mm)', color: '#f2f5f8', grosor: 16 }
];

export default function CocinaMontada3({ currentUser, state, setState, logo }) {
  const [cliente, setCliente] = useState('');
  const [ref, setRef] = useState('');
  const [telefono, setTelefono] = useState('');
  const [descuento, setDescuento] = useState(0);
  const [ivaRate, setIvaRate] = useState(21);
  const [acabadoPuerta, setAcabadoPuerta] = useState(MUESTRARIO_PUERTAS.T1[0].nombre);
  const [acabadoCasco, setAcabadoCasco] = useState(MUESTRARIO_CASCOS[0].nombre);
  
  const [muebles, setMuebles] = useState([]);
  const [observacionesGenerales, setObservacionesGenerales] = useState('');
  const [busca, setBusca] = useState('');
  const [buscando, setBuscando] = useState(false);
  const [aviso, setAviso] = useState('');
  const [guardando, setGuardando] = useState(false);
  const [savedId, setSavedId] = useState(null);
  // EL PEDIDO YA CREADO DESDE ESTA RELACIÓN. Sin esto, cada pulsación de «Crear
  // pedido» generaba un id nuevo con la hora y creaba OTRO pedido: los dos
  // entraban en COOP y los dos pagaban comisión. Una cocina vendida una vez,
  // pagada dos.
  const [pedidoId, setPedidoId] = useState(null);
  
  const [verCoste, setVerCoste] = useState(false);
  const [pistaCandado, setPistaCandado] = useState('');
  
  // Modales y vistas
  const [showPegadoMasivo, setShowPegadoMasivo] = useState(false);
  const [textoMasivo, setTextoMasivo] = useState('');

  // ─── RELACIÓN QUE LLEGA DEL ESTUDIO 3D ──────────────────────────────────
  //
  // El botón «Volcar a Montada 3» del Estudio 3D manda aquí los muebles que se
  // LEYERON DEL PLANO, ya en notación MV. Llegan al cuadro de pegado masivo y
  // se abre solo, para que se vean ANTES de meterlos: se repasan, se corrige lo
  // que haga falta y se procesa.
  //
  // NO se procesan solos a propósito. Esto acaba en un presupuesto que firma un
  // cliente, y la relación trae cosas deducidas —la familia de cajonera se
  // saca contando frentes—. Que entre sin que nadie la haya mirado es cómo se
  // firma un mueble que no es.
  useEffect(() => {
    const texto = state?.relacionMVPendiente;
    if (!texto) return;
    setTextoMasivo(String(texto));
    setShowPegadoMasivo(true);
    if (setState) setState(p => { const { relacionMVPendiente, ...resto } = p; return resto; });
  }, [state?.relacionMVPendiente]);   // eslint-disable-line
  const [showComparador, setShowComparador] = useState(false);
  const [showEscandallo, setShowEscandallo] = useState(false);
  const [showMuestrario, setShowMuestrario] = useState(false);
  const [filtroCat, setFiltroCat] = useState('TODOS');
  const [copiadoWs, setCopiadoWs] = useState(false);
  const [showModalDtos, setShowModalDtos] = useState(false);
  
  // Estado e inputs para el desplegable de IMPORTAR
  const [menuImportar, setMenuImportar] = useState(false);
  const [relacionRevisar, setRelacionRevisar] = useState(null);
  const [importandoRel, setImportandoRel] = useState(false);
  const [progresoImportacion, setProgresoImportacion] = useState('');
  const relacionInputRef = useRef(null);
  const alvicInputRef = useRef(null);

  // Recibe propuestas MV creadas desde una proforma Alvic en Cocina Desmontada.
  // Siempre se abre la revisión antes de mezclar nada en el presupuesto actual.
  useEffect(() => {
    const pendientes = state?.cocinaMontadaPendingMuebles;
    if (!Array.isArray(pendientes) || pendientes.length === 0) return;
    setRelacionRevisar(pendientes);
    setState?.(p => ({ ...p, cocinaMontadaPendingMuebles: null }));
  }, [state?.cocinaMontadaPendingMuebles, setState]);

  const authHeaders = () => {
    const token = getToken();
    return {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    };
  };

  const importarRelacion = async (file) => {
    if (!file) return;
    setImportandoRel(true); setMenuImportar(false);
    setProgresoImportacion(`Analizando ${file.name} (detectando páginas y códigos de módulos)...`);
    try {
      const b64 = await new Promise((res, rej) => {
        const fr = new FileReader(); fr.onload = () => res(fr.result); fr.onerror = rej; fr.readAsDataURL(file);
      });
      const r = await fetch(`${API_URL}/api/cascos/mv/detectar-relacion`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ pdfBase64: b64, tariff: tarifa }),
      });
      let d = {}; try { d = await r.json(); } catch { d = {}; }
      if (!r.ok || !d.success) throw new Error(d.detail || 'Error al procesar PDF');
      if (!d.muebles || !d.muebles.length) {
        alert('No se detectaron módulos válidos en el PDF.');
        return;
      }
      setRelacionRevisar(d.muebles);
    } catch (e) { alert(e.message || 'Error al procesar el PDF'); }
    finally { setImportandoRel(false); setProgresoImportacion(''); if (relacionInputRef.current) relacionInputRef.current.value = ''; }
  };

  const importarAlvic = async (file) => {
    if (!file) return;
    setImportandoRel(true); setMenuImportar(false);
    setProgresoImportacion(`Analizando proforma Alvic ${file.name} (detectando muebles y cascos equivalentes)...`);
    try {
      const b64 = await new Promise((res, rej) => {
        const fr = new FileReader(); fr.onload = () => res(fr.result); fr.onerror = rej; fr.readAsDataURL(file);
      });
      const r = await fetch(`${API_URL}/api/cascos/proforma`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ pdfBase64: b64 }),
      });
      let d = {}; try { d = await r.json(); } catch { d = {}; }
      if (!r.ok) throw new Error(d.detail || d.error || 'Error al procesar PDF Alvic');

      let items = d.items || [];
      if (d.estado === 'procesando' && d.jobId) {
        const inicio = Date.now();
        let pag = 1;
        while (Date.now() - inicio < 600000) {
          setProgresoImportacion(`Procesando páginas del PDF Alvic (${pag} seg)...`);
          pag += 3;
          await new Promise(res => setTimeout(res, 3000));
          const q = await fetch(`${API_URL}/api/cascos/proforma/job/${d.jobId}`, { headers: authHeaders() });
          let j = {}; try { j = await q.json(); } catch { j = {}; }
          if (!q.ok) throw new Error(j.detail || 'Error al analizar el PDF de Alvic');
          if (j.estado === 'listo') { items = j.items || []; break; }
          if (j.estado === 'error') throw new Error(j.detail || 'No se pudieron detectar los muebles.');
        }
      }
      if (!items || !items.length) {
        alert('No se detectaron módulos válidos en el PDF de Alvic.');
        return;
      }
      const mueblesAdaptados = items.map((it, idx) => {
        const rawAncho = Number(it.ancho || it.width || 0);
        const rawAlto = Number(it.largo || it.alto || it.height || 0);
        const widthCm = rawAncho > 320 ? Math.round(rawAncho / 10) : (rawAncho || null);
        const heightCm = rawAlto > 320 ? Math.round(rawAlto / 10) : (rawAlto || null);
        const qty = Number(it.cantidad || it.qty || 1);
        const pvpUnit = Number(it.pvp || it.precio || 0);

        let codMv = (it.cod || it.ref || '').trim();
        const descUpper = (it.descripcion || '').toUpperCase();
        let tipo = (it.tipo || '').toUpperCase();

        if (!tipo) {
          if (descUpper.includes('FREGADERO')) tipo = 'BAJO_FREGADERO';
          else if (descUpper.includes('RINCON')) tipo = 'BAJO_RINCON_CIEGO';
          else if (descUpper.includes('HORNO')) tipo = 'COLUMNA_HORNO_MICRO';
          else if (descUpper.includes('ALTO')) tipo = 'ALTO';
          else if (descUpper.includes('COLUMNA')) tipo = 'COLUMNA';
          else tipo = 'BAJO';
        }

        // UN PANEL NO ES UN BAJO, Y NO SE LE PONE NOMBRE DE BAJO (30/08).
        //
        // Esto fabricaba un código para CUALQUIER línea que no lo trajera, y el
        // último `else` la bautizaba `B<ancho>D/I`. Con una proforma que trae
        // paneles salía `B150D/I` —un bajo de 150 cm, que no existe: el ancho
        // estándar más grande es 120— y con un alto de 400 cm. Un código
        // inventado se arrastra al pedido y al taller.
        //
        // Solo se deduce el código cuando el tipo es una familia que el
        // despiece SABE desglosar. Lo demás conserva lo que venga del PDF.
        const conocida = tieneDespieceReal(tipo);
        if (!/^[A-Z]{1,5}\d{2,3}(D\/I|D|I)?$/i.test(codMv) && widthCm && conocida) {
          if (tipo === 'BAJO_FREGADERO') codMv = `BF${widthCm}D/I`;
          else if (tipo === 'BAJO_RINCON_CIEGO') codMv = `BR${widthCm}D/I`;
          else if (tipo === 'ALTO') codMv = `A${widthCm}D/I`;
          else if (tipo === 'BAJO') codMv = `B${widthCm}D/I`;
        }

        return {
          _k: `alvic-${Date.now()}-${idx}-${Math.random().toString(36).slice(2, 7)}`,
          // Sin código y sin familia reconocida NO se inventa uno: se deja la
          // referencia del PDF, o vacío. Un `B60D/I` puesto por defecto es un
          // mueble que nadie ha pedido (regla 7).
          cod: codMv || (conocida && widthCm ? `B${widthCm}D/I` : ''),
          descripcion: it.descripcion || `${tipo} ${widthCm || ''}x${heightCm || ''}`.trim(),
          qty,
          ancho: widthCm,
          alto: heightCm,
          familia: tipo,
          // Se marca aquí, al entrar, para que la pantalla pueda decirlo sin
          // volver a adivinarlo.
          costeAproximado: !conocida,
          pvp: pvpUnit,
          encontrado: true,
          mano: '',
        };
      });

      setMuebles(prev => fundir(prev, mueblesAdaptados));
    } catch (e) { alert(e.message || 'Error al procesar PDF Alvic'); }
    finally { setImportandoRel(false); if (alvicInputRef.current) alvicInputRef.current.value = ''; }
  };

  const descargarPlantillaEnBlanco = async () => {
    try {
      const token = getToken();
      const r = await fetch(`${API_URL}/api/cascos/mv/nomenclaturas-pdf`, {
        headers: token ? { 'Authorization': `Bearer ${token}` } : {}
      });
      if (!r.ok) throw new Error('Error al descargar la plantilla PDF');
      const blob = await r.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a'); a.href = url; a.download = 'Nomenclaturas_MV_rellenable.pdf'; a.click();
    } catch (e) { alert(e.message); }
  };

  // Descuentos comerciales de compra en fábrica de puertas (Descuento 1 + Descuento 2 en cascada)
  // EL DESCUENTO DE COMPRA DE CASCOS ACB. Se teclea a mano porque la tarifa del
  // proveedor se negocia. Por defecto 0: sin tocarlo, el coste sale igual que
  // siempre (ver `despiece` en RentabilidadMV).
  const [dtoCascos, setDtoCascos] = useState(() => {
    try { return Number(localStorage.getItem('dto_cascos_acb')) || 0; } catch { return 0; }
  });
  useEffect(() => {
    try { localStorage.setItem('dto_cascos_acb', String(dtoCascos)); } catch { /* noop */ }
  }, [dtoCascos]);

  const [dtoPuertas1, setDtoPuertas1] = useState(() => {
    try { return parseFloat(localStorage.getItem('dto_puertas_1') || localStorage.getItem('dto_puertas') || '50'); } catch { return 50; }
  });
  const [dtoPuertas2, setDtoPuertas2] = useState(() => {
    try { return parseFloat(localStorage.getItem('dto_puertas_2') || '0'); } catch { return 0; }
  });

  useEffect(() => {
    try {
      localStorage.setItem('dto_puertas_1', String(dtoPuertas1));
      localStorage.setItem('dto_puertas_2', String(dtoPuertas2));
      localStorage.setItem('dto_puertas', String(dtoPuertas1));
    } catch { /* noop */ }
  }, [dtoPuertas1, dtoPuertas2]);

  const p = useMemo(() => {
    try { 
      const s = JSON.parse(localStorage.getItem('mv_costes') || 'null'); 
      return s ? { ...MV_COSTES_DEFAULT, ...s } : MV_COSTES_DEFAULT; 
    } catch { 
      return MV_COSTES_DEFAULT; 
    }
  }, []);

  const paramsCostes = useMemo(() => ({
    ...p,
    dtoCascos,
    dtoPuertas1,
    dtoPuertas2,
  }), [p, dtoCascos, dtoPuertas1, dtoPuertas2]);

  const [familias, setFamilias] = useState(null);
  const [pv, setPv] = useState(3.33);
  const [tarifa, setTarifa] = useState(() => {
    try { return localStorage.getItem('mv_tarifa') || 'T1'; } catch { return 'T1'; }
  });
  const [tarifas, setTarifas] = useState([]);



  useEffect(() => {
    fetch(`${API_URL}/api/cascos/mv/tarifas`, { headers: authHeaders() })
      .then(r => r.json())
      .then(d => { if (d.success) setTarifas(d.tarifas || []); })
      .catch(() => {});
  }, []);

  useEffect(() => {
    try { localStorage.setItem('mv_tarifa', tarifa); } catch { /* noop */ }
    fetch(`${API_URL}/api/cascos/mv/tarifa?tariff=${encodeURIComponent(tarifa)}`, { headers: authHeaders() })
      .then(r => r.json())
      .then(d => {
        if (d.success) {
          setFamilias(d.familias);
          const newPv = d.pointValue || 3.33;
          setPv(newPv);
          // Actualizar acabado por defecto de la tarifa
          if (MUESTRARIO_PUERTAS[tarifa]) {
            setAcabadoPuerta(MUESTRARIO_PUERTAS[tarifa][0].nombre);
          }
          setMuebles(prev => prev.map(m => {
            const baseCod = String(m.cod || '').replace(/(D\/I|D|I)$/i, '');
            const info = d.familias?.[m.familia];
            const e = info?.items?.[m.cod] || info?.items?.[baseCod];
            if (e == null) return m;
            let pvp = m.pvp;
            if (Array.isArray(e)) {
              const t = info.type;
              let i = 0;
              if (t === 'h7090') i = (m.alto || 90) >= 85 ? 1 : 0;
              else if (t === 'h127147') i = (m.alto || 127) > 137 ? 1 : 0;
              else if (t === 'h200220') i = (m.alto || 200) > 210 ? 1 : 0;
              pvp = Math.round((e[i] || e[0]) * newPv * 100) / 100;
            } else if (typeof e === 'number') {
              pvp = Math.round(e * newPv * 100) / 100;
            }
            return { ...m, pvp };
          }));
        }
      })
      .catch(() => {});
  }, [tarifa]);

  const catalogo = useMemo(() => {
    if (!familias) return [];
    const out = [];
    for (const [fam, info] of Object.entries(familias)) {
      const items = info?.items;
      if (!items || typeof items !== 'object') continue;
      for (const [cod, val] of Object.entries(items)) {
        const desc = (val && typeof val === 'object' && !Array.isArray(val)) ? val.desc : null;
        const etiqueta = fam.replace(/_/g, ' ');
        out.push({
          cod, familia: fam, etiqueta, desc,
          ancho: anchoDeCod(cod, info.type),
          precio: pvpDeItem(val, pv),
          busca: norm(`${cod} ${etiqueta} ${desc || ''}`),
        });
      }
    }
    return out;
  }, [familias, pv]);

  const [sel, setSel] = useState(0);
  const [foco, setFoco] = useState(false);
  const sugerencias = useMemo(() => {
    const q = norm(busca).trim();
    if (!q || !catalogo.length) return [];
    if (/^\s*\d+\s*\S/.test(busca) || busca.includes('(')) return [];
    const term = q.split(/\s+/).filter(Boolean);
    const hits = catalogo.filter(c => term.every(t => c.busca.includes(t)));
    hits.sort((a, b) => {
      const ap = a.cod.toLowerCase().startsWith(q) ? 0 : 1;
      const bp = b.cod.toLowerCase().startsWith(q) ? 0 : 1;
      return ap - bp || a.cod.localeCompare(b.cod);
    });
    return hits.slice(0, 40);
  }, [busca, catalogo]);

  const OPCIONES_ALTURA = { h7090: [90, 70], h127147: [127, 147], h200220: [200, 220], bajo: [80, 70] };

  // Costados, laterales y regletas: sus dos columnas de tarifa son el ANCHO de
  // la pieza, no la altura del mueble que rematan (ver `services/mv_relacion.py`).
  // El ancho de un costado es el FONDO del mueble —33 en altos, 58 en bajos y
  // columnas—, así que «hasta 70» es el caso corriente y va primero.
  const OPCIONES_ANCHO = { a7090: [70, 90] };
  const ANCHO_POR_DEFECTO_LINEAL = 70;

  const alturasDe = (m) => {
    const fam = String(m.familia || '').toUpperCase();
    const tipo = String(m.tipo || '').toUpperCase();
    if (fam.startsWith('BAJO') || tipo === 'BAJO') return [80, 70];
    const t = familias?.[m.familia]?.type;
    return OPCIONES_ALTURA[t] || null;
  };

  /** Los anchos de tarifa de una pieza lineal, o null si no es una de ellas. */
  const anchosDe = (m) => OPCIONES_ANCHO[familias?.[m.familia]?.type] || null;

  const puntosLocal = (m, alto) => {
    const info = familias?.[m.familia];
    const e = info?.items?.[m.cod];
    if (e == null) return m.pvp;
    if (Array.isArray(e)) {
      const t = info.type;
      let i = 0;
      if (t === 'h7090') i = alto >= 85 ? 1 : 0;
      else if (t === 'a7090') {
        // Aquí manda el ANCHO de la pieza, no el alto del mueble. Con el alto,
        // un costado de columna (220) caía siempre en la columna cara y la
        // barata no se podía alcanzar nunca.
        const a = Number(m.anchoTarifa) || ANCHO_POR_DEFECTO_LINEAL;
        i = a > 70 ? 1 : 0;
      } else if (t === 'h127147') i = alto > 137 ? 1 : 0;
      else if (t === 'h200220') i = alto > 210 ? 1 : 0;
      return Math.round((e[i] || e[0]) * pv * 100) / 100;
    }
    return typeof e === 'number' ? Math.round(e * pv * 100) / 100 : m.pvp;
  };

  const setQty = (k, deltaOrVal, isDelta = false) => {
    setMuebles(prev => prev.map(m => {
      if (m._k !== k) return m;
      const cur = Number(m.qty) || 1;
      const next = isDelta ? Math.max(1, cur + deltaOrVal) : Math.max(1, Number(deltaOrVal) || 1);
      return { ...m, qty: next };
    }));
  };

  const setAlto = (k, v) => setMuebles(prev => prev.map(m => {
    if (m._k !== k) return m;
    const alto = Number(v) || null;
    // UN PRECIO ESCRITO A MANO MANDA SOBRE LA TARIFA. Sin esta condición,
    // cambiar el alto después de pactar un precio lo devolvía al de catálogo
    // sin decir nada, y el presupuesto salía por otra cifra.
    if (m.pvpManual) return { ...m, alto };
    return { ...m, alto, pvp: puntosLocal(m, alto) };
  }));

  /** Elige la COLUMNA de tarifa de una pieza lineal por su ancho (70 / 90).
   *  Se le pasa a `puntosLocal` el mueble YA actualizado: si se le pasara `m`,
   *  leería el ancho viejo y el precio iría un clic por detrás. */
  /**
   * LA MEDIDA DE VERDAD DE LA PIEZA, QUE NO ES LA DEL PRECIO.
   *
   * El master, 28/08: «aunque pongas hasta 70 o hasta 90, esas medidas las
   * puedo modificar para que queden grabadas las medidas definitivas», y «en
   * los costados bajos y altos también se debe poder cambiar la medida, tanto
   * de ancho como de alto, en todos».
   *
   * Son dos cosas distintas y hay que no mezclarlas:
   *   · el ESCALÓN («hasta 70», «hasta 90») decide lo que CUESTA;
   *   · el ancho y el alto reales son lo que se fabrica y lo que va al pedido.
   *
   * Por eso esto NO toca el pvp: cambiar la medida definitiva de un costado no
   * puede mover el precio por accidente. Si la pieza se sale del escalón, el
   * escalón se cambia a mano al lado, que es una decisión, no un efecto
   * secundario.
   */
  const setMedidaReal = (k, campo, v) => setMuebles(prev => prev.map(m => {
    if (m._k !== k) return m;
    // EN CENTÍMETROS Y CON DECIMALES (master, 28/08: «los costados se pueden
    // poner con decimales y siempre se escriben normalmente en centímetros»).
    // Un costado se corta a milímetro, así que 61,5 tiene que llegar entero al
    // pedido: aquí NO se redondea. Se acepta la coma además del punto, porque
    // en un teclado español se teclea coma y `Number('61,5')` es NaN — o sea,
    // la medida se perdería en silencio.
    const bruto = String(v ?? '').trim().replace(',', '.');
    const n = bruto === '' ? null : Number(bruto);
    return { ...m, [campo]: Number.isFinite(n) && n > 0 ? n : null };
  }));

  const setAnchoTarifa = (k, v) => setMuebles(prev => prev.map(m => {
    if (m._k !== k) return m;
    const conAncho = { ...m, anchoTarifa: Number(v) || ANCHO_POR_DEFECTO_LINEAL };
    if (m.pvpManual) return conAncho;   // el precio a mano manda (ver `setPvp`)
    return { ...conAncho, pvp: puntosLocal(conAncho, m.alto) };
  }));

  const setObs = (k, obs) => {
    setMuebles(prev => prev.map(m => m._k === k ? { ...m, obs } : m));
  };

  /** LA DESCRIPCIÓN DE LA LÍNEA, A MANO (master, 31/08: «que la línea importada
   *  se puedan modificar todos los campos»).
   *
   *  Se guarda APARTE de `familia`, no encima: la familia es lo que decide el
   *  despiece, el coste y si la línea comisiona (regla 16). Si escribir un
   *  texto la cambiara, renombrar «BAJO» a «Mueble del office» sacaría esa
   *  línea del cálculo de la comisión sin que nadie lo hubiera pedido.
   *  Vacío = se enseña la familia de siempre. */
  const setDesc = (k, desc) =>
    setMuebles(prev => prev.map(m => m._k === k ? { ...m, desc } : m));

  /** EL PRECIO DE VENTA, A MANO.
   *
   *  `pvpManual` NO es un adorno: en cuanto se toca a mano, ni `setAlto` ni
   *  `setAnchoTarifa` pueden volver a pisarlo. Sin esa marca, el master escribe
   *  un precio pactado, cambia el alto de la línea y el precio vuelve al de
   *  tarifa EN SILENCIO — y el presupuesto sale por otra cifra sin que nadie
   *  vea un error.
   *
   *  Dejar el campo VACÍO devuelve la línea a la tarifa: hace falta una forma
   *  de deshacer que no sea borrar la línea y volver a añadirla. */
  const setPvp = (k, v) => setMuebles(prev => prev.map(m => {
    if (m._k !== k) return m;
    const bruto = String(v ?? '').trim().replace(',', '.');   // teclado español
    if (bruto === '') {
      const { pvpManual, ...limpio } = m;
      return { ...limpio, pvp: puntosLocal(m, m.alto) };
    }
    const n = Number(bruto);
    if (!Number.isFinite(n) || n < 0) return m;
    return { ...m, pvp: Math.round(n * 100) / 100, pvpManual: true };
  }));

  /** El ancho y el alto de una línea que NO es lineal (un mueble de catálogo).
   *  Son las medidas que van al taller. NO tocan el precio: el precio de un
   *  mueble MV sale de su código, y si hiciera falta otro se escribe a mano
   *  arriba — que es una decisión, no un efecto secundario (regla del escalón). */
  const setMedidaMueble = (k, campo, v) => setMuebles(prev => prev.map(m => {
    if (m._k !== k) return m;
    const bruto = String(v ?? '').trim().replace(',', '.');
    const n = bruto === '' ? null : Number(bruto);
    return { ...m, [campo]: Number.isFinite(n) && n > 0 ? n : null };
  }));

  const quitar = (k) => setMuebles(prev => prev.filter(m => m._k !== k));

  const _MANO_SUFIJO = /(D\/I|D|I)$/;
  const manoDe = (cod) => {
    const m = _MANO_SUFIJO.exec(String(cod || '').toUpperCase());
    if (!m) return undefined;
    return m[1] === 'D/I' ? null : m[1];
  };

  const rotarMano = (k) => {
    setMuebles(prev => prev.map(m => {
      if (m._k !== k) return m;
      const cod = String(m.cod || '');
      const cur = manoDe(cod);
      if (cur === undefined) return m;
      let nextMano = 'D';
      if (cur === null) nextMano = 'D';
      else if (cur === 'D') nextMano = 'I';
      else if (cur === 'I') nextMano = 'D/I';
      return { ...m, cod: cod.replace(/(D\/I|D|I)$/i, nextMano === 'D/I' ? 'D/I' : nextMano), mano: nextMano === 'D/I' ? '' : nextMano };
    }));
  };

  const fijarTodasManos = (mano) => {
    setMuebles(prev => prev.map(m => {
      const cur = manoDe(m.cod);
      if (cur === undefined || cur !== null) return m;
      return { ...m, cod: String(m.cod).replace(/(D\/I)$/i, mano), mano: mano };
    }));
  };

  const sinMano = muebles.filter(m => manoDe(m.cod) === null).length;

  const filas = muebles.map(m => {
    const desp = m.encontrado ? costeDetalladoDe(m, paramsCostes, tarifa, pv, acabadoCasco) : { costeTotal: 0, casco: 0, cascoPvp: 0, puerta: 0, puertaPvp: 0 };
    // `|| 0` AQUÍ ERA EL FALLO DE LA COLUMNA. Cuando el casco no tiene precio,
    // `costeTotal` viene `null` — que quiere decir «no se sabe»— y un `|| 0` lo
    // convierte en «cero euros», que es una afirmación. De ahí salía un margen
    // del 73,9 % en una columna cuyo casco vale 168 € de tarifa.
    const coste = desp.costeTotal != null ? desp.costeTotal : null;
    const pvp = Number(m.pvp) || 0;
    const margen = coste == null ? null : pvp - coste;
    const margenPct = (coste == null || pvp <= 0) ? null : (margen / pvp) * 100;
    return { ...m, despiece: desp, coste, margen, margenPct };
  });

  const totalUds = muebles.reduce((s, m) => s + (Number(m.qty) || 1), 0);
  const subtotalBruto = filas.reduce((s, m) => s + m.pvp * (Number(m.qty) || 1), 0);
  const importeDescuento = subtotalBruto * (Number(descuento) || 0) / 100;
  const baseImponible = subtotalBruto - importeDescuento;
  const cuotaIva = baseImponible * (Number(ivaRate) || 0) / 100;
  const totalPvp = baseImponible + cuotaIva;

  // LAS LÍNEAS SIN COSTE NO SE SUMAN COMO CERO: SE CUENTAN Y SE AVISAN. Sumar
  // cero da un coste total más bajo que el real y un margen más alto, que es
  // exactamente el número por el que alguien fija un precio de venta.
  const sinCoste = filas.filter(m => m.coste == null);
  const totalCoste = filas.reduce((s, m) => s + (m.coste || 0) * (Number(m.qty) || 1), 0);
  const totalMargen = baseImponible - totalCoste;
  const totalMargenPct = baseImponible > 0 ? (totalMargen / baseImponible) * 100 : 0;

  // Métricas avanzadas y Escandallo de Taller
  const metricas = useMemo(() => {
    let bajosUds = 0, altosUds = 0, colUds = 0, linUds = 0;
    let bajosAnchoCm = 0, altosAnchoCm = 0;
    let totalPuertasM2 = 0;
    let totalBisagras = 0;
    let totalCajones = 0;
    let totalGavetas = 0;
    let totalPatas = 0;
    let totalColgadores = 0;

    filas.forEach(f => {
      const q = Number(f.qty) || 1;
      const t = String(f.tipo || '').toUpperCase();
      const w = Number(f.ancho) || 0;
      if (t === 'BAJO') { bajosUds += q; bajosAnchoCm += w * q; }
      else if (t === 'ALTO') { altosUds += q; altosAnchoCm += w * q; }
      else if (t === 'COLUMNA') { colUds += q; }
      else { linUds += q; }

      if (f.despiece) {
        totalPuertasM2 += (f.despiece.areaPuertas || 0) * q;
        totalBisagras += (f.despiece.puertas || 0) * 2 * q;
        totalCajones += (f.despiece.caj ? (f.despiece.caj / (p.cajon || 1)) : 0) * q;
        totalGavetas += (f.despiece.gav ? (f.despiece.gav / (p.gaveta || 1)) : 0) * q;
        if (t === 'BAJO' || t === 'COLUMNA') totalPatas += 4 * q;
        if (t === 'ALTO') totalColgadores += 2 * q;
      }
    });

    const minutosEnsamblado = (bajosUds * 25) + (altosUds * 20) + (colUds * 40);

    return {
      bajosUds, altosUds, colUds, linUds,
      metrosBajos: (bajosAnchoCm / 100).toFixed(2),
      metrosAltos: (altosAnchoCm / 100).toFixed(2),
      totalPuertasM2: totalPuertasM2.toFixed(2),
      totalBisagras,
      totalCajones: Math.round(totalCajones),
      totalGavetas: Math.round(totalGavetas),
      totalPatas,
      totalColgadores,
      tiempoTallerHoras: (minutosEnsamblado / 60).toFixed(1)
    };
  }, [filas, p]);

  const filasFiltradas = useMemo(() => {
    if (filtroCat === 'TODOS') return filas;
    if (filtroCat === 'BAJOS') return filas.filter(f => f.tipo === 'BAJO');
    if (filtroCat === 'ALTOS') return filas.filter(f => f.tipo === 'ALTO');
    if (filtroCat === 'COLUMNAS') return filas.filter(f => f.tipo === 'COLUMNA');
    if (filtroCat === 'LINEALES') return filas.filter(f => f.tipo !== 'BAJO' && f.tipo !== 'ALTO' && f.tipo !== 'COLUMNA');
    return filas;
  }, [filas, filtroCat]);

  /**
   * Pone en el CÓDIGO la mano que venía escrita en el texto.
   *
   * El servidor lee bien `10 A60I` y devuelve `mano: 'I'`, pero devuelve
   * también el código de CATÁLOGO, que es `A60D/I` —así se llama el mueble de
   * una puerta en la tarifa MV, con las dos manos posibles—. Y esta pantalla
   * saca la mano del CÓDIGO, no del campo `mano`: `A60D/I` significa «sin
   * decidir», así que la I escrita por el master llegaba y se tiraba, y el
   * mueble salía marcado «⚠️ Sin mano».
   *
   * El master, 25/08: «cuando subo para valorar desde pegado masivo no coge las
   * manos, cuando sí debería ponerlas si están escritas».
   *
   * Se arregla en el código y no leyendo `m.mano` en el rótulo a propósito: el
   * código es la única fuente de la mano en toda la pantalla —`rotarMano` y
   * `fijarTodasManos` lo reescriben—, y meter una segunda fuente acabaría con
   * las dos diciendo cosas distintas en cuanto alguien pulsara el botón.
   */
  const aplicarManoEscrita = (m) => {
    const escrita = String(m?.mano || '').toUpperCase();
    if (escrita !== 'D' && escrita !== 'I') return m;
    const cod = String(m.cod || '');
    if (!/D\/I$/i.test(cod)) return m;          // ya trae mano, o no lleva
    return { ...m, cod: cod.replace(/D\/I$/i, escrita), mano: escrita };
  };

  const fundir = (prev, nuevos) => {
    const out = [...prev];
    for (const n of nuevos) {
      const i = out.findIndex(m => m.cod && n.cod && m.cod === n.cod
        && (m.alto ?? null) === (n.alto ?? null));
      if (i >= 0) out[i] = { ...out[i], qty: (Number(out[i].qty) || 1) + (Number(n.qty) || 1) };
      else out.push(n);
    }
    return out;
  };

  const añadirTexto = async (texto) => {
    const t = (texto || '').trim();
    if (!t) return;
    setBuscando(true); setAviso('');
    try {
      const r = await fetch(`${API_URL}/api/cascos/mv/detectar-relacion`, {
        method: 'POST', headers: authHeaders(),
        body: JSON.stringify({ texto: t, tariff: tarifa }),
      });
      let d = {}; try { d = await r.json(); } catch { d = {}; }
      if (!r.ok || !d.success) { setAviso(d.detail || 'No se reconoció el mueble. Escríbelo como "1 b60i (altura 80)".'); return; }
      const nuevos = (d.muebles || []).map((m, i) =>
        aplicarManoEscrita({ ...m, _k: `add-${Date.now()}-${i}` }));
      setMuebles(prev => fundir(prev, nuevos));
      setBusca('');
      setFoco(false);
    } catch (e) {
      setAviso(`Error al buscar (${e?.message || 'red'}).`);
    } finally { setBuscando(false); }
  };

  const procesarPegadoMasivo = async () => {
    if (!textoMasivo.trim()) return;
    await añadirTexto(textoMasivo);
    setTextoMasivo('');
    setShowPegadoMasivo(false);
  };

  const añadirSugerencia = (c) => {
    if (!c) return;
    const info = familias?.[c.familia];
    const opciones = OPCIONES_ALTURA[info?.type];
    const alto = opciones ? opciones[0] : (c.familia?.startsWith('BAJO') ? 80 : null);
    const pvp = puntosLocal({ cod: c.cod, familia: c.familia, pvp: c.precio?.eur }, alto);
    const nuevo = {
      _k: `add-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
      cod: c.cod,
      familia: c.familia,
      tipo: c.familia?.startsWith('BAJO') ? 'BAJO' : c.familia?.startsWith('ALTO') ? 'ALTO' : 'COLUMNA',
      ancho: c.ancho,
      alto: alto,
      fondo: c.familia?.startsWith('ALTO') ? 33 : 58,
      mano: c.cod.endsWith('D') ? 'D' : c.cod.endsWith('I') ? 'I' : '',
      qty: 1,
      pvp: pvp,
      encontrado: true,
      raw: c.cod,
    };
    setMuebles(prev => fundir(prev, [nuevo]));
    setBusca('');
    setFoco(false);
  };

  const comparativaTarifas = useMemo(() => {
    // Usar las tarifas disponibles del API; si no han cargado aún, fallback a T1-T5
    const listaTarifas = tarifas.length > 0
      ? tarifas.map(t => t.tarifa)
      : ['T1', 'T2', 'T3', 'T4', 'T5'];
    // Índice de la tarifa actual para calcular estimaciones relativas
    const iActual = Math.max(0, listaTarifas.indexOf(tarifa || 'T1'));
    return listaTarifas.map((t, i) => {
      // Estimación por interpolación lineal desde la tarifa actual
      // (los precios del JSON son los reales; aquí solo se usan para comparativa visual)
      const ratio = iActual === 0 ? 1 + i * 0.12 : (i / iActual);
      const totalEst = iActual === 0 ? baseImponible * ratio
        : baseImponible * ((i + 1) / (iActual + 1));
      return {
        tarifa: t,
        nombre: TARIFAS_NOMBRES[t] || t,
        total: totalEst,
        activa: t === tarifa,
      };
    });
  }, [baseImponible, tarifa, tarifas]);

  const copiarParaWhatsApp = () => {
    const lineas = [
      `*PRESUPUESTO COCINA MONTADA MV*`,
      `*Cliente:* ${cliente || 'Particular'} ${ref ? `(Ref: ${ref})` : ''}`,
      `*Tarifa:* ${tarifa} - ${TARIFAS_NOMBRES[tarifa] || 'Estándar'}`,
      `*Color Puertas:* ${acabadoPuerta}`,
      `*Color Cascos:* ${acabadoCasco}`,
      ...(observacionesGenerales?.trim() ? [`*Observaciones:* ${observacionesGenerales.trim()}`] : []),
      `*Muebles Totales:* ${totalUds} unidades`,
      `----------------------------------------`,
      ...muebles.map(m => {
        const manoTxt = m.cod?.endsWith('D') ? ' [Dcha]' : m.cod?.endsWith('I') ? ' [Izq]' : '';
        const obsTxt = m.obs?.trim() ? `\n   └ ✎ Obs: ${m.obs.trim()}` : '';
        return `• ${m.qty}x *${m.cod}* (${m.ancho || '—'}x${m.alto || '—'} cm)${manoTxt} -> ${eur((Number(m.pvp) || 0) * (Number(m.qty) || 1))}${obsTxt}`;
      }),
      `----------------------------------------`,
      `*Subtotal:* ${eur(subtotalBruto)}`,
      ...(descuento > 0 ? [`*Descuento (${descuento}%):* -${eur(importeDescuento)}`] : []),
      `*Base Imponible:* ${eur(baseImponible)}`,
      `*IVA (${ivaRate}%):* ${eur(cuotaIva)}`,
      `*TOTAL FINAL:* ${eur(totalPvp)}`,
    ];
    navigator.clipboard.writeText(lineas.join('\n'));
    setCopiadoWs(true);
    setTimeout(() => setCopiadoWs(false), 2500);
  };

  // Exportador a PDF Oficial con jsPDF
  const exportarPDFOficial = () => {
    const doc = new jsPDF();
    
    // Encabezado Corporativo
    doc.setFillColor(30, 27, 75); // Indigo 950
    doc.rect(0, 0, 210, 35, 'F');
    doc.setTextColor(255, 255, 255);
    doc.setFont('helvetica', 'bold');
    // Sin marca configurada NO se inventa ninguna: el encabezado se queda
    // solo con «COCINA MONTADA». Poner aquí un nombre por defecto es cómo se
    // cuela la marca de una empresa en el presupuesto de otra.
    const _marca = (state?.settings?.companyName || currentUser?.empresa || '').trim().toUpperCase();
    const companyBrand = _marca ? `${_marca} · COCINA MONTADA` : 'COCINA MONTADA';
    doc.text(companyBrand, 14, 18);
    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    doc.text('Presupuesto Oficial de Fabricación y Mobiliario MV', 14, 26);
    
    doc.setFontSize(9);
    doc.text(`Tarifa: ${tarifa} (${TARIFAS_NOMBRES[tarifa] || 'Estándar'})`, 196, 18, { align: 'right' });
    doc.text(`Fecha: ${new Date().toLocaleDateString('es-ES')}`, 196, 26, { align: 'right' });

    // Ficha Cliente y Acabados
    doc.setTextColor(15, 23, 42);
    doc.setFillColor(248, 250, 252);
    doc.roundedRect(14, 42, 182, 24, 3, 3, 'F');
    
    doc.setFontSize(10);
    doc.setFont('helvetica', 'bold');
    doc.text(`Cliente: ${cliente || 'Particular'}`, 18, 51);
    doc.text(`Referencia: ${ref || 'Proyecto Cocina'}`, 18, 60);

    doc.setFont('helvetica', 'normal');
    doc.text(`Puertas: ${acabadoPuerta}`, 110, 51);
    doc.text(`Cascos: ${acabadoCasco}`, 110, 60);

    // Tabla de Muebles
    const tableBody = muebles.map((m, idx) => {
      const descBase = descDe(m);
      const descCompleta = m.obs?.trim() ? `${descBase}\n[Obs: ${m.obs.trim()}]` : descBase;
      return [
        idx + 1,
        m.qty,
        m.cod || '—',
        descCompleta,
        m.ancho ? `${m.ancho} cm` : '—',
        m.alto ? `${m.alto} cm` : '—',
        m.cod?.endsWith('D') ? 'Dcha' : m.cod?.endsWith('I') ? 'Izq' : '—',
        eur(m.pvp),
        eur((Number(m.pvp) || 0) * (Number(m.qty) || 1))
      ];
    });

    autoTable(doc, {
      startY: 72,
      head: [['#', 'Cant', 'Código', 'Descripción / Observaciones', 'Ancho', 'Alto', 'Mano', 'PVP Ud.', 'Total']],
      body: tableBody,
      theme: 'grid',
      headStyles: { fillColor: [67, 56, 202], textColor: 255, fontStyle: 'bold', fontSize: 9 },
      styles: { fontSize: 8, cellPadding: 3 },
      columnStyles: {
        0: { halign: 'center', cellWidth: 10 },
        1: { halign: 'center', cellWidth: 14, fontStyle: 'bold' },
        2: { fontStyle: 'bold', textColor: [67, 56, 202] },
        4: { halign: 'center' },
        5: { halign: 'center' },
        6: { halign: 'center' },
        7: { halign: 'right' },
        8: { halign: 'right', fontStyle: 'bold' }
      }
    });

    const finalY = (doc.lastAutoTable?.finalY || 120) + 10;

    // Observaciones Generales en PDF
    if (observacionesGenerales?.trim()) {
      doc.setFontSize(9);
      doc.setFont('helvetica', 'bold');
      doc.setTextColor(30, 27, 75);
      doc.text('Observaciones Generales de la Cocina / Montaje:', 14, finalY);
      doc.setFont('helvetica', 'normal');
      doc.setTextColor(71, 85, 105);
      doc.text(observacionesGenerales.trim(), 14, finalY + 5);
    }

    // Resumen de Totales
    doc.setFillColor(248, 250, 252);
    doc.roundedRect(120, finalY, 76, 38, 3, 3, 'F');
    
    doc.setFontSize(9);
    doc.text(`Subtotal:`, 125, finalY + 8);
    doc.text(eur(subtotalBruto), 190, finalY + 8, { align: 'right' });
    
    if (descuento > 0) {
      doc.setTextColor(220, 38, 38);
      doc.text(`Descuento (${descuento}%):`, 125, finalY + 16);
      doc.text(`-${eur(importeDescuento)}`, 190, finalY + 16, { align: 'right' });
      doc.setTextColor(15, 23, 42);
    }

    doc.text(`Base Imponible:`, 125, finalY + 23);
    doc.text(eur(baseImponible), 190, finalY + 23, { align: 'right' });

    doc.text(`IVA (${ivaRate}%):`, 125, finalY + 29);
    doc.text(eur(cuotaIva), 190, finalY + 29, { align: 'right' });

    doc.setFontSize(11);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(67, 56, 202);
    doc.text(`TOTAL:`, 125, finalY + 36);
    doc.text(eur(totalPvp), 190, finalY + 36, { align: 'right' });

    doc.save(`Presupuesto_Cocina_${cliente || 'Cliente'}_${tarifa}.pdf`);
  };

  const lanzarAFabricacion = async () => {
    if (!muebles.length) { setAviso('Añade al menos un mueble para lanzar a fabricación.'); return; }
    
    const esInterno = window.confirm(
      `¿Dónde se fabricará este pedido de ${totalUds} módulos? (Casco: ${acabadoCasco || 'Grafito Antracita (19mm)'})\n\n` +
      `• Pulsa ACEPTAR para: 🏠 Fabricación Interna (Taller Propio)\n` +
      `• Pulsa CANCELAR para: 🚚 Fabricación Externa (Proveedor / Fuera)`
    );

    const origen = esInterno ? 'INTERNO' : 'EXTERNO';
    const prefijo = esInterno ? 'OF-INT' : 'OF-EXT';
    const tagOrigen = esInterno ? '🏠 Taller Propio (Interno)' : '🚚 Proveedor Externo (Fuera)';

    try {
      const payload = {
        id: `${prefijo}-2026-${Math.floor(100 + Math.random() * 900)}`,
        cliente: cliente || 'Cliente General',
        ref: ref || 'Cocina Montada 3',
        tipo: 'Cocina Montada 3',
        tarifa: `${tarifa} (${acabadoPuerta})`,
        casco: acabadoCasco || 'Grafito Antracita (19mm)',
        origen: origen,
        tagOrigen: tagOrigen,
        modulos: totalUds,
        m2Tablero: Number(metricas.totalPuertasM2) || 25,
        mlCanteado: Math.round(Number(metricas.totalPuertasM2) * 4),
        estado: 'pendiente',
        prioridad: 'NORMAL',
        progreso: 10,
        observaciones: observacionesGenerales ? `${observacionesGenerales} | Casco: ${acabadoCasco} | ${tagOrigen}` : `Casco: ${acabadoCasco} | ${tagOrigen}`,
        fechaInicio: new Date().toISOString().split('T')[0],
        fechaEstRecepcion: new Date(Date.now() + 5 * 86400000).toISOString().split('T')[0],
        fechaEntrega: new Date(Date.now() + 10 * 86400000).toISOString().split('T')[0],
        muebles: muebles.map(m => ({ cod: m.cod, qty: m.qty, ancho: m.ancho, alto: m.alto, mano: m.mano, obs: m.obs })),
      };

      // AL SERVIDOR, QUE ES DONDE TIENE QUE ESTAR. Hasta el 30/08 esto solo
      // se guardaba en `localStorage`: la orden vivía en ESE navegador y en
      // ningún sitio más, así que `fabrica_orders` —la colección de la que sale
      // el estado de producción en COOP, en el dashboard y en Mis Pedidos— no
      // la escribía nadie y todos los pedidos salían «Confirmado» para siempre.
      //
      // Se manda con `budgetNumber`, que es por donde `estado_fabricacion` cruza
      // la orden con su pedido. Sin referencia la orden se guarda igual —el
      // taller la necesita— pero no aparecerá en COOP, y eso se dice.
      const r = await fetch(`${API_URL}/api/fabrica/orders`, {
        method: 'POST', headers: authHeaders(),
        body: JSON.stringify({
          // EL CUERPO QUE ESPERA EL PORTAL FÁBRICA, que es el módulo del taller
          // que ya existe. La orden vivía solo en `localStorage`, o sea en ESE
          // navegador: no la veía nadie más y COOP no se enteraba nunca.
          budgetNumber: ref || '',           // el cruce con el pedido
          customerName: cliente || 'Cliente General',
          requestedDeliveryDate: payload.fechaEntrega,
          priority: 'normal',
          factoryType: esInterno ? 'internal' : 'external',
          internalNotes: `${payload.tipo} · ${payload.tarifa}`,
          productionNotes: payload.observaciones,
          items: muebles.map(m => ({
            code: m.cod, qty: Number(m.qty) || 1,
            width: m.ancho, height: m.alto, hand: m.mano, notes: m.obs || '',
          })),
        }),
      });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(d.detail || 'No se pudo lanzar la orden.');

      // Y TAMBIÉN EN LOCAL, porque la pantalla de Planificación sigue leyendo de
      // ahí. Quitarlo ahora dejaría esa pantalla vacía; se migra aparte.
      try {
        const guardadas = JSON.parse(localStorage.getItem('ordenes_fabricacion_taller') || '[]');
        const actualizadas = [payload, ...guardadas.filter(x => x.id !== payload.id)];
        localStorage.setItem('ordenes_fabricacion_taller', JSON.stringify(actualizadas));
      } catch (e) { console.error('Error guardando OF:', e); }

      alert(`✓ Orden de Fabricación ${d.order?.orderNumber || payload.id} `
        + `[${tagOrigen}] lanzada.\n\n`
        + (ref
            ? 'Ya se ve en COOP → Producción como «Pendiente».'
            : 'AVISO: sin referencia no se puede cruzar con su pedido, así que '
              + 'no aparecerá en el seguimiento de COOP. Ponle una referencia y '
              + 'vuelve a lanzarla.'));
      if (setState) {
        setState(prev => ({ ...prev, currentTab: 'planificacionProduccion' }));
      }
    } catch (e) {
      alert(`Error al lanzar a fabricación: ${e.message}`);
    }
  };

  /**
   * PASAR LA RELACIÓN A PEDIDO.
   *
   * El master, 28/08: «necesito crear pedidos desde Cocina Montada 3». Hasta
   * ahora esta pantalla solo guardaba PRESUPUESTOS, así que sus cocinas no
   * llegaban nunca a la cooperativa: un presupuesto no se ha vendido y no paga
   * comisión a nadie.
   *
   * Se guarda como pedido con la marca `origen`, que es lo que hace que entre
   * en COOP (`services/origen_pedidos.py`). Sin esa marca sería indistinguible
   * de un pedido de Cocina Desmontada.
   *
   * LAS LÍNEAS VAN CON SU FAMILIA Y SU IMPORTE YA MULTIPLICADO. Es lo que espera
   * el cálculo de comisiones: `price` es el total de la línea y `familia` es lo
   * que decide si ese mueble incentiva o no. Sin la familia, el pedido entraría
   * con «0 muebles».
   */
  const pasarAPedido = async () => {
    if (!muebles.length) { setAviso('Añade al menos un mueble para pedir.'); return; }

    // ¿YA HAY UN PEDIDO DE ESTA COCINA? Se pregunta al servidor, no solo a la
    // memoria de la pantalla: si se recuperó un presupuesto en otra sesión, el
    // id de aquí está vacío y se volvería a duplicar.
    let destino = pedidoId;
    if (!destino && ref) {
      try {
        const q = await fetch(`${API_URL}/api/cascos/orders?kind=pedido`, { headers: authHeaders() });
        const dq = await q.json().catch(() => ({}));
        const ya = (dq.orders || []).find(
          o => (o.ref || '') === ref && (o.origen || '') === 'cocina_montada_3');
        if (ya) {
          // NO SE DECIDE POR ÉL. Duplicar paga dos comisiones y fusionar pisa un
          // pedido que quizá ya está en el taller: lo elige el master.
          // eslint-disable-next-line no-alert
          if (!window.confirm(
            `Ya existe un pedido con la referencia «${ref}»`
            + `${ya.createdAt ? ` (${String(ya.createdAt).slice(0, 10)})` : ''}.\n\n`
            + 'ACEPTAR: actualizar ESE pedido con lo que hay ahora en pantalla.\n'
            + 'CANCELAR: no hacer nada (cambia la referencia si quieres uno nuevo).')) return;
          destino = ya.id;
        }
      } catch { /* si no se puede comprobar, se sigue como pedido nuevo */ }
    }

    // Se avisa porque un pedido SÍ cuenta: entra en la cooperativa y genera
    // comisión. Un presupuesto no.
    // eslint-disable-next-line no-alert
    if (!window.confirm(
      `Vas a ${destino ? 'ACTUALIZAR el' : 'crear un'} PEDIDO de ${totalUds} `
      + `mueble${totalUds === 1 ? '' : 's'} para ${cliente || 'Cliente General'}.\n\n`
      + 'Un pedido cuenta para la cooperativa y genera comisión; un presupuesto no.\n\n¿Seguimos?')) return;
    setGuardando(true); setAviso('');
    try {
      const payload = {
        id: destino || `cm3-ped-${Date.now()}`,
        kind: 'pedido',
        origen: 'cocina_montada_3',
        cliente: cliente || 'Cliente General',
        ref: ref || '',
        expediente: ref || '',
        ivaRate: Number(ivaRate) || 21,
        descuento: Number(descuento) || 0,
        total: totalPvp,
        lines: filas.map(m => ({
          code: m.cod || '',
          name: m.etiqueta || m.desc || m.cod || '',
          familia: m.familia || '',
          quantity: Number(m.qty) || 1,
          price: (Number(m.pvp) || 0) * (Number(m.qty) || 1),
          // Las medidas DEFINITIVAS, que no son el escalón de la tarifa. Van al
          // pedido porque son lo que se fabrica.
          anchoReal: m.anchoReal ?? null,
          altoReal: m.altoReal ?? null,
        })),
      };
      const r = await fetch(`${API_URL}/api/cascos/orders`, {
        method: 'POST', headers: authHeaders(), body: JSON.stringify(payload),
      });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(d.detail || 'Error al crear el pedido');
      setAviso('');
      // SE RECUERDA EL PEDIDO: volver a pulsar ACTUALIZA este, no crea otro.
      setPedidoId(d.order?.id || payload.id);
      alert(destino
        ? '✓ Pedido actualizado.'
        : '✓ Pedido creado. Ya aparece en COOP para asignarle comercial y montador.');
    } catch (e) {
      setAviso(`No se pudo crear el pedido: ${e.message}`);
    } finally {
      setGuardando(false);
    }
  };

  /**
   * GUARDAR EL PRESUPUESTO — Y QUE SE PUEDA RECUPERAR.
   *
   * ESTO NO GUARDABA NADA (arreglado el 30/08). Se mandaba a
   * `POST /api/presupuestos`, que es el endpoint DEL DIGITALIZADOR y espera
   * otro cuerpo entero: sus campos tienen todos valor por defecto, así que
   * FastAPI aceptaba el payload de esta pantalla sin quejarse, ignoraba todo lo
   * que no reconocía —`muebles`, `cliente`, `referencia`, `total`— y grababa un
   * proyecto VACÍO: cero muebles, sin cliente, sin referencia, total 0 y
   * `userId: "anonymous"`. Y devolvía 200, así que aquí salía «✓ Presupuesto
   * guardado con éxito». Cada presupuesto guardado desde esta pantalla era un
   * registro fantasma, y el trabajo se perdía sin un solo error.
   *
   * Ahora va por el MISMO camino que un pedido (`POST /api/cascos/orders`), que
   * es el que ya funciona: guarda las líneas de verdad, pasa por el permiso de
   * la sección (regla 22) y se puede volver a listar. Cambia solo el `kind`, y
   * eso es lo que importa: un `presupuesto` NO cuenta para la cooperativa ni
   * paga comisión — solo `kind: "pedido"` entra en COOP (regla 21).
   */
  const guardarPresupuesto = async () => {
    if (!muebles.length) { setAviso('Añade al menos un mueble para guardar.'); return; }
    setGuardando(true); setAviso('');
    try {
      const payload = {
        id: savedId || `cm3-pre-${Date.now()}`,
        kind: 'presupuesto',
        origen: 'cocina_montada_3',
        cliente: cliente || 'Cliente General',
        ref: ref || '',
        expediente: ref || '',
        ivaRate: Number(ivaRate) || 21,
        descuento: Number(descuento) || 0,
        total: totalPvp,
        lines: filas.map(m => ({
          code: m.cod || '',
          name: m.etiqueta || m.desc || m.cod || '',
          familia: m.familia || '',
          quantity: Number(m.qty) || 1,
          price: (Number(m.pvp) || 0) * (Number(m.qty) || 1),
          anchoReal: m.anchoReal ?? null,
          altoReal: m.altoReal ?? null,
        })),
        // LO QUE HACE FALTA PARA REABRIRLO TAL CUAL. Las líneas de arriba son
        // para el resto del ERP; esto es el estado de ESTA pantalla, que si no
        // habría que reconstruir a ojo — y a ojo se pierden las manos D/I, los
        // acabados y la tarifa con la que se valoró.
        cm3: { muebles, telefono, tarifa, acabadoPuerta, acabadoCasco,
               observaciones: observacionesGenerales },
      };
      const r = await fetch(`${API_URL}/api/cascos/orders`, {
        method: 'POST', headers: authHeaders(), body: JSON.stringify(payload),
      });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(d.detail || 'Error al guardar');
      setSavedId(d.order?.id || payload.id);
      alert('✓ Presupuesto guardado. Se recupera con el botón «Presupuestos».');
    } catch (e) {
      setAviso(`No se pudo guardar: ${e.message}`);
    } finally { setGuardando(false); }
  };

  // ─── RECUPERAR UN PRESUPUESTO GUARDADO ───────────────────────────────────
  const [guardados, setGuardados] = useState(null);   // null = panel cerrado
  const [cargandoGuardados, setCargandoGuardados] = useState(false);

  const abrirGuardados = async () => {
    setGuardados([]); setCargandoGuardados(true);
    try {
      const r = await fetch(
        `${API_URL}/api/cascos/orders?kind=presupuesto&userId=${encodeURIComponent(currentUser?.id || '')}`,
        { headers: authHeaders() });
      const d = await r.json().catch(() => ([]));
      if (!r.ok) throw new Error(d.detail || 'No se pudieron leer los presupuestos.');
      // Solo los de ESTA pantalla: los de Cocina Desmontada se recuperan en la
      // suya, y sus líneas son cascos, no muebles de tarifa MV.
      setGuardados((Array.isArray(d) ? d : (d.orders || []))
        .filter(o => (o.origen || '') === 'cocina_montada_3' || o.cm3));
    } catch (e) {
      setAviso(e.message);
      setGuardados(null);
    } finally { setCargandoGuardados(false); }
  };

  const recuperar = (o) => {
    const c = o.cm3 || {};
    if (muebles.length && !window.confirm(
      'Vas a sustituir la relación que tienes ahora en pantalla. ¿Seguimos?')) return;
    setMuebles(Array.isArray(c.muebles) ? c.muebles : []);
    setCliente(o.cliente || '');
    setRef(o.ref || o.expediente || '');
    setTelefono(c.telefono || '');
    setDescuento(Number(o.descuento) || 0);
    setIvaRate(Number(o.ivaRate) || 21);
    if (c.tarifa) setTarifa(c.tarifa);
    if (c.acabadoPuerta) setAcabadoPuerta(c.acabadoPuerta);
    if (c.acabadoCasco) setAcabadoCasco(c.acabadoCasco);
    setObservacionesGenerales(c.observaciones || '');
    setSavedId(o.id);            // volver a guardar ACTUALIZA, no duplica
    setPedidoId(null);           // es un presupuesto: su pedido se busca por referencia
    setGuardados(null);
    setAviso('');
  };


  // EL CANDADO DEL COSTE. Estaba MUERTO: no abría de ninguna manera, ni con
  // pulsación larga ni con Shift+clic (30/08). Tres fallos a la vez:
  //
  //  1. Se esparcía `{...handlersCandado}` en el botón, y el hook NO devuelve
  //     handlers: devuelve `{ props, consumir }`. O sea que al `<button>` le
  //     llegaban dos atributos llamados `props` y `consumir` —que React ni
  //     entiende— y NINGÚN gesto. Hay que esparcir `.props`, como hace
  //     Rentabilidad, que es donde sí funciona.
  //  2. No había `onClick`, así que Shift+clic tampoco hacía nada.
  //  3. El segundo argumento era una función y el hook espera `{ ms }`: esa
  //     pista nunca se llegó a enseñar.
  //
  // Resultado: se tocaba el candado y no pasaba nada, en tablet y en ordenador.
  // Y no saltaba ningún error — el botón se veía perfectamente.
  const handlersCandado = usePulsacionLarga(() => {
    setVerCoste(v => !v);
    setPistaCandado('');
  });

  return (
    <div className="absolute inset-0 overflow-y-auto bg-slate-100 p-2 sm:p-3 pb-36 space-y-2">
      
      {/* Banner de progreso durante la importación de PDF */}
      {importandoRel && (
        <div className="bg-amber-500 text-slate-950 px-4 py-2 text-xs font-black flex items-center justify-between animate-pulse">
          <div className="flex items-center gap-2">
            <Loader size={15} className="animate-spin" />
            <span>{progresoImportacion || 'Analizando PDF con IA (detectando páginas y códigos de módulos)...'}</span>
          </div>
        </div>
      )}

      {/* Cabecera Principal Compacta */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white rounded-2xl px-3 py-2 shadow-lg border border-slate-800 flex items-center justify-between gap-2 flex-wrap">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-indigo-600 border border-indigo-400/40 flex items-center justify-center shadow-sm shrink-0">
            <Layers size={15} className="text-white" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <h1 className="text-sm font-black text-white tracking-tight">Presupuestador</h1>
              <span className="px-1.5 py-0.2 rounded-full bg-indigo-500/20 border border-indigo-400/30 text-indigo-200 text-[9px] font-black uppercase">Tarifa {tarifa}</span>
            </div>
            <p className="text-[9px] text-indigo-200/70 font-medium leading-none">
              {acabadoCasco}
            </p>
          </div>
        </div>

        {/* Botonera Central: herramientas secundarias */}
        <div className="flex items-center gap-1 flex-wrap">
          {/* MAXIMIZAR / MINIMIZAR (master, 25/08). El mismo componente que el
              carril y el Estudio 3D: una sola pantalla completa en todo el ERP,
              con un solo nombre y un solo efecto. Aquí se gana mucho — esta
              pantalla es una tabla larga y la barra del navegador se come el
              alto justo donde están las filas. */}
          <BotonPantallaCompleta
            className="flex items-center gap-1 px-2 py-1 rounded-lg border text-[10px] font-bold transition-all bg-white/10 hover:bg-white/20 border-white/10 text-white"
            claseTexto="truncate"
            textos={{ dentro: 'Reducir', fuera: 'Maximizar' }} />
          <button
            onClick={() => setShowMuestrario(v => !v)}
            className={`flex items-center gap-1 px-2 py-1 rounded-lg border text-[10px] font-bold transition-all ${showMuestrario ? 'bg-accion-500 text-white border-accion-400' : 'bg-white/10 hover:bg-white/20 border-white/10 text-white'}`}
            title="Muestrario de acabados de puertas y cascos"
          >
            <Palette size={12} className="text-dato-300" /> Acabados
          </button>
          <button
            onClick={() => setShowEscandallo(v => !v)}
            className={`flex items-center gap-1 px-2 py-1 rounded-lg border text-[10px] font-bold transition-all ${showEscandallo ? 'bg-accion-500 text-slate-950 border-accion-400' : 'bg-white/10 hover:bg-white/20 border-white/10 text-white'}`}
            title="Escandallo técnico de taller"
          >
            <Hammer size={12} className="text-dato-400" /> Escandallo
          </button>
          {/* Desplegable IMPORTAR */}
          <div className="relative">
            <input ref={relacionInputRef} type="file" accept="application/pdf" className="hidden" onChange={(e) => importarRelacion(e.target.files?.[0])} />
            <input ref={alvicInputRef} type="file" accept="application/pdf" className="hidden" onChange={(e) => importarAlvic(e.target.files?.[0])} />
            <button
              onClick={() => setMenuImportar(v => !v)}
              title="Importar muebles: en pantalla, desde la plantilla PDF o desde un presupuesto Alvic"
              className="flex items-center gap-1 px-2 py-1 bg-white/15 hover:bg-white/25 text-white rounded-lg font-bold text-[10px] border border-white/10 transition-all"
            >
              {importandoRel ? <Loader size={12} className="animate-spin" /> : <FileUp size={12} />} Importar
              <ChevronDown size={11} className={menuImportar ? 'rotate-180 transition-transform' : 'transition-transform'} />
            </button>
            {menuImportar && (
              <>
                <div className="fixed inset-0 z-40" onClick={() => setMenuImportar(false)} />
                <div className="absolute right-0 mt-1.5 z-50 w-72 bg-white rounded-xl shadow-2xl ring-1 ring-black/10 overflow-hidden text-slate-700 animate-in fade-in zoom-in-95">
                  <button
                    onClick={() => { setMenuImportar(false); setShowPegadoMasivo(true); }}
                    className="w-full text-left px-3.5 py-3.5 sm:py-2.5 hover:bg-accion-50 active:bg-accion-100 flex items-start gap-3 sm:gap-2.5 border-b border-slate-100 transition-colors"
                  >
                    <List size={16} className="text-dato-600 mt-0.5 shrink-0" />
                    <div>
                      <span className="block text-[13px] sm:text-xs font-black text-slate-800">Pegado Masivo (Texto / WhatsApp)</span>
                      <span className="block text-[11px] sm:text-[9px] text-slate-500 font-medium leading-snug">Pega la relación de muebles en masa o móntalos a mano</span>
                    </div>
                  </button>

                  <button
                    onClick={() => { setMenuImportar(false); relacionInputRef.current?.click(); }}
                    className="w-full text-left px-3.5 py-3.5 sm:py-2.5 hover:bg-accion-50 active:bg-accion-100 flex items-start gap-3 sm:gap-2.5 border-b border-slate-100 transition-colors"
                  >
                    <Sparkles size={16} className="text-dato-500 mt-0.5 shrink-0" />
                    <div>
                      <span className="block text-[13px] sm:text-xs font-black text-slate-800">Desde plantilla (PDF nomenclaturas)</span>
                      <span className="block text-[11px] sm:text-[9px] text-slate-500 font-medium leading-snug">Sube la plantilla rellenada con los códigos MV</span>
                    </div>
                  </button>

                  <button
                    onClick={() => { setMenuImportar(false); alvicInputRef.current?.click(); }}
                    className="w-full text-left px-3.5 py-3.5 sm:py-2.5 hover:bg-accion-50 active:bg-accion-100 flex items-start gap-3 sm:gap-2.5 border-b border-slate-100 transition-colors"
                  >
                    <Package size={16} className="text-dato-600 mt-0.5 shrink-0" />
                    <div>
                      <span className="block text-[13px] sm:text-xs font-black text-slate-800">Desde presupuesto Alvic (PDF)</span>
                      <span className="block text-[11px] sm:text-[9px] text-slate-500 font-medium leading-snug">Proforma Alvic → equivalencia de muebles y cascos</span>
                    </div>
                  </button>

                  <button
                    onClick={() => { setMenuImportar(false); descargarPlantillaEnBlanco(); }}
                    className="w-full text-left px-3.5 py-3.5 sm:py-2.5 hover:bg-accion-50 active:bg-accion-100 flex items-start gap-3 sm:gap-2.5 transition-colors"
                  >
                    <Download size={16} className="text-dato-600 mt-0.5 shrink-0" />
                    <div>
                      <span className="block text-[13px] sm:text-xs font-black text-slate-800">Descargar plantilla en blanco</span>
                      <span className="block text-[11px] sm:text-[9px] text-slate-500 font-medium leading-snug">PDF rellenable con las 58 familias</span>
                    </div>
                  </button>
                </div>
              </>
            )}
          </div>
          <button
            onClick={() => setShowComparador(v => !v)}
            className={`flex items-center gap-1 px-2 py-1 rounded-lg border text-[10px] font-bold transition-all ${showComparador ? 'bg-accion-500 text-slate-950 border-accion-400' : 'bg-white/10 hover:bg-white/20 border-white/10 text-white'}`}
            title="Comparar presupuesto en todas las tarifas T1-T5"
          >
            <Sparkles size={12} className={showComparador ? 'text-slate-950' : 'text-dato-400'} /> Comparar
          </button>
          <button
            onClick={exportarPDFOficial}
            disabled={!muebles.length}
            className="flex items-center gap-1 px-2 py-1 rounded-lg bg-white/10 hover:bg-white/20 border border-white/10 text-[10px] font-bold transition-all disabled:opacity-40 text-white"
            title="Exportar PDF oficial del presupuesto"
          >
            <Download size={12} /> PDF
          </button>
          {/* RECUPERAR LO GUARDADO. Esta pantalla guardaba presupuestos y no
              tenía por dónde volver a abrirlos: guardar sin poder recuperar es
              no guardar. */}
          <button
            onClick={abrirGuardados}
            className="flex items-center gap-1 px-2 py-1 rounded-lg bg-white/10 hover:bg-white/20 border border-white/10 text-[10px] font-bold transition-all text-white"
            title="Abrir un presupuesto guardado"
            data-testid="cm3-abrir-presupuestos"
          >
            <FolderOpen size={12} /> Presupuestos
          </button>
        </div>

        {/* CTAs Primarios */}
        <div className="flex items-center gap-1">
          <button
            onClick={lanzarAFabricacion}
            disabled={!muebles.length}
            className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-gradient-to-r from-accion-500 to-accion-600 hover:from-accion-600 hover:to-accion-700 text-slate-950 font-black text-[10px] shadow-sm transition-all disabled:opacity-40"
            title="Crear orden de fabricación en taller"
          >
            <Factory size={12} /> Fabricar
          </button>
          {/* CREAR PEDIDO ES LA ACCIÓN PRINCIPAL DE ESTA PANTALLA, y hasta el
              30/08 era un botón de 10 px idéntico a «Fabricar» y a
              «Presupuesto». Es la ÚNICA de las tres que crea algo que cuenta:
              entra en la cooperativa, se le asigna comercial y montador, y de
              ahí sale una comisión. Un presupuesto no se ha vendido. Que la
              acción que mueve dinero pareciera un control terciario es la razón
              de que hubiera que preguntar dónde estaba. */}
          <button
            onClick={pasarAPedido}
            disabled={!muebles.length || guardando}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-ok-600 hover:bg-ok-700 text-white text-[11px] font-black shadow-md ring-1 ring-ok-300/50 transition-all disabled:opacity-40"
            title="Crear un PEDIDO con esta relación: cuenta para la cooperativa y genera comisión"
            data-testid="cm3-pasar-a-pedido"
          >
            {guardando ? <Loader size={13} className="animate-spin" /> : <ShoppingCart size={13} />} Crear pedido
          </button>
          <button
            onClick={guardarPresupuesto}
            disabled={!muebles.length || guardando}
            className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-accion-600 hover:bg-accion-700 text-white text-[10px] font-black shadow-sm transition-all disabled:opacity-40"
            title="Guardar presupuesto en el sistema"
          >
            {guardando ? <Loader size={12} className="animate-spin" /> : <Save size={12} />} Guardar
          </button>
        </div>
      </div>

      {/* Muestrario Desplegable de Acabados — solo Cascos ACB */}
      {showMuestrario && (
        <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-sm animate-in fade-in zoom-in-95">
          <div className="space-y-2">
            <span className="text-[11px] font-black text-slate-800 uppercase tracking-wide flex items-center gap-1.5">
              <Box size={14} className="text-dato-600" /> Acabado de Cascos (Grupo ACB):
            </span>
            <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-1.5">
              {MUESTRARIO_CASCOS.map(ac => (
                <button
                  key={ac.id}
                  onClick={() => setAcabadoCasco(ac.nombre)}
                  className={`p-2 rounded-xl border text-left transition-all flex flex-col gap-1.5 ${acabadoCasco === ac.nombre ? 'border-accion-600 bg-accion-50/50 ring-1 ring-accion-300' : 'border-slate-200 hover:border-slate-300'}`}
                >
                  <div className="w-full h-6 rounded-lg border border-slate-200 shadow-inner" style={{ backgroundColor: ac.color }} />
                  <span className="text-[10px] font-bold text-slate-800 leading-tight">{ac.nombre}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Escandallo Técnico de Taller Desplegable */}
      {showEscandallo && (
        <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white rounded-2xl p-4 border border-indigo-500/30 shadow-lg grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2.5 animate-in fade-in zoom-in-95">
          <div className="p-2.5 bg-white/5 rounded-xl border border-white/10">
            <div className="text-[9px] uppercase font-bold text-indigo-300">Tablero Puertas</div>
            <div className="text-base font-black text-white">{metricas.totalPuertasM2} m²</div>
            <div className="text-[9px] text-indigo-200/70">{acabadoPuerta}</div>
          </div>
          <div className="p-2.5 bg-white/5 rounded-xl border border-white/10">
            <div className="text-[9px] uppercase font-bold text-indigo-300">Cascos ACB</div>
            <div className="text-base font-black text-white">{totalUds} módulos</div>
            <div className="text-[9px] text-indigo-200/70">{acabadoCasco}</div>
          </div>
          <div className="p-2.5 bg-white/5 rounded-xl border border-white/10">
            <div className="text-[9px] uppercase font-bold text-indigo-300">Bisagras con Freno</div>
            <div className="text-base font-black text-white">{metricas.totalBisagras} uds</div>
            <div className="text-[9px] text-indigo-200/70">Blum / Hettich</div>
          </div>
          <div className="p-2.5 bg-white/5 rounded-xl border border-white/10">
            <div className="text-[9px] uppercase font-bold text-indigo-300">Cajones & Gavetas</div>
            <div className="text-base font-black text-white">{metricas.totalCajones + metricas.totalGavetas} uds</div>
            <div className="text-[9px] text-dato-200/70">{metricas.totalCajones} caj. + {metricas.totalGavetas} gav.</div>
          </div>
          <div className="p-2.5 bg-white/5 rounded-xl border border-white/10">
            <div className="text-[9px] uppercase font-bold text-indigo-300">Patas & Colgadores</div>
            <div className="text-base font-black text-white">{metricas.totalPatas} / {metricas.totalColgadores}</div>
            <div className="text-[9px] text-indigo-200/70">Patas / Colgadores</div>
          </div>
          <div className="p-2.5 bg-emerald-950/40 rounded-xl border border-emerald-500/30">
            <div className="text-[9px] uppercase font-bold text-emerald-300">Tiempo de Taller</div>
            <div className="text-base font-black text-emerald-400">{metricas.tiempoTallerHoras} horas</div>
            <div className="text-[9px] text-emerald-200/70">Ensamblado en taller</div>
          </div>
        </div>
      )}

      {/* Datos del Cliente y Presupuesto ULTRA COMPACTOS (1 sola fila) */}
      <div className="bg-white rounded-2xl p-2 px-3 border border-slate-200 shadow-sm flex items-center gap-2 flex-wrap text-xs">
        <div className="flex-1 min-w-[150px]">
          <div className="relative flex items-center">
            <User size={13} className="absolute left-2.5 text-slate-400" />
            <input
              value={cliente}
              onChange={e => setCliente(e.target.value)}
              placeholder="Cliente / Titular…"
              className="w-full pl-7 pr-2 py-1 border border-slate-200 rounded-lg text-xs font-bold outline-none focus:border-indigo-500"
            />
          </div>
        </div>

        <div className="flex-1 min-w-[150px]">
          <div className="relative flex items-center">
            <Tag size={13} className="absolute left-2.5 text-slate-400" />
            <input
              value={ref}
              onChange={e => setRef(e.target.value)}
              placeholder="Referencia / Obra…"
              className="w-full pl-7 pr-2 py-1 border border-slate-200 rounded-lg text-xs font-bold outline-none focus:border-indigo-500"
            />
          </div>
        </div>

        <div className="w-28">
          <div className="relative flex items-center">
            <Percent size={13} className="absolute left-2.5 text-slate-400" />
            <input
              type="number"
              min="0"
              max="100"
              value={descuento}
              onChange={e => setDescuento(e.target.value)}
              placeholder="Desc %"
              className="w-full pl-7 pr-2 py-1 border border-slate-200 rounded-lg text-xs font-bold outline-none focus:border-indigo-500"
            />
          </div>
        </div>

        <div className="w-32">
          <div className="relative flex items-center">
            <Receipt size={13} className="absolute left-2.5 text-slate-400" />
            <select
              value={ivaRate}
              onChange={e => setIvaRate(e.target.value)}
              className="w-full pl-7 pr-1 py-1 border border-slate-200 rounded-lg text-xs font-bold outline-none focus:border-indigo-500 bg-white"
            >
              <option value="21">21% IVA</option>
              <option value="10">10% IVA</option>
              <option value="0">0% Exento</option>
            </select>
          </div>
        </div>

        <div className="flex-[2] min-w-[200px]">
          <div className="relative flex items-center">
            <FileText size={13} className="absolute left-2.5 text-slate-400" />
            <input
              value={observacionesGenerales}
              onChange={e => setObservacionesGenerales(e.target.value)}
              placeholder="Observaciones generales (notas taller/montaje)…"
              className="w-full pl-7 pr-2 py-1 border border-slate-200 rounded-lg text-xs font-bold outline-none focus:border-indigo-500"
            />
          </div>
        </div>
      </div>

      {/* Comparador de Tarifas Desplegable */}
      {showComparador && (
        <div className="bg-gradient-to-r from-amber-50 via-indigo-50 to-amber-50 border border-amber-200 rounded-3xl p-4 shadow-sm space-y-2">
          <div className="flex items-center justify-between gap-2 flex-wrap">
            <div className="flex items-center gap-2">
              <Sparkles size={16} className="text-dato-600 shrink-0" />
              <span className="font-black text-xs text-slate-900 uppercase tracking-wide">Ver presupuesto en otra tarifa:</span>
            </div>
            {/* AVISO IMPORTANTE: el catálogo MV NO es lineal. T4 (ZENIT/POLILAMINADO) tiene
                muchos artículos más baratos que T2 o T3. Los precios son EXACTOS al cambiar de tarifa. */}
            <span className="text-[10px] text-dato-700 font-semibold bg-dato-100 border border-dato-300 rounded-lg px-2 py-0.5">
              ⚠️ El catálogo MV no sigue orden de precio T1→T21. Pulsa cada tarifa para ver el precio real.
            </span>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            {comparativaTarifas.map(ct => (
              <button
                key={ct.tarifa}
                onClick={() => setTarifa(ct.tarifa)}
                title={TARIFAS_NOMBRES[ct.tarifa] || ct.tarifa}
                className={`px-3 py-1.5 rounded-xl border text-left transition-all ${
                  ct.activa
                    ? 'bg-accion-600 text-white border-accion-600 shadow-md ring-2 ring-accion-300'
                    : 'bg-white text-slate-700 border-slate-200 hover:border-accion-300 hover:bg-accion-50'
                }`}
              >
                <div className="text-[10px] font-black uppercase">{ct.tarifa}</div>
                <div className="text-[9px] text-current opacity-70 truncate max-w-[80px]">{(TARIFAS_NOMBRES[ct.tarifa] || '').split('/')[0]}</div>
              </button>
            ))}
          </div>
          <p className="text-[9px] text-slate-400 font-medium">Haz clic en cualquier tarifa para recalcular el presupuesto completo con los precios oficiales de esa tarifa.</p>
        </div>
      )}

      {/* Panel de Trabajo: Buscador, Paleta y Tabla */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden flex flex-col flex-1">
        
        {/* Barra Superior del Panel */}
        <div className="p-5 border-b border-slate-100 space-y-3">
          {/* Selector de Tarifa y Métricas */}
          <div className="flex items-center justify-between gap-4 flex-wrap text-xs">
            {/* `min-w-0` NO ES DECORACIÓN: sin él nada de lo de dentro se puede
                deslizar. Un hijo de un flex trae `min-width: auto`, o sea que
                se NIEGA a encogerse por debajo de su contenido: esta caja se
                iba a 819 px dentro de un padre de 332 y desbordaba, así que el
                `max-w-full` y el `overflow-x-auto` de la tira de tarifas de
                abajo no tenían contra qué medirse y no hacían nada. */}
            <div className="flex items-center gap-2 flex-wrap min-w-0 max-w-full">
              <span className="font-bold text-slate-500 uppercase text-[10px] tracking-wider shrink-0">Tarifa:</span>
              {/* Selector dinámico de tarifa — usa las 21 tarifas del API */}
              {tarifas.length > 0 ? (
                <div className="flex gap-1 bg-slate-100 p-1 rounded-xl flex-wrap max-w-xl overflow-x-auto">
                  {tarifas.map(({ tarifa: t }) => (
                    <button
                      key={t}
                      onClick={() => setTarifa(t)}
                      title={TARIFAS_NOMBRES[t] || t}
                      className={`px-2.5 py-1 rounded-lg font-black text-[10px] transition-all shrink-0 ${tarifa === t ? 'bg-accion-600 text-white shadow-sm' : 'text-slate-600 hover:bg-white'}`}
                    >
                      {t}
                    </button>
                  ))}
                </div>
              ) : (
                /* LAS 21 TARIFAS SE DESLIZAN EN PANTALLA ESTRECHA.
                   Esta tira mide 819 px de ancho. En un móvil de 390 eso deja
                   FUERA de la pantalla desde la T11 en adelante, y sin ningún
                   contenedor deslizable no había forma de llegar a ellas: la
                   mitad de las tarifas, inseleccionables desde el teléfono.
                   Los botones ya llevan `shrink-0`, así que sólo faltaba
                   dejar que la tira se desplace. La rama de arriba (la de
                   tarifas filtradas) ya lo tenía; ésta se quedó atrás. */
                <div className="flex gap-1 bg-slate-100 p-1 rounded-xl max-w-full overflow-x-auto">
                  {['T1','T2','T3','T4','T5','T6','T7','T8','T9','T10','T11','T12','T13','T14','T15','T16','T17','T18','T19','T20','T21'].map(t => (
                    <button
                      key={t}
                      onClick={() => setTarifa(t)}
                      title={TARIFAS_NOMBRES[t] || t}
                      className={`px-2.5 py-1 rounded-lg font-black text-[10px] transition-all shrink-0 ${tarifa === t ? 'bg-accion-600 text-white shadow-sm' : 'text-slate-600 hover:bg-white'}`}
                    >
                      {t}
                    </button>
                  ))}
                </div>
              )}
              <span className="text-xs text-slate-500 font-semibold italic hidden lg:inline">
                ({TARIFAS_NOMBRES[tarifa] || 'Acabado estándar'})
              </span>
            </div>

            {/* `flex-wrap`: son cuatro pastillas y en un móvil de 390 px no
                caben en una fila. Sin envolver, la última —«N sin mano · Fijar
                Dcha», que además es un BOTÓN— empezaba en x=330 y se salía por
                la derecha sin nada que deslizar: inalcanzable. */}
            <div className="flex items-center gap-2.5 flex-wrap">
              <div className="flex items-center gap-1.5 px-3 py-1 rounded-xl bg-emerald-50 text-emerald-800 border border-emerald-200 font-bold text-xs">
                <Package size={14} /> Bajos: {metricas.bajosUds} ({metricas.metrosBajos} m)
              </div>
              <div className="flex items-center gap-1.5 px-3 py-1 rounded-xl bg-sky-50 text-sky-800 border border-sky-200 font-bold text-xs">
                <Package size={14} /> Altos: {metricas.altosUds} ({metricas.metrosAltos} m)
              </div>
              <div className="flex items-center gap-1.5 px-3 py-1 rounded-xl bg-indigo-50 text-indigo-800 border border-indigo-200 font-bold text-xs">
                <Package size={14} /> Columnas: {metricas.colUds}
              </div>
              {sinMano > 0 && (
                <button
                  onClick={() => fijarTodasManos('D')}
                  className="flex items-center gap-1 px-3 py-1 rounded-xl bg-accion-100 text-accion-900 border border-accion-300 font-black text-xs hover:bg-accion-200 transition-colors animate-pulse"
                >
                  <AlertTriangle size={14} className="text-aviso-600" /> {sinMano} sin mano · Fijar Dcha
                </button>
              )}
            </div>
          </div>

          {/* Buscador predictivo en vivo */}
          <div className="relative">
            <div className="flex items-center gap-2">
              <div className="relative flex-1">
                <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  value={busca}
                  onChange={e => setBusca(e.target.value)}
                  onFocus={() => setFoco(true)}
                  onKeyDown={e => {
                    if (!sugerencias.length) { if (e.key === 'Enter') añadirTexto(busca); return; }
                    if (e.key === 'ArrowDown') { e.preventDefault(); setSel(s => (s + 1) % sugerencias.length); }
                    else if (e.key === 'ArrowUp') { e.preventDefault(); setSel(s => (s - 1 + sugerencias.length) % sugerencias.length); }
                    else if (e.key === 'Enter') { e.preventDefault(); añadirSugerencia(sugerencias[sel]); }
                    else if (e.key === 'Escape') { setFoco(false); }
                  }}
                  placeholder="Escribe un código o descripción (ej.: 1 b60i, asc60d, fregadero 60, col60, 2 gavetero 80)…"
                  className="w-full pl-11 pr-4 py-3 rounded-2xl border border-slate-200 text-sm font-medium focus:border-accion-500 focus:ring-2 focus:ring-accion-100 outline-none transition-all shadow-inner bg-slate-50/50"
                />
                {buscando && <Loader size={18} className="absolute right-4 top-1/2 -translate-y-1/2 text-dato-600 animate-spin" />}
              </div>
              <button
                onClick={() => añadirTexto(busca)}
                disabled={!busca.trim() || buscando}
                className="px-6 py-3 rounded-2xl bg-accion-600 hover:bg-accion-700 disabled:opacity-50 text-white font-bold text-sm shadow-md transition-all flex items-center gap-2"
              >
                {buscando
                  ? <><Loader size={18} className="animate-spin" /> Añadiendo…</>
                  : <><Plus size={18} /> Añadir Mueble</>}
              </button>
            </div>

            {/* Desplegable de Sugerencias */}
            {foco && sugerencias.length > 0 && (
              <div className="absolute left-0 right-0 top-full mt-2 bg-white border border-slate-200 rounded-2xl shadow-2xl z-30 max-h-80 overflow-y-auto divide-y divide-slate-100">
                {sugerencias.map((c, i) => (
                  <button
                    key={c.cod}
                    type="button"
                    onClick={() => añadirSugerencia(c)}
                    className={`w-full px-5 py-2.5 text-left flex items-center justify-between gap-3 text-xs transition-colors ${i === sel ? 'bg-accion-50 text-accion-900 font-bold' : 'hover:bg-slate-50'}`}
                  >
                    <div className="flex items-center gap-3">
                      <span className="font-mono font-black text-indigo-600 text-sm">{c.cod}</span>
                      <span className="text-slate-700 font-medium">{c.etiqueta}</span>
                      {c.ancho && <span className="px-2 py-0.5 rounded-md bg-slate-100 text-[10px] text-slate-500 font-bold">{c.ancho} cm</span>}
                    </div>
                    <span className="font-mono font-black text-slate-900">{c.precio ? `${c.precio.desde ? 'desde ' : ''}${eur(c.precio.eur)}` : '—'}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Paleta Rápida por Chips */}
          <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
            <span className="text-[10px] font-black text-slate-400 uppercase shrink-0">Atajos rápidos:</span>
            {PALETA_RAPIDA.map(grp => (
              <div key={grp.grupo} className="flex items-center gap-1 bg-slate-100/70 p-1 rounded-xl shrink-0">
                <span className="text-[9px] font-black text-slate-400 uppercase px-1.5">{grp.grupo}:</span>
                {grp.items.map(it => (
                  <button
                    key={it.label}
                    onClick={() => añadirTexto(it.expr)}
                    className="px-2.5 py-1 rounded-lg bg-white border border-slate-200 hover:border-accion-400 hover:text-accion-600 font-bold text-xs text-slate-700 shadow-2xs transition-all"
                    title={it.desc}
                  >
                    + {it.label}
                  </button>
                ))}
              </div>
            ))}
          </div>
        </div>

        {/* Pestañas de Filtro y Botón WhatsApp */}
        <div className="px-6 pt-3 bg-slate-50/50 border-b border-slate-100 flex items-center justify-between gap-4 flex-wrap">
          {/* La fila de pestañas mide 428 px: en un móvil de 390 la última se
              queda fuera. Con `min-w-0` puede encogerse (un hijo de flex trae
              `min-width: auto` y se niega) y con `overflow-x-auto` se desliza. */}
          <div className="flex gap-1 border-b border-slate-200 -mb-[1px] min-w-0 max-w-full overflow-x-auto [&>*]:shrink-0">
            {['TODOS', 'BAJOS', 'ALTOS', 'COLUMNAS', 'LINEALES'].map(cat => (
              <button
                key={cat}
                onClick={() => setFiltroCat(cat)}
                className={`px-4 py-2 border-b-2 font-black text-xs transition-all ${filtroCat === cat ? 'border-accion-600 text-accion-600' : 'border-transparent text-slate-400 hover:text-slate-700'}`}
              >
                {cat} {cat === 'TODOS' ? `(${muebles.length})` : ''}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-2 pb-2">
            <button
              onClick={copiarParaWhatsApp}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all border ${copiadoWs ? 'bg-accion-600 text-white border-accion-600' : 'bg-accion-50 text-accion-800 border-accion-200 hover:bg-accion-100'}`}
            >
              {copiadoWs ? <Check size={14} /> : <Copy size={14} />} {copiadoWs ? '¡Copiado para WhatsApp!' : 'Copiar WhatsApp'}
            </button>
          </div>
        </div>

        {/* Tabla de Muebles */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 divide-y divide-slate-100 min-h-[300px]">
          {/* MIENTRAS SE BUSCA NO SE ENSEÑA EL VACÍO.
              Añadir un mueble va al servidor y tarda cerca de un segundo. En
              ese rato la pantalla entera decía «No hay muebles añadidos», con
              un girito diminuto dentro del buscador que en una tablet no se ve.
              El master, dos veces: «tarda un poco, como un segundo, y se queda
              la pantalla en blanco; da mala imagen». No estaba rota: estaba
              enseñando un hueco. Ahora ese rato se ocupa con la fila que está a
              punto de llegar. */}
          {buscando && filasFiltradas.length === 0 ? (
            <div className="py-16 space-y-3" aria-live="polite">
              <p className="text-center text-sm font-bold text-dato-600">
                Buscando {busca.trim() ? <span className="font-mono">«{busca.trim()}»</span> : 'el mueble'}…
              </p>
              {[0, 1].map(i => (
                <div key={i}
                  className="rounded-xl border border-slate-200 bg-slate-50/70 p-4 animate-pulse"
                  style={{ animationDelay: `${i * 140}ms` }}>
                  <div className="h-3 w-24 rounded bg-slate-200 mb-3" />
                  <div className="h-2.5 w-2/3 rounded bg-slate-200/80" />
                </div>
              ))}
            </div>
          ) : filasFiltradas.length === 0 ? (
            <div className="py-20 text-center text-slate-400 space-y-3">
              <Package size={48} className="mx-auto text-dato-300 opacity-60" />
              <p className="text-base font-bold text-dato-600">No hay muebles añadidos en este presupuesto</p>
              <p className="text-xs max-w-md mx-auto">
                Escribe en el buscador superior (ej: <code>1 b60i</code>, <code>asc60d</code>, <code>fregadero 60</code>) o usa el botón <b>Pegado Masivo</b>.
              </p>
            </div>
          ) : (
            <>
            {/* ─── FICHAS: hasta `lg`. La tabla NO cabe y no hay forma de que
                 quepa. Con el candado abierto son 13 columnas: medidos 851 px
                 de tabla en un hueco de 693 en una tablet de 8,6", y en un
                 móvil de 390 ni eso. Se podía arrastrar de lado, pero leer
                 códigos arrastrando no es manejable — el master, 25/08: «muy
                 intuitiva y muy facilona de manejar».

                 Cada mueble es una ficha con el CÓDIGO grande, que es lo que se
                 lee de verdad, y los controles con el dedo en mente. En `lg`
                 para arriba vuelve la tabla, que ahí sí cabe y se compara mejor
                 en vertical. */}
            <div className="lg:hidden space-y-2.5">
              {filasFiltradas.map((m, idx) => {
                const opcionesAlt = alturasDe(m);
                const opcionesAnc = anchosDe(m);
                const tieneMano = manoDe(m.cod);
                return (
                  <div key={m._k} className="rounded-2xl border border-slate-200 bg-white p-3 shadow-xs">
                    {/* Cabecera de la ficha: nº, código y borrar */}
                    <div className="flex items-start gap-2">
                      <span className="mt-0.5 shrink-0 w-6 h-6 rounded-lg bg-slate-100 text-slate-500 text-[11px] font-black flex items-center justify-center">
                        {idx + 1}
                      </span>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-1.5 flex-wrap">
                          <span className="font-mono font-black text-indigo-700 text-lg leading-none">{m.cod}</span>
                          {!m.encontrado && (
                            <span className="px-1.5 py-0.5 rounded bg-rose-100 text-rose-700 font-bold text-[9px]">Manual</span>
                          )}
                        </div>
                        <input
                          type="text"
                          value={m.desc ?? ''}
                          onChange={e => setDesc(m._k, e.target.value)}
                          placeholder={m.familia?.replace(/_/g, ' ') || m.tipo || 'Mueble'}
                          title={`Descripción de la línea. Vacío = «${m.familia?.replace(/_/g, ' ') || m.tipo || 'Mueble'}», que es la familia de tarifa y NO cambia al escribir aquí.`}
                          className={`mt-0.5 w-full px-1.5 py-0.5 rounded-lg border font-bold text-[11px] outline-none transition-all ${
                            (m.desc || '').trim()
                              ? 'border-slate-300 bg-white text-slate-700'
                              : 'border-transparent bg-transparent text-slate-600 hover:border-slate-200 focus:border-indigo-400 focus:bg-white placeholder:text-slate-600 placeholder:font-bold'
                          }`}
                        />
                      </div>
                      <button type="button" onClick={() => quitar(m._k)}
                        title="Quitar este mueble"
                        className="shrink-0 p-2 rounded-xl text-slate-300 hover:text-error-600 hover:bg-error-50">
                        <Trash2 size={18} />
                      </button>
                    </div>

                    {/* Medidas y mano */}
                    <div className="mt-2.5 flex items-center gap-2 flex-wrap text-[11px]">
                      {opcionesAnc ? (
                        /* Costados, laterales y regletas: la tarifa va por ANCHO
                           de la pieza. Antes aquí ponía «ancho —» y el alto se
                           elegía en un desplegable — justo al revés. */
                        <>
                          <label className="flex items-center gap-1">
                            <span className="text-slate-400 font-bold">Tarifa</span>
                            <select value={m.anchoTarifa || opcionesAnc[0]}
                              onChange={e => setAnchoTarifa(m._k, e.target.value)}
                              title="El escalón que decide el PRECIO de la pieza"
                              className="px-2 py-1.5 rounded-lg border border-slate-200 bg-white font-bold text-slate-800 text-xs">
                              {opcionesAnc.map(a => <option key={a} value={a}>hasta {a} cm</option>)}
                            </select>
                          </label>
                          {/* LA MEDIDA DE VERDAD. El escalón de arriba dice lo que
                              cuesta; esto es lo que se fabrica y lo que va al
                              pedido. Cambiarlo NO mueve el precio a propósito. */}
                          <label className="flex items-center gap-1">
                            <span className="text-slate-400 font-bold">Ancho</span>
                            <input type="number" min="0" step="any" placeholder="cm"
                              value={m.anchoReal ?? ''}
                              onChange={e => setMedidaReal(m._k, 'anchoReal', e.target.value)}
                              title="Ancho definitivo de la pieza. No cambia el precio: eso lo decide la tarifa de al lado."
                              data-testid="medida-ancho-real"
                              className="w-16 px-2 py-1.5 rounded-lg border border-slate-200 bg-white font-bold text-slate-800 text-xs" />
                          </label>
                          <label className="flex items-center gap-1">
                            <span className="text-slate-400 font-bold">Alto</span>
                            <input type="number" min="0" step="any" placeholder="cm"
                              value={m.altoReal ?? ''}
                              onChange={e => setMedidaReal(m._k, 'altoReal', e.target.value)}
                              title="Alto definitivo de la pieza. No cambia el precio."
                              data-testid="medida-alto-real"
                              className="w-16 px-2 py-1.5 rounded-lg border border-slate-200 bg-white font-bold text-slate-800 text-xs" />
                          </label>
                        </>
                      ) : (
                        <span className="px-2 py-1 rounded-lg bg-slate-100 font-bold text-slate-700">
                          {m.ancho ? `${m.ancho} cm de ancho` : 'ancho —'}
                        </span>
                      )}
                      {opcionesAnc ? null : opcionesAlt ? (
                        <label className="flex items-center gap-1">
                          <span className="text-slate-400 font-bold">Alto</span>
                          <select value={m.alto || opcionesAlt[0]} onChange={e => setAlto(m._k, e.target.value)}
                            className="px-2 py-1.5 rounded-lg border border-slate-200 bg-white font-bold text-slate-800 text-xs">
                            {opcionesAlt.map(a => <option key={a} value={a}>{a} cm</option>)}
                          </select>
                        </label>
                      ) : (
                        <span className="px-2 py-1 rounded-lg bg-slate-100 font-bold text-slate-700">
                          {m.alto ? `${m.alto} cm de alto` : 'alto —'}
                        </span>
                      )}
                      {tieneMano !== undefined && (
                        <button type="button" onClick={() => rotarMano(m._k)}
                          title="Cambiar la mano de apertura"
                          className={`px-2.5 py-1.5 rounded-lg font-black text-[11px] ${
                            tieneMano === 'D' ? 'bg-accion-100 text-accion-800 border border-accion-300' :
                            tieneMano === 'I' ? 'bg-accion-100 text-accion-800 border border-accion-300' :
                            'bg-accion-100 text-accion-900 border border-accion-300 animate-pulse'
                          }`}>
                          {tieneMano === 'D' ? '▶ Dcha' : tieneMano === 'I' ? '◀ Izq' : '⚠️ Sin mano'}
                        </button>
                      )}
                    </div>

                    {/* Cantidad e importes */}
                    <div className="mt-2.5 flex items-center justify-between gap-3 flex-wrap">
                      <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-xl">
                        <button type="button" onClick={() => setQty(m._k, -1, true)}
                          aria-label="Quitar una unidad"
                          className="w-10 h-10 rounded-lg bg-white hover:bg-slate-200 text-slate-700 font-black text-lg flex items-center justify-center shadow-2xs">
                          −
                        </button>
                        <input type="number" min="1" value={m.qty} onChange={e => setQty(m._k, e.target.value)}
                          aria-label="Unidades"
                          className="w-12 text-center bg-transparent font-black text-slate-900 text-base outline-none" />
                        <button type="button" onClick={() => setQty(m._k, 1, true)}
                          aria-label="Añadir una unidad"
                          className="w-10 h-10 rounded-lg bg-white hover:bg-slate-200 text-slate-700 font-black text-lg flex items-center justify-center shadow-2xs">
                          +
                        </button>
                      </div>
                      <div className="text-right">
                        <div className="flex items-center justify-end gap-1 text-[10px] text-slate-400 font-bold">
                          <input type="number" min="0" step="any"
                            value={m.pvp ?? ''}
                            onChange={e => setPvp(m._k, e.target.value)}
                            title={m.pvpManual
                              ? 'Precio escrito a mano: manda sobre la tarifa. Bórralo para volver al de catálogo.'
                              : 'Precio de tarifa. Escribe encima para fijar uno pactado.'}
                            className={`w-20 px-1 py-0.5 rounded-lg border text-right font-mono font-bold text-[11px] outline-none ${
                              m.pvpManual
                                ? 'border-master-300 bg-master-50 text-master-800'
                                : 'border-transparent bg-transparent text-slate-500 hover:border-slate-200 focus:border-indigo-400 focus:bg-white'
                            }`} />
                          <span className="uppercase">{`€ × ${m.qty}`}</span>
                        </div>
                        <div className="font-mono font-black text-slate-900 text-lg leading-none">
                          {eur((Number(m.pvp) || 0) * (Number(m.qty) || 1))}
                        </div>
                      </div>
                    </div>

                    {/* Coste y margen: solo con el candado abierto */}
                    {verCoste && (
                      <div className="mt-2.5 flex items-center gap-2 flex-wrap text-[10px] font-mono border-t border-slate-100 pt-2">
                        {/* EL DESGLOSE TIENE QUE SUMAR EL TOTAL (master, 30/08:
                            «ojo, el coste no lo veo bien»). Se enseñaban dos de
                            los CUATRO sumandos —casco y puertas— y el total
                            llevaba además los herrajes y la mano de obra. En un
                            B90 eso eran 61,15 + 53,28 = 114,43 frente a un coste
                            de 145,55: 31,12 € que aparecían de la nada. Un
                            desglose que no cuadra no es un desglose, es una
                            sospecha. */}
                        {/* SI HAY DESCUENTO DE COMPRA, SE DICE AQUI. Sin esto el
                            casco baja de 61,15 a 44,03 y no hay en pantalla
                            nada que lo explique: el desglose seguiria sumando
                            pero el numero pareceria mal leido. */}
                        <span className="text-dato-700 font-bold"
                          title={m.despiece?.dtoCascos > 0
                            ? `Tarifa ACB ${eur(m.despiece?.cascoTarifa)} − ${m.despiece?.dtoCascos}% de descuento de compra = ${eur(m.despiece?.casco)}`
                            : 'Coste neto del casco, tarifa ACB. Sin descuento de compra aplicado.'}>
                          {`Casco ${eur(m.despiece?.casco)}`}
                          {m.despiece?.dtoCascos > 0 && (
                            <span className="ml-1 text-[9px] font-black text-master-600">{`−${m.despiece.dtoCascos}%`}</span>
                          )}
                          {/* ACB NO FABRICA TODO EN TODAS LAS GAMAS. Si esta
                              familia no existe en el acabado elegido, el precio
                              sale de la gama en la que SÍ se fabrica: es tarifa
                              de verdad, pero no la del acabado pedido, y quien
                              presupuesta tiene que verlo antes de fijar precio. */}
                          {m.despiece?.cascoOtroAcabado && (
                            <span data-testid="cm3-marca-otra-gama"
                              className="ml-1 text-[9px] font-black text-aviso-600"
                              title={`No se fabrica en el acabado elegido. Precio de tarifa de la gama «${m.despiece.cascoGama}» (${m.despiece.cascoOtroAcabado}).`}>
                              otra gama
                            </span>
                          )}
                          {m.despiece?.cascoSinPrecio && (
                            <span data-testid="cm3-marca-sin-tarifa"
                              className="ml-1 text-[9px] font-black text-error-600"
                              title="Este casco no está en la tarifa ACB. No se puede dar un coste, y por eso esta línea no entra en el margen.">
                              sin tarifa
                            </span>
                          )}
                        </span>
                        <span className="text-dato-700 font-bold">{`Puertas ${eur(m.despiece?.puerta)}`}</span>
                        <span className="text-dato-700 font-bold"
                          title={`Bisagras ${eur(m.despiece?.bisagras)} · Patas ${eur(m.despiece?.patas)} · Colgadores ${eur(m.despiece?.colg)} · Cajones ${eur(m.despiece?.caj)} · Gavetas ${eur(m.despiece?.gav)} · Soportes ${eur(m.despiece?.soportes)}`}>
                          {`Herrajes ${eur(herrajesDe(m))}`}
                        </span>
                        {/* La mano de obra por mueble ES la comisión del
                            montador (CLAUDE.md, regla 16). Va dentro del coste
                            de fábrica, así que tiene que verse. */}
                        <span className="text-dato-700 font-bold"
                          title="Mano de obra por mueble montado: la misma cifra que cobra el montador.">
                          {`M. obra ${eur(m.despiece?.mo)}`}
                        </span>
                        <span className="text-dato-900 font-black">{`Coste ${eur(m.coste)}`}</span>
                        <span className="text-dato-600 font-bold">
                          {m.margenPct == null
                            ? 'Margen — (sin coste de casco)'
                            : `Margen ${eur(m.margen)} (${m.margenPct.toFixed(1)}%)`}
                        </span>
                      </div>
                    )}

                    {/* Observaciones, a lo ancho: es donde se escribe de verdad */}
                    <input type="text" value={m.obs || ''} onChange={e => setObs(m._k, e.target.value)}
                      placeholder="✎ Observaciones / características especiales…"
                      title="Características especiales, cajeados de pilar, accesorios interiores o notas para taller"
                      className={`mt-2.5 w-full px-2.5 py-2 rounded-xl border text-[11px] outline-none transition-all ${
                        m.obs?.trim()
                          ? 'border-amber-400 bg-amber-50/70 font-bold text-amber-900 ring-1 ring-amber-300'
                          : 'border-slate-200 bg-slate-50/60 text-slate-500 focus:bg-white focus:border-indigo-400'
                      }`} />
                  </div>
                );
              })}
            </div>

            <table className="hidden lg:table w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-200 text-[10px] font-black uppercase text-slate-400">
                  <th className="py-2.5 px-2 text-center w-10">#</th>
                  <th className="py-2.5 px-3 text-center w-28">Cantidad</th>
                  <th className="py-2.5 px-3">Código</th>
                  <th className="py-2.5 px-3">Descripción / Familia</th>
                  <th className="py-2.5 px-3 text-center">Ancho</th>
                  <th className="py-2.5 px-3 text-center">Alto</th>
                  <th className="py-2.5 px-3 text-center">Mano</th>
                  <th className="py-2.5 px-3 text-right">PVP Ud.</th>
                  <th className="py-2.5 px-3 text-right">Total</th>
                  <th className="py-2.5 px-2 text-center w-10"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filasFiltradas.map((m, idx) => {
                  const opcionesAlt = alturasDe(m);
                  const opcionesAnc = anchosDe(m);
                  const tieneMano = manoDe(m.cod);
                  return (
                    <tr key={m._k} className="hover:bg-slate-50/80 transition-colors group">
                      <td className="py-3 px-2 text-center font-bold text-slate-400">{idx + 1}</td>
                      
                      {/* Cantidad con +/- */}
                      <td className="py-3 px-3">
                        <div className="flex items-center justify-center gap-1 bg-slate-100 p-0.5 rounded-xl w-fit mx-auto">
                          <button
                            type="button"
                            onClick={() => setQty(m._k, -1, true)}
                            className="w-6 h-6 rounded-lg bg-white hover:bg-slate-200 text-slate-700 font-bold flex items-center justify-center shadow-2xs"
                          >
                            -
                          </button>
                          <input
                            type="number"
                            min="1"
                            value={m.qty}
                            onChange={e => setQty(m._k, e.target.value)}
                            className="w-8 text-center bg-transparent font-black text-slate-900 outline-none"
                          />
                          <button
                            type="button"
                            onClick={() => setQty(m._k, 1, true)}
                            className="w-6 h-6 rounded-lg bg-white hover:bg-slate-200 text-slate-700 font-bold flex items-center justify-center shadow-2xs"
                          >
                            +
                          </button>
                        </div>
                      </td>

                      {/* Código */}
                      <td className="py-3 px-3">
                        <div className="flex items-center gap-1.5">
                          <span className="font-mono font-black text-indigo-700 text-sm">{m.cod}</span>
                          {!m.encontrado && (
                            <span className="px-1.5 py-0.5 rounded bg-rose-100 text-rose-700 font-bold text-[9px]">Manual</span>
                          )}
                        </div>
                      </td>

                      {/* Familia / Descripción + Línea de Observaciones / Características especiales */}
                      <td className="py-3 px-3 min-w-[220px]">
                        {/* LA DESCRIPCIÓN, EDITABLE (master, 31/08). Se escribe
                            APARTE de la familia: la familia decide el despiece,
                            el coste y si la línea comisiona, así que renombrar
                            no puede cambiarla. Vacío = la familia de siempre. */}
                        <input
                          type="text"
                          value={m.desc ?? ''}
                          onChange={e => setDesc(m._k, e.target.value)}
                          placeholder={descDe({ ...m, desc: '' })}
                          title={`Descripción de la línea. Vacío = «${descDe({ ...m, desc: '' })}», que es la familia de tarifa y NO cambia al escribir aquí.`}
                          data-testid="cm3-desc-linea"
                          className={`w-full px-1.5 py-0.5 rounded-lg border text-xs font-bold outline-none transition-all ${
                            (m.desc || '').trim()
                              ? 'border-slate-300 bg-white text-slate-800'
                              : 'border-transparent bg-transparent text-slate-800 hover:border-slate-200 focus:border-indigo-400 focus:bg-white placeholder:text-slate-800 placeholder:font-bold'
                          }`}
                        />
                        {/* Línea de Observaciones / Características Especiales del Mueble */}
                        <div className="mt-1 flex items-center gap-1">
                          <input
                            type="text"
                            value={m.obs || ''}
                            onChange={e => setObs(m._k, e.target.value)}
                            placeholder="✎ Observaciones / características especiales…"
                            title="Escribe aquí características especiales, cajeados de pilar, accesorios interiores o notas para taller"
                            className={`w-full px-2 py-1 rounded-lg border text-[11px] outline-none transition-all ${
                              m.obs?.trim()
                                ? 'border-amber-400 bg-amber-50/70 font-bold text-amber-900 shadow-xs ring-1 ring-amber-300'
                                : 'border-slate-200 bg-slate-50/60 text-slate-500 hover:bg-white focus:bg-white focus:border-indigo-400'
                            }`}
                          />
                        </div>
                      </td>

                      {/* Ancho. En costados/laterales/regletas la tarifa va por
                          ANCHO de la pieza, así que aquí se ELIGE en vez de
                          enseñar un guion. */}
                      <td className="py-3 px-3 text-center font-bold text-slate-700">
                        {opcionesAnc ? (
                          <div className="flex flex-col items-center gap-1">
                            <select
                              value={m.anchoTarifa || opcionesAnc[0]}
                              onChange={e => setAnchoTarifa(m._k, e.target.value)}
                              title="El escalón que decide el PRECIO"
                              className="px-2 py-1 rounded-lg border border-slate-200 bg-white font-bold text-slate-800 text-xs outline-none focus:border-dato-400"
                            >
                              {opcionesAnc.map(a => <option key={a} value={a}>hasta {a} cm</option>)}
                            </select>
                            <input type="number" min="0" step="any" placeholder="cm reales"
                              value={m.anchoReal ?? ''}
                              onChange={e => setMedidaReal(m._k, 'anchoReal', e.target.value)}
                              title="Ancho definitivo. No cambia el precio."
                              className="w-20 px-2 py-1 rounded-lg border border-slate-200 bg-white font-bold text-slate-800 text-[11px] outline-none focus:border-dato-400" />
                          </div>
                        ) : (
                          <input type="number" min="0" step="any" placeholder="—"
                            value={m.ancho ?? ''}
                            onChange={e => setMedidaMueble(m._k, 'ancho', e.target.value)}
                            title="Ancho de fabricación, en cm. No cambia el precio: el de un mueble MV sale de su código."
                            data-testid="cm3-ancho-linea"
                            className="w-16 px-1.5 py-1 rounded-lg border border-transparent bg-transparent text-center font-bold text-slate-700 text-xs outline-none hover:border-slate-200 focus:border-indigo-400 focus:bg-white" />
                        )}
                      </td>

                      {/* Alto */}
                      <td className="py-3 px-3 text-center">
                        {opcionesAnc ? (
                          /* El TIPO de costado (de alto, de bajo, de columna…)
                             sigue fijando su precio, pero el alto de verdad se
                             escribe y se graba: master, 28/08 —«en los costados
                             bajos y altos también se debe poder cambiar la
                             medida, tanto de ancho como de alto, en todos»—. */
                          <input type="number" min="0" step="any" placeholder="cm reales"
                            value={m.altoReal ?? ''}
                            onChange={e => setMedidaReal(m._k, 'altoReal', e.target.value)}
                            title="Alto definitivo. No cambia el precio."
                            className="w-20 px-2 py-1 rounded-lg border border-slate-200 bg-white font-bold text-slate-800 text-[11px] outline-none focus:border-dato-400" />
                        ) : opcionesAlt ? (
                          <select
                            value={m.alto || opcionesAlt[0]}
                            onChange={e => setAlto(m._k, e.target.value)}
                            className="px-2 py-1 rounded-lg border border-slate-200 bg-white font-bold text-slate-800 text-xs outline-none focus:border-dato-400"
                          >
                            {opcionesAlt.map(a => <option key={a} value={a}>{a} cm</option>)}
                          </select>
                        ) : (
                          <span className="font-bold text-slate-700">{m.alto ? `${m.alto} cm` : '—'}</span>
                        )}
                      </td>

                      {/* Mano de apertura con botón interactivo */}
                      <td className="py-3 px-3 text-center">
                        {tieneMano !== undefined ? (
                          <button
                            type="button"
                            onClick={() => rotarMano(m._k)}
                            className={`px-2.5 py-1 rounded-lg font-black text-[11px] transition-all flex items-center gap-1 mx-auto ${
                              tieneMano === 'D' ? 'bg-accion-100 text-accion-800 border border-accion-300' :
                              tieneMano === 'I' ? 'bg-accion-100 text-accion-800 border border-accion-300' :
                              'bg-accion-100 text-accion-900 border border-accion-300 animate-pulse'
                            }`}
                          >
                            {tieneMano === 'D' ? '▶ Dcha' : tieneMano === 'I' ? '◀ Izq' : '⚠️ Sin Mano'}
                          </button>
                        ) : (
                          <span className="text-slate-300 font-bold">—</span>
                        )}
                      </td>

                      {/* Coste y Margen (candado) */}

                      {/* PVP */}
                      {/* EL PVP, A MANO. En cuanto se toca, ni cambiar el alto
                          ni el ancho pueden volver a pisarlo (ver `setPvp`):
                          un precio pactado que vuelve al de tarifa en silencio
                          saca el presupuesto por otra cifra sin dar un error.
                          Dejarlo vacío devuelve la línea a la tarifa. */}
                      <td className="py-3 px-3 text-right">
                        <div className="flex items-center justify-end gap-1">
                          <input type="number" min="0" step="any"
                            value={m.pvp ?? ''}
                            onChange={e => setPvp(m._k, e.target.value)}
                            title={m.pvpManual
                              ? 'Precio escrito a mano: manda sobre la tarifa. Bórralo para volver al precio de catálogo.'
                              : 'Precio de tarifa. Escribe encima para fijar uno pactado.'}
                            data-testid="cm3-pvp-linea"
                            className={`w-24 px-1.5 py-1 rounded-lg border text-right font-mono font-bold text-sm outline-none transition-all ${
                              m.pvpManual
                                ? 'border-master-300 bg-master-50 text-master-800'
                                : 'border-transparent bg-transparent text-slate-700 hover:border-slate-200 focus:border-indigo-400 focus:bg-white'
                            }`} />
                          <span className="text-[10px] text-slate-400">€</span>
                        </div>
                        {m.pvpManual && (
                          <div className="text-[9px] font-black text-master-600 text-right pr-3 leading-none mt-0.5">a mano</div>
                        )}
                      </td>
                      <td className="py-3 px-3 text-right font-mono font-black text-slate-900 text-sm">
                        {eur((Number(m.pvp) || 0) * (Number(m.qty) || 1))}
                      </td>

                      {/* Eliminar */}
                      <td className="py-3 px-2 text-center">
                        <button
                          type="button"
                          onClick={() => quitar(m._k)}
                          className="p-1.5 rounded-lg text-slate-300 hover:text-error-600 hover:bg-error-50 transition-colors"
                          title="Eliminar fila"
                        >
                          <Trash2 size={16} />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            </>
          )}
        </div>

        {/* ─────────── EL PANEL DE COSTES ───────────
            El master, 31/08: «no me gusta este sistema de ver costos, me
            gustaba más la pantalla anterior», y al elegir: los costes FUERA de
            la tabla, en un panel aparte.

            Y tiene razón por lo que se ve en su pantallazo: el candado metía
            SEIS columnas más en la tabla, de modo que la cabecera se salía y
            el PVP —que es lo que se mira para vender— quedaba arrinconado
            contra el borde. La tabla es la que se enseña con un cliente
            delante; el coste es otra conversación y va en otro sitio.

            El desglose por línea vive AQUÍ, y la tabla de arriba se queda
            siempre igual: con el candado echado o abierto, las mismas columnas
            en el mismo sitio. */}
        {verCoste && (() => {
          const otraGama = filas.filter(m => m.despiece?.cascoOtroAcabado);
          const gamas = [...new Set(otraGama.map(m => m.despiece.cascoGama))];
          const familiasSin = [...new Set(sinCoste.map(m => m.familia || '?'))];
          return (
            <div data-testid="cm3-panel-costes" className="border-t border-slate-200 bg-slate-50/70">
              <div className="px-6 pt-4 pb-2 flex items-center gap-2">
                <span className="text-[11px] font-black uppercase tracking-widest text-master-700">
                  Coste de fábrica por línea
                </span>
                <span className="text-[10px] text-slate-400">
                  · interno, no sale en el PDF del cliente
                </span>
              </div>

              <div className="px-6 pb-4 overflow-x-auto">
                <table className="w-full text-[11px]">
                  <thead className="text-slate-400">
                    <tr className="border-b border-slate-200">
                      <th className="text-left py-1.5 pr-3 font-black uppercase">#</th>
                      <th className="text-left py-1.5 pr-3 font-black uppercase">Código</th>
                      <th className="text-right py-1.5 px-2 font-black uppercase">Casco</th>
                      <th className="text-right py-1.5 px-2 font-black uppercase">Puertas</th>
                      <th className="text-right py-1.5 px-2 font-black uppercase">Herrajes</th>
                      <th className="text-right py-1.5 px-2 font-black uppercase" title="Mano de obra por mueble montado: la misma cifra que cobra el montador.">M. obra</th>
                      <th className="text-right py-1.5 px-2 font-black uppercase">Coste ud.</th>
                      <th className="text-right py-1.5 px-2 font-black uppercase">PVP ud.</th>
                      <th className="text-right py-1.5 pl-2 font-black uppercase">Margen</th>
                    </tr>
                  </thead>
                  <tbody className="font-mono">
                    {filas.map((m, i) => (
                      <tr key={m._k} className={`border-b border-slate-100 ${m.coste == null ? 'bg-aviso-50/60' : ''}`}>
                        <td className="py-1.5 pr-3 text-slate-400">{i + 1}</td>
                        <td className="py-1.5 pr-3 font-black text-indigo-700">
                          {m.cod}
                          {m.qty > 1 && <span className="ml-1 text-slate-400 font-bold">×{m.qty}</span>}
                        </td>
                        {m.coste == null ? (
                          <td colSpan={5} className="py-1.5 px-2 text-aviso-800 font-sans font-bold">
                            Sin coste — el despiece no conoce «{m.familia || m.tipo || '?'}»
                          </td>
                        ) : (
                          <>
                            <td className="py-1.5 px-2 text-right text-dato-700"
                              title={m.despiece?.cascoOtroAcabado
                                ? `Tarifa de la gama «${m.despiece.cascoGama}»: no se fabrica en el acabado elegido.`
                                : `Tarifa ACB${m.despiece?.dtoCascos > 0 ? ` − ${m.despiece.dtoCascos}% de descuento de compra` : ''}.`}>
                              {eur(m.despiece?.casco)}
                              {m.despiece?.cascoOtroAcabado && (
                                <span data-testid="cm3-marca-otra-gama" className="ml-1 text-[9px] font-black text-aviso-600">otra gama</span>
                              )}
                              {m.despiece?.dtoCascos > 0 && (
                                <span className="ml-1 text-[9px] font-black text-master-600">{`−${m.despiece.dtoCascos}%`}</span>
                              )}
                            </td>
                            <td className="py-1.5 px-2 text-right text-dato-700"
                              title={`${(m.despiece?.puertasDetalle || []).map(fr => `${fr.desc} [${fr.puntos} pts]`).join(' + ') || '0 frentes'} · ${m.despiece?.dtoPuertas || 0}% dto.`}>
                              {eur(m.despiece?.puerta)}
                            </td>
                            <td className="py-1.5 px-2 text-right text-dato-700"
                              title={`Bisagras ${eur(m.despiece?.bisagras)} · Patas ${eur(m.despiece?.patas)} · Colgadores ${eur(m.despiece?.colg)} · Cajones ${eur(m.despiece?.caj)} · Gavetas ${eur(m.despiece?.gav)} · Soportes ${eur(m.despiece?.soportes)}`}>
                              {eur(herrajesDe(m))}
                            </td>
                            <td className="py-1.5 px-2 text-right text-dato-700">{eur(m.despiece?.mo)}</td>
                            <td className="py-1.5 px-2 text-right text-dato-900 font-black">{eur(m.coste)}</td>
                          </>
                        )}
                        <td className="py-1.5 px-2 text-right text-slate-600">
                          {eur(m.pvp)}
                          {m.pvpManual && <span className="ml-1 text-[9px] font-black text-master-600">a mano</span>}
                        </td>
                        <td className="py-1.5 pl-2 text-right font-bold text-dato-600">
                          {m.margenPct == null
                            ? <span className="text-slate-300">—</span>
                            : <>{eur(m.margen)} <span className="text-[10px] text-emerald-500">({m.margenPct.toFixed(1)}%)</span></>}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* LOS AVISOS, JUNTOS Y AL PIE DEL PANEL. Marcar la fila no basta:
                  con veinte líneas nadie va contando cuáles llevan la marca, y
                  el que fija el precio mira el margen de abajo. */}
              {(sinCoste.length > 0 || otraGama.length > 0) && (
                <div data-testid="cm3-aviso-casco" className="px-6 py-3 bg-aviso-50 border-t border-aviso-200 text-[12px] text-aviso-900 space-y-1">
                  {sinCoste.length > 0 && (
                    <div>
                      <b>{sinCoste.length} línea{sinCoste.length === 1 ? '' : 's'} sin coste.</b>{' '}
                      El despiece no conoce {familiasSin.length === 1 ? 'la familia' : 'las familias'}{' '}
                      <span className="font-mono font-bold">{familiasSin.join(', ')}</span>, así que
                      no se le pone precio de fábrica en vez de inventar uno. <b>No entra{sinCoste.length === 1 ? '' : 'n'} en
                      el coste ni en el margen de abajo</b>: el margen que ves es más alto
                      que el real.
                    </div>
                  )}
                  {otraGama.length > 0 && (
                    <div>
                      <b>{otraGama.length} línea{otraGama.length === 1 ? '' : 's'} con el
                      casco tarifado en otra gama.</b> ACB no fabrica{' '}
                      {otraGama.length === 1 ? 'ese mueble' : 'esos muebles'} en el acabado
                      elegido, así que el coste sale de{' '}
                      <span className="font-mono font-bold">{gamas.join(', ')}</span>. Es un
                      precio de tarifa de verdad, pero <b>no el del acabado que has
                      elegido</b>: confírmalo antes de fijar precio.
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })()}

        {/* Resumen Final de Importes */}
        <div className="p-6 bg-slate-50 border-t border-slate-200 flex items-center justify-between gap-6 flex-wrap">
          <div className="flex items-center gap-4">
            <button
              type="button"
              {...handlersCandado.props}
              onClick={(e) => {
                // La pulsación larga ya ha hecho lo suyo: el clic que manda el
                // navegador al soltar no puede deshacerlo en el mismo gesto.
                if (handlersCandado.consumir()) return;
                if (e.shiftKey) { setVerCoste(v => !v); setPistaCandado(''); return; }
                // Un toque corto no abre —para eso está el candado— pero SÍ
                // dice cómo se abre: un botón que no hace nada parece roto.
                setPistaCandado(AYUDA_CANDADO);
                setTimeout(() => setPistaCandado(''), 4000);
              }}
              data-testid="cm3-candado-coste"
              className={`p-2.5 rounded-2xl border transition-all ${verCoste ? 'bg-master-100 text-master-800 border-master-300' : 'bg-white text-slate-400 border-slate-200 hover:text-slate-700'}`}
              /* EL TÍTULO DECÍA SOLO «Shift + Clic», y en una tablet no hay
                 tecla Shift: el master lo preguntó porque parecía que el botón
                 no servía para nada. Se abre con PULSACIÓN LARGA, que es lo
                 que ya decía el texto de ayuda compartido; aquí faltaba. */
              title={`Coste de fábrica y margen. ${AYUDA_CANDADO}. Va escondido a propósito para poder enseñar esta pantalla con un cliente delante.`}
            >
              {verCoste ? <Unlock size={18} /> : <Lock size={18} />}
            </button>
            {pistaCandado && <span className="text-xs text-amber-600 font-bold animate-fade-in">{pistaCandado}</span>}
            
            {/* LA PUERTA DEL MODAL DE DESCUENTOS (master, 30/08: «falta el
                descuento de ACB que metía a mano»).

                El modal estaba escrito ENTERO —cabecera, campos, multiplicador
                neto y botón de aplicar— y `setShowModalDtos(true)` NO APARECIA
                EN NINGUN SITIO: no había forma de abrirlo. Es el mismo fallo
                que ya tuvo `AreaCooperativista`, y no da ningún error: la
                pantalla compila, el modal existe y simplemente no se abre nunca.

                Va DENTRO de `verCoste` a propósito: un descuento de compra es
                lo que le cuesta a la casa, y con el candado echado esta pantalla
                se enseña con un cliente delante (CLAUDE.md, reglas 5 y 9). */}
            {verCoste && (
              <>
                <button
                  type="button"
                  onClick={() => setShowModalDtos(true)}
                  data-testid="cm3-abrir-descuentos"
                  className="p-2.5 rounded-2xl border bg-white text-slate-500 border-slate-200 hover:text-master-700 hover:border-master-300 transition-all"
                  title="Descuentos de compra: cascos ACB y puertas MV. Es lo que la casa negocia con cada proveedor, no lo que ve el cliente."
                >
                  <Percent size={18} />
                </button>
                <div className="flex items-center gap-4 text-xs">
                  <div>Coste Fábrica: <b className="font-mono text-slate-800">{eur(totalCoste)}</b></div>
                  <div>Margen Bruto: <b className="font-mono text-dato-700">{eur(totalMargen)} ({totalMargenPct.toFixed(1)}%)</b></div>
                </div>
              </>
            )}
          </div>

          <div className="flex items-center gap-6">
            <div className="text-right space-y-0.5 text-xs text-slate-600">
              <div>Subtotal: <span className="font-mono font-bold text-slate-800">{eur(subtotalBruto)}</span></div>
              {descuento > 0 && <div className="text-dato-600 font-bold">Dto. ({descuento}%): -{eur(importeDescuento)}</div>}
              <div>Base Imponible: <span className="font-mono font-bold text-slate-800">{eur(baseImponible)}</span></div>
              <div>IVA ({ivaRate}%): <span className="font-mono font-bold text-slate-800">{eur(cuotaIva)}</span></div>
            </div>

            <div className="text-right pl-4 border-l border-slate-200">
              <span className="text-[10px] uppercase font-black text-slate-400 block">Total Final Presupuesto</span>
              <span className="text-2xl font-black text-dato-950 tracking-tight">{eur(totalPvp)}</span>
            </div>
          </div>
        </div>

      </div>

      {/* Modal de Pegado Masivo */}
      {showPegadoMasivo && (
        <div className="fixed inset-0 z-50 bg-slate-950/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl p-6 max-w-xl w-full space-y-4 shadow-2xl border border-slate-200 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FileUp size={22} className="text-dato-600" />
                <h3 className="text-lg font-black text-slate-900">Pegado Masivo de Relación</h3>
              </div>
              <button onClick={() => setShowPegadoMasivo(false)} className="p-1.5 rounded-xl hover:bg-slate-100 text-slate-400">
                <X size={20} />
              </button>
            </div>
            <p className="text-xs text-slate-500">
              Pega directamente la lista completa de muebles desde WhatsApp, correo electrónico o Word:
            </p>
            <textarea
              value={textoMasivo}
              onChange={e => setTextoMasivo(e.target.value)}
              placeholder={"1 b60i (altura 80)\n2 b45d\n1 asc60d\n1 columna horno 60\n2 gavetero 80\n1 col60"}
              rows={8}
              className="w-full p-4 rounded-2xl border border-slate-200 text-xs font-mono focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 outline-none resize-none bg-slate-50/50"
            />
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowPegadoMasivo(false)}
                className="px-4 py-2 rounded-xl border border-slate-200 text-xs font-bold text-slate-600 hover:bg-slate-50"
              >
                Cancelar
              </button>
              <button
                onClick={procesarPegadoMasivo}
                disabled={!textoMasivo.trim() || buscando}
                className="px-6 py-2.5 rounded-xl bg-accion-600 hover:bg-accion-700 text-white text-xs font-bold shadow-md disabled:opacity-50 flex items-center gap-2"
              >
                {buscando ? <Loader size={15} className="animate-spin" /> : <Plus size={15} />} Volcar Muebles a la Lista
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal de Descuentos Comerciales de Puertas en Cascada */}
      {showModalDtos && (
        <div className="fixed inset-0 z-50 bg-slate-950/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl p-6 max-w-md w-full space-y-4 shadow-2xl border border-slate-200 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="p-2 bg-amber-500/10 text-amber-600 rounded-xl border border-amber-500/20">
                  <Percent size={20} />
                </div>
                <div>
                  <h3 className="text-base font-black text-slate-900">Descuentos de Compra</h3>
                  <p className="text-[11px] text-slate-500">Lo que la casa negocia con cada proveedor: cascos ACB y puertas MV</p>
                </div>
              </div>
              <button onClick={() => setShowModalDtos(false)} className="p-1.5 rounded-xl hover:bg-slate-100 text-slate-400">
                <X size={20} />
              </button>
            </div>

            {/* EL DESCUENTO DE CASCOS ACB, QUE SE METIA A MANO (master, 30/08).
                Va SEPARADO de los de puertas y no en cascada con ellos: son dos
                proveedores distintos y dos tarifas distintas. Juntarlos haria
                que negociar con uno moviera el coste de lo que compra el otro. */}
            <div className="space-y-2 bg-master-50 p-4 rounded-2xl border border-master-200 text-xs">
              <div className="flex items-center gap-2 text-[11px] font-black text-master-800 uppercase tracking-wide">
                <Package size={13} /> Cascos ACB
              </div>
              <div>
                <label className="block text-slate-700 font-bold mb-1">
                  Descuento de compra sobre tarifa ACB (%):
                </label>
                <input
                  type="number"
                  step="any"
                  min="0"
                  max="100"
                  value={dtoCascos}
                  onChange={e => setDtoCascos(Math.min(100, Math.max(0, parseFloat(e.target.value) || 0)))}
                  data-testid="cm3-dto-cascos"
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 font-mono font-bold text-slate-800 bg-white focus:border-master-500 outline-none"
                  placeholder="0"
                />
                <p className="text-[10px] text-slate-500 mt-1">
                  Se aplica al COSTE del casco. El PVP de Cocina Desmontada no se
                  toca: lo que se negocia es lo que paga la casa, no lo que paga
                  el cliente.
                </p>
              </div>
            </div>

            <div className="space-y-3 bg-slate-50 p-4 rounded-2xl border border-slate-200 text-xs">
              <div className="flex items-center gap-2 text-[11px] font-black text-slate-700 uppercase tracking-wide">
                <Layers size={13} /> Puertas MV
              </div>
              <div>
                <label className="block text-slate-700 font-bold mb-1">
                  Descuento Principal 1 (%):
                </label>
                <input
                  type="number"
                  step="any"
                  min="0"
                  max="100"
                  value={dtoPuertas1}
                  onChange={e => setDtoPuertas1(parseFloat(e.target.value) || 0)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 font-mono font-bold text-slate-800 bg-white focus:border-indigo-500 outline-none"
                  placeholder="50"
                />
              </div>

              <div>
                <label className="block text-slate-700 font-bold mb-1">
                  Descuento en Cascada 2 (%) <span className="text-slate-400 font-normal">(Opcional)</span>:
                </label>
                <input
                  type="number"
                  step="any"
                  min="0"
                  max="100"
                  value={dtoPuertas2}
                  onChange={e => setDtoPuertas2(parseFloat(e.target.value) || 0)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 font-mono font-bold text-slate-800 bg-white focus:border-indigo-500 outline-none"
                  placeholder="0"
                />
              </div>

              <div className="pt-2 border-t border-slate-200 flex items-center justify-between font-bold text-slate-800">
                <span>Multiplicador Neto Total:</span>
                <span className="font-mono text-indigo-700 font-black">
                  {Math.round((1 - (1 - dtoPuertas1/100) * (1 - dtoPuertas2/100)) * 1000) / 10}% de descuento neto
                </span>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setShowModalDtos(false)}
                className="px-5 py-2.5 rounded-xl bg-accion-600 hover:bg-accion-700 text-white text-xs font-bold shadow-md flex items-center gap-2"
              >
                <Check size={14} /> Aplicar a Todas las Puertas
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal de revisión de muebles parseados desde PDF de Relación o Alvic */}
      {guardados !== null && (
        <div className="fixed inset-0 z-[80] bg-black/50 flex items-center justify-center p-4"
             onClick={() => setGuardados(null)}>
          <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full max-h-[80vh] flex flex-col"
               onClick={e => e.stopPropagation()}>
            <div className="px-5 py-4 border-b border-slate-200">
              <h3 className="text-base font-black text-slate-900">Presupuestos guardados</h3>
              <p className="text-xs text-dato-500 mt-0.5">
                Se abre tal como se guardó: muebles, acabados y tarifa.
              </p>
            </div>
            <div className="flex-1 overflow-y-auto p-3">
              {cargandoGuardados ? (
                <p className="text-sm text-dato-500 flex items-center gap-2 p-4">
                  <Loader size={15} className="animate-spin" /> Cargando…
                </p>
              ) : guardados.length === 0 ? (
                <p className="text-sm text-dato-500 p-4 text-center">
                  Todavía no hay ninguno guardado.
                </p>
              ) : guardados.map(o => (
                <button
                  key={o.id}
                  onClick={() => recuperar(o)}
                  className="w-full text-left px-4 py-3 rounded-xl hover:bg-slate-50 border border-slate-100 mb-2"
                >
                  <span className="block font-black text-sm text-slate-800">
                    {o.cliente || 'Sin cliente'}
                  </span>
                  <span className="block text-xs text-dato-500">
                    {o.ref || 'sin referencia'}
                    {' · '}
                    {(o.cm3?.muebles?.length || o.lines?.length || 0)} línea(s)
                    {o.createdAt ? ` · ${String(o.createdAt).slice(0, 10)}` : ''}
                  </span>
                </button>
              ))}
            </div>
            <div className="px-5 py-3 border-t border-slate-200 flex justify-end">
              <button onClick={() => setGuardados(null)}
                className="px-4 py-2 rounded-xl bg-slate-100 text-slate-600 font-bold text-sm hover:bg-slate-200">
                Cerrar
              </button>
            </div>
          </div>
        </div>
      )}

      {relacionRevisar && (
        <RelacionReview
          muebles={relacionRevisar}
          tarifa={tarifa}
          acabadoPuerta={acabadoPuerta}
          acabadoCasco={acabadoCasco}
          onClose={() => setRelacionRevisar(null)}
          apiUrl={API_URL}
          authHeaders={authHeaders}
          onConfirm={(mueblesActualizados) => {
            setMuebles(prev => fundir(prev, mueblesActualizados));
            setRelacionRevisar(null);
          }}
        />
      )}

    </div>
  );
}
