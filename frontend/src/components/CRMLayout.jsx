import React, { useState } from 'react';
import { LayoutDashboard, Target, Users, CalendarDays, FileBarChart, ClipboardList } from 'lucide-react';
import CRMDashboard from './CRMDashboard';
import CRMPipeline from './CRMPipeline';
import CRMContacts from './CRMContacts';
import CRMCalendar from './CRMCalendar';
import CRMActivities from './CRMActivities';

const CRM_TABS = [
  { id: 'dashboard', name: 'Resumen', icon: LayoutDashboard },
  { id: 'pipeline', name: 'Oportunidades', icon: Target },
  { id: 'contacts', name: 'Contactos', icon: Users },
  { id: 'activities', name: 'Actividades', icon: ClipboardList },
  { id: 'calendar', name: 'Calendario', icon: CalendarDays },
];

const CRMLayout = ({ currentUser }) => {
  const [activeTab, setActiveTab] = useState('dashboard');

  return (
    <div className="h-full flex flex-col">
      {/* CRM Internal Navigation - Responsive */}
      <div className="bg-white border-b border-slate-200 px-4 md:px-6 py-3 flex flex-col md:flex-row md:items-center gap-2 md:gap-1 shrink-0">
        <div className="flex items-center gap-2 md:mr-6 pl-12 md:pl-0">
          <div className="p-2 bg-indigo-600 rounded-xl">
            <Target size={18} className="text-white" />
          </div>
          <span className="text-lg font-black text-slate-900 uppercase">CRM</span>
        </div>
        
        {/* Tabs - Horizontal scroll on mobile */}
        <div className="flex gap-1 overflow-x-auto pb-1 md:pb-0 -mx-4 px-4 md:mx-0 md:px-0 scrollbar-none">
          {CRM_TABS.map(tab => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-3 md:px-4 py-2 rounded-lg text-xs md:text-sm font-bold transition-all whitespace-nowrap shrink-0 ${
                  isActive 
                    ? 'bg-indigo-600 text-white shadow-md' 
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
                data-testid={`crm-tab-${tab.id}`}
              >
                <Icon size={16} />
                <span>{tab.name}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* CRM Content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'dashboard' && (
          <CRMDashboard onNavigate={(tab) => setActiveTab(tab)} currentUser={currentUser} />
        )}
        {activeTab === 'pipeline' && <CRMPipeline currentUser={currentUser} />}
        {activeTab === 'contacts' && <CRMContacts currentUser={currentUser} />}
        {activeTab === 'activities' && <CRMActivities currentUser={currentUser} />}
        {activeTab === 'calendar' && <CRMCalendar currentUser={currentUser} />}
      </div>
    </div>
  );
};

export default CRMLayout;
