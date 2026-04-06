import React, { useState, useEffect } from 'react';
import { Building2, Check, ChevronDown, Library } from 'lucide-react';
import { librariesAPI } from '../services/api';

/**
 * Selector de Biblioteca (ZC, MV, etc.)
 * Permite cambiar entre diferentes catálogos de productos
 */
const LibrarySelector = ({ 
  currentLibrary = 'ZC', 
  onLibraryChange, 
  allowedLibraries = ['ZC'], 
  className = '' 
}) => {
  const [libraries, setLibraries] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(true);

  // Cargar bibliotecas disponibles
  useEffect(() => {
    const loadLibraries = async () => {
      try {
        const data = await librariesAPI.getAll();
        // Filtrar solo las bibliotecas activas y permitidas al usuario
        const filtered = data.filter(lib => 
          lib.isActive && allowedLibraries.includes(lib.code)
        );
        setLibraries(filtered);
      } catch (error) {
        console.error('Error loading libraries:', error);
        // Bibliotecas por defecto si falla la carga
        setLibraries([
          { code: 'ZC', name: 'Zona Cocinas', pricingSystem: 'zones' }
        ]);
      } finally {
        setLoading(false);
      }
    };
    loadLibraries();
  }, [allowedLibraries]);

  const currentLib = libraries.find(l => l.code === currentLibrary) || {
    code: currentLibrary,
    name: currentLibrary,
    pricingSystem: 'zones'
  };

  const handleSelect = (code) => {
    if (onLibraryChange) {
      onLibraryChange(code);
    }
    setIsOpen(false);
  };

  // Si solo hay una biblioteca disponible, no mostrar selector
  if (libraries.length <= 1 && !loading) {
    return (
      <div className={`flex items-center gap-2 px-3 py-2 bg-slate-800/50 rounded-lg ${className}`}>
        <Library className="w-4 h-4 text-amber-400" />
        <span className="text-sm font-medium text-white">{currentLib.name}</span>
      </div>
    );
  }

  return (
    <div className={`relative ${className}`}>
      {/* Botón principal */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={loading}
        className="flex items-center gap-2 px-3 py-2 bg-slate-800/80 hover:bg-slate-700 
                   border border-slate-600 rounded-lg transition-all min-w-[160px]"
      >
        <Library className="w-4 h-4 text-amber-400" />
        <span className="text-sm font-medium text-white flex-1 text-left">
          {loading ? 'Cargando...' : currentLib.name}
        </span>
        <ChevronDown className={`w-4 h-4 text-slate-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {/* Dropdown */}
      {isOpen && (
        <>
          {/* Overlay para cerrar al hacer clic fuera */}
          <div 
            className="fixed inset-0 z-40" 
            onClick={() => setIsOpen(false)}
          />
          
          {/* Lista de bibliotecas */}
          <div className="absolute top-full left-0 mt-1 w-full min-w-[200px] bg-slate-800 
                          border border-slate-600 rounded-lg shadow-xl z-50 overflow-hidden">
            {libraries.map((lib) => (
              <button
                key={lib.code}
                onClick={() => handleSelect(lib.code)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 text-left 
                           hover:bg-slate-700 transition-colors
                           ${lib.code === currentLibrary ? 'bg-amber-500/20' : ''}`}
              >
                <Building2 className={`w-4 h-4 ${lib.code === currentLibrary ? 'text-amber-400' : 'text-slate-400'}`} />
                <div className="flex-1">
                  <div className="text-sm font-medium text-white">{lib.name}</div>
                  <div className="text-xs text-slate-400">
                    {lib.pricingSystem === 'zones' ? 'Zonas Z1-Z12' : 'Tarifas T1-T21'}
                    {lib.productCount && ` • ${lib.productCount} productos`}
                  </div>
                </div>
                {lib.code === currentLibrary && (
                  <Check className="w-4 h-4 text-amber-400" />
                )}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
};

export default LibrarySelector;
