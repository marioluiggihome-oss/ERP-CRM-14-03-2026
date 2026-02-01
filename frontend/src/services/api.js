// API Service for LUIGGI HOME
const API_URL = process.env.REACT_APP_BACKEND_URL;

// ============================================
// AUTH
// ============================================

export const authAPI = {
  login: async (username, password) => {
    const response = await fetch(`${API_URL}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Error de autenticación');
    }
    return response.json();
  },

  init: async () => {
    const response = await fetch(`${API_URL}/api/init`, { method: 'POST' });
    return response.json();
  }
};

// ============================================
// EXPEDIENT (CONTADOR CORRELATIVO)
// ============================================

export const expedientAPI = {
  getNext: async () => {
    const response = await fetch(`${API_URL}/api/expedient/next`);
    if (!response.ok) throw new Error('Error al obtener número de expediente');
    return response.json();
  },
  
  getCurrent: async () => {
    const response = await fetch(`${API_URL}/api/expedient/current`);
    if (!response.ok) throw new Error('Error al obtener info de expediente');
    return response.json();
  }
};

// ============================================
// USERS
// ============================================

export const usersAPI = {
  getAll: async () => {
    const response = await fetch(`${API_URL}/api/users`);
    if (!response.ok) throw new Error('Error al obtener usuarios');
    return response.json();
  },

  getById: async (id) => {
    const response = await fetch(`${API_URL}/api/users/${id}`);
    if (!response.ok) throw new Error('Usuario no encontrado');
    return response.json();
  },

  create: async (user) => {
    const response = await fetch(`${API_URL}/api/users`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(user)
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Error al crear usuario');
    }
    return response.json();
  },

  update: async (id, user) => {
    const response = await fetch(`${API_URL}/api/users/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(user)
    });
    if (!response.ok) throw new Error('Error al actualizar usuario');
    return response.json();
  },

  delete: async (id) => {
    const response = await fetch(`${API_URL}/api/users/${id}`, {
      method: 'DELETE'
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Error al eliminar usuario');
    }
    return response.json();
  }
};

// ============================================
// CLIENTS (Clientes Activos)
// ============================================

export const clientsAPI = {
  getAll: async (activo = null, search = null) => {
    let url = `${API_URL}/api/clients`;
    const params = new URLSearchParams();
    if (activo !== null) params.append('activo', activo);
    if (search) params.append('search', search);
    if (params.toString()) url += `?${params.toString()}`;
    
    const response = await fetch(url);
    if (!response.ok) throw new Error('Error al obtener clientes');
    return response.json();
  },

  getById: async (id) => {
    const response = await fetch(`${API_URL}/api/clients/${id}`);
    if (!response.ok) throw new Error('Cliente no encontrado');
    return response.json();
  },

  create: async (client) => {
    const response = await fetch(`${API_URL}/api/clients`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(client)
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Error al crear cliente');
    }
    return response.json();
  },

  update: async (id, client) => {
    const response = await fetch(`${API_URL}/api/clients/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(client)
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Error al actualizar cliente');
    }
    return response.json();
  },

  delete: async (id, force = false) => {
    const url = force 
      ? `${API_URL}/api/clients/${id}?force=true`
      : `${API_URL}/api/clients/${id}`;
    
    const response = await fetch(url, {
      method: 'DELETE'
    });
    
    // Read response as text first (more robust)
    const responseText = await response.text();
    
    // If successful, return parsed JSON or success message
    if (response.ok) {
      try {
        return JSON.parse(responseText);
      } catch {
        return { message: 'Cliente eliminado' };
      }
    }
    
    // If error, try to parse error message
    try {
      const errorData = JSON.parse(responseText);
      throw new Error(errorData.detail || 'Error al eliminar cliente');
    } catch (parseError) {
      if (parseError.message && !parseError.message.includes('JSON')) {
        throw parseError;
      }
      throw new Error('Error al eliminar cliente');
    }
  },

  importCSV: async (clients) => {
    const response = await fetch(`${API_URL}/api/clients/import-csv`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ clients })
    });
    if (!response.ok) throw new Error('Error al importar clientes');
    return response.json();
  },

  getSegments: async () => {
    const response = await fetch(`${API_URL}/api/clients/segments`);
    if (!response.ok) throw new Error('Error al obtener segmentos');
    return response.json();
  },

  createFromContact: async (contactId) => {
    const response = await fetch(`${API_URL}/api/clients/from-contact/${contactId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Error al convertir contacto');
    }
    return response.json();
  },

  activate: async (id, codigo) => {
    const response = await fetch(`${API_URL}/api/clients/${id}/activate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ codigo })
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Error al activar cliente');
    }
    return response.json();
  },

  linkUser: async (id, userId) => {
    const response = await fetch(`${API_URL}/api/clients/${id}/link-user`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ userId })
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Error al vincular usuario');
    }
    return response.json();
  }
};

// ============================================
// PRODUCTS
// ============================================

export const productsAPI = {
  getAll: async (module = null) => {
    const url = module 
      ? `${API_URL}/api/products?module=${module}`
      : `${API_URL}/api/products`;
    const response = await fetch(url);
    if (!response.ok) throw new Error('Error al obtener productos');
    return response.json();
  },

  getById: async (id) => {
    const response = await fetch(`${API_URL}/api/products/${id}`);
    if (!response.ok) throw new Error('Producto no encontrado');
    return response.json();
  },

  create: async (product) => {
    const response = await fetch(`${API_URL}/api/products`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(product)
    });
    if (!response.ok) throw new Error('Error al crear producto');
    return response.json();
  },

  createBulk: async (products) => {
    const response = await fetch(`${API_URL}/api/products/bulk`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(products)
    });
    if (!response.ok) throw new Error('Error al crear productos');
    return response.json();
  },

  // Alias for backwards compatibility
  bulkCreate: async (products) => {
    const response = await fetch(`${API_URL}/api/products/bulk`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(products)
    });
    if (!response.ok) throw new Error('Error al crear productos');
    return response.json();
  },

  update: async (id, product) => {
    const response = await fetch(`${API_URL}/api/products/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(product)
    });
    if (!response.ok) throw new Error('Error al actualizar producto');
    return response.json();
  },

  delete: async (id) => {
    const response = await fetch(`${API_URL}/api/products/${id}`, {
      method: 'DELETE'
    });
    if (!response.ok) throw new Error('Error al eliminar producto');
    return response.json();
  },

  deleteBulk: async (ids) => {
    const response = await fetch(`${API_URL}/api/products/bulk/delete`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(ids)
    });
    if (!response.ok) throw new Error('Error al eliminar productos');
    return response.json();
  }
};

