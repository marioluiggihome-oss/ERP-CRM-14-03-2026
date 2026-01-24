import React, { useState, useEffect, useMemo } from 'react';
import { ShoppingCart, Settings, LogOut, FolderOpen, Sparkles, ShieldCheck, FileText, Loader, HardDrive, Users, Target, LayoutDashboard, CalendarDays, ScanLine, Wrench, Building2 } from 'lucide-react';
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
import MaintenanceScreen from './components/MaintenanceScreen';
import MaintenancePanel from './components/MaintenancePanel';
import AdminWorkView from './components/AdminWorkView';
import CommercialWorkView from './components/CommercialWorkView';
import PrescriptorAgenda from './components/PrescriptorAgenda';
import { authAPI, productsAPI, materialsAPI, settingsAPI, usersAPI } from './services/api';
import { DOOR_FINISHES, INITIAL_CARCASS_MATERIALS, DEFAULT_BRAND_COLOR, STORAGE_KEY } from './constants';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const App = () => {
  const [isManufacturingView, setIsManufacturingView] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isInMaintenance, setIsInMaintenance] = useState(false);
  const [showMaintenancePanel, setShowMaintenancePanel] = useState(false);
  const [showAdminWorkView, setShowAdminWorkView] = useState(false);
  const [showCommercialWorkView, setShowCommercialWorkView] = useState(false);
  
  const [state, setState] = useState(() => {
    const defaultState = {
      currentUser: null,
      currentModule: 'montada', 
      currentTab: 'budget', 
      uploadedImages: [], 
      budgetItemsMontada: [], 
      budgetItemsDespiece: [], 
      projects: [], 
      globalFinish: DOOR_FINISHES[0].name, 
      carcassMaterials: INITIAL_CARCASS_MATERIALS,
      selectedCarcassMaterialId: INITIAL_CARCASS_MATERIALS[0].id,
      doorColorLow: '', doorColorHigh: '', doorColorColumns: '', sideColor: '',
      pointValueMontada: 1.0, pointValueDespiece: 0.88, 
      specialIncrementWidth: 45,
      specialIncrementHeight: 45,
      specialIncrementDepth: 45,
      catalogs: [
        { id: 'cat-m-base', name: 'Cocina Montada Luiggi', manufacturer: 'Luiggi', products: [], module: 'montada' },
        { id: 'cat-d-base', name: 'Despiece Luiggi', manufacturer: 'Luiggi', products: [], module: 'despiece' }
      ], 
      activeCatalogIds: ['cat-m-base', 'cat-d-base'],
      users: [],
      customerName: '', customerAddress: '', 
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
          fetchWithTimeout(productsAPI.getAll('montada')),
          fetchWithTimeout(productsAPI.getAll('despiece')),
          fetchWithTimeout(materialsAPI.getAll()),
          fetchWithTimeout(settingsAPI.get())
        ]);

        const users = results[0].status === 'fulfilled' ? results[0].value : [];
        const productsMontada = results[1].status === 'fulfilled' ? results[1].value : [];
        const productsDespiece = results[2].status === 'fulfilled' ? results[2].value : [];
        const materials = results[3].status === 'fulfilled' ? results[3].value : [];
        const settings = results[4].status === 'fulfilled' ? results[4].value : {};

        setState(prev => ({
          ...prev,
          users,
          catalogs: [
            { id: 'cat-m-base', name: 'Cocina Montada Luiggi', manufacturer: 'Luiggi', products: productsMontada, module: 'montada' },
            { id: 'cat-d-base', name: 'Despiece Luiggi', manufacturer: 'Luiggi', products: productsDespiece, module: 'despiece' }
          ],
          carcassMaterials: materials.length > 0 ? materials : INITIAL_CARCASS_MATERIALS,
          selectedCarcassMaterialId: materials.length > 0 ? materials[0].id : INITIAL_CARCASS_MATERIALS[0].id,
          pointValueMontada: settings.pointValueMontada || 1.0,
          pointValueDespiece: settings.pointValueDespiece || 0.88,
          specialIncrementWidth: settings.specialIncrementWidth || 45,
          specialIncrementHeight: settings.specialIncrementHeight || 45,
          specialIncrementDepth: settings.specialIncrementDepth || 45,
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
    const { budgetItemsMontada, budgetItemsDespiece, projects, customerName, customerAddress, budgetNumber, internalReference, budgetCount } = state;
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({
        budgetItemsMontada,
        budgetItemsDespiece,
        projects,
        customerName,
        customerAddress,
        budgetNumber,
        internalReference,
        budgetCount
      }));
    } catch (err) {
      console.error("Storage error:", err);
    }
  }, [state.budgetItemsMontada, state.budgetItemsDespiece, state.projects, state.customerName, state.customerAddress, state.budgetNumber, state.internalReference, state.budgetCount]);

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
    setState(prev => ({ 
      ...prev, 
      currentUser: user,
      currentModule: user.allowedModules?.[0] || 'montada'
    }));
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
          <aside className="w-20 bg-slate-950 flex flex-col items-center py-10 gap-10 shrink-0 border-r border-white/5 z-50 shadow-2xl">
            <div className="w-16 h-16 bg-white rounded-2xl flex items-center justify-center shadow-lg border-b-4 border-slate-800 overflow-hidden transition-all hover:scale-105">
              {state.logo ? (
                <img src={state.logo} alt="Logo" className="w-full h-full object-contain p-1.5" />
              ) : (
                <div className="w-full h-full bg-brand flex items-center justify-center font-black text-white italic text-3xl">L</div>
              )}
            </div>
            
            <div className="flex flex-col gap-6 flex-1 w-full px-2">
              {/* CRM - Solo visible para Admin o usuarios con canAccessCRM */}
              {(state.currentUser?.isAdmin || state.currentUser?.canAccessCRM) && (
                <button 
                  onClick={() => setState(p => ({...p, currentTab: 'crm-dashboard'}))} 
                  className={`flex flex-col items-center gap-2 p-3 rounded-2xl transition-all ${
                    state.currentTab?.startsWith('crm-') 
                      ? 'bg-indigo-600 text-white shadow-xl scale-110' 
                      : 'text-slate-500 hover:text-white hover:bg-white/10'
                  }`}
                  data-testid="crm-dashboard-nav"
                >
                  <Target size={22}/>
                  <span className="text-[7px] font-black uppercase tracking-widest">CRM</span>
                </button>
              )}

              <button 
                onClick={() => setState(p => ({...p, currentTab: 'budget'}))} 
                className={`flex flex-col items-center gap-2 p-3 rounded-2xl transition-all ${state.currentTab === 'budget' ? 'bg-brand text-white shadow-xl scale-110' : 'text-slate-500 hover:text-white hover:bg-white/10'}`}
              >
                <FileText size={22}/>
                <span className="text-[7px] font-black uppercase tracking-widest">Presupuesto</span>
              </button>
              
              {/* Solo Admin y usuarios con canUseAIAnalysis pueden ver IA Lab */}
              {(state.currentUser?.isAdmin || state.currentUser?.canUseAIAnalysis) && (
                <button 
                  onClick={() => setState(p => ({...p, currentTab: 'visualizer'}))} 
                  className={`flex flex-col items-center gap-2 p-3 rounded-2xl transition-all ${state.currentTab === 'visualizer' ? 'bg-brand text-white shadow-xl scale-110' : 'text-slate-500 hover:text-white hover:bg-white/10'}`}
                >
                  <Sparkles size={22}/>
                  <span className="text-[7px] font-black uppercase tracking-widest">IA Lab</span>
                </button>
              )}
              <button 
                onClick={() => setState(p => ({...p, currentTab: 'library'}))} 
                className={`flex flex-col items-center gap-2 p-3 rounded-2xl transition-all ${state.currentTab === 'library' ? 'bg-brand text-white shadow-xl scale-110' : 'text-slate-500 hover:text-white hover:bg-white/10'}`}
              >
                <FolderOpen size={22}/>
                <span className="text-[7px] font-black uppercase tracking-widest">Archivo</span>
              </button>
              
              {/* Digitalizador - Solo Admin o usuarios con permiso */}
              {(state.currentUser?.isAdmin || state.currentUser?.canUseDigitalizador) && (
                <button 
                  onClick={() => setState(p => ({...p, currentTab: 'digitalizador'}))} 
                  className={`flex flex-col items-center gap-2 p-3 rounded-2xl transition-all ${state.currentTab === 'digitalizador' ? 'bg-orange-600 text-white shadow-xl scale-110' : 'text-slate-500 hover:text-white hover:bg-white/10'}`}
                  data-testid="digitalizador-nav-btn"
                >
                  <ScanLine size={22}/>
                  <span className="text-[7px] font-black uppercase tracking-widest">Digitalizador</span>
                </button>
              )}
              
              {/* Botón Panel Admin - Solo para Admin */}
              {state.currentUser?.isAdmin && (
                <button 
                  onClick={() => setShowAdminWorkView(true)} 
                  className="flex flex-col items-center gap-2 p-3 rounded-2xl transition-all text-slate-500 hover:text-white hover:bg-white/10"
                  data-testid="admin-panel-nav-btn"
                >
                  <Building2 size={22}/>
                  <span className="text-[7px] font-black uppercase tracking-widest">Panel Admin</span>
                </button>
              )}
              
              {/* Botón Mis Tiendas - Solo para Comerciales (no Admin) */}
              {!state.currentUser?.isAdmin && state.currentUser?.isRepresentative && (
                <button 
                  onClick={() => setShowCommercialWorkView(true)} 
                  className="flex flex-col items-center gap-2 p-3 rounded-2xl transition-all text-purple-400 hover:text-white hover:bg-purple-500/30"
                  data-testid="commercial-panel-nav-btn"
                >
                  <Users size={22}/>
                  <span className="text-[7px] font-black uppercase tracking-widest">Mis Tiendas</span>
                </button>
              )}
            </div>

            <div className="mt-auto flex flex-col gap-6 w-full px-2">
              {/* Solo mostrar Panel Maestro si es Admin o Comercial */}
              {(state.currentUser?.isAdmin || state.currentUser?.isRepresentative) && (
                <button 
                    onClick={() => setState(p => ({...p, showSettings: true}))} 
                    className={`flex flex-col items-center gap-2 p-3 rounded-2xl transition-all ${state.showSettings ? 'bg-brand text-white shadow-lg' : 'text-slate-500 hover:text-white hover:bg-white/10'}`}
                >
                    <Settings size={22}/>
                    <span className="text-[7px] font-black uppercase tracking-widest">Master</span>
                </button>
              )}
              <button 
                  onClick={() => setState(p => ({...p, currentUser: null}))}
                  className="flex flex-col items-center gap-2 p-3 rounded-2xl text-slate-500 hover:text-red-500 transition-all"
              >
                  <LogOut size={22}/>
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
            {state.currentTab === 'visualizer' && <Visualizer images={state.uploadedImages} state={state} setState={setState} />}
            {state.currentTab === 'library' && <ProjectLibrary state={state} setState={setState} />}
            {state.currentTab === 'backup' && <BackupManager />}
            {state.currentTab === 'digitalizador' && <Digitalizador state={state} />}
            
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
        </>
      )}
    </div>
  );
};

export default App;
