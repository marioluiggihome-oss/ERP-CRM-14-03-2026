/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
import { getToken } from '../services/api';
import React, { useState, useEffect, useCallback } from 'react';
import {
  BarChart2, Users, TrendingUp, Euro, AlertTriangle, CheckCircle,
  Clock, Activity, Target, FileText, Factory, Zap, RefreshCw,
  ChevronUp, ChevronDown, Minus, Receipt, Award, UserCheck,
  ShoppingCart, Brain, Bell, ArrowRight, Loader2, Calendar
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const getHeaders = () => {
  const token = getToken();
  return { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };
};

const fmt = (v) => new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR', minimumFractionDigits: 0 }).format(v || 0);
const fmtDate = (d) => {
  if (!d) return '—';
  try { return new Date(d).toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }); }
  catch { return '—'; }
};

const ACTIVITY_LABELS = {
  login: 'Inicio sesión', logout: 'Cierre sesión',
  budget_create: 'Presupuesto creado', budget_update: 'Presupuesto editado',
  budget_export_pdf: 'PDF generado', order_create: 'Pedido creado',
  order_confirm: 'Pedido confirmado', ai_telemetry: 'Uso IA',
  report_generate: 'Informe generado', settings_update: 'Config. cambiada',
  budget_delete: 'Presupuesto eliminado',
};

const ACTIVITY_ICONS = {
  login: '🔐', logout: '🚪', budget_create: '📋', budget_update: '✏️',
  budget_export_pdf: '📄', order_create: '🛒', order_confirm: '✅',
  ai_telemetry: '🤖', report_generate: '📊', settings_update: '⚙️',
};

// ─── Componentes auxiliares ─────────────────────────────────────────────────

const KPICard = ({ title, value, subtitle, icon: Icon, color, trend, trendVal }) => (
  <div className="bg-white rounded-2xl p-4 sm:p-5 border border-slate-100 shadow-sm hover:shadow-md transition-all">
    <div className="flex items-start justify-between mb-3">
      <div className={`p-2.5 rounded-xl ${color}`}>
        <Icon className="w-5 h-5 text-white" />
      </div>
      {trend !== undefined && (
        <div className={`flex items-center gap-1 text-xs font-black px-2 py-1 rounded-lg ${trend > 0 ? 'bg-green-50 text-green-600' : trend < 0 ? 'bg-red-50 text-red-600' : 'bg-slate-50 text-slate-500'}`}>
          {trend > 0 ? <ChevronUp className="w-3 h-3" /> : trend < 0 ? <ChevronDown className="w-3 h-3" /> : <Minus className="w-3 h-3" />}
          {Math.abs(trendVal || trend)}%
        </div>
      )}
    </div>
    <p className="text-2xl sm:text-3xl font-black text-slate-900 leading-none">{value}</p>
    <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mt-1.5">{title}</p>
    {subtitle && <p className="text-xs text-slate-400 mt-1">{subtitle}</p>}
  </div>
);

const AlertBadge = ({ tipo }) => {
  const cfg = { error: 'bg-red-100 text-red-700', warning: 'bg-amber-100 text-amber-700', info: 'bg-blue-100 text-blue-700' };
  return <span className={`text-[9px] font-black px-2 py-0.5 rounded-full uppercase ${cfg[tipo] || cfg.info}`}>{tipo}</span>;
};

const MiniBar = ({ value, max, color = 'bg-indigo-500' }) => (
  <div className="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
    <div className={`h-full ${color} rounded-full transition-all`} style={{ width: `${Math.min(100, max > 0 ? (value / max) * 100 : 0)}%` }} />
  </div>
);

// ─── Componente principal ────────────────────────────────────────────────────

