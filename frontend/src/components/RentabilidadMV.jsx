/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Plus, Trash2, Loader, Calculator, TrendingUp, Upload, Lock, Unlock, Download } from 'lucide-react';
import { authHeaders } from '../services/api';
import { CASCOS } from '../data/cascos';
import { valorPuntoCascos, VALOR_PUNTO_CASCOS } from '../utils/valorPuntoCascos';
import { usePulsacionLarga, AYUDA_CANDADO } from '../utils/pulsacionLarga';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const H = () => authHeaders({ 'Content-Type': 'application/json' });
const eur = (n) => (Number(n) || 0).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' €';

// Mapeo de acabados de casco a su clave de color y grosor en el catálogo ACB
const MAP_CASCO_COLOR = {
  'grafito-19': { color: 'grafito', grosor: 19 },
  'Grafito Antracita (19mm)': { color: 'grafito', grosor: 19 },
  'blanco-hidro-19': { color: 'blancoHidrofugo', grosor: 19 },
  'Blanco Hidrófugo (19mm)': { color: 'blancoHidrofugo', grosor: 19 },
  'roble-aurora-19': { color: 'robleAurora', grosor: 19 },
  'Roble Aurora (19mm)': { color: 'robleAurora', grosor: 19 },
  'blanco-16': { color: 'blanco', grosor: 16 },
  'Blanco En Kit (16mm)': { color: 'blanco', grosor: 16 },
  'aluminio-16': { color: 'aluminio', grosor: 16 },
  'Aluminio Textura (16mm)': { color: 'aluminio', grosor: 16 },
  'spike-19': { color: 'spike', grosor: 19 },
  'Spike (19mm)': { color: 'spike', grosor: 19 },
  'stone-19': { color: 'stone', grosor: 19 },
  'Stone (19mm)': { color: 'stone', grosor: 19 },
  'roble-natural-16': { color: 'roble', grosor: 16 },
  'Roble Natural (Diseño Grueso 16mm)': { color: 'roble', grosor: 16 },
  'olmo-18': { color: 'olmo', grosor: 18 },
  'Olmo (Diseño Grueso 18mm)': { color: 'olmo', grosor: 18 },
};

// EL PRECIO DEL CASCO CUANDO EL ACABADO PEDIDO NO EXISTE EN ESA FAMILIA.
//
// El master, 30/08: «mira el precio del casco de la columna». Ponía 0,00 €.
//
// ACB NO FABRICA TODO EN TODAS LAS GAMAS, y eso no es un fallo de datos: es la
// tarifa. La «Columna Despensa» y la «Semicolumna Despensa» solo existen en
// Diseño Grueso (roble 16 / olmo 18) y Especiales Blanco 16 — no hay ni una en
// la gama «en kit» ni en 19 mm. Así que pedir una columna en grafito, que es el
// acabado POR DEFECTO, no encontraba precio.
//
// Y lo que hacía entonces era lo peor que se puede hacer: devolver CERO.
//
// Un cero no da error, no se ve raro y se suma sin protestar. En la columna del
// master eran 306,36 € de PVP con «73,9 % de margen» y un casco que en tarifa
// vale entre 128 y 306 €: el margen de verdad era una fracción de eso, o
// negativo. Un hueco se ve; un cero se cobra. Es la regla 7 de CLAUDE.md por su
// lado más caro: lo que no se sabe NO se rellena con un número plausible, y el
// cero es el más plausible de todos porque siempre cuadra.
//
// LA RESERVA ESTABA ESCRITA Y NO SE EJECUTABA NUNCA. `COLOR_PRIO` llevaba aquí
// desde el principio, y la función que tenía que recorrerla se quedó en un
// `return null` seco: se la llama SIEMPRE sin color (`precioColor(c)`), así que
// devolvía null siempre y la lista era decorado. El gemelo de esta función en
// `ProformaImporter.jsx` sí la recorre — o sea que esta es una copia a la que
// se le cayó el cuerpo, y nadie lo notó porque el resultado era un número.
const COLOR_PRIO = ['grafito', 'aluminio', 'blancoEsp', 'blanco', 'roble', 'olmo', 'stone', 'spike', 'blancoHidrofugo', 'robleAurora'];

/** Devuelve `{ precio, color }` o `null`. NUNCA cero: un casco que no está en
 *  tarifa no cuesta cero, es que no se sabe lo que cuesta. */
export const precioColor = (c, colorId) => {
  if (!c || !c.precios) return null;
  if (colorId && c.precios[colorId] != null) {
    return { precio: c.precios[colorId], color: colorId };
  }
  for (const col of COLOR_PRIO) {
    if (c.precios[col] != null) return { precio: c.precios[col], color: col };
  }
  // Y si el catálogo trae mañana un color que no está en la lista de arriba,
  // tampoco se tira el precio: se coge el que haya. Quedarse sin precio por no
  // haber actualizado una lista es volver al cero por otro camino.
  for (const col of Object.keys(c.precios)) {
    if (c.precios[col] != null) return { precio: c.precios[col], color: col };
  }
  return null;
};

// EL VALOR DEL PUNTO DE CASCOS vive en `utils/valorPuntoCascos.js`, para que lo
// puedan leer también Cocina Desmontada y App.js sin arrastrarse el
// Presupuestador entero. Se conserva el nombre viejo porque lo llaman
// `despiece` y la ficha del mueble.
export const getFactorDesmontada = () => valorPuntoCascos();

// Coste y PVP del casco ACB: precio neto de catálogo ACB × factor de Cocina Desmontada (Master)
export const cascoACB = (tipoAcb, ancho, alto, factor, acabadoCasco) => {
  const f = factor != null ? factor : getFactorDesmontada();
  const conf = MAP_CASCO_COLOR[acabadoCasco] || { color: 'grafito', grosor: 19 };
  const targetColor = conf.color;
  const targetGrosor = conf.grosor;

  const pool = CASCOS.filter(c => c.tipo === tipoAcb);
  // SIN PRECIO NO ES CERO. Si esa familia no está en el catálogo, no hay coste
  // que dar: se dice, y quien mire el presupuesto lo ve. Devolver cero es
  // decirle a quien vende que ese mueble sale gratis.
  if (!pool.length) return { coste: null, pvpDesmontada: null, med: '', sinPrecio: true };

  const porGrosor = pool.filter(c => c.grosor === targetGrosor);
  const usePool = porGrosor.length ? porGrosor : pool;

  // SE BUSCA EN DOS VUELTAS Y EN ESTE ORDEN, que importa: primero el acabado
  // que se ha pedido, y solo si esa familia NO se fabrica en él, el que haya.
  // Al revés, un mueble que sí existe en grafito podría acabar tarifado con el
  // precio de otra gama sin que nadie lo pidiera.
  const busca = (lista, color) => {
    let mejor = null, bd = Infinity;
    for (const c of lista) {
      const hit = precioColor(c, color);
      if (!hit) continue;
      // Solo vale si es EL color pedido, cuando se está pidiendo uno concreto.
      if (color && hit.color !== color) continue;
      const d = Math.abs((c.ancho || 0) - ancho) * 3 + Math.abs((c.alto || 0) - alto);
      if (d < bd) { bd = d; mejor = { ...c, pNeto: hit.precio, colorUsado: hit.color }; }
    }
    return mejor;
  };

  let best = busca(usePool, targetColor) || busca(pool, targetColor);
  let otroAcabado = null;
  if (!best) {
    // La familia no se fabrica en el acabado pedido. Se coge el precio REAL de
    // la gama en la que sí se fabrica y SE MARCA: es un precio de tarifa, no un
    // invento, pero no es el del acabado que se ha elegido y quien presupuesta
    // tiene que saberlo antes de fijar precio.
    best = busca(usePool, null) || busca(pool, null);
    if (best) otroAcabado = best.colorUsado;
  }

  if (!best || best.pNeto == null) {
    return { coste: null, pvpDesmontada: null, med: '', sinPrecio: true };
  }
  const precioNeto = best.pNeto;
  return {
    coste: Math.round(precioNeto * 100) / 100,
    pvpDesmontada: Math.round(precioNeto * f * 100) / 100,
    med: `${best.ancho}x${best.alto}`,
    sinPrecio: false,
    otroAcabado,          // el color realmente tarifado, si no era el pedido
    gamaUsada: best.gama,
  };
};

// Reglas de descomposición por familia MV
export const RULES = {
  BAJO: { casco: 'Bajo Con Balda', alto: 800, patas: 1, puertas: 'dio', baldas: 1 },
  BAJO_FREGADERO: { casco: 'Bajo Fregadero', alto: 800, patas: 1, puertas: 'dio' },
  BAJO_RINCON_CIEGO: { casco: 'Bajo Con Balda', alto: 800, patas: 1, puertas: 1 },
  BAJO_RINCON_ESCUADRA: { casco: 'Bajo Con Balda', alto: 800, patas: 1, puertas: 2 },
  BAJO_HORNO: { casco: 'Bajo Con Balda', alto: 800, patas: 1, puertas: 0, cajFn: c => /BHC|BHZ/.test(c) ? 1 : 0, gavFn: c => /BHG/.test(c) ? 1 : 0 },
  BAJO_TERMINAL: { casco: 'Bajo Con Balda', alto: 800, patas: 1, puertasFn: c => /BTP/.test(c) ? 1 : 0, baldas: 1 },
  BAJO_PUERTA_CAJON: { casco: 'Bajo Con Balda', alto: 800, patas: 1, puertas: 'dio', cajones: 1 },
  BAJO_5_CAJONES: { casco: 'Bajo Con Balda', alto: 800, patas: 1, puertas: 0, cajones: 5 },
  BAJO_3CAJ_1GAV: { casco: 'Bajo Con Balda', alto: 800, patas: 1, puertas: 0, cajones: 3, gavetas: 1 },
  BAJO_2GAV_1CAJ: { casco: 'Bajo Con Balda', alto: 800, patas: 1, puertas: 0, cajones: 1, gavetas: 2 },
  BAJO_2CAJ_1GAV_1FRENTE: { casco: 'Bajo Con Balda', alto: 800, patas: 1, puertas: 0, cajones: 2, gavetas: 1 },
  BAJO_2GAV_1FRENTE: { casco: 'Bajo Con Balda', alto: 800, patas: 1, puertas: 0, gavetas: 2 },
  ALTO: { casco: 'Alto Con Balda', altoSel: true, colg: 1, puertas: 'dio', baldasSel: true },
  ALTO_DECORATIVO: { casco: 'Alto Con Balda', altoSel: true, colg: 1, puertas: 0, baldasSel: true },
  ALTO_VITRINA: { casco: 'Alto Con Balda', altoSel: true, colg: 1, puertas: 'dio', vitrina: true },
  ALTO_ESCURREPLATOS: { casco: 'Alto Con Balda', altoSel: true, colg: 1, puertas: 'dio' },
  ALTO_MICROONDAS: { casco: 'Alto Con Balda', altoSel: true, colg: 1, puertas: 'dio' },
  ALTO_CAMPANA: { casco: 'Alto Con Balda', altoSel: true, colg: 1, puertas: 'dio' },
  ALTO_CALENTADOR: { casco: 'Alto Con Balda', altoSel: true, colg: 1, puertas: 'dio' },
  ALTO_CALDERA: { casco: 'Alto Con Balda', altoSel: true, colg: 1, puertas: 'dio' },
  ALTO_SOBREFRIGO: { casco: 'Alto Con Balda', altoSel: true, colg: 1, puertas: 'dio' },
  ALTO_TERMINAL: { casco: 'Alto Con Balda', altoSel: true, colg: 1, puertas: 1 },
  ALTO_RINCON_CIEGO: { casco: 'Alto Con Balda', altoSel: true, colg: 1, puertas: 1 },
  ALTO_RINCON_ESCUADRA: { casco: 'Alto Con Balda', altoSel: true, colg: 1, puertas: 2 },
  ALTO_RINCON_CHAFLAN: { casco: 'Alto Con Balda', altoSel: true, colg: 1, puertas: 1 },
  ALTO_ABATIBLE: { casco: 'Alto Con Balda', altoSel: true, colg: 1, puertas: 2 },
  ALTO_COMBINADO: { casco: 'Alto Con Balda', altoSel: true, colg: 1, puertas: 2 },
  ALTO_COMBINADO_PLUS: { casco: 'Alto Con Balda', altoSel: true, colg: 1, puertas: 2 },
  ALTO_COMBINADO_PLUS_J: { casco: 'Alto Con Balda', altoSel: true, colg: 1, puertas: 2 },
  ALTILLO: { casco: 'Alto Con Balda', altoSel: true, colg: 1, puertas: 1 },
  ALTILLO_VITRINA: { casco: 'Alto Con Balda', altoSel: true, colg: 1, puertas: 1, vitrina: true },
  COLUMNA_DESPENSERO: { casco: 'Columna Despensa', altoCol: true, patas: 1, puertas: 2, baldas: 4 },
  COLUMNA_FRIGO: { casco: 'Columna Despensa', altoCol: true, patas: 1, puertas: 2 },
  COLUMNA_HORNO: { casco: 'Columna Despensa', altoCol: true, patas: 1, puertas: 2 },
  COLUMNA_HORNO_MICRO: { casco: 'Columna Despensa', altoCol: true, patas: 1, puertas: 2 },
  MEDIACOLUMNA: { casco: 'Semicolumna Despensa', alto: 1300, patas: 1, puertas: 'dio', baldas: 2 },
  MEDIA_PUERTA_GAVETA: { casco: 'Semicolumna Despensa', alto: 1300, patas: 1, puertas: 1, gavetas: 1 },
  MEDIACOLUMNA_HORNO: { casco: 'Semicolumna Despensa', alto: 1300, patas: 1, puertas: 1 },
  MEDIACOLUMNA_VITRINA: { casco: 'Semicolumna Despensa', alto: 1300, patas: 1, puertas: 'dio', vitrina: true },
  MEDIACOL_VITRINA_GAVETA: { casco: 'Semicolumna Despensa', alto: 1300, patas: 1, puertas: 1, gavetas: 1, vitrina: true },
};
// LAS FAMILIAS QUE EL DESPIECE SABE DESGLOSAR DE VERDAD.
//
// Se exporta para que NADIE tenga que adivinarlo: la importación de proformas
// necesita saber si el tipo que trae el PDF se va a poder costear, y la pantalla
// necesita saber si el número que enseña es real o es el genérico.
//
// POR QUÉ HACE FALTA (30/08). `RULES[familia] || RULE_GENERICA` no devuelve «no
// se sabe» cuando la familia no existe: devuelve el coste de un «Bajo Con
// Balda» de 800 mm con una puerta y una pata. O sea que un PANEL de 150×400 se
// costeaba como un bajo estándar, y el número salía en pantalla con la misma
// pinta que uno de verdad. Rentabilidad lo marcaba con un «aprox» diminuto; el
// Presupuestador no lo marcaba en absoluto.
export const FAMILIAS_CON_DESPIECE = new Set(Object.keys(RULES));

