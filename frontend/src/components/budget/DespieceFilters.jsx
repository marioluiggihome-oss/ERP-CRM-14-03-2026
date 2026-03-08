/**
 * DespieceFilters.jsx
 * Filtros específicos para el modo DESPIECE
 */
import React from 'react';
import { Factory } from 'lucide-react';

export const DespieceFiltersHorizontal = ({ 
  despieceFilters, 
  setDespieceFilters, 
  despieceFilterOptions,
  despieceProductsCount 
}) => (
  <>
    <div className="flex items-center gap-1 bg-gradient-to-r from-purple-50 to-purple-100 rounded-xl px-2 py-1 border-2 border-purple-300">
      <Factory size={14} className="text-purple-600" />
      <select 
        value={despieceFilters.manufacturer} 
        onChange={e => setDespieceFilters(prev => ({...prev, manufacturer: e.target.value}))} 
        className="bg-white border border-purple-300 rounded-lg py-1.5 px-2 text-[10px] font-bold uppercase text-purple-900 outline-none"
      >
        <option value="">🏭 FABRICANTE</option>
        {despieceFilterOptions.manufacturers.map(m => <option key={m} value={m}>{m}</option>)}
      </select>
      <select 
        value={despieceFilters.collection} 
        onChange={e => setDespieceFilters(prev => ({...prev, collection: e.target.value}))} 
        className="bg-white border border-purple-300 rounded-lg py-1.5 px-2 text-[10px] font-bold uppercase text-purple-900 outline-none"
      >
        <option value="">📦 MODELO</option>
        {despieceFilterOptions.collections.map(c => <option key={c} value={c}>{c}</option>)}
      </select>
      <select 
        value={despieceFilters.finish} 
        onChange={e => setDespieceFilters(prev => ({...prev, finish: e.target.value}))} 
        className="bg-white border border-purple-300 rounded-lg py-1.5 px-2 text-[10px] font-bold uppercase text-purple-900 outline-none"
      >
        <option value="">✨ ACABADO</option>
        {despieceFilterOptions.finishes.map(f => <option key={f} value={f}>{f}</option>)}
      </select>
      <select 
        value={despieceFilters.thickness} 
        onChange={e => setDespieceFilters(prev => ({...prev, thickness: e.target.value}))} 
        className="bg-white border border-purple-300 rounded-lg py-1.5 px-2 text-[10px] font-bold uppercase text-purple-900 outline-none"
      >
        <option value="">📏 GROSOR</option>
        {despieceFilterOptions.thicknesses.map(t => <option key={t} value={t}>{t}mm</option>)}
      </select>
    </div>
    <span className="text-[9px] font-bold text-purple-600 bg-purple-100 px-2 py-1 rounded-lg">
      {despieceProductsCount} tableros
    </span>
  </>
);

export const DespieceFiltersVertical = ({ 
  despieceFilters, 
  setDespieceFilters, 
  despieceFilterOptions,
  despieceProductsCount 
}) => (
  <>
    <div className="bg-gradient-to-r from-purple-100 to-purple-50 rounded-xl p-2 border-2 border-purple-300">
      <div className="flex items-center gap-2 mb-2">
        <Factory size={14} className="text-purple-600" />
        <span className="text-[9px] font-black text-purple-700 uppercase">Filtros Despiece</span>
      </div>
      <select 
        value={despieceFilters.manufacturer} 
        onChange={e => setDespieceFilters(prev => ({...prev, manufacturer: e.target.value}))} 
        className="w-full bg-white border border-purple-300 rounded-lg py-2 px-3 text-[10px] font-bold uppercase text-purple-900 outline-none mb-2"
      >
        <option value="">🏭 FABRICANTE</option>
        {despieceFilterOptions.manufacturers.map(m => <option key={m} value={m}>{m}</option>)}
      </select>
      <select 
        value={despieceFilters.collection} 
        onChange={e => setDespieceFilters(prev => ({...prev, collection: e.target.value}))} 
        className="w-full bg-white border border-purple-300 rounded-lg py-2 px-3 text-[10px] font-bold uppercase text-purple-900 outline-none mb-2"
      >
        <option value="">📦 MODELO</option>
        {despieceFilterOptions.collections.map(c => <option key={c} value={c}>{c}</option>)}
      </select>
      <select 
        value={despieceFilters.finish} 
        onChange={e => setDespieceFilters(prev => ({...prev, finish: e.target.value}))} 
        className="w-full bg-white border border-purple-300 rounded-lg py-2 px-3 text-[10px] font-bold uppercase text-purple-900 outline-none mb-2"
      >
        <option value="">✨ ACABADO</option>
        {despieceFilterOptions.finishes.map(f => <option key={f} value={f}>{f}</option>)}
      </select>
      <select 
        value={despieceFilters.thickness} 
        onChange={e => setDespieceFilters(prev => ({...prev, thickness: e.target.value}))} 
        className="w-full bg-white border border-purple-300 rounded-lg py-2 px-3 text-[10px] font-bold uppercase text-purple-900 outline-none"
      >
        <option value="">📏 GROSOR</option>
        {despieceFilterOptions.thicknesses.map(t => <option key={t} value={t}>{t}mm</option>)}
      </select>
    </div>
    <div className="text-center py-1">
      <span className="text-[10px] font-bold text-purple-600 bg-purple-100 px-3 py-1 rounded-lg">
        {despieceProductsCount} tableros disponibles
      </span>
    </div>
  </>
);

export default DespieceFiltersHorizontal;
