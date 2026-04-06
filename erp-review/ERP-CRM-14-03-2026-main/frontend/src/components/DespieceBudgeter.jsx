/**
 * DespieceBudgeter.jsx
 * Presupuestador de tableros y materiales de despiece
 * Permite seleccionar fabricante, colección, color, acabado y calcular presupuestos
 */
import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { 
  X, Search, Plus, Trash2, Save, Printer, Download, Filter, 
  Package, Palette, Layers, Box, ChevronDown, ChevronUp,
  AlertCircle, CheckCircle, Loader, Hash, User, FileText,
  Calculator, Ruler, Grid, Settings, RefreshCw
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const DespieceBudgeter = ({ isOpen, onClose, currentUser, onBudgetSaved }) => {
  // Estados de filtros
  const [filters, setFilters] = useState({
    manufacturer: '',
    collection: '',
    color: '',
    finish: '',
    thickness: '',
    search: ''
  });
  
  // Opciones de filtros disponibles
  const [filterOptions, setFilterOptions] = useState({
    manufacturers: [],
    collections: [],
    finishes: [],
    thicknesses: [],
    colors: []
  });
  
  // Productos del catálogo
  const [products, setProducts] = useState([]);
  const [loadingProducts, setLoadingProducts] = useState(false);
  
  // Items del presupuesto
  const [budgetItems, setBudgetItems] = useState([]);
  
  // Datos del presupuesto
  const [budgetData, setBudgetData] = useState({
    budgetNumber: '',
    customerName: '',
    customerAddress: '',
    projectRef: ''
  });
  
  // Estado del panel
  const [showFilters, setShowFilters] = useState(true);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [addItemModal, setAddItemModal] = useState(false);
  const [newItem, setNewItem] = useState({
    width: 600,
    height: 800,
    quantity: 1,
    cantoL1: false,
    cantoL2: false,
    cantoW1: false,
    cantoW2: false,
    notes: ''
  });
  
  // Cargar opciones de filtros
  useEffect(() => {
    if (isOpen) {
      loadFilterOptions();
      loadProducts();
    }
  }, [isOpen]);
  
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
    setLoadingProducts(true);
    try {
      const params = new URLSearchParams();
      if (filters.manufacturer) params.append('manufacturer', filters.manufacturer);
      if (filters.collection) params.append('collection', filters.collection);
      if (filters.color) params.append('color', filters.color);
      if (filters.finish) params.append('finish', filters.finish);
      if (filters.thickness) params.append('thickness', filters.thickness);
      if (filters.search) params.append('search', filters.search);
      
      const response = await fetch(`${API_URL}/api/despiece-budgeter/products?${params.toString()}`);
      const data = await response.json();
      setProducts(data);
    } catch (error) {
      console.error('Error loading products:', error);
      setProducts([]);
    } finally {
      setLoadingProducts(false);
    }
  };
  
  // Recargar productos cuando cambian los filtros
  useEffect(() => {
    if (isOpen) {
      const debounce = setTimeout(() => {
        loadProducts();
      }, 300);
      return () => clearTimeout(debounce);
    }
  }, [filters, isOpen]);
  
  // Inicializar datos con productos de muestra
  const seedProducts = async () => {
    try {
      const response = await fetch(`${API_URL}/api/despiece-budgeter/seed-alvic`, {
        method: 'POST'
      });
      const data = await response.json();
      alert(`✅ ${data.message}\nCreados: ${data.created}\nActualizados: ${data.updated}`);
      loadProducts();
      loadFilterOptions();
    } catch (error) {
      console.error('Error seeding products:', error);
      alert('Error al cargar productos de muestra');
    }
  };
  
  // Calcular precio de un item
  const calculateItemPrice = useCallback((item) => {
    const product = products.find(p => p.id === item.productId);
    if (!product) return { areaM2: 0, unitPrice: 0, totalPrice: 0 };
    
    // Calcular área en m2
    const areaM2 = (item.width / 1000) * (item.height / 1000);
    
    // Usar precio Z1 por defecto (se puede ajustar según zona del usuario)
    const pricePerM2 = product.priceZ1 || product.pricePerM2 || 0;
    
    // Precio base por área
    let unitPrice = areaM2 * pricePerM2;
    
    // Añadir coste de cantos
    const cantoCount = [item.cantoL1, item.cantoL2, item.cantoW1, item.cantoW2].filter(Boolean).length;
    const cantoPricePerMeter = 2.5; // Precio aproximado por metro lineal de canto
    const perimeter = (item.width * 2 + item.height * 2) / 1000; // Perímetro en metros
    const cantoLength = (cantoCount / 4) * perimeter; // Metros de canto
    unitPrice += cantoLength * cantoPricePerMeter;
    
    const totalPrice = unitPrice * item.quantity;
    
    return { areaM2, unitPrice, totalPrice };
  }, [products]);
  
  // Añadir item al presupuesto
  const handleAddItem = () => {
    if (!selectedProduct) return;
    
    const prices = calculateItemPrice({
      ...newItem,
      productId: selectedProduct.id
    });
    
    const item = {
      id: `dbi-${Date.now()}`,
      productId: selectedProduct.id,
      productCode: selectedProduct.code,
      productName: selectedProduct.name,
      manufacturer: selectedProduct.manufacturer,
      color: selectedProduct.color,
      finish: selectedProduct.finish,
      thickness: selectedProduct.thickness,
      width: newItem.width,
      height: newItem.height,
      quantity: newItem.quantity,
      cantoL1: newItem.cantoL1,
      cantoL2: newItem.cantoL2,
      cantoW1: newItem.cantoW1,
      cantoW2: newItem.cantoW2,
      cantoType: '',
      areaM2: prices.areaM2,
      unitPrice: prices.unitPrice,
      totalPrice: prices.totalPrice,
      notes: newItem.notes
    };
    
    setBudgetItems(prev => [...prev, item]);
    setAddItemModal(false);
    setSelectedProduct(null);
    setNewItem({
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
  
  // Eliminar item
  const removeItem = (itemId) => {
    setBudgetItems(prev => prev.filter(item => item.id !== itemId));
  };
  
  // Actualizar item
  const updateItem = (itemId, field, value) => {
    setBudgetItems(prev => prev.map(item => {
      if (item.id !== itemId) return item;
      const updated = { ...item, [field]: value };
      const prices = calculateItemPrice(updated);
      return { ...updated, ...prices };
    }));
  };
  
  // Calcular totales
  const totals = useMemo(() => {
    const totalArea = budgetItems.reduce((sum, item) => sum + (item.areaM2 * item.quantity), 0);
    const totalPrice = budgetItems.reduce((sum, item) => sum + item.totalPrice, 0);
    return { totalArea, totalPrice };
  }, [budgetItems]);
  
  // Guardar presupuesto
  const saveBudget = async () => {
    if (budgetItems.length === 0) {
      alert('El presupuesto está vacío');
      return;
    }
    
    try {
      const budget = {
        ...budgetData,
        items: budgetItems,
        totalArea: totals.totalArea,
        totalPrice: totals.totalPrice,
        userId: currentUser?.id || ''
      };
      
      const response = await fetch(`${API_URL}/api/despiece-budgeter/budgets`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(budget)
      });
      
      const saved = await response.json();
      alert(`✅ Presupuesto guardado: ${saved.id}`);
      onBudgetSaved?.(saved);
    } catch (error) {
      console.error('Error saving budget:', error);
      alert('Error al guardar el presupuesto');
    }
  };
  
  // Limpiar filtros
  const clearFilters = () => {
    setFilters({
      manufacturer: '',
      collection: '',
      color: '',
      finish: '',
      thickness: '',
      search: ''
    });
  };
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-[9999] flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl shadow-2xl w-full max-w-7xl max-h-[95vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-900 to-indigo-900 text-white px-8 py-5 flex justify-between items-center shrink-0">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-orange-500 rounded-xl shadow-lg">
              <Layers size={24} />
            </div>
            <div>
              <h2 className="text-xl font-black uppercase tracking-wider">Presupuestador DESPIECE</h2>
              <p className="text-purple-300 text-xs font-medium mt-0.5">Tableros y Materiales de Corte</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={seedProducts}
              className="px-4 py-2 bg-purple-700 hover:bg-purple-600 rounded-lg text-xs font-bold uppercase tracking-wider flex items-center gap-2 transition-colors"
              title="Cargar productos de muestra"
            >
              <RefreshCw size={14} />
              Demo ALVIC
            </button>
            <button 
              onClick={onClose}
              className="p-2 hover:bg-white/10 rounded-xl transition-colors"
            >
              <X size={24} />
            </button>
          </div>
        </div>
        
        {/* Datos del presupuesto */}
        <div className="bg-purple-50 px-8 py-4 border-b border-purple-100 shrink-0">
          <div className="grid grid-cols-4 gap-4">
            <div className="flex items-center gap-2">
              <Hash size={16} className="text-purple-400" />
              <div className="flex-1">
                <label className="text-[9px] font-black text-purple-400 uppercase tracking-widest">Nº Expediente</label>
                <input
                  type="text"
                  value={budgetData.budgetNumber}
                  onChange={(e) => setBudgetData(prev => ({...prev, budgetNumber: e.target.value.toUpperCase()}))}
                  placeholder="EXP-0001"
                  className="w-full text-sm font-bold text-purple-900 bg-transparent outline-none border-b border-transparent hover:border-purple-200 focus:border-orange-500 uppercase"
                />
              </div>
            </div>
            <div className="flex items-center gap-2">
              <User size={16} className="text-purple-400" />
              <div className="flex-1">
                <label className="text-[9px] font-black text-purple-400 uppercase tracking-widest">Cliente</label>
                <input
                  type="text"
                  value={budgetData.customerName}
                  onChange={(e) => setBudgetData(prev => ({...prev, customerName: e.target.value.toUpperCase()}))}
                  placeholder="Nombre cliente..."
                  className="w-full text-sm font-bold text-purple-900 bg-transparent outline-none border-b border-transparent hover:border-purple-200 focus:border-orange-500 uppercase"
                />
              </div>
            </div>
            <div className="flex items-center gap-2">
              <FileText size={16} className="text-purple-400" />
              <div className="flex-1">
                <label className="text-[9px] font-black text-purple-400 uppercase tracking-widest">Referencia</label>
                <input
                  type="text"
                  value={budgetData.projectRef}
                  onChange={(e) => setBudgetData(prev => ({...prev, projectRef: e.target.value.toUpperCase()}))}
                  placeholder="REF-001"
                  className="w-full text-sm font-bold text-purple-900 bg-transparent outline-none border-b border-transparent hover:border-purple-200 focus:border-orange-500 uppercase"
                />
              </div>
            </div>
            <div className="flex items-center justify-end gap-2">
              <div className="text-right">
                <p className="text-[9px] font-black text-purple-400 uppercase tracking-widest">Total Presupuesto</p>
                <p className="text-2xl font-black text-orange-600">
                  {totals.totalPrice.toLocaleString('es-ES', { style: 'currency', currency: 'EUR' })}
                </p>
              </div>
            </div>
          </div>
        </div>
        
        {/* Content */}
        <div className="flex-1 flex overflow-hidden">
          {/* Panel izquierdo - Filtros y catálogo */}
          <div className="w-[400px] bg-slate-50 border-r border-slate-200 flex flex-col shrink-0">
            {/* Filtros */}
            <div className="p-4 border-b border-slate-200 bg-white">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-xs font-black text-slate-600 uppercase tracking-widest flex items-center gap-2">
                  <Filter size={14} />
                  Filtros
                </h3>
                <button 
                  onClick={clearFilters}
                  className="text-[10px] text-slate-400 hover:text-red-500 font-bold uppercase"
                >
                  Limpiar
                </button>
              </div>
              
              <div className="space-y-2">
                {/* Fabricante */}
                <select
                  value={filters.manufacturer}
                  onChange={(e) => setFilters(prev => ({...prev, manufacturer: e.target.value}))}
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs font-bold text-slate-700 outline-none focus:border-purple-500"
                >
                  <option value="">🏭 Todos los fabricantes</option>
                  {filterOptions.manufacturers.map(m => (
                    <option key={m} value={m}>{m}</option>
                  ))}
                </select>
                
                {/* Colección */}
                <select
                  value={filters.collection}
                  onChange={(e) => setFilters(prev => ({...prev, collection: e.target.value}))}
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs font-bold text-slate-700 outline-none focus:border-purple-500"
                >
                  <option value="">📦 Todas las colecciones</option>
                  {filterOptions.collections.map(c => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
                
                {/* Acabado */}
                <select
                  value={filters.finish}
                  onChange={(e) => setFilters(prev => ({...prev, finish: e.target.value}))}
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs font-bold text-slate-700 outline-none focus:border-purple-500"
                >
                  <option value="">✨ Todos los acabados</option>
                  {filterOptions.finishes.map(f => (
                    <option key={f} value={f}>{f}</option>
                  ))}
                </select>
                
                {/* Grosor */}
                <select
                  value={filters.thickness}
                  onChange={(e) => setFilters(prev => ({...prev, thickness: e.target.value}))}
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-xs font-bold text-slate-700 outline-none focus:border-purple-500"
                >
                  <option value="">📏 Todos los grosores</option>
                  {filterOptions.thicknesses.map(t => (
                    <option key={t} value={t}>{t} mm</option>
                  ))}
                </select>
                
                {/* Búsqueda */}
                <div className="relative">
                  <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input
                    type="text"
                    value={filters.search}
                    onChange={(e) => setFilters(prev => ({...prev, search: e.target.value}))}
                    placeholder="Buscar por código o color..."
                    className="w-full bg-slate-50 border border-slate-200 rounded-lg pl-9 pr-3 py-2 text-xs font-bold text-slate-700 outline-none focus:border-purple-500"
                  />
                </div>
              </div>
            </div>
            
            {/* Lista de productos */}
            <div className="flex-1 overflow-y-auto p-4">
              {loadingProducts ? (
                <div className="flex flex-col items-center justify-center py-12">
                  <Loader size={32} className="animate-spin text-purple-500 mb-3" />
                  <p className="text-xs text-slate-400 font-bold uppercase">Cargando productos...</p>
                </div>
              ) : products.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12">
                  <Package size={48} className="text-slate-300 mb-3" />
                  <p className="text-xs text-slate-400 font-bold uppercase">No hay productos</p>
                  <p className="text-[10px] text-slate-300 mt-1">Haz clic en "Demo ALVIC" para cargar datos</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {products.map(product => (
                    <button
                      key={product.id}
                      onClick={() => {
                        setSelectedProduct(product);
                        setAddItemModal(true);
                      }}
                      className="w-full bg-white border border-slate-200 rounded-xl p-3 text-left hover:border-purple-400 hover:shadow-md transition-all group"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <p className="text-xs font-black text-slate-800 uppercase">{product.code}</p>
                          <p className="text-[10px] text-slate-600 mt-0.5">{product.name}</p>
                          <div className="flex items-center gap-2 mt-1.5">
                            <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded text-[9px] font-bold">
                              {product.collection}
                            </span>
                            <span className="px-2 py-0.5 bg-slate-100 text-slate-600 rounded text-[9px] font-bold">
                              {product.finish}
                            </span>
                            <span className="px-2 py-0.5 bg-orange-100 text-orange-700 rounded text-[9px] font-bold">
                              {product.thickness}mm
                            </span>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-xs font-black text-purple-600">
                            {product.priceZ1?.toFixed(2)}€/m²
                          </p>
                          <Plus size={18} className="text-slate-300 group-hover:text-purple-500 mt-1 ml-auto transition-colors" />
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
          
          {/* Panel derecho - Presupuesto */}
          <div className="flex-1 flex flex-col overflow-hidden">
            {/* Cabecera tabla */}
            <div className="bg-purple-900 text-white px-6 py-3 flex items-center shrink-0">
              <div className="flex-1">
                <h3 className="text-xs font-black uppercase tracking-widest">Líneas del Presupuesto</h3>
              </div>
              <div className="flex items-center gap-4 text-xs font-bold">
                <span>{budgetItems.length} líneas</span>
                <span>{totals.totalArea.toFixed(2)} m²</span>
              </div>
            </div>
            
            {/* Tabla de items */}
            <div className="flex-1 overflow-y-auto">
              {budgetItems.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full py-20">
                  <Box size={64} className="text-slate-200 mb-4" />
                  <p className="text-sm font-black text-slate-400 uppercase tracking-widest">Presupuesto vacío</p>
                  <p className="text-xs text-slate-300 mt-2">Selecciona productos del catálogo para añadirlos</p>
                </div>
              ) : (
                <table className="w-full">
                  <thead className="bg-slate-100 text-slate-600 text-[10px] font-black uppercase sticky top-0">
                    <tr>
                      <th className="px-4 py-2 text-left">Producto</th>
                      <th className="px-2 py-2 text-center">Ancho</th>
                      <th className="px-2 py-2 text-center">Alto</th>
                      <th className="px-2 py-2 text-center">Cant.</th>
                      <th className="px-2 py-2 text-center">Cantos</th>
                      <th className="px-2 py-2 text-center">m²</th>
                      <th className="px-4 py-2 text-right">Precio</th>
                      <th className="px-2 py-2"></th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {budgetItems.map(item => (
                      <tr key={item.id} className="hover:bg-purple-50/50 transition-colors">
                        <td className="px-4 py-3">
                          <p className="text-xs font-black text-slate-800">{item.productCode}</p>
                          <p className="text-[10px] text-slate-500">{item.color} - {item.finish}</p>
                        </td>
                        <td className="px-2 py-3 text-center">
                          <input
                            type="number"
                            value={item.width}
                            onChange={(e) => updateItem(item.id, 'width', Number(e.target.value))}
                            className="w-16 bg-slate-50 border border-slate-200 rounded px-2 py-1 text-xs font-bold text-center outline-none focus:border-purple-500"
                          />
                        </td>
                        <td className="px-2 py-3 text-center">
                          <input
                            type="number"
                            value={item.height}
                            onChange={(e) => updateItem(item.id, 'height', Number(e.target.value))}
                            className="w-16 bg-slate-50 border border-slate-200 rounded px-2 py-1 text-xs font-bold text-center outline-none focus:border-purple-500"
                          />
                        </td>
                        <td className="px-2 py-3 text-center">
                          <input
                            type="number"
                            value={item.quantity}
                            min={1}
                            onChange={(e) => updateItem(item.id, 'quantity', Math.max(1, Number(e.target.value)))}
                            className="w-12 bg-slate-50 border border-slate-200 rounded px-2 py-1 text-xs font-bold text-center outline-none focus:border-purple-500"
                          />
                        </td>
                        <td className="px-2 py-3 text-center">
                          <div className="flex items-center justify-center gap-1">
                            {['L1', 'L2', 'W1', 'W2'].map(canto => (
                              <button
                                key={canto}
                                onClick={() => updateItem(item.id, `canto${canto}`, !item[`canto${canto}`])}
                                className={`w-5 h-5 rounded text-[8px] font-bold transition-colors ${
                                  item[`canto${canto}`] 
                                    ? 'bg-purple-600 text-white' 
                                    : 'bg-slate-200 text-slate-500 hover:bg-slate-300'
                                }`}
                              >
                                {canto[0]}
                              </button>
                            ))}
                          </div>
                        </td>
                        <td className="px-2 py-3 text-center text-xs font-bold text-slate-600">
                          {(item.areaM2 * item.quantity).toFixed(2)}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <p className="text-sm font-black text-purple-600">
                            {item.totalPrice.toFixed(2)}€
                          </p>
                        </td>
                        <td className="px-2 py-3">
                          <button
                            onClick={() => removeItem(item.id)}
                            className="p-1.5 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded transition-colors"
                          >
                            <Trash2 size={14} />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
            
            {/* Totales */}
            <div className="bg-gradient-to-r from-purple-900 to-indigo-900 text-white px-6 py-4 shrink-0">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-6">
                  <div>
                    <p className="text-[10px] text-purple-300 uppercase font-bold">Total Área</p>
                    <p className="text-xl font-black">{totals.totalArea.toFixed(2)} m²</p>
                  </div>
                  <div>
                    <p className="text-[10px] text-purple-300 uppercase font-bold">Líneas</p>
                    <p className="text-xl font-black">{budgetItems.length}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-[10px] text-purple-300 uppercase font-bold">Total Presupuesto</p>
                  <p className="text-3xl font-black text-orange-400">
                    {totals.totalPrice.toLocaleString('es-ES', { style: 'currency', currency: 'EUR' })}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        {/* Footer */}
        <div className="bg-slate-100 px-8 py-4 flex justify-between items-center border-t border-slate-200 shrink-0">
          <p className="text-xs text-slate-400 font-medium">
            Presupuestador de Tableros y Materiales
          </p>
          <div className="flex gap-3">
            <button
              onClick={() => window.print()}
              className="bg-white border border-slate-200 text-slate-600 px-5 py-2.5 rounded-xl font-bold text-xs uppercase tracking-widest flex items-center gap-2 hover:bg-slate-50 transition-colors"
            >
              <Printer size={16} />
              Imprimir
            </button>
            <button
              onClick={saveBudget}
              disabled={budgetItems.length === 0}
              className="bg-purple-600 text-white px-6 py-2.5 rounded-xl font-bold text-xs uppercase tracking-widest flex items-center gap-2 hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Save size={16} />
              Guardar
            </button>
            <button
              onClick={onClose}
              className="bg-slate-600 text-white px-6 py-2.5 rounded-xl font-bold text-xs uppercase tracking-widest hover:bg-slate-700 transition-colors"
            >
              Cerrar
            </button>
          </div>
        </div>
      </div>
      
      {/* Modal para añadir item */}
      {addItemModal && selectedProduct && (
        <div className="fixed inset-0 bg-black/50 z-[10000] flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden">
            <div className="bg-purple-900 text-white px-6 py-4 flex items-center justify-between">
              <h3 className="font-black uppercase text-sm">Añadir Pieza</h3>
              <button onClick={() => setAddItemModal(false)} className="p-1 hover:bg-white/10 rounded">
                <X size={20} />
              </button>
            </div>
            
            <div className="p-6 space-y-4">
              {/* Info del producto */}
              <div className="bg-purple-50 rounded-xl p-4">
                <p className="text-xs font-black text-purple-800 uppercase">{selectedProduct.code}</p>
                <p className="text-sm text-purple-600 mt-1">{selectedProduct.name}</p>
                <div className="flex gap-2 mt-2">
                  <span className="px-2 py-1 bg-purple-200 text-purple-700 rounded text-[10px] font-bold">
                    {selectedProduct.collection}
                  </span>
                  <span className="px-2 py-1 bg-orange-200 text-orange-700 rounded text-[10px] font-bold">
                    {selectedProduct.priceZ1?.toFixed(2)}€/m²
                  </span>
                </div>
              </div>
              
              {/* Dimensiones */}
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="text-[10px] font-black text-slate-500 uppercase">Ancho (mm)</label>
                  <input
                    type="number"
                    value={newItem.width}
                    onChange={(e) => setNewItem(prev => ({...prev, width: Number(e.target.value)}))}
                    className="w-full mt-1 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm font-bold outline-none focus:border-purple-500"
                  />
                </div>
                <div>
                  <label className="text-[10px] font-black text-slate-500 uppercase">Alto (mm)</label>
                  <input
                    type="number"
                    value={newItem.height}
                    onChange={(e) => setNewItem(prev => ({...prev, height: Number(e.target.value)}))}
                    className="w-full mt-1 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm font-bold outline-none focus:border-purple-500"
                  />
                </div>
                <div>
                  <label className="text-[10px] font-black text-slate-500 uppercase">Cantidad</label>
                  <input
                    type="number"
                    value={newItem.quantity}
                    min={1}
                    onChange={(e) => setNewItem(prev => ({...prev, quantity: Math.max(1, Number(e.target.value))}))}
                    className="w-full mt-1 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm font-bold outline-none focus:border-purple-500"
                  />
                </div>
              </div>
              
              {/* Cantos */}
              <div>
                <label className="text-[10px] font-black text-slate-500 uppercase">Cantos</label>
                <div className="grid grid-cols-4 gap-2 mt-2">
                  {[
                    { key: 'cantoL1', label: 'Largo 1' },
                    { key: 'cantoL2', label: 'Largo 2' },
                    { key: 'cantoW1', label: 'Ancho 1' },
                    { key: 'cantoW2', label: 'Ancho 2' }
                  ].map(canto => (
                    <button
                      key={canto.key}
                      onClick={() => setNewItem(prev => ({...prev, [canto.key]: !prev[canto.key]}))}
                      className={`p-2 rounded-lg text-[10px] font-bold transition-colors ${
                        newItem[canto.key]
                          ? 'bg-purple-600 text-white'
                          : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                      }`}
                    >
                      {canto.label}
                    </button>
                  ))}
                </div>
              </div>
              
              {/* Notas */}
              <div>
                <label className="text-[10px] font-black text-slate-500 uppercase">Notas</label>
                <input
                  type="text"
                  value={newItem.notes}
                  onChange={(e) => setNewItem(prev => ({...prev, notes: e.target.value}))}
                  placeholder="Notas opcionales..."
                  className="w-full mt-1 bg-slate-50 border border-slate-200 rounded-lg px-3 py-2 text-sm outline-none focus:border-purple-500"
                />
              </div>
            </div>
            
            <div className="bg-slate-50 px-6 py-4 flex justify-end gap-3">
              <button
                onClick={() => setAddItemModal(false)}
                className="px-4 py-2 bg-slate-200 text-slate-700 rounded-lg text-xs font-bold uppercase hover:bg-slate-300 transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={handleAddItem}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg text-xs font-bold uppercase hover:bg-purple-700 transition-colors flex items-center gap-2"
              >
                <Plus size={14} />
                Añadir
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DespieceBudgeter;
