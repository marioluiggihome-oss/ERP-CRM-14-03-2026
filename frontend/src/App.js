import React, { useState, useEffect, useMemo, useRef, lazy, Suspense } from 'react';
import GlobalEventReminder from './components/GlobalEventReminder';
import { ShoppingCart, Settings, LogOut, FolderOpen, Sparkles, ShieldCheck, FileText, Loader, HardDrive, Users, Target, LayoutDashboard, CalendarDays, ScanLine, Wrench, Building2, Box, Factory, HelpCircle, ShoppingBag, Receipt, Shield, Image, TrendingUp, Layers, Hammer, ChefHat, Zap } from 'lucide-react';
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
const ResumenCocinas = lazy(() => import('./components/ResumenCocinas'));
const Cascos = lazy(() => import('./components/Cascos'));
const PropData = lazy(() => import('./components/PropData'));
const Armarios2 = lazy(() => import('./components/Armarios2'));
const CocinasIA = lazy(() => import('./components/CocinasIA'));
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
const KitchenDesigner3D = lazy(() => import('./components/KitchenDesigner3D'));
const EstudioCocinas = lazy(() => import('./components/EstudioCocinas')); // Módulo unificado de diseño de cocinas
const ElectrosTab = lazy(() => import('./components/settings/ElectrosTab')); // Catálogo de electrodomésticos (menú principal)
const CarpinterosUsers = lazy(() => import('./components/CarpinterosUsers')); // Gestión de usuarios de la división carpinteros
const CarpinterPanel = lazy(() => import('./components/CarpinterPanel')); // Panel independiente admin Carpinter.io (reemplaza SettingsModal)
const Studio3kLanding = lazy(() => import('./components/Studio3kLanding')); // Landing pública studio3k.io / estudio3k.io
const CarpinterosLanding = lazy(() => import('./components/CarpinterosLanding')); // Landing propia carpinteros (carpenter.io)
const AgentesDisenadores = lazy(() => import('./components/AgentesDisenadores')); // Agentes diseñadores en paralelo
const RentabilidadPanel = lazy(() => import('./components/RentabilidadPanel'));
const GestionGastos = lazy(() => import('./components/GestionGastos'));
const LuiggiFloor = lazy(() => import('./components/LuiggiFloor'));
const ReportGenerator = lazy(() => import('./components/ReportGenerator'));

