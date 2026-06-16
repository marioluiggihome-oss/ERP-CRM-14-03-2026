import React, { useState, useEffect } from 'react';
import { 
  Package, Search, Calendar, Euro, Mail, CheckCircle, 
  AlertTriangle, Eye, FileText, ChevronDown, ChevronUp,
  User, MapPin, Clock, Filter, RefreshCw, X, Printer,
  Factory, Truck, PackageCheck, Timer, Circle, Send, Paperclip
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Estados de fabricación con colores
const FABRICATION_STATES = {
  'confirmed': { label: 'Confirmado', color: 'bg-blue-100 text-blue-700', icon: CheckCircle },
  'pending': { label: 'Pendiente', color: 'bg-amber-100 text-amber-700', icon: Timer },
  'in_production': { label: 'En Producción', color: 'bg-purple-100 text-purple-700', icon: Factory },
  'ready': { label: 'Listo para Envío', color: 'bg-green-100 text-green-700', icon: PackageCheck },
  'shipped': { label: 'Enviado', color: 'bg-teal-100 text-teal-700', icon: Truck },
  'delivered': { label: 'Entregado', color: 'bg-emerald-100 text-emerald-700', icon: CheckCircle }
};

const MisPedidos = ({ currentUser }) => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedOrder, setExpandedOrder] = useState(null);
  const [filterStatus, setFilterStatus] = useState('all');
  const [showSendCopyModal, setShowSendCopyModal] = useState(null);
  const [sendCopyEmail, setSendCopyEmail] = useState('');
  const [sendCopyMessage, setSendCopyMessage] = useState('');
  const [sendCopyIncludeAttachments, setSendCopyIncludeAttachments] = useState(true);
  const [sendingCopy, setSendingCopy] = useState(false);

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

  // Enviar copia del pedido con adjuntos
  const handleSendCopy = async () => {
    if (!sendCopyEmail) {
      alert('Por favor introduce un email de destino');
      return;
    }
    
    setSendingCopy(true);
    try {
      const response = await fetch(`${API_URL}/api/orders/${showSendCopyModal.id}/send-copy`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          recipient_email: sendCopyEmail,
          include_attachments: sendCopyIncludeAttachments,
          additional_message: sendCopyMessage
        })
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Error al enviar copia');
      }
      
      const result = await response.json();
      alert(result.message || 'Copia enviada correctamente');
      setShowSendCopyModal(null);
      setSendCopyEmail('');
      setSendCopyMessage('');
      setSendCopyIncludeAttachments(true);
    } catch (err) {
      alert('Error: ' + err.message);
    } finally {
      setSendingCopy(false);
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

  // Función para imprimir pedido
  const handlePrintOrder = (order) => {
    const printWindow = window.open('', '_blank');
    const stateInfo = FABRICATION_STATES[order.fabricationStatus || 'confirmed'];
    
    const html = `
      <!DOCTYPE html>
      <html>
      <head>
        <title>Pedido #${order.budgetNumber}</title>
        <style>
          * { margin: 0; padding: 0; box-sizing: border-box; }
          body { font-family: 'Segoe UI', Arial, sans-serif; padding: 20px; color: #333; }
          .header { display: flex; justify-content: space-between; align-items: start; border-bottom: 3px solid #f97316; padding-bottom: 20px; margin-bottom: 20px; }
          .logo { font-size: 28px; font-weight: 900; color: #f97316; }
          .order-number { font-size: 24px; font-weight: 700; color: #334155; }
          .status-badge { display: inline-block; padding: 6px 12px; border-radius: 8px; font-size: 12px; font-weight: 700; background: #dbeafe; color: #1d4ed8; margin-top: 8px; }
          .section { margin-bottom: 20px; }
          .section-title { font-size: 14px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px; border-bottom: 1px solid #e2e8f0; padding-bottom: 5px; }
          .info-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; }
          .info-item label { display: block; font-size: 11px; color: #94a3b8; text-transform: uppercase; }
          .info-item span { font-size: 14px; font-weight: 600; color: #1e293b; }
          table { width: 100%; border-collapse: collapse; margin-top: 10px; }
          th { background: #f8fafc; padding: 12px 10px; text-align: left; font-size: 11px; font-weight: 700; text-transform: uppercase; color: #64748b; border-bottom: 2px solid #e2e8f0; }
          td { padding: 10px; border-bottom: 1px solid #f1f5f9; font-size: 13px; }
          .text-right { text-align: right; }
          .total-row { background: #fff7ed; font-weight: 700; }
          .total-row td { border-top: 2px solid #f97316; padding: 15px 10px; font-size: 16px; }
          .specs { background: #f8fafc; padding: 15px; border-radius: 8px; }
          .specs-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
          .specs-item { font-size: 12px; }
          .specs-item label { color: #64748b; }
          .specs-item span { font-weight: 600; color: #334155; }
          .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #e2e8f0; text-align: center; font-size: 11px; color: #94a3b8; }
          @media print { body { padding: 0; } }
        </style>
      </head>
      <body>
        <div class="header">
          <div>
            <div class="logo">LUIGGI HOME</div>
            <div style="font-size: 12px; color: #64748b;">Cocinas y Mobiliario</div>
          </div>
          <div style="text-align: right;">
            <div class="order-number">PEDIDO #${order.budgetNumber}</div>
            <div class="status-badge">${stateInfo.label}</div>
            <div style="font-size: 12px; color: #64748b; margin-top: 8px;">
              Fecha: ${formatDate(order.confirmedAt)}
            </div>
          </div>
        </div>

        <div class="section">
          <div class="section-title">Datos del Cliente</div>
          <div class="info-grid">
            <div class="info-item">
              <label>Nombre</label>
              <span>${order.customerName || '-'}</span>
            </div>
            <div class="info-item">
              <label>Email</label>
              <span>${order.email || '-'}</span>
            </div>
            <div class="info-item">
              <label>Dirección</label>
              <span>${order.customerAddress || '-'}</span>
            </div>
            <div class="info-item">
              <label>Referencia</label>
              <span>${order.projectReference || '-'}</span>
            </div>
          </div>
        </div>

        ${order.specifications ? `
        <div class="section">
          <div class="section-title">Especificaciones</div>
          <div class="specs">
            <div class="specs-grid">
              ${order.specifications.globalFinish ? `<div class="specs-item"><label>Acabado: </label><span>${order.specifications.globalFinish}</span></div>` : ''}
              ${order.specifications.carcassColor ? `<div class="specs-item"><label>Armazón: </label><span>${order.specifications.carcassColor}</span></div>` : ''}
              ${order.specifications.doorColorLow ? `<div class="specs-item"><label>Puertas Bajos: </label><span>${order.specifications.doorColorLow}</span></div>` : ''}
              ${order.specifications.doorColorHigh ? `<div class="specs-item"><label>Puertas Altos: </label><span>${order.specifications.doorColorHigh}</span></div>` : ''}
              ${order.specifications.doorColorColumns ? `<div class="specs-item"><label>Puertas Columnas: </label><span>${order.specifications.doorColorColumns}</span></div>` : ''}
              ${order.specifications.sideColor ? `<div class="specs-item"><label>Costados: </label><span>${order.specifications.sideColor}</span></div>` : ''}
            </div>
          </div>
        </div>
        ` : ''}

        <div class="section">
          <div class="section-title">Artículos del Pedido</div>
          <table>
            <thead>
              <tr>
                <th>Código</th>
                <th>Descripción</th>
                <th class="text-right">Cant.</th>
                <th class="text-right">Precio</th>
              </tr>
            </thead>
            <tbody>
              ${(order.items || []).map(item => `
                <tr>
                  <td style="font-weight: 600; color: #f97316;">${item.code || '-'}</td>
                  <td>${item.name || '-'}</td>
                  <td class="text-right">${item.quantity || 1}</td>
                  <td class="text-right">${formatCurrency(item.price)}</td>
                </tr>
              `).join('')}
              <tr class="total-row">
                <td colspan="3" class="text-right">TOTAL</td>
                <td class="text-right" style="color: #f97316;">${formatCurrency(order.totalAmount)}</td>
              </tr>
            </tbody>
          </table></div>
        </div>

        ${order.notes ? `
        <div class="section">
          <div class="section-title">Notas</div>
          <div style="background: #fffbeb; padding: 15px; border-radius: 8px; border-left: 4px solid #f59e0b;">
            ${order.notes}
          </div>
        </div>
        ` : ''}

        <div class="footer">
          LUIGGI HOME · Documento generado el ${new Date().toLocaleString('es-ES')}
        </div>
      </body>
      </html>
    `;
    
    printWindow.document.write(html);
    printWindow.document.close();
    printWindow.onload = () => {
      printWindow.print();
    };
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
                    {/* Status Icon - Based on fabrication status */}
                    {(() => {
                      const fabStatus = order.fabricationStatus || 'confirmed';
                      const stateInfo = FABRICATION_STATES[fabStatus] || FABRICATION_STATES['confirmed'];
                      const StateIcon = stateInfo.icon;
                      return (
                        <div className={`p-3 rounded-xl ${stateInfo.color.split(' ')[0]}`}>
                          <StateIcon size={24} className={stateInfo.color.split(' ')[1]} />
                        </div>
                      );
                    })()}
                    
                    {/* Order Info */}
                    <div>
                      <div className="flex items-center gap-3">
                        <span className="text-lg font-black text-slate-800">#{order.budgetNumber}</span>
                        {order.projectReference && (
                          <span className="text-sm text-slate-500">• {order.projectReference}</span>
                        )}
                        {/* Estado de Fabricación Badge */}
                        {(() => {
                          const fabStatus = order.fabricationStatus || 'confirmed';
                          const stateInfo = FABRICATION_STATES[fabStatus] || FABRICATION_STATES['confirmed'];
                          return (
                            <span className={`px-2 py-1 rounded-lg text-xs font-bold ${stateInfo.color}`}>
                              {stateInfo.label}
                            </span>
                          );
                        })()}
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

                  {/* Amount, Print, Send Copy & Expand */}
                  <div className="flex items-center gap-4">
                    {/* Send Copy Button */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setShowSendCopyModal(order);
                        setSendCopyEmail(order.email || '');
                      }}
                      className="p-2 bg-blue-100 hover:bg-blue-200 rounded-xl transition-colors"
                      title="Enviar copia con adjuntos"
                      data-testid={`send-copy-${order.id}`}
                    >
                      <Send size={18} className="text-blue-600" />
                    </button>
                    {/* Print Button */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handlePrintOrder(order);
                      }}
                      className="p-2 bg-slate-100 hover:bg-orange-100 rounded-xl transition-colors"
                      title="Imprimir Pedido"
                    >
                      <Printer size={18} className="text-slate-600 hover:text-orange-600" />
                    </button>
                    <div className="text-right">
                      <p className="text-2xl font-black text-orange-600">{formatCurrency(order.totalAmount)}</p>
                      <p className="text-xs text-slate-400">{order.itemsCount || order.items?.length || 0} artículos</p>
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
                      <div className="overflow-x-auto w-full"><table className="w-full">
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
                      </table></div>
                    </div>
                  )}

                  {/* Notes */}
                  {order.notes && (
                    <div className="mt-4 bg-amber-50 border border-amber-200 rounded-xl p-4">
                      <h4 className="font-bold text-amber-700 mb-2">Notas</h4>
                      <p className="text-amber-800">{order.notes}</p>
                    </div>
                  )}

                  {/* Adjuntos info */}
                  {order.attachments && order.attachments.length > 0 && (
                    <div className="mt-4 bg-blue-50 border border-blue-200 rounded-xl p-4">
                      <h4 className="font-bold text-blue-700 mb-2 flex items-center gap-2">
                        <Paperclip size={16} />
                        Archivos Adjuntos ({order.attachments.length})
                      </h4>
                      <div className="space-y-1">
                        {order.attachments.map((att, idx) => (
                          <p key={idx} className="text-sm text-blue-600">
                            {att.filename || `Adjunto ${idx + 1}`}
                          </p>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Modal Enviar Copia */}
      {showSendCopyModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full shadow-2xl">
            <div className="bg-gradient-to-r from-blue-600 to-blue-500 p-4 rounded-t-2xl flex items-center justify-between text-white">
              <div className="flex items-center gap-3">
                <Send size={20} />
                <h3 className="font-bold text-lg">Enviar Copia del Pedido</h3>
              </div>
              <button onClick={() => setShowSendCopyModal(null)} className="hover:bg-white/20 p-1 rounded">
                <X size={20} />
              </button>
            </div>
            
            <div className="p-6 space-y-4">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-700">
                <strong>Pedido #{showSendCopyModal.budgetNumber}</strong> - {showSendCopyModal.customerName}
              </div>
              
              <div>
                <label className="block text-sm font-bold text-slate-700 mb-1">
                  Email de destino *
                </label>
                <input
                  type="email"
                  value={sendCopyEmail}
                  onChange={(e) => setSendCopyEmail(e.target.value)}
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="correo@ejemplo.com"
                  data-testid="send-copy-email-input"
                />
              </div>
              
              <div>
                <label className="block text-sm font-bold text-slate-700 mb-1">
                  Mensaje adicional (opcional)
                </label>
                <textarea
                  value={sendCopyMessage}
                  onChange={(e) => setSendCopyMessage(e.target.value)}
                  className="w-full border border-slate-300 rounded-lg px-3 py-2 h-20 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Escribe un mensaje para incluir en el email..."
                  data-testid="send-copy-message-input"
                />
              </div>
              
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="includeAttachments"
                  checked={sendCopyIncludeAttachments}
                  onChange={(e) => setSendCopyIncludeAttachments(e.target.checked)}
                  className="h-4 w-4 text-blue-600 rounded"
                  data-testid="send-copy-include-attachments"
                />
                <label htmlFor="includeAttachments" className="text-sm text-slate-700 flex items-center gap-2">
                  <Paperclip size={14} />
                  Incluir archivos adjuntos del cliente
                  {showSendCopyModal.attachments?.length > 0 && (
                    <span className="bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full text-xs font-bold">
                      {showSendCopyModal.attachments.length} archivo(s)
                    </span>
                  )}
                </label>
              </div>
              
              <div className="flex gap-3 pt-2">
                <button
                  onClick={() => setShowSendCopyModal(null)}
                  className="flex-1 px-4 py-2 border border-slate-300 rounded-lg font-bold text-slate-700 hover:bg-slate-50"
                >
                  Cancelar
                </button>
                <button
                  onClick={handleSendCopy}
                  disabled={sendingCopy || !sendCopyEmail}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg font-bold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  data-testid="send-copy-submit-btn"
                >
                  {sendingCopy ? (
                    <>
                      <RefreshCw size={16} className="animate-spin" />
                      Enviando...
                    </>
                  ) : (
                    <>
                      <Send size={16} />
                      Enviar Copia
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MisPedidos;
