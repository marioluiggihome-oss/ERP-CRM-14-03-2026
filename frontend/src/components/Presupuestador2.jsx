import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import {
  Search, Plus, Minus, Trash2, ShoppingCart, Loader, Tag, Layers, X,
  Save, FileDown, Printer, Edit3, CheckCircle2, Receipt, Boxes, Sparkles, Scissors,
  PanelLeftClose, PanelLeftOpen, PanelRightClose, PanelRightOpen, ChevronDown, ChevronRight, ChevronUp,
  Globe, Ruler, Lock, Unlock, Library as LibraryIcon, ArrowUpDown, LayoutGrid, List,
  BookOpen, PackageCheck, Home, Maximize2, Minimize2
} from 'lucide-react';
import { authHeaders, librariesAPI, materialsAPI, settingsAPI, crmOpportunitiesAPI } from '../services/api';
import { generateBudgetPDF } from '../services/pdfGenerator';
import DespieceModal from './DespieceModal';
import ConfirmOrderModal from './ConfirmOrderModal';
import { MuebleIcon, classifyMueble, NOMENCLATURA, NOMENCLATURA_NOTAS } from './muebleIcons';
import { INITIAL_CARCASS_MATERIALS } from '../constants';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const eur = (n) => `${(Number(n) || 0).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} €`;

// Agrupa nombres de familia muy parecidos (p.ej. "PUERTA"/"PUERTAS",
// "LATERAL"/"LATERALES"/"LATERALES COLOR") bajo una misma cabecera para
// compactar la lista de categorías sin tocar los datos del catálogo.
// Familias PRINCIPALES del menú lateral, en el orden de negocio (sirve para MV y
// ZC). Cada categoría del catálogo cae en la PRIMERA que casa; lo no clasificado
// va a "Otros" al final para no perder nada. Las categorías reales quedan como
// SUBFAMILIAS dentro de cada principal.
const MAIN_FAMILY_DEFS = [
  { key: 'BAJOS',         label: '01 · Bajos',                       test: c => /^BAJO/.test(c) },
  { key: 'ALTOS',         label: '02 · Altos',                       test: c => /^(ALTO|ALTILLO|CAMPANA)/.test(c) && !/DECORATIV|VITRINA/.test(c) },
  { key: 'SEMICOLUMNAS',  label: '03 · Semicolumnas',                test: c => /^(MEDIA ?COLUMNA|SEMICOLUMNA|SEMI)/.test(c) },
  { key: 'COLUMNAS',      label: '04 · Columnas',                    test: c => /^COLUMNA/.test(c) },
  { key: 'SOBREENCIMERA', label: '05 · Sobreencimera',               test: c => /^SOBRE_?ENC/.test(c) || c === 'SOBRE' || c === 'ENCIMERA' },
  { key: 'SOBREMODULOS',  label: '06 · Sobremódulos',                test: c => /^SOBRE_?MODULO/.test(c) },
  { key: 'DECORATIVOS',   label: '07 · Muebles decorativos',         test: c => /DECORATIV|VITRINA/.test(c) },
  { key: 'COSTADOS',      label: '08 · Costados, regletas y baldas',  test: c => /^(COSTADO|REGLETA|BALDA|ESTANTE|LATERAL|TECHO|ZOCALO|CORNISA|PORTALUZ)/.test(c) },
  { key: 'ACCESORIOS',    label: '10 · Accesorios',                   test: c => /^(ACCESORIO|BOTELLERO|CESTO|CUBO|HERRAJE|PUERTA|REJILLA|GAVETERO)/.test(c) },
  { key: 'ELEMENTOS',     label: '11 · Elementos lineales',          test: c => /^(ELEMENTO|MOLDURA|REMATE|PERFIL|TIRADOR|PATA)/.test(c) },
  { key: 'ESTRUCTURAS',   label: '12 · Estructuras decorativas',     test: c => /^(ESTRUCTURA|PERGOLA|PANEL_DECOR|BANCO|MESA)/.test(c) },
];
const mainFamilyKeyOf = (category) => {
  // Normalizamos a MAYÚSCULAS y SIN tildes para que variantes como "SOBREMÓDULOS"
  // se agrupen igual que "SOBREMODULOS" (solo afecta a la agrupación, no al filtro).
  const c = String(category || '').toUpperCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  for (const d of MAIN_FAMILY_DEFS) { if (d.test(c)) return d.key; }
  return 'OTROS';
};

// Algunas categorías del catálogo MV son "bolsas mixtas" (MODULO, RINCON) que
// contienen muebles de familias DISTINTAS (p.ej. MODULO = baldas + regletas +
// media columnas + altillos…). Aquí re-categorizamos cada producto a su familia
// real según su NOMBRE/código, para que el árbol de familias quede bien acotado.
// No toca la BD: es una normalización al vuelo al cargar el catálogo.
const _norm = (s) => String(s || '').toUpperCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
const MIXED_CATEGORIES = new Set(['MODULO', 'RINCON']);
const normalizeCategory = (category, name, code) => {
  const cat = _norm(category).trim();
  if (!MIXED_CATEGORIES.has(cat)) return category; // solo tocamos las bolsas mixtas
  const n = _norm(name);
  const c = _norm(code);
  if (cat === 'RINCON') {
    if (/BAJO RINCON/.test(n) || /^BR/.test(c)) return 'BAJO_RINCON';
    if (/ALTO RINCON/.test(n) || /^AR/.test(c)) return 'ALTO_RINCON';
    return category;
  }
  // MODULO → por el tipo de elemento (nombre)
  if (/MEDIA ?COL|MEDIACOLUMNA/.test(n)) return 'MEDIA COLUMNA';
  if (/ALTILLO/.test(n) && /VITRINA/.test(n)) return 'ALTILLO_VITRINA';
  if (/^ALTILLO/.test(n)) return 'ALTILLO';
  if (/^BALDA/.test(n)) return 'BALDA';
  if (/^TECHO/.test(n)) return 'TECHO';
  if (/^REGLETA/.test(n)) return 'REGLETA';
  if (/^CORNISA/.test(n)) return 'CORNISA';
  if (/^ZOCALO/.test(n)) return 'ZOCALO';
  if (/^PORTALUZ/.test(n)) return 'PORTALUZ';
  if (/^REJILLA/.test(n)) return 'REJILLA';
  if (/^BOTELLERO/.test(n)) return 'BOTELLERO';
  if (/^PERFIL/.test(n)) return 'PERFIL';
  return category; // si no lo reconocemos, se queda como está (irá a "Otros")
};

// Familias "planas" (frentes/paneles/accesorios) que NO llevan incremento por
// corte: ni de viga ni de medidas (ancho/alto/fondo). Se detectan por el INICIO
// del nombre de familia para no confundir con muebles que contienen la palabra
// (p.ej. BAJO_PUERTA_CAJON o MEDIA_PUERTA_GAVETA sí son muebles con corte).
// NOTA: los ALTILLOS_DECORATIVOS NO van aquí: sí llevan incremento por corte de viga.
const FLAT_PANEL_RE = /^(COSTADO|LATERAL|REGLETA|BALDA|PUERTA|VITRINA|REJILLA|TECHO|ELEMENTOS_LINEALES)/;
const isFlatPanel = (category) => FLAT_PANEL_RE.test(String(category || '').toUpperCase());

/**
 * Presupuestador 2 — navegación por familias del catálogo MV (Muebles Valencia)
 * con selector de GRUPO DE TARIFA (T1…T21). El precio de cada mueble sale de
 * product.zonePoints[tarifa]. PDF con formato del Presupuestador 1 y guardado
 * en proyectos.
 */
