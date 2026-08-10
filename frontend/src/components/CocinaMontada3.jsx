/*
 * © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * CocinaMontada3.jsx — Presupuestador de Cocina Montada 3 por Relación y Códigos.
 * 
 * Flujo ultrarrápido de presupuestación por teclado / relación de códigos MV:
 *   - Añadir por texto libre ('1 b60i', 'asc60d', 'col60', '2 b45d (altura 80)')
 *   - Catálogo integrado con sugerencias y búsqueda instantánea
 *   - Selector de tarifas en tiempo real (T1 a T5) con recálculo dinámico
 *   - Gestión de manos (Dcha/Izq), alturas estándar y notas por mueble
 *   - Desglose de costes y márgenes protegido por candado 🔒
 *   - Guardado en base de datos y exportación a PDF profesional
 */
import React, { useState, useEffect, useMemo, useRef } from 'react';
import { 
  FileText, Plus, Trash2, Search, Check, Loader, AlertTriangle, 
  Download, Save, FolderOpen, Lock, Unlock, Sparkles, RefreshCw,
  Copy, Layers, ArrowUpDown, ChevronRight, HelpCircle, Package,
  ClipboardList, CheckCircle2, ChevronDown, Boxes
} from 'lucide-react';
import { getToken } from '../services/api';
import { usePulsacionLarga, AYUDA_CANDADO } from '../utils/pulsacionLarga';
import { despiece, MV_COSTES_DEFAULT } from './RentabilidadMV';
import { irA } from '../services/navegacion';

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

