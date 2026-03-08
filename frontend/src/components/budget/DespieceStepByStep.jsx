/**
 * DespieceStepByStep.jsx
 * Componente para el flujo paso a paso del presupuestador de despiece
 * Flujo: Fabricante → Modelo → Matriz de precios (Alto×Ancho)
 */
import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { 
  Factory, Box, Ruler, ChevronRight, ChevronLeft, Check, Plus,
  Package, Calculator, RefreshCw, Edit2, Trash2, ArrowLeft
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const DespieceStepByStep = ({ 
  onAddItems,
  despieceFilters,
  setDespieceFilters 
}) => {
  // Estado del flujo
  const [step, setStep] = useState(1); // 1: Fabricante, 2: Modelo, 3: Matriz
  const [loading, setLoading] = useState(false);
  
  // Selecciones
  const [selectedManufacturer, setSelectedManufacturer] = useState('');
  const [selectedCollection, setSelectedCollection] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('PUERTA');
  
  // Opciones
  const [manufacturers, setManufacturers] = useState([]);
  const [collections, setCollections] = useState([]);
  
  // Productos y matriz de precios
  const [products, setProducts] = useState([]);
  const [priceMatrix, setPriceMatrix] = useState({});

  // Cargar fabricantes
  const loadManufacturers = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/api/despiece-budgeter/products/filters`);
      const data = await response.json();
      setManufacturers(data.manufacturers || []);
    } catch (error) {
      console.error('Error loading manufacturers:', error);
    }
  }, []);
  
  // Cargar colecciones
  const loadCollections = useCallback(async (manufacturer) => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/despiece-budgeter/products/filters?manufacturer=${encodeURIComponent(manufacturer)}`);
      const data = await response.json();
      let cols = data.collections || [];
      
      // Filtrar según categoría
      if (selectedCategory === 'PUERTA') {
        cols = cols.filter(c => !c.toLowerCase().includes('tirador'));
      } else if (selectedCategory === 'TIRADOR') {
        cols = cols.filter(c => c.toLowerCase().includes('tirador'));
      }
      
      setCollections(cols);
    } catch (error) {
      console.error('Error loading collections:', error);
    } finally {
      setLoading(false);
    }
  }, [selectedCategory]);
  
  // Cargar productos y construir matriz
  const loadProducts = useCallback(async (manufacturer, collection) => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('manufacturer', manufacturer);
      params.append('collection', collection);
      params.append('limit', '3000');
      
      console.log('Loading products for:', manufacturer, collection);
      const response = await fetch(`${API_URL}/api/despiece-budgeter/products?${params.toString()}`);
      const data = await response.json();
      console.log('Products loaded:', data.length);
      setProducts(data);
      
      // Construir matriz de precios
      const matrix = {};
      data.forEach(p => {
        const h = p.height || 0;
        const w = p.width || 0;
        if (h && w) {
          if (!matrix[h]) matrix[h] = {};
          matrix[h][w] = {
            price: p.priceZ1 || p.price || 0,
            product: p
          };
        }
      });
      console.log('Matrix built:', Object.keys(matrix).length, 'heights');
      setPriceMatrix(matrix);
    } catch (error) {
      console.error('Error loading products:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  // Cargar fabricantes al montar
  useEffect(() => {
    loadManufacturers();
  }, [loadManufacturers]);
  
  // Cargar colecciones cuando cambie fabricante
  useEffect(() => {
    if (selectedManufacturer) {
      loadCollections(selectedManufacturer);
    } else {
      setCollections([]);
    }
  }, [selectedManufacturer, selectedCategory, loadCollections]);
  
  // Cargar productos cuando cambie colección
  useEffect(() => {
    if (selectedManufacturer && selectedCollection) {
      loadProducts(selectedManufacturer, selectedCollection);
    }
  }, [selectedManufacturer, selectedCollection, loadProducts]);
  
  // Obtener alturas y anchos disponibles
  const availableHeights = useMemo(() => {
    return Object.keys(priceMatrix).map(Number).sort((a, b) => a - b);
  }, [priceMatrix]);
  
  const availableWidths = useMemo(() => {
    const widths = new Set();
    Object.values(priceMatrix).forEach(row => {
      Object.keys(row).forEach(w => widths.add(Number(w)));
    });
    return [...widths].sort((a, b) => a - b);
  }, [priceMatrix]);
  
  // Añadir item desde la matriz
  const addItemFromMatrix = (height, width) => {
    const cell = priceMatrix[height]?.[width];
    if (!cell) return;
    
    const item = {
      id: `dp-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      productId: cell.product.id,
      code: cell.product.code || `DF-${selectedCollection.substring(0,10).replace(/\s/g,'')}-${height}x${width}`,
      name: `${selectedCategory} ${selectedCollection}`,
      manufacturer: selectedManufacturer,
      collection: selectedCollection,
      color: cell.product.color || 'Estándar',
      finish: cell.product.finish || 'Estándar',
      category: selectedCategory,
      height: height,
      width: width,
      thickness: cell.product.thickness || 18,
      depth: cell.product.thickness || 18,
      quantity: 1,
      areaM2: (height / 1000) * (width / 1000),
      pricePerM2: 0,
      unitPrice: cell.price,
      totalPrice: cell.price,
      isDespiece: true,
      editable: true
    };
    
    onAddItems?.([item]);
  };
  
  // Resetear
  const handleReset = () => {
    setStep(1);
    setSelectedManufacturer('');
    setSelectedCollection('');
    setProducts([]);
    setPriceMatrix({});
  };
  
  // Volver al paso anterior
  const goBack = () => {
    if (step === 3) {
      setStep(2);
      setSelectedCollection('');
      setProducts([]);
      setPriceMatrix({});
    } else if (step === 2) {
      setStep(1);
      setSelectedManufacturer('');
      setCollections([]);
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header con breadcrumb */}
      <div className="bg-gradient-to-r from-purple-800 to-indigo-800 text-white px-4 py-2 shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* Breadcrumb navegable */}
            <div className="flex items-center gap-1 text-xs">
              <button 
                onClick={() => { setStep(1); setSelectedManufacturer(''); setSelectedCollection(''); }}
                className={`px-2 py-1 rounded transition-all ${step >= 1 ? 'bg-orange-500 text-white' : 'bg-white/20'}`}
              >
                <Factory size={12} className="inline mr-1" />
                {selectedManufacturer || 'Fabricante'}
              </button>
              {step >= 2 && (
                <>
                  <ChevronRight size={12} className="text-purple-300" />
                  <button 
                    onClick={() => { setStep(2); setSelectedCollection(''); }}
                    className={`px-2 py-1 rounded transition-all ${step >= 2 ? 'bg-orange-500 text-white' : 'bg-white/20'}`}
                  >
                    <Box size={12} className="inline mr-1" />
                    {selectedCollection ? selectedCollection.substring(0, 20) + (selectedCollection.length > 20 ? '...' : '') : 'Modelo'}
                  </button>
                </>
              )}
              {step >= 3 && (
                <>
                  <ChevronRight size={12} className="text-purple-300" />
                  <span className="px-2 py-1 rounded bg-green-500 text-white">
                    <Ruler size={12} className="inline mr-1" />
                    Medidas
                  </span>
                </>
              )}
            </div>
          </div>
          
          {step > 1 && (
            <button
              onClick={handleReset}
              className="text-[10px] text-purple-200 hover:text-white flex items-center gap-1"
            >
              <RefreshCw size={12} />
              Reiniciar
            </button>
          )}
        </div>
      </div>
      
      {/* Contenido */}
      <div className="flex-1 overflow-y-auto p-3">
        {/* STEP 1: Seleccionar Fabricante */}
        {step === 1 && (
          <div className="space-y-4">
            {/* Categoría */}
            <div className="flex justify-center gap-2 mb-4">
              {[
                { value: 'PUERTA', label: 'Puertas' },
                { value: 'TIRADOR', label: 'Tiradores' },
                { value: 'COSTADO', label: 'Costados' }
              ].map(cat => (
                <button
                  key={cat.value}
                  onClick={() => setSelectedCategory(cat.value)}
                  className={`px-4 py-2 rounded-lg font-bold text-xs transition-all ${
                    selectedCategory === cat.value
                      ? 'bg-purple-600 text-white shadow-lg'
                      : 'bg-purple-100 text-purple-700 hover:bg-purple-200'
                  }`}
                >
                  {cat.label}
                </button>
              ))}
            </div>
            
            {/* Fabricantes */}
            <div className="text-center mb-3">
              <h3 className="text-sm font-black text-slate-700 uppercase">Selecciona Fabricante</h3>
            </div>
            
            <div className="grid grid-cols-2 gap-3">
              {manufacturers.map(mfr => (
                <button
                  key={mfr}
                  onClick={() => {
                    setSelectedManufacturer(mfr);
                    setStep(2);
                  }}
                  className="p-4 rounded-xl border-2 border-slate-200 bg-white hover:border-purple-500 hover:bg-purple-50 transition-all flex items-center gap-3"
                >
                  <Factory size={24} className="text-purple-600" />
                  <span className="text-sm font-black text-slate-800">{mfr}</span>
                </button>
              ))}
            </div>
          </div>
        )}
        
        {/* STEP 2: Seleccionar Modelo/Colección */}
        {step === 2 && (
          <div className="space-y-3">
            <div className="flex items-center gap-2 mb-3">
              <button
                onClick={goBack}
                className="p-2 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
              >
                <ArrowLeft size={16} className="text-slate-600" />
              </button>
              <h3 className="text-sm font-black text-slate-700 uppercase">
                Modelos de {selectedManufacturer}
              </h3>
            </div>
            
            {loading ? (
              <div className="flex justify-center py-8">
                <RefreshCw size={32} className="animate-spin text-purple-500" />
              </div>
            ) : collections.length > 0 ? (
              <div className="grid grid-cols-1 gap-2 max-h-[400px] overflow-y-auto">
                {collections.map(col => (
                  <button
                    key={col}
                    onClick={() => {
                      setSelectedCollection(col);
                      setStep(3);
                    }}
                    className="p-3 rounded-lg border-2 border-slate-200 bg-white hover:border-purple-500 hover:bg-purple-50 transition-all text-left flex items-center gap-3"
                  >
                    <Box size={18} className="text-purple-600 shrink-0" />
                    <span className="text-xs font-bold text-slate-700">{col}</span>
                    <ChevronRight size={14} className="text-slate-400 ml-auto" />
                  </button>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <Package size={40} className="mx-auto text-slate-300 mb-2" />
                <p className="text-sm text-slate-400">No hay modelos disponibles</p>
              </div>
            )}
          </div>
        )}
        
        {/* STEP 3: Matriz de Precios */}
        {step === 3 && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 mb-2">
              <button
                onClick={goBack}
                className="p-2 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
              >
                <ArrowLeft size={16} className="text-slate-600" />
              </button>
              <div>
                <h3 className="text-xs font-black text-slate-700 uppercase">Matriz de Precios</h3>
                <p className="text-[10px] text-slate-400">Haz clic en una celda para añadir al presupuesto</p>
              </div>
            </div>
            
            {loading ? (
              <div className="flex justify-center py-8">
                <RefreshCw size={32} className="animate-spin text-purple-500" />
              </div>
            ) : availableHeights.length > 0 ? (
              <div className="bg-white rounded-lg border border-purple-200 overflow-hidden">
                <div className="bg-purple-900 text-white px-3 py-1.5 flex items-center justify-between">
                  <span className="text-[10px] font-bold">
                    <Calculator size={12} className="inline mr-1" />
                    {selectedCollection}
                  </span>
                  <span className="text-[9px] text-purple-300">
                    {availableHeights.length}×{availableWidths.length} combinaciones
                  </span>
                </div>
                <div className="overflow-auto max-h-[350px]">
                  <table className="w-full text-[9px]">
                    <thead className="bg-purple-100 sticky top-0 z-10">
                      <tr>
                        <th className="p-1.5 text-purple-800 font-black sticky left-0 bg-purple-100 z-20 min-w-[55px]">
                          <div className="flex items-center gap-0.5">
                            <Ruler size={10} />
                            AL↓/AN→
                          </div>
                        </th>
                        {availableWidths.map(w => (
                          <th key={w} className="p-1 text-center text-purple-700 font-bold min-w-[50px]">
                            {w}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {availableHeights.map(h => (
                        <tr key={h} className="border-t border-purple-50 hover:bg-purple-50/50">
                          <td className="p-1.5 font-bold text-purple-700 bg-purple-50 sticky left-0 z-10">
                            {h}
                          </td>
                          {availableWidths.map(w => {
                            const cell = priceMatrix[h]?.[w];
                            return (
                              <td 
                                key={`${h}-${w}`} 
                                className={`p-1 text-center cursor-pointer transition-all ${
                                  cell 
                                    ? 'hover:bg-orange-100 hover:shadow-inner'
                                    : 'bg-slate-50 cursor-not-allowed'
                                }`}
                                onClick={() => cell && addItemFromMatrix(h, w)}
                                title={cell ? `${h}×${w}mm = ${cell.price.toFixed(2)}€` : 'No disponible'}
                              >
                                {cell ? (
                                  <span className="font-bold text-slate-700 hover:text-orange-600">
                                    {cell.price.toFixed(2)}€
                                  </span>
                                ) : (
                                  <span className="text-slate-300">-</span>
                                )}
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ) : (
              <div className="text-center py-8">
                <Package size={40} className="mx-auto text-slate-300 mb-2" />
                <p className="text-sm text-slate-400">No hay precios para esta selección</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default DespieceStepByStep;
