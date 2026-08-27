/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * «FAILED TO FETCH» NO ES UN MENSAJE PARA NADIE.
 *
 * Cuando el navegador no consigue hablar con el servidor, `fetch` lanza un
 * error cuyo texto es «Failed to fetch» (o «Load failed» en Safari, o
 * «NetworkError…» en Firefox). Eso acaba pintado tal cual en pantalla, y a
 * quien lo lee no le dice ni si el fallo es suyo, ni si tiene que esperar, ni
 * si tiene que llamar a alguien. Se vio así:
 *
 *     «(del croquis: Failed to fetch · del render: Failed to fetch ·
 *       de la descripción: Failed to fetch)»
 *
 * —tres veces la misma nada. Y encima el dato importante estaba ahí: si las
 * TRES vías fallan igual, no es el croquis ni el render, es que el servidor no
 * está contestando.
 *
 * Esto pregunta al servidor qué le pasa y devuelve UNA frase en castellano que
 * dice qué hacer. Estaba escrito dentro de la proforma; aquí está una sola vez
 * para que lo use cualquier pantalla, porque el fallo es el mismo en todas.
 */

const API_URL = process.env.REACT_APP_BACKEND_URL;

/** ¿El fallo es de red, o contestó el servidor?
 *
 * Es la pregunta que lo cambia todo: si el servidor contestó (un 422, un 404),
 * su mensaje ya explica el problema y no hay que tocarlo. Solo cuando la
 * llamada no llega hay que salir a averiguar por qué.
 */
export const esFalloDeRed = (e) => {
  const m = (e && e.message) || String(e || '');
  return /failed to fetch|load failed|networkerror|network request failed|network error/i.test(m);
};

const probar = async (url, opts) => {
  try {
    const r = await fetch(url, opts);
    let d = {};
    try { d = await r.json(); } catch { d = {}; }
    return { estado: r.status, detail: d.detail || '' };
  } catch (err) {
    return { estado: 0, detail: (err && err.message) || 'error de red' };
  }
};

/**
 * Qué decirle a quien está mirando la pantalla.
 *
 * @param {Error} e       el error tal cual llegó
 * @param {object} opciones
 *   - sonda: ruta de un endpoint NUEVO. Si el servidor responde pero esa ruta
 *     da 404, es que está sirviendo la versión anterior — que es lo que pasa
 *     durante el minuto o dos que tarda un despliegue.
 */
export const diagnosticarRed = async (e, opciones = {}) => {
  const motivo = (e && e.message) || 'error de red';

  // El servidor contestó: su mensaje es el bueno y no se toca. Sustituirlo por
  // una explicación general taparía el motivo de verdad.
  if (!esFalloDeRed(e)) return motivo;

  if (!API_URL) {
    return 'La aplicación no tiene configurada la dirección del servidor (REACT_APP_BACKEND_URL).';
  }
  if (typeof window !== 'undefined'
      && window.location.protocol === 'https:' && String(API_URL).startsWith('http:')) {
    return `El navegador bloquea la llamada: la web va por HTTPS y el servidor está en HTTP (${API_URL}).`;
  }

  const ping = await probar(`${API_URL}/api/`, { method: 'GET' });
  if (ping.estado === 0) {
    return ('El servidor no responde. O está reiniciándose tras una actualización '
      + '(tarda un par de minutos y se arregla solo) o se ha caído. '
      + 'Espera un momento y vuelve a darle.');
  }

  if (opciones.sonda) {
    const s = await probar(`${API_URL}${opciones.sonda}`, opciones.headers ? { headers: opciones.headers } : undefined);
    if (s.estado === 404) {
      return 'El servidor todavía sirve la versión anterior. Espera a que termine de actualizarse (1-2 minutos).';
    }
  }

  // El servidor está vivo y aun así la llamada no llegó. No se inventa la
  // causa: se dice lo que se sabe y lo que NO se sabe.
  return (`El servidor responde, pero esta llamada no llega hasta él (${motivo}). `
    + 'Suele ser la conexión del dispositivo o algo que la corta por el camino.');
};
