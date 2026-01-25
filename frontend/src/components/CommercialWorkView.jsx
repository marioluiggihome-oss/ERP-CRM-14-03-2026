import React, { useState, useEffect } from 'react';
import { X, Briefcase, FolderOpen, FileText, Users, Search, RefreshCw, Store, User, Calendar, Euro, ChevronDown, ChevronUp, Maximize2, Minimize2 } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const CommercialWorkView = ({ isOpen, onClose, currentUser }) => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [isFullScreen, setIsFullScreen] = useState(false); // Pantalla completa
  const [expandedSections, setExpandedSections] = useState({
    projects: true,
    opportunities: true
  });
  const [filterShop, setFilterShop] = useState('');

  useEffect(() => {
    if (isOpen && currentUser?.id) {
      loadData();
    }
  }, [isOpen, currentUser?.id]);

  const loadData = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/commercial/my-shops-work?commercial_id=${currentUser.id}`);
      const result = await response.json();
      setData(result);
    } catch (err) {
      console.error('Error loading commercial data:', err);
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
      p.shopName?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesShop = !filterShop || p.userId === filterShop;
    return matchesSearch && matchesShop;
  }) || [];

  const filteredOpportunities = data?.opportunities?.filter(o => {
    const matchesSearch = !searchTerm || 
      o.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      o.contactName?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      o.shopName?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesShop = !filterShop || o.assignedTo === filterShop || o.createdBy === filterShop;
    return matchesSearch && matchesShop;
  }) || [];

  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-5xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="bg-purple-900 text-white px-6 py-4 flex justify-between items-center shrink-0">
          <div className="flex items-center gap-3">
            <Briefcase size={24} />
            <div>
              <h2 className="font-black text-lg uppercase tracking-wider">Mis Tiendas</h2>
              <p className="text-purple-300 text-xs">Trabajo de tiendas asignadas a {currentUser?.clientName}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-lg transition-colors">
            <X size={20} />
          </button>
        </div>

        {/* Summary Cards */}
        {data?.summary && (
          <div className="p-4 bg-slate-50 border-b grid grid-cols-3 gap-4">
            <div className="bg-white rounded-xl p-4 border border-slate-200">
              <div className="flex items-center gap-2 text-purple-600 mb-1">
                <Store size={16} />
                <span className="text-xs font-bold uppercase">Tiendas Asignadas</span>
              </div>
              <p className="text-2xl font-black text-slate-900">{data.summary.totalShops}</p>
            </div>
            <div className="bg-white rounded-xl p-4 border border-slate-200">
              <div className="flex items-center gap-2 text-blue-600 mb-1">
                <FolderOpen size={16} />
                <span className="text-xs font-bold uppercase">Proyectos</span>
              </div>
              <p className="text-2xl font-black text-slate-900">{data.summary.totalProjects}</p>
            </div>
            <div className="bg-white rounded-xl p-4 border border-slate-200">
              <div className="flex items-center gap-2 text-emerald-600 mb-1">
                <Briefcase size={16} />
                <span className="text-xs font-bold uppercase">Oportunidades</span>
              </div>
              <p className="text-2xl font-black text-slate-900">{data.summary.totalOpportunities}</p>
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
              placeholder="Buscar por cliente, proyecto o tienda..."
              className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:border-purple-500"
            />
          </div>
          <select
            value={filterShop}
            onChange={(e) => setFilterShop(e.target.value)}
            className="px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm font-bold focus:outline-none focus:border-purple-500"
          >
            <option value="">Todas las tiendas</option>
            {data?.shops?.map(shop => (
              <option key={shop.id} value={shop.id}>{shop.clientName} ({shop.username})</option>
            ))}
          </select>
          <button
            onClick={loadData}
            className="p-2 bg-purple-100 text-purple-600 rounded-xl hover:bg-purple-200 transition-colors"
            title="Actualizar"
          >
            <RefreshCw size={18} />
          </button>
        </div>

        {/* Shops List */}
        {data?.shops?.length > 0 && (
          <div className="p-4 border-b bg-purple-50">
            <p className="text-xs font-bold text-purple-900 uppercase mb-2">Tiendas Asignadas:</p>
            <div className="flex flex-wrap gap-2">
              {data.shops.map(shop => (
                <span
                  key={shop.id}
                  className="px-3 py-1 bg-white text-purple-700 rounded-lg text-xs font-bold border border-purple-200"
                >
                  <Store size={12} className="inline mr-1" />
                  {shop.clientName}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {loading ? (
            <div className="flex items-center justify-center h-40">
              <RefreshCw size={24} className="animate-spin text-purple-500" />
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
                      <p className="p-4 text-center text-slate-400 text-sm">No hay proyectos de tus tiendas</p>
                    ) : (
                      filteredProjects.map(proj => (
                        <div key={proj.id} className="p-3 hover:bg-slate-50 flex justify-between items-center">
                          <div>
                            <p className="font-bold text-slate-900">{proj.budgetNumber || proj.projectName || 'Sin nombre'}</p>
                            <p className="text-xs text-slate-500">{proj.customerName}</p>
                          </div>
                          <div className="text-right">
                            <p className="text-xs font-bold text-purple-600">
                              <Store size={12} className="inline mr-1" />
                              {proj.shopName}
                            </p>
                            <p className="text-[10px] text-slate-400">{proj.createdAt ? new Date(proj.createdAt).toLocaleDateString('es-ES') : '-'}</p>
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
                  className="w-full px-4 py-3 bg-emerald-50 flex justify-between items-center hover:bg-emerald-100 transition-colors"
                >
                  <div className="flex items-center gap-2">
                    <Briefcase size={18} className="text-emerald-600" />
                    <span className="font-bold text-emerald-900">Oportunidades CRM ({filteredOpportunities.length})</span>
                  </div>
                  {expandedSections.opportunities ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                </button>
                {expandedSections.opportunities && (
                  <div className="divide-y divide-slate-100 max-h-60 overflow-y-auto">
                    {filteredOpportunities.length === 0 ? (
                      <p className="p-4 text-center text-slate-400 text-sm">No hay oportunidades de tus tiendas</p>
                    ) : (
                      filteredOpportunities.map(opp => (
                        <div key={opp.id} className="p-3 hover:bg-slate-50 flex justify-between items-center">
                          <div>
                            <p className="font-bold text-slate-900">{opp.title}</p>
                            <div className="flex items-center gap-2">
                              <p className="text-xs text-slate-500">{opp.contactName}</p>
                              <span className={`text-[10px] px-2 py-0.5 rounded font-bold ${
                                opp.stage === 'won' ? 'bg-emerald-100 text-emerald-700' :
                                opp.stage === 'lost' ? 'bg-red-100 text-red-700' :
                                opp.stage === 'proposal' ? 'bg-blue-100 text-blue-700' :
                                'bg-slate-100 text-slate-700'
                              }`}>
                                {opp.stage?.toUpperCase()}
                              </span>
                            </div>
                          </div>
                          <div className="text-right">
                            <p className="font-bold text-emerald-600">{opp.value?.toLocaleString('es-ES', { style: 'currency', currency: 'EUR' })}</p>
                            <p className="text-xs text-purple-600">
                              <Store size={10} className="inline mr-1" />
                              {opp.shopName || 'Sin asignar'}
                            </p>
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

export default CommercialWorkView;
