/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * AgendaMontajes.jsx
 * Agenda de Montadores e Instaladores
 * Similar a la agenda de prescriptores comerciales
 */
import React, { useState, useEffect } from 'react';
import { 
  Users, Search, Plus, Phone, Mail, MapPin, Star, 
  Edit2, Trash2, X, Save, Loader2, Wrench, Calendar,
  Building2, Tag, CheckCircle, Clock, AlertCircle, Pause,
  ChevronLeft, ChevronRight
} from 'lucide-react';
import { montadoresAPI, montajesAPI, googleCalendarAPI } from '../services/api';
import GoogleCalendarConnect from './GoogleCalendarConnect';
import GoogleSyncModal from './GoogleSyncModal';

// Especialidades de montadores
const SPECIALTIES = [
  "Cocinas Montadas",
  "Cocinas Despiece",
  "Armarios",
  "Baños",
  "Todo tipo"
];

// Estados de montador
const MONTADOR_STATUS = [
  { value: 'active', label: 'Activo', color: 'bg-green-100 text-green-700', icon: CheckCircle },
  { value: 'inactive', label: 'Inactivo', color: 'bg-slate-100 text-slate-700', icon: Pause },
  { value: 'vacation', label: 'Vacaciones', color: 'bg-amber-100 text-amber-700', icon: Calendar }
];

// Estados de montaje
const MONTAJE_STATUS = [
  { value: 'pendiente', label: 'Pendiente', color: 'bg-amber-100 text-amber-700', icon: Clock },
  { value: 'en_curso', label: 'En Curso', color: 'bg-blue-100 text-blue-700', icon: Wrench },
  { value: 'completado', label: 'Completado', color: 'bg-green-100 text-green-700', icon: CheckCircle },
  { value: 'cancelado', label: 'Cancelado', color: 'bg-red-100 text-red-700', icon: AlertCircle }
];

