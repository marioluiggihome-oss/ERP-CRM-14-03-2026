import React, { useState } from 'react';
import { Package, TrendingUp } from 'lucide-react';
import ProformaImporter from './ProformaImporter';
import RentabilidadMV from './RentabilidadMV';

// Módulo unificado de rentabilidad (solo master). Un selector Sistema: ALVIC / MV
// enruta al motor correspondiente. Mismo coste de fabricación, distinto sistema de
// venta. Los clientes NO lo ven (gateado a master en Cocina Desmontada).
export default function RentabilidadUnificada({ esMaster, sistemaInicial }) {
  const [sistema, setSistema] = useState(sistemaInicial === 'alvic' || sistemaInicial === 'mv' ? sistemaInicial : 'mv');
  if (!esMaster) return null;
  return (
    <div className="mb-4">
      <div className="flex items-center gap-2 flex-wrap bg-slate-800 rounded-t-2xl px-4 py-2.5">
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
        <span className="text-[11px] text-slate-400 ml-auto hidden sm:block">
          {sistema === 'mv' ? 'Códigos MV → margen (PVP puntos × 3,33)' : 'Proforma Alvic → coste ACB + puertas aparte'}
        </span>
      </div>
      <div className="border-2 border-t-0 border-slate-700 rounded-b-2xl overflow-hidden">
        {sistema === 'mv' ? <RentabilidadMV esMaster={true} /> : <ProformaImporter esMaster={true} />}
      </div>
    </div>
  );
}