// ─── Carga directa: componentes ligeros necesarios al inicio ────────────────
import Login from './components/Login';
import MaintenanceScreen from './components/MaintenanceScreen';
import MaintenancePanel from './components/MaintenancePanel';
import WelcomeScreen from './components/WelcomeScreen';
import { authAPI, productsAPI, materialsAPI, settingsAPI, usersAPI, librariesAPI } from './services/api';
import { logout as authLogout, getUser, clearTokens, isAuthenticated } from './services/authService';
import { DOOR_FINISHES, INITIAL_CARCASS_MATERIALS, DEFAULT_BRAND_COLOR, STORAGE_KEY } from './constants';
import { initSecurityGuard } from './utils/securityGuard';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Detecta fallos de carga de "chunk" (típicos tras un despliegue: el index viejo
// pide un chunk con hash que ya no existe). Se resuelven recargando la página.
const isChunkError = (e) => /Loading chunk|ChunkLoadError|dynamically imported module|Failed to fetch dynamically|importing a module script failed/i.test((e && (e.message || e.name)) || '');

class ErrorBoundary extends React.Component {
  constructor(props) { super(props); this.state = { hasError: false, error: null }; }
  static getDerivedStateFromError(error) { return { hasError: true, error }; }
  componentDidCatch(error, info) {
    console.error('[ErrorBoundary] Módulo falló al renderizar:', error, info?.componentStack);
    // Auto-recuperación: si es un fallo de chunk (despliegue nuevo), recarga una vez.
    if (isChunkError(error)) {
      try {
        const k = '__chunk_reload_ts__';
        const last = Number(sessionStorage.getItem(k) || 0);
        if (Date.now() - last > 10000) { sessionStorage.setItem(k, String(Date.now())); window.location.reload(); }
      } catch { window.location.reload(); }
    }
  }
  render() {
    if (this.state.hasError) {
      const chunk = isChunkError(this.state.error);
      return (
        <div className="h-full flex items-center justify-center bg-slate-50 p-8">
          <div className="text-center">
            <p className="text-2xl mb-2">⚠️</p>
            <p className="font-black text-slate-700 text-sm uppercase">{chunk ? 'Actualizando a la última versión…' : 'Error al cargar el módulo'}</p>
            <p className="text-xs text-slate-400 mt-2 font-mono">{chunk ? 'Recarga la página para cargar la versión más reciente.' : this.state.error?.message}</p>
            <button onClick={() => chunk ? window.location.reload() : this.setState({ hasError: false })}
              className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-xl text-xs font-black">
              {chunk ? 'Recargar' : 'Reintentar'}
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
      defaultEdgeBandingPriceMl: 1.77,
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
        { id: 'cat-m-base', name: 'Cocina Montada', manufacturer: 'Base', products: [], module: 'montada' },
        { id: 'cat-d-base', name: 'Despiece', manufacturer: 'Base', products: [], module: 'despiece' }
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
            { id: 'cat-m-base', name: 'ZC - Montada', manufacturer: 'ZC', products: productsMontada, module: 'montada', library: 'ZC' },
            { id: 'cat-d-base', name: 'ZC - Despiece', manufacturer: 'ZC', products: productsDespiece, module: 'despiece', library: 'ZC' }
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
          pointValueDesmontada: settings.cascosPointValue || settings.pointValueDesmontada || 1.0,
          defaultEdgeBandingPriceMl: settings.defaultEdgeBandingPriceMl ?? 1.77,
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
          companyName: settings.companyName || '',
          marcaBlanca: !!settings.marcaBlanca,
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
            marcaBlanca: settings.marcaBlanca ?? prev.marcaBlanca,
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
        armarios: 'armarios', montajes: 'montajes', fabrica: 'fabrica', render: 'renderStudio', cocinas3d: 'kitchenDesigner',
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
    // Permisos de presupuestadores (independientes). P1 por defecto permitido
    // (compatibilidad con usuarios antiguos); P2 requiere autorización explícita.
    const _canP1 = user.canUsePresupuestador1 !== false;
    const _canP2 = user.canUsePresupuestador2 !== false;
    const _defaultBudgetTab = _canP2 ? 'presupuestador2' : 'budget';
    // Calendario (vista Día): lo más práctico en la calle = ver las visitas de hoy
    // CONTROLLER (solo consulta): entra directo al informe de rentabilidad.
    const _soloController = !!user.isController && !(user.isAdmin || user.isGerente
      || user.isDirectorComercial || user.isDirectorFabrica || user.isResponsableDelegacion);
    const _landingTab = _soloController
      ? 'rentabilidad'
      : _floorOnly
      ? 'luiggifloor'
      : _crmOnly
        ? 'crm-calendar'
        : _isMobileTablet
          ? (_canCRM ? 'crm-calendar' : _defaultBudgetTab)  // móvil/tablet: como estaba
          : 'welcome';  // PC: pantalla de bienvenida tras el login

    setState(prev => ({
      ...prev,
      currentUser: user,
      currentTab: _landingTab,
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
      logo: (user.useCustomBranding && user.logo) ? user.logo : prev.logo,
      // Colores de marca carpinter.io: naranja corporativo para todos los usuarios de la división
      brandColor: (user.isCarpintero || user.linkedCarpinteroAdminId) ? '#C4621D' : prev.brandColor
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
    
    const tipo = (furniture.tipo || 'MUEBLE').toUpperCase();
    const subtipo = furniture.subtipo ? furniture.subtipo.replace(/_/g, ' ') : '';
    // Preferir dimensiones REALES del catálogo (backend) sobre las estimadas por la IA
    const ancho = furniture.ancho_real || furniture.width || furniture.ancho_estimado || 600;
    const alto = furniture.alto_real || furniture.height || furniture.alto_estimado || 70;
    const fondo = furniture.fondo_real || furniture.depth || furniture.fondo_estimado || 58;
    // Código CONFIRMADO por el backend (no la simple sugerencia de la IA)
    const matchedCode = furniture.code || furniture.codigo_catalogo;
    const iaCode = matchedCode || furniture.codigo_sugerido;
    // Cantidad de muebles idénticos agrupados (IA Lab). Por defecto 1.
    const qty = Number(furniture.cantidad || furniture.qty) || 1;

    // Generar posibles códigos y buscar en catálogo (el código confirmado va primero)
    const possibleCodes = generatePossibleCodes(tipo, subtipo, ancho, alto);
    if (furniture.codigo_sugerido) possibleCodes.unshift(furniture.codigo_sugerido);
    if (matchedCode) possibleCodes.unshift(matchedCode);


    const foundProduct = findProductInCatalog(possibleCodes, iaCode);
    
    let newItem;
    
    if (foundProduct) {
      // Producto encontrado en catálogo - usar sus datos reales
      newItem = {
        id: `ia-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        productId: foundProduct.id,
        productCode: foundProduct.code,
        productName: foundProduct.name,
        quantity: qty,
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
      const puntos = furniture.points ?? furniture.puntos ?? 0;
      newItem = {
        id: `ia-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        productId: furniture.productId || furniture.product_id || matchedCode,
        productCode: matchedCode.toUpperCase(),
        productName: furniture.name || furniture.nombre_catalogo || `${tipo} ${subtipo}`.trim(),
        quantity: qty,
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
      const productName = `${tipo} ${subtipo} ${ancho}x${alto}x${fondo}mm [REF. NO ENCONTRADA]`.toUpperCase().trim();
      const productCode = iaCode || possibleCodes[0] || `IA-${tipo.substring(0,3)}-${ancho}`;
      
      newItem = {
        id: `ia-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        productId: productCode,
        productCode: productCode.toUpperCase(),
        productName: productName,
        quantity: qty,
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
    // Detectar marca por dominio o parámetro de URL para colorear la pantalla de carga
    const _lHost = (window.location.hostname || '').toLowerCase();
    const _lParams = new URLSearchParams(window.location.search);
    const _lIsS3k = _lHost.includes('studio3k') || _lHost.includes('estudio3k') || _lParams.has('s3k') || _lParams.get('brand') === 'studio3k';
    const _lIsCarp = _lHost.includes('carpinter') || _lHost.includes('carpenter') || _lParams.has('carp') || _lParams.get('brand') === 'carpinteros';
    // Studio3K: fondo navy oscuro + spinner azul índigo
    // Carpinter.io: fondo beige oscuro + spinner naranja corporativo
    // Luiggi Home (default): fondo slate-900 + spinner naranja
    const _lBg = _lIsS3k ? '#0A0A1A' : _lIsCarp ? '#17130F' : '#0f172a';
    const _lSpinner = _lIsS3k ? '#3B5BDB' : '#C4622D';
    return (
      <div className="fixed inset-0 flex items-center justify-center" style={{ background: _lBg }}>
        <div className="text-center">
          <svg className="animate-spin mx-auto mb-4" width="48" height="48" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="24" cy="24" r="20" stroke="rgba(255,255,255,0.1)" strokeWidth="4" />
            <path d="M44 24a20 20 0 0 0-20-20" stroke={_lSpinner} strokeWidth="4" strokeLinecap="round" />
          </svg>
          <p className="text-white font-bold text-sm uppercase tracking-widest" style={{ opacity: 0.6 }}>Cargando...</p>
        </div>
      </div>
    );
  }

  // Marca Carpinteros: entrando por carpenter.io / carpinter.io (o ?brand=carpinteros)
  // el visitante ve primero la LANDING comercial de la división; el botón de
  // acceso lleva al login con la marca carpinteros.
  const _isCarpBrandEntry = (() => {
    try {
      const host = (window.location.hostname || '').toLowerCase();
      const sp = new URLSearchParams(window.location.search);
      const path = (window.location.pathname || '').toLowerCase();
      return host.includes('carpenter.io') || host.includes('carpinter.io') || sp.get('brand') === 'carpinteros' || sp.has('carp') || path === '/carp' || path.endsWith('/carp');
    } catch { return false; }
  })();

  // Acceso directo al programa saltando la landing: ?entrar / ?app / ?login
  const _skipLanding = (() => {
    try {
      const sp = new URLSearchParams(window.location.search);
      return sp.has('entrar') || sp.has('app') || sp.has('login');
    } catch { return false; }
  })();

  // La web comercial de carpinter.io está PUBLICADA: quien entra por el dominio
  // ve la landing. Para volver a ocultarla (y mandar al público directo al
  // login) basta con poner esto en false; entonces solo se vería en modo VISTA
  // PREVIA (?preview o #preview).
  // OJO: la landing solo se muestra a quien NO ha iniciado sesión. Si ya estás
  // dentro del ERP y abres carpinter.io, entras a la aplicación; para verla
  // logueado hay que añadir ?preview.
  const CARP_LANDING_PUBLISHED = true;
  const _carpPreview = (() => {
    try {
      const sp = new URLSearchParams(window.location.search);
      const path = (window.location.pathname || '').toLowerCase();
      return sp.has('preview') || sp.has('carp') || sp.get('vista') === 'previa'
        || path === '/carp' || path.endsWith('/carp')
        || ((window.location.hash || '').toLowerCase().includes('preview'));
    } catch { return false; }
  })();
  const _showCarpLanding = _isCarpBrandEntry && (CARP_LANDING_PUBLISHED || _carpPreview);

  // ── Studio3K: entrando por studio3k.io / estudio3k.io (o ?brand=studio3k)
  // muestra la landing comercial de Studio3K. Publicada por defecto.
  const _isStudio3kEntry = (() => {
    try {
      const host = (window.location.hostname || '').toLowerCase();
      const sp = new URLSearchParams(window.location.search);
      const path = (window.location.pathname || '').toLowerCase();
      return host.includes('studio3k.io') || host.includes('estudio3k.io')
        || sp.get('brand') === 'studio3k' || sp.has('s3k')
        || path === '/s3k' || path.endsWith('/s3k');
    } catch { return false; }
  })();
  const STUDIO3K_LANDING_PUBLISHED = true;
  const _studio3kPreview = (() => {
    try {
      const sp = new URLSearchParams(window.location.search);
      const path = (window.location.pathname || '').toLowerCase();
      return sp.has('s3k') || sp.get('brand') === 'studio3k'
        || path === '/s3k' || path.endsWith('/s3k')
        || ((window.location.hash || '').toLowerCase().includes('s3k'));
    } catch { return false; }
  })();
  const _showStudio3kLanding = _isStudio3kEntry && (STUDIO3K_LANDING_PUBLISHED || _studio3kPreview);

  // Vista previa Studio3K aunque estés logueado
  if (_studio3kPreview && _showStudio3kLanding && !state.studio3kLandingSkip && !_skipLanding) {
    return (
      <Suspense fallback={<div className="min-h-screen bg-[#0A0A0A]" />}>
        <Studio3kLanding onEnter={() => setState(prev => ({ ...prev, studio3kLandingSkip: true }))} />
      </Suspense>
    );
  }

  // Vista previa de la LANDING aunque estés logueado: si pides ?carp / /carp /
  // ?preview explícitamente, muestra la web comercial (para revisarla sin cerrar
  // sesión). El botón "Entrar" de la landing (onEnter) la cierra y sigues a la app.
  if (_carpPreview && _showCarpLanding && !state.carpLandingSkip && !_skipLanding) {
    return (
      <Suspense fallback={<div className="min-h-screen bg-[#F5F0E8]" />}>
        <CarpinterosLanding onEnter={() => setState(prev => ({ ...prev, carpLandingSkip: true }))} />
      </Suspense>
    );
  }

  if (!state.currentUser) {
    if (_showCarpLanding && !state.carpLandingSkip && !_skipLanding) {
      return (
        <Suspense fallback={<div className="min-h-screen bg-[#F5F0E8]" />}>
          <CarpinterosLanding onEnter={() => setState(prev => ({ ...prev, carpLandingSkip: true }))} />
        </Suspense>
      );
    }
    if (_showStudio3kLanding && !state.studio3kLandingSkip && !_skipLanding) {
      return (
        <Suspense fallback={<div className="min-h-screen bg-[#0A0A0A]" />}>
          <Studio3kLanding onEnter={() => setState(prev => ({ ...prev, studio3kLandingSkip: true }))} />
        </Suspense>
      );
    }
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

  // Agenda de Negocios (Prescriptor): si el usuario SOLO tiene este permiso
  // (colaborador externo sin más funciones), ve únicamente su agenda a pantalla
  // completa. Si además tiene otras funciones (admin, CRM, fábrica, etc.), NO se
  // le bloquea nada: ve la app completa y la Agenda como un icono más en la barra.
  const _u = state.currentUser || {};
  const _hasOtherAccess = !!(
    _u.isAdmin || _u.isGerente || _u.isDirectorComercial || _u.isDirectorFabrica ||
    _u.isResponsableDelegacion || _u.isRepresentative || _u.isTienda || _u.isFabrica ||
    _u.isMontador || _u.canAccessCRM || _u.canAccessFabrica || _u.canAccessArmarios ||
    _u.canUseDigitalizador || _u.canAccessMontajes || (_u.allowedModules && _u.allowedModules.length > 0) ||
    _u.canManageCarpinteroUsers  // Admin de división carpinteros: entra a la app completa con panel Master
  );
  // CONTROLLER en modo consulta: SOLO el informe de rentabilidad, sin barra de
  // módulos ni acceso al resto de la aplicación.
  const _soloControllerUI = !!_u.isController && !(_u.isAdmin || _u.isGerente
    || _u.isDirectorComercial || _u.isDirectorFabrica || _u.isResponsableDelegacion) && !_hasOtherAccess;
  if (_soloControllerUI) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col">
        <div className="bg-slate-900 text-white px-4 py-2.5 flex items-center justify-between">
          <span className="text-xs font-black uppercase tracking-widest">
            Informe de rentabilidad · <span className="text-emerald-400">Consulta</span>
          </span>
          <div className="flex items-center gap-3">
            <span className="text-[11px] text-slate-300">{_u.clientName || _u.username}</span>
            <button onClick={async () => { await authLogout(); setState(p => ({ ...p, currentUser: null })); }}
              className="text-[11px] font-bold bg-white/10 hover:bg-white/20 px-3 py-1 rounded-lg">
              Salir
            </button>
          </div>
        </div>
        <div className="flex-1 overflow-hidden">
          {/* Con ErrorBoundary, igual que la pestaña de rentabilidad del resto de
              perfiles: el CONTROLLER entra DIRECTO aquí y sin esto un fallo del
              módulo (o un chunk viejo en caché tras un despliegue) le tumbaba la
              aplicación entera con la pantalla negra de "Algo ha fallado". */}
          <ErrorBoundary>
            <Suspense fallback={<div className="p-6 text-slate-400">Cargando…</div>}>
              <RentabilidadPanel currentUser={state.currentUser} />
            </Suspense>
          </ErrorBoundary>
        </div>
      </div>
    );
  }

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

  // Portal Carpinteros & Ebanistas: el usuario con perfil carpintero entra a su
  // web de inicio (landing configurable por usuario) a pantalla completa. Si
  // además tiene el presupuestador de Cocina Desmontada, un botón le deja pasar
  // a la app normal. La landing por defecto es la web del negocio de carpinteros.
  if (state.currentUser?.isCarpintero && !_hasOtherAccess && !state.carpinteroPortalOff) {
    // Sin URL configurada se muestra la landing PROPIA (componente local, sin
    // iframes externos que puedan dar 403). Si el usuario tiene una URL, iframe.
    const landingUrl = state.currentUser?.carpinteroLandingUrl || '';
    return (
      <div className="h-screen flex flex-col bg-slate-950 overflow-hidden">
        <style>{`:root { --brand-primary: ${activeBrandColor}; }`}</style>
        {state.showCarpinterosUsers && (
          <Suspense fallback={null}>
            <CarpinterosUsers onClose={() => setState(prev => ({ ...prev, showCarpinterosUsers: false }))} />
          </Suspense>
        )}
        <div className="flex items-center justify-between px-4 py-2 bg-slate-900 shrink-0">
          <div className="flex items-center gap-2">
            {state.logo && <img src={state.logo} alt="" className="h-7 rounded" />}
            <span className="text-xs font-black text-amber-400 uppercase tracking-widest">Carpinteros & Ebanistas</span>
          </div>
          <div className="flex items-center gap-3">
            {state.currentUser?.canManageCarpinteroUsers && (
              <button
                onClick={() => setState(prev => ({ ...prev, showCarpinterosUsers: true }))}
                className="text-xs font-bold text-white bg-stone-700 hover:bg-stone-600 px-3 py-1.5 rounded-lg uppercase tracking-wide"
              >
                Usuarios
              </button>
            )}
            {state.currentUser?.canUseCascos && (
              <button
                onClick={() => setState(prev => ({ ...prev, carpinteroPortalOff: true, currentTab: 'cascos' }))}
                className="text-xs font-bold text-white bg-amber-600 hover:bg-amber-500 px-3 py-1.5 rounded-lg uppercase tracking-wide"
              >
                Presupuestador
              </button>
            )}
            {(state.currentUser?.canUseKitchenDesigner || state.currentUser?.canUseCocinasAI || state.currentUser?.canUseAIAnalysis) && (
              <button
                onClick={() => setState(prev => ({ ...prev, carpinteroPortalOff: true, currentTab: 'estudioCocinas' }))}
                className="text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-500 px-3 py-1.5 rounded-lg uppercase tracking-wide"
              >
                Estudio 3D
              </button>
            )}
            {state.currentUser?.canAccessArmarios && (
              <button
                onClick={() => setState(prev => ({ ...prev, carpinteroPortalOff: true, currentTab: 'armarios' }))}
                className="text-xs font-bold text-white bg-cyan-600 hover:bg-cyan-500 px-3 py-1.5 rounded-lg uppercase tracking-wide"
              >
                Armarios
              </button>
            )}
            {landingUrl && (
              <a href={landingUrl} target="_blank" rel="noreferrer"
                className="text-xs font-bold text-slate-400 hover:text-white uppercase tracking-widest">
                Abrir web
              </a>
            )}
            <button
              onClick={() => setState(prev => ({ ...prev, currentUser: null }))}
              className="text-xs font-bold text-amber-400 hover:text-amber-300 uppercase tracking-widest"
            >
              Salir
            </button>
          </div>
        </div>
        <div className="flex-1 min-h-0 overflow-y-auto bg-white">
          {landingUrl ? (
            <iframe src={landingUrl} title="Portal Carpinteros" className="w-full h-full border-0 bg-white" />
          ) : (
            <Suspense fallback={<div className="min-h-full bg-[#F5F0E8]" />}>
              <CarpinterosLanding onEnter={null} embedded />
            </Suspense>
          )}
        </div>
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
            <Suspense fallback={<div className="p-10 text-center text-amber-400">Cargando Floor…</div>}>
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
          {/* Botón flotante - solo visible cuando sidebar está cerrada.
              Muestra el LOGO de Luiggi Home (la marca no se pierde al colapsar)
              y al pasar el ratón enseña el icono de menú. */}
          {!sidebarOpen && (
            <button
              onClick={() => setSidebarOpen(true)}
              className="fixed top-3 left-3 z-[60] w-12 h-12 bg-white rounded-xl shadow-2xl flex items-center justify-center border border-slate-200 overflow-hidden hover:scale-95 transition-all group"
              aria-label="Mostrar menú"
              data-testid="sidebar-toggle"
              title="Mostrar menú"
            >
              {(state.currentUser?.isCarpintero || state.currentUser?.linkedCarpinteroAdminId || state.currentUser?.canManageCarpinteroUsers) && _isCarpBrandEntry ? (
                <img src="/carpinter-logo-icon.png" alt="carpinter.io" className="w-full h-full object-contain p-1" />
              ) : state.logo ? (
                <img src={state.logo} alt="logo" className="w-full h-full object-contain p-1" />
              ) : state.marcaBlanca ? (
                <div className="w-full h-full bg-indigo-600 flex items-center justify-center font-black text-white text-lg">
                  {(state.companyName || '').trim().charAt(0).toUpperCase() || '·'}
                </div>
              ) : (
                <div className="w-full h-full bg-brand flex items-center justify-center font-black text-white italic text-xl">L</div>
              )}
              <span className="absolute inset-0 bg-slate-900/45 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" /></svg>
              </span>
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
              {(state.currentUser?.isCarpintero || state.currentUser?.linkedCarpinteroAdminId || state.currentUser?.canManageCarpinteroUsers) && _isCarpBrandEntry ? (
                <img src="/carpinter-logo-icon.png" alt="carpinter.io" className="w-full h-full object-contain p-1.5 group-hover:opacity-60 transition-opacity" />
              ) : state.logo ? (
                <img src={state.logo} alt="Logo" className="w-full h-full object-contain p-1.5 group-hover:opacity-60 transition-opacity" />
              ) : (
                <div className="w-full h-full bg-brand flex items-center justify-center font-black text-white italic text-2xl group-hover:opacity-60 transition-opacity">L</div>
              )}
              {/* Icono de colapsar que aparece al hacer hover */}
              <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity bg-slate-900/40 rounded-2xl">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M11 19l-7-7 7-7" /></svg>
              </div>
            </button>

            {/* Botón EXPLÍCITO para ocultar la barra (funciona en móvil, tablet y desktop) */}
            <button
              onClick={() => setSidebarOpen(false)}
              className="w-full flex flex-col items-center gap-0.5 py-1 rounded-lg text-slate-500 hover:text-white hover:bg-white/10 transition-colors shrink-0"
              title="Ocultar el menú"
              data-testid="sidebar-hide-btn"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M11 19l-7-7 7-7M18 19l-7-7 7-7" /></svg>
              <span className="text-[7px] font-black uppercase tracking-widest">Ocultar</span>
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
                    {/* Inicio - pantalla de bienvenida (vídeo + accesos rápidos). Visible
                        también en móvil para poder ver/abrir todos los módulos desde ahí. */}
                    <button
                      onClick={() => setState(p => ({...p, currentTab: 'welcome'}))}
                      className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-colors duration-200 ${state.currentTab === 'welcome' ? 'bg-slate-700 text-white shadow-xl scale-110' : 'text-slate-500 hover:text-white hover:bg-white/10'}`}
                      data-testid="welcome-nav-btn"
                    >
                      <LayoutDashboard size={18}/>
                      <span className="text-[7px] font-black uppercase tracking-widest">Inicio</span>
                    </button>

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

                    {/* Presupuestador (MV por tarifa) - principal, abre por defecto */}
                    {(state.currentUser?.canUsePresupuestador2 !== false) && (
                      <button
                        onClick={() => setState(p => ({...p, currentTab: 'presupuestador2'}))}
                        className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-colors duration-200 ${state.currentTab === 'presupuestador2' ? 'bg-emerald-600 text-white shadow-xl scale-110' : 'text-slate-500 hover:text-white hover:bg-white/10'}`}
                      >
                        <Receipt size={18}/>
                        <span className="text-[7px] font-black uppercase tracking-widest text-center leading-tight">Cocina Montada</span>
                      </button>
                    )}

                    {/* Presupuestador 2 (el anterior) - requiere autorización por usuario */}
                    {(state.currentUser?.canUsePresupuestador1 !== false) && (
                    <button
                      onClick={() => setState(p => ({...p, currentTab: 'budget'}))}
                      className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-colors duration-200 ${state.currentTab === 'budget' ? 'bg-brand text-white shadow-xl scale-110' : 'text-slate-500 hover:text-white hover:bg-white/10'}`}
                    >
                      <FileText size={18}/>
                      <span className="text-[7px] font-black uppercase tracking-widest text-center leading-tight">Cocina Montada 2</span>
                    </button>
                    )}

                    {/* Mis Pedidos - requiere permiso explícito (la casilla manda) */}
                    {!state.currentUser?.isTienda && state.currentUser?.canAccessPedidos === true && (
                      <button
                        onClick={() => setState(p => ({...p, currentTab: 'misPedidos'}))}
                        className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-colors duration-200 ${state.currentTab === 'misPedidos' ? 'bg-orange-600 text-white shadow-xl scale-110' : 'text-slate-500 hover:text-white hover:bg-white/10'}`}
                        data-testid="mis-pedidos-nav-btn"
                      >
                        <ShoppingBag size={18}/>
                        <span className="text-[7px] font-black uppercase tracking-widest">Pedidos</span>
                      </button>
                    )}

                    {/* Resumen Totales - resumen por cocinas con totales y forma de pago (permiso específico) */}
                    {!state.currentUser?.isTienda && state.currentUser?.canUseResumenTotales === true && (
                      <button
                        onClick={() => setState(p => ({...p, currentTab: 'resumenCocinas'}))}
                        className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-colors duration-200 ${state.currentTab === 'resumenCocinas' ? 'bg-brand text-white shadow-xl scale-110' : 'text-slate-500 hover:text-white hover:bg-white/10'}`}
                      >
                        <Layers size={18}/>
                        <span className="text-[7px] font-black uppercase tracking-widest">Resumen Tot.</span>
                      </button>
                    )}

                    {/* Presupuestador de Cascos - permiso específico */}
                    {!state.currentUser?.isTienda && state.currentUser?.canUseCascos === true && (
                      <button
                        onClick={() => setState(p => ({...p, currentTab: 'cascos'}))}
                        className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-colors duration-200 ${state.currentTab === 'cascos' ? 'bg-brand text-white shadow-xl scale-110' : 'text-slate-500 hover:text-white hover:bg-white/10'}`}
                      >
                        <Box size={18}/>
                        <span className="text-[7px] font-black uppercase tracking-widest text-center leading-tight">Cocina Desmontada</span>
                      </button>
                    )}

                    {/* Prospección de Obra Nueva (PropData IA) - permiso específico */}
                    {!state.currentUser?.isTienda && state.currentUser?.canUsePropData === true && (
                      <button
                        onClick={() => setState(p => ({...p, currentTab: 'propdata'}))}
                        className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-colors duration-200 ${state.currentTab === 'propdata' ? 'bg-brand text-white shadow-xl scale-110' : 'text-slate-500 hover:text-white hover:bg-white/10'}`}
                      >
                        <Building2 size={18}/>
                        <span className="text-[7px] font-black uppercase tracking-widest text-center leading-tight">Obra Nueva</span>
                      </button>
                    )}

                    {/* Armarios 2 - diseñador IA (permiso específico) */}
                    {!state.currentUser?.isTienda && state.currentUser?.canUseArmarios2 === true && (
                      <button
                        onClick={() => setState(p => ({...p, currentTab: 'armarios2'}))}
                        className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-colors duration-200 ${state.currentTab === 'armarios2' ? 'bg-brand text-white shadow-xl scale-110' : 'text-slate-500 hover:text-white hover:bg-white/10'}`}
                      >
                        <Hammer size={18}/>
                        <span className="text-[7px] font-black uppercase tracking-widest text-center leading-tight">Armarios 2</span>
                      </button>
                    )}

                    {/* Cocinas IA 2 oculta: unificado en Estudio 3D + Agentes (reversible) */}
                    {false && !state.currentUser?.isTienda && state.currentUser?.canUseCocinasAI === true && (
                      <button
                        onClick={() => setState(p => ({...p, currentTab: 'cocinasai'}))}
                        className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-colors duration-200 ${state.currentTab === 'cocinasai' ? 'bg-brand text-white shadow-xl scale-110' : 'text-slate-500 hover:text-white hover:bg-white/10'}`}
                      >
                        <ChefHat size={18}/>
                        <span className="text-[7px] font-black uppercase tracking-widest text-center leading-tight">Cocinas IA 2</span>
                      </button>
                    )}

                    {/* Archivo - requiere permiso explícito (la casilla manda) */}
                    {!state.currentUser?.isTienda && state.currentUser?.canAccessArchivo === true && (
                      <button
                        onClick={() => setState(p => ({...p, currentTab: 'library'}))}
                        className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-colors duration-200 ${state.currentTab === 'library' ? 'bg-brand text-white shadow-xl scale-110' : 'text-slate-500 hover:text-white hover:bg-white/10'}`}
                      >
                        <FolderOpen size={18}/>
                        <span className="text-[7px] font-black uppercase tracking-widest">Archivo</span>
                      </button>
                    )}

                    {/* G. Comercial / Facturación - requiere permiso explícito (la casilla manda) */}
                    {state.currentUser?.canAccessInvoices === true && (
                      <button
                        onClick={() => setState(p => ({...p, currentTab: 'invoices'}))}
                        className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-colors duration-200 ${state.currentTab === 'invoices' ? 'bg-orange-500 text-white shadow-xl scale-110' : 'text-slate-500 hover:text-white hover:bg-white/10'}`}
                        data-testid="invoices-nav-btn"
                      >
                        <Receipt size={18}/>
                        <span className="text-[7px] font-black uppercase tracking-widest">G. Comercial</span>
                      </button>
                    )}

                    {/* Rentabilidad - requiere permiso explícito (la casilla manda) */}
                    {state.currentUser?.canAccessRentabilidad === true && (
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
                    {(state.currentUser?.canAccessFloor === true) && (
                      <button
                        onClick={() => setState(p => ({...p, currentTab: 'luiggifloor'}))}
                        className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-colors duration-200 ${state.currentTab === 'luiggifloor' ? 'bg-amber-500 text-zinc-900 shadow-xl scale-110' : 'text-slate-500 hover:text-white hover:bg-white/10'}`}
                        data-testid="luiggifloor-nav-btn"
                      >
                        <Layers size={18}/>
                        <span className="text-[7px] font-black uppercase tracking-widest">Floor</span>
                      </button>
                    )}

                    {/* Panel de Mando - requiere permiso explícito (la casilla manda) */}
                    {state.currentUser?.canAccessMando === true && (
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
                    
                    {/* Render 3D Studio — APARCADO: integrado en 3D Estudio */}
                    {/* Kitchen 3D Designer — APARCADO: integrado en 3D Estudio */}
                    {/* 3D Estudio — Módulo unificado con Manus API (render, plano, ficha, presentación) */}
                    {(state.currentUser?.canUseKitchenDesigner || state.currentUser?.canUseCocinasAI || state.currentUser?.canUseAIAnalysis) && !state.currentUser?.isTienda && (
                      <button 
                        onClick={() => setState(p => ({...p, currentTab: 'estudioCocinas'}))} 
                        className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-colors duration-200 ${state.currentTab === 'estudioCocinas' ? 'bg-amber-600 text-white shadow-xl scale-110' : 'text-slate-500 hover:text-white hover:bg-white/10'}`}
                        data-testid="estudio-3d-nav-btn"
                        title="Estudio 3D: Renders, Planos 2D, Fichas Técnicas y Presentaciones"
                      >
                        <ChefHat size={18}/>
                        <span className="text-[7px] font-black uppercase tracking-widest">Estudio 3D</span>
                      </button>
                    )}
                    


                    {/* Diseñador de Armarios */}
                    {state.currentUser?.canAccessArmarios && !state.currentUser?.isTienda && (
                      <button
                        onClick={() => setState(p => ({...p, currentTab: 'armarios'}))}
                        className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-colors duration-200 ${state.currentTab === 'armarios' ? 'bg-cyan-600 text-white shadow-xl scale-110' : 'text-slate-500 hover:text-white hover:bg-white/10'}`}
                        data-testid="armarios-nav-btn"
                      >
                        <Box size={18}/>
                        <span className="text-[7px] font-black uppercase tracking-widest">Armarios</span>
                      </button>
                    )}

                    {/* Electros — catálogo de electrodomésticos (coste solo master; el resto ve PVP) */}
                    {!state.currentUser?.isTienda && (
                      <button
                        onClick={() => setState(p => ({...p, currentTab: 'electros'}))}
                        className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-colors duration-200 ${state.currentTab === 'electros' ? 'bg-amber-500 text-white shadow-xl scale-110' : 'text-slate-500 hover:text-white hover:bg-white/10'}`}
                        data-testid="electros-nav-btn"
                        title="Electros: catálogo de electrodomésticos (PVP; coste solo master)"
                      >
                        <Zap size={18}/>
                        <span className="text-[7px] font-black uppercase tracking-widest">Electros</span>
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
                    {state.settings?.montajesEnabled && (state.currentUser?.canAccessMontajes || state.currentUser?.isMontador) && (                      <button 
                        onClick={() => setState(p => ({...p, currentTab: 'montajes'}))} 
                        className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-colors duration-200 ${state.currentTab === 'montajes' ? 'bg-orange-600 text-white shadow-xl scale-110' : 'text-slate-500 hover:text-white hover:bg-white/10'}`}
                        data-testid="montajes-nav-btn"
                      >
                        <Wrench size={18}/>
                        <span className="text-[7px] font-black uppercase tracking-widest">Montajes</span>
                      </button>
                    )}
                    
                    {/* Portal de Fábrica - requiere permiso explícito (la casilla manda) */}
                    {state.currentUser?.canAccessFabrica === true && (
                      <button 
                        onClick={() => setState(p => ({...p, currentTab: 'fabrica'}))} 
                        className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-colors duration-200 ${state.currentTab === 'fabrica' ? 'bg-emerald-600 text-white shadow-xl scale-110' : 'text-slate-500 hover:text-white hover:bg-white/10'}`}
                        data-testid="fabrica-nav-btn"
                      >
                        <Factory size={18}/>
                        <span className="text-[7px] font-black uppercase tracking-widest">Fábrica</span>
                      </button>
                    )}

                    {/* Agentes Diseñadores IA - sección Producción */}
                    {(state.currentUser?.canUseAgentesIA || state.currentUser?.isAdmin) && !state.currentUser?.isTienda && (
                      <button
                        onClick={() => setState(p => ({...p, currentTab: 'agentesDisenadores'}))}
                        className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-colors duration-200 ${state.currentTab === 'agentesDisenadores' ? 'bg-purple-600 text-white shadow-xl scale-110' : 'text-slate-500 hover:text-white hover:bg-white/10'}`}
                        title="Agentes Diseñadores: lanza hasta 7 proyectos en paralelo"
                        data-testid="agentes-ia-nav-btn"
                      >
                        <Sparkles size={18}/>
                        <span className="text-[7px] font-black uppercase tracking-widest">Agentes</span>
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
                  fabrica/tienda). Un Comercial lo ve si no es Tienda ni solo Fabrica.
                  El admin de la división carpinteros (canManageCarpinteroUsers) también
                  lo ve para poder gestionar su cuenta y usuarios. */}
              {(state.currentUser?.isAdmin || state.currentUser?.canManageCarpinteroUsers || (state.currentUser?.isRepresentative && !state.currentUser?.isTienda && !state.currentUser?.isFabrica && state.currentUser?.canAccessMaster !== false)) && (
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

          <main className={`flex-1 relative overflow-hidden bg-white shadow-2xl border-l border-white/10 ${!sidebarOpen ? 'ml-0 my-0 rounded-l-none border-l-0' : 'rounded-l-[3.5rem] my-2'}`}>
            <Suspense fallback={<div className="h-full flex items-center justify-center"><Loader className="animate-spin text-slate-400" size={32}/></div>}>
            {state.currentTab === 'welcome' && (
              <ErrorBoundary>
                {state.currentUser?.canManageCarpinteroUsers && _isCarpBrandEntry ? (
                  <div className="h-full overflow-y-auto">
                    <Suspense fallback={<div className="min-h-full bg-[#F5F0E8]" />}>
                      <CarpinterosLanding onEnter={null} embedded />
                    </Suspense>
                  </div>
                ) : (
                  <WelcomeScreen
                    currentUser={state.currentUser}
                    settings={state.settings}
                    onNavigate={(tab) => setState(p => ({ ...p, currentTab: tab }))}
                  />
                )}
              </ErrorBoundary>
            )}
            {state.currentTab === 'budget' && (state.currentUser?.canUsePresupuestador1 !== false) && (
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
            {state.currentTab === 'presupuestador2' && (state.currentUser?.canUsePresupuestador2 !== false) && (
              <ErrorBoundary>
              {!state.renderReturn && state.currentUser?.canUseAIAnalysis && (
                <div className="flex items-center gap-2 flex-wrap px-4 py-2 bg-white border-b border-slate-200">
                  <button onClick={() => setState(p => ({ ...p, currentTab: 'renderStudio', estudio3dPreset: { tipo: 'cocina' } }))}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-bold text-white bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 shadow-sm"
                    title="Diseñar esta cocina en Estudio 3D (render IA fotorrealista)">
                    <Sparkles size={13} /> Diseñar en Estudio 3D
                  </button>
                </div>
              )}
              {state.renderReturn && (
                <div className="flex items-center gap-2 flex-wrap px-4 py-2 bg-indigo-50 border-b border-indigo-200">
                  <span className="text-[11px] font-black text-indigo-700 uppercase tracking-wider">Vienes de Estudio 3D</span>
                  <button onClick={() => setState(p => ({ ...p, currentTab: 'renderStudio' }))}
                    className="px-3 py-1 rounded-full text-[11px] font-bold bg-indigo-600 text-white hover:bg-indigo-700">← Volver a Estudio 3D</button>
                  <button onClick={() => setState(p => ({ ...p, renderReturn: false }))}
                    className="px-3 py-1 rounded-full text-[11px] font-bold bg-white border border-indigo-200 text-indigo-700 hover:bg-indigo-100">Quedarme en Presupuestador 1</button>
                </div>
              )}
              <Presupuestador2
                currentUser={state.currentUser}
                logo={state.logo}
                incomingProject={state.p2IncomingProject}
                onProjectConsumed={() => setState(p => ({ ...p, p2IncomingProject: null }))}
                incomingLines={state.p2PendingLines}
                incomingLibrary={state.p2PendingLibrary}
                onLinesConsumed={() => setState(p => ({ ...p, p2PendingLines: null, p2PendingLibrary: null }))}
              /></ErrorBoundary>
            )}
            {state.currentTab === 'visualizer' && state.currentUser?.canUseAIAnalysis && (
              <Visualizer images={state.uploadedImages} state={state} setState={setState} onAddToBudget={handleAddFromVisualizer} />
            )}
            {state.currentTab === 'library' && <ErrorBoundary><ProjectLibrary state={state} setState={setState} /></ErrorBoundary>}
            {state.currentTab === 'resumenCocinas' && state.currentUser?.canUseResumenTotales === true && <ErrorBoundary><ResumenCocinas state={state} /></ErrorBoundary>}
            {state.currentTab === 'cascos' && state.currentUser?.canUseCascos === true && (
              <ErrorBoundary>
              {state.renderReturn && (
                <div className="flex items-center gap-2 flex-wrap px-4 py-2 bg-indigo-50 border-b border-indigo-200">
                  <span className="text-[11px] font-black text-indigo-700 uppercase tracking-wider">Vienes de Estudio 3D</span>
                  <button onClick={() => setState(p => ({ ...p, currentTab: 'renderStudio' }))}
                    className="px-3 py-1 rounded-full text-[11px] font-bold bg-indigo-600 text-white hover:bg-indigo-700">← Volver a Estudio 3D</button>
                  <button onClick={() => setState(p => ({ ...p, renderReturn: false }))}
                    className="px-3 py-1 rounded-full text-[11px] font-bold bg-white border border-indigo-200 text-indigo-700 hover:bg-indigo-100">Quedarme en Cocina Desmontada</button>
                </div>
              )}
              <Cascos state={state} setState={setState} />
              </ErrorBoundary>
            )}
            {state.currentTab === 'propdata' && state.currentUser?.canUsePropData === true && <ErrorBoundary><PropData state={state} /></ErrorBoundary>}
            {state.currentTab === 'armarios2' && state.currentUser?.canUseArmarios2 === true && <ErrorBoundary><Armarios2 state={state} /></ErrorBoundary>}
            {state.currentTab === 'cocinasai' && (state.currentUser?.canUseCocinasAI === true || state.currentUser?.isAdmin) && <ErrorBoundary><CocinasIA state={state} /></ErrorBoundary>}
            {state.currentTab === 'backup' && <BackupManager />}
            {state.currentTab === 'invoices' && <ErrorBoundary><Invoices currentUser={state.currentUser} /></ErrorBoundary>}
            {state.currentTab === 'rentabilidad' && <ErrorBoundary><RentabilidadPanel currentUser={state.currentUser} /></ErrorBoundary>}
            {state.currentTab === 'gastos' && <ErrorBoundary><GestionGastos currentUser={state.currentUser} /></ErrorBoundary>}
            {state.currentTab === 'luiggifloor' && <ErrorBoundary><LuiggiFloor currentUser={state.currentUser} /></ErrorBoundary>}
            {state.currentTab === 'command' && <ErrorBoundary><CommandCenter currentUser={state.currentUser} /></ErrorBoundary>}
            {state.currentTab === 'digitalizador' && state.currentUser?.canUseDigitalizador && (
              <Digitalizador state={state} setState={setState} />
            )}
            {state.currentTab === 'armarios' && state.currentUser?.canAccessArmarios && (
              <Armarios state={state} setState={setState} />
            )}
            {/* Electros — catálogo de electrodomésticos (menú principal) */}
            {state.currentTab === 'electros' && !state.currentUser?.isTienda && (
              <ErrorBoundary>
                <div className="max-w-6xl mx-auto p-4 sm:p-8">
                  <ElectrosTab
                    isMaster={!!state.currentUser?.isPrimaryAdmin}
                    isAdmin={!!state.currentUser?.isAdmin}
                  />
                </div>
              </ErrorBoundary>
            )}
            {state.currentTab === 'montajes' && state.settings?.montajesEnabled && (state.currentUser?.canAccessMontajes || state.currentUser?.isMontador) && (
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
              <ErrorBoundary><AIRenderStudio state={state} setState={setState} /></ErrorBoundary>
            )}
            {/* Kitchen 3D Designer - Panel de proyectos (mantenido por compatibilidad) */}
            {state.currentTab === 'kitchenDesigner' && (state.currentUser?.canUseKitchenDesigner || state.currentUser?.isAdmin) && (
              <KitchenDesigner3D state={state} setState={setState} onAddToBudget={handleAddFromVisualizer} />
            )}
            {/* Estudio de Cocinas — Módulo unificado */}
            {state.currentTab === 'estudioCocinas' && (state.currentUser?.canUseKitchenDesigner || state.currentUser?.canUseCocinasAI || state.currentUser?.canUseAIAnalysis) && (
              <EstudioCocinas state={state} setState={setState} />
            )}

            {/* Agentes Diseñadores en Paralelo */}
            {state.currentTab === 'agentesDisenadores' && (state.currentUser?.canUseAgentesIA || state.currentUser?.isAdmin) && (
              <ErrorBoundary><AgentesDisenadores state={state} /></ErrorBoundary>
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
               <span className="text-[8px] font-black uppercase tracking-widest text-slate-900 italic">
                 {(state.currentUser?.isCarpintero || state.currentUser?.linkedCarpinteroAdminId || state.currentUser?.canManageCarpinteroUsers)
                   ? 'CARPINTER.IO ERP v4.1'
                   : 'LUIGGI HOME ERP v4.1'}
               </span>
            </div>
          </main>

          <Suspense fallback={null}>
            {/* Panel Maestro: si el usuario es admin de división Carpinter.io (canManageCarpinteroUsers && !isAdmin)
                mostramos el panel independiente sin branding ni tabs de Luiggi Home.
                Para todos los demás (admin, gerente, comerciales) mostramos el SettingsModal completo. */}
            {state.currentUser?.canManageCarpinteroUsers && !state.currentUser?.isAdmin ? (
              <CarpinterPanel
                isOpen={state.showSettings || false}
                onClose={() => setState(p => ({...p, showSettings: false}))}
                currentUser={state.currentUser}
              />
            ) : (
              <SettingsModal 
                isOpen={state.showSettings || false} 
                onClose={() => setState(p => ({...p, showSettings: false}))} 
                state={state} 
                setState={setState} 
              />
            )}
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
