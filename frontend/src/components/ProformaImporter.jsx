import { useState, useMemo, useRef, useCallback } from 'react';
import { Upload, Loader, FileText, Calculator, Trash2, ChevronDown, ChevronUp, Save, FolderOpen, X, AlertTriangle, Lock, Unlock, Download, Edit2, Check } from 'lucide-react';
import { authHeaders } from '../services/api';
import { CASCOS as _CASCOS_RAW } from '../data/cascos';

const CASCOS = Array.isArray(_CASCOS_RAW) ? _CASCOS_RAW : [];
const API_URL = process.env.REACT_APP_BACKEND_URL;
const getAuthHeaders = () => authHeaders({ 'Content-Type': 'application/json' });

// ── Helpers ──────────────────────────────────────────────────────────────────
const eur = (n) => (Number(n) || 0).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' €';

const COLOR_LBL = {
  grafito: 'Antracita', aluminio: 'Aluminio', blancoEsp: 'Blanco Esp.',
  blanco: 'Blanco', roble: 'Roble', olmo: 'Olmo',
  blancoHidrofugo: 'Blanco Hidr.', robleAurora: 'Roble Aurora',
  spike: 'Spike', stone: 'Stone',
};
const COLOR_PRIO = ['grafito', 'aluminio', 'blancoEsp', 'blanco', 'roble', 'olmo', 'stone', 'spike', 'robleAurora', 'blancoHidrofugo'];
const PUNTO = 2.0;

// Tipos de cascos disponibles para el selector inline
const TIPOS_ACB = [
  'Alto Con Balda', 'Alto Platero Con Balda', 'Alto Campana Extraíble', 'Alto Cubretermo',
  'Alto Diseño', 'Alto Escurreplatos', 'Alto Rincon Angular', 'Alto Rincón Chaflán',
  'Alto Rincón Escuadra', 'Alto Terminal (Puerta 35)', 'Alto Transversal',
  'Altillo Con Balda', 'Altillo Sin Balda',
  'Bajo Angular', 'Bajo Bombona', 'Bajo Con Balda', 'Bajo Diseño', 'Bajo Fregadero',
  'Bajo Horno', 'Bajo Placa', 'Bajo Rincón Angular', 'Bajo Rincón Escuadra',
  'Bajo Terminal (Puerta 35)',
  'Columna Con Baldas', 'Columna Con Baldas (Despensero)', 'Columna Despensa',
  'Columna Horno', 'Columna Horno-Micro', 'Columna Horno 2000/2200', 'Columna Horno-Micro 2000/2200',
  'Semicolumna Despensa', 'Semicolumna (Despensero)', 'Semicolumna (Horno-Micro)', 'Semicolumna 1300/1500 X580',
  'Sobre Columna', 'Sobre Columna Horno', 'Sobre Columna Horno-Micro',
  'Sobre Encimera', 'Sobre Encimera 1300X330',
  'Banda Mel. Con Canal', 'Banda Mel. Sin Canal', 'Tablero', 'Trasera',
];

// Herrajes especiales a alertar
const HERRAJE_ESPECIAL = [
  { re: /HERRAJE\s*270|RINCON\s*L|RINCÓN\s*L|BRI\/LTE|MAGIC\s*CORNER/i, label: 'Herraje rincón 270°' },
  { re: /LAZY\s*SUSAN/i, label: 'Lazy Susan' },
  { re: /MAGIC\s*CORNER/i, label: 'Magic Corner' },
  { re: /HERRAJE\s*EXTRAIBLE|EXTRAÍBLE/i, label: 'Herraje extraíble' },
  { re: /HERRAJE\s*GIRO|GIRATORIO/i, label: 'Herraje giratorio' },
];

const _precio_color = (c) => {
  if (!c || !c.precios) return null;
  for (const col of COLOR_PRIO) if (c.precios[col] != null) return { precio: c.precios[col], color: col };
  return null;
};

const _medidas_mm = (it) => {
  const m = /^(\d{2,3})/.exec(it.cod || '');
  const ancho = m ? parseInt(m[1], 10) * 10 : (Number(it.ancho) || 600);
  const alto = Number(it.largo) || 0;
  const fondo = Number(it.grueso) || 0;
  return { ancho, alto, fondo };
};

const _tipo_acb_auto = (desc, tipo) => {
  const t = (desc || '').toUpperCase();
  if (/PUERTA DE INTEGRACION|^PTA |ZOCALO|ZÓCALO|^REG |REGLETA|COPETE|COSTADO/.test(t)) return null;
  if (t.includes('FREGADERO')) return 'Bajo Fregadero';
  if (t.includes('BAJO')) return 'Bajo Con Balda';
  if (/SEMICOLUMNA/.test(t)) return 'Semicolumna Despensa';
  if (/COLUMNA/.test(t)) return 'Columna Despensa';
  if (/SOBREMODULO|SOBREMÓDULO|SOBRE MODULO|SOBRE COLUMNA/.test(t)) return 'Alto Con Balda';
  if (t.includes('ALTO') && t.includes('PLATERO')) return 'Alto Platero Con Balda';
  if (t.includes('ALTO') || t.includes('ALTILLO')) return 'Alto Con Balda';
  return tipo === 'bajo' ? 'Bajo Con Balda' : (tipo === 'alto' ? 'Alto Con Balda' : (tipo === 'columna' ? 'Columna Despensa' : null));
};

const _match_acb = (it, tipoOverride, colorOverride, grosorOverride) => {
  const tipoAcb = tipoOverride || _tipo_acb_auto(it.descripcion, it.tipo);
  if (!tipoAcb) return null;
  const { ancho, alto, fondo } = _medidas_mm(it);
  const grosor = grosorOverride || 19;
  const colorKey = colorOverride || 'grafito';
  let pool = CASCOS.filter(c => c.tipo === tipoAcb && c.grosor === grosor && c.precios && c.precios[colorKey] != null);
  if (!pool.length) pool = CASCOS.filter(c => c.tipo === tipoAcb && c.grosor === grosor && _precio_color(c) != null);
  if (!pool.length) pool = CASCOS.filter(c => c.tipo === tipoAcb && _precio_color(c) != null);
  if (!pool.length) return null;
  let best = pool[0], bd = Infinity;
  for (const c of pool) {
    const d = Math.abs((c.ancho || 0) - ancho) * 3
      + (alto ? Math.abs((c.alto || 0) - alto) : 0)
      + (fondo ? Math.abs((c.fondo || 0) - fondo) : 0);
    if (d < bd) { bd = d; best = c; }
  }
  const precio = best.precios[colorKey] ?? _precio_color(best)?.precio ?? 0;
  const colorFinal = best.precios[colorKey] != null ? colorKey : (_precio_color(best)?.color || colorKey);
  return { ...best, _base: precio, _precio: precio * PUNTO, _color: colorFinal, _colorLbl: COLOR_LBL[colorFinal] || colorFinal };
};

// ── Destinos de pedido ───────────────────────────────────────────────────────
// Cada linea se manda a un proveedor distinto. La clasificacion es automatica
// pero SIEMPRE editable en la tabla: si una linea cae en el grupo equivocado se
// corrige en el desplegable, no hay que tocar codigo.
const DESTINOS = {
  cascos:   { id: 'cascos',   label: 'Cascos',   color: '#4f46e5' },
  puertas:  { id: 'puertas',  label: 'Puertas',  color: '#C4622D' },
  herrajes: { id: 'herrajes', label: 'Herrajes', color: '#0891b2' },
  otros:    { id: 'otros',    label: 'Otros',    color: '#64748b' },
};

