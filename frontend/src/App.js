import React, { useState, useEffect, useMemo } from 'react';
import { ShoppingCart, Settings, LogOut, FolderOpen, Sparkles, ShieldCheck, FileText, Zap } from 'lucide-react';
import "./App.css";
import BudgetTable from './components/BudgetTable';
import Visualizer from './components/Visualizer';
import ProjectLibrary from './components/ProjectLibrary';
import SettingsModal from './components/SettingsModal';
import ManufacturingReport from './components/ManufacturingReport';
import Login from './components/Login';
import TelemetryAI from './components/TelemetryAI';
import { adminUser } from './mock';
import { CATALOG_BASE_MONTADA, CATALOG_BASE_DESPIECE, DOOR_FINISHES, INITIAL_CARCASS_MATERIALS, DEFAULT_BRAND_COLOR, STORAGE_KEY } from './constants';

const initialCatalogs = [
  { id: 'cat-m-base', name: 'Cocina Montada Luiggi', manufacturer: 'Luiggi', products: CATALOG_BASE_MONTADA, module: 'montada' },
  { id: 'cat-d-base', name: 'Despiece Luiggi', manufacturer: 'Luiggi', products: CATALOG_BASE_DESPIECE, module: 'despiece' }
];

const App = () => {
  const [isManufacturingView, setIsManufacturingView] = useState(false);
  
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
      catalogs: initialCatalogs, 
      activeCatalogIds: initialCatalogs.map(c => c.id),
      users: [adminUser], 
      customerName: '', customerAddress: '', 
      budgetNumber: `EXP-2026-001`, 
      internalReference: '', logo: null,
      showDistributorPrice: false, showSettings: false,
      budgetCount: 0,
      brandColor: DEFAULT_BRAND_COLOR
    };

    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        const loadedCatalogs = parsed.catalogs && parsed.catalogs.length > 0 ? parsed.catalogs : initialCatalogs;
        const sanitizedCatalogs = loadedCatalogs.map((cat) => ({
          ...cat,
          products: cat.products.map((p) => {
            let cleanPoints = p.points;
            if (typeof p.points === 'object' && p.points !== null) {
              cleanPoints = p.points.Z1 || p.points.points || 0;
            }
            return { ...p, points: Number(cleanPoints) || 0 };
          })
        }));

        // Asegurar que el admin siempre tenga las credenciales actuales
        const updatedUsers = parsed.users ? parsed.users.map(u => 
          u.id === 'admin' ? { ...u, ...adminUser } : u
        ) : [adminUser];

        return { 
          ...defaultState,
          ...parsed, 
          uploadedImages: [], 
          currentUser: null, 
          catalogs: sanitizedCatalogs,
          users: updatedUsers,
          brandColor: parsed.brandColor || DEFAULT_BRAND_COLOR
        };
      }
    } catch (e) {
      console.error("Error persistencia:", e);
    }
    return defaultState;
  });

  useEffect(() => {
    const { currentUser, uploadedImages, ...toSave } = state; 
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(toSave));
    } catch (err) {
      console.error("Storage error:", err);
    }
  }, [state]);

  const activeBrandColor = useMemo(() => {
    return state.brandColor || DEFAULT_BRAND_COLOR;
  }, [state.brandColor]);

  const handleLogin = (user) => {
    setState(prev => ({ 
      ...prev, 
      currentUser: user,
      currentModule: user.allowedModules[0] || 'montada'
    }));
  };

  if (!state.currentUser) {
    return (
        <>
            <style>{`:root { --brand-primary: ${state.brandColor}; }`}</style>
            <Login onLogin={handleLogin} authorizedUsers={state.users} customLogo={state.logo} />
        </>
    );
  }

  const carcassMaterialName = state.carcassMaterials.find(m => m.id === state.selectedCarcassMaterialId)?.name || 'Blanco';

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
              <button 
                onClick={() => setState(p => ({...p, currentTab: 'budget'}))} 
                className={`flex flex-col items-center gap-2 p-3 rounded-2xl transition-all ${state.currentTab === 'budget' ? 'bg-brand text-white shadow-xl scale-110' : 'text-slate-500 hover:text-white hover:bg-white/10'}`}
              >
                <FileText size={22}/>
                <span className="text-[7px] font-black uppercase tracking-widest">Presupuesto</span>
              </button>
              
              {/* Solo Admin y Comerciales con canManageArticles pueden ver Telemetría IA */}
              {(state.currentUser?.isAdmin || state.currentUser?.canManageArticles) && (
                <button 
                  onClick={() => setState(p => ({...p, currentTab: 'telemetry'}))} 
                  className={`flex flex-col items-center gap-2 p-3 rounded-2xl transition-all ${state.currentTab === 'telemetry' ? 'bg-brand text-white shadow-xl scale-110' : 'text-slate-500 hover:text-white hover:bg-white/10'}`}
                >
                  <Zap size={22}/>
                  <span className="text-[7px] font-black uppercase tracking-widest">Telemetría IA</span>
                </button>
              )}
              
              <button 
                onClick={() => setState(p => ({...p, currentTab: 'visualizer'}))} 
                className={`flex flex-col items-center gap-2 p-3 rounded-2xl transition-all ${state.currentTab === 'visualizer' ? 'bg-brand text-white shadow-xl scale-110' : 'text-slate-500 hover:text-white hover:bg-white/10'}`}
              >
                <Sparkles size={22}/>
                <span className="text-[7px] font-black uppercase tracking-widest">IA Lab</span>
              </button>
              <button 
                onClick={() => setState(p => ({...p, currentTab: 'library'}))} 
                className={`flex flex-col items-center gap-2 p-3 rounded-2xl transition-all ${state.currentTab === 'library' ? 'bg-brand text-white shadow-xl scale-110' : 'text-slate-500 hover:text-white hover:bg-white/10'}`}
              >
                <FolderOpen size={22}/>
                <span className="text-[7px] font-black uppercase tracking-widest">Archivo</span>
              </button>
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
            {state.currentTab === 'telemetry' && <TelemetryAI state={state} setState={setState} />}
            {state.currentTab === 'visualizer' && <Visualizer images={state.uploadedImages} state={state} setState={setState} />}
            {state.currentTab === 'library' && <ProjectLibrary state={state} setState={setState} />}

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
        </>
      )}
    </div>
  );
};

export default App;
