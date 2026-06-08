import React, { useState, useEffect, useMemo, useRef } from 'react';
import { 
  Calendar, ChevronLeft, ChevronRight, Plus, X, Save, Loader2,
  Clock, MapPin, User, Target, Phone, Users as UsersIcon, Check,
  Trash2, Edit2, CalendarDays, LayoutGrid, List, CheckCircle2
} from 'lucide-react';
import { crmCalendarAPI, crmContactsAPI, crmOpportunitiesAPI, googleCalendarAPI } from '../services/api';
import GoogleCalendarConnect from './GoogleCalendarConnect';
import GoogleSyncModal from './GoogleSyncModal';
import { 
  format, startOfMonth, endOfMonth, startOfWeek, endOfWeek, 
  addDays, addMonths, subMonths, addWeeks, subWeeks,
  isSameMonth, isSameDay, isToday, parseISO,
  startOfDay, endOfDay, eachDayOfInterval, eachHourOfInterval,
  setHours, setMinutes
} from 'date-fns';
import { es } from 'date-fns/locale';

const EVENT_TYPES = {
  cita: { name: 'Cita/Visita', color: '#3b82f6', bgColor: 'bg-blue-100', textColor: 'text-blue-700' },
  seguimiento: { name: 'Seguimiento', color: '#f59e0b', bgColor: 'bg-amber-100', textColor: 'text-amber-700' },
  llamada: { name: 'Llamada', color: '#10b981', bgColor: 'bg-emerald-100', textColor: 'text-emerald-700' },
  reunion: { name: 'Reunión', color: '#8b5cf6', bgColor: 'bg-violet-100', textColor: 'text-violet-700' },
  otro: { name: 'Otro', color: '#6b7280', bgColor: 'bg-slate-100', textColor: 'text-slate-700' }
};

const VIEWS = {
  month: { name: 'Mes', icon: LayoutGrid },
  week: { name: 'Semana', icon: CalendarDays },
  day: { name: 'Día', icon: Clock },
  lista: { name: 'Lista', icon: List }
};

