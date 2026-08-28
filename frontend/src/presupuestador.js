/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * QUIÉN VE QUÉ DENTRO DEL PRESUPUESTADOR.
 *
 * El master, 28/08: juntar Cocina Montada 3 y Cocina Desmontada en una sola
 * sección llamada «Presupuestador», y que «el máster vería todo, pero el resto
 * de usuarios la pestaña de Cocina Desmontada la verían dependiendo de si está
 * activo o no ese permiso».
 *
 * LOS PERMISOS NO CAMBIAN: son los mismos de siempre (`canUsePresupuestador3` y
 * `canUseCascos`). Lo único que cambia es dónde se pintan. Cambiar la puerta no
 * puede cambiar quién entra — si de paso se movieran los permisos, nadie sabría
 * si un usuario dejó de ver algo por el rediseño o porque se lo quitamos.
 *
 * ESTO ES UNA SUGERENCIA, NO UN CANDADO. Esconder una pestaña no cierra nada:
 * la API de cascos comprueba el permiso por su cuenta. Es la regla 8 del
 * proyecto — un cierre que solo está en pantalla es de adorno.
 */
export const MONTADA = 'montada';
export const DESMONTADA = 'desmontada';

export const NOMBRES = {
  [MONTADA]: 'Cocina Montada',
  [DESMONTADA]: 'Cocina Desmontada',
};

const esMaster = (u) =>
  !!(u && (u.isMaster || u.isPrimaryAdmin || u.isAdmin));

/** Cocina Montada 3: el permiso es «no estar desactivado» (así estaba). */
export const puedeMontada = (u) =>
  esMaster(u) || (u ? u.canUsePresupuestador3 !== false : false);

/** Cocina Desmontada: permiso EXPLÍCITO, y nunca para una tienda. */
export const puedeDesmontada = (u) => {
  if (!u) return false;
  if (esMaster(u)) return true;
  return u.canUseCascos === true && !u.isTienda;
};

/** Las pestañas que le tocan a ese usuario, en orden. */
export const pestanasDe = (u) => {
  const fuera = [];
  if (puedeMontada(u)) fuera.push(MONTADA);
  if (puedeDesmontada(u)) fuera.push(DESMONTADA);
  return fuera;
};

/** Si ve alguna, ve la sección. */
export const puedeEntrar = (u) => pestanasDe(u).length > 0;

/**
 * La barra de pestañas SOLO se enseña si hay más de una.
 *
 * A quien solo tiene una, una pestaña suelta no le dice nada: es ruido con
 * aspecto de que falta algo.
 */
export const hayQueEnseñarPestanas = (u) => pestanasDe(u).length > 1;
