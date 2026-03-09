/**
 * DespieceStepByStep.jsx
 * Flujo simplificado: Categoría → Colección → Matriz de Precios
 */
import React, { useState, useEffect, useMemo } from 'react';
import { 
  Factory, Box, Ruler, ChevronRight, Check, Plus,
  Package, Calculator, RefreshCw, ArrowLeft
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const DespieceStepByStep = ({ onAddItems }) => {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  
  const [selectedCategory, setSelectedCategory] = useState('PUERTA');
  const [selectedCollection, setSelectedCollection] = useState('');
  
  const [collections, setCollections] = useState([]);
  const [products, setProducts] = useState([]);
  const [priceMatrix, setPriceMatrix] = useState({});

  // Cargar colecciones según categoría
  useEffect(() => {
    loadCollections();
  }, [selectedCategory]);
  
  // Cargar productos cuando se selecciona colección
  useEffect(() => {
    console.log('Collection changed:', selectedCollection);
    if (selectedCollection) {
      loadProducts(selectedCollection);
    }
  }, [selectedCollection]);
  
  const loadCollections = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/despiece-budgeter/products/filters?manufacturer=ALVIC`);
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
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const loadProducts = async (collection) => {
    setLoading(true);
    setPriceMatrix({});
    setProducts([]);
    
    try {
      const params = new URLSearchParams();
      params.append('manufacturer', 'ALVIC');
      params.append('collection', collection);
      params.append('limit', '3000');
      
      const url = `${API_URL}/api/despiece-budgeter/products?${params.toString()}`;
      console.log('Fetching:', url);
      
      const response = await fetch(url);
      
      if (!response.ok) {
        console.error('Response not ok:', response.status);
        return;
      }
      
      const data = await response.json();
      console.log('Products loaded:', data.length);
      setProducts(data);
      
      // Construir matriz Alto x Ancho
      const matrix = {};
      data.forEach(p => {
        const h = p.height || 0;
        const w = p.width || 0;
        const price = p.priceZ1 || p.price || 0;
        if (h > 0 && w > 0 && price > 0) {
          if (!matrix[h]) matrix[h] = {};
          matrix[h][w] = { price, product: p };
        }
      });
      console.log('Matrix heights:', Object.keys(matrix).length);
      setPriceMatrix(matrix);
    } catch (error) {
      console.error('Error loading products:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const heights = useMemo(() => Object.keys(priceMatrix).map(Number).sort((a,b) => a-b), [priceMatrix]);
  const widths = useMemo(() => {
    const w = new Set();
    Object.values(priceMatrix).forEach(row => Object.keys(row).forEach(k => w.add(Number(k))));
    return [...w].sort((a,b) => a-b);
  }, [priceMatrix]);
  
  const addItem = (height, width) => {
    const cell = priceMatrix[height]?.[width];
    if (!cell) return;
    
    onAddItems?.([{
      id: `dp-${Date.now()}-${Math.random().toString(36).substr(2,6)}`,
      code: `ALVIC-${selectedCollection.substring(0,8).replace(/\s/g,'')}-${height}x${width}`,
      name: `${selectedCategory} ${selectedCollection}`,
      manufacturer: 'ALVIC',
      collection: selectedCollection,
      category: selectedCategory,
      height, width,
      thickness: 18,
      depth: 18,
      quantity: 1,
      unitPrice: cell.price,
      totalPrice: cell.price,
      isDespiece: true,
      editable: true
    }]);
  };
  
  const goBack = () => {
    if (step === 2) {
      setStep(1);
      setSelectedCollection('');
      setPriceMatrix({});
    }
  };

  return (
    <div className="h-full flex flex-col bg-slate-50">
      {/* Header */}
      <div className="bg-purple-800 text-white px-3 py-2 shrink-0">
        <div className="flex items-center gap-2 text-xs">
          <span className={`px-2 py-1 rounded ${step >= 1 ? 'bg-orange-500' : 'bg-white/20'}`}>
            {selectedCategory}
          </span>
          {selectedCollection && (
            <>
              <ChevronRight size={12} />
              <span className="px-2 py-1 rounded bg-green-500 truncate max-w-[150px]">
                {selectedCollection}
              </span>
            </>
          )}
        </div>
      </div>
      
      {/* Content */}
      <div className="flex-1 overflow-y-auto p-3">
        {/* STEP 1: Seleccionar Colección */}
        {step === 1 && (
          <div className="space-y-3">
            {/* Categorías */}
            <div className="flex gap-2 justify-center">
              {['PUERTA', 'TIRADOR'].map(cat => (
                <button
                  key={cat}
                  onClick={() => { setSelectedCategory(cat); setSelectedCollection(''); }}
                  className={`px-3 py-1.5 rounded-lg font-bold text-xs ${
                    selectedCategory === cat ? 'bg-purple-600 text-white' : 'bg-white text-purple-700 border'
                  }`}
                >
                  {cat === 'PUERTA' ? 'Puertas' : 'Tiradores'}
                </button>
              ))}
            </div>
            
            <h3 className="text-xs font-black text-center text-slate-600 uppercase">Selecciona Modelo</h3>
            
            {loading ? (
              <div className="flex justify-center py-6">
                <RefreshCw size={24} className="animate-spin text-purple-500" />
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-1.5">
                {collections.map(col => (
                  <button
                    key={col}
                    onClick={() => { setSelectedCollection(col); setStep(2); }}
                    className="p-2 rounded-lg bg-white border border-slate-200 hover:border-purple-500 hover:bg-purple-50 text-left flex items-center gap-2"
                  >
                    <Box size={14} className="text-purple-600 shrink-0" />
                    <span className="text-[11px] font-bold text-slate-700 truncate">{col}</span>
                    <ChevronRight size={12} className="text-slate-400 ml-auto shrink-0" />
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
        
        {/* STEP 2: Matriz de Precios */}
        {step === 2 && (
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <button onClick={goBack} className="p-1.5 bg-slate-200 rounded-lg hover:bg-slate-300">
                <ArrowLeft size={14} />
              </button>
              <span className="text-xs font-black text-slate-600">MATRIZ DE PRECIOS</span>
            </div>
            
            {loading ? (
              <div className="flex justify-center py-6">
                <RefreshCw size={24} className="animate-spin text-purple-500" />
              </div>
            ) : heights.length > 0 ? (
              <div className="bg-white rounded-lg border overflow-hidden">
                <div className="bg-purple-900 text-white px-2 py-1 text-[9px] font-bold">
                  <Calculator size={10} className="inline mr-1" />
                  {selectedCollection} ({heights.length}×{widths.length})
                </div>
                <div className="overflow-auto max-h-[300px]">
                  <table className="w-full text-[8px]">
                    <thead className="bg-purple-100 sticky top-0">
                      <tr>
                        <th className="p-1 text-purple-800 font-black sticky left-0 bg-purple-100 z-10 min-w-[45px]">
                          <Ruler size={8} className="inline" /> AL/AN
                        </th>
                        {widths.map(w => (
                          <th key={w} className="p-1 text-center text-purple-700 font-bold min-w-[42px]">{w}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {heights.map(h => (
                        <tr key={h} className="border-t border-purple-50 hover:bg-purple-50/30">
                          <td className="p-1 font-bold text-purple-700 bg-purple-50 sticky left-0">{h}</td>
                          {widths.map(w => {
                            const cell = priceMatrix[h]?.[w];
                            return (
                              <td 
                                key={`${h}-${w}`}
                                onClick={() => cell && addItem(h, w)}
                                className={`p-0.5 text-center cursor-pointer transition-colors ${
                                  cell ? 'hover:bg-orange-200' : 'bg-slate-100 cursor-not-allowed'
                                }`}
                                title={cell ? `${h}×${w}mm = ${cell.price.toFixed(2)}€` : ''}
                              >
                                {cell ? (
                                  <span className="font-bold text-slate-700">{cell.price.toFixed(2)}</span>
                                ) : '-'}
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
              <div className="text-center py-6">
                <Package size={32} className="mx-auto text-slate-300 mb-2" />
                <p className="text-xs text-slate-400">Sin precios disponibles</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default DespieceStepByStep;
