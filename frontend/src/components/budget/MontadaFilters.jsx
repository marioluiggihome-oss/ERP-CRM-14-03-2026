/*
 * © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * MontadaFilters.jsx
 * Filtros específicos para el modo MONTADA (muebles ensamblados)
 */
import React from 'react';
import { Search, X } from 'lucide-react';

export const MontadaFiltersHorizontal = ({
  selectedPrograma,
  setSelectedPrograma,
  selectedCategory,
  setSelectedCategory,
  selectedSeries,
  setSelectedSeries,
  selectedApertura,
  setSelectedApertura,
  uniqueProgramas,
  uniqueCategories,
  uniqueSeries,
  uniqueAperturas,
  filterWidth,
  setFilterWidth,
  filterHeight,
  setFilterHeight,
  filterDepth,
  setFilterDepth,
  searchQuery,
  setSearchQuery
}) => (
  <>
    <select 
      value={selectedPrograma} 
      onChange={e => { setSelectedPrograma(e.target.value); setSelectedCategory('TODAS'); setSelectedSeries('TODAS'); setSelectedApertura && setSelectedApertura('TODAS'); }} 
      className="bg-indigo-100 border-2 border-indigo-400 rounded-lg py-2 px-4 text-[11px] font-black uppercase text-indigo-900 outline-none"
    >
      <option value="TODOS">📁 PROGRAMA</option>
      {uniqueProgramas.map(p => <option key={p} value={p}>{p}</option>)}
    </select>
    <select 
      value={selectedCategory} 
      onChange={e => { setSelectedCategory(e.target.value); setSelectedSeries('TODAS'); setSelectedApertura && setSelectedApertura('TODAS'); }} 
      className="bg-purple-100 border-2 border-purple-400 rounded-lg py-2 px-4 text-[11px] font-black uppercase text-purple-900 outline-none" 
      disabled={selectedPrograma === 'TODOS'}
    >
      <option value="TODAS">📂 CATEGORÍA</option>
      {uniqueCategories.map(c => <option key={c} value={c}>{c}</option>)}
    </select>
    <select 
      value={selectedSeries} 
      onChange={e => { setSelectedSeries(e.target.value); setSelectedApertura && setSelectedApertura('TODAS'); }}
      className="bg-amber-100 border-2 border-amber-400 rounded-lg py-2 px-4 text-[11px] font-black uppercase text-amber-900 outline-none" 
      disabled={selectedCategory === 'TODAS'}
    >
      <option value="TODAS">📄 SERIE</option>
      {uniqueSeries.map(s => <option key={s} value={s}>{s}</option>)}
    </select>
    {/* Filtro de Apertura (1P, 2P, etc.) */}
    {uniqueAperturas && uniqueAperturas.length > 0 && (
      <select 
        value={selectedApertura || 'TODAS'} 
        onChange={e => setSelectedApertura && setSelectedApertura(e.target.value)}
        className="bg-green-100 border-2 border-green-400 rounded-lg py-2 px-4 text-[11px] font-black uppercase text-green-900 outline-none"
      >
        <option value="TODAS">🚪 APERTURA</option>
        {uniqueAperturas.map(a => <option key={a} value={a}>{a === '1P D/I' ? '1P ↔ D/I' : a}</option>)}
      </select>
    )}
    
    {/* Filtros de medidas */}
    <div className="flex items-center gap-1.5 bg-gradient-to-r from-blue-50 to-blue-100 rounded-xl px-3 py-2 border-2 border-blue-300 shadow-sm">
      <span className="text-[9px] font-black text-blue-600 mr-1">📐 MEDIDAS:</span>
      <div className="flex flex-col items-center">
        <label className="text-[7px] font-bold text-blue-500 uppercase">Ancho</label>
        <input 
          type="number" 
          placeholder="cm" 
          value={filterWidth} 
          onChange={e => setFilterWidth(e.target.value)}
          className="w-16 bg-white border-2 border-blue-300 rounded-lg px-2 py-1.5 text-xs font-bold text-center outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
          title="Filtrar por ancho (cm)"
        />
      </div>
      <div className="flex flex-col items-center">
        <label className="text-[7px] font-bold text-blue-500 uppercase">Alto</label>
        <input 
          type="number" 
          placeholder="cm" 
          value={filterHeight} 
          onChange={e => setFilterHeight(e.target.value)}
          className="w-16 bg-white border-2 border-blue-300 rounded-lg px-2 py-1.5 text-xs font-bold text-center outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
          title="Filtrar por alto (cm)"
        />
      </div>
      <div className="flex flex-col items-center">
        <label className="text-[7px] font-bold text-blue-500 uppercase">Fondo</label>
        <input 
          type="number" 
          placeholder="cm" 
          value={filterDepth} 
          onChange={e => setFilterDepth(e.target.value)}
          className="w-16 bg-white border-2 border-blue-300 rounded-lg px-2 py-1.5 text-xs font-bold text-center outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
          title="Filtrar por fondo (cm)"
        />
      </div>
      {(filterWidth || filterHeight || filterDepth) && (
        <button 
          onClick={() => { setFilterWidth(''); setFilterHeight(''); setFilterDepth(''); }}
          className="p-1.5 bg-red-100 text-red-500 hover:bg-red-200 rounded-lg ml-1 transition-colors"
          title="Limpiar filtros de medidas"
        >
          <X size={14} />
        </button>
      )}
    </div>
    <div className="relative w-[180px]">
      <Search className="absolute left-2 top-1/2 -translate-y-1/2 text-indigo-300" size={12} />
      <input 
        type="text" 
        placeholder="BUSCAR..." 
        value={searchQuery} 
        onChange={e => setSearchQuery(e.target.value)} 
        className="w-full bg-white border border-indigo-100 rounded-lg py-1 pl-7 pr-7 text-[8px] font-bold outline-none uppercase" 
      />
      {searchQuery && (
        <button onClick={() => setSearchQuery('')} className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-red-500" title="Limpiar búsqueda">
          <X size={12} />
        </button>
      )}
    </div>
  </>
);

