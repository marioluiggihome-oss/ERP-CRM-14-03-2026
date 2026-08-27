/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * EL EXPEDIENTE DE LA OBRA, en la tablet de 8" y de pie.
 *
 * El motor (`backend/services/expediente.py`) ya existía y estaba probado, pero
 * no había pantalla: había que saltar entre módulos para enterarse de en qué
 * punto está una obra y qué falta.
 *
 * TRES DECISIONES QUE NO SON DE ESTILO
 * ------------------------------------
 * 1. LOS IMPORTES NO SE OCULTAN AQUÍ. Los oculta el servidor no mandándolos.
 *    Si `verImportes` es false, la clave `importes` NI SIQUIERA VIENE. Esta
 *    pantalla no enmascara nada: pinta lo que le llega. Tapar un dato en el
 *    navegador no protege nada, se ve abriendo el inspector.
 *
 * 2. LO QUE NO SE SABE NO SE PINTA COMO CERO. Un importe que no viene se
 *    queda sin fila. Un cero es un dato falso y encima creíble.
 *
 * 3. TODO CABE DE ANCHO. En 8" no hay sitio para una tabla: son tarjetas en
 *    una sola columna, con el texto partido, y lo único que rueda en
 *    horizontal es la tira de etapas, que es una tira a propósito. Lo dijo el
 *    master: «las páginas no se ven enteras en las tablets de 8 pulgadas».
 *    Los botones son de 44 px de alto porque se pulsan con el dedo y con la
 *    obra puesta.
 */
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ClipboardList, Search, RefreshCw, Loader, AlertTriangle, CheckCircle2,
  ChevronLeft, Factory, Euro, User, ArrowRight, ShieldCheck, XCircle, Ruler,
} from 'lucide-react';
import { projectsAPI, proformaAPI, expedienteAPI, medidasAPI } from '../services/api';
import BotonPantallaCompleta from './BotonPantallaCompleta';

// Cómo se lee cada importe. `margen` y `descuento` son porcentajes; el resto,
// euros. Un importe que no esté en este mapa se pinta tal cual antes que
// ponerle una unidad inventada.
const IMPORTES = {
  totalPvp: { etiqueta: 'PVP', unidad: 'eur' },
  totalCoste: { etiqueta: 'Coste', unidad: 'eur' },
  totalConIVA: { etiqueta: 'Total con IVA', unidad: 'eur' },
  margen: { etiqueta: 'Margen', unidad: 'pct' },
  descuento: { etiqueta: 'Descuento', unidad: 'pct' },
  descuentoAplicado: { etiqueta: 'Descuento', unidad: 'pct' },
};

const EUR = new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR' });

const formatearImporte = (clave, valor) => {
  if (valor === null || valor === undefined || valor === '') return null;
  const n = Number(valor);
  if (!Number.isFinite(n)) return String(valor);
  const unidad = (IMPORTES[clave] || {}).unidad;
  if (unidad === 'eur') return EUR.format(n);
  if (unidad === 'pct') return `${n.toFixed(1)} %`;
  return String(valor);
};

const ESTADO_COLOR = {
  borrador: 'bg-slate-100 text-slate-600',
  draft: 'bg-slate-100 text-slate-600',
  enviado: 'bg-blue-100 text-blue-700',
  aceptado: 'bg-green-100 text-green-700',
  en_fabricacion: 'bg-orange-100 text-orange-700',
  entregado: 'bg-indigo-100 text-indigo-700',
  rechazado: 'bg-red-100 text-red-600',
};

// Quién resuelve cada cosa, con color propio: en obra se busca «lo mío» de un
// vistazo, no se lee la lista entera.
const COLOR_RESPONSABLE = {
  Diseñador: 'bg-purple-100 text-purple-700',
  Comercial: 'bg-blue-100 text-blue-700',
  Gerencia: 'bg-amber-100 text-amber-800',
  Montador: 'bg-emerald-100 text-emerald-700',
  'Sin asignar': 'bg-slate-100 text-slate-600',
};

const textoDelSitio = (donde) => {
  if (!donde || !donde.tipo) return '';
  if (donde.tipo === 'linea') {
    const ids = (donde.ids || []).join(', ');
    return ids ? `En las líneas: ${ids}` : 'En las líneas del presupuesto';
  }
  if (donde.tipo === 'cambios') return 'En los cambios del proyecto';
  if (donde.tipo === 'acabados') return 'En los acabados del proyecto';
  return '';
};


// ─── Selector de obra ───────────────────────────────────────────────────────