const CommandCenter = ({ currentUser }) => {
  const [overview, setOverview] = useState(null);
  const [usersActivity, setUsersActivity] = useState(null);
  const [alerts, setAlerts] = useState(null);
  const [timeline, setTimeline] = useState(null);
  const [performance, setPerformance] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [dayFilter, setDayFilter] = useState(30);
  const [lastRefresh, setLastRefresh] = useState(null);
  const [loadError, setLoadError] = useState(false);

  const safeFetch = async (url) => {
    try {
      const r = await fetch(url, { headers: getHeaders() });
      if (!r.ok) return null;
      return await r.json();
    } catch (e) { 
      console.error('Fetch error:', url, e);
      return null; 
    }
  };

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const base = API_URL || '';
      const [ov, ua, al, tl, pf] = await Promise.all([
        safeFetch(`${base}/api/command-center/overview`),
        safeFetch(`${base}/api/command-center/users-activity?days=${dayFilter}`),
        safeFetch(`${base}/api/command-center/alerts`),
        safeFetch(`${base}/api/command-center/activity-timeline?days=7`),
        safeFetch(`${base}/api/command-center/performance/users?days=${dayFilter}`),
      ]);
      if (ov) setOverview(ov);
      if (ua) setUsersActivity(ua);
      if (al) setAlerts(al);
      if (tl) setTimeline(tl);
      if (pf) setPerformance(pf);
      // Si NINGUNA llamada devolvió datos, el backend no es accesible (o falta REACT_APP_BACKEND_URL)
      setLoadError(!ov && !ua && !al && !tl && !pf);
      setLastRefresh(new Date());
    } catch (e) { console.error('CommandCenter load error:', e); setLoadError(true); }
    finally { setLoading(false); }
  }, [dayFilter]);

  useEffect(() => { load(); }, [load]);

  // Auto-refresh cada 5 minutos
  useEffect(() => {
    const interval = setInterval(load, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [load]);

  const TABS = [
    { id: 'overview', label: 'Resumen', icon: BarChart2 },
    { id: 'usuarios', label: 'Usuarios', icon: Users },
    { id: 'rendimiento', label: 'Rendimiento', icon: Award },
    { id: 'alertas', label: 'Alertas', icon: Bell, badge: alerts?.total },
    { id: 'actividad', label: 'Actividad', icon: Activity },
  ];

  if (loading && !overview) return (
    <div className="h-full flex items-center justify-center bg-slate-50">
      <div className="text-center">
        <Loader2 className="w-10 h-10 text-indigo-500 animate-spin mx-auto mb-3" />
        <p className="text-sm font-bold text-slate-400 uppercase tracking-widest">Cargando panel de mando...</p>
      </div>
    </div>
  );

  return (
    <div className="h-full flex flex-col bg-slate-50">
      {/* Header */}
      <div className="hueco-logo bg-gradient-to-r from-slate-900 to-slate-800 px-4 sm:px-6 py-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-slate-400 text-[10px] font-black uppercase tracking-widest">Panel de Mando</p>
            <h1 className="text-white text-xl font-black mt-0.5">Centro de Control</h1>
          </div>
          <div className="flex items-center gap-2">
            <select value={dayFilter} onChange={e => setDayFilter(Number(e.target.value))}
              className="px-3 py-1.5 bg-white/10 border border-white/20 text-white rounded-xl text-xs font-bold outline-none">
              <option value={7}>7 días</option>
              <option value={30}>30 días</option>
              <option value={90}>90 días</option>
            </select>
            <button onClick={load} disabled={loading}
              className="p-2 bg-white/10 hover:bg-white/20 text-white rounded-xl transition-all" title="Actualizar">
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
        {lastRefresh && (
          <p className="text-slate-500 text-[10px] mt-1">Actualizado: {lastRefresh.toLocaleTimeString('es-ES')}</p>
        )}

        {/* Tabs */}
        <div className="flex gap-1 mt-4 overflow-x-auto scrollbar-none">
          {TABS.map(tab => {
            const Icon = tab.icon;
            return (
              <button key={tab.id} onClick={() => setActiveTab(tab.id)}
                className={`relative flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-black uppercase whitespace-nowrap transition-all ${activeTab === tab.id ? 'bg-white text-slate-900' : 'text-slate-400 hover:text-white hover:bg-white/10'}`}>
                <Icon className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">{tab.label}</span>
                {tab.badge > 0 && (
                  <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white rounded-full text-[9px] flex items-center justify-center font-black">{tab.badge}</span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-4 sm:p-6">

        {/* Aviso de conexión: evita el "área en blanco" cuando el backend no responde */}
        {loadError && !overview && (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <AlertTriangle className="w-12 h-12 text-amber-400 mb-3" />
            <p className="font-black text-slate-700 text-sm uppercase">No se pudieron cargar los datos</p>
            <p className="text-xs text-slate-400 mt-2 max-w-sm">
              No hay conexión con el servidor. Comprueba que el backend está en marcha y que
              <span className="font-mono"> REACT_APP_BACKEND_URL</span> está configurado.
            </p>
            <button onClick={load} className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-xl text-xs font-black">
              Reintentar
            </button>
          </div>
        )}

        {/* ── RESUMEN ─────────────────────────────────────────────── */}
        {activeTab === 'overview' && overview && (
          <div className="space-y-5">
            {/* KPIs principales */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <KPICard title="Presupuestos este mes" value={overview.presupuestos.esteMes}
                subtitle={`${overview.presupuestos.total} total`} icon={FileText} color="bg-indigo-500"
                trend={overview.presupuestos.variacion} trendVal={overview.presupuestos.variacion} />
              <KPICard title="Facturado este mes" value={fmt(overview.facturacion.esteMes)}
                subtitle={`${fmt(overview.facturacion.pendienteCobro)} pendiente`} icon={Receipt} color="bg-orange-500" />
              <KPICard title="Pipeline CRM" value={fmt(overview.crm.valorPipeline)}
                subtitle={`${overview.crm.oportunidadesActivas} oportunidades activas`} icon={Target} color="bg-purple-500" />
              <KPICard title="Usuarios activos hoy" value={overview.usuarios.activosHoy}
                subtitle={`${overview.usuarios.activosSemana} esta semana`} icon={Users} color="bg-green-500" />
            </div>

            {/* Segunda fila de KPIs */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <KPICard title="Total facturado" value={fmt(overview.facturacion.totalFacturado)}
                subtitle={`${fmt(overview.facturacion.totalPagado)} cobrado`} icon={Euro} color="bg-emerald-500" />
              <KPICard title="Contactos CRM" value={overview.crm.totalContactos}
                subtitle={`+${overview.crm.contactosMes} este mes`} icon={UserCheck} color="bg-blue-500" />
              <KPICard title="Pedidos fábrica" value={overview.fabrica.totalPedidos}
                subtitle={`${overview.fabrica.pendientes} pendientes`} icon={Factory} color="bg-amber-500" />
              {overview.facturacion.facturasVencidas > 0 && (
                <KPICard title="Facturas vencidas" value={overview.facturacion.facturasVencidas}
                  subtitle="Requieren atención" icon={AlertTriangle} color="bg-red-500" />
              )}
              {overview.crm.ganadas_mes > 0 && (
                <KPICard title="Oportunidades ganadas" value={overview.crm.ganadas_mes}
                  subtitle="Este mes" icon={Award} color="bg-yellow-500" />
              )}
            </div>

            {/* Estados presupuestos */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
                <div className="px-5 py-4 border-b border-slate-100 flex items-center gap-2">
                  <div className="w-1.5 h-5 bg-indigo-500 rounded-full" />
                  <h3 className="font-black text-slate-900 text-sm uppercase">Estado Presupuestos</h3>
                </div>
                <div className="p-4 space-y-3">
                  {[
                    { key: 'borrador', label: 'Borrador', color: 'bg-slate-400' },
                    { key: 'enviado', label: 'Enviado', color: 'bg-blue-500' },
                    { key: 'aceptado', label: 'Aceptado', color: 'bg-green-500' },
                    { key: 'en_fabricacion', label: 'En Fabricación', color: 'bg-orange-500' },
                    { key: 'entregado', label: 'Entregado', color: 'bg-indigo-500' },
                    { key: 'rechazado', label: 'Rechazado', color: 'bg-red-400' },
                  ].map(s => {
                    const data = overview.presupuestos.porEstado[s.key] || { count: 0, total: 0 };
                    return (
                      <div key={s.key} className="flex items-center gap-3">
                        <div className={`w-2 h-2 rounded-full flex-shrink-0 ${s.color}`} />
                        <span className="text-xs font-bold text-slate-600 w-28 flex-shrink-0">{s.label}</span>
                        <div className="flex-1">
                          <MiniBar value={data.count} max={overview.presupuestos.total} color={s.color} />
                        </div>
                        <span className="text-xs font-black text-slate-900 w-6 text-right">{data.count}</span>
                        <span className="text-xs text-slate-400 w-20 text-right">{fmt(data.total)}</span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Evolución mensual */}
              <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
                <div className="px-5 py-4 border-b border-slate-100 flex items-center gap-2">
                  <div className="w-1.5 h-5 bg-orange-500 rounded-full" />
                  <h3 className="font-black text-slate-900 text-sm uppercase">Evolución 6 Meses</h3>
                </div>
                <div className="p-4">
                  <div className="space-y-3">
                    {overview.evolucion.map((m, i) => {
                      const maxPvp = Math.max(...overview.evolucion.map(x => x.facturado), 1);
                      return (
                        <div key={i} className="flex items-center gap-3">
                          <span className="text-[10px] font-black text-slate-400 w-16 flex-shrink-0">{m.month}</span>
                          <div className="flex-1 space-y-1">
                            <div className="flex items-center gap-2">
                              <div className="flex-1 bg-slate-100 rounded-full h-1.5 overflow-hidden">
                                <div className="h-full bg-indigo-400 rounded-full" style={{ width: `${Math.min(100, (m.presupuestos / Math.max(...overview.evolucion.map(x=>x.presupuestos),1))*100)}%` }} />
                              </div>
                              <span className="text-[10px] text-slate-500 w-6 text-right">{m.presupuestos}</span>
                            </div>
                            <div className="flex items-center gap-2">
                              <div className="flex-1 bg-slate-100 rounded-full h-1.5 overflow-hidden">
                                <div className="h-full bg-orange-400 rounded-full" style={{ width: `${Math.min(100, (m.facturado / maxPvp)*100)}%` }} />
                              </div>
                              <span className="text-[10px] text-slate-500 w-16 text-right">{fmt(m.facturado)}</span>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                  <div className="flex gap-4 mt-3 pt-3 border-t border-slate-50">
                    <div className="flex items-center gap-1.5"><div className="w-2 h-2 bg-indigo-400 rounded-full"/><span className="text-[9px] text-slate-400 font-bold">Presupuestos</span></div>
                    <div className="flex items-center gap-1.5"><div className="w-2 h-2 bg-orange-400 rounded-full"/><span className="text-[9px] text-slate-400 font-bold">Facturado</span></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ── USUARIOS ────────────────────────────────────────────── */}
        {activeTab === 'usuarios' && usersActivity && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-2">
              {[
                { label: 'Activos hoy', value: overview?.usuarios.activosHoy || 0, color: 'text-green-600' },
                { label: 'Esta semana', value: overview?.usuarios.activosSemana || 0, color: 'text-blue-600' },
                { label: 'Este mes', value: overview?.usuarios.activosMes || 0, color: 'text-indigo-600' },
                { label: 'En seguimiento', value: usersActivity.total, color: 'text-slate-600' },
              ].map((s, i) => (
                <div key={i} className="bg-white rounded-2xl p-4 border border-slate-100 shadow-sm">
                  <p className={`text-2xl font-black ${s.color}`}>{s.value}</p>
                  <p className="text-[10px] font-black text-slate-400 uppercase mt-1">{s.label}</p>
                </div>
              ))}
            </div>

            <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
              <div className="px-5 py-4 border-b border-slate-100">
                <h3 className="font-black text-slate-900 text-sm uppercase">Actividad por Usuario — últimos {dayFilter} días</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-100">
                      {['Usuario', 'Rol', 'Acciones', 'Logins', 'Presupuestos', 'Pedidos', 'PDFs', 'IA', 'Última actividad'].map(h => (
                        <th key={h} className="px-4 py-3 text-[9px] font-black text-slate-400 uppercase text-left whitespace-nowrap">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-50">
                    {usersActivity.usuarios.map((u, i) => (
                      <tr key={i} className="hover:bg-slate-50 transition-colors">
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <div className="w-8 h-8 bg-indigo-100 rounded-xl flex items-center justify-center font-black text-indigo-700 text-xs flex-shrink-0">
                              {(u.nombre || u.username || '?')[0].toUpperCase()}
                            </div>
                            <div>
                              <p className="font-bold text-slate-900 text-xs">{u.nombre || u.username}</p>
                              <p className="text-[10px] text-slate-400">{u.email}</p>
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <span className={`text-[9px] font-black px-2 py-0.5 rounded-full uppercase ${u.rol === 'Admin' ? 'bg-red-100 text-red-700' : u.rol === 'Comercial' ? 'bg-purple-100 text-purple-700' : u.rol === 'Tienda' ? 'bg-blue-100 text-blue-700' : 'bg-slate-100 text-slate-600'}`}>
                            {u.rol}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-center"><span className="font-black text-slate-900 text-sm">{u.totalAcciones}</span></td>
                        <td className="px-4 py-3 text-center"><span className="text-xs text-slate-600">{u.logins}</span></td>
                        <td className="px-4 py-3 text-center"><span className="text-xs font-bold text-indigo-600">{u.presupuestosCreados}</span></td>
                        <td className="px-4 py-3 text-center"><span className="text-xs font-bold text-orange-600">{u.pedidosCreados}</span></td>
                        <td className="px-4 py-3 text-center"><span className="text-xs text-slate-500">{u.pdfsGenerados}</span></td>
                        <td className="px-4 py-3 text-center"><span className="text-xs text-purple-600">{u.usoIA}</span></td>
                        <td className="px-4 py-3 whitespace-nowrap"><span className="text-[10px] text-slate-400">{fmtDate(u.ultimaActividad)}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {usersActivity.usuarios.length === 0 && (
                  <div className="flex flex-col items-center py-10 text-slate-300">
                    <Users className="w-10 h-10 mb-2" />
                    <p className="font-black text-slate-400 text-sm">Sin datos de actividad</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ── RENDIMIENTO ─────────────────────────────────────────── */}
        {activeTab === 'rendimiento' && performance && (
          <div className="space-y-4">
            <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
              <div className="px-5 py-4 border-b border-slate-100">
                <h3 className="font-black text-slate-900 text-sm uppercase">Ranking Comercial — últimos {dayFilter} días</h3>
              </div>
              <div className="divide-y divide-slate-50">
                {performance.ranking.map((u, i) => {
                  const maxPvp = Math.max(...performance.ranking.map(x => x.totalPvp), 1);
                  return (
                    <div key={i} className="flex items-center gap-4 px-5 py-4 hover:bg-slate-50 transition-colors">
                      <div className={`w-8 h-8 rounded-2xl flex items-center justify-center font-black text-sm flex-shrink-0 ${i === 0 ? 'bg-yellow-100 text-yellow-700' : i === 1 ? 'bg-slate-100 text-slate-600' : i === 2 ? 'bg-orange-50 text-orange-600' : 'bg-slate-50 text-slate-400'}`}>
                        {i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : i + 1}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <p className="font-black text-slate-900 text-sm truncate">{u.nombre}</p>
                          <span className={`text-[9px] font-black px-1.5 py-0.5 rounded-full uppercase flex-shrink-0 ${u.rol === 'Comercial' ? 'bg-purple-100 text-purple-700' : 'bg-blue-100 text-blue-700'}`}>{u.rol}</span>
                        </div>
                        <MiniBar value={u.totalPvp} max={maxPvp} color="bg-indigo-500" />
                      </div>
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 flex-shrink-0 text-right">
                        <div className="hidden sm:block">
                          <p className="text-[10px] text-slate-400 font-black uppercase">Presupuestos</p>
                          <p className="text-sm font-black text-slate-900">{u.presupuestos}</p>
                        </div>
                        <div className="hidden sm:block">
                          <p className="text-[10px] text-slate-400 font-black uppercase">Conversión</p>
                          <p className={`text-sm font-black ${u.conversion >= 50 ? 'text-green-600' : u.conversion >= 25 ? 'text-amber-600' : 'text-red-500'}`}>{u.conversion}%</p>
                        </div>
                        <div>
                          <p className="text-[10px] text-slate-400 font-black uppercase">PVP Total</p>
                          <p className="text-sm font-black text-indigo-700">{fmt(u.totalPvp)}</p>
                        </div>
                        <div>
                          <p className="text-[10px] text-slate-400 font-black uppercase">Facturado</p>
                          <p className="text-sm font-black text-orange-600">{fmt(u.totalFacturado)}</p>
                        </div>
                      </div>
                    </div>
                  );
                })}
                {performance.ranking.length === 0 && (
                  <div className="flex flex-col items-center py-10 text-slate-300">
                    <Award className="w-10 h-10 mb-2" />
                    <p className="font-black text-slate-400 text-sm">Sin datos de rendimiento</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ── ALERTAS ─────────────────────────────────────────────── */}
        {activeTab === 'alertas' && alerts && (
          <div className="space-y-3">
            {alerts.alertas.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-40 bg-white rounded-2xl border border-slate-100">
                <CheckCircle className="w-10 h-10 text-green-400 mb-2" />
                <p className="font-black text-slate-600 text-sm">Todo en orden</p>
                <p className="text-xs text-slate-400 mt-1">No hay alertas pendientes</p>
              </div>
            ) : alerts.alertas.map((a, i) => (
              <div key={i} className={`bg-white rounded-2xl border shadow-sm p-5 flex items-start gap-4 ${a.tipo === 'error' ? 'border-red-200' : a.tipo === 'warning' ? 'border-amber-200' : 'border-blue-100'}`}>
                <span className="text-2xl flex-shrink-0">{a.icono}</span>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <p className="font-black text-slate-900 text-sm">{a.titulo}</p>
                    <AlertBadge tipo={a.tipo} />
                  </div>
                  <p className="text-xs text-slate-500">{a.descripcion}</p>
                </div>
                <div className="flex-shrink-0">
                  <span className="text-[10px] font-black text-indigo-600 uppercase">{a.accion} →</span>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* ── ACTIVIDAD ───────────────────────────────────────────── */}
        {activeTab === 'actividad' && timeline && (
          <div className="space-y-4">
            <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden">
              <div className="px-5 py-4 border-b border-slate-100">
                <h3 className="font-black text-slate-900 text-sm uppercase">Últimas Acciones</h3>
              </div>
              <div className="divide-y divide-slate-50">
                {timeline.actividades.map((a, i) => (
                  <div key={i} className="flex items-center gap-3 px-5 py-3 hover:bg-slate-50 transition-colors">
                    <span className="text-lg flex-shrink-0">{ACTIVITY_ICONS[a.activityType] || '📌'}</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-bold text-slate-900 truncate">
                        {a.username} <span className="font-normal text-slate-400">—</span> {ACTIVITY_LABELS[a.activityType] || a.activityType}
                      </p>
                      {a.details && Object.keys(a.details).length > 0 && (
                        <p className="text-[10px] text-slate-400 truncate">{JSON.stringify(a.details).slice(0, 80)}</p>
                      )}
                    </div>
                    <p className="text-[10px] text-slate-300 flex-shrink-0 ml-2">{fmtDate(a.timestamp)}</p>
                  </div>
                ))}
                {timeline.actividades.length === 0 && (
                  <div className="flex flex-col items-center py-10 text-slate-300">
                    <Activity className="w-10 h-10 mb-2" />
                    <p className="font-black text-slate-400 text-sm">Sin actividad reciente</p>
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

export default CommandCenter;
