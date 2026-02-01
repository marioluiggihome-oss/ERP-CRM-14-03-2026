import React, { useState, useEffect, useMemo } from 'react';
import { X, FileText, Layers, Scissors, Package, Download, Printer, ChevronDown, ChevronRight, Edit3, Save, AlertCircle, Loader, Box, Ruler, Calendar, User, Hash } from 'lucide-react';
import { despieceAPI } from '../services/api';

const DespieceModal = ({ isOpen, onClose, items, catalogs, carcassMaterialName, customerName, projectReference, expedientNumber }) => {
  const [despieceData, setDespieceData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeView, setActiveView] = useState('montaje'); // 'montaje' or 'corte'
  const [expandedItems, setExpandedItems] = useState({});
  const [editingComponent, setEditingComponent] = useState(null);
  const [editedComponents, setEditedComponents] = useState({});
  
  // Editable header fields
  const [editableCustomerName, setEditableCustomerName] = useState(customerName || '');
  const [editableProjectRef, setEditableProjectRef] = useState(projectReference || '');
  const [editableExpedient, setEditableExpedient] = useState(expedientNumber || '');
  
  // Update editable fields when props change
  useEffect(() => {
    setEditableCustomerName(customerName || '');
    setEditableProjectRef(projectReference || '');
    setEditableExpedient(expedientNumber || '');
  }, [customerName, projectReference, expedientNumber]);

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
        "Tablero 8mm",  // Trasera siempre 8mm
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

  // Exportar archivo CSV para seccionadora
  const handleExportCSV = () => {
    if (!despieceData || !despieceData.items) {
      alert('No hay datos de despiece para exportar');
      return;
    }
    
    // Formato: Material;Grosor;Nombre pieza;Largo pieza;Ancho pieza;Cantidad;Textura;Código
    let csvContent = "Material;Grosor;Nombre pieza;Largo pieza;Ancho pieza;Cantidad;Textura;Código\n";
    
    despieceData.items.forEach(item => {
      const itemQty = item.itemQuantity || 1;
      item.components?.forEach(comp => {
        const compValue = (field) => getComponentValue(item.productId, comp, field);
        const espesor = compValue('thickness') || 18;
        // Código material basado en espesor y tipo
        const materialBase = carcassMaterialName?.toUpperCase().replace(/\s+/g, '') || 'MELAMINA';
        const material = `40-${materialBase}${espesor < 10 ? '0' : ''}${espesor}`;
        const nombrePieza = comp.name || 'Pieza';
        const largo = compValue('length') || 0;
        const ancho = compValue('width') || 0;
        const cantidad = (compValue('quantity') || 1) * itemQty;
        // Textura: 0 = sin veta, 1 = con veta (verticales suelen tener veta)
        const esVertical = nombrePieza.toLowerCase().includes('lateral') || 
                          nombrePieza.toLowerCase().includes('costado') ||
                          nombrePieza.toLowerCase().includes('vertical');
        const textura = esVertical ? 1 : 0;
        // Código de la pieza
        const codigo = `${item.productCode || ''}-${comp.id || nombrePieza.substring(0,3).toUpperCase()}`;
        
        csvContent += `${material};${espesor.toFixed(1).replace('.', ',')};${nombrePieza};${largo};${ancho};${cantidad};${textura};${codigo}\n`;
      });
    });
    
    // Descargar archivo
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `DESPIECE_${editableExpedient || 'EXP'}_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  // Exportar archivo XML para seccionadora (formato CutRite/Ardis)
  const handleExportXML = () => {
    if (!despieceData || !despieceData.items) {
      alert('No hay datos de despiece para exportar');
      return;
    }
    
    let xmlContent = '<?xml version="1.0" encoding="UTF-8"?>\n';
    xmlContent += '<CuttingList>\n';
    xmlContent += `  <Project name="${editableExpedient || 'DESPIECE'}" customer="${editableCustomerName || ''}" date="${new Date().toISOString().split('T')[0]}">\n`;
    
    // Agrupar por material
    const byMaterial = {};
    despieceData.items.forEach(item => {
      const itemQty = item.itemQuantity || 1;
      item.components?.forEach(comp => {
        const mat = comp.material || carcassMaterialName || 'MELAMINA';
        if (!byMaterial[mat]) byMaterial[mat] = [];
        byMaterial[mat].push({
          ...comp,
          productCode: item.productCode,
          itemQuantity: itemQty,
          productId: item.productId
        });
      });
    });
    
    let partId = 1;
    Object.entries(byMaterial).forEach(([material, pieces]) => {
      xmlContent += `    <Material name="${material}">\n`;
      pieces.forEach((piece) => {
        const compValue = (field) => getComponentValue(piece.productId, piece, field);
        const desc = `${piece.productCode} - ${piece.name}`;
        const qty = (compValue('quantity') || 1) * piece.itemQuantity;
        
        xmlContent += `      <Part id="${partId++}" description="${desc}">\n`;
        xmlContent += `        <Length>${compValue('length') || 0}</Length>\n`;
        xmlContent += `        <Width>${compValue('width') || 0}</Width>\n`;
        xmlContent += `        <Thickness>${compValue('thickness') || 18}</Thickness>\n`;
        xmlContent += `        <Quantity>${qty}</Quantity>\n`;
        xmlContent += `        <Grain>${piece.grain ? 'true' : 'false'}</Grain>\n`;
        xmlContent += `        <EdgeBanding l1="0" l2="0" w1="0" w2="0"/>\n`;
        xmlContent += `      </Part>\n`;
      });
      xmlContent += `    </Material>\n`;
    });
    
    xmlContent += `  </Project>\n`;
    xmlContent += '</CuttingList>\n';
    
    // Descargar archivo
    const blob = new Blob([xmlContent], { type: 'application/xml;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `DESPIECE_${editableExpedient || 'EXP'}_${new Date().toISOString().split('T')[0]}.xml`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
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

        {/* Project Info Bar - Cliente, Referencia, Fecha, Expediente */}
        <div className="bg-white px-8 py-4 border-b border-indigo-100 shrink-0">
          <div className="grid grid-cols-4 gap-4">
            <div className="flex items-center gap-2">
              <User size={16} className="text-indigo-400" />
              <div className="flex-1">
                <label className="text-[9px] font-black text-indigo-300 uppercase tracking-widest">Cliente</label>
                <input
                  type="text"
                  value={editableCustomerName}
                  onChange={(e) => setEditableCustomerName(e.target.value)}
                  placeholder="Nombre del cliente..."
                  className="w-full text-sm font-bold text-indigo-900 bg-transparent outline-none border-b border-transparent hover:border-indigo-200 focus:border-orange-500"
                />
              </div>
            </div>
            <div className="flex items-center gap-2">
              <FileText size={16} className="text-indigo-400" />
              <div className="flex-1">
                <label className="text-[9px] font-black text-indigo-300 uppercase tracking-widest">Referencia Proyecto</label>
                <input
                  type="text"
                  value={editableProjectRef}
                  onChange={(e) => setEditableProjectRef(e.target.value)}
                  placeholder="REF-001..."
                  className="w-full text-sm font-bold text-indigo-900 bg-transparent outline-none border-b border-transparent hover:border-indigo-200 focus:border-orange-500"
                />
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Calendar size={16} className="text-indigo-400" />
              <div className="flex-1">
                <label className="text-[9px] font-black text-indigo-300 uppercase tracking-widest">Fecha</label>
                <p className="text-sm font-bold text-indigo-900">{new Date().toLocaleDateString('es-ES')}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Hash size={16} className="text-indigo-400" />
              <div className="flex-1">
                <label className="text-[9px] font-black text-indigo-300 uppercase tracking-widest">Nº Expediente</label>
                <input
                  type="text"
                  value={editableExpedient}
                  onChange={(e) => setEditableExpedient(e.target.value)}
                  placeholder="EXP-0001..."
                  className="w-full text-sm font-bold text-indigo-900 bg-transparent outline-none border-b border-transparent hover:border-indigo-200 focus:border-orange-500"
                />
              </div>
            </div>
          </div>
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
                            <p className="text-xs text-indigo-300 uppercase font-bold">Dimensiones (mm)</p>
                            <p className="font-black text-indigo-800 text-sm">
                              {furniture.originalWidth} x {furniture.originalHeight * 10} x {furniture.originalDepth * 10}
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
            {/* Botones de exportación para seccionadora */}
            {despieceData && (
              <>
                <button
                  onClick={handleExportCSV}
                  className="bg-emerald-600 text-white px-5 py-2.5 rounded-xl font-bold text-xs uppercase tracking-widest flex items-center gap-2 hover:bg-emerald-700 transition-colors shadow-lg"
                  title="Exportar CSV para seccionadora"
                >
                  <Download size={16} />
                  CSV Seccionadora
                </button>
                <button
                  onClick={handleExportXML}
                  className="bg-blue-600 text-white px-5 py-2.5 rounded-xl font-bold text-xs uppercase tracking-widest flex items-center gap-2 hover:bg-blue-700 transition-colors shadow-lg"
                  title="Exportar XML (CutRite/Ardis)"
                >
                  <Download size={16} />
                  XML CutRite
                </button>
              </>
            )}
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