const SelectorDeObra = ({ proyectos, cargando, error, onElegir, onRecargar, busqueda, setBusqueda }) => (
  <div className="h-full flex flex-col min-w-0">
    <div className="shrink-0 p-3 border-b border-slate-200 bg-white">
      <div className="flex items-center gap-2">
        <div className="relative flex-1 min-w-0">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            placeholder="Cliente, nº de presupuesto o referencia"
            className="w-full min-h-[44px] pl-9 pr-3 rounded-xl border border-slate-300 text-[14px] focus:outline-none focus:ring-2 focus:ring-slate-900/10"
            data-testid="buscar-obra"
          />
        </div>
        <button
          type="button"
          onClick={onRecargar}
          className="shrink-0 min-h-[44px] min-w-[44px] flex items-center justify-center rounded-xl border border-slate-300 text-slate-600 active:bg-slate-100"
          aria-label="Recargar la lista de obras"
        >
          <RefreshCw size={16} className={cargando ? 'animate-spin' : ''} />
        </button>
      </div>
    </div>

    <div className="flex-1 overflow-y-auto overflow-x-hidden p-3 space-y-2">
      {error && (
        <div className="flex items-start gap-2 p-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-[13px]">
          <AlertTriangle size={16} className="shrink-0 mt-0.5" />
          <span className="min-w-0 break-words">{error}</span>
        </div>
      )}
      {cargando && !proyectos.length && (
        <div className="flex items-center justify-center py-10 text-slate-400">
          <Loader size={22} className="animate-spin" />
        </div>
      )}
      {!cargando && !proyectos.length && !error && (
        <p className="text-center text-[13px] text-slate-500 py-10">
          No hay obras que coincidan con la búsqueda.
        </p>
      )}

      {proyectos.map((p) => (
        <button
          key={p.id}
          type="button"
          onClick={() => onElegir(p)}
          className="w-full text-left p-3 rounded-2xl bg-white border border-slate-200 active:bg-slate-50 shadow-sm min-w-0"
        >
          <div className="flex items-center gap-2 min-w-0">
            <div className="min-w-0 flex-1">
              <p className="text-[14px] font-black text-slate-900 truncate">
                {p.customerName || p.clientCode || 'Sin cliente'}
              </p>
              <p className="text-[11px] text-slate-500 truncate">
                <span className={p._origen === 'casco' ? 'text-cyan-700 font-bold' : 'text-slate-400'}>
                  {p._de}
                </span>
                {' · '}{p.budgetNumber || p.id}
                {p.internalReference ? ` · ${p.internalReference}` : ''}
              </p>
            </div>
            <span className={`shrink-0 px-2 py-1 rounded-lg text-[10px] font-black uppercase ${ESTADO_COLOR[p.status] || ESTADO_COLOR.borrador}`}>
              {(p.status || 'borrador').replace('_', ' ')}
            </span>
            <ArrowRight size={16} className="shrink-0 text-slate-400" />
          </div>
        </button>
      ))}
    </div>
  </div>
);


// ─── Tira de etapas ─────────────────────────────────────────────────────────

const TiraDeEtapas = ({ etapas, actual }) => {
  const i = Math.max(0, (etapas || []).indexOf(actual));
  return (
    // Lo ÚNICO que rueda en horizontal de toda la pantalla, y es una tira: en
    // 8" no caben siete etapas de ancho y partirlas en dos filas roba alto,
    // que es justo lo que falta.
    <div className="flex gap-1.5 overflow-x-auto pb-1 -mx-1 px-1">
      {(etapas || []).map((e, idx) => (
        <span
          key={e}
          className={`shrink-0 px-2.5 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-wide ${
            idx === i ? 'bg-slate-900 text-white'
              : idx < i ? 'bg-emerald-100 text-emerald-700'
              : 'bg-slate-100 text-slate-400'
          }`}
        >
          {e}
        </span>
      ))}
    </div>
  );
};


// ─── Una cosa pendiente ─────────────────────────────────────────────────────

const Accion = ({ accion, onAprobar, aprobando }) => {
  const esCambio = accion.donde && accion.donde.tipo === 'cambios'
    && accion.donde.indice !== undefined && accion.donde.indice !== null;
  const sitio = textoDelSitio(accion.donde);

  return (
    <div className={`p-3 rounded-2xl border min-w-0 ${
      accion.bloquea ? 'bg-red-50 border-red-200' : 'bg-amber-50 border-amber-200'
    }`}>
      <div className="flex items-start gap-2 min-w-0">
        {accion.bloquea
          ? <XCircle size={16} className="shrink-0 mt-0.5 text-red-600" />
          : <AlertTriangle size={16} className="shrink-0 mt-0.5 text-amber-600" />}
        <div className="min-w-0 flex-1">
          <p className="text-[14px] font-black text-slate-900 break-words">{accion.titulo}</p>
          {accion.detalle && (
            <p className="text-[12px] text-slate-600 mt-0.5 break-words">{accion.detalle}</p>
          )}
          {sitio && <p className="text-[11px] text-slate-500 mt-1 break-words">{sitio}</p>}
          <div className="flex items-center gap-1.5 flex-wrap mt-2">
            <span className={`px-2 py-0.5 rounded-lg text-[10px] font-black uppercase ${
              COLOR_RESPONSABLE[accion.responsable] || COLOR_RESPONSABLE['Sin asignar']}`}>
              <User size={9} className="inline mr-1 -mt-0.5" />{accion.responsable}
            </span>
            <span className={`px-2 py-0.5 rounded-lg text-[10px] font-black uppercase ${
              accion.bloquea ? 'bg-red-600 text-white' : 'bg-amber-500 text-white'}`}>
              {accion.bloquea ? 'Bloquea' : 'Aviso'}
            </span>
          </div>
        </div>
      </div>

      {esCambio && (
        <button
          type="button"
          onClick={() => onAprobar(accion.donde.indice)}
          disabled={aprobando}
          className="mt-2 w-full min-h-[44px] rounded-xl bg-slate-900 text-white text-[13px] font-black uppercase tracking-wide active:bg-slate-800 disabled:opacity-50"
        >
          {aprobando ? 'Aprobando…' : 'Aprobar el cambio'}
        </button>
      )}
    </div>
  );
};