export const tieneDespieceReal = (familia) =>
  FAMILIAS_CON_DESPIECE.has(String(familia || '').toUpperCase());

export const RULE_GENERICA = { casco: 'Bajo Con Balda', alto: 800, patas: 1, puertas: 1, generica: true };

// La mano de obra por mueble montado. Se exporta para que el candado la
// compare con `comisiones.MANO_DE_OBRA_POR_DEFECTO` del backend: si se
// separan, la pantalla calcula el margen con una cifra y la nomina paga con
// otra, y nadie ve un error.
export const MANO_DE_OBRA_POR_DEFECTO = 17;

// Costes por defecto de componentes MV (editables en la UI de Rentabilidad)
export const MV_COSTES_DEFAULT = {
  doorM2: 26,       // € por m² de puerta (tarifa base)
  bisagra: 3.07,    // € por bisagra (2 por puerta)
  pata4: 0.64,      // € por juego de 4 patas
  colgador: 3.50,   // € por colgador de mueble alto (2 por mueble)
  soporte: 0.30,    // € por soporte/balda (4 por balda)
  // 17 € por mueble MONTADO (master, 28/08). Es la cifra de la casa: cada
  // montador puede tener la suya en su ficha, y esa es la que cobra
  // (backend `services/comisiones.py`, `mano_de_obra_de`).
  mano: MANO_DE_OBRA_POR_DEFECTO,
  cajon: 41.34,     // € por cajón
  gaveta: 54.37,    // € por gaveta
  dtoCascos: 0,     // % descuento de compra sobre la tarifa ACB de cascos
  dtoPuertas1: 0,   // % descuento 1 sobre tarifa de puertas MV
  dtoPuertas2: 0,   // % descuento 2 (acumulado sobre el resultado del 1)
  dtoPuertas: 0,    // alias legado (compatibilidad)
};

// ─── COMISIONES DE LOS COOPERATIVISTAS ──────────────────────────────────────
//
// ESTO ES NÓMINA. Los tramos los dictó el master el 25/08/2026 y tienen que
// decir LO MISMO que `backend/services/comisiones.py`, que es donde vive el
// cálculo de verdad y donde están las pruebas. Hay un candado que compara las
// dos tablas: si se separan, la pantalla enseñaría una cifra y el cálculo daría
// otra — y aquí eso es que alguien cobra de menos.
//
//   valoración < 2.500 €      ->  20 € por mueble
//   de 2.500 € a 6.000 €      ->  30 € por mueble
//   de 6.000 € a 9.000 €      ->  40 € por mueble
//   de 9.000 € a 12.000 €     ->  50 € por mueble
//   de 12.000 € a 15.000 €    ->  60 € por mueble
//   de 15.000 € en adelante   ->  70 € por mueble
//   tope, pase lo que pase    ->  70 € por mueble
//
// El TOPE sube CON el tramo más alto. Si se quedara por detrás, el `Math.min`
// de abajo recortaría los tramos altos en silencio y el comercial cobraría
// menos de lo que dice esta tabla. Hoy vale lo mismo que el tramo de arriba, o
// sea que no recorta nada — y es a propósito: el master, 25/08, «70 tope de
// momento».
export const TRAMOS_COMISION_COMERCIAL = [
  { hasta: 2500, euros: 20 },
  { hasta: 6000, euros: 30 },
  { hasta: 9000, euros: 40 },
  { hasta: 12000, euros: 50 },
  { hasta: 15000, euros: 60 },
  { hasta: null, euros: 70 },
];
export const TOPE_COMISION_POR_MUEBLE = 70;

/** € por mueble que se lleva el comercial con esa valoración de pedido. */
export const comisionPorMueble = (valoracion) => {
  const v = Number(valoracion) || 0;
  for (const t of TRAMOS_COMISION_COMERCIAL) {
    // En el borde exacto (2.500, 6.000 o 9.000 clavados) se paga el de ARRIBA:
    // en la duda no se le quita dinero a quien vende. Igual que el backend.
    if (t.hasta === null || v < t.hasta) return Math.min(t.euros, TOPE_COMISION_POR_MUEBLE);
  }
  return Math.min(TRAMOS_COMISION_COMERCIAL[TRAMOS_COMISION_COMERCIAL.length - 1].euros,
                  TOPE_COMISION_POR_MUEBLE);
};

/**
 * 12000 -> «12.000 €», con el punto de los miles.
 *
 * A mano y no con `toLocaleString('es-ES')` a propósito: eso depende del ICU
 * del navegador y donde no esté completo devuelve «12,000 €» con coma. El
 * candado compara este rótulo con el del backend carácter a carácter, así que
 * tiene que salir igual siempre, en cualquier máquina.
 */
const eurosDelTramo = (v) => `${String(Math.round(v)).replace(/\B(?=(\d{3})+(?!\d))/g, '.')} €`;

/**
 * El rótulo del tramo, DERIVADO de la tabla de arriba.
 *
 * Antes era una cadena de `if` escritos a mano: los tramos otra vez, con otras
 * palabras. Y se rompió — al añadir el tramo de 9.000 € el importe pasó a 50 €
 * y el rótulo se quedó diciendo «más de 6.000 €». El número bien y la
 * explicación mintiendo, que es peor que no explicar nada. Derivándolo, añadir
 * un tramo no puede desincronizar el rótulo.
 */
/**
 * La escala entera en una frase, DERIVADA de la tabla.
 *
 * El párrafo que explicaba esto estaba escrito a mano y se quedó atrás: decía
 * «20 € por debajo de 2.500 €, 30 € hasta 6.000 €, 40 € por encima; tope de
 * 50 €» cuando ya había seis tramos y el tope era de 70 €. Es el mismo fallo
 * que ya tuvo el rótulo del tramo, y el mismo arreglo: si la escala se escribe
 * a mano en algún sitio, ese sitio acaba mintiendo. Y en nómina, una
 * explicación que miente es peor que ninguna, porque quien la lee se fía.
 */
export const escalaDeComisionEnPalabras = () => {
  const partes = TRAMOS_COMISION_COMERCIAL.map((t, i) => {
    const euros = `${Math.min(t.euros, TOPE_COMISION_POR_MUEBLE)} €`;
    if (t.hasta === null) return `${euros} por encima`;
    if (i === 0) return `${euros} por debajo de ${eurosDelTramo(t.hasta)}`;
    return `${euros} hasta ${eurosDelTramo(t.hasta)}`;
  });
  return `${partes.join(', ')}; tope de ${TOPE_COMISION_POR_MUEBLE} € por mueble`;
};

export const nombreDelTramo = (valoracion) => {
  const v = Number(valoracion) || 0;
  let anterior = null;
  for (const t of TRAMOS_COMISION_COMERCIAL) {
    if (t.hasta === null) break;
    // Borde exacto -> tramo de ARRIBA, igual que el backend.
    if (v < t.hasta) {
      return anterior === null
        ? `menos de ${eurosDelTramo(t.hasta)}`
        : `de ${eurosDelTramo(anterior)} a ${eurosDelTramo(t.hasta)}`;
    }
    anterior = t.hasta;
  }
  return anterior === null ? 'todos' : `más de ${eurosDelTramo(anterior)}`;
};

// Ancho (mm) del prefijo numérico del código
export const anchoDe = (cod) => {
  const m = /^[A-Z_]+(\d+)/.exec(cod || '');
  if (!m) return 600;
  const n = parseInt(m[1], 10);
  return n < 20 ? n * 100 : n * 10;
};

