/*
 * © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
import { DOOR_FINISHES, MV_TARIFFS } from '../constants';

/**
 * Motor de precio PURO reutilizable (extraído de calculateLineDetails en
 * BudgetTable.jsx). Replica EXACTAMENTE la fórmula del Presupuestador 1
 * respetando las dos librerías/sistemas de tarifa:
 *   - MV: columnas de tarifa T1..T21 (mapa MV_TARIFFS por globalFinish/tarifa)
 *   - ZC: columnas de zona   Z1..Z12 (mapa DOOR_FINISHES por grupo de precios)
 *
 * NO depende de React ni de `state`: todo lo que antes salía del estado se
 * recibe por `opts`.
 *
 * @param {object|null} product  Producto de catálogo (o null en líneas manuales)
 * @param {object} opts
 * @param {boolean} [opts.isManual]            Línea manual (valor directo en €)
 * @param {number}  [opts.manualPoints]        Valor € de la línea manual
 * @param {string}  [opts.library]             'MV' | 'ZC' (state.currentLibrary)
 * @param {string}  [opts.module]              'montada' | 'despiece' (para etiqueta dto)
 * @param {string}  [opts.finishName]          Acabado/tarifa activa (state.globalFinish)
 * @param {number}  [opts.pointValue]          Valor del punto (€/pt) ya resuelto
 * @param {object}  [opts.increments]          { width, height, depth } incrementos por corte
 * @param {number}  [opts.carcassIncrement]    Incremento fijo del material de casco
 * @param {number}  [opts.vigaIncrement]       Incremento por corte de viga
 * @param {boolean} [opts.hasVigaCut]          Si la línea lleva corte de viga
 * @param {object}  [opts.customDims]          { width, height, depth } medidas de la línea
 * @param {boolean} [opts.showDistributorPrice] Modo PVP/COSTO
 * @param {number}  [opts.discountPct]         % descuento comercial ya resuelto
 * @param {number}  [opts.quantity]            Cantidad de la línea
 * @returns {{ usedPoints:number, unitPrice:number, finalPrice:number, breakdown:string, hasExtras:boolean, vigaCost:number, cuts:string[] }}
 */
