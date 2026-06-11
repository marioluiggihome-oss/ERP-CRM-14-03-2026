import React, { useState, useEffect, useMemo, useRef, lazy, Suspense } from 'react';
import GlobalEventReminder from './components/GlobalEventReminder';
import { ShoppingCart, Settings, LogOut, FolderOpen, Sparkles, ShieldCheck, FileText, Loader, HardDrive, Users, Target, LayoutDashboard, CalendarDays, ScanLine, Wrench, Building2, Box, Factory, HelpCircle, ShoppingBag, Receipt, Shield, Image, TrendingUp, Layers } from 'lucide-react';
import "./App.css";

// ─── Lazy Loading: componentes pesados se cargan bajo demanda ───────────────
// Esto reduce el bundle inicial de ~1.5MB a ~400KB (solo Login + shell)
const BudgetTable = lazy(() => import('./components/BudgetTable'));
const Presupuestador2 = lazy(() => import('./components/Presupuestador2'));
const Visualizer = lazy(() => import('./components/Visualizer'));
const ProjectLibrary = lazy(() => import('./components/ProjectLibrary'));
const Invoices = lazy(() => import('./components/Invoices'));
const CommandCenter = lazy(() => import('./components/CommandCenter'));
const SettingsModal = lazy(() => import('./components/SettingsModal'));
const ManufacturingReport = lazy(() => import('./components/ManufacturingReport'));
const CRMLayout = lazy(() => import('./components/CRMLayout'));
const Digitalizador = lazy(() => import('./components/Digitalizador'));
const AgendaMontajes = lazy(() => import('./components/AgendaMontajes'));
const AdminWorkView = lazy(() => import('./components/AdminWorkView'));
const CommercialWorkView = lazy(() => import('./components/CommercialWorkView'));
const PrescriptorAgenda = lazy(() => import('./components/PrescriptorAgenda'));
const Armarios = lazy(() => import('./components/Armarios'));
const PortalFabrica = lazy(() => import('./components/PortalFabrica'));
const UserManualModal = lazy(() => import('./components/UserManualModal'));
const MisPedidos = lazy(() => import('./components/MisPedidos'));
const BackupManager = lazy(() => import('./components/BackupManager'));
const AIRenderStudio = lazy(() => import('./components/AIRenderStudio'));
const RentabilidadPanel = lazy(() => import('./components/RentabilidadPanel'));
const GestionGastos = lazy(() => import('./components/GestionGastos'));
const LuiggiFloor = lazy(() => import('./components/LuiggiFloor'));
const ReportGenerator = lazy(() => import('./components/ReportGenerator'));

// ─── Carga directa: componentes ligeros necesarios al inicio ────────────────
import Login from './components/Login';
import WelcomeScreen from './components/WelcomeScreen';
import MaintenanceScreen from './components/MaintenanceScreen';
import MaintenancePanel from './components/MaintenancePanel';
import { authAPI, productsAPI, materialsAPI, settingsAPI, usersAPI, librariesAPI } from './services/api';
import { logout as authLogout, getUser, clearTokens, isAuthenticated } from './services/authService';
import { DOOR_FINISHES, INITIAL_CARCASS_MATERIALS, DEFAULT_BRAND_COLOR, STORAGE_KEY } from './constants';
import { initSecurityGuard } from './utils/securityGuard';

const API_URL = process.env.REACT_APP_BACKEND_URL;

