import React from 'react';
import { ArrowLeft, Printer, FileText } from 'lucide-react';

const ManufacturingReport = ({ items, finish, carcassColor, state, catalogs, logo, distributorName, onBack }) => {
  
  const allProducts = catalogs
    .flatMap(c => c.products.map(p => ({ ...p, catalogId: c.id })));

  return (
    <div className="h-screen bg-slate-900 overflow-auto">
      <div className="sticky top-0 z-50 bg-slate-950 border-b border-white/10 px-8 py-4 flex justify-between items-center">
        <button
          onClick={onBack}
          className="flex items-center gap-2 px-4 py-2 bg-white/10 text-white rounded-xl font-black uppercase text-xs hover:bg-white/20 transition-all"
        >
          <ArrowLeft size={18} />
          Volver a Mesa
        </button>
        
        <h1 className="text-xl font-black text-white uppercase tracking-wider flex items-center gap-3">
          <FileText size={24} className="text-orange-500" />
          Informe Industrial de Fabricación
        </h1>

        <button
          onClick={() => window.print()}
          className="flex items-center gap-2 px-6 py-2 bg-orange-600 text-white rounded-xl font-black uppercase text-xs hover:bg-orange-700 transition-all shadow-xl"
        >
          <Printer size={18} />
          Imprimir
        </button>
      </div>

      <div className="max-w-7xl mx-auto p-12 bg-white my-8 rounded-2xl shadow-2xl">
        {/* Header */}
        <div className="border-b-4 border-indigo-950 pb-6 mb-8">
          <div className="flex justify-between items-start">
            <div>
              {logo ? (
                <img src={logo} alt="Logo" className="h-16 mb-4" />
              ) : (
                <div className="text-3xl font-black italic text-indigo-950 mb-2">LUIGGI HOME</div>
              )}
              <p className="text-sm font-black text-indigo-400 uppercase">{distributorName}</p>
            </div>
            <div className="text-right">
              <h1 className="text-3xl font-black uppercase text-indigo-950 tracking-tight mb-2">
                Orden de Fabricación
              </h1>
              <p className="text-xs font-black text-indigo-400 uppercase">
                Expediente: {state.budgetNumber}
              </p>
              <p className="text-xs font-black text-indigo-400 uppercase">
                Fecha: {new Date().toLocaleDateString('es-ES')}
              </p>
            </div>
          </div>
        </div>

        {/* Especificaciones Generales */}
        <div className="mb-8 grid grid-cols-2 gap-4">
          <div className="bg-indigo-50 p-4 rounded-xl border border-indigo-100">
            <p className="text-[9px] font-black text-indigo-300 uppercase mb-1">Cliente</p>
            <p className="text-lg font-black text-indigo-950">{state.customerName || 'Sin especificar'}</p>
          </div>
          <div className="bg-orange-50 p-4 rounded-xl border border-orange-100">
            <p className="text-[9px] font-black text-orange-300 uppercase mb-1">Acabado Global</p>
            <p className="text-sm font-black text-orange-950">{finish}</p>
          </div>
        </div>

        {/* Lista de Muebles */}
        <div className="mb-8">
          <h2 className="text-xl font-black text-indigo-950 uppercase mb-4 flex items-center gap-2">
            <div className="w-1 h-6 bg-orange-600"></div>
            Lista de Muebles a Fabricar
          </h2>
          
          <table className="w-full">
            <thead className="bg-indigo-950 text-white">
              <tr>
                <th className="text-left p-4 text-xs font-black uppercase">Cant.</th>
                <th className="text-left p-4 text-xs font-black uppercase">Referencia</th>
                <th className="text-left p-4 text-xs font-black uppercase">Descripción</th>
                <th className="text-center p-4 text-xs font-black uppercase">Medidas (W×H×D)</th>
                <th className="text-center p-4 text-xs font-black uppercase">Apertura</th>
                <th className="text-left p-4 text-xs font-black uppercase">Notas</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-indigo-50">
              {items.map((item, idx) => {
                const product = allProducts.find(p => p.id === item.productId);
                
                if (item.isManual) {
                  return (
                    <tr key={item.id} className="hover:bg-indigo-50/50">
                      <td className="p-4 font-black text-indigo-900">{item.quantity}</td>
                      <td className="p-4 font-black text-indigo-600 uppercase text-xs">
                        {item.customReference || 'MANUAL'}
                      </td>
                      <td className="p-4 font-bold text-indigo-900 text-sm">
                        {item.manualDescription || 'Concepto Manual'}
                      </td>
                      <td className="p-4 text-center text-xs font-bold text-indigo-400">-</td>
                      <td className="p-4 text-center text-xs font-bold text-indigo-400">-</td>
                      <td className="p-4 text-xs text-indigo-600 italic">
                        Línea manual - {item.manualPoints || 0} puntos
                      </td>
                    </tr>
                  );
                }

                if (!product) return null;

                return (
                  <tr key={item.id} className="hover:bg-indigo-50/50">
                    <td className="p-4 font-black text-indigo-900 text-lg">{item.quantity}</td>
                    <td className="p-4 font-black text-indigo-600 uppercase text-xs">
                      {item.customReference || product.code}
                    </td>
                    <td className="p-4 font-bold text-indigo-900 text-sm">{product.name}</td>
                    <td className="p-4 text-center font-mono text-xs font-bold text-indigo-800">
                      {item.customWidth} × {item.customHeight} × {item.customDepth} cm
                    </td>
                    <td className="p-4 text-center text-xs font-black uppercase text-indigo-600">
                      {item.openingDirection || 'N/A'}
                    </td>
                    <td className="p-4 text-xs text-indigo-600 italic">
                      {item.notes || '-'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Especificaciones de Materiales */}
        <div className="bg-slate-50 p-6 rounded-xl border border-slate-200">
          <h3 className="text-sm font-black text-slate-900 uppercase mb-3">Especificaciones de Materiales</h3>
          <div className="grid grid-cols-2 gap-4 text-xs">
            <div>
              <span className="font-black text-slate-500 uppercase">Armazón/Casco:</span>
              <span className="ml-2 font-bold text-slate-900">{carcassColor}</span>
            </div>
            <div>
              <span className="font-black text-slate-500 uppercase">Frentes:</span>
              <span className="ml-2 font-bold text-slate-900">{finish}</span>
            </div>
            {state.doorColorLow && (
              <div>
                <span className="font-black text-slate-500 uppercase">Puertas Bajos:</span>
                <span className="ml-2 font-bold text-slate-900">{state.doorColorLow}</span>
              </div>
            )}
            {state.doorColorHigh && (
              <div>
                <span className="font-black text-slate-500 uppercase">Puertas Altos:</span>
                <span className="ml-2 font-bold text-slate-900">{state.doorColorHigh}</span>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="mt-12 pt-6 border-t border-slate-200 text-center">
          <p className="text-[8px] font-black text-slate-300 uppercase tracking-widest">
            Documento Generado por Luiggi Home Master Industrial System v2026
          </p>
        </div>
      </div>
    </div>
  );
};

export default ManufacturingReport;
