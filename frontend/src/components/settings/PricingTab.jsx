import React, { useState } from 'react';
import { Euro, Loader, Save } from 'lucide-react';
import { settingsAPI, librariesAPI } from '../../services/api';

/**
 * PricingTab - Pestaña de Márgenes y Configuración de Precios
 */
const PricingTab = ({ state, setState }) => {
  const [isSavingSettings, setIsSavingSettings] = useState(false);

  const handleSavePricingSettings = async () => {
    setIsSavingSettings(true);
    try {
      await settingsAPI.update({
        pointValueMontada: state.pointValueMontada,
        pointValueDespiece: state.pointValueDespiece,
        specialIncrementWidth: state.specialIncrementWidth,
        specialIncrementHeight: state.specialIncrementHeight,
        specialIncrementDepth: state.specialIncrementDepth,
        librarySpecialIncrements: state.librarySpecialIncrements,
        vigaCutIncrement: state.vigaCutIncrement || 0,
        libraryVigaCutIncrements: state.libraryVigaCutIncrements || { ZC: 0, MV: 0 }
      });
      alert('Configuración guardada correctamente');
    } catch (err) {
      console.error('Error saving settings:', err);
      alert('Error al guardar la configuración');
    } finally {
      setIsSavingSettings(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-gradient-to-r from-indigo-50 to-purple-50 p-6 rounded-2xl border border-indigo-200">
        <h3 className="text-xl font-black text-indigo-950 uppercase mb-2 flex items-center gap-3">
          <Euro size={24} className="text-orange-600" />
          Márgenes Maestros del Sistema
        </h3>
        <p className="text-xs text-indigo-600 font-bold uppercase">Configuración Global de Costos y Valores</p>
      </div>

      {/* Valores de Punto */}
      <div className="bg-white border border-indigo-100 rounded-2xl p-6 shadow-sm">
        <h3 className="text-sm font-black text-indigo-900 uppercase tracking-widest mb-4 flex items-center gap-2">
          Valor de Punto Base
        </h3>
        
        {/* Valor de punto por BIBLIOTECA (MONTADA) */}
        <div className="mb-4">
          <label className="text-xs font-black text-indigo-600 uppercase mb-3 block">
            Valor de Punto por Tarifa (Montada)
          </label>
          <div className="grid grid-cols-2 gap-4">
            {(state.libraries || []).map(lib => (
              <div key={lib.code} className="bg-gradient-to-br from-indigo-50 to-purple-50 border-2 border-indigo-200 rounded-xl p-4">
                <label className="text-xs font-black text-indigo-500 uppercase mb-2 flex items-center gap-2">
                  <span className={`w-3 h-3 rounded-full ${lib.code === 'ZC' ? 'bg-blue-500' : 'bg-amber-500'}`}></span>
                  {lib.code} (€/punto)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={state.libraryPointValues?.[lib.code] || lib.pointValue || 1.0}
                  onChange={async (e) => {
                    const newValue = parseFloat(e.target.value) || 1.0;
                    setState(prev => ({
                      ...prev,
                      libraryPointValues: {
                        ...prev.libraryPointValues,
                        [lib.code]: newValue
                      }
                    }));
                    try {
                      await librariesAPI.update(lib.code, { pointValue: newValue });
                    } catch (err) {
                      console.error('Error guardando valor de punto:', err);
                    }
                  }}
                  className="w-full bg-white border-2 border-indigo-300 rounded-xl p-3 text-2xl font-black text-indigo-900 outline-none focus:border-orange-500 text-center"
                />
              </div>
            ))}
            {(!state.libraries || state.libraries.length === 0) && (
              <div className="col-span-2 text-center text-indigo-400 py-4">
                <Loader className="w-6 h-6 animate-spin inline mr-2" />
                Cargando bibliotecas...
              </div>
            )}
          </div>
        </div>

        <div className="border-t border-indigo-100 my-4"></div>
        
        {/* Valor de punto DESPIECE */}
        <div>
          <label className="text-xs font-black text-indigo-400 uppercase mb-2 block">
            Despiece (€/punto) - Común a todas las tarifas
          </label>
          <input
            type="number"
            step="0.01"
            value={state.pointValueDespiece}
            onChange={(e) => setState(prev => ({ ...prev, pointValueDespiece: parseFloat(e.target.value) || 0.88 }))}
            className="w-full bg-indigo-50 border-2 border-indigo-200 rounded-xl p-4 text-2xl font-black text-indigo-900 outline-none focus:border-orange-500 text-center max-w-xs"
          />
        </div>
      </div>

      {/* Incrementos Cortes Especiales POR TARIFA */}
      <div className="bg-white border border-orange-100 rounded-2xl p-6 shadow-sm">
        <h3 className="text-sm font-black text-orange-900 uppercase tracking-widest mb-4 flex items-center gap-2">
          Incrementos Cortes Especiales por Tarifa
        </h3>
        
        {/* Incrementos ZC */}
        <div className="mb-4 bg-gradient-to-br from-blue-50 to-indigo-50 border-2 border-blue-200 rounded-xl p-4">
          <label className="text-xs font-black text-blue-600 uppercase mb-3 flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-blue-500"></span>
            TARIFA ZC
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            <div>
              <label className="text-[10px] font-black text-blue-400 uppercase mb-1 block">Ancho (€)</label>
              <input
                type="number"
                value={state.librarySpecialIncrements?.ZC?.width ?? state.specialIncrementWidth}
                onChange={(e) => setState(prev => ({
                  ...prev,
                  librarySpecialIncrements: {
                    ...prev.librarySpecialIncrements,
                    ZC: { ...prev.librarySpecialIncrements?.ZC, width: parseInt(e.target.value) || 45 }
                  }
                }))}
                className="w-full bg-white border-2 border-blue-200 rounded-xl p-3 text-xl font-black text-blue-900 outline-none focus:border-blue-500 text-center"
              />
            </div>
            <div>
              <label className="text-[10px] font-black text-blue-400 uppercase mb-1 block">Alto (€)</label>
              <input
                type="number"
                value={state.librarySpecialIncrements?.ZC?.height ?? state.specialIncrementHeight}
                onChange={(e) => setState(prev => ({
                  ...prev,
                  librarySpecialIncrements: {
                    ...prev.librarySpecialIncrements,
                    ZC: { ...prev.librarySpecialIncrements?.ZC, height: parseInt(e.target.value) || 45 }
                  }
                }))}
                className="w-full bg-white border-2 border-blue-200 rounded-xl p-3 text-xl font-black text-blue-900 outline-none focus:border-blue-500 text-center"
              />
            </div>
            <div>
              <label className="text-[10px] font-black text-blue-400 uppercase mb-1 block">Fondo (€)</label>
              <input
                type="number"
                value={state.librarySpecialIncrements?.ZC?.depth ?? state.specialIncrementDepth}
                onChange={(e) => setState(prev => ({
                  ...prev,
                  librarySpecialIncrements: {
                    ...prev.librarySpecialIncrements,
                    ZC: { ...prev.librarySpecialIncrements?.ZC, depth: parseInt(e.target.value) || 45 }
                  }
                }))}
                className="w-full bg-white border-2 border-blue-200 rounded-xl p-3 text-xl font-black text-blue-900 outline-none focus:border-blue-500 text-center"
              />
            </div>
          </div>
        </div>
        
        {/* Incrementos MV */}
        <div className="mb-4 bg-gradient-to-br from-amber-50 to-orange-50 border-2 border-amber-200 rounded-xl p-4">
          <label className="text-xs font-black text-amber-600 uppercase mb-3 flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-amber-500"></span>
            TARIFA MV
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            <div>
              <label className="text-[10px] font-black text-amber-400 uppercase mb-1 block">Ancho (€)</label>
              <input
                type="number"
                value={state.librarySpecialIncrements?.MV?.width ?? state.specialIncrementWidth}
                onChange={(e) => setState(prev => ({
                  ...prev,
                  librarySpecialIncrements: {
                    ...prev.librarySpecialIncrements,
                    MV: { ...prev.librarySpecialIncrements?.MV, width: parseInt(e.target.value) || 45 }
                  }
                }))}
                className="w-full bg-white border-2 border-amber-200 rounded-xl p-3 text-xl font-black text-amber-900 outline-none focus:border-amber-500 text-center"
              />
            </div>
            <div>
              <label className="text-[10px] font-black text-amber-400 uppercase mb-1 block">Alto (€)</label>
              <input
                type="number"
                value={state.librarySpecialIncrements?.MV?.height ?? state.specialIncrementHeight}
                onChange={(e) => setState(prev => ({
                  ...prev,
                  librarySpecialIncrements: {
                    ...prev.librarySpecialIncrements,
                    MV: { ...prev.librarySpecialIncrements?.MV, height: parseInt(e.target.value) || 45 }
                  }
                }))}
                className="w-full bg-white border-2 border-amber-200 rounded-xl p-3 text-xl font-black text-amber-900 outline-none focus:border-amber-500 text-center"
              />
            </div>
            <div>
              <label className="text-[10px] font-black text-amber-400 uppercase mb-1 block">Fondo (€)</label>
              <input
                type="number"
                value={state.librarySpecialIncrements?.MV?.depth ?? state.specialIncrementDepth}
                onChange={(e) => setState(prev => ({
                  ...prev,
                  librarySpecialIncrements: {
                    ...prev.librarySpecialIncrements,
                    MV: { ...prev.librarySpecialIncrements?.MV, depth: parseInt(e.target.value) || 45 }
                  }
                }))}
                className="w-full bg-white border-2 border-amber-200 rounded-xl p-3 text-xl font-black text-amber-900 outline-none focus:border-amber-500 text-center"
              />
            </div>
          </div>
        </div>
        
        {/* Corte Viga por biblioteca */}
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-blue-50 rounded-xl p-4">
            <label className="text-xs font-black text-blue-600 uppercase mb-2 block">Corte Viga ZC (€)</label>
            <input
              type="number"
              step="0.5"
              value={state.libraryVigaCutIncrements?.ZC || state.vigaCutIncrement || 0}
              onChange={(e) => setState(prev => ({ 
                ...prev, 
                libraryVigaCutIncrements: {
                  ...prev.libraryVigaCutIncrements,
                  ZC: parseFloat(e.target.value) || 0
                }
              }))}
              className="w-full bg-white border-2 border-blue-300 rounded-xl p-3 text-xl font-black text-blue-800 outline-none focus:border-blue-500 text-center"
            />
          </div>
          <div className="bg-green-50 rounded-xl p-4">
            <label className="text-xs font-black text-green-600 uppercase mb-2 block">Corte Viga MV (€)</label>
            <input
              type="number"
              step="0.5"
              value={state.libraryVigaCutIncrements?.MV || 0}
              onChange={(e) => setState(prev => ({ 
                ...prev, 
                libraryVigaCutIncrements: {
                  ...prev.libraryVigaCutIncrements,
                  MV: parseFloat(e.target.value) || 0
                }
              }))}
              className="w-full bg-white border-2 border-green-300 rounded-xl p-3 text-xl font-black text-green-800 outline-none focus:border-green-500 text-center"
            />
          </div>
        </div>
        
        <p className="text-xs text-slate-500 mt-3 italic">Los incrementos se aplican según la tarifa activa cuando hay corte especial.</p>
        
        {/* Botón Guardar Configuración */}
        <div className="mt-6 flex justify-end">
          <button
            onClick={handleSavePricingSettings}
            disabled={isSavingSettings}
            className="flex items-center gap-2 px-6 py-3 bg-green-600 text-white rounded-xl font-black uppercase text-sm hover:bg-green-700 transition-all shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
            data-testid="save-pricing-btn"
          >
            {isSavingSettings ? (
              <>
                <Loader size={18} className="animate-spin" />
                Guardando...
              </>
            ) : (
              <>
                <Save size={18} />
                Guardar Configuración
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default PricingTab;
