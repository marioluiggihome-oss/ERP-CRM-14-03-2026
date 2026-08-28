/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
import React, { useState, useMemo, useEffect } from 'react';
import { COOPERATIVA as PLATAFORMA_COOPERATIVA, TODAS as PLATAFORMAS, NOMBRES as NOMBRES_PLATAFORMA } from '@/plataformas';
import { X, Users, Euro, Palette, Camera, Settings as SettingsIcon, Plus, Pencil, Trash2, Check, UserPlus, Shield, Store, Briefcase, Search, Package, Save, CheckSquare, Square, Loader, Zap, Upload, FileImage, XCircle, RefreshCw, CheckCircle, Building2, FileSpreadsheet, Download, HardDrive, Database, Clock, AlertTriangle, Wrench, Power, ShieldAlert, Timer, Maximize2, Minimize2, Target, Award, TrendingUp, BarChart3, FolderOpen, FileText, ChevronDown, ChevronUp, UserCheck, Layers, Factory, Percent, Eye } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, PieChart as RechartsPie, Pie, Cell, Legend } from 'recharts';
import { usersAPI, productsAPI, materialsAPI, settingsAPI, clientsAPI, librariesAPI, authHeaders } from '../services/api';
import CatalogImporter from './CatalogImporter';

// Componentes refactorizados
import { TelemetryTab, TelemetryAuditTab, DigitalizadorAuditTab, IdentityTab, SecurityTab, DashboardTab, UsageReportTab, BackupManagementTab, DirectorTab, ShopClientsTab, PricingTab, BackupsTab, MaintenanceTab, InventoryTab, ArmazonesTab, SubscriptionTab, CostesArticulosTab, AIMeterTab } from './settings';

// Tipos de mueble del Estudio 3D (permisos por partidas). Compartido con AIRenderStudio.
const ESTUDIO_3D_TIPOS = [
  { id: 'cocina', label: 'Cocina' },
  { id: 'armario', label: 'Armario / Vestidor' },
  { id: 'bano', label: 'Baño' },
  { id: 'otro', label: 'Otro mueble' },
];

// Capacidades técnicas (checkboxes del panel de permisos) para los botones
// "Marcar todo / Desmarcar todo". Solo capacidades, NO roles ni modos "solo".
const CAPABILITY_KEYS = [
  'canUsePresupuestador2', 'canUsePresupuestador1', 'canSeeCost', 'canViewTechnicalDespiece',
  'canAccessCRM', 'canAccessGastos', 'canAccessFabrica', 'canAccessMontajes', 'isMontador',
  'canManageArticles', 'canAccessFloor', 'canUseAIAnalysis', 'canUseKitchenDesigner', 'canUseDigitalizador',
  'canAccessMaster', 'canAuthorizePermissions', 'canChangeLogo', 'canAccessArmarios',
  'canAccessPedidos', 'canAccessArchivo', 'canAccessInvoices', 'canAccessRentabilidad', 'canAccessMando', 'isController',
  'canUseResumenTotales', 'canUseCascos', 'canVerVinculadosCascos', 'canUsePropData', 'canUseArmarios2', 'canUseCocinasAI', 'canUseAgentesIA',
  'canUseRender360', 'canUse4K', 'canUseAmueblado', 'canVolcarMV',
];

// Lista de provincias de España con sus códigos
const PROVINCIAS_ESPANA = [
  { codigo: 'AL', nombre: 'Almería' },
  { codigo: 'CA', nombre: 'Cádiz' },
  { codigo: 'CO', nombre: 'Córdoba' },
  { codigo: 'GR', nombre: 'Granada' },
  { codigo: 'HU', nombre: 'Huelva' },
  { codigo: 'JA', nombre: 'Jaén' },
  { codigo: 'MA', nombre: 'Málaga' },
  { codigo: 'SE', nombre: 'Sevilla' },
  { codigo: 'HU', nombre: 'Huesca' },
  { codigo: 'TE', nombre: 'Teruel' },
  { codigo: 'ZA', nombre: 'Zaragoza' },
  { codigo: 'OV', nombre: 'Asturias' },
  { codigo: 'IB', nombre: 'Islas Baleares' },
  { codigo: 'LP', nombre: 'Las Palmas' },
  { codigo: 'TF', nombre: 'Santa Cruz de Tenerife' },
  { codigo: 'SA', nombre: 'Cantabria' },
  { codigo: 'AB', nombre: 'Albacete' },
  { codigo: 'CR', nombre: 'Ciudad Real' },
  { codigo: 'CU', nombre: 'Cuenca' },
  { codigo: 'GU', nombre: 'Guadalajara' },
  { codigo: 'TO', nombre: 'Toledo' },
  { codigo: 'AV', nombre: 'Ávila' },
  { codigo: 'BU', nombre: 'Burgos' },
  { codigo: 'LE', nombre: 'León' },
  { codigo: 'PA', nombre: 'Palencia' },
  { codigo: 'SM', nombre: 'Salamanca' },
  { codigo: 'SG', nombre: 'Segovia' },
  { codigo: 'SO', nombre: 'Soria' },
  { codigo: 'VA', nombre: 'Valladolid' },
  { codigo: 'ZM', nombre: 'Zamora' },
  { codigo: 'BA', nombre: 'Barcelona' },
  { codigo: 'GI', nombre: 'Girona' },
  { codigo: 'LL', nombre: 'Lleida' },
  { codigo: 'TA', nombre: 'Tarragona' },
  { codigo: 'BA', nombre: 'Badajoz' },
  { codigo: 'CC', nombre: 'Cáceres' },
  { codigo: 'CO', nombre: 'A Coruña' },
  { codigo: 'LU', nombre: 'Lugo' },
  { codigo: 'OR', nombre: 'Ourense' },
  { codigo: 'PO', nombre: 'Pontevedra' },
  { codigo: 'LO', nombre: 'La Rioja' },
  { codigo: 'MD', nombre: 'Madrid' },
  { codigo: 'MU', nombre: 'Murcia' },
  { codigo: 'NA', nombre: 'Navarra' },
  { codigo: 'AL', nombre: 'Álava' },
  { codigo: 'BI', nombre: 'Bizkaia' },
  { codigo: 'SS', nombre: 'Gipuzkoa' },
  { codigo: 'AL', nombre: 'Alicante' },
  { codigo: 'CS', nombre: 'Castellón' },
  { codigo: 'VL', nombre: 'Valencia' },
  { codigo: 'CE', nombre: 'Ceuta' },
  { codigo: 'ML', nombre: 'Melilla' }
].sort((a, b) => a.nombre.localeCompare(b.nombre));

