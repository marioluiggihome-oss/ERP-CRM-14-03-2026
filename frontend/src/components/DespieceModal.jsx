import React, { useState, useEffect, useMemo } from 'react';
import { X, FileText, Layers, Scissors, Package, Download, Printer, ChevronDown, ChevronRight, Edit3, Save, AlertCircle, Loader, Box, Ruler } from 'lucide-react';
import { despieceAPI } from '../services/api';

const DespieceModal = ({ isOpen, onClose, items, catalogs, carcassMaterialName }) => {
  const [despieceData, setDespieceData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeView, setActiveView] = useState('montaje'); // 'montaje' or 'corte'
  const [expandedItems, setExpandedItems] = useState({});
  const [editingComponent, setEditingComponent] = useState(null);
  const [editedComponents, setEditedComponents] = useState({});

  // Get all products from catalogs
  const allProducts = useMemo(() => {
    return catalogs.flatMap(c => c.products.map(p => ({ ...p, catalogId: c.id })));
  }, [catalogs]);

  // Calculate despiece when modal opens
  useEffect(() => {
    if (isOpen && items.length > 0) {
      calculateDespiece();
    }
  }, [isOpen]);

  const calculateDespiece = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Prepare items for API
      const apiItems = items.filter(item => !item.isManual).map(item => {
        const product = allProducts.find(p => p.id === item.productId);
        return {
          productId: item.productId,
          productCode: item.customReference || product?.code || 'UNKNOWN',
          productName: product?.name || 'Producto Desconocido',
          width: item.customWidth,
          height: item.customHeight,
          depth: item.customDepth,
          quantity: item.quantity,
          category: product?.category || ''
        };
      });

      if (apiItems.length === 0) {
        setError('No hay muebles válidos para calcular el despiece');
        setLoading(false);
        return;
      }

      const result = await despieceAPI.calculate(
        apiItems,
        carcassMaterialName,
        "Tablero 3mm",
        18
      );
      
      setDespieceData(result);
      
      // Expand all items by default
      const expanded = {};
      result.items.forEach(item => {
        expanded[item.productId] = true;
      });
      setExpandedItems(expanded);
      
    } catch (err) {
      console.error('Despiece error:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const toggleExpand = (productId) => {
    setExpandedItems(prev => ({
      ...prev,
      [productId]: !prev[productId]
    }));
  };

  const handleEditComponent = (productId, componentId, field, value) => {
    const key = `${productId}-${componentId}`;
    setEditedComponents(prev => ({
      ...prev,
      [key]: {
        ...(prev[key] || {}),
        [field]: value
      }
    }));
  };

  const getComponentValue = (productId, component, field) => {
    const key = `${productId}-${component.id}`;
    if (editedComponents[key] && editedComponents[key][field] !== undefined) {
      return editedComponents[key][field];
    }
    return component[field];
  };

  const handlePrint = () => {
    window.print();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-[9999] flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl shadow-2xl w-full max-w-6xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="bg-indigo-950 text-white px-8 py-5 flex justify-between items-center shrink-0">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-orange-600 rounded-xl">
              <Scissors size={24} />
            </div>
            <div>
              <h2 className="text-xl font-black uppercase tracking-wider">Sistema de Despiece</h2>
              <p className="text-indigo-300 text-xs font-medium mt-0.5">Orden de Montaje y Lista de Corte</p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-2 hover:bg-white/10 rounded-xl transition-colors"
          >
            <X size={24} />
          </button>
        </div>

        {/* View Tabs */}
        <div className="bg-indigo-50 px-8 py-3 flex gap-2 border-b border-indigo-100 shrink-0">
          <button
            onClick={() => setActiveView('montaje')}
            className={`px-6 py-2.5 rounded-xl font-black text-xs uppercase tracking-widest transition-all flex items-center gap-2 ${
              activeView === 'montaje' 
                ? 'bg-indigo-950 text-white shadow-lg' 
                : 'bg-white text-indigo-400 hover:bg-indigo-100 border border-indigo-100'
            }`}
          >
            <Package size={16} />
            Orden de Montaje
          </button>
          <button
            onClick={() => setActiveView('corte')}
            className={`px-6 py-2.5 rounded-xl font-black text-xs uppercase tracking-widest transition-all flex items-center gap-2 ${
              activeView === 'corte' 
                ? 'bg-orange-600 text-white shadow-lg' 
                : 'bg-white text-indigo-400 hover:bg-indigo-100 border border-indigo-100'
            }`}
          >
            <Scissors size={16} />
            Lista de Corte
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-8">
          {loading && (
            <div className="flex flex-col items-center justify-center py-20">
              <Loader size={48} className="animate-spin text-indigo-600 mb-4" />
              <p className="text-indigo-600 font-bold uppercase tracking-widest text-sm">Calculando despiece...</p>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-6 flex items-center gap-4">
              <AlertCircle size={24} className="text-red-500 shrink-0" />
              <div>
                <p className="font-bold text-red-700">Error al calcular despiece</p>
                <p className="text-red-600 text-sm">{error}</p>
              </div>
            </div>
          )}

          {despieceData && !loading && (
            <>
              {/* Summary Banner */}
              <div className="bg-gradient-to-r from-indigo-950 to-indigo-800 rounded-2xl p-6 mb-6 text-white">
                <div className="grid grid-cols-4 gap-6">
                  <div className="text-center">
                    <p className="text-indigo-300 text-xs font-bold uppercase tracking-widest mb-1">Muebles</p>
                    <p className="text-3xl font-black">{despieceData.summary.totalFurniture}</p>
                  </div>
                  <div className="text-center">
                    <p className="text-indigo-300 text-xs font-bold uppercase tracking-widest mb-1">Piezas Totales</p>
                    <p className="text-3xl font-black text-orange-500">{despieceData.summary.totalPieces}</p>
                  </div>
                  <div className="text-center">
                    <p className="text-indigo-300 text-xs font-bold uppercase tracking-widest mb-1">Área Total</p>
                    <p className="text-3xl font-black">{despieceData.summary.totalArea} m²</p>
                  </div>
                  <div className="text-center">
                    <p className="text-indigo-300 text-xs font-bold uppercase tracking-widest mb-1">Material Armazón</p>
                    <p className="text-lg font-black truncate">{carcassMaterialName}</p>
                  </div>
                </div>
              </div>

              {/* Material Summary */}
              <div className="bg-indigo-50 rounded-xl p-4 mb-6">
                <h3 className="text-xs font-black uppercase tracking-widest text-indigo-400 mb-3">Resumen por Material</h3>
                <div className="flex flex-wrap gap-3">
                  {Object.entries(despieceData.summary.byMaterial).map(([material, data]) => (
                    <div key={material} className="bg-white rounded-lg px-4 py-2 border border-indigo-100 flex items-center gap-3">
                      <Box size={16} className="text-indigo-600" />
                      <div>
                        <p className="font-bold text-indigo-900 text-sm">{material}</p>
                        <p className="text-xs text-indigo-400">{data.pieces} piezas · {data.area} m²</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Orden de Montaje View */}
              {activeView === 'montaje' && (
                <div className="space-y-4">
                  {despieceData.items.map((furniture, idx) => (
                    <div key={furniture.productId} className="bg-white border border-indigo-100 rounded-xl overflow-hidden shadow-sm">
                      {/* Furniture Header */}
                      <button 
                        onClick={() => toggleExpand(furniture.productId)}
                        className="w-full px-6 py-4 flex items-center justify-between bg-indigo-50/50 hover:bg-indigo-50 transition-colors"
                      >
                        <div className="flex items-center gap-4">
                          <span className="w-8 h-8 bg-indigo-950 text-white rounded-lg flex items-center justify-center font-black text-sm">
                            {idx + 1}
                          </span>
                          <div className="text-left">
                            <p className="font-black text-indigo-950 uppercase tracking-tight">{furniture.productCode}</p>
                            <p className="text-xs text-indigo-400 font-medium">{furniture.productName}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-6">
                          <div className="text-right">
                            <p className="text-xs text-indigo-300 uppercase font-bold">Dimensiones</p>
                            <p className="font-black text-indigo-800 text-sm">
                              {Math.round(furniture.originalWidth / 10)} x {furniture.originalHeight} x {furniture.originalDepth} cm
                            </p>
                          </div>
                          <div className="text-right">
                            <p className="text-xs text-indigo-300 uppercase font-bold">Cantidad</p>
                            <p className="font-black text-orange-600 text-lg">x{furniture.itemQuantity}</p>
                          </div>
                          {expandedItems[furniture.productId] ? <ChevronDown size={20} className="text-indigo-300" /> : <ChevronRight size={20} className="text-indigo-300" />}
                        </div>
                      </button>

                      {/* Components List */}
                      {expandedItems[furniture.productId] && (
                        <div className="border-t border-indigo-100">
                          <table className="w-full">
                            <thead className="bg-indigo-950 text-white text-xs font-black uppercase tracking-widest">
                              <tr>
                                <th className="px-6 py-3 text-left">Componente</th>
                                <th className="px-4 py-3 text-center">Código</th>
                                <th className="px-4 py-3 text-center">Material</th>
                                <th className="px-4 py-3 text-center">Ancho (mm)</th>
                                <th className="px-4 py-3 text-center">Alto (mm)</th>
                                <th className="px-4 py-3 text-center">Cant.</th>
                                <th className="px-4 py-3 text-right">Notas</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-indigo-50">
                              {furniture.components.map((comp, compIdx) => (
                                <tr key={comp.id} className="hover:bg-indigo-50/50 transition-colors">
                                  <td className="px-6 py-3">
                                    <span className="font-bold text-indigo-900">{comp.name}</span>
                                  </td>
                                  <td className="px-4 py-3 text-center">
                                    <span className="bg-indigo-100 text-indigo-700 px-2 py-1 rounded text-xs font-black">
                                      {comp.nameShort}
                                    </span>
                                  </td>
                                  <td className="px-4 py-3 text-center text-sm text-indigo-600">{comp.material}</td>
                                  <td className="px-4 py-3 text-center">
                                    <input
                                      type="number"
                                      value={getComponentValue(furniture.productId, comp, 'width')}
                                      onChange={(e) => handleEditComponent(furniture.productId, comp.id, 'width', parseFloat(e.target.value))}
                                      className="w-20 bg-white border border-indigo-200 rounded px-2 py-1 text-center text-sm font-bold focus:border-orange-500 focus:outline-none"
                                    />
                                  </td>
                                  <td className="px-4 py-3 text-center">
                                    <input
                                      type="number"
                                      value={getComponentValue(furniture.productId, comp, 'height')}
                                      onChange={(e) => handleEditComponent(furniture.productId, comp.id, 'height', parseFloat(e.target.value))}
                                      className="w-20 bg-white border border-indigo-200 rounded px-2 py-1 text-center text-sm font-bold focus:border-orange-500 focus:outline-none"
                                    />
                                  </td>
                                  <td className="px-4 py-3 text-center font-black text-orange-600">{comp.quantity}</td>
                                  <td className="px-4 py-3 text-right text-xs text-indigo-400 italic">{comp.notes}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                          <div className="px-6 py-3 bg-indigo-50/50 flex justify-between items-center">
                            <span className="text-xs font-bold text-indigo-400 uppercase">Total componentes: {furniture.totalPanels}</span>
                            <span className="text-xs font-bold text-indigo-400 uppercase">Área: {furniture.totalArea} m²</span>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Lista de Corte View */}
              {activeView === 'corte' && (
                <div className="bg-white border border-indigo-100 rounded-xl overflow-hidden">
                  <table className="w-full">
                    <thead className="bg-orange-600 text-white text-xs font-black uppercase tracking-widest">
                      <tr>
                        <th className="px-6 py-4 text-left">#</th>
                        <th className="px-4 py-4 text-left">Mueble</th>
                        <th className="px-4 py-4 text-left">Pieza</th>
                        <th className="px-4 py-4 text-center">Material</th>
                        <th className="px-4 py-4 text-center">Largo (mm)</th>
                        <th className="px-4 py-4 text-center">Ancho (mm)</th>
                        <th className="px-4 py-4 text-center">Cantidad</th>
                        <th className="px-4 py-4 text-center">Cantos</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-indigo-50">
                      {despieceData.items.flatMap((furniture, fIdx) => 
                        furniture.components.map((comp, cIdx) => {
                          const rowNum = despieceData.items
                            .slice(0, fIdx)
                            .reduce((acc, f) => acc + f.components.length, 0) + cIdx + 1;
                          
                          // Determine edge banding based on component
                          let cantos = "-";
                          if (comp.notes.includes("frontal visto")) cantos = "1L";
                          if (comp.name.includes("LATERAL")) cantos = "1L";
                          if (comp.name.includes("TAPA")) cantos = "1L";
                          
                          return (
                            <tr key={`${furniture.productId}-${comp.id}`} className="hover:bg-orange-50/50 transition-colors">
                              <td className="px-6 py-3 font-black text-indigo-300">{rowNum}</td>
                              <td className="px-4 py-3">
                                <span className="font-bold text-indigo-900 text-sm">{furniture.productCode}</span>
                                <span className="text-indigo-400 text-xs ml-2">x{furniture.itemQuantity}</span>
                              </td>
                              <td className="px-4 py-3">
                                <span className="bg-indigo-100 text-indigo-700 px-2 py-1 rounded text-xs font-black mr-2">
                                  {comp.nameShort}
                                </span>
                                <span className="text-sm text-indigo-600">{comp.name}</span>
                              </td>
                              <td className="px-4 py-3 text-center text-xs text-indigo-500">{comp.material}</td>
                              <td className="px-4 py-3 text-center font-black text-indigo-900">
                                {getComponentValue(furniture.productId, comp, 'width')}
                              </td>
                              <td className="px-4 py-3 text-center font-black text-indigo-900">
                                {getComponentValue(furniture.productId, comp, 'height')}
                              </td>
                              <td className="px-4 py-3 text-center font-black text-orange-600">
                                {comp.quantity * furniture.itemQuantity}
                              </td>
                              <td className="px-4 py-3 text-center">
                                <span className={`px-2 py-1 rounded text-xs font-bold ${cantos !== '-' ? 'bg-green-100 text-green-700' : 'text-indigo-300'}`}>
                                  {cantos}
                                </span>
                              </td>
                            </tr>
                          );
                        })
                      )}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="bg-indigo-50 px-8 py-4 flex justify-between items-center border-t border-indigo-100 shrink-0">
          <p className="text-xs text-indigo-400 font-medium">
            Generado: {despieceData?.generatedAt ? new Date(despieceData.generatedAt).toLocaleString('es-ES') : '-'}
          </p>
          <div className="flex gap-3">
            <button
              onClick={handlePrint}
              className="bg-white border border-indigo-200 text-indigo-700 px-5 py-2.5 rounded-xl font-bold text-xs uppercase tracking-widest flex items-center gap-2 hover:bg-indigo-50 transition-colors"
            >
              <Printer size={16} />
              Imprimir
            </button>
            <button
              onClick={onClose}
              className="bg-indigo-950 text-white px-6 py-2.5 rounded-xl font-bold text-xs uppercase tracking-widest hover:bg-indigo-800 transition-colors"
            >
              Cerrar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DespieceModal;