// Matriz Oficial de Puntos de Puertas MV por Tarifa (T1 a T5)
export const PUERTAS_MATRIZ_MV = {
  T1: {
    '14': { 'P30': 4, 'P35': 4, 'P40': 4, 'P45': 4, 'P50': 4, 'P60': 4 },
    '28': { 'P30': 5, 'P35': 6, 'P40': 6, 'P45': 7, 'P50': 7, 'P60': 8 },
    '40': { 'P30': 9, 'P35': 10, 'P40': 10, 'P45': 10, 'P50': 11, 'P60': 11 },
    '56': { 'P30': 10, 'P35': 11, 'P40': 11, 'P45': 11, 'P50': 13, 'P60': 13 },
    '70': { 'P25': 10, 'P30': 11, 'P35': 12, 'P40': 13, 'P45': 13, 'P50': 14, 'P60': 16 },
    '90': { 'P25': 13, 'P30': 14, 'P35': 15, 'P40': 15, 'P45': 16, 'P50': 17, 'P60': 19 },
    '127': { 'P30': 16, 'P35': 17, 'P40': 19, 'P45': 19, 'P50': 20, 'P60': 22 },
    '147': { 'P30': 19, 'P35': 20, 'P40': 21, 'P45': 22, 'P50': 23, 'P60': 26 },
  },
  T2: {
    '14': { 'P30': 11, 'P35': 11, 'P40': 12, 'P45': 13, 'P50': 15, 'P60': 16 },
    '28': { 'P30': 19, 'P35': 20, 'P40': 21, 'P45': 23, 'P50': 25, 'P60': 25 },
    '40': { 'P30': 21, 'P35': 23, 'P40': 26, 'P45': 27, 'P50': 28, 'P60': 32 },
    '56': { 'P30': 23, 'P35': 26, 'P40': 28, 'P45': 29, 'P50': 31, 'P60': 35 },
    '70': { 'P25': 28, 'P30': 28, 'P35': 30, 'P40': 32, 'P45': 35, 'P50': 37, 'P60': 43 },
    '90': { 'P25': 34, 'P30': 34, 'P35': 36, 'P40': 39, 'P45': 43, 'P50': 45, 'P60': 52 },
    '127': { 'P30': 41, 'P35': 49, 'P40': 51, 'P45': 54, 'P50': 67, 'P60': 68 },
    '147': { 'P30': 47, 'P35': 54, 'P40': 55, 'P45': 58, 'P50': 60, 'P60': 75 },
  },
  T3: {
    '14': { 'P30': 4, 'P35': 5, 'P40': 5, 'P45': 5, 'P50': 5, 'P60': 5 },
    '28': { 'P30': 7, 'P35': 8, 'P40': 9, 'P45': 9, 'P50': 10, 'P60': 11 },
    '40': { 'P30': 13, 'P35': 14, 'P40': 14, 'P45': 15, 'P50': 16, 'P60': 19 },
    '56': { 'P30': 14, 'P35': 15, 'P40': 16, 'P45': 17, 'P50': 19, 'P60': 20 },
    '70': { 'P25': 15, 'P30': 16, 'P35': 17, 'P40': 19, 'P45': 19, 'P50': 21, 'P60': 25 },
    '90': { 'P25': 19, 'P30': 20, 'P35': 22, 'P40': 23, 'P45': 25, 'P50': 26, 'P60': 29 },
    '127': { 'P30': 25, 'P35': 28, 'P40': 29, 'P45': 32, 'P50': 34, 'P60': 38 },
    '147': { 'P30': 29, 'P35': 32, 'P40': 34, 'P45': 36, 'P50': 39, 'P60': 44 },
  },
  T4: {
    '14': { 'P30': 8, 'P35': 9, 'P40': 9, 'P45': 10, 'P50': 10, 'P60': 11 },
    '28': { 'P30': 12, 'P35': 14, 'P40': 14, 'P45': 15, 'P50': 16, 'P60': 17 },
    '40': { 'P30': 16, 'P35': 17, 'P40': 18, 'P45': 20, 'P50': 21, 'P60': 24 },
    '56': { 'P30': 17, 'P35': 20, 'P40': 21, 'P45': 23, 'P50': 25, 'P60': 28 },
    '70': { 'P25': 18, 'P30': 19, 'P35': 21, 'P40': 22, 'P45': 25, 'P50': 27, 'P60': 32 },
    '90': { 'P25': 21, 'P30': 24, 'P35': 27, 'P40': 30, 'P45': 32, 'P50': 35, 'P60': 40 },
    '127': { 'P30': 33, 'P35': 37, 'P40': 41, 'P45': 46, 'P50': 49, 'P60': 55 },
    '147': { 'P30': 42, 'P35': 46, 'P40': 50, 'P45': 52, 'P50': 55, 'P60': 62 },
  },
  T5: {
    '14': { 'P30': 12, 'P35': 12, 'P40': 12, 'P45': 14, 'P50': 15, 'P60': 16 },
    '28': { 'P30': 15, 'P35': 18, 'P40': 18, 'P45': 18, 'P50': 21, 'P60': 22 },
    '40': { 'P30': 20, 'P35': 21, 'P40': 23, 'P45': 24, 'P50': 26, 'P60': 29 },
    '56': { 'P30': 24, 'P35': 26, 'P40': 27, 'P45': 30, 'P50': 33, 'P60': 37 },
    '70': { 'P25': 24, 'P30': 26, 'P35': 27, 'P40': 29, 'P45': 31, 'P50': 34, 'P60': 40 },
    '90': { 'P25': 31, 'P30': 32, 'P35': 34, 'P40': 37, 'P45': 39, 'P50': 41, 'P60': 48 },
    '127': { 'P30': 42, 'P35': 46, 'P40': 50, 'P45': 54, 'P50': 57, 'P60': 65 },
    '147': { 'P30': 46, 'P35': 49, 'P40': 54, 'P45': 59, 'P50': 62, 'P60': 69 },
  },
  T6: {
    '14': { 'P30': 11, 'P35': 13, 'P40': 15, 'P45': 16, 'P50': 17, 'P60': 20 },
    '28': { 'P30': 15, 'P35': 15, 'P40': 15, 'P45': 17, 'P50': 19, 'P60': 21 },
    '40': { 'P30': 18, 'P35': 20, 'P40': 22, 'P45': 25, 'P50': 26, 'P60': 30 },
    '56': { 'P30': 23, 'P35': 26, 'P40': 29, 'P45': 32, 'P50': 34, 'P60': 40 },
    '70': { 'P25': 26, 'P30': 26, 'P35': 29, 'P40': 33, 'P45': 36, 'P50': 39, 'P60': 47 },
    '90': { 'P25': 31, 'P30': 31, 'P35': 35, 'P40': 39, 'P45': 43, 'P50': 47, 'P60': 55 },
    '127': { 'P30': 39, 'P35': 45, 'P40': 50, 'P45': 55, 'P50': 60, 'P60': 69 },
    '147': { 'P30': 47, 'P35': 53, 'P40': 60, 'P45': 66, 'P50': 72, 'P60': 83 },
  },
  T7: {
    '14': { 'P30': 15, 'P35': 16, 'P40': 17, 'P45': 19, 'P50': 21, 'P60': 25 },
    '28': { 'P30': 19, 'P35': 19, 'P40': 19, 'P45': 20, 'P50': 23, 'P60': 26 },
    '40': { 'P30': 21, 'P35': 24, 'P40': 26, 'P45': 29, 'P50': 32, 'P60': 36 },
    '56': { 'P30': 27, 'P35': 31, 'P40': 34, 'P45': 38, 'P50': 42, 'P60': 49 },
    '70': { 'P25': 30, 'P30': 30, 'P35': 35, 'P40': 39, 'P45': 44, 'P50': 47, 'P60': 57 },
    '90': { 'P25': 37, 'P30': 37, 'P35': 42, 'P40': 47, 'P45': 52, 'P50': 57, 'P60': 67 },
    '127': { 'P30': 47, 'P35': 54, 'P40': 60, 'P45': 67, 'P50': 74, 'P60': 87 },
    '147': { 'P30': 57, 'P35': 64, 'P40': 72, 'P45': 81, 'P50': 88, 'P60': 105 },
  },
  T8: {
    '14': { 'P30': 21, 'P35': 22, 'P40': 23, 'P45': 25, 'P50': 26, 'P60': 28 },
    '28': { 'P30': 36, 'P35': 36, 'P40': 36, 'P45': 37, 'P50': 38, 'P60': 41 },
    '40': { 'P30': 39, 'P35': 41, 'P40': 41, 'P45': 44, 'P50': 45, 'P60': 53 },
    '56': { 'P30': 42, 'P35': 44, 'P40': 49, 'P45': 53, 'P50': 60, 'P60': 65 },
    '70': { 'P25': 49, 'P30': 49, 'P35': 54, 'P40': 59, 'P45': 64, 'P50': 70, 'P60': 82 },
    '90': { 'P25': 59, 'P30': 59, 'P35': 66, 'P40': 72, 'P45': 79, 'P50': 85, 'P60': 99 },
    '127': { 'P30': 82, 'P35': 92, 'P40': 101, 'P45': 117, 'P50': 126, 'P60': 145 },
    '147': { 'P30': 99, 'P35': 110, 'P40': 128, 'P45': 139, 'P50': 151, 'P60': 173 },
  },
  T9: {
    '14': { 'P30': 17, 'P35': 19, 'P40': 20, 'P45': 21, 'P50': 22, 'P60': 23 },
    '28': { 'P30': 25, 'P35': 25, 'P40': 25, 'P45': 26, 'P50': 26, 'P60': 29 },
    '40': { 'P30': 27, 'P35': 29, 'P40': 30, 'P45': 32, 'P50': 32, 'P60': 38 },
    '56': { 'P30': 31, 'P35': 32, 'P40': 35, 'P45': 38, 'P50': 42, 'P60': 45 },
    '70': { 'P25': 35, 'P30': 35, 'P35': 38, 'P40': 41, 'P45': 44, 'P50': 46, 'P60': 53 },
    '90': { 'P25': 41, 'P30': 41, 'P35': 45, 'P40': 48, 'P45': 51, 'P50': 54, 'P60': 61 },
    '127': { 'P30': 53, 'P35': 58, 'P40': 62, 'P45': 67, 'P50': 69, 'P60': 81 },
    '147': { 'P30': 63, 'P35': 70, 'P40': 75, 'P45': 80, 'P50': 89, 'P60': 97 },
  },
  T10: {
    '14': { 'P30': 21, 'P35': 22, 'P40': 23, 'P45': 25, 'P50': 26, 'P60': 27 },
    '28': { 'P30': 29, 'P35': 29, 'P40': 29, 'P45': 30, 'P50': 32, 'P60': 35 },
    '40': { 'P30': 32, 'P35': 34, 'P40': 36, 'P45': 38, 'P50': 38, 'P60': 45 },
    '56': { 'P30': 36, 'P35': 38, 'P40': 41, 'P45': 45, 'P50': 48, 'P60': 52 },
    '70': { 'P25': 41, 'P30': 41, 'P35': 45, 'P40': 47, 'P45': 51, 'P50': 54, 'P60': 61 },
    '90': { 'P25': 48, 'P30': 48, 'P35': 54, 'P40': 57, 'P45': 59, 'P50': 63, 'P60': 70 },
    '127': { 'P30': 61, 'P35': 67, 'P40': 71, 'P45': 76, 'P50': 84, 'P60': 94 },
    '147': { 'P30': 74, 'P35': 80, 'P40': 85, 'P45': 93, 'P50': 101, 'P60': 113 },
  },
  T11: {
    '14': { 'P30': 21, 'P35': 22, 'P40': 23, 'P45': 25, 'P50': 26, 'P60': 27 },
    '28': { 'P30': 32, 'P35': 32, 'P40': 32, 'P45': 33, 'P50': 34, 'P60': 39 },
    '40': { 'P30': 35, 'P35': 38, 'P40': 40, 'P45': 41, 'P50': 44, 'P60': 49 },
    '56': { 'P30': 39, 'P35': 41, 'P40': 45, 'P45': 49, 'P50': 52, 'P60': 56 },
    '70': { 'P25': 45, 'P30': 45, 'P35': 49, 'P40': 52, 'P45': 56, 'P50': 58, 'P60': 66 },
    '90': { 'P25': 53, 'P30': 53, 'P35': 57, 'P40': 62, 'P45': 59, 'P50': 65, 'P60': 77 },
    '127': { 'P30': 66, 'P35': 73, 'P40': 78, 'P45': 84, 'P50': 91, 'P60': 103 },
    '147': { 'P30': 79, 'P35': 87, 'P40': 94, 'P45': 101, 'P50': 110, 'P60': 123 },
  },
  T12: {
    '14': { 'P30': 11, 'P35': 11, 'P40': 11, 'P45': 12, 'P50': 12, 'P60': 13 },
    '28': { 'P30': 15, 'P35': 15, 'P40': 15, 'P45': 17, 'P50': 19, 'P60': 22 },
    '40': { 'P30': 23, 'P35': 26, 'P40': 29, 'P45': 32, 'P50': 35, 'P60': 41 },
    '56': { 'P30': 23, 'P35': 26, 'P40': 29, 'P45': 32, 'P50': 35, 'P60': 41 },
    '70': { 'P25': 28, 'P30': 28, 'P35': 31, 'P40': 35, 'P45': 38, 'P50': 42, 'P60': 51 },
    '90': { 'P25': 35, 'P30': 35, 'P35': 40, 'P40': 44, 'P45': 49, 'P50': 54, 'P60': 63 },
    '127': { 'P30': 47, 'P35': 54, 'P40': 61, 'P45': 68, 'P50': 75, 'P60': 88 },
    '147': { 'P30': 57, 'P35': 65, 'P40': 73, 'P45': 81, 'P50': 89, 'P60': 106 },
  },
  T13: {
    '14': { 'P30': 16, 'P35': 17, 'P40': 20, 'P45': 21, 'P50': 23, 'P60': 27 },
    '28': { 'P30': 28, 'P35': 28, 'P40': 28, 'P45': 33, 'P50': 35, 'P60': 41 },
    '40': { 'P30': 33, 'P35': 38, 'P40': 42, 'P45': 46, 'P50': 48, 'P60': 52 },
    '56': { 'P30': 46, 'P35': 48, 'P40': 52, 'P45': 58, 'P50': 64, 'P60': 71 },
    '70': { 'P25': 49, 'P30': 49, 'P35': 53, 'P40': 61, 'P45': 66, 'P50': 69, 'P60': 77 },
    '90': { 'P25': 60, 'P30': 60, 'P35': 64, 'P40': 68, 'P45': 74, 'P50': 82, 'P60': 96 },
    '127': { 'P30': 74, 'P35': 84, 'P40': 93, 'P45': 104, 'P50': 113, 'P60': 134 },
    '147': { 'P30': 88, 'P35': 100, 'P40': 112, 'P45': 125, 'P50': 135, 'P60': 161 },
  },
  T14: {
    '14': { 'P30': 20, 'P35': 22, 'P40': 23, 'P45': 24, 'P50': 26, 'P60': 28 },
    '28': { 'P30': 27, 'P35': 27, 'P40': 27, 'P45': 29, 'P50': 30, 'P60': 34 },
    '40': { 'P30': 36, 'P35': 39, 'P40': 42, 'P45': 45, 'P50': 48, 'P60': 54 },
    '56': { 'P30': 36, 'P35': 39, 'P40': 42, 'P45': 45, 'P50': 48, 'P60': 54 },
    '70': { 'P25': 42, 'P30': 42, 'P35': 45, 'P40': 49, 'P45': 52, 'P50': 56, 'P60': 64 },
    '90': { 'P25': 50, 'P30': 50, 'P35': 54, 'P40': 59, 'P45': 63, 'P50': 68, 'P60': 76 },
    '127': { 'P30': 68, 'P35': 74, 'P40': 79, 'P45': 85, 'P50': 92, 'P60': 104 },
    '147': { 'P30': 81, 'P35': 88, 'P40': 95, 'P45': 103, 'P50': 110, 'P60': 125 },
  },
  T15: {
    '14': { 'P30': 25, 'P35': 27, 'P40': 29, 'P45': 32, 'P50': 33, 'P60': 37 },
    '28': { 'P30': 37, 'P35': 37, 'P40': 37, 'P45': 40, 'P50': 43, 'P60': 47 },
    '40': { 'P30': 50, 'P35': 54, 'P40': 57, 'P45': 61, 'P50': 65, 'P60': 72 },
    '56': { 'P30': 50, 'P35': 54, 'P40': 57, 'P45': 61, 'P50': 65, 'P60': 72 },
    '70': { 'P25': 57, 'P30': 57, 'P35': 61, 'P40': 66, 'P45': 70, 'P50': 74, 'P60': 85 },
    '90': { 'P25': 69, 'P30': 69, 'P35': 74, 'P40': 79, 'P45': 85, 'P50': 90, 'P60': 100 },
    '127': { 'P30': 89, 'P35': 96, 'P40': 103, 'P45': 110, 'P50': 117, 'P60': 131 },
    '147': { 'P30': 107, 'P35': 116, 'P40': 124, 'P45': 132, 'P50': 141, 'P60': 158 },
  },
  T16: {
    '14': { 'P30': 15, 'P35': 16, 'P40': 17, 'P45': 18, 'P50': 21, 'P60': 25 },
    '28': { 'P30': 23, 'P35': 23, 'P40': 24, 'P45': 29, 'P50': 29, 'P60': 31 },
    '40': { 'P30': 27, 'P35': 29, 'P40': 31, 'P45': 33, 'P50': 35, 'P60': 39 },
    '56': { 'P30': 33, 'P35': 36, 'P40': 38, 'P45': 41, 'P50': 44, 'P60': 50 },
    '70': { 'P25': 36, 'P30': 37, 'P35': 40, 'P40': 44, 'P45': 47, 'P50': 50, 'P60': 57 },
    '90': { 'P25': 44, 'P30': 46, 'P35': 49, 'P40': 53, 'P45': 57, 'P50': 61, 'P60': 69 },
    '127': { 'P30': 59, 'P35': 64, 'P40': 70, 'P45': 75, 'P50': 80, 'P60': 91 },
    '147': { 'P30': 72, 'P35': 78, 'P40': 84, 'P45': 91, 'P50': 97, 'P60': 110 },
  },
  T17: {
    '14': { 'P30': 13, 'P35': 14, 'P40': 15, 'P45': 16, 'P50': 18, 'P60': 21 },
    '28': { 'P30': 23, 'P35': 23, 'P40': 24, 'P45': 30, 'P50': 30, 'P60': 31 },
    '40': { 'P30': 27, 'P35': 29, 'P40': 32, 'P45': 34, 'P50': 36, 'P60': 40 },
    '56': { 'P30': 34, 'P35': 37, 'P40': 40, 'P45': 43, 'P50': 46, 'P60': 53 },
    '70': { 'P25': 37, 'P30': 37, 'P35': 41, 'P40': 45, 'P45': 48, 'P50': 52, 'P60': 61 },
    '90': { 'P25': 47, 'P30': 48, 'P35': 51, 'P40': 55, 'P45': 60, 'P50': 64, 'P60': 72 },
    '127': { 'P30': 60, 'P35': 67, 'P40': 73, 'P45': 79, 'P50': 86, 'P60': 98 },
    '147': { 'P30': 74, 'P35': 81, 'P40': 89, 'P45': 97, 'P50': 104, 'P60': 120 },
  },
  T18: {
    '14': { 'P30': 16, 'P35': 17, 'P40': 18, 'P45': 20, 'P50': 22, 'P60': 26 },
    '28': { 'P30': 24, 'P35': 25, 'P40': 25, 'P45': 30, 'P50': 31, 'P60': 33 },
    '40': { 'P30': 28, 'P35': 30, 'P40': 33, 'P45': 35, 'P50': 37, 'P60': 42 },
    '56': { 'P30': 35, 'P35': 38, 'P40': 41, 'P45': 44, 'P50': 47, 'P60': 53 },
    '70': { 'P25': 38, 'P30': 39, 'P35': 43, 'P40': 46, 'P45': 50, 'P50': 53, 'P60': 61 },
    '90': { 'P25': 46, 'P30': 48, 'P35': 52, 'P40': 57, 'P45': 61, 'P50': 65, 'P60': 74 },
    '127': { 'P30': 63, 'P35': 69, 'P40': 74, 'P45': 80, 'P50': 85, 'P60': 97 },
    '147': { 'P30': 76, 'P35': 83, 'P40': 90, 'P45': 96, 'P50': 103, 'P60': 117 },
  },
  T19: {
    '14': { 'P30': 18, 'P35': 19, 'P40': 20, 'P45': 22, 'P50': 24, 'P60': 29 },
    '28': { 'P30': 27, 'P35': 28, 'P40': 28, 'P45': 33, 'P50': 34, 'P60': 37 },
    '40': { 'P30': 31, 'P35': 33, 'P40': 37, 'P45': 39, 'P50': 41, 'P60': 47 },
    '56': { 'P30': 39, 'P35': 42, 'P40': 46, 'P45': 49, 'P50': 52, 'P60': 59 },
    '70': { 'P25': 42, 'P30': 43, 'P35': 48, 'P40': 51, 'P45': 56, 'P50': 59, 'P60': 68 },
    '90': { 'P25': 51, 'P30': 53, 'P35': 58, 'P40': 63, 'P45': 68, 'P50': 72, 'P60': 82 },
    '127': { 'P30': 70, 'P35': 77, 'P40': 82, 'P45': 89, 'P50': 94, 'P60': 108 },
    '147': { 'P30': 84, 'P35': 92, 'P40': 100, 'P45': 107, 'P50': 114, 'P60': 130 },
  },
  T20: {
    '14': { 'P30': 20, 'P35': 22, 'P40': 23, 'P45': 26, 'P50': 28, 'P60': 33 },
    '28': { 'P30': 31, 'P35': 32, 'P40': 32, 'P45': 38, 'P50': 40, 'P60': 42 },
    '40': { 'P30': 36, 'P35': 38, 'P40': 42, 'P45': 45, 'P50': 47, 'P60': 54 },
    '56': { 'P30': 45, 'P35': 49, 'P40': 52, 'P45': 56, 'P50': 60, 'P60': 68 },
    '70': { 'P25': 49, 'P30': 50, 'P35': 55, 'P40': 59, 'P45': 64, 'P50': 68, 'P60': 78 },
    '90': { 'P25': 59, 'P30': 61, 'P35': 67, 'P40': 73, 'P45': 78, 'P50': 83, 'P60': 95 },
    '127': { 'P30': 81, 'P35': 88, 'P40': 95, 'P45': 102, 'P50': 109, 'P60': 124 },
    '147': { 'P30': 97, 'P35': 106, 'P40': 115, 'P45': 123, 'P50': 132, 'P60': 150 },
  },
  T21: {
    '14': { 'P30': 24, 'P35': 26, 'P40': 27, 'P45': 30, 'P50': 33, 'P60': 39 },
    '28': { 'P30': 36, 'P35': 38, 'P40': 38, 'P45': 45, 'P50': 46, 'P60': 50 },
    '40': { 'P30': 42, 'P35': 45, 'P40': 50, 'P45': 52, 'P50': 56, 'P60': 63 },
    '56': { 'P30': 52, 'P35': 57, 'P40': 62, 'P45': 66, 'P50': 70, 'P60': 80 },
    '70': { 'P25': 57, 'P30': 58, 'P35': 64, 'P40': 69, 'P45': 75, 'P50': 80, 'P60': 92 },
    '90': { 'P25': 69, 'P30': 72, 'P35': 78, 'P40': 86, 'P45': 92, 'P50': 98, 'P60': 111 },
    '127': { 'P30': 94, 'P35': 104, 'P40': 111, 'P45': 120, 'P50': 128, 'P60': 146 },
    '147': { 'P30': 114, 'P35': 124, 'P40': 135, 'P45': 144, 'P50': 154, 'P60': 176 },
  },
};

