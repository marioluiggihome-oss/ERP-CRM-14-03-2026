import React, { useState, useMemo, useEffect } from 'react';
import { X, Users, Euro, Palette, Camera, Settings as SettingsIcon, Plus, Pencil, Trash2, Check, UserPlus, Shield, Store, Briefcase, Search, Package, Save, CheckSquare, Square, Loader, Zap, Upload, FileImage, XCircle, RefreshCw, CheckCircle, Building2, FileSpreadsheet, Download, HardDrive, Database, Clock, AlertTriangle, Wrench, Power, ShieldAlert, Timer } from 'lucide-react';
import { usersAPI, productsAPI, materialsAPI, settingsAPI, clientsAPI } from '../services/api';
import CatalogImporter from './CatalogImporter';
import { getProductIcon } from './FurnitureIcons';

const SettingsModal = ({ isOpen, onClose, state, setState }) => {
  const [activeTab, setActiveTab] = useState('users');
  const [colorInput, setColorInput] = useState(state.brandColor || '#ea580c');
  const [userSearch, setUserSearch] = useState('');
  const [isEditingUser, setIsEditingUser] = useState(false);
  const [editingUserId, setEditingUserId] = useState(null);
  const [isSaving, setIsSaving] = useState(false);
  
  // Inventory states
  const [inventoryModule, setInventoryModule] = useState('montada');
  const [productSearch, setProductSearch] = useState('');
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
  const [materialForm, setMaterialForm] = useState({
    name: '',
    fixedIncrement: 0,
    thickness: 16
  });
  const [userForm, setUserForm] = useState({
    username: '',
    password: '',
    clientName: '',
    isActive: true,
    isAdmin: false,
    isRepresentative: false,
    isPrescriptor: false,
    isTienda: false,  // Tienda/Punto de Venta
    linkedRepresentativeId: '',
    allowedModules: ['montada'],
    commercialDiscount: 0,
    canSeeCost: false,
    canSeeRetail: true,
    canUseAIAnalysis: false,
    canManageArticles: false,
    canViewTechnicalDespiece: false,
    canAccessCRM: false,
    canUseDigitalizador: false,
    canAccessArmarios: false,
    useCustomBranding: false,
    canChangeLogo: false,
    linkedClientId: ''
  });

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
  const [maintenanceMessage, setMaintenanceMessage] = useState('Sistema en actualización. Volvemos pronto.');
  const [maintenanceMinutes, setMaintenanceMinutes] = useState(30);
  const [maintenanceCreateBackup, setMaintenanceCreateBackup] = useState(true);

  // Load clients and segments when tab is active
  useEffect(() => {
    if (isOpen && activeTab === 'clients') {
      loadClients();
      loadSegments();
    }
  }, [isOpen, activeTab]);

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

  const representatives = useMemo(() => state.users.filter(u => u.isRepresentative), [state.users]);

  // Filtrar usuarios según el rol del usuario actual
  const visibleUsers = useMemo(() => {
    if (state.currentUser?.isAdmin) {
      // Admins ven todos los usuarios
      return state.users;
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
    return visibleUsers.filter(u => 
      u.username.toLowerCase().includes(query) || 
      u.clientName.toLowerCase().includes(query)
    );
  }, [visibleUsers, userSearch]);

  // Product management  
  const currentCatalog = useMemo(() => {
    return state.catalogs.find(c => c.module === inventoryModule);
  }, [state.catalogs, inventoryModule]);

  const filteredProducts = useMemo(() => {
    if (!currentCatalog) return [];
    const query = productSearch.toLowerCase();
    const filtered = currentCatalog.products.filter(p =>
      p.code.toLowerCase().includes(query) ||
      p.name.toLowerCase().includes(query)
    );
    // Ordenar por código de referencia
    return filtered.sort((a, b) => (a.code || '').localeCompare(b.code || ''));
  }, [currentCatalog, productSearch]);

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
    const isCommercial = !state.currentUser?.isAdmin && state.currentUser?.isRepresentative;
    
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
      isRepresentative: false,
      isPrescriptor: false,
      isTienda: false,
      linkedRepresentativeId: isCommercial ? state.currentUser.id : '',
      allowedModules: ['montada'],
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
      useCustomBranding: false,
      canChangeLogo: false
    });
  };

  const handleEditUser = (user) => {
    // Comerciales solo pueden editar tiendas asignadas a ellos
    if (!state.currentUser?.isAdmin && state.currentUser?.isRepresentative) {
      if (user.linkedRepresentativeId !== state.currentUser.id && user.id !== state.currentUser.id) {
        alert('No tienes permisos para editar este usuario');
        return;
      }
    }
    
    // Load clients if not already loaded
    if (clients.length === 0) {
      loadClients();
    }
    
    setIsEditingUser(true);
    setEditingUserId(user.id);
    setUserForm({ ...user, linkedClientId: user.linkedClientId || '' });
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
    if (!state.currentUser?.isAdmin && state.currentUser?.isRepresentative) {
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
    setMaterialForm({ name: '', fixedIncrement: 0, thickness: 16 });
  };

  const handleEditMaterial = (material) => {
    setIsEditingMaterial(true);
    setEditingMaterialId(material.id);
    setMaterialForm({
      name: material.name,
      fixedIncrement: material.fixedIncrement || 0,
      thickness: material.thickness || 16
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
      <div className="bg-white rounded-3xl shadow-2xl w-full max-w-5xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-8 py-6 border-b border-slate-100 flex justify-between items-center bg-gradient-to-r from-indigo-950 to-indigo-900">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-white/10 rounded-xl">
              <SettingsIcon size={24} className="text-white" />
            </div>
            <div>
              <h2 className="text-2xl font-black text-white uppercase tracking-tight">Panel Maestro</h2>
              <p className="text-xs font-bold text-indigo-300 uppercase tracking-wider">Configuración Industrial</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-xl transition-all">
            <X size={24} className="text-white" />
          </button>
        </div>

        {/* Tabs */}
        <div className="px-8 py-4 bg-slate-50 border-b border-slate-200 flex gap-3 overflow-x-auto">
          <button
            onClick={() => setActiveTab('users')}
            className={`flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-black uppercase tracking-wide transition-all whitespace-nowrap ${
              activeTab === 'users' ? 'bg-indigo-600 text-white shadow-lg' : 'text-slate-500 hover:bg-white hover:text-slate-700'
            }`}
          >
            <Users size={16} />
            Red Distribución
          </button>
          
          {/* Tab Clientes - Solo Admin */}
          {state.currentUser?.isAdmin && (
            <button
              onClick={() => setActiveTab('clients')}
              className={`flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-black uppercase tracking-wide transition-all whitespace-nowrap ${
                activeTab === 'clients' ? 'bg-emerald-600 text-white shadow-lg' : 'text-slate-500 hover:bg-white hover:text-slate-700'
              }`}
              data-testid="clients-tab"
            >
              <Building2 size={16} />
              Clientes
            </button>
          )}
          
          {/* Solo Admin y Comerciales con permiso canManageArticles pueden ver Inventario */}
          {(state.currentUser?.isAdmin || state.currentUser?.canManageArticles) && (
            <button
              onClick={() => setActiveTab('inventory')}
              className={`flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-black uppercase tracking-wide transition-all whitespace-nowrap ${
                activeTab === 'inventory' ? 'bg-indigo-600 text-white shadow-lg' : 'text-slate-500 hover:bg-white hover:text-slate-700'
              }`}
            >
              <Package size={16} />
              Inventario
            </button>
          )}
          
          {/* Solo Admin y Comerciales con permiso canManageArticles pueden ver Márgenes */}
          {(state.currentUser?.isAdmin || state.currentUser?.canManageArticles) && (
            <button
              onClick={() => setActiveTab('pricing')}
              className={`flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-black uppercase tracking-wide transition-all whitespace-nowrap ${
                activeTab === 'pricing' ? 'bg-indigo-600 text-white shadow-lg' : 'text-slate-500 hover:bg-white hover:text-slate-700'
              }`}
            >
              <Euro size={16} />
              Márgenes
            </button>
          )}
          
          {/* Tab Armazones - Separada */}
          {(state.currentUser?.isAdmin || state.currentUser?.canManageArticles) && (
            <button
              onClick={() => setActiveTab('armazones')}
              className={`flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-black uppercase tracking-wide transition-all whitespace-nowrap ${
                activeTab === 'armazones' ? 'bg-amber-600 text-white shadow-lg' : 'text-slate-500 hover:bg-white hover:text-slate-700'
              }`}
              data-testid="armazones-tab"
            >
              <Package size={16} />
              Armazones
            </button>
          )}
          
          {/* Tab Backups - Solo Admin */}
          {state.currentUser?.isAdmin && (
            <button
              onClick={() => setActiveTab('backups')}
              className={`flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-black uppercase tracking-wide transition-all whitespace-nowrap ${
                activeTab === 'backups' ? 'bg-orange-600 text-white shadow-lg' : 'text-slate-500 hover:bg-white hover:text-slate-700'
              }`}
              data-testid="backups-tab"
            >
              <HardDrive size={16} />
              Backups
            </button>
          )}
          
          {/* Pestaña Mantenimiento - Solo Admin */}
          {state.currentUser?.isAdmin && (
            <button
              onClick={() => setActiveTab('maintenance')}
              className={`flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-black uppercase tracking-wide transition-all whitespace-nowrap ${
                activeTab === 'maintenance' ? 'bg-red-600 text-white shadow-lg' : 'text-slate-500 hover:bg-white hover:text-slate-700'
              }`}
              data-testid="maintenance-tab"
            >
              <Wrench size={16} />
              Mantenimiento
            </button>
          )}
          
          {state.currentUser?.isAdmin && (
            <button
              onClick={() => setActiveTab('telemetry')}
              className={`flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-black uppercase tracking-wide transition-all whitespace-nowrap ${
                activeTab === 'telemetry' ? 'bg-orange-500 text-white shadow-lg' : 'text-slate-500 hover:bg-white hover:text-slate-700'
              }`}
            >
              <Zap size={16} />
              Telemetría IA
            </button>
          )}
          
          <button
            onClick={() => setActiveTab('identity')}
            className={`flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-black uppercase tracking-wide transition-all whitespace-nowrap ${
              activeTab === 'identity' ? 'bg-indigo-600 text-white shadow-lg' : 'text-slate-500 hover:bg-white hover:text-slate-700'
            }`}
          >
            <Camera size={16} />
            Identidad
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-8">
          {activeTab === 'users' && (
            <div className="space-y-6">
              {!isEditingUser ? (
                <>
                  {/* Header with search and add button */}
                  <div className="flex justify-between items-center mb-6">
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
                      {state.currentUser?.isAdmin ? 'Nuevo Usuario' : 'Nueva Tienda'}
                    </button>
                  </div>

                  {/* Users List */}
                  <div className="space-y-3">
                    {filteredUsers.map(user => (
                      <div key={user.id} className="bg-white border border-slate-200 rounded-xl p-4 hover:shadow-md transition-all">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                              <div className={`p-2 rounded-lg ${user.isAdmin ? 'bg-orange-100' : user.isRepresentative ? 'bg-purple-100' : user.isPrescriptor ? 'bg-amber-100' : user.isTienda ? 'bg-green-100' : 'bg-indigo-100'}`}>
                                {user.isAdmin ? <Shield size={20} className="text-orange-600" /> : 
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
                                  {user.isAdmin ? '🛡️ Admin Maestro' : user.isRepresentative ? '💼 Comercial/Rep.' : user.isPrescriptor ? '🤝 Colaborador' : user.isTienda ? '🏪 Punto de Venta' : '🏪 Tienda'}
                                </p>
                              </div>
                              <div className="bg-slate-50 p-2 rounded-lg">
                                <p className="text-[9px] font-black text-slate-400 uppercase mb-1">Descuento</p>
                                <p className="text-xs font-bold text-orange-600">{user.commercialDiscount}%</p>
                              </div>
                              <div className="bg-slate-50 p-2 rounded-lg">
                                <p className="text-[9px] font-black text-slate-400 uppercase mb-1">Módulos</p>
                                <p className="text-xs font-bold text-indigo-600">
                                  {user.allowedModules?.join(', ').toUpperCase() || 'N/A'}
                                </p>
                              </div>
                            </div>

                            {/* Capabilities badges */}
                            <div className="flex flex-wrap gap-1 mt-3">
                              {user.canAccessArmarios && <span className="px-2 py-1 bg-cyan-100 text-cyan-700 rounded text-[9px] font-black">ARMARIOS</span>}
                              {user.canUseAIAnalysis && <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded text-[9px] font-black">IA LAB</span>}
                              {user.canSeeCost && <span className="px-2 py-1 bg-orange-100 text-orange-700 rounded text-[9px] font-black">VER COSTO</span>}
                              {user.canViewTechnicalDespiece && <span className="px-2 py-1 bg-indigo-100 text-indigo-700 rounded text-[9px] font-black">INFORMES</span>}
                              {user.canManageArticles && <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-[9px] font-black">INVENTARIO</span>}
                              {user.canAccessCRM && <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-[9px] font-black">CRM</span>}
                              {user.canUseDigitalizador && <span className="px-2 py-1 bg-amber-100 text-amber-700 rounded text-[9px] font-black">DIGITALIZADOR</span>}
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
                        <label className="text-xs font-black text-slate-600 uppercase mb-2 block">Nombre Público Tienda *</label>
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
                    {state.currentUser?.isAdmin && (
                      <div className="bg-orange-50 p-4 rounded-xl border border-orange-100">
                        <h4 className="text-sm font-black text-orange-900 uppercase mb-3">Rol y Jerarquía</h4>
                        <div className="space-y-3">
                          <label className="flex items-center gap-3 cursor-pointer">
                            <input
                              type="checkbox"
                              checked={userForm.isAdmin}
                              onChange={(e) => setUserForm({...userForm, isAdmin: e.target.checked})}
                              className="w-5 h-5 rounded border-2 border-orange-300"
                            />
                            <div>
                              <span className="text-sm font-black text-slate-900">Administrador Maestro</span>
                              <p className="text-xs text-slate-500">Control total del sistema</p>
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

                          {/* Checkbox Colaborador Comercial - Solo visible para Admin */}
                          {state.currentUser?.isAdmin && (
                            <label className="flex items-center gap-3 cursor-pointer p-3 bg-amber-50 rounded-xl border border-amber-200">
                              <input
                                type="checkbox"
                                checked={userForm.isPrescriptor}
                                onChange={(e) => setUserForm({...userForm, isPrescriptor: e.target.checked, isRepresentative: false, isTienda: false})}
                                className="w-5 h-5 rounded border-2 border-amber-300"
                              />
                              <div>
                                <span className="text-sm font-black text-slate-900">Colaborador Comercial</span>
                                <p className="text-xs text-slate-500">Solo aporta contactos/clientes potenciales (gestionado por Admin)</p>
                              </div>
                            </label>
                          )}

                          {/* Checkbox Tienda/Punto de Venta - Solo visible para Admin */}
                          {state.currentUser?.isAdmin && (
                            <label className="flex items-center gap-3 cursor-pointer p-3 bg-green-50 rounded-xl border border-green-200">
                              <input
                                type="checkbox"
                                checked={userForm.isTienda}
                                onChange={(e) => setUserForm({...userForm, isTienda: e.target.checked, isRepresentative: false, isPrescriptor: false, isAdmin: false})}
                                className="w-5 h-5 rounded border-2 border-green-300"
                              />
                              <div>
                                <span className="text-sm font-black text-slate-900">Tienda / Punto de Venta</span>
                                <p className="text-xs text-slate-500">Solo acceso al presupuestador (sin CRM ni panel maestro)</p>
                              </div>
                            </label>
                          )}

                          {!userForm.isAdmin && !userForm.isRepresentative && !userForm.isPrescriptor && !userForm.isTienda && representatives.length > 0 && (
                            <div>
                              <label className="text-xs font-black text-slate-600 uppercase mb-2 block">Asignar a Comercial / Representante</label>
                              <select
                                value={userForm.linkedRepresentativeId || ''}
                                onChange={(e) => setUserForm({...userForm, linkedRepresentativeId: e.target.value})}
                                className="w-full bg-white border border-orange-200 rounded-xl p-3 text-sm font-bold outline-none"
                              >
                                <option value="">Sin comercial asignado</option>
                                {representatives.map(rep => (
                                  <option key={rep.id} value={rep.id}>{rep.clientName}</option>
                                ))}
                              </select>
                            </div>
                          )}

                          {/* Vincular a Cliente Activo */}
                          {state.currentUser?.isAdmin && clients.length > 0 && (
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
                    {!state.currentUser?.isAdmin && state.currentUser?.isRepresentative && (
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
                      <div className="flex gap-3">
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
                      </div>
                    </div>

                    {/* Technical Capabilities */}
                    <div className="bg-purple-50 p-4 rounded-xl border border-purple-100">
                      <h4 className="text-sm font-black text-purple-900 uppercase mb-3">Capacidades Técnicas</h4>
                      <div className="grid grid-cols-2 gap-3">
                        <label className="flex items-center gap-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={userForm.canUseAIAnalysis}
                            onChange={(e) => setUserForm({...userForm, canUseAIAnalysis: e.target.checked})}
                            className="w-4 h-4 rounded"
                          />
                          <span className="text-xs font-bold text-slate-900">IA Lab (Reconocimiento)</span>
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={userForm.canSeeCost}
                            onChange={(e) => setUserForm({...userForm, canSeeCost: e.target.checked})}
                            className="w-4 h-4 rounded"
                          />
                          <span className="text-xs font-bold text-slate-900">Visualizar Costo Fábrica</span>
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={userForm.canViewTechnicalDespiece}
                            onChange={(e) => setUserForm({...userForm, canViewTechnicalDespiece: e.target.checked})}
                            className="w-4 h-4 rounded"
                          />
                          <span className="text-xs font-bold text-slate-900">Informes Industriales</span>
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={userForm.canManageArticles}
                            onChange={(e) => setUserForm({...userForm, canManageArticles: e.target.checked})}
                            className="w-4 h-4 rounded"
                          />
                          <span className="text-xs font-bold text-slate-900">Gestionar Inventario</span>
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={userForm.canAccessCRM}
                            onChange={(e) => setUserForm({...userForm, canAccessCRM: e.target.checked})}
                            className="w-4 h-4 rounded"
                          />
                          <span className="text-xs font-bold text-slate-900">Acceso al CRM</span>
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={userForm.canUseDigitalizador}
                            onChange={(e) => setUserForm({...userForm, canUseDigitalizador: e.target.checked})}
                            className="w-4 h-4 rounded"
                          />
                          <span className="text-xs font-bold text-slate-900">Digitalizador Borradores</span>
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={userForm.canAccessArmarios}
                            onChange={(e) => setUserForm({...userForm, canAccessArmarios: e.target.checked})}
                            className="w-4 h-4 rounded"
                          />
                          <span className="text-xs font-bold text-slate-900">Diseñador de Armarios</span>
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={userForm.useCustomBranding}
                            onChange={(e) => setUserForm({...userForm, useCustomBranding: e.target.checked})}
                            className="w-4 h-4 rounded"
                          />
                          <span className="text-xs font-bold text-slate-900">Personalizar Interfaz</span>
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer">
                          <input
                            type="checkbox"
                            checked={userForm.canChangeLogo}
                            onChange={(e) => setUserForm({...userForm, canChangeLogo: e.target.checked})}
                            className="w-4 h-4 rounded"
                          />
                          <span className="text-xs font-bold text-slate-900">Modificar Logo Corporativo</span>
                        </label>
                      </div>
                    </div>

                    {/* Commercial Discount */}
                    <div className="bg-green-50 p-4 rounded-xl border border-green-100">
                      <h4 className="text-sm font-black text-green-900 uppercase mb-3">Descuento Comercial Base (%)</h4>
                      <div className="flex items-center gap-4">
                        <input
                          type="range"
                          min="0"
                          max="100"
                          value={userForm.commercialDiscount}
                          onChange={(e) => setUserForm({...userForm, commercialDiscount: parseInt(e.target.value)})}
                          className="flex-1"
                        />
                        <input
                          type="number"
                          min="0"
                          max="100"
                          value={userForm.commercialDiscount}
                          onChange={(e) => setUserForm({...userForm, commercialDiscount: parseInt(e.target.value) || 0})}
                          className="w-20 bg-white border-2 border-green-300 rounded-xl p-2 text-center text-lg font-black text-green-700 outline-none"
                        />
                        <span className="text-sm font-black text-green-700">%</span>
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
                                        await clientsAPI.delete(client.id);
                                        loadClients();
                                      } catch (err) {
                                        alert(err.message);
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
                  {/* Header with module selector, search and add button */}
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
                    </div>
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
                            <th className="p-2 text-center text-[9px] font-black uppercase whitespace-nowrap w-12"></th>
                            <th className="p-3 text-left text-[9px] font-black uppercase whitespace-nowrap">REF</th>
                            <th className="p-3 text-left text-[9px] font-black uppercase min-w-[200px]">NOMBRE</th>
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
                              <td colSpan={inventoryModule === 'montada' ? 17 : 7} className="p-8 text-center text-slate-400 italic">
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
                                <td className="p-2 w-12">
                                  <div 
                                    className="w-10 h-10 flex items-center justify-center text-indigo-600"
                                    dangerouslySetInnerHTML={{ __html: getProductIcon(product.code, product.name) }}
                                  />
                                </td>
                                <td className="p-3 text-xs font-black text-orange-600 uppercase">{product.code}</td>
                                <td className="p-3 text-xs font-bold text-slate-900">{product.name}</td>
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
                      // Refresh catalog after import
                      loadCatalogs();
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

              {/* Valores de Punto */}
              <div className="bg-white border border-indigo-100 rounded-2xl p-6 shadow-sm">
                <h3 className="text-sm font-black text-indigo-900 uppercase tracking-widest mb-4 flex items-center gap-2">
                  💰 Valor de Punto Base
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs font-black text-indigo-400 uppercase mb-2 block">Montada (€/punto)</label>
                    <input
                      type="number"
                      step="0.01"
                      value={state.pointValueMontada}
                      onChange={(e) => setState(prev => ({ ...prev, pointValueMontada: parseFloat(e.target.value) || 1.0 }))}
                      className="w-full bg-indigo-50 border-2 border-indigo-200 rounded-xl p-4 text-2xl font-black text-indigo-900 outline-none focus:border-orange-500 text-center"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-black text-indigo-400 uppercase mb-2 block">Despiece (€/punto)</label>
                    <input
                      type="number"
                      step="0.01"
                      value={state.pointValueDespiece}
                      onChange={(e) => setState(prev => ({ ...prev, pointValueDespiece: parseFloat(e.target.value) || 0.88 }))}
                      className="w-full bg-indigo-50 border-2 border-indigo-200 rounded-xl p-4 text-2xl font-black text-indigo-900 outline-none focus:border-orange-500 text-center"
                    />
                  </div>
                </div>
              </div>

              {/* Incrementos Cortes Especiales */}
              <div className="bg-white border border-orange-100 rounded-2xl p-6 shadow-sm">
                <h3 className="text-sm font-black text-orange-900 uppercase tracking-widest mb-4 flex items-center gap-2">
                  ✂️ Incrementos Cortes Especiales
                </h3>
                <div className="grid grid-cols-4 gap-4">
                  <div>
                    <label className="text-xs font-black text-orange-400 uppercase mb-2 block">Ancho (€)</label>
                    <input
                      type="number"
                      value={state.specialIncrementWidth}
                      onChange={(e) => setState(prev => ({ ...prev, specialIncrementWidth: parseInt(e.target.value) || 45 }))}
                      className="w-full bg-orange-50 border-2 border-orange-200 rounded-xl p-4 text-2xl font-black text-orange-900 outline-none focus:border-orange-500 text-center"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-black text-orange-400 uppercase mb-2 block">Alto (€)</label>
                    <input
                      type="number"
                      value={state.specialIncrementHeight}
                      onChange={(e) => setState(prev => ({ ...prev, specialIncrementHeight: parseInt(e.target.value) || 45 }))}
                      className="w-full bg-orange-50 border-2 border-orange-200 rounded-xl p-4 text-2xl font-black text-orange-900 outline-none focus:border-orange-500 text-center"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-black text-orange-400 uppercase mb-2 block">Fondo (€)</label>
                    <input
                      type="number"
                      value={state.specialIncrementDepth}
                      onChange={(e) => setState(prev => ({ ...prev, specialIncrementDepth: parseInt(e.target.value) || 45 }))}
                      className="w-full bg-orange-50 border-2 border-orange-200 rounded-xl p-4 text-2xl font-black text-orange-900 outline-none focus:border-orange-500 text-center"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-black text-amber-600 uppercase mb-2 block">🪵 Corte Viga (€)</label>
                    <input
                      type="number"
                      step="0.5"
                      value={state.vigaCutIncrement || 0}
                      onChange={(e) => setState(prev => ({ ...prev, vigaCutIncrement: parseFloat(e.target.value) || 0 }))}
                      className="w-full bg-amber-50 border-2 border-amber-300 rounded-xl p-4 text-2xl font-black text-amber-800 outline-none focus:border-amber-500 text-center"
                    />
                  </div>
                </div>
                <p className="text-xs text-slate-500 mt-3 italic">Los incrementos se aplican por línea cuando hay corte especial o corte de viga activado.</p>
              </div>

              {/* Gestión de Armazones */}
              <div className="bg-white border border-purple-100 rounded-2xl p-6 shadow-sm">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-sm font-black text-purple-900 uppercase tracking-widest flex items-center gap-2">
                    🏗️ Gestión de Armazones / Cascos
                  </h3>
                  {!isEditingMaterial && (
                    <button
                      onClick={handleCreateMaterial}
                      className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-xl font-black uppercase text-[10px] hover:bg-purple-700 transition-all shadow-md"
                    >
                      <Plus size={16} />
                      Nuevo Material
                    </button>
                  )}
                </div>

                {!isEditingMaterial ? (
                  <div className="space-y-3">
                    {state.carcassMaterials.map(material => (
                      <div key={material.id} className="bg-purple-50 border border-purple-200 rounded-xl p-4 flex justify-between items-center hover:shadow-md transition-all">
                        <div className="flex-1">
                          <h4 className="text-sm font-black text-purple-900">{material.name}</h4>
                          <div className="flex gap-4 mt-2">
                            <span className="text-xs text-purple-600 font-bold">
                              Incremento: <span className="text-orange-600">+{material.fixedIncrement}€</span>
                            </span>
                            <span className="text-xs text-purple-600 font-bold">
                              Grosor: <span className="text-indigo-600">{material.thickness}mm</span>
                            </span>
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleEditMaterial(material)}
                            className="p-2 hover:bg-purple-100 rounded-lg transition-all"
                            title="Editar"
                          >
                            <Pencil size={16} className="text-purple-600" />
                          </button>
                          <button
                            onClick={() => handleDeleteMaterial(material.id)}
                            className="p-2 hover:bg-red-100 rounded-lg transition-all"
                            title="Eliminar"
                          >
                            <Trash2 size={16} className="text-red-600" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  /* Material Form */
                  <div className="bg-purple-50 border-2 border-purple-300 rounded-xl p-6">
                    <h4 className="text-sm font-black text-purple-900 uppercase mb-4">
                      {editingMaterialId ? 'Editar Material' : 'Nuevo Material'}
                    </h4>
                    <div className="space-y-4">
                      <div>
                        <label className="text-xs font-black text-purple-600 uppercase mb-2 block">Nombre del Material *</label>
                        <input
                          type="text"
                          value={materialForm.name}
                          onChange={(e) => setMaterialForm({...materialForm, name: e.target.value})}
                          placeholder="Ej: Blanco Ártico Standard"
                          className="w-full bg-white border border-purple-200 rounded-xl p-3 text-sm font-bold outline-none focus:border-orange-500"
                        />
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="text-xs font-black text-purple-600 uppercase mb-2 block">Incremento Fijo (€)</label>
                          <input
                            type="number"
                            value={materialForm.fixedIncrement}
                            onChange={(e) => setMaterialForm({...materialForm, fixedIncrement: parseInt(e.target.value) || 0})}
                            className="w-full bg-white border border-purple-200 rounded-xl p-3 text-lg font-black text-center text-orange-600 outline-none focus:border-orange-500"
                          />
                        </div>
                        <div>
                          <label className="text-xs font-black text-purple-600 uppercase mb-2 block">Grosor (mm)</label>
                          <input
                            type="number"
                            value={materialForm.thickness}
                            onChange={(e) => setMaterialForm({...materialForm, thickness: parseInt(e.target.value) || 16})}
                            className="w-full bg-white border border-purple-200 rounded-xl p-3 text-lg font-black text-center text-indigo-600 outline-none focus:border-orange-500"
                          />
                        </div>
                      </div>
                      <div className="flex gap-3 pt-2">
                        <button
                          onClick={handleSaveMaterial}
                          className="flex-1 bg-purple-600 text-white py-3 rounded-xl font-black uppercase text-xs hover:bg-purple-700 transition-all shadow-lg flex items-center justify-center gap-2"
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
              </div>
            </div>
          )}

          {/* Tab Armazones - Separada */}
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
                    <p className="text-xs text-indigo-400">Configura los materiales de estructura</p>
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
                  {state.carcassMaterials.map(material => (
                    <div key={material.id} className="bg-white border border-amber-200 rounded-xl p-5 hover:shadow-lg transition-all">
                      <div className="flex justify-between items-start mb-3">
                        <h4 className="text-base font-black text-amber-900">{material.name}</h4>
                        <div className="flex gap-1">
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
                      {material.id === state.selectedCarcassMaterialId && (
                        <div className="mt-3 px-3 py-1.5 bg-emerald-100 text-emerald-700 rounded-lg text-[10px] font-bold text-center uppercase">
                          Seleccionado como predeterminado
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                /* Material Form */
                <div className="bg-amber-50 border-2 border-amber-300 rounded-xl p-6 max-w-lg mx-auto">
                  <h4 className="text-sm font-black text-amber-900 uppercase mb-4">
                    {editingMaterialId ? 'Editar Material' : 'Nuevo Material'}
                  </h4>
                  <div className="space-y-4">
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
                              addLog({ type: 'info', msg: `IA detectó ${result.products.length} producto(s)` });
                              const newP = [], dupP = [];
                              for (let i = 0; i < result.products.length; i++) {
                                const p = result.products[i];
                                setTelemetryProgress({ current: i + 1, total: result.products.length });
                                await new Promise(r => setTimeout(r, 80));
                                if (existingCodes.has(p.code)) { dupP.push(p); addLog({ type: 'dup', code: p.code, name: p.name, pts: p.points || 0 }); }
                                else { newP.push(p); addLog({ type: 'new', code: p.code, name: p.name, pts: p.points || 0 }); setExistingCodes(prev => new Set([...prev, p.code])); }
                              }
                              if (newP.length > 0) { await productsAPI.bulkCreate(newP); addLog({ type: 'ok', msg: `${newP.length} guardado(s)` }); }
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
        </div>
      </div>
    </div>
  );
};

export default SettingsModal;
