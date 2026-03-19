import React, { useState, useMemo, useEffect } from 'react';
import { X, Users, Euro, Palette, Camera, Settings as SettingsIcon, Plus, Pencil, Trash2, Check, UserPlus, Shield, Store, Briefcase, Search, Package, Save, CheckSquare, Square, Loader, Zap, Upload, FileImage, XCircle, RefreshCw, CheckCircle, Building2, FileSpreadsheet, Download, HardDrive, Database, Clock, AlertTriangle, Wrench, Power, ShieldAlert, Timer, Maximize2, Minimize2, Target, Award, TrendingUp, BarChart3, FolderOpen, FileText, ChevronDown, ChevronUp, UserCheck, Layers, Factory } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, PieChart as RechartsPie, Pie, Cell, Legend } from 'recharts';
import { usersAPI, productsAPI, materialsAPI, settingsAPI, clientsAPI, librariesAPI } from '../services/api';
import CatalogImporter from './CatalogImporter';

const SettingsModal = ({ isOpen, onClose, state, setState }) => {
  const [activeTab, setActiveTab] = useState('users');
  const [colorInput, setColorInput] = useState(state.brandColor || '#ea580c');
  const [userSearch, setUserSearch] = useState('');
  const [isEditingUser, setIsEditingUser] = useState(false);
  const [editingUserId, setEditingUserId] = useState(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isFullScreen, setIsFullScreen] = useState(false); // Estado para pantalla completa
  const [userRoleFilter, setUserRoleFilter] = useState('all'); // Filtro por rol de usuario
  
  // Inventory states
  const [inventoryModule, setInventoryModule] = useState('montada');
  const [inventoryLibraryFilter, setInventoryLibraryFilter] = useState(''); // Filtro por biblioteca (ZC/MV)
  const [productSearch, setProductSearch] = useState('');
  const [productSeriesFilter, setProductSeriesFilter] = useState(''); // Filtro por serie
  const [productProgramaFilter, setProductProgramaFilter] = useState(''); // Filtro por programa
  const [productTipoMuebleFilter, setProductTipoMuebleFilter] = useState(''); // Filtro por tipo de mueble
  const [productZeroPriceFilter, setProductZeroPriceFilter] = useState(false); // Filtro sin precio
  const [isEditingProduct, setIsEditingProduct] = useState(false);
  const [editingProductId, setEditingProductId] = useState(null);
  const [selectedProducts, setSelectedProducts] = useState([]);
  const [productForm, setProductForm] = useState({
    code: '',
    name: '',
    category: '',
    series: '',
    visualType: '',
    width: 0,
    height: 0,
    depth: 0,
    manufacturer: 'Luiggi Home Master',
    zonePoints: {
      Z1: 0, Z2: 0, Z3: 0, Z4: 0, Z5: 0, Z6: 0,
      Z7: 0, Z8: 0, Z9: 0, Z10: 0, Z11: 0, Z12: 0
    }
  });

  // Carcass material states
  const [isEditingMaterial, setIsEditingMaterial] = useState(false);
  const [editingMaterialId, setEditingMaterialId] = useState(null);
  const [materialLibraryFilter, setMaterialLibraryFilter] = useState('TODAS');
  const [materialForm, setMaterialForm] = useState({
    name: '',
    fixedIncrement: 0,
    thickness: 16,
    library: 'ZC'
  });
  const [userForm, setUserForm] = useState({
    username: '',
    password: '',
    clientName: '',
    isActive: true,
    isAdmin: false,  // Director Comercial
    isGerente: false,  // Gerente - mismo acceso que Director
    isDirectorComercial: false,  // Director Comercial (ve todo el CRM)
    isResponsableDelegacion: false,  // Responsable Delegación
    isRepresentative: false,
    isPrescriptor: false,
    isTienda: false,  // Tienda/Punto de Venta
    isMontador: false,  // Montador/Instalador
    linkedRepresentativeId: '',
    allowedModules: ['montada'],
    allowedLibraries: ['ZC'],  // Tarifas/Bibliotecas activas (ZC, MV, etc.)
    commercialDiscount: 0,
    discountMontada: 0,
    discountDespiece: 0,
    canSeeCost: false,
    canSeeRetail: true,
    canUseAIAnalysis: false,
    canManageArticles: false,
    canViewTechnicalDespiece: false,
    canAccessCRM: false,
    canUseDigitalizador: false,
    canAccessArmarios: false,
    canAccessFabrica: false,  // Acceso a Portal de Fábrica
    canAccessMontajes: false,  // Acceso a Agenda de Montajes
    canAuthorizePermissions: false,
    useCustomBranding: false,
    canChangeLogo: false,
    linkedClientId: '',
    factoryId: ''  // ID de la fábrica asignada
  });

  // Lista de fábricas disponibles
  const [factories, setFactories] = useState([]);

  // Telemetry states
  const [telemetryModule, setTelemetryModule] = useState('montada');
  const [telemetryFiles, setTelemetryFiles] = useState([]);
  const [isProcessingTelemetry, setIsProcessingTelemetry] = useState(false);
  const [telemetryLog, setTelemetryLog] = useState([]);
  const [telemetryProgress, setTelemetryProgress] = useState({ current: 0, total: 0 });
  const [existingCodes, setExistingCodes] = useState(new Set());
  const [telemetryResult, setTelemetryResult] = useState(null);

  // Client states
  const [clients, setClients] = useState([]);
  const [clientSearch, setClientSearch] = useState('');
  const [clientFilterType, setClientFilterType] = useState('todos'); // 'todos', 'potencial', 'activo'
  const [clientFilterSegment, setClientFilterSegment] = useState('');
  const [clientSegments, setClientSegments] = useState([]);
  const [isEditingClient, setIsEditingClient] = useState(false);
  const [editingClientId, setEditingClientId] = useState(null);
  const [isSavingClient, setIsSavingClient] = useState(false);
  const [isImportingClients, setIsImportingClients] = useState(false);
  const [importResult, setImportResult] = useState(null);
  const [showActivateModal, setShowActivateModal] = useState(null);
  const [activateCode, setActivateCode] = useState('');
  const [showLinkUserModal, setShowLinkUserModal] = useState(null);
  const [linkUserId, setLinkUserId] = useState('');
  const [clientForm, setClientForm] = useState({
    tipo: 'potencial',
    codigo: '',
    nombre: '',
    cif: '',
    segmento: '',
    direccion: '',
    localidad: '',
    provincia: '',
    codigoPostal: '',
    telefono: '',
    email: '',
    descuento: 0,
    activo: true,
    notas: ''
  });

  // Maintenance states
  const [maintenanceStatus, setMaintenanceStatus] = useState(null);
  const [maintenanceLoading, setMaintenanceLoading] = useState(false);
  const [maintenanceActivating, setMaintenanceActivating] = useState(false);
  const [maintenanceDeactivating, setMaintenanceDeactivating] = useState(false);
  const [maintenanceBackups, setMaintenanceBackups] = useState([]);
  
  // Export database state
  const [isExportingDB, setIsExportingDB] = useState(false);
  const [maintenanceMessage, setMaintenanceMessage] = useState('Sistema en actualización. Volvemos pronto.');
  const [maintenanceMinutes, setMaintenanceMinutes] = useState(30);
  const [maintenanceCreateBackup, setMaintenanceCreateBackup] = useState(true);

  // Director Panel states (formerly AdminWorkView)
  const [directorLoading, setDirectorLoading] = useState(true);
  const [directorData, setDirectorData] = useState(null);
  const [directorMetrics, setDirectorMetrics] = useState(null);
  const [directorTrends, setDirectorTrends] = useState(null);
  const [directorTab, setDirectorTab] = useState('metrics');
  const [directorSearchTerm, setDirectorSearchTerm] = useState('');
  const [directorFilterUser, setDirectorFilterUser] = useState('');
  const [directorExpandedSections, setDirectorExpandedSections] = useState({
    projects: true,
    opportunities: true,
    digitalizaciones: false
  });

  // Settings saving state
  const [isSavingSettings, setIsSavingSettings] = useState(false);

  // Function to save pricing settings
  const handleSavePricingSettings = async () => {
    setIsSavingSettings(true);
    try {
      await settingsAPI.update({
        pointValueMontada: state.pointValueMontada,
        pointValueDespiece: state.pointValueDespiece,
        specialIncrementWidth: state.specialIncrementWidth,
        specialIncrementHeight: state.specialIncrementHeight,
        specialIncrementDepth: state.specialIncrementDepth,
        librarySpecialIncrements: state.librarySpecialIncrements,
        vigaCutIncrement: state.vigaCutIncrement || 0,
        libraryVigaCutIncrements: state.libraryVigaCutIncrements || { ZC: 0, MV: 0 }
      });
      alert('✅ Configuración guardada correctamente');
    } catch (err) {
      console.error('Error saving settings:', err);
      alert('❌ Error al guardar la configuración');
    } finally {
      setIsSavingSettings(false);
    }
  };

  // Load clients and segments when tab is active
  useEffect(() => {
    if (isOpen && activeTab === 'clients') {
      loadClients();
      loadSegments();
    }
  }, [isOpen, activeTab]);

  // Load factories when needed (for user form)
  useEffect(() => {
    if (isOpen && (activeTab === 'network' || activeTab === 'clients' || activeTab === 'users')) {
      loadFactories();
    }
  }, [isOpen, activeTab]);

  const loadFactories = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/fabrica/factories`);
      if (response.ok) {
        const data = await response.json();
        setFactories(data.filter(f => f.isActive !== false));
      }
    } catch (err) {
      console.error('Error loading factories:', err);
    }
  };

  const loadSegments = async () => {
    try {
      const data = await clientsAPI.getSegments();
      setClientSegments(data.segments || []);
    } catch (err) {
      console.error('Error loading segments:', err);
    }
  };

  // Load clients when tab is active
  useEffect(() => {
    if (isOpen && activeTab === 'clients') {
      loadClients();
    }
  }, [isOpen, activeTab]);

  const loadClients = async () => {
    try {
      const data = await clientsAPI.getAll();
      setClients(data);
    } catch (err) {
      console.error('Error loading clients:', err);
    }
  };

  // Backup states
  const [backups, setBackups] = useState([]);
  const [loadingBackups, setLoadingBackups] = useState(false);
  const [creatingBackup, setCreatingBackup] = useState(false);

  // Load backups when tab is active
  useEffect(() => {
    if (isOpen && activeTab === 'backups') {
      loadBackups();
    }
  }, [isOpen, activeTab]);

  const loadBackups = async () => {
    setLoadingBackups(true);
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/backups`);
      const data = await response.json();
      setBackups(data);
    } catch (err) {
      console.error('Error loading backups:', err);
    } finally {
      setLoadingBackups(false);
    }
  };

  // Load Director Panel data when tab is active
  useEffect(() => {
    if (isOpen && activeTab === 'director') {
      loadDirectorData();
      loadDirectorMetrics();
      loadDirectorTrends();
    }
  }, [isOpen, activeTab]);

  const loadDirectorData = async () => {
    setDirectorLoading(true);
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/all-work`);
      const result = await response.json();
      setDirectorData(result);
    } catch (err) {
      console.error('Error loading director data:', err);
    } finally {
      setDirectorLoading(false);
    }
  };

  const loadDirectorMetrics = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/metrics`);
      const result = await response.json();
      setDirectorMetrics(result);
    } catch (err) {
      console.error('Error loading metrics:', err);
    }
  };

  const loadDirectorTrends = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/metrics/trends`);
      const result = await response.json();
      setDirectorTrends(result);
    } catch (err) {
      console.error('Error loading trends:', err);
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('es-ES', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value || 0);
  };

  const toggleDirectorSection = (section) => {
    setDirectorExpandedSections(prev => ({ ...prev, [section]: !prev[section] }));
  };

  // Load maintenance status when tab is active
  useEffect(() => {
    if (isOpen && activeTab === 'maintenance') {
      loadMaintenanceStatus();
      loadMaintenanceBackups();
    }
  }, [isOpen, activeTab]);

  const loadMaintenanceStatus = async () => {
    setMaintenanceLoading(true);
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/maintenance/status`);
      const data = await response.json();
      setMaintenanceStatus(data);
    } catch (err) {
      console.error('Error loading maintenance status:', err);
    } finally {
      setMaintenanceLoading(false);
    }
  };

  const loadMaintenanceBackups = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/maintenance/backups`);
      const data = await response.json();
      setMaintenanceBackups(data.backups || []);
    } catch (err) {
      console.error('Error loading maintenance backups:', err);
    }
  };

  const handleActivateMaintenance = async () => {
    if (!window.confirm('¿Activar modo mantenimiento? Los usuarios no podrán acceder al sistema.')) return;
    
    setMaintenanceActivating(true);
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/maintenance/activate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: maintenanceMessage,
          estimatedMinutes: maintenanceMinutes,
          adminUserId: state.currentUser?.id,
          createBackup: maintenanceCreateBackup
        })
      });
      const data = await response.json();
      if (data.success) {
        alert('✅ Modo mantenimiento activado' + (maintenanceCreateBackup ? '\n📦 Backup de seguridad creado' : ''));
        loadMaintenanceStatus();
        loadMaintenanceBackups();
      } else {
        alert('Error: ' + (data.detail || 'No se pudo activar'));
      }
    } catch (err) {
      alert('Error al activar modo mantenimiento');
    } finally {
      setMaintenanceActivating(false);
    }
  };

  const handleDeactivateMaintenance = async () => {
    if (!window.confirm('¿Desactivar modo mantenimiento? El sistema volverá a estar operativo.')) return;
    
    setMaintenanceDeactivating(true);
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/maintenance/deactivate?adminUserId=${state.currentUser?.id}`, {
        method: 'POST'
      });
      const data = await response.json();
      if (data.success) {
        alert('✅ Sistema operativo. Modo mantenimiento desactivado.');
        loadMaintenanceStatus();
      } else {
        alert('Error: ' + (data.detail || 'No se pudo desactivar'));
      }
    } catch (err) {
      alert('Error al desactivar modo mantenimiento');
    } finally {
      setMaintenanceDeactivating(false);
    }
  };

  const handleDownloadMaintenanceBackup = async (backupId) => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/maintenance/backups/${backupId}/download`);
      const data = await response.json();
      if (data.success) {
        const blob = new Blob([JSON.stringify(data.backup, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${backupId}.json`;
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch (err) {
      alert('Error al descargar backup');
    }
  };

  const createManualBackup = async () => {
    setCreatingBackup(true);
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/backups/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          type: 'manual',
          createdBy: state.currentUser?.username || 'admin'
        })
      });
      if (response.ok) {
        await loadBackups();
        alert('✅ Backup creado correctamente');
      } else {
        throw new Error('Error al crear backup');
      }
    } catch (err) {
      console.error('Error creating backup:', err);
      alert('Error al crear backup');
    } finally {
      setCreatingBackup(false);
    }
  };

  // Export database to Excel
  const handleExportDatabase = async () => {
    setIsExportingDB(true);
    try {
      const token = localStorage.getItem('authToken');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/export-database`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Error al exportar');
      }
      
      // Download the file
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `LUIGGI_Export_${new Date().toISOString().split('T')[0]}.xlsx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      alert('✅ Base de datos exportada correctamente');
    } catch (err) {
      console.error('Error exporting database:', err);
      alert('❌ Error al exportar: ' + err.message);
    } finally {
      setIsExportingDB(false);
    }
  };

  useEffect(() => {
    if (!isOpen || activeTab !== 'telemetry') return;
    const loadCodes = async () => {
      try {
        const products = await productsAPI.getAll(telemetryModule);
        setExistingCodes(new Set(products.map(p => p.code)));
      } catch (err) { console.error(err); }
    };
    loadCodes();
  }, [telemetryModule, isOpen, activeTab]);

  // Lista de usuarios que pueden tener tiendas asignadas (Director, Gerente, Responsable, Comercial)
  const representatives = useMemo(() => state.users.filter(u => u.isAdmin || u.isGerente || u.isDirectorComercial || u.isResponsableDelegacion || u.isRepresentative), [state.users]);

  // Filtrar usuarios según el rol del usuario actual
  const visibleUsers = useMemo(() => {
    if (state.currentUser?.isAdmin || state.currentUser?.isGerente || state.currentUser?.isDirectorComercial) {
      // Director Comercial / Gerente ve todos los usuarios
      return state.users;
    } else if (state.currentUser?.isResponsableDelegacion || state.currentUser?.canAuthorizePermissions) {
      // Responsable Delegación ve comerciales y tiendas de su delegación
      return state.users.filter(u => 
        u.id === state.currentUser.id || 
        u.linkedRepresentativeId === state.currentUser.id ||
        u.isRepresentative ||
        u.isTienda
      );
    } else if (state.currentUser?.isRepresentative) {
      // Comerciales solo ven sus tiendas asignadas + a sí mismos
      return state.users.filter(u => 
        u.id === state.currentUser.id || // El comercial se ve a sí mismo
        u.linkedRepresentativeId === state.currentUser.id // Tiendas asignadas al comercial
      );
    }
    // Tiendas no deberían poder acceder aquí, pero por seguridad retornamos vacío
    return [];
  }, [state.users, state.currentUser]);

  const filteredUsers = useMemo(() => {
    const query = userSearch.toLowerCase();
    return visibleUsers.filter(u => {
      // Filtro por búsqueda
      const matchesSearch = u.username.toLowerCase().includes(query) || 
        u.clientName.toLowerCase().includes(query);
      
      // Filtro por rol
      if (userRoleFilter === 'all') return matchesSearch;
      if (userRoleFilter === 'director' && u.isAdmin) return matchesSearch;
      if (userRoleFilter === 'gerente' && u.isGerente) return matchesSearch;
      if (userRoleFilter === 'responsable' && u.isResponsableDelegacion) return matchesSearch;
      if (userRoleFilter === 'comercial' && u.isRepresentative && !u.isAdmin && !u.isGerente && !u.isResponsableDelegacion) return matchesSearch;
      if (userRoleFilter === 'tienda' && u.isTienda) return matchesSearch;
      if (userRoleFilter === 'colaborador' && u.isPrescriptor) return matchesSearch;
      
      return false;
    });
  }, [visibleUsers, userSearch, userRoleFilter]);

  // Product management - Usar inventoryCatalogs para tener TODOS los productos
  const currentCatalog = useMemo(() => {
    // Para el inventario, usar el catálogo de inventario que tiene todos los productos
    const invCatalogs = state.inventoryCatalogs || [];
    const invCatalog = invCatalogs.find(c => c.module === inventoryModule);
    if (invCatalog) return invCatalog;
    // Fallback al catálogo normal si no hay inventoryCatalogs
    return state.catalogs.find(c => c.module === inventoryModule);
  }, [state.catalogs, state.inventoryCatalogs, inventoryModule]);

  // Obtener lista de programas únicos para el filtro
  const availableProgramas = useMemo(() => {
    if (!currentCatalog) return [];
    const programas = new Set(currentCatalog.products.map(p => p.programa || 'SIN PROGRAMA'));
    return Array.from(programas).sort();
  }, [currentCatalog]);

  // Obtener lista de tipos de mueble únicos para el filtro (dependiente del programa seleccionado)
  const availableTiposMueble = useMemo(() => {
    if (!currentCatalog) return [];
    let products = currentCatalog.products;
    if (productProgramaFilter) {
      products = products.filter(p => (p.programa || 'SIN PROGRAMA') === productProgramaFilter);
    }
    const tipos = new Set(products.map(p => p.tipo_mueble || 'SIN TIPO'));
    return Array.from(tipos).sort();
  }, [currentCatalog, productProgramaFilter]);

  // Obtener lista de series únicas para el filtro (dependiente del programa y tipo seleccionados)
  const availableSeries = useMemo(() => {
    if (!currentCatalog) return [];
    let products = currentCatalog.products;
    if (productProgramaFilter) {
      products = products.filter(p => (p.programa || 'SIN PROGRAMA') === productProgramaFilter);
    }
    if (productTipoMuebleFilter) {
      products = products.filter(p => (p.tipo_mueble || 'SIN TIPO') === productTipoMuebleFilter);
    }
    const series = new Set(products.map(p => p.series || 'SIN SERIE'));
    return Array.from(series).sort();
  }, [currentCatalog, productProgramaFilter, productTipoMuebleFilter]);

  const filteredProducts = useMemo(() => {
    if (!currentCatalog) return [];
    const query = productSearch.toLowerCase();
    let filtered = currentCatalog.products.filter(p =>
      p.code.toLowerCase().includes(query) ||
      p.name.toLowerCase().includes(query)
    );
    
    // Filtrar por biblioteca (ZC/MV)
    if (inventoryLibraryFilter) {
      filtered = filtered.filter(p => p.library === inventoryLibraryFilter);
    }
    
    // Filtrar por programa
    if (productProgramaFilter) {
      filtered = filtered.filter(p => (p.programa || 'SIN PROGRAMA') === productProgramaFilter);
    }
    
    // Filtrar por tipo de mueble
    if (productTipoMuebleFilter) {
      filtered = filtered.filter(p => (p.tipo_mueble || 'SIN TIPO') === productTipoMuebleFilter);
    }
    
    // Filtrar por serie
    if (productSeriesFilter) {
      filtered = filtered.filter(p => (p.series || 'SIN SERIE') === productSeriesFilter);
    }
    
    // Filtrar por productos sin precio
    if (productZeroPriceFilter) {
      filtered = filtered.filter(p => 
        (!p.zonePoints?.Z1 || p.zonePoints.Z1 === 0) && 
        (!p.points || p.points === 0)
      );
    }
    
    // Ordenar por código de referencia
    return filtered.sort((a, b) => (a.code || '').localeCompare(b.code || ''));
  }, [currentCatalog, productSearch, inventoryLibraryFilter, productProgramaFilter, productTipoMuebleFilter, productSeriesFilter, productZeroPriceFilter]);

  if (!isOpen) return null;

  const handleColorChange = () => {
    setState(prev => ({ ...prev, brandColor: colorInput }));
  };

  const handleLogoUpload = async (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = async (e) => {
        const logoData = e.target.result;
        setState(prev => ({ ...prev, logo: logoData }));
        
        // Save logo to server
        try {
          await settingsAPI.update({ logo: logoData });
        } catch (err) {
          console.error('Error saving logo to server:', err);
        }
      };
      reader.readAsDataURL(file);
    }
  };

  const handleCreateUser = () => {
    setIsEditingUser(true);
    setEditingUserId(null);
    
    // Si es comercial, automáticamente crear como tienda asignada a él
    const isCommercial = !(state.currentUser?.isAdmin || state.currentUser?.isGerente || state.currentUser?.isDirectorComercial) && state.currentUser?.isRepresentative;
    
    // Load clients if not already loaded
    if (clients.length === 0) {
      loadClients();
    }
    
    setUserForm({
      username: '',
      password: '',
      clientName: '',
      linkedClientId: '',
      isActive: true,
      isAdmin: false,
      isResponsableDelegacion: false,
      isRepresentative: false,
      isPrescriptor: false,
      isTienda: false,
      isMontador: false,
      linkedRepresentativeId: isCommercial ? state.currentUser.id : '',
      allowedModules: ['montada'],
      allowedLibraries: ['ZC'],  // Por defecto ZC
      allowedCatalogIds: state.catalogs.map(c => c.id),
      commercialDiscount: 0,
      canSeeCost: false,
      canSeeRetail: true,
      canUseAIAnalysis: false,
      canManageArticles: false,
      canViewTechnicalDespiece: false,
      canAccessCRM: false,
      canUseDigitalizador: false,
      canAccessArmarios: false,
      canAccessFabrica: false,
      canAccessMontajes: false,
      canAuthorizePermissions: false,
      useCustomBranding: false,
      canChangeLogo: false
    });
  };

  const handleEditUser = (user) => {
    // Director Comercial, Responsable Delegación o comercial pueden editar tiendas
    const canEdit = state.currentUser?.isAdmin || 
                    state.currentUser?.isResponsableDelegacion ||
                    (state.currentUser?.isRepresentative && (user.linkedRepresentativeId === state.currentUser.id || user.id === state.currentUser.id));
    
    if (!canEdit) {
      alert('No tienes permisos para editar este usuario');
      return;
    }
    
    // Load clients if not already loaded
    if (clients.length === 0) {
      loadClients();
    }
    
    setIsEditingUser(true);
    setEditingUserId(user.id);
    // Asegurar que allowedLibraries tenga valor por defecto
    setUserForm({ 
      ...user, 
      linkedClientId: user.linkedClientId || '',
      allowedLibraries: user.allowedLibraries || ['ZC']
    });
  };

  const handleSaveUser = async () => {
    if (!userForm.username || !userForm.clientName) {
      alert('Usuario y Nombre de Cliente son obligatorios');
      return;
    }

    if (!editingUserId && !userForm.password) {
      alert('La contraseña es obligatoria para nuevos usuarios');
      return;
    }

    setIsSaving(true);
    try {
      if (editingUserId) {
        // Edit existing user
        const updateData = { ...userForm };
        // Si no se proporcionó password, no lo enviamos
        if (!userForm.password) {
          delete updateData.password;
        }
        const updated = await usersAPI.update(editingUserId, updateData);
        setState(prev => ({
          ...prev,
          users: prev.users.map(u => u.id === editingUserId ? updated : u)
        }));
      } else {
        // Create new user
        const newUser = await usersAPI.create(userForm);
        setState(prev => ({
          ...prev,
          users: [...prev.users, newUser]
        }));
      }

      setIsEditingUser(false);
      setEditingUserId(null);
    } catch (err) {
      alert('Error al guardar usuario: ' + err.message);
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteUser = async (userId) => {
    if (userId === 'admin') {
      alert('No puedes eliminar el usuario administrador principal');
      return;
    }
    
    // Comerciales solo pueden eliminar tiendas asignadas a ellos
    if (!(state.currentUser?.isAdmin || state.currentUser?.isGerente || state.currentUser?.isDirectorComercial) && state.currentUser?.isRepresentative) {
      const userToDelete = state.users.find(u => u.id === userId);
      if (userToDelete && userToDelete.linkedRepresentativeId !== state.currentUser.id) {
        alert('No tienes permisos para eliminar este usuario');
        return;
      }
    }
    
    if (window.confirm('¿Estás seguro de eliminar este usuario?')) {
      try {
        await usersAPI.delete(userId);
        setState(prev => ({
          ...prev,
          users: prev.users.filter(u => u.id !== userId)
        }));
      } catch (err) {
        alert('Error al eliminar usuario: ' + err.message);
      }
    }
  };

  const handleToggleModule = (module) => {
    setUserForm(prev => {
      const modules = prev.allowedModules.includes(module)
        ? prev.allowedModules.filter(m => m !== module)
        : [...prev.allowedModules, module];
      return { ...prev, allowedModules: modules };
    });
  };

  const handleCreateProduct = () => {
    setIsEditingProduct(true);
    setEditingProductId(null);
    setProductForm({
      code: '',
      name: '',
      category: '',
      series: '',
      visualType: '',
      width: 0,
      height: 0,
      depth: 0,
      manufacturer: 'Luiggi Home Master',
      zonePoints: {
        Z1: 0, Z2: 0, Z3: 0, Z4: 0, Z5: 0, Z6: 0,
        Z7: 0, Z8: 0, Z9: 0, Z10: 0, Z11: 0, Z12: 0
      }
    });
  };

  const handleEditProduct = (product) => {
    setIsEditingProduct(true);
    setEditingProductId(product.id);
    setProductForm({
      code: product.code,
      name: product.name,
      category: product.category || '',
      series: product.series || '',
      visualType: product.visualType || '',
      width: product.width || 0,
      height: product.height || 0,
      depth: product.depth || 0,
      manufacturer: product.manufacturer || 'Luiggi Home Master',
      zonePoints: product.zonePoints || {
        Z1: 0, Z2: 0, Z3: 0, Z4: 0, Z5: 0, Z6: 0,
        Z7: 0, Z8: 0, Z9: 0, Z10: 0, Z11: 0, Z12: 0
      }
    });
  };

  const handleSaveProduct = async () => {
    if (!productForm.code || !productForm.name) {
      alert('Código y Nombre son obligatorios');
      return;
    }

    setIsSaving(true);
    try {
      const productData = {
        ...productForm,
        module: inventoryModule,
        points: productForm.zonePoints?.Z1 || 0
      };

      if (editingProductId) {
        // Edit existing via API
        const updated = await productsAPI.update(editingProductId, productData);
        
        // Update local state
        const catalogIndex = state.catalogs.findIndex(c => c.module === inventoryModule);
        if (catalogIndex !== -1) {
          const updatedCatalogs = [...state.catalogs];
          updatedCatalogs[catalogIndex] = {
            ...updatedCatalogs[catalogIndex],
            products: updatedCatalogs[catalogIndex].products.map(p =>
              p.id === editingProductId ? updated : p
            )
          };
          setState(prev => ({ ...prev, catalogs: updatedCatalogs }));
        }
      } else {
        // Create new via API
        const newProduct = await productsAPI.create(productData);
        
        // Update local state
        const catalogIndex = state.catalogs.findIndex(c => c.module === inventoryModule);
        if (catalogIndex !== -1) {
          const updatedCatalogs = [...state.catalogs];
          updatedCatalogs[catalogIndex] = {
            ...updatedCatalogs[catalogIndex],
            products: [...updatedCatalogs[catalogIndex].products, newProduct]
          };
          setState(prev => ({ ...prev, catalogs: updatedCatalogs }));
        }
      }

      setIsEditingProduct(false);
      setEditingProductId(null);
    } catch (err) {
      alert('Error al guardar producto: ' + err.message);
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteProduct = async (productId) => {
    if (window.confirm('¿Eliminar este artículo del inventario?')) {
      try {
        await productsAPI.delete(productId);
        
        const catalogIndex = state.catalogs.findIndex(c => c.module === inventoryModule);
        if (catalogIndex !== -1) {
          const updatedCatalogs = [...state.catalogs];
          updatedCatalogs[catalogIndex] = {
            ...updatedCatalogs[catalogIndex],
            products: updatedCatalogs[catalogIndex].products.filter(p => p.id !== productId)
          };
          setState(prev => ({ ...prev, catalogs: updatedCatalogs }));
        }
        setSelectedProducts(prev => prev.filter(id => id !== productId));
      } catch (err) {
        alert('Error al eliminar producto: ' + err.message);
      }
    }
  };

  // Mass delete products
  const handleToggleProductSelection = (productId) => {
    setSelectedProducts(prev => 
      prev.includes(productId) 
        ? prev.filter(id => id !== productId)
        : [...prev, productId]
    );
  };

  const handleSelectAllProducts = () => {
    if (selectedProducts.length === filteredProducts.length) {
      setSelectedProducts([]);
    } else {
      setSelectedProducts(filteredProducts.map(p => p.id));
    }
  };

  const handleDeleteSelectedProducts = async () => {
    if (selectedProducts.length === 0) return;
    
    if (window.confirm(`¿Eliminar ${selectedProducts.length} artículos seleccionados?`)) {
      try {
        await productsAPI.deleteBulk(selectedProducts);
        
        const catalogIndex = state.catalogs.findIndex(c => c.module === inventoryModule);
        if (catalogIndex !== -1) {
          const updatedCatalogs = [...state.catalogs];
          updatedCatalogs[catalogIndex] = {
            ...updatedCatalogs[catalogIndex],
            products: updatedCatalogs[catalogIndex].products.filter(p => !selectedProducts.includes(p.id))
          };
          setState(prev => ({ ...prev, catalogs: updatedCatalogs }));
        }
        setSelectedProducts([]);
      } catch (err) {
        alert('Error al eliminar productos: ' + err.message);
      }
    }
  };

  // Carcass material management
  const handleCreateMaterial = () => {
    setIsEditingMaterial(true);
    setEditingMaterialId(null);
    // Al crear, usar el filtro activo como tarifa por defecto
    const defaultLibrary = materialLibraryFilter !== 'TODAS' ? materialLibraryFilter : 'ZC';
    setMaterialForm({ name: '', fixedIncrement: 0, thickness: 16, library: defaultLibrary });
  };

  const handleEditMaterial = (material) => {
    setIsEditingMaterial(true);
    setEditingMaterialId(material.id);
    setMaterialForm({
      name: material.name,
      fixedIncrement: material.fixedIncrement || 0,
      thickness: material.thickness || 16,
      library: material.library || 'ZC'  // Mantener la tarifa actual (no editable)
    });
  };

  const handleSaveMaterial = async () => {
    if (!materialForm.name) {
      alert('El nombre del material es obligatorio');
      return;
    }

    setIsSaving(true);
    try {
      if (editingMaterialId) {
        // Edit existing via API
        const updated = await materialsAPI.update(editingMaterialId, materialForm);
        setState(prev => ({
          ...prev,
          carcassMaterials: prev.carcassMaterials.map(m =>
            m.id === editingMaterialId ? updated : m
          )
        }));
      } else {
        // Create new via API
        const newMaterial = await materialsAPI.create(materialForm);
        setState(prev => ({
          ...prev,
          carcassMaterials: [...prev.carcassMaterials, newMaterial]
        }));
      }

      setIsEditingMaterial(false);
      setEditingMaterialId(null);
    } catch (err) {
      alert('Error al guardar material: ' + err.message);
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteMaterial = async (materialId) => {
    if (state.carcassMaterials.length <= 1) {
      alert('Debe existir al menos un material de armazón');
      return;
    }
    
    if (window.confirm('¿Eliminar este material de armazón?')) {
      try {
        await materialsAPI.delete(materialId);
        setState(prev => ({
          ...prev,
          carcassMaterials: prev.carcassMaterials.filter(m => m.id !== materialId),
          selectedCarcassMaterialId: prev.selectedCarcassMaterialId === materialId 
            ? prev.carcassMaterials[0].id 
            : prev.selectedCarcassMaterialId
        }));
      } catch (err) {
        alert('Error al eliminar material: ' + err.message);
      }
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-6">
      <div className={`bg-white rounded-3xl shadow-2xl overflow-hidden flex flex-col transition-all duration-300 ${
        isFullScreen 
          ? 'w-full h-full max-w-none max-h-none rounded-none' 
          : 'w-full max-w-5xl max-h-[90vh]'
      }`}>
        {/* Header */}
        <div className="px-8 py-6 border-b border-slate-100 flex justify-between items-center bg-gradient-to-r from-indigo-950 to-indigo-900 shrink-0">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-white/10 rounded-xl">
              <SettingsIcon size={24} className="text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-black text-white uppercase tracking-tight">Panel Maestro</h2>
              <p className="text-xs font-bold text-indigo-300 uppercase tracking-wider">Configuración Industrial</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {/* Botón Pantalla Completa */}
            <button 
              onClick={() => setIsFullScreen(!isFullScreen)} 
              className="p-2 hover:bg-white/10 rounded-xl transition-all"
              title={isFullScreen ? 'Salir de pantalla completa' : 'Ver en pantalla completa'}
            >
              {isFullScreen ? (
                <Minimize2 size={20} className="text-white" />
              ) : (
                <Maximize2 size={20} className="text-white" />
              )}
            </button>
            <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-xl transition-all">
              <X size={24} className="text-white" />
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="px-8 py-4 bg-slate-50 border-b border-slate-200 flex gap-2 overflow-x-auto shrink-0">
          {/* Tab Panel Director - Solo Admin (antes era Panel Admin separado) */}
          {(state.currentUser?.isAdmin || state.currentUser?.isGerente || state.currentUser?.isDirectorComercial) && (
            <button
              onClick={() => setActiveTab('director')}
              className={`px-5 py-3 rounded-xl text-sm font-black uppercase tracking-wide transition-all whitespace-nowrap ${
                activeTab === 'director' ? 'bg-purple-600 text-white shadow-lg' : 'text-slate-500 hover:bg-white hover:text-slate-700'
              }`}
              data-testid="director-tab"
            >
              Panel Director
            </button>
          )}
          
          <button
            onClick={() => setActiveTab('users')}
            className={`px-5 py-3 rounded-xl text-sm font-black uppercase tracking-wide transition-all whitespace-nowrap ${
              activeTab === 'users' ? 'bg-indigo-600 text-white shadow-lg' : 'text-slate-500 hover:bg-white hover:text-slate-700'
            }`}
          >
            Red Distribución
          </button>
          
          {/* Tab Clientes - Solo Admin */}
          {(state.currentUser?.isAdmin || state.currentUser?.isGerente || state.currentUser?.isDirectorComercial) && (
            <button
              onClick={() => setActiveTab('clients')}
              className={`px-5 py-3 rounded-xl text-sm font-black uppercase tracking-wide transition-all whitespace-nowrap ${
                activeTab === 'clients' ? 'bg-emerald-600 text-white shadow-lg' : 'text-slate-500 hover:bg-white hover:text-slate-700'
              }`}
              data-testid="clients-tab"
            >
              Clientes
            </button>
          )}
          
          {/* Solo Admin y Comerciales con permiso canManageArticles pueden ver Inventario */}
          {(state.currentUser?.isAdmin || state.currentUser?.canManageArticles) && (
            <button
              onClick={() => setActiveTab('inventory')}
              className={`px-5 py-3 rounded-xl text-sm font-black uppercase tracking-wide transition-all whitespace-nowrap ${
                activeTab === 'inventory' ? 'bg-indigo-600 text-white shadow-lg' : 'text-slate-500 hover:bg-white hover:text-slate-700'
              }`}
            >
              Inventario
            </button>
          )}
          
          {/* Solo Admin y Comerciales con permiso canManageArticles pueden ver Márgenes */}
          {(state.currentUser?.isAdmin || state.currentUser?.canManageArticles) && (
            <button
              onClick={() => setActiveTab('pricing')}
              className={`px-5 py-3 rounded-xl text-sm font-black uppercase tracking-wide transition-all whitespace-nowrap ${
                activeTab === 'pricing' ? 'bg-indigo-600 text-white shadow-lg' : 'text-slate-500 hover:bg-white hover:text-slate-700'
              }`}
            >
              Márgenes
            </button>
          )}
          
          {/* Tab Armazones - Separada */}
          {(state.currentUser?.isAdmin || state.currentUser?.canManageArticles) && (
            <button
              onClick={() => setActiveTab('armazones')}
              className={`px-5 py-3 rounded-xl text-sm font-black uppercase tracking-wide transition-all whitespace-nowrap ${
                activeTab === 'armazones' ? 'bg-amber-600 text-white shadow-lg' : 'text-slate-500 hover:bg-white hover:text-slate-700'
              }`}
              data-testid="armazones-tab"
            >
              Armazones
            </button>
          )}
          
          {/* Tab Backups - Solo Admin */}
          {(state.currentUser?.isAdmin || state.currentUser?.isGerente || state.currentUser?.isDirectorComercial) && (
            <button
              onClick={() => setActiveTab('backups')}
              className={`px-5 py-3 rounded-xl text-sm font-black uppercase tracking-wide transition-all whitespace-nowrap ${
                activeTab === 'backups' ? 'bg-orange-600 text-white shadow-lg' : 'text-slate-500 hover:bg-white hover:text-slate-700'
              }`}
              data-testid="backups-tab"
            >
              Backups
            </button>
          )}
          
          {/* Pestaña Mantenimiento - Solo Admin */}
          {(state.currentUser?.isAdmin || state.currentUser?.isGerente || state.currentUser?.isDirectorComercial) && (
            <button
              onClick={() => setActiveTab('maintenance')}
              className={`px-5 py-3 rounded-xl text-sm font-black uppercase tracking-wide transition-all whitespace-nowrap ${
                activeTab === 'maintenance' ? 'bg-red-600 text-white shadow-lg' : 'text-slate-500 hover:bg-white hover:text-slate-700'
              }`}
              data-testid="maintenance-tab"
            >
              Mantenimiento
            </button>
          )}
          
          {(state.currentUser?.isAdmin || state.currentUser?.isGerente || state.currentUser?.isDirectorComercial) && (
            <button
              onClick={() => setActiveTab('telemetry')}
              className={`px-5 py-3 rounded-xl text-sm font-black uppercase tracking-wide transition-all whitespace-nowrap ${
                activeTab === 'telemetry' ? 'bg-orange-500 text-white shadow-lg' : 'text-slate-500 hover:bg-white hover:text-slate-700'
              }`}
            >
              Telemetría IA
            </button>
          )}
          
          <button
            onClick={() => setActiveTab('identity')}
            className={`px-5 py-3 rounded-xl text-sm font-black uppercase tracking-wide transition-all whitespace-nowrap ${
              activeTab === 'identity' ? 'bg-indigo-600 text-white shadow-lg' : 'text-slate-500 hover:bg-white hover:text-slate-700'
            }`}
          >
            Identidad
          </button>
          <button
            onClick={() => setActiveTab('security')}
            className={`px-5 py-3 rounded-xl text-sm font-black uppercase tracking-wide transition-all whitespace-nowrap ${
              activeTab === 'security' ? 'bg-emerald-600 text-white shadow-lg' : 'text-slate-500 hover:bg-white hover:text-slate-700'
            }`}
          >
            <span className="flex items-center gap-2">
              <Shield size={16} /> Seguridad 2FA
            </span>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-8">
          {/* PANEL DIRECTOR TAB */}
          {activeTab === 'director' && (
            <div className="space-y-6">
              {/* Sub-tabs for Director Panel */}
              <div className="flex gap-2 mb-4">
                <button 
                  onClick={() => setDirectorTab('metrics')}
                  className={`px-4 py-2 rounded-lg text-sm font-bold transition-all ${directorTab === 'metrics' ? 'bg-orange-500 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}
                >
                  <BarChart3 size={16} className="inline mr-2" />
                  Métricas
                </button>
                <button 
                  onClick={() => setDirectorTab('work')}
                  className={`px-4 py-2 rounded-lg text-sm font-bold transition-all ${directorTab === 'work' ? 'bg-orange-500 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}
                >
                  <FolderOpen size={16} className="inline mr-2" />
                  Trabajos
                </button>
                <button
                  onClick={() => {
                    loadDirectorData();
                    loadDirectorMetrics();
                    loadDirectorTrends();
                  }}
                  className="p-2 bg-slate-100 text-slate-600 rounded-lg hover:bg-slate-200 transition-colors ml-auto"
                  title="Actualizar datos"
                >
                  <RefreshCw size={18} />
                </button>
                
                {/* Botones de exportación */}
                <div className="flex gap-2">
                  <a
                    href="/catalogo_productos_completo.xlsx"
                    download="LUIGGI_Catalogo_Productos.xlsx"
                    className="flex items-center gap-1 px-3 py-2 bg-orange-500 text-white rounded-lg text-xs font-bold hover:bg-orange-600 transition-colors"
                    title="Exportar Catálogo Productos"
                    data-testid="export-productos-btn"
                  >
                    <Download size={14} />
                    Artículos
                  </a>
                  <button
                    onClick={async () => {
                      try {
                        const token = localStorage.getItem('token');
                        const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/export/presupuestos`, {
                          headers: { 'Authorization': `Bearer ${token}` }
                        });
                        if (response.ok) {
                          const blob = await response.blob();
                          const url = window.URL.createObjectURL(blob);
                          const a = document.createElement('a');
                          a.href = url;
                          a.download = `LUIGGI_Presupuestos_${new Date().toISOString().split('T')[0]}.xlsx`;
                          a.click();
                          window.URL.revokeObjectURL(url);
                        }
                      } catch (err) {
                        console.error('Error exportando:', err);
                      }
                    }}
                    className="flex items-center gap-1 px-3 py-2 bg-green-600 text-white rounded-lg text-xs font-bold hover:bg-green-700 transition-colors"
                    title="Exportar Presupuestos"
                    data-testid="export-presupuestos-btn"
                  >
                    <Download size={14} />
                    Presup.
                  </button>
                  <button
                    onClick={async () => {
                      try {
                        const token = localStorage.getItem('token');
                        const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/export/crm`, {
                          headers: { 'Authorization': `Bearer ${token}` }
                        });
                        if (response.ok) {
                          const blob = await response.blob();
                          const url = window.URL.createObjectURL(blob);
                          const a = document.createElement('a');
                          a.href = url;
                          a.download = `LUIGGI_CRM_${new Date().toISOString().split('T')[0]}.xlsx`;
                          a.click();
                          window.URL.revokeObjectURL(url);
                        }
                      } catch (err) {
                        console.error('Error exportando:', err);
                      }
                    }}
                    className="flex items-center gap-1 px-3 py-2 bg-blue-600 text-white rounded-lg text-xs font-bold hover:bg-blue-700 transition-colors"
                    title="Exportar CRM"
                    data-testid="export-crm-btn"
                  >
                    <Download size={14} />
                    CRM
                  </button>
                  <button
                    onClick={async () => {
                      try {
                        const token = localStorage.getItem('token');
                        const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/export/usuarios`, {
                          headers: { 'Authorization': `Bearer ${token}` }
                        });
                        if (response.ok) {
                          const blob = await response.blob();
                          const url = window.URL.createObjectURL(blob);
                          const a = document.createElement('a');
                          a.href = url;
                          a.download = `LUIGGI_Usuarios_${new Date().toISOString().split('T')[0]}.xlsx`;
                          a.click();
                          window.URL.revokeObjectURL(url);
                        }
                      } catch (err) {
                        console.error('Error exportando:', err);
                      }
                    }}
                    className="flex items-center gap-1 px-3 py-2 bg-purple-600 text-white rounded-lg text-xs font-bold hover:bg-purple-700 transition-colors"
                    title="Exportar Usuarios"
                    data-testid="export-usuarios-btn"
                  >
                    <Download size={14} />
                    Usuarios
                  </button>
                </div>
              </div>

              {/* METRICS TAB */}
              {directorTab === 'metrics' && directorMetrics && (
                <div className="space-y-6">
                  {/* Global Summary Cards */}
                  <div className="grid grid-cols-5 gap-4">
                    <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-xl p-4 text-white">
                      <div className="flex items-center gap-2 mb-2">
                        <Euro size={20} />
                        <span className="text-xs font-bold uppercase opacity-80">Ventas Cerradas</span>
                      </div>
                      <p className="text-3xl font-black">{formatCurrency(directorMetrics.global?.totalValue)}</p>
                      <p className="text-xs opacity-80 mt-1">{directorMetrics.global?.wonOpportunities || 0} oportunidades ganadas</p>
                    </div>
                    <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-4 text-white">
                      <div className="flex items-center gap-2 mb-2">
                        <Target size={20} />
                        <span className="text-xs font-bold uppercase opacity-80">Pipeline</span>
                      </div>
                      <p className="text-3xl font-black">{formatCurrency(directorMetrics.global?.pipelineValue)}</p>
                      <p className="text-xs opacity-80 mt-1">{directorMetrics.global?.activeOpportunities || 0} oportunidades activas</p>
                    </div>
                    <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl p-4 text-white">
                      <div className="flex items-center gap-2 mb-2">
                        <TrendingUp size={20} />
                        <span className="text-xs font-bold uppercase opacity-80">Conversión</span>
                      </div>
                      <p className="text-3xl font-black">{directorMetrics.global?.conversionRate || 0}%</p>
                      <p className="text-xs opacity-80 mt-1">de {directorMetrics.global?.totalOpportunities || 0} totales</p>
                    </div>
                    <div className="bg-gradient-to-br from-indigo-500 to-indigo-600 rounded-xl p-4 text-white">
                      <div className="flex items-center gap-2 mb-2">
                        <Users size={20} />
                        <span className="text-xs font-bold uppercase opacity-80">Contactos</span>
                      </div>
                      <p className="text-3xl font-black">{directorMetrics.global?.totalContacts || 0}</p>
                      <p className="text-xs opacity-80 mt-1">{directorMetrics.global?.totalProjects || 0} proyectos</p>
                    </div>
                    <div className="bg-gradient-to-br from-slate-600 to-slate-700 rounded-xl p-4 text-white">
                      <div className="flex items-center gap-2 mb-2">
                        <Store size={20} />
                        <span className="text-xs font-bold uppercase opacity-80">Red Distribución</span>
                      </div>
                      <p className="text-3xl font-black">{directorMetrics.global?.totalTiendas || 0}</p>
                      <p className="text-xs opacity-80 mt-1">
                        {directorMetrics.global?.totalComerciales || 0} comerciales, {directorMetrics.global?.totalResponsables || 0} responsables
                      </p>
                    </div>
                  </div>

                  {/* Top Performers */}
                  {directorMetrics.topPerformers && directorMetrics.topPerformers.length > 0 && (
                    <div>
                      <h3 className="text-lg font-black text-slate-900 mb-4 flex items-center gap-2">
                        <Award className="text-orange-500" size={20} />
                        Top Performers
                      </h3>
                      <div className="grid grid-cols-3 gap-4">
                        {directorMetrics.topPerformers.slice(0, 6).map((user, index) => (
                          <div key={user.userId} className={`bg-white rounded-xl p-4 border-2 ${index === 0 ? 'border-yellow-400' : index === 1 ? 'border-slate-300' : index === 2 ? 'border-orange-400' : 'border-slate-100'}`}>
                            <div className="flex items-center gap-3 mb-3">
                              <div className={`w-8 h-8 rounded-full flex items-center justify-center font-black text-white ${index === 0 ? 'bg-yellow-500' : index === 1 ? 'bg-slate-400' : index === 2 ? 'bg-orange-500' : 'bg-indigo-500'}`}>
                                {index + 1}
                              </div>
                              <div>
                                <p className="font-black text-slate-900">{user.userName}</p>
                                <p className="text-xs text-slate-500">{user.role}</p>
                              </div>
                            </div>
                            <div className="grid grid-cols-2 gap-2 text-xs">
                              <div className="bg-green-50 rounded-lg p-2">
                                <p className="text-green-600 font-bold">Ventas</p>
                                <p className="font-black text-green-800">{formatCurrency(user.totalValue)}</p>
                              </div>
                              <div className="bg-blue-50 rounded-lg p-2">
                                <p className="text-blue-600 font-bold">Pipeline</p>
                                <p className="font-black text-blue-800">{formatCurrency(user.pipelineValue)}</p>
                              </div>
                              <div className="bg-purple-50 rounded-lg p-2">
                                <p className="text-purple-600 font-bold">Conversión</p>
                                <p className="font-black text-purple-800">{user.conversionRate}%</p>
                              </div>
                              <div className="bg-slate-50 rounded-lg p-2">
                                <p className="text-slate-600 font-bold">Tiendas</p>
                                <p className="font-black text-slate-800">{user.totalShops}</p>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Detailed Table */}
                  {directorMetrics.byUser && directorMetrics.byUser.length > 0 && (
                    <div>
                      <h3 className="text-lg font-black text-slate-900 mb-4 flex items-center gap-2">
                        <UserCheck className="text-indigo-500" size={20} />
                        Detalle por Comercial / Responsable
                      </h3>
                      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
                        <table className="w-full text-sm">
                          <thead className="bg-slate-50">
                            <tr>
                              <th className="text-left p-3 font-black text-slate-600">Usuario</th>
                              <th className="text-left p-3 font-black text-slate-600">Rol</th>
                              <th className="text-right p-3 font-black text-slate-600">Ventas</th>
                              <th className="text-right p-3 font-black text-slate-600">Pipeline</th>
                              <th className="text-center p-3 font-black text-slate-600">Conv.</th>
                              <th className="text-center p-3 font-black text-slate-600">Opps</th>
                              <th className="text-center p-3 font-black text-slate-600">Contactos</th>
                              <th className="text-center p-3 font-black text-slate-600">Tiendas</th>
                            </tr>
                          </thead>
                          <tbody>
                            {directorMetrics.byUser.map((user) => (
                              <tr key={user.userId} className="border-t border-slate-100 hover:bg-slate-50">
                                <td className="p-3 font-bold text-slate-900">{user.userName}</td>
                                <td className="p-3">
                                  <span className={`px-2 py-1 rounded-full text-xs font-bold ${user.role === 'Resp. Delegación' ? 'bg-red-100 text-red-700' : 'bg-purple-100 text-purple-700'}`}>
                                    {user.role}
                                  </span>
                                </td>
                                <td className="p-3 text-right font-black text-green-600">{formatCurrency(user.totalValue)}</td>
                                <td className="p-3 text-right font-bold text-blue-600">{formatCurrency(user.pipelineValue)}</td>
                                <td className="p-3 text-center">
                                  <span className={`px-2 py-1 rounded-full text-xs font-black ${user.conversionRate >= 50 ? 'bg-green-100 text-green-700' : user.conversionRate >= 25 ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'}`}>
                                    {user.conversionRate}%
                                  </span>
                                </td>
                                <td className="p-3 text-center font-bold">{user.wonOpportunities}/{user.totalOpportunities}</td>
                                <td className="p-3 text-center font-bold">{user.totalContacts}</td>
                                <td className="p-3 text-center font-bold">{user.totalShops}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {/* Charts Section */}
                  {directorTrends && (
                    <div className="space-y-6">
                      <h3 className="text-lg font-black text-slate-900 mb-4 flex items-center gap-2">
                        <BarChart3 className="text-blue-500" size={20} />
                        Análisis y Tendencias
                      </h3>
                      
                      <div className="grid grid-cols-2 gap-6">
                        {/* Monthly Sales Chart */}
                        <div className="bg-white rounded-xl border border-slate-200 p-4">
                          <h4 className="font-bold text-slate-700 mb-4">Ventas Mensuales (€)</h4>
                          <div className="h-64">
                            <ResponsiveContainer width="100%" height="100%">
                              <BarChart data={directorTrends.monthly || []}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                                <XAxis dataKey="monthLabel" tick={{ fontSize: 11 }} />
                                <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `${(v/1000).toFixed(0)}k`} />
                                <Tooltip formatter={(value) => formatCurrency(value)} labelStyle={{ fontWeight: 'bold' }} />
                                <Bar dataKey="wonValue" fill="#22c55e" name="Ventas Cerradas" radius={[4,4,0,0]} />
                                <Bar dataKey="createdValue" fill="#3b82f6" name="Creadas" radius={[4,4,0,0]} />
                              </BarChart>
                            </ResponsiveContainer>
                          </div>
                        </div>

                        {/* Opportunities Count Chart */}
                        <div className="bg-white rounded-xl border border-slate-200 p-4">
                          <h4 className="font-bold text-slate-700 mb-4">Oportunidades por Mes</h4>
                          <div className="h-64">
                            <ResponsiveContainer width="100%" height="100%">
                              <LineChart data={directorTrends.monthly || []}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                                <XAxis dataKey="monthLabel" tick={{ fontSize: 11 }} />
                                <YAxis tick={{ fontSize: 11 }} />
                                <Tooltip />
                                <Line type="monotone" dataKey="created" stroke="#6366f1" strokeWidth={2} name="Creadas" dot={{ r: 4 }} />
                                <Line type="monotone" dataKey="won" stroke="#22c55e" strokeWidth={2} name="Ganadas" dot={{ r: 4 }} />
                                <Line type="monotone" dataKey="lost" stroke="#ef4444" strokeWidth={2} name="Perdidas" dot={{ r: 4 }} />
                              </LineChart>
                            </ResponsiveContainer>
                          </div>
                        </div>

                        {/* Funnel */}
                        {directorTrends.funnel && directorTrends.funnel.length > 0 && (
                          <div className="bg-white rounded-xl border border-slate-200 p-4 col-span-2">
                            <h4 className="font-bold text-slate-700 mb-4">Embudo de Conversión</h4>
                            <div className="space-y-2">
                              {directorTrends.funnel.map((stage, idx) => {
                                const maxCount = Math.max(...directorTrends.funnel.map(s => s.count));
                                const width = maxCount > 0 ? (stage.count / maxCount) * 100 : 0;
                                const colors = ['bg-blue-500', 'bg-yellow-500', 'bg-purple-500', 'bg-orange-500', 'bg-green-500'];
                                return (
                                  <div key={stage.stage} className="flex items-center gap-3">
                                    <span className="w-24 text-xs font-bold text-slate-600 text-right">{stage.name}</span>
                                    <div className="flex-1 h-8 bg-slate-100 rounded-lg overflow-hidden relative">
                                      <div 
                                        className={`h-full ${colors[idx % colors.length]} transition-all duration-500`}
                                        style={{ width: `${width}%` }}
                                      />
                                      <span className="absolute inset-0 flex items-center justify-center text-xs font-black text-slate-700">
                                        {stage.count} ({formatCurrency(stage.value)})
                                      </span>
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* WORK TAB */}
              {directorTab === 'work' && (
                <div className="space-y-4">
                  {/* Summary Cards */}
                  {directorData?.summary && (
                    <div className="grid grid-cols-4 gap-4 mb-4">
                      <div className="bg-white rounded-xl p-4 border border-slate-200">
                        <div className="flex items-center gap-2 text-indigo-600 mb-1">
                          <Users size={16} />
                          <span className="text-xs font-bold uppercase">Usuarios</span>
                        </div>
                        <p className="text-2xl font-black text-slate-900">{directorData.summary.totalUsers}</p>
                      </div>
                      <div className="bg-white rounded-xl p-4 border border-slate-200">
                        <div className="flex items-center gap-2 text-blue-600 mb-1">
                          <FolderOpen size={16} />
                          <span className="text-xs font-bold uppercase">Proyectos</span>
                        </div>
                        <p className="text-2xl font-black text-slate-900">{directorData.summary.totalProjects}</p>
                      </div>
                      <div className="bg-white rounded-xl p-4 border border-slate-200">
                        <div className="flex items-center gap-2 text-purple-600 mb-1">
                          <Briefcase size={16} />
                          <span className="text-xs font-bold uppercase">Oportunidades</span>
                        </div>
                        <p className="text-2xl font-black text-slate-900">{directorData.summary.totalOpportunities}</p>
                      </div>
                      <div className="bg-white rounded-xl p-4 border border-slate-200">
                        <div className="flex items-center gap-2 text-emerald-600 mb-1">
                          <FileText size={16} />
                          <span className="text-xs font-bold uppercase">Digitalizaciones</span>
                        </div>
                        <p className="text-2xl font-black text-slate-900">{directorData.summary.totalDigitalizaciones}</p>
                      </div>
                    </div>
                  )}

                  {/* Filters */}
                  <div className="flex gap-4 items-center mb-4">
                    <div className="relative flex-1">
                      <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                      <input
                        type="text"
                        value={directorSearchTerm}
                        onChange={(e) => setDirectorSearchTerm(e.target.value)}
                        placeholder="Buscar por cliente, proyecto o usuario..."
                        className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:border-indigo-500"
                      />
                    </div>
                    <select
                      value={directorFilterUser}
                      onChange={(e) => setDirectorFilterUser(e.target.value)}
                      className="px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm font-bold focus:outline-none focus:border-indigo-500"
                    >
                      <option value="">Todos los usuarios</option>
                      {directorData?.users?.map(u => (
                        <option key={u.id} value={u.id}>{u.username} ({u.clientName})</option>
                      ))}
                    </select>
                  </div>

                  {directorLoading ? (
                    <div className="flex items-center justify-center h-40">
                      <RefreshCw size={24} className="animate-spin text-indigo-500" />
                    </div>
                  ) : (
                    <>
                      {/* Projects Section */}
                      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
                        <button
                          onClick={() => toggleDirectorSection('projects')}
                          className="w-full px-4 py-3 bg-blue-50 flex justify-between items-center hover:bg-blue-100 transition-colors"
                        >
                          <div className="flex items-center gap-2">
                            <FolderOpen size={18} className="text-blue-600" />
                            <span className="font-bold text-blue-900">
                              Proyectos ({directorData?.projects?.filter(p => {
                                const matchesSearch = !directorSearchTerm || 
                                  p.customerName?.toLowerCase().includes(directorSearchTerm.toLowerCase()) ||
                                  p.projectName?.toLowerCase().includes(directorSearchTerm.toLowerCase());
                                const matchesUser = !directorFilterUser || p.userId === directorFilterUser;
                                return matchesSearch && matchesUser;
                              }).length || 0})
                            </span>
                          </div>
                          {directorExpandedSections.projects ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                        </button>
                        {directorExpandedSections.projects && (
                          <div className="divide-y divide-slate-100 max-h-60 overflow-y-auto">
                            {(!directorData?.projects || directorData.projects.filter(p => {
                              const matchesSearch = !directorSearchTerm || 
                                p.customerName?.toLowerCase().includes(directorSearchTerm.toLowerCase()) ||
                                p.projectName?.toLowerCase().includes(directorSearchTerm.toLowerCase());
                              const matchesUser = !directorFilterUser || p.userId === directorFilterUser;
                              return matchesSearch && matchesUser;
                            }).length === 0) ? (
                              <p className="p-4 text-center text-slate-400 text-sm">No hay proyectos</p>
                            ) : (
                              directorData.projects.filter(p => {
                                const matchesSearch = !directorSearchTerm || 
                                  p.customerName?.toLowerCase().includes(directorSearchTerm.toLowerCase()) ||
                                  p.projectName?.toLowerCase().includes(directorSearchTerm.toLowerCase());
                                const matchesUser = !directorFilterUser || p.userId === directorFilterUser;
                                return matchesSearch && matchesUser;
                              }).map(proj => (
                                <div key={proj.id} className="p-3 hover:bg-slate-50 flex justify-between items-center">
                                  <div>
                                    <p className="font-bold text-slate-900">{proj.projectName || 'Sin nombre'}</p>
                                    <p className="text-xs text-slate-500">{proj.customerName}</p>
                                  </div>
                                  <div className="text-right">
                                    <p className="text-xs font-bold text-indigo-600">{proj.userName}</p>
                                    <p className="text-[10px] text-slate-400">{proj.createdAt ? new Date(proj.createdAt).toLocaleDateString('es-ES') : ''}</p>
                                  </div>
                                </div>
                              ))
                            )}
                          </div>
                        )}
                      </div>

                      {/* Opportunities Section */}
                      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
                        <button
                          onClick={() => toggleDirectorSection('opportunities')}
                          className="w-full px-4 py-3 bg-purple-50 flex justify-between items-center hover:bg-purple-100 transition-colors"
                        >
                          <div className="flex items-center gap-2">
                            <Briefcase size={18} className="text-purple-600" />
                            <span className="font-bold text-purple-900">
                              Oportunidades CRM ({directorData?.opportunities?.filter(o => {
                                const matchesSearch = !directorSearchTerm || 
                                  o.title?.toLowerCase().includes(directorSearchTerm.toLowerCase()) ||
                                  o.contactName?.toLowerCase().includes(directorSearchTerm.toLowerCase());
                                const matchesUser = !directorFilterUser || o.assignedTo === directorFilterUser;
                                return matchesSearch && matchesUser;
                              }).length || 0})
                            </span>
                          </div>
                          {directorExpandedSections.opportunities ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                        </button>
                        {directorExpandedSections.opportunities && (
                          <div className="divide-y divide-slate-100 max-h-60 overflow-y-auto">
                            {(!directorData?.opportunities || directorData.opportunities.filter(o => {
                              const matchesSearch = !directorSearchTerm || 
                                o.title?.toLowerCase().includes(directorSearchTerm.toLowerCase()) ||
                                o.contactName?.toLowerCase().includes(directorSearchTerm.toLowerCase());
                              const matchesUser = !directorFilterUser || o.assignedTo === directorFilterUser;
                              return matchesSearch && matchesUser;
                            }).length === 0) ? (
                              <p className="p-4 text-center text-slate-400 text-sm">No hay oportunidades</p>
                            ) : (
                              directorData.opportunities.filter(o => {
                                const matchesSearch = !directorSearchTerm || 
                                  o.title?.toLowerCase().includes(directorSearchTerm.toLowerCase()) ||
                                  o.contactName?.toLowerCase().includes(directorSearchTerm.toLowerCase());
                                const matchesUser = !directorFilterUser || o.assignedTo === directorFilterUser;
                                return matchesSearch && matchesUser;
                              }).map(opp => (
                                <div key={opp.id} className="p-3 hover:bg-slate-50 flex justify-between items-center">
                                  <div>
                                    <p className="font-bold text-slate-900">{opp.title}</p>
                                    <p className="text-xs text-slate-500">{opp.contactName} - {opp.stage}</p>
                                  </div>
                                  <div className="text-right">
                                    <p className="font-bold text-purple-600">{opp.value?.toLocaleString('es-ES', { style: 'currency', currency: 'EUR' })}</p>
                                    <p className="text-xs text-slate-400">{opp.userName}</p>
                                  </div>
                                </div>
                              ))
                            )}
                          </div>
                        )}
                      </div>
                    </>
                  )}
                </div>
              )}

              {/* Loading State */}
              {directorTab === 'metrics' && !directorMetrics && (
                <div className="flex items-center justify-center h-40">
                  <RefreshCw size={24} className="animate-spin text-indigo-500" />
                  <span className="ml-3 text-slate-500">Cargando métricas...</span>
                </div>
              )}
            </div>
          )}

          {activeTab === 'users' && (
            <div className="space-y-6">
              {!isEditingUser ? (
                <>
                  {/* Header with search and add button */}
                  <div className="flex justify-between items-center mb-4">
                    <div className="relative flex-1 max-w-md">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                      <input
                        type="text"
                        placeholder="Buscar usuario..."
                        value={userSearch}
                        onChange={(e) => setUserSearch(e.target.value)}
                        className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none focus:border-indigo-500"
                      />
                    </div>
                    <button
                      onClick={handleCreateUser}
                      className="flex items-center gap-2 px-6 py-2 bg-indigo-600 text-white rounded-xl font-black uppercase text-xs hover:bg-indigo-700 transition-all shadow-lg"
                    >
                      <UserPlus size={18} />
                      {(state.currentUser?.isAdmin || state.currentUser?.isGerente || state.currentUser?.isDirectorComercial) ? 'Nuevo Usuario' : 'Nueva Tienda'}
                    </button>
                  </div>

                  {/* Filtro por rol - Deslizable */}
                  <div className="flex items-center gap-2 overflow-x-auto pb-2">
                    <span className="text-xs font-black text-slate-500 uppercase whitespace-nowrap">Filtrar por rol:</span>
                    <div className="flex gap-1 bg-slate-100 rounded-xl p-1">
                      <button
                        onClick={() => setUserRoleFilter('all')}
                        className={`px-3 py-1.5 rounded-lg text-xs font-bold uppercase whitespace-nowrap transition-all ${
                          userRoleFilter === 'all' ? 'bg-slate-700 text-white shadow' : 'text-slate-600 hover:bg-slate-200'
                        }`}
                      >
                        Todos ({visibleUsers.length})
                      </button>
                      <button
                        onClick={() => setUserRoleFilter('gerente')}
                        className={`px-3 py-1.5 rounded-lg text-xs font-bold uppercase whitespace-nowrap transition-all ${
                          userRoleFilter === 'gerente' ? 'bg-blue-500 text-white shadow' : 'text-slate-600 hover:bg-blue-100'
                        }`}
                      >
                        👔 Gerente ({visibleUsers.filter(u => u.isGerente).length})
                      </button>
                      <button
                        onClick={() => setUserRoleFilter('director')}
                        className={`px-3 py-1.5 rounded-lg text-xs font-bold uppercase whitespace-nowrap transition-all ${
                          userRoleFilter === 'director' ? 'bg-orange-500 text-white shadow' : 'text-slate-600 hover:bg-orange-100'
                        }`}
                      >
                        🛡️ Director ({visibleUsers.filter(u => u.isAdmin).length})
                      </button>
                      <button
                        onClick={() => setUserRoleFilter('responsable')}
                        className={`px-3 py-1.5 rounded-lg text-xs font-bold uppercase whitespace-nowrap transition-all ${
                          userRoleFilter === 'responsable' ? 'bg-red-500 text-white shadow' : 'text-slate-600 hover:bg-red-100'
                        }`}
                      >
                        📍 Resp. Delegación ({visibleUsers.filter(u => u.isResponsableDelegacion).length})
                      </button>
                      <button
                        onClick={() => setUserRoleFilter('comercial')}
                        className={`px-3 py-1.5 rounded-lg text-xs font-bold uppercase whitespace-nowrap transition-all ${
                          userRoleFilter === 'comercial' ? 'bg-purple-500 text-white shadow' : 'text-slate-600 hover:bg-purple-100'
                        }`}
                      >
                        💼 Comercial ({visibleUsers.filter(u => u.isRepresentative && !u.isAdmin && !u.isGerente && !u.isResponsableDelegacion).length})
                      </button>
                      <button
                        onClick={() => setUserRoleFilter('tienda')}
                        className={`px-3 py-1.5 rounded-lg text-xs font-bold uppercase whitespace-nowrap transition-all ${
                          userRoleFilter === 'tienda' ? 'bg-green-500 text-white shadow' : 'text-slate-600 hover:bg-green-100'
                        }`}
                      >
                        🏪 Punto de Venta ({visibleUsers.filter(u => u.isTienda).length})
                      </button>
                      <button
                        onClick={() => setUserRoleFilter('colaborador')}
                        className={`px-3 py-1.5 rounded-lg text-xs font-bold uppercase whitespace-nowrap transition-all ${
                          userRoleFilter === 'colaborador' ? 'bg-amber-500 text-white shadow' : 'text-slate-600 hover:bg-amber-100'
                        }`}
                      >
                        🤝 Colaborador ({visibleUsers.filter(u => u.isPrescriptor).length})
                      </button>
                    </div>
                  </div>

                  {/* Users List */}
                  <div className="space-y-3">
                    {filteredUsers.map(user => (
                      <div key={user.id} className="bg-white border border-slate-200 rounded-xl p-4 hover:shadow-md transition-all">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                              <div className={`p-2 rounded-lg ${user.isGerente ? 'bg-blue-100' : user.isAdmin ? 'bg-orange-100' : user.isResponsableDelegacion ? 'bg-red-100' : user.isRepresentative ? 'bg-purple-100' : user.isPrescriptor ? 'bg-amber-100' : user.isTienda ? 'bg-green-100' : 'bg-indigo-100'}`}>
                                {user.isGerente ? <Shield size={20} className="text-blue-600" /> :
                                 user.isAdmin ? <Shield size={20} className="text-orange-600" /> : 
                                 user.isResponsableDelegacion ? <Shield size={20} className="text-red-600" /> :
                                 user.isRepresentative ? <Briefcase size={20} className="text-purple-600" /> :
                                 user.isPrescriptor ? <UserPlus size={20} className="text-amber-600" /> :
                                 user.isTienda ? <Store size={20} className="text-green-600" /> :
                                 <Store size={20} className="text-indigo-600" />}
                              </div>
                              <div>
                                <h3 className="text-lg font-black text-slate-900">{user.clientName}</h3>
                                <p className="text-xs text-slate-500 font-bold uppercase">@{user.username}</p>
                              </div>
                              <div className={`px-3 py-1 rounded-lg text-xs font-black ${user.isActive ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                                {user.isActive ? 'ACTIVO' : 'INACTIVO'}
                              </div>
                            </div>
                            
                            <div className="grid grid-cols-3 gap-3 mt-3">
                              <div className="bg-slate-50 p-2 rounded-lg">
                                <p className="text-[9px] font-black text-slate-400 uppercase mb-1">Rol</p>
                                <p className="text-xs font-bold text-slate-900">
                                  {user.isGerente ? '👔 Gerente' :
                                   user.isAdmin ? '🛡️ Director Comercial' : 
                                   user.isResponsableDelegacion ? '📍 Resp. Delegación' : 
                                   user.isRepresentative ? '💼 Comercial' : 
                                   user.isPrescriptor ? '🤝 Colaborador' : 
                                   user.isTienda ? '🏪 Punto de Venta' : '🏪 Tienda'}
                                </p>
                              </div>
                              <div className="bg-slate-50 p-2 rounded-lg">
                                <p className="text-[9px] font-black text-slate-400 uppercase mb-1">Dto. Montada</p>
                                <p className="text-xs font-bold text-green-600">{user.discountMontada || 0}%</p>
                              </div>
                              <div className="bg-slate-50 p-2 rounded-lg">
                                <p className="text-[9px] font-black text-slate-400 uppercase mb-1">Dto. Despiece</p>
                                <p className="text-xs font-bold text-orange-600">{user.discountDespiece || 0}%</p>
                              </div>
                              <div className="bg-slate-50 p-2 rounded-lg">
                                <p className="text-[9px] font-black text-slate-400 uppercase mb-1">Módulos</p>
                                <p className="text-xs font-bold text-indigo-600">
                                  {user.allowedModules?.join(', ').toUpperCase() || 'N/A'}
                                </p>
                              </div>
                              <div className="bg-amber-50 p-2 rounded-lg">
                                <p className="text-[9px] font-black text-slate-400 uppercase mb-1">Tarifas</p>
                                <p className="text-xs font-bold text-amber-700">
                                  {user.allowedLibraries?.join(', ') || 'ZC'}
                                </p>
                              </div>
                            </div>

                            {/* Capabilities badges */}
                            <div className="flex flex-wrap gap-1 mt-3">
                              {user.canAuthorizePermissions && <span className="px-2 py-1 bg-red-100 text-red-700 rounded text-[9px] font-black">AUTORIZA</span>}
                              {user.canAccessArmarios && <span className="px-2 py-1 bg-cyan-100 text-cyan-700 rounded text-[9px] font-black">ARMARIOS</span>}
                              {user.canUseAIAnalysis && <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded text-[9px] font-black">IA LAB</span>}
                              {user.canSeeCost && <span className="px-2 py-1 bg-orange-100 text-orange-700 rounded text-[9px] font-black">VER COSTO</span>}
                              {user.canViewTechnicalDespiece && <span className="px-2 py-1 bg-indigo-100 text-indigo-700 rounded text-[9px] font-black">INFORMES</span>}
                              {user.canManageArticles && <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-[9px] font-black">INVENTARIO</span>}
                              {user.canAccessCRM && <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-[9px] font-black">CRM</span>}
                              {user.canUseDigitalizador && <span className="px-2 py-1 bg-amber-100 text-amber-700 rounded text-[9px] font-black">DIGITALIZADOR</span>}
                              {user.canAccessFabrica && (
                                <span className="px-2 py-1 bg-emerald-100 text-emerald-700 rounded text-[9px] font-black">
                                  FÁBRICA{user.factoryId && factories.find(f => f.id === user.factoryId) ? ` (${factories.find(f => f.id === user.factoryId).code})` : ''}
                                </span>
                              )}
                              {user.canAccessMontajes && <span className="px-2 py-1 bg-orange-100 text-orange-700 rounded text-[9px] font-black">MONTAJES</span>}
                              {user.isMontador && <span className="px-2 py-1 bg-rose-100 text-rose-700 rounded text-[9px] font-black">MONTADOR</span>}
                              {user.useCustomBranding && <span className="px-2 py-1 bg-pink-100 text-pink-700 rounded text-[9px] font-black">PERSONALIZAR</span>}
                            </div>
                          </div>

                          <div className="flex gap-2">
                            <button
                              onClick={() => handleEditUser(user)}
                              className="p-2 hover:bg-indigo-50 rounded-lg transition-all"
                              title="Editar"
                            >
                              <Pencil size={16} className="text-indigo-600" />
                            </button>
                            {user.id !== 'admin' && (
                              <button
                                onClick={() => handleDeleteUser(user.id)}
                                className="p-2 hover:bg-red-50 rounded-lg transition-all"
                                title="Eliminar"
                              >
                                <Trash2 size={16} className="text-red-600" />
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                /* User Form */
                <div className="bg-white border-2 border-orange-200 rounded-2xl p-6">
                  <div className="flex justify-between items-center mb-6">
                    <h3 className="text-xl font-black text-slate-900 uppercase">
                      {editingUserId ? 'Editar Usuario' : 'Nuevo Usuario'}
                    </h3>
                    <button
                      onClick={() => setIsEditingUser(false)}
                      className="text-slate-400 hover:text-slate-600"
                    >
                      <X size={24} />
                    </button>
                  </div>

                  <div className="space-y-6">
                    {/* Basic Info */}
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-xs font-black text-slate-600 uppercase mb-2 block">Nombre *</label>
                        <input
                          type="text"
                          value={userForm.clientName}
                          onChange={(e) => setUserForm({...userForm, clientName: e.target.value})}
                          placeholder="Ej: COCINAS MADRID S.L."
                          className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-sm font-bold outline-none focus:border-orange-500"
                        />
                      </div>
                      <div>
                        <label className="text-xs font-black text-slate-600 uppercase mb-2 block">Identificador Técnico *</label>
                        <input
                          type="text"
                          value={userForm.username}
                          onChange={(e) => setUserForm({...userForm, username: e.target.value.toUpperCase()})}
                          placeholder="USUARIO"
                          className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-sm font-black uppercase outline-none focus:border-orange-500"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="text-xs font-black text-slate-600 uppercase mb-2 block">Clave Acceso</label>
                      <input
                        type="password"
                        value={userForm.password || ''}
                        onChange={(e) => setUserForm({...userForm, password: e.target.value})}
                        placeholder={editingUserId ? "Dejar vacío para no cambiar" : "••••"}
                        className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-sm font-bold outline-none focus:border-orange-500"
                      />
                    </div>

                    {/* Role & Hierarchy */}
                    {(state.currentUser?.isAdmin || state.currentUser?.isGerente || state.currentUser?.isDirectorComercial) && (
                      <div className="bg-orange-50 p-4 rounded-xl border border-orange-100">
                        <h4 className="text-sm font-black text-orange-900 uppercase mb-3">Rol y Jerarquía</h4>
                        <div className="space-y-3">
                          {/* GERENTE - Primero */}
                          <label className="flex items-center gap-3 cursor-pointer p-3 bg-blue-50 rounded-xl border border-blue-200">
                            <input
                              type="checkbox"
                              checked={userForm.isGerente}
                              onChange={(e) => setUserForm({...userForm, isGerente: e.target.checked, isAdmin: false})}
                              className="w-5 h-5 rounded border-2 border-blue-300"
                            />
                            <div>
                              <span className="text-sm font-black text-slate-900">Gerente</span>
                              <p className="text-xs text-slate-500">Acceso total al sistema</p>
                            </div>
                          </label>
                          {/* DIRECTOR COMERCIAL - Segundo */}
                          <label className="flex items-center gap-3 cursor-pointer p-3 bg-orange-100 rounded-xl border border-orange-200">
                            <input
                              type="checkbox"
                              checked={userForm.isDirectorComercial}
                              onChange={(e) => setUserForm({...userForm, isDirectorComercial: e.target.checked, isGerente: false})}
                              className="w-5 h-5 rounded border-2 border-orange-300"
                            />
                            <div>
                              <span className="text-sm font-black text-slate-900">Director Comercial</span>
                              <p className="text-xs text-slate-500">Ve todo el CRM y estadísticas</p>
                            </div>
                          </label>
                          <label className="flex items-center gap-3 cursor-pointer">
                            <input
                              type="checkbox"
                              checked={userForm.isRepresentative}
                              onChange={(e) => setUserForm({...userForm, isRepresentative: e.target.checked, isPrescriptor: false})}
                              className="w-5 h-5 rounded border-2 border-orange-300"
                            />
                            <div>
                              <span className="text-sm font-black text-slate-900">Comercial / Representante</span>
                              <p className="text-xs text-slate-500">Puede tener tiendas asignadas</p>
                            </div>
                          </label>

                          {/* Checkbox Responsable Delegación - Solo visible para Director Comercial */}
                          {(state.currentUser?.isAdmin || state.currentUser?.isGerente || state.currentUser?.isDirectorComercial) && (
                            <label className="flex items-center gap-3 cursor-pointer p-3 bg-red-50 rounded-xl border border-red-200">
                              <input
                                type="checkbox"
                                checked={userForm.isResponsableDelegacion}
                                onChange={(e) => setUserForm({
                                  ...userForm, 
                                  isResponsableDelegacion: e.target.checked, 
                                  isRepresentative: false, 
                                  isPrescriptor: false, 
                                  isTienda: false,
                                  isAdmin: false,
                                  isGerente: false,
                                  canAuthorizePermissions: e.target.checked // Por defecto puede autorizar
                                })}
                                className="w-5 h-5 rounded border-2 border-red-300"
                              />
                              <div>
                                <span className="text-sm font-black text-slate-900">Responsable de Delegación</span>
                                <p className="text-xs text-slate-500">Reporta al Director Comercial. Puede autorizar permisos a comerciales.</p>
                              </div>
                            </label>
                          )}

                          {/* Checkbox Colaborador Comercial - Solo visible para Admin/Responsable */}
                          {(state.currentUser?.isAdmin || state.currentUser?.isGerente || state.currentUser?.isDirectorComercial || state.currentUser?.isResponsableDelegacion) && (
                            <label className="flex items-center gap-3 cursor-pointer p-3 bg-amber-50 rounded-xl border border-amber-200">
                              <input
                                type="checkbox"
                                checked={userForm.isPrescriptor}
                                onChange={(e) => setUserForm({...userForm, isPrescriptor: e.target.checked, isRepresentative: false, isTienda: false, isAdmin: false, isGerente: false, isResponsableDelegacion: false})}
                                className="w-5 h-5 rounded border-2 border-amber-300"
                              />
                              <div>
                                <span className="text-sm font-black text-slate-900">Colaborador Comercial</span>
                                <p className="text-xs text-slate-500">Solo aporta contactos/clientes potenciales</p>
                              </div>
                            </label>
                          )}

                          {/* Checkbox Tienda/Punto de Venta - Solo visible para Admin/Responsable */}
                          {(state.currentUser?.isAdmin || state.currentUser?.isGerente || state.currentUser?.isDirectorComercial || state.currentUser?.isResponsableDelegacion || state.currentUser?.canAuthorizePermissions) && (
                            <label className="flex items-center gap-3 cursor-pointer p-3 bg-green-50 rounded-xl border border-green-200">
                              <input
                                type="checkbox"
                                checked={userForm.isTienda}
                                onChange={(e) => setUserForm({...userForm, isTienda: e.target.checked, isRepresentative: false, isPrescriptor: false, isAdmin: false, isGerente: false, isResponsableDelegacion: false})}
                                className="w-5 h-5 rounded border-2 border-green-300"
                              />
                              <div>
                                <span className="text-sm font-black text-slate-900">Tienda / Punto de Venta</span>
                                <p className="text-xs text-slate-500">Solo acceso al presupuestador (sin CRM ni panel maestro)</p>
                              </div>
                            </label>
                          )}

                          {/* Vincular Tienda a Comercial/Responsable/Director - Para roles Tienda */}
                          {userForm.isTienda && representatives.length > 0 && (
                            <div>
                              <label className="text-xs font-black text-slate-600 uppercase mb-2 block">Vincular a Comercial / Responsable / Director</label>
                              <select
                                value={userForm.linkedRepresentativeId || ''}
                                onChange={(e) => setUserForm({...userForm, linkedRepresentativeId: e.target.value})}
                                className="w-full bg-white border border-orange-200 rounded-xl p-3 text-sm font-bold outline-none"
                              >
                                <option value="">Sin vincular</option>
                                {representatives.map(rep => (
                                  <option key={rep.id} value={rep.id}>
                                    {rep.clientName} ({rep.isAdmin ? 'Director' : rep.isResponsableDelegacion ? 'Resp. Deleg.' : 'Comercial'})
                                  </option>
                                ))}
                              </select>
                              <p className="text-[10px] text-slate-400 mt-1">La tienda quedará bajo la gestión de este usuario</p>
                            </div>
                          )}

                          {/* Vincular a Cliente Activo - Ya no se usa para tiendas */}
                          {state.currentUser?.isAdmin && !userForm.isTienda && clients.length > 0 && (
                            <div>
                              <label className="text-xs font-black text-slate-600 uppercase mb-2 block">
                                <Building2 size={12} className="inline mr-1" />
                                Vincular a Cliente
                              </label>
                              <select
                                value={userForm.linkedClientId || ''}
                                onChange={(e) => {
                                  const selectedClientId = e.target.value;
                                  const selectedClient = clients.find(c => c.id === selectedClientId);
                                  setUserForm({
                                    ...userForm, 
                                    linkedClientId: selectedClientId,
                                    // Heredar descuento del cliente si está vinculado
                                    commercialDiscount: selectedClient?.descuento || userForm.commercialDiscount
                                  });
                                }}
                                className="w-full bg-white border border-emerald-200 rounded-xl p-3 text-sm font-bold outline-none focus:border-emerald-500"
                              >
                                <option value="">Sin cliente vinculado</option>
                                {clients.filter(c => c.activo).map(client => (
                                  <option key={client.id} value={client.id}>
                                    {client.codigo} - {client.nombre} {client.descuento > 0 ? `(Dto: ${client.descuento}%)` : ''}
                                  </option>
                                ))}
                              </select>
                              <p className="text-[10px] text-slate-400 mt-1">El usuario heredará el descuento del cliente vinculado</p>
                            </div>
                          )}

                          {/* SELECTOR DE FÁBRICA - Para usuarios con acceso a fábrica */}
                          {factories.length > 0 && (
                            <div className="mt-3 bg-gradient-to-r from-emerald-50 to-teal-50 rounded-xl p-4 border border-emerald-200">
                              <label className="text-xs font-black text-emerald-700 mb-2 block flex items-center gap-2">
                                <Factory size={14} className="text-emerald-600" />
                                🏭 Fábrica Asignada
                              </label>
                              <select
                                value={userForm.factoryId || ''}
                                onChange={(e) => setUserForm({...userForm, factoryId: e.target.value})}
                                className="w-full px-3 py-2 border-2 border-emerald-300 rounded-xl text-sm font-bold text-emerald-800 focus:border-emerald-500 outline-none bg-white"
                                data-testid="factory-selector"
                              >
                                <option value="">-- Sin fábrica asignada --</option>
                                {factories.map(factory => (
                                  <option key={factory.id} value={factory.id}>
                                    {factory.name} ({factory.code})
                                  </option>
                                ))}
                              </select>
                              <p className="text-[10px] text-emerald-500 mt-1">
                                Si tiene rol de fábrica, solo verá las órdenes de esta fábrica
                              </p>
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Si es comercial, mostrar info de asignación automática */}
                    {!(state.currentUser?.isAdmin || state.currentUser?.isGerente || state.currentUser?.isDirectorComercial) && state.currentUser?.isRepresentative && (
                      <div className="bg-indigo-50 p-4 rounded-xl border border-indigo-200">
                        <div className="flex items-center gap-3">
                          <Briefcase size={20} className="text-indigo-600" />
                          <div>
                            <p className="text-sm font-black text-indigo-900">Nueva tienda asignada a ti</p>
                            <p className="text-xs text-indigo-600">Como comercial, esta tienda quedará bajo tu gestión</p>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Modules */}
                    <div className="bg-indigo-50 p-4 rounded-xl border border-indigo-100">
                      <h4 className="text-sm font-black text-indigo-900 uppercase mb-3">Módulos Activos</h4>
                      <div className="flex flex-wrap gap-3">
                        <label className="flex items-center gap-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={userForm.allowedModules?.includes('montada')}
                            onChange={() => handleToggleModule('montada')}
                            className="w-5 h-5 rounded border-2 border-indigo-300"
                          />
                          <span className="text-sm font-black text-slate-900">Uso Cocina Montada</span>
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={userForm.allowedModules?.includes('despiece')}
                            onChange={() => handleToggleModule('despiece')}
                            className="w-5 h-5 rounded border-2 border-indigo-300"
                          />
                          <span className="text-sm font-black text-slate-900">Uso Formato Despiece</span>
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer bg-purple-100 px-3 py-1 rounded-lg border border-purple-200">
                          <input
                            type="checkbox"
                            checked={userForm.canAccessArmarios}
                            onChange={(e) => setUserForm({...userForm, canAccessArmarios: e.target.checked})}
                            className="w-5 h-5 rounded border-2 border-purple-300"
                          />
                          <span className="text-sm font-black text-purple-900">Diseñador Armarios</span>
                        </label>
                      </div>
                    </div>

                    {/* Tarifas/Bibliotecas Activas */}
                    <div className="bg-amber-50 p-4 rounded-xl border border-amber-200">
                      <h4 className="text-sm font-black text-amber-900 uppercase mb-3">
                        📦 Tarifas de Precios Activas
                      </h4>
                      <p className="text-xs text-amber-700 mb-3">
                        Selecciona las tarifas/catálogos a los que tiene acceso este usuario para presupuestar
                      </p>
                      <div className="flex flex-wrap gap-3">
                        <label className="flex items-center gap-2 cursor-pointer bg-white px-3 py-2 rounded-lg border border-amber-200 hover:border-amber-400 transition-colors">
                          <input
                            type="checkbox"
                            checked={userForm.allowedLibraries?.includes('ZC')}
                            onChange={() => {
                              const libs = userForm.allowedLibraries || [];
                              const newLibs = libs.includes('ZC') 
                                ? libs.filter(l => l !== 'ZC') 
                                : [...libs, 'ZC'];
                              setUserForm({...userForm, allowedLibraries: newLibs});
                            }}
                            className="w-5 h-5 rounded border-2 border-amber-400 accent-amber-500"
                            data-testid="library-zc-checkbox"
                          />
                          <div>
                            <span className="text-sm font-black text-slate-900 block">ZC</span>
                            <span className="text-[10px] text-slate-500">Sistema Zonas Z1-Z12</span>
                          </div>
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer bg-white px-3 py-2 rounded-lg border border-amber-200 hover:border-amber-400 transition-colors">
                          <input
                            type="checkbox"
                            checked={userForm.allowedLibraries?.includes('MV')}
                            onChange={() => {
                              const libs = userForm.allowedLibraries || [];
                              const newLibs = libs.includes('MV') 
                                ? libs.filter(l => l !== 'MV') 
                                : [...libs, 'MV'];
                              setUserForm({...userForm, allowedLibraries: newLibs});
                            }}
                            className="w-5 h-5 rounded border-2 border-amber-400 accent-amber-500"
                            data-testid="library-mv-checkbox"
                          />
                          <div>
                            <span className="text-sm font-black text-slate-900 block">MV</span>
                            <span className="text-[10px] text-slate-500">Sistema Tarifas T1-T21</span>
                          </div>
                        </label>
                      </div>
                    </div>

                    {/* Technical Capabilities */}
                    <div className="bg-purple-50 p-4 rounded-xl border border-purple-100">
                      <h4 className="text-sm font-black text-purple-900 uppercase mb-3">Capacidades Técnicas</h4>
                      <div className="grid grid-cols-3 gap-x-4 gap-y-2">
                        {/* Columna 1: Análisis y Visualización */}
                        <label className="flex items-center gap-2 cursor-pointer bg-white/50 px-2 py-1.5 rounded-lg hover:bg-white transition-colors">
                          <input
                            type="checkbox"
                            checked={userForm.canUseAIAnalysis}
                            onChange={(e) => setUserForm({...userForm, canUseAIAnalysis: e.target.checked})}
                            className="w-4 h-4 rounded accent-purple-600"
                          />
                          <span className="text-xs font-bold text-slate-700">IA Lab</span>
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer bg-white/50 px-2 py-1.5 rounded-lg hover:bg-white transition-colors">
                          <input
                            type="checkbox"
                            checked={userForm.canSeeCost}
                            onChange={(e) => setUserForm({...userForm, canSeeCost: e.target.checked})}
                            className="w-4 h-4 rounded accent-purple-600"
                          />
                          <span className="text-xs font-bold text-slate-700">Ver Costo</span>
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer bg-white/50 px-2 py-1.5 rounded-lg hover:bg-white transition-colors">
                          <input
                            type="checkbox"
                            checked={userForm.canViewTechnicalDespiece}
                            onChange={(e) => setUserForm({...userForm, canViewTechnicalDespiece: e.target.checked})}
                            className="w-4 h-4 rounded accent-purple-600"
                          />
                          <span className="text-xs font-bold text-slate-700">Informes</span>
                        </label>
                        
                        {/* Columna 2: Acceso a Módulos */}
                        <label className="flex items-center gap-2 cursor-pointer bg-white/50 px-2 py-1.5 rounded-lg hover:bg-white transition-colors">
                          <input
                            type="checkbox"
                            checked={userForm.canAccessCRM}
                            onChange={(e) => setUserForm({...userForm, canAccessCRM: e.target.checked})}
                            className="w-4 h-4 rounded accent-blue-600"
                          />
                          <span className="text-xs font-bold text-slate-700">CRM</span>
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer bg-white/50 px-2 py-1.5 rounded-lg hover:bg-white transition-colors">
                          <input
                            type="checkbox"
                            checked={userForm.canUseDigitalizador}
                            onChange={(e) => setUserForm({...userForm, canUseDigitalizador: e.target.checked})}
                            className="w-4 h-4 rounded accent-orange-600"
                          />
                          <span className="text-xs font-bold text-slate-700">Digitalizador</span>
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer bg-emerald-100 px-2 py-1.5 rounded-lg hover:bg-emerald-200 transition-colors border border-emerald-300">
                          <input
                            type="checkbox"
                            checked={userForm.canAccessFabrica}
                            onChange={(e) => setUserForm({...userForm, canAccessFabrica: e.target.checked})}
                            className="w-4 h-4 rounded accent-emerald-600"
                          />
                          <span className="text-xs font-black text-emerald-800">FÁBRICA</span>
                        </label>
                        
                        {/* Columna 3: Otros permisos */}
                        <label className="flex items-center gap-2 cursor-pointer bg-white/50 px-2 py-1.5 rounded-lg hover:bg-white transition-colors">
                          <input
                            type="checkbox"
                            checked={userForm.canAccessMontajes}
                            onChange={(e) => setUserForm({...userForm, canAccessMontajes: e.target.checked})}
                            className="w-4 h-4 rounded accent-orange-600"
                          />
                          <span className="text-xs font-bold text-slate-700">Montajes</span>
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer bg-white/50 px-2 py-1.5 rounded-lg hover:bg-white transition-colors">
                          <input
                            type="checkbox"
                            checked={userForm.canManageArticles}
                            onChange={(e) => setUserForm({...userForm, canManageArticles: e.target.checked})}
                            className="w-4 h-4 rounded accent-green-600"
                          />
                          <span className="text-xs font-bold text-slate-700">Inventario</span>
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer bg-white/50 px-2 py-1.5 rounded-lg hover:bg-white transition-colors">
                          <input
                            type="checkbox"
                            checked={userForm.isMontador}
                            onChange={(e) => setUserForm({...userForm, isMontador: e.target.checked})}
                            className="w-4 h-4 rounded accent-rose-600"
                          />
                          <span className="text-xs font-bold text-slate-700">Montador</span>
                        </label>
                        
                        {/* Fila extra: Personalización */}
                        <label className="flex items-center gap-2 cursor-pointer bg-white/50 px-2 py-1.5 rounded-lg hover:bg-white transition-colors">
                          <input
                            type="checkbox"
                            checked={userForm.useCustomBranding}
                            onChange={(e) => setUserForm({...userForm, useCustomBranding: e.target.checked})}
                            className="w-4 h-4 rounded accent-pink-600"
                          />
                          <span className="text-xs font-bold text-slate-700">Personalizar</span>
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer bg-white/50 px-2 py-1.5 rounded-lg hover:bg-white transition-colors">
                          <input
                            type="checkbox"
                            checked={userForm.canChangeLogo}
                            onChange={(e) => setUserForm({...userForm, canChangeLogo: e.target.checked})}
                            className="w-4 h-4 rounded accent-pink-600"
                          />
                          <span className="text-xs font-bold text-slate-700">Cambiar Logo</span>
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer bg-white/50 px-2 py-1.5 rounded-lg hover:bg-white transition-colors">
                          <input
                            type="checkbox"
                            checked={userForm.canAuthorizePermissions}
                            onChange={(e) => setUserForm({...userForm, canAuthorizePermissions: e.target.checked})}
                            className="w-4 h-4 rounded accent-red-600"
                          />
                          <span className="text-xs font-bold text-slate-700">Autorizar</span>
                        </label>
                      </div>
                      
                      {/* Checkbox especial para usuario SOLO fábrica */}
                      <div className="mt-3 pt-3 border-t border-purple-200">
                        <label className="flex items-center gap-3 cursor-pointer bg-emerald-50 px-3 py-2 rounded-lg hover:bg-emerald-100 transition-colors border border-emerald-200">
                          <input
                            type="checkbox"
                            checked={userForm.isFabrica}
                            onChange={(e) => setUserForm({...userForm, isFabrica: e.target.checked})}
                            className="w-5 h-5 rounded accent-emerald-600"
                          />
                          <div>
                            <span className="text-sm font-black text-emerald-800 block">Usuario SOLO Fábrica</span>
                            <span className="text-[10px] text-emerald-600">Solo verá el módulo de Fábrica, sin acceso a presupuestos, clientes ni otros módulos</span>
                          </div>
                        </label>
                      </div>
                    </div>

                    {/* Commercial Discount */}
                    <div className="bg-green-50 p-4 rounded-xl border border-green-100">
                      <h4 className="text-sm font-black text-green-900 uppercase mb-3">Descuentos Comerciales (%)</h4>
                      
                      {/* Descuento Montada */}
                      <div className="mb-4">
                        <label className="text-xs font-bold text-green-700 mb-1 block">Descuento MONTADA</label>
                        <div className="flex items-center gap-4">
                          <input
                            type="range"
                            min="0"
                            max="100"
                            value={userForm.discountMontada}
                            onChange={(e) => setUserForm({...userForm, discountMontada: parseInt(e.target.value)})}
                            className="flex-1"
                          />
                          <input
                            type="number"
                            min="0"
                            max="100"
                            value={userForm.discountMontada}
                            onChange={(e) => setUserForm({...userForm, discountMontada: parseInt(e.target.value) || 0})}
                            className="w-20 bg-white border-2 border-green-300 rounded-xl p-2 text-center text-lg font-black text-green-700 outline-none"
                          />
                          <span className="text-sm font-black text-green-700">%</span>
                        </div>
                      </div>
                      
                      {/* Descuento Despiece */}
                      <div>
                        <label className="text-xs font-bold text-orange-700 mb-1 block">Descuento DESPIECE</label>
                        <div className="flex items-center gap-4">
                          <input
                            type="range"
                            min="0"
                            max="100"
                            value={userForm.discountDespiece}
                            onChange={(e) => setUserForm({...userForm, discountDespiece: parseInt(e.target.value)})}
                            className="flex-1"
                          />
                          <input
                            type="number"
                            min="0"
                            max="100"
                            value={userForm.discountDespiece}
                            onChange={(e) => setUserForm({...userForm, discountDespiece: parseInt(e.target.value) || 0})}
                            className="w-20 bg-white border-2 border-orange-300 rounded-xl p-2 text-center text-lg font-black text-orange-700 outline-none"
                          />
                          <span className="text-sm font-black text-orange-700">%</span>
                        </div>
                      </div>
                    </div>

                    {/* Active Status */}
                    <label className="flex items-center gap-3 cursor-pointer p-4 bg-slate-50 rounded-xl border border-slate-200">
                      <input
                        type="checkbox"
                        checked={userForm.isActive}
                        onChange={(e) => setUserForm({...userForm, isActive: e.target.checked})}
                        className="w-5 h-5 rounded border-2 border-slate-300"
                      />
                      <div>
                        <span className="text-sm font-black text-slate-900">Usuario Activo</span>
                        <p className="text-xs text-slate-500">Puede iniciar sesión en el sistema</p>
                      </div>
                    </label>

                    {/* Action Buttons */}
                    <div className="flex gap-3 pt-4 border-t border-slate-200">
                      <button
                        onClick={handleSaveUser}
                        className="flex-1 bg-indigo-600 text-white py-3 rounded-xl font-black uppercase text-sm hover:bg-indigo-700 transition-all shadow-lg flex items-center justify-center gap-2"
                      >
                        <Check size={18} />
                        Guardar Configuración
                      </button>
                      <button
                        onClick={() => setIsEditingUser(false)}
                        className="px-6 py-3 bg-slate-200 text-slate-700 rounded-xl font-black uppercase text-sm hover:bg-slate-300 transition-all"
                      >
                        Cancelar
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Tab Clientes */}
          {activeTab === 'clients' && (
            <div className="space-y-6">
              {!isEditingClient ? (
                <>
                  {/* Header with filters */}
                  <div className="flex flex-wrap justify-between items-center gap-4 mb-6">
                    <div className="flex items-center gap-3 flex-wrap">
                      <div className="relative">
                        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                        <input
                          type="text"
                          placeholder="Buscar cliente..."
                          value={clientSearch}
                          onChange={(e) => setClientSearch(e.target.value)}
                          className="pl-10 pr-4 py-2 bg-white border border-slate-200 rounded-xl text-sm focus:outline-none focus:border-emerald-500 w-56"
                        />
                      </div>
                      
                      {/* Filtro por tipo */}
                      <select
                        value={clientFilterType}
                        onChange={(e) => setClientFilterType(e.target.value)}
                        className="px-3 py-2 bg-white border border-slate-200 rounded-xl text-sm font-bold focus:outline-none focus:border-emerald-500"
                      >
                        <option value="todos">Todos</option>
                        <option value="potencial">🟠 Potenciales</option>
                        <option value="activo">🟢 Activos</option>
                      </select>
                      
                      {/* Filtro por segmento */}
                      <select
                        value={clientFilterSegment}
                        onChange={(e) => setClientFilterSegment(e.target.value)}
                        className="px-3 py-2 bg-white border border-slate-200 rounded-xl text-sm font-bold focus:outline-none focus:border-emerald-500"
                      >
                        <option value="">Todos los segmentos</option>
                        {clientSegments.map(seg => (
                          <option key={seg} value={seg}>{seg}</option>
                        ))}
                      </select>
                    </div>
                    
                    <div className="flex gap-2">
                      <label className="flex items-center gap-2 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold uppercase cursor-pointer transition-colors">
                        <Upload size={14} />
                        Importar CSV
                        <input
                          type="file"
                          accept=".csv"
                          className="hidden"
                          onChange={async (e) => {
                            const file = e.target.files[0];
                            if (!file) return;
                            setIsImportingClients(true);
                            setImportResult(null);
                            try {
                              const text = await file.text();
                              const lines = text.split('\n').filter(l => l.trim());
                              const headers = lines[0].split(/[,;]/).map(h => h.trim().toLowerCase());
                              const clientsData = lines.slice(1).map(line => {
                                const values = line.split(/[,;]/);
                                const client = {};
                                headers.forEach((h, i) => {
                                  const key = h === 'cp' ? 'codigoPostal' : h;
                                  client[key] = values[i]?.trim() || '';
                                });
                                return client;
                              });
                              const result = await clientsAPI.importCSV(clientsData);
                              setImportResult(result);
                              loadClients();
                            } catch (err) {
                              setImportResult({ error: err.message });
                            } finally {
                              setIsImportingClients(false);
                              e.target.value = '';
                            }
                          }}
                        />
                      </label>
                      
                      {/* Nuevo Cliente Potencial */}
                      <button
                        onClick={() => {
                          setIsEditingClient(true);
                          setEditingClientId(null);
                          setClientForm({
                            tipo: 'potencial',
                            codigo: '',
                            nombre: '',
                            cif: '',
                            segmento: '',
                            direccion: '',
                            localidad: '',
                            provincia: '',
                            codigoPostal: '',
                            telefono: '',
                            email: '',
                            descuento: 0,
                            activo: true,
                            notas: ''
                          });
                        }}
                        className="flex items-center gap-2 px-4 py-2 bg-orange-500 hover:bg-orange-600 text-white rounded-xl text-xs font-bold uppercase transition-colors"
                      >
                        <Plus size={14} />
                        Potencial
                      </button>
                      
                      {/* Nuevo Cliente Activo */}
                      <button
                        onClick={() => {
                          setIsEditingClient(true);
                          setEditingClientId(null);
                          setClientForm({
                            tipo: 'activo',
                            codigo: '',
                            nombre: '',
                            cif: '',
                            segmento: '',
                            direccion: '',
                            localidad: '',
                            provincia: '',
                            codigoPostal: '',
                            telefono: '',
                            email: '',
                            descuento: 0,
                            activo: true,
                            notas: ''
                          });
                        }}
                        className="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold uppercase transition-colors"
                        data-testid="add-client-btn"
                      >
                        <Plus size={14} />
                        Activo
                      </button>
                      
                      {/* Botón Exportar Clientes */}
                      <button
                        onClick={async () => {
                          try {
                            const token = localStorage.getItem('token');
                            const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/export/clientes`, {
                              headers: { 'Authorization': `Bearer ${token}` }
                            });
                            if (response.ok) {
                              const blob = await response.blob();
                              const url = window.URL.createObjectURL(blob);
                              const a = document.createElement('a');
                              a.href = url;
                              a.download = `LUIGGI_Clientes_${new Date().toISOString().split('T')[0]}.xlsx`;
                              a.click();
                              window.URL.revokeObjectURL(url);
                            }
                          } catch (err) {
                            console.error('Error exportando:', err);
                          }
                        }}
                        className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold uppercase transition-colors"
                        data-testid="export-clients-btn"
                      >
                        <Download size={14} />
                        Excel
                      </button>
                    </div>
                  </div>

                  {/* Stats */}
                  <div className="grid grid-cols-3 gap-4 mb-4">
                    <div className="bg-slate-50 rounded-xl p-3 text-center">
                      <p className="text-2xl font-black text-slate-700">{clients.length}</p>
                      <p className="text-[10px] font-bold text-slate-400 uppercase">Total</p>
                    </div>
                    <div className="bg-orange-50 rounded-xl p-3 text-center">
                      <p className="text-2xl font-black text-orange-600">{clients.filter(c => !c.codigo && (c.tipo === 'potencial' || !c.tipo)).length}</p>
                      <p className="text-[10px] font-bold text-orange-400 uppercase">Potenciales</p>
                    </div>
                    <div className="bg-emerald-50 rounded-xl p-3 text-center">
                      <p className="text-2xl font-black text-emerald-600">{clients.filter(c => c.codigo || c.tipo === 'activo').length}</p>
                      <p className="text-[10px] font-bold text-emerald-400 uppercase">Activos</p>
                    </div>
                  </div>

                  {importResult && (
                    <div className={`p-4 rounded-xl text-sm font-medium ${importResult.error ? 'bg-red-100 text-red-700' : 'bg-emerald-100 text-emerald-700'}`}>
                      {importResult.error ? `Error: ${importResult.error}` : `Importación: ${importResult.imported} nuevos, ${importResult.updated} actualizados`}
                      <button onClick={() => setImportResult(null)} className="ml-2 underline">Cerrar</button>
                    </div>
                  )}

                  {/* Clients table */}
                  <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
                    <table className="w-full">
                      <thead className="bg-slate-50 border-b border-slate-200">
                        <tr>
                          <th className="px-3 py-3 text-left text-[10px] font-black text-slate-500 uppercase">Tipo</th>
                          <th className="px-3 py-3 text-left text-[10px] font-black text-slate-500 uppercase">Código</th>
                          <th className="px-3 py-3 text-left text-[10px] font-black text-slate-500 uppercase">Nombre</th>
                          <th className="px-3 py-3 text-left text-[10px] font-black text-slate-500 uppercase">Segmento</th>
                          <th className="px-3 py-3 text-left text-[10px] font-black text-slate-500 uppercase">Localidad</th>
                          <th className="px-3 py-3 text-center text-[10px] font-black text-slate-500 uppercase">Dto%</th>
                          <th className="px-3 py-3 text-center text-[10px] font-black text-slate-500 uppercase">Vinculado</th>
                          <th className="px-3 py-3 text-center text-[10px] font-black text-slate-500 uppercase">Acciones</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {clients
                          .filter(c => {
                            // Inferir tipo si no existe: si tiene código es activo
                            const tipo = c.tipo || (c.codigo ? 'activo' : 'potencial');
                            if (clientFilterType !== 'todos' && tipo !== clientFilterType) return false;
                            if (clientFilterSegment && c.segmento !== clientFilterSegment) return false;
                            if (!clientSearch) return true;
                            const q = clientSearch.toLowerCase();
                            return c.codigo?.toLowerCase().includes(q) ||
                                   c.nombre?.toLowerCase().includes(q) ||
                                   c.cif?.toLowerCase().includes(q) ||
                                   c.localidad?.toLowerCase().includes(q);
                          })
                          .map(client => {
                            // Inferir tipo para clientes antiguos
                            const clientTipo = client.tipo || (client.codigo ? 'activo' : 'potencial');
                            return (
                            <tr key={client.id} className="hover:bg-slate-50 transition-colors">
                              <td className="px-3 py-2">
                                <span className={`px-2 py-1 rounded-lg text-[10px] font-black uppercase ${
                                  clientTipo === 'activo' ? 'bg-emerald-100 text-emerald-700' : 'bg-orange-100 text-orange-700'
                                }`}>
                                  {clientTipo === 'activo' ? '🟢 ACTIVO' : '🟠 POTENCIAL'}
                                </span>
                              </td>
                              <td className="px-3 py-2">
                                <span className="font-mono font-bold text-indigo-600">{client.codigo || '-'}</span>
                              </td>
                              <td className="px-3 py-2">
                                <span className="font-bold text-slate-900 text-sm">{client.nombre}</span>
                                {client.cif && <p className="text-[10px] text-slate-400">{client.cif}</p>}
                              </td>
                              <td className="px-3 py-2">
                                <span className="text-xs text-slate-600">{client.segmento || '-'}</span>
                              </td>
                              <td className="px-3 py-2 text-slate-600 text-xs">{client.localidad || '-'}</td>
                              <td className="px-3 py-2 text-center">
                                {client.descuento > 0 ? (
                                  <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded-lg text-xs font-bold">{client.descuento}%</span>
                                ) : '-'}
                              </td>
                              <td className="px-3 py-2 text-center">
                                {client.usuarioVinculadoId ? (
                                  <span className="text-emerald-600 text-xs font-bold">✓ Sí</span>
                                ) : (
                                  <span className="text-slate-300 text-xs">No</span>
                                )}
                              </td>
                              <td className="px-3 py-2">
                                <div className="flex justify-center gap-1">
                                  {/* Activar (solo si es potencial y no tiene código) */}
                                  {clientTipo === 'potencial' && !client.codigo && (
                                    <button
                                      onClick={() => { setShowActivateModal(client); setActivateCode(''); }}
                                      className="p-1.5 text-orange-500 hover:text-emerald-600 hover:bg-emerald-50 rounded-lg transition-colors"
                                      title="Activar cliente"
                                    >
                                      <CheckCircle size={14} />
                                    </button>
                                  )}
                                  {/* Vincular usuario */}
                                  <button
                                    onClick={() => { setShowLinkUserModal(client); setLinkUserId(client.usuarioVinculadoId || ''); }}
                                    className="p-1.5 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
                                    title="Vincular usuario"
                                  >
                                    <UserPlus size={14} />
                                  </button>
                                  <button
                                    onClick={() => {
                                      setIsEditingClient(true);
                                      setEditingClientId(client.id);
                                      setClientForm({ ...client, tipo: clientTipo });
                                    }}
                                    className="p-1.5 text-slate-400 hover:text-emerald-600 hover:bg-emerald-50 rounded-lg transition-colors"
                                    title="Editar"
                                  >
                                    <Pencil size={14} />
                                  </button>
                                  <button
                                    onClick={async () => {
                                      if (!window.confirm(`¿Eliminar cliente "${client.nombre}"?`)) return;
                                      try {
                                        const result = await clientsAPI.delete(client.id);
                                        console.log('Delete result:', result);
                                        alert(`✅ ${result.message || 'Cliente eliminado correctamente'}`);
                                        loadClients();
                                      } catch (err) {
                                        console.error('Delete error:', err);
                                        // Si tiene usuarios vinculados, preguntar si forzar
                                        if (err.message && err.message.includes('vinculado')) {
                                          if (window.confirm(`${err.message}\n\n¿Desea forzar la eliminación? Los usuarios serán desvinculados automáticamente.`)) {
                                            try {
                                              const result = await clientsAPI.delete(client.id, true);
                                              alert(`✅ ${result.message || 'Cliente eliminado correctamente'}`);
                                              loadClients();
                                            } catch (err2) {
                                              alert(`❌ ${err2.message}`);
                                            }
                                          }
                                        } else {
                                          alert(`❌ ${err.message}`);
                                        }
                                      }
                                    }}
                                    className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                                    title="Eliminar"
                                  >
                                    <Trash2 size={14} />
                                  </button>
                                </div>
                              </td>
                            </tr>
                          );})
                        }
                      </tbody>
                    </table>
                    
                    {clients.length === 0 && (
                      <div className="p-8 text-center text-slate-400">
                        <Building2 size={40} className="mx-auto mb-3 opacity-50" />
                        <p className="font-medium">No hay clientes registrados</p>
                      </div>
                    )}
                  </div>

                  {/* Modal Activar Cliente */}
                  {showActivateModal && (
                    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 p-6">
                        <h3 className="text-lg font-black text-emerald-700 uppercase mb-4">Activar Cliente</h3>
                        <p className="text-sm text-slate-600 mb-4">
                          Asigna un código del programa de gestión para activar a <strong>{showActivateModal.nombre}</strong>
                        </p>
                        <div className="mb-4">
                          <label className="text-xs font-black text-slate-500 uppercase block mb-1">Código de Cliente *</label>
                          <input
                            type="text"
                            value={activateCode}
                            onChange={(e) => setActivateCode(e.target.value.toUpperCase())}
                            placeholder="Ej: CLI001"
                            className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-lg font-mono font-bold text-center focus:outline-none focus:border-emerald-500"
                            autoFocus
                          />
                        </div>
                        <div className="flex gap-3">
                          <button
                            onClick={() => setShowActivateModal(null)}
                            className="flex-1 px-4 py-2 bg-slate-100 text-slate-700 rounded-xl font-bold"
                          >
                            Cancelar
                          </button>
                          <button
                            onClick={async () => {
                              if (!activateCode.trim()) {
                                alert('El código es obligatorio');
                                return;
                              }
                              try {
                                await clientsAPI.activate(showActivateModal.id, activateCode);
                                setShowActivateModal(null);
                                loadClients();
                              } catch (err) {
                                alert(err.message);
                              }
                            }}
                            className="flex-1 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-bold"
                          >
                            Activar
                          </button>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Modal Vincular Usuario */}
                  {showLinkUserModal && (
                    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 p-6">
                        <h3 className="text-lg font-black text-indigo-700 uppercase mb-4">Vincular Usuario</h3>
                        <p className="text-sm text-slate-600 mb-4">
                          Vincula un usuario del sistema a <strong>{showLinkUserModal.nombre}</strong>
                        </p>
                        <div className="mb-4">
                          <label className="text-xs font-black text-slate-500 uppercase block mb-1">Usuario</label>
                          <select
                            value={linkUserId}
                            onChange={(e) => setLinkUserId(e.target.value)}
                            className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl font-bold focus:outline-none focus:border-indigo-500"
                          >
                            <option value="">Sin vincular</option>
                            {state.users.map(u => (
                              <option key={u.id} value={u.id}>{u.username} ({u.clientName})</option>
                            ))}
                          </select>
                        </div>
                        <div className="flex gap-3">
                          <button
                            onClick={() => setShowLinkUserModal(null)}
                            className="flex-1 px-4 py-2 bg-slate-100 text-slate-700 rounded-xl font-bold"
                          >
                            Cancelar
                          </button>
                          <button
                            onClick={async () => {
                              try {
                                await clientsAPI.linkUser(showLinkUserModal.id, linkUserId);
                                setShowLinkUserModal(null);
                                loadClients();
                              } catch (err) {
                                alert(err.message);
                              }
                            }}
                            className="flex-1 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-bold"
                          >
                            Guardar
                          </button>
                        </div>
                      </div>
                    </div>
                  )}
                </>
              ) : (
                /* Client Edit Form */
                <div className="bg-white rounded-xl border border-slate-200 p-6">
                  <div className="flex justify-between items-center mb-6">
                    <h3 className="text-lg font-black text-slate-900 uppercase">
                      {editingClientId ? 'Editar Cliente' : clientForm.tipo === 'activo' ? 'Nuevo Cliente Activo' : 'Nuevo Cliente Potencial'}
                    </h3>
                    <button
                      onClick={() => {
                        setIsEditingClient(false);
                        setEditingClientId(null);
                      }}
                      className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg"
                    >
                      <X size={20} />
                    </button>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    {/* Tipo y Segmento */}
                    <div>
                      <label className="text-[10px] font-black text-slate-500 uppercase tracking-wider">Tipo de Cliente *</label>
                      <select
                        value={clientForm.tipo}
                        onChange={(e) => setClientForm(p => ({ ...p, tipo: e.target.value }))}
                        className={`w-full mt-1 px-3 py-2 border rounded-lg text-sm font-bold focus:outline-none ${
                          clientForm.tipo === 'activo' ? 'bg-emerald-50 border-emerald-200' : 'bg-orange-50 border-orange-200'
                        }`}
                      >
                        <option value="potencial">🟠 Potencial</option>
                        <option value="activo">🟢 Activo</option>
                      </select>
                    </div>
                    <div>
                      <label className="text-[10px] font-black text-slate-500 uppercase tracking-wider">Segmento</label>
                      <select
                        value={clientForm.segmento}
                        onChange={(e) => setClientForm(p => ({ ...p, segmento: e.target.value }))}
                        className="w-full mt-1 px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm font-bold focus:outline-none focus:border-emerald-500"
                      >
                        <option value="">Seleccionar segmento...</option>
                        {clientSegments.map(seg => (
                          <option key={seg} value={seg}>{seg}</option>
                        ))}
                      </select>
                    </div>

                    {/* Código (solo si es activo) */}
                    {clientForm.tipo === 'activo' && (
                      <div>
                        <label className="text-[10px] font-black text-slate-500 uppercase tracking-wider">Código *</label>
                        <input
                          type="text"
                          value={clientForm.codigo}
                          onChange={(e) => setClientForm(p => ({ ...p, codigo: e.target.value.toUpperCase() }))}
                          className="w-full mt-1 px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm font-mono font-bold focus:outline-none focus:border-emerald-500"
                          placeholder="CLI001"
                          data-testid="client-codigo"
                        />
                      </div>
                    )}
                    <div className={clientForm.tipo === 'activo' ? '' : 'col-span-2'}>
                      <label className="text-[10px] font-black text-slate-500 uppercase tracking-wider">CIF/NIF</label>
                      <input
                        type="text"
                        value={clientForm.cif}
                        onChange={(e) => setClientForm(p => ({ ...p, cif: e.target.value.toUpperCase() }))}
                        className="w-full mt-1 px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-emerald-500"
                        placeholder="B12345678"
                      />
                    </div>

                    <div className="col-span-2">
                      <label className="text-[10px] font-black text-slate-500 uppercase tracking-wider">Nombre / Razón Social *</label>
                      <input
                        type="text"
                        value={clientForm.nombre}
                        onChange={(e) => setClientForm(p => ({ ...p, nombre: e.target.value }))}
                        className="w-full mt-1 px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm font-bold focus:outline-none focus:border-emerald-500"
                        placeholder="Cocinas Pérez S.L."
                        data-testid="client-nombre"
                      />
                    </div>

                    <div className="col-span-2">
                      <label className="text-[10px] font-black text-slate-500 uppercase tracking-wider">Dirección</label>
                      <input
                        type="text"
                        value={clientForm.direccion}
                        onChange={(e) => setClientForm(p => ({ ...p, direccion: e.target.value }))}
                        className="w-full mt-1 px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-emerald-500"
                        placeholder="Calle Mayor, 123"
                      />
                    </div>

                    <div>
                      <label className="text-[10px] font-black text-slate-500 uppercase tracking-wider">Localidad</label>
                      <input
                        type="text"
                        value={clientForm.localidad}
                        onChange={(e) => setClientForm(p => ({ ...p, localidad: e.target.value }))}
                        className="w-full mt-1 px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-emerald-500"
                        placeholder="Madrid"
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <label className="text-[10px] font-black text-slate-500 uppercase tracking-wider">Provincia</label>
                        <input
                          type="text"
                          value={clientForm.provincia}
                          onChange={(e) => setClientForm(p => ({ ...p, provincia: e.target.value }))}
                          className="w-full mt-1 px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-emerald-500"
                          placeholder="Madrid"
                        />
                      </div>
                      <div>
                        <label className="text-[10px] font-black text-slate-500 uppercase tracking-wider">C.P.</label>
                        <input
                          type="text"
                          value={clientForm.codigoPostal}
                          onChange={(e) => setClientForm(p => ({ ...p, codigoPostal: e.target.value }))}
                          className="w-full mt-1 px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-emerald-500"
                          placeholder="28001"
                        />
                      </div>
                    </div>
                    <div>
                      <label className="text-[10px] font-black text-slate-500 uppercase tracking-wider">Teléfono</label>
                      <input
                        type="text"
                        value={clientForm.telefono}
                        onChange={(e) => setClientForm(p => ({ ...p, telefono: e.target.value }))}
                        className="w-full mt-1 px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-emerald-500"
                        placeholder="+34 600 000 000"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] font-black text-slate-500 uppercase tracking-wider">Email</label>
                      <input
                        type="email"
                        value={clientForm.email}
                        onChange={(e) => setClientForm(p => ({ ...p, email: e.target.value }))}
                        className="w-full mt-1 px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-emerald-500"
                        placeholder="info@empresa.com"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] font-black text-slate-500 uppercase tracking-wider">Descuento (%)</label>
                      <input
                        type="number"
                        value={clientForm.descuento}
                        onChange={(e) => setClientForm(p => ({ ...p, descuento: parseFloat(e.target.value) || 0 }))}
                        className="w-full mt-1 px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-emerald-500"
                        min="0"
                        max="100"
                        step="0.5"
                      />
                    </div>
                    <div className="flex items-center gap-3 pt-6">
                      <button
                        onClick={() => setClientForm(p => ({ ...p, activo: !p.activo }))}
                        className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-bold transition-colors ${clientForm.activo ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'}`}
                      >
                        {clientForm.activo ? <CheckSquare size={16} /> : <Square size={16} />}
                        {clientForm.activo ? 'Habilitado' : 'Deshabilitado'}
                      </button>
                    </div>
                    <div className="col-span-2">
                      <label className="text-[10px] font-black text-slate-500 uppercase tracking-wider">Notas</label>
                      <textarea
                        value={clientForm.notas}
                        onChange={(e) => setClientForm(p => ({ ...p, notas: e.target.value }))}
                        className="w-full mt-1 px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-emerald-500 resize-none"
                        rows={2}
                        placeholder="Observaciones..."
                      />
                    </div>
                  </div>

                  {/* Save/Cancel buttons */}
                  <div className="flex justify-end gap-3 mt-6 pt-6 border-t border-slate-200">
                    <button
                      onClick={() => {
                        setIsEditingClient(false);
                        setEditingClientId(null);
                      }}
                      className="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-lg text-sm font-bold transition-colors"
                    >
                      Cancelar
                    </button>
                    <button
                      onClick={async () => {
                        if (!clientForm.nombre) {
                          alert('El nombre es obligatorio');
                          return;
                        }
                        if (clientForm.tipo === 'activo' && !clientForm.codigo) {
                          alert('El código es obligatorio para clientes activos');
                          return;
                        }
                        
                        setIsSavingClient(true);
                        try {
                          if (editingClientId) {
                            await clientsAPI.update(editingClientId, clientForm);
                          } else {
                            await clientsAPI.create(clientForm);
                          }
                          loadClients();
                          setIsEditingClient(false);
                          setEditingClientId(null);
                        } catch (err) {
                          alert(err.message);
                        } finally {
                          setIsSavingClient(false);
                        }
                      }}
                      disabled={isSavingClient}
                      className={`flex items-center gap-2 px-6 py-2 text-white rounded-lg text-sm font-bold transition-colors ${
                        clientForm.tipo === 'activo' ? 'bg-emerald-600 hover:bg-emerald-700' : 'bg-orange-500 hover:bg-orange-600'
                      }`}
                      data-testid="save-client-btn"
                    >
                      {isSavingClient ? <Loader size={14} className="animate-spin" /> : <Save size={14} />}
                      {editingClientId ? 'Guardar Cambios' : 'Crear Cliente'}
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'inventory' && (
            <div className="space-y-6">
              {!isEditingProduct ? (
                <>
                  {/* Header with module selector, library filter, search and add button */}
                  <div className="flex justify-between items-center mb-6 gap-4">
                    <div className="flex gap-3">
                      <button
                        onClick={() => setInventoryModule('montada')}
                        className={`px-6 py-2 rounded-xl text-xs font-black uppercase tracking-widest transition-all ${
                          inventoryModule === 'montada' ? 'bg-orange-600 text-white shadow-lg' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                        }`}
                      >
                        Cocina Montada
                      </button>
                      <button
                        onClick={() => setInventoryModule('despiece')}
                        className={`px-6 py-2 rounded-xl text-xs font-black uppercase tracking-widest transition-all ${
                          inventoryModule === 'despiece' ? 'bg-indigo-700 text-white shadow-lg' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                        }`}
                      >
                        Formato Despiece
                      </button>
                      
                      {/* Filtro por biblioteca */}
                      <select
                        value={inventoryLibraryFilter}
                        onChange={(e) => setInventoryLibraryFilter(e.target.value)}
                        className="px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-xs font-bold uppercase outline-none"
                      >
                        <option value="">TODAS</option>
                        <option value="ZC">ZC</option>
                        <option value="MV">MV</option>
                      </select>
                    </div>
                    
                    <div className="flex gap-3 flex-1 max-w-2xl">
                      <div className="relative flex-1">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                        <input
                          type="text"
                          placeholder="BUSCAR REFERENCIA..."
                          value={productSearch}
                          onChange={(e) => setProductSearch(e.target.value)}
                          className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm font-bold uppercase outline-none focus:border-indigo-500"
                        />
                      </div>
                      
                      {/* Botón eliminar seleccionados */}
                      {selectedProducts.length > 0 && (
                        <button
                          onClick={handleDeleteSelectedProducts}
                          className="flex items-center gap-2 px-6 py-2 bg-red-600 text-white rounded-xl font-black uppercase text-xs hover:bg-red-700 transition-all shadow-lg whitespace-nowrap"
                        >
                          <Trash2 size={18} />
                          Eliminar ({selectedProducts.length})
                        </button>
                      )}
                      
                      <button
                        onClick={handleCreateProduct}
                        className="flex items-center gap-2 px-6 py-2 bg-indigo-950 text-white rounded-xl font-black uppercase text-xs hover:bg-indigo-900 transition-all shadow-lg whitespace-nowrap"
                      >
                        <Plus size={18} />
                        Nueva Alta
                      </button>
                      
                      {/* Botones descargar catálogo por biblioteca */}
                      <a
                        href={`${process.env.REACT_APP_BACKEND_URL}/api/products/export/library/ZC`}
                        download="catalogo_ZC.xlsx"
                        className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-xl font-black uppercase text-xs hover:bg-blue-700 transition-all shadow-lg whitespace-nowrap"
                        data-testid="download-catalog-zc-btn"
                        title="Descargar catálogo ZC (Zonas Z1-Z12)"
                      >
                        <Download size={16} />
                        ZC
                      </a>
                      <a
                        href={`${process.env.REACT_APP_BACKEND_URL}/api/products/export/library/MV`}
                        download="catalogo_MV.xlsx"
                        className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-xl font-black uppercase text-xs hover:bg-green-700 transition-all shadow-lg whitespace-nowrap"
                        data-testid="download-catalog-mv-btn"
                        title="Descargar catálogo MV (Tarifas T1-T21)"
                      >
                        <Download size={16} />
                        MV
                      </a>
                    </div>
                  </div>

                  {/* Filtros de auditoría - Jerarquía: PROGRAMA → TIPO MUEBLE → SERIE */}
                  <div className="flex flex-wrap gap-3 items-center bg-gradient-to-r from-indigo-50 to-amber-50 border border-indigo-200 rounded-xl p-3">
                    <span className="text-xs font-black text-indigo-900 uppercase">📂 Jerarquía:</span>
                    
                    {/* Filtro por PROGRAMA */}
                    <select
                      value={productProgramaFilter}
                      onChange={(e) => {
                        setProductProgramaFilter(e.target.value);
                        setProductTipoMuebleFilter('');
                        setProductSeriesFilter('');
                      }}
                      className="px-3 py-1.5 bg-indigo-100 border-2 border-indigo-400 rounded-lg text-xs font-black focus:outline-none focus:border-indigo-600 min-w-[140px]"
                    >
                      <option value="">📁 PROGRAMA ({availableProgramas.length})</option>
                      {availableProgramas.map(prog => (
                        <option key={prog} value={prog}>{prog}</option>
                      ))}
                    </select>
                    
                    <span className="text-indigo-400 font-bold">→</span>
                    
                    {/* Filtro por TIPO MUEBLE */}
                    <select
                      value={productTipoMuebleFilter}
                      onChange={(e) => {
                        setProductTipoMuebleFilter(e.target.value);
                        setProductSeriesFilter('');
                      }}
                      className="px-3 py-1.5 bg-purple-100 border-2 border-purple-400 rounded-lg text-xs font-black focus:outline-none focus:border-purple-600 min-w-[160px]"
                      disabled={!productProgramaFilter}
                    >
                      <option value="">📂 TIPO MUEBLE ({availableTiposMueble.length})</option>
                      {availableTiposMueble.map(tipo => (
                        <option key={tipo} value={tipo}>{tipo}</option>
                      ))}
                    </select>
                    
                    <span className="text-purple-400 font-bold">→</span>
                    
                    {/* Filtro por SERIE */}
                    <select
                      value={productSeriesFilter}
                      onChange={(e) => setProductSeriesFilter(e.target.value)}
                      className="px-3 py-1.5 bg-amber-100 border-2 border-amber-400 rounded-lg text-xs font-black focus:outline-none focus:border-amber-600 min-w-[200px]"
                      disabled={!productTipoMuebleFilter}
                    >
                      <option value="">📄 SERIE ({availableSeries.length})</option>
                      {availableSeries.map(series => (
                        <option key={series} value={series}>{series}</option>
                      ))}
                    </select>
                    
                    {/* Filtro sin precio */}
                    <button
                      onClick={() => setProductZeroPriceFilter(!productZeroPriceFilter)}
                      className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                        productZeroPriceFilter 
                          ? 'bg-red-600 text-white' 
                          : 'bg-white border border-red-300 text-red-700 hover:bg-red-50'
                      }`}
                    >
                      {productZeroPriceFilter ? <CheckSquare size={14} /> : <Square size={14} />}
                      Sin Precio
                    </button>
                    
                    {/* Limpiar filtros */}
                    {(productProgramaFilter || productTipoMuebleFilter || productSeriesFilter || productZeroPriceFilter) && (
                      <button
                        onClick={() => {
                          setProductProgramaFilter('');
                          setProductTipoMuebleFilter('');
                          setProductSeriesFilter('');
                          setProductZeroPriceFilter(false);
                        }}
                        className="px-3 py-1.5 bg-slate-600 text-white rounded-lg text-xs font-bold hover:bg-slate-700 transition-all"
                      >
                        ✕ Limpiar
                      </button>
                    )}
                  </div>

                  {/* Products Table */}
                  <div className="bg-white border-2 border-indigo-100 rounded-2xl overflow-hidden">
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead className="bg-indigo-950 text-white">
                          <tr>
                            <th className="p-3 text-center w-12">
                              <button 
                                onClick={handleSelectAllProducts}
                                className="p-1 hover:bg-white/20 rounded transition-all"
                                title={selectedProducts.length === filteredProducts.length ? "Deseleccionar todos" : "Seleccionar todos"}
                              >
                                {selectedProducts.length === filteredProducts.length && filteredProducts.length > 0 ? (
                                  <CheckSquare size={18} className="text-orange-400" />
                                ) : (
                                  <Square size={18} className="text-white/60" />
                                )}
                              </button>
                            </th>
                            <th className="p-3 text-left text-[9px] font-black uppercase whitespace-nowrap">REF</th>
                            <th className="p-3 text-left text-[9px] font-black uppercase min-w-[200px]">NOMBRE</th>
                            <th className="p-3 text-left text-[9px] font-black uppercase whitespace-nowrap bg-amber-900">SERIE</th>
                            <th className="p-3 text-center text-[9px] font-black uppercase whitespace-nowrap bg-amber-900">FONDO</th>
                            {inventoryModule === 'montada' ? (
                              <>
                                <th className="p-3 text-center text-[9px] font-black uppercase whitespace-nowrap">Z1</th>
                                <th className="p-3 text-center text-[9px] font-black uppercase whitespace-nowrap">Z2</th>
                                <th className="p-3 text-center text-[9px] font-black uppercase whitespace-nowrap">Z3</th>
                                <th className="p-3 text-center text-[9px] font-black uppercase whitespace-nowrap">Z4</th>
                                <th className="p-3 text-center text-[9px] font-black uppercase whitespace-nowrap">Z5</th>
                                <th className="p-3 text-center text-[9px] font-black uppercase whitespace-nowrap">Z6</th>
                                <th className="p-3 text-center text-[9px] font-black uppercase whitespace-nowrap">Z7</th>
                                <th className="p-3 text-center text-[9px] font-black uppercase whitespace-nowrap">Z8</th>
                                <th className="p-3 text-center text-[9px] font-black uppercase whitespace-nowrap">Z9</th>
                                <th className="p-3 text-center text-[9px] font-black uppercase whitespace-nowrap">Z10</th>
                                <th className="p-3 text-center text-[9px] font-black uppercase whitespace-nowrap">Z11</th>
                                <th className="p-3 text-center text-[9px] font-black uppercase whitespace-nowrap">Z12</th>
                              </>
                            ) : (
                              <th className="p-3 text-center text-[9px] font-black uppercase whitespace-nowrap bg-orange-900">PUNTOS BASE</th>
                            )}
                            <th className="p-3 text-center text-[9px] font-black uppercase whitespace-nowrap sticky right-0 bg-indigo-950 z-10">GESTIÓN</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {filteredProducts.length === 0 ? (
                            <tr>
                              <td colSpan={inventoryModule === 'montada' ? 18 : 8} className="p-8 text-center text-slate-400 italic">
                                No hay productos en este catálogo
                              </td>
                            </tr>
                          ) : (
                            filteredProducts.map(product => (
                              <tr key={product.id} className={`hover:bg-indigo-50/30 transition-colors ${selectedProducts.includes(product.id) ? 'bg-orange-50' : ''}`}>
                                <td className="p-3 text-center">
                                  <button 
                                    onClick={() => handleToggleProductSelection(product.id)}
                                    className="p-1 hover:bg-indigo-100 rounded transition-all"
                                  >
                                    {selectedProducts.includes(product.id) ? (
                                      <CheckSquare size={18} className="text-orange-600" />
                                    ) : (
                                      <Square size={18} className="text-slate-300" />
                                    )}
                                  </button>
                                </td>
                                <td className="p-3 text-xs font-black text-orange-600 uppercase">{product.code}</td>
                                <td className="p-3 text-xs font-bold text-slate-900">{product.name}</td>
                                <td className="p-3 text-[10px] font-bold text-amber-800 bg-amber-50 max-w-[150px] truncate" title={product.series || 'Sin serie'}>{product.series || '-'}</td>
                                <td className="p-3 text-center text-xs font-bold text-amber-800 bg-amber-50">{product.depth || '-'}</td>
                                {inventoryModule === 'montada' ? (
                                  <>
                                    <td className="p-3 text-center text-xs font-bold text-slate-700">{product.zonePoints?.Z1 || product.points || 0}</td>
                                    <td className="p-3 text-center text-xs font-bold text-slate-700">{product.zonePoints?.Z2 || product.points || 0}</td>
                                    <td className="p-3 text-center text-xs font-bold text-slate-700">{product.zonePoints?.Z3 || product.points || 0}</td>
                                    <td className="p-3 text-center text-xs font-bold text-slate-700">{product.zonePoints?.Z4 || product.points || 0}</td>
                                    <td className="p-3 text-center text-xs font-bold text-slate-700">{product.zonePoints?.Z5 || product.points || 0}</td>
                                    <td className="p-3 text-center text-xs font-bold text-slate-700">{product.zonePoints?.Z6 || product.points || 0}</td>
                                    <td className="p-3 text-center text-xs font-bold text-slate-700">{product.zonePoints?.Z7 || product.points || 0}</td>
                                    <td className="p-3 text-center text-xs font-bold text-slate-700">{product.zonePoints?.Z8 || product.points || 0}</td>
                                    <td className="p-3 text-center text-xs font-bold text-slate-700">{product.zonePoints?.Z9 || product.points || 0}</td>
                                    <td className="p-3 text-center text-xs font-bold text-slate-700">{product.zonePoints?.Z10 || product.points || 0}</td>
                                    <td className="p-3 text-center text-xs font-bold text-slate-700">{product.zonePoints?.Z11 || product.points || 0}</td>
                                    <td className="p-3 text-center text-xs font-bold text-slate-700">{product.zonePoints?.Z12 || product.points || 0}</td>
                                  </>
                                ) : (
                                  <td className="p-3 text-center text-lg font-black text-orange-600 bg-orange-50">{product.points || 0}</td>
                                )}
                                <td className="p-3 sticky right-0 bg-white shadow-[-4px_0_6px_-2px_rgba(0,0,0,0.1)]">
                                  <div className="flex justify-center gap-2">
                                    <button
                                      onClick={() => handleEditProduct(product)}
                                      className="p-2 hover:bg-indigo-100 rounded-lg transition-all"
                                      title="Editar"
                                    >
                                      <Pencil size={14} className="text-indigo-600" />
                                    </button>
                                    <button
                                      onClick={() => handleDeleteProduct(product.id)}
                                      className="p-2 hover:bg-red-100 rounded-lg transition-all"
                                      title="Eliminar"
                                    >
                                      <Trash2 size={14} className="text-red-600" />
                                    </button>
                                  </div>
                                </td>
                              </tr>
                            ))
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  <div className="bg-indigo-50 p-4 rounded-xl border border-indigo-100">
                    <p className="text-xs font-bold text-indigo-900">
                      📊 Total de artículos en catálogo <span className="text-orange-600">({inventoryModule === 'montada' ? 'Cocina Montada' : 'Formato Despiece'})</span>: <span className="font-black text-orange-600">{filteredProducts.length}</span>
                      {productSearch && <span className="text-indigo-400 ml-2">(Filtrados de {currentCatalog?.products?.length || 0})</span>}
                    </p>
                  </div>

                  {/* Catalog Importer - AI */}
                  <CatalogImporter 
                    onProductsImported={() => {
                      // Los catálogos se actualizan automáticamente al recargar la página
                      // El usuario puede cerrar el panel y volver a abrirlo para ver los cambios
                      console.log('Productos importados - refrescar catálogos');
                    }}
                  />
                </>
              ) : (
                /* Product Form */
                <div className="bg-white border-2 border-orange-200 rounded-2xl p-6">
                  <div className="flex justify-between items-center mb-6">
                    <h3 className="text-xl font-black text-slate-900 uppercase">
                      {editingProductId ? 'Editar Artículo' : 'Nuevo Artículo'}
                    </h3>
                    <button
                      onClick={() => setIsEditingProduct(false)}
                      className="text-slate-400 hover:text-slate-600"
                    >
                      <X size={24} />
                    </button>
                  </div>

                  <div className="space-y-6">
                    {/* Basic Info */}
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-xs font-black text-slate-600 uppercase mb-2 block">Código / Referencia *</label>
                        <input
                          type="text"
                          value={productForm.code}
                          onChange={(e) => setProductForm({...productForm, code: e.target.value.toUpperCase()})}
                          placeholder="Ej: 35A1P350"
                          className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-sm font-black uppercase outline-none focus:border-orange-500"
                        />
                      </div>
                      <div>
                        <label className="text-xs font-black text-slate-600 uppercase mb-2 block">Nombre Comercial *</label>
                        <input
                          type="text"
                          value={productForm.name}
                          onChange={(e) => setProductForm({...productForm, name: e.target.value})}
                          placeholder="Ej: Alto 1 Puerta 35cm"
                          className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-sm font-bold outline-none focus:border-orange-500"
                        />
                      </div>
                    </div>

                    {/* Dimensions */}
                    <div className="grid grid-cols-3 gap-4">
                      <div>
                        <label className="text-xs font-black text-slate-600 uppercase mb-2 block">Ancho (cm)</label>
                        <input
                          type="number"
                          value={productForm.width}
                          onChange={(e) => setProductForm({...productForm, width: parseInt(e.target.value) || 0})}
                          className="w-full bg-orange-50 border border-orange-200 rounded-xl p-3 text-lg font-black text-center outline-none focus:border-orange-500"
                        />
                      </div>
                      <div>
                        <label className="text-xs font-black text-slate-600 uppercase mb-2 block">Alto (cm)</label>
                        <input
                          type="number"
                          value={productForm.height}
                          onChange={(e) => setProductForm({...productForm, height: parseInt(e.target.value) || 0})}
                          className="w-full bg-orange-50 border border-orange-200 rounded-xl p-3 text-lg font-black text-center outline-none focus:border-orange-500"
                        />
                      </div>
                      <div>
                        <label className="text-xs font-black text-slate-600 uppercase mb-2 block">Fondo (cm)</label>
                        <input
                          type="number"
                          value={productForm.depth}
                          onChange={(e) => setProductForm({...productForm, depth: parseInt(e.target.value) || 0})}
                          className="w-full bg-orange-50 border border-orange-200 rounded-xl p-3 text-lg font-black text-center outline-none focus:border-orange-500"
                        />
                      </div>
                    </div>

                    {/* Zone Points - Solo para Montada */}
                    {inventoryModule === 'montada' ? (
                      <div className="bg-indigo-50 p-6 rounded-xl border border-indigo-200">
                        <h4 className="text-sm font-black text-indigo-900 uppercase mb-4">Puntos por Zona de Acabado (Montada)</h4>
                        <div className="grid grid-cols-4 gap-3">
                          {Object.keys(productForm.zonePoints).map(zone => (
                            <div key={zone}>
                              <label className="text-[9px] font-black text-indigo-600 uppercase mb-1 block">{zone}</label>
                              <input
                                type="number"
                                value={productForm.zonePoints[zone]}
                                onChange={(e) => setProductForm({
                                  ...productForm,
                                  zonePoints: { ...productForm.zonePoints, [zone]: parseInt(e.target.value) || 0 }
                                })}
                                className="w-full bg-white border border-indigo-200 rounded-lg p-2 text-sm font-black text-center text-indigo-900 outline-none focus:border-orange-500"
                              />
                            </div>
                          ))}
                        </div>
                      </div>
                    ) : (
                      <div className="bg-orange-50 p-6 rounded-xl border border-orange-200">
                        <h4 className="text-sm font-black text-orange-900 uppercase mb-4">Puntos Base (Despiece - Sin Zonas)</h4>
                        <p className="text-xs text-orange-700 mb-4">En despiece el precio solo varía según el material del armazón/casco</p>
                        <div>
                          <label className="text-xs font-black text-orange-600 uppercase mb-2 block">Puntos Base del Componente</label>
                          <input
                            type="number"
                            value={productForm.zonePoints?.Z1 || 0}
                            onChange={(e) => {
                              const basePoints = parseInt(e.target.value) || 0;
                              setProductForm({
                                ...productForm,
                                zonePoints: {
                                  Z1: basePoints, Z2: basePoints, Z3: basePoints, Z4: basePoints,
                                  Z5: basePoints, Z6: basePoints, Z7: basePoints, Z8: basePoints,
                                  Z9: basePoints, Z10: basePoints, Z11: basePoints, Z12: basePoints
                                }
                              });
                            }}
                            className="w-full bg-white border-2 border-orange-300 rounded-xl p-4 text-2xl font-black text-center text-orange-900 outline-none focus:border-orange-500"
                          />
                        </div>
                      </div>
                    )}

                    {/* Additional Info */}
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-xs font-black text-slate-600 uppercase mb-2 block">Categoría</label>
                        <input
                          type="text"
                          value={productForm.category}
                          onChange={(e) => setProductForm({...productForm, category: e.target.value})}
                          placeholder="Ej: Altos"
                          className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-sm font-bold outline-none focus:border-orange-500"
                        />
                      </div>
                      <div>
                        <label className="text-xs font-black text-slate-600 uppercase mb-2 block">Serie</label>
                        <input
                          type="text"
                          value={productForm.series}
                          onChange={(e) => setProductForm({...productForm, series: e.target.value})}
                          placeholder="Ej: Altos 35cm"
                          className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-sm font-bold outline-none focus:border-orange-500"
                        />
                      </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex gap-3 pt-4 border-t border-slate-200">
                      <button
                        onClick={handleSaveProduct}
                        className="flex-1 bg-indigo-600 text-white py-3 rounded-xl font-black uppercase text-sm hover:bg-indigo-700 transition-all shadow-lg flex items-center justify-center gap-2"
                      >
                        <Save size={18} />
                        Guardar Artículo
                      </button>
                      <button
                        onClick={() => setIsEditingProduct(false)}
                        className="px-6 py-3 bg-slate-200 text-slate-700 rounded-xl font-black uppercase text-sm hover:bg-slate-300 transition-all"
                      >
                        Cancelar
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'pricing' && (
            <div className="space-y-6">
              <div className="bg-gradient-to-r from-indigo-50 to-purple-50 p-6 rounded-2xl border border-indigo-200">
                <h3 className="text-xl font-black text-indigo-950 uppercase mb-2 flex items-center gap-3">
                  <Euro size={24} className="text-orange-600" />
                  Márgenes Maestros del Sistema
                </h3>
                <p className="text-xs text-indigo-600 font-bold uppercase">Configuración Global de Costos y Valores</p>
              </div>

              {/* Módulos del Sistema */}
              <div className="bg-white border border-orange-200 rounded-2xl p-6 shadow-sm">
                <h3 className="text-sm font-black text-orange-900 uppercase tracking-widest mb-4 flex items-center gap-2">
                  🔧 Módulos del Sistema
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  <label className="flex items-center gap-3 cursor-pointer bg-orange-50 p-4 rounded-xl border border-orange-200 hover:border-orange-400 transition-all">
                    <input
                      type="checkbox"
                      checked={state.settings?.montajesEnabled || false}
                      onChange={async (e) => {
                        const newValue = e.target.checked;
                        setState(prev => ({
                          ...prev,
                          settings: { ...prev.settings, montajesEnabled: newValue }
                        }));
                        try {
                          await settingsAPI.update({ montajesEnabled: newValue });
                        } catch (err) {
                          console.error('Error guardando configuración:', err);
                        }
                      }}
                      className="w-6 h-6 rounded border-2 border-orange-400 accent-orange-600"
                    />
                    <div>
                      <span className="text-sm font-black text-orange-900">Agenda de Montajes</span>
                      <p className="text-xs text-orange-600">Habilitar módulo de gestión de instaladores</p>
                    </div>
                  </label>
                </div>
              </div>

              {/* Valores de Punto */}
              <div className="bg-white border border-indigo-100 rounded-2xl p-6 shadow-sm">
                <h3 className="text-sm font-black text-indigo-900 uppercase tracking-widest mb-4 flex items-center gap-2">
                  💰 Valor de Punto Base
                </h3>
                
                {/* Valor de punto por BIBLIOTECA (MONTADA) */}
                <div className="mb-4">
                  <label className="text-xs font-black text-indigo-600 uppercase mb-3 block">
                    📚 Valor de Punto por Tarifa (Montada)
                  </label>
                  <div className="grid grid-cols-2 gap-4">
                    {(state.libraries || []).map(lib => (
                      <div key={lib.code} className="bg-gradient-to-br from-indigo-50 to-purple-50 border-2 border-indigo-200 rounded-xl p-4">
                        <label className="text-xs font-black text-indigo-500 uppercase mb-2 flex items-center gap-2">
                          <span className={`w-3 h-3 rounded-full ${lib.code === 'ZC' ? 'bg-blue-500' : 'bg-amber-500'}`}></span>
                          {lib.code} (€/punto)
                        </label>
                        <input
                          type="number"
                          step="0.01"
                          value={state.libraryPointValues?.[lib.code] || lib.pointValue || 1.0}
                          onChange={async (e) => {
                            const newValue = parseFloat(e.target.value) || 1.0;
                            // Actualizar estado local
                            setState(prev => ({
                              ...prev,
                              libraryPointValues: {
                                ...prev.libraryPointValues,
                                [lib.code]: newValue
                              }
                            }));
                            // Guardar en backend
                            try {
                              await librariesAPI.update(lib.code, { pointValue: newValue });
                            } catch (err) {
                              console.error('Error guardando valor de punto:', err);
                            }
                          }}
                          className="w-full bg-white border-2 border-indigo-300 rounded-xl p-3 text-2xl font-black text-indigo-900 outline-none focus:border-orange-500 text-center"
                        />
                      </div>
                    ))}
                    {(!state.libraries || state.libraries.length === 0) && (
                      <div className="col-span-2 text-center text-indigo-400 py-4">
                        <Loader className="w-6 h-6 animate-spin inline mr-2" />
                        Cargando bibliotecas...
                      </div>
                    )}
                  </div>
                </div>

                {/* Separador */}
                <div className="border-t border-indigo-100 my-4"></div>
                
                {/* Valor de punto DESPIECE (común) */}
                <div>
                  <label className="text-xs font-black text-indigo-400 uppercase mb-2 block">
                    🔧 Despiece (€/punto) - Común a todas las tarifas
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={state.pointValueDespiece}
                    onChange={(e) => setState(prev => ({ ...prev, pointValueDespiece: parseFloat(e.target.value) || 0.88 }))}
                    className="w-full bg-indigo-50 border-2 border-indigo-200 rounded-xl p-4 text-2xl font-black text-indigo-900 outline-none focus:border-orange-500 text-center max-w-xs"
                  />
                </div>
              </div>

              {/* Incrementos Cortes Especiales POR TARIFA */}
              <div className="bg-white border border-orange-100 rounded-2xl p-6 shadow-sm">
                <h3 className="text-sm font-black text-orange-900 uppercase tracking-widest mb-4 flex items-center gap-2">
                  ✂️ Incrementos Cortes Especiales por Tarifa
                </h3>
                
                {/* Incrementos ZC */}
                <div className="mb-4 bg-gradient-to-br from-blue-50 to-indigo-50 border-2 border-blue-200 rounded-xl p-4">
                  <label className="text-xs font-black text-blue-600 uppercase mb-3 flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full bg-blue-500"></span>
                    TARIFA ZC
                  </label>
                  <div className="grid grid-cols-3 gap-3">
                    <div>
                      <label className="text-[10px] font-black text-blue-400 uppercase mb-1 block">Ancho (€)</label>
                      <input
                        type="number"
                        value={state.librarySpecialIncrements?.ZC?.width ?? state.specialIncrementWidth}
                        onChange={(e) => setState(prev => ({
                          ...prev,
                          librarySpecialIncrements: {
                            ...prev.librarySpecialIncrements,
                            ZC: { ...prev.librarySpecialIncrements?.ZC, width: parseInt(e.target.value) || 45 }
                          }
                        }))}
                        className="w-full bg-white border-2 border-blue-200 rounded-xl p-3 text-xl font-black text-blue-900 outline-none focus:border-blue-500 text-center"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] font-black text-blue-400 uppercase mb-1 block">Alto (€)</label>
                      <input
                        type="number"
                        value={state.librarySpecialIncrements?.ZC?.height ?? state.specialIncrementHeight}
                        onChange={(e) => setState(prev => ({
                          ...prev,
                          librarySpecialIncrements: {
                            ...prev.librarySpecialIncrements,
                            ZC: { ...prev.librarySpecialIncrements?.ZC, height: parseInt(e.target.value) || 45 }
                          }
                        }))}
                        className="w-full bg-white border-2 border-blue-200 rounded-xl p-3 text-xl font-black text-blue-900 outline-none focus:border-blue-500 text-center"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] font-black text-blue-400 uppercase mb-1 block">Fondo (€)</label>
                      <input
                        type="number"
                        value={state.librarySpecialIncrements?.ZC?.depth ?? state.specialIncrementDepth}
                        onChange={(e) => setState(prev => ({
                          ...prev,
                          librarySpecialIncrements: {
                            ...prev.librarySpecialIncrements,
                            ZC: { ...prev.librarySpecialIncrements?.ZC, depth: parseInt(e.target.value) || 45 }
                          }
                        }))}
                        className="w-full bg-white border-2 border-blue-200 rounded-xl p-3 text-xl font-black text-blue-900 outline-none focus:border-blue-500 text-center"
                      />
                    </div>
                  </div>
                </div>
                
                {/* Incrementos MV */}
                <div className="mb-4 bg-gradient-to-br from-amber-50 to-orange-50 border-2 border-amber-200 rounded-xl p-4">
                  <label className="text-xs font-black text-amber-600 uppercase mb-3 flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full bg-amber-500"></span>
                    TARIFA MV
                  </label>
                  <div className="grid grid-cols-3 gap-3">
                    <div>
                      <label className="text-[10px] font-black text-amber-400 uppercase mb-1 block">Ancho (€)</label>
                      <input
                        type="number"
                        value={state.librarySpecialIncrements?.MV?.width ?? state.specialIncrementWidth}
                        onChange={(e) => setState(prev => ({
                          ...prev,
                          librarySpecialIncrements: {
                            ...prev.librarySpecialIncrements,
                            MV: { ...prev.librarySpecialIncrements?.MV, width: parseInt(e.target.value) || 45 }
                          }
                        }))}
                        className="w-full bg-white border-2 border-amber-200 rounded-xl p-3 text-xl font-black text-amber-900 outline-none focus:border-amber-500 text-center"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] font-black text-amber-400 uppercase mb-1 block">Alto (€)</label>
                      <input
                        type="number"
                        value={state.librarySpecialIncrements?.MV?.height ?? state.specialIncrementHeight}
                        onChange={(e) => setState(prev => ({
                          ...prev,
                          librarySpecialIncrements: {
                            ...prev.librarySpecialIncrements,
                            MV: { ...prev.librarySpecialIncrements?.MV, height: parseInt(e.target.value) || 45 }
                          }
                        }))}
                        className="w-full bg-white border-2 border-amber-200 rounded-xl p-3 text-xl font-black text-amber-900 outline-none focus:border-amber-500 text-center"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] font-black text-amber-400 uppercase mb-1 block">Fondo (€)</label>
                      <input
                        type="number"
                        value={state.librarySpecialIncrements?.MV?.depth ?? state.specialIncrementDepth}
                        onChange={(e) => setState(prev => ({
                          ...prev,
                          librarySpecialIncrements: {
                            ...prev.librarySpecialIncrements,
                            MV: { ...prev.librarySpecialIncrements?.MV, depth: parseInt(e.target.value) || 45 }
                          }
                        }))}
                        className="w-full bg-white border-2 border-amber-200 rounded-xl p-3 text-xl font-black text-amber-900 outline-none focus:border-amber-500 text-center"
                      />
                    </div>
                  </div>
                </div>
                
                {/* Corte Viga por biblioteca */}
                <div className="grid grid-cols-2 gap-4">
                  {/* Corte Viga ZC */}
                  <div className="bg-blue-50 rounded-xl p-4">
                    <label className="text-xs font-black text-blue-600 uppercase mb-2 block">🪵 Corte Viga ZC (€)</label>
                    <input
                      type="number"
                      step="0.5"
                      value={state.libraryVigaCutIncrements?.ZC || state.vigaCutIncrement || 0}
                      onChange={(e) => setState(prev => ({ 
                        ...prev, 
                        libraryVigaCutIncrements: {
                          ...prev.libraryVigaCutIncrements,
                          ZC: parseFloat(e.target.value) || 0
                        }
                      }))}
                      className="w-full bg-white border-2 border-blue-300 rounded-xl p-3 text-xl font-black text-blue-800 outline-none focus:border-blue-500 text-center"
                    />
                  </div>
                  {/* Corte Viga MV */}
                  <div className="bg-green-50 rounded-xl p-4">
                    <label className="text-xs font-black text-green-600 uppercase mb-2 block">🪵 Corte Viga MV (€)</label>
                    <input
                      type="number"
                      step="0.5"
                      value={state.libraryVigaCutIncrements?.MV || 0}
                      onChange={(e) => setState(prev => ({ 
                        ...prev, 
                        libraryVigaCutIncrements: {
                          ...prev.libraryVigaCutIncrements,
                          MV: parseFloat(e.target.value) || 0
                        }
                      }))}
                      className="w-full bg-white border-2 border-green-300 rounded-xl p-3 text-xl font-black text-green-800 outline-none focus:border-green-500 text-center"
                    />
                  </div>
                </div>
                
                <p className="text-xs text-slate-500 mt-3 italic">Los incrementos se aplican según la tarifa activa cuando hay corte especial.</p>
                
                {/* Botón Guardar Configuración */}
                <div className="mt-6 flex justify-end">
                  <button
                    onClick={handleSavePricingSettings}
                    disabled={isSavingSettings}
                    className="flex items-center gap-2 px-6 py-3 bg-green-600 text-white rounded-xl font-black uppercase text-sm hover:bg-green-700 transition-all shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isSavingSettings ? (
                      <>
                        <Loader size={18} className="animate-spin" />
                        Guardando...
                      </>
                    ) : (
                      <>
                        <Save size={18} />
                        Guardar Configuración
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Tab Armazones */}
          {activeTab === 'armazones' && (
            <div className="space-y-6">
              {/* Header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-gradient-to-br from-amber-500 to-yellow-500 rounded-xl">
                    <Package size={20} className="text-white" />
                  </div>
                  <div>
                    <h3 className="text-lg font-black text-indigo-950 uppercase">Gestión de Armazones / Cascos</h3>
                    <p className="text-xs text-indigo-400">Configura los materiales de estructura por tarifa</p>
                  </div>
                  {/* Filtro por tarifa */}
                  <div className="flex gap-2">
                    <button
                      onClick={() => setMaterialLibraryFilter('TODAS')}
                      className={`px-3 py-1.5 rounded-lg text-xs font-black uppercase transition-all ${
                        (!materialLibraryFilter || materialLibraryFilter === 'TODAS')
                          ? 'bg-indigo-600 text-white'
                          : 'bg-indigo-100 text-indigo-600 hover:bg-indigo-200'
                      }`}
                    >
                      TODAS
                    </button>
                    <button
                      onClick={() => setMaterialLibraryFilter('ZC')}
                      className={`px-3 py-1.5 rounded-lg text-xs font-black uppercase transition-all ${
                        materialLibraryFilter === 'ZC'
                          ? 'bg-blue-600 text-white'
                          : 'bg-blue-100 text-blue-600 hover:bg-blue-200'
                      }`}
                    >
                      ZC
                    </button>
                    <button
                      onClick={() => setMaterialLibraryFilter('MV')}
                      className={`px-3 py-1.5 rounded-lg text-xs font-black uppercase transition-all ${
                        materialLibraryFilter === 'MV'
                          ? 'bg-amber-600 text-white'
                          : 'bg-amber-100 text-amber-600 hover:bg-amber-200'
                      }`}
                    >
                      MV
                    </button>
                  </div>
                </div>
                {!isEditingMaterial && (
                  <button
                    onClick={handleCreateMaterial}
                    className="flex items-center gap-2 px-4 py-2 bg-amber-600 text-white rounded-xl font-black uppercase text-xs hover:bg-amber-700 transition-all shadow-md"
                  >
                    <Plus size={16} />
                    Nuevo Material
                  </button>
                )}
              </div>

              {!isEditingMaterial ? (
                <div className="grid grid-cols-2 gap-4">
                  {state.carcassMaterials
                    .filter(m => materialLibraryFilter === 'TODAS' || m.library === materialLibraryFilter)
                    .map(material => {
                    const isDefault = material.id === state.selectedCarcassMaterialId;
                    const matLibrary = material.library || 'ZC';
                    return (
                    <div key={material.id} className={`bg-white border-2 ${isDefault ? 'border-emerald-400 shadow-lg shadow-emerald-100' : 'border-amber-200'} rounded-xl p-5 hover:shadow-lg transition-all`}>
                      <div className="flex justify-between items-start mb-3">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <h4 className="text-base font-black text-amber-900">{material.name}</h4>
                            {/* Badge de tarifa */}
                            <span className={`px-2 py-0.5 rounded text-[9px] font-black uppercase ${
                              matLibrary === 'MV' 
                                ? 'bg-amber-100 text-amber-700' 
                                : 'bg-blue-100 text-blue-700'
                            }`}>
                              {matLibrary}
                            </span>
                          </div>
                          {isDefault && (
                            <span className="inline-flex items-center gap-1 mt-1 px-2 py-0.5 bg-emerald-100 text-emerald-700 rounded text-[9px] font-black uppercase">
                              <CheckCircle size={10} /> PREDETERMINADO
                            </span>
                          )}
                        </div>
                        <div className="flex gap-1">
                          {/* Los cascos son FIJOS a su tarifa - no se pueden cambiar */}
                          <button
                            onClick={() => handleEditMaterial(material)}
                            className="p-1.5 hover:bg-amber-100 rounded-lg transition-all"
                            title="Editar"
                          >
                            <Pencil size={14} className="text-amber-600" />
                          </button>
                          <button
                            onClick={() => handleDeleteMaterial(material.id)}
                            className="p-1.5 hover:bg-red-100 rounded-lg transition-all"
                            title="Eliminar"
                          >
                            <Trash2 size={14} className="text-red-600" />
                          </button>
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div className="bg-amber-50 rounded-lg p-3 text-center">
                          <p className="text-[9px] font-black text-amber-400 uppercase">Incremento</p>
                          <p className="text-xl font-black text-orange-600">+{material.fixedIncrement}€</p>
                        </div>
                        <div className="bg-slate-50 rounded-lg p-3 text-center">
                          <p className="text-[9px] font-black text-slate-400 uppercase">Grosor</p>
                          <p className="text-xl font-black text-indigo-600">{material.thickness}mm</p>
                        </div>
                      </div>
                      {!isDefault && (
                        <button
                          onClick={async () => {
                            setState(prev => ({ ...prev, selectedCarcassMaterialId: material.id }));
                            try {
                              await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/settings`, {
                                method: 'PUT',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ defaultCarcassMaterialId: material.id })
                              });
                            } catch (err) {
                              console.error('Error saving default carcass:', err);
                            }
                          }}
                          className="mt-3 w-full flex items-center justify-center gap-2 px-3 py-2 bg-violet-600 hover:bg-violet-700 text-white rounded-lg text-[10px] font-black uppercase transition-all"
                        >
                          <Target size={12} />
                          Establecer como Predeterminado
                        </button>
                      )}
                    </div>
                    );
                  })}
                </div>
              ) : (
                /* Material Form */
                <div className="bg-amber-50 border-2 border-amber-300 rounded-xl p-6 max-w-lg mx-auto">
                  <h4 className="text-sm font-black text-amber-900 uppercase mb-4">
                    {editingMaterialId ? 'Editar Material' : 'Nuevo Material'}
                  </h4>
                  <div className="space-y-4">
                    {/* Selector de Tarifa - Solo al crear */}
                    {!editingMaterialId && (
                      <div>
                        <label className="text-xs font-black text-amber-600 uppercase mb-2 block">Tarifa *</label>
                        <div className="flex gap-2">
                          <button
                            type="button"
                            onClick={() => setMaterialForm({...materialForm, library: 'ZC'})}
                            className={`flex-1 py-3 rounded-xl font-black uppercase text-sm transition-all ${
                              materialForm.library === 'ZC'
                                ? 'bg-blue-600 text-white shadow-lg'
                                : 'bg-blue-100 text-blue-600 hover:bg-blue-200'
                            }`}
                          >
                            ZC
                          </button>
                          <button
                            type="button"
                            onClick={() => setMaterialForm({...materialForm, library: 'MV'})}
                            className={`flex-1 py-3 rounded-xl font-black uppercase text-sm transition-all ${
                              materialForm.library === 'MV'
                                ? 'bg-amber-600 text-white shadow-lg'
                                : 'bg-amber-100 text-amber-600 hover:bg-amber-200'
                            }`}
                          >
                            MV
                          </button>
                        </div>
                        <p className="text-[9px] text-amber-500 mt-1 italic">Una vez creado, no se puede cambiar la tarifa</p>
                      </div>
                    )}
                    {/* Mostrar tarifa actual al editar (no editable) */}
                    {editingMaterialId && (
                      <div className="bg-slate-100 rounded-xl p-3 text-center">
                        <span className="text-xs font-black text-slate-500 uppercase">Tarifa: </span>
                        <span className={`px-3 py-1 rounded-lg text-sm font-black ${
                          materialForm.library === 'MV' ? 'bg-amber-200 text-amber-800' : 'bg-blue-200 text-blue-800'
                        }`}>
                          {materialForm.library || 'ZC'}
                        </span>
                      </div>
                    )}
                    <div>
                      <label className="text-xs font-black text-amber-600 uppercase mb-2 block">Nombre del Material *</label>
                      <input
                        type="text"
                        value={materialForm.name}
                        onChange={(e) => setMaterialForm({...materialForm, name: e.target.value})}
                        placeholder="Ej: Blanco Ártico Standard"
                        className="w-full bg-white border border-amber-200 rounded-xl p-3 text-sm font-bold outline-none focus:border-orange-500"
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-xs font-black text-amber-600 uppercase mb-2 block">Incremento Fijo (€)</label>
                        <input
                          type="number"
                          value={materialForm.fixedIncrement}
                          onChange={(e) => setMaterialForm({...materialForm, fixedIncrement: parseInt(e.target.value) || 0})}
                          className="w-full bg-white border border-amber-200 rounded-xl p-3 text-lg font-black text-center text-orange-600 outline-none focus:border-orange-500"
                        />
                      </div>
                      <div>
                        <label className="text-xs font-black text-amber-600 uppercase mb-2 block">Grosor (mm)</label>
                        <input
                          type="number"
                          value={materialForm.thickness}
                          onChange={(e) => setMaterialForm({...materialForm, thickness: parseInt(e.target.value) || 16})}
                          className="w-full bg-white border border-amber-200 rounded-xl p-3 text-lg font-black text-center text-indigo-600 outline-none focus:border-orange-500"
                        />
                      </div>
                    </div>
                    <div className="flex gap-3 pt-2">
                      <button
                        onClick={handleSaveMaterial}
                        className="flex-1 bg-amber-600 text-white py-3 rounded-xl font-black uppercase text-xs hover:bg-amber-700 transition-all shadow-lg flex items-center justify-center gap-2"
                      >
                        <Check size={18} />
                        Guardar
                      </button>
                      <button
                        onClick={() => setIsEditingMaterial(false)}
                        className="px-6 py-3 bg-slate-200 text-slate-700 rounded-xl font-black uppercase text-xs hover:bg-slate-300 transition-all"
                      >
                        Cancelar
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Info */}
              <div className="bg-slate-50 rounded-xl p-4 text-sm text-slate-600">
                <p className="font-bold text-slate-700 mb-1">¿Qué es el incremento de armazón?</p>
                <p className="text-xs">El incremento fijo se suma al precio de cada mueble para cubrir el coste del material de estructura (casco/armazón). El grosor afecta a los cálculos del despiece.</p>
              </div>
            </div>
          )}

          {/* Tab Backups */}
          {activeTab === 'backups' && (
            <div className="space-y-6">
              {/* Header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-gradient-to-br from-orange-500 to-red-500 rounded-xl">
                    <Database size={20} className="text-white" />
                  </div>
                  <div>
                    <h3 className="text-lg font-black text-indigo-950 uppercase">Copias de Seguridad</h3>
                    <p className="text-xs text-indigo-400">Gestión de backups del sistema</p>
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={loadBackups}
                    disabled={loadingBackups}
                    className="flex items-center gap-2 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs font-bold uppercase transition-colors"
                  >
                    <RefreshCw size={14} className={loadingBackups ? 'animate-spin' : ''} />
                    Actualizar
                  </button>
                  <button
                    onClick={createManualBackup}
                    disabled={creatingBackup}
                    className="flex items-center gap-2 px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-xl text-xs font-bold uppercase transition-colors"
                    data-testid="create-backup-btn"
                  >
                    {creatingBackup ? <Loader size={14} className="animate-spin" /> : <HardDrive size={14} />}
                    Crear Backup Manual
                  </button>
                  <button
                    onClick={handleExportDatabase}
                    disabled={isExportingDB}
                    className="flex items-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold uppercase transition-colors"
                    data-testid="export-database-btn"
                  >
                    {isExportingDB ? <Loader size={14} className="animate-spin" /> : <Download size={14} />}
                    Exportar a Excel
                  </button>
                </div>
              </div>

              {/* Info Box */}
              <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
                <div className="flex items-start gap-3">
                  <AlertTriangle size={18} className="text-amber-600 shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-bold text-amber-800">Sistema de Backups Automáticos</p>
                    <p className="text-xs text-amber-700 mt-1">
                      Los backups automáticos se crean diariamente a las 03:00. También se crean automáticamente antes de activar el modo mantenimiento.
                    </p>
                  </div>
                </div>
              </div>

              {/* Backups Table */}
              <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
                <table className="w-full">
                  <thead className="bg-slate-50 border-b border-slate-200">
                    <tr>
                      <th className="px-4 py-3 text-left text-[10px] font-black text-slate-500 uppercase tracking-wider">Fecha</th>
                      <th className="px-4 py-3 text-left text-[10px] font-black text-slate-500 uppercase tracking-wider">Tipo</th>
                      <th className="px-4 py-3 text-left text-[10px] font-black text-slate-500 uppercase tracking-wider">Creado Por</th>
                      <th className="px-4 py-3 text-left text-[10px] font-black text-slate-500 uppercase tracking-wider">Archivo</th>
                      <th className="px-4 py-3 text-center text-[10px] font-black text-slate-500 uppercase tracking-wider">Acciones</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {loadingBackups ? (
                      <tr>
                        <td colSpan={5} className="p-8 text-center">
                          <Loader size={24} className="animate-spin mx-auto text-indigo-500" />
                        </td>
                      </tr>
                    ) : backups.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="p-8 text-center text-slate-400">
                          <Database size={40} className="mx-auto mb-3 opacity-50" />
                          <p className="font-medium">No hay backups registrados</p>
                        </td>
                      </tr>
                    ) : (
                      backups.slice(0, 20).map(backup => (
                        <tr key={backup.id} className="hover:bg-slate-50">
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-2">
                              <Clock size={14} className="text-slate-400" />
                              <span className="text-sm font-medium text-slate-900">
                                {new Date(backup.createdAt).toLocaleString('es-ES')}
                              </span>
                            </div>
                          </td>
                          <td className="px-4 py-3">
                            <span className={`px-2 py-1 rounded-lg text-xs font-bold ${
                              backup.type === 'manual' ? 'bg-blue-100 text-blue-700' :
                              backup.type === 'auto' ? 'bg-green-100 text-green-700' :
                              'bg-orange-100 text-orange-700'
                            }`}>
                              {backup.type === 'manual' ? 'MANUAL' : 
                               backup.type === 'auto' ? 'AUTOMÁTICO' : 'PRE-UPDATE'}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-sm text-slate-600">{backup.createdBy || 'Sistema'}</td>
                          <td className="px-4 py-3">
                            <span className="text-xs font-mono text-slate-500 truncate block max-w-[200px]">
                              {backup.path?.split('/').pop() || backup.id}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-center">
                            <button
                              onClick={() => {
                                if (window.confirm('¿Restaurar este backup? Se sobrescribirán los datos actuales.')) {
                                  alert('Función de restauración pendiente de implementar');
                                }
                              }}
                              className="p-1.5 text-slate-400 hover:text-orange-600 hover:bg-orange-50 rounded-lg transition-colors"
                              title="Restaurar"
                            >
                              <RefreshCw size={14} />
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>

              {backups.length > 20 && (
                <p className="text-xs text-slate-400 text-center">
                  Mostrando los últimos 20 backups de {backups.length} totales
                </p>
              )}
            </div>
          )}

          {/* Maintenance Tab Content */}
          {activeTab === 'maintenance' && (
            <div className="space-y-6">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-gradient-to-br from-red-500 to-orange-500 rounded-xl">
                  <Wrench size={20} className="text-white" />
                </div>
                <div>
                  <h3 className="text-lg font-black text-indigo-950 uppercase">Modo Mantenimiento</h3>
                  <p className="text-xs text-slate-400">Gestiona el acceso al sistema durante actualizaciones</p>
                </div>
              </div>

              {maintenanceLoading ? (
                <div className="flex items-center justify-center py-12">
                  <Loader size={32} className="animate-spin text-indigo-600" />
                </div>
              ) : (
                <>
                  {/* Current Status */}
                  <div className={`rounded-2xl p-6 ${maintenanceStatus?.active ? 'bg-orange-50 border-2 border-orange-200' : 'bg-green-50 border-2 border-green-200'}`}>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        {maintenanceStatus?.active ? (
                          <div className="w-12 h-12 bg-orange-500 rounded-xl flex items-center justify-center">
                            <Wrench size={24} className="text-white" />
                          </div>
                        ) : (
                          <div className="w-12 h-12 bg-green-500 rounded-xl flex items-center justify-center">
                            <CheckCircle size={24} className="text-white" />
                          </div>
                        )}
                        <div>
                          <h3 className="font-black text-lg text-gray-900">
                            {maintenanceStatus?.active ? 'MODO MANTENIMIENTO ACTIVO' : 'SISTEMA OPERATIVO'}
                          </h3>
                          <p className="text-sm text-gray-600">
                            {maintenanceStatus?.active 
                              ? `Activado por ${maintenanceStatus.activatedBy} el ${new Date(maintenanceStatus.activatedAt).toLocaleString('es-ES')}`
                              : 'El sistema está funcionando con normalidad'
                            }
                          </p>
                        </div>
                      </div>
                      
                      {maintenanceStatus?.active && (
                        <button
                          onClick={handleDeactivateMaintenance}
                          disabled={maintenanceDeactivating}
                          className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-xl font-bold text-sm uppercase tracking-wider flex items-center gap-2 disabled:opacity-50"
                        >
                          {maintenanceDeactivating ? <Loader size={18} className="animate-spin" /> : <Power size={18} />}
                          Reactivar Sistema
                        </button>
                      )}
                    </div>
                    
                    {maintenanceStatus?.active && maintenanceStatus?.preUpdateBackupId && (
                      <div className="mt-4 p-3 bg-white/50 rounded-lg flex items-center gap-2 text-sm">
                        <Shield size={16} className="text-green-600" />
                        <span className="text-gray-700">Backup de seguridad: <strong>{maintenanceStatus.preUpdateBackupId}</strong></span>
                      </div>
                    )}
                  </div>

                  {/* Activate Form - Only show when NOT in maintenance */}
                  {!maintenanceStatus?.active && (
                    <div className="bg-white rounded-2xl border border-indigo-100 p-6">
                      <h3 className="font-black text-lg text-indigo-950 mb-4 flex items-center gap-2">
                        <AlertTriangle size={20} className="text-orange-500" />
                        Activar Modo Mantenimiento
                      </h3>
                      
                      <div className="space-y-4">
                        <div>
                          <label className="block text-xs font-bold text-indigo-400 uppercase tracking-wider mb-1">
                            Mensaje para usuarios
                          </label>
                          <input
                            type="text"
                            value={maintenanceMessage}
                            onChange={(e) => setMaintenanceMessage(e.target.value)}
                            className="w-full border border-indigo-200 rounded-lg px-4 py-2 text-sm focus:border-orange-500 outline-none"
                            placeholder="Sistema en actualización..."
                          />
                        </div>
                        
                        <div>
                          <label className="block text-xs font-bold text-indigo-400 uppercase tracking-wider mb-1">
                            Tiempo estimado (minutos)
                          </label>
                          <input
                            type="number"
                            value={maintenanceMinutes}
                            onChange={(e) => setMaintenanceMinutes(parseInt(e.target.value) || 30)}
                            min="5"
                            max="480"
                            className="w-32 border border-indigo-200 rounded-lg px-4 py-2 text-sm focus:border-orange-500 outline-none"
                          />
                        </div>
                        
                        <label className="flex items-center gap-3 cursor-pointer p-3 bg-indigo-50 rounded-lg">
                          <input
                            type="checkbox"
                            checked={maintenanceCreateBackup}
                            onChange={(e) => setMaintenanceCreateBackup(e.target.checked)}
                            className="w-5 h-5 rounded"
                          />
                          <div>
                            <p className="font-bold text-indigo-900">Crear backup automático</p>
                            <p className="text-xs text-indigo-400">Se guardará una copia de seguridad antes de la actualización</p>
                          </div>
                        </label>
                        
                        <div className="pt-4 border-t border-indigo-100">
                          <button
                            onClick={handleActivateMaintenance}
                            disabled={maintenanceActivating}
                            className="bg-orange-600 hover:bg-orange-700 text-white px-6 py-3 rounded-xl font-bold text-sm uppercase tracking-wider flex items-center gap-2 disabled:opacity-50"
                          >
                            {maintenanceActivating ? <Loader size={18} className="animate-spin" /> : <AlertTriangle size={18} />}
                            {maintenanceActivating ? 'Activando...' : 'Activar Mantenimiento'}
                          </button>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Backup History */}
                  <div className="bg-white rounded-2xl border border-indigo-100 p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="font-black text-lg text-indigo-950 flex items-center gap-2">
                        <Database size={20} />
                        Backups Pre-Actualización
                      </h3>
                      <button
                        onClick={loadMaintenanceBackups}
                        className="p-2 text-indigo-400 hover:text-indigo-600 transition-colors"
                      >
                        <RefreshCw size={18} />
                      </button>
                    </div>
                    
                    {maintenanceBackups.length === 0 ? (
                      <p className="text-center text-indigo-400 py-6">No hay backups pre-actualización</p>
                    ) : (
                      <div className="space-y-2 max-h-60 overflow-y-auto">
                        {maintenanceBackups.map((backup) => (
                          <div key={backup.id} className="flex items-center justify-between p-3 bg-indigo-50 rounded-lg">
                            <div>
                              <p className="font-bold text-indigo-900 text-sm">{backup.id}</p>
                              <p className="text-xs text-indigo-400">
                                {new Date(backup.createdAt).toLocaleString('es-ES')} · Por: {backup.createdBy}
                              </p>
                            </div>
                            <button
                              onClick={() => handleDownloadMaintenanceBackup(backup.id)}
                              className="p-2 text-indigo-600 hover:bg-indigo-100 rounded-lg transition-colors"
                              title="Descargar backup"
                            >
                              <Download size={18} />
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </>
              )}
            </div>
          )}

          {activeTab === 'telemetry' && (
            <div className="flex gap-6 h-[500px]">
              <div className="flex-1 flex flex-col">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-2 bg-gradient-to-br from-orange-500 to-yellow-500 rounded-xl">
                    <Zap size={20} className="text-white" />
                  </div>
                  <div>
                    <h3 className="text-lg font-black text-indigo-950 uppercase">Telemetría IA</h3>
                    <p className="text-xs text-indigo-400">Sincronización por Reconocimiento Óptico</p>
                  </div>
                </div>

                <div className="flex gap-2 mb-4">
                  {['montada', 'despiece'].map(mod => (
                    <button key={mod} onClick={() => setTelemetryModule(mod)} disabled={isProcessingTelemetry}
                      className={`flex-1 p-3 rounded-xl transition-all border-2 ${telemetryModule === mod ? (mod === 'montada' ? 'bg-orange-500 border-orange-400' : 'bg-indigo-500 border-indigo-400') + ' text-white' : 'bg-slate-50 border-slate-200 text-slate-600'}`}>
                      <span className="font-black text-sm uppercase">{mod}</span>
                    </button>
                  ))}
                </div>

                <div className="bg-slate-50 rounded-xl p-4 flex-1 flex flex-col border border-slate-200">
                  <label className="flex-1 flex flex-col items-center justify-center border-2 border-dashed border-slate-300 rounded-xl p-4 cursor-pointer hover:border-orange-400 hover:bg-orange-50 transition-all min-h-[120px]">
                    <FileImage size={36} className="text-slate-400 mb-2" />
                    <p className="text-sm font-black text-slate-700 uppercase">Cargar fichas</p>
                    <p className="text-xs text-slate-500">JPG, PNG, PDF</p>
                    <input type="file" multiple accept="image/*,application/pdf" className="hidden" disabled={isProcessingTelemetry}
                      onChange={(e) => {
                        const files = Array.from(e.target.files);
                        setTelemetryFiles(prev => [...prev, ...files.map(f => ({ id: Math.random().toString(36).slice(2), file: f, name: f.name, preview: URL.createObjectURL(f) }))]);
                      }} />
                  </label>

                  {telemetryFiles.length > 0 && (
                    <div className="mt-3 space-y-2">
                      <div className="max-h-[80px] overflow-y-auto space-y-1">
                        {telemetryFiles.map(f => (
                          <div key={f.id} className="bg-white border border-slate-200 rounded-lg p-2 flex items-center justify-between">
                            <span className="text-xs font-bold text-slate-700 truncate flex-1">{f.name}</span>
                            <button onClick={() => setTelemetryFiles(prev => prev.filter(x => x.id !== f.id))} className="p-1 hover:bg-red-100 rounded">
                              <XCircle size={14} className="text-red-500" />
                            </button>
                          </div>
                        ))}
                      </div>
                      <button disabled={isProcessingTelemetry} className="w-full bg-gradient-to-r from-orange-500 to-orange-600 text-white py-3 rounded-xl font-black uppercase text-xs flex items-center justify-center gap-2 disabled:opacity-50"
                        onClick={async () => {
                          setIsProcessingTelemetry(true); setTelemetryResult(null); setTelemetryLog([]);
                          const addLog = (e) => setTelemetryLog(p => [...p, { ...e, time: new Date().toLocaleTimeString() }]);
                          addLog({ type: 'info', msg: `Iniciando ${telemetryFiles.length} archivo(s)...` });
                          try {
                            const formData = new FormData();
                            formData.append('module', telemetryModule);
                            telemetryFiles.forEach(f => formData.append('files', f.file));
                            const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/analyze-product-sheets`, { method: 'POST', body: formData });
                            const result = await res.json();
                            if (result.success && result.products) {
                              // Show detected categories
                              if (result.detectedCategories && result.detectedCategories.length > 0) {
                                addLog({ type: 'info', msg: `📁 Categorías: ${result.detectedCategories.join(', ')}` });
                              }
                              addLog({ type: 'info', msg: `IA detectó ${result.products.length} producto(s)` });
                              const newP = [], dupP = [];
                              for (let i = 0; i < result.products.length; i++) {
                                const p = result.products[i];
                                setTelemetryProgress({ current: i + 1, total: result.products.length });
                                await new Promise(r => setTimeout(r, 80));
                                if (existingCodes.has(p.code)) { dupP.push(p); addLog({ type: 'dup', code: p.code, name: p.name, pts: p.points || 0 }); }
                                else { newP.push(p); addLog({ type: 'new', code: p.code, name: p.name, pts: p.points || 0 }); setExistingCodes(prev => new Set([...prev, p.code])); }
                              }
                              if (newP.length > 0) { 
                                try {
                                  const bulkResult = await productsAPI.bulkCreate(newP);
                                  if (bulkResult.errors && bulkResult.errors.length > 0) {
                                    addLog({ type: 'err', msg: `${bulkResult.errors.length} error(es)` });
                                  }
                                  addLog({ type: 'ok', msg: `${bulkResult.created || newP.length} guardado(s)` });
                                } catch (bulkErr) {
                                  addLog({ type: 'err', msg: `Error al crear: ${bulkErr.message}` });
                                }
                              }
                              setTelemetryResult({ ok: true, newC: newP.length, dupC: dupP.length });
                            } else { addLog({ type: 'err', msg: result.error || 'Error' }); }
                            setTelemetryFiles([]);
                          } catch (e) { addLog({ type: 'err', msg: e.message }); }
                          setIsProcessingTelemetry(false);
                        }}>
                        {isProcessingTelemetry ? <><Loader size={16} className="animate-spin" /> Procesando...</> : <><Zap size={16} /> Digitalizar</>}
                      </button>
                    </div>
                  )}
                  {telemetryResult?.ok && (
                    <div className="mt-3 bg-green-50 border border-green-200 rounded-xl p-3">
                      <div className="flex items-center gap-2"><CheckCircle size={16} className="text-green-600" /><span className="font-black text-green-800 text-sm">Completado</span></div>
                      <p className="text-xs text-green-700 mt-1">{telemetryResult.newC} nuevo(s) • {telemetryResult.dupC} duplicado(s)</p>
                      <button onClick={() => { setTelemetryResult(null); setTelemetryLog([]); }} className="mt-2 w-full bg-indigo-900 text-white py-2 rounded-lg font-bold text-xs flex items-center justify-center gap-2"><RefreshCw size={14} /> Nueva</button>
                    </div>
                  )}
                </div>
              </div>

              <div className="w-[280px] bg-indigo-950 rounded-2xl flex flex-col overflow-hidden">
                <div className="p-3 border-b border-indigo-800 flex items-center gap-2">
                  <Zap size={14} className="text-orange-500" />
                  <span className="text-xs font-black text-white uppercase">Log: {telemetryModule}</span>
                </div>
                {isProcessingTelemetry && telemetryProgress.total > 0 && (
                  <div className="px-3 py-2 bg-indigo-900/50">
                    <div className="h-1 bg-indigo-800 rounded-full overflow-hidden">
                      <div className="h-full bg-orange-500 transition-all" style={{ width: `${(telemetryProgress.current / telemetryProgress.total) * 100}%` }} />
                    </div>
                  </div>
                )}
                <div className="flex-1 overflow-y-auto p-3 space-y-1 text-xs">
                  {telemetryLog.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center"><Zap size={20} className="text-indigo-700 mb-2" /><p className="text-indigo-500">Sin actividad</p></div>
                  ) : telemetryLog.map((e, i) => (
                    e.type === 'new' || e.type === 'dup' ? (
                      <div key={i} className="flex items-center gap-2 py-1 px-2 rounded bg-white/5">
                        <span className={`px-1.5 py-0.5 rounded text-[9px] font-black ${e.type === 'new' ? 'bg-green-500' : 'bg-orange-500'} text-white`}>{e.type === 'new' ? 'NUEVO' : 'DUP'}</span>
                        <span className="text-white/80 truncate flex-1">{e.code}</span>
                        <span className={e.type === 'new' ? 'text-green-400' : 'text-orange-400'}>{e.pts}</span>
                      </div>
                    ) : <div key={i} className={`${e.type === 'err' ? 'text-red-400' : e.type === 'ok' ? 'text-green-400' : 'text-white/60'}`}>[{e.time}] {e.msg}</div>
                  ))}
                </div>
                <div className="p-2 border-t border-indigo-800 flex justify-center gap-3 text-[9px]">
                  <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-green-500"></span> Nuevo</span>
                  <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-orange-500"></span> Duplicado</span>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'identity' && (
            <div className="space-y-6">
              <div className="bg-white border border-purple-100 rounded-2xl p-6 shadow-sm">
                <h3 className="text-sm font-black text-indigo-900 uppercase tracking-widest mb-4">Color de Marca</h3>
                <div className="flex gap-4 items-end">
                  <div className="flex-1">
                    <label className="text-xs font-black text-indigo-400 uppercase mb-2 block">Color Hexadecimal</label>
                    <input
                      type="text"
                      value={colorInput}
                      onChange={(e) => setColorInput(e.target.value)}
                      placeholder="#ea580c"
                      className="w-full bg-indigo-50 border border-indigo-100 rounded-xl p-3 text-lg font-black text-indigo-900 outline-none focus:border-orange-500"
                    />
                  </div>
                  <div 
                    className="w-24 h-12 rounded-xl border-4 border-white shadow-lg"
                    style={{ backgroundColor: colorInput }}
                  ></div>
                  <button
                    onClick={handleColorChange}
                    className="px-6 py-3 bg-indigo-600 text-white rounded-xl font-black uppercase text-xs hover:bg-indigo-700 transition-all"
                  >
                    Aplicar
                  </button>
                </div>
              </div>

              <div className="bg-white border border-purple-100 rounded-2xl p-6 shadow-sm">
                <h3 className="text-sm font-black text-indigo-900 uppercase tracking-widest mb-4">Logo Corporativo</h3>
                <div className="space-y-4">
                  {state.logo && (
                    <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between">
                      <img src={state.logo} alt="Logo" className="h-16 object-contain" />
                      <button
                        onClick={() => setState(prev => ({ ...prev, logo: null }))}
                        className="px-4 py-2 bg-red-100 text-red-600 rounded-lg text-xs font-black uppercase hover:bg-red-200 transition-all"
                      >
                        Eliminar
                      </button>
                    </div>
                  )}
                  <label className="block">
                    <div className="border-2 border-dashed border-indigo-200 rounded-xl p-8 text-center cursor-pointer hover:border-indigo-400 hover:bg-indigo-50 transition-all">
                      <Camera size={32} className="mx-auto text-indigo-300 mb-2" />
                      <p className="text-sm font-black text-indigo-900 uppercase">Subir Logo</p>
                      <p className="text-xs text-indigo-400 mt-1">PNG, JPG, SVG</p>
                    </div>
                    <input type="file" accept="image/*" onChange={handleLogoUpload} className="hidden" />
                  </label>
                </div>
              </div>
            </div>
          )}

          {/* SECURITY 2FA TAB */}
          {activeTab === 'security' && (
            <div className="space-y-6">
              <div className="flex items-center gap-4 mb-6">
                <div className="p-4 bg-emerald-100 rounded-2xl">
                  <Shield size={32} className="text-emerald-600" />
                </div>
                <div>
                  <h3 className="text-2xl font-black text-slate-800 uppercase tracking-wider">Seguridad 2FA</h3>
                  <p className="text-slate-500">Gestiona la autenticación de dos factores para tu cuenta</p>
                </div>
              </div>

              {/* Estado actual del 2FA */}
              <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                <div className="bg-gradient-to-r from-slate-800 to-slate-900 text-white px-6 py-4">
                  <h4 className="font-black uppercase tracking-wider">Estado de 2FA</h4>
                </div>
                <div className="p-6">
                  <div className="flex items-center justify-between p-4 bg-slate-50 rounded-xl">
                    <div className="flex items-center gap-4">
                      <div className={`p-3 rounded-xl ${state.currentUser?.has2FAEnabled ? 'bg-emerald-100' : 'bg-amber-100'}`}>
                        <Shield size={24} className={state.currentUser?.has2FAEnabled ? 'text-emerald-600' : 'text-amber-600'} />
                      </div>
                      <div>
                        <p className="font-bold text-slate-800">
                          {state.currentUser?.has2FAEnabled ? 'Autenticación 2FA Activada' : 'Autenticación 2FA Desactivada'}
                        </p>
                        <p className="text-sm text-slate-500">
                          {state.currentUser?.has2FAEnabled 
                            ? 'Tu cuenta está protegida con autenticación de dos factores' 
                            : 'Activa 2FA para mayor seguridad en tu cuenta'}
                        </p>
                      </div>
                    </div>
                    <div className={`px-4 py-2 rounded-lg font-bold uppercase text-sm ${
                      state.currentUser?.has2FAEnabled 
                        ? 'bg-emerald-100 text-emerald-700' 
                        : 'bg-amber-100 text-amber-700'
                    }`}>
                      {state.currentUser?.has2FAEnabled ? '✅ Activo' : '⚠️ Inactivo'}
                    </div>
                  </div>
                </div>
              </div>

              {/* Acciones 2FA */}
              <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
                <div className="bg-gradient-to-r from-emerald-600 to-emerald-700 text-white px-6 py-4">
                  <h4 className="font-black uppercase tracking-wider">Acciones</h4>
                </div>
                <div className="p-6 space-y-4">
                  {!state.currentUser?.has2FAEnabled ? (
                    <>
                      <div className="bg-emerald-50 rounded-xl p-4 border border-emerald-200">
                        <h5 className="font-bold text-emerald-800 mb-2">Activar Autenticación 2FA</h5>
                        <p className="text-sm text-emerald-600 mb-4">
                          Añade una capa extra de seguridad a tu cuenta. Necesitarás una app autenticadora como Google Authenticator o Authy.
                        </p>
                        <button
                          onClick={() => {
                            // Abrir el modal de TwoFactorSetup
                            setState(prev => ({ ...prev, show2FASetup: true }));
                          }}
                          className="bg-emerald-600 text-white px-6 py-3 rounded-xl font-bold uppercase text-sm hover:bg-emerald-700 transition-colors flex items-center gap-2"
                          data-testid="enable-2fa-btn"
                        >
                          <Shield size={18} />
                          Configurar 2FA
                        </button>
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="bg-slate-50 rounded-xl p-4 border border-slate-200">
                        <h5 className="font-bold text-slate-800 mb-2">Desactivar 2FA</h5>
                        <p className="text-sm text-slate-600 mb-4">
                          ⚠️ No recomendado. Si desactivas 2FA, tu cuenta será menos segura.
                        </p>
                        <button
                          onClick={async () => {
                            if (window.confirm('¿Estás seguro de que quieres desactivar la autenticación 2FA? Tu cuenta será menos segura.')) {
                              try {
                                const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/auth-advanced/2fa/disable-simple`, {
                                  method: 'POST',
                                  headers: {
                                    'Content-Type': 'application/json',
                                    'Authorization': `Bearer ${state.token}`
                                  },
                                  body: JSON.stringify({ userId: state.currentUser?.id })
                                });
                                const data = await response.json();
                                if (data.success) {
                                  setState(prev => ({ 
                                    ...prev, 
                                    currentUser: { ...prev.currentUser, has2FAEnabled: false }
                                  }));
                                  alert('2FA desactivado correctamente');
                                } else {
                                  alert(data.detail || 'Error al desactivar 2FA');
                                }
                              } catch (err) {
                                alert('Error de conexión');
                              }
                            }
                          }}
                          className="bg-red-100 text-red-700 px-6 py-3 rounded-xl font-bold uppercase text-sm hover:bg-red-200 transition-colors flex items-center gap-2"
                          data-testid="disable-2fa-btn"
                        >
                          <XCircle size={18} />
                          Desactivar 2FA
                        </button>
                      </div>

                      <div className="bg-amber-50 rounded-xl p-4 border border-amber-200">
                        <h5 className="font-bold text-amber-800 mb-2">Regenerar Códigos de Respaldo</h5>
                        <p className="text-sm text-amber-600 mb-4">
                          Genera nuevos códigos de respaldo si has perdido los anteriores o los has usado todos.
                        </p>
                        <button
                          onClick={async () => {
                            if (window.confirm('¿Generar nuevos códigos de respaldo? Los códigos anteriores quedarán invalidados.')) {
                              try {
                                const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/auth-advanced/2fa/regenerate-backup`, {
                                  method: 'POST',
                                  headers: {
                                    'Content-Type': 'application/json',
                                    'Authorization': `Bearer ${state.token}`
                                  },
                                  body: JSON.stringify({ userId: state.currentUser?.id })
                                });
                                const data = await response.json();
                                if (data.success && data.backupCodes) {
                                  alert('Nuevos códigos de respaldo:\n\n' + data.backupCodes.join('\n') + '\n\nGuárdalos en un lugar seguro.');
                                } else {
                                  alert(data.detail || 'Error al regenerar códigos');
                                }
                              } catch (err) {
                                alert('Error de conexión');
                              }
                            }
                          }}
                          className="bg-amber-600 text-white px-6 py-3 rounded-xl font-bold uppercase text-sm hover:bg-amber-700 transition-colors flex items-center gap-2"
                          data-testid="regenerate-backup-btn"
                        >
                          <RefreshCw size={18} />
                          Regenerar Códigos
                        </button>
                      </div>
                    </>
                  )}
                </div>
              </div>

              {/* Información adicional */}
              <div className="bg-blue-50 rounded-xl p-6 border border-blue-200">
                <h5 className="font-bold text-blue-800 mb-3 flex items-center gap-2">
                  <AlertTriangle size={18} />
                  Información Importante
                </h5>
                <ul className="text-sm text-blue-700 space-y-2">
                  <li>• La autenticación 2FA añade una capa extra de seguridad a tu cuenta.</li>
                  <li>• Necesitarás tu teléfono cada vez que inicies sesión.</li>
                  <li>• Guarda los códigos de respaldo en un lugar seguro (no en el móvil).</li>
                  <li>• Si pierdes acceso a tu autenticador, usa un código de respaldo para entrar.</li>
                </ul>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SettingsModal;
