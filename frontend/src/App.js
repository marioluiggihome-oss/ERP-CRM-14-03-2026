import React, { useState, useEffect, useMemo } from 'react';
import { ShoppingCart, Settings, LogOut, FolderOpen, Sparkles, ShieldCheck, FileText, Loader, HardDrive, Users, Target, LayoutDashboard, CalendarDays, ScanLine, Wrench, Building2, Box, Factory, HelpCircle, ShoppingBag } from 'lucide-react';
import "./App.css";
import BudgetTable from './components/BudgetTable';
import Visualizer from './components/Visualizer';
import ProjectLibrary from './components/ProjectLibrary';
import SettingsModal from './components/SettingsModal';
import ManufacturingReport from './components/ManufacturingReport';
import Login from './components/Login';
import BackupManager from './components/BackupManager';
import CRMLayout from './components/CRMLayout';
import Digitalizador from './components/Digitalizador';
import AgendaMontajes from './components/AgendaMontajes';
import MaintenanceScreen from './components/MaintenanceScreen';
import MaintenancePanel from './components/MaintenancePanel';
import AdminWorkView from './components/AdminWorkView';
import CommercialWorkView from './components/CommercialWorkView';
import PrescriptorAgenda from './components/PrescriptorAgenda';
import Armarios from './components/Armarios';
import PortalFabrica from './components/PortalFabrica';
import UserManualModal from './components/UserManualModal';
import MisPedidos from './components/MisPedidos';
import { authAPI, productsAPI, materialsAPI, settingsAPI, usersAPI, librariesAPI } from './services/api';
import { logout as authLogout, getUser, clearTokens, isAuthenticated } from './services/authService';
import { DOOR_FINISHES, INITIAL_CARCASS_MATERIALS, DEFAULT_BRAND_COLOR, STORAGE_KEY } from './constants';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const App = () => {
  const [isManufacturingView, setIsManufacturingView] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isInMaintenance, setIsInMaintenance] = useState(false);
  const [showMaintenancePanel, setShowMaintenancePanel] = useState(false);
  const [showAdminWorkView, setShowAdminWorkView] = useState(false);
  const [showCommercialWorkView, setShowCommercialWorkView] = useState(false);
  const [showUserManual, setShowUserManual] = useState(false);
  
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

  const handleLogin = (user) => {
    // Al hacer login, limpiar los items del presupuesto para evitar 
    // que un usuario vea los datos de otro usuario
    const userLibraries = user.allowedLibraries || ['ZC'];
    const defaultLibrary = userLibraries[0] || 'ZC';
    
    setState(prev => ({ 
      ...prev, 
      currentUser: user,
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
      golaBajo: false, golaBajoColor: ''
    }));
    
    // Recargar productos de la biblioteca del usuario
    loadProductsByLibrary(defaultLibrary);
    
    // Limpiar localStorage también
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
    const ancho = furniture.ancho_estimado || furniture.width || 600;
    const alto = furniture.alto_estimado || furniture.height || 70;
    const fondo = furniture.fondo_estimado || furniture.depth || 58;
    const iaCode = furniture.codigo_sugerido;
    
    // Generar posibles códigos y buscar en catálogo
    const possibleCodes = generatePossibleCodes(tipo, subtipo, ancho, alto);
    if (iaCode) possibleCodes.unshift(iaCode);
    
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

  // Prescriptor users see ONLY their agenda - restricted access
  if (state.currentUser?.isPrescriptor) {
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
          <aside className="w-20 bg-slate-950 flex flex-col items-center py-6 gap-4 shrink-0 border-r border-white/5 z-50 shadow-2xl">
            <div className="w-14 h-14 bg-white rounded-2xl flex items-center justify-center shadow-lg border-b-4 border-slate-800 overflow-hidden transition-transform duration-200 hover:scale-105 shrink-0">
              {state.logo ? (
                <img src={state.logo} alt="Logo" className="w-full h-full object-contain p-1.5" />
              ) : (
                <div className="w-full h-full bg-brand flex items-center justify-center font-black text-white italic text-2xl">L</div>
              )}
            </div>
            
            <div className="flex flex-col gap-3 flex-1 w-full px-2 overflow-y-auto scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent">
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

                    <button 
                      onClick={() => setState(p => ({...p, currentTab: 'budget'}))} 
                      className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-colors duration-200 ${state.currentTab === 'budget' ? 'bg-brand text-white shadow-xl scale-110' : 'text-slate-500 hover:text-white hover:bg-white/10'}`}
                    >
                      <FileText size={18}/>
                      <span className="text-[7px] font-black uppercase tracking-widest">Presupuesto</span>
                    </button>
                    
                    {/* Archivo - NO visible para Tienda/Punto de Venta - JUSTO DEBAJO DE PRESUPUESTO */}
                    {!state.currentUser?.isTienda && (
                      <button 
                        onClick={() => setState(p => ({...p, currentTab: 'library'}))} 
                        className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-colors duration-200 ${state.currentTab === 'library' ? 'bg-brand text-white shadow-xl scale-110' : 'text-slate-500 hover:text-white hover:bg-white/10'}`}
                      >
                        <FolderOpen size={18}/>
                        <span className="text-[7px] font-black uppercase tracking-widest">Archivo</span>
                      </button>
                    )}
                    
                    {/* Mis Pedidos - Visible para todos los usuarios NO tienda */}
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
                    {state.settings?.montajesEnabled && (state.currentUser?.canAccessMontajes || state.currentUser?.isAdmin || state.currentUser?.isMontador) && (
                      <button 
                        onClick={() => setState(p => ({...p, currentTab: 'montajes'}))} 
                        className={`flex flex-col items-center gap-1 p-2 rounded-xl transition-colors duration-200 ${state.currentTab === 'montajes' ? 'bg-orange-600 text-white shadow-xl scale-110' : 'text-slate-500 hover:text-white hover:bg-white/10'}`}
                        data-testid="montajes-nav-btn"
                      >
                        <Wrench size={18}/>
                        <span className="text-[7px] font-black uppercase tracking-widest">Montajes</span>
                      </button>
                    )}
                    
                    {/* Portal de Fábrica - usuarios con permiso */}
                    {(state.currentUser?.canAccessFabrica || state.currentUser?.isFabrica) && (
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

            <div className="mt-auto flex flex-col gap-6 w-full px-2">
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
              
              {/* Solo mostrar Panel Maestro si es Admin o Comercial (NO para Tienda ni usuario solo Fábrica) */}
              {(state.currentUser?.isAdmin || state.currentUser?.isRepresentative) && !state.currentUser?.isTienda && !state.currentUser?.isFabrica && (
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

          <main className="flex-1 relative overflow-hidden bg-white shadow-2xl rounded-l-[3.5rem] my-2 border-l border-white/10">
            {state.currentTab === 'budget' && (
              <BudgetTable 
                items={state.currentModule === 'montada' ? state.budgetItemsMontada : state.budgetItemsDespiece} 
                catalogs={state.catalogs} 
                activeCatalogIds={state.activeCatalogIds} 
                state={state} 
                setState={setState} 
                onOpenManufacturing={() => setIsManufacturingView(true)} 
              />
            )}
            {state.currentTab === 'visualizer' && state.currentUser?.canUseAIAnalysis && (
              <Visualizer images={state.uploadedImages} state={state} setState={setState} onAddToBudget={handleAddFromVisualizer} />
            )}
            {state.currentTab === 'library' && <ProjectLibrary state={state} setState={setState} />}
            {state.currentTab === 'backup' && <BackupManager />}
            {state.currentTab === 'digitalizador' && state.currentUser?.canUseDigitalizador && (
              <Digitalizador state={state} />
            )}
            {state.currentTab === 'armarios' && state.currentUser?.canAccessArmarios && (
              <Armarios state={state} setState={setState} />
            )}
            {state.currentTab === 'montajes' && state.settings?.montajesEnabled && (state.currentUser?.canAccessMontajes || state.currentUser?.isAdmin || state.currentUser?.isMontador) && (
              <AgendaMontajes currentUser={state.currentUser} />
            )}
            
            {/* Portal de Fábrica - SOLO usuarios con permiso explícito */}
            {state.currentTab === 'fabrica' && (state.currentUser?.canAccessFabrica || state.currentUser?.isFabrica) && (
              <PortalFabrica currentUser={state.currentUser} />
            )}
            
            {/* Mis Pedidos */}
            {state.currentTab === 'misPedidos' && (
              <MisPedidos currentUser={state.currentUser} />
            )}
            
            {/* CRM - Single Component with internal navigation */}
            {state.currentTab?.startsWith('crm') && <CRMLayout currentUser={state.currentUser} />}

            <div className="absolute bottom-6 left-12 pointer-events-none opacity-20 flex items-center gap-2">
               <ShieldCheck size={14} className="text-slate-900" />
               <span className="text-[8px] font-black uppercase tracking-widest text-slate-900 italic">BLINDADO v3.2 [REACT BUILD]</span>
            </div>
          </main>

          <SettingsModal 
            isOpen={state.showSettings || false} 
            onClose={() => setState(p => ({...p, showSettings: false}))} 
            state={state} 
            setState={setState} 
          />

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
          <AdminWorkView 
            isOpen={showAdminWorkView}
            onClose={() => setShowAdminWorkView(false)}
            currentUser={state.currentUser}
          />

          {/* Commercial Work View Modal - COMMERCIAL ONLY */}
          <CommercialWorkView 
            isOpen={showCommercialWorkView}
            onClose={() => setShowCommercialWorkView(false)}
            currentUser={state.currentUser}
          />

          {/* User Manual Modal - Disponible para todos los usuarios */}
          <UserManualModal 
            isOpen={showUserManual}
            onClose={() => setShowUserManual(false)}
            currentUser={state.currentUser}
          />
        </>
      )}
    </div>
  );
};

export default App;
