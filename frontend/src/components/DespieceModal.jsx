import React, { useState, useEffect, useMemo, useRef } from 'react';
import { X, FileText, Layers, Scissors, Package, Download, Printer, ChevronDown, ChevronRight, Edit3, Save, AlertCircle, Loader, Box, Ruler, Calendar, User, Hash, Copy, Check, FileDown, Grid3X3, Wrench, Maximize2, Minimize2, LayoutGrid, DoorOpen, Truck, Send } from 'lucide-react';
import { despieceAPI } from '../services/api';
import BoardOptimizer from './BoardOptimizer';

const DespieceModal = ({ isOpen, onClose, items, catalogs, carcassMaterialName, carcassBackThickness, customerName, projectReference, expedientNumber, doorColorLow, doorColorHigh, doorColorColumns, sideColor, doorHasVeta = false }) => {
  const [despieceData, setDespieceData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeView, setActiveView] = useState('montaje'); // 'montaje', 'corte', 'bandas', 'herrajes', 'puertas_proveedor'
  const [supplierDoors, setSupplierDoors] = useState([]); // Puertas editables para proveedor
  const [expandedItems, setExpandedItems] = useState({});
  const [editingComponent, setEditingComponent] = useState(null);
  const [editedComponents, setEditedComponents] = useState({});
  const [copiedCascoId, setCopiedCascoId] = useState(null);
  const [isMaximized, setIsMaximized] = useState(false);
  const [showBoardOptimizer, setShowBoardOptimizer] = useState(false);
  const printRef = useRef(null);
  
  // Editable header fields
  const [editableCustomerName, setEditableCustomerName] = useState(customerName || '');
  const [editableProjectRef, setEditableProjectRef] = useState(projectReference || '');
  const [editableExpedient, setEditableExpedient] = useState(expedientNumber || '');
  
  // Función para copiar dimensiones del casco al portapapeles
  const handleCopyCascoDimensions = (furniture) => {
    const ancho = furniture.originalWidth;
    const alto = furniture.originalHeight;
    const fondo = furniture.originalDepth;
    
    const text = `${furniture.productCode} - Casco: ${ancho} x ${alto} x ${fondo} cm`;
    
    navigator.clipboard.writeText(text).then(() => {
      setCopiedCascoId(furniture.productId);
      setTimeout(() => setCopiedCascoId(null), 2000);
    }).catch(err => {
      console.error('Error copying to clipboard:', err);
      alert('Error al copiar al portapapeles');
    });
  };
  
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
      // Prepare items for API - incluir tanto muebles del catálogo como líneas manuales
      const apiItems = items.map(item => {
        if (item.isManual) {
          // Línea manual - usar los datos del item directamente
          return {
            productId: item.productId || `manual-${item.id}`,
            productCode: 'MANUAL',
            productName: item.manualDescription || 'CONCEPTO MANUAL',
            width: item.customWidth || 0,
            height: item.customHeight || 0,
            depth: item.customDepth || 0,
            quantity: item.quantity || 1,
            category: 'MANUAL',
            isManual: true
          };
        } else {
          // Mueble del catálogo
          const product = allProducts.find(p => p.id === item.productId);
          return {
            productId: item.productId,
            productCode: item.customReference || product?.code || 'UNKNOWN',
            productName: product?.name || item.productName || 'Producto Desconocido',
            width: item.customWidth,
            height: item.customHeight,
            depth: item.customDepth,
            quantity: item.quantity,
            category: product?.category || ''
          };
        }
      });

      if (apiItems.length === 0) {
        setError('No hay muebles válidos para calcular el despiece');
        setLoading(false);
        return;
      }

      const result = await despieceAPI.calculate(
        apiItems,
        carcassMaterialName,
        `Tablero ${carcassBackThickness || 8}mm`,  // Trasera con grosor configurable desde armazón
        18,
        carcassBackThickness || 8  // Pasar el grosor de trasera
      );
      
      setDespieceData(result);
      
      // Expand all items by default
      const expanded = {};
      result.items.forEach(item => {
        expanded[item.productId] = true;
      });
      setExpandedItems(expanded);
      
      // Inicializar puertas para proveedor con datos calculados
      initializeSupplierDoors(result.items);
      
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

  // Función para detectar tipo de mueble (ALTO, BAJO, COLUMNA) - Reutilizable
  const detectTipoMueble = (code, name) => {
    const c = (code || '').toUpperCase();
    const n = (name || '').toUpperCase();
    
    // COLUMNAS (detectar primero - más específico)
    const columnaPrefixes = ['CD', 'CE', 'CF', 'CH', 'CHPC', 'CHGC', 'CHC', 'CHM', 'CHMG', 'CHMC', 'CHMCG', 'BOC'];
    if (columnaPrefixes.some(prefix => c.startsWith(prefix))) return 'COLUMNAS';
    const mediaColumnaPrefixes = ['MGHM', 'MCHM', 'MPG', 'MVG', 'MPH', 'MPM'];
    if (mediaColumnaPrefixes.some(prefix => c.startsWith(prefix))) return 'COLUMNAS';
    if (/^M\d/.test(c) || /^MV\d/.test(c)) return 'COLUMNAS';
    if (n.includes('COLUMNA') || n.includes('SEMICOLUMNA') || n.includes('MEDIACOLUMNA')) return 'COLUMNAS';
    
    // ALTOS
    const altoPrefixes = ['ASCE', 'ASC', 'ARI', 'ARU', 'ARC', 'AD', 'AV', 'AE', 'AMF', 'AM', 'ACA', 'ACC', 'ASF', 'ATP', 'AT', 'AA', 'ACPJ', 'ACP', 'AC', 'AR'];
    if (altoPrefixes.some(prefix => c.startsWith(prefix))) return 'ALTOS';
    if (/^A\d/.test(c) || /^9A/.test(c)) return 'ALTOS';
    const altilloSobrePrefixes = ['LD', 'LV', 'SVC', 'SV', 'SC', 'BOA', 'BOS'];
    if (altilloSobrePrefixes.some(prefix => c.startsWith(prefix))) return 'ALTOS';
    if (/^L\d/.test(c) || /^S\d/.test(c)) return 'ALTOS';
    if (n.includes('ALTO') || n.includes('ALTILLO') || n.includes('SOBREENCIMERA') || n.includes('SOBREM')) return 'ALTOS';
    
    // BAJOS
    const bajoPrefixes = ['BRI', 'BRU', 'BR', 'BHZ', 'BHG', 'BHC', 'BH', 'BTP', 'BT', 'BPC', 'BCGF', 'BCG', 'BGF', 'BGC', 'BC', 'BF'];
    if (bajoPrefixes.some(prefix => c.startsWith(prefix))) return 'BAJOS';
    if (/^B\d/.test(c) || /^9B/.test(c)) return 'BAJOS';
    if (n.includes('BAJO') || n.includes('FREGADERO') || (n.includes('HORNO') && !n.includes('COLUMNA'))) return 'BAJOS';
    
    // Puertas sueltas = BAJOS por defecto
    if (c.startsWith('P') || c.startsWith('PV') || c.startsWith('PVI') || c.startsWith('PVR')) return 'BAJOS';
    
    return 'BAJOS';
  };

  // Inicializar puertas editables para proveedor
  const initializeSupplierDoors = (items) => {
    const doors = [];
    let doorIndex = 0;
    
    items?.forEach(furniture => {
      const tipoMueble = detectTipoMueble(furniture.productCode, furniture.productName);
      
      // Determinar color según tipo
      let color = '';
      if (tipoMueble === 'ALTOS') color = doorColorHigh || 'Sin especificar';
      else if (tipoMueble === 'BAJOS') color = doorColorLow || 'Sin especificar';
      else color = doorColorColumns || 'Sin especificar';
      
      const puertaComps = furniture.components?.filter(c => 
        c.name?.toLowerCase().includes('puerta') || 
        c.type?.toUpperCase() === 'PUERTA'
      ) || [];
      
      puertaComps.forEach(p => {
        const itemQty = parseInt(furniture.itemQuantity) || 1;
        const doorQty = parseInt(p.quantity) || 1;
        const totalDoors = doorQty * itemQty;
        
        console.log(`[Puertas Proveedor] ${furniture.productCode}: doorQty=${doorQty} x itemQty=${itemQty} = ${totalDoors} puertas`);
        
        // Crear una entrada por cada tipo de puerta con sus unidades
        doors.push({
          id: `door-${doorIndex++}`,
          muebleCode: furniture.productCode,
          muebleName: furniture.productName,
          tipoMueble: tipoMueble,
          color: color,
          alto: parseFloat(p.length) || 0,
          ancho: parseFloat(p.width) || 0,
          veta: doorHasVeta ? 'V' : 'N', // Usar config del presupuesto: V=Vertical, N=Sin veta
          unidades: totalDoors, // Cantidad de puertas
          observaciones: ''
        });
      });
    });
    
    setSupplierDoors(doors);
  };

  // Actualizar puerta de proveedor
  const updateSupplierDoor = (doorId, field, value) => {
    setSupplierDoors(prev => prev.map(d => 
      d.id === doorId ? { ...d, [field]: value } : d
    ));
  };

  // Exportar CSV de puertas para proveedor
  const handleExportSupplierDoorsCSV = () => {
    if (!supplierDoors || supplierDoors.length === 0) {
      alert('No hay puertas para exportar');
      return;
    }
    
    // Calcular total de unidades
    const totalUnidades = supplierDoors.reduce((sum, d) => sum + (parseInt(d.unidades) || 1), 0);
    
    // Generar CSV
    let csv = "PEDIDO PUERTAS - PROVEEDOR\n";
    csv += `Cliente: ${editableCustomerName || '-'}\n`;
    csv += `Expediente: ${editableExpedient || '-'}\n`;
    csv += `Fecha: ${new Date().toLocaleDateString('es-ES')}\n\n`;
    csv += "Mueble;Color;Alto (cm);Ancho (cm);Veta;Unidades;Tipo;Observaciones\n";
    
    supplierDoors.forEach(d => {
      const vetaText = d.veta === 'V' ? 'Vertical' : d.veta === 'H' ? 'Horizontal' : 'Sin veta';
      csv += `${d.muebleCode};${d.color};${d.alto};${d.ancho};${vetaText};${d.unidades || 1};${d.tipoMueble};${d.observaciones || ''}\n`;
    });
    
    // Totales
    csv += `\nTOTAL PUERTAS: ${totalUnidades}\n`;
    
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    const nombreArchivo = `PUERTAS_PROVEEDOR_${(editableExpedient || 'EXP').replace(/[^a-zA-Z0-9-]/g, '_')}_${new Date().toISOString().split('T')[0]}.csv`;
    link.setAttribute('download', nombreArchivo);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  // Exportar PDF de puertas para proveedor
  const handleExportSupplierDoorsPDF = () => {
    if (!supplierDoors || supplierDoors.length === 0) {
      alert('No hay puertas para exportar');
      return;
    }
    
    const printWindow = window.open('', '_blank');
    const fechaHoy = new Date().toLocaleDateString('es-ES');
    
    // Calcular total de unidades
    const totalUnidades = supplierDoors.reduce((sum, d) => sum + (parseInt(d.unidades) || 1), 0);
    
    let html = `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="UTF-8">
        <title>PEDIDO PUERTAS - PROVEEDOR</title>
        <style>
          @page { size: A4 portrait; margin: 15mm; }
          @media print { body { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; } }
          * { box-sizing: border-box; margin: 0; padding: 0; }
          body { font-family: Arial, Helvetica, sans-serif; font-size: 11px; color: #333; line-height: 1.4; }
          .header { background: #1e40af; color: white; padding: 20px; margin-bottom: 15px; }
          .header h1 { font-size: 18px; margin-bottom: 5px; }
          .header-subtitle { font-size: 10px; opacity: 0.9; }
          .info-box { background: #f3f4f6; border: 1px solid #e5e7eb; padding: 15px; margin-bottom: 15px; display: flex; justify-content: space-between; }
          .info-item { text-align: center; }
          .info-label { font-size: 9px; color: #666; text-transform: uppercase; font-weight: bold; }
          .info-value { font-size: 14px; font-weight: bold; margin-top: 3px; }
          table { width: 100%; border-collapse: collapse; margin-bottom: 15px; }
          th { background: #1e40af; color: white; padding: 10px; font-size: 10px; text-align: left; font-weight: bold; text-transform: uppercase; }
          td { padding: 10px; border-bottom: 1px solid #e5e7eb; }
          tr:nth-child(even) { background: #f9fafb; }
          .text-center { text-align: center; }
          .text-right { text-align: right; }
          .font-bold { font-weight: bold; }
          .total-row { background: #dbeafe !important; }
          .total-row td { font-weight: bold; font-size: 13px; border-top: 2px solid #1e40af; }
          .footer { margin-top: 20px; padding-top: 10px; border-top: 1px solid #ccc; font-size: 9px; color: #666; text-align: center; }
          .veta-badge { background: #d1fae5; color: #065f46; padding: 3px 8px; border-radius: 4px; font-size: 9px; font-weight: bold; }
          .color-badge { background: #fef3c7; color: #92400e; padding: 3px 8px; border-radius: 4px; font-size: 9px; font-weight: bold; }
        </style>
      </head>
      <body>
        <div class="header">
          <h1>📦 PEDIDO DE PUERTAS - PROVEEDOR</h1>
          <div class="header-subtitle">LUIGGI HOME - Documento para envío a proveedor</div>
        </div>
        
        <div class="info-box">
          <div class="info-item">
            <div class="info-label">Cliente</div>
            <div class="info-value">${editableCustomerName || '-'}</div>
          </div>
          <div class="info-item">
            <div class="info-label">Expediente</div>
            <div class="info-value">${editableExpedient || '-'}</div>
          </div>
          <div class="info-item">
            <div class="info-label">Referencia</div>
            <div class="info-value">${editableProjectRef || '-'}</div>
          </div>
          <div class="info-item">
            <div class="info-label">Fecha Pedido</div>
            <div class="info-value">${fechaHoy}</div>
          </div>
        </div>
        
        <table>
          <thead>
            <tr>
              <th>Mueble</th>
              <th>Color/Acabado</th>
              <th class="text-center">Alto (cm)</th>
              <th class="text-center">Ancho (cm)</th>
              <th class="text-center">Veta</th>
              <th class="text-center">Unidades</th>
              <th>Tipo</th>
              <th>Observaciones</th>
            </tr>
          </thead>
          <tbody>
    `;
    
    supplierDoors.forEach(d => {
      const vetaText = d.veta === 'V' ? '↕ Vertical' : d.veta === 'H' ? '↔ Horizontal' : '— Sin veta';
      html += `
        <tr>
          <td><strong>${d.muebleCode}</strong></td>
          <td><span class="color-badge">${d.color}</span></td>
          <td class="text-center font-bold">${d.alto}</td>
          <td class="text-center font-bold">${d.ancho}</td>
          <td class="text-center"><span class="veta-badge">${vetaText}</span></td>
          <td class="text-center font-bold" style="font-size:14px;">${d.unidades || 1}</td>
          <td>${d.tipoMueble}</td>
          <td style="font-size:9px;">${d.observaciones || '-'}</td>
        </tr>
      `;
    });
    
    html += `
            <tr class="total-row">
              <td colspan="5" class="text-right">TOTAL PUERTAS:</td>
              <td class="text-center" style="font-size:16px;">${totalUnidades}</td>
              <td colspan="2"></td>
            </tr>
          </tbody>
        </table>
        
        <div class="footer">
          LUIGGI HOME ERP | Documento generado: ${fechaHoy} ${new Date().toLocaleTimeString('es-ES')} | Este documento es un pedido para proveedor de puertas
        </div>
      </body>
      </html>
    `;
    
    printWindow.document.write(html);
    printWindow.document.close();
    printWindow.onload = () => {
      printWindow.print();
    };
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

  // Calcular canto necesario para cada pieza
  const calculateCantoForComponent = (comp, quantity = 1) => {
    const length = comp.length || 0;
    const width = comp.width || 0;
    const notes = (comp.notes || '').toLowerCase();
    
    // Cantos por defecto según tipo de pieza
    let cantos = { l1: 0, l2: 0, w1: 0, w2: 0 };
    
    if (notes.includes('1l')) {
      // 1 canto largo
      cantos.l1 = length;
    } else if (notes.includes('2l')) {
      // 2 cantos largos
      cantos.l1 = length;
      cantos.l2 = length;
    } else if (notes.includes('4l') || notes.includes('todos')) {
      // 4 cantos (todos los lados)
      cantos.l1 = length;
      cantos.l2 = length;
      cantos.w1 = width;
      cantos.w2 = width;
    }
    
    // Calcular metros lineales totales
    const totalMl = ((cantos.l1 + cantos.l2 + cantos.w1 + cantos.w2) * quantity) / 100;
    return { cantos, totalMl };
  };

  // Calcular resumen de bandas y traseras
  const calculateBandasYTraseras = useMemo(() => {
    if (!despieceData?.items) return null;
    
    let totalCanto = 0;
    let traseraTotalArea = 0;
    let cascoTotalArea = 0;
    const cantoByMaterial = {};
    const traserasByThickness = {};
    
    despieceData.items.forEach(item => {
      const itemQty = item.itemQuantity || 1;
      
      item.components?.forEach(comp => {
        const compQty = (comp.quantity || 1) * itemQty;
        const area = ((comp.length || 0) * (comp.width || 0) * compQty) / 10000; // m²
        const material = comp.material || carcassMaterialName || 'MELAMINA';
        const thickness = comp.thickness || 18;
        
        // Calcular canto
        const { totalMl } = calculateCantoForComponent(comp, compQty);
        totalCanto += totalMl;
        
        if (!cantoByMaterial[material]) cantoByMaterial[material] = 0;
        cantoByMaterial[material] += totalMl;
        
        // Separar traseras del resto
        if (comp.name?.toLowerCase().includes('trasera')) {
          traseraTotalArea += area;
          const key = `${thickness}mm`;
          if (!traserasByThickness[key]) traserasByThickness[key] = { area: 0, pieces: 0 };
          traserasByThickness[key].area += area;
          traserasByThickness[key].pieces += compQty;
        } else {
          cascoTotalArea += area;
        }
      });
    });
    
    return {
      totalCanto: totalCanto.toFixed(2),
      cantoByMaterial,
      traseraTotalArea: traseraTotalArea.toFixed(3),
      cascoTotalArea: cascoTotalArea.toFixed(3),
      traserasByThickness
    };
  }, [despieceData, carcassMaterialName]);

  // Calcular herrajes necesarios (incluye colgadores del backend)
  const calculateHerrajes = useMemo(() => {
    if (!despieceData?.items) return null;
    
    let totalBisagras = 0;
    let totalCorrederas = 0;
    let totalTiradores = 0;
    let totalSoportesBaldas = 0;
    let totalColgadores = 0;  // NUEVO: Colgadores para ALTOS
    
    despieceData.items.forEach(item => {
      const itemQty = item.itemQuantity || 1;
      const height = item.originalHeight || 70;
      const width = item.originalWidth || 60;
      const category = (item.productName || '').toUpperCase();
      
      // Bisagras: 2-3 por puerta según altura
      const numPuertas = category.includes('2P') ? 2 : 1;
      const bisagrasPerPuerta = height > 100 ? 3 : 2;
      totalBisagras += (numPuertas * bisagrasPerPuerta * itemQty);
      
      // Correderas para cajones
      if (category.includes('CAJON') || category.includes('GAVETA')) {
        const numCajones = category.includes('5') ? 5 : category.includes('3') ? 3 : category.includes('2') ? 2 : 1;
        totalCorrederas += (numCajones * 2 * itemQty); // Par por cajón
      }
      
      // Tiradores: 1 por puerta/cajón
      totalTiradores += (numPuertas * itemQty);
      
      // Soportes baldas: 4 por balda
      const numBaldas = item.components?.filter(c => c.name?.toLowerCase().includes('balda')).reduce((acc, c) => acc + (c.quantity || 1), 0) || 0;
      totalSoportesBaldas += (numBaldas * 4 * itemQty);
      
      // COLGADORES: Buscar en componentes del API (ya calculados en backend)
      const colgadorComp = item.components?.find(c => 
        c.name?.toLowerCase().includes('colgador') || c.nameShort === 'COLG'
      );
      if (colgadorComp) {
        totalColgadores += ((colgadorComp.quantity || 1) * itemQty);
      }
    });
    
    return {
      bisagras: totalBisagras,
      correderas: totalCorrederas,
      tiradores: totalTiradores,
      soportesBaldas: totalSoportesBaldas,
      colgadores: totalColgadores  // NUEVO
    };
  }, [despieceData]);

  // Exportar PDF - Genera contenido según la pestaña activa
  const handleExportPDF = () => {
    const printWindow = window.open('', '_blank');
    const fechaHoy = new Date().toLocaleDateString('es-ES');
    
    // Determinar título y contenido según la vista activa
    const viewTitles = {
      'montaje': 'ORDEN DE MONTAJE',
      'corte': 'LISTA DE CORTE',
      'bandas': 'BANDAS Y TRASERAS',
      'herrajes': 'CASCO, PUERTA Y HERRAJE'
    };
    const viewTitle = viewTitles[activeView] || 'DESPIECE';
    
    let html = `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="UTF-8">
        <title>${viewTitle} - ${editableExpedient || 'PRESUPUESTO'}</title>
        <style>
          @page { 
            size: A4 portrait; 
            margin: 10mm 8mm; 
          }
          @media print {
            body { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
          }
          * { box-sizing: border-box; margin: 0; padding: 0; }
          body { font-family: Arial, Helvetica, sans-serif; font-size: 9px; color: #333; line-height: 1.3; }
          .header { background: #1e1b4b; color: white; padding: 10px 12px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; }
          .header h1 { font-size: 14px; margin: 0; }
          .header-right { text-align: right; font-size: 8px; opacity: 0.8; }
          .info-bar { display: flex; justify-content: space-between; margin-bottom: 8px; padding: 8px; background: #f3f4f6; border: 1px solid #e5e7eb; font-size: 8px; }
          .info-item { text-align: center; flex: 1; }
          .info-label { font-size: 7px; color: #666; text-transform: uppercase; font-weight: bold; }
          .info-value { font-size: 10px; font-weight: bold; margin-top: 2px; }
          .summary { display: flex; gap: 6px; margin-bottom: 10px; }
          .summary-box { flex: 1; padding: 6px 8px; background: #eef2ff; border: 1px solid #c7d2fe; text-align: center; }
          .summary-number { font-size: 16px; font-weight: bold; color: #4f46e5; }
          .summary-label { font-size: 7px; color: #666; text-transform: uppercase; }
          table { width: 100%; border-collapse: collapse; margin-bottom: 10px; font-size: 8px; }
          th { background: #1e1b4b; color: white; padding: 5px 4px; font-size: 7px; text-align: left; font-weight: bold; }
          td { padding: 4px; border-bottom: 1px solid #e5e7eb; vertical-align: middle; }
          tr:nth-child(even) { background: #f9fafb; }
          .furniture-header { background: #fef3c7 !important; font-weight: bold; }
          .furniture-header td { font-size: 9px; padding: 6px 4px; border-bottom: 2px solid #f59e0b; }
          .component-row td:first-child { padding-left: 12px; }
          .section-title { background: #1e1b4b; color: white; padding: 6px 10px; margin: 10px 0 6px 0; font-weight: bold; font-size: 10px; page-break-after: avoid; }
          .page-break { page-break-before: always; }
          .avoid-break { page-break-inside: avoid; }
          .footer { margin-top: 15px; padding-top: 8px; border-top: 1px solid #ccc; font-size: 7px; color: #666; text-align: center; }
          .two-col { display: flex; gap: 10px; }
          .two-col > div { flex: 1; }
          .mini-table { font-size: 8px; }
          .mini-table th { padding: 4px; font-size: 7px; }
          .mini-table td { padding: 3px 4px; }
          .text-right { text-align: right; }
          .text-center { text-align: center; }
          .font-bold { font-weight: bold; }
          .bg-amber { background: #fef3c7; }
          .bg-emerald { background: #d1fae5; }
          .bg-orange { background: #ffedd5; }
          .bg-blue { background: #dbeafe; }
          .casco-box { background: #d1fae5; border: 2px solid #10b981; padding: 10px; margin: 8px 0; border-radius: 4px; }
          .casco-dims { display: flex; gap: 15px; justify-content: center; margin-top: 8px; }
          .casco-dim { text-align: center; }
          .casco-dim .label { font-size: 7px; color: #047857; text-transform: uppercase; }
          .casco-dim .value { font-size: 16px; font-weight: bold; color: #065f46; }
        </style>
      </head>
      <body>
        <div class="header">
          <div>
            <h1>${viewTitle}</h1>
          </div>
          <div class="header-right">
            LUIGGI HOME ERP<br/>
            ${fechaHoy}
          </div>
        </div>
        
        <div class="info-bar">
          <div class="info-item">
            <div class="info-label">Cliente</div>
            <div class="info-value">${editableCustomerName || '-'}</div>
          </div>
          <div class="info-item">
            <div class="info-label">Expediente</div>
            <div class="info-value">${editableExpedient || '-'}</div>
          </div>
          <div class="info-item">
            <div class="info-label">Referencia</div>
            <div class="info-value">${editableProjectRef || '-'}</div>
          </div>
          <div class="info-item">
            <div class="info-label">Material Casco</div>
            <div class="info-value">${carcassMaterialName || '-'}</div>
          </div>
        </div>
    `;
    
    // ========== CONTENIDO ESPECÍFICO POR VISTA ==========
    
    if (activeView === 'montaje') {
      // ORDEN DE MONTAJE - Lista completa de piezas por mueble
      html += `
        <div class="summary">
          <div class="summary-box">
            <div class="summary-number">${despieceData?.summary?.totalFurniture || 0}</div>
            <div class="summary-label">Muebles</div>
          </div>
          <div class="summary-box">
            <div class="summary-number">${despieceData?.summary?.totalPieces || 0}</div>
            <div class="summary-label">Piezas</div>
          </div>
          <div class="summary-box">
            <div class="summary-number">${despieceData?.summary?.totalArea || 0}</div>
            <div class="summary-label">Área (m²)</div>
          </div>
          <div class="summary-box">
            <div class="summary-number">${calculateBandasYTraseras?.totalCanto || 0}</div>
            <div class="summary-label">Canto (ml)</div>
          </div>
        </div>

        <div class="section-title">LISTA DE PIEZAS POR MUEBLE</div>
        <table>
          <thead>
            <tr>
              <th style="width:25%">Pieza</th>
              <th style="width:15%">Material</th>
              <th style="width:12%" class="text-center">Largo cm</th>
              <th style="width:12%" class="text-center">Ancho cm</th>
              <th style="width:8%" class="text-center">Gr.mm</th>
              <th style="width:8%" class="text-center">Ud.</th>
              <th style="width:10%" class="text-center">Canto ml</th>
              <th style="width:10%">Notas</th>
            </tr>
          </thead>
          <tbody>
      `;
      
      despieceData?.items?.forEach(item => {
        html += `
          <tr class="furniture-header avoid-break">
            <td colspan="8"><strong>${item.productCode}</strong> - ${item.productName} (${item.originalWidth}×${item.originalHeight}×${item.originalDepth} cm) × ${item.itemQuantity || 1}</td>
          </tr>
        `;
        
        item.components?.forEach(comp => {
          const qty = (comp.quantity || 1) * (item.itemQuantity || 1);
          const { totalMl } = calculateCantoForComponent(comp, qty);
          html += `
            <tr class="component-row avoid-break">
              <td>${comp.name || '-'}</td>
              <td>${comp.material || carcassMaterialName || '-'}</td>
              <td class="text-center">${comp.length || 0}</td>
              <td class="text-center">${comp.width || 0}</td>
              <td class="text-center">${comp.thickness || 18}</td>
              <td class="text-center font-bold">${qty}</td>
              <td class="text-center">${totalMl.toFixed(1)}</td>
              <td>${comp.notes || ''}</td>
            </tr>
          `;
        });
      });
      
      html += `</tbody></table>`;
      
    } else if (activeView === 'corte') {
      // LISTA DE CORTE - Agrupada por material para seccionadora
      html += `
        <div class="summary">
          <div class="summary-box">
            <div class="summary-number">${despieceData?.summary?.totalPieces || 0}</div>
            <div class="summary-label">Piezas Totales</div>
          </div>
          <div class="summary-box">
            <div class="summary-number">${despieceData?.summary?.totalArea || 0}</div>
            <div class="summary-label">Área (m²)</div>
          </div>
        </div>
        <div class="section-title">PIEZAS AGRUPADAS POR MATERIAL</div>
      `;
      
      // Agrupar por material
      const byMaterial = {};
      despieceData?.items?.forEach(item => {
        const itemQty = item.itemQuantity || 1;
        item.components?.forEach(comp => {
          const mat = comp.material || carcassMaterialName || 'MELAMINA';
          if (!byMaterial[mat]) byMaterial[mat] = [];
          byMaterial[mat].push({
            ...comp,
            productCode: item.productCode,
            productName: item.productName,
            itemQuantity: itemQty
          });
        });
      });
      
      // CONSOLIDAR PIEZAS IGUALES (mismo nombre, dimensiones, grosor)
      const consolidatePieces = (pieces) => {
        const consolidated = {};
        pieces.forEach(piece => {
          // Clave única basada en características de la pieza
          const key = `${piece.name || '-'}_${piece.length || 0}_${piece.width || 0}_${piece.thickness || 18}`;
          const qty = (piece.quantity || 1) * (piece.itemQuantity || 1);
          
          if (!consolidated[key]) {
            consolidated[key] = {
              ...piece,
              consolidatedQty: qty,
              productCodes: [piece.productCode]
            };
          } else {
            consolidated[key].consolidatedQty += qty;
            if (!consolidated[key].productCodes.includes(piece.productCode)) {
              consolidated[key].productCodes.push(piece.productCode);
            }
          }
        });
        return Object.values(consolidated);
      };
      
      Object.entries(byMaterial).forEach(([material, pieces]) => {
        const consolidatedPieces = consolidatePieces(pieces);
        const totalPieces = consolidatedPieces.reduce((acc, p) => acc + p.consolidatedQty, 0);
        html += `
          <div class="section-title bg-orange">${material} (${totalPieces} piezas)</div>
          <table>
            <thead>
              <tr>
                <th style="width:10%">Mueble</th>
                <th style="width:20%">Pieza</th>
                <th style="width:15%" class="text-center">Largo cm</th>
                <th style="width:15%" class="text-center">Ancho cm</th>
                <th style="width:10%" class="text-center">Grosor mm</th>
                <th style="width:10%" class="text-center">Cantidad</th>
                <th style="width:20%">Notas</th>
              </tr>
            </thead>
            <tbody>
        `;
        
        consolidatedPieces.forEach(piece => {
          const muebleInfo = piece.productCodes.length > 1 
            ? `${piece.productCodes.slice(0, 2).join(', ')}${piece.productCodes.length > 2 ? '...' : ''}`
            : piece.productCode;
          html += `
            <tr class="avoid-break">
              <td class="font-bold">${muebleInfo}</td>
              <td>${piece.name || '-'}</td>
              <td class="text-center">${piece.length || 0}</td>
              <td class="text-center">${piece.width || 0}</td>
              <td class="text-center">${piece.thickness || 18}</td>
              <td class="text-center font-bold">${piece.consolidatedQty}</td>
              <td>${piece.notes || ''}</td>
            </tr>
          `;
        });
        
        html += `</tbody></table>`;
      });
      
    } else if (activeView === 'bandas') {
      // BANDAS Y TRASERAS
      html += `
        <div class="summary">
          <div class="summary-box bg-emerald">
            <div class="summary-number">${calculateBandasYTraseras?.totalCanto || 0}</div>
            <div class="summary-label">Canto Total (ml)</div>
          </div>
          <div class="summary-box bg-amber">
            <div class="summary-number">${calculateBandasYTraseras?.cascoTotalArea || 0}</div>
            <div class="summary-label">Área Casco (m²)</div>
          </div>
          <div class="summary-box bg-orange">
            <div class="summary-number">${calculateBandasYTraseras?.traseraTotalArea || 0}</div>
            <div class="summary-label">Área Traseras (m²)</div>
          </div>
        </div>
        
        <div class="section-title">RESUMEN DE CANTO POR MATERIAL</div>
        <table class="mini-table">
          <thead><tr><th>Material</th><th class="text-right">Metros Lineales</th></tr></thead>
          <tbody>
      `;
      
      Object.entries(calculateBandasYTraseras?.cantoByMaterial || {}).forEach(([mat, ml]) => {
        html += `<tr><td>${mat}</td><td class="text-right font-bold">${ml.toFixed(2)} ml</td></tr>`;
      });
      
      html += `
          </tbody>
        </table>
        
        <div class="section-title">RESUMEN DE TRASERAS POR ESPESOR</div>
        <table class="mini-table">
          <thead><tr><th>Espesor</th><th class="text-right">Área (m²)</th><th class="text-right">Piezas</th></tr></thead>
          <tbody>
      `;
      
      Object.entries(calculateBandasYTraseras?.traserasByThickness || {}).forEach(([thickness, data]) => {
        html += `<tr><td>${thickness}</td><td class="text-right">${data.area.toFixed(3)}</td><td class="text-right font-bold">${data.pieces}</td></tr>`;
      });
      
      html += `
          </tbody>
        </table>
        
        <div class="section-title">DETALLE DE TRASERAS</div>
        <table>
          <thead>
            <tr>
              <th>Mueble</th>
              <th class="text-center">Largo cm</th>
              <th class="text-center">Ancho cm</th>
              <th class="text-center">Espesor</th>
              <th class="text-center">Cantidad</th>
              <th class="text-right">Área m²</th>
            </tr>
          </thead>
          <tbody>
      `;
      
      despieceData?.items?.forEach(item => {
        const traseras = item.components?.filter(c => c.name?.toLowerCase().includes('trasera')) || [];
        traseras.forEach(t => {
          const qty = (t.quantity || 1) * (item.itemQuantity || 1);
          const area = ((t.length || 0) * (t.width || 0) * qty / 10000).toFixed(3);
          html += `
            <tr class="avoid-break">
              <td class="font-bold">${item.productCode} - ${item.productName}</td>
              <td class="text-center">${t.length || 0}</td>
              <td class="text-center">${t.width || 0}</td>
              <td class="text-center">${t.thickness || 8}mm</td>
              <td class="text-center font-bold">${qty}</td>
              <td class="text-right">${area}</td>
            </tr>
          `;
        });
      });
      
      html += `</tbody></table>`;
      
    } else if (activeView === 'herrajes') {
      // CASCO, PUERTA Y HERRAJE
      html += `
        <div class="section-title">DIMENSIONES DE CASCO POR MUEBLE</div>
      `;
      
      despieceData?.items?.forEach((item, idx) => {
        html += `
          <div class="casco-box avoid-break">
            <div style="display:flex; justify-content:space-between; align-items:center;">
              <div>
                <strong style="font-size:11px;">${idx + 1}. ${item.productCode}</strong>
                <span style="color:#666; font-size:9px;"> - ${item.productName}</span>
              </div>
              <div style="font-size:10px; color:#ea580c; font-weight:bold;">×${item.itemQuantity || 1}</div>
            </div>
            <div class="casco-dims">
              <div class="casco-dim"><div class="label">Ancho</div><div class="value">${item.originalWidth} cm</div></div>
              <div class="casco-dim"><div class="label">Alto</div><div class="value">${item.originalHeight} cm</div></div>
              <div class="casco-dim"><div class="label">Fondo</div><div class="value">${item.originalDepth} cm</div></div>
            </div>
          </div>
        `;
      });
      
      // Función para detectar tipo de mueble - Soporta nomenclaturas ZC y MV
      const detectTipoMueble = (code, name) => {
        const c = (code || '').toUpperCase();
        const n = (name || '').toUpperCase();
        
        // COLUMNAS (más específico primero)
        const columnaPrefixes = ['CD', 'CE', 'CF', 'CH', 'CHPC', 'CHGC', 'CHC', 'CHM', 'CHMG', 'CHMC', 'CHMCG', 'BOC'];
        if (columnaPrefixes.some(prefix => c.startsWith(prefix))) return 'COLUMNAS';
        const mediaColumnaPrefixes = ['MGHM', 'MCHM', 'MPG', 'MVG', 'MPH', 'MPM'];
        if (mediaColumnaPrefixes.some(prefix => c.startsWith(prefix))) return 'COLUMNAS';
        if (/^M\d/.test(c) || /^MV\d/.test(c)) return 'COLUMNAS';
        if (n.includes('COLUMNA') || n.includes('SEMICOLUMNA') || n.includes('MEDIACOLUMNA')) return 'COLUMNAS';
        
        // ALTOS
        const altoPrefixes = ['ASCE', 'ASC', 'ARI', 'ARU', 'ARC', 'AD', 'AV', 'AE', 'AMF', 'AM', 'ACA', 'ACC', 'ASF', 'ATP', 'AT', 'AA', 'ACPJ', 'ACP', 'AC', 'AR'];
        if (altoPrefixes.some(prefix => c.startsWith(prefix))) return 'ALTOS';
        if (/^A\d/.test(c) || /^9A/.test(c)) return 'ALTOS';
        const altilloSobrePrefixes = ['LD', 'LV', 'SVC', 'SV', 'SC', 'BOA', 'BOS'];
        if (altilloSobrePrefixes.some(prefix => c.startsWith(prefix))) return 'ALTOS';
        if (/^L\d/.test(c) || /^S\d/.test(c)) return 'ALTOS';
        if (n.includes('ALTO') || n.includes('ALTILLO') || n.includes('SOBREENCIMERA') || n.includes('SOBREM')) return 'ALTOS';
        
        // BAJOS
        const bajoPrefixes = ['BRI', 'BRU', 'BR', 'BHZ', 'BHG', 'BHC', 'BH', 'BTP', 'BT', 'BPC', 'BCGF', 'BCG', 'BGF', 'BGC', 'BC', 'BF'];
        if (bajoPrefixes.some(prefix => c.startsWith(prefix))) return 'BAJOS';
        if (/^B\d/.test(c) || /^9B/.test(c)) return 'BAJOS';
        if (n.includes('BAJO') || n.includes('FREGADERO')) return 'BAJOS';
        if (c.startsWith('P') || c.startsWith('PV')) return 'BAJOS';
        
        return 'BAJOS';
      };
      
      // Puertas agrupadas por tipo
      const puertas = [];
      despieceData?.items?.forEach(item => {
        const puertaComp = item.components?.find(c => c.name?.toLowerCase().includes('puerta'));
        if (puertaComp) {
          puertas.push({
            productCode: item.productCode,
            productName: item.productName,
            itemQuantity: item.itemQuantity || 1,
            doorHeight: puertaComp.length,
            doorWidth: puertaComp.width,
            doorQty: puertaComp.quantity || 1,
            tipoMueble: detectTipoMueble(item.productCode, item.productName)
          });
        }
      });
      
      // Colores por tipo
      const coloresPorTipo = {
        ALTOS: doorColorHigh || 'Sin especificar',
        BAJOS: doorColorLow || 'Sin especificar',
        COLUMNAS: doorColorColumns || 'Sin especificar'
      };
      
      if (puertas.length > 0) {
        // Resumen de colores
        const totalAltos = puertas.filter(p => p.tipoMueble === 'ALTOS').reduce((sum, p) => sum + (p.doorQty * p.itemQuantity), 0);
        const totalBajos = puertas.filter(p => p.tipoMueble === 'BAJOS').reduce((sum, p) => sum + (p.doorQty * p.itemQuantity), 0);
        const totalColumnas = puertas.filter(p => p.tipoMueble === 'COLUMNAS').reduce((sum, p) => sum + (p.doorQty * p.itemQuantity), 0);
        const totalPuertas = totalAltos + totalBajos + totalColumnas;
        
        html += `
          <div class="section-title">🎨 RESUMEN DE PUERTAS POR COLOR</div>
          <div style="display:flex; gap:10px; margin-bottom:15px;">
            <div style="flex:1; background:#dbeafe; border:2px solid #3b82f6; padding:10px; border-radius:8px; text-align:center;">
              <div style="font-size:8px; color:#1e40af; font-weight:bold;">P. ALTOS</div>
              <div style="font-size:20px; font-weight:bold; color:#1e40af;">${totalAltos}</div>
              <div style="font-size:9px; color:#3b82f6; margin-top:4px;">Color: ${coloresPorTipo.ALTOS}</div>
            </div>
            <div style="flex:1; background:#ffedd5; border:2px solid #f97316; padding:10px; border-radius:8px; text-align:center;">
              <div style="font-size:8px; color:#c2410c; font-weight:bold;">P. BAJOS</div>
              <div style="font-size:20px; font-weight:bold; color:#c2410c;">${totalBajos}</div>
              <div style="font-size:9px; color:#f97316; margin-top:4px;">Color: ${coloresPorTipo.BAJOS}</div>
            </div>
            <div style="flex:1; background:#ede9fe; border:2px solid #8b5cf6; padding:10px; border-radius:8px; text-align:center;">
              <div style="font-size:8px; color:#6d28d9; font-weight:bold;">P. COLUMNAS</div>
              <div style="font-size:20px; font-weight:bold; color:#6d28d9;">${totalColumnas}</div>
              <div style="font-size:9px; color:#8b5cf6; margin-top:4px;">Color: ${coloresPorTipo.COLUMNAS}</div>
            </div>
          </div>
        `;
        
        // Tablas por tipo
        ['ALTOS', 'BAJOS', 'COLUMNAS'].forEach(tipo => {
          const puertasTipo = puertas.filter(p => p.tipoMueble === tipo);
          if (puertasTipo.length === 0) return;
          
          const subtotal = puertasTipo.reduce((sum, p) => sum + (p.doorQty * p.itemQuantity), 0);
          const bgColor = tipo === 'ALTOS' ? '#dbeafe' : tipo === 'BAJOS' ? '#ffedd5' : '#ede9fe';
          const borderColor = tipo === 'ALTOS' ? '#3b82f6' : tipo === 'BAJOS' ? '#f97316' : '#8b5cf6';
          
          html += `
            <div class="section-title" style="background:${borderColor};">🚪 PUERTAS ${tipo} - Color: ${coloresPorTipo[tipo]}</div>
            <table>
              <thead>
                <tr>
                  <th>Mueble</th>
                  <th class="text-center">Alto (cm)</th>
                  <th class="text-center">Ancho (cm)</th>
                  <th class="text-center">Veta</th>
                  <th class="text-center">Puertas/Mueble</th>
                  <th class="text-center">Total</th>
                </tr>
              </thead>
              <tbody>
          `;
          
          puertasTipo.forEach(p => {
            const total = p.doorQty * p.itemQuantity;
            html += `
              <tr class="avoid-break">
                <td class="font-bold">${p.productCode}</td>
                <td class="text-center">${p.doorHeight}</td>
                <td class="text-center">${p.doorWidth}</td>
                <td class="text-center" style="background:#d1fae5; color:#065f46; font-weight:bold;">↕ V</td>
                <td class="text-center">${p.doorQty}</td>
                <td class="text-center font-bold">${total}</td>
              </tr>
            `;
          });
          
          html += `
              <tr style="background:${bgColor};"><td colspan="5" class="text-right font-bold">SUBTOTAL ${tipo}:</td><td class="text-center font-bold">${subtotal}</td></tr>
              </tbody>
            </table>
          `;
        });
        
        html += `
          <div style="background:#d1fae5; padding:8px; border-radius:6px; font-size:9px; color:#065f46; margin-top:10px;">
            <strong>📐 VETA:</strong> Todas las puertas con veta VERTICAL (↕) - La veta sigue la dirección del ALTO
          </div>
          <div style="background:#fef3c7; padding:8px; border-radius:6px; font-size:9px; color:#92400e; margin-top:5px;">
            <strong>TOTAL GENERAL:</strong> ${totalPuertas} puertas${sideColor ? ` | <strong>Costados:</strong> ${sideColor}` : ''}
          </div>
        `;
      }
      
      // Herrajes estimados
      html += `
        <div class="section-title">HERRAJES ESTIMADOS</div>
        <table class="mini-table">
          <thead><tr><th>Herraje</th><th class="text-right">Cantidad</th></tr></thead>
          <tbody>
            <tr><td>Bisagras</td><td class="text-right font-bold">${calculateHerrajes?.bisagras || 0} uds</td></tr>
            <tr><td>Correderas (pares)</td><td class="text-right font-bold">${calculateHerrajes?.correderas || 0}</td></tr>
            <tr><td>Tiradores</td><td class="text-right font-bold">${calculateHerrajes?.tiradores || 0} uds</td></tr>
            <tr><td>Soportes de Baldas</td><td class="text-right font-bold">${calculateHerrajes?.soportesBaldas || 0} uds</td></tr>
            ${calculateHerrajes?.colgadores > 0 ? `<tr style="background:#fef3c7;"><td><strong>🪝 Colgadores (juegos)</strong></td><td class="text-right font-bold">${calculateHerrajes.colgadores} (= ${calculateHerrajes.colgadores * 2} uds)</td></tr>` : ''}
          </tbody>
        </table>
      `;
    }
    
    // Footer
    html += `
        <div class="footer">
          Documento generado por LUIGGI HOME ERP | ${fechaHoy} ${new Date().toLocaleTimeString('es-ES')} | Medidas en cm, grosor en mm
        </div>
      </body>
      </html>
    `;
    
    printWindow.document.write(html);
    printWindow.document.close();
    printWindow.onload = () => {
      printWindow.print();
    };
  };

  // Exportar archivo CSV para seccionadora
  const handleExportCSV = () => {
    if (!despieceData || !despieceData.items) {
      alert('No hay datos de despiece para exportar');
      return;
    }
    
    // CSV LIMPIO para seccionadora - SOLO datos de piezas
    // Sin cabeceras de cliente/expediente, sin resumen al final
    
    // Primero consolidar todas las piezas
    const allPieces = [];
    despieceData.items.forEach(item => {
      const itemQty = item.itemQuantity || 1;
      item.components?.forEach(comp => {
        const compValue = (field) => getComponentValue(item.productId, comp, field);
        const espesor = compValue('thickness') || 18;
        const materialBase = carcassMaterialName?.toUpperCase().replace(/\s+/g, '') || 'MELAMINA';
        const material = `40-${materialBase}${espesor < 10 ? '0' : ''}${espesor}`;
        const nombrePieza = comp.name || 'Pieza';
        const largo = compValue('length') || 0;
        const ancho = compValue('width') || 0;
        const cantidad = (compValue('quantity') || 1) * itemQty;
        const esPuerta = nombrePieza.toLowerCase().includes('puerta');
        const esVertical = nombrePieza.toLowerCase().includes('lateral') || 
                          nombrePieza.toLowerCase().includes('costado') ||
                          nombrePieza.toLowerCase().includes('vertical');
        const textura = (esPuerta || esVertical) ? 1 : 0;
        const codigo = `${item.productCode || ''}-${comp.id || nombrePieza.substring(0,3).toUpperCase()}`;
        const mueble = `${item.productCode} - ${item.productName || ''}`;
        
        allPieces.push({ material, espesor, nombrePieza, largo, ancho, cantidad, textura, codigo, mueble });
      });
    });
    
    // Consolidar piezas iguales (mismo nombre, dimensiones, grosor)
    const consolidatedCSV = {};
    allPieces.forEach(p => {
      const key = `${p.material}_${p.nombrePieza}_${p.largo}_${p.ancho}_${p.espesor}_${p.textura}`;
      if (!consolidatedCSV[key]) {
        consolidatedCSV[key] = { ...p, cantidad: p.cantidad };
      } else {
        consolidatedCSV[key].cantidad += p.cantidad;
      }
    });
    
    // Encabezados de la tabla de piezas
    let csvContent = "Material;Grosor;Nombre pieza;Largo pieza;Ancho pieza;Cantidad;Textura;Código;Mueble\n";
    
    // Generar filas consolidadas
    Object.values(consolidatedCSV).forEach(p => {
      csvContent += `${p.material};${p.espesor.toFixed(1).replace('.', ',')};${p.nombrePieza};${p.largo};${p.ancho};${p.cantidad};${p.textura};${p.codigo};${p.mueble}\n`;
    });
    
    // Descargar archivo - nombre incluye expediente y cliente para identificación
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    const nombreArchivo = `CORTE_${(editableExpedient || 'EXP').replace(/[^a-zA-Z0-9-]/g, '_')}_${(editableCustomerName || 'CLIENTE').replace(/[^a-zA-Z0-9]/g, '_').substring(0,20)}_${new Date().toISOString().split('T')[0]}.csv`;
    link.setAttribute('download', nombreArchivo);
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
    
    const fechaHoy = new Date().toISOString().split('T')[0];
    const horaHoy = new Date().toLocaleTimeString('es-ES');
    
    let xmlContent = '<?xml version="1.0" encoding="UTF-8"?>\n';
    xmlContent += '<CuttingList version="1.0">\n';
    xmlContent += `  <Header>\n`;
    xmlContent += `    <GeneratedDate>${fechaHoy}</GeneratedDate>\n`;
    xmlContent += `    <GeneratedTime>${horaHoy}</GeneratedTime>\n`;
    xmlContent += `    <Software>LUIGGI HOME ERP</Software>\n`;
    xmlContent += `  </Header>\n`;
    xmlContent += `  <Project>\n`;
    xmlContent += `    <Name>${editableExpedient || 'DESPIECE'}</Name>\n`;
    xmlContent += `    <Reference>${editableProjectRef || ''}</Reference>\n`;
    xmlContent += `    <Customer>${editableCustomerName || ''}</Customer>\n`;
    xmlContent += `    <Date>${fechaHoy}</Date>\n`;
    xmlContent += `    <TotalPieces>${despieceData.totalPieces || 0}</TotalPieces>\n`;
    xmlContent += `    <TotalArea>${despieceData.totalArea?.toFixed(3) || 0}</TotalArea>\n`;
    xmlContent += `    <BaseMaterial>${carcassMaterialName || 'Sin especificar'}</BaseMaterial>\n`;
    
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
          productName: item.productName,
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
        // Veta: PUERTAS siempre vertical, LATERALES/COSTADOS/VERTICALES también
        const esPuerta = piece.name?.toLowerCase().includes('puerta');
        const esVertical = piece.name?.toLowerCase().includes('lateral') || 
                          piece.name?.toLowerCase().includes('costado') ||
                          piece.name?.toLowerCase().includes('vertical');
        const tieneVeta = esPuerta || esVertical;
        
        xmlContent += `      <Part id="${partId++}">\n`;
        xmlContent += `        <Description>${desc}</Description>\n`;
        xmlContent += `        <FurnitureCode>${piece.productCode || ''}</FurnitureCode>\n`;
        xmlContent += `        <FurnitureName>${piece.productName || ''}</FurnitureName>\n`;
        xmlContent += `        <PieceName>${piece.name || ''}</PieceName>\n`;
        xmlContent += `        <Length>${compValue('length') || 0}</Length>\n`;
        xmlContent += `        <Width>${compValue('width') || 0}</Width>\n`;
        xmlContent += `        <Thickness>${compValue('thickness') || 18}</Thickness>\n`;
        xmlContent += `        <Quantity>${qty}</Quantity>\n`;
        xmlContent += `        <Grain>${tieneVeta ? '1' : '0'}</Grain>\n`;
        xmlContent += `        <GrainDirection>vertical</GrainDirection>\n`;
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
    const nombreArchivo = `CORTE_${(editableExpedient || 'EXP').replace(/[^a-zA-Z0-9-]/g, '_')}_${(editableCustomerName || 'CLIENTE').replace(/[^a-zA-Z0-9]/g, '_').substring(0,20)}_${new Date().toISOString().split('T')[0]}.xml`;
    link.setAttribute('download', nombreArchivo);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-[9999] flex items-center justify-center p-4 print:p-0 print:bg-white">
      <div className={`bg-white rounded-3xl shadow-2xl overflow-hidden flex flex-col transition-all duration-300 print:rounded-none print:shadow-none print:max-h-none ${
        isMaximized 
          ? 'w-full h-full max-w-none max-h-none rounded-none' 
          : 'w-full max-w-6xl max-h-[90vh]'
      }`}>
        {/* Header */}
        <div className="bg-indigo-950 text-white px-8 py-5 flex justify-between items-center shrink-0 print:hidden">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-orange-600 rounded-xl">
              <Scissors size={24} />
            </div>
            <div>
              <h2 className="text-xl font-black uppercase tracking-wider">Sistema de Despiece</h2>
              <p className="text-indigo-300 text-xs font-medium mt-0.5">Orden de Montaje y Lista de Corte</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button 
              onClick={() => setIsMaximized(!isMaximized)}
              className="p-2 hover:bg-white/10 rounded-xl transition-colors"
              title={isMaximized ? "Restaurar" : "Maximizar"}
            >
              {isMaximized ? <Minimize2 size={20} /> : <Maximize2 size={20} />}
            </button>
            <button 
              onClick={onClose}
              className="p-2 hover:bg-white/10 rounded-xl transition-colors"
            >
              <X size={24} />
            </button>
          </div>
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
                  onChange={(e) => setEditableCustomerName(e.target.value.toUpperCase())}
                  placeholder="Nombre del cliente..."
                  className="w-full text-sm font-bold text-indigo-900 bg-transparent outline-none border-b border-transparent hover:border-indigo-200 focus:border-orange-500 uppercase"
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
                  onChange={(e) => setEditableProjectRef(e.target.value.toUpperCase())}
                  placeholder="REF-001..."
                  className="w-full text-sm font-bold text-indigo-900 bg-transparent outline-none border-b border-transparent hover:border-indigo-200 focus:border-orange-500 uppercase"
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
                  onChange={(e) => setEditableExpedient(e.target.value.toUpperCase())}
                  placeholder="EXP-0001..."
                  className="w-full text-sm font-bold text-indigo-900 bg-transparent outline-none border-b border-transparent hover:border-indigo-200 focus:border-orange-500 uppercase"
                />
              </div>
            </div>
          </div>
        </div>

        {/* View Tabs */}
        <div className="bg-indigo-50 px-8 py-3 flex gap-2 border-b border-indigo-100 shrink-0 flex-wrap">
          <button
            onClick={() => setActiveView('montaje')}
            className={`px-5 py-2 rounded-xl font-black text-xs uppercase tracking-widest transition-all flex items-center gap-2 ${
              activeView === 'montaje' 
                ? 'bg-indigo-950 text-white shadow-lg' 
                : 'bg-white text-indigo-400 hover:bg-indigo-100 border border-indigo-100'
            }`}
          >
            <Package size={14} />
            Orden Montaje
          </button>
          <button
            onClick={() => setActiveView('corte')}
            className={`px-5 py-2 rounded-xl font-black text-xs uppercase tracking-widest transition-all flex items-center gap-2 ${
              activeView === 'corte' 
                ? 'bg-orange-600 text-white shadow-lg' 
                : 'bg-white text-indigo-400 hover:bg-indigo-100 border border-indigo-100'
            }`}
          >
            <Scissors size={14} />
            Lista Corte
          </button>
          <button
            onClick={() => setActiveView('bandas')}
            className={`px-5 py-2 rounded-xl font-black text-xs uppercase tracking-widest transition-all flex items-center gap-2 ${
              activeView === 'bandas' 
                ? 'bg-emerald-600 text-white shadow-lg' 
                : 'bg-white text-indigo-400 hover:bg-indigo-100 border border-indigo-100'
            }`}
          >
            <Grid3X3 size={14} />
            Bandas y Traseras
          </button>
          <button
            onClick={() => setActiveView('herrajes')}
            className={`px-5 py-2 rounded-xl font-black text-xs uppercase tracking-widest transition-all flex items-center gap-2 ${
              activeView === 'herrajes' 
                ? 'bg-amber-600 text-white shadow-lg' 
                : 'bg-white text-indigo-400 hover:bg-indigo-100 border border-indigo-100'
            }`}
          >
            <Wrench size={14} />
            Casco, Puerta y Herraje
          </button>
          <button
            onClick={() => setActiveView('puertas_proveedor')}
            className={`px-5 py-2 rounded-xl font-black text-xs uppercase tracking-widest transition-all flex items-center gap-2 ${
              activeView === 'puertas_proveedor' 
                ? 'bg-blue-600 text-white shadow-lg' 
                : 'bg-white text-blue-500 hover:bg-blue-50 border border-blue-200'
            }`}
            data-testid="tab-puertas-proveedor"
          >
            <Truck size={14} />
            Puertas Proveedor
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
                            <p className="text-xs text-indigo-300 uppercase font-bold">Cantidad</p>
                            <p className="font-black text-orange-600 text-lg">x{furniture.itemQuantity}</p>
                          </div>
                          {expandedItems[furniture.productId] ? <ChevronDown size={20} className="text-indigo-300" /> : <ChevronRight size={20} className="text-indigo-300" />}
                        </div>
                      </button>

                      {/* CASCO (Cabinet Body) Dimensions - Always visible */}
                      <div className="px-6 py-3 bg-gradient-to-r from-emerald-50 to-teal-50 border-y border-emerald-200">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <div className="p-2 bg-emerald-600 rounded-lg">
                              <Box size={18} className="text-white" />
                            </div>
                            <div>
                              <p className="text-[10px] font-black text-emerald-700 uppercase tracking-widest">Dimensiones del Casco Ensamblado</p>
                              <p className="text-[9px] text-emerald-500">Medidas exteriores del mueble montado</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-4">
                            <div className="text-center px-3 py-1.5 bg-white rounded-lg border border-emerald-200 shadow-sm">
                              <p className="text-[9px] text-emerald-500 uppercase font-bold">Ancho</p>
                              <p className="font-black text-emerald-800 text-lg">{furniture.originalWidth}</p>
                              <p className="text-[9px] text-emerald-400">cm</p>
                            </div>
                            <div className="text-emerald-300 font-bold">×</div>
                            <div className="text-center px-3 py-1.5 bg-white rounded-lg border border-emerald-200 shadow-sm">
                              <p className="text-[9px] text-emerald-500 uppercase font-bold">Alto</p>
                              <p className="font-black text-emerald-800 text-lg">{furniture.originalHeight}</p>
                              <p className="text-[9px] text-emerald-400">cm</p>
                            </div>
                            <div className="text-emerald-300 font-bold">×</div>
                            <div className="text-center px-3 py-1.5 bg-white rounded-lg border border-emerald-200 shadow-sm">
                              <p className="text-[9px] text-emerald-500 uppercase font-bold">Fondo</p>
                              <p className="font-black text-emerald-800 text-lg">{furniture.originalDepth}</p>
                              <p className="text-[9px] text-emerald-400">cm</p>
                            </div>
                            {/* Botón Copiar Dimensiones */}
                            <button
                              onClick={() => handleCopyCascoDimensions(furniture)}
                              className={`ml-3 px-3 py-2 rounded-lg text-xs font-bold uppercase tracking-wider flex items-center gap-2 transition-all ${
                                copiedCascoId === furniture.productId
                                  ? 'bg-emerald-600 text-white'
                                  : 'bg-emerald-100 text-emerald-700 hover:bg-emerald-200 border border-emerald-300'
                              }`}
                              title="Copiar dimensiones del casco"
                            >
                              {copiedCascoId === furniture.productId ? (
                                <>
                                  <Check size={14} />
                                  Copiado
                                </>
                              ) : (
                                <>
                                  <Copy size={14} />
                                  Copiar
                                </>
                              )}
                            </button>
                          </div>
                        </div>
                      </div>

                      {/* Components List */}
                      {expandedItems[furniture.productId] && (
                        <div className="border-t border-indigo-100">
                          <table className="w-full">
                            <thead className="bg-indigo-950 text-white text-xs font-black uppercase tracking-widest">
                              <tr>
                                <th className="px-6 py-3 text-left">Componente</th>
                                <th className="px-4 py-3 text-center">Código</th>
                                <th className="px-4 py-3 text-center">Material</th>
                                <th className="px-4 py-3 text-center">Largo (cm)</th>
                                <th className="px-4 py-3 text-center">Ancho (cm)</th>
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
                                    <span className="w-20 bg-slate-100 border border-indigo-200 rounded px-2 py-1 text-center text-sm font-bold inline-block">
                                      {getComponentValue(furniture.productId, comp, 'length')}
                                    </span>
                                  </td>
                                  <td className="px-4 py-3 text-center">
                                    <span className="w-20 bg-slate-100 border border-indigo-200 rounded px-2 py-1 text-center text-sm font-bold inline-block">
                                      {getComponentValue(furniture.productId, comp, 'width')}
                                    </span>
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
                        <th className="px-4 py-4 text-center">Largo (cm)</th>
                        <th className="px-4 py-4 text-center">Ancho (cm)</th>
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
                                {getComponentValue(furniture.productId, comp, 'length')}
                              </td>
                              <td className="px-4 py-3 text-center font-black text-indigo-900">
                                {getComponentValue(furniture.productId, comp, 'width')}
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

              {/* Vista Bandas y Traseras */}
              {activeView === 'bandas' && calculateBandasYTraseras && (
                <div className="space-y-6">
                  {/* Resumen General */}
                  <div className="grid grid-cols-3 gap-4">
                    <div className="bg-gradient-to-br from-emerald-500 to-emerald-700 rounded-2xl p-6 text-white">
                      <p className="text-emerald-100 text-xs font-bold uppercase tracking-widest mb-2">Canto Total</p>
                      <p className="text-4xl font-black">{calculateBandasYTraseras.totalCanto} <span className="text-lg">ml</span></p>
                    </div>
                    <div className="bg-gradient-to-br from-blue-500 to-blue-700 rounded-2xl p-6 text-white">
                      <p className="text-blue-100 text-xs font-bold uppercase tracking-widest mb-2">Tablero Casco</p>
                      <p className="text-4xl font-black">{calculateBandasYTraseras.cascoTotalArea} <span className="text-lg">m²</span></p>
                    </div>
                    <div className="bg-gradient-to-br from-amber-500 to-amber-700 rounded-2xl p-6 text-white">
                      <p className="text-amber-100 text-xs font-bold uppercase tracking-widest mb-2">Tablero Trasera</p>
                      <p className="text-4xl font-black">{calculateBandasYTraseras.traseraTotalArea} <span className="text-lg">m²</span></p>
                    </div>
                  </div>

                  {/* Detalle por mueble */}
                  <div className="bg-white border border-indigo-100 rounded-xl overflow-hidden">
                    <div className="bg-emerald-600 text-white px-6 py-3">
                      <h3 className="font-black uppercase tracking-widest text-sm">Detalle de Canto por Pieza</h3>
                    </div>
                    <table className="w-full">
                      <thead className="bg-emerald-50">
                        <tr className="text-xs font-black text-emerald-700 uppercase tracking-widest">
                          <th className="px-4 py-3 text-left">Mueble</th>
                          <th className="px-4 py-3 text-left">Pieza</th>
                          <th className="px-4 py-3 text-center">Largo (cm)</th>
                          <th className="px-4 py-3 text-center">Ancho (cm)</th>
                          <th className="px-4 py-3 text-center">Cant.</th>
                          <th className="px-4 py-3 text-center">Canto (ml)</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-emerald-50">
                        {despieceData.items.flatMap(furniture => 
                          furniture.components.map(comp => {
                            const qty = (comp.quantity || 1) * (furniture.itemQuantity || 1);
                            const { totalMl } = calculateCantoForComponent(comp, qty);
                            return (
                              <tr key={`${furniture.productId}-${comp.id}`} className="hover:bg-emerald-50/50">
                                <td className="px-4 py-2 font-bold text-indigo-900">{furniture.productCode}</td>
                                <td className="px-4 py-2 text-sm">{comp.name}</td>
                                <td className="px-4 py-2 text-center">{comp.length}</td>
                                <td className="px-4 py-2 text-center">{comp.width}</td>
                                <td className="px-4 py-2 text-center font-bold text-orange-600">{qty}</td>
                                <td className="px-4 py-2 text-center font-bold text-emerald-700">{totalMl.toFixed(2)}</td>
                              </tr>
                            );
                          })
                        )}
                      </tbody>
                      <tfoot className="bg-emerald-100">
                        <tr className="font-black text-emerald-800">
                          <td colSpan="5" className="px-4 py-3 text-right uppercase">Total Canto:</td>
                          <td className="px-4 py-3 text-center text-xl">{calculateBandasYTraseras.totalCanto} ml</td>
                        </tr>
                      </tfoot>
                    </table>
                  </div>

                  {/* Traseras por grosor */}
                  <div className="bg-white border border-indigo-100 rounded-xl overflow-hidden">
                    <div className="bg-amber-600 text-white px-6 py-3">
                      <h3 className="font-black uppercase tracking-widest text-sm">Resumen Traseras por Grosor</h3>
                    </div>
                    <div className="p-4 grid grid-cols-3 gap-4">
                      {Object.entries(calculateBandasYTraseras.traserasByThickness).map(([thickness, data]) => (
                        <div key={thickness} className="bg-amber-50 rounded-lg p-4 border border-amber-200">
                          <p className="text-amber-600 text-xs font-bold uppercase">{thickness}</p>
                          <p className="text-2xl font-black text-amber-800">{data.area.toFixed(3)} m²</p>
                          <p className="text-xs text-amber-500">{data.pieces} piezas</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Vista Casco, Puerta y Herraje */}
              {activeView === 'herrajes' && calculateHerrajes && (
                <div className="space-y-6">
                  {/* Resumen Herrajes */}
                  <div className="grid grid-cols-5 gap-4">
                    <div className="bg-gradient-to-br from-indigo-500 to-indigo-700 rounded-2xl p-6 text-white">
                      <p className="text-indigo-100 text-xs font-bold uppercase tracking-widest mb-2">Bisagras</p>
                      <p className="text-4xl font-black">{calculateHerrajes.bisagras}</p>
                      <p className="text-indigo-200 text-xs mt-1">unidades</p>
                    </div>
                    <div className="bg-gradient-to-br from-purple-500 to-purple-700 rounded-2xl p-6 text-white">
                      <p className="text-purple-100 text-xs font-bold uppercase tracking-widest mb-2">Correderas</p>
                      <p className="text-4xl font-black">{calculateHerrajes.correderas}</p>
                      <p className="text-purple-200 text-xs mt-1">pares</p>
                    </div>
                    <div className="bg-gradient-to-br from-pink-500 to-pink-700 rounded-2xl p-6 text-white">
                      <p className="text-pink-100 text-xs font-bold uppercase tracking-widest mb-2">Tiradores</p>
                      <p className="text-4xl font-black">{calculateHerrajes.tiradores}</p>
                      <p className="text-pink-200 text-xs mt-1">unidades</p>
                    </div>
                    <div className="bg-gradient-to-br from-teal-500 to-teal-700 rounded-2xl p-6 text-white">
                      <p className="text-teal-100 text-xs font-bold uppercase tracking-widest mb-2">Soportes Baldas</p>
                      <p className="text-4xl font-black">{calculateHerrajes.soportesBaldas}</p>
                      <p className="text-teal-200 text-xs mt-1">unidades</p>
                    </div>
                    {/* NUEVO: Colgadores para muebles ALTOS */}
                    {calculateHerrajes.colgadores > 0 && (
                      <div className="bg-gradient-to-br from-amber-500 to-orange-600 rounded-2xl p-6 text-white">
                        <p className="text-amber-100 text-xs font-bold uppercase tracking-widest mb-2">Colgadores</p>
                        <p className="text-4xl font-black">{calculateHerrajes.colgadores}</p>
                        <p className="text-amber-200 text-xs mt-1">juegos (2 uds/juego)</p>
                      </div>
                    )}
                  </div>

                  {/* ===================== SECCIÓN PUERTAS POR COLOR ===================== */}
                  {(() => {
                    // Función para detectar el tipo de mueble (ALTO, BAJO, COLUMNA)
                    // Soporta nomenclaturas de AMBAS bibliotecas: ZC y MV
                    const detectTipoMueble = (code, name) => {
                      const c = (code || '').toUpperCase();
                      const n = (name || '').toUpperCase();
                      
                      // ========== COLUMNAS (detectar primero - más específico) ==========
                      // MV: CD, CE, CF, CH, CHPC, CHGC, CHC, CHM, CHMG, CHMC, CHMCG, BOC
                      // ZC: C (código simple)
                      const columnaPrefixes = ['CD', 'CE', 'CF', 'CH', 'CHPC', 'CHGC', 'CHC', 'CHM', 'CHMG', 'CHMC', 'CHMCG', 'BOC'];
                      if (columnaPrefixes.some(prefix => c.startsWith(prefix))) {
                        return 'COLUMNAS';
                      }
                      // MV: MEDIA COLUMNA - M, MV, MPG, MVG, MPH, MPM, MGHM, MCHM
                      const mediaColumnaPrefixes = ['MGHM', 'MCHM', 'MPG', 'MVG', 'MPH', 'MPM'];
                      if (mediaColumnaPrefixes.some(prefix => c.startsWith(prefix))) {
                        return 'COLUMNAS';
                      }
                      // Código simple M seguido de número (MEDIA COLUMNA MV)
                      if (/^M\d/.test(c) || /^MV\d/.test(c)) {
                        return 'COLUMNAS';
                      }
                      // Por nombre
                      if (n.includes('COLUMNA') || n.includes('SEMICOLUMNA') || n.includes('MEDIACOLUMNA')) {
                        return 'COLUMNAS';
                      }
                      
                      // ========== ALTOS ==========
                      // MV: A, ASCE, ASC, AR, ARI, ARU, ARC, AD, AV, AE, AM, AMF, ACA, ACC, ASF, AT, ATP, AA, AC, ACP, ACPJ
                      // MV: L (ALTILLO), LV, S (SOBREENCIMERA), SV, SC, SVC, BOA, BOS
                      // ZC: A (código simple), 9A...
                      const altoPrefixes = ['ASCE', 'ASC', 'ARI', 'ARU', 'ARC', 'AD', 'AV', 'AE', 'AMF', 'AM', 'ACA', 'ACC', 'ASF', 'ATP', 'AT', 'AA', 'ACPJ', 'ACP', 'AC', 'AR'];
                      if (altoPrefixes.some(prefix => c.startsWith(prefix))) {
                        return 'ALTOS';
                      }
                      // Código simple A seguido de número
                      if (/^A\d/.test(c) || /^9A/.test(c)) {
                        return 'ALTOS';
                      }
                      // ALTILLOS y SOBREENCIMERAS (van como ALTOS)
                      const altilloSobrePrefixes = ['LD', 'LV', 'SVC', 'SV', 'SC', 'BOA', 'BOS'];
                      if (altilloSobrePrefixes.some(prefix => c.startsWith(prefix))) {
                        return 'ALTOS';
                      }
                      // Código simple L o S seguido de número
                      if (/^L\d/.test(c) || /^S\d/.test(c)) {
                        return 'ALTOS';
                      }
                      // Por nombre
                      if (n.includes('ALTO') || n.includes('ALTILLO') || n.includes('SOBREENCIMERA') || n.includes('SOBREM')) {
                        return 'ALTOS';
                      }
                      
                      // ========== BAJOS ==========
                      // MV: B, BF, BRI, BRU, BR, BH, BHC, BHZ, BHG, BT, BTP, BPC, BC, BCG, BGC, BCGF, BGF
                      // ZC: B (código simple), 9B...
                      const bajoPrefixes = ['BRI', 'BRU', 'BR', 'BHZ', 'BHG', 'BHC', 'BH', 'BTP', 'BT', 'BPC', 'BCGF', 'BCG', 'BGF', 'BGC', 'BC', 'BF'];
                      if (bajoPrefixes.some(prefix => c.startsWith(prefix))) {
                        return 'BAJOS';
                      }
                      // Código simple B seguido de número
                      if (/^B\d/.test(c) || /^9B/.test(c)) {
                        return 'BAJOS';
                      }
                      // Por nombre
                      if (n.includes('BAJO') || n.includes('FREGADERO') || n.includes('HORNO') && !n.includes('COLUMNA')) {
                        return 'BAJOS';
                      }
                      
                      // ========== PUERTAS SUELTAS (van como BAJOS por defecto) ==========
                      if (c.startsWith('P') || c.startsWith('PV') || c.startsWith('PVI') || c.startsWith('PVR')) {
                        return 'BAJOS';
                      }
                      
                      // Por defecto, BAJOS
                      return 'BAJOS';
                    };

                    // Extraer puertas de los componentes y clasificarlas
                    const puertas = despieceData.items.flatMap(furniture => {
                      const puertaComps = furniture.components?.filter(c => 
                        c.name?.toLowerCase().includes('puerta') || 
                        c.type?.toUpperCase() === 'PUERTA'
                      ) || [];
                      
                      const tipoMueble = detectTipoMueble(furniture.productCode, furniture.productName);
                      
                      return puertaComps.map(p => ({
                        muebleCode: furniture.productCode,
                        muebleName: furniture.productName,
                        doorHeight: p.length,
                        doorWidth: p.width,
                        doorQty: p.quantity || 1,
                        itemQty: furniture.itemQuantity || 1,
                        material: p.material,
                        tipoMueble: tipoMueble
                      }));
                    });

                    // Agrupar puertas por tipo
                    const puertasPorTipo = {
                      ALTOS: puertas.filter(p => p.tipoMueble === 'ALTOS'),
                      BAJOS: puertas.filter(p => p.tipoMueble === 'BAJOS'),
                      COLUMNAS: puertas.filter(p => p.tipoMueble === 'COLUMNAS')
                    };

                    // Colores asignados a cada tipo
                    const coloresPorTipo = {
                      ALTOS: doorColorHigh || 'Sin especificar',
                      BAJOS: doorColorLow || 'Sin especificar',
                      COLUMNAS: doorColorColumns || 'Sin especificar'
                    };

                    // Configuración de estilos por tipo
                    const estilosPorTipo = {
                      ALTOS: { bg: 'from-blue-500 to-indigo-600', bgLight: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200' },
                      BAJOS: { bg: 'from-orange-500 to-amber-600', bgLight: 'bg-orange-50', text: 'text-orange-700', border: 'border-orange-200' },
                      COLUMNAS: { bg: 'from-purple-500 to-violet-600', bgLight: 'bg-purple-50', text: 'text-purple-700', border: 'border-purple-200' }
                    };

                    const totalPuertas = puertas.reduce((sum, p) => sum + (p.doorQty * p.itemQty), 0);

                    if (puertas.length === 0) return null;

                    return (
                      <div className="space-y-4">
                        {/* Resumen de Colores */}
                        <div className="bg-white border-2 border-gray-200 rounded-xl overflow-hidden">
                          <div className="bg-gradient-to-r from-gray-700 to-gray-900 text-white px-6 py-3 flex justify-between items-center">
                            <h3 className="font-black uppercase tracking-widest text-sm">🎨 Resumen de Puertas por Color</h3>
                            <span className="bg-white/20 px-3 py-1 rounded-full text-sm font-bold">{totalPuertas} puertas total</span>
                          </div>
                          
                          {/* Tarjetas de resumen por tipo */}
                          <div className="grid grid-cols-3 gap-4 p-4">
                            {Object.entries(puertasPorTipo).map(([tipo, puertasTipo]) => {
                              const totalTipo = puertasTipo.reduce((sum, p) => sum + (p.doorQty * p.itemQty), 0);
                              const estilo = estilosPorTipo[tipo];
                              const color = coloresPorTipo[tipo];
                              
                              return (
                                <div key={tipo} className={`bg-gradient-to-br ${estilo.bg} rounded-xl p-4 text-white shadow-lg`}>
                                  <div className="flex items-center justify-between mb-2">
                                    <span className="text-xs font-bold uppercase tracking-widest opacity-80">P. {tipo}</span>
                                    <span className="text-2xl font-black">{totalTipo}</span>
                                  </div>
                                  <div className="bg-white/20 rounded-lg px-3 py-2 mt-2">
                                    <p className="text-xs font-bold uppercase tracking-wider opacity-90">Color:</p>
                                    <p className="text-sm font-black truncate" title={color}>{color}</p>
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </div>

                        {/* Leyenda de veta */}
                        <div className="bg-emerald-50 border border-emerald-200 rounded-xl px-4 py-2 flex items-center gap-4">
                          <span className="text-emerald-700 font-black text-xs uppercase tracking-widest">📐 Orientación de Veta:</span>
                          <span className="bg-emerald-600 text-white px-3 py-1 rounded-full text-xs font-bold flex items-center gap-1">
                            ↕ VERTICAL (por defecto)
                          </span>
                          <span className="text-emerald-600 text-xs">La veta sigue la dirección del ALTO de la puerta</span>
                        </div>

                        {/* Tablas detalladas por tipo */}
                        {Object.entries(puertasPorTipo).map(([tipo, puertasTipo]) => {
                          if (puertasTipo.length === 0) return null;
                          
                          const totalTipo = puertasTipo.reduce((sum, p) => sum + (p.doorQty * p.itemQty), 0);
                          const estilo = estilosPorTipo[tipo];
                          const color = coloresPorTipo[tipo];
                          
                          return (
                            <div key={tipo} className={`bg-white border-2 ${estilo.border} rounded-xl overflow-hidden`}>
                              <div className={`bg-gradient-to-r ${estilo.bg} text-white px-6 py-3 flex justify-between items-center`}>
                                <div className="flex items-center gap-3">
                                  <h3 className="font-black uppercase tracking-widest text-sm">🚪 Puertas {tipo}</h3>
                                  <span className="bg-white/30 px-3 py-1 rounded-full text-xs font-bold">
                                    Color: {color}
                                  </span>
                                </div>
                                <span className="bg-white/20 px-3 py-1 rounded-full text-sm font-bold">{totalTipo} puertas</span>
                              </div>
                              <table className="w-full">
                                <thead className={estilo.bgLight}>
                                  <tr className={`text-xs font-black ${estilo.text} uppercase tracking-widest`}>
                                    <th className="px-4 py-3 text-left">Mueble</th>
                                    <th className="px-4 py-3 text-left">Descripción</th>
                                    <th className="px-4 py-3 text-center">Alto (cm)</th>
                                    <th className="px-4 py-3 text-center">Ancho (cm)</th>
                                    <th className="px-4 py-3 text-center">Veta</th>
                                    <th className="px-4 py-3 text-center">Puertas/Mueble</th>
                                    <th className="px-4 py-3 text-center">Cant. Muebles</th>
                                    <th className="px-4 py-3 text-center">Total Puertas</th>
                                  </tr>
                                </thead>
                                <tbody className={`divide-y ${estilo.border.replace('border-', 'divide-')}`}>
                                  {puertasTipo.map((p, idx) => (
                                    <tr key={idx} className={`hover:${estilo.bgLight}`}>
                                      <td className={`px-4 py-3 font-bold ${estilo.text.replace('text-', 'text-').replace('-700', '-900')}`}>{p.muebleCode}</td>
                                      <td className={`px-4 py-3 text-sm ${estilo.text.replace('-700', '-600')}`}>{p.muebleName}</td>
                                      <td className={`px-4 py-3 text-center font-mono text-lg font-bold ${estilo.text.replace('-700', '-800')}`}>{p.doorHeight}</td>
                                      <td className={`px-4 py-3 text-center font-mono text-lg font-bold ${estilo.text.replace('-700', '-800')}`}>{p.doorWidth}</td>
                                      <td className="px-4 py-3 text-center">
                                        <span className="bg-emerald-100 text-emerald-700 px-2 py-1 rounded text-xs font-bold">↕ V</span>
                                      </td>
                                      <td className="px-4 py-3 text-center font-bold">{p.doorQty}</td>
                                      <td className="px-4 py-3 text-center font-bold text-indigo-600">{p.itemQty}</td>
                                      <td className={`px-4 py-3 text-center font-black ${estilo.text.replace('-700', '-600')} text-lg`}>{p.doorQty * p.itemQty}</td>
                                    </tr>
                                  ))}
                                </tbody>
                                <tfoot className={`${estilo.bgLight}`}>
                                  <tr className={`font-black ${estilo.text.replace('-700', '-900')}`}>
                                    <td colSpan="7" className="px-4 py-3 text-right uppercase">Subtotal Puertas {tipo}:</td>
                                    <td className="px-4 py-3 text-center text-xl">{totalTipo}</td>
                                  </tr>
                                </tfoot>
                              </table>
                            </div>
                          );
                        })}

                        {/* Nota informativa */}
                        <div className="bg-amber-50 border border-amber-200 rounded-xl px-6 py-3 text-xs text-amber-700">
                          <strong>Nota:</strong> Las dimensiones de puerta incluyen tolerancias aplicadas (-2mm alto, -3mm ancho).
                          Los colores mostrados corresponden a la configuración del presupuesto (P.Bajos, P.Altos, P.Colum).
                          {sideColor && <span className="ml-2 font-bold">Costados: {sideColor}</span>}
                        </div>
                      </div>
                    );
                  })()}

                  {/* Detalle por mueble */}
                  <div className="bg-white border border-indigo-100 rounded-xl overflow-hidden">
                    <div className="bg-indigo-950 text-white px-6 py-3">
                      <h3 className="font-black uppercase tracking-widest text-sm">Detalle Herrajes por Mueble</h3>
                    </div>
                    <table className="w-full">
                      <thead className="bg-indigo-50">
                        <tr className="text-xs font-black text-indigo-700 uppercase tracking-widest">
                          <th className="px-4 py-3 text-left">Mueble</th>
                          <th className="px-4 py-3 text-left">Descripción</th>
                          <th className="px-4 py-3 text-center">Dimensiones</th>
                          <th className="px-4 py-3 text-center">Cant.</th>
                          <th className="px-4 py-3 text-center">Bisagras</th>
                          <th className="px-4 py-3 text-center">Tiradores</th>
                          <th className="px-4 py-3 text-center">Baldas</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-indigo-50">
                        {despieceData.items.map(furniture => {
                          const numPuertas = (furniture.productName || '').toUpperCase().includes('2P') ? 2 : 1;
                          const height = furniture.originalHeight || 70;
                          const bisagrasPerPuerta = height > 100 ? 3 : 2;
                          const numBaldas = furniture.components?.filter(c => c.name?.toLowerCase().includes('balda')).reduce((acc, c) => acc + (c.quantity || 1), 0) || 0;
                          
                          return (
                            <tr key={furniture.productId} className="hover:bg-indigo-50/50">
                              <td className="px-4 py-3 font-bold text-indigo-900">{furniture.productCode}</td>
                              <td className="px-4 py-3 text-sm text-indigo-600">{furniture.productName}</td>
                              <td className="px-4 py-3 text-center text-xs">{furniture.originalWidth}×{furniture.originalHeight}×{furniture.originalDepth} cm</td>
                              <td className="px-4 py-3 text-center font-bold text-orange-600">{furniture.itemQuantity}</td>
                              <td className="px-4 py-3 text-center font-bold">{numPuertas * bisagrasPerPuerta * furniture.itemQuantity}</td>
                              <td className="px-4 py-3 text-center font-bold">{numPuertas * furniture.itemQuantity}</td>
                              <td className="px-4 py-3 text-center font-bold">{numBaldas * furniture.itemQuantity} <span className="text-xs text-indigo-400">({numBaldas * 4 * furniture.itemQuantity} soportes)</span></td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>

                  {/* Nota informativa */}
                  <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
                    <p className="text-amber-800 text-sm">
                      <strong>Nota:</strong> Los herrajes se calculan de forma estimada. Las bisagras se calculan según la altura del mueble (2 para ≤100cm, 3 para &gt;100cm). 
                      Las correderas se calculan para muebles con cajones/gavetas. Los <strong>colgadores</strong> se añaden automáticamente para muebles <strong>ALTOS</strong> (1 juego = 2 unidades por mueble).
                      Verificar según especificaciones del fabricante.
                    </p>
                  </div>
                </div>
              )}

              {/* ===================== NUEVA VISTA: PUERTAS PROVEEDOR ===================== */}
              {activeView === 'puertas_proveedor' && supplierDoors && (
                <div className="space-y-6" data-testid="puertas-proveedor-section">
                  {/* Header informativo */}
                  <div className="bg-gradient-to-r from-blue-600 to-blue-800 rounded-2xl p-6 text-white">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className="bg-white/20 rounded-full p-3">
                          <Truck size={28} />
                        </div>
                        <div>
                          <h2 className="text-xl font-black uppercase tracking-widest">Pedido Puertas para Proveedor</h2>
                          <p className="text-blue-200 text-sm mt-1">Edite las dimensiones y exporte la lista para enviar al proveedor de puertas</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-blue-200 text-xs font-bold uppercase">Total Puertas</p>
                        <p className="text-4xl font-black">{supplierDoors.reduce((sum, d) => sum + (parseInt(d.unidades) || 1), 0)}</p>
                      </div>
                    </div>
                  </div>

                  {/* Resumen por tipo */}
                  <div className="grid grid-cols-3 gap-4">
                    {['ALTOS', 'BAJOS', 'COLUMNAS'].map(tipo => {
                      const count = supplierDoors.filter(d => d.tipoMueble === tipo).reduce((sum, d) => sum + (parseInt(d.unidades) || 1), 0);
                      const color = tipo === 'ALTOS' ? doorColorHigh : tipo === 'BAJOS' ? doorColorLow : doorColorColumns;
                      const bgColor = tipo === 'ALTOS' ? 'from-blue-500 to-indigo-600' : tipo === 'BAJOS' ? 'from-orange-500 to-amber-600' : 'from-purple-500 to-violet-600';
                      
                      return (
                        <div key={tipo} className={`bg-gradient-to-br ${bgColor} rounded-xl p-4 text-white`}>
                          <p className="text-xs font-bold uppercase tracking-widest opacity-80">P. {tipo}</p>
                          <p className="text-3xl font-black">{count}</p>
                          <p className="text-xs mt-1 opacity-90">Color: {color || 'Sin definir'}</p>
                        </div>
                      );
                    })}
                  </div>

                  {/* Tabla editable de puertas */}
                  <div className="bg-white border-2 border-blue-200 rounded-xl overflow-hidden">
                    <div className="bg-blue-600 text-white px-6 py-3 flex justify-between items-center">
                      <h3 className="font-black uppercase tracking-widest text-sm">Lista de Puertas - Editable</h3>
                      <div className="flex gap-2">
                        <button
                          onClick={handleExportSupplierDoorsCSV}
                          className="bg-white/20 hover:bg-white/30 px-3 py-1 rounded-lg text-xs font-bold uppercase flex items-center gap-1"
                          data-testid="export-puertas-csv"
                        >
                          <Download size={12} />
                          CSV
                        </button>
                        <button
                          onClick={handleExportSupplierDoorsPDF}
                          className="bg-white/20 hover:bg-white/30 px-3 py-1 rounded-lg text-xs font-bold uppercase flex items-center gap-1"
                          data-testid="export-puertas-pdf"
                        >
                          <FileDown size={12} />
                          PDF
                        </button>
                      </div>
                    </div>
                    
                    <div className="max-h-[400px] overflow-y-auto">
                      <table className="w-full">
                        <thead className="bg-blue-50 sticky top-0">
                          <tr className="text-xs font-black text-blue-700 uppercase tracking-widest">
                            <th className="px-4 py-3 text-left">#</th>
                            <th className="px-4 py-3 text-left">Mueble</th>
                            <th className="px-4 py-3 text-left">Tipo</th>
                            <th className="px-4 py-3 text-left">Color</th>
                            <th className="px-4 py-3 text-center">Alto (cm)</th>
                            <th className="px-4 py-3 text-center">Ancho (cm)</th>
                            <th className="px-4 py-3 text-center">Veta</th>
                            <th className="px-4 py-3 text-center bg-orange-100 text-orange-700">Uds</th>
                            <th className="px-4 py-3 text-left">Observaciones</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-blue-100">
                          {supplierDoors.map((door, idx) => (
                            <tr key={door.id} className="hover:bg-blue-50/50">
                              <td className="px-4 py-2 text-xs text-gray-500 font-mono">{idx + 1}</td>
                              <td className="px-4 py-2">
                                <div className="font-bold text-indigo-900 text-sm">{door.muebleCode}</div>
                                <div className="text-xs text-gray-500 truncate max-w-[150px]" title={door.muebleName}>{door.muebleName}</div>
                              </td>
                              <td className="px-4 py-2">
                                <span className={`px-2 py-1 rounded text-xs font-bold ${
                                  door.tipoMueble === 'ALTOS' ? 'bg-blue-100 text-blue-700' :
                                  door.tipoMueble === 'BAJOS' ? 'bg-orange-100 text-orange-700' :
                                  'bg-purple-100 text-purple-700'
                                }`}>
                                  {door.tipoMueble}
                                </span>
                              </td>
                              <td className="px-4 py-2">
                                <input
                                  type="text"
                                  value={door.color}
                                  onChange={(e) => updateSupplierDoor(door.id, 'color', e.target.value)}
                                  className="w-full px-2 py-1 text-sm border border-gray-200 rounded focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
                                  data-testid={`door-color-${idx}`}
                                />
                              </td>
                              <td className="px-4 py-2">
                                <input
                                  type="number"
                                  value={door.alto}
                                  onChange={(e) => updateSupplierDoor(door.id, 'alto', parseFloat(e.target.value) || 0)}
                                  className="w-20 px-2 py-1 text-sm text-center font-bold border border-gray-200 rounded focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
                                  data-testid={`door-alto-${idx}`}
                                />
                              </td>
                              <td className="px-4 py-2">
                                <input
                                  type="number"
                                  value={door.ancho}
                                  onChange={(e) => updateSupplierDoor(door.id, 'ancho', parseFloat(e.target.value) || 0)}
                                  className="w-20 px-2 py-1 text-sm text-center font-bold border border-gray-200 rounded focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
                                  data-testid={`door-ancho-${idx}`}
                                />
                              </td>
                              <td className="px-4 py-2 text-center">
                                <select
                                  value={door.veta}
                                  onChange={(e) => updateSupplierDoor(door.id, 'veta', e.target.value)}
                                  className="px-2 py-1 text-xs font-bold border border-gray-200 rounded focus:border-blue-500 outline-none bg-white"
                                  data-testid={`door-veta-${idx}`}
                                >
                                  <option value="V">↕ Vertical</option>
                                  <option value="H">↔ Horizontal</option>
                                  <option value="N">— Sin veta</option>
                                </select>
                              </td>
                              <td className="px-4 py-2">
                                <input
                                  type="number"
                                  min="1"
                                  value={door.unidades || 1}
                                  onChange={(e) => updateSupplierDoor(door.id, 'unidades', parseInt(e.target.value) || 1)}
                                  className="w-16 px-2 py-1 text-sm text-center font-bold border border-orange-300 rounded focus:border-orange-500 focus:ring-1 focus:ring-orange-500 outline-none bg-orange-50"
                                  data-testid={`door-unidades-${idx}`}
                                />
                              </td>
                              <td className="px-4 py-2">
                                <input
                                  type="text"
                                  value={door.observaciones}
                                  onChange={(e) => updateSupplierDoor(door.id, 'observaciones', e.target.value)}
                                  placeholder="Notas..."
                                  className="w-full px-2 py-1 text-xs border border-gray-200 rounded focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
                                  data-testid={`door-obs-${idx}`}
                                />
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* Botones de exportación grandes */}
                  <div className="grid grid-cols-2 gap-4">
                    <button
                      onClick={handleExportSupplierDoorsCSV}
                      className="bg-emerald-600 hover:bg-emerald-700 text-white px-6 py-4 rounded-xl font-black text-sm uppercase tracking-widest flex items-center justify-center gap-3 transition-colors shadow-lg"
                      data-testid="export-puertas-csv-main"
                    >
                      <Download size={20} />
                      Exportar CSV para Proveedor
                    </button>
                    <button
                      onClick={handleExportSupplierDoorsPDF}
                      className="bg-red-600 hover:bg-red-700 text-white px-6 py-4 rounded-xl font-black text-sm uppercase tracking-widest flex items-center justify-center gap-3 transition-colors shadow-lg"
                      data-testid="export-puertas-pdf-main"
                    >
                      <FileDown size={20} />
                      Exportar PDF para Proveedor
                    </button>
                  </div>

                  {/* Nota informativa */}
                  <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
                    <p className="text-blue-800 text-sm">
                      <strong>Uso:</strong> Esta sección permite modificar las dimensiones de las puertas antes de enviar el pedido al proveedor.
                      Puede cambiar medidas, orientación de veta y añadir observaciones específicas para cada puerta.
                      El archivo exportado (CSV o PDF) está listo para enviar al proveedor de puertas.
                    </p>
                  </div>
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
          <div className="flex gap-2 flex-wrap">
            {despieceData && (
              <>
                <button
                  onClick={() => setShowBoardOptimizer(true)}
                  className="bg-emerald-700 text-white px-4 py-2 rounded-xl font-bold text-xs uppercase tracking-widest flex items-center gap-2 hover:bg-emerald-800 transition-colors shadow-lg"
                  title="Optimizar cortes de tableros"
                  data-testid="open-board-optimizer"
                >
                  <LayoutGrid size={14} />
                  Optimizar Tableros
                </button>
                <button
                  onClick={handleExportPDF}
                  className="bg-red-600 text-white px-4 py-2 rounded-xl font-bold text-xs uppercase tracking-widest flex items-center gap-2 hover:bg-red-700 transition-colors shadow-lg"
                  title="Exportar PDF A4"
                >
                  <FileDown size={14} />
                  PDF A4
                </button>
                <button
                  onClick={handleExportCSV}
                  className="bg-emerald-600 text-white px-4 py-2 rounded-xl font-bold text-xs uppercase tracking-widest flex items-center gap-2 hover:bg-emerald-700 transition-colors shadow-lg"
                  title="Exportar CSV para seccionadora"
                >
                  <Download size={14} />
                  CSV
                </button>
                <button
                  onClick={handleExportXML}
                  className="bg-blue-600 text-white px-4 py-2 rounded-xl font-bold text-xs uppercase tracking-widest flex items-center gap-2 hover:bg-blue-700 transition-colors shadow-lg"
                  title="Exportar XML (CutRite/Ardis)"
                >
                  <Download size={14} />
                  XML
                </button>
              </>
            )}
            <button
              onClick={handlePrint}
              className="bg-white border border-indigo-200 text-indigo-700 px-4 py-2 rounded-xl font-bold text-xs uppercase tracking-widest flex items-center gap-2 hover:bg-indigo-50 transition-colors"
            >
              <Printer size={14} />
              Imprimir
            </button>
            <button
              onClick={onClose}
              className="bg-indigo-950 text-white px-5 py-2 rounded-xl font-bold text-xs uppercase tracking-widest hover:bg-indigo-800 transition-colors"
            >
              Cerrar
            </button>
          </div>
        </div>

        {/* Board Optimizer Modal */}
        <BoardOptimizer
          isOpen={showBoardOptimizer}
          onClose={() => setShowBoardOptimizer(false)}
          despiecePieces={despieceData?.items?.flatMap(item => 
            item.components?.filter(c => c.material && c.length && c.width).map(c => ({
              name: `${item.productCode} - ${c.name}`,
              width: Math.round(c.length * 10), // cm to mm (length = largo)
              height: Math.round(c.width * 10), // cm to mm (width = ancho)
              quantity: c.quantity || 1,
              material: c.material
            }))
          ) || []}
          material={carcassMaterialName || 'Melamina'}
        />
      </div>
    </div>
  );
};

export default DespieceModal;
