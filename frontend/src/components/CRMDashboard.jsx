/*
 * © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
import React, { useState, useEffect, useMemo } from 'react';
import {
  Users, Target, TrendingUp, Euro, Phone, Calendar, Clock,
  ArrowUpRight, CheckCircle2, Loader2, AlertTriangle, UserX,
  ShoppingCart, ChevronRight, Activity, Zap, BarChart3, Percent,
  Download, Mail, MapPin, FileText
} from 'lucide-react';
import { crmDashboardAPI, crmAnalyticsAPI } from '../services/api';

const CRMDashboard = ({ onNavigate, currentUser }) => {
  const [dashboard, setDashboard] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [timeFilter, setTimeFilter] = useState('all');

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
  const fmtK = (v) => {
    const n = Number(v) || 0;
    if (n >= 1000) return `${(n / 1000).toFixed(1)}k\u20AC`;
    return `${n.toFixed(0)}\u20AC`;
  };

  const stageLabel = (s) => ({ lead: 'Prospecto', contacted: 'Contactado', proposal: 'Propuesta', negotiation: 'Negociación', won: 'Ganada', lost: 'Perdida' }[s] || s);
  const stageColor = (s) => ({ lead: 'bg-blue-100 text-blue-700', contacted: 'bg-cyan-100 text-cyan-700', proposal: 'bg-purple-100 text-purple-700', negotiation: 'bg-orange-100 text-orange-700', won: 'bg-green-100 text-green-700', lost: 'bg-red-100 text-red-700' }[s] || 'bg-slate-100 text-slate-600');
  const stageBgBar = (s) => ({ lead: 'bg-blue-500', contacted: 'bg-cyan-500', proposal: 'bg-purple-500', negotiation: 'bg-orange-500', won: 'bg-green-500', lost: 'bg-red-400' }[s] || 'bg-slate-400');

  const actIcon = (type) => {
    if (type === 'call') return <Phone className="w-3.5 h-3.5 text-green-600" />;
    if (type === 'meeting') return <Calendar className="w-3.5 h-3.5 text-blue-600" />;
    if (type === 'email') return <Mail className="w-3.5 h-3.5 text-purple-600" />;
    if (type === 'visit') return <MapPin className="w-3.5 h-3.5 text-orange-600" />;
    return <Clock className="w-3.5 h-3.5 text-slate-400" />;
  };
  const actBadge = (type) => ({ call: 'Llamada', meeting: 'Reunión', email: 'Email', visit: 'Visita', task: 'Tarea' }[type] || 'Tarea');
  const actBadgeColor = (type) => ({ call: 'bg-green-100 text-green-700', meeting: 'bg-blue-100 text-blue-700', email: 'bg-purple-100 text-purple-700', visit: 'bg-orange-100 text-orange-700' }[type] || 'bg-slate-100 text-slate-600');

  // KPIs
  const winRate = useMemo(() => {
    const won = dashboard?.wonThisMonth || 0;
    const lost = dashboard?.lostThisMonth || 0;
    const total = won + lost;
    return total > 0 ? Math.round((won / total) * 100) : 0;
  }, [dashboard]);

  const ticketMedio = useMemo(() => {
    const won = dashboard?.wonThisMonth || 0;
    const totalValue = dashboard?.wonValueThisMonth || 0;
    return won > 0 ? totalValue / won : 0;
  }, [dashboard]);

  const previsionPonderada = useMemo(() => {
    const opps = dashboard?.topOpportunities || [];
    return opps.reduce((sum, opp) => sum + ((opp.value || 0) * ((opp.probability || 50) / 100)), 0);
  }, [dashboard]);

  // Embudo
  const funnelStages = useMemo(() => {
    const stages = dashboard?.pipelineByStage || {};
    const order = ['lead', 'contacted', 'proposal', 'negotiation', 'won'];
    const labels = { lead: 'Prospecto', contacted: 'Contactado', proposal: 'Propuesta', negotiation: 'Negociación', won: 'Ganada' };
    const colors = { lead: 'bg-blue-500', contacted: 'bg-cyan-500', proposal: 'bg-purple-500', negotiation: 'bg-orange-500', won: 'bg-green-500' };
    const totalValue = order.reduce((s, st) => s + (stages[st]?.value || 0), 0);
    return order.map(s => ({
      id: s,
      label: labels[s],
      count: stages[s]?.count || 0,
      value: stages[s]?.value || 0,
      color: colors[s],
      pct: totalValue > 0 ? Math.round(((stages[s]?.value || 0) / totalValue) * 100) : 0,
      width: totalValue > 0 ? Math.max(((stages[s]?.value || 0) / totalValue) * 100, 5) : 5
    }));
  }, [dashboard]);

  const totalPipeline = funnelStages.reduce((s, st) => s + st.value, 0);
  const totalOps = funnelStages.reduce((s, st) => s + st.count, 0);

  // Top oportunidades por valor esperado
  const topByExpected = useMemo(() => {
    const opps = dashboard?.topOpportunities || [];
    return [...opps]
      .map(o => ({ ...o, expected: (o.value || 0) * ((o.probability || 50) / 100) }))
      .sort((a, b) => b.expected - a.expected)
      .slice(0, 5);
  }, [dashboard]);

  const maxExpected = topByExpected.length > 0 ? Math.max(...topByExpected.map(o => o.expected)) : 1;

  // Exportar Excel
  const exportExcel = () => {
    const opps = dashboard?.topOpportunities || [];
    if (opps.length === 0) { alert('No hay oportunidades para exportar'); return; }
    const header = 'Oportunidad\tCliente\tEtapa\tImporte\tProbabilidad\n';
    const rows = opps.map(o => `${o.title}\t${o.company || o.contactName}\t${stageLabel(o.stage)}\t${o.value || 0}\t${o.probability || 50}%`).join('\n');
    const blob = new Blob([header + rows], { type: 'text/tab-separated-values' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = `pipeline_${new Date().toISOString().slice(0,10)}.xls`;
    a.click(); URL.revokeObjectURL(url);
  };

  const API_URL = process.env.REACT_APP_BACKEND_URL;

  // 💾 DESCARGAR BACKUP CRM EN JSON
  const descargarBackupCRM = async () => {
    try {
      const token = localStorage.getItem('token');
      const r = await fetch(`${API_URL}/api/crm/export-backup`, {
        headers: { ...(token ? { 'Authorization': `Bearer ${token}` } : {}) }
      });
      if (!r.ok) throw new Error('Error al descargar backup CRM');
      const blob = await r.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `backup_crm_${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
    } catch (e) {
      alert(`Error al exportar backup: ${e.message}`);
    }
  };

  // 🧹 VACIADO SEGURO DE DATOS CRM (PROTEGIENDO EL DIGITALIZADOR)
  const ejecutarVaciadoSeguroCRM = async () => {
    const ok = window.confirm(
      "⚠️ VACIADO SEGURO DE DATOS DEL CRM\n\n" +
      "1. Se creará PRIMERO una copia de seguridad automática en el servidor.\n" +
      "2. Se vaciarán los contactos, oportunidades y agendas del CRM.\n" +
      "3. 🔒 EL DIGITALIZADOR Y SUS PLANTILLAS PERMANECEN 100% INTACTOS.\n\n" +
      "¿Deseas guardar la copia y proceder con el vaciado del CRM?"
    );
    if (!ok) return;

    try {
      const token = localStorage.getItem('token');
      const r = await fetch(`${API_URL}/api/crm/purge-safe`, {
        method: 'POST',
        headers: { ...(token ? { 'Authorization': `Bearer ${token}` } : {}) }
      });
      if (!r.ok) { const err = await r.json(); throw new Error(err.detail || 'Error en el servidor'); }
      const res = await r.json();

      // Limpiar claves locales del CRM
      localStorage.removeItem('crm_deals');
      localStorage.removeItem('crm_contacts');
      localStorage.removeItem('crm_companies');
      localStorage.removeItem('crm_activities');

      alert(`✓ ¡Vaciado del CRM completado!\n\n- Copia guardada en: ${res.backupFile}\n- ${res.message}`);
      loadDashboard();
    } catch (e) {
      alert(`Error durante el vaciado seguro: ${e.message}`);
    }
  };

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center bg-slate-50">
        <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="h-full overflow-auto bg-slate-50">
      {/* Hero header */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-900 to-purple-900 px-4 sm:px-6 pt-5 pb-10">
        <div className="flex items-center justify-between mb-1 flex-wrap gap-3">
          <div>
            <h1 className="text-white text-xl sm:text-2xl font-black">Panel CRM</h1>
            <p className="text-indigo-300 text-xs mt-0.5">
              Resumen del día · {new Date().toLocaleDateString('es-ES', { weekday: 'long', day: 'numeric', month: 'long' })}
            </p>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            <button onClick={descargarBackupCRM}
              className="flex items-center gap-2 px-3.5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold shadow transition-all border border-indigo-400/30"
              title="Descargar copia de seguridad exclusiva de los datos del CRM en JSON">
              <Download size={14} /> Backup CRM (JSON)
            </button>
            <button onClick={exportExcel}
              className="flex items-center gap-2 px-3.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold shadow transition-all">
              <Download size={14} /> Exportar Excel
            </button>
            {(currentUser?.isAdmin || currentUser?.canAccessMaster) && (
              <button onClick={ejecutarVaciadoSeguroCRM}
                className="flex items-center gap-2 px-3.5 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-xl text-xs font-black shadow transition-all"
                title="Vaciado seguro del CRM previa copia de seguridad en servidor (Protege Digitalizador)">
                🧹 Vaciado Seguro CRM
              </button>
            )}
          </div>
        </div>

        {/* KPIs superiores */}
        <div className="grid grid-cols-2 sm:grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 mt-5">
          <div className="bg-white/10 backdrop-blur rounded-2xl p-4">
            <div className="flex items-center gap-2 mb-1">
              <Users className="w-4 h-4 text-indigo-300" />
            </div>
            <p className="text-2xl font-black text-white">{dashboard?.totalContacts || 0}</p>
            <p className="text-[10px] text-indigo-300 font-bold uppercase">Clientes activos</p>
          </div>
          <div className="bg-white/10 backdrop-blur rounded-2xl p-4">
            <div className="flex items-center gap-2 mb-1">
              <CheckCircle2 className="w-4 h-4 text-green-300" />
            </div>
            <p className="text-2xl font-black text-white">{dashboard?.upcomingActivities?.length || 0}</p>
            <p className="text-[10px] text-indigo-300 font-bold uppercase">Actividades pendientes</p>
          </div>
          <div className="bg-white/10 backdrop-blur rounded-2xl p-4">
            <div className="flex items-center gap-2 mb-1">
              <Calendar className="w-4 h-4 text-amber-300" />
            </div>
            <p className="text-2xl font-black text-white">{dashboard?.eventsToday || 0}</p>
            <p className="text-[10px] text-indigo-300 font-bold uppercase">Eventos hoy</p>
          </div>
          <div className="bg-white/10 backdrop-blur rounded-2xl p-4">
            <div className="flex items-center gap-2 mb-1">
              <TrendingUp className="w-4 h-4 text-emerald-300" />
            </div>
            <p className="text-2xl font-black text-white">{dashboard?.activeOpportunities || 0}</p>
            <p className="text-[10px] text-indigo-300 font-bold uppercase">Oportunidades</p>
          </div>
        </div>
      </div>

      <div className="px-3 sm:px-6 -mt-5 pb-8 space-y-5">
        {/* Oportunidades & Pipeline */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-5">
          <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
            <div className="flex items-center gap-2">
              <div className="w-1.5 h-5 bg-gradient-to-b from-orange-500 to-amber-500 rounded-full" />
              <h2 className="font-black text-slate-900 text-sm uppercase">Oportunidades & Pipeline</h2>
            </div>
            <div className="flex gap-1.5 flex-wrap">
              {[['month','Este mes'],['3m','Últimos 3m'],['6m','Últimos 6m'],['year','Este año'],['all','Todo']].map(([id, lbl]) => (
                <button key={id} onClick={() => setTimeFilter(id)}
                  className={`px-3 py-1.5 rounded-lg text-[10px] font-black uppercase whitespace-nowrap transition-all ${timeFilter === id ? 'bg-indigo-600 text-white shadow' : 'bg-slate-100 text-slate-500 hover:bg-slate-200'}`}>
                  {lbl}
                </button>
              ))}
            </div>
          </div>

          {/* 4 KPIs de pipeline */}
          <div className="grid grid-cols-2 sm:grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 mb-5">
            <div className="bg-slate-50 rounded-xl p-3 border border-slate-100">
              <p className="text-[10px] font-black text-slate-400 uppercase mb-1">Pipeline activo</p>
              <p className="text-xl font-black text-slate-900">{fmtK(dashboard?.pipelineValue)}</p>
              <p className="text-[10px] text-slate-400">{dashboard?.activeOpportunities || 0} oportunidades</p>
            </div>
            <div className="bg-slate-50 rounded-xl p-3 border border-slate-100">
              <p className="text-[10px] font-black text-slate-400 uppercase mb-1">Importe ganado</p>
              <p className="text-xl font-black text-emerald-700">{fmtK(dashboard?.wonValueThisMonth)}</p>
              <p className="text-[10px] text-slate-400">{dashboard?.wonThisMonth || 0} cerradas</p>
            </div>
            <div className="bg-slate-50 rounded-xl p-3 border border-slate-100">
              <p className="text-[10px] font-black text-slate-400 uppercase mb-1">Win Rate</p>
              <p className="text-xl font-black text-indigo-700">{winRate}%</p>
              <p className="text-[10px] text-slate-400">Tasa de cierre</p>
            </div>
            <div className="bg-slate-50 rounded-xl p-3 border border-slate-100">
              <p className="text-[10px] font-black text-slate-400 uppercase mb-1">Ticket medio</p>
              <p className="text-xl font-black text-amber-700">{fmtK(ticketMedio)}</p>
              <p className="text-[10px] text-slate-400">Por oportunidad</p>
            </div>
          </div>

          {/* Embudo de ventas */}
          <div className="mb-5">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-black text-slate-800 text-xs uppercase">Embudo de ventas</h3>
              <span className="text-[10px] text-slate-400">Prospecto \u2192 Negociación \u2192 Ganada</span>
            </div>
            <div className="space-y-2">
              {funnelStages.map(stage => (
                <div key={stage.id} className="flex items-center gap-3">
                  <span className="text-[10px] font-bold text-slate-500 w-20 text-right shrink-0">{stage.label}</span>
                  <div className="flex-1 h-8 bg-slate-100 rounded-lg overflow-hidden relative">
                    <div className={`h-full ${stage.color} rounded-lg transition-all duration-500 flex items-center px-2 gap-2`}
                      style={{ width: `${stage.width}%` }}>
                      <span className="text-[10px] font-black text-white whitespace-nowrap">{fmtK(stage.value)}</span>
                      {stage.count > 0 && <span className="text-[9px] text-white/80">· {stage.count} op.</span>}
                    </div>
                  </div>
                  <span className="text-[10px] font-bold text-slate-400 w-10 shrink-0 text-right">{stage.pct}%</span>
                </div>
              ))}
            </div>
            <div className="flex justify-between mt-2 text-[10px] text-slate-400">
              <span>{totalOps} oportunidades activas</span>
              <span className="font-bold">Total pipeline: {fmtK(totalPipeline)}</span>
            </div>
          </div>

          {/* Previsión de ventas */}
          <div className="border-t border-slate-100 pt-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-black text-slate-800 text-xs uppercase">Previsión de ventas</h3>
              <span className="text-[10px] text-slate-400">Valor esperado = importe × probabilidad</span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 mb-4">
              <div className="bg-indigo-50 rounded-xl p-3 border border-indigo-100">
                <p className="text-[9px] font-black text-indigo-500 uppercase">Valor esperado</p>
                <p className="text-lg font-black text-indigo-700">{fmtK(previsionPonderada)}</p>
                <p className="text-[9px] text-indigo-400">Pipeline ponderado</p>
              </div>
              <div className="bg-green-50 rounded-xl p-3 border border-green-100">
                <p className="text-[9px] font-black text-green-500 uppercase">Ganado</p>
                <p className="text-lg font-black text-green-700">{fmtK(dashboard?.wonValueThisMonth)}</p>
                <p className="text-[9px] text-green-400">{dashboard?.wonThisMonth || 0} cerradas</p>
              </div>
              <div className="bg-amber-50 rounded-xl p-3 border border-amber-100">
                <p className="text-[9px] font-black text-amber-500 uppercase">Confianza</p>
                <p className="text-lg font-black text-amber-700">{dashboard?.pipelineValue > 0 ? Math.round((previsionPonderada / dashboard.pipelineValue) * 100) : 0}%</p>
                <p className="text-[9px] text-amber-400">Media ponderada</p>
              </div>
              <div className="bg-red-50 rounded-xl p-3 border border-red-100">
                <p className="text-[9px] font-black text-red-500 uppercase">En riesgo</p>
                <p className="text-lg font-black text-red-700">
                  {(dashboard?.topOpportunities || []).filter(o => (o.value || 0) > 5000 && (o.probability || 50) < 30).length}
                </p>
                <p className="text-[9px] text-red-400">{'>'}5k\u20AC con prob. {'<'}30%</p>
              </div>
            </div>

            {/* Top oportunidades por valor esperado */}
            {topByExpected.length > 0 && (
              <div>
                <p className="text-[9px] font-black text-slate-400 uppercase mb-2">Top oportunidades por valor esperado</p>
                <div className="space-y-1.5">
                  {topByExpected.map(opp => (
                    <div key={opp.id} className="flex items-center gap-3">
                      <div className="w-1 h-5 bg-indigo-400 rounded-full shrink-0" />
                      <span className="text-xs font-bold text-slate-700 flex-1 truncate">{opp.title}</span>
                      <div className="flex-1 h-3 bg-slate-100 rounded-full overflow-hidden max-w-[200px]">
                        <div className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full" style={{ width: `${(opp.expected / maxExpected) * 100}%` }} />
                      </div>
                      <span className="text-xs font-black text-indigo-700 w-16 text-right">{fmtK(opp.expected)}</span>
                      <span className="text-[9px] text-slate-400 w-16 text-right">{opp.probability || 50}%</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Tabla de oportunidades destacadas */}
        <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
          <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <div className="w-1.5 h-5 bg-amber-500 rounded-full" />
              <h2 className="font-black text-slate-900 text-sm uppercase">Oportunidades destacadas</h2>
            </div>
            <button onClick={() => onNavigate?.('pipeline')}
              className="flex items-center gap-1 text-[10px] font-black text-indigo-600 uppercase hover:text-indigo-800">
              Ver todas <ChevronRight className="w-3 h-3" />
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 text-slate-500">
                <tr>
                  <th className="text-left px-5 py-2.5 text-[10px] font-black uppercase">Oportunidad</th>
                  <th className="text-left px-3 py-2.5 text-[10px] font-black uppercase">Cliente</th>
                  <th className="text-left px-3 py-2.5 text-[10px] font-black uppercase">Etapa</th>
                  <th className="text-right px-3 py-2.5 text-[10px] font-black uppercase">Importe</th>
                  <th className="text-right px-5 py-2.5 text-[10px] font-black uppercase">Prob.</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {(dashboard?.topOpportunities || []).map(opp => (
                  <tr key={opp.id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-5 py-3 font-bold text-slate-900">{opp.title}</td>
                    <td className="px-3 py-3 text-slate-500">{opp.company || opp.contactName}</td>
                    <td className="px-3 py-3">
                      <span className={`text-[10px] font-black px-2.5 py-1 rounded-full ${stageColor(opp.stage)}`}>
                        {stageLabel(opp.stage)}
                      </span>
                    </td>
                    <td className="px-3 py-3 text-right font-black text-emerald-700">{fmt(opp.value)}</td>
                    <td className="px-5 py-3 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <div className="w-12 h-2 bg-slate-100 rounded-full overflow-hidden">
                          <div className={`h-full rounded-full ${(opp.probability || 50) >= 70 ? 'bg-green-500' : (opp.probability || 50) >= 40 ? 'bg-orange-500' : 'bg-red-500'}`}
                            style={{ width: `${opp.probability || 50}%` }} />
                        </div>
                        <span className="text-xs font-bold text-slate-600">{opp.probability || 50}%</span>
                      </div>
                    </td>
                  </tr>
                ))}
                {(!dashboard?.topOpportunities || dashboard.topOpportunities.length === 0) && (
                  <tr><td colSpan={5} className="px-5 py-8 text-center text-slate-400">Sin oportunidades activas</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Próximos eventos + Actividades pendientes */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Próximos eventos */}
          <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
            <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <div className="w-1.5 h-5 bg-blue-500 rounded-full" />
                <h2 className="font-black text-slate-900 text-sm uppercase">Próximos eventos</h2>
              </div>
              <button onClick={() => onNavigate?.('calendar')}
                className="flex items-center gap-1 text-[10px] font-black text-indigo-600 uppercase hover:text-indigo-800">
                Ver todos <ChevronRight className="w-3 h-3" />
              </button>
            </div>
            <div className="divide-y divide-slate-50">
              {dashboard?.upcomingActivities?.filter(a => a.type === 'meeting' || a.type === 'visit').length > 0
                ? dashboard.upcomingActivities.filter(a => a.type === 'meeting' || a.type === 'visit').slice(0, 4).map(evt => {
                  const d = evt.dueDate ? new Date(evt.dueDate) : null;
                  return (
                    <div key={evt.id} className="flex items-center gap-4 px-5 py-3.5 hover:bg-slate-50 transition-colors">
                      <div className="text-center shrink-0 w-10">
                        <p className="text-lg font-black text-indigo-700">{d ? d.getDate() : '-'}</p>
                        <p className="text-[9px] font-bold text-slate-400 uppercase">{d ? d.toLocaleDateString('es-ES', { month: 'short' }) : ''}</p>
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-bold text-slate-900 text-sm truncate">{evt.title}</p>
                        <p className="text-[10px] text-slate-400 truncate">{evt.dueTime || ''} · {evt.contactName}</p>
                      </div>
                    </div>
                  );
                })
                : dashboard?.upcomingActivities?.length > 0
                  ? dashboard.upcomingActivities.slice(0, 4).map(evt => {
                    const d = evt.dueDate ? new Date(evt.dueDate) : null;
                    return (
                      <div key={evt.id} className="flex items-center gap-4 px-5 py-3.5 hover:bg-slate-50 transition-colors">
                        <div className="text-center shrink-0 w-10">
                          <p className="text-lg font-black text-indigo-700">{d ? d.getDate() : '-'}</p>
                          <p className="text-[9px] font-bold text-slate-400 uppercase">{d ? d.toLocaleDateString('es-ES', { month: 'short' }) : ''}</p>
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-bold text-slate-900 text-sm truncate">{evt.title}</p>
                          <p className="text-[10px] text-slate-400 truncate">{evt.dueTime || ''} · {evt.contactName}</p>
                        </div>
                      </div>
                    );
                  })
                  : (
                    <div className="flex flex-col items-center justify-center py-10 text-slate-300">
                      <Calendar className="w-10 h-10 mb-2" />
                      <p className="font-black text-sm text-slate-400">Sin eventos próximos</p>
                    </div>
                  )
              }
            </div>
          </div>

          {/* Actividades pendientes */}
          <div className="bg-white rounded-2xl shadow-sm border border-slate-100 overflow-hidden">
            <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <div className="w-1.5 h-5 bg-orange-500 rounded-full" />
                <h2 className="font-black text-slate-900 text-sm uppercase">Actividades pendientes</h2>
              </div>
              <button onClick={() => onNavigate?.('activities')}
                className="flex items-center gap-1 text-[10px] font-black text-indigo-600 uppercase hover:text-indigo-800">
                Ver todas <ChevronRight className="w-3 h-3" />
              </button>
            </div>
            <div className="divide-y divide-slate-50">
              {dashboard?.upcomingActivities?.length > 0 ? dashboard.upcomingActivities.slice(0, 4).map(act => (
                <div key={act.id} className="flex items-center gap-3 px-5 py-3.5 hover:bg-slate-50 transition-colors">
                  <span className={`text-[9px] font-black px-2 py-1 rounded-full shrink-0 ${actBadgeColor(act.type)}`}>
                    {actBadge(act.type)}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="font-bold text-slate-900 text-xs truncate">{act.title}</p>
                    <p className="text-[10px] text-slate-400 truncate">{act.dueDate || 'Hoy'} · {act.contactName}</p>
                  </div>
                </div>
              )) : (
                <div className="flex flex-col items-center justify-center py-10 text-slate-300">
                  <CheckCircle2 className="w-10 h-10 mb-2" />
                  <p className="font-black text-sm text-slate-400">Sin actividades pendientes</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Alertas clientes inactivos */}
        {analytics && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
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
