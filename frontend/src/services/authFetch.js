/*
 * © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
// Interceptor global de `fetch`: adjunta el JWT a TODAS las peticiones al backend
// propio. Así la app sigue funcionando cuando el backend exija autenticación de
// forma global (Fase 2), sin tener que tocar las ~300 llamadas una por una.
//
// Está acotado a nuestro backend (el frontend no hace fetch a terceros), por lo
// que el token NUNCA se filtra a dominios externos. Si una llamada ya trae su
// cabecera Authorization (p. ej. via authHeaders()), se respeta y no se duplica.
const BACKEND = process.env.REACT_APP_BACKEND_URL || '';

const getToken = () => {
  try {
    return (
      localStorage.getItem('luiggi_access_token') ||
      localStorage.getItem('token') ||
      localStorage.getItem('access_token')
    );
  } catch {
    return null;
  }
};

const isBackendUrl = (url) => {
  if (typeof url !== 'string') return false;
  if (BACKEND && url.startsWith(BACKEND)) return true;
  return url.startsWith('/api/'); // rutas relativas mismo-origen
};

if (typeof window !== 'undefined' && window.fetch && !window.__luiggiAuthFetch) {
  const origFetch = window.fetch.bind(window);

  window.fetch = (input, init) => {
    try {
      const url = typeof input === 'string' ? input : (input && input.url) || '';
      if (isBackendUrl(url)) {
        const token = getToken();
        if (token) {
          const base =
            (init && init.headers) ||
            (typeof input !== 'string' && input && input.headers) ||
            {};
          const headers = new Headers(base);
          if (!headers.has('Authorization')) {
            headers.set('Authorization', `Bearer ${token}`);
            init = { ...(init || {}), headers };
          }
        }
      }
    } catch {
      // Nunca bloquear una petición por un fallo del interceptor.
    }
    return origFetch(input, init);
  };

  window.__luiggiAuthFetch = true;
}
