import React, { useState } from 'react';
import { LayoutDashboard, Target, Users, CalendarDays, FileBarChart } from 'lucide-react';
import CRMDashboard from './CRMDashboard';
import CRMPipeline from './CRMPipeline';
import CRMContacts from './CRMContacts';
import CRMCalendar from './CRMCalendar';

const CRM_TABS = [
  { id: 'dashboard', name: 'Resumen', icon: LayoutDashboard },
  { id: 'pipeline', name: 'Oportunidades', icon: Target },
  { id: 'contacts', name: 'Contactos', icon: Users },
];

const CRMLayout = () => {
  const [activeTab, setActiveTab] = useState('dashboard');

  return (
    <div className="h-full flex flex-col">
      {/* CRM Internal Navigation */}
      <div className="bg-white border-b border-slate-200 px-6 py-3 flex items-center gap-1 shrink-0">
        <div className="flex items-center gap-2 mr-6">
          <div className="p-2 bg-indigo-600 rounded-xl">
            <Target size={18} className="text-white" />
          </div>
          <span className="text-lg font-black text-slate-900 uppercase">Gestión Comercial</span>
        </div>
        
        <div className="flex gap-1">
          {CRM_TABS.map(tab => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-bold transition-all ${
                  isActive 
                    ? 'bg-indigo-600 text-white shadow-md' 
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
                data-testid={`crm-tab-${tab.id}`}
              >
                <Icon size={16} />
                {tab.name}
              </button>
            );
          })}
        </div>
      </div>

      {/* CRM Content */}
      <div className="flex-1 overflow-hidden">
        {activeTab === 'dashboard' && (
          <CRMDashboard onNavigate={(tab) => setActiveTab(tab)} />
        )}
        {activeTab === 'pipeline' && <CRMPipeline />}
        {activeTab === 'contacts' && <CRMContacts />}
      </div>
    </div>
  );
};

export default CRMLayout;
