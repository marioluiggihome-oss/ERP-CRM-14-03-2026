/*
 * © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * Authentication Service
 * Maneja tokens JWT, almacenamiento seguro y renovación automática
 */

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Claves de localStorage
const TOKEN_KEY = 'luiggi_access_token';
const REFRESH_TOKEN_KEY = 'luiggi_refresh_token';
const USER_KEY = 'luiggi_user';

/**
 * Almacenar tokens de forma segura
 */
export const setTokens = (accessToken, refreshToken) => {
  localStorage.setItem(TOKEN_KEY, accessToken);
  if (refreshToken) {
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  }
};

/**
 * Obtener access token
 */
export const getAccessToken = () => {
  return localStorage.getItem(TOKEN_KEY);
};

/**
 * Obtener refresh token
 */
export const getRefreshToken = () => {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
};

/**
 * Limpiar tokens (logout)
 */
export const clearTokens = () => {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
};

/**
 * Guardar usuario en localStorage
 */
export const setUser = (user) => {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
};

/**
 * Obtener usuario de localStorage
 */
export const getUser = () => {
  const userStr = localStorage.getItem(USER_KEY);
  if (!userStr) return null;
  try {
    return JSON.parse(userStr);
  } catch {
    return null;
  }
};

/**
 * Verificar si hay sesión activa
 */
export const isAuthenticated = () => {
  const token = getAccessToken();
  if (!token) return false;
  
  // Verificar si el token ha expirado (decodificación básica)
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const exp = payload.exp * 1000; // Convertir a milliseconds
    return Date.now() < exp;
  } catch {
    return false;
  }
};

/**
 * Renovar access token usando refresh token
 */
export const refreshAccessToken = async () => {
  const refreshToken = getRefreshToken();
  if (!refreshToken) {
    throw new Error('No refresh token available');
  }
  
  const response = await fetch(`${API_URL}/api/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken })
  });
  
  if (!response.ok) {
    clearTokens();
    throw new Error('Token refresh failed');
  }
  
  const data = await response.json();
  setTokens(data.access_token, null); // Solo actualiza el access token
  return data.access_token;
};

/**
 * Hacer petición autenticada con renovación automática de token
 */
export const authFetch = async (url, options = {}) => {
  let token = getAccessToken();
  
  // Si no hay token, intentar obtenerlo
  if (!token) {
    throw new Error('No authentication token');
  }
  
  // Verificar si el token está próximo a expirar (menos de 5 minutos)
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const exp = payload.exp * 1000;
    const fiveMinutes = 5 * 60 * 1000;
    
    if (Date.now() > exp - fiveMinutes) {
      // Token próximo a expirar, renovar
      try {
        token = await refreshAccessToken();
      } catch (e) {
        // Si falla la renovación, usar el token actual hasta que expire
        console.warn('Token refresh failed, using current token');
      }
    }
  } catch (e) {
    console.error('Token decode error:', e);
  }
  
  // Añadir header de autorización
  const headers = {
    ...options.headers,
    'Authorization': `Bearer ${token}`
  };
  
  const response = await fetch(url, { ...options, headers });
  
  // Si es 401, intentar renovar y reintentar
  if (response.status === 401) {
    try {
      token = await refreshAccessToken();
      headers['Authorization'] = `Bearer ${token}`;
      return fetch(url, { ...options, headers });
    } catch (e) {
      clearTokens();
      window.location.href = '/'; // Redirigir al login
      throw new Error('Session expired');
    }
  }
  
  return response;
};

/**
 * Login
 */
export const login = async (username, password) => {
  try {
    const response = await fetch(`${API_URL}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    
    const text = await response.text();
    let data;
    
    try {
      data = JSON.parse(text);
    } catch {
      throw new Error('Error en respuesta del servidor');
    }
    
    if (!response.ok) {
      throw new Error(data.detail || 'Login failed');
    }
    
    // Guardar tokens y usuario
    if (data.tokens) {
      setTokens(data.tokens.access_token, data.tokens.refresh_token);
    }
    setUser(data.user);
    
    return data;
  } catch (error) {
    throw error;
  }
};

/**
 * Logout
 */
export const logout = async () => {
  try {
    const token = getAccessToken();
    if (token) {
      await fetch(`${API_URL}/api/auth/logout`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      });
    }
  } catch (e) {
    console.error('Logout error:', e);
  } finally {
    clearTokens();
  }
};

/**
 * Obtener información del usuario actual desde el servidor
 */
export const getCurrentUser = async () => {
  const token = getAccessToken();
  if (!token) return null;
  
  try {
    const response = await authFetch(`${API_URL}/api/auth/me`);
    if (!response.ok) return null;
    
    const data = await response.json();
    setUser(data.user);
    return data.user;
  } catch {
    return null;
  }
};

export default {
  login,
  logout,
  isAuthenticated,
  getAccessToken,
  getUser,
  setUser,
  clearTokens,
  authFetch,
  refreshAccessToken,
  getCurrentUser
};
