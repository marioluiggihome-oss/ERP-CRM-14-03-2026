/*
 * © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * CatalogProductRow.jsx
 * Fila de producto en el catálogo/librería
 */
import React from 'react';
import { Plus } from 'lucide-react';
import CabinetIcon from '../CabinetIcon';

// Helper function to get icon type from product
const getIconType = (code, category) => {
  const c = code?.toUpperCase() || '';
  
  if ((c.includes('APABL') || c.includes('AVABL') || c.includes('APVBL')) && 
      !c.includes('HL') && !c.includes('HS') && !c.includes('HF')) {
    return 'HK-TOP';
  }
  if (c.includes('HS')) return 'HS';
  if (c.includes('HL')) return 'HL';
  if (c.includes('HF')) return 'HF';
  if (c.includes('HM') || c.includes('CHM') || c.includes('PHM')) return 'HORNO+MICRO';
  if (c.includes('AM') || c.includes('BM')) return 'MICRO';
  if (c.includes('CH') || c.includes('BH') || c.includes('PH') || c.includes('VH')) return 'HORNO';
  if (c.includes('BP')) return 'PLACA';
  if (c.includes('BF')) return 'FREG';
  if (c.includes('AT')) return 'TERMO';
  if (c.includes('AE')) return 'ESCURRE';
  if (c.includes('AC')) return 'CAMPANA';
  if (c.includes('PE')) return 'EXTRAIBLE';
  if (c.includes('BOT')) return 'BOTELLERO';
  if (c.includes('ESC')) return 'ESCOBERO';
  if (c.includes('FRI')) return 'FRIGO';
  if (c.includes('ARA') || c.includes('BRA') || c.includes('ARC') || c.includes('BRC')) return 'RINCON';
  if (c.includes('3C') || c.includes('4C') || c.includes('5C')) return '3C';
  if (c.startsWith('COS_') || category === 'COSTADOS') return 'COSTADO';
  if (c.startsWith('EST_') || category === 'ESTANTES') return 'ESTANTE';
  if (c.startsWith('REG_') || category === 'REGLETAS') return 'REGLETA';
  if (c.startsWith('PTA_') || category === 'PUERTAS') return 'PUERTA';
  if (c.startsWith('VIT_') || category === 'VITRINAS') return 'VITRINA';
  if (c.startsWith('COR_') || category === 'CORNISAS') return 'CORNISA';
  if (c.startsWith('ZOC_') || category === 'ZOCALOS') return 'ZOCALO';
  if (c.includes('2P')) return '2P';
  if (c.includes('1V') || c.includes('2V')) return '1V';
  
  return '1P';
};

// Helper for hardware type
const getHardwareType = (code) => {
  const c = code?.toUpperCase() || '';
  if ((c.includes('APABL') || c.includes('AVABL') || c.includes('APVBL') || c.includes('AVVBL')) && 
      !c.includes('HL') && !c.includes('HS') && !c.includes('HF')) {
    return 'HK';
  }
  if (c.includes('HS')) return 'HS';
  if (c.includes('HL')) return 'HL';
  if (c.includes('HF')) return 'HF';
  return null;
};

// Helper for special type
const getSpecialType = (code, name) => {
  const c = code?.toUpperCase() || '';
  const n = name?.toUpperCase() || '';
  
  if (c.includes('HM') || c.includes('CHM') || c.includes('PHM') || c.includes('VHM')) return 'HORNO+MICRO';
  if (c.includes('AM') || c.includes('BM')) return 'MICRO';
  if (c.includes('CH') || c.includes('BH') || c.includes('PH') || c.includes('VH')) return 'HORNO';
  if (c.includes('BP')) return 'PLACA';
  if (c.includes('BF')) return 'FREG';
  if (c.includes('AT')) return 'TERMO';
  if (c.includes('AE')) return 'ESCURRE';
  if (c.includes('AC')) return 'CAMPANA';
  if (c.includes('PE') || c.includes('PEL') || c.includes('PEB')) return 'EXTRAÍBLE';
  if (c.includes('BOT')) return 'BOTELLERO';
  if (c.includes('ESC')) return 'ESCOBERO';
  if (c.includes('FRI')) return 'FRIGO';
  
  if (n.includes('HORNO') && n.includes('MICRO')) return 'HORNO+MICRO';
  if (n.includes('MICROONDAS') || n.includes('MICRO')) return 'MICRO';
  if (n.includes('HORNO')) return 'HORNO';
  if (n.includes('PLACA') || n.includes('VITRO')) return 'PLACA';
  if (n.includes('FREGADERO') || n.includes('FREG')) return 'FREG';
  if (n.includes('CACEROLERO')) return 'CAJONES';
  if (n.includes('CAJONES') || n.includes('CAJÓN')) return 'CAJONES';
  
  return null;
};

const hardwareColors = {
  'HK': 'bg-red-500 text-white',
  'HS': 'bg-emerald-500 text-white', 
  'HL': 'bg-violet-500 text-white',
  'HF': 'bg-cyan-500 text-white'
};

const specialColors = {
  'MICRO': 'bg-blue-100 text-blue-700',
  'HORNO': 'bg-amber-100 text-amber-700',
  'HORNO+MICRO': 'bg-orange-100 text-orange-700',
  'PLACA': 'bg-red-100 text-red-700',
  'FREG': 'bg-sky-100 text-sky-700',
  'TERMO': 'bg-teal-100 text-teal-700',
  'ESCURRE': 'bg-indigo-100 text-indigo-700',
  'CAMPANA': 'bg-purple-100 text-purple-700',
  'EXTRAÍBLE': 'bg-lime-100 text-lime-700',
  'BOTELLERO': 'bg-rose-100 text-rose-700',
  'ESCOBERO': 'bg-stone-100 text-stone-700',
  'FRIGO': 'bg-cyan-100 text-cyan-700',
  'CAJONES': 'bg-yellow-100 text-yellow-700'
};