const CRMCalendar = ({ currentUser }) => {
  const [events, setEvents] = useState([]);
  const [contacts, setContacts] = useState([]);
  const [opportunities, setOpportunities] = useState([]);
  const [prescriptorNotes, setPrescriptorNotes] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [currentDate, setCurrentDate] = useState(new Date());
  const [view, setView] = useState('month');
  const [showModal, setShowModal] = useState(false);
  const [editingEvent, setEditingEvent] = useState(null);
  const [selectedDate, setSelectedDate] = useState(null);
  const [filterType, setFilterType] = useState('');
  const [viewAllEvents, setViewAllEvents] = useState(false);
  const [showPrescriptorNotes, setShowPrescriptorNotes] = useState(true);
  // Google Calendar (por usuario, aislado en el backend)
  const [googleConnected, setGoogleConnected] = useState(false);
  const [pendingGoogleEvent, setPendingGoogleEvent] = useState(null);
  // Vista de listado (por día/semana/mes). El aviso pop-up es global (App).
  const [listRange, setListRange] = useState('mes'); // 'dia' | 'semana' | 'mes'

  const [formData, setFormData] = useState({
    title: '',
    description: '',
    eventType: 'cita',
    startDate: '',
    startTime: '09:00',
    endDate: '',
    endTime: '10:00',
    allDay: false,
    contactId: '',
    contactName: '',
    opportunityId: '',
    opportunityTitle: '',
    location: '',
    notes: '',
    reminder: 30
  });

  useEffect(() => {
    loadData();
  }, [currentDate, view, viewAllEvents, filterType, googleConnected]);

  useEffect(() => {
    loadContactsAndOpportunities();
    if (currentUser?.isAdmin || currentUser?.isGerente || currentUser?.isDirectorComercial) {
      loadPrescriptorNotes();
    }
  }, [currentDate]);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const params = {
        userId: currentUser?.id
      };
      
      // Date range based on view
      if (view === 'month' || view === 'lista') {
        const start = startOfMonth(currentDate);
        const end = endOfMonth(currentDate);
        params.startDate = format(start, "yyyy-MM-dd'T'00:00:00");
        params.endDate = format(end, "yyyy-MM-dd'T'23:59:59");
      } else if (view === 'week') {
        const start = startOfWeek(currentDate, { weekStartsOn: 1 });
        const end = endOfWeek(currentDate, { weekStartsOn: 1 });
        params.startDate = format(start, "yyyy-MM-dd'T'00:00:00");
        params.endDate = format(end, "yyyy-MM-dd'T'23:59:59");
      } else {
        params.startDate = format(currentDate, "yyyy-MM-dd'T'00:00:00");
        params.endDate = format(currentDate, "yyyy-MM-dd'T'23:59:59");
      }
      
      if (filterType) params.eventType = filterType;
      if (viewAllEvents && currentUser?.isAdmin || currentUser?.isGerente || currentUser?.isDirectorComercial) params.viewAll = true;
      if (currentUser?.isRepresentative && !currentUser?.isAdmin || currentUser?.isGerente || currentUser?.isDirectorComercial) {
        params.commercialId = currentUser.id;
      }
      
      const data = await crmCalendarAPI.getEvents(params);

      // Traer también los eventos de Google del propio usuario (solo lectura)
      // y fusionarlos. El backend garantiza que cada usuario ve solo los suyos.
      let merged = Array.isArray(data) ? data : [];
      if (googleConnected) {
        try {
          const gres = await googleCalendarAPI.getEvents(params.startDate, params.endDate);
          const gEvents = (gres?.events || []).map(g => ({
            id: g.id,
            title: g.title,
            description: g.description,
            location: g.location,
            startDate: g.startDate,
            endDate: g.endDate,
            allDay: g.allDay,
            eventType: 'otro',
            color: g.color || '#16a34a',
            completed: false,
            source: 'google',
            readOnlyFromGoogle: true,
            htmlLink: g.htmlLink,
          }));
          merged = merged.concat(gEvents);
        } catch (gerr) {
          console.warn('No se pudieron cargar eventos de Google:', gerr);
        }
      }
      setEvents(merged);
    } catch (err) {
      console.error('Error loading calendar events:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const loadContactsAndOpportunities = async () => {
    try {
      const [contactsData, oppsData] = await Promise.all([
        crmContactsAPI.getAll(),
        crmOpportunitiesAPI.getAll()
      ]);
      setContacts(contactsData);
      setOpportunities(oppsData);
    } catch (err) {
      console.error('Error loading contacts/opportunities:', err);
    }
  };

  const loadPrescriptorNotes = async () => {
    if (!currentUser?.isAdmin || currentUser?.isGerente || currentUser?.isDirectorComercial) return;
    try {
      const start = startOfMonth(currentDate);
      const end = endOfMonth(currentDate);
      const API_URL = process.env.REACT_APP_BACKEND_URL;
      const response = await fetch(
        `${API_URL}/api/prescriptor/notes/all?start=${format(start, 'yyyy-MM-dd')}&end=${format(end, 'yyyy-MM-dd')}`
      );
      if (response.ok) {
        const data = await response.json();
        setPrescriptorNotes(data);
      }
    } catch (err) {
      console.error('Error loading prescriptor notes:', err);
    }
  };

  const openCreateModal = (date = null) => {
    const targetDate = date || new Date();
    setEditingEvent(null);
    setFormData({
      title: '',
      description: '',
      eventType: 'cita',
      startDate: format(targetDate, 'yyyy-MM-dd'),
      startTime: '09:00',
      endDate: format(targetDate, 'yyyy-MM-dd'),
      endTime: '10:00',
      allDay: false,
      contactId: '',
      contactName: '',
      opportunityId: '',
      opportunityTitle: '',
      location: '',
      notes: '',
      reminder: 30
    });
    setShowModal(true);
  };

  const openEditModal = (event) => {
    const startParsed = parseISO(event.startDate);
    const endParsed = parseISO(event.endDate);
    setEditingEvent(event);
    setFormData({
      title: event.title || '',
      description: event.description || '',
      eventType: event.eventType || 'cita',
      startDate: format(startParsed, 'yyyy-MM-dd'),
      startTime: format(startParsed, 'HH:mm'),
      endDate: format(endParsed, 'yyyy-MM-dd'),
      endTime: format(endParsed, 'HH:mm'),
      allDay: event.allDay || false,
      contactId: event.contactId || '',
      contactName: event.contactName || '',
      opportunityId: event.opportunityId || '',
      opportunityTitle: event.opportunityTitle || '',
      location: event.location || '',
      notes: event.notes || '',
      reminder: event.reminder || 30
    });
    setShowModal(true);
  };

  const handleSave = async () => {
    if (!formData.title.trim()) {
      alert('El título es obligatorio');
      return;
    }

    try {
      const eventData = {
        title: formData.title,
        description: formData.description,
        eventType: formData.eventType,
        startDate: `${formData.startDate}T${formData.startTime}:00`,
        endDate: `${formData.endDate}T${formData.endTime}:00`,
        allDay: formData.allDay,
        contactId: formData.contactId || null,
        contactName: formData.contactName || null,
        opportunityId: formData.opportunityId || null,
        opportunityTitle: formData.opportunityTitle || null,
        location: formData.location,
        notes: formData.notes,
        reminder: formData.reminder,
        assignedTo: currentUser?.id,
        assignedToName: currentUser?.clientName || currentUser?.username
      };

      let erpId = editingEvent?.id;
      if (editingEvent) {
        await crmCalendarAPI.update(editingEvent.id, eventData);
      } else {
        const created = await crmCalendarAPI.create(eventData, currentUser?.id, currentUser?.clientName || currentUser?.username);
        erpId = created?.id || erpId;
      }

      setShowModal(false);
      loadData();

      // Si el usuario tiene Google Calendar conectado, preguntar si quiere
      // guardar también allí (solo para eventos nuevos del ERP, no los de Google).
      if (googleConnected && !editingEvent?.source) {
        setPendingGoogleEvent({
          title: eventData.title,
          startDate: eventData.startDate,
          endDate: eventData.endDate,
          description: eventData.description || '',
          location: eventData.location || '',
          allDay: !!eventData.allDay,
          erpId,
        });
      }
    } catch (err) {
      alert('Error al guardar evento: ' + err.message);
    }
  };

  const handleDelete = async () => {
    if (!editingEvent) return;
    if (!window.confirm('¿Eliminar este evento?')) return;
    
    try {
      await crmCalendarAPI.delete(editingEvent.id);
      setShowModal(false);
      loadData();
    } catch (err) {
      alert('Error al eliminar evento: ' + err.message);
    }
  };

  const handleComplete = async (event) => {
    try {
      await crmCalendarAPI.complete(event.id);
      loadData();
    } catch (err) {
      alert('Error al completar evento: ' + err.message);
    }
  };

  const navigate = (direction) => {
    if (view === 'month' || view === 'lista') {
      setCurrentDate(direction === 'next' ? addMonths(currentDate, 1) : subMonths(currentDate, 1));
    } else if (view === 'week') {
      setCurrentDate(direction === 'next' ? addWeeks(currentDate, 1) : subWeeks(currentDate, 1));
    } else {
      setCurrentDate(direction === 'next' ? addDays(currentDate, 1) : addDays(currentDate, -1));
    }
  };

  const goToToday = () => setCurrentDate(new Date());

  const getEventsForDate = (date) => {
    return events.filter(evt => {
      const evtDate = parseISO(evt.startDate);
      return isSameDay(evtDate, date);
    });
  };

  // Month View Calendar Grid
  const monthDays = useMemo(() => {
    const start = startOfWeek(startOfMonth(currentDate), { weekStartsOn: 1 });
    const end = endOfWeek(endOfMonth(currentDate), { weekStartsOn: 1 });
    return eachDayOfInterval({ start, end });
  }, [currentDate]);

  // Week View Days
  const weekDays = useMemo(() => {
    const start = startOfWeek(currentDate, { weekStartsOn: 1 });
    return eachDayOfInterval({ start, end: addDays(start, 6) });
  }, [currentDate]);

  // Day View Hours
  const dayHours = useMemo(() => {
    return Array.from({ length: 14 }, (_, i) => i + 7); // 7:00 to 20:00
  }, []);

  const getTitle = () => {
    if (view === 'month' || view === 'lista') return format(currentDate, 'MMMM yyyy', { locale: es });
    if (view === 'week') {
      const start = startOfWeek(currentDate, { weekStartsOn: 1 });
      const end = endOfWeek(currentDate, { weekStartsOn: 1 });
      return `${format(start, 'd', { locale: es })} - ${format(end, 'd MMM yyyy', { locale: es })}`;
    }
    return format(currentDate, "EEEE, d 'de' MMMM yyyy", { locale: es });
  };

  return (
    <div className="h-full flex flex-col bg-slate-50">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 px-3 md:px-6 py-3 md:py-4 flex flex-col md:flex-row md:items-center justify-between shrink-0 gap-3">
        <div className="flex items-center gap-2 md:gap-4  flex-wrap">
          <div className="flex items-center gap-1 md:gap-2">
            <button 
              onClick={() => navigate('prev')}
              className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
            >
              <ChevronLeft size={20} />
            </button>
            <button 
              onClick={() => navigate('next')}
              className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
            >
              <ChevronRight size={20} />
            </button>
          </div>
          <h2 className="text-base md:text-xl font-black text-slate-900 capitalize">{getTitle()}</h2>
          <button 
            onClick={goToToday}
            className="px-2 md:px-3 py-1 text-xs md:text-sm font-bold text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
          >
            Hoy
          </button>
        </div>

        <div className="flex items-center gap-2 md:gap-3 flex-wrap">
          {/* Google Calendar (conectar / estado por usuario) */}
          <GoogleCalendarConnect compact onStatusChange={(s) => setGoogleConnected(!!s.connected)} />

          {/* View Selector */}
          <div className="flex bg-slate-100 rounded-lg p-1">
            {Object.entries(VIEWS).map(([key, v]) => {
              const Icon = v.icon;
              return (
                <button
                  key={key}
                  onClick={() => setView(key)}
                  className={`flex items-center gap-1 px-3 py-1.5 rounded-md text-xs font-bold transition-all ${
                    view === key ? 'bg-white text-indigo-600 shadow-sm' : 'text-slate-500 hover:text-slate-700'
                  }`}
                >
                  <Icon size={14} />
                  {v.name}
                </button>
              );
            })}
          </div>

          {/* Filter by Type */}
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="px-3 py-2 bg-white border border-slate-200 rounded-lg text-sm font-bold outline-none focus:border-indigo-500"
          >
            <option value="">Todos los tipos</option>
            {Object.entries(EVENT_TYPES).map(([key, type]) => (
              <option key={key} value={key}>{type.name}</option>
            ))}
          </select>

          {/* Admin: View All Toggle */}
          {currentUser?.isAdmin || currentUser?.isGerente || currentUser?.isDirectorComercial && (
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={viewAllEvents}
                onChange={(e) => setViewAllEvents(e.target.checked)}
                className="w-4 h-4 rounded"
              />
              <span className="text-xs font-bold text-slate-600">Ver todos</span>
            </label>
          )}

          {/* Admin: Show Prescriptor Notes Toggle */}
          {currentUser?.isAdmin || currentUser?.isGerente || currentUser?.isDirectorComercial && (
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={showPrescriptorNotes}
                onChange={(e) => setShowPrescriptorNotes(e.target.checked)}
                className="w-4 h-4 rounded accent-amber-500"
              />
              <span className="text-xs font-bold text-amber-600">Notas Colaboradores</span>
            </label>
          )}

          {/* Add Event Button */}
          <button
            onClick={() => openCreateModal()}
            className="flex items-center gap-2 px-3 md:px-4 py-2 bg-indigo-600 text-white rounded-lg font-bold text-xs md:text-sm hover:bg-indigo-700 transition-colors shadow-sm whitespace-nowrap"
          >
            <Plus size={16} />
            <span className="hidden sm:inline">Nuevo Evento</span>
            <span className="sm:hidden">Nuevo</span>
          </button>
        </div>
      </div>

      {/* Calendar Content */}
      <div className="flex-1 overflow-auto p-4">
        {isLoading ? (
          <div className="h-full flex items-center justify-center">
            <Loader2 className="w-8 h-8 text-indigo-600 animate-spin" />
          </div>
        ) : (
          <>
            {/* Month View */}
            {view === 'month' && (
              <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-x-auto">
                <div className="min-w-[640px]">
                {/* Weekday Headers */}
                <div className="grid grid-cols-7 border-b border-slate-200">
                  {['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'].map(day => (
                    <div key={day} className="p-2 text-center text-xs font-black text-slate-500 uppercase bg-slate-50">
                      {day}
                    </div>
                  ))}
                </div>
                {/* Days Grid */}
                <div className="grid grid-cols-7">
                  {monthDays.map((day, idx) => {
                    const dayEvents = getEventsForDate(day);
                    const isCurrentMonth = isSameMonth(day, currentDate);
                    // Get prescriptor notes for this day (admin only)
                    const dayPrescriptorNotes = showPrescriptorNotes ? prescriptorNotes.filter(
                      n => n.date === format(day, 'yyyy-MM-dd')
                    ) : [];
                    return (
                      <div
                        key={idx}
                        onClick={() => openCreateModal(day)}
                        className={`min-h-[52px] sm:min-h-[80px] md:min-h-[100px] border-b border-r border-slate-100 p-0.5 sm:p-1 cursor-pointer transition-colors hover:bg-slate-50 ${
                          !isCurrentMonth ? 'bg-slate-50' : ''
                        } ${isToday(day) ? 'bg-indigo-50' : ''}`}
                      >
                        <div className="flex items-center justify-between mb-0.5 sm:mb-1">
                          <span className={`text-xs sm:text-sm font-bold ${
                            isToday(day) ? 'text-indigo-600' : isCurrentMonth ? 'text-slate-900' : 'text-slate-300'
                          }`}>
                            {format(day, 'd')}
                          </span>
                          {(dayEvents.length + dayPrescriptorNotes.length) > 1 && (
                            <span
                              className="text-[9px] font-black text-white bg-indigo-500 rounded-full px-1.5 min-w-[16px] text-center leading-4"
                              title={`${dayEvents.length + dayPrescriptorNotes.length} gestiones este día`}
                            >
                              {dayEvents.length + dayPrescriptorNotes.length}
                            </span>
                          )}
                        </div>
                        <div className="space-y-0.5">
                          {dayEvents.slice(0, 3).map(evt => (
                            <div key={evt.id} onClick={(e) => { e.stopPropagation(); openEditModal(evt); }} className="cursor-pointer">
                              {/* Móvil: solo punto */}
                              <div className={`sm:hidden w-1.5 h-1.5 rounded-full mb-0.5 ${EVENT_TYPES[evt.eventType]?.bgColor?.replace('bg-', 'bg-') || 'bg-slate-400'}`} />
                              {/* Desktop: texto completo */}
                              <div className={`hidden sm:block text-[10px] px-1.5 py-0.5 rounded truncate ${EVENT_TYPES[evt.eventType]?.bgColor || 'bg-slate-100'} ${EVENT_TYPES[evt.eventType]?.textColor || 'text-slate-700'} ${evt.completed ? 'opacity-50 line-through' : ''}`}>
                                {evt.title}
                              </div>
                            </div>
                          ))}
                          {/* Prescriptor Notes (amber/orange) */}
                          {dayPrescriptorNotes.slice(0, 2).map(note => (
                            <div
                              key={note.id}
                              className="text-[10px] px-1.5 py-0.5 rounded truncate bg-amber-100 text-amber-800 border border-amber-200"
                              title={`${note.prescriptorName}: ${note.title || note.content}`}
                            >
                              📋 {note.title || note.content?.substring(0, 15)}
                            </div>
                          ))}
                          {(dayEvents.length + dayPrescriptorNotes.length) > 4 && (
                            <div className="text-[10px] text-slate-400 font-bold pl-1">
                              +{(dayEvents.length + dayPrescriptorNotes.length) - 4} más
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
                </div>
              </div>
            )}

            {/* Week View */}
            {view === 'week' && (
              <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-x-auto">
                <div className="min-w-[720px]">
                {/* Day Headers */}
                <div className="grid grid-cols-8 border-b border-slate-200">
                  <div className="p-2 bg-slate-50 border-r border-slate-200"></div>
                  {weekDays.map(day => (
                    <div 
                      key={day.toString()} 
                      className={`p-2 text-center border-r border-slate-200 ${isToday(day) ? 'bg-indigo-50' : 'bg-slate-50'}`}
                    >
                      <div className="text-xs font-bold text-slate-500 uppercase">
                        {format(day, 'EEE', { locale: es })}
                      </div>
                      <div className={`text-lg font-black ${isToday(day) ? 'text-indigo-600' : 'text-slate-900'}`}>
                        {format(day, 'd')}
                      </div>
                    </div>
                  ))}
                </div>
                {/* Hours Grid */}
                <div className="max-h-[500px] overflow-y-auto">
                  {dayHours.map(hour => (
                    <div key={hour} className="grid grid-cols-8 border-b border-slate-100">
                      <div className="p-2 text-xs font-bold text-slate-400 text-right border-r border-slate-200 bg-slate-50">
                        {hour}:00
                      </div>
                      {weekDays.map(day => {
                        const dayEvents = events.filter(evt => {
                          const evtDate = parseISO(evt.startDate);
                          return isSameDay(evtDate, day) && evtDate.getHours() === hour;
                        });
                        return (
                          <div 
                            key={day.toString()}
                            onClick={() => openCreateModal(setHours(day, hour))}
                            className="min-h-[50px] border-r border-slate-100 p-1 hover:bg-slate-50 cursor-pointer"
                          >
                            {dayEvents.map(evt => (
                              <div
                                key={evt.id}
                                onClick={(e) => { e.stopPropagation(); openEditModal(evt); }}
                                className={`text-[10px] px-1 py-0.5 rounded truncate cursor-pointer mb-0.5 ${EVENT_TYPES[evt.eventType]?.bgColor || 'bg-slate-100'} ${EVENT_TYPES[evt.eventType]?.textColor || 'text-slate-700'} ${evt.completed ? 'opacity-50 line-through' : ''}`}
                              >
                                {evt.title}
                              </div>
                            ))}
                          </div>
                        );
                      })}
                    </div>
                  ))}
                </div>
                </div>
              </div>
            )}

            {/* Day View */}
            {view === 'day' && (
              <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                {/* Resumen: TODOS los eventos del día (incluye los de fuera de 7-20h y todo el día) */}
                {(() => {
                  const dayAll = getEventsForDate(currentDate)
                    .slice()
                    .sort((a, b) => (a.startDate || '').localeCompare(b.startDate || ''));
                  if (dayAll.length === 0) return null;
                  return (
                    <div className="p-3 border-b border-slate-100 bg-slate-50">
                      <p className="text-xs font-black text-slate-500 uppercase mb-2">{dayAll.length} evento(s) este día</p>
                      <div className="flex flex-wrap gap-1.5">
                        {dayAll.map(evt => (
                          <button key={evt.id} onClick={() => openEditModal(evt)}
                            className={`text-xs px-2.5 py-1 rounded-lg font-bold ${EVENT_TYPES[evt.eventType]?.bgColor || 'bg-slate-100'} ${EVENT_TYPES[evt.eventType]?.textColor || 'text-slate-700'} ${evt.completed ? 'opacity-50 line-through' : ''}`}>
                            {evt.allDay ? 'Todo el día' : (() => { try { return format(parseISO(evt.startDate), 'HH:mm'); } catch { return ''; } })()} · {evt.title}
                          </button>
                        ))}
                      </div>
                    </div>
                  );
                })()}
                <div className="max-h-[600px] overflow-y-auto">
                  {dayHours.map(hour => {
                    const hourEvents = events.filter(evt => {
                      const evtDate = parseISO(evt.startDate);
                      return isSameDay(evtDate, currentDate) && evtDate.getHours() === hour;
                    });
                    return (
                      <div key={hour} className="flex border-b border-slate-100">
                        <div className="w-20 p-3 text-sm font-bold text-slate-400 text-right border-r border-slate-200 bg-slate-50 shrink-0">
                          {hour}:00
                        </div>
                        <div 
                          onClick={() => openCreateModal(setHours(currentDate, hour))}
                          className="flex-1 min-h-[60px] p-2 hover:bg-slate-50 cursor-pointer"
                        >
                          {hourEvents.map(evt => (
                            <div
                              key={evt.id}
                              onClick={(e) => { e.stopPropagation(); openEditModal(evt); }}
                              className={`p-2 rounded-lg mb-1 cursor-pointer ${EVENT_TYPES[evt.eventType]?.bgColor || 'bg-slate-100'} ${evt.completed ? 'opacity-50' : ''}`}
                            >
                              <div className="flex items-center justify-between">
                                <span className={`font-bold text-sm ${EVENT_TYPES[evt.eventType]?.textColor || 'text-slate-700'} ${evt.completed ? 'line-through' : ''}`}>
                                  {evt.title}
                                </span>
                                {!evt.completed && evt.source !== 'google' && (
                                  <button
                                    onClick={(e) => { e.stopPropagation(); handleComplete(evt); }}
                                    className="p-1 hover:bg-white/50 rounded"
                                    title="Marcar completado"
                                  >
                                    <Check size={14} />
                                  </button>
                                )}
                                {evt.completed && <CheckCircle2 size={14} className="text-green-600" />}
                              </div>
                              {evt.contactName && (
                                <p className="text-xs text-slate-500 flex items-center gap-1 mt-1">
                                  <User size={10} /> {evt.contactName}
                                </p>
                              )}
                              {evt.location && (
                                <p className="text-xs text-slate-500 flex items-center gap-1">
                                  <MapPin size={10} /> {evt.location}
                                </p>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Vista Lista (listado por día / semana / mes) */}
            {view === 'lista' && (() => {
              const inRange = (d) => {
                if (listRange === 'dia') return isSameDay(d, currentDate);
                if (listRange === 'semana') {
                  const ws = startOfWeek(currentDate, { weekStartsOn: 1 });
                  const we = endOfWeek(currentDate, { weekStartsOn: 1 });
                  return d >= ws && d <= we;
                }
                return isSameMonth(d, currentDate);
              };
              const listed = [...events]
                .filter(e => { try { return inRange(parseISO(e.startDate)); } catch { return false; } })
                .sort((a, b) => (a.startDate || '').localeCompare(b.startDate || ''));
              const groups = {};
              listed.forEach(e => {
                const k = format(parseISO(e.startDate), 'yyyy-MM-dd');
                (groups[k] = groups[k] || []).push(e);
              });
              const keys = Object.keys(groups).sort();
              return (
                <div className="bg-white rounded-xl border border-slate-200 shadow-sm">
                  <div className="flex items-center gap-2 p-3 border-b border-slate-100">
                    {[['dia', 'Día'], ['semana', 'Semana'], ['mes', 'Mes']].map(([k, label]) => (
                      <button key={k} onClick={() => setListRange(k)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-bold ${listRange === k ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}>
                        {label}
                      </button>
                    ))}
                    <span className="ml-auto text-xs text-slate-400">{listed.length} eventos</span>
                  </div>
                  <div className="max-h-[600px] overflow-y-auto divide-y divide-slate-100">
                    {keys.length === 0 && <div className="p-8 text-center text-slate-400">No hay eventos en este rango</div>}
                    {keys.map(k => (
                      <div key={k} className="p-3">
                        <p className="text-xs font-black text-slate-500 uppercase mb-2 capitalize">
                          {format(parseISO(k + 'T00:00:00'), "EEEE d 'de' MMMM", { locale: es })}
                        </p>
                        <div className="space-y-1.5">
                          {groups[k].map(evt => (
                            <div key={evt.id} onClick={() => openEditModal(evt)}
                              className={`flex items-center gap-3 p-2.5 rounded-xl cursor-pointer hover:shadow-sm ${EVENT_TYPES[evt.eventType]?.bgColor || 'bg-slate-100'} ${evt.completed ? 'opacity-50' : ''}`}>
                              <span className="text-xs font-mono font-bold text-slate-600 w-12 shrink-0">
                                {evt.allDay ? 'Todo' : format(parseISO(evt.startDate), 'HH:mm')}
                              </span>
                              <span className={`flex-1 font-bold text-sm truncate ${EVENT_TYPES[evt.eventType]?.textColor || 'text-slate-700'} ${evt.completed ? 'line-through' : ''}`}>
                                {evt.title}
                              </span>
                              {evt.contactName && <span className="text-xs text-slate-500 hidden sm:flex items-center gap-1"><User size={11} />{evt.contactName}</span>}
                              {evt.source === 'google' && <span className="text-[9px] font-black text-green-700 bg-green-100 px-1.5 py-0.5 rounded">G</span>}
                              {!evt.completed && !evt.source && (
                                <button onClick={(e) => { e.stopPropagation(); handleComplete(evt); }} className="p-1 hover:bg-white/50 rounded shrink-0" title="Completar"><Check size={14} /></button>
                              )}
                              {evt.completed && <CheckCircle2 size={14} className="text-green-600 shrink-0" />}
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })()}
          </>
        )}
      </div>

      {/* Event Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-t-3xl sm:rounded-2xl shadow-2xl w-full sm:max-w-lg max-h-[92vh] overflow-hidden">
            <div className="bg-indigo-600 text-white px-6 py-4 flex justify-between items-center">
              <h2 className="font-black text-lg uppercase">
                {editingEvent ? 'Editar Evento' : 'Nuevo Evento'}
              </h2>
              <button onClick={() => setShowModal(false)} className="p-1 hover:bg-white/10 rounded">
                <X size={20} />
              </button>
            </div>
            
            <div className="p-6 space-y-4 max-h-[60vh] overflow-y-auto">
              {/* Title */}
              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Título *</label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({...formData, title: e.target.value})}
                  className="w-full px-4 py-2.5 border-2 border-slate-200 rounded-xl text-sm font-bold outline-none focus:border-indigo-500"
                  placeholder="Ej: Visita cliente García"
                />
              </div>

              {/* Type */}
              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Tipo de Evento</label>
                <div className="grid grid-cols-3 sm:grid-cols-5 gap-2">
                  {Object.entries(EVENT_TYPES).map(([key, type]) => (
                    <button
                      key={key}
                      onClick={() => setFormData({...formData, eventType: key})}
                      className={`p-2 rounded-lg text-xs font-bold transition-all ${
                        formData.eventType === key 
                          ? `${type.bgColor} ${type.textColor} ring-2 ring-offset-1`
                          : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                      }`}
                      style={{ '--tw-ring-color': type.color }}
                    >
                      {type.name.split('/')[0]}
                    </button>
                  ))}
                </div>
              </div>

              {/* Date & Time */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Fecha Inicio</label>
                  <input
                    type="date"
                    value={formData.startDate}
                    onChange={(e) => setFormData({...formData, startDate: e.target.value, endDate: e.target.value})}
                    className="w-full px-4 py-2.5 border-2 border-slate-200 rounded-xl text-sm font-bold outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Hora Inicio</label>
                  <input
                    type="time"
                    value={formData.startTime}
                    onChange={(e) => setFormData({...formData, startTime: e.target.value})}
                    className="w-full px-4 py-2.5 border-2 border-slate-200 rounded-xl text-sm font-bold outline-none focus:border-indigo-500"
                    disabled={formData.allDay}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Fecha Fin</label>
                  <input
                    type="date"
                    value={formData.endDate}
                    onChange={(e) => setFormData({...formData, endDate: e.target.value})}
                    className="w-full px-4 py-2.5 border-2 border-slate-200 rounded-xl text-sm font-bold outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Hora Fin</label>
                  <input
                    type="time"
                    value={formData.endTime}
                    onChange={(e) => setFormData({...formData, endTime: e.target.value})}
                    className="w-full px-4 py-2.5 border-2 border-slate-200 rounded-xl text-sm font-bold outline-none focus:border-indigo-500"
                    disabled={formData.allDay}
                  />
                </div>
              </div>

              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.allDay}
                  onChange={(e) => setFormData({...formData, allDay: e.target.checked})}
                  className="w-4 h-4 rounded"
                />
                <span className="text-sm font-bold text-slate-600">Todo el día</span>
              </label>

              {/* Contact Link */}
              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Vincular Contacto</label>
                <select
                  value={formData.contactId}
                  onChange={(e) => {
                    const contact = contacts.find(c => c.id === e.target.value);
                    setFormData({...formData, contactId: e.target.value, contactName: contact?.name || ''});
                  }}
                  className="w-full px-4 py-2.5 border-2 border-slate-200 rounded-xl text-sm font-bold outline-none focus:border-indigo-500"
                >
                  <option value="">Sin contacto</option>
                  {contacts.map(c => (
                    <option key={c.id} value={c.id}>{c.name} {c.company ? `(${c.company})` : ''}</option>
                  ))}
                </select>
              </div>

              {/* Opportunity Link */}
              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Vincular Oportunidad</label>
                <select
                  value={formData.opportunityId}
                  onChange={(e) => {
                    const opp = opportunities.find(o => o.id === e.target.value);
                    setFormData({...formData, opportunityId: e.target.value, opportunityTitle: opp?.title || ''});
                  }}
                  className="w-full px-4 py-2.5 border-2 border-slate-200 rounded-xl text-sm font-bold outline-none focus:border-indigo-500"
                >
                  <option value="">Sin oportunidad</option>
                  {opportunities.map(o => (
                    <option key={o.id} value={o.id}>{o.title} ({o.contactName})</option>
                  ))}
                </select>
              </div>

              {/* Location */}
              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Ubicación</label>
                <input
                  type="text"
                  value={formData.location}
                  onChange={(e) => setFormData({...formData, location: e.target.value})}
                  className="w-full px-4 py-2.5 border-2 border-slate-200 rounded-xl text-sm font-bold outline-none focus:border-indigo-500"
                  placeholder="Ej: Oficina central, Domicilio cliente..."
                />
              </div>

              {/* Notes */}
              <div>
                <label className="block text-xs font-bold text-slate-500 uppercase mb-1">Notas</label>
                <textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({...formData, notes: e.target.value})}
                  className="w-full px-4 py-2.5 border-2 border-slate-200 rounded-xl text-sm font-bold outline-none focus:border-indigo-500 resize-none"
                  rows={2}
                  placeholder="Notas adicionales..."
                />
              </div>
            </div>

            {/* Actions */}
            <div className="px-6 py-4 bg-slate-50 border-t border-slate-200 flex justify-between">
              {editingEvent && (
                <button
                  onClick={handleDelete}
                  className="flex items-center gap-2 px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg font-bold text-sm"
                >
                  <Trash2 size={16} />
                  Eliminar
                </button>
              )}
              <div className={`flex gap-2 ${!editingEvent ? 'ml-auto' : ''}`}>
                <button
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 text-slate-600 hover:bg-slate-200 rounded-lg font-bold text-sm"
                >
                  Cancelar
                </button>
                <button
                  onClick={handleSave}
                  className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg font-bold text-sm hover:bg-indigo-700"
                >
                  <Save size={16} />
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
        defaultContext="crm"
        currentUser={currentUser}
        onClose={() => { setPendingGoogleEvent(null); loadData(); }}
      />
    </div>
  );
};

export default CRMCalendar;
