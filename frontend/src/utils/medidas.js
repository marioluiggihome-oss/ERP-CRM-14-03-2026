/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * UNA SOLA FORMA DE PASAR UNA MEDIDA A MILÍMETROS.
 *
 * POR QUÉ EXISTE ESTO
 * -------------------
 * Cocina Desmontada trabaja en MILÍMETROS: el catálogo de cascos guarda 600, no
 * 60. A ese módulo le llegan muebles desde tres sitios distintos —el analizador
 * de planos, el diseñador 3D y la relación de muebles del PDF— y cada uno tenía
 * su idea de en qué unidad mandarlos.
 *
 * Dos convertían. El tercero mandaba CENTÍMETROS tal cual. Y como el
 * emparejamiento busca «el casco cuyo ancho se parece más», comparar 60 contra
 * 600 no da un error: da el casco MÁS ESTRECHO DEL CATÁLOGO, porque 300 es lo
 * más cercano a 60 que hay. Un bajo de 60, uno de 90 y uno de 60 con cajones
 * salían los tres como el mismo casco de 30 cm, se fundían en una línea, y el
 * presupuesto se imprimía tan tranquilo con muebles que nadie había pedido.
 *
 * Nada fallaba. Ese es el problema: un presupuesto con las medidas cambiadas
 * tiene exactamente el mismo aspecto que uno bueno.
 *
 * LA REGLA
 * --------
 * Un mueble de cocina mide entre 15 y 320 cm. Por debajo de 320 el número es
 * centímetros; a partir de ahí ya son milímetros. No hay mueble de 320 mm de
 * ancho (serían 32 cm) que se confunda con uno de 320 cm, porque los de 32 cm
 * se escriben 32 en cm y 320 en mm — y ese es justo el límite.
 *
 * OJO CON EL LÍMITE: es una heurística, no una verdad. Funciona porque todas
 * las medidas que entran aquí son de muebles de cocina. No se use para otra
 * cosa. Si algún día entra una medida de verdad ambigua, lo correcto es que el
 * origen diga en qué unidad viene, no afinar más este número.
 */

/** Frontera entre «esto son centímetros» y «esto ya son milímetros». */
export const LIMITE_CM_MM = 320;

/**
 * Pasa una medida de mueble a milímetros.
 * Devuelve 0 si no hay medida: un 0 aquí significa «no consta», y quien lo use
 * tiene que tratarlo como tal, no como un ancho de cero.
 */
export function aMilimetros(v) {
  const n = Number(v) || 0;
  if (n <= 0) return 0;
  return n < LIMITE_CM_MM ? Math.round(n * 10) : Math.round(n);
}
