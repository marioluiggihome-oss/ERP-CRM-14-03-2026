import React from 'react';
import { Palette, Box, Layers } from 'lucide-react';

/**
 * BudgetTotals - Sección de totales del presupuesto con IVA editable
 */
const BudgetTotals = ({ total, ivaRate, onIvaChange }) => {
  return (
    <div className="pt-4 mt-auto border-t-4 border-indigo-950 mb-4">
      <div className="flex flex-col gap-2">
        <div className="text-[9px] font-black text-indigo-400 uppercase tracking-widest">
          PRESUPUESTO TÉCNICO
        </div>
        
        {/* Caja de totales en HORIZONTAL - ANCHO COMPLETO */}
        <div className="bg-indigo-950 text-white rounded-xl shadow-lg w-full">
          <div className="flex w-full">
            {/* BRUTO LÍNEAS */}
            <div className="flex-1 px-4 py-3 border-r border-indigo-800/50">
              <div className="text-[7px] font-bold uppercase tracking-wide text-indigo-400">BRUTO LÍNEAS</div>
              <div className="text-sm font-black italic tracking-tight text-white">
                {total.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}€
              </div>
            </div>
            
            {/* BASE IMPONIBLE */}
            <div className="flex-1 px-4 py-3 border-r border-indigo-800/50">
              <div className="text-[7px] font-bold uppercase tracking-wide text-indigo-400">BASE IMPONIBLE</div>
              <div className="text-sm font-black italic tracking-tight text-white">
                {total.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}€
              </div>
            </div>
            
            {/* IVA EDITABLE */}
            <div className="flex-1 px-4 py-3 border-r border-indigo-800/50">
              <div className="flex items-center gap-1">
                <span className="text-[7px] font-bold uppercase tracking-wide text-indigo-400">IVA</span>
                <input 
                  type="number" 
                  min="0" 
                  max="100" 
                  value={ivaRate || 21}
                  onChange={e => onIvaChange(parseFloat(e.target.value) || 0)}
                  className="w-10 bg-indigo-800 border border-indigo-700 rounded px-1 py-0.5 text-xs font-black text-white text-center outline-none focus:border-orange-500 no-print"
                  data-testid="iva-rate-input"
                />
                <span className="print-only text-[7px] font-bold text-indigo-400">{ivaRate || 21}</span>
                <span className="text-[7px] font-bold text-indigo-400">%</span>
              </div>
              <div className="text-sm font-black italic tracking-tight text-white">
                {(total * (ivaRate || 21) / 100).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}€
              </div>
            </div>
            
            {/* TOTAL */}
            <div className="flex-1 px-4 py-3 bg-orange-600 rounded-r-xl">
              <div className="text-[7px] font-black uppercase tracking-wide text-orange-200">TOTAL PRESUPUESTO</div>
              <div className="text-lg font-black italic tracking-tight text-white text-right">
                {(total * (1 + (ivaRate || 21) / 100)).toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}€
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

/**
 * BudgetHeader - Cabecera de configuración del presupuesto (acabado, armazón, colores)
 */
const BudgetHeader = ({ 
  globalFinish, 
  carcassMaterialName, 
  sideColor,
  doorColorLow,
  doorColorHigh,
  doorColorColumns
}) => {
  return (
    <div className="bg-indigo-50/30 p-2 rounded-xl border border-indigo-100 mb-2 space-y-2">
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
        <div className="flex items-center gap-1.5">
          <div className="p-1 bg-indigo-950 text-white rounded-md"><Palette size={12}/></div>
          <div>
            <p className="text-[6px] font-black uppercase text-indigo-300 tracking-widest leading-none mb-0.5">ACABADO GLOBAL</p>
            <p className="text-[8px] font-black text-indigo-950 uppercase italic leading-none">{globalFinish}</p>
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="p-1 bg-orange-600 text-white rounded-md"><Box size={12}/></div>
          <div>
            <p className="text-[6px] font-black uppercase text-indigo-300 tracking-widest leading-none mb-0.5">MATERIAL ARMAZÓN</p>
            <p className="text-[8px] font-black text-indigo-950 uppercase italic leading-none">{carcassMaterialName}</p>
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="p-1 bg-indigo-700 text-white rounded-md"><Layers size={12}/></div>
          <div>
            <p className="text-[6px] font-black uppercase text-indigo-300 tracking-widest leading-none mb-0.5">COSTADOS / VISTOS</p>
            <p className="text-[8px] font-black text-indigo-950 uppercase italic leading-none">{sideColor || 'Igual a Frentes'}</p>
          </div>
        </div>
      </div>

      {(doorColorLow || doorColorHigh || doorColorColumns) && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2 pt-2 border-t border-indigo-100">
          {doorColorLow && (
            <DoorColorItem label="P. BAJOS" value={doorColorLow} />
          )}
          {doorColorHigh && (
            <DoorColorItem label="P. ALTOS" value={doorColorHigh} />
          )}
          {doorColorColumns && (
            <DoorColorItem label="P. COLUMNAS" value={doorColorColumns} />
          )}
        </div>
      )}
    </div>
  );
};

const DoorColorItem = ({ label, value }) => (
  <div className="flex items-center gap-1.5">
    <div className="w-3 h-3 rounded-full bg-indigo-400" />
    <div>
      <p className="text-[5px] font-black uppercase text-indigo-300 leading-none">{label}</p>
      <p className="text-[7px] font-black text-indigo-900 uppercase leading-none">{value}</p>
    </div>
  </div>
);

export { BudgetTotals, BudgetHeader };
export default BudgetTotals;