const Presupuestador2 = ({ currentUser, logo, incomingProject, onProjectConsumed, incomingLines, incomingLibrary, onLinesConsumed }) => {
  const [libraryCode, setLibraryCode] = useState(() => localStorage.getItem('p2_library') || 'MV');
  const [availableLibraries, setAvailableLibraries] = useState([]);
  const [library, setLibrary] = useState(null);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tariff, setTariff] = useState(() => localStorage.getItem(`p2_tariff_${localStorage.getItem('p2_library') || 'MV'}`) || 'T1');
  const [family, setFamily] = useState('');
  const [search, setSearch] = useState('');
  const [searchScope, setSearchScope] = useState(() => localStorage.getItem('p2_search_scope') || 'all'); // 'all' | 'family'
  const [sizeFilter, setSizeFilter] = useState('');
  const [familyFilter, setFamilyFilter] = useState('');
  const [expandedGroups, setExpandedGroups] = useState({});
  const [familiesCollapsed, setFamiliesCollapsed] = useState(false);
  const [cartCollapsed, setCartCollapsed] = useState(false);
  const [budgetExpanded, setBudgetExpanded] = useState(false); // ocultar el catálogo y ver el presupuesto a todo el ancho
  const [configCollapsed, setConfigCollapsed] = useState(false); // ocultar fila de tarifa/acabados
  const [actionsCollapsed, setActionsCollapsed] = useState(false); // barra inferior plegable (totales + acciones)
  const cartListRef = useRef(null);   // auto-scroll al último mueble añadido
  const prevCartLen = useRef(0);
  const [familiesWidth, setFamiliesWidth] = useState(224);
  const [cartWidth, setCartWidth] = useState(416);
  const isResizingFamilies = useRef(false);
  const isResizingCart = useRef(false);

  useEffect(() => {
    const onMouseMove = (e) => {
      if (isResizingFamilies.current) setFamiliesWidth(Math.max(160, Math.min(500, e.clientX)));
      if (isResizingCart.current) setCartWidth(Math.max(280, Math.min(700, window.innerWidth - e.clientX)));
    };
    const onMouseUp = () => { isResizingFamilies.current = false; isResizingCart.current = false; };
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
    return () => { window.removeEventListener('mousemove', onMouseMove); window.removeEventListener('mouseup', onMouseUp); };
  }, []);
  const [mobileTab, setMobileTab] = useState('catalog'); // 'catalog' | 'cart'
  const [useMillimeters, setUseMillimeters] = useState(() => localStorage.getItem('p2_use_mm') === 'true');
  const [catalogView, setCatalogView] = useState(() => localStorage.getItem('p2_catalog_view') || 'list');
  const [showDistributorPrice, setShowDistributorPrice] = useState(false);
  const [sortBy, setSortBy] = useState('default'); // 'default' | 'code' | 'name' | 'width' | 'height' | 'price'
  const [sortDir, setSortDir] = useState('asc');
  const [cart, setCart] = useState([]);          // [{id, code, name, price, qty, manual}]
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [manualLine, setManualLine] = useState({ name: '', price: '', qty: 1 });
  const [showManual, setShowManual] = useState(false);
  const [clientName, setClientName] = useState('');
  const [clientId, setClientId] = useState('');          // cliente enlazado de la BD
  const [clientCodigo, setClientCodigo] = useState('');
  const [clientResults, setClientResults] = useState([]); // resultados de búsqueda
  const [showClientList, setShowClientList] = useState(false);
  const [budgetReference, setBudgetReference] = useState('');
  const [notes, setNotes] = useState('');
  const [doorColorLow, setDoorColorLow] = useState('');
  const [doorColorHigh, setDoorColorHigh] = useState('');
  const [doorColorColumns, setDoorColorColumns] = useState('');
  const [sideColor, setSideColor] = useState('');
  const [carcassMaterials, setCarcassMaterials] = useState(INITIAL_CARCASS_MATERIALS);
  const [selectedCarcassMaterialId, setSelectedCarcassMaterialId] = useState(INITIAL_CARCASS_MATERIALS[0]?.id || '');
  // Incrementos por biblioteca (medidas especiales y corte de viga), cargados de ajustes.
  const [librarySpecialIncrements, setLibrarySpecialIncrements] = useState({
    ZC: { width: 45, height: 45, depth: 45 }, MV: { width: 45, height: 45, depth: 45 },
  });
  const [libraryVigaCutIncrements, setLibraryVigaCutIncrements] = useState({ ZC: 0, MV: 0 });
  const [doorHasVeta, setDoorHasVeta] = useState(false);
  const [golaAlto, setGolaAlto] = useState(false);
  const [golaAltoColor, setGolaAltoColor] = useState('');
  const [golaBajo, setGolaBajo] = useState(false);
  const [golaBajoColor, setGolaBajoColor] = useState('');
  const [showDespiece, setShowDespiece] = useState(false);
  const [importing, setImporting] = useState(false);
  const [showNomenclatura, setShowNomenclatura] = useState(false);
  const [activeModule, setActiveModule] = useState('montada'); // 'montada' | 'despiece'
  const [showConfirmOrder, setShowConfirmOrder] = useState(false);
  const [orderEmail, setOrderEmail] = useState('');
  const [orderNotes, setOrderNotes] = useState('');
  const [orderAttachments, setOrderAttachments] = useState([]);
  const [isSendingOrder, setIsSendingOrder] = useState(false);
  const [orderSent, setOrderSent] = useState(false);
  // Render 3D adjuntado desde Estudio 3D (se incluye en el PDF del presupuesto).
  const [render3dImage, setRender3dImage] = useState(null);

  // Importar tarifas oficiales a los productos (solo admin). Hace dry-run, muestra
  // el resumen y, si confirmas, reconstruye el catálogo MV desde las tarifas.
  const importTariffs = async () => {
    setImporting(true);
    try {
      const dr = await fetch(`${API_URL}/api/libraries/MV/import-tariffs?dry_run=true`,
        { method: 'POST', headers: authHeaders() });
      const rep = await dr.json();
      if (!dr.ok) { alert('Error: ' + (rep.detail || dr.status)); return; }
      const tarifas = (rep.tarifas_con_datos || []).join(', ');
      const ok = window.confirm(
        `SIMULACIÓN del importador:\n\n` +
        `• ${rep.total_skus} muebles (SKUs)\n` +
        `• Tarifas con datos: ${tarifas || '—'}\n\n` +
        `¿APLICAR ahora? Reconstruye el catálogo MV desde las tarifas oficiales y ` +
        `elimina duplicados. Afecta a Presupuestador 1 y 2.`
      );
      if (!ok) return;
      const ap = await fetch(`${API_URL}/api/libraries/MV/import-tariffs?dry_run=false&wipe=true`,
        { method: 'POST', headers: authHeaders() });
      const r2 = await ap.json();
      if (ap.ok) {
        alert(`✅ Importado: ${r2.insertados} creados, ${r2.actualizados} actualizados.\n` +
              `Tarifas: ${(r2.tarifas_con_datos || []).join(', ')}`);
        await load();
      } else {
        alert('Error al aplicar: ' + (r2.detail || ap.status));
      }
    } catch (e) {
      alert('Error: ' + e.message);
    } finally {
      setImporting(false);
    }
  };

  const fixCostadosDepth = async () => {
    if (!window.confirm('Corregir el grueso de costados, regletas, zócalos, techos, etc. (33/58 -> 18cm)?')) return;
    setImporting(true);
    try {
      const r = await fetch(`${API_URL}/api/products/fix-costados-depth`,
        { method: 'POST', headers: authHeaders() });
      const rep = await r.json();
      if (r.ok) {
        alert(`✅ ${rep.message}`);
        await load();
      } else {
        alert('Error: ' + (rep.detail || r.status));
      }
    } catch (e) {
      alert('Error: ' + e.message);
    } finally {
      setImporting(false);
    }
  };

  useEffect(() => { localStorage.setItem('p2_library', libraryCode); }, [libraryCode]);

  // Cargar materiales de armazón (cascos) disponibles
  useEffect(() => {
    let active = true;
    materialsAPI.getAll(libraryCode).then(materials => {
      if (!active) return;
      const list = Array.isArray(materials) && materials.length > 0 ? materials : INITIAL_CARCASS_MATERIALS;
      setCarcassMaterials(list);
      const forLib = list.filter(m => !m.library || m.library === libraryCode);
      const saved = localStorage.getItem(`p2_carcass_${libraryCode}`);
      if (saved && forLib.some(m => m.id === saved)) {
        setSelectedCarcassMaterialId(saved);
      } else if (forLib.length > 0 && !forLib.some(m => m.id === selectedCarcassMaterialId)) {
        setSelectedCarcassMaterialId(forLib[0].id);
      }
    }).catch(() => {});
    return () => { active = false; };
  }, [libraryCode]);

  useEffect(() => { if (selectedCarcassMaterialId) localStorage.setItem(`p2_carcass_${libraryCode}`, selectedCarcassMaterialId); }, [selectedCarcassMaterialId, libraryCode]);

  // Cargar incrementos por medidas especiales, corte de viga y email de pedidos.
  useEffect(() => {
    settingsAPI.get().then(s => {
      if (!s) return;
      if (s.librarySpecialIncrements) setLibrarySpecialIncrements(s.librarySpecialIncrements);
      if (s.libraryVigaCutIncrements) setLibraryVigaCutIncrements(s.libraryVigaCutIncrements);
      if (s.emailSender && !orderEmail) setOrderEmail(s.emailSender);
    }).catch(() => {});
  }, []);
  useEffect(() => { if (tariff) localStorage.setItem(`p2_tariff_${libraryCode}`, tariff); }, [tariff, libraryCode]);
  // Consumir render3d_attach del Estudio 3D (transferencia única)
  useEffect(() => {
    try {
      const raw = localStorage.getItem('render3d_attach');
      if (raw) {
        const data = JSON.parse(raw);
        if (data.image) setRender3dImage(data.image);
        if (data.cliente && !clientName) setClientName(data.cliente);
        localStorage.removeItem('render3d_attach');
      }
    } catch (_) {}
  }, []);
  useEffect(() => { localStorage.setItem('p2_search_scope', searchScope); }, [searchScope]);
  useEffect(() => { localStorage.setItem('p2_use_mm', useMillimeters ? 'true' : 'false'); }, [useMillimeters]);
  useEffect(() => { localStorage.setItem('p2_catalog_view', catalogView); }, [catalogView]);

  // Bibliotecas disponibles para el usuario (ZC, MV, …) — solo se muestra el
  // selector si hay más de una permitida.
  useEffect(() => {
    librariesAPI.getAll()
      .then(data => {
        const allowed = currentUser?.allowedLibraries || ['MV'];
        const filtered = (Array.isArray(data) ? data : []).filter(l => l.isActive !== false && allowed.includes(l.code));
        setAvailableLibraries(filtered);
        if (filtered.length && !filtered.some(l => l.code === libraryCode)) {
          setLibraryCode(filtered[0].code);
        }
      })
      .catch(() => setAvailableLibraries([]));
  }, [currentUser]);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [libR, prodR] = await Promise.all([
        fetch(`${API_URL}/api/libraries/${libraryCode}`, { headers: authHeaders() }),
        fetch(`${API_URL}/api/libraries/${libraryCode}/products?limit=5000`, { headers: authHeaders() }),
      ]);
      const lib = await libR.json().catch(() => null);
      const prod = await prodR.json().catch(() => ({}));
      setLibrary(lib);
      const _raw = Array.isArray(prod.products) ? prod.products : [];
      setProducts(_raw.map(p => {
        const fixed = normalizeCategory(p.category, p.name || p.description, p.code || p.reference);
        return fixed === p.category ? p : { ...p, category: fixed };
      }));
    } catch (e) {
      setProducts([]);
    } finally { setLoading(false); }
  }, [libraryCode]);

  useEffect(() => { load(); }, [load]);

  // Al cambiar de biblioteca, soltamos la familia/búsqueda activas para que se
  // recalculen con el catálogo nuevo.
  useEffect(() => { setFamily(''); setSearch(''); }, [libraryCode]);

  const priceLevels = (library?.priceLevels && library.priceLevels.length)
    ? library.priceLevels
    : Array.from({ length: 21 }, (_, i) => `T${i + 1}`);
  const pointValue = library?.pointValue || 1.0;
  const levelLabel = library?.pricingSystem === 'zones' ? 'Grupo' : 'Tarifa';

  // Si la tarifa/zona guardada no existe en esta biblioteca, usamos la primera
  // disponible (p.ej. al cambiar de MV (T1-T21) a ZC (Z1-Z12)).
  useEffect(() => {
    if (!priceLevels.length) return;
    if (!priceLevels.includes(tariff)) setTariff(priceLevels[0]);
  }, [libraryCode, library]);

  // Reabrir un presupuesto creado en el Presupuestador 2: rehidrata el carrito,
  // la biblioteca, la tarifa, el cliente y los colores a partir del expediente
  // guardado (los items vienen en el formato "montada" de buildMontadaItems).
  useEffect(() => {
    if (!incomingProject) return;
    const proj = incomingProject;
    if (proj.libraryCode && proj.libraryCode !== libraryCode) setLibraryCode(proj.libraryCode);
    if (proj.tariff) setTariff(proj.tariff);
    const pv = library?.pointValue || pointValue || 1.0;
    const items = Array.isArray(proj.itemsMontada) ? proj.itemsMontada : [];
    setCart(items.map((it, idx) => {
      const isManual = !it.productId;
      const pts = Number(it.manualPoints) || 0;
      return {
        id: it.productId || `manual-${Date.now()}-${idx}`,
        code: it.customReference || it.productCode || 'MANUAL',
        name: it.manualDescription || it.productName || it.name || '',
        price: pts * pv,
        qty: it.quantity || 1,
        manual: isManual,
        hand: it.openingDirection === 'Derecha' ? 'D' : it.openingDirection === 'Izquierda' ? 'I' : null,
        notes: it.notes || '',
        customWidth: it.customWidth != null ? Number(it.customWidth) : '',
        customHeight: it.customHeight != null ? Number(it.customHeight) : '',
        customDepth: it.customDepth != null ? Number(it.customDepth) : '',
        hasVigaCut: !!it.hasVigaCut,
      };
    }));
    setClientName(proj.customerName || '');
    setBudgetReference(proj.internalReference || '');
    setNotes('');
    setDoorColorLow(proj.doorColorLow || '');
    setDoorColorHigh(proj.doorColorHigh || '');
    setDoorColorColumns(proj.doorColorColumns || '');
    setSideColor(proj.sideColor || '');
    setGolaAlto(!!proj.golaAlto);
    setGolaAltoColor(proj.golaAltoColor || '');
    setGolaBajo(!!proj.golaBajo);
    setGolaBajoColor(proj.golaBajoColor || '');
    if (proj.selectedCarcassMaterialId) setSelectedCarcassMaterialId(proj.selectedCarcassMaterialId);
    if (onProjectConsumed) onProjectConsumed();
  }, [incomingProject]);

  // Añadir líneas que llegan de otros módulos (p.ej. un plano de Cocinas 3D).
  // Se EMPAREJAN con el catálogo de la librería activa por productId o código:
  // si se encuentra el producto, entra como línea de catálogo (precio de la
  // librería, manual:false); solo si no se encuentra entra como línea manual.
  useEffect(() => {
    if (!incomingLines || !incomingLines.length) return;
    // Si el volcado viene de otra librería, cambiamos a ELLA antes de emparejar
    // (si no, los productId no existirían en el catálogo activo y todo caería a
    // manual). Al cambiar libraryCode se recargan products y el efecto re-corre.
    if (incomingLibrary && incomingLibrary !== libraryCode) { setLibraryCode(incomingLibrary); return; }
    if (!products || !products.length) return; // espera a que cargue el catálogo
    const norm = (c) => (c == null ? '' : String(c)).trim().toUpperCase();
    setCart(prev => [...prev, ...incomingLines.map((l, idx) => {
      const code = norm(l.code);
      const prod =
        (l.productId && products.find(p => p.id === l.productId)) ||
        (code && products.find(p => norm(p.code) === code)) ||
        (code && products.find(p => norm(p.code).replace(/[^A-Z0-9]/g, '') === code.replace(/[^A-Z0-9]/g, ''))) ||
        null;
      if (prod) {
        // Línea de CATÁLOGO: el precio lo calcula la propia tarifa (unitPriceOf).
        // NO se pasan medidas custom: la medida detectada por IA casi nunca
        // coincide al cm con el nominal y dispararía un recargo de "medida
        // especial" fantasma. Se usa el nominal del catálogo (custom = '').
        return {
          id: prod.id,
          code: prod.code,
          name: prod.name,
          qty: Number(l.qty) || 1,
          manual: false,
          customWidth: '',
          customHeight: '',
          customDepth: '',
        };
      }
      // No encontrado: línea manual (igual que antes).
      return {
        id: `ext-${Date.now()}-${idx}`,
        code: l.code || 'MANUAL',
        name: l.name || 'Línea',
        price: Number(l.price) || 0,
        qty: Number(l.qty) || 1,
        manual: true,
        itemType: l.itemType || null,
        finish: l.finish || null,
        interiorFinish: l.interiorFinish || null,
        customWidth: l.width != null ? Number(l.width) : '',
        customHeight: l.height != null ? Number(l.height) : '',
        customDepth: l.depth != null ? Number(l.depth) : '',
      };
    })]);
    if (onLinesConsumed) onLinesConsumed();
  }, [incomingLines, products]);

  // Descuento comercial del usuario, para el modo "COSTO fábrica".
  const discountPct = currentUser?.discountMontada ?? currentUser?.commercialDiscount ?? 0;
  const discountFactor = showDistributorPrice ? (1 - discountPct / 100) : 1;

  const measureUnit = useMillimeters ? 'mm' : 'cm';
  const formatMeasure = useCallback((v) => {
    const n = parseFloat(v);
    if (!v || Number.isNaN(n)) return null;
    return useMillimeters ? Math.round(n * 10) : n;
  }, [useMillimeters]);

  const priceOf = useCallback((p) => {
    const zp = p.zonePoints || {};
    const base = zp[tariff] ?? zp[priceLevels[0]] ?? (typeof p.points === 'number' ? p.points : 0) ?? 0;
    return (Number(base) || 0) * pointValue;
  }, [tariff, pointValue, priceLevels]);

  // Precio a mostrar según el modo PVP / COSTO fábrica (con descuento comercial).
  const displayPrice = useCallback((base) => base * discountFactor, [discountFactor]);

  // Precio unitario VIVO de una línea del presupuesto. Para los muebles del
  // catálogo se recalcula SIEMPRE con la tarifa activa (así, al cambiar T1→T2,
  // cambian el precio de cada mueble y el total). Las líneas manuales conservan
  // el precio tecleado.
  const unitPriceOf = useCallback((it) => {
    if (it.manual) return Number(it.price) || 0;
    const prod = products.find(p => p.id === it.id);
    return prod ? priceOf(prod) : (Number(it.price) || 0);
  }, [products, priceOf]);

  const families = useMemo(() => {
    const m = {};
    products.forEach(p => {
      const c = (p.category || 'OTROS').trim() || 'OTROS';
      m[c] = (m[c] || 0) + 1;
    });
    return Object.entries(m).sort((a, b) => a[0].localeCompare(b[0]));
  }, [products]);

  // A propósito NO se auto-selecciona ninguna familia al cargar: el presupuestador
  // entra mostrando todo el catálogo, sin familia ni mueble preseleccionados
  // (el usuario busca o elige familia cuando quiere).

  // Agrupa familias muy parecidas (singular/plural, variantes "color"/"melamina"…)
  // bajo una cabecera común, para que la barra de categorías no sea interminable.
  const familyGroups = useMemo(() => {
    const order = {}, labelOf = {};
    MAIN_FAMILY_DEFS.forEach((d, i) => { order[d.key] = i; labelOf[d.key] = d.label; });
    labelOf['OTROS'] = '99 · Otros'; order['OTROS'] = 999;
    const groups = {};
    // Sembrar SIEMPRE las 12 familias principales (aunque no tengan productos aún),
    // para que existan como categorías en el menú: Sobremódulos, Elementos
    // lineales y Estructuras decorativas aparecen también vacías.
    MAIN_FAMILY_DEFS.forEach((d, i) => { groups[d.key] = { key: d.key, label: d.label, order: i, total: 0, members: [] }; });
    families.forEach(([name, count]) => {
      const key = mainFamilyKeyOf(name);
      if (!groups[key]) groups[key] = { key, label: labelOf[key] || key, order: order[key] ?? 998, total: 0, members: [] };
      groups[key].total += count;
      groups[key].members.push([name, count]);
    });
    let list = Object.values(groups);
    const q = familyFilter.trim().toLowerCase();
    if (q) {
      list = list.filter(g => g.label.toLowerCase().includes(q) || g.key.toLowerCase().includes(q) || g.members.some(([n]) => n.toLowerCase().includes(q)));
    }
    list.forEach(g => g.members.sort((a, b) => a[0].localeCompare(b[0])));
    return list.sort((a, b) => a.order - b.order);
  }, [families, familyFilter]);

  // Si la familia activa pertenece a un grupo con varios miembros, lo dejamos
  // expandido automáticamente para que se vea seleccionado.
  useEffect(() => {
    if (!family) return;
    const key = mainFamilyKeyOf(family);
    setExpandedGroups(prev => (prev[key] ? prev : { ...prev, [key]: true }));
  }, [family]);

  // Búsqueda GLOBAL e intuitiva: si hay texto, busca en TODO el catálogo (o solo en
  // la familia activa, según el modo elegido) por código, nombre, familia y medidas;
  // admite varias palabras (todas deben coincidir, en cualquier orden). Sin texto,
  // filtra por la familia activa. También admite un filtro opcional de medida (±5cm).
  const searching = search.trim().length > 0;
  const shown = useMemo(() => {
    const tokens = search.trim().toLowerCase().split(/\s+/).filter(Boolean);
    const sizeQ = parseFloat(sizeFilter);
    const hasSize = !Number.isNaN(sizeQ) && sizeQ > 0;
    return products.filter(p => {
      if (tokens.length === 0) {
        if (family && (p.category || 'OTROS') !== family) return false;
      } else {
        const dims = [p.width, p.height, p.depth].filter(Boolean).join('x');
        const hay = `${p.code || ''} ${p.reference || ''} ${p.name || ''} ${p.category || ''} ${dims}`.toLowerCase();
        if (!tokens.every(t => hay.includes(t))) return false;
        if (searchScope === 'family' && family && (p.category || 'OTROS') !== family) return false;
      }
      if (hasSize) {
        const sizeInCm = useMillimeters ? sizeQ / 10 : sizeQ;
        const dims = [p.width, p.height, p.depth].filter(Boolean);
        if (!dims.some(d => Math.abs(d - sizeInCm) <= (useMillimeters ? 0.5 : 5))) return false;
      }
      return true;
    });
  }, [products, family, search, searchScope, sizeFilter, useMillimeters]);

  // Orden de los resultados (código, nombre, ancho, alto o precio).
  const sortedShown = useMemo(() => {
    if (sortBy === 'default') return shown;
    const dir = sortDir === 'asc' ? 1 : -1;
    return [...shown].sort((a, b) => {
      let va, vb;
      switch (sortBy) {
        case 'code': va = a.code || a.reference || ''; vb = b.code || b.reference || ''; break;
        case 'name': va = a.name || ''; vb = b.name || ''; break;
        case 'width': va = Number(a.width) || 0; vb = Number(b.width) || 0; break;
        case 'height': va = Number(a.height) || 0; vb = Number(b.height) || 0; break;
        case 'price': va = priceOf(a); vb = priceOf(b); break;
        default: va = 0; vb = 0;
      }
      if (typeof va === 'number' && typeof vb === 'number') return (va - vb) * dir;
      return String(va).localeCompare(String(vb)) * dir;
    });
  }, [shown, sortBy, sortDir, priceOf]);

  const addToCart = (p) => {
    const price = priceOf(p);
    setCart(prev => {
      const i = prev.findIndex(x => x.id === p.id && !x.manual);
      if (i >= 0) {
        const cp = [...prev]; cp[i] = { ...cp[i], qty: cp[i].qty + 1 }; return cp;
      }
      return [...prev, {
        id: p.id, code: p.code || p.reference, name: p.name, price, qty: 1, manual: false,
        customWidth: Number(p.width) || 0, customHeight: Number(p.height) || 0, customDepth: Number(p.depth) || 0,
        hasVigaCut: false,
      }];
    });
  };

  // Auto-scroll: al añadir un mueble, baja la lista del presupuesto para verlo.
  useEffect(() => {
    if (cart.length > prevCartLen.current && cartListRef.current) {
      cartListRef.current.scrollTop = cartListRef.current.scrollHeight;
    }
    prevCartLen.current = cart.length;
  }, [cart.length]);

  const addManualLine = () => {
    if (!manualLine.name.trim()) return;
    const price = parseFloat(manualLine.price) || 0;
    const qty = parseInt(manualLine.qty) || 1;
    setCart(prev => [...prev, {
      id: `manual-${Date.now()}`, code: 'MANUAL', name: manualLine.name.trim(), price, qty, manual: true,
    }]);
    setManualLine({ name: '', price: '', qty: 1 });
    setShowManual(false);
  };

  const setQty = (id, delta) => setCart(prev => prev
    .map(x => x.id === id ? { ...x, qty: Math.max(1, x.qty + delta) } : x));
  const setQtyValue = (id, value) => setCart(prev => prev
    .map(x => x.id === id ? { ...x, qty: Math.max(1, parseInt(value, 10) || 1) } : x));
  const removeItem = (id) => setCart(prev => prev.filter(x => x.id !== id));
  const updateItemPrice = (id, newPrice) => setCart(prev => prev
    .map(x => x.id === id ? { ...x, price: parseFloat(newPrice) || 0 } : x));
  const setItemHand = (id, hand) => setCart(prev => prev
    .map(x => x.id === id ? { ...x, hand: x.hand === hand ? null : hand } : x));
  const setItemNotes = (id, notes) => setCart(prev => prev
    .map(x => x.id === id ? { ...x, notes } : x));
  const setItemDim = (id, field, value) => setCart(prev => prev
    .map(x => x.id === id ? { ...x, [field]: value === '' ? '' : Number(value) } : x));
  const toggleViga = (id) => setCart(prev => prev
    .map(x => x.id === id ? { ...x, hasVigaCut: !x.hasVigaCut } : x));

  // Extras de precio por línea (medidas especiales + corte de viga + armazón),
  // replicando el Presupuestador 1. Los paneles planos (costados, baldas, puertas,
  // vitrinas, regletas, techos, elementos lineales…) NO llevan incremento por corte
  // (ni de viga ni de medidas). Las líneas manuales tampoco.
  const extrasOf = useCallback((it) => {
    if (it.manual) return 0;
    const prod = products.find(p => p.id === it.id);
    if (!prod) return 0;
    const flat = isFlatPanel(prod.category);
    const inc = librarySpecialIncrements?.[libraryCode] || { width: 0, height: 0, depth: 0 };
    let extra = 0;
    if (!flat) {
      if (it.customWidth !== '' && Number(it.customWidth) !== Number(prod.width)) extra += Number(inc.width) || 0;
      if (it.customHeight !== '' && Number(it.customHeight) !== Number(prod.height)) extra += Number(inc.height) || 0;
      if (it.customDepth !== '' && Number(it.customDepth) !== Number(prod.depth)) extra += Number(inc.depth) || 0;
      if (it.hasVigaCut) extra += Number(libraryVigaCutIncrements?.[libraryCode]) || 0;
    }
    const mat = carcassMaterials.find(m => m.id === selectedCarcassMaterialId);
    extra += Number(mat?.fixedIncrement) || 0;
    return extra;
  }, [products, librarySpecialIncrements, libraryVigaCutIncrements, libraryCode, carcassMaterials, selectedCarcassMaterialId]);

  // Precio unitario COMPLETO: catálogo + extras (medidas, viga, armazón).
  const unitFull = useCallback((it) => unitPriceOf(it) + extrasOf(it), [unitPriceOf, extrasOf]);

  // Las líneas manuales nunca llevan descuento; el resto sí, si está activo el modo COSTO.
  const lineTotal = (x) => unitFull(x) * x.qty * (x.manual ? 1 : discountFactor);
  const cartTotal = cart.reduce((s, x) => s + lineTotal(x), 0);
  const cartTotalPvp = cart.reduce((s, x) => s + unitFull(x) * x.qty, 0);
  const ivaRate = 21;
  const ivaAmount = cartTotal * (ivaRate / 100);
  const totalConIva = cartTotal + ivaAmount;
  const totalUds = cart.reduce((s, x) => s + (x.qty || 0), 0);

  const budgetNumberRef = useRef(null);
  const getBudgetNumber = useCallback(() => {
    if (!budgetNumberRef.current) budgetNumberRef.current = `${libraryCode}-${new Date().getFullYear()}-${String(Date.now()).slice(-5)}`;
    return budgetNumberRef.current;
  }, [libraryCode]);
  // Reset when library changes so a new reference is generated
  useEffect(() => { budgetNumberRef.current = null; }, [libraryCode]);

  // Mapea las líneas de P2 a items "montada" de P1 (líneas manuales: el precio sale
  // de la tarifa). precio P1 = manualPoints * pointValue * qty → manualPoints = precio/pointValue
  const buildMontadaItems = useCallback(() => cart.map((it, idx) => {
    const prod = !it.manual ? products.find(p => p.id === it.id) : null;
    // El descuento de distribuidor (modo COSTO) debe reflejarse en TODOS los
    // canales (PDF, guardado, email de pedido), no solo en el total de pantalla.
    // Las líneas manuales nunca llevan descuento (misma regla que lineTotal).
    const unit = unitFull(it) * (it.manual ? 1 : discountFactor);
    const pts = pointValue ? (unit / pointValue) : unit;
    return {
      id: `p2-${idx}-${it.id}`,
      productId: it.manual ? null : it.id,
      quantity: it.qty,
      isManual: it.manual,
      manualDescription: it.name,
      customReference: it.code,
      manualPoints: pts,
      // Las líneas manuales con medidas (p.ej. armario) las conservan; el resto 0.
      customWidth: it.customWidth !== '' && it.customWidth != null ? Number(it.customWidth) : (it.manual ? 0 : (prod?.width || 0)),
      customHeight: it.customHeight !== '' && it.customHeight != null ? Number(it.customHeight) : (it.manual ? 0 : (prod?.height || 0)),
      customDepth: it.customDepth !== '' && it.customDepth != null ? Number(it.customDepth) : (it.manual ? 0 : (prod?.depth || 0)),
      hasVigaCut: !!it.hasVigaCut,
      openingDirection: it.hand === 'D' ? 'Derecha' : it.hand === 'I' ? 'Izquierda' : '',
      notes: it.notes || '',
      itemType: it.itemType || null,
      finish: it.finish || null,
    };
  }), [cart, products, pointValue, unitFull, discountFactor]);

  // Items para el DESPIECE (reutiliza el motor/modal del Presupuestador 1).
  // Las medidas salen del catálogo MV; el backend clasifica por nombre/código.
  const rawDespieceItems = useMemo(() => cart.map((it, idx) => {
    const prod = !it.manual ? products.find(p => p.id === it.id) : null;
    const width = it.customWidth !== '' && it.customWidth != null ? Number(it.customWidth) : (prod?.width || 0);
    const height = it.customHeight !== '' && it.customHeight != null ? Number(it.customHeight) : (prod?.height || 0);
    const depth = it.customDepth !== '' && it.customDepth != null ? Number(it.customDepth) : (prod?.depth || 0);
    return {
      id: `p2d-${idx}`,
      productId: it.manual ? `manual-${idx}` : it.id,
      isManual: !!it.manual,
      customReference: it.code,
      manualDescription: it.name,
      productName: it.name,
      customWidth: width,
      customHeight: height,
      customDepth: depth,
      hasVigaCut: !!it.hasVigaCut,
      quantity: Number(it.qty) || 0,
      // Las líneas manuales NO entran a fábrica/despiece (no son muebles del catálogo).
      _canDespiece: !it.manual && width > 0 && height > 0 && depth > 0 && (Number(it.qty) || 0) > 0,
    };
  }), [cart, products]);

  const despieceItems = useMemo(() => rawDespieceItems.filter(i => i._canDespiece), [rawDespieceItems]);

  const openDespiece = () => {
    if (cart.length === 0) { alert('Añade al menos una línea'); return; }
    if (despieceItems.length === 0) {
      alert('No hay líneas con ancho, alto, fondo y cantidad válidos para generar el despiece. Revisa las medidas del catálogo o de la línea manual.');
      return;
    }
    const ignored = rawDespieceItems.length - despieceItems.length;
    if (ignored > 0 && !window.confirm(`${ignored} línea(s) manuales o sin medidas/cantidad válidas se excluirán del despiece. ¿Continuar?`)) return;
    setShowDespiece(true);
  };

  const saveOrder = async () => {
    if (cart.length === 0) { alert('Añade al menos una línea'); return; }
    setSaving(true);
    try {
      const projectData = {
        budgetNumber: getBudgetNumber(),
        customerName: clientName || currentUser?.clientName || 'Sin cliente',
        clientId: clientId || undefined,
        clientCodigo: clientCodigo || undefined,
        customerAddress: '',
        internalReference: budgetReference || notes || `Presupuesto ${libraryCode} (${levelLabel} ${tariff})`,
        itemsMontada: buildMontadaItems(),
        itemsDespiece: [],
        doorColorLow,
        doorColorHigh,
        doorColorColumns,
        sideColor,
        selectedCarcassMaterialId,
        carcassMaterialName: carcassMaterials.find(m => m.id === selectedCarcassMaterialId)?.name || '',
        golaAlto,
        golaAltoColor,
        golaBajo,
        golaBajoColor,
        status: 'activo',
        totalPvp: cartTotalPvp,
        ivaRate,
        // Marca de origen para reabrirlo en el Presupuestador 2 (con su tarifa
        // y biblioteca) y mostrarlo en naranja en el Archivo de Proyectos.
        source: 'presupuestador2',
        libraryCode,
        tariff,
      };
      const r = await fetch(`${API_URL}/api/projects?user_id=${encodeURIComponent(currentUser?.id || '')}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify(projectData),
      });
      if (r.ok) {
        setSaved(true); setTimeout(() => setSaved(false), 3000);
        // Tras guardar, ofrecer crear la oportunidad en el CRM (solo a usuarios con CRM).
        const savedProject = await r.json().catch(() => null);
        const savedId = savedProject?.id;
        if (savedId && currentUser?.canAccessCRM && window.confirm('Presupuesto guardado. ¿Crear también una oportunidad en el CRM con este presupuesto?')) {
          try {
            const res = await crmOpportunitiesAPI.createFromProject(savedId);
            alert(`✅ Oportunidad creada en el CRM: "${res?.opportunity?.title || 'OK'}"`);
          } catch (err) {
            alert('El presupuesto se guardó, pero no se pudo crear la oportunidad: ' + (err.message || err));
          }
        }
      }
      else { const e = await r.json().catch(() => ({})); alert('Error al guardar el presupuesto: ' + (e.detail || r.status)); }
    } catch (e) { alert('Error de conexión al guardar'); }
    finally { setSaving(false); }
  };

  // Exportar PDF con el MISMO formato que el Presupuestador 1 (descarga un PDF real).
  const exportPDF = (valorado = true) => {
    if (cart.length === 0) { alert('Añade al menos una línea'); return; }
    try {
      generateBudgetPDF({
        valorado,
        budgetNumber: getBudgetNumber(),
        customerName: clientName || currentUser?.clientName || 'Sin especificar',
        clientId: clientId || undefined,
        clientCodigo: clientCodigo || undefined,
        customerAddress: '',
        internalReference: budgetReference || notes || '',
        itemsMontada: buildMontadaItems(),
        itemsDespiece: [],
        pointValueMontada: pointValue,
        logo: logo || currentUser?.logo,
        brandColor: '#ea580c',
        companyName: 'LUIGGI HOME',
        ivaRate,
        allProducts: products,
        globalFinish: `${levelLabel} ${tariff}`,
        doorColorLow,
        doorColorHigh,
        doorColorColumns,
        sideColor,
        selectedCarcassMaterialId,
        carcassMaterialName: carcassMaterials.find(m => m.id === selectedCarcassMaterialId)?.name || '',
        golaAlto,
        golaAltoColor,
        golaBajo,
        golaBajoColor,
        render3dImage,
      });
    } catch (e) { alert('No se pudo generar el PDF: ' + (e.message || e)); }
  };

  const handlePrint = () => exportPDF();

  const handleConfirmOrder = async () => {
    if (!orderEmail.trim()) { alert('Introduce el email del destinatario'); return; }
    setIsSendingOrder(true);
    try {
      const formData = new FormData();
      const budNum = getBudgetNumber();
      formData.append('budgetNumber', budNum);
      formData.append('customerName', clientName || currentUser?.clientName || 'Sin cliente');
      if (clientId) formData.append('clientId', clientId);
      if (clientCodigo) formData.append('clientCodigo', clientCodigo);
      formData.append('customerAddress', '');
      formData.append('totalAmount', String(totalConIva.toFixed(2)));
      formData.append('email', orderEmail);
      formData.append('notes', orderNotes || notes || '');
      formData.append('items', JSON.stringify(buildMontadaItems().map(it => ({
        name: it.manualDescription, code: it.customReference, qty: it.quantity,
        price: (it.manualPoints || 0) * pointValue,
        width: it.customWidth || 0, height: it.customHeight || 0, depth: it.customDepth || 0,
        itemType: it.itemType || null, finish: it.finish || null,
      }))));
      formData.append('doorColorLow', doorColorLow);
      formData.append('doorColorHigh', doorColorHigh);
      formData.append('doorColorColumns', doorColorColumns);
      formData.append('sideColor', sideColor);
      formData.append('carcassColor', carcassMaterials.find(m => m.id === selectedCarcassMaterialId)?.name || '');
      formData.append('globalFinish', `${levelLabel} ${tariff}`);
      formData.append('distributorName', currentUser?.name || '');
      formData.append('userId', currentUser?.id || '');
      formData.append('projectReference', budgetReference || budNum);
      orderAttachments.slice(0, 5).forEach((f, i) => formData.append(`attachment_${i}`, f));
      const r = await fetch(`${API_URL}/api/orders/confirm`, {
        // FormData multipart: solo Authorization (el navegador pone el Content-Type
        // con su boundary; poner application/json rompería el parseo).
        method: 'POST', headers: { Authorization: authHeaders().Authorization }, body: formData,
      });
      if (r.ok) {
        setOrderSent(true);
        await saveOrder();
        setTimeout(() => {
          setOrderSent(false);
          setShowConfirmOrder(false);
          setOrderNotes('');
          setOrderAttachments([]);
          setCart([]);
          budgetNumberRef.current = null;
        }, 2500);
      } else {
        const e = await r.json().catch(() => ({}));
        alert('Error al enviar pedido: ' + (e.detail || r.status));
      }
    } catch (e) { alert('Error: ' + e.message); }
    finally { setIsSendingOrder(false); }
  };

  const inCart = (id) => cart.some(x => x.id === id && !x.manual);

  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-slate-50 to-orange-50/40">
      {/* ── Cabecera ── */}
      <div className="shrink-0 bg-gradient-to-r from-orange-700 via-orange-600 to-amber-600 text-white shadow-lg sticky top-0 z-30">
        {/* Fila principal */}
        <div className="pl-5 sm:pl-7 pr-3 sm:pr-4 py-2 flex items-center gap-2">
          {/* Logo */}
          <div className="w-9 h-9 bg-white rounded-xl flex items-center justify-center ring-1 ring-white/30 overflow-hidden shrink-0">
            {logo
              ? <img src={logo} alt="Logo" className="h-full w-full object-contain p-0.5" />
              : <span className="text-orange-600 font-black italic text-sm leading-none select-none">L</span>
            }
          </div>
          <div className="shrink-0 hidden sm:block">
            <h1 className="text-sm font-black uppercase leading-none tracking-tight">Presupuestador</h1>
            <p className="text-[9px] text-orange-100/80 flex items-center gap-0.5 mt-0.5 whitespace-nowrap">
              <Boxes size={9} /> {products.length} muebles
            </p>
          </div>

          {/* Cliente — buscador enlazado a la base de datos de clientes */}
          <div className="relative flex-1 min-w-0 max-w-[22rem]">
            <input
              value={clientName}
              onChange={async (e) => {
                const v = e.target.value;
                setClientName(v); setClientId(''); setClientCodigo('');
                if (v.trim().length < 2) { setClientResults([]); setShowClientList(false); return; }
                try {
                  const r = await fetch(`${API_URL}/api/clients?search=${encodeURIComponent(v.trim())}`, { headers: authHeaders() });
                  const list = r.ok ? await r.json() : [];
                  setClientResults(Array.isArray(list) ? list.slice(0, 12) : []);
                  setShowClientList(true);
                } catch { setClientResults([]); }
              }}
              onFocus={() => { if (clientName.trim().length >= 2) setShowClientList(true); }}
              onBlur={() => setTimeout(() => setShowClientList(false), 150)}
              placeholder="👤 Cliente…"
              className="w-full px-3 py-1.5 bg-white rounded-xl ring-1 ring-white/25 text-xs font-black text-black placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-white" />
            {clientId && <span className="absolute -bottom-4 left-1 text-[9px] font-bold text-emerald-200">✓ Enlazado{clientCodigo ? ` · ${clientCodigo}` : ''}</span>}
            {showClientList && clientName.trim().length >= 2 && (
              <div className="absolute z-[120] mt-1 w-full bg-white rounded-xl shadow-2xl border border-slate-200 max-h-72 overflow-y-auto">
                {clientResults.map(c => (
                  <button key={c.id} type="button"
                    onMouseDown={(ev) => { ev.preventDefault(); setClientName(c.nombre || ''); setClientId(c.id || ''); setClientCodigo(c.codigo || ''); setShowClientList(false); }}
                    className="w-full text-left px-3 py-2 hover:bg-indigo-50 border-b border-slate-100 last:border-0">
                    <span className="block text-xs font-black text-slate-800 truncate">{c.nombre || 'Sin nombre'}</span>
                    <span className="block text-[10px] text-slate-400">{[c.codigo && `Cód. ${c.codigo}`, c.localidad, c.cif].filter(Boolean).join(' · ') || '—'}</span>
                  </button>
                ))}
                {/* Sin coincidencia exacta: usar el texto escrito como nombre libre */}
                <button type="button"
                  onMouseDown={(ev) => { ev.preventDefault(); setClientId(''); setClientCodigo(''); setShowClientList(false); }}
                  className="w-full text-left px-3 py-2 hover:bg-amber-100 bg-amber-50/50 border-t border-slate-100">
                  <span className="block text-xs font-black text-amber-700 truncate">Usar "{clientName.trim()}"</span>
                  <span className="block text-[10px] text-amber-500">{clientResults.length ? 'Como cliente nuevo (sin enlazar)' : 'No está en la BD · se usará tal cual'}</span>
                </button>
              </div>
            )}
          </div>
          <input value={budgetReference} onChange={e => setBudgetReference(e.target.value)} placeholder="🏷️ Ref…"
            className="w-24 sm:w-40 shrink-0 px-3 py-1.5 bg-white rounded-xl ring-1 ring-white/25 text-xs font-black text-black placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-white" />

          {/* Botones utilitarios — con etiqueta (en pantallas grandes) para que se entienda su función */}
          <div className="flex items-center gap-1.5 shrink-0 ml-auto">
            <button onClick={() => setConfigCollapsed(v => !v)} title={configCollapsed ? 'Mostrar la fila de tarifa y acabados' : 'Ocultar la fila de tarifa y acabados'}
              className="flex items-center gap-1 px-2 py-1.5 bg-white/15 hover:bg-white/25 rounded-lg text-[10px] font-bold">
              {configCollapsed ? <ChevronDown size={13} /> : <ChevronUp size={13} />}
              <span className="hidden lg:inline">Acabados</span>
            </button>
            <button onClick={() => setUseMillimeters(v => !v)} title="Cambiar unidad de medida (cm / mm)"
              className="flex items-center gap-1 px-2 py-1.5 bg-white/15 hover:bg-white/25 rounded-lg text-[10px] font-bold">
              <Ruler size={13} />
              <span className="hidden lg:inline">{useMillimeters ? 'mm' : 'cm'}</span>
            </button>
            <button onClick={() => setCatalogView(v => v === 'list' ? 'icons' : 'list')} title={catalogView === 'list' ? 'Ver el catálogo con iconos' : 'Ver el catálogo en lista'}
              className="flex items-center gap-1 px-2 py-1.5 bg-white/15 hover:bg-white/25 rounded-lg text-[10px] font-bold">
              {catalogView === 'list' ? <LayoutGrid size={13} /> : <List size={13} />}
              <span className="hidden lg:inline">Vista</span>
            </button>
            {discountPct > 0 && (
              <button onClick={() => setShowDistributorPrice(v => !v)} title={showDistributorPrice ? 'Mostrando precio de distribuidor (clic para PVP)' : 'Mostrando PVP (clic para precio distribuidor)'}
                className={`flex items-center gap-1 px-2 py-1.5 rounded-lg text-[10px] font-bold transition-colors ${showDistributorPrice ? 'bg-orange-500' : 'bg-white/15 hover:bg-white/25'}`}>
                {showDistributorPrice ? <Unlock size={13} /> : <Lock size={13} />}
                <span className="hidden lg:inline">{showDistributorPrice ? 'Distrib.' : 'PVP'}</span>
              </button>
            )}
            <button onClick={() => setShowNomenclatura(true)} title="Nomenclatura: códigos e iconos de los muebles"
              className="hidden sm:flex items-center gap-1 px-2 py-1.5 bg-white/15 hover:bg-white/25 rounded-lg text-[10px] font-bold">
              <BookOpen size={13} />
              <span className="hidden lg:inline">Nomenclatura</span>
            </button>
            {currentUser?.isAdmin && libraryCode === 'MV' && (
              <button onClick={importTariffs} disabled={importing} title="Importar las tarifas oficiales MV a los precios (admin)"
                className="hidden sm:flex items-center gap-1 px-2 py-1.5 bg-white/15 hover:bg-white/25 rounded-lg text-[10px] font-bold disabled:opacity-60">
                {importing ? <Loader size={13} className="animate-spin" /> : <Boxes size={13} />}
                <span className="hidden lg:inline">Importar</span>
              </button>
            )}
            {currentUser?.isAdmin && libraryCode === 'ZC' && (
              <button onClick={fixCostadosDepth} disabled={importing} title="Corregir el grueso de los paneles ZC (admin)"
                className="hidden sm:flex items-center gap-1 px-2 py-1.5 bg-white/15 hover:bg-white/25 rounded-lg text-[10px] font-bold disabled:opacity-60">
                {importing ? <Loader size={13} className="animate-spin" /> : <Boxes size={13} />}
                <span className="hidden lg:inline">Paneles ZC</span>
              </button>
            )}
            {cartTotal > 0 && (
              <div className="flex flex-col items-end leading-none ml-1 shrink-0 pl-1 sm:pl-2">
                <span className="text-[8px] sm:text-[9px] uppercase text-orange-100/80 font-bold whitespace-nowrap">Total c/IVA</span>
                <span className="text-sm sm:text-base font-black whitespace-nowrap">{eur(totalConIva)}</span>
              </div>
            )}
          </div>
        </div>
        {/* Fila única: biblioteca, tarifa, colores/acabados y total — una sola línea a todo el ancho.
            Ocultable con el botón (chevron) de la cabecera. */}
        {!configCollapsed && (
        <div className="px-3 sm:px-4 pb-2 flex items-center gap-1.5 overflow-x-auto no-scrollbar">
          {availableLibraries.length > 1 && (
            <div className="flex items-center gap-1.5 bg-white/15 backdrop-blur rounded-xl pl-2 pr-1 py-1 ring-1 ring-white/25 shrink-0">
              <LibraryIcon size={12} className="shrink-0" />
              <select value={libraryCode} onChange={e => setLibraryCode(e.target.value)}
                className="px-1.5 py-0.5 bg-white rounded-lg text-xs font-black text-orange-700 focus:ring-2 focus:ring-white outline-none cursor-pointer">
                {availableLibraries.map(l => <option key={l.code} value={l.code}>{l.name || l.code}</option>)}
              </select>
            </div>
          )}
          <div className="flex items-center gap-1.5 bg-white/15 backdrop-blur rounded-xl pl-2 pr-1 py-1 ring-1 ring-white/25 shrink-0">
            <Tag size={12} className="shrink-0" />
            <select value={tariff} onChange={e => setTariff(e.target.value)}
              className="px-1.5 py-0.5 bg-white rounded-lg text-xs font-black text-orange-700 focus:ring-2 focus:ring-white outline-none cursor-pointer">
              {priceLevels.map(t => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
          {[
            ['Bajos', doorColorLow, setDoorColorLow],
            ['Altos', doorColorHigh, setDoorColorHigh],
            ['Col.', doorColorColumns, setDoorColorColumns],
            ['Cost.', sideColor, setSideColor],
          ].map(([label, val, setter]) => (
            <label key={label} className="flex items-center gap-1 bg-white/10 rounded-lg ring-1 ring-white/25 pl-2 pr-1 py-0.5 flex-1 min-w-[5rem]">
              <span className="text-[9px] font-black text-orange-50 uppercase tracking-wide whitespace-nowrap">{label}</span>
              <input type="text" value={val} onChange={e => setter(e.target.value)}
                className="flex-1 min-w-0 w-full px-1.5 py-0.5 bg-white rounded-md text-[10px] font-bold text-black placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-orange-300" placeholder="color…" />
            </label>
          ))}
          <label className="flex items-center gap-1 bg-white/10 rounded-lg ring-1 ring-white/25 pl-2 pr-1 py-0.5 shrink-0">
            <span className="text-[9px] font-black text-orange-50 uppercase tracking-wide whitespace-nowrap">Armazón</span>
            <select value={selectedCarcassMaterialId} onChange={e => setSelectedCarcassMaterialId(e.target.value)}
              className="px-1.5 py-0.5 bg-white rounded-md text-[10px] font-bold text-slate-900 focus:outline-none focus:ring-1 focus:ring-orange-300">
              {carcassMaterials.filter(m => !m.library || m.library === libraryCode).map(m => (
                <option key={m.id} value={m.id}>{m.name}</option>
              ))}
            </select>
          </label>
          <label className="flex items-center gap-1 bg-white/15 rounded-lg px-2 py-0.5 ring-1 ring-white/25 text-[9px] font-bold cursor-pointer select-none whitespace-nowrap shrink-0">
            <input type="checkbox" checked={doorHasVeta === true} onChange={e => setDoorHasVeta(e.target.checked)} className="w-3 h-3 accent-white" />
            Veta
          </label>
          <label className="flex items-center gap-1 bg-white/10 rounded-lg pl-2 pr-1 py-0.5 ring-1 ring-white/25 flex-1 min-w-[7rem]">
            <input type="checkbox" checked={golaAlto} onChange={e => { setGolaAlto(e.target.checked); if (!e.target.checked) setGolaAltoColor(''); }} className="w-3 h-3 accent-white shrink-0" />
            <span className="text-[9px] font-black text-orange-50 uppercase tracking-wide whitespace-nowrap">G.Alto</span>
            <input type="text" value={golaAltoColor} onChange={e => { setGolaAltoColor(e.target.value); setGolaAlto(true); }}
              className="flex-1 min-w-0 w-full px-1.5 py-0.5 bg-white rounded-md text-[10px] font-bold text-black placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-orange-300 disabled:opacity-50" placeholder="color…" disabled={!golaAlto} />
          </label>
          <label className="flex items-center gap-1 bg-white/10 rounded-lg pl-2 pr-1 py-0.5 ring-1 ring-white/25 flex-1 min-w-[7rem]">
            <input type="checkbox" checked={golaBajo} onChange={e => { setGolaBajo(e.target.checked); if (!e.target.checked) setGolaBajoColor(''); }} className="w-3 h-3 accent-white shrink-0" />
            <span className="text-[9px] font-black text-orange-50 uppercase tracking-wide whitespace-nowrap">G.Bajo</span>
            <input type="text" value={golaBajoColor} onChange={e => { setGolaBajoColor(e.target.value); setGolaBajo(true); }}
              className="flex-1 min-w-0 w-full px-1.5 py-0.5 bg-white rounded-md text-[10px] font-bold text-black placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-orange-300 disabled:opacity-50" placeholder="color…" disabled={!golaBajo} />
          </label>
        </div>
        )}
      </div>

      {/* ── Pestañas móviles: Catálogo / Presupuesto ── */}
      <div className="md:hidden shrink-0 flex border-b border-slate-200 bg-white sticky z-20" style={{ top: configCollapsed ? '52px' : '84px' }}>
        <button onClick={() => setMobileTab('catalog')}
          className={`flex-1 py-2.5 text-xs font-black uppercase flex items-center justify-center gap-1.5 transition-colors ${
            mobileTab === 'catalog' ? 'text-orange-700 border-b-2 border-orange-600 bg-orange-50/60' : 'text-slate-400'}`}>
          <Boxes size={14} /> Catálogo
        </button>
        <button onClick={() => setMobileTab('cart')}
          className={`flex-1 py-2.5 text-xs font-black uppercase flex items-center justify-center gap-1.5 transition-colors ${
            mobileTab === 'cart' ? 'text-orange-700 border-b-2 border-orange-600 bg-orange-50/60' : 'text-slate-400'}`}>
          <ShoppingCart size={14} /> Presupuesto {cart.length > 0 && <span className="bg-orange-600 text-white rounded-full px-1.5 py-0.5 text-[9px] ml-1">{cart.length}</span>}
        </button>
      </div>

      <div className="flex-1 flex flex-col md:flex-row overflow-hidden">
        {/* ── Catálogo ── */}
        <div className={`flex-1 flex flex-col md:flex-row overflow-hidden ${budgetExpanded ? 'hidden' : (mobileTab === 'cart' ? 'hidden md:flex' : 'flex')}`}>
          {/* Familias */}
          {familiesCollapsed ? (
            <div className="flex w-full md:w-10 shrink-0 bg-white/70 backdrop-blur border-b md:border-b-0 md:border-r border-slate-200 md:flex-col items-center py-2 md:py-3 px-2 md:px-0 justify-between md:justify-center">
              <p className="md:hidden text-[10px] font-black text-slate-400 uppercase flex items-center gap-1.5"><Layers size={12} /> Familias</p>
              <button onClick={() => setFamiliesCollapsed(false)} title="Mostrar familias"
                className="p-2 rounded-lg hover:bg-orange-50 text-orange-600">
                <PanelLeftOpen size={18} />
              </button>
            </div>
          ) : (
            <div className="w-full md:w-56 shrink-0 bg-white/70 backdrop-blur border-b md:border-b-0 md:border-r border-slate-200 overflow-y-auto max-h-[40vh] md:max-h-none relative"
              style={typeof window !== 'undefined' && window.innerWidth >= 768 ? { width: familiesWidth, maxWidth: familiesWidth } : undefined}
            >
              <div className="hidden md:block absolute top-0 right-0 w-1.5 h-full cursor-ew-resize hover:bg-orange-500/40 z-20"
                onMouseDown={() => { isResizingFamilies.current = true; }} />
              <div className="p-2.5">
                <div className="flex items-center justify-between px-2 py-1.5">
                  <p className="text-[10px] font-black text-slate-400 uppercase flex items-center gap-1.5"><Layers size={12} /> Familias</p>
                  <button onClick={() => setFamiliesCollapsed(true)} title="Ocultar familias"
                    className="text-slate-300 hover:text-orange-600">
                    <PanelLeftClose size={14} />
                  </button>
                </div>
                <div className="px-2 pb-2">
                  <input value={familyFilter} onChange={e => setFamilyFilter(e.target.value)}
                    placeholder="Filtrar categorías…"
                    className="w-full px-2.5 py-1.5 text-[11px] border border-slate-200 rounded-lg outline-none focus:border-orange-400 focus:ring-2 focus:ring-orange-100" />
                </div>
                <div className="flex md:flex-col gap-1.5 flex-wrap">
                  {familyGroups.map(g => {
                    const single = g.members.length === 1;
                    const empty = g.total === 0;  // familia creada pero sin productos aún
                    // Sub-familias = miembros del grupo distintos de la familia base (cuyo
                    // nombre coincide con la cabecera). Así "BAJO" no se repite dentro de "BAJO".
                    const hasBase = g.members.some(([n]) => n === g.key);
                    const subs = g.members.filter(([n]) => n !== g.key);
                    const expandable = !single && subs.length > 0;
                    const expanded = !!expandedGroups[g.key];
                    // Familia que selecciona la cabecera: el único miembro (single) o la base.
                    const headerFamily = single ? g.members[0][0] : (hasBase ? g.key : null);
                    const isHeaderActive = !!headerFamily && family === headerFamily;
                    const isActiveGroup = g.members.some(([n]) => n === family);
                    const toggleExpand = () => setExpandedGroups(p => ({ ...p, [g.key]: !p[g.key] }));
                    return (
                      <div key={g.key} className="md:w-full">
                        <button
                          title={empty ? 'Familia sin productos todavía (categoría creada)' : undefined}
                          onClick={() => {
                            if (headerFamily) { setFamily(headerFamily); setSearch(''); }
                            else if (expandable) toggleExpand();
                          }}
                          className={`w-full text-left px-3 py-2 rounded-xl text-xs font-bold flex justify-between items-center gap-2 transition-all whitespace-nowrap ${empty ? 'opacity-40' : ''} ${
                            isHeaderActive
                              ? 'bg-gradient-to-r from-orange-600 to-amber-600 text-white shadow-md shadow-orange-200'
                              : isActiveGroup ? 'bg-orange-50 text-orange-700' : 'text-slate-600 hover:bg-orange-50'}`}>
                          <span className="flex items-center gap-1.5 min-w-0">
                            <MuebleIcon type={classifyMueble({ category: g.members[0]?.[0] || g.key })} size={16} className="shrink-0" />
                            <span className="truncate">{single ? g.members[0][0] : g.label}</span>
                          </span>
                          <span className="flex items-center gap-1 shrink-0">
                            <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${
                              isHeaderActive ? 'bg-white/25' : 'bg-slate-100 text-slate-400'}`}>{g.total}</span>
                            {expandable && (
                              <span role="button" tabIndex={0} title={expanded ? 'Contraer' : 'Desplegar sub-familias'}
                                onClick={(e) => { e.stopPropagation(); toggleExpand(); }}
                                className="p-0.5 -m-0.5 rounded hover:bg-black/10 cursor-pointer">
                                {expanded ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
                              </span>
                            )}
                          </span>
                        </button>
                        {expandable && expanded && (
                          <div className="ml-3 mt-1 mb-1 flex md:flex-col gap-1 flex-wrap border-l-2 border-orange-100 pl-2">
                            {subs.map(([name, count]) => (
                              <button key={name} onClick={() => { setFamily(name); setSearch(''); }}
                                className={`text-left px-2.5 py-1.5 rounded-lg text-[11px] font-bold flex justify-between items-center gap-2 transition-all whitespace-nowrap ${
                                  family === name ? 'bg-orange-600 text-white' : 'text-slate-500 hover:bg-orange-50'}`}>
                                <span className="truncate">{name}</span>
                                <span className={`text-[9px] px-1.5 py-0.5 rounded-full ${
                                  family === name ? 'bg-white/25' : 'bg-slate-100 text-slate-400'}`}>{count}</span>
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
                {familyGroups.length === 0 && !loading && <p className="text-xs text-slate-400 px-3 py-2">Sin categorías</p>}
              </div>
            </div>
          )}

          {/* Listado de muebles */}
          <div className="flex-1 overflow-y-auto p-3 sm:p-5">
            <div className="mb-4 max-w-3xl">
              <div className="relative">
                <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-orange-500" />
                <input value={search} onChange={e => setSearch(e.target.value)} autoFocus
                  placeholder="Buscar en TODO el catálogo: código, nombre o medida (p. ej. «bajo 60» o «B60»)…"
                  className="w-full pl-11 pr-24 py-3 bg-white border-2 border-slate-200 rounded-2xl text-sm outline-none focus:border-orange-500 focus:ring-4 focus:ring-orange-100 shadow-sm transition-all" />
                {search && (
                  <button onClick={() => setSearch('')} title="Limpiar"
                    className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1 px-2.5 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-500 text-xs font-bold transition-colors">
                    <X size={13} /> Limpiar
                  </button>
                )}
              </div>

              {/* Modo de búsqueda + filtro de medida */}
              <div className="flex flex-wrap items-center gap-2 mt-2 px-1">
                <div className="flex items-center gap-1 bg-slate-100 rounded-lg p-0.5 text-[11px] font-bold">
                  <button onClick={() => setSearchScope('all')}
                    className={`px-2.5 py-1 rounded-md flex items-center gap-1 transition-colors ${
                      searchScope === 'all' ? 'bg-white shadow text-orange-700' : 'text-slate-500 hover:text-slate-700'}`}>
                    <Globe size={12} /> Todo el catálogo
                  </button>
                  <button onClick={() => setSearchScope('family')}
                    className={`px-2.5 py-1 rounded-md flex items-center gap-1 transition-colors ${
                      searchScope === 'family' ? 'bg-white shadow text-orange-700' : 'text-slate-500 hover:text-slate-700'}`}>
                    <Layers size={12} /> Solo esta familia
                  </button>
                </div>
                <div className="relative">
                  <Ruler size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input value={sizeFilter} onChange={e => setSizeFilter(e.target.value)} type="number" min="0"
                    placeholder={`Medida (${measureUnit})`}
                    className="w-28 pl-7 pr-2 py-1.5 text-[11px] border border-slate-200 rounded-lg outline-none focus:border-orange-400 focus:ring-2 focus:ring-orange-100" />
                </div>
                {sizeFilter && (
                  <button onClick={() => setSizeFilter('')}
                    className="text-[11px] text-slate-400 hover:text-red-500 flex items-center gap-0.5 font-bold">
                    <X size={11} /> quitar medida
                  </button>
                )}

                {/* Orden de resultados */}
                <div className="flex items-center gap-1 ml-auto">
                  <ArrowUpDown size={13} className="text-slate-400" />
                  <select value={sortBy} onChange={e => setSortBy(e.target.value)}
                    className="text-[11px] border border-slate-200 rounded-lg px-2 py-1.5 outline-none focus:border-orange-400 bg-white">
                    <option value="default">Orden por defecto</option>
                    <option value="code">Código</option>
                    <option value="name">Nombre</option>
                    <option value="width">Ancho</option>
                    <option value="height">Alto</option>
                    <option value="price">Precio</option>
                  </select>
                  {sortBy !== 'default' && (
                    <button onClick={() => setSortDir(d => d === 'asc' ? 'desc' : 'asc')} title="Invertir orden"
                      className="text-[11px] border border-slate-200 rounded-lg px-2 py-1.5 bg-white hover:bg-slate-50 font-bold text-slate-500">
                      {sortDir === 'asc' ? '↑' : '↓'}
                    </button>
                  )}
                </div>
              </div>

              {/* Estado de la búsqueda */}
              {!loading && (
                <div className="flex items-center gap-2 mt-2 px-1 text-[11px]">
                  {searching ? (
                    <span className="inline-flex items-center gap-1.5 font-bold text-orange-700">
                      <Search size={12} />
                      {sortedShown.length} resultado{sortedShown.length === 1 ? '' : 's'}
                      {searchScope === 'family' && family ? ` en ${family}` : ' en todo el catálogo'}
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1.5 text-slate-400 font-medium">
                      <Layers size={12} /> Mostrando familia <b className="text-slate-600 ml-0.5">{family || '—'}</b> · o escribe para buscar
                    </span>
                  )}
                </div>
              )}
            </div>

            {loading ? (
              <div className="flex flex-col items-center justify-center py-24 text-slate-400 gap-3">
                <Loader className="animate-spin" size={30} />
                <span className="text-sm">Cargando catálogo {libraryCode}…</span>
              </div>
            ) : catalogView === 'icons' ? (
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-2.5">
                {sortedShown.slice(0, 200).map(p => {
                  const added = inCart(p.id);
                  const med = [p.width && formatMeasure(p.width), p.heightLabel || (p.height && formatMeasure(p.height)), p.depth && formatMeasure(p.depth)].filter(Boolean).join('×');
                  return (
                    <button key={p.id} onClick={() => addToCart(p)}
                      className={`group text-center bg-white border rounded-2xl p-3 flex flex-col items-center gap-1.5 transition-all hover:shadow-md ${
                        added ? 'border-orange-300 ring-1 ring-orange-200' : 'border-slate-200 hover:border-orange-300'}`}>
                      <div className={`shrink-0 w-16 h-16 rounded-xl flex items-center justify-center border ${
                        added ? 'bg-orange-50 border-orange-200 text-orange-600' : 'bg-slate-50 border-slate-200 text-slate-500 group-hover:text-orange-600 group-hover:border-orange-200'}`}>
                        <MuebleIcon mueble={p} size={36} />
                      </div>
                      <span className="font-mono text-[10px] font-bold text-indigo-600 bg-indigo-50 px-1.5 py-0.5 rounded truncate max-w-full">{p.reference || p.code || '—'}</span>
                      <p className="text-[11px] font-bold text-slate-700 leading-tight line-clamp-2">{p.name}</p>
                      {med && <p className="text-[10px] text-slate-400">{med} {measureUnit}</p>}
                      <p className="font-mono font-black text-orange-700 text-sm">{eur(displayPrice(priceOf(p)))}</p>
                      {added && <span className="text-[9px] font-black text-orange-600 flex items-center gap-0.5"><CheckCircle2 size={11} /> añadido</span>}
                    </button>
                  );
                })}
                {sortedShown.length === 0 && (
                  <div className="col-span-full py-16 text-center text-slate-400">
                    <Boxes size={40} className="mx-auto mb-2 opacity-40" />
                    <p className="text-sm">Sin muebles en esta familia</p>
                  </div>
                )}
                {sortedShown.length > 120 && (
                  <p className="col-span-full text-center text-xs text-slate-400 py-2">Mostrando 200 de {sortedShown.length} — usa el buscador para filtrar</p>
                )}
              </div>
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-2.5">
                {sortedShown.slice(0, 200).map(p => {
                  const added = inCart(p.id);
                  const med = [p.width && formatMeasure(p.width), p.heightLabel || (p.height && formatMeasure(p.height)), p.depth && formatMeasure(p.depth)].filter(Boolean).join('×');
                  return (
                    <button key={p.id} onClick={() => addToCart(p)}
                      className={`group text-left bg-white border rounded-2xl p-3 flex items-center gap-3 transition-all hover:shadow-md ${
                        added ? 'border-orange-300 ring-1 ring-orange-200' : 'border-slate-200 hover:border-orange-300'}`}>
                      {/* Dibujo/icono del mueble según su familia */}
                      <div className={`shrink-0 w-11 h-11 rounded-xl flex items-center justify-center border ${
                        added ? 'bg-orange-50 border-orange-200 text-orange-600' : 'bg-slate-50 border-slate-200 text-slate-500 group-hover:text-orange-600 group-hover:border-orange-200'}`}>
                        <MuebleIcon mueble={p} size={26} />
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-1.5 flex-wrap">
                          <span className="font-mono text-[10px] font-bold text-indigo-600 bg-indigo-50 px-1.5 py-0.5 rounded">{p.reference || p.code || '—'}</span>
                          {(searching || familiesCollapsed) && p.category && (
                            <span className="text-[9px] font-bold text-orange-700 bg-orange-50 px-1.5 py-0.5 rounded uppercase tracking-wide">{p.category}</span>
                          )}
                          {added && <span className="text-[9px] font-black text-orange-600 flex items-center gap-0.5"><CheckCircle2 size={11} /> añadido</span>}
                        </div>
                        <p className="text-sm font-bold text-slate-800 truncate mt-1">{p.name}</p>
                        {med && <p className="text-[11px] text-slate-400">{med} {measureUnit}</p>}
                      </div>
                      <div className="text-right shrink-0">
                        <p className="font-mono font-black text-orange-700 text-sm whitespace-nowrap">{eur(displayPrice(priceOf(p)))}</p>
                        {showDistributorPrice && discountPct > 0 && (
                          <p className="text-[9px] text-slate-400 line-through">{eur(priceOf(p))}</p>
                        )}
                        <span className="inline-flex items-center gap-1 mt-1 px-2 py-1 bg-orange-600 group-hover:bg-orange-700 text-white rounded-lg text-[11px] font-bold">
                          <Plus size={12} /> Añadir
                        </span>
                      </div>
                    </button>
                  );
                })}
                {sortedShown.length === 0 && (
                  <div className="col-span-full py-16 text-center text-slate-400">
                    <Boxes size={40} className="mx-auto mb-2 opacity-40" />
                    <p className="text-sm">Sin muebles en esta familia</p>
                  </div>
                )}
                {sortedShown.length > 120 && (
                  <p className="col-span-full text-center text-xs text-slate-400 py-2">Mostrando 200 de {sortedShown.length} — usa el buscador para filtrar</p>
                )}
              </div>
            )}
          </div>
        </div>

        {/* ── Presupuesto / Carrito ── */}
        {cartCollapsed ? (
          <div className="hidden md:flex w-10 shrink-0 border-l border-slate-200 bg-white flex-col items-center py-3 gap-2">
            <button onClick={() => setCartCollapsed(false)} title="Mostrar presupuesto"
              className="p-2 rounded-lg hover:bg-orange-50 text-orange-600">
              <PanelRightOpen size={18} />
            </button>
            {cart.length > 0 && (
              <span className="text-[10px] font-black text-orange-600 bg-orange-50 rounded-full px-1.5 py-0.5">{cart.length}</span>
            )}
          </div>
        ) : (
          <div className={`${budgetExpanded ? 'w-full md:flex-1' : 'w-full md:w-[26rem] shrink-0'} bg-white border-t md:border-t-0 md:border-l border-slate-200 flex-col shadow-[-4px_0_20px_rgba(0,0,0,0.03)] relative ${
            mobileTab === 'catalog' ? 'hidden md:flex' : 'flex'}`}
            style={!budgetExpanded && typeof window !== 'undefined' && window.innerWidth >= 768 ? { width: cartWidth, maxWidth: cartWidth } : undefined}
          >
            <div className={`${budgetExpanded ? 'hidden' : 'hidden md:block'} absolute top-0 left-0 w-1.5 h-full cursor-ew-resize hover:bg-orange-500/40 z-20`}
              onMouseDown={() => { isResizingCart.current = true; }} />
            {/* Module tabs */}
            <div className="flex bg-slate-100 shrink-0">
              <button onClick={() => setActiveModule('montada')}
                className={`flex-1 py-2 text-[10px] font-black uppercase tracking-wide flex items-center justify-center gap-1 transition-all ${
                  activeModule === 'montada' ? 'bg-orange-600 text-white shadow-inner' : 'text-slate-500 hover:bg-white/60'}`}>
                <Home size={11} /> Cocina Montada
              </button>
              <button onClick={() => { setActiveModule('despiece'); if (cart.length > 0) openDespiece(); }}
                className={`flex-1 py-2 text-[10px] font-black uppercase tracking-wide flex items-center justify-center gap-1 transition-all ${
                  activeModule === 'despiece' ? 'bg-indigo-700 text-white shadow-inner' : 'text-slate-500 hover:bg-white/60'}`}>
                <Scissors size={11} /> Despiece
              </button>
              <button onClick={() => setBudgetExpanded(v => !v)} title={budgetExpanded ? 'Volver a ver los muebles' : 'Ver el presupuesto en grande (ocultar muebles)'}
                className="hidden md:flex items-center px-2 text-slate-400 hover:text-orange-600">
                {budgetExpanded ? <Minimize2 size={15} /> : <Maximize2 size={15} />}
              </button>
              {!budgetExpanded && (
                <button onClick={() => setCartCollapsed(true)} title="Ocultar presupuesto"
                  className="hidden md:flex items-center px-2 text-slate-400 hover:text-orange-600">
                  <PanelRightClose size={15} />
                </button>
              )}
            </div>

            <div className="px-3 py-2 border-b border-slate-100 flex items-center gap-2 bg-slate-50/60">
              <div className="w-7 h-7 bg-orange-100 rounded-lg flex items-center justify-center"><ShoppingCart size={14} className="text-orange-600" /></div>
              <div>
                <h3 className="font-black text-slate-800 text-xs uppercase leading-none">Presupuesto</h3>
                <p className="text-[9px] text-slate-400 mt-0.5">{cart.length} líneas · {totalUds} ud.</p>
              </div>
              <div className="ml-auto flex items-center gap-2">
                {cart.length > 0 && (
                  <button onClick={() => { if (window.confirm('¿Vaciar todo el presupuesto?')) setCart([]); }}
                    className="text-[11px] font-bold text-slate-400 hover:text-red-500 flex items-center gap-1">
                    <X size={13} /> Vaciar
                  </button>
                )}
              </div>
            </div>

            {/* Notas */}
            <div className="px-4 py-3 border-b border-slate-100 space-y-2 bg-slate-50/30">
              <input value={notes} onChange={e => setNotes(e.target.value)} placeholder="📝 Notas / observaciones…"
                className="w-full px-3 py-2 border border-slate-200 rounded-xl text-xs focus:outline-none focus:border-orange-500 focus:ring-2 focus:ring-orange-100" />
            </div>

            {/* Líneas */}
            <div ref={cartListRef} className="flex-1 overflow-y-auto px-3 py-2">
              {cart.length === 0 && (
                <div className="flex flex-col items-center justify-center h-full text-center text-slate-300 py-10">
                  <Receipt size={44} className="mb-2 opacity-50" />
                  <p className="text-sm font-bold text-slate-400">El presupuesto está vacío</p>
                  <p className="text-xs text-slate-300 mt-1">Pulsa un mueble del catálogo para añadirlo</p>
                </div>
              )}
              <div className="space-y-2">
                {cart.map(it => (
                  <div key={it.id} className="bg-white border border-slate-200 rounded-xl p-1.5 hover:border-orange-200 transition-colors">
                    <div className="flex items-start gap-2">
                      {!it.manual && (
                        <div className="shrink-0 w-7 h-7 rounded-lg bg-orange-50 border border-orange-100 text-orange-600 flex items-center justify-center mt-0.5">
                          <MuebleIcon type={classifyMueble({ code: it.code, name: it.name })} size={17} />
                        </div>
                      )}
                      <div className="min-w-0 flex-1">
                        <p className="font-bold text-slate-800 text-xs leading-tight">{it.name}</p>
                        <p className="text-[9px] text-slate-400 font-mono mt-0.5">{it.code}{it.manual ? ' · manual' : ''}</p>
                      </div>
                      <button onClick={() => removeItem(it.id)} className="text-slate-300 hover:text-red-500 shrink-0"><Trash2 size={13} /></button>
                    </div>
                    <div className="flex items-center justify-between mt-1.5">
                      <div className="flex items-center gap-1 bg-slate-100 rounded-lg p-0.5">
                        <button onClick={() => setQty(it.id, -1)} className="w-6 h-6 rounded-md bg-white hover:bg-slate-50 flex items-center justify-center shadow-sm active:scale-95 transition"><Minus size={12} /></button>
                        <input type="number" min="1" value={it.qty} onChange={e => setQtyValue(it.id, e.target.value)} onFocus={e => e.target.select()}
                          className="w-9 h-6 text-center font-black text-sm bg-white rounded-md shadow-sm border-0 focus:outline-none focus:ring-1 focus:ring-orange-400 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none" />
                        <button onClick={() => setQty(it.id, 1)} className="w-6 h-6 rounded-md bg-white hover:bg-slate-50 flex items-center justify-center shadow-sm active:scale-95 transition"><Plus size={12} /></button>
                      </div>
                      <div className="flex items-center gap-2">
                        {it.manual ? (
                          <input value={it.price} onChange={e => updateItemPrice(it.id, e.target.value)} type="number" step="0.01"
                            className="w-16 text-right text-[11px] px-1.5 py-1 border border-amber-200 bg-amber-50 rounded-md font-mono" />
                        ) : (
                          <span className="font-mono text-[11px] text-slate-400">{eur(displayPrice(unitFull(it)))}/ud</span>
                        )}
                        <span className="font-mono font-black text-orange-700 text-sm w-20 text-right">{eur(lineTotal(it))}</span>
                      </div>
                    </div>
                    {!it.manual && (() => {
                      const prod = products.find(p => p.id === it.id);
                      const ow = prod?.width, oh = prod?.height, od = prod?.depth;
                      const dims = [
                        { lbl: 'An', field: 'customWidth', val: it.customWidth, orig: ow },
                        { lbl: 'Al', field: 'customHeight', val: it.customHeight, orig: oh },
                        { lbl: 'Fo', field: 'customDepth', val: it.customDepth, orig: od },
                      ];
                      const vigaInc = Number(libraryVigaCutIncrements?.[libraryCode]) || 0;
                      const flat = isFlatPanel(prod?.category);
                      return (
                        <div className="flex items-center gap-1.5 mt-1 pt-1 border-t border-slate-100 flex-wrap">
                          {dims.map(d => {
                            const changed = d.val !== '' && d.val != null && Number(d.val) !== Number(d.orig);
                            return (
                              <label key={d.field} className="flex items-center gap-1" title={`Original: ${d.orig ?? '–'} ${measureUnit}`}>
                                <span className="text-[10px] font-black text-slate-400 uppercase">{d.lbl}</span>
                                <input type="number" step="0.1" value={d.val ?? ''}
                                  onChange={e => setItemDim(it.id, d.field, e.target.value)}
                                  className={`w-12 px-1 py-1 text-xs font-bold text-center rounded-md border outline-none ${
                                    changed ? 'border-orange-500 text-orange-600 bg-orange-50' : 'border-slate-200 text-slate-600'}`} />
                              </label>
                            );
                          })}
                          {!flat && (
                            <button onClick={() => toggleViga(it.id)} title={`Corte de viga${vigaInc ? ` (+${vigaInc}€)` : ''}`}
                              className={`px-1.5 py-0.5 rounded-md text-[9px] font-black uppercase border transition-colors ${
                                it.hasVigaCut ? 'bg-orange-600 text-white border-orange-600' : 'bg-white text-slate-500 border-slate-200 hover:bg-slate-50'}`}>
                              Viga
                            </button>
                          )}
                        </div>
                      );
                    })()}
                    {(
                      <div className="flex items-center gap-1.5 mt-1 pt-1 border-t border-slate-100">
                        {String(it.code || '').includes('D/I') && (
                          <div className="flex items-center gap-1 bg-slate-100 rounded-lg p-0.5">
                            {['D', 'I'].map(h => (
                              <button key={h} onClick={() => setItemHand(it.id, h)}
                                title={h === 'D' ? 'Apertura Derecha' : 'Apertura Izquierda'}
                                className={`w-6 h-6 rounded-md text-[11px] font-black transition-colors ${
                                  it.hand === h ? 'bg-orange-600 text-white shadow-sm' : 'bg-white hover:bg-slate-50 text-slate-500'}`}>
                                {h}
                              </button>
                            ))}
                          </div>
                        )}
                        <input value={it.notes || ''} onChange={e => setItemNotes(it.id, e.target.value)}
                          placeholder="Observación (p.ej. pendiente confirmar apertura)…"
                          className="flex-1 min-w-0 px-2 py-1 text-[10px] border border-slate-200 rounded-lg outline-none focus:border-orange-400" />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Línea manual */}
            {showManual && (
              <div className="px-4 py-2.5 border-t border-amber-100 bg-amber-50">
                <p className="text-[10px] font-black text-amber-700 uppercase mb-1.5 flex items-center gap-1"><Edit3 size={11} /> Añadir línea manual</p>
                <div className="flex gap-1.5 items-end">
                  <input value={manualLine.name} onChange={e => setManualLine(p => ({ ...p, name: e.target.value }))} placeholder="Concepto…"
                    className="flex-1 px-2 py-1.5 border border-amber-200 rounded-lg text-xs" />
                  <input value={manualLine.price} onChange={e => setManualLine(p => ({ ...p, price: e.target.value }))} placeholder="€" type="number" step="0.01"
                    className="w-20 px-2 py-1.5 border border-amber-200 rounded-lg text-xs text-right" />
                  <input value={manualLine.qty} onChange={e => setManualLine(p => ({ ...p, qty: e.target.value }))} placeholder="Ud" type="number" min="1"
                    className="w-12 px-2 py-1.5 border border-amber-200 rounded-lg text-xs text-center" />
                  <button onClick={addManualLine} className="px-2.5 py-1.5 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-xs font-bold"><Plus size={12} /></button>
                </div>
              </div>
            )}

            {/* Totales + acciones — barra inferior plegable (libera espacio para la lista) */}
            <div className="border-t border-slate-200 bg-gradient-to-b from-white to-slate-50 shrink-0">
              {actionsCollapsed ? (
                <div className="flex items-center gap-2 px-3 py-2">
                  <button onClick={() => setActionsCollapsed(false)} title="Mostrar totales y acciones"
                    className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-500 shrink-0">
                    <ChevronUp size={16} />
                  </button>
                  <div className="flex flex-col leading-none">
                    <span className="text-[8px] uppercase text-slate-400 font-bold">Total c/IVA</span>
                    <span className="text-lg font-black text-orange-600">{eur(totalConIva)}</span>
                  </div>
                  <button onClick={() => { if (cart.length === 0) { alert('Añade al menos una línea'); return; } setShowConfirmOrder(true); }}
                    disabled={cart.length === 0}
                    className="ml-auto py-2.5 px-4 bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-200 disabled:text-slate-400 rounded-xl text-xs font-black text-white flex items-center justify-center gap-2 transition-all shadow-md shadow-emerald-200 uppercase tracking-wider">
                    <PackageCheck size={15} /> Confirmar
                  </button>
                </div>
              ) : (
                <div className="p-4 space-y-3">
                  <button onClick={() => setActionsCollapsed(true)} title="Ocultar totales y acciones (más espacio para la lista)"
                    className="w-full flex items-center justify-center gap-1 text-[10px] font-black uppercase text-slate-400 hover:text-slate-600">
                    <ChevronDown size={14} /> Ocultar totales y acciones
                  </button>
                  <div className="rounded-2xl bg-slate-900 text-white p-4">
                    <div className="flex justify-between text-xs text-slate-300 mb-1">
                      <span>Base imponible</span><span className="font-mono">{eur(cartTotal)}</span>
                    </div>
                    <div className="flex justify-between text-xs text-slate-300 mb-2">
                      <span>IVA ({ivaRate}%)</span><span className="font-mono">{eur(ivaAmount)}</span>
                    </div>
                    <div className="flex justify-between items-center pt-2 border-t border-white/10">
                      <span className="text-xs font-black uppercase text-orange-300 flex items-center gap-1"><Sparkles size={13} /> Total</span>
                      <span className="text-2xl font-black text-orange-400">{eur(totalConIva)}</span>
                    </div>
                  </div>

                  {/* Confirmar Pedido — acción principal */}
                  <button onClick={() => { if (cart.length === 0) { alert('Añade al menos una línea'); return; } setShowConfirmOrder(true); }}
                    disabled={cart.length === 0}
                    className="w-full py-3.5 bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-200 disabled:text-slate-400 rounded-xl text-xs font-black text-white flex items-center justify-center gap-2 transition-all shadow-md shadow-emerald-200 uppercase tracking-wider border-2 border-emerald-400 disabled:border-slate-200">
                    <PackageCheck size={16} /> Confirmar Pedido
                  </button>

                  <div className="grid grid-cols-2 gap-2">
                    <button onClick={() => setShowManual(!showManual)}
                      className="py-2.5 bg-amber-100 hover:bg-amber-200 rounded-xl text-xs font-bold text-amber-700 flex items-center justify-center gap-1.5 transition-colors">
                      <Edit3 size={13} /> Línea manual
                    </button>
                    <button onClick={saveOrder} disabled={saving || cart.length === 0}
                      className="py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-200 disabled:text-slate-400 rounded-xl text-xs font-bold text-white flex items-center justify-center gap-1.5 transition-all shadow-sm">
                      {saving ? <Loader size={13} className="animate-spin" /> : saved ? <CheckCircle2 size={13} /> : <Save size={13} />}
                      {saving ? 'Guardando…' : saved ? '¡Guardado!' : 'Guardar'}
                    </button>
                    <button onClick={() => exportPDF(true)} disabled={cart.length === 0}
                      className="py-2.5 bg-gradient-to-r from-purple-600 to-fuchsia-600 hover:from-purple-700 hover:to-fuchsia-700 disabled:from-slate-200 disabled:to-slate-200 disabled:text-slate-400 rounded-xl text-xs font-bold text-white flex items-center justify-center gap-1.5 transition-all shadow-sm">
                      <FileDown size={13} /> Exportar PDF
                    </button>
                    <button onClick={handlePrint} disabled={cart.length === 0}
                      className="py-2.5 bg-slate-100 hover:bg-slate-200 disabled:bg-slate-50 disabled:text-slate-300 rounded-xl text-xs font-bold text-slate-700 flex items-center justify-center gap-1.5 transition-colors">
                      <Printer size={13} /> Imprimir
                    </button>
                    <button onClick={() => exportPDF(false)} disabled={cart.length === 0}
                      className="col-span-2 py-2.5 bg-white border-2 border-purple-200 hover:bg-purple-50 disabled:border-slate-100 disabled:text-slate-300 rounded-xl text-xs font-bold text-purple-700 flex items-center justify-center gap-1.5 transition-all shadow-sm">
                      <FileDown size={13} /> PDF sin precios (no valorado)
                    </button>
                  </div>
                  {currentUser?.canViewTechnicalDespiece && (
                    <button onClick={openDespiece} disabled={cart.length === 0}
                      className="w-full py-2.5 bg-orange-600 hover:bg-orange-700 disabled:bg-slate-100 disabled:text-slate-300 rounded-xl text-xs font-black text-white flex items-center justify-center gap-1.5 transition-colors uppercase tracking-wider">
                      <Scissors size={14} /> Generar despiece
                    </button>
                  )}
                  {render3dImage && (
                    <div className="flex items-center gap-2 p-2 rounded-lg bg-green-50 border border-green-200">
                      <img src={render3dImage} alt="Render 3D" className="w-12 h-8 object-cover rounded" />
                      <span className="text-[10px] font-bold text-green-700 flex-1">Render 3D adjunto (se incluirá en el PDF)</span>
                      <button onClick={() => setRender3dImage(null)} className="text-red-400 hover:text-red-600"><X size={12} /></button>
                    </div>
                  )}
                  <p className="text-[10px] text-center text-slate-400">PDF con formato Luiggi Home · se guarda como presupuesto</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Botón flotante móvil: Confirmar Pedido (solo visible en pestaña Catálogo con items) */}
      {mobileTab === 'catalog' && cart.length > 0 && (
        <div className="md:hidden fixed bottom-4 right-4 z-40 flex flex-col items-end gap-2">
          <button
            onClick={() => setShowConfirmOrder(true)}
            className="flex items-center gap-2 px-4 py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-2xl font-black text-xs uppercase tracking-wider shadow-xl border-2 border-emerald-400">
            <PackageCheck size={16} /> Confirmar Pedido
            <span className="bg-white/25 rounded-full px-2 py-0.5 text-[10px]">{eur(totalConIva)}</span>
          </button>
          <button
            onClick={() => setMobileTab('cart')}
            className="flex items-center gap-2 px-3 py-2 bg-slate-800/90 text-white rounded-xl font-bold text-xs shadow-lg">
            <ShoppingCart size={13} /> Ver presupuesto ({cart.length})
          </button>
        </div>
      )}

      {showNomenclatura && (
        <div className="fixed inset-0 z-[80] bg-black/50 flex items-center justify-center p-4" onClick={() => setShowNomenclatura(false)}>
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-3xl max-h-[88vh] flex flex-col overflow-hidden" onClick={e => e.stopPropagation()}>
            <div className="px-5 py-3.5 bg-gradient-to-r from-orange-700 to-amber-600 text-white flex items-center gap-2 shrink-0">
              <BookOpen size={18} />
              <h3 className="font-black uppercase text-sm tracking-tight">Nomenclatura de muebles MV</h3>
              <button onClick={() => setShowNomenclatura(false)} className="ml-auto hover:bg-white/15 rounded-lg p-1"><X size={18} /></button>
            </div>
            <div className="overflow-y-auto p-5 space-y-5">
              {NOMENCLATURA.map(g => (
                <div key={g.grupo}>
                  <p className="text-[11px] font-black text-orange-700 uppercase tracking-widest mb-2 border-b border-orange-100 pb-1">{g.grupo}</p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {g.items.map(it => (
                      <div key={it.code} className="flex items-center gap-3 p-2 rounded-xl border border-slate-100 hover:border-orange-200 hover:bg-orange-50/40">
                        <div className="shrink-0 w-9 h-9 rounded-lg bg-slate-50 border border-slate-200 text-slate-500 flex items-center justify-center">
                          <MuebleIcon type={it.type} size={22} />
                        </div>
                        <div className="min-w-0">
                          <p className="font-mono font-bold text-indigo-600 text-xs">{it.code}</p>
                          <p className="text-[11px] text-slate-600 leading-tight">{it.desc}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
              <div className="bg-slate-50 rounded-xl p-3 border border-slate-200">
                <p className="text-[11px] font-black text-slate-500 uppercase mb-1.5">Sufijos</p>
                <ul className="text-[11px] text-slate-600 space-y-0.5 list-disc pl-4">
                  {NOMENCLATURA_NOTAS.map((n, i) => <li key={i}>{n}</li>)}
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}

      <DespieceModal
        isOpen={showDespiece}
        onClose={() => setShowDespiece(false)}
        items={despieceItems}
        catalogs={[{ id: libraryCode, products }]}
        carcassMaterialName={carcassMaterials.find(m => m.id === selectedCarcassMaterialId)?.name || 'Melamina Blanca'}
        carcassBackThickness={8}
        customerName={clientName}
        projectReference={budgetReference || `Presupuesto ${libraryCode} (${levelLabel} ${tariff})`}
        expedientNumber={getBudgetNumber()}
        doorColorLow={doorColorLow}
        doorColorHigh={doorColorHigh}
        doorColorColumns={doorColorColumns}
        sideColor={sideColor}
        doorHasVeta={doorHasVeta}
        doorToleranceHeight={2}
        doorToleranceWidth={3}
        canSeeCost={currentUser?.isAdmin === true || currentUser?.canSeeCost === true}
      />

      <ConfirmOrderModal
        isOpen={showConfirmOrder}
        onClose={() => setShowConfirmOrder(false)}
        budgetNumber={getBudgetNumber()}
        customerName={clientName || currentUser?.clientName || 'Sin cliente'}
        total={totalConIva}
        orderEmail={orderEmail}
        setOrderEmail={setOrderEmail}
        orderNotes={orderNotes}
        setOrderNotes={setOrderNotes}
        orderAttachments={orderAttachments}
        setOrderAttachments={setOrderAttachments}
        isSendingOrder={isSendingOrder}
        orderSent={orderSent}
        onConfirm={handleConfirmOrder}
      />
    </div>
  );
};

export default Presupuestador2;
