/*
 * © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * CocinaMontada3.jsx — Módulo Oficial de Presupuestación Rápida de Cocina Montada 3.
 * 
 * Funcionalidades avanzadas:
 *   - Pegado masivo multilínea (WhatsApp, Email, Hojas de corte)
 *   - Paleta interactiva de adición rápida (Bajos, Altos, Columnas, Gaveteros, Lineales)
 *   - Buscador predictivo en tiempo real con sinónimos en lenguaje natural
 *   - Conmutador de tarifas dinámico (T1 a T5) con matriz comparativa en vivo
 *   - Muestrario interactivo de acabados para puertas y cascos con swatches de color
 *   - Selector de cliente CRM, descuentos comerciales y selector de IVA (0%, 10%, 21%)
 *   - Desglose de costes y márgenes con candado 🔒 (Casco neto ACB, puertas por tarifa, herrajes y MO)
 *   - Escandallo técnico para taller con cálculo de tableros, bisagras y tiempos
 *   - Lanzamiento directo de orden de fabricación al módulo de Producción
 *   - Exportación a PDF oficial de alta resolución con jsPDF y copia formateada para WhatsApp
 */
import React, { useState, useEffect, useMemo, useRef } from 'react';
import { 
  FileText, Plus, Trash2, Search, Check, Loader, AlertTriangle, 
  Download, Save, FolderOpen, Lock, Unlock, Sparkles, RefreshCw,
  Copy, Layers, ArrowUpDown, ChevronRight, HelpCircle, Package,
  ClipboardList, CheckCircle2, ChevronDown, Boxes, Box, X, Printer, FileUp,
  User, Percent, Receipt, Phone, Building2, Tag, Calendar, ArrowLeft,
  Palette, Factory, Hammer, Clock, Wrench, ShieldCheck, Play
} from 'lucide-react';
import jsPDF from 'jspdf';
import 'jspdf-autotable';
import { getToken } from '../services/api';
import { usePulsacionLarga, AYUDA_CANDADO } from '../utils/pulsacionLarga';
import { despiece, MV_COSTES_DEFAULT, getFactorDesmontada } from './RentabilidadMV';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const eur = (n) => (n == null ? '—' : `${Number(n).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} €`);

const norm = (s) => (s || '').toString()
  .normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();

const TIPOS_SIN_ANCHO = new Set(['ent_med', 'h355060']);
const PAT_ANCHO = /^[A-Z]+(\d{2,3})(?:D\/I|D|I)?$/;
const anchoDeCod = (cod, type) => {
  if (TIPOS_SIN_ANCHO.has(type)) return null;
  const m = PAT_ANCHO.exec(cod || '');
  return m ? Number(m[1]) : null;
};

const pvpDeItem = (val, pv) => {
  if (typeof val === 'number') return { eur: Math.round(val * pv * 100) / 100, desde: false };
  if (Array.isArray(val)) {
    const ns = val.filter(n => typeof n === 'number');
    if (!ns.length) return null;
    return { eur: Math.round(Math.min(...ns) * pv * 100) / 100, desde: true };
  }
  return null;
};

const costeDetalladoDe = (m, p, tarifa, pvVal, acabadoCasco) => {
  return despiece({ cod: m.cod, altura: m.alto ? String(m.alto) : '', familia: m.familia }, p, tarifa, pvVal, acabadoCasco);
};

const PALETA_RAPIDA = [
  { grupo: 'Bajos', items: [
    { label: 'B60', expr: '1 b60d', desc: 'Bajo 1P 60' },
    { label: 'B45', expr: '1 b45d', desc: 'Bajo 1P 45' },
    { label: 'B90 (2P)', expr: '1 b90', desc: 'Bajo 2P 90' },
    { label: 'BF60 Freg.', expr: '1 bf60', desc: 'Fregadero 60' },
    { label: 'BF90 Freg.', expr: '1 bf90', desc: 'Fregadero 90' },
    { label: 'BGF80 (2 Gav)', expr: '1 bgf80', desc: '2 Gavetas 80' },
    { label: 'BGF90 (2 Gav)', expr: '1 bgf90', desc: '2 Gavetas 90' },
    { label: 'BCG60 (3C+1G)', expr: '1 bcg60', desc: 'Cajonero 60' },
    { label: 'BR90 Rincón', expr: '1 br90', desc: 'Rincón Ciego 90' },
    { label: 'BH60 Horno', expr: '1 bh60', desc: 'Bajo Horno 60' },
  ]},
  { grupo: 'Altos', items: [
    { label: 'A60 (h90)', expr: '1 a60d (altura 90)', desc: 'Alto 1P 60 h90' },
    { label: 'A45 (h90)', expr: '1 a45d (altura 90)', desc: 'Alto 1P 45 h90' },
    { label: 'A90 (2P h90)', expr: '1 a90 (altura 90)', desc: 'Alto 2P 90 h90' },
    { label: 'ASC60 Camp.', expr: '1 asc60d (altura 90)', desc: 'Campana 60' },
    { label: 'ASCE90 Camp.', expr: '1 asce90 (altura 90)', desc: 'Campana 90' },
    { label: 'AA60 Abat.', expr: '1 aa60 (altura 90)', desc: 'Abatible 60' },
    { label: 'AA90 Abat.', expr: '1 aa90 (altura 90)', desc: 'Abatible 90' },
    { label: 'AV60 Vitrina', expr: '1 av60d (altura 90)', desc: 'Vitrina 60' },
    { label: 'AR65 Rincón', expr: '1 ar65d (altura 90)', desc: 'Rincón 65' },
  ]},
  { grupo: 'Columnas', items: [
    { label: 'CD60 Desp.', expr: '1 cd60d (altura 200)', desc: 'Despensero 60' },
    { label: 'CH60 Horno', expr: '1 ch60 (altura 200)', desc: 'Columna Horno 60' },
    { label: 'CHM60 H+M', expr: '1 chm60 (altura 200)', desc: 'Horno + Micro 60' },
    { label: 'CF60 Frigo', expr: '1 cf60 (altura 200)', desc: 'Frigo Integrable 60' },
  ]},
  { grupo: 'Lineales y Remates', items: [
    { label: 'Costado Bajo', expr: '1 ccb', desc: 'Costado Bajo' },
    { label: 'Costado Alto', expr: '1 cca', desc: 'Costado Alto' },
    { label: 'Costado Col.', expr: '1 ccc', desc: 'Costado Columna' },
    { label: 'Zócalo Alum.', expr: '1 zoc', desc: 'Tira Zócalo' },
    { label: 'Copete', expr: '1 cop', desc: 'Tira Copete' },
  ]}
];

const TARIFAS_NOMBRES = {
  T1: 'Sincro / Melamina Texturada (Base)',
  T2: 'Estratificado Mate / Seda',
  T3: 'Lacado Seda / Brillo',
  T4: 'ZENIT Supermate Antihuella',
  T5: 'FENIX NTM Alta Resistencia'
};

const MUESTRARIO_PUERTAS = {
  T1: [
    { id: 't1-roble', nombre: 'Roble Sincro', color: '#b58d67' },
    { id: 't1-nogal', nombre: 'Nogal Pacific', color: '#6e4c36' },
    { id: 't1-gris', nombre: 'Gris Texturado', color: '#8e9092' },
    { id: 't1-blanco', nombre: 'Blanco Polar', color: '#f3f4f6' }
  ],
  T2: [
    { id: 't2-blanco-seda', nombre: 'Blanco Seda', color: '#f9fafb' },
    { id: 't2-cashmere', nombre: 'Cashmere Seda', color: '#d8cfc4' },
    { id: 't2-verde', nombre: 'Verde Oliva Seda', color: '#687766' },
    { id: 't2-antracita', nombre: 'Antracita Seda', color: '#374151' }
  ],
  T3: [
    { id: 't3-blanco-brillo', nombre: 'Blanco Puro Brillo', color: '#ffffff' },
    { id: 't3-blanco-mate', nombre: 'Blanco Seda Mate', color: '#f1f5f9' },
    { id: 't3-negro', nombre: 'Negro Carbón Lacado', color: '#1e293b' },
    { id: 't3-azul', nombre: 'Azul Noche Lacado', color: '#1e3a8a' }
  ],
  T4: [
    { id: 't4-zenit-blanco', nombre: 'ZENIT Blanco Supermate', color: '#fafafa' },
    { id: 't4-zenit-antracita', nombre: 'ZENIT Antracita Metal', color: '#334155' },
    { id: 't4-zenit-basalto', nombre: 'ZENIT Gris Basalto', color: '#475569' },
    { id: 't4-zenit-croma', nombre: 'ZENIT Croma Oro', color: '#854d0e' }
  ],
  T5: [
    { id: 't5-fenix-negro', nombre: 'FENIX Nero Ingo (Antihuella)', color: '#0f172a' },
    { id: 't5-fenix-blanco', nombre: 'FENIX Bianco Kos', color: '#ffffff' },
    { id: 't5-fenix-londra', nombre: 'FENIX Grigio Londra', color: '#52525b' },
    { id: 't5-fenix-verde', nombre: 'FENIX Verde Comodoro', color: '#2d3b36' }
  ]
};

