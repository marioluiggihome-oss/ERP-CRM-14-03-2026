/*
 * © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * EL ALMACÉN: qué hay, qué está apartado y qué hay que comprar.
 *
 * El cálculo estaba hecho y probado en el servidor (`services/almacen.py` y
 * `almacen_datos.py`) pero no había por dónde meter ni ver los datos, así que
 * no servía para nada. Esto es esa pantalla.
 *
 * LO QUE NO SE HACE AQUÍ
 * ----------------------
 * No se calcula NADA. Lo que hay que comprar lo dice el servidor; esta pantalla
 * lo enseña. Si se recalculara aquí «para ir más rápido» habría dos cuentas
 * distintas y un día darían resultados distintos.
 *
 * «NO SE SABE» NO ES CERO
 * -----------------------
 * Una referencia sin ficha llega con el stock a `null`. Se pinta «?» y sale en
 * su propia lista, no entre las cubiertas ni entre las que faltan. Un cero
 * dispara una compra que quizá sobra; un «no se sabe» manda a alguien a la
 * estantería, que es lo que toca.
 *
 * LO MÍO NO ME HACE COMPRAR DE MÁS
 * --------------------------------
 * Al mirar si a una cocina le falta material, resta lo que tienen apartado LOS
 * DEMÁS, no lo suyo. Eso lo resuelve el servidor; aquí solo hay que mandarle de
 * qué proyecto se está hablando — por eso el plan SIEMPRE va con un proyecto
 * delante y no hay forma de pedirlo «en general».
 */
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Boxes, Search, RefreshCw, Loader, AlertTriangle, Plus, Trash2, Save,
  ShoppingCart, HelpCircle, CheckCircle2, Bookmark,
} from 'lucide-react';
import { projectsAPI, proformaAPI, almacenAPI } from '../services/api';
import BotonPantallaCompleta from './BotonPantallaCompleta';

const PESTANAS = [
  { id: 'existencias', label: 'Existencias', icono: Boxes },
  { id: 'reservas', label: 'Reservas', icono: Bookmark },
  { id: 'plan', label: 'Plan de compra', icono: ShoppingCart },
];

const _ref = (v) => String(v || '').trim().toUpperCase();

/** Un número tal cual llega, y «?» cuando no se sabe.
 *
 * `null` y `0` NO se pintan igual: uno dice «ve a mirarlo» y el otro «no hay».
 * Confundirlos en pantalla es confundirlos en la cabeza de quien la mira.
 */
const num = (v) => (v === null || v === undefined || v === '' ? '?' : String(v));

const Aviso = ({ children, tono = 'rojo' }) => (
  <div className={`flex items-start gap-2 p-3 rounded-xl text-[13px] border min-w-0 ${
    tono === 'rojo' ? 'bg-red-50 border-red-200 text-red-700'
      : tono === 'ambar' ? 'bg-amber-50 border-amber-200 text-amber-800'
      : 'bg-slate-50 border-slate-200 text-slate-600'
  }`}>
    <AlertTriangle size={15} className="shrink-0 mt-0.5" />
    <span className="min-w-0 break-words">{children}</span>
  </div>
);


// ─── Existencias ────────────────────────────────────────────────────────────