const _destino_auto = (it, acb) => {
  const t = (it.descripcion || '').toUpperCase();
  if (/^PTA |PUERTA DE INTEGRACION/.test(t)) return 'puertas';
  if (/COSTADO|^REG |REGLETA|COPETE|ZOCALO|ZÓCALO|TABLERO|TRASERA|BANDA/.test(t)) return 'otros';
  if (acb) return 'cascos';
  return 'otros';
};

const _herraje_especial = (desc) => {
  for (const h of HERRAJE_ESPECIAL) if (h.re.test(desc || '')) return h.label;
  return null;
};

// Diagnóstico de red
const _diagnostico = async (e) => {
  const motivo = e?.message || 'error de red';
  if (!API_URL) return 'La aplicación no tiene configurada la dirección del servidor (REACT_APP_BACKEND_URL).';
  if (window.location.protocol === 'https:' && String(API_URL).startsWith('http:'))
    return `El navegador bloquea la llamada: la web va por HTTPS y el servidor está en HTTP (${API_URL}).`;
  const probar = async (url, opts) => {
    try { const r = await fetch(url, opts); let d = {}; try { d = await r.json(); } catch { d = {}; } return { estado: r.status, detail: d.detail || '' }; }
    catch (err) { return { estado: 0, detail: err?.message || 'error de red' }; }
  };
  const ping = await probar(`${API_URL}/api/`, { method: 'GET' });
  if (ping.estado === 0) return `El servidor no responde (${motivo}). Está caído o terminando de desplegarse.`;
  const sondeo = await probar(`${API_URL}/api/cascos/proforma/ping`, { headers: { ...authHeaders() } });
  if (sondeo.estado === 404) return 'El backend sirve la versión anterior. Espera a que termine de desplegarse (1-2 min).';
  return `El envío del PDF corta la conexión (${motivo}). El servidor responde bien. Prueba a subir solo las páginas con la tabla de artículos.`;
};