export const MontadaFiltersVertical = ({
  selectedPrograma,
  setSelectedPrograma,
  selectedCategory,
  setSelectedCategory,
  selectedSeries,
  setSelectedSeries,
  selectedApertura,
  setSelectedApertura,
  uniqueProgramas,
  uniqueCategories,
  uniqueSeries,
  uniqueAperturas,
  filterWidth,
  setFilterWidth,
  filterHeight,
  setFilterHeight,
  filterDepth,
  setFilterDepth,
  searchQuery,
  setSearchQuery
}) => (
  <>
    <select 
      value={selectedPrograma} 
      onChange={e => { setSelectedPrograma(e.target.value); setSelectedCategory('TODAS'); setSelectedSeries('TODAS'); setSelectedApertura && setSelectedApertura('TODAS'); }} 
      className="w-full bg-indigo-100 border-2 border-indigo-400 rounded-lg py-2 px-3 text-[10px] font-black uppercase text-indigo-900 outline-none"
    >
      <option value="TODOS">📁 TODOS PROGRAMAS</option>
      {uniqueProgramas.map(p => <option key={p} value={p}>{p}</option>)}
    </select>
    <select 
      value={selectedCategory} 
      onChange={e => { setSelectedCategory(e.target.value); setSelectedSeries('TODAS'); setSelectedApertura && setSelectedApertura('TODAS'); }} 
      className="w-full bg-purple-100 border-2 border-purple-400 rounded-lg py-2 px-3 text-[10px] font-black uppercase text-purple-900 outline-none" 
      disabled={selectedPrograma === 'TODOS'}
    >
      <option value="TODAS">📂 TODAS CATEGORÍAS</option>
      {uniqueCategories.map(c => <option key={c} value={c}>{c}</option>)}
    </select>
    <select 
      value={selectedSeries} 
      onChange={e => { setSelectedSeries(e.target.value); setSelectedApertura && setSelectedApertura('TODAS'); }}
      className="w-full bg-amber-100 border-2 border-amber-400 rounded-lg py-2 px-3 text-[10px] font-black uppercase text-amber-900 outline-none" 
      disabled={selectedCategory === 'TODAS'}
    >
      <option value="TODAS">📄 TODAS SERIES</option>
      {uniqueSeries.map(s => <option key={s} value={s}>{s}</option>)}
    </select>
    {/* Filtro de Apertura (1P, 2P, etc.) */}
    {uniqueAperturas && uniqueAperturas.length > 0 && (
      <select 
        value={selectedApertura || 'TODAS'} 
        onChange={e => setSelectedApertura && setSelectedApertura(e.target.value)}
        className="w-full bg-green-100 border-2 border-green-400 rounded-lg py-2 px-3 text-[10px] font-black uppercase text-green-900 outline-none"
      >
        <option value="TODAS">🚪 TODAS APERTURAS</option>
        {uniqueAperturas.map(a => <option key={a} value={a}>{a === '1P D/I' ? '1P ↔ D/I' : a}</option>)}
      </select>
    )}
    
    {/* Filtros de medidas - Vista vertical */}
    <div className="flex items-center gap-2 bg-slate-100 rounded-lg p-2 border border-slate-200">
      <span className="text-[9px] font-black text-slate-500">📐 MEDIDAS:</span>
      <div className="flex gap-1.5">
        <input 
          type="number" 
          placeholder="AN" 
          value={filterWidth} 
          onChange={e => setFilterWidth(e.target.value)}
          className="w-14 bg-white border border-slate-200 rounded px-1.5 py-1 text-[10px] font-bold text-center outline-none"
          title="Filtrar por ancho (cm)"
        />
        <input 
          type="number" 
          placeholder="AL" 
          value={filterHeight} 
          onChange={e => setFilterHeight(e.target.value)}
          className="w-14 bg-white border border-slate-200 rounded px-1.5 py-1 text-[10px] font-bold text-center outline-none"
          title="Filtrar por alto (cm)"
        />
        <input 
          type="number" 
          placeholder="FO" 
          value={filterDepth} 
          onChange={e => setFilterDepth(e.target.value)}
          className="w-14 bg-white border border-slate-200 rounded px-1.5 py-1 text-[10px] font-bold text-center outline-none"
          title="Filtrar por fondo (cm)"
        />
      </div>
      {(filterWidth || filterHeight || filterDepth) && (
        <button 
          onClick={() => { setFilterWidth(''); setFilterHeight(''); setFilterDepth(''); }}
          className="text-slate-400 hover:text-red-500"
          title="Limpiar filtros"
        >
          <X size={12} />
        </button>
      )}
    </div>
    <div className="relative">
      <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-indigo-300" size={14} />
      <input 
        type="text" 
        placeholder="BUSCAR..." 
        value={searchQuery} 
        onChange={e => setSearchQuery(e.target.value)} 
        className="w-full bg-white border border-indigo-100 rounded-lg py-2 pl-9 pr-8 text-[10px] font-bold outline-none uppercase" 
      />
      {searchQuery && (
        <button onClick={() => setSearchQuery('')} className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-red-500" title="Limpiar búsqueda">
          <X size={14} />
        </button>
      )}
    </div>
  </>
);

export default MontadaFiltersHorizontal;
