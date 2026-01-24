import React, { useState, useEffect } from 'react';
import { 
  Users, Plus, Phone, Mail, Building2, MapPin, Save, X, Loader2,
  Search, Edit2, Trash2, User, CheckCircle, LogOut
} from 'lucide-react';

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

const API_URL = process.env.REACT_APP_BACKEND_URL;

const PrescriptorAgenda = ({ currentUser, onLogout }) => {
  const [contacts, setContacts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [segmentFilter, setSegmentFilter] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingContact, setEditingContact] = useState(null);
  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    company: '',
    position: '',
    address: '',
    segment: '',
    notes: ''
  });

  useEffect(() => {
    loadContacts();
  }, [currentUser?.id]);

  const loadContacts = async () => {
    if (!currentUser?.id) return;
    setIsLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/crm/contacts/by-prescriptor/${currentUser.id}`);
      if (response.ok) {
        const data = await response.json();
        setContacts(data);
      }
    } catch (err) {
      console.error('Error loading contacts:', err);
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
        segment: contact.segment || '',
        notes: contact.notes || ''
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
        segment: '',
        notes: ''
      });
    }
    setShowModal(true);
  };

  const handleSave = async () => {
    if (!formData.name.trim()) {
      alert('El nombre es obligatorio');
      return;
    }

    setSaving(true);
    try {
      const contactData = {
        ...formData,
        status: 'lead', // Siempre son clientes potenciales
        source: 'prescriptor',
        prescriptorId: currentUser.id,
        prescriptorName: currentUser.clientName
      };

      let response;
      if (editingContact) {
        response = await fetch(`${API_URL}/api/crm/contacts/${editingContact.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(contactData)
        });
      } else {
        response = await fetch(`${API_URL}/api/crm/contacts`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(contactData)
        });
      }

      if (response.ok) {
        setShowModal(false);
        loadContacts();
      } else {
        const err = await response.json();
        alert('Error: ' + (err.detail || 'No se pudo guardar'));
      }
    } catch (err) {
      alert('Error al guardar: ' + err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (contact) => {
    if (!window.confirm(`¿Eliminar contacto "${contact.name}"?`)) return;
    
    try {
      const response = await fetch(`${API_URL}/api/crm/contacts/${contact.id}`, {
        method: 'DELETE'
      });
      if (response.ok) {
        loadContacts();
      }
    } catch (err) {
      alert('Error al eliminar: ' + err.message);
    }
  };

  const filteredContacts = contacts.filter(c => {
    const matchesSearch = !searchQuery || 
      c.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.company?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.phone?.includes(searchQuery);
    const matchesSegment = !segmentFilter || c.segment === segmentFilter;
    return matchesSearch && matchesSegment;
  });

  // Stats
  const totalContacts = contacts.length;
  const bySegment = contacts.reduce((acc, c) => {
    const seg = c.segment || 'SIN SEGMENTO';
    acc[seg] = (acc[seg] || 0) + 1;
    return acc;
  }, {});

  return (
    <div className="min-h-screen bg-gradient-to-br from-amber-50 to-orange-50">
      {/* Header */}
      <div className="bg-white border-b border-amber-200 px-6 py-4 shadow-sm">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-amber-500 rounded-2xl shadow-lg">
              <Users size={28} className="text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-black text-slate-900 uppercase tracking-tight">Mi Agenda de Contactos</h1>
              <p className="text-sm text-amber-600 font-bold">{currentUser?.clientName} · Prescriptor Comercial</p>
            </div>
          </div>
          <button
            onClick={() => openModal()}
            className="flex items-center gap-2 px-5 py-3 bg-amber-500 text-white rounded-xl font-black uppercase text-sm hover:bg-amber-600 transition-all shadow-lg"
            data-testid="new-contact-btn"
          >
            <Plus size={18} />
            Nuevo Contacto
          </button>
          {onLogout && (
            <button
              onClick={onLogout}
              className="flex items-center gap-2 px-4 py-3 bg-slate-200 text-slate-700 rounded-xl font-bold text-sm hover:bg-slate-300 transition-all"
              data-testid="prescriptor-logout-btn"
            >
              <LogOut size={18} />
              Salir
            </button>
          )}
        </div>
      </div>

      <div className="max-w-6xl mx-auto p-6">
        {/* Stats Cards */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-xl p-4 border border-amber-200 shadow-sm">
            <p className="text-3xl font-black text-amber-600">{totalContacts}</p>
            <p className="text-xs font-bold text-slate-500 uppercase">Total Contactos</p>
          </div>
          {Object.entries(bySegment).slice(0, 3).map(([seg, count]) => (
            <div key={seg} className="bg-white rounded-xl p-4 border border-slate-200 shadow-sm">
              <p className="text-3xl font-black text-slate-700">{count}</p>
              <p className="text-[10px] font-bold text-slate-400 uppercase truncate">{seg}</p>
            </div>
          ))}
        </div>

        {/* Filters */}
        <div className="flex items-center gap-4 mb-6">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-amber-400" size={18} />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Buscar por nombre, empresa o teléfono..."
              className="w-full pl-12 pr-4 py-3 bg-white border-2 border-amber-200 rounded-xl text-sm font-bold outline-none focus:border-amber-500"
            />
          </div>
          <select
            value={segmentFilter}
            onChange={(e) => setSegmentFilter(e.target.value)}
            className="px-4 py-3 bg-white border-2 border-amber-200 rounded-xl text-sm font-bold outline-none focus:border-amber-500"
          >
            <option value="">Todos los segmentos</option>
            {CLIENT_SEGMENTS.map(seg => (
              <option key={seg} value={seg}>{seg}</option>
            ))}
          </select>
        </div>

        {/* Contacts List */}
        <div className="bg-white rounded-2xl border border-amber-200 shadow-sm overflow-hidden">
          {isLoading ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="w-8 h-8 text-amber-500 animate-spin" />
            </div>
          ) : filteredContacts.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 text-slate-400">
              <Users className="w-16 h-16 mb-4 opacity-50" />
              <p className="font-black text-lg">Sin contactos</p>
              <p className="text-sm">Añade tu primer contacto potencial</p>
            </div>
          ) : (
            <div className="divide-y divide-amber-100">
              {filteredContacts.map(contact => (
                <div key={contact.id} className="p-4 hover:bg-amber-50/50 transition-colors flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-amber-100 rounded-full flex items-center justify-center">
                      <span className="text-amber-600 font-black text-lg">
                        {contact.name?.charAt(0).toUpperCase()}
                      </span>
                    </div>
                    <div>
                      <p className="font-black text-slate-900">{contact.name}</p>
                      <div className="flex items-center gap-3 text-xs text-slate-500">
                        {contact.company && (
                          <span className="flex items-center gap-1">
                            <Building2 size={12} /> {contact.company}
                          </span>
                        )}
                        {contact.phone && (
                          <span className="flex items-center gap-1">
                            <Phone size={12} /> {contact.phone}
                          </span>
                        )}
                        {contact.email && (
                          <span className="flex items-center gap-1">
                            <Mail size={12} /> {contact.email}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    {contact.segment && (
                      <span className="text-[10px] px-3 py-1 bg-violet-100 text-violet-700 rounded-full font-bold">
                        {contact.segment}
                      </span>
                    )}
                    {contact.assignedToName && (
                      <span className="text-[10px] px-3 py-1 bg-emerald-100 text-emerald-700 rounded-full font-bold flex items-center gap-1">
                        <CheckCircle size={10} /> Asignado: {contact.assignedToName}
                      </span>
                    )}
                    <button
                      onClick={() => openModal(contact)}
                      className="p-2 text-amber-600 hover:bg-amber-100 rounded-lg transition-colors"
                    >
                      <Edit2 size={16} />
                    </button>
                    <button
                      onClick={() => handleDelete(contact)}
                      className="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Info Box */}
        <div className="mt-6 p-4 bg-amber-100 rounded-xl border border-amber-200">
          <p className="text-sm text-amber-800">
            <strong>ℹ️ Información:</strong> Los contactos que añadas aquí son clientes potenciales. 
            El administrador los revisará y los asignará al comercial correspondiente para su gestión.
          </p>
        </div>
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden">
            <div className="bg-amber-500 text-white px-6 py-4 flex justify-between items-center">
              <h2 className="font-black text-lg uppercase">
                {editingContact ? 'Editar Contacto' : 'Nuevo Contacto Potencial'}
              </h2>
              <button onClick={() => setShowModal(false)} className="p-1 hover:bg-white/20 rounded">
                <X size={20} />
              </button>
            </div>

            <div className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Nombre *</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  className="w-full px-4 py-3 border-2 border-slate-200 rounded-xl text-sm font-bold outline-none focus:border-amber-500"
                  placeholder="Nombre completo"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Teléfono</label>
                  <input
                    type="tel"
                    value={formData.phone}
                    onChange={(e) => setFormData({...formData, phone: e.target.value})}
                    className="w-full px-4 py-3 border-2 border-slate-200 rounded-xl text-sm font-bold outline-none focus:border-amber-500"
                    placeholder="600 000 000"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Email</label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({...formData, email: e.target.value})}
                    className="w-full px-4 py-3 border-2 border-slate-200 rounded-xl text-sm font-bold outline-none focus:border-amber-500"
                    placeholder="email@ejemplo.com"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Empresa</label>
                  <input
                    type="text"
                    value={formData.company}
                    onChange={(e) => setFormData({...formData, company: e.target.value})}
                    className="w-full px-4 py-3 border-2 border-slate-200 rounded-xl text-sm font-bold outline-none focus:border-amber-500"
                    placeholder="Nombre de empresa"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Cargo</label>
                  <input
                    type="text"
                    value={formData.position}
                    onChange={(e) => setFormData({...formData, position: e.target.value})}
                    className="w-full px-4 py-3 border-2 border-slate-200 rounded-xl text-sm font-bold outline-none focus:border-amber-500"
                    placeholder="Cargo o puesto"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Segmento / Tipo de Cliente</label>
                <select
                  value={formData.segment}
                  onChange={(e) => setFormData({...formData, segment: e.target.value})}
                  className="w-full px-4 py-3 border-2 border-violet-200 rounded-xl text-sm font-bold outline-none focus:border-violet-500"
                >
                  <option value="">Seleccionar segmento...</option>
                  {CLIENT_SEGMENTS.map(seg => (
                    <option key={seg} value={seg}>{seg}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Dirección</label>
                <input
                  type="text"
                  value={formData.address}
                  onChange={(e) => setFormData({...formData, address: e.target.value})}
                  className="w-full px-4 py-3 border-2 border-slate-200 rounded-xl text-sm font-bold outline-none focus:border-amber-500"
                  placeholder="Dirección completa"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Notas / Observaciones</label>
                <textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({...formData, notes: e.target.value})}
                  rows={3}
                  className="w-full px-4 py-3 border-2 border-slate-200 rounded-xl text-sm font-bold outline-none focus:border-amber-500 resize-none"
                  placeholder="Información adicional sobre el contacto..."
                />
              </div>
            </div>

            <div className="px-6 py-4 bg-slate-50 border-t border-slate-200 flex justify-end gap-3">
              <button
                onClick={() => setShowModal(false)}
                className="px-5 py-2.5 text-slate-600 hover:bg-slate-200 rounded-xl font-bold text-sm"
              >
                Cancelar
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                className="flex items-center gap-2 px-5 py-2.5 bg-amber-500 text-white rounded-xl font-bold text-sm hover:bg-amber-600 disabled:opacity-50"
              >
                {saving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
                Guardar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PrescriptorAgenda;
