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
  getAll: async (status = null, search = null) => {
    let url = `${API_URL}/api/crm/contacts`;
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (search) params.append('search', search);
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
  getAll: async (stage = null, contactId = null) => {
    let url = `${API_URL}/api/crm/opportunities`;
    const params = new URLSearchParams();
    if (stage) params.append('stage', stage);
    if (contactId) params.append('contactId', contactId);
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

  createFromProject: async (projectId) => {
    const response = await fetch(`${API_URL}/api/crm/opportunities/from-project/${projectId}`, {
      method: 'POST'
    });
    if (!response.ok) throw new Error('Error al crear oportunidad desde proyecto');
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
  get: async () => {
    const response = await fetch(`${API_URL}/api/crm/dashboard`);
    if (!response.ok) throw new Error('Error al obtener dashboard CRM');
    return response.json();
  }
};
