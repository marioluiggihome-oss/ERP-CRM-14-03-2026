/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * DashboardTab - Dashboard de Fábrica
 * Métricas de producción y ventas
 */
import React, { useState, useEffect } from 'react';
import { Factory, RefreshCw, TrendingUp, Users, Package, FileText, FolderOpen, BarChart3 } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart as RechartsPie, Pie, Cell, Legend } from 'recharts';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const DashboardTab = () => {
  const [dashboardPeriod, setDashboardPeriod] = useState('month');
  const [dashboardMetrics, setDashboardMetrics] = useState(null);
  const [dashboardLoading, setDashboardLoading] = useState(false);

  useEffect(() => {
    loadMetrics();
  }, [dashboardPeriod]);

  const loadMetrics = async () => {
    setDashboardLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/dashboard/metrics?period=${dashboardPeriod}`);
      const data = await response.json();
      setDashboardMetrics(data);
    } catch (error) {
      console.error('Error loading dashboard metrics:', error);
    } finally {
      setDashboardLoading(false);
    }
  };

  return (
    <div className="space-y-6" data-testid="dashboard-content">
      {/* Header con selector de período */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-xl flex items-center justify-center">
            <Factory size={24} className="text-white" />
          </div>
          <div>
            <h2 className="text-xl font-black text-slate-800 uppercase">Dashboard Fábrica</h2>
            <p className="text-sm text-slate-500">Métricas de Producción y Ventas</p>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          <select
            value={dashboardPeriod}
            onChange={(e) => setDashboardPeriod(e.target.value)}
            className="px-4 py-2 bg-white border border-slate-200 rounded-xl text-sm font-bold text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            data-testid="dashboard-period-selector"
          >
            <option value="week">Última Semana</option>
            <option value="month">Último Mes</option>
            <option value="quarter">Último Trimestre</option>
            <option value="year">Último Año</option>
            <option value="all">Todo el Histórico</option>
          </select>
          
          <button
            onClick={loadMetrics}
            className="px-4 py-2 bg-blue-600 text-white rounded-xl text-sm font-bold flex items-center gap-2 hover:bg-blue-700 transition-colors"
          >
            <RefreshCw size={16} className={dashboardLoading ? 'animate-spin' : ''} />
            Actualizar
          </button>
        </div>
      </div>

      {dashboardLoading ? (
        <div className="flex items-center justify-center h-64">
          <RefreshCw size={32} className="animate-spin text-blue-500" />
          <span className="ml-3 text-slate-500 font-bold">Cargando métricas...</span>
        </div>
      ) : dashboardMetrics ? (
        <>
          {/* KPIs Principales */}
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
            <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl p-4 text-white">
              <div className="text-xs uppercase font-bold opacity-80">Órdenes Fab.</div>
              <div className="text-3xl font-black">{dashboardMetrics.kpis?.totalFabOrders || 0}</div>
            </div>
            <div className="bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-2xl p-4 text-white">
              <div className="text-xs uppercase font-bold opacity-80">Pedidos Confirm.</div>
              <div className="text-3xl font-black">{dashboardMetrics.kpis?.totalConfirmedOrders || 0}</div>
            </div>
            <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-2xl p-4 text-white">
              <div className="text-xs uppercase font-bold opacity-80">Presupuestos</div>
              <div className="text-3xl font-black">{dashboardMetrics.kpis?.totalBudgets || 0}</div>
            </div>
            <div className="bg-gradient-to-br from-orange-500 to-orange-600 rounded-2xl p-4 text-white">
              <div className="text-xs uppercase font-bold opacity-80">Ventas €</div>
              <div className="text-2xl font-black">{(dashboardMetrics.kpis?.totalSalesValue || 0).toLocaleString('es-ES', {maximumFractionDigits: 0})}€</div>
            </div>
            <div className="bg-gradient-to-br from-cyan-500 to-cyan-600 rounded-2xl p-4 text-white">
              <div className="text-xs uppercase font-bold opacity-80">Pres. Valor €</div>
              <div className="text-2xl font-black">{(dashboardMetrics.kpis?.totalBudgetValue || 0).toLocaleString('es-ES', {maximumFractionDigits: 0})}€</div>
            </div>
            <div className="bg-gradient-to-br from-pink-500 to-pink-600 rounded-2xl p-4 text-white">
              <div className="text-xs uppercase font-bold opacity-80">Piezas Prod.</div>
              <div className="text-3xl font-black">{dashboardMetrics.kpis?.totalPiecesInProduction || 0}</div>
            </div>
            <div className="bg-gradient-to-br from-amber-500 to-amber-600 rounded-2xl p-4 text-white">
              <div className="text-xs uppercase font-bold opacity-80">Conversión</div>
              <div className="text-3xl font-black">{dashboardMetrics.kpis?.conversionRate || 0}%</div>
            </div>
          </div>

          {/* Gráficos Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Tendencia Mensual */}
            <div className="bg-white rounded-2xl border border-slate-200 p-6">
              <h3 className="text-sm font-black text-slate-800 uppercase mb-4 flex items-center gap-2">
                <TrendingUp size={18} className="text-blue-500" />
                Tendencia Mensual
              </h3>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={dashboardMetrics.monthlyTrend || []}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e3e8ee" />
                  <XAxis dataKey="name" tick={{fontSize: 12}} />
                  <YAxis tick={{fontSize: 12}} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="pedidos" name="Pedidos" fill="#5f87c9" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="presupuestos" name="Presupuestos" fill="#8572c7" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Estado Producción */}
            <div className="bg-white rounded-2xl border border-slate-200 p-6">
              <h3 className="text-sm font-black text-slate-800 uppercase mb-4 flex items-center gap-2">
                <Factory size={18} className="text-emerald-500" />
                Estado de Producción
              </h3>
              <ResponsiveContainer width="100%" height={250}>
                <RechartsPie>
                  <Pie
                    data={[
                      { name: 'Borrador', value: dashboardMetrics.production?.byStatus?.draft || 0, color: '#97a3b2' },
                      { name: 'Confirmado', value: dashboardMetrics.production?.byStatus?.confirmed || 0, color: '#5f87c9' },
                      { name: 'En Producción', value: dashboardMetrics.production?.byStatus?.in_production || 0, color: '#d5ab7c' },
                      { name: 'Listo', value: dashboardMetrics.production?.byStatus?.ready || 0, color: '#6bae8e' },
                      { name: 'Entregado', value: dashboardMetrics.production?.byStatus?.delivered || 0, color: '#8572c7' },
                    ].filter(d => d.value > 0)}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={2}
                    dataKey="value"
                    label={({name, value}) => `${name}: ${value}`}
                  >
                    {[
                      { name: 'Borrador', value: dashboardMetrics.production?.byStatus?.draft || 0, color: '#97a3b2' },
                      { name: 'Confirmado', value: dashboardMetrics.production?.byStatus?.confirmed || 0, color: '#5f87c9' },
                      { name: 'En Producción', value: dashboardMetrics.production?.byStatus?.in_production || 0, color: '#d5ab7c' },
                      { name: 'Listo', value: dashboardMetrics.production?.byStatus?.ready || 0, color: '#6bae8e' },
                      { name: 'Entregado', value: dashboardMetrics.production?.byStatus?.delivered || 0, color: '#8572c7' },
                    ].filter(d => d.value > 0).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </RechartsPie>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Segunda Row: Prioridad y Clientes/Productos */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Prioridad Órdenes */}
            <div className="bg-white rounded-2xl border border-slate-200 p-6">
              <h3 className="text-sm font-black text-slate-800 uppercase mb-4">Prioridad Órdenes</h3>
              <div className="space-y-3">
                {[
                  { key: 'urgent', label: 'Urgente', color: 'bg-red-500' },
                  { key: 'high', label: 'Alta', color: 'bg-orange-500' },
                  { key: 'normal', label: 'Normal', color: 'bg-blue-500' },
                  { key: 'low', label: 'Baja', color: 'bg-slate-400' },
                ].map(item => (
                  <div key={item.key} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className={`w-3 h-3 rounded-full ${item.color}`}></div>
                      <span className="text-sm text-slate-600">{item.label}</span>
                    </div>
                    <span className="text-lg font-black text-slate-800">
                      {dashboardMetrics.production?.byPriority?.[item.key] || 0}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Clientes */}
            <div className="bg-white rounded-2xl border border-slate-200 p-6">
              <h3 className="text-sm font-black text-slate-800 uppercase mb-4 flex items-center gap-2">
                <Users size={18} className="text-purple-500" />
                Clientes
              </h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-600">Total</span>
                  <span className="text-2xl font-black text-slate-800">{dashboardMetrics.clients?.total || 0}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-emerald-600">Activos</span>
                  <span className="text-xl font-black text-emerald-600">{dashboardMetrics.clients?.active || 0}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-amber-600">Potenciales</span>
                  <span className="text-xl font-black text-amber-600">{dashboardMetrics.clients?.potential || 0}</span>
                </div>
              </div>
            </div>

            {/* Productos */}
            <div className="bg-white rounded-2xl border border-slate-200 p-6">
              <h3 className="text-sm font-black text-slate-800 uppercase mb-4 flex items-center gap-2">
                <Package size={18} className="text-cyan-500" />
                Catálogo Productos
              </h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-600">Total</span>
                  <span className="text-2xl font-black text-slate-800">{dashboardMetrics.products?.total || 0}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-blue-600">Librería ZC</span>
                  <span className="text-xl font-black text-blue-600">{dashboardMetrics.products?.zc || 0}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-purple-600">Librería MV</span>
                  <span className="text-xl font-black text-purple-600">{dashboardMetrics.products?.mv || 0}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Tablas: Pedidos Recientes y Fabricación Pendiente */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Pedidos Recientes */}
            <div className="bg-white rounded-2xl border border-slate-200 p-6">
              <h3 className="text-sm font-black text-slate-800 uppercase mb-4 flex items-center gap-2">
                <FileText size={18} className="text-emerald-500" />
                Últimos Pedidos Confirmados
              </h3>
              {dashboardMetrics.sales?.recentOrders?.length > 0 ? (
                <div className="space-y-2">
                  {dashboardMetrics.sales.recentOrders.map((order, idx) => (
                    <div key={idx} className="flex items-center justify-between p-3 bg-slate-50 rounded-xl">
                      <div>
                        <div className="font-bold text-slate-800">{order.orderNumber}</div>
                        <div className="text-xs text-slate-500">{order.clientName}</div>
                      </div>
                      <div className="text-right">
                        <div className="font-black text-emerald-600">{(order.total || 0).toLocaleString('es-ES')}€</div>
                        <div className="text-xs text-slate-400">
                          {order.confirmedAt ? new Date(order.confirmedAt).toLocaleDateString('es-ES') : '-'}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center text-slate-400 py-8">Sin pedidos recientes</div>
              )}
            </div>

            {/* Fabricación Pendiente */}
            <div className="bg-white rounded-2xl border border-slate-200 p-6">
              <h3 className="text-sm font-black text-slate-800 uppercase mb-4 flex items-center gap-2">
                <Factory size={18} className="text-orange-500" />
                Fabricación Pendiente
              </h3>
              {dashboardMetrics.production?.pendingOrders?.length > 0 ? (
                <div className="space-y-2">
                  {dashboardMetrics.production.pendingOrders.map((fab, idx) => (
                    <div key={idx} className="flex items-center justify-between p-3 bg-slate-50 rounded-xl">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-slate-800">{fab.orderNumber}</span>
                          {fab.manufacturingNumber && (
                            <span className="px-2 py-0.5 bg-orange-100 text-orange-700 text-xs font-bold rounded">
                              Nº FAB: {fab.manufacturingNumber}
                            </span>
                          )}
                        </div>
                        <div className="text-xs text-slate-500">{fab.customerName}</div>
                      </div>
                      <div className="text-right">
                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-0.5 text-xs font-bold rounded ${
                            fab.priority === 'urgent' ? 'bg-red-100 text-red-700' :
                            fab.priority === 'high' ? 'bg-orange-100 text-orange-700' :
                            'bg-blue-100 text-blue-700'
                          }`}>
                            {fab.priority === 'urgent' ? 'URGENTE' : fab.priority === 'high' ? 'ALTA' : 'NORMAL'}
                          </span>
                          <span className="font-black text-slate-700">{fab.totalPieces} pzs</span>
                        </div>
                        <div className="text-xs text-slate-400">{fab.factoryName}</div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center text-slate-400 py-8">Sin órdenes pendientes</div>
              )}
            </div>
          </div>

          {/* Presupuestos por Estado */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6">
            <h3 className="text-sm font-black text-slate-800 uppercase mb-4 flex items-center gap-2">
              <FolderOpen size={18} className="text-purple-500" />
              Presupuestos por Estado
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
              {[
                { key: 'draft', label: 'Borrador', color: 'bg-slate-100 text-slate-600', icon: '📝' },
                { key: 'sent', label: 'Enviado', color: 'bg-blue-100 text-blue-600', icon: '📤' },
                { key: 'accepted', label: 'Aceptado', color: 'bg-emerald-100 text-emerald-600', icon: '✅' },
                { key: 'rejected', label: 'Rechazado', color: 'bg-red-100 text-red-600', icon: '❌' },
                { key: 'completed', label: 'Completado', color: 'bg-purple-100 text-purple-600', icon: '🏆' },
              ].map(item => (
                <div key={item.key} className={`rounded-xl p-4 ${item.color} text-center`}>
                  <div className="text-2xl mb-1">{item.icon}</div>
                  <div className="text-2xl font-black">{dashboardMetrics.budgets?.byStatus?.[item.key] || 0}</div>
                  <div className="text-xs font-bold uppercase">{item.label}</div>
                </div>
              ))}
            </div>
          </div>
        </>
      ) : (
        <div className="text-center text-slate-400 py-16">
          <BarChart3 size={48} className="mx-auto mb-4 opacity-50" />
          <p>Selecciona un período para ver las métricas</p>
        </div>
      )}
    </div>
  );
};

export default DashboardTab;
