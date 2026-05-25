import React, { useState, useEffect } from 'react';
import {
  Users, Target, TrendingUp, Euro, Phone, Calendar, Clock,
  ArrowUpRight, CheckCircle2, Loader2, AlertTriangle, UserX,
  ShoppingCart, ChevronRight, Activity, Zap
} from 'lucide-react';
import { crmDashboardAPI, crmAnalyticsAPI } from '../services/api';

const CRMDashboard = ({ onNavigate, currentUser }) => {
  const [dashboard, setDashboard] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [timeFilter, setTimeFilter] = useState('30d');

  useEffect(() => { loadDashboard(); loadAnalytics(); }, [currentUser]);

  const loadDashboard = async () => {
    setIsLoading(true);
    try {
      const canViewAll = currentUser?.isAdmin || currentUser?.isGerente || currentUser?.isDirectorComercial;
      const options = canViewAll ? {} : { assignedTo: currentUser?.id, isAdmin: false };
      const data = await crmDashboardAPI.get(options);
      setDashboard(data);
    } catch (err) { console.error(err); }
    finally { setIsLoading(false); }
  };

  const loadAnalytics = async () => {
    try {
      const data = await crmAnalyticsAPI.getInactiveClients(30, 60);
      setAnalytics(data);
    } catch (err) { console.error(err); }
  };

  const fmt = (v) => new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR', minimumFractionDigits: 0 }).format(v || 0);

  const stageLabel = (s) => ({ lead: 'Nuevo', contacted: 'Contactado', proposal: 'Presupuesto', negotiation: 'Negociación', won: 'Ganado', lost: 'Perdido' }[s] || s);
  const stageColor = (s) => ({ lead: 'bg-blue-100 text-blue-700', contacted: 'bg-yellow-100 text-yellow-700', proposal: 'bg-purple-100 text-purple-700', negotiation: 'bg-orange-100 text-orange-700', won: 'bg-green-100 text-green-700', lost: 'bg-red-100 text-red-700' }[s] || 'bg-slate-100 text-slate-600');

  const actIcon = (type) => {
    if (type === 'call') return <Phone className="w-3.5 h-3.5 text-green-600" />;
    if (type === 'meeting') return <Calendar className="w-3.5 h-3.5 text-blue-600" />;
    return <Clock className="w-3.5 h-3.5 text-slate-400" />;
  };
  const actBg = (type) => ({ call: 'bg-green-100', meeting: 'bg-blue-100', task: 'bg-purple-100' }[type] || 'bg-slate-100');

  if (isLoading) return (
    <div className="h-full flex items-center justify-center bg-slate-50">
      <div className="text-center">
        <Loader2 className="w-10 h-10 text-indigo-500 animate-spin mx-auto mb-3" />
        <p className="text-sm font-bold text-slate-400 uppercase tracking-widest">Cargando datos...</p>
      </div>
    </div>
  );

  const stats = [
    { label: 'Contactos', value: dashboard?.totalContacts || 0, icon: Users, color: 'from-blue-500 to-blue-600', bg: 'bg-blue-50', text: 'text-blue-600' },
    { label: 'Oportunidades', value: dashboard?.activeOpportunities || 0, icon: Target, color: 'from-purple-500 to-purple-600', bg: 'bg-purple-50', text: 'text-purple-600' },
    { label: 'Ventas mes', value: dashboard?.wonThisMonth || 0, icon: TrendingUp, color: 'from-green-500 to-green-600', bg: 'bg-green-50', text: 'text-green-600' },
    { label: 'Pipeline', value: fmt(dashboard?.pipelineValue), icon: Euro, color: 'from-orange-500 to-orange-600', bg: 'bg-orange-50', text: 'text-orange-600', isText: true },
  ];

  return (
    <div className="h-full overflow-auto bg-slate-50">
      {/* Hero header */}
      <div className="bg-gradient-to-r from-indigo-600 to-indigo-800 px-4 sm:px-6 pt-6 pb-10">
        <div className="flex items-center justify-between mb-1">
          <div>
            <p className="text-indigo-200 text-xs font-bold uppercase tracking-widest">CRM · Resumen comercial</p>
            <h1 className="text-white text-xl sm:text-2xl font-black mt-0.5">
              Hola, {currentUser?.clientName?.split(' ')[0] || 'Comercial'} 👋
            </h1>
          </div>
          <div className="p-2.5 bg-white/10 rounded-2xl">
            <Activity className="w-6 h-6 text-white" />
          </div>
        </div>
        <p className="text-indigo-300 text-xs mt-1">
          {new Date().toLocaleDateString('es-ES', { weekday: 'long', day: 'numeric', month: 'long' })}
        </p>

        {/* Filtro tiempo */}
        <div className="flex gap-1.5 mt-4 overflow-x-auto pb-1 scrollbar-none">
          {[['7d','7 días'],['30d','30 días'],['month','Este mes'],['quarter','Trimestre']].map(([id, lbl]) => (
            <button key={id} onClick={() => setTimeFilter(id)}
              className={`px-3 py-1.5 rounded-lg text-[10px] font-black uppercase whitespace-nowrap transition-all ${timeFilter === id ? 'bg-white text-indigo-700 shadow' : 'bg-white/15 text-white/80 hover:bg-white/25'}`}>
              {lbl}
            </button>
          ))}
        </div>
      </div>

      <div className="px-3 sm:px-6 -mt-6 pb-8 space-y-4 sm:space-y-6">
        {/* Stats flotantes sobre el hero */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {stats.map((s, i) => {
            const Icon = s.icon;
            return (
              <div key={i} className="bg-white rounded-2xl p-3 sm:p-4 shadow-lg border border-slate-100">
                <div className={`inline-flex p-2 ${s.bg} rounded-xl mb-2`}>
                  <Icon className={`w-4 h-4 sm:w-5 sm:h-5 ${s.text}`} />
                </div>
                <p className={`text-lg sm:text-2xl font-black text-slate-900 ${s.isText ? 'text-sm sm:text-lg' : ''}`}>
                  {s.value}
                </p>
                <p className="text-[9px] sm:text-[10px] font-black text-slate-400 uppercase tracking-wider mt-0.5">{s.label}</p>
              </div>
            );
          })}
        </div>

        {/* Oportunidades + Seguimientos */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          {/* Mejores oportunidades */}
          <div className="md:col-span-3 bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
            <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <div className="w-1.5 h-5 bg-indigo-600 rounded-full" />
                <h2 className="font-black text-slate-900 text-sm uppercase">Oportunidades activas</h2>
              </div>
              <button onClick={() => onNavigate?.('pipeline')}
                className="flex items-center gap-1 text-[10px] font-black text-indigo-600 uppercase hover:text-indigo-800">
                Ver todas <ChevronRight className="w-3 h-3" />
              </button>
            </div>
            <div className="divide-y divide-slate-50">
              {dashboard?.topOpportunities?.length > 0 ? dashboard.topOpportunities.map((opp, i) => (
                <div key={opp.id} className="flex items-center gap-3 px-5 py-3.5 hover:bg-slate-50 transition-colors">
                  <div className="w-7 h-7 bg-gradient-to-br from-indigo-500 to-indigo-600 rounded-xl flex items-center justify-center text-white font-black text-xs flex-shrink-0">
                    {i + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-bold text-slate-900 text-sm truncate">{opp.title}</p>
                    <p className="text-xs text-slate-400 truncate">{opp.company || opp.contactName}</p>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <p className="font-black text-slate-900 text-sm">{fmt(opp.value)}</p>
                    <span className={`text-[9px] font-black px-2 py-0.5 rounded-full ${stageColor(opp.stage)}`}>
                      {stageLabel(opp.stage)}
                    </span>
                  </div>
                </div>
              )) : (
                <div className="flex flex-col items-center justify-center py-10 text-slate-300">
                  <Target className="w-10 h-10 mb-2" />
                  <p className="font-black text-sm text-slate-400">Sin oportunidades activas</p>
                  <p className="text-xs text-slate-300 mt-1">Crea tu primera oportunidad</p>
                </div>
              )}
            </div>
          </div>

          {/* Próximos seguimientos */}
          <div className="md:col-span-2 bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
            <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <div className="w-1.5 h-5 bg-green-500 rounded-full" />
                <h2 className="font-black text-slate-900 text-sm uppercase">Seguimientos</h2>
              </div>
              <button onClick={() => onNavigate?.('activities')}
                className="flex items-center gap-1 text-[10px] font-black text-indigo-600 uppercase hover:text-indigo-800">
                Ver todos <ChevronRight className="w-3 h-3" />
              </button>
            </div>
            <div className="divide-y divide-slate-50">
              {dashboard?.upcomingActivities?.length > 0 ? dashboard.upcomingActivities.map(act => (
                <div key={act.id} className="flex items-center gap-3 px-5 py-3.5 hover:bg-slate-50 transition-colors">
                  <div className={`p-2 rounded-xl flex-shrink-0 ${actBg(act.type)}`}>
                    {actIcon(act.type)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-bold text-slate-900 text-xs truncate">{act.title}</p>
                    <p className="text-[10px] text-slate-400 truncate">{act.contactName}</p>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <p className="text-xs font-black text-slate-600">{act.dueTime || '—'}</p>
                    <p className="text-[10px] text-slate-300">{act.dueDate || 'Hoy'}</p>
                  </div>
                </div>
              )) : (
                <div className="flex flex-col items-center justify-center py-10 text-slate-300">
                  <Calendar className="w-10 h-10 mb-2" />
                  <p className="font-black text-sm text-slate-400">Sin seguimientos</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Historial reciente */}
        {dashboard?.recentActivities?.length > 0 && (
          <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
            <div className="flex items-center gap-2 px-5 py-4 border-b border-slate-100">
              <div className="w-1.5 h-5 bg-slate-400 rounded-full" />
              <h2 className="font-black text-slate-900 text-sm uppercase">Actividad reciente</h2>
            </div>
            <div className="divide-y divide-slate-50">
              {dashboard.recentActivities.slice(0, 5).map(act => (
                <div key={act.id} className="flex items-center gap-3 px-5 py-3 hover:bg-slate-50 transition-colors">
                  <div className={`p-1.5 rounded-full flex-shrink-0 ${act.completed ? 'bg-green-100' : 'bg-slate-100'}`}>
                    {act.completed
                      ? <CheckCircle2 className="w-3.5 h-3.5 text-green-600" />
                      : <Clock className="w-3.5 h-3.5 text-slate-400" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-slate-900 truncate">
                      <span className="font-bold">{act.title}</span>
                      {act.contactName && <span className="text-slate-400"> · {act.contactName}</span>}
                    </p>
                  </div>
                  <p className="text-[10px] text-slate-300 flex-shrink-0 ml-2">
                    {new Date(act.createdAt).toLocaleDateString('es-ES')}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Alertas clientes inactivos */}
        {analytics && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Sin presupuesto +30d */}
            <div className="bg-white rounded-2xl shadow-sm border border-amber-100 overflow-hidden">
              <div className="flex items-center gap-3 px-5 py-4 bg-gradient-to-r from-amber-50 to-orange-50 border-b border-amber-100">
                <div className="p-2 bg-amber-500 rounded-xl">
                  <AlertTriangle className="w-4 h-4 text-white" />
                </div>
                <div>
                  <h3 className="font-black text-amber-900 text-xs uppercase">Sin presupuesto +30 días</h3>
                  <p className="text-[10px] text-amber-600 font-bold">
                    {analytics.summary?.totalWithoutOffer30Days || 0} contactos
                  </p>
                </div>
              </div>
              <div className="divide-y divide-amber-50 max-h-56 overflow-y-auto">
                {analytics.withoutRecentOffer?.length > 0 ? analytics.withoutRecentOffer.slice(0, 6).map(c => (
                  <div key={c.id} className="flex items-center justify-between px-5 py-2.5 hover:bg-amber-50/50">
                    <div className="flex items-center gap-2 min-w-0">
                      <UserX className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
                      <div className="min-w-0">
                        <p className="font-bold text-slate-800 text-xs truncate">{c.name}</p>
                        <p className="text-[10px] text-slate-400 truncate">{c.company || c.email}</p>
                      </div>
                    </div>
                    <span className="text-[10px] font-black text-amber-700 bg-amber-100 px-2 py-0.5 rounded-full ml-2 flex-shrink-0">
                      {c.daysWithoutOffer}d
                    </span>
                  </div>
                )) : (
                  <div className="flex flex-col items-center py-8 text-amber-300">
                    <CheckCircle2 className="w-8 h-8 mb-1" />
                    <p className="text-xs font-black text-amber-500">¡Todos al día!</p>
                  </div>
                )}
              </div>
            </div>

            {/* Sin compra +60d */}
            <div className="bg-white rounded-2xl shadow-sm border border-red-100 overflow-hidden">
              <div className="flex items-center gap-3 px-5 py-4 bg-gradient-to-r from-red-50 to-rose-50 border-b border-red-100">
                <div className="p-2 bg-red-500 rounded-xl">
                  <ShoppingCart className="w-4 h-4 text-white" />
                </div>
                <div>
                  <h3 className="font-black text-red-900 text-xs uppercase">Sin compra +60 días</h3>
                  <p className="text-[10px] text-red-600 font-bold">
                    {analytics.summary?.totalWithoutPurchase60Days || 0} contactos
                  </p>
                </div>
              </div>
              <div className="divide-y divide-red-50 max-h-56 overflow-y-auto">
                {analytics.withoutRecentPurchase?.length > 0 ? analytics.withoutRecentPurchase.slice(0, 6).map(c => (
                  <div key={c.id} className="flex items-center justify-between px-5 py-2.5 hover:bg-red-50/50">
                    <div className="flex items-center gap-2 min-w-0">
                      <UserX className="w-3.5 h-3.5 text-red-400 flex-shrink-0" />
                      <div className="min-w-0">
                        <p className="font-bold text-slate-800 text-xs truncate">{c.name}</p>
                        <p className="text-[10px] text-slate-400 truncate">{c.company || c.email}</p>
                      </div>
                    </div>
                    <span className={`text-[10px] font-black px-2 py-0.5 rounded-full ml-2 flex-shrink-0 ${c.daysWithoutPurchase >= 90 ? 'text-red-700 bg-red-100' : 'text-orange-700 bg-orange-100'}`}>
                      {c.daysWithoutPurchase === 9999 ? 'Nunca' : `${c.daysWithoutPurchase}d`}
                    </span>
                  </div>
                )) : (
                  <div className="flex flex-col items-center py-8 text-red-300">
                    <CheckCircle2 className="w-8 h-8 mb-1" />
                    <p className="text-xs font-black text-red-500">¡Excelente!</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CRMDashboard;