export const VITRINA_MATRIZ_MV = {
  T1: {
    '28': { 'PV30': 20, 'PV35': 22, 'PV40': 23, 'PV45': 24, 'PV50': 25, 'PV60': 28 },
    '40': { 'PV30': 34, 'PV35': 36, 'PV40': 37, 'PV45': 38, 'PV50': 40, 'PV60': 42 },
    '70': { 'PV30': 40, 'PV35': 43, 'PV40': 45, 'PV45': 47, 'PV50': 49, 'PV60': 54 },
    '90': { 'PV30': 49, 'PV35': 52, 'PV40': 54, 'PV45': 57, 'PV50': 59, 'PV60': 65 },
    '127': { 'PV30': 68, 'PV35': 72, 'PV40': 76, 'PV45': 81, 'PV50': 85, 'PV60': 89 },
    '147': { 'PV30': 77, 'PV35': 82, 'PV40': 87, 'PV45': 92, 'PV50': 97, 'PV60': 118 },
  },
  T2: {
    '28': { 'PV30': 33, 'PV35': 35, 'PV40': 37, 'PV45': 41, 'PV50': 44, 'PV60': 45 },
    '40': { 'PV30': 43, 'PV35': 47, 'PV40': 51, 'PV45': 53, 'PV50': 56, 'PV60': 63 },
    '70': { 'PV30': 57, 'PV35': 61, 'PV40': 64, 'PV45': 69, 'PV50': 73, 'PV60': 80 },
    '90': { 'PV30': 69, 'PV35': 73, 'PV40': 77, 'PV45': 83, 'PV50': 87, 'PV60': 99 },
    '127': { 'PV30': 92, 'PV35': 106, 'PV40': 110, 'PV45': 115, 'PV50': 132, 'PV60': 135 },
    '147': { 'PV30': 106, 'PV35': 116, 'PV40': 121, 'PV45': 128, 'PV50': 133, 'PV60': 147 },
  },
  T3: {
    '28': { 'PV30': 20, 'PV35': 22, 'PV40': 25, 'PV45': 26, 'PV50': 28, 'PV60': 30 },
    '40': { 'PV30': 35, 'PV35': 38, 'PV40': 39, 'PV45': 41, 'PV50': 44, 'PV60': 50 },
    '70': { 'PV30': 45, 'PV35': 48, 'PV40': 51, 'PV45': 53, 'PV50': 57, 'PV60': 62 },
    '90': { 'PV30': 55, 'PV35': 59, 'PV40': 61, 'PV45': 65, 'PV50': 68, 'PV60': 76 },
    '127': { 'PV30': 76, 'PV35': 83, 'PV40': 88, 'PV45': 93, 'PV50': 99, 'PV60': 105 },
    '147': { 'PV30': 88, 'PV35': 94, 'PV40': 100, 'PV45': 106, 'PV50': 112, 'PV60': 136 },
  },
  T4: {
    '28': { 'PV30': 29, 'PV35': 32, 'PV40': 33, 'PV45': 35, 'PV50': 36, 'PV60': 37 },
    '40': { 'PV30': 32, 'PV35': 33, 'PV40': 35, 'PV45': 42, 'PV50': 43, 'PV60': 50 },
    '70': { 'PV30': 42, 'PV35': 47, 'PV40': 50, 'PV45': 55, 'PV50': 60, 'PV60': 69 },
    '90': { 'PV30': 55, 'PV35': 58, 'PV40': 62, 'PV45': 70, 'PV50': 75, 'PV60': 85 },
    '127': { 'PV30': 74, 'PV35': 81, 'PV40': 88, 'PV45': 95, 'PV50': 103, 'PV60': 113 },
    '147': { 'PV30': 89, 'PV35': 94, 'PV40': 102, 'PV45': 108, 'PV50': 115, 'PV60': 128 },
  },
  T5: {
    '28': { 'PV30': 25, 'PV35': 29, 'PV40': 30, 'PV45': 31, 'PV50': 32, 'PV60': 34 },
    '40': { 'PV30': 37, 'PV35': 40, 'PV40': 42, 'PV45': 44, 'PV50': 49, 'PV60': 51 },
    '70': { 'PV30': 49, 'PV35': 52, 'PV40': 57, 'PV45': 61, 'PV50': 67, 'PV60': 77 },
    '90': { 'PV30': 62, 'PV35': 67, 'PV40': 72, 'PV45': 77, 'PV50': 82, 'PV60': 92 },
    '127': { 'PV30': 83, 'PV35': 89, 'PV40': 97, 'PV45': 104, 'PV50': 111, 'PV60': 123 },
    '147': { 'PV30': 93, 'PV35': 100, 'PV40': 109, 'PV45': 117, 'PV50': 124, 'PV60': 139 },
  },
  T6: {
    '28': { 'PV30': 24, 'PV35': 25, 'PV40': 26, 'PV45': 27, 'PV50': 29, 'PV60': 34 },
    '40': { 'PV30': 29, 'PV35': 33, 'PV40': 36, 'PV45': 39, 'PV50': 42, 'PV60': 49 },
    '70': { 'PV30': 38, 'PV35': 44, 'PV40': 50, 'PV45': 56, 'PV50': 62, 'PV60': 74 },
    '90': { 'PV30': 46, 'PV35': 54, 'PV40': 61, 'PV45': 65, 'PV50': 76, 'PV60': 88 },
    '127': { 'PV30': 60, 'PV35': 70, 'PV40': 81, 'PV45': 91, 'PV50': 101, 'PV60': 115 },
    '147': { 'PV30': 72, 'PV35': 84, 'PV40': 96, 'PV45': 105, 'PV50': 121, 'PV60': 138 },
  },
  T7: {
    '28': { 'PV30': 28, 'PV35': 28, 'PV40': 29, 'PV45': 29, 'PV50': 36, 'PV60': 39 },
    '40': { 'PV30': 32, 'PV35': 36, 'PV40': 39, 'PV45': 44, 'PV50': 47, 'PV60': 55 },
    '70': { 'PV30': 44, 'PV35': 51, 'PV40': 58, 'PV45': 65, 'PV50': 72, 'PV60': 85 },
    '90': { 'PV30': 53, 'PV35': 62, 'PV40': 71, 'PV45': 79, 'PV50': 88, 'PV60': 102 },
    '127': { 'PV30': 70, 'PV35': 82, 'PV40': 93, 'PV45': 105, 'PV50': 117, 'PV60': 137 },
    '147': { 'PV30': 83, 'PV35': 97, 'PV40': 112, 'PV45': 126, 'PV50': 140, 'PV60': 164 },
  },
  T8: {
    '28': { 'PV30': 51, 'PV35': 51, 'PV40': 52, 'PV45': 52, 'PV50': 53, 'PV60': 58 },
    '40': { 'PV30': 55, 'PV35': 57, 'PV40': 58, 'PV45': 62, 'PV50': 63, 'PV60': 74 },
    '70': { 'PV30': 65, 'PV35': 74, 'PV40': 82, 'PV45': 90, 'PV50': 99, 'PV60': 115 },
    '90': { 'PV30': 80, 'PV35': 91, 'PV40': 101, 'PV45': 112, 'PV50': 122, 'PV60': 141 },
    '127': { 'PV30': 112, 'PV35': 127, 'PV40': 149, 'PV45': 164, 'PV50': 179, 'PV60': 205 },
    '147': { 'PV30': 134, 'PV35': 152, 'PV40': 179, 'PV45': 197, 'PV50': 215, 'PV60': 247 },
  },
  T9: {
    '28': { 'PV30': 42, 'PV35': 43, 'PV40': 44, 'PV45': 45, 'PV50': 46, 'PV60': 52 },
    '40': { 'PV30': 48, 'PV35': 52, 'PV40': 52, 'PV45': 56, 'PV50': 57, 'PV60': 67 },
    '70': { 'PV30': 61, 'PV35': 66, 'PV40': 72, 'PV45': 78, 'PV50': 83, 'PV60': 95 },
    '90': { 'PV30': 72, 'PV35': 79, 'PV40': 86, 'PV45': 92, 'PV50': 99, 'PV60': 110 },
    '127': { 'PV30': 94, 'PV35': 104, 'PV40': 112, 'PV45': 121, 'PV50': 133, 'PV60': 145 },
    '147': { 'PV30': 112, 'PV35': 123, 'PV40': 132, 'PV45': 143, 'PV50': 157, 'PV60': 171 },
  },
  T10: {
    '28': { 'PV30': 50, 'PV35': 50, 'PV40': 51, 'PV45': 52, 'PV50': 54, 'PV60': 60 },
    '40': { 'PV30': 54, 'PV35': 58, 'PV40': 62, 'PV45': 65, 'PV50': 67, 'PV60': 77 },
    '70': { 'PV30': 68, 'PV35': 75, 'PV40': 80, 'PV45': 87, 'PV50': 92, 'PV60': 104 },
    '90': { 'PV30': 81, 'PV35': 90, 'PV40': 96, 'PV45': 102, 'PV50': 109, 'PV60': 121 },
    '127': { 'PV30': 105, 'PV35': 114, 'PV40': 123, 'PV45': 134, 'PV50': 145, 'PV60': 161 },
    '147': { 'PV30': 124, 'PV35': 136, 'PV40': 145, 'PV45': 158, 'PV50': 171, 'PV60': 190 },
  },
  T11: {
    '28': { 'PV30': 53, 'PV35': 53, 'PV40': 54, 'PV45': 55, 'PV50': 57, 'PV60': 64 },
    '40': { 'PV30': 58, 'PV35': 62, 'PV40': 66, 'PV45': 68, 'PV50': 69, 'PV60': 81 },
    '70': { 'PV30': 72, 'PV35': 79, 'PV40': 85, 'PV45': 92, 'PV50': 98, 'PV60': 111 },
    '90': { 'PV30': 86, 'PV35': 94, 'PV40': 102, 'PV45': 108, 'PV50': 116, 'PV60': 129 },
    '127': { 'PV30': 111, 'PV35': 121, 'PV40': 131, 'PV45': 142, 'PV50': 154, 'PV60': 172 },
    '147': { 'PV30': 131, 'PV35': 144, 'PV40': 155, 'PV45': 168, 'PV50': 182, 'PV60': 203 },
  },
  T12: {
    '28': { 'PV30': 20, 'PV35': 20, 'PV40': 21, 'PV45': 23, 'PV50': 25, 'PV60': 28 },
    '40': { 'PV30': 30, 'PV35': 34, 'PV40': 38, 'PV45': 42, 'PV50': 45, 'PV60': 53 },
    '70': { 'PV30': 34, 'PV35': 39, 'PV40': 44, 'PV45': 50, 'PV50': 54, 'PV60': 65 },
    '90': { 'PV30': 43, 'PV35': 50, 'PV40': 56, 'PV45': 63, 'PV50': 70, 'PV60': 81 },
    '127': { 'PV30': 58, 'PV35': 68, 'PV40': 78, 'PV45': 88, 'PV50': 97, 'PV60': 114 },
    '147': { 'PV30': 70, 'PV35': 82, 'PV40': 93, 'PV45': 105, 'PV50': 117, 'PV60': 136 },
  },
  T13: {
    '28': { 'PV30': 34, 'PV35': 34, 'PV40': 35, 'PV45': 39, 'PV50': 42, 'PV60': 49 },
    '40': { 'PV30': 40, 'PV35': 45, 'PV40': 50, 'PV45': 56, 'PV50': 58, 'PV60': 63 },
    '70': { 'PV30': 53, 'PV35': 59, 'PV40': 68, 'PV45': 74, 'PV50': 79, 'PV60': 88 },
    '90': { 'PV30': 66, 'PV35': 71, 'PV40': 78, 'PV45': 85, 'PV50': 96, 'PV60': 111 },
    '127': { 'PV30': 81, 'PV35': 95, 'PV40': 107, 'PV45': 120, 'PV50': 132, 'PV60': 155 },
    '147': { 'PV30': 97, 'PV35': 113, 'PV40': 127, 'PV45': 144, 'PV50': 158, 'PV60': 186 },
  },
  T14: {
    '28': { 'PV30': 31, 'PV35': 32, 'PV40': 33, 'PV45': 34, 'PV50': 35, 'PV60': 39 },
    '40': { 'PV30': 41, 'PV35': 45, 'PV40': 48, 'PV45': 51, 'PV50': 55, 'PV60': 62 },
    '70': { 'PV30': 47, 'PV35': 52, 'PV40': 57, 'PV45': 62, 'PV50': 68, 'PV60': 77 },
    '90': { 'PV30': 56, 'PV35': 63, 'PV40': 69, 'PV45': 76, 'PV50': 82, 'PV60': 93 },
    '127': { 'PV30': 76, 'PV35': 85, 'PV40': 95, 'PV45': 104, 'PV50': 113, 'PV60': 128 },
    '147': { 'PV30': 91, 'PV35': 102, 'PV40': 113, 'PV45': 125, 'PV50': 136, 'PV60': 154 },
  },
  T15: {
    '28': { 'PV30': 39, 'PV35': 39, 'PV40': 40, 'PV45': 41, 'PV50': 45, 'PV60': 50 },
    '40': { 'PV30': 52, 'PV35': 57, 'PV40': 60, 'PV45': 64, 'PV50': 68, 'PV60': 76 },
    '70': { 'PV30': 58, 'PV35': 64, 'PV40': 70, 'PV45': 76, 'PV50': 82, 'PV60': 93 },
    '90': { 'PV30': 71, 'PV35': 78, 'PV40': 85, 'PV45': 92, 'PV50': 100, 'PV60': 111 },
    '127': { 'PV30': 93, 'PV35': 103, 'PV40': 113, 'PV45': 123, 'PV50': 133, 'PV60': 149 },
    '147': { 'PV30': 111, 'PV35': 123, 'PV40': 135, 'PV45': 147, 'PV50': 159, 'PV60': 179 },
  },
  T16: {
    '28': { 'PV30': 36, 'PV35': 37, 'PV40': 38, 'PV45': 46, 'PV50': 47, 'PV60': 49 },
    '40': { 'PV30': 42, 'PV35': 46, 'PV40': 49, 'PV45': 52, 'PV50': 56, 'PV60': 63 },
    '70': { 'PV30': 58, 'PV35': 62, 'PV40': 64, 'PV45': 67, 'PV50': 69, 'PV60': 76 },
    '90': { 'PV30': 69, 'PV35': 72, 'PV40': 74, 'PV45': 79, 'PV50': 81, 'PV60': 86 },
    '127': { 'PV30': 83, 'PV35': 86, 'PV40': 90, 'PV45': 95, 'PV50': 98, 'PV60': 105 },
    '147': { 'PV30': 98, 'PV35': 101, 'PV40': 105, 'PV45': 112, 'PV50': 115, 'PV60': 123 },
  },
  T17: {
    '28': { 'PV30': 27, 'PV35': 28, 'PV40': 29, 'PV45': 36, 'PV50': 37, 'PV60': 37 },
    '40': { 'PV30': 32, 'PV35': 35, 'PV40': 38, 'PV45': 41, 'PV50': 43, 'PV60': 48 },
    '70': { 'PV30': 40, 'PV35': 43, 'PV40': 47, 'PV45': 51, 'PV50': 55, 'PV60': 62 },
    '90': { 'PV30': 48, 'PV35': 53, 'PV40': 58, 'PV45': 62, 'PV50': 67, 'PV60': 74 },
    '127': { 'PV30': 62, 'PV35': 69, 'PV40': 75, 'PV45': 82, 'PV50': 88, 'PV60': 97 },
    '147': { 'PV30': 74, 'PV35': 82, 'PV40': 90, 'PV45': 97, 'PV50': 106, 'PV60': 116 },
  },
  T18: {
    '28': { 'PV30': 38, 'PV35': 39, 'PV40': 40, 'PV45': 49, 'PV50': 50, 'PV60': 52 },
    '40': { 'PV30': 45, 'PV35': 49, 'PV40': 52, 'PV45': 56, 'PV50': 59, 'PV60': 67 },
    '70': { 'PV30': 62, 'PV35': 66, 'PV40': 68, 'PV45': 71, 'PV50': 73, 'PV60': 81 },
    '90': { 'PV30': 74, 'PV35': 76, 'PV40': 79, 'PV45': 84, 'PV50': 87, 'PV60': 92 },
    '127': { 'PV30': 88, 'PV35': 92, 'PV40': 95, 'PV45': 101, 'PV50': 105, 'PV60': 112 },
    '147': { 'PV30': 104, 'PV35': 108, 'PV40': 112, 'PV45': 119, 'PV50': 123, 'PV60': 131 },
  },
  T19: {
    '28': { 'PV30': 42, 'PV35': 43, 'PV40': 44, 'PV45': 54, 'PV50': 56, 'PV60': 58 },
    '40': { 'PV30': 50, 'PV35': 54, 'PV40': 58, 'PV45': 62, 'PV50': 65, 'PV60': 74 },
    '70': { 'PV30': 69, 'PV35': 73, 'PV40': 75, 'PV45': 79, 'PV50': 81, 'PV60': 90 },
    '90': { 'PV30': 82, 'PV35': 84, 'PV40': 88, 'PV45': 93, 'PV50': 97, 'PV60': 102 },
    '127': { 'PV30': 98, 'PV35': 102, 'PV40': 105, 'PV45': 112, 'PV50': 117, 'PV60': 124 },
    '147': { 'PV30': 115, 'PV35': 120, 'PV40': 124, 'PV45': 132, 'PV50': 137, 'PV60': 145 },
  },
  T20: {
    '28': { 'PV30': 49, 'PV35': 50, 'PV40': 51, 'PV45': 63, 'PV50': 64, 'PV60': 67 },
    '40': { 'PV30': 58, 'PV35': 63, 'PV40': 67, 'PV45': 72, 'PV50': 76, 'PV60': 86 },
    '70': { 'PV30': 79, 'PV35': 84, 'PV40': 87, 'PV45': 91, 'PV50': 93, 'PV60': 104 },
    '90': { 'PV30': 95, 'PV35': 97, 'PV40': 101, 'PV45': 108, 'PV50': 111, 'PV60': 118 },
    '127': { 'PV30': 113, 'PV35': 118, 'PV40': 122, 'PV45': 129, 'PV50': 134, 'PV60': 143 },
    '147': { 'PV30': 133, 'PV35': 138, 'PV40': 143, 'PV45': 152, 'PV50': 157, 'PV60': 168 },
  },
  T21: {
    '28': { 'PV30': 57, 'PV35': 58, 'PV40': 60, 'PV45': 74, 'PV50': 75, 'PV60': 78 },
    '40': { 'PV30': 68, 'PV35': 74, 'PV40': 78, 'PV45': 84, 'PV50': 88, 'PV60': 100 },
    '70': { 'PV30': 93, 'PV35': 99, 'PV40': 102, 'PV45': 106, 'PV50': 110, 'PV60': 122 },
    '90': { 'PV30': 111, 'PV35': 114, 'PV40': 118, 'PV45': 126, 'PV50': 130, 'PV60': 138 },
    '127': { 'PV30': 132, 'PV35': 138, 'PV40': 142, 'PV45': 152, 'PV50': 158, 'PV60': 168 },
    '147': { 'PV30': 156, 'PV35': 162, 'PV40': 168, 'PV45': 178, 'PV50': 184, 'PV60': 196 },
  },
};