// ─── Las medidas de la obra, con sus tres niveles ───────────────────────────
//
// Aquí es donde se usa: de pie en la cocina, con el metro en una mano y la
// tablet en la otra. Por eso cada medida es una tarjeta y cada acción un botón
// del tamaño de un dedo.
//
// CONFIRMAR NO VIENE RELLENO. El campo enseña la de obra como pista pero NO la
// escribe: confirmar es el acto de dar por buena una medida, y traerla puesta
// convertiría el botón en un «aceptar» que no comprueba nada. Para no obligar
// a teclear cuatro cifras con guantes, hay un botón que la copia — copiarla es
// entonces una decisión visible, que es justo lo que tiene que ser.

const COLOR_NIVEL = {
  sin_medir: 'bg-slate-200 text-slate-600',
  introducida: 'bg-blue-100 text-blue-700',
  tomada: 'bg-amber-100 text-amber-800',
  confirmada: 'bg-emerald-100 text-emerald-700',
};

const Medida = ({ m, onTomar, onConfirmar, ocupada }) => {
  const [tomada, setTomada] = useState('');
  const [confirmada, setConfirmada] = useState('');

  return (
    <div className={`p-3 rounded-2xl border min-w-0 ${
      m.bloquea ? 'bg-red-50 border-red-200'
        : m.discrepa ? 'bg-amber-50 border-amber-200' : 'bg-white border-slate-200'
    }`}>
      <div className="flex items-start gap-2 min-w-0">
        <div className="min-w-0 flex-1">
          <p className="text-[14px] font-black text-slate-900 break-words">
            {m.etiqueta}
            {m.critica && (
              <span className="ml-1.5 px-1.5 py-0.5 rounded bg-slate-900 text-white text-[9px] font-black uppercase align-middle">
                Crítica
              </span>
            )}
          </p>
          <span className={`inline-block mt-1 px-2 py-0.5 rounded-lg text-[10px] font-black uppercase ${COLOR_NIVEL[m.nivel]}`}>
            {m.nivelEtiqueta}
          </span>
        </div>
        {m.diferencia !== null && m.diferencia !== undefined && m.discrepa && (
          <span className="shrink-0 px-2 py-1 rounded-lg bg-amber-500 text-white text-[12px] font-black">
            {m.diferencia > 0 ? '+' : ''}{m.diferencia} {m.unidad}
          </span>
        )}
      </div>

      {/* Los tres números, siempre los tres a la vista: la diferencia entre
          ellos es el dato, y esconder el de la venta la borraría. */}
      <div className="grid grid-cols-3 gap-2 mt-2">
        {[['Venta', m.introducida], ['Obra', m.tomada], ['Confirmada', m.confirmada]].map(([lbl, v]) => (
          <div key={lbl} className="min-w-0">
            <p className="text-[10px] uppercase font-bold text-slate-400 truncate">{lbl}</p>
            <p className={`text-[15px] font-black truncate ${v === null || v === undefined ? 'text-slate-300' : 'text-slate-900'}`}>
              {v === null || v === undefined ? '—' : v}
            </p>
          </div>
        ))}
      </div>

      {m.pendiente && (
        <p className="text-[12px] text-slate-600 mt-2 break-words">{m.pendiente}</p>
      )}

      <div className="grid sm:grid-cols-2 gap-2 mt-2">
        <div className="flex gap-1.5 min-w-0">
          <input type="number" step="any" value={tomada} onChange={e => setTomada(e.target.value)}
            placeholder={`Medir (${m.unidad})`}
            className="flex-1 min-w-0 min-h-[44px] px-2 rounded-xl border border-slate-300 text-[14px]" />
          <button onClick={() => { onTomar(m.clave, tomada); setTomada(''); }}
            disabled={tomada === '' || ocupada}
            className="shrink-0 min-h-[44px] px-3 rounded-xl bg-amber-600 text-white text-[12px] font-black uppercase disabled:opacity-40">
            Apuntar
          </button>
        </div>
        <div className="flex gap-1.5 min-w-0">
          <input type="number" step="any" value={confirmada} onChange={e => setConfirmada(e.target.value)}
            placeholder={m.tomada != null ? `Confirmar (obra: ${m.tomada})` : 'Confirmar'}
            title="Escribe la medida buena. Puede no ser ninguna de las dos anteriores."
            className="flex-1 min-w-0 min-h-[44px] px-2 rounded-xl border border-slate-300 text-[14px]" />
          {m.tomada != null && confirmada === '' && (
            <button onClick={() => setConfirmada(String(m.tomada))}
              title="Copiar la medida de obra al campo de confirmar"
              className="shrink-0 min-h-[44px] px-2 rounded-xl border border-slate-300 bg-white text-[11px] font-bold text-slate-600">
              ← obra
            </button>
          )}
          <button onClick={() => { onConfirmar(m.clave, confirmada); setConfirmada(''); }}
            disabled={confirmada === '' || ocupada}
            className="shrink-0 min-h-[44px] px-3 rounded-xl bg-emerald-600 text-white text-[12px] font-black uppercase disabled:opacity-40">
            Confirmar
          </button>
        </div>
      </div>
    </div>
  );
};

