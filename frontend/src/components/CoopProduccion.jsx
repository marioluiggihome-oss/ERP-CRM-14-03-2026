/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { AlertTriangle, ChevronDown, ChevronRight, CircleDollarSign, Loader, Package, RefreshCw, Search, Trash2, Truck, Wallet } from 'lucide-react';
import { authHeaders } from '../services/api';

const API_URL = process.env.REACT_APP_BACKEND_URL || '';
import { ESTADOS_FABRICACION, estadoDe } from '../estadosFabricacion';

/**
 * POR DÓNDE VA CADA PEDIDO EN FÁBRICA.
 *
 * El master, 30/08: «los pedidos y el estado de los mismos en fábrica, vamos
 * los procesos de producción y su estado».
 *
 * EL ESTADO NO SE INVENTA AQUÍ: lo manda el servidor a partir de
 * `fabrica_orders`, la colección que ya lleva el taller. Esta pantalla solo lo
 * pinta — si un día el taller cambia de estados, cambian en un sitio.
 *
 * LO MÁS ATRASADO, PRIMERO. Es lo que hay que empujar; una lista por fecha
 * enseña lo último que entró, que es lo que menos corre prisa.
 *
 * SIN IMPORTES, a propósito. Aquí se mira por dónde va una cocina, no lo que
 * vale: para eso está Rentabilidad, con su puerta. Vale igual para el detalle:
 * al abrir un pedido salen sus códigos y sus unidades, y ni un euro.
 */
