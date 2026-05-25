/**
 * DirectorTab.jsx - Panel Director Comercial
 * Extraído de SettingsModal.jsx para mejorar mantenibilidad
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  BarChart3, FolderOpen, RefreshCw, Download, Euro, Target,
  TrendingUp, Users, Store, Award, UserCheck, Briefcase,
  Search, ChevronUp, ChevronDown, FileText
} from 'lucide-react';
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, LineChart, Line
} from 'recharts';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const formatCurrency = (value) => {
  if (!value && value !== 0) return '0 €';
  return new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(value);
};

const DirectorTab = () => {
  const [directorTab, setDirectorTab] = useState('metrics');
  const [directorData, setDirectorData] = useState(null);
  const [directorMetrics, setDirectorMetrics] = useState(null);
  const [directorTrends, setDirectorTrends] = useState(null);
  const [directorLoading, setDirectorLoading] = useState(false);
  const [directorSearchTerm, setDirectorSearchTerm] = useState('');
  const [directorFilterUser, setDirectorFilterUser] = useState('');
  const [directorExpandedSections, setDirectorExpandedSections] = useState({
    projects: true,
    opportunities: true
  });

  const loadDirectorData = useCallback(async () => {
    setDirectorLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/director/data`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setDirectorData(data);
      }
    } catch (error) {
      console.error('Error loading director data:', error);
    } finally {
      setDirectorLoading(false);
    }
  }, []);

  const loadDirectorMetrics = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/director/metrics`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setDirectorMetrics(data);
      }
    } catch (error) {
      console.error('Error loading director metrics:', error);
    }
  }, []);

  const loadDirectorTrends = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/director/trends`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setDirectorTrends(data);
      }
    } catch (error) {
      console.error('Error loading director trends:', error);
    }
  }, []);

  useEffect(() => {
    loadDirectorData();
    loadDirectorMetrics();
    loadDirectorTrends();
  }, [loadDirectorData, loadDirectorMetrics, loadDirectorTrends]);

  const toggleDirectorSection = (section) => {
    setDirectorExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const handleExport = async (type) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/export/${type}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `LUIGGI_${type}_${new Date().toISOString().split('T')[0]}.xlsx`;
        a.click();
        window.URL.revokeObjectURL(url);
      }
    } catch (err) {
      console.error('Error exportando:', err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Sub-tabs for Director Panel */}
      <div className="flex gap-2 mb-4">
        <button 
          onClick={() => setDirectorTab('metrics')}
          className={`px-4 py-2 rounded-lg text-sm font-bold transition-all ${directorTab === 'metrics' ? 'bg-orange-500 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}
        >
          <BarChart3 size={16} className="inline mr-2" />
          Métricas
        </button>
        <button 
          onClick={() => setDirectorTab('work')}
          className={`px-4 py-2 rounded-lg text-sm font-bold transition-all ${directorTab === 'work' ? 'bg-orange-500 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}
        >
          <FolderOpen size={16} className="inline mr-2" />
          Trabajos
        </button>
        <button
          onClick={() => {
            loadDirectorData();
            loadDirectorMetrics();
            loadDirectorTrends();
          }}
          className="p-2 bg-slate-100 text-slate-600 rounded-lg hover:bg-slate-200 transition-colors ml-auto"
          title="Actualizar datos"
        >
          <RefreshCw size={18} />
        </button>
        
        {/* Export Buttons */}
        <div className="flex gap-2">
          <a
            href="/catalogo_productos_completo.xlsx"
            download="LUIGGI_Catalogo_Productos.xlsx"
            className="flex items-center gap-1 px-3 py-2 bg-orange-500 text-white rounded-lg text-xs font-bold hover:bg-orange-600 transition-colors"
            title="Exportar Catálogo Productos"
            data-testid="export-productos-btn"
          >
            <Download size={14} />
            Artículos
          </a>
          <button
            onClick={() => handleExport('presupuestos')}
            className="flex items-center gap-1 px-3 py-2 bg-green-600 text-white rounded-lg text-xs font-bold hover:bg-green-700 transition-colors"
            title="Exportar Presupuestos"
            data-testid="export-presupuestos-btn"
          >
            <Download size={14} />
            Presup.
          </button>
          <button
            onClick={() => handleExport('crm')}
            className="flex items-center gap-1 px-3 py-2 bg-blue-600 text-white rounded-lg text-xs font-bold hover:bg-blue-700 transition-colors"
            title="Exportar CRM"
            data-testid="export-crm-btn"
          >
            <Download size={14} />
            CRM
          </button>
          <button
            onClick={() => handleExport('usuarios')}
            className="flex items-center gap-1 px-3 py-2 bg-purple-600 text-white rounded-lg text-xs font-bold hover:bg-purple-700 transition-colors"
            title="Exportar Usuarios"
            data-testid="export-usuarios-btn"
          >
            <Download size={14} />
            Usuarios
          </button>
        </div>
      </div>

      {/* METRICS TAB */}
      {directorTab === 'metrics' && directorMetrics && (
        <div className="space-y-6">
          {/* Global Summary Cards */}
          <div className="grid grid-cols-5 gap-4">
            <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-xl p-4 text-white">
              <div className="flex items-center gap-2 mb-2">
                <Euro size={20} />
                <span className="text-xs font-bold uppercase opacity-80">Ventas Cerradas</span>
              </div>
              <p className="text-3xl font-black">{formatCurrency(directorMetrics.global?.totalValue)}</p>
              <p className="text-xs opacity-80 mt-1">{directorMetrics.global?.wonOpportunities || 0} oportunidades ganadas</p>
            </div>
            <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-4 text-white">
              <div className="flex items-center gap-2 mb-2">
                <Target size={20} />
                <span className="text-xs font-bold uppercase opacity-80">Pipeline</span>
              </div>
              <p className="text-3xl font-black">{formatCurrency(directorMetrics.global?.pipelineValue)}</p>
              <p className="text-xs opacity-80 mt-1">{directorMetrics.global?.activeOpportunities || 0} oportunidades activas</p>
            </div>
            <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl p-4 text-white">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp size={20} />
                <span className="text-xs font-bold uppercase opacity-80">Conversión</span>
              </div>
              <p className="text-3xl font-black">{directorMetrics.global?.conversionRate || 0}%</p>
              <p className="text-xs opacity-80 mt-1">de {directorMetrics.global?.totalOpportunities || 0} totales</p>
            </div>
            <div className="bg-gradient-to-br from-indigo-500 to-indigo-600 rounded-xl p-4 text-white">
              <div className="flex items-center gap-2 mb-2">
                <Users size={20} />
                <span className="text-xs font-bold uppercase opacity-80">Contactos</span>
              </div>
              <p className="text-3xl font-black">{directorMetrics.global?.totalContacts || 0}</p>
              <p className="text-xs opacity-80 mt-1">{directorMetrics.global?.totalProjects || 0} proyectos</p>
            </div>
            <div className="bg-gradient-to-br from-slate-600 to-slate-700 rounded-xl p-4 text-white">
              <div className="flex items-center gap-2 mb-2">
                <Store size={20} />
                <span className="text-xs font-bold uppercase opacity-80">Red Distribución</span>
              </div>
              <p className="text-3xl font-black">{directorMetrics.global?.totalTiendas || 0}</p>
              <p className="text-xs opacity-80 mt-1">
                {directorMetrics.global?.totalComerciales || 0} comerciales, {directorMetrics.global?.totalResponsables || 0} responsables
              </p>
            </div>
          </div>

          {/* Top Performers */}
          {directorMetrics.topPerformers && directorMetrics.topPerformers.length > 0 && (
            <div>
              <h3 className="text-lg font-black text-slate-900 mb-4 flex items-center gap-2">
                <Award className="text-orange-500" size={20} />
                Top Performers
              </h3>
              <div className="grid grid-cols-3 gap-4">
                {directorMetrics.topPerformers.slice(0, 6).map((user, index) => (
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
          )}

          {/* Detailed Table */}
          {directorMetrics.byUser && directorMetrics.byUser.length > 0 && (
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
                    {directorMetrics.byUser.map((user) => (
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
          )}

          {/* Charts Section */}
          {directorTrends && (
            <div className="space-y-6">
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
                      <BarChart data={directorTrends.monthly || []}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                        <XAxis dataKey="monthLabel" tick={{ fontSize: 11 }} />
                        <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `${(v/1000).toFixed(0)}k`} />
                        <Tooltip formatter={(value) => formatCurrency(value)} labelStyle={{ fontWeight: 'bold' }} />
                        <Bar dataKey="wonValue" fill="#22c55e" name="Ventas Cerradas" radius={[4,4,0,0]} />
                        <Bar dataKey="createdValue" fill="#3b82f6" name="Creadas" radius={[4,4,0,0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Opportunities Count Chart */}
                <div className="bg-white rounded-xl border border-slate-200 p-4">
                  <h4 className="font-bold text-slate-700 mb-4">Oportunidades por Mes</h4>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={directorTrends.monthly || []}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                        <XAxis dataKey="monthLabel" tick={{ fontSize: 11 }} />
                        <YAxis tick={{ fontSize: 11 }} />
                        <Tooltip />
                        <Line type="monotone" dataKey="created" stroke="#6366f1" strokeWidth={2} name="Creadas" dot={{ r: 4 }} />
                        <Line type="monotone" dataKey="won" stroke="#22c55e" strokeWidth={2} name="Ganadas" dot={{ r: 4 }} />
                        <Line type="monotone" dataKey="lost" stroke="#ef4444" strokeWidth={2} name="Perdidas" dot={{ r: 4 }} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Funnel */}
                {directorTrends.funnel && directorTrends.funnel.length > 0 && (
                  <div className="bg-white rounded-xl border border-slate-200 p-4 col-span-2">
                    <h4 className="font-bold text-slate-700 mb-4">Embudo de Conversión</h4>
                    <div className="space-y-2">
                      {directorTrends.funnel.map((stage, idx) => {
                        const maxCount = Math.max(...directorTrends.funnel.map(s => s.count));
                        const width = maxCount > 0 ? (stage.count / maxCount) * 100 : 0;
                        const colors = ['bg-blue-500', 'bg-yellow-500', 'bg-purple-500', 'bg-orange-500', 'bg-green-500'];
                        return (
                          <div key={stage.stage} className="flex items-center gap-3">
                            <span className="w-24 text-xs font-bold text-slate-600 text-right">{stage.name}</span>
                            <div className="flex-1 h-8 bg-slate-100 rounded-lg overflow-hidden relative">
                              <div 
                                className={`h-full ${colors[idx % colors.length]} transition-all duration-500`}
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
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* WORK TAB */}
      {directorTab === 'work' && (
        <div className="space-y-4">
          {/* Summary Cards */}
          {directorData?.summary && (
            <div className="grid grid-cols-4 gap-4 mb-4">
              <div className="bg-white rounded-xl p-4 border border-slate-200">
                <div className="flex items-center gap-2 text-indigo-600 mb-1">
                  <Users size={16} />
                  <span className="text-xs font-bold uppercase">Usuarios</span>
                </div>
                <p className="text-2xl font-black text-slate-900">{directorData.summary.totalUsers}</p>
              </div>
              <div className="bg-white rounded-xl p-4 border border-slate-200">
                <div className="flex items-center gap-2 text-blue-600 mb-1">
                  <FolderOpen size={16} />
                  <span className="text-xs font-bold uppercase">Proyectos</span>
                </div>
                <p className="text-2xl font-black text-slate-900">{directorData.summary.totalProjects}</p>
              </div>
              <div className="bg-white rounded-xl p-4 border border-slate-200">
                <div className="flex items-center gap-2 text-purple-600 mb-1">
                  <Briefcase size={16} />
                  <span className="text-xs font-bold uppercase">Oportunidades</span>
                </div>
                <p className="text-2xl font-black text-slate-900">{directorData.summary.totalOpportunities}</p>
              </div>
              <div className="bg-white rounded-xl p-4 border border-slate-200">
                <div className="flex items-center gap-2 text-emerald-600 mb-1">
                  <FileText size={16} />
                  <span className="text-xs font-bold uppercase">Digitalizaciones</span>
                </div>
                <p className="text-2xl font-black text-slate-900">{directorData.summary.totalDigitalizaciones}</p>
              </div>
            </div>
          )}

          {/* Filters */}
          <div className="flex gap-4 items-center mb-4">
            <div className="relative flex-1">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                value={directorSearchTerm}
                onChange={(e) => setDirectorSearchTerm(e.target.value)}
                placeholder="Buscar por cliente, proyecto o usuario..."
                className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:border-indigo-500"
              />
            </div>
            <select
              value={directorFilterUser}
              onChange={(e) => setDirectorFilterUser(e.target.value)}
              className="px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm font-bold focus:outline-none focus:border-indigo-500"
            >
              <option value="">Todos los usuarios</option>
              {directorData?.users?.map(u => (
                <option key={u.id} value={u.id}>{u.username} ({u.clientName})</option>
              ))}
            </select>
          </div>

          {directorLoading ? (
            <div className="flex items-center justify-center h-40">
              <RefreshCw size={24} className="animate-spin text-indigo-500" />
            </div>
          ) : (
            <>
              {/* Projects Section */}
              <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
                <button
                  onClick={() => toggleDirectorSection('projects')}
                  className="w-full px-4 py-3 bg-blue-50 flex justify-between items-center hover:bg-blue-100 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <FolderOpen size={18} className="text-blue-600" />
                    <span className="font-bold text-blue-900">
                      Proyectos ({directorData?.projects?.filter(p => {
                        const matchesSearch = !directorSearchTerm || 
                          p.customerName?.toLowerCase().includes(directorSearchTerm.toLowerCase()) ||
                          p.projectName?.toLowerCase().includes(directorSearchTerm.toLowerCase());
                        const matchesUser = !directorFilterUser || p.userId === directorFilterUser;
                        return matchesSearch && matchesUser;
                      }).length || 0})
                    </span>
                  </div>
                  {directorExpandedSections.projects ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                </button>
                {directorExpandedSections.projects && (
                  <div className="divide-y divide-slate-100 max-h-60 overflow-y-auto">
                    {(!directorData?.projects || directorData.projects.filter(p => {
                      const matchesSearch = !directorSearchTerm || 
                        p.customerName?.toLowerCase().includes(directorSearchTerm.toLowerCase()) ||
                        p.projectName?.toLowerCase().includes(directorSearchTerm.toLowerCase());
                      const matchesUser = !directorFilterUser || p.userId === directorFilterUser;
                      return matchesSearch && matchesUser;
                    }).length === 0) ? (
                      <p className="p-4 text-center text-slate-400 text-sm">No hay proyectos</p>
                    ) : (
                      directorData.projects.filter(p => {
                        const matchesSearch = !directorSearchTerm || 
                          p.customerName?.toLowerCase().includes(directorSearchTerm.toLowerCase()) ||
                          p.projectName?.toLowerCase().includes(directorSearchTerm.toLowerCase());
                        const matchesUser = !directorFilterUser || p.userId === directorFilterUser;
                        return matchesSearch && matchesUser;
                      }).map(proj => (
                        <div key={proj.id} className="p-3 hover:bg-slate-50 flex justify-between items-center">
                          <div>
                            <p className="font-bold text-slate-900">{proj.projectName || 'Sin nombre'}</p>
                            <p className="text-xs text-slate-500">{proj.customerName}</p>
                          </div>
                          <div className="text-right">
                            <p className="text-xs font-bold text-indigo-600">{proj.userName}</p>
                            <p className="text-[10px] text-slate-400">{proj.createdAt ? new Date(proj.createdAt).toLocaleDateString('es-ES') : ''}</p>
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
                  onClick={() => toggleDirectorSection('opportunities')}
                  className="w-full px-4 py-3 bg-purple-50 flex justify-between items-center hover:bg-purple-100 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <Briefcase size={18} className="text-purple-600" />
                    <span className="font-bold text-purple-900">
                      Oportunidades CRM ({directorData?.opportunities?.filter(o => {
                        const matchesSearch = !directorSearchTerm || 
                          o.title?.toLowerCase().includes(directorSearchTerm.toLowerCase()) ||
                          o.contactName?.toLowerCase().includes(directorSearchTerm.toLowerCase());
                        const matchesUser = !directorFilterUser || o.assignedTo === directorFilterUser;
                        return matchesSearch && matchesUser;
                      }).length || 0})
                    </span>
                  </div>
                  {directorExpandedSections.opportunities ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                </button>
                {directorExpandedSections.opportunities && (
                  <div className="divide-y divide-slate-100 max-h-60 overflow-y-auto">
                    {(!directorData?.opportunities || directorData.opportunities.filter(o => {
                      const matchesSearch = !directorSearchTerm || 
                        o.title?.toLowerCase().includes(directorSearchTerm.toLowerCase()) ||
                        o.contactName?.toLowerCase().includes(directorSearchTerm.toLowerCase());
                      const matchesUser = !directorFilterUser || o.assignedTo === directorFilterUser;
                      return matchesSearch && matchesUser;
                    }).length === 0) ? (
                      <p className="p-4 text-center text-slate-400 text-sm">No hay oportunidades</p>
                    ) : (
                      directorData.opportunities.filter(o => {
                        const matchesSearch = !directorSearchTerm || 
                          o.title?.toLowerCase().includes(directorSearchTerm.toLowerCase()) ||
                          o.contactName?.toLowerCase().includes(directorSearchTerm.toLowerCase());
                        const matchesUser = !directorFilterUser || o.assignedTo === directorFilterUser;
                        return matchesSearch && matchesUser;
                      }).map(opp => (
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
            </>
          )}
        </div>
      )}

      {/* Loading State */}
      {directorTab === 'metrics' && !directorMetrics && (
        <div className="flex items-center justify-center h-40">
          <RefreshCw size={24} className="animate-spin text-indigo-500" />
          <span className="ml-3 text-slate-500">Cargando métricas...</span>
        </div>
      )}
    </div>
  );
};

export default DirectorTab;
