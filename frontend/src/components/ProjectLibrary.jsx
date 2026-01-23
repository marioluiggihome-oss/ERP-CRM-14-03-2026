import React, { useState } from 'react';
import { FolderOpen, Trash2, Eye, Calendar, Euro, Search, FileText } from 'lucide-react';

const ProjectLibrary = ({ state, setState }) => {
  const [searchQuery, setSearchQuery] = useState('');

  const filteredProjects = state.projects.filter(p => 
    p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    p.budgetNumber.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const loadProject = (project) => {
    if (window.confirm(`¿Cargar proyecto "${project.name}" en la mesa de trabajo?`)) {
      setState(prev => ({
        ...prev,
        budgetItemsMontada: [...project.itemsMontada],
        budgetItemsDespiece: [...project.itemsDespiece],
        currentModule: project.module,
        globalFinish: project.finish,
        customerName: project.customerName,
        customerAddress: project.customerAddress,
        budgetNumber: project.budgetNumber,
        internalReference: project.internalReference,
        doorColorLow: project.doorColorLow,
        doorColorHigh: project.doorColorHigh,
        doorColorColumns: project.doorColorColumns,
        sideColor: project.sideColor
      }));
      alert('Proyecto cargado correctamente');
    }
  };

  const deleteProject = (projectId) => {
    if (window.confirm('¿Eliminar este proyecto permanentemente?')) {
      setState(prev => ({
        ...prev,
        projects: prev.projects.filter(p => p.id !== projectId)
      }));
    }
  };

  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-slate-50 to-indigo-50 p-12">
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <div className="p-4 bg-indigo-600 rounded-2xl shadow-xl">
            <FolderOpen size={32} className="text-white" />
          </div>
          <div>
            <h2 className="text-3xl font-black text-slate-900 uppercase tracking-tight">Archivo de Proyectos</h2>
            <p className="text-sm font-bold text-slate-400 uppercase tracking-wider">{filteredProjects.length} expedientes guardados</p>
          </div>
        </div>

        <div className="relative w-96">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-indigo-300" size={18} />
          <input 
            type="text" 
            placeholder="Buscar proyecto..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            className="w-full bg-white border-2 border-indigo-100 rounded-xl py-3 pl-12 pr-4 text-sm font-bold outline-none focus:border-indigo-500 uppercase"
          />
        </div>
      </div>

      {filteredProjects.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center opacity-30">
          <FileText size={80} className="text-slate-400 mb-4" strokeWidth={1} />
          <p className="text-lg font-black uppercase tracking-widest text-slate-600">Sin proyectos archivados</p>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto">
          <div className="grid grid-cols-1 gap-4">
            {filteredProjects.map(project => (
              <div key={project.id} className="bg-white rounded-2xl p-6 shadow-lg border border-indigo-100 hover:shadow-xl transition-all group">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-xl font-black text-slate-900 uppercase">{project.name}</h3>
                      <span className="px-3 py-1 bg-orange-100 text-orange-600 rounded-lg text-[10px] font-black uppercase">
                        {project.module}
                      </span>
                    </div>
                    
                    <div className="grid grid-cols-4 gap-4 mt-4">
                      <div>
                        <p className="text-[9px] font-black text-indigo-300 uppercase tracking-widest">Nº Expediente</p>
                        <p className="text-sm font-black text-indigo-900">{project.budgetNumber}</p>
                      </div>
                      <div>
                        <p className="text-[9px] font-black text-indigo-300 uppercase tracking-widest">Fecha</p>
                        <p className="text-sm font-black text-indigo-900">{new Date(project.date).toLocaleDateString('es-ES')}</p>
                      </div>
                      <div>
                        <p className="text-[9px] font-black text-indigo-300 uppercase tracking-widest">Acabado</p>
                        <p className="text-[10px] font-bold text-slate-600">{project.finish.split(':')[0]}</p>
                      </div>
                      <div>
                        <p className="text-[9px] font-black text-indigo-300 uppercase tracking-widest">Total</p>
                        <p className="text-lg font-black text-orange-600">
                          {project.totalPvp.toLocaleString('es-ES', { style: 'currency', currency: 'EUR' })}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <button 
                      onClick={() => loadProject(project)}
                      className="p-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition-all shadow-md"
                      title="Cargar proyecto"
                    >
                      <Eye size={18} />
                    </button>
                    <button 
                      onClick={() => deleteProject(project.id)}
                      className="p-3 bg-red-100 text-red-600 rounded-xl hover:bg-red-200 transition-all"
                      title="Eliminar proyecto"
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
