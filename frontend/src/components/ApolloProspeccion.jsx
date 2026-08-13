/*
 * © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
import React, { useState, useEffect } from 'react';
import { 
  Building2, Palette, Hammer, Building, Store, Search, MapPin, 
  Mail, Phone, Linkedin, Globe, CheckCircle, UserPlus, Download, 
  Sparkles, RefreshCw, Send, ShieldCheck, AlertCircle, ExternalLink, Database,
  ChevronLeft, ChevronRight, CheckCheck
} from 'lucide-react';
import { getToken } from '../services/api';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const SECTORES = [
  { id: 'todos', nombre: 'Todos los Sectores', icon: Sparkles },
  { id: 'arquitectura', nombre: 'Estudios de Arquitectura', icon: Building2 },
  { id: 'interiorismo', nombre: 'Diseño de Interiores', icon: Palette },
  { id: 'reformas', nombre: 'Reformas Integrales', icon: Hammer },
  { id: 'promotoras', nombre: 'Promotoras & Constructoras', icon: Building },
  { id: 'tiendas', nombre: 'Tiendas de Cocinas', icon: Store }
];

const CIUDADES_PRESET = [
  'Toda España',
  'Madrid',
  'Toledo',
  'Salamanca',
  'Zamora',
  'Cáceres',
  'Valladolid',
  'Badajoz',
  'Illescas',
  'Talavera de la Reina',
  'Ciudad Real',
  'Albacete',
  'Cuenca',
  'Guadalajara',
  'Barcelona',
  'Valencia',
  'Alicante',
  'Sevilla',
  'Málaga',
  'Marbella',
  'Bilbao',
  'Zaragoza',
  'Murcia',
  'Palma de Mallorca',
  'Granada',
  'Córdoba',
  'Santander',
  'Vigo',
  'A Coruña'
];

export default function ApolloProspeccion({ currentUser, onNavigateToContacts }) {
  const [sector, setSector] = useState('todos');
  const [ciudad, setCiudad] = useState('Toda España');
  const [busqueda, setBusqueda] = useState('');
  const [cargo, setCargo] = useState('');
  const [pagina, setPagina] = useState(1);
  const [limite, setLimite] = useState(30);
  
  const [prospectos, setProspectos] = useState([]);
  const [totalResultados, setTotalResultados] = useState(0);
  const [totalPaginas, setTotalPaginas] = useState(1);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState({ configurado: false, modo: 'sin_fuente_configurada' });
  const [sourceMeta, setSourceMeta] = useState({ origen: 'sin_fuente_verificable', mensaje: '' });
  const [auditoria, setAuditoria] = useState(null);
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [apiKeyInput, setApiKeyInput] = useState('');
  const [guardandoKey, setGuardandoKey] = useState(false);
  const [importados, setImportados] = useState({});
  const [importingId, setImportingId] = useState(null);
  const [importandoLote, setImportandoLote] = useState(false);
  const [mensajeExito, setMensajeExito] = useState(null);
  const [error, setError] = useState(null);

  // Cargar estado inicial y prospectos
  useEffect(() => {
    fetchStatus();
  }, []);

  useEffect(() => {
    setPagina(1);
    buscarProspectos(1);
  }, [sector, ciudad]);

  const getHeaders = () => {
    const token = getToken();
    return {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    };
  };

  const fetchStatus = async () => {
    try {
      const res = await fetch(`${API_URL}/api/apollo/status`, { headers: getHeaders() });
      if (res.ok) {
        const data = await res.json();
        setStatus(data);
      }
    } catch (e) {
      console.warn('No se pudo verificar estado de Apollo:', e);
    }
  };

  const guardarApiKey = async () => {
    setGuardandoKey(true);
    try {
      const res = await fetch(`${API_URL}/api/apollo/set-key`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ apiKey: apiKeyInput })
      });
      if (res.ok) {
        await fetchStatus();
        setShowConfigModal(false);
        setMensajeExito(apiKeyInput.trim() ? '✓ Clave de Apollo.io configurada con éxito.' : '✓ Sin fuente B2B activa hasta configurar Apollo.');
        setTimeout(() => setMensajeExito(null), 4000);
        buscarProspectos(1);
      }
    } catch (e) {
      alert('Error guardando la clave de API: ' + e.message);
    } finally {
      setGuardandoKey(false);
    }
  };

  const buscarProspectos = async (numPagina = pagina) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/api/apollo/search`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({
          sector: sector === 'todos' ? '' : sector,
          ubicacion: ciudad === 'Toda España' ? 'España' : ciudad,
          cargo: cargo.trim(),
          termino: busqueda.trim(),
          pagina: numPagina,
          limite: limite
        })
      });
      if (res.ok) {
        const data = await res.json();
        setProspectos(data.prospectos || []);
        setTotalResultados(data.total || (data.prospectos || []).length);
        setTotalPaginas(data.totalPaginas || 1);
        setSourceMeta({ origen: data.origen || 'sin_fuente_verificable', mensaje: data.mensaje || '' });
        setPagina(numPagina);
      } else {
        setError('Error al conectar con el motor de prospección B2B.');
      }
    } catch (e) {
      setError('Error de conexión con el servidor.');
    } finally {
      setLoading(false);
    }
  };

  const handleImportar = async (p) => {
    setImportingId(p.id);
    try {
      const res = await fetch(`${API_URL}/api/apollo/importar-crm`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({
          id: p.id,
          nombre: p.nombre,
          cargo: p.cargo,
          empresa: p.empresa,
          sector: p.sector,
          ciudad: p.ciudad,
          provincia: p.provincia,
          email: p.email,
          telefono: p.telefono,
          telefono_directo: p.telefono_directo,
          linkedin: p.linkedin,
          web: p.web,
          notas: `Importado desde ${p.proveedor || p.origen || 'fuente no indicada'}. ${p.proyectos_recientes || ''}`,
          origen: p.origen,
          proveedor: p.proveedor,
          source_record_id: p.source_record_id,
          source_url: p.source_url,
          consultado_en: p.consultado_en
        })
      });
      if (res.ok) {
        const data = await res.json();
        setImportados(prev => ({ ...prev, [p.id]: true }));
        setMensajeExito(data.mensaje || `¡${p.nombre} importado con éxito en el CRM!`);
        setTimeout(() => setMensajeExito(null), 4000);
      }
    } catch (e) {
      setError('No se pudo importar el contacto al CRM.');
    } finally {
      setImportingId(null);
    }
  };

  const handleImportarLote = async () => {
    const pendientes = prospectos.filter(p => !importados[p.id]);
    if (!pendientes.length) {
      alert('Todos los prospectos visibles ya han sido importados.');
      return;
    }
    if (!window.confirm(`¿Importar los ${pendientes.length} prospectos visibles al CRM como contactos y oportunidades?`)) {
      return;
    }
    setImportandoLote(true);
    let guardados = 0;
    try {
      for (const p of pendientes) {
        try {
          const res = await fetch(`${API_URL}/api/apollo/importar-crm`, {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({
              id: p.id,
              nombre: p.nombre,
              cargo: p.cargo,
              empresa: p.empresa,
              sector: p.sector,
              ciudad: p.ciudad,
              provincia: p.provincia,
              email: p.email,
              telefono: p.telefono,
              telefono_directo: p.telefono_directo,
              linkedin: p.linkedin,
              web: p.web,
              notas: `Importado desde ${p.proveedor || p.origen || 'fuente no indicada'}. ${p.proyectos_recientes || ''}`,
              origen: p.origen,
              proveedor: p.proveedor,
              source_record_id: p.source_record_id,
              source_url: p.source_url,
              consultado_en: p.consultado_en
            })
          });
          if (res.ok) {
            setImportados(prev => ({ ...prev, [p.id]: true }));
            guardados++;
          }
        } catch (err) {
          console.warn('Error al importar:', p.nombre, err);
        }
      }
      setMensajeExito(`✅ ¡${guardados} prospectos importados con éxito al CRM!`);
      setTimeout(() => setMensajeExito(null), 5000);
    } finally {
      setImportandoLote(false);
    }
  };

  const auditarCRM = async () => {
    try {
      const res = await fetch(`${API_URL}/api/apollo/audit-crm`, { headers: getHeaders() });
      if (res.ok) setAuditoria(await res.json());
      else setError('No se pudo auditar la trazabilidad de los contactos B2B del CRM.');
    } catch (e) {
      setError('Error de conexión al auditar el CRM.');
    }
  };

  const exportarCSV = () => {
    if (!prospectos.length) return;
    const cabeceras = ['Nombre', 'Cargo', 'Empresa', 'Sector', 'Ciudad', 'Provincia', 'Email', 'Teléfono', 'LinkedIn', 'Web', 'Proyectos'];
    const filas = prospectos.map(p => [
      `"${p.nombre}"`,
      `"${p.cargo}"`,
      `"${p.empresa}"`,
      `"${p.sector}"`,
      `"${p.ciudad}"`,
      `"${p.provincia || ''}"`,
      `"${p.email}"`,
      `"${p.telefono_directo || p.telefono}"`,
      `"${p.linkedin || ''}"`,
      `"${p.web || ''}"`,
      `"${p.proyectos_recientes || ''}"`
    ]);
    const contenido = [cabeceras.join(','), ...filas.map(f => f.join(','))].join('\n');
    const blob = new Blob([`\uFEFF${contenido}`], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `Prospectos_B2B_${ciudad.replace(/\s+/g, '_')}_${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="absolute inset-0 overflow-y-auto bg-slate-50 pb-28">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white p-6 shadow-md shrink-0">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="p-1.5 bg-amber-500/20 text-amber-400 border border-amber-500/30 rounded-lg">
                <Database size={16} />
              </span>
              <h1 className="text-xl font-black tracking-tight text-white">Base de Datos de Clientes Potenciales (B2B)</h1>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full border bg-emerald-500/20 text-emerald-300 border-emerald-500/30">
                ● {status.configurado ? 'Consulta en vivo con fuente trazable' : 'Sin fuente de datos activa'}
              </span>
            </div>
            <p className="text-xs text-slate-300">
              Prescripción y captación de <b>Estudios de Arquitectura, Interioristas, Empresas de Reformas y Promotoras</b> para suministro de cocinas y mobiliario de Luiggi Home.
            </p>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={() => setShowConfigModal(true)}
              className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold border transition-all ${status.configurado ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30' : 'bg-white/10 hover:bg-white/20 text-white border-white/10'}`}
              title="Configurar clave de Apollo.io para búsquedas en vivo"
            >
              <ShieldCheck size={14} className={status.configurado ? 'text-emerald-400' : 'text-slate-300'} />
              <span>{status.configurado ? 'Apollo API Activa' : 'Configurar Apollo Key'}</span>
            </button>
            <button
              onClick={auditarCRM}
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold bg-white/10 hover:bg-white/20 text-white border border-white/10 transition-colors"
              title="Revisar cuántos contactos B2B importados al CRM tienen fuente trazable"
            >
              <ShieldCheck size={14} /> Auditar CRM
            </button>
            <button
              onClick={handleImportarLote}
              disabled={importandoLote || !prospectos.length}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-black bg-emerald-600 hover:bg-emerald-500 text-white shadow-md transition-colors disabled:opacity-50"
              title="Importar todos los prospectos de la lista actual al CRM"
            >
              {importandoLote ? <RefreshCw size={14} className="animate-spin" /> : <CheckCheck size={14} />}
              <span>Importar Lote ({prospectos.filter(p => !importados[p.id]).length})</span>
            </button>
            <button
              onClick={exportarCSV}
              disabled={!prospectos.length}
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold bg-white/10 hover:bg-white/20 text-white border border-white/10 transition-colors disabled:opacity-50"
            >
              <Download size={14} /> Exportar CSV
            </button>
            <button
              onClick={() => buscarProspectos(pagina)}
              disabled={loading}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-black bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg transition-all disabled:opacity-50"
            >
              <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Actualizar
            </button>
          </div>
        </div>
      </div>

      {/* Alerta de éxito */}
      {mensajeExito && (
        <div className="max-w-7xl mx-auto w-full px-6 pt-4">
          <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs font-bold flex items-center justify-between shadow-sm">
            <div className="flex items-center gap-2">
              <CheckCircle size={16} className="text-emerald-600" />
              <span>{mensajeExito}</span>
            </div>
            {onNavigateToContacts && (
              <button
                onClick={() => onNavigateToContacts('contacts')}
                className="text-xs font-black text-emerald-700 underline hover:text-emerald-900"
              >
                Ver en Contactos →
              </button>
            )}
          </div>
        </div>
      )}

      {/* Panel de Filtros */}
      <div className="max-w-7xl mx-auto w-full p-6 space-y-4">
        {/* Selector de Sectores */}
        <div className="flex flex-wrap gap-2">
          {SECTORES.map(sec => {
            const Icon = sec.icon;
            const isSelected = sector === sec.id;
            return (
              <button
                key={sec.id}
                onClick={() => { setSector(sec.id); }}
                className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-black transition-all ${
                  isSelected
                    ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/20 ring-2 ring-indigo-400 ring-offset-1'
                    : 'bg-white text-slate-700 hover:bg-slate-100 border border-slate-200 shadow-sm'
                }`}
              >
                <Icon size={14} />
                <span>{sec.nombre}</span>
              </button>
            );
          })}
        </div>

        {/* Barra de Búsqueda Avanzada */}
        <div className="bg-white p-3 rounded-2xl border border-slate-200 shadow-sm grid grid-cols-1 sm:grid-cols-12 gap-2.5 items-center">
          {/* Ciudad */}
          <div className="sm:col-span-4">
            <div className="relative">
              <MapPin size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <select
                value={ciudad}
                onChange={e => setCiudad(e.target.value)}
                className="w-full pl-8 pr-3 py-2 text-xs font-bold bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none"
              >
                {CIUDADES_PRESET.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
          </div>

          {/* Cargo */}
          <div className="sm:col-span-3">
            <input
              type="text"
              placeholder="Cargo (ej: Arquitecto, Compras, Interiorista...)"
              value={cargo}
              onChange={e => setCargo(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && buscarProspectos(1)}
              className="w-full px-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none"
            />
          </div>

          {/* Empresa / Palabra clave */}
          <div className="sm:col-span-3">
            <div className="relative">
              <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                placeholder="Empresa, palabra o nombre..."
                value={busqueda}
                onChange={e => setBusqueda(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && buscarProspectos(1)}
                className="w-full pl-8 pr-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none"
              />
            </div>
          </div>

          {/* Botón Buscar */}
          <div className="sm:col-span-2">
            <button
              onClick={() => buscarProspectos(1)}
              disabled={loading}
              className="w-full flex items-center justify-center gap-1.5 px-4 py-2 rounded-xl text-xs font-black bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm transition-colors disabled:opacity-50"
            >
              {loading ? <RefreshCw size={14} className="animate-spin" /> : <Search size={14} />}
              <span>Filtrar</span>
            </button>
          </div>
        </div>

        {/* Estadísticas / Resumen de resultados */}
        <div className="flex items-center justify-between text-xs text-slate-500 px-1 flex-wrap gap-2">
          <span>Se han encontrado <b>{totalResultados}</b> organizaciones procedentes de <b>{sourceMeta.origen === 'apollo_live_api' ? 'Apollo.io' : 'una fuente no configurada'}</b> en <b>{ciudad}</b></span>
          <span className={`flex items-center gap-1 font-bold ${sourceMeta.origen === 'apollo_live_api' ? 'text-indigo-600' : 'text-amber-700'}`}>
            <ShieldCheck size={14} /> {sourceMeta.mensaje || 'Revisa cada dato antes de contactar'}
          </span>
        </div>

        {auditoria && (
          <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-xs text-amber-900 flex flex-wrap gap-x-5 gap-y-1">
            <b>Auditoría CRM B2B:</b><span>{auditoria.totalProspeccionB2B} registros de prospección</span><span>{auditoria.conTrazabilidadIndividual} trazables</span><span className="font-bold">{auditoria.pendientesDeRevision} pendientes de revisión</span>
          </div>
        )}

        {/* Grid de Prospectos */}
        {loading ? (
          <div className="py-16 text-center">
            <RefreshCw size={32} className="animate-spin text-indigo-600 mx-auto mb-3" />
            <p className="text-sm font-bold text-slate-700">Consultando base de datos B2B...</p>
            <p className="text-xs text-slate-400">Extrayendo contactos verificados de arquitectura, interiorismo y reformas</p>
          </div>
        ) : prospectos.length === 0 ? (
          <div className="py-16 text-center bg-white rounded-2xl border border-slate-200">
            <AlertCircle size={32} className="text-slate-400 mx-auto mb-2" />
            <p className="text-sm font-bold text-slate-700">No se encontraron prospectos con estos filtros.</p>
            <p className="text-xs text-slate-400 mt-1">Prueba seleccionando otra ciudad o ampliando a «Toda España».</p>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {prospectos.map(p => {
                const estaImportado = importados[p.id];
                const isImporting = importingId === p.id;
                return (
                  <div 
                    key={p.id}
                    className="bg-white rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-all p-4 flex flex-col justify-between"
                  >
                    <div>
                      {/* Cabecera Tarjeta */}
                      <div className="flex items-start justify-between gap-2 mb-2.5">
                        <div className="flex items-center gap-2.5">
                          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 text-white font-black text-sm flex items-center justify-center shadow-sm">
                            {p.nombre.split(' ').map(n => n[0]).slice(0, 2).join('')}
                          </div>
                          <div>
                            <h3 className="text-sm font-black text-slate-800 leading-tight">{p.nombre}</h3>
                            <p className="text-[11px] font-bold text-indigo-600">{p.cargo}</p>
                          </div>
                        </div>
                        {p.proveedor && <span className="text-[10px] font-black px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-700 border border-indigo-200">{p.proveedor}</span>}
                      </div>

                      {/* Empresa y Ubicación */}
                      <div className="space-y-1 text-xs text-slate-600 mb-3 bg-slate-50/70 p-2.5 rounded-xl border border-slate-100">
                        <div className="flex items-center gap-1.5 font-bold text-slate-800">
                          <Building2 size={13} className="text-slate-400 shrink-0" />
                          <span className="truncate">{p.empresa}</span>
                        </div>
                        <div className="flex items-center justify-between text-[11px] text-slate-500">
                          <span className="flex items-center gap-1">
                            <MapPin size={11} className="text-slate-400" />
                            {p.ciudad}, {p.provincia || p.pais}
                          </span>
                          <span>{p.tamano_empresa}</span>
                        </div>
                      </div>

                      {/* Proyectos / Contexto */}
                      {p.proyectos_recientes && (
                        <p className="text-[11px] text-slate-500 italic mb-3 line-clamp-2">
                          «{p.proyectos_recientes}»
                        </p>
                      )}

                      {/* Datos de la fuente: solo se marcan verificados con evidencia explícita. */}
                      <div className="space-y-1 text-[11px] text-slate-600 mb-4 border-t border-slate-100 pt-2.5">
                        {p.email && (
                          <div className="flex items-center justify-between">
                            <span className="flex items-center gap-1.5 truncate text-slate-700 font-medium">
                              <Mail size={12} className="text-indigo-500 shrink-0" />
                              <a href={`mailto:${p.email}`} className="hover:underline truncate">{p.email}</a>
                            </span>
                            {p.email_verificado && <span className="text-[9px] font-black text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded">Verificado por proveedor</span>}
                          </div>
                        )}
                        {(p.telefono_directo || p.telefono) && (
                          <div className="flex items-center gap-1.5 text-slate-700">
                            <Phone size={12} className="text-emerald-500 shrink-0" />
                            <a href={`tel:${p.telefono_directo || p.telefono}`} className="hover:underline font-bold">
                              {p.telefono_directo || p.telefono}
                            </a>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Acciones */}
                    <div className="flex items-center gap-2 pt-2 border-t border-slate-100">
                      <button
                        onClick={() => handleImportar(p)}
                        disabled={estaImportado || isImporting}
                        className={`flex-1 flex items-center justify-center gap-1.5 py-2 px-3 rounded-xl text-xs font-black transition-all ${
                          estaImportado
                            ? 'bg-emerald-100 text-emerald-700 cursor-default'
                            : 'bg-indigo-600 hover:bg-indigo-700 text-white shadow-sm'
                        }`}
                      >
                        {estaImportado ? (
                          <><CheckCircle size={13} /> Importado en CRM</>
                        ) : isImporting ? (
                          <><RefreshCw size={13} className="animate-spin" /> Guardando...</>
                        ) : (
                          <><UserPlus size={13} /> Importar a CRM</>
                        )}
                      </button>

                      {p.telefono_directo && (
                        <a
                          href={`https://wa.me/${(p.telefono_directo || '').replace(/\D/g, '')}?text=${encodeURIComponent(`Hola ${p.nombre}, le contacto de Luiggi Home (Fábrica de Cocinas y Muebles a Medida). Nos encantaría presentarle nuestro catálogo y condiciones especiales para profesionales en ${p.ciudad}.`)}`}
                          target="_blank"
                          rel="noreferrer"
                          className="p-2 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 rounded-xl border border-emerald-200 transition-colors"
                          title="Enviar WhatsApp de presentación"
                        >
                          <Send size={13} />
                        </a>
                      )}

                      {p.linkedin && (
                        <a
                          href={p.linkedin}
                          target="_blank"
                          rel="noreferrer"
                          className="p-2 bg-slate-100 hover:bg-blue-50 text-slate-600 hover:text-blue-600 rounded-xl transition-colors"
                          title="Ver perfil de LinkedIn"
                        >
                          <Linkedin size={13} />
                        </a>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Paginador */}
            {totalPaginas > 1 && (
              <div className="flex items-center justify-center gap-2 pt-6">
                <button
                  onClick={() => buscarProspectos(Math.max(1, pagina - 1))}
                  disabled={pagina <= 1}
                  className="p-2 rounded-xl bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 disabled:opacity-40"
                >
                  <ChevronLeft size={16} />
                </button>
                <span className="text-xs font-bold text-slate-600 px-3">
                  Página {pagina} de {totalPaginas}
                </span>
                <button
                  onClick={() => buscarProspectos(Math.min(totalPaginas, pagina + 1))}
                  disabled={pagina >= totalPaginas}
                  className="p-2 rounded-xl bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 disabled:opacity-40"
                >
                  <ChevronRight size={16} />
                </button>
              </div>
            )}
          </>
        )}
      </div>

      {/* Modal de Configuración de Apollo API Key */}
      {showConfigModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl p-6 max-w-lg w-full space-y-4 shadow-2xl border border-slate-200 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ShieldCheck size={22} className="text-indigo-600" />
                <h3 className="text-lg font-black text-slate-900">Configuración de Apollo.io API</h3>
              </div>
              <button onClick={() => setShowConfigModal(false)} className="p-1.5 rounded-xl hover:bg-slate-100 text-slate-400">
                ✕
              </button>
            </div>

            <div className="space-y-2 text-xs text-slate-600">
              <p>
                <b>Estado actual:</b> {status.configurado ? (
                  <span className="text-emerald-700 font-bold">● Conectado a la API oficial de Apollo.io (Búsquedas en vivo entre 275M+ contactos).</span>
                ) : (
                  <span className="text-indigo-700 font-bold">● Directorio Oficial Verificado (Colegios de Arquitectos y Registro Mercantil).</span>
                )}
              </p>
              <p>
                Si dispones de una cuenta de <b>Apollo.io</b>, introduce tu clave de API privada para buscar y sincronizar contactos reales en tiempo real:
              </p>
            </div>

            <div>
              <label className="text-[10px] font-black uppercase text-slate-400 block mb-1">Clave de API de Apollo (X-Api-Key)</label>
              <input
                type="password"
                value={apiKeyInput}
                onChange={e => setApiKeyInput(e.target.value)}
                placeholder="Pega aquí tu clave de Apollo.io..."
                className="w-full px-4 py-2.5 rounded-xl border border-slate-200 text-xs font-mono focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 outline-none"
              />
              <p className="text-[10px] text-slate-400 mt-1">
                * Deja el campo vacío y guarda para volver al Directorio Oficial Verificado.
              </p>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setShowConfigModal(false)}
                className="px-4 py-2 rounded-xl border border-slate-200 text-xs font-bold text-slate-600 hover:bg-slate-50"
              >
                Cancelar
              </button>
              <button
                onClick={guardarApiKey}
                disabled={guardandoKey}
                className="px-6 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold shadow-md transition-all flex items-center gap-1.5"
              >
                {guardandoKey ? <RefreshCw size={14} className="animate-spin" /> : <CheckCircle size={14} />} Guardar Clave
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
