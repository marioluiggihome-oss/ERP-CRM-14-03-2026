import React, { useState, useEffect } from 'react';
import { 
  Users, Target, TrendingUp, Euro, Phone, Calendar, Clock, 
  ArrowUpRight, ArrowDownRight, CheckCircle2, Loader2, AlertTriangle, UserX, ShoppingCart
} from 'lucide-react';
import { crmDashboardAPI, crmAnalyticsAPI } from '../services/api';

const CRMDashboard = ({ onNavigate }) => {
  const [dashboard, setDashboard] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [timeFilter, setTimeFilter] = useState('30d');

  useEffect(() => {
    loadDashboard();
    loadAnalytics();
  }, []);

  const loadDashboard = async () => {
    setIsLoading(true);
    try {
      const data = await crmDashboardAPI.get();
      setDashboard(data);
    } catch (err) {
      console.error('Error loading CRM dashboard:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const loadAnalytics = async () => {
    try {
      const data = await crmAnalyticsAPI.getInactiveClients(30, 60);
      setAnalytics(data);
    } catch (err) {
      console.error('Error loading CRM analytics:', err);
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('es-ES', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  const getStageColor = (stage) => {
    const colors = {
      lead: 'bg-blue-100 text-blue-700',
      contacted: 'bg-yellow-100 text-yellow-700',
      proposal: 'bg-purple-100 text-purple-700',
      negotiation: 'bg-orange-100 text-orange-700',
      won: 'bg-green-100 text-green-700',
      lost: 'bg-red-100 text-red-700'
    };
    return colors[stage] || 'bg-gray-100 text-gray-700';
  };

  const getStageName = (stage) => {
    const names = {
      lead: 'Nuevo Lead',
      contacted: 'Contactado',
      proposal: 'Propuesta',
      negotiation: 'Negociación',
      won: 'Ganada',
      lost: 'Perdida'
    };
    return names[stage] || stage;
  };

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center bg-slate-50">
        <Loader2 className="w-8 h-8 text-indigo-600 animate-spin" />
      </div>
    );
  }

  return (
    <div className="h-full overflow-auto bg-gradient-to-br from-slate-50 to-indigo-50 p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-black text-slate-900 uppercase tracking-tight">Dashboard CRM</h1>
        <p className="text-sm text-slate-500">Resumen de tu actividad comercial</p>
      </div>

      {/* Time Filter */}
      <div className="flex gap-2 mb-6">
        {[
          { id: '7d', label: 'Últimos 7 días' },
          { id: '30d', label: 'Últimos 30 días' },
          { id: 'month', label: 'Este mes' },
          { id: 'quarter', label: 'Este trimestre' }
        ].map(filter => (
          <button
            key={filter.id}
            onClick={() => setTimeFilter(filter.id)}
            className={`px-4 py-2 rounded-lg text-xs font-bold uppercase transition-all ${
              timeFilter === filter.id
                ? 'bg-indigo-600 text-white shadow-md'
                : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
            }`}
          >
            {filter.label}
          </button>
        ))}
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Users className="w-5 h-5 text-blue-600" />
            </div>
            <span className="flex items-center text-xs font-bold text-green-600">
              <ArrowUpRight className="w-3 h-3 mr-1" /> +12%
            </span>
          </div>
          <p className="text-2xl font-black text-slate-900">{dashboard?.totalContacts || 0}</p>
          <p className="text-xs text-slate-500 uppercase font-bold">Total Contactos</p>
        </div>

        <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Target className="w-5 h-5 text-purple-600" />
            </div>
            <span className="flex items-center text-xs font-bold text-green-600">
              <ArrowUpRight className="w-3 h-3 mr-1" /> +5
            </span>
          </div>
          <p className="text-2xl font-black text-slate-900">{dashboard?.activeOpportunities || 0}</p>
          <p className="text-xs text-slate-500 uppercase font-bold">Oportunidades Activas</p>
        </div>

        <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <TrendingUp className="w-5 h-5 text-green-600" />
            </div>
            <span className="flex items-center text-xs font-bold text-green-600">
              <ArrowUpRight className="w-3 h-3 mr-1" /> +23%
            </span>
          </div>
          <p className="text-2xl font-black text-slate-900">{dashboard?.wonThisMonth || 0}</p>
          <p className="text-xs text-slate-500 uppercase font-bold">Ganadas este Mes</p>
        </div>

        <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <div className="p-2 bg-orange-100 rounded-lg">
              <Euro className="w-5 h-5 text-orange-600" />
            </div>
            <span className="flex items-center text-xs font-bold text-green-600">
              <ArrowUpRight className="w-3 h-3 mr-1" /> +15%
            </span>
          </div>
          <p className="text-2xl font-black text-slate-900">{formatCurrency(dashboard?.pipelineValue || 0)}</p>
          <p className="text-xs text-slate-500 uppercase font-bold">Ingresos Pipeline</p>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-3 gap-6">
        {/* Top Opportunities */}
        <div className="col-span-2 bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-4 border-b border-slate-100 flex items-center justify-between">
            <h2 className="font-black text-slate-900 uppercase text-sm">Top Oportunidades</h2>
            <button 
              onClick={() => onNavigate && onNavigate('pipeline')}
              className="text-xs text-indigo-600 font-bold hover:underline flex items-center gap-1"
            >
              Ver todas <ArrowUpRight className="w-3 h-3" />
            </button>
          </div>
          <div className="divide-y divide-slate-100">
            {dashboard?.topOpportunities?.length > 0 ? (
              dashboard.topOpportunities.map((opp, idx) => (
                <div key={opp.id} className="p-4 flex items-center hover:bg-slate-50 transition-colors">
                  <div className="w-8 h-8 bg-indigo-100 rounded-full flex items-center justify-center text-indigo-600 font-black text-sm mr-4">
                    {idx + 1}
                  </div>
                  <div className="flex-1">
                    <p className="font-bold text-slate-900">{opp.title}</p>
                    <p className="text-xs text-slate-500">{opp.company || opp.contactName}</p>
                  </div>
                  <div className="text-right mr-4">
                    <p className="font-black text-slate-900">{formatCurrency(opp.value)}</p>
                    <span className={`text-xs px-2 py-0.5 rounded-full font-bold ${getStageColor(opp.stage)}`}>
                      {opp.probability}%
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <div className="p-8 text-center text-slate-400">
                <Target className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p className="font-bold">Sin oportunidades</p>
                <p className="text-xs">Crea tu primera oportunidad</p>
              </div>
            )}
          </div>
        </div>

        {/* Upcoming Activities */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-4 border-b border-slate-100 flex items-center justify-between">
            <h2 className="font-black text-slate-900 uppercase text-sm">Próximas Actividades</h2>
            <button 
              onClick={() => onNavigate && onNavigate('activities')}
              className="text-xs text-indigo-600 font-bold hover:underline flex items-center gap-1"
            >
              Ver todas <ArrowUpRight className="w-3 h-3" />
            </button>
          </div>
          <div className="divide-y divide-slate-100">
            {dashboard?.upcomingActivities?.length > 0 ? (
              dashboard.upcomingActivities.map(act => (
                <div key={act.id} className="p-4 hover:bg-slate-50 transition-colors">
                  <div className="flex items-start gap-3">
                    <div className={`p-2 rounded-lg ${
                      act.type === 'call' ? 'bg-green-100' :
                      act.type === 'meeting' ? 'bg-blue-100' :
                      act.type === 'task' ? 'bg-purple-100' : 'bg-slate-100'
                    }`}>
                      {act.type === 'call' ? <Phone className="w-4 h-4 text-green-600" /> :
                       act.type === 'meeting' ? <Calendar className="w-4 h-4 text-blue-600" /> :
                       <Clock className="w-4 h-4 text-purple-600" />}
                    </div>
                    <div className="flex-1">
                      <p className="font-bold text-slate-900 text-sm">{act.title}</p>
                      <p className="text-xs text-slate-500">{act.contactName}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-xs font-bold text-slate-600">{act.dueTime || '09:00'}</p>
                      <p className="text-xs text-slate-400">{act.dueDate || 'Hoy'}</p>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="p-8 text-center text-slate-400">
                <Calendar className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p className="font-bold">Sin actividades</p>
                <p className="text-xs">Programa tu primera actividad</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="mt-6 bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-slate-100">
          <h2 className="font-black text-slate-900 uppercase text-sm">Actividad Reciente</h2>
        </div>
        <div className="divide-y divide-slate-100">
          {dashboard?.recentActivities?.length > 0 ? (
            dashboard.recentActivities.slice(0, 5).map(act => (
              <div key={act.id} className="p-4 flex items-center gap-4 hover:bg-slate-50 transition-colors">
                <div className={`p-2 rounded-full ${
                  act.completed ? 'bg-green-100' : 'bg-slate-100'
                }`}>
                  {act.completed ? 
                    <CheckCircle2 className="w-4 h-4 text-green-600" /> :
                    <Clock className="w-4 h-4 text-slate-400" />
                  }
                </div>
                <div className="flex-1">
                  <p className="text-sm">
                    <span className="font-bold text-slate-900">{act.title}</span>
                    {act.contactName && <span className="text-slate-500"> - {act.contactName}</span>}
                  </p>
                </div>
                <p className="text-xs text-slate-400">
                  {new Date(act.createdAt).toLocaleDateString('es-ES')}
                </p>
              </div>
            ))
          ) : (
            <div className="p-8 text-center text-slate-400">
              <Clock className="w-12 h-12 mx-auto mb-2 opacity-50" />
              <p className="font-bold">Sin actividad reciente</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CRMDashboard;