const FilaFicha = ({ ficha, reservado, onGuardar, onBorrar }) => {
  const [f, setF] = useState({
    stock: ficha.stock ?? '', minimo: ficha.minimo ?? '', ubicacion: ficha.ubicacion || '',
  });
  const [guardando, setGuardando] = useState(false);
  const sucio = String(f.stock) !== String(ficha.stock ?? '')
    || String(f.minimo) !== String(ficha.minimo ?? '')
    || f.ubicacion !== (ficha.ubicacion || '');

  // Disponible = lo que hay menos lo apartado. Sin stock no se calcula: se
  // deja en «?» en vez de enseñar un número que no significa nada.
  const disp = ficha.stock === null || ficha.stock === undefined || ficha.stock === ''
    ? null : Number(ficha.stock) - (reservado || 0);
  const bajoMinimo = disp !== null && ficha.minimo != null && ficha.minimo !== ''
    && disp < Number(ficha.minimo);

  const guardar = async () => {
    setGuardando(true);
    try {
      // Vacío se manda como null a propósito: es «no se sabe», no cero.
      await onGuardar(ficha.referencia, {
        referencia: ficha.referencia,
        stock: f.stock === '' ? null : Number(f.stock),
        minimo: f.minimo === '' ? null : Number(f.minimo),
        ubicacion: f.ubicacion,
      });
    } finally { setGuardando(false); }
  };

  return (
    <div className={`p-3 rounded-2xl border min-w-0 ${bajoMinimo ? 'bg-amber-50 border-amber-300' : 'bg-white border-slate-200'}`}>
      <div className="flex items-center gap-2 min-w-0">
        <p className="text-[14px] font-black text-slate-900 font-mono truncate flex-1">{ficha.referencia}</p>
        {bajoMinimo && (
          <span className="shrink-0 px-2 py-0.5 rounded-lg bg-amber-500 text-white text-[10px] font-black uppercase">
            Reponer
          </span>
        )}
        <button onClick={() => onBorrar(ficha.referencia)} className="shrink-0 p-2 text-slate-300 hover:text-red-500"
          aria-label={`Borrar la ficha ${ficha.referencia}`}>
          <Trash2 size={14} />
        </button>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mt-2">
        <label className="min-w-0">
          <span className="block text-[10px] uppercase font-bold text-slate-400">Stock</span>
          <input type="number" step="any" value={f.stock}
            onChange={e => setF(p => ({ ...p, stock: e.target.value }))}
            placeholder="no se sabe"
            className="w-full min-h-[40px] px-2 rounded-xl border border-slate-300 text-[14px]" />
        </label>
        <label className="min-w-0">
          <span className="block text-[10px] uppercase font-bold text-slate-400">Mínimo</span>
          <input type="number" step="any" value={f.minimo}
            onChange={e => setF(p => ({ ...p, minimo: e.target.value }))}
            placeholder="sin mínimo"
            title="Sin mínimo no se avisa de reposición: un aviso inventado se aprende a ignorar."
            className="w-full min-h-[40px] px-2 rounded-xl border border-slate-300 text-[14px]" />
        </label>
        <label className="min-w-0 col-span-2">
          <span className="block text-[10px] uppercase font-bold text-slate-400">Dónde está</span>
          <input value={f.ubicacion}
            onChange={e => setF(p => ({ ...p, ubicacion: e.target.value }))}
            placeholder="Estantería A3"
            className="w-full min-h-[40px] px-2 rounded-xl border border-slate-300 text-[14px]" />
        </label>
      </div>

      <div className="flex items-center gap-2 flex-wrap mt-2">
        <span className="text-[11px] text-slate-500">
          Apartado: <b>{reservado || 0}</b> · Disponible: <b>{disp === null ? '?' : disp}</b>
        </span>
        {sucio && (
          <button onClick={guardar} disabled={guardando}
            className="ml-auto min-h-[40px] px-3 rounded-xl bg-slate-900 text-white text-[12px] font-black uppercase flex items-center gap-1.5 disabled:opacity-50">
            <Save size={13} /> {guardando ? 'Guardando…' : 'Guardar'}
          </button>
        )}
      </div>
    </div>
  );
};

