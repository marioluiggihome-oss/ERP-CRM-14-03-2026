/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
import React from 'react';
import { Package, Plus, Pencil, Trash2, Check, CheckCircle, Target } from 'lucide-react';

/**
 * ArmazonesTab - Pestaña de gestión de armazones/cascos
 */
const ArmazonesTab = ({
  state,
  setState,
  materialLibraryFilter,
  setMaterialLibraryFilter,
  isEditingMaterial,
  setIsEditingMaterial,
  editingMaterialId,
  materialForm,
  setMaterialForm,
  handleCreateMaterial,
  handleEditMaterial,
  handleSaveMaterial,
  handleDeleteMaterial
}) => {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gradient-to-br from-amber-500 to-yellow-500 rounded-xl">
            <Package size={20} className="text-white" />
          </div>
          <div>
            <h3 className="text-lg font-black text-indigo-950 uppercase">Gestión de Armazones / Cascos</h3>
            <p className="text-xs text-indigo-400">Configura los materiales de estructura por tarifa</p>
          </div>
          {/* Filtro por tarifa */}
          <div className="flex gap-2">
            <button
              onClick={() => setMaterialLibraryFilter('TODAS')}
              className={`px-3 py-1.5 rounded-lg text-xs font-black uppercase transition-all ${
                (!materialLibraryFilter || materialLibraryFilter === 'TODAS')
                  ? 'bg-indigo-600 text-white'
                  : 'bg-indigo-100 text-indigo-600 hover:bg-indigo-200'
              }`}
            >
              TODAS
            </button>
            <button
              onClick={() => setMaterialLibraryFilter('ZC')}
              className={`px-3 py-1.5 rounded-lg text-xs font-black uppercase transition-all ${
                materialLibraryFilter === 'ZC'
                  ? 'bg-blue-600 text-white'
                  : 'bg-blue-100 text-blue-600 hover:bg-blue-200'
              }`}
            >
              ZC
            </button>
            <button
              onClick={() => setMaterialLibraryFilter('MV')}
              className={`px-3 py-1.5 rounded-lg text-xs font-black uppercase transition-all ${
                materialLibraryFilter === 'MV'
                  ? 'bg-amber-600 text-white'
                  : 'bg-amber-100 text-amber-600 hover:bg-amber-200'
              }`}
            >
              MV
            </button>
          </div>
        </div>
        {!isEditingMaterial && (
          <button
            onClick={handleCreateMaterial}
            className="flex items-center gap-2 px-4 py-2 bg-amber-600 text-white rounded-xl font-black uppercase text-xs hover:bg-amber-700 transition-all shadow-md"
          >
            <Plus size={16} />
            Nuevo Material
          </button>
        )}
      </div>

      {!isEditingMaterial ? (
        <div className="grid grid-cols-2 gap-4">
          {state.carcassMaterials
            .filter(m => materialLibraryFilter === 'TODAS' || m.library === materialLibraryFilter)
            .map(material => {
            const isDefault = material.id === state.selectedCarcassMaterialId;
            const matLibrary = material.library || 'ZC';
            return (
            <div key={material.id} className={`bg-white border-2 ${isDefault ? 'border-emerald-400 shadow-lg shadow-emerald-100' : 'border-amber-200'} rounded-xl p-5 hover:shadow-lg transition-all`}>
              <div className="flex justify-between items-start mb-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h4 className="text-base font-black text-amber-900">{material.name}</h4>
                    {/* Badge de tarifa */}
                    <span className={`px-2 py-0.5 rounded text-[9px] font-black uppercase ${
                      matLibrary === 'MV' 
                        ? 'bg-amber-100 text-amber-700' 
                        : 'bg-blue-100 text-blue-700'
                    }`}>
                      {matLibrary}
                    </span>
                  </div>
                  {isDefault && (
                    <span className="inline-flex items-center gap-1 mt-1 px-2 py-0.5 bg-emerald-100 text-emerald-700 rounded text-[9px] font-black uppercase">
                      <CheckCircle size={10} /> PREDETERMINADO
                    </span>
                  )}
                </div>
                <div className="flex gap-1">
                  <button
                    onClick={() => handleEditMaterial(material)}
                    className="p-1.5 hover:bg-amber-100 rounded-lg transition-all"
                    title="Editar"
                  >
                    <Pencil size={14} className="text-amber-600" />
                  </button>
                  <button
                    onClick={() => handleDeleteMaterial(material.id)}
                    className="p-1.5 hover:bg-red-100 rounded-lg transition-all"
                    title="Eliminar"
                  >
                    <Trash2 size={14} className="text-red-600" />
                  </button>
                </div>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                <div className="bg-amber-50 rounded-lg p-3 text-center">
                  <p className="text-[9px] font-black text-amber-400 uppercase">Incremento</p>
                  <p className="text-xl font-black text-orange-600">+{material.fixedIncrement}€</p>
                </div>
                <div className="bg-slate-50 rounded-lg p-3 text-center">
                  <p className="text-[9px] font-black text-slate-400 uppercase">Grosor Casco</p>
                  <p className="text-xl font-black text-indigo-600">{material.thickness}mm</p>
                </div>
                <div className="bg-purple-50 rounded-lg p-3 text-center">
                  <p className="text-[9px] font-black text-purple-400 uppercase">Grosor Trasera</p>
                  <p className="text-xl font-black text-purple-600">{material.backThickness || 8}mm</p>
                </div>
              </div>
              {!isDefault && (
                <button
                  onClick={async () => {
                    setState(prev => ({ ...prev, selectedCarcassMaterialId: material.id }));
                    try {
                      await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/settings`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ defaultCarcassMaterialId: material.id })
                      });
                    } catch (err) {
                      console.error('Error saving default carcass:', err);
                    }
                  }}
                  className="mt-3 w-full flex items-center justify-center gap-2 px-3 py-2 bg-violet-600 hover:bg-violet-700 text-white rounded-lg text-[10px] font-black uppercase transition-all"
                >
                  <Target size={12} />
                  Establecer como Predeterminado
                </button>
              )}
            </div>
            );
          })}
        </div>
      ) : (
        /* Material Form */
        <div className="bg-amber-50 border-2 border-amber-300 rounded-xl p-6 max-w-lg mx-auto">
          <h4 className="text-sm font-black text-amber-900 uppercase mb-4">
            {editingMaterialId ? 'Editar Material' : 'Nuevo Material'}
          </h4>
          <div className="space-y-4">
            {/* Selector de Tarifa - Solo al crear */}
            {!editingMaterialId && (
              <div>
                <label className="text-xs font-black text-amber-600 uppercase mb-2 block">Tarifa *</label>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setMaterialForm({...materialForm, library: 'ZC'})}
                    className={`flex-1 py-3 rounded-xl font-black uppercase text-sm transition-all ${
                      materialForm.library === 'ZC'
                        ? 'bg-blue-600 text-white shadow-lg'
                        : 'bg-blue-100 text-blue-600 hover:bg-blue-200'
                    }`}
                  >
                    ZC
                  </button>
                  <button
                    type="button"
                    onClick={() => setMaterialForm({...materialForm, library: 'MV'})}
                    className={`flex-1 py-3 rounded-xl font-black uppercase text-sm transition-all ${
                      materialForm.library === 'MV'
                        ? 'bg-amber-600 text-white shadow-lg'
                        : 'bg-amber-100 text-amber-600 hover:bg-amber-200'
                    }`}
                  >
                    MV
                  </button>
                </div>
                <p className="text-[9px] text-amber-500 mt-1 italic">Una vez creado, no se puede cambiar la tarifa</p>
              </div>
            )}
            {/* Mostrar tarifa actual al editar (no editable) */}
            {editingMaterialId && (
              <div className="bg-slate-100 rounded-xl p-3 text-center">
                <span className="text-xs font-black text-slate-500 uppercase">Tarifa: </span>
                <span className={`px-3 py-1 rounded-lg text-sm font-black ${
                  materialForm.library === 'MV' ? 'bg-amber-200 text-amber-800' : 'bg-blue-200 text-blue-800'
                }`}>
                  {materialForm.library || 'ZC'}
                </span>
              </div>
            )}
            <div>
              <label className="text-xs font-black text-amber-600 uppercase mb-2 block">Nombre del Material *</label>
              <input
                type="text"
                value={materialForm.name}
                onChange={(e) => setMaterialForm({...materialForm, name: e.target.value})}
                placeholder="Ej: Blanco Ártico Standard"
                className="w-full bg-white border border-amber-200 rounded-xl p-3 text-sm font-bold outline-none focus:border-orange-500"
              />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <div>
                <label className="text-xs font-black text-amber-600 uppercase mb-2 block">Incremento Fijo (€)</label>
                <input
                  type="number"
                  value={materialForm.fixedIncrement}
                  onChange={(e) => setMaterialForm({...materialForm, fixedIncrement: parseInt(e.target.value) || 0})}
                  className="w-full bg-white border border-amber-200 rounded-xl p-3 text-lg font-black text-center text-orange-600 outline-none focus:border-orange-500"
                />
              </div>
              <div>
                <label className="text-xs font-black text-amber-600 uppercase mb-2 block">Grosor Casco (mm)</label>
                <input
                  type="number"
                  value={materialForm.thickness}
                  onChange={(e) => setMaterialForm({...materialForm, thickness: parseInt(e.target.value) || 16})}
                  className="w-full bg-white border border-amber-200 rounded-xl p-3 text-lg font-black text-center text-indigo-600 outline-none focus:border-orange-500"
                />
              </div>
              <div>
                <label className="text-xs font-black text-amber-600 uppercase mb-2 block">Grosor Trasera (mm)</label>
                <input
                  type="number"
                  value={materialForm.backThickness}
                  onChange={(e) => setMaterialForm({...materialForm, backThickness: parseInt(e.target.value) || 8})}
                  className="w-full bg-white border border-amber-200 rounded-xl p-3 text-lg font-black text-center text-purple-600 outline-none focus:border-orange-500"
                />
              </div>
            </div>
            <div className="flex gap-3 pt-2">
              <button
                onClick={handleSaveMaterial}
                className="flex-1 bg-amber-600 text-white py-3 rounded-xl font-black uppercase text-xs hover:bg-amber-700 transition-all shadow-lg flex items-center justify-center gap-2"
              >
                <Check size={18} />
                Guardar
              </button>
              <button
                onClick={() => setIsEditingMaterial(false)}
                className="px-6 py-3 bg-slate-200 text-slate-700 rounded-xl font-black uppercase text-xs hover:bg-slate-300 transition-all"
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Info */}
      <div className="bg-slate-50 rounded-xl p-4 text-sm text-slate-600">
        <p className="font-bold text-slate-700 mb-1">¿Qué es el incremento de armazón?</p>
        <p className="text-xs">El incremento fijo se suma al precio de cada mueble para cubrir el coste del material de estructura (casco/armazón). El grosor afecta a los cálculos del despiece.</p>
      </div>
    </div>
  );
};

export default ArmazonesTab;
