import React from 'react';
import { ArrowLeft, Printer, FileText, Download, Scissors } from 'lucide-react';
import { generateManufacturingPDF } from '../services/pdfGenerator';

// onOpenDespiece (opcional): si se pasa, muestra un botón "Despiece" en la
// cabecera que abre el despiece COMPLETO (5 secciones). Lo usa el Portal de
// Fábrica para tener todo en el mismo Informe Industrial. Desde el presupuesto
// no se pasa, por lo que el botón no aparece y no afecta a ese flujo.
const ManufacturingReport = ({ items, finish, carcassColor, state, catalogs, logo, distributorName, onBack, onOpenDespiece }) => {
  
  const allProducts = catalogs
    .flatMap(c => c.products.map(p => ({ ...p, catalogId: c.id })));

  // Pedido de armarios: usa acabado de armario (color), no specs de cocina.
  const _items = Array.isArray(items) ? items : [];
  const isArmarioReport = _items.length > 0 && _items.every(i => i.itemType === 'armario');
  const armarioFinish = _items.find(i => i.itemType === 'armario')?.finish
    || _items.find(i => i.itemType === 'armario')?.material || finish;

  const handleExportPDF = () => {
    generateManufacturingPDF({
      budgetNumber: state.budgetNumber,
      customerName: state.customerName,
      globalFinish: finish,
      carcassColor: carcassColor,
      doorColorLow: state.doorColorLow,
      doorColorHigh: state.doorColorHigh,
      doorColorColumns: state.doorColorColumns,
      sideColor: state.sideColor,
      items: items,
      allProducts: allProducts,
      logo: logo,
      brandColor: state.brandColor,
      companyName: 'LUIGGI HOME',
      distributorName: distributorName
    });
  };

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

        <div className="flex gap-2">
          {onOpenDespiece && (
            <button
              onClick={onOpenDespiece}
              className="flex items-center gap-2 px-6 py-2 bg-indigo-600 text-white rounded-xl font-black uppercase text-xs hover:bg-indigo-700 transition-all shadow-xl"
              data-testid="report-despiece-btn"
              title="Ver despiece completo: corte, bandas, herrajes, puertas proveedor…"
            >
              <Scissors size={18} />
              Despiece
            </button>
          )}
          <button
            onClick={handleExportPDF}
            className="flex items-center gap-2 px-6 py-2 bg-emerald-600 text-white rounded-xl font-black uppercase text-xs hover:bg-emerald-700 transition-all shadow-xl"
          >
            <Download size={18} />
            Exportar PDF
          </button>
          <button
            onClick={() => window.print()}
            className="flex items-center gap-2 px-6 py-2 bg-orange-600 text-white rounded-xl font-black uppercase text-xs hover:bg-orange-700 transition-all shadow-xl"
          >
            <Printer size={18} />
            Imprimir
          </button>
        </div>
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
          <div className={`p-4 rounded-xl border ${isArmarioReport ? 'bg-purple-50 border-purple-100' : 'bg-orange-50 border-orange-100'}`}>
            <p className={`text-[9px] font-black uppercase mb-1 flex items-center gap-2 ${isArmarioReport ? 'text-purple-300' : 'text-orange-300'}`}>
              {isArmarioReport && <span className="px-1.5 py-0.5 rounded bg-purple-600 text-white tracking-wider">🚪 Armario</span>}
              Acabado Global
            </p>
            <p className={`text-sm font-black ${isArmarioReport ? 'text-purple-950' : 'text-orange-950'}`}>{isArmarioReport ? armarioFinish : finish}</p>
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
              {items.filter(item => !item.isManual).map((item, idx) => {
                // El producto del catálogo es OPCIONAL: en el Portal de Fábrica el
                // catálogo va vacío, así que usamos los datos del propio item como
                // fallback (no descartamos la fila si no hay producto en catálogo).
                const product = allProducts.find(p => p.id === item.productId);

                const code = item.customReference || item.productCode || product?.code || '—';
                const name = product?.name || item.productName || item.description || '—';
                const width = item.customWidth ?? item.width ?? product?.width ?? '';
                const height = item.customHeight ?? item.height ?? product?.height ?? '';
                const depth = item.customDepth ?? item.depth ?? product?.depth ?? '';

                // Cortes especiales: solo se pueden detectar si tenemos las medidas
                // originales del catálogo para comparar.
                const specialCuts = [];
                if (product) {
                  if (Number(item.customWidth) !== Number(product.width)) specialCuts.push('C.ANCHO');
                  if (Number(item.customHeight) !== Number(product.height)) specialCuts.push('C.ALTO');
                  if (Number(item.customDepth) !== Number(product.depth)) specialCuts.push('C.FONDO');
                }
                if (item.hasVigaCut) specialCuts.push('C.VIGA');

                const notesDisplay = [...specialCuts];
                if (item.notes) notesDisplay.push(item.notes);

                return (
                  <tr key={item.id || idx} className="hover:bg-indigo-50/50">
                    <td className="p-4 font-black text-indigo-900 text-lg">{item.quantity}</td>
                    <td className="p-4 font-black text-indigo-600 uppercase text-xs">
                      {code}
                      {item.itemType === 'armario' && (
                        <span className="ml-1 px-1 py-0.5 rounded bg-purple-100 text-purple-700 text-[8px] tracking-wider">ARMARIO</span>
                      )}
                    </td>
                    <td className="p-4 font-bold text-indigo-900 text-sm">{name}</td>
                    <td className="p-4 text-center font-mono text-xs font-bold text-indigo-800">
                      {width} × {height} × {depth} mm
                    </td>
                    <td className="p-4 text-center text-xs font-black uppercase text-indigo-600">
                      {item.openingDirection || 'N/A'}
                    </td>
                    <td className="p-4 text-xs">
                      {specialCuts.length > 0 && (
                        <span className="font-black text-orange-600">{specialCuts.join(', ')}</span>
                      )}
                      {specialCuts.length > 0 && item.notes && ' - '}
                      {item.notes && <span className="text-indigo-600 italic">{item.notes}</span>}
                      {notesDisplay.length === 0 && '-'}
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
          {isArmarioReport ? (
            <div className="grid grid-cols-2 gap-4 text-xs">
              <div>
                <span className="font-black text-slate-500 uppercase">Tipo:</span>
                <span className="ml-2 font-bold text-purple-700">Armario a medida</span>
              </div>
              <div>
                <span className="font-black text-slate-500 uppercase">Acabado / Color:</span>
                <span className="ml-2 font-bold text-slate-900">{armarioFinish}</span>
              </div>
            </div>
          ) : (
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
            {state.doorColorColumns && (
              <div>
                <span className="font-black text-slate-500 uppercase">Puertas Columnas:</span>
                <span className="ml-2 font-bold text-slate-900">{state.doorColorColumns}</span>
              </div>
            )}
            {state.sideColor && (
              <div>
                <span className="font-black text-slate-500 uppercase">Costados / Vistos:</span>
                <span className="ml-2 font-bold text-slate-900">{state.sideColor}</span>
              </div>
            )}
          </div>
          )}
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
