/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
import React, { useState, useEffect } from 'react';
import { 
  Users, Search, Plus, Mail, Phone, Building2, MapPin, Tag,
  Edit2, Trash2, X, Save, Loader2, UserPlus, Filter, UserCheck, User, Settings, MessageCircle
} from 'lucide-react';
import { crmContactsAPI, clientsAPI, usersAPI } from '../services/api';

// WhatsApp click-to-chat: normaliza el teléfono (añade +34 si no hay prefijo) y
// abre wa.me con un saludo personalizado. Omnicanal desde la ficha del contacto.
const waLink = (contact) => {
  const raw = (contact?.phone || '').replace(/[^\d+]/g, '');
  if (!raw) return null;
  let num = raw.replace(/^\+/, '');
  if (!raw.startsWith('+') && num.length === 9) num = '34' + num; // España por defecto
  const primer = (contact?.name || '').trim().split(' ')[0] || '';
  const texto = encodeURIComponent(`Hola ${primer}, te escribimos desde Luiggi Home 👋`);
  return `https://wa.me/${num}?text=${texto}`;
};

const CLIENT_SEGMENTS = [
  "PROMOTOR",
  "CONSTRUCTOR",
  "PROMOTOR-CONSTRUCTOR",
  "DECORADOR-INTERIORISTA",
  "ESTUDIO DE COCINA",
  "TIENDA DE MUEBLES",
  "TIENDA DE COCINA Y BAÑOS",
  "TIENDA DE ARMARIOS",
  "ARQUITECTO",
  "REFORMISTA",
  "USUARIO FINAL",
  "OTRO"
];

// Tipos de negocio para etiquetas
const BUSINESS_TYPES = [
  { id: 'cocina-montada', name: 'Cocina Montada', color: 'bg-orange-100 text-orange-700 border-orange-300' },
  { id: 'cocina-despiece', name: 'Cocina Despiece', color: 'bg-indigo-100 text-indigo-700 border-indigo-300' },
  { id: 'armarios', name: 'Armarios', color: 'bg-purple-100 text-purple-700 border-purple-300' },
];

