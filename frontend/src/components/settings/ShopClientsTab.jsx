/*
 * © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
import React, { useState, useEffect, useMemo } from 'react';
import { Search, Plus, Pencil, Trash2, Users, Building2, Phone, Mail, MapPin, Save, X, Upload, Download, UserCheck, AlertCircle } from 'lucide-react';
import { shopClientsAPI } from '../../services/api';

/**
 * ShopClientsTab - Pestaña "Mis Clientes" para tiendas/distribuidores
 * Solo visible para usuarios con isTienda=true o administradores
 */
const ShopClientsTab = ({ currentUser }) => {
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({ total: 0, active: 0, potential: 0 });
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  
  // Form states
  const [isEditing, setIsEditing] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [isSaving, setIsSaving] = useState(false);
  const [formData, setFormData] = useState({
    code: '',
    name: '',
    company: '',
    email: '',
    phone: '',
    address: '',
    city: '',
    province: '',
    postalCode: '',
    taxId: '',
    status: 'potential',
    notes: ''
  });

  // Verificar si es admin
  const isAdmin = currentUser?.isAdmin || currentUser?.isGerente || currentUser?.isDirectorComercial;
  const isTienda = currentUser?.isTienda;

  // Cargar datos al montar
  useEffect(() => {
    loadClients();
    loadStats();
  }, [currentUser?.id]);

  const loadClients = async () => {
    setLoading(true);
    try {
      const data = await shopClientsAPI.getAll(currentUser?.id, search, statusFilter);
      setClients(data);
    } catch (err) {
      console.error('Error loading shop clients:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const data = await shopClientsAPI.getStats(currentUser?.id);
      setStats(data);
    } catch (err) {
      console.error('Error loading stats:', err);
    }
  };

  // Recargar cuando cambia el filtro
  useEffect(() => {
    const timer = setTimeout(() => {
      loadClients();
    }, 300);
    return () => clearTimeout(timer);
  }, [search, statusFilter]);

  // Filtrar clientes localmente
  const filteredClients = useMemo(() => {
    return clients.filter(client => {
      const matchesSearch = !search || 
        client.name?.toLowerCase().includes(search.toLowerCase()) ||
        client.company?.toLowerCase().includes(search.toLowerCase()) ||
        client.email?.toLowerCase().includes(search.toLowerCase()) ||
        client.phone?.includes(search);
      
      const matchesStatus = !statusFilter || client.status === statusFilter;
      
      return matchesSearch && matchesStatus;
    });
  }, [clients, search, statusFilter]);

  const handleCreate = () => {
    setIsEditing(true);
    setEditingId(null);
    setFormData({
      code: '',
      name: '',
      company: '',
      email: '',
      phone: '',
      address: '',
      city: '',
      province: '',
      postalCode: '',
      taxId: '',
      status: 'potential',
      notes: ''
    });
  };

  const handleEdit = (client) => {
    setIsEditing(true);
    setEditingId(client.id);
    setFormData({
      code: client.code || '',
      name: client.name || '',
      company: client.company || '',
      email: client.email || '',
      phone: client.phone || '',
      address: client.address || '',
      city: client.city || '',
      province: client.province || '',
      postalCode: client.postalCode || '',
      taxId: client.taxId || '',
      status: client.status || 'potential',
      notes: client.notes || ''
    });
  };

  const handleSave = async () => {
    if (!formData.name) {
      alert('El nombre es obligatorio');
      return;
    }

    setIsSaving(true);
    try {
      if (editingId) {
        await shopClientsAPI.update(editingId, formData, currentUser?.id);
      } else {
        await shopClientsAPI.create(formData, currentUser?.id);
      }
      
      setIsEditing(false);
      setEditingId(null);
      loadClients();
      loadStats();
    } catch (err) {
      alert('Error al guardar: ' + err.message);
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async (clientId) => {
    if (!window.confirm('¿Eliminar este cliente?')) return;
    
    try {
      await shopClientsAPI.delete(clientId, currentUser?.id);
      loadClients();
      loadStats();
    } catch (err) {
      alert('Error al eliminar: ' + err.message);
    }
  };

  const handleExportCSV = () => {
    const headers = ['Código', 'Nombre', 'Empresa', 'Email', 'Teléfono', 'Dirección', 'Ciudad', 'Provincia', 'CP', 'CIF/NIF', 'Estado'];
    const rows = filteredClients.map(c => [
      c.code, c.name, c.company, c.email, c.phone, c.address, c.city, c.province, c.postalCode, c.taxId, c.status
    ]);
    
    const csv = [headers.join(';'), ...rows.map(r => r.join(';'))].join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `mis_clientes_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
  };

  // Si no es tienda ni admin, no mostrar
  if (!isTienda && !isAdmin) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <AlertCircle size={48} className="text-amber-500 mb-4" />
        <p className="text-slate-500 font-medium">Esta sección solo está disponible para tiendas y distribuidores.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header con estadísticas */}
      <div className="bg-gradient-to-r from-emerald-600 to-teal-600 rounded-2xl p-6 text-white">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-white/20 rounded-xl">
              <Users size={28} />
            </div>
            <div>
              <h2 className="text-2xl font-black">MIS CLIENTES</h2>
              <p className="text-emerald-100 text-sm">Gestiona tu cartera de clientes finales</p>
            </div>
          </div>
          <button
            onClick={handleCreate}
            className="flex items-center gap-2 px-5 py-2.5 bg-white text-emerald-700 rounded-xl font-black text-sm hover:bg-emerald-50 transition-all shadow-lg"
            data-testid="new-shop-client-btn"
          >
            <Plus size={18} />
            NUEVO CLIENTE
          </button>
        </div>
        
        {/* Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <div className="bg-white/10 backdrop-blur rounded-xl p-4 text-center">
            <p className="text-3xl font-black">{stats.total}</p>
            <p className="text-xs font-bold text-emerald-100 uppercase">Total</p>
          </div>
          <div className="bg-white/10 backdrop-blur rounded-xl p-4 text-center">
            <p className="text-3xl font-black">{stats.active}</p>
            <p className="text-xs font-bold text-emerald-100 uppercase">Activos</p>
          </div>
          <div className="bg-white/10 backdrop-blur rounded-xl p-4 text-center">
            <p className="text-3xl font-black">{stats.potential}</p>
            <p className="text-xs font-bold text-emerald-100 uppercase">Potenciales</p>
          </div>
        </div>
      </div>

      {/* Formulario de edición */}
      {isEditing && (
        <div className="bg-white border-2 border-emerald-200 rounded-2xl p-6 shadow-lg">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-black text-slate-900">
              {editingId ? 'Editar Cliente' : 'Nuevo Cliente'}
            </h3>
            <button onClick={() => setIsEditing(false)} className="p-2 hover:bg-slate-100 rounded-lg">
              <X size={20} className="text-slate-500" />
            </button>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-black text-slate-500 uppercase mb-1">Código</label>
              <input
                type="text"
                value={formData.code}
                onChange={(e) => setFormData(prev => ({ ...prev, code: e.target.value }))}
                className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm"
                placeholder="CLI-001"
              />
            </div>
            <div>
              <label className="block text-xs font-black text-slate-500 uppercase mb-1">Nombre *</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm"
                placeholder="Nombre del cliente"
                data-testid="shop-client-name-input"
              />
            </div>
            <div>
              <label className="block text-xs font-black text-slate-500 uppercase mb-1">Empresa</label>
              <input
                type="text"
                value={formData.company}
                onChange={(e) => setFormData(prev => ({ ...prev, company: e.target.value }))}
                className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm"
                placeholder="Nombre de empresa"
              />
            </div>
            <div>
              <label className="block text-xs font-black text-slate-500 uppercase mb-1">CIF/NIF</label>
              <input
                type="text"
                value={formData.taxId}
                onChange={(e) => setFormData(prev => ({ ...prev, taxId: e.target.value }))}
                className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm"
                placeholder="12345678A"
              />
            </div>
            <div>
              <label className="block text-xs font-black text-slate-500 uppercase mb-1">Email</label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm"
                placeholder="email@ejemplo.com"
              />
            </div>
            <div>
              <label className="block text-xs font-black text-slate-500 uppercase mb-1">Teléfono</label>
              <input
                type="tel"
                value={formData.phone}
                onChange={(e) => setFormData(prev => ({ ...prev, phone: e.target.value }))}
                className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm"
                placeholder="+34 600 000 000"
              />
            </div>
            <div className="col-span-2">
              <label className="block text-xs font-black text-slate-500 uppercase mb-1">Dirección</label>
              <input
                type="text"
                value={formData.address}
                onChange={(e) => setFormData(prev => ({ ...prev, address: e.target.value }))}
                className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm"
                placeholder="Calle, número, piso..."
              />
            </div>
            <div>
              <label className="block text-xs font-black text-slate-500 uppercase mb-1">Ciudad</label>
              <input
                type="text"
                value={formData.city}
                onChange={(e) => setFormData(prev => ({ ...prev, city: e.target.value }))}
                className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm"
                placeholder="Ciudad"
              />
            </div>
            <div>
              <label className="block text-xs font-black text-slate-500 uppercase mb-1">Provincia</label>
              <input
                type="text"
                value={formData.province}
                onChange={(e) => setFormData(prev => ({ ...prev, province: e.target.value }))}
                className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm"
                placeholder="Provincia"
              />
            </div>
            <div>
              <label className="block text-xs font-black text-slate-500 uppercase mb-1">Código Postal</label>
              <input
                type="text"
                value={formData.postalCode}
                onChange={(e) => setFormData(prev => ({ ...prev, postalCode: e.target.value }))}
                className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm"
                placeholder="00000"
              />
            </div>
            <div>
              <label className="block text-xs font-black text-slate-500 uppercase mb-1">Estado</label>
              <select
                value={formData.status}
                onChange={(e) => setFormData(prev => ({ ...prev, status: e.target.value }))}
                className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm"
              >
                <option value="potential">Potencial</option>
                <option value="active">Activo</option>
                <option value="inactive">Inactivo</option>
              </select>
            </div>
            <div className="col-span-2">
              <label className="block text-xs font-black text-slate-500 uppercase mb-1">Notas</label>
              <textarea
                value={formData.notes}
                onChange={(e) => setFormData(prev => ({ ...prev, notes: e.target.value }))}
                className="w-full px-4 py-2 bg-slate-50 border border-slate-200 rounded-xl text-sm"
                rows={3}
                placeholder="Notas adicionales..."
              />
            </div>
          </div>
          
          <div className="flex justify-end gap-3 mt-6">
            <button
              onClick={() => setIsEditing(false)}
              className="px-5 py-2 bg-slate-100 text-slate-600 rounded-xl font-bold text-sm hover:bg-slate-200 transition-all"
            >
              Cancelar
            </button>
            <button
              onClick={handleSave}
              disabled={isSaving}
              className="flex items-center gap-2 px-6 py-2 bg-emerald-600 text-white rounded-xl font-bold text-sm hover:bg-emerald-700 transition-all disabled:opacity-50"
              data-testid="save-shop-client-btn"
            >
              <Save size={16} />
              {isSaving ? 'Guardando...' : 'Guardar'}
            </button>
          </div>
        </div>
      )}

      {/* Barra de búsqueda y filtros */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
          <input
            type="text"
            placeholder="Buscar por nombre, empresa, email o teléfono..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm outline-none focus:border-emerald-500"
            data-testid="shop-client-search"
          />
        </div>
        
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-4 py-2.5 bg-white border border-slate-200 rounded-xl text-sm outline-none"
        >
          <option value="">Todos los estados</option>
          <option value="active">Activos</option>
          <option value="potential">Potenciales</option>
          <option value="inactive">Inactivos</option>
        </select>
        
        <button
          onClick={handleExportCSV}
          className="flex items-center gap-2 px-4 py-2.5 bg-slate-100 text-slate-700 rounded-xl font-bold text-sm hover:bg-slate-200 transition-all"
        >
          <Download size={16} />
          Exportar
        </button>
      </div>

      {/* Lista de clientes */}
      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"></div>
        </div>
      ) : filteredClients.length === 0 ? (
        <div className="text-center py-12 bg-slate-50 rounded-2xl">
          <Users size={48} className="mx-auto text-slate-300 mb-3" />
          <p className="text-slate-500 font-medium">No hay clientes registrados</p>
          <p className="text-slate-400 text-sm mt-1">Haz clic en "Nuevo Cliente" para agregar el primero</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredClients.map(client => (
            <div
              key={client.id}
              className="bg-white border border-slate-200 rounded-xl p-4 hover:shadow-md transition-all"
              data-testid={`shop-client-${client.id}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <div className="p-2 bg-emerald-100 rounded-lg">
                      <Building2 size={20} className="text-emerald-600" />
                    </div>
                    <div>
                      <h3 className="text-lg font-black text-slate-900">{client.name}</h3>
                      {client.company && (
                        <p className="text-sm text-slate-500">{client.company}</p>
                      )}
                    </div>
                    <span className={`px-3 py-1 rounded-full text-xs font-black ${
                      client.status === 'active' 
                        ? 'bg-green-100 text-green-700' 
                        : client.status === 'potential'
                        ? 'bg-amber-100 text-amber-700'
                        : 'bg-slate-100 text-slate-600'
                    }`}>
                      {client.status === 'active' ? 'ACTIVO' : client.status === 'potential' ? 'POTENCIAL' : 'INACTIVO'}
                    </span>
                    {client.code && (
                      <span className="px-2 py-1 bg-slate-100 text-slate-600 rounded text-xs font-mono">
                        {client.code}
                      </span>
                    )}
                  </div>
                  
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mt-3">
                    {client.email && (
                      <div className="flex items-center gap-2 text-sm text-slate-600">
                        <Mail size={14} className="text-slate-400" />
                        <span className="truncate">{client.email}</span>
                      </div>
                    )}
                    {client.phone && (
                      <div className="flex items-center gap-2 text-sm text-slate-600">
                        <Phone size={14} className="text-slate-400" />
                        {client.phone}
                      </div>
                    )}
                    {(client.city || client.province) && (
                      <div className="flex items-center gap-2 text-sm text-slate-600">
                        <MapPin size={14} className="text-slate-400" />
                        {[client.city, client.province].filter(Boolean).join(', ')}
                      </div>
                    )}
                  </div>
                  
                  {/* Mostrar tienda propietaria para admins */}
                  {isAdmin && client.ownerName && (
                    <div className="mt-2 flex items-center gap-2">
                      <UserCheck size={14} className="text-indigo-500" />
                      <span className="text-xs text-indigo-600 font-bold">
                        Tienda: {client.ownerName}
                      </span>
                    </div>
                  )}
                </div>
                
                <div className="flex gap-2">
                  <button
                    onClick={() => handleEdit(client)}
                    className="p-2 hover:bg-indigo-50 rounded-lg transition-all"
                    title="Editar"
                  >
                    <Pencil size={16} className="text-indigo-600" />
                  </button>
                  <button
                    onClick={() => handleDelete(client.id)}
                    className="p-2 hover:bg-red-50 rounded-lg transition-all"
                    title="Eliminar"
                  >
                    <Trash2 size={16} className="text-red-600" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ShopClientsTab;