const NuevaMedida = ({ onCrear, ocupada }) => {
  const [m, setM] = useState({ etiqueta: '', introducida: '', unidad: 'mm', critica: true });

  // La clave sale de la etiqueta: sin clave la medida no se puede volver a
  // encontrar ni comparar con nada, así que no se deja crear sin ella.
  const claveDe = (t) => t.trim().toLowerCase()
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '');
  // Sin clave la medida no se puede volver a encontrar ni comparar con nada,
  // y el servidor la rechaza. Una etiqueta de solo signos («¿?») da clave
  // vacía, así que se mira la clave y no la etiqueta.
  const listo = claveDe(m.etiqueta).length > 0;

  return (
    <div className="p-3 rounded-2xl border-2 border-dashed border-slate-300 bg-white min-w-0 space-y-2">
      <input value={m.etiqueta} onChange={e => setM(p => ({ ...p, etiqueta: e.target.value }))}
        placeholder="Qué se mide (p. ej. «Hueco de la columna»)"
        className="w-full min-h-[44px] px-3 rounded-xl border border-slate-300 text-[14px]" />
      <div className="flex gap-2 flex-wrap">
        <input type="number" step="any" value={m.introducida}
          onChange={e => setM(p => ({ ...p, introducida: e.target.value }))}
          placeholder="De la venta (opcional)"
          className="flex-1 min-w-[140px] min-h-[44px] px-3 rounded-xl border border-slate-300 text-[14px]" />
        <label className="flex items-center gap-2 min-h-[44px] px-3 rounded-xl border border-slate-300 text-[13px] font-bold text-slate-700">
          <input type="checkbox" checked={m.critica}
            onChange={e => setM(p => ({ ...p, critica: e.target.checked }))} />
          Crítica
        </label>
        <button onClick={() => {
          onCrear({
            clave: claveDe(m.etiqueta), etiqueta: m.etiqueta.trim(),
            introducida: m.introducida === '' ? null : Number(m.introducida),
            unidad: m.unidad, critica: m.critica,
          });
          setM({ etiqueta: '', introducida: '', unidad: 'mm', critica: true });
        }} disabled={!listo || ocupada}
          className="min-h-[44px] px-4 rounded-xl bg-slate-900 text-white text-[13px] font-black uppercase disabled:opacity-40">
          Añadir
        </button>
      </div>
      <p className="text-[11px] text-slate-500">
        Crítica = sin confirmar, no baja al taller. Las demás solo avisan.
      </p>
    </div>
  );
};


// ─── Lo presupuestado contra lo que hay en la orden de fabricación ──────────

const _valor = (v) => (v === null || v === undefined || v === '' ? '—' : String(v));

const LineaSuelta = ({ n }) => (
  <p className="text-[12px] text-slate-700 break-words">
    · {n.codigo || n.nombre || 'Línea sin código'}
    {n.width ? ` (${n.width}×${n.height || '?'})` : ''}
  </p>
);

