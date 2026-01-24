import React, { useState, useEffect } from 'react';
import { FolderOpen, Trash2, Eye, Calendar, Euro, Search, FileText, Save, Loader, RefreshCw, Plus, Archive, ArchiveRestore, Filter } from 'lucide-react';
import { projectsAPI } from '../services/api';

const ProjectLibrary = ({ state, setState }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [projects, setProjects] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [viewFilter, setViewFilter] = useState('active'); // 'active', 'archived', 'all'

  // Cargar proyectos desde MongoDB
  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    setIsLoading(true);
    try {
      const data = await projectsAPI.getAll(state.currentUser?.id);
      setProjects(data);
    } catch (err) {
      console.error('Error loading projects:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const filteredProjects = projects.filter(p => 
    (p.customerName?.toLowerCase() || '').includes(searchQuery.toLowerCase()) ||
    (p.budgetNumber?.toLowerCase() || '').includes(searchQuery.toLowerCase())
  );

  // Guardar presupuesto actual como proyecto
  const saveCurrentBudget = async () => {
    if (!state.budgetNumber) {
      alert('Por favor, ingresa un número de expediente');
      return;
    }

    const totalItems = state.budgetItemsMontada.length + state.budgetItemsDespiece.length;
    if (totalItems === 0) {
      alert('No hay items en el presupuesto actual para guardar');
      return;
    }

    setIsSaving(true);
    try {
      // Calcular total del presupuesto
      const calculateTotal = (items, pointValue) => {
        return items.reduce((sum, item) => sum + (item.totalPoints || 0) * pointValue, 0);
      };
      
      const totalMontada = calculateTotal(state.budgetItemsMontada, state.pointValueMontada);
      const totalDespiece = calculateTotal(state.budgetItemsDespiece, state.pointValueDespiece);
      const totalPvp = totalMontada + totalDespiece;

      const projectData = {
        budgetNumber: state.budgetNumber,
        customerName: state.customerName || 'Sin nombre',
        customerAddress: state.customerAddress || '',
        internalReference: state.internalReference || '',
        itemsMontada: state.budgetItemsMontada.map(item => ({
          id: item.id,
          productId: item.productId,
          productCode: item.productCode,
          productName: item.productName,
          quantity: item.quantity,
          customWidth: item.customWidth,
          customHeight: item.customHeight,
          customDepth: item.customDepth,
          unitPoints: item.unitPoints,
          totalPoints: item.totalPoints
        })),
        itemsDespiece: state.budgetItemsDespiece.map(item => ({
          id: item.id,
          productId: item.productId,
          productCode: item.productCode,
          productName: item.productName,
          quantity: item.quantity,
          unitPoints: item.unitPoints,
          totalPoints: item.totalPoints
        })),
        doorColorLow: state.doorColorLow || '',
        doorColorHigh: state.doorColorHigh || '',
        doorColorColumns: state.doorColorColumns || '',
        sideColor: state.sideColor || '',
        selectedCarcassMaterialId: state.selectedCarcassMaterialId,
        totalPvp: totalPvp,
        status: 'draft'
      };

      await projectsAPI.create(projectData, state.currentUser?.id || 'admin');
      alert('Proyecto guardado correctamente');
      loadProjects(); // Recargar lista
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
        currentTab: 'budget' // Ir a la mesa de trabajo
      }));
      alert('Proyecto cargado correctamente');
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

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    try {
      return new Date(dateStr).toLocaleDateString('es-ES', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
      });
    } catch {
      return 'N/A';
    }
  };

  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-slate-50 to-indigo-50 p-8">
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

        <div className="flex items-center gap-4">
          {/* Buscar */}
          <div className="relative w-72">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-indigo-300" size={16} />
            <input 
              type="text" 
              placeholder="Buscar proyecto..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="w-full bg-white border-2 border-indigo-100 rounded-xl py-2.5 pl-10 pr-4 text-sm font-bold outline-none focus:border-indigo-500 uppercase"
            />
          </div>

          {/* Refrescar */}
          <button
            onClick={loadProjects}
            disabled={isLoading}
            className="p-2.5 bg-white border-2 border-indigo-100 text-indigo-600 rounded-xl hover:bg-indigo-50 transition-all"
            title="Refrescar lista"
          >
            <RefreshCw size={18} className={isLoading ? 'animate-spin' : ''} />
          </button>

          {/* Guardar actual */}
          <button
            onClick={saveCurrentBudget}
            disabled={isSaving}
            className="flex items-center gap-2 px-5 py-2.5 bg-indigo-600 text-white rounded-xl font-black uppercase text-xs hover:bg-indigo-700 transition-all shadow-lg disabled:opacity-50"
          >
            {isSaving ? <Loader size={16} className="animate-spin" /> : <Save size={16} />}
            Guardar Actual
          </button>
        </div>
      </div>

      {/* Contenido */}
      {isLoading ? (
        <div className="flex-1 flex flex-col items-center justify-center">
          <Loader size={48} className="text-indigo-400 animate-spin mb-4" />
          <p className="text-sm font-bold uppercase tracking-widest text-slate-400">Cargando proyectos...</p>
        </div>
      ) : filteredProjects.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center opacity-40">
          <FileText size={80} className="text-slate-400 mb-4" strokeWidth={1} />
          <p className="text-lg font-black uppercase tracking-widest text-slate-600">Sin proyectos archivados</p>
          <p className="text-sm text-slate-400 mt-2">Guarda tu primer presupuesto usando el botón "Guardar Actual"</p>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto">
          <div className="grid grid-cols-1 gap-4">
            {filteredProjects.map(project => (
              <div key={project.id} className="bg-white rounded-2xl p-5 shadow-lg border border-indigo-100 hover:shadow-xl transition-all group">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-3">
                      <h3 className="text-lg font-black text-slate-900 uppercase">
                        {project.customerName || 'Sin nombre'}
                      </h3>
                      <span className={`px-3 py-1 rounded-lg text-[10px] font-black uppercase ${
                        project.status === 'completed' 
                          ? 'bg-green-100 text-green-600' 
                          : project.status === 'archived'
                          ? 'bg-slate-100 text-slate-600'
                          : 'bg-orange-100 text-orange-600'
                      }`}>
                        {project.status === 'completed' ? 'Completado' : project.status === 'archived' ? 'Archivado' : 'Borrador'}
                      </span>
                    </div>
                    
                    <div className="grid grid-cols-5 gap-4">
                      <div>
                        <p className="text-[9px] font-black text-indigo-300 uppercase tracking-widest">Nº Expediente</p>
                        <p className="text-sm font-black text-indigo-900">{project.budgetNumber}</p>
                      </div>
                      <div>
                        <p className="text-[9px] font-black text-indigo-300 uppercase tracking-widest">Fecha</p>
                        <p className="text-sm font-black text-indigo-900">{formatDate(project.createdAt)}</p>
                      </div>
                      <div>
                        <p className="text-[9px] font-black text-indigo-300 uppercase tracking-widest">Items Montada</p>
                        <p className="text-sm font-bold text-slate-600">{project.itemsMontada?.length || 0}</p>
                      </div>
                      <div>
                        <p className="text-[9px] font-black text-indigo-300 uppercase tracking-widest">Items Despiece</p>
                        <p className="text-sm font-bold text-slate-600">{project.itemsDespiece?.length || 0}</p>
                      </div>
                      <div>
                        <p className="text-[9px] font-black text-indigo-300 uppercase tracking-widest">Total PVP</p>
                        <p className="text-lg font-black text-orange-600">
                          {(project.totalPvp || 0).toLocaleString('es-ES', { style: 'currency', currency: 'EUR' })}
                        </p>
                      </div>
                    </div>

                    {project.customerAddress && (
                      <p className="mt-2 text-xs text-slate-400">{project.customerAddress}</p>
                    )}
                  </div>

                  <div className="flex gap-2 ml-4">
                    <button 
                      onClick={() => loadProject(project)}
                      className="p-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition-all shadow-md"
                      title="Cargar proyecto"
                      data-testid={`load-project-${project.id}`}
                    >
                      <Eye size={18} />
                    </button>
                    <button 
                      onClick={() => deleteProject(project.id)}
                      className="p-3 bg-red-100 text-red-600 rounded-xl hover:bg-red-200 transition-all"
                      title="Eliminar proyecto"
                      data-testid={`delete-project-${project.id}`}
                    >
                      <Trash2 size={18} />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ProjectLibrary;
