/*
 * © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
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
  ChevronLeft, Factory, Euro, User, ArrowRight, ShieldCheck, XCircle,
} from 'lucide-react';
import { projectsAPI, expedienteAPI } from '../services/api';
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
                {p.budgetNumber || p.id}
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

  const cargarLista = useCallback(async () => {
    setCargandoLista(true);
    setErrorLista('');
    try {
      const data = await projectsAPI.getAll(usuarioId);
      setProyectos(Array.isArray(data) ? data : (data?.projects || []));
    } catch (e) {
      setErrorLista(e.message || 'No se pudo cargar la lista de obras.');
    } finally {
      setCargandoLista(false);
    }
  }, [usuarioId]);

  useEffect(() => { cargarLista(); }, [cargarLista]);

  const cargarExpediente = useCallback(async (projectId) => {
    setCargandoExp(true);
    setErrorExp('');
    try {
      const data = await expedienteAPI.get(projectId);
      setExp(data);
    } catch (e) {
      // Se deja `exp` como estaba y se dice qué ha fallado. Vaciarlo dejaría
      // la pantalla en blanco sin explicar por qué.
      setErrorExp(e.message || 'No se pudo abrir el expediente.');
    } finally {
      setCargandoExp(false);
    }
  }, []);

  const abrir = useCallback((p) => {
    setObra(p);
    setExp(null);
    setComparacion(null);
    setErrorComparacion('');
    cargarExpediente(p.id);
  }, [cargarExpediente]);

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
        <div className="shrink-0 flex items-center gap-2 px-3 py-2 bg-slate-900 text-white">
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
              {cab.proyecto || obra.budgetNumber || obra.id}
              {cab.referencia ? ` · ${cab.referencia}` : ''}
            </p>
          </div>
          <button
            type="button"
            onClick={() => cargarExpediente(obra.id)}
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

            {/* Presupuestado contra fabricado. Bajo petición porque tira de la
                orden de fabricación y no siempre existe. */}
            <div className="min-w-0">
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
