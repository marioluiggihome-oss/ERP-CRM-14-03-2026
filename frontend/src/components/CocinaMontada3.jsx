/*
 * © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * CocinaMontada3.jsx — Módulo de Presupuestación Rápida de Cocina Montada 3.
 * 
 * Flujo de alta velocidad por códigos MV y relación directa:
 *   - Pegado masivo de relaciones completas desde WhatsApp / Email / Word
 *   - Paleta interactiva de adición rápida (Bajos, Altos, Columnas, Gaveteros, Lineales)
 *   - Buscador predictivo en tiempo real con sinónimos en lenguaje natural
 *   - Conmutador de tarifas dinámico (T1 Sincro a T5 FENIX) con recálculo instantáneo
 *   - Selector de cliente vinculado a CRM y gestión de descuentos comerciales
 *   - Selector interactivo de mano de apertura con resolución masiva
 *   - Desglose de costes y márgenes con candado 🔒
 *   - Exportación profesional a PDF, impresión de alta resolución y WhatsApp
 *   - Guardado en base de datos ERP para seguimiento comercial
 */
import React, { useState, useEffect, useMemo, useRef } from 'react';
import { 
  FileText, Plus, Trash2, Search, Check, Loader, AlertTriangle, 
  Download, Save, FolderOpen, Lock, Unlock, Sparkles, RefreshCw,
  Copy, Layers, ArrowUpDown, ChevronRight, HelpCircle, Package,
  ClipboardList, CheckCircle2, ChevronDown, Boxes, Printer, FileUp,
  User, Percent, Receipt, Phone, Building2, Tag, Calendar, ArrowLeft
} from 'lucide-react';
import { getToken } from '../services/api';
import { usePulsacionLarga, AYUDA_CANDADO } from '../utils/pulsacionLarga';
import { despiece, MV_COSTES_DEFAULT } from './RentabilidadMV';

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