const SettingsModal = ({ isOpen, onClose, state, setState }) => {
  const [activeTab, setActiveTab] = useState('users');
  const [colorInput, setColorInput] = useState(state.brandColor || '#c0795f');
  const [userSearch, setUserSearch] = useState('');
  const [isEditingUser, setIsEditingUser] = useState(false);
  const [editingUserId, setEditingUserId] = useState(null);
  const [isSaving, setIsSaving] = useState(false);
  // Fichas de la agenda de montajes, para vincularlas con la cuenta.
  const [fichasMontador, setFichasMontador] = useState([]);
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
    manufacturer: 'Master',
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
    backThickness: 8,  // Grosor de trasera por defecto
    library: 'ZC'
  });
  const [userForm, setUserForm] = useState({
    username: '',
    password: '',
    clientName: '',
    linkedClientCodigo: '',  // Código de cliente del CRM (relaciona usuario↔cliente)
    provinciaCode: '',  // Código de provincia (2 letras: AV, LE, SA, etc.)
    accessExpirationDate: '',  // Fecha de caducidad del acceso
    isActive: true,
    isAdmin: false,  // Director Comercial
    isGerente: false,  // Gerente - mismo acceso que Director
    isDirectorComercial: false,  // Director Comercial (ve todo el CRM)
    isDirectorFabrica: false,  // Director de Fábrica (ve Dashboard Fábrica y gestiona producción)
    isResponsableDelegacion: false,  // Responsable Delegación
    isRepresentative: false,
    isPrescriptor: false,
    isTienda: false,  // Tienda/Punto de Venta
    isMontador: false,  // Montador/Instalador
    plataforma: PLATAFORMA_COOPERATIVA,  // cooperativa | carpinter | studio3k
    esCooperativistaComercial: false,  // socio: cobra por tramos
    esCooperativistaMontador: false,   // socio: cobra mano de obra
    manoObraPorMueble: null,           // su € por mueble; null = la de la casa
    isCarpintero: false,  // Carpintero/Ebanista (portal con landing propia)
    canManageCarpinteroUsers: false,  // Admin de división: crea sus propios usuarios
    carpinteroLandingUrl: '',  // URL de la web de inicio del portal carpinteros
    linkedRepresentativeId: '',
    allowedModules: ['montada'],
    allowedLibraries: ['ZC'],  // Tarifas/Bibliotecas activas (ZC, MV, etc.)
    commercialDiscount: 0,
    discountMontada: 0,
    discountDespiece: 0,
    discountDesmontada: 0,
    canSeeCost: false,
    canSeeRetail: true,
    canUseAIAnalysis: false,
    canUseKitchenDesigner: false,
    canManageArticles: false,
    canViewTechnicalDespiece: false,
    canAccessCRM: false,
    canUseResumenTotales: false,
    canUseCascos: false,
    canUseRender360: false,
    canUse4K: false,
    canUseAmueblado: false,
    canVolcarMV: false,
    canVerVinculadosCascos: false,
    canUsePropData: false,
    canUseArmarios2: false,
    canUseCocinasAI: false,
    canUseDigitalizador: false,
    canAccessArmarios: false,
    canAccessFabrica: false,  // Acceso a Portal de Fábrica
    canAccessMontajes: false,  // Acceso a Agenda de Montajes
    canUsePresupuestador1: true,  // Acceso al Presupuestador 2 (el anterior; por defecto sí)
    canUsePresupuestador2: true,  // Acceso al Presupuestador (MV, principal; por defecto sí)
    canAccessMaster: true,  // Acceso al Panel MASTER (config) - visible por defecto
    canAccessGastos: true,  // Acceso al módulo de Gastos - visible por defecto
    canAccessFloor: false,  // Luiggi Floor - opt-in por usuario (red de distribución)
    canUseAgentesIA: false,  // Agentes IA - diseño en paralelo con IA
    floorOnly: false,  // Usuario SOLO Luiggi Floor (entra directo, sin otros presupuestadores)
    crmOnly: false,    // Usuario SOLO CRM (entra directo, sin barra de navegación)
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
  const [telemetryLibrary, setTelemetryLibrary] = useState(() => {
    // Recuperar biblioteca guardada en localStorage o usar ZC por defecto
    const saved = localStorage.getItem('telemetryLibrary');
    return saved === 'MV' ? 'MV' : 'ZC';
  });
  const [telemetryTariff, setTelemetryTariff] = useState(() => {
    // Para MV: T1-T21, Para ZC: Z1-Z12
    const saved = localStorage.getItem('telemetryTariff');
    return saved || 'T1';
  });

  // Dashboard states
  const [dashboardMetrics, setDashboardMetrics] = useState(null);
  const [dashboardPeriod, setDashboardPeriod] = useState('month');
  const [dashboardLoading, setDashboardLoading] = useState(false);

  // Client states
  const [clients, setClients] = useState([]);
  const [showClientCodeList, setShowClientCodeList] = useState(false);
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

  // Settings saving state
  const [isSavingProduct, setIsSavingProduct] = useState(false);

  // Billing tab states
  const [billingForm, setBillingForm] = useState({});
  const [savingBilling, setSavingBilling] = useState(false);
  const [billingMsg, setBillingMsg] = useState('');

  useEffect(() => {
    if (state.settings) {
      setBillingForm({
        companyName: state.settings.companyName || '',
        companyTaxId: state.settings.companyTaxId || '',
        companyAddress: state.settings.companyAddress || '',
        companyPhone: state.settings.companyPhone || '',
        companyEmail: state.settings.companyEmail || '',
        companyIban: state.settings.companyIban || '',
        centrosEnvio: state.settings.centrosEnvio || '',
        emailSender: state.settings.emailSender || '',
        sendgridApiKey: ''
      });
    }
  }, [state.settings, activeTab]);

  const handleSaveBilling = async () => {
    setSavingBilling(true);
    setBillingMsg('');
    try {
      const patch = { ...billingForm };
      if (!patch.sendgridApiKey) delete patch.sendgridApiKey;
      await saveSetting(patch);
      if (billingForm.sendgridApiKey) {
        await settingsAPI.update({ sendgridApiKey: billingForm.sendgridApiKey });
      }
      setBillingMsg('✓ ¡Datos de facturación guardados con éxito!');
      setTimeout(() => setBillingMsg(''), 4000);
    } catch (e) {
      alert('Error al guardar datos de facturación');
    } finally {
      setSavingBilling(false);
    }
  };

  // Guarda un ajuste global y refresca el estado local (para que otras vistas,
  // p.ej. Cocina Desmontada, vean el cambio sin recargar). Se usa en onBlur.
  const saveSetting = async (patch) => {
    try {
      await settingsAPI.update(patch);
      setState(prev => ({ ...prev, settings: { ...(prev.settings || {}), ...patch } }));
    } catch (err) { console.error('Error guardando ajuste:', err); alert('No se pudo guardar el ajuste.'); }
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

  const handleBackfillClients = async () => {
    if (!window.confirm('¿Asignar TODOS los clientes sin dueño al usuario MARIO? (datos antiguos, una sola vez)')) return;
    try {
      const res = await clientsAPI.backfillOwner('MARIO');
      alert(`Listo: ${res.asignados} cliente(s) asignados a ${res.usuario}.`);
      loadClients();
    } catch (e) { alert('Error: ' + e.message); }
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
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/backup/status`, { headers: authHeaders() });
      const data = await response.json();
      const list = Array.isArray(data?.existing_backups) ? data.existing_backups : [];
      setBackups(list.map(b => ({
        id: b.filename,
        path: b.filename,
        createdAt: b.created,
        type: (b.filename || '').includes('pre_update') ? 'pre_update' : 'manual',
        createdBy: 'Sistema',
        size_mb: b.size_mb,
      })));
    } catch (err) {
      console.error('Error loading backups:', err);
      setBackups([]);
    } finally {
      setLoadingBackups(false);
    }
  };

  // Load Director Panel data when tab is active
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
        headers: authHeaders({ 'Content-Type': 'application/json' }),
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
        method: 'POST',
        headers: authHeaders()
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
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/maintenance/backups/${backupId}/download`, { headers: authHeaders() });
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
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/backup/create`, {
        method: 'POST',
        headers: authHeaders({ 'Content-Type': 'application/json' }),
      });
      if (response.ok) {
        await loadBackups();
        alert('✅ Backup creado correctamente (código + base de datos)');
      } else {
        const e = await response.json().catch(() => ({}));
        throw new Error(e.detail || 'Error al crear backup');
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
      const token = localStorage.getItem('token');
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
      a.download = `Export_${new Date().toISOString().split('T')[0]}.xlsx`;
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

  // Cargar métricas del dashboard
  useEffect(() => {
    if (!isOpen || activeTab !== 'dashboard') return;
    const loadDashboardMetrics = async () => {
      setDashboardLoading(true);
      try {
        const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/dashboard/metrics?period=${dashboardPeriod}`);
        const data = await res.json();
        setDashboardMetrics(data);
      } catch (err) {
        console.error('Error loading dashboard metrics:', err);
      } finally {
        setDashboardLoading(false);
      }
    };
    loadDashboardMetrics();
  }, [isOpen, activeTab, dashboardPeriod]);

  // Lista de usuarios que pueden tener tiendas asignadas (Director, Gerente, Responsable, Comercial)
  const representatives = useMemo(() => state.users.filter(u => u.isAdmin || u.isGerente || u.isDirectorComercial || u.isResponsableDelegacion || u.isRepresentative), [state.users]);

  // Filtrar usuarios según el rol del usuario actual
  const visibleUsers = useMemo(() => {
    if (state.currentUser?.isAdmin || state.currentUser?.isGerente || state.currentUser?.isDirectorComercial) {
      // Director Comercial / Gerente ve todos los usuarios
      return state.users;
    } else if (state.currentUser?.canManageCarpinteroUsers && !state.currentUser?.isAdmin) {
      // Admin de división Carpintero: solo ve sus propios usuarios vinculados + a sí mismo
      return state.users.filter(u =>
        u.id === state.currentUser.id ||
        u.linkedCarpinteroAdminId === state.currentUser.id
      );
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
      const matchesSearch = (u.username || '').toLowerCase().includes(query) ||
        (u.clientName || '').toLowerCase().includes(query);
      
      // Filtro por rol
      if (userRoleFilter === 'all') return matchesSearch;
      if (userRoleFilter === 'director' && u.isAdmin) return matchesSearch;
      if (userRoleFilter === 'gerente' && u.isGerente) return matchesSearch;
      if (userRoleFilter === 'responsable' && u.isResponsableDelegacion) return matchesSearch;
      if (userRoleFilter === 'comercial' && u.isRepresentative && !u.isAdmin && !u.isGerente && !u.isResponsableDelegacion) return matchesSearch;
      if (userRoleFilter === 'tienda' && u.isTienda && !u.isCarpintero) return matchesSearch;
      if (userRoleFilter === 'colaborador' && u.isPrescriptor) return matchesSearch;
      if (userRoleFilter === 'carpintero' && u.isCarpintero) return matchesSearch;
      if (userRoleFilter === 'controller' && u.isController) return matchesSearch;
      
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
      linkedClientCodigo: '',
      provinciaCode: '',  // Código de provincia
      accessExpirationDate: '',  // Fecha de caducidad
      linkedClientId: '',
      isActive: true,
      isAdmin: false,
      isResponsableDelegacion: false,
      isRepresentative: false,
      isPrescriptor: false,
      isTienda: false,
      isMontador: false,
      plataforma: PLATAFORMA_COOPERATIVA,
      esCooperativistaComercial: false,
      esCooperativistaMontador: false,
      manoObraPorMueble: null,
      isCarpintero: false,
      canManageCarpinteroUsers: false,
      carpinteroLandingUrl: '',
      isStudio3k: false,
      canManageStudio3kUsers: false,
      studio3kLandingUrl: 'https://studio3k.io',
      linkedRepresentativeId: isCommercial ? state.currentUser.id : '',
      allowedModules: ['montada'],
      allowedLibraries: ['ZC'],  // Por defecto ZC
      allowedCatalogIds: state.catalogs.map(c => c.id),
      commercialDiscount: 0,
      discountMontada: 0,
      discountDespiece: 0,
      discountDesmontada: 0,
      canSeeCost: false,
      canSeeRetail: true,
      canUseAIAnalysis: false,
      canUseKitchenDesigner: false,
      canManageArticles: false,
      canViewTechnicalDespiece: false,
      canAccessCRM: false,
      canUseResumenTotales: false,
      canUseCascos: false,
      canUseRender360: false,
      canUse4K: false,
      canUseAmueblado: false,
    canVolcarMV: false,
      canVerVinculadosCascos: false,
      canUsePropData: false,
      canUseArmarios2: false,
      canUseCocinasAI: false,
      canUseDigitalizador: false,
      canAccessArmarios: false,
      canAccessFabrica: false,
      canAccessMontajes: false,
      canUsePresupuestador1: true,
      canUsePresupuestador2: true,
      canAccessMaster: true,
      canAccessGastos: true,
      canAccessFloor: false,
      canUseAgentesIA: false,
      floorOnly: false,
      crmOnly: false,
      canAuthorizePermissions: false,
      useCustomBranding: false,
      canChangeLogo: false
    });
  };

  // Se cargan una vez: son pocas y hacen falta en cuanto se abre una ficha.
  useEffect(() => {
    (async () => {
      try {
        const r = await fetch(
          `${process.env.REACT_APP_BACKEND_URL}/api/montadores`,
          { headers: authHeaders() });
        if (!r.ok) return;                       // sin agenda, sin sugerencias
        const d = await r.json().catch(() => []);
        setFichasMontador(Array.isArray(d) ? d : (d.montadores || []));
      } catch { /* la vinculación es opcional: no rompe la pantalla */ }
    })();
  }, []);

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
    // Asegurar que allowedLibraries, provinciaCode y accessExpirationDate tengan valor por defecto
    setUserForm({
      ...user,
      linkedClientId: user.linkedClientId || '',
      linkedClientCodigo: user.linkedClientCodigo || '',
      allowedLibraries: user.allowedLibraries || ['ZC'],
      provinciaCode: user.provinciaCode || '',
      accessExpirationDate: user.accessExpirationDate || '',
      // Los usuarios de antes del 27/08 no traen plataforma: son de la
      // cooperativa, el negocio de siempre. Mismo defecto que el servidor.
      plataforma: user.plataforma || PLATAFORMA_COOPERATIVA,
      // Socio se marca: nadie lo es por defecto (master, 27/08).
      esCooperativistaComercial: !!user.esCooperativistaComercial,
      esCooperativistaMontador: !!user.esCooperativistaMontador,
      // `?? null` y no `|| null`: un 0 puesto a propósito por el master
      // es una decisión suya y no se puede caer al valor de la casa.
      manoObraPorMueble: user.manoObraPorMueble ?? null
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
          users: prev.users.map(u => u.id === editingUserId ? updated : u),
          // Si se edita al usuario con sesión iniciada, refrescar currentUser
          // para que el presupuesto recalcule el COSTO (descuento) al instante,
          // sin necesidad de volver a iniciar sesión.
          ...(prev.currentUser?.id === editingUserId
            ? { currentUser: { ...prev.currentUser, ...updated } }
            : {})
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
      manufacturer: 'Master',
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
      manufacturer: product.manufacturer || 'Master',
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

    setIsSavingProduct(true);
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
      setIsSavingProduct(false);
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
    setMaterialForm({ name: '', fixedIncrement: 0, thickness: 16, backThickness: 8, library: defaultLibrary });
  };

  const handleEditMaterial = (material) => {
    setIsEditingMaterial(true);
    setEditingMaterialId(material.id);
    setMaterialForm({
      name: material.name,
      fixedIncrement: material.fixedIncrement || 0,
      thickness: material.thickness || 16,
      backThickness: material.backThickness || 8,
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
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 sm:p-6">
      <div className={`bg-white rounded-3xl shadow-2xl overflow-hidden flex flex-col transition-all duration-300 ${
        isFullScreen 
          ? 'w-full h-full max-w-none max-h-none rounded-none' 
          : 'w-full max-w-5xl max-h-[90vh]'
      }`}>
        {/* Header */}
        <div className="px-4 sm:px-8 py-4 sm:py-6 border-b border-slate-100 flex justify-between items-center bg-gradient-to-r from-indigo-950 to-indigo-900 shrink-0">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-white/10 rounded-xl">
              <SettingsIcon size={24} className="text-white" />
            </div>
            <div>
              <h2 className="text-xl sm:text-2xl font-black text-white uppercase tracking-tight">Panel Maestro</h2>
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

        {/* Pestañas + contenido: barra lateral en PC, barra deslizable arriba en móvil */}
        <div className="flex flex-col sm:flex-row flex-1 min-h-0">
        {/* Tabs */}
        <div className="px-3 py-3 sm:py-4 bg-slate-50 border-b sm:border-b-0 sm:border-r border-slate-200 flex sm:flex-col gap-2 overflow-x-auto sm:overflow-x-hidden sm:overflow-y-auto [&>button]:shrink-0 shrink-0 sm:w-56">
          {/* Tab Panel Director Comercial - Solo Admin/Gerente/Director Comercial */}
          {(state.currentUser?.isAdmin || state.currentUser?.isGerente || state.currentUser?.isDirectorComercial) && (
            <button
              onClick={() => setActiveTab('director')}
              className={`px-5 py-3 rounded-xl text-sm font-black uppercase tracking-wide transition-all whitespace-nowrap ${
                activeTab === 'director' ? 'bg-purple-600 text-white shadow-lg' : 'text-slate-500 hover:bg-white hover:text-slate-700'
              }`}
              data-testid="director-tab"
            >
              Panel Director Comercial
            </button>
          )}
          
          {/* Tab Dashboard Fábrica - Admin/Gerente/Director Comercial/Director Fábrica */}
          {(state.currentUser?.isAdmin || state.currentUser?.isGerente || state.currentUser?.isDirectorComercial || state.currentUser?.isDirectorFabrica) && (
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`px-5 py-3 rounded-xl text-sm font-black uppercase tracking-wide transition-all whitespace-nowrap ${
                activeTab === 'dashboard' ? 'bg-gradient-to-r from-blue-600 to-cyan-500 text-white shadow-lg' : 'text-slate-500 hover:bg-white hover:text-slate-700'
              }`}
              data-testid="dashboard-tab"
            >
              Dashboard Fábrica
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
          
          {/* Tab Mis Clientes - Solo Tiendas y Admin */}
          {(state.currentUser?.isTienda || state.currentUser?.isAdmin || state.currentUser?.isGerente || state.currentUser?.isDirectorComercial) && (
            <button
              onClick={() => setActiveTab('shop-clients')}
              className={`px-5 py-3 rounded-xl text-sm font-black uppercase tracking-wide transition-all whitespace-nowrap ${
                activeTab === 'shop-clients' ? 'bg-teal-600 text-white shadow-lg' : 'text-slate-500 hover:bg-white hover:text-slate-700'
              }`}
              data-testid="shop-clients-tab"
            >
              Mis Clientes
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

          {/* Tab Armarios - precios del configurador de armarios (separada de Armazones) */}
          {(state.currentUser?.isAdmin || state.currentUser?.canManageArticles) && (
            <button
              onClick={() => setActiveTab('armarios')}
              className={`px-5 py-3 rounded-xl text-sm font-black uppercase tracking-wide transition-all whitespace-nowrap ${
                activeTab === 'armarios' ? 'bg-amber-600 text-white shadow-lg' : 'text-slate-500 hover:bg-white hover:text-slate-700'
              }`}
              data-testid="armarios-precios-tab"
            >
              Armarios
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

          {/* Tab Facturación - Solo Admin */}
          {(state.currentUser?.isAdmin || state.currentUser?.isGerente) && (
            <button
              onClick={() => setActiveTab('billing')}
              className={`px-5 py-3 rounded-xl text-sm font-black uppercase tracking-wide transition-all whitespace-nowrap ${
                activeTab === 'billing' ? 'bg-emerald-700 text-white shadow-lg' : 'text-slate-500 hover:bg-white hover:text-slate-700'
              }`}
            >
              Facturación
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
          
          {(state.currentUser?.isAdmin || state.currentUser?.isGerente || state.currentUser?.isDirectorComercial) && (
            <button
              onClick={() => setActiveTab('digitalizador-audit')}
              className={`px-5 py-3 rounded-xl text-sm font-black uppercase tracking-wide transition-all whitespace-nowrap ${
                activeTab === 'digitalizador-audit' ? 'bg-amber-600 text-white shadow-lg' : 'text-slate-500 hover:bg-white hover:text-slate-700'
              }`}
              data-testid="digitalizador-audit-tab"
            >
              Digitalizador IA
            </button>
          )}
          
          {(state.currentUser?.isAdmin || state.currentUser?.isGerente) && (
            <button
              onClick={() => setActiveTab('telemetry-audit')}
              className={`px-5 py-3 rounded-xl text-sm font-black uppercase tracking-wide transition-all whitespace-nowrap ${
                activeTab === 'telemetry-audit' ? 'bg-purple-600 text-white shadow-lg' : 'text-slate-500 hover:bg-white hover:text-slate-700'
              }`}
            >
              Auditoría IA
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
          
          {/* Nueva pestaña: Informe de Uso - Solo Admin Principal */}
          {state.currentUser?.isPrimaryAdmin && (
            <button
              onClick={() => setActiveTab('usage-report')}
              className={`px-5 py-3 rounded-xl text-sm font-black uppercase tracking-wide transition-all whitespace-nowrap ${
                activeTab === 'usage-report' ? 'bg-cyan-600 text-white shadow-lg' : 'text-slate-500 hover:bg-white hover:text-slate-700'
              }`}
            >
              <span className="flex items-center gap-2">
                <TrendingUp size={16} /> Uso Usuarios
              </span>
            </button>
          )}
          
          
          {/* Medidor de consumo IA por cliente - Solo Admin */}
          {state.currentUser?.isAdmin && (
            <button
              onClick={() => setActiveTab('ai-meter')}
              className={`px-5 py-3 rounded-xl text-sm font-black uppercase tracking-wide transition-all whitespace-nowrap ${
                activeTab === 'ai-meter' ? 'bg-gradient-to-r from-amber-500 to-orange-600 text-white shadow-lg' : 'text-slate-500 hover:bg-white hover:text-slate-700'
              }`}
            >
              <span className="flex items-center gap-2">
                <Euro size={16} /> Consumo IA
              </span>
            </button>
          )}
          {/* Suscripciones SaaS - Solo Admin */}
          {state.currentUser?.isAdmin && (
            <button
              onClick={() => setActiveTab('subscriptions')}
              className={`px-5 py-3 rounded-xl text-sm font-black uppercase tracking-wide transition-all whitespace-nowrap ${
                activeTab === 'subscriptions' ? 'bg-gradient-to-r from-indigo-600 to-violet-600 text-white shadow-lg' : 'text-slate-500 hover:bg-white hover:text-slate-700'
              }`}
            >
              <span className="flex items-center gap-2">
                <Euro size={16} /> Suscripciones
              </span>
            </button>
          )}
          {/* Costes de artículos - Solo Admin */}
          {state.currentUser?.isAdmin && (
            <button
              onClick={() => setActiveTab('costes-articulos')}
              className={`px-5 py-3 rounded-xl text-sm font-black uppercase tracking-wide transition-all whitespace-nowrap ${
                activeTab === 'costes-articulos' ? 'bg-gradient-to-r from-emerald-600 to-teal-600 text-white shadow-lg' : 'text-slate-500 hover:bg-white hover:text-slate-700'
              }`}
            >
              <span className="flex items-center gap-2">
                <Euro size={16} /> Costes artículos
              </span>
            </button>
          )}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-8 min-w-0">
          {/* PANEL DIRECTOR TAB */}
          {activeTab === 'director' && (
            <DirectorTab />
          )}

          {/* ============================================ */}
          {/* DASHBOARD DE MÉTRICAS */}
          {/* ============================================ */}
          {activeTab === 'dashboard' && (
            <DashboardTab />
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
                      <button
                        onClick={() => setUserRoleFilter('carpintero')}
                        className={`px-3 py-1.5 rounded-lg text-xs font-bold uppercase whitespace-nowrap transition-all ${
                          userRoleFilter === 'carpintero' ? 'bg-orange-600 text-white shadow' : 'text-slate-600 hover:bg-orange-100'
                        }`}
                      >
                        🪚 Carpintero ({visibleUsers.filter(u => u.isCarpintero).length})
                      </button>
                      <button
                        onClick={() => setUserRoleFilter('controller')}
                        className={`px-3 py-1.5 rounded-lg text-xs font-bold uppercase whitespace-nowrap transition-all ${
                          userRoleFilter === 'controller' ? 'bg-emerald-600 text-white shadow' : 'text-slate-600 hover:bg-emerald-100'
                        }`}
                      >
                        📊 Controller ({visibleUsers.filter(u => u.isController).length})
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
                            
                            {(state.currentUser?.isAdmin || state.currentUser?.isGerente || state.currentUser?.isDirectorComercial) && <div className="grid grid-cols-3 gap-3 mt-3">
                              <div className="bg-slate-50 p-2 rounded-lg">
                                <p className="text-[9px] font-black text-slate-400 uppercase mb-1">Rol</p>
                                <p className="text-xs font-bold text-slate-900">
                                  {user.isGerente ? '👔 Gerente' :
                                   user.isAdmin ? '🛡️ Director Comercial' :
                                   user.isDirectorComercial ? '📊 Dir. Comercial' :
                                   user.isDirectorFabrica ? '🏭 Dir. Fábrica' :
                                   user.isResponsableDelegacion ? '📍 Resp. Delegación' :
                                   user.isRepresentative ? '💼 Comercial' :
                                   user.isPrescriptor ? '🤝 Colaborador' :
                                   user.isController ? '📊 Controller (consulta)' :
                                   user.isCarpintero ? '🪚 Carpintero/Ebanista' :
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
                                <p className="text-[9px] font-black text-slate-400 uppercase mb-1">Dto. Des-Montada</p>
                                <p className="text-xs font-bold text-cyan-600">{user.discountDesmontada || 0}%</p>
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
                                                        </div>}
                            {/* Capabilities badges - solo visible para admins */}
                            {(state.currentUser?.isAdmin || state.currentUser?.isGerente || state.currentUser?.isDirectorComercial) && <div className="flex flex-wrap gap-1 mt-3">
                              {user.canAuthorizePermissions && <span className="px-2 py-1 bg-red-100 text-red-700 rounded text-[9px] font-black">AUTORIZA</span>}
                              {user.canAccessArmarios && <span className="px-2 py-1 bg-cyan-100 text-cyan-700 rounded text-[9px] font-black">ARMARIOS</span>}
                              {user.canUseAIAnalysis && <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded text-[9px] font-black">IA LAB</span>}
                              {user.canUseKitchenDesigner && <span className="px-2 py-1 bg-amber-100 text-amber-700 rounded text-[9px] font-black">3D ESTUDIO</span>}
                              {user.canSeeCost && <span className="px-2 py-1 bg-orange-100 text-orange-700 rounded text-[9px] font-black">VER COSTO</span>}
                              {user.canViewTechnicalDespiece && <span className="px-2 py-1 bg-indigo-100 text-indigo-700 rounded text-[9px] font-black">INFORMES</span>}
                              {user.canManageArticles && <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-[9px] font-black">INVENTARIO</span>}
                              {user.canAccessCRM && <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-[9px] font-black">CRM</span>}
                              {user.canUseDigitalizador && <span className="px-2 py-1 bg-amber-100 text-amber-700 rounded text-[9px] font-black">DIGITALIZADOR</span>}
                              {user.canUsePresupuestador1 === false && <span className="px-2 py-1 bg-red-100 text-red-700 rounded text-[9px] font-black">SIN COCINA MONT. 2</span>}
                              {user.canUsePresupuestador2 === false && <span className="px-2 py-1 bg-red-100 text-red-700 rounded text-[9px] font-black">SIN COCINA MONT.</span>}
                              {user.canAccessFabrica && (
                                <span className="px-2 py-1 bg-emerald-100 text-emerald-700 rounded text-[9px] font-black">
                                  FÁBRICA{user.factoryId && factories.find(f => f.id === user.factoryId) ? ` (${factories.find(f => f.id === user.factoryId).code})` : ''}
                                </span>
                              )}
                              {user.canUseAgentesIA && <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded text-[9px] font-black">AGENTES IA</span>}
                              {user.canAccessMontajes && <span className="px-2 py-1 bg-orange-100 text-orange-700 rounded text-[9px] font-black">MONTAJES</span>}
                              {user.isMontador && <span className="px-2 py-1 bg-rose-100 text-rose-700 rounded text-[9px] font-black">MONTADOR</span>}
                              {user.isCarpintero && <span className="px-2 py-1 bg-amber-100 text-amber-800 rounded text-[9px] font-black">CARPINTERO</span>}
                              {user.useCustomBranding && <span className="px-2 py-1 bg-pink-100 text-pink-700 rounded text-[9px] font-black">PERSONALIZAR</span>}
                            </div>}
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
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
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
                        <label className="text-xs font-black text-slate-600 uppercase mb-2 block">Usuario / Email *</label>
                        <input
                          type="text"
                          value={userForm.username}
                          onChange={(e) => setUserForm({...userForm, username: e.target.value})}
                          placeholder="usuario@email.com o usuario123"
                          className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-sm font-bold outline-none focus:border-orange-500"
                        />
                        <p className="text-[10px] text-slate-400 mt-1">Puede ser un email o texto libre (minúsculas permitidas)</p>
                      </div>
                      <div className="relative">
                        <label className="text-xs font-black text-slate-600 uppercase mb-2 block">Código cliente (CRM)</label>
                        <input
                          type="text"
                          value={userForm.linkedClientCodigo || ''}
                          onChange={(e) => { setUserForm({...userForm, linkedClientCodigo: e.target.value, linkedClientId: ''}); setShowClientCodeList(true); }}
                          onFocus={() => setShowClientCodeList(true)}
                          onBlur={() => setTimeout(() => setShowClientCodeList(false), 150)}
                          placeholder="Ej: 2546 o nombre"
                          className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-sm font-bold outline-none focus:border-orange-500"
                        />
                        {(() => {
                          const q = (userForm.linkedClientCodigo || '').trim().toLowerCase();
                          const exact = q && clients.find(c => (c.codigo || '').toLowerCase() === q);
                          if (exact) return <p className="text-[10px] text-emerald-600 font-bold mt-1">✓ {exact.nombre}</p>;
                          if (q) return <p className="text-[10px] text-amber-500 mt-1">Sin coincidencia exacta · se guardará tal cual</p>;
                          return <p className="text-[10px] text-slate-400 mt-1">Si este usuario es un cliente con acceso, pon su código para relacionarlo con el CRM.</p>;
                        })()}
                        {showClientCodeList && (userForm.linkedClientCodigo || '').trim().length >= 1 && (() => {
                          const q = userForm.linkedClientCodigo.trim().toLowerCase();
                          const matches = clients.filter(c => (c.codigo || '').toLowerCase().includes(q) || (c.nombre || '').toLowerCase().includes(q)).slice(0, 8);
                          if (!matches.length) return null;
                          return (
                            <div className="absolute z-[120] mt-1 w-full bg-white rounded-xl shadow-2xl border border-slate-200 max-h-64 overflow-y-auto">
                              {matches.map(c => (
                                <button key={c.id} type="button"
                                  onMouseDown={(ev) => { ev.preventDefault(); setUserForm(f => ({ ...f, linkedClientCodigo: c.codigo || '', linkedClientId: c.id || '', clientName: f.clientName || c.nombre || '' })); setShowClientCodeList(false); }}
                                  className="w-full text-left px-3 py-2 hover:bg-orange-50 border-b border-slate-100 last:border-0">
                                  <span className="block text-xs font-black text-slate-800 truncate">{c.nombre || 'Sin nombre'}</span>
                                  <span className="block text-[10px] text-slate-400">{[c.codigo && `Cód. ${c.codigo}`, c.localidad].filter(Boolean).join(' · ') || 'Sin código'}</span>
                                </button>
                              ))}
                            </div>
                          );
                        })()}
                      </div>
                    </div>

                    {/* Provincia */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div>
                        <label className="text-xs font-black text-slate-600 uppercase mb-2 block">Provincia *</label>
                        <select
                          value={userForm.provinciaCode || ''}
                          onChange={(e) => setUserForm({...userForm, provinciaCode: e.target.value})}
                          className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-sm font-bold outline-none focus:border-orange-500 cursor-pointer"
                        >
                          <option value="">-- Seleccionar provincia --</option>
                          {PROVINCIAS_ESPANA.map(prov => (
                            <option key={prov.codigo + prov.nombre} value={prov.codigo}>
                              {prov.nombre} ({prov.codigo})
                            </option>
                          ))}
                        </select>
                        <p className="text-[10px] text-slate-400 mt-1">Se usará para numerar expedientes: EXP-2026-{userForm.provinciaCode || 'XX'}-001</p>
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
                    </div>

                    {/* Fecha de caducidad del acceso */}
                    <div className="bg-amber-50 p-4 rounded-xl border border-amber-200">
                      <h4 className="text-sm font-black text-amber-800 uppercase mb-3 flex items-center gap-2">
                        <Clock size={16} className="text-amber-600" />
                        Caducidad del Acceso
                      </h4>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div>
                          <label className="text-xs font-black text-amber-700 uppercase mb-2 block">Fecha de Vencimiento</label>
                          <input
                            type="date"
                            value={userForm.accessExpirationDate || ''}
                            onChange={(e) => setUserForm({...userForm, accessExpirationDate: e.target.value})}
                            min={new Date().toISOString().split('T')[0]}
                            className="w-full bg-white border border-amber-300 rounded-xl p-3 text-sm font-bold outline-none focus:border-orange-500"
                          />
                        </div>
                        <div className="flex items-end">
                          {userForm.accessExpirationDate && (
                            <div className="flex flex-col gap-2 w-full">
                              <span className={`text-xs font-black px-3 py-2 rounded-lg text-center ${
                                new Date(userForm.accessExpirationDate) > new Date() 
                                  ? 'bg-emerald-100 text-emerald-700' 
                                  : 'bg-red-100 text-red-700'
                              }`}>
                                {new Date(userForm.accessExpirationDate) > new Date() 
                                  ? `✓ Activo hasta ${new Date(userForm.accessExpirationDate).toLocaleDateString('es-ES')}`
                                  : `✗ Expirado el ${new Date(userForm.accessExpirationDate).toLocaleDateString('es-ES')}`
                                }
                              </span>
                              <button
                                type="button"
                                onClick={() => {
                                  const newDate = new Date();
                                  newDate.setFullYear(newDate.getFullYear() + 1);
                                  setUserForm({...userForm, accessExpirationDate: newDate.toISOString().split('T')[0]});
                                }}
                                className="text-[10px] text-amber-600 hover:text-amber-800 font-bold underline"
                              >
                                Renovar +1 año
                              </button>
                            </div>
                          )}
                          {!userForm.accessExpirationDate && (
                            <span className="text-xs text-slate-400 italic">Sin fecha de caducidad (acceso permanente)</span>
                          )}
                        </div>
                      </div>
                      <p className="text-[10px] text-amber-600 mt-2">Si no se establece fecha, el acceso es permanente. Los usuarios con acceso expirado no podrán iniciar sesión.</p>
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
                              <span title="Rol elevado: acceso casi total salvo lo reservado al admin principal." className="text-sm font-black text-slate-900">Gerente</span>
                              <p className="text-xs text-slate-500">Acceso total al sistema</p>
                            </div>
                          </label>
                          {/* DIRECTOR COMERCIAL - Segundo */}
                          <label className="flex items-center gap-3 cursor-pointer p-3 bg-orange-100 rounded-xl border border-orange-200">
                            <input
                              type="checkbox"
                              checked={userForm.isDirectorComercial}
                              onChange={(e) => setUserForm({...userForm, isDirectorComercial: e.target.checked, isGerente: false, isDirectorFabrica: false})}
                              className="w-5 h-5 rounded border-2 border-orange-300"
                            />
                            <div>
                              <span title="Dirección comercial: ve toda la red comercial y sus datos." className="text-sm font-black text-slate-900">Director Comercial</span>
                              <p className="text-xs text-slate-500">Ve todo el CRM y estadísticas</p>
                            </div>
                          </label>
                          {/* DIRECTOR DE FÁBRICA - Nuevo */}
                          <label className="flex items-center gap-3 cursor-pointer p-3 bg-cyan-100 rounded-xl border border-cyan-200">
                            <input
                              type="checkbox"
                              checked={userForm.isDirectorFabrica}
                              onChange={(e) => setUserForm({
                                ...userForm, 
                                isDirectorFabrica: e.target.checked, 
                                isGerente: false, 
                                isDirectorComercial: false,
                                canAccessFabrica: e.target.checked // Acceso automático a Fábrica
                              })}
                              className="w-5 h-5 rounded border-2 border-cyan-300"
                            />
                            <div>
                              <span title="Dirección de fábrica: acceso a producción y fábrica." className="text-sm font-black text-slate-900">Director de Fábrica</span>
                              <p className="text-xs text-slate-500">Ve Dashboard Fábrica y gestiona producción</p>
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
                              <span title="Comercial: gestiona sus clientes y presupuestos." className="text-sm font-black text-slate-900">Comercial / Representante</span>
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
                                <span title="Responsable de una delegación: ve a su equipo y clientes." className="text-sm font-black text-slate-900">Responsable de Delegación</span>
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
                                <span title="Prescriptor/colaborador externo: agenda de negocios limitada." className="text-sm font-black text-slate-900">Colaborador Comercial</span>
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
                                <span title="Punto de venta: acceso restringido de tienda." className="text-sm font-black text-slate-900">Tienda / Punto de Venta</span>
                                <p className="text-xs text-slate-500">Solo acceso al presupuestador (sin CRM ni panel maestro)</p>
                              </div>
                            </label>
                          )}

                          {/* USUARIO SOLO FÁBRICA - Selector de fábrica asignada */}
                          {factories.length > 0 && (
                            <div className="bg-gradient-to-r from-emerald-50 to-teal-50 rounded-xl p-4 border border-emerald-200">
                              <label className="text-xs font-black text-emerald-700 mb-2 block flex items-center gap-2">
                                <Factory size={14} className="text-emerald-600" />
                                🏭 Usuario Solo Fábrica
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
                          <span title="Habilita el presupuestador Cocina Montada." className="text-sm font-black text-slate-900">Uso Cocina Montada</span>
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={userForm.canUsePresupuestador3 !== false}
                            onChange={(e) => setUserForm({...userForm, canUsePresupuestador3: e.target.checked})}
                            className="w-5 h-5 rounded border-2 border-indigo-300"
                          />
                          <span title="Habilita Cocina Montada 3 (presupuestación rápida por códigos MV)." className="text-sm font-black text-slate-900">Uso Cocina Montada 3</span>
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={userForm.allowedModules?.includes('despiece')}
                            onChange={() => handleToggleModule('despiece')}
                            className="w-5 h-5 rounded border-2 border-indigo-300"
                          />
                          <span title="Habilita el formato de despiece en presupuestos." className="text-sm font-black text-slate-900">Uso Formato Despiece</span>
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer bg-purple-100 px-3 py-1 rounded-lg border border-purple-200">
                          <input
                            type="checkbox"
                            checked={userForm.canAccessArmarios}
                            onChange={(e) => setUserForm({...userForm, canAccessArmarios: e.target.checked})}
                            className="w-5 h-5 rounded border-2 border-purple-300"
                          />
                          <span title="Acceso al configurador de Armarios (por m²)." className="text-sm font-black text-purple-900">Diseñador Armarios</span>
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

                    {/* PLATAFORMA. Tres negocios comparten este ERP «de momento» y solo
                        uno tiene cooperativistas: cambiar esto decide si el usuario
                        puede cobrar comisiones, no solo qué ve. Por eso está aquí
                        arriba, con su explicación, y no escondido como una casilla
                        más. Ver services/plataformas.py. */}
                    <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
                      <h4 className="text-sm font-black text-slate-800 uppercase mb-1">Plataforma</h4>
                      <p className="text-[11px] text-slate-500 mb-2">
                        A qué negocio pertenece este usuario. Solo la red de distribución
                        tiene socios cooperativistas y comisiones: carpinter.io y Studio3K
                        venden suscripciones.
                      </p>
                      <select
                        value={userForm.plataforma || PLATAFORMA_COOPERATIVA}
                        onChange={(e) => setUserForm({...userForm, plataforma: e.target.value})}
                        className="w-full px-3 py-2 rounded-lg border border-slate-300 text-sm font-bold text-slate-800 bg-white"
                        data-testid="user-plataforma-select"
                      >
                        {PLATAFORMAS.map((k) => (
                          <option key={k} value={k}>{NOMBRES_PLATAFORMA[k]}</option>
                        ))}
                      </select>

                      {/* SOCIO COOPERATIVISTA. Se marca aquí, y solo aquí: no se
                          deduce de «Montador» ni de «Comercial», que son los roles
                          genéricos del ERP y los tiene medio mundo. Estas dos
                          casillas son las ÚNICAS que reparten comisión. */}
                      <div className="mt-3 pt-3 border-t border-slate-200">
                        <p className="text-[11px] font-black text-slate-700 uppercase tracking-widest mb-1">
                          Socio cooperativista
                        </p>
                        <p className="text-[11px] text-slate-500 mb-2">
                          Solo estos dos roles cobran comisión y ven «Mi área». El resto
                          —incluidos el comercial y el montador en nómina— son
                          independientes y no llevan compensación.
                        </p>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                          <label className="flex items-center gap-2 cursor-pointer bg-white px-2 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-100 transition-colors">
                            <input
                              type="checkbox"
                              checked={!!userForm.esCooperativistaComercial}
                              onChange={(e) => setUserForm({...userForm, esCooperativistaComercial: e.target.checked})}
                              className="w-4 h-4 rounded accent-ok-600"
                              data-testid="cooperativista-comercial-checkbox"
                            />
                            <span title="Socio comercial: cobra por tramos según la valoración del pedido." className="text-xs font-bold text-slate-700">Comercial cooperativista</span>
                          </label>
                          <label className="flex items-center gap-2 cursor-pointer bg-white px-2 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-100 transition-colors">
                            <input
                              type="checkbox"
                              checked={!!userForm.esCooperativistaMontador}
                              onChange={(e) => setUserForm({...userForm, esCooperativistaMontador: e.target.checked})}
                              className="w-4 h-4 rounded accent-ok-600"
                              data-testid="cooperativista-montador-checkbox"
                            />
                            <span title="Socio montador: cobra la mano de obra por mueble." className="text-xs font-bold text-slate-700">Montador cooperativista</span>
                          </label>
                        </div>
                        {/* LA FICHA DE LA AGENDA. Es el puente entre el montaje que ya
                            está agendado y la cuenta con la que entra: con esto el ERP
                            puede proponer solo quién montó cada pedido, en vez de que el
                            master lo diga a mano uno por uno. Sin ficha no pasa nada
                            malo — solo que no habrá sugerencia. */}
                        {userForm.esCooperativistaMontador && (
                          <div className="mt-2 flex items-center gap-2 flex-wrap">
                            <span className="text-[11px] font-bold text-slate-600">
                              Su ficha en la agenda de montajes:
                            </span>
                            <select
                              value={userForm.montadorId || ''}
                              onChange={(e) => setUserForm({...userForm, montadorId: e.target.value || null})}
                              className="px-2 py-1 rounded-lg border border-slate-300 text-xs font-bold text-slate-800 bg-white"
                              data-testid="montador-ficha-select"
                            >
                              <option value="">— sin vincular —</option>
                              {(fichasMontador || []).map((f) => (
                                <option key={f.id} value={f.id}>{f.name || f.id}</option>
                              ))}
                            </select>
                            <span className="text-[11px] text-slate-500">
                              sirve para proponer quién montó cada pedido
                            </span>
                            <p className="w-full text-[11px] text-slate-500 mt-1">
                              En la agenda hay montadores externos y de la cooperativa.
                              Vincular la ficha NO hace socio a nadie: quien cobra es
                              quien tiene marcado «Montador cooperativista» aquí arriba.
                            </p>
                          </div>
                        )}

                        {/* SU mano de obra por mueble. Vacío = cobra la de la casa.
                            Se deja vacío a propósito en vez de precargar los 17: un
                            número escrito ahí parece una decisión tomada para esta
                            persona, y no lo es. */}
                        {userForm.esCooperativistaMontador && (
                          <div className="mt-2 flex items-center gap-2 flex-wrap">
                            <span className="text-[11px] font-bold text-slate-600">
                              Su mano de obra por mueble montado:
                            </span>
                            <input
                              type="number"
                              step="0.01"
                              min="0"
                              value={userForm.manoObraPorMueble ?? ''}
                              placeholder="la de la casa"
                              onChange={(e) => setUserForm({
                                ...userForm,
                                manoObraPorMueble: e.target.value === '' ? null : Number(e.target.value),
                              })}
                              className="w-28 px-2 py-1 rounded-lg border border-slate-300 text-xs font-bold text-slate-800 bg-white"
                              data-testid="mano-obra-montador-input"
                            />
                            <span className="text-[11px] text-slate-500">
                              € · en blanco cobra la de la casa
                            </span>
                          </div>
                        )}
                        {userForm.plataforma && userForm.plataforma !== PLATAFORMA_COOPERATIVA
                          && (userForm.esCooperativistaComercial || userForm.esCooperativistaMontador) && (
                          <p className="text-[11px] text-aviso-700 font-bold mt-2">
                            Ojo: está marcado como socio cooperativista, pero al no ser de la
                            red de distribución NO cobrará comisiones ni verá «Mi área».
                          </p>
                        )}
                      </div>
                    </div>

                    {/* Technical Capabilities */}
                    <div className="bg-purple-50 p-4 rounded-xl border border-purple-100">
                      <p className="text-[11px] text-purple-500 mb-2 italic">💡 Pasa el ratón sobre cada permiso para ver qué habilita.</p>
                      <div className="flex items-center justify-between mb-3 gap-2">
                        <h4 className="text-sm font-black text-purple-900 uppercase">Capacidades Técnicas</h4>
                        <div className="flex gap-1.5 shrink-0">
                          <button type="button"
                            onClick={() => setUserForm(prev => ({ ...prev, ...Object.fromEntries(CAPABILITY_KEYS.map(k => [k, true])) }))}
                            className="px-2 py-1 rounded-lg bg-emerald-600 text-white text-[10px] font-black uppercase hover:bg-emerald-700 transition-colors">Marcar todo</button>
                          <button type="button"
                            onClick={() => setUserForm(prev => ({ ...prev, ...Object.fromEntries(CAPABILITY_KEYS.map(k => [k, false])) }))}
                            className="px-2 py-1 rounded-lg bg-slate-200 text-slate-700 text-[10px] font-black uppercase hover:bg-slate-300 transition-colors">Desmarcar todo</button>
                        </div>
                      </div>
                      <div className="space-y-3">
                        {/* ── Grupo: Presupuestación ── */}
                        <div>
                          <p className="text-[10px] font-black text-purple-400 uppercase tracking-widest mb-1.5">📐 Presupuestación</p>
                          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                            <label className="flex items-center gap-2 cursor-pointer bg-white/50 px-2 py-1.5 rounded-lg hover:bg-white transition-colors">
                              <input
                                type="checkbox"
                                checked={userForm.canUsePresupuestador2 !== false}
                                onChange={(e) => setUserForm({...userForm, canUsePresupuestador2: e.target.checked})}
                                className="w-4 h-4 rounded accent-emerald-600"
                              />
                              <span title="Acceso al presupuestador principal (Cocina Montada / MV)." className="text-xs font-bold text-slate-700">Cocina Montada (principal)</span>
                            </label>
                            <label className="flex items-center gap-2 cursor-pointer bg-white/50 px-2 py-1.5 rounded-lg hover:bg-white transition-colors">
                              <input
                                type="checkbox"
                                checked={userForm.canUsePresupuestador1 !== false}
                                onChange={(e) => setUserForm({...userForm, canUsePresupuestador1: e.target.checked})}
                                className="w-4 h-4 rounded accent-brand"
                              />
                              <span title="Acceso al presupuestador secundario (Cocina Montada 2)." className="text-xs font-bold text-slate-700">Cocina Montada 2</span>
                            </label>
                            <label className="flex items-center gap-2 cursor-pointer bg-white/50 px-2 py-1.5 rounded-lg hover:bg-white transition-colors">
                              <input
                                type="checkbox"
                                checked={userForm.canUsePresupuestador3 !== false}
                                onChange={(e) => setUserForm({...userForm, canUsePresupuestador3: e.target.checked})}
                                className="w-4 h-4 rounded accent-indigo-600"
                              />
                              <span title="Acceso al presupuestador Cocina Montada 3 (por relación y códigos MV)." className="text-xs font-bold text-slate-700">Cocina Montada 3</span>
                            </label>
                            <label className="flex items-center gap-2 cursor-pointer bg-white/50 px-2 py-1.5 rounded-lg hover:bg-white transition-colors">
                              <input
                                type="checkbox"
                                checked={userForm.canSeeCost}
                                onChange={(e) => setUserForm({...userForm, canSeeCost: e.target.checked})}
                                className="w-4 h-4 rounded accent-purple-600"
                              />
                              <span title="Permite ver el coste/escandallo de los productos." className="text-xs font-bold text-slate-700">Ver Costo</span>
                            </label>
                            <label className="flex items-center gap-2 cursor-pointer bg-white/50 px-2 py-1.5 rounded-lg hover:bg-white transition-colors">
                              <input
                                type="checkbox"
                                checked={userForm.canViewTechnicalDespiece}
                                onChange={(e) => setUserForm({...userForm, canViewTechnicalDespiece: e.target.checked})}
                                className="w-4 h-4 rounded accent-purple-600"
                              />
                              <span title="Ver informes técnicos y de despiece." className="text-xs font-bold text-slate-700">Informes</span>
                            </label>
                          </div>
                        </div>

                        {/* ── Grupo: CRM / Comercial ── */}
                        <div>
                          <p className="text-[10px] font-black text-blue-400 uppercase tracking-widest mb-1.5">🤝 CRM / Comercial</p>
                          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                            <label className="flex items-center gap-2 cursor-pointer bg-white/50 px-2 py-1.5 rounded-lg hover:bg-white transition-colors">
                              <input
                                type="checkbox"
                                checked={userForm.canAccessCRM}
                                onChange={(e) => setUserForm({...userForm, canAccessCRM: e.target.checked})}
                                className="w-4 h-4 rounded accent-blue-600"
                              />
                              <span title="Acceso al CRM: clientes, oportunidades y agenda comercial." className="text-xs font-bold text-slate-700">CRM</span>
                            </label>
                            <label className="flex items-center gap-2 cursor-pointer bg-indigo-50 px-2 py-1.5 rounded-lg hover:bg-indigo-100 transition-colors border border-indigo-200">
                              <input
                                type="checkbox"
                                checked={!!userForm.crmOnly}
                                onChange={(e) => setUserForm({...userForm, crmOnly: e.target.checked, canAccessCRM: e.target.checked ? true : userForm.canAccessCRM})}
                                className="w-4 h-4 rounded accent-indigo-600"
                              />
                              <span className="text-xs font-black text-indigo-700">Solo CRM (directo)</span>
                            </label>
                            <label className="flex items-center gap-2 cursor-pointer bg-teal-100 px-2 py-1.5 rounded-lg hover:bg-teal-200 transition-colors border border-teal-300">
                              <input
                                type="checkbox"
                                checked={userForm.canAccessGastos !== false}
                                onChange={(e) => setUserForm({...userForm, canAccessGastos: e.target.checked})}
                                className="w-4 h-4 rounded accent-teal-600"
                              />
                              <span className="text-xs font-black text-teal-800">Gastos</span>
                            </label>
                          </div>
                        </div>

                        {/* ── Grupo: Producción / Fábrica ── */}
                        <div>
                          <p className="text-[10px] font-black text-emerald-500 uppercase tracking-widest mb-1.5">🏭 Producción / Fábrica</p>
                          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                            <label className="flex items-center gap-2 cursor-pointer bg-indigo-100 px-2 py-1.5 rounded-lg hover:bg-indigo-200 transition-colors border border-indigo-300">
                              <input
                                type="checkbox"
                                checked={userForm.canAccessPlanificacion !== false}
                                onChange={(e) => setUserForm({...userForm, canAccessPlanificacion: e.target.checked})}
                                className="w-4 h-4 rounded accent-indigo-600"
                              />
                              <span className="text-xs font-black text-indigo-900">Producción y Almacén</span>
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
                            <label className="flex items-center gap-2 cursor-pointer bg-orange-100 px-2 py-1.5 rounded-lg hover:bg-orange-200 transition-colors border border-orange-300">
                              <input
                                type="checkbox"
                                checked={userForm.canAccessMontajes}
                                onChange={(e) => setUserForm({...userForm, canAccessMontajes: e.target.checked})}
                                className="w-4 h-4 rounded accent-orange-600"
                              />
                              <span className="text-xs font-black text-orange-800">Agenda Montajes</span>
                            </label>
                            <label className="flex items-center gap-2 cursor-pointer bg-white/50 px-2 py-1.5 rounded-lg hover:bg-white transition-colors">
                              <input
                                type="checkbox"
                                checked={userForm.isMontador}
                                onChange={(e) => setUserForm({...userForm, isMontador: e.target.checked})}
                                className="w-4 h-4 rounded accent-rose-600"
                              />
                              <span title="Marca al usuario como montador (agenda de montajes)." className="text-xs font-bold text-slate-700">Montador</span>
                            </label>
                            <label className="flex items-center gap-2 cursor-pointer bg-white/50 px-2 py-1.5 rounded-lg hover:bg-white transition-colors">
                              <input
                                type="checkbox"
                                checked={!!userForm.isCarpintero}
                                onChange={(e) => setUserForm({...userForm, isCarpintero: e.target.checked})}
                                className="w-4 h-4 rounded accent-amber-700"
                              />
                              <span title="Perfil Carpintero/Ebanista: al entrar ve su portal con la web de inicio configurada." className="text-xs font-bold text-slate-700">Carpintero/Ebanista</span>
                            </label>
                            {userForm.isCarpintero && (
                              <>
                                <input
                                  type="url"
                                  value={userForm.carpinteroLandingUrl || ''}
                                  onChange={(e) => setUserForm({...userForm, carpinteroLandingUrl: e.target.value})}
                                  placeholder="URL web de inicio (landing carpinteros)"
                                  className="w-full px-2 py-1.5 border border-amber-300 rounded-lg text-xs"
                                />
                                <label className="flex items-center gap-2 cursor-pointer bg-amber-50 px-2 py-1.5 rounded-lg hover:bg-amber-100 transition-colors border border-amber-200">
                                  <input
                                    type="checkbox"
                                    checked={!!userForm.canManageCarpinteroUsers}
                                    onChange={(e) => setUserForm({...userForm, canManageCarpinteroUsers: e.target.checked})}
                                    className="w-4 h-4 rounded accent-amber-700"
                                  />
                                  <span title="Admin de la división: puede crear y gestionar sus propios usuarios/clientes, que heredan su marca y su landing." className="text-xs font-bold text-amber-900">Admin de división (crea sus usuarios)</span>
                                </label>
                              </>
                            )}
                            <label className="flex items-center gap-2 cursor-pointer bg-white/50 px-2 py-1.5 rounded-lg hover:bg-white transition-colors">
                              <input
                                type="checkbox"
                                checked={!!userForm.isStudio3k}
                                onChange={(e) => setUserForm({
                                  ...userForm,
                                  isStudio3k: e.target.checked,
                                  canUseKitchenDesigner: e.target.checked ? true : userForm.canUseKitchenDesigner,
                                  canUseCocinasAI: e.target.checked ? true : userForm.canUseCocinasAI,
                                  canUseAIAnalysis: e.target.checked ? true : userForm.canUseAIAnalysis,
                                  allowedModules: e.target.checked ? [] : userForm.allowedModules,
                                })}
                                className="w-4 h-4 rounded accent-indigo-600"
                              />
                              <span title="Perfil Studio3K: entra en un entorno privado con Estudio 3D como aplicación principal." className="text-xs font-bold text-slate-700">Studio3K · Estudio de cocinas</span>
                            </label>
                            {userForm.isStudio3k && (
                              <>
                                <input
                                  type="url"
                                  value={userForm.studio3kLandingUrl || ''}
                                  onChange={(e) => setUserForm({...userForm, studio3kLandingUrl: e.target.value})}
                                  placeholder="URL web de inicio Studio3K"
                                  className="w-full px-2 py-1.5 border border-indigo-300 rounded-lg text-xs"
                                />
                                <label className="flex items-center gap-2 cursor-pointer bg-indigo-50 px-2 py-1.5 rounded-lg hover:bg-indigo-100 transition-colors border border-indigo-200">
                                  <input
                                    type="checkbox"
                                    checked={!!userForm.canManageStudio3kUsers}
                                    onChange={(e) => setUserForm({...userForm, canManageStudio3kUsers: e.target.checked})}
                                    className="w-4 h-4 rounded accent-indigo-600"
                                  />
                                  <span title="Admin del estudio: puede crear y gestionar únicamente los usuarios vinculados a su organización Studio3K." className="text-xs font-bold text-indigo-900">Admin del estudio (crea sus usuarios)</span>
                                </label>
                              </>
                            )}
                            <label className="flex items-center gap-2 cursor-pointer bg-white/50 px-2 py-1.5 rounded-lg hover:bg-white transition-colors">
                              <input
                                type="checkbox"
                                checked={userForm.canManageArticles}
                                onChange={(e) => setUserForm({...userForm, canManageArticles: e.target.checked})}
                                className="w-4 h-4 rounded accent-green-600"
                              />
                              <span title="Gestionar artículos e inventario." className="text-xs font-bold text-slate-700">Inventario</span>
                            </label>
                            <label className="flex items-center gap-2 cursor-pointer bg-amber-100 px-2 py-1.5 rounded-lg hover:bg-amber-200 transition-colors border border-amber-300">
                              <input
                                type="checkbox"
                                checked={!!userForm.canAccessFloor}
                                onChange={(e) => setUserForm({...userForm, canAccessFloor: e.target.checked})}
                                className="w-4 h-4 rounded accent-amber-600"
                              />
                              <span className="text-xs font-black text-amber-800">Floor</span>
                            </label>
                            <label className="flex items-center gap-2 cursor-pointer bg-amber-50 px-2 py-1.5 rounded-lg hover:bg-amber-100 transition-colors border border-amber-200">
                              <input
                                type="checkbox"
                                checked={!!userForm.floorOnly}
                                onChange={(e) => setUserForm({...userForm, floorOnly: e.target.checked, canAccessFloor: e.target.checked ? true : userForm.canAccessFloor})}
                                className="w-4 h-4 rounded accent-amber-600"
                              />
                              <span className="text-xs font-black text-amber-700">Solo Floor (directo)</span>
                            </label>
                            <label className="flex items-center gap-2 cursor-pointer bg-purple-100 px-2 py-1.5 rounded-lg hover:bg-purple-200 transition-colors border border-purple-300">
                              <input
                                type="checkbox"
                                checked={!!userForm.canUseAgentesIA}
                                onChange={(e) => setUserForm({...userForm, canUseAgentesIA: e.target.checked})}
                                className="w-4 h-4 rounded accent-purple-600"
                              />
                              <span className="text-xs font-black text-purple-800">Agentes IA</span>
                            </label>
                          </div>
                        </div>

                        {/* ── Grupo: IA / Diseño ── */}
                        <div>
                          <p className="text-[10px] font-black text-fuchsia-400 uppercase tracking-widest mb-1.5">🤖 IA / Diseño</p>
                          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                            <label className="flex items-center gap-2 cursor-pointer bg-white/50 px-2 py-1.5 rounded-lg hover:bg-white transition-colors">
                              <input
                                type="checkbox"
                                checked={userForm.canUseAIAnalysis}
                                onChange={(e) => setUserForm({...userForm, canUseAIAnalysis: e.target.checked})}
                                className="w-4 h-4 rounded accent-purple-600"
                              />
                              <span title="Herramientas de IA (análisis y laboratorio)." className="text-xs font-bold text-slate-700">IA Lab</span>
                            </label>
                            <label className="flex items-center gap-2 cursor-pointer bg-emerald-100 px-2 py-1.5 rounded-lg hover:bg-emerald-200 transition-colors border border-emerald-300">
                              <input
                                type="checkbox"
                                checked={!!userForm.canUseKitchenDesigner}
                                onChange={(e) => setUserForm({...userForm, canUseKitchenDesigner: e.target.checked})}
                                className="w-4 h-4 rounded accent-emerald-600"
                              />
                              <span className="text-xs font-black text-amber-800">Estudio 3D</span>
                            </label>
                            {/* Tipos permitidos dentro de Estudio 3D (por partidas). Vacío = todos. */}
                            {!!userForm.canUseKitchenDesigner && (
                              <div className="col-span-2 sm:col-span-3 bg-emerald-50 border border-emerald-200 rounded-lg px-2.5 py-2">
                                <p className="text-[10px] font-black text-emerald-700 uppercase tracking-wide mb-1.5">Estudio 3D · tipos permitidos <span className="text-emerald-500 font-bold normal-case">(vacío = todos)</span></p>
                                <div className="flex flex-wrap gap-1.5">
                                  {ESTUDIO_3D_TIPOS.map(tp => {
                                    const sel = Array.isArray(userForm.estudio3dTipos) ? userForm.estudio3dTipos : [];
                                    const on = sel.includes(tp.id);
                                    return (
                                      <button key={tp.id} type="button"
                                        onClick={() => { const next = on ? sel.filter(x => x !== tp.id) : [...sel, tp.id]; setUserForm({ ...userForm, estudio3dTipos: next }); }}
                                        className={`px-2.5 py-1 rounded-full text-[11px] font-bold border transition-colors ${on ? 'bg-emerald-600 text-white border-emerald-600' : 'bg-white text-slate-500 border-slate-200 hover:bg-slate-50'}`}>
                                        {tp.label}
                                      </button>
                                    );
                                  })}
                                </div>
                              </div>
                            )}
                            <label className="flex items-center gap-2 cursor-pointer bg-white/50 px-2 py-1.5 rounded-lg hover:bg-white transition-colors">
                              <input
                                type="checkbox"
                                checked={!!userForm.canVolcarMV}
                                onChange={(e) => setUserForm({...userForm, canVolcarMV: e.target.checked})}
                                className="w-4 h-4 rounded accent-emerald-600"
                              />
                              <span title="Volcar al presupuesto la relación de muebles MV que sale del Estudio 3D. NO da acceso a la tarifa (puntos y PVP), que es solo del master: se vuelcan los muebles, no los precios." className="text-xs font-bold text-slate-700">Volcar relación MV</span>
                            </label>
                            <label className="flex items-center gap-2 cursor-pointer bg-white/50 px-2 py-1.5 rounded-lg hover:bg-white transition-colors">
                              <input
                                type="checkbox"
                                checked={userForm.canUseDigitalizador}
                                onChange={(e) => setUserForm({...userForm, canUseDigitalizador: e.target.checked})}
                                className="w-4 h-4 rounded accent-orange-600"
                              />
                              <span title="Digitalizador de presupuestos a partir de documentos." className="text-xs font-bold text-slate-700">Digitalizador</span>
                            </label>
                            <label className="flex items-center gap-2 cursor-pointer bg-white/50 px-2 py-1.5 rounded-lg hover:bg-white transition-colors">
                              <input
                                type="checkbox"
                                checked={!!userForm.canUseResumenTotales}
                                onChange={(e) => setUserForm({...userForm, canUseResumenTotales: e.target.checked})}
                                className="w-4 h-4 rounded accent-indigo-600"
                              />
                              <span title="Resumen de cocinas con totales y forma de pago." className="text-xs font-bold text-slate-700">Resumen Totales</span>
                            </label>
                            <label className="flex items-center gap-2 cursor-pointer bg-white/50 px-2 py-1.5 rounded-lg hover:bg-white transition-colors">
                              <input
                                type="checkbox"
                                checked={!!userForm.canUseCascos}
                                onChange={(e) => setUserForm({...userForm, canUseCascos: e.target.checked})}
                                className="w-4 h-4 rounded accent-cyan-600"
                              />
                              <span title="Presupuestador de cascos (Cocina Desmontada)." className="text-xs font-bold text-slate-700">Cocina Desmontada (Cascos)</span>
                            </label>
                            <label className="flex items-center gap-2 cursor-pointer bg-white/50 px-2 py-1.5 rounded-lg hover:bg-white transition-colors">
                              <input
                                type="checkbox"
                                checked={!!userForm.canUseRender360}
                                onChange={(e) => setUserForm({...userForm, canUseRender360: e.target.checked})}
                                className="w-4 h-4 rounded accent-indigo-600"
                              />
                              <span title="Estudio 3D: generar un giro 360º del render y moverlo con el ratón (consume créditos de IA)." className="text-xs font-bold text-slate-700">Render 360º (giro con ratón)</span>
                            </label>
                            <label className="flex items-center gap-2 cursor-pointer bg-white/50 px-2 py-1.5 rounded-lg hover:bg-white transition-colors">
                              <input
                                type="checkbox"
                                checked={!!userForm.canUse4K}
                                onChange={(e) => setUserForm({...userForm, canUse4K: e.target.checked})}
                                className="w-4 h-4 rounded accent-indigo-600"
                              />
                              <span title="Estudio 3D: generar y descargar el render a resolución 4K real (3840 px)." className="text-xs font-bold text-slate-700">Render 4K</span>
                            </label>
                            <label className="flex items-center gap-2 cursor-pointer bg-white/50 px-2 py-1.5 rounded-lg hover:bg-white transition-colors">
                              <input
                                type="checkbox"
                                checked={!!userForm.canUseAmueblado}
                                onChange={(e) => setUserForm({...userForm, canUseAmueblado: e.target.checked})}
                                className="w-4 h-4 rounded accent-amber-600"
                              />
                              <span title="Estudio 3D: diseñar el mueble sobre una foto de la estancia real del cliente (amueblado virtual)." className="text-xs font-bold text-slate-700">Amueblado virtual (foto real)</span>
                            </label>
                            <label className="flex items-center gap-2 cursor-pointer bg-white/50 px-2 py-1.5 rounded-lg hover:bg-white transition-colors">
                              <input
                                type="checkbox"
                                checked={!!userForm.canVerVinculadosCascos}
                                onChange={(e) => setUserForm({...userForm, canVerVinculadosCascos: e.target.checked})}
                                className="w-4 h-4 rounded accent-cyan-600"
                              />
                              <span title="Abrir el documento vinculado (venta↔compra) por expediente." className="text-xs font-bold text-slate-700">Cascos: ver venta/compra vinculada</span>
                            </label>
                            <label className="flex items-center gap-2 cursor-pointer bg-white/50 px-2 py-1.5 rounded-lg hover:bg-white transition-colors">
                              <input
                                type="checkbox"
                                checked={!!userForm.canUsePropData}
                                onChange={(e) => setUserForm({...userForm, canUsePropData: e.target.checked})}
                                className="w-4 h-4 rounded accent-cyan-600"
                              />
                              <span title="Localizar promociones de obra nueva, arquitectos y prescriptores con IA." className="text-xs font-bold text-slate-700">Obra Nueva y Prescripción</span>
                            </label>
                            <label className="flex items-center gap-2 cursor-pointer bg-white/50 px-2 py-1.5 rounded-lg hover:bg-white transition-colors">
                              <input
                                type="checkbox"
                                checked={!!userForm.canUseArmarios2}
                                onChange={(e) => setUserForm({...userForm, canUseArmarios2: e.target.checked})}
                                className="w-4 h-4 rounded accent-cyan-600"
                              />
                              <span title="Diseñador de armarios con interior a medida y render IA." className="text-xs font-bold text-slate-700">Armarios 2 (diseñador IA)</span>
                            </label>
                            <label className="flex items-center gap-2 cursor-pointer bg-white/50 px-2 py-1.5 rounded-lg hover:bg-white transition-colors">
                              <input
                                type="checkbox"
                                checked={!!userForm.canUseCocinasAI}
                                onChange={(e) => setUserForm({...userForm, canUseCocinasAI: e.target.checked})}
                                className="w-4 h-4 rounded accent-cyan-600"
                              />
                              <span title="Render fotorrealista de cocina a partir del plano (IA)." className="text-xs font-bold text-slate-700">Cocinas IA 2 (render)</span>
                            </label>
                          </div>
                          {/* Créditos de IA por usuario (bolsa mensual). 0/vacío = usar el valor por defecto global. Admin/master = ilimitado. */}
                          <div className="mt-2 bg-white/60 border border-fuchsia-200 rounded-lg px-2.5 py-2">
                            <label className="block text-[10px] font-black text-fuchsia-600 uppercase tracking-wide mb-1">Créditos IA / mes</label>
                            <input
                              type="number"
                              min="0"
                              value={userForm.aiCreditsMonthly ?? ''}
                              onChange={(e) => setUserForm({ ...userForm, aiCreditsMonthly: e.target.value === '' ? '' : parseInt(e.target.value, 10) })}
                              placeholder="0 = valor por defecto"
                              className="w-full px-2 py-1.5 rounded-lg border border-slate-200 text-sm font-bold text-slate-700"
                            />
                            <p className="text-[10px] text-slate-400 mt-1">0 o vacío usa el crédito mensual por defecto. Admin/gerente tienen créditos ilimitados.</p>
                          </div>
                        </div>

                        {/* ── Grupo: Administración ── */}
                        <div>
                          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5">⚙️ Administración</p>
                          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                            <label className="flex items-center gap-2 cursor-pointer bg-indigo-100 px-2 py-1.5 rounded-lg hover:bg-indigo-200 transition-colors border border-indigo-300">
                              <input
                                type="checkbox"
                                checked={userForm.canAccessMaster !== false}
                                onChange={(e) => setUserForm({...userForm, canAccessMaster: e.target.checked})}
                                className="w-4 h-4 rounded accent-indigo-600"
                              />
                              <span className="text-xs font-black text-indigo-800">Panel MASTER</span>
                            </label>
                            <label className="flex items-center gap-2 cursor-pointer bg-white/50 px-2 py-1.5 rounded-lg hover:bg-white transition-colors">
                              <input
                                type="checkbox"
                                checked={userForm.canAuthorizePermissions}
                                onChange={(e) => setUserForm({...userForm, canAuthorizePermissions: e.target.checked})}
                                className="w-4 h-4 rounded accent-red-600"
                              />
                              <span title="Autorizar y gestionar los permisos de otros usuarios." className="text-xs font-bold text-slate-700">Autorizar</span>
                            </label>
                            <label className="flex items-center gap-2 cursor-pointer bg-white/50 px-2 py-1.5 rounded-lg hover:bg-white transition-colors">
                              <input
                                type="checkbox"
                                checked={userForm.useCustomBranding}
                                onChange={(e) => setUserForm({...userForm, useCustomBranding: e.target.checked})}
                                className="w-4 h-4 rounded accent-pink-600"
                              />
                              <span title="Personalizar apariencia/marca del sistema." className="text-xs font-bold text-slate-700">Personalizar</span>
                            </label>
                            <label className="flex items-center gap-2 cursor-pointer bg-white/50 px-2 py-1.5 rounded-lg hover:bg-white transition-colors">
                              <input
                                type="checkbox"
                                checked={userForm.canChangeLogo}
                                onChange={(e) => setUserForm({...userForm, canChangeLogo: e.target.checked})}
                                className="w-4 h-4 rounded accent-pink-600"
                              />
                              <span title="Cambiar el logo/marca del sistema." className="text-xs font-bold text-slate-700">Cambiar Logo</span>
                            </label>
                          </div>
                        </div>

                        {/* ── Grupo: Otros módulos ── */}
                        <div>
                          <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5">📂 Otros módulos</p>
                          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                            <label className="flex items-center gap-2 cursor-pointer bg-white/50 px-2 py-1.5 rounded-lg hover:bg-white transition-colors">
                              <input type="checkbox" checked={userForm.canAccessPedidos === true}
                                onChange={(e) => setUserForm({...userForm, canAccessPedidos: e.target.checked})}
                                className="w-4 h-4 rounded accent-orange-600" />
                              <span className="text-xs font-bold text-slate-700">Pedidos</span>
                            </label>
                            <label className="flex items-center gap-2 cursor-pointer bg-white/50 px-2 py-1.5 rounded-lg hover:bg-white transition-colors">
                              <input type="checkbox" checked={userForm.canAccessArchivo === true}
                                onChange={(e) => setUserForm({...userForm, canAccessArchivo: e.target.checked})}
                                className="w-4 h-4 rounded accent-blue-600" />
                              <span className="text-xs font-bold text-slate-700">Archivo</span>
                            </label>
                            <label className="flex items-center gap-2 cursor-pointer bg-orange-100 px-2 py-1.5 rounded-lg hover:bg-orange-200 transition-colors border border-orange-300">
                              <input type="checkbox" checked={userForm.canAccessInvoices !== false}
                                onChange={(e) => setUserForm({...userForm, canAccessInvoices: e.target.checked})}
                                className="w-4 h-4 rounded accent-orange-600" />
                              <span className="text-xs font-black text-orange-900">Gestión Comercial</span>
                            </label>
                            <label className="flex items-center gap-2 cursor-pointer bg-white/50 px-2 py-1.5 rounded-lg hover:bg-white transition-colors">
                              <input type="checkbox" checked={userForm.canAccessRentabilidad === true}
                                onChange={(e) => setUserForm({...userForm, canAccessRentabilidad: e.target.checked})}
                                className="w-4 h-4 rounded accent-emerald-600" />
                              <span className="text-xs font-bold text-slate-700">Rentabilidad</span>
                            </label>
                            <label className="flex items-center gap-2 cursor-pointer bg-white/50 px-2 py-1.5 rounded-lg hover:bg-white transition-colors"
                              title="Perfil CONTROLLER: SOLO consulta del informe de rentabilidad. No puede modificar nada.">
                              <input type="checkbox" checked={userForm.isController === true}
                                onChange={(e) => setUserForm({...userForm, isController: e.target.checked})}
                                className="w-4 h-4 rounded accent-emerald-600" />
                              <span className="text-xs font-bold text-slate-700">📊 Controller (consulta)</span>
                            </label>
                            <label className="flex items-center gap-2 cursor-pointer bg-white/50 px-2 py-1.5 rounded-lg hover:bg-white transition-colors">
                              <input type="checkbox" checked={userForm.canAccessMando === true}
                                onChange={(e) => setUserForm({...userForm, canAccessMando: e.target.checked})}
                                className="w-4 h-4 rounded accent-slate-600" />
                              <span className="text-xs font-bold text-slate-700">Panel Mando</span>
                            </label>
                          </div>
                        </div>
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

                      {/* Descuento Des-Montada (Cascos) */}
                      <div className="mt-4">
                        <label className="text-xs font-bold text-cyan-700 mb-1 block">Descuento DES-MONTADA (Cascos)</label>
                        <div className="flex items-center gap-4">
                          <input
                            type="range"
                            min="0"
                            max="100"
                            value={userForm.discountDesmontada || 0}
                            onChange={(e) => setUserForm({...userForm, discountDesmontada: parseInt(e.target.value)})}
                            className="flex-1"
                          />
                          <input
                            type="number"
                            min="0"
                            max="100"
                            value={userForm.discountDesmontada || 0}
                            onChange={(e) => setUserForm({...userForm, discountDesmontada: parseInt(e.target.value) || 0})}
                            className="w-20 bg-white border-2 border-cyan-300 rounded-xl p-2 text-center text-lg font-black text-cyan-700 outline-none"
                          />
                          <span className="text-sm font-black text-cyan-700">%</span>
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
                          <option key={seg.id || seg} value={seg.id || seg}>{seg.name || seg}</option>
                        ))}
                      </select>
                    </div>
                    
                    <div className="flex gap-2">
                      <button
                        onClick={handleBackfillClients}
                        className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold uppercase transition-colors"
                        title="Asignar los clientes antiguos (sin dueño) al usuario MARIO"
                      >
                        Asignar antiguos a MARIO
                      </button>
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
                              a.download = `Clientes_${new Date().toISOString().split('T')[0]}.xlsx`;
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
                  <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto">
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
                      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 sm:mx-auto p-4 sm:p-6">
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
                      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 sm:mx-auto p-4 sm:p-6">
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

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
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
                          <option key={seg.id || seg} value={seg.id || seg}>{seg.name || seg}</option>
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

          {/* Tab Mis Clientes (Shop Clients) */}
          {activeTab === 'shop-clients' && (
            <ShopClientsTab currentUser={state.currentUser} />
          )}

          {activeTab === 'inventory' && (
            <InventoryTab
              inventoryModule={inventoryModule}
              setInventoryModule={setInventoryModule}
              inventoryLibraryFilter={inventoryLibraryFilter}
              setInventoryLibraryFilter={setInventoryLibraryFilter}
              productSearch={productSearch}
              setProductSearch={setProductSearch}
              selectedProducts={selectedProducts}
              isEditingProduct={isEditingProduct}
              setIsEditingProduct={setIsEditingProduct}
              editingProductId={editingProductId}
              productForm={productForm}
              setProductForm={setProductForm}
              filteredProducts={filteredProducts}
              currentCatalog={currentCatalog}
              productProgramaFilter={productProgramaFilter}
              setProductProgramaFilter={setProductProgramaFilter}
              productTipoMuebleFilter={productTipoMuebleFilter}
              setProductTipoMuebleFilter={setProductTipoMuebleFilter}
              productSeriesFilter={productSeriesFilter}
              setProductSeriesFilter={setProductSeriesFilter}
              productZeroPriceFilter={productZeroPriceFilter}
              setProductZeroPriceFilter={setProductZeroPriceFilter}
              availableProgramas={availableProgramas}
              availableTiposMueble={availableTiposMueble}
              availableSeries={availableSeries}
              handleCreateProduct={handleCreateProduct}
              handleEditProduct={handleEditProduct}
              handleSaveProduct={handleSaveProduct}
              handleDeleteProduct={handleDeleteProduct}
              handleDeleteSelectedProducts={handleDeleteSelectedProducts}
              handleSelectAllProducts={handleSelectAllProducts}
              handleToggleProductSelection={handleToggleProductSelection}
              isSavingProduct={isSavingProduct}
            />
          )}

          {activeTab === 'pricing' && (
            <PricingTab state={state} setState={setState} />
          )}

          {/* Tab Armazones */}
          {activeTab === 'armazones' && (
            <ArmazonesTab
              state={state}
              setState={setState}
              materialLibraryFilter={materialLibraryFilter}
              setMaterialLibraryFilter={setMaterialLibraryFilter}
              isEditingMaterial={isEditingMaterial}
              setIsEditingMaterial={setIsEditingMaterial}
              editingMaterialId={editingMaterialId}
              materialForm={materialForm}
              setMaterialForm={setMaterialForm}
              handleCreateMaterial={handleCreateMaterial}
              handleEditMaterial={handleEditMaterial}
              handleSaveMaterial={handleSaveMaterial}
              handleDeleteMaterial={handleDeleteMaterial}
            />
          )}

          {activeTab === 'armarios' && (
            <div className="p-6 space-y-5 bg-slate-50">
              <div className="bg-white border border-slate-200 rounded-2xl p-5">
                <div className="flex items-center gap-3 mb-1">
                  <div className="w-10 h-10 rounded-xl bg-amber-100 text-amber-600 flex items-center justify-center shrink-0"><Layers size={18} /></div>
                  <h3 className="text-base font-black text-slate-900 uppercase">Armarios — precios</h3>
                </div>
                <p className="text-xs text-slate-500 mb-5 ml-[52px]">Precios base del configurador de armarios (modelo por m²). Vacío = valor por defecto.</p>
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
                  {[
                    { k: 'basePerM2', label: 'Base', unit: '€/m²', def: 450 },
                    { k: 'depthSuppPerMm', label: 'Fondo (>600)', unit: '€/mm', def: 0.5 },
                    { k: 'doorSlidingPerM2', label: 'P. corredera', unit: '€/m²', def: 180 },
                    { k: 'doorFoldingPerM2', label: 'P. plegable', unit: '€/m²', def: 250 },
                    { k: 'endStandard', label: 'Term. estándar', unit: '€', def: 85 },
                    { k: 'endPremium', label: 'Term. premium', unit: '€', def: 150 },
                    { k: 'endColumn', label: 'Term. columna', unit: '€', def: 280 },
                    { k: 'shelf', label: 'Balda', unit: '€', def: 25 },
                    { k: 'drawer', label: 'Cajón', unit: '€', def: 85 },
                    { k: 'hangingRod', label: 'Barra', unit: '€', def: 35 },
                    { k: 'softClosePerModule', label: 'Cierre suave', unit: '€/mód.', def: 45 },
                    { k: 'antiFingerprintPerM2', label: 'Anti-huellas', unit: '€/m²', def: 80 },
                    { k: 'ledPerModule', label: 'LED', unit: '€/mód.', def: 120 },
                    { k: 'mirror', label: 'Espejo', unit: '€', def: 200 },
                  ].map(f => (
                    <div key={f.k} className="bg-slate-50 border border-slate-200 rounded-xl p-2.5 hover:border-emerald-300 transition-colors">
                      <label className="text-[11px] font-bold text-slate-600 uppercase tracking-wide block truncate">{f.label}</label>
                      <div className="flex items-center gap-1 mt-1.5">
                        <input type="number" step="0.01" placeholder={String(f.def)}
                          defaultValue={state.settings?.['armPrice_' + f.k] ?? ''}
                          onBlur={(e) => saveSetting({ ['armPrice_' + f.k]: e.target.value === '' ? null : Number(e.target.value) })}
                          className="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded-lg text-sm outline-none focus:border-emerald-500 font-mono font-bold text-slate-900" />
                        <span className="text-[10px] font-bold text-slate-400 shrink-0">{f.unit}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <div className="bg-white border border-slate-200 rounded-2xl p-5">
                <div className="flex items-center gap-3 mb-1">
                  <div className="w-10 h-10 rounded-xl bg-purple-100 text-purple-600 flex items-center justify-center shrink-0"><Palette size={18} /></div>
                  <h3 className="text-base font-black text-slate-900 uppercase">Armarios — suplemento por material</h3>
                </div>
                <p className="text-xs text-slate-500 mb-5 ml-[52px]">€/m² extra según la categoría de color/acabado elegida (exterior e interior). Se suma al precio base €/m². Vacío = valor por defecto.</p>
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
                  {[
                    { k: 'matSupp_blancos', label: 'Blancos', def: 0 },
                    { k: 'matSupp_grises', label: 'Grises', def: 0 },
                    { k: 'matSupp_cremas', label: 'Cremas/Beiges', def: 5 },
                    { k: 'matSupp_verdes', label: 'Verdes', def: 15 },
                    { k: 'matSupp_azules', label: 'Azules', def: 15 },
                    { k: 'matSupp_calidos', label: 'Rojos/Cálidos', def: 15 },
                    { k: 'matSupp_maderas-claras', label: 'Maderas claras', def: 20 },
                    { k: 'matSupp_maderas-medias', label: 'Maderas medias (roble)', def: 25 },
                    { k: 'matSupp_maderas-oscuras', label: 'Maderas oscuras', def: 30 },
                    { k: 'matSupp_nogales', label: 'Nogales', def: 35 },
                    { k: 'matSupp_cerezos', label: 'Cerezos y otros', def: 35 },
                    { k: 'matSupp_metalizados', label: 'Metalizados', def: 40 },
                    { k: 'matSupp_piedras', label: 'Piedras/Cementos', def: 45 },
                    { k: 'matSupp_textiles', label: 'Textiles', def: 30 },
                    { k: 'matSupp_alvic', label: 'ALVIC (acabados)', def: 35 },
                    { k: 'matSupp_acb', label: 'ACB (puertas)', def: 30 },
                  ].map(f => (
                    <div key={f.k} className="bg-slate-50 border border-slate-200 rounded-xl p-2.5 hover:border-emerald-300 transition-colors">
                      <label className="text-[11px] font-bold text-slate-600 uppercase tracking-wide block truncate">{f.label}</label>
                      <div className="flex items-center gap-1 mt-1.5">
                        <input type="number" step="0.01" placeholder={String(f.def)}
                          defaultValue={state.settings?.['armPrice_' + f.k] ?? ''}
                          onBlur={(e) => saveSetting({ ['armPrice_' + f.k]: e.target.value === '' ? null : Number(e.target.value) })}
                          className="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded-lg text-sm outline-none focus:border-emerald-500 font-mono font-bold text-slate-900" />
                        <span className="text-[10px] font-bold text-slate-400 shrink-0">€/m²</span>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Márgenes Armarios */}
                <div className="mt-6 pt-5 border-t border-slate-200">
                  <div className="flex items-center gap-3 mb-1">
                    <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-600 flex items-center justify-center shrink-0"><Percent size={18} /></div>
                    <h3 className="text-base font-black text-slate-900 uppercase">Márgenes Armarios</h3>
                  </div>
                  <p className="text-xs text-slate-500 mb-4 ml-[52px]">Porcentaje de margen comercial aplicado al PVP del armario. Cada distribuidor puede tener su propio margen (se asigna en la ficha de usuario); aquí se define el <b>margen por defecto</b> para nuevos usuarios.</p>
                  <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
                    {[
                      { k: 'armMargin_default', label: 'Margen por defecto', def: 30 },
                      { k: 'armMargin_premium', label: 'Margen Premium', def: 35 },
                      { k: 'armMargin_basico', label: 'Margen Básico', def: 25 },
                      { k: 'armMargin_interior', label: 'Margen Interior', def: 20 },
                    ].map(f => (
                      <div key={f.k} className="bg-slate-50 border border-slate-200 rounded-xl p-2.5 hover:border-emerald-300 transition-colors">
                        <label className="text-[11px] font-bold text-slate-600 uppercase tracking-wide block truncate">{f.label}</label>
                        <div className="flex items-center gap-1 mt-1.5">
                          <input type="number" step="0.5" min="0" max="100" placeholder={String(f.def)}
                            defaultValue={state.settings?.[f.k] ?? ''}
                            onBlur={(e) => saveSetting({ [f.k]: e.target.value === '' ? null : Number(e.target.value) })}
                            className="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded-lg text-sm outline-none focus:border-emerald-500 font-mono font-bold text-slate-900" />
                          <span className="text-[10px] font-bold text-slate-400 shrink-0">%</span>
                        </div>
                      </div>
                    ))}
                  </div>
                  {/* Botón ver costos */}
                  <button
                    onClick={() => {
                      const base = state.settings?.armPrice_basePerM2 || 450;
                      const marginDef = state.settings?.armMargin_default || 30;
                      const pvp = base / (1 - marginDef / 100);
                      alert(`RESUMEN COSTOS ARMARIOS\n\nPrecio base: ${base} €/m²\nMargen por defecto: ${marginDef}%\nPVP resultante: ${pvp.toFixed(2)} €/m²\n\nFondo extra: ${state.settings?.armPrice_depthSuppPerMm || 0.5} €/mm\nP. corredera: ${state.settings?.armPrice_doorSlidingPerM2 || 180} €/m²\nP. plegable: ${state.settings?.armPrice_doorFoldingPerM2 || 250} €/m²`);
                    }}
                    className="mt-3 ml-[52px] flex items-center gap-2 px-4 py-2 bg-emerald-50 border border-emerald-200 rounded-lg text-xs font-bold text-emerald-700 hover:bg-emerald-100 transition-colors">
                    <Eye size={14} /> Ver costos resultantes
                  </button>
                </div>

                {/* Cocina Des-Montada (Cascos): el valor de punto se configura en Márgenes Maestros → Valor de Punto Base. */}
                <div className="mt-6 pt-5 border-t border-slate-200">
                  <h3 className="text-base font-black text-slate-900 uppercase">Cocina Des-Montada (Cascos)</h3>
                  <p className="text-xs text-slate-500">El <b>valor de punto</b> de Des-Montada se configura en <b>Márgenes Maestros → Valor de Punto Base → Cocina Des-Montada</b>. El <b>descuento por usuario</b> se asigna en cada ficha de usuario.</p>
                </div>
              </div>
            </div>
          )}

          {/* Tab Facturación */}
          {activeTab === 'billing' && (
            <div className="p-6 space-y-5 bg-slate-50">
              {billingMsg && (
                <div className="p-4 bg-emerald-100 border border-emerald-300 rounded-2xl text-emerald-900 font-bold text-sm flex items-center gap-2 animate-in fade-in">
                  <CheckCircle2 size={18} className="text-emerald-600 shrink-0" />
                  {billingMsg}
                </div>
              )}

              <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm">
                <div className="flex items-center justify-between gap-4 mb-4 flex-wrap">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-600 flex items-center justify-center shrink-0"><Building2 size={18} /></div>
                    <div>
                      <h3 className="text-base font-black text-slate-900 uppercase">Datos de Facturación</h3>
                      <p className="text-xs text-slate-500">Estos datos aparecerán en las facturas PDF generadas.</p>
                    </div>
                  </div>
                  <button
                    onClick={handleSaveBilling}
                    disabled={savingBilling}
                    className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-black text-xs rounded-xl shadow-md transition-all flex items-center gap-2"
                  >
                    {savingBilling ? <Loader2 size={15} className="animate-spin" /> : <Save size={15} />}
                    {savingBilling ? 'Guardando…' : '💾 Guardar Datos de Facturación'}
                  </button>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {[
                    { key: 'companyName', label: 'Nombre / Razón Social', placeholder: 'LUIGGI HOME S.L.' },
                    { key: 'companyTaxId', label: 'NIF / CIF', placeholder: 'B12345678' },
                    { key: 'companyAddress', label: 'Dirección fiscal', placeholder: 'Calle...' },
                    { key: 'companyPhone', label: 'Teléfono', placeholder: '+34 600 000 000' },
                    { key: 'companyEmail', label: 'Email de facturación', placeholder: 'facturacion@empresa.es' },
                    { key: 'companyIban', label: 'IBAN (datos bancarios)', placeholder: 'ES00 0000 0000 00 0000000000' },
                  ].map(field => (
                    <div key={field.key} className="bg-slate-50 border border-slate-200 rounded-xl p-3 hover:border-emerald-300 transition-colors">
                      <label className="text-[11px] font-bold text-slate-600 uppercase tracking-wide">{field.label}</label>
                      <input
                        type="text"
                        placeholder={field.placeholder}
                        value={billingForm[field.key] || ''}
                        onChange={(e) => setBillingForm({ ...billingForm, [field.key]: e.target.value })}
                        onBlur={(e) => saveSetting({ [field.key]: e.target.value })}
                        className="w-full mt-1.5 px-3 py-2 bg-white border border-slate-300 rounded-lg text-sm outline-none focus:border-emerald-500 font-bold text-slate-900"
                      />
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm">
                <h3 className="text-base font-black text-slate-900 uppercase mb-1">Centros / direcciones de envío</h3>
                <p className="text-xs text-slate-500 mb-3">Uno por línea, con el formato <b>Nombre — Dirección completa</b>. Aparecerán como opciones de "Centro de envío" al generar pedidos a proveedor.</p>
                <textarea
                  rows={4}
                  placeholder={"Central Cádiz — C/ Ejemplo 1, 11000 Cádiz\nAlmacén Sevilla — Pol. Ind. ..., 41000 Sevilla"}
                  value={billingForm.centrosEnvio || ''}
                  onChange={(e) => setBillingForm({ ...billingForm, centrosEnvio: e.target.value })}
                  onBlur={(e) => saveSetting({ centrosEnvio: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm font-mono outline-none focus:border-indigo-500"
                />
              </div>

              <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm">
                <div className="flex items-center gap-3 mb-1">
                  <div className="w-10 h-10 rounded-xl bg-indigo-100 text-indigo-600 flex items-center justify-center shrink-0"><RefreshCw size={18} /></div>
                  <h3 className="text-base font-black text-slate-900 uppercase">Email (envío de pedidos)</h3>
                </div>
                <p className="text-xs text-slate-500 mb-5 ml-[52px]">Para que los pedidos confirmados se envíen por email. Si se deja vacío, el pedido se confirma igual pero sin email.</p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 hover:border-emerald-300 transition-colors">
                    <label className="text-[11px] font-bold text-slate-600 uppercase tracking-wide">Email remitente</label>
                    <input
                      type="text"
                      placeholder="no-reply@luiggihome.es"
                      value={billingForm.emailSender || ''}
                      onChange={(e) => setBillingForm({ ...billingForm, emailSender: e.target.value })}
                      onBlur={(e) => saveSetting({ emailSender: e.target.value })}
                      className="w-full mt-1.5 px-3 py-2 bg-white border border-slate-300 rounded-lg text-sm outline-none focus:border-emerald-500 font-bold text-slate-900"
                    />
                  </div>
                  <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 hover:border-emerald-300 transition-colors">
                    <label className="text-[11px] font-bold text-slate-600 uppercase tracking-wide">SendGrid API Key</label>
                    <input
                      type="password"
                      autoComplete="new-password"
                      placeholder={state.settings?.sendgridConfigured ? '•••••••• (ya configurada)' : 'SG.xxxxx'}
                      value={billingForm.sendgridApiKey || ''}
                      onChange={(e) => setBillingForm({ ...billingForm, sendgridApiKey: e.target.value })}
                      className="w-full mt-1.5 px-3 py-2 bg-white border border-slate-300 rounded-lg text-sm outline-none focus:border-emerald-500 font-mono font-bold text-slate-900"
                    />
                  </div>
                </div>
              </div>

              {/* Botón flotante inferior de Guardar Todo */}
              <div className="pt-3 border-t border-slate-200 flex justify-end">
                <button
                  onClick={handleSaveBilling}
                  disabled={savingBilling}
                  className="w-full sm:w-auto px-8 py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-black text-sm rounded-xl shadow-lg transition-all flex items-center justify-center gap-2"
                >
                  {savingBilling ? <Loader2 size={18} className="animate-spin" /> : <Save size={18} />}
                  {savingBilling ? 'Guardando Cambios…' : '💾 GUARDAR DATOS DE FACTURACIÓN'}
                </button>
              </div>
            </div>
          )}

          {activeTab === 'backups' && (
            <div className="space-y-8">
              {/* Copias de la BASE DE DATOS: crear, DESCARGAR y restaurar */}
              <BackupManagementTab />
              {/* Copia por email/Drive y exportación a Excel */}
              <BackupsTab
              backups={backups}
              loadingBackups={loadingBackups}
              loadBackups={loadBackups}
              creatingBackup={creatingBackup}
              createManualBackup={createManualBackup}
              isExportingDB={isExportingDB}
              handleExportDatabase={handleExportDatabase}
            />
            </div>
          )}

          {/* Maintenance Tab Content */}
          {activeTab === 'maintenance' && (
            <MaintenanceTab
              maintenanceStatus={maintenanceStatus}
              maintenanceLoading={maintenanceLoading}
              maintenanceMessage={maintenanceMessage}
              setMaintenanceMessage={setMaintenanceMessage}
              maintenanceMinutes={maintenanceMinutes}
              setMaintenanceMinutes={setMaintenanceMinutes}
              maintenanceCreateBackup={maintenanceCreateBackup}
              setMaintenanceCreateBackup={setMaintenanceCreateBackup}
              maintenanceActivating={maintenanceActivating}
              maintenanceDeactivating={maintenanceDeactivating}
              handleActivateMaintenance={handleActivateMaintenance}
              handleDeactivateMaintenance={handleDeactivateMaintenance}
              maintenanceBackups={maintenanceBackups}
              loadMaintenanceBackups={loadMaintenanceBackups}
              handleDownloadMaintenanceBackup={handleDownloadMaintenanceBackup}
            />
          )}

          {/* Botón de migración: normalizar refs con espacios en fichas existentes */}
          {activeTab === 'maintenance' && state.currentUser?.isAdmin && (
            <div className="mt-6 border-t border-slate-200 pt-6">
              <h3 className="text-sm font-black uppercase tracking-wide text-slate-700 mb-2">Migración de datos</h3>
              <p className="text-xs text-slate-500 mb-3">
                Normaliza las referencias de todas las fichas de Rentabilidad eliminando espacios alrededor de la barra
                (p. ej. <code>LG26 / 61</code> → <code>LG26/61</code>) para que el filtro funcione correctamente.
              </p>
              <button
                onClick={async () => {
                  if (!window.confirm('¿Normalizar todas las referencias de Rentabilidad? Esta acción es segura y reversible.')) return;
                  try {
                    const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/rentabilidad/admin/normalize-refs`, {
                      method: 'POST', headers: authHeaders()
                    });
                    const data = await res.json();
                    alert(`✅ ${data.message}`);
                  } catch (e) {
                    alert('❌ Error al normalizar referencias: ' + e.message);
                  }
                }}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-bold hover:bg-indigo-700 transition-colors"
              >
                🔧 Normalizar referencias (LG26 / 61 → LG26/61)
              </button>
            </div>
          )}

          {activeTab === 'telemetry' && (
            <TelemetryTab state={state} setState={setState} />
          )}

          {activeTab === 'digitalizador-audit' && (
            <DigitalizadorAuditTab state={state} />
          )}

          {activeTab === 'telemetry-audit' && (
            <TelemetryAuditTab state={state} />
          )}

          {activeTab === 'identity' && (
            <IdentityTab state={state} setState={setState} />
          )}

          {/* SECURITY 2FA TAB */}
          {activeTab === 'security' && (
            <SecurityTab state={state} setState={setState} />
          )}
          
          {/* Nueva pestaña: Informe de Uso */}
          {activeTab === 'usage-report' && (
            <UsageReportTab />
          )}
          
          {/* Suscripciones SaaS */}
          {activeTab === 'subscriptions' && (
            <SubscriptionTab />
          )}
          {/* Costes de artículos (catálogo auditable) */}
          {activeTab === 'costes-articulos' && (
            <CostesArticulosTab />
          )}
          {/* Medidor de consumo IA por cliente + packs de renders */}
          {activeTab === 'ai-meter' && (
            <AIMeterTab />
          )}
        </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsModal;