// ============================================
// MATERIALS
// ============================================

export const materialsAPI = {
  getAll: async () => {
    const response = await fetch(`${API_URL}/api/materials`);
    if (!response.ok) throw new Error('Error al obtener materiales');
    return response.json();
  },

  create: async (material) => {
    const response = await fetch(`${API_URL}/api/materials`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(material)
    });
    if (!response.ok) throw new Error('Error al crear material');
    return response.json();
  },

  update: async (id, material) => {
    const response = await fetch(`${API_URL}/api/materials/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(material)
    });
    if (!response.ok) throw new Error('Error al actualizar material');
    return response.json();
  },

  delete: async (id) => {
    const response = await fetch(`${API_URL}/api/materials/${id}`, {
      method: 'DELETE'
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Error al eliminar material');
    }
    return response.json();
  }
};

// ============================================
// SETTINGS
// ============================================

export const settingsAPI = {
  get: async () => {
    const response = await fetch(`${API_URL}/api/settings`);
    if (!response.ok) throw new Error('Error al obtener configuración');
    return response.json();
  },

  update: async (settings) => {
    const response = await fetch(`${API_URL}/api/settings`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings)
    });
    if (!response.ok) throw new Error('Error al actualizar configuración');
    return response.json();
  }
};

// ============================================
// PROJECTS/BUDGETS
// ============================================

export const projectsAPI = {
  getAll: async (userId = null) => {
    const url = userId 
      ? `${API_URL}/api/projects?user_id=${userId}`
      : `${API_URL}/api/projects`;
    const response = await fetch(url);
    if (!response.ok) throw new Error('Error al obtener proyectos');
    return response.json();
  },

  getById: async (id) => {
    const response = await fetch(`${API_URL}/api/projects/${id}`);
    if (!response.ok) throw new Error('Proyecto no encontrado');
    return response.json();
  },

  create: async (project, userId) => {
    const response = await fetch(`${API_URL}/api/projects?user_id=${userId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(project)
    });
    if (!response.ok) throw new Error('Error al crear proyecto');
    return response.json();
  },

  update: async (id, project) => {
    const response = await fetch(`${API_URL}/api/projects/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(project)
    });
    if (!response.ok) throw new Error('Error al actualizar proyecto');
    return response.json();
  },

  delete: async (id) => {
    const response = await fetch(`${API_URL}/api/projects/${id}`, {
      method: 'DELETE'
    });
    if (!response.ok) throw new Error('Error al eliminar proyecto');
    return response.json();
  }
};

// ============================================
// TELEMETRY (AI)
// ============================================

export const telemetryAPI = {
  analyzeSheets: async (module, files) => {
    const formData = new FormData();
    formData.append('module', module);
    files.forEach(file => {
      formData.append('files', file);
    });
    
    const response = await fetch(`${API_URL}/api/analyze-product-sheets`, {
      method: 'POST',
      body: formData
    });
    
    if (!response.ok) throw new Error('Error al analizar fichas');
    return response.json();
  }
};

// ============================================
// BACKUP
// ============================================

export const backupAPI = {
  getStatus: async () => {
    const response = await fetch(`${API_URL}/api/backup/status`);
    if (!response.ok) throw new Error('Error al obtener estado de backup');
    return response.json();
  },

  triggerManual: async () => {
    const response = await fetch(`${API_URL}/api/backup/manual`, {
      method: 'POST'
    });
    if (!response.ok) throw new Error('Error al crear backup');
    return response.json();
  },

  download: async () => {
    const response = await fetch(`${API_URL}/api/backup/download`);
    if (!response.ok) throw new Error('Error al descargar backup');
    return response.json();
  },

  restore: async (backupData) => {
    const response = await fetch(`${API_URL}/api/backup/restore`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(backupData)
    });
    if (!response.ok) throw new Error('Error al restaurar backup');
    return response.json();
  },

  getHistory: async () => {
    const response = await fetch(`${API_URL}/api/backup/history`);
    if (!response.ok) throw new Error('Error al obtener historial');
    return response.json();
  }
};

// ============================================
// CRM - CONTACTS
// ============================================

export const crmContactsAPI = {
  getAll: async (status = null, search = null, options = {}) => {
    let url = `${API_URL}/api/crm/contacts`;
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (search) params.append('search', search);
    // Filtrado por comercial asignado (para usuarios no-admin)
    if (options.assignedTo) params.append('assignedTo', options.assignedTo);
    if (options.isAdmin !== undefined) params.append('isAdmin', options.isAdmin);
    if (params.toString()) url += `?${params.toString()}`;
    
    const response = await fetch(url);
    if (!response.ok) throw new Error('Error al obtener contactos');
    return response.json();
  },

  getById: async (id) => {
    const response = await fetch(`${API_URL}/api/crm/contacts/${id}`);
    if (!response.ok) throw new Error('Contacto no encontrado');
    return response.json();
  },

  create: async (contact) => {
    const response = await fetch(`${API_URL}/api/crm/contacts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(contact)
    });
    if (!response.ok) throw new Error('Error al crear contacto');
    return response.json();
  },

  update: async (id, contact) => {
    const response = await fetch(`${API_URL}/api/crm/contacts/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(contact)
    });
    if (!response.ok) throw new Error('Error al actualizar contacto');
    return response.json();
  },

  delete: async (id) => {
    const response = await fetch(`${API_URL}/api/crm/contacts/${id}`, {
      method: 'DELETE'
    });
    if (!response.ok) throw new Error('Error al eliminar contacto');
    return response.json();
  }
};

// ============================================
// CRM - OPPORTUNITIES
// ============================================

export const crmOpportunitiesAPI = {
  getAll: async (stage = null, contactId = null, options = {}) => {
    let url = `${API_URL}/api/crm/opportunities`;
    const params = new URLSearchParams();
    if (stage) params.append('stage', stage);
    if (contactId) params.append('contactId', contactId);
    // Filtrado por comercial asignado (para usuarios no-admin)
    if (options.assignedTo) params.append('assignedTo', options.assignedTo);
    if (options.isAdmin !== undefined) params.append('isAdmin', options.isAdmin);
    // Filtrado por tipo de negocio y módulo
    if (options.businessType) params.append('businessType', options.businessType);
    if (options.moduleType) params.append('moduleType', options.moduleType);
    if (params.toString()) url += `?${params.toString()}`;
    
    const response = await fetch(url);
    if (!response.ok) throw new Error('Error al obtener oportunidades');
    return response.json();
  },

  getById: async (id) => {
    const response = await fetch(`${API_URL}/api/crm/opportunities/${id}`);
    if (!response.ok) throw new Error('Oportunidad no encontrada');
    return response.json();
  },

  create: async (opportunity) => {
    const response = await fetch(`${API_URL}/api/crm/opportunities`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(opportunity)
    });
    if (!response.ok) throw new Error('Error al crear oportunidad');
    return response.json();
  },

  createFromProject: async (projectId, businessType = 'cocina') => {
    const response = await fetch(`${API_URL}/api/crm/opportunities/from-project/${projectId}?businessType=${businessType}`, {
      method: 'POST'
    });
    if (!response.ok) throw new Error('Error al crear oportunidad desde proyecto');
    return response.json();
  },

  createFromArmario: async (projectId) => {
    const response = await fetch(`${API_URL}/api/crm/opportunities/from-armario/${projectId}`, {
      method: 'POST'
    });
    if (!response.ok) throw new Error('Error al crear oportunidad desde armario');
    return response.json();
  },

  update: async (id, opportunity) => {
    const response = await fetch(`${API_URL}/api/crm/opportunities/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(opportunity)
    });
    if (!response.ok) throw new Error('Error al actualizar oportunidad');
    return response.json();
  },

  delete: async (id) => {
    const response = await fetch(`${API_URL}/api/crm/opportunities/${id}`, {
      method: 'DELETE'
    });
    if (!response.ok) throw new Error('Error al eliminar oportunidad');
    return response.json();
  }
};

