/**
 * Ejemplo de refactorización de api.js usando utilidades centralizadas.
 * Reduce el código en ~60% y mejora la mantenibilidad.
 */

import {
  buildUrl,
  buildHeaders,
  fetchGet,
  fetchPost,
  fetchPut,
  fetchDelete,
  createCRUDAPI,
  withRetry,
  interceptResponse
} from './api_utils';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// ============================================
// AUTH API
// ============================================

export const authAPI = {
  login: async (username, password) => {
    const response = await fetchPost(`${API_URL}/api/auth/login`, {
      username,
      password
    });
    return interceptResponse(response);
  },

  init: async () => {
    const response = await fetchPost(`${API_URL}/api/init`);
    return interceptResponse(response);
  },

  refreshToken: async (refreshToken) => {
    const response = await fetchPost(`${API_URL}/api/auth/refresh`, {
      refresh_token: refreshToken
    });
    return interceptResponse(response);
  }
};

// ============================================
// EXPEDIENT API
// ============================================

export const expedientAPI = {
  getNext: async (clientCode = null) => {
    const url = buildUrl(`${API_URL}/api/expedient/next`, {
      client_code: clientCode
    });
    const response = await fetchGet(url);
    return interceptResponse(response);
  },

  getCurrent: async () => {
    const response = await fetchGet(`${API_URL}/api/expedient/current`);
    return interceptResponse(response);
  }
};

// ============================================
// USERS API (usando CRUD factory)
// ============================================

export const usersAPI = createCRUDAPI(`${API_URL}/api/users`);

// Extender con métodos personalizados
usersAPI.changePassword = async (userId, oldPassword, newPassword) => {
  const response = await fetchPost(
    `${API_URL}/api/users/${userId}/change-password`,
    { oldPassword, newPassword }
  );
  return interceptResponse(response);
};

// ============================================
// CLIENTS API (usando CRUD factory)
// ============================================

export const clientsAPI = {
  ...createCRUDAPI(`${API_URL}/api/clients`),

  // Métodos adicionales
  getAll: async (activo = null, search = null) => {
    const url = buildUrl(`${API_URL}/api/clients`, {
      activo: activo !== null ? activo : undefined,
      search: search || undefined
    });
    const response = await fetchGet(url);
    return interceptResponse(response);
  },

  backfillOwner: async (username = 'MARIO') => {
    const response = await fetchPost(
      `${API_URL}/api/clients/backfill-owner`,
      { username }
    );
    return interceptResponse(response);
  },

  importCSV: async (clients) => {
    const response = await fetchPost(
      `${API_URL}/api/clients/import-csv`,
      { clients }
    );
    return interceptResponse(response);
  },

  getSegments: async () => {
    const response = await fetchGet(`${API_URL}/api/clients/segments`);
    return interceptResponse(response);
  },

  createFromContact: async (contactId) => {
    const response = await fetchPost(
      `${API_URL}/api/clients/from-contact/${contactId}`
    );
    return interceptResponse(response);
  },

  activate: async (id, codigo) => {
    const response = await fetchPost(
      `${API_URL}/api/clients/${id}/activate`,
      { codigo }
    );
    return interceptResponse(response);
  },

  linkUser: async (id, userId) => {
    const response = await fetchPost(
      `${API_URL}/api/clients/${id}/link-user`,
      { userId }
    );
    return interceptResponse(response);
  }
};

// ============================================
// PRODUCTS API
// ============================================