const MUESTRARIO_CASCOS = [
  { id: 'grafito-19', nombre: 'Grafito Antracita (19mm)', color: '#334155', grosor: 19 },
  { id: 'blanco-hidro-19', nombre: 'Blanco Hidrófugo (19mm)', color: '#f8fafc', grosor: 19 },
  { id: 'roble-aurora-19', nombre: 'Roble Aurora (19mm)', color: '#c49a6c', grosor: 19 },
  { id: 'blanco-16', nombre: 'Blanco En Kit (16mm)', color: '#ffffff', grosor: 16 },
  { id: 'aluminio-16', nombre: 'Aluminio Textura (16mm)', color: '#94a3b8', grosor: 16 }
];

export default function CocinaMontada3({ currentUser, state, setState, logo }) {
  const [cliente, setCliente] = useState('');
  const [ref, setRef] = useState('');
  const [telefono, setTelefono] = useState('');
  const [descuento, setDescuento] = useState(0);
  const [ivaRate, setIvaRate] = useState(21);
  const [acabadoPuerta, setAcabadoPuerta] = useState(MUESTRARIO_PUERTAS.T1[0].nombre);
  const [acabadoCasco, setAcabadoCasco] = useState(MUESTRARIO_CASCOS[0].nombre);
  
  const [muebles, setMuebles] = useState([]);
  const [observacionesGenerales, setObservacionesGenerales] = useState('');
  const [busca, setBusca] = useState('');
  const [buscando, setBuscando] = useState(false);
  const [aviso, setAviso] = useState('');
  const [guardando, setGuardando] = useState(false);
  const [savedId, setSavedId] = useState(null);
  
  const [verCoste, setVerCoste] = useState(false);
  const [pistaCandado, setPistaCandado] = useState('');
  
  // Modales y vistas
  const [showPegadoMasivo, setShowPegadoMasivo] = useState(false);
  const [textoMasivo, setTextoMasivo] = useState('');
  const [showComparador, setShowComparador] = useState(false);
  const [showEscandallo, setShowEscandallo] = useState(false);
  const [showMuestrario, setShowMuestrario] = useState(false);
  const [filtroCat, setFiltroCat] = useState('TODOS');
  const [copiadoWs, setCopiadoWs] = useState(false);
  const [showModalDtos, setShowModalDtos] = useState(false);
  
  // Descuentos comerciales de compra en fábrica de puertas (Descuento 1 + Descuento 2 en cascada)
  const [dtoPuertas1, setDtoPuertas1] = useState(() => {
    try { return parseFloat(localStorage.getItem('dto_puertas_1') || localStorage.getItem('dto_puertas') || '50'); } catch { return 50; }
  });
  const [dtoPuertas2, setDtoPuertas2] = useState(() => {
    try { return parseFloat(localStorage.getItem('dto_puertas_2') || '0'); } catch { return 0; }
  });

  useEffect(() => {
    try {
      localStorage.setItem('dto_puertas_1', String(dtoPuertas1));
      localStorage.setItem('dto_puertas_2', String(dtoPuertas2));
      localStorage.setItem('dto_puertas', String(dtoPuertas1));
    } catch { /* noop */ }
  }, [dtoPuertas1, dtoPuertas2]);

  const p = useMemo(() => {
    try { 
      const s = JSON.parse(localStorage.getItem('mv_costes') || 'null'); 
      return s ? { ...MV_COSTES_DEFAULT, ...s } : MV_COSTES_DEFAULT; 
    } catch { 
      return MV_COSTES_DEFAULT; 
    }
  }, []);

  const paramsCostes = useMemo(() => ({
    ...p,
    dtoPuertas1,
    dtoPuertas2,
  }), [p, dtoPuertas1, dtoPuertas2]);

  const [familias, setFamilias] = useState(null);
  const [pv, setPv] = useState(3.33);
  const [tarifa, setTarifa] = useState(() => {
    try { return localStorage.getItem('mv_tarifa') || 'T1'; } catch { return 'T1'; }
  });
  const [tarifas, setTarifas] = useState([]);

  const authHeaders = () => {
    const token = getToken();
    return {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    };
  };

  useEffect(() => {
    fetch(`${API_URL}/api/cascos/mv/tarifas`, { headers: authHeaders() })
      .then(r => r.json())
      .then(d => { if (d.success) setTarifas(d.tarifas || []); })
      .catch(() => {});
  }, []);

  useEffect(() => {
    try { localStorage.setItem('mv_tarifa', tarifa); } catch { /* noop */ }
    fetch(`${API_URL}/api/cascos/mv/tarifa?tariff=${encodeURIComponent(tarifa)}`, { headers: authHeaders() })
      .then(r => r.json())
      .then(d => {
        if (d.success) {
          setFamilias(d.familias);
          const newPv = d.pointValue || 3.33;
          setPv(newPv);
          // Actualizar acabado por defecto de la tarifa
          if (MUESTRARIO_PUERTAS[tarifa]) {
            setAcabadoPuerta(MUESTRARIO_PUERTAS[tarifa][0].nombre);
          }
          setMuebles(prev => prev.map(m => {
            const baseCod = String(m.cod || '').replace(/(D\/I|D|I)$/i, '');
            const info = d.familias?.[m.familia];
            const e = info?.items?.[m.cod] || info?.items?.[baseCod];
            if (e == null) return m;
            let pvp = m.pvp;
            if (Array.isArray(e)) {
              const t = info.type;
              let i = 0;
              if (t === 'h7090') i = (m.alto || 90) >= 85 ? 1 : 0;
              else if (t === 'h127147') i = (m.alto || 127) > 137 ? 1 : 0;
              else if (t === 'h200220') i = (m.alto || 200) > 210 ? 1 : 0;
              pvp = Math.round((e[i] || e[0]) * newPv * 100) / 100;
            } else if (typeof e === 'number') {
              pvp = Math.round(e * newPv * 100) / 100;
            }
            return { ...m, pvp };
          }));
        }
      })
      .catch(() => {});
  }, [tarifa]);

  const catalogo = useMemo(() => {
    if (!familias) return [];
    const out = [];
    for (const [fam, info] of Object.entries(familias)) {
      const items = info?.items;
      if (!items || typeof items !== 'object') continue;
      for (const [cod, val] of Object.entries(items)) {
        const desc = (val && typeof val === 'object' && !Array.isArray(val)) ? val.desc : null;
        const etiqueta = fam.replace(/_/g, ' ');
        out.push({
          cod, familia: fam, etiqueta, desc,
          ancho: anchoDeCod(cod, info.type),
          precio: pvpDeItem(val, pv),
          busca: norm(`${cod} ${etiqueta} ${desc || ''}`),
        });
      }
    }
    return out;
  }, [familias, pv]);

  const [sel, setSel] = useState(0);
  const [foco, setFoco] = useState(false);
  const sugerencias = useMemo(() => {
    const q = norm(busca).trim();
    if (!q || !catalogo.length) return [];
    if (/^\s*\d+\s*\S/.test(busca) || busca.includes('(')) return [];
    const term = q.split(/\s+/).filter(Boolean);
    const hits = catalogo.filter(c => term.every(t => c.busca.includes(t)));
    hits.sort((a, b) => {
      const ap = a.cod.toLowerCase().startsWith(q) ? 0 : 1;
      const bp = b.cod.toLowerCase().startsWith(q) ? 0 : 1;
      return ap - bp || a.cod.localeCompare(b.cod);
    });
    return hits.slice(0, 40);
  }, [busca, catalogo]);

  const OPCIONES_ALTURA = { h7090: [90, 70], h127147: [127, 147], h200220: [200, 220], bajo: [80, 70] };
  const alturasDe = (m) => {
    const fam = String(m.familia || '').toUpperCase();
    const tipo = String(m.tipo || '').toUpperCase();
    if (fam.startsWith('BAJO') || tipo === 'BAJO') return [80, 70];
    const t = familias?.[m.familia]?.type;
    return OPCIONES_ALTURA[t] || null;
  };

  const puntosLocal = (m, alto) => {
    const info = familias?.[m.familia];
    const e = info?.items?.[m.cod];
    if (e == null) return m.pvp;
    if (Array.isArray(e)) {
      const t = info.type;
      let i = 0;
      if (t === 'h7090') i = alto >= 85 ? 1 : 0;
      else if (t === 'h127147') i = alto > 137 ? 1 : 0;
      else if (t === 'h200220') i = alto > 210 ? 1 : 0;
      return Math.round((e[i] || e[0]) * pv * 100) / 100;
    }
    return typeof e === 'number' ? Math.round(e * pv * 100) / 100 : m.pvp;
  };

  const setQty = (k, deltaOrVal, isDelta = false) => {
    setMuebles(prev => prev.map(m => {
      if (m._k !== k) return m;
      const cur = Number(m.qty) || 1;
      const next = isDelta ? Math.max(1, cur + deltaOrVal) : Math.max(1, Number(deltaOrVal) || 1);
      return { ...m, qty: next };
    }));
  };

  const setAlto = (k, v) => setMuebles(prev => prev.map(m => {
    if (m._k !== k) return m;
    const alto = Number(v) || null;
    return { ...m, alto, pvp: puntosLocal(m, alto) };
  }));

  const setObs = (k, obs) => {
    setMuebles(prev => prev.map(m => m._k === k ? { ...m, obs } : m));
  };

  const quitar = (k) => setMuebles(prev => prev.filter(m => m._k !== k));

  const _MANO_SUFIJO = /(D\/I|D|I)$/;
  const manoDe = (cod) => {
    const m = _MANO_SUFIJO.exec(String(cod || '').toUpperCase());
    if (!m) return undefined;
    return m[1] === 'D/I' ? null : m[1];
  };

  const rotarMano = (k) => {
    setMuebles(prev => prev.map(m => {
      if (m._k !== k) return m;
      const cod = String(m.cod || '');
      const cur = manoDe(cod);
      if (cur === undefined) return m;
      let nextMano = 'D';
      if (cur === null) nextMano = 'D';
      else if (cur === 'D') nextMano = 'I';
      else if (cur === 'I') nextMano = 'D/I';
      return { ...m, cod: cod.replace(/(D\/I|D|I)$/i, nextMano === 'D/I' ? 'D/I' : nextMano), mano: nextMano === 'D/I' ? '' : nextMano };
    }));
  };

  const fijarTodasManos = (mano) => {
    setMuebles(prev => prev.map(m => {
      const cur = manoDe(m.cod);
      if (cur === undefined || cur !== null) return m;
      return { ...m, cod: String(m.cod).replace(/(D\/I)$/i, mano), mano: mano };
    }));
  };

  const sinMano = muebles.filter(m => manoDe(m.cod) === null).length;

  const filas = muebles.map(m => {
    const desp = m.encontrado ? costeDetalladoDe(m, paramsCostes, tarifa, pv, acabadoCasco) : { costeTotal: 0, casco: 0, cascoPvp: 0, puerta: 0, puertaPvp: 0 };
    const coste = desp.costeTotal || 0;
    const pvp = Number(m.pvp) || 0;
    const margen = pvp - coste;
    const margenPct = pvp > 0 ? (margen / pvp) * 100 : 0;
    return { ...m, despiece: desp, coste, margen, margenPct };
  });

  const totalUds = muebles.reduce((s, m) => s + (Number(m.qty) || 1), 0);
  const subtotalBruto = filas.reduce((s, m) => s + m.pvp * (Number(m.qty) || 1), 0);
  const importeDescuento = subtotalBruto * (Number(descuento) || 0) / 100;
  const baseImponible = subtotalBruto - importeDescuento;
  const cuotaIva = baseImponible * (Number(ivaRate) || 0) / 100;
  const totalPvp = baseImponible + cuotaIva;

  const totalCoste = filas.reduce((s, m) => s + m.coste * (Number(m.qty) || 1), 0);
  const totalMargen = baseImponible - totalCoste;
  const totalMargenPct = baseImponible > 0 ? (totalMargen / baseImponible) * 100 : 0;

  // Métricas avanzadas y Escandallo de Taller
  const metricas = useMemo(() => {
    let bajosUds = 0, altosUds = 0, colUds = 0, linUds = 0;
    let bajosAnchoCm = 0, altosAnchoCm = 0;
    let totalPuertasM2 = 0;
    let totalBisagras = 0;
    let totalCajones = 0;
    let totalGavetas = 0;
    let totalPatas = 0;
    let totalColgadores = 0;

    filas.forEach(f => {
      const q = Number(f.qty) || 1;
      const t = String(f.tipo || '').toUpperCase();
      const w = Number(f.ancho) || 0;
      if (t === 'BAJO') { bajosUds += q; bajosAnchoCm += w * q; }
      else if (t === 'ALTO') { altosUds += q; altosAnchoCm += w * q; }
      else if (t === 'COLUMNA') { colUds += q; }
      else { linUds += q; }

      if (f.despiece) {
        totalPuertasM2 += (f.despiece.areaPuertas || 0) * q;
        totalBisagras += (f.despiece.puertas || 0) * 2 * q;
        totalCajones += (f.despiece.caj ? (f.despiece.caj / (p.cajon || 1)) : 0) * q;
        totalGavetas += (f.despiece.gav ? (f.despiece.gav / (p.gaveta || 1)) : 0) * q;
        if (t === 'BAJO' || t === 'COLUMNA') totalPatas += 4 * q;
        if (t === 'ALTO') totalColgadores += 2 * q;
      }
    });

    const minutosEnsamblado = (bajosUds * 25) + (altosUds * 20) + (colUds * 40);

    return {
      bajosUds, altosUds, colUds, linUds,
      metrosBajos: (bajosAnchoCm / 100).toFixed(2),
      metrosAltos: (altosAnchoCm / 100).toFixed(2),
      totalPuertasM2: totalPuertasM2.toFixed(2),
      totalBisagras,
      totalCajones: Math.round(totalCajones),
      totalGavetas: Math.round(totalGavetas),
      totalPatas,
      totalColgadores,
      tiempoTallerHoras: (minutosEnsamblado / 60).toFixed(1)
    };
  }, [filas, p]);

  const filasFiltradas = useMemo(() => {
    if (filtroCat === 'TODOS') return filas;
    if (filtroCat === 'BAJOS') return filas.filter(f => f.tipo === 'BAJO');
    if (filtroCat === 'ALTOS') return filas.filter(f => f.tipo === 'ALTO');
    if (filtroCat === 'COLUMNAS') return filas.filter(f => f.tipo === 'COLUMNA');
    if (filtroCat === 'LINEALES') return filas.filter(f => f.tipo !== 'BAJO' && f.tipo !== 'ALTO' && f.tipo !== 'COLUMNA');
    return filas;
  }, [filas, filtroCat]);

  const fundir = (prev, nuevos) => {
    const out = [...prev];
    for (const n of nuevos) {
      const i = out.findIndex(m => m.cod && n.cod && m.cod === n.cod
        && (m.alto ?? null) === (n.alto ?? null));
      if (i >= 0) out[i] = { ...out[i], qty: (Number(out[i].qty) || 1) + (Number(n.qty) || 1) };
      else out.push(n);
    }
    return out;
  };

  const añadirTexto = async (texto) => {
    const t = (texto || '').trim();
    if (!t) return;
    setBuscando(true); setAviso('');
    try {
      const r = await fetch(`${API_URL}/api/cascos/mv/detectar-relacion`, {
        method: 'POST', headers: authHeaders(),
        body: JSON.stringify({ texto: t, tariff: tarifa }),
      });
      let d = {}; try { d = await r.json(); } catch { d = {}; }
      if (!r.ok || !d.success) { setAviso(d.detail || 'No se reconoció el mueble. Escríbelo como "1 b60i (altura 80)".'); return; }
      const nuevos = (d.muebles || []).map((m, i) => ({ ...m, _k: `add-${Date.now()}-${i}` }));
      setMuebles(prev => fundir(prev, nuevos));
      setBusca('');
      setFoco(false);
    } catch (e) {
      setAviso(`Error al buscar (${e?.message || 'red'}).`);
    } finally { setBuscando(false); }
  };

  const procesarPegadoMasivo = async () => {
    if (!textoMasivo.trim()) return;
    await añadirTexto(textoMasivo);
    setTextoMasivo('');
    setShowPegadoMasivo(false);
  };

  const añadirSugerencia = (c) => {
    if (!c) return;
    const info = familias?.[c.familia];
    const opciones = OPCIONES_ALTURA[info?.type];
    const alto = opciones ? opciones[0] : (c.familia?.startsWith('BAJO') ? 80 : null);
    const pvp = puntosLocal({ cod: c.cod, familia: c.familia, pvp: c.precio?.eur }, alto);
    const nuevo = {
      _k: `add-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
      cod: c.cod,
      familia: c.familia,
      tipo: c.familia?.startsWith('BAJO') ? 'BAJO' : c.familia?.startsWith('ALTO') ? 'ALTO' : 'COLUMNA',
      ancho: c.ancho,
      alto: alto,
      fondo: c.familia?.startsWith('ALTO') ? 33 : 58,
      mano: c.cod.endsWith('D') ? 'D' : c.cod.endsWith('I') ? 'I' : '',
      qty: 1,
      pvp: pvp,
      encontrado: true,
      raw: c.cod,
    };
    setMuebles(prev => fundir(prev, [nuevo]));
    setBusca('');
    setFoco(false);
  };

  const comparativaTarifas = useMemo(() => {
    const multTarifas = { T1: 1.0, T2: 1.15, T3: 1.28, T4: 1.42, T5: 1.60 };
    return ['T1', 'T2', 'T3', 'T4', 'T5'].map(t => {
      const totalEst = baseImponible * (multTarifas[t] / multTarifas[tarifa || 'T1']);
      return {
        tarifa: t,
        nombre: TARIFAS_NOMBRES[t] || t,
        total: totalEst,
        activa: t === tarifa
      };
    });
  }, [baseImponible, tarifa]);

  const copiarParaWhatsApp = () => {
    const lineas = [
      `*PRESUPUESTO COCINA MONTADA MV*`,
      `*Cliente:* ${cliente || 'Particular'} ${ref ? `(Ref: ${ref})` : ''}`,
      `*Tarifa:* ${tarifa} - ${TARIFAS_NOMBRES[tarifa] || 'Estándar'}`,
      `*Color Puertas:* ${acabadoPuerta}`,
      `*Color Cascos:* ${acabadoCasco}`,
      ...(observacionesGenerales?.trim() ? [`*Observaciones:* ${observacionesGenerales.trim()}`] : []),
      `*Muebles Totales:* ${totalUds} unidades`,
      `----------------------------------------`,
      ...muebles.map(m => {
        const manoTxt = m.cod?.endsWith('D') ? ' [Dcha]' : m.cod?.endsWith('I') ? ' [Izq]' : '';
        const obsTxt = m.obs?.trim() ? `\n   └ ✎ Obs: ${m.obs.trim()}` : '';
        return `• ${m.qty}x *${m.cod}* (${m.ancho || '—'}x${m.alto || '—'} cm)${manoTxt} -> ${eur((Number(m.pvp) || 0) * (Number(m.qty) || 1))}${obsTxt}`;
      }),
      `----------------------------------------`,
      `*Subtotal:* ${eur(subtotalBruto)}`,
      ...(descuento > 0 ? [`*Descuento (${descuento}%):* -${eur(importeDescuento)}`] : []),
      `*Base Imponible:* ${eur(baseImponible)}`,
      `*IVA (${ivaRate}%):* ${eur(cuotaIva)}`,
      `*TOTAL FINAL:* ${eur(totalPvp)}`,
    ];
    navigator.clipboard.writeText(lineas.join('\n'));
    setCopiadoWs(true);
    setTimeout(() => setCopiadoWs(false), 2500);
  };

  // Exportador a PDF Oficial con jsPDF
  const exportarPDFOficial = () => {
    const doc = new jsPDF();
    
    // Encabezado Corporativo
    doc.setFillColor(30, 27, 75); // Indigo 950
    doc.rect(0, 0, 210, 35, 'F');
    doc.setTextColor(255, 255, 255);
    doc.setFont('helvetica', 'bold');
    const companyBrand = (state?.settings?.companyName || currentUser?.empresa || 'STUDIO 3K').toUpperCase() + ' · COCINA MONTADA';
    doc.text(companyBrand, 14, 18);
    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    doc.text('Presupuesto Oficial de Fabricación y Mobiliario MV', 14, 26);
    
    doc.setFontSize(9);
    doc.text(`Tarifa: ${tarifa} (${TARIFAS_NOMBRES[tarifa] || 'Estándar'})`, 196, 18, { align: 'right' });
    doc.text(`Fecha: ${new Date().toLocaleDateString('es-ES')}`, 196, 26, { align: 'right' });

    // Ficha Cliente y Acabados
    doc.setTextColor(15, 23, 42);
    doc.setFillColor(248, 250, 252);
    doc.roundedRect(14, 42, 182, 24, 3, 3, 'F');
    
    doc.setFontSize(10);
    doc.setFont('helvetica', 'bold');
    doc.text(`Cliente: ${cliente || 'Particular'}`, 18, 51);
    doc.text(`Referencia: ${ref || 'Proyecto Cocina'}`, 18, 60);

    doc.setFont('helvetica', 'normal');
    doc.text(`Puertas: ${acabadoPuerta}`, 110, 51);
    doc.text(`Cascos: ${acabadoCasco}`, 110, 60);

    // Tabla de Muebles
    const tableBody = muebles.map((m, idx) => {
      const descBase = m.familia?.replace(/_/g, ' ') || m.tipo || 'Mueble';
      const descCompleta = m.obs?.trim() ? `${descBase}\n[Obs: ${m.obs.trim()}]` : descBase;
      return [
        idx + 1,
        m.qty,
        m.cod || '—',
        descCompleta,
        m.ancho ? `${m.ancho} cm` : '—',
        m.alto ? `${m.alto} cm` : '—',
        m.cod?.endsWith('D') ? 'Dcha' : m.cod?.endsWith('I') ? 'Izq' : '—',
        eur(m.pvp),
        eur((Number(m.pvp) || 0) * (Number(m.qty) || 1))
      ];
    });

    doc.autoTable({
      startY: 72,
      head: [['#', 'Cant', 'Código', 'Descripción / Observaciones', 'Ancho', 'Alto', 'Mano', 'PVP Ud.', 'Total']],
      body: tableBody,
      theme: 'grid',
      headStyles: { fillColor: [67, 56, 202], textColor: 255, fontStyle: 'bold', fontSize: 9 },
      styles: { fontSize: 8, cellPadding: 3 },
      columnStyles: {
        0: { halign: 'center', cellWidth: 10 },
        1: { halign: 'center', cellWidth: 14, fontStyle: 'bold' },
        2: { fontStyle: 'bold', textColor: [67, 56, 202] },
        4: { halign: 'center' },
        5: { halign: 'center' },
        6: { halign: 'center' },
        7: { halign: 'right' },
        8: { halign: 'right', fontStyle: 'bold' }
      }
    });

    const finalY = doc.lastAutoTable.finalY + 10;

    // Observaciones Generales en PDF
    if (observacionesGenerales?.trim()) {
      doc.setFontSize(9);
      doc.setFont('helvetica', 'bold');
      doc.setTextColor(30, 27, 75);
      doc.text('Observaciones Generales de la Cocina / Montaje:', 14, finalY);
      doc.setFont('helvetica', 'normal');
      doc.setTextColor(71, 85, 105);
      doc.text(observacionesGenerales.trim(), 14, finalY + 5);
    }

    // Resumen de Totales
    doc.setFillColor(248, 250, 252);
    doc.roundedRect(120, finalY, 76, 38, 3, 3, 'F');
    
    doc.setFontSize(9);
    doc.text(`Subtotal:`, 125, finalY + 8);
    doc.text(eur(subtotalBruto), 190, finalY + 8, { align: 'right' });
    
    if (descuento > 0) {
      doc.setTextColor(220, 38, 38);
      doc.text(`Descuento (${descuento}%):`, 125, finalY + 16);
      doc.text(`-${eur(importeDescuento)}`, 190, finalY + 16, { align: 'right' });
      doc.setTextColor(15, 23, 42);
    }

    doc.text(`Base Imponible:`, 125, finalY + 23);
    doc.text(eur(baseImponible), 190, finalY + 23, { align: 'right' });

    doc.text(`IVA (${ivaRate}%):`, 125, finalY + 29);
    doc.text(eur(cuotaIva), 190, finalY + 29, { align: 'right' });

    doc.setFontSize(11);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(67, 56, 202);
    doc.text(`TOTAL:`, 125, finalY + 36);
    doc.text(eur(totalPvp), 190, finalY + 36, { align: 'right' });

    doc.save(`Presupuesto_Cocina_${cliente || 'Cliente'}_${tarifa}.pdf`);
  };

  const lanzarAFabricacion = async () => {
    if (!muebles.length) { setAviso('Añade al menos un mueble para lanzar a fabricación.'); return; }
    
    const esInterno = window.confirm(
      `¿Dónde se fabricará este pedido de ${totalUds} módulos? (Casco: ${acabadoCasco || 'Grafito Antracita (19mm)'})\n\n` +
      `• Pulsa ACEPTAR para: 🏠 Fabricación Interna (Taller Propio)\n` +
      `• Pulsa CANCELAR para: 🚚 Fabricación Externa (Proveedor / Fuera)`
    );

    const origen = esInterno ? 'INTERNO' : 'EXTERNO';
    const prefijo = esInterno ? 'OF-INT' : 'OF-EXT';
    const tagOrigen = esInterno ? '🏠 Taller Propio (Interno)' : '🚚 Proveedor Externo (Fuera)';

    try {
      const payload = {
        id: `${prefijo}-2026-${Math.floor(100 + Math.random() * 900)}`,
        cliente: cliente || 'Cliente General',
        ref: ref || 'Cocina Montada 3',
        tipo: 'Cocina Montada 3',
        tarifa: `${tarifa} (${acabadoPuerta})`,
        casco: acabadoCasco || 'Grafito Antracita (19mm)',
        origen: origen,
        tagOrigen: tagOrigen,
        modulos: totalUds,
        m2Tablero: Number(metricas.totalPuertasM2) || 25,
        mlCanteado: Math.round(Number(metricas.totalPuertasM2) * 4),
        estado: 'pendiente',
        prioridad: 'NORMAL',
        progreso: 10,
        observaciones: observacionesGenerales ? `${observacionesGenerales} | Casco: ${acabadoCasco} | ${tagOrigen}` : `Casco: ${acabadoCasco} | ${tagOrigen}`,
        fechaInicio: new Date().toISOString().split('T')[0],
        fechaEstRecepcion: new Date(Date.now() + 5 * 86400000).toISOString().split('T')[0],
        fechaEntrega: new Date(Date.now() + 10 * 86400000).toISOString().split('T')[0],
        muebles: muebles.map(m => ({ cod: m.cod, qty: m.qty, ancho: m.ancho, alto: m.alto, mano: m.mano, obs: m.obs })),
      };

      // Persistir orden en el almacén de producción
      try {
        const guardadas = JSON.parse(localStorage.getItem('ordenes_fabricacion_taller') || '[]');
        const actualizadas = [payload, ...guardadas.filter(x => x.id !== payload.id)];
        localStorage.setItem('ordenes_fabricacion_taller', JSON.stringify(actualizadas));
      } catch (e) { console.error('Error guardando OF:', e); }

      alert(`✓ Orden de Fabricación ${payload.id} [${tagOrigen}] lanzada con éxito.`);
      if (setState) {
        setState(prev => ({ ...prev, currentTab: 'planificacionProduccion' }));
      }
    } catch (e) {
      alert(`Error al lanzar a fabricación: ${e.message}`);
    }
  };

  const guardarPresupuesto = async () => {
    if (!muebles.length) { setAviso('Añade al menos un mueble para guardar.'); return; }
    setGuardando(true); setAviso('');
    try {
      const payload = {
        id: savedId || `cm3-${Date.now()}`,
        cliente: cliente || 'Cliente General',
        referencia: ref || 'Proyecto Cocina Montada 3',
        telefono,
        tarifa,
        acabadoPuerta,
        acabadoCasco,
        observaciones: observacionesGenerales,
        descuento: Number(descuento) || 0,
        ivaRate: Number(ivaRate) || 21,
        subtotal: subtotalBruto,
        total: totalPvp,
        muebles,
        tipo: 'cocina_montada_3',
        fecha: new Date().toISOString(),
      };
      const r = await fetch(`${API_URL}/api/presupuestos`, {
        method: 'POST', headers: authHeaders(),
        body: JSON.stringify(payload),
      });
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail || 'Error al guardar');
      setSavedId(d.id || d._id || payload.id);
      alert('✓ Presupuesto guardado con éxito en el sistema.');
    } catch (e) {
      setAviso(`No se pudo guardar: ${e.message}`);
    } finally { setGuardando(false); }
  };

  const handlersCandado = usePulsacionLarga(() => {
    setVerCoste(v => !v);
    setPistaCandado('');
  }, () => {
    setPistaCandado(AYUDA_CANDADO);
    setTimeout(() => setPistaCandado(''), 4000);
  });

  return (
    <div className="absolute inset-0 overflow-y-auto bg-slate-100 p-3 sm:p-6 pb-36 space-y-4">
      
      {/* Cabecera Principal */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white rounded-3xl px-4 py-3 sm:px-5 sm:py-3.5 shadow-xl border border-slate-800 flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-indigo-600 border border-indigo-400/40 flex items-center justify-center shadow-md shadow-indigo-600/30 shrink-0">
            <Layers size={18} className="text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-black text-white tracking-tight">Cocina Montada 3</h1>
              <span className="px-2 py-0.5 rounded-full bg-indigo-500/20 border border-indigo-400/30 text-indigo-200 text-[10px] font-black uppercase">Tarifa {tarifa}</span>
            </div>
            <p className="text-[10px] text-indigo-200/70 font-medium leading-tight">
              {acabadoPuerta} / {acabadoCasco}
            </p>
          </div>
        </div>

        {/* Botonera Central: herramientas secundarias */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <button
            onClick={() => setShowMuestrario(v => !v)}
            className={`flex items-center gap-1 px-2.5 py-1.5 rounded-lg border text-[11px] font-bold transition-all ${showMuestrario ? 'bg-indigo-500 text-white border-indigo-400' : 'bg-white/8 hover:bg-white/15 border-white/10 text-white'}`}
            title="Muestrario de acabados de puertas y cascos"
          >
            <Palette size={13} className="text-indigo-300" /> Acabados
          </button>
          <button
            onClick={() => setShowEscandallo(v => !v)}
            className={`flex items-center gap-1 px-2.5 py-1.5 rounded-lg border text-[11px] font-bold transition-all ${showEscandallo ? 'bg-amber-500 text-slate-950 border-amber-400' : 'bg-white/8 hover:bg-white/15 border-white/10 text-white'}`}
            title="Escandallo técnico de taller"
          >
            <Hammer size={13} className="text-amber-400" /> Escandallo
          </button>
          <button
            onClick={() => setShowPegadoMasivo(true)}
            className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-indigo-600/50 hover:bg-indigo-600 border border-indigo-400/30 text-[11px] font-bold transition-all text-white"
            title="Pegar lista completa de muebles de WhatsApp, email o Word"
          >
            <FileUp size={13} /> Pegado Masivo
          </button>
          <button
            onClick={() => setShowComparador(v => !v)}
            className={`flex items-center gap-1 px-2.5 py-1.5 rounded-lg border text-[11px] font-bold transition-all ${showComparador ? 'bg-amber-500 text-slate-950 border-amber-400' : 'bg-white/8 hover:bg-white/15 border-white/10 text-white'}`}
            title="Comparar presupuesto en todas las tarifas T1-T5"
          >
            <Sparkles size={13} className={showComparador ? 'text-slate-950' : 'text-amber-400'} /> Comparar
          </button>
          <button
            onClick={exportarPDFOficial}
            disabled={!muebles.length}
            className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-white/8 hover:bg-white/15 border border-white/10 text-[11px] font-bold transition-all disabled:opacity-40 text-white"
            title="Exportar PDF oficial del presupuesto"
          >
            <Download size={13} /> PDF
          </button>
        </div>

        {/* CTAs Primarios */}
        <div className="flex items-center gap-1.5">
          <button
            onClick={lanzarAFabricacion}
            disabled={!muebles.length}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-slate-950 font-black text-[11px] shadow-md transition-all disabled:opacity-40"
            title="Crear orden de fabricación en taller"
          >
            <Factory size={13} /> Fabricar
          </button>
          <button
            onClick={guardarPresupuesto}
            disabled={!muebles.length || guardando}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-[11px] font-black shadow-md transition-all disabled:opacity-40"
            title="Guardar presupuesto en el sistema"
          >
            {guardando ? <Loader size={13} className="animate-spin" /> : <Save size={13} />} Guardar
          </button>
        </div>
      </div>

      {/* Muestrario Desplegable de Acabados */}
      {showMuestrario && (
        <div className="bg-white rounded-3xl p-5 border border-slate-200 shadow-sm grid grid-cols-1 md:grid-cols-2 gap-6 animate-in fade-in zoom-in-95">
          {/* Muestrario de Puertas */}
          <div className="space-y-2.5">
            <span className="text-xs font-black text-slate-800 uppercase tracking-wide flex items-center gap-2">
              <Palette size={16} className="text-indigo-600" /> Acabado de Puertas ({tarifa}):
            </span>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {(MUESTRARIO_PUERTAS[tarifa] || MUESTRARIO_PUERTAS.T1).map(ac => (
                <button
                  key={ac.id}
                  onClick={() => setAcabadoPuerta(ac.nombre)}
                  className={`p-2.5 rounded-2xl border text-left transition-all flex flex-col gap-2 ${acabadoPuerta === ac.nombre ? 'border-indigo-600 bg-indigo-50/50 ring-2 ring-indigo-200' : 'border-slate-200 hover:border-slate-300'}`}
                >
                  <div className="w-full h-8 rounded-xl border border-slate-200 shadow-inner" style={{ backgroundColor: ac.color }} />
                  <span className="text-[11px] font-bold text-slate-800 leading-tight">{ac.nombre}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Muestrario de Cascos */}
          <div className="space-y-2.5">
            <span className="text-xs font-black text-slate-800 uppercase tracking-wide flex items-center gap-2">
              <Box size={16} className="text-indigo-600" /> Acabado de Cascos (Grupo ACB):
            </span>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {MUESTRARIO_CASCOS.map(ac => (
                <button
                  key={ac.id}
                  onClick={() => setAcabadoCasco(ac.nombre)}
                  className={`p-2.5 rounded-2xl border text-left transition-all flex flex-col gap-2 ${acabadoCasco === ac.nombre ? 'border-indigo-600 bg-indigo-50/50 ring-2 ring-indigo-200' : 'border-slate-200 hover:border-slate-300'}`}
                >
                  <div className="w-full h-8 rounded-xl border border-slate-200 shadow-inner" style={{ backgroundColor: ac.color }} />
                  <span className="text-[11px] font-bold text-slate-800 leading-tight">{ac.nombre}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Escandallo Técnico de Taller Desplegable */}
      {showEscandallo && (
        <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white rounded-3xl p-5 border border-indigo-500/30 shadow-xl grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3 animate-in fade-in zoom-in-95">
          <div className="p-3 bg-white/5 rounded-2xl border border-white/10">
            <div className="text-[10px] uppercase font-bold text-indigo-300">Tablero Puertas</div>
            <div className="text-lg font-black text-white">{metricas.totalPuertasM2} m²</div>
            <div className="text-[10px] text-indigo-200/70">{acabadoPuerta}</div>
          </div>
          <div className="p-3 bg-white/5 rounded-2xl border border-white/10">
            <div className="text-[10px] uppercase font-bold text-indigo-300">Cascos ACB</div>
            <div className="text-lg font-black text-white">{totalUds} módulos</div>
            <div className="text-[10px] text-indigo-200/70">{acabadoCasco}</div>
          </div>
          <div className="p-3 bg-white/5 rounded-2xl border border-white/10">
            <div className="text-[10px] uppercase font-bold text-indigo-300">Bisagras con Freno</div>
            <div className="text-lg font-black text-white">{metricas.totalBisagras} uds</div>
            <div className="text-[10px] text-indigo-200/70">Blum / Hettich</div>
          </div>
          <div className="p-3 bg-white/5 rounded-2xl border border-white/10">
            <div className="text-[10px] uppercase font-bold text-indigo-300">Cajones & Gavetas</div>
            <div className="text-lg font-black text-white">{metricas.totalCajones + metricas.totalGavetas} uds</div>
            <div className="text-[10px] text-indigo-200/70">{metricas.totalCajones} caj. + {metricas.totalGavetas} gav.</div>
          </div>
          <div className="p-3 bg-white/5 rounded-2xl border border-white/10">
            <div className="text-[10px] uppercase font-bold text-indigo-300">Patas & Colgadores</div>
            <div className="text-lg font-black text-white">{metricas.totalPatas} / {metricas.totalColgadores}</div>
            <div className="text-[10px] text-indigo-200/70">Patas / Colgadores</div>
          </div>
          <div className="p-3 bg-emerald-950/40 rounded-2xl border border-emerald-500/30">
            <div className="text-[10px] uppercase font-bold text-emerald-300">Tiempo de Taller</div>
            <div className="text-lg font-black text-emerald-400">{metricas.tiempoTallerHoras} horas</div>
            <div className="text-[10px] text-emerald-200/70">Ensamblado en taller</div>
          </div>
        </div>
      )}

      {/* Datos del Cliente y Presupuesto */}
      <div className="bg-white rounded-3xl p-5 border border-slate-200 shadow-sm grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
        <div>
          <label className="text-[10px] font-black uppercase text-slate-400 block mb-1">Cliente / Titular</label>
          <div className="relative">
            <User size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              value={cliente}
              onChange={e => setCliente(e.target.value)}
              placeholder="Nombre del cliente o tienda…"
              className="w-full pl-9 pr-3 py-2 border border-slate-200 rounded-xl text-xs font-bold outline-none focus:border-indigo-500"
            />
          </div>
        </div>

        <div>
          <label className="text-[10px] font-black uppercase text-slate-400 block mb-1">Referencia / Obra</label>
          <div className="relative">
            <Tag size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              value={ref}
              onChange={e => setRef(e.target.value)}
              placeholder="Ref. Cocina Paseo Canalejas…"
              className="w-full pl-9 pr-3 py-2 border border-slate-200 rounded-xl text-xs font-bold outline-none focus:border-indigo-500"
            />
          </div>
        </div>

        <div>
          <label className="text-[10px] font-black uppercase text-slate-400 block mb-1">Descuento Comercial (%)</label>
          <div className="relative">
            <Percent size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="number"
              min="0"
              max="100"
              value={descuento}
              onChange={e => setDescuento(e.target.value)}
              placeholder="0%"
              className="w-full pl-9 pr-3 py-2 border border-slate-200 rounded-xl text-xs font-bold outline-none focus:border-indigo-500"
            />
          </div>
        </div>

        <div>
          <label className="text-[10px] font-black uppercase text-slate-400 block mb-1">Tipo de IVA</label>
          <div className="relative">
            <Receipt size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <select
              value={ivaRate}
              onChange={e => setIvaRate(e.target.value)}
              className="w-full pl-9 pr-3 py-2 border border-slate-200 rounded-xl text-xs font-bold outline-none focus:border-indigo-500 bg-white"
            >
              <option value="21">21% (General)</option>
              <option value="10">10% (Reformas)</option>
              <option value="0">0% (Exento / Exportación)</option>
            </select>
          </div>
        </div>

        <div className="sm:col-span-2 md:col-span-3 lg:col-span-1">
          <label className="text-[10px] font-black uppercase text-slate-400 block mb-1">Observaciones Generales</label>
          <div className="relative">
            <FileText size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              value={observacionesGenerales}
              onChange={e => setObservacionesGenerales(e.target.value)}
              placeholder="Notas de montaje/taller…"
              className="w-full pl-9 pr-3 py-2 border border-slate-200 rounded-xl text-xs font-bold outline-none focus:border-indigo-500"
            />
          </div>
        </div>
      </div>

      {/* Comparador de Tarifas Desplegable */}
      {showComparador && (
        <div className="bg-gradient-to-r from-amber-500/10 via-indigo-500/10 to-amber-500/10 border border-amber-200 rounded-3xl p-4 flex items-center justify-between gap-4 overflow-x-auto shadow-sm">
          <div className="flex items-center gap-2 shrink-0">
            <Sparkles size={18} className="text-amber-600" />
            <span className="font-black text-xs text-slate-900 uppercase tracking-wide">Presupuesto en otras Tarifas:</span>
          </div>
          <div className="flex items-center gap-3">
            {comparativaTarifas.map(ct => (
              <button
                key={ct.tarifa}
                onClick={() => setTarifa(ct.tarifa)}
                className={`px-4 py-2 rounded-2xl border text-left transition-all ${ct.activa ? 'bg-indigo-600 text-white border-indigo-600 shadow-md ring-2 ring-indigo-300' : 'bg-white text-slate-700 border-slate-200 hover:border-indigo-300'}`}
              >
                <div className="text-[10px] font-black uppercase opacity-80">{ct.tarifa} - {ct.nombre.split('/')[0]}</div>
                <div className="text-sm font-black">{eur(ct.total)}</div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Panel de Trabajo: Buscador, Paleta y Tabla */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden flex flex-col flex-1">
        
        {/* Barra Superior del Panel */}
        <div className="p-5 border-b border-slate-100 space-y-3">
          {/* Selector de Tarifa y Métricas */}
          <div className="flex items-center justify-between gap-4 flex-wrap text-xs">
            <div className="flex items-center gap-2">
              <span className="font-bold text-slate-500 uppercase text-[10px] tracking-wider">Tarifa:</span>
              <div className="flex gap-1 bg-slate-100 p-1 rounded-xl">
                {['T1', 'T2', 'T3', 'T4', 'T5'].map(t => (
                  <button
                    key={t}
                    onClick={() => setTarifa(t)}
                    className={`px-3 py-1 rounded-lg font-black text-xs transition-all ${tarifa === t ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-600 hover:bg-white'}`}
                  >
                    {t}
                  </button>
                ))}
              </div>
              <span className="text-xs text-slate-500 font-semibold italic hidden sm:inline">
                ({TARIFAS_NOMBRES[tarifa] || 'Acabado estándar'})
              </span>
            </div>

            <div className="flex items-center gap-2.5">
              <div className="flex items-center gap-1.5 px-3 py-1 rounded-xl bg-emerald-50 text-emerald-800 border border-emerald-200 font-bold text-xs">
                <Package size={14} /> Bajos: {metricas.bajosUds} ({metricas.metrosBajos} m)
              </div>
              <div className="flex items-center gap-1.5 px-3 py-1 rounded-xl bg-sky-50 text-sky-800 border border-sky-200 font-bold text-xs">
                <Package size={14} /> Altos: {metricas.altosUds} ({metricas.metrosAltos} m)
              </div>
              <div className="flex items-center gap-1.5 px-3 py-1 rounded-xl bg-indigo-50 text-indigo-800 border border-indigo-200 font-bold text-xs">
                <Package size={14} /> Columnas: {metricas.colUds}
              </div>
              {sinMano > 0 && (
                <button
                  onClick={() => fijarTodasManos('D')}
                  className="flex items-center gap-1 px-3 py-1 rounded-xl bg-amber-100 text-amber-900 border border-amber-300 font-black text-xs hover:bg-amber-200 transition-colors animate-pulse"
                >
                  <AlertTriangle size={14} className="text-amber-600" /> {sinMano} sin mano · Fijar Dcha
                </button>
              )}
            </div>
          </div>

          {/* Buscador predictivo en vivo */}
          <div className="relative">
            <div className="flex items-center gap-2">
              <div className="relative flex-1">
                <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  value={busca}
                  onChange={e => setBusca(e.target.value)}
                  onFocus={() => setFoco(true)}
                  onKeyDown={e => {
                    if (!sugerencias.length) { if (e.key === 'Enter') añadirTexto(busca); return; }
                    if (e.key === 'ArrowDown') { e.preventDefault(); setSel(s => (s + 1) % sugerencias.length); }
                    else if (e.key === 'ArrowUp') { e.preventDefault(); setSel(s => (s - 1 + sugerencias.length) % sugerencias.length); }
                    else if (e.key === 'Enter') { e.preventDefault(); añadirSugerencia(sugerencias[sel]); }
                    else if (e.key === 'Escape') { setFoco(false); }
                  }}
                  placeholder="Escribe un código o descripción (ej.: 1 b60i, asc60d, fregadero 60, col60, 2 gavetero 80)…"
                  className="w-full pl-11 pr-4 py-3 rounded-2xl border border-slate-200 text-sm font-medium focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 outline-none transition-all shadow-inner bg-slate-50/50"
                />
                {buscando && <Loader size={18} className="absolute right-4 top-1/2 -translate-y-1/2 text-indigo-600 animate-spin" />}
              </div>
              <button
                onClick={() => añadirTexto(busca)}
                disabled={!busca.trim() || buscando}
                className="px-6 py-3 rounded-2xl bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-bold text-sm shadow-md transition-all flex items-center gap-2"
              >
                <Plus size={18} /> Añadir Mueble
              </button>
            </div>

            {/* Desplegable de Sugerencias */}
            {foco && sugerencias.length > 0 && (
              <div className="absolute left-0 right-0 top-full mt-2 bg-white border border-slate-200 rounded-2xl shadow-2xl z-30 max-h-80 overflow-y-auto divide-y divide-slate-100">
                {sugerencias.map((c, i) => (
                  <button
                    key={c.cod}
                    type="button"
                    onClick={() => añadirSugerencia(c)}
                    className={`w-full px-5 py-2.5 text-left flex items-center justify-between gap-3 text-xs transition-colors ${i === sel ? 'bg-indigo-50 text-indigo-900 font-bold' : 'hover:bg-slate-50'}`}
                  >
                    <div className="flex items-center gap-3">
                      <span className="font-mono font-black text-indigo-600 text-sm">{c.cod}</span>
                      <span className="text-slate-700 font-medium">{c.etiqueta}</span>
                      {c.ancho && <span className="px-2 py-0.5 rounded-md bg-slate-100 text-[10px] text-slate-500 font-bold">{c.ancho} cm</span>}
                    </div>
                    <span className="font-mono font-black text-slate-900">{c.precio ? `${c.precio.desde ? 'desde ' : ''}${eur(c.precio.eur)}` : '—'}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Paleta Rápida por Chips */}
          <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
            <span className="text-[10px] font-black text-slate-400 uppercase shrink-0">Atajos rápidos:</span>
            {PALETA_RAPIDA.map(grp => (
              <div key={grp.grupo} className="flex items-center gap-1 bg-slate-100/70 p-1 rounded-xl shrink-0">
                <span className="text-[9px] font-black text-slate-400 uppercase px-1.5">{grp.grupo}:</span>
                {grp.items.map(it => (
                  <button
                    key={it.label}
                    onClick={() => añadirTexto(it.expr)}
                    className="px-2.5 py-1 rounded-lg bg-white border border-slate-200 hover:border-indigo-400 hover:text-indigo-600 font-bold text-xs text-slate-700 shadow-2xs transition-all"
                    title={it.desc}
                  >
                    + {it.label}
                  </button>
                ))}
              </div>
            ))}
          </div>
        </div>

        {/* Pestañas de Filtro y Botón WhatsApp */}
        <div className="px-6 pt-3 bg-slate-50/50 border-b border-slate-100 flex items-center justify-between gap-4 flex-wrap">
          <div className="flex gap-1 border-b border-slate-200 -mb-[1px]">
            {['TODOS', 'BAJOS', 'ALTOS', 'COLUMNAS', 'LINEALES'].map(cat => (
              <button
                key={cat}
                onClick={() => setFiltroCat(cat)}
                className={`px-4 py-2 border-b-2 font-black text-xs transition-all ${filtroCat === cat ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-slate-400 hover:text-slate-700'}`}
              >
                {cat} {cat === 'TODOS' ? `(${muebles.length})` : ''}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-2 pb-2">
            <button
              onClick={copiarParaWhatsApp}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all border ${copiadoWs ? 'bg-emerald-600 text-white border-emerald-600' : 'bg-emerald-50 text-emerald-800 border-emerald-200 hover:bg-emerald-100'}`}
            >
              {copiadoWs ? <Check size={14} /> : <Copy size={14} />} {copiadoWs ? '¡Copiado para WhatsApp!' : 'Copiar WhatsApp'}
            </button>
          </div>
        </div>

        {/* Tabla de Muebles */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 divide-y divide-slate-100 min-h-[300px]">
          {filasFiltradas.length === 0 ? (
            <div className="py-20 text-center text-slate-400 space-y-3">
              <Package size={48} className="mx-auto text-slate-300 opacity-60" />
              <p className="text-base font-bold text-slate-600">No hay muebles añadidos en este presupuesto</p>
              <p className="text-xs max-w-md mx-auto">
                Escribe en el buscador superior (ej: <code>1 b60i</code>, <code>asc60d</code>, <code>fregadero 60</code>) o usa el botón <b>Pegado Masivo</b>.
              </p>
            </div>
          ) : (
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-200 text-[10px] font-black uppercase text-slate-400">
                  <th className="py-2.5 px-2 text-center w-10">#</th>
                  <th className="py-2.5 px-3 text-center w-28">Cantidad</th>
                  <th className="py-2.5 px-3">Código</th>
                  <th className="py-2.5 px-3">Descripción / Familia</th>
                  <th className="py-2.5 px-3 text-center">Ancho</th>
                  <th className="py-2.5 px-3 text-center">Alto</th>
                  <th className="py-2.5 px-3 text-center">Mano</th>
                  {verCoste && <th className="py-2.5 px-3 text-right text-purple-700" title="Coste Neto de Casco ACB">Casco Neto (ACB)</th>}
                  {verCoste && <th className="py-2.5 px-3 text-right text-purple-700" title={`Coste de Puertas según Tarifa ${tarifa}`}>Puertas ({tarifa})</th>}
                  {verCoste && <th className="py-2.5 px-3 text-right text-purple-700">Coste Total</th>}
                  {verCoste && <th className="py-2.5 px-3 text-right text-emerald-700">Margen</th>}
                  <th className="py-2.5 px-3 text-right">PVP Ud.</th>
                  <th className="py-2.5 px-3 text-right">Total</th>
                  <th className="py-2.5 px-2 text-center w-10"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filasFiltradas.map((m, idx) => {
                  const opcionesAlt = alturasDe(m);
                  const tieneMano = manoDe(m.cod);
                  return (
                    <tr key={m._k} className="hover:bg-slate-50/80 transition-colors group">
                      <td className="py-3 px-2 text-center font-bold text-slate-400">{idx + 1}</td>
                      
                      {/* Cantidad con +/- */}
                      <td className="py-3 px-3">
                        <div className="flex items-center justify-center gap-1 bg-slate-100 p-0.5 rounded-xl w-fit mx-auto">
                          <button
                            type="button"
                            onClick={() => setQty(m._k, -1, true)}
                            className="w-6 h-6 rounded-lg bg-white hover:bg-slate-200 text-slate-700 font-bold flex items-center justify-center shadow-2xs"
                          >
                            -
                          </button>
                          <input
                            type="number"
                            min="1"
                            value={m.qty}
                            onChange={e => setQty(m._k, e.target.value)}
                            className="w-8 text-center bg-transparent font-black text-slate-900 outline-none"
                          />
                          <button
                            type="button"
                            onClick={() => setQty(m._k, 1, true)}
                            className="w-6 h-6 rounded-lg bg-white hover:bg-slate-200 text-slate-700 font-bold flex items-center justify-center shadow-2xs"
                          >
                            +
                          </button>
                        </div>
                      </td>

                      {/* Código */}
                      <td className="py-3 px-3">
                        <div className="flex items-center gap-1.5">
                          <span className="font-mono font-black text-indigo-700 text-sm">{m.cod}</span>
                          {!m.encontrado && (
                            <span className="px-1.5 py-0.5 rounded bg-rose-100 text-rose-700 font-bold text-[9px]">Manual</span>
                          )}
                        </div>
                      </td>

                      {/* Familia / Descripción + Línea de Observaciones / Características especiales */}
                      <td className="py-3 px-3 min-w-[220px]">
                        <div className="font-bold text-slate-800 text-xs">
                          {m.familia?.replace(/_/g, ' ') || m.tipo || 'Mueble'}
                        </div>
                        {/* Línea de Observaciones / Características Especiales del Mueble */}
                        <div className="mt-1 flex items-center gap-1">
                          <input
                            type="text"
                            value={m.obs || ''}
                            onChange={e => setObs(m._k, e.target.value)}
                            placeholder="✎ Observaciones / características especiales…"
                            title="Escribe aquí características especiales, cajeados de pilar, accesorios interiores o notas para taller"
                            className={`w-full px-2 py-1 rounded-lg border text-[11px] outline-none transition-all ${
                              m.obs?.trim()
                                ? 'border-amber-400 bg-amber-50/70 font-bold text-amber-900 shadow-xs ring-1 ring-amber-300'
                                : 'border-slate-200 bg-slate-50/60 text-slate-500 hover:bg-white focus:bg-white focus:border-indigo-400'
                            }`}
                          />
                        </div>
                      </td>

                      {/* Ancho */}
                      <td className="py-3 px-3 text-center font-bold text-slate-700">
                        {m.ancho ? `${m.ancho} cm` : '—'}
                      </td>

                      {/* Alto */}
                      <td className="py-3 px-3 text-center">
                        {opcionesAlt ? (
                          <select
                            value={m.alto || opcionesAlt[0]}
                            onChange={e => setAlto(m._k, e.target.value)}
                            className="px-2 py-1 rounded-lg border border-slate-200 bg-white font-bold text-slate-800 text-xs outline-none focus:border-indigo-400"
                          >
                            {opcionesAlt.map(a => <option key={a} value={a}>{a} cm</option>)}
                          </select>
                        ) : (
                          <span className="font-bold text-slate-700">{m.alto ? `${m.alto} cm` : '—'}</span>
                        )}
                      </td>

                      {/* Mano de apertura con botón interactivo */}
                      <td className="py-3 px-3 text-center">
                        {tieneMano !== undefined ? (
                          <button
                            type="button"
                            onClick={() => rotarMano(m._k)}
                            className={`px-2.5 py-1 rounded-lg font-black text-[11px] transition-all flex items-center gap-1 mx-auto ${
                              tieneMano === 'D' ? 'bg-emerald-100 text-emerald-800 border border-emerald-300' :
                              tieneMano === 'I' ? 'bg-sky-100 text-sky-800 border border-sky-300' :
                              'bg-amber-100 text-amber-900 border border-amber-300 animate-pulse'
                            }`}
                          >
                            {tieneMano === 'D' ? '▶ Dcha' : tieneMano === 'I' ? '◀ Izq' : '⚠️ Sin Mano'}
                          </button>
                        ) : (
                          <span className="text-slate-300 font-bold">—</span>
                        )}
                      </td>

                      {/* Coste y Margen (candado) */}
                      {verCoste && (
                        <td className="py-3 px-3 text-right font-mono text-purple-700 font-bold" title={`Neto ACB: ${eur(m.despiece?.casco)} | PVP Desmontada (factor ${m.despiece?.factorDesmontada}): ${eur(m.despiece?.cascoPvp)}`}>
                          {eur(m.despiece?.casco)}
                        </td>
                      )}
                      {verCoste && (
                        <td className="py-3 px-3 text-right font-mono text-purple-700 font-bold" title={`Puertas: ${(m.despiece?.puertasDetalle || []).map(f => `${f.desc} [${f.puntos} pts]`).join(' + ') || '0 frentes'} = ${m.despiece?.puntosPuertas || 0} pts (${eur(m.despiece?.puertaPvp)}) | Coste neto (${m.despiece?.dtoPuertas || 50}% dto): ${eur(m.despiece?.puerta)}`}>
                          {eur(m.despiece?.puerta)}
                        </td>
                      )}
                      {verCoste && (
                        <td className="py-3 px-3 text-right font-mono text-purple-900 font-black">
                          {eur(m.coste)}
                        </td>
                      )}
                      {verCoste && (
                        <td className="py-3 px-3 text-right font-mono font-bold text-emerald-600">
                          {eur(m.margen)} <span className="text-[10px] text-emerald-500">({m.margenPct.toFixed(1)}%)</span>
                        </td>
                      )}

                      {/* PVP */}
                      <td className="py-3 px-3 text-right font-mono font-bold text-slate-700">{eur(m.pvp)}</td>
                      <td className="py-3 px-3 text-right font-mono font-black text-slate-900 text-sm">
                        {eur((Number(m.pvp) || 0) * (Number(m.qty) || 1))}
                      </td>

                      {/* Eliminar */}
                      <td className="py-3 px-2 text-center">
                        <button
                          type="button"
                          onClick={() => quitar(m._k)}
                          className="p-1.5 rounded-lg text-slate-300 hover:text-rose-600 hover:bg-rose-50 transition-colors"
                          title="Eliminar fila"
                        >
                          <Trash2 size={16} />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>

        {/* Resumen Final de Importes */}
        <div className="p-6 bg-slate-50 border-t border-slate-200 flex items-center justify-between gap-6 flex-wrap">
          <div className="flex items-center gap-4">
            <button
              type="button"
              {...handlersCandado}
              className={`p-2.5 rounded-2xl border transition-all ${verCoste ? 'bg-purple-100 text-purple-800 border-purple-300' : 'bg-white text-slate-400 border-slate-200 hover:text-slate-700'}`}
              title="Shift + Clic para ver desglose de coste y margen"
            >
              {verCoste ? <Unlock size={18} /> : <Lock size={18} />}
            </button>
            {pistaCandado && <span className="text-xs text-amber-600 font-bold animate-fade-in">{pistaCandado}</span>}
            
            {verCoste && (
              <div className="flex items-center gap-4 text-xs">
                <div>Coste Fábrica: <b className="font-mono text-slate-800">{eur(totalCoste)}</b></div>
                <div>Margen Bruto: <b className="font-mono text-emerald-700">{eur(totalMargen)} ({totalMargenPct.toFixed(1)}%)</b></div>
              </div>
            )}
          </div>

          <div className="flex items-center gap-6">
            <div className="text-right space-y-0.5 text-xs text-slate-600">
              <div>Subtotal: <span className="font-mono font-bold text-slate-800">{eur(subtotalBruto)}</span></div>
              {descuento > 0 && <div className="text-rose-600 font-bold">Dto. ({descuento}%): -{eur(importeDescuento)}</div>}
              <div>Base Imponible: <span className="font-mono font-bold text-slate-800">{eur(baseImponible)}</span></div>
              <div>IVA ({ivaRate}%): <span className="font-mono font-bold text-slate-800">{eur(cuotaIva)}</span></div>
            </div>

            <div className="text-right pl-4 border-l border-slate-200">
              <span className="text-[10px] uppercase font-black text-slate-400 block">Total Final Presupuesto</span>
              <span className="text-2xl font-black text-indigo-950 tracking-tight">{eur(totalPvp)}</span>
            </div>
          </div>
        </div>

      </div>

      {/* Modal de Pegado Masivo */}
      {showPegadoMasivo && (
        <div className="fixed inset-0 z-50 bg-slate-950/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl p-6 max-w-xl w-full space-y-4 shadow-2xl border border-slate-200 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FileUp size={22} className="text-indigo-600" />
                <h3 className="text-lg font-black text-slate-900">Pegado Masivo de Relación</h3>
              </div>
              <button onClick={() => setShowPegadoMasivo(false)} className="p-1.5 rounded-xl hover:bg-slate-100 text-slate-400">
                <X size={20} />
              </button>
            </div>
            <p className="text-xs text-slate-500">
              Pega directamente la lista completa de muebles desde WhatsApp, correo electrónico o Word:
            </p>
            <textarea
              value={textoMasivo}
              onChange={e => setTextoMasivo(e.target.value)}
              placeholder={"1 b60i (altura 80)\n2 b45d\n1 asc60d\n1 columna horno 60\n2 gavetero 80\n1 col60"}
              rows={8}
              className="w-full p-4 rounded-2xl border border-slate-200 text-xs font-mono focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 outline-none resize-none bg-slate-50/50"
            />
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowPegadoMasivo(false)}
                className="px-4 py-2 rounded-xl border border-slate-200 text-xs font-bold text-slate-600 hover:bg-slate-50"
              >
                Cancelar
              </button>
              <button
                onClick={procesarPegadoMasivo}
                disabled={!textoMasivo.trim() || buscando}
                className="px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-md disabled:opacity-50 flex items-center gap-2"
              >
                {buscando ? <Loader size={15} className="animate-spin" /> : <Plus size={15} />} Volcar Muebles a la Lista
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal de Descuentos Comerciales de Puertas en Cascada */}
      {showModalDtos && (
        <div className="fixed inset-0 z-50 bg-slate-950/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl p-6 max-w-md w-full space-y-4 shadow-2xl border border-slate-200 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="p-2 bg-amber-500/10 text-amber-600 rounded-xl border border-amber-500/20">
                  <Percent size={20} />
                </div>
                <div>
                  <h3 className="text-base font-black text-slate-900">Descuentos de Compra en Puertas</h3>
                  <p className="text-[11px] text-slate-500">Ajusta el descuento comercial sobre la tarifa oficial MV</p>
                </div>
              </div>
              <button onClick={() => setShowModalDtos(false)} className="p-1.5 rounded-xl hover:bg-slate-100 text-slate-400">
                <X size={20} />
              </button>
            </div>

            <div className="space-y-3 bg-slate-50 p-4 rounded-2xl border border-slate-200 text-xs">
              <div>
                <label className="block text-slate-700 font-bold mb-1">
                  Descuento Principal 1 (%):
                </label>
                <input
                  type="number"
                  step="any"
                  min="0"
                  max="100"
                  value={dtoPuertas1}
                  onChange={e => setDtoPuertas1(parseFloat(e.target.value) || 0)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 font-mono font-bold text-slate-800 bg-white focus:border-indigo-500 outline-none"
                  placeholder="50"
                />
              </div>

              <div>
                <label className="block text-slate-700 font-bold mb-1">
                  Descuento en Cascada 2 (%) <span className="text-slate-400 font-normal">(Opcional)</span>:
                </label>
                <input
                  type="number"
                  step="any"
                  min="0"
                  max="100"
                  value={dtoPuertas2}
                  onChange={e => setDtoPuertas2(parseFloat(e.target.value) || 0)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-300 font-mono font-bold text-slate-800 bg-white focus:border-indigo-500 outline-none"
                  placeholder="0"
                />
              </div>

              <div className="pt-2 border-t border-slate-200 flex items-center justify-between font-bold text-slate-800">
                <span>Multiplicador Neto Total:</span>
                <span className="font-mono text-indigo-700 font-black">
                  {Math.round((1 - (1 - dtoPuertas1/100) * (1 - dtoPuertas2/100)) * 1000) / 10}% de descuento neto
                </span>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setShowModalDtos(false)}
                className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-md flex items-center gap-2"
              >
                <Check size={14} /> Aplicar a Todas las Puertas
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
