/*
 * © 2024-2026 ALEMAR FUTURE 07 SLU. Todos los derechos reservados. [ALEMAR-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Loader, RefreshCw, Search, Truck, Wallet } from 'lucide-react';
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
 * vale: para eso está Rentabilidad, con su puerta.
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
            {filas.map(p => <Fila key={p.pedidoId} p={p} />)}
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

function Fila({ p }) {
  const info = estadoDe(p.estado);
  const Icono = info.icon;
  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-3 sm:p-4">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
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
      </div>
    </div>
  );
}
