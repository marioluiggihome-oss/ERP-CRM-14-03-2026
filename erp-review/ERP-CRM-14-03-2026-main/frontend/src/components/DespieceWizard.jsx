/**
 * DespieceWizard.jsx
 * Presupuestador de DESPIECE con flujo paso a paso
 * Según especificaciones: Fabricante → Modelo → Medidas (con precio calculado)
 * Las medidas se pueden modificar después de añadir
 */
import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { 
  Factory, Palette, Box, Ruler, Plus, X, ChevronRight, ChevronLeft,
  Check, Save, Package, Grid, Calculator, Trash2, RefreshCw, Edit2
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

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
  const [selectedCategory, setSelectedCategory] = useState('PUERTA');
  
  // Opciones disponibles (dinámicas)
  const [manufacturers, setManufacturers] = useState([]);
  const [collections, setCollections] = useState([]);
  
  // Productos y matriz de precios
  const [products, setProducts] = useState([]);
  const [priceMatrix, setPriceMatrix] = useState({});
  
  // Items seleccionados para el presupuesto
  const [selectedItems, setSelectedItems] = useState([]);
  
  // Estado para edición de medidas
  const [editingItem, setEditingItem] = useState(null);
  const [editHeight, setEditHeight] = useState('');
  const [editWidth, setEditWidth] = useState('');

  // Cargar fabricantes iniciales
  useEffect(() => {
    if (isOpen) {
      loadManufacturers();
    }
  }, [isOpen]);
  
  // Cargar colecciones cuando cambia el fabricante
  useEffect(() => {
    if (selectedManufacturer) {
      loadCollections(selectedManufacturer);
    } else {
      setCollections([]);
    }
  }, [selectedManufacturer]);
  
  // Cargar productos cuando cambian las selecciones
  useEffect(() => {
    if (selectedManufacturer && selectedCollection) {
      loadProducts();
    }
  }, [selectedManufacturer, selectedCollection, selectedCategory]);
  
  const loadManufacturers = async () => {
    try {
      const response = await fetch(`${API_URL}/api/despiece-budgeter/products/filters`);
      const data = await response.json();
      setManufacturers(data.manufacturers || []);
    } catch (error) {
      console.error('Error loading manufacturers:', error);
    }
  };
  
  const loadCollections = async (manufacturer) => {
    try {
      const response = await fetch(`${API_URL}/api/despiece-budgeter/products/filters?manufacturer=${encodeURIComponent(manufacturer)}`);
      const data = await response.json();
      // Filtrar colecciones según categoría - excluir tiradores si seleccionamos PUERTA
      let cols = data.collections || [];
      if (selectedCategory === 'PUERTA') {
        cols = cols.filter(c => !c.toLowerCase().includes('tirador'));
      } else if (selectedCategory === 'TIRADOR') {
        cols = cols.filter(c => c.toLowerCase().includes('tirador'));
      }
      setCollections(cols);
    } catch (error) {
      console.error('Error loading collections:', error);
    }
  };
  
  const loadProducts = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('manufacturer', selectedManufacturer);
      params.append('collection', selectedCollection);
      if (selectedCategory) params.append('category', selectedCategory);
      params.append('limit', '3000');
      
      const response = await fetch(`${API_URL}/api/despiece-budgeter/products?${params.toString()}`);
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
            price: p.priceZ1 || p.price || 0,
            product: p
          };
        }
      });
      setPriceMatrix(matrix);
      
    } catch (error) {
      console.error('Error loading products:', error);
      setProducts([]);
    } finally {
      setLoading(false);
    }
  };
  
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
  
  // Función para encontrar el precio más cercano
  const findClosestPrice = (height, width) => {
    // Buscar precio exacto
    if (priceMatrix[height]?.[width]) {
      return priceMatrix[height][width].price;
    }
    
    // Buscar el precio más cercano
    let closestH = availableHeights.reduce((prev, curr) => 
      Math.abs(curr - height) < Math.abs(prev - height) ? curr : prev
    , availableHeights[0]);
    
    let closestW = availableWidths.reduce((prev, curr) => 
      Math.abs(curr - width) < Math.abs(prev - width) ? curr : prev
    , availableWidths[0]);
    
    if (priceMatrix[closestH]?.[closestW]) {
      return priceMatrix[closestH][closestW].price;
    }
    
    // Si no hay precio cercano, calcular por m²
    const anyProduct = products[0];
    if (anyProduct && anyProduct.pricePerM2) {
      const area = (height / 1000) * (width / 1000);
      return area * anyProduct.pricePerM2;
    }
    
    return 0;
  };
  
  // Añadir item desde la matriz
  const addItemFromMatrix = (height, width) => {
    const cell = priceMatrix[height]?.[width];
    if (!cell) return;
    
    const item = {
      id: `dw-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      productId: cell.product.id,
      code: cell.product.code,
      name: `${selectedCategory} ${selectedCollection} ${height}×${width}mm`,
      manufacturer: selectedManufacturer,
      collection: selectedCollection,
      color: cell.product.color || 'Estándar',
      finish: cell.product.finish || 'Estándar',
      category: selectedCategory,
      height: height,
      width: width,
      thickness: cell.product.thickness || 18,
      quantity: 1,
      unitPrice: cell.price,
      totalPrice: cell.price,
      areaM2: (height / 1000) * (width / 1000),
      editable: true
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
  
  // Iniciar edición de medidas
  const startEditingDimensions = (item) => {
    setEditingItem(item.id);
    setEditHeight(item.height.toString());
    setEditWidth(item.width.toString());
  };
  
  // Guardar medidas editadas
  const saveEditedDimensions = (itemId) => {
    const newHeight = parseInt(editHeight) || 0;
    const newWidth = parseInt(editWidth) || 0;
    
    if (newHeight <= 0 || newWidth <= 0) {
      alert('Las medidas deben ser mayores a 0');
      return;
    }
    
    // Calcular nuevo precio
    const newPrice = findClosestPrice(newHeight, newWidth);
    
    setSelectedItems(prev => prev.map(item => {
      if (item.id !== itemId) return item;
      return {
        ...item,
        height: newHeight,
        width: newWidth,
        name: `${item.category} ${item.collection} ${newHeight}×${newWidth}mm`,
        unitPrice: newPrice,
        totalPrice: newPrice * item.quantity,
        areaM2: (newHeight / 1000) * (newWidth / 1000)
      };
    }));
    
    setEditingItem(null);
    setEditHeight('');
    setEditWidth('');
  };
  
  // Cancelar edición
  const cancelEditing = () => {
    setEditingItem(null);
    setEditHeight('');
    setEditWidth('');
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
      onClose?.();
    }
  };
  
  // Resetear wizard
  const handleReset = () => {
    setStep(1);
    setSelectedManufacturer('');
    setSelectedCollection('');
    setSelectedItems([]);
    setProducts([]);
    setPriceMatrix({});
    setEditingItem(null);
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
                  {selectedCategory === 'PUERTA' ? 'Puertas' : selectedCategory === 'TIRADOR' ? 'Tiradores' : 'Costados/Regletas'}
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
              { num: 3, label: 'Medidas', icon: Ruler }
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
                {idx < 2 && <ChevronRight size={16} className="text-purple-400" />}
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
                    { value: 'TIRADOR', label: 'Tiradores' },
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
                  {manufacturers.map(mfr => (
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
                
                {loading ? (
                  <div className="flex justify-center py-12">
                    <RefreshCw size={40} className="animate-spin text-purple-500" />
                  </div>
                ) : collections.length > 0 ? (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {collections.map(col => (
                      <button
                        key={col}
                        onClick={() => {
                          setSelectedCollection(col);
                          setStep(3);
                        }}
                        className={`p-4 rounded-2xl border-2 transition-all hover:shadow-lg text-left ${
                          selectedCollection === col
                            ? 'border-orange-500 bg-orange-50'
                            : 'border-slate-200 bg-white hover:border-purple-400'
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <Box size={24} className="text-purple-600 shrink-0" />
                          <p className="text-sm font-bold text-slate-800">{col}</p>
                        </div>
                      </button>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <Package size={48} className="mx-auto text-slate-300 mb-4" />
                    <p className="text-slate-500">No hay modelos disponibles para {selectedManufacturer}</p>
                  </div>
                )}
                
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
            
            {/* Step 3: Matriz de Medidas */}
            {step === 3 && (
              <div className="space-y-4">
                <div className="text-center mb-4">
                  <h3 className="text-xl font-black text-slate-800 uppercase tracking-wider">Selecciona Medidas</h3>
                  <p className="text-slate-500 text-sm">Haz clic en una celda para añadir al presupuesto. Las medidas se pueden modificar después.</p>
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
                        {selectedCategory} • {selectedCollection}
                      </span>
                      <span className="text-xs text-purple-300">
                        {availableHeights.length} altos × {availableWidths.length} anchos | Click = Añadir
                      </span>
                    </div>
                    <div className="overflow-auto max-h-[400px]">
                      <table className="w-full text-[10px]">
                        <thead className="bg-purple-100 sticky top-0 z-10">
                          <tr>
                            <th className="p-2 text-purple-800 font-black sticky left-0 bg-purple-100 z-20 min-w-[70px]">
                              <div className="flex items-center gap-1">
                                <Ruler size={12} />
                                Alto↓ / Ancho→
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
                    <p className="text-slate-500">No hay precios disponibles para esta selección</p>
                    <p className="text-slate-400 text-sm mt-2">Selecciona otro modelo o fabricante</p>
                  </div>
                )}
                
                <div className="flex justify-between mt-4">
                  <button
                    onClick={() => setStep(2)}
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
          <div className="w-[320px] bg-slate-50 border-l border-slate-200 flex flex-col shrink-0">
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
                  <p className="text-[10px] text-slate-300 mt-1">Haz clic en la matriz para añadir</p>
                </div>
              ) : (
                selectedItems.map(item => (
                  <div key={item.id} className="bg-white rounded-lg p-3 border border-slate-200 shadow-sm">
                    {editingItem === item.id ? (
                      // Modo edición
                      <div className="space-y-2">
                        <p className="text-[10px] font-black text-purple-800">{item.category} - {item.collection}</p>
                        <div className="flex items-center gap-2">
                          <div className="flex-1">
                            <label className="text-[9px] text-slate-400">Alto (mm)</label>
                            <input
                              type="number"
                              value={editHeight}
                              onChange={(e) => setEditHeight(e.target.value)}
                              className="w-full bg-slate-100 rounded px-2 py-1 text-xs font-bold outline-none border border-purple-300 focus:border-purple-500"
                              min={1}
                            />
                          </div>
                          <span className="text-slate-400 mt-4">×</span>
                          <div className="flex-1">
                            <label className="text-[9px] text-slate-400">Ancho (mm)</label>
                            <input
                              type="number"
                              value={editWidth}
                              onChange={(e) => setEditWidth(e.target.value)}
                              className="w-full bg-slate-100 rounded px-2 py-1 text-xs font-bold outline-none border border-purple-300 focus:border-purple-500"
                              min={1}
                            />
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <button
                            onClick={() => saveEditedDimensions(item.id)}
                            className="flex-1 bg-green-500 hover:bg-green-600 text-white px-2 py-1 rounded text-[10px] font-bold flex items-center justify-center gap-1"
                          >
                            <Check size={12} />
                            Guardar
                          </button>
                          <button
                            onClick={cancelEditing}
                            className="flex-1 bg-slate-400 hover:bg-slate-500 text-white px-2 py-1 rounded text-[10px] font-bold flex items-center justify-center gap-1"
                          >
                            <X size={12} />
                            Cancelar
                          </button>
                        </div>
                      </div>
                    ) : (
                      // Modo visualización
                      <>
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <p className="text-[10px] font-black text-purple-800">{item.category}</p>
                            <p className="text-[9px] text-slate-500 truncate max-w-[180px]" title={item.collection}>
                              {item.collection}
                            </p>
                          </div>
                          <div className="flex gap-1">
                            <button
                              onClick={() => startEditingDimensions(item)}
                              className="p-1 text-slate-400 hover:text-blue-500 transition-colors"
                              title="Editar medidas"
                            >
                              <Edit2 size={12} />
                            </button>
                            <button
                              onClick={() => removeItem(item.id)}
                              className="p-1 text-slate-400 hover:text-red-500 transition-colors"
                              title="Eliminar"
                            >
                              <Trash2 size={12} />
                            </button>
                          </div>
                        </div>
                        
                        {/* Medidas destacadas */}
                        <div className="bg-purple-50 rounded-lg px-2 py-1 mb-2">
                          <div className="flex items-center justify-center gap-2 text-purple-700">
                            <Ruler size={12} />
                            <span className="font-black text-sm">{item.height} × {item.width} mm</span>
                          </div>
                        </div>
                        
                        <div className="flex items-center gap-2 text-[10px]">
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
                      </>
                    )}
                  </div>
                ))
              )}
            </div>
            
            {/* Totales */}
            <div className="bg-gradient-to-r from-purple-900 to-indigo-900 text-white px-4 py-3">
              <div className="flex justify-between items-center mb-2">
                <span className="text-[9px] text-purple-300 uppercase">Total ({totals.totalQuantity} uds)</span>
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