export function computeUnitPrice(product, opts = {}) {
  const {
    isManual = false,
    manualPoints = 0,
    library = 'ZC',
    module = 'montada',
    finishName,
    pointValue = 1.0,
    increments = { width: 0, height: 0, depth: 0 },
    carcassIncrement = 0,
    vigaIncrement = 0,
    hasVigaCut = false,
    customDims = {},
    showDistributorPrice = false,
    discountPct = 0,
    quantity = 1,
  } = opts;

  let usedPoints = 0;
  let carcassCost = 0;
  let cutsCost = 0;
  let cuts = [];

  if (isManual) {
    usedPoints = manualPoints || 0;
  } else {
    const isMV = library === 'MV';

    // Para MV, buscar en MV_TARIFFS; para ZC, buscar en DOOR_FINISHES
    const finishObj = isMV
      ? (MV_TARIFFS.find(f => f.name === finishName) || MV_TARIFFS[0])
      : (DOOR_FINISHES.find(f => f.name === finishName) || DOOR_FINISHES[0]);

    let productBasePoints = 100;
    if (typeof product.points === 'number') productBasePoints = product.points;
    else if (typeof product.points === 'object' && product.points !== null) {
      // Para MV usar T1, para ZC usar Z1
      productBasePoints = isMV
        ? (product.points.T1 || product.points.Z1 || 100)
        : (product.points.Z1 || 100);
    }

    usedPoints = product.zonePoints?.[finishObj.group] ?? productBasePoints;

    // NO aplicar incrementos por medidas en COSTADOS y REGLETAS
    const categoryUpper = (product.category || '').toUpperCase();
    const isExcludedCategory = categoryUpper.includes('COSTADO') || categoryUpper.includes('REGLETA');

    if (!isExcludedCategory) {
      // Solo se cobra corte cuando la medida a medida es MAYOR que la del
      // catálogo (corte que agranda). Un campo vacío/0 o una medida menor no
      // dispara el incremento.
      const bigger = (cd, base) => cd != null && cd !== '' && Number(cd) > 0 && Number(cd) > Number(base);
      if (bigger(customDims.width, product.width)) { cutsCost += increments.width; cuts.push('Ancho'); }
      if (bigger(customDims.height, product.height)) { cutsCost += increments.height; cuts.push('Alto'); }
      if (bigger(customDims.depth, product.depth)) { cutsCost += increments.depth; cuts.push('Fondo'); }
    }

    carcassCost = carcassIncrement || 0;
  }

  // Incremento por corte de viga (se calcula siempre; las líneas manuales lo
  // reflejan en hasExtras pero NO en unitPrice, igual que el original)
  const vigaCost = hasVigaCut ? (vigaIncrement || 0) : 0;

  // LÍNEAS MANUALES: el valor es directamente en €, NO se multiplica por punto
  // LÍNEAS DE LIBRERÍA: puntos × valor del punto + extras
  const pointsCost = isManual ? usedPoints : (usedPoints * pointValue);
  const unitPrice = isManual
    ? pointsCost // Manual: valor directo en €, sin extras ni incrementos
    : (pointsCost + cutsCost + carcassCost + vigaCost); // Librería: con extras

  // Las líneas manuales NUNCA tienen descuento ni se afectan por modo PVP/COSTO
  const discountFactor = isManual ? 1 : (showDistributorPrice ? (1 - discountPct / 100) : 1);

  const finalPrice = (unitPrice * quantity) * discountFactor;

  const breakdown = `
DESGLOSE DE PRECIO:
-------------------
${isManual ? `• Valor Manual: ${usedPoints.toFixed(2)} €` : `• Puntos Base: ${usedPoints} pts
• Valor Punto: ${pointValue.toFixed(2)} €/pt
  (Subtotal Mueble: ${pointsCost.toFixed(2)}€)`}

${!isManual ? `EXTRAS APLICADOS:
• Armazón: +${carcassCost.toFixed(2)}€
• Cortes Especiales (${cuts.length}): +${cutsCost.toFixed(2)}€${vigaCost > 0 ? `
• Corte Viga: +${vigaCost.toFixed(2)}€` : ''}` : '• (Artículo Manual / Neto)'}

PRECIO UNITARIO: ${unitPrice.toFixed(2)}€
CANTIDAD: x${quantity}
${showDistributorPrice ? `DTO. COMERCIAL (${module?.toUpperCase()}): -${discountPct}%` : ''}
`.trim();

  // 'sinPrecio': línea de librería sin puntos para la zona/tarifa activa, o sin
  // valor de punto válido → no se debe facturar; la UI debe avisar/bloquear.
  const sinPrecio = !isManual && (!(usedPoints > 0) || !(pointValue > 0));

  return {
    usedPoints,
    unitPrice,
    finalPrice,
    breakdown,
    hasExtras: (carcassCost > 0 || cutsCost > 0 || vigaCost > 0),
    vigaCost,
    cuts,
    sinPrecio,
  };
}

/**
 * Estimación de €/ml (mediana) sobre los módulos base de bajos, altos y
 * columnas del catálogo activo. Derivado del MISMO motor `computeUnitPrice`
 * (sin cortes a medida, sin dto), para usarse como pre-estimación cuando no
 * hay lista de módulos concreta (p.ej. Estudio 3D con solo medidas + estilo).
 *
 * @param {object[]} products  Productos del catálogo activo
 * @param {object} opts        Mismas opciones que computeUnitPrice (library, finishName, pointValue, ...)
 * @returns {number} mediana de €/ml (0 si no hay datos)
 */
export function avgEurPerMl(products = [], opts = {}) {
  const CATS = ['BAJO', 'ALTO', 'COLUMNA'];
  const values = [];

  for (const p of products) {
    const cat = (p.category || '').toUpperCase();
    if (!CATS.some(c => cat.includes(c))) continue;
    const w = Number(p.width);
    if (!w || w <= 0) continue;

    const { unitPrice } = computeUnitPrice(p, {
      ...opts,
      isManual: false,
      // Sin cortes a medida: dims iguales a las del producto
      customDims: { width: p.width, height: p.height, depth: p.depth },
      hasVigaCut: false,
      showDistributorPrice: false,
    });

    const ml = w / 100; // width en cm -> metros lineales
    if (ml > 0) values.push(unitPrice / ml);
  }

  if (values.length === 0) return 0;
  values.sort((a, b) => a - b);
  const mid = Math.floor(values.length / 2);
  return values.length % 2 !== 0
    ? values[mid]
    : (values[mid - 1] + values[mid]) / 2;
}