const NuevaFicha = ({ onCrear }) => {
  const [ref, setRef] = useState('');
  const [stock, setStock] = useState('');
  const [creando, setCreando] = useState(false);

  const crear = async () => {
    if (!_ref(ref)) return;
    setCreando(true);
    try {
      await onCrear(_ref(ref), {
        referencia: _ref(ref),
        stock: stock === '' ? null : Number(stock),
        minimo: null, ubicacion: '',
      });
      setRef(''); setStock('');
    } finally { setCreando(false); }
  };

  return (
    <div className="p-3 rounded-2xl border-2 border-dashed border-slate-300 bg-white min-w-0">
      <div className="flex gap-2 flex-wrap">
        <input value={ref} onChange={e => setRef(e.target.value)} placeholder="Referencia nueva"
          className="flex-1 min-w-[140px] min-h-[44px] px-3 rounded-xl border border-slate-300 text-[14px] font-mono uppercase" />
        <input type="number" step="any" value={stock} onChange={e => setStock(e.target.value)}
          placeholder="stock"
          className="w-24 min-h-[44px] px-3 rounded-xl border border-slate-300 text-[14px]" />
        <button onClick={crear} disabled={!_ref(ref) || creando}
          className="min-h-[44px] px-4 rounded-xl bg-emerald-600 text-white text-[13px] font-black uppercase flex items-center gap-1.5 disabled:opacity-40">
          <Plus size={15} /> Dar de alta
        </button>
      </div>
    </div>
  );
};


// ─── Reservas ───────────────────────────────────────────────────────────────

const NuevaReserva = ({ onCrear }) => {
  const [r, setR] = useState({ referencia: '', proyecto: '', cantidad: '', motivo: '' });
  const [creando, setCreando] = useState(false);
  const listo = _ref(r.referencia) && _ref(r.proyecto) && Number(r.cantidad) > 0;

  const crear = async () => {
    if (!listo) return;
    setCreando(true);
    try {
      await onCrear({ ...r, referencia: _ref(r.referencia), proyecto: _ref(r.proyecto), cantidad: Number(r.cantidad) });
      setR({ referencia: '', proyecto: '', cantidad: '', motivo: '' });
    } finally { setCreando(false); }
  };

  return (
    <div className="p-3 rounded-2xl border-2 border-dashed border-slate-300 bg-white min-w-0 space-y-2">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        <input value={r.referencia} onChange={e => setR(p => ({ ...p, referencia: e.target.value }))}
          placeholder="Referencia"
          className="min-h-[44px] px-3 rounded-xl border border-slate-300 text-[14px] font-mono uppercase" />
        <input value={r.proyecto} onChange={e => setR(p => ({ ...p, proyecto: e.target.value }))}
          placeholder="Proyecto"
          className="min-h-[44px] px-3 rounded-xl border border-slate-300 text-[14px] uppercase" />
        <input type="number" step="any" value={r.cantidad} onChange={e => setR(p => ({ ...p, cantidad: e.target.value }))}
          placeholder="Cantidad"
          className="min-h-[44px] px-3 rounded-xl border border-slate-300 text-[14px]" />
        <input value={r.motivo} onChange={e => setR(p => ({ ...p, motivo: e.target.value }))}
          placeholder="Motivo (opcional)"
          className="min-h-[44px] px-3 rounded-xl border border-slate-300 text-[14px]" />
      </div>
      <button onClick={crear} disabled={!listo || creando}
        className="w-full sm:w-auto min-h-[44px] px-4 rounded-xl bg-emerald-600 text-white text-[13px] font-black uppercase flex items-center justify-center gap-1.5 disabled:opacity-40">
        <Plus size={15} /> Apartar material
      </button>
      {/* Apartar más de lo que hay NO se bloquea, y es a propósito: es un dato
          real (se ha comprometido y habrá que comprarlo) y el plan de compra lo
          va a decir. Bloquearlo escondería el problema en vez de enseñarlo. */}
      <p className="text-[11px] text-slate-500">
        Se puede apartar más de lo que hay: es un compromiso real y el plan de compra lo dirá.
      </p>
    </div>
  );
};


// ─── Plan de compra ─────────────────────────────────────────────────────────