/**
 * Puntos de una puerta segun la TARIFA OFICIAL. Devuelve `null` cuando no hay
 * dato, y eso es a proposito.
 *
 * Antes tenia tres redes de seguridad que tapaban el agujero en vez de
 * enseñarlo, y las tres cobraban de menos o de mas sin avisar:
 *
 *   `PUERTAS_MATRIZ_MV[tariff] || .T1`  -> 16 tarifas cobrando precios de T1.
 *   `tMat[hKey] || tMat['70']`          -> una altura que falta cobraba como 70.
 *   `row[wKey] || ... || 16`            -> un ancho que falta cobraba 16 puntos
 *                                          sacados de la nada.
 *
 * Un presupuesto con una casilla vacia se arregla mirandola. Un presupuesto con
 * un numero inventado no se arregla nunca, porque nadie sabe que esta mal.
 */
/**
 * Busca en una matriz de la tarifa (puertas o vitrinas). `null` = no hay dato.
 * Una sola funcion para las dos: si cada una tuviera la suya, acabarian
 * redondeando distinto y una vitrina y su puerta no cuadrarian.
 */
const puntosDeMatriz = (matriz, altoCm, anchoCm, tariff, prefijo) => {
  const tMat = matriz[tariff];
  if (!tMat) return null;

  let hKey = '70';
  if (altoCm <= 20) hKey = '14';
  else if (altoCm <= 35) hKey = '28';
  else if (altoCm <= 48) hKey = '40';
  else if (altoCm <= 60) hKey = '56';
  else if (altoCm <= 78) hKey = '70';
  else if (altoCm <= 100) hKey = '90';
  else if (altoCm <= 135) hKey = '127';
  else hKey = '147';

  const row = tMat[hKey];
  if (!row) return null;

  // El ancho se redondea HACIA ARRIBA: una puerta de 55 se corta de un tablero
  // de 60, no de uno de 50. Antes se cogia el mas cercano y en los empates
  // ganaba el pequeño, o sea que se cobraba una puerta mas estrecha de la que
  // hay que fabricar.
  const anchosDisp = [25, 30, 35, 40, 45, 50, 60];
  const cabe = anchosDisp.filter(w => w >= anchoCm && row[`${prefijo}${w}`] != null);
  if (cabe.length) return row[`${prefijo}${cabe[0]}`];

  // Mas ancha que el mayor de la tarifa: se cobra el mayor que exista, que es
  // lo unico defendible, pero nunca un numero inventado.
  const mayor = [...anchosDisp].reverse().find(w => row[`${prefijo}${w}`] != null);
  return mayor ? row[`${prefijo}${mayor}`] : null;
};

export const getPuntosPuertaMV = (altoCm, anchoCm, tariff = 'T1') =>
  puntosDeMatriz(PUERTAS_MATRIZ_MV, altoCm, anchoCm, tariff, 'P');

/**
 * Puntos de un frente de VITRINA, de SU tabla de la tarifa.
 *
 * Antes se calculaba como «puerta x 1,3», un recargo inventado que no se parece
 * a la tarifa en ninguna parte: en T1 salia el 35% de lo que toca (una vitrina
 * de 70x30 son 40 puntos y se cobraban 14), en T11 el 79%, y en T21 grande se
 * pasaba hasta el 113%. La tabla de VITRINA lleva ahi todo el tiempo.
 */
export const getPuntosVitrinaMV = (altoCm, anchoCm, tariff = 'T1') =>
  puntosDeMatriz(VITRINA_MATRIZ_MV, altoCm, anchoCm, tariff, 'PV');

export const getDescuentoPuertas = () => {
  try {
    const rawVal = localStorage.getItem('dto_puertas');
    if (rawVal != null) return parseFloat(rawVal) || 50;
    const st = JSON.parse(localStorage.getItem('app_state') || '{}');
    if (st?.discountPuertas != null) return parseFloat(st.discountPuertas) || 50;
    return 50;
  } catch {
    return 50;
  }
};

