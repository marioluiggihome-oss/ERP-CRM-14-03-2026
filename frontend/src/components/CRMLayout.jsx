/*
 * © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
import React, { useState, useEffect } from 'react';
import { LayoutDashboard, Target, Users, CalendarDays, ClipboardList, Mic, Megaphone, LifeBuoy, Zap, Database } from 'lucide-react';
import CRMDashboard from './CRMDashboard';
import CRMPipeline from './CRMPipeline';
import CRMContacts from './CRMContacts';
import CRMCalendar from './CRMCalendar';
import CRMActivities from './CRMActivities';
import CRMParteDiario from './CRMParteDiario';
import CRMMarketing from './CRMMarketing';
import CRMPostventa from './CRMPostventa';
import CRMAutomation from './CRMAutomation';
import ApolloProspeccion from './ApolloProspeccion';

const CRM_TABS = [
  { id: 'dashboard',   name: 'Resumen',       icon: LayoutDashboard, color: 'text-indigo-600',  activeBg: 'bg-indigo-600' },
  { id: 'apollo',      name: 'Base de datos', icon: Database,       color: 'text-amber-600',   activeBg: 'bg-amber-600' },
  { id: 'pipeline',    name: 'Oportunidades', icon: Target,          color: 'text-purple-600',  activeBg: 'bg-purple-600' },
  { id: 'contacts',    name: 'Contactos',     icon: Users,           color: 'text-blue-600',    activeBg: 'bg-blue-600' },
  { id: 'activities',  name: 'Actividades',   icon: ClipboardList,   color: 'text-green-600',   activeBg: 'bg-green-600' },
  { id: 'calendar',    name: 'Calendario',    icon: CalendarDays,    color: 'text-orange-600',  activeBg: 'bg-orange-600' },
  { id: 'parte',       name: 'Parte diario',  icon: Mic,             color: 'text-pink-600',    activeBg: 'bg-pink-600' },
  { id: 'marketing',   name: 'Marketing',     icon: Megaphone,       color: 'text-rose-600',    activeBg: 'bg-rose-600' },
  { id: 'postventa',   name: 'Postventa',     icon: LifeBuoy,        color: 'text-cyan-600',    activeBg: 'bg-cyan-600' },
  { id: 'automation',  name: 'Automatizar',   icon: Zap,             color: 'text-amber-500',   activeBg: 'bg-amber-500' },
];

const CRMLayout = ({ currentUser, initialTab, focusEvent }) => {
  const [activeTab, setActiveTab] = useState(initialTab && CRM_TABS.some(t => t.id === initialTab) ? initialTab : 'dashboard');
  const activeConfig = CRM_TABS.find(t => t.id === activeTab);

  // Si App pide una pestaña concreta (p. ej. "Ir al calendario"), saltar a ella
  useEffect(() => {
    if (initialTab && CRM_TABS.some(t => t.id === initialTab)) setActiveTab(initialTab);
  }, [initialTab, focusEvent]);

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Top Nav */}
      <div className="hueco-logo bg-white border-b border-slate-100 px-3 sm:px-6 flex items-center gap-2 shrink-0 overflow-x-auto scrollbar-none">
        {CRM_TABS.map(tab => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              data-testid={`crm-tab-${tab.id}`}
              className={`relative flex items-center gap-1.5 px-3 py-3.5 text-xs font-black uppercase tracking-wide whitespace-nowrap shrink-0 transition-all border-b-2 ${
                isActive
                  ? `border-indigo-600 text-indigo-700`
                  : 'border-transparent text-slate-400 hover:text-slate-700 hover:border-slate-200'
              }`}
            >
              <Icon size={14} />
              <span className="hidden sm:inline">{tab.name}</span>
            </button>
          );
        })}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'dashboard'  && <CRMDashboard onNavigate={setActiveTab} currentUser={currentUser} />}
        {activeTab === 'apollo'     && <ApolloProspeccion currentUser={currentUser} onNavigateToContacts={setActiveTab} />}
        {activeTab === 'pipeline'   && <CRMPipeline currentUser={currentUser} />}
        {activeTab === 'contacts'   && <CRMContacts currentUser={currentUser} />}
        {activeTab === 'activities' && <CRMActivities currentUser={currentUser} />}
        {activeTab === 'calendar'   && <CRMCalendar currentUser={currentUser} focusEvent={focusEvent} />}
        {activeTab === 'parte'      && <CRMParteDiario currentUser={currentUser} />}
        {activeTab === 'marketing'  && <CRMMarketing currentUser={currentUser} />}
        {activeTab === 'postventa'  && <CRMPostventa currentUser={currentUser} />}
        {activeTab === 'automation' && <CRMAutomation currentUser={currentUser} />}
      </div>
    </div>
  );
};

export default CRMLayout;