export const productsAPI = {
  getAll: async (module = null, library = null) => {
    const url = buildUrl(`${API_URL}/api/products`, {
      module: module || undefined,
      library: library || undefined
    });
    const response = await fetchGet(url);
    return interceptResponse(response);
  },

  getByLibrary: async (libraryCode, options = {}) => {
    const { module, category, programa, series, search, limit = 500 } = options;
    const url = buildUrl(`${API_URL}/api/products/library/${libraryCode}`, {
      module: module || undefined,
      category: category || undefined,
      programa: programa || undefined,
      series: series || undefined,
      search: search || undefined,
      limit
    });
    const response = await fetchGet(url);
    return interceptResponse(response);
  },

  search: async (query, options = {}) => {
    const url = buildUrl(`${API_URL}/api/products/search`, {
      q: query,
      limit: options.limit || 50,
      offset: options.offset || 0
    });
    const response = await fetchGet(url);
    return interceptResponse(response);
  }
};

// ============================================
// ORDERS API
// ============================================

export const ordersAPI = {
  getAll: async (filters = {}) => {
    const url = buildUrl(`${API_URL}/api/orders`, filters);
    const response = await fetchGet(url);
    return interceptResponse(response);
  },

  getById: async (id) => {
    const response = await fetchGet(`${API_URL}/api/orders/${id}`);
    return interceptResponse(response);
  },

  confirm: async (orderData, attachments = []) => {
    // Usar FormData para soportar archivos
    const formData = new FormData();
    
    // Añadir datos del pedido como JSON
    formData.append('order_data', JSON.stringify(orderData));
    
    // Añadir archivos adjuntos
    attachments.forEach((file, index) => {
      if (file) {
        formData.append(`attachment_${index}`, file);
      }
    });
    
    const response = await fetch(`${API_URL}/api/orders/confirm`, {
      method: 'POST',
      headers: buildHeaders(),
      body: formData
    });

    if (!response.ok) {
      throw new Error(await response.text());
    }

    return interceptResponse(await response.json());
  },

  update: async (id, data) => {
    const response = await fetchPut(`${API_URL}/api/orders/${id}`, data);
    return interceptResponse(response);
  },

  delete: async (id) => {
    const response = await fetchDelete(`${API_URL}/api/orders/${id}`);
    return interceptResponse(response);
  },

  getManufacturingOrders: async (filters = {}) => {
    const url = buildUrl(`${API_URL}/api/orders/manufacturing`, filters);
    const response = await fetchGet(url);
    return interceptResponse(response);
  }
};

// ============================================
// BUDGETS API
// ============================================

export const budgetsAPI = {
  ...createCRUDAPI(`${API_URL}/api/budgets`),

  getByClient: async (clientId) => {
    const url = buildUrl(`${API_URL}/api/budgets`, { client_id: clientId });
    const response = await fetchGet(url);
    return interceptResponse(response);
  },

  export: async (id, format = 'pdf') => {
    const url = `${API_URL}/api/budgets/${id}/export?format=${format}`;
    const response = await fetch(url, {
      headers: buildHeaders()
    });
    
    if (!response.ok) {
      throw new Error('Error exportando presupuesto');
    }
    
    return response.blob();
  }
};

// ============================================
// UTILITIES
// ============================================

/**
 * Ejecutar una solicitud con reintentos automáticos
 * Útil para operaciones críticas
 */
export const withAutoRetry = (fn, maxRetries = 3) => {
  return withRetry(fn, maxRetries, 1000);
};

/**
 * Obtener el token JWT del localStorage
 */
export const getToken = () => {
  try {
    if (typeof localStorage === 'undefined') return null;
    return localStorage.getItem('luiggi_access_token')
      || localStorage.getItem('token')
      || localStorage.getItem('access_token');
  } catch (_) {
    return null;
  }
};

/**
 * Guardar token en localStorage
 */
export const saveToken = (token, type = 'access') => {
  try {
    localStorage.setItem('luiggi_access_token', token);
  } catch (_) {
    console.warn('Could not save token to localStorage');
  }
};

/**
 * Limpiar token del localStorage
 */
export const clearToken = () => {
  try {
    localStorage.removeItem('luiggi_access_token');
    localStorage.removeItem('token');
    localStorage.removeItem('access_token');
  } catch (_) {
    console.warn('Could not clear token from localStorage');
  }
};