// Desglose exhaustivo de frentes y puertas por cada familia MV
export const getDesglosePuertasDetallado = (cod, familia, w, altura, altoMm, R = {}, tariff = 'T1') => {
  const c = (cod || '').toUpperCase();
  const f = (familia || '').toUpperCase();
  const dio = /D\/I/.test(c);
  const wCm = Math.round(w / 10);
  const frentes = [];
  const hBajo = (altura === '70' || altoMm === 700) ? 70 : 80;

  // 1. BAJOS DE CAJONES Y GAVETAS
  if (f === 'BAJO_5_CAJONES' || /^BC\d+/.test(c)) {
    const hCaj = hBajo === 80 ? 16 : 14;
    for (let i = 0; i < 5; i++) {
      frentes.push({ h: hCaj, w: wCm, desc: `Cajón ${i + 1} (${hCaj}x${wCm})` });
    }
  } else if (f === 'BAJO_3CAJ_1GAV' || /^BCG\d+/.test(c)) {
    const hCaj = 14;
    const hGav = hBajo === 80 ? 35 : 28;
    for (let i = 0; i < 3; i++) {
      frentes.push({ h: hCaj, w: wCm, desc: `Cajón ${i + 1} (${hCaj}x${wCm})` });
    }
    frentes.push({ h: hGav, w: wCm, desc: `Gaveta inferior (${hGav}x${wCm})` });
  } else if (f === 'BAJO_2GAV_1CAJ' || /^BGC\d+/.test(c)) {
    const hCaj = 14;
    const hGav = hBajo === 80 ? 33 : 28;
    frentes.push({ h: hCaj, w: wCm, desc: `Cajón superior (${hCaj}x${wCm})` });
    frentes.push({ h: hGav, w: wCm, desc: `Gaveta media (${hGav}x${wCm})` });
    frentes.push({ h: hGav, w: wCm, desc: `Gaveta inferior (${hGav}x${wCm})` });
  } else if (f === 'BAJO_2CAJ_1GAV_1FRENTE' || /^BCGF\d+/.test(c)) {
    const hGav = hBajo === 80 ? 35 : 28;
    frentes.push({ h: 14, w: wCm, desc: `Cajón 1 (14x${wCm})` });
    frentes.push({ h: 14, w: wCm, desc: `Cajón 2 (14x${wCm})` });
    frentes.push({ h: hGav, w: wCm, desc: `Gaveta cacerolero (${hGav}x${wCm})` });
  } else if (f === 'BAJO_2GAV_1FRENTE' || /^BGF\d+/.test(c)) {
    const hGav = hBajo === 80 ? 35 : 28;
    frentes.push({ h: hGav, w: wCm, desc: `Gaveta superior (${hGav}x${wCm})` });
    frentes.push({ h: hGav, w: wCm, desc: `Gaveta inferior (${hGav}x${wCm})` });
  } else if (f === 'BAJO_PUERTA_CAJON' || /^BPC\d+/.test(c)) {
    const hPuer = hBajo === 80 ? 60 : 56;
    frentes.push({ h: 14, w: wCm, desc: `Frente cajón (14x${wCm})` });
    frentes.push({ h: hPuer, w: wCm, desc: `Puerta inferior (${hPuer}x${wCm})` });
  } else if (f === 'BAJO_HORNO' || /^BH/.test(c)) {
    if (/BHC|BHZ/.test(c)) {
      frentes.push({ h: 14, w: 60, desc: 'Frente cajón inferior (14x60)' });
    } else if (/BHG/.test(c)) {
      frentes.push({ h: hBajo === 80 ? 35 : 28, w: 60, desc: `Frente gaveta inferior (${hBajo === 80 ? 35 : 28}x60)` });
    }
  } else if (f === 'BAJO_RINCON_ESCUADRA' || /^BRI|^BRU/.test(c)) {
    frentes.push({ h: hBajo, w: 30, desc: `Puerta escuadra 1 (${hBajo}x30)` });
    frentes.push({ h: hBajo, w: 30, desc: `Puerta escuadra 2 (${hBajo}x30)` });
  } else if (f === 'BAJO_RINCON_CIEGO' || /^BR\d+/.test(c)) {
    const wPuerta = Math.max(40, wCm - 50);
    frentes.push({ h: hBajo, w: wPuerta, desc: `Puerta rincón ciego (${hBajo}x${wPuerta})` });
  } else if (f.startsWith('BAJO') || /^B\d+|^BF\d+/.test(c)) {
    // Bajos y Fregaderos estándar (h=80 por defecto, o h=70)
    const numP = (wCm >= 70 && !dio) ? 2 : 1;
    const wUnit = numP > 1 ? Math.round(wCm / numP) : wCm;
    for (let i = 0; i < numP; i++) {
      frentes.push({ h: hBajo, w: wUnit, desc: numP > 1 ? `Puerta ${i + 1} (${hBajo}x${wUnit})` : `Puerta bajo (${hBajo}x${wUnit})` });
    }
  } 
  // 2. COLUMNAS
  else if (f === 'COLUMNA_DESPENSERO' || /^CD\d+/.test(c)) {
    const hAlta = (altura === '220' || altoMm >= 2150) ? 147 : 127;
    frentes.push({ h: hAlta, w: wCm, desc: `Puerta superior despensa (${hAlta}x${wCm})` });
    frentes.push({ h: hBajo === 80 ? 80 : 70, w: wCm, desc: `Puerta inferior despensa (${hBajo === 80 ? 80 : 70}x${wCm})` });
  } else if (f === 'COLUMNA_FRIGO' || /^CF\d+/.test(c)) {
    frentes.push({ h: 127, w: 60, desc: 'Puerta superior frigo (127x60)' });
    frentes.push({ h: hBajo === 80 ? 80 : 70, w: 60, desc: `Puerta inferior congelador (${hBajo === 80 ? 80 : 70}x60)` });
  } else if (f === 'COLUMNA_HORNO' || /^CH\d+/.test(c)) {
    const hSup = (altura === '220' || altoMm >= 2150) ? 90 : 70;
    frentes.push({ h: hSup, w: 60, desc: `Puerta superior horno (${hSup}x60)` });
    frentes.push({ h: hBajo === 80 ? 80 : 70, w: 60, desc: `Puerta/Gaveta inferior (${hBajo === 80 ? 80 : 70}x60)` });
  } else if (f === 'COLUMNA_HORNO_MICRO' || /^CHM\d+/.test(c)) {
    const hSup = (altura === '220' || altoMm >= 2150) ? 56 : 40;
    frentes.push({ h: hSup, w: 60, desc: `Puerta superior (${hSup}x60)` });
    frentes.push({ h: hBajo === 80 ? 80 : 70, w: 60, desc: `Puerta/Gaveta inferior (${hBajo === 80 ? 80 : 70}x60)` });
  } else if (f.startsWith('MEDIACOLUMNA') || f.startsWith('MEDIA_') || /^M\d+|^MPG\d+|^MPH\d+|^MV\d+/.test(c)) {
    if (f === 'MEDIA_PUERTA_GAVETA' || /^MPG/.test(c)) {
      frentes.push({ h: hBajo === 80 ? 80 : 70, w: wCm, desc: `Puerta semicolumna (${hBajo === 80 ? 80 : 70}x${wCm})` });
      frentes.push({ h: 28, w: wCm, desc: `Gaveta inferior (28x${wCm})` });
    } else {
      frentes.push({ h: 127, w: wCm, desc: `Puerta semicolumna (127x${wCm})` });
    }
  } else if (f.startsWith('SOBREENC') || /^S\d+|^SV\d+|^SC\d+/.test(c)) {
    const hSob = (altura === '147' || altoMm >= 1400) ? 147 : 127;
    if (f.includes('CAJON')) {
      frentes.push({ h: 14, w: wCm, desc: `Cajón sobreencimera (14x${wCm})` });
      frentes.push({ h: hSob === 147 ? 127 : 90, w: wCm, desc: `Puerta sobreencimera (${hSob === 147 ? 127 : 90}x${wCm})` });
    } else {
      frentes.push({ h: hSob, w: wCm, desc: `Puerta sobreencimera (${hSob}x${wCm})` });
    }
  }
  // 3. ALTOS
  else if (f === 'ALTO_ABATIBLE' || /^AA\d+/.test(c)) {
    frentes.push({ h: 40, w: wCm, desc: `Frente abatible superior (40x${wCm})` });
    frentes.push({ h: 40, w: wCm, desc: `Frente abatible inferior (40x${wCm})` });
  } else if (f === 'ALTO_CAMPANA' || /^ASC|^ASCE/.test(c)) {
    const hAlto = (altura === '90' || altoMm >= 850) ? 90 : 70;
    if (wCm >= 90) {
      frentes.push({ h: hAlto, w: 45, desc: `Puerta campana izq. (${hAlto}x45)` });
      frentes.push({ h: hAlto, w: 45, desc: `Puerta campana dcha. (${hAlto}x45)` });
    } else {
      frentes.push({ h: hAlto, w: wCm, desc: `Puerta campana (${hAlto}x${wCm})` });
    }
  } else if (f === 'ALTILLO' || f === 'ALTILLO_VITRINA' || /^L\d+|^LV\d+/.test(c)) {
    const hAltillo = (altura === '90' || altoMm >= 850) ? 40 : 28;
    frentes.push({ h: hAltillo, w: wCm, desc: `Puerta altillo (${hAltillo}x${wCm})` });
  } else if (f.startsWith('ALTO') || /^A\d+|^AV\d+|^AE\d+|^AM\d+/.test(c)) {
    const hAlto = (altura === '90' || altoMm >= 850) ? 90 : 70;
    const numP = (wCm >= 70 && !dio) ? 2 : 1;
    const wUnit = numP > 1 ? Math.round(wCm / numP) : wCm;
    for (let i = 0; i < numP; i++) {
      frentes.push({ h: hAlto, w: wUnit, desc: numP > 1 ? `Puerta ${i + 1} (${hAlto}x${wUnit})` : `Puerta alto (${hAlto}x${wUnit})` });
    }
  }

  // Calcular puntos de cada frente
  let puntosTotales = 0;
  let sinTarifa = 0;
  const esVitrina = R.vitrina || f.includes('VITRINA');
  const detalle = frentes.map(fr => {
    const pts = esVitrina
      ? getPuntosVitrinaMV(fr.h, fr.w, tariff)
      : getPuntosPuertaMV(fr.h, fr.w, tariff);
    // `null` es «la tarifa no tiene esa casilla». Sumarlo daria 0 y el frente
    // saldria gratis sin que nadie lo notara: se cuenta aparte para poder
    // decirlo en pantalla.
    if (pts == null) {
      sinTarifa += 1;
      return { ...fr, puntos: null, sinTarifa: true };
    }
    puntosTotales += pts;
    return { ...fr, puntos: pts };
  });

  return { frentes: detalle, puntosTotales, numPuertas: frentes.length, sinTarifa };
};

// Descompone un código MV según la regla de su familia y tarifa activa.
export const despiece = (item, p, tariff = 'T1', pvCustom, acabadoCasco) => {
  const cod = item.cod, altura = item.altura, familia = item.familia;
  const R = RULES[familia] || RULE_GENERICA;
  const dio = /D\/I/.test(cod);
  const w = anchoDe(cod);
  const wCasco = w < 300 ? 300 : w;
  const altoMm = R.altoSel ? (altura === '90' ? 900 : 700) : (R.altoCol ? (altura === '220' ? 2200 : 2000) : (altura === '70' ? 700 : (R.alto || 800)));
  const factorDesmontada = getFactorDesmontada();
  const ccBruto = cascoACB(R.casco, wCasco, altoMm, factorDesmontada, acabadoCasco);
  // EL DESCUENTO DE ACB, QUE SE METE A MANO (master, 30/08: «falta el descuento
  // de ACB que metía a mano»). La tarifa del proveedor se negocia y cambia; el
  // catálogo trae el precio de tarifa y el descuento va aparte.
  //
  // POR DEFECTO ES 0, y eso importa: sin tocarlo, el coste sale EXACTAMENTE
  // igual que antes. Un descuento que apareciera con un valor puesto movería
  // todos los márgenes ya calculados sin que nadie lo hubiera decidido.
  //
  // Se aplica aquí y no dentro de `cascoACB` para no cambiarle la forma a una
  // función que devuelve también el PVP de Desmontada: el descuento es de
  // COMPRA, y el PVP no se toca.
  const dtoCascos = Math.min(100, Math.max(0, Number((p && p.dtoCascos) || 0)));
  // Sobre un casco SIN PRECIO no se aplica descuento: el 28% de «no se sabe»
  // sigue siendo «no se sabe», y calcularlo lo convertiría en un 0,00 € con
  // pinta de cifra.
  const cc = (dtoCascos > 0 && ccBruto.coste != null)
    ? { ...ccBruto, coste: Math.round(ccBruto.coste * (1 - dtoCascos / 100) * 100) / 100 }
    : ccBruto;
  
  // Desglose técnico preciso de puertas y frentes
  const desgloseFrentes = getDesglosePuertasDetallado(cod, familia, w, altura, altoMm, R, tariff);
  const puertas = desgloseFrentes.numPuertas;
  const cajones = (R.cajFn ? R.cajFn(cod) : (R.cajones || 0));
  const gavetas = (R.gavFn ? R.gavFn(cod) : (R.gavetas || 0));
  const baldas = R.baldasSel ? (altura === '90' ? 2 : 1) : (R.baldas || 0);
  
  // Cálculo de Puntos Oficiales de Puertas según la Matriz MV
  const pvPuntos = pvCustom || 3.33; // Valor punto oficial
  const dto1 = (p && p.dtoPuertas1 != null) ? Number(p.dtoPuertas1) : ((p && p.dtoPuertas != null) ? Number(p.dtoPuertas) : getDescuentoPuertas());
  const dto2 = (p && p.dtoPuertas2 != null) ? Number(p.dtoPuertas2) : 0;
  const factorDto = (1 - dto1 / 100) * (1 - dto2 / 100);
  const puntosPuertas = desgloseFrentes.puntosTotales;

  const pvpPuertas = Math.round(puntosPuertas * pvPuntos * 100) / 100;
  const costePuertas = Math.round(pvpPuertas * factorDto * 100) / 100;

  const altoFrente = R.altoCol ? altoMm : (R.altoSel ? altoMm : (altura === '70' ? 713 : 790));
  const areaP = (puertas > 0 || cajones > 0 || gavetas > 0) ? (w / 1000) * (altoFrente / 1000) : 0;

  const costeHerrajes = Math.round((puertas * 2 * (Number(p.bisagra) || 0)
    + (R.patas ? (Number(p.pata4) || 0) : 0)
    + (R.colg ? 2 * (Number(p.colgador) || 0) : 0)
    + (cajones * (Number(p.cajon) || 0))
    + (gavetas * (Number(p.gaveta) || 0))
    + (baldas * 4 * (Number(p.soporte) || 0))) * 100) / 100;
  const costeMo = Number(p.mano) || 0;
  // UN COSTE INCOMPLETO NO ES UN COSTE. Si el casco no tiene precio, el total
  // sale `null` y NO la suma de lo demás: sumar los otros tres sumandos daría
  // un número con toda la pinta de ser el coste, más bajo que el de verdad, y
  // de ahí saldría un margen inflado. Es lo que pasaba con las columnas.
  // UNA FAMILIA QUE EL DESPIECE NO CONOCE TAMPOCO TIENE COSTE (master, 31/08:
  // «nada: “?” y fuera del margen»).
  //
  // `RULES[familia] || RULE_GENERICA` no devuelve «no se sabe»: devuelve el
  // despiece de un BAJO CON BALDA de 800 con una puerta. Así que un PANEL, un
  // zócalo o un TIRADOR salían costando 67,01 € — el mismo número que un mueble
  // de verdad y con la misma pinta. En la cocina que lo destapó eran 7 líneas de
  // 12 y el margen del presupuesto entero salía en −126,8 % en una cocina que
  // gana dinero. Marcarlo con un «aprox» diminuto no bastaba: el número seguía
  // sumando.
  //
  // Ahora no suma. La línea se queda sin coste, se marca, y el aviso de abajo
  // dice cuántas hay y que el margen que se ve es más alto que el real. Es la
  // regla 7 de CLAUDE.md: lo que no se sabe va vacío, nunca con un número
  // plausible.
  const cascoSinPrecio = cc.coste == null;
  const sinDespiece = !!R.generica;
  const costeTotal = (cascoSinPrecio || sinDespiece)
    ? null
    : Math.round((cc.coste + costePuertas + costeHerrajes + costeMo) * 100) / 100;

  return {
    fam: familia, med: cc.med, inc: w < 300 ? 'inc. corte' : '',
    casco: cc.coste,
    cascoTarifa: ccBruto.coste,   // antes del descuento de compra
    cascoSinPrecio,
    sinDespiece,
    cascoOtroAcabado: ccBruto.otroAcabado || null,
    cascoGama: ccBruto.gamaUsada || null,
    dtoCascos,
    cascoPvp: cc.pvpDesmontada,
    puerta: costePuertas,
    puertaPvp: pvpPuertas,
    puertasDetalle: desgloseFrentes.frentes,
    dtoPuertas: dto1,
    dtoPuertas1: dto1,
    dtoPuertas2: dto2,
    puertas,
    areaPuertas: Math.round(areaP * 100) / 100,
    bisagras: puertas * 2 * (Number(p.bisagra) || 0),
    patas: R.patas ? (Number(p.pata4) || 0) : 0,
    colg: R.colg ? 2 * (Number(p.colgador) || 0) : 0,
    caj: cajones * (Number(p.cajon) || 0), 
    gav: gavetas * (Number(p.gaveta) || 0),
    soportes: baldas * 4 * (Number(p.soporte) || 0),
    mo: costeMo,
    costeTotal,
    factorDesmontada,
    generica: R.generica || false,
  };
};

