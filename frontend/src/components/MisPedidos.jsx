import React, { useState, useEffect } from 'react';
import { 
  Package, Search, Calendar, Euro, Mail, CheckCircle, 
  AlertTriangle, Eye, FileText, ChevronDown, ChevronUp,
  User, MapPin, Clock, Filter, RefreshCw, X
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const MisPedidos = ({ currentUser }) => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedOrder, setExpandedOrder] = useState(null);
  const [filterStatus, setFilterStatus] = useState('all');

  // Fetch orders
  useEffect(() => {
    fetchOrders();
  }, [currentUser]);

  const fetchOrders = async () => {
    setLoading(true);
    setError(null);
    try {
      // Si el usuario es admin/gerente, mostrar todos los pedidos
      // Si no, mostrar solo los del usuario actual (pero incluir pedidos sin userId asignado)
      const isAdmin = currentUser?.isAdmin || currentUser?.isGerente || currentUser?.isDirectorComercial;
      const url = isAdmin 
        ? `${API_URL}/api/orders`
        : `${API_URL}/api/orders`;  // Backend filtrará si es necesario
      
      const response = await fetch(url);
      if (!response.ok) throw new Error('Error al cargar pedidos');
      const data = await response.json();
      
      // Filtrar en frontend: admin ve todo, otros ven solo sus pedidos o los sin userId
      const filteredData = isAdmin 
        ? data 
        : data.filter(o => !o.userId || o.userId === currentUser?.id);
      
      setOrders(filteredData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Filter orders
  const filteredOrders = orders.filter(order => {
    const matchesSearch = 
      order.budgetNumber?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      order.customerName?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      order.projectReference?.toLowerCase().includes(searchTerm.toLowerCase());
    
    if (filterStatus === 'all') return matchesSearch;
    if (filterStatus === 'email_sent') return matchesSearch && order.emailSent;
    if (filterStatus === 'email_failed') return matchesSearch && !order.emailSent;
    return matchesSearch;
  });

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('es-ES', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('es-ES', {
      style: 'currency',
      currency: 'EUR'
    }).format(amount || 0);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500"></div>
      </div>
    );
  }

  return (
    <div className="p-6 bg-slate-50 min-h-screen">
      {/* Header */}
      <div className="bg-gradient-to-r from-orange-600 to-amber-500 rounded-2xl p-6 mb-6 text-white shadow-xl">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="bg-white/20 p-3 rounded-xl">
              <Package size={32} />
            </div>
            <div>
              <h1 className="text-2xl font-black">Mis Pedidos</h1>
              <p className="text-orange-100">Historial de pedidos confirmados</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="bg-white/20 px-4 py-2 rounded-xl font-bold">
              {orders.length} pedidos
            </span>
            <button
              onClick={fetchOrders}
              className="bg-white/20 p-2 rounded-xl hover:bg-white/30 transition-colors"
              title="Refrescar"
            >
              <RefreshCw size={20} />
            </button>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-2xl p-4 mb-6 shadow-lg border border-slate-200">
        <div className="flex flex-wrap items-center gap-4">
          {/* Search */}
          <div className="flex-1 min-w-[250px] relative">
            <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Buscar por nº expediente, cliente o referencia..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border-2 border-slate-200 rounded-xl focus:border-orange-500 outline-none"
            />
          </div>

          {/* Status Filter */}
          <div className="flex items-center gap-2">
            <Filter size={16} className="text-slate-400" />
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="border-2 border-slate-200 rounded-xl px-3 py-2 font-medium focus:border-orange-500 outline-none"
            >
              <option value="all">Todos</option>
              <option value="email_sent">Email enviado</option>
              <option value="email_failed">Email pendiente</option>
            </select>
          </div>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-xl mb-6 flex items-center gap-3">
          <AlertTriangle size={20} />
          {error}
        </div>
      )}

      {/* Orders List */}
      {filteredOrders.length === 0 ? (
        <div className="bg-white rounded-2xl p-12 text-center shadow-lg border border-slate-200">
          <Package size={48} className="mx-auto text-slate-300 mb-4" />
          <h3 className="text-xl font-bold text-slate-400 mb-2">No hay pedidos</h3>
          <p className="text-slate-400">Los pedidos confirmados aparecerán aquí</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredOrders.map(order => (
            <div 
              key={order.id} 
              className="bg-white rounded-2xl shadow-lg border border-slate-200 overflow-hidden hover:shadow-xl transition-shadow"
            >
              {/* Order Header */}
              <div 
                className="p-4 cursor-pointer hover:bg-slate-50 transition-colors"
                onClick={() => setExpandedOrder(expandedOrder === order.id ? null : order.id)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    {/* Status Icon */}
                    <div className={`p-3 rounded-xl ${order.emailSent ? 'bg-green-100' : 'bg-amber-100'}`}>
                      {order.emailSent ? (
                        <CheckCircle size={24} className="text-green-600" />
                      ) : (
                        <AlertTriangle size={24} className="text-amber-600" />
                      )}
                    </div>
                    
                    {/* Order Info */}
                    <div>
                      <div className="flex items-center gap-3">
                        <span className="text-lg font-black text-slate-800">#{order.budgetNumber}</span>
                        {order.projectReference && (
                          <span className="text-sm text-slate-500">• {order.projectReference}</span>
                        )}
                      </div>
                      <div className="flex items-center gap-4 text-sm text-slate-500 mt-1">
                        <span className="flex items-center gap-1">
                          <User size={14} />
                          {order.customerName}
                        </span>
                        <span className="flex items-center gap-1">
                          <Calendar size={14} />
                          {formatDate(order.confirmedAt)}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Amount & Expand */}
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <p className="text-2xl font-black text-orange-600">{formatCurrency(order.totalAmount)}</p>
                      <p className="text-xs text-slate-400">{order.itemsCount} artículos</p>
                    </div>
                    <div className="text-slate-400">
                      {expandedOrder === order.id ? <ChevronUp size={24} /> : <ChevronDown size={24} />}
                    </div>
                  </div>
                </div>
              </div>

              {/* Expanded Details */}
              {expandedOrder === order.id && (
                <div className="border-t border-slate-200 p-4 bg-slate-50">
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {/* Customer Info */}
                    <div className="bg-white p-4 rounded-xl border border-slate-200">
                      <h4 className="font-bold text-slate-700 mb-3 flex items-center gap-2">
                        <User size={16} className="text-orange-500" />
                        Cliente
                      </h4>
                      <p className="font-bold text-slate-800">{order.customerName}</p>
                      {order.customerAddress && (
                        <p className="text-sm text-slate-500 flex items-center gap-1 mt-1">
                          <MapPin size={12} />
                          {order.customerAddress}
                        </p>
                      )}
                      {order.email && (
                        <p className="text-sm text-slate-500 flex items-center gap-1 mt-1">
                          <Mail size={12} />
                          {order.email}
                        </p>
                      )}
                    </div>

                    {/* Status Info */}
                    <div className="bg-white p-4 rounded-xl border border-slate-200">
                      <h4 className="font-bold text-slate-700 mb-3 flex items-center gap-2">
                        <Mail size={16} className="text-orange-500" />
                        Estado Email
                      </h4>
                      {order.emailSent ? (
                        <div className="flex items-center gap-2 text-green-600">
                          <CheckCircle size={16} />
                          <span className="font-bold">Enviado correctamente</span>
                        </div>
                      ) : (
                        <div className="flex items-center gap-2 text-amber-600">
                          <AlertTriangle size={16} />
                          <span className="font-bold">No enviado</span>
                        </div>
                      )}
                      {order.emailProvider && (
                        <p className="text-xs text-slate-400 mt-1">vía {order.emailProvider}</p>
                      )}
                    </div>

                    {/* Specifications */}
                    {order.specifications && (
                      <div className="bg-white p-4 rounded-xl border border-slate-200">
                        <h4 className="font-bold text-slate-700 mb-3 flex items-center gap-2">
                          <FileText size={16} className="text-orange-500" />
                          Especificaciones
                        </h4>
                        <div className="text-sm space-y-1">
                          {order.specifications.globalFinish && (
                            <p><span className="text-slate-500">Acabado:</span> <span className="font-bold">{order.specifications.globalFinish}</span></p>
                          )}
                          {order.specifications.carcassColor && (
                            <p><span className="text-slate-500">Armazón:</span> <span className="font-bold">{order.specifications.carcassColor}</span></p>
                          )}
                          {order.specifications.doorColorLow && (
                            <p><span className="text-slate-500">Puertas Bajos:</span> <span className="font-bold">{order.specifications.doorColorLow}</span></p>
                          )}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Items */}
                  {order.items && order.items.length > 0 && (
                    <div className="mt-4 bg-white rounded-xl border border-slate-200 overflow-hidden">
                      <div className="bg-slate-100 px-4 py-2 font-bold text-slate-700">
                        Artículos del Pedido
                      </div>
                      <table className="w-full">
                        <thead className="bg-slate-50">
                          <tr className="text-xs font-bold text-slate-500 uppercase">
                            <th className="px-4 py-2 text-left">Código</th>
                            <th className="px-4 py-2 text-left">Descripción</th>
                            <th className="px-4 py-2 text-center">Cant.</th>
                            <th className="px-4 py-2 text-right">Precio</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {order.items.map((item, idx) => (
                            <tr key={idx} className="hover:bg-slate-50">
                              <td className="px-4 py-2 font-bold text-orange-600">{item.code || '-'}</td>
                              <td className="px-4 py-2 text-sm">{item.name || '-'}</td>
                              <td className="px-4 py-2 text-center font-bold">{item.quantity || 1}</td>
                              <td className="px-4 py-2 text-right font-bold">{formatCurrency(item.price)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}

                  {/* Notes */}
                  {order.notes && (
                    <div className="mt-4 bg-amber-50 border border-amber-200 rounded-xl p-4">
                      <h4 className="font-bold text-amber-700 mb-2">Notas</h4>
                      <p className="text-amber-800">{order.notes}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default MisPedidos;
