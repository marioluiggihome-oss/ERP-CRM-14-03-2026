/**
 * DespieceCatalog.jsx
 * Catálogo de tableros y materiales de despiece refactorizado
 * Incluye tabla de precios por dimensiones tipo VIFORMING/ALVIC
 */
import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { 
  Search, Plus, Trash2, Package, Factory, Palette, Layers, Box,
  ChevronDown, ChevronUp, Filter, X, Grid, List, Calculator,
  Ruler, Square, RefreshCw, Download, ArrowUpDown, Check
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Dimensiones estándar comunes (en mm)
const STANDARD_WIDTHS = [300, 400, 450, 500, 600, 700, 800, 900, 1000, 1200];
const STANDARD_HEIGHTS = [300, 400, 500, 600, 700, 720, 800, 900, 1000, 1200, 1400, 1600, 1800, 2000, 2200];

const DespieceCatalog = ({ 
  onAddProduct, 
  budgetItems = [],
  onRemoveItem,
  onUpdateItem,
  isExpanded = true
}) => {
  // Estados de productos y filtros
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filterOptions, setFilterOptions] = useState({
    manufacturers: [],
    collections: [],
    finishes: [],
    thicknesses: [],
    colors: [],
    categories: []
  });
  
  const [filters, setFilters] = useState({
    manufacturer: '',
    collection: '',
    finish: '',
    thickness: '',
    color: '',
    category: '',
    search: ''
  });
  
  // Vista y ordenación
  const [viewMode, setViewMode] = useState('table'); // 'table' | 'grid' | 'matrix'
  const [sortBy, setSortBy] = useState('code');
  const [sortDir, setSortDir] = useState('asc');
  
  // Producto seleccionado para vista de matriz de precios
  const [selectedProduct, setSelectedProduct] = useState(null);
  
  // Modal de añadir
  const [addModal, setAddModal] = useState({
    isOpen: false,
    product: null,
    width: 600,
    height: 800,
    quantity: 1,
    cantoL1: false,
    cantoL2: false,
    cantoW1: false,
    cantoW2: false,
    notes: ''
  });

  // Cargar datos iniciales
  useEffect(() => {
    loadFilterOptions();
    loadProducts();
  }, []);

  // Recargar productos cuando cambien los filtros
  useEffect(() => {
    const debounce = setTimeout(() => {
      loadProducts();
    }, 300);
    return () => clearTimeout(debounce);
  }, [filters]);

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
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.append(key, value);
      });
      
      const response = await fetch(`${API_URL}/api/despiece-budgeter/products?${params.toString()}`);
      const data = await response.json();
      setProducts(data);
    } catch (error) {
      console.error('Error loading products:', error);
      setProducts([]);
    } finally {
      setLoading(false);
    }
  };

  // Productos ordenados
  const sortedProducts = useMemo(() => {
    return [...products].sort((a, b) => {
      let aVal = a[sortBy] || '';
      let bVal = b[sortBy] || '';
      if (typeof aVal === 'string') aVal = aVal.toLowerCase();
      if (typeof bVal === 'string') bVal = bVal.toLowerCase();
      if (sortDir === 'asc') return aVal > bVal ? 1 : -1;
      return aVal < bVal ? 1 : -1;
    });
  }, [products, sortBy, sortDir]);

  // Calcular precio de una pieza
  const calculatePrice = useCallback((product, width, height, quantity = 1, cantos = {}) => {
    const areaM2 = (width / 1000) * (height / 1000);
    const pricePerM2 = product?.priceZ1 || 0;
    let basePrice = areaM2 * pricePerM2;
    
    // Coste de cantos (precio por metro lineal)
    const cantoCount = [cantos.cantoL1, cantos.cantoL2, cantos.cantoW1, cantos.cantoW2].filter(Boolean).length;
    if (cantoCount > 0) {
      const cantoPricePerMeter = 2.5; // €/ml
      const cantoLength = ((cantoCount >= 2 ? width * 2 : width) + (cantoCount >= 2 ? height * 2 : height)) / 1000 / 2;
      basePrice += cantoLength * cantoPricePerMeter;
    }
    
    return {
      areaM2,
      unitPrice: basePrice,
      totalPrice: basePrice * quantity
    };
  }, []);

  // Abrir modal de añadir
  const openAddModal = (product) => {
    setAddModal({
      isOpen: true,
      product: product,
      width: 600,
      height: 800,
      quantity: 1,
      cantoL1: false,
      cantoL2: false,
      cantoW1: false,
      cantoW2: false,
      notes: ''
    });
  };

  // Confirmar añadir producto
  const handleAddProduct = () => {
    if (!addModal.product) return;
    
    const prices = calculatePrice(
      addModal.product,
      addModal.width,
      addModal.height,
      addModal.quantity,
      {
        cantoL1: addModal.cantoL1,
        cantoL2: addModal.cantoL2,
        cantoW1: addModal.cantoW1,
        cantoW2: addModal.cantoW2
      }
    );
    
    const item = {
      id: `dp-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      productId: addModal.product.id,
      code: addModal.product.code,
      name: addModal.product.name,
      manufacturer: addModal.product.manufacturer,
      collection: addModal.product.collection,
      color: addModal.product.color,
      finish: addModal.product.finish,
      thickness: addModal.product.thickness,
      width: addModal.width,
      height: addModal.height,
      quantity: addModal.quantity,
      cantoL1: addModal.cantoL1,
      cantoL2: addModal.cantoL2,
      cantoW1: addModal.cantoW1,
      cantoW2: addModal.cantoW2,
      ...prices,
      notes: addModal.notes,
      isDespiece: true
    };
    
    onAddProduct?.(item);
    setAddModal(prev => ({ ...prev, isOpen: false, product: null }));
  };

  // Añadir rápido desde matriz
  const handleQuickAdd = (product, width, height) => {
    const prices = calculatePrice(product, width, height, 1, {});
    const item = {
      id: `dp-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      productId: product.id,
      code: product.code,
      name: product.name,
      manufacturer: product.manufacturer,
      collection: product.collection,
      color: product.color,
      finish: product.finish,
      thickness: product.thickness,
      width: width,
      height: height,
      quantity: 1,
      ...prices,
      isDespiece: true
    };
    onAddProduct?.(item);
  };

  // Limpiar filtros
  const clearFilters = () => {
    setFilters({
      manufacturer: '',
      collection: '',
      finish: '',
      thickness: '',
      color: '',
      category: '',
      search: ''
    });
  };

  // Toggle ordenación
  const toggleSort = (column) => {
    if (sortBy === column) {
      setSortDir(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortDir('asc');
    }
  };

  // Totales del presupuesto
  const budgetTotals = useMemo(() => {
    const totalArea = budgetItems.reduce((sum, item) => sum + (item.areaM2 * item.quantity), 0);
    const totalPrice = budgetItems.reduce((sum, item) => sum + item.totalPrice, 0);
    return { totalArea, totalPrice, itemCount: budgetItems.length };
  }, [budgetItems]);

  if (!isExpanded) return null;

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header con filtros */}
      <div className="bg-gradient-to-r from-purple-900 to-indigo-900 px-4 py-3 shrink-0">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-orange-500 rounded-lg">
              <Package size={18} className="text-white" />
            </div>
            <div>
              <h3 className="text-sm font-black text-white uppercase tracking-wider">
                Catálogo Tableros
              </h3>
              <p className="text-[10px] text-purple-300">
                {products.length} productos | {budgetTotals.itemCount} en presupuesto
              </p>
            </div>
          </div>
          
          {/* Controles de vista */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setViewMode('table')}
              className={`p-2 rounded-lg transition-colors ${viewMode === 'table' ? 'bg-white/20 text-white' : 'text-purple-300 hover:text-white'}`}
              title="Vista tabla"
            >
              <List size={16} />
            </button>
            <button
              onClick={() => setViewMode('grid')}
              className={`p-2 rounded-lg transition-colors ${viewMode === 'grid' ? 'bg-white/20 text-white' : 'text-purple-300 hover:text-white'}`}
              title="Vista cuadrícula"
            >
              <Grid size={16} />
            </button>
            <button
              onClick={() => setViewMode('matrix')}
              className={`p-2 rounded-lg transition-colors ${viewMode === 'matrix' ? 'bg-white/20 text-white' : 'text-purple-300 hover:text-white'}`}
              title="Matriz de precios"
            >
              <Calculator size={16} />
            </button>
          </div>
        </div>
        
        {/* Filtros */}
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <select 
            value={filters.manufacturer} 
            onChange={e => setFilters(prev => ({...prev, manufacturer: e.target.value}))} 
            className="bg-white/10 backdrop-blur border border-white/20 rounded-lg py-1.5 px-3 text-[10px] font-bold uppercase text-white outline-none focus:border-orange-400"
          >
            <option value="" className="text-slate-900">🏭 FABRICANTE</option>
            {filterOptions.manufacturers.map(m => <option key={m} value={m} className="text-slate-900">{m}</option>)}
          </select>
          
          <select 
            value={filters.collection} 
            onChange={e => setFilters(prev => ({...prev, collection: e.target.value}))} 
            className="bg-white/10 backdrop-blur border border-white/20 rounded-lg py-1.5 px-3 text-[10px] font-bold uppercase text-white outline-none focus:border-orange-400"
          >
            <option value="" className="text-slate-900">📦 COLECCIÓN</option>
            {filterOptions.collections.map(c => <option key={c} value={c} className="text-slate-900">{c}</option>)}
          </select>
          
          <select 
            value={filters.finish} 
            onChange={e => setFilters(prev => ({...prev, finish: e.target.value}))} 
            className="bg-white/10 backdrop-blur border border-white/20 rounded-lg py-1.5 px-3 text-[10px] font-bold uppercase text-white outline-none focus:border-orange-400"
          >
            <option value="" className="text-slate-900">✨ ACABADO</option>
            {filterOptions.finishes.map(f => <option key={f} value={f} className="text-slate-900">{f}</option>)}
          </select>
          
          <select 
            value={filters.thickness} 
            onChange={e => setFilters(prev => ({...prev, thickness: e.target.value}))} 
            className="bg-white/10 backdrop-blur border border-white/20 rounded-lg py-1.5 px-3 text-[10px] font-bold uppercase text-white outline-none focus:border-orange-400"
          >
            <option value="" className="text-slate-900">📏 GROSOR</option>
            {filterOptions.thicknesses.map(t => <option key={t} value={t} className="text-slate-900">{t}mm</option>)}
          </select>
          
          <div className="relative flex-1 min-w-[150px] max-w-[250px]">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-purple-300" />
            <input
              type="text"
              value={filters.search}
              onChange={e => setFilters(prev => ({...prev, search: e.target.value}))}
              placeholder="Buscar código o color..."
              className="w-full bg-white/10 backdrop-blur border border-white/20 rounded-lg pl-9 pr-8 py-1.5 text-[10px] font-bold text-white outline-none placeholder-purple-300 focus:border-orange-400"
            />
            {filters.search && (
              <button 
                onClick={() => setFilters(prev => ({...prev, search: ''}))}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-purple-300 hover:text-white"
              >
                <X size={12} />
              </button>
            )}
          </div>
          
          {Object.values(filters).some(v => v) && (
            <button 
              onClick={clearFilters}
              className="p-1.5 bg-red-500/20 hover:bg-red-500/40 rounded-lg text-red-300 transition-colors"
              title="Limpiar filtros"
            >
              <X size={14} />
            </button>
          )}
        </div>
      </div>
      
      {/* Contenido principal */}
      <div className="flex-1 flex overflow-hidden">
        {/* Panel izquierdo - Catálogo */}
        <div className="flex-1 overflow-y-auto">
          {loading ? (
            <div className="flex flex-col items-center justify-center h-full py-20">
              <RefreshCw size={40} className="animate-spin text-purple-400 mb-4" />
              <p className="text-sm font-bold text-purple-400">Cargando productos...</p>
            </div>
          ) : products.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full py-20">
              <Package size={64} className="text-slate-200 mb-4" />
              <p className="text-sm font-bold text-slate-400">No hay productos</p>
              <p className="text-xs text-slate-300 mt-1">Ajusta los filtros o carga datos</p>
            </div>
          ) : viewMode === 'table' ? (
            /* VISTA TABLA */
            <table className="w-full text-left">
              <thead className="bg-purple-100 text-purple-900 text-[10px] font-black uppercase sticky top-0 z-10">
                <tr>
                  <th className="p-2 pl-3 cursor-pointer hover:bg-purple-200" onClick={() => toggleSort('code')}>
                    CÓDIGO {sortBy === 'code' && (sortDir === 'asc' ? '↑' : '↓')}
                  </th>
                  <th className="p-2 cursor-pointer hover:bg-purple-200" onClick={() => toggleSort('name')}>
                    PRODUCTO {sortBy === 'name' && (sortDir === 'asc' ? '↑' : '↓')}
                  </th>
                  <th className="p-2 cursor-pointer hover:bg-purple-200" onClick={() => toggleSort('collection')}>
                    COLECCIÓN {sortBy === 'collection' && (sortDir === 'asc' ? '↑' : '↓')}
                  </th>
                  <th className="p-2">COLOR</th>
                  <th className="p-2">ACABADO</th>
                  <th className="p-2 text-center">mm</th>
                  <th className="p-2 text-right cursor-pointer hover:bg-purple-200" onClick={() => toggleSort('priceZ1')}>
                    €/m² {sortBy === 'priceZ1' && (sortDir === 'asc' ? '↑' : '↓')}
                  </th>
                  <th className="p-2 w-[60px]"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-purple-50">
                {sortedProducts.map(product => (
                  <tr 
                    key={product.id} 
                    className="hover:bg-purple-50 cursor-pointer transition-colors group"
                    onClick={() => openAddModal(product)}
                  >
                    <td className="p-2 pl-3">
                      <span className="text-[11px] font-black text-purple-800">{product.code}</span>
                    </td>
                    <td className="p-2">
                      <span className="text-[10px] font-bold text-slate-700">{product.name}</span>
                    </td>
                    <td className="p-2">
                      <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded text-[9px] font-bold">
                        {product.collection}
                      </span>
                    </td>
                    <td className="p-2">
                      <span className="text-[10px] font-bold text-slate-600">{product.color}</span>
                    </td>
                    <td className="p-2">
                      <span className="text-[9px] text-slate-500">{product.finish}</span>
                    </td>
                    <td className="p-2 text-center">
                      <span className="text-[10px] font-bold text-slate-700">{product.thickness}</span>
                    </td>
                    <td className="p-2 text-right">
                      <span className="text-[11px] font-black text-orange-600">
                        {product.priceZ1?.toFixed(2)}€
                      </span>
                    </td>
                    <td className="p-2">
                      <div className="flex items-center gap-1">
                        <button
                          onClick={(e) => { e.stopPropagation(); setSelectedProduct(product); setViewMode('matrix'); }}
                          className="p-1 text-slate-300 hover:text-purple-600 rounded transition-colors"
                          title="Ver matriz de precios"
                        >
                          <Calculator size={14} />
                        </button>
                        <Plus size={16} className="text-slate-300 group-hover:text-purple-600 transition-colors" />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : viewMode === 'grid' ? (
            /* VISTA CUADRÍCULA */
            <div className="p-4 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
              {sortedProducts.map(product => (
                <div 
                  key={product.id}
                  onClick={() => openAddModal(product)}
                  className="bg-white border-2 border-purple-100 rounded-xl p-3 hover:border-purple-400 hover:shadow-lg cursor-pointer transition-all group"
                >
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-[10px] font-black text-purple-800">{product.code}</span>
                    <span className="px-2 py-0.5 bg-orange-100 text-orange-700 rounded text-[9px] font-bold">
                      {product.priceZ1?.toFixed(2)}€/m²
                    </span>
                  </div>
                  <p className="text-[10px] font-bold text-slate-700 mb-2">{product.name}</p>
                  <div className="flex flex-wrap gap-1">
                    <span className="px-1.5 py-0.5 bg-purple-50 text-purple-600 rounded text-[8px] font-bold">{product.collection}</span>
                    <span className="px-1.5 py-0.5 bg-slate-50 text-slate-500 rounded text-[8px] font-bold">{product.finish}</span>
                    <span className="px-1.5 py-0.5 bg-slate-50 text-slate-500 rounded text-[8px] font-bold">{product.thickness}mm</span>
                  </div>
                  <div className="mt-2 flex items-center justify-between">
                    <span className="text-[9px] text-slate-500">{product.color}</span>
                    <Plus size={14} className="text-slate-300 group-hover:text-purple-600 transition-colors" />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            /* VISTA MATRIZ DE PRECIOS */
            <div className="p-4">
              {selectedProduct ? (
                <div>
                  {/* Info del producto seleccionado */}
                  <div className="bg-gradient-to-r from-purple-100 to-purple-50 rounded-xl p-4 mb-4 border border-purple-200">
                    <div className="flex justify-between items-start">
                      <div>
                        <h4 className="text-sm font-black text-purple-800">{selectedProduct.code}</h4>
                        <p className="text-xs text-purple-600">{selectedProduct.name}</p>
                        <div className="flex gap-2 mt-2">
                          <span className="px-2 py-0.5 bg-purple-200 text-purple-700 rounded text-[9px] font-bold">{selectedProduct.collection}</span>
                          <span className="px-2 py-0.5 bg-slate-200 text-slate-600 rounded text-[9px] font-bold">{selectedProduct.color}</span>
                          <span className="px-2 py-0.5 bg-slate-200 text-slate-600 rounded text-[9px] font-bold">{selectedProduct.finish}</span>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-2xl font-black text-orange-600">{selectedProduct.priceZ1?.toFixed(2)}€</p>
                        <p className="text-[10px] text-slate-500">por m²</p>
                      </div>
                    </div>
                  </div>
                  
                  {/* Matriz de precios Alto x Ancho */}
                  <div className="bg-white rounded-xl border border-purple-200 overflow-hidden">
                    <div className="bg-purple-900 text-white px-4 py-2">
                      <h5 className="text-[10px] font-black uppercase tracking-wider">
                        Matriz de Precios (Alto × Ancho) - Click para añadir
                      </h5>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full text-[9px]">
                        <thead className="bg-purple-100">
                          <tr>
                            <th className="p-2 text-purple-800 font-black sticky left-0 bg-purple-100 z-10">
                              <div className="flex items-center gap-1">
                                <Ruler size={12} />
                                Alto↓ / Ancho→
                              </div>
                            </th>
                            {STANDARD_WIDTHS.map(w => (
                              <th key={w} className="p-2 text-center text-purple-700 font-bold min-w-[60px]">
                                {w}mm
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {STANDARD_HEIGHTS.map(h => (
                            <tr key={h} className="border-t border-purple-50">
                              <td className="p-2 font-bold text-purple-700 bg-purple-50 sticky left-0 z-10">
                                {h}mm
                              </td>
                              {STANDARD_WIDTHS.map(w => {
                                const price = calculatePrice(selectedProduct, w, h, 1, {});
                                return (
                                  <td 
                                    key={`${h}-${w}`} 
                                    className="p-1 text-center hover:bg-orange-100 cursor-pointer transition-colors group"
                                    onClick={() => handleQuickAdd(selectedProduct, w, h)}
                                    title={`${w}×${h}mm = ${price.areaM2.toFixed(3)}m² → Click para añadir`}
                                  >
                                    <div className="flex flex-col items-center">
                                      <span className="font-bold text-slate-700 group-hover:text-orange-600">
                                        {price.unitPrice.toFixed(2)}€
                                      </span>
                                      <span className="text-[7px] text-slate-400">
                                        {price.areaM2.toFixed(2)}m²
                                      </span>
                                    </div>
                                  </td>
                                );
                              })}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                  
                  <button
                    onClick={() => setSelectedProduct(null)}
                    className="mt-4 px-4 py-2 bg-slate-100 hover:bg-slate-200 rounded-lg text-xs font-bold text-slate-600 transition-colors"
                  >
                    ← Volver al listado
                  </button>
                </div>
              ) : (
                <div className="text-center py-20">
                  <Calculator size={48} className="mx-auto text-slate-300 mb-4" />
                  <p className="text-sm font-bold text-slate-400">Selecciona un producto</p>
                  <p className="text-xs text-slate-300 mt-1">Haz clic en el icono de calculadora junto a un producto</p>
                </div>
              )}
            </div>
          )}
        </div>
        
        {/* Panel derecho - Presupuesto */}
        {budgetItems.length > 0 && (
          <div className="w-[320px] bg-slate-50 border-l border-slate-200 flex flex-col shrink-0">
            <div className="bg-purple-800 text-white px-4 py-3 shrink-0">
              <h4 className="text-[10px] font-black uppercase tracking-wider">
                Presupuesto Despiece
              </h4>
              <p className="text-purple-300 text-[9px]">
                {budgetTotals.itemCount} líneas | {budgetTotals.totalArea.toFixed(2)}m²
              </p>
            </div>
            
            <div className="flex-1 overflow-y-auto p-2 space-y-2">
              {budgetItems.map(item => (
                <div key={item.id} className="bg-white rounded-lg p-2 border border-slate-200 shadow-sm">
                  <div className="flex justify-between items-start mb-1">
                    <div>
                      <p className="text-[10px] font-black text-purple-800">{item.code}</p>
                      <p className="text-[9px] text-slate-500">{item.color}</p>
                    </div>
                    <button
                      onClick={() => onRemoveItem?.(item.id)}
                      className="p-1 text-slate-300 hover:text-red-500 transition-colors"
                    >
                      <Trash2 size={12} />
                    </button>
                  </div>
                  <div className="flex items-center gap-2 text-[9px]">
                    <span className="px-1.5 py-0.5 bg-slate-100 rounded font-bold">
                      {item.width}×{item.height}
                    </span>
                    <span className="text-slate-400">×</span>
                    <input
                      type="number"
                      value={item.quantity}
                      onChange={(e) => onUpdateItem?.(item.id, 'quantity', Math.max(1, parseInt(e.target.value) || 1))}
                      className="w-10 bg-slate-100 rounded px-1 py-0.5 text-center font-bold outline-none"
                      min={1}
                    />
                    <span className="text-slate-400">=</span>
                    <span className="font-black text-orange-600">{item.totalPrice.toFixed(2)}€</span>
                  </div>
                </div>
              ))}
            </div>
            
            <div className="bg-gradient-to-r from-purple-900 to-indigo-900 text-white px-4 py-3 shrink-0">
              <div className="flex justify-between items-center">
                <div>
                  <p className="text-[9px] text-purple-300 uppercase">Total</p>
                  <p className="text-[9px] text-purple-300">{budgetTotals.totalArea.toFixed(2)} m²</p>
                </div>
                <p className="text-xl font-black text-orange-400">
                  {budgetTotals.totalPrice.toFixed(2)}€
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
      
      {/* Modal de añadir producto */}
      {addModal.isOpen && addModal.product && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[9999] p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden">
            <div className="bg-gradient-to-r from-purple-800 to-purple-900 text-white px-6 py-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Package size={24} />
                <h2 className="text-base font-black uppercase tracking-wider">Añadir Tablero</h2>
              </div>
              <button 
                onClick={() => setAddModal(prev => ({...prev, isOpen: false, product: null}))}
                className="p-1 hover:bg-white/20 rounded-lg transition-colors"
              >
                <X size={20} />
              </button>
            </div>
            
            <div className="p-6 space-y-4">
              {/* Info del producto */}
              <div className="bg-purple-50 rounded-xl p-4 border border-purple-200">
                <div className="flex justify-between items-start">
                  <div>
                    <p className="text-xs font-black text-purple-800 uppercase">{addModal.product.code}</p>
                    <p className="text-sm font-bold text-purple-600 mt-1">{addModal.product.name}</p>
                  </div>
                  <span className="px-3 py-1 bg-orange-100 text-orange-700 rounded-lg text-sm font-black">
                    {addModal.product.priceZ1?.toFixed(2)}€/m²
                  </span>
                </div>
                <div className="flex flex-wrap gap-2 mt-3">
                  <span className="px-2 py-1 bg-purple-200 text-purple-700 rounded text-[10px] font-bold">
                    {addModal.product.collection}
                  </span>
                  <span className="px-2 py-1 bg-slate-200 text-slate-700 rounded text-[10px] font-bold">
                    {addModal.product.color}
                  </span>
                  <span className="px-2 py-1 bg-slate-200 text-slate-700 rounded text-[10px] font-bold">
                    {addModal.product.finish}
                  </span>
                  <span className="px-2 py-1 bg-slate-200 text-slate-700 rounded text-[10px] font-bold">
                    {addModal.product.thickness}mm
                  </span>
                </div>
              </div>
              
              {/* Dimensiones */}
              <div>
                <label className="text-[10px] font-black text-slate-500 uppercase mb-2 block">
                  Dimensiones de la pieza
                </label>
                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <label className="text-[9px] font-bold text-slate-400 uppercase">Ancho (mm)</label>
                    <input
                      type="number"
                      value={addModal.width}
                      onChange={(e) => setAddModal(prev => ({...prev, width: Number(e.target.value)}))}
                      className="w-full mt-1 bg-slate-50 border-2 border-slate-200 rounded-lg px-3 py-2.5 text-sm font-bold outline-none focus:border-purple-500"
                    />
                  </div>
                  <div>
                    <label className="text-[9px] font-bold text-slate-400 uppercase">Alto (mm)</label>
                    <input
                      type="number"
                      value={addModal.height}
                      onChange={(e) => setAddModal(prev => ({...prev, height: Number(e.target.value)}))}
                      className="w-full mt-1 bg-slate-50 border-2 border-slate-200 rounded-lg px-3 py-2.5 text-sm font-bold outline-none focus:border-purple-500"
                    />
                  </div>
                  <div>
                    <label className="text-[9px] font-bold text-slate-400 uppercase">Cantidad</label>
                    <input
                      type="number"
                      value={addModal.quantity}
                      min={1}
                      onChange={(e) => setAddModal(prev => ({...prev, quantity: Math.max(1, Number(e.target.value))}))}
                      className="w-full mt-1 bg-slate-50 border-2 border-slate-200 rounded-lg px-3 py-2.5 text-sm font-bold outline-none focus:border-purple-500"
                    />
                  </div>
                </div>
              </div>
              
              {/* Cantos */}
              <div>
                <label className="text-[10px] font-black text-slate-500 uppercase mb-2 block">
                  Cantos (opcional)
                </label>
                <div className="grid grid-cols-4 gap-2">
                  {[
                    { key: 'cantoL1', label: 'Largo 1' },
                    { key: 'cantoL2', label: 'Largo 2' },
                    { key: 'cantoW1', label: 'Ancho 1' },
                    { key: 'cantoW2', label: 'Ancho 2' }
                  ].map(canto => (
                    <button
                      key={canto.key}
                      onClick={() => setAddModal(prev => ({...prev, [canto.key]: !prev[canto.key]}))}
                      className={`p-2 rounded-lg text-[10px] font-bold transition-all flex items-center justify-center gap-1 ${
                        addModal[canto.key]
                          ? 'bg-purple-600 text-white shadow-md'
                          : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                      }`}
                    >
                      {addModal[canto.key] && <Check size={12} />}
                      {canto.label}
                    </button>
                  ))}
                </div>
              </div>
              
              {/* Notas */}
              <div>
                <label className="text-[10px] font-black text-slate-500 uppercase mb-2 block">
                  Notas (opcional)
                </label>
                <input
                  type="text"
                  value={addModal.notes}
                  onChange={(e) => setAddModal(prev => ({...prev, notes: e.target.value}))}
                  placeholder="Instrucciones especiales..."
                  className="w-full bg-slate-50 border-2 border-slate-200 rounded-lg px-3 py-2 text-sm outline-none focus:border-purple-500"
                />
              </div>
              
              {/* Preview de cálculo */}
              <div className="bg-gradient-to-r from-purple-100 to-purple-50 rounded-xl p-4 border border-purple-200">
                <div className="flex justify-between items-center">
                  <div>
                    <p className="text-[9px] text-purple-500 uppercase font-bold">Área calculada</p>
                    <p className="text-lg font-black text-purple-700">
                      {((addModal.width / 1000) * (addModal.height / 1000) * addModal.quantity).toFixed(3)} m²
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-[9px] text-purple-500 uppercase font-bold">Precio estimado</p>
                    <p className="text-2xl font-black text-orange-600">
                      {calculatePrice(addModal.product, addModal.width, addModal.height, addModal.quantity, {
                        cantoL1: addModal.cantoL1,
                        cantoL2: addModal.cantoL2,
                        cantoW1: addModal.cantoW1,
                        cantoW2: addModal.cantoW2
                      }).totalPrice.toFixed(2)}€
                    </p>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="bg-slate-50 px-6 py-4 flex justify-end gap-3 border-t border-slate-200">
              <button
                onClick={() => setAddModal(prev => ({...prev, isOpen: false, product: null}))}
                className="px-5 py-2.5 bg-slate-200 text-slate-700 rounded-xl text-xs font-bold uppercase hover:bg-slate-300 transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={handleAddProduct}
                className="px-5 py-2.5 bg-purple-600 text-white rounded-xl text-xs font-bold uppercase hover:bg-purple-700 transition-colors flex items-center gap-2"
              >
                <Plus size={16} />
                Añadir al Presupuesto
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DespieceCatalog;
