/**
 * ReportGenerator - Generador de informes con filtros avanzados
 * Permite filtrar por fechas, clientes, categorías, tipo de documento
 * y exportar a PDF directamente desde la app.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { FileText, Download, Filter, RefreshCw, Calendar, User, Tag, TrendingUp, BarChart3, X, Printer } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const eur = (n) => (Number(n) || 0).toLocaleString('es-ES', { style: 'currency', currency: 'EUR' });
const pct = (n) => `${(Number(n) || 0).toFixed(1)}%`;

const ReportGenerator = ({ onOpenDocument }) => {
  // Filtros
  const [filters, setFilters] = useState({
    fecha_desde: '',
    fecha_hasta: '',
    cliente: '',
    categoria: '',
    doc_type: '',
    min_venta: '',
    max_venta: '',
    created_by: '',
    revisada: '',
    sort_by: 'fecha',
    sort_order: 'desc',
  });

  // Opciones de filtros disponibles
  const [availableFilters, setAvailableFilters] = useState({
    clientes: [],
    clientesInfo: [],
    categorias: [],
    creadores: [],
    docTypes: [],
    fechaMin: null,
    fechaMax: null,
  });

  // Datos del informe
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showFilters, setShowFilters] = useState(true);
  const [exporting, setExporting] = useState(false);

  // Cargar filtros disponibles al montar
  useEffect(() => {
    const loadFilters = async () => {
      try {
        const r = await fetch(`${API_URL}/api/reports/available-filters`);
        if (r.ok) {
          const data = await r.json();
          setAvailableFilters(data);
          // Establecer rango de fechas por defecto
          if (data.fechaMin && data.fechaMax) {
            setFilters(prev => ({
              ...prev,
              fecha_desde: data.fechaMin,
              fecha_hasta: data.fechaMax,
            }));
          }
        }
      } catch (e) {
        console.error('Error cargando filtros:', e);
      }
    };
    loadFilters();
  }, []);

  // Generar informe
  const generateReport = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.append(key, value);
      });
      
      const r = await fetch(`${API_URL}/api/reports/rentabilidad?${params.toString()}`);
      if (r.ok) {
        const data = await r.json();
        setReport(data);
      } else {
        console.error('Error generando informe');
      }
    } catch (e) {
      console.error('Error:', e);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  // Exportar a PDF
  const exportPDF = async () => {
    setExporting(true);
    try {
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.append(key, value);
      });
      
      const r = await fetch(`${API_URL}/api/reports/rentabilidad/pdf?${params.toString()}`);
      if (r.ok) {
        const blob = await r.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `informe_rentabilidad_${new Date().toISOString().slice(0,10)}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      }
    } catch (e) {
      console.error('Error exportando PDF:', e);
    } finally {
      setExporting(false);
    }
  };

  // Limpiar filtros
  const clearFilters = () => {
    setFilters({
      fecha_desde: availableFilters.fechaMin || '',
      fecha_hasta: availableFilters.fechaMax || '',
      cliente: '',
      categoria: '',
      doc_type: '',
      min_venta: '',
      max_venta: '',
      created_by: '',
      revisada: '',
      sort_by: 'fecha',
      sort_order: 'desc',
    });
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-50 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-900 to-purple-900 text-white p-5 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-white/10 rounded-xl">
            <BarChart3 size={24} />
          </div>
          <div>
            <h1 className="text-xl font-black tracking-tight">GENERADOR DE INFORMES</h1>
            <p className="text-xs text-indigo-300 uppercase tracking-widest">Rentabilidad por líneas de documentos</p>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-bold text-sm transition-all ${
              showFilters ? 'bg-white/20 text-white' : 'bg-white/10 text-white/70 hover:bg-white/20'
            }`}
          >
            <Filter size={16} />
            Filtros
          </button>
          <button
            onClick={generateReport}
            disabled={loading}
            className="flex items-center gap-2 bg-emerald-500 hover:bg-emerald-400 px-5 py-2 rounded-lg font-bold text-sm transition-colors disabled:opacity-50"
          >
            {loading ? <RefreshCw size={16} className="animate-spin" /> : <TrendingUp size={16} />}
            Generar
          </button>
          {report && (
            <button
              onClick={exportPDF}
              disabled={exporting}
              className="flex items-center gap-2 bg-red-500 hover:bg-red-400 px-5 py-2 rounded-lg font-bold text-sm transition-colors disabled:opacity-50"
            >
              {exporting ? <RefreshCw size={16} className="animate-spin" /> : <Download size={16} />}
              PDF
            </button>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        {/* Panel de filtros */}
        {showFilters && (
          <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-5 mb-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-black text-slate-700 uppercase tracking-wider flex items-center gap-2">
                <Filter size={14} className="text-indigo-500" />
                Filtros del informe
              </h3>
              <button onClick={clearFilters} className="text-xs text-slate-400 hover:text-slate-600 font-bold">
                Limpiar filtros
              </button>
            </div>
            
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
              {/* Fecha desde */}
              <div>
                <label className="text-[10px] font-bold text-slate-500 uppercase flex items-center gap-1">
                  <Calendar size={10} /> Desde
                </label>
                <input
                  type="date"
                  value={filters.fecha_desde}
                  onChange={(e) => setFilters(prev => ({ ...prev, fecha_desde: e.target.value }))}
                  className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-indigo-400"
                />
              </div>
              
              {/* Fecha hasta */}
              <div>
                <label className="text-[10px] font-bold text-slate-500 uppercase flex items-center gap-1">
                  <Calendar size={10} /> Hasta
                </label>
                <input
                  type="date"
                  value={filters.fecha_hasta}
                  onChange={(e) => setFilters(prev => ({ ...prev, fecha_hasta: e.target.value }))}
                  className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-indigo-400"
                />
              </div>
              
              {/* Cliente */}
              <div>
                <label className="text-[10px] font-bold text-slate-500 uppercase flex items-center gap-1">
                  <User size={10} /> Cliente (nombre o código)
                </label>
                <input
                  list="report-clientes-datalist"
                  value={filters.cliente}
                  onChange={(e) => setFilters(prev => ({ ...prev, cliente: e.target.value }))}
                  placeholder="Todos · escribe nombre o código"
                  className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-indigo-400"
                />
                <datalist id="report-clientes-datalist">
                  {(availableFilters.clientesInfo && availableFilters.clientesInfo.length
                    ? availableFilters.clientesInfo
                    : (availableFilters.clientes || []).map(n => ({ nombre: n, codigo: '' }))
                  ).map(c => (
                    // Una sola entrada por cliente. El texto incluye el código para poder
                    // buscarlo; el valor es el nombre. También puedes teclear el código y
                    // filtrar (el backend casa por nombre o código).
                    <option key={c.nombre} value={c.nombre}>{c.codigo ? `${c.nombre} (${c.codigo})` : c.nombre}</option>
                  ))}
                </datalist>
              </div>
              
              {/* Categoría */}
              <div>
                <label className="text-[10px] font-bold text-slate-500 uppercase flex items-center gap-1">
                  <Tag size={10} /> Categoría
                </label>
                <select
                  value={filters.categoria}
                  onChange={(e) => setFilters(prev => ({ ...prev, categoria: e.target.value }))}
                  className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-indigo-400"
                >
                  <option value="">Todas las categorías</option>
                  {availableFilters.categorias.map(c => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>
              
              {/* Tipo documento */}
              <div>
                <label className="text-[10px] font-bold text-slate-500 uppercase">Tipo documento</label>
                <select
                  value={filters.doc_type}
                  onChange={(e) => setFilters(prev => ({ ...prev, doc_type: e.target.value }))}
                  className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-indigo-400"
                >
                  <option value="">Todos</option>
                  {availableFilters.docTypes.map(d => (
                    <option key={d} value={d}>{d.charAt(0).toUpperCase() + d.slice(1)}</option>
                  ))}
                </select>
              </div>
              
              {/* Check Controller */}
              <div>
                <label className="text-[10px] font-bold text-slate-500 uppercase">Check Controller</label>
                <select
                  value={filters.revisada}
                  onChange={(e) => setFilters(prev => ({ ...prev, revisada: e.target.value }))}
                  className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-indigo-400"
                >
                  <option value="">Todas</option>
                  <option value="no">❓ Faltan por revisar</option>
                  <option value="si">✅ Revisadas</option>
                </select>
              </div>

              {/* Venta mínima */}
              <div>
                <label className="text-[10px] font-bold text-slate-500 uppercase">Venta mín. (€)</label>
                <input
                  type="number"
                  value={filters.min_venta}
                  onChange={(e) => setFilters(prev => ({ ...prev, min_venta: e.target.value }))}
                  placeholder="0"
                  className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-indigo-400"
                />
              </div>
              
              {/* Venta máxima */}
              <div>
                <label className="text-[10px] font-bold text-slate-500 uppercase">Venta máx. (€)</label>
                <input
                  type="number"
                  value={filters.max_venta}
                  onChange={(e) => setFilters(prev => ({ ...prev, max_venta: e.target.value }))}
                  placeholder="Sin límite"
                  className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-indigo-400"
                />
              </div>
              
              {/* Ordenar por */}
              <div>
                <label className="text-[10px] font-bold text-slate-500 uppercase">Ordenar por</label>
                <div className="flex gap-1 mt-1">
                  <select
                    value={filters.sort_by}
                    onChange={(e) => setFilters(prev => ({ ...prev, sort_by: e.target.value }))}
                    className="flex-1 px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-indigo-400"
                  >
                    <option value="fecha">Fecha</option>
                    <option value="venta">Venta</option>
                    <option value="margen">Margen</option>
                    <option value="cliente">Cliente</option>
                  </select>
                  <button
                    onClick={() => setFilters(prev => ({ ...prev, sort_order: prev.sort_order === 'desc' ? 'asc' : 'desc' }))}
                    className="px-3 py-2 border border-slate-200 rounded-lg text-xs font-bold hover:bg-slate-100"
                  >
                    {filters.sort_order === 'desc' ? '↓' : '↑'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Resultados del informe */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <RefreshCw size={32} className="animate-spin text-indigo-500" />
            <span className="ml-3 text-slate-500 font-bold">Generando informe...</span>
          </div>
        ) : report ? (
          <div className="space-y-6">
            {/* KPIs principales */}
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
              <div className="bg-white rounded-xl p-4 shadow-sm border border-slate-200">
                <p className="text-[10px] font-bold text-slate-400 uppercase">Facturación</p>
                <p className="text-lg font-black text-slate-800">{eur(report.summary.totalVenta)}</p>
              </div>
              <div className="bg-white rounded-xl p-4 shadow-sm border border-slate-200">
                <p className="text-[10px] font-bold text-slate-400 uppercase">Coste</p>
                <p className="text-lg font-black text-red-600">{eur(report.summary.totalCoste)}</p>
              </div>
              <div className="bg-white rounded-xl p-4 shadow-sm border border-slate-200">
                <p className="text-[10px] font-bold text-slate-400 uppercase">Margen</p>
                <p className="text-lg font-black text-emerald-600">{eur(report.summary.totalMargen)}</p>
              </div>
              <div className="bg-white rounded-xl p-4 shadow-sm border border-slate-200">
                <p className="text-[10px] font-bold text-slate-400 uppercase">% Margen</p>
                <p className="text-lg font-black text-indigo-600">{pct(report.summary.margenPct)}</p>
              </div>
              <div className="bg-white rounded-xl p-4 shadow-sm border border-slate-200">
                <p className="text-[10px] font-bold text-slate-400 uppercase">Documentos</p>
                <p className="text-lg font-black text-slate-800">{report.summary.numFichas}</p>
              </div>
              <div className="bg-white rounded-xl p-4 shadow-sm border border-slate-200">
                <p className="text-[10px] font-bold text-slate-400 uppercase">Líneas</p>
                <p className="text-lg font-black text-slate-800">{report.summary.numLineas}</p>
              </div>
            </div>

            {/* Dos columnas: Categorías y Clientes */}
            <div className="grid grid-cols-2 gap-6">
              {/* Por categoría */}
              <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                <div className="bg-indigo-50 px-5 py-3 border-b border-indigo-100">
                  <h3 className="text-xs font-black text-indigo-800 uppercase tracking-wider">Por Categoría</h3>
                </div>
                <div className="p-4">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-slate-200">
                        <th className="text-left py-2 font-bold text-slate-500">Categoría</th>
                        <th className="text-right py-2 font-bold text-slate-500">Venta</th>
                        <th className="text-right py-2 font-bold text-slate-500">%</th>
                      </tr>
                    </thead>
                    <tbody>
                      {report.byCategory.map((cat, i) => (
                        <tr key={i} className="border-b border-slate-100 hover:bg-slate-50">
                          <td className="py-2 font-bold text-slate-700">{cat.categoria}</td>
                          <td className="py-2 text-right text-slate-600">{eur(cat.venta)}</td>
                          <td className="py-2 text-right">
                            <span className="bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full font-bold">
                              {pct(cat.pctTotal)}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Por cliente */}
              <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                <div className="bg-emerald-50 px-5 py-3 border-b border-emerald-100">
                  <h3 className="text-xs font-black text-emerald-800 uppercase tracking-wider">Por Cliente</h3>
                </div>
                <div className="p-4">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-slate-200">
                        <th className="text-left py-2 font-bold text-slate-500">Cliente</th>
                        <th className="text-right py-2 font-bold text-slate-500">Venta</th>
                        <th className="text-right py-2 font-bold text-slate-500">%</th>
                      </tr>
                    </thead>
                    <tbody>
                      {report.byClient.map((cli, i) => (
                        <tr key={i} className="border-b border-slate-100 hover:bg-slate-50">
                          <td className="py-2 font-bold text-slate-700">{cli.cliente}</td>
                          <td className="py-2 text-right text-slate-600">{eur(cli.venta)}</td>
                          <td className="py-2 text-right">
                            <span className="bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full font-bold">
                              {pct(cli.pctTotal)}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            {/* Top líneas */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
              <div className="bg-purple-50 px-5 py-3 border-b border-purple-100 flex items-center justify-between">
                <h3 className="text-xs font-black text-purple-800 uppercase tracking-wider">Top Líneas por Venta</h3>
                <span className="text-[10px] text-purple-500 font-bold">{report.topLines.length} líneas</span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-200">
                      <th className="text-left px-4 py-2 font-bold text-slate-500">Ref</th>
                      <th className="text-left px-4 py-2 font-bold text-slate-500">Concepto</th>
                      <th className="text-left px-4 py-2 font-bold text-slate-500">Cliente</th>
                      <th className="text-left px-4 py-2 font-bold text-slate-500">Categoría</th>
                      <th className="text-right px-4 py-2 font-bold text-slate-500">Coste</th>
                      <th className="text-right px-4 py-2 font-bold text-slate-500">Venta</th>
                      <th className="text-right px-4 py-2 font-bold text-slate-500">Margen</th>
                      <th className="text-right px-4 py-2 font-bold text-slate-500">%</th>
                    </tr>
                  </thead>
                  <tbody>
                    {report.topLines.map((line, i) => {
                      const lmargen = (Number(line.venta) || 0) - (Number(line.coste) || 0);
                      const mpct = (Number(line.coste) || 0) > 0 ? (lmargen / (Number(line.coste) || 0) * 100) : null;
                      return (
                      <tr key={i}
                        onClick={() => onOpenDocument && line.docRef && onOpenDocument(line.docRef)}
                        title={line.docRef ? `Ir al documento ${line.docRef}` : ''}
                        className={`border-b border-slate-100 hover:bg-slate-50 ${onOpenDocument && line.docRef ? 'cursor-pointer' : ''}`}>
                        <td className="px-4 py-2 font-mono text-indigo-600 font-bold">{line.ref || '—'}{line.docRef && <span className="block text-[9px] text-slate-400 font-normal">📄 {line.docRef}</span>}</td>
                        <td className="px-4 py-2 text-slate-700 max-w-[300px] truncate">{line.concepto}</td>
                        <td className="px-4 py-2 text-slate-500">{line.cliente}</td>
                        <td className="px-4 py-2">
                          <span className="bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full text-[10px] font-bold">
                            {line.categoria}
                          </span>
                        </td>
                        <td className="px-4 py-2 text-right text-red-500">{eur(line.coste)}</td>
                        <td className="px-4 py-2 text-right font-bold text-slate-800">{eur(line.venta)}</td>
                        <td className={`px-4 py-2 text-right font-bold ${lmargen >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>{eur(lmargen)}</td>
                        <td className={`px-4 py-2 text-right font-bold ${lmargen >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>{mpct === null ? '—' : pct(mpct)}</td>
                      </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Detalle por documento */}
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
              <div className="bg-amber-50 px-5 py-3 border-b border-amber-100">
                <h3 className="text-xs font-black text-amber-800 uppercase tracking-wider">Detalle por Documento</h3>
              </div>
              <div className="p-4 space-y-4">
                {report.fichas.map((ficha, i) => (
                  <div key={i} className="border border-slate-200 rounded-lg overflow-hidden">
                    <div className={`bg-slate-50 px-4 py-3 flex items-center justify-between ${onOpenDocument && ficha.ref ? 'cursor-pointer hover:bg-slate-100' : ''}`}
                      onClick={() => onOpenDocument && ficha.ref && onOpenDocument(ficha.ref)}
                      title={ficha.ref ? `Ir al documento ${ficha.ref}` : ''}>
                      <div className="flex items-center gap-3">
                        <span className="text-sm font-black text-indigo-600">{onOpenDocument && ficha.ref ? '📄 ' : ''}{ficha.ref}</span>
                        <span className="text-xs text-slate-500">{ficha.cliente}</span>
                        <span className="text-[10px] bg-slate-200 text-slate-600 px-2 py-0.5 rounded-full font-bold">{ficha.fecha}</span>
                      </div>
                      <div className="flex items-center gap-4 text-xs">
                        <span className="text-slate-500">Coste: <strong className="text-red-500">{eur(ficha.totals.coste)}</strong></span>
                        <span className="text-slate-500">Venta: <strong className="text-slate-800">{eur(ficha.totals.venta)}</strong></span>
                        <span className="text-slate-500">Margen: <strong className="text-emerald-600">{eur((Number(ficha.totals.venta) || 0) - (Number(ficha.totals.coste) || 0))}</strong></span>
                        <span className="text-slate-500">%: <strong className="text-emerald-500">{(Number(ficha.totals.coste) || 0) > 0 ? pct(((Number(ficha.totals.venta) || 0) - (Number(ficha.totals.coste) || 0)) / (Number(ficha.totals.coste) || 0) * 100) : '—'}</strong></span>
                      </div>
                    </div>
                    <table className="w-full text-[11px]">
                      <thead>
                        <tr className="bg-slate-100/50">
                          <th className="text-left px-3 py-1.5 font-bold text-slate-400">Ref</th>
                          <th className="text-left px-3 py-1.5 font-bold text-slate-400">Concepto</th>
                          <th className="text-right px-3 py-1.5 font-bold text-slate-400">Cant.</th>
                          <th className="text-right px-3 py-1.5 font-bold text-slate-400">Coste</th>
                          <th className="text-right px-3 py-1.5 font-bold text-slate-400">Venta</th>
                          <th className="text-right px-3 py-1.5 font-bold text-slate-400">Margen</th>
                          <th className="text-right px-3 py-1.5 font-bold text-slate-400">%</th>
                        </tr>
                      </thead>
                      <tbody>
                        {ficha.lines.map((line, j) => {
                          const lmargen = (Number(line.venta) || 0) - (Number(line.coste) || 0);
                          const lpct = (Number(line.coste) || 0) > 0 ? (lmargen / (Number(line.coste) || 0) * 100) : null;
                          return (
                          <tr key={j} className="border-t border-slate-100">
                            <td className="px-3 py-1.5 font-mono text-indigo-500 text-[10px]">{line.ref || '—'}</td>
                            <td className="px-3 py-1.5 text-slate-700">{line.concepto}</td>
                            <td className="px-3 py-1.5 text-right text-slate-500">{line.cantidad}</td>
                            <td className="px-3 py-1.5 text-right text-red-500">{eur(line.coste)}</td>
                            <td className="px-3 py-1.5 text-right font-bold">{eur(line.venta)}</td>
                            <td className={`px-3 py-1.5 text-right font-bold ${lmargen >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>{eur(lmargen)}</td>
                            <td className={`px-3 py-1.5 text-right font-bold ${lmargen >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>{lpct === null ? '—' : pct(lpct)}</td>
                          </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                ))}
              </div>
            </div>

            {/* Footer del informe */}
            <div className="text-center text-xs text-slate-400 py-4">
              Informe generado el {new Date(report.generatedAt).toLocaleString('es-ES')} — LuiggiAI Engine — Luiggi Home ERP v4.1
            </div>
          </div>
        ) : (
          /* Estado vacío */
          <div className="flex flex-col items-center justify-center py-20">
            <FileText size={64} className="text-slate-200 mb-4" />
            <h3 className="text-lg font-bold text-slate-400">Genera un informe</h3>
            <p className="text-sm text-slate-300 mt-1">Configura los filtros y pulsa "Generar" para crear el informe de rentabilidad</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ReportGenerator;