const ComparacionConFabrica = ({ comparacion }) => {
  const c = comparacion.comparacion || {};
  const cambiados = c.cambiados || [];
  const soloPres = c.soloPresupuesto || [];
  const soloFab = c.soloFabricacion || [];

  return (
    <div className="mt-2 p-3 rounded-2xl bg-white border border-slate-200 min-w-0 space-y-2">
      <p className="text-[11px] font-black uppercase tracking-wide text-slate-500 break-words">
        Orden {comparacion.ordenNumero || comparacion.numeroFabricacion || ''}
      </p>
      <p className={`text-[13px] font-bold break-words ${c.hayDiferencias ? 'text-amber-800' : 'text-emerald-700'}`}>
        {c.resumen || ''}
      </p>

      {/* Un cambio de 60 a 600 no es un cambio: es un lío de unidades, y se
          dice aparte porque se arregla de otra manera. */}
      {c.posibleLioDeUnidades && (
        <p className="p-2 rounded-xl bg-red-50 border border-red-200 text-[12px] text-red-700 break-words">
          Alguna diferencia parece un lío de centímetros contra milímetros. Míralo antes de cortar.
        </p>
      )}

      {cambiados.map((l, i) => (
        <div key={i} className="p-2 rounded-xl bg-amber-50 border border-amber-200 min-w-0">
          <p className="text-[12px] font-black text-amber-900 break-words">
            {l.codigo || l.nombre || 'Línea'}
          </p>
          {(l.diferencias || []).map((d, j) => (
            <p key={j} className="text-[11px] text-amber-800 break-words">
              {d.campo}: {_valor(d.antes)} → {_valor(d.despues)}
              {d.unidades ? ' (¿cm/mm?)' : ''}
            </p>
          ))}
        </div>
      ))}

      {soloPres.length > 0 && (
        <div className="p-2 rounded-xl bg-slate-50 border border-slate-200 min-w-0">
          <p className="text-[11px] font-black uppercase text-slate-500">Presupuestado y no fabricado</p>
          {soloPres.map((n, i) => <LineaSuelta key={i} n={n} />)}
        </div>
      )}

      {soloFab.length > 0 && (
        <div className="p-2 rounded-xl bg-slate-50 border border-slate-200 min-w-0">
          <p className="text-[11px] font-black uppercase text-slate-500">En fabricación y no presupuestado</p>
          {soloFab.map((n, i) => <LineaSuelta key={i} n={n} />)}
        </div>
      )}
    </div>
  );
};


// ─── Pantalla ───────────────────────────────────────────────────────────────