export default function CoopProduccion() {
  const [datos, setDatos] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState('');
  const [busca, setBusca] = useState('');
  const [filtro, setFiltro] = useState('');

  const cargar = useCallback(async () => {
    setCargando(true); setError('');
    try {
      const r = await fetch(`${API_URL}/api/cooperativistas/produccion`, { headers: authHeaders() });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(d.detail || 'No se pudo leer la producción.');
      setDatos(d);
    } catch (e) {
      setError(e.message);
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => { cargar(); }, [cargar]);

  const filas = useMemo(() => {
    const t = busca.trim().toLowerCase();
    return (datos?.pedidos || []).filter(p =>
      (!filtro || p.estado === filtro)
      && (!t || `${p.cliente} ${p.referencia}`.toLowerCase().includes(t)));
  }, [datos, busca, filtro]);

  if (cargando) {
    return (
      <div className="h-full flex items-center justify-center text-dato-500">
        <Loader className="animate-spin mr-2" size={18} /> Cargando la producción…
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 sm:p-6">
        <div className="rounded-2xl border border-error-200 bg-error-50/60 p-5">
          <p className="font-bold text-error-800 text-sm">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto p-3 sm:p-6">
      <div className="max-w-6xl mx-auto space-y-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <h2 className="text-lg font-black text-dato-900">Producción</h2>
            <p className="text-[13px] text-dato-500">
              Por dónde va cada pedido de la cooperativa. El estado lo lleva la fábrica.
            </p>
          </div>
          <button
            onClick={cargar}
            className="shrink-0 p-2 rounded-xl border border-slate-200 bg-white hover:bg-slate-100"
            title="Recargar" aria-label="Recargar la producción"
          >
            <RefreshCw size={16} className="text-dato-600" />
          </button>
        </div>

        {/* CUÁNTOS HAY EN CADA ESTADO, en orden de proceso. Es la foto de un
            vistazo, y además sirve de filtro: se pulsa y se ve solo eso. */}
        <div className="flex flex-wrap gap-2">
          <Contador activo={!filtro} onClick={() => setFiltro('')}
            nombre="Todos" n={datos?.resumen?.total || 0} />
          {(datos?.resumen?.porEstado || []).map(e => (
            <Contador key={e.estado} activo={filtro === e.estado}
              onClick={() => setFiltro(filtro === e.estado ? '' : e.estado)}
              nombre={e.nombre} n={e.pedidos} clave={e.estado} />
          ))}
        </div>

        {!!datos?.sinFichaEnFabrica && (
          <p className="text-[11px] text-dato-500">
            {datos.sinFichaEnFabrica} pedido{datos.sinFichaEnFabrica === 1 ? '' : 's'} sin
            ficha en fábrica: están vendidos y aún no han entrado en el taller.
          </p>
        )}

        <div className="relative">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-dato-400" />
          <input
            value={busca} onChange={(e) => setBusca(e.target.value)}
            placeholder="Cliente o referencia…"
            className="w-full pl-9 pr-3 py-2 rounded-xl border border-slate-200 text-sm outline-none focus:border-master-400"
          />
        </div>

        {filas.length === 0 ? (
          <p className="text-sm text-dato-500 py-8 text-center">
            No hay pedidos que coincidan.
          </p>
        ) : (
          <div className="space-y-2">
            {filas.map(p => <Fila key={p.pedidoId} p={p} alBorrar={cargar} />)}
          </div>
        )}
      </div>
    </div>
  );
}

function Contador({ nombre, n, activo, onClick, clave }) {
  const tono = clave ? estadoDe(clave).color : 'bg-dato-100 text-dato-700';
  return (
    <button
      onClick={onClick}
      className={`px-3 py-1.5 rounded-xl text-xs font-black whitespace-nowrap border transition-colors ${
        activo ? 'border-master-400 ring-1 ring-master-300' : 'border-transparent'} ${tono}`}
      data-testid={`produccion-filtro-${clave || 'todos'}`}
    >
      {nombre} · {n}
    </button>
  );
}

function Fila({ p, alBorrar }) {
  const info = estadoDe(p.estado);
  const Icono = info.icon;
  // ABIERTO / CERRADO, y el contenido SE PIDE AL ABRIR, no antes: con cien
  // pedidos en la lista, traerse las líneas de todos de golpe es una llamada
  // enorme para mirar uno.
  const [abierto, setAbierto] = useState(false);
  const [detalle, setDetalle] = useState(null);
  const [cargando, setCargando] = useState(false);
  const [fallo, setFallo] = useState('');

  const abrir = async () => {
    const va = !abierto;
    setAbierto(va);
    if (!va || detalle || cargando) return;
    setCargando(true); setFallo('');
    try {
      const r = await fetch(
        `${API_URL}/api/cooperativistas/produccion/${encodeURIComponent(p.pedidoId)}`,
        { headers: authHeaders() });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(d.detail || 'No se pudo leer el pedido.');
      setDetalle(d.pedido || null);
    } catch (e) {
      setFallo(e.message);
    } finally {
      setCargando(false);
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200">
      <button
        onClick={abrir}
        className="w-full text-left p-3 sm:p-4 hover:bg-slate-50 rounded-2xl transition-colors"
        data-testid={`produccion-pedido-${p.pedidoId}`}
        aria-expanded={abierto}
      >
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div className="min-w-0 flex-1 flex items-start gap-2">
            <span className="shrink-0 mt-0.5 text-dato-400">
              {abierto ? <ChevronDown size={15} /> : <ChevronRight size={15} />}
            </span>
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
                <span className="font-black text-dato-900 text-sm truncate">
                  {p.cliente || 'Sin cliente'}
                </span>
                {!!p.referencia && (
                  <span className="text-xs text-dato-500">· {p.referencia}</span>
                )}
              </div>
              <p className="text-[11px] text-dato-400 mt-0.5">{p.origen}</p>
            </div>
          </div>
          <span className={`shrink-0 px-2.5 py-1 rounded-lg text-[11px] font-black flex items-center gap-1.5 ${info.color}`}>
            <Icono size={13} /> {p.estadoNombre}
          </span>
        </div>

        {/* El progreso solo si la fábrica lo da. Una barra a 0 en un pedido que
            ni ha entrado al taller parece que va mal, y no va de ninguna manera. */}
        {p.progreso > 0 && (
          <div className="mt-2 h-1.5 rounded-full bg-slate-100 overflow-hidden">
            <div className="h-full bg-master-500 rounded-full" style={{ width: `${p.progreso}%` }} />
          </div>
        )}

        {/* EL FINAL DEL PROCESO. «Entregado» en fábrica no quiere decir cobrado, y
            esa diferencia es justo la que decide si una comisión se libera. */}
        <div className="flex flex-wrap gap-3 mt-2 text-[11px]">
          <span className={`flex items-center gap-1 ${p.servido ? 'text-ok-700 font-bold' : 'text-dato-400'}`}>
            <Truck size={12} /> {p.servido ? 'Servido' : 'Sin servir'}
          </span>
          <span className={`flex items-center gap-1 ${p.cobrado ? 'text-ok-700 font-bold' : 'text-dato-400'}`}>
            <Wallet size={12} /> {p.cobrado ? 'Cobrado' : 'Sin cobrar'}
          </span>
          {/* LA SEÑAL DEL 50 % (master, 30/08: «50% al confirmar pedido,
              siempre»). Se enseña el importe porque «falta la señal» sin la
              cifra obliga a ir a buscarla a Rentabilidad. */}
          {!!p.senal && (
            <span className={`flex items-center gap-1 ${
              p.senalCubierta ? 'text-ok-700 font-bold' : 'text-aviso-700 font-bold'}`}>
              <CircleDollarSign size={12} />
              {p.senalCubierta
                ? 'Señal cobrada'
                : `Falta la señal (${p.senal.toLocaleString('es-ES', { minimumFractionDigits: 2 })} €)`}
            </span>
          )}
          {!p.cobradoDelTodo && p.pendiente > 0 && (
            <span className="flex items-center gap-1 text-dato-500">
              Pendiente {p.pendiente.toLocaleString('es-ES', { minimumFractionDigits: 2 })} €
            </span>
          )}
        </div>

        {/* LO QUE NO CUADRA CON EL ORDEN QUE PIDIÓ EL MASTER. Avisa, no bloquea:
            en una obra pasan cosas, y un ERP que impide lo que la realidad ya ha
            hecho se acaba esquivando por fuera. */}
        {!!p.avisos?.length && (
          <div className="mt-2 flex flex-col gap-1">
            {p.avisos.map(a => (
              <span key={a.clave}
                className="flex items-start gap-1.5 text-[11px] font-bold text-aviso-800 bg-aviso-50 border border-aviso-200 rounded-lg px-2 py-1">
                <AlertTriangle size={12} className="shrink-0 mt-0.5" /> {a.texto}
              </span>
            ))}
          </div>
        )}
      </button>

      {abierto && (
        <div className="border-t border-slate-100 px-3 sm:px-4 py-3">
          {cargando && (
            <p className="text-xs text-dato-500 flex items-center gap-2">
              <Loader className="animate-spin" size={14} /> Leyendo el pedido…
            </p>
          )}
          {!!fallo && <p className="text-xs font-bold text-error-700">{fallo}</p>}
          {!cargando && !fallo && detalle && <Contenido d={detalle} />}
          {/* BORRAR VA AQUÍ DENTRO, no en la fila. Hay que abrir el pedido y
              ver lo que lleva antes de poder tirarlo: un botón de borrar en la
              lista se pulsa sin querer, y estos pedidos son los que pagan. */}
          {!cargando && !fallo && detalle && (
            <div className="mt-3 pt-3 border-t border-slate-100 flex justify-end">
              <Borrar pedidoId={p.pedidoId} referencia={p.referencia}
                cliente={p.cliente} alBorrar={alBorrar} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * QUÉ LLEVA EL PEDIDO. Códigos, descripción y unidades — sin un solo euro, igual
 * que la lista: aquí se mira qué cocina hay que fabricar, no lo que vale.
 *
 * Los MUEBLES se cuentan aparte de las UNIDADES a propósito: son dos números
 * distintos y los dos hacen falta. Fábrica monta todas las unidades; la comisión
 * solo paga los muebles (master, 25/08: puertas, costados y líneas manuales de
 * servicios no llevan compensación). Ver «14 muebles» en un pedido de 20 líneas
 * sin poder ver por qué es lo que hace pensar que a uno le están quitando.
 */
function Contenido({ d }) {
  if (d.sinDesglose) {
    return (
      <p className="text-xs text-dato-500">
        Este pedido no guarda sus líneas, así que no se sabe qué lleva. No es
        «cero muebles»: es que no consta.
      </p>
    );
  }
  return (
    <div>
      <div className="flex flex-wrap gap-3 text-[11px] mb-2">
        <span className="flex items-center gap-1 font-black text-dato-700">
          <Package size={12} /> {d.lineas.length} línea{d.lineas.length === 1 ? '' : 's'}
        </span>
        <span className="text-dato-600">{d.unidades} unidades</span>
        <span className="text-dato-600">{d.muebles} muebles</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-[12px]">
          <thead>
            <tr className="text-left text-dato-400 uppercase text-[10px] tracking-widest">
              <th className="py-1 pr-3 font-black">Código</th>
              <th className="py-1 pr-3 font-black">Descripción</th>
              <th className="py-1 pr-3 font-black">Medidas</th>
              <th className="py-1 pr-3 font-black">Familia</th>
              <th className="py-1 text-right font-black">Uds.</th>
            </tr>
          </thead>
          <tbody>
            {d.lineas.map((l, i) => (
              <tr key={`${l.codigo}-${i}`} className="border-t border-slate-100">
                <td className="py-1 pr-3 font-bold text-dato-800 whitespace-nowrap">
                  {l.codigo || '—'}
                </td>
                <td className="py-1 pr-3 text-dato-600">
                  {l.descripcion || '—'}
                  {!!l.acabado && (
                    <span className="block text-[10px] text-dato-400">{l.acabado}</span>
                  )}
                </td>
                {/* Lo que se fabrica. Vacío es vacío: una cota que no consta no
                    se rellena con un número plausible. */}
                <td className="py-1 pr-3 text-dato-600 whitespace-nowrap tabular-nums">
                  {l.medidas || '—'}
                </td>
                <td className="py-1 pr-3 text-dato-500">
                  {l.familia || '—'}
                  {/* Lo que NO cuenta para la comisión, dicho: es la misma
                      función que la de la nómina, no una copia. */}
                  {!l.esMueble && (
                    <span className="ml-1 text-[10px] text-dato-400">(no cuenta)</span>
                  )}
                </td>
                <td className="py-1 text-right font-black text-dato-800">{l.unidades}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/**
 * BORRAR UN PEDIDO.
 *
 * El master, 30/08: «déjame borrar pedidos». Hace falta de verdad —probando se
 * crean pedidos que luego sobran—, pero no todos se pueden tirar.
 *
 * UN PEDIDO YA LIQUIDADO NO SE BORRA, y eso lo decide el SERVIDOR, no esta
 * pantalla: al cerrar el mes se guarda DENTRO del pedido lo que se pagó por él,
 * y ese dato es el justificante de esa nómina. Si el pedido desaparece, el mes
 * que ya se pagó deja de cuadrar y no queda ni rastro de por qué. Aquí solo se
 * enseña el motivo que devuelve el servidor: esconder el botón sería un cierre
 * de adorno, porque la API se puede llamar a mano (regla 8).
 */
function Borrar({ pedidoId, referencia, cliente, alBorrar }) {
  const [borrando, setBorrando] = useState(false);
  const [fallo, setFallo] = useState('');

  const borrar = async () => {
    // eslint-disable-next-line no-alert
    if (!window.confirm(
      `Vas a BORRAR el pedido de ${cliente || 'sin cliente'}`
      + `${referencia ? ` (${referencia})` : ''}.\n\n`
      + 'No se puede deshacer.\n\n¿Seguimos?')) return;
    setBorrando(true); setFallo('');
    try {
      const r = await fetch(`${API_URL}/api/cascos/orders/${encodeURIComponent(pedidoId)}`,
        { method: 'DELETE', headers: authHeaders() });
      if (!r.ok) {
        const d = await r.json().catch(() => ({}));
        throw new Error(d.detail || 'No se ha podido borrar el pedido.');
      }
      alBorrar?.();
    } catch (e) {
      setFallo(e.message);
      setBorrando(false);
    }
  };

  return (
    <div className="flex flex-col items-end gap-1.5">
      {!!fallo && (
        <p className="text-[11px] font-bold text-error-700 text-right max-w-md">{fallo}</p>
      )}
      <button
        onClick={borrar}
        disabled={borrando}
        className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-error-200 text-error-700 hover:bg-error-50 text-[11px] font-black transition-colors disabled:opacity-40"
        data-testid={`produccion-borrar-${pedidoId}`}
      >
        {borrando ? <Loader size={12} className="animate-spin" /> : <Trash2 size={12} />}
        Borrar pedido
      </button>
    </div>
  );
}
