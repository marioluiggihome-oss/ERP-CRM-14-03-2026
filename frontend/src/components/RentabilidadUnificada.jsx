/*
 * © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
import React, { useState } from 'react';
import { Package, TrendingUp } from 'lucide-react';
import ProformaImporter from './ProformaImporter';
import RentabilidadMV from './RentabilidadMV';
import RelacionReview from './RelacionReview';
import { authHeaders } from '../services/api';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Módulo unificado de rentabilidad (solo master). Un selector Sistema: ALVIC / MV
// enruta al motor correspondiente. Mismo coste de fabricación, distinto sistema de
// venta. Los clientes NO lo ven (gateado a master en Cocina Desmontada).
export default function RentabilidadUnificada({ esMaster, sistemaInicial, valorPunto, onClose, onVolcarDesmontada, onVolcarMontada }) {
  const [sistema, setSistema] = useState(sistemaInicial === 'alvic' || sistemaInicial === 'mv' ? sistemaInicial : 'mv');
  const [relacionMV, setRelacionMV] = useState(null);
  if (!esMaster) return null;
  if (relacionMV) return (
    <RelacionReview
      muebles={relacionMV}
      apiUrl={API_URL}
      authHeaders={() => authHeaders()}
      onClose={() => setRelacionMV(null)}
      onConfirm={(muebles, contexto) => {
        onVolcarDesmontada?.(muebles, contexto);
        setRelacionMV(null);
      }}
      onExportDesmontada={(muebles, contexto) => {
        onVolcarDesmontada?.(muebles, contexto);
        setRelacionMV(null);
      }}
      onExportMontada={(muebles, contexto) => {
        onVolcarMontada?.(muebles, contexto);
        setRelacionMV(null);
      }}
    />
  );
  return (
    // Ocupa todo el alto que le dé el modal: la cabecera se queda fija arriba y
    // es la tabla la que se desplaza, no la ventana entera.
    <div className="flex flex-col h-full min-h-0">
      <div className="shrink-0 flex items-center gap-2 flex-wrap bg-slate-800 rounded-t-2xl px-4 py-2.5">
        <span className="text-[10px] font-black uppercase tracking-widest text-slate-300 bg-slate-700 px-2 py-0.5 rounded">Solo master</span>
        <span className="text-sm font-black text-white mr-2">Rentabilidad</span>
        <div className="inline-flex rounded-lg bg-slate-700 p-0.5">
          <button onClick={() => setSistema('mv')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-black ${sistema === 'mv' ? 'bg-emerald-500 text-white' : 'text-slate-300 hover:text-white'}`}>
            <TrendingUp size={14} /> MV
          </button>
          <button onClick={() => setSistema('alvic')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-black ${sistema === 'alvic' ? 'bg-amber-500 text-white' : 'text-slate-300 hover:text-white'}`}>
            <Package size={14} /> Alvic
          </button>
        </div>
        <span className="text-[11px] text-slate-400 ml-2 hidden sm:block">
          {sistema === 'mv' ? 'Códigos MV → margen (PVP puntos × 3,33)' : 'Proforma Alvic → coste ACB + puertas aparte'}
        </span>
        {onClose && (
          <button onClick={onClose} className="ml-auto text-slate-400 hover:text-white p-1 rounded" title="Cerrar">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M1 1l12 12M13 1L1 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/></svg>
          </button>
        )}
      </div>
      {/* La tabla es larga: tiene su propio scroll, para que la cabecera con el
          selector MV/Alvic no se pierda al bajar. Antes se limitaba con
          `max-h-[85vh]`; ahora ocupa todo el hueco que quede bajo la cabecera. */}
      <div className="flex-1 min-h-0 border-2 border-t-0 border-slate-700 rounded-b-2xl bg-white overflow-auto">
        {sistema === 'mv' ? <RentabilidadMV esMaster={true} /> : <ProformaImporter esMaster={true} valorPunto={valorPunto} onConvertirMV={setRelacionMV} />}
      </div>
    </div>
  );
}
