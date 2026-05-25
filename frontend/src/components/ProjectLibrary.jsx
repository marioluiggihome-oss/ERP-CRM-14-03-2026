import React, { useState, useEffect } from 'react';
import { FolderOpen, Trash2, Eye, Search, FileText, Save, Loader, RefreshCw, Archive, ArchiveRestore, Target, ChevronDown, Clock, CheckCircle, XCircle, Truck, Factory, Send, RotateCcw, AlertTriangle, Copy } from 'lucide-react';
import { projectsAPI, crmOpportunitiesAPI } from '../services/api';


// ─── Configuración de estados ───────────────────────────────────────────────
const STATUS_CONFIG = {
  borrador:       { label: 'Borrador',       color: 'bg-slate-100 text-slate-600',   icon: FileText,     dot: 'bg-slate-400' },
  draft:          { label: 'Borrador',       color: 'bg-slate-100 text-slate-600',   icon: FileText,     dot: 'bg-slate-400' },
  enviado:        { label: 'Enviado',        color: 'bg-blue-100 text-blue-700',     icon: Send,         dot: 'bg-blue-500' },
  aceptado:       { label: 'Aceptado',       color: 'bg-green-100 text-green-700',   icon: CheckCircle,  dot: 'bg-green-500' },
  en_fabricacion: { label: 'En Fabricación', color: 'bg-orange-100 text-orange-700', icon: Factory,      dot: 'bg-orange-500' },
  entregado:      { label: 'Entregado',      color: 'bg-indigo-100 text-indigo-700', icon: Truck,        dot: 'bg-indigo-500' },
  rechazado:      { label: 'Rechazado',      color: 'bg-red-100 text-red-600',       icon: XCircle,      dot: 'bg-red-500' },
  archived:       { label: 'Archivado',      color: 'bg-slate-100 text-slate-500',   icon: Archive,      dot: 'bg-slate-300' },
};

const TRANSITIONS = {
  borrador:       [{ to: 'enviado',        label: 'Marcar como Enviado',        icon: Send }],
  draft:          [{ to: 'enviado',        label: 'Marcar como Enviado',        icon: Send }],
  enviado:        [{ to: 'aceptado',       label: 'Marcar como Aceptado',       icon: CheckCircle },
                   { to: 'rechazado',      label: 'Marcar como Rechazado',      icon: XCircle }],
  aceptado:       [{ to: 'en_fabricacion', label: 'Enviar a Fabricación',       icon: Factory },
                   { to: 'rechazado',      label: 'Marcar como Rechazado',      icon: XCircle }],
  en_fabricacion: [{ to: 'entregado',      label: 'Marcar como Entregado',      icon: Truck }],
  entregado:      [],
  rechazado:      [{ to: 'borrador',       label: 'Reabrir como Borrador',      icon: RotateCcw }],
  archived:       [],
};

