import React, { useState, useMemo } from 'react';
import { X, Users, Euro, Palette, Camera, Settings as SettingsIcon, Plus, Pencil, Trash2, Check, UserPlus, Shield, Store, Briefcase, Search, Package, Save, CheckSquare, Square, Loader } from 'lucide-react';
import { usersAPI, productsAPI, materialsAPI, settingsAPI } from '../services/api';

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
    linkedRepresentativeId: '',
    allowedModules: ['montada'],
    commercialDiscount: 0,
    canSeeCost: false,
    canSeeRetail: true,
    canUseAIAnalysis: false,
    canManageArticles: false,
    canViewTechnicalDespiece: false,
    useCustomBranding: false,
    canChangeLogo: false
  });

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
    return currentCatalog.products.filter(p =>
      p.code.toLowerCase().includes(query) ||
      p.name.toLowerCase().includes(query)
    );
  }, [currentCatalog, productSearch]);

  if (!isOpen) return null;

  const handleColorChange = () => {
    setState(prev => ({ ...prev, brandColor: colorInput }));
  };

  const handleLogoUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setState(prev => ({ ...prev, logo: e.target.result }));
      };
      reader.readAsDataURL(file);
    }
  };

  const handleCreateUser = () => {
    setIsEditingUser(true);
    setEditingUserId(null);
    
    // Si es comercial, automáticamente crear como tienda asignada a él
    const isCommercial = !state.currentUser?.isAdmin && state.currentUser?.isRepresentative;
    
    setUserForm({
      username: '',
      password: '',
      clientName: '',
      isActive: true,
      isAdmin: false,
      isRepresentative: false,
      linkedRepresentativeId: isCommercial ? state.currentUser.id : '',
      allowedModules: ['montada'],
      allowedCatalogIds: state.catalogs.map(c => c.id),
      commercialDiscount: 0,
      canSeeCost: false,
      canSeeRetail: true,
      canUseAIAnalysis: false,
      canManageArticles: false,
      canViewTechnicalDespiece: false,
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
    
    setIsEditingUser(true);
    setEditingUserId(user.id);
    setUserForm({ ...user });
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
        )
      }));
    } else {
      // Create new
      const newMaterial = {
        ...materialForm,
        id: `mat-${Date.now()}`
      };
      setState(prev => ({
        ...prev,
        carcassMaterials: [...prev.carcassMaterials, newMaterial]
      }));
    }

    setIsEditingMaterial(false);
    setEditingMaterialId(null);
  };

  const handleDeleteMaterial = (materialId) => {
    if (state.carcassMaterials.length <= 1) {
      alert('Debe existir al menos un material de armazón');
      return;
    }
    
    if (window.confirm('¿Eliminar este material de armazón?')) {
      setState(prev => ({
        ...prev,
        carcassMaterials: prev.carcassMaterials.filter(m => m.id !== materialId),
        selectedCarcassMaterialId: prev.selectedCarcassMaterialId === materialId 
          ? prev.carcassMaterials[0].id 
          : prev.selectedCarcassMaterialId
      }));
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
                              <div className={`p-2 rounded-lg ${user.isAdmin ? 'bg-orange-100' : user.isRepresentative ? 'bg-purple-100' : 'bg-indigo-100'}`}>
                                {user.isAdmin ? <Shield size={20} className="text-orange-600" /> : 
                                 user.isRepresentative ? <Briefcase size={20} className="text-purple-600" /> :
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
                                  {user.isAdmin ? '🛡️ Admin Maestro' : user.isRepresentative ? '💼 Comercial' : '🏪 Tienda'}
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
                              {user.canUseAIAnalysis && <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded text-[9px] font-black">IA LAB</span>}
                              {user.canSeeCost && <span className="px-2 py-1 bg-orange-100 text-orange-700 rounded text-[9px] font-black">VER COSTO</span>}
                              {user.canViewTechnicalDespiece && <span className="px-2 py-1 bg-indigo-100 text-indigo-700 rounded text-[9px] font-black">INFORMES</span>}
                              {user.canManageArticles && <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-[9px] font-black">INVENTARIO</span>}
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
                              onChange={(e) => setUserForm({...userForm, isRepresentative: e.target.checked})}
                              className="w-5 h-5 rounded border-2 border-orange-300"
                            />
                            <div>
                              <span className="text-sm font-black text-slate-900">Comercial / Representante</span>
                              <p className="text-xs text-slate-500">Puede tener tiendas asignadas</p>
                            </div>
                          </label>

                          {!userForm.isAdmin && !userForm.isRepresentative && representatives.length > 0 && (
                            <div>
                              <label className="text-xs font-black text-slate-600 uppercase mb-2 block">Asignar a Comercial</label>
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
                            <th className="p-3 text-center text-[9px] font-black uppercase whitespace-nowrap">GESTIÓN</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {filteredProducts.length === 0 ? (
                            <tr>
                              <td colSpan={inventoryModule === 'montada' ? 16 : 6} className="p-8 text-center text-slate-400 italic">
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
                                <td className="p-3">
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
                <div className="grid grid-cols-3 gap-4">
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
                </div>
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