const LineaPlan = ({ l, tono, pedido, onPedido, onApartar }) => (
  <div className={`p-3 rounded-2xl border min-w-0 ${
    tono === 'falta' ? 'bg-red-50 border-red-200'
      : tono === 'duda' ? 'bg-slate-100 border-slate-300' : 'bg-white border-slate-200'
  }`}>
    <div className="flex items-center gap-2 min-w-0">
      <p className="text-[14px] font-black font-mono text-slate-900 truncate flex-1">{l.referencia}</p>
      {tono === 'falta' && (
        <span className="shrink-0 px-2 py-0.5 rounded-lg bg-red-600 text-white text-[11px] font-black">
          Faltan {l.pendiente}
        </span>
      )}
      {tono === 'duda' && (
        <span className="shrink-0 px-2 py-0.5 rounded-lg bg-slate-600 text-white text-[10px] font-black uppercase">
          Sin dato
        </span>
      )}
    </div>
    <p className="text-[12px] text-slate-600 mt-1 break-words">
      Necesita <b>{num(l.necesario)}</b> · disponible <b>{num(l.disponible)}</b> · de camino <b>{num(l.pedido)}</b>
    </p>
    {l.motivo && <p className="text-[12px] text-slate-500 mt-0.5 break-words">{l.motivo}</p>}

    {tono === 'falta' && (
      <div className="flex items-center gap-2 flex-wrap mt-2">
        <label className="flex items-center gap-1.5 text-[11px] text-slate-500">
          Ya pedido
          <input type="number" step="any" value={pedido ?? ''} onChange={e => onPedido(e.target.value)}
            placeholder="0"
            title="Lo que ya viene de camino del proveedor: se descuenta de lo que falta."
            className="w-20 min-h-[36px] px-2 rounded-lg border border-slate-300 text-[13px]" />
        </label>
        <button onClick={() => onApartar(l.referencia, l.necesario)}
          className="ml-auto min-h-[36px] px-3 rounded-lg border border-slate-300 bg-white text-[12px] font-bold text-slate-700">
          Apartar para esta obra
        </button>
      </div>
    )}
  </div>
);


// ─── Pantalla ───────────────────────────────────────────────────────────────

