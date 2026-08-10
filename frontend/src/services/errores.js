/*
 * © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * LEER LO QUE DICE EL SERVIDOR CUANDO ALGO FALLA.
 *
 * POR QUÉ EXISTE ESTO
 * -------------------
 * Al guardar un presupuesto del digitalizador salía esto en rojo:
 *
 *     [object Object]
 *
 * Y no es un error raro: es lo que pasa SIEMPRE que el servidor rechaza los
 * datos. FastAPI, cuando algo no cuadra, no contesta con una frase: contesta
 * con una LISTA de objetos, uno por campo mal:
 *
 *     {"detail": [{"loc": ["body","lines",0,"quantity"],
 *                  "msg": "Input should be a valid integer", ...}]}
 *
 * El código de la pantalla hacía `new Error(d.detail)`, y JavaScript convierte
 * un objeto en texto poniendo «[object Object]». O sea que el servidor decía
 * exactamente qué línea y qué campo estaban mal, y esa información se tiraba
 * por el camino. El usuario veía un mensaje que no significa nada y el fallo se
 * volvía imposible de arreglar sin abrir el log.
 *
 * Aquí se traduce a algo que se pueda leer, DICIENDO EL CAMPO. «La línea 1
 * tiene la cantidad mal» se arregla solo; «[object Object]» no se arregla nunca.
 */

// Cómo se llama en cristiano cada campo que puede venir mal.
const NOMBRE_CAMPO = {
  quantity: 'cantidad',
  price: 'precio',
  discount: 'descuento',
  description: 'descripción',
  reference: 'referencia',
  lines: 'líneas',
  items: 'líneas',
  projectName: 'nombre del proyecto',
  customerName: 'cliente',
  userId: 'usuario',
  ivaRate: 'IVA',
  globalDiscount: 'descuento global',
  globalMarkup: 'incremento global',
};

const _campo = (nombre) => NOMBRE_CAMPO[nombre] || nombre;

/** Convierte el `loc` de FastAPI en algo que se entienda. */
function _donde(loc) {
  // ['body', 'lines', 0, 'quantity'] → «línea 1 · cantidad»
  const partes = (loc || []).filter(p => p !== 'body');
  const trozos = [];
  for (let i = 0; i < partes.length; i++) {
    const p = partes[i];
    if (typeof p === 'number') continue;
    const siguiente = partes[i + 1];
    if (typeof siguiente === 'number') {
      // Una posición dentro de una lista. Se cuenta desde 1: quien mira la
      // pantalla ve la línea 1, no la 0.
      trozos.push(`${_campo(p) === 'líneas' ? 'línea' : _campo(p)} ${siguiente + 1}`);
    } else {
      trozos.push(_campo(p));
    }
  }
  return trozos.join(' · ');
}

/**
 * El mensaje legible de un error del servidor.
 *
 * @param {any} detail  el campo `detail` de la respuesta, sea lo que sea
 * @param {number} status  el código HTTP, para poder decir algo si no hay detail
 */
export function mensajeDeError(detail, status) {
  if (typeof detail === 'string' && detail.trim()) return detail;

  if (Array.isArray(detail) && detail.length) {
    // Error de validación de FastAPI: una entrada por campo que no cuadra.
    const problemas = detail.slice(0, 3).map((e) => {
      const donde = _donde(e?.loc);
      const que = e?.msg || 'dato no válido';
      return donde ? `${donde}: ${que}` : que;
    });
    const resto = detail.length > 3 ? ` (y ${detail.length - 3} más)` : '';
    return `El servidor ha rechazado los datos — ${problemas.join('; ')}${resto}.`;
  }

  if (detail && typeof detail === 'object') {
    // Un objeto suelto: se enseña lo que tenga dentro antes que un «[object
    // Object]», que no dice absolutamente nada.
    const texto = detail.message || detail.error || detail.detail;
    if (typeof texto === 'string' && texto.trim()) return texto;
    try { return JSON.stringify(detail); } catch { /* referencias circulares */ }
  }

  if (status === 401) return 'La sesión ha caducado. Vuelve a entrar.';
  if (status === 403) return 'No tienes permiso para hacer esto.';
  if (status === 413) return 'El archivo es demasiado grande.';
  if (status) return `El servidor ha contestado ${status}.`;
  return 'No se ha podido completar la operación.';
}

/**
 * Lee una respuesta que ha ido mal y devuelve el mensaje ya legible.
 * Se usa así:  if (!r.ok) throw new Error(await errorDeRespuesta(r));
 */
export async function errorDeRespuesta(respuesta) {
  let cuerpo = null;
  try { cuerpo = await respuesta.json(); } catch { /* no era JSON */ }
  return mensajeDeError(cuerpo?.detail ?? cuerpo, respuesta?.status);
}
