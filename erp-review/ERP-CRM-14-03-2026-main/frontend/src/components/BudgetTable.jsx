import { ShoppingCart, Printer, Trash2, Save, LayoutPanelTop, Search, Plus, PanelLeftClose, PanelLeftOpen, PanelRightClose, PanelRightOpen, PanelBottomClose, PanelBottomOpen, PanelTopClose, PanelTopOpen, FileText, ChevronDown, ChevronUp, Hash, Tag, Info, AlertCircle, Lock, Unlock, Palette, Box, Layers, Filter, PaintBucket, Keyboard, PenTool, Download, Scissors, CheckCircle, Paperclip, Mail, X, Upload, Image, FileImage, LayoutGrid, LayoutList, ArrowRightLeft, LogOut, Package, Factory, Wand2, Library } from 'lucide-react';
import React, { useMemo, useState, useCallback, useEffect, useRef } from 'react';
import { exportToPdf } from '../utils/pdfHelper';
import { generateBudgetPDF } from '../services/pdfGenerator';
import { DOOR_FINISHES, MV_TARIFFS, CabinetCategory } from '../constants';
import Logo from './Logo';
import DespieceModal from './DespieceModal';
import DespieceCatalog from './DespieceCatalog';
import DespieceWizard from './DespieceWizard';
import ClientSelector from './ClientSelector';
import CabinetIcon from './CabinetIcon';
// Componentes refactorizados
import { 
  DespieceAddModal,
  DespieceStepByStep,
  DespieceFiltersHorizontal, 
  DespieceFiltersVertical,
  MontadaFiltersHorizontal,
  MontadaFiltersVertical,
  CatalogProductRowTable,
  CatalogProductRowCard
} from './budget';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const BudgetTable = ({ items, catalogs, activeCatalogIds, state, setState, onOpenManufacturing }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedPrograma, setSelectedPrograma] = useState('TODOS');
  const [selectedSeries, setSelectedSeries] = useState('TODAS');
  const [selectedCategory, setSelectedCategory] = useState('TODAS');
  const [selectedApertura, setSelectedApertura] = useState('TODAS');
  // Filtros de medidas
  const [filterWidth, setFilterWidth] = useState('');
  const [filterHeight, setFilterHeight] = useState('');
  const [filterDepth, setFilterDepth] = useState('');
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
  // Estados para el catálogo de tableros (modo despiece) - REQUERIDOS para la UI existente
  const [despieceProducts, setDespieceProducts] = useState([]);
  const [despieceFilters, setDespieceFilters] = useState({
    manufacturer: '',
    collection: '',
    finish: '',
    thickness: ''
  });
  const [despieceFilterOptions, setDespieceFilterOptions] = useState({
    manufacturers: [],
    collections: [],
    finishes: [],
    thicknesses: []
  });
  const [loadingDespiece, setLoadingDespiece] = useState(false);
  const [despieceAddModal, setDespieceAddModal] = useState({
    isOpen: false,
    product: null,
    width: 600,
    height: 800,
    quantity: 1
  });
  const [isDespieceWizardOpen, setIsDespieceWizardOpen] = useState(false);
  const [isConfirmOrderOpen, setIsConfirmOrderOpen] = useState(false);
  const [orderAttachments, setOrderAttachments] = useState([]);
  const [orderEmail, setOrderEmail] = useState('');
  const [orderNotes, setOrderNotes] = useState('');
  const [isSendingOrder, setIsSendingOrder] = useState(false);
  const [orderSent, setOrderSent] = useState(false);
  const [isValorado, setIsValorado] = useState(true);  // Toggle para mostrar/ocultar precios
  const [showExitConfirm, setShowExitConfirm] = useState(false); // Diálogo de confirmación al salir
  const [sortColumn, setSortColumn] = useState(null); // Columna de ordenación: 'code', 'name', 'width', 'height', 'depth', 'points'
  const [sortDirection, setSortDirection] = useState('asc'); // 'asc' o 'desc'
  const [useMillimeters, setUseMillimeters] = useState(() => {
    const saved = localStorage.getItem('luiggi_use_millimeters');
    return saved === 'true';
  }); // Toggle para mm/cm
  
  // Estado para tarifa/zona seleccionada (MV: T1-T15, ZC: Z1-Z12)
  const [selectedTariff, setSelectedTariff] = useState(() => {
    const saved = localStorage.getItem('luiggi_selected_tariff');
    return saved || 'T1';
  });
  const [selectedZone, setSelectedZone] = useState(() => {
    const saved = localStorage.getItem('luiggi_selected_zone');
    return saved || 'Z1';
  });
  
  // Guardar preferencia cuando cambie
  useEffect(() => {
    localStorage.setItem('luiggi_selected_tariff', selectedTariff);
  }, [selectedTariff]);
  useEffect(() => {
    localStorage.setItem('luiggi_selected_zone', selectedZone);
  }, [selectedZone]);
  useEffect(() => {
    localStorage.setItem('luiggi_use_millimeters', useMillimeters.toString());
  }, [useMillimeters]);
  
  // Función para formatear medidas según la unidad seleccionada
  const formatMeasure = useCallback((value) => {
    if (value === null || value === undefined || value === '') return '-';
    const numValue = parseFloat(value);
    if (isNaN(numValue)) return '-';
    return useMillimeters ? Math.round(numValue * 10) : numValue;
  }, [useMillimeters]);
  
  // Función para parsear valores de input (convierte de la unidad visual a CM para almacenamiento)
  const parseMeasureInput = useCallback((inputValue) => {
    const numValue = parseInt(inputValue) || 0;
    // Si está en MM, dividimos por 10 para guardar en CM
    return useMillimeters ? Math.round(numValue / 10) : numValue;
  }, [useMillimeters]);
  
  const measureUnit = useMillimeters ? 'mm' : 'cm';
  
  const isResizingSidebar = useRef(false);
  const isResizingCatalog = useRef(false);
  const isResizingCatalogWidth = useRef(false);

  // Función para cambiar la ordenación
  const handleSort = (column) => {
    if (sortColumn === column) {
      // Si ya está ordenado por esta columna, cambiar dirección
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      // Nueva columna, ordenar ascendente
      setSortColumn(column);
      setSortDirection('asc');
    }
  };

  // Detectar si hay líneas sin guardar
  const hasUnsavedItems = useMemo(() => {
    const montadaItems = state.budgetItemsMontada || [];
    const despieceItems = state.budgetItemsDespiece || [];
    return montadaItems.length > 0 || despieceItems.length > 0;
  }, [state.budgetItemsMontada, state.budgetItemsDespiece]);

  // Advertir al usuario si intenta cerrar la ventana con líneas sin guardar
  useEffect(() => {
    const handleBeforeUnload = (e) => {
      if (hasUnsavedItems) {
        e.preventDefault();
        e.returnValue = '¿Seguro que quieres salir? Tienes líneas sin guardar.';
        return e.returnValue;
      }
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [hasUnsavedItems]);

  // Guardar preferencia cuando cambie
  useEffect(() => {
    localStorage.setItem('luiggi_catalog_position', catalogPosition);
  }, [catalogPosition]);

  // Helper para obtener precio según tarifa/zona seleccionada
  const getProductPrice = useCallback((product) => {
    if (!product) return 0;
    const isMV = product.library === 'MV';
    const zp = product.zonePoints || {};
    
    if (isMV) {
      // MV: usar tarifa seleccionada (T1-T21)
      return zp[selectedTariff] ?? zp.T1 ?? (typeof product.points === 'number' ? product.points : product.points?.T1) ?? 0;
    } else {
      // ZC: usar GRUPO DE PRECIOS (globalFinish -> mapea a Z1-Z12)
      const finishObj = DOOR_FINISHES.find(f => f.name === state.globalFinish) || DOOR_FINISHES[0];
      const zoneKey = finishObj.group; // Z1, Z2, etc.
      return zp[zoneKey] ?? zp.Z1 ?? (typeof product.points === 'number' ? product.points : product.points?.Z1) ?? 0;
    }
  }, [selectedTariff, state.globalFinish]);

  // Cargar productos de despiece cuando cambie el módulo a despiece
  useEffect(() => {
    if (state.currentModule === 'despiece') {
      loadDespieceFilterOptions();
      loadDespieceProducts();
    }
  }, [state.currentModule]);

  // Cargar filtros disponibles para despiece
  const loadDespieceFilterOptions = async () => {
    try {
      const response = await fetch(`${API_URL}/api/despiece-budgeter/products/filters`);
      const data = await response.json();
      setDespieceFilterOptions(data);
    } catch (error) {
      console.error('Error loading despiece filter options:', error);
    }
  };

  // Cargar productos de despiece con filtros
  const loadDespieceProducts = async () => {
    setLoadingDespiece(true);
    try {
      const params = new URLSearchParams();
      if (despieceFilters.manufacturer) params.append('manufacturer', despieceFilters.manufacturer);
      if (despieceFilters.collection) params.append('collection', despieceFilters.collection);
      if (despieceFilters.finish) params.append('finish', despieceFilters.finish);
      if (despieceFilters.thickness) params.append('thickness', despieceFilters.thickness);
      if (despieceFilters.type) params.append('type', despieceFilters.type);
      
      const response = await fetch(`${API_URL}/api/despiece-budgeter/products?${params.toString()}`);
      const data = await response.json();
      setDespieceProducts(data);
    } catch (error) {
      console.error('Error loading despiece products:', error);
      setDespieceProducts([]);
    } finally {
      setLoadingDespiece(false);
    }
  };

  // Recargar productos cuando cambien los filtros de despiece
  useEffect(() => {
    if (state.currentModule === 'despiece') {
      const debounce = setTimeout(() => {
        loadDespieceProducts();
      }, 300);
      return () => clearTimeout(debounce);
    }
  }, [despieceFilters]);

  // Función para añadir producto de despiece al presupuesto
  const addDespieceProductToBudget = (product, width, height, quantity = 1) => {
    const areaM2 = (width / 1000) * (height / 1000);
    const pricePerM2 = product.priceZ1 || 0;
    const totalPrice = areaM2 * pricePerM2 * quantity;
    
    const newItem = {
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
      depth: product.thickness,
      quantity: quantity,
      areaM2: areaM2,
      pricePerM2: pricePerM2,
      unitPrice: totalPrice / quantity,
      totalPrice: totalPrice,
      category: product.category,
      isDespiece: true
    };
    
    setState(prev => ({
      ...prev,
      budgetItemsDespiece: [...(prev.budgetItemsDespiece || []), newItem]
    }));
  };

  // Funciones para gestionar items de despiece
  const handleAddDespieceItem = useCallback((item) => {
    setState(prev => ({
      ...prev,
      budgetItemsDespiece: [...(prev.budgetItemsDespiece || []), item]
    }));
  }, []);

  const handleRemoveDespieceItem = useCallback((itemId) => {
    setState(prev => ({
      ...prev,
      budgetItemsDespiece: (prev.budgetItemsDespiece || []).filter(item => item.id !== itemId)
    }));
  }, []);

  const handleUpdateDespieceItem = useCallback((itemId, field, value) => {
    setState(prev => ({
      ...prev,
      budgetItemsDespiece: (prev.budgetItemsDespiece || []).map(item => {
        if (item.id !== itemId) return item;
        const updated = { ...item, [field]: value };
        // Recalcular precio si cambia cantidad
        if (field === 'quantity') {
          updated.totalPrice = updated.unitPrice * value;
        }
        return updated;
      })
    }));
  }, []);

  const allProducts = useMemo(() => {
    return catalogs
      .filter(c => activeCatalogIds.includes(c.id))
      .flatMap(c => c.products.map(p => ({ ...p, catalogId: c.id })));
  }, [catalogs, activeCatalogIds]);

  // Programas únicos
  const uniqueProgramas = useMemo(() => {
    const currentModuleProducts = allProducts.filter(p => 
      catalogs.find(c => c.id === p.catalogId)?.module === state.currentModule
    );
    const programas = new Set(currentModuleProducts.map(p => p.programa || 'ESTÁNDAR'));
    return Array.from(programas).sort();
  }, [allProducts, state.currentModule, catalogs]);

  const uniqueCategories = useMemo(() => {
    const currentModuleProducts = allProducts.filter(p => 
      catalogs.find(c => c.id === p.catalogId)?.module === state.currentModule
    );
    // Filtrar por programa si está seleccionado
    let programaFilteredProducts = selectedPrograma === 'TODOS'
      ? currentModuleProducts
      : currentModuleProducts.filter(p => (p.programa || 'ESTÁNDAR') === selectedPrograma);
    
    // También aplicar filtros de medidas si están activos
    if (filterHeight) {
      const heightNum = parseInt(filterHeight);
      programaFilteredProducts = programaFilteredProducts.filter(p => p.height && Math.abs(Number(p.height) - heightNum) <= 5);
    }
    if (filterWidth) {
      const widthNum = parseInt(filterWidth);
      programaFilteredProducts = programaFilteredProducts.filter(p => p.width && Math.abs(Number(p.width) - widthNum) <= 5);
    }
    if (filterDepth) {
      const depthNum = parseInt(filterDepth);
      programaFilteredProducts = programaFilteredProducts.filter(p => p.depth && Math.abs(Number(p.depth) - depthNum) <= 5);
    }
    
    // Las categorías vienen directamente de los productos filtrados por programa
    // No necesitamos filtrado adicional por nombre
    let categories = new Set(programaFilteredProducts.map(p => p.category || 'OTROS'));
    
    // Orden de categorías según el catálogo
    const categoryOrder = {
      'ALTOS': 1,
      'ALTOS GOLA': 2,
      'ALTOS ALUMINIO': 3,
      'SOBREMÓDULOS': 4,
      'BAJOS': 5,
      'BAJOS GOLA': 6,
      'BAJOS ALUMINIO': 7,
      'SEMICOLUMNAS': 8,
      'SEMICOLUMNAS GOLA': 9,
      'SEMICOLUMNAS ALUMINIO': 10,
      'COLUMNAS': 11,
      'COLUMNAS GOLA': 12,
      'COSTADOS': 13,
      'ESTANTES': 14,
      'REGLETAS': 15,
      'PUERTAS': 16,
      'VITRINAS': 17,
      'CORNISAS': 18,
      'ZOCALOS': 19,
      'COMPLEMENTOS': 20,
      'ELECTRODOMESTICOS': 21,
      'ACCESORIOS': 22,
      'OTROS': 99
    };
    
    return Array.from(categories).sort((a, b) => {
      const orderA = categoryOrder[a] || 50;
      const orderB = categoryOrder[b] || 50;
      return orderA - orderB;
    });
  }, [allProducts, state.currentModule, catalogs, selectedPrograma, filterWidth, filterHeight, filterDepth]);

  const uniqueSeries = useMemo(() => {
    const currentModuleProducts = allProducts.filter(p => 
      catalogs.find(c => c.id === p.catalogId)?.module === state.currentModule
    );
    // Filtrar por programa si está seleccionado
    let filteredProducts = selectedPrograma === 'TODOS'
      ? currentModuleProducts
      : currentModuleProducts.filter(p => (p.programa || 'ESTÁNDAR') === selectedPrograma);
    // Filter by category if one is selected
    filteredProducts = selectedCategory === 'TODAS' 
      ? filteredProducts 
      : filteredProducts.filter(p => (p.category || 'OTROS') === selectedCategory);
    
    // También aplicar filtros de medidas si están activos
    if (filterHeight) {
      const heightNum = parseInt(filterHeight);
      filteredProducts = filteredProducts.filter(p => p.height && Math.abs(Number(p.height) - heightNum) <= 5);
    }
    if (filterWidth) {
      const widthNum = parseInt(filterWidth);
      filteredProducts = filteredProducts.filter(p => p.width && Math.abs(Number(p.width) - widthNum) <= 5);
    }
    if (filterDepth) {
      const depthNum = parseInt(filterDepth);
      filteredProducts = filteredProducts.filter(p => p.depth && Math.abs(Number(p.depth) - depthNum) <= 5);
    }
    
    const series = new Set(filteredProducts.map(p => p.series || 'GENERAL'));
    return Array.from(series).sort();
  }, [allProducts, state.currentModule, catalogs, selectedPrograma, selectedCategory, filterWidth, filterHeight, filterDepth]);

  // Aperturas únicas (solo para MV o productos con apertura definida)
  const uniqueAperturas = useMemo(() => {
    let filteredProducts = allProducts;
    
    if (state.currentModule === 'montada') {
      filteredProducts = catalogs
        .filter(c => c.module === 'montada')
        .flatMap(c => c.products || []);
    }
    
    // Filtrar por serie si está seleccionada
    if (selectedSeries !== 'TODAS') {
      filteredProducts = filteredProducts.filter(p => (p.series || 'GENERAL') === selectedSeries);
    }
    
    const aperturas = new Set(filteredProducts.filter(p => p.apertura).map(p => p.apertura));
    return Array.from(aperturas).sort();
  }, [allProducts, state.currentModule, catalogs, selectedSeries]);

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

  // Función para limpiar código (quitar D/I de la referencia)
  const cleanCode = useCallback((code) => {
    if (!code) return '';
    // Quitar D/I, /I del código para mostrar
    return code.replace(/D\/I/g, '').replace(/\/I/g, '').trim();
  }, []);

  // Función helper para detectar tipo de mueble especial
  const getSpecialType = useCallback((code, name) => {
    const c = code?.toUpperCase() || '';
    const n = name?.toUpperCase() || '';
    
    // Por código primero - ORDEN IMPORTANTE: detectar combinados primero
    // HORNO + MICRO (HM en cualquier posición, CHM, PHM, VHM)
    if (c.includes('HM') || c.includes('CHM') || c.includes('PHM') || c.includes('VHM')) return 'HORNO+MICRO';
    // Solo MICRO (AM, BM)
    if (c.includes('AM') || c.includes('BM')) return 'MICRO';
    // Solo HORNO (CH, BH, PH, VH)
    if (c.includes('CH') || c.includes('BH') || c.includes('PH') || c.includes('VH')) return 'HORNO';
    if (c.includes('BP')) return 'PLACA';
    if (c.includes('BF')) return 'FREG';
    if (c.includes('AT')) return 'TERMO';
    if (c.includes('AE')) return 'ESCURRE';
    if (c.includes('AC')) return 'CAMPANA';
    if (c.includes('PE') || c.includes('PEL') || c.includes('PEB')) return 'EXTRAÍBLE';
    if (c.includes('BOT')) return 'BOTELLERO';
    if (c.includes('ESC')) return 'ESCOBERO';
    if (c.includes('FRI')) return 'FRIGO';
    
    // Por nombre si no se detectó por código
    if (n.includes('HORNO') && n.includes('MICRO')) return 'HORNO+MICRO';
    if (n.includes('MICROONDAS') || n.includes('MICRO')) return 'MICRO';
    if (n.includes('HORNO')) return 'HORNO';
    if (n.includes('PLACA') || n.includes('VITRO')) return 'PLACA';
    if (n.includes('FREGADERO') || n.includes('FREG')) return 'FREG';
    if (n.includes('TERMO') || n.includes('CALENTADOR')) return 'TERMO';
    if (n.includes('ESCURREPLATOS') || n.includes('ESCURRE')) return 'ESCURRE';
    if (n.includes('CAMPANA')) return 'CAMPANA';
    if (n.includes('EXTRAIBLE') || n.includes('EXTRAÍBLE')) return 'EXTRAÍBLE';
    if (n.includes('BOTELLERO')) return 'BOTELLERO';
    if (n.includes('ESCOBERO')) return 'ESCOBERO';
    if (n.includes('FRIGO') || n.includes('FRIGORÍFICO')) return 'FRIGO';
    if (n.includes('CACEROLERO')) return 'CAJONES';
    if (n.includes('CAJONES') || n.includes('CAJÓN')) return 'CAJONES';
    
    return null;
  }, []);

  const filteredCatalog = useMemo(() => {
    const q = searchQuery.toLowerCase().trim();
    
    console.log('Search query:', q, '| Length:', q.length);
    
    // Orden según el catálogo PDF TARIFA-TECNICA-ZONACOCINAS
    const categoryOrder = {
      'ALTO': 1, 'ALTOS': 1,
      'ALTOS GOLA': 2,
      'ALTOS ALUMINIO': 3,
      'SOBREMÓDULOS': 4,
      'BAJO': 5, 'BAJOS': 5,
      'BAJOS GOLA': 6,
      'BAJOS ALUMINIO': 7,
      'SEMICOLUMNA': 8, 'SEMICOLUMNAS': 8,
      'SEMICOLUMNAS GOLA': 9,
      'SEMICOLUMNAS ALUMINIO': 10,
      'COLUMNA': 11, 'COLUMNAS': 11,
      'COLUMNAS GOLA': 12,
      'COSTADOS': 13,
      'ESTANTES': 14,
      'REGLETAS': 15,
      'PUERTAS': 16,
      'VITRINAS': 17,
      'CORNISAS': 18,
      'ZOCALOS': 19,
      'COMPLEMENTOS': 20,
      'ELECTRO': 21, 'ELECTRODOMESTICOS': 21,
      'ACCESORIO': 22, 'ACCESORIOS': 22,
      'OTRO': 99, 'OTROS': 99
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
      const qUpper = q.toUpperCase().trim();
      const refUpper = (p.reference || '').toUpperCase();
      const descUpper = (p.description || '').toUpperCase();
      
      let matchesSearch = false;
      
      if (q && q.length > 0) {
        // Búsqueda FLEXIBLE: busca en código, nombre, referencia y descripción
        matchesSearch = 
          codeUpper.includes(qUpper) || 
          nameUpper.includes(qUpper) || 
          refUpper.includes(qUpper) ||
          descUpper.includes(qUpper);
      } else {
        // Sin búsqueda, mostrar todo
        matchesSearch = true;
      }
      
      const isCorrectModule = catalogs.find(c => c.id === p.catalogId)?.module === state.currentModule;
      
      // Si hay búsqueda activa, ignorar filtros de programa/categoría/serie
      const hasActiveSearch = q && q.length >= 2;
      const matchesPrograma = hasActiveSearch || selectedPrograma === 'TODOS' || (p.programa || 'ESTÁNDAR') === selectedPrograma;
      const matchesSeries = hasActiveSearch || selectedSeries === 'TODAS' || (p.series || 'GENERAL') === selectedSeries;
      const matchesCategory = hasActiveSearch || selectedCategory === 'TODAS' || (p.category || 'OTROS') === selectedCategory;
      const matchesApertura = hasActiveSearch || selectedApertura === 'TODAS' || !p.apertura || p.apertura === selectedApertura;
      
      // Filtro de medidas (ancho, alto, fondo)
      let matchesMedidas = true;
      if (filterWidth) {
        const widthNum = parseInt(filterWidth);
        matchesMedidas = matchesMedidas && p.width && Math.abs(Number(p.width) - widthNum) <= 5;
      }
      if (filterHeight) {
        const heightNum = parseInt(filterHeight);
        matchesMedidas = matchesMedidas && p.height && Math.abs(Number(p.height) - heightNum) <= 5;
      }
      if (filterDepth) {
        const depthNum = parseInt(filterDepth);
        matchesMedidas = matchesMedidas && p.depth && Math.abs(Number(p.depth) - depthNum) <= 5;
      }
      
      const result = matchesSearch && isCorrectModule && matchesPrograma && matchesSeries && matchesCategory && matchesApertura && matchesMedidas;
      
      // Log para depuración
      if (q && q.length > 5 && result) {
        console.log('MATCH:', codeUpper, '| startsWith:', codeUpper.startsWith(qUpper), '| module:', isCorrectModule);
      }
      
      return result;
    });
    
    // Ordenar: primero coincidencias exactas/por inicio, luego por categoría y código
    const qUpper = q.toUpperCase();
    let sorted = filtered.sort((a, b) => {
      // Si hay una columna de ordenación seleccionada, usar esa
      if (sortColumn) {
        let valA, valB;
        switch (sortColumn) {
          case 'code':
            valA = a.code || '';
            valB = b.code || '';
            break;
          case 'name':
            valA = a.name || '';
            valB = b.name || '';
            break;
          case 'width':
            valA = Number(a.width) || 0;
            valB = Number(b.width) || 0;
            break;
          case 'height':
            valA = Number(a.height) || 0;
            valB = Number(b.height) || 0;
            break;
          case 'depth':
            valA = Number(a.depth) || 0;
            valB = Number(b.depth) || 0;
            break;
          case 'points':
            // Usar la tarifa/zona seleccionada
            valA = Number(getProductPrice(a)) || 0;
            valB = Number(getProductPrice(b)) || 0;
            break;
          default:
            valA = a.code || '';
            valB = b.code || '';
        }
        
        // Comparar
        let comparison = 0;
        if (typeof valA === 'number' && typeof valB === 'number') {
          comparison = valA - valB;
        } else {
          comparison = String(valA).localeCompare(String(valB));
        }
        
        return sortDirection === 'desc' ? -comparison : comparison;
      }
      
      // Ordenación por defecto (sin columna seleccionada)
      // Priorizar coincidencias que empiezan con el término de búsqueda
      if (q) {
        const aStartsWith = a.code?.toUpperCase().startsWith(qUpper) ? 0 : 1;
        const bStartsWith = b.code?.toUpperCase().startsWith(qUpper) ? 0 : 1;
        if (aStartsWith !== bStartsWith) return aStartsWith - bStartsWith;
      }
      
      const catA = categoryOrder[a.category?.toUpperCase()] || 99;
      const catB = categoryOrder[b.category?.toUpperCase()] || 99;
      if (catA !== catB) return catA - catB;
      
      // Para ALTOS, ordenar primero los de altura 90 (más utilizados)
      const isAltosA = a.category?.toUpperCase().includes('ALTOS');
      const isAltosB = b.category?.toUpperCase().includes('ALTOS');
      if (isAltosA && isAltosB) {
        // Altura 90 tiene prioridad
        const heightA = Number(a.height) || 0;
        const heightB = Number(b.height) || 0;
        const is90A = heightA >= 88 && heightA <= 92 ? 0 : 1;
        const is90B = heightB >= 88 && heightB <= 92 ? 0 : 1;
        if (is90A !== is90B) return is90A - is90B;
      }
      
      // Dentro de la misma categoría, ordenar por código
      return a.code.localeCompare(b.code);
    });
    
    return sorted;
  }, [allProducts, searchQuery, state.currentModule, catalogs, selectedPrograma, selectedSeries, selectedCategory, selectedApertura, filterWidth, filterHeight, filterDepth, sortColumn, sortDirection, selectedTariff, state.globalFinish, getProductPrice]);

  const budgetKey = state.currentModule === 'montada' ? 'budgetItemsMontada' : 'budgetItemsDespiece';

  const addItemToBudget = (product) => {
    setState(prev => {
      const currentItems = prev[budgetKey];
      
      // Buscar si ya existe una línea con el mismo producto (mismo productId y mismas dimensiones)
      const existingItemIndex = currentItems.findIndex(item => 
        item.productId === product.id && 
        !item.isManual &&
        item.customWidth === Number(product.width) &&
        item.customHeight === Number(product.height) &&
        item.customDepth === Number(product.depth)
      );
      
      if (existingItemIndex >= 0) {
        // Si existe, incrementar la cantidad
        const updatedItems = [...currentItems];
        updatedItems[existingItemIndex] = {
          ...updatedItems[existingItemIndex],
          quantity: updatedItems[existingItemIndex].quantity + 1
        };
        return { ...prev, [budgetKey]: updatedItems };
      } else {
        // Si no existe, crear nueva línea
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
          hasVigaCut: false
        };
        return { ...prev, [budgetKey]: [...currentItems, newItem] };
      }
    });
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

  // Obtener grosor de trasera del armazón seleccionado
  const carcassBackThickness = useMemo(() => {
    const selectedMaterial = state.carcassMaterials.find(m => m.id === state.selectedCarcassMaterialId);
    return selectedMaterial?.backThickness || 8; // Default 8mm
  }, [state.carcassMaterials, state.selectedCarcassMaterialId]);

  const calculateLineDetails = useCallback((item, product) => {
     // Para montada, usar el valor de punto de la biblioteca activa
     // Para despiece, usar pointValueDespiece (común)
     const currentLibrary = state.currentLibrary || 'ZC';
     const libraryPointValue = state.libraryPointValues?.[currentLibrary] || state.pointValueMontada || 1.0;
     const pointValue = state.currentModule === 'montada' ? libraryPointValue : state.pointValueDespiece;
     
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
         const isMV = state.currentLibrary === 'MV';
         
         // Para MV, buscar en MV_TARIFFS; para ZC, buscar en DOOR_FINISHES
         const finishObj = isMV 
           ? (MV_TARIFFS.find(f => f.name === currentFinish) || MV_TARIFFS[0])
           : (DOOR_FINISHES.find(f => f.name === currentFinish) || DOOR_FINISHES[0]);
         
         let productBasePoints = 100;
         if (typeof product.points === 'number') productBasePoints = product.points;
         else if (typeof product.points === 'object' && product.points !== null) {
           // Para MV usar T1, para ZC usar Z1
           productBasePoints = isMV 
             ? (product.points.T1 || product.points.Z1 || 100) 
             : (product.points.Z1 || 100);
         }
         
         // Para MV, usar tariffPrices; para ZC, usar zonePoints
         if (isMV && product.tariffPrices) {
           usedPoints = product.tariffPrices[finishObj.group] ?? productBasePoints;
         } else {
           usedPoints = product.zonePoints?.[finishObj.group] ?? productBasePoints;
         }
         finalProductName = product.name;

         // NO aplicar incrementos por medidas en COSTADOS y REGLETAS
         const categoryUpper = (product.category || '').toUpperCase();
         const isExcludedCategory = categoryUpper.includes('COSTADO') || categoryUpper.includes('REGLETA');
         
         // Obtener incrementos de la biblioteca activa (o usar los globales como fallback)
         const currentLibrary = state.currentLibrary || 'ZC';
         const libIncrements = state.librarySpecialIncrements?.[currentLibrary] || {
           width: state.specialIncrementWidth,
           height: state.specialIncrementHeight,
           depth: state.specialIncrementDepth
         };
         
         if (!isExcludedCategory) {
           if (Number(item.customWidth) !== Number(product.width)) { cutsCost += libIncrements.width; cuts.push('Ancho'); }
           if (Number(item.customHeight) !== Number(product.height)) { cutsCost += libIncrements.height; cuts.push('Alto'); }
           if (Number(item.customDepth) !== Number(product.depth)) { cutsCost += libIncrements.depth; cuts.push('Fondo'); }
         }

         const selectedMaterial = state.carcassMaterials.find(m => m.id === state.selectedCarcassMaterialId);
         carcassCost = selectedMaterial?.fixedIncrement || 0;
     }
     
     // Añadir incremento por corte de viga si está marcado (por biblioteca)
     // Usamos currentLibrary ya declarada arriba
     const vigaCutValue = state.libraryVigaCutIncrements?.[currentLibrary] || state.vigaCutIncrement || 0;
     const vigaCost = item.hasVigaCut ? vigaCutValue : 0;
     
     // LÍNEAS MANUALES: El valor introducido es directamente en €, NO se multiplica por punto
     // LÍNEAS DE LIBRERÍA: Se multiplica puntos × valor del punto
     const pointsCost = item.isManual ? usedPoints : (usedPoints * pointValue);
     const unitPrice = item.isManual 
       ? pointsCost  // Manual: valor directo en €, sin extras ni incrementos
       : (pointsCost + cutsCost + carcassCost + vigaCost);  // Librería: con extras
     
     // Usar descuento específico según el módulo actual
     // IMPORTANTE: Usar ?? en lugar de || para respetar 0 como valor válido
     const discountPct = state.currentModule === 'despiece' 
       ? (state.currentUser?.discountDespiece ?? state.currentUser?.commercialDiscount ?? 0)
       : (state.currentUser?.discountMontada ?? state.currentUser?.commercialDiscount ?? 0);
     // Las líneas manuales NUNCA tienen descuento ni se afectan por modo PVP/COSTO
     const discountFactor = (item.isManual) ? 1 : (state.showDistributorPrice ? (1 - discountPct / 100) : 1);
     
     const finalPrice = (unitPrice * item.quantity) * discountFactor;

     const breakdown = `
DESGLOSE DE PRECIO:
-------------------
${item.isManual ? `• Valor Manual: ${usedPoints.toFixed(2)} €` : `• Puntos Base: ${usedPoints} pts
• Valor Punto: ${pointValue.toFixed(2)} €/pt
  (Subtotal Mueble: ${pointsCost.toFixed(2)}€)`}

${!item.isManual ? `EXTRAS APLICADOS:
• Armazón: +${carcassCost.toFixed(2)}€
• Cortes Especiales (${cuts.length}): +${cutsCost.toFixed(2)}€${vigaCost > 0 ? `
• Corte Viga: +${vigaCost.toFixed(2)}€` : ''}` : '• (Artículo Manual / Neto)'}

PRECIO UNITARIO: ${unitPrice.toFixed(2)}€
CANTIDAD: x${item.quantity}
${state.showDistributorPrice ? `DTO. COMERCIAL (${state.currentModule?.toUpperCase()}): -${discountPct}%` : ''}
`.trim();

     return { total: finalPrice, breakdown, hasExtras: (carcassCost > 0 || cutsCost > 0 || vigaCost > 0), usedPoints, vigaCost };
  }, [state.globalFinish, state.currentModule, state.pointValueMontada, state.pointValueDespiece, state.libraryPointValues, state.currentLibrary, state.specialIncrementWidth, state.specialIncrementHeight, state.specialIncrementDepth, state.librarySpecialIncrements, state.showDistributorPrice, state.currentUser?.commercialDiscount, state.currentUser?.discountMontada, state.currentUser?.discountDespiece, state.selectedCarcassMaterialId, state.carcassMaterials, state.vigaCutIncrement, state.libraryVigaCutIncrements]);


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
          // Obtener siguiente número disponible (usando código de provincia del usuario)
          const provinciaCode = state.currentUser?.provinciaCode || '';
          const expUrl = provinciaCode 
            ? `${process.env.REACT_APP_BACKEND_URL}/api/expedient/next?client_code=${encodeURIComponent(provinciaCode)}`
            : `${process.env.REACT_APP_BACKEND_URL}/api/expedient/next`;
          const expResponse = await fetch(expUrl);
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
        clientCode: state.clientCode || '',  // Código de cliente para agrupar
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
        // Perfiles GOLA
        golaAlto: state.golaAlto || false,
        golaAltoColor: state.golaAltoColor || '',
        golaBajo: state.golaBajo || false,
        golaBajoColor: state.golaBajoColor || '',
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

      // Obtener siguiente número de expediente (sin código de cliente ya que se limpiará)
      // El próximo expediente se generará cuando se seleccione un nuevo cliente
      let nextBudgetNumber = '';
      // No pre-generamos expediente, el usuario usará AUTO cuando tenga nuevo cliente

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
        clientCode: '',  // Limpiar código de cliente
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
      
      // Datos de usuario y proyecto
      formData.append('userId', state.currentUser?.id || '');
      formData.append('projectReference', state.projectReference || '');
      
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
        
        // LIMPIAR PRESUPUESTO después de confirmar pedido
        setState(prev => ({
          ...prev,
          budgetItemsMontada: [],
          budgetItemsDespiece: [],
          budgetNumber: '',
          customerName: '',
          customerAddress: '',
          projectReference: '',
          // Mantener configuraciones de colores y acabados
        }));
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
           
           {/* Botón para ocultar/mostrar barra lateral izquierda */}
           <button 
             onClick={() => setIsConfigOpen(!isConfigOpen)} 
             className={`p-3 rounded-xl transition-all shadow-lg border-2 ${isConfigOpen ? 'bg-indigo-900 text-white border-indigo-700 hover:bg-indigo-800' : 'bg-orange-500 text-white border-orange-400 hover:bg-orange-600'}`}
             title={isConfigOpen ? "Ocultar panel izquierdo" : "Mostrar panel izquierdo"}
           >
              {isConfigOpen ? <PanelLeftClose size={20} /> : <PanelLeftOpen size={20} />}
           </button>
        </div>
        
        <div className="flex gap-3 items-center">
          {/* Pestaña ARMARIOS - Solo para usuarios con permiso específico */}
          {state.currentUser?.canAccessArmarios && (
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
                companyName: 'LUIGGI HOME',
                globalFinish: state.globalFinish,
                allProducts: allProducts,
                calculateLineDetails: calculateLineDetails,
                golaAlto: state.golaAlto,
                golaAltoColor: state.golaAltoColor,
                golaBajo: state.golaBajo,
                golaBajoColor: state.golaBajoColor
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
        <aside 
          style={{ width: isConfigOpen ? sidebarWidth : 0, minWidth: isConfigOpen ? sidebarWidth : 0 }} 
          className={`bg-white border-r border-indigo-50 flex flex-col no-print transition-all duration-300 relative shadow-inner h-[calc(100vh-70px)] ${!isConfigOpen ? 'opacity-0 pointer-events-none overflow-hidden' : 'opacity-100'}`}
        >
           {isConfigOpen && <div onMouseDown={() => { isResizingSidebar.current = true; }} className="absolute top-0 right-0 w-1.5 h-full cursor-ew-resize hover:bg-orange-600 z-50"></div>}
           <div className={`p-3 space-y-2 overflow-y-auto scrollbar-thin flex-1 ${!isConfigOpen ? 'invisible' : 'visible'}`}>
              <section className="space-y-2">
                 <h4 className="text-[8px] font-black text-indigo-300 uppercase tracking-widest italic flex items-center gap-1">DATOS EXPEDIENTE</h4>
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
                              // Usar código de provincia del usuario logueado
                              const provinciaCode = state.currentUser?.provinciaCode || '';
                              const url = provinciaCode 
                                ? `${process.env.REACT_APP_BACKEND_URL}/api/expedient/next?client_code=${encodeURIComponent(provinciaCode)}`
                                : `${process.env.REACT_APP_BACKEND_URL}/api/expedient/next`;
                              const response = await fetch(url);
                              const data = await response.json();
                              if (data.success) {
                                setState(p => ({...p, budgetNumber: data.expedient}));
                              }
                            } catch (err) {
                              console.error('Error getting expedient:', err);
                            }
                          }}
                          className="bg-orange-600 hover:bg-orange-700 text-white px-2 rounded-lg text-[8px] font-black transition-colors"
                          title={state.currentUser?.provinciaCode ? `Generar expediente para ${state.currentUser.provinciaCode}` : "Generar número de expediente automático (configura provincia en tu perfil)"}
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
                        // Guardar también el ID y código del cliente seleccionado
                        setState(p => ({
                          ...p, 
                          customerName: client.nombre,
                          clientCode: client.codigo || client.id?.substring(0, 8).toUpperCase() || '',
                          selectedClientId: client.id,
                          customerPhone: client.telefono || '',
                          customerEmail: client.email || ''
                        }));
                      }}
                      placeholder="Buscar o crear cliente..."
                    />
                    {/* Campo de código de cliente */}
                    <div className="relative mt-1">
                      <Hash size={12} className="absolute left-2 top-1/2 -translate-y-1/2 text-purple-400" />
                      <input 
                        type="text" 
                        value={state.clientCode || ''} 
                        onChange={e => setState(p => ({...p, clientCode: e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, '')}))} 
                        placeholder="Cód. Cliente (auto)" 
                        className="w-full bg-purple-50/50 border border-purple-200 rounded-lg py-2 pl-7 pr-2 text-[9px] font-black outline-none focus:border-purple-500 uppercase text-purple-800"
                        title="Código de cliente para agrupar presupuestos"
                        maxLength={10}
                      />
                    </div>
                 </div>
              </section>
              
              {/* SELECTOR DE TARIFA/BIBLIOTECA - Solo si el usuario tiene más de una */}
              {state.allowedLibraries?.length > 1 && (
              <section className="space-y-1.5 pt-2 border-t border-amber-200">
                 <h4 className="text-[9px] font-black text-amber-700 uppercase tracking-widest flex items-center gap-1">
                   <Library size={10} />
                   TARIFA ACTIVA
                 </h4>
                 <select 
                   className="w-full bg-amber-50 text-amber-900 border-2 border-amber-300 rounded-xl p-2 text-[11px] font-black outline-none cursor-pointer focus:border-amber-500 text-center" 
                   value={state.currentLibrary || 'ZC'}
                   onChange={e => {
                     const newLib = e.target.value;
                     
                     // GUARDAR en localStorage para persistir entre sesiones
                     try {
                       localStorage.setItem('luiggi_active_library', newLib);
                     } catch (err) {
                       console.error("Error saving library:", err);
                     }
                     
                     // Llamar a la función de cambio de biblioteca del padre
                     if (setState) {
                       // Cargar productos de la nueva biblioteca
                       fetch(`${API_URL}/api/products?library=${newLib}&module=montada`)
                         .then(r => r.json())
                         .then(productsMontada => {
                           fetch(`${API_URL}/api/products?library=${newLib}&module=despiece`)
                             .then(r => r.json())
                             .then(productsDespiece => {
                               // Resetear el grupo de precios al primer grupo de la nueva biblioteca
                               const defaultFinish = newLib === 'MV' ? 'TARIFA 1' : 'GRUPO 1';
                               setState(prev => ({
                                 ...prev,
                                 currentLibrary: newLib,
                                 globalFinish: defaultFinish,
                                 catalogs: [
                                   { id: 'cat-m-base', name: `${newLib} - Montada`, manufacturer: newLib, products: productsMontada, module: 'montada', library: newLib },
                                   { id: 'cat-d-base', name: `${newLib} - Despiece`, manufacturer: newLib, products: productsDespiece, module: 'despiece', library: newLib }
                                 ]
                               }));
                             });
                         });
                     }
                   }}
                   data-testid="library-selector"
                 >
                   {state.allowedLibraries?.map(lib => (
                     <option key={lib} value={lib}>
                       {lib === 'ZC' ? '📦 ZC (Zonas Z1-Z12)' : lib === 'MV' ? '📦 MV (Tarifas T1-T21)' : `📦 ${lib}`}
                     </option>
                   ))}
                 </select>
              </section>
              )}
              
              {/* TARIFA MV - Selector unificado para MV (T1-T21) */}
              {state.currentModule === 'montada' && state.currentLibrary === 'MV' && (
              <section className="space-y-1.5 pt-2 border-t border-orange-100">
                 <h4 className="text-[9px] font-black text-orange-600 uppercase tracking-widest">
                   💰 TARIFA MV
                 </h4>
                 <select 
                   className="w-full bg-orange-50 text-orange-900 border-2 border-orange-200 rounded-xl p-2 text-[10px] font-black outline-none cursor-pointer focus:border-orange-500 text-center" 
                   value={selectedTariff}
                   onChange={e => {
                     const newTariff = e.target.value;
                     setSelectedTariff(newTariff);
                     // Sincronizar con globalFinish para MV
                     const tariffNum = parseInt(newTariff.replace('T', ''));
                     setState(p => ({...p, globalFinish: `TARIFA ${tariffNum}`}));
                   }}
                   data-testid="tariff-selector-mv"
                 >
                   {[...Array(15)].map((_, i) => (
                     <option key={`T${i+1}`} value={`T${i+1}`}>
                       Tarifa T{i+1}
                     </option>
                   ))}
                 </select>
                 <p className="text-[8px] text-slate-400 text-center">
                   Los precios se muestran según {selectedTariff}
                 </p>
              </section>
              )}
              
              {/* MEDIDAS + Tolerancia Puertas - Todo en una línea */}
              <section className="pt-1.5 border-t border-slate-200">
                <div className="flex items-center justify-between gap-2">
                  {/* CM/MM Toggle */}
                  <div className="flex items-center gap-1.5">
                    <span className="text-[7px] font-black text-slate-500 uppercase">CM/MM</span>
                    <button
                      onClick={() => setUseMillimeters(!useMillimeters)}
                      className={`flex items-center gap-0.5 px-1.5 py-0.5 rounded-md border transition-all text-[7px] font-bold ${
                        useMillimeters 
                          ? 'bg-blue-50 border-blue-300 text-blue-700' 
                          : 'bg-emerald-50 border-emerald-300 text-emerald-700'
                      }`}
                      data-testid="unit-toggle"
                    >
                      <span className={!useMillimeters ? 'opacity-100' : 'opacity-40'}>CM</span>
                      <span className="text-slate-300">/</span>
                      <span className={useMillimeters ? 'opacity-100' : 'opacity-40'}>MM</span>
                    </button>
                  </div>
                  {/* Tolerancia Puertas */}
                  <div className="flex items-center gap-1.5">
                    <span className="text-[7px] font-black text-slate-500 uppercase">TOL.</span>
                    <div className="flex items-center gap-1 px-1.5 py-1 bg-emerald-50 border border-emerald-200 rounded-md">
                      <span className="text-[8px] text-emerald-600 font-bold">A:</span>
                      <input 
                        type="number" 
                        value={state.doorToleranceHeight ?? 2} 
                        onChange={e => setState(p => ({...p, doorToleranceHeight: parseFloat(e.target.value) || 0}))} 
                        className="w-8 h-5 bg-white border border-emerald-300 rounded text-[10px] font-bold text-center text-emerald-700 outline-none focus:border-orange-500"
                        step="0.5" min="0" max="10"
                        data-testid="door-tolerance-height"
                      />
                      <span className="text-[8px] text-emerald-600 font-bold">N:</span>
                      <input 
                        type="number" 
                        value={state.doorToleranceWidth ?? 3} 
                        onChange={e => setState(p => ({...p, doorToleranceWidth: parseFloat(e.target.value) || 0}))} 
                        className="w-8 h-5 bg-white border border-emerald-300 rounded text-[10px] font-bold text-center text-emerald-700 outline-none focus:border-orange-500"
                        step="0.5" min="0" max="10"
                        data-testid="door-tolerance-width"
                      />
                    </div>
                  </div>
                </div>
              </section>
              
              {/* GRUPO DE PRECIOS - Solo para ZC en modo MONTADA */}
              {state.currentModule === 'montada' && state.currentLibrary === 'ZC' && (
              <section className="space-y-1.5 pt-2 border-t border-orange-100">
                 <h4 className="text-[9px] font-black text-orange-600 uppercase tracking-widest">
                   GRUPO DE PRECIOS
                 </h4>
                 <select 
                   className="w-full bg-orange-50 text-orange-900 border-2 border-orange-200 rounded-xl p-2 text-[10px] font-black outline-none cursor-pointer focus:border-orange-500 text-center" 
                   value={state.globalFinish} 
                   onChange={e => setState(p => ({...p, globalFinish: e.target.value}))}
                 >
                   {DOOR_FINISHES.map(f => (
                     <option key={f.name} value={f.name}>
                       {f.name}
                     </option>
                   ))}
                 </select>
              </section>
              )}

              {/* SELECCIÓN MATERIAL DESPIECE - Solo en modo DESPIECE */}
              {state.currentModule === 'despiece' && (
              <section className="space-y-1.5 pt-2 border-t border-purple-200">
                 <h4 className="text-[9px] font-black text-purple-600 uppercase tracking-widest">
                   <Factory size={10} className="inline mr-1" />
                   MATERIAL DESPIECE
                 </h4>
                 <select 
                   className="w-full bg-purple-50 text-purple-900 border-2 border-purple-200 rounded-xl p-2 text-[10px] font-black outline-none cursor-pointer focus:border-purple-500 text-center" 
                   value={despieceFilters.manufacturer}
                   onChange={e => setDespieceFilters(prev => ({...prev, manufacturer: e.target.value}))}
                 >
                   <option value="">🏭 TODOS FABRICANTES</option>
                   {despieceFilterOptions.manufacturers.map(m => (
                     <option key={m} value={m}>{m}</option>
                   ))}
                 </select>
                 <select 
                   className="w-full bg-purple-50 text-purple-900 border-2 border-purple-200 rounded-xl p-2 text-[10px] font-black outline-none cursor-pointer focus:border-purple-500 text-center" 
                   value={despieceFilters.collection}
                   onChange={e => setDespieceFilters(prev => ({...prev, collection: e.target.value}))}
                 >
                   <option value="">📦 TODAS COLECCIONES</option>
                   {despieceFilterOptions.collections.map(c => (
                     <option key={c} value={c}>{c}</option>
                   ))}
                 </select>
                 <select 
                   className="w-full bg-purple-50 text-purple-900 border-2 border-purple-200 rounded-xl p-2 text-[10px] font-black outline-none cursor-pointer focus:border-purple-500 text-center" 
                   value={despieceFilters.finish}
                   onChange={e => setDespieceFilters(prev => ({...prev, finish: e.target.value}))}
                 >
                   <option value="">✨ TODOS ACABADOS</option>
                   {despieceFilterOptions.finishes.map(f => (
                     <option key={f} value={f}>{f}</option>
                   ))}
                 </select>
                 <div className="flex gap-1">
                   <select 
                     className="flex-1 bg-purple-50 text-purple-900 border-2 border-purple-200 rounded-xl p-2 text-[9px] font-black outline-none cursor-pointer focus:border-purple-500 text-center" 
                     value={despieceFilters.thickness}
                     onChange={e => setDespieceFilters(prev => ({...prev, thickness: e.target.value}))}
                   >
                     <option value="">📏 GROSOR</option>
                     {despieceFilterOptions.thicknesses.map(t => (
                       <option key={t} value={t}>{t}mm</option>
                     ))}
                   </select>
                   {(despieceFilters.manufacturer || despieceFilters.collection || despieceFilters.finish || despieceFilters.thickness) && (
                     <button 
                       onClick={() => setDespieceFilters({manufacturer: '', collection: '', finish: '', thickness: ''})}
                       className="p-2 bg-red-100 text-red-500 rounded-xl hover:bg-red-200 transition-colors"
                       title="Limpiar filtros"
                     >
                       <X size={12} />
                     </button>
                   )}
                 </div>
                 <p className="text-[8px] text-purple-400 text-center font-bold">
                   {despieceProducts.length} productos
                 </p>
                 {/* Botón para abrir el Wizard de Despiece */}
                 <button 
                   onClick={() => setIsDespieceWizardOpen(true)}
                   className="w-full mt-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white py-2.5 rounded-xl font-black uppercase text-[9px] tracking-wider flex items-center justify-center gap-2 transition-all shadow-lg"
                   data-testid="despiece-wizard-btn"
                 >
                   <Wand2 size={14}/> WIZARD DESPIECE
                 </button>
              </section>
              )}
              
              {/* ARMAZÓN - Solo en modo MONTADA - Filtrado por biblioteca */}
              {state.currentModule === 'montada' && (
              <section className="space-y-1.5 pt-2 border-t border-orange-100">
                 <h4 className="text-[9px] font-black text-orange-600 uppercase tracking-widest">ARMAZÓN ({state.currentLibrary})</h4>
                 <select className="w-full bg-orange-50 text-orange-900 border-2 border-orange-200 rounded-xl p-2 text-[9px] font-black outline-none cursor-pointer focus:border-orange-500" value={state.selectedCarcassMaterialId} onChange={e => setState(p => ({...p, selectedCarcassMaterialId: e.target.value}))}>
                    {state.carcassMaterials
                      .filter(m => !m.library || m.library === state.currentLibrary)
                      .map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
                 </select>
              </section>
              )}

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
                 <h4 className="text-[9px] font-black text-orange-600 uppercase tracking-widest">COLORES</h4>
                 <div className="grid grid-cols-2 gap-1">
                    <input type="text" value={state.doorColorLow} onChange={e => setState(p => ({...p, doorColorLow: e.target.value}))} className="bg-orange-50 border border-orange-200 rounded-lg p-1.5 text-[8px] font-bold outline-none focus:border-orange-500 text-orange-900" placeholder="P.Bajos" />
                    <input type="text" value={state.doorColorHigh} onChange={e => setState(p => ({...p, doorColorHigh: e.target.value}))} className="bg-orange-50 border border-orange-200 rounded-lg p-1.5 text-[8px] font-bold outline-none focus:border-orange-500 text-orange-900" placeholder="P.Altos" />
                    <input type="text" value={state.doorColorColumns} onChange={e => setState(p => ({...p, doorColorColumns: e.target.value}))} className="bg-orange-50 border border-orange-200 rounded-lg p-1.5 text-[8px] font-bold outline-none focus:border-orange-500 text-orange-900" placeholder="P.Colum" />
                    <input type="text" value={state.sideColor} onChange={e => setState(p => ({...p, sideColor: e.target.value}))} className="bg-orange-50 border border-orange-200 rounded-lg p-1.5 text-[8px] font-bold outline-none focus:border-orange-500 text-orange-900" placeholder="Costados" />
                 </div>
                 {/* Checkbox VETA */}
                 <div className="flex items-center gap-2 mt-1 p-1.5 bg-amber-50 border border-amber-200 rounded-lg">
                    <input 
                      type="checkbox" 
                      checked={state.doorHasVeta === true} 
                      onChange={e => setState(p => ({...p, doorHasVeta: e.target.checked}))} 
                      className="w-3.5 h-3.5 accent-amber-600"
                      id="doorHasVeta"
                    />
                    <label htmlFor="doorHasVeta" className="text-[8px] font-bold text-amber-800 cursor-pointer select-none">
                      PUERTA CON VETA (dirección de la fibra)
                    </label>
                 </div>
              </section>

              {/* PERFILES GOLA - Compacto */}
              <section className="space-y-1 pt-2 border-t border-orange-100">
                 <h4 className="text-[9px] font-black text-purple-600 uppercase tracking-widest">🔲 GOLA</h4>
                 <div className="grid grid-cols-2 gap-1">
                    {/* GOLA ALTO */}
                    <div className="flex items-center gap-1">
                       <input 
                         type="checkbox" 
                         checked={state.golaAlto || false} 
                         onChange={e => setState(p => ({...p, golaAlto: e.target.checked, golaAltoColor: e.target.checked ? p.golaAltoColor : ''}))} 
                         className="w-3 h-3 accent-purple-600"
                       />
                       <input 
                         type="text" 
                         value={state.golaAltoColor || ''} 
                         onChange={e => setState(p => ({...p, golaAltoColor: e.target.value, golaAlto: true}))} 
                         className="flex-1 bg-purple-50 border border-purple-200 rounded p-1 text-[8px] font-bold outline-none focus:border-purple-500 text-purple-900" 
                         placeholder="Alto"
                         disabled={!state.golaAlto}
                       />
                    </div>
                    {/* GOLA BAJO */}
                    <div className="flex items-center gap-1">
                       <input 
                         type="checkbox" 
                         checked={state.golaBajo || false} 
                         onChange={e => setState(p => ({...p, golaBajo: e.target.checked, golaBajoColor: e.target.checked ? p.golaBajoColor : ''}))} 
                         className="w-3 h-3 accent-purple-600"
                       />
                       <input 
                         type="text" 
                         value={state.golaBajoColor || ''} 
                         onChange={e => setState(p => ({...p, golaBajoColor: e.target.value, golaBajo: true}))} 
                         className="flex-1 bg-purple-50 border border-purple-200 rounded p-1 text-[8px] font-bold outline-none focus:border-purple-500 text-purple-900" 
                         placeholder="Bajo"
                         disabled={!state.golaBajo}
                       />
                    </div>
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
                 <button 
                   onClick={() => {
                     if (hasUnsavedItems) {
                       setShowExitConfirm(true);
                     } else {
                       setState(prev => ({ 
                         ...prev, 
                         budgetItemsMontada: [], 
                         budgetItemsDespiece: [],
                         budgetNumber: '',
                         customerName: '',
                         customerAddress: '',
                         internalReference: '',
                         existingProjectId: null
                       }));
                     }
                   }} 
                   className="w-full bg-slate-600 text-white py-2 rounded-xl font-black uppercase text-[9px] tracking-widest flex items-center justify-center gap-2 hover:bg-slate-700 transition-all"
                 >
                    <LogOut size={14}/> NUEVO PRESUPUESTO
                 </button>
              </div>
           </div>
        </aside>

        <div 
          className="flex-1 overflow-y-auto p-12 pb-64 bg-indigo-50/30 scrollbar-thin transition-all duration-300"
          style={{ 
            paddingRight: catalogPosition === 'vertical' ? (isCatalogOpen ? catalogWidth + 48 : 60) : 48,
            paddingBottom: catalogPosition === 'horizontal' && isCatalogOpen ? catalogHeight + 48 : 256,
            paddingTop: catalogPosition === 'top' && isCatalogOpen ? catalogHeight + 48 : 48
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
                     <h1 className="text-2xl font-black italic uppercase text-indigo-950 tracking-tighter leading-none">PRESUPUESTO</h1>
                     {/* Toggle Valorado / No Valorado */}
                     <button 
                       onClick={() => setIsValorado(!isValorado)}
                       className={`mt-1 px-3 py-1 rounded-lg text-[9px] font-black uppercase tracking-wider transition-all no-print ${
                         isValorado 
                           ? 'bg-orange-500 text-white hover:bg-orange-600' 
                           : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
                       }`}
                     >
                       {isValorado ? 'DOCUMENTO VALORADO' : 'DOCUMENTO SIN VALORACIÓN'}
                     </button>
                     <p className="print-only text-[9px] font-black uppercase tracking-wider mt-1 text-orange-600">
                       {isValorado ? 'DOCUMENTO VALORADO' : 'DOCUMENTO SIN VALORACIÓN'}
                     </p>
                     <div className="mt-2 space-y-0.5">
                        <p className="text-[9px] font-black text-indigo-300 uppercase">Nº EXP: <span className="text-indigo-950">{state.budgetNumber}</span></p>
                        {state.internalReference && <p className="text-[8px] font-black text-indigo-300 uppercase">REF: <span className="text-orange-600">{state.internalReference}</span></p>}
                        {state.customerName && <p className="text-[8px] font-black text-indigo-950 uppercase italic tracking-widest">CLIENTE: {state.customerName}</p>}
                     </div>
                  </div>
               </div>

               <div className="bg-indigo-50/30 p-1.5 rounded-xl border border-indigo-100 mb-2 space-y-1">
                 {/* Fila 1: Acabado, Armazón, Costados */}
                 <div className="flex items-center gap-2 text-[7px]">
                    <span className="flex items-center gap-0.5 bg-indigo-950 text-white px-1 py-0.5 rounded text-[6px] font-black"><Palette size={8}/> {state.globalFinish}</span>
                    <span className="flex items-center gap-0.5 bg-orange-600 text-white px-1 py-0.5 rounded text-[6px] font-black"><Box size={8}/> {carcassMaterialName?.split(' ').slice(0, 2).join(' ')}</span>
                    <span className="flex items-center gap-0.5 bg-indigo-700 text-white px-1 py-0.5 rounded text-[6px] font-black"><Layers size={8}/> {state.sideColor || 'FRENTES'}</span>
                 </div>

                 {/* Fila 2: Colores puertas (si hay) */}
                 {(state.doorColorLow || state.doorColorHigh || state.doorColorColumns) && (
                   <div className="flex flex-wrap gap-1 text-[6px]">
                      {state.doorColorLow && <span className="px-1 py-0.5 bg-indigo-100 text-indigo-800 rounded font-bold">Bajos: {state.doorColorLow}</span>}
                      {state.doorColorHigh && <span className="px-1 py-0.5 bg-indigo-100 text-indigo-800 rounded font-bold">Altos: {state.doorColorHigh}</span>}
                      {state.doorColorColumns && <span className="px-1 py-0.5 bg-indigo-100 text-indigo-800 rounded font-bold">Col: {state.doorColorColumns}</span>}
                   </div>
                 )}
                 
                 {/* Fila 3: GOLA (si hay) */}
                 {(state.golaAlto || state.golaBajo) && (
                   <div className="flex gap-1 text-[6px]">
                      {state.golaAlto && <span className="px-1 py-0.5 bg-purple-600 text-white rounded font-bold">G.Alto: {state.golaAltoColor || 'Sí'}</span>}
                      {state.golaBajo && <span className="px-1 py-0.5 bg-purple-600 text-white rounded font-bold">G.Bajo: {state.golaBajoColor || 'Sí'}</span>}
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
                     <div className="w-11 text-center shrink-0">AN<span className="text-orange-400 text-[5px]">({measureUnit})</span></div>
                     <div className="w-11 text-center shrink-0">AL<span className="text-orange-400 text-[5px]">({measureUnit})</span></div>
                     <div className="w-11 text-center shrink-0">FO<span className="text-orange-400 text-[5px]">({measureUnit})</span></div>
                     <div className="w-8 text-center shrink-0">AP</div>
                     <div className="w-20 shrink-0">OBS</div>
                     {/* Columna de precio solo si es valorado */}
                     {isValorado && (
                       <div className="w-20 text-right shrink-0 pr-2">€</div>
                     )}
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
                    
                    // Detectar si es mueble que NO necesita selector D/I (Derecha/Izquierda)
                    // - Muebles de 2 puertas
                    // - Semicolumnas con 2 puertas
                    // - Muebles con cajones o gavetas (con o sin horno)
                    const productName = product.name?.toLowerCase() || '';
                    const productCode = product.code || '';
                    const productRef = product.reference || '';
                    
                    const isTwoDoor = productName.includes('2 puerta') || 
                                      productName.includes('2p') ||
                                      productCode.includes('2P') ||
                                      product.visualType === '2P';
                    
                    // Semicolumnas con 2 puertas
                    const isSemicolumnaTwoDoor = (productName.includes('semicolumna') || productRef.startsWith('SC') || productRef.startsWith('10') || productRef.startsWith('11')) &&
                                                  (productName.includes('2 puerta') || productCode.includes('2P'));
                    
                    // Muebles con cajones o gavetas (incluye los que tienen horno)
                    const hasDrawersOrGavetas = productName.includes('cajón') || 
                                                productName.includes('cajon') ||
                                                productName.includes('cajones') ||
                                                productName.includes('gaveta') ||
                                                productName.includes('gavetas') ||
                                                productName.includes('cacerolero') ||
                                                productCode.includes('CB') ||  // Cajón Bax
                                                productCode.includes('CL') ||  // Cajón Lux
                                                /^\d+[A-Z]*\d*C/.test(productCode);  // Código con C para cajones (ej: 7B3C, 10SC3C) pero no GOLA
                    
                    // Determinar si NO necesita selector de apertura
                    const noNeedsOpeningSelector = isTwoDoor || isSemicolumnaTwoDoor || hasDrawersOrGavetas;

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
                                    <span className="w-full bg-indigo-50/50 border border-indigo-100 rounded px-1 py-0.5 text-[7px] font-black uppercase italic text-indigo-900">{cleanCode(item.customReference ?? product.code)}</span>
                                    <span className="print-only text-[7px] font-black uppercase italic text-indigo-900">{cleanCode(item.customReference ?? product.code)}</span>
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
                                <div className="w-14 shrink-0 text-center">
                                    <input type="number" value={formatMeasure(item.customWidth) || ''} onChange={e => updateItem(item.id, 'customWidth', parseMeasureInput(e.target.value))} className={`w-12 bg-indigo-50/50 rounded p-0.5 text-[9px] font-black text-center outline-none border ${Number(item.customWidth) !== Number(product.width) ? 'border-orange-500 text-orange-600 bg-orange-50' : 'border-indigo-100'} no-print`} />
                                    <span className="print-only font-bold text-[9px]">{formatMeasure(item.customWidth)}</span>
                                </div>
                                <div className="w-14 shrink-0 text-center">
                                    <input type="number" value={formatMeasure(item.customHeight) || ''} onChange={e => updateItem(item.id, 'customHeight', parseMeasureInput(e.target.value))} className={`w-12 bg-indigo-50/50 rounded p-0.5 text-[9px] font-black text-center outline-none border ${Number(item.customHeight) !== Number(product.height) ? 'border-orange-500 text-orange-600 bg-orange-50' : 'border-indigo-100'} no-print`} />
                                    <span className="print-only font-bold text-[9px]">{formatMeasure(item.customHeight)}</span>
                                </div>
                                <div className="w-14 shrink-0 text-center">
                                    <input type="number" value={formatMeasure(item.customDepth) || ''} onChange={e => updateItem(item.id, 'customDepth', parseMeasureInput(e.target.value))} className={`w-12 bg-indigo-50/50 rounded p-0.5 text-[9px] font-black text-center outline-none border ${Number(item.customDepth) !== Number(product.depth) ? 'border-orange-500 text-orange-600 bg-orange-50' : 'border-indigo-100'} no-print`} />
                                    <span className="print-only font-bold text-[9px]">{formatMeasure(item.customDepth)}</span>
                                </div>
                                <div className="w-8 shrink-0 text-center">
                                    {noNeedsOpeningSelector ? (
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

                         {/* Precio - Solo visible si es valorado */}
                         {isValorado && (
                         <div className="w-20 shrink-0 text-right flex items-center justify-end gap-1 relative group/price">
                            {hasExtras && state.currentUser?.isAdmin && <Info size={7} className="text-orange-600 no-print" />}
                            <span className="text-[10px] font-black italic tracking-tight">{price.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}€</span>
                            
                            {/* Desglose solo visible para admin */}
                            {state.currentUser?.isAdmin && (
                              <div className="absolute right-0 top-full mt-2 z-50 hidden group-hover/price:block w-64 bg-slate-900 text-white p-4 rounded-xl shadow-2xl text-[9px] font-mono whitespace-pre-wrap text-left border border-indigo-500/30">
                                <div className="absolute -top-1 right-4 w-2 h-2 bg-slate-900 rotate-45 border-t border-l border-indigo-500/30"></div>
                                {breakdown}
                              </div>
                            )}
                         </div>
                         )}
                         
                         {/* Botón eliminar */}
                         <div className="w-6 shrink-0 no-print">
                            <button onClick={() => removeItem(item.id)} className="p-1 text-indigo-200 hover:text-red-500 transition-all"><Trash2 size={12}/></button>
                         </div>
                      </div>
                    );
                  })}
                  </div>
               </div>

               {/* Sección de items DESPIECE */}
               {(state.budgetItemsDespiece?.length > 0 || state.currentModule === 'despiece') && (
                 <div className="mt-4 mb-4">
                   <div className="flex items-center justify-between px-2 py-2 bg-purple-900 text-white rounded-t-lg">
                     <span className="text-[8px] font-black uppercase tracking-widest">
                       <Package size={12} className="inline mr-1" />
                       DESPIECE - TABLEROS ({state.budgetItemsDespiece?.length || 0})
                     </span>
                     <span className="text-[10px] font-black text-orange-400">
                       {(state.budgetItemsDespiece || []).reduce((sum, item) => sum + (item.totalPrice || 0), 0).toFixed(2)}€
                     </span>
                   </div>
                   <div className="border-x border-b border-purple-200 rounded-b-lg overflow-hidden max-h-[200px] overflow-y-auto">
                     {(state.budgetItemsDespiece || []).length === 0 ? (
                       <div className="p-4 text-center text-xs text-purple-400">
                         No hay tableros en el presupuesto
                       </div>
                     ) : (
                       (state.budgetItemsDespiece || []).map(item => (
                         <div key={item.id} className="flex items-center justify-between px-2 py-1.5 bg-purple-50/50 hover:bg-purple-100 border-b border-purple-100 last:border-b-0 text-[9px]">
                           <div className="flex-1">
                             <span className="font-black text-purple-800">{item.code}</span>
                             <span className="text-purple-500 ml-2">{formatMeasure(item.width)}×{formatMeasure(item.height)}{measureUnit}</span>
                             <span className="text-purple-400 ml-1">×{item.quantity}</span>
                           </div>
                           <div className="flex items-center gap-2">
                             <span className="font-bold text-orange-600">{item.totalPrice?.toFixed(2)}€</span>
                             <button
                               onClick={() => handleRemoveDespieceItem(item.id)}
                               className="p-0.5 text-purple-300 hover:text-red-500 transition-colors no-print"
                             >
                               <Trash2 size={10} />
                             </button>
                           </div>
                         </div>
                       ))
                     )}
                   </div>
                 </div>
               )}

               {/* Sección de totales - Solo si es valorado */}
               {isValorado && (
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
               )}
            </div>
          )}
        </div>

        {/* Catálogo - POSICIÓN HORIZONTAL (abajo) */}
        {catalogPosition === 'horizontal' && (
          <div style={{ height: isCatalogOpen ? catalogHeight : 50 }} className="absolute bottom-0 left-0 right-0 bg-white border-t border-indigo-100 no-print transition-all duration-300 z-50 overflow-hidden shadow-2xl">
             {isCatalogOpen && <div onMouseDown={() => { isResizingCatalog.current = true; }} className="h-1.5 cursor-ns-resize hover:bg-orange-600/30"></div>}
             <div className={`h-[50px] px-4 bg-indigo-50/30 border-b border-indigo-50 flex justify-between items-center`}>
                <div className="flex items-center gap-3">
                  {/* Botón ocultar/mostrar - Icono de panel */}
                  <button 
                    onClick={() => setIsCatalogOpen(!isCatalogOpen)}
                    className="p-2.5 bg-indigo-900 hover:bg-indigo-700 rounded-xl transition-colors shadow-lg border-2 border-indigo-600"
                    title={isCatalogOpen ? "Ocultar librería" : "Mostrar librería"}
                  >
                    {isCatalogOpen ? <PanelBottomClose size={18} className="text-white"/> : <PanelBottomOpen size={18} className="text-white"/>}
                  </button>
                  <LayoutPanelTop size={16} className="text-orange-600"/>
                  <h3 className="text-[10px] font-black uppercase tracking-wider text-indigo-900">
                    LIBRERÍA <span className="text-orange-600">({filteredCatalog.length})</span>
                  </h3>
                </div>
                <div className="flex items-center gap-2">
                   {/* Filtros solo cuando está abierto - Usando componentes extraídos */}
                   {isCatalogOpen && state.currentModule === 'despiece' && (
                     <DespieceFiltersHorizontal
                       despieceFilters={despieceFilters}
                       setDespieceFilters={setDespieceFilters}
                       despieceFilterOptions={despieceFilterOptions}
                       despieceProductsCount={despieceProducts.length}
                     />
                   )}
                   {isCatalogOpen && state.currentModule !== 'despiece' && (
                     <MontadaFiltersHorizontal
                       selectedPrograma={selectedPrograma}
                       setSelectedPrograma={setSelectedPrograma}
                       selectedCategory={selectedCategory}
                       setSelectedCategory={setSelectedCategory}
                       selectedSeries={selectedSeries}
                       setSelectedSeries={setSelectedSeries}
                       selectedApertura={selectedApertura}
                       setSelectedApertura={setSelectedApertura}
                       uniqueProgramas={uniqueProgramas}
                       uniqueCategories={uniqueCategories}
                       uniqueSeries={uniqueSeries}
                       uniqueAperturas={uniqueAperturas}
                       filterWidth={filterWidth}
                       setFilterWidth={setFilterWidth}
                       filterHeight={filterHeight}
                       setFilterHeight={setFilterHeight}
                       filterDepth={filterDepth}
                       setFilterDepth={setFilterDepth}
                       searchQuery={searchQuery}
                       setSearchQuery={setSearchQuery}
                     />
                   )}
                   {/* Botones cambiar posición */}
                   <button 
                     onClick={() => setCatalogPosition('top')} 
                     className="p-1.5 bg-indigo-100 hover:bg-indigo-200 rounded-lg transition-colors"
                     title="Mover arriba"
                   >
                     <PanelTopOpen size={14} className="text-indigo-600"/>
                   </button>
                   <button 
                     onClick={() => setCatalogPosition('vertical')} 
                     className="p-1.5 bg-indigo-100 hover:bg-indigo-200 rounded-lg transition-colors"
                     title="Mover a la derecha"
                   >
                     <PanelRightOpen size={14} className="text-indigo-600"/>
                   </button>
                </div>
             </div>
             
             <div className="h-[calc(100%-45px)] overflow-hidden">
                {/* Contenido según modo */}
                {state.currentModule === 'despiece' ? (
                  /* FLUJO PASO A PASO (Modo Despiece) */
                  <DespieceStepByStep
                    onAddItems={(items) => {
                      setState(prev => ({
                        ...prev,
                        budgetItemsDespiece: [...(prev.budgetItemsDespiece || []), ...items]
                      }));
                    }}
                    despieceFilters={despieceFilters}
                    setDespieceFilters={setDespieceFilters}
                  />
                ) : (
                  /* TABLA DE MUEBLES (Modo Montada) */
                  <table className="w-full text-left">
                  <thead className="bg-indigo-950 text-white text-[10px] font-black uppercase sticky top-0 z-20">
                    <tr>
                      <th className="p-2 pl-3 w-[45px]"></th>
                      <th className="p-2 w-[90px] cursor-pointer hover:bg-indigo-800 select-none" onClick={() => handleSort('code')}>
                        <div className="flex items-center gap-1">
                          REF {sortColumn === 'code' && (sortDirection === 'asc' ? '↑' : '↓')}
                        </div>
                      </th>
                      <th className="p-2 min-w-[180px] cursor-pointer hover:bg-indigo-800 select-none" onClick={() => handleSort('name')}>
                        <div className="flex items-center gap-1">
                          DESCRIPCIÓN {sortColumn === 'name' && (sortDirection === 'asc' ? '↑' : '↓')}
                        </div>
                      </th>
                      <th className="p-1 text-center w-[65px]">
                        <div className="flex flex-col items-center gap-0.5">
                          <span className="cursor-pointer hover:text-orange-300" onClick={() => handleSort('width')}>
                            AN ({measureUnit}) {sortColumn === 'width' && (sortDirection === 'asc' ? '↑' : '↓')}
                          </span>
                          <input 
                            type="number" 
                            value={filterWidth} 
                            onChange={e => setFilterWidth(e.target.value)}
                            placeholder={measureUnit}
                            className="w-14 bg-blue-600 border-2 border-blue-400 rounded-lg px-1 py-1 text-[10px] font-bold text-center text-white outline-none placeholder-blue-200 focus:bg-blue-500 focus:border-white transition-all"
                            onClick={e => e.stopPropagation()}
                          />
                        </div>
                      </th>
                      <th className="p-1 text-center w-[65px]">
                        <div className="flex flex-col items-center gap-0.5">
                          <span className="cursor-pointer hover:text-orange-300" onClick={() => handleSort('height')}>
                            AL ({measureUnit}) {sortColumn === 'height' && (sortDirection === 'asc' ? '↑' : '↓')}
                          </span>
                          <input 
                            type="number" 
                            value={filterHeight} 
                            onChange={e => setFilterHeight(e.target.value)}
                            placeholder={measureUnit}
                            className="w-14 bg-blue-600 border-2 border-blue-400 rounded-lg px-1 py-1 text-[10px] font-bold text-center text-white outline-none placeholder-blue-200 focus:bg-blue-500 focus:border-white transition-all"
                            onClick={e => e.stopPropagation()}
                          />
                        </div>
                      </th>
                      <th className="p-1 text-center w-[65px]">
                        <div className="flex flex-col items-center gap-0.5">
                          <span className="cursor-pointer hover:text-orange-300" onClick={() => handleSort('depth')}>
                            FO ({measureUnit}) {sortColumn === 'depth' && (sortDirection === 'asc' ? '↑' : '↓')}
                          </span>
                          <input 
                            type="number" 
                            value={filterDepth} 
                            onChange={e => setFilterDepth(e.target.value)}
                            placeholder={measureUnit}
                            className="w-14 bg-blue-600 border-2 border-blue-400 rounded-lg px-1 py-1 text-[10px] font-bold text-center text-white outline-none placeholder-blue-200 focus:bg-blue-500 focus:border-white transition-all"
                            onClick={e => e.stopPropagation()}
                          />
                        </div>
                      </th>
                      <th className="p-2 text-center w-[60px] cursor-pointer hover:bg-indigo-800 select-none" onClick={() => handleSort('points')}>
                        PTS {sortColumn === 'points' && (sortDirection === 'asc' ? '↑' : '↓')}
                      </th>
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
                      const specialType = getSpecialType(code, p.name);
                      
                      // Detectar tipo de mueble especial para icono
                      let iconType = '1P';
                      // HK-TOP: códigos abatibles sin HL/HS/HF
                      if ((code.includes('APABL') || code.includes('AVABL') || code.includes('APVBL')) && 
                          !code.includes('HL') && !code.includes('HS') && !code.includes('HF')) {
                        iconType = 'HK-TOP';
                      }
                      else if (code.includes('HS')) iconType = 'HS';
                      else if (code.includes('HL')) iconType = 'HL';
                      else if (code.includes('HF')) iconType = 'HF';
                      // HORNO+MICRO primero (HM en código o ambos en nombre)
                      else if (code.includes('HM') || code.includes('CHM') || code.includes('PHM') || (p.name?.toUpperCase().includes('HORNO') && p.name?.toUpperCase().includes('MICRO'))) iconType = 'HORNO+MICRO';
                      // Solo MICRO
                      else if (code.includes('AM') || code.includes('BM') || p.name?.toUpperCase().includes('MICRO')) iconType = 'MICRO';
                      // Solo HORNO
                      else if (code.includes('CH') || code.includes('BH') || code.includes('PH') || code.includes('VH') || p.name?.toUpperCase().includes('HORNO')) iconType = 'HORNO';
                      else if (code.includes('BP') || p.name?.toUpperCase().includes('PLACA')) iconType = 'PLACA';
                      else if (code.includes('BF') || p.name?.toUpperCase().includes('FREGADERO')) iconType = 'FREG';
                      else if (code.includes('AT') || p.name?.toUpperCase().includes('TERMO')) iconType = 'TERMO';
                      else if (code.includes('AE') || p.name?.toUpperCase().includes('ESCURRE')) iconType = 'ESCURRE';
                      else if (code.includes('AC') || p.name?.toUpperCase().includes('CAMPANA')) iconType = 'CAMPANA';
                      else if (code.includes('PE') || p.name?.toUpperCase().includes('EXTRAIBLE') || p.name?.toUpperCase().includes('EXTRAÍBLE')) iconType = 'EXTRAIBLE';
                      else if (code.includes('BOT') || p.name?.toUpperCase().includes('BOTELLERO')) iconType = 'BOTELLERO';
                      else if (code.includes('ESC') || p.name?.toUpperCase().includes('ESCOBERO')) iconType = 'ESCOBERO';
                      else if (code.includes('FRI') || p.name?.toUpperCase().includes('FRIGO')) iconType = 'FRIGO';
                      else if (p.name?.toUpperCase().includes('CACEROLERO') || p.name?.toUpperCase().includes('CAJONES') || p.name?.toUpperCase().includes('CAJÓN')) iconType = 'CAJONES';
                      else if (code.includes('ARA') || code.includes('BRA') || code.includes('ARC') || code.includes('BRC')) iconType = 'RINCON';
                      else if (code.includes('3C') || code.includes('4C') || code.includes('5C')) iconType = '3C';
                      // Nuevas categorías: Costados, Estantes, Regletas, etc.
                      else if (code.startsWith('COS_') || p.category === 'COSTADOS') iconType = 'COSTADO';
                      else if (code.startsWith('EST_') || p.category === 'ESTANTES') iconType = 'ESTANTE';
                      else if (code.startsWith('REG_') || p.category === 'REGLETAS') iconType = 'REGLETA';
                      else if (code.startsWith('PTA_') || p.category === 'PUERTAS') iconType = 'PUERTA';
                      else if (code.startsWith('VIT_') || p.category === 'VITRINAS') iconType = 'VITRINA';
                      else if (code.startsWith('COR_') || p.category === 'CORNISAS') iconType = 'CORNISA';
                      else if (code.startsWith('ZOC_') || p.category === 'ZOCALOS') iconType = 'ZOCALO';
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
                        'ESCURRE': 'bg-indigo-100 text-indigo-700',
                        'CAMPANA': 'bg-purple-100 text-purple-700',
                        'EXTRAÍBLE': 'bg-lime-100 text-lime-700',
                        'BOTELLERO': 'bg-rose-100 text-rose-700',
                        'ESCOBERO': 'bg-stone-100 text-stone-700',
                        'FRIGO': 'bg-cyan-100 text-cyan-700',
                        'CAJONES': 'bg-yellow-100 text-yellow-700'
                      };
                      
                      return (
                        <tr key={p.id} className="hover:bg-orange-50 group cursor-pointer transition-colors" onClick={() => addItemToBudget(p)}>
                          <td className="p-1 pl-2 w-[45px]">
                            <CabinetIcon type={iconType} isGola={isGola} className="w-8 h-8" />
                          </td>
                          <td className="p-2 font-bold text-indigo-900 text-[11px] w-[90px]">{cleanCode(p.code)}</td>
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
                              {/* Apertura para MV */}
                              {p.apertura && (
                                <span className={`px-1 py-0.5 rounded text-[7px] font-bold ${
                                  p.apertura === '1P D/I' ? 'bg-blue-100 text-blue-700' :
                                  p.apertura === '2P' ? 'bg-green-100 text-green-700' :
                                  'bg-gray-100 text-gray-600'
                                }`}>
                                  {p.apertura === '1P D/I' ? '1P↔' : p.apertura}
                                </span>
                              )}
                            </div>
                            {p.series && <div className="text-[8px] text-orange-500 font-medium mt-0.5">{p.series}</div>}
                          </td>
                          <td className="p-2 text-center font-bold text-slate-600 text-[10px] w-[55px]">{formatMeasure(p.width)}</td>
                          <td className="p-2 text-center font-bold text-slate-600 text-[10px] w-[55px]">{formatMeasure(p.height)}</td>
                          <td className="p-2 text-center font-bold text-slate-600 text-[10px] w-[55px]">{formatMeasure(p.depth)}</td>
                          <td className="p-2 text-center font-black text-orange-600 text-[11px] w-[60px]">
                                                        {getProductPrice(p)}
                          </td>
                          <td className="p-2 pr-3 text-right w-[40px]"><Plus size={14} className="text-orange-600 inline opacity-0 group-hover:opacity-100 transition-opacity"/></td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
                )}
             </div>
          </div>
        )}

        {/* Catálogo - POSICIÓN HORIZONTAL ARRIBA (top) */}
        {catalogPosition === 'top' && (
          <div style={{ height: isCatalogOpen ? catalogHeight : 50 }} className="absolute top-0 left-0 right-0 bg-white border-b border-indigo-100 no-print transition-all duration-300 z-50 overflow-hidden shadow-2xl">
             <div className={`h-[50px] px-4 bg-indigo-50/30 border-b border-indigo-50 flex justify-between items-center`}>
                <div className="flex items-center gap-3">
                  {/* Botón ocultar/mostrar - Icono de panel */}
                  <button 
                    onClick={() => setIsCatalogOpen(!isCatalogOpen)}
                    className="p-2.5 bg-indigo-900 hover:bg-indigo-700 rounded-xl transition-colors shadow-lg border-2 border-indigo-600"
                    title={isCatalogOpen ? "Ocultar librería" : "Mostrar librería"}
                  >
                    {isCatalogOpen ? <PanelTopClose size={18} className="text-white"/> : <PanelTopOpen size={18} className="text-white"/>}
                  </button>
                  <LayoutPanelTop size={16} className="text-orange-600"/>
                  <h3 className="text-[10px] font-black uppercase tracking-wider text-indigo-900">
                    LIBRERÍA <span className="text-orange-600">({filteredCatalog.length})</span>
                  </h3>
                </div>
                <div className="flex items-center gap-2">
                   {/* Filtros solo cuando está abierto - Usando componentes extraídos */}
                   {isCatalogOpen && state.currentModule === 'despiece' && (
                     <DespieceFiltersHorizontal
                       despieceFilters={despieceFilters}
                       setDespieceFilters={setDespieceFilters}
                       despieceFilterOptions={despieceFilterOptions}
                       despieceProductsCount={despieceProducts.length}
                     />
                   )}
                   {isCatalogOpen && state.currentModule !== 'despiece' && (
                     <MontadaFiltersHorizontal
                       selectedPrograma={selectedPrograma}
                       setSelectedPrograma={setSelectedPrograma}
                       selectedCategory={selectedCategory}
                       setSelectedCategory={setSelectedCategory}
                       selectedSeries={selectedSeries}
                       setSelectedSeries={setSelectedSeries}
                       selectedApertura={selectedApertura}
                       setSelectedApertura={setSelectedApertura}
                       uniqueProgramas={uniqueProgramas}
                       uniqueCategories={uniqueCategories}
                       uniqueSeries={uniqueSeries}
                       uniqueAperturas={uniqueAperturas}
                       filterWidth={filterWidth}
                       setFilterWidth={setFilterWidth}
                       filterHeight={filterHeight}
                       setFilterHeight={setFilterHeight}
                       filterDepth={filterDepth}
                       setFilterDepth={setFilterDepth}
                       searchQuery={searchQuery}
                       setSearchQuery={setSearchQuery}
                     />
                   )}
                   {/* Botones cambiar posición */}
                   <button 
                     onClick={() => setCatalogPosition('horizontal')} 
                     className="p-1.5 bg-indigo-100 hover:bg-indigo-200 rounded-lg transition-colors"
                     title="Mover abajo"
                   >
                     <PanelBottomOpen size={14} className="text-indigo-600"/>
                   </button>
                   <button 
                     onClick={() => setCatalogPosition('vertical')} 
                     className="p-1.5 bg-indigo-100 hover:bg-indigo-200 rounded-lg transition-colors"
                     title="Mover a la derecha"
                   >
                     <PanelRightOpen size={14} className="text-indigo-600"/>
                   </button>
                </div>
             </div>
             {isCatalogOpen && <div onMouseDown={() => { isResizingCatalog.current = true; }} className="absolute bottom-0 left-0 right-0 h-1.5 cursor-ns-resize hover:bg-orange-600/30 z-10"></div>}
             
             <div className="h-[calc(100%-50px)] overflow-y-auto">
                <table className="w-full text-left">
                  <thead className="bg-indigo-950 text-white text-[10px] font-black uppercase sticky top-0 z-20">
                    <tr>
                      <th className="p-2 pl-3 w-[45px]"></th>
                      <th className="p-2 w-[90px] cursor-pointer hover:bg-indigo-800 select-none" onClick={() => handleSort('code')}>
                        <div className="flex items-center gap-1">
                          REF {sortColumn === 'code' && (sortDirection === 'asc' ? '↑' : '↓')}
                        </div>
                      </th>
                      <th className="p-2 min-w-[180px] cursor-pointer hover:bg-indigo-800 select-none" onClick={() => handleSort('name')}>
                        <div className="flex items-center gap-1">
                          DESCRIPCIÓN {sortColumn === 'name' && (sortDirection === 'asc' ? '↑' : '↓')}
                        </div>
                      </th>
                      <th className="p-1 text-center w-[65px]">
                        <div className="flex flex-col items-center gap-0.5">
                          <span className="cursor-pointer hover:text-orange-300" onClick={() => handleSort('width')}>
                            AN ({measureUnit}) {sortColumn === 'width' && (sortDirection === 'asc' ? '↑' : '↓')}
                          </span>
                          <input 
                            type="number" 
                            value={filterWidth} 
                            onChange={e => setFilterWidth(e.target.value)}
                            placeholder={measureUnit}
                            className="w-14 bg-blue-600 border-2 border-blue-400 rounded-lg px-1 py-1 text-[10px] font-bold text-center text-white outline-none placeholder-blue-200 focus:bg-blue-500 focus:border-white transition-all"
                            onClick={e => e.stopPropagation()}
                          />
                        </div>
                      </th>
                      <th className="p-1 text-center w-[65px]">
                        <div className="flex flex-col items-center gap-0.5">
                          <span className="cursor-pointer hover:text-orange-300" onClick={() => handleSort('height')}>
                            AL ({measureUnit}) {sortColumn === 'height' && (sortDirection === 'asc' ? '↑' : '↓')}
                          </span>
                          <input 
                            type="number" 
                            value={filterHeight} 
                            onChange={e => setFilterHeight(e.target.value)}
                            placeholder={measureUnit}
                            className="w-14 bg-blue-600 border-2 border-blue-400 rounded-lg px-1 py-1 text-[10px] font-bold text-center text-white outline-none placeholder-blue-200 focus:bg-blue-500 focus:border-white transition-all"
                            onClick={e => e.stopPropagation()}
                          />
                        </div>
                      </th>
                      <th className="p-1 text-center w-[65px]">
                        <div className="flex flex-col items-center gap-0.5">
                          <span className="cursor-pointer hover:text-orange-300" onClick={() => handleSort('depth')}>
                            FO ({measureUnit}) {sortColumn === 'depth' && (sortDirection === 'asc' ? '↑' : '↓')}
                          </span>
                          <input 
                            type="number" 
                            value={filterDepth} 
                            onChange={e => setFilterDepth(e.target.value)}
                            placeholder={measureUnit}
                            className="w-14 bg-blue-600 border-2 border-blue-400 rounded-lg px-1 py-1 text-[10px] font-bold text-center text-white outline-none placeholder-blue-200 focus:bg-blue-500 focus:border-white transition-all"
                            onClick={e => e.stopPropagation()}
                          />
                        </div>
                      </th>
                      <th className="p-2 text-center w-[60px] cursor-pointer hover:bg-indigo-800 select-none" onClick={() => handleSort('points')}>
                        PTS {sortColumn === 'points' && (sortDirection === 'asc' ? '↑' : '↓')}
                      </th>
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
                      const specialType = getSpecialType(code, p.name);
                      
                      // Detectar tipo de mueble especial para icono
                      let iconType = '1P';
                      if ((code.includes('APABL') || code.includes('AVABL') || code.includes('APVBL')) && 
                          !code.includes('HL') && !code.includes('HS') && !code.includes('HF')) {
                        iconType = 'HK-TOP';
                      }
                      else if (code.includes('HS')) iconType = 'HS';
                      else if (code.includes('HL')) iconType = 'HL';
                      else if (code.includes('HF')) iconType = 'HF';
                      else if (code.includes('HM') || code.includes('CHM') || code.includes('PHM') || (p.name?.toUpperCase().includes('HORNO') && p.name?.toUpperCase().includes('MICRO'))) iconType = 'HORNO+MICRO';
                      else if (code.includes('AM') || code.includes('BM') || p.name?.toUpperCase().includes('MICRO')) iconType = 'MICRO';
                      else if (code.includes('CH') || code.includes('BH') || code.includes('PH') || code.includes('VH') || p.name?.toUpperCase().includes('HORNO')) iconType = 'HORNO';
                      else if (code.includes('BP') || p.name?.toUpperCase().includes('PLACA')) iconType = 'PLACA';
                      else if (code.includes('BF') || p.name?.toUpperCase().includes('FREGADERO')) iconType = 'FREG';
                      else if (code.includes('AT') || p.name?.toUpperCase().includes('TERMO')) iconType = 'TERMO';
                      else if (code.includes('AE') || p.name?.toUpperCase().includes('ESCURRE')) iconType = 'ESCURRE';
                      else if (code.includes('AC') || p.name?.toUpperCase().includes('CAMPANA')) iconType = 'CAMPANA';
                      else if (code.includes('PE') || p.name?.toUpperCase().includes('EXTRAIBLE') || p.name?.toUpperCase().includes('EXTRAÍBLE')) iconType = 'EXTRAIBLE';
                      else if (code.includes('BOT') || p.name?.toUpperCase().includes('BOTELLERO')) iconType = 'BOTELLERO';
                      else if (code.includes('ESC') || p.name?.toUpperCase().includes('ESCOBERO')) iconType = 'ESCOBERO';
                      else if (code.includes('FRI') || p.name?.toUpperCase().includes('FRIGO')) iconType = 'FRIGO';
                      else if (p.name?.toUpperCase().includes('CACEROLERO') || p.name?.toUpperCase().includes('CAJONES') || p.name?.toUpperCase().includes('CAJÓN')) iconType = 'CAJONES';
                      else if (code.includes('ARA') || code.includes('BRA') || code.includes('ARC') || code.includes('BRC')) iconType = 'RINCON';
                      else if (code.includes('3C') || code.includes('4C') || code.includes('5C')) iconType = '3C';
                      else if (code.startsWith('COS_') || p.category === 'COSTADOS') iconType = 'COSTADO';
                      else if (code.startsWith('EST_') || p.category === 'ESTANTES') iconType = 'ESTANTE';
                      else if (code.startsWith('REG_') || p.category === 'REGLETAS') iconType = 'REGLETA';
                      else if (code.startsWith('PTA_') || p.category === 'PUERTAS') iconType = 'PUERTA';
                      else if (code.startsWith('VIT_') || p.category === 'VITRINAS') iconType = 'VITRINA';
                      else if (code.startsWith('COR_') || p.category === 'CORNISAS') iconType = 'CORNISA';
                      else if (code.startsWith('ZOC_') || p.category === 'ZOCALOS') iconType = 'ZOCALO';
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
                        'ESCURRE': 'bg-indigo-100 text-indigo-700',
                        'CAMPANA': 'bg-purple-100 text-purple-700',
                        'EXTRAÍBLE': 'bg-lime-100 text-lime-700',
                        'BOTELLERO': 'bg-rose-100 text-rose-700',
                        'ESCOBERO': 'bg-stone-100 text-stone-700',
                        'FRIGO': 'bg-cyan-100 text-cyan-700',
                        'CAJONES': 'bg-yellow-100 text-yellow-700'
                      };
                      
                      return (
                        <tr key={p.id} className="hover:bg-orange-50 group cursor-pointer transition-colors" onClick={() => addItemToBudget(p)}>
                          <td className="p-1 pl-2 w-[45px]">
                            <CabinetIcon type={iconType} isGola={isGola} className="w-8 h-8" />
                          </td>
                          <td className="p-2 font-bold text-indigo-900 text-[11px] w-[90px]">{cleanCode(p.code)}</td>
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
                              {/* Apertura para MV */}
                              {p.apertura && (
                                <span className={`px-1 py-0.5 rounded text-[7px] font-bold ${
                                  p.apertura === '1P D/I' ? 'bg-blue-100 text-blue-700' :
                                  p.apertura === '2P' ? 'bg-green-100 text-green-700' :
                                  'bg-gray-100 text-gray-600'
                                }`}>
                                  {p.apertura === '1P D/I' ? '1P↔' : p.apertura}
                                </span>
                              )}
                            </div>
                            {p.series && <div className="text-[8px] text-orange-500 font-medium mt-0.5">{p.series}</div>}
                          </td>
                          <td className="p-2 text-center font-bold text-slate-600 text-[10px] w-[55px]">{formatMeasure(p.width)}</td>
                          <td className="p-2 text-center font-bold text-slate-600 text-[10px] w-[55px]">{formatMeasure(p.height)}</td>
                          <td className="p-2 text-center font-bold text-slate-600 text-[10px] w-[55px]">{formatMeasure(p.depth)}</td>
                          <td className="p-2 text-center font-black text-orange-600 text-[11px] w-[60px]">
                                                        {getProductPrice(p)}
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
            style={{ width: isCatalogOpen ? catalogWidth : 45 }} 
            className="absolute top-0 right-0 bottom-0 bg-white border-l border-indigo-100 no-print transition-all duration-300 z-50 shadow-2xl flex flex-col"
          >
            {/* Resizer horizontal - Solo cuando está abierto */}
            {isCatalogOpen && (
              <div 
                onMouseDown={() => { isResizingCatalogWidth.current = true; }} 
                className="absolute left-0 top-0 bottom-0 w-1.5 cursor-ew-resize hover:bg-orange-600/30 z-10"
              />
            )}
            
            {/* Header cuando está CERRADO */}
            {!isCatalogOpen && (
              <div className="h-full flex flex-col items-center pt-3 bg-indigo-50">
                <button 
                  onClick={() => setIsCatalogOpen(true)}
                  className="p-2 bg-indigo-900 hover:bg-indigo-700 rounded-lg transition-colors shadow-lg"
                  title="Mostrar librería"
                >
                  <PanelRightOpen size={16} className="text-white"/>
                </button>
              </div>
            )}
            
            {/* Header cuando está ABIERTO */}
            {isCatalogOpen && (
              <div className="h-[45px] px-3 bg-indigo-50/30 border-b border-indigo-50 flex items-center gap-2 shrink-0">
                <button 
                  onClick={() => setIsCatalogOpen(false)}
                  className="p-2 bg-indigo-900 hover:bg-indigo-700 rounded-lg transition-colors shadow-lg"
                  title="Ocultar librería"
                >
                  <PanelRightClose size={16} className="text-white"/>
                </button>
                <div className="flex-1">
                  <h3 className="text-[8px] font-black uppercase text-indigo-900">
                    LIBRERÍA <span className="text-orange-600">({filteredCatalog.length})</span>
                  </h3>
                </div>
                <button 
                  onClick={() => setCatalogPosition('top')} 
                  className="p-1.5 bg-indigo-100 hover:bg-indigo-200 rounded-lg transition-colors"
                  title="Mover arriba"
                >
                  <PanelTopOpen size={14} className="text-indigo-600"/>
                </button>
                <button 
                  onClick={() => setCatalogPosition('horizontal')} 
                  className="p-1.5 bg-indigo-100 hover:bg-indigo-200 rounded-lg transition-colors"
                  title="Mover abajo"
                >
                  <PanelBottomOpen size={14} className="text-indigo-600"/>
                </button>
              </div>
            )}

            {isCatalogOpen && (
              <>
                {state.currentModule === 'despiece' ? (
                  /* Modo Despiece: Flujo paso a paso */
                  <div className="flex-1 overflow-hidden">
                    <DespieceStepByStep
                      onAddItems={(items) => {
                        setState(prev => ({
                          ...prev,
                          budgetItemsDespiece: [...(prev.budgetItemsDespiece || []), ...items]
                        }));
                      }}
                      despieceFilters={despieceFilters}
                      setDespieceFilters={setDespieceFilters}
                    />
                  </div>
                ) : (
                  <>
                    {/* Filtros verticales - Modo Montada */}
                    <div className="p-3 space-y-2 border-b border-indigo-50 shrink-0">
                      <MontadaFiltersVertical
                        selectedPrograma={selectedPrograma}
                        setSelectedPrograma={setSelectedPrograma}
                        selectedCategory={selectedCategory}
                        setSelectedCategory={setSelectedCategory}
                        selectedSeries={selectedSeries}
                        setSelectedSeries={setSelectedSeries}
                        selectedApertura={selectedApertura}
                        setSelectedApertura={setSelectedApertura}
                        uniqueProgramas={uniqueProgramas}
                        uniqueCategories={uniqueCategories}
                        uniqueSeries={uniqueSeries}
                        uniqueAperturas={uniqueAperturas}
                        filterWidth={filterWidth}
                        setFilterWidth={setFilterWidth}
                        filterHeight={filterHeight}
                        setFilterHeight={setFilterHeight}
                        filterDepth={filterDepth}
                        setFilterDepth={setFilterDepth}
                        searchQuery={searchQuery}
                        setSearchQuery={setSearchQuery}
                      />
                    </div>

                {/* Lista de productos - más visible */}
                <div className="flex-1 overflow-y-auto" key={`catalog-${searchQuery}-${selectedPrograma}-${selectedCategory}-${selectedSeries}`}>
                  <div className="divide-y divide-indigo-100">
                    {filteredCatalog.map(p => {
                      const code = p.code?.toUpperCase() || '';
                      const isGola = code.startsWith('G') && /^G\d/.test(code);
                      
                      // Detectar tipo de herraje y tipo especial
                      const hardwareType = getHardwareType(code);
                      const specialType = getSpecialType(code, p.name);
                      
                      // Detectar tipo de mueble especial para icono
                      let iconType = '1P';
                      // HK-TOP: códigos abatibles sin HL/HS/HF
                      if ((code.includes('APABL') || code.includes('AVABL') || code.includes('APVBL')) && 
                          !code.includes('HL') && !code.includes('HS') && !code.includes('HF')) {
                        iconType = 'HK-TOP';
                      }
                      else if (code.includes('HS')) iconType = 'HS';
                      else if (code.includes('HL')) iconType = 'HL';
                      else if (code.includes('HF')) iconType = 'HF';
                      // HORNO+MICRO primero (HM en código o ambos en nombre)
                      else if (code.includes('HM') || code.includes('CHM') || code.includes('PHM') || (p.name?.toUpperCase().includes('HORNO') && p.name?.toUpperCase().includes('MICRO'))) iconType = 'HORNO+MICRO';
                      // Solo MICRO
                      else if (code.includes('AM') || code.includes('BM') || p.name?.toUpperCase().includes('MICRO')) iconType = 'MICRO';
                      // Solo HORNO
                      else if (code.includes('CH') || code.includes('BH') || code.includes('PH') || code.includes('VH') || p.name?.toUpperCase().includes('HORNO')) iconType = 'HORNO';
                      else if (code.includes('BP') || p.name?.toUpperCase().includes('PLACA')) iconType = 'PLACA';
                      else if (code.includes('BF') || p.name?.toUpperCase().includes('FREGADERO')) iconType = 'FREG';
                      else if (code.includes('AT') || p.name?.toUpperCase().includes('TERMO')) iconType = 'TERMO';
                      else if (code.includes('AE') || p.name?.toUpperCase().includes('ESCURRE')) iconType = 'ESCURRE';
                      else if (code.includes('AC') || p.name?.toUpperCase().includes('CAMPANA')) iconType = 'CAMPANA';
                      else if (code.includes('PE') || p.name?.toUpperCase().includes('EXTRAIBLE') || p.name?.toUpperCase().includes('EXTRAÍBLE')) iconType = 'EXTRAIBLE';
                      else if (code.includes('BOT') || p.name?.toUpperCase().includes('BOTELLERO')) iconType = 'BOTELLERO';
                      else if (code.includes('ESC') || p.name?.toUpperCase().includes('ESCOBERO')) iconType = 'ESCOBERO';
                      else if (code.includes('FRI') || p.name?.toUpperCase().includes('FRIGO')) iconType = 'FRIGO';
                      else if (p.name?.toUpperCase().includes('CACEROLERO') || p.name?.toUpperCase().includes('CAJONES') || p.name?.toUpperCase().includes('CAJÓN')) iconType = 'CAJONES';
                      else if (code.includes('ARA') || code.includes('BRA') || code.includes('ARC') || code.includes('BRC')) iconType = 'RINCON';
                      else if (code.includes('3C') || code.includes('4C') || code.includes('5C')) iconType = '3C';
                      // Nuevas categorías: Costados, Estantes, Regletas, etc.
                      else if (code.startsWith('COS_') || p.category === 'COSTADOS') iconType = 'COSTADO';
                      else if (code.startsWith('EST_') || p.category === 'ESTANTES') iconType = 'ESTANTE';
                      else if (code.startsWith('REG_') || p.category === 'REGLETAS') iconType = 'REGLETA';
                      else if (code.startsWith('PTA_') || p.category === 'PUERTAS') iconType = 'PUERTA';
                      else if (code.startsWith('VIT_') || p.category === 'VITRINAS') iconType = 'VITRINA';
                      else if (code.startsWith('COR_') || p.category === 'CORNISAS') iconType = 'CORNISA';
                      else if (code.startsWith('ZOC_') || p.category === 'ZOCALOS') iconType = 'ZOCALO';
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
                        'ESCURRE': 'bg-indigo-100 text-indigo-700',
                        'CAMPANA': 'bg-purple-100 text-purple-700',
                        'EXTRAÍBLE': 'bg-lime-100 text-lime-700',
                        'BOTELLERO': 'bg-rose-100 text-rose-700',
                        'ESCOBERO': 'bg-stone-100 text-stone-700',
                        'FRIGO': 'bg-cyan-100 text-cyan-700',
                        'CAJONES': 'bg-yellow-100 text-yellow-700'
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
                                <span className="text-[13px] font-black text-indigo-900">{cleanCode(p.code)}</span>
                                <span className="text-[14px] font-black text-orange-600">                            {getProductPrice(p)} pts</span>
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
                                  AN: {formatMeasure(p.width)} | AL: {formatMeasure(p.height)} | FO: {formatMeasure(p.depth)}
                                </span>
                                {/* Mostrar info de apertura para MV */}
                                {p.apertura && (
                                  <span className={`text-[8px] font-black px-1.5 py-0.5 rounded ${
                                    p.apertura === '1P D/I' ? 'bg-blue-100 text-blue-700' :
                                    p.apertura === '2P' ? 'bg-green-100 text-green-700' :
                                    p.apertura === '2P FREGADERO' ? 'bg-cyan-100 text-cyan-700' :
                                    p.apertura === 'ELECTRO' ? 'bg-amber-100 text-amber-700' :
                                    'bg-gray-100 text-gray-600'
                                  }`}>
                                    {p.apertura === '1P D/I' ? '1P ↔ D/I' : p.apertura}
                                  </span>
                                )}
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
        carcassBackThickness={carcassBackThickness}
        customerName={state.customerName || ''}
        projectReference={state.internalReference || ''}
        expedientNumber={state.budgetNumber || ''}
        doorColorLow={state.doorColorLow || ''}
        doorColorHigh={state.doorColorHigh || ''}
        doorColorColumns={state.doorColorColumns || ''}
        sideColor={state.sideColor || ''}
        doorHasVeta={state.doorHasVeta === true}
        doorToleranceHeight={state.doorToleranceHeight ?? 2}
        doorToleranceWidth={state.doorToleranceWidth ?? 3}
      />

      {/* Modal para añadir tablero al presupuesto - Componente extraído */}
      <DespieceAddModal
        isOpen={despieceAddModal.isOpen}
        product={despieceAddModal.product}
        width={despieceAddModal.width}
        height={despieceAddModal.height}
        quantity={despieceAddModal.quantity}
        onClose={() => setDespieceAddModal(prev => ({...prev, isOpen: false, product: null}))}
        onWidthChange={(val) => setDespieceAddModal(prev => ({...prev, width: val}))}
        onHeightChange={(val) => setDespieceAddModal(prev => ({...prev, height: val}))}
        onQuantityChange={(val) => setDespieceAddModal(prev => ({...prev, quantity: val}))}
        onAdd={() => {
          addDespieceProductToBudget(
            despieceAddModal.product, 
            despieceAddModal.width, 
            despieceAddModal.height, 
            despieceAddModal.quantity
          );
          setDespieceAddModal(prev => ({...prev, isOpen: false, product: null}));
        }}
      />

      {/* Wizard de Despiece - Modal a pantalla completa */}
      <DespieceWizard
        isOpen={isDespieceWizardOpen}
        onClose={() => setIsDespieceWizardOpen(false)}
        onAddItems={(wizardItems) => {
          // Convertir items del wizard al formato del presupuesto despiece
          const newItems = wizardItems.map(item => ({
            id: item.id,
            productId: item.productId,
            code: item.code,
            name: item.name,
            isDespiece: true,
            width: item.width,
            height: item.height,
            thickness: item.thickness,
            quantity: item.quantity,
            unitPriceM2: item.unitPrice,
            totalPrice: item.totalPrice,
            manufacturer: item.manufacturer,
            collection: item.collection,
            color: item.color,
            finish: item.finish,
            category: item.category
          }));
          // Añadir al presupuesto despiece
          setState(prev => ({
            ...prev,
            budgetItemsDespiece: [...(prev.budgetItemsDespiece || []), ...newItems]
          }));
        }}
        currentUser={state.currentUser}
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

      {/* Modal de confirmación al salir con líneas sin guardar */}
      {showExitConfirm && (
        <div className="fixed inset-0 bg-black/70 z-[100] flex items-center justify-center p-4 no-print">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6 border-t-4 border-amber-500">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 rounded-full bg-amber-100 flex items-center justify-center">
                <AlertCircle size={24} className="text-amber-600" />
              </div>
              <div>
                <h3 className="text-lg font-black text-indigo-900">LÍNEAS SIN GUARDAR</h3>
                <p className="text-sm text-slate-500">Tienes {(state.budgetItemsMontada?.length || 0) + (state.budgetItemsDespiece?.length || 0)} líneas pendientes</p>
              </div>
            </div>
            
            <p className="text-sm text-slate-600 mb-6">
              ¿Qué deseas hacer con las líneas del presupuesto actual antes de salir?
            </p>
            
            <div className="flex flex-col gap-2">
              <button
                onClick={async () => {
                  // Guardar y salir
                  await handleSaveBudget();
                  setShowExitConfirm(false);
                  setState(prev => ({ 
                    ...prev, 
                    budgetItemsMontada: [], 
                    budgetItemsDespiece: [],
                    budgetNumber: '',
                    customerName: '',
                    customerAddress: '',
                    internalReference: '',
                    existingProjectId: null
                  }));
                }}
                className="w-full bg-green-600 text-white py-3 rounded-xl font-bold uppercase text-sm flex items-center justify-center gap-2 hover:bg-green-700 transition-all"
              >
                <Save size={18} /> GUARDAR Y SALIR
              </button>
              
              <button
                onClick={() => {
                  // Borrar y salir
                  setShowExitConfirm(false);
                  setState(prev => ({ 
                    ...prev, 
                    budgetItemsMontada: [], 
                    budgetItemsDespiece: [],
                    budgetNumber: '',
                    customerName: '',
                    customerAddress: '',
                    internalReference: '',
                    existingProjectId: null
                  }));
                }}
                className="w-full bg-red-600 text-white py-3 rounded-xl font-bold uppercase text-sm flex items-center justify-center gap-2 hover:bg-red-700 transition-all"
              >
                <Trash2 size={18} /> DESCARTAR Y SALIR
              </button>
              
              <button
                onClick={() => setShowExitConfirm(false)}
                className="w-full bg-slate-200 text-slate-700 py-3 rounded-xl font-bold uppercase text-sm flex items-center justify-center gap-2 hover:bg-slate-300 transition-all"
              >
                <X size={18} /> CANCELAR
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default BudgetTable;
