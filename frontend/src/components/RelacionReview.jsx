/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * RelacionReview — Panel de revisión y edición en pantalla de la relación de muebles MV.
 * 
 * Capacidades avanzadas:
 *   - Pegado masivo multilínea (WhatsApp, correos, notas de obra, hojas de corte)
 *   - Paleta interactiva de adición rápida (Bajos, Altos, Columnas, Gaveteros, Lineales)
 *   - Filtrado por categorías y cálculo automático de metros lineales
 *   - Comparador dinámico de tarifas (T1 Sincro a T5 FENIX) en tiempo real
 *   - Selector visual de mano de apertura (Izq / Dcha / 2P) con resolución masiva
 *   - Desglose técnico de despiece (cascos, puertas, herrajes, patas, bisagras)
 *   - Impresión oficial, exportación a PDF y copia formateada para WhatsApp
 */
import React, { useState, useEffect, useMemo, useRef } from 'react';
import { 
  X, Plus, Trash2, Search, Check, Loader, AlertTriangle, FileUp, 
  Lock, Unlock, Download, Printer, Copy, CheckCircle2, RefreshCw, 
  Layers, Package, Sparkles, ChevronRight, Boxes, Eye, ArrowUpDown,
  Filter, HelpCircle, FileText
} from 'lucide-react';
import { usePulsacionLarga, AYUDA_CANDADO } from '../utils/pulsacionLarga';
import { despiece, MV_COSTES_DEFAULT } from './RentabilidadMV';

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

// Accesorios habituales y muebles rápidos
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

const MUESTRARIO_CASCOS = [
  { id: 'grafito-19', nombre: 'Grafito Antracita (19mm)' },
  { id: 'blanco-hidro-19', nombre: 'Blanco Hidrófugo (19mm)' },
  { id: 'roble-aurora-19', nombre: 'Roble Aurora (19mm)' },
  { id: 'blanco-16', nombre: 'Blanco En Kit (16mm)' },
  { id: 'aluminio-16', nombre: 'Aluminio Textura (16mm)' },
  { id: 'spike-19', nombre: 'Spike (19mm)' },
  { id: 'stone-19', nombre: 'Stone (19mm)' },
  { id: 'roble-natural-16', nombre: 'Roble Natural (Diseño Grueso 16mm)' },
  { id: 'olmo-18', nombre: 'Olmo (Diseño Grueso 18mm)' },
];

