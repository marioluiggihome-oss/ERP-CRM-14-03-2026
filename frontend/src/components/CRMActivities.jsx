import { getToken } from '../services/api';
import React, { useState, useEffect } from 'react';
import { 
  Phone, MapPin, Users, Calendar, Clock, Plus, Search, Filter, 
  ChevronDown, ChevronUp, Trash2, Edit2, Check, X, User,
  PhoneCall, Building2, Coffee, Video, Mail, MessageSquare
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Tipos de actividades con iconos y colores
const ACTIVITY_TYPES = {
  call: { label: 'Llamada', icon: PhoneCall, color: 'blue', bgColor: 'bg-blue-100', textColor: 'text-blue-700', borderColor: 'border-blue-300' },
  visit: { label: 'Visita', icon: MapPin, color: 'green', bgColor: 'bg-green-100', textColor: 'text-green-700', borderColor: 'border-green-300' },
  meeting: { label: 'Reunión', icon: Users, color: 'purple', bgColor: 'bg-purple-100', textColor: 'text-purple-700', borderColor: 'border-purple-300' },
  video: { label: 'Videollamada', icon: Video, color: 'indigo', bgColor: 'bg-indigo-100', textColor: 'text-indigo-700', borderColor: 'border-indigo-300' },
  email: { label: 'Email', icon: Mail, color: 'orange', bgColor: 'bg-orange-100', textColor: 'text-orange-700', borderColor: 'border-orange-300' },
  note: { label: 'Nota', icon: MessageSquare, color: 'slate', bgColor: 'bg-slate-100', textColor: 'text-slate-700', borderColor: 'border-slate-300' },
};

const CRMActivities = ({ currentUser }) => {
  const [activities, setActivities] = useState([]);
  const [contacts, setContacts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [filterDate, setFilterDate] = useState('all'); // all, today, week, month
  const [expandedId, setExpandedId] = useState(null);
  
  const [formData, setFormData] = useState({
    type: 'call',
    contactId: '',
    contactName: '',
    date: new Date().toISOString().split('T')[0],
    time: new Date().toTimeString().slice(0, 5),
    duration: 15,
    subject: '',
    notes: '',
    outcome: ''
  });

  // Cargar actividades y contactos
  useEffect(() => {
    fetchActivities();
    fetchContacts();
    // Mantener el listado al día: refrescar al volver a la ventana/pestaña
    const refresh = () => { if (!document.hidden) fetchActivities(); };
    window.addEventListener('focus', refresh);
    document.addEventListener('visibilitychange', refresh);
    return () => {
      window.removeEventListener('focus', refresh);
      document.removeEventListener('visibilitychange', refresh);
    };
  }, [currentUser]);

  const fetchActivities = async () => {
    try {
      const response = await fetch(`${API_URL}/api/crm/activities`, {
        headers: { 'Authorization': `Bearer ${getToken()}` }
      });
      if (response.ok) {
        const data = await response.json();
        setActivities(data);
      }
    } catch (error) {
      console.error('Error loading activities:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchContacts = async () => {
    try {
      const response = await fetch(`${API_URL}/api/crm/contacts`, {
        headers: { 'Authorization': `Bearer ${getToken()}` }
      });
      if (response.ok) {
        const data = await response.json();
        setContacts(data);
      }
    } catch (error) {
      console.error('Error loading contacts:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const url = editingId 
        ? `${API_URL}/api/crm/activities/${editingId}` 
        : `${API_URL}/api/crm/activities`;
      
      const response = await fetch(url, {
        method: editingId ? 'PUT' : 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getToken()}`
        },
        body: JSON.stringify({
          activityType: formData.type || 'call',
          description: [formData.subject, formData.notes].filter(Boolean).join(' - ') || formData.subject || 'Sin descripción',
          contactId: formData.contactId || null,
          title: formData.subject || '',
          dueDate: formData.date || null,
          dueTime: formData.time || null,
          userId: currentUser?.id || '',
          userName: currentUser?.clientName || currentUser?.username || ''
        })
      });

      if (response.ok) {
        fetchActivities();
        resetForm();
      } else {
        let detail = 'No se pudo registrar la actividad';
        try {
          const err = await response.json();
          detail = err.detail || detail;
        } catch (_) {}
        alert(`Error: ${detail}`);
      }
    } catch (error) {
      console.error('Error saving activity:', error);
      alert('Error de conexión al registrar la actividad');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('¿Eliminar esta actividad?')) return;
    try {
      await fetch(`${API_URL}/api/crm/activities/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${getToken()}` }
      });
      fetchActivities();
    } catch (error) {
      console.error('Error deleting activity:', error);
    }
  };

  const handleEdit = (activity) => {
    setFormData({
      type: activity.activityType || activity.type || 'call',
      contactId: activity.contactId || '',
      contactName: activity.contactName || '',
      date: activity.date?.split('T')[0] || new Date().toISOString().split('T')[0],
      time: activity.time || '09:00',
      duration: activity.duration || 15,
      subject: activity.subject || '',
      notes: activity.notes || '',
      outcome: activity.outcome || ''
    });
    setEditingId(activity.id);
    setShowForm(true);
  };

  const resetForm = () => {
    setFormData({
      type: 'call',
      contactId: '',
      contactName: '',
      date: new Date().toISOString().split('T')[0],
      time: new Date().toTimeString().slice(0, 5),
      duration: 15,
      subject: '',
      notes: '',
      outcome: ''
    });
    setEditingId(null);
    setShowForm(false);
  };

  // Filtrar actividades
  // Campo de fecha robusto: usa date, dueDate o createdAt según lo que traiga el backend
  const getActivityDate = (a) => a.date || a.dueDate || (a.createdAt ? String(a.createdAt).slice(0, 10) : '');

  const filteredActivities = activities.filter(activity => {
    const q = searchTerm.toLowerCase();
    const matchesSearch = !q ||
      (activity.title || '').toLowerCase().includes(q) ||
      (activity.subject || '').toLowerCase().includes(q) ||
      (activity.contactName || '').toLowerCase().includes(q) ||
      (activity.notes || '').toLowerCase().includes(q) ||
      (activity.description || '').toLowerCase().includes(q);

    const matchesType = filterType === 'all' || (activity.activityType || activity.type) === filterType;

    let matchesDate = true;
    const rawDate = getActivityDate(activity);
    if (filterDate !== 'all' && rawDate) {
      const activityDate = new Date(rawDate);
      const today = new Date();
      today.setHours(0, 0, 0, 0);

      if (filterDate === 'today') {
        matchesDate = activityDate.toDateString() === today.toDateString();
      } else if (filterDate === 'week') {
        const weekAgo = new Date(today);
        weekAgo.setDate(weekAgo.getDate() - 7);
        matchesDate = activityDate >= weekAgo;
      } else if (filterDate === 'month') {
        const monthAgo = new Date(today);
        monthAgo.setMonth(monthAgo.getMonth() - 1);
        matchesDate = activityDate >= monthAgo;
      }
    }

    return matchesSearch && matchesType && matchesDate;
  }).sort((a, b) => {
    const dateA = new Date(`${getActivityDate(a)}T${a.time || a.dueTime || '00:00'}`);
    const dateB = new Date(`${getActivityDate(b)}T${b.time || b.dueTime || '00:00'}`);
    return dateB - dateA;
  });

  // Agrupar por fecha — usar el campo robusto (date || dueDate || createdAt)
  // para que no salga "Invalid Date" cuando la actividad se guardó en dueDate.
  const groupedActivities = filteredActivities.reduce((groups, activity) => {
    const date = getActivityDate(activity) || 'Sin fecha';
    if (!groups[date]) groups[date] = [];
    groups[date].push(activity);
    return groups;
  }, {});

  // Estadísticas rápidas
  const todayCount = activities.filter(a => {
    const raw = getActivityDate(a);
    if (!raw) return false;
    return new Date(raw).toDateString() === new Date().toDateString();
  }).length;

  const weekCount = activities.filter(a => {
    const raw = getActivityDate(a);
    if (!raw) return false;
    const actDate = new Date(raw);
    const weekAgo = new Date();
    weekAgo.setDate(weekAgo.getDate() - 7);
    return actDate >= weekAgo;
  }).length;

  const formatDate = (dateStr) => {
    if (!dateStr || dateStr === 'Sin fecha') return 'Sin fecha';
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) return 'Sin fecha';
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    if (date.toDateString() === today.toDateString()) return 'Hoy';
    if (date.toDateString() === yesterday.toDateString()) return 'Ayer';

    return date.toLocaleDateString('es-ES', {
      weekday: 'long',
      day: 'numeric',
      month: 'long'
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-slate-50">
      {/* Header con estadísticas - Responsive */}
      <div className="bg-white border-b border-slate-200 p-4 md:p-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="">
            <h1 className="text-xl md:text-2xl font-black text-slate-900">Registro de Actividades</h1>
            <p className="text-xs md:text-sm text-slate-500">Visitas, llamadas, reuniones y más</p>
          </div>
          
          {/* Stats - Grid responsive */}
          <div className="grid grid-cols-3 gap-2 md:gap-4 overflow-hidden">
            <div className="bg-indigo-50 rounded-xl p-3 text-center">
              <p className="text-2xl md:text-3xl font-black text-indigo-600">{todayCount}</p>
              <p className="text-[10px] md:text-xs font-bold text-indigo-500 uppercase">Hoy</p>
            </div>
            <div className="bg-green-50 rounded-xl p-3 text-center">
              <p className="text-2xl md:text-3xl font-black text-green-600">{weekCount}</p>
              <p className="text-[10px] md:text-xs font-bold text-green-500 uppercase">Semana</p>
            </div>
            <div className="bg-purple-50 rounded-xl p-3 text-center">
              <p className="text-2xl md:text-3xl font-black text-purple-600">{activities.length}</p>
              <p className="text-[10px] md:text-xs font-bold text-purple-500 uppercase">Total</p>
            </div>
          </div>
        </div>

        {/* Filtros y búsqueda - Responsive */}
        <div className="mt-4 flex flex-col md:flex-row gap-3">
          {/* Búsqueda */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
            <input
              type="text"
              placeholder="Buscar actividades..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none focus:border-indigo-500"
            />
          </div>

          {/* Filtros - Horizontal scroll en móvil */}
          <div className="flex gap-2 overflow-x-auto pb-2 md:pb-0">
            {/* Filtro por tipo */}
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="px-3 py-2.5 bg-white border border-slate-200 rounded-xl text-sm font-bold text-slate-700 outline-none min-w-[120px]"
            >
              <option value="all">Todos los tipos</option>
              {Object.entries(ACTIVITY_TYPES).map(([key, { label }]) => (
                <option key={key} value={key}>{label}</option>
              ))}
            </select>

            {/* Filtro por fecha */}
            <select
              value={filterDate}
              onChange={(e) => setFilterDate(e.target.value)}
              className="px-3 py-2.5 bg-white border border-slate-200 rounded-xl text-sm font-bold text-slate-700 outline-none min-w-[100px]"
            >
              <option value="all">Todas</option>
              <option value="today">Hoy</option>
              <option value="week">Esta semana</option>
              <option value="month">Este mes</option>
            </select>

            {/* Botón nueva actividad */}
            <button
              onClick={() => setShowForm(true)}
              className="flex items-center gap-2 px-4 py-2.5 bg-indigo-600 text-white rounded-xl font-bold text-sm hover:bg-indigo-700 transition-all shadow-lg whitespace-nowrap"
              data-testid="new-activity-btn"
            >
              <Plus size={18} />
              <span className="hidden md:inline">Nueva Actividad</span>
              <span className="md:hidden">Nueva</span>
            </button>
          </div>
        </div>
      </div>

      {/* Contenido principal */}
      <div className="flex-1 overflow-y-auto p-4 md:p-6">
        {/* Modal/Form para nueva actividad */}
        {showForm && (
          <div className="fixed inset-0 bg-black/50 flex items-end md:items-center justify-center z-50 p-0 md:p-4">
            <div className="bg-white w-full md:w-full md:max-w-lg rounded-t-3xl md:rounded-2xl max-h-[90vh] overflow-y-auto">
              {/* Header del form */}
              <div className="sticky top-0 bg-white border-b border-slate-200 p-4 flex items-center justify-between rounded-t-3xl md:rounded-t-2xl">
                <h2 className="text-lg font-black text-slate-900">
                  {editingId ? 'Editar Actividad' : 'Nueva Actividad'}
                </h2>
                <button onClick={resetForm} className="p-2 hover:bg-slate-100 rounded-full">
                  <X size={20} />
                </button>
              </div>

              <form onSubmit={handleSubmit} className="p-4 space-y-4">
                {/* Tipo de actividad - Grid de iconos */}
                <div>
                  <label className="text-xs font-bold text-slate-600 uppercase mb-2 block">Tipo de actividad</label>
                  <div className="grid grid-cols-3 md:grid-cols-6 gap-2">
                    {Object.entries(ACTIVITY_TYPES).map(([key, { label, icon: Icon, bgColor, textColor, borderColor }]) => (
                      <button
                        key={key}
                        type="button"
                        onClick={() => setFormData({ ...formData, type: key })}
                        className={`flex flex-col items-center gap-1 p-3 rounded-xl border-2 transition-all ${
                          formData.type === key 
                            ? `${bgColor} ${borderColor} ${textColor}` 
                            : 'border-slate-200 hover:border-slate-300'
                        }`}
                      >
                        <Icon size={20} />
                        <span className="text-[10px] font-bold">{label}</span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Contacto */}
                <div>
                  <label className="text-xs font-bold text-slate-600 uppercase mb-2 block">Contacto / Cliente</label>
                  <select
                    value={formData.contactId}
                    onChange={(e) => {
                      const contact = contacts.find(c => c.id === e.target.value);
                      setFormData({
                        ...formData,
                        contactId: e.target.value,
                        contactName: contact ? (contact.name || '').trim() : ''
                      });
                    }}
                    className="w-full p-3 border border-slate-200 rounded-xl text-sm outline-none focus:border-indigo-500"
                  >
                    <option value="">Seleccionar contacto...</option>
                    {contacts.map(contact => (
                      <option key={contact.id} value={contact.id}>
                        {contact.name}{contact.company ? ` (${contact.company})` : ''}
                      </option>
                    ))}
                  </select>
                  {/* O escribir manualmente */}
                  <input
                    type="text"
                    placeholder="O escribe el nombre manualmente..."
                    value={formData.contactName}
                    onChange={(e) => setFormData({ ...formData, contactName: e.target.value, contactId: '' })}
                    className="w-full p-3 border border-slate-200 rounded-xl text-sm outline-none focus:border-indigo-500 mt-2"
                  />
                </div>

                {/* Fecha y Hora - Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-bold text-slate-600 uppercase mb-2 block">Fecha</label>
                    <input
                      type="date"
                      value={formData.date}
                      onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                      className="w-full p-3 border border-slate-200 rounded-xl text-sm outline-none focus:border-indigo-500"
                      required
                    />
                  </div>
                  <div>
                    <label className="text-xs font-bold text-slate-600 uppercase mb-2 block">Hora</label>
                    <input
                      type="time"
                      value={formData.time}
                      onChange={(e) => setFormData({ ...formData, time: e.target.value })}
                      className="w-full p-3 border border-slate-200 rounded-xl text-sm outline-none focus:border-indigo-500"
                    />
                  </div>
                </div>

                {/* Duración */}
                <div>
                  <label className="text-xs font-bold text-slate-600 uppercase mb-2 block">Duración (minutos)</label>
                  <div className="flex gap-2">
                    {[15, 30, 45, 60, 90, 120].map(mins => (
                      <button
                        key={mins}
                        type="button"
                        onClick={() => setFormData({ ...formData, duration: mins })}
                        className={`flex-1 py-2 rounded-lg text-sm font-bold transition-all ${
                          formData.duration === mins
                            ? 'bg-indigo-600 text-white'
                            : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                        }`}
                      >
                        {mins < 60 ? `${mins}m` : `${mins/60}h`}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Asunto */}
                <div>
                  <label className="text-xs font-bold text-slate-600 uppercase mb-2 block">Asunto</label>
                  <input
                    type="text"
                    placeholder="Ej: Presentación de presupuesto, Seguimiento..."
                    value={formData.subject}
                    onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                    className="w-full p-3 border border-slate-200 rounded-xl text-sm outline-none focus:border-indigo-500"
                    required
                  />
                </div>

                {/* Notas */}
                <div>
                  <label className="text-xs font-bold text-slate-600 uppercase mb-2 block">Notas</label>
                  <textarea
                    placeholder="Detalles de la actividad..."
                    value={formData.notes}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                    rows={3}
                    className="w-full p-3 border border-slate-200 rounded-xl text-sm outline-none focus:border-indigo-500 resize-none"
                  />
                </div>

                {/* Resultado */}
                <div>
                  <label className="text-xs font-bold text-slate-600 uppercase mb-2 block">Resultado / Seguimiento</label>
                  <input
                    type="text"
                    placeholder="Ej: Cliente interesado, Enviar presupuesto, Agendar visita..."
                    value={formData.outcome}
                    onChange={(e) => setFormData({ ...formData, outcome: e.target.value })}
                    className="w-full p-3 border border-slate-200 rounded-xl text-sm outline-none focus:border-indigo-500"
                  />
                </div>

                {/* Botones */}
                <div className="flex gap-3 pt-2">
                  <button
                    type="button"
                    onClick={resetForm}
                    className="flex-1 py-3 bg-slate-100 text-slate-700 rounded-xl font-bold hover:bg-slate-200 transition-all"
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    className="flex-1 py-3 bg-indigo-600 text-white rounded-xl font-bold hover:bg-indigo-700 transition-all"
                    data-testid="save-activity-btn"
                  >
                    {editingId ? 'Guardar Cambios' : 'Registrar Actividad'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Lista de actividades agrupadas por fecha */}
        {Object.keys(groupedActivities).length === 0 ? (
          <div className="text-center py-12">
            <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Calendar size={32} className="text-slate-400" />
            </div>
            <h3 className="text-lg font-bold text-slate-700 mb-2">Sin actividades</h3>
            <p className="text-slate-500 text-sm mb-4">
              {searchTerm || filterType !== 'all' || filterDate !== 'all' 
                ? 'No hay actividades que coincidan con los filtros'
                : 'Empieza registrando tu primera actividad'}
            </p>
            <button
              onClick={() => setShowForm(true)}
              className="px-6 py-3 bg-indigo-600 text-white rounded-xl font-bold hover:bg-indigo-700 transition-all"
            >
              <Plus size={18} className="inline mr-2" />
              Nueva Actividad
            </button>
          </div>
        ) : (
          <div className="space-y-6">
            {Object.entries(groupedActivities).map(([date, dateActivities]) => (
              <div key={date}>
                {/* Fecha como header */}
                <div className="flex items-center gap-3 mb-3">
                  <div className="flex items-center gap-2 bg-white px-4 py-2 rounded-full shadow-sm border border-slate-200">
                    <Calendar size={14} className="text-indigo-600" />
                    <span className="text-sm font-bold text-slate-700 capitalize">{formatDate(date)}</span>
                  </div>
                  <div className="flex-1 h-px bg-slate-200"></div>
                  <span className="text-xs font-bold text-slate-400">{dateActivities.length} actividades</span>
                </div>

                {/* Actividades del día */}
                <div className="space-y-2">
                  {dateActivities.map(activity => {
                    const typeConfig = ACTIVITY_TYPES[activity.activityType || activity.type] || ACTIVITY_TYPES.note;
                    const Icon = typeConfig.icon;
                    const isExpanded = expandedId === activity.id;

                    return (
                      <div
                        key={activity.id}
                        className={`bg-white rounded-xl border-2 ${typeConfig.borderColor} overflow-hidden shadow-sm transition-all`}
                      >
                        {/* Cabecera de la actividad - Clickable */}
                        <div 
                          className="p-3 md:p-4 cursor-pointer"
                          onClick={() => setExpandedId(isExpanded ? null : activity.id)}
                        >
                          <div className="flex items-start gap-3">
                            {/* Icono tipo */}
                            <div className={`p-2.5 rounded-xl ${typeConfig.bgColor} shrink-0`}>
                              <Icon size={20} className={typeConfig.textColor} />
                            </div>

                            {/* Info principal */}
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 flex-wrap">
                                <span className={`text-xs font-bold uppercase ${typeConfig.textColor} ${typeConfig.bgColor} px-2 py-0.5 rounded`}>
                                  {typeConfig.label}
                                </span>
                                <span className="text-xs text-slate-500 flex items-center gap-1">
                                  <Clock size={12} />
                                  {activity.time || activity.dueTime || '00:00'}
                                </span>
                                {activity.duration && (
                                  <span className="text-xs text-slate-400">
                                    ({activity.duration < 60 ? `${activity.duration}min` : `${activity.duration/60}h`})
                                  </span>
                                )}
                              </div>
                              
                              <h3 className="font-bold text-slate-900 mt-1 truncate">{activity.subject}</h3>
                              
                              {activity.contactName && (
                                <p className="text-sm text-slate-500 flex items-center gap-1 mt-0.5">
                                  <User size={12} />
                                  {activity.contactName}
                                </p>
                              )}
                            </div>

                            {/* Chevron */}
                            <div className="shrink-0">
                              {isExpanded ? <ChevronUp size={20} className="text-slate-400" /> : <ChevronDown size={20} className="text-slate-400" />}
                            </div>
                          </div>
                        </div>

                        {/* Contenido expandido */}
                        {isExpanded && (
                          <div className="px-3 md:px-4 pb-3 md:pb-4 border-t border-slate-100 pt-3 space-y-3">
                            {activity.notes && (
                              <div>
                                <p className="text-xs font-bold text-slate-500 uppercase mb-1">Notas</p>
                                <p className="text-sm text-slate-700 whitespace-pre-wrap">{activity.notes}</p>
                              </div>
                            )}
                            
                            {activity.outcome && (
                              <div>
                                <p className="text-xs font-bold text-slate-500 uppercase mb-1">Resultado / Seguimiento</p>
                                <p className="text-sm text-slate-700 bg-yellow-50 p-2 rounded-lg border border-yellow-200">{activity.outcome}</p>
                              </div>
                            )}

                            {/* Acciones */}
                            <div className="flex gap-2 pt-2">
                              <button
                                onClick={(e) => { e.stopPropagation(); handleEdit(activity); }}
                                className="flex items-center gap-1 px-3 py-1.5 bg-slate-100 text-slate-600 rounded-lg text-sm font-bold hover:bg-slate-200 transition-all"
                              >
                                <Edit2 size={14} />
                                Editar
                              </button>
                              <button
                                onClick={(e) => { e.stopPropagation(); handleDelete(activity.id); }}
                                className="flex items-center gap-1 px-3 py-1.5 bg-red-50 text-red-600 rounded-lg text-sm font-bold hover:bg-red-100 transition-all"
                              >
                                <Trash2 size={14} />
                                Eliminar
                              </button>
                            </div>

                            {/* Meta info */}
                            <div className="text-[10px] text-slate-400 pt-2 border-t border-slate-100">
                              Registrado por {activity.userName || 'Usuario'} 
                              {activity.createdAt && ` el ${new Date(activity.createdAt).toLocaleDateString('es-ES')}`}
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Botón flotante para móvil */}
      <button
        onClick={() => setShowForm(true)}
        className="md:hidden fixed bottom-6 right-6 w-14 h-14 bg-indigo-600 text-white rounded-full shadow-xl flex items-center justify-center hover:bg-indigo-700 transition-all z-40"
        data-testid="fab-new-activity"
      >
        <Plus size={24} />
      </button>
    </div>
  );
};

export default CRMActivities;
