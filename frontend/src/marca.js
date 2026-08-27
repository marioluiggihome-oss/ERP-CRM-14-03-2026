/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * EL NOMBRE COMERCIAL DEL ERP EN LA PANTALLA. UNO SOLO, Y VACÍO POR DEFECTO.
 *
 * Gemelo de `backend/services/marca.py`. Existen los dos porque hay documentos
 * que se generan en el servidor (facturas, catálogo) y otros en el navegador
 * (despiece, fichas de fabricación), y los dos tienen que decidir lo mismo.
 *
 * LA REGLA: EL VALOR POR DEFECTO NO PUEDE SER UNA MARCA. El fallo que había
 * repartido por el ERP era este:
 *
 *     (state?.settings?.companyName || 'LUIGGI HOME')
 *
 * Un ajuste cuyo defecto es la marca no despersonaliza nada: en cuanto una
 * instalación deja el campo vacío, el cliente se encuentra impresa la marca de
 * otra empresa en su presupuesto. Sin marca configurada no se imprime ninguna.
 */

/** La marca configurada, o cadena vacía. Nunca un nombre inventado. */
export const nombreComercial = (settings) =>
  String(settings?.companyName || '').trim();

/**
 * «Despiece de Tableros» + marca -> «Despiece de Tableros · ACME».
 *
 * Sin marca devuelve el texto tal cual, SIN el separador colgando. Ese detalle
 * es la mitad del trabajo: concatenar a pelo deja cabeceras como
 * «· Despiece de Tableros» con el punto al aire, y eso en un PDF que ve un
 * proveedor canta más que la propia marca.
 */
export const conMarca = (texto, settings, separador = ' · ') => {
  const m = nombreComercial(settings);
  if (!m) return texto || '';
  if (!texto) return m;
  return `${m}${separador}${texto}`;
};