// ── Componente principal ──────────────────────────────────────────────────────
export default function ProformaImporter({ esMaster }) {
  const [cargando, setCargando] = useState(false);
  const [progreso, setProgreso] = useState('');
  const [error, setError] = useState(null);
  const [items, setItems] = useState([]);
  const [overrides, setOverrides] = useState({}); // { idx: { tipo, color, grosor } }
  const [deletedRows, setDeletedRows] = useState(new Set());
  const [bloqueado, setBloqueado] = useState(false);
  const [showDesc2, setShowDesc2] = useState(false);
  const fileRef = useRef(null);

  // Guardar/cargar proyectos
  const [nombreProyecto, setNombreProyecto] = useState('');
  const [proyectos, setProyectos] = useState([]);
  const [showProyectos, setShowProyectos] = useState(false);
  const [guardando, setGuardando] = useState(false);
  const [cargandoProyecto, setCargandoProyecto] = useState(false);

  // Editor de puertas
  const [showEditorPuertas, setShowEditorPuertas] = useState(false);
  const [precioM2Puerta, setPrecioM2Puerta] = useState('');
  const [puertasEditadas, setPuertasEditadas] = useState({}); // { idx: { alto, ancho } }
  // Mano de obra y coste de puerta POR LINEA. Sin valor propio, cada mueble
  // toma la mano de obra general y cada puerta su precio por m2; con valor,
  // manda el de la linea. Asi se puede subir o bajar un mueble suelto sin
  // tocar el resto.
  const [moLinea, setMoLinea] = useState({});          // { origIdx: euros }
  const [puertaLinea, setPuertaLinea] = useState({});  // { origIdx: euros }
  // Pedido: que lineas van y a que proveedor. Sin entrada propia, la linea va
  // marcada y con el destino que le toca por su descripcion.
  const [excluidas, setExcluidas] = useState({});   // { origIdx: true } -> fuera del pedido
  const [destinoLinea, setDestinoLinea] = useState({}); // { origIdx: 'cascos'|... }
  const [exportando, setExportando] = useState(false);

  const HERRAJE = {
    blum: { cajon: 41.34, gaveta: 54.37 },
    gtv: { cajon: 24.65, gaveta: 29.41 },
  };
  const BISAGRA = { blum: 3.07, emuca: 1.01 };
  const [marcaCaj, setMarcaCaj] = useState('blum');
  const [marcaBis, setMarcaBis] = useState('blum');
  const P_DEFAULT = { desc1: 50, desc2: 28, bisagra: BISAGRA.blum, pata: 1.20, colgador: 3.50, cajon: HERRAJE.blum.cajon, gaveta: HERRAJE.blum.gaveta, manoObra: 0, margen: 0 };
  const [p, setP] = useState(() => {
    try { const s = JSON.parse(localStorage.getItem('alvic_costes') || 'null'); return s ? { ...P_DEFAULT, ...s } : P_DEFAULT; } catch { return P_DEFAULT; }
  });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const setNum = useCallback((k) => (e) => setP(prev => ({ ...prev, [k]: e.target.value === '' ? '' : Number(e.target.value) })), []);
  const cambiarMarcaCaj = (m) => { setMarcaCaj(m); setP(prev => ({ ...prev, cajon: HERRAJE[m].cajon, gaveta: HERRAJE[m].gaveta })); };
  const cambiarMarcaBis = (m) => { setMarcaBis(m); setP(prev => ({ ...prev, bisagra: BISAGRA[m] })); };

  // Persistir costes
  useState(() => { try { localStorage.setItem('alvic_costes', JSON.stringify(p)); } catch { /* noop */ } });

  const importar = async (file) => {
    if (!file) return;
    setCargando(true); setError(null); setItems([]); setProgreso(''); setOverrides({}); setDeletedRows(new Set());
    try {
      const b64 = await new Promise((res, rej) => {
        const fr = new FileReader(); fr.onload = () => res(fr.result); fr.onerror = rej; fr.readAsDataURL(file);
      });
      const r = await fetch(`${API_URL}/api/cascos/proforma`, {
        method: 'POST', headers: getAuthHeaders(), body: JSON.stringify({ pdfBase64: b64 }),
      });
      let d = {}; try { d = await r.json(); } catch { d = {}; }
      if (!r.ok) { setError(d.detail || d.error || `El servidor devolvió un error (${r.status}).`); return; }
      if (d.estado === 'procesando' && d.jobId) {
        setProgreso('Leyendo el PDF…');
        const inicio = Date.now();
        while (Date.now() - inicio < 600000) {
          await new Promise(res => setTimeout(res, 3000));
          const q = await fetch(`${API_URL}/api/cascos/proforma/job/${d.jobId}`, { headers: getAuthHeaders() });
          let j = {}; try { j = await q.json(); } catch { j = {}; }
          if (!q.ok) { setError(j.detail || `El servidor devolvió un error (${q.status}).`); return; }
          if (j.total) setProgreso(`Analizando página ${Math.min(j.hechas + 1, j.total)} de ${j.total}…`);
          if (j.estado === 'listo') { setItems(j.items || []); return; }
          if (j.estado === 'error') { setError(j.detail || 'No se pudieron detectar los muebles.'); return; }
        }
        setError('El análisis está tardando demasiado. Prueba a subir solo las páginas con la tabla de partidas.');
        return;
      }
      if (d.success) setItems(d.items || []);
      else setError(d.detail || d.error || 'No se pudieron detectar los muebles.');
    } catch (e) {
      setError(await _diagnostico(e));
    } finally { setCargando(false); setProgreso(''); }
  };

  const calc = useMemo(() => {
    const facCasco = (1 - (Number(p.desc1) || 0) / 100) * (1 - (Number(p.desc2) || 0) / 100);
    const pm2 = Number(precioM2Puerta) || 0;
    const esPuertaDesc = (d) => /^PTA |PUERTA DE INTEGRACION/i.test(d || '');
    // puertasEditadas se indexa por la POSICION dentro de la lista de puertas,
    // no por la fila; este mapa permite casar una cosa con la otra para que el
    // coste respete las medidas corregidas en el editor de puertas.
    const idxPuertaPorOrig = {};
    let _np = 0;
    items.forEach((it, i) => {
      if (!deletedRows.has(i) && esPuertaDesc(it.descripcion)) { idxPuertaPorOrig[i] = _np; _np += 1; }
    });
    const moGeneral = Number(p.manoObra) || 0;
    const rows = items
      .filter((_, i) => !deletedRows.has(i))
      .map((it, idx) => {
        const origIdx = items.indexOf(it);
        const ov = overrides[origIdx] || {};
        const acb = _match_acb(it, ov.tipo || null, ov.color || null, ov.grosor || null);
        const precioAcb = acb ? (Number(acb._precio) || 0) : 0;
        const casco = precioAcb * facCasco;
        const bisagras = (it.puertas || 0) * 2 * (Number(p.bisagra) || 0);
        const patas = (it.tipo === 'bajo' || it.tipo === 'columna') ? 4 * (Number(p.pata) || 0) : 0;
        const colgadores = (it.tipo === 'alto') ? 2 * (Number(p.colgador) || 0) : 0;
        const guias = (it.cajones || 0) * (Number(p.cajon) || 0) + (it.gavetas || 0) * (Number(p.gaveta) || 0);
        const herraje = bisagras + patas + colgadores + guias;
        const herrajeEsp = _herraje_especial(it.descripcion);

        // Mano de obra: el valor general se aplica A CADA MUEBLE (los paneles,
        // puertas y regletas no llevan). Si la linea tiene valor propio, manda.
        const moPropia = moLinea[origIdx];
        const moDeLinea = (moPropia !== undefined && moPropia !== '')
          ? (Number(moPropia) || 0)
          : (acb ? moGeneral : 0);

        // Puertas: por defecto m2 x precio/m2 (con las medidas del editor si se
        // han corregido); si la linea tiene precio propio, manda ese.
        const esPuerta = idxPuertaPorOrig[origIdx] !== undefined;
        let puertaDeLinea = 0;
        if (esPuerta) {
          const ovp = puertasEditadas[idxPuertaPorOrig[origIdx]] || {};
          const altoP = Number(ovp.alto ?? it.largo) || 0;
          const anchoP = Number(ovp.ancho ?? it.ancho) || 0;
          if (altoP > 0 && anchoP > 0 && pm2 > 0) puertaDeLinea = (altoP / 1000) * (anchoP / 1000) * pm2;
        }
        const puertaPropia = puertaLinea[origIdx];
        if (puertaPropia !== undefined && puertaPropia !== '') puertaDeLinea = Number(puertaPropia) || 0;

        return {
          ...it, _origIdx: origIdx, _acb: acb, _precioAcb: precioAcb,
          _casco: casco, _herraje: herraje, _bis: bisagras, _pat: patas,
          _col: colgadores, _gui: guias, _mat: casco + herraje,
          _herrajeEsp: herrajeEsp,
          _pvpAlvic: Number(it.pvp) || 0,
          _totalAlvic: Number(it.total) || 0,
          _mo: moDeLinea, _puerta: puertaDeLinea, _esPuerta: esPuerta,
          _coste: casco + herraje + moDeLinea + puertaDeLinea,
          _destino: destinoLinea[origIdx] || _destino_auto(it, acb),
          _pedir: !excluidas[origIdx],
        };
      });

    const totMat = rows.reduce((a, r) => a + r._mat, 0);
    const totCasco = rows.reduce((a, r) => a + r._casco, 0);
    const totHerr = rows.reduce((a, r) => a + r._herraje, 0);
    const totAlvic = rows.reduce((a, r) => a + r._totalAlvic, 0);

    // Puertas: items con tipo 'panel' que contienen PTA o PUERTA DE INTEGRACION
    const puertas = items.filter((it, i) => !deletedRows.has(i) && /^PTA |PUERTA DE INTEGRACION/i.test(it.descripcion || ''));
    const costados = items.filter((it, i) => !deletedRows.has(i) && /COSTADO/i.test(it.descripcion || ''));
    const regletas = items.filter((it, i) => !deletedRows.has(i) && /^REG |REGLETA|COPETE|ZOCALO|ZÓCALO/i.test(it.descripcion || ''));
    const totPuertas = rows.reduce((a, r) => a + (r.puertas || 0), 0);
    const sinMatch = rows.filter(r => r.esMueble && !r._acb).length;
    const herrajesEsp = rows.filter(r => r._herrajeEsp);
    const mo = Number(p.manoObra) || 0;
    const margen = Number(p.margen) || 0;
    // La mano de obra ya no es un importe unico: es la suma de la de cada
    // mueble, con las lineas que se hayan retocado a mano.
    const totMo = rows.reduce((a, r) => a + r._mo, 0);
    const nMuebles = rows.filter(r => r._acb).length;
    const costePuertas = rows.reduce((a, r) => a + r._puerta, 0);
    const costeProduccion = totMat + totMo + costePuertas;
    const precioVenta = costeProduccion + margen;

    return { rows, totMat, totCasco, totHerr, totAlvic, totPuertas, sinMatch, herrajesEsp,
             mo, totMo, nMuebles, margen, costeProduccion, precioVenta,
             puertas, costados, regletas, costePuertas, pm2 };
  }, [items, p, overrides, deletedRows, precioM2Puerta, moLinea, puertaLinea, puertasEditadas, destinoLinea, excluidas]);

  // ── Guardar proyecto ──────────────────────────────────────────────────────
  const guardarProyecto = async () => {
    if (!nombreProyecto.trim()) { alert('Escribe un nombre para el proyecto'); return; }
    setGuardando(true);
    try {
      const payload = {
        nombre: nombreProyecto.trim(),
        items,
        overrides,
        parametros: p,
        precioM2Puerta,
      };
      const r = await fetch(`${API_URL}/api/cascos/proforma/proyectos`, {
        method: 'POST', headers: getAuthHeaders(), body: JSON.stringify(payload),
      });
      const d = await r.json();
      if (d.success) { alert(`Proyecto "${nombreProyecto}" guardado ✓`); }
      else alert('Error al guardar: ' + (d.detail || 'desconocido'));
    } catch (e) { alert('Error de red: ' + e.message); }
    finally { setGuardando(false); }
  };

  const cargarProyectos = async () => {
    setCargandoProyecto(true);
    try {
      const r = await fetch(`${API_URL}/api/cascos/proforma/proyectos`, { headers: getAuthHeaders() });
      const d = await r.json();
      setProyectos(d.proyectos || []);
      setShowProyectos(true);
    } catch (e) { alert('Error cargando proyectos: ' + e.message); }
    finally { setCargandoProyecto(false); }
  };

  const abrirProyecto = (proy) => {
    setItems(proy.items || []);
    if (proy.overrides) setOverrides(proy.overrides);
    if (proy.parametros) setP(prev => ({ ...prev, ...proy.parametros }));
    if (proy.precioM2Puerta) setPrecioM2Puerta(proy.precioM2Puerta);
    setNombreProyecto(proy.nombre || '');
    setDeletedRows(new Set());
    setShowProyectos(false);
  };

  // ── Exportar pedido puertas ───────────────────────────────────────────────
  // Linea nueva a mano: para lo que no venga en la proforma (un mueble extra,
  // un accesorio, un porte). Se anade vacia y se rellena en la tabla.
  const anadirLinea = () => {
    setItems(prev => [...prev, {
      n: prev.length + 1, cod: '', descripcion: 'NUEVA LÍNEA', material: '',
      largo: null, ancho: null, grueso: null, cantidad: 1, pvp: null, total: null,
      puertas: 0, cajones: 0, gavetas: 0, tipo: '', esMueble: false, _manual: true,
    }]);
  };

  // ── Pedidos a proveedor en PDF ──────────────────────────────────────────────
  // Un PDF por proveedor, solo con las lineas marcadas. Los HERRAJES son la
  // excepcion: no son lineas de la proforma sino piezas que salen de cada
  // mueble (bisagras, patas, colgadores, guias), asi que se piden por cantidad
  // total, que es como se compran.
  const exportarPedidos = async (destinosPedidos) => {
    const marcadas = calc.rows.filter(r => r._pedir);
    if (!marcadas.length) { alert('No hay ninguna línea marcada para pedir.'); return; }
    setExportando(true);
    try {
      const { jsPDF } = await import('jspdf');
      const autoTable = (await import('jspdf-autotable')).default;
      const hoy = new Date().toLocaleDateString('es-ES');
      const ref = nombreProyecto || 'sin referencia';
      let generados = 0;

      for (const destino of destinosPedidos) {
        const info = DESTINOS[destino];
        // Los herrajes no son lineas de la proforma: son las piezas que lleva
        // cada mueble. Por eso su pedido sale de los MUEBLES marcados, no de las
        // lineas cuyo destino sea 'herrajes' (que no existirian nunca).
        const lineas = destino === 'herrajes'
          ? marcadas.filter(r => r._acb)
          : marcadas.filter(r => r._destino === destino);
        if (!lineas.length) continue;

        const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
        doc.setFontSize(16); doc.setFont(undefined, 'bold');
        doc.text(`Pedido · ${info.label}`, 14, 18);
        doc.setFontSize(9); doc.setFont(undefined, 'normal');
        doc.text(`Referencia: ${ref}`, 14, 25);
        doc.text(`Fecha: ${hoy}`, 14, 30);

        if (destino === 'herrajes') {
          // Se acumulan las piezas de todos los muebles marcados.
          const piezas = {};
          const sumar = (nombre, n) => { if (n > 0) piezas[nombre] = (piezas[nombre] || 0) + n; };
          for (const r of lineas) {
            sumar(`Bisagra ${marcaBis.toUpperCase()}`, (r.puertas || 0) * 2);
            sumar('Pata regulable', (r.tipo === 'bajo' || r.tipo === 'columna') ? 4 : 0);
            sumar('Colgador', r.tipo === 'alto' ? 2 : 0);
            sumar(`Cajón ${marcaCaj.toUpperCase()}`, r.cajones || 0);
            sumar(`Gaveta ${marcaCaj.toUpperCase()}`, r.gavetas || 0);
          }
          const filas = Object.entries(piezas).map(([n, c]) => [n, String(c)]);
          if (!filas.length) { continue; }
          autoTable(doc, {
            startY: 36, head: [['Pieza', 'Cantidad']], body: filas,
            styles: { fontSize: 9 }, headStyles: { fillColor: info.color },
          });
        } else {
          const filas = lineas.map((r, i) => [
            String(i + 1),
            r.cod || '',
            r.descripcion || '',
            r._acb ? `${r._acb.tipo} ${r._acb.ancho}` : '',
            [r.largo, r.ancho, r.grueso].filter(Boolean).join(' × ') || '',
            String(r.cantidad || 1),
          ]);
          autoTable(doc, {
            startY: 36,
            head: [['#', 'Código', 'Descripción', 'Equivalencia', 'Medidas (mm)', 'Ud']],
            body: filas,
            styles: { fontSize: 8, cellPadding: 1.5 },
            headStyles: { fillColor: info.color },
            columnStyles: { 0: { cellWidth: 8 }, 1: { cellWidth: 26 }, 5: { cellWidth: 12, halign: 'center' } },
          });
        }
        doc.save(`pedido-${destino}-${(ref || 'alvic').replace(/[^\w-]+/g, '_')}.pdf`);
        generados += 1;
      }
      if (!generados) alert('Las líneas marcadas no corresponden a ningún pedido de los elegidos.');
    } catch (e) {
      alert(`No se pudo generar el PDF: ${e?.message || 'error'}`);
    } finally { setExportando(false); }
  };

  const exportarPedidoPuertas = () => {
    const lineas = [
      ['#', 'Código', 'Descripción', 'Cantidad', 'Alto (mm)', 'Ancho (mm)', 'Área m²', 'Precio/m²', 'Total €'],
      ...calc.puertas.map((it, i) => {
        const ov = puertasEditadas[i] || {};
        const alto = Number(ov.alto ?? it.largo) || 0;
        const ancho = Number(ov.ancho ?? it.ancho) || 0;
        const area = alto > 0 && ancho > 0 ? ((alto / 1000) * (ancho / 1000)).toFixed(4) : '—';
        const total = calc.pm2 > 0 && area !== '—' ? (parseFloat(area) * calc.pm2).toFixed(2) : '—';
        return [i + 1, it.cod, it.descripcion, it.cantidad || 1, alto || '—', ancho || '—', area, calc.pm2 || '—', total];
      }),
      [],
      ['', '', '', '', '', '', '', 'TOTAL PUERTAS:', calc.costePuertas.toFixed(2) + ' €'],
      [],
      ['COSTADOS'],
      ['#', 'Código', 'Descripción', 'Cantidad', 'Alto (mm)', 'Ancho (mm)'],
      ...calc.costados.map((it, i) => [i + 1, it.cod, it.descripcion, it.cantidad || 1, it.largo || '—', it.ancho || '—']),
      [],
      ['REGLETAS / ZÓCALOS'],
      ['#', 'Código', 'Descripción', 'Cantidad', 'Largo (mm)'],
      ...calc.regletas.map((it, i) => [i + 1, it.cod, it.descripcion, it.cantidad || 1, it.largo || '—']),
    ];
    const csv = lineas.map(r => r.join('\t')).join('\n');
    const blob = new Blob([csv], { type: 'text/tab-separated-values;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url;
    a.download = `pedido-puertas-${nombreProyecto || 'proforma'}.tsv`;
    a.click(); URL.revokeObjectURL(url);
  };

  if (!esMaster) return null;

  return (
    <div className={`bg-white border-2 rounded-2xl overflow-hidden shadow-sm mb-4 ${bloqueado ? 'border-slate-400' : 'border-amber-300'}`}>
      {/* Cabecera */}
      <div className={`flex items-center justify-between gap-3 px-4 py-3 border-b ${bloqueado ? 'bg-slate-100 border-slate-300' : 'bg-amber-50 border-amber-200'}`}>
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-black uppercase tracking-widest text-amber-700 bg-amber-200 px-2 py-0.5 rounded">Solo master</span>
          <h3 className="text-sm font-black text-amber-900">Importar presupuesto de venta → coste / precio</h3>
        </div>
        <div className="flex items-center gap-2">
          {bloqueado && <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wide">Bloqueado</span>}
          <button
            onClick={() => setBloqueado(v => !v)}
            title={bloqueado ? 'Desbloquear edición' : 'Bloquear edición'}
            className={`p-1.5 rounded-lg transition-colors ${bloqueado ? 'bg-slate-200 text-slate-600 hover:bg-slate-300' : 'bg-amber-100 text-amber-700 hover:bg-amber-200'}`}
          >
            {bloqueado ? <Lock size={15} /> : <Unlock size={15} />}
          </button>
        </div>
      </div>

      <div className="p-4 space-y-4">
        {/* Botones de acción */}
        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={() => !bloqueado && fileRef.current?.click()}
            disabled={cargando || bloqueado}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl font-black text-sm text-white bg-amber-600 hover:bg-amber-700 disabled:opacity-50"
          >
            {cargando ? <Loader size={16} className="animate-spin" /> : <Upload size={16} />}
            {cargando ? (progreso || 'Detectando muebles…') : 'Importar presupuesto de venta (PDF)'}
          </button>
          <input ref={fileRef} type="file" accept="application/pdf" className="hidden" onChange={e => importar(e.target.files?.[0])} />
          {items.length > 0 && <span className="text-xs font-bold text-slate-500 flex items-center gap-1"><FileText size={13} /> {items.length - deletedRows.size} líneas</span>}

          {/* Guardar proyecto */}
          {items.length > 0 && !bloqueado && (
            <div className="flex items-center gap-1 ml-auto">
              <input
                type="text"
                placeholder="Nombre del proyecto…"
                value={nombreProyecto}
                onChange={e => setNombreProyecto(e.target.value)}
                className="px-2 py-1.5 border border-slate-200 rounded-lg text-xs w-44"
              />
              <button
                onClick={guardarProyecto}
                disabled={guardando}
                className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-bold bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50"
              >
                {guardando ? <Loader size={12} className="animate-spin" /> : <Save size={12} />} Guardar
              </button>
            </div>
          )}
          <button
            onClick={cargarProyectos}
            disabled={cargandoProyecto}
            className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-bold border border-slate-200 text-slate-600 hover:bg-slate-50"
          >
            {cargandoProyecto ? <Loader size={12} className="animate-spin" /> : <FolderOpen size={12} />} Proyectos
          </button>
        </div>

        {error && <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-sm text-red-700">{error}</div>}

        {/* Lista de proyectos guardados */}
        {showProyectos && (
          <div className="rounded-xl border border-slate-200 p-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-black text-slate-700 uppercase tracking-wide">Proyectos guardados</span>
              <button onClick={() => setShowProyectos(false)}><X size={14} className="text-slate-400" /></button>
            </div>
            {proyectos.length === 0
              ? <p className="text-xs text-slate-400">No hay proyectos guardados.</p>
              : <div className="space-y-1 max-h-48 overflow-y-auto">
                {proyectos.map(o => (
                  <div key={o.id} className="flex items-center justify-between gap-2 px-2 py-1.5 rounded-lg hover:bg-slate-50">
                    <div>
                      <span className="text-xs font-bold text-slate-700">{o.ref || o.cliente}</span>
                      <span className="text-[10px] text-slate-400 ml-2">{new Date(o.createdAt).toLocaleDateString('es-ES')}</span>
                      <span className="text-[10px] text-slate-400 ml-2">{(o.lines || []).length} líneas</span>
                    </div>
                    <button
                      onClick={() => abrirProyecto(o)}
                      className="text-xs font-bold text-indigo-600 hover:text-indigo-800 px-2 py-0.5 rounded border border-indigo-200"
                    >
                      Abrir
                    </button>
                  </div>
                ))}
              </div>
            }
          </div>
        )}

        {items.length > 0 && (
          <>
            {/* Panel de costes */}
            <div className="rounded-xl border border-slate-200 p-3">
              <div className="flex items-center gap-1.5 mb-3 text-slate-600">
                <Calculator size={14} />
                <span className="text-[11px] font-black uppercase tracking-wide">Coste del casco</span>
              </div>

              {/* Descuento 1 + botón para mostrar descuento 2 */}
              <div className="flex items-end gap-2 mb-3 flex-wrap">
                <label className="flex flex-col gap-1">
                  <span className="text-[10px] font-bold text-slate-400 uppercase">Dto casco 1 %</span>
                  <input
                    type="number" step="any" value={p.desc1} onChange={setNum('desc1')}
                    disabled={bloqueado}
                    className="px-2 py-1.5 border-2 border-amber-200 rounded-lg text-sm font-bold w-28 disabled:opacity-60"
                  />
                </label>
                {showDesc2
                  ? (
                    <label className="flex flex-col gap-1">
                      <span className="text-[10px] font-bold text-slate-400 uppercase flex items-center gap-1">
                        Dto casco 2 %
                        <button onClick={() => setShowDesc2(false)} className="text-slate-300 hover:text-slate-500"><X size={10} /></button>
                      </span>
                      <input
                        type="number" step="any" value={p.desc2} onChange={setNum('desc2')}
                        disabled={bloqueado}
                        className="px-2 py-1.5 border-2 border-amber-100 rounded-lg text-sm font-bold w-28 disabled:opacity-60"
                      />
                    </label>
                  )
                  : (
                    <button
                      onClick={() => setShowDesc2(true)}
                      className="mb-0.5 text-[10px] font-bold text-slate-400 hover:text-amber-700 flex items-center gap-1 border border-dashed border-slate-200 rounded-lg px-2 py-1.5"
                    >
                      <ChevronDown size={12} /> + 2º descuento
                    </button>
                  )
                }
              </div>

              {/* Herraje */}
              <div className="flex items-center gap-3 mb-2 flex-wrap">
                <span className="text-[11px] font-black uppercase tracking-wide text-slate-600">Herraje (set + fondo)</span>
                <label className="text-[11px] font-bold text-slate-500 flex items-center gap-1">Cajones/gavetas:
                  <select value={marcaCaj} onChange={e => cambiarMarcaCaj(e.target.value)} disabled={bloqueado} className="border border-slate-200 rounded px-1.5 py-0.5 text-xs font-bold disabled:opacity-60">
                    <option value="blum">BLUM</option><option value="gtv">GTV</option>
                  </select>
                </label>
                <label className="text-[11px] font-bold text-slate-500 flex items-center gap-1">Bisagras:
                  <select value={marcaBis} onChange={e => cambiarMarcaBis(e.target.value)} disabled={bloqueado} className="border border-slate-200 rounded px-1.5 py-0.5 text-xs font-bold disabled:opacity-60">
                    <option value="blum">BLUM</option><option value="emuca">EMUCA</option>
                  </select>
                </label>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
                {[['bisagra', 'Bisagra € (×2/puerta)'], ['pata', 'Pata € (×4/bajo)'], ['colgador', 'Colgador € (×2/alto)'], ['cajon', 'Cajón €'], ['gaveta', 'Gaveta €']].map(([k, l]) => (
                  <label key={k} className="flex flex-col gap-1">
                    <span className="text-[10px] font-bold text-slate-400 uppercase">{l}</span>
                    <input type="number" step="any" value={p[k]} onChange={setNum(k)} disabled={bloqueado} className="px-2 py-1.5 border border-slate-200 rounded-lg text-sm disabled:opacity-60" />
                  </label>
                ))}
              </div>
              <div className="grid grid-cols-2 gap-2 mt-3">
                <label className="flex flex-col gap-1">
                  <span className="text-[10px] font-black text-emerald-600 uppercase">Mano de obra € (coste producción)</span>
                  <input type="number" step="any" value={p.manoObra} onChange={setNum('manoObra')} disabled={bloqueado} className="px-2 py-1.5 border-2 border-emerald-200 rounded-lg text-sm font-bold disabled:opacity-60" />
                </label>
                <label className="flex flex-col gap-1">
                  <span className="text-[10px] font-black text-indigo-600 uppercase">Margen € a ganar (0 = coste)</span>
                  <input type="number" step="any" value={p.margen} onChange={setNum('margen')} disabled={bloqueado} className="px-2 py-1.5 border-2 border-indigo-200 rounded-lg text-sm font-bold disabled:opacity-60" />
                </label>
              </div>
            </div>

            {/* Alertas herraje especial */}
            {calc.herrajesEsp.length > 0 && (
              <div className="rounded-lg bg-orange-50 border border-orange-300 px-3 py-2 text-xs text-orange-800 flex items-start gap-2">
                <AlertTriangle size={14} className="mt-0.5 shrink-0 text-orange-500" />
                <div>
                  <b>Herrajes especiales detectados — cotizar aparte:</b>
                  {calc.herrajesEsp.map((r, i) => (
                    <span key={i} className="block mt-0.5">· Fila {r.n}: <b>{r._herrajeEsp}</b> — {r.descripcion}</span>
                  ))}
                </div>
              </div>
            )}

            {/* Tabla de muebles */}
            {/* Barra de pedidos: que se pide y a quien */}
            <div className="flex flex-wrap items-center gap-2 rounded-xl border border-indigo-200 bg-indigo-50/40 p-2.5">
              <span className="text-[11px] font-black text-indigo-900 uppercase tracking-wide">Pedidos</span>
              {Object.values(DESTINOS).map(d => {
                const n = d.id === 'herrajes'
                  ? calc.rows.filter(r => r._pedir && r._acb).length
                  : calc.rows.filter(r => r._pedir && r._destino === d.id).length;
                return (
                  <button key={d.id} onClick={() => exportarPedidos([d.id])} disabled={!n || exportando}
                    title={n ? `Generar el PDF del pedido de ${d.label}` : `No hay líneas marcadas para ${d.label}`}
                    className="px-2.5 py-1 rounded-lg text-[11px] font-bold text-white disabled:opacity-30"
                    style={{ background: d.color }}>
                    {d.label} ({n})
                  </button>
                );
              })}
              <button onClick={() => exportarPedidos(Object.keys(DESTINOS))} disabled={exportando}
                className="px-2.5 py-1 rounded-lg text-[11px] font-black bg-slate-800 hover:bg-slate-900 text-white disabled:opacity-40 flex items-center gap-1">
                {exportando ? <Loader size={11} className="animate-spin" /> : <Download size={11} />} Todos
              </button>
              <span className="mx-1 w-px h-4 bg-indigo-200" />
              <button onClick={() => setExcluidas({})} disabled={bloqueado}
                className="px-2 py-1 rounded-lg text-[11px] font-bold bg-white border border-slate-200 hover:bg-slate-50 disabled:opacity-40">
                Marcar todas
              </button>
              <button onClick={() => setExcluidas(Object.fromEntries(calc.rows.map(r => [r._origIdx, true])))} disabled={bloqueado}
                className="px-2 py-1 rounded-lg text-[11px] font-bold bg-white border border-slate-200 hover:bg-slate-50 disabled:opacity-40">
                Desmarcar todas
              </button>
              <button onClick={anadirLinea} disabled={bloqueado}
                className="ml-auto px-2.5 py-1 rounded-lg text-[11px] font-black bg-emerald-600 hover:bg-emerald-700 text-white disabled:opacity-40">
                + Añadir línea
              </button>
            </div>

            <div className="overflow-x-auto rounded-xl border border-slate-200">
              <table className="w-full text-xs" style={{ fontVariantNumeric: 'tabular-nums' }}>
                <thead className="bg-slate-50 text-slate-500">
                  <tr className="text-left">
                    <th className="px-2 py-2 w-6"></th>
                    <th className="px-2 py-2 w-6" title="Marcar para incluir en el pedido">Pedir</th>
                    <th className="px-2 py-2">#</th>
                    <th className="px-2 py-2">Código</th>
                    <th className="px-2 py-2">Descripción</th>
                    <th className="px-2 py-2">Casco ACB (equiv.)</th>
                    <th className="px-2 py-2 text-center">P/C/G</th>
                    <th className="px-2 py-2 text-right text-slate-400">Val. Alvic</th>
                    <th className="px-2 py-2 text-right">Tarifa ACB</th>
                    <th className="px-2 py-2 text-right">Casco coste</th>
                    <th className="px-2 py-2 text-right">Herraje</th>
                    <th className="px-2 py-2 text-right">Coste mat.</th>
                    <th className="px-2 py-2 text-right">Mano obra</th>
                    <th className="px-2 py-2 text-right">Puertas</th>
                    <th className="px-2 py-2 text-right font-black">Total línea</th>
                    <th className="px-2 py-2">Pedido a</th>
                  </tr>
                </thead>
                <tbody>
                  {calc.rows.map((r) => (
                    <FilaMueble
                      key={r._origIdx}
                      r={r}
                      bloqueado={bloqueado}
                      override={overrides[r._origIdx] || {}}
                      onOverride={(ov) => setOverrides(prev => ({ ...prev, [r._origIdx]: { ...(prev[r._origIdx] || {}), ...ov } }))}
                      onDelete={() => setDeletedRows(prev => new Set([...prev, r._origIdx]))}
                      moLinea={moLinea[r._origIdx]}
                      onMo={(v) => setMoLinea(prev => ({ ...prev, [r._origIdx]: v }))}
                      puertaLinea={puertaLinea[r._origIdx]}
                      onPuerta={(v) => setPuertaLinea(prev => ({ ...prev, [r._origIdx]: v }))}
                      onPedir={(v) => setExcluidas(prev => ({ ...prev, [r._origIdx]: !v }))}
                      onDestino={(v) => setDestinoLinea(prev => ({ ...prev, [r._origIdx]: v }))}
                      onDescripcion={(v) => setItems(prev => prev.map((x, i) => i === r._origIdx ? { ...x, descripcion: v } : x))}
                      onCod={(v) => setItems(prev => prev.map((x, i) => i === r._origIdx ? { ...x, cod: v } : x))}
                    />
                  ))}
                </tbody>
              </table>
            </div>

            {/* Resumen económico */}
            <div className="grid sm:grid-cols-2 gap-3">
              <div className="rounded-xl border border-slate-200 p-3 text-sm space-y-1">
                <div className="flex justify-between"><span className="text-slate-400 text-xs">Valor Alvic (presupuesto proveedor)</span><b className="text-slate-400">{eur(calc.totAlvic)}</b></div>
                <div className="flex justify-between border-t border-slate-100 pt-1 mt-1"><span className="text-slate-500">Cascos ACB</span><b>{eur(calc.totCasco)}</b></div>
                <div className="flex justify-between"><span className="text-slate-500">Herraje (bisagras, patas, colgadores, guías)</span><b>{eur(calc.totHerr)}</b></div>
                {calc.costePuertas > 0 && <div className="flex justify-between"><span className="text-slate-500">Puertas ({calc.pm2}€/m²)</span><b>{eur(calc.costePuertas)}</b></div>}
                <div className="flex justify-between border-t border-slate-100 pt-1"><span className="text-slate-600 font-bold">Materiales</span><b>{eur(calc.totMat + calc.costePuertas)}</b></div>
                <div className="flex justify-between"><span className="text-emerald-600 font-bold">+ Mano de obra{calc.nMuebles > 0 ? ` (${calc.nMuebles} muebles)` : ''}</span><b className="text-emerald-700">{eur(calc.totMo)}</b></div>
              </div>
              <div className="rounded-xl border-2 border-indigo-200 bg-indigo-50/50 p-3 text-sm space-y-1">
                <div className="flex justify-between"><span className="text-slate-600 font-bold">COSTE de producción</span><b className="text-slate-900">{eur(calc.costeProduccion)}</b></div>
                <div className="flex justify-between"><span className="text-indigo-600 font-bold">+ Margen</span><b className="text-indigo-700">{eur(calc.margen)}</b></div>
                <div className="flex justify-between border-t border-indigo-200 pt-1 text-base"><span className="font-black text-indigo-900">PRECIO DE VENTA</span><b className="text-indigo-900">{eur(calc.precioVenta)}</b></div>
              </div>
            </div>

            {/* Aviso puertas + sin equivalencia */}
            <div className="rounded-lg bg-amber-50 border border-amber-200 px-3 py-2 text-xs text-amber-800 space-y-1">
              <div className="flex items-center justify-between gap-2 flex-wrap">
                <span>
                  <b>Puertas a cotizar:</b> {calc.totPuertas} puerta(s) — el casco ACB va desnudo.
                  {calc.puertas.length > 0 && (
                    <label className="ml-3 inline-flex items-center gap-1">
                      <span className="text-slate-500">€/m²:</span>
                      <input
                        type="number" step="any" value={precioM2Puerta}
                        onChange={e => setPrecioM2Puerta(e.target.value)}
                        disabled={bloqueado}
                        placeholder="0"
                        className="w-16 px-1.5 py-0.5 border border-amber-300 rounded text-xs font-bold disabled:opacity-60"
                      />
                    </label>
                  )}
                </span>
                {(calc.puertas.length > 0 || calc.costados.length > 0 || calc.regletas.length > 0) && (
                  <button
                    onClick={() => setShowEditorPuertas(v => !v)}
                    className="flex items-center gap-1 text-[10px] font-bold text-amber-700 border border-amber-300 rounded px-2 py-0.5 hover:bg-amber-100"
                  >
                    <Edit2 size={10} /> Editor pedido puertas {showEditorPuertas ? <ChevronUp size={10} /> : <ChevronDown size={10} />}
                  </button>
                )}
              </div>
              {calc.sinMatch > 0 && <div className="text-red-600"><b>{calc.sinMatch}</b> mueble(s) sin equivalencia ACB — revísalos.</div>}
            </div>

            {/* Editor de pedido de puertas */}
            {showEditorPuertas && (
              <EditorPuertas
                puertas={calc.puertas}
                costados={calc.costados}
                regletas={calc.regletas}
                pm2={calc.pm2}
                costePuertas={calc.costePuertas}
                puertasEditadas={puertasEditadas}
                setPuertasEditadas={setPuertasEditadas}
                bloqueado={bloqueado}
                onExportar={exportarPedidoPuertas}
              />
            )}
          </>
        )}
      </div>
    </div>
  );
}

// ── Fila de mueble con selector inline de casco/color/grosor ─────────────────
function FilaMueble({ r, bloqueado, override, onOverride, onDelete, moLinea, onMo, puertaLinea, onPuerta, onPedir, onDestino, onDescripcion, onCod }) {
  const [editando, setEditando] = useState(false);
  const tipoActual = override.tipo || (r._acb ? r._acb.tipo : '');
  const colorActual = override.color || (r._acb ? r._acb._color : 'grafito');
  const grosorActual = override.grosor || (r._acb ? r._acb.grosor : 19);

  return (
    <tr className={`border-t border-slate-100 ${r._herrajeEsp ? 'bg-orange-50' : ''}`}>
      <td className="px-1 py-1.5">
        {!bloqueado && (
          <button onClick={onDelete} className="text-slate-300 hover:text-red-500 transition-colors">
            <Trash2 size={12} />
          </button>
        )}
      </td>
      <td className="px-1 py-1.5 text-center">
        <input type="checkbox" checked={r._pedir} disabled={bloqueado}
          onChange={e => onPedir(e.target.checked)} title="Incluir esta línea en el pedido" />
      </td>
      <td className="px-2 py-1.5">{r.n}</td>
      <td className="px-2 py-1.5 font-mono">
        {bloqueado ? r.cod : (
          <input value={r.cod || ''} onChange={e => onCod(e.target.value)} placeholder="código"
            className="w-24 px-1 py-0.5 border border-slate-200 rounded text-xs font-mono" />
        )}
      </td>
      <td className="px-2 py-1.5 max-w-[180px]">
        {bloqueado
          ? <span className="truncate block" title={`${r.descripcion} · ${r.color}`}>{r.descripcion}</span>
          : <input value={r.descripcion || ''} onChange={e => onDescripcion(e.target.value)}
              title={`${r.descripcion} · ${r.color}`}
              className="w-full min-w-[150px] px-1 py-0.5 border border-slate-200 rounded text-xs" />}
        <div className="flex items-center gap-1 flex-wrap">
          {r.herrajeBlum && <span className="text-[9px] font-black text-orange-600">BLUM</span>}
          {r._herrajeEsp && (
            <span className="text-[9px] font-black text-orange-700 bg-orange-100 px-1 rounded flex items-center gap-0.5">
              <AlertTriangle size={8} /> {r._herrajeEsp}
            </span>
          )}
        </div>
      </td>
      <td className="px-2 py-1.5 text-slate-600 min-w-[160px]">
        {editando && !bloqueado ? (
          <div className="flex flex-col gap-1">
            <select
              value={tipoActual}
              onChange={e => onOverride({ tipo: e.target.value })}
              className="border border-slate-200 rounded px-1 py-0.5 text-[10px] w-full"
            >
              <option value="">— tipo —</option>
              {TIPOS_ACB.map(t => <option key={t} value={t}>{t}</option>)}
            </select>
            <div className="flex gap-1">
              <select
                value={colorActual}
                onChange={e => onOverride({ color: e.target.value })}
                className="border border-slate-200 rounded px-1 py-0.5 text-[10px] flex-1"
              >
                {Object.entries(COLOR_LBL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
              <select
                value={grosorActual}
                onChange={e => onOverride({ grosor: Number(e.target.value) })}
                className="border border-slate-200 rounded px-1 py-0.5 text-[10px] w-14"
              >
                <option value={16}>16mm</option>
                <option value={18}>18mm</option>
                <option value={19}>19mm</option>
              </select>
            </div>
            <button onClick={() => setEditando(false)} className="text-[10px] font-bold text-indigo-600 flex items-center gap-0.5">
              <Check size={10} /> Aplicar
            </button>
          </div>
        ) : (
          <div className="flex items-center gap-1 group">
            <span className="text-xs">
              {r._acb
                ? `${r._acb.tipo} ${r._acb.ancho} · ${r._acb._colorLbl} ${r._acb.grosor}`
                : (r.esMueble ? <span className="text-red-500 font-bold">sin equivalencia</span> : '—')}
            </span>
            {!bloqueado && r.esMueble && (
              <button onClick={() => setEditando(true)} className="opacity-0 group-hover:opacity-100 transition-opacity text-slate-400 hover:text-indigo-600">
                <Edit2 size={10} />
              </button>
            )}
          </div>
        )}
      </td>
      <td className="px-2 py-1.5 text-center">{r.puertas}/{r.cajones}/{r.gavetas}</td>
      <td className="px-2 py-1.5 text-right text-slate-400">{r._totalAlvic > 0 ? eur(r._totalAlvic) : '—'}</td>
      <td className="px-2 py-1.5 text-right text-slate-400">{r._precioAcb ? eur(r._precioAcb) : '—'}</td>
      <td className="px-2 py-1.5 text-right">{eur(r._casco)}</td>
      <td className="px-2 py-1.5 text-right" title={`Bisagras ${eur(r._bis)} · Patas ${eur(r._pat)} · Colgadores ${eur(r._col)} · Guías ${eur(r._gui)}`}>
        {r._herraje ? eur(r._herraje) : '—'}
      </td>
      <td className="px-2 py-1.5 text-right text-slate-600">{eur(r._mat)}</td>
      {/* Mano de obra de ESTA linea: vacia = la general del mueble. */}
      <td className="px-2 py-1.5 text-right">
        {bloqueado ? eur(r._mo) : (
          <input
            type="number" step="any"
            value={moLinea ?? ''}
            placeholder={r._mo ? r._mo.toFixed(2) : '0'}
            onChange={e => onMo(e.target.value)}
            title="Vacío = mano de obra general. Escribe un valor para esta línea."
            className={`w-20 px-1 py-0.5 border rounded text-right text-xs ${moLinea !== undefined && moLinea !== '' ? 'border-emerald-400 font-bold text-emerald-700' : 'border-slate-200 text-slate-500'}`}
          />
        )}
      </td>
      {/* Puertas: vacio = m2 x precio/m2. Solo tiene sentido en las puertas. */}
      <td className="px-2 py-1.5 text-right">
        {!r._esPuerta ? <span className="text-slate-300">—</span> : bloqueado ? eur(r._puerta) : (
          <input
            type="number" step="any"
            value={puertaLinea ?? ''}
            placeholder={r._puerta ? r._puerta.toFixed(2) : '0'}
            onChange={e => onPuerta(e.target.value)}
            title="Vacío = área × precio/m². Escribe un precio para esta puerta."
            className={`w-20 px-1 py-0.5 border rounded text-right text-xs ${puertaLinea !== undefined && puertaLinea !== '' ? 'border-amber-400 font-bold text-amber-700' : 'border-slate-200 text-slate-500'}`}
          />
        )}
      </td>
      <td className="px-2 py-1.5 text-right font-black text-slate-800">{eur(r._coste)}</td>
      <td className="px-2 py-1.5">
        {bloqueado ? DESTINOS[r._destino].label : (
          <select value={r._destino} onChange={e => onDestino(e.target.value)}
            title="Proveedor al que se pedirá esta línea"
            className="border border-slate-200 rounded px-1 py-0.5 text-[10px]"
            style={{ color: DESTINOS[r._destino].color }}>
            {Object.values(DESTINOS).filter(d => d.id !== 'herrajes').map(d => <option key={d.id} value={d.id}>{d.label}</option>)}
          </select>
        )}
      </td>
    </tr>
  );
}

// ── Editor de pedido de puertas/costados/regletas ────────────────────────────
function EditorPuertas({ puertas, costados, regletas, pm2, costePuertas, puertasEditadas, setPuertasEditadas, bloqueado, onExportar }) {
  const setMedida = (i, campo, val) => {
    setPuertasEditadas(prev => ({ ...prev, [i]: { ...(prev[i] || {}), [campo]: val } }));
  };

  return (
    <div className="rounded-xl border border-amber-200 bg-amber-50/30 p-3 space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-black text-amber-800 uppercase tracking-wide">Editor pedido puertas / costados / regletas</span>
        <button
          onClick={onExportar}
          className="flex items-center gap-1 text-xs font-bold text-white bg-amber-600 hover:bg-amber-700 px-3 py-1.5 rounded-lg"
        >
          <Download size={12} /> Exportar TSV
        </button>
      </div>

      {/* Puertas */}
      {puertas.length > 0 && (
        <div>
          <div className="text-[10px] font-black text-slate-600 uppercase mb-1.5">
            Puertas ({puertas.length}) {pm2 > 0 && <span className="text-amber-700">— {pm2}€/m² → Total: {costePuertas.toLocaleString('es-ES', { minimumFractionDigits: 2 })}€</span>}
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead className="bg-amber-100 text-amber-800">
                <tr>
                  <th className="px-2 py-1 text-left">#</th>
                  <th className="px-2 py-1 text-left">Código</th>
                  <th className="px-2 py-1 text-left">Descripción</th>
                  <th className="px-2 py-1 text-center">Cant.</th>
                  <th className="px-2 py-1 text-center">Alto mm</th>
                  <th className="px-2 py-1 text-center">Ancho mm</th>
                  <th className="px-2 py-1 text-right">Área m²</th>
                  {pm2 > 0 && <th className="px-2 py-1 text-right">Total €</th>}
                </tr>
              </thead>
              <tbody>
                {puertas.map((it, i) => {
                  const ov = puertasEditadas[i] || {};
                  const alto = Number(ov.alto ?? it.largo) || 0;
                  const ancho = Number(ov.ancho ?? it.ancho) || 0;
                  const area = alto > 0 && ancho > 0 ? (alto / 1000) * (ancho / 1000) : null;
                  const total = area && pm2 > 0 ? area * pm2 : null;
                  return (
                    <tr key={i} className="border-t border-amber-100">
                      <td className="px-2 py-1">{i + 1}</td>
                      <td className="px-2 py-1 font-mono">{it.cod}</td>
                      <td className="px-2 py-1 max-w-[160px] truncate" title={it.descripcion}>{it.descripcion}</td>
                      <td className="px-2 py-1 text-center">{it.cantidad || 1}</td>
                      <td className="px-2 py-1 text-center">
                        {!bloqueado
                          ? <input type="number" value={ov.alto ?? (it.largo || '')} onChange={e => setMedida(i, 'alto', e.target.value)} className="w-16 px-1 py-0.5 border border-amber-200 rounded text-center text-xs" />
                          : (it.largo || '—')}
                      </td>
                      <td className="px-2 py-1 text-center">
                        {!bloqueado
                          ? <input type="number" value={ov.ancho ?? (it.ancho || '')} onChange={e => setMedida(i, 'ancho', e.target.value)} className="w-16 px-1 py-0.5 border border-amber-200 rounded text-center text-xs" />
                          : (it.ancho || '—')}
                      </td>
                      <td className="px-2 py-1 text-right font-mono">{area ? area.toFixed(4) : '—'}</td>
                      {pm2 > 0 && <td className="px-2 py-1 text-right font-bold">{total ? eur(total) : '—'}</td>}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Costados */}
      {costados.length > 0 && (
        <div>
          <div className="text-[10px] font-black text-slate-600 uppercase mb-1.5">Costados ({costados.length})</div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead className="bg-slate-100 text-slate-600">
                <tr>
                  <th className="px-2 py-1 text-left">#</th>
                  <th className="px-2 py-1 text-left">Código</th>
                  <th className="px-2 py-1 text-left">Descripción</th>
                  <th className="px-2 py-1 text-center">Cant.</th>
                  <th className="px-2 py-1 text-center">Alto mm</th>
                  <th className="px-2 py-1 text-center">Ancho mm</th>
                </tr>
              </thead>
              <tbody>
                {costados.map((it, i) => (
                  <tr key={i} className="border-t border-slate-100">
                    <td className="px-2 py-1">{i + 1}</td>
                    <td className="px-2 py-1 font-mono">{it.cod}</td>
                    <td className="px-2 py-1 max-w-[200px] truncate">{it.descripcion}</td>
                    <td className="px-2 py-1 text-center">{it.cantidad || 1}</td>
                    <td className="px-2 py-1 text-center">{it.largo || '—'}</td>
                    <td className="px-2 py-1 text-center">{it.ancho || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Regletas / Zócalos */}
      {regletas.length > 0 && (
        <div>
          <div className="text-[10px] font-black text-slate-600 uppercase mb-1.5">Regletas / Zócalos / Copetes ({regletas.length})</div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead className="bg-slate-100 text-slate-600">
                <tr>
                  <th className="px-2 py-1 text-left">#</th>
                  <th className="px-2 py-1 text-left">Código</th>
                  <th className="px-2 py-1 text-left">Descripción</th>
                  <th className="px-2 py-1 text-center">Cant.</th>
                  <th className="px-2 py-1 text-center">Largo mm</th>
                </tr>
              </thead>
              <tbody>
                {regletas.map((it, i) => (
                  <tr key={i} className="border-t border-slate-100">
                    <td className="px-2 py-1">{i + 1}</td>
                    <td className="px-2 py-1 font-mono">{it.cod}</td>
                    <td className="px-2 py-1 max-w-[200px] truncate">{it.descripcion}</td>
                    <td className="px-2 py-1 text-center">{it.cantidad || 1}</td>
                    <td className="px-2 py-1 text-center">{it.largo || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
