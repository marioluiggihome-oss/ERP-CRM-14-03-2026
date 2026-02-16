import React, { useState, useRef, useCallback, useEffect } from 'react';
import { Upload, Trash2, Plus, Download, FileText, Loader, History, Percent, Edit3, X, Camera, AlertCircle, Save, Search, FolderOpen, Target, UserPlus, Briefcase, CheckCircle, Lock, Unlock, RefreshCw } from 'lucide-react';
import Logo from './Logo';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const Digitalizador = ({ state }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isCreatingOpportunity, setIsCreatingOpportunity] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  const [projectName, setProjectName] = useState('');
  const [customerName, setCustomerName] = useState('');
  const [customerEmail, setCustomerEmail] = useState('');
  const [customerPhone, setCustomerPhone] = useState('');
  const [lines, setLines] = useState([]);
  const [globalDiscount, setGlobalDiscount] = useState(0);
  const [globalMarkup, setGlobalMarkup] = useState(0);  // Incremento global
  const [ivaRate, setIvaRate] = useState(21);
  const [acabado, setAcabado] = useState('');
  const [armazon, setArmazon] = useState('');
  const [costados, setCostados] = useState('');
  const [showHistory, setShowHistory] = useState(false);
  const [history, setHistory] = useState([]);
  const [historySearch, setHistorySearch] = useState('');
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [showCRMModal, setShowCRMModal] = useState(false);
  const [showSaveOptionsModal, setShowSaveOptionsModal] = useState(false);  // Modal de opciones de guardado
  const [saveToPresupuestos, setSaveToPresupuestos] = useState(true);  // Guardar en presupuestos
  const [saveToHistory, setSaveToHistory] = useState(true);  // Guardar en historial
  const [saveToCRM, setSaveToCRM] = useState(false);  // Guardar en CRM
  const [crmContactName, setCrmContactName] = useState('');
  const [crmContactEmail, setCrmContactEmail] = useState('');
  const [crmContactPhone, setCrmContactPhone] = useState('');
  const [crmCompany, setCrmCompany] = useState('');
  const [opportunityCreated, setOpportunityCreated] = useState(null);
  const [currentPage, setCurrentPage] = useState(0);  // Página actual para navegación
  const [isLocked, setIsLocked] = useState(true);  // Modo bloqueado/desbloqueado
  const [expNumber, setExpNumber] = useState('');  // Número de expediente único
  const [isGeneratingExp, setIsGeneratingExp] = useState(false);  // Loading state para generar exp
  const [showCostMode, setShowCostMode] = useState(false);  // Mostrar precio COSTO vs PVP
  const [documentTitle, setDocumentTitle] = useState('Presupuesto Técnico');  // Título editable del documento
  const [isValorado, setIsValorado] = useState(true);  // Mostrar/ocultar precios
  const fileInputRef = useRef(null);

  // Obtener descuento del usuario actual
  const userDiscount = state?.currentUser?.discountMontada || state?.currentUser?.commercialDiscount || 0;

  // Generar número de expediente único desde el servidor (thread-safe)
  const generateExpNumber = async () => {
    setIsGeneratingExp(true);
    try {
      const response = await fetch(`${API_URL}/api/digitalizador/generate-exp-number`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userId: state?.currentUser?.id || 'anonymous' })
      });
      
      if (response.ok) {
        const data = await response.json();
        setExpNumber(data.expNumber);
        return data.expNumber;
      } else {
        // Fallback a generación local si falla el servidor
        const fallback = `EXP-LOCAL-${Date.now()}`;
        setExpNumber(fallback);
        return fallback;
      }
    } catch (err) {
      console.error('Error generating exp number:', err);
      const fallback = `EXP-LOCAL-${Date.now()}`;
      setExpNumber(fallback);
      return fallback;
    } finally {
      setIsGeneratingExp(false);
    }
  };

  // Inicializar número de expediente cuando no hay uno
  useEffect(() => {
    if (!expNumber) {
      generateExpNumber();
    }
  }, []);

  // Configuración de paginación
  const LINES_FIRST_PAGE = 15;  // Primera página tiene cabecera
  const LINES_PER_PAGE = 22;    // Páginas siguientes

  // Calcular páginas
  const getPages = () => {
    if (lines.length === 0) return [];
    const pages = [];
    let remaining = [...lines];
    
    // Primera página
    pages.push(remaining.splice(0, LINES_FIRST_PAGE));
    
    // Páginas siguientes
    while (remaining.length > 0) {
      pages.push(remaining.splice(0, LINES_PER_PAGE));
    }
    
    return pages;
  };

  const pages = getPages();
  const totalPages = pages.length;

  // Load history from database
  const loadHistory = async () => {
    setLoadingHistory(true);
    try {
      const userId = (state.currentUser?.isAdmin || state.currentUser?.isGerente) ? null : state.currentUser?.id;
      const url = userId 
        ? `${API_URL}/api/digitalizador/history?userId=${userId}${historySearch ? `&search=${historySearch}` : ''}`
        : `${API_URL}/api/digitalizador/history${historySearch ? `?search=${historySearch}` : ''}`;
      
      const response = await fetch(url);
      if (response.ok) {
        const data = await response.json();
        setHistory(data.items || []);
      }
    } catch (err) {
      console.error('Error loading history:', err);
    } finally {
      setLoadingHistory(false);
    }
  };

  // Load history when sidebar opens
  useEffect(() => {
    if (showHistory) {
      loadHistory();
    }
  }, [showHistory, historySearch]);

  // Abrir modal de opciones de guardado
  const handleSaveBudget = () => {
    if (lines.length === 0) {
      setError('No hay líneas para guardar');
      return;
    }
    // Pre-llenar datos del CRM
    setCrmContactName(customerName || '');
    setCrmContactEmail(customerEmail || '');
    setCrmContactPhone(customerPhone || '');
    setShowSaveOptionsModal(true);
  };

  // Ejecutar guardado con las opciones seleccionadas
  const executeSave = async () => {
    setIsSaving(true);
    setError(null);
    let savedItems = [];

    try {
      // 1. Guardar en historial del digitalizador (siempre)
      if (saveToHistory) {
        const historyResponse = await fetch(`${API_URL}/api/digitalizador/save`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            projectName: projectName || 'Sin nombre',
            customerName,
            acabado,
            armazon,
            costados,
            lines,
            globalDiscount,
            globalMarkup,
            ivaRate,
            userId: state.currentUser?.id || 'anonymous',
            expNumber: expNumber
          })
        });

        if (historyResponse.ok) {
          savedItems.push('Historial');
        }
      }

      // 2. Guardar en presupuestos principales
      if (saveToPresupuestos) {
        const presupuestoResponse = await fetch(`${API_URL}/api/presupuestos`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            budgetNumber: expNumber,
            projectName: projectName || 'Sin nombre',
            customerName,
            finish: acabado,
            carcassMaterial: armazon,
            sideColor: costados,
            items: lines.map(line => ({
              productId: line.id,
              productCode: line.reference || 'DIGI',
              productName: line.description,
              quantity: line.quantity,
              customWidth: 0,
              customHeight: 0,
              customDepth: 0,
              manualPrice: line.price,
              discount: line.discount,
              isManual: line.isManual || false,
              fromDigitalizador: true
            })),
            globalDiscount,
            globalMarkup,
            ivaRate,
            module: 'montada',
            source: 'digitalizador',
            userId: state.currentUser?.id || 'anonymous',
            totalPvp: totals.total
          })
        });

        if (presupuestoResponse.ok) {
          savedItems.push('Presupuestos');
        }
      }

      // 3. Crear oportunidad en CRM si está marcado
      if (saveToCRM && crmContactName.trim()) {
        // Primero crear/buscar contacto
        const contactResponse = await fetch(`${API_URL}/api/crm/contacts`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: crmContactName,
            email: crmContactEmail || '',
            phone: crmContactPhone || '',
            company: crmCompany || '',
            type: 'lead',
            source: 'digitalizador',
            notes: `Contacto desde Digitalizador - ${projectName || 'Sin nombre'}`
          })
        });

        if (contactResponse.ok) {
          const contact = await contactResponse.json();
          
          // Crear oportunidad
          const oppResponse = await fetch(`${API_URL}/api/crm/opportunities`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              title: projectName || `Presupuesto ${crmContactName}`,
              description: `Presupuesto digitalizado - ${lines.length} líneas\nAcabado: ${acabado || 'N/A'}\nArmazón: ${armazon || 'N/A'}`,
              contactId: contact.id,
              contactName: contact.name,
              company: crmCompany || '',
              value: totals.total,
              probability: 30,
              stage: 'lead',
              notes: `EXP: ${expNumber}\nBase: ${totals.baseImponible.toFixed(2)}€\nIVA: ${totals.iva.toFixed(2)}€`,
              tags: ['digitalizador', 'presupuesto'],
              assignedTo: state.currentUser?.id || ''
            })
          });

          if (oppResponse.ok) {
            savedItems.push('CRM');
            setOpportunityCreated(await oppResponse.json());
          }
        }
      }

      // Mostrar mensaje de éxito
      if (savedItems.length > 0) {
        setSuccessMessage(`✓ Guardado en: ${savedItems.join(', ')}`);
        setTimeout(() => setSuccessMessage(null), 4000);
      }

      setShowSaveOptionsModal(false);
      
      // Refresh history si está abierto
      if (showHistory) {
        loadHistory();
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setIsSaving(false);
    }
  };

  // Load a budget from history
  const loadBudgetFromHistory = (item) => {
    setProjectName(item.projectName || '');
    setCustomerName(item.customerName || '');
    setAcabado(item.acabado || '');
    setArmazon(item.armazon || '');
    setCostados(item.costados || '');
    setGlobalDiscount(item.globalDiscount || 0);
    setIvaRate(item.ivaRate || 21);
    setLines(item.lines || []);
    setShowHistory(false);
  };

  // Delete a budget from history
  const deleteBudgetFromHistory = async (itemId, e) => {
    e.stopPropagation();
    if (!window.confirm('¿Eliminar este presupuesto del historial?')) return;

    try {
      const response = await fetch(`${API_URL}/api/digitalizador/history/${itemId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        loadHistory();
      }
    } catch (err) {
      console.error('Error deleting:', err);
    }
  };

  // Handle file upload
  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Validate file type
    const validTypes = ['image/jpeg', 'image/png', 'image/webp', 'application/pdf'];
    if (!validTypes.includes(file.type)) {
      setError('Formato no válido. Use JPG, PNG, WEBP o PDF.');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Convert file to base64
      const base64 = await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
          const result = reader.result;
          // Remove data URL prefix
          const base64Data = result.split(',')[1];
          resolve(base64Data);
        };
        reader.onerror = reject;
        reader.readAsDataURL(file);
      });

      // Send to API
      const response = await fetch(`${API_URL}/api/digitalizador/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          imageBase64: base64,
          filename: file.name
        })
      });

      if (!response.ok) {
        throw new Error('Error al analizar la imagen');
      }

      const data = await response.json();

      if (data.success) {
        setProjectName(data.projectName || '');
        setLines(data.lines || []);
        
        // Save to history
        const historyEntry = {
          id: Date.now(),
          date: new Date().toISOString(),
          projectName: data.projectName,
          lineCount: data.lines.length,
          filename: file.name
        };
        setHistory(prev => [historyEntry, ...prev.slice(0, 9)]);
      } else {
        setError(data.error || 'No se pudo extraer información de la imagen');
      }
    } catch (err) {
      console.error('Upload error:', err);
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  // Update a line
  const updateLine = (id, field, value) => {
    setLines(prev => prev.map(line => 
      line.id === id ? { ...line, [field]: value } : line
    ));
  };

  // Delete a line
  const deleteLine = (id) => {
    setLines(prev => prev.filter(line => line.id !== id));
  };

  // Add manual line
  const addManualLine = () => {
    const newLine = {
      id: `MANUAL-${Date.now()}`,
      quantity: 1,
      reference: 'MANUAL',
      description: 'NUEVA LÍNEA PERSONALIZADA...',
      price: 0,
      discount: 0,
      isManual: true
    };
    setLines(prev => [...prev, newLine]);
  };

  // Calculate totals
  const calculateTotals = useCallback(() => {
    let brutoLineas = 0;
    
    lines.forEach(line => {
      const linePrice = line.price * line.quantity;
      brutoLineas += linePrice;
    });

    // Calculate base with discounts
    let baseImponible = 0;
    lines.forEach(line => {
      const linePrice = line.price * line.quantity;
      let lineDiscount = line.isManual ? line.discount : Math.max(line.discount, globalDiscount);
      baseImponible += linePrice * (1 - lineDiscount / 100);
    });

    // Aplicar incremento global de margen (SIEMPRE si existe, independiente del candado)
    if (globalMarkup > 0) {
      baseImponible = baseImponible * (1 + globalMarkup / 100);
    }

    const iva = baseImponible * (ivaRate / 100);
    const total = baseImponible + iva;

    return { brutoLineas, baseImponible, iva, total };
  }, [lines, globalDiscount, globalMarkup, ivaRate]);

  const totals = calculateTotals();

  // Calcular totales en modo COSTO (con descuento de usuario)
  const calculateCostTotals = useCallback(() => {
    if (lines.length === 0) return { brutoLineas: 0, baseImponible: 0, iva: 0, total: 0 };

    // Aplicar descuento del usuario a cada línea
    let brutoLineas = lines.reduce((sum, line) => {
      const linePrice = line.price * line.quantity;
      let lineDiscount = line.isManual ? line.discount : Math.max(line.discount, globalDiscount);
      return sum + (linePrice * (1 - lineDiscount / 100));
    }, 0);

    // Aplicar incremento global de margen (SIEMPRE si existe, independiente del candado)
    if (globalMarkup > 0) {
      brutoLineas = brutoLineas * (1 + globalMarkup / 100);
    }

    // Aplicar descuento del usuario (COSTO)
    const baseImponible = brutoLineas * (1 - userDiscount / 100);
    const iva = baseImponible * (ivaRate / 100);
    const total = baseImponible + iva;

    return { brutoLineas, baseImponible, iva, total };
  }, [lines, globalDiscount, globalMarkup, ivaRate, userDiscount]);

  const costTotals = calculateCostTotals();

  // Get net price for a line (con incremento de margen si aplica)
  const getLineNet = (line) => {
    const linePrice = line.price * line.quantity;
    let lineDiscount = line.isManual ? line.discount : Math.max(line.discount, globalDiscount);
    let netPrice = linePrice * (1 - lineDiscount / 100);
    
    // Aplicar incremento global de margen (SIEMPRE si existe, independiente del candado)
    if (globalMarkup > 0) {
      netPrice = netPrice * (1 + globalMarkup / 100);
    }
    
    return netPrice;
  };

  // Get COST price for a line (with user discount and markup)
  const getLineCost = (line) => {
    const netPrice = getLineNet(line);
    return netPrice * (1 - userDiscount / 100);
  };

  // Export to PDF (uses browser print)
  const handleExportPDF = () => {
    // Temporalmente mostrar todas las líneas para impresión
    setCurrentPage(-1); // -1 significa "mostrar todas"
    setTimeout(() => {
      window.print();
      setCurrentPage(0); // Volver a la primera página después de imprimir
    }, 100);
  };

  // Export to CSV for cutting machine
  const handleExportCSV = async () => {
    try {
      const response = await fetch(`${API_URL}/api/digitalizador/export-csv`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          lines: lines,
          materialCode: "40-ESTEITEX16",
          materialThickness: 16.0
        })
      });

      if (!response.ok) throw new Error('Error al exportar');

      const data = await response.json();
      
      // Download CSV
      const blob = new Blob([data.csv], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `despiece_${projectName || 'export'}_${Date.now()}.csv`;
      link.click();
    } catch (err) {
      console.error('Export CSV error:', err);
      setError('Error al exportar CSV');
    }
  };

  // Reset form
  const handleReset = () => {
    setLines([]);
    setProjectName('');
    setGlobalDiscount(0);
    setAcabado('');
    setArmazon('');
    setCostados('');
    setError(null);
    setOpportunityCreated(null);
    setCurrentPage(0);
    setIsLocked(true);
    setShowCostMode(false);
    setGlobalMarkup(0);
    generateExpNumber();  // Nuevo número de expediente desde servidor
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Open CRM modal with pre-filled data
  const openCRMModal = () => {
    setCrmContactName(customerName || '');
    setCrmContactEmail(customerEmail || '');
    setCrmContactPhone(customerPhone || '');
    setCrmCompany('');
    setShowCRMModal(true);
  };

  // Create opportunity in CRM
  const handleCreateOpportunity = async () => {
    if (lines.length === 0) {
      setError('No hay líneas en el presupuesto');
      return;
    }

    setIsCreatingOpportunity(true);
    setError(null);

    try {
      // First, create or find a contact
      const contactResponse = await fetch(`${API_URL}/api/crm/contacts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: crmContactName || customerName || 'Cliente sin nombre',
          email: crmContactEmail || customerEmail || '',
          phone: crmContactPhone || customerPhone || '',
          company: crmCompany || '',
          type: 'lead',
          source: 'digitalizador',
          notes: `Contacto creado desde Digitalizador de Borradores - Proyecto: ${projectName || 'Sin nombre'}`
        })
      });

      if (!contactResponse.ok) {
        throw new Error('Error al crear contacto');
      }

      const contact = await contactResponse.json();

      // Now create the opportunity
      const opportunityResponse = await fetch(`${API_URL}/api/crm/opportunities`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: projectName || `Presupuesto ${crmContactName || customerName || 'Cliente'}`,
          description: `Presupuesto digitalizado - ${lines.length} líneas\nAcabado: ${acabado || 'N/A'}\nArmazón: ${armazon || 'N/A'}\nCostados: ${costados || 'N/A'}`,
          contactId: contact.id,
          contactName: contact.name,
          company: crmCompany || contact.company || '',
          value: totals.total,
          probability: 30,
          stage: 'lead',
          notes: `Creado desde Digitalizador de Borradores\nBase imponible: ${totals.baseImponible.toLocaleString('es-ES', { style: 'currency', currency: 'EUR' })}\nIVA (${ivaRate}%): ${totals.iva.toLocaleString('es-ES', { style: 'currency', currency: 'EUR' })}`,
          tags: ['digitalizador', 'presupuesto'],
          assignedTo: state.currentUser?.id || ''
        })
      });

      if (!opportunityResponse.ok) {
        throw new Error('Error al crear oportunidad');
      }

      const opportunity = await opportunityResponse.json();
      
      setOpportunityCreated(opportunity);
      setSuccessMessage(`¡Oportunidad "${opportunity.title}" creada en el CRM!`);
      setShowCRMModal(false);
      
      setTimeout(() => setSuccessMessage(null), 5000);
    } catch (err) {
      console.error('Create opportunity error:', err);
      setError(err.message);
    } finally {
      setIsCreatingOpportunity(false);
    }
  };

  return (
    <div className="h-full flex flex-col bg-slate-200 overflow-hidden">
      {/* Header */}
      <header className="bg-indigo-950 text-white px-6 py-3 flex items-center justify-between shrink-0 no-print">
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center overflow-hidden">
            <Logo className="w-8 h-8" customLogo={state.logo} />
          </div>
          <button 
            onClick={() => setShowHistory(!showHistory)}
            className="flex items-center gap-2 px-4 py-2 bg-white/10 rounded-lg hover:bg-white/20 transition-colors"
          >
            <History size={16} />
            <span className="text-xs font-bold uppercase tracking-wider">Historial</span>
          </button>
        </div>

        <div className="flex items-center gap-3">
          {/* Candado - Modo Bloqueado/Desbloqueado */}
          <button
            onClick={() => {
              const newLockedState = !isLocked;
              setIsLocked(newLockedState);
              // Si se bloquea, desactivar modo COSTO
              if (newLockedState) {
                setShowCostMode(false);
              }
            }}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg font-bold text-xs transition-all ${
              isLocked 
                ? 'bg-white/10 text-white/60 hover:bg-white/20' 
                : 'bg-emerald-500 text-white shadow-lg'
            }`}
            title={isLocked ? 'Desbloquear edición de precios' : 'Bloquear edición'}
          >
            {isLocked ? <Lock size={16} /> : <Unlock size={16} />}
          </button>

          {/* Modo PVP/COSTO - Solo visible si desbloqueado */}
          {!isLocked && (
          <button
            onClick={() => setShowCostMode(!showCostMode)}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg font-bold text-xs uppercase transition-all ${
              showCostMode 
                ? 'bg-purple-600 text-white shadow-lg' 
                : 'bg-white/10 text-white/60 hover:bg-white/20'
            }`}
            title={showCostMode ? 'Ver precio PVP' : `Ver COSTO (-${userDiscount}%)`}
          >
            {showCostMode ? `COSTO -${userDiscount}%` : 'PVP'}
          </button>
          )}

          <div className="flex items-center gap-2 bg-white/10 rounded-lg px-3 py-1.5">
            <span className="text-xs font-bold text-white/60 uppercase">Dto Global:</span>
            <input
              type="number"
              value={globalDiscount}
              onChange={(e) => setGlobalDiscount(parseFloat(e.target.value) || 0)}
              className="w-12 bg-orange-500 text-white text-center font-bold rounded px-2 py-1 text-sm outline-none"
              min="0"
              max="100"
            />
            <span className="text-white/60 font-bold">%</span>
          </div>

          {/* Incremento global - solo visible si desbloqueado */}
          {!isLocked && (
            <div className="flex items-center gap-2 bg-emerald-500/20 rounded-lg px-3 py-1.5">
              <span className="text-xs font-bold text-emerald-300 uppercase">Inc:</span>
              <input
                type="number"
                value={globalMarkup}
                onChange={(e) => setGlobalMarkup(parseFloat(e.target.value) || 0)}
                className="w-12 bg-emerald-500 text-white text-center font-bold rounded px-2 py-1 text-sm outline-none"
                min="0"
                max="100"
              />
              <span className="text-emerald-300 font-bold">%</span>
            </div>
          )}

          <div className="flex items-center gap-2 bg-white/10 rounded-lg px-3 py-1.5">
            <span className="text-xs font-bold text-white/60 uppercase">IVA:</span>
            <select
              value={ivaRate}
              onChange={(e) => setIvaRate(parseFloat(e.target.value))}
              className="bg-transparent text-white font-bold text-sm outline-none cursor-pointer"
            >
              <option value="21" className="text-black">21%</option>
              <option value="10" className="text-black">10%</option>
              <option value="4" className="text-black">4%</option>
              <option value="0" className="text-black">0%</option>
            </select>
          </div>

          <button
            onClick={handleExportPDF}
            disabled={lines.length === 0}
            className="flex items-center gap-2 bg-orange-600 hover:bg-orange-700 disabled:bg-orange-600/50 text-white px-5 py-2.5 rounded-xl font-bold text-xs uppercase tracking-wider transition-colors shadow-lg"
          >
            <Download size={16} />
            PDF
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 overflow-auto p-8">
        {/* Upload Area - shown when no lines */}
        {lines.length === 0 && !isLoading && (
          <div className="max-w-md mx-auto mt-20">
            <div className="bg-white rounded-3xl shadow-xl p-10 text-center">
              <div className="w-16 h-16 bg-indigo-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
                <Upload size={32} className="text-indigo-600" />
              </div>
              <h2 className="text-2xl font-black text-indigo-950 uppercase tracking-tight mb-2">
                Subir Presupuesto
              </h2>
              <p className="text-indigo-400 text-sm mb-6">
                Sube una foto o PDF de tu borrador para digitalizarlo
              </p>
              
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*,application/pdf"
                onChange={handleFileUpload}
                className="hidden"
                id="file-upload"
              />
              <label
                htmlFor="file-upload"
                className="inline-flex items-center gap-2 bg-indigo-950 hover:bg-indigo-800 text-white px-8 py-4 rounded-xl font-black text-sm uppercase tracking-wider cursor-pointer transition-colors shadow-lg"
              >
                <Camera size={20} />
                Seleccionar Foto / PDF
              </label>

              {error && (
                <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-xl flex items-center gap-3">
                  <AlertCircle size={20} className="text-red-500 shrink-0" />
                  <p className="text-red-700 text-sm font-medium">{error}</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Loading State */}
        {isLoading && (
          <div className="max-w-md mx-auto mt-20">
            <div className="bg-white rounded-3xl shadow-xl p-10 text-center">
              <Loader size={48} className="animate-spin text-indigo-600 mx-auto mb-6" />
              <h2 className="text-xl font-black text-indigo-950 uppercase tracking-tight mb-2">
                Analizando Imagen...
              </h2>
              <p className="text-indigo-400 text-sm">
                Extrayendo líneas del presupuesto con IA
              </p>
            </div>
          </div>
        )}

        {/* Results View */}
        {lines.length > 0 && !isLoading && (
          <div className="max-w-5xl mx-auto" id="digitalizador-pdf">
            <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
              {/* Document Header */}
              <div className="p-8 border-b border-indigo-100">
                <div className="flex justify-between items-start">
                  <div className="flex items-center gap-4">
                    <Logo className="h-16 w-auto" customLogo={state.logo} />
                  </div>
                  <div className="text-right">
                    {/* Título editable del documento */}
                    <div className="relative group">
                      <input
                        type="text"
                        value={documentTitle}
                        onChange={(e) => setDocumentTitle(e.target.value)}
                        className="text-2xl font-black text-indigo-950 uppercase tracking-tight text-right bg-transparent outline-none border-b-2 border-transparent hover:border-indigo-200 focus:border-orange-500 w-full no-print"
                        placeholder="Presupuesto Técnico"
                      />
                      <h1 className="print-only text-2xl font-black text-indigo-950 uppercase tracking-tight">
                        {documentTitle || 'Presupuesto Técnico'}
                      </h1>
                    </div>
                    
                    {/* Botón Valorado/No Valorado */}
                    <div className="flex items-center justify-end gap-2 mt-2">
                      <button 
                        onClick={() => setIsValorado(!isValorado)}
                        className={`px-3 py-1 rounded-lg text-[9px] font-black uppercase tracking-wider transition-all no-print ${
                          isValorado 
                            ? 'bg-orange-500 text-white hover:bg-orange-600' 
                            : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
                        }`}
                      >
                        {isValorado ? 'VALORADO' : 'SIN VALORAR'}
                      </button>
                      <p className="print-only text-[9px] font-black uppercase tracking-wider text-orange-600">
                        {isValorado ? 'DOCUMENTO VALORADO' : 'DOCUMENTO SIN VALORACIÓN'}
                      </p>
                    </div>
                    
                    {/* Número de expediente único */}
                    <div className="flex items-center justify-end gap-2 mt-2">
                      <span className="px-3 py-1.5 bg-indigo-100 text-indigo-800 rounded-lg font-black text-sm tracking-wider">
                        {isGeneratingExp ? '...' : expNumber || 'SIN EXP'}
                      </span>
                      <button
                        onClick={generateExpNumber}
                        disabled={isGeneratingExp}
                        className="p-1.5 text-indigo-400 hover:text-indigo-600 hover:bg-indigo-50 rounded transition-colors no-print"
                        title="Generar nuevo número de expediente"
                      >
                        <RefreshCw size={14} className={isGeneratingExp ? 'animate-spin' : ''} />
                      </button>
                    </div>
                    <p className="text-xs text-indigo-400 mt-1">
                      {state.currentUser?.clientName || 'FACTORY 01'} &nbsp; {new Date().toLocaleDateString('es-ES')}
                    </p>
                  </div>
                </div>

                {/* Project Name */}
                <div className="mt-6">
                  <label className="text-[10px] font-black text-indigo-300 uppercase tracking-widest">Proyecto:</label>
                  <input
                    type="text"
                    value={projectName}
                    onChange={(e) => setProjectName(e.target.value)}
                    placeholder="Nombre del proyecto..."
                    className="block text-xl font-black text-indigo-950 uppercase bg-transparent outline-none border-b border-transparent hover:border-indigo-200 focus:border-orange-500 w-full mt-1"
                  />
                </div>

                {/* Config Fields */}
                <div className="grid grid-cols-3 gap-6 mt-6">
                  <div>
                    <label className="text-[10px] font-black text-indigo-300 uppercase tracking-widest block mb-1">Acabado</label>
                    <input
                      type="text"
                      value={acabado}
                      onChange={(e) => setAcabado(e.target.value)}
                      placeholder="-"
                      className="w-full bg-indigo-50/50 border border-indigo-100 rounded-lg px-3 py-2 text-sm font-bold text-indigo-800 outline-none focus:border-orange-500"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] font-black text-indigo-300 uppercase tracking-widest block mb-1">Armazón</label>
                    <input
                      type="text"
                      value={armazon}
                      onChange={(e) => setArmazon(e.target.value)}
                      placeholder="-"
                      className="w-full bg-indigo-50/50 border border-indigo-100 rounded-lg px-3 py-2 text-sm font-bold text-indigo-800 outline-none focus:border-orange-500"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] font-black text-indigo-300 uppercase tracking-widest block mb-1">Costados</label>
                    <input
                      type="text"
                      value={costados}
                      onChange={(e) => setCostados(e.target.value)}
                      placeholder="-"
                      className="w-full bg-indigo-50/50 border border-indigo-100 rounded-lg px-3 py-2 text-sm font-bold text-indigo-800 outline-none focus:border-orange-500"
                    />
                  </div>
                </div>
              </div>

              {/* Page Navigation - Solo si hay más de una página */}
              {totalPages > 1 && (
                <div className="flex justify-center items-center gap-2 my-4 no-print bg-indigo-50 rounded-xl p-3">
                  <button
                    onClick={() => setCurrentPage(0)}
                    disabled={currentPage === 0 || currentPage === -1}
                    className="px-3 py-1.5 bg-white text-indigo-600 rounded-lg font-bold text-xs disabled:opacity-40 hover:bg-indigo-100 transition-colors shadow-sm"
                  >
                    ««
                  </button>
                  <button
                    onClick={() => setCurrentPage(prev => Math.max(0, prev - 1))}
                    disabled={currentPage <= 0}
                    className="px-3 py-1.5 bg-white text-indigo-600 rounded-lg font-bold text-xs disabled:opacity-40 hover:bg-indigo-100 transition-colors shadow-sm"
                  >
                    « Anterior
                  </button>
                  
                  <div className="flex gap-1">
                    {Array.from({ length: totalPages }, (_, i) => (
                      <button
                        key={i}
                        onClick={() => setCurrentPage(i)}
                        className={`w-8 h-8 rounded-lg font-black text-sm transition-colors shadow-sm ${
                          currentPage === i 
                            ? 'bg-indigo-600 text-white' 
                            : 'bg-white text-indigo-600 hover:bg-indigo-100'
                        }`}
                      >
                        {i + 1}
                      </button>
                    ))}
                  </div>
                  
                  <button
                    onClick={() => setCurrentPage(prev => Math.min(totalPages - 1, prev + 1))}
                    disabled={currentPage === totalPages - 1 || currentPage === -1}
                    className="px-3 py-1.5 bg-white text-indigo-600 rounded-lg font-bold text-xs disabled:opacity-40 hover:bg-indigo-100 transition-colors shadow-sm"
                  >
                    Siguiente »
                  </button>
                  <button
                    onClick={() => setCurrentPage(totalPages - 1)}
                    disabled={currentPage === totalPages - 1 || currentPage === -1}
                    className="px-3 py-1.5 bg-white text-indigo-600 rounded-lg font-bold text-xs disabled:opacity-40 hover:bg-indigo-100 transition-colors shadow-sm"
                  >
                    »»
                  </button>
                  
                  <div className="border-l border-indigo-200 pl-3 ml-2">
                    <button
                      onClick={() => setCurrentPage(currentPage === -1 ? 0 : -1)}
                      className={`px-4 py-1.5 rounded-lg font-bold text-xs transition-colors shadow-sm ${
                        currentPage === -1
                          ? 'bg-orange-500 text-white'
                          : 'bg-white text-orange-600 hover:bg-orange-50'
                      }`}
                    >
                      {currentPage === -1 ? '📄 Paginado' : '📋 Ver Todo'}
                    </button>
                  </div>
                  
                  <span className="ml-3 text-xs font-bold text-indigo-500 bg-white px-3 py-1.5 rounded-lg">
                    {currentPage === -1 ? `Mostrando todas (${lines.length} líneas)` : `Pág. ${currentPage + 1}/${totalPages} (${lines.length} líneas)`}
                  </span>
                </div>
              )}

              {/* Lines Table */}
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-indigo-950 text-white">
                    <tr>
                      <th className="px-4 py-3 text-left text-[10px] font-black uppercase tracking-widest w-16">Ct.</th>
                      <th className="px-4 py-3 text-left text-[10px] font-black uppercase tracking-widest w-24">Ref.</th>
                      <th className="px-4 py-3 text-left text-[10px] font-black uppercase tracking-widest">Descripción del Mueble / Artículo</th>
                      {/* Columnas de precio solo si es valorado */}
                      {isValorado && (
                        <>
                          <th className="px-4 py-3 text-center text-[10px] font-black uppercase tracking-widest w-24">Precio</th>
                          <th className="px-4 py-3 text-center text-[10px] font-black uppercase tracking-widest w-20">Dto%</th>
                        </>
                      )}
                      {/* Columna INC% solo visible cuando está desbloqueado y valorado */}
                      {isValorado && !isLocked && globalMarkup > 0 && (
                        <th className="px-4 py-3 text-center text-[10px] font-black uppercase tracking-widest w-20 text-emerald-400">Inc%</th>
                      )}
                      {/* Columna Neto solo si valorado */}
                      {isValorado && (
                        <th className="px-4 py-3 text-right text-[10px] font-black uppercase tracking-widest w-28">Neto</th>
                      )}
                      <th className="px-4 py-3 text-center w-12 no-print"></th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-indigo-50">
                    {(currentPage === -1 ? lines : (pages[currentPage] || [])).map((line) => {
                      // Calcular precio a mostrar según estado del candado
                      const originalPrice = line.price;
                      const priceWithMarkup = originalPrice * (1 + globalMarkup / 100);
                      const displayPrice = isLocked && globalMarkup > 0 ? priceWithMarkup : originalPrice;
                      
                      return (
                      <tr key={line.id} className={`hover:bg-indigo-50/50 transition-colors ${line.isManual ? 'bg-orange-50/30' : ''}`}>
                        <td className="px-4 py-3">
                          <input
                            type="number"
                            value={line.quantity}
                            onChange={(e) => updateLine(line.id, 'quantity', parseInt(e.target.value) || 1)}
                            className="w-12 bg-transparent text-center font-bold text-indigo-900 outline-none border-b border-transparent hover:border-indigo-200 focus:border-orange-500"
                            min="1"
                          />
                        </td>
                        <td className="px-4 py-3">
                          {/* Campo REF ahora es EDITABLE */}
                          <input
                            type="text"
                            value={line.reference || (line.isManual ? 'MANUAL' : 'AUTO')}
                            onChange={(e) => updateLine(line.id, 'reference', e.target.value)}
                            className={`w-20 bg-transparent text-center text-xs font-bold uppercase outline-none border-b border-transparent hover:border-indigo-200 focus:border-orange-500 ${line.isManual ? 'text-orange-600' : 'text-indigo-400'}`}
                          />
                        </td>
                        <td className="px-4 py-3">
                          <input
                            type="text"
                            value={line.description}
                            onChange={(e) => updateLine(line.id, 'description', e.target.value)}
                            className="w-full bg-transparent font-medium text-indigo-900 outline-none border-b border-transparent hover:border-indigo-200 focus:border-orange-500"
                          />
                        </td>
                        {/* Precio y Descuento solo si valorado */}
                        {isValorado && (
                        <>
                        <td className="px-4 py-3 text-center">
                          {/* Precio: muestra original si desbloqueado, o con incremento si bloqueado */}
                          <div className="flex flex-col items-center">
                            <input
                              type="text"
                              value={isLocked ? displayPrice.toFixed(2) : line.price}
                              onChange={(e) => {
                                if (!isLocked) {
                                  const value = e.target.value.replace(',', '.');
                                  updateLine(line.id, 'price', parseFloat(value) || 0);
                                }
                              }}
                              readOnly={isLocked && globalMarkup > 0}
                              className={`w-24 bg-transparent text-center font-bold outline-none border-b border-transparent hover:border-indigo-200 focus:border-orange-500 ${isLocked && globalMarkup > 0 ? 'text-indigo-900' : 'text-indigo-900'}`}
                              placeholder="0.00"
                            />
                            {/* Mostrar precio original tachado si hay markup y está desbloqueado */}
                            {!isLocked && globalMarkup > 0 && (
                              <span className="text-[9px] text-emerald-600 font-bold">
                                → {priceWithMarkup.toFixed(2)}€
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="px-4 py-3 text-center">
                          {/* Descuento SIEMPRE editable - casilla más ancha */}
                          <input
                            type="text"
                            value={line.isManual ? line.discount : (line.discount > 0 ? line.discount : (globalDiscount > 0 ? globalDiscount : ''))}
                            onChange={(e) => {
                              const value = e.target.value.replace(',', '.');
                              updateLine(line.id, 'discount', parseFloat(value) || 0);
                            }}
                            placeholder={line.isManual ? "0" : (globalDiscount > 0 ? String(globalDiscount) : "0")}
                            className={`w-16 bg-indigo-50 rounded px-2 py-1 text-center font-bold outline-none border border-transparent hover:border-indigo-200 focus:border-orange-500 ${line.isManual ? 'text-orange-600 bg-orange-50' : (line.discount > 0 ? 'text-orange-600' : 'text-indigo-600')}`}
                          />
                        </td>
                        </>
                        )}
                        {/* Columna INC% solo visible cuando está desbloqueado y valorado */}
                        {isValorado && !isLocked && globalMarkup > 0 && (
                          <td className="px-4 py-3 text-center">
                            <span className="text-emerald-600 font-bold">{globalMarkup}</span>
                          </td>
                        )}
                        {/* Neto solo si valorado */}
                        {isValorado && (
                        <td className="px-4 py-3 text-right font-black text-indigo-950">
                          {getLineNet(line).toLocaleString('es-ES', { style: 'currency', currency: 'EUR' })}
                        </td>
                        )}
                        <td className="px-4 py-3 text-center no-print">
                          <button
                            onClick={() => deleteLine(line.id)}
                            className="p-1.5 text-indigo-300 hover:text-red-500 transition-colors"
                          >
                            <Trash2 size={16} />
                          </button>
                        </td>
                      </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {/* Add Manual Line Button */}
              <div className="p-6 border-t border-dashed border-indigo-200 no-print">
                <button
                  onClick={addManualLine}
                  className="w-full py-4 border-2 border-dashed border-indigo-200 rounded-xl text-indigo-400 font-bold text-sm uppercase tracking-wider hover:border-orange-400 hover:text-orange-600 transition-colors flex items-center justify-center gap-2"
                >
                  <Plus size={18} />
                  Insertar Línea Manual
                </button>
              </div>

              {/* Totals Footer - Solo si valorado */}
              {isValorado && (
              <div className="bg-indigo-950 text-white p-6">
                <div className="grid grid-cols-4 gap-4">
                  <div className="text-center p-4 bg-indigo-900/50 rounded-xl">
                    <p className="text-[10px] font-bold text-indigo-300 uppercase tracking-widest mb-1">Bruto Líneas</p>
                    <p className="text-xl font-black">{totals.brutoLineas.toLocaleString('es-ES', { style: 'currency', currency: 'EUR' })}</p>
                  </div>
                  <div className="text-center p-4 bg-indigo-900/50 rounded-xl">
                    <p className="text-[10px] font-bold text-indigo-300 uppercase tracking-widest mb-1">Base Imponible (Neto)</p>
                    <p className="text-xl font-black text-indigo-300">{totals.baseImponible.toLocaleString('es-ES', { style: 'currency', currency: 'EUR' })}</p>
                    <p className="text-[9px] text-orange-500 font-bold mt-1">DTO GLOBAL APLICADO</p>
                  </div>
                  <div className="text-center p-4 bg-indigo-900/50 rounded-xl">
                    <p className="text-[10px] font-bold text-indigo-300 uppercase tracking-widest mb-1">IVA ({ivaRate}%)</p>
                    <p className="text-xl font-black text-indigo-300">{totals.iva.toLocaleString('es-ES', { style: 'currency', currency: 'EUR' })}</p>
                  </div>
                  <div className="text-center p-4 bg-orange-600 rounded-xl border-l-4 border-orange-400">
                    <p className="text-[10px] font-bold text-orange-200 uppercase tracking-widest mb-1">Total Presupuesto</p>
                    <p className="text-3xl font-black text-white">{totals.total.toLocaleString('es-ES', { style: 'currency', currency: 'EUR' })}</p>
                  </div>
                </div>
              </div>
              )}

              {/* Footer */}
              <div className="px-6 py-3 bg-white border-t border-indigo-100 flex justify-between items-center text-[9px] text-indigo-300 font-bold uppercase tracking-widest">
                <span>— Luiggi Home Master Report Professional</span>
                <span>Fin de Documento</span>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="mt-6 flex justify-center gap-4 no-print flex-wrap">
              <button
                onClick={handleReset}
                className="flex items-center gap-2 bg-white text-indigo-600 px-6 py-3 rounded-xl font-bold text-sm uppercase tracking-wider hover:bg-indigo-50 transition-colors border border-indigo-200"
              >
                <Upload size={18} />
                Nuevo Presupuesto
              </button>
              <button
                onClick={handleSaveBudget}
                disabled={isSaving}
                className="flex items-center gap-2 bg-green-600 text-white px-6 py-3 rounded-xl font-bold text-sm uppercase tracking-wider hover:bg-green-700 disabled:bg-green-400 transition-colors shadow-lg"
              >
                {isSaving ? <Loader size={18} className="animate-spin" /> : <Save size={18} />}
                Guardar en Historial
              </button>
              <button
                onClick={openCRMModal}
                disabled={isCreatingOpportunity || opportunityCreated}
                className={`flex items-center gap-2 px-6 py-3 rounded-xl font-bold text-sm uppercase tracking-wider transition-colors shadow-lg ${
                  opportunityCreated 
                    ? 'bg-emerald-500 text-white cursor-default' 
                    : 'bg-purple-600 text-white hover:bg-purple-700 disabled:bg-purple-400'
                }`}
                data-testid="create-crm-opportunity-btn"
              >
                {opportunityCreated ? (
                  <>
                    <CheckCircle size={18} />
                    Oportunidad Creada
                  </>
                ) : isCreatingOpportunity ? (
                  <>
                    <Loader size={18} className="animate-spin" />
                    Creando...
                  </>
                ) : (
                  <>
                    <Briefcase size={18} />
                    Crear Oportunidad CRM
                  </>
                )}
              </button>
              <button
                onClick={handleExportCSV}
                className="flex items-center gap-2 bg-indigo-600 text-white px-6 py-3 rounded-xl font-bold text-sm uppercase tracking-wider hover:bg-indigo-700 transition-colors shadow-lg"
              >
                <FileText size={18} />
                Exportar CSV Máquina
              </button>
            </div>

            {/* Success Message */}
            {successMessage && (
              <div className="mt-4 p-4 bg-green-100 border border-green-300 rounded-xl text-center">
                <p className="text-green-700 font-bold">{successMessage}</p>
              </div>
            )}
          </div>
        )}
      </main>

      {/* History Sidebar */}
      {showHistory && (
        <div className="fixed inset-y-0 left-0 w-96 bg-white shadow-2xl z-50 flex flex-col no-print">
          <div className="bg-indigo-950 text-white px-6 py-4 flex justify-between items-center shrink-0">
            <h3 className="font-black uppercase tracking-wider">Historial</h3>
            <button onClick={() => setShowHistory(false)} className="p-1 hover:bg-white/10 rounded">
              <X size={20} />
            </button>
          </div>
          
          {/* Search */}
          <div className="p-4 border-b border-indigo-100 shrink-0">
            <div className="relative">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-indigo-300" />
              <input
                type="text"
                value={historySearch}
                onChange={(e) => setHistorySearch(e.target.value)}
                placeholder="Buscar por proyecto o cliente..."
                className="w-full pl-10 pr-4 py-2 bg-indigo-50 rounded-lg text-sm font-medium text-indigo-900 outline-none focus:ring-2 focus:ring-orange-500"
              />
            </div>
          </div>
          
          <div className="flex-1 overflow-auto p-4 space-y-2">
            {loadingHistory ? (
              <div className="flex justify-center py-8">
                <Loader size={24} className="animate-spin text-indigo-400" />
              </div>
            ) : history.length === 0 ? (
              <p className="text-center text-indigo-400 text-sm py-8">No hay historial</p>
            ) : (
              history.map((entry) => (
                <div 
                  key={entry.id} 
                  onClick={() => loadBudgetFromHistory(entry)}
                  className="p-4 bg-indigo-50 rounded-xl hover:bg-indigo-100 cursor-pointer transition-colors group"
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <p className="font-bold text-indigo-900">{entry.projectName || 'Sin nombre'}</p>
                      {entry.customerName && (
                        <p className="text-xs text-orange-600 font-bold mt-0.5">{entry.customerName}</p>
                      )}
                    </div>
                    <button
                      onClick={(e) => deleteBudgetFromHistory(entry.id, e)}
                      className="p-1.5 text-indigo-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                  <p className="text-xs text-indigo-400 mt-2">
                    {new Date(entry.createdAt).toLocaleString('es-ES')}
                  </p>
                  <div className="flex justify-between items-center mt-1">
                    <p className="text-xs text-indigo-400">
                      {entry.lines?.length || 0} líneas
                    </p>
                    <p className="text-sm font-black text-indigo-900">
                      {(entry.totalConIva || 0).toLocaleString('es-ES', { style: 'currency', currency: 'EUR' })}
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Modal de Opciones de Guardado */}
      {showSaveOptionsModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 no-print">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 overflow-hidden">
            <div className="bg-green-600 text-white px-6 py-4 flex justify-between items-center">
              <div className="flex items-center gap-3">
                <Save size={24} />
                <h3 className="font-black uppercase tracking-wider">Guardar Presupuesto</h3>
              </div>
              <button 
                onClick={() => setShowSaveOptionsModal(false)} 
                className="p-1 hover:bg-white/10 rounded transition-colors"
              >
                <X size={20} />
              </button>
            </div>
            
            <div className="p-6 space-y-4">
              {/* Preview del presupuesto */}
              <div className="bg-green-50 rounded-xl p-4 border border-green-200">
                <p className="text-[10px] font-black text-green-600 uppercase tracking-widest mb-2">Presupuesto</p>
                <p className="font-bold text-green-900 text-lg">{expNumber}</p>
                <p className="text-sm text-green-700">{projectName || 'Sin nombre'}</p>
                <p className="text-2xl font-black text-green-600 mt-2">
                  {totals.total.toLocaleString('es-ES', { style: 'currency', currency: 'EUR' })}
                </p>
                <p className="text-xs text-green-500 mt-1">{lines.length} líneas · IVA {ivaRate}%</p>
              </div>

              {/* Opciones de guardado */}
              <div className="space-y-3">
                <p className="text-[10px] font-black text-indigo-400 uppercase tracking-widest">¿Dónde guardar?</p>
                
                {/* Historial */}
                <label className="flex items-center gap-3 p-3 bg-indigo-50 rounded-xl cursor-pointer hover:bg-indigo-100 transition-colors">
                  <input
                    type="checkbox"
                    checked={saveToHistory}
                    onChange={(e) => setSaveToHistory(e.target.checked)}
                    className="w-5 h-5 rounded border-indigo-300 text-indigo-600 focus:ring-indigo-500"
                  />
                  <div className="flex-1">
                    <p className="font-bold text-indigo-900">Historial Digitalizador</p>
                    <p className="text-xs text-indigo-500">Guardar en el historial del digitalizador</p>
                  </div>
                  <History size={20} className="text-indigo-400" />
                </label>

                {/* Presupuestos */}
                <label className="flex items-center gap-3 p-3 bg-orange-50 rounded-xl cursor-pointer hover:bg-orange-100 transition-colors">
                  <input
                    type="checkbox"
                    checked={saveToPresupuestos}
                    onChange={(e) => setSaveToPresupuestos(e.target.checked)}
                    className="w-5 h-5 rounded border-orange-300 text-orange-600 focus:ring-orange-500"
                  />
                  <div className="flex-1">
                    <p className="font-bold text-orange-900">Presupuestos Principales</p>
                    <p className="text-xs text-orange-500">Guardar junto a los presupuestos de cocina</p>
                  </div>
                  <FileText size={20} className="text-orange-400" />
                </label>

                {/* CRM */}
                <label className="flex items-center gap-3 p-3 bg-purple-50 rounded-xl cursor-pointer hover:bg-purple-100 transition-colors">
                  <input
                    type="checkbox"
                    checked={saveToCRM}
                    onChange={(e) => setSaveToCRM(e.target.checked)}
                    className="w-5 h-5 rounded border-purple-300 text-purple-600 focus:ring-purple-500"
                  />
                  <div className="flex-1">
                    <p className="font-bold text-purple-900">Crear Oportunidad CRM</p>
                    <p className="text-xs text-purple-500">Crear contacto y oportunidad en el CRM</p>
                  </div>
                  <Briefcase size={20} className="text-purple-400" />
                </label>
              </div>

              {/* Campos CRM si está marcado */}
              {saveToCRM && (
                <div className="space-y-3 pt-3 border-t border-purple-200">
                  <p className="text-[10px] font-black text-purple-400 uppercase tracking-widest">Datos del Cliente para CRM</p>
                  <input
                    type="text"
                    value={crmContactName}
                    onChange={(e) => setCrmContactName(e.target.value)}
                    placeholder="Nombre del cliente *"
                    className="w-full bg-purple-50 border border-purple-200 rounded-lg px-4 py-2.5 text-sm font-medium text-purple-900 outline-none focus:border-purple-500"
                  />
                  <div className="grid grid-cols-2 gap-2">
                    <input
                      type="email"
                      value={crmContactEmail}
                      onChange={(e) => setCrmContactEmail(e.target.value)}
                      placeholder="Email"
                      className="bg-purple-50 border border-purple-200 rounded-lg px-3 py-2 text-sm font-medium text-purple-900 outline-none focus:border-purple-500"
                    />
                    <input
                      type="tel"
                      value={crmContactPhone}
                      onChange={(e) => setCrmContactPhone(e.target.value)}
                      placeholder="Teléfono"
                      className="bg-purple-50 border border-purple-200 rounded-lg px-3 py-2 text-sm font-medium text-purple-900 outline-none focus:border-purple-500"
                    />
                  </div>
                  <input
                    type="text"
                    value={crmCompany}
                    onChange={(e) => setCrmCompany(e.target.value)}
                    placeholder="Empresa (opcional)"
                    className="w-full bg-purple-50 border border-purple-200 rounded-lg px-4 py-2 text-sm font-medium text-purple-900 outline-none focus:border-purple-500"
                  />
                </div>
              )}

              {error && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2">
                  <AlertCircle size={16} className="text-red-500 shrink-0" />
                  <p className="text-red-700 text-sm font-medium">{error}</p>
                </div>
              )}
            </div>

            <div className="px-6 pb-6 flex gap-3">
              <button
                onClick={() => setShowSaveOptionsModal(false)}
                className="flex-1 px-4 py-3 bg-gray-100 text-gray-700 rounded-xl font-bold text-sm uppercase tracking-wider hover:bg-gray-200 transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={executeSave}
                disabled={isSaving || (!saveToHistory && !saveToPresupuestos && !saveToCRM)}
                className="flex-1 px-4 py-3 bg-green-600 text-white rounded-xl font-bold text-sm uppercase tracking-wider hover:bg-green-700 disabled:bg-green-400 transition-colors shadow-lg flex items-center justify-center gap-2"
              >
                {isSaving ? (
                  <>
                    <Loader size={16} className="animate-spin" />
                    Guardando...
                  </>
                ) : (
                  <>
                    <Save size={16} />
                    Guardar
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* CRM Opportunity Modal */}
      {showCRMModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 no-print">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 overflow-hidden">
            <div className="bg-purple-600 text-white px-6 py-4 flex justify-between items-center">
              <div className="flex items-center gap-3">
                <Briefcase size={24} />
                <h3 className="font-black uppercase tracking-wider">Nueva Oportunidad CRM</h3>
              </div>
              <button 
                onClick={() => setShowCRMModal(false)} 
                className="p-1 hover:bg-white/10 rounded transition-colors"
              >
                <X size={20} />
              </button>
            </div>
            
            <div className="p-6 space-y-4">
              {/* Preview del presupuesto */}
              <div className="bg-purple-50 rounded-xl p-4 border border-purple-100">
                <p className="text-[10px] font-black text-purple-400 uppercase tracking-widest mb-2">Presupuesto a vincular</p>
                <p className="font-bold text-purple-900 text-lg">{projectName || 'Sin nombre de proyecto'}</p>
                <p className="text-2xl font-black text-purple-600 mt-1">
                  {totals.total.toLocaleString('es-ES', { style: 'currency', currency: 'EUR' })}
                </p>
                <p className="text-xs text-purple-400 mt-1">{lines.length} líneas · IVA {ivaRate}% incluido</p>
              </div>

              {/* Datos del contacto */}
              <div>
                <label className="text-[10px] font-black text-indigo-400 uppercase tracking-widest block mb-1">
                  Nombre del Cliente *
                </label>
                <input
                  type="text"
                  value={crmContactName}
                  onChange={(e) => setCrmContactName(e.target.value)}
                  placeholder="Nombre completo del cliente"
                  className="w-full bg-indigo-50 border border-indigo-100 rounded-lg px-4 py-3 text-sm font-medium text-indigo-900 outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-200"
                  data-testid="crm-contact-name"
                />
              </div>

              <div>
                <label className="text-[10px] font-black text-indigo-400 uppercase tracking-widest block mb-1">
                  Empresa
                </label>
                <input
                  type="text"
                  value={crmCompany}
                  onChange={(e) => setCrmCompany(e.target.value)}
                  placeholder="Nombre de la empresa (opcional)"
                  className="w-full bg-indigo-50 border border-indigo-100 rounded-lg px-4 py-3 text-sm font-medium text-indigo-900 outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-200"
                  data-testid="crm-company"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-[10px] font-black text-indigo-400 uppercase tracking-widest block mb-1">
                    Email
                  </label>
                  <input
                    type="email"
                    value={crmContactEmail}
                    onChange={(e) => setCrmContactEmail(e.target.value)}
                    placeholder="email@ejemplo.com"
                    className="w-full bg-indigo-50 border border-indigo-100 rounded-lg px-4 py-3 text-sm font-medium text-indigo-900 outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-200"
                    data-testid="crm-contact-email"
                  />
                </div>
                <div>
                  <label className="text-[10px] font-black text-indigo-400 uppercase tracking-widest block mb-1">
                    Teléfono
                  </label>
                  <input
                    type="tel"
                    value={crmContactPhone}
                    onChange={(e) => setCrmContactPhone(e.target.value)}
                    placeholder="+34 600 000 000"
                    className="w-full bg-indigo-50 border border-indigo-100 rounded-lg px-4 py-3 text-sm font-medium text-indigo-900 outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-200"
                    data-testid="crm-contact-phone"
                  />
                </div>
              </div>

              {error && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2">
                  <AlertCircle size={16} className="text-red-500 shrink-0" />
                  <p className="text-red-700 text-sm font-medium">{error}</p>
                </div>
              )}
            </div>

            <div className="px-6 pb-6 flex gap-3">
              <button
                onClick={() => setShowCRMModal(false)}
                className="flex-1 px-4 py-3 bg-gray-100 text-gray-700 rounded-xl font-bold text-sm uppercase tracking-wider hover:bg-gray-200 transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={handleCreateOpportunity}
                disabled={isCreatingOpportunity || !crmContactName.trim()}
                className="flex-1 px-4 py-3 bg-purple-600 text-white rounded-xl font-bold text-sm uppercase tracking-wider hover:bg-purple-700 disabled:bg-purple-400 transition-colors shadow-lg flex items-center justify-center gap-2"
                data-testid="confirm-create-opportunity-btn"
              >
                {isCreatingOpportunity ? (
                  <>
                    <Loader size={16} className="animate-spin" />
                    Creando...
                  </>
                ) : (
                  <>
                    <Briefcase size={16} />
                    Crear Oportunidad
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Digitalizador;
