import { ShoppingCart, Printer, Trash2, Save, LayoutPanelTop, Search, Plus, PanelLeftClose, PanelLeftOpen, PanelRightClose, PanelRightOpen, PanelBottomClose, PanelBottomOpen, FileText, ChevronDown, ChevronUp, Hash, Tag, Info, AlertCircle, Lock, Unlock, Palette, Box, Layers, Filter, PaintBucket, Keyboard, PenTool, Download, Scissors, CheckCircle, Paperclip, Mail, X, Upload, Image, FileImage, LayoutGrid, LayoutList, ArrowRightLeft } from 'lucide-react';
import React, { useMemo, useState, useCallback, useEffect, useRef } from 'react';
import { exportToPdf } from '../utils/pdfHelper';
import { generateBudgetPDF } from '../services/pdfGenerator';
import { DOOR_FINISHES, CabinetCategory } from '../constants';
import Logo from './Logo';
import DespieceModal from './DespieceModal';
import ClientSelector from './ClientSelector';
import CabinetIcon from './CabinetIcon';

const BudgetTable = ({ items, catalogs, activeCatalogIds, state, setState, onOpenManufacturing }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSeries, setSelectedSeries] = useState('TODAS');
  const [selectedCategory, setSelectedCategory] = useState('TODAS');
  const [isCatalogOpen, setIsCatalogOpen] = useState(true);
  const [isConfigOpen, setIsConfigOpen] = useState(true);
  const [sidebarWidth, setSidebarWidth] = useState(300);
  const [catalogHeight, setCatalogHeight] = useState(300);
  const [catalogWidth, setCatalogWidth] = useState(400);
  // Cargar preferencia de posición guardada
  const [catalogPosition, setCatalogPosition] = useState(() => {
    const saved = localStorage.getItem('luiggi_catalog_position');
    return saved || 'horizontal';
  });
  const [isDespieceOpen, setIsDespieceOpen] = useState(false);
  const [isConfirmOrderOpen, setIsConfirmOrderOpen] = useState(false);
  const [orderAttachments, setOrderAttachments] = useState([]);
  const [orderEmail, setOrderEmail] = useState('');
  const [orderNotes, setOrderNotes] = useState('');
  const [isSendingOrder, setIsSendingOrder] = useState(false);
  const [orderSent, setOrderSent] = useState(false);
  const isResizingSidebar = useRef(false);
  const isResizingCatalog = useRef(false);
  const isResizingCatalogWidth = useRef(false);

  // Guardar preferencia cuando cambie
  useEffect(() => {
    localStorage.setItem('luiggi_catalog_position', catalogPosition);
  }, [catalogPosition]);

  const allProducts = useMemo(() => {
    return catalogs
      .filter(c => activeCatalogIds.includes(c.id))
      .flatMap(c => c.products.map(p => ({ ...p, catalogId: c.id })));
  }, [catalogs, activeCatalogIds]);

  const uniqueCategories = useMemo(() => {
    const currentModuleProducts = allProducts.filter(p => 
      catalogs.find(c => c.id === p.catalogId)?.module === state.currentModule
    );
    const categories = new Set(currentModuleProducts.map(p => p.category || 'OTROS'));
    return Array.from(categories).sort();
  }, [allProducts, state.currentModule, catalogs]);

  const uniqueSeries = useMemo(() => {
    const currentModuleProducts = allProducts.filter(p => 
      catalogs.find(c => c.id === p.catalogId)?.module === state.currentModule
    );
    // Filter by category if one is selected
    const categoryFilteredProducts = selectedCategory === 'TODAS' 
      ? currentModuleProducts 
      : currentModuleProducts.filter(p => (p.category || 'OTROS') === selectedCategory);
    const series = new Set(categoryFilteredProducts.map(p => p.series || 'GENERAL'));
    return Array.from(series).sort();
  }, [allProducts, state.currentModule, catalogs, selectedCategory]);

  const sortedItems = useMemo(() => {
    return [...items].sort((a, b) => {
      if (a.isManual) return 1;
      if (b.isManual) return -1;

      const pA = allProducts.find(p => p.id === a.productId);
      const pB = allProducts.find(p => p.id === b.productId);
      if (!pA) return 1;
      if (!pB) return -1;
      const orderMap = {
        [CabinetCategory.COLUMNA]: 1, [CabinetCategory.SEMICOLUMNA]: 2,
        [CabinetCategory.ALTO]: 3, [CabinetCategory.BAJO]: 4, [CabinetCategory.ELECTRO]: 5
      };
      return (orderMap[pA.category] || 99) - (orderMap[pB.category] || 99);
    });
  }, [items, allProducts]);

  // Función helper para detectar tipo de herraje del código
  const getHardwareType = useCallback((code) => {
    const c = code?.toUpperCase() || '';
    // HK: códigos APABL/AVABL sin HL/HS/HF al final
    if ((c.includes('APABL') || c.includes('AVABL') || c.includes('APVBL') || c.includes('AVVBL')) && 
        !c.includes('HL') && !c.includes('HS') && !c.includes('HF')) {
      return 'HK';
    }
    if (c.includes('HS')) return 'HS';
    if (c.includes('HL')) return 'HL';
    if (c.includes('HF')) return 'HF';
    return null;
  }, []);

  // Función helper para detectar tipo de mueble especial
  const getSpecialType = useCallback((code) => {
    const c = code?.toUpperCase() || '';
    if (c.includes('AM') || c.includes('BM')) return 'MICRO';
    if (c.includes('CHM')) return 'HORNO+MICRO';
    if (c.includes('CH') || c.includes('BH')) return 'HORNO';
    if (c.includes('BP')) return 'PLACA';
    if (c.includes('BF')) return 'FREG';
    if (c.includes('AT')) return 'TERMO';
    if (c.includes('AE')) return 'ESCURRE';
    return null;
  }, []);

  const filteredCatalog = useMemo(() => {
    const q = searchQuery.toLowerCase().trim();
    
    // Orden según el catálogo PDF TARIFA-TECNICA-ZONACOCINAS
    // 1. ALTOS (primero en parte 1)
    // 2. BAJOS (parte 2, páginas 1-27)
    // 3. SEMICOLUMNAS (parte 2, páginas 33-77)
    // 4. COLUMNAS (parte 2, páginas 78-125)
    const categoryOrder = {
      'ALTO': 1, 'ALTOS': 1,
      'BAJO': 2, 'BAJOS': 2,
      'SEMICOLUMNA': 3, 'SEMICOLUMNAS': 3,
      'COLUMNA': 4, 'COLUMNAS': 4,
      'ELECTRO': 5, 'ELECTRODOMESTICOS': 5,
      'PUERTAS': 6, 'PUERTAS Y VITRINAS': 6,
      'ACCESORIO': 7, 'ACCESORIOS': 7,
      'OTRO': 8, 'OTROS': 8
    };

    // Mapeo de términos de búsqueda para herrajes
    const hardwareSearchTerms = {
      'hk': 'HK-TOP', 'hk-top': 'HK-TOP', 'hktop': 'HK-TOP', 'aventos hk': 'HK-TOP',
      'hs': 'HS', 'servo': 'SERVO', 'servo-drive': 'SERVO', 'servodrive': 'SERVO',
      'hl': 'HL', 'lift': 'LIFT',
      'hf': 'HF', 'free fold': 'FREE', 'freefold': 'FREE', 'free-fold': 'FREE'
    };

    // Mapeo de términos de búsqueda para tipos especiales
    const specialSearchTerms = {
      'micro': ['AM', 'BM'], 'microondas': ['AM', 'BM'],
      'horno': ['CH', 'BH', 'CHM'], 'oven': ['CH', 'BH', 'CHM'],
      'placa': ['BP'], 'vitro': ['BP'], 'vitroceramica': ['BP'],
      'freg': ['BF'], 'fregadero': ['BF'], 'sink': ['BF'],
      'termo': ['AT'], 'calentador': ['AT'],
      'escurre': ['AE'], 'escurreplatos': ['AE']
    };
    
    const filtered = allProducts.filter(p => {
      const codeUpper = p.code?.toUpperCase() || '';
      const nameUpper = p.name?.toUpperCase() || '';
      const nameLower = p.name?.toLowerCase() || '';
      
      // Búsqueda estándar por código y nombre
      let matchesSearch = codeUpper.toLowerCase().includes(q) || nameLower.includes(q);
      
      // Si no coincide, buscar por términos de herraje
      if (!matchesSearch && q) {
        const hardwareText = hardwareSearchTerms[q];
        if (hardwareText) {
          // Buscar en código O en nombre
          if (codeUpper.includes(hardwareText) || nameUpper.includes(hardwareText)) {
            matchesSearch = true;
          }
        }
        
        // Buscar por tipo especial (horno, micro, etc.)
        if (!matchesSearch) {
          for (const [term, codes] of Object.entries(specialSearchTerms)) {
            if (term.includes(q) || q.includes(term)) {
              if (codes.some(c => codeUpper.includes(c))) {
                matchesSearch = true;
                break;
              }
            }
          }
        }
      }
      
      const isCorrectModule = catalogs.find(c => c.id === p.catalogId)?.module === state.currentModule;
      const matchesSeries = selectedSeries === 'TODAS' || (p.series || 'GENERAL') === selectedSeries;
      const matchesCategory = selectedCategory === 'TODAS' || (p.category || 'OTROS') === selectedCategory;
      return matchesSearch && isCorrectModule && matchesSeries && matchesCategory;
    });
    
    // Ordenar por categoría y luego por código
    return filtered.sort((a, b) => {
      const catA = categoryOrder[a.category?.toUpperCase()] || 99;
      const catB = categoryOrder[b.category?.toUpperCase()] || 99;
      if (catA !== catB) return catA - catB;
      // Dentro de la misma categoría, ordenar por código
      return a.code.localeCompare(b.code);
    });
  }, [allProducts, searchQuery, state.currentModule, catalogs, selectedSeries, selectedCategory]);

  const budgetKey = state.currentModule === 'montada' ? 'budgetItemsMontada' : 'budgetItemsDespiece';

  const addItemToBudget = (product) => {
    const newItem = {
      id: Math.random().toString(36).substr(2, 9),
      productId: product.id,
      catalogId: product.catalogId,
      quantity: 1,
      customReference: product.code,
      customWidth: Number(product.width),
      customHeight: Number(product.height),
      customDepth: Number(product.depth),
      openingDirection: 'Derecha',
      notes: '',
      hasVigaCut: false  // Nuevo campo para incremento de corte viga
    };
    setState(prev => ({ ...prev, [budgetKey]: [...prev[budgetKey], newItem] }));
  };

  const addManualItemToBudget = () => {
    const newItem = {
      id: Math.random().toString(36).substr(2, 9),
      productId: `MANUAL-${Date.now()}`,
      catalogId: 'manual',
      quantity: 1,
      customReference: '', 
      customWidth: 0, customHeight: 0, customDepth: 0,
      openingDirection: 'N/A',
      notes: '',
      isManual: true,
      manualDescription: '',
      hasVigaCut: false,
      manualPoints: 0
    };
    setState(prev => ({ ...prev, [budgetKey]: [...prev[budgetKey], newItem] }));
  };

  const updateItem = (id, field, value) => {
    setState(prev => ({
      ...prev,
      [budgetKey]: prev[budgetKey].map(item => item.id === id ? { ...item, [field]: value } : item)
    }));
  };

  const removeItem = (id) => {
    setState(prev => ({ ...prev, [budgetKey]: prev[budgetKey].filter(item => item.id !== id) }));
  };

  const carcassMaterialName = useMemo(() => {
    return state.carcassMaterials.find(m => m.id === state.selectedCarcassMaterialId)?.name || 'No seleccionado';
  }, [state.carcassMaterials, state.selectedCarcassMaterialId]);

  const calculateLineDetails = useCallback((item, product) => {
     const pointValue = state.currentModule === 'montada' ? state.pointValueMontada : state.pointValueDespiece;
     let usedPoints = 0;
     let carcassCost = 0;
     let cutsCost = 0;
     let cuts = [];
     let finalProductName = "";

     if (item.isManual) {
         usedPoints = item.manualPoints || 0;
         finalProductName = item.manualDescription || "Concepto Manual";
     } else {
         if (!product) return { total: 0, breakdown: '', hasExtras: false, usedPoints: 0 };
         
         const currentFinish = item.specificFinish || state.globalFinish;
         const finishObj = DOOR_FINISHES.find(f => f.name === currentFinish) || DOOR_FINISHES[0];
         
         let productBasePoints = 100;
         if (typeof product.points === 'number') productBasePoints = product.points;
         else if (typeof product.points === 'object' && product.points !== null) productBasePoints = product.points.Z1 || 100;
         
         usedPoints = product.zonePoints?.[finishObj.group] ?? productBasePoints;
         finalProductName = product.name;

         if (Number(item.customWidth) !== Number(product.width)) { cutsCost += state.specialIncrementWidth; cuts.push('Ancho'); }
         if (Number(item.customHeight) !== Number(product.height)) { cutsCost += state.specialIncrementHeight; cuts.push('Alto'); }
         if (Number(item.customDepth) !== Number(product.depth)) { cutsCost += state.specialIncrementDepth; cuts.push('Fondo'); }

         const selectedMaterial = state.carcassMaterials.find(m => m.id === state.selectedCarcassMaterialId);
         carcassCost = selectedMaterial?.fixedIncrement || 0;
     }
     
     // Añadir incremento por corte de viga si está marcado
     const vigaCost = item.hasVigaCut ? (state.vigaCutIncrement || 0) : 0;
     
     const pointsCost = usedPoints * pointValue;
     const unitPrice = pointsCost + cutsCost + carcassCost + vigaCost;
     
     const discountPct = state.currentUser?.commercialDiscount || 0;
     // Las líneas manuales NO se afectan por el cambio de modo PVP/COSTO
     const discountFactor = (state.showDistributorPrice && !item.isManual) ? (1 - discountPct / 100) : 1;
     
     const finalPrice = (unitPrice * item.quantity) * discountFactor;

     const breakdown = `
DESGLOSE DE PRECIO:
-------------------
• Puntos Base: ${usedPoints} pts
• Valor Punto: ${pointValue.toFixed(2)} €/pt
  (Subtotal Mueble: ${pointsCost.toFixed(2)}€)

${!item.isManual ? `EXTRAS APLICADOS:
• Armazón: +${carcassCost.toFixed(2)}€
• Cortes Especiales (${cuts.length}): +${cutsCost.toFixed(2)}€${vigaCost > 0 ? `
• Corte Viga: +${vigaCost.toFixed(2)}€` : ''}` : '• (Artículo Manual / Neto)'}

PRECIO UNITARIO: ${unitPrice.toFixed(2)}€
CANTIDAD: x${item.quantity}
${state.showDistributorPrice ? `DTO. COMERCIAL: -${discountPct}%` : ''}
`.trim();

     return { total: finalPrice, breakdown, hasExtras: (carcassCost > 0 || cutsCost > 0 || vigaCost > 0), usedPoints, vigaCost };
  }, [state.globalFinish, state.currentModule, state.pointValueMontada, state.pointValueDespiece, state.specialIncrementWidth, state.specialIncrementHeight, state.specialIncrementDepth, state.showDistributorPrice, state.currentUser?.commercialDiscount, state.selectedCarcassMaterialId, state.carcassMaterials, state.vigaCutIncrement]);


  const total = useMemo(() => sortedItems.reduce((acc, item) => {
    const product = allProducts.find(p => p.id === item.productId);
    return acc + calculateLineDetails(item, product).total;
  }, 0), [sortedItems, allProducts, calculateLineDetails]);

  const handleSaveBudget = async () => {
    if (!state.currentUser) return;
    if (items.length === 0) {
      alert("La mesa de trabajo está vacía. Añade muebles antes de archivar.");
      return;
    }

    const itemsMontadaCopy = [...state.budgetItemsMontada];
    const itemsDespieceCopy = [...state.budgetItemsDespiece];

    try {
      // Verificar si ya existe un presupuesto con este número
      const checkResponse = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/projects/check-budget-number/${encodeURIComponent(state.budgetNumber)}`);
      const checkData = await checkResponse.json();
      
      let shouldOverwrite = false;
      let existingProjectId = null;
      
      if (checkData.exists) {
        const userChoice = window.confirm(
          `⚠️ El número de presupuesto "${state.budgetNumber}" ya existe.\n\n` +
          `Cliente: ${checkData.customerName}\n` +
          `Fecha: ${new Date(checkData.createdAt).toLocaleDateString('es-ES')}\n\n` +
          `¿Desea SOBRESCRIBIR el presupuesto existente?\n\n` +
          `(Pulse "Cancelar" para guardar con un número diferente)`
        );
        
        if (userChoice) {
          shouldOverwrite = true;
          existingProjectId = checkData.projectId;
        } else {
          // Obtener siguiente número disponible
          const expResponse = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/expedient/next`);
          const expData = await expResponse.json();
          if (expData.success) {
            setState(prev => ({ ...prev, budgetNumber: expData.expedient }));
            alert(`Se usará el número: ${expData.expedient}\n\nVuelva a pulsar GUARDAR para confirmar.`);
            return;
          }
        }
      }

      // GUARDAR EN BACKEND - Persistir en MongoDB
      const projectData = {
        budgetNumber: state.budgetNumber,
        customerName: state.customerName || 'Cliente sin nombre',
        customerAddress: state.customerAddress || '',
        internalReference: state.internalReference || '',
        itemsMontada: itemsMontadaCopy,
        itemsDespiece: itemsDespieceCopy,
        doorColorLow: state.doorColorLow || '',
        doorColorHigh: state.doorColorHigh || '',
        doorColorColumns: state.doorColorColumns || '',
        sideColor: state.sideColor || '',
        selectedCarcassMaterialId: state.selectedCarcassMaterialId,
        status: 'activo',
        totalPvp: total // Incluir el total del presupuesto
      };

      let response;
      if (shouldOverwrite && existingProjectId) {
        // Actualizar proyecto existente
        response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/projects/${existingProjectId}?user_id=${state.currentUser.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(projectData)
        });
      } else {
        // Crear nuevo proyecto
        response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/projects?user_id=${state.currentUser.id}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(projectData)
        });
      }

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Error al guardar el proyecto');
      }

      const savedProject = await response.json();

      // Obtener siguiente número de expediente
      let nextBudgetNumber = state.budgetNumber;
      try {
        const expResponse = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/expedient/next`);
        const expData = await expResponse.json();
        if (expData.success) {
          nextBudgetNumber = expData.expedient;
        }
      } catch (err) {
        console.error('Error getting next expedient:', err);
      }

      // Crear proyecto local para la lista
      const newProject = {
        id: savedProject.id,
        name: savedProject.customerName,
        date: savedProject.createdAt,
        totalPvp: total,
        itemsMontada: itemsMontadaCopy,
        itemsDespiece: itemsDespieceCopy,
        finish: state.globalFinish,
        carcassColorLow: carcassMaterialName,
        carcassColorHigh: carcassMaterialName,
        doorColorLow: state.doorColorLow,
        doorColorHigh: state.doorColorHigh,
        doorColorColumns: state.doorColorColumns,
        sideColor: state.sideColor,
        module: state.currentModule,
        customerName: state.customerName,
        customerAddress: state.customerAddress,
        budgetNumber: state.budgetNumber,
        internalReference: state.internalReference,
        userId: state.currentUser.id
      };

      setState(prev => ({
        ...prev,
        projects: [newProject, ...prev.projects],
        budgetNumber: nextBudgetNumber,
        budgetItemsMontada: [],
        budgetItemsDespiece: [],
        customerName: '',
        internalReference: '',
        customerAddress: '',
        doorColorLow: '',
        doorColorHigh: '',
        doorColorColumns: '',
        sideColor: ''
      }));

      // Preguntar si quiere crear oportunidad en CRM
      if (state.currentUser?.canAccessCRM && total > 0) {
        // Determinar el tipo de módulo basado en qué pestaña tiene más elementos
        const montadaCount = state.budgetItemsMontada?.length || 0;
        const despieceCount = state.budgetItemsDespiece?.length || 0;
        const moduleType = despieceCount > 0 && montadaCount === 0 ? 'despiece' : 'montada';
        const moduleLabel = moduleType === 'montada' ? 'COCINA MONTADA' : 'COCINA DESPIECE';
        
        const createOpp = window.confirm(
          `✅ EXPEDIENTE ${newProject.budgetNumber} GUARDADO EN BASE DE DATOS.\n\n¿Desea crear una OPORTUNIDAD de ${moduleLabel} en el CRM?\n\nCliente: ${newProject.customerName}\nValor: ${total.toLocaleString('es-ES', { style: 'currency', currency: 'EUR' })}`
        );
        
        if (createOpp) {
          try {
            // Create contact first
            const contactRes = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/crm/contacts`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                name: newProject.customerName || 'Cliente sin nombre',
                type: 'lead',
                source: 'presupuesto',
                notes: `Contacto creado desde presupuesto ${newProject.budgetNumber}`
              })
            });
            const contact = await contactRes.json();

            // Create opportunity with businessType: cocina and moduleType
            await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/crm/opportunities`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                title: `Presupuesto ${moduleLabel} - ${newProject.customerName}`,
                description: `Presupuesto generado automáticamente\nAcabado: ${newProject.finish}\nMódulo: ${newProject.module}`,
                contactId: contact.id,
                contactName: contact.name,
                value: total,
                probability: 50,
                stage: 'proposal',
                tags: ['presupuesto', 'auto', 'cocina', moduleType],
                assignedTo: state.currentUser.id,
                linkedProjectId: newProject.id,
                linkedProjectNumber: newProject.budgetNumber,
                businessType: 'cocina',
                moduleType: moduleType
              })
            });
            
            alert(`✅ Oportunidad de ${moduleLabel} creada en CRM para ${newProject.customerName}`);
          } catch (err) {
            console.error('Error creating CRM opportunity:', err);
            alert('Presupuesto guardado, pero hubo un error al crear la oportunidad CRM.');
          }
        }
      } else {
        alert(`✅ EXPEDIENTE ${newProject.budgetNumber} GUARDADO CORRECTAMENTE.`);
      }
    } catch (error) {
      console.error('Error saving project:', error);
      alert(`❌ Error al guardar el proyecto: ${error.message}`);
    }
  };

  // Función para confirmar pedido y enviar por email
  const handleConfirmOrder = async () => {
    if (!orderEmail) {
      alert('Por favor, introduce un email de destino');
      return;
    }
    
    setIsSendingOrder(true);
    try {
      // Preparar datos del formulario con archivos
      const formData = new FormData();
      formData.append('budgetNumber', state.budgetNumber);
      formData.append('customerName', state.customerName || 'Sin nombre');
      formData.append('customerAddress', state.customerAddress || '');
      formData.append('totalAmount', total.toFixed(2));
      formData.append('email', orderEmail);
      formData.append('notes', orderNotes);
      
      // Especificaciones de acabados
      formData.append('doorColorLow', state.doorColorLow || '');
      formData.append('doorColorHigh', state.doorColorHigh || '');
      formData.append('doorColorColumns', state.doorColorColumns || '');
      formData.append('sideColor', state.sideColor || '');
      formData.append('carcassColor', carcassMaterialName || '');
      formData.append('globalFinish', state.globalFinish || '');
      formData.append('distributorName', state.currentUser?.clientName || '');
      
      formData.append('items', JSON.stringify(sortedItems.map(item => {
        const product = allProducts.find(p => p.id === item.productId);
        const details = calculateLineDetails(item, product);
        return {
          code: product?.code || item.productCode || item.customReference || 'Manual',
          name: product?.name || item.productName || item.manualDescription || 'Artículo manual',
          quantity: item.quantity,
          price: details.total
        };
      })));
      
      // Adjuntar archivos
      orderAttachments.forEach((file, index) => {
        formData.append(`attachment_${index}`, file);
      });
      
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/orders/confirm`, {
        method: 'POST',
        body: formData
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Error al enviar la confirmación');
      }
      
      setOrderSent(true);
      setTimeout(() => {
        setIsConfirmOrderOpen(false);
        setOrderSent(false);
        setOrderAttachments([]);
        setOrderNotes('');
      }, 2000);
      
    } catch (error) {
      console.error('Error confirming order:', error);
      alert(`Error al confirmar pedido: ${error.message}`);
    } finally {
      setIsSendingOrder(false);
    }
  };

  // Manejar archivos adjuntos
  const handleAttachmentChange = (e) => {
    const files = Array.from(e.target.files);
    setOrderAttachments(prev => [...prev, ...files]);
  };

  const removeAttachment = (index) => {
    setOrderAttachments(prev => prev.filter((_, i) => i !== index));
  };

  useEffect(() => {
    const onMouseMove = (e) => {
      if (isResizingSidebar.current) setSidebarWidth(Math.max(250, Math.min(600, e.clientX - 80)));
      if (isResizingCatalog.current) setCatalogHeight(Math.max(120, Math.min(600, window.innerHeight - e.clientY)));
      if (isResizingCatalogWidth.current) setCatalogWidth(Math.max(280, Math.min(800, window.innerWidth - e.clientX)));
    };
    const onMouseUp = () => { 
      isResizingSidebar.current = false;
      isResizingCatalog.current = false; 
      isResizingCatalogWidth.current = false;
    };
    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
    return () => { window.removeEventListener('mousemove', onMouseMove); window.removeEventListener('mouseup', onMouseUp); };
  }, []);

  const hasMontada = state.currentUser?.allowedModules?.includes('montada');
  const hasDespiece = state.currentUser?.allowedModules?.includes('despiece');

  return (
    <div className="flex flex-col h-full bg-indigo-50/10 overflow-hidden relative">
      <div className="px-8 py-3 border-b border-indigo-100 bg-white flex justify-between items-center z-30 no-print shadow-sm">
        <div className="flex items-center gap-4">
           <div className="flex bg-indigo-50 p-1 rounded-xl border border-indigo-100">
              {hasMontada && (
                <button 
                  onClick={() => setState(p => ({...p, currentModule: 'montada'}))} 
                  className={`px-5 py-2 rounded-lg text-[9px] font-black uppercase tracking-widest transition-all ${state.currentModule === 'montada' ? 'bg-orange-600 text-white shadow-lg' : 'text-indigo-400 hover:bg-white/50'}`}
                >
                  Cocina Montada
                </button>
              )}
              {hasDespiece && (
                <button 
                  onClick={() => setState(p => ({...p, currentModule: 'despiece'}))} 
                  className={`px-5 py-2 rounded-lg text-[9px] font-black uppercase tracking-widest transition-all ${state.currentModule === 'despiece' ? 'bg-indigo-700 text-white shadow-lg' : 'text-indigo-400 hover:bg-white/50'}`}
                >
                  Cocina Despiece
                </button>
              )}
           </div>
           
           <button onClick={() => setIsConfigOpen(!isConfigOpen)} className={`p-2.5 rounded-lg transition-all ${isConfigOpen ? 'bg-indigo-950 text-white shadow-md' : 'bg-white border text-indigo-200'}`}>
              {isConfigOpen ? <PanelLeftClose size={18} /> : <PanelLeftOpen size={18} />}
           </button>
        </div>
        
        <div className="flex gap-3 items-center">
          {/* Pestaña ARMARIOS - Solo para usuarios con permiso */}
          {(state.currentUser?.isAdmin || state.currentUser?.canAccessArmarios) && (
            <button 
              onClick={() => setState(p => ({...p, currentTab: 'armarios'}))} 
              className="flex items-center gap-2 px-4 py-2 bg-purple-100 hover:bg-purple-200 rounded-xl border border-purple-200 transition-all"
              data-testid="armarios-tab-btn"
            >
              <Box size={14} className="text-purple-600" />
              <span className="text-[9px] font-black text-purple-700 uppercase tracking-widest">Armarios</span>
            </button>
          )}

          <button onClick={addManualItemToBudget} className="bg-white border-2 border-indigo-100 text-indigo-800 px-4 py-2 rounded-xl font-black uppercase text-[9px] tracking-widest flex items-center gap-2 hover:bg-indigo-50 transition-all shadow-sm">
             <Keyboard size={14}/> LÍNEA MANUAL
          </button>

          <button 
            onClick={() => {
              const carcassMat = state.carcassMaterials?.find(m => m.id === state.selectedCarcassMaterialId);
              generateBudgetPDF({
                budgetNumber: state.budgetNumber,
                customerName: state.customerName,
                customerAddress: state.customerAddress,
                internalReference: state.internalReference,
                itemsMontada: state.budgetItemsMontada,
                itemsDespiece: state.budgetItemsDespiece,
                pointValueMontada: state.pointValueMontada,
                pointValueDespiece: state.pointValueDespiece,
                doorColorLow: state.doorColorLow,
                doorColorHigh: state.doorColorHigh,
                doorColorColumns: state.doorColorColumns,
                sideColor: state.sideColor,
                carcassMaterialName: carcassMat?.name || 'No especificado',
                brandColor: state.brandColor,
                logo: state.logo,
                companyName: state.currentUser?.clientName || 'LUIGGI HOME',
                globalFinish: state.globalFinish,
                allProducts: allProducts,
                calculateLineDetails: calculateLineDetails
              });
            }}
            className="bg-green-600 text-white px-5 py-2.5 rounded-xl font-black uppercase text-[9px] tracking-widest flex items-center gap-2 hover:bg-green-700 transition-all shadow-lg"
            data-testid="export-pdf-btn"
          >
            <Download size={16}/> EXPORTAR PDF
          </button>

          {/* Botón Confirmar Pedido - Siempre visible */}
          <button 
            onClick={() => setIsConfirmOrderOpen(true)}
            className="bg-emerald-600 text-white px-5 py-2.5 rounded-xl font-black uppercase text-[9px] tracking-widest flex items-center gap-2 hover:bg-emerald-700 transition-all shadow-lg border-2 border-emerald-400"
            data-testid="confirm-order-btn"
          >
            <CheckCircle size={16}/> CONFIRMAR PEDIDO
          </button>

          {state.currentUser?.canViewTechnicalDespiece && (
            <button 
              onClick={() => setIsDespieceOpen(true)} 
              className="bg-orange-600 text-white px-6 py-2.5 rounded-xl font-black uppercase text-[9px] tracking-widest flex items-center gap-3 hover:bg-orange-700 transition-all shadow-xl"
              data-testid="despiece-btn"
            >
              <Scissors size={16}/> DESPIECE
            </button>
          )}

          {state.currentUser?.canViewTechnicalDespiece && (
            <button onClick={onOpenManufacturing} className="bg-indigo-950 text-white px-6 py-2.5 rounded-xl font-black uppercase text-[9px] tracking-widest flex items-center gap-3 hover:bg-indigo-800 transition-all shadow-xl">
              <FileText size={16}/> INFORME INDUSTRIAL
            </button>
          )}

          <div className="flex items-center gap-2">
            <button 
              onClick={() => setState(prev => ({ ...prev, showDistributorPrice: !prev.showDistributorPrice }))}
              title={state.showDistributorPrice ? "Cerrar Candado (Mostrar PVP al Cliente)" : "Abrir Candado (Mostrar Costo Distribuidor)"}
              className={`p-3.5 rounded-xl transition-all flex flex-col items-center justify-center gap-1 border shadow-lg ${state.showDistributorPrice ? 'bg-orange-600 border-orange-600 text-white animate-pulse' : 'bg-indigo-50 border-indigo-100 text-indigo-900 hover:bg-indigo-100'}`}
            >
               {state.showDistributorPrice ? <Unlock size={20} /> : <Lock size={20} />}
               <span className="text-[7px] font-black uppercase tracking-widest">{state.showDistributorPrice ? 'COSTO' : 'PVP'}</span>
            </button>

            <div className={`px-8 py-2.5 rounded-xl text-right border-b-4 shadow-xl transition-colors duration-500 ${state.showDistributorPrice ? 'bg-orange-600 border-white/20 text-white' : 'bg-indigo-950 border-orange-600 text-white'}`}>
               <p className={`text-[7px] font-black uppercase mb-1 ${state.showDistributorPrice ? 'text-white/70' : 'text-indigo-300'}`}>
                 TOTAL {state.showDistributorPrice ? 'NETO FÁBRICA' : 'VENTA PÚBLICO'} (IVA NO INC.)
               </p>
               <p className={`text-2xl font-black italic tracking-tighter ${state.showDistributorPrice ? 'text-white' : 'text-orange-600'}`}>
                 {total.toLocaleString('es-ES', { style: 'currency', currency: 'EUR' })}
               </p>
            </div>
          </div>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        <aside style={{ width: isConfigOpen ? sidebarWidth : 0 }} className="bg-white border-r border-indigo-50 flex flex-col no-print transition-all duration-300 relative overflow-hidden shadow-inner">
           <div onMouseDown={() => { isResizingSidebar.current = true; }} className="absolute top-0 right-0 w-1.5 h-full cursor-ew-resize hover:bg-orange-600 z-50"></div>
           <div className="p-4 space-y-3 overflow-y-auto scrollbar-thin">
              <section className="space-y-2">
                 <h4 className="text-[8px] font-black text-indigo-300 uppercase tracking-widest italic flex items-center gap-1">📂 DATOS EXPEDIENTE</h4>
                 <div className="space-y-1.5">
                    <div className="relative flex gap-1">
                      <div className="relative flex-1">
                        <Hash className="absolute left-2 top-1/2 -translate-y-1/2 text-indigo-200" size={10} />
                        <input type="text" value={state.budgetNumber} onChange={e => setState(p => ({...p, budgetNumber: e.target.value}))} placeholder="Nº Expediente" className="w-full bg-indigo-50/30 border border-indigo-50 rounded-lg py-2 pl-7 pr-2 text-[9px] font-black outline-none focus:border-orange-500 uppercase" />
                      </div>
                      {/* Botón AUTO solo visible para Admin */}
                      {state.currentUser?.isAdmin && (
                        <button 
                          onClick={async () => {
                            try {
                              const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/expedient/next`);
                              const data = await response.json();
                              if (data.success) {
                                setState(p => ({...p, budgetNumber: data.expedient}));
                              }
                            } catch (err) {
                              console.error('Error getting expedient:', err);
                            }
                          }}
                          className="bg-orange-600 hover:bg-orange-700 text-white px-2 rounded-lg text-[8px] font-black transition-colors"
                          title="Generar número de expediente automático"
                        >
                          AUTO
                        </button>
                      )}
                    </div>
                    <div className="relative">
                      <Tag className="absolute left-2 top-1/2 -translate-y-1/2 text-indigo-200" size={10} />
                      <input type="text" value={state.internalReference} onChange={e => setState(p => ({...p, internalReference: e.target.value.toUpperCase()}))} placeholder="Ref. Proyecto" className="w-full bg-indigo-50/30 border border-indigo-50 rounded-lg py-2 pl-7 pr-2 text-[9px] font-black outline-none focus:border-orange-500 uppercase" />
                    </div>
                    {/* Selector de Cliente con búsqueda y permisos */}
                    <ClientSelector
                      value={state.customerName}
                      onChange={(name) => setState(p => ({...p, customerName: name}))}
                      currentUser={state.currentUser}
                      onClientSelected={(client) => {
                        // Guardar también el ID del cliente seleccionado
                        setState(p => ({
                          ...p, 
                          customerName: client.nombre,
                          selectedClientId: client.id,
                          customerPhone: client.telefono || '',
                          customerEmail: client.email || ''
                        }));
                      }}
                      placeholder="Buscar o crear cliente..."
                    />
                 </div>
              </section>
              
              <section className="space-y-1.5 pt-2 border-t border-orange-100">
                 <h4 className="text-[9px] font-black text-orange-600 uppercase tracking-widest">🎨 ACABADO / TARIFA</h4>
                 <select 
                   className="w-full bg-orange-50 text-orange-900 border-2 border-orange-200 rounded-xl p-2 text-[10px] font-black outline-none cursor-pointer focus:border-orange-500" 
                   value={state.globalFinish} 
                   onChange={e => setState(p => ({...p, globalFinish: e.target.value}))}
                 >
                   {DOOR_FINISHES.map(f => (
                     <option key={f.name} value={f.name}>
                       {f.name}
                     </option>
                   ))}
                 </select>
                 <div className="flex justify-center">
                   <span className="px-4 py-1 bg-orange-500 text-white rounded-full text-[10px] font-black uppercase tracking-wider shadow">
                     TARIFA {DOOR_FINISHES.find(f => f.name === state.globalFinish)?.group || 'Z1'}
                   </span>
                 </div>
              </section>
              
              <section className="space-y-1.5 pt-2 border-t border-orange-100">
                 <h4 className="text-[9px] font-black text-orange-600 uppercase tracking-widest">🏗️ ARMAZÓN</h4>
                 <select className="w-full bg-orange-50 text-orange-900 border-2 border-orange-200 rounded-xl p-2 text-[9px] font-black outline-none cursor-pointer focus:border-orange-500" value={state.selectedCarcassMaterialId} onChange={e => setState(p => ({...p, selectedCarcassMaterialId: e.target.value}))}>
                    {state.carcassMaterials.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
                 </select>
              </section>

              {/* Botón para añadir línea manual */}
              <section className="pt-2 border-t border-orange-100">
                <button 
                  onClick={addManualItemToBudget}
                  className="w-full bg-emerald-500 hover:bg-emerald-600 text-white py-2 rounded-xl font-black uppercase text-[9px] tracking-widest flex items-center justify-center gap-2 transition-colors"
                  data-testid="add-manual-line-btn"
                >
                  <Plus size={14}/> LÍNEA MANUAL
                </button>
                <p className="text-[7px] text-orange-400 italic mt-0.5 text-center">Añadir concepto libre</p>
              </section>

              <section className="space-y-1.5 pt-2 border-t border-orange-100">
                 <h4 className="text-[9px] font-black text-orange-600 uppercase tracking-widest">✏️ COLORES ESPECÍFICOS</h4>
                 <div className="space-y-1">
                    <input type="text" value={state.doorColorLow} onChange={e => setState(p => ({...p, doorColorLow: e.target.value}))} className="w-full bg-orange-50 border-2 border-orange-200 rounded-xl p-1.5 text-[9px] font-bold outline-none focus:border-orange-500 text-orange-900" placeholder="P. Bajos" />
                    <input type="text" value={state.doorColorHigh} onChange={e => setState(p => ({...p, doorColorHigh: e.target.value}))} className="w-full bg-orange-50 border-2 border-orange-200 rounded-xl p-1.5 text-[9px] font-bold outline-none focus:border-orange-500 text-orange-900" placeholder="P. Altos" />
                    <input type="text" value={state.doorColorColumns} onChange={e => setState(p => ({...p, doorColorColumns: e.target.value}))} className="w-full bg-orange-50 border-2 border-orange-200 rounded-xl p-1.5 text-[9px] font-bold outline-none focus:border-orange-500 text-orange-900" placeholder="P. Columnas" />
                    <input type="text" value={state.sideColor} onChange={e => setState(p => ({...p, sideColor: e.target.value}))} className="w-full bg-orange-50 border-2 border-orange-200 rounded-xl p-1.5 text-[9px] font-bold outline-none focus:border-orange-500 text-orange-900" placeholder="Costados" />
                 </div>
              </section>

              <div className="pt-3 space-y-1.5">
                 {items.length > 0 ? (
                   <>
                     <button onClick={handleSaveBudget} className="w-full bg-orange-500 text-white py-2 rounded-xl font-black uppercase text-[9px] tracking-widest flex items-center justify-center gap-2 hover:bg-orange-600 transition-all">
                        <Save size={14}/> GUARDAR
                     </button>
                     <button 
                       onClick={() => setIsConfirmOrderOpen(true)} 
                       className="w-full bg-emerald-500 text-white py-2 rounded-xl font-black uppercase text-[9px] tracking-widest flex items-center justify-center gap-2 hover:bg-emerald-600 transition-all"
                       data-testid="confirm-order-btn"
                     >
                        <CheckCircle size={14}/> CONFIRMAR PEDIDO
                     </button>
                   </>
                 ) : (
                   <div className="p-1.5 bg-orange-50 rounded-xl border border-orange-200 flex items-center gap-2">
                      <AlertCircle size={12} className="text-orange-400" />
                      <span className="text-[7px] font-black text-orange-400 uppercase leading-tight">Añade artículos</span>
                   </div>
                 )}
                 <button onClick={() => exportToPdf('budget-pdf', `EXP_${state.budgetNumber}`)} className="w-full bg-indigo-800 text-white py-2 rounded-xl font-black uppercase text-[9px] tracking-widest flex items-center justify-center gap-2 hover:bg-indigo-900 transition-all">
                    <Printer size={14}/> IMPRIMIR
                 </button>
              </div>
           </div>
        </aside>

        <div 
          className="flex-1 overflow-y-auto p-12 pb-64 bg-indigo-50/30 scrollbar-thin transition-all duration-300"
          style={{ 
            paddingRight: catalogPosition === 'vertical' && isCatalogOpen ? catalogWidth + 48 : 48,
            paddingBottom: catalogPosition === 'horizontal' && isCatalogOpen ? catalogHeight + 48 : 256
          }}
        >
          {items.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center opacity-20">
               <FileText size={120} strokeWidth={0.5} className="text-indigo-900 mb-6" />
               <p className="text-sm font-black uppercase tracking-[0.5em] text-indigo-950">Presupuesto vacío</p>
               <p className="text-[10px] font-bold text-indigo-400 mt-2 italic uppercase">Selecciona artículos de la librería inferior o añade líneas manuales</p>
            </div>
          ) : (
            <div id="budget-pdf" className="w-[210mm] mx-auto bg-white shadow-2xl p-[10mm] flex flex-col rounded-sm border-t-[8px] border-indigo-950">
               <div className="flex justify-between items-center mb-2 border-b border-indigo-50 pb-3 h-16">
                  <div className="h-full flex items-center">
                    <Logo className="h-full w-auto" customLogo={state.logo} />
                  </div>
                  <div className="text-right">
                     <h1 className="text-2xl font-black italic uppercase text-indigo-950 tracking-tighter leading-none">PRESUPUESTO TÉCNICO</h1>
                     <div className="mt-2 space-y-0.5">
                        <p className="text-[9px] font-black text-indigo-300 uppercase">Nº EXP: <span className="text-indigo-950">{state.budgetNumber}</span></p>
                        {state.internalReference && <p className="text-[8px] font-black text-indigo-300 uppercase">REF: <span className="text-orange-600">{state.internalReference}</span></p>}
                        {state.customerName && <p className="text-[8px] font-black text-indigo-950 uppercase italic tracking-widest">CLIENTE: {state.customerName}</p>}
                     </div>
                  </div>
               </div>

               <div className="bg-indigo-50/30 p-2 rounded-xl border border-indigo-100 mb-2 space-y-2">
                 <div className="grid grid-cols-3 gap-2">
                    <div className="flex items-center gap-1.5">
                       <div className="p-1 bg-indigo-950 text-white rounded-md"><Palette size={12}/></div>
                       <div>
                          <p className="text-[6px] font-black uppercase text-indigo-300 tracking-widest leading-none mb-0.5">ACABADO GLOBAL</p>
                          <p className="text-[8px] font-black text-indigo-950 uppercase italic leading-none">{state.globalFinish}</p>
                       </div>
                    </div>
                    <div className="flex items-center gap-1.5">
                       <div className="p-1 bg-orange-600 text-white rounded-md"><Box size={12}/></div>
                       <div>
                          <p className="text-[6px] font-black uppercase text-indigo-300 tracking-widest leading-none mb-0.5">MATERIAL ARMAZÓN</p>
                          <p className="text-[8px] font-black text-indigo-950 uppercase italic leading-none">{carcassMaterialName}</p>
                       </div>
                    </div>
                    <div className="flex items-center gap-1.5">
                       <div className="p-1 bg-indigo-700 text-white rounded-md"><Layers size={12}/></div>
                       <div>
                          <p className="text-[6px] font-black uppercase text-indigo-300 tracking-widest leading-none mb-0.5">COSTADOS / VISTOS</p>
                          <p className="text-[8px] font-black text-indigo-950 uppercase italic leading-none">{state.sideColor || 'Igual a Frentes'}</p>
                       </div>
                    </div>
                 </div>

                 {(state.doorColorLow || state.doorColorHigh || state.doorColorColumns) && (
                   <div className="grid grid-cols-4 gap-2 pt-2 border-t border-indigo-100">
                      {state.doorColorLow && (
                        <div className="flex items-center gap-1.5">
                          <PaintBucket size={10} className="text-indigo-400"/>
                          <div>
                            <p className="text-[5px] font-black uppercase text-indigo-300 leading-none">P. BAJOS</p>
                            <p className="text-[7px] font-black text-indigo-900 uppercase leading-none">{state.doorColorLow}</p>
                          </div>
                        </div>
                      )}
                      {state.doorColorHigh && (
                        <div className="flex items-center gap-1.5">
                          <PaintBucket size={10} className="text-indigo-400"/>
                          <div>
                            <p className="text-[5px] font-black uppercase text-indigo-300 leading-none">P. ALTOS</p>
                            <p className="text-[7px] font-black text-indigo-900 uppercase leading-none">{state.doorColorHigh}</p>
                          </div>
                        </div>
                      )}
                      {state.doorColorColumns && (
                        <div className="flex items-center gap-1.5">
                          <PaintBucket size={10} className="text-indigo-400"/>
                          <div>
                            <p className="text-[5px] font-black uppercase text-indigo-300 leading-none">P. COLUMNAS</p>
                            <p className="text-[7px] font-black text-indigo-900 uppercase leading-none">{state.doorColorColumns}</p>
                          </div>
                        </div>
                      )}
                   </div>
                 )}
               </div>

               <div className="flex-1 mb-4">
                  {/* Header - usando flex en lugar de grid para mejor control */}
                  <div className="flex items-center px-2 py-2 bg-indigo-950 text-white rounded-t-lg text-[6px] font-black uppercase tracking-widest italic">
                     <div className="w-7 text-center shrink-0">V</div>
                     <div className="w-8 text-center shrink-0">UD</div>
                     <div className="w-20 shrink-0">REF</div>
                     <div className="flex-1 min-w-[150px]">DESCRIPCIÓN</div>
                     <div className="w-11 text-center shrink-0">AN</div>
                     <div className="w-11 text-center shrink-0">AL</div>
                     <div className="w-11 text-center shrink-0">FO</div>
                     <div className="w-8 text-center shrink-0">AP</div>
                     <div className="w-20 shrink-0">OBS</div>
                     <div className="w-20 text-right shrink-0 pr-2">€</div>
                     <div className="w-6 shrink-0 no-print"></div>
                  </div>
                  <div className="divide-y divide-indigo-50 border-x border-b border-indigo-50 rounded-b-lg overflow-hidden">
                  {sortedItems.map((item) => {
                    let product = allProducts.find(p => p.id === item.productId);
                    let isUnknown = false;

                    if (item.isManual) {
                        product = {
                            id: item.productId,
                            code: 'MANUAL',
                            name: item.manualDescription || 'CONCEPTO MANUAL',
                            category: CabinetCategory.MANUAL,
                            series: 'MANUAL',
                            visualType: 'HUECO',
                            width: item.customWidth || 0,
                            height: item.customHeight || 0,
                            depth: item.customDepth || 0,
                            points: item.manualPoints || 0,
                            zonePoints: {},
                            manufacturer: 'Manual'
                        };
                    } else if (item.fromAI) {
                        // Producto detectado por IA - usar los datos del item
                        product = {
                            id: item.productId,
                            code: item.productCode || 'IA-DETECT',
                            name: item.productName || 'MUEBLE DETECTADO POR IA',
                            category: item.category || 'IA',
                            series: 'IA',
                            visualType: 'HUECO',
                            width: item.customWidth || item.width || 600,
                            height: item.customHeight || item.height || 70,
                            depth: item.customDepth || item.depth || 58,
                            points: item.points || 0,
                            zonePoints: item.zonePoints || {},
                            manufacturer: 'IA Lab'
                        };
                    } else if (!product) {
                        isUnknown = true;
                        product = { id: item.productId, code: item.productCode || item.customReference || '???', name: item.productName || 'REFERENCIA DESCONOCIDA (DESCATALOGADO)', category: CabinetCategory.MANUAL, series: 'DESCONOCIDO', visualType: 'HUECO', width: item.customWidth || item.width || 0, height: item.customHeight || item.height || 0, depth: item.customDepth || item.depth || 0, points: 0, zonePoints: {}, manufacturer: 'Unknown' };
                    }

                    const { total: price, breakdown, hasExtras } = calculateLineDetails(item, product);
                    const specialCuts = [];
                    if (!item.isManual) {
                        if (Number(item.customWidth) !== Number(product.width)) specialCuts.push("ANCHO");
                        if (Number(item.customHeight) !== Number(product.height)) specialCuts.push("ALTO");
                        if (Number(item.customDepth) !== Number(product.depth)) specialCuts.push("FONDO");
                        if (item.hasVigaCut) specialCuts.push("VIGA");
                    }
                    const specialLabel = specialCuts.length > 0 ? `+ CORTE ${specialCuts.join('/')}` : '';
                    
                    // Detectar si es mueble de 2 puertas (no necesita selector D/I)
                    const isTwoDoor = product.name?.toLowerCase().includes('2 puerta') || 
                                      product.name?.toLowerCase().includes('2p') ||
                                      product.code?.includes('2P') ||
                                      product.visualType === '2P';

                    return (
                      <div key={item.id} className={`flex items-center px-2 py-2 text-indigo-950 hover:bg-indigo-50/50 transition-colors ${isUnknown ? 'bg-red-50 border-l-4 border-red-500' : item.fromAI ? 'bg-purple-50/50 border-l-4 border-purple-500' : item.isManual ? 'bg-emerald-50/30' : specialCuts.length > 0 ? 'bg-orange-50/20' : ''}`}>
                         {/* Corte Viga - Primera columna */}
                         <div className="w-7 shrink-0 flex justify-center">
                            {!item.isManual ? (
                              <button
                                onClick={() => updateItem(item.id, 'hasVigaCut', !item.hasVigaCut)}
                                className={`no-print p-1 rounded transition-all ${
                                  item.hasVigaCut 
                                    ? 'bg-orange-600 text-white shadow-md' 
                                    : 'bg-slate-100 text-slate-300 hover:bg-orange-100 hover:text-orange-600'
                                }`}
                                title={item.hasVigaCut ? 'Quitar corte de viga' : 'Añadir corte de viga (+€)'}
                              >
                                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round">
                                  <path d="M4 20L20 4" />
                                  <path d="M2 12h4" />
                                  <path d="M18 12h4" />
                                </svg>
                              </button>
                            ) : (
                              <span className="text-[8px] text-emerald-500 font-black">M</span>
                            )}
                            {item.hasVigaCut && <span className="print-only text-[6px] font-black text-orange-600">V</span>}
                         </div>

                         {/* Cantidad */}
                         <div className="w-8 shrink-0 text-center">
                            <input type="number" min="1" value={item.quantity} onChange={e => updateItem(item.id, 'quantity', parseInt(e.target.value) || 1)} className="w-7 bg-transparent text-center font-black text-[10px] italic outline-none no-print" />
                            <span className="print-only font-black text-[10px] italic">x{item.quantity}</span>
                         </div>
                         
                         {/* Referencia - Más corta */}
                         <div className="w-20 shrink-0 pr-1">
                            {item.isManual ? (
                                <>
                                  <input 
                                    type="text" 
                                    value={item.customReference || ''} 
                                    onChange={e => updateItem(item.id, 'customReference', e.target.value)} 
                                    placeholder="REF" 
                                    className="w-full bg-white border border-emerald-200 rounded px-1 py-0.5 text-[7px] font-black uppercase text-indigo-800 outline-none focus:border-emerald-500 no-print placeholder-indigo-300" 
                                  />
                                  <span className="print-only text-[7px] font-black uppercase italic text-indigo-900">{item.customReference}</span>
                                </>
                            ) : (
                                <>
                                    <input type="text" value={item.customReference ?? product.code} onChange={e => updateItem(item.id, 'customReference', e.target.value)} className="w-full bg-indigo-50/50 border border-indigo-100 rounded px-1 py-0.5 text-[7px] font-black uppercase italic text-indigo-900 outline-none no-print focus:border-orange-500" />
                                    <span className="print-only text-[7px] font-black uppercase italic text-indigo-900">{item.customReference ?? product.code}</span>
                                </>
                            )}
                         </div>

                         {/* Descripción - para líneas manuales, ocupar todo el espacio de descripción + medidas */}
                         {item.isManual ? (
                             <>
                               {/* Descripción extendida que ocupa: flex-1 + w-9*3 + w-8 = todo el espacio hasta PTS */}
                               <div className="flex-1 min-w-[180px] flex items-center gap-2">
                                  <input 
                                      type="text" 
                                      value={item.manualDescription || ''} 
                                      onChange={e => updateItem(item.id, 'manualDescription', e.target.value)}
                                      placeholder="Descripción del concepto o servicio..."
                                      className="flex-1 bg-white border border-emerald-200 rounded px-2 py-0.5 text-[8px] font-bold uppercase text-indigo-900 outline-none focus:border-emerald-500 placeholder-indigo-300 no-print"
                                  />
                                  <span className="print-only text-[8px] font-bold uppercase italic text-indigo-900 flex-1">{item.manualDescription}</span>
                               </div>
                             </>
                         ) : (
                            <div className="flex-1 min-w-[180px] pr-2">
                                <span className={`text-[8px] font-bold uppercase italic leading-tight block ${isUnknown ? 'text-red-500' : 'text-indigo-800'}`}>{product.name}</span>
                                {specialLabel && <span className="text-[6px] font-black text-orange-600 uppercase tracking-wide">{specialLabel}</span>}
                            </div>
                         )}

                         {/* Dimensiones y Apertura - Solo para productos normales */}
                         {item.isManual ? (
                            <>
                                {/* Para líneas manuales, solo el campo de puntos alineado con OBS */}
                                <div className="w-24 shrink-0 pr-1">
                                    <div className="flex items-center gap-1 bg-white border border-emerald-200 rounded px-1 py-0.5 no-print">
                                        <span className="text-[6px] font-black text-emerald-600">PTS:</span>
                                        <input 
                                            type="number" 
                                            value={item.manualPoints || 0} 
                                            onChange={e => updateItem(item.id, 'manualPoints', parseFloat(e.target.value) || 0)}
                                            className="w-full font-black text-[8px] text-orange-600 outline-none bg-transparent"
                                            placeholder="0"
                                        />
                                    </div>
                                    <span className="print-only text-[7px] font-bold text-emerald-600">{item.manualPoints} pts</span>
                                </div>
                            </>
                         ) : (
                            <>
                                <div className="w-11 shrink-0 text-center">
                                    <input type="number" value={Math.round(item.customWidth)} onChange={e => updateItem(item.id, 'customWidth', parseInt(e.target.value) || 0)} className={`w-10 bg-indigo-50/50 rounded p-0.5 text-[8px] font-black text-center outline-none border ${Number(item.customWidth) !== Number(product.width) ? 'border-orange-500 text-orange-600 bg-orange-50' : 'border-indigo-100'} no-print`} />
                                    <span className="print-only font-bold text-[8px]">{item.customWidth ? Math.round(item.customWidth) : '-'}</span>
                                </div>
                                <div className="w-11 shrink-0 text-center">
                                    <input type="number" value={item.customHeight} onChange={e => updateItem(item.id, 'customHeight', parseInt(e.target.value) || 0)} className={`w-10 bg-indigo-50/50 rounded p-0.5 text-[8px] font-black text-center outline-none border ${Number(item.customHeight) !== Number(product.height) ? 'border-orange-500 text-orange-600 bg-orange-50' : 'border-indigo-100'} no-print`} />
                                    <span className="print-only font-bold text-[8px]">{item.customHeight || '-'}</span>
                                </div>
                                <div className="w-11 shrink-0 text-center">
                                    <input type="number" value={item.customDepth} onChange={e => updateItem(item.id, 'customDepth', parseInt(e.target.value) || 0)} className={`w-10 bg-indigo-50/50 rounded p-0.5 text-[8px] font-black text-center outline-none border ${Number(item.customDepth) !== Number(product.depth) ? 'border-orange-500 text-orange-600 bg-orange-50' : 'border-indigo-100'} no-print`} />
                                    <span className="print-only font-bold text-[8px]">{item.customDepth || '-'}</span>
                                </div>
                                <div className="w-8 shrink-0 text-center">
                                    {isTwoDoor ? (
                                      <>
                                        <span className="text-[7px] font-black text-indigo-300 no-print">-</span>
                                        <span className="print-only font-black text-[7px]">-</span>
                                      </>
                                    ) : (
                                      <>
                                        <select value={item.openingDirection || 'Derecha'} onChange={e => updateItem(item.id, 'openingDirection', e.target.value)} className="w-7 bg-indigo-50/50 border border-indigo-100 rounded py-0.5 text-[7px] font-black uppercase italic outline-none no-print">
                                          <option value="Derecha">D</option>
                                          <option value="Izquierda">I</option>
                                          <option value="N/A">-</option>
                                        </select>
                                        <span className="print-only font-black text-[7px] italic uppercase">{item.openingDirection === 'Derecha' ? 'D' : item.openingDirection === 'Izquierda' ? 'I' : '-'}</span>
                                      </>
                                    )}
                                </div>
                                {/* Observaciones */}
                                <div className="w-20 shrink-0 pr-1">
                                    <input type="text" placeholder="Notas..." value={item.notes || ''} onChange={e => updateItem(item.id, 'notes', e.target.value)} className="w-full bg-indigo-50/50 border border-indigo-100 rounded px-1 py-0.5 text-[7px] font-bold text-indigo-400 outline-none focus:border-orange-300 no-print" />
                                    <p className="print-only text-[7px] font-bold text-indigo-400 italic truncate">{item.notes}</p>
                                </div>
                            </>
                         )}

                         {/* Precio - Siempre visible y alineado */}
                         <div className="w-20 shrink-0 text-right flex items-center justify-end gap-1 relative group/price">
                            {hasExtras && state.currentUser?.isAdmin && <Info size={7} className="text-orange-600 no-print" />}
                            <span className="text-[10px] font-black italic tracking-tight">{price.toLocaleString('es-ES', { minimumFractionDigits: 2 })}€</span>
                            
                            {/* Desglose solo visible para admin */}
                            {state.currentUser?.isAdmin && (
                              <div className="absolute right-0 top-full mt-2 z-50 hidden group-hover/price:block w-64 bg-slate-900 text-white p-4 rounded-xl shadow-2xl text-[9px] font-mono whitespace-pre-wrap text-left border border-indigo-500/30">
                                <div className="absolute -top-1 right-4 w-2 h-2 bg-slate-900 rotate-45 border-t border-l border-indigo-500/30"></div>
                                {breakdown}
                              </div>
                            )}
                         </div>
                         
                         {/* Botón eliminar */}
                         <div className="w-6 shrink-0 no-print">
                            <button onClick={() => removeItem(item.id)} className="p-1 text-indigo-200 hover:text-red-500 transition-all"><Trash2 size={12}/></button>
                         </div>
                      </div>
                    );
                  })}
                  </div>
               </div>

               <div className="pt-4 mt-auto border-t-4 border-indigo-950 mb-4">
                  {/* Sección de totales */}
                  <div className="flex flex-col gap-2">
                     <div className="text-[9px] font-black text-indigo-400 uppercase tracking-widest">
                        PRESUPUESTO TÉCNICO
                     </div>
                     
                     {/* Caja de totales en HORIZONTAL - ANCHO COMPLETO */}
                     <div className="bg-indigo-950 text-white rounded-xl shadow-lg w-full">
                        <div className="flex w-full">
                           {/* BRUTO LÍNEAS */}
                           <div className="flex-1 px-4 py-3 border-r border-indigo-800/50">
                              <div className="text-[7px] font-bold uppercase tracking-wide text-indigo-400">BRUTO LÍNEAS</div>
                              <div className="text-sm font-black italic tracking-tight text-white">
                                {total.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}€
                              </div>
                           </div>
                           {/* BASE IMPONIBLE */}
                           <div className="flex-1 px-4 py-3 border-r border-indigo-800/50">
                              <div className="text-[7px] font-bold uppercase tracking-wide text-indigo-400">BASE IMPONIBLE</div>
                              <div className="text-sm font-black italic tracking-tight text-white">
                                {total.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}€
                              </div>
                           </div>
                           {/* IVA EDITABLE */}
                           <div className="flex-1 px-4 py-3 border-r border-indigo-800/50">
                              <div className="flex items-center gap-1">
                                <span className="text-[7px] font-bold uppercase tracking-wide text-indigo-400">IVA</span>
                                <input 
                                  type="number" 
                                  min="0" 
                                  max="100" 
                                  value={state.ivaRate || 21}
                                  onChange={e => setState(prev => ({...prev, ivaRate: parseFloat(e.target.value) || 0}))}
                                  className="w-10 bg-indigo-800 border border-indigo-700 rounded px-1 py-0.5 text-xs font-black text-white text-center outline-none focus:border-orange-500 no-print"
                                />
                                <span className="text-[7px] font-bold text-indigo-400 print-only">{state.ivaRate || 21}</span>
                                <span className="text-[7px] font-bold text-indigo-400">%</span>
                              </div>
                              <div className="text-sm font-black italic tracking-tight text-white">
                                {(total * (state.ivaRate || 21) / 100).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}€
                              </div>
                           </div>
                           {/* TOTAL */}
                           <div className="flex-1 px-4 py-3 bg-orange-600 rounded-r-xl">
                              <div className="text-[7px] font-black uppercase tracking-wide text-orange-200">TOTAL PRESUPUESTO</div>
                              <div className="text-lg font-black italic tracking-tight text-white text-right">
                                {(total * (1 + (state.ivaRate || 21) / 100)).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}€
                              </div>
                           </div>
                        </div>
                     </div>
                  </div>
               </div>
            </div>
          )}
        </div>

        {/* Catálogo - POSICIÓN HORIZONTAL (abajo) */}
        {catalogPosition === 'horizontal' && (
          <div style={{ height: isCatalogOpen ? catalogHeight : 40 }} className="absolute bottom-0 left-0 right-0 bg-white border-t border-indigo-100 no-print transition-all duration-300 z-50 overflow-hidden shadow-2xl">
             {isCatalogOpen && <div onMouseDown={() => { isResizingCatalog.current = true; }} className="h-1.5 cursor-ns-resize hover:bg-orange-600/30"></div>}
             <div className={`${isCatalogOpen ? 'h-[40px]' : 'h-[40px]'} px-4 bg-indigo-50/30 border-b border-indigo-50 flex justify-between items-center`}>
                <div className="flex items-center gap-2">
                  {/* Botón ocultar/mostrar */}
                  <button 
                    onClick={() => setIsCatalogOpen(!isCatalogOpen)}
                    className="p-1.5 bg-indigo-100 hover:bg-indigo-200 rounded-lg transition-colors"
                    title={isCatalogOpen ? "Ocultar librería" : "Mostrar librería"}
                  >
                    {isCatalogOpen ? <ChevronDown size={14} className="text-indigo-600"/> : <ChevronUp size={14} className="text-indigo-600"/>}
                  </button>
                  <LayoutPanelTop size={14} className="text-orange-600"/>
                  <h3 className="text-[9px] font-black uppercase tracking-wider text-indigo-900">
                    LIBRERÍA <span className="text-orange-600">({filteredCatalog.length})</span>
                  </h3>
                </div>
                <div className="flex items-center gap-2">
                   {/* Filtros solo cuando está abierto */}
                   {isCatalogOpen && (
                     <>
                       <select value={selectedCategory} onChange={e => { setSelectedCategory(e.target.value); setSelectedSeries('TODAS'); }} className="bg-white border border-indigo-100 rounded-lg py-1 px-2 text-[8px] font-black uppercase text-indigo-800 outline-none">
                         <option value="TODAS">CATEGORÍAS</option>
                         {uniqueCategories.map(c => <option key={c} value={c}>{c}</option>)}
                       </select>
                       <select value={selectedSeries} onChange={e => setSelectedSeries(e.target.value)} className="bg-white border border-indigo-100 rounded-lg py-1 px-2 text-[8px] font-black uppercase text-indigo-800 outline-none">
                         <option value="TODAS">SERIES</option>
                         {uniqueSeries.map(s => <option key={s} value={s}>{s}</option>)}
                       </select>
                       <div className="relative w-[180px]">
                          <Search className="absolute left-2 top-1/2 -translate-y-1/2 text-indigo-300" size={12} />
                          <input type="text" placeholder="BUSCAR..." value={searchQuery} onChange={e => setSearchQuery(e.target.value)} className="w-full bg-white border border-indigo-100 rounded-lg py-1 pl-7 pr-2 text-[8px] font-bold outline-none uppercase" />
                       </div>
                     </>
                   )}
                   {/* Botón cambiar posición */}
                   <button 
                     onClick={() => setCatalogPosition('vertical')} 
                     className="p-1.5 bg-indigo-100 hover:bg-indigo-200 rounded-lg transition-colors"
                     title="Cambiar a vista vertical (derecha)"
                   >
                     <PanelRightOpen size={14} className="text-indigo-600"/>
                   </button>
                </div>
             </div>
             
             <div className="h-[calc(100%-45px)] overflow-y-auto">
                <table className="w-full text-left">
                  <thead className="bg-indigo-950 text-white text-[10px] font-black uppercase sticky top-0 z-20">
                    <tr>
                      <th className="p-2 pl-3 w-[45px]"></th>
                      <th className="p-2 w-[90px]">REF</th>
                      <th className="p-2 min-w-[180px]">DESCRIPCIÓN</th>
                      <th className="p-2 text-center w-[55px]">AN</th>
                      <th className="p-2 text-center w-[55px]">AL</th>
                      <th className="p-2 text-center w-[55px]">FO</th>
                      <th className="p-2 text-center w-[60px]">PTS</th>
                      <th className="p-2 pr-3 text-right w-[40px]"></th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-indigo-50">
                    {filteredCatalog.map(p => {
                      // Determinar tipo de icono basado en el código
                      const code = p.code?.toUpperCase() || '';
                      const isGola = code.startsWith('G') && /^G\d/.test(code);
                      
                      // Detectar tipo de herraje
                      const hardwareType = getHardwareType(code);
                      // Detectar tipo de mueble especial
                      const specialType = getSpecialType(code);
                      
                      // Detectar tipo de mueble especial para icono
                      let iconType = '1P';
                      if (code.includes('HK')) iconType = 'HK-TOP';
                      else if (code.includes('HS')) iconType = 'HS';
                      else if (code.includes('HL')) iconType = 'HL';
                      else if (code.includes('HF')) iconType = 'HF';
                      else if (code.includes('AM') || code.includes('BM')) iconType = 'MICRO';
                      else if (code.includes('CHM')) iconType = 'HORNO-MICRO';
                      else if (code.includes('CH') || code.includes('BH')) iconType = 'HORNO';
                      else if (code.includes('BP')) iconType = 'PLACA';
                      else if (code.includes('BF')) iconType = 'FREG';
                      else if (code.includes('AT')) iconType = 'TERMO';
                      else if (code.includes('AE')) iconType = 'ESCURRE';
                      else if (code.includes('ARA') || code.includes('BRA') || code.includes('ARC') || code.includes('BRC')) iconType = 'RINCON';
                      else if (code.includes('3C') || code.includes('4C') || code.includes('5C')) iconType = '3C';
                      else if (code.includes('2P')) iconType = '2P';
                      else if (code.includes('1V') || code.includes('2V')) iconType = '1V';
                      
                      // Colores para badges de herraje
                      const hardwareColors = {
                        'HK': 'bg-red-500 text-white',
                        'HS': 'bg-emerald-500 text-white', 
                        'HL': 'bg-violet-500 text-white',
                        'HF': 'bg-cyan-500 text-white'
                      };
                      
                      // Colores para badges de tipo especial
                      const specialColors = {
                        'MICRO': 'bg-blue-100 text-blue-700',
                        'HORNO': 'bg-amber-100 text-amber-700',
                        'HORNO+MICRO': 'bg-orange-100 text-orange-700',
                        'PLACA': 'bg-red-100 text-red-700',
                        'FREG': 'bg-sky-100 text-sky-700',
                        'TERMO': 'bg-teal-100 text-teal-700',
                        'ESCURRE': 'bg-indigo-100 text-indigo-700'
                      };
                      
                      return (
                        <tr key={p.id} className="hover:bg-orange-50 group cursor-pointer transition-colors" onClick={() => addItemToBudget(p)}>
                          <td className="p-1 pl-2 w-[45px]">
                            <CabinetIcon type={iconType} isGola={isGola} className="w-8 h-8" />
                          </td>
                          <td className="p-2 font-bold text-indigo-900 text-[11px] w-[90px]">{p.code}</td>
                          <td className="p-2 min-w-[180px]">
                            <div className="flex items-center gap-1.5 flex-wrap">
                              <span className="text-[10px] font-bold text-indigo-600 uppercase">{p.name}</span>
                              {hardwareType && (
                                <span className={`px-1.5 py-0.5 rounded text-[7px] font-black ${hardwareColors[hardwareType]}`}>
                                  {hardwareType}
                                </span>
                              )}
                              {specialType && (
                                <span className={`px-1.5 py-0.5 rounded text-[7px] font-bold ${specialColors[specialType]}`}>
                                  {specialType}
                                </span>
                              )}
                            </div>
                            {p.series && <div className="text-[8px] text-orange-500 font-medium mt-0.5">{p.series}</div>}
                          </td>
                          <td className="p-2 text-center font-bold text-slate-600 text-[10px] w-[55px]">{p.width ? Math.round(p.width) : '-'}</td>
                          <td className="p-2 text-center font-bold text-slate-600 text-[10px] w-[55px]">{p.height || '-'}</td>
                          <td className="p-2 text-center font-bold text-slate-600 text-[10px] w-[55px]">{p.depth || '-'}</td>
                          <td className="p-2 text-center font-black text-orange-600 text-[11px] w-[60px]">
                            {typeof p.points === 'number' ? p.points : p.points?.Z1 || 0}
                          </td>
                          <td className="p-2 pr-3 text-right w-[40px]"><Plus size={14} className="text-orange-600 inline opacity-0 group-hover:opacity-100 transition-opacity"/></td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
             </div>
          </div>
        )}

        {/* Catálogo - POSICIÓN VERTICAL (derecha) */}
        {catalogPosition === 'vertical' && (
          <div 
            style={{ width: isCatalogOpen ? catalogWidth : 50 }} 
            className="absolute top-0 right-0 bottom-0 bg-white border-l border-indigo-100 no-print transition-all duration-300 z-50 overflow-hidden shadow-2xl flex flex-col"
          >
            {/* Resizer horizontal */}
            <div 
              onMouseDown={() => { isResizingCatalogWidth.current = true; }} 
              className="absolute left-0 top-0 bottom-0 w-1.5 cursor-ew-resize hover:bg-orange-600/30 z-10"
            />
            
            {/* Header */}
            <div className="h-[45px] px-3 bg-indigo-50/30 border-b border-indigo-50 flex items-center gap-2 shrink-0">
              <button 
                onClick={() => setIsCatalogOpen(!isCatalogOpen)}
                className="p-1"
              >
                {isCatalogOpen ? <PanelRightClose size={16} className="text-indigo-600"/> : <PanelRightOpen size={16} className="text-indigo-600"/>}
              </button>
              {isCatalogOpen && (
                <>
                  <div className="flex-1">
                    <h3 className="text-[8px] font-black uppercase text-indigo-900">
                      LIBRERÍA <span className="text-orange-600">({filteredCatalog.length})</span>
                    </h3>
                  </div>
                  <button 
                    onClick={() => setCatalogPosition('horizontal')} 
                    className="p-1.5 bg-indigo-100 hover:bg-indigo-200 rounded-lg transition-colors"
                    title="Cambiar a vista horizontal (abajo)"
                  >
                    <PanelBottomOpen size={14} className="text-indigo-600"/>
                  </button>
                </>
              )}
            </div>

            {isCatalogOpen && (
              <>
                {/* Filtros verticales */}
                <div className="p-3 space-y-2 border-b border-indigo-50 shrink-0">
                  <select value={selectedCategory} onChange={e => { setSelectedCategory(e.target.value); setSelectedSeries('TODAS'); }} className="w-full bg-white border border-indigo-100 rounded-lg py-2 px-3 text-[10px] font-black uppercase text-indigo-800 outline-none">
                    <option value="TODAS">TODAS CATEGORÍAS</option>
                    {uniqueCategories.map(c => <option key={c} value={c}>{c}</option>)}
                  </select>
                  <select value={selectedSeries} onChange={e => setSelectedSeries(e.target.value)} className="w-full bg-white border border-indigo-100 rounded-lg py-2 px-3 text-[10px] font-black uppercase text-indigo-800 outline-none">
                    <option value="TODAS">TODAS SERIES</option>
                    {uniqueSeries.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-indigo-300" size={14} />
                    <input type="text" placeholder="BUSCAR..." value={searchQuery} onChange={e => setSearchQuery(e.target.value)} className="w-full bg-white border border-indigo-100 rounded-lg py-2 pl-9 pr-3 text-[10px] font-bold outline-none uppercase" />
                  </div>
                </div>

                {/* Lista de productos - más visible */}
                <div className="flex-1 overflow-y-auto">
                  <div className="divide-y divide-indigo-100">
                    {filteredCatalog.map(p => {
                      const code = p.code?.toUpperCase() || '';
                      const isGola = code.startsWith('G') && /^G\d/.test(code);
                      
                      // Detectar tipo de herraje y tipo especial
                      const hardwareType = getHardwareType(code);
                      const specialType = getSpecialType(code);
                      
                      // Detectar tipo de mueble especial para icono
                      let iconType = '1P';
                      if (code.includes('HK')) iconType = 'HK-TOP';
                      else if (code.includes('HS')) iconType = 'HS';
                      else if (code.includes('HL')) iconType = 'HL';
                      else if (code.includes('HF')) iconType = 'HF';
                      else if (code.includes('AM') || code.includes('BM')) iconType = 'MICRO';
                      else if (code.includes('CHM')) iconType = 'HORNO-MICRO';
                      else if (code.includes('CH') || code.includes('BH')) iconType = 'HORNO';
                      else if (code.includes('BP')) iconType = 'PLACA';
                      else if (code.includes('BF')) iconType = 'FREG';
                      else if (code.includes('AT')) iconType = 'TERMO';
                      else if (code.includes('AE')) iconType = 'ESCURRE';
                      else if (code.includes('ARA') || code.includes('BRA') || code.includes('ARC') || code.includes('BRC')) iconType = 'RINCON';
                      else if (code.includes('3C') || code.includes('4C') || code.includes('5C')) iconType = '3C';
                      else if (code.includes('2P')) iconType = '2P';
                      else if (code.includes('1V') || code.includes('2V')) iconType = '1V';
                      
                      // Colores para badges de herraje
                      const hardwareColors = {
                        'HK': 'bg-red-500 text-white',
                        'HS': 'bg-emerald-500 text-white', 
                        'HL': 'bg-violet-500 text-white',
                        'HF': 'bg-cyan-500 text-white'
                      };
                      
                      // Colores para badges de tipo especial
                      const specialColors = {
                        'MICRO': 'bg-blue-100 text-blue-700',
                        'HORNO': 'bg-amber-100 text-amber-700',
                        'HORNO+MICRO': 'bg-orange-100 text-orange-700',
                        'PLACA': 'bg-red-100 text-red-700',
                        'FREG': 'bg-sky-100 text-sky-700',
                        'TERMO': 'bg-teal-100 text-teal-700',
                        'ESCURRE': 'bg-indigo-100 text-indigo-700'
                      };
                      
                      return (
                        <div 
                          key={p.id} 
                          className="p-3 hover:bg-orange-50 cursor-pointer transition-colors group"
                          onClick={() => addItemToBudget(p)}
                        >
                          <div className="flex items-center gap-3">
                            <CabinetIcon type={iconType} isGola={isGola} className="w-12 h-12 shrink-0" />
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center justify-between gap-2">
                                <span className="text-[13px] font-black text-indigo-900">{p.code}</span>
                                <span className="text-[14px] font-black text-orange-600">{typeof p.points === 'number' ? p.points : p.points?.Z1 || 0} pts</span>
                              </div>
                              <div className="flex items-center gap-1.5 flex-wrap mt-1">
                                <span className="text-[11px] font-bold text-indigo-600 uppercase">{p.name}</span>
                                {hardwareType && (
                                  <span className={`px-1.5 py-0.5 rounded text-[8px] font-black ${hardwareColors[hardwareType]}`}>
                                    {hardwareType}
                                  </span>
                                )}
                                {specialType && (
                                  <span className={`px-1.5 py-0.5 rounded text-[8px] font-bold ${specialColors[specialType]}`}>
                                    {specialType}
                                  </span>
                                )}
                              </div>
                              <div className="flex items-center gap-3 mt-1">
                                <span className="text-[10px] font-bold text-slate-500">
                                  AN: {p.width ? Math.round(p.width) : '-'} | AL: {p.height || '-'} | FO: {p.depth || '-'}
                                </span>
                              </div>
                              {p.series && <div className="text-[9px] text-orange-500 font-medium mt-1">{p.series}</div>}
                            </div>
                            <Plus size={18} className="text-orange-600 opacity-0 group-hover:opacity-100 transition-opacity shrink-0"/>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </>
            )}

            {/* Cuando está cerrado, mostrar solo icono */}
            {!isCatalogOpen && (
              <div className="flex-1 flex items-center justify-center">
                <div className="transform -rotate-90 whitespace-nowrap text-[10px] font-black uppercase text-indigo-400 tracking-widest">
                  LIBRERÍA ({filteredCatalog.length})
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Despiece Modal */}
      <DespieceModal
        isOpen={isDespieceOpen}
        onClose={() => setIsDespieceOpen(false)}
        items={items}
        catalogs={catalogs}
        carcassMaterialName={carcassMaterialName}
        customerName={state.customerName || ''}
        projectReference={state.internalReference || ''}
        expedientNumber={state.budgetNumber || ''}
      />

      {/* Modal Confirmar Pedido */}
      {isConfirmOrderOpen && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden">
            {/* Header */}
            <div className="bg-emerald-600 text-white px-6 py-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <CheckCircle size={24} />
                <h2 className="text-lg font-black uppercase tracking-wider">Confirmar Pedido</h2>
              </div>
              <button onClick={() => setIsConfirmOrderOpen(false)} className="p-1 hover:bg-white/20 rounded-lg transition-colors">
                <X size={20} />
              </button>
            </div>

            {/* Content */}
            <div className="p-6 space-y-4">
              {orderSent ? (
                <div className="text-center py-8">
                  <CheckCircle size={64} className="mx-auto text-emerald-500 mb-4" />
                  <p className="text-xl font-black text-emerald-600">¡Pedido Confirmado!</p>
                  <p className="text-sm text-gray-500 mt-2">Se ha enviado la confirmación al email indicado</p>
                </div>
              ) : (
                <>
                  {/* Info del presupuesto */}
                  <div className="bg-indigo-50 rounded-xl p-4 space-y-1">
                    <p className="text-xs font-black text-indigo-400 uppercase">Resumen del Pedido</p>
                    <p className="text-sm font-bold text-indigo-950">Expediente: <span className="text-orange-600">{state.budgetNumber}</span></p>
                    <p className="text-sm font-bold text-indigo-950">Cliente: {state.customerName || 'Sin nombre'}</p>
                    <p className="text-sm font-bold text-indigo-950">Total: <span className="text-emerald-600">{total.toLocaleString('es-ES', { style: 'currency', currency: 'EUR' })}</span></p>
                    <p className="text-sm text-indigo-400">{sortedItems.length} artículo(s)</p>
                  </div>

                  {/* Email destino */}
                  <div>
                    <label className="text-xs font-black text-indigo-950 uppercase mb-1 block">
                      <Mail size={12} className="inline mr-1" /> Email de destino *
                    </label>
                    <input
                      type="email"
                      value={orderEmail}
                      onChange={(e) => setOrderEmail(e.target.value)}
                      placeholder="pedidos@empresa.com"
                      className="w-full border border-indigo-200 rounded-lg px-4 py-2.5 text-sm focus:border-emerald-500 outline-none"
                    />
                  </div>

                  {/* Archivos adjuntos */}
                  <div>
                    <label className="text-xs font-black text-indigo-950 uppercase mb-2 block">
                      <Paperclip size={12} className="inline mr-1" /> Adjuntar Planos / Fotos
                    </label>
                    <div className="border-2 border-dashed border-indigo-200 rounded-xl p-4 text-center hover:border-emerald-400 transition-colors">
                      <input
                        type="file"
                        multiple
                        accept="image/*,.pdf,.dwg,.dxf"
                        onChange={handleAttachmentChange}
                        className="hidden"
                        id="order-attachments"
                      />
                      <label htmlFor="order-attachments" className="cursor-pointer">
                        <Upload size={32} className="mx-auto text-indigo-300 mb-2" />
                        <p className="text-xs font-bold text-indigo-400">Click para adjuntar archivos</p>
                        <p className="text-[10px] text-indigo-300">Planos, fotos de cocina, dibujos...</p>
                      </label>
                    </div>

                    {/* Lista de archivos adjuntos */}
                    {orderAttachments.length > 0 && (
                      <div className="mt-3 space-y-2">
                        {orderAttachments.map((file, index) => (
                          <div key={index} className="flex items-center justify-between bg-indigo-50 rounded-lg px-3 py-2">
                            <div className="flex items-center gap-2">
                              <FileImage size={16} className="text-indigo-400" />
                              <span className="text-xs font-bold text-indigo-950 truncate max-w-[200px]">{file.name}</span>
                              <span className="text-[10px] text-indigo-300">({(file.size / 1024).toFixed(0)} KB)</span>
                            </div>
                            <button onClick={() => removeAttachment(index)} className="p-1 hover:bg-red-100 rounded text-red-500">
                              <X size={14} />
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Notas adicionales */}
                  <div>
                    <label className="text-xs font-black text-indigo-950 uppercase mb-1 block">
                      Notas adicionales
                    </label>
                    <textarea
                      value={orderNotes}
                      onChange={(e) => setOrderNotes(e.target.value)}
                      placeholder="Instrucciones especiales, observaciones..."
                      rows={3}
                      className="w-full border border-indigo-200 rounded-lg px-4 py-2.5 text-sm focus:border-emerald-500 outline-none resize-none"
                    />
                  </div>
                </>
              )}
            </div>

            {/* Footer */}
            {!orderSent && (
              <div className="px-6 py-4 bg-gray-50 flex gap-3">
                <button
                  onClick={() => setIsConfirmOrderOpen(false)}
                  className="flex-1 px-4 py-2.5 border border-gray-300 rounded-lg text-sm font-bold text-gray-600 hover:bg-gray-100 transition-colors"
                >
                  Cancelar
                </button>
                <button
                  onClick={handleConfirmOrder}
                  disabled={isSendingOrder || !orderEmail}
                  className="flex-1 px-4 py-2.5 bg-emerald-600 text-white rounded-lg text-sm font-black uppercase tracking-wider hover:bg-emerald-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {isSendingOrder ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Enviando...
                    </>
                  ) : (
                    <>
                      <Mail size={16} /> Enviar Confirmación
                    </>
                  )}
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default BudgetTable;
