/**
 * DespieceWizard.jsx
 * Presupuestador de DESPIECE con flujo paso a paso
 * Según especificaciones del documento: Fabricante → Modelo → Color → Medidas → Tiradores
 */
import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { 
  Factory, Palette, Box, Ruler, Plus, X, ChevronRight, ChevronLeft,
  Check, Save, Package, Grid, Calculator, Trash2, RefreshCw
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Dimensiones estándar para la matriz
const STANDARD_WIDTHS = [156, 196, 246, 296, 346, 396, 446, 496, 596, 696, 796, 896, 996, 1096, 1196];
const STANDARD_HEIGHTS = [296, 396, 496, 596, 696, 796, 896, 996, 1096, 1196, 1296, 1396, 1496, 1596, 1696, 1796, 1896, 1996, 2096, 2196];

const DespieceWizard = ({ 
  isOpen, 
  onClose, 
  onAddItems,
  currentUser 
}) => {
  // Estado del wizard
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  
  // Selecciones del usuario
  const [selectedManufacturer, setSelectedManufacturer] = useState('');
  const [selectedCollection, setSelectedCollection] = useState('');
  const [selectedColor, setSelectedColor] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('PUERTA');
  
  // Opciones disponibles
  const [filterOptions, setFilterOptions] = useState({
    manufacturers: [],
    collections: [],
    colors: [],
    categories: []
  });
  
  // Productos y matriz de precios
  const [products, setProducts] = useState([]);
  const [priceMatrix, setPriceMatrix] = useState({});
  
  // Items seleccionados para el presupuesto
  const [selectedItems, setSelectedItems] = useState([]);
  
  // Cargar opciones iniciales
  useEffect(() => {
    if (isOpen) {
      loadFilterOptions();
    }
  }, [isOpen]);
  
  // Cargar productos cuando cambian las selecciones
  useEffect(() => {
    if (selectedManufacturer && selectedCollection) {
      loadProducts();
    }
  }, [selectedManufacturer, selectedCollection, selectedCategory]);
  
  const loadFilterOptions = async () => {
    try {
      const response = await fetch(`${API_URL}/api/despiece-budgeter/products/filters`);
      const data = await response.json();
      setFilterOptions(data);
    } catch (error) {
      console.error('Error loading filter options:', error);
    }
  };
  
  const loadProducts = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (selectedManufacturer) params.append('manufacturer', selectedManufacturer);
      if (selectedCollection) params.append('collection', selectedCollection);
      if (selectedCategory) params.append('category', selectedCategory);
      
      const response = await fetch(`${API_URL}/api/despiece-budgeter/products?${params.toString()}&limit=2000`);
      const data = await response.json();
      setProducts(data);
      
      // Construir matriz de precios
      const matrix = {};
      data.forEach(p => {
        const h = p.height || 0;
        const w = p.width || 0;
        if (h && w) {
          if (!matrix[h]) matrix[h] = {};
          matrix[h][w] = {
            price: p.priceZ1 || 0,
            product: p
          };
        }
      });
      setPriceMatrix(matrix);
      
      // Extraer colores únicos
      const uniqueColors = [...new Set(data.map(p => p.color).filter(Boolean))];
      setFilterOptions(prev => ({ ...prev, colors: uniqueColors }));
      
    } catch (error) {
      console.error('Error loading products:', error);
      setProducts([]);
    } finally {
      setLoading(false);
    }
  };
  
  // Filtrar colecciones por fabricante
  const availableCollections = useMemo(() => {
    if (!selectedManufacturer) return filterOptions.collections;
    // Filtrar colecciones que tengan productos del fabricante seleccionado
    return filterOptions.collections;
  }, [selectedManufacturer, filterOptions.collections]);
  
  // Obtener alturas y anchos disponibles en la matriz
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
      id: `dw-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      productId: cell.product.id,
      code: cell.product.code,
      name: cell.product.name,
      manufacturer: selectedManufacturer,
      collection: selectedCollection,
      color: selectedColor || cell.product.color,
      finish: cell.product.finish,
      category: selectedCategory,
      height: height,
      width: width,
      thickness: cell.product.thickness || 18,
      quantity: 1,
      unitPrice: cell.price,
      totalPrice: cell.price,
      areaM2: (height / 1000) * (width / 1000)
    };
    
    setSelectedItems(prev => [...prev, item]);
  };
  
  // Actualizar cantidad de un item
  const updateItemQuantity = (itemId, quantity) => {
    setSelectedItems(prev => prev.map(item => {
      if (item.id !== itemId) return item;
      return {
        ...item,
        quantity: Math.max(1, quantity),
        totalPrice: item.unitPrice * Math.max(1, quantity)
      };
    }));
  };
  
  // Eliminar item
  const removeItem = (itemId) => {
    setSelectedItems(prev => prev.filter(item => item.id !== itemId));
  };
  
  // Calcular totales
  const totals = useMemo(() => {
    const totalItems = selectedItems.length;
    const totalQuantity = selectedItems.reduce((sum, item) => sum + item.quantity, 0);
    const totalPrice = selectedItems.reduce((sum, item) => sum + item.totalPrice, 0);
    return { totalItems, totalQuantity, totalPrice };
  }, [selectedItems]);
  
  // Finalizar y enviar items
  const handleFinish = () => {
    if (selectedItems.length > 0) {
      onAddItems?.(selectedItems);
      setSelectedItems([]);
      setStep(1);
      setSelectedManufacturer('');
      setSelectedCollection('');
      setSelectedColor('');
      onClose?.();
    }
  };
  
  // Resetear wizard
  const handleReset = () => {
    setStep(1);
    setSelectedManufacturer('');
    setSelectedCollection('');
    setSelectedColor('');
    setSelectedItems([]);
    setProducts([]);
    setPriceMatrix({});
  };
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-[9999] flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl shadow-2xl w-full max-w-6xl max-h-[95vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-900 to-indigo-900 text-white px-8 py-5 shrink-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-orange-500 rounded-xl shadow-lg">
                <Package size={24} />
              </div>
              <div>
                <h2 className="text-xl font-black uppercase tracking-wider">Presupuestador DESPIECE</h2>
                <p className="text-purple-300 text-xs font-medium mt-0.5">
                  {selectedCategory === 'PUERTA' ? 'Puertas' : selectedCategory === 'COSTADO' ? 'Costados' : 'Regletas'}
                  {selectedManufacturer && ` • ${selectedManufacturer}`}
                  {selectedCollection && ` • ${selectedCollection}`}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={handleReset}
                className="px-4 py-2 bg-purple-700 hover:bg-purple-600 rounded-lg text-xs font-bold uppercase tracking-wider flex items-center gap-2 transition-colors"
              >
                <RefreshCw size={14} />
                Reiniciar
              </button>
              <button 
                onClick={onClose}
                className="p-2 hover:bg-white/10 rounded-xl transition-colors"
              >
                <X size={24} />
              </button>
            </div>
          </div>
          
          {/* Progress Steps */}
          <div className="flex items-center justify-center gap-2 mt-4">
            {[
              { num: 1, label: 'Fabricante', icon: Factory },
              { num: 2, label: 'Modelo', icon: Box },
              { num: 3, label: 'Color', icon: Palette },
              { num: 4, label: 'Medidas', icon: Ruler }
            ].map((s, idx) => (
              <React.Fragment key={s.num}>
                <button
                  onClick={() => s.num <= step && setStep(s.num)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-xl transition-all ${
                    step === s.num 
                      ? 'bg-orange-500 text-white shadow-lg' 
                      : step > s.num 
                        ? 'bg-white/20 text-white cursor-pointer hover:bg-white/30' 
                        : 'bg-white/10 text-purple-300 cursor-not-allowed'
                  }`}
                  disabled={s.num > step}
                >
                  <s.icon size={16} />
                  <span className="text-xs font-bold uppercase">{s.label}</span>
                  {step > s.num && <Check size={14} className="text-green-400" />}
                </button>
                {idx < 3 && <ChevronRight size={16} className="text-purple-400" />}
              </React.Fragment>
            ))}
          </div>
        </div>
        
        {/* Content */}
        <div className="flex-1 flex overflow-hidden">
          {/* Main Content */}
          <div className="flex-1 overflow-y-auto p-6">
            {/* Step 1: Fabricante */}
            {step === 1 && (
              <div className="space-y-6">
                <div className="text-center mb-8">
                  <h3 className="text-2xl font-black text-slate-800 uppercase tracking-wider">Selecciona Fabricante</h3>
                  <p className="text-slate-500 mt-2">Elige el fabricante del material de despiece</p>
                </div>
                
                {/* Categoría de producto */}
                <div className="flex justify-center gap-3 mb-6">
                  {[
                    { value: 'PUERTA', label: 'Puertas' },
                    { value: 'COSTADO', label: 'Costados' },
                    { value: 'REGLETA', label: 'Regletas' }
                  ].map(cat => (
                    <button
                      key={cat.value}
                      onClick={() => setSelectedCategory(cat.value)}
                      className={`px-6 py-3 rounded-xl font-bold text-sm uppercase transition-all ${
                        selectedCategory === cat.value
                          ? 'bg-purple-600 text-white shadow-lg'
                          : 'bg-purple-100 text-purple-700 hover:bg-purple-200'
                      }`}
                    >
                      {cat.label}
                    </button>
                  ))}
                </div>
                
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {filterOptions.manufacturers.map(mfr => (
                    <button
                      key={mfr}
                      onClick={() => {
                        setSelectedManufacturer(mfr);
                        setStep(2);
                      }}
                      className={`p-6 rounded-2xl border-2 transition-all hover:shadow-lg ${
                        selectedManufacturer === mfr
                          ? 'border-orange-500 bg-orange-50'
                          : 'border-slate-200 bg-white hover:border-purple-400'
                      }`}
                    >
                      <Factory size={32} className="mx-auto text-purple-600 mb-3" />
                      <p className="text-lg font-black text-slate-800">{mfr}</p>
                    </button>
                  ))}
                </div>
              </div>
            )}
            
            {/* Step 2: Modelo/Colección */}
            {step === 2 && (
              <div className="space-y-6">
                <div className="text-center mb-8">
                  <h3 className="text-2xl font-black text-slate-800 uppercase tracking-wider">Selecciona Modelo</h3>
                  <p className="text-slate-500 mt-2">Elige el modelo de {selectedManufacturer}</p>
                </div>
                
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {availableCollections.map(col => (
                    <button
                      key={col}
                      onClick={() => {
                        setSelectedCollection(col);
                        setStep(3);
                      }}
                      className={`p-6 rounded-2xl border-2 transition-all hover:shadow-lg ${
                        selectedCollection === col
                          ? 'border-orange-500 bg-orange-50'
                          : 'border-slate-200 bg-white hover:border-purple-400'
                      }`}
                    >
                      <Box size={32} className="mx-auto text-purple-600 mb-3" />
                      <p className="text-lg font-black text-slate-800">{col}</p>
                    </button>
                  ))}
                </div>
                
                <div className="flex justify-start mt-6">
                  <button
                    onClick={() => setStep(1)}
                    className="px-4 py-2 bg-slate-200 hover:bg-slate-300 rounded-lg text-sm font-bold text-slate-600 flex items-center gap-2 transition-colors"
                  >
                    <ChevronLeft size={16} />
                    Volver
                  </button>
                </div>
              </div>
            )}
            
            {/* Step 3: Color */}
            {step === 3 && (
              <div className="space-y-6">
                <div className="text-center mb-8">
                  <h3 className="text-2xl font-black text-slate-800 uppercase tracking-wider">Selecciona Color</h3>
                  <p className="text-slate-500 mt-2">Elige el color para {selectedCollection}</p>
                </div>
                
                {loading ? (
                  <div className="flex justify-center py-12">
                    <RefreshCw size={40} className="animate-spin text-purple-500" />
                  </div>
                ) : (
                  <div className="grid grid-cols-3 md:grid-cols-5 gap-3">
                    {filterOptions.colors.length > 0 ? (
                      filterOptions.colors.map(color => (
                        <button
                          key={color}
                          onClick={() => {
                            setSelectedColor(color);
                            setStep(4);
                          }}
                          className={`p-4 rounded-xl border-2 transition-all hover:shadow-lg ${
                            selectedColor === color
                              ? 'border-orange-500 bg-orange-50'
                              : 'border-slate-200 bg-white hover:border-purple-400'
                          }`}
                        >
                          <Palette size={24} className="mx-auto text-purple-600 mb-2" />
                          <p className="text-sm font-bold text-slate-800 text-center">{color}</p>
                        </button>
                      ))
                    ) : (
                      <button
                        onClick={() => setStep(4)}
                        className="col-span-full p-6 rounded-xl border-2 border-slate-200 bg-white hover:border-purple-400 transition-all"
                      >
                        <p className="text-lg font-bold text-slate-600">Continuar sin seleccionar color específico</p>
                      </button>
                    )}
                  </div>
                )}
                
                <div className="flex justify-between mt-6">
                  <button
                    onClick={() => setStep(2)}
                    className="px-4 py-2 bg-slate-200 hover:bg-slate-300 rounded-lg text-sm font-bold text-slate-600 flex items-center gap-2 transition-colors"
                  >
                    <ChevronLeft size={16} />
                    Volver
                  </button>
                  <button
                    onClick={() => setStep(4)}
                    className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm font-bold flex items-center gap-2 transition-colors"
                  >
                    Saltar
                    <ChevronRight size={16} />
                  </button>
                </div>
              </div>
            )}
            
            {/* Step 4: Matriz de Medidas */}
            {step === 4 && (
              <div className="space-y-4">
                <div className="text-center mb-4">
                  <h3 className="text-xl font-black text-slate-800 uppercase tracking-wider">Matriz de Precios</h3>
                  <p className="text-slate-500 text-sm">Haz clic en una celda para añadir al presupuesto</p>
                </div>
                
                {loading ? (
                  <div className="flex justify-center py-12">
                    <RefreshCw size={40} className="animate-spin text-purple-500" />
                  </div>
                ) : availableHeights.length > 0 ? (
                  <div className="bg-white rounded-xl border border-purple-200 overflow-hidden">
                    <div className="bg-purple-900 text-white px-4 py-2 flex items-center justify-between">
                      <span className="text-xs font-black uppercase tracking-wider">
                        <Calculator size={14} className="inline mr-2" />
                        {selectedCategory} • {selectedCollection} {selectedColor && `• ${selectedColor}`}
                      </span>
                      <span className="text-xs text-purple-300">
                        Click = Añadir | {availableHeights.length} altos × {availableWidths.length} anchos
                      </span>
                    </div>
                    <div className="overflow-auto max-h-[400px]">
                      <table className="w-full text-[10px]">
                        <thead className="bg-purple-100 sticky top-0 z-10">
                          <tr>
                            <th className="p-2 text-purple-800 font-black sticky left-0 bg-purple-100 z-20 min-w-[70px]">
                              <div className="flex items-center gap-1">
                                <Ruler size={12} />
                                Alto↓/Ancho→
                              </div>
                            </th>
                            {availableWidths.map(w => (
                              <th key={w} className="p-2 text-center text-purple-700 font-bold min-w-[60px]">
                                {w}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {availableHeights.map(h => (
                            <tr key={h} className="border-t border-purple-50 hover:bg-purple-50/50">
                              <td className="p-2 font-bold text-purple-700 bg-purple-50 sticky left-0 z-10">
                                {h}
                              </td>
                              {availableWidths.map(w => {
                                const cell = priceMatrix[h]?.[w];
                                const isInCart = selectedItems.some(
                                  item => item.height === h && item.width === w
                                );
                                return (
                                  <td 
                                    key={`${h}-${w}`} 
                                    className={`p-1 text-center cursor-pointer transition-all ${
                                      cell 
                                        ? isInCart
                                          ? 'bg-green-100 hover:bg-green-200'
                                          : 'hover:bg-orange-100'
                                        : 'bg-slate-50 cursor-not-allowed'
                                    }`}
                                    onClick={() => cell && addItemFromMatrix(h, w)}
                                    title={cell ? `${h}×${w}mm = ${cell.price.toFixed(2)}€ - Click para añadir` : 'No disponible'}
                                  >
                                    {cell ? (
                                      <div className="flex flex-col items-center">
                                        <span className={`font-bold ${isInCart ? 'text-green-700' : 'text-slate-700'}`}>
                                          {cell.price.toFixed(2)}€
                                        </span>
                                        {isInCart && <Check size={10} className="text-green-600" />}
                                      </div>
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
                  <div className="text-center py-12">
                    <Package size={48} className="mx-auto text-slate-300 mb-4" />
                    <p className="text-slate-500">No hay productos con matriz de precios para esta selección</p>
                  </div>
                )}
                
                <div className="flex justify-between mt-4">
                  <button
                    onClick={() => setStep(3)}
                    className="px-4 py-2 bg-slate-200 hover:bg-slate-300 rounded-lg text-sm font-bold text-slate-600 flex items-center gap-2 transition-colors"
                  >
                    <ChevronLeft size={16} />
                    Volver
                  </button>
                </div>
              </div>
            )}
          </div>
          
          {/* Sidebar - Items seleccionados */}
          <div className="w-[300px] bg-slate-50 border-l border-slate-200 flex flex-col shrink-0">
            <div className="bg-purple-800 text-white px-4 py-3">
              <h4 className="text-xs font-black uppercase tracking-wider">
                Presupuesto ({totals.totalItems} líneas)
              </h4>
            </div>
            
            <div className="flex-1 overflow-y-auto p-3 space-y-2">
              {selectedItems.length === 0 ? (
                <div className="text-center py-8">
                  <Package size={32} className="mx-auto text-slate-300 mb-2" />
                  <p className="text-xs text-slate-400">Sin items seleccionados</p>
                </div>
              ) : (
                selectedItems.map(item => (
                  <div key={item.id} className="bg-white rounded-lg p-2 border border-slate-200 shadow-sm">
                    <div className="flex justify-between items-start mb-1">
                      <div>
                        <p className="text-[10px] font-black text-purple-800">{item.category}</p>
                        <p className="text-[9px] text-slate-500">{item.height}×{item.width}mm</p>
                      </div>
                      <button
                        onClick={() => removeItem(item.id)}
                        className="p-1 text-slate-300 hover:text-red-500 transition-colors"
                      >
                        <Trash2 size={12} />
                      </button>
                    </div>
                    <div className="flex items-center gap-2 text-[9px]">
                      <span className="text-slate-400">Cant:</span>
                      <input
                        type="number"
                        value={item.quantity}
                        onChange={(e) => updateItemQuantity(item.id, parseInt(e.target.value) || 1)}
                        className="w-12 bg-slate-100 rounded px-1 py-0.5 text-center font-bold outline-none"
                        min={1}
                      />
                      <span className="text-slate-400">×</span>
                      <span className="text-slate-600">{item.unitPrice.toFixed(2)}€</span>
                      <span className="text-slate-400">=</span>
                      <span className="font-black text-orange-600">{item.totalPrice.toFixed(2)}€</span>
                    </div>
                  </div>
                ))
              )}
            </div>
            
            {/* Totales */}
            <div className="bg-gradient-to-r from-purple-900 to-indigo-900 text-white px-4 py-3">
              <div className="flex justify-between items-center mb-2">
                <span className="text-[9px] text-purple-300 uppercase">Total</span>
                <span className="text-xl font-black text-orange-400">
                  {totals.totalPrice.toFixed(2)}€
                </span>
              </div>
              <button
                onClick={handleFinish}
                disabled={selectedItems.length === 0}
                className="w-full bg-orange-500 hover:bg-orange-600 disabled:bg-slate-600 disabled:cursor-not-allowed text-white py-2.5 rounded-xl font-black uppercase text-xs tracking-wider flex items-center justify-center gap-2 transition-colors"
              >
                <Save size={16} />
                Añadir al Presupuesto
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DespieceWizard;
