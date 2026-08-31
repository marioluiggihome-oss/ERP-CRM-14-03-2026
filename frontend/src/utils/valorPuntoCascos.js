/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * EL VALOR DEL PUNTO DE CASCOS. Uno solo, y ES DOS.
 *
 * El master, 31/08: «el precio parte del PVP, por eso se multiplica por el
 * valor, que ahora es 2», y «el valor del punto hoy es 2, según la casilla de
 * márgenes».
 *
 * QUÉ ES: el catálogo `cascos.js` trae la TARIFA de ACB, que es lo que le
 * CUESTA a la casa. Multiplicada por el valor del punto sale el PVP de venta.
 * El descuento del proveedor (hoy un −28 %) NO va aquí: lo teclea el master en
 * el modal de descuentos «porque puede variar».
 *
 *     PVP   = tarifa × valor del punto          (2)
 *     coste = tarifa × (1 − descuento ACB)      (el que se teclea)
 *
 * POR QUÉ ESTABA MAL, Y CUÁNTO COSTABA: este dato se leía en CUATRO sitios con
 * CUATRO defectos distintos —1,0 en la casilla de Ajustes, 1,0 al cargar en
 * App.js, 1 en Cocina Desmontada y 1,30 aquí—. Con la casilla vacía, o mientras
 * los ajustes aún no han cargado, el MISMO casco de 58,52 € de tarifa se vendía
 * a 58,52 € en Cocina Desmontada y a 76,08 € en el Presupuestador, cuando su
 * PVP son 117,04 €. O sea: Desmontada lo vendía a MITAD DE PRECIO, sin dar
 * ningún error y con toda la pinta de un presupuesto normal.
 *
 * Un dato de dinero con cuatro defectos no tiene defecto: tiene cuatro precios.
 */
export const VALOR_PUNTO_CASCOS = 2;

/** El valor del punto de cascos, mire quien lo mire.
 *
 *  Se acepta el `state` de la aplicación (que es de donde lo lee Cocina
 *  Desmontada) y, si no llega, se busca en localStorage (que es de donde lo lee
 *  el Presupuestador). Las dos puertas, UNA sola respuesta. */
export const valorPuntoCascos = (state) => {
  const limpio = (v) => {
    const n = parseFloat(v);
    return Number.isFinite(n) && n > 0 ? n : null;
  };
  const delEstado = limpio(state?.pointValueDesmontada) ?? limpio(state?.settings?.cascosPointValue);
  if (delEstado != null) return delEstado;
  try {
    const v = limpio(localStorage.getItem('pointValueDesmontada'));
    if (v != null) return v;
    const st = JSON.parse(localStorage.getItem('app_state') || '{}');
    const w = limpio(st?.pointValueDesmontada);
    if (w != null) return w;
    const set = JSON.parse(localStorage.getItem('settings') || '{}');
    const x = limpio(set?.cascosPointValue);
    if (x != null) return x;
  } catch { /* sin navegador o con datos rotos: el valor de la casa */ }
  return VALOR_PUNTO_CASCOS;
};