export default function Expediente({ state }) {
  const usuarioId = state?.currentUser?.id;

  const [proyectos, setProyectos] = useState([]);
  const [cargandoLista, setCargandoLista] = useState(false);
  const [errorLista, setErrorLista] = useState('');
  const [busqueda, setBusqueda] = useState('');

  const [obra, setObra] = useState(null);       // el proyecto elegido (de la lista)
  const [exp, setExp] = useState(null);         // lo que manda el servidor
  const [cargandoExp, setCargandoExp] = useState(false);
  const [errorExp, setErrorExp] = useState('');
  const [aprobando, setAprobando] = useState(null);

  const [comparacion, setComparacion] = useState(null);
  const [comparando, setComparando] = useState(false);
  const [errorComparacion, setErrorComparacion] = useState('');

  // Medidas de la obra. Van aparte del expediente porque se tocan aquí mismo,
  // con el metro en la mano, y hay que poder recargarlas solas sin volver a
  // pedir el expediente entero.
  const [medidas, setMedidas] = useState(null);
  const [errorMedidas, setErrorMedidas] = useState('');
  const [ocupadaMedida, setOcupadaMedida] = useState(false);

  // LAS OBRAS DE LAS TRES COCINAS, EN UNA SOLA LISTA. Cocina Montada 1 y 2
  // guardan proyectos; Cocina Desmontada guarda pedidos de casco. Para quien
  // busca una obra es la misma pregunta —«¿cómo va lo de María García?»— así
  // que no se le pide que sepa en qué módulo se tecleó.
  const cargarLista = useCallback(async () => {
    setCargandoLista(true);
    setErrorLista('');
    try {
      const [proj, casco] = await Promise.all([
        projectsAPI.getAll(usuarioId).catch(() => []),
        // Los pedidos de casco pueden estar cerrados para este usuario; si no
        // llegan, la lista sigue con lo demás en vez de quedarse vacía.
        proformaAPI.listarPedidos(usuarioId).then(d => d?.orders || []).catch(() => []),
      ]);
      const proyectos = (Array.isArray(proj) ? proj : (proj?.projects || []))
        .map(p => ({ ...p, _origen: 'proj', _de: 'Cocina Montada' }));
      const pedidos = casco.map(o => ({
        ...o, _origen: 'casco', _de: 'Cocina Desmontada',
        // Se traduce lo justo para pintar la ficha; lo demás lo trae el
        // expediente cuando se abre.
        budgetNumber: o.expediente || o.ref || o.id,
        customerName: o.cliente || '',
        internalReference: o.ref || '',
        status: o.kind === 'presupuesto' ? 'borrador' : 'aceptado',
      }));
      setProyectos([...proyectos, ...pedidos]);
    } catch (e) {
      setErrorLista(e.message || 'No se pudo cargar la lista de obras.');
    } finally {
      setCargandoLista(false);
    }
  }, [usuarioId]);

  useEffect(() => { cargarLista(); }, [cargarLista]);

  const cargarExpediente = useCallback(async (projectId, origen = 'proj') => {
    setCargandoExp(true);
    setErrorExp('');
    try {
      const data = await expedienteAPI.get(projectId, origen);
      setExp(data);
    } catch (e) {
      // Se deja `exp` como estaba y se dice qué ha fallado. Vaciarlo dejaría
      // la pantalla en blanco sin explicar por qué.
      setErrorExp(e.message || 'No se pudo abrir el expediente.');
    } finally {
      setCargandoExp(false);
    }
  }, []);

  const cargarMedidas = useCallback(async (projectId, origen = 'proj') => {
    setErrorMedidas('');
    try {
      setMedidas(await medidasAPI.listar(projectId, origen));
    } catch (e) {
      setErrorMedidas(e.message || 'No se pudieron leer las medidas.');
    }
  }, []);

  const abrir = useCallback((p) => {
    setObra(p);
    setExp(null);
    setComparacion(null);
    setErrorComparacion('');
    setMedidas(null);
    setErrorMedidas('');
    cargarExpediente(p.id, p._origen);
    cargarMedidas(p.id, p._origen);
  }, [cargarExpediente, cargarMedidas]);

  // Tomar y confirmar son la MISMA operación con distinto nombre, y el motor
  // ya las distingue: aquí solo cambia a qué ruta se llama.
  const cambiarNivel = useCallback(async (accion, clave, valor) => {
    if (!obra) return;
    setOcupadaMedida(true);
    setErrorMedidas('');
    try {
      const fn = accion === 'tomar' ? medidasAPI.tomar : medidasAPI.confirmar;
      setMedidas(await fn(obra.id, clave, valor === '' ? null : Number(valor), obra._origen));
      // Una medida crítica confirmada puede desbloquear la fabricación, y eso
      // lo dice el expediente: si no se recarga, el cartel de arriba sigue
      // diciendo que hay bloqueos que ya no hay.
      cargarExpediente(obra.id, obra._origen);
    } catch (e) {
      setErrorMedidas(e.message || 'No se pudo guardar la medida.');
    } finally { setOcupadaMedida(false); }
  }, [obra, cargarExpediente]);

  const crearMedida = useCallback(async (nueva) => {
    if (!obra) return;
    const yaEsta = (medidas?.medidas || []).some(m => m.clave === nueva.clave);
    if (yaEsta) { setErrorMedidas(`Ya hay una medida llamada «${nueva.etiqueta}».`); return; }
    setOcupadaMedida(true);
    setErrorMedidas('');
    try {
      // Se manda la lista entera: guardar NO sube de nivel (eso son `tomar` y
      // `confirmar`, cada una con su autor y su fecha), así que las que ya
      // estaban vuelven tal cual.
      // Se devuelven TAMBIÉN quién y cuándo: lo que no se mande aquí se
      // pierde, y añadir una medida borraría quién tomó las demás. Una medida
      // que no se le puede preguntar a nadie vale la mitad.
      const lista = [...(medidas?.medidas || []).map(m => ({
        clave: m.clave, etiqueta: m.etiqueta, unidad: m.unidad, critica: m.critica,
        introducida: m.introducida, tomada: m.tomada, confirmada: m.confirmada,
        notas: m.notas,
        tomadaPor: m.tomadaPor, tomadaAt: m.tomadaAt,
        confirmadaPor: m.confirmadaPor, confirmadaAt: m.confirmadaAt,
      })), nueva];
      setMedidas(await medidasAPI.guardar(obra.id, lista, obra._origen));
    } catch (e) {
      setErrorMedidas(e.message || 'No se pudo añadir la medida.');
    } finally { setOcupadaMedida(false); }
  }, [obra, medidas]);

  const aprobarCambio = useCallback(async (indice) => {
    if (!obra) return;
    setAprobando(indice);
    setErrorExp('');
    try {
      await expedienteAPI.aprobarCambio(obra.id, indice);
      await cargarExpediente(obra.id);
    } catch (e) {
      setErrorExp(e.message || 'No se pudo aprobar el cambio.');
    } finally {
      setAprobando(null);
    }
  }, [obra, cargarExpediente]);

  const compararConFabrica = useCallback(async () => {
    if (!obra) return;
    setComparando(true);
    setErrorComparacion('');
    try {
      setComparacion(await expedienteAPI.compararFabricacion(obra.id));
    } catch (e) {
      setErrorComparacion(e.message || 'No se pudo comparar con fabricación.');
    } finally {
      setComparando(false);
    }
  }, [obra]);

  const filtrados = useMemo(() => {
    const q = busqueda.trim().toLowerCase();
    const lista = proyectos.filter((p) => (p.status || '') !== 'archived');
    if (!q) return lista.slice(0, 200);
    return lista.filter((p) => [
      p.customerName, p.budgetNumber, p.clientCode, p.internalReference, p.reference,
    ].some((v) => String(v || '').toLowerCase().includes(q))).slice(0, 200);
  }, [proyectos, busqueda]);

  // Los importes que REALMENTE han llegado. Si el usuario no puede verlos, la
  // clave `importes` no viene y esto queda vacío: no hay nada que tapar.
  const importes = useMemo(() => {
    const src = exp?.importes || {};
    return Object.keys(IMPORTES)
      .map((k) => ({ clave: k, etiqueta: IMPORTES[k].etiqueta, texto: formatearImporte(k, src[k]) }))
      .filter((x) => x.texto !== null);
  }, [exp]);

  if (!obra) {
    return (
      <div className="h-full flex flex-col bg-slate-50 min-w-0">
        <div className="hueco-logo shrink-0 flex items-center gap-2 px-3 py-2 bg-slate-900 text-white">
          <ClipboardList size={18} className="shrink-0" />
          <h1 className="text-[14px] font-black uppercase tracking-wide truncate">Expediente de obra</h1>
          <div className="ml-auto shrink-0">
            <BotonPantallaCompleta mostrarTexto={false} className="p-2 rounded-xl text-slate-300 active:bg-white/10" />
          </div>
        </div>
        <div className="flex-1 min-h-0">
          <SelectorDeObra
            proyectos={filtrados}
            cargando={cargandoLista}
            error={errorLista}
            onElegir={abrir}
            onRecargar={cargarLista}
            busqueda={busqueda}
            setBusqueda={setBusqueda}
          />
        </div>
      </div>
    );
  }

  const cab = exp?.cabecera || {};
  const acciones = exp?.acciones || [];
  const bloqueos = exp?.bloqueos || 0;

  return (
    <div className="h-full flex flex-col bg-slate-50 min-w-0">
      {/* Cabecera fija: en obra se mira la pantalla de refilón y hay que saber
          de quién es la cocina sin volver arriba. */}
      <div className="shrink-0 px-3 py-2 bg-slate-900 text-white">
        <div className="flex items-center gap-2 min-w-0">
          <button
            type="button"
            onClick={() => { setObra(null); setExp(null); }}
            className="shrink-0 min-h-[40px] min-w-[40px] flex items-center justify-center rounded-xl active:bg-white/10"
            aria-label="Volver a la lista de obras"
          >
            <ChevronLeft size={20} />
          </button>
          <div className="min-w-0 flex-1">
            <p className="text-[14px] font-black truncate">{cab.cliente || obra.customerName || 'Sin cliente'}</p>
            <p className="text-[11px] text-slate-300 truncate">
              {/* De qué cocina viene, siempre a la vista: el expediente es el
                  mismo pero la obra no, y confundirlas cuesta un pedido. */}
              <span className="text-slate-400">{obra._de || 'Cocina Montada'}</span>
              {' · '}{cab.proyecto || obra.budgetNumber || obra.id}
              {cab.referencia ? ` · ${cab.referencia}` : ''}
            </p>
          </div>
          <button
            type="button"
            onClick={() => cargarExpediente(obra.id, obra._origen)}
            className="shrink-0 min-h-[40px] min-w-[40px] flex items-center justify-center rounded-xl active:bg-white/10"
            aria-label="Actualizar el expediente"
          >
            <RefreshCw size={16} className={cargandoExp ? 'animate-spin' : ''} />
          </button>
          <BotonPantallaCompleta mostrarTexto={false} className="shrink-0 p-2 rounded-xl text-slate-300 active:bg-white/10" />
        </div>
      </div>

      <div className="flex-1 min-h-0 overflow-y-auto overflow-x-hidden p-3 space-y-3">
        {errorExp && (
          <div className="flex items-start gap-2 p-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-[13px]">
            <AlertTriangle size={16} className="shrink-0 mt-0.5" />
            <span className="min-w-0 break-words">{errorExp}</span>
          </div>
        )}

        {cargandoExp && !exp && (
          <div className="flex items-center justify-center py-10 text-slate-400">
            <Loader size={22} className="animate-spin" />
          </div>
        )}

        {exp && (
          <>
            <TiraDeEtapas etapas={exp.etapas} actual={exp.etapaActual} />

            {/* Lo primero de todo: ¿se puede bajar al taller o no? */}
            <div className={`p-3 rounded-2xl border flex items-start gap-2 min-w-0 ${
              exp.puedeLiberar ? 'bg-emerald-50 border-emerald-200' : 'bg-red-50 border-red-200'
            }`}>
              {exp.puedeLiberar
                ? <CheckCircle2 size={18} className="shrink-0 mt-0.5 text-emerald-600" />
                : <ShieldCheck size={18} className="shrink-0 mt-0.5 text-red-600" />}
              <div className="min-w-0">
                <p className={`text-[14px] font-black ${exp.puedeLiberar ? 'text-emerald-800' : 'text-red-800'}`}>
                  {exp.puedeLiberar ? 'Listo para bajar al taller' : `${bloqueos} bloqueo(s) sin resolver`}
                </p>
                <p className="text-[12px] text-slate-600 break-words">
                  {exp.lineas} línea(s) de presupuesto · etapa {exp.etapaActual}
                </p>
              </div>
            </div>

            {/* Importes: solo si han llegado. No se pintan a cero ni tapados. */}
            {importes.length > 0 && (
              <div className="p-3 rounded-2xl bg-white border border-slate-200 min-w-0">
                <p className="flex items-center gap-1.5 text-[11px] font-black uppercase tracking-wide text-slate-500 mb-2">
                  <Euro size={12} /> Importes
                </p>
                <div className="grid grid-cols-2 gap-2">
                  {importes.map((i) => (
                    <div key={i.clave} className="min-w-0">
                      <p className="text-[10px] uppercase font-bold text-slate-400 truncate">{i.etiqueta}</p>
                      <p className="text-[15px] font-black text-slate-900 truncate">{i.texto}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="min-w-0">
              <p className="text-[11px] font-black uppercase tracking-wide text-slate-500 mb-2">
                {acciones.length ? `Pendiente de resolver (${acciones.length})` : 'Pendiente de resolver'}
              </p>
              {acciones.length === 0 ? (
                <div className="p-3 rounded-2xl bg-emerald-50 border border-emerald-200 text-[13px] text-emerald-800">
                  No queda nada pendiente en este expediente.
                </div>
              ) : (
                <div className="space-y-2">
                  {acciones.map((a) => (
                    <Accion
                      key={a.clave}
                      accion={a}
                      onAprobar={aprobarCambio}
                      aprobando={aprobando === (a.donde || {}).indice}
                    />
                  ))}
                </div>
              )}
            </div>

            {/* LAS MEDIDAS DE LA OBRA. Aquí es donde se usa: de pie en la
                cocina, con el metro en una mano. */}
            <div className="min-w-0">
              <div className="flex items-center gap-1.5 mb-2">
                <Ruler size={13} className="text-slate-500" />
                <p className="text-[11px] font-black uppercase tracking-wide text-slate-500">
                  Medidas de la obra
                </p>
                {medidas && (
                  <span className={`ml-auto px-2 py-0.5 rounded-lg text-[10px] font-black uppercase ${
                    medidas.puedeFabricar ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'}`}>
                    {medidas.puedeFabricar ? 'Se puede cortar' : `${medidas.bloqueos.length} sin confirmar`}
                  </span>
                )}
              </div>

              {errorMedidas && (
                <p className="mb-2 p-2 rounded-xl bg-red-50 border border-red-200 text-[12px] text-red-700 break-words">
                  {errorMedidas}
                </p>
              )}

              {medidas && (
                <>
                  <p className="text-[12px] text-slate-600 mb-2 break-words">{medidas.resumen}</p>
                  <div className="space-y-2">
                    {medidas.medidas.map(m => (
                      <Medida key={m.clave} m={m} ocupada={ocupadaMedida}
                        onTomar={(clave, valor) => cambiarNivel('tomar', clave, valor)}
                        onConfirmar={(clave, valor) => cambiarNivel('confirmar', clave, valor)} />
                    ))}
                  </div>
                  <div className="mt-2">
                    <NuevaMedida onCrear={crearMedida} ocupada={ocupadaMedida} />
                  </div>
                </>
              )}
            </div>

            {/* Presupuestado contra fabricado. Bajo petición porque tira de la
                orden de fabricación y no siempre existe.

                Solo para Cocina Montada: una obra de Desmontada no pasa por
                orden de fabricación, así que el botón no se pinta en vez de
                pintarse y contestar siempre que no hay nada. */}
            <div className={`min-w-0 ${obra._origen === 'casco' ? 'hidden' : ''}`}>
              <button
                type="button"
                onClick={compararConFabrica}
                disabled={comparando}
                className="w-full min-h-[44px] rounded-xl border border-slate-300 bg-white text-slate-800 text-[13px] font-black uppercase tracking-wide active:bg-slate-100 disabled:opacity-50 flex items-center justify-center gap-2"
              >
                <Factory size={15} />
                {comparando ? 'Comparando…' : 'Comparar con fabricación'}
              </button>

              {errorComparacion && (
                <p className="mt-2 text-[12px] text-red-700 break-words">{errorComparacion}</p>
              )}

              {comparacion && !comparacion.hayOrden && (
                <p className="mt-2 p-3 rounded-2xl bg-slate-100 text-[13px] text-slate-600 break-words">
                  {comparacion.mensaje}
                </p>
              )}

              {comparacion && comparacion.hayOrden && (
                <ComparacionConFabrica comparacion={comparacion} />
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
