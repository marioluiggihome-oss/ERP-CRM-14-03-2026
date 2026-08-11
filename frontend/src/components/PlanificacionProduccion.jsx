/*
 * © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * PlanificacionProduccion.jsx — Módulo Oficial de Planificación y Capacidad de Producción.
 * 
 * Funcionalidades:
 *   - Diagrama Gantt interactivo de órdenes de fabricación (Cocina Montada & Desmontada)
 *   - Control de carga y capacidad por estaciones de trabajo:
 *       1. Corte & Seccionado
 *       2. Mecanizado CNC
 *       3. Canteado PUR
 *       4. Ensamblado en Taller
 *       5. Control de Calidad & Embalaje
 *   - Detección en tiempo real de cuellos de botella y alertas de sobrecarga
 *   - Fechas estimadas de entrega dinámicas y asignación de operarios
 */
import React, { useState, useEffect, useMemo } from 'react';
import { 
  Factory, Calendar, Clock, AlertTriangle, CheckCircle2, 
  ChevronRight, Filter, Search, Plus, Play, Pause, Layers,
  Boxes, TrendingUp, Users, ArrowUpRight, ShieldCheck, RefreshCw
} from 'lucide-react';
import { getToken } from '../services/api';

const ESTACIONES = [
  { id: 'corte', nombre: '1. Corte & Seccionado', icon: '🪚', capacidadMax: 120, unidad: 'm²' },
  { id: 'cnc', nombre: '2. Mecanizado CNC', icon: '⚙️', capacidadMax: 85, unidad: 'módulos' },
  { id: 'canteado', nombre: '3. Canteado Láser/PUR', icon: '📏', capacidadMax: 600, unidad: 'ml' },
  { id: 'ensamblado', nombre: '4. Ensamblado Taller', icon: '🔨', capacidadMax: 45, unidad: 'módulos' },
  { id: 'embalaje', nombre: '5. Embalaje & Envío', icon: '📦', capacidadMax: 50, unidad: 'módulos' }
];

const PEDIDOS_DEMO = [
  {
    id: 'OF-2026-081',
    cliente: 'Promociones Canalejas Salamanca',
    ref: 'Vivienda Ático D',
    tipo: 'Cocina Montada 3',
    tarifa: 'T4 ZENIT',
    modulos: 18,
    m2Tablero: 42.5,
    mlCanteado: 145,
    estado: 'mecanizado',
    prioridad: 'ALTA',
    progreso: 45,
    fechaInicio: '2026-08-11',
    fechaEntrega: '2026-08-18',
    estaciones: {
      corte: { completado: true, fecha: '11/08 09:30', operario: 'Carlos M.' },
      cnc: { completado: false, enCurso: true, progreso: 60, operario: 'David R.' },
      canteado: { completado: false, pendiente: true },
      ensamblado: { completado: false, pendiente: true },
      embalaje: { completado: false, pendiente: true }
    }
  },
  {
    id: 'OF-2026-082',
    cliente: 'Estudio Álvarez-Quiñones',
    ref: 'Chalet Villares',
    tipo: 'Cocina Montada 3',
    tarifa: 'T2 Seda',
    modulos: 12,
    m2Tablero: 28.0,
    mlCanteado: 95,
    estado: 'corte',
    prioridad: 'NORMAL',
    progreso: 20,
    fechaInicio: '2026-08-11',
    fechaEntrega: '2026-08-20',
    estaciones: {
      corte: { completado: false, enCurso: true, progreso: 50, operario: 'Carlos M.' },
      cnc: { completado: false, pendiente: true },
      canteado: { completado: false, pendiente: true },
      ensamblado: { completado: false, pendiente: true },
      embalaje: { completado: false, pendiente: true }
    }
  },
  {
    id: 'OF-2026-083',
    cliente: 'Marmolería y Cocinas Zamora',
    ref: 'Edificio Plaza Mayor',
    tipo: 'Cocina Desmontada',
    tarifa: 'T1 Sincro',
    modulos: 24,
    m2Tablero: 58.0,
    mlCanteado: 190,
    estado: 'ensamblado',
    prioridad: 'URGENTE',
    progreso: 80,
    fechaInicio: '2026-08-09',
    fechaEntrega: '2026-08-14',
    estaciones: {
      corte: { completado: true, fecha: '09/08 11:00', operario: 'Carlos M.' },
      cnc: { completado: true, fecha: '10/08 14:00', operario: 'David R.' },
      canteado: { completado: true, fecha: '10/08 18:30', operario: 'Elena P.' },
      ensamblado: { completado: false, enCurso: true, progreso: 65, operario: 'Manuel T.' },
      embalaje: { completado: false, pendiente: true }
    }
  },
  {
    id: 'OF-2026-084',
    cliente: 'Construcciones Valladolid Norte',
    ref: 'Residencial Zaratán Bloque 2',
    tipo: 'Cocina Montada 3',
    tarifa: 'T5 FENIX',
    modulos: 15,
    m2Tablero: 36.0,
    mlCanteado: 120,
    estado: 'pendiente',
    prioridad: 'NORMAL',
    progreso: 0,
    fechaInicio: '2026-08-13',
    fechaEntrega: '2026-08-22',
    estaciones: {
      corte: { completado: false, pendiente: true },
      cnc: { completado: false, pendiente: true },
      canteado: { completado: false, pendiente: true },
      ensamblado: { completado: false, pendiente: true },
      embalaje: { completado: false, pendiente: true }
    }
  }
];

