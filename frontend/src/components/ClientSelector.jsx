import React, { useState, useEffect, useRef } from 'react';
import { Search, Plus, User, Building2, Phone, Mail, X, ChevronDown, Check, UserPlus } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

/**
 * ClientSelector - Componente para seleccionar o crear clientes en el presupuestador
 * 
 * Permisos:
 * - Admin/Director Comercial: Ve todos los clientes
 * - Comerciales: Solo ven sus clientes asignados
 * - Tiendas: Gestionan su propia base de datos de clientes (clientes proyecto)
 * - Colaboradores Comerciales: Sin acceso
 */
const ClientSelector = ({ 
  value, 
  onChange, 
  currentUser,
  onClientSelected,
  placeholder = "Buscar o crear cliente..."
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [clients, setClients] = useState([]);
  const [filteredClients, setFilteredClients] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newClientName, setNewClientName] = useState('');
  const [newClientPhone, setNewClientPhone] = useState('');
  const [newClientEmail, setNewClientEmail] = useState('');
  const containerRef = useRef(null);

  // Check if user can access clients
  const canAccessClients = currentUser && !currentUser.isPrescriptor;
  
  // Check if user can create new clients
  const canCreateClients = currentUser && (
    currentUser.isAdmin || 
    currentUser.isRepresentative || 
    currentUser.isTienda ||
    currentUser.isResponsableDelegacion
  );

  // Fetch clients on mount
  useEffect(() => {
    if (canAccessClients) {
      fetchClients();
    }
  }, [canAccessClients]);

  // Filter clients based on search query and user permissions
  useEffect(() => {
    if (!searchQuery.trim()) {
      setFilteredClients(clients.slice(0, 20)); // Show first 20 by default
      return;
    }

    const query = searchQuery.toLowerCase();
    const filtered = clients.filter(client => 
      client.nombre?.toLowerCase().includes(query) ||
      client.codigo?.toLowerCase().includes(query) ||
      client.telefono?.includes(query) ||
      client.email?.toLowerCase().includes(query)
    );
    setFilteredClients(filtered.slice(0, 30));
  }, [searchQuery, clients]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setIsOpen(false);
        setShowCreateForm(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const fetchClients = async () => {
    setIsLoading(true);
    try {
      // Fetch from CRM contacts as they are the main source
      const response = await fetch(`${API_URL}/api/crm/contacts`);
      if (!response.ok) throw new Error('Error fetching contacts');
      
      let contactsData = await response.json();
      
      // Apply permission filters
      if (currentUser) {
        if (currentUser.isAdmin || currentUser.isResponsableDelegacion) {
          // Admins and Responsables see all
        } else if (currentUser.isRepresentative) {
          // Comerciales: Only see their assigned clients
          contactsData = contactsData.filter(c => 
            c.assignedTo === currentUser.id || 
            c.createdBy === currentUser.id
          );
        } else if (currentUser.isTienda) {
          // Tiendas: Only see their own created clients
          contactsData = contactsData.filter(c => 
            c.createdBy === currentUser.id
          );
        }
      }

      // Map contacts to client format
      const mappedClients = contactsData.map(contact => ({
        id: contact.id,
        codigo: contact.id.substring(0, 8).toUpperCase(),
        nombre: contact.name,
        telefono: contact.phone || '',
        email: contact.email || '',
        empresa: contact.company || '',
        tipo: contact.status === 'customer' ? 'activo' : 'potencial',
        assignedTo: contact.assignedTo
      }));

      setClients(mappedClients);
      setFilteredClients(mappedClients.slice(0, 20));
    } catch (error) {
      console.error('Error fetching clients:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectClient = (client) => {
    onChange(client.nombre);
    if (onClientSelected) {
      onClientSelected(client);
    }
    setIsOpen(false);
    setSearchQuery('');
  };

  const handleCreateClient = async () => {
    if (!newClientName.trim()) return;

    try {
      // Create new contact in CRM
      const response = await fetch(`${API_URL}/api/crm/contacts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newClientName.toUpperCase(),
          phone: newClientPhone,
          email: newClientEmail,
          source: currentUser?.isTienda ? 'tienda' : 'presupuesto',
          status: 'lead',
          assignedTo: currentUser?.id || '',
          notes: `Cliente creado desde presupuestador por ${currentUser?.username || 'Usuario'}`
        })
      });

      if (!response.ok) throw new Error('Error creating contact');
      
      const newContact = await response.json();
      
      // Add to local list
      const newClient = {
        id: newContact.id,
        codigo: newContact.id.substring(0, 8).toUpperCase(),
        nombre: newContact.name,
        telefono: newContact.phone || '',
        email: newContact.email || '',
        tipo: 'potencial',
        assignedTo: newContact.assignedTo
      };

      setClients(prev => [newClient, ...prev]);
      handleSelectClient(newClient);
      
      // Reset form
      setShowCreateForm(false);
      setNewClientName('');
      setNewClientPhone('');
      setNewClientEmail('');
    } catch (error) {
      console.error('Error creating client:', error);
      alert('Error al crear el cliente');
    }
  };

  // If user is Colaborador Comercial, show disabled input
  if (currentUser?.isPrescriptor) {
    return (
      <div className="relative">
        <input 
          type="text" 
          value={value || ''} 
          disabled
          placeholder="Sin acceso a clientes" 
          className="w-full bg-slate-100 border border-slate-200 rounded-lg p-2 text-[9px] font-black outline-none uppercase text-slate-400 cursor-not-allowed" 
        />
      </div>
    );
  }

  return (
    <div ref={containerRef} className="relative">
      {/* Main Input */}
      <div 
        className="relative cursor-pointer"
        onClick={() => setIsOpen(true)}
      >
        <User className="absolute left-2 top-1/2 -translate-y-1/2 text-indigo-300" size={12} />
        <input 
          type="text" 
          value={isOpen ? searchQuery : value || ''} 
          onChange={(e) => {
            setSearchQuery(e.target.value);
            if (!isOpen) setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
          placeholder={placeholder}
          className="w-full bg-indigo-50/30 border border-indigo-100 rounded-lg py-2 pl-7 pr-8 text-[9px] font-black outline-none focus:border-orange-500 uppercase"
          data-testid="client-selector-input"
        />
        <ChevronDown 
          size={14} 
          className={`absolute right-2 top-1/2 -translate-y-1/2 text-indigo-300 transition-transform ${isOpen ? 'rotate-180' : ''}`} 
        />
      </div>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-indigo-200 rounded-xl shadow-xl max-h-64 overflow-hidden">
          {/* Search header */}
          <div className="p-2 border-b border-indigo-100 bg-indigo-50/50">
            <div className="flex items-center gap-2">
              <Search size={12} className="text-indigo-400" />
              <span className="text-[8px] font-bold text-indigo-400 uppercase">
                {isLoading ? 'Cargando...' : `${filteredClients.length} clientes`}
              </span>
              {canCreateClients && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setShowCreateForm(true);
                    setNewClientName(searchQuery);
                  }}
                  className="ml-auto flex items-center gap-1 px-2 py-1 bg-emerald-500 hover:bg-emerald-600 text-white rounded-lg text-[7px] font-black uppercase transition-colors"
                  data-testid="create-new-client-btn"
                >
                  <UserPlus size={10} /> Nuevo
                </button>
              )}
            </div>
          </div>

          {/* Create Form */}
          {showCreateForm && (
            <div className="p-3 bg-emerald-50 border-b border-emerald-200 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[9px] font-black text-emerald-800 uppercase">Crear Nuevo Cliente</span>
                <button 
                  onClick={() => setShowCreateForm(false)}
                  className="p-1 hover:bg-emerald-200 rounded"
                >
                  <X size={12} className="text-emerald-600" />
                </button>
              </div>
              <input
                type="text"
                value={newClientName}
                onChange={(e) => setNewClientName(e.target.value.toUpperCase())}
                placeholder="Nombre del cliente *"
                className="w-full bg-white border border-emerald-200 rounded-lg p-2 text-[9px] font-bold outline-none focus:border-emerald-500 uppercase"
                autoFocus
                data-testid="new-client-name-input"
              />
              <div className="flex gap-2">
                <input
                  type="tel"
                  value={newClientPhone}
                  onChange={(e) => setNewClientPhone(e.target.value)}
                  placeholder="Teléfono"
                  className="flex-1 bg-white border border-emerald-200 rounded-lg p-2 text-[9px] font-bold outline-none focus:border-emerald-500"
                  data-testid="new-client-phone-input"
                />
                <input
                  type="email"
                  value={newClientEmail}
                  onChange={(e) => setNewClientEmail(e.target.value)}
                  placeholder="Email"
                  className="flex-1 bg-white border border-emerald-200 rounded-lg p-2 text-[9px] font-bold outline-none focus:border-emerald-500"
                  data-testid="new-client-email-input"
                />
              </div>
              <button
                onClick={handleCreateClient}
                disabled={!newClientName.trim()}
                className="w-full py-2 bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-300 text-white rounded-lg text-[9px] font-black uppercase transition-colors flex items-center justify-center gap-2"
                data-testid="confirm-create-client-btn"
              >
                <Check size={12} /> Crear y Seleccionar
              </button>
            </div>
          )}

          {/* Client List */}
          {!showCreateForm && (
            <div className="overflow-y-auto max-h-48">
              {filteredClients.length === 0 ? (
                <div className="p-4 text-center">
                  <p className="text-[9px] text-indigo-400">No se encontraron clientes</p>
                  {searchQuery && canCreateClients && (
                    <button
                      onClick={() => {
                        setShowCreateForm(true);
                        setNewClientName(searchQuery);
                      }}
                      className="mt-2 text-[9px] font-bold text-emerald-600 hover:underline"
                    >
                      + Crear "{searchQuery}" como nuevo cliente
                    </button>
                  )}
                </div>
              ) : (
                filteredClients.map((client) => (
                  <div
                    key={client.id}
                    onClick={() => handleSelectClient(client)}
                    className="p-2 hover:bg-indigo-50 cursor-pointer border-b border-indigo-50 last:border-b-0 transition-colors"
                    data-testid={`client-option-${client.id}`}
                  >
                    <div className="flex items-center gap-2">
                      <div className={`p-1.5 rounded-lg ${client.tipo === 'activo' ? 'bg-emerald-100' : 'bg-amber-100'}`}>
                        <User size={10} className={client.tipo === 'activo' ? 'text-emerald-600' : 'text-amber-600'} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-[9px] font-black text-indigo-900 uppercase truncate">
                          {client.nombre}
                        </p>
                        <div className="flex items-center gap-2 text-[7px] text-indigo-400">
                          {client.telefono && (
                            <span className="flex items-center gap-0.5">
                              <Phone size={8} /> {client.telefono}
                            </span>
                          )}
                          {client.empresa && (
                            <span className="flex items-center gap-0.5">
                              <Building2 size={8} /> {client.empresa}
                            </span>
                          )}
                        </div>
                      </div>
                      <span className={`px-1.5 py-0.5 rounded text-[6px] font-black uppercase ${
                        client.tipo === 'activo' 
                          ? 'bg-emerald-100 text-emerald-700' 
                          : 'bg-amber-100 text-amber-700'
                      }`}>
                        {client.tipo === 'activo' ? 'Activo' : 'Lead'}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ClientSelector;