class ErrorBoundary extends React.Component {
  constructor(props) { super(props); this.state = { hasError: false, error: null }; }
  static getDerivedStateFromError(error) { return { hasError: true, error }; }
  componentDidCatch(error, info) {
    // Surfacing real para diagnosticar "pantallas en blanco": deja el error y el stack en consola
    console.error('[ErrorBoundary] Módulo falló al renderizar:', error, info?.componentStack);
  }
  render() {
    if (this.state.hasError) {
      return (
        <div className="h-full flex items-center justify-center bg-slate-50 p-8">
          <div className="text-center">
            <p className="text-2xl mb-2">⚠️</p>
            <p className="font-black text-slate-700 text-sm uppercase">Error al cargar el módulo</p>
            <p className="text-xs text-slate-400 mt-2 font-mono">{this.state.error?.message}</p>
            <button onClick={() => this.setState({ hasError: false })} 
              className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-xl text-xs font-black">
              Reintentar
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

const APP_VERSION = 'v4.2-crm-paginacion-presup2';

const App = () => {
  const [isManufacturingView, setIsManufacturingView] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isInMaintenance, setIsInMaintenance] = useState(false);
  const [showMaintenancePanel, setShowMaintenancePanel] = useState(false);
  const [showAdminWorkView, setShowAdminWorkView] = useState(false);
  const [showCommercialWorkView, setShowCommercialWorkView] = useState(false);
  const [showUserManual, setShowUserManual] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(() => {
    // Abierto por defecto en desktop (≥768px), cerrado en móvil
    if (typeof window !== 'undefined') {
      return window.innerWidth >= 768;
    }
    return true;
  }); // toggle plegable en desktop y móvil
  
  const [state, setState] = useState(() => {
    const defaultState = {
      currentUser: null,
      currentModule: 'montada', 
      currentTab: 'budget', 
      currentLibrary: 'ZC', // Biblioteca activa (ZC, MV, etc.)
      allowedLibraries: ['ZC'], // Bibliotecas permitidas para el usuario actual
      libraries: [], // Lista de bibliotecas con sus pointValues
      uploadedImages: [], 
      budgetItemsMontada: [], 
      budgetItemsDespiece: [], 
      projects: [], 
      globalFinish: DOOR_FINISHES[0].name, 
      carcassMaterials: INITIAL_CARCASS_MATERIALS,
      selectedCarcassMaterialId: INITIAL_CARCASS_MATERIALS[0].id,
      doorColorLow: '', doorColorHigh: '', doorColorColumns: '', sideColor: '',
      doorHasVeta: false, // Por defecto las puertas SIN veta
      // Tolerancias de puertas (en mm)
      doorToleranceHeight: 2, // Tolerancia alto puerta (mm)
      doorToleranceWidth: 3,  // Tolerancia ancho puerta (mm)
      // Opciones GOLA (perfiles)
      golaAlto: false, golaAltoColor: '',
      golaBajo: false, golaBajoColor: '',
      pointValueMontada: 1.0, pointValueDespiece: 0.88,
      // Valor de punto por biblioteca (para montada)
      libraryPointValues: { ZC: 1.0, MV: 1.0 },
      // Incrementos muebles especiales GLOBALES (legacy)
      specialIncrementWidth: 45,
      specialIncrementHeight: 45,
      specialIncrementDepth: 45,
      // Incrementos muebles especiales POR BIBLIOTECA
      librarySpecialIncrements: {
        ZC: { width: 45, height: 45, depth: 45 },
        MV: { width: 45, height: 45, depth: 45 }
      },
      // Corte de viga POR BIBLIOTECA
      libraryVigaCutIncrements: {
        ZC: 0,
        MV: 0
      },
      ivaRate: 21, // IVA editable (por defecto 21%)
      catalogs: [
        { id: 'cat-m-base', name: 'Cocina Montada Luiggi', manufacturer: 'Luiggi', products: [], module: 'montada' },
        { id: 'cat-d-base', name: 'Despiece Luiggi', manufacturer: 'Luiggi', products: [], module: 'despiece' }
      ], 
      activeCatalogIds: ['cat-m-base', 'cat-d-base'],
      users: [],
      customerName: '', customerAddress: '', 
      clientCode: '',  // Código de cliente para agrupar presupuestos
      budgetNumber: `EXP-2026-001`, 
      internalReference: '', logo: null,
      showDistributorPrice: false, showSettings: false,
      budgetCount: 0,
      brandColor: DEFAULT_BRAND_COLOR
    };

    // Load budget items from localStorage (these stay local)
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        return { 
          ...defaultState,
          budgetItemsMontada: parsed.budgetItemsMontada || [],
          budgetItemsDespiece: parsed.budgetItemsDespiece || [],
          projects: parsed.projects || [],
          customerName: parsed.customerName || '',
          customerAddress: parsed.customerAddress || '',
          clientCode: parsed.clientCode || '',
          budgetNumber: parsed.budgetNumber || 'EXP-2026-001',
          internalReference: parsed.internalReference || '',
          budgetCount: parsed.budgetCount || 0
        };
      }
    } catch (e) {
      console.error("Error loading local data:", e);
    }
    return defaultState;
  });

  // Load data from API on mount
  useEffect(() => {
    // Inicializar protección de seguridad
    initSecurityGuard();
    
    const loadData = async () => {
      try {
        // Init admin if needed
        await authAPI.init().catch(() => {});
        
        // Load users, products, materials, settings with timeout
        const fetchWithTimeout = async (promise, timeout = 10000) => {
          const timeoutPromise = new Promise((_, reject) => 
            setTimeout(() => reject(new Error('Timeout')), timeout)
          );
          return Promise.race([promise, timeoutPromise]);
        };

        const results = await Promise.allSettled([
          fetchWithTimeout(usersAPI.getAll()),
          fetchWithTimeout(productsAPI.getAll('montada', 'ZC')), // Filtrar por biblioteca ZC
          fetchWithTimeout(productsAPI.getAll('despiece', 'ZC')),
          fetchWithTimeout(materialsAPI.getAll()),
          fetchWithTimeout(settingsAPI.get()),
          fetchWithTimeout(librariesAPI.getAll()), // Cargar bibliotecas con sus pointValues
          fetchWithTimeout(productsAPI.getAll('montada')), // TODOS los productos montada para inventario
        ]);

        const users = results[0].status === 'fulfilled' ? results[0].value : [];
        const productsMontada = results[1].status === 'fulfilled' ? results[1].value : [];
        const productsDespiece = results[2].status === 'fulfilled' ? results[2].value : [];
        const materials = results[3].status === 'fulfilled' ? results[3].value : [];
        const settings = results[4].status === 'fulfilled' ? results[4].value : {};
        const libraries = results[5].status === 'fulfilled' ? results[5].value : [];
        const allProductsMontada = results[6].status === 'fulfilled' ? results[6].value : [];

        // Construir objeto de pointValues por biblioteca
        const libraryPointValues = {};
        libraries.forEach(lib => {
          libraryPointValues[lib.code] = lib.pointValue || 1.0;
        });

        // Determinar el material de casco predeterminado
        const defaultMaterialId = settings.defaultCarcassMaterialId || 
          (materials.length > 0 ? materials[0].id : INITIAL_CARCASS_MATERIALS[0].id);

        setState(prev => ({
          ...prev,
          users,
          libraries, // Lista completa de bibliotecas
          libraryPointValues, // Valores de punto por biblioteca
          currentLibrary: 'ZC', // Biblioteca por defecto
          catalogs: [
            { id: 'cat-m-base', name: 'Zona Cocinas - Montada', manufacturer: 'Zona Cocinas', products: productsMontada, module: 'montada', library: 'ZC' },
            { id: 'cat-d-base', name: 'Zona Cocinas - Despiece', manufacturer: 'Zona Cocinas', products: productsDespiece, module: 'despiece', library: 'ZC' }
          ],
          // Catálogo de inventario con TODOS los productos de todas las bibliotecas
          inventoryCatalogs: [
            { id: 'inv-montada', name: 'Inventario Montada', products: allProductsMontada, module: 'montada' },
          ],
          carcassMaterials: materials.length > 0 ? materials : INITIAL_CARCASS_MATERIALS,
          selectedCarcassMaterialId: defaultMaterialId,
          settings: settings,  // Guardar settings completo para montajesEnabled y otros
          pointValueMontada: settings.pointValueMontada || 1.0,
          pointValueDespiece: settings.pointValueDespiece || 0.88,
          specialIncrementWidth: settings.specialIncrementWidth || 45,
          specialIncrementHeight: settings.specialIncrementHeight || 45,
          specialIncrementDepth: settings.specialIncrementDepth || 45,
          // Incrementos por biblioteca
          librarySpecialIncrements: settings.librarySpecialIncrements || {
            ZC: { width: 45, height: 45, depth: 45 },
            MV: { width: 45, height: 45, depth: 45 }
          },
          vigaCutIncrement: settings.vigaCutIncrement || 0,
          // Corte de viga por biblioteca
          libraryVigaCutIncrements: settings.libraryVigaCutIncrements || {
            ZC: 0,
            MV: 0
          },
          brandColor: settings.brandColor || DEFAULT_BRAND_COLOR,
          logo: settings.logo || null
        }));
      } catch (err) {
        console.error("Error loading data from API:", err);
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, []);

  // Save budget items to localStorage (these stay local for now)
  useEffect(() => {
    const { budgetItemsMontada, budgetItemsDespiece, projects, customerName, customerAddress, clientCode, budgetNumber, internalReference, budgetCount } = state;
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({
        budgetItemsMontada,
        budgetItemsDespiece,
        projects,
        customerName,
        customerAddress,
        clientCode,
        budgetNumber,
        internalReference,
        budgetCount
      }));
    } catch (err) {
      console.error("Storage error:", err);
    }
  }, [state.budgetItemsMontada, state.budgetItemsDespiece, state.projects, state.customerName, state.customerAddress, state.clientCode, state.budgetNumber, state.internalReference, state.budgetCount]);

  const activeBrandColor = useMemo(() => {
    return state.brandColor || DEFAULT_BRAND_COLOR;
  }, [state.brandColor]);

  // Check maintenance mode
  const checkMaintenanceMode = async () => {
    try {
      const response = await fetch(`${API_URL}/api/maintenance/status`);
      const data = await response.json();
      
      // Only block non-admin users
      if (data.active && state.currentUser && !state.currentUser.isAdmin) {
        setIsInMaintenance(true);
      } else {
        setIsInMaintenance(false);
      }
    } catch (err) {
      console.error('Error checking maintenance:', err);
    }
  };

  // Check maintenance periodically
  useEffect(() => {
    if (state.currentUser) {
      checkMaintenanceMode();
      const interval = setInterval(checkMaintenanceMode, 30000); // Check every 30 seconds
      return () => clearInterval(interval);
    }
  }, [state.currentUser]);

  // After login: reload users and settings (endpoints protected by JWT, so they
  // fail on initial mount when no token exists yet)
  useEffect(() => {
    if (!state.currentUser?.id) return;
    let cancelled = false;
    (async () => {
      try {
        const [usersRes, settingsRes] = await Promise.allSettled([
          usersAPI.getAll(),
          settingsAPI.get(),
        ]);
        if (cancelled) return;
        const users = usersRes.status === 'fulfilled' ? usersRes.value : null;
        const settings = settingsRes.status === 'fulfilled' ? settingsRes.value : null;
        setState(prev => ({
          ...prev,
          ...(users ? { users } : {}),
          ...(settings ? {
            tarifa: settings.tarifa !== undefined ? settings.tarifa : prev.tarifa,
            ivaPercent: settings.ivaPercent !== undefined ? settings.ivaPercent : prev.ivaPercent,
            companyName: settings.companyName ?? prev.companyName,
            companyLogo: settings.logo ?? prev.companyLogo,
            brandColor: settings.brandColor ?? prev.brandColor,
          } : {}),
        }));
      } catch (err) {
        console.error('Error reloading users/settings post-login:', err);
      }
    })();
    return () => { cancelled = true; };
  }, [state.currentUser?.id]);

  // Enlace directo por URL: ?tab=crm (alias amigables → pestaña interna)
  const deepLinkApplied = useRef(false);
  useEffect(() => {
    if (deepLinkApplied.current || !state.currentUser?.id) return;
    deepLinkApplied.current = true;
    try {
      const tab = new URLSearchParams(window.location.search).get('tab');
      if (!tab) return;
      const map = {
        crm: 'crm-dashboard', presupuesto: 'budget', presup2: 'presupuestador2',
        presupuestador2: 'presupuestador2', rentabilidad: 'rentabilidad', facturas: 'invoices',
        archivo: 'library', mando: 'command', pedidos: 'misPedidos', digitalizador: 'digitalizador',
        armarios: 'armarios', montajes: 'montajes', fabrica: 'fabrica', render: 'renderStudio',
      };
      const target = map[tab.toLowerCase()] || tab;
      setState(p => ({ ...p, currentTab: target }));
    } catch { /* noop */ }
  }, [state.currentUser?.id]);

  const handleLogin = (user) => {
    // Al hacer login, limpiar los items del presupuesto para evitar 
    // que un usuario vea los datos de otro usuario
    const userLibraries = user.allowedLibraries || ['ZC'];
    
    // Recuperar la última biblioteca usada del localStorage (si el usuario tiene acceso)
    let savedLibrary = null;
    try {
      savedLibrary = localStorage.getItem('luiggi_active_library');
    } catch (e) {
      console.error("Error reading library from localStorage:", e);
    }
    
    // Usar la biblioteca guardada si el usuario tiene acceso, sino usar la primera permitida
    const defaultLibrary = (savedLibrary && userLibraries.includes(savedLibrary))
      ? savedLibrary
      : (userLibraries[0] || 'ZC');

    // En MÓVIL/TABLET (vista responsive), si el usuario tiene el CRM activado,
    // entrar directamente al CRM al loguearse.
    let _w = 1920;
    try { _w = window.innerWidth || 1920; } catch (e) { /* noop */ }
    const _isMobileTablet = _w < 1024;
    const _canCRM = !!user.canAccessCRM && !user.isTienda;
    // Usuario SOLO Luiggi Floor: entra directo a esa sección, sin otros presupuestadores
    const _floorOnly = !user.isAdmin && !!user.floorOnly;
    // Usuario SOLO CRM: entra directo al CRM, sin barra de navegación
    const _crmOnly = !user.isAdmin && !!user.crmOnly && _canCRM;
    // Calendario (vista Día): lo más práctico en la calle = ver las visitas de hoy
    const _landingTab = _floorOnly
      ? 'luiggifloor'
      : _crmOnly
        ? 'crm-calendar'
        : ((_isMobileTablet && _canCRM) ? 'crm-calendar' : 'budget');

    setState(prev => ({
      ...prev,
      currentUser: user,
      currentTab: _landingTab,
      // Pantalla de bienvenida (saludo inicial) solo en escritorio; en móvil/tablet
      // se entra directo a los menús, como acordamos.
      showWelcome: !_isMobileTablet,
      currentModule: user.allowedModules?.[0] || 'montada',
      currentLibrary: defaultLibrary,
      allowedLibraries: userLibraries,
      // Limpiar presupuesto actual al cambiar de usuario
      budgetItemsMontada: [],
      budgetItemsDespiece: [],
      customerName: '',
      customerAddress: '',
      clientCode: '',  // Limpiar código de cliente
      internalReference: '',
      doorColorLow: '',
      doorColorHigh: '',
      doorColorColumns: '',
      sideColor: '',
      golaAlto: false, golaAltoColor: '',
      golaBajo: false, golaBajoColor: '',
      // Logo POR USUARIO: si el usuario tiene marca propia y logo, usar el suyo;
      // si no, mantener el logo global cargado por defecto.
      logo: (user.useCustomBranding && user.logo) ? user.logo : prev.logo
    }));
    
    // Recargar productos de la biblioteca del usuario
    loadProductsByLibrary(defaultLibrary);
    
    // Limpiar localStorage de presupuesto (pero NO la biblioteca activa)
    try {
      localStorage.removeItem('luiggi_budget_data');
    } catch (e) {
      console.error("Error clearing localStorage:", e);
    }
  };

  // Función para cargar productos de una biblioteca específica
  const loadProductsByLibrary = async (libraryCode) => {
    try {
      const [productsMontada, productsDespiece] = await Promise.all([
        productsAPI.getAll('montada', libraryCode),
        productsAPI.getAll('despiece', libraryCode)
      ]);
      
      setState(prev => ({
        ...prev,
        currentLibrary: libraryCode,
        catalogs: [
          { id: 'cat-m-base', name: `${libraryCode} - Montada`, manufacturer: libraryCode, products: productsMontada, module: 'montada', library: libraryCode },
          { id: 'cat-d-base', name: `${libraryCode} - Despiece`, manufacturer: libraryCode, products: productsDespiece, module: 'despiece', library: libraryCode }
        ]
      }));
    } catch (error) {
      console.error('Error loading library products:', error);
    }
  };

  // Handler para cambio de biblioteca
  const handleLibraryChange = async (libraryCode) => {
    // Guardar la biblioteca activa en localStorage para persistencia entre sesiones
    try {
      localStorage.setItem('luiggi_active_library', libraryCode);
    } catch (e) {
      console.error("Error saving library to localStorage:", e);
    }
    
    // Cargar productos de la nueva biblioteca
    loadProductsByLibrary(libraryCode);
    
    // Seleccionar un armazón válido para la nueva biblioteca
    const materialsForLibrary = state.carcassMaterials.filter(m => m.library === libraryCode);
    if (materialsForLibrary.length > 0) {
      setState(prev => ({
        ...prev,
        selectedCarcassMaterialId: materialsForLibrary[0].id
      }));
    }
  };

  // Function to generate possible product codes from furniture dimensions
  const generatePossibleCodes = (tipo, subtipo, ancho, alto) => {
    const codes = [];
    const puertas = subtipo?.includes('2') ? '2' : '1';
    const tipoLetra = subtipo?.includes('VITRINA') ? 'V' : 'P';
    
    // Normalizar altura (la IA da en cm, los códigos usan formato especial)
    // Altos: 35, 40, 45, 60, 70, 80, 90 -> 35A, 40A, 45A, 60A, 7A, 8A, 9A
    // Bajos: 70, 80 -> 7B, 8B
    // Columnas: 200, 220, 240 -> 20CD, 22CD, 24CD
    // Semicolumnas: 110, 120, 130, 140 -> 11SM, 12SM, 13SM, 14SM
    
    const alturaNum = parseInt(alto) || 70;
    const anchoNum = parseInt(ancho) || 600;
    
    if (tipo === 'ALTO') {
      // Formato: {altura}A{puertas}P{ancho} o {altura/10}A{puertas}P{ancho}
      if (alturaNum >= 70 && alturaNum < 100) {
        // Altos 70-90cm: 7A, 8A, 9A
        const h = Math.floor(alturaNum / 10);
        codes.push(`${h}A${puertas}${tipoLetra}${anchoNum}`);
        codes.push(`A${h}A${puertas}${tipoLetra}${anchoNum}`); // Versión aluminio
      } else {
        // Altos 35-60cm: 35A, 40A, etc.
        codes.push(`${alturaNum}A${puertas}${tipoLetra}${anchoNum}`);
      }
    } else if (tipo === 'BAJO') {
      // Formato: {altura/10}B{puertas}P{ancho}
      const h = alturaNum >= 70 ? Math.floor(alturaNum / 10) : alturaNum;
      codes.push(`${h}B${puertas}${tipoLetra}${anchoNum}`);
      // Variantes con G (GOLA)
      codes.push(`${h}B1G2CB${anchoNum}`);
    } else if (tipo === 'COLUMNA') {
      // Formato: {altura/10}CD{puertas}P{ancho}
      const h = Math.floor(alturaNum / 10);
      codes.push(`${h}CD${puertas}P${anchoNum}`);
      codes.push(`${h}C${puertas}P${anchoNum}`);
    } else if (tipo === 'SEMICOLUMNA') {
      // Formato: {altura/10}SM{puertas}P{ancho}
      const h = Math.floor(alturaNum / 10);
      codes.push(`${h}SM${puertas}P${anchoNum}`);
      codes.push(`${h}SE${puertas}P${anchoNum}`);
      codes.push(`${h}SC${puertas}P${anchoNum}`);
    }
    
    // Añadir código sugerido por la IA si existe
    return codes;
  };

  // Function to find matching product in catalog
  const findProductInCatalog = (possibleCodes, iaCode) => {
    const allProducts = [...(state.productsMontada || []), ...(state.productsDespiece || [])];
    
    // Primero buscar código exacto de la IA
    if (iaCode) {
      const exactMatch = allProducts.find(p => 
        p.code?.toUpperCase() === iaCode.toUpperCase()
      );
      if (exactMatch) return exactMatch;
    }
    
    // Buscar por códigos generados
    for (const code of possibleCodes) {
      const match = allProducts.find(p => 
        p.code?.toUpperCase() === code.toUpperCase()
      );
      if (match) return match;
    }
    
    // Búsqueda parcial - buscar productos que contengan parte del código
    for (const code of possibleCodes) {
      const partialMatch = allProducts.find(p => 
        p.code?.toUpperCase().includes(code.substring(0, 5).toUpperCase())
      );
      if (partialMatch) return partialMatch;
    }
    
    return null;
  };

  // Function to add furniture from Visualizer (IA Lab) to budget
  const handleAddFromVisualizer = (furniture, showAlert = true) => {
    console.log('Datos recibidos de IA:', furniture);
    
    const tipo = (furniture.tipo || 'MUEBLE').toUpperCase();
    const subtipo = furniture.subtipo ? furniture.subtipo.replace(/_/g, ' ') : '';
    // Preferir dimensiones REALES del catálogo (backend) sobre las estimadas por la IA
    const ancho = furniture.ancho_real || furniture.width || furniture.ancho_estimado || 600;
    const alto = furniture.alto_real || furniture.height || furniture.alto_estimado || 70;
    const fondo = furniture.fondo_real || furniture.depth || furniture.fondo_estimado || 58;
    // Código CONFIRMADO por el backend (no la simple sugerencia de la IA)
    const matchedCode = furniture.code || furniture.codigo_catalogo;
    const iaCode = matchedCode || furniture.codigo_sugerido;

    // Generar posibles códigos y buscar en catálogo (el código confirmado va primero)
    const possibleCodes = generatePossibleCodes(tipo, subtipo, ancho, alto);
    if (furniture.codigo_sugerido) possibleCodes.unshift(furniture.codigo_sugerido);
    if (matchedCode) possibleCodes.unshift(matchedCode);

    console.log('Códigos posibles:', possibleCodes);

    const foundProduct = findProductInCatalog(possibleCodes, iaCode);
    
    let newItem;
    
    if (foundProduct) {
      // Producto encontrado en catálogo - usar sus datos reales
      console.log('✅ Producto encontrado:', foundProduct.code, foundProduct.name);
      newItem = {
        id: `ia-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        productId: foundProduct.id,
        productCode: foundProduct.code,
        productName: foundProduct.name,
        quantity: 1,
        customWidth: foundProduct.width || ancho,
        customHeight: foundProduct.height || alto,
        customDepth: foundProduct.depth || fondo,
        width: foundProduct.width || ancho,
        height: foundProduct.height || alto,
        depth: foundProduct.depth || fondo,
        category: foundProduct.category || tipo,
        points: foundProduct.points || 0,
        zonePoints: foundProduct.zonePoints || {},
        fromAI: true,
        catalogMatch: true
      };
    } else if (furniture.producto_encontrado && matchedCode) {
      // El backend YA encontró el producto en su catálogo (aunque el catálogo del
      // frontend no lo tenga cargado): usar SUS datos -> código, nombre, medidas y puntos.
      console.log('✅ Usando match del backend:', matchedCode);
      const puntos = furniture.points ?? furniture.puntos ?? 0;
      newItem = {
        id: `ia-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        productId: furniture.productId || furniture.product_id || matchedCode,
        productCode: matchedCode.toUpperCase(),
        productName: furniture.name || furniture.nombre_catalogo || `${tipo} ${subtipo}`.trim(),
        quantity: 1,
        customWidth: ancho,
        customHeight: alto,
        customDepth: fondo,
        width: ancho,
        height: alto,
        depth: fondo,
        category: furniture.category || furniture.categoria || tipo,
        points: puntos,
        zonePoints: furniture.zonePoints || {},
        fromAI: true,
        catalogMatch: true
      };
    } else {
      // Producto NO encontrado - crear con referencia desconocida
      console.log('⚠️ Producto NO encontrado, códigos probados:', possibleCodes);
      const productName = `${tipo} ${subtipo} ${ancho}x${alto}x${fondo}mm [REF. NO ENCONTRADA]`.toUpperCase().trim();
      const productCode = iaCode || possibleCodes[0] || `IA-${tipo.substring(0,3)}-${ancho}`;
      
      newItem = {
        id: `ia-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        productId: productCode,
        productCode: productCode.toUpperCase(),
        productName: productName,
        quantity: 1,
        customWidth: ancho,
        customHeight: alto,
        customDepth: fondo,
        width: ancho,
        height: alto,
        depth: fondo,
        category: tipo,
        points: 0,
        zonePoints: {},
        fromAI: true,
        catalogMatch: false
      };
    }

    console.log('Item para presupuesto:', newItem);

    // Add to the current module's budget items
    if (state.currentModule === 'montada') {
      setState(prev => ({
        ...prev,
        budgetItemsMontada: [...prev.budgetItemsMontada, newItem]
      }));
    } else {
      setState(prev => ({
        ...prev,
        budgetItemsDespiece: [...prev.budgetItemsDespiece, newItem]
      }));
    }
    
    if (showAlert && foundProduct) {
      // No mostrar alerta individual, se mostrará al final
    }
  };

  // Loading screen
  if (isLoading) {
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-slate-900">
        <div className="text-center">
          <Loader size={48} className="animate-spin text-orange-500 mx-auto mb-4" />
          <p className="text-white font-bold text-sm uppercase tracking-widest">Cargando Sistema...</p>
        </div>
      </div>
    );
  }

  if (!state.currentUser) {
    return (
        <>
            <style>{`:root { --brand-primary: ${state.brandColor}; }`}</style>
            <Login onLogin={handleLogin} customLogo={state.logo} />
        </>
    );
  }

  // Maintenance screen for non-admin users
  if (isInMaintenance && !state.currentUser?.isAdmin) {
    return <MaintenanceScreen onCheckAgain={checkMaintenanceMode} />;
  }

  // Pantalla de bienvenida (saludo inicial con nombre y foto) tras iniciar sesión.
  // Solo en escritorio; tras unos segundos o al pulsar "Entrar", da paso a los menús.
  if (state.showWelcome) {
    return (
      <>
        <style>{`:root { --brand-primary: ${activeBrandColor}; }`}</style>
        <WelcomeScreen
          user={state.currentUser}
          logo={state.logo}
          onContinue={() => setState(prev => ({ ...prev, showWelcome: false }))}
        />
      </>
    );
  }

  // Agenda de Negocios (Prescriptor): si el usuario SOLO tiene este permiso
  // (colaborador externo sin más funciones), ve únicamente su agenda a pantalla
  // completa. Si además tiene otras funciones (admin, CRM, fábrica, etc.), NO se
  // le bloquea nada: ve la app completa y la Agenda como un icono más en la barra.
  const _u = state.currentUser || {};
  const _hasOtherAccess = !!(
    _u.isAdmin || _u.isGerente || _u.isDirectorComercial || _u.isDirectorFabrica ||
    _u.isResponsableDelegacion || _u.isRepresentative || _u.isTienda || _u.isFabrica ||
    _u.isMontador || _u.canAccessCRM || _u.canAccessFabrica || _u.canAccessArmarios ||
    _u.canUseDigitalizador || _u.canAccessMontajes || (_u.allowedModules && _u.allowedModules.length > 0)
  );
  if (state.currentUser?.isPrescriptor && !_hasOtherAccess) {
    return (
      <div className="min-h-screen bg-slate-950">
        <style>{`:root { --brand-primary: ${activeBrandColor}; }`}</style>
        <PrescriptorAgenda
          currentUser={{...state.currentUser, companyLogo: state.logo}}
          onLogout={() => setState(prev => ({ ...prev, currentUser: null }))}
        />
      </div>
    );
  }

  // Usuario SOLO Luiggi Floor: entra directo a esa sección a pantalla completa,
  // sin acceso al resto de presupuestadores ni módulos. Cadena de altura correcta
  // (h-screen + flex-col + flex-1/min-h-0) para que se vea bien en iPhone/iPad.
  if (state.currentUser?.floorOnly && !state.currentUser?.isAdmin) {
    return (
      <div className="h-screen flex flex-col bg-zinc-950 overflow-hidden">
        <style>{`:root { --brand-primary: ${activeBrandColor}; }`}</style>
        <div className="flex items-center justify-end px-4 py-2 bg-zinc-900 shrink-0">
          <button
            onClick={() => setState(prev => ({ ...prev, currentUser: null }))}
            className="text-xs font-bold text-amber-400 hover:text-amber-300 uppercase tracking-widest"
          >
            Salir
          </button>
        </div>
        <div className="flex-1 min-h-0">
          <ErrorBoundary>
            <Suspense fallback={<div className="p-10 text-center text-amber-400">Cargando Luiggi Floor…</div>}>
              <LuiggiFloor currentUser={state.currentUser} />
            </Suspense>
          </ErrorBoundary>
        </div>
      </div>
    );
  }

  // Usuario SOLO CRM: entra directo al CRM a pantalla completa, sin barra lateral
  // de navegación ni ningún otro módulo. Misma cadena de altura responsive.
  if (state.currentUser?.crmOnly && !state.currentUser?.isAdmin && state.currentUser?.canAccessCRM && !state.currentUser?.isTienda) {
    const _crmTab = (state.currentTab || '').startsWith('crm-') ? state.currentTab.slice(4) : undefined;
    return (
      <div className="h-screen flex flex-col bg-white overflow-hidden">
        <style>{`:root { --brand-primary: ${activeBrandColor}; }`}</style>
        <div className="flex items-center justify-between px-4 py-2 bg-slate-900 shrink-0">
          <span className="text-xs font-black text-indigo-300 uppercase tracking-widest">CRM</span>
          <button
            onClick={() => setState(prev => ({ ...prev, currentUser: null }))}
            className="text-xs font-bold text-indigo-300 hover:text-indigo-200 uppercase tracking-widest"
          >
            Salir
          </button>
        </div>
        <div className="flex-1 min-h-0">
          <ErrorBoundary>
            <Suspense fallback={<div className="p-10 text-center text-indigo-400">Cargando CRM…</div>}>
              <CRMLayout currentUser={state.currentUser} initialTab={_crmTab} focusEvent={state.crmFocusEvent} />
            </Suspense>
          </ErrorBoundary>
        </div>
      </div>
    );
  }

  const carcassMaterialName = state.carcassMaterials?.find(m => m.id === state.selectedCarcassMaterialId)?.name || 'Blanco';

  return (
    <div className="flex h-screen bg-slate-950 overflow-hidden text-slate-800">
      <style>{`
        :root {
          --brand-primary: ${activeBrandColor};
        }
        .text-brand { color: var(--brand-primary) !important; }
        .bg-brand { background-color: var(--brand-primary) !important; }
        .border-brand { border-color: var(--brand-primary) !important; }
        .ring-brand { --tw-ring-color: var(--brand-primary) !important; }
        .hover-bg-brand:hover { background-color: var(--brand-primary) !important; }
        .hover-text-brand:hover { color: var(--brand-primary) !important; }
        
        .master-panel { background: rgba(15, 23, 42, 0.05); }
        
        .scrollbar-thin::-webkit-scrollbar { width: 6px; height: 6px; }
        .scrollbar-thin::-webkit-scrollbar-track { background: transparent; }
        .scrollbar-thin::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 10px; }
        .scrollbar-thin::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
        
        @media print {
          .no-print { display: none !important; }
          .print-only { display: block !important; }
        }
      `}</style>

      {isManufacturingView ? (
        <ManufacturingReport 
            items={state.currentModule === 'montada' ? state.budgetItemsMontada : state.budgetItemsDespiece}
            finish={state.globalFinish}
            carcassColor={carcassMaterialName}
            state={state}
            catalogs={state.catalogs}
            logo={state.logo}
            distributorName={state.currentUser.clientName}
            onBack={() => setIsManufacturingView(false)}
        />
      ) : (
        <>
          {/* Botón hamburguesa - solo visible cuando sidebar está cerrada */}
          {!sidebarOpen && (
            <button
              onClick={() => setSidebarOpen(true)}
              className="fixed top-3 left-3 z-[60] w-10 h-10 bg-slate-950 text-white rounded-xl shadow-2xl flex items-center justify-center border border-white/10 hover:bg-slate-800 transition-all"
              aria-label="Mostrar menú"
              data-testid="sidebar-toggle"
              title="Mostrar menú"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" /></svg>
            </button>
          )}

          {/* Overlay oscuro al abrir sidebar en móvil */}
          {sidebarOpen && (
            <div
              onClick={() => setSidebarOpen(false)}
              className="md:hidden fixed inset-0 bg-black/50 z-40"
              data-testid="mobile-sidebar-overlay"
            />
          )}

          <aside className={`${sidebarOpen ? 'fixed inset-y-0 left-0 translate-x-0 md:relative md:translate-x-0' : 'fixed -translate-x-full md:hidden'} transition-transform duration-300 ease-in-out w-20 bg-slate-950 flex flex-col items-center py-6 gap-4 shrink-0 border-r border-white/5 z-50 shadow-2xl overflow-hidden max-h-screen`} onClick={(e) => {
            // En móvil cerrar al hacer click en un botón de navegación
            if (window.innerWidth < 768 && e.target.closest('button[data-nav]')) {
              setTimeout(() => setSidebarOpen(false), 150);
            }
          }}>
            {/* LOGO - Toca para colapsar/ocultar la sidebar */}
            <button
              onClick={() => setSidebarOpen(false)}
              className="w-14 h-14 bg-white rounded-2xl flex items-center justify-center shadow-lg border-b-4 border-slate-800 overflow-hidden transition-all duration-200 hover:scale-95 hover:opacity-80 shrink-0 group relative"
              title="Toca para ocultar el menú"
              data-testid="sidebar-logo-toggle"
            >
              {state.logo ? (
                <img src={state.logo} alt="Logo" className="w-full h-full object-contain p-1.5 group-hover:opacity-60 transition-opacity" />
              ) : (
                <div className="w-full h-full bg-brand flex items-center justify-center font-black text-white italic text-2xl group-hover:opacity-60 transition-opacity">L</div>
              )}
              {/* Icono de colapsar que aparece al hacer hover */}
              <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity bg-slate-900/40 rounded-2xl">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M11 19l-7-7 7-7" /></svg>
              </div>
            </button>
            
            <div className="flex flex-col gap-3 flex-1 w-full px-2 overflow-y-auto scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent min-h-0">
              {/* 
                IMPORTANTE: Usuarios con isFabrica o que SOLO tienen canAccessFabrica
                no deben ver otros módulos - solo ven el botón de FÁBRICA
              */}
              {(() => {
                // Determinar si es un usuario SOLO de fábrica (no admin, no tiene otros permisos importantes)
                const isFabricaOnly = state.currentUser?.isFabrica && 
                  !state.currentUser?.isAdmin && 
                  !state.currentUser?.isGerente && 
                  !state.currentUser?.isDirectorComercial &&
                  !state.currentUser?.isRepresentative;
                
                // Si es usuario solo fábrica, mostrar solo el botón de fábrica
                if (isFabricaOnly) {
                  return (
                    <button 
                      onClick={() => setState(p => ({...p, currentTab: 'fabrica'}))} 
                      className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-colors duration-200 ${state.currentTab === 'fabrica' ? 'bg-emerald-600 text-white shadow-xl scale-110' : 'text-slate-500 hover:text-white hover:bg-white/10'}`}
                      data-testid="fabrica-nav-btn"
                    >
                      <Factory size={18}/>
                      <span className="text-[7px] font-black uppercase tracking-widest">Fábrica</span>
                    </button>
                  );
                }
                
                // Para otros usuarios, mostrar navegación normal
                return (
                  <>
                    {/* CRM - Solo visible para usuarios con canAccessCRM (NO para Tienda/Punto de Venta) */}
                    {state.currentUser?.canAccessCRM && !state.currentUser?.isTienda && (
                      <button 
                        onClick={() => setState(p => ({...p, currentTab: 'crm-dashboard'}))} 
                        className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-colors duration-200 ${
                          state.currentTab?.startsWith('crm-') 
                            ? 'bg-indigo-600 text-white shadow-xl scale-110' 
                            : 'text-slate-500 hover:text-white hover:bg-white/10'
                        }`}
                        data-testid="crm-dashboard-nav"
                      >
                        <Target size={18}/>
                        <span className="text-[7px] font-black uppercase tracking-widest">CRM</span>
                      </button>
                    )}

                    {/* Agenda de Negocios (Prescriptor) - icono ADITIVO, justo debajo del CRM:
                        aparece si el usuario tiene el permiso, sin ocultar el resto de funciones */}
                    {state.currentUser?.isPrescriptor && (
                      <button
                        onClick={() => setState(p => ({...p, currentTab: 'agendaNegocios'}))}
                        className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-colors duration-200 ${state.currentTab === 'agendaNegocios' ? 'bg-indigo-600 text-white shadow-xl scale-110' : 'text-slate-500 hover:text-white hover:bg-white/10'}`}
                        data-testid="agenda-negocios-nav-btn"
                      >
                        <CalendarDays size={18}/>
                        <span className="text-[7px] font-black uppercase tracking-widest">Agenda Neg.</span>
                      </button>
                    )}

                    <button 
                      onClick={() => setState(p => ({...p, currentTab: 'budget'}))} 
                      className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-colors duration-200 ${state.currentTab === 'budget' ? 'bg-brand text-white shadow-xl scale-110' : 'text-slate-500 hover:text-white hover:bg-white/10'}`}
                    >
                      <FileText size={18}/>
                      <span className="text-[7px] font-black uppercase tracking-widest">Presupuesto</span>
                    </button>

                    {/* Presupuestador 2 (MV por tarifa) - requiere autorización por usuario */}
                    {(state.currentUser?.canUsePresupuestador2 || state.currentUser?.isAdmin) && (
                      <button
                        onClick={() => setState(p => ({...p, currentTab: 'presupuestador2'}))}
                        className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-colors duration-200 ${state.currentTab === 'presupuestador2' ? 'bg-emerald-600 text-white shadow-xl scale-110' : 'text-slate-500 hover:text-white hover:bg-white/10'}`}
                      >
                        <Receipt size={18}/>
                        <span className="text-[7px] font-black uppercase tracking-widest">Presup. 2</span>
                      </button>
                    )}

                    {/* Mis Pedidos - Visible para todos los usuarios NO tienda - DEBAJO DE PRESUPUESTOS */}
                    {!state.currentUser?.isTienda && (
                      <button 
                        onClick={() => setState(p => ({...p, currentTab: 'misPedidos'}))} 
                        className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-colors duration-200 ${state.currentTab === 'misPedidos' ? 'bg-orange-600 text-white shadow-xl scale-110' : 'text-slate-500 hover:text-white hover:bg-white/10'}`}
                        data-testid="mis-pedidos-nav-btn"
                      >
                        <ShoppingBag size={18}/>
                        <span className="text-[7px] font-black uppercase tracking-widest">Pedidos</span>
                      </button>
                    )}

                    {/* Archivo - NO visible para Tienda/Punto de Venta */}
                    {!state.currentUser?.isTienda && (
                      <button 
                        onClick={() => setState(p => ({...p, currentTab: 'library'}))} 
                        className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-colors duration-200 ${state.currentTab === 'library' ? 'bg-brand text-white shadow-xl scale-110' : 'text-slate-500 hover:text-white hover:bg-white/10'}`}
                      >
                        <FolderOpen size={18}/>
                        <span className="text-[7px] font-black uppercase tracking-widest">Archivo</span>
                      </button>
                    )}

                    {/* Facturación - Solo admin, gerente y director comercial */}
                    {(state.currentUser?.isAdmin || state.currentUser?.isGerente || state.currentUser?.isDirectorComercial) && (
                      <button
                        onClick={() => setState(p => ({...p, currentTab: 'invoices'}))}
                        className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-colors duration-200 ${state.currentTab === 'invoices' ? 'bg-orange-500 text-white shadow-xl scale-110' : 'text-slate-500 hover:text-white hover:bg-white/10'}`}
                        data-testid="invoices-nav-btn"
                      >
                        <Receipt size={18}/>
                        <span className="text-[7px] font-black uppercase tracking-widest">G. Comercial</span>
                      </button>
                    )}

                    {/* Rentabilidad por proyecto - admin/gerente/director comercial */}
                    {(state.currentUser?.isAdmin || state.currentUser?.isGerente || state.currentUser?.isDirectorComercial) && (
                      <button
                        onClick={() => setState(p => ({...p, currentTab: 'rentabilidad'}))}
                        className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-colors duration-200 ${state.currentTab === 'rentabilidad' ? 'bg-emerald-600 text-white shadow-xl scale-110' : 'text-slate-500 hover:text-white hover:bg-white/10'}`}
                        data-testid="rentabilidad-nav-btn"
                      >
                        <TrendingUp size={18}/>
                        <span className="text-[7px] font-black uppercase tracking-widest">Rentab.</span>
                      </button>
                    )}

                    {/* Gastos de comercial (escaneo de tickets) - comerciales y admin, con permiso */}
                    {(state.currentUser?.isAdmin || state.currentUser?.isRepresentative || state.currentUser?.isGerente || state.currentUser?.isDirectorComercial) && state.currentUser?.canAccessGastos !== false && (
                      <button
                        onClick={() => setState(p => ({...p, currentTab: 'gastos'}))}
                        className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-colors duration-200 ${state.currentTab === 'gastos' ? 'bg-indigo-600 text-white shadow-xl scale-110' : 'text-slate-500 hover:text-white hover:bg-white/10'}`}
                        data-testid="gastos-nav-btn"
                      >
                        <Receipt size={18}/>
                        <span className="text-[7px] font-black uppercase tracking-widest">Gastos</span>
                      </button>
                    )}

                    {/* Luiggi Floor - división de suelo SPC (solo con permiso canAccessFloor) */}
                    {(state.currentUser?.isAdmin || state.currentUser?.canAccessFloor === true) && (
                      <button
                        onClick={() => setState(p => ({...p, currentTab: 'luiggifloor'}))}
                        className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-colors duration-200 ${state.currentTab === 'luiggifloor' ? 'bg-amber-500 text-zinc-900 shadow-xl scale-110' : 'text-slate-500 hover:text-white hover:bg-white/10'}`}
                        data-testid="luiggifloor-nav-btn"
                      >
                        <Layers size={18}/>
                        <span className="text-[7px] font-black uppercase tracking-widest">Floor</span>
                      </button>
                    )}

                    {/* Panel de Mando - Solo admin y gerente */}
                    {(state.currentUser?.isAdmin || state.currentUser?.isGerente) && (
                      <button
                        onClick={() => setState(p => ({...p, currentTab: 'command'}))}
                        className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-colors duration-200 ${state.currentTab === 'command' ? 'bg-slate-700 text-white shadow-xl scale-110' : 'text-slate-500 hover:text-white hover:bg-white/10'}`}
                        data-testid="command-center-btn"
                      >
                        <Shield size={18}/>
                        <span className="text-[7px] font-black uppercase tracking-widest">Mando</span>
                      </button>
                    )}
                    
                    {/* Solo usuarios con canUseAIAnalysis pueden ver IA Lab (NO para Tienda) */}
                    {state.currentUser?.canUseAIAnalysis && !state.currentUser?.isTienda && (
                      <button 
                        onClick={() => setState(p => ({...p, currentTab: 'visualizer'}))} 
                        className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-colors duration-200 ${state.currentTab === 'visualizer' ? 'bg-brand text-white shadow-xl scale-110' : 'text-slate-500 hover:text-white hover:bg-white/10'}`}
                      >
                        <Sparkles size={18}/>
                        <span className="text-[7px] font-black uppercase tracking-widest">IA Lab</span>
                      </button>
                    )}
                    
                    {/* Render 3D Studio - Usuarios con acceso a IA (NO para Tienda) */}
                    {state.currentUser?.canUseAIAnalysis && !state.currentUser?.isTienda && (
                      <button 
                        onClick={() => setState(p => ({...p, currentTab: 'renderStudio'}))} 
                        className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-colors duration-200 ${state.currentTab === 'renderStudio' ? 'bg-purple-600 text-white shadow-xl scale-110' : 'text-slate-500 hover:text-white hover:bg-white/10'}`}
                        data-testid="render-studio-nav-btn"
                      >
                        <Image size={18}/>
                        <span className="text-[7px] font-black uppercase tracking-widest">Render 3D</span>
                      </button>
                    )}
                    
                    {/* Informes: ahora vive DENTRO de RENTAB (pestaña "Generador de informes") */}
                    
                    {/* Digitalizador - Solo usuarios con permiso (NO para Tienda) */}
                    {state.currentUser?.canUseDigitalizador && !state.currentUser?.isTienda && (
                      <button 
                        onClick={() => setState(p => ({...p, currentTab: 'digitalizador'}))} 
                        className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-colors duration-200 ${state.currentTab === 'digitalizador' ? 'bg-orange-600 text-white shadow-xl scale-110' : 'text-slate-500 hover:text-white hover:bg-white/10'}`}
                        data-testid="digitalizador-nav-btn"
                      >
                        <ScanLine size={18}/>
                        <span className="text-[7px] font-black uppercase tracking-widest">Digitalizador</span>
                      </button>
                    )}
                    
                    {/* Agenda de Montajes - Solo si está habilitada en settings Y usuario tiene permiso */}
                    {state.settings?.montajesEnabled && (state.currentUser?.canAccessMontajes || state.currentUser?.isAdmin || state.currentUser?.isMontador) && (                      <button 
                        onClick={() => setState(p => ({...p, currentTab: 'montajes'}))} 
                        className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-colors duration-200 ${state.currentTab === 'montajes' ? 'bg-orange-600 text-white shadow-xl scale-110' : 'text-slate-500 hover:text-white hover:bg-white/10'}`}
                        data-testid="montajes-nav-btn"
                      >
                        <Wrench size={18}/>
                        <span className="text-[7px] font-black uppercase tracking-widest">Montajes</span>
                      </button>
                    )}
                    
                    {/* Portal de Fábrica - usuarios con permiso o Director de Fábrica */}
                    {(state.currentUser?.canAccessFabrica || state.currentUser?.isFabrica || state.currentUser?.isDirectorFabrica) && (
                      <button 
                        onClick={() => setState(p => ({...p, currentTab: 'fabrica'}))} 
                        className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-colors duration-200 ${state.currentTab === 'fabrica' ? 'bg-emerald-600 text-white shadow-xl scale-110' : 'text-slate-500 hover:text-white hover:bg-white/10'}`}
                        data-testid="fabrica-nav-btn"
                      >
                        <Factory size={18}/>
                        <span className="text-[7px] font-black uppercase tracking-widest">Fábrica</span>
                      </button>
                    )}

                    {/* Botón Mis Tiendas - Solo para Comerciales (no Admin, no Tienda) */}
                    {!state.currentUser?.isAdmin && state.currentUser?.isRepresentative && !state.currentUser?.isTienda && (
                      <button 
                        onClick={() => setShowCommercialWorkView(true)} 
                        className="flex flex-col items-center gap-1 p-2 rounded-xl transition-colors duration-200 text-purple-400 hover:text-white hover:bg-purple-500/30"
                        data-testid="commercial-panel-nav-btn"
                      >
                        <Users size={18}/>
                        <span className="text-[7px] font-black uppercase tracking-widest">Mis Tiendas</span>
                      </button>
                    )}
                  </>
                );
              })()}
            </div>

            <div className="mt-auto flex flex-col gap-4 w-full px-2 shrink-0 pb-4">
              {/* Botón de Ayuda - Visible para todos excepto Tiendas y Montadores */}
              {!state.currentUser?.isTienda && !state.currentUser?.isMontador && (
                <button 
                    onClick={() => setShowUserManual(true)} 
                    className="flex flex-col items-center gap-1 p-2 rounded-xl text-slate-500 hover:text-indigo-500 hover:bg-indigo-50/30 transition-colors duration-200"
                    data-testid="help-button"
                >
                    <HelpCircle size={18}/>
                    <span className="text-[7px] font-black uppercase tracking-widest">Ayuda</span>
                </button>
              )}
              
              {/* Panel Maestro: un ADMIN siempre lo ve (aunque tenga ademas rol de
                  fabrica/tienda). Un Comercial lo ve si no es Tienda ni solo Fabrica. */}
              {(state.currentUser?.isAdmin || (state.currentUser?.isRepresentative && !state.currentUser?.isTienda && !state.currentUser?.isFabrica)) && state.currentUser?.canAccessMaster !== false && (
                <button 
                    onClick={() => setState(p => ({...p, showSettings: true}))} 
                    className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-colors duration-200 ${state.showSettings ? 'bg-brand text-white shadow-lg' : 'text-slate-500 hover:text-white hover:bg-white/10'}`}
                >
                    <Settings size={18}/>
                    <span className="text-[7px] font-black uppercase tracking-widest">Master</span>
                </button>
              )}
              <button 
                  onClick={async () => {
                    // Verificar si hay líneas de presupuesto sin guardar
                    const hasUnsavedItems = (state.budgetItemsMontada?.length > 0) || (state.budgetItemsDespiece?.length > 0);
                    
                    if (hasUnsavedItems) {
                      const confirmLogout = window.confirm(
                        `Tienes ${(state.budgetItemsMontada?.length || 0) + (state.budgetItemsDespiece?.length || 0)} líneas de presupuesto sin guardar.\n\n¿Estás seguro de que quieres salir sin guardar?`
                      );
                      if (!confirmLogout) {
                        return; // No cerrar sesión
                      }
                    }
                    
                    await authLogout();
                    setState(p => ({...p, currentUser: null, budgetItemsMontada: [], budgetItemsDespiece: []}));
                  }}
                  className="flex flex-col items-center gap-1 p-2 rounded-xl text-slate-500 hover:text-red-500 transition-colors duration-200"
              >
                  <LogOut size={18}/>
                  <span className="text-[7px] font-black uppercase tracking-widest">Salir</span>
              </button>
            </div>
          </aside>

          {/* Aviso GLOBAL de eventos próximos (aparece en cualquier pantalla) */}
          <GlobalEventReminder
            currentUser={state.currentUser}
            onOpenCalendar={(evt) => setState(p => ({ ...p, currentTab: 'crm-calendar', crmFocusEvent: evt || null }))}
          />

          <main className="flex-1 relative overflow-hidden bg-white shadow-2xl rounded-l-[3.5rem] my-2 border-l border-white/10">
            <Suspense fallback={<div className="h-full flex items-center justify-center"><Loader className="animate-spin text-slate-400" size={32}/></div>}>
            {state.currentTab === 'budget' && (
              <ErrorBoundary>
              <BudgetTable 
                items={state.currentModule === 'montada' ? state.budgetItemsMontada : state.budgetItemsDespiece} 
                catalogs={state.catalogs} 
                activeCatalogIds={state.activeCatalogIds} 
                state={state} 
                setState={setState} 
                onOpenManufacturing={() => setIsManufacturingView(true)} 
              />
              </ErrorBoundary>
            )}
            {state.currentTab === 'presupuestador2' && (state.currentUser?.canUsePresupuestador2 || state.currentUser?.isAdmin) && (
              <ErrorBoundary><Presupuestador2 currentUser={state.currentUser} /></ErrorBoundary>
            )}
            {state.currentTab === 'visualizer' && state.currentUser?.canUseAIAnalysis && (
              <Visualizer images={state.uploadedImages} state={state} setState={setState} onAddToBudget={handleAddFromVisualizer} />
            )}
            {state.currentTab === 'library' && <ErrorBoundary><ProjectLibrary state={state} setState={setState} /></ErrorBoundary>}
            {state.currentTab === 'backup' && <BackupManager />}
            {state.currentTab === 'invoices' && <ErrorBoundary><Invoices currentUser={state.currentUser} /></ErrorBoundary>}
            {state.currentTab === 'rentabilidad' && <ErrorBoundary><RentabilidadPanel currentUser={state.currentUser} /></ErrorBoundary>}
            {state.currentTab === 'gastos' && <ErrorBoundary><GestionGastos currentUser={state.currentUser} /></ErrorBoundary>}
            {state.currentTab === 'luiggifloor' && <ErrorBoundary><LuiggiFloor currentUser={state.currentUser} /></ErrorBoundary>}
            {state.currentTab === 'command' && <ErrorBoundary><CommandCenter currentUser={state.currentUser} /></ErrorBoundary>}
            {state.currentTab === 'digitalizador' && state.currentUser?.canUseDigitalizador && (
              <Digitalizador state={state} />
            )}
            {state.currentTab === 'armarios' && state.currentUser?.canAccessArmarios && (
              <Armarios state={state} setState={setState} />
            )}
            {state.currentTab === 'montajes' && state.settings?.montajesEnabled && (state.currentUser?.canAccessMontajes || state.currentUser?.isAdmin || state.currentUser?.isMontador) && (
              <AgendaMontajes currentUser={state.currentUser} />
            )}
            {state.currentTab === 'agendaNegocios' && state.currentUser?.isPrescriptor && (
              <PrescriptorAgenda
                currentUser={{...state.currentUser, companyLogo: state.logo}}
                embedded={true}
                onLogout={() => setState(prev => ({ ...prev, currentUser: null }))}
              />
            )}
            
            {/* Portal de Fábrica - SOLO usuarios con permiso explícito o Director de Fábrica */}
            {state.currentTab === 'fabrica' && (state.currentUser?.canAccessFabrica || state.currentUser?.isFabrica || state.currentUser?.isDirectorFabrica) && (
              <PortalFabrica currentUser={state.currentUser} />
            )}
            
            {/* Render 3D Studio */}
            {state.currentTab === 'renderStudio' && state.currentUser?.canUseAIAnalysis && (
              <AIRenderStudio state={state} />
            )}

            {/* Generador de Informes */}
            {state.currentTab === 'informes' && (state.currentUser?.isAdmin || state.currentUser?.isRepresentative) && (
              <ReportGenerator />
            )}

            {/* Mis Pedidos */}
            {state.currentTab === 'misPedidos' && (
              <MisPedidos currentUser={state.currentUser} />
            )}
            
            {/* CRM - Single Component with internal navigation */}
            {state.currentTab?.startsWith('crm') && <CRMLayout currentUser={state.currentUser} initialTab={(state.currentTab || '').startsWith('crm-') ? state.currentTab.slice(4) : undefined} focusEvent={state.crmFocusEvent} />}
            </Suspense>

            <div className="absolute bottom-6 left-12 pointer-events-none opacity-20 flex items-center gap-2">
               <ShieldCheck size={14} className="text-slate-900" />
               <span className="text-[8px] font-black uppercase tracking-widest text-slate-900 italic">LUIGGI HOME ERP v4.1</span>
            </div>
          </main>

          <Suspense fallback={null}>
            <SettingsModal 
              isOpen={state.showSettings || false} 
              onClose={() => setState(p => ({...p, showSettings: false}))} 
              state={state} 
              setState={setState} 
            />
          </Suspense>

          {/* Maintenance Panel Modal - ADMIN ONLY */}
          {showMaintenancePanel && state.currentUser?.isAdmin && (
            <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-[9999] flex items-center justify-center p-4">
              <div className="bg-white rounded-3xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
                <div className="bg-indigo-950 text-white px-8 py-5 flex justify-between items-center shrink-0">
                  <div className="flex items-center gap-4">
                    <div className="p-3 bg-orange-600 rounded-xl">
                      <Wrench size={24} />
                    </div>
                    <div>
                      <h2 className="text-xl font-black uppercase tracking-wider">Panel de Mantenimiento</h2>
                      <p className="text-indigo-300 text-xs font-medium mt-0.5">Gestión de actualizaciones y backups</p>
                    </div>
                  </div>
                  <button 
                    onClick={() => setShowMaintenancePanel(false)}
                    className="p-2 hover:bg-white/10 rounded-xl transition-colors"
                  >
                    ✕
                  </button>
                </div>
                <div className="flex-1 overflow-auto p-6">
                  <MaintenancePanel 
                    currentUser={state.currentUser} 
                    onClose={() => setShowMaintenancePanel(false)} 
                  />
                </div>
              </div>
            </div>
          )}

          {/* Admin Work View Modal - ADMIN ONLY */}
          <Suspense fallback={null}>
            <AdminWorkView 
              isOpen={showAdminWorkView}
              onClose={() => setShowAdminWorkView(false)}
              currentUser={state.currentUser}
            />
          </Suspense>

          {/* Commercial Work View Modal - COMMERCIAL ONLY */}
          <Suspense fallback={null}>
            <CommercialWorkView 
              isOpen={showCommercialWorkView}
              onClose={() => setShowCommercialWorkView(false)}
              currentUser={state.currentUser}
            />
          </Suspense>

          {/* User Manual Modal - Disponible para todos los usuarios */}
          <Suspense fallback={null}>
            <UserManualModal 
              isOpen={showUserManual}
              onClose={() => setShowUserManual(false)}
              currentUser={state.currentUser}
            />
          </Suspense>
        </>
      )}
    </div>
  );
};

export default App;
