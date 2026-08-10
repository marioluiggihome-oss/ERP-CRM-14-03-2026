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
  lineMarkup: 'INC% de la línea',
  expNumber: 'nº de expediente',
  budgetNumber: 'nº de presupuesto',
  totalPvp: 'total',
};

// Los mensajes de Pydantic vienen en inglés y de forma técnica. Los tres o
// cuatro que salen de verdad, dichos como los diría una persona.
const TRADUCCION_MSG = [
  [/unable to parse string as a number|valid number/i, 'está en blanco o no es un número'],
  [/valid integer/i, 'tiene que ser un número entero'],
  [/[Ff]ield required/i, 'falta por rellenar'],
  [/greater than 0|greater_than/i, 'tiene que ser mayor que cero'],
  [/valid string/i, 'no es un texto válido'],
];

const _traducirMsg = (msg) => {
  for (const [patron, texto] of TRADUCCION_MSG) if (patron.test(msg)) return texto;
  return msg;
};

const _campo = (nombre) => NOMBRE_CAMPO[nombre] || nombre;

/** Convierte el `loc` de FastAPI en algo que se entienda. */
function _donde(loc) {
  // ['body', 'lines', 0, 'quantity'] → «línea 1 · cantidad»
  // Del formato `campo` llega como texto: "body.lines.0.quantity" ya partido,
  // así que los índices vienen como cadenas y hay que volverlos a número.
  const partes = (loc || [])
    .filter(p => p !== 'body' && p !== '')
    .map(p => (typeof p === 'string' && /^\d+$/.test(p) ? Number(p) : p));
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
    // Error de validación: una entrada por campo que no cuadra.
    //
    // OJO: este servidor NO manda el formato de FastAPI tal cual. Tiene su
    // propio manejador (`_validation_error_handler` en server.py) que reescribe
    // cada error como {campo: "body.lines.0.quantity", msg: "..."}. Se
    // entienden LAS DOS FORMAS: si solo se leyera `loc`, el mensaje llegaba sin
    // decir qué campo fallaba — que es la mitad de lo que sirve.
    const problemas = detail.slice(0, 3).map((e) => {
      const donde = _donde(e?.loc || String(e?.campo || '').split('.'));
      const que = _traducirMsg(e?.msg || 'dato no válido');
      return donde ? `${donde} ${que}` : que;
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