export default function CocinaMontada3({ currentUser, state, setState, logo }) {
  const [cliente, setCliente] = useState('');
  const [ref, setRef] = useState('');
  const [descuento, setDescuento] = useState(0);
  const [ivaRate, setIvaRate] = useState(21);
  const [notas, setNotas] = useState('');
  
  const [muebles, setMuebles] = useState([]);
  const [busca, setBusca] = useState('');
  const [buscando, setBuscando] = useState(false);
  const [aviso, setAviso] = useState('');
  const [guardando, setGuardando] = useState(false);
  const [savedId, setSavedId] = useState(null);
  const [savedKind, setSavedKind] = useState(null);
  
  const [verCoste, setVerCoste] = useState(false);
  const [pistaCandado, setPistaCandado] = useState('');

  // Costes de componentes para cálculo de margen
  const p = useMemo(() => {
    try { 
      const s = JSON.parse(localStorage.getItem('mv_costes') || 'null'); 
      return s ? { ...MV_COSTES_DEFAULT, ...s } : MV_COSTES_DEFAULT; 
    } catch { 
      return MV_COSTES_DEFAULT; 
    }
  }, []);

  // Catálogo MV y tarifas
  const [familias, setFamilias] = useState(null);
  const [pv, setPv] = useState(3.33);
  const [selFam, setSelFam] = useState('');
  const [selCod, setSelCod] = useState('');
  const [selQty, setSelQty] = useState(1);

  const [tarifa, setTarifa] = useState(() => {
    try { return localStorage.getItem('mv_tarifa') || 'T1'; } catch { return 'T1'; }
  });
  const [tarifas, setTarifas] = useState([]);

  const acabadosDeTarifa = useMemo(
    () => (tarifas.find(t => t.tarifa === tarifa)?.acabados) || [],
    [tarifas, tarifa]
  );

  const authHeaders = () => {
    const token = getToken();
    return {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    };
  };

  // Cargar catálogo de tarifas
  useEffect(() => {
    fetch(`${API_URL}/api/cascos/mv/tarifas`, { headers: authHeaders() })
      .then(r => r.json())
      .then(d => { if (d.success) setTarifas(d.tarifas || []); })
      .catch(() => {});
  }, []);

  // Cambiar tarifa y recalcular precios en tiempo real
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

  const codigosFam = useMemo(() => {
    if (!familias || !selFam) return [];
    const it = familias[selFam]?.items;
    return it && typeof it === 'object' ? Object.keys(it) : [];
  }, [familias, selFam]);

  // Catálogo indexado para buscador instantáneo
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
    return hits.slice(0, 30);
  }, [busca, catalogo]);

  useEffect(() => { setSel(0); }, [busca]);

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

  const setQty = (k, v) => setMuebles(prev => prev.map(m => m._k === k ? { ...m, qty: Math.max(1, Number(v) || 1) } : m));
  const setAlto = (k, v) => setMuebles(prev => prev.map(m => {
    if (m._k !== k) return m;
    const alto = Number(v) || null;
    return { ...m, alto, pvp: puntosLocal(m, alto) };
  }));
  const quitar = (k) => setMuebles(prev => prev.filter(m => m._k !== k));
  const duplicar = (k) => {
    const orig = muebles.find(m => m._k === k);
    if (!orig) return;
    const copia = { ...orig, _k: `dup-${Date.now()}-${Math.random().toString(36).slice(2, 7)}` };
    setMuebles(prev => [...prev, copia]);
  };

  const _MANO_SUFIJO = /(D\/I|D|I)$/;
  const manoDe = (cod) => {
    const m = _MANO_SUFIJO.exec(String(cod || '').toUpperCase());
    if (!m) return undefined;
    return m[1] === 'D/I' ? null : m[1];
  };

  const setMano = (k, mano) => setMuebles(prev => prev.map(m => {
    if (m._k !== k) return m;
    const cod = String(m.cod || '');
    return { ...m, cod: cod.replace(/(D\/I|D|I)$/i, mano) };
  }));

  const setNota = (k, nota) => setMuebles(prev => prev.map(m => m._k === k ? { ...m, nota } : m));

  const fundir = (prev, nuevos) => {
    const out = [...prev];
    for (const n of nuevos) {
      const i = out.findIndex(m => m.cod && n.cod && m.cod === n.cod && (m.alto ?? null) === (n.alto ?? null));
      if (i >= 0) out[i] = { ...out[i], qty: (Number(out[i].qty) || 1) + (Number(n.qty) || 1) };
      else out.push(n);
    }
    return out;
  };

  // Añadir por texto
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
      if (!r.ok || !d.success) { 
        setAviso(d.detail || 'No se reconoció el mueble. Escríbelo como "1 b60i (altura 80)" o "asc60d".'); 
        return; 
      }
      const nuevos = (d.muebles || []).map((m, i) => ({ ...m, _k: `add-${Date.now()}-${i}` }));
      setMuebles(prev => fundir(prev, nuevos));
      setBusca('');
      setFoco(false);
    } catch (e) {
      setAviso(`Error al buscar (${e?.message || 'red'}).`);
    } finally { 
      setBuscando(false); 
    }
  };

  const añadirDelSelector = () => {
    if (!selCod) return;
    añadirTexto(`${Math.max(1, Number(selQty) || 1)} ${selCod}`);
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

  const teclaBuscador = (e) => {
    if (!sugerencias.length) { if (e.key === 'Enter') añadirTexto(busca); return; }
    if (e.key === 'ArrowDown') { e.preventDefault(); setSel(s => (s + 1) % sugerencias.length); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setSel(s => (s - 1 + sugerencias.length) % sugerencias.length); }
    else if (e.key === 'Enter') { e.preventDefault(); añadirSugerencia(sugerencias[sel]); }
    else if (e.key === 'Escape') { e.preventDefault(); setBusca(''); }
  };

  // Cálculos de totales y márgenes
  const filas = muebles.map(m => {
    const coste = m.encontrado ? costeDe(m, p) : 0;
    const pvp = Number(m.pvp) || 0;
    const margen = pvp - coste;
    const margenPct = pvp > 0 ? (margen / pvp) * 100 : 0;
    return { ...m, coste, margen, margenPct };
  });

  const totalUds = muebles.reduce((s, m) => s + (Number(m.qty) || 1), 0);
  const totalBruto = filas.reduce((s, m) => s + m.pvp * (Number(m.qty) || 1), 0);
  const totalDto = Math.round(totalBruto * (Number(descuento) || 0) / 100 * 100) / 100;
  const baseImponible = totalBruto - totalDto;
  const totalIva = Math.round(baseImponible * (Number(ivaRate) || 0) / 100 * 100) / 100;
  const totalPvp = baseImponible + totalIva;
  
  const totalCoste = filas.reduce((s, m) => s + m.coste * (Number(m.qty) || 1), 0);
  const totalMargen = baseImponible - totalCoste;
  const totalMargenPct = baseImponible > 0 ? (totalMargen / baseImponible) * 100 : 0;

  const sinMano = muebles.filter(m => manoDe(m.cod) === null).length;

  // Candado de coste / margen
  const candadoLargo = usePulsacionLarga(() => { setPistaCandado(''); setVerCoste(v => !v); });
  const candadoClick = (e) => {
    if (candadoLargo.consumir()) return;
    if (e.shiftKey || verCoste) { setPistaCandado(''); setVerCoste(v => !v); return; }
    setPistaCandado(AYUDA_CANDADO + ' para ver coste y margen.');
  };

  // Guardar en el servidor
  const guardarPresupuesto = async (kind = 'presupuesto') => {
    if (!muebles.length) {
      alert('Añade al menos un mueble antes de guardar.');
      return;
    }
    setGuardando(true);
    try {
      const payload = {
        id: savedId || undefined,
        kind,
        cliente: cliente.trim() || 'Cliente Sin Nombre',
        ref: ref.trim() || 'Ref. Cocina Montada 3',
        tarifa,
        descuento: Number(descuento) || 0,
        ivaRate: Number(ivaRate) || 21,
        total: totalPvp,
        subtotal: baseImponible,
        bruto: totalBruto,
        notes: notas,
        lines: muebles.map(m => ({
          cod: m.cod,
          familia: m.familia,
          tipo: m.tipo,
          ancho: m.ancho,
          alto: m.alto,
          fondo: m.fondo,
          qty: m.qty,
          pvp: m.pvp,
          total: (m.pvp || 0) * (m.qty || 1),
          nota: m.nota || ''
        }))
      };

      const res = await fetch(`${API_URL}/api/cascos/orders`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        const data = await res.json();
        setSavedId(data.order?.id || data.id);
        setSavedKind(kind);
        alert(`✅ ${kind === 'pedido' ? 'Pedido' : 'Presupuesto'} de Cocina Montada 3 guardado con éxito.`);
      } else {
        alert('Error al guardar en el servidor.');
      }
    } catch (e) {
      alert('Error de conexión.');
    } finally {
      setGuardando(false);
    }
  };

  // Generar PDF Oficial
  const exportarPDF = async () => {
    if (!muebles.length) {
      alert('Añade muebles al presupuesto para generar el PDF.');
      return;
    }
    try {
      const { jsPDF } = await import('jspdf');
      const autoTable = (await import('jspdf-autotable')).default;
      const pdf = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
      const W = pdf.internal.pageSize.getWidth(); 
      const M = 14;

      if (logo && typeof logo === 'string' && logo.startsWith('data:')) {
        try { 
          const fmt = logo.includes('png') ? 'PNG' : logo.includes('webp') ? 'WEBP' : 'JPEG'; 
          pdf.addImage(logo, fmt, M, 12, 32, 16); 
        } catch {}
      } else { 
        pdf.setFontSize(15); 
        pdf.setFont(undefined, 'bold'); 
        pdf.text('LUIGGI HOME', M, 20); 
      }

      pdf.setFontSize(16); 
      pdf.setTextColor(30, 27, 65); 
      pdf.setFont(undefined, 'bold');
      pdf.text('PRESUPUESTO COCINA MONTADA', W - M, 18, { align: 'right' }); 
      
      pdf.setFontSize(10); 
      pdf.setTextColor(100); 
      pdf.setFont(undefined, 'normal');
      pdf.text(`Tarifa: ${tarifa} (${acabadosDeTarifa.slice(0, 2).join(', ')})`, W - M, 24, { align: 'right' });
      pdf.text(`${cliente || 'Cliente'}  ·  ${ref || 'Ref. Obra'}`, W - M, 29, { align: 'right' });
      pdf.text(new Date().toLocaleDateString('es-ES'), W - M, 34, { align: 'right' });

      autoTable(pdf, {
        startY: 42,
        head: [['Código', 'Tipo', 'Medidas (Al×An×F)', 'Mano', 'Ud.', 'PVP Unit.', 'Importe']],
        body: filas.map(f => [
          f.cod || '—',
          f.familia ? f.familia.replace(/_/g, ' ') : (f.tipo || 'Mueble'),
          `${f.alto || 80} × ${f.ancho || 60} × ${f.fondo || 58} cm`,
          f.mano || (manoDe(f.cod) === null ? 'S/D' : '—'),
          String(f.qty || 1),
          eur(f.pvp),
          eur((f.pvp || 0) * (f.qty || 1))
        ]),
        styles: { fontSize: 8.5, cellPadding: 2 },
        headStyles: { fillColor: [49, 46, 129], textColor: [255, 255, 255] },
        alternateRowStyles: { fillColor: [248, 250, 252] },
        columnStyles: { 
          0: { fontStyle: 'bold', textColor: [49, 46, 129] }, 
          3: { halign: 'center' },
          4: { halign: 'center' }, 
          5: { halign: 'right' }, 
          6: { halign: 'right', fontStyle: 'bold' } 
        },
        margin: { left: M, right: M },
      });

      let y = (pdf.lastAutoTable?.finalY || 42) + 8;
      const bx = W - M - 70;
      pdf.setFontSize(10); 
      pdf.setTextColor(40);
      pdf.text('Bruto líneas', bx, y); 
      pdf.text(eur(totalBruto), W - M, y, { align: 'right' }); 
      y += 6;

      if (Number(descuento) > 0) { 
        pdf.text(`Descuento ${descuento}%`, bx, y); 
        pdf.text('-' + eur(totalDto), W - M, y, { align: 'right' }); 
        y += 6; 
      }

      pdf.text('Base imponible', bx, y); 
      pdf.text(eur(baseImponible), W - M, y, { align: 'right' }); 
      y += 6;

      pdf.text(`IVA ${ivaRate}%`, bx, y); 
      pdf.text(eur(totalIva), W - M, y, { align: 'right' }); 
      y += 5;

      pdf.setFillColor(79, 70, 229); 
      pdf.roundedRect(bx - 4, y, 74 + 4, 11, 2, 2, 'F');
      pdf.setFontSize(12); 
      pdf.setTextColor(255); 
      pdf.setFont(undefined, 'bold');
      pdf.text('TOTAL PRESUPUESTO', bx, y + 7.5); 
      pdf.text(eur(totalPvp), W - M, y + 7.5, { align: 'right' });

      pdf.save(`Presupuesto_CocinaMontada3_${(cliente || 'Cliente').replace(/\s+/g, '_')}.pdf`);
    } catch (e) {
      alert('Error generando PDF.');
    }
  };

  return (
    <div className="h-full flex flex-col bg-slate-100 overflow-y-auto">
      {/* Barra de cabecera */}
      <div className="bg-gradient-to-r from-indigo-700 via-violet-700 to-indigo-900 text-white p-4 shadow-lg shrink-0">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center md:justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-white/10 rounded-xl">
              <Layers size={20} className="text-indigo-200" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-black tracking-tight">Cocina Montada 3</h1>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  Relación Directa MV
                </span>
              </div>
              <p className="text-xs text-indigo-200">
                Presupuestación rápida por códigos, relación de muebles y control de tarifas en tiempo real.
              </p>
            </div>
          </div>

          {/* Selector de Tarifa Activa y Acciones */}
          <div className="flex items-center gap-3 flex-wrap justify-end">
            <div className="flex items-center gap-1.5 bg-white/15 px-3 py-1.5 rounded-xl border border-white/20">
              <span className="text-[10px] font-black uppercase tracking-widest text-indigo-100">Tarifa</span>
              <select 
                value={tarifa} 
                onChange={e => setTarifa(e.target.value)}
                className="px-2 py-1 rounded-lg text-xs font-black bg-white text-indigo-900 shadow-sm outline-none"
              >
                {(tarifas.length ? tarifas : [{ tarifa: 'T1', acabados: [] }]).map(t => (
                  <option key={t.tarifa} value={t.tarifa}>{t.tarifa}</option>
                ))}
              </select>
              {acabadosDeTarifa.length > 0 && (
                <span className="text-[11px] text-white/90 max-w-[200px] truncate hidden sm:inline" title={acabadosDeTarifa.join(' · ')}>
                  {acabadosDeTarifa.join(' · ')}
                </span>
              )}
            </div>

            <button
              onClick={exportarPDF}
              disabled={!muebles.length}
              className="flex items-center gap-1 px-3 py-2 bg-white/15 hover:bg-white/25 text-white rounded-xl text-xs font-bold transition-all disabled:opacity-50"
            >
              <Download size={14} /> PDF
            </button>

            <button
              onClick={() => guardarPresupuesto('presupuesto')}
              disabled={guardando || !muebles.length}
              className="flex items-center gap-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-black shadow-md transition-all disabled:opacity-50"
            >
              {guardando ? <Loader size={14} className="animate-spin" /> : <Save size={14} />} Guardar
            </button>
          </div>
        </div>
      </div>

      {/* Contenido Principal */}
      <div className="max-w-7xl mx-auto w-full p-4 sm:p-6 space-y-4">
        {/* Datos de Cabecera (Cliente, Ref, Descuento) */}
        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm grid grid-cols-1 sm:grid-cols-12 gap-3 items-center">
          <div className="sm:col-span-4">
            <label className="text-[10px] font-black text-slate-400 uppercase block mb-1">Cliente / Titular</label>
            <input 
              type="text" 
              placeholder="Nombre del cliente o estudio..."
              value={cliente}
              onChange={e => setCliente(e.target.value)}
              className="w-full px-3 py-2 text-xs font-bold bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none"
            />
          </div>
          <div className="sm:col-span-3">
            <label className="text-[10px] font-black text-slate-400 uppercase block mb-1">Referencia / Obra</label>
            <input 
              type="text" 
              placeholder="Ref. Vivienda o proyecto..."
              value={ref}
              onChange={e => setRef(e.target.value)}
              className="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none"
            />
          </div>
          <div className="sm:col-span-2">
            <label className="text-[10px] font-black text-slate-400 uppercase block mb-1">Descuento (%)</label>
            <input 
              type="number" 
              min="0"
              max="100"
              value={descuento}
              onChange={e => setDescuento(e.target.value)}
              className="w-full px-3 py-2 text-xs text-center font-bold bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none"
            />
          </div>
          <div className="sm:col-span-3">
            <label className="text-[10px] font-black text-slate-400 uppercase block mb-1">Margen & Coste</label>
            <button
              {...candadoLargo.props}
              onClick={candadoClick}
              className={`w-full flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl text-xs font-black transition-colors ${
                verCoste 
                  ? 'bg-emerald-500 text-white shadow-sm' 
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
              title={pistaCandado || 'Mantén pulsado o Shift+clic para desbloquear'}
            >
              {verCoste ? <Unlock size={14} /> : <Lock size={14} />}
              <span>{verCoste ? 'Márgenes Visibles' : 'Márgenes Protegidos'}</span>
            </button>
          </div>
        </div>

        {/* Panel de Añadir Muebles (Buscador Libre + Desplegable MV) */}
        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm space-y-3">
          <div>
            <label className="text-[11px] font-black text-slate-500 uppercase">Añadir Mueble Escribiendo o Buscando</label>
            <div className="flex gap-2 mt-1">
              <div className="relative flex-1">
                <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input 
                  value={busca} 
                  onChange={e => setBusca(e.target.value)}
                  onKeyDown={teclaBuscador}
                  onFocus={() => setFoco(true)}
                  onBlur={() => setTimeout(() => setFoco(false), 200)}
                  placeholder='Código o palabra: "asc60d", "b60i", "fregadero", "col60", "2 b45d (altura 80)"'
                  className="w-full pl-9 pr-3 py-2.5 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-indigo-400 outline-none" 
                />
                {/* Sugerencias instantáneas */}
                {foco && sugerencias.length > 0 && (
                  <ul className="absolute z-50 left-0 right-0 top-full mt-1 max-h-64 overflow-y-auto bg-white border border-slate-200 rounded-xl shadow-2xl">
                    {sugerencias.map((c, i) => (
                      <li key={c.familia + c.cod}>
                        <button 
                          type="button"
                          onMouseEnter={() => setSel(i)}
                          onMouseDown={(e) => { e.preventDefault(); e.stopPropagation(); añadirSugerencia(c); }}
                          className={`w-full text-left px-3.5 py-2 flex items-baseline gap-2 cursor-pointer transition-colors ${i === sel ? 'bg-indigo-50 text-indigo-950 font-bold' : 'hover:bg-slate-50'}`}
                        >
                          <span className="font-black text-indigo-900 text-xs w-28 shrink-0">{c.cod}</span>
                          <span className="text-[11px] text-slate-600 truncate flex-1">
                            {c.desc || c.etiqueta.toLowerCase()}
                          </span>
                          {c.ancho != null && (
                            <span className="text-[11px] font-semibold text-slate-400 shrink-0">{c.ancho} cm</span>
                          )}
                          {c.precio && (
                            <span className="text-[11px] font-black text-slate-700 shrink-0 w-24 text-right">
                              {c.precio.desde ? 'desde ' : ''}{c.precio.eur.toFixed(2)} €
                            </span>
                          )}
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
              <button 
                onClick={() => añadirTexto(busca)} 
                disabled={buscando || !busca.trim()}
                className="flex items-center gap-1.5 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-black text-xs disabled:opacity-50 shadow-sm"
              >
                {buscando ? <Loader size={15} className="animate-spin" /> : <Plus size={15} />} Añadir
              </button>
            </div>
          </div>

          {/* Selector de Catálogo MV */}
          <div className="pt-2 border-t border-slate-100">
            <label className="text-[10px] font-black text-slate-400 uppercase block mb-1">…o eligiendo del catálogo oficial MV</label>
            <div className="flex gap-2 flex-wrap">
              <select 
                value={selFam} 
                onChange={e => { setSelFam(e.target.value); setSelCod(''); }}
                className="flex-1 min-w-[150px] px-3 py-2 border border-slate-200 rounded-xl text-xs bg-slate-50"
              >
                <option value="">Seleccionar Familia…</option>
                {familias && Object.keys(familias).filter(f => (familias[f]?.items && Object.keys(familias[f].items).length)).map(f => (
                  <option key={f} value={f}>{f.replace(/_/g, ' ')}</option>
                ))}
              </select>
              <select 
                value={selCod} 
                onChange={e => setSelCod(e.target.value)} 
                disabled={!codigosFam.length}
                className="flex-1 min-w-[140px] px-3 py-2 border border-slate-200 rounded-xl text-xs bg-slate-50 disabled:bg-slate-100"
              >
                <option value="">Seleccionar Código…</option>
                {codigosFam.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
              <input 
                type="number" 
                min="1" 
                value={selQty} 
                onChange={e => setSelQty(e.target.value)}
                className="w-16 text-center border border-slate-200 rounded-xl px-1 py-2 text-xs font-bold bg-slate-50" 
                title="Cantidad" 
              />
              <button 
                onClick={añadirDelSelector} 
                disabled={!selCod || buscando}
                className="flex items-center gap-1 px-4 py-2 bg-slate-800 hover:bg-slate-900 text-white rounded-xl font-bold text-xs disabled:opacity-50"
              >
                <Plus size={14} /> Añadir
              </button>
            </div>
          </div>

          {aviso && (
            <p className="text-xs text-amber-700 font-bold flex items-center gap-1.5 bg-amber-50 p-2 rounded-lg border border-amber-200">
              <AlertTriangle size={14} className="shrink-0 text-amber-600" /> {aviso}
            </p>
          )}
        </div>

        {/* Tabla de Muebles */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
          <div className="p-3.5 bg-slate-50 border-b border-slate-200 flex items-center justify-between flex-wrap gap-2">
            <div className="flex items-center gap-2">
              <span className="text-xs font-black text-slate-800 uppercase tracking-wider">
                Relación de Muebles ({muebles.length} líneas · {totalUds} uds.)
              </span>
              {sinMano > 0 && (
                <span className="text-[10px] font-black px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 border border-amber-300">
                  ⚠️ {sinMano} sin mano
                </span>
              )}
            </div>
            <button 
              onClick={() => { if (window.confirm('¿Vaciar toda la lista?')) setMuebles([]); }}
              disabled={!muebles.length}
              className="text-xs font-bold text-red-500 hover:text-red-700 disabled:opacity-30"
            >
              Vaciar lista
            </button>
          </div>

          {muebles.length === 0 ? (
            <div className="py-16 text-center text-slate-400">
              <FileText size={36} className="mx-auto mb-2 opacity-40" />
              <p className="text-sm font-bold text-slate-600">No hay muebles en el presupuesto.</p>
              <p className="text-xs text-slate-400">Escribe arriba un código como «b60» o «asc60d» para empezar.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-slate-50/80 text-slate-400 uppercase text-[10px] font-black border-b border-slate-200">
                    <th className="py-2.5 px-3">Código</th>
                    <th className="py-2.5 px-3">Tipo / Familia</th>
                    <th className="py-2.5 px-3 text-center">Ancho</th>
                    <th className="py-2.5 px-3 text-center">Alto</th>
                    <th className="py-2.5 px-3 text-center">Mano</th>
                    <th className="py-2.5 px-3 text-center">Uds.</th>
                    <th className="py-2.5 px-3">Observación</th>
                    <th className="py-2.5 px-3 text-right">PVP MV</th>
                    <th className="py-2.5 px-3 text-right">Importe</th>
                    {verCoste && (
                      <>
                        <th className="py-2.5 px-3 text-right text-amber-700 bg-amber-50/50">Coste</th>
                        <th className="py-2.5 px-3 text-right text-emerald-700 bg-emerald-50/50">Margen</th>
                      </>
                    )}
                    <th className="py-2.5 px-3 text-center">Acciones</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filas.map((m) => {
                    const opcionesAlt = alturasDe(m);
                    const mano = manoDe(m.cod);
                    return (
                      <tr key={m._k} className="hover:bg-slate-50/80 transition-colors">
                        <td className="py-2.5 px-3 font-black text-indigo-900">
                          {m.cod}
                        </td>
                        <td className="py-2.5 px-3 text-slate-600 font-medium">
                          {m.familia ? m.familia.replace(/_/g, ' ') : m.tipo}
                        </td>
                        <td className="py-2.5 px-3 text-center font-bold text-slate-700">
                          {m.ancho != null ? `${m.ancho} cm` : '—'}
                        </td>
                        <td className="py-2.5 px-3 text-center">
                          {opcionesAlt ? (
                            <select 
                              value={m.alto || opcionesAlt[0]} 
                              onChange={e => setAlto(m._k, e.target.value)}
                              className="px-1.5 py-1 text-xs font-bold border border-slate-200 rounded-lg bg-white"
                            >
                              {opcionesAlt.map(a => <option key={a} value={a}>{a} cm</option>)}
                            </select>
                          ) : (
                            <span className="text-slate-500 font-medium">{m.alto ? `${m.alto} cm` : '80 cm'}</span>
                          )}
                        </td>
                        <td className="py-2.5 px-3 text-center">
                          {mano !== undefined && (
                            <div className="inline-flex rounded-lg border border-slate-200 p-0.5 bg-slate-50">
                              <button
                                onClick={() => setMano(m._k, 'D')}
                                className={`px-1.5 py-0.5 rounded text-[10px] font-black ${mano === 'D' ? 'bg-indigo-600 text-white' : 'text-slate-500'}`}
                              >
                                D
                              </button>
                              <button
                                onClick={() => setMano(m._k, 'I')}
                                className={`px-1.5 py-0.5 rounded text-[10px] font-black ${mano === 'I' ? 'bg-indigo-600 text-white' : 'text-slate-500'}`}
                              >
                                I
                              </button>
                            </div>
                          )}
                        </td>
                        <td className="py-2.5 px-3 text-center">
                          <input 
                            type="number" 
                            min="1" 
                            value={m.qty || 1} 
                            onChange={e => setQty(m._k, e.target.value)}
                            className="w-12 text-center font-black border border-slate-200 rounded-lg py-1 text-xs" 
                          />
                        </td>
                        <td className="py-2.5 px-3">
                          <input 
                            type="text" 
                            placeholder="Nota..." 
                            value={m.nota || ''} 
                            onChange={e => setNota(m._k, e.target.value)}
                            className="w-full px-2 py-1 text-xs border border-transparent hover:border-slate-200 focus:border-indigo-400 rounded-lg outline-none bg-transparent" 
                          />
                        </td>
                        <td className="py-2.5 px-3 text-right font-bold text-slate-700">
                          {eur(m.pvp)}
                        </td>
                        <td className="py-2.5 px-3 text-right font-black text-indigo-900">
                          {eur((m.pvp || 0) * (m.qty || 1))}
                        </td>
                        {verCoste && (
                          <>
                            <td className="py-2.5 px-3 text-right text-amber-700 font-bold bg-amber-50/30">
                              {eur(m.coste * (m.qty || 1))}
                            </td>
                            <td className="py-2.5 px-3 text-right font-black text-emerald-700 bg-emerald-50/30">
                              {eur(m.margen * (m.qty || 1))} <span className="text-[10px] font-normal">({m.margenPct.toFixed(0)}%)</span>
                            </td>
                          </>
                        )}
                        <td className="py-2.5 px-3 text-center">
                          <div className="flex items-center justify-center gap-1">
                            <button 
                              onClick={() => duplicar(m._k)} 
                              title="Duplicar línea"
                              className="p-1 text-slate-400 hover:text-indigo-600 rounded"
                            >
                              <Copy size={13} />
                            </button>
                            <button 
                              onClick={() => quitar(m._k)} 
                              title="Eliminar línea"
                              className="p-1 text-slate-400 hover:text-red-600 rounded"
                            >
                              <Trash2 size={13} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* Resumen de Totales */}
          {muebles.length > 0 && (
            <div className="p-4 bg-slate-50 border-t border-slate-200 flex flex-col sm:flex-row items-end sm:items-center justify-between gap-4">
              <div className="text-xs text-slate-500 space-y-1">
                <p><b>{totalUds}</b> muebles en presupuesto · Tarifa activa: <b>{tarifa}</b></p>
                {savedId && (
                  <p className="text-emerald-700 font-bold flex items-center gap-1">
                    <CheckCircle2 size={13} /> Guardado en el sistema con ID: {savedId}
                  </p>
                )}
              </div>

              <div className="flex items-center gap-4 bg-white px-5 py-3 rounded-xl border border-slate-200 shadow-sm">
                <div className="text-right">
                  <span className="text-[10px] font-black text-slate-400 uppercase block">Base Imponible</span>
                  <span className="text-sm font-bold text-slate-700">{eur(baseImponible)}</span>
                </div>
                <div className="text-right pl-4 border-l border-slate-200">
                  <span className="text-[10px] font-black text-indigo-500 uppercase block">Total ({ivaRate}% IVA)</span>
                  <span className="text-lg font-black text-indigo-900">{eur(totalPvp)}</span>
                </div>
                {verCoste && (
                  <div className="text-right pl-4 border-l border-slate-200">
                    <span className="text-[10px] font-black text-emerald-600 uppercase block">Margen Total</span>
                    <span className="text-sm font-black text-emerald-700">{eur(totalMargen)} ({totalMargenPct.toFixed(0)}%)</span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Acceso Directo a Expediente y Almacén tras guardar */}
        {savedId && (
          <div className="flex items-center gap-3 p-4 bg-amber-50 rounded-2xl border border-amber-200 text-xs">
            <span className="font-bold text-amber-900">Módulos vinculados a esta obra:</span>
            <button 
              onClick={() => irA(setState, 'expediente')}
              className="flex items-center gap-1 px-3 py-1.5 bg-amber-600 text-white rounded-lg font-bold hover:bg-amber-700"
            >
              <ClipboardList size={13} /> Ver en Expediente
            </button>
            <button 
              onClick={() => irA(setState, 'almacen')}
              className="flex items-center gap-1 px-3 py-1.5 bg-slate-800 text-white rounded-lg font-bold hover:bg-slate-900"
            >
              <Boxes size={13} /> Consultar en Almacén
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