export default function RelacionReview({ muebles: inicial, noLeidas, onConfirm, onExportDesmontada, onExportMontada, onClose, apiUrl, authHeaders }) {
  const [muebles, setMuebles] = useState(() => (inicial || []).map((m, i) => ({ ...m, _k: `${m.cod || 'x'}-${i}-${Date.now()}-${m.raw || ''}` })));
  const [busca, setBusca] = useState('');
  const [buscando, setBuscando] = useState(false);
  const [aviso, setAviso] = useState('');
  const [verCoste, setVerCoste] = useState(false);
  const [pistaCandado, setPistaCandado] = useState('');
  
  // Modales y paneles auxiliares
  const [showPegadoMasivo, setShowPegadoMasivo] = useState(() => !inicial || inicial.length === 0);
  const [textoMasivo, setTextoMasivo] = useState('');
  const [showComparador, setShowComparador] = useState(false);
  const [showDespiece, setShowDespiece] = useState(false);
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
  const [acabadoCasco, setAcabadoCasco] = useState(() => {
    try { return localStorage.getItem('mv_casco') || MUESTRARIO_CASCOS[0].nombre; } catch { return MUESTRARIO_CASCOS[0].nombre; }
  });
  const [tarifas, setTarifas] = useState([]);
  const [todasTarifasData, setTodasTarifasData] = useState({});

  useEffect(() => {
    try { localStorage.setItem('mv_casco', acabadoCasco); } catch { /* noop */ }
  }, [acabadoCasco]);

  const acabadosDeTarifa = useMemo(
    () => (tarifas.find(t => t.tarifa === tarifa)?.acabados) || [],
    [tarifas, tarifa]
  );

  useEffect(() => {
    fetch(`${apiUrl}/api/cascos/mv/tarifas`, { headers: authHeaders() })
      .then(r => r.json())
      .then(d => { if (d.success) setTarifas(d.tarifas || []); })
      .catch(() => {});
  }, [apiUrl, authHeaders]);

  useEffect(() => {
    try { localStorage.setItem('mv_tarifa', tarifa); } catch { /* noop */ }
    fetch(`${apiUrl}/api/cascos/mv/tarifa?tariff=${encodeURIComponent(tarifa)}`, { headers: authHeaders() })
      .then(r => r.json())
      .then(d => {
        if (d.success) {
          setFamilias(d.familias);
          const newPv = d.pointValue || 3.33;
          setPv(newPv);
          setTodasTarifasData(prev => ({ ...prev, [tarifa]: { familias: d.familias, pv: newPv } }));
          // Al cambiar de tarifa se revaloran los muebles YA metidos: dejarlos
          // con el precio de la tarifa anterior daría un presupuesto MEZCLADO,
          // unas líneas a un precio y otras a otro, sin ningún aviso.
          // Se valora con la MISMA función que todo lo demás: aquí había una
          // copia de la fórmula y las dos ya se habían separado.
          setMuebles(prev => prev.map(m => ({
            ...m, pvp: puntosLocal(m, m.alto, d.familias, newPv),
          })));
        }
      })
      .catch(() => {});
  }, [apiUrl, authHeaders, tarifa]);

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

  // El precio SIEMPRE sale de la tarifa. `fams`/`punto` permiten valorar con una
  // tarifa recién descargada, antes de que el estado se haya actualizado.
  const puntosLocal = (m, alto, fams = familias, punto = pv) => {
    const info = fams?.[m.familia];
    // En la tarifa el código lleva la mano SIN decidir («AE60D/I»). Una vez
    // decidida («AE60D») ya no existe en la tarifa: buscando solo por `m.cod` no
    // se encontraba nada, se devolvía el precio anterior y la línea se quedaba
    // congelada a la tarifa vieja. No daba error: daba un presupuesto mezclado.
    const baseCod = String(m.cod || '').replace(/(D\/I|D|I)$/i, '');
    const e = info?.items?.[m.cod] ?? info?.items?.[`${baseCod}D/I`] ?? info?.items?.[baseCod];
    if (e == null) return m.pvp;
    if (Array.isArray(e)) {
      const t = info.type;
      let i = 0;
      if (t === 'h7090') i = alto >= 85 ? 1 : 0;
      else if (t === 'h127147') i = alto > 137 ? 1 : 0;
      else if (t === 'h200220') i = alto > 210 ? 1 : 0;
      return Math.round((e[i] || e[0]) * punto * 100) / 100;
    }
    return typeof e === 'number' ? Math.round(e * punto * 100) / 100 : m.pvp;
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

  const setNota = (k, nota) => setMuebles(prev => prev.map(m => m._k === k ? { ...m, nota } : m));

  const sinMano = muebles.filter(m => manoDe(m.cod) === null).length;

  useEffect(() => {
    if (!familias) return;
    setMuebles(prev => {
      let cambia = false;
      const sig = prev.map(m => {
        if (m.alto) return m;
        const opciones = OPCIONES_ALTURA[familias?.[m.familia]?.type];
        if (!opciones) return m;
        cambia = true;
        return { ...m, alto: opciones[0], _altoDeLaCasa: true, pvp: puntosLocal(m, opciones[0]) };
      });
      return cambia ? sig : prev;
    });
  }, [familias, muebles.length]); // eslint-disable-line

  const filas = muebles.map(m => {
    const desp = m.encontrado ? costeDetalladoDe(m, p, tarifa, pv, acabadoCasco) : { costeTotal: 0, casco: 0, cascoPvp: 0, puerta: 0, puertaPvp: 0 };
    // Mismo `|| 0` que en CocinaMontada3, mismo fallo: un casco sin precio en
    // tarifa se convertía en «cero euros» y de ahí salía un margen inflado.
    const coste = desp.costeTotal != null ? desp.costeTotal : null;
    const pvp = Number(m.pvp) || 0;
    const margen = coste == null ? null : pvp - coste;
    const margenPct = (coste == null || pvp <= 0) ? null : (margen / pvp) * 100;
    return { ...m, despiece: desp, coste, margen, margenPct };
  });

  const totalUds = muebles.reduce((s, m) => s + (Number(m.qty) || 1), 0);
  const totalPvp = filas.reduce((s, m) => s + m.pvp * (Number(m.qty) || 1), 0);
  const totalCoste = filas.reduce((s, m) => s + (m.coste || 0) * (Number(m.qty) || 1), 0);
  const totalMargen = totalPvp - totalCoste;
  const totalMargenPct = totalPvp > 0 ? (totalMargen / totalPvp) * 100 : 0;

  // Métricas avanzadas
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

  // Filtrado de filas
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
      const r = await fetch(`${apiUrl}/api/cascos/mv/detectar-relacion`, {
        method: 'POST', headers: { ...authHeaders(), 'Content-Type': 'application/json' },
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
      // «AV30D/I» acaba en «I»: con `endsWith` un mueble recién añadido del
      // catálogo nacía con la mano puesta a izquierda sin que nadie la eligiera.
      // Vacío = sin decidir, que es lo que de verdad se sabe al añadirlo.
      mano: manoDe(c.cod) || '',
      qty: 1,
      pvp: pvp,
      encontrado: true,
      raw: c.cod,
    };
    setMuebles(prev => fundir(prev, [nuevo]));
    setBusca('');
    setFoco(false);
  };

  // Comparador de presupuesto en todas las tarifas (T1 a T5)
  const comparativaTarifas = useMemo(() => {
    const pvTarifas = { T1: 3.33, T2: 3.33, T3: 3.33, T4: 3.33, T5: 3.33 };
    const multTarifas = { T1: 1.0, T2: 1.15, T3: 1.28, T4: 1.42, T5: 1.60 };
    
    return ['T1', 'T2', 'T3', 'T4', 'T5'].map(t => {
      const totalEstimado = totalPvp * (multTarifas[t] / multTarifas[tarifa || 'T1']);
      return {
        tarifa: t,
        nombre: TARIFAS_NOMBRES[t] || t,
        total: totalEstimado,
        diferencia: totalEstimado - totalPvp,
        activa: t === tarifa
      };
    });
  }, [totalPvp, tarifa]);

  // Copia formateada para WhatsApp
  const copiarParaWhatsApp = () => {
    const lineas = [
      `*PRESUPUESTO COCINA MONTADA MV*`,
      `*Tarifa Puertas:* ${tarifa} (${TARIFAS_NOMBRES[tarifa] || 'Estándar'})`,
      `*Casco ACB:* ${acabadoCasco}`,
      `*Total Unidades:* ${totalUds} muebles`,
      `----------------------------------------`,
      ...muebles.map(m => {
        // `endsWith('I')` es CIERTO para «AV30D/I»: una puerta sin decidir se
        // copiaba como [Izq]. La mano sale de `manoDe`, que sí las distingue.
        const mano = manoDe(m.cod);
        const manoTxt = mano === 'D' ? ' [Dcha]' : mano === 'I' ? ' [Izq]'
          : mano === null ? ' [MANO SIN DECIDIR]' : '';
        const nota = (m.nota || '').trim();
        return `• ${m.qty}x *${m.cod}* (${m.ancho || '—'}x${m.alto || '—'} cm)${manoTxt} -> ${eur((Number(m.pvp) || 0) * (Number(m.qty) || 1))}`
          + (nota ? `\n    _${nota}_` : '');
      }),
      `----------------------------------------`,
      `*TOTAL PRESUPUESTO:* ${eur(totalPvp)} + IVA`,
    ];
    navigator.clipboard.writeText(lineas.join('\n'));
    setCopiadoWs(true);
    setTimeout(() => setCopiadoWs(false), 2500);
  };

  // Impresión profesional
  const imprimirPresupuesto = () => {
    const w = window.open('', '_blank');
    if (!w) return;
    // Lo que escriba el usuario va a un documento: se escapa. Un «<» suelto en
    // una observación se comería el resto del presupuesto impreso.
    const esc = (t) => String(t ?? '').replace(/[&<>"]/g, c => (
      { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
    const filasHtml = muebles.map((m, idx) => {
      // OJO: `cod.endsWith('I')` es CIERTO para «AV30D/I», o sea que una puerta
      // SIN mano decidida se imprimía como «Izq». El taller la fabricaba a la
      // izquierda sin que nadie lo hubiera decidido. La mano sale de `manoDe`,
      // que distingue las tres situaciones: sin mano, sin decidir, y decidida.
      const mano = manoDe(m.cod);
      const manoTxt = mano === 'D' ? 'Dcha' : mano === 'I' ? 'Izq'
        : mano === null ? 'Sin decidir' : '—';
      const nota = (m.nota || '').trim();
      return `
      <tr style="border-bottom: ${nota ? 'none' : '1px solid #e3e8ee'}; font-size: 13px;">
        <td style="padding: 8px 12px; font-weight: bold; text-align: center; color: #4a5564;">${idx + 1}</td>
        <td style="padding: 8px 12px; font-weight: bold; text-align: center; color: #474d9b;">${m.qty}</td>
        <td style="padding: 8px 12px; font-weight: bold; color: #111726;">${esc(m.cod) || '—'}</td>
        <td style="padding: 8px 12px; color: #4a5564;">${esc(m.familia?.replace(/_/g, ' ') || m.tipo || 'Mueble')}</td>
        <td style="padding: 8px 12px; text-align: center; color: #364150;">${m.ancho ? m.ancho + ' cm' : '—'}</td>
        <td style="padding: 8px 12px; text-align: center; color: #364150;">${m.alto ? m.alto + ' cm' : '—'}</td>
        <td style="padding: 8px 12px; text-align: center; font-weight: bold; ${mano === null ? 'color:#95674e;' : ''}">${manoTxt}</td>
        <td style="padding: 8px 12px; text-align: right; color: #364150;">${eur(m.pvp)}</td>
        <td style="padding: 8px 12px; text-align: right; font-weight: bold; color: #111726;">${eur((Number(m.pvp) || 0) * (Number(m.qty) || 1))}</td>
      </tr>
      ${nota ? `<tr style="border-bottom: 1px solid #e3e8ee; font-size: 12px;">
        <td></td>
        <td colspan="8" style="padding: 0 12px 8px 12px; color: #4a5564; font-style: italic;">${esc(nota)}</td>
      </tr>` : ''}`;
    }).join('');

    w.document.write(`<!DOCTYPE html>
      <html>
        <head>
          <meta charset="utf-8"/>
          <title>Relación de Muebles - Cocina Montada MV</title>
          <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; padding: 25px; color: #212937; }
            .header { border-bottom: 2px solid #474d9b; padding-bottom: 12px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: flex-end; }
            .title { font-size: 22px; font-weight: 900; color: #1f203b; margin: 0; }
            .badge { display: inline-block; padding: 4px 10px; background: #e3e7f5; color: #3b3f7d; border-radius: 6px; font-weight: bold; font-size: 12px; }
            .badge-casco { display: inline-block; padding: 4px 10px; background: #f2f5f8; color: #364150; border-radius: 6px; font-weight: bold; font-size: 12px; margin-left: 6px; }
            table { width: 100%; border-collapse: collapse; margin-top: 10px; }
            th { background: #f8fafb; padding: 10px 12px; font-size: 11px; text-transform: uppercase; color: #687485; border-bottom: 2px solid #cdd5de; text-align: left; }
            .total-box { margin-top: 25px; margin-left: auto; width: 280px; background: #f8fafb; border: 1px solid #e3e8ee; border-radius: 12px; padding: 15px; }
            .total-row { display: flex; justify-content: space-between; padding: 4px 0; font-size: 13px; }
            .total-row.final { border-top: 2px solid #cdd5de; margin-top: 6px; padding-top: 8px; font-size: 16px; font-weight: bold; color: #474d9b; }
          </style>
        </head>
        <body>
          <div class="header">
            <div>
              <h1 class="title">RELACIÓN DE MUEBLES · COCINA MONTADA</h1>
              <p style="margin: 4px 0 0 0; color: #687485; font-size: 13px;">Sistema Oficial de Tarifas MV · Luiggi Home</p>
            </div>
            <div style="text-align: right;">
              <span class="badge">Tarifa ${tarifa} (${TARIFAS_NOMBRES[tarifa] || 'Estándar'})</span>
              <span class="badge-casco">Casco: ${acabadoCasco}</span>
              <div style="font-size: 11px; color: #97a3b2; margin-top: 4px;">${new Date().toLocaleDateString('es-ES')}</div>
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
            <div class="total-row"><span>Total Elementos:</span> <b>${totalUds} uds</b></div>
            <div class="total-row"><span>Casco ACB:</span> <b>${acabadoCasco}</b></div>
            <div class="total-row final"><span>Total (sin IVA):</span> <b>${eur(totalPvp)}</b></div>
          </div>
        </body>
      </html>
    `);
    w.document.close();
    w.print();
  };

  // El candado del coste. `usePulsacionLarga` recibe SOLO la acción: el segundo
  // argumento son OPCIONES ({ms}), no una segunda función. Pasarle ahí la pista
  // hacía que no se llamara nunca y el aviso no salía jamás.
  const largoCandado = usePulsacionLarga(() => {
    setVerCoste(v => !v);
    setPistaCandado('');
  });

  // Volcar es el último punto donde se puede mirar: después ya no se mira.
  const confirmar = () => {
    // Un código que acaba en «D/I» es una puerta SIN mano decidida. Si sale así
    // hacia el taller la decide el taller: acierta la mitad de las veces, y la
    // otra mitad es un frente desmontado y vuelto a taladrar en casa del
    // cliente. Se decide delante del plano, que es donde se sabe.
    if (sinMano > 0) {
      const seguir = window.confirm(
        `Hay ${sinMano} ${sinMano === 1 ? 'puerta' : 'puertas'} sin decidir la mano (el código acaba en «D/I»).\n\n` +
        'Si se vuelca así, la mano la elegirá quien fabrique.\n\n' +
        '¿Volcar de todas formas?');
      if (!seguir) return;
    }
    // La observación de cada línea viaja con ella: si se queda aquí, se escribe
    // y se pierde al volcar, que es peor que no poder escribirla.
    const lineas = muebles.map(m => ({ ...m, nota: m.nota || '' }));
    const contexto = { tarifa, acabadoCasco, valorPunto: pv };
    if (onExportDesmontada) onExportDesmontada(lineas, contexto);
    else if (onConfirm) onConfirm(lineas, contexto);
  };

  const clicCandado = (e) => {
    // Al soltar el dedo el navegador manda TAMBIÉN un clic: sin `consumir()` la
    // pulsación larga abre el candado y ese clic lo cierra en el mismo gesto.
    if (largoCandado.consumir()) return;
    if (e.shiftKey) { setVerCoste(v => !v); setPistaCandado(''); return; }
    setPistaCandado(AYUDA_CANDADO);
    setTimeout(() => setPistaCandado(''), 4000);
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/80 backdrop-blur-md flex items-center justify-center p-2 sm:p-4 animate-fade-in">
      <div className="bg-white w-[98vw] max-w-[1600px] h-[95vh] rounded-3xl shadow-2xl border border-slate-200 flex flex-col overflow-hidden">
        
        {/* Cabecera Principal */}
        <div className="px-6 py-4 bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white flex items-center justify-between gap-4 shrink-0 shadow-md">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-2xl bg-indigo-600/30 border border-indigo-400/30 text-indigo-300">
              <Boxes size={22} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-black text-white tracking-tight">Relación de Muebles · Cocina Montada</h2>
                <span className="px-2 py-0.5 rounded-full bg-indigo-500/20 border border-indigo-400/30 text-indigo-200 text-[10px] font-black uppercase">
                  Tarifa {tarifa}
                </span>
              </div>
              <p className="text-xs text-indigo-200/70 font-medium">
                {muebles.length} líneas · {totalUds} módulos · Total: <span className="font-bold text-white">{eur(totalPvp)}</span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowPegadoMasivo(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-indigo-600/60 hover:bg-indigo-600 border border-indigo-400/30 text-xs font-bold transition-all"
              title="Pegar lista completa de muebles desde WhatsApp o texto"
            >
              <FileUp size={14} /> Pegado Masivo
            </button>
            <button
              onClick={() => setShowComparador(v => !v)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-bold transition-all ${showComparador ? 'bg-amber-500 text-slate-950 border-amber-400 shadow-md' : 'bg-white/10 hover:bg-white/20 border-white/10 text-white'}`}
              title="Comparar presupuesto en T1, T2, T3, T4 y T5"
            >
              <Sparkles size={14} className={showComparador ? 'text-slate-950' : 'text-amber-400'} /> Comparar Tarifas
            </button>
            <button
              onClick={imprimirPresupuesto}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white/10 hover:bg-white/20 border border-white/10 text-xs font-bold transition-all"
              title="Imprimir relación oficial de muebles"
            >
              <Printer size={14} /> Imprimir
            </button>
            <button
              onClick={onClose}
              className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
              title="Cerrar modal"
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Barra de Métricas y Selector de Tarifa / Casco */}
        <div className="px-6 py-2.5 bg-slate-50 border-b border-slate-200 flex items-center justify-between gap-4 flex-wrap text-xs">
          {/* Selector de Tarifa y Casco ACB */}
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex items-center gap-2">
              <span className="font-bold text-slate-500 uppercase text-[10px] tracking-wider">Tarifa:</span>
              <div className="flex gap-1 bg-white p-1 rounded-xl border border-slate-200 shadow-sm">
                {['T1', 'T2', 'T3', 'T4', 'T5'].map(t => (
                  <button
                    key={t}
                    onClick={() => setTarifa(t)}
                    className={`px-2.5 py-1 rounded-lg font-black text-xs transition-all ${tarifa === t ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-600 hover:bg-slate-100'}`}
                  >
                    {t}
                  </button>
                ))}
              </div>
              <span className="text-[11px] text-slate-500 font-semibold italic hidden lg:inline">
                ({TARIFAS_NOMBRES[tarifa] || 'Acabado estándar'})
              </span>
            </div>

            {/* Selector de Casco ACB */}
            <div className="flex items-center gap-2 border-l border-slate-200 pl-3">
              <span className="font-bold text-slate-500 uppercase text-[10px] tracking-wider">Casco ACB:</span>
              <select
                value={acabadoCasco}
                onChange={(e) => setAcabadoCasco(e.target.value)}
                className="px-3 py-1 rounded-xl border border-slate-200 bg-white text-xs font-bold text-slate-800 shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                {MUESTRARIO_CASCOS.map(c => (
                  <option key={c.id} value={c.nombre}>{c.nombre}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Métricas de Composición */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-emerald-50 text-emerald-800 border border-emerald-200 font-bold text-[11px]">
              <Package size={13} /> Bajos: {metricas.bajosUds} ({metricas.metrosBajos} m)
            </div>
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-sky-50 text-sky-800 border border-sky-200 font-bold text-[11px]">
              <Package size={13} /> Altos: {metricas.altosUds} ({metricas.metrosAltos} m)
            </div>
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-indigo-50 text-indigo-800 border border-indigo-200 font-bold text-[11px]">
              <Package size={13} /> Columnas: {metricas.colUds}
            </div>
            {sinMano > 0 && (
              <button
                onClick={() => fijarTodasManos('D')}
                className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-amber-100 text-amber-900 border border-amber-300 font-black text-[11px] hover:bg-amber-200 transition-colors animate-pulse"
                title="Poner mano Dcha a todos los que tienen mano pendiente"
              >
                <AlertTriangle size={13} className="text-amber-600" /> {sinMano} sin mano · Fijar Dcha
              </button>
            )}
          </div>
        </div>

        {/* Comparador de Tarifas Desplegable */}
        {showComparador && (
          <div className="px-6 py-3 bg-gradient-to-r from-amber-500/10 via-indigo-500/10 to-amber-500/10 border-b border-amber-200/60 flex items-center justify-between gap-4 overflow-x-auto">
            <div className="flex items-center gap-2 shrink-0">
              <Sparkles size={16} className="text-amber-600" />
              <span className="font-black text-xs text-slate-800 uppercase tracking-wide">Presupuesto en otras Tarifas:</span>
            </div>
            <div className="flex items-center gap-3">
              {comparativaTarifas.map(ct => (
                <button
                  key={ct.tarifa}
                  onClick={() => setTarifa(ct.tarifa)}
                  className={`px-3 py-1.5 rounded-xl border text-left transition-all ${ct.activa ? 'bg-indigo-600 text-white border-indigo-600 shadow-md ring-2 ring-indigo-300' : 'bg-white text-slate-700 border-slate-200 hover:border-indigo-300'}`}
                >
                  <div className="text-[10px] font-black uppercase opacity-80">{ct.tarifa}</div>
                  <div className="text-xs font-black">{eur(ct.total)}</div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Buscador y Paleta de Adición Rápida */}
        <div className="p-4 bg-white border-b border-slate-100 space-y-3">
          {/* Buscador en vivo */}
          <div className="relative">
            <div className="flex items-center gap-2">
              <div className="relative flex-1">
                <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
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
                  placeholder="Escribe un código o texto (ej.: 1 b60i, asc60d, fregadero 60, col60, 2 gavetero 80)…"
                  className="w-full pl-10 pr-4 py-2.5 rounded-2xl border border-slate-200 text-sm font-medium focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 outline-none transition-all shadow-inner"
                />
                {buscando && <Loader size={16} className="absolute right-3.5 top-1/2 -translate-y-1/2 text-indigo-600 animate-spin" />}
              </div>
              <button
                onClick={() => añadirTexto(busca)}
                disabled={!busca.trim() || buscando}
                className="px-5 py-2.5 rounded-2xl bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-bold text-sm shadow-md transition-all flex items-center gap-1.5"
              >
                <Plus size={16} /> Añadir
              </button>
            </div>

            {/* Desplegable de Sugerencias */}
            {foco && sugerencias.length > 0 && (
              <div className="absolute left-0 right-0 top-full mt-1.5 bg-white border border-slate-200 rounded-2xl shadow-2xl z-30 max-h-72 overflow-y-auto divide-y divide-slate-100">
                {sugerencias.map((c, i) => (
                  <button
                    key={c.cod}
                    type="button"
                    onClick={() => añadirSugerencia(c)}
                    className={`w-full px-4 py-2 text-left flex items-center justify-between gap-3 text-xs transition-colors ${i === sel ? 'bg-indigo-50 text-indigo-900 font-bold' : 'hover:bg-slate-50'}`}
                  >
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-black text-indigo-600 text-sm">{c.cod}</span>
                      <span className="text-slate-600">{c.etiqueta}</span>
                      {c.ancho && <span className="px-1.5 py-0.5 rounded bg-slate-100 text-[10px] text-slate-500 font-bold">{c.ancho} cm</span>}
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
                <span className="text-[9px] font-black text-slate-400 uppercase px-1">{grp.grupo}:</span>
                {grp.items.map(it => (
                  <button
                    key={it.label}
                    onClick={() => añadirTexto(it.expr)}
                    className="px-2 py-0.5 rounded-lg bg-white border border-slate-200 hover:border-indigo-400 hover:text-indigo-600 font-bold text-[11px] text-slate-700 shadow-2xs transition-all"
                    title={it.desc}
                  >
                    + {it.label}
                  </button>
                ))}
              </div>
            ))}
          </div>
        </div>

        {/* Pestañas de Filtro y Tabla */}
        <div className="px-6 pt-3 bg-white border-b border-slate-100 flex items-center justify-between gap-4 flex-wrap">
          {/* La fila de pestañas mide 428 px: en un móvil de 390 la última se
              queda fuera. Con `min-w-0` puede encogerse (un hijo de flex trae
              `min-width: auto` y se niega) y con `overflow-x-auto` se desliza. */}
          <div className="flex gap-1 border-b border-slate-200 -mb-[1px] min-w-0 max-w-full overflow-x-auto [&>*]:shrink-0">
            {['TODOS', 'BAJOS', 'ALTOS', 'COLUMNAS', 'LINEALES'].map(cat => (
              <button
                key={cat}
                onClick={() => setFiltroCat(cat)}
                className={`px-3 py-1.5 border-b-2 font-black text-xs transition-all ${filtroCat === cat ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-slate-400 hover:text-slate-700'}`}
              >
                {cat} {cat === 'TODOS' ? `(${muebles.length})` : ''}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-2 pb-1.5">
            <button
              onClick={copiarParaWhatsApp}
              className={`flex items-center gap-1 px-3 py-1 rounded-lg text-xs font-bold transition-all border ${copiadoWs ? 'bg-emerald-600 text-white border-emerald-600' : 'bg-emerald-50 text-emerald-800 border-emerald-200 hover:bg-emerald-100'}`}
              title="Copiar resumen del presupuesto listo para WhatsApp"
            >
              {copiadoWs ? <Check size={14} /> : <Copy size={14} />} {copiadoWs ? '¡Copiado!' : 'WhatsApp'}
            </button>
          </div>
        </div>

        {/* Tabla de Muebles */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 divide-y divide-slate-100">
          {filasFiltradas.length === 0 ? (
            <div className="py-16 text-center text-slate-400 space-y-2">
              <Package size={40} className="mx-auto text-slate-300 opacity-60" />
              <p className="text-sm font-bold text-slate-600">No hay muebles en esta categoría</p>
              <p className="text-xs">Usa el buscador superior o la paleta de atajos rápidos para añadir muebles.</p>
            </div>
          ) : (
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-200 text-[10px] font-black uppercase text-slate-400">
                  <th className="py-2 px-2 text-center w-10">#</th>
                  <th className="py-2 px-3 text-center w-28">Cantidad</th>
                  <th className="py-2 px-3">Código</th>
                  <th className="py-2 px-3">Descripción / Familia</th>
                  <th className="py-2 px-3 text-center">Ancho</th>
                  <th className="py-2 px-3 text-center">Alto</th>
                  <th className="py-2 px-3 text-center">Mano</th>
                  <th className="py-2 px-3 text-left">Observación</th>
                  {verCoste && <th className="py-2 px-3 text-right text-purple-700" title="Coste Neto de Casco ACB">Casco Neto (ACB)</th>}
                  {verCoste && <th className="py-2 px-3 text-right text-purple-700" title={`Coste de Puertas según Tarifa ${tarifa}`}>Puertas ({tarifa})</th>}
                  {verCoste && <th className="py-2 px-3 text-right text-purple-700">Coste Total</th>}
                  {verCoste && <th className="py-2 px-3 text-right text-emerald-700">Margen</th>}
                  <th className="py-2 px-3 text-right">PVP Ud.</th>
                  <th className="py-2 px-3 text-right">Total</th>
                  <th className="py-2 px-2 text-center w-10"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filasFiltradas.map((m, idx) => {
                  const opcionesAlt = alturasDe(m);
                  const tieneMano = manoDe(m.cod);
                  return (
                    <tr key={m._k} className="hover:bg-slate-50/80 transition-colors group">
                      <td className="py-2.5 px-2 text-center font-bold text-slate-400">{idx + 1}</td>
                      
                      {/* Cantidad con +/- */}
                      <td className="py-2.5 px-3">
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
                      <td className="py-2.5 px-3">
                        <div className="flex items-center gap-1.5">
                          <span className="font-mono font-black text-indigo-700 text-sm">{m.cod}</span>
                          {!m.encontrado && (
                            <span className="px-1.5 py-0.5 rounded bg-rose-100 text-rose-700 font-bold text-[9px]">Manual</span>
                          )}
                        </div>
                      </td>

                      {/* Familia / Descripción */}
                      <td className="py-2.5 px-3 text-slate-600 font-medium">
                        {m.familia?.replace(/_/g, ' ') || m.tipo || 'Mueble'}
                      </td>

                      {/* Ancho */}
                      <td className="py-2.5 px-3 text-center font-bold text-slate-700">
                        {m.ancho ? `${m.ancho} cm` : '—'}
                      </td>

                      {/* Alto */}
                      <td className="py-2.5 px-3 text-center">
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
                      <td className="py-2.5 px-3 text-center">
                        {tieneMano !== undefined ? (
                          <button
                            type="button"
                            onClick={() => rotarMano(m._k)}
                            className={`px-2 py-1 rounded-lg font-black text-[11px] transition-all flex items-center gap-1 mx-auto ${
                              tieneMano === 'D' ? 'bg-emerald-100 text-emerald-800 border border-emerald-300' :
                              tieneMano === 'I' ? 'bg-sky-100 text-sky-800 border border-sky-300' :
                              'bg-amber-100 text-amber-900 border border-amber-300 animate-pulse'
                            }`}
                            title="Haz clic para alternar mano Dcha / Izq"
                          >
                            {tieneMano === 'D' ? '▶ Dcha' : tieneMano === 'I' ? '◀ Izq' : '⚠️ Sin Mano'}
                          </button>
                        ) : (
                          <span className="text-slate-300 font-bold">—</span>
                        )}
                      </td>

                      {/* Observación de la línea: sale impresa en el presupuesto */}
                      <td className="py-2.5 px-3">
                        <input
                          type="text"
                          value={m.nota || ''}
                          onChange={e => setNota(m._k, e.target.value)}
                          placeholder="Observación…"
                          title="Se imprime en el presupuesto, debajo de la línea"
                          className="w-full min-w-[9rem] px-2 py-1 rounded-lg border border-slate-200 bg-white text-xs text-slate-700 outline-none focus:border-indigo-400 placeholder:text-slate-300"
                        />
                      </td>

                      {/* Coste y Margen (candado) */}
                      {verCoste && (
                        <td className="py-2.5 px-3 text-right font-mono text-purple-700 font-bold" title={`Neto ACB: ${eur(m.despiece?.casco)} | PVP Desmontada (factor ${m.despiece?.factorDesmontada}): ${eur(m.despiece?.cascoPvp)}`}>
                          {eur(m.despiece?.casco)}
                        </td>
                      )}
                      {verCoste && (
                        <td className="py-2.5 px-3 text-right font-mono text-purple-700 font-bold" title={`Puertas: ${(m.despiece?.puertasDetalle || []).map(f => `${f.desc} [${f.puntos} pts]`).join(' + ') || '0 frentes'} = ${m.despiece?.puntosPuertas || 0} pts (${eur(m.despiece?.puertaPvp)}) | Coste neto (${m.despiece?.dtoPuertas || 50}% dto): ${eur(m.despiece?.puerta)}`}>
                          {eur(m.despiece?.puerta)}
                        </td>
                      )}
                      {verCoste && (
                        <td className="py-2.5 px-3 text-right font-mono text-purple-900 font-black">
                          {eur(m.coste)}
                        </td>
                      )}
                      {verCoste && (
                        <td className="py-2.5 px-3 text-right font-mono font-bold text-emerald-600">
                          {eur(m.margen)}{m.margenPct != null && <span className="text-[10px] text-emerald-500"> ({m.margenPct.toFixed(1)}%)</span>}
                        </td>
                      )}

                      {/* PVP */}
                      <td className="py-2.5 px-3 text-right font-mono font-bold text-slate-700">{eur(m.pvp)}</td>
                      <td className="py-2.5 px-3 text-right font-mono font-black text-slate-900 text-sm">
                        {eur((Number(m.pvp) || 0) * (Number(m.qty) || 1))}
                      </td>

                      {/* Eliminar */}
                      <td className="py-2.5 px-2 text-center">
                        <button
                          type="button"
                          onClick={() => quitar(m._k)}
                          className="p-1.5 rounded-lg text-slate-300 hover:text-rose-600 hover:bg-rose-50 transition-colors"
                          title="Eliminar fila"
                        >
                          <Trash2 size={15} />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>

        {/* Modal de Pegado Masivo */}
        {showPegadoMasivo && (
          <div className="fixed inset-0 z-60 bg-slate-950/70 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-white rounded-3xl p-6 max-w-xl w-full space-y-4 shadow-2xl border border-slate-200 animate-in fade-in zoom-in-95">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FileUp size={20} className="text-indigo-600" />
                  <h3 className="text-base font-black text-slate-900">Pegado Masivo de Relación</h3>
                </div>
                <button onClick={() => setShowPegadoMasivo(false)} className="p-1.5 rounded-xl hover:bg-slate-100 text-slate-400">
                  <X size={18} />
                </button>
              </div>
              <p className="text-xs text-slate-500">
                Pega directamente la lista de muebles desde WhatsApp, correo o Word (una línea por mueble, con cantidad y mano opcional):
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
                  className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-md disabled:opacity-50 flex items-center gap-1.5"
                >
                  {buscando ? <Loader size={14} className="animate-spin" /> : <Plus size={14} />} Volcar a la Lista
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Pie de Página con Totales y Confirmación */}
        <div className="px-6 py-4 bg-slate-50 border-t border-slate-200 flex items-center justify-between gap-4 flex-wrap shrink-0">
          <div className="flex items-center gap-4">
            <button
              type="button"
              {...largoCandado.props}
              onClick={clicCandado}
              className={`p-2 rounded-xl border transition-all ${verCoste ? 'bg-purple-100 text-purple-800 border-purple-300' : 'bg-white text-slate-400 border-slate-200 hover:text-slate-700'}`}
              title={AYUDA_CANDADO}
              aria-label="Ver coste y margen"
            >
              {verCoste ? <Unlock size={16} /> : <Lock size={16} />}
            </button>
            {pistaCandado && <span className="text-xs text-amber-600 font-bold animate-fade-in">{pistaCandado}</span>}
            
            {verCoste && (
              <div className="flex items-center gap-3 text-xs">
                <div>Coste Fábrica: <b className="font-mono text-slate-800">{eur(totalCoste)}</b></div>
                <div>Margen Bruto: <b className="font-mono text-emerald-700">{eur(totalMargen)} ({totalMargenPct.toFixed(1)}%)</b></div>
              </div>
            )}
          </div>

          <div className="flex items-center gap-3">
            <div className="text-right">
              <span className="text-[10px] uppercase font-black text-slate-400 block">Total Presupuesto ({tarifa})</span>
              <span className="text-xl font-black text-slate-900 tracking-tight">{eur(totalPvp)} <span className="text-xs font-bold text-slate-400">+ IVA</span></span>
            </div>

            {onExportMontada && (
              <button
                onClick={() => onExportMontada(muebles, { tarifa, acabadoCasco, valorPunto: pv })}
                className="px-4 py-3 rounded-2xl bg-indigo-600 hover:bg-indigo-700 text-white font-black text-sm shadow-xl shadow-indigo-600/20 transition-all flex items-center gap-2"
              >
                <CheckCircle2 size={18} /> Presupuestador
              </button>
            )}
            <button
              onClick={confirmar}
              className="px-6 py-3 rounded-2xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white font-black text-sm shadow-xl shadow-emerald-600/20 transition-all flex items-center gap-2"
            >
              <CheckCircle2 size={18} /> {onExportDesmontada ? 'Cocina Desmontada' : 'Volcar al Presupuesto'}
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}
