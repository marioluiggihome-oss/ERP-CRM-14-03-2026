import React, { useState, useMemo } from 'react';
import { X, Users, Euro, Palette, Camera, Settings as SettingsIcon, Plus, Pencil, Trash2, Check, UserPlus, Shield, Store, Briefcase, Search } from 'lucide-react';

const SettingsModal = ({ isOpen, onClose, state, setState }) => {
  const [activeTab, setActiveTab] = useState('users');
  const [colorInput, setColorInput] = useState(state.brandColor || '#ea580c');
  const [userSearch, setUserSearch] = useState('');
  const [isEditingUser, setIsEditingUser] = useState(false);
  const [editingUserId, setEditingUserId] = useState(null);
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

  const filteredUsers = useMemo(() => {
    const query = userSearch.toLowerCase();
    return state.users.filter(u => 
      u.username.toLowerCase().includes(query) || 
      u.clientName.toLowerCase().includes(query)
    );
  }, [state.users, userSearch]);

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
    setUserForm({
      username: '',
      password: '',
      clientName: '',
      isActive: true,
      isAdmin: false,
      isRepresentative: false,
      linkedRepresentativeId: '',
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
    setIsEditingUser(true);
    setEditingUserId(user.id);
    setUserForm({ ...user });
  };

  const handleSaveUser = () => {
    if (!userForm.username || !userForm.clientName) {
      alert('Usuario y Nombre de Cliente son obligatorios');
      return;
    }

    if (editingUserId) {
      // Edit existing user
      setState(prev => ({
        ...prev,
        users: prev.users.map(u => u.id === editingUserId ? { ...userForm, id: editingUserId } : u)
      }));
    } else {
      // Create new user
      const newUser = {
        ...userForm,
        id: `user-${Date.now()}`
      };
      setState(prev => ({
        ...prev,
        users: [...prev.users, newUser]
      }));
    }

    setIsEditingUser(false);
    setEditingUserId(null);
  };

  const handleDeleteUser = (userId) => {
    if (userId === 'admin') {
      alert('No puedes eliminar el usuario administrador principal');
      return;
    }
    if (window.confirm('¿Estás seguro de eliminar este usuario?')) {
      setState(prev => ({
        ...prev,
        users: prev.users.filter(u => u.id !== userId)
      }));
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
        <div className="px-8 py-4 bg-slate-50 border-b border-slate-200 flex gap-2 overflow-x-auto">
          <button
            onClick={() => setActiveTab('users')}
            className={`px-6 py-2 rounded-lg text-xs font-black uppercase tracking-widest transition-all whitespace-nowrap ${
              activeTab === 'users' ? 'bg-indigo-600 text-white shadow-lg' : 'text-slate-400 hover:bg-white'
            }`}
          >
            <Users size={14} className="inline mr-2" />
            Red Distribución
          </button>
          <button
            onClick={() => setActiveTab('pricing')}
            className={`px-6 py-2 rounded-lg text-xs font-black uppercase tracking-widest transition-all whitespace-nowrap ${
              activeTab === 'pricing' ? 'bg-indigo-600 text-white shadow-lg' : 'text-slate-400 hover:bg-white'
            }`}
          >
            <Euro size={14} className="inline mr-2" />
            Márgenes
          </button>
          <button
            onClick={() => setActiveTab('identity')}
            className={`px-6 py-2 rounded-lg text-xs font-black uppercase tracking-widest transition-all whitespace-nowrap ${
              activeTab === 'identity' ? 'bg-indigo-600 text-white shadow-lg' : 'text-slate-400 hover:bg-white'
            }`}
          >
            <Camera size={14} className="inline mr-2" />
            Identidad
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-8">
          {activeTab === 'pricing' && (
            <div className="space-y-6">
              <div className="bg-white border border-indigo-100 rounded-2xl p-6 shadow-sm">
                <h3 className="text-sm font-black text-indigo-900 uppercase tracking-widest mb-4">Valor de Punto</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs font-black text-indigo-400 uppercase mb-2 block">Montada (€/punto)</label>
                    <input
                      type="number"
                      step="0.01"
                      value={state.pointValueMontada}
                      onChange={(e) => setState(prev => ({ ...prev, pointValueMontada: parseFloat(e.target.value) || 1.0 }))}
                      className="w-full bg-indigo-50 border border-indigo-100 rounded-xl p-3 text-lg font-black text-indigo-900 outline-none focus:border-orange-500"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-black text-indigo-400 uppercase mb-2 block">Despiece (€/punto)</label>
                    <input
                      type="number"
                      step="0.01"
                      value={state.pointValueDespiece}
                      onChange={(e) => setState(prev => ({ ...prev, pointValueDespiece: parseFloat(e.target.value) || 0.88 }))}
                      className="w-full bg-indigo-50 border border-indigo-100 rounded-xl p-3 text-lg font-black text-indigo-900 outline-none focus:border-orange-500"
                    />
                  </div>
                </div>
              </div>

              <div className="bg-white border border-indigo-100 rounded-2xl p-6 shadow-sm">
                <h3 className="text-sm font-black text-indigo-900 uppercase tracking-widest mb-4">Incrementos Cortes Especiales</h3>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="text-xs font-black text-indigo-400 uppercase mb-2 block">Ancho (€)</label>
                    <input
                      type="number"
                      value={state.specialIncrementWidth}
                      onChange={(e) => setState(prev => ({ ...prev, specialIncrementWidth: parseInt(e.target.value) || 45 }))}
                      className="w-full bg-orange-50 border border-orange-100 rounded-xl p-3 text-lg font-black text-orange-900 outline-none focus:border-orange-500"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-black text-indigo-400 uppercase mb-2 block">Alto (€)</label>
                    <input
                      type="number"
                      value={state.specialIncrementHeight}
                      onChange={(e) => setState(prev => ({ ...prev, specialIncrementHeight: parseInt(e.target.value) || 45 }))}
                      className="w-full bg-orange-50 border border-orange-100 rounded-xl p-3 text-lg font-black text-orange-900 outline-none focus:border-orange-500"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-black text-indigo-400 uppercase mb-2 block">Fondo (€)</label>
                    <input
                      type="number"
                      value={state.specialIncrementDepth}
                      onChange={(e) => setState(prev => ({ ...prev, specialIncrementDepth: parseInt(e.target.value) || 45 }))}
                      className="w-full bg-orange-50 border border-orange-100 rounded-xl p-3 text-lg font-black text-orange-900 outline-none focus:border-orange-500"
                    />
                  </div>
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
