/*
 * © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
// API Service for LUIGGI HOME
import axios from 'axios';
const API_URL = process.env.REACT_APP_BACKEND_URL;

// ÚNICA fuente de verdad para leer el token JWT (las claves legacy 'token' y
// 'access_token' se mantienen por compatibilidad con sesiones antiguas).
export const getToken = () => {
  try {
    if (typeof localStorage === 'undefined') return null;
    return localStorage.getItem('luiggi_access_token')
      || localStorage.getItem('token')
      || localStorage.getItem('access_token');
  } catch (_) { return null; }
};

// Interceptor GLOBAL de axios: añade el token JWT a TODAS las peticiones axios
// automáticamente. Evita errores 401 "Autenticación requerida" en cualquier
// llamada (p.ej. guardar presupuesto) por olvidar la cabecera Authorization.
axios.interceptors.request.use((config) => {
  const t = getToken();
  if (t) {
    config.headers = config.headers || {};
    if (!config.headers.Authorization) config.headers.Authorization = `Bearer ${t}`;
  }
  return config;
});

// Helper: build Authorization header with JWT (única forma recomendada de
// construir cabeceras para fetch en toda la app).
export const authHeaders = (extra = {}) => {
  const token = getToken();
  const h = { ...extra };
  if (token) h['Authorization'] = `Bearer ${token}`;
  return h;
};

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
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error de autenticación');
    }
    return data;
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
    const response = await fetch(`${API_URL}/api/users`, { headers: authHeaders() });
    if (!response.ok) throw new Error('Error al obtener usuarios');
    return response.json();
  },

  getById: async (id) => {
    const response = await fetch(`${API_URL}/api/users/${id}`, { headers: authHeaders() });
    if (!response.ok) throw new Error('Usuario no encontrado');
    return response.json();
  },

  create: async (user) => {
    const response = await fetch(`${API_URL}/api/users`, {
      method: 'POST',
      headers: authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(user)
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al crear usuario');
    }
    return data;
  },

  update: async (id, user) => {
    const response = await fetch(`${API_URL}/api/users/${id}`, {
      method: 'PUT',
      headers: authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(user)
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al actualizar usuario');
    }
    return data;
  },

  delete: async (id) => {
    const response = await fetch(`${API_URL}/api/users/${id}`, {
      method: 'DELETE',
      headers: authHeaders()
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al eliminar usuario');
    }
    return data;
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

    const response = await fetch(url, { headers: authHeaders() });
    if (!response.ok) throw new Error('Error al obtener clientes');
    return response.json();
  },

  getById: async (id) => {
    const response = await fetch(`${API_URL}/api/clients/${id}`, { headers: authHeaders() });
    if (!response.ok) throw new Error('Cliente no encontrado');
    return response.json();
  },

  // Asigna los clientes antiguos (sin dueño) a un usuario. Solo admin/dirección.
  backfillOwner: async (username = 'MARIO') => {
    const response = await fetch(`${API_URL}/api/clients/backfill-owner`, {
      method: 'POST',
      headers: authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({ username }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Error en la reasignación');
    return data;
  },

  create: async (client) => {
    const response = await fetch(`${API_URL}/api/clients`, {
      method: 'POST',
      headers: authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(client)
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al crear cliente');
    }
    return data;
  },

  update: async (id, client) => {
    const response = await fetch(`${API_URL}/api/clients/${id}`, {
      method: 'PUT',
      headers: authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(client)
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al actualizar cliente');
    }
    return data;
  },

  delete: async (id, force = false) => {
    const url = force 
      ? `${API_URL}/api/clients/${id}?force=true`
      : `${API_URL}/api/clients/${id}`;
    
    // Use XMLHttpRequest for more reliable body handling
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open('DELETE', url, true);
      const _auth = authHeaders();
      if (_auth['Authorization']) xhr.setRequestHeader('Authorization', _auth['Authorization']);

      xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
          try {
            const data = xhr.responseText ? JSON.parse(xhr.responseText) : {};
            if (xhr.status >= 200 && xhr.status < 300) {
              resolve(data.message ? data : { message: 'Cliente eliminado' });
            } else {
              reject(new Error(data.detail || 'Error al eliminar cliente'));
            }
          } catch (e) {
            if (xhr.status >= 200 && xhr.status < 300) {
              resolve({ message: 'Cliente eliminado' });
            } else {
              reject(new Error('Error al eliminar cliente'));
            }
          }
        }
      };
      
      xhr.onerror = function() {
        reject(new Error('Error de conexión al eliminar cliente'));
      };
      
      xhr.send();
    });
  },

  importCSV: async (clients) => {
    const response = await fetch(`${API_URL}/api/clients/import-csv`, {
      method: 'POST',
      headers: authHeaders({ 'Content-Type': 'application/json' }),
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
      headers: authHeaders({ 'Content-Type': 'application/json' })
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al convertir contacto');
    }
    return data;
  },

  activate: async (id, codigo) => {
    const response = await fetch(`${API_URL}/api/clients/${id}/activate`, {
      method: 'POST',
      headers: authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({ codigo })
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al activar cliente');
    }
    return data;
  },

  linkUser: async (id, userId) => {
    const response = await fetch(`${API_URL}/api/clients/${id}/link-user`, {
      method: 'POST',
      headers: authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({ userId })
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al vincular usuario');
    }
    return data;
  }
};

// ============================================
// SHOP CLIENTS (Clientes de Tiendas/Distribuidores)
// ============================================

export const shopClientsAPI = {
  getAll: async (userId = null, search = null, status = null) => {
    const params = new URLSearchParams();
    if (userId) params.append('user_id', userId);
    if (search) params.append('search', search);
    if (status) params.append('status', status);
    
    const url = params.toString()
      ? `${API_URL}/api/shop-clients?${params.toString()}`
      : `${API_URL}/api/shop-clients`;
    
    const response = await fetch(url);
    if (!response.ok) throw new Error('Error al obtener clientes de tienda');
    return response.json();
  },

  getByOwner: async (ownerUserId, search = null) => {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    
    const url = params.toString()
      ? `${API_URL}/api/shop-clients/by-owner/${ownerUserId}?${params.toString()}`
      : `${API_URL}/api/shop-clients/by-owner/${ownerUserId}`;
    
    const response = await fetch(url);
    if (!response.ok) throw new Error('Error al obtener clientes de tienda');
    return response.json();
  },

  getStats: async (userId = null) => {
    const params = new URLSearchParams();
    if (userId) params.append('user_id', userId);
    
    const url = params.toString()
      ? `${API_URL}/api/shop-clients/stats?${params.toString()}`
      : `${API_URL}/api/shop-clients/stats`;
    
    const response = await fetch(url);
    if (!response.ok) throw new Error('Error al obtener estadísticas');
    return response.json();
  },

  getById: async (id, userId = null) => {
    const params = new URLSearchParams();
    if (userId) params.append('user_id', userId);
    
    const url = params.toString()
      ? `${API_URL}/api/shop-clients/${id}?${params.toString()}`
      : `${API_URL}/api/shop-clients/${id}`;
    
    const response = await fetch(url);
    if (!response.ok) throw new Error('Cliente no encontrado');
    return response.json();
  },

  create: async (client, userId = null) => {
    const params = new URLSearchParams();
    if (userId) params.append('user_id', userId);
    
    const url = params.toString()
      ? `${API_URL}/api/shop-clients?${params.toString()}`
      : `${API_URL}/api/shop-clients`;
    
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(client)
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al crear cliente');
    }
    return data;
  },

  update: async (id, client, userId = null) => {
    const params = new URLSearchParams();
    if (userId) params.append('user_id', userId);
    
    const url = params.toString()
      ? `${API_URL}/api/shop-clients/${id}?${params.toString()}`
      : `${API_URL}/api/shop-clients/${id}`;
    
    const response = await fetch(url, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(client)
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al actualizar cliente');
    }
    return data;
  },

  delete: async (id, userId = null) => {
    const params = new URLSearchParams();
    if (userId) params.append('user_id', userId);
    
    const url = params.toString()
      ? `${API_URL}/api/shop-clients/${id}?${params.toString()}`
      : `${API_URL}/api/shop-clients/${id}`;
    
    const response = await fetch(url, { method: 'DELETE' });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al eliminar cliente');
    }
    return data;
  },

  import: async (clients, userId = null) => {
    const params = new URLSearchParams();
    if (userId) params.append('user_id', userId);
    
    const url = params.toString()
      ? `${API_URL}/api/shop-clients/import?${params.toString()}`
      : `${API_URL}/api/shop-clients/import`;
    
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ clients })
    });
    if (!response.ok) throw new Error('Error al importar clientes');
    return response.json();
  }
};

// ============================================
// PRODUCTS
// ============================================

export const productsAPI = {
  getAll: async (module = null, library = null) => {
    const params = new URLSearchParams();
    if (module) params.append('module', module);
    if (library) params.append('library', library);
    const url = params.toString() 
      ? `${API_URL}/api/products?${params.toString()}`
      : `${API_URL}/api/products`;
    const response = await fetch(url);
    if (!response.ok) throw new Error('Error al obtener productos');
    return response.json();
  },

  getByLibrary: async (libraryCode, options = {}) => {
    const { module, category, programa, series, search, limit = 500 } = options;
    const params = new URLSearchParams();
    if (module) params.append('module', module);
    if (category) params.append('category', category);
    if (programa) params.append('programa', programa);
    if (series) params.append('series', series);
    if (search) params.append('search', search);
    params.append('limit', limit);
    
    const response = await fetch(`${API_URL}/api/libraries/${libraryCode}/products?${params.toString()}`);
    if (!response.ok) throw new Error('Error al obtener productos de biblioteca');
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
      headers: authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(product)
    });
    if (!response.ok) throw new Error('Error al crear producto');
    return response.json();
  },

  createBulk: async (products) => {
    const response = await fetch(`${API_URL}/api/products/bulk`, {
      method: 'POST',
      headers: authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(products)
    });
    if (!response.ok) throw new Error('Error al crear productos');
    return response.json();
  },

  // Alias for backwards compatibility
  bulkCreate: async (products) => {
    const response = await fetch(`${API_URL}/api/products/bulk`, {
      method: 'POST',
      headers: authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(products)
    });
    
    // Usar arrayBuffer para lectura robusta
    let responseText;
    try {
      const buffer = await response.arrayBuffer();
      responseText = new TextDecoder().decode(buffer);
    } catch (readErr) {
      throw new Error('Error de conexión con el servidor');
    }
    
    if (!response.ok) {
      let errorMsg = 'Error al crear productos';
      try {
        const errorData = JSON.parse(responseText);
        errorMsg = errorData.detail || errorData.error || errorMsg;
      } catch (e) {
        errorMsg = responseText.substring(0, 200) || errorMsg;
      }
      throw new Error(errorMsg);
    }
    try {
      return JSON.parse(responseText);
    } catch (e) {
      throw new Error('Respuesta inválida del servidor');
    }
  },

  // Upsert de productos (crear o actualizar zonePoints por tarifa)
  bulkUpsert: async (products, tariff = 'T1', library = 'MV') => {
    const response = await fetch(`${API_URL}/api/products/bulk-upsert`, {
      method: 'POST',
      headers: authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({ products, tariff, library })
    });
    
    // Usar arrayBuffer para lectura robusta
    let responseText;
    try {
      const buffer = await response.arrayBuffer();
      responseText = new TextDecoder().decode(buffer);
    } catch (readErr) {
      throw new Error('Error de conexión con el servidor');
    }
    
    if (!response.ok) {
      let errorMsg = 'Error al actualizar productos';
      try {
        const errorData = JSON.parse(responseText);
        errorMsg = errorData.detail || errorData.error || errorMsg;
      } catch (e) {
        errorMsg = responseText.substring(0, 200) || errorMsg;
      }
      throw new Error(errorMsg);
    }
    try {
      return JSON.parse(responseText);
    } catch (e) {
      throw new Error('Respuesta inválida del servidor');
    }
  },

  update: async (id, product) => {
    const response = await fetch(`${API_URL}/api/products/${id}`, {
      method: 'PUT',
      headers: authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(product)
    });
    if (!response.ok) throw new Error('Error al actualizar producto');
    return response.json();
  },

  delete: async (id) => {
    const response = await fetch(`${API_URL}/api/products/${id}`, {
      method: 'DELETE',
      headers: authHeaders()
    });
    if (!response.ok) throw new Error('Error al eliminar producto');
    return response.json();
  },

  deleteBulk: async (ids) => {
    const response = await fetch(`${API_URL}/api/products/bulk/delete`, {
      method: 'DELETE',
      headers: authHeaders({ 'Content-Type': 'application/json' }),
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
  getAll: async (library = null) => {
    const params = new URLSearchParams();
    if (library) params.append('library', library);
    const url = params.toString() 
      ? `${API_URL}/api/materials?${params.toString()}`
      : `${API_URL}/api/materials`;
    const response = await fetch(url);
    if (!response.ok) throw new Error('Error al obtener materiales');
    return response.json();
  },

  getByLibrary: async (libraryCode) => {
    const response = await fetch(`${API_URL}/api/materials?library=${libraryCode}`);
    if (!response.ok) throw new Error('Error al obtener materiales');
    return response.json();
  },

  create: async (material) => {
    const response = await fetch(`${API_URL}/api/materials`, {
      method: 'POST',
      headers: authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(material)
    });
    if (!response.ok) throw new Error('Error al crear material');
    return response.json();
  },

  update: async (id, material) => {
    const response = await fetch(`${API_URL}/api/materials/${id}`, {
      method: 'PUT',
      headers: authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(material)
    });
    if (!response.ok) throw new Error('Error al actualizar material');
    return response.json();
  },

  delete: async (id) => {
    const response = await fetch(`${API_URL}/api/materials/${id}`, {
      method: 'DELETE',
      headers: authHeaders()
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al eliminar material');
    }
    return data;
  }
};

// ============================================
// SETTINGS
// ============================================

export const settingsAPI = {
  get: async () => {
    const response = await fetch(`${API_URL}/api/settings`, { headers: authHeaders() });
    if (!response.ok) throw new Error('Error al obtener configuración');
    return response.json();
  },

  update: async (settings) => {
    const response = await fetch(`${API_URL}/api/settings`, {
      method: 'PUT',
      headers: authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(settings)
    });
    if (!response.ok) {
      let detail = `HTTP ${response.status}`;
      try { const e = await response.json(); detail = e.detail ? (typeof e.detail === 'string' ? e.detail : JSON.stringify(e.detail)) : detail; } catch (_) {}
      throw new Error(detail);
    }
    return response.json();
  },

  // Logo POR USUARIO: el backend guarda el logo en la ficha del usuario si tiene
  // marca personalizada; si es admin sin marca propia, actualiza el global.
  updateLogo: async (logo) => {
    const response = await fetch(`${API_URL}/api/settings/logo`, {
      method: 'PUT',
      headers: authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({ logo })
    });
    if (!response.ok) {
      let detail = 'Error al actualizar el logo';
      try { const e = await response.json(); detail = e.detail || detail; } catch (_) {}
      throw new Error(detail);
    }
    return response.json();
  },

  // Logo efectivo del usuario actual (su logo propio o el global por defecto).
  getLogo: async () => {
    const response = await fetch(`${API_URL}/api/settings/logo`, { headers: authHeaders() });
    if (!response.ok) throw new Error('Error al obtener el logo');
    return response.json();
  },

  // Logo GLOBAL público para la pantalla de login (no requiere sesión).
  getPublicLogo: async () => {
    const response = await fetch(`${API_URL}/api/settings/public-logo`);
    if (!response.ok) throw new Error('Error al obtener el logo público');
    return response.json();
  },

  // Logo de marca Luiggi Floor para la pantalla de login (acceso directo, sin sesión).
  getPublicFloorLogo: async () => {
    const response = await fetch(`${API_URL}/api/floor/public-logo`);
    if (!response.ok) throw new Error('Error al obtener el logo de Floor');
    return response.json();
  }
};

// ============================================
// PROJECTS/BUDGETS
// ============================================

export const projectsAPI = {
  _headers: () => {
    const token = getToken();
    return {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    };
  },

  getAll: async (userId = null) => {
    const url = userId
      ? `${API_URL}/api/projects?user_id=${userId}`
      : `${API_URL}/api/projects`;
    const response = await fetch(url, { headers: projectsAPI._headers() });
    if (!response.ok) throw new Error('Error al obtener proyectos');
    return response.json();
  },

  getById: async (id) => {
    const response = await fetch(`${API_URL}/api/projects/${id}`, { headers: projectsAPI._headers() });
    if (!response.ok) throw new Error('Proyecto no encontrado');
    return response.json();
  },

  create: async (project, userId) => {
    const response = await fetch(`${API_URL}/api/projects?user_id=${userId}`, {
      method: 'POST',
      headers: projectsAPI._headers(),
      body: JSON.stringify(project)
    });
    if (!response.ok) throw new Error('Error al crear proyecto');
    return response.json();
  },

  update: async (id, project) => {
    const response = await fetch(`${API_URL}/api/projects/${id}`, {
      method: 'PUT',
      headers: projectsAPI._headers(),
      body: JSON.stringify(project)
    });
    if (!response.ok) throw new Error('Error al actualizar proyecto');
    return response.json();
  },

  delete: async (id) => {
    const response = await fetch(`${API_URL}/api/projects/${id}`, {
      method: 'DELETE',
      headers: projectsAPI._headers()
    });
    if (!response.ok) throw new Error('Error al eliminar proyecto');
    return response.json();
  },

  changeStatus: async (id, status, changedBy = 'usuario', note = '') => {
    const response = await fetch(`${API_URL}/api/projects/${id}/status`, {
      method: 'PATCH',
      headers: projectsAPI._headers(),
      body: JSON.stringify({ status, changedBy, note })
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || 'Error al cambiar estado');
    }
    return response.json();
  },

  clone: async (id, budgetNumber, userId) => {
    const response = await fetch(`${API_URL}/api/projects/${id}/clone?user_id=${userId}`, {
      method: 'POST',
      headers: projectsAPI._headers(),
      body: JSON.stringify({ budgetNumber })
    });
    if (!response.ok) throw new Error('Error al duplicar proyecto');
    return response.json();
  },

  getStatusHistory: async (id) => {
    const response = await fetch(`${API_URL}/api/projects/${id}/status-history`, {
      headers: projectsAPI._headers()
    });
    if (!response.ok) throw new Error('Error al obtener historial');
    return response.json();
  }
};


// ============================================
// EXPEDIENTE ÚNICO DE LA OBRA
// ============================================
//
// El backend YA decide qué se manda: a quien no puede ver importes no se le
// envía la clave `importes` (no va a cero: no va). Aquí no se enmascara nada
// ni se rellenan huecos — si un dato no viene, es que no tiene que venir.

const _errorDe = async (r, porDefecto) => {
  const e = await r.json().catch(() => ({}));
  return new Error(e.detail || porDefecto);
};

// Una obra puede venir de Cocina Montada (un proyecto) o de Cocina Desmontada
// (un pedido de cascos). El expediente es EL MISMO; lo único que cambia es de
// dónde salen los datos, así que lo único que cambia aquí es la ruta.
const _baseDeObra = (origen, id) => (origen === 'casco'
  ? `${API_URL}/api/cascos/orders/${encodeURIComponent(id)}`
  : `${API_URL}/api/projects/${encodeURIComponent(id)}`);

export const expedienteAPI = {
  _h: () => {
    const token = getToken();
    return { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };
  },

  get: async (projectId, origen = 'proj') => {
    const r = await fetch(`${_baseDeObra(origen, projectId)}/expediente`, { headers: expedienteAPI._h() });
    if (!r.ok) throw await _errorDe(r, 'No se pudo abrir el expediente');
    return r.json();
  },

  validacion: async (projectId) => {
    const r = await fetch(`${API_URL}/api/projects/${projectId}/validacion`, { headers: expedienteAPI._h() });
    if (!r.ok) throw await _errorDe(r, 'No se pudo comprobar el proyecto');
    return r.json();
  },

  compararFabricacion: async (projectId) => {
    const r = await fetch(`${API_URL}/api/projects/${projectId}/comparar-fabricacion`, { headers: expedienteAPI._h() });
    if (!r.ok) throw await _errorDe(r, 'No se pudo comparar con fabricación');
    return r.json();
  },

  aprobarCambio: async (projectId, indice) => {
    const r = await fetch(`${API_URL}/api/projects/${projectId}/cambios/${indice}/aprobar`, {
      method: 'POST', headers: expedienteAPI._h()
    });
    if (!r.ok) throw await _errorDe(r, 'No se pudo aprobar el cambio');
    return r.json();
  },
};


// ============================================
// MEDICIÓN EN OBRA: LOS TRES NIVELES DE UNA MEDIDA
// ============================================
//
// Introducida (la de la venta), tomada (la del metro en la obra) y confirmada
// (la que se da por buena para fabricar). Subir de nivel es un ACTO y tiene su
// propia llamada, con su autor y su fecha: guardar la lista NO confirma nada.
// Si guardar pudiera confirmar de paso, confirmar dejaría de significar algo.

export const medidasAPI = {
  _h: () => {
    const token = getToken();
    return { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };
  },

  listar: async (projectId, origen = 'proj') => {
    const r = await fetch(`${_baseDeObra(origen, projectId)}/medidas`, { headers: medidasAPI._h() });
    if (!r.ok) throw await _errorDe(r, 'No se pudieron leer las medidas');
    return r.json();
  },

  guardar: async (projectId, medidas, origen = 'proj') => {
    const r = await fetch(`${_baseDeObra(origen, projectId)}/medidas`, {
      method: 'PUT', headers: medidasAPI._h(), body: JSON.stringify({ medidas })
    });
    if (!r.ok) throw await _errorDe(r, 'No se pudieron guardar las medidas');
    return r.json();
  },

  tomar: async (projectId, clave, valor, origen = 'proj') => {
    const r = await fetch(`${_baseDeObra(origen, projectId)}/medidas/${encodeURIComponent(clave)}/tomar`, {
      method: 'POST', headers: medidasAPI._h(), body: JSON.stringify({ valor })
    });
    if (!r.ok) throw await _errorDe(r, 'No se pudo apuntar la medida');
    return r.json();
  },

  confirmar: async (projectId, clave, valor, origen = 'proj') => {
    const r = await fetch(`${_baseDeObra(origen, projectId)}/medidas/${encodeURIComponent(clave)}/confirmar`, {
      method: 'POST', headers: medidasAPI._h(), body: JSON.stringify({ valor })
    });
    if (!r.ok) throw await _errorDe(r, 'No se pudo confirmar la medida');
    return r.json();
  },
};


// ============================================
// PROYECTOS DE COCINA DESMONTADA (proformas)
// ============================================
//
// Cocina Desmontada guarda sus proyectos en su propia colección, aparte de los
// de Cocina Montada 1 y 2. Se leen desde aquí para que el almacén pueda pedir
// material de los TRES presupuestadores y no solo de dos.

export const proformaAPI = {
  _h: () => {
    const token = getToken();
    return { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };
  },

  listar: async () => {
    const r = await fetch(`${API_URL}/api/cascos/proforma/proyectos`, { headers: proformaAPI._h() });
    if (!r.ok) throw await _errorDe(r, 'No se pudieron leer los proyectos de Cocina Desmontada');
    return r.json();
  },

  get: async (id) => {
    const r = await fetch(`${API_URL}/api/cascos/proforma/proyectos/${encodeURIComponent(id)}`, { headers: proformaAPI._h() });
    if (!r.ok) throw await _errorDe(r, 'No se pudo abrir el proyecto de Cocina Desmontada');
    return r.json();
  },

  // Los presupuestos y pedidos de casco: es lo que de verdad se teclea en la
  // pantalla de Cocina Desmontada, y vive en otra colección distinta de las
  // proformas de Alvic.
  listarPedidos: async (userId) => {
    const q = userId ? `?userId=${encodeURIComponent(userId)}` : '';
    const r = await fetch(`${API_URL}/api/cascos/orders${q}`, { headers: proformaAPI._h() });
    if (!r.ok) throw await _errorDe(r, 'No se pudieron leer los pedidos de Cocina Desmontada');
    return r.json();
  },
};


// ============================================
// ALMACÉN: EXISTENCIAS, RESERVAS Y PLAN DE COMPRA
// ============================================
//
// El cálculo está en el servidor (`services/almacen.py` y `almacen_datos.py`),
// probado y sin base de datos. Aquí no se calcula nada: lo que no venga en la
// respuesta NO se rellena — y en particular un stock desconocido llega como
// `null` y tiene que seguir siendo `null`, que no es lo mismo que cero.

export const almacenAPI = {
  _h: () => {
    const token = getToken();
    return { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };
  },

  listarStock: async () => {
    const r = await fetch(`${API_URL}/api/almacen/stock`, { headers: almacenAPI._h() });
    if (!r.ok) throw await _errorDe(r, 'No se pudieron leer las existencias');
    return r.json();
  },

  guardarStock: async (referencia, ficha) => {
    const r = await fetch(`${API_URL}/api/almacen/stock/${encodeURIComponent(referencia)}`, {
      method: 'PUT', headers: almacenAPI._h(), body: JSON.stringify(ficha)
    });
    if (!r.ok) throw await _errorDe(r, 'No se pudo guardar la ficha');
    return r.json();
  },

  borrarStock: async (referencia) => {
    const r = await fetch(`${API_URL}/api/almacen/stock/${encodeURIComponent(referencia)}`, {
      method: 'DELETE', headers: almacenAPI._h()
    });
    if (!r.ok) throw await _errorDe(r, 'No se pudo borrar la ficha');
    return r.json();
  },

  listarReservas: async (proyecto = null) => {
    const q = proyecto ? `?proyecto=${encodeURIComponent(proyecto)}` : '';
    const r = await fetch(`${API_URL}/api/almacen/reservas${q}`, { headers: almacenAPI._h() });
    if (!r.ok) throw await _errorDe(r, 'No se pudieron leer las reservas');
    return r.json();
  },

  crearReserva: async (reserva) => {
    const r = await fetch(`${API_URL}/api/almacen/reservas`, {
      method: 'POST', headers: almacenAPI._h(), body: JSON.stringify(reserva)
    });
    if (!r.ok) throw await _errorDe(r, 'No se pudo apartar el material');
    return r.json();
  },

  borrarReserva: async (referencia, proyecto) => {
    const r = await fetch(
      `${API_URL}/api/almacen/reservas?referencia=${encodeURIComponent(referencia)}&proyecto=${encodeURIComponent(proyecto)}`,
      { method: 'DELETE', headers: almacenAPI._h() });
    if (!r.ok) throw await _errorDe(r, 'No se pudo soltar la reserva');
    return r.json();
  },

  plan: async (proyecto, lineas, pedidos = null) => {
    const r = await fetch(`${API_URL}/api/almacen/plan`, {
      method: 'POST', headers: almacenAPI._h(),
      body: JSON.stringify({ proyecto, lineas, pedidos })
    });
    if (!r.ok) throw await _errorDe(r, 'No se pudo calcular el plan de compra');
    return r.json();
  },
};


// ============================================
// INVOICES (FACTURACIÓN)
// ============================================

export const invoicesAPI = {
  _h: () => {
    const token = getToken();
    return { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };
  },
  getAll: async (status = null, search = null) => {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (search) params.append('search', search);
    const r = await fetch(`${API_URL}/api/invoices?${params}`, { headers: invoicesAPI._h() });
    if (!r.ok) throw new Error('Error al obtener facturas');
    return r.json();
  },
  getStats: async () => {
    const r = await fetch(`${API_URL}/api/invoices/stats`, { headers: invoicesAPI._h() });
    if (!r.ok) throw new Error('Error al obtener estadísticas');
    return r.json();
  },
  getNextNumber: async () => {
    const r = await fetch(`${API_URL}/api/invoices/next-number`, { headers: invoicesAPI._h() });
    if (!r.ok) throw new Error('Error');
    return r.json();
  },
  get: async (id) => {
    const r = await fetch(`${API_URL}/api/invoices/${id}`, { headers: invoicesAPI._h() });
    if (!r.ok) throw new Error('Factura no encontrada');
    return r.json();
  },
  create: async (invoice) => {
    const r = await fetch(`${API_URL}/api/invoices`, { method: 'POST', headers: invoicesAPI._h(), body: JSON.stringify(invoice) });
    if (!r.ok) { const e = await r.json().catch(()=>({})); throw new Error(e.detail || 'Error al crear factura'); }
    return r.json();
  },
  createFromProject: async (projectId) => {
    const r = await fetch(`${API_URL}/api/invoices/from-project/${projectId}`, { method: 'POST', headers: invoicesAPI._h() });
    if (!r.ok) { const e = await r.json().catch(()=>({})); throw new Error(e.detail || 'Error al crear factura'); }
    return r.json();
  },
  update: async (id, data) => {
    const r = await fetch(`${API_URL}/api/invoices/${id}`, { method: 'PUT', headers: invoicesAPI._h(), body: JSON.stringify(data) });
    if (!r.ok) throw new Error('Error al actualizar factura');
    return r.json();
  },
  changeStatus: async (id, status, paidAt = null) => {
    const r = await fetch(`${API_URL}/api/invoices/${id}/status`, { method: 'PATCH', headers: invoicesAPI._h(), body: JSON.stringify({ status, paidAt }) });
    if (!r.ok) throw new Error('Error al cambiar estado');
    return r.json();
  },
  delete: async (id) => {
    const r = await fetch(`${API_URL}/api/invoices/${id}`, { method: 'DELETE', headers: invoicesAPI._h() });
    if (!r.ok) throw new Error('Error al eliminar factura');
    return r.json();
  },
  downloadPdf: (id) => {
    const token = getToken() || '';
    window.open(`${API_URL}/api/invoices/${id}/pdf`, '_blank');
  },
  sendEmail: async (id, email = null) => {
    const r = await fetch(`${API_URL}/api/invoices/${id}/send-email`, { method: 'POST', headers: invoicesAPI._h(), body: JSON.stringify({ email }) });
    if (!r.ok) { const e = await r.json().catch(()=>({})); throw new Error(e.detail || 'Error al enviar email'); }
    return r.json();
  },
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
  // Descarga la copia COMPLETA de la base de datos en UNA sola petición: el ZIP
  // se genera y se entrega en la misma llamada, así la copia aterriza en tu
  // equipo y no depende del disco del contenedor (que es efímero y se borra al
  // redesplegar). Devuelve el nombre del fichero descargado.
  descargarAhora: async () => {
    const response = await fetch(`${API_URL}/api/backup/descargar-ahora`, { headers: authHeaders() });
    if (!response.ok) {
      let motivo = `Error ${response.status}`;
      try { const d = await response.json(); motivo = d.detail || d.error || motivo; } catch { /* noop */ }
      throw new Error(motivo);
    }
    const cols = response.headers.get('X-Backup-Colecciones');
    const docs = response.headers.get('X-Backup-Documentos');
    const blob = await response.blob();
    const cd = response.headers.get('Content-Disposition') || '';
    const m = cd.match(/filename="([^"]+)"/);
    const nombre = (m && m[1]) || `luiggi_bd_completa_${new Date().toISOString().slice(0, 10)}.zip`;
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = nombre;
    document.body.appendChild(a); a.click(); a.remove();
    window.URL.revokeObjectURL(url);
    return { nombre, colecciones: cols, documentos: docs, tamanoMB: (blob.size / (1024 * 1024)).toFixed(1) };
  },

  // Google Drive: estado de la integración (no expone secretos).
  driveEstado: async () => {
    const r = await fetch(`${API_URL}/api/backup/drive/estado`, { headers: authHeaders() });
    if (!r.ok) throw new Error('No se pudo consultar el estado de Google Drive');
    return r.json();
  },

  // Genera una copia y la sube a Drive en el momento.
  driveSubirAhora: async () => {
    const r = await fetch(`${API_URL}/api/backup/drive/subir-ahora`, { method: 'POST', headers: authHeaders() });
    let d = null; try { d = await r.json(); } catch { d = null; }
    if (!r.ok) throw new Error((d && (d.detail || d.error)) || `Error ${r.status}`);
    return d;
  },

  getStatus: async () => {
    const response = await fetch(`${API_URL}/api/backup/status`);
    if (!response.ok) throw new Error('Error al obtener estado de backup');
    return response.json();
  },

  triggerManual: async () => {
    // Genera el backup COMPLETO (JSON de todas las colecciones) y lo envia por
    // email a marioluiggihome@gmail.com. Endpoint real: /api/backup/send-email.
    const response = await fetch(`${API_URL}/api/backup/send-email`, {
      method: 'POST', headers: authHeaders()
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok || data.success === false) {
      throw new Error(data.error || data.detail || 'Error al crear/enviar backup');
    }
    return data;
  },

  // Descargar el JSON de toda la BD (requiere admin).
  download: async () => {
    const response = await fetch(`${API_URL}/api/backup/export-db-only`, { headers: authHeaders() });
    if (!response.ok) throw new Error('Error al descargar backup (requiere admin)');
    return response.blob();
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
  _h: () => {
    const token = getToken();
    return { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) };
  },

  getAll: async (status = null, search = null, options = {}) => {
    let url = `${API_URL}/api/crm/contacts`;
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (search) params.append('search', search);
    if (options.assignedTo) params.append('assignedTo', options.assignedTo);
    if (options.isAdmin !== undefined) params.append('isAdmin', options.isAdmin);
    if (params.toString()) url += `?${params.toString()}`;
    
    const response = await fetch(url, { headers: crmContactsAPI._h() });
    if (!response.ok) throw new Error('Error al obtener contactos');
    return response.json();
  },

  getById: async (id) => {
    const response = await fetch(`${API_URL}/api/crm/contacts/${id}`, { headers: authHeaders() });
    if (!response.ok) throw new Error('Contacto no encontrado');
    return response.json();
  },

  create: async (contact) => {
    const response = await fetch(`${API_URL}/api/crm/contacts`, {
      method: 'POST',
      headers: crmContactsAPI._h(),
      body: JSON.stringify(contact)
    });
    if (!response.ok) throw new Error('Error al crear contacto');
    return response.json();
  },

  update: async (id, contact) => {
    const response = await fetch(`${API_URL}/api/crm/contacts/${id}`, {
      method: 'PUT',
      headers: crmContactsAPI._h(),
      body: JSON.stringify(contact)
    });
    if (!response.ok) throw new Error('Error al actualizar contacto');
    return response.json();
  },

  delete: async (id) => {
    const response = await fetch(`${API_URL}/api/crm/contacts/${id}`, {
      method: 'DELETE',
      headers: crmContactsAPI._h()
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

    const response = await fetch(url, { headers: authHeaders() });
    if (!response.ok) throw new Error('Error al obtener oportunidades');
    return response.json();
  },

  getById: async (id) => {
    const response = await fetch(`${API_URL}/api/crm/opportunities/${id}`, { headers: authHeaders() });
    if (!response.ok) throw new Error('Oportunidad no encontrada');
    return response.json();
  },

  create: async (opportunity) => {
    const response = await fetch(`${API_URL}/api/crm/opportunities`, {
      method: 'POST',
      headers: authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(opportunity)
    });
    if (!response.ok) throw new Error('Error al crear oportunidad');
    return response.json();
  },

  createFromProject: async (projectId, businessType = 'cocina') => {
    const response = await fetch(`${API_URL}/api/crm/opportunities/from-project/${projectId}?businessType=${businessType}`, {
      method: 'POST',
      headers: authHeaders()
    });
    if (!response.ok) throw new Error('Error al crear oportunidad desde proyecto');
    return response.json();
  },

  createFromArmario: async (projectId) => {
    const response = await fetch(`${API_URL}/api/crm/opportunities/from-armario/${projectId}`, {
      method: 'POST',
      headers: authHeaders()
    });
    if (!response.ok) throw new Error('Error al crear oportunidad desde armario');
    return response.json();
  },

  update: async (id, opportunity) => {
    const response = await fetch(`${API_URL}/api/crm/opportunities/${id}`, {
      method: 'PUT',
      headers: authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(opportunity)
    });
    if (!response.ok) throw new Error('Error al actualizar oportunidad');
    return response.json();
  },

  delete: async (id) => {
    const response = await fetch(`${API_URL}/api/crm/opportunities/${id}`, {
      method: 'DELETE',
      headers: authHeaders()
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
      headers: authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(activity)
    });
    if (!response.ok) throw new Error('Error al crear actividad');
    return response.json();
  },

  update: async (id, activity) => {
    const response = await fetch(`${API_URL}/api/crm/activities/${id}`, {
      method: 'PUT',
      headers: authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(activity)
    });
    if (!response.ok) throw new Error('Error al actualizar actividad');
    return response.json();
  },

  delete: async (id) => {
    const response = await fetch(`${API_URL}/api/crm/activities/${id}`, {
      method: 'DELETE',
      headers: authHeaders()
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

    const response = await fetch(url, { headers: authHeaders() });
    if (!response.ok) throw new Error('Error al obtener dashboard CRM');
    return response.json();
  }
};

// ============================================
// CRM - ANALYTICS (Clientes Inactivos)
// ============================================

export const crmAnalyticsAPI = {
  getInactiveClients: async (daysWithoutOffer = 30, daysWithoutPurchase = 60) => {
    const response = await fetch(`${API_URL}/api/crm/analytics/inactive-clients?days_without_offer=${daysWithoutOffer}&days_without_purchase=${daysWithoutPurchase}`, { headers: authHeaders() });
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
    // El backend espera 'start'/'end' (no startDate/endDate)
    if (params.startDate) queryParams.append('start', params.startDate);
    if (params.endDate) queryParams.append('end', params.endDate);
    if (params.eventType) queryParams.append('eventType', params.eventType);
    if (params.viewAll) queryParams.append('viewAll', 'true');
    if (params.commercialId) queryParams.append('commercialId', params.commercialId);

    const response = await fetch(`${API_URL}/api/crm/calendar/events?${queryParams.toString()}`, { headers: authHeaders() });
    if (!response.ok) throw new Error('Error al obtener eventos');
    return response.json();
  },

  create: async (event, createdBy, createdByName) => {
    const response = await fetch(`${API_URL}/api/crm/calendar/events?createdBy=${createdBy}&createdByName=${encodeURIComponent(createdByName)}`, {
      method: 'POST',
      headers: authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(event)
    });
    if (!response.ok) throw new Error('Error al crear evento');
    return response.json();
  },

  update: async (eventId, updates) => {
    const response = await fetch(`${API_URL}/api/crm/calendar/events/${eventId}`, {
      method: 'PUT',
      headers: authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(updates)
    });
    if (!response.ok) throw new Error('Error al actualizar evento');
    return response.json();
  },

  delete: async (eventId) => {
    const response = await fetch(`${API_URL}/api/crm/calendar/events/${eventId}`, {
      method: 'DELETE',
      headers: authHeaders()
    });
    if (!response.ok) throw new Error('Error al eliminar evento');
    return response.json();
  },
  
  complete: async (eventId) => {
    const response = await fetch(`${API_URL}/api/crm/calendar/events/${eventId}/complete`, {
      method: 'PUT'
    });
    if (!response.ok) throw new Error('Error al completar evento');
    return response.json();
  }
};

// ============================================
// DESPIECE (BILL OF MATERIALS)
// ============================================

export const despieceAPI = {
  calculate: async (items, carcassMaterial = "Melamina Blanca", backPanelMaterial = "Tablero 8mm", grosor = 18, backThickness = 8, doorToleranceHeight = 2, doorToleranceWidth = 3) => {
    const response = await fetch(`${API_URL}/api/despiece/calculate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        items,
        carcassMaterial,
        backPanelMaterial,
        grosor,
        backThickness,
        doorToleranceHeight,
        doorToleranceWidth
      })
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al calcular despiece');
    }
    return data;
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
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al analizar imagen');
    }
    return data;
  },

  exportCSV: async (lines, materialCode = "40-ESTEITEX16", materialThickness = 16.0) => {
    const response = await fetch(`${API_URL}/api/digitalizador/export-csv`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lines, materialCode, materialThickness })
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al exportar CSV');
    }
    return data;
  }
};

// ============================================
// ARMARIOS - PROYECTOS
// ============================================

export const armariosAPI = {
  // ALZADO VECTORIAL ACOTADO (frente + interior + planta). Lo dibuja el
  // backend desde las medidas reales: el alzado que se dibujaba en el
  // navegador repartía el alto en filas iguales y rotulaba esas filas como si
  // fueran alturas medidas, así que la barra de colgar salía a 192 cm cuando
  // está a 122. Aquí las cotas salen de `services/armario_geometry.py`.
  alzado: async (config, moduleConfigs, opciones = {}) => {
    const response = await fetch(`${API_URL}/api/armarios/alzado`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ config, moduleConfigs, ...opciones })
    });
    const data = await response.json().catch(() => null);
    if (!response.ok) {
      // El 422 trae instrucciones («falta el ancho»): se propaga tal cual en
      // vez de un «error al generar» que no dice qué hay que tocar.
      throw new Error((data && (data.detail || data.error)) || 'No se pudo generar el alzado.');
    }
    return data;
  },

  // Crear proyecto (la propiedad la fija el backend con el token)
  create: async (project) => {
    const response = await fetch(`${API_URL}/api/armarios/projects`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify(project)
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al crear proyecto');
    }
    return data;
  },

  // Obtener lista de proyectos del usuario autenticado
  getAll: async () => {
    const response = await fetch(`${API_URL}/api/armarios/projects`, { headers: authHeaders() });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al obtener proyectos');
    }
    return data;
  },

  // Obtener un proyecto específico
  get: async (projectId) => {
    const response = await fetch(`${API_URL}/api/armarios/projects/${projectId}`, { headers: authHeaders() });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al obtener proyecto');
    }
    return data;
  },

  // Actualizar proyecto
  update: async (projectId, updates) => {
    const response = await fetch(`${API_URL}/api/armarios/projects/${projectId}`, {
      method: 'PUT',
      headers: authHeaders(),
      body: JSON.stringify(updates)
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al actualizar proyecto');
    }
    return data;
  },

  // Eliminar proyecto
  delete: async (projectId) => {
    const response = await fetch(`${API_URL}/api/armarios/projects/${projectId}`, {
      method: 'DELETE', headers: authHeaders()
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al eliminar proyecto');
    }
    return data;
  },

  // IA: Configurar módulos automáticamente
  iaConfiguracion: async (instruction, currentConfig = {}) => {
    const response = await fetch(`${API_URL}/api/armarios/ia/configure`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ instruction, current_config: currentConfig })
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al configurar con IA');
    }
    return data;
  },

  // IA: Generar render realista
  iaRender: async (config) => {
    const response = await fetch(`${API_URL}/api/armarios/ia/render`, {
      method: 'POST',
      headers: { ...authHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al generar render');
    }
    return data;
  }
};

// ============================================
// ADMIN METRICS
// ============================================

export const adminMetricsAPI = {
  get: async () => {
    const response = await fetch(`${API_URL}/api/admin/metrics`, { headers: authHeaders() });
    if (!response.ok) throw new Error('Error al obtener métricas');
    return response.json();
  },

  getTrends: async () => {
    const response = await fetch(`${API_URL}/api/admin/metrics/trends`, { headers: authHeaders() });
    if (!response.ok) throw new Error('Error al obtener tendencias');
    return response.json();
  }
};

// ============================================
// LIBRARIES (Multi-Library System)
// ============================================

export const librariesAPI = {
  getAll: async () => {
    const response = await fetch(`${API_URL}/api/libraries`);
    if (!response.ok) throw new Error('Error al obtener bibliotecas');
    return response.json();
  },

  getById: async (code) => {
    const response = await fetch(`${API_URL}/api/libraries/${code}`);
    if (!response.ok) throw new Error('Biblioteca no encontrada');
    return response.json();
  },

  getStats: async (code) => {
    const response = await fetch(`${API_URL}/api/libraries/${code}/stats`);
    if (!response.ok) throw new Error('Error al obtener estadísticas');
    return response.json();
  },

  getUserAccess: async (userId) => {
    const response = await fetch(`${API_URL}/api/libraries/users/${userId}/access`);
    if (!response.ok) throw new Error('Error al obtener acceso de usuario');
    return response.json();
  },

  updateUserAccess: async (userId, libraries) => {
    const response = await fetch(`${API_URL}/api/libraries/users/${userId}/access`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ userId, libraries })
    });
    if (!response.ok) throw new Error('Error al actualizar acceso');
    return response.json();
  },

  create: async (library) => {
    const response = await fetch(`${API_URL}/api/libraries`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(library)
    });
    if (!response.ok) throw new Error('Error al crear biblioteca');
    return response.json();
  },

  update: async (code, data) => {
    const response = await fetch(`${API_URL}/api/libraries/${code}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!response.ok) throw new Error('Error al actualizar biblioteca');
    return response.json();
  },

  delete: async (code) => {
    const response = await fetch(`${API_URL}/api/libraries/${code}`, {
      method: 'DELETE'
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al eliminar biblioteca');
    }
    return data;
  }
};

// ============================================
// MONTADORES (Instaladores) API
// ============================================

export const montadoresAPI = {
  getAll: async (status = null, userId = null) => {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (userId) params.append('user_id', userId);
    const url = params.toString()
      ? `${API_URL}/api/montadores?${params.toString()}`
      : `${API_URL}/api/montadores`;
    const response = await fetch(url, { headers: authHeaders() });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al obtener montadores');
    }
    return data;
  },

  getOne: async (id) => {
    const response = await fetch(`${API_URL}/api/montadores/${id}`, { headers: authHeaders() });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al obtener montador');
    }
    return data;
  },

  create: async (montador) => {
    const response = await fetch(`${API_URL}/api/montadores`, {
      method: 'POST',
      headers: authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(montador)
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al crear montador');
    }
    return data;
  },

  update: async (id, montador) => {
    const response = await fetch(`${API_URL}/api/montadores/${id}`, {
      method: 'PUT',
      headers: authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(montador)
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al actualizar montador');
    }
    return data;
  },

  delete: async (id) => {
    const response = await fetch(`${API_URL}/api/montadores/${id}`, {
      method: 'DELETE',
      headers: authHeaders()
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al eliminar montador');
    }
    return data;
  },

  getMontajes: async (montadorId, status = null) => {
    const url = status
      ? `${API_URL}/api/montadores/${montadorId}/montajes?status=${status}`
      : `${API_URL}/api/montadores/${montadorId}/montajes`;
    const response = await fetch(url, { headers: authHeaders() });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al obtener montajes');
    }
    return data;
  }
};

// ============================================
// MONTAJES (Instalaciones) API
// ============================================

export const montajesAPI = {
  getAll: async (filters = {}) => {
    const params = new URLSearchParams();
    if (filters.status) params.append('status', filters.status);
    if (filters.montadorId) params.append('montador_id', filters.montadorId);
    if (filters.startDate) params.append('start_date', filters.startDate);
    if (filters.endDate) params.append('end_date', filters.endDate);
    if (filters.userId) params.append('user_id', filters.userId);

    const url = params.toString()
      ? `${API_URL}/api/montajes?${params.toString()}`
      : `${API_URL}/api/montajes`;
    const response = await fetch(url, { headers: authHeaders() });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al obtener montajes');
    }
    return data;
  },

  getOne: async (id) => {
    const response = await fetch(`${API_URL}/api/montajes/${id}`, { headers: authHeaders() });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al obtener montaje');
    }
    return data;
  },

  create: async (montaje) => {
    const response = await fetch(`${API_URL}/api/montajes`, {
      method: 'POST',
      headers: authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(montaje)
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al crear montaje');
    }
    return data;
  },

  update: async (id, montaje) => {
    const response = await fetch(`${API_URL}/api/montajes/${id}`, {
      method: 'PUT',
      headers: authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(montaje)
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al actualizar montaje');
    }
    return data;
  },

  delete: async (id) => {
    const response = await fetch(`${API_URL}/api/montajes/${id}`, {
      method: 'DELETE',
      headers: authHeaders()
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al eliminar montaje');
    }
    return data;
  }
};

// ============================================
// FABRICA (Portal de Fábrica) API
// ============================================

export const fabricaAPI = {
  // Órdenes de fabricación
  getOrders: async (filters = {}) => {
    const params = new URLSearchParams();
    if (filters.status) params.append('status', filters.status);
    if (filters.priority) params.append('priority', filters.priority);
    if (filters.search) params.append('search', filters.search);
    if (filters.limit) params.append('limit', filters.limit);
    if (filters.skip) params.append('skip', filters.skip);
    
    const url = params.toString()
      ? `${API_URL}/api/fabrica/orders?${params.toString()}`
      : `${API_URL}/api/fabrica/orders`;
    const response = await fetch(url);
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al obtener órdenes');
    }
    return data;
  },

  getOrder: async (orderId) => {
    const response = await fetch(`${API_URL}/api/fabrica/orders/${orderId}`);
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al obtener orden');
    }
    return data;
  },

  createOrder: async (order, userId = '', userName = '') => {
    const params = new URLSearchParams();
    if (userId) params.append('userId', userId);
    if (userName) params.append('userName', userName);
    
    const url = params.toString()
      ? `${API_URL}/api/fabrica/orders?${params.toString()}`
      : `${API_URL}/api/fabrica/orders`;
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(order)
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al crear orden');
    }
    return data;
  },

  updateOrder: async (orderId, update) => {
    const response = await fetch(`${API_URL}/api/fabrica/orders/${orderId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(update)
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al actualizar orden');
    }
    return data;
  },

  deleteOrder: async (orderId) => {
    const response = await fetch(`${API_URL}/api/fabrica/orders/${orderId}`, {
      method: 'DELETE'
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al eliminar orden');
    }
    return data;
  },

  updateOrderStatus: async (orderId, status, notes = '') => {
    const params = new URLSearchParams({ status });
    if (notes) params.append('notes', notes);
    
    const response = await fetch(`${API_URL}/api/fabrica/orders/${orderId}/status?${params.toString()}`, {
      method: 'PATCH'
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al actualizar estado');
    }
    return data;
  },

  // Hoja de ruta de taller: marcar/desmarcar una fase de produccion de la orden.
  updateOrderPhase: async (orderId, phase, done = true) => {
    const params = new URLSearchParams({ phase, done: done ? 'true' : 'false' });
    const response = await fetch(`${API_URL}/api/fabrica/orders/${orderId}/phase?${params.toString()}`, {
      method: 'PATCH', headers: authHeaders()
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Error al actualizar fase');
    return data;
  },

  setDeliveryDate: async (orderId, estimatedDate, notes = '') => {
    const params = new URLSearchParams({ estimated_date: estimatedDate });
    if (notes) params.append('notes', notes);
    
    const response = await fetch(`${API_URL}/api/fabrica/orders/${orderId}/delivery-date?${params.toString()}`, {
      method: 'PATCH'
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al establecer fecha de entrega');
    }
    return data;
  },

  // Importación
  importPDF: async (pdfBase64, fileName) => {
    const response = await fetch(`${API_URL}/api/fabrica/import-pdf`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pdfBase64, fileName })
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al importar PDF');
    }
    return data;
  },

  importFromBudget: async (budgetId, userId = '', userName = '') => {
    const params = new URLSearchParams();
    if (userId) params.append('userId', userId);
    if (userName) params.append('userName', userName);
    
    const response = await fetch(`${API_URL}/api/fabrica/import-from-budget/${budgetId}?${params.toString()}`, {
      method: 'POST'
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al importar desde presupuesto');
    }
    return data;
  },

  // Dashboard y estadísticas
  getDashboardStats: async () => {
    const response = await fetch(`${API_URL}/api/fabrica/dashboard/stats`);
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al obtener estadísticas');
    }
    return data;
  },

  // Despiece de orden
  getOrderDespiece: async (orderId) => {
    const response = await fetch(`${API_URL}/api/fabrica/orders/${orderId}/despiece`);
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al obtener despiece');
    }
    return data;
  },

  // Descargar informe de producción PDF
  downloadProductionReport: async (orderId) => {
    const response = await fetch(`${API_URL}/api/fabrica/reports/production/${orderId}`);
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Error descargando informe' }));
      throw new Error(error.detail || 'Error al descargar informe de producción');
    }
    
    // Obtener el blob y descargarlo
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Informe_Produccion_${orderId}.pdf`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
    
    return { success: true };
  },

  // Descargar informe de producción desde presupuesto
  downloadProductionReportFromBudget: async (budgetId) => {
    const response = await fetch(`${API_URL}/api/fabrica/reports/production-from-budget/${budgetId}`);
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Error descargando informe' }));
      throw new Error(error.detail || 'Error al descargar informe de producción');
    }
    
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Informe_Produccion_${budgetId}.pdf`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
    
    return { success: true };
  }
};


// ============================================
// ORDERS API (Pedidos confirmados)
// ============================================

export const ordersAPI = {
  // Obtener pedidos del usuario autenticado (el backend filtra por el token).
  getOrders: async (userId = null, limit = 100) => {
    const params = new URLSearchParams();
    if (limit) params.append('limit', limit);
    const url = params.toString()
      ? `${API_URL}/api/orders?${params.toString()}`
      : `${API_URL}/api/orders`;
    const response = await fetch(url, { headers: authHeaders() });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al obtener pedidos');
    }
    return data;
  },

  // Obtener detalle de un pedido
  getOrder: async (orderId) => {
    const response = await fetch(`${API_URL}/api/orders/${orderId}`, { headers: authHeaders() });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al obtener pedido');
    }
    return data;
  },

  // Enviar copia de pedido con adjuntos
  sendCopy: async (orderId, recipientEmail, includeAttachments = true, additionalMessage = '') => {
    const response = await fetch(`${API_URL}/api/orders/${orderId}/send-copy`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({
        recipient_email: recipientEmail,
        include_attachments: includeAttachments,
        additional_message: additionalMessage
      })
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Error al enviar copia');
    }
    return data;
  }
};

// ============================================
// GOOGLE CALENDAR (integración OAuth por usuario)
// Cada usuario conecta su propia cuenta; el aislamiento lo garantiza el backend.
// ============================================
export const googleCalendarAPI = {
  // Estado: { configured, connected, email }
  status: async () => {
    const r = await fetch(`${API_URL}/api/google-calendar/status`, { headers: authHeaders() });
    return r.json();
  },
  // Obtiene la URL de consentimiento y redirige el navegador a Google.
  connect: async (returnPath = '/') => {
    const r = await fetch(
      `${API_URL}/api/google-calendar/connect?return_path=${encodeURIComponent(returnPath)}`,
      { headers: authHeaders() }
    );
    const data = await r.json();
    if (!r.ok || !data.url) throw new Error(data.detail || 'No se pudo iniciar la conexión con Google');
    window.location.href = data.url;
  },
  disconnect: async () => {
    const r = await fetch(`${API_URL}/api/google-calendar/disconnect`, {
      method: 'POST', headers: authHeaders(),
    });
    return r.json();
  },
  // Eventos del propio usuario en el rango (ISO 'YYYY-MM-DD' o datetime).
  getEvents: async (start, end) => {
    const qs = new URLSearchParams();
    if (start) qs.set('start', start);
    if (end) qs.set('end', end);
    const r = await fetch(`${API_URL}/api/google-calendar/events?${qs.toString()}`, { headers: authHeaders() });
    return r.json();
  },
  // Push ERP→Google. event: { title, startDate, endDate, description, location, allDay, module, erpId }
  createEvent: async (event) => {
    // Timeout para que el botón no se quede "pensativo" si Google tarda/cuelga.
    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), 25000);
    let r;
    try {
      r = await fetch(`${API_URL}/api/google-calendar/events`, {
        method: 'POST',
        headers: authHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify(event),
        signal: ctrl.signal,
      });
    } catch (e) {
      clearTimeout(t);
      throw new Error(e.name === 'AbortError' ? 'Google Calendar tardó demasiado en responder. Inténtalo de nuevo.' : 'No se pudo conectar con Google Calendar.');
    }
    clearTimeout(t);
    const data = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(data.detail || 'No se pudo guardar en Google Calendar');
    return data;
  },
  updateEvent: async (googleEventId, event) => {
    const r = await fetch(`${API_URL}/api/google-calendar/events/${googleEventId}`, {
      method: 'PUT',
      headers: authHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(event),
    });
    const data = await r.json();
    if (!r.ok) throw new Error(data.detail || 'No se pudo actualizar en Google Calendar');
    return data;
  },
  deleteEvent: async (googleEventId, module, erpId) => {
    const qs = new URLSearchParams();
    if (module) qs.set('module', module);
    if (erpId) qs.set('erpId', erpId);
    const r = await fetch(`${API_URL}/api/google-calendar/events/${googleEventId}?${qs.toString()}`, {
      method: 'DELETE', headers: authHeaders(),
    });
    return r.json();
  },
};
