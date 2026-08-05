/*
 * © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
/**
 * DigitalizadorAuditTab - Auditoría del Digitalizador IA
 * Muestra todos los expedientes generados con el Digitalizador
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  ScanLine,
  Eye,
  X,
  Calendar,
  User,
  FileText,
  Loader,
  Search,
  RefreshCw,
  Trash2,
  Building,
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const DigitalizadorAuditTab = ({ state }) => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [userFilter, setUserFilter] = useState('');

  const loadHistory = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ limit: 100 });
      if (searchTerm) params.append('search', searchTerm);
      if (userFilter) params.append('userId', userFilter);

      const response = await fetch(`${API_URL}/api/digitalizador/history?${params}`);
      const data = await response.json();
      if (data.success) {
        setHistory(data.history || []);
      }
    } catch (err) {
      console.error('Error loading digitalizador history:', err);
    } finally {
      setLoading(false);
    }
  }, [searchTerm, userFilter]);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  const handleDelete = async (itemId, e) => {
    e.stopPropagation();
    if (!window.confirm('¿Eliminar este expediente del historial?')) return;
    try {
      await fetch(`${API_URL}/api/digitalizador/history/${itemId}`, { method: 'DELETE' });
      setHistory((prev) => prev.filter((h) => h.id !== itemId));
      if (selected?.id === itemId) setSelected(null);
    } catch (err) {
      console.error(err);
    }
  };

  const formatDate = (isoDate) => {
    if (!isoDate) return '-';
    try {
      return new Date(isoDate).toLocaleDateString('es-ES', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return isoDate;
    }
  };

  // Stats
  const totalExpedientes = history.length;
  const totalLineas = history.reduce((acc, h) => acc + (h.lines?.length || 0), 0);
  const usuariosUnicos = new Set(history.map((h) => h.userId).filter(Boolean)).size;

  const allUsers = state?.users || [];
  const usersWithDigitalizador = allUsers.filter((u) => u.canUseDigitalizador);

  return (
    <div className="space-y-4" data-testid="digitalizador-audit-tab">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gradient-to-br from-orange-500 to-amber-600 rounded-xl">
            <ScanLine size={22} className="text-white" />
          </div>
          <div>
            <h3 className="text-lg font-black text-slate-900 uppercase">Auditoría Digitalizador IA</h3>
            <p className="text-xs text-slate-500">Expedientes técnicos generados por reconocimiento óptico</p>
          </div>
        </div>

        <button
          onClick={loadHistory}
          className="p-2 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
          disabled={loading}
          data-testid="digitalizador-audit-refresh"
        >
          <RefreshCw size={16} className={`text-slate-600 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <div className="p-4 bg-gradient-to-br from-orange-50 to-amber-50 rounded-xl border border-orange-100">
          <div className="flex items-center gap-2 mb-1">
            <FileText size={14} className="text-orange-600" />
            <span className="text-[10px] font-black uppercase text-orange-700">Expedientes</span>
          </div>
          <div className="text-2xl font-black text-orange-900">{totalExpedientes}</div>
        </div>
        <div className="p-4 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl border border-blue-100">
          <div className="flex items-center gap-2 mb-1">
            <Building size={14} className="text-blue-600" />
            <span className="text-[10px] font-black uppercase text-blue-700">Líneas totales</span>
          </div>
          <div className="text-2xl font-black text-blue-900">{totalLineas}</div>
        </div>
        <div className="p-4 bg-gradient-to-br from-emerald-50 to-green-50 rounded-xl border border-emerald-100">
          <div className="flex items-center gap-2 mb-1">
            <User size={14} className="text-emerald-600" />
            <span className="text-[10px] font-black uppercase text-emerald-700">Usuarios activos</span>
          </div>
          <div className="text-2xl font-black text-emerald-900">{usuariosUnicos}</div>
        </div>
      </div>

      {/* Filtros */}
      <div className="flex gap-3 items-center">
        <div className="flex-1 relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Buscar por expediente, proyecto o cliente..."
            className="w-full pl-9 pr-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:border-orange-500"
            data-testid="digitalizador-audit-search"
          />
        </div>
        <select
          value={userFilter}
          onChange={(e) => setUserFilter(e.target.value)}
          className="px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:border-orange-500"
          data-testid="digitalizador-audit-user-filter"
        >
          <option value="">Todos los usuarios</option>
          {usersWithDigitalizador.map((u) => (
            <option key={u.id} value={u.id}>{u.username || u.clientName}</option>
          ))}
        </select>
      </div>

      {/* Lista de expedientes */}
      <div className="bg-slate-50 rounded-xl border border-slate-200 overflow-hidden">
        <div className="max-h-[500px] overflow-y-auto">
          {loading && history.length === 0 ? (
            <div className="h-32 flex items-center justify-center">
              <Loader size={20} className="animate-spin text-orange-500" />
            </div>
          ) : history.length === 0 ? (
            <div className="h-40 flex flex-col items-center justify-center text-slate-400">
              <ScanLine size={36} className="mb-2 opacity-50" />
              <p className="font-bold text-sm">Sin expedientes registrados</p>
              <p className="text-xs">Los expedientes generados con el Digitalizador aparecerán aquí</p>
            </div>
          ) : (
            <div className="divide-y divide-slate-200">
              {history.map((item) => (
                <div
                  key={item.id}
                  onClick={() => setSelected(item)}
                  className="p-3 bg-white hover:bg-orange-50 cursor-pointer transition-colors flex items-center gap-3"
                  data-testid={`digitalizador-audit-row-${item.id}`}
                >
                  <div className="p-2 bg-orange-100 rounded-lg">
                    <FileText size={14} className="text-orange-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-black text-sm text-slate-900">{item.expNumber || 'Sin nº'}</span>
                      {item.projectName && (
                        <span className="text-xs text-slate-600 truncate">{item.projectName}</span>
                      )}
                    </div>
                    <div className="flex items-center gap-3 mt-0.5 text-[11px] text-slate-500">
                      {item.customerName && <span>{item.customerName}</span>}
                      {item.userName && <span>· {item.userName}</span>}
                      <span>· {(item.lines?.length || 0)} líneas</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-[10px] text-slate-400 flex items-center gap-1">
                      <Calendar size={10} /> {formatDate(item.createdAt)}
                    </span>
                    <button
                      onClick={() => setSelected(item)}
                      className="p-1.5 hover:bg-orange-100 rounded text-orange-600"
                      title="Ver detalle"
                    >
                      <Eye size={14} />
                    </button>
                    <button
                      onClick={(e) => handleDelete(item.id, e)}
                      className="p-1.5 hover:bg-red-100 rounded text-red-600"
                      title="Eliminar"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Modal de detalle */}
      {selected && (
        <div className="fixed inset-0 bg-black/50 z-[100] flex items-center justify-center p-4" onClick={() => setSelected(null)}>
          <div className="bg-white rounded-2xl shadow-2xl max-w-3xl w-full max-h-[85vh] overflow-hidden flex flex-col" onClick={(e) => e.stopPropagation()}>
            <div className="px-6 py-4 bg-gradient-to-r from-orange-500 to-amber-600 text-white flex items-center justify-between">
              <div>
                <h3 className="font-black text-lg">{selected.expNumber || 'Expediente'}</h3>
                <p className="text-xs opacity-90">{selected.projectName} · {selected.customerName}</p>
              </div>
              <button onClick={() => setSelected(null)} className="p-1.5 hover:bg-white/20 rounded-lg">
                <X size={20} />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div><span className="font-bold text-slate-500">Usuario:</span> {selected.userName || '-'}</div>
                <div><span className="font-bold text-slate-500">Fecha:</span> {formatDate(selected.createdAt)}</div>
                <div><span className="font-bold text-slate-500">Cliente:</span> {selected.customerName || '-'}</div>
                <div><span className="font-bold text-slate-500">Email:</span> {selected.customerEmail || '-'}</div>
              </div>

              {selected.lines && selected.lines.length > 0 && (
                <div>
                  <h4 className="font-black text-xs uppercase text-slate-700 mb-2">Líneas ({selected.lines.length})</h4>
                  <div className="bg-slate-50 rounded-lg overflow-hidden border border-slate-200">
                    <table className="w-full text-xs">
                      <thead className="bg-slate-100">
                        <tr>
                          <th className="px-3 py-2 text-left font-black">Ref</th>
                          <th className="px-3 py-2 text-left font-black">Descripción</th>
                          <th className="px-3 py-2 text-right font-black">Cant.</th>
                          <th className="px-3 py-2 text-right font-black">PVP</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-200">
                        {selected.lines.slice(0, 50).map((ln, idx) => (
                          <tr key={idx} className="bg-white">
                            <td className="px-3 py-1.5 font-mono">{ln.ref || '-'}</td>
                            <td className="px-3 py-1.5">{ln.description || ln.descripcion || '-'}</td>
                            <td className="px-3 py-1.5 text-right">{ln.quantity || ln.cantidad || 1}</td>
                            <td className="px-3 py-1.5 text-right font-bold">{ln.pvp ? `${ln.pvp}€` : '-'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    {selected.lines.length > 50 && (
                      <div className="px-3 py-2 bg-slate-100 text-xs text-slate-500 text-center">
                        +{selected.lines.length - 50} líneas más
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DigitalizadorAuditTab;
