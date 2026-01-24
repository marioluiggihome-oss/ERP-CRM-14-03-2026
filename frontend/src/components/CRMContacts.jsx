import React, { useState, useEffect } from 'react';
import { 
  Users, Search, Plus, Mail, Phone, Building2, MapPin, Tag,
  Edit2, Trash2, X, Save, Loader2, UserPlus, Filter, UserCheck, User
} from 'lucide-react';
import { crmContactsAPI, clientsAPI, usersAPI } from '../services/api';

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

const CRMContacts = ({ currentUser }) => {
  const [contacts, setContacts] = useState([]);
  const [prescriptors, setPrescriptors] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [segmentFilter, setSegmentFilter] = useState('');
  const [prescriptorFilter, setPrescriptorFilter] = useState('');
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
    prescriptorName: ''
  });

  useEffect(() => {
    loadContacts();
    loadPrescriptors();
  }, [statusFilter, segmentFilter, prescriptorFilter]);

  const loadContacts = async () => {
    setIsLoading(true);
    try {
      const data = await crmContactsAPI.getAll(statusFilter || null, null);
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
        prescriptorName: contact.prescriptorName || ''
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
        prescriptorName: currentUser?.isPrescriptor ? currentUser?.clientName : ''
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

  const filteredContacts = contacts.filter(c => 
    c.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    c.company?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    c.email?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="h-full flex flex-col bg-gradient-to-br from-slate-50 to-indigo-50 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-indigo-600 rounded-2xl shadow-xl">
            <Users size={28} className="text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-black text-slate-900 uppercase tracking-tight">Contactos</h2>
            <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">{contacts.length} contactos</p>
          </div>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 bg-white border-2 border-indigo-100 rounded-xl text-sm font-bold outline-none focus:border-indigo-500"
            data-testid="status-filter"
          >
            <option value="">Todos los estados</option>
            <option value="lead">Nuevos</option>
            <option value="active">Activos</option>
            <option value="customer">Clientes</option>
            <option value="inactive">Inactivos</option>
          </select>

          {/* Segment Filter */}
          <select
            value={segmentFilter}
            onChange={(e) => setSegmentFilter(e.target.value)}
            className="px-3 py-2 bg-white border-2 border-indigo-100 rounded-xl text-sm font-bold outline-none focus:border-indigo-500"
            data-testid="segment-filter"
          >
            <option value="">Todos los segmentos</option>
            {CLIENT_SEGMENTS.map(seg => (
              <option key={seg} value={seg}>{seg}</option>
            ))}
          </select>

          {/* Prescriptor Filter */}
          {prescriptors.length > 0 && (
            <select
              value={prescriptorFilter}
              onChange={(e) => setPrescriptorFilter(e.target.value)}
              className="px-3 py-2 bg-white border-2 border-amber-100 rounded-xl text-sm font-bold outline-none focus:border-amber-500"
              data-testid="prescriptor-filter"
            >
              <option value="">Todos los prescriptores</option>
              {prescriptors.map(p => (
                <option key={p.id} value={p.id}>{p.clientName}</option>
              ))}
            </select>
          )}

          {/* Search */}
          <div className="relative w-60">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-indigo-300" size={16} />
            <input 
              type="text" 
              placeholder="Buscar contacto..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSearch()}
              className="w-full bg-white border-2 border-indigo-100 rounded-xl py-2 pl-10 pr-4 text-sm font-bold outline-none focus:border-indigo-500"
              data-testid="search-contacts"
            />
          </div>

          {/* Add Contact */}
          <button
            onClick={() => openModal()}
            className="flex items-center gap-2 px-5 py-2.5 bg-indigo-600 text-white rounded-xl font-black uppercase text-xs hover:bg-indigo-700 transition-all shadow-lg"
            data-testid="add-contact-btn"
          >
            <UserPlus size={16} />
            Nuevo Contacto
          </button>
        </div>
      </div>

      {/* Contacts Table */}
      <div className="flex-1 bg-white rounded-2xl border-2 border-indigo-100 shadow-xl overflow-hidden">
        {isLoading ? (
          <div className="h-full flex items-center justify-center">
            <Loader2 className="w-8 h-8 text-indigo-600 animate-spin" />
          </div>
        ) : filteredContacts.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-slate-400">
            <Users className="w-16 h-16 mb-4 opacity-50" />
            <p className="font-black text-lg">Sin contactos</p>
            <p className="text-sm">Añade tu primer contacto</p>
          </div>
        ) : (
          <div className="overflow-auto h-full">
            <table className="w-full">
              <thead className="bg-slate-50 sticky top-0">
                <tr>
                  <th className="text-left py-4 px-6 text-xs font-black text-slate-500 uppercase">Contacto</th>
                  <th className="text-left py-4 px-6 text-xs font-black text-slate-500 uppercase">Empresa</th>
                  <th className="text-left py-4 px-6 text-xs font-black text-slate-500 uppercase">Contacto</th>
                  <th className="text-left py-4 px-6 text-xs font-black text-slate-500 uppercase">Estado</th>
                  <th className="text-right py-4 px-6 text-xs font-black text-slate-500 uppercase">Valor Total</th>
                  <th className="text-center py-4 px-6 text-xs font-black text-slate-500 uppercase">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredContacts.map(contact => (
                  <tr key={contact.id} className="hover:bg-slate-50 transition-colors">
                    <td className="py-4 px-6">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-indigo-100 rounded-full flex items-center justify-center">
                          <span className="text-indigo-600 font-black text-sm">
                            {contact.name?.charAt(0).toUpperCase()}
                          </span>
                        </div>
                        <div>
                          <p className="font-bold text-slate-900">{contact.name}</p>
                          <p className="text-xs text-slate-500">{contact.position}</p>
                        </div>
                      </div>
                    </td>
                    <td className="py-4 px-6">
                      <div className="flex items-center gap-2">
                        <Building2 className="w-4 h-4 text-slate-400" />
                        <span className="text-sm text-slate-600">{contact.company || '-'}</span>
                      </div>
                    </td>
                    <td className="py-4 px-6">
                      <div className="space-y-1">
                        {contact.email && (
                          <div className="flex items-center gap-2 text-xs text-slate-500">
                            <Mail className="w-3 h-3" />
                            {contact.email}
                          </div>
                        )}
                        {contact.phone && (
                          <div className="flex items-center gap-2 text-xs text-slate-500">
                            <Phone className="w-3 h-3" />
                            {contact.phone}
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="py-4 px-6">
                      <span className={`px-3 py-1 rounded-full text-xs font-bold ${getStatusColor(contact.status)}`}>
                        {getStatusName(contact.status)}
                      </span>
                    </td>
                    <td className="py-4 px-6 text-right">
                      <span className="font-bold text-slate-900">{formatCurrency(contact.totalValue || 0)}</span>
                    </td>
                    <td className="py-4 px-6">
                      <div className="flex items-center justify-center gap-2">
                        {/* Convertir a Cliente Potencial - Solo si no está convertido */}
                        {!contact.convertedToClientId && (
                          <button
                            onClick={() => handleConvertToClient(contact)}
                            className="p-2 text-orange-500 hover:bg-orange-50 rounded-lg transition-colors"
                            title="Convertir a Cliente Potencial"
                            data-testid={`convert-contact-${contact.id}`}
                          >
                            <UserCheck size={16} />
                          </button>
                        )}
                        {contact.convertedToClientId && (
                          <span className="text-[10px] text-emerald-600 font-bold px-2 py-1 bg-emerald-50 rounded">
                            CONVERTIDO
                          </span>
                        )}
                        <button
                          onClick={() => openModal(contact)}
                          className="p-2 text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
                          data-testid={`edit-contact-${contact.id}`}
                        >
                          <Edit2 size={16} />
                        </button>
                        <button
                          onClick={() => handleDelete(contact.id)}
                          className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                          data-testid={`delete-contact-${contact.id}`}
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-black text-slate-900 uppercase">
                {editingContact ? 'Editar Contacto' : 'Nuevo Contacto'}
              </h3>
              <button onClick={() => setShowModal(false)} className="p-2 hover:bg-slate-100 rounded-lg">
                <X size={20} />
              </button>
            </div>

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
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

              <div className="grid grid-cols-2 gap-4">
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

              <div className="grid grid-cols-2 gap-4">
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
            </div>

            <div className="flex justify-end gap-3 mt-6">
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