export default function RentabilidadMV({ esMaster, seed }) {
  // Descuento comercial que se aplicará al presupuesto. NO afecta al coste ni
  // al margen de esta pantalla: solo sirve para saber con qué base imponible se
  // decide el tramo de la comisión del comercial.
  const [dtoComision, setDtoComision] = useState(0);
  const [pv, setPv] = useState(3.33);
  const [familias, setFamilias] = useState(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState(null);
  const [lineas, setLineas] = useState([]);   // [{cod, altura, puntos, cant}]
  const [sel, setSel] = useState('');
  const [alturaSel, setAlturaSel] = useState('70');
  const [pvpVisible, setPvpVisible] = useState(false);       // clic en candado → ver PVP
  const [margenVisible, setMargenVisible] = useState(false); // Shift+clic → ver también coste/margen
  const [cant, setCant] = useState(1);
  // Costes de componentes (editables).
  const P_DEFAULT = MV_COSTES_DEFAULT;
  const [p, setP] = useState(() => {
    try { const s = JSON.parse(localStorage.getItem('mv_costes') || 'null'); return s ? { ...P_DEFAULT, ...s } : P_DEFAULT; } catch { return P_DEFAULT; }
  });
  useEffect(() => { try { localStorage.setItem('mv_costes', JSON.stringify(p)); } catch { /* noop */ } }, [p]);
  const setNum = (k) => (e) => setP(prev => ({ ...prev, [k]: e.target.value === '' ? '' : Number(e.target.value) }));

  useEffect(() => {
    if (!esMaster) return;
    setCargando(true);
    fetch(`${API_URL}/api/cascos/mv/tarifa?tariff=T1`, { headers: H() })
      .then(r => r.json())
      .then(d => { if (d.success) { setFamilias(d.familias); setPv(d.pointValue || 3.33); } else setError(d.detail || 'No se pudo cargar la tarifa MV.'); })
      .catch(() => setError('Error al cargar la tarifa MV.'))
      .finally(() => setCargando(false));
  }, [esMaster]);

  // Índice código → { familia, entry, type }. Cubre TODAS las familias con items.
  const codeIndex = useMemo(() => {
    const idx = {};
    if (!familias) return idx;
    Object.entries(familias).forEach(([fam, v]) => {
      if (v && v.items) Object.entries(v.items).forEach(([cod, entry]) => { idx[cod] = { familia: fam, entry, type: v.type }; });
    });
    return idx;
  }, [familias]);

  const familiaDe = (cod) => codeIndex[cod]?.familia || null;

  // Resuelve los puntos según el tipo de familia (single, dual, h7090, h127147, h200220).
  const puntosDe = (cod, altura) => {
    const it = codeIndex[cod]; if (!it) return 0;
    const e = it.entry;
    if (!Array.isArray(e)) return e;
    if (it.type === 'h7090') return e[altura === '90' ? 1 : 0];
    if (it.type === 'h200220') return e[altura === '220' ? 1 : 0];
    if (it.type === 'h127147') return e[altura === '147' ? 1 : 0];
    if (it.type === 'dual') return e[0]; // fregadero: precio normal (idx 0)
    return e[0];
  };
  // Opciones de altura según la familia del código.
  const alturasDe = (cod) => {
    const t = codeIndex[cod]?.type;
    if (t === 'h7090') return ['70', '90'];
    if (t === 'h200220') return ['200', '220'];
    if (t === 'h127147') return ['127', '147'];
    return [];
  };

  const anadir = () => {
    if (!sel) return;
    const alts = alturasDe(sel);
    const altura = alts.length ? alturaSel : '';
    setLineas(prev => [...prev, { cod: sel, familia: familiaDe(sel), altura, puntos: puntosDe(sel, altura), cant: Math.max(1, Number(cant) || 1) }]);
  };

  // Exporta el escandallo + margen a PDF (master).
  const exportarPDF = async () => {
    if (!calc.rows.length) return;
    const { jsPDF } = await import('jspdf');
    const pdf = new jsPDF({ orientation: 'landscape', unit: 'mm', format: 'a4' });
    const W = pdf.internal.pageSize.getWidth(); let y = 14;
    pdf.setFont('helvetica', 'bold'); pdf.setFontSize(15); pdf.setTextColor(20, 60, 40);
    pdf.text('RENTABILIDAD TARIFA MV', 12, y); y += 6;
    pdf.setFont('helvetica', 'normal'); pdf.setFontSize(9); pdf.setTextColor(110);
    pdf.text(`Valor punto ${pv} €  ·  Puerta ${p.doorM2} €/m²  ·  Generado`, 12, y); y += 6;
    const cols = [['Código', 22], ['Cant', 12], ['Casco', 20], ['Puerta', 20], ['Bisag', 18], ['Otros', 20], ['M.O.', 16], ['Coste', 22], ['PVP', 22], ['Margen', 30]];
    let x = 12; pdf.setFont('helvetica', 'bold'); pdf.setFontSize(8); pdf.setTextColor(40);
    cols.forEach(([t, w]) => { pdf.text(t, x + 1, y); x += w; }); y += 2; pdf.setDrawColor(200); pdf.line(12, y, 12 + cols.reduce((a, c) => a + c[1], 0), y); y += 4;
    pdf.setFont('helvetica', 'normal');
    const E = (n) => (Number(n) || 0).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    calc.rows.forEach(r => {
      x = 12; const otros = (r.patas + r.colg + r.caj + r.gav + r.soportes) * r.cant;
      const vals = [`${r.cod}${r.altura ? '/' + r.altura : ''}`, String(r.cant), E(r.casco * r.cant), E(r.puerta * r.cant), E(r.bisagras * r.cant), E(otros), E(r.mo * r.cant), E(r.coste), E(r.pvp), `${E(r.margen)} (${r.pvp ? Math.round(r.margen / r.pvp * 100) : 0}%)`];
      vals.forEach((v, i) => { pdf.text(String(v), x + 1, y); x += cols[i][1]; }); y += 5;
      if (y > 190) { pdf.addPage(); y = 14; }
    });
    y += 2; pdf.setDrawColor(120); pdf.line(12, y, 12 + cols.reduce((a, c) => a + c[1], 0), y); y += 5;
    pdf.setFont('helvetica', 'bold');
    pdf.text('TOTAL', 12, y);
    pdf.text(`Coste ${E(calc.tot.coste)} €`, 130, y);
    pdf.text(`PVP ${E(calc.tot.pvp)} €`, 175, y);
    pdf.text(`MARGEN ${E(calc.tot.margen)} € (${calc.tot.pvp ? Math.round(calc.tot.margen / calc.tot.pvp * 100) : 0}%)`, 215, y);
    pdf.save(`rentabilidad_mv_${new Date().toISOString().slice(0, 10)}.pdf`);
  };

  // Carga muebles precargados (p.ej. "coger del diseño" de Estudio 3D).
  const seedKey = JSON.stringify(seed || []);
  useEffect(() => {
    if (!familias || !seed || !seed.length) return;
    const nuevas = [];
    seed.forEach(s => {
      if (!codeIndex[s.cod]) return;
      const alts = alturasDe(s.cod);
      const altura = s.altura || (alts.length ? alts[alts.length - 1] : '');
      nuevas.push({ cod: s.cod, familia: familiaDe(s.cod), altura, puntos: puntosDe(s.cod, altura), cant: Math.max(1, Number(s.cant) || 1) });
    });
    if (nuevas.length) setLineas(nuevas);
  }, [seedKey, familias]); // eslint-disable-line

  // Importar una relación de muebles desde PDF: detecta los códigos y los añade.
  const fileRef = useRef(null);
  const [importando, setImportando] = useState(false);
  const [noSoportados, setNoSoportados] = useState([]);
  const importarPDF = async (file) => {
    if (!file || !familias) return;
    setImportando(true); setError(null); setNoSoportados([]);
    try {
      const b64 = await new Promise((res, rej) => { const fr = new FileReader(); fr.onload = () => res(fr.result); fr.onerror = rej; fr.readAsDataURL(file); });
      const r = await fetch(`${API_URL}/api/cascos/mv/detectar-pdf`, { method: 'POST', headers: H(), body: JSON.stringify({ pdfBase64: b64 }) });
      const d = await r.json().catch(() => ({}));
      if (!r.ok || !d.success) { setError(d.detail || 'No se pudieron detectar muebles en el PDF.'); return; }
      const nuevas = [], noSop = [];
      (d.codigos || []).forEach(c => {
        const cant = (d.conteo && d.conteo[c]) || 1;
        if (codeIndex[c]) {
          const alts = alturasDe(c);
          const altura = alts.length ? alts[alts.length - 1] : ''; // por defecto la mayor (90/220/147)
          nuevas.push({ cod: c, familia: familiaDe(c), altura, puntos: puntosDe(c, altura), cant });
        } else noSop.push(c);
      });
      if (nuevas.length) setLineas(prev => [...prev, ...nuevas]);
      setNoSoportados(noSop);
      if (!nuevas.length) setError('No se reconoció ningún código de bajo/alto en el PDF.');
    } catch { setError('Error al importar el PDF.'); }
    finally { setImportando(false); }
  };

  const calc = useMemo(() => {
    const rows = lineas.map(l => {
      const d = despiece({ cod: l.cod, altura: l.altura, familia: l.familia }, p) || {};
      // ESTA PANTALLA SUMA LAS PARTES POR SU CUENTA, así que el `costeTotal`
      // en `null` de `despiece` no la alcanzaba: con `|| 0` en cada sumando,
      // una línea sin coste habría salido costando la mano de obra sola. Se
      // pregunta lo mismo que pregunta el Presupuestador, para que las dos
      // pantallas cuenten la misma historia del mismo mueble.
      const sinCoste = d.costeTotal == null;
      const coste = sinCoste ? null
        : (d.casco || 0) + (d.puerta || 0) + (d.bisagras || 0) + (d.patas || 0) + (d.colg || 0) + (d.caj || 0) + (d.gav || 0) + (d.soportes || 0) + (d.mo || 0);
      const pvp = (Number(l.puntos) || 0) * pv;
      return { ...l, ...d, sinCoste, costeUd: coste, pvpUd: pvp,
        coste: sinCoste ? null : coste * l.cant,
        pvp: pvp * l.cant,
        margen: sinCoste ? null : (pvp - coste) * l.cant };
    });
    const tot = rows.reduce((a, r) => ({
      pvp: a.pvp + r.pvp,
      coste: a.coste + (r.coste || 0),
      margen: a.margen + (r.margen || 0),
      sinCoste: a.sinCoste + (r.sinCoste ? 1 : 0),
    }), { pvp: 0, coste: 0, margen: 0, sinCoste: 0 });
    return { rows, tot };
  }, [lineas, p, pv]);

  // El candado del coste/margen. Se abre manteniendo pulsado o con Shift+clic.
  // Va ANTES del `return null` de abajo: un hook no puede quedarse a un lado de
  // un `if`, o React se pierde entre un render y el siguiente.
  const candadoMargen = usePulsacionLarga(() => setMargenVisible(v => !v));

  if (!esMaster) return null;

  return (
    <div className="bg-white border-2 border-emerald-300 rounded-2xl overflow-hidden shadow-sm mb-4">
      <div className="flex items-center gap-2 px-4 py-3 bg-emerald-50 border-b border-emerald-200">
        <span className="text-[10px] font-black uppercase tracking-widest text-emerald-700 bg-emerald-200 px-2 py-0.5 rounded">Solo master</span>
        <h3 className="text-sm font-black text-emerald-900 flex items-center gap-1.5"><TrendingUp size={15} /> Rentabilidad Tarifa MV</h3>
        <button
          {...candadoMargen.props}
          onClick={(e) => {
            // La pulsación larga ya ha hecho lo suyo: el clic que manda el
            // navegador al soltar no debe deshacerlo.
            if (candadoMargen.consumir()) return;
            if (e.shiftKey) setMargenVisible(v => !v); else setPvpVisible(v => !v);
          }}
          title={`Toque: ver/ocultar PVP · Coste y margen: ${AYUDA_CANDADO}`}
          className={`ml-auto flex items-center gap-1 px-2 py-1 rounded-lg text-[10px] font-black ${margenVisible ? 'bg-emerald-600 text-white' : (pvpVisible ? 'bg-emerald-200 text-emerald-800' : 'bg-white border border-emerald-300 text-emerald-700')}`}>
          {(pvpVisible || margenVisible) ? <Unlock size={12} /> : <Lock size={12} />} {margenVisible ? 'Coste' : (pvpVisible ? 'PVP' : 'Ver')}
        </button>
        <span className="text-[11px] text-emerald-500">punto {pv} €</span>
      </div>
      <div className="p-4 space-y-4">
        {cargando && <div className="text-sm text-slate-500 flex items-center gap-2"><Loader size={14} className="animate-spin" /> Cargando tarifa MV…</div>}
        {error && <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-sm text-red-700">{error}</div>}

        {/* Añadir mueble */}
        {familias && (
          <div className="flex items-end gap-2 flex-wrap bg-slate-50 border border-slate-200 rounded-xl p-3">
            <label className="flex flex-col gap-1">
              <span className="text-[10px] font-bold text-slate-400 uppercase">Código MV (bajo/alto)</span>
              <select value={sel} onChange={e => setSel(e.target.value)} className="px-2 py-1.5 border border-slate-200 rounded-lg text-sm min-w-[200px]">
                <option value="">Elegir…</option>
                {Object.entries(familias).filter(([, v]) => v && v.items).map(([fam, v]) => (
                  <optgroup key={fam} label={fam.replace(/_/g, ' ')}>
                    {Object.keys(v.items).map(c => <option key={c} value={c}>{c}</option>)}
                  </optgroup>
                ))}
              </select>
            </label>
            {alturasDe(sel).length > 0 && (
              <label className="flex flex-col gap-1">
                <span className="text-[10px] font-bold text-slate-400 uppercase">Altura</span>
                <select value={alturaSel} onChange={e => setAlturaSel(e.target.value)} className="px-2 py-1.5 border border-slate-200 rounded-lg text-sm">
                  {alturasDe(sel).map(h => <option key={h} value={h}>{h}</option>)}
                </select>
              </label>
            )}
            <label className="flex flex-col gap-1">
              <span className="text-[10px] font-bold text-slate-400 uppercase">Cant.</span>
              <input type="number" min="1" value={cant} onChange={e => setCant(e.target.value)} className="px-2 py-1.5 border border-slate-200 rounded-lg text-sm w-16" />
            </label>
            <button onClick={anadir} disabled={!sel} className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-black bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-50"><Plus size={14} /> Añadir</button>
            <span className="w-px h-8 bg-slate-200 mx-1" />
            <button onClick={() => fileRef.current?.click()} disabled={importando} className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-black bg-slate-800 text-white hover:bg-slate-900 disabled:opacity-50">
              {importando ? <Loader size={14} className="animate-spin" /> : <Upload size={14} />} {importando ? 'Detectando…' : 'Importar PDF'}
            </button>
            <input ref={fileRef} type="file" accept="application/pdf" className="hidden" onChange={e => importarPDF(e.target.files?.[0])} />
            {lineas.length > 0 && (<>
              <button onClick={exportarPDF} className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-black bg-slate-800 text-white hover:bg-slate-900"><Download size={14} /> PDF</button>
              <button onClick={() => setLineas([])} className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-bold bg-slate-100 text-slate-600 hover:bg-slate-200"><Trash2 size={14} /> Vaciar</button>
            </>)}
          </div>
        )}
        {noSoportados.length > 0 && (
          <div className="p-2.5 rounded-lg bg-amber-50 border border-amber-200 text-[11px] text-amber-800">
            <b>Códigos detectados aún no soportados</b> (Fase 2: cajoneras, columnas, rincones…): {noSoportados.join(', ')}
          </div>
        )}

        {/* Parámetros de coste */}
        <div className="rounded-xl border border-slate-200 p-3">
          <div className="flex items-center gap-1.5 mb-2 text-slate-600"><Calculator size={14} /><span className="text-[11px] font-black uppercase tracking-wide">Costes de componente (editables)</span></div>
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2">
            {[['doorM2', 'Puerta €/m²'], ['bisagra', 'Bisagra €'], ['cajon', 'Cajón €'], ['gaveta', 'Gaveta €'], ['pata4', 'Patas (4) €'], ['colgador', 'Colgador €'], ['soporte', 'Soporte balda €'], ['mano', 'Mano obra €']].map(([k, l]) => (
              <label key={k} className="flex flex-col gap-1">
                <span className="text-[10px] font-bold text-slate-400 uppercase">{l}</span>
                <input type="number" step="any" value={p[k]} onChange={setNum(k)} className="px-2 py-1.5 border border-slate-200 rounded-lg text-sm" />
              </label>
            ))}
          </div>
          <p className="text-[10px] text-slate-400 mt-2">Casco = ACB antracita (base ×2 −50% −28%). Puerta = superficie × €/m² (provisional, carga tu tarifa Alvic). Bisagras 2/puerta. Patas en bajos; colgadores + soportes en altos.</p>
        </div>

        {/* KPIs */}
        {calc.rows.length > 0 && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            <div className="rounded-xl border border-slate-200 p-2.5"><div className="text-[10px] font-black text-slate-400 uppercase">Muebles</div><div className="text-lg font-black text-slate-800">{lineas.reduce((a, l) => a + l.cant, 0)}</div></div>
            <div className="rounded-xl border border-slate-200 p-2.5"><div className="text-[10px] font-black text-slate-400 uppercase">PVP total</div><div className="text-lg font-black text-slate-800">{pvpVisible ? eur(calc.tot.pvp) : '•••'}</div></div>
            <div className="rounded-xl border border-emerald-200 bg-emerald-50/40 p-2.5"><div className="text-[10px] font-black text-emerald-500 uppercase">Margen total</div><div className="text-lg font-black text-emerald-700">{margenVisible ? eur(calc.tot.margen) : '•••'}</div></div>
            <div className="rounded-xl border border-emerald-200 bg-emerald-50/40 p-2.5"><div className="text-[10px] font-black text-emerald-500 uppercase">Margen medio</div><div className="text-lg font-black text-emerald-700">{margenVisible ? `${calc.tot.pvp ? Math.round(calc.tot.margen / calc.tot.pvp * 100) : 0}%` : '•••'}</div></div>
          </div>
        )}

        {/* ─── COMISIONES DE LOS COOPERATIVISTAS ───────────────────────────
            Va DESPUÉS de los KPIs a propósito: el tramo lo marca la valoración
            del pedido, así que primero se ve el total y luego lo que sale de
            él. Y va dentro de Rentabilidad MV, que ya es solo del master
            (CLAUDE.md, regla 8): esto es nómina de gente. */}
        {calc.rows.length > 0 && (() => {
          const uds = lineas.reduce((a, l) => a + l.cant, 0);
          // EL TRAMO LO MARCA LA BASE IMPONIBLE: el PVP DESPUÉS del descuento y
          // SIN IVA. El master, 25/08: «siempre va sobre la base imponible, no
          // sobre el total con IVA».
          //
          // Costó dos correcciones suyas llegar aquí. Primero se hizo sobre el
          // COSTE («importes de costo … de valoración») y lo corrigió: «es
          // sobre el PVP». Y después preguntó por los descuentos y lo zanjó con
          // la base imponible.
          //
          // El PVP de esta pantalla no lleva IVA —es la suma de la tarifa—, así
          // que lo único que faltaba era el descuento. Aquí no había casilla
          // para él: el descuento se mete en Cocina Montada 3, en otra
          // pantalla, así que sin esto el tramo salía del PVP SIN DESCONTAR y
          // se comisionaba sobre dinero que no llega a entrar.
          const baseImponible = Math.round(calc.tot.pvp * (1 - Math.min(Math.max(Number(dtoComision) || 0, 0), 100) / 100) * 100) / 100;
          const valoracion = baseImponible;
          const porMuebleCom = comisionPorMueble(valoracion);
          const totalCom = Math.round(porMuebleCom * uds * 100) / 100;
          const manoUd = Number(p.mano) || 0;
          const totalMon = Math.round(manoUd * uds * 100) / 100;
          return (
            <div className="rounded-xl border border-dato-200 bg-dato-50/60 p-3">
              <div className="flex items-center gap-1.5 mb-2 text-dato-600">
                <Calculator size={14} />
                <span className="text-[11px] font-black uppercase tracking-wide">
                  Comisiones de cooperativistas
                </span>
              </div>
              {/* LA CADENA A LA VISTA. El tramo no sale del PVP: sale de la
                  base imponible. Enseñarla entera evita la pregunta de «¿sobre
                  qué se ha calculado esto?», que es la que hizo el master. */}
              <div className="flex items-center gap-2 flex-wrap mb-2 text-[11px]">
                <span className="text-slate-500">
                  {`PVP muebles ${pvpVisible ? eur(calc.tot.pvp) : '•••'}`}
                </span>
                <span className="text-slate-400">−</span>
                <label className="flex items-center gap-1">
                  <span className="text-slate-500">Dto.</span>
                  <input type="number" step="any" min="0" max="100" value={dtoComision}
                    onChange={e => setDtoComision(e.target.value === '' ? '' : Number(e.target.value))}
                    title="Descuento comercial que se aplicará al presupuesto. Solo sirve para saber con qué base imponible se decide el tramo de la comisión; no toca el coste ni el margen."
                    className="w-16 px-1.5 py-1 border border-dato-300 rounded-md bg-white font-bold text-right" />
                  <span className="text-slate-500">%</span>
                </label>
                <span className="text-slate-400">=</span>
                <span className="font-black text-dato-900" title="Base imponible: el PVP tras el descuento, sin IVA. El IVA no entra nunca en el tramo.">
                  {`Base imponible ${pvpVisible ? eur(baseImponible) : '•••'}`}
                </span>
                <span className="text-slate-400 text-[10px]">(el IVA no cuenta)</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                <div className="rounded-lg border border-dato-200 bg-white p-2.5">
                  <div className="text-[10px] font-black text-dato-500 uppercase">Comercial</div>
                  <div className="text-lg font-black text-dato-900">
                    {margenVisible ? eur(totalCom) : '•••'}
                  </div>
                  <div className="text-[10px] text-slate-500">
                    {`${eur(porMuebleCom)} × ${uds} mueble${uds === 1 ? '' : 's'}`}
                  </div>
                  <div className="text-[10px] text-slate-400" title="El tramo lo marca la base imponible: el PVP después del descuento y sin IVA.">
                    {`tramo: ${nombreDelTramo(valoracion)}`}
                  </div>
                </div>
                <div className="rounded-lg border border-dato-200 bg-white p-2.5">
                  <div className="text-[10px] font-black text-dato-500 uppercase">Montadores</div>
                  <div className="text-lg font-black text-dato-900">
                    {margenVisible ? eur(totalMon) : '•••'}
                  </div>
                  <div className="text-[10px] text-slate-500">
                    {`${eur(manoUd)} de mano de obra × ${uds} mueble${uds === 1 ? '' : 's'}`}
                  </div>
                  <div className="text-[10px] text-slate-400">
                    se cambia arriba, en «Mano obra €»
                  </div>
                </div>
                <div className="rounded-lg border border-accion-200 bg-accion-50/70 p-2.5">
                  <div className="text-[10px] font-black text-accion-700 uppercase">Total comisiones</div>
                  <div className="text-lg font-black text-accion-900">
                    {margenVisible ? eur(totalCom + totalMon) : '•••'}
                  </div>
                  <div className="text-[10px] text-slate-500">
                    {`sobre una base imponible de ${pvpVisible ? eur(baseImponible) : '•••'}`}
                  </div>
                </div>
              </div>
              <p className="text-[10px] text-slate-400 mt-2">
                Comercial: cantidad fija por mueble según la BASE IMPONIBLE del pedido
                —el PVP tras el descuento, sin IVA— ({escalaDeComisionEnPalabras()}).
                Montadores: la mano de obra por mueble que hay puesta
                arriba. Los importes van con el mismo candado que el margen.
              </p>
            </div>
          );
        })()}

        {/* Tabla */}
        {calc.rows.length > 0 && (
          <div className="overflow-x-auto rounded-xl border border-slate-200">
            <table className="w-full text-xs" style={{ fontVariantNumeric: 'tabular-nums' }}>
              <thead className="bg-slate-50 text-slate-500">
                <tr className="text-left">
                  <th className="px-2 py-2">Código</th><th className="px-2 py-2 text-center">Cant.</th>
                  <th className="px-2 py-2 text-right">Casco</th><th className="px-2 py-2 text-right">Puerta</th><th className="px-2 py-2 text-right">Bisag.</th>
                  <th className="px-2 py-2 text-right">Otros</th><th className="px-2 py-2 text-right">M.O.</th>
                  <th className="px-2 py-2 text-right">Coste</th><th className="px-2 py-2 text-right">PVP</th><th className="px-2 py-2 text-right font-black">Margen</th><th className="px-2 py-2"></th>
                </tr>
              </thead>
              <tbody>
                {calc.rows.map((r, i) => (
                  <tr key={i} className="border-t border-slate-100">
                    <td className="px-2 py-1.5 font-mono">{r.cod}{r.altura ? `/${r.altura}` : ''} <span className="text-[9px] text-slate-400">{r.puntos}pts · {r.med}{r.inc ? ' ⚠' : ''}</span></td>
                    <td className="px-2 py-1.5 text-center">
                      <input type="number" min="1" value={r.cant}
                        onChange={e => { const v = Math.max(1, Number(e.target.value) || 1); setLineas(prev => prev.map((x, j) => j === i ? { ...x, cant: v } : x)); }}
                        className="w-12 px-1 py-0.5 border border-slate-200 rounded text-center text-xs" />
                    </td>
                    <td className="px-2 py-1.5 text-right">{margenVisible ? eur(r.casco * r.cant) : '•••'}</td>
                    <td className="px-2 py-1.5 text-right">{margenVisible ? eur(r.puerta * r.cant) : '•••'}</td>
                    <td className="px-2 py-1.5 text-right">{margenVisible ? eur(r.bisagras * r.cant) : '•••'}</td>
                    <td className="px-2 py-1.5 text-right" title={`Patas ${eur(r.patas)} · Colg ${eur(r.colg)} · Cajones ${eur(r.caj)} · Gavetas ${eur(r.gav)} · Soportes ${eur(r.soportes)}`}>{margenVisible ? eur((r.patas + r.colg + r.caj + r.gav + r.soportes) * r.cant) : '•••'}{r.generica && <span className="text-[9px] text-amber-600 ml-1">aprox</span>}</td>
                    <td className="px-2 py-1.5 text-right">{margenVisible ? eur(r.mo * r.cant) : '•••'}</td>
                    <td className="px-2 py-1.5 text-right font-bold">{margenVisible ? eur(r.coste) : '•••'}</td>
                    <td className="px-2 py-1.5 text-right text-slate-500">{pvpVisible ? eur(r.pvp) : '•••'}</td>
                    <td className={`px-2 py-1.5 text-right font-black ${r.margen >= 0 ? 'text-emerald-700' : 'text-red-600'}`}>{margenVisible ? <>{eur(r.margen)} <span className="text-[9px]">({r.pvp ? Math.round(r.margen / r.pvp * 100) : 0}%)</span></> : '•••'}</td>
                    <td className="px-2 py-1.5"><button onClick={() => setLineas(prev => prev.filter((_, j) => j !== i))} className="text-red-400 hover:text-red-600"><Trash2 size={13} /></button></td>
                  </tr>
                ))}
              </tbody>
              <tfoot className="bg-emerald-50 font-black text-slate-800">
                <tr className="border-t-2 border-emerald-300">
                  <td className="px-2 py-2" colSpan={7}>TOTAL COCINA</td>
                  <td className="px-2 py-2 text-right">{margenVisible ? eur(calc.tot.coste) : '•••'}</td>
                  <td className="px-2 py-2 text-right">{pvpVisible ? eur(calc.tot.pvp) : '•••'}</td>
                  <td className="px-2 py-2 text-right text-emerald-800">{margenVisible ? <>{eur(calc.tot.margen)} <span className="text-[10px]">({calc.tot.pvp ? Math.round(calc.tot.margen / calc.tot.pvp * 100) : 0}%)</span></> : '•••'}</td>
                  <td></td>
                </tr>
              </tfoot>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