const CRMContacts = ({ currentUser }) => {
  const [contacts, setContacts] = useState([]);
  const [prescriptors, setPrescriptors] = useState([]);
  const [representatives, setRepresentatives] = useState([]); // Comerciales/Representantes para asignar
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [segmentFilter, setSegmentFilter] = useState('');
  const [prescriptorFilter, setPrescriptorFilter] = useState('');
  const [businessTypeFilter, setBusinessTypeFilter] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingContact, setEditingContact] = useState(null);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    company: '',
    position: '',
    address: '',
    notes: '',
    status: 'lead',
    source: '',
    segment: '',
    prescriptorId: '',
    prescriptorName: '',
    assignedTo: '',
    tags: [] // Etiquetas de tipo de negocio
  });

  useEffect(() => {
    loadContacts();
    loadPrescriptors();
    loadRepresentatives();
  }, [statusFilter, segmentFilter, prescriptorFilter]);

  const loadContacts = async () => {
    setIsLoading(true);
    try {
      // Director Comercial y Gerente siempre ven TODO
      const canViewAll = currentUser?.isAdmin === true || currentUser?.isGerente === true || currentUser?.isDirectorComercial === true;
      const options = canViewAll ? {} : {
        assignedTo: currentUser?.id,
        isAdmin: false
      };
      
      const data = await crmContactsAPI.getAll(statusFilter || null, null, options);
      // Apply local filters for segment and prescriptor
      let filtered = data;
      if (segmentFilter) {
        filtered = filtered.filter(c => c.segment === segmentFilter);
      }
      if (prescriptorFilter) {
        filtered = filtered.filter(c => c.prescriptorId === prescriptorFilter);
      }
      setContacts(filtered);
    } catch (err) {
      console.error('Error loading contacts:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const loadPrescriptors = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/crm/prescriptors`);
      if (response.ok) {
        const data = await response.json();
        setPrescriptors(data);
      }
    } catch (err) {
      console.error('Error loading prescriptors:', err);
    }
  };

  const loadRepresentatives = async () => {
    try {
      const users = await usersAPI.getAll();
      // Filtrar solo usuarios que sean comerciales/representantes
      const reps = users.filter(u => u.isRepresentative || u.isAdmin);
      setRepresentatives(reps);
    } catch (err) {
      console.error('Error loading representatives:', err);
    }
  };

  const handleSearch = async () => {
    setIsLoading(true);
    try {
      const data = await crmContactsAPI.getAll(statusFilter || null, searchQuery || null);
      let filtered = data;
      if (segmentFilter) {
        filtered = filtered.filter(c => c.segment === segmentFilter);
      }
      if (prescriptorFilter) {
        filtered = filtered.filter(c => c.prescriptorId === prescriptorFilter);
      }
      setContacts(filtered);
    } catch (err) {
      console.error('Error searching contacts:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const openModal = (contact = null) => {
    if (contact) {
      setEditingContact(contact);
      setFormData({
        name: contact.name || '',
        email: contact.email || '',
        phone: contact.phone || '',
        company: contact.company || '',
        position: contact.position || '',
        address: contact.address || '',
        notes: contact.notes || '',
        status: contact.status || 'lead',
        source: contact.source || '',
        segment: contact.segment || '',
        prescriptorId: contact.prescriptorId || '',
        prescriptorName: contact.prescriptorName || '',
        assignedTo: contact.assignedTo || '',
        tags: contact.tags || []
      });
    } else {
      setEditingContact(null);
      setFormData({
        name: '',
        email: '',
        phone: '',
        company: '',
        position: '',
        address: '',
        notes: '',
        status: 'lead',
        source: '',
        segment: '',
        prescriptorId: currentUser?.isPrescriptor ? currentUser?.id : '',
        prescriptorName: currentUser?.isPrescriptor ? currentUser?.clientName : '',
        // Auto-assign to current user if they are a comercial
        assignedTo: currentUser?.isRepresentative ? currentUser?.id : '',
        tags: []
      });
    }
    setShowModal(true);
  };

  const handleSave = async () => {
    try {
      if (editingContact) {
        await crmContactsAPI.update(editingContact.id, formData);
      } else {
        await crmContactsAPI.create(formData);
      }
      setShowModal(false);
      loadContacts();
    } catch (err) {
      alert('Error al guardar contacto: ' + err.message);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('¿Eliminar este contacto?')) {
      try {
        await crmContactsAPI.delete(id);
        loadContacts();
      } catch (err) {
        alert('Error al eliminar contacto: ' + err.message);
      }
    }
  };

  // Convertir contacto CRM a cliente potencial
  const handleConvertToClient = async (contact) => {
    if (contact.convertedToClientId) {
      alert('Este contacto ya fue convertido a cliente');
      return;
    }
    
    if (!window.confirm(`¿Convertir "${contact.name}" a Cliente Potencial?\n\nEsto copiará los datos del contacto a la base de datos de Clientes.`)) {
      return;
    }
    
    try {
      const newClient = await clientsAPI.createFromContact(contact.id);
      alert(`✅ Cliente potencial "${newClient.nombre}" creado correctamente.\n\nPuedes gestionarlo desde Maestro → Clientes.`);
      loadContacts(); // Reload to update the contact's status
    } catch (err) {
      alert('Error al convertir: ' + err.message);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      lead: 'bg-blue-100 text-blue-700',
      active: 'bg-green-100 text-green-700',
      customer: 'bg-purple-100 text-purple-700',
      inactive: 'bg-slate-100 text-slate-500'
    };
    return colors[status] || 'bg-slate-100 text-slate-500';
  };

  const getStatusName = (status) => {
    const names = {
      lead: 'Nuevo',
      active: 'Activo',
      customer: 'Cliente',
      inactive: 'Inactivo'
    };
    return names[status] || status;
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('es-ES', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 0
    }).format(value);
  };

  const filteredContacts = contacts.filter(c => {
    const matchesSearch = c.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.company?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.email?.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesBusinessType = !businessTypeFilter || 
      (c.tags && c.tags.includes(businessTypeFilter));
    
    return matchesSearch && matchesBusinessType;
  });

  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-slate-50 to-indigo-50 p-3 md:p-6">
      {/* Header */}
      <div className="flex flex-col gap-3 mb-4 md:mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-indigo-600 rounded-xl shadow-lg">
              <Users size={20} className="text-white" />
            </div>
            <div>
              <h2 className="text-lg font-black text-slate-900 uppercase tracking-tight">Contactos</h2>
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">{contacts.length} registros</p>
            </div>
          </div>
          {/* Add button visible en header en móvil */}
          <button onClick={() => openModal()}
            className="flex items-center gap-1.5 px-3 py-2 bg-indigo-600 text-white rounded-xl font-black uppercase text-xs hover:bg-indigo-700 transition-all shadow-md md:hidden"
            data-testid="add-contact-btn-mobile">
            <UserPlus size={14} /> Nuevo
          </button>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-2 md:px-3 py-2 bg-white border-2 border-indigo-100 rounded-xl text-xs md:text-sm font-bold outline-none focus:border-indigo-500 min-w-[100px]"
            data-testid="status-filter"
          >
            <option value="">Estados</option>
            <option value="lead">Nuevos</option>
            <option value="active">Activos</option>
            <option value="customer">Clientes</option>
            <option value="inactive">Inactivos</option>
          </select>

          {/* Segment Filter */}
          <select
            value={segmentFilter}
            onChange={(e) => setSegmentFilter(e.target.value)}
            className="px-2 md:px-3 py-2 bg-white border-2 border-indigo-100 rounded-xl text-xs md:text-sm font-bold outline-none focus:border-indigo-500 min-w-[100px]"
            data-testid="segment-filter"
          >
            <option value="">Segmentos</option>
            {CLIENT_SEGMENTS.map(seg => (
              <option key={seg} value={seg}>{seg}</option>
            ))}
          </select>

          {/* Business Type Filter */}
          <select
            value={businessTypeFilter}
            onChange={(e) => setBusinessTypeFilter(e.target.value)}
            className="px-3 py-2 bg-white border-2 border-purple-100 rounded-xl text-sm font-bold outline-none focus:border-purple-500"
            data-testid="business-type-filter"
          >
            <option value="">Todos los negocios</option>
            {BUSINESS_TYPES.map(bt => (
              <option key={bt.id} value={bt.id}>{bt.name}</option>
            ))}
          </select>

          {/* Colaborador Filter */}
          {prescriptors.length > 0 && (
            <select
              value={prescriptorFilter}
              onChange={(e) => setPrescriptorFilter(e.target.value)}
              className="px-3 py-2 bg-white border-2 border-amber-100 rounded-xl text-sm font-bold outline-none focus:border-amber-500"
              data-testid="prescriptor-filter"
            >
              <option value="">Todos los colaboradores</option>
              {prescriptors.map(p => (
                <option key={p.id} value={p.id}>{p.clientName}</option>
              ))}
            </select>
          )}

          {/* Search */}
          <div className="relative w-full md:w-60">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-indigo-300" size={16} />
            <input 
              type="text" 
              placeholder="Buscar..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSearch()}
              className="w-full bg-white border-2 border-indigo-100 rounded-xl py-2 pl-10 pr-4 text-xs md:text-sm font-bold outline-none focus:border-indigo-500"
              data-testid="search-contacts"
            />
          </div>

          {/* Add Contact */}
          <button
            onClick={() => openModal()}
            className="flex items-center gap-2 px-3 md:px-5 py-2.5 bg-indigo-600 text-white rounded-xl font-black uppercase text-xs hover:bg-indigo-700 transition-all shadow-lg whitespace-nowrap"
            data-testid="add-contact-btn"
          >
            <UserPlus size={16} />
            <span className="hidden md:inline">Nuevo Contacto</span>
            <span className="md:hidden">Nuevo</span>
          </button>
        </div>
      </div>

      {/* Contacts - Card view for mobile, Table for desktop */}
      <div className="flex-1 bg-white rounded-2xl border-2 border-indigo-100 shadow-xl overflow-hidden">
        {isLoading ? (
          <div className="h-full flex items-center justify-center">
            <Loader2 className="w-8 h-8 text-indigo-600 animate-spin" />
          </div>
        ) : filteredContacts.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-slate-400 p-8">
            <Users className="w-12 h-12 md:w-16 md:h-16 mb-4 opacity-50" />
            <p className="font-black text-base md:text-lg">Sin contactos</p>
            <p className="text-xs md:text-sm">Añade tu primer contacto</p>
          </div>
        ) : (
          <div className="overflow-auto h-full">
            {/* Mobile Card View */}
            <div className="md:hidden p-3 space-y-2.5">
              {filteredContacts.map(contact => (
                <div key={contact.id} className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden active:scale-[0.99] transition-transform">
                  {/* Color top bar por estado */}
                  <div className={`h-1 w-full ${contact.status === 'customer' ? 'bg-purple-500' : contact.status === 'active' ? 'bg-green-500' : contact.status === 'inactive' ? 'bg-slate-300' : 'bg-blue-400'}`} />
                  <div className="p-4">
                    <div className="flex items-start justify-between mb-2.5">
                      <div className="flex items-center gap-3">
                        <div className={`w-11 h-11 rounded-2xl flex items-center justify-center font-black text-base flex-shrink-0 ${
                          contact.status === 'customer' ? 'bg-purple-100 text-purple-700' :
                          contact.status === 'active' ? 'bg-green-100 text-green-700' :
                          'bg-indigo-100 text-indigo-700'
                        }`}>
                          {contact.name?.charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <p className="font-black text-slate-900 text-sm leading-tight">{contact.name}</p>
                          <p className="text-xs text-slate-400 mt-0.5">{contact.company || 'Sin empresa'}</p>
                        </div>
                      </div>
                      <span className={`px-2 py-0.5 rounded-lg text-[9px] font-black uppercase ${getStatusColor(contact.status)}`}>
                        {getStatusName(contact.status)}
                      </span>
                    </div>

                    {/* Info rápida */}
                    <div className="flex flex-wrap gap-x-4 gap-y-1 mb-3">
                      {contact.phone && (
                        <a href={`tel:${contact.phone}`} className="flex items-center gap-1.5 text-xs text-slate-600 hover:text-indigo-600">
                          <Phone size={11} className="text-slate-400" />
                          <span>{contact.phone}</span>
                        </a>
                      )}
                      {contact.phone && waLink(contact) && (
                        <a href={waLink(contact)} target="_blank" rel="noopener noreferrer"
                          className="flex items-center gap-1.5 text-xs font-bold text-green-600 hover:text-green-700"
                          title="Escribir por WhatsApp">
                          <MessageCircle size={11} />
                          <span>WhatsApp</span>
                        </a>
                      )}
                      {contact.email && (
                        <a href={`mailto:${contact.email}`} className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-indigo-600 truncate max-w-[160px]">
                          <Mail size={11} />
                          <span className="truncate">{contact.email}</span>
                        </a>
                      )}
                    </div>

                    {/* Tags */}
                    {contact.tags?.length > 0 && (
                      <div className="flex flex-wrap gap-1 mb-3">
                        {contact.tags.map(tagId => {
                          const bt = BUSINESS_TYPES.find(b => b.id === tagId);
                          return bt ? (
                            <span key={tagId} className={`px-2 py-0.5 rounded-full text-[9px] font-black border ${bt.color}`}>
                              {bt.name}
                            </span>
                          ) : null;
                        })}
                      </div>
                    )}

                    {/* Footer */}
                    <div className="flex items-center justify-between pt-2.5 border-t border-slate-50">
                      <span className="text-sm font-black text-indigo-600">
                        {formatCurrency(contact.totalValue || 0)}
                      </span>
                      <div className="flex items-center gap-1.5">
                        {!contact.convertedToClientId && (
                          <button onClick={() => handleConvertToClient(contact)}
                            className="p-2 bg-orange-50 text-orange-500 rounded-xl hover:bg-orange-100 transition-colors" title="Convertir a cliente">
                            <UserCheck size={14} />
                          </button>
                        )}
                        <button onClick={() => openModal(contact)}
                          className="p-2 bg-indigo-50 text-indigo-600 rounded-xl hover:bg-indigo-100 transition-colors">
                          <Edit2 size={14} />
                        </button>
                        <button onClick={() => handleDelete(contact.id)}
                          className="p-2 bg-red-50 text-red-500 rounded-xl hover:bg-red-100 transition-colors">
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            
            {/* Desktop Table View */}
            <div className="overflow-x-auto w-full"><table className="w-full hidden md:table">
              <thead className="bg-slate-50 sticky top-0">
                <tr>
                  <th className="text-left py-4 px-4 text-xs font-black text-slate-500 uppercase">Contacto</th>
                  <th className="text-left py-4 px-4 text-xs font-black text-slate-500 uppercase">Empresa</th>
                  <th className="text-left py-4 px-4 text-xs font-black text-slate-500 uppercase">Tipo Negocio</th>
                  <th className="text-left py-4 px-4 text-xs font-black text-slate-500 uppercase">Segmento</th>
                  <th className="text-left py-4 px-4 text-xs font-black text-slate-500 uppercase">Colaborador</th>
                  <th className="text-left py-4 px-4 text-xs font-black text-slate-500 uppercase">Estado</th>
                  <th className="text-right py-4 px-4 text-xs font-black text-slate-500 uppercase">Valor</th>
                  <th className="text-center py-4 px-4 text-xs font-black text-slate-500 uppercase">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredContacts.map(contact => (
                  <tr key={contact.id} className="hover:bg-slate-50 transition-colors">
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 bg-indigo-100 rounded-full flex items-center justify-center">
                          <span className="text-indigo-600 font-black text-sm">
                            {contact.name?.charAt(0).toUpperCase()}
                          </span>
                        </div>
                        <div>
                          <p className="font-bold text-slate-900 text-sm">{contact.name}</p>
                          <div className="flex items-center gap-2 text-[10px] text-slate-400">
                            {contact.email && <span>{contact.email}</span>}
                            {contact.phone && <span>· {contact.phone}</span>}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <span className="text-sm text-slate-600">{contact.company || '-'}</span>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex flex-wrap gap-1">
                        {contact.tags && contact.tags.length > 0 ? (
                          contact.tags.map(tagId => {
                            const bt = BUSINESS_TYPES.find(b => b.id === tagId);
                            return bt ? (
                              <span key={tagId} className={`text-[9px] px-2 py-0.5 rounded-full font-bold border ${bt.color}`}>
                                {bt.name}
                              </span>
                            ) : null;
                          })
                        ) : (
                          <span className="text-xs text-slate-300">-</span>
                        )}
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      {contact.segment ? (
                        <span className="text-[10px] px-2 py-1 bg-violet-100 text-violet-700 rounded-full font-bold">
                          {contact.segment}
                        </span>
                      ) : (
                        <span className="text-xs text-slate-300">-</span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      {contact.prescriptorName ? (
                        <span className="text-[10px] px-2 py-1 bg-amber-100 text-amber-700 rounded-full font-bold flex items-center gap-1 w-fit">
                          <User size={10} />
                          {contact.prescriptorName}
                        </span>
                      ) : (
                        <span className="text-xs text-slate-300">-</span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-1 rounded-full text-[10px] font-bold ${getStatusColor(contact.status)}`}>
                        {getStatusName(contact.status)}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <span className="font-bold text-slate-900 text-sm">{formatCurrency(contact.totalValue || 0)}</span>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center justify-center gap-1">
                        {/* Convertir a Cliente Potencial - Solo si no está convertido */}
                        {!contact.convertedToClientId && (
                          <button
                            onClick={() => handleConvertToClient(contact)}
                            className="p-1.5 text-orange-500 hover:bg-orange-50 rounded-lg transition-colors"
                            title="Convertir a Cliente Potencial"
                            data-testid={`convert-contact-${contact.id}`}
                          >
                            <UserCheck size={14} />
                          </button>
                        )}
                        {contact.convertedToClientId && (
                          <span className="text-[10px] text-emerald-600 font-bold px-2 py-1 bg-emerald-50 rounded">
                            CONVERTIDO
                          </span>
                        )}
                        <button
                          onClick={() => openModal(contact)}
                          className="p-1.5 text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
                          data-testid={`edit-contact-${contact.id}`}
                        >
                          <Edit2 size={14} />
                        </button>
                        <button
                          onClick={() => handleDelete(contact.id)}
                          className="p-1.5 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                          data-testid={`delete-contact-${contact.id}`}
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table></div>
          </div>
        )}
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-end sm:items-center justify-center z-50 p-0 sm:p-4">
          <div className="bg-white rounded-t-3xl sm:rounded-2xl shadow-2xl w-full sm:max-w-lg max-h-[92vh] flex flex-col">
            <div className="flex items-center justify-between p-6 border-b border-slate-200">
              <h3 className="text-xl font-black text-slate-900 uppercase">
                {editingContact ? 'Editar Contacto' : 'Nuevo Contacto'}
              </h3>
              <button onClick={() => setShowModal(false)} className="p-2 hover:bg-slate-100 rounded-lg">
                <X size={20} />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-6">
              <div className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Nombre *</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={e => setFormData({...formData, name: e.target.value})}
                    className="w-full px-4 py-2.5 border-2 border-slate-200 rounded-xl text-sm font-bold outline-none focus:border-indigo-500"
                    data-testid="contact-name-input"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Empresa</label>
                  <input
                    type="text"
                    value={formData.company}
                    onChange={e => setFormData({...formData, company: e.target.value})}
                    className="w-full px-4 py-2.5 border-2 border-slate-200 rounded-xl text-sm font-bold outline-none focus:border-indigo-500"
                    data-testid="contact-company-input"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Email</label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={e => setFormData({...formData, email: e.target.value})}
                    className="w-full px-4 py-2.5 border-2 border-slate-200 rounded-xl text-sm font-bold outline-none focus:border-indigo-500"
                    data-testid="contact-email-input"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Teléfono</label>
                  <input
                    type="tel"
                    value={formData.phone}
                    onChange={e => setFormData({...formData, phone: e.target.value})}
                    className="w-full px-4 py-2.5 border-2 border-slate-200 rounded-xl text-sm font-bold outline-none focus:border-indigo-500"
                    data-testid="contact-phone-input"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Cargo</label>
                  <input
                    type="text"
                    value={formData.position}
                    onChange={e => setFormData({...formData, position: e.target.value})}
                    className="w-full px-4 py-2.5 border-2 border-slate-200 rounded-xl text-sm font-bold outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Estado</label>
                  <select
                    value={formData.status}
                    onChange={e => setFormData({...formData, status: e.target.value})}
                    className="w-full px-4 py-2.5 border-2 border-slate-200 rounded-xl text-sm font-bold outline-none focus:border-indigo-500"
                    data-testid="contact-status-select"
                  >
                    <option value="lead">Nuevo</option>
                    <option value="active">Activo</option>
                    <option value="customer">Cliente</option>
                    <option value="inactive">Inactivo</option>
                  </select>
                </div>
              </div>

              {/* Segmento y Colaborador */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Segmento</label>
                  <select
                    value={formData.segment}
                    onChange={e => setFormData({...formData, segment: e.target.value})}
                    className="w-full px-4 py-2.5 border-2 border-violet-200 rounded-xl text-sm font-bold outline-none focus:border-violet-500"
                    data-testid="contact-segment-select"
                  >
                    <option value="">Sin segmento</option>
                    {CLIENT_SEGMENTS.map(seg => (
                      <option key={seg} value={seg}>{seg}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Colaborador Comercial</label>
                  <select
                    value={formData.prescriptorId}
                    onChange={e => {
                      const presc = prescriptors.find(p => p.id === e.target.value);
                      setFormData({
                        ...formData, 
                        prescriptorId: e.target.value,
                        prescriptorName: presc?.clientName || ''
                      });
                    }}
                    className="w-full px-4 py-2.5 border-2 border-amber-200 rounded-xl text-sm font-bold outline-none focus:border-amber-500"
                    data-testid="contact-prescriptor-select"
                    disabled={currentUser?.isPrescriptor}
                  >
                    <option value="">Sin colaborador</option>
                    {prescriptors.map(p => (
                      <option key={p.id} value={p.id}>{p.clientName}</option>
                    ))}
                  </select>
                  {currentUser?.isPrescriptor && (
                    <p className="text-[10px] text-amber-600 mt-1">Este contacto será tuyo como colaborador comercial</p>
                  )}
                </div>
              </div>

              {/* Asignar a Comercial / Representante - Solo visible para Admin */}
              {(currentUser?.isAdmin || currentUser?.isGerente || currentUser?.isDirectorComercial) && (
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Asignar a Comercial / Representante</label>
                  <select
                    value={formData.assignedTo || ''}
                    onChange={e => setFormData({...formData, assignedTo: e.target.value})}
                    className="w-full px-4 py-2.5 border-2 border-indigo-200 rounded-xl text-sm font-bold outline-none focus:border-indigo-500"
                    data-testid="contact-assignedto-select"
                  >
                    <option value="">Sin asignar</option>
                    {representatives.map(rep => (
                      <option key={rep.id} value={rep.id}>
                        {rep.clientName} {rep.isAdmin ? '(Admin)' : '(Comercial)'}
                      </option>
                    ))}
                  </select>
                  <p className="text-[10px] text-slate-400 mt-1">El comercial asignado podrá ver y gestionar este contacto</p>
                </div>
              )}

              {/* Tipo de Negocio (Tags) */}
              <div className="col-span-2">
                <label className="block text-xs font-bold text-slate-500 uppercase mb-2">Tipo de Negocio</label>
                <div className="flex flex-wrap gap-2">
                  {BUSINESS_TYPES.map(bt => {
                    const isSelected = formData.tags?.includes(bt.id);
                    return (
                      <button
                        key={bt.id}
                        type="button"
                        onClick={() => {
                          const newTags = isSelected
                            ? (formData.tags || []).filter(t => t !== bt.id)
                            : [...(formData.tags || []), bt.id];
                          setFormData({...formData, tags: newTags});
                        }}
                        className={`px-3 py-1.5 rounded-lg text-xs font-bold border-2 transition-all ${
                          isSelected 
                            ? bt.color + ' shadow-md' 
                            : 'bg-slate-100 text-slate-400 border-slate-200 hover:border-slate-300'
                        }`}
                      >
                        {bt.name}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Dirección</label>
                <input
                  type="text"
                  value={formData.address}
                  onChange={e => setFormData({...formData, address: e.target.value})}
                  className="w-full px-4 py-2.5 border-2 border-slate-200 rounded-xl text-sm font-bold outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Notas</label>
                <textarea
                  value={formData.notes}
                  onChange={e => setFormData({...formData, notes: e.target.value})}
                  rows={3}
                  className="w-full px-4 py-2.5 border-2 border-slate-200 rounded-xl text-sm font-bold outline-none focus:border-indigo-500 resize-none"
                />
              </div>

              {/* Valores Personalizados - Solo para Admin y al editar */}
              {(currentUser?.isAdmin || currentUser?.isGerente || currentUser?.isDirectorComercial) && editingContact && (
                <div className="bg-amber-50 border-2 border-amber-200 rounded-xl p-4 mt-4">
                  <h4 className="text-xs font-black text-amber-700 uppercase mb-3 flex items-center gap-2">
                    <Settings size={14} />
                    Valores Personalizados para este Cliente
                  </h4>
                  <p className="text-[10px] text-amber-600 mb-3">
                    Estos valores sobreescriben los valores por defecto del sistema solo para este cliente
                  </p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label className="block text-[10px] font-bold text-amber-600 uppercase mb-1">Incremento Ancho (€)</label>
                      <input
                        type="number"
                        step="0.01"
                        value={formData.customWidthIncrement ?? ''}
                        onChange={e => setFormData({...formData, customWidthIncrement: e.target.value ? parseFloat(e.target.value) : null})}
                        placeholder="Por defecto"
                        className="w-full px-3 py-2 border-2 border-amber-200 rounded-lg text-sm font-bold outline-none focus:border-amber-500 bg-white"
                      />
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-amber-600 uppercase mb-1">Incremento Alto (€)</label>
                      <input
                        type="number"
                        step="0.01"
                        value={formData.customHeightIncrement ?? ''}
                        onChange={e => setFormData({...formData, customHeightIncrement: e.target.value ? parseFloat(e.target.value) : null})}
                        placeholder="Por defecto"
                        className="w-full px-3 py-2 border-2 border-amber-200 rounded-lg text-sm font-bold outline-none focus:border-amber-500 bg-white"
                      />
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-amber-600 uppercase mb-1">Incremento Fondo (€)</label>
                      <input
                        type="number"
                        step="0.01"
                        value={formData.customDepthIncrement ?? ''}
                        onChange={e => setFormData({...formData, customDepthIncrement: e.target.value ? parseFloat(e.target.value) : null})}
                        placeholder="Por defecto"
                        className="w-full px-3 py-2 border-2 border-amber-200 rounded-lg text-sm font-bold outline-none focus:border-amber-500 bg-white"
                      />
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-amber-600 uppercase mb-1">Incremento Viga (€)</label>
                      <input
                        type="number"
                        step="0.01"
                        value={formData.customVigaCutIncrement ?? ''}
                        onChange={e => setFormData({...formData, customVigaCutIncrement: e.target.value ? parseFloat(e.target.value) : null})}
                        placeholder="Por defecto"
                        className="w-full px-3 py-2 border-2 border-amber-200 rounded-lg text-sm font-bold outline-none focus:border-amber-500 bg-white"
                      />
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-amber-600 uppercase mb-1">Valor Punto Montada</label>
                      <input
                        type="number"
                        step="0.01"
                        value={formData.customPointValueMontada ?? ''}
                        onChange={e => setFormData({...formData, customPointValueMontada: e.target.value ? parseFloat(e.target.value) : null})}
                        placeholder="Por defecto"
                        className="w-full px-3 py-2 border-2 border-amber-200 rounded-lg text-sm font-bold outline-none focus:border-amber-500 bg-white"
                      />
                    </div>
                    <div>
                      <label className="block text-[10px] font-bold text-amber-600 uppercase mb-1">Valor Punto Despiece</label>
                      <input
                        type="number"
                        step="0.01"
                        value={formData.customPointValueDespiece ?? ''}
                        onChange={e => setFormData({...formData, customPointValueDespiece: e.target.value ? parseFloat(e.target.value) : null})}
                        placeholder="Por defecto"
                        className="w-full px-3 py-2 border-2 border-amber-200 rounded-lg text-sm font-bold outline-none focus:border-amber-500 bg-white"
                      />
                    </div>
                  </div>
                </div>
              )}
              </div>
            </div>

            <div className="flex justify-end gap-3 p-6 border-t border-slate-200">
              <button
                onClick={() => setShowModal(false)}
                className="px-6 py-2.5 border-2 border-slate-200 text-slate-600 rounded-xl font-bold uppercase text-xs hover:bg-slate-50"
              >
                Cancelar
              </button>
              <button
                onClick={handleSave}
                disabled={!formData.name}
                className="px-6 py-2.5 bg-indigo-600 text-white rounded-xl font-bold uppercase text-xs hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-2"
                data-testid="save-contact-btn"
              >
                <Save size={16} />
                Guardar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CRMContacts;
