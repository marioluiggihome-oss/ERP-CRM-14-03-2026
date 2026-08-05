/*
 * © 2024-2026 Luiggi Home. Todos los derechos reservados. [LUIGGI-COPYRIGHT]
 * Software propietario y confidencial. Ver LICENSE.
 * Prohibida su copia, distribución, modificación o uso sin autorización
 * escrita del titular.
 */
import React, { useState, useEffect } from 'react';
import { 
  History, Clock, User, ArrowRight, Package, Factory, 
  CheckCircle, Truck, FileText, AlertCircle, Filter,
  ChevronDown, ChevronRight, Calendar, Search
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

/**
 * Historial de Cambios y Trazabilidad
 * Muestra un log completo de todos los cambios de estado en órdenes de fabricación
 */

// Configuración de estados para íconos y colores
const STATUS_CONFIG = {
  draft: { label: 'Borrador', color: 'bg-gray-100 text-gray-700', icon: FileText },
  confirmed: { label: 'Confirmada', color: 'bg-blue-100 text-blue-700', icon: CheckCircle },
  in_production: { label: 'En Producción', color: 'bg-amber-100 text-amber-700', icon: Factory },
  ready: { label: 'Fabricada', color: 'bg-emerald-100 text-emerald-700', icon: Package },
  delivered: { label: 'Entregada', color: 'bg-green-100 text-green-700', icon: Truck },
  cancelled: { label: 'Cancelada', color: 'bg-red-100 text-red-700', icon: AlertCircle }
};

// Tipos de cambio
const CHANGE_TYPES = {
  status_change: { label: 'Cambio de Estado', icon: ArrowRight, color: 'text-blue-600' },
  item_fabricated: { label: 'Mueble Fabricado', icon: CheckCircle, color: 'text-green-600' },
  priority_change: { label: 'Cambio de Prioridad', icon: AlertCircle, color: 'text-amber-600' },
  date_change: { label: 'Cambio de Fecha', icon: Calendar, color: 'text-purple-600' },
  note_added: { label: 'Nota Añadida', icon: FileText, color: 'text-slate-600' },
  order_created: { label: 'Orden Creada', icon: Package, color: 'text-emerald-600' },
  order_deleted: { label: 'Orden Eliminada', icon: AlertCircle, color: 'text-red-600' }
};

// Componente de entrada de historial
const HistoryEntry = ({ entry, expanded, onToggle }) => {
  const changeConfig = CHANGE_TYPES[entry.changeType] || CHANGE_TYPES.status_change;
  const ChangeIcon = changeConfig.icon;
  const fromStatus = STATUS_CONFIG[entry.fromValue] || { label: entry.fromValue, color: 'bg-gray-100 text-gray-700' };
  const toStatus = STATUS_CONFIG[entry.toValue] || { label: entry.toValue, color: 'bg-gray-100 text-gray-700' };

  return (
    <div className="bg-white rounded-xl border border-slate-200 overflow-hidden hover:shadow-md transition-shadow">
      <div 
        className="p-4 cursor-pointer flex items-center gap-4"
        onClick={onToggle}
      >
        {/* Indicador de tipo */}
        <div className={`p-2 rounded-xl bg-slate-100 ${changeConfig.color}`}>
          <ChangeIcon size={20} />
        </div>

        {/* Info principal */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-bold text-slate-800">
              {entry.orderNumber || entry.orderId}
            </span>
            <span className="text-slate-400">•</span>
            <span className="text-sm text-slate-600">{changeConfig.label}</span>
          </div>
          
          {/* Cambio de estado visual */}
          {entry.changeType === 'status_change' && (
            <div className="flex items-center gap-2 mt-1">
              <span className={`px-2 py-0.5 rounded text-xs font-bold ${fromStatus.color}`}>
                {fromStatus.label}
              </span>
              <ArrowRight size={14} className="text-slate-400" />
              <span className={`px-2 py-0.5 rounded text-xs font-bold ${toStatus.color}`}>
                {toStatus.label}
              </span>
            </div>
          )}
          
          {/* Otro tipo de cambio */}
          {entry.changeType !== 'status_change' && entry.description && (
            <p className="text-sm text-slate-500 mt-1 truncate">
              {entry.description}
            </p>
          )}
        </div>

        {/* Timestamp y usuario */}
        <div className="text-right shrink-0">
          <p className="text-xs text-slate-400">
            {new Date(entry.timestamp).toLocaleDateString('es-ES', {
              day: '2-digit',
              month: 'short',
              year: 'numeric'
            })}
          </p>
          <p className="text-xs text-slate-500 font-medium">
            {new Date(entry.timestamp).toLocaleTimeString('es-ES', {
              hour: '2-digit',
              minute: '2-digit'
            })}
          </p>
          {entry.userName && (
            <p className="text-xs text-blue-600 font-bold mt-1 flex items-center gap-1 justify-end">
              <User size={10} />
              {entry.userName}
            </p>
          )}
        </div>

        {/* Indicador de expansión */}
        <div className="text-slate-400">
          {expanded ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
        </div>
      </div>

      {/* Detalles expandidos */}
      {expanded && (
        <div className="px-4 pb-4 pt-0 border-t border-slate-100 bg-slate-50">
          <div className="grid grid-cols-2 gap-4 text-sm mt-3">
            {entry.orderId && (
              <div>
                <span className="text-slate-500">ID Orden:</span>
                <span className="ml-2 font-mono text-slate-700">{entry.orderId}</span>
              </div>
            )}
            {entry.factoryId && (
              <div>
                <span className="text-slate-500">Fábrica:</span>
                <span className="ml-2 font-medium text-slate-700">{entry.factoryName || entry.factoryId}</span>
              </div>
            )}
            {entry.clientName && (
              <div>
                <span className="text-slate-500">Cliente:</span>
                <span className="ml-2 font-medium text-slate-700">{entry.clientName}</span>
              </div>
            )}
            {entry.itemName && (
              <div>
                <span className="text-slate-500">Mueble:</span>
                <span className="ml-2 font-medium text-slate-700">{entry.itemName}</span>
              </div>
            )}
          </div>
          {entry.notes && (
            <div className="mt-3 p-3 bg-white rounded-lg border border-slate-200">
              <p className="text-xs text-slate-500 mb-1">Notas:</p>
              <p className="text-sm text-slate-700">{entry.notes}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Componente principal de Historial
const OrderHistory = ({ orders = [], currentUser, factories = [] }) => {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState(null);
  const [filterType, setFilterType] = useState('all');
  const [filterOrder, setFilterOrder] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  // Generar historial a partir de las órdenes
  useEffect(() => {
    const generateHistory = () => {
      const historyEntries = [];
      
      orders.forEach(order => {
        // Entrada de creación
        historyEntries.push({
          id: `${order.id}-created`,
          orderId: order.id,
          orderNumber: order.orderNumber,
          changeType: 'order_created',
          description: `Orden creada con ${order.items?.length || 0} muebles`,
          timestamp: order.createdAt,
          userName: order.createdBy || 'Sistema',
          factoryId: order.factoryId,
          factoryName: factories.find(f => f.id === order.factoryId)?.name,
          clientName: order.clientName
        });

        // Historial de cambios si existe
        if (order.statusHistory) {
          order.statusHistory.forEach((change, idx) => {
            historyEntries.push({
              id: `${order.id}-status-${idx}`,
              orderId: order.id,
              orderNumber: order.orderNumber,
              changeType: 'status_change',
              fromValue: change.from,
              toValue: change.to,
              timestamp: change.timestamp,
              userName: change.userName || 'Sistema',
              factoryId: order.factoryId,
              factoryName: factories.find(f => f.id === order.factoryId)?.name,
              clientName: order.clientName,
              notes: change.notes
            });
          });
        }

        // Muebles fabricados
        if (order.items) {
          order.items.forEach(item => {
            if (item.fabricationStatus === 'completed' && item.fabricatedAt) {
              historyEntries.push({
                id: `${order.id}-item-${item.id}`,
                orderId: order.id,
                orderNumber: order.orderNumber,
                changeType: 'item_fabricated',
                description: `${item.productCode} - ${item.productName}`,
                itemName: `${item.productCode} ${item.productName}`,
                timestamp: item.fabricatedAt,
                userName: item.fabricatedBy || 'Operario',
                factoryId: order.factoryId,
                factoryName: factories.find(f => f.id === order.factoryId)?.name
              });
            }
          });
        }
      });

      // Ordenar por fecha descendente
      historyEntries.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
      
      setHistory(historyEntries);
      setLoading(false);
    };

    generateHistory();
  }, [orders, factories]);

  // Filtrar historial
  const filteredHistory = history.filter(entry => {
    if (filterType !== 'all' && entry.changeType !== filterType) return false;
    if (filterOrder && entry.orderId !== filterOrder) return false;
    if (searchTerm) {
      const search = searchTerm.toLowerCase();
      return (
        entry.orderNumber?.toLowerCase().includes(search) ||
        entry.description?.toLowerCase().includes(search) ||
        entry.userName?.toLowerCase().includes(search) ||
        entry.clientName?.toLowerCase().includes(search)
      );
    }
    return true;
  });

  // Agrupar por fecha
  const groupedHistory = filteredHistory.reduce((groups, entry) => {
    const date = new Date(entry.timestamp).toLocaleDateString('es-ES', {
      weekday: 'long',
      day: 'numeric',
      month: 'long',
      year: 'numeric'
    });
    if (!groups[date]) groups[date] = [];
    groups[date].push(entry);
    return groups;
  }, {});

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-emerald-500 border-t-transparent"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-2xl font-black text-slate-800 flex items-center gap-3">
            <History className="text-purple-600" />
            Historial y Trazabilidad
          </h2>
          <p className="text-slate-500 text-sm mt-1">
            Registro completo de cambios en órdenes de fabricación
          </p>
        </div>
        
        <div className="flex items-center gap-3 flex-wrap">
          {/* Búsqueda */}
          <div className="relative">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Buscar..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9 pr-4 py-2 border-2 border-slate-200 rounded-xl text-sm focus:border-purple-500 outline-none w-48"
            />
          </div>
          
          {/* Filtro por tipo */}
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="px-4 py-2 border-2 border-slate-200 rounded-xl text-sm font-medium focus:border-purple-500 outline-none"
          >
            <option value="all">Todos los cambios</option>
            <option value="status_change">Cambios de estado</option>
            <option value="item_fabricated">Muebles fabricados</option>
            <option value="order_created">Órdenes creadas</option>
          </select>
          
          {/* Filtro por orden */}
          <select
            value={filterOrder}
            onChange={(e) => setFilterOrder(e.target.value)}
            className="px-4 py-2 border-2 border-slate-200 rounded-xl text-sm font-medium focus:border-purple-500 outline-none"
          >
            <option value="">Todas las órdenes</option>
            {orders.map(o => (
              <option key={o.id} value={o.id}>{o.orderNumber}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Estadísticas rápidas */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl p-4 border border-slate-200">
          <p className="text-xs text-slate-500 uppercase tracking-widest">Total Eventos</p>
          <p className="text-2xl font-black text-slate-800">{history.length}</p>
        </div>
        <div className="bg-white rounded-xl p-4 border border-slate-200">
          <p className="text-xs text-slate-500 uppercase tracking-widest">Cambios Estado</p>
          <p className="text-2xl font-black text-blue-600">
            {history.filter(h => h.changeType === 'status_change').length}
          </p>
        </div>
        <div className="bg-white rounded-xl p-4 border border-slate-200">
          <p className="text-xs text-slate-500 uppercase tracking-widest">Muebles Fabricados</p>
          <p className="text-2xl font-black text-green-600">
            {history.filter(h => h.changeType === 'item_fabricated').length}
          </p>
        </div>
        <div className="bg-white rounded-xl p-4 border border-slate-200">
          <p className="text-xs text-slate-500 uppercase tracking-widest">Órdenes Creadas</p>
          <p className="text-2xl font-black text-purple-600">
            {history.filter(h => h.changeType === 'order_created').length}
          </p>
        </div>
      </div>

      {/* Timeline */}
      <div className="space-y-6">
        {Object.entries(groupedHistory).length === 0 ? (
          <div className="text-center py-12 bg-white rounded-2xl border border-slate-200">
            <History size={48} className="mx-auto text-slate-300 mb-4" />
            <p className="text-slate-500 font-medium">No hay registros de historial</p>
            <p className="text-slate-400 text-sm">Los cambios aparecerán aquí cuando se realicen</p>
          </div>
        ) : (
          Object.entries(groupedHistory).map(([date, entries]) => (
            <div key={date}>
              <div className="flex items-center gap-3 mb-3">
                <Calendar size={16} className="text-purple-500" />
                <h3 className="font-bold text-slate-600 capitalize">{date}</h3>
                <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded text-xs font-bold">
                  {entries.length} eventos
                </span>
              </div>
              <div className="space-y-2 ml-6 border-l-2 border-purple-200 pl-4">
                {entries.map(entry => (
                  <HistoryEntry
                    key={entry.id}
                    entry={entry}
                    expanded={expandedId === entry.id}
                    onToggle={() => setExpandedId(expandedId === entry.id ? null : entry.id)}
                  />
                ))}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default OrderHistory;
