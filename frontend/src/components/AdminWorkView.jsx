/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
import React, { useState, useEffect } from 'react';
import { authHeaders } from '../services/api';
import { X, Briefcase, FolderOpen, FileText, Users, Search, RefreshCw, Building2, User, Calendar, Euro, ChevronDown, ChevronUp, TrendingUp, Target, Award, Store, UserCheck, BarChart3, Maximize2, Minimize2, PieChart, UtensilsCrossed, DoorOpen } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, PieChart as RechartsPie, Pie, Cell, Legend, FunnelChart, Funnel, LabelList } from 'recharts';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const AdminWorkView = ({ isOpen, onClose, currentUser }) => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [trends, setTrends] = useState(null);
  const [activeTab, setActiveTab] = useState('metrics'); // 'metrics' or 'work'
  const [searchTerm, setSearchTerm] = useState('');
  const [isFullScreen, setIsFullScreen] = useState(false); // Pantalla completa
  const [expandedSections, setExpandedSections] = useState({
    projects: true,
    opportunities: true,
    digitalizaciones: false
  });
  const [filterUser, setFilterUser] = useState('');

  useEffect(() => {
    if (isOpen) {
      loadData();
      loadMetrics();
      loadTrends();
    }
  }, [isOpen]);

  const loadData = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/admin/all-work`, { headers: authHeaders() });
      const result = await response.json();
      setData(result);
    } catch (err) {
      console.error('Error loading admin data:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadMetrics = async () => {
    try {
      const response = await fetch(`${API_URL}/api/admin/metrics`, { headers: authHeaders() });
      const result = await response.json();
      setMetrics(result);
    } catch (err) {
      console.error('Error loading metrics:', err);
    }
  };

  const loadTrends = async () => {
    try {
      const response = await fetch(`${API_URL}/api/admin/metrics/trends`, { headers: authHeaders() });
      const result = await response.json();
      setTrends(result);
    } catch (err) {
      console.error('Error loading trends:', err);
    }
  };

  if (!isOpen) return null;

  const toggleSection = (section) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }));
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('es-ES', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value || 0);
  };

  const filteredProjects = data?.projects?.filter(p => {
    const matchesSearch = !searchTerm || 
      p.customerName?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.projectName?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.userName?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesUser = !filterUser || p.userId === filterUser;
    return matchesSearch && matchesUser;
  }) || [];

  const filteredOpportunities = data?.opportunities?.filter(o => {
    const matchesSearch = !searchTerm || 
      o.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      o.contactName?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      o.userName?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesUser = !filterUser || o.assignedTo === filterUser;
    return matchesSearch && matchesUser;
  }) || [];

  const filteredDigitalizaciones = data?.digitalizaciones?.filter(d => {
    const matchesSearch = !searchTerm || 
      d.projectName?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      d.customerName?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      d.userName?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesUser = !filterUser || d.createdBy === filterUser;
    return matchesSearch && matchesUser;
  }) || [];

  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
      <div className={`bg-white rounded-2xl shadow-2xl overflow-hidden flex flex-col transition-all duration-300 ${
        isFullScreen 
          ? 'w-full h-full max-w-none max-h-none rounded-none' 
          : 'w-full max-w-6xl max-h-[90vh]'
      }`}>
        {/* Header */}
        <div className="bg-indigo-950 text-white px-6 py-4 flex justify-between items-center shrink-0">
          <div className="flex items-center gap-3">
            <Building2 size={24} />
            <div>
              <h2 className="font-black text-lg uppercase tracking-wider">Panel Director Comercial</h2>
              <p className="text-indigo-300 text-xs">Métricas y trabajos del sistema</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {/* Tabs */}
            <button 
              onClick={() => setActiveTab('metrics')}
              className={`px-4 py-2 rounded-lg text-sm font-bold transition-all ${activeTab === 'metrics' ? 'bg-orange-500 text-white' : 'bg-white/10 hover:bg-white/20'}`}
            >
              <BarChart3 size={16} className="inline mr-2" />
              Métricas
            </button>
            <button 
              onClick={() => setActiveTab('work')}
              className={`px-4 py-2 rounded-lg text-sm font-bold transition-all ${activeTab === 'work' ? 'bg-orange-500 text-white' : 'bg-white/10 hover:bg-white/20'}`}
            >
              <FolderOpen size={16} className="inline mr-2" />
              Trabajos
            </button>
            {/* Botón Pantalla Completa */}
            <button 
              onClick={() => setIsFullScreen(!isFullScreen)} 
              className="p-2 hover:bg-white/10 rounded-lg transition-colors ml-2"
              title={isFullScreen ? 'Salir de pantalla completa' : 'Ver en pantalla completa'}
            >
              {isFullScreen ? <Minimize2 size={18} /> : <Maximize2 size={18} />}
            </button>
            <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-lg transition-colors ml-2">
              <X size={20} />
            </button>
          </div>
        </div>

        {/* METRICS TAB */}
        {activeTab === 'metrics' && metrics && (
          <div className="flex-1 overflow-auto p-6">
            {/* Global Summary Cards */}
            <div className={`grid gap-4 mb-6 ${isFullScreen ? 'grid-cols-5' : 'grid-cols-5'}`}>
              <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-xl p-4 text-white">
                <div className="flex items-center gap-2 mb-2">
                  <Euro size={20} />
                  <span className="text-xs font-bold uppercase opacity-80">Ventas Cerradas</span>
                </div>
                <p className={`font-black ${isFullScreen ? 'text-4xl' : 'text-3xl'}`}>{formatCurrency(metrics.global.totalValue)}</p>
                <p className="text-xs opacity-80 mt-1">{metrics.global.wonOpportunities} oportunidades ganadas</p>
              </div>
              <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-4 text-white">
                <div className="flex items-center gap-2 mb-2">
                  <Target size={20} />
                  <span className="text-xs font-bold uppercase opacity-80">Pipeline</span>
                </div>
                <p className="text-3xl font-black">{formatCurrency(metrics.global.pipelineValue)}</p>
                <p className="text-xs opacity-80 mt-1">{metrics.global.activeOpportunities} oportunidades activas</p>
              </div>
              <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl p-4 text-white">
                <div className="flex items-center gap-2 mb-2">
                  <TrendingUp size={20} />
                  <span className="text-xs font-bold uppercase opacity-80">Conversión</span>
                </div>
                <p className="text-3xl font-black">{metrics.global.conversionRate}%</p>
                <p className="text-xs opacity-80 mt-1">de {metrics.global.totalOpportunities} totales</p>
              </div>
              <div className="bg-gradient-to-br from-indigo-500 to-indigo-600 rounded-xl p-4 text-white">
                <div className="flex items-center gap-2 mb-2">
                  <Users size={20} />
                  <span className="text-xs font-bold uppercase opacity-80">Contactos</span>
                </div>
                <p className="text-3xl font-black">{metrics.global.totalContacts}</p>
                <p className="text-xs opacity-80 mt-1">{metrics.global.totalProjects} proyectos</p>
              </div>
              <div className="bg-gradient-to-br from-slate-600 to-slate-700 rounded-xl p-4 text-white">
                <div className="flex items-center gap-2 mb-2">
                  <Store size={20} />
                  <span className="text-xs font-bold uppercase opacity-80">Red Distribución</span>
                </div>
                <p className="text-3xl font-black">{metrics.global.totalTiendas}</p>
                <p className="text-xs opacity-80 mt-1">
                  {metrics.global.totalComerciales} comerciales, {metrics.global.totalResponsables} responsables
                </p>
              </div>
            </div>

            {/* Top Performers */}
            <div className="mb-6">
              <h3 className="text-lg font-black text-slate-900 mb-4 flex items-center gap-2">
                <Award className="text-orange-500" size={20} />
                Top Performers
              </h3>
              <div className="grid grid-cols-3 gap-4">
                {metrics.topPerformers.slice(0, 6).map((user, index) => (
                  <div key={user.userId} className={`bg-white rounded-xl p-4 border-2 ${index === 0 ? 'border-yellow-400' : index === 1 ? 'border-slate-300' : index === 2 ? 'border-orange-400' : 'border-slate-100'}`}>
                    <div className="flex items-center gap-3 mb-3">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center font-black text-white ${index === 0 ? 'bg-yellow-500' : index === 1 ? 'bg-slate-400' : index === 2 ? 'bg-orange-500' : 'bg-indigo-500'}`}>
                        {index + 1}
                      </div>
                      <div>
                        <p className="font-black text-slate-900">{user.userName}</p>
                        <p className="text-xs text-slate-500">{user.role}</p>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div className="bg-green-50 rounded-lg p-2">
                        <p className="text-green-600 font-bold">Ventas</p>
                        <p className="font-black text-green-800">{formatCurrency(user.totalValue)}</p>
                      </div>
                      <div className="bg-blue-50 rounded-lg p-2">
                        <p className="text-blue-600 font-bold">Pipeline</p>
                        <p className="font-black text-blue-800">{formatCurrency(user.pipelineValue)}</p>
                      </div>
                      <div className="bg-purple-50 rounded-lg p-2">
                        <p className="text-purple-600 font-bold">Conversión</p>
                        <p className="font-black text-purple-800">{user.conversionRate}%</p>
                      </div>
                      <div className="bg-slate-50 rounded-lg p-2">
                        <p className="text-slate-600 font-bold">Tiendas</p>
                        <p className="font-black text-slate-800">{user.totalShops}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Detailed Table */}
            <div>
              <h3 className="text-lg font-black text-slate-900 mb-4 flex items-center gap-2">
                <UserCheck className="text-indigo-500" size={20} />
                Detalle por Comercial / Responsable
              </h3>
              <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-slate-50">
                    <tr>
                      <th className="text-left p-3 font-black text-slate-600">Usuario</th>
                      <th className="text-left p-3 font-black text-slate-600">Rol</th>
                      <th className="text-right p-3 font-black text-slate-600">Ventas</th>
                      <th className="text-right p-3 font-black text-slate-600">Pipeline</th>
                      <th className="text-center p-3 font-black text-slate-600">Conv.</th>
                      <th className="text-center p-3 font-black text-slate-600">Opps</th>
                      <th className="text-center p-3 font-black text-slate-600">Contactos</th>
                      <th className="text-center p-3 font-black text-slate-600">Tiendas</th>
                    </tr>
                  </thead>
                  <tbody>
                    {metrics.byUser.map((user) => (
                      <tr key={user.userId} className="border-t border-slate-100 hover:bg-slate-50">
                        <td className="p-3 font-bold text-slate-900">{user.userName}</td>
                        <td className="p-3">
                          <span className={`px-2 py-1 rounded-full text-xs font-bold ${user.role === 'Resp. Delegación' ? 'bg-red-100 text-red-700' : 'bg-purple-100 text-purple-700'}`}>
                            {user.role}
                          </span>
                        </td>
                        <td className="p-3 text-right font-black text-green-600">{formatCurrency(user.totalValue)}</td>
                        <td className="p-3 text-right font-bold text-blue-600">{formatCurrency(user.pipelineValue)}</td>
                        <td className="p-3 text-center">
                          <span className={`px-2 py-1 rounded-full text-xs font-black ${user.conversionRate >= 50 ? 'bg-green-100 text-green-700' : user.conversionRate >= 25 ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'}`}>
                            {user.conversionRate}%
                          </span>
                        </td>
                        <td className="p-3 text-center font-bold">{user.wonOpportunities}/{user.totalOpportunities}</td>
                        <td className="p-3 text-center font-bold">{user.totalContacts}</td>
                        <td className="p-3 text-center font-bold">{user.totalShops}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Charts Section */}
            {trends && (
              <div className="mt-6 space-y-6">
                <h3 className="text-lg font-black text-slate-900 mb-4 flex items-center gap-2">
                  <BarChart3 className="text-blue-500" size={20} />
                  Análisis y Tendencias
                </h3>
                
                <div className="grid grid-cols-2 gap-6">
                  {/* Monthly Sales Chart */}
                  <div className="bg-white rounded-xl border border-slate-200 p-4">
                    <h4 className="font-bold text-slate-700 mb-4">Ventas Mensuales (€)</h4>
                    <div className="h-64">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={trends.monthly}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#e3e8ee" />
                          <XAxis dataKey="monthLabel" tick={{ fontSize: 11 }} />
                          <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `${(v/1000).toFixed(0)}k`} />
                          <Tooltip 
                            formatter={(value) => formatCurrency(value)} 
                            labelStyle={{ fontWeight: 'bold' }}
                          />
                          <Bar dataKey="wonValue" fill="#75b882" name="Ventas Cerradas" radius={[4,4,0,0]} />
                          <Bar dataKey="createdValue" fill="#5f87c9" name="Creadas" radius={[4,4,0,0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  {/* Opportunities Count Chart */}
                  <div className="bg-white rounded-xl border border-slate-200 p-4">
                    <h4 className="font-bold text-slate-700 mb-4">Oportunidades por Mes</h4>
                    <div className="h-64">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={trends.monthly}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#e3e8ee" />
                          <XAxis dataKey="monthLabel" tick={{ fontSize: 11 }} />
                          <YAxis tick={{ fontSize: 11 }} />
                          <Tooltip />
                          <Line type="monotone" dataKey="created" stroke="#6b74c1" strokeWidth={2} name="Creadas" dot={{ r: 4 }} />
                          <Line type="monotone" dataKey="won" stroke="#75b882" strokeWidth={2} name="Ganadas" dot={{ r: 4 }} />
                          <Line type="monotone" dataKey="lost" stroke="#d5635c" strokeWidth={2} name="Perdidas" dot={{ r: 4 }} />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  {/* Business Type Distribution */}
                  <div className="bg-white rounded-xl border border-slate-200 p-4">
                    <h4 className="font-bold text-slate-700 mb-4">Distribución por Tipo de Negocio</h4>
                    <div className="h-64 flex items-center justify-center">
                      <ResponsiveContainer width="100%" height="100%">
                        <RechartsPie>
                          <Pie
                            data={[
                              { name: 'Cocina', value: trends.byBusinessType?.cocina?.value || 0, count: trends.byBusinessType?.cocina?.count || 0 },
                              { name: 'Armarios', value: trends.byBusinessType?.armarios?.value || 0, count: trends.byBusinessType?.armarios?.count || 0 }
                            ]}
                            cx="50%"
                            cy="50%"
                            outerRadius={80}
                            fill="#8a8aba"
                            dataKey="value"
                            label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                          >
                            <Cell fill="#d5ab7c" />
                            <Cell fill="#6bae8e" />
                          </Pie>
                          <Tooltip formatter={(value) => formatCurrency(value)} />
                          <Legend />
                        </RechartsPie>
                      </ResponsiveContainer>
                    </div>
                    <div className="grid grid-cols-2 gap-4 mt-4">
                      <div className="flex items-center gap-2 p-2 bg-amber-50 rounded-lg">
                        <UtensilsCrossed className="text-amber-600" size={16} />
                        <div>
                          <p className="text-xs text-amber-600 font-bold">Cocina</p>
                          <p className="text-sm font-black text-amber-800">{trends.byBusinessType?.cocina?.count || 0} opps</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 p-2 bg-emerald-50 rounded-lg">
                        <DoorOpen className="text-emerald-600" size={16} />
                        <div>
                          <p className="text-xs text-emerald-600 font-bold">Armarios</p>
                          <p className="text-sm font-black text-emerald-800">{trends.byBusinessType?.armarios?.count || 0} opps</p>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Funnel */}
                  <div className="bg-white rounded-xl border border-slate-200 p-4">
                    <h4 className="font-bold text-slate-700 mb-4">Embudo de Conversión</h4>
                    <div className="space-y-2">
                      {trends.funnel?.map((stage, idx) => {
                        const maxCount = Math.max(...trends.funnel.map(s => s.count));
                        const width = maxCount > 0 ? (stage.count / maxCount) * 100 : 0;
                        const colors = ['bg-blue-500', 'bg-yellow-500', 'bg-purple-500', 'bg-orange-500'];
                        return (
                          <div key={stage.stage} className="flex items-center gap-3">
                            <span className="w-24 text-xs font-bold text-slate-600 text-right">{stage.name}</span>
                            <div className="flex-1 h-8 bg-slate-100 rounded-lg overflow-hidden relative">
                              <div 
                                className={`h-full ${colors[idx]} transition-all duration-500`}
                                style={{ width: `${width}%` }}
                              />
                              <span className="absolute inset-0 flex items-center justify-center text-xs font-black text-slate-700">
                                {stage.count} ({formatCurrency(stage.value)})
                              </span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* WORK TAB - Original content */}
        {activeTab === 'work' && (
          <>
        {/* Summary Cards */}
        {data?.summary && (
          <div className="p-4 bg-slate-50 border-b grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            <div className="bg-white rounded-xl p-4 border border-slate-200">
              <div className="flex items-center gap-2 text-indigo-600 mb-1">
                <Users size={16} />
                <span className="text-xs font-bold uppercase">Usuarios</span>
              </div>
              <p className="text-2xl font-black text-slate-900">{data.summary.totalUsers}</p>
            </div>
            <div className="bg-white rounded-xl p-4 border border-slate-200">
              <div className="flex items-center gap-2 text-blue-600 mb-1">
                <FolderOpen size={16} />
                <span className="text-xs font-bold uppercase">Proyectos</span>
              </div>
              <p className="text-2xl font-black text-slate-900">{data.summary.totalProjects}</p>
            </div>
            <div className="bg-white rounded-xl p-4 border border-slate-200">
              <div className="flex items-center gap-2 text-purple-600 mb-1">
                <Briefcase size={16} />
                <span className="text-xs font-bold uppercase">Oportunidades</span>
              </div>
              <p className="text-2xl font-black text-slate-900">{data.summary.totalOpportunities}</p>
            </div>
            <div className="bg-white rounded-xl p-4 border border-slate-200">
              <div className="flex items-center gap-2 text-emerald-600 mb-1">
                <FileText size={16} />
                <span className="text-xs font-bold uppercase">Digitalizaciones</span>
              </div>
              <p className="text-2xl font-black text-slate-900">{data.summary.totalDigitalizaciones}</p>
            </div>
          </div>
        )}

        {/* Filters */}
        <div className="p-4 border-b flex gap-4 items-center">
          <div className="relative flex-1">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Buscar por cliente, proyecto o usuario..."
              className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:border-indigo-500"
            />
          </div>
          <select
            value={filterUser}
            onChange={(e) => setFilterUser(e.target.value)}
            className="px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm font-bold focus:outline-none focus:border-indigo-500"
          >
            <option value="">Todos los usuarios</option>
            {data?.users?.map(u => (
              <option key={u.id} value={u.id}>{u.username} ({u.clientName})</option>
            ))}
          </select>
          <button
            onClick={loadData}
            className="p-2 bg-indigo-100 text-indigo-600 rounded-xl hover:bg-indigo-200 transition-colors"
            title="Actualizar"
          >
            <RefreshCw size={18} />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {loading ? (
            <div className="flex items-center justify-center h-40">
              <RefreshCw size={24} className="animate-spin text-indigo-500" />
            </div>
          ) : (
            <>
              {/* Projects Section */}
              <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
                <button
                  onClick={() => toggleSection('projects')}
                  className="w-full px-4 py-3 bg-blue-50 flex justify-between items-center hover:bg-blue-100 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <FolderOpen size={18} className="text-blue-600" />
                    <span className="font-bold text-blue-900">Proyectos ({filteredProjects.length})</span>
                  </div>
                  {expandedSections.projects ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                </button>
                {expandedSections.projects && (
                  <div className="divide-y divide-slate-100 max-h-60 overflow-y-auto">
                    {filteredProjects.length === 0 ? (
                      <p className="p-4 text-center text-slate-400 text-sm">No hay proyectos</p>
                    ) : (
                      filteredProjects.map(proj => (
                        <div key={proj.id} className="p-3 hover:bg-slate-50 flex justify-between items-center">
                          <div>
                            <p className="font-bold text-slate-900">{proj.projectName || 'Sin nombre'}</p>
                            <p className="text-xs text-slate-500">{proj.customerName}</p>
                          </div>
                          <div className="text-right">
                            <p className="text-xs font-bold text-indigo-600">{proj.userName}</p>
                            <p className="text-[10px] text-slate-400">{new Date(proj.createdAt).toLocaleDateString('es-ES')}</p>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                )}
              </div>

              {/* Opportunities Section */}
              <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
                <button
                  onClick={() => toggleSection('opportunities')}
                  className="w-full px-4 py-3 bg-purple-50 flex justify-between items-center hover:bg-purple-100 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <Briefcase size={18} className="text-purple-600" />
                    <span className="font-bold text-purple-900">Oportunidades CRM ({filteredOpportunities.length})</span>
                  </div>
                  {expandedSections.opportunities ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                </button>
                {expandedSections.opportunities && (
                  <div className="divide-y divide-slate-100 max-h-60 overflow-y-auto">
                    {filteredOpportunities.length === 0 ? (
                      <p className="p-4 text-center text-slate-400 text-sm">No hay oportunidades</p>
                    ) : (
                      filteredOpportunities.map(opp => (
                        <div key={opp.id} className="p-3 hover:bg-slate-50 flex justify-between items-center">
                          <div>
                            <p className="font-bold text-slate-900">{opp.title}</p>
                            <p className="text-xs text-slate-500">{opp.contactName} - {opp.stage}</p>
                          </div>
                          <div className="text-right">
                            <p className="font-bold text-purple-600">{opp.value?.toLocaleString('es-ES', { style: 'currency', currency: 'EUR' })}</p>
                            <p className="text-xs text-slate-400">{opp.userName}</p>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                )}
              </div>

              {/* Digitalizaciones Section */}
              <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
                <button
                  onClick={() => toggleSection('digitalizaciones')}
                  className="w-full px-4 py-3 bg-emerald-50 flex justify-between items-center hover:bg-emerald-100 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <FileText size={18} className="text-emerald-600" />
                    <span className="font-bold text-emerald-900">Digitalizaciones ({filteredDigitalizaciones.length})</span>
                  </div>
                  {expandedSections.digitalizaciones ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                </button>
                {expandedSections.digitalizaciones && (
                  <div className="divide-y divide-slate-100 max-h-60 overflow-y-auto">
                    {filteredDigitalizaciones.length === 0 ? (
                      <p className="p-4 text-center text-slate-400 text-sm">No hay digitalizaciones</p>
                    ) : (
                      filteredDigitalizaciones.map(dig => (
                        <div key={dig.id} className="p-3 hover:bg-slate-50 flex justify-between items-center">
                          <div>
                            <p className="font-bold text-slate-900">{dig.projectName || 'Sin nombre'}</p>
                            <p className="text-xs text-slate-500">{dig.customerName} - {dig.lines?.length || 0} líneas</p>
                          </div>
                          <div className="text-right">
                            <p className="font-bold text-emerald-600">{dig.totalConIva?.toLocaleString('es-ES', { style: 'currency', currency: 'EUR' })}</p>
                            <p className="text-xs text-slate-400">{dig.userName}</p>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                )}
              </div>
            </>
          )}
        </div>
          </>
        )}
      </div>
    </div>
  );
};

export default AdminWorkView;
