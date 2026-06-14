/**
 * Utilidades para simplificar y centralizar la lógica de API del frontend.
 * Reduce duplicación de código en api.js y mejora la mantenibilidad.
 */

// ============================================
// URL BUILDER
// ============================================

/**
 * Construir URL con parámetros de consulta
 * @param {string} baseUrl - URL base
 * @param {Object} params - Parámetros a añadir
 * @returns {string} URL completa con parámetros
 */
export const buildUrl = (baseUrl, params = {}) => {
  const query = new URLSearchParams(params);
  return query.toString() ? `${baseUrl}?${query.toString()}` : baseUrl;
};

/**
 * Construir headers con autenticación
 * @param {Object} extra - Headers adicionales
 * @returns {Object} Headers con autenticación incluida
 */
export const buildHeaders = (extra = {}) => {
  const token = getToken();
  const headers = { ...extra };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
};

// ============================================
// ERROR HANDLING
// ============================================

/**
 * Clase personalizada para errores de API
 */
export class APIError extends Error {
  constructor(message, statusCode = 500, detail = null) {
    super(message);
    this.name = 'APIError';
    this.statusCode = statusCode;
    this.detail = detail;
  }
}

/**
 * Procesar respuesta de error desde la API
 * @param {Response} response - Respuesta HTTP
 * @returns {Promise<APIError>}
 */
export const handleAPIError = async (response) => {
  try {
    const data = await response.json();
    return new APIError(
      data.error || data.detail || 'Error desconocido',
      response.status,
      data.detail || null
    );
  } catch {
    return new APIError(
      `Error HTTP ${response.status}`,
      response.status
    );
  }
};

// ============================================
// FETCH WRAPPERS
// ============================================

/**
 * Hacer una solicitud GET
 * @param {string} url - URL a solicitar
 * @param {Object} options - Opciones adicionales
 * @returns {Promise<Object>}
 */
export const fetchGet = async (url, options = {}) => {
  const response = await fetch(url, {
    method: 'GET',
    headers: buildHeaders(options.headers),
    ...options
  });

  if (!response.ok) {
    throw await handleAPIError(response);
  }

  return response.json();
};

/**
 * Hacer una solicitud POST
 * @param {string} url - URL a solicitar
 * @param {Object} body - Cuerpo de la solicitud
 * @param {Object} options - Opciones adicionales
 * @returns {Promise<Object>}
 */
export const fetchPost = async (url, body = {}, options = {}) => {
  const response = await fetch(url, {
    method: 'POST',
    headers: buildHeaders({
      'Content-Type': 'application/json',
      ...options.headers
    }),
    body: JSON.stringify(body),
    ...options
  });

  if (!response.ok) {
    throw await handleAPIError(response);
  }

  return response.json();
};

/**
 * Hacer una solicitud PUT
 * @param {string} url - URL a solicitar
 * @param {Object} body - Cuerpo de la solicitud
 * @param {Object} options - Opciones adicionales
 * @returns {Promise<Object>}
 */
export const fetchPut = async (url, body = {}, options = {}) => {
  const response = await fetch(url, {
    method: 'PUT',
    headers: buildHeaders({
      'Content-Type': 'application/json',
      ...options.headers
    }),
    body: JSON.stringify(body),
    ...options
  });

  if (!response.ok) {
    throw await handleAPIError(response);
  }

  return response.json();
};

/**
 * Hacer una solicitud DELETE
 * @param {string} url - URL a solicitar
 * @param {Object} options - Opciones adicionales
 * @returns {Promise<Object>}
 */
export const fetchDelete = async (url, options = {}) => {
  const response = await fetch(url, {
    method: 'DELETE',
    headers: buildHeaders(options.headers),
    ...options
  });

  if (!response.ok) {
    throw await handleAPIError(response);
  }

  return response.json();
};

// ============================================
// CRUD FACTORY
// ============================================

/**
 * Crear un conjunto de funciones CRUD para un recurso
 * @param {string} baseUrl - URL base del recurso
 * @returns {Object} Funciones CRUD
 */
export const createCRUDAPI = (baseUrl) => ({
  getAll: async (params = {}) => {
    const url = buildUrl(baseUrl, params);
    return fetchGet(url);
  },

  getById: async (id, params = {}) => {
    const url = buildUrl(`${baseUrl}/${id}`, params);
    return fetchGet(url);
  },

  create: async (data) => {
    return fetchPost(baseUrl, data);
  },

  update: async (id, data) => {
    return fetchPut(`${baseUrl}/${id}`, data);
  },

  delete: async (id, params = {}) => {
    const url = buildUrl(`${baseUrl}/${id}`, params);
    return fetchDelete(url);
  }
});

// ============================================
// RETRY LOGIC
// ============================================

/**
 * Ejecutar una función con reintentos
 * @param {Function} fn - Función a ejecutar
 * @param {number} maxRetries - Número máximo de reintentos
 * @param {number} delay - Delay entre reintentos (ms)
 * @returns {Promise}
 */
export const withRetry = async (fn, maxRetries = 3, delay = 1000) => {
  let lastError;

  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      if (i < maxRetries - 1) {
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }

  throw lastError;
};

// ============================================
// RESPONSE INTERCEPTOR
// ============================================

/**
 * Interceptor para manejar respuestas globales
 * @param {Object} response - Respuesta de la API
 * @returns {Object} Respuesta procesada
 */
export const interceptResponse = (response) => {
  // Aquí se pueden añadir lógicas globales como:
  // - Actualizar token si está próximo a expirar
  // - Redirigir a login si el token expiró
  // - Registrar errores globales
  
  if (response.success === false) {
    throw new APIError(
      response.error || 'Error en la solicitud',
      response.status_code || 500,
      response.detail
    );
  }

  return response;
};

// ============================================
// BATCH OPERATIONS
// ============================================

/**
 * Ejecutar múltiples solicitudes en paralelo
 * @param {Array<Promise>} promises - Promesas a ejecutar
 * @returns {Promise<Array>}
 */
export const batchFetch = async (promises) => {
  try {
    return await Promise.all(promises);
  } catch (error) {
    console.error('Error en operación batch:', error);
    throw error;
  }
};

/**
 * Ejecutar múltiples solicitudes con límite de concurrencia
 * @param {Array<Promise>} promises - Promesas a ejecutar
 * @param {number} limit - Límite de concurrencia
 * @returns {Promise<Array>}
 */
export const batchFetchWithLimit = async (promises, limit = 5) => {
  const results = [];
  const executing = [];

  for (const promise of promises) {
    const p = Promise.resolve(promise).then(res => {
      executing.splice(executing.indexOf(p), 1);
      return res;
    });

    results.push(p);
    executing.push(p);

    if (executing.length >= limit) {
      await Promise.race(executing);
    }
  }

  return Promise.all(results);
};
