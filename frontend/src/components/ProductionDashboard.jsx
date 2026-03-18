import React, { useState, useEffect, useMemo } from 'react';
import { 
  BarChart3, TrendingUp, Factory, Package, Clock, CheckCircle, 
  Truck, AlertTriangle, Calendar, Users, Building2, RefreshCw,
  ArrowUp, ArrowDown, Minus, PieChart, Activity
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

/**
 * Dashboard Gráfico de Producción
 * Muestra métricas, gráficas de progreso y estadísticas por fábrica
 */

// Configuración de estados
const STATUS_CONFIG = {
  draft: { label: 'Borrador', color: '#9ca3af', bgColor: '#f3f4f6' },
  confirmed: { label: 'Confirmada', color: '#3b82f6', bgColor: '#dbeafe' },
  in_production: { label: 'En Producción', color: '#f59e0b', bgColor: '#fef3c7' },
  ready: { label: 'Lista', color: '#10b981', bgColor: '#d1fae5' },
  delivered: { label: 'Entregada', color: '#059669', bgColor: '#a7f3d0' },
  cancelled: { label: 'Cancelada', color: '#ef4444', bgColor: '#fee2e2' }
};

// Componente de gráfica de barras simple con CSS
const SimpleBarChart = ({ data, title, height = 200 }) => {
  const maxValue = Math.max(...data.map(d => d.value), 1);
  
  return (
    <div className="bg-white rounded-2xl p-4 border border-slate-200">
      <h4 className="font-bold text-slate-700 mb-4">{title}</h4>
      <div className="flex items-end gap-2 justify-around" style={{ height }}>
        {data.map((item, idx) => {
          const heightPercent = (item.value / maxValue) * 100;
          return (
            <div key={idx} className="flex flex-col items-center gap-2 flex-1">
              <span className="text-sm font-bold text-slate-700">{item.value}</span>
              <div 
                className="w-full rounded-t-lg transition-all duration-500"
                style={{ 
                  height: `${Math.max(heightPercent, 5)}%`,
                  backgroundColor: item.color || '#3b82f6',
                  minHeight: '8px'
                }}
              />
              <span className="text-xs text-slate-500 text-center font-medium">{item.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

// Componente de gráfica circular (donut)
const DonutChart = ({ data, title, size = 150 }) => {
  const total = data.reduce((sum, d) => sum + d.value, 0);
  let cumulativePercent = 0;
  
  const getCoordinatesForPercent = (percent) => {
    const x = Math.cos(2 * Math.PI * percent);
    const y = Math.sin(2 * Math.PI * percent);
    return [x, y];
  };

  return (
    <div className="bg-white rounded-2xl p-4 border border-slate-200">
      <h4 className="font-bold text-slate-700 mb-4">{title}</h4>
      <div className="flex items-center justify-center gap-6">
        <svg width={size} height={size} viewBox="-1 -1 2 2" style={{ transform: 'rotate(-90deg)' }}>
          {total > 0 && data.map((item, idx) => {
            const percent = item.value / total;
            const [startX, startY] = getCoordinatesForPercent(cumulativePercent);
            cumulativePercent += percent;
            const [endX, endY] = getCoordinatesForPercent(cumulativePercent);
            const largeArcFlag = percent > 0.5 ? 1 : 0;
            
            const pathData = [
              `M ${startX} ${startY}`,
              `A 1 1 0 ${largeArcFlag} 1 ${endX} ${endY}`,
              `L 0 0`
            ].join(' ');
            
            return (
              <path key={idx} d={pathData} fill={item.color} />
            );
          })}
          <circle cx="0" cy="0" r="0.6" fill="white" />
        </svg>
        <div className="space-y-2">
          {data.map((item, idx) => (
            <div key={idx} className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
              <span className="text-xs text-slate-600">{item.label}: <strong>{item.value}</strong></span>
            </div>
          ))}
        </div>
      </div>
      <div className="text-center mt-2">
        <span className="text-2xl font-black text-slate-800">{total}</span>
        <span className="text-sm text-slate-500 ml-1">total</span>
      </div>
    </div>
  );
};

// Componente de tarjeta de métrica
const MetricCard = ({ icon: Icon, label, value, trend, trendValue, color = 'blue' }) => {
  const colorClasses = {
    blue: 'from-blue-500 to-blue-700',
    emerald: 'from-emerald-500 to-emerald-700',
    amber: 'from-amber-500 to-amber-700',
    purple: 'from-purple-500 to-purple-700',
    red: 'from-red-500 to-red-700',
    slate: 'from-slate-500 to-slate-700'
  };

  return (
    <div className={`bg-gradient-to-br ${colorClasses[color]} rounded-2xl p-5 text-white shadow-lg`}>
      <div className="flex items-start justify-between">
        <div className="p-2 bg-white/20 rounded-xl">
          <Icon size={24} />
        </div>
        {trend && (
          <div className={`flex items-center gap-1 px-2 py-1 rounded-full text-xs font-bold ${
            trend === 'up' ? 'bg-green-400/30' : trend === 'down' ? 'bg-red-400/30' : 'bg-white/20'
          }`}>
            {trend === 'up' && <ArrowUp size={12} />}
            {trend === 'down' && <ArrowDown size={12} />}
            {trend === 'neutral' && <Minus size={12} />}
            {trendValue}
          </div>
        )}
      </div>
      <div className="mt-4">
        <p className="text-white/80 text-xs font-bold uppercase tracking-widest">{label}</p>
        <p className="text-3xl font-black mt-1">{value}</p>
      </div>
    </div>
  );
};

// Componente principal del Dashboard
const ProductionDashboard = ({ currentUser, orders = [], factories = [] }) => {
  const [timeRange, setTimeRange] = useState('week'); // week, month, year
  const [selectedFactory, setSelectedFactory] = useState('all');
  const [refreshing, setRefreshing] = useState(false);

  // Filtrar órdenes por fábrica si el usuario tiene una asignada
  const filteredOrders = useMemo(() => {
    let result = orders;
    
    // Si el usuario tiene una fábrica asignada, filtrar por ella
    if (currentUser?.factoryId) {
      result = result.filter(o => o.factoryId === currentUser.factoryId || !o.factoryId);
    }
    
    // Si hay filtro de fábrica seleccionado
    if (selectedFactory !== 'all') {
      result = result.filter(o => o.factoryId === selectedFactory);
    }
    
    return result;
  }, [orders, currentUser, selectedFactory]);

  // Calcular métricas
  const metrics = useMemo(() => {
    const now = new Date();
    const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
    
    const activeOrders = filteredOrders.filter(o => 
      !['delivered', 'cancelled'].includes(o.status)
    );
    
    const inProduction = filteredOrders.filter(o => o.status === 'in_production');
    const ready = filteredOrders.filter(o => o.status === 'ready');
    const delivered = filteredOrders.filter(o => o.status === 'delivered');
    const delayed = filteredOrders.filter(o => {
      if (!o.estimatedDelivery) return false;
      return new Date(o.estimatedDelivery) < now && !['delivered', 'cancelled'].includes(o.status);
    });
    
    // Contar piezas
    const totalPieces = filteredOrders.reduce((sum, o) => 
      sum + (o.items?.reduce((s, i) => s + (i.quantity || 1), 0) || 0), 0
    );
    
    // Órdenes esta semana
    const ordersThisWeek = filteredOrders.filter(o => 
      new Date(o.createdAt) >= weekAgo
    ).length;
    
    return {
      totalOrders: filteredOrders.length,
      activeOrders: activeOrders.length,
      inProduction: inProduction.length,
      ready: ready.length,
      delivered: delivered.length,
      delayed: delayed.length,
      totalPieces,
      ordersThisWeek
    };
  }, [filteredOrders]);

  // Datos para gráfica de estados
  const statusChartData = useMemo(() => {
    const counts = {};
    filteredOrders.forEach(o => {
      counts[o.status] = (counts[o.status] || 0) + 1;
    });
    
    return Object.entries(STATUS_CONFIG).map(([key, config]) => ({
      label: config.label,
      value: counts[key] || 0,
      color: config.color
    }));
  }, [filteredOrders]);

  // Datos para gráfica por fábrica
  const factoryChartData = useMemo(() => {
    if (factories.length === 0) return [];
    
    const counts = {};
    factories.forEach(f => { counts[f.id] = 0; });
    counts['unassigned'] = 0;
    
    filteredOrders.forEach(o => {
      if (o.factoryId && counts[o.factoryId] !== undefined) {
        counts[o.factoryId]++;
      } else {
        counts['unassigned']++;
      }
    });
    
    return [
      ...factories.map(f => ({
        label: f.code,
        value: counts[f.id] || 0,
        color: f.code === 'SAL' ? '#3b82f6' : f.code === 'ZAM' ? '#10b981' : '#8b5cf6'
      })),
      { label: 'Sin asignar', value: counts['unassigned'], color: '#9ca3af' }
    ];
  }, [filteredOrders, factories]);

  // Datos para gráfica de tendencia (últimos 7 días)
  const trendChartData = useMemo(() => {
    const days = [];
    for (let i = 6; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      date.setHours(0, 0, 0, 0);
      
      const nextDate = new Date(date);
      nextDate.setDate(nextDate.getDate() + 1);
      
      const count = filteredOrders.filter(o => {
        const orderDate = new Date(o.createdAt);
        return orderDate >= date && orderDate < nextDate;
      }).length;
      
      days.push({
        label: date.toLocaleDateString('es-ES', { weekday: 'short' }),
        value: count,
        color: '#3b82f6'
      });
    }
    return days;
  }, [filteredOrders]);

  // Progreso de fabricación
  const fabricationProgress = useMemo(() => {
    let totalItems = 0;
    let completedItems = 0;
    let inProgressItems = 0;
    
    filteredOrders.forEach(o => {
      if (o.items) {
        o.items.forEach(item => {
          totalItems += item.quantity || 1;
          if (item.fabricationStatus === 'completed') {
            completedItems += item.quantity || 1;
          } else if (item.fabricationStatus === 'in_progress') {
            inProgressItems += item.quantity || 1;
          }
        });
      }
    });
    
    return { totalItems, completedItems, inProgressItems, pendingItems: totalItems - completedItems - inProgressItems };
  }, [filteredOrders]);

  const handleRefresh = async () => {
    setRefreshing(true);
    // El refresh real se manejará en el componente padre
    await new Promise(r => setTimeout(r, 1000));
    setRefreshing(false);
  };

  return (
    <div className="space-y-6">
      {/* Header con filtros */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-2xl font-black text-slate-800 flex items-center gap-3">
            <BarChart3 className="text-emerald-600" />
            Dashboard de Producción
          </h2>
          <p className="text-slate-500 text-sm mt-1">
            Métricas y estadísticas en tiempo real
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          {/* Filtro de fábrica */}
          {factories.length > 0 && !currentUser?.factoryId && (
            <select
              value={selectedFactory}
              onChange={(e) => setSelectedFactory(e.target.value)}
              className="px-4 py-2 border-2 border-slate-200 rounded-xl text-sm font-bold focus:border-emerald-500 outline-none"
            >
              <option value="all">Todas las Fábricas</option>
              {factories.map(f => (
                <option key={f.id} value={f.id}>{f.name}</option>
              ))}
            </select>
          )}
          
          {/* Filtro de tiempo */}
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="px-4 py-2 border-2 border-slate-200 rounded-xl text-sm font-bold focus:border-emerald-500 outline-none"
          >
            <option value="week">Esta Semana</option>
            <option value="month">Este Mes</option>
            <option value="year">Este Año</option>
          </select>
          
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="p-2 bg-emerald-100 hover:bg-emerald-200 rounded-xl transition-colors"
          >
            <RefreshCw size={20} className={`text-emerald-700 ${refreshing ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Métricas principales */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        <MetricCard 
          icon={Package} 
          label="Órdenes Activas" 
          value={metrics.activeOrders}
          trend="up"
          trendValue={`+${metrics.ordersThisWeek} esta semana`}
          color="blue"
        />
        <MetricCard 
          icon={Factory} 
          label="En Producción" 
          value={metrics.inProduction}
          color="amber"
        />
        <MetricCard 
          icon={CheckCircle} 
          label="Listas" 
          value={metrics.ready}
          color="emerald"
        />
        <MetricCard 
          icon={Truck} 
          label="Entregadas" 
          value={metrics.delivered}
          color="purple"
        />
        <MetricCard 
          icon={AlertTriangle} 
          label="Retrasadas" 
          value={metrics.delayed}
          color={metrics.delayed > 0 ? 'red' : 'slate'}
        />
        <MetricCard 
          icon={Activity} 
          label="Piezas Total" 
          value={metrics.totalPieces}
          color="slate"
        />
      </div>

      {/* Barra de progreso general */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200">
        <h4 className="font-bold text-slate-700 mb-4 flex items-center gap-2">
          <TrendingUp size={18} />
          Progreso de Fabricación Global
        </h4>
        <div className="h-8 bg-slate-100 rounded-full overflow-hidden flex">
          <div 
            className="bg-green-500 transition-all duration-500 flex items-center justify-center"
            style={{ width: `${(fabricationProgress.completedItems / Math.max(fabricationProgress.totalItems, 1)) * 100}%` }}
          >
            {fabricationProgress.completedItems > 0 && (
              <span className="text-white text-xs font-bold">{fabricationProgress.completedItems}</span>
            )}
          </div>
          <div 
            className="bg-blue-500 transition-all duration-500 flex items-center justify-center"
            style={{ width: `${(fabricationProgress.inProgressItems / Math.max(fabricationProgress.totalItems, 1)) * 100}%` }}
          >
            {fabricationProgress.inProgressItems > 0 && (
              <span className="text-white text-xs font-bold">{fabricationProgress.inProgressItems}</span>
            )}
          </div>
          <div 
            className="bg-red-400 transition-all duration-500 flex items-center justify-center"
            style={{ width: `${(fabricationProgress.pendingItems / Math.max(fabricationProgress.totalItems, 1)) * 100}%` }}
          >
            {fabricationProgress.pendingItems > 0 && (
              <span className="text-white text-xs font-bold">{fabricationProgress.pendingItems}</span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-6 mt-3 text-sm">
          <span className="flex items-center gap-2">
            <span className="w-3 h-3 bg-green-500 rounded-full"></span>
            Fabricado: <strong>{fabricationProgress.completedItems}</strong>
          </span>
          <span className="flex items-center gap-2">
            <span className="w-3 h-3 bg-blue-500 rounded-full"></span>
            En Proceso: <strong>{fabricationProgress.inProgressItems}</strong>
          </span>
          <span className="flex items-center gap-2">
            <span className="w-3 h-3 bg-red-400 rounded-full"></span>
            Pendiente: <strong>{fabricationProgress.pendingItems}</strong>
          </span>
        </div>
      </div>

      {/* Gráficas */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Gráfica por estado */}
        <DonutChart 
          data={statusChartData.filter(d => d.value > 0)} 
          title="Órdenes por Estado" 
        />
        
        {/* Gráfica por fábrica */}
        {factories.length > 0 && !currentUser?.factoryId && (
          <SimpleBarChart 
            data={factoryChartData} 
            title="Órdenes por Fábrica" 
          />
        )}
        
        {/* Tendencia semanal */}
        <SimpleBarChart 
          data={trendChartData} 
          title="Órdenes (Últimos 7 días)" 
        />
      </div>

      {/* Info de fábrica del usuario */}
      {currentUser?.factoryId && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-2xl p-4">
          <div className="flex items-center gap-3">
            <Building2 className="text-emerald-600" size={24} />
            <div>
              <p className="font-bold text-emerald-800">
                Mostrando datos de: {factories.find(f => f.id === currentUser.factoryId)?.name || 'Tu Fábrica'}
              </p>
              <p className="text-sm text-emerald-600">
                Solo ves las órdenes asignadas a tu fábrica
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProductionDashboard;