const AgendaMontajes = ({ currentUser }) => {
  // State
  const [montadores, setMontadores] = useState([]);
  const [montajes, setMontajes] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [activeTab, setActiveTab] = useState(null); // Se establecerá en useEffect según el rol
  const [currentMonth, setCurrentMonth] = useState(new Date());
  
  // Modal states
  const [showMontadorModal, setShowMontadorModal] = useState(false);
  const [showMontajeModal, setShowMontajeModal] = useState(false);
  const [editingMontador, setEditingMontador] = useState(null);
  const [editingMontaje, setEditingMontaje] = useState(null);
  const [isSaving, setIsSaving] = useState(false);
  // Google Calendar (por usuario, aislado en el backend)
  const [googleConnected, setGoogleConnected] = useState(false);
  const [pendingGoogleEvent, setPendingGoogleEvent] = useState(null);
  
  // Form states
  const [montadorForm, setMontadorForm] = useState({
    name: '',
    phone: '',
    email: '',
    company: '',
    specialty: '',
    zone: '',
    address: '',
    notes: '',
    status: 'active',
    rating: 0,
    tags: []
  });
  
  const [montajeForm, setMontajeForm] = useState({
    montadorId: '',
    clientName: '',
    clientPhone: '',
    clientAddress: '',
    projectDescription: '',
    expectedDeliveryDate: '',  // Fecha recepción cocina
    scheduledDate: '',         // Fecha montaje comprometida
    scheduledTime: '',
    estimatedDuration: '',
    status: 'pendiente',
    budgetRef: '',
    notes: ''
  });

  // Load data
  useEffect(() => {
    loadMontadores();
    loadMontajes();
    
    // Establecer pestaña por defecto según el rol
    if (activeTab === null) {
      if (currentUser?.isMontador && !currentUser?.isAdmin) {
        setActiveTab('montajes'); // Montadores ven sus montajes
      } else {
        setActiveTab('montadores'); // Admins ven gestión de montadores
      }
    }
  }, [statusFilter, currentUser]);

  const loadMontadores = async () => {
    setIsLoading(true);
    try {
      const data = await montadoresAPI.getAll(statusFilter || null);
      setMontadores(data);
    } catch (err) {
      console.error('Error loading montadores:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const loadMontajes = async () => {
    try {
      const data = await montajesAPI.getAll({ status: statusFilter || null });
      setMontajes(data);
    } catch (err) {
      console.error('Error loading montajes:', err);
    }
  };

  // Filter montadores
  const filteredMontadores = montadores.filter(m => {
    const query = searchQuery.toLowerCase();
    return m.name?.toLowerCase().includes(query) ||
           m.company?.toLowerCase().includes(query) ||
           m.zone?.toLowerCase().includes(query) ||
           m.phone?.includes(query) ||
           m.createdByName?.toLowerCase().includes(query);
  });

  // Filter montajes - Si es montador, solo ve los suyos
  const filteredMontajes = montajes.filter(m => {
    // Si el usuario es montador, solo mostrar sus montajes
    if (currentUser?.isMontador && !currentUser?.isAdmin) {
      // Filtrar por el ID del usuario o por su nombre
      const isMyMontaje = m.montadorId === currentUser?.id || 
                          m.montadorId === currentUser?.montadorId ||
                          m.montadorName?.toLowerCase() === currentUser?.clientName?.toLowerCase() ||
                          m.montadorName?.toLowerCase() === currentUser?.name?.toLowerCase();
      if (!isMyMontaje) return false;
    }
    
    const query = searchQuery.toLowerCase();
    return m.clientName?.toLowerCase().includes(query) ||
           m.montadorName?.toLowerCase().includes(query) ||
           m.clientAddress?.toLowerCase().includes(query) ||
           m.budgetRef?.toLowerCase().includes(query) ||
           m.createdByName?.toLowerCase().includes(query);
  });

  // Montador handlers
  const handleSaveMontador = async () => {
    if (!montadorForm.name) {
      alert('El nombre es obligatorio');
      return;
    }
    
    setIsSaving(true);
    try {
      if (editingMontador) {
        await montadoresAPI.update(editingMontador.id, montadorForm);
      } else {
        await montadoresAPI.create(montadorForm);
      }
      setShowMontadorModal(false);
      setEditingMontador(null);
      resetMontadorForm();
      loadMontadores();
    } catch (err) {
      alert(err.message);
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteMontador = async (id) => {
    if (!window.confirm('¿Eliminar este montador?')) return;
    try {
      await montadoresAPI.delete(id);
      loadMontadores();
    } catch (err) {
      alert(err.message);
    }
  };

  const openEditMontador = (montador) => {
    setEditingMontador(montador);
    setMontadorForm({
      name: montador.name || '',
      phone: montador.phone || '',
      email: montador.email || '',
      company: montador.company || '',
      specialty: montador.specialty || '',
      zone: montador.zone || '',
      address: montador.address || '',
      notes: montador.notes || '',
      status: montador.status || 'active',
      rating: montador.rating || 0,
      tags: montador.tags || []
    });
    setShowMontadorModal(true);
  };

  const resetMontadorForm = () => {
    setMontadorForm({
      name: '',
      phone: '',
      email: '',
      company: '',
      specialty: '',
      zone: '',
      address: '',
      notes: '',
      status: 'active',
      rating: 0,
      tags: []
    });
  };

  // Montaje handlers
  const handleSaveMontaje = async () => {
    if (!montajeForm.montadorId || !montajeForm.clientName || !montajeForm.scheduledDate) {
      alert('Montador, cliente y fecha son obligatorios');
      return;
    }
    
    setIsSaving(true);
    try {
      let createdId = editingMontaje?.id;
      if (editingMontaje) {
        await montajesAPI.update(editingMontaje.id, montajeForm);
      } else {
        const created = await montajesAPI.create(montajeForm);
        createdId = created?.id || createdId;
      }
      const wasNew = !editingMontaje;
      const mf = montajeForm;
      setShowMontajeModal(false);
      setEditingMontaje(null);
      resetMontajeForm();
      loadMontajes();

      // Si tiene Google conectado, preguntar si guardar también allí (montajes nuevos).
      if (googleConnected && wasNew) {
        const hasTime = !!mf.scheduledTime;
        setPendingGoogleEvent({
          title: `Montaje: ${mf.clientName}`,
          startDate: hasTime ? `${mf.scheduledDate}T${mf.scheduledTime}` : mf.scheduledDate,
          endDate: hasTime ? `${mf.scheduledDate}T${mf.scheduledTime}` : mf.scheduledDate,
          description: mf.projectDescription || '',
          location: mf.clientAddress || '',
          allDay: !hasTime,
          erpId: createdId,
        });
      }
    } catch (err) {
      alert(err.message);
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteMontaje = async (id) => {
    if (!window.confirm('¿Eliminar este montaje?')) return;
    try {
      await montajesAPI.delete(id);
      loadMontajes();
    } catch (err) {
      alert(err.message);
    }
  };

  const openEditMontaje = (montaje) => {
    setEditingMontaje(montaje);
    setMontajeForm({
      montadorId: montaje.montadorId || '',
      clientName: montaje.clientName || '',
      clientPhone: montaje.clientPhone || '',
      clientAddress: montaje.clientAddress || '',
      projectDescription: montaje.projectDescription || '',
      expectedDeliveryDate: montaje.expectedDeliveryDate || '',
      scheduledDate: montaje.scheduledDate || '',
      scheduledTime: montaje.scheduledTime || '',
      estimatedDuration: montaje.estimatedDuration || '',
      status: montaje.status || 'pendiente',
      budgetRef: montaje.budgetRef || '',
      notes: montaje.notes || ''
    });
    setShowMontajeModal(true);
  };

  const resetMontajeForm = () => {
    setMontajeForm({
      montadorId: '',
      clientName: '',
      clientPhone: '',
      clientAddress: '',
      projectDescription: '',
      expectedDeliveryDate: '',
      scheduledDate: '',
      scheduledTime: '',
      estimatedDuration: '',
      status: 'pendiente',
      budgetRef: '',
      notes: ''
    });
  };

  // Render star rating
  const renderRating = (rating, editable = false, onChange = null) => {
    return (
      <div className="flex items-center gap-0.5">
        {[1, 2, 3, 4, 5].map(star => (
          <button
            key={star}
            type="button"
            onClick={() => editable && onChange && onChange(star)}
            className={`${editable ? 'cursor-pointer hover:scale-110' : 'cursor-default'} transition-transform`}
          >
            <Star 
              size={editable ? 20 : 14} 
              className={star <= rating ? 'text-amber-400 fill-amber-400' : 'text-slate-300'}
            />
          </button>
        ))}
      </div>
    );
  };

  // Get status info
  const getMontadorStatus = (status) => MONTADOR_STATUS.find(s => s.value === status) || MONTADOR_STATUS[0];
  const getMontajeStatus = (status) => MONTAJE_STATUS.find(s => s.value === status) || MONTAJE_STATUS[0];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-orange-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="hueco-logo-centrado flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-gradient-to-br from-orange-500 to-amber-500 rounded-2xl flex items-center justify-center shadow-lg">
              <Wrench className="text-white" size={24} />
            </div>
            <div>
              <h1 className="text-2xl font-black text-slate-900">Agenda de Montajes</h1>
              <p className="text-sm text-slate-500">Gestión de montadores e instalaciones</p>
            </div>
          </div>
          
          <GoogleCalendarConnect compact onStatusChange={(s) => setGoogleConnected(!!s.connected)} />

          {/* Tabs */}
          <div className="flex items-center gap-2 bg-white rounded-xl p-1 shadow-sm">
            {/* Solo mostrar pestaña Montadores a admins */}
            {(!currentUser?.isMontador || currentUser?.isAdmin) && (
              <button
                onClick={() => setActiveTab('montadores')}
                className={`px-4 py-2 rounded-lg text-sm font-bold transition-all ${
                  activeTab === 'montadores' 
                    ? 'bg-orange-500 text-white shadow-md' 
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                <Users size={16} className="inline mr-2" />
                Montadores ({montadores.length})
              </button>
            )}
            <button
              onClick={() => setActiveTab('montajes')}
              className={`px-4 py-2 rounded-lg text-sm font-bold transition-all ${
                activeTab === 'montajes' 
                  ? 'bg-orange-500 text-white shadow-md' 
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              <Wrench size={16} className="inline mr-2" />
              {currentUser?.isMontador && !currentUser?.isAdmin ? 'Mis Montajes' : 'Montajes'} ({filteredMontajes.length})
            </button>
            <button
              onClick={() => setActiveTab('calendario')}
              className={`px-4 py-2 rounded-lg text-sm font-bold transition-all ${
                activeTab === 'calendario' 
                  ? 'bg-orange-500 text-white shadow-md' 
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              <Calendar size={16} className="inline mr-2" />
              Mi Calendario
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-2xl shadow-sm p-4 mb-6">
          <div className="flex items-center gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
              <input
                type="text"
                placeholder={currentUser?.isAdmin ? "Buscar (cliente, montador, usuario...)" : "Buscar..."}
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none focus:border-orange-500"
              />
            </div>
            
            <select
              value={statusFilter}
              onChange={e => setStatusFilter(e.target.value)}
              className="px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium outline-none"
            >
              <option value="">Todos los estados</option>
              {activeTab === 'montadores' 
                ? MONTADOR_STATUS.map(s => <option key={s.value} value={s.value}>{s.label}</option>)
                : MONTAJE_STATUS.map(s => <option key={s.value} value={s.value}>{s.label}</option>)
              }
            </select>
            
            {/* Solo admins pueden crear montajes/montadores.
                Mostramos AMBOS botones siempre, sin depender de la pestaña activa,
                para que la opción de "Nuevo Montaje" esté siempre visible. */}
            {(!currentUser?.isMontador || currentUser?.isAdmin) && (
              <>
                <button
                  onClick={() => {
                    resetMontajeForm();
                    setEditingMontaje(null);
                    setShowMontajeModal(true);
                  }}
                  className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-orange-500 to-amber-500 text-white rounded-xl font-bold text-sm shadow-md hover:shadow-lg transition-all whitespace-nowrap"
                >
                  <Plus size={18} />
                  Nuevo Montaje
                </button>
                <button
                  onClick={() => {
                    resetMontadorForm();
                    setEditingMontador(null);
                    setShowMontadorModal(true);
                  }}
                  className="flex items-center gap-2 px-4 py-2.5 bg-white border-2 border-orange-300 text-orange-600 rounded-xl font-bold text-sm shadow-sm hover:bg-orange-50 transition-all whitespace-nowrap"
                >
                  <Plus size={18} />
                  Nuevo Montador
                </button>
              </>
            )}
          </div>
        </div>

        {/* Content */}
        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="animate-spin text-orange-500" size={40} />
          </div>
        ) : activeTab === 'montadores' ? (
          /* Montadores Grid */
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredMontadores.map(montador => {
              const statusInfo = getMontadorStatus(montador.status);
              const StatusIcon = statusInfo.icon;
              
              return (
                <div key={montador.id} className="bg-white rounded-2xl shadow-sm p-5 hover:shadow-md transition-all">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 bg-gradient-to-br from-orange-100 to-amber-100 rounded-xl flex items-center justify-center">
                        <Wrench className="text-orange-600" size={24} />
                      </div>
                      <div>
                        <h3 className="font-black text-slate-900">{montador.name}</h3>
                        {montador.company && (
                          <p className="text-xs text-slate-500 flex items-center gap-1">
                            <Building2 size={12} /> {montador.company}
                          </p>
                        )}
                        {currentUser?.isAdmin && montador.createdByName && (
                          <p className="text-[10px] text-indigo-500 font-bold mt-0.5">Creado por: {montador.createdByName}</p>
                        )}
                      </div>
                    </div>
                    <span className={`px-2 py-1 rounded-lg text-[10px] font-bold flex items-center gap-1 ${statusInfo.color}`}>
                      <StatusIcon size={12} />
                      {statusInfo.label}
                    </span>
                  </div>
                  
                  <div className="space-y-2 text-sm mb-3">
                    {montador.phone && (
                      <p className="flex items-center gap-2 text-slate-600">
                        <Phone size={14} className="text-slate-400" /> {montador.phone}
                      </p>
                    )}
                    {montador.email && (
                      <p className="flex items-center gap-2 text-slate-600">
                        <Mail size={14} className="text-slate-400" /> {montador.email}
                      </p>
                    )}
                    {montador.zone && (
                      <p className="flex items-center gap-2 text-slate-600">
                        <MapPin size={14} className="text-slate-400" /> {montador.zone}
                      </p>
                    )}
                    {montador.specialty && (
                      <p className="flex items-center gap-2 text-slate-600">
                        <Tag size={14} className="text-slate-400" /> {montador.specialty}
                      </p>
                    )}
                  </div>
                  
                  <div className="flex items-center justify-between pt-3 border-t border-slate-100">
                    <div className="flex items-center gap-2">
                      {renderRating(montador.rating || 0)}
                      <span className="text-xs text-slate-500">({montador.totalMontajes || 0} montajes)</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => openEditMontador(montador)}
                        className="p-2 text-slate-400 hover:text-orange-500 hover:bg-orange-50 rounded-lg transition-colors"
                      >
                        <Edit2 size={16} />
                      </button>
                      <button
                        onClick={() => handleDeleteMontador(montador.id)}
                        className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
            
            {filteredMontadores.length === 0 && (
              <div className="col-span-full py-20 text-center text-slate-500">
                <Users size={48} className="mx-auto mb-4 opacity-30" />
                <p className="font-medium">No hay montadores registrados</p>
                <p className="text-sm">Añade tu primer montador para empezar</p>
              </div>
            )}
          </div>
        ) : activeTab === 'montajes' ? (
          /* Montajes List */
          <div className="space-y-3">
            {filteredMontajes.map(montaje => {
              const statusInfo = getMontajeStatus(montaje.status);
              const StatusIcon = statusInfo.icon;
              
              return (
                <div key={montaje.id} className="bg-white rounded-2xl shadow-sm p-5 hover:shadow-md transition-all">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      {/* Fechas: Recepción y Montaje */}
                      <div className="flex flex-col gap-1">
                        {montaje.expectedDeliveryDate && (
                          <div className="w-14 h-10 bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg flex flex-col items-center justify-center" title="Recepción Cocina">
                            <span className="text-[9px] font-bold text-blue-600">
                              {new Date(montaje.expectedDeliveryDate).toLocaleDateString('es-ES', { day: '2-digit', month: 'short' })}
                            </span>
                            <span className="text-[7px] font-medium text-blue-400">📦 RECEP</span>
                          </div>
                        )}
                        <div className="w-14 h-10 bg-gradient-to-br from-orange-50 to-orange-100 rounded-lg flex flex-col items-center justify-center" title="Montaje Comprometido">
                          <span className="text-[9px] font-bold text-orange-600">
                            {new Date(montaje.scheduledDate).toLocaleDateString('es-ES', { day: '2-digit', month: 'short' })}
                          </span>
                          <span className="text-[7px] font-medium text-orange-400">🔧 MONT</span>
                        </div>
                      </div>
                      
                      <div>
                        <h3 className="font-black text-slate-900">{montaje.clientName}</h3>
                        <p className="text-sm text-slate-500 flex items-center gap-2">
                          <MapPin size={14} /> {montaje.clientAddress}
                        </p>
                        <p className="text-xs text-orange-600 font-medium mt-1">
                          <Wrench size={12} className="inline mr-1" />
                          {montaje.montadorName || 'Sin asignar'}
                          {montaje.scheduledTime && ` • ${montaje.scheduledTime}`}
                          {montaje.estimatedDuration && ` • ${montaje.estimatedDuration}`}
                        </p>
                        {currentUser?.isAdmin && montaje.createdByName && (
                          <p className="text-[10px] text-indigo-500 font-bold mt-0.5">Creado por: {montaje.createdByName}</p>
                        )}
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-4">
                      {montaje.budgetRef && (
                        <span className="px-3 py-1 bg-slate-100 text-slate-600 rounded-lg text-xs font-bold">
                          #{montaje.budgetRef}
                        </span>
                      )}
                      <span className={`px-3 py-1.5 rounded-lg text-xs font-bold flex items-center gap-1 ${statusInfo.color}`}>
                        <StatusIcon size={14} />
                        {statusInfo.label}
                      </span>
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => openEditMontaje(montaje)}
                          className="p-2 text-slate-400 hover:text-orange-500 hover:bg-orange-50 rounded-lg transition-colors"
                        >
                          <Edit2 size={16} />
                        </button>
                        <button
                          onClick={() => handleDeleteMontaje(montaje.id)}
                          className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
            
            {filteredMontajes.length === 0 && (
              <div className="py-20 text-center text-slate-500">
                <Calendar size={48} className="mx-auto mb-4 opacity-30" />
                <p className="font-medium">
                  {currentUser?.isMontador && !currentUser?.isAdmin 
                    ? 'No tienes montajes asignados' 
                    : 'No hay montajes programados'}
                </p>
                <p className="text-sm">
                  {currentUser?.isMontador && !currentUser?.isAdmin 
                    ? 'Los administradores asignarán montajes a tu agenda' 
                    : 'Programa tu primer montaje'}
                </p>
              </div>
            )}
          </div>
        ) : activeTab === 'calendario' ? (
          /* Calendario View */
          <div className="bg-white rounded-2xl shadow-sm p-6">
            {/* Header del calendario */}
            <div className="flex items-center justify-between mb-6">
              <button
                onClick={() => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1))}
                className="p-2 hover:bg-slate-100 rounded-xl transition-colors"
              >
                <ChevronLeft size={24} />
              </button>
              <h3 className="text-xl font-black text-slate-900 uppercase">
                {currentMonth.toLocaleDateString('es-ES', { month: 'long', year: 'numeric' })}
              </h3>
              <button
                onClick={() => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1))}
                className="p-2 hover:bg-slate-100 rounded-xl transition-colors"
              >
                <ChevronRight size={24} />
              </button>
            </div>
            
            {/* Días de la semana */}
            <div className="grid grid-cols-7 gap-1 mb-2 min-w-[400px]">
              {['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'].map(day => (
                <div key={day} className="text-center text-xs font-bold text-slate-500 uppercase py-2">
                  {day}
                </div>
              ))}
            </div>
            
            {/* Días del mes */}
            <div className="grid grid-cols-7 gap-1 min-w-[400px]">
              {(() => {
                const year = currentMonth.getFullYear();
                const month = currentMonth.getMonth();
                const firstDay = new Date(year, month, 1);
                const lastDay = new Date(year, month + 1, 0);
                const startDayOfWeek = (firstDay.getDay() + 6) % 7; // Lunes = 0
                const daysInMonth = lastDay.getDate();
                const days = [];
                
                // Días vacíos al inicio
                for (let i = 0; i < startDayOfWeek; i++) {
                  days.push(<div key={`empty-${i}`} className="h-24" />);
                }
                
                // Días del mes
                for (let day = 1; day <= daysInMonth; day++) {
                  const date = new Date(year, month, day);
                  const dateStr = date.toISOString().split('T')[0];
                  const dayMontajes = montajes.filter(m => {
                    const mDate = m.scheduledDate?.split('T')[0];
                    return mDate === dateStr;
                  });
                  const isToday = new Date().toDateString() === date.toDateString();
                  
                  days.push(
                    <div 
                      key={day} 
                      className={`h-24 border border-slate-100 rounded-xl p-1 overflow-hidden transition-colors ${
                        isToday ? 'bg-orange-50 border-orange-300' : 'hover:bg-slate-50'
                      }`}
                    >
                      <div className={`text-right text-sm font-bold ${isToday ? 'text-orange-600' : 'text-slate-600'}`}>
                        {day}
                      </div>
                      <div className="space-y-0.5 overflow-y-auto max-h-16">
                        {dayMontajes.map(m => {
                          const montador = montadores.find(mt => mt.id === m.montadorId);
                          return (
                            <div 
                              key={m.id}
                              className="text-[10px] bg-gradient-to-r from-orange-500 to-amber-500 text-white px-1.5 py-0.5 rounded truncate cursor-pointer hover:opacity-80"
                              title={`${m.clientName} - ${montador?.name || 'Sin asignar'}`}
                              onClick={() => {
                                setEditingMontaje(m);
                                setMontajeForm({
                                  montadorId: m.montadorId || '',
                                  clientName: m.clientName || '',
                                  clientPhone: m.clientPhone || '',
                                  clientAddress: m.clientAddress || '',
                                  projectDescription: m.projectDescription || '',
                                  expectedDeliveryDate: m.expectedDeliveryDate || '',
                                  scheduledDate: m.scheduledDate || '',
                                  scheduledTime: m.scheduledTime || '',
                                  estimatedDuration: m.estimatedDuration || '',
                                  status: m.status || 'pendiente',
                                  budgetRef: m.budgetRef || '',
                                  notes: m.notes || ''
                                });
                                setShowMontajeModal(true);
                              }}
                            >
                              {m.scheduledTime && <span className="font-bold">{m.scheduledTime} </span>}
                              {m.clientName}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  );
                }
                
                return days;
              })()}
            </div>
            
            {/* Leyenda */}
            <div className="mt-4 pt-4 border-t border-slate-100">
              <div className="flex items-center gap-4 text-xs text-slate-500">
                <div className="flex items-center gap-1">
                  <div className="w-3 h-3 rounded bg-gradient-to-r from-orange-500 to-amber-500"></div>
                  <span>Montaje programado</span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-3 h-3 rounded bg-orange-100 border border-orange-300"></div>
                  <span>Hoy</span>
                </div>
              </div>
            </div>
          </div>
        ) : null}
      </div>

      {/* Modal Montador */}
      {showMontadorModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-3xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-slate-100 flex items-center justify-between">
              <h2 className="text-xl font-black text-slate-900">
                {editingMontador ? 'Editar Montador' : 'Nuevo Montador'}
              </h2>
              <button onClick={() => setShowMontadorModal(false)} className="p-2 hover:bg-slate-100 rounded-xl">
                <X size={20} />
              </button>
            </div>
            
            <div className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-bold text-slate-600 uppercase mb-1 block">Nombre *</label>
                  <input
                    type="text"
                    value={montadorForm.name}
                    onChange={e => setMontadorForm({...montadorForm, name: e.target.value})}
                    className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none focus:border-orange-500"
                    placeholder="Nombre completo"
                  />
                </div>
                <div>
                  <label className="text-xs font-bold text-slate-600 uppercase mb-1 block">Empresa</label>
                  <input
                    type="text"
                    value={montadorForm.company}
                    onChange={e => setMontadorForm({...montadorForm, company: e.target.value})}
                    className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none focus:border-orange-500"
                    placeholder="Empresa o autónomo"
                  />
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-bold text-slate-600 uppercase mb-1 block">Teléfono</label>
                  <input
                    type="tel"
                    value={montadorForm.phone}
                    onChange={e => setMontadorForm({...montadorForm, phone: e.target.value})}
                    className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none focus:border-orange-500"
                    placeholder="600 000 000"
                  />
                </div>
                <div>
                  <label className="text-xs font-bold text-slate-600 uppercase mb-1 block">Email</label>
                  <input
                    type="email"
                    value={montadorForm.email}
                    onChange={e => setMontadorForm({...montadorForm, email: e.target.value})}
                    className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none focus:border-orange-500"
                    placeholder="email@ejemplo.com"
                  />
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-bold text-slate-600 uppercase mb-1 block">Especialidad</label>
                  <select
                    value={montadorForm.specialty}
                    onChange={e => setMontadorForm({...montadorForm, specialty: e.target.value})}
                    className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none"
                  >
                    <option value="">Seleccionar...</option>
                    {SPECIALTIES.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-xs font-bold text-slate-600 uppercase mb-1 block">Zona de trabajo</label>
                  <input
                    type="text"
                    value={montadorForm.zone}
                    onChange={e => setMontadorForm({...montadorForm, zone: e.target.value})}
                    className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none focus:border-orange-500"
                    placeholder="Madrid, Toledo, etc."
                  />
                </div>
              </div>
              
              <div>
                <label className="text-xs font-bold text-slate-600 uppercase mb-1 block">Dirección</label>
                <input
                  type="text"
                  value={montadorForm.address}
                  onChange={e => setMontadorForm({...montadorForm, address: e.target.value})}
                  className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none focus:border-orange-500"
                  placeholder="Dirección completa"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-bold text-slate-600 uppercase mb-1 block">Estado</label>
                  <select
                    value={montadorForm.status}
                    onChange={e => setMontadorForm({...montadorForm, status: e.target.value})}
                    className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none"
                  >
                    {MONTADOR_STATUS.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-xs font-bold text-slate-600 uppercase mb-1 block">Valoración</label>
                  <div className="pt-2">
                    {renderRating(montadorForm.rating, true, (rating) => setMontadorForm({...montadorForm, rating}))}
                  </div>
                </div>
              </div>
              
              <div>
                <label className="text-xs font-bold text-slate-600 uppercase mb-1 block">Notas</label>
                <textarea
                  value={montadorForm.notes}
                  onChange={e => setMontadorForm({...montadorForm, notes: e.target.value})}
                  className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none focus:border-orange-500 resize-none"
                  rows={3}
                  placeholder="Observaciones..."
                />
              </div>
            </div>
            
            <div className="p-6 border-t border-slate-100 flex justify-end gap-3">
              <button
                onClick={() => setShowMontadorModal(false)}
                className="px-6 py-2.5 text-slate-600 font-bold text-sm hover:bg-slate-100 rounded-xl transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={handleSaveMontador}
                disabled={isSaving}
                className="px-6 py-2.5 bg-gradient-to-r from-orange-500 to-amber-500 text-white font-bold text-sm rounded-xl shadow-md hover:shadow-lg transition-all flex items-center gap-2"
              >
                {isSaving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
                Guardar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal Montaje */}
      {showMontajeModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-3xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-slate-100 flex items-center justify-between">
              <h2 className="text-xl font-black text-slate-900">
                {editingMontaje ? 'Editar Montaje' : 'Nuevo Montaje'}
              </h2>
              <button onClick={() => setShowMontajeModal(false)} className="p-2 hover:bg-slate-100 rounded-xl">
                <X size={20} />
              </button>
            </div>
            
            <div className="p-6 space-y-4">
              <div>
                <label className="text-xs font-bold text-slate-600 uppercase mb-1 block">Montador *</label>
                <select
                  value={montajeForm.montadorId}
                  onChange={e => setMontajeForm({...montajeForm, montadorId: e.target.value})}
                  className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none"
                >
                  <option value="">Seleccionar montador...</option>
                  {montadores.filter(m => m.status === 'active').map(m => (
                    <option key={m.id} value={m.id}>{m.name} - {m.zone || 'Sin zona'}</option>
                  ))}
                </select>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-bold text-slate-600 uppercase mb-1 block">Cliente *</label>
                  <input
                    type="text"
                    value={montajeForm.clientName}
                    onChange={e => setMontajeForm({...montajeForm, clientName: e.target.value})}
                    className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none focus:border-orange-500"
                    placeholder="Nombre del cliente"
                  />
                </div>
                <div>
                  <label className="text-xs font-bold text-slate-600 uppercase mb-1 block">Teléfono cliente</label>
                  <input
                    type="tel"
                    value={montajeForm.clientPhone}
                    onChange={e => setMontajeForm({...montajeForm, clientPhone: e.target.value})}
                    className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none focus:border-orange-500"
                    placeholder="600 000 000"
                  />
                </div>
              </div>
              
              <div>
                <label className="text-xs font-bold text-slate-600 uppercase mb-1 block">Dirección de montaje *</label>
                <input
                  type="text"
                  value={montajeForm.clientAddress}
                  onChange={e => setMontajeForm({...montajeForm, clientAddress: e.target.value})}
                  className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none focus:border-orange-500"
                  placeholder="Dirección completa"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-bold text-slate-600 uppercase mb-1 block">📦 Recepción Cocina</label>
                  <input
                    type="date"
                    value={montajeForm.expectedDeliveryDate}
                    onChange={e => setMontajeForm({...montajeForm, expectedDeliveryDate: e.target.value})}
                    className="w-full px-4 py-2.5 bg-blue-50 border border-blue-200 rounded-xl text-sm outline-none focus:border-blue-500"
                  />
                  <p className="text-[9px] text-blue-500 mt-0.5">Fecha prevista de recepción</p>
                </div>
                <div>
                  <label className="text-xs font-bold text-slate-600 uppercase mb-1 block">🔧 Montaje Comprometido *</label>
                  <input
                    type="date"
                    value={montajeForm.scheduledDate}
                    onChange={e => setMontajeForm({...montajeForm, scheduledDate: e.target.value})}
                    className="w-full px-4 py-2.5 bg-orange-50 border border-orange-200 rounded-xl text-sm outline-none focus:border-orange-500"
                  />
                  <p className="text-[9px] text-orange-500 mt-0.5">Fecha comprometida de instalación</p>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-bold text-slate-600 uppercase mb-1 block">Hora</label>
                  <input
                    type="time"
                    value={montajeForm.scheduledTime}
                    onChange={e => setMontajeForm({...montajeForm, scheduledTime: e.target.value})}
                    className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none focus:border-orange-500"
                  />
                </div>
                <div>
                  <label className="text-xs font-bold text-slate-600 uppercase mb-1 block">Duración estimada</label>
                  <input
                    type="text"
                    value={montajeForm.estimatedDuration}
                    onChange={e => setMontajeForm({...montajeForm, estimatedDuration: e.target.value})}
                    className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none focus:border-orange-500"
                    placeholder="2 días"
                  />
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-bold text-slate-600 uppercase mb-1 block">Estado</label>
                  <select
                    value={montajeForm.status}
                    onChange={e => setMontajeForm({...montajeForm, status: e.target.value})}
                    className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none"
                  >
                    {MONTAJE_STATUS.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-xs font-bold text-slate-600 uppercase mb-1 block">Ref. Presupuesto</label>
                  <input
                    type="text"
                    value={montajeForm.budgetRef}
                    onChange={e => setMontajeForm({...montajeForm, budgetRef: e.target.value})}
                    className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none focus:border-orange-500"
                    placeholder="EXP-2026-001"
                  />
                </div>
              </div>
              
              <div>
                <label className="text-xs font-bold text-slate-600 uppercase mb-1 block">Descripción del proyecto</label>
                <textarea
                  value={montajeForm.projectDescription}
                  onChange={e => setMontajeForm({...montajeForm, projectDescription: e.target.value})}
                  className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none focus:border-orange-500 resize-none"
                  rows={2}
                  placeholder="Cocina completa, armarios, etc."
                />
              </div>
              
              <div>
                <label className="text-xs font-bold text-slate-600 uppercase mb-1 block">Notas</label>
                <textarea
                  value={montajeForm.notes}
                  onChange={e => setMontajeForm({...montajeForm, notes: e.target.value})}
                  className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm outline-none focus:border-orange-500 resize-none"
                  rows={2}
                  placeholder="Observaciones..."
                />
              </div>
            </div>
            
            <div className="p-6 border-t border-slate-100 flex justify-end gap-3">
              <button
                onClick={() => setShowMontajeModal(false)}
                className="px-6 py-2.5 text-slate-600 font-bold text-sm hover:bg-slate-100 rounded-xl transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={handleSaveMontaje}
                disabled={isSaving}
                className="px-6 py-2.5 bg-gradient-to-r from-orange-500 to-amber-500 text-white font-bold text-sm rounded-xl shadow-md hover:shadow-lg transition-all flex items-center gap-2"
              >
                {isSaving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
                Guardar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Preguntar si guardar también en Google Calendar */}
      <GoogleSyncModal
        event={pendingGoogleEvent}
        defaultContext="montajes"
        currentUser={currentUser}
        onClose={() => setPendingGoogleEvent(null)}
      />
    </div>
  );
};

export default AgendaMontajes;
