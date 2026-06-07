import React, { useState, useEffect, useMemo } from 'react';
import { 
  Users, Plus, Phone, Mail, Building2, Save, X, Loader2,
  Search, Edit2, Trash2, CheckCircle, LogOut, Calendar,
  ChevronLeft, ChevronRight, StickyNote, Briefcase, UserPlus
} from 'lucide-react';
import {
  format, startOfMonth, endOfMonth, startOfWeek, endOfWeek,
  addDays, addMonths, subMonths, isSameMonth, isSameDay, isToday
} from 'date-fns';
import { es } from 'date-fns/locale';
import { googleCalendarAPI } from '../services/api';
import GoogleCalendarConnect from './GoogleCalendarConnect';
import GoogleSyncModal from './GoogleSyncModal';

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
  const [activeTab, setActiveTab] = useState('contacts');
  const [systemLogo, setSystemLogo] = useState(null);
  
  // Contacts state
  const [contacts, setContacts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [segmentFilter, setSegmentFilter] = useState('');
  const [showContactModal, setShowContactModal] = useState(false);
  const [editingContact, setEditingContact] = useState(null);
  const [saving, setSaving] = useState(false);
  const [contactFormData, setContactFormData] = useState({
    name: '', email: '', phone: '', company: '', position: '', address: '', segment: '', notes: ''
  });

  // Calendar state
  const [currentDate, setCurrentDate] = useState(new Date());
  const [calendarNotes, setCalendarNotes] = useState([]);
  const [loadingNotes, setLoadingNotes] = useState(false);
  const [selectedDate, setSelectedDate] = useState(null);
  const [showNoteModal, setShowNoteModal] = useState(false);
  const [editingNote, setEditingNote] = useState(null);
  const [noteFormData, setNoteFormData] = useState({ title: '', content: '', contactId: '', contactName: '' });
  const [savingNote, setSavingNote] = useState(false);
  const [showNewContactInNote, setShowNewContactInNote] = useState(false);
  const [newContactInNote, setNewContactInNote] = useState({ name: '', phone: '', company: '', segment: '' });
  // Google Calendar (por usuario, aislado en el backend)
  const [googleConnected, setGoogleConnected] = useState(false);
  const [pendingGoogleEvent, setPendingGoogleEvent] = useState(null);

  useEffect(() => {
    if (currentUser?.id) {
      loadContacts();
      loadCalendarNotes();
      loadSystemLogo();
    }
  }, [currentUser?.id]);

  const loadSystemLogo = async () => {
    try {
      const response = await fetch(`${API_URL}/api/settings`);
      if (response.ok) {
        const data = await response.json();
        if (data.logo) {
          setSystemLogo(data.logo);
        }
      }
    } catch (err) {
      console.error('Error loading system logo:', err);
    }
  };

  useEffect(() => {
    if (currentUser?.id) {
      loadCalendarNotes();
    }
  }, [currentDate]);

  // ========== CONTACTS FUNCTIONS ==========
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

  const openContactModal = (contact = null) => {
    if (contact) {
      setEditingContact(contact);
      setContactFormData({
        name: contact.name || '', email: contact.email || '', phone: contact.phone || '',
        company: contact.company || '', position: contact.position || '', address: contact.address || '',
        segment: contact.segment || '', notes: contact.notes || ''
      });
    } else {
      setEditingContact(null);
      setContactFormData({ name: '', email: '', phone: '', company: '', position: '', address: '', segment: '', notes: '' });
    }
    setShowContactModal(true);
  };

  const handleSaveContact = async () => {
    if (!contactFormData.name.trim()) {
      alert('El nombre es obligatorio');
      return;
    }
    setSaving(true);
    try {
      const contactData = {
        ...contactFormData,
        status: 'lead',
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
        setShowContactModal(false);
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

  const handleDeleteContact = async (contact) => {
    if (!window.confirm(`¿Eliminar contacto "${contact.name}"?`)) return;
    try {
      const response = await fetch(`${API_URL}/api/crm/contacts/${contact.id}`, { method: 'DELETE' });
      if (response.ok) loadContacts();
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

  // ========== CALENDAR FUNCTIONS ==========
  const loadCalendarNotes = async () => {
    if (!currentUser?.id) return;
    setLoadingNotes(true);
    try {
      const start = startOfMonth(currentDate);
      const end = endOfMonth(currentDate);
      const response = await fetch(
        `${API_URL}/api/prescriptor/notes?prescriptor_id=${currentUser.id}&start=${format(start, 'yyyy-MM-dd')}&end=${format(end, 'yyyy-MM-dd')}`
      );
      if (response.ok) {
        const data = await response.json();
        setCalendarNotes(data);
      }
    } catch (err) {
      console.error('Error loading calendar notes:', err);
    } finally {
      setLoadingNotes(false);
    }
  };

  const openNoteModal = (date, note = null) => {
    setSelectedDate(date);
    setShowNewContactInNote(false);
    setNewContactInNote({ name: '', phone: '', company: '', segment: '' });
    if (note) {
      setEditingNote(note);
      setNoteFormData({ 
        title: note.title || '', 
        content: note.content || '',
        contactId: note.contactId || '',
        contactName: note.contactName || ''
      });
    } else {
      setEditingNote(null);
      setNoteFormData({ title: '', content: '', contactId: '', contactName: '' });
    }
    setShowNoteModal(true);
  };

  const handleSaveNote = async () => {
    if (!noteFormData.title.trim() && !noteFormData.content.trim()) {
      alert('Escribe un título o contenido para la nota');
      return;
    }
    setSavingNote(true);
    try {
      let contactId = noteFormData.contactId;
      let contactName = noteFormData.contactName;

      // If creating a new contact from the note modal
      if (showNewContactInNote && newContactInNote.name.trim()) {
        const contactData = {
          name: newContactInNote.name,
          phone: newContactInNote.phone,
          company: newContactInNote.company,
          segment: newContactInNote.segment,
          status: 'lead',
          source: 'prescriptor',
          prescriptorId: currentUser.id,
          prescriptorName: currentUser.clientName
        };

        const contactResponse = await fetch(`${API_URL}/api/crm/contacts`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(contactData)
        });

        if (contactResponse.ok) {
          const newContact = await contactResponse.json();
          contactId = newContact.id;
          contactName = newContact.name;
          // Refresh contacts list
          loadContacts();
        }
      }

      const noteData = {
        ...noteFormData,
        contactId,
        contactName,
        date: format(selectedDate, 'yyyy-MM-dd'),
        prescriptorId: currentUser.id,
        prescriptorName: currentUser.clientName
      };

      let response;
      if (editingNote) {
        response = await fetch(`${API_URL}/api/prescriptor/notes/${editingNote.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(noteData)
        });
      } else {
        response = await fetch(`${API_URL}/api/prescriptor/notes`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(noteData)
        });
      }

      if (response.ok) {
        const saved = await response.json().catch(() => null);
        setShowNoteModal(false);
        loadCalendarNotes();
        // Si tiene Google conectado, preguntar si guardar también allí (notas nuevas).
        if (googleConnected && !editingNote) {
          setPendingGoogleEvent({
            title: noteData.title || 'Nota',
            startDate: noteData.date,
            endDate: noteData.date,
            description: noteData.content || '',
            allDay: true,
            erpId: saved?.id,
          });
        }
      } else {
        const err = await response.json();
        alert('Error: ' + (err.detail || 'No se pudo guardar'));
      }
    } catch (err) {
      alert('Error al guardar nota: ' + err.message);
    } finally {
      setSavingNote(false);
    }
  };

  const handleDeleteNote = async (note) => {
    if (!window.confirm('¿Eliminar esta nota?')) return;
    try {
      const response = await fetch(`${API_URL}/api/prescriptor/notes/${note.id}`, { method: 'DELETE' });
      if (response.ok) {
        setShowNoteModal(false);
        loadCalendarNotes();
      }
    } catch (err) {
      alert('Error al eliminar: ' + err.message);
    }
  };

  // Calendar grid generation
  const calendarDays = useMemo(() => {
    const monthStart = startOfMonth(currentDate);
    const monthEnd = endOfMonth(currentDate);
    const startDate = startOfWeek(monthStart, { weekStartsOn: 1 });
    const endDate = endOfWeek(monthEnd, { weekStartsOn: 1 });

    const days = [];
    let day = startDate;
    while (day <= endDate) {
      days.push(day);
      day = addDays(day, 1);
    }
    return days;
  }, [currentDate]);

  const getNotesForDate = (date) => {
    const dateStr = format(date, 'yyyy-MM-dd');
    return calendarNotes.filter(n => n.date === dateStr);
  };

  // Stats
  const totalContacts = contacts.length;
  const totalNotes = calendarNotes.length;

  return (
    <div className="min-h-screen bg-gradient-to-br from-amber-50 to-orange-50">
      {/* Header */}
      <div className="bg-white border-b border-amber-200 px-6 py-4 shadow-sm">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            {/* Logo from System Settings */}
            {(systemLogo || currentUser?.companyLogo) ? (
              <img 
                src={systemLogo || currentUser.companyLogo} 
                alt="Logo" 
                className="h-16 w-auto object-contain"
              />
            ) : (
              <div className="p-3 bg-amber-500 rounded-2xl shadow-lg">
                <Briefcase size={28} className="text-white" />
              </div>
            )}
            <div>
              <h1 className="text-2xl font-black text-slate-900 uppercase tracking-tight">Agenda de Negocios</h1>
              <p className="text-sm text-amber-600 font-bold">{currentUser?.clientName} · Colaborador Comercial</p>
            </div>
          </div>
          
          {/* Tabs */}
          <div className="flex items-center gap-2 bg-amber-100 p-1 rounded-xl">
            <button
              onClick={() => setActiveTab('contacts')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-bold text-sm transition-all ${
                activeTab === 'contacts' 
                  ? 'bg-amber-500 text-white shadow' 
                  : 'text-amber-700 hover:bg-amber-200'
              }`}
              data-testid="tab-contacts"
            >
              <Users size={16} />
              Contactos
            </button>
            <button
              onClick={() => setActiveTab('calendar')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-bold text-sm transition-all ${
                activeTab === 'calendar' 
                  ? 'bg-amber-500 text-white shadow' 
                  : 'text-amber-700 hover:bg-amber-200'
              }`}
              data-testid="tab-calendar"
            >
              <Calendar size={16} />
              Calendario
            </button>
          </div>
          
          <div className="flex items-center gap-3">
            {activeTab === 'contacts' && (
              <button
                onClick={() => openContactModal()}
                className="flex items-center gap-2 px-5 py-3 bg-amber-500 text-white rounded-xl font-black uppercase text-sm hover:bg-amber-600 transition-all shadow-lg"
                data-testid="new-contact-btn"
              >
                <Plus size={18} />
                Nuevo Contacto
              </button>
            )}
            <GoogleCalendarConnect compact onStatusChange={(s) => setGoogleConnected(!!s.connected)} />
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
      </div>

      <div className="max-w-6xl mx-auto p-6">
        {/* CONTACTS TAB */}
        {activeTab === 'contacts' && (
          <>
            {/* Stats Cards */}
            <div className="grid grid-cols-4 gap-4 mb-6">
              <div className="bg-white rounded-xl p-4 border border-amber-200 shadow-sm">
                <p className="text-3xl font-black text-amber-600">{totalContacts}</p>
                <p className="text-xs font-bold text-slate-500 uppercase">Total Contactos</p>
              </div>
              {Object.entries(contacts.reduce((acc, c) => {
                const seg = c.segment || 'SIN SEGMENTO';
                acc[seg] = (acc[seg] || 0) + 1;
                return acc;
              }, {})).slice(0, 3).map(([seg, count]) => (
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
                          onClick={() => openContactModal(contact)}
                          className="p-2 text-amber-600 hover:bg-amber-100 rounded-lg transition-colors"
                        >
                          <Edit2 size={16} />
                        </button>
                        <button
                          onClick={() => handleDeleteContact(contact)}
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
          </>
        )}

        {/* CALENDAR TAB */}
        {activeTab === 'calendar' && (
          <>
            {/* Calendar Header */}
            <div className="bg-white rounded-2xl border border-amber-200 shadow-sm overflow-hidden mb-6">
              <div className="px-6 py-4 border-b border-amber-100 flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <button
                    onClick={() => setCurrentDate(subMonths(currentDate, 1))}
                    className="p-2 hover:bg-amber-100 rounded-lg transition-colors"
                  >
                    <ChevronLeft size={20} className="text-amber-600" />
                  </button>
                  <h2 className="text-xl font-black text-slate-900 uppercase min-w-[200px] text-center">
                    {format(currentDate, 'MMMM yyyy', { locale: es })}
                  </h2>
                  <button
                    onClick={() => setCurrentDate(addMonths(currentDate, 1))}
                    className="p-2 hover:bg-amber-100 rounded-lg transition-colors"
                  >
                    <ChevronRight size={20} className="text-amber-600" />
                  </button>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-sm text-slate-500 font-bold">
                    {totalNotes} notas este mes
                  </span>
                  <button
                    onClick={() => setCurrentDate(new Date())}
                    className="px-4 py-2 bg-amber-100 text-amber-700 rounded-lg font-bold text-sm hover:bg-amber-200 transition-colors"
                  >
                    Hoy
                  </button>
                </div>
              </div>

              {/* Calendar Grid */}
              <div className="p-4">
                {/* Week Headers */}
                <div className="grid grid-cols-7 mb-2">
                  {['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'].map(day => (
                    <div key={day} className="py-2 text-center text-xs font-black text-slate-400 uppercase">
                      {day}
                    </div>
                  ))}
                </div>

                {/* Days Grid */}
                {loadingNotes ? (
                  <div className="flex items-center justify-center py-20">
                    <Loader2 className="w-8 h-8 text-amber-500 animate-spin" />
                  </div>
                ) : (
                  <div className="grid grid-cols-7 gap-1">
                    {calendarDays.map((day, idx) => {
                      const dayNotes = getNotesForDate(day);
                      const isCurrentMonth = isSameMonth(day, currentDate);
                      const isCurrentDay = isToday(day);
                      
                      return (
                        <div
                          key={idx}
                          onClick={() => openNoteModal(day, dayNotes[0] || null)}
                          className={`min-h-[100px] p-2 rounded-xl border cursor-pointer transition-all hover:border-amber-400 hover:shadow-md ${
                            isCurrentMonth 
                              ? isCurrentDay 
                                ? 'bg-amber-100 border-amber-400' 
                                : 'bg-white border-slate-200'
                              : 'bg-slate-50 border-slate-100'
                          }`}
                        >
                          <div className={`text-right mb-1 ${
                            isCurrentMonth 
                              ? isCurrentDay 
                                ? 'text-amber-700 font-black' 
                                : 'text-slate-700 font-bold'
                              : 'text-slate-400 font-medium'
                          }`}>
                            {format(day, 'd')}
                          </div>
                          
                          {dayNotes.length > 0 && (
                            <div className="space-y-1">
                              {dayNotes.slice(0, 2).map((note, nIdx) => (
                                <div 
                                  key={nIdx}
                                  className="text-[10px] px-2 py-1 bg-amber-200 text-amber-800 rounded font-bold truncate"
                                  title={note.title || note.content}
                                >
                                  <StickyNote size={10} className="inline mr-1" />
                                  {note.title || note.content?.substring(0, 20)}
                                </div>
                              ))}
                              {dayNotes.length > 2 && (
                                <p className="text-[10px] text-amber-600 font-bold pl-2">
                                  +{dayNotes.length - 2} más
                                </p>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>

            {/* Info Box */}
            <div className="p-4 bg-amber-100 rounded-xl border border-amber-200">
              <p className="text-sm text-amber-800">
                <strong>📅 Calendario:</strong> Haz clic en cualquier día para añadir notas sobre citas, fechas importantes o recordatorios.
                El administrador puede ver tu calendario desde el CRM.
              </p>
            </div>
          </>
        )}
      </div>

      {/* Contact Modal */}
      {showContactModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden">
            <div className="bg-amber-500 text-white px-6 py-4 flex justify-between items-center">
              <h2 className="font-black text-lg uppercase">
                {editingContact ? 'Editar Contacto' : 'Nuevo Contacto Potencial'}
              </h2>
              <button onClick={() => setShowContactModal(false)} className="p-1 hover:bg-white/20 rounded">
                <X size={20} />
              </button>
            </div>

            <div className="p-6 space-y-4 max-h-[60vh] overflow-y-auto">
              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Nombre *</label>
                <input
                  type="text"
                  value={contactFormData.name}
                  onChange={(e) => setContactFormData({...contactFormData, name: e.target.value})}
                  className="w-full px-4 py-3 border-2 border-slate-200 rounded-xl text-sm font-bold outline-none focus:border-amber-500"
                  placeholder="Nombre completo"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Teléfono</label>
                  <input
                    type="tel"
                    value={contactFormData.phone}
                    onChange={(e) => setContactFormData({...contactFormData, phone: e.target.value})}
                    className="w-full px-4 py-3 border-2 border-slate-200 rounded-xl text-sm font-bold outline-none focus:border-amber-500"
                    placeholder="600 000 000"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Email</label>
                  <input
                    type="email"
                    value={contactFormData.email}
                    onChange={(e) => setContactFormData({...contactFormData, email: e.target.value})}
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
                    value={contactFormData.company}
                    onChange={(e) => setContactFormData({...contactFormData, company: e.target.value})}
                    className="w-full px-4 py-3 border-2 border-slate-200 rounded-xl text-sm font-bold outline-none focus:border-amber-500"
                    placeholder="Nombre de empresa"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Cargo</label>
                  <input
                    type="text"
                    value={contactFormData.position}
                    onChange={(e) => setContactFormData({...contactFormData, position: e.target.value})}
                    className="w-full px-4 py-3 border-2 border-slate-200 rounded-xl text-sm font-bold outline-none focus:border-amber-500"
                    placeholder="Cargo o puesto"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Segmento</label>
                <select
                  value={contactFormData.segment}
                  onChange={(e) => setContactFormData({...contactFormData, segment: e.target.value})}
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
                  value={contactFormData.address}
                  onChange={(e) => setContactFormData({...contactFormData, address: e.target.value})}
                  className="w-full px-4 py-3 border-2 border-slate-200 rounded-xl text-sm font-bold outline-none focus:border-amber-500"
                  placeholder="Dirección completa"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Notas</label>
                <textarea
                  value={contactFormData.notes}
                  onChange={(e) => setContactFormData({...contactFormData, notes: e.target.value})}
                  rows={3}
                  className="w-full px-4 py-3 border-2 border-slate-200 rounded-xl text-sm font-bold outline-none focus:border-amber-500 resize-none"
                  placeholder="Información adicional sobre el contacto..."
                />
              </div>
            </div>

            <div className="px-6 py-4 bg-slate-50 border-t border-slate-200 flex justify-end gap-3">
              <button
                onClick={() => setShowContactModal(false)}
                className="px-5 py-2.5 text-slate-600 hover:bg-slate-200 rounded-xl font-bold text-sm"
              >
                Cancelar
              </button>
              <button
                onClick={handleSaveContact}
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

      {/* Note Modal */}
      {showNoteModal && selectedDate && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden">
            <div className="bg-amber-500 text-white px-6 py-4 flex justify-between items-center">
              <div>
                <h2 className="font-black text-lg uppercase">
                  {editingNote ? 'Editar Nota' : 'Nueva Nota'}
                </h2>
                <p className="text-amber-100 text-sm font-bold">
                  {format(selectedDate, "EEEE, d 'de' MMMM yyyy", { locale: es })}
                </p>
              </div>
              <button onClick={() => setShowNoteModal(false)} className="p-1 hover:bg-white/20 rounded">
                <X size={20} />
              </button>
            </div>

            <div className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Título</label>
                <input
                  type="text"
                  value={noteFormData.title}
                  onChange={(e) => setNoteFormData({...noteFormData, title: e.target.value})}
                  className="w-full px-4 py-3 border-2 border-slate-200 rounded-xl text-sm font-bold outline-none focus:border-amber-500"
                  placeholder="Ej: Cita con cliente, Llamar a..."
                />
              </div>

              {/* Contact selector */}
              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase mb-1">
                  👤 Contacto Asociado (opcional)
                </label>
                {!showNewContactInNote ? (
                  <div className="flex gap-2">
                    <select
                      value={noteFormData.contactId}
                      onChange={(e) => {
                        const selectedContact = contacts.find(c => c.id === e.target.value);
                        setNoteFormData({
                          ...noteFormData, 
                          contactId: e.target.value,
                          contactName: selectedContact?.name || ''
                        });
                      }}
                      className="flex-1 px-4 py-3 border-2 border-slate-200 rounded-xl text-sm font-bold outline-none focus:border-amber-500"
                    >
                      <option value="">Sin contacto asociado</option>
                      {contacts.map(c => (
                        <option key={c.id} value={c.id}>{c.name} {c.company ? `(${c.company})` : ''}</option>
                      ))}
                    </select>
                    <button
                      type="button"
                      onClick={() => setShowNewContactInNote(true)}
                      className="px-4 py-3 bg-emerald-100 text-emerald-700 rounded-xl font-bold text-sm hover:bg-emerald-200 flex items-center gap-2"
                      title="Crear nuevo contacto"
                    >
                      <UserPlus size={16} />
                    </button>
                  </div>
                ) : (
                  <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <p className="text-xs font-bold text-emerald-700 uppercase">Nuevo Contacto</p>
                      <button
                        type="button"
                        onClick={() => {
                          setShowNewContactInNote(false);
                          setNewContactInNote({ name: '', phone: '', company: '', segment: '' });
                        }}
                        className="text-slate-400 hover:text-slate-600"
                      >
                        <X size={16} />
                      </button>
                    </div>
                    <input
                      type="text"
                      value={newContactInNote.name}
                      onChange={(e) => setNewContactInNote({...newContactInNote, name: e.target.value})}
                      className="w-full px-3 py-2 border border-emerald-200 rounded-lg text-sm font-bold outline-none focus:border-emerald-500"
                      placeholder="Nombre del contacto *"
                    />
                    <div className="grid grid-cols-2 gap-2">
                      <input
                        type="tel"
                        value={newContactInNote.phone}
                        onChange={(e) => setNewContactInNote({...newContactInNote, phone: e.target.value})}
                        className="px-3 py-2 border border-emerald-200 rounded-lg text-sm font-bold outline-none focus:border-emerald-500"
                        placeholder="Teléfono"
                      />
                      <input
                        type="text"
                        value={newContactInNote.company}
                        onChange={(e) => setNewContactInNote({...newContactInNote, company: e.target.value})}
                        className="px-3 py-2 border border-emerald-200 rounded-lg text-sm font-bold outline-none focus:border-emerald-500"
                        placeholder="Empresa"
                      />
                    </div>
                    <select
                      value={newContactInNote.segment}
                      onChange={(e) => setNewContactInNote({...newContactInNote, segment: e.target.value})}
                      className="w-full px-3 py-2 border border-violet-200 rounded-lg text-sm font-bold outline-none focus:border-violet-500 bg-white"
                    >
                      <option value="">Tipo de negocio...</option>
                      {CLIENT_SEGMENTS.map(seg => (
                        <option key={seg} value={seg}>{seg}</option>
                      ))}
                    </select>
                  </div>
                )}
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Contenido</label>
                <textarea
                  value={noteFormData.content}
                  onChange={(e) => setNoteFormData({...noteFormData, content: e.target.value})}
                  rows={3}
                  className="w-full px-4 py-3 border-2 border-slate-200 rounded-xl text-sm font-bold outline-none focus:border-amber-500 resize-none"
                  placeholder="Escribe aquí los detalles de la nota..."
                />
              </div>
            </div>

            <div className="px-6 py-4 bg-slate-50 border-t border-slate-200 flex justify-between">
              {editingNote ? (
                <button
                  onClick={() => handleDeleteNote(editingNote)}
                  className="flex items-center gap-2 px-4 py-2.5 text-red-600 hover:bg-red-50 rounded-xl font-bold text-sm"
                >
                  <Trash2 size={16} />
                  Eliminar
                </button>
              ) : (
                <div />
              )}
              <div className="flex gap-3">
                <button
                  onClick={() => setShowNoteModal(false)}
                  className="px-5 py-2.5 text-slate-600 hover:bg-slate-200 rounded-xl font-bold text-sm"
                >
                  Cancelar
                </button>
                <button
                  onClick={handleSaveNote}
                  disabled={savingNote}
                  className="flex items-center gap-2 px-5 py-2.5 bg-amber-500 text-white rounded-xl font-bold text-sm hover:bg-amber-600 disabled:opacity-50"
                >
                  {savingNote ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
                  Guardar
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Preguntar si guardar también en Google Calendar */}
      <GoogleSyncModal
        event={pendingGoogleEvent}
        defaultContext="prescriptor"
        currentUser={currentUser}
        onClose={() => setPendingGoogleEvent(null)}
      />
    </div>
  );
};

export default PrescriptorAgenda;