// ============================================
// CRM - ACTIVITIES
// ============================================

export const crmActivitiesAPI = {
  getAll: async (filters = {}) => {
    let url = `${API_URL}/api/crm/activities`;
    const params = new URLSearchParams();
    if (filters.type) params.append('type', filters.type);
    if (filters.contactId) params.append('contactId', filters.contactId);
    if (filters.opportunityId) params.append('opportunityId', filters.opportunityId);
    if (filters.completed !== undefined) params.append('completed', filters.completed);
    if (params.toString()) url += `?${params.toString()}`;
    
    const response = await fetch(url);
    if (!response.ok) throw new Error('Error al obtener actividades');
    return response.json();
  },

  create: async (activity) => {
    const response = await fetch(`${API_URL}/api/crm/activities`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(activity)
    });
    if (!response.ok) throw new Error('Error al crear actividad');
    return response.json();
  },

  update: async (id, activity) => {
    const response = await fetch(`${API_URL}/api/crm/activities/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(activity)
    });
    if (!response.ok) throw new Error('Error al actualizar actividad');
    return response.json();
  },

  delete: async (id) => {
    const response = await fetch(`${API_URL}/api/crm/activities/${id}`, {
      method: 'DELETE'
    });
    if (!response.ok) throw new Error('Error al eliminar actividad');
    return response.json();
  }
};

// ============================================
// CRM - DASHBOARD
// ============================================

export const crmDashboardAPI = {
  get: async (options = {}) => {
    let url = `${API_URL}/api/crm/dashboard`;
    const params = new URLSearchParams();
    // Filtrado por comercial asignado (para usuarios no-admin)
    if (options.assignedTo) params.append('assignedTo', options.assignedTo);
    if (options.isAdmin !== undefined) params.append('isAdmin', options.isAdmin);
    if (params.toString()) url += `?${params.toString()}`;
    
    const response = await fetch(url);
    if (!response.ok) throw new Error('Error al obtener dashboard CRM');
    return response.json();
  }
};

// ============================================
// CRM - ANALYTICS (Clientes Inactivos)
// ============================================

export const crmAnalyticsAPI = {
  getInactiveClients: async (daysWithoutOffer = 30, daysWithoutPurchase = 60) => {
    const response = await fetch(`${API_URL}/api/crm/analytics/inactive-clients?days_without_offer=${daysWithoutOffer}&days_without_purchase=${daysWithoutPurchase}`);
    if (!response.ok) throw new Error('Error al obtener análisis de clientes');
    return response.json();
  }
};

// ============================================
// CRM - CALENDAR (Calendario)
// ============================================

export const crmCalendarAPI = {
  getEventTypes: async () => {
    const response = await fetch(`${API_URL}/api/crm/calendar/event-types`);
    if (!response.ok) throw new Error('Error al obtener tipos de evento');
    return response.json();
  },
  
  getEvents: async (params = {}) => {
    const queryParams = new URLSearchParams();
    if (params.userId) queryParams.append('userId', params.userId);
    if (params.startDate) queryParams.append('startDate', params.startDate);
    if (params.endDate) queryParams.append('endDate', params.endDate);
    if (params.eventType) queryParams.append('eventType', params.eventType);
    if (params.viewAll) queryParams.append('viewAll', 'true');
    if (params.commercialId) queryParams.append('commercialId', params.commercialId);
    
    const response = await fetch(`${API_URL}/api/crm/calendar/events?${queryParams.toString()}`);
    if (!response.ok) throw new Error('Error al obtener eventos');
    return response.json();
  },
  
  create: async (event, createdBy, createdByName) => {
    const response = await fetch(`${API_URL}/api/crm/calendar/events?createdBy=${createdBy}&createdByName=${encodeURIComponent(createdByName)}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(event)
    });
    if (!response.ok) throw new Error('Error al crear evento');
    return response.json();
  },
  
  update: async (eventId, updates) => {
    const response = await fetch(`${API_URL}/api/crm/calendar/events/${eventId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates)
    });
    if (!response.ok) throw new Error('Error al actualizar evento');
    return response.json();
  },
  
  delete: async (eventId) => {
    const response = await fetch(`${API_URL}/api/crm/calendar/events/${eventId}`, {
      method: 'DELETE'
    });
    if (!response.ok) throw new Error('Error al eliminar evento');
    return response.json();
  },
  
  complete: async (eventId) => {
    const response = await fetch(`${API_URL}/api/crm/calendar/events/${eventId}/complete`, {
      method: 'POST'
    });
    if (!response.ok) throw new Error('Error al completar evento');
    return response.json();
  }
};

// ============================================
// DESPIECE (BILL OF MATERIALS)
// ============================================

export const despieceAPI = {
  calculate: async (items, carcassMaterial = "Melamina Blanca", backPanelMaterial = "Tablero 3mm", grosor = 18) => {
    const response = await fetch(`${API_URL}/api/despiece/calculate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        items,
        carcassMaterial,
        backPanelMaterial,
        grosor
      })
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Error al calcular despiece');
    }
    return response.json();
  }
};

