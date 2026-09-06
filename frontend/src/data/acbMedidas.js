/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
// CÓMO SE FACTURA UNA MEDIDA QUE NO ESTÁ EN EL CUADRO.
//
// Las tres tarifas de ACB —canteado, laca y madera— son rejillas de alto ×
// ancho. Una puerta real casi nunca cae en una casilla: mide 596 × 397, no
// 598 × 398. La tarifa lo resuelve en una línea (pág. 7 de la laca):
//
//     «El precio para medidas especiales será igual al precio de la medida
//      inmediata superior»
//
// NO SE INTERPOLA. Interpolar da un número que ACB no factura, que es
// exactamente inventarse una cifra (CLAUDE.md, regla 7).
//
// LO QUE LA TARIFA NO DICE, Y HAY QUE DECIDIR. «Subir cada medida por su lado»
// parece lo natural y da resultados absurdos, porque la rejilla TIENE HUECOS:
// la fila de alto 598 solo se fabrica en 598 de ancho, y la de 418 solo en 298
// y 598. Medido sobre las tres tarifas, en el 96 % de las medidas las dos
// reglas coinciden; en el 4 % restante subir por ejes COBRA DE MÁS:
//
//     una pieza de 560 × 200  ->  por ejes 598 × 598 = 61,91 €
//                             ->  la más barata que la cubre 698 × 248 = 35,42 €
//
// y en otros 210 casos ni siquiera encuentra casilla, dejando sin presupuestar
// una puerta que ACB sí fabrica.
//
// LA REGLA ES: LA CASILLA MÁS BARATA QUE CUBRE LA PIEZA (alto ≥ alto pedido y
// ancho ≥ ancho pedido). Cuando la casilla exacta existe, las dos reglas dan lo
// mismo —así que en el caso normal esto ES «la medida inmediata superior»—, y
// en los huecos no cobra de más ni deja de tarifar lo que se fabrica.
//
// ESTO ES UNA DECISIÓN NUESTRA, NO UNA LÍNEA DEL PDF, así que la casilla con la
// que se factura VIAJA CON LA LÍNEA y se enseña al lado de la medida real. Un
// criterio que no se ve no lo puede comprobar nadie con el proveedor.
//
// Y LA MEDIDA REAL NO SE PIERDE. El escalón decide lo que CUESTA; el alto y el
// ancho de verdad son lo que se fabrica y lo que viaja con el pedido — es la
// misma regla que ya rige en los costados de MV (CLAUDE.md: «EL ESCALÓN DE LA
// TARIFA NO ES LA MEDIDA»).

/** Pasa a MILÍMETROS lo que se teclea, en la unidad en la que esté la pantalla.
 *
 *  ADMITE LA COMA. En un teclado español se teclea «59,6», y `Number('59,6')`
 *  es `NaN`: sin esto la medida se perdería en silencio.
 *
 *  Devuelve `null` —no 0— cuando no hay nada escrito o no es un número. Un 0
 *  aquí sería un ancho de cero, y eso sí que se cuela en un presupuesto. */
export const aMmTecleado = (texto, unidad) => {
  const bruto = String(texto ?? '').trim().replace(',', '.');
  if (!bruto) return null;
  const n = Number(bruto);
  if (!Number.isFinite(n) || n <= 0) return null;
  return Math.round(unidad === 'cm' ? n * 10 : n);
};

/** LA CASILLA CON LA QUE SE FACTURA UNA MEDIDA.
 *
 *  `matriz` es la MISMA que pinta la tabla —{ grupos: [{ altos, precios }] }—
 *  a propósito: así el precio que sale al teclear una medida y el que sale al
 *  pulsar una casilla no pueden separarse nunca, porque salen del mismo sitio.
 *
 *  Devuelve `null` cuando ACB no fabrica ninguna pieza que cubra esa medida.
 *  Eso NO es un error a tapar: es que la puerta no se puede pedir así. */
export const casillaFacturableACB = (matriz, altoMm, anchoMm) => {
  const a = Number(altoMm), w = Number(anchoMm);
  if (!Number.isFinite(a) || !Number.isFinite(w) || a <= 0 || w <= 0) return null;

  /* LA CASILLA EXACTA MANDA SOBRE TODO LO DEMÁS.
     Si la medida ES una medida de tarifa, se factura ESA casilla y punto: eso
     es lo que dice la tarifa y es lo que se ve al pulsarla en el cuadro.
     Hace falta decirlo aparte porque la tarifa de ACB tiene inversiones de un
     céntimo —el Touch 22 de 798x248 vale 31,64 € y el de 798x298 vale
     31,63 €—, así que «la más barata que cubre» elegiría la de al lado y
     teclear 79,8 x 24,8 daría un precio distinto que pulsar esa casilla. Un
     céntimo no arruina a nadie; dos precios para la misma puerta según por
     dónde entres, sí, porque no hay forma de saber cuál es el bueno. */
  for (const g of (matriz && matriz.grupos) || []) {
    if (!(g.altos || []).includes(a)) continue;
    const p = (g.precios || {})[String(w)];
    if (p != null) return { alto: a, ancho: w, precio: p, exacta: true };
  }

  let mejor = null;
  for (const g of (matriz && matriz.grupos) || []) {
    for (const alto of g.altos || []) {
      if (alto < a) continue;
      for (const clave of Object.keys(g.precios || {})) {
        const ancho = Number(clave);
        const precio = g.precios[clave];
        if (!(ancho >= w) || precio == null) continue;
        // A igualdad de precio, la pieza MÁS PEQUEÑA: es la que menos tablero
        // gasta y la que el proveedor entiende como «la inmediata superior».
        const gana = !mejor || precio < mejor.precio
          || (precio === mejor.precio
              && (alto < mejor.alto || (alto === mejor.alto && ancho < mejor.ancho)));
        if (gana) mejor = { alto, ancho, precio };
      }
    }
  }
  if (!mejor) return null;
  // Si se llega aquí es que la casilla exacta no existe: la medida es especial.
  return { ...mejor, exacta: false };
};

/** El escalón con el que se factura un TIRADOR para un ancho dado.
 *
 *  Mismo criterio y por el mismo motivo: el inmediato superior, nunca
 *  interpolado. `null` si ACB no lo hace tan ancho — que es distinto de que
 *  sea gratis. */
export const escalonTiradorACB = (precios, anchoMm) => {
  const w = Number(anchoMm);
  if (!precios || !Number.isFinite(w) || w <= 0) return null;
  const pasos = Object.keys(precios).map(Number).filter(Number.isFinite)
    .sort((x, y) => x - y);
  const paso = pasos.find((x) => x >= w);
  if (paso == null) return null;
  return { ancho: paso, precio: precios[String(paso)], exacta: paso === w };
};