const costeDe = (m, p) => {
  const d = despiece({ cod: m.cod, altura: m.alto ? String(m.alto) : '', familia: m.familia }, p);
  return (d.casco || 0) + (d.puerta || 0) + (d.bisagras || 0) + (d.patas || 0) + (d.colg || 0)
    + (d.caj || 0) + (d.gav || 0) + (d.soportes || 0) + (d.mo || 0);
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

export default function CocinaMontada3({ currentUser, state, setState, logo }) {
  const [cliente, setCliente] = useState('');
  const [ref, setRef] = useState('');
  const [telefono, setTelefono] = useState('');
  const [descuento, setDescuento] = useState(0);
  const [ivaRate, setIvaRate] = useState(21);
  const [notas, setNotas] = useState('');
  
  const [muebles, setMuebles] = useState([]);
  const [busca, setBusca] = useState('');
  const [buscando, setBuscando] = useState(false);
  const [aviso, setAviso] = useState('');
  const [guardando, setGuardando] = useState(false);
  const [savedId, setSavedId] = useState(null);
  
  const [verCoste, setVerCoste] = useState(false);
  const [pistaCandado, setPistaCandado] = useState('');
  
  // Modales
  const [showPegadoMasivo, setShowPegadoMasivo] = useState(false);
  const [textoMasivo, setTextoMasivo] = useState('');
  const [showComparador, setShowComparador] = useState(false);
  const [filtroCat, setFiltroCat] = useState('TODOS');
  const [copiadoWs, setCopiadoWs] = useState(false);

  const p = useMemo(() => {
    try { 
      const s = JSON.parse(localStorage.getItem('mv_costes') || 'null'); 
      return s ? { ...MV_COSTES_DEFAULT, ...s } : MV_COSTES_DEFAULT; 
    } catch { 
      return MV_COSTES_DEFAULT; 
    }
  }, []);

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
          setMuebles(prev => prev.map(m => {
            const info = d.familias?.[m.familia];
            const e = info?.items?.[m.cod];
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

  const OPCIONES_ALTURA = { h7090: [90, 70], h127147: [127, 147], h200220: [200, 220] };
  const alturasDe = (m) => {
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
    const coste = m.encontrado ? costeDe(m, p) : 0;
    const pvp = Number(m.pvp) || 0;
    const margen = pvp - coste;
    const margenPct = pvp > 0 ? (margen / pvp) * 100 : 0;
    return { ...m, coste, margen, margenPct };
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

  const metricas = useMemo(() => {
    let bajosUds = 0, altosUds = 0, colUds = 0, linUds = 0;
    let bajosAnchoCm = 0, altosAnchoCm = 0;

    muebles.forEach(m => {
      const q = Number(m.qty) || 1;
      const t = String(m.tipo || '').toUpperCase();
      const w = Number(m.ancho) || 0;
      if (t === 'BAJO') { bajosUds += q; bajosAnchoCm += w * q; }
      else if (t === 'ALTO') { altosUds += q; altosAnchoCm += w * q; }
      else if (t === 'COLUMNA') { colUds += q; }
      else { linUds += q; }
    });

    return {
      bajosUds, altosUds, colUds, linUds,
      metrosBajos: (bajosAnchoCm / 100).toFixed(2),
      metrosAltos: (altosAnchoCm / 100).toFixed(2),
    };
  }, [muebles]);

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
      `*PRESUPUESTO COCINA MONTADA MV (LUIGGI HOME)*`,
      `*Cliente:* ${cliente || 'Particular'} ${ref ? `(Ref: ${ref})` : ''}`,
      `*Tarifa:* ${tarifa} - ${TARIFAS_NOMBRES[tarifa] || 'Estándar'}`,
      `*Muebles Totales:* ${totalUds} unidades`,
      `----------------------------------------`,
      ...muebles.map(m => {
        const manoTxt = m.cod?.endsWith('D') ? ' [Dcha]' : m.cod?.endsWith('I') ? ' [Izq]' : '';
        return `• ${m.qty}x *${m.cod}* (${m.ancho || '—'}x${m.alto || '—'} cm)${manoTxt} -> ${eur((Number(m.pvp) || 0) * (Number(m.qty) || 1))}`;
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

  const imprimirPresupuesto = () => {
    const w = window.open('', '_blank');
    if (!w) return;
    const filasHtml = muebles.map((m, idx) => `
      <tr style="border-bottom: 1px solid #e2e8f0; font-size: 13px;">
        <td style="padding: 8px 12px; font-weight: bold; text-align: center; color: #475569;">${idx + 1}</td>
        <td style="padding: 8px 12px; font-weight: bold; text-align: center; color: #4338ca;">${m.qty}</td>
        <td style="padding: 8px 12px; font-weight: bold; color: #0f172a;">${m.cod || '—'}</td>
        <td style="padding: 8px 12px; color: #475569;">${m.familia?.replace(/_/g, ' ') || m.tipo || 'Mueble'}</td>
        <td style="padding: 8px 12px; text-align: center; color: #334155;">${m.ancho ? m.ancho + ' cm' : '—'}</td>
        <td style="padding: 8px 12px; text-align: center; color: #334155;">${m.alto ? m.alto + ' cm' : '—'}</td>
        <td style="padding: 8px 12px; text-align: center; font-weight: bold;">${m.cod?.endsWith('D') ? 'Dcha' : m.cod?.endsWith('I') ? 'Izq' : '—'}</td>
        <td style="padding: 8px 12px; text-align: right; color: #334155;">${eur(m.pvp)}</td>
        <td style="padding: 8px 12px; text-align: right; font-weight: bold; color: #0f172a;">${eur((Number(m.pvp) || 0) * (Number(m.qty) || 1))}</td>
      </tr>
    `).join('');

    w.document.write(`<!DOCTYPE html>
      <html>
        <head>
          <meta charset="utf-8"/>
          <title>Presupuesto Oficial - Cocina Montada 3</title>
          <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; padding: 30px; color: #1e293b; }
            .header { border-bottom: 3px solid #4338ca; padding-bottom: 15px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: flex-start; }
            .title { font-size: 24px; font-weight: 900; color: #1e1b4b; margin: 0; }
            .badge { display: inline-block; padding: 4px 12px; background: #e0e7ff; color: #3730a3; border-radius: 8px; font-weight: bold; font-size: 13px; }
            .client-box { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 12px 18px; margin-bottom: 20px; display: flex; justify-content: space-between; font-size: 13px; }
            table { width: 100%; border-collapse: collapse; margin-top: 10px; }
            th { background: #f8fafc; padding: 10px 12px; font-size: 11px; text-transform: uppercase; color: #64748b; border-bottom: 2px solid #cbd5e1; text-align: left; }
            .total-box { margin-top: 25px; margin-left: auto; width: 320px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 15px; }
            .total-row { display: flex; justify-content: space-between; padding: 4px 0; font-size: 13px; }
            .total-row.final { border-top: 2px solid #cbd5e1; margin-top: 6px; padding-top: 8px; font-size: 18px; font-weight: bold; color: #4338ca; }
            @media print { button { display: none; } }
          </style>
        </head>
        <body>
          <div class="header">
            <div>
              <h1 class="title">PRESUPUESTO COCINA MONTADA</h1>
              <p style="margin: 4px 0 0 0; color: #64748b; font-size: 13px;">Luiggi Home · Sistema Oficial de Tarifas MV</p>
            </div>
            <div style="text-align: right;">
              <span class="badge">Tarifa ${tarifa} (${TARIFAS_NOMBRES[tarifa] || 'Estándar'})</span>
              <div style="font-size: 11px; color: #94a3b8; margin-top: 5px;">${new Date().toLocaleDateString('es-ES')}</div>
            </div>
          </div>

          <div class="client-box">
            <div>
              <div><b>Cliente:</b> ${cliente || 'Cliente General'}</div>
              <div><b>Referencia:</b> ${ref || 'Proyecto Cocina'}</div>
            </div>
            <div>
              <div><b>Teléfono:</b> ${telefono || '—'}</div>
              <div><b>Comercial:</b> ${currentUser?.clientName || currentUser?.username || 'Oficina'}</div>
            </div>
          </div>

          <table>
            <thead>
              <tr>
                <th style="text-align: center;">#</th>
                <th style="text-align: center;">Cant.</th>
                <th>Código</th>
                <th>Descripción / Familia</th>
                <th style="text-align: center;">Ancho</th>
                <th style="text-align: center;">Alto</th>
                <th style="text-align: center;">Mano</th>
                <th style="text-align: right;">PVP Ud.</th>
                <th style="text-align: right;">Total</th>
              </tr>
            </thead>
            <tbody>
              ${filasHtml}
            </tbody>
          </table>

          <div class="total-box">
            <div class="total-row"><span>Subtotal:</span> <span>${eur(subtotalBruto)}</span></div>
            ${descuento > 0 ? `<div class="total-row" style="color: #dc2626;"><span>Descuento (${descuento}%):</span> <span>-${eur(importeDescuento)}</span></div>` : ''}
            <div class="total-row"><span>Base Imponible:</span> <b>${eur(baseImponible)}</b></div>
            <div class="total-row"><span>IVA (${ivaRate}%):</span> <span>${eur(cuotaIva)}</span></div>
            <div class="total-row final"><span>TOTAL:</span> <span>${eur(totalPvp)}</span></div>
          </div>

          <script>window.onload = () => window.print();</script>
        </body>
      </html>`);
    w.document.close();
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
      setSavedId(payload.id);
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
    <div className="h-full flex flex-col bg-slate-100 overflow-y-auto p-3 sm:p-6 pb-24 space-y-4">
      
      {/* Cabecera Principal */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white rounded-3xl p-5 sm:p-6 shadow-xl border border-slate-800 flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-indigo-600 border border-indigo-400/40 flex items-center justify-center shadow-lg shadow-indigo-600/30">
            <Layers size={26} className="text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2.5">
              <h1 className="text-xl sm:text-2xl font-black text-white tracking-tight">Cocina Montada 3</h1>
              <span className="px-2.5 py-0.5 rounded-full bg-indigo-500/20 border border-indigo-400/30 text-indigo-200 text-xs font-black uppercase">
                Tarifa {tarifa}
              </span>
            </div>
            <p className="text-xs sm:text-sm text-indigo-200/80 font-medium">
              Presupuestación rápida por códigos MV · Relación en pantalla y cálculo automático
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={() => setShowPegadoMasivo(true)}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-indigo-600/60 hover:bg-indigo-600 border border-indigo-400/30 text-xs font-bold transition-all shadow-sm"
            title="Pegar lista de muebles copiada de WhatsApp o texto"
          >
            <FileUp size={15} /> Pegado Masivo
          </button>
          <button
            onClick={() => setShowComparador(v => !v)}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-xl border text-xs font-bold transition-all ${showComparador ? 'bg-amber-500 text-slate-950 border-amber-400 shadow-md' : 'bg-white/10 hover:bg-white/20 border-white/10 text-white'}`}
          >
            <Sparkles size={15} className={showComparador ? 'text-slate-950' : 'text-amber-400'} /> Comparar Tarifas
          </button>
          <button
            onClick={imprimirPresupuesto}
            disabled={!muebles.length}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-white/10 hover:bg-white/20 border border-white/10 text-xs font-bold transition-all disabled:opacity-40"
          >
            <Printer size={15} /> Imprimir / PDF
          </button>
          <button
            onClick={guardarPresupuesto}
            disabled={!muebles.length || guardando}
            className="flex items-center gap-1.5 px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-black shadow-lg shadow-emerald-600/20 transition-all disabled:opacity-40"
          >
            {guardando ? <Loader size={15} className="animate-spin" /> : <Save size={15} />} Guardar
          </button>
        </div>
      </div>

      {/* Datos del Cliente y Presupuesto */}
      <div className="bg-white rounded-3xl p-5 border border-slate-200 shadow-sm grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
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
                  {verCoste && <th className="py-2.5 px-3 text-right text-purple-700">Coste Ud.</th>}
                  {verCoste && <th className="py-2.5 px-3 text-right text-purple-700">Margen</th>}
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

                      {/* Familia / Descripción */}
                      <td className="py-3 px-3 text-slate-600 font-medium">
                        {m.familia?.replace(/_/g, ' ') || m.tipo || 'Mueble'}
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
                      {verCoste && <td className="py-3 px-3 text-right font-mono font-bold text-purple-700">{eur(m.coste)}</td>}
                      {verCoste && <td className="py-3 px-3 text-right font-mono font-bold text-emerald-600">{m.margenPct.toFixed(1)}%</td>}

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

    </div>
  );
}