const StatusBadge = ({ status }) => {
  const cfg = STATUS_CONFIG[status] || STATUS_CONFIG.borrador;
  const Icon = cfg.icon;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[10px] font-black uppercase ${cfg.color}`}>
      <Icon size={11} />
      {cfg.label}
    </span>
  );
};

const StatusDropdown = ({ project, onStatusChange }) => {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const transitions = TRANSITIONS[project.status] || [];

  if (transitions.length === 0) return <StatusBadge status={project.status} />;

  const handleChange = async (to) => {
    setOpen(false);
    setLoading(true);
    try {
      await onStatusChange(project.id, to);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(v => !v)}
        className="inline-flex items-center gap-1.5 focus:outline-none"
        disabled={loading}
      >
        {loading ? <Loader size={14} className="animate-spin text-slate-400" /> : (
          <>
            <StatusBadge status={project.status} />
            <ChevronDown size={12} className="text-slate-400" />
          </>
        )}
      </button>
      {open && (
        <div className="absolute left-0 top-8 z-50 bg-white rounded-xl shadow-2xl border border-slate-100 min-w-[200px] py-1 overflow-hidden">
          {transitions.map(t => {
            const Icon = t.icon;
            return (
              <button
                key={t.to}
                onClick={() => handleChange(t.to)}
                className="w-full flex items-center gap-2 px-4 py-2.5 text-xs font-bold text-slate-700 hover:bg-slate-50 uppercase text-left transition-colors"
              >
                <Icon size={14} className="text-slate-400" />
                {t.label}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};

// ─── Componente principal ────────────────────────────────────────────────────
const ProjectLibrary = ({ state, setState }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [projects, setProjects] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [viewFilter, setViewFilter] = useState('active');
  const [expiryWarnings, setExpiryWarnings] = useState([]);

  useEffect(() => { loadProjects(); }, []);

  const loadProjects = async () => {
    setIsLoading(true);
    try {
      const data = await projectsAPI.getAll(state.currentUser?.id);
      setProjects(data);
      // Detectar presupuestos caducados o próximos a caducar (7 días)
      const now = new Date();
      const soon = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);
      const warnings = data.filter(p => {
        if (!p.validUntil) return false;
        const exp = new Date(p.validUntil);
        return exp <= soon && p.status !== 'entregado' && p.status !== 'rechazado' && p.status !== 'archived';
      });
      setExpiryWarnings(warnings);
    } catch (err) {
      console.error('Error loading projects:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStatusChange = async (projectId, newStatus) => {
    try {
      const updated = await projectsAPI.changeStatus(
        projectId, newStatus,
        state.currentUser?.username || 'usuario'
      );
      setProjects(prev => prev.map(p => p.id === projectId ? { ...p, ...updated } : p));
    } catch (err) {
      alert('Error al cambiar estado: ' + err.message);
    }
  };

  const filteredProjects = projects.filter(p => {
    const statusMatch = viewFilter === 'all'
      ? true
      : viewFilter === 'archived'
        ? p.status === 'archived'
        : p.status !== 'archived';
    const searchMatch =
      (p.customerName?.toLowerCase() || '').includes(searchQuery.toLowerCase()) ||
      (p.budgetNumber?.toLowerCase() || '').includes(searchQuery.toLowerCase());
    return statusMatch && searchMatch;
  });

  // Contar por estado
  const counts = {
    active: projects.filter(p => p.status !== 'archived').length,
    archived: projects.filter(p => p.status === 'archived').length,
    all: projects.length,
  };

  const saveCurrentBudget = async () => {
    if (!state.budgetNumber) { alert('Por favor, ingresa un número de expediente'); return; }
    const totalItems = state.budgetItemsMontada.length + state.budgetItemsDespiece.length;
    if (totalItems === 0) { alert('No hay items en el presupuesto actual para guardar'); return; }

    setIsSaving(true);
    try {
      const totalMontada = state.budgetItemsMontada.reduce((s, i) => s + (i.totalPoints || 0) * state.pointValueMontada, 0);
      const totalDespiece = state.budgetItemsDespiece.reduce((s, i) => s + (i.totalPoints || 0) * state.pointValueDespiece, 0);

      const projectData = {
        budgetNumber: state.budgetNumber,
        customerName: state.customerName || 'Sin nombre',
        customerAddress: state.customerAddress || '',
        internalReference: state.internalReference || '',
        itemsMontada: state.budgetItemsMontada.map(item => ({
          id: item.id, productId: item.productId, productCode: item.productCode,
          productName: item.productName, quantity: item.quantity,
          customWidth: item.customWidth, customHeight: item.customHeight, customDepth: item.customDepth,
          unitPoints: item.unitPoints, totalPoints: item.totalPoints
        })),
        itemsDespiece: state.budgetItemsDespiece.map(item => ({
          id: item.id, productId: item.productId, productCode: item.productCode,
          productName: item.productName, quantity: item.quantity,
          unitPoints: item.unitPoints, totalPoints: item.totalPoints
        })),
        doorColorLow: state.doorColorLow || '',
        doorColorHigh: state.doorColorHigh || '',
        doorColorColumns: state.doorColorColumns || '',
        sideColor: state.sideColor || '',
        selectedCarcassMaterialId: state.selectedCarcassMaterialId,
        totalPvp: totalPvp,
        totalCoste: Math.round(totalCoste * 100) / 100,
        margen: Math.round(margen * 10) / 10,
        totalConIVA: Math.round(totalConIVA * 100) / 100,
        ivaRate: ivaRate,
        descuentoAplicado: descuento,
        status: 'borrador',
        // Caducidad por defecto: 30 días
        validUntil: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
      };

      await projectsAPI.create(projectData, state.currentUser?.id || 'admin');
      alert('Proyecto guardado correctamente');
      loadProjects();
    } catch (err) {
      alert('Error al guardar proyecto: ' + err.message);
    } finally {
      setIsSaving(false);
    }
  };

  const loadProject = async (project) => {
    if (window.confirm(`¿Cargar proyecto "${project.customerName || project.budgetNumber}" en la mesa de trabajo?`)) {
      setState(prev => ({
        ...prev,
        budgetItemsMontada: project.itemsMontada || [],
        budgetItemsDespiece: project.itemsDespiece || [],
        customerName: project.customerName || '',
        customerAddress: project.customerAddress || '',
        budgetNumber: project.budgetNumber || '',
        internalReference: project.internalReference || '',
        doorColorLow: project.doorColorLow || '',
        doorColorHigh: project.doorColorHigh || '',
        doorColorColumns: project.doorColorColumns || '',
        sideColor: project.sideColor || '',
        selectedCarcassMaterialId: project.selectedCarcassMaterialId || prev.selectedCarcassMaterialId,
        currentTab: 'budget'
      }));
    }
  };

  const deleteProject = async (projectId) => {
    if (window.confirm('¿Eliminar este proyecto permanentemente?')) {
      try {
        await projectsAPI.delete(projectId);
        setProjects(prev => prev.filter(p => p.id !== projectId));
      } catch (err) {
        alert('Error al eliminar proyecto: ' + err.message);
      }
    }
  };

  const toggleArchive = async (project) => {
    const isArchived = project.status === 'archived';
    if (window.confirm(`¿${isArchived ? 'Desarchivar' : 'Archivar'} el proyecto "${project.customerName || project.budgetNumber}"?`)) {
      try {
        const newStatus = isArchived ? 'borrador' : 'archived';
        await projectsAPI.update(project.id, { status: newStatus });
        setProjects(prev => prev.map(p => p.id === project.id ? { ...p, status: newStatus } : p));
      } catch (err) {
        alert('Error: ' + err.message);
      }
    }
  };

  const createOpportunity = async (project) => {
    if (window.confirm(`¿Crear oportunidad CRM para "${project.customerName || project.budgetNumber}"?`)) {
      try {
        const result = await crmOpportunitiesAPI.createFromProject(project.id);
        alert(`✅ Oportunidad creada: "${result.opportunity.title}"\nValor: ${result.opportunity.value.toLocaleString('es-ES')}€`);
      } catch (err) {
        alert('Error: ' + err.message);
      }
    }
  };

  const cloneProject = async (project) => {
    const newNum = window.prompt(
      `Duplicar "${project.budgetNumber}"\nNúmero de expediente para la copia:`,
      `${project.budgetNumber}-COPIA`
    );
    if (!newNum) return;
    try {
      await projectsAPI.clone(project.id, newNum, state.currentUser?.id || 'admin');
      alert(`✅ Presupuesto duplicado como "${newNum}"`);
      loadProjects();
    } catch (err) {
      alert('Error: ' + err.message);
    }
  };

  const formatDate = (d) => {
    if (!d) return '—';
    try { return new Date(d).toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit', year: 'numeric' }); }
    catch { return '—'; }
  };

  const isExpiringSoon = (p) => {
    if (!p.validUntil) return false;
    const exp = new Date(p.validUntil);
    const now = new Date();
    return exp <= new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000) && exp > now;
  };

  const isExpired = (p) => {
    if (!p.validUntil) return false;
    return new Date(p.validUntil) < new Date();
  };

  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-slate-50 to-indigo-50 p-8">
      {/* Avisos de caducidad */}
      {expiryWarnings.length > 0 && (
        <div className="mb-4 bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-start gap-3">
          <AlertTriangle size={18} className="text-amber-500 mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-xs font-black text-amber-700 uppercase">
              {expiryWarnings.length} presupuesto{expiryWarnings.length > 1 ? 's' : ''} próximo{expiryWarnings.length > 1 ? 's' : ''} a caducar
            </p>
            <p className="text-xs text-amber-600 mt-0.5">
              {expiryWarnings.map(p => p.budgetNumber).join(', ')}
            </p>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-indigo-600 rounded-2xl shadow-xl">
            <FolderOpen size={28} className="text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-black text-slate-900 uppercase tracking-tight">Archivo de Proyectos</h2>
            <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">{projects.length} expedientes guardados</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Filtros */}
          <div className="flex bg-white rounded-xl border-2 border-indigo-100 p-1">
            {[['active', 'Activos', counts.active], ['archived', 'Archivados', counts.archived], ['all', 'Todos', counts.all]].map(([val, lbl, cnt]) => (
              <button key={val} onClick={() => setViewFilter(val)}
                className={`px-4 py-2 rounded-lg text-xs font-black uppercase transition-all ${viewFilter === val ? 'bg-indigo-600 text-white shadow-md' : 'text-slate-500 hover:bg-indigo-50'}`}>
                {lbl} ({cnt})
              </button>
            ))}
          </div>

          {/* Búsqueda */}
          <div className="relative w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-indigo-300" size={15} />
            <input type="text" placeholder="Buscar..." value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="w-full bg-white border-2 border-indigo-100 rounded-xl py-2.5 pl-9 pr-4 text-sm font-bold outline-none focus:border-indigo-500 uppercase" />
          </div>

          <button onClick={loadProjects} disabled={isLoading}
            className="p-2.5 bg-white border-2 border-indigo-100 text-indigo-600 rounded-xl hover:bg-indigo-50 transition-all" title="Refrescar">
            <RefreshCw size={18} className={isLoading ? 'animate-spin' : ''} />
          </button>

          <button onClick={saveCurrentBudget} disabled={isSaving}
            className="flex items-center gap-2 px-5 py-2.5 bg-indigo-600 text-white rounded-xl font-black uppercase text-xs hover:bg-indigo-700 transition-all shadow-lg disabled:opacity-50">
            {isSaving ? <Loader size={16} className="animate-spin" /> : <Save size={16} />}
            Guardar Actual
          </button>
        </div>
      </div>

      {/* Lista */}
      {isLoading ? (
        <div className="flex-1 flex flex-col items-center justify-center">
          <Loader size={48} className="text-indigo-400 animate-spin mb-4" />
          <p className="text-sm font-bold uppercase tracking-widest text-slate-400">Cargando proyectos...</p>
        </div>
      ) : filteredProjects.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center opacity-40">
          <FileText size={80} className="text-slate-400 mb-4" strokeWidth={1} />
          <p className="text-lg font-black uppercase tracking-widest text-slate-600">Sin proyectos</p>
          <p className="text-sm text-slate-400 mt-2">Guarda tu primer presupuesto usando "Guardar Actual"</p>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto">
          <div className="grid grid-cols-1 gap-4">
            {filteredProjects.map(project => {
              const expiring = isExpiringSoon(project);
              const expired = isExpired(project);
              return (
                <div key={project.id}
                  className={`bg-white rounded-2xl p-5 shadow-lg border transition-all hover:shadow-xl ${expiring ? 'border-amber-300' : expired ? 'border-red-200' : 'border-indigo-100'}`}>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-3">
                        <h3 className="text-lg font-black text-slate-900 uppercase">
                          {project.customerName || 'Sin nombre'}
                        </h3>
                        <StatusDropdown project={project} onStatusChange={handleStatusChange} />
                        {expiring && (
                          <span className="inline-flex items-center gap-1 px-2 py-1 bg-amber-100 text-amber-700 rounded-lg text-[9px] font-black uppercase">
                            <AlertTriangle size={10} /> Caduca pronto
                          </span>
                        )}
                        {expired && (
                          <span className="inline-flex items-center gap-1 px-2 py-1 bg-red-100 text-red-600 rounded-lg text-[9px] font-black uppercase">
                            <XCircle size={10} /> Caducado
                          </span>
                        )}
                      </div>

                      <div className="grid grid-cols-6 gap-4">
                        <div>
                          <p className="text-[9px] font-black text-indigo-300 uppercase tracking-widest">Nº Expediente</p>
                          <p className="text-sm font-black text-indigo-900">{project.budgetNumber}</p>
                        </div>
                        <div>
                          <p className="text-[9px] font-black text-indigo-300 uppercase tracking-widest">Creado</p>
                          <p className="text-sm font-black text-indigo-900">{formatDate(project.createdAt)}</p>
                        </div>
                        <div>
                          <p className="text-[9px] font-black text-indigo-300 uppercase tracking-widest">Válido hasta</p>
                          <p className={`text-sm font-black ${expired ? 'text-red-500' : expiring ? 'text-amber-600' : 'text-slate-600'}`}>
                            {formatDate(project.validUntil)}
                          </p>
                        </div>
                        <div>
                          <p className="text-[9px] font-black text-indigo-300 uppercase tracking-widest">Montada</p>
                          <p className="text-sm font-bold text-slate-600">{project.itemsMontada?.length || 0} items</p>
                        </div>
                        <div>
                          <p className="text-[9px] font-black text-indigo-300 uppercase tracking-widest">Despiece</p>
                          <p className="text-sm font-bold text-slate-600">{project.itemsDespiece?.length || 0} items</p>
                        </div>
                        <div>
                          <p className="text-[9px] font-black text-indigo-300 uppercase tracking-widest">Total PVP</p>
                          <p className="text-lg font-black text-orange-600">
                            {(project.totalPvp || 0).toLocaleString('es-ES', { style: 'currency', currency: 'EUR' })}
                          </p>
                        </div>
                      </div>

                      {/* Totales desglosados */}
                      {(project.totalCoste > 0 || project.totalConIVA > 0) && (
                        <div className="mt-3 flex items-center gap-6 bg-slate-50 rounded-xl px-4 py-2.5">
                          {project.totalCoste > 0 && (
                            <div>
                              <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest">Coste</p>
                              <p className="text-sm font-black text-slate-600">
                                {project.totalCoste.toLocaleString('es-ES', { style: 'currency', currency: 'EUR' })}
                              </p>
                            </div>
                          )}
                          {project.margen > 0 && (
                            <div>
                              <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest">Margen</p>
                              <p className="text-sm font-black text-green-600">{project.margen.toFixed(1)}%</p>
                            </div>
                          )}
                          {project.descuentoAplicado > 0 && (
                            <div>
                              <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest">Descuento</p>
                              <p className="text-sm font-black text-amber-600">{project.descuentoAplicado.toFixed(1)}%</p>
                            </div>
                          )}
                          {project.totalConIVA > 0 && (
                            <div>
                              <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest">Total c/IVA ({project.ivaRate || 21}%)</p>
                              <p className="text-sm font-black text-indigo-700">
                                {project.totalConIVA.toLocaleString('es-ES', { style: 'currency', currency: 'EUR' })}
                              </p>
                            </div>
                          )}
                          {project.versions?.length > 0 && (
                            <div className="ml-auto">
                              <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest">Versiones</p>
                              <p className="text-sm font-black text-slate-500">{project.versions.length} guardadas</p>
                            </div>
                          )}
                        </div>
                      )}

                      {project.customerAddress && (
                        <p className="mt-2 text-xs text-slate-400">{project.customerAddress}</p>
                      )}

                      {/* Historial de estados (si hay) */}
                      {project.statusHistory?.length > 0 && (
                        <div className="mt-3 flex items-center gap-2">
                          <Clock size={11} className="text-slate-300" />
                          <span className="text-[9px] text-slate-400 font-bold uppercase">
                            Último cambio: {project.statusHistory[project.statusHistory.length - 1]?.at
                              ? formatDate(project.statusHistory[project.statusHistory.length - 1].at)
                              : '—'}
                            {' '}por {project.statusHistory[project.statusHistory.length - 1]?.by || '—'}
                          </span>
                        </div>
                      )}
                    </div>

                    <div className="flex gap-2 ml-4">
                      <button onClick={() => loadProject(project)}
                        className="p-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition-all shadow-md" title="Cargar proyecto">
                        <Eye size={18} />
                      </button>
                      <button onClick={() => cloneProject(project)}
                        className="p-3 bg-cyan-100 text-cyan-700 rounded-xl hover:bg-cyan-200 transition-all" title="Duplicar presupuesto">
                        <Copy size={18} />
                      </button>
                      <button onClick={() => createOpportunity(project)}
                        className="p-3 bg-purple-100 text-purple-600 rounded-xl hover:bg-purple-200 transition-all" title="Crear oportunidad CRM">
                        <Target size={18} />
                      </button>
                      <button onClick={() => toggleArchive(project)}
                        className={`p-3 rounded-xl transition-all ${project.status === 'archived' ? 'bg-green-100 text-green-600 hover:bg-green-200' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}
                        title={project.status === 'archived' ? 'Desarchivar' : 'Archivar'}>
                        {project.status === 'archived' ? <ArchiveRestore size={18} /> : <Archive size={18} />}
                      </button>
                      <button onClick={() => deleteProject(project.id)}
                        className="p-3 bg-red-100 text-red-600 rounded-xl hover:bg-red-200 transition-all" title="Eliminar">
                        <Trash2 size={18} />
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default ProjectLibrary;