export default function Almacen({ state }) {
  const usuarioId = state?.currentUser?.id;

  const [pestana, setPestana] = useState('existencias');
  const [fichas, setFichas] = useState([]);
  const [reservas, setReservas] = useState([]);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState('');
  const [busqueda, setBusqueda] = useState('');

  // Plan. Las obras vienen de los TRES presupuestadores: Cocina Montada 1 y 2
  // guardan en `projects`, y Cocina Desmontada en su propia colección de
  // proformas. Son la misma pregunta —«qué material necesita esta obra»— así
  // que aquí se eligen del mismo desplegable.
  const [proyectos, setProyectos] = useState([]);
  const [proformas, setProformas] = useState([]);
  const [pedidosCasco, setPedidosCasco] = useState([]);
  const [proyectoId, setProyectoId] = useState('');
  const [plan, setPlan] = useState(null);
  const [calculando, setCalculando] = useState(false);
  const [errorPlan, setErrorPlan] = useState('');
  const [pedidos, setPedidos] = useState({});
  const [lineasDelProyecto, setLineasDelProyecto] = useState(null);

  const cargar = useCallback(async () => {
    setCargando(true);
    setError('');
    try {
      const [s, r] = await Promise.all([almacenAPI.listarStock(), almacenAPI.listarReservas()]);
      setFichas(s.fichas || []);
      setReservas(r.reservas || []);
    } catch (e) {
      setError(e.message || 'No se pudo leer el almacén.');
    } finally { setCargando(false); }
  }, []);

  useEffect(() => { cargar(); }, [cargar]);

  useEffect(() => {
    projectsAPI.getAll(usuarioId)
      .then(d => setProyectos(Array.isArray(d) ? d : (d?.projects || [])))
      .catch(() => { /* el plan avisa por su cuenta si no hay proyectos */ });
    // Las proformas son solo del master. Si no lo es, el servidor contesta que
    // no y esta lista se queda vacía: no es un error que haya que enseñar.
    proformaAPI.listar()
      .then(d => setProformas(d?.proyectos || []))
      .catch(() => setProformas([]));
    proformaAPI.listarPedidos(usuarioId)
      .then(d => setPedidosCasco(d?.orders || []))
      .catch(() => setPedidosCasco([]));
  }, [usuarioId]);

  // Lo apartado por referencia, sumando TODOS los proyectos. En la lista de
  // existencias esto es lo correcto: nadie está preguntando por una obra
  // concreta todavía. En el plan sí, y ahí lo separa el servidor.
  const reservadoPorRef = useMemo(() => {
    const m = {};
    for (const r of reservas) {
      const k = _ref(r.referencia);
      m[k] = (m[k] || 0) + (Number(r.cantidad) || 0);
    }
    return m;
  }, [reservas]);

  const guardarFicha = useCallback(async (referencia, ficha) => {
    try {
      await almacenAPI.guardarStock(referencia, ficha);
      await cargar();
    } catch (e) { setError(e.message || 'No se pudo guardar la ficha.'); }
  }, [cargar]);

  const borrarFicha = useCallback(async (referencia) => {
    try {
      await almacenAPI.borrarStock(referencia);
      await cargar();
    } catch (e) { setError(e.message || 'No se pudo borrar la ficha.'); }
  }, [cargar]);

  const crearReserva = useCallback(async (reserva) => {
    try {
      await almacenAPI.crearReserva(reserva);
      await cargar();
    } catch (e) { setError(e.message || 'No se pudo apartar el material.'); }
  }, [cargar]);

  const borrarReserva = useCallback(async (referencia, proyecto) => {
    try {
      await almacenAPI.borrarReserva(referencia, proyecto);
      await cargar();
    } catch (e) { setError(e.message || 'No se pudo soltar la reserva.'); }
  }, [cargar]);

  // El plan necesita las líneas del proyecto. Salen del propio presupuesto —
  // los dos juegos de líneas, montada y desmontada— sin tocarlas: el servidor
  // ya sabe sumar las referencias repetidas.
  // El valor del desplegable lleva de dónde sale la obra: `proj:` de Cocina
  // Montada 1 y 2, `prof:` de Cocina Desmontada. Sin el prefijo habría que
  // adivinarlo por el id, y dos obras de módulos distintos pueden llamarse
  // igual.
  const calcularPlan = useCallback(async (valor, pedidosActuales) => {
    if (!valor) return;
    const [origen, id] = valor.split(':');
    setCalculando(true);
    setErrorPlan('');
    setPlan(null);
    try {
      let lineas = [];
      let referencia = id;

      if (origen === 'prof') {
        // Cocina Desmontada: las líneas son las de la proforma, quitando las
        // borradas y las desmarcadas en pantalla. Si se mandaran todas, el
        // plan pediría material que alguien ya había decidido no pedir.
        const d = await proformaAPI.get(id);
        const p = d?.proyecto || {};
        const fuera = new Set([
          ...(p.deletedRows || []).map(Number),
          ...Object.keys(p.excluidas || {}).filter(k => p.excluidas[k]).map(Number),
        ]);
        lineas = (p.items || []).filter((_, i) => !fuera.has(i));
        referencia = p.nombre || id;
      } else if (origen === 'casco') {
        // COCINA DESMONTADA no tiene código de proveedor por línea: lo que
        // identifica un casco es su FIRMA —módulo + acabado—, que es la misma
        // por la que la pantalla junta dos líneas iguales en el carro. Para el
        // almacén eso es exactamente lo que hace falta: dos cascos con la
        // misma firma son la misma pieza en la estantería.
        //
        // Va escrito aquí y no metido en el lector general de líneas a
        // propósito: la firma NO es un código de tarifa, y colarla como tal
        // haría que la validación técnica diera por buenas líneas que no
        // tienen código de verdad.
        const pedido = pedidosCasco.find(o => o.id === id) || {};
        lineas = (pedido.lines || []).map(l => ({
          referencia: l.sig || '',
          cantidad: l.qty,
          descripcion: [l.tipo, l.ancho, l.colorLabel].filter(Boolean).join(' '),
        }));
        referencia = pedido.expediente || pedido.ref || pedido.cliente || id;
      } else {
        const proy = proyectos.find(p => p.id === id);
        const detalle = await projectsAPI.getById(id).catch(() => proy || {});
        lineas = [...(detalle.itemsMontada || []), ...(detalle.itemsDespiece || [])];
        referencia = detalle.budgetNumber || detalle.id || id;
      }

      setLineasDelProyecto(lineas.length);
      const r = await almacenAPI.plan(referencia, lineas, pedidosActuales || null);
      setPlan({ ...r, proyecto: referencia });
    } catch (e) {
      setErrorPlan(e.message || 'No se pudo calcular el plan de compra.');
    } finally { setCalculando(false); }
  }, [proyectos, pedidosCasco]);

  const apartarDelPlan = useCallback(async (referencia, cantidad) => {
    if (!plan?.proyecto) return;
    await crearReserva({ referencia, proyecto: plan.proyecto, cantidad, motivo: 'Desde el plan de compra' });
    await calcularPlan(proyectoId, pedidos);
  }, [plan, crearReserva, calcularPlan, proyectoId, pedidos]);

  const fichasFiltradas = useMemo(() => {
    const q = busqueda.trim().toLowerCase();
    const l = [...fichas].sort((a, b) => String(a.referencia).localeCompare(String(b.referencia)));
    if (!q) return l;
    return l.filter(f => `${f.referencia} ${f.ubicacion || ''}`.toLowerCase().includes(q));
  }, [fichas, busqueda]);

  const reservasFiltradas = useMemo(() => {
    const q = busqueda.trim().toLowerCase();
    const l = [...reservas].sort((a, b) => String(a.proyecto).localeCompare(String(b.proyecto)));
    if (!q) return l;
    return l.filter(r => `${r.referencia} ${r.proyecto} ${r.motivo || ''}`.toLowerCase().includes(q));
  }, [reservas, busqueda]);

  return (
    <div className="h-full flex flex-col bg-slate-50 min-w-0">
      <div className="hueco-logo shrink-0 px-3 py-2 bg-slate-900 text-white flex items-center gap-2 min-w-0">
        <Boxes size={18} className="shrink-0" />
        <h1 className="text-[14px] font-black uppercase tracking-wide truncate">Almacén</h1>
        <button onClick={cargar}
          className="ml-auto shrink-0 min-h-[40px] min-w-[40px] flex items-center justify-center rounded-xl active:bg-white/10"
          aria-label="Recargar">
          <RefreshCw size={16} className={cargando ? 'animate-spin' : ''} />
        </button>
        {/* En el almacén se anda con la tablet en la mano entre estanterías:
            cada línea de pantalla que se recupera cuenta. */}
        <BotonPantallaCompleta mostrarTexto={false}
          className="shrink-0 p-2 rounded-xl text-slate-300 active:bg-white/10" />
      </div>

      <div className="shrink-0 flex gap-1 px-2 pt-2 bg-white border-b border-slate-200 overflow-x-auto">
        {PESTANAS.map(t => {
          const Icono = t.icono;
          return (
            <button key={t.id} onClick={() => setPestana(t.id)}
              className={`shrink-0 min-h-[44px] px-3 rounded-t-xl text-[13px] font-black uppercase tracking-wide flex items-center gap-1.5 ${
                pestana === t.id ? 'bg-slate-900 text-white' : 'text-slate-500 hover:bg-slate-100'
              }`}>
              <Icono size={14} /> {t.label}
            </button>
          );
        })}
      </div>

      <div className="flex-1 min-h-0 overflow-y-auto overflow-x-hidden p-3 space-y-3">
        {error && <Aviso>{error}</Aviso>}

        {pestana !== 'plan' && (
          <div className="relative">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input value={busqueda} onChange={e => setBusqueda(e.target.value)}
              placeholder={pestana === 'existencias' ? 'Referencia o sitio' : 'Referencia, proyecto o motivo'}
              className="w-full min-h-[44px] pl-9 pr-3 rounded-xl border border-slate-300 text-[14px]" />
          </div>
        )}

        {/* ── Existencias ── */}
        {pestana === 'existencias' && (
          <>
            <NuevaFicha onCrear={guardarFicha} />
            {cargando && !fichas.length && (
              <div className="flex justify-center py-8 text-slate-400"><Loader size={22} className="animate-spin" /></div>
            )}
            {!cargando && !fichasFiltradas.length && (
              <p className="text-center text-[13px] text-slate-500 py-8">
                No hay ninguna referencia dada de alta todavía.
              </p>
            )}
            {fichasFiltradas.map(f => (
              <FilaFicha key={f.referencia} ficha={f} reservado={reservadoPorRef[_ref(f.referencia)] || 0}
                onGuardar={guardarFicha} onBorrar={borrarFicha} />
            ))}
          </>
        )}

        {/* ── Reservas ── */}
        {pestana === 'reservas' && (
          <>
            <NuevaReserva onCrear={crearReserva} />
            {!reservasFiltradas.length && (
              <p className="text-center text-[13px] text-slate-500 py-8">No hay nada apartado.</p>
            )}
            {reservasFiltradas.map(r => (
              <div key={`${r.referencia}|${r.proyecto}`} className="p-3 rounded-2xl bg-white border border-slate-200 min-w-0">
                <div className="flex items-center gap-2 min-w-0">
                  <div className="min-w-0 flex-1">
                    <p className="text-[14px] font-black font-mono text-slate-900 truncate">{r.referencia}</p>
                    <p className="text-[12px] text-slate-500 truncate">
                      {r.proyecto} · <b>{r.cantidad}</b>{r.motivo ? ` · ${r.motivo}` : ''}
                    </p>
                  </div>
                  <button onClick={() => borrarReserva(r.referencia, r.proyecto)}
                    className="shrink-0 p-2 text-slate-300 hover:text-red-500"
                    aria-label={`Soltar la reserva de ${r.referencia}`}>
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            ))}
          </>
        )}

        {/* ── Plan de compra ── */}
        {pestana === 'plan' && (
          <>
            <div className="p-3 rounded-2xl bg-white border border-slate-200 min-w-0 space-y-2">
              {/* El plan SIEMPRE va con un proyecto delante: sin saber de quién
                  es la obra no se puede distinguir lo apartado por los demás de
                  lo apartado por ella, que es lo único que hace que la cuenta
                  salga bien. */}
              <label className="block text-[11px] font-black uppercase tracking-wide text-slate-500">
                ¿Para qué obra?
              </label>
              <select value={proyectoId}
                onChange={e => { setProyectoId(e.target.value); setPlan(null); setPedidos({}); }}
                className="w-full min-h-[44px] px-3 rounded-xl border border-slate-300 text-[14px]">
                <option value="">— elige una obra —</option>
                <optgroup label="Cocina Montada (1 y 2)">
                  {proyectos.filter(p => (p.status || '') !== 'archived').map(p => (
                    <option key={p.id} value={`proj:${p.id}`}>
                      {p.budgetNumber || p.id} · {p.customerName || 'sin cliente'}
                    </option>
                  ))}
                </optgroup>
                {pedidosCasco.length > 0 && (
                  <optgroup label="Cocina Desmontada">
                    {pedidosCasco.map(o => (
                      <option key={o.id} value={`casco:${o.id}`}>
                        {o.expediente || o.ref || o.id} · {o.cliente || 'sin cliente'}
                      </option>
                    ))}
                  </optgroup>
                )}
                {proformas.length > 0 && (
                  <optgroup label="Proformas de proveedor">
                    {proformas.map(p => (
                      <option key={p.id} value={`prof:${p.id}`}>{p.nombre || p.id}</option>
                    ))}
                  </optgroup>
                )}
              </select>
              <button onClick={() => calcularPlan(proyectoId, pedidos)} disabled={!proyectoId || calculando}
                className="w-full min-h-[44px] rounded-xl bg-slate-900 text-white text-[13px] font-black uppercase tracking-wide disabled:opacity-40 flex items-center justify-center gap-2">
                <ShoppingCart size={15} /> {calculando ? 'Calculando…' : 'Qué hay que comprar'}
              </button>
            </div>

            {errorPlan && <Aviso>{errorPlan}</Aviso>}

            {plan && (
              <>
                <div className={`p-3 rounded-2xl border flex items-start gap-2 min-w-0 ${
                  plan.hayQueComprar ? 'bg-red-50 border-red-200' : 'bg-emerald-50 border-emerald-200'}`}>
                  {plan.hayQueComprar
                    ? <ShoppingCart size={18} className="shrink-0 mt-0.5 text-red-600" />
                    : <CheckCircle2 size={18} className="shrink-0 mt-0.5 text-emerald-600" />}
                  <div className="min-w-0">
                    <p className={`text-[14px] font-black ${plan.hayQueComprar ? 'text-red-800' : 'text-emerald-800'}`}>
                      {plan.resumen}
                    </p>
                    <p className="text-[12px] text-slate-600 break-words">
                      Obra {plan.proyecto}
                      {lineasDelProyecto != null ? ` · ${lineasDelProyecto} línea(s) de presupuesto` : ''}
                    </p>
                  </div>
                </div>

                {(plan.pendientes || []).map(l => (
                  <LineaPlan key={l.referencia} l={l} tono="falta"
                    pedido={pedidos[l.referencia]}
                    onPedido={(v) => setPedidos(p => ({ ...p, [l.referencia]: v === '' ? undefined : Number(v) }))}
                    onApartar={apartarDelPlan} />
                ))}

                {(plan.pendientes || []).length > 0 && (
                  <button onClick={() => calcularPlan(proyectoId, pedidos)}
                    className="w-full min-h-[44px] rounded-xl border border-slate-300 bg-white text-[13px] font-black uppercase text-slate-700">
                    Recalcular con lo que ya viene de camino
                  </button>
                )}

                {/* Sin dato de stock: NI cubiertas NI pendientes. Es un agujero
                    de información, y mezclarlo con cualquiera de las otras dos
                    listas daría por resuelto lo que ni se ha mirado. */}
                {(plan.sinDato || []).length > 0 && (
                  <>
                    <p className="text-[11px] font-black uppercase tracking-wide text-slate-500 flex items-center gap-1.5">
                      <HelpCircle size={12} /> Hay que ir a mirarlo ({plan.sinDato.length})
                    </p>
                    {plan.sinDato.map(l => <LineaPlan key={l.referencia} l={l} tono="duda" />)}
                  </>
                )}

                {(plan.sinFicha || []).length > 0 && (
                  <div className="p-3 rounded-2xl bg-white border border-slate-200 min-w-0">
                    <p className="text-[11px] font-black uppercase tracking-wide text-slate-500">
                      Sin ficha de almacén ({plan.sinFicha.length})
                    </p>
                    <p className="text-[12px] text-slate-500 mt-0.5">
                      Nadie las ha dado de alta todavía. No es lo mismo que estar a cero.
                    </p>
                    <div className="flex flex-wrap gap-1.5 mt-2">
                      {plan.sinFicha.map(ref => (
                        <button key={ref}
                          onClick={() => guardarFicha(ref, { referencia: ref, stock: null, minimo: null, ubicacion: '' })}
                          className="px-2 py-1 rounded-lg border border-slate-300 bg-white text-[11px] font-mono font-bold text-slate-700 hover:bg-slate-50"
                          title="Dar de alta esta referencia (sin stock: queda por mirar)">
                          + {ref}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {(plan.reposicion || []).length > 0 && (
                  <Aviso tono="ambar">
                    Por debajo del mínimo: {plan.reposicion.join(', ')}.
                  </Aviso>
                )}

                {plan.cubiertas > 0 && (
                  <p className="text-center text-[12px] text-emerald-700 font-bold py-2">
                    {plan.cubiertas} referencia(s) cubiertas con lo que hay.
                  </p>
                )}
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
}
