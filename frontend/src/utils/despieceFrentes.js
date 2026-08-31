/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * EL DESPIECE DE FRENTES: PIEZA A PIEZA, PARA PODER PEDIRLE AL PROVEEDOR.
 *
 * El master, 31/08: «en algún sitio debo de poder meter el descuento o los
 * precios de cada puerta, haciendo un desglose de puertas, frentes, costados,
 * etc., para luego comprobar y ver si están bien de cara a poder pedir a
 * proveedor».
 *
 * QUÉ FALTABA. El «Escandallo» que ya había da TOTALES —metros de tablero,
 * bisagras, horas de taller— y eso no sirve para pedir: al proveedor no se le
 * pide «4,2 m² de puerta», se le piden CINCO puertas de 80×45 y TRES cajones de
 * 14×60. El dato existía —`despiece` ya devuelve `puertasDetalle` con cada
 * frente y sus puntos— y no se enseñaba en ninguna parte: vivía dentro del
 * texto de ayuda de una celda.
 *
 * LAS TRES COSAS QUE HACEN QUE ESTA LISTA SIRVA PARA PEDIR
 * --------------------------------------------------------
 * 1. LAS UNIDADES MULTIPLICAN. Dos muebles B90 iguales son CUATRO puertas, no
 *    dos (CLAUDE.md, regla 4). Pedir de menos se ve en la obra, con el montador
 *    delante y la cocina a medio montar.
 *
 * 2. UN FRENTE SIN TARIFA NO VALE CERO. La matriz MV no tiene todas las
 *    casillas; `getDesglosePuertasDetallado` ya lo marca (`sinTarifa`) en vez de
 *    sumar 0. Aquí se conserva la marca: una pieza que sale gratis en la lista
 *    se pide igual y llega la factura.
 *
 * 3. LOS LINEALES ENTRAN TAMBIÉN. Costados, laterales, regletas y techos no son
 *    frentes y no tienen despiece, pero SE PIDEN. Una lista para el proveedor a
 *    la que le faltan los costados es una lista que hay que completar a mano,
 *    y entonces no se usa.
 */

/** Redondeo a céntimos, en un solo sitio para que todas las cifras cuadren. */
const cent = (n) => Math.round((Number(n) || 0) * 100) / 100;

/**
 * Aplana las líneas del presupuesto en PIEZAS pedibles.
 *
 * Cada pieza: { mueble, cod, pieza, alto, ancho, uds, puntos, pvpUd, costeUd,
 *               pvp, coste, sinTarifa, esLineal }
 * Medidas en CENTÍMETROS, que es como se le habla al proveedor.
 */
export const despieceDeFrentes = (filas, { esLineal } = {}) => {
  const piezas = [];
  for (const m of filas || []) {
    const uds = Math.max(1, Number(m.qty) || 1);
    const d = m.despiece || {};
    const detalle = Array.isArray(d.puertasDetalle) ? d.puertasDetalle : [];

    // ── LINEALES: no se despiezan, se piden tal cual ──
    if (esLineal && esLineal(m)) {
      piezas.push({
        mueble: m.cod || '?', cod: m.cod || '?',
        pieza: (m.desc || '').trim() || (m.familia || 'Pieza lineal').replace(/_/g, ' '),
        // La medida REAL manda sobre el escalón de tarifa: el escalón dice lo
        // que cuesta, la medida es lo que se corta (CLAUDE.md, regla del escalón).
        alto: m.altoReal ?? m.alto ?? null,
        ancho: m.anchoReal ?? m.anchoTarifa ?? m.ancho ?? null,
        uds, puntos: null,
        pvpUd: cent(m.pvp), costeUd: m.coste == null ? null : cent(m.coste),
        pvp: cent((Number(m.pvp) || 0) * uds),
        coste: m.coste == null ? null : cent(m.coste * uds),
        sinTarifa: false, esLineal: true,
      });
      continue;
    }

    if (!detalle.length) continue;   // un mueble sin frentes no aporta piezas

    // EL REPARTO DEL COSTE ENTRE LOS FRENTES va POR PUNTOS, no a partes
    // iguales: en un BCG60 el cajón de 14 y la gaveta de 35 no cuestan lo
    // mismo, y repartir a medias daría un precio bonito y falso en las dos.
    const puntosTotales = detalle.reduce((t, f) => t + (Number(f.puntos) || 0), 0);
    for (const f of detalle) {
      const pts = f.puntos == null ? null : Number(f.puntos);
      const parte = (pts != null && puntosTotales > 0) ? pts / puntosTotales : 0;
      const pvpUd = pts == null ? null : cent((Number(d.puertaPvp) || 0) * parte);
      const costeUd = pts == null ? null : cent((Number(d.puerta) || 0) * parte);
      piezas.push({
        mueble: m.cod || '?', cod: m.cod || '?',
        // El rótulo del frente trae las medidas entre paréntesis; se quitan,
        // que van en sus columnas.
        pieza: String(f.desc || 'Frente').replace(/\s*\([^)]*\)\s*$/, ''),
        alto: f.h ?? null, ancho: f.w ?? null,
        uds, puntos: pts,
        pvpUd, costeUd,
        pvp: pvpUd == null ? null : cent(pvpUd * uds),
        coste: costeUd == null ? null : cent(costeUd * uds),
        sinTarifa: !!f.sinTarifa, esLineal: false,
      });
    }
  }
  return piezas;
};

/** Los totales de la lista. Los `null` NO cuentan como cero: se cuentan aparte,
 *  porque un total que se traga las piezas sin tarifa sale más barato que la
 *  factura que llega después. */
export const totalesDelDespiece = (piezas) => {
  let uds = 0, puntos = 0, pvp = 0, coste = 0, sinTarifa = 0, m2 = 0;
  for (const p of piezas || []) {
    uds += p.uds;
    if (p.puntos != null) puntos += p.puntos * p.uds;
    if (p.pvp != null) pvp += p.pvp;
    if (p.coste != null) coste += p.coste; else sinTarifa += p.uds;
    if (p.alto && p.ancho) m2 += (p.alto / 100) * (p.ancho / 100) * p.uds;
  }
  return {
    piezas: (piezas || []).length,
    uds, puntos,
    pvp: cent(pvp), coste: cent(coste),
    m2: Math.round(m2 * 100) / 100,
    sinTarifa,
  };
};
