/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */

/**
 * LO QUE CUESTA UN RENDER, EN CRÉDITOS — Y EN UN SOLO SITIO.
 *
 * Gemelo de `COSTE_POR_MOTOR` de `backend/services/ai_usage.py`, que es quien
 * COBRA de verdad. Aquí solo se AVISA. El candado
 * `test_pantalla_aviso_de_coste.py` compara las dos tablas motor a motor: si se
 * separan, el aviso dice una cosa y la factura otra, y ninguno de los dos
 * números parece un error.
 *
 * VIVE AQUÍ Y NO DENTRO DE UNA PANTALLA porque desde el 09/09/2026 hay DOS que
 * renderizan: el Estudio 3D de producción (`AIRenderStudio.jsx`, congelado) y
 * su clon de pruebas (`Estudio3DLab.jsx`). Con la tabla copiada en cada una,
 * añadir un motor obligaría a acordarse de tocar las dos — y el día que se
 * olvide una, esa pantalla avisará un precio distinto del cobro real.
 *
 * EL AVISO NUNCA DICE QUÉ IA SE USA (CLAUDE.md, regla 15; el master, 25/08:
 * «que no ponga nunca qué IA se usa»). Por eso esto es una tabla de NÚMEROS y
 * las claves son nombres técnicos que no salen a pantalla.
 */
export const COSTE_CREDITOS = {
  chatgpt: 1,
  julio11: 1,
  julio11_plus: 1,
  banana_pro: 3.3,
  flux: 1,
  manus: 1,
  gemini: 1,
  gemini_premium: 1,
};

/** Créditos de UN render con el motor dado. Se redondea HACIA ARRIBA, igual
 *  que `coste_de_motor` en el servidor: nadie regala el trozo suelto. */
export function creditosDeUnRender(provider) {
  return Math.ceil(COSTE_CREDITOS[provider] ?? 1);
}