export const CatalogProductRowTable = ({ product, onAdd, selectedTariff = 'T1', selectedZone = 'Z1', formatMeasure = (v) => v }) => {
  const code = product.code?.toUpperCase() || '';
  const isGola = code.startsWith('G') && /^G\d/.test(code);
  const hardwareType = getHardwareType(code);
  const specialType = getSpecialType(code, product.name);
  const iconType = getIconType(code, product.category);
  
  // Obtener precio según tarifa/zona seleccionada
  const getPrice = () => {
    const zp = product.zonePoints || {};
    if (product.library === 'MV') {
      return zp[selectedTariff] ?? zp.T1 ?? (typeof product.points === 'number' ? product.points : product.points?.T1) ?? 0;
    } else {
      return zp[selectedZone] ?? zp.Z1 ?? (typeof product.points === 'number' ? product.points : product.points?.Z1) ?? 0;
    }
  };
  
  return (
    <tr className="hover:bg-orange-50 group cursor-pointer transition-colors" onClick={() => onAdd(product)}>
      <td className="p-1 pl-2 w-[45px]">
        <CabinetIcon type={iconType} isGola={isGola} className="w-8 h-8" />
      </td>
      <td className="p-2 font-bold text-indigo-900 text-[11px] w-[90px]">{product.code}</td>
      <td className="p-2 min-w-[180px]">
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-[10px] font-bold text-indigo-600 uppercase">{product.name}</span>
          {hardwareType && (
            <span className={`px-1.5 py-0.5 rounded text-[7px] font-black ${hardwareColors[hardwareType]}`}>
              {hardwareType}
            </span>
          )}
          {specialType && (
            <span className={`px-1.5 py-0.5 rounded text-[7px] font-bold ${specialColors[specialType]}`}>
              {specialType}
            </span>
          )}
        </div>
        {product.series && <div className="text-[8px] text-orange-500 font-medium mt-0.5">{product.series}</div>}
      </td>
      <td className="p-2 text-center font-bold text-slate-600 text-[10px] w-[55px]">{formatMeasure(product.width) || '-'}</td>
      <td className="p-2 text-center font-bold text-slate-600 text-[10px] w-[55px]">{formatMeasure(product.height) || '-'}</td>
      <td className="p-2 text-center font-bold text-slate-600 text-[10px] w-[55px]">{formatMeasure(product.depth) || '-'}</td>
      <td className="p-2 text-center font-black text-orange-600 text-[11px] w-[60px]">
        {getPrice()}
      </td>
      <td className="p-2 pr-3 text-right w-[40px]">
        <Plus size={14} className="text-orange-600 inline opacity-0 group-hover:opacity-100 transition-opacity"/>
      </td>
    </tr>
  );
};

export const CatalogProductRowCard = ({ product, onAdd, selectedTariff = 'T1', selectedZone = 'Z1', formatMeasure = (v) => v, measureUnit = 'cm' }) => {
  const code = product.code?.toUpperCase() || '';
  const isGola = code.startsWith('G') && /^G\d/.test(code);
  const hardwareType = getHardwareType(code);
  const specialType = getSpecialType(code, product.name);
  const iconType = getIconType(code, product.category);
  
  // Obtener precio según tarifa/zona seleccionada
  const getPrice = () => {
    const zp = product.zonePoints || {};
    if (product.library === 'MV') {
      return zp[selectedTariff] ?? zp.T1 ?? (typeof product.points === 'number' ? product.points : product.points?.T1) ?? 0;
    } else {
      return zp[selectedZone] ?? zp.Z1 ?? (typeof product.points === 'number' ? product.points : product.points?.Z1) ?? 0;
    }
  };
  
  return (
    <div 
      className="p-3 hover:bg-orange-50 cursor-pointer transition-colors group"
      onClick={() => onAdd(product)}
    >
      <div className="flex items-center gap-3">
        <CabinetIcon type={iconType} isGola={isGola} className="w-12 h-12 shrink-0" />
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <span className="text-[13px] font-black text-indigo-900">{product.code}</span>
            <span className="text-[14px] font-black text-orange-600">
              {getPrice()} pts
            </span>
          </div>
          <div className="flex items-center gap-1.5 flex-wrap mt-1">
            <span className="text-[11px] font-bold text-indigo-600 uppercase">{product.name}</span>
            {hardwareType && (
              <span className={`px-1.5 py-0.5 rounded text-[8px] font-black ${hardwareColors[hardwareType]}`}>
                {hardwareType}
              </span>
            )}
            {specialType && (
              <span className={`px-1.5 py-0.5 rounded text-[8px] font-bold ${specialColors[specialType]}`}>
                {specialType}
              </span>
            )}
          </div>
          <div className="flex items-center gap-3 mt-1">
            <span className="text-[10px] font-bold text-slate-500">
              AN: {formatMeasure(product.width) || '-'} | AL: {formatMeasure(product.height) || '-'} | FO: {formatMeasure(product.depth) || '-'} {measureUnit}
            </span>
          </div>
          {product.series && <div className="text-[9px] text-orange-500 font-medium mt-1">{product.series}</div>}
        </div>
        <Plus size={18} className="text-orange-600 opacity-0 group-hover:opacity-100 transition-opacity shrink-0"/>
      </div>
    </div>
  );
};

export default CatalogProductRowTable;
