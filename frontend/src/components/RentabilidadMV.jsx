/*
 * © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Plus, Trash2, Loader, Calculator, TrendingUp, Upload, Lock, Unlock, Download } from 'lucide-react';
import { authHeaders } from '../services/api';
import { CASCOS } from '../data/cascos';
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

// Precio del color: preferencia según color indicado o por defecto el primero disponible
const COLOR_PRIO = ['grafito', 'aluminio', 'blancoEsp', 'blanco', 'roble', 'olmo', 'stone', 'spike', 'blancoHidrofugo', 'robleAurora'];
const precioColor = (c, colorId) => { 
  if (!c || !c.precios) return null; 
  if (colorId && c.precios[colorId] != null) return c.precios[colorId];
  for (const k of COLOR_PRIO) if (c.precios[k] != null) return c.precios[k]; 
  return null; 
};

// Coste y PVP del casco ACB: precio neto de catálogo ACB × factor de Cocina Desmontada (Master)
export const cascoACB = (tipoAcb, ancho, alto, factor, acabadoCasco) => {
  const f = factor != null ? factor : getFactorDesmontada();
  const conf = MAP_CASCO_COLOR[acabadoCasco] || { color: 'grafito', grosor: 19 };
  const targetColor = conf.color;
  const targetGrosor = conf.grosor;

  const pool = CASCOS.filter(c => c.tipo === tipoAcb);
  if (!pool.length) return { coste: 0, pvpDesmontada: 0, med: '' };

  const porGrosor = pool.filter(c => c.grosor === targetGrosor);
  const usePool = porGrosor.length ? porGrosor : pool;

  let best = null, bd = Infinity;
  for (const c of usePool) {
    const pNeto = (c.precios && c.precios[targetColor] != null) ? c.precios[targetColor] : precioColor(c);
    if (pNeto != null) {
      const d = Math.abs((c.ancho || 0) - ancho) * 3 + Math.abs((c.alto || 0) - alto);
      if (d < bd) { bd = d; best = { ...c, pNeto }; }
    }
  }

  if (!best) {
    for (const c of pool) {
      const pNeto = precioColor(c);
      if (pNeto != null) {
        const d = Math.abs((c.ancho || 0) - ancho) * 3 + Math.abs((c.alto || 0) - alto);
        if (d < bd) { bd = d; best = { ...c, pNeto }; }
      }
    }
  }

  if (!best) return { coste: 0, pvpDesmontada: 0, med: '' };
  const precioNeto = best.pNeto || 0;
  return { 
    coste: Math.round(precioNeto * 100) / 100, 
    pvpDesmontada: Math.round(precioNeto * f * 100) / 100, 
    med: `${best.ancho}x${best.alto}` 
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
export const RULE_GENERICA = { casco: 'Bajo Con Balda', alto: 800, patas: 1, puertas: 1, generica: true };

// Costes por defecto de componentes MV (editables en la UI de Rentabilidad)
export const MV_COSTES_DEFAULT = { doorM2: 26, bisagra: 3.07, pata4: 0.64, colgador: 3.50, soporte: 0.30, mano: 20, cajon: 41.34, gaveta: 54.37 };

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
    '14': { 'P25': 6, 'P30': 7, 'P35': 7, 'P40': 8, 'P45': 8, 'P50': 9, 'P60': 10 },
    '28': { 'P25': 8, 'P30': 8, 'P35': 9, 'P40': 9, 'P45': 10, 'P50': 10, 'P60': 11 },
    '40': { 'P25': 9, 'P30': 9, 'P35': 10, 'P40': 10, 'P45': 11, 'P50': 11, 'P60': 12 },
    '56': { 'P25': 9, 'P30': 10, 'P35': 10, 'P40': 11, 'P45': 11, 'P50': 12, 'P60': 13 },
    '70': { 'P25': 10, 'P30': 11, 'P35': 12, 'P40': 13, 'P45': 13, 'P50': 14, 'P60': 16 },
    '90': { 'P25': 13, 'P30': 14, 'P35': 15, 'P40': 15, 'P45': 16, 'P50': 17, 'P60': 19 },
    '127': { 'P30': 16, 'P35': 17, 'P40': 19, 'P45': 19, 'P50': 20, 'P60': 22 },
    '147': { 'P30': 19, 'P35': 20, 'P40': 21, 'P45': 22, 'P50': 23, 'P60': 26 }
  },
  T2: {
    '14': { 'P25': 15, 'P30': 15, 'P35': 16, 'P40': 17, 'P45': 18, 'P50': 19, 'P60': 21 },
    '28': { 'P25': 20, 'P30': 20, 'P35': 22, 'P40': 23, 'P45': 25, 'P50': 26, 'P60': 29 },
    '70': { 'P25': 28, 'P30': 28, 'P35': 30, 'P40': 32, 'P45': 35, 'P50': 37, 'P60': 43 },
    '90': { 'P25': 34, 'P30': 34, 'P35': 36, 'P40': 39, 'P45': 43, 'P50': 45, 'P60': 52 },
    '127': { 'P30': 41, 'P35': 49, 'P40': 51, 'P45': 54, 'P50': 67, 'P60': 68 },
    '147': { 'P30': 47, 'P35': 54, 'P40': 55, 'P45': 58, 'P50': 60, 'P60': 75 }
  },
  T3: {
    '14': { 'P25': 9, 'P30': 9, 'P35': 10, 'P40': 10, 'P45': 11, 'P50': 12, 'P60': 13 },
    '28': { 'P25': 12, 'P30': 12, 'P35': 13, 'P40': 14, 'P45': 15, 'P50': 16, 'P60': 18 },
    '70': { 'P25': 15, 'P30': 16, 'P35': 17, 'P40': 19, 'P45': 19, 'P50': 21, 'P60': 25 },
    '90': { 'P25': 19, 'P30': 20, 'P35': 22, 'P40': 23, 'P45': 25, 'P50': 26, 'P60': 29 },
    '127': { 'P30': 25, 'P35': 28, 'P40': 29, 'P45': 32, 'P50': 34, 'P60': 38 },
    '147': { 'P30': 29, 'P35': 32, 'P40': 34, 'P45': 36, 'P50': 39, 'P60': 44 }
  },
  T4: {
    '14': { 'P25': 11, 'P30': 12, 'P35': 13, 'P40': 14, 'P45': 15, 'P50': 16, 'P60': 18 },
    '28': { 'P25': 14, 'P30': 15, 'P35': 16, 'P40': 17, 'P45': 19, 'P50': 20, 'P60': 23 },
    '70': { 'P25': 18, 'P30': 19, 'P35': 21, 'P40': 22, 'P45': 25, 'P50': 27, 'P60': 32 },
    '90': { 'P25': 21, 'P30': 24, 'P35': 27, 'P40': 30, 'P45': 32, 'P50': 35, 'P60': 40 },
    '127': { 'P30': 33, 'P35': 37, 'P40': 41, 'P45': 46, 'P50': 49, 'P60': 55 },
    '147': { 'P30': 42, 'P35': 46, 'P40': 50, 'P45': 52, 'P50': 55, 'P60': 62 }
  },
  T5: {
    '14': { 'P25': 14, 'P30': 15, 'P35': 16, 'P40': 17, 'P45': 19, 'P50': 20, 'P60': 23 },
    '28': { 'P25': 18, 'P30': 19, 'P35': 21, 'P40': 23, 'P45': 25, 'P50': 27, 'P60': 31 },
    '70': { 'P25': 24, 'P30': 26, 'P35': 27, 'P40': 29, 'P45': 31, 'P50': 34, 'P60': 40 },
    '90': { 'P25': 31, 'P30': 32, 'P35': 34, 'P40': 37, 'P45': 39, 'P50': 41, 'P60': 48 },
    '127': { 'P30': 42, 'P35': 46, 'P40': 50, 'P45': 54, 'P50': 57, 'P60': 65 },
    '147': { 'P30': 46, 'P35': 49, 'P40': 54, 'P45': 59, 'P50': 62, 'P60': 69 }
  }
};

export const getPuntosPuertaMV = (altoCm, anchoCm, tariff = 'T1') => {
  const tMat = PUERTAS_MATRIZ_MV[tariff] || PUERTAS_MATRIZ_MV.T1;
  let hKey = '70';
  if (altoCm <= 20) hKey = '14';
  else if (altoCm <= 35) hKey = '28';
  else if (altoCm <= 48) hKey = '40';
  else if (altoCm <= 60) hKey = '56';
  else if (altoCm <= 78) hKey = '70';
  else if (altoCm <= 100) hKey = '90';
  else if (altoCm <= 135) hKey = '127';
  else hKey = '147';

  const row = tMat[hKey] || tMat['70'];
  const anchosDisp = [25, 30, 35, 40, 45, 50, 60];
  let bestW = 60, bestDiff = Infinity;
  for (const w of anchosDisp) {
    const diff = Math.abs(w - anchoCm);
    if (diff < bestDiff) { bestDiff = diff; bestW = w; }
  }
  const wKey = `P${bestW}`;
  return row[wKey] || (bestW >= 60 ? (row['P60'] || 16) : (row['P30'] || 11));
};

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
  const detalle = frentes.map(fr => {
    let pts = getPuntosPuertaMV(fr.h, fr.w, tariff);
    if (R.vitrina || f.includes('VITRINA')) pts = Math.round(pts * 1.3);
    puntosTotales += pts;
    return { ...fr, puntos: pts };
  });

  return { frentes: detalle, puntosTotales, numPuertas: frentes.length };
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
  const cc = cascoACB(R.casco, wCasco, altoMm, factorDesmontada, acabadoCasco);
  
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
  const costeTotal = Math.round((cc.coste + costePuertas + costeHerrajes + costeMo) * 100) / 100;

  return {
    fam: familia, med: cc.med, inc: w < 300 ? 'inc. corte' : '',
    casco: cc.coste,
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

// Costes por defecto de componentes (editables desde la UI de Rentabilidad MV).
// Se exporta para que CocinaMontada3 y RelacionReview puedan leerlo/usarlo.
export const MV_COSTES_DEFAULT = {
  dtoPuertas1: 0,   // % descuento 1 sobre tarifa de puertas MV
  dtoPuertas2: 0,   // % descuento 2 (acumulado sobre el resultado del 1)
  dtoPuertas: 0,    // alias legado (compatibilidad)
  bisagra: 0.65,    // € por bisagra (2 por puerta)
  pata4: 0.45,      // € por juego de 4 patas
  colgador: 0.30,   // € por colgador de mueble alto (2 por mueble)
  cajon: 3.50,      // € por cajón
  gaveta: 4.80,     // € por gaveta (cajón con frente completo)
  soporte: 0.15,    // € por soporte/balda (4 por balda)
  mano: 12.00,      // € mano de obra por mueble
};

export default function RentabilidadMV({ esMaster, seed }) {
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
      const coste = (d.casco || 0) + (d.puerta || 0) + (d.bisagras || 0) + (d.patas || 0) + (d.colg || 0) + (d.caj || 0) + (d.gav || 0) + (d.soportes || 0) + (d.mo || 0);
      const pvp = (Number(l.puntos) || 0) * pv;
      return { ...l, ...d, costeUd: coste, pvpUd: pvp, coste: coste * l.cant, pvp: pvp * l.cant, margen: (pvp - coste) * l.cant };
    });
    const tot = rows.reduce((a, r) => ({ pvp: a.pvp + r.pvp, coste: a.coste + r.coste, margen: a.margen + r.margen }), { pvp: 0, coste: 0, margen: 0 });
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