// ============================================
// DIGITALIZADOR DE BORRADORES
// ============================================

export const digitalizadorAPI = {
  analyze: async (imageBase64, filename) => {
    const response = await fetch(`${API_URL}/api/digitalizador/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ imageBase64, filename })
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Error al analizar imagen');
    }
    return response.json();
  },

  exportCSV: async (lines, materialCode = "40-ESTEITEX16", materialThickness = 16.0) => {
    const response = await fetch(`${API_URL}/api/digitalizador/export-csv`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lines, materialCode, materialThickness })
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Error al exportar CSV');
    }
    return response.json();
  }
};

// ============================================
// ARMARIOS - PROYECTOS
// ============================================

export const armariosAPI = {
  // Crear proyecto
  create: async (project, userId = "") => {
    const response = await fetch(`${API_URL}/api/armarios/projects?userId=${userId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(project)
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Error al crear proyecto');
    }
    return response.json();
  },

  // Obtener lista de proyectos
  getAll: async (userId = "") => {
    const response = await fetch(`${API_URL}/api/armarios/projects?userId=${userId}`);
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Error al obtener proyectos');
    }
    return response.json();
  },

  // Obtener un proyecto específico
  get: async (projectId) => {
    const response = await fetch(`${API_URL}/api/armarios/projects/${projectId}`);
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Error al obtener proyecto');
    }
    return response.json();
  },

  // Actualizar proyecto
  update: async (projectId, updates) => {
    const response = await fetch(`${API_URL}/api/armarios/projects/${projectId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updates)
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Error al actualizar proyecto');
    }
    return response.json();
  },

  // Eliminar proyecto
  delete: async (projectId) => {
    const response = await fetch(`${API_URL}/api/armarios/projects/${projectId}`, {
      method: 'DELETE'
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Error al eliminar proyecto');
    }
    return response.json();
  },

  // IA: Configurar módulos automáticamente
  iaConfiguracion: async (instruction, currentConfig = {}) => {
    const response = await fetch(`${API_URL}/api/armarios/ia/configure`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ instruction, current_config: currentConfig })
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Error al configurar con IA');
    }
    return response.json();
  },

  // IA: Generar render realista
  iaRender: async (config) => {
    const response = await fetch(`${API_URL}/api/armarios/ia/render`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Error al generar render');
    }
    return response.json();
  }
};

// ============================================
// ADMIN METRICS
// ============================================

export const adminMetricsAPI = {
  get: async () => {
    const response = await fetch(`${API_URL}/api/admin/metrics`);
    if (!response.ok) throw new Error('Error al obtener métricas');
    return response.json();
  },

  getTrends: async () => {
    const response = await fetch(`${API_URL}/api/admin/metrics/trends`);
    if (!response.ok) throw new Error('Error al obtener tendencias');
    return response.json();
  }
};