export default function PlanificacionProduccion({ currentUser }) {
  const [pedidos, setPedidos] = useState(() => {
    try {
      const guardados = JSON.parse(localStorage.getItem('ordenes_fabricacion_taller') || '[]');
      if (guardados && guardados.length > 0) {
        const idsGuardados = new Set(guardados.map(g => g.id));
        return [...guardados, ...PEDIDOS_DEMO.filter(d => !idsGuardados.has(d.id))];
      }
      return PEDIDOS_DEMO;
    } catch {
      return PEDIDOS_DEMO;
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem('ordenes_fabricacion_taller', JSON.stringify(pedidos));
    } catch (e) { console.error('Error guardando OFs:', e); }
  }, [pedidos]);

  const isAdmin = currentUser?.isAdmin === true || currentUser?.isGerente === true || currentUser?.canAccessMaster === true || currentUser?.role === 'admin';

  const eliminarOrden = (id) => {
    if (!window.confirm(`¿Seguro que deseas eliminar la Orden de Fabricación ${id}? Esta acción no se puede deshacer.`)) return;
    setPedidos(prev => {
      const next = prev.filter(x => x.id !== id);
      try { localStorage.setItem('ordenes_fabricacion_taller', JSON.stringify(next)); } catch {}
      return next;
    });
  };
  const [filtroOrigen, setFiltroOrigen] = useState('TODOS');
  const [filtroPrioridad, setFiltroPrioridad] = useState('TODOS');
  const [busqueda, setBusqueda] = useState('');

  const pedidosFiltrados = useMemo(() => {
    return pedidos.filter(p => {
      const orig = p.origen || (p.id.includes('EXT') ? 'EXTERNO' : 'INTERNO');
      const matchOrigen = filtroOrigen === 'TODOS' || orig === filtroOrigen;
      const matchPrioridad = filtroPrioridad === 'TODOS' || p.prioridad === filtroPrioridad;
      const matchBusqueda = !busqueda.trim() || 
        p.id.toLowerCase().includes(busqueda.toLowerCase()) ||
        p.cliente.toLowerCase().includes(busqueda.toLowerCase()) ||
        (p.casco && p.casco.toLowerCase().includes(busqueda.toLowerCase())) ||
        p.ref.toLowerCase().includes(busqueda.toLowerCase());
      return matchOrigen && matchPrioridad && matchBusqueda;
    });
  }, [pedidos, filtroOrigen, filtroPrioridad, busqueda]);

  const avanzarEstacion = (idPedido) => {
    setPedidos(prev => prev.map(p => {
      if (p.id !== idPedido) return p;
      let nextEstado = p.estado;
      let nextProgreso = p.progreso;
      const ests = { ...p.estaciones };

      if (p.estado === 'pendiente') {
        nextEstado = 'corte'; nextProgreso = 20;
        ests.corte = { completado: false, enCurso: true, progreso: 30, operario: 'Carlos M.' };
      } else if (p.estado === 'corte') {
        nextEstado = 'mecanizado'; nextProgreso = 40;
        ests.corte = { completado: true, fecha: 'Hoy' };
        ests.cnc = { completado: false, enCurso: true, progreso: 40, operario: 'David R.' };
      } else if (p.estado === 'mecanizado') {
        nextEstado = 'canteado'; nextProgreso = 60;
        ests.cnc = { completado: true, fecha: 'Hoy' };
        ests.canteado = { completado: false, enCurso: true, progreso: 50, operario: 'Elena P.' };
      } else if (p.estado === 'canteado') {
        nextEstado = 'ensamblado'; nextProgreso = 80;
        ests.canteado = { completado: true, fecha: 'Hoy' };
        ests.ensamblado = { completado: false, enCurso: true, progreso: 60, operario: 'Manuel T.' };
      } else if (p.estado === 'ensamblado') {
        nextEstado = 'embalaje'; nextProgreso = 95;
        ests.ensamblado = { completado: true, fecha: 'Hoy' };
        ests.embalaje = { completado: false, enCurso: true, progreso: 70, operario: 'Ana S.' };
      } else if (p.estado === 'embalaje') {
        nextEstado = 'listo'; nextProgreso = 100;
        ests.embalaje = { completado: true, fecha: 'Hoy' };
      }

      return { ...p, estado: nextEstado, progreso: nextProgreso, estaciones: ests };
    }));
  };

  return (
    <div className="absolute inset-0 overflow-y-auto bg-slate-100 p-4 sm:p-6 pb-36 space-y-5">
      
      {/* Cabecera Principal */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white rounded-3xl p-6 shadow-xl border border-slate-800 flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-indigo-600 border border-indigo-400/40 flex items-center justify-center shadow-lg shadow-indigo-600/30">
            <Factory size={26} className="text-white" />
          </div>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-black text-white tracking-tight">Planificación de Fabricación de Cascos</h1>
              <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/20 border border-emerald-400/30 text-emerald-300 text-xs font-black uppercase">
                {pedidos.length} Órdenes Activas
              </span>
            </div>
            <p className="text-sm text-indigo-200/80 font-medium">
              Control de órdenes de fabricación por casco por defecto y fechas de entrega
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="px-4 py-2 rounded-2xl bg-white/10 border border-white/10 text-xs font-bold flex items-center gap-2">
            <Calendar size={15} className="text-indigo-300" />
            <span>Semana Actual ({new Date().toLocaleDateString('es-ES')})</span>
          </div>
        </div>
      </div>

      {/* Filtros y Buscador de Órdenes */}
      <div className="bg-white rounded-3xl p-4 border border-slate-200 shadow-sm flex items-center justify-between gap-4 flex-wrap text-xs">
        <div className="flex items-center gap-2 flex-1 min-w-[260px]">
          <Search size={16} className="text-slate-400" />
          <input
            value={busqueda}
            onChange={e => setBusqueda(e.target.value)}
            placeholder="Buscar por código OF, cliente, casco o referencia…"
            className="w-full bg-transparent font-medium outline-none text-slate-800"
          />
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <span className="font-bold text-slate-400 uppercase text-[10px]">Origen Fabricación:</span>
            <select
              value={filtroOrigen}
              onChange={e => setFiltroOrigen(e.target.value)}
              className="px-3 py-1.5 rounded-xl border border-slate-200 bg-slate-50 font-bold text-slate-700 outline-none"
            >
              <option value="TODOS">Todas las Órdenes</option>
              <option value="INTERNO">🏠 Taller Propio (Interno)</option>
              <option value="EXTERNO">🚚 Proveedor Externo (Fuera)</option>
            </select>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="font-bold text-slate-400 uppercase text-[10px]">Prioridad:</span>
            <select
              value={filtroPrioridad}
              onChange={e => setFiltroPrioridad(e.target.value)}
              className="px-3 py-1.5 rounded-xl border border-slate-200 bg-slate-50 font-bold text-slate-700 outline-none"
            >
              <option value="TODOS">Todas</option>
              <option value="URGENTE">Urgente</option>
              <option value="ALTA">Alta</option>
              <option value="NORMAL">Normal</option>
            </select>
          </div>
        </div>
      </div>

      {/* Lista de Órdenes de Fabricación */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden divide-y divide-slate-100">
        <div className="px-6 py-4 bg-slate-50/70 flex items-center justify-between text-xs font-black uppercase text-slate-400">
          <span>Órdenes de Fabricación en Curso ({pedidosFiltrados.length})</span>
          <span>Acciones y Borrado (Admin)</span>
        </div>

        {pedidosFiltrados.map(p => (
          <div key={p.id} className="p-5 hover:bg-slate-50/80 transition-colors space-y-3">
            <div className="flex items-center justify-between gap-4 flex-wrap">
              <div className="flex items-center gap-3">
                <div className="font-mono font-black text-sm text-indigo-700 bg-indigo-50 border border-indigo-200 px-3 py-1 rounded-xl">
                  {p.id}
                </div>
                <div>
                  <h4 className="font-black text-sm text-slate-900">{p.cliente} · <span className="text-slate-600 font-medium">{p.ref}</span></h4>
                  <div className="flex items-center gap-2 mt-0.5 text-xs text-slate-500 flex-wrap">
                    <span className="font-bold text-indigo-600">{p.tipo}</span>
                    <span>•</span>
                    <span className="font-semibold text-slate-700">{p.tarifa}</span>
                    <span>•</span>
                    <span className="px-2 py-0.5 bg-slate-100 rounded-md font-bold text-slate-800">Casco: {p.casco || 'Grafito Antracita (19mm)'}</span>
                    <span>•</span>
                    <span className={`px-2 py-0.5 rounded-md font-black text-xs border ${
                      (p.origen === 'EXTERNO' || p.id.includes('EXT')) ? 'bg-purple-100 text-purple-900 border-purple-300' : 'bg-blue-100 text-blue-900 border-blue-300'
                    }`}>
                      {(p.origen === 'EXTERNO' || p.id.includes('EXT')) ? '🚚 Proveedor Fuera' : '🏠 Taller Propio'}
                    </span>
                    <span>•</span>
                    <span>{p.modulos} módulos</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <span className={`px-2.5 py-1 rounded-xl text-xs font-black uppercase border ${
                  p.prioridad === 'URGENTE' ? 'bg-rose-100 text-rose-800 border-rose-300 animate-pulse' :
                  p.prioridad === 'ALTA' ? 'bg-amber-100 text-amber-800 border-amber-300' :
                  'bg-slate-100 text-slate-700 border-slate-200'
                }`}>
                  {p.prioridad}
                </span>

                <div className="text-right text-xs">
                  <div className="text-slate-400 font-semibold text-[10px]">Entrega Prevista:</div>
                  <div className="font-black text-slate-800">{p.fechaEntrega}</div>
                </div>

                {isAdmin && (
                  <button
                    onClick={() => eliminarOrden(p.id)}
                    className="p-2 rounded-xl text-rose-500 hover:bg-rose-50 border border-rose-200 transition-all"
                    title="Eliminar Orden de Fabricación (Solo Administrador)"
                  >
                    <Trash2 size={16} />
                  </button>
                )}
              </div>
            </div>

            {/* Stepper Visual de Estaciones */}
            <div className="grid grid-cols-5 gap-2 pt-2">
              {ESTACIONES.map(est => {
                const infoEst = p.estaciones[est.id] || {};
                const isCurrent = p.estado === est.id;
                const isDone = infoEst.completado;

                return (
                  <div 
                    key={est.id} 
                    className={`p-2.5 rounded-2xl border transition-all text-xs ${
                      isDone ? 'bg-emerald-50/70 border-emerald-300 text-emerald-950' :
                      isCurrent ? 'bg-indigo-50 border-indigo-400 ring-2 ring-indigo-200 text-indigo-950 shadow-sm' :
                      'bg-slate-50/50 border-slate-200 text-slate-400 opacity-60'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-bold text-[11px] truncate">{est.nombre.split('. ')[1]}</span>
                      {isDone ? <CheckCircle2 size={14} className="text-emerald-600 shrink-0" /> :
                       isCurrent ? <Play size={12} className="text-indigo-600 shrink-0" fill="currentColor" /> :
                       <Clock size={12} className="text-slate-300 shrink-0" />}
                    </div>
                    <div className="text-[10px] font-medium text-slate-500 truncate">
                      {isDone ? `Completado (${infoEst.fecha || 'OK'})` :
                       isCurrent ? `${infoEst.operario || 'En proceso'} (${infoEst.progreso || 50}%)` :
                       'Pendiente'}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>

    </div>
  );
}
