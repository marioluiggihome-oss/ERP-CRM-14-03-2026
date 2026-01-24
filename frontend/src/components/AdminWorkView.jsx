import React, { useState, useEffect } from 'react';
import { X, Briefcase, FolderOpen, FileText, Users, Search, RefreshCw, Building2, User, Calendar, Euro, ChevronDown, ChevronUp } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const AdminWorkView = ({ isOpen, onClose, currentUser }) => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedSections, setExpandedSections] = useState({
    projects: true,
    opportunities: true,
    digitalizaciones: false
  });
  const [filterUser, setFilterUser] = useState('');

  useEffect(() => {
    if (isOpen) {
      loadData();
    }
  }, [isOpen]);

  const loadData = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/admin/all-work`);
      const result = await response.json();
      setData(result);
    } catch (err) {
      console.error('Error loading admin data:', err);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const toggleSection = (section) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }));
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
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-6xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="bg-indigo-950 text-white px-6 py-4 flex justify-between items-center shrink-0">
          <div className="flex items-center gap-3">
            <Building2 size={24} />
            <div>
              <h2 className="font-black text-lg uppercase tracking-wider">Panel Administrador</h2>
              <p className="text-indigo-300 text-xs">Todos los trabajos del sistema</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-lg transition-colors">
            <X size={20} />
          </button>
        </div>

        {/* Summary Cards */}
        {data?.summary && (
          <div className="p-4 bg-slate-50 border-b grid grid-cols-4 gap-4">
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
      </div>
    </div>
  );
};

export default AdminWorkView;
