/**
 * BudgetItemRow.jsx
 * Componente para una fila de ítem en el presupuesto
 */
import React from 'react';
import { Trash2, Info } from 'lucide-react';
import CabinetIcon from '../CabinetIcon';

const BudgetItemRow = ({
  item,
  product,
  isUnknown,
  lineDetails,
  isValorado,
  currentUser,
  updateItem,
  removeItem,
  getHardwareType,
  getSpecialType
}) => {
  const { total: price, breakdown, hasExtras } = lineDetails;
  
  // Detectar tipo de herraje
  const code = product?.code || '';
  const codeUpper = code.toUpperCase();
  const hardwareType = getHardwareType?.(codeUpper);
  const specialType = getSpecialType?.(codeUpper, product?.name);
  
  // Calcular cortes especiales
  let specialCuts = [];
  if (!item.isManual && product) {
    if (Number(item.customWidth) !== Number(product.width)) specialCuts.push("ANCHO");
    if (Number(item.customHeight) !== Number(product.height)) specialCuts.push("ALTO");
    if (Number(item.customDepth) !== Number(product.depth)) specialCuts.push("FONDO");
    if (item.hasVigaCut) specialCuts.push("VIGA");
  }
  const specialLabel = specialCuts.length > 0 ? `+ CORTE ${specialCuts.join('/')}` : '';
  
  // Detectar si NO necesita selector D/I
  const productName = product?.name?.toLowerCase() || '';
  const productCode = product?.code || '';
  const productRef = product?.reference || '';
  
  const isTwoDoor = productName.includes('2 puerta') || 
                    productName.includes('2p') ||
                    productCode.includes('2P') ||
                    product?.visualType === '2P';
  
  const isSemicolumnaTwoDoor = (productName.includes('semicolumna') || productRef.startsWith('SC') || productRef.startsWith('10') || productRef.startsWith('11')) &&
                              (productName.includes('2 puerta') || productCode.includes('2P'));
  
  const hasDrawersOrGavetas = productName.includes('cajón') || 
                              productName.includes('cajon') ||
                              productName.includes('cajones') ||
                              productName.includes('gaveta') ||
                              productName.includes('gavetas') ||
                              productName.includes('cacerolero') ||
                              productCode.includes('CB') ||
                              productCode.includes('CL') ||
                              /^\d+[A-Z]*\d*C/.test(productCode);
  
  const noNeedsOpeningSelector = isTwoDoor || isSemicolumnaTwoDoor || hasDrawersOrGavetas;

  // Detectar tipo de icono
  let iconType = '1P';
  if ((codeUpper.includes('APABL') || codeUpper.includes('AVABL') || codeUpper.includes('APVBL')) && 
      !codeUpper.includes('HL') && !codeUpper.includes('HS') && !codeUpper.includes('HF')) {
    iconType = 'HK-TOP';
  }
  else if (codeUpper.includes('HS')) iconType = 'HS';
  else if (codeUpper.includes('HL')) iconType = 'HL';
  else if (codeUpper.includes('HF')) iconType = 'HF';
  else if (codeUpper.includes('HM') || codeUpper.includes('CHM') || codeUpper.includes('PHM')) iconType = 'HORNO+MICRO';
  else if (codeUpper.includes('AM') || codeUpper.includes('BM')) iconType = 'MICRO';
  else if (codeUpper.includes('CH') || codeUpper.includes('BH') || codeUpper.includes('PH') || codeUpper.includes('VH')) iconType = 'HORNO';
  else if (codeUpper.includes('BP')) iconType = 'PLACA';
  else if (codeUpper.includes('BF')) iconType = 'FREG';
  else if (codeUpper.includes('AT')) iconType = 'TERMO';
  else if (codeUpper.includes('AE')) iconType = 'ESCURRE';
  else if (codeUpper.includes('AC')) iconType = 'CAMPANA';
  else if (codeUpper.includes('2P')) iconType = '2P';
  else if (codeUpper.includes('1V') || codeUpper.includes('2V')) iconType = '1V';

  const isGola = codeUpper.startsWith('G') && /^G\d/.test(codeUpper);

  return (
    <div className={`flex items-center px-2 py-2 text-indigo-950 hover:bg-indigo-50/50 transition-colors ${isUnknown ? 'bg-red-50 border-l-4 border-red-500' : item.fromAI ? 'bg-purple-50/50 border-l-4 border-purple-500' : item.isManual ? 'bg-emerald-50/30' : specialCuts.length > 0 ? 'bg-orange-50/20' : ''}`}>
      {/* Corte Viga */}
      <div className="w-7 shrink-0 flex justify-center">
        {!item.isManual ? (
          <button
            onClick={() => updateItem(item.id, 'hasVigaCut', !item.hasVigaCut)}
            className={`no-print p-1 rounded transition-all ${
              item.hasVigaCut 
                ? 'bg-orange-600 text-white shadow-md' 
                : 'bg-slate-100 text-slate-300 hover:bg-orange-100 hover:text-orange-600'
            }`}
            title={item.hasVigaCut ? 'Quitar corte de viga' : 'Añadir corte de viga (+€)'}
          >
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round">
              <path d="M4 20L20 4" />
              <path d="M2 12h4" />
              <path d="M18 12h4" />
            </svg>
          </button>
        ) : (
          <span className="text-[8px] text-emerald-500 font-black">M</span>
        )}
        {item.hasVigaCut && <span className="print-only text-[6px] font-black text-orange-600">V</span>}
      </div>

      {/* Cantidad */}
      <div className="w-8 shrink-0 text-center">
        <input type="number" min="1" value={item.quantity} onChange={e => updateItem(item.id, 'quantity', parseInt(e.target.value) || 1)} className="w-7 bg-transparent text-center font-black text-[10px] italic outline-none no-print" />
        <span className="print-only font-black text-[10px] italic">x{item.quantity}</span>
      </div>
      
      {/* Referencia */}
      <div className="w-20 shrink-0 pr-1">
        {item.isManual ? (
          <>
            <input 
              type="text" 
              value={item.customReference || ''} 
              onChange={e => updateItem(item.id, 'customReference', e.target.value)} 
              placeholder="REF" 
              className="w-full bg-white border border-emerald-200 rounded px-1 py-0.5 text-[7px] font-black uppercase text-indigo-800 outline-none focus:border-emerald-500 no-print placeholder-indigo-300" 
            />
            <span className="print-only text-[7px] font-black uppercase italic text-indigo-900">{item.customReference}</span>
          </>
        ) : (
          <>
            <span className="w-full bg-indigo-50/50 border border-indigo-100 rounded px-1 py-0.5 text-[7px] font-black uppercase italic text-indigo-900">{item.customReference ?? product?.code}</span>
            <span className="print-only text-[7px] font-black uppercase italic text-indigo-900">{item.customReference ?? product?.code}</span>
          </>
        )}
      </div>

      {/* Descripción */}
      {item.isManual ? (
        <div className="flex-1 min-w-[180px] flex items-center gap-2">
          <input 
            type="text" 
            value={item.manualDescription || ''} 
            onChange={e => updateItem(item.id, 'manualDescription', e.target.value)}
            placeholder="Descripción del concepto o servicio..."
            className="flex-1 bg-white border border-emerald-200 rounded px-2 py-0.5 text-[8px] font-bold uppercase text-indigo-900 outline-none focus:border-emerald-500 placeholder-indigo-300 no-print"
          />
          <span className="print-only text-[8px] font-bold uppercase italic text-indigo-900 flex-1">{item.manualDescription}</span>
        </div>
      ) : (
        <div className="flex-1 min-w-[180px] pr-2">
          <span className={`text-[8px] font-bold uppercase italic leading-tight block ${isUnknown ? 'text-red-500' : 'text-indigo-800'}`}>{product?.name}</span>
          {specialLabel && <span className="text-[6px] font-black text-orange-600 uppercase tracking-wide">{specialLabel}</span>}
        </div>
      )}

      {/* Dimensiones y Apertura */}
      {item.isManual ? (
        <div className="w-24 shrink-0 pr-1">
          <div className="flex items-center gap-1 bg-white border border-emerald-200 rounded px-1 py-0.5 no-print">
            <span className="text-[6px] font-black text-emerald-600">PTS:</span>
            <input 
              type="number" 
              value={item.manualPoints || 0} 
              onChange={e => updateItem(item.id, 'manualPoints', parseFloat(e.target.value) || 0)}
              className="w-full font-black text-[8px] text-orange-600 outline-none bg-transparent"
              placeholder="0"
            />
          </div>
          <span className="print-only text-[7px] font-bold text-emerald-600">{item.manualPoints} pts</span>
        </div>
      ) : (
        <>
          <div className="w-14 shrink-0 text-center">
            <input type="number" value={item.customWidth || ''} onChange={e => updateItem(item.id, 'customWidth', parseInt(e.target.value) || 0)} className={`w-12 bg-indigo-50/50 rounded p-0.5 text-[9px] font-black text-center outline-none border ${Number(item.customWidth) !== Number(product?.width) ? 'border-orange-500 text-orange-600 bg-orange-50' : 'border-indigo-100'} no-print`} />
            <span className="print-only font-bold text-[9px]">{item.customWidth || '-'}</span>
          </div>
          <div className="w-14 shrink-0 text-center">
            <input type="number" value={item.customHeight || ''} onChange={e => updateItem(item.id, 'customHeight', parseInt(e.target.value) || 0)} className={`w-12 bg-indigo-50/50 rounded p-0.5 text-[9px] font-black text-center outline-none border ${Number(item.customHeight) !== Number(product?.height) ? 'border-orange-500 text-orange-600 bg-orange-50' : 'border-indigo-100'} no-print`} />
            <span className="print-only font-bold text-[9px]">{item.customHeight || '-'}</span>
          </div>
          <div className="w-14 shrink-0 text-center hidden sm:block">
            <input type="number" value={item.customDepth || ''} onChange={e => updateItem(item.id, 'customDepth', parseInt(e.target.value) || 0)} className={`w-12 bg-indigo-50/50 rounded p-0.5 text-[9px] font-black text-center outline-none border ${Number(item.customDepth) !== Number(product?.depth) ? 'border-orange-500 text-orange-600 bg-orange-50' : 'border-indigo-100'} no-print`} />
            <span className="print-only font-bold text-[9px]">{item.customDepth || '-'}</span>
          </div>
          <div className="w-8 shrink-0 text-center">
            {noNeedsOpeningSelector ? (
              <>
                <span className="text-[7px] font-black text-indigo-300 no-print">-</span>
                <span className="print-only font-black text-[7px]">-</span>
              </>
            ) : (
              <>
                <select value={item.openingDirection || 'Derecha'} onChange={e => updateItem(item.id, 'openingDirection', e.target.value)} className="w-7 bg-indigo-50/50 border border-indigo-100 rounded py-0.5 text-[7px] font-black uppercase italic outline-none no-print">
                  <option value="Derecha">D</option>
                  <option value="Izquierda">I</option>
                  <option value="N/A">-</option>
                </select>
                <span className="print-only font-black text-[7px] italic uppercase">{item.openingDirection === 'Derecha' ? 'D' : item.openingDirection === 'Izquierda' ? 'I' : '-'}</span>
              </>
            )}
          </div>
          <div className="w-20 shrink-0 pr-1 hidden sm:block">
            <input type="text" placeholder="Notas..." value={item.notes || ''} onChange={e => updateItem(item.id, 'notes', e.target.value)} className="w-full bg-indigo-50/50 border border-indigo-100 rounded px-1 py-0.5 text-[7px] font-bold text-indigo-400 outline-none focus:border-orange-300 no-print" />
            <p className="print-only text-[7px] font-bold text-indigo-400 italic truncate">{item.notes}</p>
          </div>
        </>
      )}

      {/* Precio */}
      {isValorado && (
        <div className="w-20 shrink-0 text-right flex items-center justify-end gap-1 relative group/price">
          {hasExtras && currentUser?.isAdmin && <Info size={7} className="text-orange-600 no-print" />}
          <span className="text-[10px] font-black italic tracking-tight">{price.toLocaleString('es-ES', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}€</span>
          
          {currentUser?.isAdmin && (
            <div className="absolute right-0 top-full mt-2 z-50 hidden group-hover/price:block w-64 bg-slate-900 text-white p-4 rounded-xl shadow-2xl text-[9px] font-mono whitespace-pre-wrap text-left border border-indigo-500/30">
              <div className="absolute -top-1 right-4 w-2 h-2 bg-slate-900 rotate-45 border-t border-l border-indigo-500/30"></div>
              {breakdown}
            </div>
          )}
        </div>
      )}
      
      {/* Botón eliminar */}
      <div className="w-6 shrink-0 no-print">
        <button onClick={() => removeItem(item.id)} className="p-1 text-indigo-200 hover:text-red-500 transition-all"><Trash2 size={12}/></button>
      </div>
    </div>
  );
};

export default BudgetItemRow;
