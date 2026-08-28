/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * TRES PLATAFORMAS EN EL MISMO ERP, Y SOLO UNA TIENE COOPERATIVISTAS.
 *
 * Copia en pantalla de `backend/services/plataformas.py`. Existe porque el menú
 * tiene que decidir si enseña «Mi área» ANTES de llamar a nadie, y no puede
 * preguntarle al servidor por cada botón.
 *
 * OJO: esto NO es el candado. El que manda es el del servidor
 * (`area_cooperativista.rol_de`), que es el único que cierra de verdad: un menú
 * es una sugerencia y cualquiera puede llamar a la API por su cuenta. Esto solo
 * evita enseñarle a un suscriptor de carpinter.io un botón que le va a dar 403.
 * Que las dos mitades digan lo mismo lo vigila
 * `test_calculo_plataformas.py::test_la_pantalla_decide_igual_que_el_servidor`.
 */
export const COOPERATIVA = 'cooperativa';
export const CARPINTER = 'carpinter';
export const STUDIO3K = 'studio3k';

export const TODAS = [COOPERATIVA, CARPINTER, STUDIO3K];

// Las que venden suscripciones. Ni comisiones, ni cooperativistas, ni nómina.
export const SOLO_SUSCRIPCIONES = [CARPINTER, STUDIO3K];

export const NOMBRES = {
  [COOPERATIVA]: 'Red de distribución',
  [CARPINTER]: 'carpinter.io',
  [STUDIO3K]: 'Studio3K.io',
};

/**
 * A qué plataforma pertenece un usuario. Por defecto, la cooperativa: todos los
 * usuarios que ya existen son del negocio de siempre y ninguno tiene el campo,
 * así que cualquier otro defecto los dejaría sin su área el día del despliegue.
 */
export const plataformaDe = (u) => {
  const v = String((u && u.plataforma) || '').trim().toLowerCase();
  return TODAS.includes(v) ? v : COOPERATIVA;
};

export const esDeLaCooperativa = (u) => plataformaDe(u) === COOPERATIVA;

/** Solo la cooperativa reparte comisiones. Ser comercial no basta. */
export const puedeTenerComision = (u) => esDeLaCooperativa(u);

/**
 * SER COOPERATIVISTA SE MARCA, NO SE DEDUCE.
 *
 * El master, 27/08/2026: «no todos son de la cooperativa. Comercial
 * cooperativista sí, montador cooperativista también. Los demás son
 * independientes. El rol de comisiones solamente es para estos dos».
 *
 * La primera versión sacaba el socio del rol genérico del ERP (`isMontador`,
 * `isRepresentative`), y con eso el comercial y el montador de toda la vida de
 * la casa entraban en la nómina sin que nadie lo hubiera decidido.
 */
export const esCooperativistaMontador = (u) =>
  !!(u && u.esCooperativistaMontador) && puedeTenerComision(u);

export const esCooperativistaComercial = (u) =>
  !!(u && u.esCooperativistaComercial) && puedeTenerComision(u);

/** Quién ve «Mi área»: socio de la cooperativa, y nadie más. */
export const esCooperativista = (u) =>
  esCooperativistaMontador(u) || esCooperativistaComercial(u);
